"""
Alta masiva de usuarios institucionales: instituto elige/confirma, carga una
tabla de filas (manual o CSV) y el panel crea todas las cuentas válidas de
una sola vez con el plan Institutes, cada una con su propio token de
activación firmado (mismo mecanismo de core.tokens que el alta individual de
adminx_users.py) y su email de bienvenida con el logo/color de la
institución (core.mailer.activation_email_html(..., institution=...)).

Alcance deliberado (ver plan): CSV vía csv stdlib — sin dependencia nueva
para Excel (openpyxl/xlrd). Un admin que solo tenga .xlsx puede
"Guardar como CSV" primero; se indica en la UI, no es un límite silencioso.
"""
import csv
import io
import re
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, render_template, request, url_for
from flask_login import login_required

from utils.connections import db
from models.model import Users, Institution
from core.shared_models import PLANS
from core.security import require_role, get_csrf_token
from core.audit import log_action
from core import tokens as tk
from core import mailer

adminx_bulk_users_bp = Blueprint('adminx_bulk_users', __name__)

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
MAX_BATCH_ROWS = 500

# Alias de encabezado tolerantes (CSV exportado desde Excel/Sheets en
# cualquiera de los dos idiomas del equipo) — todo se compara en minúsculas
# y sin espacios.
_HEADER_ALIASES = {
    'email': 'email', 'e-mail': 'email', 'correo': 'email', 'mail': 'email',
    'first_name': 'first_name', 'firstname': 'first_name', 'nombre': 'first_name',
    'last_name': 'last_name', 'lastname': 'last_name', 'apellido': 'last_name',
}


@adminx_bulk_users_bp.route('/', methods=['GET'])
@login_required
def page():
    return render_template('adminx/bulk_users.html', csrf_token=get_csrf_token(), plans=PLANS)


@adminx_bulk_users_bp.route('/api/parse-csv', methods=['POST'])
@require_role('admin')
def parse_csv():
    """Solo lectura/preview — no toca la base. El admin confirma en el
    cliente antes de llamar a /api/bulk-create."""
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': 'No file provided.'}), 400
    raw = file.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        return jsonify({'error': 'CSV too large (max 2MB).'}), 413
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return jsonify({'error': 'File is not valid UTF-8 text. Export the CSV as UTF-8.'}), 400

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return jsonify({'error': 'Empty file.'}), 400
    cols = [_HEADER_ALIASES.get(h.strip().lower()) for h in header]
    if 'email' not in cols:
        return jsonify({'error': 'CSV must have an "email" column '
                                 '(first_name/last_name optional).'}), 400

    rows, errors = [], []
    for i, raw_row in enumerate(reader, start=2):
        if not any(c.strip() for c in raw_row):
            continue
        if len(rows) + len(errors) >= MAX_BATCH_ROWS:
            errors.append({'row': i, 'reason': f'Truncated at {MAX_BATCH_ROWS} rows.'})
            break
        row = {}
        for col, val in zip(cols, raw_row):
            if col:
                row[col] = (val or '').strip()
        email = (row.get('email') or '').lower()
        if not _EMAIL_RE.match(email):
            errors.append({'row': i, 'email': row.get('email') or '', 'reason': 'Invalid email format.'})
            continue
        rows.append({'email': email, 'first_name': row.get('first_name') or '',
                    'last_name': row.get('last_name') or ''})
    return jsonify({'rows': rows, 'parse_errors': errors, 'total_parsed': len(rows)})


def _resolve_institution(institution_id):
    inst = Institution.query.filter(Institution.id == institution_id,
                                    Institution.deleted_at.is_(None)).first()
    if not inst:
        return None, 'Institution not found.'
    if (inst.status or 'active') != 'active':
        return None, 'Institution is inactive.'
    return inst, None


