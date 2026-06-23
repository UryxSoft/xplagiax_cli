# websocket_handlers.py - Manejadores para eventos WebSocket
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from modules.monitoring_endpoints import handle_start_monitoring, handle_stop_monitoring

def register_websocket_handlers(socketio):
    """
    Registra los manejadores de eventos WebSocket
    """
    
    @socketio.on('connect')
    def handle_connect():
        print(f'Cliente conectado: {current_user.id if current_user.is_authenticated else "Anonymous"}')
        if current_user.is_authenticated:
            join_room(f'monitor_{current_user.id}')
        emit('connected', {'status': 'success'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Cliente desconectado: {current_user.id if current_user.is_authenticated else "Anonymous"}')
        if current_user.is_authenticated:
            leave_room(f'monitor_{current_user.id}')
    
    @socketio.on('start_monitoring')
    def handle_start_monitoring_event():
        if current_user.is_authenticated:
            handle_start_monitoring(socketio, current_user)
        else:
            emit('monitoring_error', {'error': 'Usuario no autenticado'})
    
    @socketio.on('stop_monitoring')
    def handle_stop_monitoring_event():
        if current_user.is_authenticated:
            handle_stop_monitoring(current_user)
        else:
            emit('monitoring_error', {'error': 'Usuario no autenticado'})