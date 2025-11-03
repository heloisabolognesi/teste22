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

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer)
    specialization = db.Column(db.String(200))
    description = db.Column(db.Text)
    experience = db.Column(db.Text)
    profile_photo = db.Column(db.String(255))
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
    
    # Relationship
    artifact = db.relationship('Artifact', backref='scans_3d')

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
