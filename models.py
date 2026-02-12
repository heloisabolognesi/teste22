from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Account type fields
    account_type = db.Column(db.String(50))  # profissional, universitaria, estudante
    
    # Professional account validation
    lattes_url = db.Column(db.String(255))  # Lattes CV URL
    cv_file_path = db.Column(db.String(255))  # Legacy: Path to CV file
    cv_status = db.Column(db.String(50), default='Em análise')  # Em análise, Aprovado, Rejeitado
    cv_rejection_reason = db.Column(db.Text)  # Reason for rejection if applicable
    cv_reviewed_at = db.Column(db.DateTime)  # When CV was reviewed
    cv_reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin who reviewed
    
    # Institutional fields (for university accounts)
    institution_name = db.Column(db.String(200))  # Official institution name
    institution_cnpj = db.Column(db.String(50))  # CNPJ or institutional code
    institution_courses = db.Column(db.Text)  # Courses offered (comma-separated)
    institution_responsible_name = db.Column(db.String(200))  # Name of person registering
    institution_contact_email = db.Column(db.String(200))  # Institutional contact email
    institution_status = db.Column(db.String(50), default='Em análise')  # Em análise, Aprovado, Rejeitado
    institution_rejection_reason = db.Column(db.Text)
    institution_reviewed_at = db.Column(db.DateTime)
    institution_reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Academic information fields (for student and university accounts)
    university = db.Column(db.String(200))
    university_custom = db.Column(db.String(200))  # For custom university input
    course = db.Column(db.String(200))
    entry_year = db.Column(db.Integer)
    institution_type = db.Column(db.String(50))  # publica, privada
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    
    # Relationships
    artifacts = db.relationship('Artifact', backref='cataloged_by', lazy='dynamic')
    
    def can_catalog_artifacts(self):
        """Check if user has permission to catalog artifacts"""
        if self.account_type == 'estudante':
            return False  # Students do NOT have cataloging access
        elif self.account_type == 'profissional':
            return self.cv_status == 'Aprovado'  # Professionals need approved CV
        elif self.account_type == 'universitaria':
            return self.institution_status == 'Aprovado'  # Institutions need approval
        return False

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer)
    specialization = db.Column(db.String(200))
    description = db.Column(db.Text)
    experience = db.Column(db.Text)
    profile_photo = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    lattes_cv = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Artifact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), unique=True)
    discovery_date = db.Column(db.Date)
    origin_location = db.Column(db.String(300))
    archaeological_site = db.Column(db.String(300))
    artifact_type = db.Column(db.String(100))
    conservation_state = db.Column(db.String(100))
    observations = db.Column(db.Text)
    photo_path = db.Column(db.String(255))
    model_3d_path = db.Column(db.String(255))
    iphan_form_path = db.Column(db.String(255))
    qr_code = db.Column(db.String(100), unique=True)
    qr_code_image_path = db.Column(db.String(255))
    
    # Campos de localização arqueológica
    depth = db.Column(db.String(50))  # Profundidade
    level = db.Column(db.String(100))  # Nível estratigráfico
    coordinates = db.Column(db.String(200))  # Coordenadas (GPS ou grid)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Transport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artifact_id = db.Column(db.Integer, db.ForeignKey('artifact.id'), nullable=False)
    origin_location = db.Column(db.String(300), nullable=False)
    destination_location = db.Column(db.String(300), nullable=False)
    transport_date = db.Column(db.DateTime)
    responsible_person = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Pendente')  # Pendente, Em Transito, Concluído
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    artifact = db.relationship('Artifact', backref='transports')

class Scanner3D(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artifact_id = db.Column(db.Integer, db.ForeignKey('artifact.id'))
    scan_date = db.Column(db.DateTime, default=datetime.utcnow)
    scanner_type = db.Column(db.String(100))
    resolution = db.Column(db.String(50))
    file_path = db.Column(db.String(255))
    file_size = db.Column(db.Integer)  # in bytes
    notes = db.Column(db.Text)
    
    # AI Generation fields
    is_ai_generated = db.Column(db.Boolean, default=False)
    ai_task_id = db.Column(db.String(100))
    ai_status = db.Column(db.String(50))  # PENDING, PROCESSING, SUCCEEDED, FAILED
    ai_source_image = db.Column(db.String(500))  # Source image URL
    ai_thumbnail = db.Column(db.String(500))  # AI-generated thumbnail
    generated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationship
    artifact = db.relationship('Artifact', backref='scans_3d')
    generated_by = db.relationship('User', backref='generated_3d_models')

class PhotoGallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_path = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), default='geral')  # geral, equipe, evento
    event_name = db.Column(db.String(200))  # Nome do evento se categoria for 'evento'
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship
    created_by = db.relationship('User', backref='photo_galleries')


class UserSession(db.Model):
    """Track user sessions for monitoring and analytics"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(100), unique=True, nullable=False)
    
    # Session timing
    login_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    logout_at = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Session metadata
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    # Session status
    is_active = db.Column(db.Boolean, default=True)
    logout_type = db.Column(db.String(50))  # manual, expired, forced
    
    # Relationship
    user = db.relationship('User', backref='sessions')
    
    @property
    def duration_seconds(self):
        """Calculate session duration in seconds"""
        end_time = self.logout_at or datetime.utcnow()
        return int((end_time - self.login_at).total_seconds())
    
    @property
    def duration_formatted(self):
        """Format duration as human-readable string"""
        seconds = self.duration_seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"
