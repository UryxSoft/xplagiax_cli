"""
Copyright (c) 2025 - present URYX TECHNOLOGIES SRL
"""
import json
import os
import re
import shutil
import time
import logging
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from flask import Flask, Blueprint, request, jsonify, url_for, session, render_template,redirect,flash, send_file, abort, current_app
from flask_login import current_user, login_required
import requests
import tempfile
import uuid
from itsdangerous import URLSafeSerializer, BadSignature
#import clamd  # pip install clamd
from datetime import datetime, timedelta
from modules.doc_service.modules.doc_analysis_task import DocAnalysisTask
#from .modules.integrated_doc_analysis import DocAnalysisTask
from settings.utilities import verify_token
from modules.bucket_service.bucket_routes import get_storage_client, clear_cache_for_user
from flask_cors import CORS
from typing import Dict, Any, List
from settings.connections import db, limiter
from modules.models.model import Users, DocumentAnalysis, ClassifiedParagraph, Folder, File, CollaborativePermission, Tag, SmartRule, FileTag, ItemShare, ItemHistory

logger = logging.getLogger(__name__)

# Lazy cache for sentence-transformer models (loaded once per process)
_qdrant_model_cache: Dict[str, Any] = {}

x_doc = Blueprint('x_doc', __name__)
#socketio = SocketIO()  # Crear instancia de SocketIO sin ningún argumento
#CORS(x_doc)  # Configura CORS para permitir solicitudes desde cualquier origen
#socketio = SocketIO(x_doc)
# Session global reutilizable para mejor rendimiento
session_pool = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=2
)
session_pool.mount('http://', adapter)
session_pool.mount('https://', adapter)

# Configuración de ClamAV
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx',".xps", 'epub', 'mobi', 'fb2', 'cbz'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Define la carpeta de carga en la misma ruta que el script
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads/uploads_analysis')
SAVE_FOLDER   = os.path.join(os.path.dirname(__file__), 'uploads/uploads_save')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def make_user_dir(user_id):   
    user_directory = os.path.join(UPLOAD_FOLDER, str(user_id))
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
        
def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
def get_user_data():
    """Obtiene los datos del usuario autenticado actual - VERSIÓN ROBUSTA"""
    from flask_login import current_user
    
    if not current_user or not current_user.is_authenticated: #print("get_user_data: Usuario no autenticado")
        return {
            'id': None, 'email': '', 'name': '', 'lastname': '', 'institute': '', 'country': '', 'user_type': ''
        }
    
    try: #MEJORAR CON COMPLEMENTOS SI ESTÁN DISPONIBLES
        try:
            getter = ComplementsGetter()
            getter.set_param('country_id', getattr(current_user, 'country', ''))
            getter.set_param('institute_id', getattr(current_user, 'institute', ''))
            results = getter.get_complements()
            institute_name = results.get('institute_name', '')
            country_name = results.get('country_name', '')
        except Exception as e: #print(f"Error obteniendo complementos: {e}")
            institute_name = getattr(current_user, 'institute', '') or ''
            country_name = getattr(current_user, 'country', '') or ''
        user_data = {
            'id': current_user.id,
            'email': current_user.email or '',
            'name': current_user.name or '',
            'lastname': getattr(current_user, 'lastname', '') or '',
            'institute': institute_name,
            'country': country_name,
            'user_type': getattr(current_user, 'user_type', '') or 'Starter'
        }#print(f"get_user_data exitosa para usuario {user_data['email']}")
        return user_data
        
    except Exception as e:#print(f"Error en get_user_data: {e}")
        return {
            'id': None, 'email': '','name': '', 'lastname': '', 'institute': '', 'country': '', 'user_type': ''
        }
     
def save_file_with_timestamp(file, document_name, user_id, use_upload_folder): #=True
    """
    Save a file with timestamp in the appropriate directory without consuming the file stream.
    This version copies the file content to disk but resets the file pointer after reading.
    """
    import unicodedata
    import re
    
    def sanitize_filename(filename):
        """
        Sanitiza un nombre de archivo para que sea ASCII-safe.
        """
        # Normalizar Unicode
        normalized = unicodedata.normalize('NFKD', filename)
        # Convertir a ASCII
        ascii_name = normalized.encode('ASCII', 'ignore').decode('ASCII')
        # Remover caracteres no permitidos
        safe_name = re.sub(r'[^\w\s\-\.]', '', ascii_name)
        # Limpiar espacios múltiples
        safe_name = re.sub(r'\s+', '_', safe_name)
        return safe_name
    
    def obtener_nombre(nombre_archivo):
        return os.path.splitext(nombre_archivo)[0]
    
    def obtener_extension(nombre_archivo):
        _, extension = os.path.splitext(nombre_archivo)
        return extension

    try:
        safe_document_name = sanitize_filename(document_name)
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        if use_upload_folder==True:
            base_folder = UPLOAD_FOLDER 
        else:
            base_folder = SAVE_FOLDER
        
        user_directory = os.path.join(base_folder, str(user_id), f"{obtener_nombre(safe_document_name)}_{timestamp}")
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)
        
        user_img_directory = os.path.join(base_folder, str(user_id), f"{obtener_nombre(safe_document_name)}_{timestamp}","images")
        if not os.path.exists(user_img_directory):
            os.makedirs(user_img_directory)    
            
        safe_document_name = safe_document_name.strip().replace(' ', '_')
        filepath = os.path.join(user_directory, f"{obtener_nombre(safe_document_name)}_{timestamp}{ obtener_extension(safe_document_name)}")
        
        # Save the file content while preserving the file pointer position
        file_content = file.read()  # Read the content
        file.seek(0)  # Reset file pointer to the beginning
        
        with open(filepath, 'wb') as f:
            f.write(file_content)
        #print(os.path.splitext(filepath)[0] + '.pdf')
        return filepath, user_img_directory 
    except Exception as e:
        return str(e), None

def insert_analysis_from_json(user_id, json_data, db_session=None):
    """
    Insertar un análisis completo desde los datos JSON
    FORMATO DE IA ESPERADO:
    {
      'ai_model': 'text-davinci-003',
      'confidence': 99.85,
      'is_human': False,
      'text': [page_num, paragraph_num, 'texto completo...']
    }
    
    FORMATO SIN IA (SOLO BD):
    {
      'page_number': 1,
      'paragraph_number': 1,
      'text': 'texto completo...',
      'is_human': None,
      ...
    }
    """
    if db_session is None:
        from modules.settings_service.connections import db
        db_session = db.session
    
    # Asegurar que el user_id coincida
    if json_data.get('user_id') != user_id:
        json_data['user_id'] = user_id
    
    # Determinar tipo de análisis
    analysis_type = json_data.get('analysis_type', 'full')
    
    logger.debug(f"🔄 Insertando análisis tipo: {analysis_type}")
    
    # Crear el análisis principal
    analysis = DocumentAnalysis(
        analysis_id=json_data['analysis_id'],
        analysis_date=datetime.fromisoformat(json_data['analysis_date']),
        user_id=json_data['user_id'],
        analysis_type=analysis_type,
        
        # Metadata
        title=json_data['metadata'].get('title'),
        author=json_data['metadata'].get('author'),
        creator=json_data['metadata'].get('creator'),
        producer=json_data['metadata'].get('producer'),
        subject=json_data['metadata'].get('subject'),
        keywords=json_data['metadata'].get('keywords'),
        format=json_data['metadata'].get('format'),
        creation_date=json_data['metadata'].get('creationDate'),
        mod_date=json_data['metadata'].get('modDate'),
        encryption=json_data['metadata'].get('encryption'),
        trapped=json_data['metadata'].get('trapped'),
        
        # Información del documento
        pages=json_data.get('pages'),
        language=json_data.get('language'),
        success=json_data.get('success', True),
        
        # Resumen
        total_paragraphs=json_data['summary'].get('total_paragraphs', 0),
        human_count=json_data['summary'].get('human_count', 0),
        ai_count=json_data['summary'].get('ai_count', 0),
        average_confidence=json_data['summary'].get('average_confidence', 0.0),
        
        # JSON fields
        annotations=json_data.get('annotations', []),
        images=json_data.get('images', []),
        urls=json_data.get('urls', [])
    )
    
    db_session.add(analysis)
    db_session.flush()
    logger.debug(f"✅ DocumentAnalysis creado con ID: {analysis.id}")
    
    # Guardar párrafos
    paragraphs_saved = 0
    if json_data.get('classified_paragraphs'):
        total_paragraphs = len(json_data['classified_paragraphs'])
        logger.debug(f"📝 Procesando {total_paragraphs} párrafos...")
        
        for idx, paragraph_data in enumerate(json_data['classified_paragraphs']):
            
            # ========================================
            # CASO 1: FORMATO DE IA (DICCIONARIO CON 'ai_model')
            # ========================================
            if isinstance(paragraph_data, dict) and 'ai_model' in paragraph_data:
                
                # Extraer el campo 'text' que es una lista [page, para_num, texto]
                text_field = paragraph_data.get('text', [])
                
                # Validar que text sea una lista con al menos 3 elementos
                if isinstance(text_field, (list, tuple)) and len(text_field) >= 3:
                    page_num = int(text_field[0]) if text_field[0] is not None else 1
                    para_num = int(text_field[1]) if text_field[1] is not None else idx + 1
                    text_content = str(text_field[2]) if text_field[2] is not None else ""
                else:
                    logger.debug(f"⚠️ Párrafo {idx}: 'text' no es lista o está incompleta: {text_field}")
                    continue
                
                # Extraer valores de clasificación
                is_human = paragraph_data.get('is_human', False)
                confidence = paragraph_data.get('confidence')
                ai_model = paragraph_data.get('ai_model')
                
                # Calcular probabilidades
                if confidence is not None:
                    confidence_float = float(confidence)
                    if is_human:
                        human_prob = confidence_float
                        ai_prob = 100.0 - confidence_float
                    else:
                        ai_prob = confidence_float
                        human_prob = 100.0 - confidence_float
                else:
                    human_prob = None
                    ai_prob = None
                    confidence_float = None
                
                # Crear model_scores
                model_scores = None
                if ai_model and confidence_float is not None:
                    model_scores = {ai_model: confidence_float}
                
                # Crear y guardar párrafo
                paragraph = ClassifiedParagraph(
                    analysis_id=json_data['analysis_id'],
                    page_number=page_num,
                    paragraph_number=para_num,
                    text=text_content[:10000],
                    is_human=bool(is_human),
                    human_probability=human_prob,
                    ai_probability=ai_prob,
                    predicted_model=str(ai_model) if ai_model else None,
                    model_scores=model_scores,
                    final_confidence=confidence_float
                )
                
                db_session.add(paragraph)
                paragraphs_saved += 1
                
                # Debug detallado
                if idx == 0 or (idx + 1) % 10 == 0:
                    logger.debug(f"  ✅ Párrafo {idx + 1}/{total_paragraphs}:")
                    logger.debug(f"     - page={page_num}, num={para_num}")
                    logger.debug(f"     - text_length={len(text_content)} chars")
                    logger.debug(f"     - is_human={is_human}, confidence={confidence_float}%")
                    logger.debug(f"     - model={ai_model}")
            
            # ========================================
            # CASO 2: FORMATO SIN IA (DICCIONARIO CON 'page_number')
            # ========================================
            elif isinstance(paragraph_data, dict) and 'page_number' in paragraph_data:
                
                text_content = paragraph_data.get('text', '')
                
                # Validar que text sea string directo
                if not isinstance(text_content, str):
                    text_content = str(text_content)
                
                paragraph = ClassifiedParagraph(
                    analysis_id=json_data['analysis_id'],
                    page_number=int(paragraph_data.get('page_number', 1)),
                    paragraph_number=int(paragraph_data.get('paragraph_number', idx + 1)),
                    text=text_content[:10000],
                    is_human=None,
                    human_probability=None,
                    ai_probability=None,
                    predicted_model=None,
                    model_scores=None,
                    final_confidence=None
                )
                
                db_session.add(paragraph)
                paragraphs_saved += 1
                
                if idx == 0 or (idx + 1) % 10 == 0:
                    logger.debug(f"  📄 Párrafo {idx + 1}/{total_paragraphs} (sin IA):")
                    logger.debug(f"     - text_length={len(text_content)} chars")
            
            # ========================================
            # CASO 3: FORMATO NO RECONOCIDO
            # ========================================
            else:
                logger.debug(f"❌ Párrafo {idx}: formato no reconocido")
                logger.debug(f"   - Tipo: {type(paragraph_data)}")
                if isinstance(paragraph_data, dict):
                    logger.debug(f"   - Claves: {paragraph_data.keys()}")
                continue
    
    # Commit final
    db_session.commit()
    logger.debug(f"\n{'='*60}")
    logger.debug(f"✅ GUARDADO COMPLETADO")
    logger.debug(f"{'='*60}")
    logger.debug(f"   Analysis ID: {json_data['analysis_id']}")
    logger.debug(f"   Tipo: {analysis_type}")
    logger.debug(f"   Párrafos guardados: {paragraphs_saved}/{json_data['summary'].get('total_paragraphs', 0)}")
    logger.debug(f"{'='*60}\n")
    
    return analysis

# FUNCIÓN AUXILIAR PARA OBTENER ESTADÍSTICAS DEL ANÁLISIS
def get_analysis_statistics(classified_document):
    """
    Obtiene estadísticas del documento clasificado
    """
    paragraphs = classified_document.get('paragraphs', [])
    
    if not paragraphs:
        return {}
    
    human_count = 0
    ai_count = 0
    confidences = []
    ai_models = {}
    
    for paragraph in paragraphs:
        # Verificar que el párrafo tenga los 9 elementos esperados
        if len(paragraph) >= 9:  # >= 9 para manejar posibles elementos adicionales
            is_human = paragraph[3]
            confidence = paragraph[8]
            ai_model = paragraph[6]
            
            if is_human:
                human_count += 1
            else:
                ai_count += 1
                # Manejar correctamente valores nulos en ai_model
                if ai_model is not None and ai_model != 'None' and ai_model != 'null':
                    ai_models[ai_model] = ai_models.get(ai_model, 0) + 1
            
            # Asegurar que confidence es un número válido
            if confidence is not None and isinstance(confidence, (int, float)):
                confidences.append(confidence)
    
    # Calcular porcentajes
    total_paragraphs = len(paragraphs)
    human_percentage = round((human_count / total_paragraphs) * 100, 1) if total_paragraphs > 0 else 0
    ai_percentage = round((ai_count / total_paragraphs) * 100, 1) if total_paragraphs > 0 else 0
    
    # Calcular estadísticas de confianza
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0
    min_confidence = min(confidences) if confidences else 0
    max_confidence = max(confidences) if confidences else 0
    
    return {
        'total_paragraphs': total_paragraphs,
        'human_count': human_count,
        'ai_count': ai_count,
        'human_percentage': human_percentage,
        'ai_percentage': ai_percentage,
        'average_confidence': avg_confidence,
        'min_confidence': min_confidence,
        'max_confidence': max_confidence,
        'detected_ai_models': ai_models
    }
    
def db_batch_search_(es_document: Dict[str, Any], search_type: str = 'fuzzy') -> Dict[str, Any]:
    """
    Uso de la API web-batch-search con soporte para diferentes tipos de búsqueda.
    
    Args:
        es_document: Documento con la estructura que tienes
        search_type: Tipo de búsqueda ('fuzzy', 'morelike', 'semantic', 'paraphrase')
    """
    try:
        metadata = es_document.get("metadata", {})
        
        # Adaptar el documento al formato esperado
        payload = {
            "texts": es_document.get("texts", []),
            "index_name": metadata.get("index_name", "essays_index"),
            "countrys": metadata.get("countrys"),
            "institutes": metadata.get("institutes"),
            "languages": [es_document.get("language")] if es_document.get("language") else None,
            "theme": metadata.get("theme"),
            "max_workers": metadata.get("max_workers", 10),
            "search_type": search_type  # Nuevo parámetro
        }
        
        # Parámetros adicionales para búsquedas con embeddings
        if search_type in ['semantic', 'paraphrase']:
            payload["k"] = metadata.get("k", 10)
            payload["num_candidates"] = metadata.get("num_candidates", 100)
        
        response = requests.post(
            'http://127.0.0.1:5000/x_search/api/search/parallel',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300
        )
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "result": data
        }
            
    except requests.exceptions.Timeout:
        return {"error": "Timeout: La petición tardó más de 5 minutos"}
    except requests.exceptions.ConnectionError:
        return {"error": "Error de conexión al servidor"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"Error HTTP {e.response.status_code}", "details": str(e)}
    except Exception as e:
        return {"error": f"Error inesperado: {str(e)}"}

def db_batch_search(es_document: Dict[str, Any], search_type: str = 'fuzzy') -> Dict[str, Any]:
    """
    Realiza búsqueda en batch de múltiples párrafos contra Qdrant.
    
    MEJORADO:
    - Validación de entrada
    - Logging detallado
    - Manejo de errores robusto
    - Estadísticas de resultados
    
    Args:
        es_document: Documento con estructura:
            {
                "texts": List[str],           # Lista de párrafos (REQUERIDO)
                "language": str,              # Idioma (opcional)
                "metadata": {                 # Metadatos opcionales
                    "index_name": str,
                    "countrys": List[str],
                    "institutes": List[str],
                    "theme": str,
                    "max_workers": int,
                    "k": int,                 # Para semantic/paraphrase
                    "num_candidates": int     # Para semantic/paraphrase
                }
            }
        search_type: Tipo de búsqueda ('fuzzy', 'morelike', 'semantic', 'paraphrase')
    
    Returns:
        Dict con estructura:
            {
                "success": bool,
                "result": List[Dict],         # Resultados de búsqueda
                "stats": {                    # Estadísticas opcionales
                    "total_paragraphs": int,
                    "with_matches": int,
                    "without_matches": int,
                    "avg_score": float
                },
                "error": str                  # Solo si success=False
            }
    """
    import logging
    logger = logging.getLogger('db_batch_search')
    
    try:
        # ========================================
        # 1. VALIDACIÓN DE ENTRADA
        # ========================================
        
        texts = es_document.get("texts", [])
        
        # Validación crítica: verificar que texts existe y no está vacío
        if not texts:
            logger.error("❌ No se proporcionaron textos para buscar")
            return {
                "success": False,
                "error": "No se encontraron párrafos para buscar (campo 'texts' vacío o ausente)",
                "result": []
            }
        
        # Validar que texts es una lista de strings
        if not isinstance(texts, list):
            logger.error(f"❌ 'texts' debe ser una lista, recibido: {type(texts)}")
            return {
                "success": False,
                "error": f"Campo 'texts' inválido: esperado list, recibido {type(texts).__name__}",
                "result": []
            }
        
        # Filtrar elementos no-string y vacíos
        valid_texts = [
            str(text).strip() 
            for text in texts 
            if text and str(text).strip()
        ]
        
        if not valid_texts:
            logger.error("❌ Todos los textos están vacíos después de filtrado")
            return {
                "success": False,
                "error": "Todos los textos proporcionados están vacíos",
                "result": []
            }
        
        if len(valid_texts) < len(texts):
            logger.warning(
                f"⚠️  Filtrados {len(texts) - len(valid_texts)} textos vacíos/inválidos"
            )
        
        # ========================================
        # 2. PREPARAR PAYLOAD
        # ========================================
        
        metadata = es_document.get("metadata", {})
        language = es_document.get("language")
        
        payload = {
            "texts": valid_texts,  # ✅ Usar textos validados
            "index_name": metadata.get("index_name", "essays_index"),
            "search_type": search_type,
            "max_workers": metadata.get("max_workers", min(32, len(valid_texts) * 2))
        }
        
        # Agregar filtros opcionales (solo si tienen valor)
        if metadata.get("countrys"):
            payload["countrys"] = metadata["countrys"]
        
        if metadata.get("institutes"):
            payload["institutes"] = metadata["institutes"]
        
        if language:
            payload["languages"] = [language]
        
        if metadata.get("theme"):
            payload["theme"] = metadata["theme"]
        
        # Parámetros específicos para búsquedas con embeddings
        if search_type in ['semantic', 'paraphrase']:
            payload["k"] = metadata.get("k", 10)
            payload["num_candidates"] = metadata.get("num_candidates", 100)
        
        # ========================================
        # 3. LOGGING DE SOLICITUD
        # ========================================
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 INICIANDO BÚSQUEDA BATCH")
        logger.info(f"{'='*70}")
        logger.info(f"   Tipo: {search_type}")
        logger.info(f"   Índice: {payload['index_name']}")
        logger.info(f"   Total párrafos: {len(valid_texts)}")
        logger.info(f"   Idioma: {language or 'N/A'}")
        logger.info(f"   Workers: {payload['max_workers']}")
        
        if search_type in ['semantic', 'paraphrase']:
            logger.info(f"   k: {payload['k']}")
            logger.info(f"   num_candidates: {payload['num_candidates']}")
        
        # Mostrar preview del primer texto
        first_text = valid_texts[0][:100] + "..." if len(valid_texts[0]) > 100 else valid_texts[0]
        logger.info(f"   Primer párrafo: {first_text}")
        logger.info(f"{'='*70}\n")
        
        # ========================================
        # 4. REALIZAR SOLICITUD
        # ========================================
        
        response = requests.post(
            'http://127.0.0.1:5000/x_search/api/search/parallel',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minutos
        )
        
        # Verificar código de estado
        response.raise_for_status()
        
        # ========================================
        # 5. PROCESAR RESULTADOS
        # ========================================
        
        data = response.json()
        
        # Validar estructura de respuesta
        if not isinstance(data, list):
            logger.error(f"❌ Formato de respuesta inválido: esperado list, recibido {type(data)}")
            return {
                "success": False,
                "error": f"Formato de respuesta inválido del servidor",
                "result": []
            }
        
        # ========================================
        # 6. CALCULAR ESTADÍSTICAS
        # ========================================
        
        total_paragraphs = len(valid_texts)
        with_matches = 0
        scores = []
        
        for item in data:
            matches = item.get('matches', [])
            if matches and len(matches) > 0:
                first_match = matches[0]
                score = first_match.get('normalized_score', 0)
                
                if score > 0:
                    with_matches += 1
                    scores.append(score)
        
        without_matches = total_paragraphs - with_matches
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # ========================================
        # 7. LOGGING DE RESULTADOS
        # ========================================
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ BÚSQUEDA COMPLETADA")
        logger.info(f"{'='*70}")
        logger.info(f"   Total párrafos: {total_paragraphs}")
        logger.info(f"   Con matches: {with_matches} ({with_matches/total_paragraphs*100:.1f}%)")
        logger.info(f"   Sin matches: {without_matches} ({without_matches/total_paragraphs*100:.1f}%)")
        logger.info(f"   Score promedio: {avg_score:.4f}")
        
        # Mostrar top 3 matches
        if with_matches > 0:
            logger.info(f"\n   📊 Top 3 Matches:")
            count = 0
            for item in data:
                if count >= 3:
                    break
                
                matches = item.get('matches', [])
                if matches and matches[0].get('normalized_score', 0) > 0:
                    match = matches[0]
                    count += 1
                    logger.info(
                        f"      [{count}] Score: {match.get('normalized_score', 0):.4f} | "
                        f"Title: {match.get('title', 'N/A')[:50]}"
                    )
        
        logger.info(f"{'='*70}\n")
        
        # ========================================
        # 8. RETORNAR RESULTADO
        # ========================================
        
        return {
            "success": True,
            "result": data,
            "stats": {
                "total_paragraphs": total_paragraphs,
                "with_matches": with_matches,
                "without_matches": without_matches,
                "avg_score": round(avg_score, 4),
                "match_rate": round(with_matches / total_paragraphs * 100, 2) if total_paragraphs > 0 else 0
            }
        }
        
    # ========================================
    # 9. MANEJO DE ERRORES
    # ========================================
    
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout: La petición tardó más de 5 minutos")
        return {
            "success": False,
            "error": "Timeout: La petición tardó más de 5 minutos",
            "result": []
        }
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Error de conexión: {str(e)}")
        return {
            "success": False,
            "error": "Error de conexión al servidor de búsqueda",
            "details": str(e),
            "result": []
        }
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else 'unknown'
        error_text = e.response.text if e.response else str(e)
        
        logger.error(f"❌ Error HTTP {status_code}: {error_text[:200]}")
        
        return {
            "success": False,
            "error": f"Error HTTP {status_code}",
            "details": error_text[:500],  # Limitar texto de error
            "result": []
        }
    
    except ValueError as e:
        # Error de JSON parsing
        logger.error(f"❌ Error parseando respuesta: {str(e)}")
        return {
            "success": False,
            "error": "Error parseando respuesta del servidor",
            "details": str(e),
            "result": []
        }
    
    except Exception as e:
        # Cualquier otro error
        logger.error(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": f"Error inesperado: {str(e)}",
            "result": []
        }


