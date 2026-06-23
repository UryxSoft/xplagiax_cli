from flask import Flask, jsonify, request
from flask_cors import CORS
import docker
import requests
import redis
import psutil
import pika
from datetime import datetime, timedelta
import time
import subprocess
import json
from minio import Minio
from elasticsearch import Elasticsearch
import qdrant_client
from qdrant_client.http import models
import logging

app = Flask(__name__)
CORS(app)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de conexiones (ajusta según tu setup)
DOCKER_CONTAINERS = {
    'clamav': 'clamav',
    'elasticsearch': 'elasticsearch', 
    'minio': 'minio',
    'qdrant': 'qdrant',
    'redis': 'redis',
    'rabbitmq': 'rabbitmq'
}

# Configuración de servicios
SERVICE_CONFIG = {
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0
    },
    'elasticsearch': {
        'host': 'localhost',
        'port': 9200
    },
    'minio': {
        'endpoint': 'localhost:9000',
        'access_key': 'minioadmin',  # Cambiar por tus credenciales
        'secret_key': 'minioadmin'
    },
    'qdrant': {
        'host': 'localhost',
        'port': 6333
    },
    'rabbitmq': {
        'host': 'localhost',
        'port': 5672,
        'username': 'guest',  # Cambiar por tus credenciales
        'password': 'guest'
    },
    'clamav': {
        'host': 'localhost',
        'port': 3310
    }
}

def get_docker_client():
    """Obtener cliente Docker"""
    try:
        return docker.from_env()
    except Exception as e:
        logger.error(f"Error conectando a Docker: {e}")
        return None

def get_container_info(container_name):
    """Obtener información detallada del contenedor"""
    try:
        client = get_docker_client()
        if not client:
            return None
            
        container = client.containers.get(container_name)
        
        # Calcular uptime
        created = datetime.strptime(container.attrs['Created'][:19], '%Y-%m-%dT%H:%M:%S')
        uptime = datetime.now() - created
        
        # Obtener estadísticas de uso
        stats = container.stats(stream=False)
        
        # Calcular uso de CPU
        cpu_usage = 0
        if 'cpu_stats' in stats and 'precpu_stats' in stats:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            if system_delta > 0:
                cpu_usage = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
        
        # Calcular uso de memoria
        memory_usage = 0
        memory_limit = 0
        if 'memory_stats' in stats:
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 0)
        
        return {
            'name': container.name,
            'status': container.status,
            'state': container.attrs['State'],
            'created': container.attrs['Created'],
            'uptime': str(uptime).split('.')[0],  # Sin microsegundos
            'cpu_usage': round(cpu_usage, 2),
            'memory_usage': memory_usage,
            'memory_limit': memory_limit,
            'memory_percentage': round((memory_usage / memory_limit * 100), 2) if memory_limit > 0 else 0,
            'ports': container.attrs.get('NetworkSettings', {}).get('Ports', {}),
            'image': container.attrs['Config']['Image']
        }
    except Exception as e:
        logger.error(f"Error obteniendo info del contenedor {container_name}: {e}")
        return None

def check_service_health(service_name):
    """Verificar salud específica de cada servicio"""
    try:
        if service_name == 'redis':
            return check_redis_health()
        elif service_name == 'elasticsearch':
            return check_elasticsearch_health()
        elif service_name == 'minio':
            return check_minio_health()
        elif service_name == 'qdrant':
            return check_qdrant_health()
        elif service_name == 'rabbitmq':
            return check_rabbitmq_health()
        elif service_name == 'clamav':
            return check_clamav_health()
        else:
            return {'healthy': False, 'error': 'Servicio no reconocido'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_redis_health():
    """Verificar salud de Redis"""
    try:
        config = SERVICE_CONFIG['redis']
        r = redis.Redis(host=config['host'], port=config['port'], db=config['db'], socket_timeout=5)
        
        start_time = time.time()
        info = r.info()
        response_time = (time.time() - start_time) * 1000
        
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2),
            'version': info.get('redis_version'),
            'uptime_seconds': info.get('uptime_in_seconds'),
            'connected_clients': info.get('connected_clients'),
            'used_memory': info.get('used_memory_human'),
            'total_commands_processed': info.get('total_commands_processed')
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_elasticsearch_health():
    """Verificar salud de Elasticsearch"""
    try:
        config = SERVICE_CONFIG['elasticsearch']
        es = Elasticsearch([f"http://{config['host']}:{config['port']}"], request_timeout=5)
        
        start_time = time.time()
        health = es.cluster.health()
        response_time = (time.time() - start_time) * 1000
        
        return {
            'healthy': health['status'] in ['green', 'yellow'],
            'response_time_ms': round(response_time, 2),
            'cluster_name': health.get('cluster_name'),
            'status': health.get('status'),
            'number_of_nodes': health.get('number_of_nodes'),
            'number_of_data_nodes': health.get('number_of_data_nodes'),
            'active_primary_shards': health.get('active_primary_shards'),
            'active_shards': health.get('active_shards')
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_minio_health():
    """Verificar salud de MinIO"""
    try:
        config = SERVICE_CONFIG['minio']
        client = Minio(
            config['endpoint'],
            access_key=config['access_key'],
            secret_key=config['secret_key'],
            secure=False
        )
        
        start_time = time.time()
        # Intentar listar buckets como health check
        buckets = list(client.list_buckets())
        response_time = (time.time() - start_time) * 1000
        
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2),
            'bucket_count': len(buckets),
            'buckets': [bucket.name for bucket in buckets]
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_qdrant_health():
    """Verificar salud de Qdrant"""
    try:
        config = SERVICE_CONFIG['qdrant']
        client = qdrant_client.QdrantClient(host=config['host'], port=config['port'], timeout=5)
        
        start_time = time.time()
        collections = client.get_collections()
        response_time = (time.time() - start_time) * 1000
        
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2),
            'collections_count': len(collections.collections),
            'collections': [col.name for col in collections.collections]
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_rabbitmq_health():
    """Verificar salud de RabbitMQ"""
    try:
        config = SERVICE_CONFIG['rabbitmq']
        
        start_time = time.time()
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=config['host'],
                port=config['port'],
                virtual_host='/',
                credentials=pika.PlainCredentials(config['username'], config['password']),
                socket_timeout=5
            )
        )
        channel = connection.channel()
        response_time = (time.time() - start_time) * 1000
        
        connection.close()
        
        # Intentar obtener información adicional via API HTTP
        try:
            api_response = requests.get(
                f"http://{config['host']}:15672/api/overview",
                auth=(config['username'], config['password']),
                timeout=5
            )
            if api_response.status_code == 200:
                api_data = api_response.json()
                return {
                    'healthy': True,
                    'response_time_ms': round(response_time, 2),
                    'version': api_data.get('rabbitmq_version'),
                    'erlang_version': api_data.get('erlang_version'),
                    'message_stats': api_data.get('message_stats', {})
                }
        except:
            pass
            
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2)
        }
        
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_clamav_health():
    """Verificar salud de ClamAV"""
    try:
        config = SERVICE_CONFIG['clamav']
        
        start_time = time.time()
        # Alternativa usando socket directo
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((config['host'], config['port']))
        sock.close()
        response_time = (time.time() - start_time) * 1000
        
        if result == 0:
            return {
                'healthy': True,
                'response_time_ms': round(response_time, 2),
                'service': 'clamd'
            }
        else:
            return {'healthy': False, 'error': 'No se puede conectar al daemon'}
            
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

