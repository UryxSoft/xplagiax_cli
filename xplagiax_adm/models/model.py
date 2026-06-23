"""
Copyright (c) 2024 - present URYX TECHNOLOGIES SRL
"""
from utils.connections import db
import bcrypt
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from itsdangerous import URLSafeTimedSerializer as Serializer
from utils.config import Config
from sqlalchemy import Enum,Index,Column, Integer
import uuid
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

# This Python class defines a model for users with various attributes such as email, password hash,
# name, avatar, institute, country, and activation status.
class Users(UserMixin, db.Model):
    __tablename__       = 'users'
    id                  = db.Column(db.Integer, primary_key = True) # primary keys are required by SQLAlchemy
    email               = db.Column(db.String(100), unique = True)
    _password_hash      = db.Column(db.String(255), nullable = True)
    hashCode            = db.Column(db.String(255), nullable = True)
    name                = db.Column(db.String(100),nullable = True)
    lastname            = db.Column(db.String(100),nullable = True)
    avatar              = db.Column(db.String(200), nullable = True)
    tokens              = db.Column(db.Text, nullable = True)
    institute           = db.Column(db.String(255), nullable = True)
    country             = db.Column(db.String(100), nullable = True)
    is_active           = db.Column(db.Boolean, default = False)
    token               = db.Column(db.String(32), unique = True)
    totp_secret         = db.Column(db.String(16), nullable=True)
    active_session      = db.Column(db.Boolean, default=False)
    confirmado          = db.Column(db.Boolean, default=False)
    folders             = db.relationship('Folder',backref='owner',lazy=True)
    files               = db.relationship('File',backref='owner',lazy=True)
    created_date        = db.Column(db.DateTime, default=datetime.utcnow)
    # Información de almacenamiento
    storage_plan_id = db.Column(db.Integer, db.ForeignKey('storage_plans.id'))
    used_storage_bytes = db.Column(db.BigInteger, default=0)  # Almacenamiento utilizado en bytes
    user_type  = db.Column(Enum('Starter', 'Individual', 'Institutes'),nullable=True)
    addon_subscriptions = db.relationship('UserAddonSubscription', backref='user', lazy=True)

    # Relaciones
    created_sessions = db.relationship('SubmissionSession', back_populates='professor', lazy='dynamic')
    student_submissions = db.relationship('StudentSubmission', back_populates='student', lazy='dynamic')

    
    def __init__(self, email, _password_hash, hashCode, name, lastname, avatar, tokens, institute, country, is_active, token,totp_secret, active_session, confirmado, storage_plan_id=None, used_storage_bytes=0,user_type = None):
        self.email = email
        self._password_hash = _password_hash
        self.hashCode = hashCode
        self.name = name
        self.lastname = lastname
        self.avatar = avatar
        self.tokens = tokens
        self.institute = institute
        self.country = country
        self.is_active = is_active
        self.token = token
        self.totp_secret = totp_secret
        self.active_session = active_session
        self.confirmado = confirmado
        self.storage_plan_id = storage_plan_id
        self.used_storage_bytes = used_storage_bytes
        self.user_type = user_type
    
    def get_total_storage_limit_bytes(self):
        """Calcular el límite total de almacenamiento en bytes (plan base + complementos)"""
        # Obtener almacenamiento base del plan
        base_storage_bytes = self.storage_plan.base_storage_mb * 1024 * 1024
        
        # Calcular almacenamiento adicional de complementos activos
        addon_storage_bytes = sum(
            subscription.addon.storage_mb * 1024 * 1024
            for subscription in self.addon_subscriptions
            if subscription.is_active
        )
        
        return base_storage_bytes + addon_storage_bytes
    
    def get_remaining_storage_bytes(self):
        """Calcular el almacenamiento restante en bytes"""
        return self.get_total_storage_limit_bytes() - self.used_storage_bytes
    
    def get_storage_usage_percentage(self):
        """Calcular el porcentaje de almacenamiento utilizado"""
        total = self.get_total_storage_limit_bytes()
        if total == 0:
            return 100  # Evitar división por cero
        return (self.used_storage_bytes / total) * 100
    
    def get_user_type(self):
        return self.user_type
    
    def can_upload_file(self, file_size_bytes):
        """Verificar si el usuario puede subir un archivo del tamaño especificado"""
        return file_size_bytes <= self.get_remaining_storage_bytes()
    
    def get_token(self, purpose, expires_sec=3600):
        """
        Genera un token JWT para un propósito concreto,
        por ejemplo 'confirm' o 'reset'.
        """
        s = Serializer(Config['SECRET_KEY'], expires_sec)
        return s.dumps({purpose: self.id}).decode('utf-8')

    @staticmethod
    def verify_token(token, purpose):
        """
        Verifica un token y devuelve el usuario si es válido,
        o None si es inválido o expirado.
        """
        s = Serializer(Config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return Users.query.get(data.get(purpose))
    
    def __repr__(self):
        return f'<User {self.email}>'
  
class Users_admin(UserMixin, db.Model):
    __tablename__ = 'users_admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Relationships
    ssh_sessions = db.relationship(
        'SSHSession', 
        backref='user',  # Cambiar a 'user' para consistencia
        lazy=True,
        foreign_keys='SSHSession.user_id'
    )
    # Indexes
    __table_args__ = (
        db.Index('idx_user_active_role', 'is_active', 'role'),
        db.Index('idx_user_created', 'created_at'),
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Método requerido por Flask-Login
    def get_id(self):
        return str(self.id)
    
    # Método estático para cargar usuario por ID
    @staticmethod
    def get(user_id):
        return Users_admin.query.get(int(user_id))
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'is_active': self.is_active
        }

class SSHSession(db.Model):
    __tablename__ = 'ssh_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users_admin.id'), nullable=False)  # Corregido: apunta a users_admin
    name = db.Column(db.String(100), nullable=False)
    hostname = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, default=22)
    username = db.Column(db.String(100), nullable=False)
    auth_type = db.Column(db.String(10), default='password')
    password_encrypted = db.Column(db.Text, nullable=True)
    key_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    connected_at = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hostname': self.hostname,
            'port': self.port,
            'username': self.username,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }

