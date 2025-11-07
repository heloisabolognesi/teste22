"""
Migration script to update user status values from English to Portuguese
This script updates existing CV and institution status values to Portuguese
"""
from app import app, db
from models import User

def migrate_status_values():
    """Migrate user status values from English to Portuguese"""
    with app.app_context():
        # Mapping of old English values to new Portuguese values
        status_mapping = {
            'pending': 'Em análise',
            'approved': 'Aprovado',
            'rejected': 'Rejeitado'
        }
        
        updated_count = 0
        
        # Update CV status for professional accounts
        for old_status, new_status in status_mapping.items():
            professional_users = User.query.filter_by(
                account_type='profissional',
                cv_status=old_status
            ).all()
            
            for user in professional_users:
                user.cv_status = new_status
                updated_count += 1
                print(f"Updated professional user {user.username}: cv_status '{old_status}' -> '{new_status}'")
        
        # Update institution status for university accounts
        for old_status, new_status in status_mapping.items():
            university_users = User.query.filter_by(
                account_type='universitaria',
                institution_status=old_status
            ).all()
            
            for user in university_users:
                user.institution_status = new_status
                updated_count += 1
                print(f"Updated university user {user.username}: institution_status '{old_status}' -> '{new_status}'")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\nMigration completed successfully!")
        print(f"Total records updated: {updated_count}")

if __name__ == '__main__':
    migrate_status_values()
