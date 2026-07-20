"""
Dashboard ejecutivo v1 — métricas por plan, créditos y actividad reciente.
Todo sale de tablas que appcli2 ya llena (users, analysis_limits,
user_analysis_usage): cero escrituras, solo agregaciones.
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from sqlalchemy import func

from utils.connections import db
from models.model import Users
from core.shared_models import AnalysisLimit, UserAnalysisUsage, PLANS
from core.security import get_csrf_token

adminx_dashboard_bp = Blueprint('adminx_dashboard', __name__)


@adminx_dashboard_bp.route('/', methods=['GET'])
@login_required
def page():
    return render_template('adminx/dashboard.html', csrf_token=get_csrf_token())


@adminx_dashboard_bp.route('/api/metrics', methods=['GET'])
@login_required
def metrics():
    now = datetime.utcnow()
    today = now.date()

    rows = (db.session.query(
                Users.user_type,
                func.count(Users.id),
                func.sum(func.if_(Users.isactive == True, 1, 0)),          # noqa: E712
                func.sum(func.if_(Users.is_on_trial == True, 1, 0)),       # noqa: E712
                func.sum(func.if_((Users.is_on_trial == True) &            # noqa: E712
                                  (Users.trial_ends_at != None) &          # noqa: E711
                                  (Users.trial_ends_at < now), 1, 0)))
            .group_by(Users.user_type).all())
    by_plan = {p: {'total': 0, 'active': 0, 'inactive': 0, 'trial': 0, 'expired_trial': 0}
               for p in PLANS}
    for plan, total, active, trial, expired in rows:
        key = plan if plan in by_plan else 'Starter'
        d = by_plan[key]
        d['total'] += int(total or 0)
        d['active'] += int(active or 0)
        d['trial'] += int(trial or 0)
        d['expired_trial'] += int(expired or 0)
        d['inactive'] = d['total'] - d['active']

    limits = {l.plan_name: l.daily_analysis_limit
              for l in AnalysisLimit.query.filter_by(is_active=True).all()}

    used_today = int(db.session.query(func.coalesce(func.sum(UserAnalysisUsage.analysis_count), 0))
                     .filter(UserAnalysisUsage.usage_date == today).scalar() or 0)
    used_30d = int(db.session.query(func.coalesce(func.sum(UserAnalysisUsage.analysis_count), 0))
                   .filter(UserAnalysisUsage.usage_date >= today - timedelta(days=30)).scalar() or 0)
    # Capacidad diaria total = Σ usuarios_activos_por_plan × límite_del_plan.
    capacity = sum(by_plan[p]['active'] * int(limits.get(p, 10) or 0) for p in PLANS)

    week_ago = now - timedelta(days=7)
    new_7d = Users.query.filter(Users.created_date >= week_ago).count()

    recent = [{'name': f'{(u.name or "").strip()} {(u.lastname or "").strip()}'.strip() or '—',
               'email': u.email, 'plan': u.user_type or 'Starter',
               'created': u.created_date.strftime('%Y-%m-%d %H:%M') if u.created_date else None}
              for u in Users.query.order_by(Users.created_date.desc()).limit(8).all()]
    last_logins = [{'email': u.email, 'plan': u.user_type or 'Starter',
                    'last_login': u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else None}
                   for u in (Users.query.filter(Users.last_login != None)          # noqa: E711
                             .order_by(Users.last_login.desc()).limit(8).all())]

    return jsonify({
        'plans': by_plan, 'plan_limits': limits,
        'analyses': {'used_today': used_today, 'used_30d': used_30d,
                     'daily_capacity': capacity,
                     'remaining_today': max(0, capacity - used_today)},
        'new_users_7d': new_7d,
        'recent_users': recent, 'last_logins': last_logins,
        'generated_at': now.strftime('%Y-%m-%d %H:%M UTC'),
    })
