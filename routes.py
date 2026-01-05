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
from storage import upload_file, upload_artifact_photo, upload_professional_photo, upload_gallery_photo, download_file, file_exists, get_content_type, generate_qr_code_image

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, folder='uploads'):
    """Save uploaded file to local storage"""
    return upload_file(file, folder)


@app.route('/uploads/<path:file_path>')
def serve_uploads(file_path):
    """Serve files from uploads/ directory."""
    from flask import abort, send_from_directory
    
    if '..' in file_path or file_path.startswith('/'):
        abort(403)
    
    try:
        return send_from_directory('uploads', file_path)
    except Exception as e:
        current_app.logger.error(f"Error serving file {file_path}: {str(e)}")
        return Response("File not found", status=404)


@app.route('/storage/<path:file_path>')
def serve_storage_file(file_path):
    """Serve files from uploads/ or static/ directory (legacy support)."""
    from flask import abort, send_from_directory
    
    if '..' in file_path or file_path.startswith('/'):
        abort(403)
    
    try:
        if file_path.startswith('uploads/'):
            return send_from_directory('.', file_path)
        
        if os.path.exists(file_path):
            return send_file(file_path)
        
        static_path = os.path.join('static', file_path)
        if os.path.exists(static_path):
            return send_file(static_path)
        
        current_app.logger.warning(f"File not found: {file_path}")
        return Response("File not found", status=404)
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

@app.route('/importacao-excel')
@login_required
def importacao_excel():
    if not current_user.can_catalog_artifacts():
        flash('Você não tem permissão para acessar a importação de dados.', 'warning')
        return redirect(url_for('dashboard'))
    return render_template('importacao_excel.html')

@app.route('/download-modelo-excel')
@login_required
def download_modelo_excel():
    return send_file('static/templates/modelo_importacao_laari.xlsx', 
                     as_attachment=True, 
                     download_name='modelo_importacao_laari.xlsx')

