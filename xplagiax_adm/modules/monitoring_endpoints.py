from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
import psutil
from models.model import SSHSession, Users_admin
import time
from threading import Thread

monitoring_bp = Blueprint('monitoring_bp', __name__)

# Variable global para controlar el hilo de monitoreo
monitoring_threads = {}

@monitoring_bp.route('/api/active_sessions')
@login_required
def get_active_sessions():
    try:
        active_sessions = SSHSession.query.filter_by(user_id=current_user.id, is_active=True).all()
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'hostname': s.hostname,
            'username': s.username,
            'connected_at': s.connected_at.isoformat() if s.connected_at else None,
            'last_activity': s.last_activity.isoformat() if s.last_activity else None
        } for s in active_sessions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_monitoring_task(socketio):
    def monitoring_task():
        while True:
            try:
                time.sleep(5)
                for user in Users_admin.query.filter_by(is_active=True).all():
                    cpu_percent = psutil.cpu_percent()
                    memory = psutil.virtual_memory()
                    
                    active_sessions = SSHSession.query.filter_by(user_id=user.id, is_active=True).all()
                    sessions_data = [{
                        'id': s.id,
                        'name': s.name,
                        'hostname': s.hostname,
                        'username': s.username,
                        'connected_at': s.connected_at.isoformat() if s.connected_at else None,
                        'last_activity': s.last_activity.isoformat() if s.last_activity else None,
                        'traffic': 0  # Agregar campo de tráfico
                    } for s in active_sessions]
                    
                    # Cambiar el nombre del evento para que coincida con el frontend
                    socketio.emit('system_stats', {
                        'cpu': cpu_percent,
                        'memory': {
                            'total': memory.total,
                            'used': memory.used,
                            'percent': memory.percent
                        },
                        'active_sessions': sessions_data
                    }, room=f'monitor_{user.id}')
            except Exception as e:
                print(f"Error en monitoring task: {e}")
                break
    
    thread = Thread(target=monitoring_task)
    thread.daemon = True
    thread.start()
    return thread

# Funciones para manejar eventos de WebSocket
def handle_start_monitoring(socketio, current_user):
    try:
        room = f'monitor_{current_user.id}'
        join_room(room)
        
        # Iniciar hilo de monitoreo específico para este usuario si no existe
        if current_user.id not in monitoring_threads:
            monitoring_threads[current_user.id] = start_user_monitoring(socketio, current_user.id)
        
        emit('monitoring_started', {'status': 'success'})
    except Exception as e:
        emit('monitoring_error', {'error': str(e)})

def handle_stop_monitoring(current_user):
    try:
        room = f'monitor_{current_user.id}'
        leave_room(room)
        
        # Detener hilo de monitoreo específico
        if current_user.id in monitoring_threads:
            monitoring_threads[current_user.id] = None
        
        emit('monitoring_stopped', {'status': 'success'})
    except Exception as e:
        emit('monitoring_error', {'error': str(e)})

def start_user_monitoring(socketio, user_id):
    def user_monitoring_task():
        while monitoring_threads.get(user_id) is not None:
            try:
                time.sleep(5)
                
                # Obtener estadísticas del sistema
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                # Obtener sesiones activas del usuario
                active_sessions = SSHSession.query.filter_by(user_id=user_id, is_active=True).all()
                sessions_data = [{
                    'id': s.id,
                    'name': s.name,
                    'hostname': s.hostname,
                    'username': s.username,
                    'connected_at': s.connected_at.isoformat() if s.connected_at else None,
                    'last_activity': s.last_activity.isoformat() if s.last_activity else None,
                    'traffic': 0  # Placeholder para tráfico
                } for s in active_sessions]
                
                # Enviar datos al cliente
                socketio.emit('system_stats', {
                    'cpu': cpu_percent,
                    'memory': {
                        'total': memory.total,
                        'used': memory.used,
                        'percent': memory.percent
                    },
                    'active_sessions': sessions_data
                }, room=f'monitor_{user_id}')
                
            except Exception as e:
                print(f"Error en user monitoring task: {e}")
                break
    
    thread = Thread(target=user_monitoring_task)
    thread.daemon = True
    thread.start()
    return thread