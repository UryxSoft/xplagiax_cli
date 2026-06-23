import paramiko
import threading
from datetime import datetime
import logging
import select
import socket

logger = logging.getLogger(__name__)

class SSHManager:
    def __init__(self):
        self.connections = {}
        self.terminals = {}
        self.lock = threading.RLock()
    
    def create_connection(self, session_id, hostname, port, username, password=None, key_path=None):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': hostname,
                'port': port,
                'username': username,
                'timeout': 30,
                'compress': True,  # Mejorar rendimiento
                'allow_agent': False,  # Evitar problemas de autenticación
                'look_for_keys': False  # Evitar búsqueda automática de claves
            }
            
            if key_path:
                connect_kwargs['key_filename'] = key_path
            elif password:
                connect_kwargs['password'] = password
            
            client.connect(**connect_kwargs)
            
            # Test de conexión más robusto
            try:
                transport = client.get_transport()
                if transport is None or not transport.is_active():
                    raise Exception("Transport not active")
                
                # Test simple sin dependencia de output específico
                stdin, stdout, stderr = client.exec_command('echo test', timeout=5)
                stdout.channel.recv_exit_status()  # Esperar que termine
                
            except Exception as e:
                client.close()
                raise Exception(f"Connection test failed: {str(e)}")
            
            with self.lock:
                self.connections[session_id] = {
                    'client': client,
                    'hostname': hostname,
                    'port': port,
                    'username': username,
                    'connected_at': datetime.now(),
                    'last_activity': datetime.now()
                }
            
            logger.info(f"SSH connection established for session {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"SSH connection failed for session {session_id}: {str(e)}")
            return None
        
    def create_terminal(self, session_id, cols=80, rows=24, socketio=None):
        """Crea un terminal interactivo para la sesión SSH"""
        try:
            with self.lock:
                if session_id not in self.connections:
                    logger.error(f"No SSH connection found for session {session_id}")
                    return False
                
                client = self.connections[session_id]['client']
                
                # Crear canal para el terminal
                channel = client.invoke_shell()
                channel.settimeout(0.1)  # Timeout no bloqueante
                
                # Configurar tamaño del terminal
                channel.resize_pty(width=cols, height=rows)
                
                # Guardar información del terminal
                self.terminals[session_id] = {
                    'channel': channel,
                    'cols': cols,
                    'rows': rows,
                    'active': True,
                    'socketio': socketio
                }
                
                # Iniciar hilo para leer salida del terminal
                if socketio:
                    output_thread = threading.Thread(
                        target=self._read_terminal_output,
                        args=(session_id, channel, socketio),
                        daemon=True
                    )
                    output_thread.start()
                
                logger.info(f"Terminal created for session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create terminal for session {session_id}: {str(e)}")
            return False
    
    def _read_terminal_output(self, session_id, channel, socketio):
        """Lee la salida del terminal y la envía via socketio"""
        try:
            buffer = b''
            while True:
                with self.lock:
                    if session_id not in self.terminals or not self.terminals[session_id]['active']:
                        break
                
                try:
                    # Usar select para evitar bloqueo
                    ready, _, _ = select.select([channel], [], [], 0.1)
                    
                    if ready:
                        chunk = channel.recv(4096)
                        if not chunk:
                            break
                        
                        buffer += chunk
                        
                        # Procesar buffer completo
                        try:
                            output = buffer.decode('utf-8')
                            buffer = b''
                        except UnicodeDecodeError:
                            # Esperar más datos para completar el carácter
                            if len(buffer) > 10:  # Evitar buffer infinito
                                output = buffer.decode('utf-8', errors='replace')
                                buffer = b''
                            else:
                                continue
                        
                        if output:
                            socketio.emit('terminal_output', {
                                'session_id': session_id,
                                'data': output
                            }, room=f'ssh_{session_id}')
                    
                    # Verificar errores
                    if channel.recv_stderr_ready():
                        error_data = channel.recv_stderr(1024)
                        if error_data:
                            error_output = error_data.decode('utf-8', errors='replace')
                            socketio.emit('terminal_output', {
                                'session_id': session_id,
                                'data': error_output
                            }, room=f'ssh_{session_id}')
                    
                    # Verificar si el canal sigue abierto
                    if channel.closed:
                        break
                        
                except Exception as e:
                    if 'Socket is closed' in str(e) or 'Connection reset' in str(e):
                        break
                    logger.error(f"Error reading terminal output: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Terminal output thread error: {str(e)}")
        finally:
            # Limpiar cuando termine
            with self.lock:
                if session_id in self.terminals:
                    self.terminals[session_id]['active'] = False
            
            socketio.emit('terminal_disconnected', {
                'session_id': session_id
            }, room=f'ssh_{session_id}')
            
        
    def get_connection(self, session_id):
        with self.lock:
            if session_id in self.connections:
                return self.connections[session_id]['client']
            return None
    
    def send_input(self, session_id, data):
        """Envía entrada al terminal"""
        try:
            with self.lock:
                if session_id not in self.terminals:
                    logger.warning(f"No terminal found for session {session_id}")
                    return False
                
                terminal = self.terminals[session_id]
                channel = terminal['channel']
                
                if channel.closed:
                    logger.warning(f"Channel closed for session {session_id}")
                    return False
                
                # Enviar datos
                bytes_sent = channel.send(data.encode('utf-8'))
                
                # Actualizar última actividad
                if session_id in self.connections:
                    self.connections[session_id]['last_activity'] = datetime.now()
                
                return bytes_sent > 0
                
        except Exception as e:
            logger.error(f"Error sending input to terminal {session_id}: {str(e)}")
            return False
    
    def resize_terminal(self, session_id, cols, rows):
        """Redimensiona el terminal"""
        try:
            with self.lock:
                if session_id in self.terminals:
                    terminal = self.terminals[session_id]
                    terminal['channel'].resize_pty(width=cols, height=rows)
                    terminal['cols'] = cols
                    terminal['rows'] = rows
                    return True
                return False
        except Exception as e:
            logger.error(f"Error resizing terminal {session_id}: {str(e)}")
            return False
    
    def close_connection(self, session_id):
        """Cierra la conexión SSH y el terminal"""
        with self.lock:
            # Cerrar terminal
            if session_id in self.terminals:
                try:
                    self.terminals[session_id]['active'] = False
                    self.terminals[session_id]['channel'].close()
                except Exception as e:
                    logger.error(f"Error closing terminal {session_id}: {str(e)}")
                del self.terminals[session_id]
            
            # Cerrar conexión
            if session_id in self.connections:
                try:
                    self.connections[session_id]['client'].close()
                except Exception as e:
                    logger.error(f"Error closing connection {session_id}: {str(e)}")
                del self.connections[session_id]
        
        logger.info(f"Connection and terminal closed for session {session_id}")
    
    def get_terminal_status(self, session_id):
        """Obtiene el estado del terminal"""
        with self.lock:
            if session_id in self.terminals:
                terminal = self.terminals[session_id]
                return {
                    'active': terminal['active'],
                    'cols': terminal['cols'],
                    'rows': terminal['rows'],
                    'channel_open': not terminal['channel'].closed
                }
            return None
    
    def list_active_sessions(self):
        """Lista las sesiones activas"""
        with self.lock:
            return list(self.connections.keys())