@app.route('/processar-importacao-excel', methods=['POST'])
@login_required
def processar_importacao_excel():
    import json
    import tempfile
    
    if not current_user.can_catalog_artifacts():
        flash('Você não tem permissão para importar dados.', 'warning')
        return redirect(url_for('dashboard'))
    
    if 'excel_file' not in request.files:
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('importacao_excel'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('importacao_excel'))
    
    if not file.filename.endswith(('.xlsx', '.csv')):
        flash('Formato de arquivo não suportado. Use .xlsx ou .csv', 'error')
        return redirect(url_for('importacao_excel'))
    
    try:
        import pandas as pd
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file, engine='openpyxl')
        
        required_columns = ['nome_artefato', 'tipo', 'estado_conservacao']
        all_columns = ['nome_artefato', 'codigo_artefato', 'data_descoberta', 'tipo', 
                      'local_origem', 'localizacao_arqueologica', 'profundidade', 
                      'nivel_estratigrafico', 'coordenadas', 'estado_conservacao', 'observacoes']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            flash(f'Colunas obrigatórias ausentes: {", ".join(missing_columns)}', 'error')
            return redirect(url_for('importacao_excel'))
        
        if len(df) > 100:
            flash('A planilha excede o limite de 100 artefatos. Por favor, divida em arquivos menores.', 'error')
            return redirect(url_for('importacao_excel'))
        
        if len(df) == 0:
            flash('A planilha está vazia.', 'error')
            return redirect(url_for('importacao_excel'))
        
        artifacts_data = []
        errors = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2
            row_errors = []
            
            if pd.isna(row.get('nome_artefato')) or str(row.get('nome_artefato')).strip() == '':
                row_errors.append('nome do artefato ausente')
            
            artifact = {
                'row': row_num,
                'nome_artefato': str(row.get('nome_artefato', '')).strip()[:200] if not pd.isna(row.get('nome_artefato')) else '',
                'codigo_artefato': str(row.get('codigo_artefato', '')).strip()[:100] if not pd.isna(row.get('codigo_artefato')) else '',
                'data_descoberta': str(row.get('data_descoberta', '')).strip()[:50] if not pd.isna(row.get('data_descoberta')) else '',
                'tipo': str(row.get('tipo', '')).strip()[:100] if not pd.isna(row.get('tipo')) else '',
                'local_origem': str(row.get('local_origem', '')).strip()[:200] if not pd.isna(row.get('local_origem')) else '',
                'localizacao_arqueologica': str(row.get('localizacao_arqueologica', '')).strip()[:200] if not pd.isna(row.get('localizacao_arqueologica')) else '',
                'profundidade': str(row.get('profundidade', '')).strip()[:50] if not pd.isna(row.get('profundidade')) else '',
                'nivel_estratigrafico': str(row.get('nivel_estratigrafico', '')).strip()[:100] if not pd.isna(row.get('nivel_estratigrafico')) else '',
                'coordenadas': str(row.get('coordenadas', '')).strip()[:100] if not pd.isna(row.get('coordenadas')) else '',
                'estado_conservacao': str(row.get('estado_conservacao', '')).strip()[:50] if not pd.isna(row.get('estado_conservacao')) else '',
                'observacoes': str(row.get('observacoes', '')).strip()[:1000] if not pd.isna(row.get('observacoes')) else '',
                'errors': row_errors
            }
            artifacts_data.append(artifact)
            if row_errors:
                errors.append({'row': row_num, 'errors': row_errors})
        
        import_token = uuid.uuid4().hex
        import_file_path = os.path.join(tempfile.gettempdir(), f'laari_import_{current_user.id}_{import_token}.json')
        with open(import_file_path, 'w', encoding='utf-8') as f:
            json.dump({'artifacts': artifacts_data, 'errors': errors}, f, ensure_ascii=False)
        
        session['import_token'] = import_token
        
        return render_template('importacao_excel_preview.html', 
                             artifacts=artifacts_data, 
                             errors=errors,
                             total=len(artifacts_data),
                             valid=len(artifacts_data) - len(errors),
                             import_token=import_token)
    
    except Exception as e:
        current_app.logger.error(f"Erro ao processar planilha: {str(e)}")
        flash(f'Erro ao processar o arquivo: {str(e)}', 'error')
        return redirect(url_for('importacao_excel'))

