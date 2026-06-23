import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
       
    SECRET_KEY = '21XSWcxz3zaq45EDCxsw'
    SECURITY_PASSWORD_SALT = '146585145368132386173505678016728509634'
    REMEMBER_COOKIE_SAMESITE  = "strict"
    SESSION_COOKIE_SAMESITE  = "strict"
    
    DATABASE_URI =  'mysql+pymysql://root:@localhost/xplagiax_db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 3600

    SERPAPI_KEY = '18d0a89227e075bb1903ccf7453caff6205dc390687411edda0319d7066f58d0'
    ZENSERP_KEY = 'a9739160-ebe3-11f0-83d4-b9ca31f7dc25',

    QDRANT_HOST='localhost'
    QDRANT_PORT=6333  # Puerto HTTP, no gRPC (6334)
    QDRANT_API_KEY=None
    QDRANT_PREFER_GRPC=False  # Usar HTTP en lugar de gRPC
    #QDRANT_LOG_LEVEL=logging.INFO,
    QDRANT_LITE_MODE=False

    SEAWEEDFS_FILER_URL  = 'http://localhost:8333'
    SEAWEEDFS_MASTER_URL = 'http://localhost:8333'
    SEAWEEDFS_BUCKET     = 'xplagiax-users-documents'
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB default
    CACHE_TTL = 300
    #SESSION_COOKIE_NAME= 'xplagiax_session',
    #SESSION_COOKIE_HTTPONLY= True,
    #SESSION_COOKIE_SECURE= False,  # Cambiar a True en producción con HTTPS
    #SESSION_COOKIE_SAMESITE= 'Lax',  # CRÍTICO para OAuth
    #SESSION_USE_SIGNER= True,
    #PERMANENT_SESSION_LIFETIME= timedelta(hours=2),
    
    # Configuraciones adicionales
    #SESSION_REFRESH_EACH_REQUEST= True,
    #SESSION_COOKIE_DOMAIN= None,  # Dejar que Flask lo detecte automáticamente
    #SESSION_COOKIE_PATH= '/',
    
    # Configuraciones de seguridad
    #WTF_CSRF_ENABLED= True,
    #WTF_CSRF_TIME_LIMIT= None,
    #WTF_CSRF_SSL_STRICT= False, 

    # Email principal - No Reply (para confirmaciones, notificaciones automáticas)
    MAIL_SERVER = 'smtp.ionos.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False  # No SSL para puerto 587
    MAIL_USE_TLS = True   # TLS activado para puerto 587
    MAIL_USERNAME = 'noreply@xplagiax.ca'
    MAIL_PASSWORD = 'MYR1xkd2kqc_gat2hem'
    MAIL_DEFAULT_SENDER = ('XPlagiax', 'noreply@xplagiax.ca')
    
    # Email de Billing - Para facturas, pagos, suscripciones
    BILLING_MAIL_SERVER = 'smtp.ionos.com'
    BILLING_MAIL_PORT = 587
    BILLING_MAIL_USE_SSL = False
    BILLING_MAIL_USE_TLS = True
    BILLING_MAIL_USERNAME = 'billing@xplagiax.com'
    BILLING_MAIL_PASSWORD = 'VNZ-twu!jgt5xwk1ybd'
    BILLING_MAIL_SENDER = ('XPlagiax Billing', 'billing@xplagiax.com')
    
    #payments 
    # Stripe Configuration
    STRIPE_SECRET_KEY = ''   # Para testing, sk_live_... para producción
    STRIPE_PUBLISHABLE_KEY = ''  # Para testing, pk_live_... para producción
    STRIPE_WEBHOOK_SECRET = ''  # Obtenido del webhook endpoint en Stripe Dashboard

    # PayPal Configuration
    PAYPAL_CLIENT_ID = 'AW0S5eppYQPy26v_E2JrQx8apXIVeV4MRS-sTLF9Nu89FxyEV0yI0GSl-98K4-jGra7bDeiaR7nso1q8'
    PAYPAL_CLIENT_SECRET = 'ECHRT-KJ5VZSKCvqpf8ppp1hPZZhGyQXRmDyoSLRHKRVmY-EC-LjEiYnoCIJMlp0xbRFek1ZcZJEacCw'
    PAYPAL_MODE = 'live'  # 'sandbox' para testing, 'live' para producción
    PAYPAL_WEBHOOK_ID = os.environ.get('PAYPAL_WEBHOOK_ID', '')  # Configurar en producción
    
    # Scheduler
    SCHEDULER_TIMEZONE = 'UTC'
    
    # Configuración de subida de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt','ppt','pptx','epub','rtf','mobi', 'png', 'jpg', 'jpeg'}
    
    CACHE_TTL = 300 
    # Configuración OAuth para cada proveedor
    OAUTH_CONFIG = {
        'onedrive': {
            'client_id': 'bdf2666a-3055-423c-a97c-ff98fd098f77',
            'client_secret': '9aae517d-2322-496c-bbed-a00501aa379b',
            'authorization_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            'scope': 'https://graph.microsoft.com/Files.ReadWrite offline_access',
            'api_base': 'https://graph.microsoft.com/v1.0'
        },
        'google_drive': {
            'client_id': '121671119534-92uo2m1vpju3m3msh74jcf389nqhif4r.apps.googleusercontent.com',
            'client_secret': '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',
            'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'scope': 'https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/drive.metadata.readonly',
            'api_base': 'https://www.googleapis.com/drive/v3'
        },
        'dropbox': {
            'client_id': 'uksuctfs3bvxl9o',
            'client_secret': 'ohsz9unjmmbi6t0',
            'authorization_url': 'https://www.dropbox.com/oauth2/authorize',
            'token_url': 'https://api.dropboxapi.com/oauth2/token',
            'scope': 'account_info.read files.metadata.read files.content.read files.content.write',
            'api_base': 'https://api.dropboxapi.com/2'
        },
        'box': {
            'client_id': '2exf4vhqo7jozfhrxt3grl885ltm36c1',
            'client_secret': 'Jdgzvg5HExQAnupFNYzGXmdUQNrwrhsf',
            'authorization_url': 'https://account.box.com/api/oauth2/authorize',
            'token_url': 'https://api.box.com/oauth2/token',
            'scope': 'root_readwrite',
            'api_base': 'https://api.box.com/2.0'
        }
    } 
    
    # Configuración de Celery y Redis
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
    SECRET_KEY = '43RFCvfr5edc67TGBvfr'
    SQLALCHEMY_DATABASE_URI =  'mysql+pymysql://root:@localhost/xplagiax_db'
    
class TestingConfig(Config):
    TESTING = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_COMMIT_ON_TEADOWN = False
    SECRET_KEY = '65YHNbgt7ujm89UJMmko'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/xplagiax_db'

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SECRET_KEY = '87UJMnhy9ikl01IOPlok'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admininsideout:insideout_2024@172.105.102.130/xplagiax_db'

Config = {
       'development':  DevelopmentConfig,
       'testing'    :  TestingConfig,
       'production' :  ProductionConfig,
       'default'    :  DevelopmentConfig    
}