# ============================================
# BÚSQUEDA DIRECTA EN QDRANT (texto completo)
# ============================================

def _get_embedding_model(vector_name: str):
    """Lazy-loads and caches sentence-transformer models to avoid reloading per request."""
    MODEL_MAP = {
        'semantic':   'sentence-transformers/all-MiniLM-L6-v2',
        'paraphrase': 'sentence-transformers/paraphrase-MiniLM-L3-v2',
    }
    model_id = MODEL_MAP.get(vector_name, MODEL_MAP['semantic'])
    if model_id not in _qdrant_model_cache:
        from sentence_transformers import SentenceTransformer
        _qdrant_model_cache[model_id] = SentenceTransformer(model_id)
    return _qdrant_model_cache[model_id]


def _chunk_text(text: str, max_words: int = 300) -> List[str]:
    """Splits text into chunks of at most max_words words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words]).strip()
        if len(chunk) > 20:
            chunks.append(chunk)
    return chunks


def qdrant_search_fulltext(full_text: str, search_type: str = 'semantic', top_k: int = 10) -> Dict[str, Any]:
    """
    Searches Qdrant essays_index for documents similar to full_text.

    - Chunks the text into ~300-word segments
    - Encodes each chunk with the matching sentence-transformer model
    - Searches Qdrant using the appropriate named vector (semantic / paraphrase)
    - Aggregates results by document_id keeping the highest score per document
    - fuzzy / morelike map to semantic search since those were Elasticsearch-specific

    Returns:
        {
            "success": bool,
            "result": List[Dict],   # sorted by score desc
            "stats": { ... },
            "error": str            # only when success=False
        }
    """
    _log = logging.getLogger('qdrant_search_fulltext')

    QDRANT_HOST = os.environ.get('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.environ.get('QDRANT_PORT', 6333))
    COLLECTION  = 'essays_index'

    # Map findex_subcheck values to Qdrant named vectors
    vector_name = search_type if search_type in ('semantic', 'paraphrase') else 'semantic'

    try:
        if not full_text or not full_text.strip():
            return {"success": False, "error": "Texto vacío, nada que buscar", "result": []}

        chunks = _chunk_text(full_text, max_words=300)
        if not chunks:
            return {"success": False, "error": "No se pudo segmentar el texto", "result": []}

        _log.info(f"🔍 Qdrant search — vector={vector_name}  chunks={len(chunks)}  top_k={top_k}")

        # Encode all chunks in one batch
        model = _get_embedding_model(vector_name)
        embeddings = model.encode(
            chunks,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

        # For each chunk, search Qdrant; aggregate by document_id keeping best score
        doc_best: Dict[str, Dict] = {}

        for chunk_val, embedding in zip(chunks, embeddings):
            hits = client.search(
                collection_name=COLLECTION,
                query_vector=(vector_name, embedding.tolist()),
                limit=top_k,
                with_payload=True,
            )
            for hit in hits:
                doc_id = hit.payload.get('document_id', str(hit.id))
                score  = round(float(hit.score), 4)
                if doc_id not in doc_best or score > doc_best[doc_id]['score']:
                    doc_best[doc_id] = {
                        'document_id':      doc_id,
                        'score':            score,
                        'normalized_score': score,
                        'source_file':      hit.payload.get('source_file', ''),
                        'author':           hit.payload.get('author', ''),
                        'institution':      hit.payload.get('institution', ''),
                        'country':          hit.payload.get('country', ''),
                        'language':         hit.payload.get('language', ''),
                        'theme':            hit.payload.get('theme', ''),
                        'document_type':    hit.payload.get('document_type', ''),
                        'date_published':   hit.payload.get('date_published', ''),
                        'matched_content':  hit.payload.get('content', '')[:300],
                        'query_preview':    chunk_val[:100],
                    }

        results = sorted(doc_best.values(), key=lambda x: x['score'], reverse=True)

        _log.info(f"✅ Qdrant search done — {len(results)} unique documents matched")

        return {
            "success": True,
            "result": results,
            "stats": {
                "chunks_searched":    len(chunks),
                "unique_documents":   len(results),
                "search_type":        vector_name,
                "top_score":          results[0]['score'] if results else 0.0,
            }
        }

    except Exception as e:
        _log.error(f"❌ Qdrant search failed: {e}", exc_info=True)
        return {"success": False, "error": "Error interno del servidor", "result": []}


# ============================================
# FUNCIÓN AUXILIAR: VALIDAR FORMATO DE DOCUMENTO
# ============================================

def validate_es_document(es_document: Dict[str, Any]) -> tuple[bool, str]:
    """
    ✅ VERSIÓN CORREGIDA: Validación menos restrictiva
    
    Valida que el documento tenga el formato correcto para búsqueda.
    
    Args:
        es_document: Diccionario con estructura esperada
    
    Returns:
        (is_valid, error_message)
    """
    import logging
    logger = logging.getLogger('validate_es_document')
    
    # 1. Validar que es un diccionario
    if not isinstance(es_document, dict):
        error = f"es_document debe ser dict, recibido {type(es_document).__name__}"
        logger.error(f"❌ {error}")
        return False, error
    
    # 2. Verificar que existe el campo 'texts'
    if "texts" not in es_document:
        error = "Campo 'texts' es requerido"
        logger.error(f"❌ {error}")
        return False, error
    
    texts = es_document["texts"]
    
    # 3. Validar que 'texts' es una lista
    if not isinstance(texts, list):
        error = f"Campo 'texts' debe ser list, recibido {type(texts).__name__}"
        logger.error(f"❌ {error}")
        return False, error
    
    # 4. ✅ CAMBIO CRÍTICO: Aceptar listas vacías temporalmente
    if not texts:
        logger.warning(f"⚠️  Campo 'texts' está vacío")
        # ❌ ANTES: return False, "Campo 'texts' está vacío"
        # ✅ AHORA: Permitir continuar (se filtrará después)
    
    # 5. Contar textos válidos (strings no vacíos)
    valid_texts = []
    for idx, text_item in enumerate(texts):
        # Manejar diferentes formatos
        if isinstance(text_item, str):
            text = text_item
        elif isinstance(text_item, (list, tuple)) and len(text_item) >= 3:
            text = text_item[2]  # Formato [page, para, text]
        else:
            logger.debug(f"  Texto {idx}: formato no reconocido: {type(text_item)}")
            continue
        
        # Validar contenido
        if text and isinstance(text, str) and len(text.strip()) > 5:  # ✅ Mínimo 5 chars
            valid_texts.append(text_item)
    
    # 6. ✅ CAMBIO CRÍTICO: Requerir AL MENOS 1 texto válido
    if len(valid_texts) == 0:
        error = "Ningún texto válido encontrado en 'texts' (todos vacíos o muy cortos)"
        logger.error(f"❌ {error}")
        logger.error(f"   Total items: {len(texts)}")
        logger.error(f"   Válidos: 0")
        return False, error
    
    # 7. Log de éxito
    logger.info(f"✅ Validación exitosa:")
    logger.info(f"   Total items: {len(texts)}")
    logger.info(f"   Válidos: {len(valid_texts)}")
    
    if len(valid_texts) < len(texts):
        logger.warning(f"   ⚠️  Filtrados: {len(texts) - len(valid_texts)} textos inválidos")
    
    return True, ""

def extract_texts_from_paragraphs(paragraphs):
    """
    Extrae solo el texto de una lista de párrafos en diferentes formatos.
    
    Formatos soportados:
    - Tuplas: (page, para_num, text) → extrae text
    - Listas: [page, para_num, text] → extrae text
    - Strings: 'text' → devuelve directamente
    - Diccionarios: {'text': 'text'} → extrae text
    
    Args:
        paragraphs: Lista de párrafos en cualquier formato
    
    Returns:
        Lista de strings con solo los textos
    """
    import logging
    logger = logging.getLogger('extract_texts')
    
    if not paragraphs:
        logger.warning("⚠️  Lista de párrafos vacía")
        return []
    
    extracted_texts = []
    
    for idx, para in enumerate(paragraphs):
        try:
            # CASO 1: Tupla o lista con 3 elementos [page, para_num, text]
            if isinstance(para, (tuple, list)) and len(para) >= 3:
                text = str(para[2]).strip()
                
                if text and len(text) > 5:  # Mínimo 5 caracteres
                    extracted_texts.append(text)
                else:
                    logger.debug(f"  Párrafo {idx}: texto muy corto o vacío")
            
            # CASO 2: String directo
            elif isinstance(para, str):
                text = para.strip()
                
                if text and len(text) > 5:
                    extracted_texts.append(text)
                else:
                    logger.debug(f"  Párrafo {idx}: string vacío")
            
            # CASO 3: Diccionario con clave 'text'
            elif isinstance(para, dict) and 'text' in para:
                text = str(para['text']).strip()
                
                if text and len(text) > 5:
                    extracted_texts.append(text)
                else:
                    logger.debug(f"  Párrafo {idx}: dict con texto vacío")
            
            # CASO 4: Formato no reconocido
            else:
                logger.warning(
                    f"  Párrafo {idx}: formato no reconocido "
                    f"(tipo: {type(para).__name__})"
                )
                
        except Exception as e:
            logger.error(f"  Error procesando párrafo {idx}: {e}")
            continue
    
    # Log final
    logger.info(f"✅ Extracción completada:")
    logger.info(f"   Total input: {len(paragraphs)}")
    logger.info(f"   Textos extraídos: {len(extracted_texts)}")
    logger.info(f"   Filtrados: {len(paragraphs) - len(extracted_texts)}")
    
    # Mostrar preview del primer texto
    if extracted_texts:
        preview = extracted_texts[0][:80] + "..." if len(extracted_texts[0]) > 80 else extracted_texts[0]
        logger.info(f"   Primer texto: {preview}")
    
    return extracted_texts

def web_batch_search(es_document: Dict[str, Any]) -> None:
    """Uso de la API web-batch-search"""
    # Datos de ejemplo
    try:        
        response = requests.post(
            'http://127.0.0.1:5000/x_search/api/web-batch-search',
            json = es_document,
            headers ={'Content-Type': 'application/json'},
            timeout = 300  # 5 minutos de timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return response.json()
            
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None   
    except Exception as e:
        return str(e)
    
def img_db_single_search(img_file, similarity_threshold: float = 0.4):
    """
    Uso de la API img-single-search in database QDRANT
    img_file: objeto tipo FileStorage (request.files['analysis_file'])
    """
    try:
        files = {
            "file": (img_file.filename, img_file.stream, img_file.mimetype)
        }
        data = {"similarity_threshold": similarity_threshold}

        response = requests.post(
            "http://127.0.0.1:5000/enhanced_img/search",
            files=files,
            data=data,
            timeout=300
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return response.json()
            
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None   
    except Exception as e:
        return str(e)

def img_ai_single_search(img_file) ->None:
    """Uso de la API img-single-search in database QDRANT"""
    try:        
        response = requests.post(
            'http://127.0.0.1:5000/enhanced_img/search',
            json = img_file,
            headers ={'Content-Type': 'application/json'},
            timeout = 300  # 5 minutos de timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return response.json()
            
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None   
    except Exception as e:
        return str(e)

def img_web_single_search(img_file) ->None:
    """Uso de la API img-single-search in database QDRANT"""
    try:        
        response = requests.post(
            'http://127.0.0.1:5000/enhanced_img/search',
            json = img_file,
            headers ={'Content-Type': 'application/json'},
            timeout = 300  # 5 minutos de timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return response.json()
            
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None   
    except Exception as e:
        return str(e)

@x_doc.route('/serve_analysis/<path:filepath>')
@login_required
def serve_analysis(filepath):
    try:
        #print(f"\n=== SERVE ANALYSIS CALLED ===")
        #print(f"Filepath: {filepath}")

        # BUGFIX (seguridad): esta ruta no tenia @login_required NI verificaba dueno,
        # y `filepath` siempre empieza con el user_id (ver comentario abajo) -> antes,
        # cualquiera (ni siquiera logueado) que adivinara/enumerara una ruta podia ver
        # el result.html o las imagenes de OTRO usuario. Se exige login + que el primer
        # segmento de la ruta coincida con el usuario autenticado.
        owner_id = filepath.split('/', 1)[0]
        if not owner_id.isdigit() or int(owner_id) != current_user.id:
            abort(403, description="Access denied")

        base_path = os.path.join(
            current_app.root_path,
            'modules/doc_service/uploads/uploads_analysis'
        )
        
        #print(f"Base path: {base_path}")
        
        # filepath incluye user_id y todo: "32/Fratal_2025-10-16-00-09-58/images/image_page_3_image_1.png"
        file_path = safe_join(base_path, filepath)
        
        #print(f"Full file path: {file_path}")
        #print(f"File exists: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path):
            abort(404, description="Archivo no encontrado")
        
        if not os.path.isfile(file_path):
            abort(403, description="Acceso denegado")
        
        # Detectar mimetype automáticamente
        import mimetypes
        mimetype, _ = mimetypes.guess_type(file_path)
        
        # Si no se puede detectar, usar un default
        if not mimetype:
            # Defaults por extensión
            ext = os.path.splitext(file_path)[1].lower()
            mimetypes_map = {
                '.html': 'text/html',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.svg': 'image/svg+xml',
                '.pdf': 'application/pdf'
            }
            mimetype = mimetypes_map.get(ext, 'application/octet-stream')
        
        #print(f"Mimetype: {mimetype}")
        #print(f"==============================\n")
        
        return send_file(file_path, mimetype=mimetype)
        
    except Exception as e:
        #print(f"Error sirviendo archivo: {e}")
        import traceback
        traceback.print_exc()
        abort(500, description="Error al cargar el archivo")

def convert_absolute_to_url(absolute_path, user_id=None):
    """
    Convierte: /path/to/uploads_analysis/32/Fratal_2025-10-15-22-49-24/result.html
    A: /x_doc/serve_analysis/32/Fratal_2025-10-15-22-49-24/result.html
    """
    try:
        # Verificar que absolute_path sea string
        if not isinstance(absolute_path, str):
            #print(f"Error: absolute_path no es string, es {type(absolute_path)}")
            return None
        
        # Extraer la parte después de 'uploads_analysis/'
        if 'uploads_analysis/' not in absolute_path:
            #print(f"Error: Path doesn't contain 'uploads_analysis/': {absolute_path}")
            return None
        
        parts = absolute_path.split('uploads_analysis/')
        
        if len(parts) < 2:
            #print(f"Error: Ruta inválida después de split: {parts}")
            return None
        
        # Obtener la ruta relativa completa (ya incluye user_id)
        relative_path = parts[1]
        
        # Construir URL simple
        url = f"/x_doc/serve_analysis/{relative_path}"
        
        return url
        
    except Exception as e:
        #print(f"Exception en convert_absolute_to_url: {e}")
        import traceback
        traceback.print_exc()
        return None

def convert_images_to_urls(images, user_id):
    """
    Convierte imágenes a URLs, manejando diferentes formatos.
    """
    images_urls = []
    
    if not images:
        return images_urls
    
    for img in images:
        # Si es un string (ruta directa)
        if isinstance(img, str):
            url = convert_absolute_to_url(img, user_id)
            if url:
                images_urls.append(url)
        
        # Si es un diccionario con 'path' o 'file_path'
        elif isinstance(img, dict):
            img_path = img.get('path') or img.get('file_path') or img.get('url')
            if img_path:
                url = convert_absolute_to_url(img_path, user_id)
                if url:
                    # Mantener el formato dict pero con URL
                    img_dict = img.copy()
                    img_dict['url'] = url
                    images_urls.append(img_dict)
        #else:
        #    print(f"Warning: Formato de imagen desconocido: {type(img)}")
    
    return images_urls

@x_doc.route('/uploadanalysis_', methods=['POST'])   
def upload_analysis_():
    """
    Endpoint para cargar, procesar y guardar un documento en múltiples sistemas:
    1. Qdrant (para indexación y búsqueda) - PRIMERO
    2. MinIO (servicio de almacenamiento de objetos) - SEGUNDO, usando el ID de Qdrant
    3. Sistema de archivos local
    """
    #try:
        # Verificar autenticación del usuario
    user_id = current_user.id
    
    if user_id is None:
        return jsonify({'error': 'Unauthenticated user or session expired'}), 401
    
    # 1. Verificar si el usuario puede realizar análisis
    if not current_user.can_perform_analysis():
        stats = current_user.get_analysis_stats()
        return jsonify({
            'success': False,
            'error': 'Daily analysis limit reached',
            'limit_reached': True,
            'stats': stats
        }), 403
        
    # Obtener datos del usuario desde el token
    user_data = get_user_data()
    if not user_data:
        return jsonify({'error': 'Could not get user information'}), 400
    
    # Verificar que se haya enviado un archivo
    if 'analysis_file' not in request.files:
        return jsonify({'error': 'The file was not found in the request'}), 400
        
    file = request.files['analysis_file']
    if file.filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    EXTENSIONS = {
            '.pdf': ('document', 'pdf'),
            '.doc': ('document', 'word'),
            '.docx': ('document', 'word'),
            '.fb2': ('document', 'fb2'),
            '.mobi': ('document', 'mobi'),
            '.epub': ('document', 'epub'),
            '.jpg': ('image', 'image'),
            '.jpeg': ('image', 'image'),
            '.png': ('image', 'image'),
            '.webp': ('image', 'image')
        }

    # Obtener extensión y validar
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in EXTENSIONS:
        return jsonify({'error': f'File type not supported: {ext}'}), 400

    file_type, document_type = EXTENSIONS[ext]
    
    theme_filter = use_db_search = use_detect_ai = image_filter = use_web_source = False
    
    analysis_types = request.form.getlist('analysis_types[]')
    
    findex_subcheck = request.form.get('findex_subcheck')  # SOLO UNO
   
    # Verificar cada tipo con condiciones IF
    if 'search_source' in analysis_types:
        use_db_search = True
    
    if 'detect_ai' in analysis_types:
        use_detect_ai = True
    
    if 'analysis_image' in analysis_types:
        image_filter = True
    
    if 'web_source' in analysis_types:
        use_web_source = True

    # Procesamiento según tipo
    if file_type == 'document':
        # Crear directorio del usuario si no existe
        make_user_dir(user_id)
        
        #if document_type == 'pdf':#    print("Procesando archivo PDF...")#elif document_type == 'word':# print("Procesando documento Word...")# Guardar archivo en sistema de archivos local
        path, img_path = save_file_with_timestamp(file, file.filename, user_id, use_upload_folder=True)
        if isinstance(path, str) and img_path is None:
            return jsonify({'error': f'Error saving file: {path}'}), 500
        
        # Procesar y extraer contenido del documento
            #try:
        doc_analyzer = DocAnalysisTask(userid = user_id,  file_or_url = path,  upload_folder = img_path, analysis_or_save = True, theme_return  = theme_filter)

        #paragraphs, metadata, language, annotations, images, urls 
        document_data = doc_analyzer.extract_info()
        #print("RUTA DE LAS IMAGES " + str(img_path))

        # Extraer datos del primer (y único) elemento
        doc_info = document_data[0]
        paragraphs = doc_info.get("paragraphs", [])
        metadata = doc_info.get("metadata", {})
        language = doc_info.get("idiom", "unknown")
        annotations = doc_info.get("annotations", [])
        images = doc_info.get("images", [])
        urls = doc_info.get("urls", [])
        pages = doc_info.get("pages", "unknown")
        theme = doc_info.get("theme", "unknown")
        result_view = doc_info.get("result_view", "unknown")
        #preview_info =  doc_info.get("preview_info")
        
        # Preparar documento para Qdrant - igual que antes
        current_date = datetime.now().strftime('%Y-%m-%d')
        es_document = {
            "user_id": user_id,
            "metadata": metadata, 
            "texts": paragraphs, 
            "language": language, 
            "annotations": annotations, 
            "images": images,
            "urls": urls,
            "pages": pages,
            "analysis_date": current_date,
            "result_view" : result_view
        }

        #print(es_document)
        # Indexar documento en Qdrant - PRIMERO
        # Inicializar variables antes de las condiciones
        results_ai = None
        results_db = None
        html_url = None
        images_urls = None
        analysis_id = str(uuid.uuid4())  # Generar ID único
        
        html_url = convert_absolute_to_url(result_view, user_id)
        images_urls = convert_images_to_urls(images, user_id)

        if use_detect_ai == True:
            response_aitext = requests.post(
                'http://127.0.0.1:5000/x_aitestpro/api/classify-batch-doc',
                json = es_document, 
                headers = {'Content-Type': 'application/json'},
                timeout = 300  # 5 minutos de timeout
            )
            classified_document = response_aitext.json()
                    
            # Preparar respuesta con estadísticas
            summary = classified_document.get('classification_summary', {})
            
            paragraphs_raw = classified_document.get('paragraphs', [])
          
            if os.path.splitext(path)[0] != '.pdf':   
                new_path = os.path.splitext(path)[0] + '.pdf'
            
            results_ai = {
                'success': True,
                'classified_paragraphs': paragraphs_raw, #classified_document.get('paragraphs', []),
                'summary': summary
            }

        if use_db_search == True:

            # Búsqueda fuzzy
            if findex_subcheck in ('morelike', 'semantic', 'paraphrase', 'fuzzy'):
                results_db = db_batch_search(es_document, search_type=findex_subcheck)
            else:
                # Manejo de casos no reconocidos
                results_db = db_batch_search(es_document, search_type='fuzzy')
            logger.debug(results_db)
            
            # Convertir a URL accesible
            html_url = convert_absolute_to_url(result_view, user_id)
            
            # Convertir las rutas de las imágenes
            images_urls = convert_images_to_urls(images, user_id)    
            

        # Incrementar contador si hubo éxito en cualquiera de las operaciones
        if (results_ai and results_ai.get("success")) or (results_db and results_db.get("success")):
            current_user.increment_analysis_count()

        # Obtener stats actualizados
        stats = current_user.get_analysis_stats()
        
        # ===== GUARDAR EN BASE DE DATOS =====
        # Guardar si se realizó CUALQUIER tipo de análisis
        if (use_detect_ai or use_db_search) and (results_ai or results_db):
            try:
                # Determinar tipo de análisis
                if use_detect_ai and use_db_search:
                    analysis_type = 'full'
                elif use_detect_ai:
                    analysis_type = 'ai_only'
                else:
                    analysis_type = 'db_only'
                
                logger.debug(f"\n{'='*80}")
                logger.debug(f"💾 PREPARANDO GUARDADO EN BD")
                logger.debug(f"{'='*80}")
                logger.debug(f"   Tipo de análisis: {analysis_type}")
                logger.debug(f"   use_detect_ai: {use_detect_ai}")
                logger.debug(f"   use_db_search: {use_db_search}")
                
                # ===== CASO 1: CON IA (ai_only o full) =====
                if results_ai and results_ai.get("success"):
                    summary = results_ai['summary']
                    classified_paragraphs = results_ai['classified_paragraphs']
                    
                    logger.debug(f"   ✅ Análisis CON IA detectado")
                    logger.debug(f"   Total párrafos clasificados: {len(classified_paragraphs)}")
                    
                    # Verificar formato del primer párrafo
                    if classified_paragraphs:
                        first_para = classified_paragraphs[0]
                        logger.debug(f"   Formato primer párrafo: {type(first_para)}")
                        if isinstance(first_para, dict):
                            logger.debug(f"   Claves: {first_para.keys()}")
                            # Verificar que tenga el formato esperado del servicio de IA
                            if 'text' in first_para and isinstance(first_para['text'], (list, tuple)):
                                logger.debug(f"   ✅ Formato de IA válido: text=[{first_para['text'][0]}, {first_para['text'][1]}, '...']")
                            else:
                                logger.debug(f"   ⚠️ Formato inesperado en 'text': {type(first_para.get('text'))}")
                
                # ===== CASO 2: SOLO BD (db_only) =====
                else:
                    logger.debug(f"   📋 Análisis SOLO BD (sin clasificación IA)")
                    
                    # Crear resumen básico
                    summary = {
                        'total_paragraphs': len(paragraphs),
                        'human_count': 0,
                        'ai_count': 0,
                        'average_confidence': 0.0
                    }
                    
                    # Crear párrafos SIN clasificación - FORMATO DICCIONARIO SIMPLE
                    classified_paragraphs = []
                    for idx, para_text in enumerate(paragraphs):
                        classified_paragraphs.append({
                            'page_number': 1,  # Por defecto página 1 (mejora esto si tienes info de páginas)
                            'paragraph_number': idx + 1,
                            'text': para_text,  # ✅ Texto directo, NO en lista
                            # Campos de IA en None
                            'is_human': None,
                            'human_probability': None,
                            'ai_probability': None,
                            'predicted_model': None,
                            'model_scores': None,
                            'final_confidence': None
                        })
                    
                    logger.debug(f"   Total párrafos sin clasificar: {len(classified_paragraphs)}")
                
                # Preparar JSON completo para guardar
                json_data = {
                    'analysis_id': analysis_id,
                    'analysis_date': current_date,
                    'user_id': user_id,
                    'analysis_type': analysis_type,
                    'metadata': metadata,
                    'pages': pages,
                    'language': language,
                    'success': True,
                    'summary': summary,
                    'annotations': annotations,
                    'images': images_urls or [],
                    'urls': urls,
                    'classified_paragraphs': classified_paragraphs
                }
                
                logger.debug(f"\n   📦 JSON preparado:")
                logger.debug(f"      - analysis_id: {analysis_id}")
                logger.debug(f"      - analysis_type: {analysis_type}")
                logger.debug(f"      - total_paragraphs: {summary.get('total_paragraphs')}")
                logger.debug(f"      - human_count: {summary.get('human_count')}")
                logger.debug(f"      - ai_count: {summary.get('ai_count')}")
                logger.debug(f"      - classified_paragraphs: {len(classified_paragraphs)} items")
                logger.debug(f"{'='*80}\n")
                
                # Llamar a la función de guardado
                from modules.settings_service.connections import db
                saved_analysis = insert_analysis_from_json(user_id, json_data, db_session=db.session)
                
                logger.debug(f"\n{'='*80}")
                logger.debug(f"✅ GUARDADO EXITOSO")
                logger.debug(f"{'='*80}")
                logger.debug(f"   Analysis ID: {analysis_id}")
                logger.debug(f"   Tipo: {analysis_type}")
                logger.debug(f"   DB ID: {saved_analysis.id}")
                logger.debug(f"{'='*80}\n")
                
            except Exception as e:
                logger.debug(f"\n{'='*80}")
                logger.debug(f"❌ ERROR EN GUARDADO")
                logger.debug(f"{'='*80}")
                logger.debug(f"   Error: {str(e)}")
                import traceback
                traceback.print_exc()
                logger.debug(f"{'='*80}\n")
                
                # Rollback en caso de error
                try:
                    db.session.rollback()
                    logger.debug("   ↩️  Rollback ejecutado")
                except Exception as rb_error:
                    logger.debug(f"   ⚠️  Error en rollback: {rb_error}")
        else:
            logger.debug(f"\nℹ️  No se guardó en BD:")
            logger.debug(f"   use_detect_ai: {use_detect_ai}")
            logger.debug(f"   use_db_search: {use_db_search}")
            logger.debug(f"   results_ai: {'present' if results_ai else 'absent'}")
            logger.debug(f"   results_db: {'present' if results_db else 'absent'}\n")

        # Return unificado para ambos casos
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'user_id': user_id,
            'language': language,
            'result_ai': results_ai or [],
            'result_db': (results_db.get("result") if results_db else []),
            'result_view': html_url or '',
            'annotations': annotations,
            'images': images_urls or [],
            'urls': urls,
            'pages': pages,
            'analysis_date': current_date,
            'metadata': metadata,
            'theme': theme,
            'stats': stats
        }), 200
        
    elif file_type == 'image':
       results = img_db_single_search(file)   # le pasas el FileStorage
       return jsonify(results), 200           #siempre devuelve JSON
    else:
        return jsonify({'error': 'Unsupported file type'}), 400

@x_doc.route('/uploadanalysis', methods=['POST'])   
def upload_analysis():
    """
    Endpoint completo y optimizado para análisis de documentos.
    
    Funcionalidades:
    - Análisis de similitud con Qdrant (párrafo por párrafo)
    - Detección de contenido generado por IA
    - Análisis de imágenes (opcional)
    - Búsqueda en web (opcional)
    - Guardado automático en base de datos
    
    Mejoras implementadas:
    - Validación robusta de entrada
    - Logging detallado
    - Estadísticas agregadas
    - Manejo de errores específico
    - Formato correcto para búsqueda párrafo por párrafo
    """
    
    import logging
    logger = logging.getLogger('upload_analysis')
    
    try:
        # ==========================================
        # 1. VALIDACIÓN DE USUARIO Y AUTENTICACIÓN
        # ==========================================
        
        user_id = current_user.id
        
        if user_id is None:
            return jsonify({'error': 'Unauthenticated user or session expired'}), 401
        
        # Verificar límite de análisis diarios
        if not current_user.can_perform_analysis():
            stats = current_user.get_analysis_stats()
            return jsonify({
                'success': False,
                'error': 'Daily analysis limit reached',
                'limit_reached': True,
                'stats': stats
            }), 403
        
        # Obtener datos del usuario
        user_data = get_user_data()
        if not user_data:
            return jsonify({'error': 'Could not get user information'}), 400
        
        # ==========================================
        # 2. VALIDACIÓN DE ARCHIVO
        # ==========================================
        
        if 'analysis_file' not in request.files:
            return jsonify({'error': 'The file was not found in the request'}), 400
        
        file = request.files['analysis_file']
        if file.filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Extensiones soportadas
        EXTENSIONS = {
            '.pdf': ('document', 'pdf'),
            '.doc': ('document', 'word'),
            '.docx': ('document', 'word'),
            '.fb2': ('document', 'fb2'),
            '.mobi': ('document', 'mobi'),
            '.epub': ('document', 'epub'),
            '.jpg': ('image', 'image'),
            '.jpeg': ('image', 'image'),
            '.png': ('image', 'image'),
            '.webp': ('image', 'image')
        }
        
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in EXTENSIONS:
            return jsonify({'error': f'File type not supported: {ext}'}), 400
        
        file_type, document_type = EXTENSIONS[ext]
        
        # ==========================================
        # 3. CONFIGURACIÓN DE ANÁLISIS
        # ==========================================
        
        # Tipos de análisis solicitados
        analysis_types = request.form.getlist('analysis_types[]')
        findex_subcheck = request.form.get('findex_subcheck', 'fuzzy')
        
        # Flags de análisis
        use_db_search = 'search_source' in analysis_types
        use_detect_ai = 'detect_ai' in analysis_types
        image_filter = 'analysis_image' in analysis_types
        use_web_source = 'web_source' in analysis_types
        theme_filter = False  # Configurar según necesidad
        
        # ==========================================
        # 4. PROCESAMIENTO SEGÚN TIPO DE ARCHIVO
        # ==========================================
        
        if file_type == 'document':
            # ========================================
            # 4A. PROCESAMIENTO DE DOCUMENTOS
            # ========================================
            
            # Crear directorio del usuario
            make_user_dir(user_id)
            
            # Guardar archivo localmente
            path, img_path = save_file_with_timestamp(
                file, 
                file.filename, 
                user_id, 
                use_upload_folder=True
            )
            
            if isinstance(path, str) and img_path is None:
                return jsonify({'error': f'Error saving file: {path}'}), 500
            
            # Extraer contenido del documento
            doc_analyzer = DocAnalysisTask(
                userid=user_id,
                file_or_url=path,
                upload_folder=img_path,
                analysis_or_save=True,
                theme_return=theme_filter
            )
            
            document_data = doc_analyzer.extract_info()
            doc_info = document_data[0]
            
            # Extraer información
            paragraphs = doc_info.get("paragraphs", [])
            metadata = doc_info.get("metadata", {})
            language = doc_info.get("idiom", "unknown")
            annotations = doc_info.get("annotations", [])
            images = doc_info.get("images", [])
            urls = doc_info.get("urls", [])
            pages = doc_info.get("pages", "unknown")
            theme = doc_info.get("theme", "unknown")
            result_view = doc_info.get("result_view", "unknown")

            # Build a single full-text string from all paragraphs
            # Paragraphs are tuples: (page_num, para_num, text)
            full_text = ' '.join(
                str(p[2]).strip() for p in paragraphs
                if isinstance(p, (tuple, list)) and len(p) >= 3 and len(str(p[2]).strip()) > 5
            )

            # Generar ID único para este análisis
            analysis_id = str(uuid.uuid4())
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Convertir rutas a URLs
            html_url = convert_absolute_to_url(result_view, user_id)
            images_urls = convert_images_to_urls(images, user_id)
            
            # Variables para resultados
            results_ai = None
            results_db = None
            
            # ========================================
            # 5. ANÁLISIS DE SIMILITUD EN BASE DE DATOS
            # ========================================
            
            if use_db_search:
                results_db = qdrant_search_fulltext(
                    full_text,
                    search_type=findex_subcheck,
                    top_k=10,
                )
            
            # ========================================
            # 6. DETECCIÓN DE CONTENIDO GENERADO POR IA
            # ========================================
            
            if use_detect_ai:
                
                # Formato para servicio de IA
                ai_document = {
                    "user_id": user_id,
                    "metadata": metadata,
                    "text": full_text,
                    "language": language,
                    "pages": pages
                }
                
                try:
                    response_aitext = requests.post(
                        'http://127.0.0.1:5000/x_aitestpro/api/classify-batch-doc',
                        json=ai_document,
                        headers={'Content-Type': 'application/json'},
                        timeout=300
                    )
                    
                    response_aitext.raise_for_status()
                    classified_document = response_aitext.json()
                    summary = classified_document.get('classification_summary', {})
                    paragraphs_raw = classified_document.get('paragraphs', [])
                    
                    results_ai = {
                        'success': True,
                        'classified_paragraphs': paragraphs_raw,
                        'summary': summary
                    }
                    
                except Exception as e:
                    results_ai = {
                        'success': False,
                        'error': str(e)
                    }
            
            # ========================================
            # 7. INCREMENTAR CONTADOR DE ANÁLISIS
            # ========================================
            
            if (results_ai and results_ai.get("success")) or (results_db and results_db.get("success")):
                current_user.increment_analysis_count()
            
            # Obtener stats actualizados
            stats = current_user.get_analysis_stats()
            
            # ========================================
            # 8. GUARDAR EN BASE DE DATOS
            # ========================================
            
            if (use_detect_ai or use_db_search) and (results_ai or results_db):
                try:                    
                    # Determinar tipo de análisis
                    if use_detect_ai and use_db_search:
                        analysis_type = 'full'
                    elif use_detect_ai:
                        analysis_type = 'ai_only'
                    else:
                        analysis_type = 'db_only'
                    
                    logger.info(f"   Tipo análisis: {analysis_type}")
                    
                    # Preparar datos base
                    json_data = {
                        'analysis_id': analysis_id,
                        'analysis_date': current_date,
                        'user_id': user_id,
                        'metadata': metadata,
                        'pages': pages,
                        'language': language,
                        'success': True,
                        'annotations': annotations,
                        'images': images_urls or [],
                        'urls': urls
                    }
                    
                    # Agregar datos de IA o preparar párrafos sin clasificación
                    if results_ai and results_ai.get('success'):
                        json_data.update({
                            'analysis_type': analysis_type,
                            'summary': results_ai['summary'],
                            'classified_paragraphs': results_ai['classified_paragraphs']
                        })
                        logger.info(f"   ✓ Datos de IA agregados")
                    else:
                        # Store full text as a single unclassified entry
                        json_data.update({
                            'analysis_type': analysis_type,
                            'summary': {
                                'total_paragraphs': 1,
                                'human_count': 0,
                                'ai_count': 0,
                                'average_confidence': 0.0
                            },
                            'classified_paragraphs': [{
                                'page_number': 1,
                                'paragraph_number': 1,
                                'text': full_text,
                                'is_human': None,
                                'human_probability': None,
                                'ai_probability': None,
                                'predicted_model': None,
                                'model_scores': None,
                                'final_confidence': None
                            }]
                        })
                        logger.info(f"   ✓ Texto completo sin clasificación preparado")
                    
                    # Agregar estadísticas de búsqueda
                    if results_db and results_db.get("success") and "stats" in results_db:
                        json_data['search_stats'] = results_db['stats']
                        logger.info(f"   ✓ Estadísticas de búsqueda agregadas")
                    
                    # Guardar en base de datos
                    from modules.settings_service.connections import db
                    saved_analysis = insert_analysis_from_json(
                        user_id,
                        json_data,
                        db_session=db.session
                    )
                    
                    
                except Exception as e:

                    
                    import traceback
                    traceback.print_exc()
                    
                    # Rollback en caso de error
                    try:
                        db.session.rollback()
                        logger.error(f"   ↩️  Rollback ejecutado")
                    except Exception as rb_error:
                        logger.error(f"   ⚠️  Error en rollback: {rb_error}")
                    
                    logger.error(f"{'='*70}\n")
            
            # ========================================
            # 9. PREPARAR RESPUESTA FINAL
            # ========================================
            
            response_data = {
                'success': True,
                'analysis_id': analysis_id,
                'user_id': user_id,
                'language': language,
                'result_view': html_url or '',
                'full_text': full_text,
                'annotations': annotations,
                'images': images_urls or [],
                'urls': urls,
                'pages': pages,
                'analysis_date': current_date,
                'metadata': metadata,
                'theme': theme,
                'stats': stats
            }
            
            # Agregar resultados de IA
            if results_ai:
                response_data['result_ai'] = results_ai
            else:
                response_data['result_ai'] = []
            
            # Agregar resultados de búsqueda
            if results_db:
                response_data['result_db'] = results_db.get("result", [])
                
                # Incluir estadísticas para frontend
                if results_db.get("success") and "stats" in results_db:
                    response_data['search_stats'] = results_db['stats']
            else:
                response_data['result_db'] = []
            
            logger.info(f"✅ Respuesta preparada y enviada al cliente\n")
            
            return jsonify(response_data), 200
        
        elif file_type == 'image':
            # ========================================
            # 4B. PROCESAMIENTO DE IMÁGENES
            # ========================================
            
            results = img_db_single_search(file)
            
            return jsonify(results), 200
        
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
    
    except Exception as e:
        
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': 'Unexpected error during document processing',
            'details': str(e)
        }), 500


@x_doc.route('/extract_text', methods=['POST'])
@login_required
def extract_text():
    """Extrae el texto plano de un documento (PDF/DOC/DOCX/…).

    Sirve para que el análisis de documentos use los mismos servicios de texto
    del inputWrapper (AI detection en /x_doc/analyze_text y FinderX en
    /x_doc/finderx_check): el navegador sube el archivo, este endpoint devuelve
    el texto extraído, y el front lo envía a esos servicios.
    """
    try:
        user_id = current_user.id
        if user_id is None:
            return jsonify({'error': 'Unauthenticated user or session expired'}), 401

        if 'analysis_file' not in request.files:
            return jsonify({'error': 'The file was not found in the request'}), 400
        file = request.files['analysis_file']
        if file.filename == '':
            return jsonify({'error': 'No files selected'}), 400

        DOC_EXTENSIONS = {'.pdf', '.doc', '.docx', '.fb2', '.mobi', '.epub'}
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in DOC_EXTENSIONS:
            return jsonify({'error': f'File type not supported for text extraction: {ext}'}), 400

        # Guardar y extraer (misma mecánica que upload_analysis).
        make_user_dir(user_id)
        path, img_path = save_file_with_timestamp(file, file.filename, user_id, use_upload_folder=True)
        if isinstance(path, str) and img_path is None:
            return jsonify({'error': f'Error saving file: {path}'}), 500

        doc_analyzer = DocAnalysisTask(
            userid=user_id,
            file_or_url=path,
            upload_folder=img_path,
            analysis_or_save=True,
            theme_return=False
        )
        # Extracción: texto completo (en paralelo) + metadata, idioma, imágenes,
        # annotations, urls y preview HTML.
        extracted = doc_analyzer.extract_full_text()

        if extracted.get('error'):
            return jsonify({'error': extracted.get('message') or extracted.get('error')}), 422

        full_text = (extracted.get('text') or '').strip()
        if not full_text or len(full_text.split()) < 10:
            return jsonify({'error': 'Could not extract enough text from the document (min. 10 words).'}), 422

        # URLs accesibles para preview HTML e imágenes.
        result_view = extracted.get('result_view')
        html_url = convert_absolute_to_url(result_view, user_id) if result_view else ''
        images_urls = convert_images_to_urls(extracted.get('images', []), user_id)

        # Token firmado sobre la carpeta donde se guardó el upload (archivo original +
        # /images con preview/annotations). Permite al front pedir su borrado más tarde
        # (Document Retention) sin exponer la ruta real ni depender de la cookie de sesión.
        doc_token = _sign_job('doc', os.path.dirname(path))

        return jsonify({
            'success': True,
            'text': full_text,
            'word_count': len(full_text.split()),
            'language': extracted.get('idiom', 'unknown'),
            'metadata': extracted.get('metadata', {}),
            'images': images_urls or [],
            'annotations': extracted.get('annotations', []),
            'urls': extracted.get('urls', []),
            'result_view': html_url or '',
            'doc_token': doc_token
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Unexpected error extracting text',
            'details': str(e)
        }), 500


@x_doc.route('/delete_uploaded_document', methods=['POST'])
@login_required
def delete_uploaded_document():
    """Borra la carpeta de un documento subido vía /extract_text (Document Retention).

    Requiere el `doc_token` devuelto por /extract_text — firmado con el user_id, así
    que solo quien subió el archivo puede pedir su borrado (mismo mecanismo que
    _sign_job/_unsign_job usan los jobs de IA/FinderX).
    """
    data = request.get_json(silent=True) or {}
    doc_token = data.get('doc_token')
    if not doc_token:
        return jsonify({'error': 'Missing doc_token'}), 400

    real_path = _unsign_job('doc', doc_token)
    if real_path is None:
        return jsonify({'error': 'Invalid or expired document token'}), 403

    # Defensa en profundidad: aunque el token ya está firmado, confirmar que la
    # carpeta a borrar vive dentro del directorio de uploads del propio usuario.
    user_root = os.path.abspath(os.path.join(UPLOAD_FOLDER, str(current_user.id)))
    target = os.path.abspath(real_path)
    if os.path.commonpath([user_root, target]) != user_root:
        logger.warning('delete_uploaded_document: path outside user root, user=%s path=%s',
                        current_user.id, target)
        return jsonify({'error': 'Invalid document path'}), 403

    try:
        shutil.rmtree(target, ignore_errors=True)
    except Exception as exc:
        logger.error('delete_uploaded_document failed: %s', exc)
        return jsonify({'error': 'Could not delete the document'}), 500

    return jsonify({'success': True}), 200


def convert_images_to_urls(images_list, user_id=None):
    """
    Convierte una lista de rutas absolutas de imágenes a URLs.
    
    Args:
        images_list: Lista de rutas absolutas de imágenes
        user_id: ID del usuario (opcional, por compatibilidad)
    
    Returns:
        Lista de URLs accesibles
    """
    converted_images = []
    
    for image_path in images_list:
        url = convert_absolute_to_url(image_path, user_id)
        if url:
            converted_images.append(url)
        #else:
        #    print(f"Warning: No se pudo convertir la imagen: {image_path}")
    
    return converted_images

@x_doc.route('/uploadsave_', methods=['POST'])   
def upload_save_():
    """
    Endpoint optimizado para cargar, procesar y guardar un documento en múltiples sistemas:
    1. Qdrant (para indexación y búsqueda) - PRIMERO
    2. MinIO y Milvus en PARALELO (ambos usan el ID de Qdrant)
    
    Mejoras de rendimiento:
    - Paralelización de requests MinIO y Milvus
    - Session reutilizable con connection pooling
    - Timeouts optimizados
    - Manejo de errores mejorado
    """
    
    start_time = time.time()  # Para medir rendimiento
    
    #try:
    # =================== VALIDACIONES INICIALES ===================
    user_id = current_user.id
    
    if user_id is None:
        return jsonify({'error': 'Unauthenticated user or session expired'}), 401
        
    user_data = get_user_data()
    if not user_data:
        return jsonify({'error': 'Could not get user information'}), 400
    
    if 'save_file' not in request.files:
        return jsonify({'error': 'The file was not found in the request'}), 400
        
    file = request.files['save_file']
    if file.filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # =================== PROCESAMIENTO DE ARCHIVO ===================
    make_user_dir(user_id)
    
    # Guardar archivo localmente
    path, img_path = save_file_with_timestamp(file, file.filename, user_id, use_upload_folder=False)
    if isinstance(path, str) and img_path is None:
        return jsonify({'error': f'Error saving file: {path}'}), 500
    
    # Extraer contenido del documento
    doc_analyzer = DocAnalysisTask(
        userid=user_id, 
        file_or_url=path, 
        upload_folder=img_path, 
        analysis_or_save=True,
        theme_return=True
    )
    title, author, content, date, language, img_path, theme = doc_analyzer.extract_content_info()
    
    #print(f"⏱️ Procesamiento de archivo completado en: {time.time() - start_time:.2f}s")
    
    # =================== PREPARAR DATOS ===================
    current_date = datetime.now().strftime('%Y-%m-%d')
    es_document = {
        "user_id": user_id,
        "title": title, 
        "author": author, 
        "date_published": current_date, 
        "content": content, 
        "country": user_data.get('country', 'unknown'),
        "institution": user_data.get('institute', 'unknown'), 
        "language": language,
        "theme": theme
    }
    
    # =================== FUNCIONES PARA REQUESTS PARALELOS ===================
    def elasticsearch_request():
        """Request a Qdrant - Debe ejecutarse primero"""
        try:
            response = session_pool.post(
                'http://localhost:5000/x_search/api/documents/essays_index',
                json=es_document, 
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            return {
                'success': response.status_code == 200,
                'response': response,
                'data': response.json() if response.status_code == 200 else None,
                'error': response.text if response.status_code != 200 else None
            }
        except Exception as e:
            return {
                'success': False,
                'response': None,
                'data': None,
                'error': str(e)
            }
    
    def minio_request(doc_id, file_content):
        """Request a MinIO - Ejecutar en paralelo con Milvus"""
        try:
            form_data = {
                'user_id': user_id,
                'title': title,
                'author': author,
                'date_published': date,
                'language': language,
                'rena': str(path),
                'document_id': doc_id,
                'theme': theme
            }
            
            response = session_pool.post(
                'http://localhost:5000/x_buck/api/documents', 
                files={'file': (file.filename, file_content, file.content_type)}, 
                data=form_data,
                timeout=60  # Timeout más largo para uploads
            )
            
            return {
                'success': response.status_code == 201,
                'response': response,
                'data': response.json() if response.status_code == 201 else None,
                'error': response.text if response.status_code != 201 else None
            }
        except Exception as e:
            return {
                'success': False,
                'response': None,
                'data': None,
                'error': str(e)
            }
    
    def milvus_request(doc_id):
        """Request a Milvus - Ejecutar en paralelo con MinIO"""
        try:
            encoded_path = quote(img_path)
            response = session_pool.post(
                'http://localhost:5000/enhanced_img/upload_directory', 
                json={'path': encoded_path, 'group_id': doc_id},
                timeout=30
            )
            
            return {
                'success': response.status_code == 200,
                'response': response,
                'data': response.json() if response.status_code == 200 else None,
                'error': response.text if response.status_code != 200 else None
            }
        except Exception as e:
            return {
                'success': False,
                'response': None,
                'data': None,
                'error': str(e)
            }
    
    # =================== EJECUTAR REQUESTS ===================
    
    # PASO 1: Qdrant (obligatorio primero para obtener doc_id)
    #print("🔍 Iniciando indexación en Qdrant...")
    elastic_start = time.time()
    
    elastic_result = elasticsearch_request()
    
    if not elastic_result['success']:
        return jsonify({
            'error': 'Error indexing document in Qdrant',
            'details': elastic_result['error'],
            'processing_time': f"{time.time() - start_time:.2f}s"
        }), 500
    
    doc_id = elastic_result['data'].get('id')
    if not doc_id:
        return jsonify({
            'error': 'Could not get the indexed document ID',
            'elastic_response': elastic_result['data'],
            'processing_time': f"{time.time() - start_time:.2f}s"
        }), 500
    
    #print(f"✅ Qdrant completado en: {time.time() - elastic_start:.2f}s")
    
    # PASO 2: MinIO y Milvus EN PARALELO
    #print("🚀 Iniciando MinIO y Milvus en paralelo...")
    parallel_start = time.time()
    
    # Preparar contenido del archivo para MinIO
    file.seek(0)
    file_content = file.read()
    
    # Ejecutar MinIO y Milvus en paralelo usando ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Enviar ambas tareas al pool
        future_minio = executor.submit(minio_request, doc_id, file_content)
        future_milvus = executor.submit(milvus_request, doc_id)
        
        # Recoger resultados conforme se completen
        futures = {
            future_minio: 'MinIO',
            future_milvus: 'Milvus'
        }
        
        results = {}
        for future in as_completed(futures):
            service_name = futures[future]
            try:
                result = future.result()
                results[service_name] = result
                #print(f"✅ {service_name} completado: {'✓' if result['success'] else '✗'}")
            except Exception as e:
                results[service_name] = {
                    'success': False,
                    'error': str(e)
                }
                #print(f"❌ {service_name} falló: {str(e)}")
    
    #print(f"🏁 Requests paralelos completados en: {time.time() - parallel_start:.2f}s")
    
    # =================== VERIFICAR RESULTADOS ===================
    
    # Verificar resultado de Milvus (no crítico, solo log)
    milvus_result = results.get('Milvus', {})
    #if milvus_result.get('success'):
    #    print("✅ Milvus éxito:", milvus_result.get('data'))
    #else:
    #    print("⚠️ Milvus error:", milvus_result.get('error'))
    
    # Verificar resultado de MinIO (crítico)
    minio_result = results.get('MinIO', {})
    if not minio_result.get('success'):
        return jsonify({
            'error': 'Error saving file in MinIO',
            'elastic_id': doc_id,
            'details': minio_result.get('error'),
            'milvus_status': 'success' if milvus_result.get('success') else 'failed',
            'processing_time': f"{time.time() - start_time:.2f}s"
        }), 500
    
    # =================== RESPUESTA EXITOSA ===================
    total_time = time.time() - start_time
    
    return jsonify({
        'success': True,
        'message': 'Document processed and saved successfully',
        'document_id': doc_id,
        'elasticsearch_id': doc_id,
        'minio_status': 'success',
        'milvus_status': 'success' if milvus_result.get('success') else 'warning',
        'processing_time': f"{total_time:.2f}s",
        'performance_metrics': {
            'total_time': f"{total_time:.2f}s",
            'elasticsearch_time': f"{time.time() - elastic_start:.2f}s",
            'parallel_operations_time': f"{time.time() - parallel_start:.2f}s"
        }
    }), 200
    
    #except Exception as e:
    #    total_time = time.time() - start_time
        #print(f"❌ Error inesperado: {str(e)}")
        
    #    return jsonify({
    #        'error': 'Unexpected error during document processing',
    #        'details': str(e),
    #        'processing_time': f"{total_time:.2f}s"
    #    }), 500
        
@x_doc.route('/uploadsave', methods=['POST'])   
def upload_save():
    """
    Endpoint optimizado para cargar, procesar y guardar un documento en múltiples sistemas:
    1. Qdrant (para indexación y búsqueda) - PRIMERO
    2. MinIO y Milvus en PARALELO (ambos usan el ID de Qdrant)
    
    Mejoras de rendimiento:
    - Paralelización de requests MinIO y Milvus
    - Session reutilizable con connection pooling
    - Timeouts optimizados
    - Manejo de errores mejorado
    - Logging detallado
    - Validación robusta
    
    Returns:
        JSON con información del documento guardado y métricas de rendimiento
    """
    
    import logging
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from urllib.parse import quote
    import time
    
    logger = logging.getLogger('upload_save')
    start_time = time.time()  # Para medir rendimiento total
    
    #try:
    # =================== VALIDACIONES INICIALES ===================
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📤 NUEVO DOCUMENTO PARA GUARDAR")
    logger.info(f"{'='*70}")
    
    user_id = current_user.id
    
    if user_id is None:
        logger.error("❌ Usuario no autenticado")
        return jsonify({'error': 'Unauthenticated user or session expired'}), 401
    
    logger.info(f"   User ID: {user_id}")
    
    user_data = get_user_data()
    if not user_data:
        logger.error("❌ No se pudo obtener información del usuario")
        return jsonify({'error': 'Could not get user information'}), 400
    
    if 'save_file' not in request.files:
        logger.error("❌ Archivo no encontrado en la solicitud")
        return jsonify({'error': 'The file was not found in the request'}), 400
    
    file = request.files['save_file']
    if file.filename == '':
        logger.error("❌ Nombre de archivo vacío")
        return jsonify({'error': 'No files selected'}), 400
    
    logger.info(f"   Archivo: {file.filename}")
    logger.info(f"   Tipo MIME: {file.content_type}")
    logger.info(f"{'='*70}\n")
    
    # =================== PROCESAMIENTO DE ARCHIVO ===================
    
    logger.info("📁 Guardando archivo localmente...")
    
    make_user_dir(user_id)
    
    # Guardar archivo localmente
    path, img_path = save_file_with_timestamp(
        file, 
        file.filename, 
        user_id, 
        use_upload_folder=False
    )
    
    if isinstance(path, str) and img_path is None:
        logger.error(f"❌ Error al guardar archivo: {path}")
        return jsonify({'error': f'Error saving file: {path}'}), 500
    
    logger.info(f"✅ Archivo guardado:")
    logger.info(f"   Path: {path}")
    logger.info(f"   Images: {img_path or 'N/A'}\n")
    
    # Extraer contenido del documento
    logger.info("🔍 Extrayendo contenido del documento...")
    
    extraction_start = time.time()
    
    doc_analyzer = DocAnalysisTask(
        userid=user_id, 
        file_or_url=path, 
        upload_folder=img_path, 
        analysis_or_save=True,  # Modo save
        theme_return=True
    )
    
    title, author, content, date, language, img_path, theme = doc_analyzer.extract_content_info()
    
    extraction_time = time.time() - extraction_start
    
    # Count extracted images
    extracted_image_count = 0
    if img_path and os.path.exists(img_path):
        extracted_image_count = len([f for f in os.listdir(img_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))])
    
    logger.info(f"✅ Contenido extraído en {extraction_time:.2f}s:")
    logger.info(f"   Title: {title[:50]}..." if len(title) > 50 else f"   Title: {title}")
    logger.info(f"   Author: {author}")
    logger.info(f"   Language: {language}")
    logger.info(f"   Theme: {theme}")
    logger.info(f"   Content length: {len(content)} chars")
    logger.info(f"   Date: {date}")
    logger.info(f"   🖼️  Images extracted: {extracted_image_count}\n")
    
    # =================== PREPARAR DATOS ===================
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    es_document = {
        "user_id": user_id,
        "title": title, 
        "author": author, 
        "date_published": current_date, 
        "content": content,  # ✅ Texto completo para almacenamiento
        "country": user_data.get('country', 'unknown'),
        "institution": user_data.get('institute', 'unknown'), 
        "language": language,
        "theme": theme,
        "source_file": file.filename,  # ✅ Nombre original del archivo
        "mime_type": file.content_type,  # ✅ Tipo MIME del archivo
        "image_count": extracted_image_count,  # ✅ Conteo de imágenes extraídas
        "image_folder": img_path if extracted_image_count > 0 else None  # ✅ Ruta a las imágenes
    }
    
    logger.info("📋 Documento preparado para Qdrant:")
    logger.info(f"   Fields: {list(es_document.keys())}")
    logger.info(f"   Country: {es_document['country']}")
    logger.info(f"   Institution: {es_document['institution']}")
    logger.info(f"   Image count: {extracted_image_count}\n")
    
    # =================== FUNCIONES PARA REQUESTS PARALELOS ===================
    
    def elasticsearch_request():
        """
        Request a Qdrant - Debe ejecutarse primero para obtener doc_id
        """
        #try:
        logger.info("🔍 Indexando en Qdrant (Search Service)...")
        
        response = session_pool.post(
            'http://localhost:5000/x_search/api/documents/essays_index',
            json=es_document, 
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        success = response.status_code == 200
        
        if success:
            data = response.json()
            doc_id = data.get('id')
            logger.info(f"✅ Qdrant: Documento indexado (ID: {doc_id})")
        else:
            logger.error(f"❌ Qdrant: Error {response.status_code}")
            logger.error(f"   Response: {response.text[:200]}")
        
        return {
            'success': success,
            'response': response,
            'data': data if success else None,
            'error': response.text if not success else None
        }
        #except Exception as e:
        #    logger.error(f"❌ Qdrant: Excepción - {str(e)}")
        #    return {
        #        'success': False,
        #        'response': None,
        #        'data': None,
        #        'error': str(e)
        #    }
    
    def seaweedfs_request(doc_id, file_content):
        """
        Request a SeaweedFS - Ejecutar en paralelo con Milvus
        Usa endpoint interno que no requiere sesión
        """
        #try:
        logger.info(f"☁️  Subiendo a SeaweedFS (doc_id: {doc_id})...")
        
        #  SOLUCIÓN: Sanitizar metadatos para que solo contengan ASCII
        def sanitize_for_s3(text):
            """Convierte texto a ASCII seguro para S3 metadata"""
            if not text:
                return text
            # Opción 1: Transliterar (í -> i, ñ -> n, etc.)
            import unicodedata
            nfkd = unicodedata.normalize('NFKD', text)
            ascii_text = nfkd.encode('ASCII', 'ignore').decode('ASCII')
            return ascii_text
        
        form_data = {
            'user_id': user_id,
            'title': sanitize_for_s3(title),
            'author': sanitize_for_s3(author),
            'date_published': date,
            'language': language,
            'rena': str(path),
            'document_id': doc_id,
            'theme': sanitize_for_s3(theme) 
        }
        
        response = session_pool.post(
            'http://localhost:5000/x_buck/api/documents/internal',  # Endpoint interno sin sesión
            files={'file': (file.filename, file_content, file.content_type)}, 
            data=form_data,
            timeout=60  # Timeout más largo para uploads
        )
        
        success = response.status_code == 201
        
        if success:
            logger.info(f"✅ SeaweedFS: Archivo subido exitosamente")
        else:
            logger.error(f"❌ SeaweedFS: Error {response.status_code}")
            logger.error(f"   Response: {response.text[:200]}")
        
        return {
            'success': success,
            'response': response,
            'data': response.json() if success else None,
            'error': response.text if not success else None
        }
        #except Exception as e:
        #    logger.error(f"❌ MinIO: Excepción - {str(e)}")
        #    return {
        #        'success': False,
        #        'response': None,
        #        'data': None,
        #        'error': str(e)
        #    }
    
    def qdrant_image_request(doc_id):
        """
        Indexación de imágenes en Qdrant — DESHABILITADA.
        El endpoint /x_image/upload_and_index fue eliminado junto con los modelos
        CLIP (clip-ViT-B-32) y SigLIP (Ateeqq/ai-vs-human-image-detector).
        Se mantiene como no-op para no romper el flujo paralelo de subida.
        """
        return {
            'success': True,
            'response': None,
            'data': {'message': 'Image indexing disabled (CLIP/SigLIP removed)'},
            'error': None
        }
    
    # =================== EJECUTAR REQUESTS ===================
    
    # PASO 1: Qdrant (obligatorio primero para obtener doc_id)
    logger.info(f"\n{'='*70}")
    logger.info("PASO 1: INDEXACIÓN EN QDRANT / SEARCH SERVICE")
    logger.info(f"{'='*70}\n")
    
    elastic_start = time.time()
    elastic_result = elasticsearch_request()
    elastic_time = time.time() - elastic_start
    
    if not elastic_result['success']:
        logger.error(f"\n{'='*70}")
        logger.error("❌ FALLO CRÍTICO: Error en Qdrant")
        logger.error(f"{'='*70}")
        logger.error(f"   Error: {elastic_result['error']}")
        logger.error(f"   Tiempo: {elastic_time:.2f}s")
        logger.error(f"{'='*70}\n")
        
        return jsonify({
            'error': 'Error indexing document in Qdrant',
            'details': elastic_result['error'],
            'processing_time': f"{time.time() - start_time:.2f}s"
        }), 500
    
    doc_id = elastic_result['data'].get('id')
    if not doc_id:
        logger.error(f"\n{'='*70}")
        logger.error("❌ ERROR: No se obtuvo document_id de Qdrant")
        logger.error(f"{'='*70}")
        logger.error(f"   Response: {elastic_result['data']}")
        logger.error(f"{'='*70}\n")
        
        return jsonify({
            'error': 'Could not get the indexed document ID',
            'elastic_response': elastic_result['data'],
            'processing_time': f"{time.time() - start_time:.2f}s"
        }), 500
    
    logger.info(f"✅ Qdrant completado en {elastic_time:.2f}s")
    logger.info(f"   Document ID: {doc_id}\n")
    
    # PASO 2: SeaweedFS y Milvus EN PARALELO
    logger.info(f"{'='*70}")
    logger.info("PASO 2: ALMACENAMIENTO PARALELO (SeaweedFS + Milvus)")
    logger.info(f"{'='*70}\n")
    
    parallel_start = time.time()
    
    # Preparar contenido del archivo para SeaweedFS
    file.seek(0)
    file_content = file.read()
    
    logger.info(f"🚀 Iniciando operaciones paralelas...")
    logger.info(f"   SeaweedFS: Subiendo archivo ({len(file_content)} bytes)")
    logger.info(f"   Qdrant Images: Indexando imágenes en {img_path or 'N/A'}\n")
    
    # Ejecutar SeaweedFS y Qdrant Images en paralelo usando ThreadPoolExecutor
    results = {}
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Enviar ambas tareas al pool
        future_seaweedfs = executor.submit(seaweedfs_request, doc_id, file_content)
        future_qdrant_imgs = executor.submit(qdrant_image_request, doc_id)
        
        # Recoger resultados conforme se completen
        futures = {
            future_seaweedfs: 'SeaweedFS',
            future_qdrant_imgs: 'Qdrant_Images'
        }
        
        for future in as_completed(futures):
            service_name = futures[future]
            try:
                result = future.result()
                results[service_name] = result
                
                status = "✅" if result['success'] else "❌"
                logger.info(f"{status} {service_name} completado")
                
            except Exception as e:
                results[service_name] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"❌ {service_name} falló: {str(e)}")
    
    parallel_time = time.time() - parallel_start
    
    logger.info(f"\n✅ Operaciones paralelas completadas en {parallel_time:.2f}s\n")
    
    # =================== VERIFICAR RESULTADOS ===================
    
    logger.info(f"{'='*70}")
    logger.info("VERIFICACIÓN DE RESULTADOS")
    logger.info(f"{'='*70}\n")
    
    # Verificar resultado de Qdrant Images (no crítico, solo log)
    qdrant_imgs_result = results.get('Qdrant_Images', {})
    qdrant_imgs_status = "success" if qdrant_imgs_result.get('success') else "warning"
    
    if qdrant_imgs_result.get('success'):
        logger.info(f"✅ Qdrant Images: Operación exitosa")
        if qdrant_imgs_result.get('data'):
            logger.info(f"   Data: {qdrant_imgs_result['data']}")
    else:
        logger.warning(f"⚠️  Qdrant Images: Operación con advertencias")
        logger.warning(f"   Error: {qdrant_imgs_result.get('error', 'Unknown')}")
    
    # Verificar resultado de SeaweedFS (crítico)
    seaweedfs_result = results.get('SeaweedFS', {})
    
    if not seaweedfs_result.get('success'):
        logger.error(f"\n{'='*70}")
        logger.error("❌ ERROR CRÍTICO: Fallo en SeaweedFS")
        logger.error(f"{'='*70}")
        logger.error(f"   Error: {seaweedfs_result.get('error')}")
        logger.error(f"   Qdrant ID: {doc_id} (documento indexado)")
        logger.error(f"   Milvus status: {milvus_status}")
        logger.error(f"{'='*70}\n")
        
        return jsonify({
            'error': 'Error saving file in SeaweedFS',
            'elastic_id': doc_id,
            'details': seaweedfs_result.get('error'),
            'qdrant_images_status': qdrant_imgs_status,
            'processing_time': f"{time.time() - start_time:.2f}s"
        }), 500
    
    logger.info(f"✅ SeaweedFS: Archivo guardado exitosamente\n")
    
    # =================== RESPUESTA EXITOSA ===================
    
    total_time = time.time() - start_time
    
    logger.info(f"{'='*70}")
    logger.info("✅ DOCUMENTO GUARDADO EXITOSAMENTE")
    logger.info(f"{'='*70}")
    logger.info(f"   Document ID: {doc_id}")
    logger.info(f"   Title: {title[:50]}..." if len(title) > 50 else f"   Title: {title}")
    logger.info(f"   Author: {author}")
    logger.info(f"   Language: {language}")
    logger.info(f"   Theme: {theme}")
    logger.info(f"\n   MÉTRICAS DE RENDIMIENTO:")
    logger.info(f"   • Tiempo total: {total_time:.2f}s")
    logger.info(f"   • Extracción: {extraction_time:.2f}s")
    logger.info(f"   • Qdrant: {elastic_time:.2f}s")
    logger.info(f"   • Operaciones paralelas: {parallel_time:.2f}s")
    logger.info(f"   • Qdrant status: ✅ success")
    logger.info(f"   • SeaweedFS status: ✅ success")
    logger.info(f"   • Qdrant Images status: {'✅ success' if qdrant_imgs_result.get('success') else '⚠️  warning'}")
    logger.info(f"{'='*70}\n")
    
    return jsonify({
        'success': True,
        'message': 'Document processed and saved successfully',
        'document_id': doc_id,
        'elasticsearch_id': doc_id,
        'seaweed_status': 'success',
        'qdrant_images_status': qdrant_imgs_status,
        'document_info': {
            'title': title,
            'author': author,
            'language': language,
            'theme': theme,
            'date_published': current_date,
            'content_length': len(content)
        },
        'processing_time': f"{total_time:.2f}s",
        'performance_metrics': {
            'total_time': f"{total_time:.2f}s",
            'extraction_time': f"{extraction_time:.2f}s",
            'qdrant_time': f"{elastic_time:.2f}s",
            'parallel_operations_time': f"{parallel_time:.2f}s",
            'speedup_factor': f"{(elastic_time + parallel_time) / total_time:.2f}x"
        }
    }), 200
        
    #except Exception as e:
    #    total_time = time.time() - start_time
        
    #    logger.error(f"\n{'='*70}")
    #    logger.error("❌ ERROR INESPERADO EN upload_save")
    #    logger.error(f"{'='*70}")
    #    logger.error(f"   Error: {str(e)}")
    #    logger.error(f"   Tiempo transcurrido: {total_time:.2f}s")
        
    #    import traceback
    #    traceback.print_exc()
        
    #    logger.error(f"{'='*70}\n")
        
    #    return jsonify({
    #        'error': 'Unexpected error during document processing',
    #        'details': str(e),
    #        'processing_time': f"{total_time:.2f}s"
    #    }), 500

@x_doc.route('/deletesave/<path:document_id>', methods=['DELETE', 'POST'])
def delete_save(document_id):
    """Eliminar documento de Minio, Qdrant y Milvus en paralelo"""
    user_id = session.get('user_id')
    
    if user_id is None:
        return jsonify({'error': 'Unauthenticated user or session expired'}), 401

    # Función mejorada para hacer DELETE con timeout
    def safe_delete(service_info):
        service_name, url = service_info
        try:
            response = requests.delete(url, timeout=5)
            return service_name, response
        except requests.RequestException as e:
            return service_name, str(e)

    # Endpoints de borrado
    urls = [
        ("bucket", f'http://localhost:5000/x_buck/api/documents/{document_id}/{user_id}'),
        ("qdrant", f'http://localhost:5000/x_search/api/documents/essays_index/{document_id}'),
        ("qdrant_images", f'http://localhost:5000/x_image/delete_by_group/{document_id}')
    ]

    results = {}
    
    # Ejecutar requests en paralelo con ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Enviar todas las tareas al pool
        future_to_service = {executor.submit(safe_delete, service_info): service_info[0] 
                           for service_info in urls}
        
        # Procesar resultados conforme se completan
        for future in as_completed(future_to_service):
            service_name, resp = future.result()
            
            if isinstance(resp, str):
                results[service_name] = {"status": "error", "details": resp}
            else:
                # Parsear JSON de forma segura
                try:
                    resp_json = resp.json() if resp.text and resp.text.strip() else {}
                except:
                    resp_json = {"raw": resp.text[:200] if resp.text else "empty response"}
                
                if resp.status_code == 200:
                    results[service_name] = {
                        "status": "success", 
                        "details": resp_json
                    }
                else:
                    results[service_name] = {
                        "status": "error", 
                        "details": resp_json, 
                        "code": resp.status_code
                    }

    # Verificar si hubo algún error
    errors = {k: v for k, v in results.items() if v['status'] == 'error'}

    if errors:
        return jsonify({
            "message": "Error deleting on one or more services.",
            "results": results
        }), 207  # 207 Multi-Status

    return jsonify({
        "message": "Document successfully deleted on all services.",
        "results": results
    }), 200

# ==========================================
# DMS ADVANCED FEATURES - FOLDERS & ORGANIZATION
# ==========================================

@x_doc.route('/folders', methods=['GET'])
@login_required
def list_folders_and_files():
    """Lista contenido de una carpeta (o raíz si no se provee parent_id)"""
    parent_id = request.args.get('parent_id', type=int)
    show_trash = request.args.get('trash', 'false').lower() == 'true'
    
    query_folders = Folder.query.filter_by(user_id=current_user.id, is_trash=show_trash)
    query_files = File.query.filter_by(user_id=current_user.id, is_trash=show_trash)
    
    if parent_id:
        query_folders = query_folders.filter_by(parent_id=parent_id)
        query_files = query_files.filter_by(folder_id=parent_id)
    else:
        query_folders = query_folders.filter_by(parent_id=None)
        query_files = query_files.filter_by(folder_id=None)
        
    folders = query_folders.all()
    files = query_files.all()
    
    return jsonify({
        'folders': [{
            'id': f.id,
            'name': f.name,
            'path': f.path,
            'parent_id': f.parent_id,
            'is_shared': f.is_shared,
            'created_at': f.created_at.isoformat()
        } for f in folders],
        'files': [{
            'id': fl.id,
            'filename': fl.filename,
            'original_filename': fl.original_filename,
            'size': fl.size,
            'status': fl.status,
            'is_locked': fl.is_locked,
            'is_evidence': fl.is_evidence,
            'created_at': fl.created_at.isoformat(),
            'minio_url': fl.minio_url,
            'mime_type': fl.mime_type
        } for fl in files]
    })

@x_doc.route('/folders/create', methods=['POST'])
@login_required
def create_folder():
    """Crea una nueva carpeta"""
    data = request.get_json()
    name = data.get('name')
    parent_id = data.get('parent_id')
    
    if not name:
        return jsonify({'error': 'Folder name is required'}), 400
        
    # Calcular el path
    path = name
    if parent_id:
        parent = Folder.query.get(parent_id)
        if parent:
            path = f"{parent.path}/{name}"
            
    new_folder = Folder(name=name, path=path, user_id=current_user.id, parent_id=parent_id)
    db.session.add(new_folder)
    db.session.commit()
    
    return jsonify({
        'message': 'Folder created successfully',
        'folder': {
            'id': new_folder.id,
            'name': new_folder.name,
            'path': new_folder.path
        }
    }), 201

@x_doc.route('/folders/rename/<int:folder_id>', methods=['POST'])
@login_required
def rename_folder(folder_id):
    """Renombra una carpeta"""
    folder = Folder.query.filter_by(id=folder_id, user_id=current_user.id).first()
    if not folder:
        return jsonify({'error': 'Folder not found'}), 404
        
    data = request.get_json()
    new_name = data.get('name')
    if not new_name:
        return jsonify({'error': 'New name is required'}), 400
        
    folder.name = new_name
    # Actualizar path recursivamente podría ser complejo, por ahora solo el nombre
    db.session.commit()
    
    return jsonify({'message': 'Folder renamed successfully'})

@x_doc.route('/organize/move', methods=['POST'])
@login_required
def move_item():
    """Mueve un archivo o carpeta a una nueva ubicación"""
    data = request.get_json()
    item_id = data.get('item_id')
    item_type = data.get('type') # 'file' or 'folder'
    new_parent_id = data.get('new_parent_id')
    
    if item_type == 'folder':
        item = Folder.query.filter_by(id=item_id, user_id=current_user.id).first()
        if item:
            item.parent_id = new_parent_id
    elif item_type == 'file':
        item = File.query.filter_by(id=item_id, user_id=current_user.id).first()
        if item:
            item.folder_id = new_parent_id
    else:
        return jsonify({'error': 'Invalid item type'}), 400
        
    if not item:
        return jsonify({'error': 'Item not found'}), 404
        
    db.session.commit()
    return jsonify({'message': 'Item moved successfully'})

@x_doc.route('/organize/trash', methods=['POST'])
@login_required
def move_to_trash():
    """Mueve un archivo o carpeta a la papelera"""
    data = request.get_json()
    item_id = data.get('item_id')
    item_type = data.get('type')
    
    if item_type == 'folder':
        item = Folder.query.filter_by(id=item_id, user_id=current_user.id).first()
    else:
        item = File.query.filter_by(id=item_id, user_id=current_user.id).first()
        
    if not item:
        return jsonify({'error': 'Item not found'}), 404
        
    if getattr(item, 'is_evidence', False):
         return jsonify({'error': 'Cannot move evidence to trash'}), 403

    def mark_trash_recursive(folder):
        folder.is_trash = True
        for sub in folder.subfolders:
            mark_trash_recursive(sub)
        for f in folder.files:
            f.is_trash = True

    if item_type == 'folder':
        mark_trash_recursive(item)
    else:
        item.is_trash = True

    db.session.commit()
    clear_cache_for_user(current_user.id)
    return jsonify({'message': 'Item moved to trash'})

@x_doc.route('/organize/restore', methods=['POST'])
@login_required
def restore_from_trash():
    """Restaura un archivo o carpeta de la papelera"""
    data = request.get_json()
    item_id = data.get('item_id')
    item_type = data.get('type')
    
    if item_type == 'folder':
        item = Folder.query.filter_by(id=item_id, user_id=current_user.id).first()
    else:
        item = File.query.filter_by(id=item_id, user_id=current_user.id).first()
        
    if not item:
        return jsonify({'error': 'Item not found'}), 404
        
    def restore_recursive(folder):
        folder.is_trash = False
        for sub in folder.subfolders:
            restore_recursive(sub)
        for f in folder.files:
            f.is_trash = False

    if item_type == 'folder':
        restore_recursive(item)
    else:
        item.is_trash = False

    db.session.commit()
    clear_cache_for_user(current_user.id)
    return jsonify({'message': 'Item restored successfully'})


@x_doc.route('/organize/permanent-delete', methods=['POST'])
@login_required
def permanent_delete():
    """Elimina permanentemente un archivo o carpeta de la papelera y físicamente de los servicios."""
    data = request.get_json()
    item_id = data.get('item_id')
    item_type = data.get('type')
    
    if item_type == 'folder':
        item = Folder.query.filter_by(id=item_id, user_id=current_user.id, is_trash=True).first()
    else:
        item = File.query.filter_by(id=item_id, user_id=current_user.id, is_trash=True).first()
        
    if not item:
        return jsonify({'error': 'Item not found in trash'}), 404

    storage_client = get_storage_client()
    deletion_results = []

    def trigger_physical_deletion(file_obj):
        """Intenta borrar el archivo de Qdrant, Milvus y SeaweedFS"""
        # Intentar obtener el document_id (ID de Qdrant)
        # Probamos con las dos rutas posibles en SeaweedFS
        possible_keys = [
            f"documents/{file_obj.user_id}/{file_obj.filename}",
            f"{file_obj.user_id}/{file_obj.filename}"
        ]
        
        doc_id = None
        for key in possible_keys:
            found_id = storage_client.get_document_id_from_key(key)
            if found_id:
                doc_id = found_id
                break
        
        if doc_id:
            # Si tenemos doc_id, usamos la ruta unificada de borrado (deletesave)
            try:
                # Llamar internamente a la lógica de deletesave para mayor eficiencia
                # o hacer el request al endpoint local
                logger.info(f"Triggering unified deletion for document: {doc_id}")
                resp = session_pool.delete(f'http://localhost:5000/x_doc/deletesave/{doc_id}', timeout=10)
                return {"file": file_obj.original_filename, "unified_delete": resp.status_code == 200}
            except Exception as e:
                logger.error(f"Error in unified deletion for {doc_id}: {e}")
                return {"file": file_obj.original_filename, "error": str(e)}
        else:
            # Si no hay doc_id (archivo simple sin indexar), borrar solo de SeaweedFS
            try:
                logger.info(f"Document ID not found for {file_obj.filename}. Deleting from SeaweedFS only.")
                storage_client.delete_file(f"{file_obj.user_id}/{file_obj.filename}", user=file_obj.user_id)
                # También probar ruta /documents/ por si acaso
                try:
                    storage_client.delete_file(f"documents/{file_obj.user_id}/{file_obj.filename}")
                except:
                    pass
                return {"file": file_obj.original_filename, "storage_delete": True}
            except Exception as e:
                return {"file": file_obj.original_filename, "error": str(e)}

    def delete_recursive(folder):
        """Elimina recursivamente subcarpetas y archivos físicamente y de BD"""
        # Coleccionar archivos primero para borrar físicamente
        for f in folder.files:
            res = trigger_physical_deletion(f)
            deletion_results.append(res)
            db.session.delete(f)
            
        for sub in folder.subfolders:
            delete_recursive(sub)
            
        db.session.delete(folder)
    
    try:
        if item_type == 'folder':
            delete_recursive(item)
        else:
            res = trigger_physical_deletion(item)
            deletion_results.append(res)
            db.session.delete(item)
            
        db.session.commit()
        clear_cache_for_user(current_user.id)
        return jsonify({
            'message': 'Item permanently deleted from database and storage services',
            'details': deletion_results
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in permanent_delete: {str(e)}")
        return jsonify({'error': f'Error deleting item: {str(e)}'}), 500


# ==========================================
# SHARED USERS - GET/POST
# ==========================================
@x_doc.route('/shared/<item_type>/<int:item_id>', methods=['GET'])
@login_required
def get_shared_users(item_type, item_id):
    """Get list of users an item is shared with"""
    from modules.models.model import ItemShare
    
    shares = ItemShare.query.filter_by(
        item_type=item_type,
        item_id=item_id,
        owner_id=current_user.id
    ).all()
    
    return jsonify({
        'shares': [s.to_dict() for s in shares]
    })


@x_doc.route('/share', methods=['POST'])
@login_required
def share_item():
    """Share an item with another user"""
    from modules.models.model import ItemShare, Users
    
    data = request.get_json()
    item_type = data.get('item_type')
    item_id = data.get('item_id')
    email = data.get('email')
    permission = data.get('permission', 'viewer')
    
    if not all([item_type, item_id, email]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Find user by email
    target_user = Users.query.filter_by(email=email).first()
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
    
    if target_user.id == current_user.id:
        return jsonify({'error': 'Cannot share with yourself'}), 400
    
    # Check if already shared
    existing = ItemShare.query.filter_by(
        item_type=item_type,
        item_id=item_id,
        shared_with_id=target_user.id
    ).first()
    
    if existing:
        existing.permission = permission
    else:
        share = ItemShare(
            item_type=item_type,
            item_id=item_id,
            owner_id=current_user.id,
            shared_with_id=target_user.id,
            permission=permission
        )
        db.session.add(share)

    db.session.commit()
    clear_cache_for_user(current_user.id)
    clear_cache_for_user(target_user.id)
    return jsonify({'message': 'Item shared successfully'}), 201


@x_doc.route('/share/<int:share_id>', methods=['DELETE'])
@login_required
def remove_share(share_id):
    """Remove a share"""
    from modules.models.model import ItemShare
    
    share = ItemShare.query.filter_by(id=share_id, owner_id=current_user.id).first()
    if not share:
        return jsonify({'error': 'Share not found'}), 404
    
    db.session.delete(share)
    db.session.commit()
    return jsonify({'message': 'Share removed successfully'})


# ==========================================
# ITEM HISTORY - GET
# ==========================================
@x_doc.route('/history/<item_type>/<int:item_id>', methods=['GET'])
@login_required
def get_item_history(item_type, item_id):
    """Get rename/change history for an item"""
    from modules.models.model import ItemHistory

    if item_type == 'file':
        owned = File.query.filter_by(id=item_id, user_id=current_user.id).first()
        if not owned:
            return jsonify({'error': 'File not found'}), 404

    history = ItemHistory.query.filter_by(
        item_type=item_type,
        item_id=item_id
    ).order_by(ItemHistory.created_at.desc()).limit(20).all()

    return jsonify({
        'history': [h.to_dict() for h in history]
    })


@x_doc.route('/users/search', methods=['GET'])
@login_required
def search_users():
    """Search users by email for sharing"""
    from modules.models.model import Users
    query = request.args.get('q', '')
    if len(query) < 3:
        return jsonify({'users': []})
    
    users = Users.query.filter(Users.email.like(f'%{query}%')).limit(10).all()
    return jsonify({
        'users': [{
            'id': u.id,
            'email': u.email,
            'name': f"{u.name or ''} {u.lastname or ''}".strip() or u.email.split('@')[0],
            'avatar': (u.name or 'U')[0].upper() + (u.lastname or 'X')[0].upper()
        } for u in users if u.id != current_user.id]
    })


@x_doc.route('/rename', methods=['POST'])
@login_required
def rename_item_generic():
    """Renombra un archivo o carpeta y registra historial"""
    from modules.models.model import File, Folder, ItemHistory
    data = request.get_json()
    item_id = data.get('id')
    item_type = data.get('type') # 'file' or 'folder'
    new_name = data.get('name')
    
    if not all([item_id, item_type, new_name]):
        return jsonify({'error': 'Missing data'}), 400

    old_name = ""
    if item_type == 'folder':
        item = Folder.query.filter_by(id=item_id, user_id=current_user.id).first()
        if item:
            old_name = item.name
            item.name = new_name
    else:
        item = File.query.filter_by(id=item_id, user_id=current_user.id).first()
        if item:
            old_name = item.original_filename
            item.original_filename = new_name
            
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Record history
    history = ItemHistory(
        item_type=item_type,
        item_id=item_id,
        action='rename',
        old_value=old_name,
        new_value=new_name,
        user_id=current_user.id
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify({'message': 'Item renamed successfully', 'new_name': new_name})


# ==========================================
# TAGS CRUD - Create, Read, Update, Delete
# ==========================================
@x_doc.route('/tags', methods=['GET'])
@login_required
def get_tags():
    """Get all tags for current user"""
    tags = Tag.query.filter_by(user_id=current_user.id).order_by(Tag.name).all()
    return jsonify({
        'tags': [t.to_dict() for t in tags]
    })


@x_doc.route('/tags', methods=['POST'])
@login_required
def create_tag():
    """Create a new tag"""
    data = request.get_json()
    name = data.get('name', '').strip()
    color = data.get('color', '#007bff')
    
    if not name:
        return jsonify({'error': 'Tag name is required'}), 400
    
    # Check for duplicate
    existing = Tag.query.filter_by(user_id=current_user.id, name=name).first()
    if existing:
        return jsonify({'error': 'Tag already exists'}), 400
    
    tag = Tag(name=name, color=color, user_id=current_user.id)
    db.session.add(tag)
    db.session.commit()
    
    return jsonify({'message': 'Tag created successfully', 'tag': tag.to_dict()}), 201


@x_doc.route('/tags/<int:tag_id>', methods=['PUT'])
@login_required
def update_tag(tag_id):
    """Update a tag"""
    tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    data = request.get_json()
    if 'name' in data:
        tag.name = data['name'].strip()
    if 'color' in data:
        tag.color = data['color']
    
    db.session.commit()
    return jsonify({'message': 'Tag updated', 'tag': tag.to_dict()})


@x_doc.route('/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def delete_tag(tag_id):
    """Delete a tag"""
    tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    db.session.delete(tag)
    db.session.commit()
    return jsonify({'message': 'Tag deleted'})


# ==========================================
# FILE TAGS - Assign/Remove tags from files
# ==========================================
@x_doc.route('/files/<int:file_id>/tags', methods=['GET'])
@login_required
def get_file_tags(file_id):
    """Get tags assigned to a file"""
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    file_tags = FileTag.query.filter_by(file_id=file_id).all()
    tags = [Tag.query.get(ft.tag_id) for ft in file_tags]
    
    return jsonify({
        'tags': [t.to_dict() for t in tags if t]
    })


@x_doc.route('/files/<int:file_id>/tags', methods=['POST'])
@login_required
def assign_file_tag(file_id):
    """Assign a tag to a file"""
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    data = request.get_json()
    tag_id = data.get('tag_id')
    is_auto = data.get('is_auto', False)
    
    if not tag_id:
        return jsonify({'error': 'Tag ID is required'}), 400
    
    # Verify tag belongs to user
    tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    # Check if already assigned
    existing = FileTag.query.filter_by(file_id=file_id, tag_id=tag_id).first()
    if existing:
        return jsonify({'message': 'Tag already assigned'}), 200
    
    file_tag = FileTag(
        file_id=file_id,
        tag_id=tag_id,
        assigned_by=current_user.id,
        is_auto=is_auto
    )
    db.session.add(file_tag)
    db.session.commit()
    
    return jsonify({'message': 'Tag assigned successfully'}), 201


@x_doc.route('/files/<int:file_id>/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def remove_file_tag(file_id, tag_id):
    """Remove a tag from a file"""
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    file_tag = FileTag.query.filter_by(file_id=file_id, tag_id=tag_id).first()
    if not file_tag:
        return jsonify({'error': 'Tag not assigned to this file'}), 404
    
    db.session.delete(file_tag)
    db.session.commit()
    
    return jsonify({'message': 'Tag removed'})


# ==========================================
# FILE STATUS - Update document status
# ==========================================
VALID_STATUSES = ['Borrador', 'En revisión', 'Validado', 'Archivado']

@x_doc.route('/files/<int:file_id>/status', methods=['PUT'])
@login_required
def update_file_status(file_id):
    """Update file status (Borrador, En revisión, Validado, Archivado)"""
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in VALID_STATUSES:
        return jsonify({'error': f'Invalid status. Valid values: {VALID_STATUSES}'}), 400
    
    old_status = file.status
    file.status = new_status

    # Archive expiry: 10 days TTL stored in expires_at
    if new_status == 'Archivado':
        file.expires_at = datetime.utcnow() + timedelta(days=10)
    elif old_status == 'Archivado':
        file.expires_at = None

    # Record history
    history = ItemHistory(
        item_type='file',
        item_id=file_id,
        action='status_change',
        old_value=old_status,
        new_value=new_status,
        user_id=current_user.id
    )
    db.session.add(history)
    db.session.commit()
    clear_cache_for_user(current_user.id)

    return jsonify({'message': 'Status updated', 'status': new_status})


@x_doc.route('/files/<int:file_id>/status', methods=['GET'])
@login_required
def get_file_status(file_id):
    """Get file status and valid options"""
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    return jsonify({
        'status': file.status,
        'valid_statuses': VALID_STATUSES
    })


# ==========================================
# ENHANCED SHARING - With expiration dates
# ==========================================
@x_doc.route('/share/enhanced', methods=['POST'])
@login_required
def share_item_enhanced():
    """Share an item with expiration date support"""
    data = request.get_json()
    item_type = data.get('item_type')
    item_id = data.get('item_id')
    email = data.get('email')
    permission = data.get('permission', 'viewer')
    expires_at_str = data.get('expires_at')  # ISO format datetime string
    
    if not all([item_type, item_id, email]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate permission level
    valid_permissions = ['viewer', 'commenter', 'editor', 'reviewer']
    if permission not in valid_permissions:
        return jsonify({'error': f'Invalid permission. Valid: {valid_permissions}'}), 400
    
    # Parse expiration date
    expires_at = None
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid expires_at format. Use ISO format.'}), 400
    
    # Find user by email
    target_user = Users.query.filter_by(email=email).first()
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
    
    if target_user.id == current_user.id:
        return jsonify({'error': 'Cannot share with yourself'}), 400
    
    # Check if already shared
    existing = ItemShare.query.filter_by(
        item_type=item_type,
        item_id=item_id,
        shared_with_id=target_user.id
    ).first()
    
    if existing:
        existing.permission = permission
        existing.expires_at = expires_at
    else:
        share = ItemShare(
            item_type=item_type,
            item_id=item_id,
            owner_id=current_user.id,
            shared_with_id=target_user.id,
            permission=permission,
            expires_at=expires_at
        )
        db.session.add(share)
    
    db.session.commit()
    return jsonify({'message': 'Item shared successfully'}), 201


@x_doc.route('/shared/<item_type>/<int:item_id>/avatars', methods=['GET'])
@login_required
def get_shared_avatars(item_type, item_id):
    """Get shared user avatars for stacked display"""
    shares = ItemShare.query.filter_by(
        item_type=item_type,
        item_id=item_id,
        owner_id=current_user.id
    ).all()
    
    # Filter out expired shares
    active_shares = [s for s in shares if not s.is_expired()]
    
    avatars = []
    for share in active_shares[:5]:  # Limit to 5 avatars
        user = share.shared_with
        avatars.append({
            'id': user.id,
            'initials': (user.name or 'U')[0].upper() + (user.lastname or 'X')[0].upper(),
            'name': f"{user.name or ''} {user.lastname or ''}".strip() or user.email.split('@')[0],
            'permission': share.permission
        })
    
    return jsonify({
        'avatars': avatars,
        'total_shared': len(active_shares),
        'has_more': len(active_shares) > 5
    })


# ==========================================
# MOVE DOCUMENTS - Between folders/spaces
# ==========================================
@x_doc.route('/organize/move-to', methods=['POST'])
@login_required
def move_to_folder():
    """Move file or folder to another location with history tracking"""
    data = request.get_json()
    item_id = data.get('item_id')
    item_type = data.get('type')  # 'file' or 'folder'
    target_folder_id = data.get('target_folder_id')  # null for root
    
    if not all([item_id, item_type]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Get item
    if item_type == 'folder':
        item = Folder.query.filter_by(id=item_id, user_id=current_user.id).first()
        old_parent = item.parent_id if item else None
        if item:
            # Prevent moving folder into itself or its children
            if target_folder_id:
                target = Folder.query.get(target_folder_id)
                current = target
                while current:
                    if current.id == item_id:
                        return jsonify({'error': 'Cannot move folder into itself'}), 400
                    current = current.parent
            item.parent_id = target_folder_id
    else:
        item = File.query.filter_by(id=item_id, user_id=current_user.id).first()
        old_parent = item.folder_id if item else None
        if item:
            item.folder_id = target_folder_id
    
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Get folder names for history
    old_folder_name = 'Root'
    new_folder_name = 'Root'
    if old_parent:
        old_folder = Folder.query.get(old_parent)
        old_folder_name = old_folder.name if old_folder else 'Unknown'
    if target_folder_id:
        new_folder = Folder.query.get(target_folder_id)
        new_folder_name = new_folder.name if new_folder else 'Unknown'
    
    # Record history
    history = ItemHistory(
        item_type=item_type,
        item_id=item_id,
        action='move',
        old_value=old_folder_name,
        new_value=new_folder_name,
        user_id=current_user.id
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify({'message': 'Item moved successfully'})


@x_doc.route('/folders/tree', methods=['GET'])
@login_required
def get_folder_tree():
    """Get folder tree for move modal"""
    def build_tree(parent_id=None):
        folders = Folder.query.filter_by(
            user_id=current_user.id,
            parent_id=parent_id,
            is_trash=False
        ).order_by(Folder.name).all()
        
        tree = []
        for folder in folders:
            tree.append({
                'id': folder.id,
                'name': folder.name,
                'children': build_tree(folder.id)
            })
        return tree
    
    return jsonify({
        'tree': [
            {'id': None, 'name': 'My Documents', 'children': build_tree(None)}
        ]
    })


# Servicio de detección de IA (xota:5006). Igual que xplagiax_marktrack:
# es ASÍNCRONO → POST /analyze_document_async devuelve {task_id}, y se consulta
# GET /analyze_status/{task_id} hasta status == 'ok'.
AI_TEXT_SERVICE_URL = (
    os.environ.get('AI_TEXT_SERVICE_URL')
    or os.environ.get('XPLAGIAX_URL')
    or 'http://localhost:5006/analyze_document_async'
)
AI_TEXT_SERVICE_API_KEY = os.environ.get(
    'AI_TEXT_SERVICE_API_KEY', '7d9a2c4f8e1b3d5a6f7c9e2b4a1d8c3f'
)
AI_POLL_INTERVAL = float(os.environ.get('AI_POLL_INTERVAL', '1.5'))
AI_POLL_TIMEOUT = float(os.environ.get('AI_POLL_TIMEOUT', '120'))


# Modo del servicio de IA: 'sync' usa /analyze_document (inline, SIN worker Celery);
# 'async' usa /analyze_document_async (requiere worker + polling).
# Default 'sync': en este despliegue xota NO tiene worker Celery → el async queda
# 'pending' para siempre. El síncrono procesa en la misma petición.
AI_SERVICE_MODE = os.environ.get('AI_SERVICE_MODE', 'sync').strip().lower()

# Plugins por defecto: idénticos a marktrack (el resultado de ai_detection se usa igual).
AI_DEFAULT_PLUGINS = ['ai_detection', 'citation_check', 'stylometric_analysis']

# El endpoint corto del servicio (POST /analyze) admite textos limitados; por
# encima de este umbral (palabras) se usa /analyze_document, que procesa el
# documento por párrafos sin ese tope. Ajustable por entorno.
AI_ANALYZE_MAX_WORDS = int(os.environ.get('AI_ANALYZE_MAX_WORDS', '600'))

# Por encima de este umbral (palabras), /analyze_document se manda por la vía
# async (/analyze_document_async + poll) SIN IMPORTAR AI_SERVICE_MODE — un
# documento grande procesado inline puede superar el proxy_read_timeout de
# nginx (60s en app.xplagiax.ca, ver documentations/nginx.txt) antes de que
# xota termine, y el cliente nunca ve el resultado de AI TestPro aunque
# FinderX/Citations (que sí son async) sí lleguen. Asume que xota tiene un
# worker Celery vivo (CELERY_BROKER_URL/CELERY_RESULT_BACKEND +
# GUNICORN_SPAWN_CELERY=1 en su despliegue) — si no lo tiene, estos jobs
# quedarían en 'pending' para siempre. Poner en 0 (o un número muy alto)
# desactiva la promoción a async y vuelve al comportamiento previo.
#
# Derivado del propio código de xota (app/routes.py), no a ojo:
#   - adaptive_timeout(word_count) ≈ base(30s) + per_kwords(15s) * (words/1000),
#     tope _SYNC_TIMEOUT_CAP=100s en los endpoints síncronos.
#   - En 2000 palabras ese presupuesto YA iguala los 60s de nginx (30+15*2=60)
#     con margen cero — y esto es por UN plugin; analyze_text() pide 3
#     (ai_detection + citation_check + stylometric_analysis) por defecto, y no
#     tenemos visibilidad de si registry.run() los corre secuencial o en
#     paralelo. Por eso el default queda bien por debajo de ese cruce (1500,
#     ~52.5s de presupuesto para 1 plugin) en vez de pegado al límite.
#   - Ajustar con los logs de 'AI submit finished in Xs' que se agregan más
#     abajo en analyze_text() una vez haya tráfico real.
AI_ASYNC_THRESHOLD_WORDS = int(os.environ.get('AI_ASYNC_THRESHOLD_WORDS', '1500'))


def _user_ai_plugins():
    """Plugins elegidos en Settings › AI & Automation (lista validada, [] = default)."""
    try:
        from modules.users_service.user_routes import _clean_ai_plugins
        from modules.models.model import UserPreference
        pref = UserPreference.query.filter_by(user_id=current_user.id).first()
        raw = getattr(pref, 'ai_plugins', None) if pref else None
        if not raw:
            return []
        return _clean_ai_plugins(json.loads(raw))
    except Exception:
        logger.warning('Could not read AI plugin preferences', exc_info=True)
        return []


def _effective_ai_plugins(requested):
    """Lista final de plugins para el servicio de IA.

    - Preferencias con full_analysis  → ['full_analysis'] (+ forensic_report si
      se marcó): el pipeline completo ya incluye detección/estilometría/citas.
    - Preferencias individuales       → ai_detection (principal) + defaults +
      los seleccionados, sin duplicados.
    - Sin preferencias                → lo pedido por el cliente o el default.
    """
    prefs = _user_ai_plugins()
    if not prefs:
        return list(requested) if requested else list(AI_DEFAULT_PLUGINS)
    if 'full_analysis' in prefs:
        return prefs
    merged = list(AI_DEFAULT_PLUGINS)
    for p in prefs:
        if p not in merged:
            merged.append(p)
    return merged


def _ai_async_urls(word_count=None):
    """Devuelve (submit_url, base_url) del servicio de IA.

    Si la URL configurada apunta al endpoint corto /analyze (limitado en tamaño
    de texto) y el documento supera AI_ANALYZE_MAX_WORDS, se cambia
    automáticamente a /analyze_document (procesa por párrafos, sin ese límite) —
    sin esto, un texto de ~1000 palabras devolvía HTTP 400 del servicio.

    sync vs async: normalmente lo decide AI_SERVICE_MODE, pero un documento por
    encima de AI_ASYNC_THRESHOLD_WORDS se manda async pase lo que pase — inline
    (sync) puede superar el proxy_read_timeout de nginx antes de que xota
    responda (ver AI_ASYNC_THRESHOLD_WORDS arriba).
    """
    submit_url = AI_TEXT_SERVICE_URL
    if submit_url.rstrip('/').endswith('/analyze') and word_count and word_count > AI_ANALYZE_MAX_WORDS:
        submit_url = submit_url.rstrip('/') + '_document'

    oversized = bool(
        AI_ASYNC_THRESHOLD_WORDS > 0 and word_count and word_count > AI_ASYNC_THRESHOLD_WORDS
    )
    use_async = oversized or AI_SERVICE_MODE == 'async'

    if use_async:
        if submit_url.endswith('/analyze_document'):
            submit_url = submit_url + '_async'
    else:
        # Forzar endpoint síncrono (no requiere worker).
        if submit_url.endswith('/analyze_document_async'):
            submit_url = submit_url[:-len('_async')]
    return submit_url, submit_url.rsplit('/', 1)[0]


def _sign_job(kind, real_id):
    """Firma (real_id, user_id) en un token URL-safe sin estado.

    Reemplaza el binding por cookie de sesion, que sufria una carrera cuando el
    front lanza varios analisis en paralelo (Promise.allSettled): el Set-Cookie
    de una respuesta pisaba el de otra y se perdia el job -> 403 al pedir el
    reporte. Firmar con SECRET_KEY es stateless y no depende de la cookie.
    """
    ser = URLSafeSerializer(current_app.secret_key, salt='xpx-job-' + kind)
    return ser.dumps([str(real_id), current_user.id])


def _unsign_job(kind, token):
    """Verifica un token de _sign_job; devuelve el id real o None si es invalido/ajeno."""
    ser = URLSafeSerializer(current_app.secret_key, salt='xpx-job-' + kind)
    try:
        real_id, uid = ser.loads(token)
    except (BadSignature, ValueError, TypeError):
        return None
    if str(uid) != str(current_user.id):
        return None
    return real_id


@x_doc.route('/analyze_text', methods=['POST'])
@login_required
def analyze_text():
    """Encola el análisis de IA (xota:5006) y devuelve task_id de inmediato.

    NO bloquea el worker: el navegador consulta /x_doc/analyze_status/<task_id>.
    Así un servicio lento no puede agotar los workers ni congelar la app.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text or len(text.split()) < 10:
        return jsonify({'error': 'Please enter at least 10 words to analyze.'}), 400

    # Server-side gate (defense in depth): the client already checks/counts via
    # /x_analysiscounter/api/analysis/perform before calling this endpoint, but
    # this endpoint must not trust that — a direct call bypassing the UI must
    # still be rejected. Read-only check, does NOT increment (counting happens
    # exactly once, in the counter endpoint).
    if not current_user.can_perform_analysis():
        return jsonify({
            'error': 'Daily analysis limit reached',
            'limit_reached': True,
            'stats': current_user.get_analysis_stats()
        }), 403

    # Plugins efectivos: preferencias del usuario (Settings › AI & Automation)
    # mandan sobre lo que pida el cliente; sin preferencias, comportamiento actual.
    plugins = _effective_ai_plugins(data.get('plugins'))
    word_count = len(text.split())
    submit_url, _ = _ai_async_urls(word_count)
    headers = {'Content-Type': 'application/json', 'X-API-Key': AI_TEXT_SERVICE_API_KEY}
    payload = {'text': text, 'plugins': plugins, 'max_tokens': 150}

    def _post(url):
        return session_pool.post(
            url, headers=headers, json=payload,
            # Modo sync procesa inline (tarda unos segundos) → read timeout amplio.
            timeout=(5, 90),
        )

    # Sin tiempos reales de xota por tamaño de documento — este log es la
    # fuente para calibrar AI_ASYNC_THRESHOLD_WORDS con datos en vez de
    # a ojo (ver el comentario en la definición de esa constante).
    t0 = time.monotonic()
    try:
        submit = _post(submit_url)
        # Fallback tamaño: el endpoint corto /analyze rechaza con 400 los textos
        # que exceden su límite. Reintentar UNA vez contra /analyze_document
        # (por párrafos, sin ese tope) antes de rendirse.
        if submit.status_code == 400 and submit_url.rstrip('/').endswith('/analyze'):
            doc_url = submit_url.rstrip('/') + '_document'
            logger.info('AI submit got 400 on /analyze — retrying via %s', doc_url)
            submit = _post(doc_url)
    except requests.exceptions.RequestException as exc:
        logger.error('AI submit failed after %.1fs (word_count=%d, url=%s): %s',
                      time.monotonic() - t0, word_count, submit_url, exc)
        return jsonify({'error': 'Could not reach the analysis service.'}), 502
    logger.info('AI submit finished in %.1fs (word_count=%d, url=%s, status=%s)',
                time.monotonic() - t0, word_count, submit_url, submit.status_code)
    if not submit.ok:
        logger.error('AI submit returned %s: %s', submit.status_code, submit.text[:300])
        if submit.status_code == 400:
            return jsonify({'error': 'The analysis service rejected this text. '
                                     'Try a shorter document or try again later.'}), 502
        return jsonify({'error': f'Analysis service error ({submit.status_code}).'}), 502

    try:
        sd = submit.json()
    except ValueError:
        return jsonify({'error': 'Invalid response from analysis service.'}), 502

    logger.info('AI submit OK → keys=%s', list(sd.keys()))

    # Si el servicio ya respondió síncrono con el resultado, devolverlo.
    if sd.get('results'):
        return jsonify({'done': True, 'result': sd}), 200

    inner = sd.get('data', sd) if isinstance(sd.get('data'), dict) else sd
    task_id = (sd.get('task_id') or sd.get('job_id') or sd.get('id')
               or inner.get('task_id') or inner.get('job_id') or inner.get('id'))
    if not task_id:
        logger.error('AI submit missing task_id: %s', str(sd)[:300])
        return jsonify({'error': 'Analysis service did not return a task id.'}), 502

    # Token firmado sin estado (evita la carrera de la cookie con analisis en paralelo).
    token = _sign_job('ai', task_id)

    return jsonify({'done': False, 'task_id': token}), 202


