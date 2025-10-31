from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"autocomplete": "email"})
    password = PasswordField('Senha', validators=[DataRequired()], render_kw={"autocomplete": "current-password"})

class RegisterForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=64)], render_kw={"autocomplete": "username"})
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"autocomplete": "email"})
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)], render_kw={"autocomplete": "new-password"})
    
    # Account type
    account_type = SelectField('Tipo de Conta', choices=[
        ('', 'Selecione o tipo de conta'),
        ('profissional', 'Conta Profissional'),
        ('universitaria', 'Conta Universitária'),
        ('estudante', 'Conta Estudante')
    ], validators=[DataRequired()])
    
    # Academic information (conditional - for students and university accounts)
    university = SelectField('Faculdade', choices=[
        ('', 'Selecione a faculdade'),
        
        ('Brasil', [
            ('USP', 'USP'),
            ('UNICAMP', 'UNICAMP'),
            ('UFRJ', 'UFRJ'),
            ('UnB', 'UnB'),
            ('UFMG', 'UFMG'),
            ('UFPA', 'UFPA'),
            ('UFSCar', 'UFSCar'),
            ('UFRGS', 'UFRGS'),
            ('PUC-SP', 'PUC-SP'),
            ('PUC-Rio', 'PUC-Rio'),
            ('UFPE', 'UFPE'),
            ('UFBA', 'UFBA')
        ]),
        
        ('Países Americanos', [
            ('Harvard', 'Harvard University'),
            ('Stanford', 'Stanford University'),
            ('UC Berkeley', 'University of California – Berkeley'),
            ('UChicago', 'University of Chicago'),
            ('UNAM', 'UNAM'),
            ('Tec Monterrey', 'Tecnológico de Monterrey'),
            ('McGill', 'McGill University'),
            ('Toronto', 'University of Toronto')
        ]),
        
        ('Europa', [
            ('Oxford', 'University of Oxford'),
            ('Cambridge', 'University of Cambridge'),
            ('UCL', 'University College London'),
            ('Complutense', 'Universidad Complutense de Madrid'),
            ('Barcelona', 'Universidad de Barcelona'),
            ('Sorbonne', 'Sorbonne Université'),
            ('EHESS', 'École des Hautes Études en Sciences Sociales')
        ]),
        
        ('custom', 'Outra (digitar manualmente)')
    ], validators=[Optional()])
    
    university_custom = StringField('Digite o nome da faculdade', validators=[Optional(), Length(max=200)])
    course = StringField('Curso/Área de estudo', validators=[Optional(), Length(max=200)])
    entry_year = IntegerField('Ano de entrada', validators=[Optional()])
    institution_type = SelectField('Tipo de instituição', choices=[
        ('', 'Selecione'),
        ('publica', 'Pública'),
        ('privada', 'Privada')
    ], validators=[Optional()])
    city = StringField('Cidade', validators=[Optional(), Length(max=100)])
    state = StringField('Estado', validators=[Optional(), Length(max=100)])
    country = StringField('País', validators=[Optional(), Length(max=100)])

class ArtifactForm(FlaskForm):
    name = StringField('Nome do Artefato', validators=[DataRequired(), Length(max=200)])
    code = StringField('Código do Artefato', validators=[Length(max=50)])
    discovery_date = DateField('Data de Descoberta', validators=[Optional()])
    origin_location = StringField('Local de Origem', validators=[Length(max=300)])
    archaeological_site = StringField('Sítio Arqueológico', validators=[Length(max=300)])
    artifact_type = SelectField('Tipo de Artefato', choices=[
        ('ceramica', 'Cerâmica'),
        ('litico', 'Lítico'),
        ('metal', 'Metal'),
        ('osso', 'Osso'),
        ('madeira', 'Madeira'),
        ('textil', 'Têxtil'),
        ('vidro', 'Vidro'),
        ('outro', 'Outro')
    ])
    conservation_state = SelectField('Estado de Conservação', choices=[
        ('excelente', 'Excelente'),
        ('bom', 'Bom'),
        ('regular', 'Regular'),
        ('ruim', 'Ruim'),
        ('pessimo', 'Péssimo')
    ])
    
    # Campos de localização arqueológica
    depth = StringField('Profundidade', validators=[Length(max=50)])
    level = StringField('Nível Estratigráfico', validators=[Length(max=100)])
    coordinates = StringField('Coordenadas', validators=[Length(max=200)])
    
    observations = TextAreaField('Observações')
    photo = FileField('Foto', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens são permitidas!')])
    model_3d = FileField('Modelo 3D', validators=[FileAllowed(['obj', 'ply', 'stl', 'fbx'], 'Apenas modelos 3D são permitidos!')])

class ProfessionalForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    age = IntegerField('Idade', validators=[Optional()])
    specialization = StringField('Especialização', validators=[Length(max=200)])
    description = TextAreaField('Descrição')
    experience = TextAreaField('Experiência')
    profile_photo = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens são permitidas!')])

class TransportForm(FlaskForm):
    artifact_id = SelectField('Artefato', coerce=int, validators=[DataRequired()])
    origin_location = StringField('Local de Origem', validators=[DataRequired(), Length(max=300)])
    destination_location = StringField('Local de Destino', validators=[DataRequired(), Length(max=300)])
    transport_date = DateField('Data de Transporte', validators=[Optional()])
    responsible_person = StringField('Responsável', validators=[Length(max=100)])
    status = SelectField('Status', choices=[
        ('pendente', 'Pendente'),
        ('em_transito', 'Em Trânsito'),
        ('concluido', 'Concluído')
    ])
    notes = TextAreaField('Observações')

class Scanner3DForm(FlaskForm):
    artifact_id = SelectField('Artefato', coerce=int, validators=[DataRequired()])
    scanner_type = StringField('Tipo de Scanner', validators=[Length(max=100)])
    resolution = StringField('Resolução', validators=[Length(max=50)])
    scan_file = FileField('Arquivo do Scan', validators=[FileAllowed(['obj', 'ply', 'stl', 'fbx'], 'Apenas arquivos 3D são permitidos!')])
    notes = TextAreaField('Observações')

class AdminUserForm(FlaskForm):
    user_id = SelectField('Usuário', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Usuário Ativo')
    is_admin = BooleanField('Administrador')

class PhotoGalleryForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Descrição')
    category = SelectField('Categoria', choices=[
        ('geral', 'Foto Geral'),
        ('equipe', 'Foto da Equipe'),
        ('evento', 'Foto de Evento')
    ], default='geral')
    event_name = StringField('Nome do Evento', validators=[Length(max=200)])
    image = FileField('Imagem', validators=[DataRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens são permitidas!')])
    is_published = BooleanField('Publicar no Mural')
