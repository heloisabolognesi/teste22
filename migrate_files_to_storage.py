"""
Migration script to upload existing local files to Replit Object Storage.
Run this script with: flask shell < migrate_files_to_storage.py
Or import and call from app context.
"""
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_uploads_to_object_storage(static_folder='static'):
    """Migrate all files from static/uploads to Object Storage."""
    
    try:
        from replit.object_storage import Client
        storage_client = Client()
        logger.info("Object Storage client initialized")
    except Exception as e:
        logger.error(f"Object Storage is not available: {e}")
        return False
    
    uploads_dir = os.path.join(static_folder, 'uploads')
    migrated_count = 0
    error_count = 0
    skipped_count = 0
    
    if not os.path.exists(uploads_dir):
        logger.warning(f"Uploads directory not found: {uploads_dir}")
        return False
    
    for root, dirs, files in os.walk(uploads_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, static_folder)
            
            try:
                if storage_client.exists(relative_path):
                    logger.info(f"Already exists, skipping: {relative_path}")
                    skipped_count += 1
                    continue
                
                logger.info(f"Migrating: {relative_path}")
                
                with open(local_path, 'rb') as f:
                    file_bytes = f.read()
                
                storage_client.upload_from_bytes(relative_path, file_bytes)
                
                migrated_count += 1
                logger.info(f"Successfully migrated: {relative_path}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to migrate {relative_path}: {str(e)}")
    
    logger.info(f"Migration complete. Migrated: {migrated_count}, Skipped: {skipped_count}, Errors: {error_count}")
    return migrated_count > 0 or skipped_count > 0


if __name__ == '__main__':
    from app import app
    with app.app_context():
        migrate_uploads_to_object_storage(app.static_folder)
