import paramiko
import threading
from datetime import datetime
import logging
import select
import socket
import time

logger = logging.getLogger(__name__)

class SSHManager:
    def __init__(self):
        self.connections = {}
        self.terminals = {}
        self.lock = threading.RLock()
    
    def create_connection(self, session_id, hostname, port, username, password=None, key_path=None):
        try:
            # Cerrar conexión existente si existe
            if session_id in self.connections:
                self.close_connection(session_id)
            
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': hostname,
                'port': port,
                'username': username,
                'timeout': 30,
                'compress': True,
                'allow_agent': False,
                'look_for_keys': False
            }
            
            if key_path:
                connect_kwargs['key_filename'] = key_path
            elif password:
                connect_kwargs['password'] = password
            
            logger.info(f"Conectando SSH a {hostname}:{port} como {username}")
            client.connect(**connect_kwargs)
            
            # Test de conexión más robusto
            try:
                transport = client.get_transport()
                if transport is None or not transport.is_active():
                    raise Exception("Transport not active")
                
                # Test simple
                stdin, stdout, stderr = client.exec_command('echo "SSH_TEST_OK"', timeout=10)
                result = stdout.read().decode().strip()
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    raise Exception(f"Test command failed with exit status {exit_status}")
                
                logger.info(f"SSH test successful: {result}")
                
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
                
                # Cerrar terminal existente si existe
                if session_id in self.terminals:
                    self._close_terminal(session_id)
                
                # Crear canal para el terminal
                channel = client.invoke_shell()
                channel.settimeout(None)  # Usar modo bloqueante para mejor estabilidad
                
                # Configurar tamaño del terminal
                channel.resize_pty(width=cols, height=rows)
                
                # Configuraciones adicionales del terminal
                channel.setblocking(0)  # No bloqueante para lectura
                
                # Guardar información del terminal
                terminal_info = {
                    'channel': channel,
                    'cols': cols,
                    'rows': rows,
                    'active': True,
                    'socketio': socketio,
                    'output_thread': None,
                    'last_activity': datetime.now()
                }
                
                self.terminals[session_id] = terminal_info
                
                # Iniciar hilo para leer salida del terminal
                if socketio:
                    output_thread = threading.Thread(
                        target=self._read_terminal_output,
                        args=(session_id,),
                        daemon=True,
                        name=f"SSH_Output_{session_id}"
                    )
                    terminal_info['output_thread'] = output_thread
                    output_thread.start()
                
                logger.info(f"Terminal created for session {session_id} ({cols}x{rows})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create terminal for session {session_id}: {str(e)}")
            return False
    
    def _read_terminal_output(self, session_id):
        """Lee la salida del terminal y la envía via socketio - VERSIÓN MEJORADA"""
        logger.info(f"Starting output thread for session {session_id}")
        
        try:
            buffer = b''
            last_send_time = time.time()
            
            while True:
                try:
                    with self.lock:
                        if session_id not in self.terminals or not self.terminals[session_id]['active']:
                            logger.info(f"Terminal {session_id} no longer active, stopping output thread")
                            break
                        
                        terminal = self.terminals[session_id]
                        channel = terminal['channel']
                        socketio = terminal['socketio']
                    
                    if channel.closed:
                        logger.info(f"Channel closed for session {session_id}")
                        break
                    
                    # Leer datos disponibles
                    ready_to_read = select.select([channel], [], [], 0.1)[0]
                    
                    if ready_to_read:
                        try:
                            chunk = channel.recv(4096)
                            if not chunk:
                                logger.info(f"Received empty chunk, connection likely closed for session {session_id}")
                                break
                            
                            buffer += chunk
                            current_time = time.time()
                            
                            # Enviar datos inmediatamente o después de un pequeño delay para agrupar
                            if len(buffer) > 1024 or (current_time - last_send_time) > 0.05:
                                self._send_buffered_output(session_id, buffer, socketio)
                                buffer = b''
                                last_send_time = current_time
                                
                        except socket.timeout:
                            continue
                        except Exception as e:
                            if 'Socket is closed' in str(e) or 'Connection reset' in str(e):
                                logger.info(f"Socket closed for session {session_id}")
                                break
                            logger.error(f"Error reading from channel: {str(e)}")
                            continue
                    
                    # Enviar buffer restante si ha pasado tiempo
                    if buffer and (time.time() - last_send_time) > 0.1:
                        self._send_buffered_output(session_id, buffer, socketio)
                        buffer = b''
                        last_send_time = time.time()
                    
                    # Verificar errores en stderr
                    if channel.recv_stderr_ready():
                        try:
                            error_data = channel.recv_stderr(1024)
                            if error_data:
                                self._send_buffered_output(session_id, error_data, socketio, is_stderr=True)
                        except:
                            pass
                            
                except Exception as e:
                    logger.error(f"Error in output loop for session {session_id}: {str(e)}")
                    time.sleep(0.1)
                    continue
                    
        except Exception as e:
            logger.error(f"Fatal error in terminal output thread for session {session_id}: {str(e)}")
        finally:
            # Enviar buffer final si existe
            if buffer:
                try:
                    with self.lock:
                        if session_id in self.terminals:
                            socketio = self.terminals[session_id]['socketio']
                            self._send_buffered_output(session_id, buffer, socketio)
                except:
                    pass
            
            # Limpiar cuando termine
            logger.info(f"Output thread ending for session {session_id}")
            self._notify_terminal_disconnected(session_id)
    
    def _send_buffered_output(self, session_id, buffer, socketio, is_stderr=False):
        """Envía datos del buffer via socketio con manejo mejorado de encoding"""
        try:
            if not buffer:
                return
            
            # Intentar decodificar como UTF-8
            try:
                output = buffer.decode('utf-8')
            except UnicodeDecodeError:
                # Si falla, usar latin1 que siempre funciona y luego convertir caracteres problemáticos
                output = buffer.decode('latin1')
                # Reemplazar caracteres no imprimibles problemáticos
                output = ''.join(char if ord(char) < 127 or char.isprintable() else '?' for char in output)
            
            if output:
                event_data = {
                    'session_id': session_id,
                    'data': output
                }
                
                if is_stderr:
                    event_data['type'] = 'stderr'
                
                socketio.emit('terminal_output', event_data, room=f'ssh_{session_id}')
                
                # Actualizar última actividad
                with self.lock:
                    if session_id in self.terminals:
                        self.terminals[session_id]['last_activity'] = datetime.now()
                
        except Exception as e:
            logger.error(f"Error sending output for session {session_id}: {str(e)}")
    
    def _notify_terminal_disconnected(self, session_id):
        """Notifica que el terminal se ha desconectado"""
        try:
            with self.lock:
                if session_id in self.terminals and self.terminals[session_id]['socketio']:
                    socketio = self.terminals[session_id]['socketio']
                    socketio.emit('ssh_disconnected', {
                        'session_id': session_id,
                        'reason': 'Terminal disconnected'
                    }, room=f'ssh_{session_id}')
        except Exception as e:
            logger.error(f"Error notifying disconnection for session {session_id}: {str(e)}")
        
    def get_connection(self, session_id):
        with self.lock:
            if session_id in self.connections:
                return self.connections[session_id]['client']
            return None
    
    def send_input(self, session_id, data):
        """Envía entrada al terminal - VERSIÓN MEJORADA"""
        try:
            with self.lock:
                if session_id not in self.terminals:
                    logger.warning(f"No terminal found for session {session_id}")
                    return False
                
                terminal = self.terminals[session_id]
                
                if not terminal['active']:
                    logger.warning(f"Terminal not active for session {session_id}")
                    return False
                
                channel = terminal['channel']
                
                if channel.closed:
                    logger.warning(f"Channel closed for session {session_id}")
                    return False
            
            # Enviar datos (fuera del lock para evitar bloqueos)
            try:
                if isinstance(data, str):
                    data_bytes = data.encode('utf-8')
                else:
                    data_bytes = data
                
                bytes_sent = channel.send(data_bytes)
                
                if bytes_sent > 0:
                    # Actualizar última actividad
                    with self.lock:
                        if session_id in self.connections:
                            self.connections[session_id]['last_activity'] = datetime.now()
                        if session_id in self.terminals:
                            self.terminals[session_id]['last_activity'] = datetime.now()
                    
                    logger.debug(f"Sent {bytes_sent} bytes to session {session_id}: {repr(data[:50])}")
                    return True
                else:
                    logger.warning(f"No bytes sent to session {session_id}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error sending data to channel: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending input to terminal {session_id}: {str(e)}")
            return False
    
    def resize_terminal(self, session_id, cols, rows):
        """Redimensiona el terminal"""
        try:
            with self.lock:
                if session_id in self.terminals:
                    terminal = self.terminals[session_id]
                    channel = terminal['channel']
                    
                    if not channel.closed:
                        channel.resize_pty(width=cols, height=rows)
                        terminal['cols'] = cols
                        terminal['rows'] = rows
                        logger.info(f"Terminal {session_id} resized to {cols}x{rows}")
                        return True
                    else:
                        logger.warning(f"Cannot resize closed channel for session {session_id}")
                        return False
                else:
                    logger.warning(f"No terminal found for resize: {session_id}")
                    return False
        except Exception as e:
            logger.error(f"Error resizing terminal {session_id}: {str(e)}")
            return False
    
    def _close_terminal(self, session_id):
        """Cierra solo el terminal sin tocar la conexión SSH"""
        try:
            if session_id in self.terminals:
                terminal = self.terminals[session_id]
                terminal['active'] = False
                
                if terminal['channel'] and not terminal['channel'].closed:
                    terminal['channel'].close()
                
                # Esperar a que termine el hilo
                if terminal.get('output_thread') and terminal['output_thread'].is_alive():
                    terminal['output_thread'].join(timeout=1)
                
                del self.terminals[session_id]
                logger.info(f"Terminal closed for session {session_id}")
        except Exception as e:
            logger.error(f"Error closing terminal {session_id}: {str(e)}")
    
    def close_connection(self, session_id):
        """Cierra la conexión SSH y el terminal"""
        logger.info(f"Closing connection for session {session_id}")
        
        with self.lock:
            # Cerrar terminal primero
            if session_id in self.terminals:
                try:
                    terminal = self.terminals[session_id]
                    terminal['active'] = False
                    
                    if terminal['channel'] and not terminal['channel'].closed:
                        terminal['channel'].close()
                except Exception as e:
                    logger.error(f"Error closing terminal {session_id}: {str(e)}")
            
            # Cerrar conexión
            if session_id in self.connections:
                try:
                    self.connections[session_id]['client'].close()
                    del self.connections[session_id]
                except Exception as e:
                    logger.error(f"Error closing connection {session_id}: {str(e)}")
            
            # Limpiar terminal
            if session_id in self.terminals:
                del self.terminals[session_id]
        
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
                    'channel_open': not terminal['channel'].closed if terminal['channel'] else False,
                    'last_activity': terminal['last_activity'].isoformat() if terminal.get('last_activity') else None
                }
            return None
    
    def list_active_sessions(self):
        """Lista las sesiones activas"""
        with self.lock:
            return {
                'connections': list(self.connections.keys()),
                'terminals': list(self.terminals.keys())
            }