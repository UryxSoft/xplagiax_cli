"""
Copyright (c) 2024 - present URYX TECHNOLOGIES SRL

SeaweedFS Storage Client
Provides file and document storage operations via SeaweedFS Filer HTTP API.
"""

import os
import uuid
import json
import logging
import mimetypes
from datetime import datetime
from typing import Optional, Dict, List, Any

import requests
from flask import send_file
import io

logger = logging.getLogger(__name__)


class SeaweedFSClient:
    """
    Cliente HTTP para interactuar con SeaweedFS Filer.

    Métodos principales:
      - create_folder(path)
      - upload_file(file, user, folder_path)
      - download_file(filename) -> bytes
      - delete_file(filename, user)
      - delete_folder(path)
      - upload_documents(file, user_id, metadata) -> dict
      - upload_document(file, title, author, theme, user_id, doc_id=None) -> dict
      - list_user_documents(user_id) -> list
      - delete_document_by_id(document_id, user_id) -> dict
      - get_document_info(file_key) -> dict
      - download_document(file_key) -> Response
      - update_document_metadata(file_key, new_metadata) -> dict
      - get_user_storage_stats(user_id) -> dict
    """

    def __init__(self, filer_url: str, master_url: str, bucket_name: str):
        self.filer_url = filer_url.rstrip('/')
        self.master_url = master_url.rstrip('/')
        self.bucket_name = bucket_name
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})
        logger.info(f"SeaweedFSClient initialized — filer: {self.filer_url}, bucket: {self.bucket_name}")

    # ------------------------------------------------------------------ #
    #  INTERNAL HELPERS                                                    #
    # ------------------------------------------------------------------ #

    def _filer_path(self, *parts: str) -> str:
        """Construye la URL completa del Filer para un path dado."""
        path = '/'.join(p.strip('/') for p in parts if p)
        return f"{self.filer_url}/{path}"

    def _safe_filename(self, filename: str) -> str:
        """Genera un nombre de archivo único y seguro."""
        ext = os.path.splitext(filename)[1].lower()
        return f"{uuid.uuid4().hex}{ext}"

    def _guess_mime(self, filename: str) -> str:
        mime, _ = mimetypes.guess_type(filename)
        return mime or 'application/octet-stream'

    def _head_size(self, url: str) -> int:
        """Obtiene el tamaño en bytes de un objeto remoto vía HEAD."""
        try:
            r = self.session.head(url, timeout=5)
            return int(r.headers.get('Content-Length', 0))
        except Exception:
            return 0

    # ------------------------------------------------------------------ #
    #  FOLDERS                                                             #
    # ------------------------------------------------------------------ #

    def create_folder(self, path: str) -> str:
        """
        Crea una carpeta en SeaweedFS.
        Retorna el path normalizado (con trailing slash).
        """
        normalized = path.strip('/') + '/'
        url = self._filer_path(self.bucket_name, normalized)
        try:
            # SeaweedFS crea carpetas con un PUT vacío al path con trailing slash
            r = self.session.post(
                url,
                headers={'Content-Type': 'application/octet-stream'},
                data=b'',
                timeout=10
            )
            if r.status_code not in (200, 201, 204):
                logger.warning(f"create_folder: unexpected status {r.status_code} for {url}")
        except requests.RequestException as e:
            logger.error(f"create_folder error: {e}")
            # No lanzamos excepción — SeaweedFS crea la carpeta implícitamente al subir
        return normalized

    def delete_folder(self, path: str) -> bool:
        """Elimina una carpeta (y su contenido) en SeaweedFS."""
        url = self._filer_path(self.bucket_name, path.strip('/'))
        try:
            r = self.session.delete(url, params={'recursive': 'true'}, timeout=15)
            return r.status_code in (200, 204, 404)
        except requests.RequestException as e:
            logger.error(f"delete_folder error: {e}")
            return False

    # ------------------------------------------------------------------ #
    #  FILES (DMS genérico)                                               #
    # ------------------------------------------------------------------ #

    def upload_file(self, file, user, folder_path: str = '') -> Dict:
        """
        Sube un archivo binario a SeaweedFS.

        Retorna dict con:
          file_id, object_name, original_filename, mime_type,
          size, minio_url, storage_info
        """
        original_filename = file.filename
        safe_name = self._safe_filename(original_filename)
        mime_type = self._guess_mime(original_filename)

        # Ruta dentro del bucket: <bucket>/<user_id>/<folder_path>/<safe_name>
        parts = [self.bucket_name, str(user.id)]
        if folder_path:
            parts.append(folder_path.strip('/'))
        parts.append(safe_name)
        object_key = '/'.join(parts)

        url = f"{self.filer_url}/{object_key}"

        file.seek(0)
        file_bytes = file.read()
        size = len(file_bytes)

        try:
            r = self.session.post(
                url,
                files={'file': (safe_name, file_bytes, mime_type)},
                timeout=60
            )
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"upload_file error: {e}")
            raise RuntimeError(f"Error subiendo archivo a SeaweedFS: {e}")

        # Actualizar almacenamiento del usuario si el modelo lo soporta
        try:
            user.used_storage_bytes = (user.used_storage_bytes or 0) + size
            from settings.connections import db
            db.session.commit()
        except Exception as ex:
            logger.warning(f"No se pudo actualizar used_storage_bytes: {ex}")

        return {
            'file_id': safe_name,
            'object_name': safe_name,
            'original_filename': original_filename,
            'mime_type': mime_type,
            'size': size,
            'minio_url': url,
            'storage_info': {
                'bucket': self.bucket_name,
                'key': object_key,
            }
        }

    def download_file(self, filename: str) -> bytes:
        """
        Descarga un archivo por su nombre (object_key relativo o absoluto).
        Retorna los bytes del contenido.
        """
        # Si ya es una URL completa, úsala directamente
        if filename.startswith('http'):
            url = filename
        else:
            url = f"{self.filer_url}/{self.bucket_name}/{filename.lstrip('/')}"

        try:
            r = self.session.get(url, timeout=60)
            r.raise_for_status()
            return r.content
        except requests.RequestException as e:
            logger.error(f"download_file error: {e}")
            raise FileNotFoundError(f"Archivo no encontrado en almacenamiento: {filename}")

    def delete_file(self, filename: str, user=None) -> bool:
        """Elimina un archivo de SeaweedFS y descuenta el storage del usuario."""
        if filename.startswith('http'):
            url = filename
        else:
            url = f"{self.filer_url}/{self.bucket_name}/{filename.lstrip('/')}"

        size = self._head_size(url)

        try:
            r = self.session.delete(url, timeout=10)
            deleted = r.status_code in (200, 204, 404)
        except requests.RequestException as e:
            logger.error(f"delete_file error: {e}")
            return False

        if deleted and user and size:
            try:
                user.used_storage_bytes = max(0, (user.used_storage_bytes or 0) - size)
                from settings.connections import db
                db.session.commit()
            except Exception as ex:
                logger.warning(f"No se pudo decrementar used_storage_bytes: {ex}")

        return deleted

    # ------------------------------------------------------------------ #
    #  DOCUMENTS (con metadata JSON)                                       #
    # ------------------------------------------------------------------ #

    def _document_base_path(self, user_id) -> str:
        return f"{self.bucket_name}/documents/{user_id}"

    def upload_documents(self, file, user_id, metadata: Dict) -> Dict:
        """
        Sube un documento con metadata asociada (versión usada en upload_document endpoint).
        Compatible con la firma: upload_documents(file, user_id, metadata)
        """
        doc_id = metadata.get('document_id') or uuid.uuid4().hex
        return self._store_document(file, user_id, metadata, doc_id)

    def upload_document(self, file, title: str, author: str, theme: str,
                        user_id, doc_id: str = None) -> Dict:
        """
        Sube un documento con metadata explícita (versión usada en endpoint interno).
        Compatible con la firma: upload_document(file, title, author, theme, user_id, doc_id=None)
        """
        if doc_id is None:
            doc_id = uuid.uuid4().hex

        metadata = {
            'title': title,
            'author': author,
            'theme': theme,
            'user_id': str(user_id),
            'document_id': doc_id,
        }
        return self._store_document(file, user_id, metadata, doc_id)

    def _store_document(self, file, user_id, metadata: Dict, doc_id: str) -> Dict:
        """Lógica interna compartida para subir un documento con su metadata."""
        original_filename = file.filename
        safe_name = self._safe_filename(original_filename)
        mime_type = self._guess_mime(original_filename)
        base = self._document_base_path(user_id)

        file_key = f"{base}/{doc_id}/{safe_name}"
        meta_key = f"{base}/{doc_id}/metadata.json"

        file.seek(0)
        file_bytes = file.read()
        size = len(file_bytes)

        file_url = f"{self.filer_url}/{file_key}"
        meta_url = f"{self.filer_url}/{meta_key}"

        # Subir archivo
        try:
            r = self.session.post(
                file_url,
                files={'file': (safe_name, file_bytes, mime_type)},
                timeout=60
            )
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"_store_document upload error: {e}")
            raise RuntimeError(f"Error subiendo documento: {e}")

        # Construir y subir metadata
        full_metadata = {
            **metadata,
            'document_id': doc_id,
            'original_filename': original_filename,
            'stored_filename': safe_name,
            'file_key': file_key,
            'mime_type': mime_type,
            'size': size,
            'uploaded_at': datetime.utcnow().isoformat(),
            'url': file_url,
        }

        try:
            meta_bytes = json.dumps(full_metadata, ensure_ascii=False).encode('utf-8')
            self.session.post(
                meta_url,
                files={'file': ('metadata.json', meta_bytes, 'application/json')},
                timeout=10
            )
        except Exception as e:
            logger.warning(f"_store_document metadata upload warning: {e}")

        # Actualizar storage del usuario
        try:
            from modules.models.model import Users
            from settings.connections import db
            user = Users.query.get(user_id)
            if user:
                user.used_storage_bytes = (user.used_storage_bytes or 0) + size
                db.session.commit()
        except Exception as ex:
            logger.warning(f"No se pudo actualizar used_storage_bytes: {ex}")

        return {
            'document_id': doc_id,
            'key': file_key,
            'url': file_url,
            'original_filename': original_filename,
            'mime_type': mime_type,
            'size': size,
            **{k: v for k, v in full_metadata.items() if k not in ('file_key',)},
        }

    def list_user_documents(self, user_id) -> List[Dict]:
        """Lista todos los documentos de un usuario leyendo el Filer."""
        base_url = f"{self.filer_url}/{self._document_base_path(user_id)}"
        documents = []

        try:
            r = self.session.get(base_url, params={'pretty': 'y'}, timeout=10)
            if r.status_code == 404:
                return []
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.warning(f"list_user_documents error listing base: {e}")
            return []

        entries = data.get('Entries') or []
        for entry in entries:
            doc_id = entry.get('FullPath', '').rstrip('/').split('/')[-1]
            if not doc_id:
                continue

            meta = self._fetch_metadata(user_id, doc_id)
            if meta:
                documents.append(meta)
            else:
                documents.append({
                    'document_id': doc_id,
                    'title': doc_id,
                    'uploaded_at': entry.get('Mtime', ''),
                })

        return documents

    def _fetch_metadata(self, user_id, doc_id: str) -> Optional[Dict]:
        """Descarga el metadata.json de un documento específico."""
        meta_url = f"{self.filer_url}/{self._document_base_path(user_id)}/{doc_id}/metadata.json"
        try:
            r = self.session.get(meta_url, timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.debug(f"_fetch_metadata error for {doc_id}: {e}")
        return None

    def delete_document_by_id(self, document_id: str, user_id) -> Dict:
        """Elimina un documento completo (archivo + metadata) por su ID."""
        base_url = f"{self.filer_url}/{self._document_base_path(user_id)}/{document_id}"

        # Obtener metadata antes de borrar (para descontar size)
        meta = self._fetch_metadata(user_id, document_id)
        size = meta.get('size', 0) if meta else 0

        try:
            r = self.session.delete(base_url, params={'recursive': 'true'}, timeout=15)
            deleted = r.status_code in (200, 204, 404)
        except requests.RequestException as e:
            logger.error(f"delete_document_by_id error: {e}")
            raise RuntimeError(f"Error eliminando documento: {e}")

        if deleted and size:
            try:
                from modules.models.model import Users
                from settings.connections import db
                user = Users.query.get(user_id)
                if user:
                    user.used_storage_bytes = max(0, (user.used_storage_bytes or 0) - size)
                    db.session.commit()
            except Exception as ex:
                logger.warning(f"No se pudo decrementar used_storage_bytes: {ex}")

        return {
            'deleted': deleted,
            'document_id': document_id,
            'message': 'Documento eliminado correctamente' if deleted else 'Error al eliminar'
        }

    def get_document_info(self, file_key: str) -> Dict:
        """Obtiene información/metadata de un documento por su file_key."""
        url = f"{self.filer_url}/{file_key.lstrip('/')}"
        try:
            r = self.session.head(url, timeout=5)
            if r.status_code == 404:
                raise FileNotFoundError(f"Documento no encontrado: {file_key}")
            return {
                'file_key': file_key,
                'url': url,
                'size': int(r.headers.get('Content-Length', 0)),
                'mime_type': r.headers.get('Content-Type', 'application/octet-stream'),
                'last_modified': r.headers.get('Last-Modified', ''),
            }
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"get_document_info error: {e}")
            raise RuntimeError(f"Error obteniendo información del documento: {e}")

    def download_document(self, file_key: str):
        """
        Descarga un documento y retorna un objeto Flask Response (send_file).
        Compatible con: return storage_client.download_document(file_key)
        """
        url = f"{self.filer_url}/{file_key.lstrip('/')}"
        filename = file_key.split('/')[-1]
        mime_type = self._guess_mime(filename)

        try:
            r = self.session.get(url, timeout=60, stream=True)
            if r.status_code == 404:
                raise FileNotFoundError(f"Documento no encontrado: {file_key}")
            r.raise_for_status()
            content = r.content
        except FileNotFoundError:
            raise
        except requests.RequestException as e:
            logger.error(f"download_document error: {e}")
            raise RuntimeError(f"Error descargando documento: {e}")

        return send_file(
            io.BytesIO(content),
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )

    def update_document_metadata(self, file_key: str, new_metadata: Dict) -> Dict:
        """Actualiza el metadata.json asociado a un documento."""
        # Derivar la ruta del metadata desde el file_key
        parts = file_key.rstrip('/').split('/')
        # Reemplazar el filename por metadata.json
        parts[-1] = 'metadata.json'
        meta_key = '/'.join(parts)
        meta_url = f"{self.filer_url}/{meta_key.lstrip('/')}"

        # Obtener metadata actual
        existing = {}
        try:
            r = self.session.get(meta_url, timeout=5)
            if r.status_code == 200:
                existing = r.json()
        except Exception:
            pass

        # Merge y persistir
        merged = {**existing, **new_metadata, 'updated_at': datetime.utcnow().isoformat()}

        try:
            meta_bytes = json.dumps(merged, ensure_ascii=False).encode('utf-8')
            self.session.post(
                meta_url,
                files={'file': ('metadata.json', meta_bytes, 'application/json')},
                timeout=10
            )
        except Exception as e:
            logger.error(f"update_document_metadata error: {e}")
            raise RuntimeError(f"Error actualizando metadata: {e}")

        return {'updated': True, 'file_key': file_key, 'metadata': merged}

    # ------------------------------------------------------------------ #
    #  STORAGE STATS                                                       #
    # ------------------------------------------------------------------ #

    def get_user_storage_stats(self, user_id) -> Dict:
        """Retorna estadísticas de almacenamiento del usuario."""
        try:
            from modules.models.model import Users
            user = Users.query.get(user_id)
            if not user:
                raise FileNotFoundError(f"Usuario {user_id} no encontrado")

            used = user.used_storage_bytes or 0
            total = user.get_total_storage_limit_bytes()
            remaining = user.get_remaining_storage_bytes()
            percentage = user.get_storage_usage_percentage()

            return {
                'user_id': user_id,
                'used_bytes': used,
                'used_mb': round(used / (1024 * 1024), 2),
                'total_bytes': total,
                'total_mb': round(total / (1024 * 1024), 2),
                'remaining_bytes': remaining,
                'remaining_mb': round(remaining / (1024 * 1024), 2),
                'usage_percentage': round(percentage, 2),
                'user_type': user.get_user_type() if hasattr(user, 'get_user_type') else user.user_type,
            }
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"get_user_storage_stats error: {e}")
            raise RuntimeError(f"Error obteniendo estadísticas: {e}")
