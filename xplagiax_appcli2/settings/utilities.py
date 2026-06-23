import jwt
import logging
from datetime import datetime, timedelta
from settings.config import DevelopmentConfig

logger = logging.getLogger(__name__)

SECRET_KEY = DevelopmentConfig.SECRET_KEY

def generate_token(usuario_id):
    payload = {
        'usuario_id': usuario_id,
        'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp())
    }
    token = jwt.encode(payload, '21XSWcxz3zaq45EDCxsw', algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, '21XSWcxz3zaq45EDCxsw', algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError:
        logger.warning('JWT token inválido o expirado')
        return None