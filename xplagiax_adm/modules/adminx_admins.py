"""
Gestión de cuentas de administrador (Users_admin): alta, cambio de rol,
activar/desactivar. Todas las mutaciones exigen superadmin. Nunca se envían
contraseñas por email — al crear una cuenta se fija un hash aleatorio
inutilizable y se manda un link de "set your password" de un solo uso (ver
core/tokens.py:resolve_password_reset_token). El mismo mecanismo cubre el
"olvidé mi contraseña" en auth_endpoints.py.

Guardas de seguridad:
- Un superadmin no puede desactivarse a sí mismo (evita bloqueo accidental).
- No se puede desactivar ni degradar de rol al ÚLTIMO superadmin activo.
"""
import re
import secrets

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

from utils.connections import db
from models.model import Users_admin
from core.security import require_role, get_csrf_token, ROLE_LEVELS
from core.audit import log_action
from core import mailer

adminx_admins_bp = Blueprint('adminx_admins', __name__)

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _admin_dict(a):
    return {
        'id': a.id, 'username': a.username, 'email': a.email, 'role': a.role,
        'is_active': bool(a.is_active),
        'created_at': a.created_at.strftime('%Y-%m-%d %H:%M') if a.created_at else None,
        'last_login_at': a.last_login_at.strftime('%Y-%m-%d %H:%M') if a.last_login_at else None,
        'is_self': bool(current_user.is_authenticated and a.id == current_user.id),
    }


def _active_superadmin_count(exclude_id=None):
    q = Users_admin.query.filter_by(role='superadmin', is_active=True)
    if exclude_id is not None:
        q = q.filter(Users_admin.id != exclude_id)
    return q.count()


@adminx_admins_bp.route('/', methods=['GET'])
@login_required
def page():
    return render_template('adminx/admins.html', csrf_token=get_csrf_token(),
                           is_superadmin=(current_user.role == 'superadmin'))


@adminx_admins_bp.route('/api/admins', methods=['GET'])
@login_required
def list_admins():
    rows = Users_admin.query.order_by(Users_admin.created_at.desc()).all()
    return jsonify({'admins': [_admin_dict(a) for a in rows]})


@adminx_admins_bp.route('/api/admins', methods=['POST'])
@require_role('superadmin')
def create_admin():
    data = request.get_json(silent=True) or {}
    username = str(data.get('username') or '').strip()
    email = str(data.get('email') or '').strip().lower()
    role = str(data.get('role') or 'admin').strip().lower()

    if not username:
        return jsonify({'error': 'Username is required.'}), 400
    if not _EMAIL_RE.match(email):
        return jsonify({'error': 'Valid email is required.'}), 400
    if role not in ROLE_LEVELS:
        return jsonify({'error': f'Unknown role. Valid: {", ".join(ROLE_LEVELS)}'}), 400
    if Users_admin.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken.'}), 409
    if Users_admin.query.filter_by(email=email).first():
        return jsonify({'error': 'An admin with this email already exists.'}), 409

    # Hash aleatorio inutilizable: nadie conoce esta contraseña, ni siquiera
    # temporalmente — la cuenta solo se puede activar vía el link de abajo.
    placeholder_hash = generate_password_hash(secrets.token_urlsafe(32))
    admin = Users_admin(username=username, email=email, role=role, is_active=True,
                        password_hash=placeholder_hash)
    db.session.add(admin)
    db.session.commit()

    sent = mailer.send_password_set_email(admin, subject='Set your XplagiaX Admin password')
    log_action('admin.create', 'users_admin', admin.id,
               {'email': email, 'role': role, 'invite_email_sent': sent})
    return jsonify({'ok': True, 'admin': _admin_dict(admin), 'invite_email_sent': sent}), 201


@adminx_admins_bp.route('/api/admins/<int:aid>', methods=['PATCH'])
@require_role('superadmin')
def update_admin(aid):
    admin = Users_admin.query.get_or_404(aid)
    data = request.get_json(silent=True) or {}
    before = {'role': admin.role, 'is_active': bool(admin.is_active), 'username': admin.username}

    if 'role' in data:
        new_role = str(data['role'] or '').strip().lower()
        if new_role not in ROLE_LEVELS:
            return jsonify({'error': f'Unknown role. Valid: {", ".join(ROLE_LEVELS)}'}), 400
        if (admin.role == 'superadmin' and new_role != 'superadmin' and admin.is_active
                and _active_superadmin_count(exclude_id=admin.id) < 1):
            return jsonify({'error': 'Cannot demote the last active superadmin.'}), 400
        admin.role = new_role

    if 'is_active' in data:
        new_active = bool(data['is_active'])
        if not new_active:
            if admin.id == current_user.id:
                return jsonify({'error': 'You cannot deactivate your own account.'}), 400
            if admin.role == 'superadmin' and _active_superadmin_count(exclude_id=admin.id) < 1:
                return jsonify({'error': 'Cannot deactivate the last active superadmin.'}), 400
        admin.is_active = new_active

    if 'username' in data:
        new_username = str(data['username'] or '').strip()
        if not new_username:
            return jsonify({'error': 'Username cannot be empty.'}), 400
        if Users_admin.query.filter(Users_admin.username == new_username,
                                    Users_admin.id != aid).first():
            return jsonify({'error': 'Username already taken.'}), 409
        admin.username = new_username

    db.session.commit()
    log_action('admin.update', 'users_admin', aid, {'before': before, 'after': data})
    return jsonify({'ok': True, 'admin': _admin_dict(admin)})


@adminx_admins_bp.route('/api/admins/<int:aid>/resend-invite', methods=['POST'])
@require_role('superadmin')
def resend_invite(aid):
    """Reenvía el link de set/reset password — también sirve para un admin
    que perdió el primer email de alta, o que quedó bloqueado sin acceso."""
    admin = Users_admin.query.get_or_404(aid)
    if not admin.is_active:
        return jsonify({'error': 'Cannot send a password link to a deactivated account.'}), 400
    sent = mailer.send_password_set_email(admin, subject='Reset your XplagiaX Admin password')
    log_action('admin.resend_invite', 'users_admin', aid, {'email_sent': sent})
    return jsonify({'ok': True, 'email_sent': sent})
