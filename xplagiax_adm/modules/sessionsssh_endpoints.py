from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from utils.connections import db
from models.model import SSHSession
from utils.encryption import EncryptionManager
import paramiko
import socket
import os
from datetime import datetime

sessionsssh_bp = Blueprint('sessionsssh_bp', __name__)
encryption_manager = EncryptionManager()

@sessionsssh_bp.route('/')
@login_required
def index():
    return render_template('sessions_list.html')

@sessionsssh_bp.route('/new')
@login_required
def new_session():
    return render_template('new_session.html')

@sessionsssh_bp.route('/api/sessions', methods=['GET'])
@login_required
def get_sessions():
    sessions = SSHSession.query.filter_by(user_id=current_user.id).all()
    return jsonify([session.to_dict() for session in sessions])

@sessionsssh_bp.route('/api/sessions', methods=['POST'])
@login_required
def create_session():
    data = request.get_json()
    
    required_fields = ['name', 'hostname', 'username']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    password_encrypted = None
    if data.get('password'):
        password_encrypted = encryption_manager.encrypt(data['password'])
    
    session = SSHSession(
        user_id=current_user.id,
        name=data['name'],
        hostname=data['hostname'],
        port=data.get('port', 22),
        username=data['username'],
        auth_type=data.get('auth_type', 'password'),
        password_encrypted=password_encrypted,
        key_path=data.get('key_path')
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify({'id': session.id, 'message': 'Session created'}), 201

@sessionsssh_bp.route('/api/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def delete_session(session_id):
    session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    from xplagiax_adm.utils.ssh_manager1 import SSHManager
    ssh_manager = SSHManager()
    ssh_manager.close_connection(session_id)
    db.session.delete(session)
    db.session.commit()
    return jsonify({'message': 'Session deleted'})

@sessionsssh_bp.route('/api/test_connection', methods=['POST'])
@login_required
def test_connection():
    data = request.get_json()
    
    required_fields = ['hostname', 'username']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    hostname = data['hostname']
    port = data.get('port', 22)
    username = data['username']
    auth_type = data.get('auth_type', 'password')
    password = data.get('password')
    key_path = data.get('key_path')
    
    try:
        # Crear cliente SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Configurar autenticación
        if auth_type == 'password':
            if not password:
                return jsonify({'success': False, 'message': 'Password is required for password authentication'}), 400
            
            ssh_client.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=10
            )
        else:  # key authentication
            if not key_path:
                return jsonify({'success': False, 'message': 'Key path is required for key authentication'}), 400
            
            if not os.path.exists(key_path):
                return jsonify({'success': False, 'message': f'Key file not found: {key_path}'}), 400
            
            ssh_client.connect(
                hostname=hostname,
                port=port,
                username=username,
                key_filename=key_path,
                timeout=10
            )
        
        # Ejecutar comando de prueba
        stdin, stdout, stderr = ssh_client.exec_command('whoami')
        result = stdout.read().decode().strip()
        
        # Cerrar conexión
        ssh_client.close()
        
        return jsonify({
            'success': True, 
            'message': f'Connection successful! Connected as: {result}',
            'username': result
        })
        
    except paramiko.AuthenticationException:
        return jsonify({'success': False, 'message': 'Authentication failed. Please check your credentials.'}), 401
    except paramiko.SSHException as e:
        return jsonify({'success': False, 'message': f'SSH connection error: {str(e)}'}), 500
    except socket.timeout:
        return jsonify({'success': False, 'message': 'Connection timeout. Please check the hostname and port.'}), 408
    except socket.gaierror:
        return jsonify({'success': False, 'message': 'Hostname resolution failed. Please check the hostname.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'Connection error: {str(e)}'}), 500

@sessionsssh_bp.route('/api/sessions/<int:session_id>/connect', methods=['POST'])
@login_required
def connect_session(session_id):
    session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    
    # Actualizar última actividad
    session.last_used_at = datetime.utcnow()
    session.is_active = True
    session.connected_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Session connected', 'terminal_url': f'/sessionsssh_bp/terminal/{session_id}'})

@sessionsssh_bp.route('/api/sessions/<int:session_id>/disconnect', methods=['POST'])
@login_required  # Descomentar este decorador
def disconnect_session(session_id):
    session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    
    try:
        # Importar SSHManager al inicio del archivo
        from xplagiax_adm.utils.ssh_manager1 import SSHManager
        ssh_manager = SSHManager()
        ssh_manager.close_connection(session_id)
        
        session.is_active = False
        session.last_used_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Session disconnected successfully'})
    except Exception as e:
        session.is_active = False
        session.last_used_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': False, 'message': f'Error disconnecting session: {str(e)}'}), 500

@sessionsssh_bp.route('/terminal/<int:session_id>')
@login_required
def terminal(session_id):
    session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    return render_template('/terminal/terminal_html_fixed1.html', session=session)