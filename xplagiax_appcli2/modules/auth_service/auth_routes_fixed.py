# auth_routes.py
import os
import re
import logging
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify, session, url_for, redirect, render_template, current_app, g, flash, session, make_response
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,BooleanField, validators
#from extensions_fixed import db, login_manager, mail
from modules.models.model import Users, StoragePlan, ModelVersion, UserModelPreference, ModelPlanAccess, LoginHistory
from settings.connections import mail, limiter
from flask_login import login_user, logout_user, login_required, current_user
from settings.utilities import generate_token, verify_token
from settings.email_service import EmailService, EmailTemplates
from . import totp_crypto, totp_service
import bcrypt
import requests
from flask_mail import Message
from .google_oauth import GoogleOAuth
from .microsoft_oauth import MicrosoftOAuth
from datetime import datetime, timedelta
import secrets
from functools import wraps
from settings.connections import db 

auth_bp = Blueprint('auth_bp', __name__)

# Inicializar servicio OAuth
google_oauth = GoogleOAuth()
microsoft_oauth = MicrosoftOAuth()


# Forms for CSRF protection
class LoginForm(FlaskForm):
    email = StringField('Email', [validators.Email(), validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    remember_me = BooleanField('Remember Me')

class SignupForm(FlaskForm):
    email = StringField('Email', [validators.Email(), validators.DataRequired()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.Length(min=8, message="The password must be at least 8 characters long."),
        validators.Regexp(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', 
                         message="c")
    ])
    password_confirm = PasswordField('Confirmar Password', [
        validators.DataRequired(),
        validators.EqualTo('password', message='Passwords do not match')
    ])
    name = StringField('Name', [validators.Length(max=100)])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.Length(min=8)
    ])

def validate_email_domain(email):
    """Optional: validate email domain whitelist"""
    # You can implement domain restrictions here
    return True

def sanitize_redirect_url(url):
    """Rechaza cualquier URL con scheme o host — solo rutas relativas simples."""
    if not url:
        return url_for('x_users.analysis')
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return url_for('x_users.analysis')
    if not url.startswith('/'):
        return url_for('x_users.analysis')
    return url