@app.route('/confirmar-importacao-excel', methods=['POST'])
@login_required
def confirmar_importacao_excel():
    import json
    import tempfile
    
    if not current_user.can_catalog_artifacts():
        flash('Você não tem permissão para importar dados.', 'warning')
        return redirect(url_for('dashboard'))
    
    import_token = session.get('import_token')
    if not import_token:
        flash('Sessão expirada. Por favor, envie a planilha novamente.', 'error')
        return redirect(url_for('importacao_excel'))
    
    import_file_path = os.path.join(tempfile.gettempdir(), f'laari_import_{current_user.id}_{import_token}.json')
    if not os.path.exists(import_file_path):
        flash('Dados da importação não encontrados. Por favor, envie a planilha novamente.', 'error')
        session.pop('import_token', None)
        return redirect(url_for('importacao_excel'))
    
    try:
        with open(import_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        import_data = data.get('artifacts', [])
        if not import_data:
            flash('Nenhum dado para importar.', 'error')
            return redirect(url_for('importacao_excel'))
        
        imported_count = 0
        batch_id = f"IMPORT-{uuid.uuid4().hex[:8].upper()}"
        
        for item in import_data:
            if item.get('errors'):
                continue
            
            conservation_map = {
                'excelente': 'excelente',
                'bom': 'bom',
                'regular': 'regular',
                'ruim': 'ruim',
                'inteiro': 'excelente',
                'íntegro': 'excelente',
                'fragmentado': 'regular',
                'restaurado': 'bom',
                'danificado': 'ruim'
            }
            estado = item.get('estado_conservacao', '')
            conservation = conservation_map.get(estado.lower() if estado else '', 'regular')
            
            codigo = item.get('codigo_artefato', '').strip()
            if not codigo:
                codigo = f"LAR-{uuid.uuid4().hex[:8].upper()}"
            
            artifact = Artifact(
                name=item['nome_artefato'],
                code=codigo,
                artifact_type=item.get('tipo', ''),
                origin_location=item.get('local_origem', ''),
                depth=item.get('profundidade', ''),
                level=item.get('nivel_estratigrafico', ''),
                coordinates=item.get('coordenadas', ''),
                conservation_state=conservation,
                observations=f"Localização arqueológica: {item.get('localizacao_arqueologica', '')}\n{item.get('observacoes', '')}\n\n[Importado via Excel - Lote: {batch_id}]",
                user_id=current_user.id,
                qr_code=f"LAARI-{uuid.uuid4().hex[:8].upper()}"
            )
            
            if item.get('data_descoberta'):
                try:
                    from datetime import datetime
                    artifact.discovery_date = datetime.strptime(item['data_descoberta'], '%Y-%m-%d').date()
                except:
                    pass
            
            db.session.add(artifact)
            imported_count += 1
        
        db.session.commit()
        
        os.remove(import_file_path)
        session.pop('import_token', None)
        
        flash(f'Importação concluída com sucesso! {imported_count} artefatos foram catalogados. (Lote: {batch_id})', 'success')
        return redirect(url_for('catalogacao'))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao confirmar importação: {str(e)}")
        flash(f'Erro ao importar dados: {str(e)}', 'error')
        return redirect(url_for('importacao_excel'))

@app.route('/cancelar-importacao-excel', methods=['POST'])
@login_required
def cancelar_importacao_excel():
    import tempfile
    
    import_token = session.get('import_token')
    if import_token:
        import_file_path = os.path.join(tempfile.gettempdir(), f'laari_import_{current_user.id}_{import_token}.json')
        if os.path.exists(import_file_path):
            os.remove(import_file_path)
    
    session.pop('import_token', None)
    flash('Importação cancelada.', 'info')
    return redirect(url_for('importacao_excel'))

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
        
        # Handle photo upload (Cloudinary required - blocks save on failure)
        photo_upload_failed = False
        # Check if photo was actually provided (not just empty FileStorage)
        has_photo = form.photo.data and hasattr(form.photo.data, 'filename') and form.photo.data.filename
        if has_photo:
            from storage import upload_artifact_photo, is_cloudinary_available
            import logging
            logging.info(f"Photo upload attempt: filename={form.photo.data.filename}, content_type={form.photo.data.content_type}")
            
            if not is_cloudinary_available():
                lang = session.get('language', 'pt')
                messages = {
                    'pt': 'Serviço de armazenamento de imagens não disponível. Tente novamente mais tarde.',
                    'en': 'Image storage service is not available. Please try again later.',
                    'es': 'Servicio de almacenamiento de imágenes no disponible. Intente nuevamente más tarde.',
                    'fr': 'Service de stockage d\'images non disponible. Veuillez réessayer plus tard.'
                }
                flash(messages.get(lang, messages['pt']), 'error')
                photo_upload_failed = True
            else:
                photo_url = upload_artifact_photo(form.photo.data)
                if photo_url:
                    artifact.photo_path = photo_url
                    logging.info(f"Photo uploaded successfully: {photo_url}")
                else:
                    lang = session.get('language', 'pt')
                    messages = {
                        'pt': 'Erro ao fazer upload da foto. Verifique se o arquivo é uma imagem válida e tente novamente.',
                        'en': 'Error uploading photo. Please check if the file is a valid image and try again.',
                        'es': 'Error al subir la foto. Verifique si el archivo es una imagen válida e intente nuevamente.',
                        'fr': 'Erreur lors du téléchargement de la photo. Vérifiez si le fichier est une image valide et réessayez.'
                    }
                    flash(messages.get(lang, messages['pt']), 'error')
                    photo_upload_failed = True
        
        # If photo upload was attempted but failed, don't save the artifact
        if photo_upload_failed:
            return render_template('catalogar_novo.html', form=form)
        
        # Handle 3D model upload
        if form.model_3d.data:
            from storage import upload_file
            model_url = upload_file(form.model_3d.data, 'uploads/3d_models')
            if model_url:
                artifact.model_3d_path = model_url
            else:
                flash('Erro ao fazer upload do modelo 3D. Tente novamente.', 'warning')
        
        # Handle IPHAN form upload
        if form.iphan_form.data:
            from storage import upload_file
            iphan_url = upload_file(form.iphan_form.data, 'uploads/iphan_forms')
            if iphan_url:
                artifact.iphan_form_path = iphan_url
            else:
                flash('Erro ao fazer upload da ficha IPHAN. Tente novamente.', 'warning')
        
        db.session.add(artifact)
        db.session.commit()
        
        # Generate QR code image with URL after artifact is saved (to get the ID)
        if artifact.qr_code:
            artifact_url = url_for('ver_artefato', id=artifact.id, _external=True)
            qr_image_path = generate_qr_code_image(artifact_url, artifact.id)
            if qr_image_path:
                artifact.qr_code_image_path = qr_image_path
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
        
        # Handle new photo upload (Cloudinary required - blocks save on failure)
        photo_upload_failed = False
        if form.photo.data:
            from storage import upload_artifact_photo, delete_file, is_cloudinary_available
            import logging
            logging.info(f"Photo edit upload attempt: filename={form.photo.data.filename}, content_type={form.photo.data.content_type}")
            
            if not is_cloudinary_available():
                lang = session.get('language', 'pt')
                messages = {
                    'pt': 'Serviço de armazenamento de imagens não disponível. Tente novamente mais tarde.',
                    'en': 'Image storage service is not available. Please try again later.',
                    'es': 'Servicio de almacenamiento de imágenes no disponible. Intente nuevamente más tarde.',
                    'fr': 'Service de stockage d\'images non disponible. Veuillez réessayer plus tard.'
                }
                flash(messages.get(lang, messages['pt']), 'error')
                photo_upload_failed = True
            else:
                photo_url = upload_artifact_photo(form.photo.data)
                if photo_url:
                    if artifact.photo_path:
                        delete_file(artifact.photo_path)
                    artifact.photo_path = photo_url
                    logging.info(f"Photo updated successfully: {photo_url}")
                else:
                    lang = session.get('language', 'pt')
                    messages = {
                        'pt': 'Erro ao fazer upload da nova foto. Verifique se o arquivo é uma imagem válida e tente novamente.',
                        'en': 'Error uploading new photo. Please check if the file is a valid image and try again.',
                        'es': 'Error al subir la nueva foto. Verifique si el archivo es una imagen válida e intente nuevamente.',
                        'fr': 'Erreur lors du téléchargement de la nouvelle photo. Vérifiez si le fichier est une image valide et réessayez.'
                    }
                    flash(messages.get(lang, messages['pt']), 'error')
                    photo_upload_failed = True
        
        # If photo upload was attempted but failed, don't save the changes
        if photo_upload_failed:
            return render_template('editar_artefato.html', form=form, artifact=artifact)
        
        # Handle new 3D model upload
        if form.model_3d.data:
            from storage import upload_file, delete_file
            if artifact.model_3d_path:
                delete_file(artifact.model_3d_path)
            model_url = upload_file(form.model_3d.data, 'uploads/3d_models')
            if model_url:
                artifact.model_3d_path = model_url
        
        # Handle new IPHAN form upload
        if form.iphan_form.data:
            from storage import upload_file, delete_file
            if artifact.iphan_form_path:
                delete_file(artifact.iphan_form_path)
            iphan_url = upload_file(form.iphan_form.data, 'uploads/iphan_forms')
            if iphan_url:
                artifact.iphan_form_path = iphan_url
        
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


@app.route('/api/artefato/<int:id>')
@login_required
def api_artefato_detalhes(id):
    """API endpoint to get artifact details for modal display."""
    try:
        artifact = Artifact.query.get_or_404(id)
        
        photo_url = None
        if artifact.photo_path:
            photo_url = url_for('serve_storage_file', file_path=artifact.photo_path)
        
        model_3d_url = None
        if artifact.model_3d_path:
            model_3d_url = url_for('serve_storage_file', file_path=artifact.model_3d_path)
        
        iphan_form_url = None
        if artifact.iphan_form_path:
            iphan_form_url = url_for('serve_storage_file', file_path=artifact.iphan_form_path)
        
        qr_code_image_url = None
        if artifact.qr_code_image_path:
            qr_code_image_url = url_for('serve_storage_file', file_path=artifact.qr_code_image_path)
        
        return jsonify({
            'success': True,
            'artifact': {
                'id': artifact.id,
                'name': artifact.name,
                'code': artifact.code,
                'qr_code': artifact.qr_code,
                'qr_code_image_url': qr_code_image_url,
                'discovery_date': artifact.discovery_date.strftime('%d/%m/%Y') if artifact.discovery_date else None,
                'origin_location': artifact.origin_location,
                'artifact_type': artifact.artifact_type,
                'conservation_state': artifact.conservation_state,
                'depth': artifact.depth,
                'level': artifact.level,
                'coordinates': artifact.coordinates,
                'observations': artifact.observations,
                'photo_url': photo_url,
                'model_3d_url': model_3d_url,
                'iphan_form_url': iphan_form_url,
                'cataloged_by': artifact.cataloged_by.username if artifact.cataloged_by else 'N/A',
                'created_at': artifact.created_at.strftime('%d/%m/%Y %H:%M') if artifact.created_at else None
            }
        })
    except Exception as e:
        current_app.logger.error(f'Error getting artifact details: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Erro ao carregar detalhes do artefato.'
        }), 500