class SessionLog(db.Model):
    __tablename__ = 'session_logs'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('ssh_sessions.id'), nullable=False)
    command = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    exit_code = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'command': self.command,
            'output': self.output,
            'execution_time': self.execution_time,
            'exit_code': self.exit_code,
            'timestamp': self.timestamp.isoformat()
        }

class FileTransfer(db.Model):
    __tablename__ = 'file_transfers'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('ssh_sessions.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    remote_path = db.Column(db.String(500), nullable=False)
    transfer_type = db.Column(db.String(10), nullable=False)  # 'upload' or 'download'
    file_size = db.Column(db.BigInteger, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'filename': self.filename,
            'remote_path': self.remote_path,
            'transfer_type': self.transfer_type,
            'file_size': self.file_size,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
class ContainerStatus(db.Model):
    __tablename__ = 'container_status'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    container_id = db.Column(db.String(255), nullable=False, index=True)
    container_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    running = db.Column(db.Boolean, default=False, nullable=False)
    health = db.Column(db.String(50), nullable=True)
    cpu_usage = db.Column(db.Float, nullable=True)
    memory_usage = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<ContainerStatus {self.container_name}: {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'container_id': self.container_id,
            'container_name': self.container_name,
            'status': self.status,
            'running': self.running,
            'health': self.health,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
                     
class SubmissionSession(db.Model):
    __tablename__ = 'submission_sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    analysis_started = db.Column(db.Boolean, nullable=False, default=False)
    analysis_completed = db.Column(db.Boolean, nullable=False, default=False)
    forced_analysis = db.Column(db.Boolean, nullable=False, default=False)

    # Índices opcionales (por convención, puedes usar __table_args__)
    __table_args__ = (
        db.Index('idx_session_dates', 'start_date', 'end_date'),
        db.Index('idx_session_professor', 'professor_id'),
        db.Index('idx_session_status', 'analysis_started', 'analysis_completed'),
        {'comment': 'Sesiones de entrega creadas por profesores'}
    )

    # Relaciones (si tienes un modelo User)

    professor = db.relationship('Users', back_populates='created_sessions')

    def __init__(self, name, professor_id, start_date, end_date,
                 analysis_started=False, analysis_completed=False, forced_analysis=False):
        self.name = name
        self.professor_id = professor_id
        self.start_date = start_date
        self.end_date = end_date
        self.analysis_started = analysis_started
        self.analysis_completed = analysis_completed
        self.forced_analysis = forced_analysis
        
class StudentSubmission(db.Model):
    __tablename__ = 'student_submissions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    session_id = db.Column(db.Integer, db.ForeignKey('submission_sessions.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    email = db.Column(db.String(120), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)

    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    professor_comment = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('session_id', 'email', name='unique_submission_per_session_email'),
        db.Index('idx_submission_email', 'email'),
        db.Index('idx_submission_date', 'uploaded_at'),
        {'comment': 'Documentos entregados por estudiantes'}
    )

    # Relaciones
    session = db.relationship('SubmissionSession', backref=db.backref('student_submissions', cascade='all, delete-orphan'))
    student = db.relationship('Users', back_populates='student_submissions')

    def __init__(self, session_id, email, file_path, file_name, file_size, mime_type, student_id=None, professor_comment=None):
        self.session_id = session_id
        self.email = email
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.mime_type = mime_type
        self.student_id = student_id
        self.professor_comment = professor_comment

# This Python class defines a model for a Country entity with attributes for id, country name, and
# creation date.
class Country(db.Model):
    __tablename__  = 'Country'
    id           = db.Column(db.Integer, primary_key = True)
    country      = db.Column(db.String(100), nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,country):
        self.country  = country
        
class ProvinceState(db.Model):
    __tablename__ = 'Province_state'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    province_state = db.Column(db.String(255), nullable=True)
    country_id = db.Column(db.Integer, db.ForeignKey('Country.id'), nullable=True)
    #user_id = db.Column(db.Integer, db.ForeignKey('users_admin.id'), nullable=True)
    created_date = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relaciones (opcional - puedes definirlas si tienes los otros modelos)
    # country = db.relationship('Country', backref='provinces')
    # user = db.relationship('UserAdmin', backref='created_provinces')
    
    def __init__(self, province_state=None, country_id=None):
        self.province_state = province_state
        self.country_id = country_id
        #self.user_id = user_id
        
class Institution(db.Model):
    __tablename__  = 'Institution'
    id                = db.Column(db.Integer, primary_key = True)
    institution       = db.Column(db.String(255), nullable=True)
    institution_type  = db.Column(db.Integer, nullable=False)
    city_id           = db.Column(db.Integer, nullable=False)
    country_id        = db.Column(db.Integer, nullable=False)
    created_date      = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,institution,country_id):
        self.institution  = institution
        self.country_id   = country_id
        
class Institution_type(db.Model):
    __tablename__  = 'Institution_type'
    id               = db.Column(db.Integer, primary_key = True)
    institution_type = db.Column(db.String(255), nullable=True)
    created_date     = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,institution_type):
        self.institution_type  = institution_type
     
