"""
Servicio de Imágenes — búsqueda inversa en la web (degradable) + almacenamiento Qdrant.

⚠️ RECONSTRUIDO (sin modelos de ML)
El archivo original se perdió durante una operación de git en el árbol de trabajo y no
existía en git/backups, por lo que esta es una reconstrucción funcional, no byte-idéntica.

Eliminado a propósito (ya NO se cargan estos modelos pesados):
  - SigLIP  (Ateeqq/ai-vs-human-image-detector)  → detección AI-vs-Humano
  - CLIP    (clip-ViT-B-32)                        → embeddings / búsqueda por similitud

Capacidades activas:
  1. Búsqueda inversa de imágenes en la web (requiere el helper ApiRotator + claves;
     mientras no esté disponible el endpoint responde 503 de forma controlada).
  2. CRUD de imágenes indexadas en Qdrant (listar, obtener, borrar por id / por grupo).

Storage: Qdrant (colección vectorial)
"""

import os
import io
import uuid
import base64

from flask import request, jsonify, Blueprint, send_file
from flask_login import login_required
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, PointIdsList,
    Filter, FieldCondition, MatchValue, FilterSelector
)
from PIL import Image
from typing import Optional

x_image = Blueprint('x_image', __name__)

# -------------------
# Configuración Qdrant
# -------------------
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))
COLLECTION = "xplagiax_images_documents"
VECTOR_SIZE = 512  # dimensión histórica de la colección (CLIP ViT-B/32)

# -------------------
# Configuración del sistema de archivos
# -------------------
IMAGE_BASE_PATH = "/mnt/user-data/uploads"

# -------------------
# Búsqueda inversa de imágenes (ApiRotator)
# -------------------
# El helper ApiRotator (rotación SerpApi/Zenserp) ya no está presente en el árbol.
# Se deja la integración preparada: si en el futuro se restaura el helper, basta con
# importarlo aquí e inicializar `api_rotator`. Mientras tanto queda en None y el
# endpoint de búsqueda inversa responde 503 de forma controlada.
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
ZENSERP_KEY = os.getenv("ZENSERP_KEY", "")
api_rotator = None  # ApiRotator no disponible (helper eliminado del proyecto)

# -------------------
# Cliente Qdrant (lazy)
# -------------------
client = None
_qdrant_initialized = False


def get_qdrant_client():
    """Inicialización perezosa del cliente Qdrant."""
    global client, _qdrant_initialized

    if _qdrant_initialized:
        return client

    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=5)

        if not client.collection_exists(collection_name=COLLECTION):
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
        print("✓ Qdrant client initialized successfully")
        _qdrant_initialized = True
        return client
    except Exception as e:
        print(f"⚠️ Qdrant not available: {e}")
        _qdrant_initialized = True  # no reintentar en cada request
        return None


def require_qdrant():
    """Devuelve (client, error_response). error_response es None si Qdrant está disponible."""
    qdrant = get_qdrant_client()
    if qdrant is None:
        return None, (jsonify({"error": "Qdrant service not available"}), 503)
    return qdrant, None


# -------------------
# Helper: localizar el archivo físico de una imagen indexada
# -------------------
def find_image_file(filename: str, group_id: Optional[str] = None) -> Optional[str]:
    """
    Busca un archivo de imagen en las ubicaciones probables.
    Qdrant sólo guarda metadatos (filename/group_id/page), no los bytes, por lo que
    para servir la imagen hay que localizarla en disco.
    """
    if not filename:
        return None

    candidates = []
    if group_id:
        candidates.append(os.path.join(IMAGE_BASE_PATH, group_id, filename))
    candidates.append(os.path.join(IMAGE_BASE_PATH, filename))
    candidates.append(filename)

    for path in candidates:
        if path and os.path.isfile(path):
            return path

    # Búsqueda recursiva como último recurso
    try:
        for root, _dirs, files in os.walk(IMAGE_BASE_PATH):
            if filename in files:
                return os.path.join(root, filename)
    except Exception:
        pass

    return None


def _payload_for(qdrant, point_id):
    """Recupera el payload de un punto por id (o None)."""
    try:
        pts = qdrant.retrieve(collection_name=COLLECTION, ids=[point_id], with_payload=True)
        if pts:
            return pts[0].payload or {}
    except Exception:
        pass
    return None


# ============================================================
# BÚSQUEDA INVERSA DE IMÁGENES (web)
# ============================================================
@x_image.route("/reverse_image_search", methods=["POST"])
@login_required
def reverse_image_search_endpoint():
    """
    Busca imágenes similares en la web (SerpApi/Zenserp vía ApiRotator).

    Estado: el helper ApiRotator fue eliminado del proyecto, por lo que este endpoint
    responde 503 hasta que se restaure. La firma y validaciones se conservan.
    """
    if not api_rotator:
        return jsonify({
            "error": "Reverse image search no disponible: el helper ApiRotator no está "
                     "configurado en este despliegue."
        }), 503

    try:
        image_url = None

        if request.form.get("image_url"):
            image_url = request.form.get("image_url")
        elif "file" in request.files:
            file = request.files["file"]
            file_bytes = file.read()
            b64 = base64.b64encode(file_bytes).decode()
            try:
                img = Image.open(io.BytesIO(file_bytes))
                fmt = (img.format or "jpeg").lower()
            except Exception:
                fmt = "jpeg"
            image_url = f"data:image/{fmt};base64,{b64}"
        else:
            return jsonify({"error": "Se requiere 'file' o 'image_url'"}), 400

        num_results = int(request.form.get("num_results", 10))
        results = api_rotator.reverse_image_search(image_url, num_results)

        return jsonify({
            "status": "success",
            "results": results,
            "usage": api_rotator.get_usage_status()
        }), 200

    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500


