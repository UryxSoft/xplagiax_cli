from utils.config import Config
from flask_migrate import Migrate
#from flask_cors import CORS
from utils.connections import db
from flask_login import LoginManager, UserMixin
from flask_socketio import SocketIO,emit  # Importar SocketIO
from flask import Flask,url_for,redirect
from flask_talisman import Talisman
import os
app = Flask(__name__)

#CORS(app)
app.config.from_object(Config['production'])
app.config['SESSION_COOKIE_SECURE'] = True  # Solo enviar cookies por HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JS no puede acceder a las cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protege contra CSRF

socketio = SocketIO(app, cors_allowed_origins="*")  # Ajusta CORS según necesites

# Inicializar extensiones
db.init_app(app)

talisman = Talisman(app, content_security_policy=None)
# Configurar Flask-Login
login_manager = LoginManager()
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'
# FIX: 'admx.login_page' apuntaba al blueprint app_routes.py, eliminado junto
# con el resto de módulos legacy — el login vive ahora en auth_bp (ver
# modules/auth_endpoints.py: GET /auth_bp/login).
login_manager.login_view = 'auth_bp.login_page'
login_manager.init_app(app)

# Importar modelos después de inicializar db
from models.model import Users_admin

# Required user loader para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        return Users_admin.query.get(int(user_id))
    except (ValueError, TypeError):
        return None

# NOTA: los blueprints legacy (institutions_endpoints, countries_endpoints,
# cities_endpoints, provinces_endpoints, users_endpoints, terminal_*,
# services_*, settings_endpoints, app_routes/admx, admin, etc.) fueron
# eliminados del repo — este app.py antes seguía importándolos y el proceso
# no podía ni arrancar (ModuleNotFoundError en el primer import). Se
# reemplazan por el panel adminx/* (dashboard + usuarios + instituciones).
from modules.auth_endpoints import auth_bp
from core.security import (csrf_protect_blueprint, login_required_blueprint,
                           apply_security_headers)

app.register_blueprint(auth_bp, url_prefix='/auth_bp')

# ── AdminX: dashboard + gestión de usuarios + instituciones ──────────────────
from modules.adminx_dashboard import adminx_dashboard_bp
from modules.adminx_users import adminx_users_bp
from modules.adminx_institutions import adminx_institutions_bp
from modules.adminx_admins import adminx_admins_bp
from modules.adminx_audit import adminx_audit_bp
from modules.adminx_bulk_users import adminx_bulk_users_bp

csrf_protect_blueprint(adminx_dashboard_bp)
csrf_protect_blueprint(adminx_users_bp)
csrf_protect_blueprint(adminx_institutions_bp)
csrf_protect_blueprint(adminx_admins_bp)
csrf_protect_blueprint(adminx_audit_bp)
csrf_protect_blueprint(adminx_bulk_users_bp)
app.register_blueprint(adminx_dashboard_bp, url_prefix='/adminx')
app.register_blueprint(adminx_users_bp, url_prefix='/adminx/users')
app.register_blueprint(adminx_institutions_bp, url_prefix='/adminx/institutions')
app.register_blueprint(adminx_admins_bp, url_prefix='/adminx/admins')
app.register_blueprint(adminx_audit_bp, url_prefix='/adminx/audit')
app.register_blueprint(adminx_bulk_users_bp, url_prefix='/adminx/bulk-users')

apply_security_headers(app)


@app.route('/healthz')
@talisman(force_https=False)
def healthz():
    """Liveness check para HEALTHCHECK/orquestador — sin auth, sin DB.
    force_https=False: el HEALTHCHECK del Dockerfile pega por loopback en
    http:// puro (gunicorn no sirve TLS — eso lo termina el proxy de
    delante); sin esta excepción Talisman lo redirigía siempre a https y el
    check nunca podía completarse (no hay TLS escuchando en este puerto)."""
    return {'status': 'ok'}, 200


@app.route('/')
def root():
    """Sin esto, la URL más obvia para un despliegue nuevo (el dominio
    pelado) daba 404 — no había ninguna ruta en '/'. adminx_dashboard.page
    ya maneja tanto el caso autenticado (dashboard) como el no autenticado
    (Flask-Login redirige solo a login_view)."""
    return redirect(url_for('adminx_dashboard.page'))


if __name__ == '__main__':
    #app.run(debug=True,host='127.0.0.1',port=5001)
    socketio.run(app, host='127.0.0.1', port=5001)