@x_doc.route('/analyze_status/<task_id>', methods=['GET'])
@login_required
def analyze_status(task_id):
    """Proxy rápido del estado del análisis de IA (no bloquea el worker)."""
    real_id = _unsign_job('ai', task_id)
    if real_id is None:
        return jsonify({'error': 'Task not found or access denied.'}), 403
    task_id = real_id
    _, base_url = _ai_async_urls()
    headers = {'Content-Type': 'application/json', 'X-API-Key': AI_TEXT_SERVICE_API_KEY}
    try:
        poll = session_pool.get(
            f'{base_url}/analyze_status/{task_id}', headers=headers, timeout=(5, 25)
        )
    except requests.exceptions.RequestException as exc:
        logger.error('AI poll failed: %s', exc)
        return jsonify({'error': 'Could not reach the analysis service.'}), 502
    if not poll.ok:
        logger.error('AI poll returned %s: %s', poll.status_code, poll.text[:300])
        return jsonify({'error': f'Analysis service error ({poll.status_code}).'}), 502
    try:
        pdata = poll.json()
    except ValueError:
        return jsonify({'error': 'Invalid response from analysis service.'}), 502
    logger.info('AI status %s → status=%r keys=%s', task_id, pdata.get('status'), list(pdata.keys()))
    return jsonify(pdata), 200


