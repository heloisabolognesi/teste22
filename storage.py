"""
Local file storage utilities for persistent file uploads.
This module handles all file uploads using local directories.
"""
import os
import uuid
import logging
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'uploads'
ARTEFATOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'artefatos')
EQUIPE_FOLDER = os.path.join(UPLOAD_FOLDER, 'equipe')
GALLERY_FOLDER = os.path.join(UPLOAD_FOLDER, 'gallery')

os.makedirs(ARTEFATOS_FOLDER, exist_ok=True)
os.makedirs(EQUIPE_FOLDER, exist_ok=True)
os.makedirs(GALLERY_FOLDER, exist_ok=True)

logger.info("Local storage initialized successfully")


def get_storage_path(folder, filename):
    """Generate a storage path with folder structure."""
    return f"{folder}/{filename}"


def upload_file(file, folder='uploads'):
    """
    Upload a file to local storage.
    
    Args:
        file: FileStorage object from Flask request
        folder: Folder to store the file under
        
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
        
        os.makedirs(folder, exist_ok=True)
        
        file_path = os.path.join(folder, unique_filename)
        file.save(file_path)
        
        logger.info(f"File saved to local storage: {file_path}")
        return file_path
            
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return None


def upload_artifact_photo(file):
    """Upload an artifact photo to uploads/artefatos/"""
    return upload_file(file, ARTEFATOS_FOLDER)


def upload_professional_photo(file):
    """Upload a professional photo to uploads/equipe/"""
    return upload_file(file, EQUIPE_FOLDER)


def upload_gallery_photo(file):
    """Upload a gallery photo to uploads/gallery/"""
    return upload_file(file, GALLERY_FOLDER)


def download_file(storage_key):
    """
    Download a file from local storage.
    
    Args:
        storage_key: The storage path/key of the file
        
    Returns:
        bytes: The file content, or None if not found
    """
    if not storage_key:
        return None
    
    try:
        if os.path.exists(storage_key):
            with open(storage_key, 'rb') as f:
                return f.read()
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
        return os.path.exists(storage_key)
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
        if os.path.exists(storage_key):
            os.remove(storage_key)
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
        'mp4': 'video/mp4',
    }
    return content_types.get(ext, 'application/octet-stream')


def is_object_storage_available():
    """Check if Object Storage is available (always False for local storage)."""
    return False
