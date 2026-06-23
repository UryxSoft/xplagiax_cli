import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
       
    SECRET_KEY = '21XSWcxz3zaq45EDCxsw'
    SECURITY_PASSWORD_SALT = '146585145368132386173505678016728509634'
    REMEMBER_COOKIE_SAMESITE  = "strict"
    SESSION_COOKIE_SAMESITE  = "strict"
    SQLALCHEMY_COMMIT_ON_OPTIONS = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    # Configuración de correo electrónico
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'xplagiax@gmail.com'
    MAIL_PASSWORD = 'akkv bxvl nmui sbws' #'ooisensjskgemgle'
    MAIL_DEFAULT_SENDER = ('no-replit', 'xplagiax@gmail.com')
    
    # Configuración de subida de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'zip'}
    
    # Configuración de Celery y Redis
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
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://xplagiaxadminuser:xplagiax001@mysql-container:3306/xplagiax_db"


Config = {
       'development':  DevelopmentConfig,
       'testing'    :  TestingConfig,
       'production' :  ProductionConfig,
       'default'    :  DevelopmentConfig    
}