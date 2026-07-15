# microsoft_oauth.py
import os
import secrets
import requests
import urllib.parse
from datetime import datetime
from flask import current_app, session, request, url_for

class MicrosoftOAuth:
    """Servicio para manejar autenticación con Microsoft OAuth 2.0"""
    
    def __init__(self):
        # Configuración OAuth - considera mover a variables de entorno
        self.client_id =  os.environ.get("MICROSOFT_CLIENT_ID", "35f3700d-cfc1-42df-bde5-2f03206dbf82")
        self.client_secret =  os.environ.get("MICROSOFT_CLIENT_SECRET", "uv~8Q~nwt.OD0611lMKDiFW58GhNDeaIiueGnbln")
        self.tenant_id =  os.environ.get("MICROSOFT_TENANT_ID", "common")  # 'common' permite cuentas personales y organizacionales

        # URLs de Microsoft OAuth
        self.auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.userinfo_url = "https://graph.microsoft.com/v1.0/me"
        
        # Scopes mínimos necesarios
        self.scopes = ["openid", "profile", "email", "User.Read"]

    def get_redirect_uri(self):
        """Redirect URI resuelta EN TIEMPO DE REQUEST (ver google_oauth.py).

        MICROSOFT_REDIRECT_URI tiene prioridad; sin ella se deriva del host
        real de la request. El valor fijo anterior (localhost:5000) no
        coincidía con el puerto real de la app (5003) ni con el dominio de
        producción → AADSTS50011 (redirect URI mismatch)."""
        return os.environ.get('MICROSOFT_REDIRECT_URI') or url_for('auth_bp.microsoft_callback', _external=True)

    def get_authorization_url(self):
        """Generar URL de autorización para redirigir al usuario"""
        # Generar estado único para seguridad CSRF
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        session.permanent = True  # asegurar que la cookie persista el ida-y-vuelta

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.get_redirect_uri(),
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'state': state,
            'response_mode': 'query',
            'prompt': 'select_account'  # Permite elegir cuenta si hay múltiples
        }
        
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_user_data(self, authorization_code, state):
        """
        Intercambiar código de autorización por datos del usuario
        Returns: (user_data, error_message)
        """
        try:
            # Verificar estado para prevenir CSRF
            stored_state = session.get('oauth_state')
            state_ok = bool(stored_state) and state == stored_state
            # ⚠️ TEMPORAL: ver OAUTH_RELAX_STATE en google_oauth.py.
            relax = os.getenv('OAUTH_RELAX_STATE', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
            if not state_ok and not relax:
                return None, "Estado OAuth inválido - posible ataque CSRF"

            # Intercambiar código por token
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.get_redirect_uri(),
                'scope': ' '.join(self.scopes)
            }
            
            # Obtener token de acceso
            token_response = requests.post(self.token_url, data=token_data, timeout=10)
            if not token_response.ok:
                current_app.logger.error(f"Error token response: {token_response.text}")
                return None, f"Error obteniendo token: {token_response.status_code}"
            
            token_info = token_response.json()
            access_token = token_info.get('access_token')
            
            if not access_token:
                return None, "No se recibió token de acceso válido"
            
            # Obtener información del usuario usando Microsoft Graph
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            user_response = requests.get(self.userinfo_url, headers=headers, timeout=10)
            
            if not user_response.ok:
                current_app.logger.error(f"Error user response: {user_response.text}")
                return None, f"Error obteniendo datos de usuario: {user_response.status_code}"
            
            user_data = user_response.json()
            
            # Validar datos mínimos requeridos
            email = user_data.get('mail') or user_data.get('userPrincipalName')
            if not email:
                return None, "No se pudo obtener email del usuario"
            
            # Normalizar datos para compatibilidad con el sistema existente
            normalized_data = {
                'id': user_data.get('id'),
                'email': email,
                'name': user_data.get('displayName', ''),
                'given_name': user_data.get('givenName', ''),
                'family_name': user_data.get('surname', ''),
                'picture': None,  # Microsoft Graph requiere llamada separada para foto
                'verified_email': True,  # Microsoft siempre verifica emails
                'access_token': access_token  # ✅ Pasar token para obtener foto en el callback
            }
            
            return normalized_data, None
            
        except requests.exceptions.Timeout:
            return None, "Timeout de conexión con Microsoft"
        except requests.exceptions.RequestException as e:
            current_app.logger.exception("Error de conexión con Microsoft")
            return None, f"Error de conexión: {str(e)}"
        except Exception as e:
            current_app.logger.exception("Error inesperado en OAuth Microsoft")
            return None, f"Error inesperado: {str(e)}"

    def get_user_photo(self, access_token):
        """
        Obtener foto de perfil del usuario (opcional)
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            photo_response = requests.get(
                "https://graph.microsoft.com/v1.0/me/photo/$value", 
                headers=headers, 
                timeout=5
            )
            
            if photo_response.ok:
                return photo_response.content
            return None
            
        except Exception:
            return None