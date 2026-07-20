"""
Seguridad núcleo del admin: CSRF liviano, rate limiting en memoria y RBAC.

Sin dependencias nuevas (no flask-wtf / flask-limiter): CSRF double-submit
con token de sesión comparado en tiempo constante, y limiter por IP con
ventana deslizante en memoria (suficiente para un panel de pocos admins;
si algún día corre multi-worker, cambiar a Redis).

RBAC v1 sobre Users_admin.role: 'superadmin' > 'admin' > 'readonly'.
Los roles legados se mapean ('admin'→admin, cualquier otro→readonly).
"""
import hmac
import secrets
import time
import logging
from collections import defaultdict, deque
from functools import wraps

from flask import request, session, jsonify
from flask_login import current_user

logger = logging.getLogger(__name__)

ROLE_LEVELS = {'readonly': 0, 'admin': 1, 'superadmin': 2}


def role_level(user):
    role = str(getattr(user, 'role', '') or '').lower()
    if role not in ROLE_LEVELS:
        role = 'admin' if role == 'admin' else 'readonly'
    return ROLE_LEVELS.get(role, 0)


def require_role(minimum='admin'):
    """Gate por rol mínimo. readonly puede GET; escrituras exigen admin+."""
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            if role_level(current_user) < ROLE_LEVELS[minimum]:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return wrapper
    return deco


# ── CSRF (double-submit: sesión ↔ header X-CSRF-Token o campo csrf_token) ────

def get_csrf_token():
    tok = session.get('_admx_csrf')
    if not tok:
        tok = secrets.token_urlsafe(32)
        session['_admx_csrf'] = tok
    return tok


def validate_csrf():
    sent = (request.headers.get('X-CSRF-Token')
            or (request.form.get('csrf_token') if request.form else None)
            or ((request.get_json(silent=True) or {}).get('csrf_token')
                if request.is_json else None) or '')
    good = session.get('_admx_csrf') or ''
    return bool(good) and hmac.compare_digest(str(sent), str(good))


def csrf_protect_blueprint(bp):
    """before_request del blueprint: exige CSRF en métodos mutantes."""
    @bp.before_request
    def _csrf_guard():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and not validate_csrf():
            return jsonify({'error': 'CSRF token missing or invalid.'}), 403


def login_required_blueprint(bp):
    """Cierra un blueprint entero tras login (fix de los endpoints que estaban
    completamente abiertos: instituciones/países/ciudades/provincias)."""
    @bp.before_request
    def _auth_guard():
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401


# ── Rate limiting en memoria (ventana deslizante por clave) ──────────────────

_hits = defaultdict(deque)


def rate_limit(max_hits, window_seconds, key_prefix):
    """5/15min para login, etc. Por IP. In-memory: reinicia con el proceso."""
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = f'{key_prefix}:{request.headers.get("X-Real-IP", request.remote_addr)}'
            now = time.monotonic()
            dq = _hits[key]
            while dq and now - dq[0] > window_seconds:
                dq.popleft()
            if len(dq) >= max_hits:
                logger.warning('Rate limit hit: %s', key)
                return jsonify({'error': 'Too many attempts. Try again later.'}), 429
            dq.append(now)
            return f(*args, **kwargs)
        return wrapper
    return deco


def apply_security_headers(app):
    @app.after_request
    def _headers(resp):
        resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
        resp.headers.setdefault('X-Frame-Options', 'DENY')
        resp.headers.setdefault('Referrer-Policy', 'same-origin')
        resp.headers.setdefault('X-Robots-Tag', 'noindex, nofollow')
        return resp
