"""
Visor de auditoría: lista/filtra/pagina AdminAuditLog. core.audit.log_action
ya escribe una fila en cada mutación del panel (users, institutions, admins,
login) — esta es la superficie de LECTURA que faltaba por completo.
Solo lectura: cualquier rol autenticado puede consultarla.
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from core.audit import AdminAuditLog, ensure_table
from core.security import get_csrf_token

adminx_audit_bp = Blueprint('adminx_audit', __name__)


@adminx_audit_bp.before_request
def _ensure_schema():
    ensure_table()


def _row_dict(r):
    return {
        'id': r.id, 'admin_id': r.admin_id, 'admin_email': r.admin_email,
        'action': r.action, 'entity': r.entity, 'entity_id': r.entity_id,
        'detail': r.detail, 'ip': r.ip, 'user_agent': r.user_agent,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else None,
    }


@adminx_audit_bp.route('/', methods=['GET'])
@login_required
def page():
    return render_template('adminx/audit.html', csrf_token=get_csrf_token())


@adminx_audit_bp.route('/api/logs', methods=['GET'])
@login_required
def list_logs():
    q = AdminAuditLog.query

    action = request.args.get('action', '').strip()
    if action:
        q = q.filter(AdminAuditLog.action.like(f'%{action}%'))
    entity = request.args.get('entity', '').strip()
    if entity:
        q = q.filter(AdminAuditLog.entity == entity)
    admin_email = request.args.get('admin_email', '').strip()
    if admin_email:
        q = q.filter(AdminAuditLog.admin_email.like(f'%{admin_email}%'))

    date_from = request.args.get('date_from', '').strip()
    if date_from:
        try:
            q = q.filter(AdminAuditLog.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
        except ValueError:
            pass
    date_to = request.args.get('date_to', '').strip()
    if date_to:
        try:
            q = q.filter(AdminAuditLog.created_at < datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            pass

    page_n = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(10, int(request.args.get('per_page', 30))))
    total = q.count()
    rows = (q.order_by(AdminAuditLog.created_at.desc())
            .offset((page_n - 1) * per_page).limit(per_page).all())
    return jsonify({'logs': [_row_dict(r) for r in rows], 'total': total,
                    'page': page_n, 'per_page': per_page})


@adminx_audit_bp.route('/api/actions', methods=['GET'])
@login_required
def distinct_actions():
    """Puebla el <select> de filtro sin hardcodear la lista de acciones —
    nuevas acciones (nuevos módulos) aparecen solas."""
    rows = (AdminAuditLog.query.with_entities(AdminAuditLog.action)
            .distinct().order_by(AdminAuditLog.action).all())
    return jsonify({'actions': [r[0] for r in rows]})
