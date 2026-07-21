"""
Gestión de usuarios de la app cliente — tabs por plan, CRUD, trial, créditos
y flujo de activación por email. Toda mutación exige rol admin+ (CSRF a nivel
blueprint en app.py) y queda auditada.
"""
import re
import uuid
from datetime import datetime, timedelta, date

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import login_required
from sqlalchemy import or_

from utils.connections import db
from models.model import Users
from core.shared_models import AnalysisLimit, UserAnalysisUsage, PLANS
from core.security import require_role, get_csrf_token
from core.audit import log_action
from core import tokens as tk
from core import mailer

adminx_users_bp = Blueprint('adminx_users', __name__)

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _user_dict(u):
    today_usage = UserAnalysisUsage.query.filter_by(user_id=u.id, usage_date=date.today()).first()
    used = int(today_usage.analysis_count or 0) if today_usage else 0
    limit_row = AnalysisLimit.query.filter_by(plan_name=u.user_type or 'Starter',
                                              is_active=True).first()
    limit = int(limit_row.daily_analysis_limit) if limit_row else 10
    trial_expired = bool(u.is_on_trial and u.trial_ends_at and u.trial_ends_at < datetime.utcnow())
    return {
        'id': u.id, 'email': u.email,
        'name': f'{(u.name or "").strip()} {(u.lastname or "").strip()}'.strip() or '—',
        'first_name': u.name, 'last_name': u.lastname,
        'plan': u.user_type or 'Starter',
        'active': bool(u.isactive), 'confirmed': bool(u.confirmed),
        'on_trial': bool(u.is_on_trial), 'trial_expired': trial_expired,
        'trial_ends_at': u.trial_ends_at.strftime('%Y-%m-%d') if u.trial_ends_at else None,
        'subscription_status': u.subscription_status,
        'subscription_ends_at': u.subscription_ends_at.strftime('%Y-%m-%d') if u.subscription_ends_at else None,
        'created': u.created_date.strftime('%Y-%m-%d') if u.created_date else None,
        'last_login': u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else None,
        'credits_limit': limit, 'credits_used_today': used,
        'credits_remaining_today': max(0, limit - used),
        'institute': u.institute, 'country': u.country,
        # F3: institución real (FK) — 'institute' arriba es el texto libre
        # legado, se mantiene solo para referencia histórica.
        'institution_id': u.institution_id,
        'institution_name': u.institution.institution if u.institution_id and u.institution else None,
    }


@adminx_users_bp.route('/', methods=['GET'])
@login_required
def page():
    return render_template('adminx/users.html', csrf_token=get_csrf_token(), plans=PLANS)


@adminx_users_bp.route('/api/users', methods=['GET'])
@login_required
def list_users():
    q = Users.query
    plan = request.args.get('plan', '').strip()
    if plan and plan in PLANS:
        q = q.filter(Users.user_type == plan) if plan != 'Starter' else \
            q.filter(or_(Users.user_type == 'Starter', Users.user_type == None))  # noqa: E711
    search = request.args.get('search', '').strip()
    if search:
        like = f'%{search}%'
        q = q.filter(or_(Users.email.like(like), Users.name.like(like),
                         Users.lastname.like(like), Users.institute.like(like)))
    status = request.args.get('status', '').strip()
    if status == 'active':
        q = q.filter(Users.isactive == True)        # noqa: E712
    elif status == 'inactive':
        q = q.filter(Users.isactive == False)       # noqa: E712
    elif status == 'trial':
        q = q.filter(Users.is_on_trial == True)     # noqa: E712
    elif status == 'unconfirmed':
        q = q.filter(Users.confirmed == False)      # noqa: E712

    page_n = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(5, int(request.args.get('per_page', 20))))
    total = q.count()
    users = (q.order_by(Users.created_date.desc())
             .offset((page_n - 1) * per_page).limit(per_page).all())
    return jsonify({'users': [_user_dict(u) for u in users],
                    'total': total, 'page': page_n, 'per_page': per_page})


@adminx_users_bp.route('/api/users', methods=['POST'])
@require_role('admin')
def create_user():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email') or '').strip().lower()
    if not _EMAIL_RE.match(email):
        return jsonify({'error': 'Valid email is required.'}), 400
    if Users.query.filter_by(email=email).first():
        return jsonify({'error': 'A user with this email already exists.'}), 409
    plan = data.get('plan') or 'Starter'
    if plan not in PLANS:
        return jsonify({'error': f'Unknown plan. Valid: {", ".join(PLANS)}'}), 400

    u = Users(email=email, name=(data.get('first_name') or '').strip() or None,
              lastname=(data.get('last_name') or '').strip() or None,
              is_active=False, confirmado=False, user_type=plan,
              token=tk.new_nonce())
    if data.get('trial'):
        days = max(1, min(365, int(data.get('trial_days') or 14)))
        now = datetime.utcnow()
        u.is_on_trial = True
        u.trial_starts_at = now
        u.trial_ends_at = now + timedelta(days=days)
        u.subscription_status = 'trialing'
    db.session.add(u)
    db.session.commit()

    sent = _send_activation(u)
    log_action('user.create', 'users', u.id,
               {'email': email, 'plan': plan, 'trial': bool(data.get('trial')),
                'activation_email_sent': sent})
    return jsonify({'ok': True, 'user': _user_dict(u), 'activation_email_sent': sent}), 201


