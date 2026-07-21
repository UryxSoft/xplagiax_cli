from utils.config import Config
from flask_migrate import Migrate
#from flask_cors import CORS
from utils.connections import db
from flask_login import LoginManager, UserMixin
from flask_socketio import SocketIO,emit  # Importar SocketIO
from flask import Flask,url_for
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

Talisman(app, content_security_policy=None)
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

csrf_protect_blueprint(adminx_dashboard_bp)
csrf_protect_blueprint(adminx_users_bp)
csrf_protect_blueprint(adminx_institutions_bp)
app.register_blueprint(adminx_dashboard_bp, url_prefix='/adminx')
app.register_blueprint(adminx_users_bp, url_prefix='/adminx/users')
app.register_blueprint(adminx_institutions_bp, url_prefix='/adminx/institutions')

apply_security_headers(app)

if __name__ == '__main__':
    #app.run(debug=True,host='127.0.0.1',port=5001)
    socketio.run(app, host='127.0.0.1', port=5001)
