"""
Auditoría de acciones administrativas: quién / qué / a quién / cuándo / IP /
user-agent / before-after. Tabla propia del admin (admin_audit_log), creada
on-demand con el mismo patrón aditivo `_ensure_*` que usa appcli2.
"""
import json
import logging
from datetime import datetime

from flask import request
from flask_login import current_user

from utils.connections import db

logger = logging.getLogger(__name__)
_TABLE_READY = False


class AdminAuditLog(db.Model):
    __tablename__ = 'admin_audit_log'
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id    = db.Column(db.Integer, nullable=True, index=True)
    admin_email = db.Column(db.String(120), nullable=True)
    action      = db.Column(db.String(64), nullable=False, index=True)
    entity      = db.Column(db.String(64), nullable=True)
    entity_id   = db.Column(db.String(64), nullable=True, index=True)
    detail      = db.Column(db.Text, nullable=True)   # JSON before/after u observaciones
    ip          = db.Column(db.String(64), nullable=True)
    user_agent  = db.Column(db.String(255), nullable=True)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


def ensure_table():
    """Pública: también la usa adminx_audit.py (visor) para poder listar/filtrar
    incluso antes de que se haya escrito la primera fila."""
    global _TABLE_READY
    if _TABLE_READY:
        return
    try:
        AdminAuditLog.__table__.create(db.engine, checkfirst=True)
        _TABLE_READY = True
    except Exception:
        logger.warning('No se pudo asegurar admin_audit_log', exc_info=True)


def log_action(action, entity=None, entity_id=None, detail=None):
    """Best-effort: la auditoría nunca debe tumbar la operación que audita."""
    try:
        ensure_table()
        row = AdminAuditLog(
            admin_id=getattr(current_user, 'id', None) if current_user and current_user.is_authenticated else None,
            admin_email=getattr(current_user, 'email', None) if current_user and current_user.is_authenticated else None,
            action=str(action)[:64],
            entity=(str(entity)[:64] if entity else None),
            entity_id=(str(entity_id)[:64] if entity_id is not None else None),
            detail=(json.dumps(detail, default=str)[:60000] if detail is not None else None),
            ip=request.headers.get('X-Real-IP', request.remote_addr) if request else None,
            user_agent=(request.headers.get('User-Agent', '')[:255] if request else None),
        )
        db.session.add(row)
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.warning('audit log failed for action=%s', action, exc_info=True)
