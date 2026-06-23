# auth.py
from functools import wraps
from flask import request, jsonify
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'error': 'Admin required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def session_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = kwargs.get('session_id') or request.view_args.get('session_id')
        if session_id:
            from models import SSHSession
            session = SSHSession.query.get_or_404(session_id)
            if session.user_id != current_user.id and current_user.role != 'admin':
                return jsonify({'error': 'Not authorized'}), 403
        return f(*args, **kwargs)
    return decorated_function
