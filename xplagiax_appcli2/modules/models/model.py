"""
Copyright (c) 2024 - present URYX TECHNOLOGIES SRL
"""
import logging
from settings.connections import db
from flask_login import UserMixin
from datetime import datetime, timedelta
from sqlalchemy import Integer, Index, Enum
from itsdangerous import URLSafeTimedSerializer as Serializer
from settings.config import Config
import secrets
import uuid
import os

logger = logging.getLogger(__name__)



# This Python class defines a model for users with various attributes such as email, password hash,
# Reemplaza tu clase Users con esta versión corregida:

class Users(db.Model, UserMixin):
    __tablename__                 = 'users'
    id                            = db.Column(db.Integer, primary_key = True)
    email                         = db.Column(db.String(100), unique = True)
    _password_hash                = db.Column(db.String(255), nullable = True)
    hashCode                      = db.Column(db.String(255), nullable = True)
    name                          = db.Column(db.String(100),nullable = True)
    lastname                      = db.Column(db.String(100),nullable = True)
    avatar                        = db.Column(db.String(200), nullable = True)
    tokens                        = db.Column(db.Text, nullable = True)
    institute                     = db.Column(db.String(255), nullable = True)
    country                       = db.Column(db.String(100), nullable = True)
    isactive                      = db.Column(db.Boolean, default = False)  # ✅ Campo principal
    token                         = db.Column(db.Text, unique = True)
    # TOTP (Google Authenticator / Authy). totp_secret guarda el secreto CIFRADO
    # (Fernet, ver totp_crypto.py) — nunca texto plano. String(16) se quedó corto
    # desde el día uno (pyotp.random_base32() ya genera 32 chars sin cifrar);
    # _ensure_totp_columns() en auth_routes_fixed.py la ensancha a VARCHAR(255)
    # en el primer request que usa 2FA, igual que el resto de auto-migraciones
    # del proyecto (db.create_all() no altera tablas existentes).
    totp_secret                   = db.Column(db.String(255), nullable=True)
    totp_enabled                  = db.Column(db.Boolean, default=False)
    totp_recovery_codes           = db.Column(db.Text, nullable=True)  # JSON: lista de hashes bcrypt, un solo uso c/u

    # Email OTP — segundo método de 2FA, independiente de TOTP (un usuario
    # puede tener uno, otro, o ambos activos — /2fa/verify-login acepta
    # cualquiera de los dos contra el mismo pending_token). El código nunca se
    # guarda en texto plano: solo su hash bcrypt + expiración, igual que los
    # recovery codes de TOTP. Ver email_otp_service.py.
    email_otp_enabled             = db.Column(db.Boolean, default=False)
    email_otp_code_hash           = db.Column(db.String(255), nullable=True)
    email_otp_expires_at          = db.Column(db.DateTime, nullable=True)

    # Session management
    active_session                = db.Column(db.Boolean, default=False)
    session_token                 = db.Column(db.String(128), nullable=True, unique=True)
    session_created_at            = db.Column(db.DateTime, nullable=True)
    last_login                    = db.Column(db.DateTime, nullable=True)
    
    # Email confirmation
    confirmed                     = db.Column(db.Boolean, default=False)
    confirmed_at                  = db.Column(db.DateTime, nullable=True)
    created_at                    = db.Column(db.DateTime, default=datetime.utcnow)
    
    folders                       = db.relationship('Folder', backref='user', lazy=True)
    files                         = db.relationship('File',backref='owner',lazy=True)
        
    # Storage and plan
    storage_plan_id               = db.Column(db.Integer, db.ForeignKey('storage_plans.id'))
    used_storage_bytes            = db.Column(db.BigInteger, default=0)
    user_type                     = db.Column(Enum('Starter','Scholar Suite' ,'Individual','Research Essentials' ,'Institutes'),nullable=True)
    addon_subscriptions           = db.relationship('UserAddonSubscription', backref='user', lazy=True)
    
    # Trial & subscription fields
    is_on_trial                   = db.Column(db.Boolean, default=False)
    trial_starts_at               = db.Column(db.DateTime, nullable=True)
    trial_ends_at                 = db.Column(db.DateTime, nullable=True)
    trial_notified                = db.Column(db.Boolean, default=False)
    
    # Subscription management
    subscription_provider         = db.Column(db.String(32), nullable=True)
    subscription_id               = db.Column(db.String(128), nullable=True)
    subscription_status           = db.Column(db.String(64), nullable=True)
    subscription_type             = db.Column(db.String(32), nullable=True)
    subscription_starts_at        = db.Column(db.DateTime, nullable=True)
    subscription_ends_at          = db.Column(db.DateTime, nullable=True)
    subscription_renewal_notified = db.Column(db.Boolean, default=False)
    
    # OAuth fields
    oauth_provider                = db.Column(db.String(32), nullable=True)
    oauth_id                      = db.Column(db.String(128), nullable=True)
    
    # Relationships
    created_sessions              = db.relationship('SubmissionSession', backref='professor', lazy='dynamic')
    student_submissions           = db.relationship('StudentSubmission', backref='student', lazy='dynamic')
    
    # Relación con preferencias
    preference                    = db.relationship('UserPreference', backref='user', uselist=False, cascade='all, delete-orphan')

    
    # Indexes for performance
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_session_token', 'session_token'),
        Index('idx_users_subscription_id', 'subscription_id'),
        Index('idx_users_trial_ends', 'trial_ends_at'),
        Index('idx_users_oauth', 'oauth_provider', 'oauth_id'),
    )
    
    def __init__(self, 
                    email,    
                    _password_hash  = None, 
                    hashCode  = None, 
                    name  = None, 
                    lastname  = None,
                    avatar  = None, 
                    tokens  = None, 
                    institute  = None,
                    country  = None,
                    isactive  = None, 
                    token  = None,
                    totp_secret = None,
                    totp_enabled = None,
                    totp_recovery_codes = None,
                    email_otp_enabled = None,
                    active_session = None,
                    confirmed = None,
                    confirmed_at = None,
                    storage_plan_id = None, 
                    used_storage_bytes = 0,
                    user_type = None,
                    oauth_provider = None,
                    oauth_id = None,
                ):
        
        self.email              = email
        self._password_hash     = _password_hash
        self.hashCode           = hashCode
        self.name               = name
        self.lastname           = lastname
        self.avatar             = avatar
        self.tokens             = tokens
        self.institute          = institute
        self.country            = country
        self.isactive           = isactive if isactive is not None else False
        self.token              = token
        self.totp_secret        = totp_secret
        self.totp_enabled       = totp_enabled if totp_enabled is not None else False
        self.totp_recovery_codes = totp_recovery_codes
        self.email_otp_enabled  = email_otp_enabled if email_otp_enabled is not None else False
        self.active_session     = active_session
        self.confirmed          = confirmed if confirmed is not None else False
        self.confirmed_at       = confirmed_at
        self.storage_plan_id    = storage_plan_id
        self.used_storage_bytes = used_storage_bytes
        self.user_type          = user_type or 'Starter'
        self.oauth_provider     = oauth_provider
        self.oauth_id           = oauth_id
        
        # ✅ Auto-confirm OAuth users
        if oauth_provider:
            self.confirmed = True
            self.confirmed_at = datetime.utcnow()
            self.isactive = True  # ✅ Usar isactive consistentemente

    @property
    def is_active(self):
        return bool(self.isactive)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        """Método requerido por Flask-Login - debe retornar string"""
        return str(self.id)

    # Session management
    def create_session(self):
        """Create a new session token and invalidate any existing session"""
        self.session_token = secrets.token_urlsafe(32)
        self.active_session = True
        self.session_created_at = datetime.utcnow()
        self.last_login = datetime.utcnow()
        return self.session_token

    def invalidate_session(self):
        """Invalidate current session"""
        self.session_token = None
        self.active_session = False
        self.session_created_at = None

    def is_session_valid(self, token):
        """Check if provided token matches current session"""
        if not self.active_session or not self.session_token:
            return False
        if not self.session_created_at:
            return False
        # Session expires after 30 days
        if datetime.utcnow() - self.session_created_at > timedelta(days=30):
            return False
        return self.session_token == token

    def get_total_storage_limit_bytes(self):
        """Calcular el límite total de almacenamiento en bytes"""
        if not self.storage_plan:
            return 1024 * 1024 * 1024 # Default to 1GB
        base_storage_bytes = self.storage_plan.base_storage_mb * 1024 * 1024
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
            return 100
        return (self.used_storage_bytes / total) * 100
    
    def get_user_type(self):
        return self.user_type
    
    def can_upload_file(self, file_size_bytes):
        """Verificar si el usuario puede subir un archivo"""
        return file_size_bytes <= self.get_remaining_storage_bytes()
    
    def get_token(self, purpose, expires_sec=3600):
        """Genera un token firmado que lleva su propia expiración en el payload."""
        secret_key = str(Config['default'].SECRET_KEY)
        s = Serializer(secret_key)
        return s.dumps({purpose: self.id, '_expires_sec': expires_sec})

    @staticmethod
    def verify_token(token, purpose):
        """Verifica el token respetando la expiración embebida en el payload."""
        secret_key = str(Config['default'].SECRET_KEY)
        s = Serializer(secret_key)
        try:
            # Primera pasada: cargar sin límite para extraer _expires_sec
            data = s.loads(token, max_age=30 * 24 * 3600)
            expires_sec = data.get('_expires_sec', 3600)
            # Segunda pasada: validar con la expiración real
            data = s.loads(token, max_age=expires_sec)
            user_id = data.get(purpose)
            if user_id:
                return Users.query.get(user_id)
        except Exception:
            return None
        return None
    
    def has_active_subscription(self):
        """Check if user has an active subscription (not trial)"""
        from datetime import datetime
        
        # If user is on trial, they don't have a real subscription yet
        if self.is_on_trial:
            return False
        
        # Check if user has subscription status as active
        if self.subscription_status == 'active':
            # Optionally check if subscription hasn't expired
            if self.subscription_ends_at:
                return datetime.utcnow() < self.subscription_ends_at
            return True
        
        # Check if user has a paid plan (not Starter which is free)
        if self.user_type and self.user_type in ['Scholar Suite' ,'Individual','Research Essentials', 'Institutes']:
            # Additional check: ensure they have a subscription_id if required
            if self.subscription_id:
                return self.subscription_status in ['active', 'trialing']

        return False

    def can_access_premium_features(self):
        """True if the user may use premium features: an active subscription, or a live (non-expired) trial."""
        if self.has_active_subscription():
            return True
        if self.is_on_trial and not self.is_trial_expired():
            return True
        return False

    def is_trial_expired(self):
        """Check if trial has expired"""
        from datetime import datetime
        
        if not self.is_on_trial or not self.trial_ends_at:
            return False
        
        return datetime.utcnow() > self.trial_ends_at
    
    def end_trial(self):
        """End trial and revert to free plan"""
        from datetime import datetime
        
        if not self.is_on_trial:
            return False
        
        try:
            # Revertir a plan gratuito
            starter_plan = StoragePlan.query.filter_by(name='Starter', is_active=True).first()
            if starter_plan:
                self.storage_plan_id = starter_plan.id
                self.user_type = 'Starter'
            
            # Limpiar datos de trial
            self.is_on_trial = False
            self.subscription_status = 'expired'
            self.trial_notified = False
            
            return True
        except Exception as e:
            logger.error("Error ending trial: %s", e)
            return False

    def is_trial_active(self):
        """Check if user has an active trial that hasn't expired"""
        from datetime import datetime
        
        if not self.is_on_trial:
            return False
        
        if not self.trial_ends_at:
            return False
        
        # Check if trial hasn't expired
        return datetime.utcnow() < self.trial_ends_at

    def start_trial(self, trial_days):
        """Start trial period for user"""
        from datetime import datetime, timedelta
        
        if self.is_on_trial:
            return False  # Already on trial
        
        if self.has_active_subscription():
            return False  # Already has subscription
        
        try:
            now = datetime.utcnow()
            self.is_on_trial = True
            self.trial_starts_at = now
            self.trial_ends_at = now + timedelta(days=trial_days)
            self.trial_notified = False
            
            # Set subscription info for trial
            self.subscription_status = 'trialing'
            self.subscription_starts_at = now
            self.subscription_ends_at = self.trial_ends_at
            
            return True
        except Exception as e:
            logger.error("Error starting trial: %s", e)
            return False

    def get_subscription_info(self):
        """Get subscription information for the user"""
        from datetime import datetime
        
        info = {
            'has_subscription': self.has_active_subscription(),
            'is_on_trial': self.is_on_trial,
            'is_trial_active': self.is_trial_active(),
            'user_type': self.user_type,
            'subscription_status': self.subscription_status,
            'trial_expired': self.is_trial_expired() if self.is_on_trial else False
        }
        
        if self.trial_ends_at:
            info['trial_ends_at'] = self.trial_ends_at.isoformat()
            info['trial_days_remaining'] = max(0, (self.trial_ends_at - datetime.utcnow()).days)
        
        if self.subscription_ends_at:
            info['subscription_ends_at'] = self.subscription_ends_at.isoformat()
        
        return info
        
    # Agregar estos métodos a la clase Users existente

    def get_daily_analysis_limit(self):
        """Obtener el límite diario de análisis según el plan del usuario"""
        if not self.user_type:
            return 10  # Default para usuarios sin tipo
        
        limit = AnalysisLimit.query.filter_by(
            plan_name=self.user_type,
            is_active=True
        ).first()
        
        return limit.daily_analysis_limit if limit else 10

    def get_today_usage(self):
        """Obtener el registro de uso de hoy"""
        today = datetime.utcnow().date()
        usage = UserAnalysisUsage.query.filter_by(
            user_id=self.id,
            usage_date=today
        ).first()
        
        # Si no existe, crear uno nuevo
        if not usage:
            usage = UserAnalysisUsage(
                user_id=self.id,
                usage_date=today,
                analysis_count=0
            )
            db.session.add(usage)
            db.session.commit()
        
        return usage

    def get_remaining_analysis(self):
        """Calcular análisis restantes para hoy"""
        limit = self.get_daily_analysis_limit()
        usage = self.get_today_usage()
        remaining = limit - usage.analysis_count
        return max(0, remaining)

    def increment_analysis_count(self):
        """Incrementa el contador con UPDATE atómico — evita race condition."""
        from sqlalchemy import text
        today = datetime.utcnow().date()
        limit = self.get_daily_analysis_limit()
        # Garantizar que exista la fila de hoy ANTES del UPDATE atómico. Sin
        # esto, si ningún caller llamó get_today_usage() antes, el UPDATE afecta
        # 0 filas y el contador "no se guarda" en silencio.
        self.get_today_usage()
        try:
            result = db.session.execute(
                text(
                    "UPDATE user_analysis_usage "
                    "SET analysis_count = analysis_count + 1, "
                    "    updated_at = :now, "
                    "    limit_reached_at = CASE "
                    "        WHEN analysis_count + 1 >= :limit AND limit_reached_at IS NULL "
                    "        THEN :now ELSE limit_reached_at END "
                    "WHERE user_id = :uid AND usage_date = :date "
                    "  AND analysis_count < :limit"
                ),
                {'uid': self.id, 'date': today, 'limit': limit, 'now': datetime.utcnow()}
            )
            db.session.commit()
            return result.rowcount > 0
        except Exception as e:
            db.session.rollback()
            logger.error('Error incrementing analysis count: %s', e)
            return False

    def get_analysis_stats(self):
        """Obtener estadísticas completas de análisis"""
        limit = self.get_daily_analysis_limit()
        usage = self.get_today_usage()
        used = usage.analysis_count
        remaining = max(0, limit - used)
        percentage = (used / limit * 100) if limit > 0 else 0
        
        # ✅ NUEVO: Calcular tiempo hasta reset basado en limit_reached_at
        seconds_until_reset = 0
        reset_time = None
        
        if remaining == 0 and usage.limit_reached_at:
            # Si llegó al límite, calcular 24 horas desde ese momento
            reset_time = usage.limit_reached_at + timedelta(hours=24)
            now = datetime.utcnow()
            
            if now < reset_time:
                seconds_until_reset = int((reset_time - now).total_seconds())
                logger.debug("User %s: reset in %ss", self.id, seconds_until_reset)
            else:
                # Ya pasaron las 24 horas, debería auto-resetearse
                seconds_until_reset = 0
                logger.debug("User %s: 24h completed, ready for reset", self.id)
        else:
            # Si aún no llega al límite, mostrar tiempo hasta medianoche UTC
            now = datetime.utcnow()
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_until_reset = int((tomorrow - now).total_seconds())
            reset_time = tomorrow
        
        return {
            'limit': limit,
            'used': used,
            'remaining': remaining,
            'percentage': round(percentage, 1),
            'can_analyze': remaining > 0,
            'plan_name': self.user_type or 'Starter',
            'reset_in_seconds': seconds_until_reset,
            'reset_at': reset_time.isoformat() if reset_time else None,
            'limit_reached_at': usage.limit_reached_at.isoformat() if usage.limit_reached_at else None,
            'last_reset': usage.last_reset_at.isoformat() if usage.last_reset_at else None
        }

    def can_perform_analysis(self):
        """Verificar si el usuario puede realizar un análisis"""
        usage = self.get_today_usage()
        limit = self.get_daily_analysis_limit()
        
        # ✅ NUEVO: Si llegó al límite, verificar si pasaron 24 horas
        if usage.analysis_count >= limit and usage.limit_reached_at:
            time_since_limit = datetime.utcnow() - usage.limit_reached_at
            
            # Si pasaron 24 horas, resetear automáticamente
            if time_since_limit >= timedelta(hours=24):
                logger.info("Auto-reset for user %s after 24h", self.id)
                self.reset_daily_analysis()
                return True
            
            logger.debug("User %s blocked, %.1fh remaining", self.id, 24 - time_since_limit.total_seconds()/3600)
            return False
        
        return usage.analysis_count < limit

    def reset_daily_analysis(self):
        """Resetear el contador diario"""
        today = datetime.utcnow().date()
        usage = UserAnalysisUsage.query.filter_by(
            user_id=self.id,
            usage_date=today
        ).first()
        
        if usage:
            logger.info("Resetting counter for user %s", self.id)
            usage.analysis_count = 0
            usage.last_reset_at = datetime.utcnow()
            usage.limit_reached_at = None  # ✅ NUEVO: Limpiar el timestamp del límite
            try:
                db.session.commit()
                logger.info("Reset completed for user %s", self.id)
            except Exception as e:
                db.session.rollback()
                logger.error("Reset error for user %s: %s", self.id, e)
    def __repr__(self):
        return f'<User {self.email}>'
   