@app.route('/artefato/<int:id>')
def ver_artefato(id):
    """Public page to view artifact details (accessed via QR code)."""
    artifact = Artifact.query.get_or_404(id)
    
    photo_url = None
    if artifact.photo_path:
        photo_url = url_for('serve_storage_file', file_path=artifact.photo_path)
    
    model_3d_url = None
    if artifact.model_3d_path:
        model_3d_url = url_for('serve_storage_file', file_path=artifact.model_3d_path)
    
    qr_code_image_url = None
    if artifact.qr_code_image_path:
        qr_code_image_url = url_for('serve_storage_file', file_path=artifact.qr_code_image_path)
    
    return render_template('ver_artefato.html', 
                           artifact=artifact, 
                           photo_url=photo_url, 
                           model_3d_url=model_3d_url,
                           qr_code_image_url=qr_code_image_url)


@app.route('/acervo')
@login_required
def acervo():
    artifacts = Artifact.query.order_by(Artifact.name).all()
    return render_template('acervo.html', artifacts=artifacts)


@app.route('/regenerar_qrcodes')
@login_required
def regenerar_qrcodes():
    """Regenerate QR code images for all artifacts that don't have them. Admin only."""
    if not current_user.is_admin:
        flash('Você não tem permissão para executar esta ação.', 'error')
        return redirect(url_for('dashboard'))
    
    artifacts = Artifact.query.filter(Artifact.qr_code.isnot(None)).all()
    regenerated = 0
    
    for artifact in artifacts:
        # Always regenerate with URL to ensure QR codes contain valid links
        artifact_url = url_for('ver_artefato', id=artifact.id, _external=True)
        qr_image_path = generate_qr_code_image(artifact_url, artifact.id)
        if qr_image_path:
            artifact.qr_code_image_path = qr_image_path
            regenerated += 1
    
    db.session.commit()
    flash(f'{regenerated} QR codes foram regenerados com sucesso!', 'success')
    return redirect(url_for('acervo'))

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
            from storage import upload_professional_photo
            photo_url = upload_professional_photo(form.profile_photo.data)
            if photo_url:
                professional.profile_photo = photo_url
            else:
                flash('Erro ao fazer upload da foto de perfil. Tente novamente.', 'warning')
        
        db.session.add(professional)
        db.session.commit()
        
        lang = session.get('language', 'pt')
        messages = {
            'pt': 'Profissional adicionado com sucesso!',
            'en': 'Professional added successfully!',
            'es': '¡Profesional añadido con éxito!',
            'fr': 'Professionnel ajouté avec succès!'
        }
        flash(messages.get(lang, messages['pt']), 'success')
        return redirect(url_for('profissionais'))
    
    return render_template('adicionar_profissional.html', form=form)