# ── FinderX: servicio de búsqueda de fuentes / plagio académico ──────────────
FINDERX_SERVICE_BASE = (
    os.environ.get('FINDERX_SERVICE_BASE')
    or os.environ.get('FINDERX_URL')
    or 'http://localhost:8000'
)
FINDERX_SERVICE_API_KEY = (
    os.environ.get('FINDERX_SERVICE_API_KEY')
    or os.environ.get('FINDERX_API_KEY')
    or 'xpx-3Td8C2oecnAXRT0-VioypUjMWTtSTQVj3k2kE8Q-5tc'
)

# ── marktrack: misma identidad de usuario (users compartida), servicio hermano.
# Usado SOLO para el borrado interno servidor-a-servidor (Delete All Documents) —
# nunca invocado desde el navegador. Clave compartida con marktrack's
# INTERNAL_SERVICE_KEY (routes/document_routes.py), mismo patrón que el
# X-API-Key que ambas apps ya usan para hablar con FinderX.
MARKTRACK_SERVICE_BASE = (
    os.environ.get('MARKTRACK_SERVICE_BASE')
    or os.environ.get('MARKTRACK_URL')
    or 'http://localhost:5001'
)
MARKTRACK_INTERNAL_KEY = (
    os.environ.get('MARKTRACK_INTERNAL_KEY')
    or os.environ.get('INTERNAL_SERVICE_KEY')
    or 'xpx-internal-4f8c2a9d6e1b7f3c5a8d2e9b4c7f1a6d'
)