class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    show_welcome_modal = db.Column(db.Boolean, default=True, index=True)
    delete_after_analysis = db.Column(db.Boolean, default=False)
    auto_archive_enabled = db.Column(db.Boolean, default=False)
    archive_after_days = db.Column(db.Integer, default=15)
    delete_after_archive_days = db.Column(db.Integer, default=15)
    # JSON array de plugins de IA (Settings › AI & Automation), p.ej.
    # ["perplexity_check","zone_classifier"] o ["full_analysis"]. NULL = default.
    ai_plugins = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    #user = db.relationship('Users', backref=db.backref('preference', uselist=False))

    def __repr__(self):
        return f'<UserPreference user_id={self.user_id} show_modal={self.show_welcome_modal}>'

class AnalysisLimit(db.Model):
    """Límites de análisis por tipo de plan"""
    __tablename__ = 'analysis_limits'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(50), nullable=False, unique=True)
    daily_analysis_limit = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AnalysisLimit {self.plan_name}: {self.daily_analysis_limit}/day>'

class UserAnalysisUsage(db.Model):
    """Tracking de uso de análisis por usuario"""
    __tablename__ = 'user_analysis_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    usage_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    analysis_count = db.Column(db.Integer, default=0)
    last_reset_at = db.Column(db.DateTime, default=datetime.utcnow)
    limit_reached_at = db.Column(db.DateTime, nullable=True)  # NUEVO: Momento en que llegó al límite
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índices para mejorar rendimiento
    __table_args__ = (
        db.Index('idx_user_date', 'user_id', 'usage_date'),
    )
    
    def __repr__(self):
        return f'<UserAnalysisUsage user_id={self.user_id} date={self.usage_date} count={self.analysis_count}>'
   
