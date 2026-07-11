# auth_routes.py
import os
import re
import logging
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify, session, url_for, redirect, render_template, current_app, g, flash, session, make_response
from flask_wtf.csrf import CSRFProtect, validate_csrf
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,BooleanField, validators
#from extensions_fixed import db, login_manager, mail
from modules.models.model import Users, StoragePlan, ModelVersion, UserModelPreference, ModelPlanAccess, LoginHistory
from settings.connections import mail, limiter
from flask_login import login_user, logout_user, login_required, current_user
from settings.utilities import generate_token, verify_token
from settings.email_service import EmailService, EmailTemplates
import bcrypt
import requests
from flask_mail import Message
from flask_dance.contrib.azure import azure  # ✅ CORREGIDO: azure en lugar de microsoft
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

@auth_bp.route("/google/login")
def google_login():
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
        #print(f" EXCEPCIÓN CRÍTICA en OAuth callback:")
        #print(traceback.format_exc())
        db.session.rollback()
        
        #  LIMPIAR SESIÓN EN CASO DE ERROR
        flask_session.clear()
        
        flash("An internal error occurred while authenticating with Google. Please try again.", "error")
        return redirect(url_for('x_apps.login'))
 
@auth_bp.route("/microsoft/login")
def microsoft_login():
    """Iniciar login con Microsoft"""
    next_url = request.args.get('next', url_for('x_users.analysis'))
    session['oauth_next'] = next_url
    auth_url = microsoft_oauth.get_authorization_url()
    current_app.logger.info("Iniciando login con Microsoft")
    return redirect(auth_url)

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
            
            # ✅ Obtener y guardar foto de Microsoft
            if user_data.get('access_token'):
                photo_content = microsoft_oauth.get_user_photo(user_data['access_token'])
                if photo_content:
                    photo_filename = f"ms_{user.id}.jpg"
                    photo_path = os.path.join(current_app.root_path, 'static', 'img', 'avatars', photo_filename)
                    with open(photo_path, 'wb') as f:
                        f.write(photo_content)
                    user.avatar = f"/static/img/avatars/{photo_filename}"
            
            #print(f" Usuario Microsoft creado con ID: {user.id}")
        else:
            #print(f" Usuario existente encontrado: {email}")
            # ✅ Actualizar foto de Microsoft si es necesario
            if user_data.get('access_token'):
                photo_content = microsoft_oauth.get_user_photo(user_data['access_token'])
                if photo_content:
                    photo_filename = f"ms_{user.id}.jpg"
                    photo_path = os.path.join(current_app.root_path, 'static', 'img', 'avatars', photo_filename)
                    with open(photo_path, 'wb') as f:
                        f.write(photo_content)
                    user.avatar = f"/static/img/avatars/{photo_filename}"

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
        print(f"💥 EXCEPCIÓN CRÍTICA en Microsoft OAuth callback:")
        print(traceback.format_exc())
        db.session.rollback()
        
        flask_session.clear()
        
        flash("Internal error in authentication with Microsoft. Please try again.", "error")
        return redirect(url_for('x_apps.login'))

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
                if request.endpoint and not request.endpoint.startswith('auth.'):
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
    
    if not user._password_hash:
        print("DEBUG LOGIN: User has no password hash (OAuth user?)")
        return jsonify({'error': 'This account was created with Google/Microsoft. Use the corresponding button.'}), 400
    
    if not bcrypt.checkpw(password.encode('utf-8'), user._password_hash.encode('utf-8')):
        print("DEBUG LOGIN: Password mismatch")
        return jsonify({'error': 'Incorrect credentials'}), 401

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
        return render_template('auth/signup.html')
    
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
    token = user.generate_token('confirm')
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    
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
    """Insert a login row into logins_xplagiax_clients after a successful login."""
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
    except Exception:
        current_app.logger.exception("Failed to record login history")


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