# ============================================================
# CRUD DE IMÁGENES INDEXADAS (Qdrant)
# ============================================================
@x_image.route("/get_image/<point_id>", methods=["GET"])
@login_required
def get_image(point_id: str):
    """Sirve el archivo de imagen asociado a un punto de Qdrant."""
    qdrant, error = require_qdrant()
    if error:
        return error

    payload = _payload_for(qdrant, point_id)
    if payload is None:
        return jsonify({"error": "Punto no encontrado"}), 404

    path = find_image_file(payload.get("filename"), payload.get("group_id"))
    if not path:
        return jsonify({"error": "Archivo de imagen no encontrado en disco"}), 404

    return send_file(path)


@x_image.route("/get_image_base64/<point_id>", methods=["GET"])
@login_required
def get_image_base64(point_id: str):
    """Devuelve la imagen asociada a un punto como data URL base64."""
    qdrant, error = require_qdrant()
    if error:
        return error

    payload = _payload_for(qdrant, point_id)
    if payload is None:
        return jsonify({"error": "Punto no encontrado"}), 404

    path = find_image_file(payload.get("filename"), payload.get("group_id"))
    if not path:
        return jsonify({"error": "Archivo de imagen no encontrado en disco"}), 404

    try:
        with open(path, "rb") as f:
            data = f.read()
        ext = (os.path.splitext(path)[1].lstrip(".") or "jpeg").lower()
        b64 = base64.b64encode(data).decode()
        return jsonify({
            "id": point_id,
            "filename": payload.get("filename"),
            "base64": f"data:image/{ext};base64,{b64}"
        }), 200
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500


@x_image.route("/delete_image/<point_id>", methods=["DELETE"])
@login_required
def delete_image(point_id: str):
    """Elimina un punto (imagen) de Qdrant por id."""
    qdrant, error = require_qdrant()
    if error:
        return error

    try:
        qdrant.delete(
            collection_name=COLLECTION,
            points_selector=PointIdsList(points=[point_id])
        )
        return jsonify({"status": "deleted", "id": point_id}), 200
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500


@x_image.route("/clear_collection", methods=["DELETE"])
@login_required
def clear_collection():
    """Vacía por completo la colección de imágenes (recrea la colección)."""
    qdrant, error = require_qdrant()
    if error:
        return error

    try:
        if qdrant.collection_exists(collection_name=COLLECTION):
            qdrant.delete_collection(collection_name=COLLECTION)
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        return jsonify({"status": "cleared", "collection": COLLECTION}), 200
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500


@x_image.route("/delete_by_group", methods=["DELETE"])
@x_image.route("/delete_by_group/<path:group_id>", methods=["DELETE"])
@login_required
def delete_by_group(group_id=None):
    """Elimina todas las imágenes de un grupo (group_id = doc_id) en Qdrant."""
    if group_id is None:
        data = request.get_json(silent=True) or {}
        group_id = data.get("group_id") or request.args.get("group_id")

    if not group_id:
        return jsonify({"error": "group_id requerido"}), 400

    qdrant, error = require_qdrant()
    if error:
        return error

    try:
        qdrant.delete(
            collection_name=COLLECTION,
            points_selector=FilterSelector(
                filter=Filter(must=[
                    FieldCondition(key="group_id", match=MatchValue(value=group_id))
                ])
            )
        )
        return jsonify({"status": "deleted", "group_id": group_id}), 200
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500


@x_image.route("/list_items", methods=["GET"])
@login_required
def list_items():
    """Lista los puntos (imágenes) indexados, opcionalmente filtrados por group_id."""
    qdrant, error = require_qdrant()
    if error:
        return error

    group_id = request.args.get("group_id")
    limit = int(request.args.get("limit", 100))

    try:
        scroll_filter = None
        if group_id:
            scroll_filter = Filter(must=[
                FieldCondition(key="group_id", match=MatchValue(value=group_id))
            ])

        points, _next = qdrant.scroll(
            collection_name=COLLECTION,
            scroll_filter=scroll_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )

        items = []
        for p in points:
            payload = p.payload or {}
            items.append({
                "id": p.id,
                "filename": payload.get("filename", "unknown"),
                "group_id": payload.get("group_id", ""),
                "page": payload.get("page", None)
            })

        return jsonify({"count": len(items), "items": items}), 200
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500


# ============================================================
# HEALTH
# ============================================================
@x_image.route("/health", methods=["GET"])
def health():
    """Estado del servicio (sin modelos de ML)."""
    qdrant, error = require_qdrant()
    if error:
        return jsonify({
            "status": "degraded",
            "qdrant_connected": False,
            "api_rotator_available": api_rotator is not None,
            "collection": COLLECTION
        }), 200

    try:
        qdrant.get_collections()
        return jsonify({
            "status": "healthy",
            "qdrant_connected": True,
            "api_rotator_available": api_rotator is not None,
            "collection": COLLECTION
        }), 200
    except Exception:
        return jsonify({
            "status": "unhealthy",
            "error": "Qdrant no disponible"
        }), 503