class ModelVersion(db.Model):
    """Modelo para las versiones disponibles de los modelos de IA"""
    __tablename__ = 'model_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., "Solenodon Detector"
    version = db.Column(db.String(20), nullable=False)  # e.g., "v1.0"
    description = db.Column(db.Text, nullable=False)  # Justificación del modelo
    biological_name = db.Column(db.String(100), nullable=True)  # e.g., "Solenodon paradoxus"
    icon = db.Column(db.String(50), nullable=True)  # Emoji or icon class
    order = db.Column(db.Integer, default=0)  # Para ordenar en el dropdown
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con planes
    plan_access = db.relationship('ModelPlanAccess', backref='model_version', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ModelVersion {self.name} {self.version}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'biological_name': self.biological_name,
            'icon': self.icon,
            'order': self.order
        }

class ModelPlanAccess(db.Model):
    """Relación entre versiones de modelos y planes de usuario"""
    __tablename__ = 'model_plan_access'
    
    id = db.Column(db.Integer, primary_key=True)
    model_version_id = db.Column(db.Integer, db.ForeignKey('model_versions.id'), nullable=False)
    plan_name = db.Column(db.String(100), nullable=False)  # 'Starter', 'Scholar Suite', etc.
    is_default = db.Column(db.Boolean, default=False)  # Modelo por defecto para este plan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Índice compuesto para búsquedas rápidas
    __table_args__ = (
        db.Index('idx_plan_model', 'plan_name', 'model_version_id'),
    )
    
    def __repr__(self):
        return f'<ModelPlanAccess {self.plan_name} - Model {self.model_version_id}>'

