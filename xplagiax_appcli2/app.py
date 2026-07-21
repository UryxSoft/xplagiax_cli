from settings.config import Config
from flask_migrate import Migrate
from settings.connections import db, csrf, limiter
from flask_login import LoginManager, login_required
from flask import Flask, send_from_directory, make_response, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from celery import Celery
from datetime import timedelta
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Detrás de nginx (TLS terminado): honrar X-Forwarded-Proto/For para que
# url_for(_external=True) genere https://app.xplagiax.ca/... y no http://127.0.0.1.
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(Config[env])
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

@app.route('/test_alive')
def test_alive():
    return "Server is live"

celery = Celery()
#mail = Mail()

# CONFIGURACIÓN CORREGIDA DE FLASK-LOGIN - MÁS ROBUSTA
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'x_apps.login'
login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

_is_production = env == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = _is_production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# 30 días, alineado con la validez del session_token del modelo (Users.
# is_session_valid expira a los 30 días) y con la cookie remember. Con 1h,
# cada visita posterior re-autenticaba vía cookie remember pero la sesión ya
# no tenía session_token → el enforcement de sesión única expulsaba al
# usuario con "Your session has expired" en cada vuelta.
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['SESSION_PERMANENT'] = True

# Inicializar extensiones
db.init_app(app)
csrf.init_app(app)
limiter.init_app(app)
migrate = Migrate(app, db)

#  USER LOADER OPTIMIZADO Y ROBUSTO
@login_manager.user_loader
def load_user(user_id):
    """Carga usuario para Flask-Login - VERSIÓN ULTRA ROBUSTA"""
    try:
        #print(f" user_loader: Buscando user_id={user_id}")
        
        if not user_id or str(user_id).strip() == '' or user_id == 'None':
            #print(" user_loader: user_id inválido")
            return None
            
        # Importar dentro de la función para evitar imports circulares
        from modules.models.model import Users
        
        # Convertir a int de manera segura
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            #print(f" user_loader: No se puede convertir user_id a int: {user_id}")
            return None
            
        # Buscar usuario con query más específica
        user = Users.query.filter_by(id=user_id_int, isactive=True, confirmed=True).first()
        
        if user:
            #print(f" user_loader: Usuario encontrado - {user.email}")
            return user
        else:
            #print(f" user_loader: Usuario no encontrado o inactivo - id={user_id}")
            return None
            
    except Exception as e:
        #print(f" user_loader: Error crítico - {e}")
        import traceback
        traceback.print_exc()
        return None

# Importar rutas
from modules.apps_service.apps_routes import x_apps
#from modules.auth_service.auth_routes import x_auth
from modules.users_service.user_routes import x_users
from modules.auth_service.auth_routes_fixed import auth_bp
from modules.billing_service.billing_routes import billing_bp
from modules.bucket_service.bucket_routes import x_buck
from modules.doc_service.doc_routes import x_doc
#from modules.finderx_service.search_routes import x_search
#from modules.genuine_service.genuine_routes import x_genuine
from modules.image_service.ai_image_routes import x_image
from modules.integration_service.routes_integrations import x_integ
#from services.sourcex_service.routes_integrations import x_integ
from modules.doc_service.routes_analysis_counter import x_analysiscounter
from modules.doc_service.routes_auto_archive import x_autoarchive

#from services.aitestprotext_service.optimized_routes_v6 import x_aitestpro
#from modules.aitestproimg_service.routes_img import enhanced_img

from modules.cleanup_service.routes_cleanup import x_cleanup, init_cleanup_system
from modules.system_status_service.status_routes import x_system_status

# Registrar blueprints
app.register_blueprint(x_apps)
#app.register_blueprint(x_auth, url_prefix='/x_auth')
app.register_blueprint(x_users,url_prefix='/')
app.register_blueprint(auth_bp, url_prefix='/auth_bp')  #  MANTENER SOLO TU OAUTH PERSONALIZADO
app.register_blueprint(billing_bp, url_prefix='/billing_bp')
app.register_blueprint(x_buck, url_prefix='/x_buck')
app.register_blueprint(x_doc, url_prefix='/x_doc')
app.register_blueprint(x_image, url_prefix='/x_image')
app.register_blueprint(x_integ, url_prefix='/x_integ')
app.register_blueprint(x_analysiscounter,url_prefix='/x_analysiscounter')
app.register_blueprint(x_autoarchive, url_prefix='/x_doc/auto-archive')
#app.register_blueprint(enhanced_img, url_prefix='/enhanced_img')
app.register_blueprint(x_cleanup, url_prefix='/x_cleanup')
app.register_blueprint(x_system_status, url_prefix='/x_system_status')  # Public - No auth required

#app.register_blueprint(x_aitestpro, url_prefix='/x_aitestpro')


# Configurar scheduler para reset diario
def setup_scheduler():
    from modules.doc_service.routes_analysis_counter import reset_all_daily_analysis
    from modules.doc_service.routes_auto_archive import run_auto_archive_sweep

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=reset_all_daily_analysis,
        trigger=CronTrigger(hour=0, minute=0),  # Medianoche UTC
        id='reset_analysis_daily',
        name='Reset daily analysis counters',
        replace_existing=True
    )
    scheduler.add_job(
        func=run_auto_archive_sweep,
        trigger=CronTrigger(hour=0, minute=30),  # Medianoche UTC + 30min
        id='auto_archive_sweep_daily',
        name='Auto-archive lifecycle sweep',
        replace_existing=True
    )
    scheduler.start()
    #print("✓ Analysis scheduler started")