@x_doc.route('/finderx_check', methods=['POST'])
@login_required
def finderx_check():
    """Encola el análisis en FinderX (:8000) y devuelve job_id de inmediato.

    NO bloquea el worker: el navegador consulta /x_doc/finderx_report/<job_id>.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text or len(text.split()) < 10:
        return jsonify({'error': 'Please enter at least 10 words to analyze.'}), 400

    # Server-side gate (defense in depth) — see analyze_text() above for rationale.
    if not current_user.can_perform_analysis():
        return jsonify({
            'error': 'Daily analysis limit reached',
            'limit_reached': True,
            'stats': current_user.get_analysis_stats()
        }), 403

    priority = data.get('priority') or 'default'
    headers = {'Content-Type': 'application/json', 'X-API-Key': FINDERX_SERVICE_API_KEY}

    try:
        submit = session_pool.post(
            # FinderX ≥2.0: el tab "Plagiarism checker" usa el modo FULL
            # (/api/v1/analyze = internet + académico). Antes usaba
            # /academic-check, pero ese modo no puede detectar copias de la web
            # (Wikipedia, blogs, noticias): solo consulta corpus académicos y el
            # provider MediaWiki con recall limitado — un copy-paste de
            # Wikipedia salía como "original". El modo full agrega búsqueda web
            # real (SearXNG) y si SearXNG no está desplegado degrada solo a
            # académico (mismo comportamiento anterior, sin romper nada). El
            # contrato de respuesta (segment_matches/segment_summary/scores) es
            # idéntico en ambos modos; se suma internet_matches.
            f'{FINDERX_SERVICE_BASE}/api/v1/analyze',
            headers=headers,
            # 500k cap (was 50k): FinderX distributes an adaptive, capped chunk
            # budget (max_chunks_cap=60) across the WHOLE document, so a thesis is
            # sampled end-to-end instead of only its first ~20%. Embedding/corpus
            # cost is bounded by the chunk cap, not text length; only local
            # segmentation grows. Matches the citation-validation cap.
            json={'text': text[:500000], 'priority': priority},
            timeout=(5, 20),
        )
    except requests.exceptions.RequestException as exc:
        logger.error('FinderX submit failed: %s', exc)
        return jsonify({'error': 'Could not reach the FinderX service.'}), 502
    if not submit.ok:
        logger.error('FinderX submit returned %s: %s', submit.status_code, submit.text[:300])
        return jsonify({'error': f'FinderX service error ({submit.status_code}).'}), 502

    try:
        sd = submit.json()
    except ValueError:
        return jsonify({'error': 'Invalid response from FinderX service.'}), 502

    # La API envuelve bajo 'data'; el campo es 'task_id' (o job_id/id/taskId).
    inner = sd.get('data', sd)

    # Cache hit de FinderX: el submit devuelve el reporte completo directamente
    # ({'cached': True, 'report': {...}}) en vez de un task_id — sin este manejo
    # un texto repetido fallaba con "did not return a job id".
    if inner.get('cached') and isinstance(inner.get('report'), dict):
        rep = inner['report']
        res = rep.get('result') if isinstance(rep.get('result'), dict) else (
            rep if 'scores' in rep else None)
        if res:
            return jsonify({'done': True, 'status': 'completed', 'result': res}), 200

    job_id = (inner.get('task_id') or inner.get('job_id')
              or inner.get('id') or inner.get('taskId'))
    if not job_id:
        logger.error('FinderX submit missing task_id: %s', str(sd)[:300])
        return jsonify({'error': 'FinderX did not return a job id.'}), 502

    # Token firmado sin estado (evita la carrera de la cookie con analisis en paralelo).
    token = _sign_job('fx', job_id)

    return jsonify({'done': False, 'job_id': token, 'status': inner.get('status')}), 202


@x_doc.route('/finderx_report/<job_id>', methods=['GET'])
@login_required
def finderx_report(job_id):
    """Proxy rápido del reporte de FinderX (no bloquea el worker)."""
    real_id = _unsign_job('fx', job_id)
    if real_id is None:
        return jsonify({'error': 'Job not found or access denied.'}), 403
    job_id = real_id
    headers = {'Content-Type': 'application/json', 'X-API-Key': FINDERX_SERVICE_API_KEY}
    try:
        report = session_pool.get(
            f'{FINDERX_SERVICE_BASE}/api/v1/report/{job_id}', headers=headers, timeout=(5, 25)
        )
    except requests.exceptions.RequestException as exc:
        logger.error('FinderX report failed: %s', exc)
        return jsonify({'error': 'Could not reach the FinderX service.'}), 502
    if not report.ok:
        logger.error('FinderX report returned %s: %s', report.status_code, report.text[:300])
        return jsonify({'error': f'FinderX service error ({report.status_code}).'}), 502
    try:
        rdata = report.json()
    except ValueError:
        return jsonify({'error': 'Invalid response from FinderX service.'}), 502

    # FinderX envuelve todo bajo 'data'. Desenvolver para que el front vea status/result.
    inner = rdata.get('data') if isinstance(rdata.get('data'), dict) else rdata
    # El resultado puede estar como inner['result'] o ser inner mismo (con scores).
    result = inner.get('result') if isinstance(inner.get('result'), dict) else (
        inner if (isinstance(inner, dict) and 'scores' in inner) else None)
    out = {
        'status': inner.get('status'),
        'result': result,
        'success': rdata.get('success', True),
    }
    logger.info('FinderX report %s → status=%r inner_keys=%s has_result=%s',
                job_id, out['status'], list(inner.keys()) if isinstance(inner, dict) else None,
                bool(result))
    return jsonify(out), 200


@x_doc.route('/citation_validation', methods=['POST'])
@login_required
def citation_validation():
    """Encola la validación de citas en FinderX (:8000) y devuelve job_id de inmediato.

    NO bloquea el worker: el navegador consulta /x_doc/citation_validation_report/<job_id>.
    A diferencia de /finderx_check (búsqueda de fuentes/plagio), esto NO busca en el
    corpus académico: solo detecta y valida las citas/referencias del texto.

    Antes este endpoint hacía el poll a /api/v1/task/<id> AQUÍ MISMO con
    time.sleep() (hasta 175s) — con gunicorn --worker-class sync y solo
    WEB_CONCURRENCY=3, una sola validación de citas podía secuestrar un worker
    completo por minutos: si 2 caían en esa espera simultáneamente, no quedaba
    capacidad para atender NINGUNA otra petición (incl. /finderx_check) →
    gunicorn mataba el worker colgado a los --timeout 120 → nginx veía la
    conexión cortada → 502 en peticiones que no tenían nada que ver. Sumado a
    que nginx tenía proxy_read_timeout 60s en esta ruta, la propia validación
    de citas también salía como 504 antes de que el backend terminara. Se
    resuelve con el mismo patrón submit+poll que ya usa finderx_check/
    finderx_report: cada petición HTTP es rápida (un solo proxy a FinderX), y
    quien espera es el navegador, no un worker de gunicorn.
    """
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text or len(text.split()) < 10:
        return jsonify({'error': 'Please enter at least 10 words to analyze.'}), 400

    # Server-side gate (defense in depth) — see analyze_text() above for rationale.
    if not current_user.can_perform_analysis():
        return jsonify({
            'error': 'Daily analysis limit reached',
            'limit_reached': True,
            'stats': current_user.get_analysis_stats()
        }), 403

    headers = {'Content-Type': 'application/json', 'X-API-Key': FINDERX_SERVICE_API_KEY}
    try:
        submit = session_pool.post(
            f'{FINDERX_SERVICE_BASE}/api/v1/citation-validation',
            headers=headers,
            # enrich=True → parity with marktrack: adds ORCID (authors), ROR
            # (institutions) and OpenCitations (citation network / cited-by) per
            # resolved reference. Does NOT change valid/partial/not_found verdicts
            # (see finderx validator.py:290 — enrichment runs after validation).
            #
            # 500k char cap (NOT the 50k the plagiarism check uses): the
            # bibliography sits at the END of long documents (theses), so a 50k
            # cut drops the whole References section → 0 refs, all citations
            # orphaned. FinderX accepts up to 800k and reference validation cost
            # scales with the NUMBER of refs, not text length, so this is safe.
            json={'text': text[:500000], 'validate': True, 'enrich': True},
            # This call only ENQUEUES (validate=true always returns 202+task_id
            # server-side, see finderx analyze.py:citation_validation) — it does
            # not wait for the validation itself, so a short read timeout is enough.
            timeout=(5, 20),
        )
    except requests.exceptions.RequestException as exc:
        logger.error('FinderX citation submit failed: %s', exc)
        return jsonify({'error': 'Could not reach the FinderX service.'}), 502
    if not submit.ok:
        logger.error('FinderX citation submit returned %s: %s', submit.status_code, submit.text[:300])
        return jsonify({'error': f'FinderX service error ({submit.status_code}).'}), 502

    try:
        sd = submit.json()
    except ValueError:
        return jsonify({'error': 'Invalid response from FinderX service.'}), 502

    # La API envuelve el resultado bajo 'data'.
    inner = sd.get('data', sd) if isinstance(sd, dict) else sd

    # validate=false (offline) ya viene resuelto — sin task_id que pollear.
    if isinstance(inner, dict) and 'detected_style' in inner:
        return jsonify({'done': True, 'result': inner}), 200

    job_id = (inner.get('task_id') or inner.get('job_id')
              or inner.get('id') or inner.get('taskId')) if isinstance(inner, dict) else None
    if not job_id:
        logger.error('FinderX citation submit missing task_id: %s', str(sd)[:300])
        return jsonify({'error': 'FinderX did not return a job id.'}), 502

    # Token firmado sin estado, namespace propio ('cv') — no intercambiable con
    # los job_id de /finderx_check ('fx') aunque ambos apunten a Redis de FinderX.
    token = _sign_job('cv', job_id)
    return jsonify({'done': False, 'job_id': token, 'status': inner.get('status')}), 202


@x_doc.route('/citation_validation_report/<job_id>', methods=['GET'])
@login_required
def citation_validation_report(job_id):
    """Proxy rápido del reporte de validación de citas (no bloquea el worker)."""
    real_id = _unsign_job('cv', job_id)
    if real_id is None:
        return jsonify({'error': 'Job not found or access denied.'}), 403
    job_id = real_id
    headers = {'Content-Type': 'application/json', 'X-API-Key': FINDERX_SERVICE_API_KEY}
    try:
        poll = session_pool.get(
            f'{FINDERX_SERVICE_BASE}/api/v1/task/{job_id}', headers=headers, timeout=(5, 25)
        )
    except requests.exceptions.RequestException as exc:
        logger.error('FinderX citation report failed: %s', exc)
        return jsonify({'error': 'Could not reach the FinderX service.'}), 502
    if not poll.ok:
        logger.error('FinderX citation report returned %s: %s', poll.status_code, poll.text[:300])
        return jsonify({'error': f'FinderX service error ({poll.status_code}).'}), 502
    try:
        pd = poll.json()
    except ValueError:
        return jsonify({'error': 'Invalid response from FinderX service.'}), 502

    inner = pd.get('data', pd) if isinstance(pd, dict) else {}
    status = str(inner.get('status') or '').lower()
    out = {
        'status': status,
        'result': inner.get('result') if status == 'completed' else None,
        'error': inner.get('error') if status in ('failed', 'error', 'not_found') else None,
    }
    logger.info('FinderX citation report %s → status=%r has_result=%s',
                job_id, status, bool(out['result']))
    return jsonify(out), 200


# ════════════════════════════════════════════════════════════════════════════
# Analysis history (pantalla "analysiss") — persistido en MySQL por usuario.
# Todos los planes PAGOS: Scholar Suite, Individual, Research Essentials,
# Institutes (alineado con la definición de "plan pago" en Users, model.py).
# Starter (gratis) no guarda historial.
# ════════════════════════════════════════════════════════════════════════════
HISTORY_PLANS = {'Scholar Suite', 'Individual', 'Research Essentials', 'Institutes'}
HISTORY_MAX_PER_USER = 50


def _history_allowed():
    return getattr(current_user, 'user_type', None) in HISTORY_PLANS


_RESULT_VIEW_COL_READY = False


def _ensure_result_view_column():
    """Auto-migración idempotente: añade la columna `result_view` a analysis_history
    si falta. Necesario porque el proyecto crea tablas con db.create_all() (que NO
    altera tablas existentes); así el guardado de historial no se rompe en despliegues
    que aún no tienen la columna, sin exigir una migración manual."""
    global _RESULT_VIEW_COL_READY
    if _RESULT_VIEW_COL_READY:
        return
    try:
        from sqlalchemy import inspect as _sa_inspect, text as _sa_text
        cols = [c['name'] for c in _sa_inspect(db.engine).get_columns('analysis_history')]
        if 'result_view' not in cols:
            db.session.execute(_sa_text(
                "ALTER TABLE analysis_history ADD COLUMN result_view VARCHAR(512) NULL"))
            db.session.commit()
        _RESULT_VIEW_COL_READY = True
    except Exception:
        db.session.rollback()
        # No marcar READY: se reintentará en el próximo guardado.
        logger.warning('Could not ensure analysis_history.result_view column', exc_info=True)


def _sanitize_result_view(value):
    """Solo se persiste una URL relativa de nuestra propia ruta de servido
    (/x_doc/serve_analysis/...). Evita almacenar rutas absolutas del servidor,
    URLs externas o valores arbitrarios."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > 512:
        return None
    return value if value.startswith('/x_doc/serve_analysis/') else None