class UserModelPreference(db.Model):
    """Preferencia de modelo seleccionado por el usuario"""
    __tablename__ = 'user_model_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_version_id = db.Column(db.Integer, db.ForeignKey('model_versions.id'), nullable=False)
    selected_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('Users', backref=db.backref('model_preference', uselist=False))
    model_version = db.relationship('ModelVersion')
    
    def __repr__(self):
        return f'<UserModelPreference User:{self.user_id} Model:{self.model_version_id}>'   

# This Python class defines a model for a Country entity with attributes for id, country name, and
# creation date.
class Country(db.Model):
    __tablename__  = 'Country'
    id         = db.Column(db.Integer, primary_key = True)
    country    = db.Column(db.String(100), nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,country):
        self.country  = country

class Institution(db.Model):
    __tablename__  = 'Institution'
    id          = db.Column(db.Integer, primary_key = True)
    institution = db.Column(db.String(255), nullable=True)
    country_id  = db.Column(db.Integer, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,institution,country_id):
        self.institution  = institution
        self.country_id   = country_id

class Institution_type(db.Model):
    __tablename__  = 'Institution_type'
    id               = db.Column(db.Integer, primary_key = True)
    institution_type = db.Column(db.String(255), nullable=True)
    user_id          = db.Column(db.Integer, nullable=False)
    created_date     = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,institution_type,user_id):
        self.institution_type  = institution_type
        self.user_id           = user_id

