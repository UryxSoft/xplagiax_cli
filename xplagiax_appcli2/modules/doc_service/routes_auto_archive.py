"""Auto-Archive document lifecycle: Active -> Archived -> Permanently Deleted.

Independent of the manual archive/trash flow in doc_routes.py/bucket_routes.py
(File.status == 'Archivado' / File.is_trash / File.expires_at). This module
only ever touches its own columns (archive_cycle_reset_at / auto_archived_at /
auto_archive_delete_at) and always skips rows the manual flow has claimed
(status == 'Archivado' or is_trash == True), so the two mechanisms never act
on the same row.
"""
from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import logging

from app import db
from modules.models.model import File, UserPreference, ItemHistory, Users

logger = logging.getLogger(__name__)

x_autoarchive = Blueprint('x_autoarchive', __name__)

BATCH_LIMIT = 500


def _delete_single_file_physical(file_obj):
    """Best-effort: SeaweedFS blob + Qdrant image embeddings for one File.
    Never raises — physical cleanup failure must not block the SQL delete."""
    try:
        if file_obj.minio_url:
            from modules.bucket_service.bucket_routes import get_storage_client
            owner = Users.query.get(file_obj.user_id)
            get_storage_client().delete_file(file_obj.minio_url, user=owner)
    except Exception:
        logger.warning('auto_archive: seaweedfs delete failed file=%s', file_obj.id, exc_info=True)
    try:
        from modules.doc_service.doc_routes import _purge_qdrant_images
        _purge_qdrant_images([str(file_obj.id)])
    except Exception:
        logger.warning('auto_archive: qdrant purge failed file=%s', file_obj.id, exc_info=True)


def _log_history(file_id, user_id, action, old_value, new_value):
    try:
        db.session.add(ItemHistory(
            item_type='file', item_id=file_id, action=action,
            old_value=old_value, new_value=new_value, user_id=user_id
        ))
    except Exception:
        logger.warning('auto_archive: could not write ItemHistory file=%s action=%s', file_id, action, exc_info=True)


# ---------------------------------------------------------------------------
# User-facing routes
# ---------------------------------------------------------------------------

@x_autoarchive.route('/files', methods=['GET'])
@login_required
def list_auto_archived_files():
    files = (File.query
             .filter_by(user_id=current_user.id)
             .filter(File.auto_archived_at.isnot(None))
             .order_by(File.auto_archive_delete_at.asc())
             .limit(200).all())
    return jsonify({
        'success': True,
        'files': [{
            'id': f.id,
            'name': f.original_filename,
            'mime_type': f.mime_type,
            'size': f.size,
            'created_at': f.created_at.isoformat() if f.created_at else None,
            'auto_archived_at': f.auto_archived_at.isoformat() if f.auto_archived_at else None,
            'auto_archive_delete_at': f.auto_archive_delete_at.isoformat() if f.auto_archive_delete_at else None,
        } for f in files]
    })


@x_autoarchive.route('/files/<int:file_id>/restore', methods=['POST'])
@login_required
def restore_auto_archived_file(file_id):
    f = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not f or not f.auto_archived_at:
        return jsonify({'success': False, 'error': 'File not found'}), 404

    f.auto_archived_at = None
    f.auto_archive_delete_at = None
    f.archive_cycle_reset_at = datetime.utcnow()
    _log_history(f.id, f.user_id, 'restore_from_archive', 'archived', 'active')
    db.session.commit()

    try:
        from modules.bucket_service.bucket_routes import clear_cache_for_user
        clear_cache_for_user(current_user.id)
    except Exception:
        pass

    return jsonify({'success': True})


@x_autoarchive.route('/files/<int:file_id>/delete-now', methods=['POST'])
@login_required
def delete_now_auto_archived_file(file_id):
    f = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not f or not f.auto_archived_at:
        return jsonify({'success': False, 'error': 'File not found'}), 404

    _delete_single_file_physical(f)
    _log_history(f.id, f.user_id, 'delete_now', 'archived', 'deleted')
    db.session.delete(f)
    db.session.commit()

    try:
        from modules.bucket_service.bucket_routes import clear_cache_for_user
        clear_cache_for_user(current_user.id)
    except Exception:
        pass

    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Scheduled sweep (daily, see app.py setup_scheduler())
# ---------------------------------------------------------------------------

def run_auto_archive_sweep():
    """Two-phase daily sweep: archive stale active files, then permanently
    delete files whose archive retention window has elapsed. Idempotent —
    running it twice in the same day is a no-op the second time, since each
    phase only selects rows still in the state it acts on."""
    from app import app as flask_app

    with flask_app.app_context():
        now = datetime.utcnow()
        archived_count = 0
        deleted_count = 0

        try:
            prefs = UserPreference.query.filter_by(auto_archive_enabled=True).all()

            # Phase 1: Active -> Archived
            for pref in prefs:
                cutoff = now - timedelta(days=pref.archive_after_days or 15)
                candidates = File.query.filter(
                    File.user_id == pref.user_id,
                    File.auto_archived_at.is_(None),
                    File.status != 'Archivado',
                    File.is_trash == False,  # noqa: E712
                ).filter(
                    db.or_(
                        db.and_(File.archive_cycle_reset_at.isnot(None), File.archive_cycle_reset_at <= cutoff),
                        db.and_(File.archive_cycle_reset_at.is_(None), File.created_at <= cutoff),
                    )
                ).limit(BATCH_LIMIT).all()

                for f in candidates:
                    f.auto_archived_at = now
                    f.auto_archive_delete_at = now + timedelta(days=pref.delete_after_archive_days or 15)
                    _log_history(f.id, f.user_id, 'auto_archive', 'active', 'archived')
                    archived_count += 1
            db.session.commit()

            # Phase 2: Archived -> Permanently Deleted
            enabled_user_ids = [p.user_id for p in prefs]
            if enabled_user_ids:
                expired = File.query.filter(
                    File.user_id.in_(enabled_user_ids),
                    File.auto_archived_at.isnot(None),
                    File.auto_archive_delete_at.isnot(None),
                    File.auto_archive_delete_at <= now,
                    File.status != 'Archivado',
                    File.is_trash == False,  # noqa: E712
                ).limit(BATCH_LIMIT).all()

                for f in expired:
                    _delete_single_file_physical(f)
                    _log_history(f.id, f.user_id, 'auto_delete', 'archived', 'deleted')
                    db.session.delete(f)
                    deleted_count += 1
                db.session.commit()

            logger.info('auto_archive_sweep: archived=%s deleted=%s', archived_count, deleted_count)
            return True
        except Exception as exc:
            db.session.rollback()
            logger.error('auto_archive_sweep: failed: %s', exc, exc_info=True)
            return False
