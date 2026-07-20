"""
Modelos de appcli2 que el admin necesita leer/escribir y que NO estaban en
models/model.py del admin: límites por plan y consumo diario de análisis.
Espejo exacto de xplagiax_appcli2/modules/models/model.py (tablas
analysis_limits / user_analysis_usage) — misma DB compartida.
"""
from datetime import datetime

from utils.connections import db

PLANS = ('Starter', 'Scholar Suite', 'Individual', 'Research Essentials', 'Institutes')


class AnalysisLimit(db.Model):
    __tablename__ = 'analysis_limits'
    id                   = db.Column(db.Integer, primary_key=True)
    plan_name            = db.Column(db.String(64), nullable=False, index=True)
    daily_analysis_limit = db.Column(db.Integer, nullable=False, default=0)
    is_active            = db.Column(db.Boolean, default=True)


class UserAnalysisUsage(db.Model):
    __tablename__ = 'user_analysis_usage'
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, nullable=False, index=True)
    usage_date       = db.Column(db.Date, nullable=False, index=True)
    analysis_count   = db.Column(db.Integer, default=0)
    limit_reached_at = db.Column(db.DateTime, nullable=True)
    last_reset_at    = db.Column(db.DateTime, nullable=True)
    updated_at       = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
