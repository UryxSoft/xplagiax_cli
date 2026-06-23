# services_endpoints_fixed.py
from flask import Blueprint, jsonify, request, current_app
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
from contextlib import contextmanager

services_bp = Blueprint('services_bp', __name__)
logger = logging.getLogger(__name__)

# Inicializar el manager de encriptación
encryption_manager = EncryptionManager()

@contextmanager
def app_context():
    """Context manager para manejar el contexto de aplicación"""
    app = current_app._get_current_object()
    with app.app_context():
        yield

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

def log_service_check_safe(service_id, status, response_time=None, error_message=None, additional_data=None):
    """Registrar resultado de verificación de servicio con manejo seguro del contexto"""
    try:
        with app_context():
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
            update_service_stats_safe(service_id, status, response_time)
            
            db.session.commit()
    except Exception as e:
        logger.error(f"Error logging service check: {e}")
        try:
            db.session.rollback()
        except:
            pass

def update_service_stats_safe(service_id, status, response_time):
    """Actualizar estadísticas diarias del servicio con manejo seguro del contexto"""
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
            'response_time': response.elapsed.total_seconds(),
            'content_length': len(response.content) if response.content else 0
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP check error for {host}:{port}{endpoint} - {e}")
        return {
            'status': False,
            'error': str(e),
            'response_time': None
        }

def check_redis_service(host, port, timeout=5, password=None):
    """Verificar servicio Redis"""
    try:
        r = redis.Redis(
            host=host, 
            port=port, 
            password=password,
            socket_timeout=timeout, 
            socket_connect_timeout=timeout,
            decode_responses=True
        )
        response = r.ping()
        info = r.info()
        
        return {
            'status': response,
            'version': info.get('redis_version', 'Unknown'),
            'uptime': info.get('uptime_in_seconds', 0),
            'connected_clients': info.get('connected_clients', 0),
            'used_memory': info.get('used_memory_human', 'Unknown'),
            'total_commands_processed': info.get('total_commands_processed', 0)
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
            
            cursor.execute("SHOW STATUS LIKE 'Queries'")
            queries = cursor.fetchone()[1]
        
        connection.close()
        
        return {
            'status': True,
            'version': version,
            'uptime': int(uptime),
            'connections': int(connections),
            'total_queries': int(queries)
        }
    except Exception as e:
        logger.error(f"MySQL check error for {host}:{port} - {e}")
        return {'status': False, 'error': str(e)}

def check_rabbitmq_service(host, port, timeout=5, username='guest', password='guest'):
    """Verificar servicio RabbitMQ"""
    try:
        # Intentar conexión AMQP
        credentials = pika.PlainCredentials(username, password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=host, 
                port=port,
                credentials=credentials,
                socket_timeout=timeout,
                blocked_connection_timeout=timeout
            )
        )
        connection.close()
        
        # Intentar obtener info del management API
        try:
            mgmt_url = f"http://{host}:15672/api/overview"
            response = requests.get(mgmt_url, timeout=timeout, auth=(username, password))
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': True,
                    'version': data.get('rabbitmq_version', 'Unknown'),
                    'erlang_version': data.get('erlang_version', 'Unknown'),
                    'management_version': data.get('management_version', 'Unknown'),
                    'node': data.get('node', 'Unknown'),
                    'uptime': data.get('uptime', 0)
                }
        except Exception as api_error:
            logger.debug(f"RabbitMQ Management API not available: {api_error}")
            
        return {'status': True, 'connection_type': 'AMQP Only'}
        
    except Exception as e:
        logger.error(f"RabbitMQ check error for {host}:{port} - {e}")
        return {'status': False, 'error': str(e)}

