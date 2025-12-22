import os
import logging
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel, gettext, ngettext
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from translations_acervo_catalog import ACERVO_CATALOG_TRANSLATIONS

# Configure logging (adjust for production)
log_level = logging.DEBUG if os.environ.get('FLASK_ENV') != 'production' else logging.INFO
logging.basicConfig(level=log_level)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "laari-archaeological-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
database_url = os.environ.get("DATABASE_URL", "sqlite:///laari.db")

# Railway PostgreSQL URL fix
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url.startswith("sqlite"):
    database_url += "?charset=utf8mb4"
    
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {"charset": "utf8mb4"} if database_url.startswith("sqlite") else {}
}

# Configure upload settings (Replit-optimized)
upload_folder = os.path.join(os.getcwd(), 'static', 'uploads')
os.makedirs(upload_folder, exist_ok=True)
# Create all upload subdirectories
upload_subdirs = ['photos', '3d_models', 'profiles', '3d_scans', 'gallery']
for subdir in upload_subdirs:
    os.makedirs(os.path.join(upload_folder, subdir), exist_ok=True)

app.config['UPLOAD_FOLDER'] = upload_folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Disable cache in development for immediate updates
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Add cache control headers
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# Initialize Babel
babel = Babel()
babel.init_app(app)

# Supported languages
LANGUAGES = {
    'pt': 'Português',
    'en': 'English', 
    'es': 'Español',
    'fr': 'Français'
}

def get_locale():
    # 1. If user has selected a language, use it
    if 'language' in session:
        return session['language']
    # 2. Otherwise try to guess from browser
    return request.accept_languages.best_match(LANGUAGES.keys()) or 'pt'


# Configure Babel
app.config['LANGUAGES'] = LANGUAGES
app.config['BABEL_DEFAULT_LOCALE'] = 'pt'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'