def require_active_subscription_or_trial():
    """Decorator to require active subscription or trial"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar si el trial ha expirado primero
            if current_user.is_on_trial and not current_user.is_trial_active():
                current_user.end_trial()
                db.session.add(current_user)
                db.session.commit()
            
            # Verificar si tiene acceso
            if not current_user.has_active_subscription() and not current_user.is_trial_active():
                if request.is_json:
                    return jsonify({
                        'error': 'This feature requires an active subscription or trial',
                        'trial_expired': True,
                        'redirect': '/pricing'
                    }), 403
                else:
                    flash('This feature requires an active subscription or trial.', 'warning')
                    return redirect(url_for('pricing'))  # Ajusta según tu ruta
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# RUTAS DE GOOGLE OAUTH
# ============================================================================

def find_or_create_user(user_data):
    email = user_data.get('email', '').lower().strip()
    if not email:
        return None, False

    user = Users.query.filter_by(email=email).first()
    is_new_user = False

    if not user:
        plan_starter = StoragePlan.query.filter_by(name="Starter").first()
        user = Users(
            email=email,
            name=user_data.get('name', ''),
            confirmed=True,
            isactive=True,
            user_type="Starter",
            storage_plan_id=plan_starter.id if plan_starter else None,
            oauth_provider='google',
            oauth_id=str(user_data.get('id')),
            confirmed_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        is_new_user = True

    # Generar token JWT
    token = generate_token(user.id)
    user.token = token
    db.session.commit()
    return user, is_new_user

@auth_bp.route('/oauth-status')
def oauth_status():
    """Diagnóstico de configuración OAuth — sin exponer datos sensibles.

    Los client_id son públicos por diseño (viajan en la URL de autorización
    que ve cualquier navegador); de los secretos solo se informa SI están
    definidos, nunca su valor. Sirve para verificar en 5 segundos si las
    credenciales llegaron al proceso y qué redirect_uri se va a usar (esa
    misma URI es la que debe estar registrada en Google/Azure)."""
    def _preview(value):
        return (value[:12] + '…') if value else None

    env_path = os.path.join(current_app.root_path, '.env')
    return jsonify({
        'google': {
            'client_id_set': bool(google_oauth.client_id),
            'client_id_preview': _preview(google_oauth.client_id),
            'client_secret_set': bool(google_oauth.client_secret),
            'redirect_uri': google_oauth.get_redirect_uri(),
            'ready': bool(google_oauth.client_id and google_oauth.client_secret),
        },
        'microsoft': {
            'client_id_set': bool(microsoft_oauth.client_id),
            'client_id_preview': _preview(microsoft_oauth.client_id),
            'client_secret_set': bool(microsoft_oauth.client_secret),
            'redirect_uri': microsoft_oauth.get_redirect_uri(),
            'ready': bool(microsoft_oauth.client_id and microsoft_oauth.client_secret),
        },
        'env_file_expected_at': os.path.abspath(env_path),
        'env_file_exists': os.path.exists(env_path),
        'hint': ('Si ready=false: define GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET en el .env '
                 'o como variables de entorno del proceso y reinicia. La redirect_uri '
                 'mostrada arriba debe estar registrada EXACTAMENTE igual en la consola '
                 'del proveedor.'),
    })


# ── Auto-migración OAuth: columnas nuevas que db.create_all() no añade ───────
# db.create_all() solo crea tablas nuevas, nunca altera las existentes.
# Estas funciones replican el patrón de _ensure_totp_columns() para columnas
# añadidas a LoginHistory (browser, os_name, city, country) y a Users (avatar).
# Sin esto, db.session.commit() falla con "Unknown column" al hacer el INSERT
# del LoginHistory o del User con avatar, cayendo en el except genérico.
_OAUTH_DB_COLUMNS_READY = False


def _ensure_oauth_db_columns():
    """Añade columnas de LoginHistory y Users que pueden faltar en DBs existentes."""
    global _OAUTH_DB_COLUMNS_READY
    if _OAUTH_DB_COLUMNS_READY:
        return
    try:
        from sqlalchemy import inspect as _sa_inspect, text as _sa_text

        # ── logins_xplagiax_clients ───────────────────────────────────────
        login_cols = {c['name'] for c in _sa_inspect(db.engine).get_columns('logins_xplagiax_clients')}
        login_additions = [
            ('browser',  "ALTER TABLE logins_xplagiax_clients ADD COLUMN browser  VARCHAR(128) NULL"),
            ('os_name',  "ALTER TABLE logins_xplagiax_clients ADD COLUMN os_name  VARCHAR(128) NULL"),
            ('city',     "ALTER TABLE logins_xplagiax_clients ADD COLUMN city     VARCHAR(128) NULL"),
            ('country',  "ALTER TABLE logins_xplagiax_clients ADD COLUMN country  VARCHAR(128) NULL"),
        ]
        for col, ddl in login_additions:
            if col not in login_cols:
                db.session.execute(_sa_text(ddl))
                current_app.logger.info("[oauth-db] Added logins_xplagiax_clients.%s", col)

        # ── users ─────────────────────────────────────────────────────────
        user_cols = {c['name'] for c in _sa_inspect(db.engine).get_columns('users')}
        if 'avatar' not in user_cols:
            db.session.execute(_sa_text(
                "ALTER TABLE users ADD COLUMN avatar VARCHAR(200) NULL"))
            current_app.logger.info("[oauth-db] Added users.avatar")

        db.session.commit()
        _OAUTH_DB_COLUMNS_READY = True
        current_app.logger.info("[oauth-db] DB columns verified/created OK")
    except Exception:
        db.session.rollback()
        current_app.logger.warning(
            "[oauth-db] Could not ensure OAuth DB columns — login may fail if columns are missing",
            exc_info=True)


@auth_bp.route("/google/login")
def google_login():
    # Garantizar que las columnas de la DB existan antes de intentar el OAuth.
    # Fail-fast con mensaje visible: sin GOOGLE_CLIENT_ID/SECRET el redirect a
    # Google muere en un "invalid_request" críptico fuera de nuestra app.
    _ensure_oauth_db_columns()
    if not google_oauth.client_id or not google_oauth.client_secret:
        current_app.logger.error(
            "Google OAuth no configurado: define GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET")
        flash('Google sign-in is not available right now. Please use email and password.', 'error')
        return redirect(url_for('x_apps.login'))
    next_url = request.args.get('next', url_for('x_users.analysis'))
    session['oauth_next'] = next_url
    auth_url = google_oauth.get_authorization_url()  # tu cliente OAuth
    current_app.logger.info("Logging in with Google")
    return redirect(auth_url)

@auth_bp.route("/google/callbackx")
def google_callbackx():
    """Callback de Google OAuth - VERSIÓN ULTRA MEJORADA"""
    from flask import session as flask_session
    from flask_login import login_user, current_user
    import traceback
    
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    #print(f" OAuth Callback iniciado: code={bool(code)}, state={bool(state)}, error={error}")

    if error or not code or not state:
        #print(" Parámetros de OAuth inválidos")
        flash('Error en autorización con Google', 'error')
        return redirect(url_for('x_apps.login'))

    try:
        # 1. Intercambiar código por datos de usuario
        user_data, error_msg = google_oauth.exchange_code_for_user_data(code, state)
        if error_msg:
            #print(f" Error intercambiando código: {error_msg}")
            flash(f'Error autenticación: {error_msg}', 'error')
            return redirect(url_for('x_apps.login'))

        email = user_data.get('email', '').lower().strip()
        if not email:
            #print(" No se obtuvo email del usuario")
            flash("No email was obtained from the user", "error")
            return redirect(url_for('x_apps.login'))

        #print(f" Datos de usuario obtenidos: {email}")

        # 2. Buscar o crear usuario
        user = Users.query.filter_by(email=email).first()
        is_new_user = False
        
        if not user:
            #print(f" Creando nuevo usuario: {email}")
            plan_starter = StoragePlan.query.filter_by(name="Starter").first()
            user = Users(
                email=email,
                name=user_data.get('name', ''),
                confirmed=True,
                isactive=True,
                user_type="Starter",
                storage_plan_id=plan_starter.id if plan_starter else None,
                oauth_provider='google',
                oauth_id=str(user_data.get('id')),
                avatar=user_data.get('picture'),  # ✅ Guardar avatar de Google
                confirmed_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()
            is_new_user = True
            #print(f" Usuario creado con ID: {user.id}")
        else:
            #print(f" Usuario existente encontrado: {email}")
            # Actualizar avatar si cambió o no existe
            if user_data.get('picture'):
                user.avatar = user_data.get('picture')
            
            # Asegurar que usuario existente esté activo
            if not user.isactive:
                user.isactive = True
                #print(" Activando usuario existente")
            if not user.confirmed:
                user.confirmed = True
                user.confirmed_at = datetime.utcnow()
                #print(" Confirmando usuario existente")
            # Actualizar datos OAuth si no existen
            if not user.oauth_provider:
                user.oauth_provider = 'google'
                user.oauth_id = str(user_data.get('id'))

        # 3. Generar token JWT
        token = generate_token(user.id)
        user.token = token
        
        #  COMMIT ANTES DE LOGIN
        db.session.commit()
        #print(f" Usuario guardado en DB y token generado")

        # 4. LIMPIAR SESIÓN COMPLETAMENTE
        flask_session.clear()
        #print(" Sesión completamente limpiada")

        # 5.  CONFIGURAR SESIÓN PERMANENTE ANTES DEL LOGIN
        flask_session.permanent = True
        
        # 6.  LOGIN CON CONFIGURACIÓN ESPECÍFICA
        #print(f" Intentando login para usuario ID: {user.id}")
        
        # Verificar que el user_loader funciona ANTES del login
        from flask import current_app
        loaded_user = current_app.login_manager._user_callback(str(user.id))
        if not loaded_user:
            #print(" CRÍTICO: user_loader falla antes del login")
            flash("Authentication system error", "error")
            return redirect(url_for('x_apps.login'))
        
        #print(f" user_loader funciona correctamente: {loaded_user.email}")
        
        # LOGIN CON REMEMBER=TRUE Y FRESH=TRUE
        login_success = login_user(
            user, 
            remember=True,
            duration=None,  # Usar PERMANENT_SESSION_LIFETIME
            force=False,
            fresh=True
        )
        
        #print(f" login_user resultado: {login_success}")

        # 7. VERIFICACIÓN INMEDIATA POST-LOGIN
        if not login_success:
            #print(" CRÍTICO: login_user falló")
            flash("Critical error logging in", "error")
            return redirect(url_for('x_apps.login'))
        
        # Verificar current_user inmediatamente después del login
        if not current_user.is_authenticated:
            #print(" CRÍTICO: current_user no está autenticado después del login")
            flash("Authentication error", "error")
            return redirect(url_for('x_apps.login'))
            
        #print(f" current_user post-login: {current_user.email} (ID: {current_user.id})")

        # 8. CREAR SESIÓN PERSONALIZADA
        try:
            session_token = user.create_session()
            flask_session['session_token'] = session_token
            flask_session['token'] = token
            flask_session['user_id'] = user.id  # ✅ Backup adicional
            record_login(user, session_token)
            #print(f" Sesión personalizada creada")
        except Exception as e:
            print(f" Error creando sesión personalizada: {e}")
            # No es crítico, continuar

        # 9.  COMMIT FINAL Y MENSAJE
        db.session.commit()
        
        welcome_msg = f"¡Bienvenido {'de nuevo' if not is_new_user else ''}, {user.name or user.email}!"
        flash(welcome_msg, 'success')
        
        #print(f"🎉 OAuth login COMPLETADO exitosamente para {email}")
        #print(f"📊 Estado final de sesión: {dict(flask_session)}")

        # 10.  REDIRECT ROBUSTO
        next_url = flask_session.pop('oauth_next', None) or url_for('x_users.analysis')
        
        #  ASEGURAR QUE EL REDIRECT SEA ABSOLUTO
        if not next_url.startswith(('http://', 'https://', '/')):
            next_url = url_for('x_users.analysis')
            
        #print(f"🔄 Redirigiendo a: {next_url}")
        
        #  USAR MAKE_RESPONSE PARA MÁS CONTROL
        response = make_response(redirect(next_url))
        
        #  CONFIGURAR HEADERS DE SESIÓN
        response.set_cookie('session_active', 'true', max_age=3600, httponly=False)
        
        return response

    except Exception as e:
        current_app.logger.exception("[google-oauth] EXCEPCIÓN CRÍTICA en OAuth callback")
        try:
            db.session.rollback()
        except Exception:
            pass  # Si la DB está caída, el rollback también fallará, evitar 500
        
        #  LIMPIAR SESIÓN EN CASO DE ERROR
        flask_session.clear()
        
        flash("An internal error occurred while authenticating with Google. Please try again.", "error")
        return redirect(url_for('x_apps.login'))
 
@auth_bp.route("/microsoft/login")
def microsoft_login():
    """Iniciar login con Microsoft"""
    _ensure_oauth_db_columns()
    if not microsoft_oauth.client_id or not microsoft_oauth.client_secret:
        current_app.logger.error(
            "Microsoft OAuth no configurado: define MICROSOFT_CLIENT_ID y MICROSOFT_CLIENT_SECRET")
        flash('Microsoft sign-in is not available right now. Please use email and password.', 'error')
        return redirect(url_for('x_apps.login'))
    next_url = request.args.get('next', url_for('x_users.analysis'))
    session['oauth_next'] = next_url
    auth_url = microsoft_oauth.get_authorization_url()
    current_app.logger.info("Iniciando login con Microsoft")
    return redirect(auth_url)

def _save_microsoft_avatar(user, access_token):
    """Guarda la foto de perfil de Microsoft de forma best-effort.

    NUNCA debe abortar la autenticación: antes, un fallo aquí (el directorio
    static/img/avatars no existe en un despliegue limpio) lanzaba
    FileNotFoundError dentro del try global del callback y hacía rollback
    del login/creación de usuario completos."""
    try:
        photo_content = microsoft_oauth.get_user_photo(access_token)
        if not photo_content:
            return
        photo_dir = os.path.join(current_app.root_path, 'static', 'img', 'avatars')
        os.makedirs(photo_dir, exist_ok=True)
        photo_filename = f"ms_{user.id}.jpg"
        with open(os.path.join(photo_dir, photo_filename), 'wb') as f:
            f.write(photo_content)
        user.avatar = f"/static/img/avatars/{photo_filename}"
    except Exception:
        current_app.logger.warning("No se pudo guardar el avatar de Microsoft", exc_info=True)


@auth_bp.route("/microsoft/callback")
def microsoft_callback():
    """Callback de Microsoft OAuth"""
    from flask import session as flask_session
    from flask_login import login_user, current_user
    import traceback
    
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    error_description = request.args.get('error_description')

    #print(f" Microsoft OAuth Callback: code={bool(code)}, state={bool(state)}, error={error}")

    if error:
        #print(f" Error de Microsoft: {error} - {error_description}")
        flash(f'Microsoft Error: {error_description or error}', 'error')
        return redirect(url_for('x_apps.login'))

    if not code or not state:
        #print(" Parámetros de OAuth inválidos")
        flash('Invalid authorization parameters', 'error')
        return redirect(url_for('x_apps.login'))

    try:
        # 1. Intercambiar código por datos de usuario
        user_data, error_msg = microsoft_oauth.exchange_code_for_user_data(code, state)
        if error_msg:
            #print(f" Error intercambiando código: {error_msg}")
            flash(f'Authentication error: {error_msg}', 'error')
            return redirect(url_for('x_apps.login'))

        email = user_data.get('email', '').lower().strip()
        if not email:
            #print(" No se obtuvo email del usuario")
            flash("No email was obtained from the user", "error")
            return redirect(url_for('x_apps.login'))

        #print(f" Datos de usuario Microsoft obtenidos: {email}")

        # 2. Buscar o crear usuario (reutilizar la misma lógica)
        user = Users.query.filter_by(email=email).first()
        is_new_user = False
        
        if not user:
            #print(f" Creando nuevo usuario Microsoft: {email}")
            plan_starter = StoragePlan.query.filter_by(name="Starter").first()
            user = Users(
                email=email,
                name=user_data.get('name', ''),
                confirmed=True,
                isactive=True,
                user_type="Starter",
                storage_plan_id=plan_starter.id if plan_starter else None,
                oauth_provider='microsoft',  # ✅ Cambio aquí
                oauth_id=str(user_data.get('id')),
                confirmed_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()
            is_new_user = True

            # ✅ Obtener y guardar foto de Microsoft (best-effort, nunca aborta el login)
            if user_data.get('access_token'):
                _save_microsoft_avatar(user, user_data['access_token'])

            #print(f" Usuario Microsoft creado con ID: {user.id}")
        else:
            #print(f" Usuario existente encontrado: {email}")
            # ✅ Actualizar foto de Microsoft si es necesario (best-effort)
            if user_data.get('access_token'):
                _save_microsoft_avatar(user, user_data['access_token'])

            # Asegurar que usuario existente esté activo
            if not user.isactive:
                user.isactive = True
                #print(" Activando usuario existente")
            if not user.confirmed:
                user.confirmed = True
                user.confirmed_at = datetime.utcnow()
                #print(" Confirmando usuario existente")
            # Actualizar datos OAuth si no existen
            if not user.oauth_provider:
                user.oauth_provider = 'microsoft'  #  Cambio aquí
                user.oauth_id = str(user_data.get('id'))

        # 3. Generar token JWT (misma lógica que Google)
        token = generate_token(user.id)
        user.token = token
        
        # COMMIT ANTES DE LOGIN
        db.session.commit()
        #print(f" Usuario Microsoft guardado en DB y token generado")

        # 4. LIMPIAR SESIÓN COMPLETAMENTE
        flask_session.clear()
        #print("🧹 Sesión completamente limpiada")

        # 5. CONFIGURAR SESIÓN PERMANENTE ANTES DEL LOGIN
        flask_session.permanent = True
        
        # 6. LOGIN CON CONFIGURACIÓN ESPECÍFICA
        #print(f" Intentando login para usuario Microsoft ID: {user.id}")
        
        # Verificar que el user_loader funciona ANTES del login
        from flask import current_app
        loaded_user = current_app.login_manager._user_callback(str(user.id))
        if not loaded_user:
            print("❌ CRÍTICO: user_loader falla antes del login")
            flash("Authentication system error", "error")
            return redirect(url_for('x_apps.login'))
        
        print(f"✅ user_loader funciona correctamente: {loaded_user.email}")
        
        # LOGIN CON REMEMBER=TRUE Y FRESH=TRUE
        login_success = login_user(
            user, 
            remember=True,
            duration=None,
            force=False,
            fresh=True
        )
        
        print(f"✅ login_user resultado: {login_success}")

        # 7. VERIFICACIÓN INMEDIATA POST-LOGIN
        if not login_success:
            print("❌ CRÍTICO: login_user falló")
            flash("Critical error logging in", "error")
            return redirect(url_for('x_apps.login'))
        
        if not current_user.is_authenticated:
            print("❌ CRÍTICO: current_user no está autenticado después del login")
            flash("Authentication error", "error")
            return redirect(url_for('x_apps.login'))
            
        print(f"✅ current_user post-login: {current_user.email} (ID: {current_user.id})")

        # 8. CREAR SESIÓN PERSONALIZADA
        try:
            session_token = user.create_session()
            flask_session['session_token'] = session_token
            flask_session['token'] = token
            flask_session['user_id'] = user.id
            record_login(user, session_token)
            print(f"✅ Sesión personalizada Microsoft creada")
        except Exception as e:
            print(f"⚠️ Error creando sesión personalizada: {e}")

        # 9. COMMIT FINAL Y MENSAJE
        db.session.commit()
        
        welcome_msg = f"¡Bienvenido {'de nuevo' if not is_new_user else ''} con Microsoft, {user.name or user.email}!"
        flash(welcome_msg, 'success')
        
        print(f"🎉 Microsoft OAuth login COMPLETADO exitosamente para {email}")

        # 10. REDIRECT ROBUSTO
        next_url = flask_session.pop('oauth_next', None) or url_for('x_users.analysis')
        
        if not next_url.startswith(('http://', 'https://', '/')):
            next_url = url_for('x_users.analysis')
            
        print(f"🔄 Redirigiendo a: {next_url}")
        
        response = make_response(redirect(next_url))
        response.set_cookie('session_active', 'true', max_age=3600, httponly=False)
        
        return response

    except Exception as e:
        current_app.logger.exception("[microsoft-oauth] EXCEPCIÓN CRÍTICA en OAuth callback")
        try:
            db.session.rollback()
        except Exception:
            pass
        
        flask_session.clear()
        
        flash("Internal error in authentication with Microsoft. Please try again.", "error")
        return redirect(url_for('x_apps.login'))

# Endpoints donde avisar "sesión expirada" es puro ruido: el usuario ya está
# en (o yendo hacia) la pantalla de login/registro, o iniciando un flujo OAuth.
_SESSION_FLASH_EXEMPT = ('x_apps.login', 'x_apps.index', 'x_apps.register')


@auth_bp.before_app_request
def security_checks():
    """Single-session enforcement and trial expiry check"""
    g.session_invalidated = False

    # Single-session enforcement
    if current_user.is_authenticated:
        try:
            stored_token = session.get('session_token')
            if not stored_token or not current_user.is_session_valid(stored_token):
                logout_user()
                session.clear()
                g.session_invalidated = True
                # El blueprint se llama 'auth_bp': el check anterior
                # startswith('auth.') no coincidía nunca y el aviso se
                # disparaba incluso al pulsar los botones de OAuth.
                if (request.endpoint
                        and not request.endpoint.startswith('auth_bp.')
                        and request.endpoint not in _SESSION_FLASH_EXEMPT):
                    flash('Your session has expired. Please log in again.', 'warning')
        except Exception as e:
            current_app.logger.exception("Session validation error")
            logout_user()
            session.clear()
            g.session_invalidated = True
        
      # Trial expiry check - MEJORADO
    if current_user.is_authenticated and current_user.is_on_trial:
        try:
            if not current_user.is_trial_active():
                # Trial expirado - ejecutar limpieza
                current_user.end_trial()
                db.session.add(current_user)
                db.session.commit()
                
                # Mostrar mensaje solo una vez por sesión
                if not session.get('trial_expired_notified'):
                    flash('Your trial period has expired. You have been moved to the free plan.', 'warning')
                    session['trial_expired_notified'] = True
                    
                current_app.logger.info(f"Trial expired for user {current_user.email}")
        except Exception as e:
            current_app.logger.exception("Trial expiry check error")

    # Trial expiry check
    #if current_user.is_authenticated and current_user.is_on_trial:
    #    try:
    #        if not current_user.is_trial_active():
    #            current_user.end_trial()
    #            db.session.add(current_user)
    #            db.session.commit()
    #            flash('Your trial period has expired.', 'info')
    #    except Exception as e:
    #        current_app.logger.exception("Trial expiry check error")

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per 15 minutes")
def login():
    if request.method == 'GET':
        return redirect(url_for('x_apps.login'))
        #return render_template('auth/login.html')
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        # For JSON requests, skip CSRF for now (implement JWT or other token system)
        remember_me = data.get('remember_me', False)
    else:
        form = LoginForm()
        if not form.validate_on_submit():
            return jsonify({'error': 'Invalid data', 'errors': form.errors}), 400
        data = form.data
        remember_me = form.remember_me.data  # Obtener el valor del checkbox

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    print(f"DEBUG LOGIN: Attempting login for email: '{email}'")
    user = Users.query.filter_by(email=email).first()
    if not user:
        print(f"DEBUG LOGIN: User not found for email: '{email}'")
        return jsonify({'error': 'Incorrect credentials'}), 401
    
    print(f"DEBUG LOGIN: User found: {user.id}, Active: {user.isactive}, Confirmed: {user.confirmed}")
    
    if not user.isactive:
        print("DEBUG LOGIN: User account is not active")
        return jsonify({'error': 'Account not activated. Check your email.'}), 401

    # El user_loader exige isactive Y confirmed: sin este check, un usuario no
    # confirmado recibía "Session started successfully" y quedaba deslogueado
    # en la request siguiente (login fantasma, sin mensaje de error).
    if not user.confirmed:
        print("DEBUG LOGIN: User account is not confirmed")
        return jsonify({'error': 'Please confirm your email before signing in.'}), 401

    if not user._password_hash:
        print("DEBUG LOGIN: User has no password hash (OAuth user?)")
        return jsonify({'error': 'This account was created with Google/Microsoft. Use the corresponding button.'}), 400
    
    if not bcrypt.checkpw(password.encode('utf-8'), user._password_hash.encode('utf-8')):
        print("DEBUG LOGIN: Password mismatch")
        return jsonify({'error': 'Incorrect credentials'}), 401

    # 2FA gate: password verified but the session is NOT created yet. A
    # short-lived signed token (same itsdangerous mechanism as confirm/reset
    # email links — stateless, no extra session/table) identifies WHO is
    # mid-login without granting access. The real session is only created in
    # verify_2fa_login() below, after the TOTP/recovery code checks out.
    _ensure_totp_columns()
    if user.totp_enabled:
        pending_token = user.get_token('2fa_pending', expires_sec=300)
        return jsonify({'requires_2fa': True, 'pending_token': pending_token}), 200

    # Create new session (invalidates any existing session)
    session_token = user.create_session()
    db.session.add(user)
    record_login(user, session_token)
    db.session.commit()

    session['session_token'] = session_token
    login_user(user, remember = remember_me)

    next_url = sanitize_redirect_url(request.args.get('next'))
    return jsonify({
        'message': 'Session started successfully',
        'redirect': next_url
    }), 200

@auth_bp.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        try:
            entry = LoginHistory(
                user_id=current_user.id,
                event_type='logout',
                ip_address=_get_client_ip(),
                user_agent=request.headers.get('User-Agent', '')[:512],
                session_token=current_user.session_token,
            )
            db.session.add(entry)
        except Exception:
            current_app.logger.exception("Failed to record logout history")
        current_user.invalidate_session()
        db.session.add(current_user)
        db.session.commit()
    logout_user()
    session.clear()
    flash('Session successfully closed', 'success')
    return redirect(url_for('x_apps.login'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("3 per 15 minutes")
def signup():
    if request.method == 'GET':
        # auth/signup.html no existe (TemplateNotFound → 500). El registro vive
        # en sign_users.html, que activa el panel de registro con ?mode=register.
        return redirect(url_for('x_apps.login', mode='register'))

    if request.is_json:
        data = request.get_json()
    else:
        form = SignupForm()
        if not form.validate_on_submit():
            return jsonify({'error': 'Invalid data', 'errors': form.errors}), 400
        data = form.data

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    lastname = (data.get('lastname') or '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': 'Formato de email inválido'}), 400

    if Users.query.filter_by(email=email).first():
        return jsonify({'error': 'This email is already registered'}), 400

    if not validate_email_domain(email):
        return jsonify({'error': 'Email domain not allowed'}), 400

    # Get Starter plan
    starter_plan = StoragePlan.query.filter_by(name="Starter").first()
    if not starter_plan:
        return jsonify({'error': 'Configuration error. Contact support.'}), 500

    try:
        # Hash password with bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = Users(
            email = email,
            _password_hash = hashed,
            name = name,
            lastname = lastname,
            storage_plan_id = starter_plan.id,
            user_type = "Starter",
            confirmed=True,  # Auto-confirm for local use
            isactive=True    # Auto-activate for local use
        )
        
        db.session.add(user)
        db.session.commit()

        # Send confirmation email
        token = user.get_token('confirm')
        confirm_url = url_for('auth_bp.confirm_email', token = token, _external=True)
        
        #try:

        # Enviar email de confirmación
        email_result = EmailTemplates.send_confirmation_email(
            user_email=user.email,
            confirm_url=confirm_url,
            user_name=user.name
        )
        
        # Log del resultado del email
        if email_result['success']:
            current_app.logger.info(f"Confirmation email sent successfully using {email_result['provider_used']}")
        else:
            current_app.logger.warning(f"Failed to send confirmation email: {email_result['message']}")
            
        return jsonify({
            'message': 'Username created successfully. Check your email to confirm your account.'
        }), 201
        
        #except Exception as e:
        #    current_app.logger.exception("Failed to send confirmation email")
            # Don't fail registration if email fails
            
        
    except Exception as e:
        current_app.logger.exception("Signup error")
        db.session.rollback()
        return jsonify({'error': 'Internal error. Please try again.'}), 500

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    user = Users.verify_token(token, 'confirm')  # 24 hours
    if not user:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for('x_apps.login'))
    
    if user.confirmed:
        flash('Your account is now confirmed.', 'info')
        return redirect(url_for('x_apps.login'))
    
    user.confirmed = True
    user.confirmed_at = datetime.utcnow()
    user.isactive = True
    db.session.add(user)
    db.session.commit()
    
    flash('Account confirmed! You can now log in.', 'success')
    return redirect(url_for('x_apps.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per 15 minutes")
def forgot_password():
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    data = request.get_json() or request.form
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email requerido'}), 400

    user = Users.query.filter_by(email=email).first()
    
    # Always return success message for security (don't reveal if email exists)
    success_msg = 'If the email exists in our system, you will receive a recovery link.'
    
    if user and user.isactive:
        try:
            token = user.get_token('reset')
            reset_url = url_for('auth_bp.reset_password', token=token, _external=True)
            
            # Usar EmailService para envío de reset
            email_result = EmailTemplates.send_password_reset(
                user_email = user.email,
                reset_url = reset_url,
                user_name = user.name
            )
            
            # Log del resultado
            if email_result['success']:
                current_app.logger.info(f"Password reset email sent using {email_result['provider_used']}")
            else:
                current_app.logger.error(f"Failed to send reset email: {email_result['message']}")
        except Exception as e:
            current_app.logger.exception("Failed to send reset email")
    
    return jsonify({'message': success_msg}), 200

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per 15 minutes")
def reset_password(token):
    user = Users.verify_token(token, 'reset')  # 24 hour
    if not user:
        flash('The recovery link is invalid or has expired.', 'error')
        return redirect(url_for('x_apps.forgot_password'))
    
    if request.method == 'GET':
        return render_template('auth/reset_password.html', token=token)
    
    if request.is_json:
        data = request.get_json()
    else:
        form = ResetPasswordForm()
        if not form.validate_on_submit():
            return jsonify({'error': 'Invalid data', 'errors': form.errors}), 400
        data = form.data

    new_password = data.get('password', '')
    if not new_password or len(new_password) < 8:
        return jsonify({'error': 'The password must be at least 8 characters long.'}), 400

    try:
        # Hash new password
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user._password_hash = hashed
        
        # Invalidate all sessions for security
        user.invalidate_session()
        
        db.session.add(user)
        db.session.commit()
        
        # Opcional: Enviar email de confirmación de cambio de contraseña
        try:
            html_content = render_template('emails/password_changed.html', 
                                         user_name=user.name or user.email)
            
            email_result = EmailService.send_email(
                subject='Password Changed - XPlagiax',
                recipients=[user.email],
                html_content=html_content,
                provider='noreply',
                fallback_provider='gmail'
            )
            
            if email_result['success']:
                current_app.logger.info(f"Password change notification sent using {email_result['provider_used']}")
        except Exception as e:
            current_app.logger.exception("Failed to send password change notification")
        
        flash('Password updated successfully. You can log in.', 'success')
        return jsonify({'message': 'Password updated', 'redirect': url_for('auth_bp.login')}), 200
        
    except Exception as e:
        current_app.logger.exception("Password reset error")
        return jsonify({'error': 'Internal error. Please try again.'}), 500

@auth_bp.route('/resend-confirmation', methods=['POST'])
@limiter.limit("3 per 15 minutes")
def resend_confirmation():
    data = request.get_json() or request.form
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    user = Users.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'If the email exists, a new link will be sent.'}), 200
    
    if user.confirmed:
        return jsonify({'error': 'This account is already confirmed'}), 400
    
    #try:
    # user.generate_token no existe (el método del modelo es get_token) y el
    # blueprint se llama auth_bp, no auth — ambos producían 500 en esta ruta.
    token = user.get_token('confirm')
    confirm_url = url_for('auth_bp.confirm_email', token=token, _external=True)
    
    # Usar EmailService
    email_result = EmailTemplates.send_confirmation_email(
        user_email=user.email,
        confirm_url=confirm_url,
        user_name=user.name
    )
    
    if email_result['success']:
        current_app.logger.info(f"Confirmation resent using {email_result['provider_used']}")
        return jsonify({'message': 'New confirmation link sent.'}), 200
    else:
        current_app.logger.error(f"Failed to resend confirmation: {email_result['message']}")
        return jsonify({'error': 'Error sending email. Please try again later.'}), 500

    #except Exception as e:
    #    current_app.logger.exception("Failed to resend confirmation")
    #    return jsonify({'error': 'Error sending email. Please try again later.'}), 500

@auth_bp.route('/start-trial', methods=['POST'])
#@login_required
def start_trial():
    """Start trial for eligible plans"""
    data = request.get_json() or request.form
    plan_name = data.get('plan')
    
    if not plan_name:
        return jsonify({'error': 'Required plan'}), 400
    
    # Verificar si tiene cuenta Starter primero
    if current_user.user_type != 'Starter':
        return jsonify({
            'error': 'You need to create a Starter account before you can start a trial'
        }), 403
        
    if current_user.is_on_trial:
        return jsonify({'error': 'You already have an active trial'}), 400
    
    if current_user.has_active_subscription():
        return jsonify({'error': 'You already have an active subscription'}), 400
    
    # Find the plan
    plan = StoragePlan.query.filter_by(name=plan_name, is_active=True).first()
    if not plan or plan.trial_days <= 0:
        return jsonify({'error': 'Plan not available for trial'}), 400
     
    try:
        # Update user plan and start trial
        current_user.storage_plan_id = plan.id
        current_user.user_type = plan_name
        
        if current_user.start_trial(plan.trial_days):
            db.session.add(current_user)
            db.session.commit()
            
            return jsonify({
                'message': f'Trial of {plan.trial_days} days started for {plan_name}',
                'trial_ends': current_user.trial_ends_at.isoformat(),
                'redirect': url_for('x_users.analysis')
            }), 200
        else:
            return jsonify({'error': 'The trial could not be started'}), 500
            
    except Exception as e:
        current_app.logger.exception("Trial start error")
        db.session.rollback()
        return jsonify({'error': 'Error interno'}), 500

@auth_bp.route('/start-trial_NO', methods=['POST'])
def start_trial_NO():  # SIN decorador login_required
    """Start trial for eligible plans"""
    
    # Verificar autenticación manualmente para API
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required', 'redirect': '/login'}), 401
    
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        plan_name = data.get('plan')
        
        if not plan_name:
            return jsonify({'error': 'Plan name is required'}), 400
        
        current_app.logger.info(f"User {current_user.id} requesting trial for {plan_name}")
        
        # Verificar si tiene cuenta Starter primero
        if current_user.user_type != 'starter':
            return jsonify({
                'error': 'You need to create a Starter account before you can start a trial',
                'needs_starter': True
            }), 403
        
        if current_user.is_on_trial:
            return jsonify({'error': 'You already have an active trial'}), 400
        
        if current_user.has_active_subscription():
            return jsonify({'error': 'You already have an active subscription'}), 400
        
        # Find the plan
        plan = StoragePlan.query.filter_by(name=plan_name, is_active=True).first()
        if not plan:
            return jsonify({'error': 'Plan not found'}), 404
            
        if plan.trial_days <= 0:
            return jsonify({'error': 'This plan does not offer a trial'}), 400
        
        # Update user plan and start trial
        current_user.storage_plan_id = plan.id
        current_user.user_type = plan_name
        
        if current_user.start_trial(plan.trial_days):
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'{plan.trial_days}-day trial started for {plan_name}',
                'trial_ends': current_user.trial_ends_at.isoformat(),
                'redirect': url_for('x_users.analysis')
            }), 200
        else:
            db.session.rollback()
            return jsonify({'error': 'Failed to start trial'}), 500
            
    except Exception as e:
        current_app.logger.exception("Trial start error")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/check-trial-status', methods=['GET'])
@login_required
def check_trial_status():
    """Check current trial status and handle expiration"""
    try:
        # Verificar si el trial ha expirado
        if current_user.is_on_trial and current_user.trial_ends_at:
            from datetime import datetime
            if datetime.utcnow() > current_user.trial_ends_at:
                # Trial expirado - limpiar automáticamente
                current_user.end_trial()
                db.session.add(current_user)
                db.session.commit()
                
                return jsonify({
                    'trial_expired': True,
                    'trial_active': False,
                    'is_on_trial': False,
                    'message': 'Your trial has expired',
                    'current_plan': current_user.user_type,
                    'days_remaining': 0,
                    'total_trial_days': 5  # ✅ AGREGADO
                })
        
        # Calcular días restantes
        days_remaining = 0
        total_trial_days = 5  # Default
        
        if current_user.is_on_trial and current_user.trial_ends_at:
            time_left = current_user.trial_ends_at - datetime.utcnow()
            days_remaining = max(0, time_left.days)
            
            # ✅ CALCULAR DÍAS TOTALES DESDE EL PLAN
            if current_user.storage_plan_id:
                plan = StoragePlan.query.get(current_user.storage_plan_id)
                if plan and plan.trial_days:
                    total_trial_days = plan.trial_days
        
        return jsonify({
            'trial_expired': False,
            'trial_active': current_user.is_trial_active() if hasattr(current_user, 'is_trial_active') else False,
            'is_on_trial': current_user.is_on_trial,
            'trial_ends_at': current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
            'current_plan': current_user.user_type,
            'days_remaining': days_remaining,
            'total_trial_days': total_trial_days,  # ✅ AGREGADO
            'subscription_status': current_user.subscription_status
        })
        
    except Exception as e:
        current_app.logger.exception("Error checking trial status")
        return jsonify({'error': 'Error checking trial status'}), 500

@auth_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    if request.method == 'GET':
        return jsonify({
            'email': current_user.email,
            'name': current_user.name,
            'lastname': current_user.lastname,
            'institute': current_user.institute,
            'country': current_user.country,
            'user_type': current_user.user_type,
            'is_on_trial': current_user.is_on_trial,
            'trial_ends_at': current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
            'subscription_status': current_user.subscription_status,
            'storage_usage': {
                'used_bytes': current_user.used_storage_bytes,
                'total_bytes': current_user.get_total_storage_limit_bytes(),
                'percentage': current_user.get_storage_usage_percentage()
            }
        })
    
    # Update profile
    data = request.get_json()
    allowed_fields = ['name', 'lastname', 'institute', 'country']
    
    try:
        for field in allowed_fields:
            if field in data:
                setattr(current_user, field, data[field])
        
        db.session.add(current_user)
        db.session.commit()
        
        return jsonify({'message': 'Updated profile'}), 200
        
    except Exception as e:
        current_app.logger.exception("Profile update error")
        db.session.rollback()
        return jsonify({'error': 'Error updating profile'}), 500


# Error handlers
@auth_bp.errorhandler(429)
def rate_limit_handler(e):
    return jsonify({'error': 'Too many attempts. Please try again later.'}), 429

@auth_bp.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Invalid request'}), 400

@auth_bp.route('/api/models/available', methods=['GET'])
@login_required
def get_available_models():
    """
    Obtiene todos los modelos disponibles y marca cuáles puede acceder el usuario
    según su plan.
    
    Returns:
        JSON con la lista de modelos, modelo actual y plan del usuario
    """
    try:
        # Obtener plan del usuario
        user_plan = current_user.user_type or 'Starter'
        
        # Obtener todos los modelos activos ordenados por 'order'
        all_models = ModelVersion.query.filter_by(
            is_active=True
        ).order_by(ModelVersion.order).all()
        
        # Obtener modelo actual del usuario
        user_preference = UserModelPreference.query.filter_by(
            user_id=current_user.id
        ).first()
        
        current_model_id = user_preference.model_version_id if user_preference else None
        
        # Si no tiene modelo seleccionado, asignar el modelo por defecto del plan
        if not current_model_id:
            default_access = ModelPlanAccess.query.filter_by(
                plan_name=user_plan,
                is_default=True
            ).first()
            
            if default_access:
                # Crear preferencia automática
                new_preference = UserModelPreference(
                    user_id=current_user.id,
                    model_version_id=default_access.model_version_id
                )
                db.session.add(new_preference)
                db.session.commit()
                current_model_id = default_access.model_version_id
        
        # Construir respuesta con modelos
        models_data = []
        for model in all_models:
            # Verificar si el usuario tiene acceso al modelo
            has_access = ModelPlanAccess.query.filter_by(
                model_version_id=model.id,
                plan_name=user_plan
            ).first() is not None
            
            models_data.append({
                'id': model.id,
                'name': model.name,
                'version': model.version,
                'biological_name': model.biological_name,
                'description': model.description,
                'icon': model.icon,
                'available': has_access,
                'order': model.order
            })
        
        return jsonify({
            'success': True,
            'models': models_data,
            'current_model_id': current_model_id,
            'user_plan': user_plan
        })
        
    except Exception as e:
        print(f"Error getting available models: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener los modelos disponibles'
        }), 500


@auth_bp.route('/api/models/select', methods=['POST'])
@login_required
def select_model():
    """
    Permite al usuario seleccionar un modelo si tiene acceso a él.
    
    Body params:
        model_id (int): ID del modelo a seleccionar
        
    Returns:
        JSON con el resultado de la operación
    """
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        
        if not model_id:
            return jsonify({
                'success': False,
                'message': 'ID de modelo requerido'
            }), 400
        
        # Verificar que el modelo existe y está activo
        model = ModelVersion.query.filter_by(
            id=model_id,
            is_active=True
        ).first()
        
        if not model:
            return jsonify({
                'success': False,
                'message': 'Modelo no encontrado o inactivo'
            }), 404
        
        # Verificar que el usuario tiene acceso al modelo
        user_plan = current_user.user_type or 'Starter'
        has_access = ModelPlanAccess.query.filter_by(
            model_version_id=model_id,
            plan_name=user_plan
        ).first()
        
        if not has_access:
            return jsonify({
                'success': False,
                'message': 'No tienes acceso a este modelo. Actualiza tu plan para desbloquearlo.'
            }), 403
        
        # Buscar o crear la preferencia del usuario
        user_preference = UserModelPreference.query.filter_by(
            user_id=current_user.id
        ).first()
        
        if user_preference:
            # Actualizar modelo existente
            user_preference.model_version_id = model_id
            user_preference.updated_at = db.func.now()
        else:
            # Crear nueva preferencia
            user_preference = UserModelPreference(
                user_id=current_user.id,
                model_version_id=model_id
            )
            db.session.add(user_preference)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Modelo actualizado correctamente',
            'model': {
                'id': model.id,
                'name': model.name,
                'version': model.version,
                'icon': model.icon
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error selecting model: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al seleccionar el modelo'
        }), 500


@auth_bp.route('/api/models/current', methods=['GET'])
@login_required
def get_current_model():
    """
    Obtiene el modelo actualmente seleccionado por el usuario.
    
    Returns:
        JSON con los datos del modelo actual
    """
    try:
        user_preference = UserModelPreference.query.filter_by(
            user_id=current_user.id
        ).first()
        
        if not user_preference:
            # Retornar modelo por defecto del plan
            user_plan = current_user.user_type or 'Starter'
            default_access = ModelPlanAccess.query.filter_by(
                plan_name=user_plan,
                is_default=True
            ).first()
            
            if not default_access:
                return jsonify({
                    'success': False,
                    'message': 'No hay modelo disponible'
                }), 404
            
            model = ModelVersion.query.get(default_access.model_version_id)
        else:
            model = ModelVersion.query.get(user_preference.model_version_id)
        
        if not model or not model.is_active:
            return jsonify({
                'success': False,
                'message': 'Modelo no encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'model': {
                'id': model.id,
                'name': model.name,
                'version': model.version,
                'biological_name': model.biological_name,
                'description': model.description,
                'icon': model.icon
            }
        })
        
    except Exception as e:
        print(f"Error getting current model: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener el modelo actual'
        }), 500


def get_user_current_model(user):
    """
    Función helper para obtener el modelo actual de un usuario.
    Útil para usar en otros endpoints.
    
    Args:
        user: Objeto Users
        
    Returns:
        ModelVersion o None
    """
    user_preference = UserModelPreference.query.filter_by(
        user_id=user.id
    ).first()
    
    if not user_preference:
        # Retornar modelo por defecto
        user_plan = user.user_type or 'Starter'
        default_access = ModelPlanAccess.query.filter_by(
            plan_name=user_plan,
            is_default=True
        ).first()
        
        if default_access:
            return ModelVersion.query.filter_by(
                id=default_access.model_version_id,
                is_active=True
            ).first()
        return None
    
    return ModelVersion.query.filter_by(
        id=user_preference.model_version_id,
        is_active=True
    ).first()


# ── Login history helpers ─────────────────────────────────────────────────────

def _parse_ua(ua_string):
    """Return (browser, os_name) from a raw User-Agent string without extra deps."""
    ua = ua_string or ''
    browser = 'Unknown Browser'
    for name, token in [('Edge', 'Edg/'), ('Chrome', 'Chrome/'), ('Firefox', 'Firefox/'),
                        ('Safari', 'Safari/'), ('Opera', 'OPR/')]:
        if token in ua:
            version = ua.split(token)[1].split(' ')[0].split('.')[0]
            browser = f'{name} {version}'
            break
    os_name = 'Unknown OS'
    for name, token in [('Windows 11', 'Windows NT 10.0'), ('Windows', 'Windows'),
                        ('macOS', 'Macintosh'), ('Android', 'Android'),
                        ('iOS', 'iPhone'), ('Linux', 'Linux')]:
        if token in ua:
            os_name = name
            break
    return browser, os_name


def _get_client_ip():
    forwarded = request.environ.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '—'


def record_login(user, session_token):
    """Insert a login row into logins_xplagiax_clients after a successful login.

    El flush() inmediato detecta columnas faltantes DENTRO del try/except,
    evitando que el error burbujee al commit() externo del callback de OAuth
    y cause el genérico "An internal error occurred"."""
    try:
        ua_string = request.headers.get('User-Agent', '')
        browser, os_name = _parse_ua(ua_string)
        ip = _get_client_ip()
        entry = LoginHistory(
            user_id=user.id,
            event_type='login',
            ip_address=ip,
            user_agent=ua_string[:512],
            browser=browser,
            os_name=os_name,
            session_token=session_token,
        )
        db.session.add(entry)
        db.session.flush()  # detectar errores de columna aquí, no en el commit externo
    except Exception:
        current_app.logger.exception("Failed to record login history")
        try:
            db.session.rollback()  # descartar solo la entrada de historial, no el usuario
        except Exception:
            pass


# ── Two-Factor Authentication (TOTP) ──────────────────────────────────────────
# db.create_all() only creates NEW tables, it never ALTERs existing ones (same
# constraint the rest of the project works around — see doc_routes.py's
# _ensure_result_view_column / _ensure_analysis_shares_table). totp_secret
# already existed as VARCHAR(16), too small even for the unencrypted 32-char
# base32 secret; widening it to fit the Fernet ciphertext (~140 chars) and
# adding totp_enabled/totp_recovery_codes needs this same self-healing pattern.
_TOTP_COLUMNS_READY = False


def _ensure_totp_columns():
    global _TOTP_COLUMNS_READY
    if _TOTP_COLUMNS_READY:
        return
    try:
        from sqlalchemy import inspect as _sa_inspect, text as _sa_text
        cols = {c['name']: c for c in _sa_inspect(db.engine).get_columns('users')}
        if 'totp_enabled' not in cols:
            db.session.execute(_sa_text(
                "ALTER TABLE users ADD COLUMN totp_enabled BOOLEAN NOT NULL DEFAULT FALSE"))
        if 'totp_recovery_codes' not in cols:
            db.session.execute(_sa_text(
                "ALTER TABLE users ADD COLUMN totp_recovery_codes TEXT NULL"))
        secret_col = cols.get('totp_secret')
        if secret_col is not None:
            size = getattr(secret_col.get('type'), 'length', None)
            if size is not None and size < 255:
                db.session.execute(_sa_text(
                    "ALTER TABLE users MODIFY COLUMN totp_secret VARCHAR(255) NULL"))
        db.session.commit()
        _TOTP_COLUMNS_READY = True
    except Exception:
        db.session.rollback()
        current_app.logger.warning("Could not ensure users.totp_* columns", exc_info=True)


@auth_bp.route('/2fa/status', methods=['GET'])
@login_required
def totp_status():
    _ensure_totp_columns()
    return jsonify({'enabled': bool(current_user.totp_enabled)})


@auth_bp.route('/2fa/setup', methods=['POST'])
@login_required
def totp_setup():
    """Start enabling 2FA: generate a fresh secret, store it ENCRYPTED but
    with totp_enabled still False (so an abandoned setup never gates login —
    it just gets overwritten by the next /2fa/setup call), and return a QR
    code + the raw secret for manual entry."""
    _ensure_totp_columns()
    if current_user.totp_enabled:
        return jsonify({'error': 'Two-factor authentication is already enabled.'}), 400

    secret = totp_service.generate_secret()
    current_user.totp_secret = totp_crypto.encrypt_secret(secret)
    db.session.add(current_user)
    db.session.commit()

    return jsonify({
        'secret': secret,
        'qr_code': totp_service.provisioning_qr_data_uri(secret, current_user.email),
    })


@auth_bp.route('/2fa/verify-setup', methods=['POST'])
@login_required
@limiter.limit("10 per 15 minutes")
def totp_verify_setup():
    """Confirms the authenticator app is correctly paired before turning 2FA
    on for real — without this step, a typo'd QR scan would silently lock the
    user out on their very next login."""
    _ensure_totp_columns()
    if current_user.totp_enabled:
        return jsonify({'error': 'Two-factor authentication is already enabled.'}), 400

    secret = totp_crypto.decrypt_secret(current_user.totp_secret)
    if not secret:
        return jsonify({'error': 'No pending setup found. Start again.'}), 400

    code = (request.get_json(silent=True) or {}).get('code', '')
    if not totp_service.verify_totp_code(secret, code):
        return jsonify({'error': 'Invalid code. Check your authenticator app and try again.'}), 400

    plain_codes, stored_codes = totp_service.generate_recovery_codes()
    current_user.totp_enabled = True
    current_user.totp_recovery_codes = stored_codes
    db.session.add(current_user)
    db.session.commit()

    return jsonify({'success': True, 'recovery_codes': plain_codes})


@auth_bp.route('/2fa/disable', methods=['POST'])
@login_required
def totp_disable():
    """Requires the current password — same bar as change_password() above.
    Disabling 2FA lowers account security, so it deserves the same proof of
    identity as the rest of this file's sensitive actions."""
    _ensure_totp_columns()
    if not current_user.totp_enabled:
        return jsonify({'error': 'Two-factor authentication is not enabled.'}), 400

    password = (request.get_json(silent=True) or {}).get('password', '')
    if not current_user._password_hash or not bcrypt.checkpw(
        password.encode('utf-8'), current_user._password_hash.encode('utf-8')
    ):
        return jsonify({'error': 'Incorrect password.'}), 400

    current_user.totp_enabled = False
    current_user.totp_secret = None
    current_user.totp_recovery_codes = None
    db.session.add(current_user)
    db.session.commit()
    return jsonify({'success': True})