class City (db.Model):
    __tablename__  = 'City'
    id               = db.Column(db.Integer, primary_key = True)
    city             = db.Column(db.String(255), nullable=True)
    state_id         = db.Column(db.Integer, nullable=True)
    created_date     = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,city,state_id):
        self.city      = city
        self.state_id  = state_id

# This class defines a model for storing documents with various attributes such as title, author,
# content, and metadata.
class Documents(db.Model):
    __tablename__  = 'Documents'
    id             =  db.Column(db.Integer, primary_key = True)
    title          = db.Column(db.String(255), nullable=True)
    author         = db.Column(db.String(255), nullable=True)
    content        = db.Column(db.Text, nullable=True)
    rena           = db.Column(db.String(255), nullable=True)
    theme          = db.Column(db.String(55), nullable=True)
    doctype_id     = db.Column(db.Integer, nullable=True)
    country_id     = db.Column(db.Integer, nullable=True)
    institution_id = db.Column(db.Integer, nullable=True)
    lenguage_id    = db.Column(db.Integer, nullable=True)
    user_id        = db.Column(db.Integer, nullable=True)
    created_date   = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,title,author,content,rena,theme,doctype_id,country_id,institution_id,lenguage_id, user_id):
        self.title           = title
        self.author          = author
        self.content         = content
        self.rena            = rena
        self.theme           = theme
        self.doctype_id      = doctype_id
        self.country_id      = country_id
        self.institution_id  = institution_id
        self.lenguage_id     = lenguage_id
        self.user_id         = user_id

