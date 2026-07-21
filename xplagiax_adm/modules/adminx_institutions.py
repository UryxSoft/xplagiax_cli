"""
Gestión de Instituciones Académicas (F3): CRUD, logo automático/manual,
asociación con usuarios del plan Institutes. Mismo patrón que adminx_users.
"""
import os
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, current_app
from flask_login import login_required
from sqlalchemy import func, or_

from utils.connections import db
from models.model import Institution, Institution_type, Country, City, Users
from core.institution_migrate import ensure_institution_schema
from core.institution_logos import fetch_official_logo, validate_and_store, MAX_UPLOAD_BYTES
from core.security import require_role, get_csrf_token
from core.audit import log_action

adminx_institutions_bp = Blueprint('adminx_institutions', __name__)


@adminx_institutions_bp.before_request
def _ensure_schema():
    ensure_institution_schema()


@adminx_institutions_bp.route('/', methods=['GET'])
@login_required
def page():
    return render_template('adminx/institutions.html', csrf_token=get_csrf_token())


@adminx_institutions_bp.route('/api/institutions', methods=['GET'])
@login_required
def list_institutions():
    q = Institution.query.filter(Institution.deleted_at.is_(None))
    search = request.args.get('search', '').strip()
    if search:
        q = q.filter(Institution.institution.like(f'%{search}%'))
    country_id = request.args.get('country_id')
    if country_id:
        q = q.filter(Institution.country_id == int(country_id))
    status = request.args.get('status', '').strip()
    if status in ('active', 'inactive'):
        q = q.filter(Institution.status == status)

    page_n = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(5, int(request.args.get('per_page', 20))))
    total = q.count()
    rows = (q.order_by(Institution.institution.asc())
            .offset((page_n - 1) * per_page).limit(per_page).all())

    counts = dict(db.session.query(Users.institution_id, func.count(Users.id))
                  .filter(Users.institution_id.isnot(None)).group_by(Users.institution_id).all())
    return jsonify({
        'institutions': [i.to_dict(user_count=counts.get(i.id, 0)) for i in rows],
        'total': total, 'page': page_n, 'per_page': per_page,
    })


@adminx_institutions_bp.route('/api/institutions/lookup', methods=['GET'])
@login_required
def lookup_institutions():
    """Para el selector del módulo de Usuarios — lista liviana, sin paginar."""
    rows = (Institution.query.filter(Institution.deleted_at.is_(None),
                                     Institution.status == 'active')
            .order_by(Institution.institution.asc()).limit(500).all())
    return jsonify({'institutions': [{'id': i.id, 'name': i.institution,
                                      'country': i.country.country if i.country else None}
                                     for i in rows]})


@adminx_institutions_bp.route('/api/options', methods=['GET'])
@login_required
def options():
    return jsonify({
        'countries': [{'id': c.id, 'name': c.country} for c in Country.query.order_by(Country.country).all()],
        'types': [{'id': t.id, 'name': t.institution_type}
                 for t in Institution_type.query.order_by(Institution_type.institution_type).all()],
        'cities': [{'id': c.id, 'name': c.city, 'state_id': c.state_id}
                  for c in City.query.order_by(City.city).limit(2000).all()],
    })


def _apply_fields(inst, data):
    if 'name' in data:
        name = str(data['name']).strip()
        if not name:
            return 'Institution name is required.'
        inst.institution = name
    if 'country_id' in data and data['country_id']:
        inst.country_id = int(data['country_id'])
    if 'city_id' in data:
        inst.city_id = int(data['city_id']) if data['city_id'] else None
    if 'institution_type_id' in data:
        inst.institution_type = int(data['institution_type_id']) if data['institution_type_id'] else None
    if 'website' in data:
        inst.website = (str(data['website']).strip() or None)
    if 'domain' in data:
        inst.domain = (str(data['domain']).strip().lower() or None)
    if 'status' in data and data['status'] in ('active', 'inactive'):
        inst.status = data['status']
    return None


