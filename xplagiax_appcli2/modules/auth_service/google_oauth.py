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
        # Configuración OAuth - considera mover a variables de entorno
        self.client_id = os.getenv('GOOGLE_CLIENT_ID', "121671119534-92uo2m1vpju3m3msh74jcf389nqhif4r.apps.googleusercontent.com")
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET', "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")
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', "http://127.0.0.1:5000/auth_bp/google/callbackx")
        
        # URLs de Google OAuth
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        # Scopes mínimos necesarios
        self.scopes = ["email", "profile"]

    def get_authorization_url(self):
        """Generar URL de autorización para redirigir al usuario"""
        # Generar estado único para seguridad CSRF
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        session.permanent = True  # asegurar que la cookie persista el ida-y-vuelta
        current_app.logger.info("[google-oauth] authorize: state set, redirect_uri=%s", self.redirect_uri)

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'state': state,
            'access_type': 'offline'
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
            current_app.logger.info(
                "[google-oauth] state check: stored=%s received=%s session_keys=%s",
                bool(stored_state), bool(state), list(session.keys()))
            if not stored_state:
                return None, "Sesión expirada (no se guardó el estado OAuth). Reintenta el login."
            if state != stored_state:
                return None, "Estado OAuth inválido - posible ataque CSRF"

            # Intercambiar código por token
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }

            # Obtener token de acceso
            token_response = requests.post(self.token_url, data=token_data, timeout=10)
            if not token_response.ok:
                current_app.logger.error(
                    "[google-oauth] token exchange failed %s: %s (redirect_uri=%s)",
                    token_response.status_code, token_response.text[:300], self.redirect_uri)
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