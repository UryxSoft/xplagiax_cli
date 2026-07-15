import jwt
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Clave de firma JWT: SIEMPRE prioriza la variable de entorno SECRET_KEY.
# El literal solo queda como fallback de compatibilidad para entornos sin la
# env var (tokens ya emitidos siguen siendo verificables); debe rotarse al
# definir SECRET_KEY en producción. Antes la clave estaba hardcodeada en las
# dos funciones e ignoraba por completo la configuración.
JWT_SECRET = os.environ.get('SECRET_KEY', '21XSWcxz3zaq45EDCxsw')


def generate_token(usuario_id):
    payload = {
        'usuario_id': usuario_id,
        'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp())
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError:
        logger.warning('JWT token inválido o expirado')
        return None
