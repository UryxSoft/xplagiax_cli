import os
import io
import shutil
import subprocess
import redis
import csv
import threading
from flask import make_response
from datetime import datetime
from modules.models.model import ChangeHistory
# Crear una instancia de conexión a Redis
# DB 11 dedicada a appcli2 para evitar colisiones con marktrack (0-6),
# xota (0,1) y finderx (10) en el Redis compartido. Honra REDIS_HOST/PORT/DB.
redis_client = redis.StrictRedis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=int(os.environ.get('REDIS_DB', 11)),
)

BACKUP_DIR  = '/path/to/backup/directory' 

# Función para establecer una entrada en Redis con tiempo de expiración
def set_cache_with_expiration(key, value, expiration_seconds):
    redis_client.setex(key, expiration_seconds, value)
    
def create_backup():

    # Ejecutar el comando SAVE
    redis_client.save()

    # Obtener la ruta del archivo de volcado
    redis_data_dir = '/var/lib/redis'  # Ajusta esta ruta según tu configuración de Redis
    dump_file = os.path.join(redis_data_dir, 'dump.rdb')

    # Crear un directorio de backups si no existe
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # Crear un identificador único para el backup (por ejemplo, un timestamp)
    backup_id = datetime.now().strftime('%Y%m%d%H%M%S')

    # Copiar el archivo de volcado al directorio de backups
    backup_file = os.path.join(BACKUP_DIR, f'dump_{backup_id}.rdb')
    shutil.copy(dump_file, backup_file)

    return backup_id

def restore_backup(backup_id):
    # Directorio donde se almacenan los respaldos
    backup_file = os.path.join(BACKUP_DIR, f'dump_{backup_id}.rdb')

    # Verificar si el archivo de respaldo existe
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file {backup_file} not found")

    # Directorio de datos de Redis
    redis_data_dir = '/var/lib/redis'  # Ajusta esta ruta según tu configuración de Redis
    dump_file = os.path.join(redis_data_dir, 'dump.rdb')

    # Detener el servicio de Redis
    subprocess.run(['sudo', 'systemctl', 'stop', 'redis'], check=True, shell=False)

    # Copiar el archivo de respaldo al directorio de datos de Redis
    shutil.copy(backup_file, dump_file)

    # Iniciar el servicio de Redis
    subprocess.run(['sudo', 'systemctl', 'start', 'redis'], check=True, shell=False)
     
def retrieve_history_from_db():
    history = ChangeHistory.query.all()
    return [history_entry_to_dict(entry) for entry in history]

def history_entry_to_dict(entry):
    return {
        'id': entry.id,
        'timestamp': entry.timestamp,
        'action': entry.action,
        'key': entry.key,
        'value': entry.value
    }
    
def generate_heatmap_data():
    # Obtener todos los datos del hash de frecuencias de acceso
    access_frequencies = redis_client.hgetall('access_frequencies')
    
    # Convertir los datos a un formato adecuado para el mapa de calor
    heatmap_data = []
    for key, count in access_frequencies.items():
        heatmap_data.append({
            'key': key.decode('utf-8'),
            'count': int(count)
        })
    
    return heatmap_data

def analyze_key_usage():
    # Obtener todos los datos del hash de frecuencias de acceso
    access_frequencies = redis_client.hgetall('access_frequencies')
    
    # Analizar el tipo de datos de cada clave
    key_usage_data = []
    for key, count in access_frequencies.items():
        key_type = redis_client.type(key).decode('utf-8')
        size = get_key_size(key, key_type)
        key_usage_data.append({
            'key': key.decode('utf-8'),
            'type': key_type,
            'count': int(count),
            'size': size
        })
    
    return key_usage_data

def get_key_size(key, key_type):
    if key_type == 'string':
        return redis_client.strlen(key)
    elif key_type == 'hash':
        return redis_client.hlen(key)
    elif key_type == 'list':
        return redis_client.llen(key)
    elif key_type == 'set':
        return redis_client.scard(key)
    elif key_type == 'zset':
        return redis_client.zcard(key)
    else:
        return 0

def generate_custom_report(report_type):
    if report_type == 'access_frequency':
        return generate_access_frequency_report()
    elif report_type == 'key_size':
        return generate_key_size_report()
    elif report_type == 'data_types':
        return generate_data_types_report()
    else:
        return {"status": "error", "message": "Invalid report type"}

