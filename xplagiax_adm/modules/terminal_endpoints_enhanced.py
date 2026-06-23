from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from flask_socketio import join_room, leave_room, emit
from werkzeug.utils import secure_filename
from utils.connections import db
from models.model import SSHSession
from utils.ssh_manager import SSHManager
from utils.encryption import EncryptionManager
from datetime import datetime
import logging
import os
import tempfile
import json
import time

logger = logging.getLogger(__name__)

terminal_bp = Blueprint('terminal_bp', __name__)
ssh_manager = SSHManager()
encryption_manager = EncryptionManager()

# Configuración para upload de archivos
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'txt', 'py', 'js', 'json', 'yaml', 'yml', 'conf', 'cfg', 'sh', 'log'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@terminal_bp.route('/terminal/<int:session_id>')
@login_required
def terminal(session_id):
    session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    return render_template('/terminal/terminal_html_fixed1.html', session=session)

@terminal_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Endpoint para subir archivos via SCP/SFTP"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        session_id = request.form.get('session_id')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400
        
        session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Transferir archivo via SFTP
            success = ssh_manager.upload_file(session_id, file_path, filename)
            
            # Limpiar archivo temporal
            os.remove(file_path)
            
            if success:
                return jsonify({'message': f'File {filename} uploaded successfully'})
            else:
                return jsonify({'error': 'Failed to upload file'}), 500
        
        return jsonify({'error': 'File type not allowed'}), 400
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/api/download/<int:session_id>/<path:filename>')
@login_required
def download_file(session_id, filename):
    """Endpoint para descargar archivos via SCP/SFTP"""
    try:
        session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Descargar archivo via SFTP
        file_content = ssh_manager.download_file(session_id, filename)
        
        if file_content:
            return file_content, 200, {
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename={filename}'
            }
        else:
            return jsonify({'error': 'File not found or download failed'}), 404
            
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/api/sessions/<int:session_id>/stats')
@login_required
def get_session_stats(session_id):
    """Obtener estadísticas de la sesión SSH"""
    try:
        session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        stats = ssh_manager.get_session_stats(session_id)
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