@adminx_bulk_users_bp.route('/api/bulk-create', methods=['POST'])
@require_role('admin')
def bulk_create():
    data = request.get_json(silent=True) or {}
    inst, err = _resolve_institution(data.get('institution_id'))
    if err:
        return jsonify({'error': err}), 400

    plan = data.get('plan') or 'Institutes'
    if plan not in PLANS:
        return jsonify({'error': f'Unknown plan. Valid: {", ".join(PLANS)}'}), 400

    trial = bool(data.get('trial'))
    trial_days = max(1, min(365, int(data.get('trial_days') or 14))) if trial else None

    accent_choice = data.get('accent') or 'primary'
    accent = (inst.secondary_color if accent_choice == 'secondary' else inst.primary_color) or None

    rows = data.get('users')
    if not isinstance(rows, list) or not rows:
        return jsonify({'error': 'No users provided.'}), 400
    if len(rows) > MAX_BATCH_ROWS:
        return jsonify({'error': f'Batch too large (max {MAX_BATCH_ROWS} users per run).'}), 400

    # ── Validación (sin tocar la DB todavía) ────────────────────────────────
    seen_in_batch = set()
    candidates, failed = [], []
    for i, row in enumerate(rows):
        email = str((row or {}).get('email') or '').strip().lower()
        first_name = str((row or {}).get('first_name') or '').strip() or None
        last_name = str((row or {}).get('last_name') or '').strip() or None
        if not _EMAIL_RE.match(email):
            failed.append({'email': email or f'(row {i + 1})', 'reason': 'Invalid email format.'})
            continue
        if email in seen_in_batch:
            failed.append({'email': email, 'reason': 'Duplicate email within this batch.'})
            continue
        seen_in_batch.add(email)
        candidates.append({'email': email, 'first_name': first_name, 'last_name': last_name})

    if candidates:
        existing = {u.email.lower() for u in
                   Users.query.filter(Users.email.in_([c['email'] for c in candidates])).all()}
    else:
        existing = set()

    to_create = []
    for c in candidates:
        if c['email'] in existing:
            failed.append({'email': c['email'], 'reason': 'Email already registered.'})
        else:
            to_create.append(c)

    # ── Creación (una sola transacción para todas las filas válidas) ────────
    created_users = []
    now = datetime.utcnow()
    for c in to_create:
        u = Users(email=c['email'], name=c['first_name'], lastname=c['last_name'],
                  is_active=False, confirmado=False, user_type=plan,
                  token=tk.new_nonce())
        u.institution_id = inst.id
        if trial:
            u.is_on_trial = True
            u.trial_starts_at = now
            u.trial_ends_at = now + timedelta(days=trial_days)
            u.subscription_status = 'trialing'
        db.session.add(u)
        created_users.append((u, c))

    if not created_users:
        db.session.rollback()
        return jsonify({'ok': True, 'created': [], 'failed': failed,
                        'summary': {'total': len(rows), 'created': 0, 'failed': len(failed)}}), 200

    db.session.commit()

    # ── Emails de bienvenida (best-effort, ya con id/token asignados) ───────
    logo_url = None
    if inst.logo_path:
        try:
            logo_url = url_for('static', filename=inst.logo_path, _external=True)
        except Exception:
            logo_url = None
    inst_branding = {'name': inst.institution, 'logo_url': logo_url, 'primary_color': accent}
    hours = current_app.config.get('ACTIVATION_MAX_AGE_HOURS', 72)

    created = []
    for u, c in created_users:
        token = tk.make_activation_token(u.email, u.token or '')
        url = f"{current_app.config['APPCLI_BASE_URL']}/auth_bp/activate/{token}"
        html = mailer.activation_email_html(u.name, url, plan, trial_days=trial_days,
                                            expires_hours=hours, institution=inst_branding)
        sent = mailer.send_email(u.email, 'Activate your XplagiaX account', html)
        created.append({'id': u.id, 'email': u.email, 'activation_email_sent': sent})

    log_action('user.bulk_create', 'Institution', inst.id, {
        'institution': inst.institution, 'plan': plan, 'trial': trial, 'trial_days': trial_days,
        'requested': len(rows), 'created': len(created), 'failed': len(failed),
        'created_emails': [c['email'] for c in created][:50],
        'failed_rows': failed[:50],
    })

    return jsonify({'ok': True, 'created': created, 'failed': failed, 'summary': {
        'total': len(rows), 'created': len(created), 'failed': len(failed),
        'emails_sent': sum(1 for c in created if c['activation_email_sent']),
    }}), 201