def check_elasticsearch_service(host, port, timeout=5, use_https=False):
    """Verificar servicio Elasticsearch"""
    try:
        protocol = 'https' if use_https else 'http'
        url = f"{protocol}://{host}:{port}"
        
        # Verificar endpoint principal
        response = requests.get(url, timeout=timeout, verify=False)
        if response.status_code == 200:
            data = response.json()
            
            # Obtener información del cluster
            cluster_url = f"{url}/_cluster/health"
            cluster_response = requests.get(cluster_url, timeout=timeout, verify=False)
            cluster_data = cluster_response.json() if cluster_response.status_code == 200 else {}
            
            return {
                'status': True,
                'version': data.get('version', {}).get('number', 'Unknown'),
                'cluster_name': data.get('cluster_name', 'Unknown'),
                'cluster_status': cluster_data.get('status', 'Unknown'),
                'number_of_nodes': cluster_data.get('number_of_nodes', 0),
                'active_shards': cluster_data.get('active_shards', 0)
            }
        else:
            return {'status': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Elasticsearch check error for {host}:{port} - {e}")
        return {'status': False, 'error': str(e)}

def check_minio_service(host, port, timeout=5, use_https=False):
    """Verificar servicio MinIO"""
    try:
        protocol = 'https' if use_https else 'http'
        url = f"{protocol}://{host}:{port}/minio/health/live"
        
        response = requests.get(url, timeout=timeout, verify=False)
        if response.status_code == 200:
            return {
                'status': True,
                'health_status': 'live',
                'response_time': response.elapsed.total_seconds()
            }
        else:
            # Intentar endpoint alternativo
            alt_url = f"{protocol}://{host}:{port}/minio/health/ready"
            alt_response = requests.get(alt_url, timeout=timeout, verify=False)
            return {
                'status': alt_response.status_code == 200,
                'health_status': 'ready' if alt_response.status_code == 200 else 'unknown',
                'response_time': alt_response.elapsed.total_seconds()
            }
            
    except Exception as e:
        logger.error(f"MinIO check error for {host}:{port} - {e}")
        return {'status': False, 'error': str(e)}

def check_qdrant_service(host, port, timeout=5, use_https=False):
    """Verificar servicio Qdrant"""
    try:
        protocol = 'https' if use_https else 'http'
        url = f"{protocol}://{host}:{port}"
        
        response = requests.get(url, timeout=timeout, verify=False)
        if response.status_code == 200:
            # Intentar obtener información del servicio
            try:
                info_url = f"{url}/telemetry"
                info_response = requests.get(info_url, timeout=timeout, verify=False)
                if info_response.status_code == 200:
                    data = info_response.json()
                    return {
                        'status': True,
                        'version': data.get('version', 'Unknown'),
                        'collections_count': len(data.get('collections', [])),
                        'response_time': response.elapsed.total_seconds()
                    }
            except:
                pass
                
            return {
                'status': True,
                'response_time': response.elapsed.total_seconds()
            }
        else:
            return {'status': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Qdrant check error for {host}:{port} - {e}")
        return {'status': False, 'error': str(e)}

def check_clamav_service(host, port, timeout=5):
    """Verificar servicio ClamAV"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        
        if result == 0:
            # Enviar comando PING
            sock.send(b'PING\n')
            response = sock.recv(1024).decode().strip()
            sock.close()
            
            return {
                'status': response == 'PONG',
                'ping_response': response
            }
        else:
            sock.close()
            return {'status': False, 'error': 'Connection failed'}
            
    except Exception as e:
        logger.error(f"ClamAV check error for {host}:{port} - {e}")
        return {'status': False, 'error': str(e)}

def check_single_service(service_name, config, service_id=None):
    """Verificar un servicio individual"""
    start_time = time.time()
    
    try:
        service_type = config['type']
        
        if service_type == 'http':
            result = check_http_service(
                config['host'], 
                config['port'], 
                config.get('endpoint', '/'),
                config['timeout'],
                config.get('use_https', False)
            )
        elif service_type == 'socket':
            result = {
                'status': check_socket_connection(
                    config['host'], 
                    config['port'], 
                    config['timeout']
                )
            }
        elif service_type == 'redis':
            result = check_redis_service(
                config['host'], 
                config['port'], 
                config['timeout'],
                config.get('password')
            )
        elif service_type == 'mysql':
            result = check_mysql_service(
                config['host'], 
                config['port'],
                config.get('user', 'root'),
                config.get('password', ''),
                config['timeout']
            )
        elif service_type == 'rabbitmq':
            result = check_rabbitmq_service(
                config['host'], 
                config['port'], 
                config['timeout'],
                config.get('username', 'guest'),
                config.get('password', 'guest')
            )
        elif service_type == 'elasticsearch':
            result = check_elasticsearch_service(
                config['host'], 
                config['port'], 
                config['timeout'],
                config.get('use_https', False)
            )
        elif service_type == 'minio':
            result = check_minio_service(
                config['host'], 
                config['port'], 
                config['timeout'],
                config.get('use_https', False)
            )
        elif service_type == 'qdrant':
            result = check_qdrant_service(
                config['host'], 
                config['port'], 
                config['timeout'],
                config.get('use_https', False)
            )
        elif service_type == 'clamav':
            result = check_clamav_service(
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
        
        # Registrar en base de datos si tenemos el service_id
        if service_id:
            additional_data = {}
            for key in ['version', 'uptime', 'used_memory', 'connected_clients', 'connections', 'cluster_status']:
                if key in result:
                    additional_data[key] = result[key]
            
            # Usar threading para no bloquear la respuesta
            def log_async():
                log_service_check_safe(
                    service_id,
                    result['status'],
                    result.get('response_time'),
                    result.get('error'),
                    additional_data if additional_data else None
                )
            
            thread = threading.Thread(target=log_async)
            thread.daemon = True
            thread.start()
        
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
        if service_id:
            def log_error_async():
                log_service_check_safe(
                    service_id,
                    False,
                    time.time() - start_time,
                    str(e)
                )
            
            thread = threading.Thread(target=log_error_async)
            thread.daemon = True
            thread.start()
        
        return error_result

@services_bp.route('/api/status2', methods=['GET'])
@login_required
def get_services_status2():
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
        
        # Función para verificar servicio con manejo de contexto
        def check_service_with_context(service_name, config):
            service_obj = services_objects.get(service_name)
            service_id = service_obj.id if service_obj else None
            return check_single_service(service_name, config, service_id)
        
        # Verificar servicios en paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(services_config), 10)) as executor:
            future_to_service = {
                executor.submit(check_service_with_context, service_name, config): service_name 
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

@services_bp.route('/api/statuss/<service_name>', methods=['GET'])
@login_required
def get_single_service_statuss(service_name):
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
        
        result = check_single_service(service_name, config, service_obj.id)
        
        return jsonify({
            'success': True,
            'service': result
        })
        
    except Exception as e:
        logger.error(f"Error getting single service status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Resto de endpoints sin cambios...
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

# Continuación del código desde la línea 664...

@services_bp.route('/api/stats/<int:service_id>', methods=['GET'])
@login_required
def get_service_stats(service_id):
    """Obtener estadísticas de un servicio específico"""
    try:
        service = Service.query.get_or_404(service_id)
        
        # Parámetros de consulta
        days = request.args.get('days', 7, type=int)
        
        # Obtener estadísticas de los últimos días
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        
        stats = ServiceStats.query.filter_by(service_id=service_id)\
            .filter(ServiceStats.date >= start_date)\
            .order_by(ServiceStats.date.desc())\
            .all()
        
        # Obtener logs recientes
        recent_logs = ServiceLog.query.filter_by(service_id=service_id)\
            .order_by(ServiceLog.checked_at.desc())\
            .limit(10)\
            .all()
        
        return jsonify({
            'success': True,
            'service_name': service.name,
            'stats': [stat.to_dict() for stat in stats],
            'recent_logs': [log.to_dict() for log in recent_logs],
            'total_stats': len(stats)
        })
        
    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@services_bp.route('/api/health', methods=['GET'])
@login_required
def get_health_summary():
    """Obtener resumen de salud de todos los servicios"""
    try:
        from datetime import timedelta
        
        # Estadísticas de las últimas 24 horas
        yesterday = date.today() - timedelta(days=1)
        
        stats = db.session.query(ServiceStats)\
            .join(Service)\
            .filter(Service.is_active == True)\
            .filter(ServiceStats.date >= yesterday)\
            .all()
        
        total_checks = sum(stat.total_checks for stat in stats)
        successful_checks = sum(stat.successful_checks for stat in stats)
        
        # Servicios activos
        active_services = Service.query.filter_by(is_active=True, is_monitored=True).count()
        
        # Tiempo de respuesta promedio
        avg_response_times = [stat.avg_response_time for stat in stats if stat.avg_response_time]
        overall_avg_response = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0
        
        return jsonify({
            'success': True,
            'health_summary': {
                'total_services': active_services,
                'total_checks_24h': total_checks,
                'successful_checks_24h': successful_checks,
                'success_rate_24h': (successful_checks / total_checks * 100) if total_checks > 0 else 0,
                'avg_response_time_24h': round(overall_avg_response, 3) if overall_avg_response else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting health summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# CORRECCIÓN PRINCIPAL: Modificar las funciones que causan el problema del contexto

def check_service_with_proper_context(service_name, config, service_id=None):
    """Verificar servicio con contexto de aplicación apropiado"""
    # Verificar el servicio SIN usar el contexto de aplicación
    result = check_single_service_standalone(service_name, config)
    
    # Solo usar contexto de aplicación para logging si es necesario
    if service_id and current_app:
        try:
            # Usar el contexto actual si existe
            additional_data = {}
            for key in ['version', 'uptime', 'used_memory', 'connected_clients', 'connections', 'cluster_status']:
                if key in result:
                    additional_data[key] = result[key]
            
            # Registrar en base de datos
            log_entry = ServiceLog(
                service_id=service_id,
                status=result.get('status', False),
                response_time=result.get('response_time'),
                error_message=result.get('error'),
                additional_data=json.dumps(additional_data) if additional_data else None
            )
            
            db.session.add(log_entry)
            
            # Actualizar estadísticas
            today = date.today()
            stats = ServiceStats.query.filter_by(service_id=service_id, date=today).first()
            if not stats:
                stats = ServiceStats(service_id=service_id, date=today)
                db.session.add(stats)
            
            stats.total_checks += 1
            if result.get('status', False):
                stats.successful_checks += 1
            else:
                stats.failed_checks += 1
            
            if result.get('response_time') is not None and result.get('status', False):
                response_time = result['response_time']
                if stats.avg_response_time is None:
                    stats.avg_response_time = response_time
                    stats.min_response_time = response_time
                    stats.max_response_time = response_time
                else:
                    total_successful = stats.successful_checks
                    if total_successful > 1:
                        stats.avg_response_time = ((stats.avg_response_time * (total_successful - 1)) + response_time) / total_successful
                    
                    stats.min_response_time = min(stats.min_response_time or response_time, response_time)
                    stats.max_response_time = max(stats.max_response_time or response_time, response_time)
            
            stats.updated_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging service check: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    return result

def check_single_service_standalone(service_name, config):
    """Verificar un servicio individual SIN contexto de aplicación"""
    start_time = time.time()
    
    try:
        service_type = config['type']
        
        # Verificaciones de servicios - todas independientes del contexto Flask
        if service_type == 'http':
            result = check_http_service(
                config['host'], 
                config['port'], 
                config.get('endpoint', '/'),
                config.get('timeout', 5),
                config.get('use_https', False)
            )
        elif service_type == 'socket':
            result = {
                'status': check_socket_connection(
                    config['host'], 
                    config['port'], 
                    config.get('timeout', 5)
                )
            }
        elif service_type == 'redis':
            result = check_redis_service(
                config['host'], 
                config['port'], 
                config.get('timeout', 5),
                config.get('password')
            )
        elif service_type == 'mysql':
            result = check_mysql_service(
                config['host'], 
                config['port'],
                config.get('user', 'root'),
                config.get('password', ''),
                config.get('timeout', 5)
            )
        elif service_type == 'rabbitmq':
            result = check_rabbitmq_service(
                config['host'], 
                config['port'], 
                config.get('timeout', 5),
                config.get('username', 'guest'),
                config.get('password', 'guest')
            )
        elif service_type == 'elasticsearch':
            result = check_elasticsearch_service(
                config['host'], 
                config['port'], 
                config.get('timeout', 5),
                config.get('use_https', False)
            )
        elif service_type == 'minio':
            result = check_minio_service(
                config['host'], 
                config['port'], 
                config.get('timeout', 5),
                config.get('use_https', False)
            )
        elif service_type == 'qdrant':
            result = check_qdrant_service(
                config['host'], 
                config['port'], 
                config.get('timeout', 5),
                config.get('use_https', False)
            )
        elif service_type == 'clamav':
            result = check_clamav_service(
                config['host'], 
                config['port'], 
                config.get('timeout', 5)
            )
        else:
            result = {'status': False, 'error': 'Unknown service type'}
            
        # Calcular tiempo de respuesta si no se proporcionó
        if 'response_time' not in result:
            result['response_time'] = time.time() - start_time
            
        # Añadir información común
        result.update({
            'service_name': service_name,
            'display_name': config.get('name', service_name),
            'host': config['host'],
            'port': config['port'],
            'icon': config.get('icon', 'fas fa-server'),
            'checked_at': datetime.utcnow().isoformat()
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Service check error for {service_name} - {e}")
        
        return {
            'service_name': service_name,
            'display_name': config.get('name', service_name),
            'host': config['host'],
            'port': config['port'],
            'icon': config.get('icon', 'fas fa-server'),
            'status': False,
            'error': str(e),
            'checked_at': datetime.utcnow().isoformat(),
            'response_time': time.time() - start_time
        }

# CORRECCIÓN DEL ENDPOINT PRINCIPAL
@services_bp.route('/api/status', methods=['GET'])
@login_required
def get_services_status():
    """Endpoint para obtener el estado de todos los servicios - CORREGIDO"""
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
        
        # Verificar servicios en paralelo SIN hilos para evitar problemas de contexto
        for service_name, config in services_config.items():
            try:
                service_obj = services_objects.get(service_name)
                
                # Verificar servicio de forma directa
                result = check_single_service_standalone(service_name, config)
                
                # Registrar en base de datos si es necesario
                if service_obj:
                    try:
                        additional_data = {}
                        for key in ['version', 'uptime', 'used_memory', 'connected_clients', 'connections', 'cluster_status']:
                            if key in result:
                                additional_data[key] = result[key]
                        
                        log_entry = ServiceLog(
                            service_id=service_obj.id,
                            status=result.get('status', False),
                            response_time=result.get('response_time'),
                            error_message=result.get('error'),
                            additional_data=json.dumps(additional_data) if additional_data else None
                        )
                        
                        db.session.add(log_entry)
                        
                        # Actualizar estadísticas
                        today = date.today()
                        stats = ServiceStats.query.filter_by(service_id=service_obj.id, date=today).first()
                        if not stats:
                            stats = ServiceStats(service_id=service_obj.id, date=today)
                            db.session.add(stats)
                        
                        stats.total_checks += 1
                        if result.get('status', False):
                            stats.successful_checks += 1
                        else:
                            stats.failed_checks += 1
                        
                        if result.get('response_time') is not None and result.get('status', False):
                            response_time = result['response_time']
                            if stats.avg_response_time is None:
                                stats.avg_response_time = response_time
                                stats.min_response_time = response_time
                                stats.max_response_time = response_time
                            else:
                                total_successful = stats.successful_checks
                                if total_successful > 1:
                                    stats.avg_response_time = ((stats.avg_response_time * (total_successful - 1)) + response_time) / total_successful
                                
                                stats.min_response_time = min(stats.min_response_time or response_time, response_time)
                                stats.max_response_time = max(stats.max_response_time or response_time, response_time)
                        
                        stats.updated_at = datetime.utcnow()
                        
                    except Exception as db_error:
                        logger.error(f"Error logging service {service_name}: {db_error}")
                        db.session.rollback()
                
                results[service_name] = result
                
            except Exception as e:
                logger.error(f"Exception checking {service_name}: {e}")
                results[service_name] = {
                    'service_name': service_name,
                    'display_name': config.get('name', service_name),
                    'host': config['host'],
                    'port': config['port'],
                    'icon': config.get('icon', 'fas fa-server'),
                    'status': False,
                    'error': str(e),
                    'checked_at': datetime.utcnow().isoformat()
                }
        
        # Confirmar cambios en la base de datos
        try:
            db.session.commit()
        except Exception as commit_error:
            logger.error(f"Error committing to database: {commit_error}")
            db.session.rollback()
        
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

# También corregir el endpoint de servicio individual
@services_bp.route('/api/status/<service_name>', methods=['GET'])
@login_required
def get_single_service_status(service_name):
    """Endpoint para obtener el estado de un servicio específico - CORREGIDO"""
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
        
        # Verificar servicio de forma directa
        result = check_single_service_standalone(service_name, config)
        
        # Registrar resultado en base de datos
        try:
            additional_data = {}
            for key in ['version', 'uptime', 'used_memory', 'connected_clients', 'connections', 'cluster_status']:
                if key in result:
                    additional_data[key] = result[key]
            
            log_entry = ServiceLog(
                service_id=service_obj.id,
                status=result.get('status', False),
                response_time=result.get('response_time'),
                error_message=result.get('error'),
                additional_data=json.dumps(additional_data) if additional_data else None
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as db_error:
            logger.error(f"Error logging single service check: {db_error}")
            db.session.rollback()
        
        return jsonify({
            'success': True,
            'service': result
        })
        
    except Exception as e:
        logger.error(f"Error getting single service status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500