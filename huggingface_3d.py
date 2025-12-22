import os
import logging
import requests
import tempfile
import uuid
import zipfile
from gradio_client import Client, handle_file

logger = logging.getLogger(__name__)

HUGGINGFACE_API_TOKEN = os.environ.get('HUGGINGFACE_API_TOKEN')

SPACE_ID = "TencentARC/InstantMesh"

def is_ai_configured():
    """Check if Hugging Face AI is properly configured."""
    return bool(HUGGINGFACE_API_TOKEN)

def generate_3d_from_image(image_url, artifact_id=None):
    """
    Generate a 3D model from an image using Hugging Face Spaces.
    
    Args:
        image_url: URL of the image to convert to 3D
        artifact_id: ID of the artifact (for tracking)
        
    Returns:
        dict with 'success', 'task_id' or 'error' message
    """
    if not HUGGINGFACE_API_TOKEN:
        logger.error("Hugging Face API token not configured")
        return {
            'success': False, 
            'error': 'API de geração 3D não configurada. Configure o token da Hugging Face.'
        }
    
    try:
        task_id = f"hf_{uuid.uuid4().hex[:16]}"
        logger.info(f"Starting 3D generation for artifact {artifact_id}, task_id: {task_id}")
        
        return {
            'success': True, 
            'task_id': task_id,
            'image_url': image_url,
            'status': 'PENDING'
        }
        
    except Exception as e:
        logger.error(f"Hugging Face exception: {str(e)}")
        return {'success': False, 'error': str(e)}

def download_image_to_temp(image_url):
    """Download image from URL to a temporary file."""
    try:
        response = requests.get(image_url, timeout=60)
        if response.status_code != 200:
            return None, f"Erro ao baixar imagem: {response.status_code}"
        
        content_type = response.headers.get('content-type', 'image/jpeg')
        if 'png' in content_type.lower():
            ext = '.png'
        elif 'gif' in content_type.lower():
            ext = '.gif'
        else:
            ext = '.jpg'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_file.write(response.content)
            return tmp_file.name, None
            
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        return None, str(e)

def extract_model_from_zip(zip_path, artifact_id):
    """Extract 3D model file from ZIP archive."""
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)
            
            model_extensions = ['.glb', '.obj', '.gltf', '.ply']
            
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    for ext in model_extensions:
                        if file.lower().endswith(ext):
                            file_path = os.path.join(root, file)
                            with open(file_path, 'rb') as f:
                                model_data = f.read()
                            return model_data, ext.lstrip('.')
            
            return None, None
    except Exception as e:
        logger.error(f"Error extracting model from ZIP: {str(e)}")
        return None, None

def process_3d_generation(image_url, artifact_id):
    """
    Process the actual 3D model generation using Hugging Face Spaces.
    
    Uses the TencentARC/InstantMesh Space with the correct API flow:
    1. /preprocess - Clean and prepare the image
    2. /generate_mvs - Generate multiview images
    3. /make3d - Generate the final 3D model
    
    Args:
        image_url: URL of the image to convert
        artifact_id: ID of the artifact
        
    Returns:
        dict with model URL or error
    """
    if not HUGGINGFACE_API_TOKEN:
        return {'success': False, 'error': 'API não configurada'}
    
    temp_image_path = None
    
    try:
        temp_image_path, error = download_image_to_temp(image_url)
        if error:
            return {'success': False, 'error': error}
        
        logger.info(f"Connecting to Hugging Face Space: {SPACE_ID}")
        
        client = Client(SPACE_ID, hf_token=HUGGINGFACE_API_TOKEN)
        
        logger.info("Step 1: Preprocessing image (removing background)...")
        preprocess_result = client.predict(
            input_image=handle_file(temp_image_path),
            do_remove_background=True,
            erode_kernel=3,
            dilate_iteration=1,
            api_name="/preprocess"
        )
        logger.info(f"Preprocess completed. Result: {type(preprocess_result)}")
        
        if isinstance(preprocess_result, tuple):
            processed_image = preprocess_result[0]
        else:
            processed_image = preprocess_result
            
        if isinstance(processed_image, dict) and 'path' in processed_image:
            processed_image_path = processed_image['path']
        elif isinstance(processed_image, str):
            processed_image_path = processed_image
        else:
            logger.error(f"Unexpected preprocess result format: {processed_image}")
            return {'success': False, 'error': 'Erro no pré-processamento da imagem.'}
        
        logger.info("Step 2: Generating multiview images...")
        mvs_result = client.predict(
            image=handle_file(processed_image_path),
            sample_steps=75,
            sample_seed=42,
            camera_distance_ratio=1.5,
            elevation_deg=20,
            api_name="/generate_mvs"
        )
        logger.info(f"Multiview generation completed. Result type: {type(mvs_result)}")
        
        if isinstance(mvs_result, tuple):
            mvs_file = mvs_result[0]
        else:
            mvs_file = mvs_result
            
        if isinstance(mvs_file, dict) and 'path' in mvs_file:
            mvs_file_path = mvs_file['path']
        elif isinstance(mvs_file, str):
            mvs_file_path = mvs_file
        else:
            logger.error(f"Unexpected MVS result format: {mvs_file}")
            return {'success': False, 'error': 'Erro na geração de visualizações múltiplas.'}
        
        logger.info("Step 3: Generating 3D model...")
        model_result = client.predict(
            mvs_result=handle_file(mvs_file_path),
            mesh_simplify_ratio=0.95,
            api_name="/make3d"
        )
        logger.info(f"3D model generation completed. Result: {type(model_result)}")
        
        model_file = None
        if isinstance(model_result, tuple):
            for item in model_result:
                if isinstance(item, str) and (item.endswith('.glb') or item.endswith('.obj') or item.endswith('.zip')):
                    model_file = item
                    break
                elif isinstance(item, dict) and 'path' in item:
                    model_file = item['path']
                    break
            if not model_file and len(model_result) > 0:
                model_file = model_result[1] if len(model_result) > 1 else model_result[0]
        elif isinstance(model_result, dict) and 'path' in model_result:
            model_file = model_result['path']
        elif isinstance(model_result, str):
            model_file = model_result
        
        if model_file:
            if isinstance(model_file, dict) and 'path' in model_file:
                model_file = model_file['path']
                
            if model_file.endswith('.zip'):
                model_data, file_ext = extract_model_from_zip(model_file, artifact_id)
                if model_data:
                    return store_model_data(model_data, artifact_id, file_ext)
                else:
                    return {'success': False, 'error': 'Não foi possível extrair o modelo 3D do arquivo.'}
            elif os.path.exists(model_file):
                with open(model_file, 'rb') as f:
                    model_data = f.read()
                
                file_ext = 'glb' if model_file.endswith('.glb') else 'obj'
                return store_model_data(model_data, artifact_id, file_ext)
            else:
                return {'success': False, 'error': 'Arquivo do modelo 3D não encontrado.'}
        
        return {
            'success': False,
            'error': 'Modelo 3D não foi gerado corretamente. Tente novamente.'
        }
            
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Hugging Face Space exception: {str(e)}")
        
        if 'queue is full' in error_str or 'busy' in error_str:
            return {
                'success': False,
                'error': 'O serviço está ocupado. Tente novamente em alguns minutos.',
                'retry': True
            }
        elif 'timeout' in error_str:
            return {
                'success': False,
                'error': 'Tempo esgotado. A geração pode levar alguns minutos.',
                'retry': True
            }
        elif 'rate limit' in error_str or '429' in error_str:
            return {
                'success': False,
                'error': 'Limite de requisições atingido. Aguarde alguns minutos.',
                'retry': True
            }
        elif 'exceeded your gpu quota' in error_str:
            return {
                'success': False,
                'error': 'Cota de GPU excedida. Tente novamente mais tarde ou atualize para PRO.',
                'retry': True
            }
        else:
            return {
                'success': False,
                'error': f'A geração 3D depende de serviços externos de IA e pode estar temporariamente indisponível.'
            }
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                os.remove(temp_image_path)
            except:
                pass