# Al inicializar la app
with app.app_context():
    if env != 'production':
        db.create_all()

    # Añadir columna solo si no existe (idempotente, sin lock innecesario en producción)
    try:
        col_exists = db.session.execute(db.text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "  AND TABLE_NAME   = 'logins_xplagiax_clients' "
            "  AND COLUMN_NAME  = 'event_type'"
        )).scalar()
        if not col_exists:
            db.session.execute(db.text(
                "ALTER TABLE logins_xplagiax_clients "
                "ADD COLUMN event_type VARCHAR(16) NOT NULL DEFAULT 'login'"
            ))
            db.session.commit()
    except Exception:
        db.session.rollback()

    # Añadir columna solo si no existe (idempotente) — preferencia de retención
    # de documentos (Settings > Privacy > Document Retention).
    try:
        col_exists = db.session.execute(db.text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "  AND TABLE_NAME   = 'user_preferences' "
            "  AND COLUMN_NAME  = 'delete_after_analysis'"
        )).scalar()
        if not col_exists:
            db.session.execute(db.text(
                "ALTER TABLE user_preferences "
                "ADD COLUMN delete_after_analysis TINYINT(1) NOT NULL DEFAULT 0"
            ))
            db.session.commit()
    except Exception:
        db.session.rollback()

    # Añadir columnas solo si no existen (idempotente) — Auto-Archive
    # (Settings > Automation Rules) y columnas de ciclo de vida en files.
    for _table, _col, _ddl in [
        ('user_preferences', 'auto_archive_enabled', "TINYINT(1) NOT NULL DEFAULT 0"),
        ('user_preferences', 'archive_after_days', "INT NOT NULL DEFAULT 15"),
        ('user_preferences', 'delete_after_archive_days', "INT NOT NULL DEFAULT 15"),
        ('files', 'archive_cycle_reset_at', "DATETIME NULL DEFAULT NULL"),
        ('files', 'auto_archived_at', "DATETIME NULL DEFAULT NULL"),
        ('files', 'auto_archive_delete_at', "DATETIME NULL DEFAULT NULL"),
    ]:
        try:
            col_exists = db.session.execute(db.text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
            ), {'t': _table, 'c': _col}).scalar()
            if not col_exists:
                db.session.execute(db.text(
                    f"ALTER TABLE {_table} ADD COLUMN {_col} {_ddl}"
                ))
                db.session.commit()
        except Exception:
            db.session.rollback()

    init_cleanup_system()
    _run_scheduler = (
        os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
        or os.environ.get('SCHEDULER_ENABLED') == 'true'
        or (env == 'development' and os.environ.get('WERKZEUG_RUN_MAIN') != 'false')
    )
    if _run_scheduler:
        setup_scheduler()

@app.route('/protected/js/auth/signin.js')
def signin_js():
    response = make_response(send_from_directory('static/js/auth', 'signin.js'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/service-worker.js')
def service_worker_killswitch():
    """aitestpro_mobile_fix.js used to call navigator.serviceWorker.register('/service-worker.js')
    on every page load, but this file never existed — any browser that
    nonetheless installed one from it is stuck running that old worker
    forever (clearing the HTTP cache doesn't remove a service worker), and
    it intercepts every fetch on the origin ahead of the browser cache —
    which defeats ?v= cache-busting on scripts like enhanced_signin.js and
    explains the "must clear cache before login" symptom independent of
    which OAuth provider is used. This unregisters it and reloads any tab
    it still controls; the client-side register() call has been removed."""
    js = (
        "self.addEventListener('install', () => self.skipWaiting());\n"
        "self.addEventListener('activate', (event) => {\n"
        "  event.waitUntil(\n"
        "    self.registration.unregister()\n"
        "      .then(() => self.clients.matchAll({ type: 'window' }))\n"
        "      .then((clients) => clients.forEach((client) => client.navigate(client.url)))\n"
        "  );\n"
        "});\n"
    )
    response = make_response(js)
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/pdf/<path:filename>')
@login_required
def serve_pdf(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_directory = os.path.join(current_dir, 'modules', 'doc_service', 'uploads', 'uploads_analysis')
    return send_from_directory(pdf_directory, filename)

@app.before_request
def before_request():
    from flask_login import current_user
    if request.endpoint and any(p in request.endpoint for p in ['home', 'x_users']):
        logger.debug('REQUEST %s: authenticated=%s', request.endpoint, current_user.is_authenticated)


@app.after_request
def security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' "
            "https://www.paypal.com https://www.sandbox.paypal.com "
            "https://unpkg.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com https://unpkg.com "
            "https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "font-src 'self' "
            "https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "frame-src 'self' blob: https://www.paypal.com https://www.sandbox.paypal.com; "
        "connect-src 'self' https://www.paypal.com https://www.sandbox.paypal.com https://unpkg.com"
    )
    if _is_production:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5003)