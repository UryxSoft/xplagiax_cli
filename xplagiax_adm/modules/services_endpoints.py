# services_monitor.py
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from utils.connections import db
from models.model import Service, ServiceLog, ServiceStats
from utils.encryption import EncryptionManager
import socket
import requests
import redis
import pymysql
import pika
import time
import logging
from datetime import datetime, date
import concurrent.futures
import threading
import json

services_bp = Blueprint('services_bp', __name__)
logger = logging.getLogger(__name__)

# Inicializar el manager de encriptación
encryption_manager = EncryptionManager()

def get_services_config():
    """Obtener configuración de servicios desde la base de datos"""
    services = Service.query.filter_by(is_active=True, is_monitored=True).all()
    
    config = {}
    for service in services:
        service_config = service.to_config_dict()
        
        # Desencriptar password si existe
        if service.password_encrypted and hasattr(encryption_manager, 'decrypt'):
            try:
                service_config['password'] = encryption_manager.decrypt(service.password_encrypted)
            except Exception as e:
                logger.error(f"Error decrypting password for service {service.name}: {e}")
                service_config['password'] = ''
        
        config[service.name] = service_config
    
    return config

def log_service_check(service_id, status, response_time=None, error_message=None, additional_data=None):
    """Registrar resultado de verificación de servicio"""
    try:
        log_entry = ServiceLog(
            service_id=service_id,
            status=status,
            response_time=response_time,
            error_message=error_message
        )
        
        if additional_data:
            log_entry.set_additional_data(additional_data)
        
        db.session.add(log_entry)
        
        # Actualizar estadísticas diarias
        update_service_stats(service_id, status, response_time)
        
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging service check: {e}")
        db.session.rollback()

def update_service_stats(service_id, status, response_time):
    """Actualizar estadísticas diarias del servicio"""
    try:
        today = date.today()
        
        # Buscar o crear estadística del día
        stats = ServiceStats.query.filter_by(service_id=service_id, date=today).first()
        if not stats:
            stats = ServiceStats(service_id=service_id, date=today)
            db.session.add(stats)
        
        # Actualizar contadores
        stats.total_checks += 1
        if status:
            stats.successful_checks += 1
        else:
            stats.failed_checks += 1
        
        # Actualizar tiempos de respuesta
        if response_time is not None and status:
            if stats.avg_response_time is None:
                stats.avg_response_time = response_time
                stats.min_response_time = response_time
                stats.max_response_time = response_time
            else:
                # Calcular nueva media
                total_successful = stats.successful_checks
                if total_successful > 1:
                    stats.avg_response_time = ((stats.avg_response_time * (total_successful - 1)) + response_time) / total_successful
                
                stats.min_response_time = min(stats.min_response_time or response_time, response_time)
                stats.max_response_time = max(stats.max_response_time or response_time, response_time)
        
        stats.updated_at = datetime.utcnow()
        
    except Exception as e:
        logger.error(f"Error updating service stats: {e}")