class Doctype(db.Model):
    __tablename__  = 'Doctype'
    id           = db.Column(db.Integer, primary_key = True)
    doctype      = db.Column(db.String(4), nullable=True)
    user_id      = db.Column(db.Integer, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
  
    def serialize(self):
        return {
            'id': self.id,
            'doctype': self.doctype,
            'user_id': self.user_id,
            'created_date': self.created_date
            # Agrega otros atributos que desees serializar
        }

    def __init__(self,doctype, user_id):
        self.doctype  = doctype
        self.user_id  = user_id

class History_db_analysis(db.Model):
    __tablename__ = 'History_db_analysis'
    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_percent    = db.Column(db.DECIMAL, nullable=True)
    aproved_percent  = db.Column(db.DECIMAL, nullable=True)
    db_percent       = db.Column(db.DECIMAL, nullable=True)
    ai_percent       = db.Column(db.DECIMAL, nullable=True)
    web_percent      = db.Column(db.DECIMAL, nullable=True)
    img_percent      = db.Column(db.DECIMAL, nullable=True)
    paragraph        = db.Column(db.Integer, nullable=True)
    user_id          = db.Column(db.Integer, nullable=True)
    created_date     = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self,total_percent, aproved_percent,db_percent,ai_percent,web_percent,img_percent, user_id):
        self.total_percent   = total_percent
        self.aproved_percent = aproved_percent
        self.db_percent      = db_percent
        self.ai_percent      = ai_percent
        self.web_percent     = web_percent
        self.img_percent     = img_percent
        self.user_id         = user_id
        
class History_ai_analysis(db.Model):
    __tablename__      = 'History_ai_analysis'
    id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_percent      = db.Column(db.DECIMAL, nullable=True)
    ai_percent         = db.Column(db.DECIMAL, nullable=True)
    probablyai_percent = db.Column(db.DECIMAL, nullable=True)
    paragraph          = db.Column(db.Integer, nullable=True)
    perplexity         = db.Column(db.DECIMAL, nullable=True)
    burstiness         = db.Column(db.DECIMAL, nullable=True)
    ai                 = db.Column(db.DECIMAL, nullable=True)
    human              = db.Column(db.DECIMAL, nullable=True)
    writen_by          = db.Column(db.String(25), nullable=True)
    user_id            = db.Column(db.Integer, nullable=True)
    created_date       = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self,total_percent, ai_percent,probablyai_percent,paragraph,perplexity,burstiness,ai,human,writen_by,user_id):
        self.total_percent      = total_percent
        self.ai_percent         = ai_percent
        self.probablyai_percent = probablyai_percent
        self.paragraph          = paragraph
        self.perplexity         = perplexity
        self.burstiness         = burstiness
        self.ai                 = ai
        self.human              = human
        self.writen_by          = writen_by
        self.user_id            = user_id
        
class DocumentAnalysis(db.Model):
    __tablename__ = 'document_analyses'
    
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    analysis_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, nullable=False)
    
    # Metadata del documento
    title = db.Column(db.Text)
    author = db.Column(db.String(500))
    creator = db.Column(db.String(500))
    producer = db.Column(db.String(500))
    subject = db.Column(db.Text)
    keywords = db.Column(db.Text)
    format = db.Column(db.String(100))
    creation_date = db.Column(db.String(100))
    mod_date = db.Column(db.String(100))
    encryption = db.Column(db.String(100))
    trapped = db.Column(db.String(100))
    
    # Información del documento
    pages = db.Column(db.Integer)
    language = db.Column(db.String(10))
    success = db.Column(db.Boolean, default=True)
    
    # Resumen del análisis
    total_paragraphs = db.Column(db.Integer)
    human_count = db.Column(db.Integer)
    ai_count = db.Column(db.Integer)
    average_confidence = db.Column(db.Float)
    
    # Información del preview
    preview_success = db.Column(db.Boolean)
    preview_page_count = db.Column(db.Integer)
    full_preview_path = db.Column(db.Text)
    preview_dir = db.Column(db.Text)
    
    # JSON fields para datos complejos
    annotations = db.Column(db.JSON)  # Lista de anotaciones
    images = db.Column(db.JSON)       # Lista de rutas de imágenes
    urls = db.Column(db.JSON)         # Lista de URLs encontradas
    preview_page_files = db.Column(db.JSON)  # Lista de archivos de páginas del preview
    
    # Relaciones
    classified_paragraphs = db.relationship("ClassifiedParagraph", back_populates="analysis", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DocumentAnalysis(id={self.id}, analysis_id='{self.analysis_id}', title='{self.title}')>"

class ClassifiedParagraph(db.Model):
    __tablename__ = 'classified_paragraphs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id = db.Column(db.String(36), db.ForeignKey('document_analyses.analysis_id'), nullable=False)
    
    # Posición en el documento
    page_number = db.Column(Integer, nullable=False)
    paragraph_number = db.Column(Integer, nullable=False)
    
    # Contenido
    text = db.Column(db.Text, nullable=False)
    
    # Clasificación
    is_human = db.Column(db.Boolean, nullable=False)
    human_probability = db.Column(db.Float, nullable=False)
    ai_probability = db.Column(db.Float, nullable=False)
    
    # Modelo que hizo la predicción (puede ser null)
    predicted_model = db.Column(db.String(100))
    
    # Puntuaciones por modelo (JSON)
    model_scores = db.Column(db.JSON)
    
    # Confianza final
    final_confidence = db.Column(db.Float, nullable=False)
    
    # Relación
    analysis = db.relationship("DocumentAnalysis", back_populates="classified_paragraphs")
    
    def __repr__(self):
        return f"<ClassifiedParagraph(id={self.id}, page={self.page_number}, paragraph={self.paragraph_number}, is_human={self.is_human})>"
        
class StoragePlan(db.Model):
    __tablename__ = 'storage_plans'
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(50), nullable = False,unique = True)
    base_storage_mb = db.Column(db.Integer, nullable = False) #Almancenamiento base MB
    description     = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)  # en lugar de is_activate
    
    users = db.relationship('Users', backref='storage_plan', lazy=True)
    
    def __repr__(self):
        return f'<StoragePlan {self.name}>'
    
