import os
import logging
import requests
import time
from storage import upload_file

logger = logging.getLogger(__name__)

MESHY_API_KEY = os.environ.get('MESHY_API_KEY')
MESHY_API_URL = "https://api.meshy.ai/openapi/v1"

def is_meshy_configured():
    """Check if Meshy AI is properly configured."""
    return bool(MESHY_API_KEY)

def generate_3d_from_image(image_url, enable_pbr=True):
    """
    Generate a 3D model from an image using Meshy AI.
    
    Args:
        image_url: URL of the image to convert to 3D
        enable_pbr: Whether to enable PBR materials
        
    Returns:
        dict with 'success', 'task_id' or 'error' message
    """
    if not MESHY_API_KEY:
        logger.error("Meshy AI API key not configured")
        return {'success': False, 'error': 'API de geração 3D não configurada'}
    
    try:
        headers = {
            'Authorization': f'Bearer {MESHY_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'image_url': image_url,
            'enable_pbr': enable_pbr,
            'should_remesh': True,
            'should_texture': True
        }
        
        response = requests.post(
            f'{MESHY_API_URL}/image-to-3d',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            task_id = data.get('result')
            logger.info(f"Meshy AI task created: {task_id}")
            return {'success': True, 'task_id': task_id}
        else:
            error_msg = response.text
            logger.error(f"Meshy AI error: {response.status_code} - {error_msg}")
            return {'success': False, 'error': f'Erro na API: {response.status_code}'}
            
    except requests.exceptions.Timeout:
        logger.error("Meshy AI request timeout")
        return {'success': False, 'error': 'Tempo esgotado ao conectar com a API'}
    except Exception as e:
        logger.error(f"Meshy AI exception: {str(e)}")
        return {'success': False, 'error': str(e)}

def check_task_status(task_id):
    """
    Check the status of a Meshy AI task.
    
    Args:
        task_id: The Meshy AI task ID
        
    Returns:
        dict with task status and model URL if completed
    """
    if not MESHY_API_KEY:
        return {'success': False, 'error': 'API não configurada'}
    
    try:
        headers = {
            'Authorization': f'Bearer {MESHY_API_KEY}'
        }
        
        response = requests.get(
            f'{MESHY_API_URL}/image-to-3d/{task_id}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'UNKNOWN')
            
            result = {
                'success': True,
                'status': status,
                'progress': data.get('progress', 0)
            }
            
            if status == 'SUCCEEDED':
                result['model_urls'] = data.get('model_urls', {})
                result['thumbnail_url'] = data.get('thumbnail_url')
            elif status == 'FAILED':
                result['error'] = data.get('task_error', {}).get('message', 'Erro desconhecido')
                
            return result
        else:
            return {'success': False, 'error': f'Erro ao verificar status: {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Error checking Meshy task status: {str(e)}")
        return {'success': False, 'error': str(e)}

def download_and_store_model(model_url, artifact_id):
    """
    Download a 3D model from Meshy and store it in Cloudinary.
    
    Args:
        model_url: URL of the model to download
        artifact_id: ID of the artifact for naming
        
    Returns:
        dict with stored model URL or error
    """
    try:
        response = requests.get(model_url, timeout=60)
        
        if response.status_code == 200:
            import tempfile
            import uuid
            
            filename = f"ai_model_{artifact_id}_{uuid.uuid4().hex[:8]}.glb"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.glb') as tmp_file:
                tmp_file.write(response.content)
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
        else:
            return {'success': False, 'error': f'Erro ao baixar modelo: {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Error downloading/storing model: {str(e)}")
        return {'success': False, 'error': str(e)}

def wait_for_model_completion(task_id, max_wait_seconds=300, poll_interval=10):
    """
    Wait for a Meshy AI task to complete (synchronous polling).
    
    Args:
        task_id: The Meshy AI task ID
        max_wait_seconds: Maximum time to wait
        poll_interval: Seconds between status checks
        
    Returns:
        dict with final status and model URLs
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        result = check_task_status(task_id)
        
        if not result.get('success'):
            return result
            
        status = result.get('status')
        
        if status == 'SUCCEEDED':
            return result
        elif status == 'FAILED':
            return {'success': False, 'error': result.get('error', 'Geração falhou')}
        
        time.sleep(poll_interval)
    
    return {'success': False, 'error': 'Tempo limite excedido aguardando geração do modelo'}
