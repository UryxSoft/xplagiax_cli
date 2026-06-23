from flask import Blueprint, request, jsonify, g, current_app, send_file, session
from flask_login import current_user, login_required
from modules.models.model import db, Folder, File, Users, ItemShare
from .seaweedfs_storage import SeaweedFSClient
import os
import io
from werkzeug.utils import secure_filename
from functools import wraps, lru_cache
from datetime import datetime, timedelta
import mimetypes
from typing import Optional, Dict, List
import logging
from settings.config import DevelopmentConfig

# ============================================
# CONFIGURACIÓN SEAWEEDFS
# ============================================
SEAWEEDFS_FILER_URL  = DevelopmentConfig.SEAWEEDFS_FILER_URL #'http://localhost:8333'
SEAWEEDFS_MASTER_URL = DevelopmentConfig.SEAWEEDFS_MASTER_URL #'http://localhost:8333'
SEAWEEDFS_BUCKET     = DevelopmentConfig.SEAWEEDFS_BUCKET #'xplagiax-users-documents'

# Límites de archivo
MAX_FILE_SIZE = DevelopmentConfig.MAX_FILE_SIZE #100 * 1024 * 1024  # 100MB default
ALLOWED_EXTENSIONS = DevelopmentConfig.ALLOWED_EXTENSIONS #{'pdf', 'doc', 'docx', 'txt','ppt','pptx', 'png', 'jpg', 'jpeg'}

# Cache de sesión simple
_session_cache = {}
CACHE_TTL = DevelopmentConfig.CACHE_TTL #300  # 5 minutos


# Configurar logging
logger = logging.getLogger(__name__)

x_buck = Blueprint('x_buck', __name__)



# ============================================
# CLIENTE SEAWEEDFS (SINGLETON)
# ============================================
_storage_client = None

def get_storage_client() -> SeaweedFSClient:
    """Obtener instancia única de SeaweedFSClient (patrón singleton)"""
    global _storage_client
    if _storage_client is None:
        _storage_client = SeaweedFSClient(
            filer_url=SEAWEEDFS_FILER_URL,
            master_url=SEAWEEDFS_MASTER_URL,
            bucket_name=SEAWEEDFS_BUCKET
        )
        logger.info("SeaweedFS client initialized")
    return _storage_client

# ============================================
# UTILIDADES Y VALIDACIONES
# ============================================

def allowed_file(filename: str) -> bool:
    """Verificar si la extensión del archivo es permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file) -> tuple:
    """Validar el tamaño del archivo. Retorna (valid, size)"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return (size <= MAX_FILE_SIZE, size)

def get_mime_type(filename: str) -> str:
    """Obtener MIME type basado en extensión"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def cache_key(prefix: str, *args) -> str:
    """Generar clave de cache"""
    return f"{prefix}:{'_'.join(map(str, args))}"

def get_from_cache(key: str) -> Optional[Dict]:
    """Obtener dato de cache si no ha expirado"""
    if key in _session_cache:
        data, timestamp = _session_cache[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
            return data
        else:
            del _session_cache[key]
    return None

def set_cache(key: str, data: Dict):
    """Guardar dato en cache"""
    _session_cache[key] = (data, datetime.now())

def clear_cache_for_user(user_id: int):
    """Limpiar cache de un usuario"""
    keys_to_delete = [k for k in _session_cache.keys() if str(user_id) in k]
    for key in keys_to_delete:
        del _session_cache[key]

# ============================================
# DECORADORES
# ============================================

def check_bucket(f):
    """Decorador mejorado para manejar excepciones"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({"error": str(e)}), 400
        except PermissionError as e:
            logger.warning(f"Permission denied: {e}")
            return jsonify({"error": "No tienes permiso para realizar esta acción"}), 403
        except FileNotFoundError as e:
            logger.warning(f"File not found: {e}")
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}", exc_info=True)
            return jsonify({"error": "Error interno del servidor"}), 500
    return decorated_function

