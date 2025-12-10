"""
Replit Object Storage utilities for persistent file storage.
This module handles all file uploads and downloads using Replit's Object Storage
to ensure files persist across deployments and restarts.
"""
import os
import uuid
import logging
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

try:
    from replit.object_storage import Client
    from replit.object_storage.errors import ObjectNotFoundError, BucketNotFoundError
    OBJECT_STORAGE_AVAILABLE = True
    storage_client = Client()
    logger.info("Replit Object Storage initialized successfully")
except Exception as e:
    OBJECT_STORAGE_AVAILABLE = False
    storage_client = None
    logger.warning(f"Replit Object Storage not available: {e}. Falling back to local storage.")


def get_storage_path(folder, filename):
    """Generate a storage path with folder structure."""
    return f"{folder}/{filename}"


def upload_file(file, folder='uploads'):
    """
    Upload a file to Replit Object Storage.
    
    Args:
        file: FileStorage object from Flask request
        folder: Folder/prefix to store the file under
        
    Returns:
        str: The storage key (path) of the uploaded file, or None on failure
    """
    if not file or not file.filename:
        return None
    
    try:
        original_filename = secure_filename(file.filename)
        if not original_filename:
            return None
        
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        storage_key = get_storage_path(folder, unique_filename)
        
        file_bytes = file.read()
        
        if OBJECT_STORAGE_AVAILABLE and storage_client:
            storage_client.upload_from_bytes(storage_key, file_bytes)
            logger.info(f"File uploaded to Object Storage: {storage_key}")
            return storage_key
        else:
            static_folder = os.path.join(os.getcwd(), 'static')
            full_folder_path = os.path.join(static_folder, folder)
            os.makedirs(full_folder_path, exist_ok=True)
            
            file_path = os.path.join(full_folder_path, unique_filename)
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            logger.info(f"File saved to local storage: {storage_key}")
            return storage_key
            
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return None


def download_file(storage_key):
    """
    Download a file from Replit Object Storage.
    
    Args:
        storage_key: The storage path/key of the file
        
    Returns:
        bytes: The file content, or None if not found
    """
    if not storage_key:
        return None
    
    try:
        if OBJECT_STORAGE_AVAILABLE and storage_client:
            return storage_client.download_as_bytes(storage_key)
        else:
            static_folder = os.path.join(os.getcwd(), 'static')
            file_path = os.path.join(static_folder, storage_key)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
            return None
            
    except ObjectNotFoundError:
        logger.warning(f"File not found in Object Storage: {storage_key}")
        return None
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return None


def file_exists(storage_key):
    """
    Check if a file exists in storage.
    
    Args:
        storage_key: The storage path/key of the file
        
    Returns:
        bool: True if file exists, False otherwise
    """
    if not storage_key:
        return False
    
    try:
        if OBJECT_STORAGE_AVAILABLE and storage_client:
            return storage_client.exists(storage_key)
        else:
            static_folder = os.path.join(os.getcwd(), 'static')
            file_path = os.path.join(static_folder, storage_key)
            return os.path.exists(file_path)
            
    except Exception as e:
        logger.error(f"Error checking file existence: {str(e)}")
        return False


def delete_file(storage_key):
    """
    Delete a file from storage.
    
    Args:
        storage_key: The storage path/key of the file
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    if not storage_key:
        return False
    
    try:
        if OBJECT_STORAGE_AVAILABLE and storage_client:
            storage_client.delete(storage_key, ignore_not_found=True)
            logger.info(f"File deleted from Object Storage: {storage_key}")
            return True
        else:
            static_folder = os.path.join(os.getcwd(), 'static')
            file_path = os.path.join(static_folder, storage_key)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted from local storage: {storage_key}")
            return True
            
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False


def get_content_type(filename):
    """Get MIME type based on file extension."""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        'ico': 'image/x-icon',
        'obj': 'model/obj',
        'ply': 'application/ply',
        'stl': 'model/stl',
        'fbx': 'application/octet-stream',
        'pdf': 'application/pdf',
    }
    return content_types.get(ext, 'application/octet-stream')


def is_object_storage_available():
    """Check if Object Storage is available."""
    return OBJECT_STORAGE_AVAILABLE
