"""
Bootstrap del superadmin master — mismo patrón que ensure_institution_schema
(no-op tras el primer éxito por proceso, try/except no fatal). Garantiza que
ADMIN_MASTER_EMAIL (utils/config.py) exista como superadmin activo,
creándolo si falta — sin importar si 'users_admin' ya tiene otras filas
(una DB real de producción casi nunca está vacía; condicionar a "la tabla
está vacía" significaba que este alta nunca se disparaba). Solo CREA si el
email todavía no existe: si ya existe (con la contraseña que sea — el admin
pudo haberla rotado desde el panel), no la toca en cada reinicio. La
contraseña se guarda siempre con Users_admin.set_password (hash de
Werkzeug) — nunca en texto plano en la DB.
"""
import logging

from flask import current_app

from utils.connections import db
from models.model import Users_admin

logger = logging.getLogger(__name__)
_READY = False


def ensure_master_admin():
    global _READY
    if _READY:
        return
    try:
        email = current_app.config['ADMIN_MASTER_EMAIL']
        password = current_app.config['ADMIN_MASTER_PASSWORD']
        exists = Users_admin.query.filter(
            (Users_admin.email == email) | (Users_admin.username == 'master-admin')
        ).first()
        if not exists:
            admin = Users_admin(username='master-admin', email=email,
                                role='superadmin', is_active=True)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            logger.warning(
                'Master superadmin bootstrapped (%s) — change this password '
                'from the panel and/or set ADMIN_MASTER_PASSWORD by env.', email)
        _READY = True
    except Exception:
        db.session.rollback()
        logger.warning('ensure_master_admin failed (non-fatal)', exc_info=True)