@app.route('/editar_profissional/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_profissional(id):
    """Edit an existing professional. Only admin can edit."""
    # Check if user is admin
    if not current_user.is_admin:
        lang = session.get('language', 'pt')
        messages = {
            'pt': 'Apenas administradores podem editar profissionais.',
            'en': 'Only administrators can edit professionals.',
            'es': 'Solo los administradores pueden editar profesionales.',
            'fr': 'Seuls les administrateurs peuvent modifier les professionnels.'
        }
        flash(messages.get(lang, messages['pt']), 'error')
        return redirect(url_for('profissionais'))
    
    professional = Professional.query.get_or_404(id)
    form = ProfessionalForm(obj=professional)
    
    if form.validate_on_submit():
        professional.name = form.name.data
        professional.email = form.email.data
        professional.age = form.age.data
        professional.specialization = form.specialization.data
        professional.description = form.description.data
        professional.experience = form.experience.data
        professional.linkedin = form.linkedin.data
        professional.lattes_cv = form.lattes_cv.data
        
        # Handle new photo upload
        if form.profile_photo.data:
            from storage import upload_professional_photo, delete_file
            # Delete old photo if exists
            if professional.profile_photo:
                delete_file(professional.profile_photo)
            photo_url = upload_professional_photo(form.profile_photo.data)
            if photo_url:
                professional.profile_photo = photo_url
        
        db.session.commit()
        
        lang = session.get('language', 'pt')
        messages = {
            'pt': 'Profissional atualizado com sucesso!',
            'en': 'Professional updated successfully!',
            'es': '¡Profesional actualizado con éxito!',
            'fr': 'Professionnel mis à jour avec succès!'
        }
        flash(messages.get(lang, messages['pt']), 'success')
        return redirect(url_for('profissionais'))
    
    return render_template('editar_profissional.html', form=form, professional=professional)


@app.route('/excluir_profissional/<int:id>', methods=['POST'])
@login_required
def excluir_profissional(id):
    """Delete a professional. Only admin can delete."""
    from storage import delete_file
    
    # Check if user is admin
    if not current_user.is_admin:
        lang = session.get('language', 'pt')
        messages = {
            'pt': 'Apenas administradores podem excluir profissionais.',
            'en': 'Only administrators can delete professionals.',
            'es': 'Solo los administradores pueden eliminar profesionales.',
            'fr': 'Seuls les administrateurs peuvent supprimer les professionnels.'
        }
        flash(messages.get(lang, messages['pt']), 'error')
        return redirect(url_for('profissionais'))
    
    professional = Professional.query.get_or_404(id)
    professional_name = professional.name
    profile_photo_path = professional.profile_photo
    
    try:
        # Delete the professional record
        db.session.delete(professional)
        db.session.commit()
        
        # Delete associated profile photo file if it exists
        if profile_photo_path:
            try:
                delete_file(profile_photo_path)
                current_app.logger.info(f'Deleted profile photo: {profile_photo_path}')
            except Exception as file_err:
                current_app.logger.warning(f'Could not delete profile photo {profile_photo_path}: {str(file_err)}')
        
        lang = session.get('language', 'pt')
        messages = {
            'pt': f'Profissional "{professional_name}" excluído com sucesso!',
            'en': f'Professional "{professional_name}" deleted successfully!',
            'es': f'¡Profesional "{professional_name}" eliminado con éxito!',
            'fr': f'Professionnel "{professional_name}" supprimé avec succès!'
        }
        flash(messages.get(lang, messages['pt']), 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting professional: {str(e)}')
        lang = session.get('language', 'pt')
        error_messages = {
            'pt': 'Erro ao excluir profissional. Tente novamente.',
            'en': 'Error deleting professional. Please try again.',
            'es': 'Error al eliminar el profesional. Inténtalo de nuevo.',
            'fr': 'Erreur lors de la suppression du professionnel. Veuillez réessayer.'
        }
        flash(error_messages.get(lang, error_messages['pt']), 'error')
    
    return redirect(url_for('profissionais'))


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
    
    # Check if AI is configured (Hugging Face)
    from huggingface_3d import is_ai_configured
    ai_configured = is_ai_configured()
    
    # Get artifacts list for AI generation section
    artifacts_list = Artifact.query.all()
    
    return render_template('scanner_3d.html', form=form, scans=scans, ai_configured=ai_configured, artifacts_list=artifacts_list)

@app.route('/scanner-3d/gerar')
@login_required
def gerar_3d_ia():
    """Dedicated page for AI 3D model generation - Currently in development."""
    flash('A funcionalidade de Reconstrução 3D por Inteligência Artificial está em desenvolvimento e faz parte do roadmap do L.A.A.R.I. Consulte a seção conceitual na página de Scanner 3D.', 'info')
    return redirect(url_for('scanner_3d'))

@app.route('/generate_3d_ai/<int:artifact_id>', methods=['POST'])
@login_required
def generate_3d_ai(artifact_id):
    """Generate a 3D model from artifact photo using AI - Currently in development."""
    flash('A funcionalidade de Reconstrução 3D por Inteligência Artificial está em desenvolvimento e faz parte do roadmap do L.A.A.R.I.', 'info')
    return redirect(url_for('scanner_3d'))

@app.route('/check_3d_status/<int:scan_id>')
@login_required
def check_3d_status(scan_id):
    """Check the status of an AI 3D generation task."""
    scan = Scanner3D.query.get_or_404(scan_id)
    
    if not scan.is_ai_generated or not scan.ai_task_id:
        return jsonify({'success': False, 'error': 'Este não é um modelo gerado por IA'})
    
    # If already completed, return cached result
    if scan.ai_status == 'SUCCEEDED' and scan.file_path:
        return jsonify({
            'success': True,
            'status': 'SUCCEEDED',
            'model_url': scan.file_path,
            'thumbnail_url': scan.ai_thumbnail
        })
    
    from huggingface_3d import check_task_status
    
    result = check_task_status(scan.ai_task_id)
    
    if result.get('success'):
        status = result.get('status')
        
        # For Hugging Face, processing is synchronous, so return current state
        return jsonify({
            'success': True,
            'status': scan.ai_status,
            'progress': result.get('progress', 0),
            'message': result.get('message', '')
        })
    
    return jsonify(result)

@app.route('/view_3d_model/<int:scan_id>')
@login_required
def view_3d_model(scan_id):
    """View a 3D model in the browser."""
    scan = Scanner3D.query.get_or_404(scan_id)
    
    if not scan.file_path:
        flash('Modelo 3D não disponível.', 'warning')
        return redirect(url_for('scanner_3d'))
    
    return render_template('view_3d_model.html', scan=scan)

@app.route('/delete_3d_scan/<int:scan_id>', methods=['POST'])
@login_required
def delete_3d_scan(scan_id):
    """Delete a 3D scan record."""
    scan = Scanner3D.query.get_or_404(scan_id)
    
    # Permission check: admin or the user who generated/created the scan
    can_delete = current_user.is_admin
    if scan.generated_by_user_id:
        can_delete = can_delete or (scan.generated_by_user_id == current_user.id)
    if scan.artifact and scan.artifact.user_id:
        can_delete = can_delete or (scan.artifact.user_id == current_user.id)
    
    if not can_delete:
        flash('Você não tem permissão para excluir este registro.', 'error')
        return redirect(url_for('scanner_3d'))
    
    # Delete from Cloudinary if it's a cloud file
    if scan.file_path and scan.file_path.startswith('http') and 'cloudinary' in scan.file_path:
        try:
            import cloudinary.uploader
            # Extract public_id from URL
            public_id = scan.file_path.split('/')[-1].rsplit('.', 1)[0]
            cloudinary.uploader.destroy(f"laari/3d_models/{public_id}", resource_type='raw')
        except Exception as e:
            current_app.logger.warning(f"Could not delete file from Cloudinary: {e}")
    
    artifact_name = scan.artifact.name if scan.artifact else 'Desconhecido'
    db.session.delete(scan)
    db.session.commit()
    
    flash(f'Registro 3D do artefato "{artifact_name}" excluído com sucesso.', 'success')
    return redirect(url_for('scanner_3d'))

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

@app.route('/api/usuario/<int:id>')
@login_required
def api_usuario_detalhes(id):
    """API endpoint to get user details for modal display."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Acesso negado.'}), 403
    
    try:
        user = User.query.get_or_404(id)
        
        cv_url = None
        if user.cv_file_path:
            cv_url = url_for('serve_storage_file', file_path=user.cv_file_path)
        
        university_name = user.university_custom if user.university_custom else user.university
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'is_active_user': user.is_active_user,
                'created_at': user.created_at.strftime('%d/%m/%Y %H:%M') if user.created_at else None,
                'account_type': user.account_type,
                'cv_file_url': cv_url,
                'cv_status': user.cv_status,
                'cv_rejection_reason': user.cv_rejection_reason,
                'cv_reviewed_at': user.cv_reviewed_at.strftime('%d/%m/%Y %H:%M') if user.cv_reviewed_at else None,
                'institution_name': user.institution_name,
                'institution_cnpj': user.institution_cnpj,
                'institution_courses': user.institution_courses,
                'institution_responsible_name': user.institution_responsible_name,
                'institution_contact_email': user.institution_contact_email,
                'institution_status': user.institution_status,
                'institution_rejection_reason': user.institution_rejection_reason,
                'institution_reviewed_at': user.institution_reviewed_at.strftime('%d/%m/%Y %H:%M') if user.institution_reviewed_at else None,
                'university': university_name,
                'course': user.course,
                'entry_year': user.entry_year,
                'institution_type': user.institution_type,
                'city': user.city,
                'state': user.state,
                'country': user.country
            }
        })
    except Exception as e:
        current_app.logger.error(f'Error getting user details: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Erro ao carregar detalhes do usuário.'
        }), 500


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
            from storage import upload_gallery_photo
            image_url = upload_gallery_photo(form.image.data)
            if image_url:
                photo.image_path = image_url
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
    if photo.image_path:
        from storage import delete_file
        delete_file(photo.image_path)
    
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
        
        from storage import upload_gallery_photo
        image_url = upload_gallery_photo(image)
        
        if not image_url:
            current_app.logger.error(f'Upload de foto da equipe falhou: erro ao salvar arquivo {image.filename}')
            return jsonify({'success': False, 'error': 'Erro ao fazer upload da imagem. Tente novamente.'}), 500
        
        photo = PhotoGallery(
            title=title,
            description=description,
            category='equipe',
            is_published=True,
            user_id=current_user.id,
            image_path=image_url
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
