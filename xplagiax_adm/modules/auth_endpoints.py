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
    """Decorador simple para limitar intentos (implementar Redis en producción)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Aquí puedes implementar rate limiting con Redis
            # Por simplicidad, solo registramos el intento
            logger.info(f"Intento de acceso desde IP: {request.remote_addr}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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
        
        # Determinar redirect basado en rol
        if user.role == 'admin':
            redirect_url = url_for('admx.documents')
        else:
            redirect_url = url_for('user.dashboard')
        
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
            'redirect_url': url_for('admx.login')
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