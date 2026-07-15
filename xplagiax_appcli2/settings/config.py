import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))


def _env_bool(key, default=False):
    v = os.environ.get(key)
    if v is None:
        return default
    return v.strip().lower() in ('1', 'true', 'yes', 'on')


class Config:

    # ── Seguridad / sesión ──────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', '21XSWcxz3zaq45EDCxsw')
    SECURITY_PASSWORD_SALT = os.environ.get(
        'SECURITY_PASSWORD_SALT', '146585145368132386173505678016728509634')
    # 'Lax' (no 'strict') por la misma razón que SESSION_COOKIE_SAMESITE: con
    # 'strict' la cookie remember no viaja en la navegación de retorno del IdP
    # (OAuth callback) y el "remember me" se pierde en esos flujos.
    REMEMBER_COOKIE_SAMESITE = "Lax"
    # C-3: 'Lax' (no 'strict') es lo mínimo que permite que la cookie de sesión
    # viaje en el callback OAuth (navegación GET cross-site top-level). Con
    # 'strict' la cookie no se enviaba, el state no sobrevivía y por eso se
    # habían desactivado los controles de seguridad del callback. app.py ya
    # forzaba 'Lax' en runtime; aquí se alinea la fuente de verdad.
    SESSION_COOKIE_SAMESITE = "Lax"

    # ── Base de datos (MySQL) ───────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'mysql+pymysql://root:@localhost/xplagiax_db')
    DATABASE_URI = SQLALCHEMY_DATABASE_URI

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('SQLALCHEMY_POOL_SIZE', 10))
    SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 20))
    SQLALCHEMY_POOL_TIMEOUT = int(os.environ.get('SQLALCHEMY_POOL_TIMEOUT', 30))
    SQLALCHEMY_POOL_RECYCLE = int(os.environ.get('SQLALCHEMY_POOL_RECYCLE', 3600))

    # ── API keys de búsqueda ────────────────────────────────────────────────
    SERPAPI_KEY = os.environ.get(
        'SERPAPI_KEY', '18d0a89227e075bb1903ccf7453caff6205dc390687411edda0319d7066f58d0')
    ZENSERP_KEY = os.environ.get('ZENSERP_KEY', 'a9739160-ebe3-11f0-83d4-b9ca31f7dc25')

    # ── Qdrant (vectorial) ──────────────────────────────────────────────────
    QDRANT_HOST = os.environ.get('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.environ.get('QDRANT_PORT', 6333))   # HTTP, no gRPC (6334)
    QDRANT_API_KEY = os.environ.get('QDRANT_API_KEY') or None
    QDRANT_PREFER_GRPC = _env_bool('QDRANT_PREFER_GRPC', False)
    QDRANT_LITE_MODE = _env_bool('QDRANT_LITE_MODE', False)

    # ── Elasticsearch ───────────────────────────────────────────────────────
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')

    # ── SeaweedFS (almacenamiento de documentos) ────────────────────────────
    SEAWEEDFS_FILER_URL = os.environ.get('SEAWEEDFS_FILER_URL', 'http://localhost:8333')
    SEAWEEDFS_MASTER_URL = os.environ.get('SEAWEEDFS_MASTER_URL', 'http://localhost:8333')
    SEAWEEDFS_BUCKET = os.environ.get('SEAWEEDFS_BUCKET', 'xplagiax-users-documents')

    # ── Servicios externos de análisis (IA / FinderX) ───────────────────────
    AI_TEXT_SERVICE_URL = os.environ.get(
        'AI_TEXT_SERVICE_URL', 'http://localhost:5006/analyze_document_async')
    AI_TEXT_SERVICE_API_KEY = os.environ.get(
        'AI_TEXT_SERVICE_API_KEY', '7d9a2c4f8e1b3d5a6f7c9e2b4a1d8c3f')
    FINDERX_SERVICE_BASE = os.environ.get('FINDERX_SERVICE_BASE', 'http://localhost:8000')
    FINDERX_SERVICE_API_KEY = os.environ.get(
        'FINDERX_SERVICE_API_KEY', 'xpx-3Td8C2oecnAXRT0-VioypUjMWTtSTQVj3k2kE8Q-5tc')

    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    CACHE_TTL = int(os.environ.get('CACHE_TTL', 300))

    # ── Email principal (No-Reply) ──────────────────────────────────────────
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.ionos.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_SSL = _env_bool('MAIL_USE_SSL', False)
    MAIL_USE_TLS = _env_bool('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'noreply@xplagiax.ca')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'MYR1xkd2kqc_gat2hem')
    MAIL_DEFAULT_SENDER = (
        os.environ.get('MAIL_SENDER_NAME', 'XPlagiax'),
        os.environ.get('MAIL_SENDER_EMAIL', 'noreply@xplagiax.ca'),
    )

    # ── Email de Billing ────────────────────────────────────────────────────
    BILLING_MAIL_SERVER = os.environ.get('BILLING_MAIL_SERVER', 'smtp.ionos.com')
    BILLING_MAIL_PORT = int(os.environ.get('BILLING_MAIL_PORT', 587))
    BILLING_MAIL_USE_SSL = _env_bool('BILLING_MAIL_USE_SSL', False)
    BILLING_MAIL_USE_TLS = _env_bool('BILLING_MAIL_USE_TLS', True)
    BILLING_MAIL_USERNAME = os.environ.get('BILLING_MAIL_USERNAME', 'billing@xplagiax.com')
    BILLING_MAIL_PASSWORD = os.environ.get('BILLING_MAIL_PASSWORD', 'VNZ-twu!jgt5xwk1ybd')
    BILLING_MAIL_SENDER = (
        os.environ.get('BILLING_MAIL_SENDER_NAME', 'XPlagiax Billing'),
        os.environ.get('BILLING_MAIL_SENDER_EMAIL', 'billing@xplagiax.com'),
    )

    # ── Pagos: Stripe ───────────────────────────────────────────────────────
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

    # ── Pagos: PayPal ───────────────────────────────────────────────────────
    PAYPAL_CLIENT_ID = os.environ.get(
        'PAYPAL_CLIENT_ID',
        'AW0S5eppYQPy26v_E2JrQx8apXIVeV4MRS-sTLF9Nu89FxyEV0yI0GSl-98K4-jGra7bDeiaR7nso1q8')
    PAYPAL_CLIENT_SECRET = os.environ.get(
        'PAYPAL_CLIENT_SECRET',
        'ECHRT-KJ5VZSKCvqpf8ppp1hPZZhGyQXRmDyoSLRHKRVmY-EC-LjEiYnoCIJMlp0xbRFek1ZcZJEacCw')
    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'live')
    PAYPAL_WEBHOOK_ID = os.environ.get('PAYPAL_WEBHOOK_ID', '')

    SCHEDULER_TIMEZONE = os.environ.get('SCHEDULER_TIMEZONE', 'UTC')

    # ── Subida de archivos ──────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx',
                          'epub', 'rtf', 'mobi', 'png', 'jpg', 'jpeg'}

    # ── OAuth proveedores de almacenamiento en nube ─────────────────────────
    # La variable de entorno SIEMPRE tiene prioridad; el valor hardcodeado es
    # solo respaldo para que el provider funcione sin configuración adicional
    # (repo privado). Recomendado: mover los secretos a env vars y rotarlos.
    # Google Drive queda env-only a propósito (rellena GOOGLE_CLIENT_* por env).
    OAUTH_CONFIG = {
        'onedrive': {
            'client_id': os.environ.get('ONEDRIVE_CLIENT_ID', 'bdf2666a-3055-423c-a97c-ff98fd098f77'),
            'client_secret': os.environ.get('ONEDRIVE_CLIENT_SECRET', '9aae517d-2322-496c-bbed-a00501aa379b'),
            'authorization_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            'scope': 'https://graph.microsoft.com/Files.ReadWrite offline_access',
            'api_base': 'https://graph.microsoft.com/v1.0'
        },
        'google_drive': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
            'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'scope': 'https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/drive.metadata.readonly',
            'api_base': 'https://www.googleapis.com/drive/v3'
        },
        'dropbox': {
            'client_id': os.environ.get('DROPBOX_CLIENT_ID', 'uksuctfs3bvxl9o'),
            'client_secret': os.environ.get('DROPBOX_CLIENT_SECRET', 'ohsz9unjmmbi6t0'),
            'authorization_url': 'https://www.dropbox.com/oauth2/authorize',
            'token_url': 'https://api.dropboxapi.com/oauth2/token',
            'scope': 'account_info.read files.metadata.read files.content.read files.content.write',
            'api_base': 'https://api.dropboxapi.com/2'
        },
        'box': {
            'client_id': os.environ.get('BOX_CLIENT_ID', '2exf4vhqo7jozfhrxt3grl885ltm36c1'),
            'client_secret': os.environ.get('BOX_CLIENT_SECRET', 'Jdgzvg5HExQAnupFNYzGXmdUQNrwrhsf'),
            'authorization_url': 'https://account.box.com/api/oauth2/authorize',
            'token_url': 'https://api.box.com/oauth2/token',
            'scope': 'root_readwrite',
            'api_base': 'https://api.box.com/2.0'
        }
    }

    # ── Celery / Redis ──────────────────────────────────────────────────────
    CELERY_CONFIG = {
        'broker_url': os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/12',
        'result_backend': os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/13',
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
    SECRET_KEY = os.environ.get('SECRET_KEY', '43RFCvfr5edc67TGBvfr')


class TestingConfig(Config):
    TESTING = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_COMMIT_ON_TEADOWN = False
    SECRET_KEY = os.environ.get('SECRET_KEY', '65YHNbgt7ujm89UJMmko')


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', '87UJMnhy9ikl01IOPlok')
    # En producción la DB DEBE venir de DATABASE_URL; el default solo es respaldo.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'mysql+pymysql://admininsideout:insideout_2024@172.105.102.130/xplagiax_db')


Config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