def require_auth(f):
    """Verificar que el usuario esté autenticado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user or not current_user.is_authenticated:
            return jsonify({"error": "Autenticación requerida"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# VALIDADORES DE PERMISOS
# ============================================

def validate_folder_access(folder: Folder, user_id: int, require_write: bool = False) -> bool:
    """Validar acceso a una carpeta"""
    if folder.user_id == user_id:
        return True
    if folder.is_shared and not require_write:
        return True
    return False

def validate_file_access(file: File, user_id: int) -> bool:
    """Validar acceso a un archivo"""
    if file.user_id == user_id:
        return True
    # Verificar si la carpeta padre es compartida
    if file.folder and file.folder.is_shared:
        return True
    return False

# ============================================
# RUTAS - CARPETAS
# ============================================

@x_buck.route('/api/folders', methods=['GET'])
@require_auth
@check_bucket
def get_folders():
    """Listar carpetas con paginación y cache"""
    user_id = current_user.id
    parent_id = request.args.get('parent_id', None)
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 100)  # Máximo 100
    
    # Intentar obtener de cache
    cache_k = cache_key('folders', user_id, parent_id, page, per_page)
    cached_data = get_from_cache(cache_k)
    if cached_data:
        return jsonify(cached_data)
    
    # Query base con paginación
    query = Folder.query.filter_by(user_id=user_id)
    
    if parent_id:
        query = query.filter_by(parent_id=parent_id)
    else:
        query = query.filter_by(parent_id=None)
    
    # Usar paginación de SQLAlchemy
    pagination = query.order_by(Folder.name).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    folders = pagination.items
    
    # Carpetas compartidas (solo en primera página de raíz)
    shared_folders = []
    if parent_id is None and page == 1:
        shared_folders = Folder.query.filter(
            Folder.is_shared == True,
            Folder.user_id != user_id,
            Folder.parent_id == None
        ).order_by(Folder.name).limit(per_page).all()
    
    # Formatear respuesta con owner name optimizado (una sola query)
    all_folders = folders + shared_folders
    folders_data = [
        {
            'id': folder.id,
            'name': folder.name,
            'path': folder.path,
            'created_at': folder.created_at.isoformat(),
            'updated_at': folder.updated_at.isoformat(),
            'is_shared': folder.is_shared,
            'owner': f"{folder.owner.name} {folder.owner.lastname}",
            'is_owner': folder.user_id == user_id
        }
        for folder in all_folders
    ]
    
    result = {
        'folders': folders_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }
    
    # Guardar en cache
    set_cache(cache_k, result)
    
    return jsonify(result)

@x_buck.route('/api/folders', methods=['POST'])
@require_auth
@check_bucket
def create_folder():
    """Crear carpeta con validaciones mejoradas"""
    data = request.json
    name = data.get('name', '').strip()
    parent_id = data.get('parent_id')
    is_shared = data.get('is_shared', False)
    
    if not name:
        raise ValueError("El nombre de la carpeta es obligatorio")
    
    if len(name) > 255:
        raise ValueError("El nombre es demasiado largo (máximo 255 caracteres)")
    
    # Validar caracteres no permitidos
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in name for char in invalid_chars):
        raise ValueError(f"El nombre contiene caracteres no permitidos: {', '.join(invalid_chars)}")
    
    user_id = current_user.id
    
    # Determinar ruta
    if parent_id:
        parent = Folder.query.get(parent_id)
        if not parent:
            raise FileNotFoundError("Carpeta padre no encontrada")
        
        if not validate_folder_access(parent, user_id, require_write=True):
            raise PermissionError("No tienes permiso para crear carpetas aquí")
        
        path = f"{parent.path}/{name}"
    else:
        path = f"{user_id}/{name}"
    
    # Verificar duplicados
    existing = Folder.query.filter_by(
        name=name,
        parent_id=parent_id,
        user_id=user_id
    ).first()
    
    if existing:
        raise ValueError("Ya existe una carpeta con este nombre")
    
    # Crear en SeaweedFS
    storage_client = get_storage_client()
    seaweedfs_path = storage_client.create_folder(path)
    
    # Crear en BD
    new_folder = Folder(
        name=name,
        path=seaweedfs_path.rstrip('/'),  # Normalizar path
        parent_id=parent_id,
        user_id=user_id,
        is_shared=is_shared
    )
    
    db.session.add(new_folder)
    db.session.commit()
    
    # Limpiar cache
    clear_cache_for_user(user_id)
    
    logger.info(f"Folder created: {new_folder.id} by user {user_id}")
    
    return jsonify({
        'id': new_folder.id,
        'name': new_folder.name,
        'path': new_folder.path,
        'created_at': new_folder.created_at.isoformat(),
        'updated_at': new_folder.updated_at.isoformat(),
        'is_shared': new_folder.is_shared
    }), 201

# ============================================
# RUTAS - ARCHIVOS
# ============================================

@x_buck.route('/api/files', methods=['POST'])
@require_auth
@check_bucket
def upload_file():
    """Subir archivo con validaciones mejoradas"""
    if 'file' not in request.files:
        raise ValueError("No se incluyó ningún archivo")
    
    file = request.files['file']
    
    if file.filename == '':
        raise ValueError("Nombre de archivo vacío")
    
    # Validar extensión
    if not allowed_file(file.filename):
        raise ValueError(f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Validar tamaño
    is_valid_size, file_size = validate_file_size(file)
    if not is_valid_size:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise ValueError(f"Archivo demasiado grande. Máximo permitido: {max_mb:.2f} MB")
    
    folder_id = request.form.get('folder_id')
    folder_path = ""
    
    # Validar carpeta si se especifica
    if folder_id:
        folder = Folder.query.get(folder_id)
        if not folder:
            raise FileNotFoundError("Carpeta no encontrada")
        
        if not validate_folder_access(folder, current_user.id, require_write=True):
            raise PermissionError("No tienes permiso para subir a esta carpeta")
        
        folder_path = folder.path
    
    # Subir archivo a SeaweedFS
    storage_client = get_storage_client()
    upload_result = storage_client.upload_file(file, current_user, folder_path)
    
    # Limpiar cache
    clear_cache_for_user(current_user.id)
    
    logger.info(f"File uploaded: {upload_result['file_id']} by user {current_user.id}, size: {file_size} bytes")
    
    return jsonify({
        'id': upload_result['file_id'],
        'filename': upload_result['object_name'],
        'original_filename': upload_result['original_filename'],
        'mime_type': upload_result['mime_type'],
        'size': upload_result['size'],
        'url': upload_result['minio_url'],
        'folder_id': folder_id,
        'storage_info': upload_result['storage_info']
    }), 201

@x_buck.route('/api/files', methods=['GET'])
@require_auth
@check_bucket
def get_files():
    """Listar archivos con paginación y búsqueda"""
    folder_id = request.args.get('folder_id')
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 100)
    sort_by = request.args.get('sort_by', 'created_at')  # name, size, created_at
    order = request.args.get('order', 'desc')  # asc, desc
    
    user_id = current_user.id
    
    # Cache key
    cache_k = cache_key('files', user_id, folder_id, search, page, per_page, sort_by, order)
    cached_data = get_from_cache(cache_k)
    if cached_data:
        return jsonify(cached_data)
    
    # Query base
    query = File.query.filter_by(user_id=user_id)
    
    # Filtrar por carpeta
    if folder_id:
        folder = Folder.query.get(folder_id)
        if not folder:
            raise FileNotFoundError("Carpeta no encontrada")
        
        if not validate_folder_access(folder, user_id):
            raise PermissionError("No tienes permiso para ver esta carpeta")
        
        query = query.filter_by(folder_id=folder_id)
    else:
        query = query.filter_by(folder_id=None)
    
    # Búsqueda
    if search:
        query = query.filter(File.original_filename.ilike(f'%{search}%'))
    
    # Ordenamiento
    sort_column = getattr(File, sort_by, File.created_at)
    if order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Formatear respuesta
    files_data = [
        {
            'id': file.id,
            'filename': file.filename,
            'original_filename': file.original_filename,
            'mime_type': file.mime_type,
            'size': file.size,
            'size_mb': round(file.size / (1024 * 1024), 2),
            'created_at': file.created_at.isoformat(),
            'url': file.minio_url,
            'folder_id': file.folder_id
        }
        for file in pagination.items
    ]
    
    result = {
        'files': files_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }
    
    # Guardar en cache
    set_cache(cache_k, result)
    
    return jsonify(result)

@x_buck.route('/api/files/<int:file_id>/download', methods=['GET'])
@require_auth
@check_bucket
def download_file(file_id):
    """Descargar archivo con validaciones"""
    file = File.query.get(file_id)
    if not file:
        raise FileNotFoundError("Archivo no encontrado")
    
    if not validate_file_access(file, current_user.id):
        raise PermissionError("No tienes permiso para descargar este archivo")
    
    # Descargar desde SeaweedFS
    storage_client = get_storage_client()
    
    try:
        content = storage_client.download_file(file.filename)
        
        logger.info(f"File downloaded: {file_id} by user {current_user.id}")
        
        return send_file(
            io.BytesIO(content),
            mimetype=file.mime_type,
            as_attachment=True,
            download_name=file.original_filename
        )
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise

@x_buck.route('/files/<int:file_id>', methods=['DELETE'])
@require_auth
@check_bucket
def delete_file(file_id):
    """Eliminar archivo"""
    file = File.query.get(file_id)
    if not file:
        raise FileNotFoundError("Archivo no encontrado")
    
    if file.user_id != current_user.id:
        raise PermissionError("No tienes permiso para eliminar este archivo")
    
    storage_client = get_storage_client()
    
    try:
        # Eliminar de SeaweedFS
        storage_client.delete_file(file.filename, current_user)
        
        # Eliminar de BD
        db.session.delete(file)
        db.session.commit()
        
        # Limpiar cache
        clear_cache_for_user(current_user.id)
        
        logger.info(f"File deleted: {file_id} by user {current_user.id}")
        
        return jsonify({"message": "Archivo eliminado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting file {file_id}: {e}")
        raise

# ============================================
# RUTAS - CARPETAS (OPERACIONES)
# ============================================

@x_buck.route('/folders/<int:folder_id>', methods=['DELETE'])
@require_auth
@check_bucket
def delete_folder(folder_id):
    """Eliminar carpeta con validaciones mejoradas"""
    folder = Folder.query.get(folder_id)
    if not folder:
        raise FileNotFoundError("Carpeta no encontrada")
    
    if folder.user_id != current_user.id:
        raise PermissionError("No tienes permiso para eliminar esta carpeta")
    
    # Verificar subcarpetas
    if folder.subfolders:
        raise ValueError("No se puede eliminar: la carpeta contiene subcarpetas")
    
    # Contar archivos
    file_count = File.query.filter_by(folder_id=folder.id).count()
    
    storage_client = get_storage_client()
    
    try:
        # Eliminar archivos primero
        files = File.query.filter_by(folder_id=folder.id).all()
        for file in files:
            storage_client.delete_file(file.filename, current_user)
            db.session.delete(file)
        
        # Eliminar carpeta de SeaweedFS
        storage_client.delete_folder(folder.path)
        
        # Eliminar de BD
        db.session.delete(folder)
        db.session.commit()
        
        # Limpiar cache
        clear_cache_for_user(current_user.id)
        
        logger.info(f"Folder deleted: {folder_id} with {file_count} files by user {current_user.id}")
        
        return jsonify({
            "message": "Carpeta eliminada correctamente",
            "files_deleted": file_count
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting folder {folder_id}: {e}")
        raise

# ============================================
# RUTAS - DOCUMENTOS
# ============================================

@x_buck.route('/api/documents', methods=['GET'])
@require_auth
@check_bucket
def list_documents():
    """Listar documentos del usuario con paginación"""
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 50)), 100)
    
    user_id = current_user.id
    
    # Cache
    cache_k = cache_key('documents', user_id, page, per_page)
    cached_data = get_from_cache(cache_k)
    if cached_data:
        return jsonify(cached_data)
    
    storage_client = get_storage_client()
    
    try:
        # Obtener documentos desde SeaweedFS
        documents = storage_client.list_user_documents(user_id)
        
        # Aplicar paginación manual
        start = (page - 1) * per_page
        end = start + per_page
        paginated_docs = documents[start:end]
        
        result = {
            'documents': paginated_docs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(documents),
                'pages': (len(documents) + per_page - 1) // per_page
            }
        }
        
        set_cache(cache_k, result)
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error listing documents for user {user_id}: {e}")
        raise

@x_buck.route('/api/documents/<path:document_id>/<int:user_id>', methods=['DELETE'])
@require_auth
@check_bucket
def delete_document(document_id, user_id):
    """Eliminar documento con validaciones"""
    # Verificar permisos
    if int(user_id) != current_user.id and not getattr(current_user, 'is_admin', False):
        raise PermissionError("No tienes permiso para eliminar este documento")
    
    storage_client = get_storage_client()
    
    try:
        result = storage_client.delete_document_by_id(document_id, user_id)
        
        # Limpiar cache
        clear_cache_for_user(user_id)
        
        logger.info(f"Document deleted: {document_id} by user {current_user.id}")
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise

@x_buck.route('/api/documents', methods=['POST'])
@require_auth
@check_bucket
def upload_document():
    """Subir documento con metadata y registro en DB"""
    if 'file' not in request.files:
        raise ValueError("No hay archivo en la solicitud")
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    folder_id = request.form.get('folder_id', type=int)
    
    if not user_id:
        raise ValueError("Se requiere user_id")
    
    # Validar permisos
    if hasattr(current_user, 'id'):
        if int(user_id) != current_user.id and not getattr(current_user, 'is_admin', False):
            raise PermissionError("No tienes permiso para subir documentos para este usuario")
    
    # Validar extensión
    if not allowed_file(file.filename):
        raise ValueError(f"Tipo de archivo no permitido")
    
    # Validar tamaño
    is_valid_size, file_size = validate_file_size(file)
    if not is_valid_size:
        raise ValueError(f"Archivo demasiado grande")
    
    # Extraer metadata
    metadata = {
        'user_id': user_id,
        'title': request.form.get('title', file.filename),
        'author': request.form.get('author', 'Unknown'),
        'date_published': request.form.get('date_published', 'Unknown'),
        'language': request.form.get('language', 'General'),
        'rena': request.form.get('rena', 'General'),
        'document_id': request.form.get('document_id'),
        'theme': request.form.get('theme', 'General'),
    }
    
    storage_client = get_storage_client()
    
    try:
        result = storage_client.upload_documents(file, user_id, metadata)
        
        # Agregar info de almacenamiento si no está
        if 'storage_info' not in result:
            user = Users.query.get(user_id)
            if user:
                result['storage_info'] = {
                    "used_mb": user.used_storage_bytes / (1024 * 1024),
                    "total_mb": user.get_total_storage_limit_bytes() / (1024 * 1024),
                    "remaining_mb": user.get_remaining_storage_bytes() / (1024 * 1024),
                    "usage_percentage": user.get_storage_usage_percentage()
                }
        
        # Limpiar cache
        clear_cache_for_user(int(user_id))
        
        # ✅ REGISTRAR EN DB (NUEVO DMS)
        try:
            from modules.models.model import File as FileModel
            new_file_record = FileModel(
                filename=result.get('key', '').split('/')[-1] or file.filename,
                original_filename=file.filename,
                mime_type=file.content_type or 'application/octet-stream',
                size=file_size,
                user_id=int(user_id),
                minio_url=result.get('url', ''),
                folder_id=folder_id
            )
            db.session.add(new_file_record)
            db.session.commit()
            result['id'] = new_file_record.id
        except Exception as db_err:
            logger.error(f"Error registering file in DB: {db_err}")
            # No fallamos la subida si solo falla el registro en la tabla Files
            # pero sería bueno que el usuario lo sepa
            result['db_warning'] = "File uploaded to storage but failed to register in DMS database"

        logger.info(f"Document uploaded: {result.get('document_id')} by user {current_user.id}")
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise

# ============================================
# RUTAS - DOCUMENTOS INTERNAL (SIN SESIÓN)
# ============================================

@x_buck.route('/api/documents/internal', methods=['POST'])
@check_bucket
def upload_document_internal():
    """
    Endpoint INTERNO para subir documentos sin requerir sesión de usuario.
    Usado por otros servicios internos (ej: doc_routes.py).
    La seguridad se basa en que solo es accesible desde localhost.
    """
    # Verificar que la petición viene de localhost (seguridad básica)
    client_ip = request.remote_addr
    if client_ip not in ['127.0.0.1', '::1', 'localhost']:
        logger.warning(f"Intento de acceso a endpoint interno desde IP no autorizada: {client_ip}")
        return jsonify({"error": "Acceso no autorizado"}), 403
    
    if 'file' not in request.files:
        raise ValueError("No hay archivo en la solicitud")
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    if not user_id:
        raise ValueError("Se requiere user_id")
    
    # Validar que el usuario existe
    user = Users.query.get(user_id)
    if not user:
        raise ValueError(f"Usuario {user_id} no encontrado")
    
    # Validar extensión
    if not allowed_file(file.filename):
        raise ValueError(f"Tipo de archivo no permitido")
    
    # Validar tamaño
    is_valid_size, file_size = validate_file_size(file)
    if not is_valid_size:
        raise ValueError(f"Archivo demasiado grande")
    
    # Extraer metadata
    title = request.form.get('title', file.filename)
    author = request.form.get('author', 'Unknown')
    theme = request.form.get('theme', 'General')
    
    storage_client = get_storage_client()
    
    try:
        # Extraer document_id externo si fue proporcionado
        external_doc_id = request.form.get('document_id')
        
        # Usar upload_document con la firma correcta, incluyendo el doc_id
        result = storage_client.upload_document(file, title, author, theme, user_id, doc_id=external_doc_id)
        
        # Agregar info de almacenamiento
        if 'storage_info' not in result:
            result['storage_info'] = {
                "used_mb": user.used_storage_bytes / (1024 * 1024),
                "total_mb": user.get_total_storage_limit_bytes() / (1024 * 1024),
                "remaining_mb": user.get_remaining_storage_bytes() / (1024 * 1024),
                "usage_percentage": user.get_storage_usage_percentage()
            }
        
        # Agregar document_id externo si fue proporcionado
        external_doc_id = request.form.get('document_id')
        if external_doc_id:
            result['external_document_id'] = external_doc_id
        
        # Limpiar cache
        clear_cache_for_user(int(user_id))
        
        logger.info(f"[INTERNAL] Document uploaded: {result.get('document_id')} for user {user_id}")
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"[INTERNAL] Error uploading document: {e}", exc_info=True)
        raise


@x_buck.route('/api/documents/<path:file_key>', methods=['GET'])
@require_auth
@check_bucket
def get_document_info(file_key):
    """Obtener información de documento"""
    storage_client = get_storage_client()
    
    try:
        result = storage_client.get_document_info(file_key)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting document info {file_key}: {e}")
        raise

@x_buck.route('/api/documents/<path:file_key>/download', methods=['GET'])
@require_auth
@check_bucket
def download_document(file_key):
    """Descargar documento"""
    storage_client = get_storage_client()
    
    try:
        logger.info(f"Document downloaded: {file_key} by user {current_user.id}")
        return storage_client.download_document(file_key)
    except Exception as e:
        logger.error(f"Error downloading document {file_key}: {e}")
        raise

@x_buck.route('/api/documents/<path:file_key>', methods=['PUT'])
@require_auth
@check_bucket
def update_document_metadata(file_key):
    """Actualizar metadata de documento"""
    new_metadata = request.json
    
    if not new_metadata:
        raise ValueError("No se proporcionaron metadatos")
    
    storage_client = get_storage_client()
    
    try:
        result = storage_client.update_document_metadata(file_key, new_metadata)
        
        # Limpiar cache si hay user_id en metadata
        if 'user_id' in new_metadata:
            clear_cache_for_user(int(new_metadata['user_id']))
        
        logger.info(f"Document metadata updated: {file_key} by user {current_user.id}")
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error updating document metadata {file_key}: {e}")
        raise

# ============================================
# RUTAS - ESTADÍSTICAS Y ALMACENAMIENTO
# ============================================

@x_buck.route('/api/storage/stats', methods=['GET'])
@require_auth
@check_bucket
def get_storage_stats():
    """Obtener estadísticas de almacenamiento con cache"""
    user_id = current_user.id
    
    # Cache con TTL más corto para stats (1 minuto)
    cache_k = cache_key('stats', user_id)
    cached_data = get_from_cache(cache_k)
    if cached_data:
        return jsonify(cached_data)
    
    storage_client = get_storage_client()
    
    try:
        stats = storage_client.get_user_storage_stats(user_id)
        
        # Cache por 1 minuto
        _session_cache[cache_k] = (stats, datetime.now())
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting storage stats for user {user_id}: {e}")
        raise

@x_buck.route('/api/storage/summary', methods=['GET'])
@require_auth
@check_bucket
def get_storage_summary():
    """Resumen rápido de almacenamiento (optimizado)"""
    user = Users.query.get(current_user.id)
    
    if not user:
        raise FileNotFoundError("Usuario no encontrado")
    
    # Contar archivos y carpetas de forma eficiente
    file_count = File.query.filter_by(user_id=user.id).count()
    folder_count = Folder.query.filter_by(user_id=user.id).count()
    
    return jsonify({
        'used_storage_mb': round(user.used_storage_bytes / (1024 * 1024), 2),
        'total_storage_mb': round(user.get_total_storage_limit_bytes() / (1024 * 1024), 2),
        'remaining_mb': round(user.get_remaining_storage_bytes() / (1024 * 1024), 2),
        'usage_percentage': round(user.get_storage_usage_percentage(), 2),
        'file_count': file_count,
        'folder_count': folder_count,
        'user_type': user.get_user_type()
    }), 200

# ============================================
# RUTAS - ARCHIVED FILES
# ============================================

@x_buck.route('/api/archived', methods=['GET'])
@login_required
def get_archived_files():
    """Return files with status='Archivado' for the current user, with days-remaining countdown."""
    uid = current_user.id
    ck = cache_key('archived', uid)
    cached = get_from_cache(ck)
    if cached:
        return jsonify(cached)

    now = datetime.utcnow()
    files = File.query.filter(
        File.user_id == uid,
        File.status == 'Archivado',
        File.is_trash == False
    ).order_by(File.created_at.desc()).all()

    result = []
    for f in files:
        days_left = None
        if f.expires_at:
            delta = f.expires_at - now
            days_left = max(0, delta.days)
        result.append({
            'id':         f.id,
            'name':       f.original_filename,
            'size':       f.size,
            'mime_type':  f.mime_type,
            'created_at': f.created_at.isoformat() if f.created_at else None,
            'expires_at': f.expires_at.isoformat() if f.expires_at else None,
            'days_left':  days_left,
        })

    data = {'files': result, 'count': len(result)}
    set_cache(ck, data)
    return jsonify(data)

# ============================================
# RUTAS - SIDEBAR COUNTS
# ============================================

@x_buck.route('/api/sidebar-counts', methods=['GET'])
@login_required
def get_sidebar_counts():
    """Sidebar quick-access counts — single round-trip, server-cached 5 min."""
    uid = current_user.id
    ck = cache_key('sidebar', uid)
    cached = get_from_cache(ck)
    if cached:
        return jsonify(cached)

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Auto-move expired archived files to trash (10-day TTL)
    expired_archived = File.query.filter(
        File.user_id == uid,
        File.status == 'Archivado',
        File.is_trash == False,
        File.expires_at != None,
        File.expires_at < now
    ).all()
    if expired_archived:
        for f in expired_archived:
            f.is_trash = True
        db.session.commit()

    # All counts in 2 raw SQL queries (no ORM object overhead)
    from sqlalchemy import text
    file_row = db.session.execute(text("""
        SELECT
          SUM(CASE WHEN is_trash = 0 AND status != 'Archivado' THEN 1 ELSE 0 END) AS total,
          SUM(CASE WHEN is_trash = 0 AND status  = 'Archivado' THEN 1 ELSE 0 END) AS archived,
          SUM(CASE WHEN is_trash = 1                            THEN 1 ELSE 0 END) AS trash_files,
          SUM(CASE WHEN is_trash = 0 AND status != 'Archivado'
                        AND created_at >= :week_ago            THEN 1 ELSE 0 END) AS new_files
        FROM files WHERE user_id = :uid
    """), {'uid': uid, 'week_ago': week_ago}).fetchone()

    folder_row = db.session.execute(text("""
        SELECT
          SUM(CASE WHEN is_trash = 1                         THEN 1 ELSE 0 END) AS trash_folders,
          SUM(CASE WHEN is_trash = 0 AND created_at >= :week_ago THEN 1 ELSE 0 END) AS new_folders
        FROM folders WHERE user_id = :uid
    """), {'uid': uid, 'week_ago': week_ago}).fetchone()

    shared_to_me = db.session.execute(text(
        "SELECT COUNT(*) FROM item_shares WHERE shared_with_id = :uid"
    ), {'uid': uid}).scalar() or 0

    shared_by_me = db.session.execute(text(
        "SELECT COUNT(*) FROM item_shares WHERE owner_id = :uid"
    ), {'uid': uid}).scalar() or 0

    data = {
        'total':        int(file_row.total        or 0),
        'archived':     int(file_row.archived     or 0),
        'trash':        int((file_row.trash_files or 0) + (folder_row.trash_folders or 0)),
        'new_files':    int(file_row.new_files    or 0),
        'new_folders':  int(folder_row.new_folders or 0),
        'shared_to_me': int(shared_to_me),
        'shared_by_me': int(shared_by_me),
    }
    set_cache(ck, data)
    return jsonify(data)

# ============================================
# RUTAS - UTILIDADES
# ============================================

@x_buck.route('/api/health', methods=['GET'])
def health_check():
    """Health check del servicio"""
    try:
        storage_client = get_storage_client()
        
        # Verificar conexión a BD
        db.session.execute('SELECT 1')
        
        # Verificar SeaweedFS
        response = requests.head(f"{storage_client.filer_url}/", timeout=2)
        seaweedfs_ok = response.status_code in [200, 404]
        
        return jsonify({
            'status': 'healthy',
            'seaweedfs': 'connected' if seaweedfs_ok else 'disconnected',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@x_buck.route('/api/cache/clear', methods=['POST'])
@require_auth
@check_bucket
def clear_user_cache():
    """Limpiar cache del usuario actual"""
    clear_cache_for_user(current_user.id)
    logger.info(f"Cache cleared for user {current_user.id}")
    return jsonify({"message": "Cache limpiado exitosamente"}), 200
