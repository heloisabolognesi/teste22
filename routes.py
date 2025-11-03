import os
import uuid
from flask import render_template, request, redirect, url_for, flash, current_app, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

from app import app, db, LANGUAGES
from models import User, Artifact, Professional, Transport, Scanner3D, PhotoGallery
from forms import LoginForm, RegisterForm, ArtifactForm, ProfessionalForm, TransportForm, Scanner3DForm, AdminUserForm, PhotoGalleryForm

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, folder='uploads'):
    """Save uploaded file with proper error handling and path consistency"""
    if not file or not file.filename:
        return None
        
    try:
        # Secure the filename
        filename = secure_filename(file.filename)
        if not filename:
            return None
            
        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Ensure folder exists
        full_folder_path = os.path.join(current_app.static_folder, folder) if folder.startswith('uploads/') else folder
        os.makedirs(full_folder_path, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(full_folder_path, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Return relative path for database storage
        if folder.startswith('uploads/'):
            return f"{folder}/{unique_filename}"
        else:
            return file_path
            
    except Exception as e:
        current_app.logger.error(f"Error saving file: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if user.is_active_user:
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Sua conta está desativada. Contate o administrador.', 'error')
        else:
            flash('Email ou senha incorretos.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_email = User.query.filter_by(email=form.email.data).first()
        existing_username = User.query.filter_by(username=form.username.data).first()
        
        if existing_email:
            flash('Este email já está cadastrado.', 'error')
        elif existing_username:
            flash('Este nome de usuário já está em uso. Por favor, escolha outro.', 'error')
        else:
            # Validate academic fields for student/university accounts
            account_type = form.account_type.data
            if account_type in ['estudante', 'universitaria']:
                # Check if required academic fields are filled
                if not form.university.data:
                    flash('Por favor, selecione a faculdade.', 'error')
                    return render_template('register.html', form=form)
                # If custom university is selected, ensure the custom field is filled
                if form.university.data == 'custom' and not form.university_custom.data:
                    flash('Por favor, digite o nome da faculdade.', 'error')
                    return render_template('register.html', form=form)
                if not form.course.data:
                    flash('Por favor, preencha o campo Curso/Área de estudo.', 'error')
                    return render_template('register.html', form=form)
                if not form.entry_year.data:
                    flash('Por favor, preencha o ano de entrada.', 'error')
                    return render_template('register.html', form=form)
                if not form.institution_type.data:
                    flash('Por favor, selecione o tipo de instituição.', 'error')
                    return render_template('register.html', form=form)
                if not form.city.data or not form.state.data or not form.country.data:
                    flash('Por favor, preencha todos os campos de localização.', 'error')
                    return render_template('register.html', form=form)
            
            # Determine which university value to use
            university_value = None
            if account_type in ['estudante', 'universitaria']:
                if form.university.data == 'custom':
                    university_value = None
                else:
                    university_value = form.university.data
            
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                account_type=account_type,
                university=university_value,
                university_custom=form.university_custom.data if form.university.data == 'custom' else None,
                course=form.course.data if account_type in ['estudante', 'universitaria'] else None,
                entry_year=form.entry_year.data if account_type in ['estudante', 'universitaria'] else None,
                institution_type=form.institution_type.data if account_type in ['estudante', 'universitaria'] else None,
                city=form.city.data if account_type in ['estudante', 'universitaria'] else None,
                state=form.state.data if account_type in ['estudante', 'universitaria'] else None,
                country=form.country.data if account_type in ['estudante', 'universitaria'] else None
            )
            db.session.add(user)
            db.session.commit()
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get some statistics
    total_artifacts = Artifact.query.count()
    total_professionals = Professional.query.count()
    pending_transports = Transport.query.filter_by(status='pendente').count()
    
    stats = {
        'artifacts': total_artifacts,
        'professionals': total_professionals,
        'pending_transports': pending_transports
    }
    
    return render_template('dashboard.html', stats=stats)

@app.route('/catalogacao')
@login_required
def catalogacao():
    artifacts = Artifact.query.order_by(Artifact.created_at.desc()).all()
    return render_template('catalogacao.html', artifacts=artifacts)

@app.route('/catalogar_novo', methods=['GET', 'POST'])
@login_required
def catalogar_novo():
    form = ArtifactForm()
    if form.validate_on_submit():
        artifact = Artifact(
            name=form.name.data,
            code=form.code.data if form.code.data else f"LAR-{uuid.uuid4().hex[:8].upper()}",
            discovery_date=form.discovery_date.data,
            origin_location=form.origin_location.data,
            artifact_type=form.artifact_type.data,
            conservation_state=form.conservation_state.data,
            depth=form.depth.data,
            level=form.level.data,
            coordinates=form.coordinates.data,
            observations=form.observations.data,
            user_id=current_user.id,
            qr_code=f"LAARI-{uuid.uuid4().hex[:8].upper()}"
        )
        
        # Handle photo upload
        if form.photo.data:
            photo_path = save_uploaded_file(form.photo.data, 'uploads/photos')
            if photo_path:
                artifact.photo_path = photo_path
            else:
                flash('Erro ao fazer upload da foto. Tente novamente.', 'warning')
        
        # Handle 3D model upload
        if form.model_3d.data:
            model_path = save_uploaded_file(form.model_3d.data, 'uploads/3d_models')
            if model_path:
                artifact.model_3d_path = model_path
            else:
                flash('Erro ao fazer upload do modelo 3D. Tente novamente.', 'warning')
        
        # Handle IPHAN form upload
        if form.iphan_form.data:
            iphan_path = save_uploaded_file(form.iphan_form.data, 'uploads/iphan_forms')
            if iphan_path:
                artifact.iphan_form_path = iphan_path
            else:
                flash('Erro ao fazer upload da ficha IPHAN. Tente novamente.', 'warning')
        
        db.session.add(artifact)
        db.session.commit()
        flash('Artefato catalogado com sucesso!', 'success')
        return redirect(url_for('catalogacao'))
    
    return render_template('catalogar_novo.html', form=form)

@app.route('/acervo')
@login_required
def acervo():
    artifacts = Artifact.query.order_by(Artifact.name).all()
    return render_template('acervo.html', artifacts=artifacts)

@app.route('/inventario')
@login_required
def inventario():
    artifacts = Artifact.query.order_by(Artifact.created_at.desc()).all()
    return render_template('inventario.html', artifacts=artifacts)

@app.route('/profissionais')
@login_required
def profissionais():
    professionals = Professional.query.order_by(Professional.name).all()
    return render_template('profissionais.html', professionals=professionals)

@app.route('/profissional/<int:id>')
@login_required
def perfil_profissional(id):
    professional = Professional.query.get_or_404(id)
    return render_template('perfil_profissional.html', professional=professional)

@app.route('/adicionar_profissional', methods=['GET', 'POST'])
@login_required
def adicionar_profissional():
    form = ProfessionalForm()
    if form.validate_on_submit():
        professional = Professional(
            name=form.name.data,
            email=form.email.data,
            age=form.age.data,
            specialization=form.specialization.data,
            description=form.description.data,
            experience=form.experience.data
        )
        
        # Handle profile photo upload
        if form.profile_photo.data:
            photo_path = save_uploaded_file(form.profile_photo.data, 'uploads/profiles')
            if photo_path:
                professional.profile_photo = photo_path
            else:
                flash('Erro ao fazer upload da foto de perfil. Tente novamente.', 'warning')
        
        db.session.add(professional)
        db.session.commit()
        flash('Profissional adicionado com sucesso!', 'success')
        return redirect(url_for('profissionais'))
    
    return render_template('adicionar_profissional.html', form=form)

@app.route('/scanner_3d', methods=['GET', 'POST'])
@login_required
def scanner_3d():
    form = Scanner3DForm()
    
    # Populate artifact choices
    artifacts = Artifact.query.all()
    form.artifact_id.choices = [(a.id, f"{a.name} - {a.qr_code}") for a in artifacts]
    
    if form.validate_on_submit():
        scan = Scanner3D(
            artifact_id=form.artifact_id.data,
            scanner_type=form.scanner_type.data,
            resolution=form.resolution.data,
            notes=form.notes.data
        )
        
        # Handle scan file upload
        if form.scan_file.data:
            file_path = save_uploaded_file(form.scan_file.data, 'uploads/3d_scans')
            if file_path:
                scan.file_path = file_path
                # Get file size
                full_path = os.path.join(current_app.static_folder, file_path)
                if os.path.exists(full_path):
                    scan.file_size = os.path.getsize(full_path)
            else:
                flash('Erro ao fazer upload do arquivo de scan. Tente novamente.', 'warning')
        
        db.session.add(scan)
        db.session.commit()
        flash('Scan 3D registrado com sucesso!', 'success')
        return redirect(url_for('scanner_3d'))
    
    scans = Scanner3D.query.order_by(Scanner3D.scan_date.desc()).all()
    return render_template('scanner_3d.html', form=form, scans=scans)

@app.route('/transporte', methods=['GET', 'POST'])
@login_required
def transporte():
    form = TransportForm()
    
    # Populate artifact choices
    artifacts = Artifact.query.all()
    form.artifact_id.choices = [(a.id, f"{a.name} - {a.qr_code}") for a in artifacts]
    
    if form.validate_on_submit():
        transport = Transport(
            artifact_id=form.artifact_id.data,
            origin_location=form.origin_location.data,
            destination_location=form.destination_location.data,
            transport_date=form.transport_date.data,
            responsible_person=form.responsible_person.data,
            status=form.status.data,
            notes=form.notes.data
        )
        
        db.session.add(transport)
        db.session.commit()
        flash('Transporte registrado com sucesso!', 'success')
        return redirect(url_for('transporte'))
    
    transports = Transport.query.order_by(Transport.created_at.desc()).all()
    return render_template('transporte.html', form=form, transports=transports)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/toggle_user/<int:user_id>')
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode desativar sua própria conta.', 'error')
    else:
        user.is_active_user = not user.is_active_user
        db.session.commit()
        status = "ativado" if user.is_active_user else "desativado"
        flash(f'Usuário {user.username} foi {status}.', 'success')
    
    return redirect(url_for('admin'))

@app.route('/admin/toggle_admin/<int:user_id>')
@login_required
def toggle_admin_status(user_id):
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Você não pode remover seus próprios privilégios de administrador.', 'error')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        status = "promovido a administrador" if user.is_admin else "removido da administração"
        flash(f'Usuário {user.username} foi {status}.', 'success')
    
    return redirect(url_for('admin'))

# Language routes
@app.route('/set_language/<language>')
def set_language(language=None):
    if language and language in LANGUAGES:
        session['language'] = language
    return redirect(request.referrer or url_for('index'))

# Photo Gallery routes
@app.route('/galeria')
@login_required
def galeria():
    # Show published photos for regular users, all photos for admins
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all', type=str)
    
    query = PhotoGallery.query
    
    # Filter by publication status for non-admins
    if not current_user.is_admin:
        query = query.filter_by(is_published=True)
    
    # Filter by category
    if category != 'all':
        query = query.filter_by(category=category)
    
    photos = query.order_by(PhotoGallery.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('galeria.html', photos=photos, current_category=category)

@app.route('/api/galeria/photos')
def api_gallery_photos():
    """
    API endpoint para retornar fotos da galeria em formato JSON
    Retorna apenas fotos publicadas da categoria 'equipe' para usuários não autenticados
    """
    try:
        # Se o usuário não estiver autenticado, retornar apenas fotos públicas da equipe
        query = PhotoGallery.query.filter_by(is_published=True, category='equipe')
        
        # Buscar todas as fotos
        photos = query.order_by(PhotoGallery.created_at.desc()).all()
        
        # Serializar as fotos para JSON
        photos_data = []
        for photo in photos:
            photos_data.append({
                'id': photo.id,
                'title': photo.title,
                'description': photo.description or '',
                'image_path': photo.image_path,
                'category': photo.category,
                'event_name': photo.event_name or '',
                'created_at': photo.created_at.strftime('%d/%m/%Y'),
                'created_by': photo.created_by.username if photo.created_by else 'Desconhecido'
            })
        
        return jsonify({
            'success': True,
            'photos': photos_data,
            'total': len(photos_data)
        })
    except Exception as e:
        # Log erro detalhado no servidor, mas retorna mensagem genérica para o cliente
        app.logger.error(f'Erro ao buscar fotos da galeria: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Erro ao carregar fotos da galeria. Tente novamente mais tarde.',
            'photos': [],
            'total': 0
        }), 500

@app.route('/admin/galeria', methods=['GET', 'POST'])
@login_required
def admin_galeria():
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    form = PhotoGalleryForm()
    if form.validate_on_submit():
        photo = PhotoGallery(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            event_name=form.event_name.data if form.category.data == 'evento' else None,
            is_published=form.is_published.data,
            user_id=current_user.id
        )
        
        # Handle image upload
        if form.image.data:
            image_path = save_uploaded_file(form.image.data, 'uploads/gallery')
            if image_path:
                photo.image_path = image_path
                db.session.add(photo)
                db.session.commit()
                flash('Foto adicionada à galeria com sucesso!', 'success')
                return redirect(url_for('admin_galeria'))
            else:
                flash('Erro ao fazer upload da imagem. Tente novamente.', 'error')
    
    photos = PhotoGallery.query.order_by(PhotoGallery.created_at.desc()).all()
    return render_template('admin_galeria.html', form=form, photos=photos)

@app.route('/admin/galeria/toggle/<int:photo_id>')
@login_required
def toggle_photo_publication(photo_id):
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    photo = PhotoGallery.query.get_or_404(photo_id)
    photo.is_published = not photo.is_published
    db.session.commit()
    
    status = "publicada" if photo.is_published else "despublicada"
    flash(f'Foto "{photo.title}" foi {status}.', 'success')
    return redirect(url_for('admin_galeria'))

@app.route('/admin/galeria/delete/<int:photo_id>')
@login_required
def delete_photo(photo_id):
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    photo = PhotoGallery.query.get_or_404(photo_id)
    
    # Delete the image file if it exists
    if photo.image_path and os.path.exists(photo.image_path):
        os.remove(photo.image_path)
    
    db.session.delete(photo)
    db.session.commit()
    flash(f'Foto "{photo.title}" foi removida da galeria.', 'success')
    return redirect(url_for('admin_galeria'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