# Ruta para el dashboard
@app.route('/')
def dashboard():
    """Servir el dashboard principal"""
    try:
        with open('./templates/docker_monitoring_dashboard.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'error': 'Dashboard HTML no encontrado'}), 404

@app.route('/api/health/<service>')
def health_check(service):
    """Endpoint para verificar salud de un servicio específico"""
    if service not in DOCKER_CONTAINERS:
        return jsonify({'error': 'Servicio no encontrado'}), 404
    
    container_name = DOCKER_CONTAINERS[service]
    
    # Información del contenedor Docker
    container_info = get_container_info(container_name)
    
    # Verificación específica del servicio
    service_health = check_service_health(service)
    
    response = {
        'service': service,
        'container': container_name,
        'timestamp': datetime.now().isoformat(),
        'docker_info': container_info,
        'service_health': service_health,
        'overall_status': 'running' if (container_info and container_info['status'] == 'running' and service_health['healthy']) else 'stopped'
    }
    
    return jsonify(response)

@app.route('/api/health')
def health_check_all():
    """Endpoint para verificar todos los servicios"""
    results = {}
    
    for service in DOCKER_CONTAINERS.keys():
        container_name = DOCKER_CONTAINERS[service]
        
        container_info = get_container_info(container_name)
        service_health = check_service_health(service)
        
        results[service] = {
            'container': container_name,
            'docker_info': container_info,
            'service_health': service_health,
            'overall_status': 'running' if (container_info and container_info['status'] == 'running' and service_health['healthy']) else 'stopped'
        }
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'services': results,
        'summary': {
            'total': len(results),
            'running': sum(1 for s in results.values() if s['overall_status'] == 'running'),
            'stopped': sum(1 for s in results.values() if s['overall_status'] == 'stopped')
        }
    })

@app.route('/api/containers')
def list_containers():
    """Listar todos los contenedores Docker"""
    try:
        client = get_docker_client()
        if not client:
            return jsonify({'error': 'No se puede conectar a Docker'}), 500
            
        containers = []
        for container in client.containers.list(all=True):
            containers.append({
                'id': container.id[:12],
                'name': container.name,
                'status': container.status,
                'image': container.attrs['Config']['Image'],
                'created': container.attrs['Created'],
                'ports': container.attrs.get('NetworkSettings', {}).get('Ports', {})
            })
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'containers': containers,
            'total': len(containers)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/container/<container_name>/logs')
def get_container_logs(container_name):
    """Obtener logs de un contenedor específico"""
    try:
        client = get_docker_client()
        if not client:
            return jsonify({'error': 'No se puede conectar a Docker'}), 500
            
        container = client.containers.get(container_name)
        
        # Obtener últimas líneas de logs
        lines = request.args.get('lines', 100, type=int)
        logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
        
        return jsonify({
            'container': container_name,
            'timestamp': datetime.now().isoformat(),
            'logs': logs.split('\n'),
            'lines_requested': lines
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stats')
def system_stats():
    """Estadísticas del sistema"""
    try:
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'used': psutil.virtual_memory().used,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'percent': psutil.disk_usage('/').percent
            },
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)