def _send_activation(u):
    token = tk.make_activation_token(u.email, u.token or '')
    url = f"{current_app.config['APPCLI_BASE_URL']}/auth_bp/activate/{token}"
    hours = current_app.config.get('ACTIVATION_MAX_AGE_HOURS', 72)
    trial_days = None
    if u.is_on_trial and u.trial_ends_at and u.trial_starts_at:
        trial_days = (u.trial_ends_at - u.trial_starts_at).days
    html = mailer.activation_email_html(u.name, url, u.user_type or 'Starter',
                                        trial_days=trial_days, expires_hours=hours)
    return mailer.send_email(u.email, 'Activate your XplagiaX account', html)


@adminx_users_bp.route('/api/users/<int:uid>', methods=['PATCH'])
@require_role('admin')
def update_user(uid):
    u = Users.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}
    before = {'plan': u.user_type, 'active': bool(u.isactive),
              'name': u.name, 'lastname': u.lastname}
    if 'plan' in data:
        if data['plan'] not in PLANS:
            return jsonify({'error': 'Unknown plan.'}), 400
        u.user_type = data['plan']
    if 'first_name' in data:
        u.name = (data['first_name'] or '').strip() or None
    if 'last_name' in data:
        u.lastname = (data['last_name'] or '').strip() or None
    if 'active' in data:
        u.isactive = bool(data['active'])
    if 'institution_id' in data:
        from models.model import Institution
        iid = data['institution_id']
        if iid in (None, '', 0, '0'):
            u.institution_id = None
        elif Institution.query.filter_by(id=int(iid)).filter(Institution.deleted_at.is_(None)).first():
            u.institution_id = int(iid)
        else:
            return jsonify({'error': 'Institution not found.'}), 400
    db.session.commit()
    log_action('user.update', 'users', uid, {'before': before, 'after': data})
    return jsonify({'ok': True, 'user': _user_dict(u)})


@adminx_users_bp.route('/api/users/<int:uid>/suspend', methods=['POST'])
@require_role('admin')
def suspend_user(uid):
    u = Users.query.get_or_404(uid)
    u.isactive = False
    u.active_session = False
    db.session.commit()
    log_action('user.suspend', 'users', uid, {'email': u.email})
    return jsonify({'ok': True, 'user': _user_dict(u)})


@adminx_users_bp.route('/api/users/<int:uid>/reactivate', methods=['POST'])
@require_role('admin')
def reactivate_user(uid):
    u = Users.query.get_or_404(uid)
    u.isactive = True
    db.session.commit()
    log_action('user.reactivate', 'users', uid, {'email': u.email})
    return jsonify({'ok': True, 'user': _user_dict(u)})


@adminx_users_bp.route('/api/users/<int:uid>/reset-activation', methods=['POST'])
@require_role('admin')
def reset_activation(uid):
    """Resetear cuenta: nonce nuevo (invalida TODOS los links previos) + email."""
    u = Users.query.get_or_404(uid)
    if u.confirmed:
        return jsonify({'error': 'Account is already activated.'}), 400
    u.token = tk.new_nonce()
    db.session.commit()
    sent = _send_activation(u)
    log_action('user.reset_activation', 'users', uid,
               {'email': u.email, 'email_sent': sent})
    return jsonify({'ok': True, 'activation_email_sent': sent})


