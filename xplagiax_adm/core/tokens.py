"""
Tokens de activación de cuentas — firmados, con expiración y de un solo uso.

Mismo esquema de seguridad que appcli2 (itsdangerous + salt por propósito).
La firma usa ACTIVATION_SIGNING_KEY, que DEBE valer lo mismo en el admin y
en appcli2 (la pantalla de activación vive en appcli2 y verifica allí).
Un solo uso: el payload incluye users.token (nonce por usuario) — resetear
la cuenta rota el nonce e invalida todos los links anteriores.
"""
import hashlib
import hmac
import uuid

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

_SALT = 'xpx-account-activation'
_PWRESET_SALT = 'xpx-admin-pwreset'


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


# ── Password set/reset para Users_admin — single-use SIN columna nueva ──────
#
# El token firma [admin_id, fingerprint(password_hash_actual)]. En vez de
# marcar el token como "usado" en una tabla, se embebe una huella del hash de
# password vigente al momento de emitirlo: apenas la contraseña cambia (por
# este mismo link, o por cualquier otro medio), la huella firmada deja de
# coincidir con la huella actual y el token queda invalidado automáticamente.
# Mismo mecanismo sirve para "olvidé mi contraseña" y para "fija tu
# contraseña inicial" (alta de admin con hash placeholder inutilizable —
# nunca se envían contraseñas por email).

def _fingerprint(password_hash):
    return hashlib.sha256((password_hash or '').encode('utf-8')).hexdigest()[:16]


def make_password_reset_token(admin_id, password_hash):
    ser = URLSafeTimedSerializer(_key(), salt=_PWRESET_SALT)
    return ser.dumps([int(admin_id), _fingerprint(password_hash)])


def resolve_password_reset_token(token, max_age_hours=24):
    """Verifica firma+expiración+vigencia y devuelve (admin, None), o
    (None, razon) con razon en {'expired','invalid','used'}. 'used' cubre
    tanto un link ya canjeado como uno que quedó obsoleto porque la cuenta
    cambió de contraseña por otra vía mientras tanto."""
    ser = URLSafeTimedSerializer(_key(), salt=_PWRESET_SALT)
    try:
        admin_id, fp = ser.loads(token, max_age=max_age_hours * 3600)
    except SignatureExpired:
        return (None, 'expired')
    except (BadSignature, ValueError, TypeError):
        return (None, 'invalid')
    from models.model import Users_admin  # import diferido: evita ciclo con model.py
    admin = Users_admin.query.get(int(admin_id))
    if not admin or not admin.is_active:
        return (None, 'invalid')
    if not hmac.compare_digest(str(fp), _fingerprint(admin.password_hash)):
        return (None, 'used')
    return (admin, None)