def check_socket_connection(host, port, timeout=5):
    """Verificar conexión socket básica"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.error(f"Socket connection error for {host}:{port} - {e}")
        return False

def check_http_service(host, port, endpoint='/', timeout=5, use_https=False):
    """Verificar servicio HTTP"""
    try:
        protocol = 'https' if use_https else 'http'
        url = f"{protocol}://{host}:{port}{endpoint}"
        
        response = requests.get(url, timeout=timeout, verify=False)
        return {
            'status': response.status_code < 400,
            'status_code': response.status_code,
            'response_time': response.elapsed.total_seconds()
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP check error for {host}:{port}{endpoint} - {e}")
        return {
            'status': False,
            'error': str(e),
            'response_time': None
        }

def check_redis_service(host, port, timeout=5):
    """Verificar servicio Redis"""
    try:
        r = redis.Redis(host=host, port=port, socket_timeout=timeout, socket_connect_timeout=timeout)
        response = r.ping()
        info = r.info()
        
        return {
            'status': response,
            'version': info.get('redis_version', 'Unknown'),
            'uptime': info.get('uptime_in_seconds', 0),
            'connected_clients': info.get('connected_clients', 0),
            'used_memory': info.get('used_memory_human', 'Unknown')
        }
    except Exception as e:
        logger.error(f"Redis check error for {host}:{port} - {e}")
        return {'status': False, 'error': str(e)}

def check_mysql_service(host, port, user='root', password='', timeout=5):
    """Verificar servicio MySQL"""
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=timeout,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SHOW STATUS LIKE 'Uptime'")
            uptime = cursor.fetchone()[1]
            
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            connections = cursor.fetchone()[1]
        
        connection.close()
        
        return {
            'status': True,
            'version': version,
            'uptime': int(uptime),
            'connections': int(connections)
        }
    except Exception as e:
        logger.error(f"MySQL check error for {host}:{port} - {e}")
        return {'status': False, 'error': str(e)}

def check_rabbitmq_service(host, port, timeout=5):
    """Verificar servicio RabbitMQ"""
    try:
        # Intentar conexión AMQP
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=host, 
                port=port,
                socket_timeout=timeout,
                blocked_connection_timeout=timeout
            )
        )
        connection.close()
        
        # Intentar obtener info del management API
        try:
            mgmt_url = f"http://{host}:15672/api/overview"
            response = requests.get(mgmt_url, timeout=timeout, auth=('guest', 'guest'))
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': True,
                    'version': data.get('rabbitmq_version', 'Unknown'),
                    'erlang_version': data.get('erlang_version', 'Unknown'),
                    'management_version': data.get('management_version', 'Unknown')
                }
        except:
            pass
            
        return {'status': True}
        
    except Exception as e:
        logger.error(f"RabbitMQ check error for {host}:{port} - {e}")
        return {'status': False, 'error': str(e)}

def check_single_service(service_name, config, service_obj=None):
    """Verificar un servicio individual"""
    start_time = time.time()
    
    try:
        if config['type'] == 'http':
            result = check_http_service(
                config['host'], 
                config['port'], 
                config.get('endpoint', '/'),
                config['timeout']
            )
        elif config['type'] == 'socket':
            result = {
                'status': check_socket_connection(
                    config['host'], 
                    config['port'], 
                    config['timeout']
                )
            }
        elif config['type'] == 'redis':
            result = check_redis_service(
                config['host'], 
                config['port'], 
                config['timeout']
            )
        elif config['type'] == 'mysql':
            result = check_mysql_service(
                config['host'], 
                config['port'],
                config.get('user', 'root'),
                config.get('password', ''),
                config['timeout']
            )
        elif config['type'] == 'rabbitmq':
            result = check_rabbitmq_service(
                config['host'], 
                config['port'], 
                config['timeout']
            )
        else:
            result = {'status': False, 'error': 'Unknown service type'}
            
        # Calcular tiempo de respuesta si no se proporcionó
        if 'response_time' not in result:
            result['response_time'] = time.time() - start_time
            
        # Añadir información común
        result.update({
            'service_name': service_name,
            'display_name': config['name'],
            'host': config['host'],
            'port': config['port'],
            'icon': config['icon'],
            'checked_at': datetime.utcnow().isoformat()
        })
        
        # Registrar en base de datos si tenemos el objeto service
        if service_obj:
            additional_data = {}
            for key in ['version', 'uptime', 'used_memory', 'connected_clients', 'connections']:
                if key in result:
                    additional_data[key] = result[key]
            
            log_service_check(
                service_obj.id,
                result['status'],
                result.get('response_time'),
                result.get('error'),
                additional_data if additional_data else None
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Service check error for {service_name} - {e}")
        
        error_result = {
            'service_name': service_name,
            'display_name': config['name'],
            'host': config['host'],
            'port': config['port'],
            'icon': config['icon'],
            'status': False,
            'error': str(e),
            'checked_at': datetime.utcnow().isoformat(),
            'response_time': time.time() - start_time
        }
        
        # Registrar error en base de datos
        if service_obj:
            log_service_check(
                service_obj.id,
                False,
                time.time() - start_time,
                str(e)
            )
        
        return error_result

@services_bp.route('/api/status', methods=['GET'])
@login_required
def get_services_status():
    """Endpoint para obtener el estado de todos los servicios"""
    start_time = time.time()
    results = {}
    
    try:
        # Obtener servicios desde la base de datos
        services_config = get_services_config()
        services_objects = {s.name: s for s in Service.query.filter_by(is_active=True, is_monitored=True).all()}
        
        if not services_config:
            return jsonify({
                'success': False,
                'error': 'No services configured',
                'services': {},
                'summary': {
                    'total_services': 0,
                    'active_services': 0,
                    'inactive_services': 0,
                    'health_percentage': 0
                }
            })
        
        # Verificar servicios en paralelo para mejor rendimiento
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(services_config)) as executor:
            future_to_service = {
                executor.submit(
                    check_single_service, 
                    service_name, 
                    config, 
                    services_objects.get(service_name)
                ): service_name 
                for service_name, config in services_config.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_service):
                service_name = future_to_service[future]
                try:
                    result = future.result()
                    results[service_name] = result
                except Exception as e:
                    logger.error(f"Exception checking {service_name}: {e}")
                    results[service_name] = {
                        'service_name': service_name,
                        'status': False,
                        'error': str(e),
                        'checked_at': datetime.utcnow().isoformat()
                    }
        
        # Calcular estadísticas generales
        total_services = len(results)
        active_services = sum(1 for result in results.values() if result.get('status', False))
        
        return jsonify({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'total_check_time': time.time() - start_time,
            'summary': {
                'total_services': total_services,
                'active_services': active_services,
                'inactive_services': total_services - active_services,
                'health_percentage': (active_services / total_services * 100) if total_services > 0 else 0
            },
            'services': results
        })
        
    except Exception as e:
        logger.error(f"Error getting services status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@services_bp.route('/api/status/<service_name>', methods=['GET'])
@login_required
def get_single_service_status(service_name):
    """Endpoint para obtener el estado de un servicio específico"""
    try:
        # Buscar servicio en la base de datos
        service_obj = Service.query.filter_by(name=service_name, is_active=True, is_monitored=True).first()
        if not service_obj:
            return jsonify({'success': False, 'error': 'Service not found'}), 404
        
        config = service_obj.to_config_dict()
        
        # Desencriptar password si existe
        if service_obj.password_encrypted and hasattr(encryption_manager, 'decrypt'):
            try:
                config['password'] = encryption_manager.decrypt(service_obj.password_encrypted)
            except Exception as e:
                logger.error(f"Error decrypting password for service {service_name}: {e}")
                config['password'] = ''
        
        result = check_single_service(service_name, config, service_obj)
        
        return jsonify({
            'success': True,
            'service': result
        })
        
    except Exception as e:
        logger.error(f"Error getting single service status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@services_bp.route('/config', methods=['GET'])
@login_required
def get_services_config_endpoint():
    """Endpoint para obtener la configuración de servicios (sin credenciales)"""
    try:
        services = Service.query.filter_by(is_active=True).all()
        
        safe_config = {}
        for service in services:
            safe_config[service.name] = {
                'id': service.id,
                'name': service.display_name,
                'host': service.host,
                'port': service.port,
                'type': service.service_type,
                'icon': service.icon,
                'is_monitored': service.is_monitored,
                'endpoint': service.endpoint,
                'timeout': service.timeout
            }
        
        return jsonify({
            'success': True,
            'services': safe_config
        })
        
    except Exception as e:
        logger.error(f"Error getting services config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@services_bp.route('/config', methods=['POST'])
@login_required
def create_service():
    """Crear un nuevo servicio"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['name', 'display_name', 'host', 'port', 'service_type']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Verificar que no exista un servicio con el mismo nombre
        existing_service = Service.query.filter_by(name=data['name']).first()
        if existing_service:
            return jsonify({'success': False, 'error': 'Service with this name already exists'}), 400
        
        # Encriptar password si se proporciona
        password_encrypted = None
        if data.get('password') and hasattr(encryption_manager, 'encrypt'):
            password_encrypted = encryption_manager.encrypt(data['password'])
        
        # Crear servicio
        service = Service(
            name=data['name'],
            display_name=data['display_name'],
            host=data['host'],
            port=data['port'],
            service_type=data['service_type'],
            endpoint=data.get('endpoint'),
            timeout=data.get('timeout', 5),
            icon=data.get('icon', 'fas fa-server'),
            username=data.get('username'),
            password_encrypted=password_encrypted,
            is_active=data.get('is_active', True),
            is_monitored=data.get('is_monitored', True),
            created_by=current_user.id
        )
        
        # Configuración extra
        extra_config = data.get('extra_config', {})
        if extra_config:
            service.set_extra_config(extra_config)
        
        db.session.add(service)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Service created successfully',
            'service': service.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating service: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@services_bp.route('/config/<int:service_id>', methods=['PUT'])
