import os
import logging
import requests
import time
import tempfile
import uuid
import base64

logger = logging.getLogger(__name__)

HUGGINGFACE_API_TOKEN = os.environ.get('HUGGINGFACE_API_TOKEN')
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models"

MODEL_ID = "stabilityai/TripoSR"

def is_ai_configured():
    """Check if Hugging Face AI is properly configured."""
    return bool(HUGGINGFACE_API_TOKEN)

def get_image_as_base64(image_url):
    """Download image from URL and convert to base64."""
    try:
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        else:
            logger.error(f"Failed to download image: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        return None

def generate_3d_from_image(image_url, artifact_id=None):
    """
    Generate a 3D model from an image using Hugging Face API.
    
    This function initiates the 3D generation process. Due to the nature of
    image-to-3D models, the process may take some time.
    
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
        logger.info(f"Image URL: {image_url}")
        
        return {
            'success': True, 
            'task_id': task_id,
            'image_url': image_url,
            'status': 'PENDING'
        }
        
    except Exception as e:
        logger.error(f"Hugging Face exception: {str(e)}")
        return {'success': False, 'error': str(e)}

def process_3d_generation(image_url, artifact_id):
    """
    Process the actual 3D model generation using Hugging Face.
    
    This is the synchronous processing function that handles the API call
    and model download.
    
    Args:
        image_url: URL of the image to convert
        artifact_id: ID of the artifact
        
    Returns:
        dict with model URL or error
    """
    if not HUGGINGFACE_API_TOKEN:
        return {'success': False, 'error': 'API não configurada'}
    
    try:
        headers = {
            'Authorization': f'Bearer {HUGGINGFACE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        image_response = requests.get(image_url, timeout=60)
        if image_response.status_code != 200:
            return {'success': False, 'error': 'Não foi possível baixar a imagem do artefato'}
        
        image_base64 = base64.b64encode(image_response.content).decode('utf-8')
        
        content_type = image_response.headers.get('content-type', 'image/jpeg')
        if 'png' in content_type.lower():
            mime_type = 'image/png'
        elif 'gif' in content_type.lower():
            mime_type = 'image/gif'
        else:
            mime_type = 'image/jpeg'
        
        payload = {
            "inputs": f"data:{mime_type};base64,{image_base64}",
            "parameters": {
                "output_format": "glb"
            }
        }
        
        api_url = f"{HUGGINGFACE_API_URL}/{MODEL_ID}"
        
        logger.info(f"Calling Hugging Face API: {api_url}")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            model_data = response.content
            
            result = store_model_data(model_data, artifact_id, 'glb')
            return result
            
        elif response.status_code == 503:
            try:
                error_data = response.json()
                estimated_time = error_data.get('estimated_time', 60)
                return {
                    'success': False, 
                    'error': f'Modelo está carregando. Tente novamente em {int(estimated_time)} segundos.',
                    'retry': True,
                    'retry_after': estimated_time
                }
            except:
                return {
                    'success': False,
                    'error': 'Serviço temporariamente indisponível. Tente novamente em alguns minutos.',
                    'retry': True
                }
        elif response.status_code == 429:
            return {
                'success': False,
                'error': 'Limite de requisições atingido. Aguarde alguns minutos.',
                'retry': True
            }
        elif response.status_code == 401 or response.status_code == 403:
            logger.error(f"Hugging Face auth error: {response.status_code}")
            return {
                'success': False,
                'error': 'Erro de autenticação com a API. Verifique o token.'
            }
        else:
            error_msg = response.text[:200] if response.text else 'Erro desconhecido'
            logger.error(f"Hugging Face API error: {response.status_code} - {error_msg}")
            return {
                'success': False,
                'error': f'A geração 3D depende de serviços externos de IA e pode estar temporariamente indisponível.'
            }
            
    except requests.exceptions.Timeout:
        logger.error("Hugging Face request timeout")
        return {
            'success': False, 
            'error': 'Tempo esgotado. A geração de modelos 3D pode levar alguns minutos.',
            'retry': True
        }
    except requests.exceptions.ConnectionError:
        logger.error("Hugging Face connection error")
        return {
            'success': False,
            'error': 'Erro de conexão com o serviço de IA. Tente novamente.',
            'retry': True
        }
    except Exception as e:
        logger.error(f"Hugging Face exception: {str(e)}")
        return {'success': False, 'error': str(e)}

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
    
    For Hugging Face, we use synchronous processing, so this function
    is mainly for compatibility with the existing flow.
    
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
