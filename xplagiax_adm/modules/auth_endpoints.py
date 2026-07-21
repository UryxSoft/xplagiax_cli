# auth_endpoints.py
from flask import Blueprint, render_template, request,session, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from models.model import Users_admin
from utils.connections import db
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
import re
from functools import wraps
import logging

from core.security import rate_limit

# Importa tu modelo (ajusta la importación según tu estructura)
# from your_app.models import Users_admin, db

auth_bp = Blueprint('auth_bp', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valida que la contraseña tenga al menos 6 caracteres"""
    return len(password) >= 6

def rate_limit_decorator(max_attempts=5):
    """Rate limit REAL (antes solo logueaba el intento y dejaba pasar todo):
    ventana deslizante de 15 minutos por IP + auditoría del intento.
    Mismo presupuesto que el 2FA de appcli2 (5/15min)."""
    from core.security import rate_limit

    def decorator(f):
        limited = rate_limit(max_attempts, 15 * 60, 'admin-login')(f)

        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger.info("Login attempt from IP: %s",
                        request.headers.get('X-Real-IP', request.remote_addr))
            try:
                from core.audit import log_action
                log_action('auth.login_attempt', 'users_admin', None,
                           {'email': (request.get_json(silent=True) or request.form.to_dict() or {}).get('email')})
            except Exception:
                pass
            return limited(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Pantalla de login. Reemplaza a admx.login_page (app_routes.py),
    eliminado junto con el resto de módulos legacy — sin esta ruta no había
    forma de presentar un formulario de login en absoluto."""
    if current_user.is_authenticated:
        return redirect(url_for('adminx_dashboard.page'))
    from core.security import get_csrf_token
    return render_template('adminx/login.html', csrf_token=get_csrf_token())


@auth_bp.route('/login', methods=['POST'])
@rate_limit_decorator(max_attempts=5)
def login():
    """Endpoint para procesar login"""
    try:
        # Obtener datos del request
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember_me = data.get('remember', False)
        
        # Validaciones básicas
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email y contraseña son requeridos'
            }), 400
        
        # Validar formato de email
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Formato de email inválido'
            }), 400
        
        # Validar contraseña
        if not validate_password(password):
            return jsonify({
                'success': False,
                'message': 'La contraseña debe tener al menos 6 caracteres'
            }), 400
        
        # Buscar usuario por email
        user = Users_admin.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"Intento de login con email no registrado: {email}")
            return jsonify({
                'success': False,
                'message': 'Credenciales inválidas'
            }), 401
        
        # Verificar si el usuario está activo
        if not user.is_active:
            logger.warning(f"Intento de login con usuario inactivo: {email}")
            return jsonify({
                'success': False,
                'message': 'Cuenta deshabilitada. Contacta al administrador.'
            }), 401
        
        # Verificar contraseña
        if not user.check_password(password):
            logger.warning(f"Intento de login con contraseña incorrecta: {email}")
            return jsonify({
                'success': False,
                'message': 'Credenciales inválidas'
            }), 401
        
        # Login exitoso
        login_user(user, remember=remember_me)
        
        # Actualizar último login
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Login exitoso para usuario: {email}")
        
        # Todos los roles admin (superadmin/admin/readonly) comparten el
        # mismo panel — el nivel de acceso lo decide core.security.require_role,
        # no una pantalla de aterrizaje distinta.
        redirect_url = url_for('adminx_dashboard.page')
        
        return jsonify({
            'success': True,
            'message': 'Login exitoso',
            'redirect_url': redirect_url,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500


@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    if current_user.is_authenticated:
        return redirect(url_for('adminx_dashboard.page'))
    return render_template('adminx/forgot_password.html')


@auth_bp.route('/forgot-password', methods=['POST'])
@rate_limit(5, 15 * 60, 'admin-forgot-pw')
def forgot_password_submit():
    """Respuesta SIEMPRE genérica (no revela si el email existe). Si la
    cuenta existe y está activa, manda el mismo link de set/reset password
    que se usa al crear un admin (core.tokens: single-use, 24h)."""
    data = request.get_json(silent=True) or request.form.to_dict()
    email = str(data.get('email') or '').strip().lower()
    generic = {'success': True,
              'message': 'If that email is registered, a password reset link has been sent.'}
    if email and validate_email(email):
        admin = Users_admin.query.filter_by(email=email).first()
        if admin and admin.is_active:
            try:
                from core import mailer
                mailer_sent = mailer.send_password_set_email(
                    admin, subject='Reset your XplagiaX Admin password')
            except Exception:
                mailer_sent = False
                logger.exception('forgot-password email failed for %s', email)
            try:
                from core.audit import log_action
                log_action('auth.forgot_password_request', 'users_admin', admin.id,
                           {'email': email, 'email_sent': mailer_sent})
            except Exception:
                pass
    return jsonify(generic), 200


@auth_bp.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    if current_user.is_authenticated:
        return redirect(url_for('adminx_dashboard.page'))
    from core import tokens as tk
    _admin, err = tk.resolve_password_reset_token(token)
    return render_template('adminx/reset_password.html', token=token, valid=(err is None))


@auth_bp.route('/reset-password/<token>', methods=['POST'])
@rate_limit(8, 15 * 60, 'admin-reset-pw')
def reset_password_submit(token):
    from core import tokens as tk
    admin, err = tk.resolve_password_reset_token(token)
    if err:
        msg = {'expired': 'This link has expired. Request a new one.',
              'used': 'This link was already used or is out of date. Request a new one.',
              'invalid': 'This link is invalid.'}.get(err, 'This link is invalid.')
        return jsonify({'success': False, 'message': msg}), 400

    data = request.get_json(silent=True) or request.form.to_dict()
    password = data.get('password') or ''
    confirm = data.get('confirm_password') or ''
    if not validate_password(password):
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters.'}), 400
    if password != confirm:
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400

    admin.set_password(password)
    db.session.commit()
    try:
        from core.audit import log_action
        log_action('admin.password_set', 'users_admin', admin.id, {'email': admin.email})
    except Exception:
        pass
    return jsonify({'success': True, 'message': 'Password set. You can now sign in.',
                    'redirect_url': url_for('auth_bp.login_page')}), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Endpoint para cerrar sesión"""
    try:
        user_email = current_user.email
        logout_user()
        session.clear()
        
        logger.info(f"Logout exitoso para usuario: {user_email}")
        
        return jsonify({
            'success': True,
            'message': 'Sesión cerrada exitosamente',
            'redirect_url': url_for('auth_bp.login_page')
        }), 200
        
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al cerrar sesión'
        }), 500

@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """Verifica si hay una sesión activa"""
    try:
        if current_user.is_authenticated:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'email': current_user.email,
                    'role': current_user.role
                }
            }), 200
        else:
            return jsonify({
                'authenticated': False
            }), 200
            
    except Exception as e:
        logger.error(f"Error verificando sesión: {str(e)}")
        return jsonify({
            'authenticated': False,
            'error': 'Error verificando sesión'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Obtiene el perfil del usuario actual"""
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo perfil: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error obteniendo perfil'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Cambia la contraseña del usuario actual"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validaciones
        if not all([current_password, new_password, confirm_password]):
            return jsonify({
                'success': False,
                'message': 'Todos los campos son requeridos'
            }), 400
        
        if new_password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'Las contraseñas no coinciden'
            }), 400
        
        if not validate_password(new_password):
            return jsonify({
                'success': False,
                'message': 'La nueva contraseña debe tener al menos 6 caracteres'
            }), 400
        
        # Verificar contraseña actual
        if not current_user.check_password(current_password):
            return jsonify({
                'success': False,
                'message': 'Contraseña actual incorrecta'
            }), 400
        
        # Cambiar contraseña
        current_user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Contraseña cambiada para usuario: {current_user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Contraseña cambiada exitosamente'
        }), 200
        
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# Manejador de errores
@auth_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint no encontrado'
    }), 404

@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Error interno del servidor'
    }), 500