def _trim_history_result(r):
    """Quita campos pesados (abstract/full_text) — los paneles usan snippet/blocks."""
    if not isinstance(r, dict):
        return r
    import copy
    c = copy.deepcopy(r)
    for key in ('academic_matches', 'internet_matches'):
        arr = c.get(key)
        if isinstance(arr, list):
            arr = arr[:12]
            for m in arr:
                if isinstance(m, dict):
                    m.pop('full_text', None)
                    m.pop('abstract', None)
            c[key] = arr
    return c


@x_doc.route('/history', methods=['POST'])
@login_required
def history_save():
    if not _history_allowed():
        return jsonify({'error': 'Your plan does not include analysis history.', 'allowed': False}), 403
    from modules.models.model import AnalysisHistory
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'Empty analysis.'}), 400

    # Garantizar la columna result_view (auto-migración idempotente) antes de insertar.
    _ensure_result_view_column()

    def _int(v):
        try:
            return int(round(float(v))) if v is not None else None
        except (TypeError, ValueError):
            return None

    entry = AnalysisHistory(
        user_id=current_user.id,
        title=(data.get('title') or text[:80]),
        text=text[:15000],
        ai=_trim_history_result(data.get('ai')),
        source=_trim_history_result(data.get('source')),
        citation=_trim_history_result(data.get('citation')),
        ai_pct=_int(data.get('aiPct')),
        overall=_int(data.get('overall')),
        cit_score=_int(data.get('cit')),
        result_view=_sanitize_result_view(data.get('resultView')),
    )
    try:
        db.session.add(entry)
        db.session.flush()
        # Conservar solo las últimas N por usuario.
        stale = (AnalysisHistory.query
                 .filter_by(user_id=current_user.id)
                 .order_by(AnalysisHistory.created_at.desc())
                 .offset(HISTORY_MAX_PER_USER).all())
        for s in stale:
            db.session.delete(s)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception('history_save failed')
        return jsonify({'error': 'Could not save history.'}), 500
    return jsonify({'id': entry.history_id}), 201


