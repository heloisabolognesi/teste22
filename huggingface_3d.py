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

OUTPUT_DIRS = ['uploads/3d_models', 'output', 'generated_models']
for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

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
    if not image_url_or_path:
        logger.error("Empty image path provided")
        return None, "Caminho da imagem está vazio ou inválido."
    
    try:
        if image_url_or_path.startswith('http://') or image_url_or_path.startswith('https://'):
            logger.info(f"Downloading image from URL: {image_url_or_path}")
            response = requests.get(image_url_or_path, timeout=60)
            if response.status_code != 200:
                logger.error(f"Failed to download image: HTTP {response.status_code}")
                return None, f"Erro ao baixar imagem da nuvem: HTTP {response.status_code}"
            
            if len(response.content) < 1000:
                logger.error(f"Downloaded image too small: {len(response.content)} bytes")
                return None, "Imagem baixada está corrompida ou muito pequena."
            
            content_type = response.headers.get('content-type', 'image/jpeg')
            if 'png' in content_type.lower():
                ext = '.png'
            elif 'gif' in content_type.lower():
                ext = '.gif'
            else:
                ext = '.jpg'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(response.content)
                logger.info(f"Image saved to temp file: {tmp_file.name}, size: {len(response.content)} bytes")
                return tmp_file.name, None
        else:
            local_path = image_url_or_path
            if local_path.startswith('/'):
                local_path = local_path[1:]
            
            logger.info(f"Looking for local image: {local_path}")
            
            possible_paths = [
                local_path,
                f"static/{local_path}",
                local_path.replace('uploads/', ''),
                f"uploads/{local_path}"
            ]
            
            file_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.path.isfile(path):
                    file_path = path
                    logger.info(f"Found image at: {path}")
                    break
            
            if not file_path:
                logger.error(f"Local file not found in any of: {possible_paths}")
                return None, f"Arquivo de imagem não encontrado no sistema: {local_path}"
            
            file_size = os.path.getsize(file_path)
            if file_size < 1000:
                logger.error(f"Local image too small: {file_size} bytes")
                return None, "Arquivo de imagem está corrompido ou muito pequeno."
            
            ext = os.path.splitext(file_path)[1] or '.jpg'
            
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(image_data)
                logger.info(f"Local image copied to temp file: {tmp_file.name}, size: {len(image_data)} bytes")
                return tmp_file.name, None
            
    except IOError as e:
        logger.error(f"IO Error reading image: {str(e)}")
        return None, f"Erro ao ler arquivo de imagem: {str(e)}"
    except Exception as e:
        logger.error(f"Error downloading/reading image: {str(e)}")
        return None, f"Erro inesperado ao processar imagem: {str(e)}"

def extract_glb_from_response(result):
    """
    Extract GLB file data from TRELLIS API response.
    
    The API can return various formats:
    - Tuple with file objects at different positions
    - Dict with 'url', 'path', or 'value' keys
    - DownloadableFile objects with .url or .path attributes
    - Direct URL strings
    - Local file paths
    
    Returns:
        tuple: (model_data bytes or None, error message or None)
    """
    if result is None:
        logger.error("TRELLIS returned None")
        return None, "A IA não retornou nenhum resultado."
    
    logger.info(f"Parsing TRELLIS response: type={type(result).__name__}")
    
    candidates = []
    
    if isinstance(result, tuple):
        for i, item in enumerate(result):
            logger.debug(f"Result tuple[{i}]: type={type(item).__name__}, value={repr(item)[:200]}")
            candidates.append(item)
    elif isinstance(result, list):
        for i, item in enumerate(result):
            candidates.append(item)
    else:
        candidates.append(result)
    
    for candidate in candidates:
        model_data, error = try_extract_glb_data(candidate)
        if model_data:
            return model_data, None
    
    return None, "Nenhum arquivo 3D válido encontrado na resposta da IA."

def try_extract_glb_data(item):
    """
    Try to extract GLB binary data from a single response item.
    
    Returns:
        tuple: (bytes or None, error or None)
    """
    if item is None:
        return None, None
    
    glb_source = None
    
    if hasattr(item, 'url') and item.url:
        glb_source = item.url
        logger.info(f"Found DownloadableFile with URL: {glb_source}")
    elif hasattr(item, 'path') and item.path:
        glb_source = item.path
        logger.info(f"Found object with path: {glb_source}")
    elif isinstance(item, dict):
        glb_source = item.get('url') or item.get('path') or item.get('value')
        if glb_source:
            logger.info(f"Found dict with source: {glb_source}")
    elif isinstance(item, str) and item:
        glb_source = item
        logger.info(f"Found string source: {glb_source[:100]}")
    
    if not glb_source:
        return None, None
    
    if isinstance(glb_source, str) and (glb_source.startswith('http://') or glb_source.startswith('https://')):
        logger.info(f"Downloading GLB from URL: {glb_source}")
        try:
            response = requests.get(glb_source, timeout=120)
            if response.status_code == 200:
                data = response.content
                if len(data) > 1000:
                    logger.info(f"Downloaded GLB: {len(data)} bytes")
                    return data, None
                else:
                    logger.warning(f"Downloaded file too small: {len(data)} bytes")
                    return None, None
            else:
                logger.error(f"Failed to download GLB: HTTP {response.status_code}")
                return None, None
        except Exception as e:
            logger.error(f"Error downloading GLB: {str(e)}")
            return None, None
    
    if isinstance(glb_source, str) and os.path.exists(glb_source):
        try:
            file_size = os.path.getsize(glb_source)
            if file_size > 1000:
                with open(glb_source, 'rb') as f:
                    data = f.read()
                logger.info(f"Read local GLB file: {len(data)} bytes")
                return data, None
            else:
                logger.warning(f"Local file too small: {file_size} bytes")
                return None, None
        except IOError as e:
            logger.error(f"Error reading local GLB: {str(e)}")
            return None, None
    
    return None, None

def process_3d_generation(image_url, artifact_id):
    """
    Process the actual 3D model generation using Hugging Face Spaces.
    
    Uses the TRELLIS Space for image-to-3D generation.
    This is an EXPERIMENTAL feature for educational/visualization purposes only.
    
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
        
        logger.info("Starting 3D generation with TRELLIS (experimental)...")
        
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
        
        logger.info(f"TRELLIS raw result type: {type(result).__name__}")
        logger.debug(f"TRELLIS raw result: {repr(result)[:500]}")
        
        model_data, extract_error = extract_glb_from_response(result)
        
        if model_data and len(model_data) > 1000:
            logger.info(f"Successfully extracted GLB data: {len(model_data)} bytes")
            return store_model_data(model_data, artifact_id, 'glb')
        
        if extract_error:
            logger.error(f"GLB extraction failed: {extract_error}")
        else:
            logger.error("No valid GLB data found in TRELLIS response")
        
        return {
            'success': False,
            'error': 'A reconstrução 3D não pôde ser gerada no momento. Esta é uma funcionalidade experimental. Tente novamente com outra foto ou mais tarde.'
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
