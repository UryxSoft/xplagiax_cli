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
login_manager.login_view = 'admx.login_page'
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

from modules.users_endpoints import users_bp
from modules.usersadmin_endpoints import usersadmin_bp
from modules.documents_endpoints import documents_bp
from modules.doctypes_endpoints import doctype_bp
from modules.languages_endpoints import languages_bp
from modules.institutions_endpoints import institutions_bp
from modules.institutionstype_endpoints  import institution_types_bp
from modules.countries_endpoints import countries_bp
from modules.cities_endpoints import cities_bp
from modules.provinces_endpoints import provinces_bp
from modules.sessions_endpoints import sessions_bp
from modules.app_routes import admx
from modules.auth_endpoints import auth_bp
from modules.admin import admin_bp
from modules.sessionsssh_endpoints import sessionsssh_bp
#from modules.monitoring_endpoints import monitoring_bp
from modules.terminal_endpoints_enhanced import terminal_bp
from modules.dashboardssh_endpoints import dashboardssh_bp
from modules.reports_endpoints import reports_bp
from modules.services_endpoints_fixed import services_bp
from modules.settings_endpoints import settings_bp
from modules.aianalisis_endpoints import document_analysis_bp
from modules.contactsale_endpoints import contact_sale_bp
# Pasar socketio al blueprint de terminal
from modules.terminal_endpoints import socket_events
socket_events(socketio)  # Registrar eventos de SocketIO

# En tu app.py principal
#from modules.websocket_handlers import register_websocket_handlers

# Después de crear socketio
#register_websocket_handlers(socketio)

app.register_blueprint(users_bp, url_prefix='/users_bp')
app.register_blueprint(usersadmin_bp, url_prefix='/usersadmin_bp')
app.register_blueprint(documents_bp, url_prefix='/documents_bp')
app.register_blueprint(doctype_bp, url_prefix='/doctype_bp')
app.register_blueprint(languages_bp, url_prefix='/languages_bp')
app.register_blueprint(institutions_bp, url_prefix='/institutions_bp')
app.register_blueprint(institution_types_bp, url_prefix='/institution_types_bp')
app.register_blueprint(countries_bp, url_prefix='/countries_bp')
app.register_blueprint(cities_bp,url_prefix='/cities_bp')
app.register_blueprint(provinces_bp, url_prefix='/provinces_bp')
app.register_blueprint(sessions_bp, url_prefix='/sessions_bp')
app.register_blueprint(admx, url_prefix='/')
app.register_blueprint(auth_bp, url_prefix='/auth_bp')
app.register_blueprint(admin_bp, url_prefix='/admin_bp')
app.register_blueprint(sessionsssh_bp, url_prefix='/sessionsssh_bp')
#app.register_blueprint(monitoring_bp, url_prefix='/monitoring_bp')
app.register_blueprint(terminal_bp, url_prefix='/terminal_bp')
app.register_blueprint(dashboardssh_bp, url_prefix='/dashboardssh_bp')
app.register_blueprint(reports_bp, url_prefix='/reports_bp')
app.register_blueprint(services_bp, url_prefix='/services_bp')
app.register_blueprint(settings_bp, url_prefix='/settings_bp')
app.register_blueprint(document_analysis_bp, url_prefix='/document_analysis_bp')
app.register_blueprint(contact_sale_bp, url_prefix='/contact_sale_bp')
if __name__ == '__main__':
    #app.run(debug=True,host='127.0.0.1',port=5001)
    socketio.run(app, host='127.0.0.1', port=5001)