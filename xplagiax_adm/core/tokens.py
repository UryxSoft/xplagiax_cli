"""
Tokens de activación de cuentas — firmados, con expiración y de un solo uso.

Mismo esquema de seguridad que appcli2 (itsdangerous + salt por propósito).
La firma usa ACTIVATION_SIGNING_KEY, que DEBE valer lo mismo en el admin y
en appcli2 (la pantalla de activación vive en appcli2 y verifica allí).
Un solo uso: el payload incluye users.token (nonce por usuario) — resetear
la cuenta rota el nonce e invalida todos los links anteriores.
"""
import uuid

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

_SALT = 'xpx-account-activation'


def _key():
    return (current_app.config.get('ACTIVATION_SIGNING_KEY')
            or current_app.config['SECRET_KEY'])


def new_nonce():
    return uuid.uuid4().hex[:32]


def make_activation_token(email, nonce):
    ser = URLSafeTimedSerializer(_key(), salt=_SALT)
    return ser.dumps([str(email).lower(), str(nonce)])


def verify_activation_token(token, max_age_hours=72):
    """Devuelve (email, nonce) o (None, razon)."""
    ser = URLSafeTimedSerializer(_key(), salt=_SALT)
    try:
        email, nonce = ser.loads(token, max_age=max_age_hours * 3600)
        return (str(email).lower(), str(nonce))
    except SignatureExpired:
        return (None, 'expired')
    except (BadSignature, ValueError, TypeError):
        return (None, 'invalid')
