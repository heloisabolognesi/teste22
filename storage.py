"""
Cloud storage utilities for persistent file uploads using Cloudinary.
This module handles all file uploads using Cloudinary for permanent storage.
Falls back to local storage if Cloudinary is not configured.
"""
import os
import uuid
import logging
import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Local upload folders (fallback)
UPLOAD_FOLDER = 'uploads'
ARTEFATOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'artefatos')
EQUIPE_FOLDER = os.path.join(UPLOAD_FOLDER, 'equipe')
GALLERY_FOLDER = os.path.join(UPLOAD_FOLDER, 'gallery')
CVS_FOLDER = os.path.join(UPLOAD_FOLDER, 'cvs')
QRCODES_FOLDER = os.path.join(UPLOAD_FOLDER, 'qrcodes')
PROFILES_FOLDER = os.path.join(UPLOAD_FOLDER, 'profiles')

# Create local folders as fallback
for folder in [ARTEFATOS_FOLDER, EQUIPE_FOLDER, GALLERY_FOLDER, CVS_FOLDER, QRCODES_FOLDER, PROFILES_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Configure Cloudinary
CLOUDINARY_CONFIGURED = False
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )
    CLOUDINARY_CONFIGURED = True
    logger.info("Cloudinary configured successfully for permanent storage")
else:
    logger.warning("Cloudinary not configured. Using local storage (files may be lost on rebuild)")


def is_cloudinary_available():
    """Check if Cloudinary is configured and available."""
    return CLOUDINARY_CONFIGURED


def upload_to_cloudinary(file, folder='laari'):
    """
    Upload a file to Cloudinary.
    
    Args:
        file: FileStorage object from Flask request
        folder: Folder in Cloudinary to store the file
        
    Returns:
        str: The secure URL of the uploaded file, or None on failure
    """
    if not file or not file.filename:
        return None
    
    try:
        original_filename = secure_filename(file.filename)
        if not original_filename:
            return None
        
        public_id = f"{folder}/{uuid.uuid4().hex}_{original_filename.rsplit('.', 1)[0]}"
        
        result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            resource_type="auto",
            overwrite=True
        )
        
        secure_url = result.get('secure_url')
        logger.info(f"File uploaded to Cloudinary: {secure_url}")
        return secure_url
        
    except Exception as e:
        logger.error(f"Error uploading to Cloudinary: {str(e)}")
        return None


def upload_file_local(file, folder='uploads'):
    """
    Upload a file to local storage (fallback).
    
    Args:
        file: FileStorage object from Flask request
        folder: Folder to store the file under
        
    Returns:
        str: The storage path of the uploaded file, or None on failure
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
        logger.error(f"Error uploading file locally: {str(e)}")
        return None


def upload_file(file, folder='uploads'):
    """
    Upload a file to storage (Cloudinary if available, otherwise local).
    
    Args:
        file: FileStorage object from Flask request
        folder: Folder/category for organization
        
    Returns:
        str: The URL (Cloudinary) or path (local) of the uploaded file, or None on failure
    """
    if CLOUDINARY_CONFIGURED:
        cloudinary_folder = folder.replace('uploads/', '').replace('uploads', 'laari')
        if not cloudinary_folder or cloudinary_folder == '/':
            cloudinary_folder = 'laari'
        return upload_to_cloudinary(file, cloudinary_folder)
    else:
        return upload_file_local(file, folder)


def upload_artifact_photo(file, require_cloudinary=True):
    """
    Upload an artifact photo to Cloudinary.
    
    Args:
        file: FileStorage object from Flask request
        require_cloudinary: If True, fails when Cloudinary is not configured
        
    Returns:
        str: The Cloudinary URL of the uploaded file, or None on failure
    """
    if not file or not file.filename:
        return None
        
    if CLOUDINARY_CONFIGURED:
        return upload_to_cloudinary(file, 'laari/artefatos')
    elif require_cloudinary:
        logger.error("Cloudinary is required for artifact photos but not configured")
        return None
    return upload_file_local(file, ARTEFATOS_FOLDER)


def upload_professional_photo(file):
    """Upload a professional/team member photo."""
    if CLOUDINARY_CONFIGURED:
        return upload_to_cloudinary(file, 'laari/equipe')
    return upload_file_local(file, EQUIPE_FOLDER)


def upload_gallery_photo(file):
    """Upload a gallery photo."""
    if CLOUDINARY_CONFIGURED:
        return upload_to_cloudinary(file, 'laari/gallery')
    return upload_file_local(file, GALLERY_FOLDER)


def upload_cv(file):
    """Upload a CV/curriculum file."""
    if CLOUDINARY_CONFIGURED:
        return upload_to_cloudinary(file, 'laari/cvs')
    return upload_file_local(file, CVS_FOLDER)


def generate_qr_code_image(qr_code_string, artifact_id):
    """
    Generate a QR code image for an artifact.
    
    Args:
        qr_code_string: The string to encode in the QR code
        artifact_id: The artifact ID for filename
        
    Returns:
        str: The storage path/URL of the generated QR code image, or None on failure
    """
    try:
        import qrcode
        from PIL import Image
        import io
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code_string)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        if CLOUDINARY_CONFIGURED:
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            public_id = f"laari/qrcodes/qrcode_{artifact_id}"
            result = cloudinary.uploader.upload(
                img_buffer,
                public_id=public_id,
                resource_type="image",
                overwrite=True
            )
            secure_url = result.get('secure_url')
            logger.info(f"QR code uploaded to Cloudinary: {secure_url}")
            return secure_url
        else:
            filename = f"qrcode_{artifact_id}.png"
            file_path = os.path.join(QRCODES_FOLDER, filename)
            img.save(file_path)
            logger.info(f"QR code generated and saved locally: {file_path}")
            return file_path
        
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return None


def download_file(storage_key):
    """
    Download a file from storage.
    
    Args:
        storage_key: The storage path/URL of the file
        
    Returns:
        bytes: The file content, or None if not found
    """
    if not storage_key:
        return None
    
    try:
        if storage_key.startswith('http'):
            import urllib.request
            with urllib.request.urlopen(storage_key) as response:
                return response.read()
        elif os.path.exists(storage_key):
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
        storage_key: The storage path/URL of the file
        
    Returns:
        bool: True if file exists, False otherwise
    """
    if not storage_key:
        return False
    
    try:
        if storage_key.startswith('http'):
            return True
        return os.path.exists(storage_key)
    except Exception as e:
        logger.error(f"Error checking file existence: {str(e)}")
        return False