@auth_bp.route('/2fa/verify-login', methods=['POST'])
@limiter.limit("5 per 15 minutes")
def totp_verify_login():
    """Second half of the 2FA-gated login (see login() above). The user is
    NOT authenticated yet — identity comes only from pending_token, so this
    mirrors login()'s own trust level, not @login_required's."""
    _ensure_totp_columns()
    data = request.get_json(silent=True) or {}
    pending_token = data.get('pending_token', '')
    code = data.get('code', '')
    remember_me = bool(data.get('remember_me', False))

    user = Users.verify_token(pending_token, '2fa_pending')
    if not user:
        return jsonify({'error': 'Your session expired. Please sign in again.'}), 401
    if not user.totp_enabled:
        return jsonify({'error': 'Two-factor authentication is not enabled for this account.'}), 400

    secret = totp_crypto.decrypt_secret(user.totp_secret)
    ok = bool(secret) and totp_service.verify_totp_code(secret, code)

    if not ok:
        # Fall back to a recovery code — consumes it on match so it can't be reused.
        new_codes = totp_service.consume_recovery_code(user.totp_recovery_codes, code)
        if new_codes is not None:
            user.totp_recovery_codes = new_codes
            ok = True

    if not ok:
        return jsonify({'error': 'Invalid code.'}), 401

    session_token = user.create_session()
    db.session.add(user)
    record_login(user, session_token)
    db.session.commit()

    session['session_token'] = session_token
    login_user(user, remember=remember_me)

    return jsonify({
        'message': 'Session started successfully',
        'redirect': sanitize_redirect_url(None),
    }), 200


