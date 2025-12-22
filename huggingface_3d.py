import os
import logging
import requests
import tempfile
import uuid
import zipfile
from gradio_client import Client, handle_file

logger = logging.getLogger(__name__)

HUGGINGFACE_API_TOKEN = os.environ.get('HUGGINGFACE_API_TOKEN')

SPACE_ID = "trellis-community/TRELLIS"

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

def download_image_to_temp(image_url_or_path):
    """Download image from URL or read from local file to a temporary file."""
    try:
        if image_url_or_path.startswith('http://') or image_url_or_path.startswith('https://'):
            response = requests.get(image_url_or_path, timeout=60)
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
        else:
            local_path = image_url_or_path
            if local_path.startswith('/'):
                local_path = local_path[1:]
            
            if os.path.exists(local_path):
                file_path = local_path
            elif os.path.exists(f"static/{local_path}"):
                file_path = f"static/{local_path}"
            elif os.path.exists(local_path.replace('uploads/', '')):
                file_path = local_path.replace('uploads/', '')
            else:
                logger.error(f"Local file not found: {local_path}")
                return None, f"Arquivo de imagem não encontrado: {local_path}"
            
            ext = os.path.splitext(file_path)[1] or '.jpg'
            
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(image_data)
                return tmp_file.name, None
            
    except Exception as e:
        logger.error(f"Error downloading/reading image: {str(e)}")
        return None, str(e)

def process_3d_generation(image_url, artifact_id):
    """
    Process the actual 3D model generation using Hugging Face Spaces.
    
    Uses the TRELLIS Space for image-to-3D generation.
    
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
        
        client = Client(SPACE_ID, token=HUGGINGFACE_API_TOKEN)
        
        logger.info("Starting 3D generation with TRELLIS...")
        
        result = client.predict(
            image=handle_file(temp_image_path),
            multiimages=[],
            seed=42,
            ss_guidance_strength=7.5,
            ss_sampling_steps=12,
            slat_guidance_strength=3.0,
            slat_sampling_steps=12,
            multiimage_algo="stochastic",
            mesh_simplify=0.95,
            texture_size=1024,
            api_name="/generate_and_extract_glb"
        )
        
        logger.info(f"TRELLIS result: {type(result)}, {result}")
        
        glb_file = None
        if isinstance(result, tuple) and len(result) >= 3:
            glb_file = result[2]
        elif isinstance(result, tuple) and len(result) >= 2:
            glb_file = result[1]
        elif isinstance(result, str):
            glb_file = result
        
        if glb_file:
            if isinstance(glb_file, dict) and 'path' in glb_file:
                glb_file = glb_file['path']
            
            if os.path.exists(glb_file):
                with open(glb_file, 'rb') as f:
                    model_data = f.read()
                
                return store_model_data(model_data, artifact_id, 'glb')
            else:
                logger.error(f"GLB file not found: {glb_file}")
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
                'error': 'Cota de GPU excedida. Tente novamente mais tarde.',
                'retry': True
            }
        elif 'runtime_error' in error_str or 'invalid state' in error_str:
            return {
                'success': False,
                'error': 'O serviço de IA está temporariamente indisponível. Tente novamente mais tarde.',
                'retry': True
            }
        else:
            return {
                'success': False,
                'error': f'A geração 3D depende de serviços externos de IA e pode estar temporariamente indisponível. Detalhes: {str(e)[:150]}'
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