@adminx_institutions_bp.route('/api/institutions', methods=['POST'])
@require_role('admin')
def create_institution():
    data = request.get_json(silent=True) or {}
    if not str(data.get('name') or '').strip():
        return jsonify({'error': 'Institution name is required.'}), 400
    if not data.get('country_id'):
        return jsonify({'error': 'Country is required.'}), 400

    inst = Institution(institution=str(data['name']).strip(), country_id=int(data['country_id']))
    err = _apply_fields(inst, data)
    if err:
        return jsonify({'error': err}), 400
    db.session.add(inst)
    db.session.commit()

    # Logo: best-effort, nunca bloquea la creación.
    if inst.website or inst.domain:
        try:
            path = fetch_official_logo(website=inst.website, domain=inst.domain)
            if path:
                inst.logo_path = path
                db.session.commit()
        except Exception:
            current_app.logger.warning('Auto logo fetch failed for institution %s', inst.id, exc_info=True)

    log_action('institution.create', 'Institution', inst.id, {'name': inst.institution})
    return jsonify({'ok': True, 'institution': inst.to_dict(user_count=0)}), 201


@adminx_institutions_bp.route('/api/institutions/<int:iid>', methods=['PATCH'])
@require_role('admin')
def update_institution(iid):
    inst = Institution.query.get_or_404(iid)
    data = request.get_json(silent=True) or {}
    before = inst.to_dict()
    err = _apply_fields(inst, data)
    if err:
        return jsonify({'error': err}), 400
    db.session.commit()
    log_action('institution.update', 'Institution', iid, {'before': before, 'data': data})
    return jsonify({'ok': True, 'institution': inst.to_dict()})


@adminx_institutions_bp.route('/api/institutions/<int:iid>/status', methods=['POST'])
@require_role('admin')
def toggle_status(iid):
    inst = Institution.query.get_or_404(iid)
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in ('active', 'inactive'):
        return jsonify({'error': 'status must be active|inactive'}), 400
    inst.status = new_status
    db.session.commit()
    log_action(f'institution.{new_status}', 'Institution', iid, {'name': inst.institution})
    return jsonify({'ok': True, 'institution': inst.to_dict()})


@adminx_institutions_bp.route('/api/institutions/<int:iid>', methods=['DELETE'])
@require_role('admin')
def delete_institution(iid):
    """Soft delete — nunca hard delete (romper la FK de usuarios asociados
    dejaría cuentas huérfanas). Los usuarios ya asociados conservan la
    referencia histórica; se les puede reasignar institución manualmente."""
    inst = Institution.query.get_or_404(iid)
    inst.deleted_at = datetime.utcnow()
    inst.status = 'inactive'
    db.session.commit()
    log_action('institution.delete_soft', 'Institution', iid, {'name': inst.institution})
    return jsonify({'ok': True})


@adminx_institutions_bp.route('/api/institutions/<int:iid>/logo/fetch', methods=['POST'])
@require_role('admin')
def refetch_logo(iid):
    inst = Institution.query.get_or_404(iid)
    if not (inst.website or inst.domain):
        return jsonify({'error': 'Set a website or domain first.'}), 400
    path = fetch_official_logo(website=inst.website, domain=inst.domain)
    if not path:
        return jsonify({'error': 'Could not find an official logo automatically. '
                                 'Upload one manually instead.'}), 422
    inst.logo_path = path
    db.session.commit()
    log_action('institution.logo_fetch', 'Institution', iid, {'logo_path': path})
    return jsonify({'ok': True, 'logo_path': path})


@adminx_institutions_bp.route('/api/institutions/<int:iid>/logo/upload', methods=['POST'])
@require_role('admin')
def upload_logo(iid):
    inst = Institution.query.get_or_404(iid)
    file = request.files.get('logo')
    if not file or not file.filename:
        return jsonify({'error': 'No file provided.'}), 400
    data = file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        return jsonify({'error': 'File too large (max 3MB).'}), 413
    path = validate_and_store(data, filename_hint=file.filename)
    if not path:
        return jsonify({'error': 'Invalid or unsafe image. Use PNG, JPG or SVG.'}), 422
    inst.logo_path = path
    db.session.commit()
    log_action('institution.logo_upload', 'Institution', iid, {'logo_path': path})
    return jsonify({'ok': True, 'logo_path': path})