def generate_access_frequency_report():
    access_frequencies = redis_client.hgetall('access_frequencies')
    report = []
    for key, count in access_frequencies.items():
        report.append({
            'key': key.decode('utf-8'),
            'access_count': int(count)
        })
    return report

def generate_key_size_report():
    keys = redis_client.keys('*')
    report = []
    for key in keys:
        key_type = redis_client.type(key).decode('utf-8')
        size = get_key_size(key, key_type)
        report.append({
            'key': key.decode('utf-8'),
            'type': key_type,
            'size': size
        })
    return report

def generate_data_types_report():
    keys = redis_client.keys('*')
    type_counts = {
        'string': 0,
        'hash': 0,
        'list': 0,
        'set': 0,
        'zset': 0,
        'other': 0
    }
    for key in keys:
        key_type = redis_client.type(key).decode('utf-8')
        if key_type in type_counts:
            type_counts[key_type] += 1
        else:
            type_counts['other'] += 1
    return type_counts

def get_key_size(key, key_type):
    if key_type == 'string':
        return redis_client.strlen(key)
    elif key_type == 'hash':
        return redis_client.hlen(key)
    elif key_type == 'list':
        return redis_client.llen(key)
    elif key_type == 'set':
        return redis_client.scard(key)
    elif key_type == 'zset':
        return redis_client.zcard(key)
    else:
        return 0
    
def export_to_csv(report_data, report_name):
    csv_data = []
    headers = report_data[0].keys() if report_data else []
    for row in report_data:
        csv_data.append(row.values())
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(csv_data)
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={report_name}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

def get_performance_metrics():
    # Obtener información del servidor Redis
    info = redis_client.info()

    # Filtrar y estructurar las métricas de rendimiento que nos interesan
    performance_metrics = {
        'total_commands_processed': info.get('total_commands_processed', 0),
        'total_connections_received': info.get('total_connections_received', 0),
        'used_memory': info.get('used_memory', 0),
        'used_memory_human': info.get('used_memory_human', '0B'),
        'used_memory_peak': info.get('used_memory_peak', 0),
        'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
        'mem_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0.0),
        'connected_clients': info.get('connected_clients', 0),
        'blocked_clients': info.get('blocked_clients', 0),
        'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
        'instantaneous_input_kbps': info.get('instantaneous_input_kbps', 0.0),
        'instantaneous_output_kbps': info.get('instantaneous_output_kbps', 0.0),
        'rejected_connections': info.get('rejected_connections', 0),
        'expired_keys': info.get('expired_keys', 0),
        'evicted_keys': info.get('evicted_keys', 0),
        'keyspace_hits': info.get('keyspace_hits', 0),
        'keyspace_misses': info.get('keyspace_misses', 0),
        'pubsub_channels': info.get('pubsub_channels', 0),
        'pubsub_patterns': info.get('pubsub_patterns', 0),
    }

    return performance_metrics

def simulate_redis_load(load_params):
    num_operations = load_params.get('num_operations', 1000)
    operation_type = load_params.get('operation_type', 'write')  # 'write' or 'read'
    key_prefix = load_params.get('key_prefix', 'load_test')
    value_size = load_params.get('value_size', 100)  # Size of the value in bytes
    concurrency = load_params.get('concurrency', 10)  # Number of concurrent threads

    def write_operations():
        for i in range(num_operations):
            key = f"{key_prefix}_{i}"
            value = 'x' * value_size
            redis_client.set(key, value)

    def read_operations():
        for i in range(num_operations):
            key = f"{key_prefix}_{i}"
            redis_client.get(key)

    threads = []
    for _ in range(concurrency):
        if operation_type == 'write':
            thread = threading.Thread(target=write_operations)
        elif operation_type == 'read':
            thread = threading.Thread(target=read_operations)
        else:
            raise ValueError("Invalid operation type. Use 'write' or 'read'.")
        
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
              
def retrieve_audit_log():
    try:
        # Suponiendo que los registros de auditoría están almacenados en una lista en Redis
        # y que los registros se almacenan en orden cronológico.
        audit_log_key = 'audit_log'  # La clave de la lista en Redis
        audit_log = redis_client.lrange(audit_log_key, 0, -1)
        
        # Convertir los registros de bytes a diccionarios
        audit_log = [json.loads(log.decode("utf-8")) for log in audit_log]
        
        return audit_log
    except redis.RedisError as err:
        print(f"Redis error: {err}")
        return []