#class Institution_type(db.Model):
#    __tablename__  = 'Institution_type'
#    id               = db.Column(db.Integer, primary_key = True)
#    institution_type = db.Column(db.String(255), nullable=True)
#    user_id          = db.Column(db.Integer, nullable=False)
#    created_date     = db.Column(db.DateTime, default=datetime.utcnow)
    
#    def __init__(self,institution_type,user_id):
#        self.institution_type  = institution_type
#        self.user_id           = user_id
     
        

# This class defines a model for storing documents with various attributes such as title, author,
# content, and metadata.
class City(db.Model):
    __tablename__ = 'City'
    id           = db.Column(db.Integer, primary_key=True)
    city         = db.Column(db.String(255), nullable=True)
    state_id     = db.Column(db.Integer, nullable=True)
    user_id      = db.Column(db.Integer, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, city, state_id, user_id):
        self.city     = city
        self.state_id = state_id
        self.user_id  = user_id


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
    
    analysis_type = db.Column(db.String(20), nullable=False, default='full')  # 'ai_only', 'db_only', 'full'
    
    
    # Relaciones
    classified_paragraphs = db.relationship("ClassifiedParagraph", back_populates="analysis", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DocumentAnalysis(id={self.id}, analysis_id='{self.analysis_id}', title='{self.title}')>"

class ClassifiedParagraph(db.Model):
    __tablename__ = 'classified_paragraphs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id = db.Column(db.String(36), db.ForeignKey('document_analyses.analysis_id'), nullable=False, index=True)

    # Posición en el documento
    page_number = db.Column(Integer, nullable=False)
    paragraph_number = db.Column(Integer, nullable=False)
    
    # Contenido
    text = db.Column(db.Text, nullable=False)
    
    # Clasificación
    is_human = db.Column(db.Boolean, nullable=True, default=None)  #  Ahora acepta NULL
    human_probability = db.Column(db.Float, nullable=True, default=None)  #  Ahora acepta NULL
    ai_probability = db.Column(db.Float, nullable=True, default=None)  #  Ahora acepta NULL
    
    # Modelo que hizo la predicción (puede ser null)
    predicted_model = db.Column(db.String(100))
    
    # Puntuaciones por modelo (JSON)
    model_scores = db.Column(db.JSON)
    
    # Confianza final
    final_confidence = db.Column(db.Float, nullable=True, default=None)
    
    # Relación
    analysis = db.relationship("DocumentAnalysis", back_populates="classified_paragraphs")
    
    def __repr__(self):
        return f"<ClassifiedParagraph(id={self.id}, page={self.page_number}, paragraph={self.paragraph_number}, is_human={self.is_human})>"
        
class StoragePlan(db.Model):
    __tablename__ = 'storage_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    base_storage_mb = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    trial_days = db.Column(db.Integer, default=0)  # trial duration for this plan
    price_monthly_usd = db.Column(db.Float, default=0)
    price_annual_usd = db.Column(db.Float, default=0)
    stripe_price_monthly = db.Column(db.String(100))  # Stripe price ID
    stripe_price_annual = db.Column(db.String(100))   # Stripe price ID
    paypal_plan_monthly = db.Column(db.String(100))   # PayPal plan ID
    paypal_plan_annual = db.Column(db.String(100))    # PayPal plan ID
    
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
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_shared = db.Column(db.Boolean, default=False)
    
    is_trash = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    rules = db.Column(db.JSON, nullable=True)  # Rules for automation
    metadata_json = db.Column(db.JSON, nullable=True) # Extra metadata
    
    # Relación auto-referencial para subcarpetas
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    # Relación con archivos
    files = db.relationship('File', backref='folder', lazy=True)
    
    def __init__(self, name, path, user_id, parent_id=None, is_shared=False, is_trash=False, expires_at=None, rules=None, metadata_json=None):
        self.name = name
        self.path = path
        self.user_id = user_id
        self.parent_id = parent_id
        self.is_shared = is_shared
        self.is_trash = is_trash
        self.expires_at = expires_at
        self.rules = rules
        self.metadata_json = metadata_json

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
    
    status = db.Column(db.String(50), default='Borrador') # Borrador, En revisión, Validado, Archivado
    is_trash = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    is_evidence = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.JSON, nullable=True) # Direct tags for quick access
    version = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, nullable=True)

    # Auto-Archive lifecycle (independent of status/expires_at/is_trash above,
    # which belong to the manual archive/trash flow).
    archive_cycle_reset_at = db.Column(db.DateTime, nullable=True)
    auto_archived_at = db.Column(db.DateTime, nullable=True)
    auto_archive_delete_at = db.Column(db.DateTime, nullable=True)

    # Relationship to tags through FileTag
    file_tags = db.relationship('FileTag', backref='file', lazy=True, cascade='all, delete-orphan')
    def __init__(self, filename, original_filename, mime_type, size, user_id, minio_url, folder_id=None, status='Borrador', is_trash=False, is_locked=False, is_evidence=False, expires_at=None, tags=None, version=1, description=None, archive_cycle_reset_at=None, auto_archived_at=None, auto_archive_delete_at=None):
        self.filename = filename
        self.original_filename = original_filename
        self.mime_type = mime_type
        self.size = size
        self.user_id = user_id
        self.minio_url = minio_url
        self.folder_id = folder_id
        self.status = status
        self.is_trash = is_trash
        self.is_locked = is_locked
        self.is_evidence = is_evidence
        self.expires_at = expires_at
        self.tags = tags
        self.version = version
        self.description = description
        self.archive_cycle_reset_at = archive_cycle_reset_at
        self.auto_archived_at = auto_archived_at
        self.auto_archive_delete_at = auto_archive_delete_at