def delete_file(storage_key):
    """
    Delete a file from storage.
    
    Args:
        storage_key: The storage path/URL of the file
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    if not storage_key:
        return False
    
    try:
        # Check if it's a Cloudinary URL
        if is_cloudinary_url(storage_key):
            if CLOUDINARY_CONFIGURED:
                public_id = extract_public_id_from_url(storage_key)
                if public_id:
                    try:
                        result = cloudinary.uploader.destroy(public_id)
                        logger.info(f"File deleted from Cloudinary: {public_id}, result: {result}")
                    except Exception as cloud_err:
                        logger.warning(f"Cloudinary deletion failed for {public_id}: {str(cloud_err)}")
            else:
                logger.warning(f"Cannot delete Cloudinary file {storage_key}: Cloudinary not configured")
            return True
        
        # Handle local file paths (relative paths only)
        if storage_key.startswith('/') or storage_key.startswith('http'):
            logger.warning(f"Skipping deletion of absolute/URL path: {storage_key}")
            return True
            
        if os.path.exists(storage_key):
            os.remove(storage_key)
            logger.info(f"File deleted from local storage: {storage_key}")
            return True
            
        logger.debug(f"File not found for deletion: {storage_key}")
        return True
            
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False


def extract_public_id_from_url(url):
    """Extract Cloudinary public_id from a secure URL."""
    try:
        if 'cloudinary.com' not in url:
            return None
        parts = url.split('/upload/')
        if len(parts) > 1:
            public_id_with_ext = parts[1].split('?')[0]
            if '/' in public_id_with_ext:
                version_and_id = public_id_with_ext.split('/', 1)
                if version_and_id[0].startswith('v'):
                    public_id_with_ext = version_and_id[1]
            public_id = public_id_with_ext.rsplit('.', 1)[0]
            return public_id
    except Exception as e:
        logger.error(f"Error extracting public_id: {str(e)}")
    return None


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


def is_cloudinary_url(path):
    """Check if a path is a Cloudinary URL."""
    if not path:
        return False
    return path.startswith('http') and 'cloudinary.com' in path


DEFAULT_PLACEHOLDER = '/static/images/default-placeholder.svg'


def get_image_url(path, default=None):
    """
    Get the display URL for an image, handling both Cloudinary URLs and local paths.
    
    Args:
        path: The stored path/URL
        default: Default image to return if path is invalid (uses SVG placeholder if None)
        
    Returns:
        str: The URL to display the image
    """
    if default is None:
        default = DEFAULT_PLACEHOLDER
        
    if not path:
        return default
    
    if is_cloudinary_url(path):
        return path
    
    if path.startswith('uploads/'):
        if os.path.exists(path):
            return f'/{path}'
        return default
    
    if os.path.exists(path):
        return f'/{path}'
    
    return default


def validate_image_url(url):
    """
    Validate if an image URL is accessible.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if valid and accessible
    """
    if not url:
        return False
    
    if is_cloudinary_url(url):
        return True
    
    if url.startswith('/'):
        local_path = url.lstrip('/')
        return os.path.exists(local_path)
    
    if os.path.exists(url):
        return True
    
    return False