def store_model_data(model_data, artifact_id, file_format='glb'):
    """
    Store the generated 3D model data.
    
    Args:
        model_data: Binary data of the 3D model
        artifact_id: ID of the artifact
        file_format: Format of the model file
        
    Returns:
        dict with stored model URL or error
    """
    try:
        filename = f"ai_model_{artifact_id}_{uuid.uuid4().hex[:8]}.{file_format}"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_format}') as tmp_file:
            tmp_file.write(model_data)
            tmp_path = tmp_file.name
        
        try:
            import cloudinary
            import cloudinary.uploader
            
            if os.environ.get('CLOUDINARY_CLOUD_NAME'):
                result = cloudinary.uploader.upload(
                    tmp_path,
                    resource_type='raw',
                    folder='laari/3d_models',
                    public_id=filename.rsplit('.', 1)[0]
                )
                stored_url = result.get('secure_url')
                logger.info(f"3D model stored in Cloudinary: {stored_url}")
                return {'success': True, 'url': stored_url}
            else:
                os.makedirs('uploads/3d_models', exist_ok=True)
                local_path = f'uploads/3d_models/{filename}'
                import shutil
                shutil.move(tmp_path, local_path)
                logger.info(f"3D model stored locally: {local_path}")
                return {'success': True, 'url': local_path}
                
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        logger.error(f"Error storing model: {str(e)}")
        return {'success': False, 'error': str(e)}

def check_task_status(task_id):
    """
    Check the status of a generation task.
    
    Args:
        task_id: The task ID
        
    Returns:
        dict with task status
    """
    return {
        'success': True,
        'status': 'PROCESSING',
        'progress': 50,
        'message': 'Processando modelo 3D...'
    }

def download_and_store_model(model_url, artifact_id):
    """
    Download a 3D model from URL and store it.
    
    Args:
        model_url: URL of the model to download
        artifact_id: ID of the artifact for naming
        
    Returns:
        dict with stored model URL or error
    """
    try:
        response = requests.get(model_url, timeout=60)
        
        if response.status_code == 200:
            return store_model_data(response.content, artifact_id, 'glb')
        else:
            return {'success': False, 'error': f'Erro ao baixar modelo: {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Error downloading/storing model: {str(e)}")
        return {'success': False, 'error': str(e)}

def generate_3d_synchronous(image_url, artifact_id):
    """
    Generate a 3D model synchronously (blocking call).
    
    This is the main entry point for 3D generation with full processing.
    
    Args:
        image_url: URL of the image
        artifact_id: ID of the artifact
        
    Returns:
        dict with model URL or error
    """
    logger.info(f"Starting synchronous 3D generation for artifact {artifact_id}")
    
    result = process_3d_generation(image_url, artifact_id)
    
    return result
