from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from flask_socketio import join_room, leave_room, emit
from utils.connections import db
from models.model import SSHSession
from utils.ssh_manager import SSHManager
from utils.encryption import EncryptionManager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

terminal_bp = Blueprint('terminal_bp', __name__)
ssh_manager = SSHManager()
encryption_manager = EncryptionManager()

@terminal_bp.route('/terminal/<int:session_id>')
def terminal(session_id):
    session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    return render_template('/terminal/terminal_new.html', session=session)

def socket_events(socketio):
    @socketio.on('connect')
    def handle_connect(auth):
        """Remover @login_required y verificar manualmente"""
        try:
            if not current_user.is_authenticated:
                return False
            
            join_room(f'user_{current_user.id}')
            logger.info(f"Usuario {current_user.id} conectado via socketio")
            emit('connection_status', {'status': 'connected'})
            return True
        except Exception as e:
            logger.error(f"Error en connect: {str(e)}")
            return False

    @socketio.on('disconnect')
    def handle_disconnect():
        """Remover @login_required"""
        try:
            if current_user.is_authenticated:
                leave_room(f'user_{current_user.id}')
                logger.info(f"Usuario {current_user.id} desconectado via socketio")
        except Exception as e:
            logger.error(f"Error en disconnect: {str(e)}")

    @socketio.on('ssh_connect')
    def handle_ssh_connect(data):
        """Debug mejorado para ssh_connect"""
        try:
            print(f"🔍 DEBUG: ssh_connect recibido con data: {data}")
            
            if not current_user.is_authenticated:
                print("❌ DEBUG: Usuario no autenticado")
                emit('ssh_error', {'error': 'Usuario no autenticado'})
                return

            session_id = data.get('session_id')
            print(f"🔍 DEBUG: session_id = {session_id}")
            
            if not session_id:
                print("❌ DEBUG: No session ID provided")
                emit('ssh_error', {'error': 'No session ID provided'})
                return
            
            session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first()
            print(f"🔍 DEBUG: session encontrada = {session}")
            
            if not session:
                print("❌ DEBUG: Session not found")
                emit('ssh_error', {'error': 'Session not found'})
                return
            
            print(f"🔍 DEBUG: Sesión: {session.name}, Host: {session.hostname}:{session.port}, User: {session.username}")
            
        
            password = None
            if session.password_encrypted:
                try:
                    password = encryption_manager.decrypt(session.password_encrypted)
                    print(f"🔍 DEBUG: Contraseña desencriptada exitosamente: {'*' if password else 'VACIA'}")
                except Exception as e:
                    print(f"❌ DEBUG: Error desencriptando contraseña: {str(e)}")
                    emit('ssh_error', {'error': f'Error desencriptando contraseña: {str(e)}'})
                    return
            
            # Test de conectividad básica
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((session.hostname, session.port))
                sock.close()
                
                if result != 0:
                    error_msg = f"No se puede conectar a {session.hostname}:{session.port}"
                    print(f"❌ DEBUG: {error_msg}")
                    emit('ssh_error', {'error': error_msg})
                    return
                else:
                    print(f"✅ DEBUG: Puerto {session.hostname}:{session.port} alcanzable")
            except Exception as e:
                error_msg = f"Error de conectividad: {str(e)}"
                print(f"❌ DEBUG: {error_msg}")
                emit('ssh_error', {'error': error_msg})
                return
            
            logger.info(f"Attempting SSH connection for session {session_id}")
            
            # Crear conexión SSH
            print("🔍 DEBUG: Iniciando create_connection...")
            connection_id = ssh_manager.create_connection(
                session_id=session_id,
                hostname=session.hostname,
                port=session.port,
                username=session.username,
                password=password,
                key_path=session.key_path
            )
            print(f"🔍 DEBUG: create_connection resultado: {connection_id}")
            
            if connection_id:
                print("🔍 DEBUG: Iniciando create_terminal...")
                # Crear terminal interactivo
                terminal_created = ssh_manager.create_terminal(
                    session_id=session_id,
                    cols=data.get('cols', 80),
                    rows=data.get('rows', 24),
                    socketio=socketio
                )
                print(f"🔍 DEBUG: create_terminal resultado: {terminal_created}")
                
                if terminal_created:
                    room = f'ssh_{session_id}'
                    join_room(room)
                    
                    # Actualizar estado de la sesión
                    session.last_used_at = datetime.utcnow()
                    session.is_active = True
                    session.connected_at = datetime.utcnow()
                    db.session.commit()
                    
                    emit('ssh_connected', {
                        'session_id': session_id,
                        'hostname': session.hostname,
                        'username': session.username
                    })
                    
                    print(f"✅ DEBUG: SSH terminal connected for session {session_id}")
                    logger.info(f"SSH terminal connected for session {session_id}")
                else:
                    print("❌ DEBUG: Failed to create terminal")
                    ssh_manager.close_connection(session_id)
                    emit('ssh_error', {'error': 'Failed to create terminal'})
            else:
                print("❌ DEBUG: Failed to establish SSH connection")
                emit('ssh_error', {'error': 'Failed to establish SSH connection'})
                
        except Exception as e:
            error_msg = f'Connection failed: {str(e)}'
            print(f"❌ DEBUG: Exception en ssh_connect: {error_msg}")
            logger.error(f"SSH connection error: {error_msg}")
            emit('ssh_error', {'error': error_msg})

    @socketio.on('terminal_input')
    def handle_terminal_input(data):
        """Manejar entrada de terminal con mejor error handling"""
        try:
            if not current_user.is_authenticated:
                emit('terminal_error', {'error': 'Usuario no autenticado'})
                return

            session_id = data.get('session_id')
            input_data = data.get('data', '')
            
            logger.debug(f"Terminal input for session {session_id}: {repr(input_data)}")
            
            if not session_id:
                emit('terminal_error', {'error': 'No session ID provided'})
                return
            
            # Verificar que el usuario tiene acceso a esta sesión
            session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first()
            if not session:
                emit('terminal_error', {'error': 'Sesión no encontrada o sin permisos'})
                return
            
            success = ssh_manager.send_input(session_id, input_data)
            if not success:
                emit('terminal_error', {'error': 'Failed to send input to terminal'})
                logger.warning(f"Failed to send input to session {session_id}")
                
        except Exception as e:
            logger.error(f"Error sending terminal input: {str(e)}")
            emit('terminal_error', {'error': f'Input error: {str(e)}'})

    @socketio.on('terminal_resize')
    def handle_terminal_resize(data):
        try:
            if not current_user.is_authenticated:
                return

            session_id = data.get('session_id')
            cols = data.get('cols', 80)
            rows = data.get('rows', 24)
            
            if not session_id:
                return
            
            success = ssh_manager.resize_terminal(session_id, cols, rows)
            if success:
                emit('terminal_resized', {
                    'session_id': session_id,
                    'cols': cols,
                    'rows': rows
                })
                logger.info(f"Terminal resized: {cols}x{rows} for session {session_id}")
        except Exception as e:
            logger.error(f"Error resizing terminal: {str(e)}")

    @socketio.on('ssh_disconnect')
    def handle_ssh_disconnect(data):
        try:
            if not current_user.is_authenticated:
                return

            session_id = data.get('session_id')
            
            if not session_id:
                return
            
            # Verificar que la sesión pertenece al usuario
            session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first()
            if session:
                ssh_manager.close_connection(session_id)
                
                # Actualizar estado de la sesión
                session.is_active = False
                session.last_used_at = datetime.utcnow()
                db.session.commit()
                
                leave_room(f'ssh_{session_id}')
                emit('ssh_disconnected', {'session_id': session_id})
                
                logger.info(f"SSH session {session_id} disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting SSH session: {str(e)}")

    @socketio.on('get_terminal_status')
    def handle_get_terminal_status(data):
        try:
            if not current_user.is_authenticated:
                return

            session_id = data.get('session_id')
            
            if not session_id:
                return
            
            status = ssh_manager.get_terminal_status(session_id)
            emit('terminal_status', {
                'session_id': session_id,
                'status': status
            })
        except Exception as e:
            logger.error(f"Error getting terminal status: {str(e)}")

    @socketio.on('ping')
    def handle_ping(data):
        """Mantener viva la conexión websocket"""
        try:
            emit('pong', {'timestamp': datetime.utcnow().isoformat()})
        except Exception as e:
            logger.error(f"Error in ping: {str(e)}")

    return socketio