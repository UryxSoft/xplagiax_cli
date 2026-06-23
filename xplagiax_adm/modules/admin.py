# admin.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.connections import db
from models.model import Users_admin, SSHSession, SessionLog
import psutil
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function._name_ = f.__name__
    return decorated_function

@admin_bp.route('/')
#@login_required
#@admin_required
def dashboard():
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # App metrics
    total_users = Users_admin.query.count()
    active_users = Users_admin.query.filter_by(is_active=True).count()
    total_sessions = SSHSession.query.count()
    active_sessions = SSHSession.query.filter_by(is_active=True).count()
    
    # Recent activity
    recent_logs = SessionLog.query.order_by(SessionLog.timestamp.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         cpu_percent=cpu_percent,
                         memory=memory,
                         disk=disk,
                         total_users=total_users,
                         active_users=active_users,
                         total_sessions=total_sessions,
                         active_sessions=active_sessions,
                         recent_logs=recent_logs)

@admin_bp.route('/users')
#@login_required
#@admin_required
def users():
    users = Users_admin.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/toggle')
#@login_required
#@admin_required
def toggle_user(user_id):
    user = Users_admin.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {user.username} {"activated" if user.is_active else "deactivated"}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/sessions')
#@login_required
#@admin_required
def sessions():
    sessions = SSHSession.query.all()
    return render_template('admin/sessions.html', sessions=sessions)

@admin_bp.route('/logs')
#@login_required
#@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    logs = SessionLog.query.order_by(SessionLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False)
    return render_template('admin/logs.html', logs=logs)