@login_required
def update_service(service_id):
    """Actualizar un servicio existente"""
    try:
        service = Service.query.get_or_404(service_id)
        data = request.get_json()
        
        # Actualizar campos permitidos
        allowed_fields = [
            'display_name', 'host', 'port', 'service_type', 'endpoint', 
            'timeout', 'icon', 'username', 'is_active', 'is_monitored'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(service, field, data[field])
        
        # Actualizar password si se proporciona
        if 'password' in data and data['password'] and hasattr(encryption_manager, 'encrypt'):
            service.password_encrypted = encryption_manager.encrypt(data['password'])
        
        # Actualizar configuración extra
        if 'extra_config' in data:
            service.set_extra_config(data['extra_config'])
        
        service.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Service updated successfully',
            'service': service.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating service: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@services_bp.route('/config/<int:service_id>', methods=['DELETE'])
@login_required
def delete_service(service_id):
    """Eliminar un servicio"""
    try:
        service = Service.query.get_or_404(service_id)
        
        db.session.delete(service)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Service deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting service: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@services_bp.route('/logs/<int:service_id>', methods=['GET'])
@login_required
def get_service_logs(service_id):
    """Obtener logs de un servicio específico"""
    try:
        service = Service.query.get_or_404(service_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        logs = ServiceLog.query.filter_by(service_id=service_id).order_by(
            ServiceLog.checked_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'service_name': service.name,
            'logs': [log.to_dict() for log in logs.items],
            'total': logs.total,
            'pages': logs.pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"Error getting service logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@services_bp.route('/api/stats/<int:service_id>', methods=['GET'])
@login_required
def get_service_stats(service_id):
    """Obtener estadísticas de un servicio específico"""
    try:
        service = Service.query.get_or_404(service_id)
        
        days = request.args.get('days', 7, type=int)
        
        # Obtener estadísticas de los últimos N días
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        
        stats = ServiceStats.query.filter(
            ServiceStats.service_id == service_id,
            ServiceStats.date >= start_date
        ).order_by(ServiceStats.date.desc()).all()
        
        return jsonify({
            'success': True,
            'service_name': service.name,
            'stats': [stat.to_dict() for stat in stats],
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@services_bp.route('/initialize', methods=['POST'])
@login_required
def initialize_default_services_endpoint():
    """Endpoint para inicializar servicios por defecto (solo admin)"""
    try:
        # Verificar que el usuario sea admin
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        from models import initialize_default_services
        initialize_default_services()
        
        return jsonify({
            'success': True,
            'message': 'Default services initialized successfully'
        })
        
    except Exception as e:
        logger.error(f"Error initializing default services: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Añadir el blueprint a tu app principal
# En app.py agregar: 
# from services_monitor import services_bp
# app.register_blueprint(services_bp, url_prefix='/api/services')

# También añadir la ruta para el panel:
# @app.route('/services')
# @login_required
# def services_monitor():
#     return render_template('services_monitor.html')