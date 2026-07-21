"""
Migración en runtime, ADITIVA (mismo patrón que _ensure_totp_columns de
appcli2: ALTER TABLE ADD COLUMN guardado por inspección de esquema, nunca
Alembic bloqueante). Se ejecuta una vez por proceso, con try/except no
fatal — si algo falla queda logueado pero la app sigue arrancando.
"""
import logging

from sqlalchemy import inspect as sa_inspect, text as sa_text

from utils.connections import db

logger = logging.getLogger(__name__)
_READY = False


def ensure_institution_schema():
    global _READY
    if _READY:
        return
    try:
        insp = sa_inspect(db.engine)
        inst_cols = {c['name'] for c in insp.get_columns('Institution')}
        adds = []
        if 'logo_path' not in inst_cols:
            adds.append("ADD COLUMN logo_path VARCHAR(500) NULL")
        if 'website' not in inst_cols:
            adds.append("ADD COLUMN website VARCHAR(255) NULL")
        if 'domain' not in inst_cols:
            adds.append("ADD COLUMN domain VARCHAR(255) NULL")
        if 'status' not in inst_cols:
            adds.append("ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'")
        if 'verified_at' not in inst_cols:
            adds.append("ADD COLUMN verified_at DATETIME NULL")
        if 'updated_at' not in inst_cols:
            adds.append("ADD COLUMN updated_at DATETIME NULL")
        if 'deleted_at' not in inst_cols:
            adds.append("ADD COLUMN deleted_at DATETIME NULL")
        # institution_type/city_id ya existían pero como NOT NULL sin default —
        # permitir NULL es lo que habilita el selector opcional de ciudad/tipo
        # en el panel sin romper filas viejas que sí los tengan.
        nullable_map = {c['name']: c['nullable'] for c in insp.get_columns('Institution')}
        if nullable_map.get('institution_type') is False:
            adds.append("MODIFY COLUMN institution_type INT NULL")
        if nullable_map.get('city_id') is False:
            adds.append("MODIFY COLUMN city_id INT NULL")

        if adds:
            db.session.execute(sa_text(f"ALTER TABLE `Institution` {', '.join(adds)}"))
            db.session.commit()
            logger.info('Institution schema updated: %s', adds)

        user_cols = {c['name'] for c in insp.get_columns('users')}
        if 'institution_id' not in user_cols:
            db.session.execute(sa_text(
                "ALTER TABLE `users` ADD COLUMN institution_id INT NULL"))
            db.session.commit()
            logger.info('users.institution_id added')

        _add_fk_best_effort(insp)
        _READY = True
    except Exception:
        db.session.rollback()
        logger.warning('ensure_institution_schema failed (non-fatal)', exc_info=True)


def _add_fk_best_effort(insp):
    """Constraints reales — SOLO si los datos existentes son íntegros (sin
    huérfanos). Si no, se deja el FK a nivel ORM nomás (join funciona igual;
    simplemente la DB no lo hace cumplir). Nunca bloquea el arranque."""
    fks = {fk['name'] for fk in insp.get_foreign_keys('Institution')}
    checks = [
        ('fk_institution_country', 'Institution', 'country_id', 'Country', 'id'),
        ('fk_institution_city', 'Institution', 'city_id', 'City', 'id'),
        ('fk_institution_type', 'Institution', 'institution_type', 'Institution_type', 'id'),
    ]
    for name, table, col, ref_table, ref_col in checks:
        if name in fks:
            continue
        try:
            orphans = db.session.execute(sa_text(
                f"SELECT COUNT(*) FROM `{table}` t WHERE t.`{col}` IS NOT NULL "
                f"AND NOT EXISTS (SELECT 1 FROM `{ref_table}` r WHERE r.`{ref_col}` = t.`{col}`)"
            )).scalar()
            if orphans:
                logger.info('Skipping FK %s: %d orphan row(s) in %s.%s', name, orphans, table, col)
                continue
            db.session.execute(sa_text(
                f"ALTER TABLE `{table}` ADD CONSTRAINT `{name}` "
                f"FOREIGN KEY (`{col}`) REFERENCES `{ref_table}` (`{ref_col}`)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.info('FK %s not added (non-fatal)', name, exc_info=True)

    user_fks = {fk['name'] for fk in insp.get_foreign_keys('users')}
    if 'fk_users_institution' not in user_fks:
        try:
            orphans = db.session.execute(sa_text(
                "SELECT COUNT(*) FROM `users` u WHERE u.`institution_id` IS NOT NULL "
                "AND NOT EXISTS (SELECT 1 FROM `Institution` i WHERE i.`id` = u.`institution_id`)"
            )).scalar()
            if not orphans:
                db.session.execute(sa_text(
                    "ALTER TABLE `users` ADD CONSTRAINT `fk_users_institution` "
                    "FOREIGN KEY (`institution_id`) REFERENCES `Institution` (`id`)"))
                db.session.commit()
        except Exception:
            db.session.rollback()
            logger.info('FK fk_users_institution not added (non-fatal)', exc_info=True)
