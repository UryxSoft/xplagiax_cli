"""
Bootstrap del primer superadmin — mismo patrón que ensure_institution_schema
(no-op tras el primer éxito por proceso, try/except no fatal). Si la tabla
'users_admin' está vacía, crea un superadmin a partir de
ADMIN_MASTER_EMAIL/ADMIN_MASTER_PASSWORD (utils/config.py) para que un
despliegue nuevo tenga forma de entrar sin acceso directo a la base de
datos. La contraseña se guarda siempre con Users_admin.set_password
(hash de Werkzeug) — nunca en texto plano en la DB.
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
        if Users_admin.query.count() == 0:
            email = current_app.config['ADMIN_MASTER_EMAIL']
            password = current_app.config['ADMIN_MASTER_PASSWORD']
            admin = Users_admin(username='admin', email=email,
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