# Simple translation function for demo (replacing full Babel)
def simple_translate(text, lang=None):
    if not lang:
        lang = session.get('language', 'pt')
    
    # Simple translations dictionary
    translations = {
        'en': {
            'Bem-vindo': 'Welcome',
            'Pesquisar por Sítio Arqueológico': 'Search by Archaeological Site',
            'Pesquisar': 'Search',
            'Buscar': 'Search',
            'Sítio Arqueológico': 'Archaeological Site',
            'Bem-vindo ao sistema de gestão arqueológica': 'Welcome to the archaeological management system',
            'Artefatos Catalogados': 'Cataloged Artifacts',
            'Profissionais Cadastrados': 'Registered Professionals',
            'Transportes Pendentes': 'Pending Transports',
            'Módulos Principais': 'Main Modules',
            'Acesso': 'Access',
            'Consulta organizada de todos os itens catalogados no sistema.': 'Organized consultation of all cataloged items in the system.',
            'Sistema completo de registro e catalogação de artefatos.': 'Complete artifact registration and cataloging system.',
            'Integração com tecnologia de digitalização tridimensional.': 'Integration with three-dimensional scanning technology.',
            'Diretório completo de arqueólogos e especialistas.': 'Complete directory of archaeologists and specialists.',
            'Controle detalhado do inventário arqueológico.': 'Detailed control of archaeological inventory.',
            'Controle e rastreamento da movimentação de itens.': 'Control and tracking of item movement.',
            'Acessar Acervo': 'Access Collection',
            'Gerenciar Catalogação': 'Manage Cataloging',
            'Acessar Scanner': 'Access Scanner',
            'Ver Profissionais': 'View Professionals',
            'Gerenciar Inventário': 'Manage Inventory',
            'Controlar Transporte': 'Control Transport',
            'Painel Administrativo': 'Administrative Panel',
            'Você possui privilégios de administrador neste sistema.': 'You have administrator privileges in this system.',
            'Acessar Administração': 'Access Administration',
            'Catalogação de Artefatos': 'Artifact Cataloging',
            'Gerencie e visualize todos os artefatos catalogados': 'Manage and view all cataloged artifacts',
            'Catalogar Novo': 'Catalog New',
            'Nenhum Artefato Catalogado': 'No Artifacts Cataloged',
            'Comece catalogando seu primeiro artefato no sistema L.A.A.R.I': 'Start by cataloging your first artifact in the L.A.A.R.I system',
            'Catalogar Primeiro Artefato': 'Catalog First Artifact',
            'Profissionais da Região': 'Regional Professionals',
            'Transporte de Artefatos': 'Artifact Transport',
            'Laboratório e Acervo Arqueológico Remoto Integrado': 'Remote Integrated Archaeological Laboratory and Collection',
            'Sistema completo de gestão arqueológica para centralizar documentação, catalogação, acervo e inventário, facilitando a comunicação entre equipes de campo e laboratório.': 'Complete archaeological management system to centralize documentation, cataloging, collection and inventory, facilitating communication between field and laboratory teams.',
            'Entrar': 'Login',
            'Acesse sua conta existente no sistema L.A.A.R.I': 'Access your existing L.A.A.R.I system account',
            'Fazer Login': 'Sign In',
            'Cadastrar': 'Register',
            'Crie uma nova conta para acessar o sistema': 'Create a new account to access the system',
            'Criar Conta': 'Create Account',
            'Funcionalidades Principais': 'Main Features',
            'Acervo Digital': 'Digital Collection',
            'Consulta organizada de todos os itens catalogados': 'Organized consultation of all cataloged items',
            'Catalogação': 'Cataloging',
            'Sistema completo de registro de artefatos': 'Complete artifact registration system',
            'Scanner 3D': '3D Scanner',
            'Modelo 3D': '3D Model',
            'Acessar Modelos': 'Access Models',
            'Integração com digitalização 3D': 'Integration with 3D digitization',
            'Profissionais': 'Professionals',
            'Diretório de arqueólogos da região': 'Directory of archaeologists in the region',
            'Inventário': 'Inventory',
            'Controle completo do inventário': 'Complete inventory control',
            'Transporte': 'Transport',
            'Rastreamento de movimentação': 'Movement tracking',
            'Dashboard': 'Dashboard',
            'Acervo': 'Collection',
            'Galeria': 'Gallery',
            'Idioma': 'Language',
            'Administração': 'Administration',
            'Gerenciar Galeria': 'Manage Gallery',
            'Sair': 'Logout',
            'Email': 'Email',
            'Senha': 'Password',
            'Entrar no L.A.A.R.I': 'Login to L.A.A.R.I',
            'Não possui uma conta?': 'Don\'t have an account?',
            'Cadastre-se aqui': 'Register here',
            'Voltar ao início': 'Back to home',
            'Nome de Usuário': 'Username',
            'Criar Conta no L.A.A.R.I': 'Create L.A.A.R.I Account',
            'Já possui uma conta?': 'Already have an account?',
            'Faça login aqui': 'Login here',
            'Galeria de Fotos': 'Photo Gallery',
            'Adicionar Foto': 'Add Photo',
            'Filtrar por:': 'Filter by:',
            'Todas': 'All',
            'Gerais': 'General',
            'Equipe': 'Team',
            'Eventos': 'Events',
            'Ver': 'View',
            'Geral': 'General',
            'Evento': 'Event',
            'Paginação da galeria': 'Gallery pagination',
            'Anterior': 'Previous',
            'Próxima': 'Next',
            'Galeria Vazia': 'Empty Gallery',
            'Não há fotos publicadas na galeria ainda.': 'There are no published photos in the gallery yet.',
            'Adicionar Primeira Foto': 'Add First Photo',
            'Carregando...': 'Loading...',
            'Carregando mais fotos...': 'Loading more photos...',
            'Mural de imagens arqueológicas, eventos e equipe': 'Archaeological images, events and team gallery',
            'Adicionar Foto': 'Add Photo',
            'Filtrar por:': 'Filter by:',
            'Todas': 'All',
            'Gerais': 'General',
            'Equipe': 'Team',
            'Eventos': 'Events',
            'Ver': 'View',
            'Paginação da galeria': 'Gallery pagination',
            'Anterior': 'Previous',
            'Próxima': 'Next',
            'Não há fotos na categoria': 'No photos in category',
            'ainda.': 'yet.',
            'Adicionar Primeira Foto': 'Add First Photo',
            'Conheca mais da nossa equipe': 'Learn more about our team',
            'Somos a equipe Tech Era, formada por alunos do 6º ao 9º ano do SESI AE Carvalho 415. Participamos da FIRST® LEGO® League (FLL), um torneio internacional de robótica que vai muito além da construção de robôs. Nosso objetivo é aprender, inovar e compartilhar conhecimento, sempre colocando em prática os valores que guiam a comunidade da FIRST.\n\nA missão da FIRST é inspirar jovens a se tornarem líderes e inovadores, usando a ciência e a tecnologia para transformar o futuro. Para isso, seguimos os Core Values, que nos lembram todos os dias que robótica é muito mais do que robôs:\n\nDescoberta: buscamos sempre aprender coisas novas.\nInovação: usamos a criatividade para resolver problemas reais.\nImpacto: aplicamos o que sabemos para melhorar nosso mundo.\nInclusão: trabalhamos juntos, respeitando e valorizando as diferenças.\nTrabalho em equipe: colaboramos e apoiamos uns aos outros.\nDiversão: celebramos cada conquista e aprendemos com cada desafio.\n\nMais do que competir, a Tech Era acredita que participar da FLL é uma forma de crescer, se preparar para o futuro e provar que tecnologia e cooperação caminham lado a lado.': 'We are the Tech Era team, formed by students from 6th to 9th grade at SESI AE Carvalho 415. We participate in FIRST® LEGO® League (FLL), an international robotics tournament that goes far beyond building robots. Our goal is to learn, innovate and share knowledge, always putting into practice the values that guide the FIRST community.\n\nFIRST\'s mission is to inspire young people to become leaders and innovators, using science and technology to transform the future. For this, we follow the Core Values, which remind us every day that robotics is much more than robots:\n\nDiscovery: we always seek to learn new things.\nInnovation: we use creativity to solve real problems.\nImpact: we apply what we know to improve our world.\nInclusion: we work together, respecting and valuing differences.\nTeamwork: we collaborate and support each other.\nFun: we celebrate every achievement and learn from every challenge.\n\nMore than competing, Tech Era believes that participating in FLL is a way to grow, prepare for the future and prove that technology and cooperation go hand in hand.'
        },
        'es': {
            'Bem-vindo': 'Bienvenido',
            'Pesquisar por Sítio Arqueológico': 'Buscar por Sitio Arqueológico',
            'Pesquisar': 'Buscar',
            'Buscar': 'Buscar',
            'Sítio Arqueológico': 'Sitio Arqueológico',
            'Bem-vindo ao sistema de gestão arqueológica': 'Bienvenido al sistema de gestión arqueológica',
            'Artefatos Catalogados': 'Artefactos Catalogados',
            'Profissionais Cadastrados': 'Profesionales Registrados',
            'Transportes Pendentes': 'Transportes Pendientes',
            'Módulos Principais': 'Módulos Principales',
            'Acesso': 'Acceso',
            'Consulta organizada de todos os itens catalogados no sistema.': 'Consulta organizada de todos los artículos catalogados en el sistema.',
            'Sistema completo de registro e catalogação de artefatos.': 'Sistema completo de registro y catalogación de artefactos.',
            'Integração com tecnologia de digitalização tridimensional.': 'Integración con tecnología de digitalización tridimensional.',
            'Diretório completo de arqueólogos e especialistas.': 'Directorio completo de arqueólogos y especialistas.',
            'Controle detalhado do inventário arqueológico.': 'Control detallado del inventario arqueológico.',
            'Controle e rastreamento da movimentação de itens.': 'Control y seguimiento del movimiento de artículos.',
            'Acessar Acervo': 'Acceder al Acervo',
            'Gerenciar Catalogação': 'Gestionar Catalogación',
            'Acessar Scanner': 'Acceder al Escáner',
            'Ver Profissionais': 'Ver Profesionales',
            'Gerenciar Inventário': 'Gestionar Inventario',
            'Controlar Transporte': 'Controlar Transporte',
            'Painel Administrativo': 'Panel Administrativo',
            'Você possui privilégios de administrador neste sistema.': 'Tienes privilegios de administrador en este sistema.',
            'Acessar Administração': 'Acceder a Administración',
            'Catalogação de Artefatos': 'Catalogación de Artefactos',
            'Gerencie e visualize todos os artefatos catalogados': 'Gestione y visualice todos los artefactos catalogados',
            'Catalogar Novo': 'Catalogar Nuevo',
            'Nenhum Artefato Catalogado': 'Ningún Artefacto Catalogado',
            'Comece catalogando seu primeiro artefato no sistema L.A.A.R.I': 'Comience catalogando su primer artefacto en el sistema L.A.A.R.I',
            'Catalogar Primeiro Artefato': 'Catalogar Primer Artefacto',
            'Profissionais da Região': 'Profesionales de la Región',
            'Transporte de Artefatos': 'Transporte de Artefactos',
            'Laboratório e Acervo Arqueológico Remoto Integrado': 'Laboratorio y Acervo Arqueológico Remoto Integrado',
            'Sistema completo de gestão arqueológica para centralizar documentação, catalogação, acervo e inventário, facilitando a comunicação entre equipes de campo e laboratório.': 'Sistema completo de gestión arqueológica para centralizar documentación, catalogación, acervo e inventario, facilitando la comunicación entre equipos de campo y laboratorio.',
            'Entrar': 'Ingresar',
            'Acesse sua conta existente no sistema L.A.A.R.I': 'Accede a tu cuenta existente en el sistema L.A.A.R.I',
            'Fazer Login': 'Iniciar Sesión',
            'Cadastrar': 'Registrarse',
            'Crie uma nova conta para acessar o sistema': 'Crea una nueva cuenta para acceder al sistema',
            'Criar Conta': 'Crear Cuenta',
            'Funcionalidades Principais': 'Funcionalidades Principales',
            'Acervo Digital': 'Acervo Digital',
            'Consulta organizada de todos os itens catalogados': 'Consulta organizada de todos los artículos catalogados',
            'Catalogação': 'Catalogación',
            'Sistema completo de registro de artefatos': 'Sistema completo de registro de artefactos',
            'Scanner 3D': 'Escáner 3D',
            'Modelo 3D': 'Modelo 3D',
            'Acessar Modelos': 'Acceder a Modelos',
            'Integração com digitalização 3D': 'Integración con digitalización 3D',
            'Profissionais': 'Profesionales',
            'Diretório de arqueólogos da região': 'Directorio de arqueólogos de la región',
            'Inventário': 'Inventario',
            'Controle completo do inventário': 'Control completo del inventario',
            'Transporte': 'Transporte',
            'Rastreamento de movimentação': 'Seguimiento de movimiento',
            'Dashboard': 'Panel',
            'Acervo': 'Acervo',
            'Galeria': 'Galería',
            'Idioma': 'Idioma',
            'Administração': 'Administración',
            'Gerenciar Galeria': 'Gestionar Galería',
            'Sair': 'Salir',
            'Email': 'Email',
            'Senha': 'Contraseña',
            'Entrar no L.A.A.R.I': 'Ingresar a L.A.A.R.I',
            'Não possui uma conta?': '¿No tienes una cuenta?',
            'Cadastre-se aqui': 'Regístrate aquí',
            'Voltar ao início': 'Volver al inicio',
            'Nome de Usuário': 'Nombre de Usuario',
            'Criar Conta no L.A.A.R.I': 'Crear Cuenta en L.A.A.R.I',
            'Já possui uma conta?': '¿Ya tienes una cuenta?',
            'Faça login aqui': 'Inicia sesión aquí',
            'Galeria de Fotos': 'Galería de Fotos',
            'Adicionar Foto': 'Agregar Foto',
            'Filtrar por:': 'Filtrar por:',
            'Todas': 'Todas',
            'Gerais': 'Generales',
            'Equipe': 'Equipo',
            'Eventos': 'Eventos',
            'Ver': 'Ver',
            'Geral': 'General',
            'Evento': 'Evento',
            'Paginação da galeria': 'Paginación de galería',
            'Anterior': 'Anterior',
            'Próxima': 'Siguiente',
            'Galeria Vazia': 'Galería Vacía',
            'Não há fotos publicadas na galeria ainda.': 'Aún no hay fotos publicadas en la galería.',
            'Adicionar Primeira Foto': 'Agregar Primera Foto',
            'Carregando...': 'Cargando...',
            'Carregando mais fotos...': 'Cargando más fotos...',
            'Mural de imagens arqueológicas, eventos e equipe': 'Galería de imágenes arqueológicas, eventos y equipo',
            'Adicionar Foto': 'Agregar Foto',
            'Filtrar por:': 'Filtrar por:',
            'Todas': 'Todas',
            'Gerais': 'Generales',
            'Equipe': 'Equipo',
            'Eventos': 'Eventos',
            'Ver': 'Ver',
            'Paginação da galeria': 'Paginación de galería',
            'Anterior': 'Anterior',
            'Próxima': 'Siguiente',
            'Não há fotos na categoria': 'No hay fotos en la categoría',
            'ainda.': 'aún.',
            'Adicionar Primeira Foto': 'Agregar Primera Foto',
            'Conheca mais da nossa equipe': 'Conoce más sobre nuestro equipo',
            'Somos a equipe Tech Era, formada por alunos do 6º ao 9º ano do SESI AE Carvalho 415. Participamos da FIRST® LEGO® League (FLL), um torneio internacional de robótica que vai muito além da construção de robôs. Nosso objetivo é aprender, inovar e compartilhar conhecimento, sempre colocando em prática os valores que guiam a comunidade da FIRST.\n\nA missão da FIRST é inspirar jovens a se tornarem líderes e inovadores, usando a ciência e a tecnologia para transformar o futuro. Para isso, seguimos os Core Values, que nos lembram todos os dias que robótica é muito mais do que robôs:\n\nDescoberta: buscamos sempre aprender coisas novas.\nInovação: usamos a criatividade para resolver problemas reais.\nImpacto: aplicamos o que sabemos para melhorar nosso mundo.\nInclusão: trabalhamos juntos, respeitando e valorizando as diferenças.\nTrabalho em equipe: colaboramos e apoiamos uns aos outros.\nDiversão: celebramos cada conquista e aprendemos com cada desafio.\n\nMais do que competir, a Tech Era acredita que participar da FLL é uma forma de crescer, se preparar para o futuro e provar que tecnologia e cooperação caminham lado a lado.': 'Somos el equipo Tech Era, formado por estudiantes de 6º a 9º grado de SESI AE Carvalho 415. Participamos en FIRST® LEGO® League (FLL), un torneo internacional de robótica que va mucho más allá de construir robots. Nuestro objetivo es aprender, innovar y compartir conocimiento, siempre poniendo en práctica los valores que guían a la comunidad FIRST.\n\nLa misión de FIRST es inspirar a los jóvenes a convertirse en líderes e innovadores, usando la ciencia y la tecnología para transformar el futuro. Para esto, seguimos los Core Values, que nos recuerdan todos los días que la robótica es mucho más que robots:\n\nDescubrimiento: siempre buscamos aprender cosas nuevas.\nInnovación: usamos la creatividad para resolver problemas reales.\nImpacto: aplicamos lo que sabemos para mejorar nuestro mundo.\nInclusión: trabajamos juntos, respetando y valorando las diferencias.\nTrabajo en equipo: colaboramos y nos apoyamos mutuamente.\nDiversión: celebramos cada logro y aprendemos de cada desafío.\n\nMás que competir, Tech Era cree que participar en FLL es una forma de crecer, prepararse para el futuro y demostrar que la tecnología y la cooperación van de la mano.'
        },
        'fr': {
            'Bem-vindo': 'Bienvenue',
            'Pesquisar por Sítio Arqueológico': 'Rechercher par Site Archéologique',
            'Pesquisar': 'Rechercher',
            'Buscar': 'Rechercher',
            'Sítio Arqueológico': 'Site Archéologique',
            'Bem-vindo ao sistema de gestão arqueológica': 'Bienvenue au système de gestion archéologique',
            'Artefatos Catalogados': 'Artefacts Catalogués',
            'Profissionais Cadastrados': 'Professionnels Enregistrés',
            'Transportes Pendentes': 'Transports en Attente',
            'Módulos Principais': 'Modules Principaux',
            'Acesso': 'Accès',
            'Consulta organizada de todos os itens catalogados no sistema.': 'Consultation organisée de tous les articles catalogués dans le système.',
            'Sistema completo de registro e catalogação de artefatos.': 'Système complet d\'enregistrement et de catalogage d\'artefacts.',
            'Integração com tecnologia de digitalização tridimensional.': 'Intégration avec la technologie de numérisation tridimensionnelle.',
            'Diretório completo de arqueólogos e especialistas.': 'Répertoire complet d\'archéologues et de spécialistes.',
            'Controle detalhado do inventário arqueológico.': 'Contrôle détaillé de l\'inventaire archéologique.',
            'Controle e rastreamento da movimentação de itens.': 'Contrôle et suivi du mouvement des articles.',
            'Acessar Acervo': 'Accéder à la Collection',
            'Gerenciar Catalogação': 'Gérer le Catalogage',
            'Acessar Scanner': 'Accéder au Scanner',
            'Ver Profissionais': 'Voir les Professionnels',
            'Gerenciar Inventário': 'Gérer l\'Inventaire',
            'Controlar Transporte': 'Contrôler le Transport',
            'Painel Administrativo': 'Panneau Administratif',
            'Você possui privilégios de administrador neste sistema.': 'Vous avez des privilèges d\'administrateur dans ce système.',
            'Acessar Administração': 'Accéder à l\'Administration',
            'Catalogação de Artefatos': 'Catalogage d\'Artefacts',
            'Gerencie e visualize todos os artefatos catalogados': 'Gérer et visualiser tous les artefacts catalogués',
            'Catalogar Novo': 'Cataloguer Nouveau',
            'Nenhum Artefato Catalogado': 'Aucun Artefact Catalogué',
            'Comece catalogando seu primeiro artefato no sistema L.A.A.R.I': 'Commencez par cataloguer votre premier artefact dans le système L.A.A.R.I',
            'Catalogar Primeiro Artefato': 'Cataloguer le Premier Artefact',
            'Profissionais da Região': 'Professionnels de la Région',
            'Transporte de Artefatos': 'Transport d\'Artefacts',
            'Laboratório e Acervo Arqueológico Remoto Integrado': 'Laboratoire et Collection Archéologique à Distance Intégré',
            'Sistema completo de gestão arqueológica para centralizar documentação, catalogação, acervo e inventário, facilitando a comunicação entre equipes de campo e laboratório.': 'Système complet de gestion archéologique pour centraliser la documentation, le catalogage, la collection et l\'inventaire, facilitant la communication entre les équipes de terrain et de laboratoire.',
            'Entrar': 'Se connecter',
            'Fazer Login': 'Connexion',
            'Cadastrar': 'S\'inscrire',
            'Criar Conta': 'Créer un compte',
            'Funcionalidades Principais': 'Fonctionnalités principales',
            'Acervo Digital': 'Collection numérique',
            'Catalogação': 'Catalogage',
            'Scanner 3D': 'Scanner 3D',
            'Modelo 3D': 'Modèle 3D',
            'Acessar Modelos': 'Accéder aux Modèles',
            'Profissionais': 'Professionnels',
            'Inventário': 'Inventaire',
            'Transporte': 'Transport',
            'Dashboard': 'Tableau de bord',
            'Acervo': 'Collection',
            'Galeria': 'Galerie',
            'Idioma': 'Langue',
            'Administração': 'Administration',
            'Gerenciar Galeria': 'Gérer la galerie',
            'Sair': 'Déconnexion',
            'Email': 'Email',
            'Senha': 'Mot de passe',
            'Nome de Usuário': 'Nom d\'utilisateur',
            'Galeria de Fotos': 'Galerie de photos',
            'Todas': 'Toutes',
            'Gerais': 'Générales',
            'Equipe': 'Équipe',
            'Eventos': 'Événements',
            'Ver': 'Voir',
            'Geral': 'Général',
            'Evento': 'Événement',
            'Anterior': 'Précédent',
            'Próxima': 'Suivant'
        }
    }
    
    for language in ['en', 'es', 'fr']:
        if language in ACERVO_CATALOG_TRANSLATIONS:
            translations[language].update(ACERVO_CATALOG_TRANSLATIONS[language])
    
    if lang in translations and text in translations[lang]:
        return translations[lang][text]
    return text

