# Configuración de SeaweedFS en XplagiaX

## Resumen

Este documento describe la configuración y solución de errores relacionados con el almacenamiento de archivos usando SeaweedFS.

---

## Configuración de Puertos

### Docker Container
```
SeaweedFS: 8333:8333
```

### Archivos de Configuración

| Archivo | Variable | Valor |
|---------|----------|-------|
| `modules/bucket_service/bucket_routes.py` | `SEAWEEDFS_FILER_URL` | `http://localhost:8333` |
| `modules/bucket_service/bucket_routes.py` | `SEAWEEDFS_MASTER_URL` | `http://localhost:8333` |
| `modules/users_service/user_routes.py` | `SEAWEEDFS_FILER_URL` | `http://localhost:8333` |

---

## Errores Comunes y Soluciones

### Error 404: Bucket No Existe
```
HEAD /xplagiax-users-documents/ HTTP/1.1" 404
```

**Significado:** El directorio/bucket `xplagiax-users-documents` no existe en SeaweedFS.

**Solución:** No es crítico. El directorio se crea automáticamente al subir el primer archivo.

---

### Error 405: Method Not Allowed
```
POST /xplagiax-users-documents/ HTTP/1.1" 405
```

**Significado:** Se intentó crear el bucket con método HTTP incorrecto.

**Solución aplicada en `seaweedfs_storage.py`:**

```python
def ensure_bucket_exists(self):
    """Asegurar que el directorio raíz (bucket) existe"""
    try:
        response = requests.head(f"{self.filer_url}{self.base_path}/")
        if response.status_code == 404:
            # SeaweedFS usa PUT para crear directorios
            put_response = requests.put(
                f"{self.filer_url}{self.base_path}/",
                data=b'',
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            # Si PUT falla, subir archivo .keep para crear estructura
            if put_response.status_code not in [200, 201, 204]:
                requests.put(
                    f"{self.filer_url}{self.base_path}/.keep",
                    data=b'',
                    headers={'Content-Type': 'application/octet-stream'}
                )
        return True
    except Exception as e:
        print(f"⚠️ Bucket check (no crítico): {e}")
        return False
```

**Cambios clave:**
- ❌ `POST` → ✅ `PUT`
- ❌ `Content-Type: application/directory` → ✅ `Content-Type: application/octet-stream`

---

## Arquitectura del Cliente SeaweedFS

### Archivo: `modules/bucket_service/seaweedfs_storage.py`

```
SeaweedFSClient
├── __init__(filer_url, master_url, bucket_name)
├── ensure_bucket_exists()      # Crea bucket si no existe
├── upload_file()               # Sube archivo individual
├── download_file()             # Descarga archivo
├── delete_file()               # Elimina archivo
├── list_files()                # Lista archivos
├── get_file_metadata()         # Obtiene metadata
├── upload_document()           # Sube documento con metadata
├── list_user_documents()       # Lista documentos de usuario
├── delete_document()           # Elimina documento
├── get_user_storage_stats()    # Estadísticas de almacenamiento
└── create_folder() / delete_folder()
```

---

## Variables de Entorno

```bash
# Opcional: Sobrescribir configuración
export SEAWEEDFS_FILER_URL=http://localhost:8333
export SEAWEEDFS_MASTER_URL=http://localhost:8333
export SEAWEEDFS_BUCKET=xplagiax-users-documents
```

---

## Migración desde MinioClient

### Cambios de Parámetros

| MinioClient (anterior) | SeaweedFSClient (actual) |
|------------------------|--------------------------|
| `endpoint` | `filer_url` |
| `access_key` | _(no requerido)_ |
| `secret_key` | _(no requerido)_ |
| `bucket_name` | `bucket_name` |
| `region_name` | _(no requerido)_ |

### Ejemplo de Inicialización

```python
# Antes (MinioClient)
minio_client = MinioClient(
    endpoint='http://localhost:9500',
    access_key='minioadmin',
    secret_key='minioadmin',
    bucket_name='xplagiax-users-documents',
    region_name='us-east-1'
)

# Ahora (SeaweedFSClient)
minio_client = SeaweedFSClient(
    filer_url='http://localhost:8333',
    master_url='http://localhost:8333',
    bucket_name='xplagiax-users-documents'
)
```

---

## Verificación de Funcionamiento

### Comando de prueba
```bash
curl -I http://localhost:8333/xplagiax-users-documents/
```

### Respuestas esperadas
- `200 OK` - Bucket existe y funciona
- `404 Not Found` - Bucket no existe (se creará al subir archivo)
- `Connection refused` - SeaweedFS no está corriendo

---

## Fecha de Actualización
2026-01-17
