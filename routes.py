import os
import io
import uuid
from flask import render_template, request, redirect, url_for, flash, current_app, jsonify, session, send_file, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

from app import app, db, LANGUAGES
from models import User, Artifact, Professional, Transport, Scanner3D, PhotoGallery
from forms import LoginForm, RegisterForm, ArtifactForm, ProfessionalForm, TransportForm, Scanner3DForm, AdminUserForm, PhotoGalleryForm
from storage import upload_file, download_file, file_exists, get_content_type, is_object_storage_available

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, folder='uploads'):
    """Save uploaded file using Replit Object Storage for persistence"""
    return upload_file(file, folder)


@app.route('/storage/<path:file_path>')
def serve_storage_file(file_path):
    """Serve files from Replit Object Storage or local fallback."""
    from werkzeug.utils import safe_join
    from flask import abort
    
    # Security: Reject path traversal attempts
    if '..' in file_path or file_path.startswith('/'):
        abort(403)
    
    try:
        file_bytes = download_file(file_path)
        
        if file_bytes is None:
            # Use safe_join to prevent path traversal in local fallback
            safe_path = safe_join(current_app.static_folder, file_path)
            if safe_path is None:
                abort(403)
            if os.path.exists(safe_path):
                return send_file(safe_path)
            current_app.logger.warning(f"File not found: {file_path}")
            return Response("File not found", status=404)
        
        content_type = get_content_type(file_path)
        
        return Response(
            file_bytes,
            mimetype=content_type,
            headers={
                'Cache-Control': 'public, max-age=31536000',
                'Content-Disposition': 'inline'
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error serving file {file_path}: {str(e)}")
        return Response("Error loading file", status=500)


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
            account_type = form.account_type.data
            
            # Validate professional account - CV upload required
            if account_type == 'profissional':
                if not form.cv_file.data or not form.cv_file.data.filename:
                    flash('Por favor, envie seu currículo (CV) para criar uma conta profissional.', 'error')
                    return render_template('register.html', form=form)
            
            # Validate university account - institutional fields required
            elif account_type == 'universitaria':
                if not form.institution_name.data:
                    flash('Por favor, preencha o nome da instituição.', 'error')
                    return render_template('register.html', form=form)
                if not form.institution_cnpj.data:
                    flash('Por favor, preencha o CNPJ ou código institucional.', 'error')
                    return render_template('register.html', form=form)
                if not form.institution_courses.data:
                    flash('Por favor, liste os cursos oferecidos.', 'error')
                    return render_template('register.html', form=form)
                if not form.institution_responsible_name.data:
                    flash('Por favor, preencha o nome do responsável.', 'error')
                    return render_template('register.html', form=form)
                if not form.institution_contact_email.data:
                    flash('Por favor, preencha o email institucional de contato.', 'error')
                    return render_template('register.html', form=form)
                if not form.city.data or not form.state.data or not form.country.data:
                    flash('Por favor, preencha todos os campos de localização.', 'error')
                    return render_template('register.html', form=form)
            
            # Validate student account - academic fields required
            elif account_type == 'estudante':
                if not form.university.data:
                    flash('Por favor, selecione a faculdade.', 'error')
                    return render_template('register.html', form=form)
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
            
            # Determine university value for students
            university_value = None
            if account_type == 'estudante':
                if form.university.data == 'custom':
                    university_value = None
                else:
                    university_value = form.university.data
            
            # Create user
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                account_type=account_type,
                university=university_value,
                university_custom=form.university_custom.data if account_type == 'estudante' and form.university.data == 'custom' else None,
                course=form.course.data if account_type == 'estudante' else None,
                entry_year=form.entry_year.data if account_type == 'estudante' else None,
                institution_type=form.institution_type.data if account_type == 'estudante' else None,
                city=form.city.data if account_type in ['estudante', 'universitaria'] else None,
                state=form.state.data if account_type in ['estudante', 'universitaria'] else None,
                country=form.country.data if account_type in ['estudante', 'universitaria'] else None
            )
            
            # Handle CV upload for professional accounts
            if account_type == 'profissional' and form.cv_file.data:
                cv_path = save_uploaded_file(form.cv_file.data, 'uploads/cvs')
                if cv_path:
                    user.cv_file_path = cv_path
                    user.cv_status = 'Em análise'
                else:
                    flash('Erro ao fazer upload do currículo. Tente novamente.', 'warning')
                    return render_template('register.html', form=form)
            
            # Handle institutional data for university accounts
            if account_type == 'universitaria':
                user.institution_name = form.institution_name.data
                user.institution_cnpj = form.institution_cnpj.data
                user.institution_courses = form.institution_courses.data
                user.institution_responsible_name = form.institution_responsible_name.data
                user.institution_contact_email = form.institution_contact_email.data
                user.institution_status = 'Em análise'
            
            db.session.add(user)
            db.session.commit()
            
            # Custom success messages based on account type
            if account_type == 'profissional':
                flash('Cadastro realizado! Seu currículo está em análise. Você receberá um email quando for aprovado.', 'success')
            elif account_type == 'universitaria':
                flash('Cadastro institucional realizado! Aguarde a validação do administrador para ter acesso completo.', 'success')
            else:
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
    # Check if user has permission to access cataloging
    if not current_user.can_catalog_artifacts():
        lang = session.get('language', 'pt')
        messages = {
            'pt': 'Você não tem permissão para acessar a catalogação. ',
            'en': 'You do not have permission to access cataloging. ',
            'es': 'No tienes permiso para acceder a la catalogación. ',
            'fr': 'Vous n\'avez pas la permission d\'accéder au catalogage. '
        }
        
        # Add specific reason based on account type
        if current_user.account_type == 'profissional' and current_user.cv_status == 'Em análise':
            reasons = {
                'pt': 'Seu currículo ainda está em análise.',
                'en': 'Your CV is still under review.',
                'es': 'Tu currículum todavía está en revisión.',
                'fr': 'Votre CV est toujours en cours d\'examen.'
            }
            flash(messages.get(lang, messages['pt']) + reasons.get(lang, reasons['pt']), 'warning')
        elif current_user.account_type == 'universitaria' and current_user.institution_status == 'Em análise':
            reasons = {
                'pt': 'Seu cadastro institucional ainda está em análise.',
                'en': 'Your institutional registration is still under review.',
                'es': 'Tu registro institucional todavía está en revisión.',
                'fr': 'Votre enregistrement institutionnel est toujours en cours d\'examen.'
            }
            flash(messages.get(lang, messages['pt']) + reasons.get(lang, reasons['pt']), 'warning')
        elif current_user.account_type == 'estudante':
            reasons = {
                'pt': 'Contas de estudantes não têm permissão para catalogar artefatos.',
                'en': 'Student accounts do not have permission to catalog artifacts.',
                'es': 'Las cuentas de estudiantes no tienen permiso para catalogar artefactos.',
                'fr': 'Les comptes étudiants n\'ont pas la permission de cataloguer des artefacts.'
            }
            flash(messages.get(lang, messages['pt']) + reasons.get(lang, reasons['pt']), 'warning')
        else:
            flash(messages.get(lang, messages['pt']), 'error')
        
        return redirect(url_for('dashboard'))
    
    artifacts = Artifact.query.order_by(Artifact.created_at.desc()).all()
    return render_template('catalogacao.html', artifacts=artifacts)

@app.route('/catalogar_novo', methods=['GET', 'POST'])
@login_required
def catalogar_novo():
    # Check if user has permission to catalog artifacts
    if not current_user.can_catalog_artifacts():
        lang = session.get('language', 'pt')
        messages = {
            'pt': 'Você não tem permissão para catalogar artefatos.',
            'en': 'You do not have permission to catalog artifacts.',
            'es': 'No tienes permiso para catalogar artefactos.',
            'fr': 'Vous n\'avez pas la permission de cataloguer des artefacts.'
        }
        flash(messages.get(lang, messages['pt']), 'error')
        return redirect(url_for('dashboard'))
    
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


@app.route('/editar_artefato/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_artefato(id):
    """Edit an existing artifact. Only the cataloger or admin can edit."""
    artifact = Artifact.query.get_or_404(id)
    
    # Check permissions: only the user who cataloged or admin can edit
    if artifact.user_id != current_user.id and not current_user.is_admin:
        lang = session.get('language', 'pt')
        messages = {
            'pt': 'Você não tem permissão para editar este artefato.',
            'en': 'You do not have permission to edit this artifact.',
            'es': 'No tienes permiso para editar este artefacto.',
            'fr': 'Vous n\'avez pas la permission de modifier cet artefact.'
        }
        flash(messages.get(lang, messages['pt']), 'error')
        return redirect(url_for('catalogacao'))
    
    form = ArtifactForm(obj=artifact)
    
    if form.validate_on_submit():
        artifact.name = form.name.data
        artifact.code = form.code.data if form.code.data else artifact.code
        artifact.discovery_date = form.discovery_date.data
        artifact.origin_location = form.origin_location.data
        artifact.artifact_type = form.artifact_type.data
        artifact.conservation_state = form.conservation_state.data
        artifact.depth = form.depth.data
        artifact.level = form.level.data
        artifact.coordinates = form.coordinates.data
        artifact.observations = form.observations.data
        
        # Handle new photo upload
        if form.photo.data:
            photo_path = save_uploaded_file(form.photo.data, 'uploads/photos')
            if photo_path:
                artifact.photo_path = photo_path
        
        # Handle new 3D model upload
        if form.model_3d.data:
            model_path = save_uploaded_file(form.model_3d.data, 'uploads/3d_models')
            if model_path:
                artifact.model_3d_path = model_path
        
        # Handle new IPHAN form upload
        if form.iphan_form.data:
            iphan_path = save_uploaded_file(form.iphan_form.data, 'uploads/iphan_forms')
            if iphan_path:
                artifact.iphan_form_path = iphan_path
        
        db.session.commit()
        
        lang = session.get('language', 'pt')
        messages = {
            'pt': 'Artefato atualizado com sucesso!',
            'en': 'Artifact updated successfully!',
            'es': '¡Artefacto actualizado con éxito!',
            'fr': 'Artefact mis à jour avec succès!'
        }
        flash(messages.get(lang, messages['pt']), 'success')
        return redirect(url_for('catalogacao'))
    
    return render_template('editar_artefato.html', form=form, artifact=artifact)


@app.route('/excluir_artefato/<int:id>', methods=['POST'])
@login_required
def excluir_artefato(id):
    """Delete an artifact. Only the cataloger or admin can delete."""
    artifact = Artifact.query.get_or_404(id)
    
    # Check permissions: only the user who cataloged or admin can delete
    if artifact.user_id != current_user.id and not current_user.is_admin:
        lang = session.get('language', 'pt')
        messages = {
            'pt': 'Você não tem permissão para excluir este artefato.',
            'en': 'You do not have permission to delete this artifact.',
            'es': 'No tienes permiso para eliminar este artefacto.',
            'fr': 'Vous n\'avez pas la permission de supprimer cet artefact.'
        }
        flash(messages.get(lang, messages['pt']), 'error')
        return redirect(url_for('catalogacao'))
    
    artifact_name = artifact.name
    
    try:
        db.session.delete(artifact)
        db.session.commit()
        
        lang = session.get('language', 'pt')
        messages = {
            'pt': f'Artefato "{artifact_name}" excluído com sucesso!',
            'en': f'Artifact "{artifact_name}" deleted successfully!',
            'es': f'¡Artefacto "{artifact_name}" eliminado con éxito!',
            'fr': f'Artefact "{artifact_name}" supprimé avec succès!'
        }
        flash(messages.get(lang, messages['pt']), 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting artifact: {str(e)}')
        lang = session.get('language', 'pt')
        error_messages = {
            'pt': 'Erro ao excluir artefato. Tente novamente.',
            'en': 'Error deleting artifact. Please try again.',
            'es': 'Error al eliminar el artefacto. Inténtalo de nuevo.',
            'fr': 'Erreur lors de la suppression de l\'artefact. Veuillez réessayer.'
        }
        flash(error_messages.get(lang, error_messages['pt']), 'error')
    
    return redirect(url_for('catalogacao'))


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
            experience=form.experience.data,
            linkedin=form.linkedin.data,
            lattes_cv=form.lattes_cv.data
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

# CV and Institution Validation Routes
@app.route('/admin/validate_cv/<int:user_id>/<action>', methods=['POST'])
@login_required
def validate_cv(user_id, action):
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem validar currículos.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.account_type != 'profissional':
        flash('Este usuário não possui conta profissional.', 'error')
        return redirect(url_for('admin'))
    
    if action == 'approve':
        user.cv_status = 'Aprovado'
        user.cv_reviewed_at = datetime.utcnow()
        user.cv_reviewed_by = current_user.id
        user.cv_rejection_reason = None
        db.session.commit()
        
        # Get current language for multilingual messages
        lang = session.get('language', 'pt')
        messages = {
            'pt': f'Currículo de {user.username} foi aprovado! O usuário agora tem acesso à catalogação.',
            'en': f'CV of {user.username} has been approved! The user now has access to cataloging.',
            'es': f'Currículum de {user.username} ha sido aprobado! El usuario ya tiene acceso a la catalogación.',
            'fr': f'CV de {user.username} a été approuvé! L\'utilisateur a maintenant accès au catalogage.'
        }
        flash(messages.get(lang, messages['pt']), 'success')
        
    elif action == 'reject':
        reason = request.form.get('reason', request.args.get('reason', 'Currículo não atende aos requisitos.'))
        user.cv_status = 'Rejeitado'
        user.cv_reviewed_at = datetime.utcnow()
        user.cv_reviewed_by = current_user.id
        user.cv_rejection_reason = reason
        user.is_active_user = False  # Deactivate account when CV is rejected
        db.session.commit()
        
        # Get current language for multilingual messages
        lang = session.get('language', 'pt')
        messages = {
            'pt': f'Currículo de {user.username} foi rejeitado. A conta foi desativada.',
            'en': f'CV of {user.username} was rejected. The account has been deactivated.',
            'es': f'Currículum de {user.username} fue rechazado. La cuenta ha sido desactivada.',
            'fr': f'CV de {user.username} a été rejeté. Le compte a été désactivé.'
        }
        flash(messages.get(lang, messages['pt']), 'warning')
    
    return redirect(url_for('admin'))

@app.route('/admin/validate_institution/<int:user_id>/<action>', methods=['POST'])
@login_required
def validate_institution(user_id, action):
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem validar instituições.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.account_type != 'universitaria':
        flash('Este usuário não possui conta universitária.', 'error')
        return redirect(url_for('admin'))
    
    if action == 'approve':
        user.institution_status = 'Aprovado'
        user.institution_reviewed_at = datetime.utcnow()
        user.institution_reviewed_by = current_user.id
        user.institution_rejection_reason = None
        db.session.commit()
        
        # Get current language for multilingual messages
        lang = session.get('language', 'pt')
        messages = {
            'pt': f'Instituição {user.institution_name} foi aprovada! A conta agora tem acesso à catalogação.',
            'en': f'Institution {user.institution_name} has been approved! The account now has access to cataloging.',
            'es': f'Institución {user.institution_name} ha sido aprobada! La cuenta ya tiene acceso a la catalogación.',
            'fr': f'Institution {user.institution_name} a été approuvée! Le compte a maintenant accès au catalogage.'
        }
        flash(messages.get(lang, messages['pt']), 'success')
        
    elif action == 'reject':
        reason = request.form.get('reason', request.args.get('reason', 'Dados institucionais não foram verificados.'))
        user.institution_status = 'Rejeitado'
        user.institution_reviewed_at = datetime.utcnow()
        user.institution_reviewed_by = current_user.id
        user.institution_rejection_reason = reason
        user.is_active_user = False  # Deactivate account when institution is rejected
        db.session.commit()
        
        # Get current language for multilingual messages
        lang = session.get('language', 'pt')
        messages = {
            'pt': f'Instituição {user.institution_name} foi rejeitada. A conta foi desativada.',
            'en': f'Institution {user.institution_name} was rejected. The account has been deactivated.',
            'es': f'Institución {user.institution_name} fue rechazada. La cuenta ha sido desactivada.',
            'fr': f'Institution {user.institution_name} a été rejetée. Le compte a été désactivé.'
        }
        flash(messages.get(lang, messages['pt']), 'warning')
    
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

@app.route('/api/team/upload_photo', methods=['POST'])
@login_required
def upload_team_photo():
    try:
        if not current_user.is_admin:
            current_app.logger.warning(f'User {current_user.username} (ID: {current_user.id}) tentou fazer upload de foto da equipe sem permissões de admin')
            return jsonify({'success': False, 'error': 'Acesso negado. Apenas administradores podem adicionar fotos.'}), 403
        
        if 'image' not in request.files:
            current_app.logger.error('Upload de foto da equipe falhou: nenhum arquivo enviado')
            return jsonify({'success': False, 'error': 'Nenhuma imagem foi enviada.'}), 400
        
        image = request.files['image']
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title:
            current_app.logger.error('Upload de foto da equipe falhou: título vazio')
            return jsonify({'success': False, 'error': 'O título é obrigatório.'}), 400
        
        if not image or not image.filename:
            current_app.logger.error('Upload de foto da equipe falhou: nenhuma imagem selecionada')
            return jsonify({'success': False, 'error': 'Nenhuma imagem foi selecionada.'}), 400
        
        if not allowed_file(image.filename, {'jpg', 'jpeg', 'png', 'gif'}):
            current_app.logger.error(f'Upload de foto da equipe falhou: formato inválido ({image.filename})')
            return jsonify({'success': False, 'error': 'Formato de imagem inválido. Use JPG, PNG ou GIF.'}), 400
        
        image.seek(0, os.SEEK_END)
        file_size = image.tell()
        image.seek(0)
        
        max_size = 16 * 1024 * 1024
        if file_size > max_size:
            current_app.logger.error(f'Upload de foto da equipe falhou: arquivo muito grande ({file_size} bytes)')
            return jsonify({'success': False, 'error': 'Arquivo muito grande. Tamanho máximo: 16MB'}), 400
        
        if file_size == 0:
            current_app.logger.error('Upload de foto da equipe falhou: arquivo vazio')
            return jsonify({'success': False, 'error': 'Arquivo vazio. Por favor, selecione uma imagem válida.'}), 400
        
        image_path = save_uploaded_file(image, 'uploads/gallery')
        
        if not image_path:
            current_app.logger.error(f'Upload de foto da equipe falhou: erro ao salvar arquivo {image.filename}')
            return jsonify({'success': False, 'error': 'Erro ao fazer upload da imagem. Tente novamente.'}), 500
        
        photo = PhotoGallery(
            title=title,
            description=description,
            category='equipe',
            is_published=True,
            user_id=current_user.id,
            image_path=image_path
        )
        
        db.session.add(photo)
        db.session.commit()
        
        current_app.logger.info(f'Foto da equipe "{title}" adicionada com sucesso por {current_user.username} (ID: {current_user.id})')
        
        return jsonify({
            'success': True,
            'message': 'Foto adicionada com sucesso!',
            'photo': {
                'id': photo.id,
                'title': photo.title,
                'description': photo.description or '',
                'image_path': photo.image_path,
                'created_at': photo.created_at.strftime('%d/%m/%Y')
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao fazer upload de foto da equipe: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'error': 'Erro interno ao processar upload. Tente novamente.'}), 500

@app.route('/admin/migrate-storage')
@login_required
def migrate_storage():
    """Admin route to migrate local files to Object Storage."""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    import os
    from storage import is_object_storage_available
    
    if not is_object_storage_available():
        flash('Object Storage não está disponível.', 'error')
        return redirect(url_for('admin'))
    
    try:
        from replit.object_storage import Client
        storage_client = Client()
    except Exception as e:
        flash(f'Erro ao inicializar Object Storage: {str(e)}', 'error')
        return redirect(url_for('admin'))
    
    uploads_dir = os.path.join(current_app.static_folder, 'uploads')
    migrated_count = 0
    error_count = 0
    skipped_count = 0
    
    if not os.path.exists(uploads_dir):
        flash('Pasta de uploads não encontrada.', 'warning')
        return redirect(url_for('admin'))
    
    for root, dirs, files in os.walk(uploads_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, current_app.static_folder)
            
            try:
                if storage_client.exists(relative_path):
                    skipped_count += 1
                    continue
                
                with open(local_path, 'rb') as f:
                    file_bytes = f.read()
                
                storage_client.upload_from_bytes(relative_path, file_bytes)
                migrated_count += 1
                current_app.logger.info(f"Migrated: {relative_path}")
                
            except Exception as e:
                error_count += 1
                current_app.logger.error(f"Failed to migrate {relative_path}: {str(e)}")
    
    flash(f'Migração concluída. Migrados: {migrated_count}, Já existentes: {skipped_count}, Erros: {error_count}', 'success')
    return redirect(url_for('admin'))


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