@x_doc.route('/history', methods=['GET'])
@login_required
def history_list():
    if not _history_allowed():
        return jsonify({'items': [], 'allowed': False}), 200
    from modules.models.model import AnalysisHistory, AnalysisShare, Users
    _ensure_analysis_shares_table()
    rows = (AnalysisHistory.query
            .filter_by(user_id=current_user.id)
            .order_by(AnalysisHistory.created_at.desc())
            .limit(HISTORY_MAX_PER_USER).all())
    items = []
    try:
        own_ids = [r.id for r in rows]
        shares_by_analysis = {}
        if own_ids:
            for s in AnalysisShare.query.filter(AnalysisShare.analysis_id.in_(own_ids)).all():
                shares_by_analysis.setdefault(s.analysis_id, []).append(s.to_dict())
        for r in rows:
            d = r.to_summary()
            if shares_by_analysis.get(r.id):
                d['sharedWith'] = shares_by_analysis[r.id]
            items.append(d)

        # Análisis que OTROS usuarios compartieron conmigo (siguen viviendo en la
        # fila del dueño: si él la borra, el join deja de devolverla — cascade real).
        incoming = (db.session.query(AnalysisShare, AnalysisHistory)
                    .join(AnalysisHistory, AnalysisShare.analysis_id == AnalysisHistory.id)
                    .filter(AnalysisShare.shared_with_id == current_user.id)
                    .order_by(AnalysisHistory.created_at.desc())
                    .limit(HISTORY_MAX_PER_USER).all())
        owner_ids = {h.user_id for _, h in incoming}
        owners = {u.id: u.email for u in Users.query.filter(Users.id.in_(owner_ids)).all()} if owner_ids else {}
        for s, h in incoming:
            d = h.to_summary()
            d['shared'] = True
            d['sharedBy'] = owners.get(h.user_id, 'another user')
            items.append(d)
        items.sort(key=lambda x: x.get('ts') or 0, reverse=True)
    except Exception:
        # Si la tabla de shares aún no existe (primer despliegue), el historial
        # propio sigue funcionando sin la capa de compartidos.
        logger.warning('history_list: shares layer unavailable', exc_info=True)
        items = [r.to_summary() for r in rows]
    return jsonify({'items': items, 'allowed': True}), 200


@x_doc.route('/history/<hid>', methods=['GET'])
@login_required
def history_get(hid):
    from modules.models.model import AnalysisHistory, AnalysisShare
    r = AnalysisHistory.query.filter_by(user_id=current_user.id, history_id=hid).first()
    if not r:
        # Receptor de un share: puede abrir/visualizar el análisis compartido.
        try:
            _ensure_analysis_shares_table()
            r = (db.session.query(AnalysisHistory)
                 .join(AnalysisShare, AnalysisShare.analysis_id == AnalysisHistory.id)
                 .filter(AnalysisHistory.history_id == hid,
                         AnalysisShare.shared_with_id == current_user.id)
                 .first())
        except Exception:
            r = None
    if not r:
        return jsonify({'error': 'Not found.'}), 404
    return jsonify({'item': r.to_full()}), 200


@x_doc.route('/history/<hid>', methods=['DELETE'])
@login_required
def history_delete(hid):
    from modules.models.model import AnalysisHistory, AnalysisShare
    r = AnalysisHistory.query.filter_by(user_id=current_user.id, history_id=hid).first()
    if r:
        # Cascade explícito: al borrar el dueño, desaparece para todos los receptores.
        try:
            AnalysisShare.query.filter_by(analysis_id=r.id).delete(synchronize_session=False)
        except Exception:
            db.session.rollback()
            r = AnalysisHistory.query.filter_by(user_id=current_user.id, history_id=hid).first()
        db.session.delete(r)
        db.session.commit()
    return jsonify({'ok': True}), 200


@x_doc.route('/history', methods=['DELETE'])
@login_required
def history_clear():
    from modules.models.model import AnalysisHistory, AnalysisShare
    ids = [r.id for r in AnalysisHistory.query.filter_by(user_id=current_user.id).all()]
    if ids:
        # Cascade explícito (además del FK): el borrado del dueño hace desaparecer
        # el análisis también para todos los receptores.
        AnalysisShare.query.filter(AnalysisShare.analysis_id.in_(ids)).delete(synchronize_session=False)
    AnalysisHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'ok': True}), 200


# ════════════════════════════════════════════════════════════════════════════
# Compartir análisis (historial) — con usuarios de la plataforma (aparece en su
# historial como "shared") o con correos externos (email HTML + PDF adjunto).
# Solo planes de pago (mismo gate que el historial: no Starter).
# ════════════════════════════════════════════════════════════════════════════
_SHARES_TABLE_READY = False


def _ensure_analysis_shares_table():
    """Auto-migración idempotente: crea analysis_shares si falta (el proyecto usa
    db.create_all() al arrancar, pero despliegues ya corriendo no la tendrían)."""
    global _SHARES_TABLE_READY
    if _SHARES_TABLE_READY:
        return
    try:
        from modules.models.model import AnalysisShare
        AnalysisShare.__table__.create(bind=db.engine, checkfirst=True)
        _SHARES_TABLE_READY = True
    except Exception:
        db.session.rollback()
        logger.warning('Could not ensure analysis_shares table', exc_info=True)


_XPA_BRAND = {'primary': '#064CDB', 'ink': '#0f172a', 'muted': '#64748b',
              'ai': '#ef4444', 'plag': '#f59e0b', 'ok': '#10b981', 'bg': '#f8fafc'}


