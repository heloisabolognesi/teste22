"""
Script to create admin user
"""
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin():
    """Create admin user"""
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email='roboticos415f2@gmail.com').first()
        
        if existing_user:
            # Update existing user to be admin
            existing_user.is_admin = True
            existing_user.is_active_user = True
            existing_user.password_hash = generate_password_hash('24062025')
            db.session.commit()
            print(f"✅ Usuário existente atualizado para administrador: {existing_user.username}")
        else:
            # Create new admin user
            admin = User(
                username='roboticos415f2',
                email='roboticos415f2@gmail.com',
                password_hash=generate_password_hash('24062025'),
                is_admin=True,
                is_active_user=True,
                account_type='profissional'
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Novo administrador criado com sucesso!")
        
        print(f"\nDetalhes da conta:")
        print(f"Email: roboticos415f2@gmail.com")
        print(f"Senha: 24062025")
        print(f"Tipo: Administrador")

if __name__ == '__main__':
    create_admin()