class StorageAddon(db.Model):
    __tablename__ = 'storage_addons'
    id                 = db.Column(db.Integer, primary_key=True)
    name               = db.Column(db.String(50), nullable = False)
    storage_mb         = db.Column(db.Integer, nullable = False) #Almancenamiento base MB
    price_monthly_usd  = db.Column(db.Float, nullable = False)
    applicable_plan_id = db.Column(db.Integer,db.ForeignKey('storage_plans.id'))
    is_active = db.Column(db.Boolean, default=True)  # en lugar de is_activate
    
    applicable_plan = db.relationship('StoragePlan', backref = 'addons')
    
    subscriptions = db.relationship('UserAddonSubscription', backref = 'addon', lazy = True)
    
    def __repr__(self):
        return f'<StorageAddon {self.name}>'
    
class UserAddonSubscription(db.Model):
    __tablename__ = 'user_addon_subscriptions'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer,db.ForeignKey('users.id'), nullable = False) 
    addon_id        = db.Column(db.Integer,db.ForeignKey('storage_addons.id'), nullable = False) 
    start_date      = db.Column(db.DateTime, default = datetime.utcnow)
    expiry_date     = db.Column(db.DateTime)
    is_active       = db.Column(db.Boolean, default = True)
    auto_renew      = db.Column(db.Boolean, default = True)
    
    def __repr__(self):
        return f'<UserAddonSubscription {self.user_id}--{self.addon_id}>'   
    
# Nuevo modelo de Folder para trabajar con tu clase Users
class Folder(db.Model):
    __tablename__ = 'folders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_shared = db.Column(db.Boolean, default=False)
    
    # Relación auto-referencial para subcarpetas
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    # Relación con archivos
    files = db.relationship('File', backref='folder', lazy=True)
    
    def __init__(self, name, path, user_id, parent_id=None, is_shared=False):
        self.name = name
        self.path = path
        self.user_id = user_id
        self.parent_id = parent_id
        self.is_shared = is_shared

# Modelo de File actualizado para trabajar con tu clase Users
class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    original_filename = db.Column(db.String(100), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    size = db.Column(db.BigInteger, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    minio_url = db.Column(db.String(255), nullable=False)
    
    def __init__(self, filename, original_filename, mime_type, size, user_id, minio_url, folder_id=None):
        self.filename = filename
        self.original_filename = original_filename
        self.mime_type = mime_type
        self.size = size
        self.user_id = user_id
        self.minio_url = minio_url
        self.folder_id = folder_id
        
# This Python class defines a model for a language entity with attributes such as language name,
# language code, user ID, and creation date.
class Lenguage(db.Model):
    __tablename__  = 'Lenguage'
    id             = db.Column(db.Integer, primary_key = True)
    lenguage_name  = db.Column(db.String(50), nullable=True)
    lenguage       = db.Column(db.String(2), nullable=True)
    created_date   = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,lenguage_name,lenguage):
        self.lenguage_name  = lenguage_name
        self.lenguage       = lenguage
        
# This class represents a model for storing document-related data in a database with attributes such
# as user_id, language_id, accuracy, model, vectorizer, xtrain, update_date, and created_date.
class Docmodels(db.Model):
    __tablename__ = 'Docmodels'
    id             = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, nullable=True)
    user_id        = db.Column(db.Integer, nullable=True)
    lenguage_id    = db.Column(db.Integer, nullable=True)
    accuracy       = db.Column(db.String(50), nullable=True)
    model          = db.Column(db.String(255), nullable=True)
    vectorizer     = db.Column(db.String(255), nullable=True)
    xtrain         = db.Column(db.String(255), nullable=True)
    update_date    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_date   = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, institution_id = None,user_id = None,lenguage_id = None, accuracy=None, model=None, vectorizer=None, xtrain=None):
        self.institution_id  = institution_id
        self.user_id         = user_id
        self.lenguage_id     = lenguage_id
        self.accuracy        = accuracy
        self.model           = model
        self.vectorizer      = vectorizer
        self.xtrain          = xtrain