# Base pública para el link/QR del reporte. Constante por entorno (mismo
# criterio que el fix de OAuth redirect URIs: url_for(_external=True) detrás
# de nginx generaba hosts equivocados, así que no se usa aquí).
PUBLIC_REPORT_BASE = (os.environ.get('PUBLIC_REPORT_BASE')
                      or 'https://app.xplagiax.ca').rstrip('/')


def _public_report_token(entry):
    """Token firmado y sin estado para la vista pública del reporte.

    Solo el id — la pantalla es de solo lectura y únicamente alcanzable con
    este token (QR/link del PDF). Revocación: borrar el análisis del
    historial invalida la vista (la ruta hace 404 si la fila no existe)."""
    ser = URLSafeSerializer(current_app.secret_key, salt='xpx-public-report')
    return ser.dumps([entry.history_id])


def _public_report_url(entry):
    return f'{PUBLIC_REPORT_BASE}/x_doc/report/{_public_report_token(entry)}'


def _share_pdf_bytes(entry, sender_email):
    """PDF enterprise del análisis (ver modules/doc_service/report_pdf.py):
    portada + QR de verificación, resumen ejecutivo, KPIs, distribución,
    risk assessment, fuentes, hallazgos por segmento, citas, métricas,
    interpretación y recomendaciones. Devuelve bytes."""
    from modules.doc_service.report_pdf import build_report_pdf
    return build_report_pdf(entry, sender_email, public_url=_public_report_url(entry))


def _share_email_html(entry, sender_email):
    """Cuerpo HTML del correo (CSS inline, colores de la app): overview + remitente."""
    B = _XPA_BRAND

    def _pct(v, unit='%'):
        return '—' if v is None else f'{int(v)}{unit}'

    def _tile(label, value, color):
        return (f'<td style="padding:14px 16px;background:{B["bg"]};border:1px solid #e2e8f0;'
                f'border-radius:10px;text-align:center;">'
                f'<div style="font-size:11px;font-weight:700;color:{B["muted"]};'
                f'text-transform:uppercase;letter-spacing:.06em;">{label}</div>'
                f'<div style="font-size:24px;font-weight:800;color:{color};margin-top:4px;">{value}</div></td>')

    title = (entry.title or 'Untitled analysis').replace('<', '&lt;')
    preview = (entry.text or '')[:220].replace('<', '&lt;')
    return f"""
<div style="margin:0;padding:24px;background:#eef2f7;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e2e8f0;">
    <div style="background:{B['primary']};padding:20px 26px;">
      <div style="color:#ffffff;font-size:17px;font-weight:800;letter-spacing:.02em;">
        <span style="opacity:.85;">&times;</span>plagia<span style="opacity:.85;">&times;</span>
      </div>
      <div style="color:rgba(255,255,255,.75);font-size:12px;margin-top:2px;">AI TestPro · FinderX — Analysis Report</div>
    </div>
    <div style="padding:26px;">
      <p style="margin:0 0 6px;font-size:13px;color:{B['muted']};">
        <b style="color:{B['ink']};">{sender_email}</b> shared an analysis with you.</p>
      <h2 style="margin:0 0 14px;font-size:17px;line-height:1.35;color:{B['ink']};">{title}</h2>
      <table role="presentation" width="100%" cellspacing="8" cellpadding="0" style="border-collapse:separate;">
        <tr>
          {_tile('AI Content', _pct(entry.ai_pct), B['ai'])}
          {_tile('Similarity', _pct(entry.overall), B['plag'])}
          {_tile('Citations', _pct(entry.cit_score, '/100'), B['primary'])}
        </tr>
      </table>
      <div style="margin-top:16px;padding:14px 16px;background:{B['bg']};border-left:3px solid {B['primary']};
                  border-radius:0 10px 10px 0;font-size:13px;line-height:1.55;color:#334155;">
        <b style="color:{B['ink']};">Overview.</b> {preview}…
      </div>
      <p style="margin:18px 0 0;font-size:12.5px;line-height:1.6;color:{B['muted']};">
        The full report is attached as a PDF. It includes the executive summary, source
        matches, per-segment findings and recommendations.</p>
      <div style="margin-top:16px;text-align:center;">
        <a href="{_public_report_url(entry)}"
           style="display:inline-block;background:{B['primary']};color:#ffffff;text-decoration:none;
                  font-size:13px;font-weight:700;padding:11px 22px;border-radius:10px;">
          View interactive report</a>
        <p style="margin:8px 0 0;font-size:11px;color:{B['muted']};">
          Same link as the QR code inside the PDF — read-only, no account required.</p>
      </div>
    </div>
    <div style="padding:14px 26px;background:{B['bg']};border-top:1px solid #e2e8f0;">
      <p style="margin:0;font-size:11px;color:{B['muted']};">
        Sent via XplagiaX on behalf of {sender_email}. If you weren't expecting this email you can ignore it.</p>
    </div>
  </div>
</div>"""


@x_doc.route('/history/<hid>/share', methods=['POST'])
@login_required
def history_share(hid):
    if not _history_allowed():
        return jsonify({'error': 'Sharing is available on paid plans only.', 'allowed': False}), 403
    from modules.models.model import AnalysisHistory, AnalysisShare, Users
    _ensure_analysis_shares_table()

    entry = AnalysisHistory.query.filter_by(user_id=current_user.id, history_id=hid).first()
    if not entry:
        return jsonify({'error': 'Analysis not found.'}), 404

    data = request.get_json(silent=True) or {}
    raw_emails = data.get('emails') or []
    emails, seen = [], set()
    for e in raw_emails:
        e = str(e or '').strip().lower()
        if e and e not in seen and re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', e):
            seen.add(e)
            emails.append(e)
    if not emails:
        return jsonify({'error': 'No valid email addresses.'}), 400
    if len(emails) > 20:
        return jsonify({'error': 'Too many recipients (max 20).'}), 400

    results = []
    pdf_bytes = None
    for email in emails:
        if email == (current_user.email or '').lower():
            results.append({'email': email, 'status': 'skipped', 'reason': 'own account'})
            continue
        target = Users.query.filter_by(email=email).first()
        existing = AnalysisShare.query.filter_by(analysis_id=entry.id, email=email).first()
        if existing:
            results.append({'email': email, 'status': 'already_shared'})
            continue
        share = AnalysisShare(analysis_id=entry.id, owner_id=current_user.id,
                              shared_with_id=target.id if target else None, email=email)
        db.session.add(share)
        if target:
            results.append({'email': email, 'status': 'shared'})
        else:
            # Externo: email HTML profesional + PDF adjunto (best-effort por destinatario).
            # Usa EmailService (provider + fallback) en vez del objeto `mail` global de
            # settings.connections: ese nunca recibe mail.init_app(app) en app.py, así
            # que mail.send() siempre lanzaba (RuntimeError: extensión no registrada) y
            # todo external share terminaba en status 'error' pase lo que pase.
            try:
                from settings.email_service import EmailService
                if pdf_bytes is None:
                    pdf_bytes = _share_pdf_bytes(entry, current_user.email)
                result = EmailService.send_email(
                    subject=f'{current_user.email} shared an XplagiaX analysis with you',
                    recipients=[email],
                    html_content=_share_email_html(entry, current_user.email),
                    provider='noreply', fallback_provider='gmail',
                    attachments=[('xplagiax-analysis-report.pdf', 'application/pdf', pdf_bytes)],
                )
                if not result['success']:
                    raise RuntimeError(result['message'])
                results.append({'email': email, 'status': 'emailed'})
            except Exception:
                logger.exception('share email failed for %s', email)
                db.session.expunge(share)
                results.append({'email': email, 'status': 'error', 'reason': 'email delivery failed'})
    db.session.commit()
    shares = AnalysisShare.query.filter_by(analysis_id=entry.id).all()
    return jsonify({'ok': True, 'results': results,
                    'shares': [s.to_dict() for s in shares]}), 200


@x_doc.route('/history/<hid>/shares', methods=['GET'])
@login_required
def history_shares(hid):
    from modules.models.model import AnalysisHistory, AnalysisShare
    _ensure_analysis_shares_table()
    entry = AnalysisHistory.query.filter_by(user_id=current_user.id, history_id=hid).first()
    if not entry:
        return jsonify({'error': 'Analysis not found.'}), 404
    shares = AnalysisShare.query.filter_by(analysis_id=entry.id).all()
    return jsonify({'shares': [s.to_dict() for s in shares]}), 200


@x_doc.route('/history/<hid>/share/<int:share_id>', methods=['DELETE'])
@login_required
def history_unshare(hid, share_id):
    """Revoca UN destinatario (el modal de compartir ahora permite editar la
    lista, no solo agregar). share_id se valida contra entry.id, que ya está
    acotado a current_user.id — no alcanza con adivinar un share_id ajeno."""
    from modules.models.model import AnalysisHistory, AnalysisShare
    _ensure_analysis_shares_table()
    entry = AnalysisHistory.query.filter_by(user_id=current_user.id, history_id=hid).first()
    if not entry:
        return jsonify({'error': 'Analysis not found.'}), 404
    share = AnalysisShare.query.filter_by(id=share_id, analysis_id=entry.id).first()
    if not share:
        return jsonify({'error': 'Share not found.'}), 404
    db.session.delete(share)
    db.session.commit()
    return jsonify({'ok': True}), 200


@x_doc.route('/report/<token>', methods=['GET'])
def public_report(token):
    """Vista pública de solo lectura del reporte — la pantalla del QR/link del
    PDF. SIN @login_required a propósito: el token firmado ES la credencial
    (solo lo tiene quien recibió el PDF/email). No aparece en ninguna
    navegación de la app; noindex para que tampoco la indexen buscadores.
    Se invalida sola cuando el dueño borra el análisis del historial."""
    from modules.models.model import AnalysisHistory
    ser = URLSafeSerializer(current_app.secret_key, salt='xpx-public-report')
    try:
        payload = ser.loads(token)
        hid = payload[0] if isinstance(payload, list) else payload
    except (BadSignature, ValueError, TypeError, IndexError):
        abort(404)
    entry = AnalysisHistory.query.filter_by(history_id=str(hid)).first()
    if not entry:
        abort(404)

    from modules.doc_service.report_pdf import (extract_report_data, risk_explanation,
                                                risk_factors, recommendations, interpretation)
    d = extract_report_data(entry)
    resp = current_app.make_response(render_template(
        'user/shared_report.html', d=d,
        explanation=risk_explanation(d), factors=risk_factors(d),
        recs=recommendations(d), interpretation=interpretation(d)))
    resp.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return resp


@x_doc.route('/history/<hid>/report.pdf', methods=['GET'])
@login_required
def history_report_pdf(hid):
    """Descarga directa del PDF enterprise (antes solo existía adjunto en el
    email de share externo). Dueño del análisis o usuario con quien se
    compartió (AnalysisShare.shared_with_id)."""
    from modules.models.model import AnalysisHistory, AnalysisShare
    entry = AnalysisHistory.query.filter_by(user_id=current_user.id, history_id=hid).first()
    if not entry:
        _ensure_analysis_shares_table()
        entry = (AnalysisHistory.query
                 .join(AnalysisShare, AnalysisShare.analysis_id == AnalysisHistory.id)
                 .filter(AnalysisHistory.history_id == hid,
                         AnalysisShare.shared_with_id == current_user.id)
                 .first())
    if not entry:
        return jsonify({'error': 'Analysis not found.'}), 404
    pdf = _share_pdf_bytes(entry, current_user.email)
    import io as _io
    return send_file(_io.BytesIO(pdf), mimetype='application/pdf',
                     as_attachment=True,
                     download_name='xplagiax-academic-integrity-report.pdf')


# ════════════════════════════════════════════════════════════════════════════
# Delete All Documents — borrado total, irreversible, de TODOS los documentos,
# análisis, historial y almacenamiento del usuario. Alcanza también marktrack
# (misma tabla `users` compartida — ver auditoría del feature). No hay 2PC real
# entre appcli2/marktrack/SeaweedFS/Qdrant/disco: cada sistema es transaccional
# en sí mismo, la operación completa es idempotente/reintentable, y se reporta
# honestamente qué se borró y qué no se pudo alcanzar (nunca se falsea éxito).
# ════════════════════════════════════════════════════════════════════════════
import threading as _threading
_purge_lock = _threading.Lock()
_purge_in_progress = set()  # user_ids con un borrado en curso EN ESTE proceso


def _purge_local_storage(user_id):
    """Borra los directorios locales del usuario en uploads_analysis/ y
    uploads_save/. Mismo patrón de contención de ruta que /delete_uploaded_document
    (nunca borra fuera de <base>/<user_id>)."""
    for base in (UPLOAD_FOLDER, SAVE_FOLDER):
        abs_base = os.path.abspath(base)
        user_root = os.path.abspath(os.path.join(abs_base, str(user_id)))
        if not os.path.isdir(user_root):
            continue
        if os.path.commonpath([abs_base, user_root]) != abs_base:
            logger.warning('purge_all: refusing to delete out-of-bounds path user=%s path=%s',
                            user_id, user_root)
            continue
        try:
            shutil.rmtree(user_root, ignore_errors=True)
        except Exception as exc:
            logger.warning('purge_all: local storage cleanup failed user=%s base=%s: %s',
                            user_id, base, exc)


def _purge_seaweedfs(user_id, minio_urls):
    """Borra objetos SeaweedFS: los explícitos (File.minio_url) + el namespace
    documents/<user_id>/ completo (cubre uploads vía /uploadsave_ que nunca
    crearon fila File — ver auditoría). Best-effort y en paralelo; un fallo
    individual no interrumpe el resto."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    deleted = 0
    try:
        client = get_storage_client()
    except Exception as exc:
        logger.warning('purge_all: SeaweedFS client unavailable user=%s: %s', user_id, exc)
        return deleted

    def _del_file(url):
        try:
            return bool(client.delete_file(url))
        except Exception as exc:
            logger.warning('purge_all: delete_file failed user=%s url=%s: %s', user_id, url, exc)
            return False

    def _del_doc(doc_id):
        try:
            client.delete_document_by_id(doc_id, user_id)
            return True
        except Exception as exc:
            logger.warning('purge_all: delete_document_by_id failed user=%s doc=%s: %s',
                            user_id, doc_id, exc)
            return False

    tasks = [(_del_file, u) for u in minio_urls if u]
    try:
        docs = client.list_user_documents(user_id)
    except Exception as exc:
        logger.warning('purge_all: list_user_documents failed user=%s: %s', user_id, exc)
        docs = []
    tasks += [(_del_doc, d.get('document_id')) for d in docs if d.get('document_id')]

    if not tasks:
        return deleted
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fn, arg) for fn, arg in tasks]
        for fut in as_completed(futures):
            if fut.result():
                deleted += 1
    return deleted


def _purge_qdrant_images(candidate_group_ids):
    """Best-effort: borra imágenes indexadas en Qdrant para cada posible
    group_id (File.id / DocumentAnalysis.analysis_id — no hay vínculo
    garantizado con user_id en los payloads de Qdrant, ver auditoría).
    NUNCA usa clear_collection (borraría de TODOS los usuarios)."""
    purged = 0
    if not candidate_group_ids:
        return purged
    try:
        from modules.image_service.ai_image_routes import require_qdrant, COLLECTION
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue, FilterSelector
    except Exception as exc:
        logger.warning('purge_all: Qdrant image module unavailable: %s', exc)
        return purged

    qdrant, error = require_qdrant()
    if error or qdrant is None:
        return purged

    for gid in candidate_group_ids:
        try:
            qdrant.delete(
                collection_name=COLLECTION,
                points_selector=FilterSelector(
                    filter=Filter(must=[FieldCondition(key='group_id', match=MatchValue(value=str(gid)))])
                ),
            )
            purged += 1
        except Exception as exc:
            logger.warning('purge_all: qdrant delete_by_group failed group_id=%s: %s', gid, exc)
    return purged


def _purge_marktrack_documents(user_id):
    """Llama al endpoint interno de marktrack para borrar los Document que ese
    usuario posee allí. Best-effort: si marktrack no responde, el borrado en
    appcli2 continúa igual — se reporta como no alcanzado (ver plan aprobado)."""
    headers = {'Content-Type': 'application/json', 'X-Internal-Key': MARKTRACK_INTERNAL_KEY}
    try:
        resp = session_pool.post(
            f'{MARKTRACK_SERVICE_BASE}/api/internal/documents/delete-all',
            headers=headers,
            json={'user_id': user_id},
            timeout=(5, 30),
        )
    except requests.exceptions.RequestException as exc:
        logger.warning('purge_all: marktrack unreachable user=%s: %s', user_id, exc)
        return {'reachable': False, 'deleted_count': 0, 'errors': [str(exc)]}

    if not resp.ok:
        logger.warning('purge_all: marktrack returned %s user=%s: %s',
                        resp.status_code, user_id, resp.text[:300])
        return {'reachable': False, 'deleted_count': 0, 'errors': [f'HTTP {resp.status_code}']}

    try:
        data = resp.json()
    except ValueError:
        return {'reachable': False, 'deleted_count': 0, 'errors': ['Invalid response from marktrack']}

    return {
        'reachable': True,
        'deleted_count': int(data.get('deleted_count') or 0),
        'errors': data.get('errors') or [],
    }


def purge_all_user_documents(user_id):
    """Borra TODOS los documentos/análisis/historial del usuario en appcli2:
    almacenamiento físico (disco local + SeaweedFS + Qdrant imágenes,
    best-effort) primero, luego las filas SQL (hijas antes que padres, todo en
    una transacción). Idempotente: reintentar sobre un usuario ya purgado no
    falla, simplemente no encuentra nada que borrar.
    """
    from modules.models.model import AnalysisHistory, Documents, ClassifiedParagraph

    # 1) Enumerar ANTES de borrar SQL — las filas son la única referencia a lo físico.
    file_rows = File.query.filter_by(user_id=user_id).all()
    minio_urls = [f.minio_url for f in file_rows if f.minio_url]
    file_ids = [f.id for f in file_rows]
    analysis_ids = [a.analysis_id for a in
                    DocumentAnalysis.query.filter_by(user_id=user_id).with_entities(DocumentAnalysis.analysis_id).all()]
    candidate_group_ids = [str(fid) for fid in file_ids] + [str(aid) for aid in analysis_ids]

    # 2) Borrado físico/externo — best-effort, nunca bloquea el borrado SQL.
    storage_files_deleted = _purge_seaweedfs(user_id, minio_urls)
    embeddings_deleted = _purge_qdrant_images(candidate_group_ids)
    _purge_local_storage(user_id)

    # 3) Borrado SQL — hijos antes que padres (bulk .delete() NO dispara cascade
    #    de relación ORM, solo el de FK a nivel de BD — hay que ser explícitos).
    try:
        if analysis_ids:
            ClassifiedParagraph.query.filter(
                ClassifiedParagraph.analysis_id.in_(analysis_ids)
            ).delete(synchronize_session=False)
        analysis_count = DocumentAnalysis.query.filter_by(user_id=user_id).delete(synchronize_session=False)

        if file_ids:
            FileTag.query.filter(FileTag.file_id.in_(file_ids)).delete(synchronize_session=False)

        CollaborativePermission.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        ItemShare.query.filter_by(owner_id=user_id).delete(synchronize_session=False)
        ItemHistory.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Tag.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        SmartRule.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        documents_count = File.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Folder.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        reports_count = AnalysisHistory.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Documents.query.filter_by(user_id=user_id).delete(synchronize_session=False)

        user = Users.query.get(user_id)
        if user is not None:
            user.used_storage_bytes = 0

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    cache_keys_cleared = 0
    try:
        from modules.bucket_service.bucket_routes import _session_cache as _bucket_cache
        cache_keys_cleared = len([k for k in _bucket_cache if str(user_id) in k])
    except Exception:
        pass
    try:
        clear_cache_for_user(user_id)
    except Exception as exc:
        logger.warning('purge_all: clear_cache_for_user failed user=%s: %s', user_id, exc)

    return {
        'documents': documents_count,
        'analysis': analysis_count,
        'reports': reports_count,
        'embeddings': embeddings_deleted,
        'storage_files': storage_files_deleted,
        'cache_keys': cache_keys_cleared,
    }


@x_doc.route('/documents/all', methods=['DELETE'])
@login_required
@limiter.limit('5 per hour')
def delete_all_documents():
    """Borra TODOS los documentos/análisis/historial/almacenamiento del usuario
    autenticado, en appcli2 Y en marktrack (misma identidad de usuario).
    Irreversible. Solo actúa sobre current_user.id — nunca acepta un id del cliente.
    """
    user_id = current_user.id

    with _purge_lock:
        if user_id in _purge_in_progress:
            return jsonify({'error': 'A deletion is already in progress for this account.'}), 409
        _purge_in_progress.add(user_id)

    try:
        try:
            appcli2_stats = purge_all_user_documents(user_id)
        except Exception:
            logger.exception('purge_all_user_documents failed for user=%s', user_id)
            return jsonify({'error': 'Could not delete your documents. Please try again.'}), 500

        marktrack_result = _purge_marktrack_documents(user_id)

        warnings = []
        if not marktrack_result['reachable']:
            warnings.append('marktrack: service unreachable — its documents were not deleted, retry later.')
        elif marktrack_result['errors']:
            warnings.append(f"marktrack: {len(marktrack_result['errors'])} document(s) had dependent "
                             f"records and were skipped — retry.")

        logger.info('delete_all_documents user=%s appcli2=%s marktrack=%s',
                    user_id, appcli2_stats, marktrack_result)

        return jsonify({
            'success': True,
            'deleted': {
                **appcli2_stats,
                'marktrack_documents': marktrack_result['deleted_count'],
            },
            'warnings': warnings,
            'marktrack_reachable': marktrack_result['reachable'],
        }), 200
    finally:
        with _purge_lock:
            _purge_in_progress.discard(user_id)