@adminx_users_bp.route('/api/users/<int:uid>/trial', methods=['POST'])
@require_role('admin')
def manage_trial(uid):
    """op: start | extend | end | convert. days para start/extend."""
    u = Users.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}
    op = str(data.get('op') or '').lower()
    now = datetime.utcnow()
    before = {'on_trial': bool(u.is_on_trial),
              'ends': u.trial_ends_at.isoformat() if u.trial_ends_at else None}
    if op == 'start':
        days = max(1, min(365, int(data.get('days') or 14)))
        u.is_on_trial = True
        u.trial_starts_at = now
        u.trial_ends_at = now + timedelta(days=days)
        u.trial_notified = False
        u.subscription_status = 'trialing'
    elif op == 'extend':
        if not u.is_on_trial:
            return jsonify({'error': 'User is not on trial.'}), 400
        days = max(1, min(365, int(data.get('days') or 7)))
        base = u.trial_ends_at if (u.trial_ends_at and u.trial_ends_at > now) else now
        u.trial_ends_at = base + timedelta(days=days)
        u.trial_notified = False
    elif op == 'end':
        u.is_on_trial = False
        u.subscription_status = 'expired' if u.subscription_status == 'trialing' else u.subscription_status
    elif op == 'convert':
        # Trial → cuenta activa (activación manual del plan actual, sin pasarela).
        u.is_on_trial = False
        u.subscription_status = 'active'
        u.subscription_provider = u.subscription_provider or 'admin_manual'
        u.subscription_starts_at = now
        u.subscription_ends_at = now + timedelta(days=int(data.get('days') or 365))
    else:
        return jsonify({'error': 'op must be start|extend|end|convert'}), 400
    db.session.commit()
    log_action(f'user.trial_{op}', 'users', uid, {'before': before, 'data': data})
    return jsonify({'ok': True, 'user': _user_dict(u)})


@adminx_users_bp.route('/api/users/<int:uid>/credits', methods=['POST'])
@require_role('admin')
def adjust_credits(uid):
    """Créditos de HOY del usuario: op=grant devuelve N usos (resta el contador),
    op=consume descuenta N. El límite por plan se administra en /api/plan-limits."""
    u = Users.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}
    op = str(data.get('op') or '').lower()
    n = max(1, min(1000, int(data.get('amount') or 1)))
    today = date.today()
    usage = UserAnalysisUsage.query.filter_by(user_id=u.id, usage_date=today).first()
    if not usage:
        usage = UserAnalysisUsage(user_id=u.id, usage_date=today, analysis_count=0)
        db.session.add(usage)
    before = int(usage.analysis_count or 0)
    if op == 'grant':
        usage.analysis_count = max(0, before - n)
        if usage.analysis_count == 0:
            usage.limit_reached_at = None
    elif op == 'consume':
        usage.analysis_count = before + n
    else:
        return jsonify({'error': 'op must be grant|consume'}), 400
    usage.updated_at = datetime.utcnow()
    db.session.commit()
    log_action(f'user.credits_{op}', 'users', uid,
               {'amount': n, 'count_before': before, 'count_after': usage.analysis_count})
    return jsonify({'ok': True, 'user': _user_dict(u)})


@adminx_users_bp.route('/api/users/<int:uid>', methods=['DELETE'])
@require_role('admin')
def delete_user(uid):
    """Soft delete por defecto (suspende + marca). Hard delete: solo superadmin
    con ?hard=1 — puede fallar por FKs (folders/files); se reporta sin borrar."""
    from core.security import role_level
    from flask_login import current_user
    u = Users.query.get_or_404(uid)
    hard = request.args.get('hard') == '1'
    if hard:
        if role_level(current_user) < 2:
            return jsonify({'error': 'Hard delete requires superadmin.'}), 403
        email = u.email
        try:
            db.session.delete(u)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Hard delete blocked by related data '
                                     '(folders/files/history). Use soft delete.'}), 409
        log_action('user.delete_hard', 'users', uid, {'email': email})
        return jsonify({'ok': True, 'deleted': 'hard'})
    u.isactive = False
    u.active_session = False
    db.session.commit()
    log_action('user.delete_soft', 'users', uid, {'email': u.email})
    return jsonify({'ok': True, 'deleted': 'soft', 'user': _user_dict(u)})


@adminx_users_bp.route('/api/plan-limits', methods=['GET'])
@login_required
def plan_limits():
    rows = AnalysisLimit.query.all()
    return jsonify({'limits': [{'id': r.id, 'plan': r.plan_name,
                                'daily_limit': r.daily_analysis_limit,
                                'active': bool(r.is_active)} for r in rows]})


@adminx_users_bp.route('/api/plan-limits/<int:lid>', methods=['PATCH'])
@require_role('superadmin')
def update_plan_limit(lid):
    """Cambia el límite DIARIO de un plan — afecta a TODOS sus usuarios."""
    row = AnalysisLimit.query.get_or_404(lid)
    data = request.get_json(silent=True) or {}
    before = row.daily_analysis_limit
    if 'daily_limit' in data:
        row.daily_analysis_limit = max(0, int(data['daily_limit']))
    if 'active' in data:
        row.is_active = bool(data['active'])
    db.session.commit()
    log_action('plan.limit_update', 'analysis_limits', lid,
               {'plan': row.plan_name, 'before': before, 'after': row.daily_analysis_limit})
    return jsonify({'ok': True})
