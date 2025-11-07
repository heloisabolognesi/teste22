from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def create_admin():
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='roboticos415f2@gmail.com').first()
        
        if existing_admin:
            print(f"Admin user already exists with email: roboticos415f2@gmail.com")
            # Update to ensure admin privileges
            existing_admin.is_admin = True
            existing_admin.is_active_user = True
            db.session.commit()
            print("Admin privileges confirmed for existing user.")
        else:
            # Create new admin user
            admin_user = User(
                username='admin_roboticos',
                email='roboticos415f2@gmail.com',
                password_hash=generate_password_hash('24062025'),
                is_admin=True,
                is_active_user=True,
                account_type='profissional'
            )
            
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user created successfully!")
            print(f"Email: roboticos415f2@gmail.com")
            print(f"Username: admin_roboticos")

if __name__ == '__main__':
    create_admin()
