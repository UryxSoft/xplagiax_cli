"""
Configuración por variables de entorno.

Los valores que antes vivían hardcodeados aquí (SECRET_KEY, salt, password
SMTP de Gmail, credenciales MySQL de producción) quedaron expuestos en el
historial del repo — se conservan SOLO como fallback de arranque para no
romper el deploy actual, con warning ruidoso. ROTARLOS y definirlos por
entorno es obligatorio (ver .env.example / LEEME del paquete).
"""
import os
import logging
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
_log = logging.getLogger(__name__)


def _env(name, fallback=None, warn=True):
    val = os.environ.get(name)
    if val:
        return val
    if warn and fallback is not None:
        _log.warning("CONFIG: %s no está definido por entorno — usando fallback "
                     "legado COMPROMETIDO. Rotar y definir la variable.", name)
    return fallback


class Config:
    SECRET_KEY = _env('ADMIN_SECRET_KEY', '21XSWcxz3zaq45EDCxsw')
    SECURITY_PASSWORD_SALT = _env('ADMIN_SECURITY_SALT',
                                  '146585145368132386173505678016728509634')
    # Firma de tokens de activación — DEBE ser el mismo valor en appcli2
    # (env ACTIVATION_SIGNING_KEY en ambos contenedores).
    ACTIVATION_SIGNING_KEY = _env('ACTIVATION_SIGNING_KEY', None, warn=False)
    ACTIVATION_MAX_AGE_HOURS = int(os.environ.get('ACTIVATION_MAX_AGE_HOURS', '72'))
    APPCLI_BASE_URL = os.environ.get('APPCLI_BASE_URL', 'https://app.xplagiax.ca').rstrip('/')

    REMEMBER_COOKIE_SAMESITE = "strict"
    SESSION_COOKIE_SAMESITE = "strict"
    SQLALCHEMY_COMMIT_ON_OPTIONS = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Correo (activación / bienvenida). Mismos nombres MAIL_* estándar.
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', '1') not in ('0', 'false', 'False')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', '0') in ('1', 'true', 'True')
    MAIL_USERNAME = _env('MAIL_USERNAME', 'xplagiax@gmail.com')
    MAIL_PASSWORD = _env('MAIL_PASSWORD', 'akkv bxvl nmui sbws')
    MAIL_DEFAULT_SENDER = (os.environ.get('MAIL_SENDER_NAME', 'XplagiaX'),
                           os.environ.get('MAIL_SENDER_ADDR', 'xplagiax@gmail.com'))

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'zip'}

    CELERY_CONFIG = {
        'broker_url': os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0',
        'result_backend': os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0',
        'timezone': 'UTC',
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'beat_schedule': {
            'check-session-status': {
                'task': 'app.tasks.celery_tasks.check_sessions_status',
                'schedule': timedelta(hours=1),
            },
            'send-reminders': {
                'task': 'app.tasks.email_tasks.send_pending_reminders',
                'schedule': timedelta(hours=12),
            },
        }
    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'ADMIN_DATABASE_URL', 'mysql+pymysql://root:@localhost/xplagiax_db')


class TestingConfig(Config):
    TESTING = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_COMMIT_ON_TEADOWN = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'ADMIN_DATABASE_URL', 'mysql+pymysql://root:@localhost/xplagiax_db')


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = _env(
        'ADMIN_DATABASE_URL',
        "mysql+pymysql://xplagiaxadminuser:xplagiax001@mysql-container:3306/xplagiax_db")


Config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