class ChangeHistory(db.Model):
    __tablename__ = 'change_history'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    action = db.Column(db.String(10))
    key = db.Column(db.String(255))
    value = db.Column(db.Text)
     
class SessionParticipant(db.Model):
    """Modelo para los participantes (estudiantes) de una sesión"""
    __tablename__ = 'session_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('submission_sessions.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    access_token = db.Column(db.String(64), unique=True, default=lambda: uuid.uuid4().hex)
    invitation_sent = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('session_id', 'email', name='unique_participant_per_session'),
    )
    
    def __repr__(self):
        return f'<SessionParticipant {self.email}>'

def document_upload_path(instance, filename):
    """Genera una ruta única para cada documento"""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('uploads', 'documents', str(instance.session_id), new_filename)

class DocumentVersion(db.Model):
    """Modelo para versiones anteriores de documentos"""
    __tablename__ = 'document_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('student_submissions.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<DocumentVersion {self.file_name} - {self.uploaded_at}>'

class ActivityLog(db.Model):
    """Modelo para registro de actividades y auditoría"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ActivityLog {self.action} - {self.entity_type}:{self.entity_id}>'
     
class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    display_name = db.Column(db.String(200), nullable=False)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # http, socket, redis, mysql, rabbitmq
    endpoint = db.Column(db.String(500), nullable=True)  # Para servicios HTTP
    timeout = db.Column(db.Integer, default=5)
    icon = db.Column(db.String(100), default='fas fa-server')
    
    # Credenciales (encriptadas)
    username = db.Column(db.String(100), nullable=True)
    password_encrypted = db.Column(db.Text, nullable=True)
    
    # Configuración adicional como JSON
    extra_config = db.Column(db.Text, nullable=True)  # JSON string para configuración adicional
    
    # Estados
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_monitored = db.Column(db.Boolean, default=True, index=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    service_logs = db.relationship('ServiceLog', backref='service', lazy=True, cascade='all, delete-orphan')
    service_stats = db.relationship('ServiceStats', backref='service', lazy=True, cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_service_active_monitored', 'is_active', 'is_monitored'),
        db.Index('idx_service_type', 'service_type'),
        db.Index('idx_service_host_port', 'host', 'port'),
    )
    
    def get_extra_config(self):
        """Obtener configuración adicional como diccionario"""
        if self.extra_config:
            try:
                return json.loads(self.extra_config)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_extra_config(self, config_dict):
        """Establecer configuración adicional desde diccionario"""
        if config_dict:
            self.extra_config = json.dumps(config_dict)
        else:
            self.extra_config = None
    
    def to_dict(self):
        """Convertir a diccionario para JSON"""
        extra_config = self.get_extra_config()
        
        result = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'host': self.host,
            'port': self.port,
            'type': self.service_type,
            'endpoint': self.endpoint,
            'timeout': self.timeout,
            'icon': self.icon,
            'username': self.username,
            'is_active': self.is_active,
            'is_monitored': self.is_monitored,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Añadir configuración extra
        result.update(extra_config)
        
        return result
    
    def to_config_dict(self):
        """Convertir a formato compatible con el sistema de monitoreo"""
        config = {
            'name': self.display_name,
            'host': self.host,
            'port': self.port,
            'type': self.service_type,
            'timeout': self.timeout,
            'icon': self.icon
        }
        
        if self.endpoint:
            config['endpoint'] = self.endpoint
            
        if self.username:
            config['user'] = self.username
            config['username'] = self.username
            
        # Añadir configuración extra
        extra_config = self.get_extra_config()
        config.update(extra_config)
        
        return config

class ServiceLog(db.Model):
    __tablename__ = 'service_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False, index=True)
    status = db.Column(db.Boolean, nullable=False, index=True)  # True = online, False = offline
    response_time = db.Column(db.Float, nullable=True)  # en segundos
    error_message = db.Column(db.Text, nullable=True)
    additional_data = db.Column(db.Text, nullable=True)  # JSON para datos extra (version, uptime, etc.)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_service_log_service_time', 'service_id', 'checked_at'),
        db.Index('idx_service_log_status_time', 'status', 'checked_at'),
    )
    
    def get_additional_data(self):
        """Obtener datos adicionales como diccionario"""
        if self.additional_data:
            try:
                return json.loads(self.additional_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_additional_data(self, data_dict):
        """Establecer datos adicionales desde diccionario"""
        if data_dict:
            self.additional_data = json.dumps(data_dict)
        else:
            self.additional_data = None
    
    def to_dict(self):
        additional_data = self.get_additional_data()
        
        return {
            'id': self.id,
            'service_id': self.service_id,
            'status': self.status,
            'response_time': self.response_time,
            'error_message': self.error_message,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None,
            **additional_data
        }

class ServiceStats(db.Model):
    __tablename__ = 'service_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False, index=True)
    
    # Estadísticas del día
    date = db.Column(db.Date, nullable=False, index=True)
    total_checks = db.Column(db.Integer, default=0)
    successful_checks = db.Column(db.Integer, default=0)
    failed_checks = db.Column(db.Integer, default=0)
    
    # Tiempos de respuesta
    avg_response_time = db.Column(db.Float, nullable=True)
    min_response_time = db.Column(db.Float, nullable=True)
    max_response_time = db.Column(db.Float, nullable=True)
    
    # Tiempos de downtime
    total_downtime = db.Column(db.Integer, default=0)  # en segundos
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint('service_id', 'date', name='uq_service_stats_service_date'),
        db.Index('idx_service_stats_date', 'date'),
    )
    
    @property
    def uptime_percentage(self):
        """Calcular porcentaje de uptime"""
        if self.total_checks == 0:
            return 0
        return (self.successful_checks / self.total_checks) * 100
    
    def to_dict(self):
        return {
            'id': self.id,
            'service_id': self.service_id,
            'date': self.date.isoformat() if self.date else None,
            'total_checks': self.total_checks,
            'successful_checks': self.successful_checks,
            'failed_checks': self.failed_checks,
            'uptime_percentage': self.uptime_percentage,
            'avg_response_time': self.avg_response_time,
            'min_response_time': self.min_response_time,
            'max_response_time': self.max_response_time,
            'total_downtime': self.total_downtime
        }
        
class ContactSale(db.Model):
    __tablename__ = 'contact_sales'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contact_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Información personal
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    
    # Información de empresa
    company_name = db.Column(db.String(200))
    job_title = db.Column(db.String(150))
    company_size = db.Column(db.String(50))  # "1-10", "11-50", "51-200", "200+", etc.
    industry = db.Column(db.String(100))
    website = db.Column(db.String(255))
    
    # Información del contacto
    service_interest = db.Column(db.String(100), nullable=False)  # SSH, Document Analysis, Other
    budget_range = db.Column(db.String(50))  # "$1k-$5k", "$5k-$10k", etc.
    timeline = db.Column(db.String(50))  # "Inmediato", "1-3 meses", "3-6 meses", etc.
    message = db.Column(db.Text, nullable=False)
    
    # Información de origen
    source = db.Column(db.String(100))  # "Website", "Social Media", "Referral", etc.
    utm_source = db.Column(db.String(100))
    utm_medium = db.Column(db.String(100))
    utm_campaign = db.Column(db.String(100))
    referrer_url = db.Column(db.String(500))
    
    # Estado y seguimiento
    status = db.Column(db.String(50), default='new')  # new, contacted, qualified, proposal, closed_won, closed_lost
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    assigned_to = db.Column(db.Integer, db.ForeignKey('users_admin.id'))  # Usuario asignado
    
    # Información adicional
    lead_score = db.Column(db.Integer, default=0)  # Puntuación del lead (0-100)
    estimated_value = db.Column(db.Float)  # Valor estimado del deal
    
    # Seguimiento de interacciones
    last_contact_date = db.Column(db.DateTime)
    next_followup_date = db.Column(db.DateTime)
    contact_attempts = db.Column(db.Integer, default=0)
    
    # Notas y comunicación
    internal_notes = db.Column(db.Text)  # Notas internas del equipo
    tags = db.Column(db.JSON)  # Tags para categorización
    
    # Información técnica
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    contacted_at = db.Column(db.DateTime)  # Primera vez que se contactó
    closed_at = db.Column(db.DateTime)  # Fecha de cierre (won/lost)
    
    # Relaciones
    assigned_user = db.relationship('Users_admin', backref='assigned_contacts', foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<ContactSale(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}', status='{self.status}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'email': self.email,
            'phone': self.phone,
            'company_name': self.company_name,
            'job_title': self.job_title,
            'company_size': self.company_size,
            'industry': self.industry,
            'website': self.website,
            'service_interest': self.service_interest,
            'budget_range': self.budget_range,
            'timeline': self.timeline,
            'message': self.message,
            'source': self.source,
            'utm_source': self.utm_source,
            'utm_medium': self.utm_medium,
            'utm_campaign': self.utm_campaign,
            'referrer_url': self.referrer_url,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'lead_score': self.lead_score,
            'estimated_value': self.estimated_value,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'next_followup_date': self.next_followup_date.isoformat() if self.next_followup_date else None,
            'contact_attempts': self.contact_attempts,
            'internal_notes': self.internal_notes,
            'tags': self.tags,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'country': self.country,
            'city': self.city,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'contacted_at': self.contacted_at.isoformat() if self.contacted_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'assigned_user_name': self.assigned_user.username if self.assigned_user else None
        }
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def days_since_created(self):
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return 0
    
    @property
    def days_since_last_contact(self):
        if self.last_contact_date:
            return (datetime.utcnow() - self.last_contact_date).days
        return None
    
    @property
    def is_overdue_followup(self):
        if self.next_followup_date:
            return datetime.utcnow() > self.next_followup_date
        return False
    
    def calculate_lead_score(self):
        """Calcular puntuación del lead basado en diferentes factores"""
        score = 0
        
        # Puntuación por empresa
        if self.company_name:
            score += 10
        
        # Puntuación por tamaño de empresa
        company_size_scores = {
            '1-10': 5,
            '11-50': 15,
            '51-200': 25,
            '200+': 35
        }
        score += company_size_scores.get(self.company_size, 0)
        
        # Puntuación por presupuesto
        budget_scores = {
            'Under $1k': 5,
            '$1k-$5k': 15,
            '$5k-$10k': 25,
            '$10k-$25k': 35,
            '$25k+': 45
        }
        score += budget_scores.get(self.budget_range, 0)
        
        # Puntuación por timeline
        timeline_scores = {
            'Inmediato': 30,
            '1-3 meses': 20,
            '3-6 meses': 10,
            '6+ meses': 5
        }
        score += timeline_scores.get(self.timeline, 0)
        
        # Puntuación por información proporcionada
        if self.phone:
            score += 5
        if self.website:
            score += 5
        if len(self.message) > 100:
            score += 10
        
        self.lead_score = min(score, 100)
        return self.lead_score

class ContactInteraction(db.Model):
    """Modelo para registrar interacciones con los contactos"""
    __tablename__ = 'contact_interactions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contact_id = db.Column(db.String(36), db.ForeignKey('contact_sales.contact_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users_admin.id'), nullable=False)
    
    # Tipo de interacción
    interaction_type = db.Column(db.String(50), nullable=False)  # email, call, meeting, note, status_change
    subject = db.Column(db.String(255))
    description = db.Column(db.Text)
    
    # Resultados
    outcome = db.Column(db.String(100))  # contacted, no_response, meeting_scheduled, etc.
    next_action = db.Column(db.String(255))
    
    # Metadata
    duration_minutes = db.Column(db.Integer)  # Para llamadas/reuniones
    scheduled_at = db.Column(db.DateTime)  # Para reuniones programadas
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relaciones
    contact = db.relationship('ContactSale', backref='interactions')
    user = db.relationship('Users_admin', backref='contact_interactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'interaction_type': self.interaction_type,
            'subject': self.subject,
            'description': self.description,
            'outcome': self.outcome,
            'next_action': self.next_action,
            'duration_minutes': self.duration_minutes,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