# ── New Security endpoints ────────────────────────────────────────────────────

@auth_bp.route('/recent-sessions', methods=['GET'])
@login_required
def recent_sessions():
    rows = (LoginHistory.query
            .filter_by(user_id=current_user.id)
            .order_by(LoginHistory.created_at.desc())
            .limit(8).all())
    result = []
    for r in rows:
        result.append({
            'id': r.id,
            'event_type': r.event_type or 'login',
            'browser': r.browser or 'Unknown Browser',
            'os': r.os_name or 'Unknown OS',
            'ip': r.ip_address or '—',
            'city': r.city or '',
            'country': r.country or '',
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'is_current': r.event_type == 'login' and r.session_token == current_user.session_token,
        })
    return jsonify({'sessions': result})


@auth_bp.route('/login-history-chart', methods=['GET'])
@login_required
def login_history_chart():
    func = db.func
    start = datetime.utcnow() - timedelta(days=13)
    rows = (db.session.query(
                func.date(LoginHistory.created_at).label('d'),
                LoginHistory.event_type.label('ev'),
                func.count(LoginHistory.id).label('n'))
            .filter(LoginHistory.user_id == current_user.id,
                    LoginHistory.created_at >= start)
            .group_by(func.date(LoginHistory.created_at), LoginHistory.event_type)
            .all())
    logins = {}
    logouts = {}
    for r in rows:
        key = str(r.d)
        if r.ev == 'logout':
            logouts[key] = r.n
        else:
            logins[key] = r.n
    labels, login_vals, logout_vals = [], [], []
    for i in range(13, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        key = day.strftime('%Y-%m-%d')
        labels.append(day.strftime('%b %d'))
        login_vals.append(logins.get(key, 0))
        logout_vals.append(logouts.get(key, 0))
    return jsonify({'labels': labels, 'logins': login_vals, 'logouts': logout_vals})


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json() or {}
    current_pw = data.get('current_password', '')
    new_pw     = data.get('new_password', '')

    if not current_user._password_hash:
        return jsonify({'error': 'This account uses OAuth login — no password to change.'}), 400
    if not bcrypt.checkpw(current_pw.encode('utf-8'), current_user._password_hash.encode('utf-8')):
        return jsonify({'error': 'Current password is incorrect.'}), 400
    if len(new_pw) < 8:
        return jsonify({'error': 'New password must be at least 8 characters.'}), 400

    hashed = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    current_user._password_hash = hashed
    db.session.add(current_user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Password updated successfully.'})


@auth_bp.route('/signout-all-sessions', methods=['POST'])
@login_required
def signout_all_sessions():
    """Invalidate all login records except the current session token."""
    (LoginHistory.query
     .filter(LoginHistory.user_id == current_user.id,
             LoginHistory.session_token != current_user.session_token)
     .update({'session_token': None}, synchronize_session=False))
    db.session.commit()
    return jsonify({'success': True})


# ════════════════════════════════════════════════════════════════════════════
# Delete Account — borrado total e irreversible de la identidad del usuario.
# Superset de "Delete All Documents" (reutiliza purge_all_user_documents):
# además borra la fila `users` compartida con marktrack, todo lo que la
# referencia en ambas apps, y cierra la sesión actual. appcli2 borra su
# propio lado y la fila `users` (última, después de que marktrack confirme
# éxito); marktrack borra su propio lado vía llamada interna. Ver plan
# aprobado: bloquea si el usuario posee workspaces/sesiones de entrega con
# otros participantes — nunca destruye silenciosamente el acceso de terceros.
# ════════════════════════════════════════════════════════════════════════════

def _owned_sessions_with_participants(user_id):
    """appcli2 tiene su propio equivalente a los Workspace de marktrack:
    SubmissionSession, creadas por un profesor, con StudentSubmission/
    SessionParticipant de OTRAS personas. Mismo criterio de bloqueo que
    marktrack — no borrar en cascada el trabajo entregado por estudiantes."""
    from modules.models.model import SubmissionSession, StudentSubmission, SessionParticipant
    blocking = []
    sessions = SubmissionSession.query.filter_by(professor_id=user_id).all()
    for s in sessions:
        has_submissions = StudentSubmission.query.filter_by(session_id=s.id).first() is not None
        has_invited = SessionParticipant.query.filter_by(
            session_id=s.id, invitation_sent=True
        ).first() is not None
        if has_submissions or has_invited:
            blocking.append(s.name)
    return blocking


def _check_delete_account_eligibility(user_id):
    """Combina el bloqueo local (SubmissionSession) con el de marktrack
    (Workspace). Falla CERRADO: si marktrack no responde, no se puede
    verificar que es seguro borrar -> no se permite continuar."""
    from modules.doc_service.doc_routes import MARKTRACK_SERVICE_BASE, MARKTRACK_INTERNAL_KEY, session_pool

    reasons = []

    local_blocking = _owned_sessions_with_participants(user_id)
    if local_blocking:
        names = ', '.join(f'"{n}"' for n in local_blocking)
        reasons.append(f'You own {len(local_blocking)} submission session(s) with student '
                        f'work or invited participants ({names}). Close or transfer them first.')

    try:
        resp = session_pool.post(
            f'{MARKTRACK_SERVICE_BASE}/api/internal/account/can-delete',
            headers={'Content-Type': 'application/json', 'X-Internal-Key': MARKTRACK_INTERNAL_KEY},
            json={'user_id': user_id},
            timeout=(5, 15),
        )
        if not resp.ok:
            return False, 'Could not verify your workspaces right now. Please try again shortly.'
        data = resp.json()
        if not data.get('can_delete', False):
            reasons.append(data.get('reason') or 'You have collaborative workspace data that would be affected.')
    except requests.exceptions.RequestException:
        return False, 'Could not reach the workspace service to verify your account. Please try again shortly.'

    if reasons:
        return False, ' '.join(reasons)
    return True, None


@auth_bp.route('/delete-account/eligibility', methods=['GET'])
@login_required
def delete_account_eligibility():
    """Se llama al abrir el modal, antes de pedir la contraseña — para que un
    usuario bloqueado vea el motivo de inmediato. Incluye has_password para que
    el front sepa si pedir contraseña o el email de confirmación (cuentas OAuth)."""
    can_delete, reason = _check_delete_account_eligibility(current_user.id)
    return jsonify({
        'can_delete': can_delete,
        'reason': reason,
        'has_password': bool(current_user._password_hash),
    }), 200


@auth_bp.route('/delete-account', methods=['POST'])
@login_required
@limiter.limit("3 per 15 minutes")
def delete_account():
    """Borra la cuenta por completo, en appcli2 Y marktrack. Irreversible.
    Requiere la contraseña actual (o el email si la cuenta es solo-OAuth)
    como confirmación — más fuerte que el confirm de 2 botones que usan el
    resto de acciones destructivas de esta app, dado que aquí se destruye la
    identidad completa, no solo datos.
    """
    from modules.doc_service.doc_routes import (
        purge_all_user_documents, MARKTRACK_SERVICE_BASE, MARKTRACK_INTERNAL_KEY, session_pool
    )
    from modules.billing_service.billing_routes import cancel_subscription_immediately
    from modules.models.model import (
        Users, UserPreference, UserAnalysisUsage, UserModelPreference,
        UserAddonSubscription, SubmissionSession, StudentSubmission,
        ActivityLog, LoginHistory, ItemShare,
    )
    from modules.cleanup_service.routes_cleanup import CleanupTask, CleanupHistory

    user_id = current_user.id
    user = current_user

    # 1) Re-verificar elegibilidad (el estado pudo cambiar desde el preflight).
    can_delete, reason = _check_delete_account_eligibility(user_id)
    if not can_delete:
        return jsonify({'error': reason}), 409

    # 2) Re-verificar contraseña/email — nunca confiar en la validación del cliente.
    data = request.get_json(silent=True) or {}
    if user._password_hash:
        password = data.get('password') or ''
        if not password or not bcrypt.checkpw(password.encode('utf-8'), user._password_hash.encode('utf-8')):
            return jsonify({'error': 'Incorrect password.'}), 401
    else:
        confirm_email = (data.get('confirm_email') or '').strip().lower()
        if confirm_email != (user.email or '').strip().lower():
            return jsonify({'error': 'Email confirmation does not match your account.'}), 401

    # 3) Cancelar suscripción de inmediato — best-effort, nunca bloquea el borrado.
    billing_ok, billing_msg = cancel_subscription_immediately(user)

    # 4) marktrack borra su lado PRIMERO. Si falla aquí, abortar todo — no dejar
    #    la cuenta a medio borrar (documentos fuera pero login vivo, o viceversa).
    try:
        mt_resp = session_pool.post(
            f'{MARKTRACK_SERVICE_BASE}/api/internal/account/delete-all',
            headers={'Content-Type': 'application/json', 'X-Internal-Key': MARKTRACK_INTERNAL_KEY},
            json={'user_id': user_id},
            timeout=(5, 60),
        )
        if not mt_resp.ok:
            current_app.logger.error('delete_account: marktrack delete-all failed user=%s status=%s body=%s',
                                      user_id, mt_resp.status_code, mt_resp.text[:300])
            return jsonify({'error': 'Could not delete your workspace data. Please try again.'}), 502
        mt_data = mt_resp.json()
    except requests.exceptions.RequestException as exc:
        current_app.logger.error('delete_account: marktrack unreachable user=%s: %s', user_id, exc)
        return jsonify({'error': 'Could not reach the workspace service. Please try again.'}), 502

    # 5) appcli2: documentos (reutiliza Delete All Documents) + resto de tablas
    #    + la fila `users` — todo en una transacción.
    try:
        appcli2_stats = purge_all_user_documents(user_id)

        UserPreference.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        UserAnalysisUsage.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        UserModelPreference.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        UserAddonSubscription.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        ActivityLog.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        LoginHistory.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        CleanupHistory.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        CleanupTask.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        # Shares de items ajenos otorgados A este usuario (no cubierto por
        # purge_all_user_documents, que solo limpia lo que el usuario POSEE).
        ItemShare.query.filter_by(shared_with_id=user_id).delete(synchronize_session=False)

        # SubmissionSession ya confirmadas sin participantes en el paso 1 —
        # cascada ORM (participants/submissions) requiere delete por objeto.
        for s in SubmissionSession.query.filter_by(professor_id=user_id).all():
            db.session.delete(s)

        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('delete_account: appcli2-side deletion failed for user=%s', user_id)
        return jsonify({'error': 'Could not complete account deletion. Please try again.'}), 500

    current_app.logger.info('delete_account: user=%s appcli2=%s marktrack=%s billing_ok=%s',
                             user_id, appcli2_stats, mt_data, billing_ok)

    # 6) Cerrar la sesión actual — la fila ya no existe, pero limpiar la cookie
    #    ahora evita depender de que la PRÓXIMA request falle para notarlo.
    logout_user()
    session.clear()

    return jsonify({
        'success': True,
        'deleted': {**appcli2_stats, 'marktrack_documents': mt_data.get('deleted_count', 0)},
        'billing': billing_msg,
    }), 200