# Template context processor to make gettext available in templates
@app.context_processor
def inject_conf_vars():
    return {
        'LANGUAGES': LANGUAGES,
        'CURRENT_LANGUAGE': session.get('language', request.accept_languages.best_match(LANGUAGES.keys()) or 'pt'),
        '_': simple_translate,
        'ngettext': ngettext
    }

# Template filter to get proper image URL
@app.template_filter('image_url')
def image_url_filter(path, default='/static/images/default-placeholder.svg'):
    """
    Convert storage path/URL to a displayable image URL.
    Handles both Cloudinary URLs and local file paths.
    """
    if not path:
        return default
    
    # If it's already a full URL (Cloudinary), return as-is
    if path.startswith('http://') or path.startswith('https://'):
        return path
    
    # If it's a relative local path starting with 'uploads/', serve it
    if path.startswith('uploads/'):
        return f'/{path}'
    
    # For any other path, try to serve through storage route
    # But don't expose absolute paths - only allow relative paths
    if not path.startswith('/') and os.path.exists(path):
        return f'/{path}'
    
    # For legacy paths that might be stored incorrectly, try to extract filename
    if '/' in path:
        filename = path.split('/')[-1]
        for folder in ['uploads/profiles', 'uploads/photos', 'uploads/gallery', 'uploads/equipe', 'uploads/artefatos']:
            potential_path = f'{folder}/{filename}'
            if os.path.exists(potential_path):
                return f'/{potential_path}'
    
    return default

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create database tables and admin user
with app.app_context():
    # Import models
    import models
    db.create_all()
    
    # Create admin user if configured via environment variables
    from models import User
    from werkzeug.security import generate_password_hash
    
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if admin_email and admin_password:
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin_user = User(
                username=os.environ.get('ADMIN_USERNAME', 'Admin'),
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            logging.info("Admin user created from environment variables")
    
    # Create additional admin users from environment variables
    # Format: ADMIN_USERS_JSON='[{"username":"Name","email":"email@example.com","password":"pass"}]'
    import json
    admin_users_json = os.environ.get('ADMIN_USERS_JSON')
    
    if admin_users_json:
        try:
            additional_admins = json.loads(admin_users_json)
            for admin_data in additional_admins:
                existing_admin = User.query.filter_by(email=admin_data['email']).first()
                if not existing_admin:
                    new_admin = User(
                        username=admin_data['username'],
                        email=admin_data['email'],
                        password_hash=generate_password_hash(admin_data['password']),
                        is_admin=True
                    )
                    db.session.add(new_admin)
                    db.session.commit()
                    logging.info(f"Admin user {admin_data['username']} created")
        except json.JSONDecodeError:
            logging.error("Invalid ADMIN_USERS_JSON format")

# Import routes
import routes