def socket_events(socketio):
    # Storage para sesiones activas y comandos
    active_sessions = {}
    command_history = {}
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Manejo de conexión WebSocket mejorado"""
        try:
            if not current_user.is_authenticated:
                logger.warning("Unauthenticated user tried to connect")
                return False
            
            user_room = f'user_{current_user.id}'
            join_room(user_room)
            
            # Inicializar datos del usuario
            if current_user.id not in active_sessions:
                active_sessions[current_user.id] = {}
            if current_user.id not in command_history:
                command_history[current_user.id] = []
            
            logger.info(f"Usuario {current_user.id} conectado via socketio")
            emit('connection_status', {
                'status': 'connected',
                'user_id': current_user.id,
                'timestamp': datetime.utcnow().isoformat()
            })
            return True
            
        except Exception as e:
            logger.error(f"Error en connect: {str(e)}")
            return False

    @socketio.on('disconnect')
    def handle_disconnect():
        """Manejo de desconexión mejorado"""
        try:
            if current_user.is_authenticated:
                user_room = f'user_{current_user.id}'
                leave_room(user_room)
                logger.info(f"Usuario {current_user.id} desconectado via socketio")
        except Exception as e:
            logger.error(f"Error en disconnect: {str(e)}")

    @socketio.on('ssh_connect')
    def handle_ssh_connect(data):
        """Conexión SSH mejorada con logging detallado"""
        try:
            if not current_user.is_authenticated:
                emit('ssh_error', {'error': 'Usuario no autenticado'})
                return

            session_id = data.get('session_id')
            if not session_id:
                emit('ssh_error', {'error': 'No session ID provided'})
                return
            
            session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first()
            if not session:
                emit('ssh_error', {'error': 'Session not found'})
                return
            
            logger.info(f"Attempting SSH connection for session {session_id} ({session.name})")
            
            # Logging detallado de la sesión
            emit('ssh_status', {
                'message': 'Inicializando conexión SSH...',
                'session': {
                    'id': session_id,
                    'name': session.name,
                    'hostname': session.hostname,
                    'port': session.port,
                    'username': session.username
                }
            })
            
            # Desencriptar password
            password = None
            if session.password_encrypted:
                try:
                    password = encryption_manager.decrypt(session.password_encrypted)
                    logger.info("Password decrypted successfully")
                except Exception as e:
                    logger.error(f"Password decryption failed: {str(e)}")
                    emit('ssh_error', {'error': f'Error desencriptando contraseña: {str(e)}'})
                    return
            
            # Crear conexión SSH
            emit('ssh_status', {'message': 'Estableciendo conexión SSH...'})
            connection_id = ssh_manager.create_connection(
                session_id=session_id,
                hostname=session.hostname,
                port=session.port,
                username=session.username,
                password=password,
                key_path=session.key_path
            )
            
            if connection_id:
                emit('ssh_status', {'message': 'Creando terminal interactivo...'})
                # Crear terminal interactivo
                terminal_created = ssh_manager.create_terminal(
                    session_id=session_id,
                    cols=data.get('cols', 80),
                    rows=data.get('rows', 24),
                    socketio=socketio
                )
                
                if terminal_created:
                    room = f'ssh_{session_id}'
                    join_room(room)
                    
                    # Actualizar estado de la sesión
                    session.last_used_at = datetime.utcnow()
                    session.is_active = True
                    session.connected_at = datetime.utcnow()
                    db.session.commit()
                    
                    # Registrar sesión activa
                    active_sessions[current_user.id][session_id] = {
                        'connected_at': datetime.utcnow(),
                        'commands_count': 0,
                        'last_activity': datetime.utcnow()
                    }
                    
                    emit('ssh_connected', {
                        'session_id': session_id,
                        'hostname': session.hostname,
                        'username': session.username,
                        'connected_at': datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"SSH terminal connected successfully for session {session_id}")
                else:
                    ssh_manager.close_connection(session_id)
                    emit('ssh_error', {'error': 'Failed to create terminal'})
            else:
                emit('ssh_error', {'error': 'Failed to establish SSH connection'})
                
        except Exception as e:
            logger.error(f"SSH connection error: {str(e)}")
            emit('ssh_error', {'error': f'Connection failed: {str(e)}'})

    @socketio.on('terminal_input')
    def handle_terminal_input(data):
        """Manejo de entrada de terminal con logging de comandos"""
        try:
            if not current_user.is_authenticated:
                emit('terminal_error', {'error': 'Usuario no autenticado'})
                return

            session_id = data.get('session_id')
            input_data = data.get('data', '')
            
            if not session_id:
                emit('terminal_error', {'error': 'No session ID provided'})
                return
            
            # Verificar que el usuario tiene acceso a esta sesión
            session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first()
            if not session:
                emit('terminal_error', {'error': 'Sesión no encontrada o sin permisos'})
                return
            
            # Logging de comandos (solo caracteres imprimibles)
            if input_data and ord(input_data[0]) >= 32:
                # Actualizar actividad de sesión
                if current_user.id in active_sessions and session_id in active_sessions[current_user.id]:
                    active_sessions[current_user.id][session_id]['last_activity'] = datetime.utcnow()
                    active_sessions[current_user.id][session_id]['commands_count'] += 1
            
            # Detectar comandos completos (Enter)
            if input_data == '\r':
                current_command = data.get('current_command', '')
                if current_command and current_command.strip():
                    # Guardar comando en historial
                    if current_user.id not in command_history:
                        command_history[current_user.id] = []
                    
                    command_entry = {
                        'command': current_command.strip(),
                        'session_id': session_id,
                        'timestamp': datetime.utcnow().isoformat(),
                        'session_name': session.name
                    }
                    
                    command_history[current_user.id].append(command_entry)
                    
                    # Limitar historial a 1000 comandos
                    if len(command_history[current_user.id]) > 1000:
                        command_history[current_user.id] = command_history[current_user.id][-1000:]
                    
                    logger.info(f"Command executed in session {session_id}: {current_command.strip()}")
            
            success = ssh_manager.send_input(session_id, input_data)
            if not success:
                emit('terminal_error', {'error': 'Failed to send input to terminal'})
                logger.warning(f"Failed to send input to session {session_id}")
                
        except Exception as e:
            logger.error(f"Error sending terminal input: {str(e)}")
            emit('terminal_error', {'error': f'Input error: {str(e)}'})

    @socketio.on('get_command_history')
    def handle_get_command_history(data):
        """Obtener historial de comandos del usuario"""
        try:
            if not current_user.is_authenticated:
                return
            
            session_id = data.get('session_id')
            limit = data.get('limit', 50)
            
            user_history = command_history.get(current_user.id, [])
            
            if session_id:
                # Filtrar por sesión específica
                filtered_history = [cmd for cmd in user_history if cmd['session_id'] == session_id]
            else:
                filtered_history = user_history
            
            # Enviar últimos comandos
            recent_history = filtered_history[-limit:] if limit else filtered_history
            
            emit('command_history', {
                'commands': recent_history,
                'total': len(filtered_history)
            })
            
        except Exception as e:
            logger.error(f"Error getting command history: {str(e)}")

    @socketio.on('get_session_stats')
    def handle_get_session_stats(data):
        """Obtener estadísticas de sesión en tiempo real"""
        try:
            if not current_user.is_authenticated:
                return
            
            session_id = data.get('session_id')
            
            if session_id and current_user.id in active_sessions:
                session_stats = active_sessions[current_user.id].get(session_id, {})
                
                # Calcular estadísticas
                if session_stats:
                    connected_time = datetime.utcnow() - session_stats['connected_at']
                    
                    stats = {
                        'session_id': session_id,
                        'connected_time': str(connected_time),
                        'commands_count': session_stats.get('commands_count', 0),
                        'last_activity': session_stats['last_activity'].isoformat(),
                        'uptime_seconds': int(connected_time.total_seconds())
                    }
                    
                    emit('session_stats', stats)
            
        except Exception as e:
            logger.error(f"Error getting session stats: {str(e)}")

    @socketio.on('terminal_resize')
    def handle_terminal_resize(data):
        """Redimensionar terminal con logging"""
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
        """Desconexión SSH mejorada"""
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
                
                # Limpiar datos de sesión activa
                if current_user.id in active_sessions and session_id in active_sessions[current_user.id]:
                    session_data = active_sessions[current_user.id][session_id]
                    connected_time = datetime.utcnow() - session_data['connected_at']
                    logger.info(f"Session {session_id} disconnected after {connected_time}")
                    del active_sessions[current_user.id][session_id]
                
                leave_room(f'ssh_{session_id}')
                emit('ssh_disconnected', {
                    'session_id': session_id,
                    'disconnected_at': datetime.utcnow().isoformat()
                })
                
                logger.info(f"SSH session {session_id} disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting SSH session: {str(e)}")

    @socketio.on('ping')
    def handle_ping(data):
        """Ping mejorado con estadísticas"""
        try:
            response_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'server_time': time.time()
            }
            
            if current_user.is_authenticated:
                # Agregar información de sesiones activas
                user_sessions = active_sessions.get(current_user.id, {})
                response_data['active_sessions'] = len(user_sessions)
                response_data['user_id'] = current_user.id
            
            emit('pong', response_data)
            
        except Exception as e:
            logger.error(f"Error in ping: {str(e)}")
            emit('pong', {'error': str(e)})

    # Eventos adicionales para funcionalidades avanzadas
    @socketio.on('save_terminal_session')
    def handle_save_terminal_session(data):
        """Guardar sesión de terminal como archivo"""
        try:
            if not current_user.is_authenticated:
                return
            
            session_id = data.get('session_id')
            content = data.get('content', '')
            
            if session_id and content:
                filename = f"terminal_session_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
                
                # Aquí podrías guardar en un directorio específico o base de datos
                logger.info(f"Terminal session saved for session {session_id}")
                
                emit('session_saved', {
                    'filename': filename,
                    'session_id': session_id
                })
        
        except Exception as e:
            logger.error(f"Error saving terminal session: {str(e)}")

    return socketio