# This Python class defines a model for a language entity with attributes such as language name,
# language code, user ID, and creation date.
class Lenguage(db.Model):
    __tablename__  = 'Lenguage'
    id             = db.Column(db.Integer, primary_key = True)
    lenguage_name  = db.Column(db.String(50), nullable=True)
    lenguage       = db.Column(db.String(2), nullable=True)
    user_id        = db.Column(db.Integer, nullable=True)
    created_date   = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self,lenguage_name,lenguage, user_id):
        self.lenguage_name  = lenguage_name
        self.lenguage       = lenguage
        self.user_id        = user_id

class CollaborativePermission(db.Model):
    """Granular permissions for shared files and folders"""
    __tablename__ = 'collaborative_permissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)
    permission_level = db.Column(db.String(50), nullable=False) # view, comment, edit, review
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CollaborativePermission user={self.user_id} level={self.permission_level}>'

class Tag(db.Model):
    """Reusable tags for organizing files"""
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), default='#007bff')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to files through FileTag
    files = db.relationship('FileTag', backref='tag', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Tag {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color
        }


class FileTag(db.Model):
    """Association model for file-tag many-to-many relationship"""
    __tablename__ = 'file_tags'
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_auto = db.Column(db.Boolean, default=False)  # True if assigned by smart rule
    
    # Unique constraint to prevent duplicate tag assignments
    __table_args__ = (
        db.UniqueConstraint('file_id', 'tag_id', name='unique_file_tag'),
    )
    
    def __repr__(self):
        return f'<FileTag file={self.file_id} tag={self.tag_id}>'

class SmartRule(db.Model):
    """Automatic actions based on conditions"""
    __tablename__ = 'smart_rules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    condition_json = db.Column(db.JSON, nullable=False) # if type == 'pdf'
    action_json = db.Column(db.JSON, nullable=False) # move to folder 'PDFs'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SmartRule {self.name}>'
        
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
      
class SubmissionSession(db.Model):
    """Modelo para las sesiones de entrega creadas por los profesores"""
    __tablename__ = 'submission_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    analysis_started = db.Column(db.Boolean, default=False)
    analysis_completed = db.Column(db.Boolean, default=False)
    forced_analysis = db.Column(db.Boolean, default=False)
    
    # Relaciones
    participants = db.relationship('SessionParticipant', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    submissions = db.relationship('StudentSubmission', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    
    def is_active(self):
        now = datetime.utcnow()
        return self.start_date <= now <= self.end_date
    
    def all_documents_submitted(self):
        """Verifica si todos los participantes han subido documentos"""
        total_participants = self.participants.count()
        total_submissions = self.submissions.count()
        return total_participants > 0 and total_participants == total_submissions
    
    def __repr__(self):
        return f'<SubmissionSession {self.name}>'


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


class StudentSubmission(db.Model):
    """Modelo para las entregas de documentos de los estudiantes"""
    __tablename__ = 'student_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('submission_sessions.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    email = db.Column(db.String(120), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    professor_comment = db.Column(db.Text, nullable=True)
    
    # Relaciones
    previous_versions = db.relationship('DocumentVersion', backref='current_document', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('session_id', 'email', name='unique_submission_per_session_email'),
    )
    
    def __repr__(self):
        return f'<StudentSubmission {self.email} - {self.file_name}>'


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


class ItemShare(db.Model):
    """Modelo para compartir archivos/carpetas con otros usuarios"""
    __tablename__ = 'item_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(10), nullable=False)  # 'file' or 'folder'
    item_id = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shared_with_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(20), default='viewer')  # 'viewer', 'commenter', 'editor', 'reviewer'
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # For temporary access
    
    # Relationships
    owner = db.relationship('Users', foreign_keys=[owner_id], backref='shared_items')
    shared_with = db.relationship('Users', foreign_keys=[shared_with_id], backref='received_shares')
    
    def is_expired(self):
        """Check if share has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_type': self.item_type,
            'item_id': self.item_id,
            'permission': self.permission,
            'shared_at': self.shared_at.isoformat() if self.shared_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired(),
            'user': {
                'id': self.shared_with.id,
                'name': f"{self.shared_with.name or ''} {self.shared_with.lastname or ''}".strip() or self.shared_with.email.split('@')[0],
                'email': self.shared_with.email,
                'avatar': (self.shared_with.name or 'U')[0].upper() + (self.shared_with.lastname or 'X')[0].upper()
            }
        }


class LoginHistory(db.Model):
    """Login history for concurrent-session enforcement and audit"""
    __tablename__ = 'logins_xplagiax_clients'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type    = db.Column(db.String(16), nullable=False, default='login')  # 'login' | 'logout'
    ip_address    = db.Column(db.String(45),  nullable=True)
    user_agent    = db.Column(db.String(512), nullable=True)
    browser       = db.Column(db.String(128), nullable=True)
    os_name       = db.Column(db.String(128), nullable=True)
    city          = db.Column(db.String(128), nullable=True)
    country       = db.Column(db.String(128), nullable=True)
    session_token = db.Column(db.String(128), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Users', backref=db.backref('login_history', lazy='dynamic'))


class ItemHistory(db.Model):
    """Modelo para historial de cambios de nombre"""
    __tablename__ = 'item_history'
    
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(10), nullable=False)  # 'file' or 'folder'
    item_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'rename', 'create', 'move'
    old_value = db.Column(db.String(255), nullable=True)
    new_value = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('Users', backref='item_changes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'date': self.created_at.strftime('%Y-%m-%d') if self.created_at else None,
            'user': f"{self.user.name or ''} {self.user.lastname or ''}".strip() or 'You'
        }


# ── Analysis history (pantalla "analysiss") — texto + resultados por usuario ──
# Solo se persiste para planes Individual / Research Essentials / Institutes
# (la regla se aplica en las rutas, no en el modelo).
class AnalysisHistory(db.Model):
    __tablename__ = 'analysis_history'

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    history_id  = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id     = db.Column(db.Integer, nullable=False, index=True)
    title       = db.Column(db.String(255))
    text        = db.Column(db.Text)          # texto analizado
    ai          = db.Column(db.JSON)          # resultado IA (recortado)
    source      = db.Column(db.JSON)          # resultado FinderX (recortado)
    citation    = db.Column(db.JSON)          # resultado validación de citas
    ai_pct      = db.Column(db.Integer)       # % IA
    overall     = db.Column(db.Integer)       # % similitud
    cit_score   = db.Column(db.Integer)       # calidad de citas /100
    result_view = db.Column(db.String(512))   # URL del result.html (vista documento) para reabrir
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def _ts_ms(self):
        import calendar
        return int(calendar.timegm(self.created_at.utctimetuple()) * 1000) if self.created_at else 0

    @staticmethod
    def summary_from_parts(history_id, created_at, title, preview,
                           ai_pct, overall, cit_score, result_view):
        """Shape of a history list entry, built from plain values instead of a
        loaded row. The list endpoint selects only these few columns (never the
        ai/source/citation JSON blobs, which run to hundreds of KB each) so
        MySQL doesn't have to carry them through the ORDER BY filesort — doing
        so blew the sort buffer (error 1038) once a user had a handful of large
        analyses. to_summary() below feeds this from a real row."""
        import calendar
        return {
            'id': history_id,
            'ts': int(calendar.timegm(created_at.utctimetuple()) * 1000) if created_at else 0,
            'title': title or 'Untitled analysis',
            'preview': (preview or '')[:160],
            'aiPct': ai_pct, 'overall': overall, 'cit': cit_score,
            # result_view is only ever set for the uploaded-document flow (the
            # server-rendered result.html to reopen) — its presence is already
            # a reliable document-vs-pasted-text signal, no new column needed.
            'isDocument': bool(result_view),
        }

    def to_summary(self):
        return self.summary_from_parts(
            self.history_id, self.created_at, self.title, self.text,
            self.ai_pct, self.overall, self.cit_score, self.result_view)

    def to_full(self):
        d = self.to_summary()
        d.update({'text': self.text or '', 'ai': self.ai, 'source': self.source,
                  'citation': self.citation, 'result_view': self.result_view})
        return d


# ── Análisis compartidos entre usuarios (pantalla "analysiss" / historial) ──
# Un share apunta a la fila de analysis_history del DUEÑO: si el dueño borra
# el análisis, el cascade elimina los shares y desaparece para los receptores
# (requisito del feature). shared_with_id es NULL para correos externos (se
# les envió el análisis por email; no tienen entrada viva en el historial).
class AnalysisShare(db.Model):
    __tablename__ = 'analysis_shares'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id    = db.Column(db.Integer,
                               db.ForeignKey('analysis_history.id', ondelete='CASCADE'),
                               nullable=False, index=True)
    owner_id       = db.Column(db.Integer, nullable=False, index=True)
    shared_with_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    email          = db.Column(db.String(255), nullable=False)   # correo destino (usuario o externo)
    created_at     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    analysis    = db.relationship('AnalysisHistory',
                                  backref=db.backref('shares', cascade='all, delete-orphan',
                                                     passive_deletes=True))
    shared_with = db.relationship('Users', foreign_keys=[shared_with_id])

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'is_user': self.shared_with_id is not None,
            'initial': (self.email or '?')[0].upper(),
        }