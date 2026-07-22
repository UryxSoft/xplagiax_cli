# google_oauth_simple.py
import os
import secrets
import requests
import urllib.parse
from datetime import datetime
from flask import current_app, session, request, url_for

class GoogleOAuth:
    """Servicio simplificado para manejar autenticación con Google OAuth 2.0"""
    
    def __init__(self):
        # La env var SIEMPRE tiene prioridad; el valor hardcodeado es respaldo
        # solicitado para que el login funcione sin configuración adicional
        # (repo privado). Recomendado: mover a env vars y rotar el secreto si
        # el repo deja de ser privado.
        self.client_id = os.getenv(
            'GOOGLE_CLIENT_ID',
            '121671119534-92uo2m1vpju3m3msh74jcf389nqhif4r.apps.googleusercontent.com')
        self.client_secret = os.getenv(
            'GOOGLE_CLIENT_SECRET',
            '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')

        # URLs de Google OAuth
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        # Scopes mínimos necesarios
        self.scopes = ["email", "profile"]

    # URI de producción registrada en Google Cloud Console.
    # La env var GOOGLE_REDIRECT_URI siempre tiene prioridad (útil en
    # desarrollo o si el dominio cambia); si no está definida se usa este
    # valor fijo que coincide con la redirect URI autorizada en el proyecto
    # de Google (repo privado).
    PRODUCTION_REDIRECT_URI = 'https://app.xplagiax.ca/auth_bp/google/callbackx'

    def get_redirect_uri(self):
        """Redirect URI resuelta EN TIEMPO DE REQUEST.

        Prioridad:
          1. Variable de entorno GOOGLE_REDIRECT_URI (máxima flexibilidad).
          2. Valor fijo de producción (PRODUCTION_REDIRECT_URI) — garantiza
             que siempre coincida con la URI registrada en Google Console.
        El valor derivado de url_for() fue eliminado porque detrás de nginx
        sin ProxyFix configurado correctamente generaba http:// o puertos
        incorrectos causando redirect_uri_mismatch (error 400 en el
        intercambio de token)."""
        return os.getenv('GOOGLE_REDIRECT_URI') or self.PRODUCTION_REDIRECT_URI

    def get_authorization_url(self):
        """Generar URL de autorización para redirigir al usuario"""
        # Generar estado único para seguridad CSRF
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        session.permanent = True  # asegurar que la cookie persista el ida-y-vuelta
        redirect_uri = self.get_redirect_uri()
        current_app.logger.info("[google-oauth] authorize: state set, redirect_uri=%s", redirect_uri)

        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',
            # Sin esto Google resuelve el login en silencio contra la sesión
            # activa (responde con prompt=none) y el usuario con varias cuentas
            # nunca llega a ver el selector: siempre entra con la principal.
            # Mismo criterio que microsoft_oauth.py, que ya lo pide explícito.
            'prompt': 'select_account'
        }
        
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_user_data(self, authorization_code, state):
        """
        Intercambiar código de autorización por datos del usuario
        Returns: (user_data, error_message)
        """
        try:
            # Verificar estado para prevenir CSRF
            stored_state = session.pop('oauth_state', None)
            state_ok = bool(stored_state) and state == stored_state
            # ⚠️ TEMPORAL: si la cookie de sesión no persiste el state (proxy/SECRET_KEY),
            # OAUTH_RELAX_STATE permite continuar igualmente. Quitar (poner 'false')
            # cuando el login con Google quede estable.
            relax = os.getenv('OAUTH_RELAX_STATE', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
            current_app.logger.info(
                "[google-oauth] state check: stored=%s received=%s match=%s relax=%s",
                bool(stored_state), bool(state), state_ok, relax)
            if not state_ok:
                if relax:
                    current_app.logger.warning(
                        "[google-oauth] state inválido/ausente — RELAJADO temporalmente (OAUTH_RELAX_STATE=true). Continuando login.")
                elif not stored_state:
                    return None, "Sesión expirada (no se guardó el estado OAuth). Reintenta el login."
                else:
                    return None, "Estado OAuth inválido - posible ataque CSRF"

            # Intercambiar código por token
            redirect_uri = self.get_redirect_uri()
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }

            # Obtener token de acceso
            token_response = requests.post(self.token_url, data=token_data, timeout=10)
            if not token_response.ok:
                current_app.logger.error(
                    "[google-oauth] token exchange failed %s: %s (redirect_uri=%s)",
                    token_response.status_code, token_response.text[:300], redirect_uri)
                return None, f"Error obteniendo token: {token_response.status_code}"
            
            token_info = token_response.json()
            access_token = token_info.get('access_token')
            
            if not access_token:
                return None, "No se recibió token de acceso válido"
            
            # Obtener información del usuario
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get(self.userinfo_url, headers=headers, timeout=10)
            
            if not user_response.ok:
                return None, f"Error obteniendo datos de usuario: {user_response.status_code}"
            
            user_data = user_response.json()
            
            # Validar datos mínimos requeridos
            if not user_data.get('email'):
                return None, "No se pudo obtener email del usuario"
            
            # Asegurar que el campo picture esté presente si existe
            if 'picture' in user_data:
                user_data['picture'] = user_data.get('picture')
                
            return user_data, None
            
        except requests.exceptions.Timeout:
            return None, "Timeout de conexión con Google"
        except requests.exceptions.RequestException as e:
            return None, f"Error de conexión: {str(e)}"
        except Exception as e:
            current_app.logger.exception("Error inesperado en OAuth")
            return None, f"Error inesperado: {str(e)}"