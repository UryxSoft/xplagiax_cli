#!/usr/bin/env python3
"""
Document Analysis Task - Production Ready (FINAL - Error Handling Fixed)
=========================================================================

CRITICAL FIXES:
1. ✅ Idioma detectado correctamente (detecta en bloques grandes)
2. ✅ PDFs escaneados retornan "NO SEARCHABLE"
3. ✅ Soporta formatos: .xps, .oxps, .epub, .fb2
4. ✅ DOS MODOS de párrafos: 'sentence' o 'block'
5. ✅ Manejo robusto de fast_langdetect (dict/str/list)
6. ✅ Validación de rutas mejorada (Jupyter/Colab compatible)
"""

import os
import fitz  # PyMuPDF
import logging
import time
import tempfile
import textwrap
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from threading import Semaphore
import requests
from urllib.parse import urlparse

# Lazy imports
def _lazy_import_docx():
    global Document
    from docx import Document

def _lazy_import_reportlab():
    global SimpleDocTemplate, Paragraph, getSampleStyleSheet, letter
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

def _lazy_import_langdetect():
    global detect
    from fast_langdetect import detect

def _lazy_import_pdf_converter():
    global PDFToHTMLConverter
    from .pdf_to_html_optimized import PDFToHTMLConverter

def _lazy_import_text_processor():
    global create_text_processor
    from optimized_text_processor import create_text_processor

def _lazy_import_classifier():
    global OptimizedTopicClassifier
    from .topic_classifier_optimized import TopicClassifier as OptimizedTopicClassifier

def _lazy_import_ocr():
    global ocr_pdf_to_searchable
    from .ocr_to_pdf import ocr_pdf_to_searchable


logger = logging.getLogger(__name__)

# Constants
MIN_WORDS = 10
MIN_CHARACTERS = 50

# Formatos soportados por PyMuPDF
SUPPORTED_FORMATS = {
    '.pdf', '.xps', '.oxps', '.epub', '.fb2',
    '.cbz', '.svg', '.txt'
}

DOCUMENT_FORMATS = {'.doc', '.docx'}


@dataclass
class TaskConfig:
    """Configuración para DocAnalysisTask."""
    max_workers: int = 4
    max_document_pages: int = 1000
    max_document_size_mb: int = 100
    page_timeout_sec: float = 30.0
    document_timeout_sec: float = 300.0
    max_concurrent_tasks: int = 10


class CircuitBreaker:
    """Circuit breaker simple para prevenir overload."""

    def __init__(self, max_concurrent: int):
        self._semaphore = Semaphore(max_concurrent)

    @contextmanager
    def protect(self):
        acquired = self._semaphore.acquire(timeout=5.0)
        if not acquired:
            raise TimeoutError("Too many concurrent operations")
        try:
            yield
        finally:
            self._semaphore.release()


class DocAnalysisTask:
    """
    Document Analysis Task - Production Ready Version
    ==================================================

    PARAMETER: paragraph_mode
    - 'sentence': Divide text by periods (original behavior)
    - 'block': Divide text only by line breaks (new mode)

    ALL FIXES APPLIED:
    1. ✅ Idioma detectado en bloques grandes (no fragmentos)
    2. ✅ PDFs escaneados retornan "NO SEARCHABLE"
    3. ✅ Soporta .xps, .oxps, .epub, .fb2
    4. ✅ Modo de párrafos configurable
    5. ✅ fast_langdetect robusto (dict/str/list)
    6. ✅ Validación de rutas mejorada
    """

    _circuit_breaker = CircuitBreaker(max_concurrent=10)

    __slots__ = ('userid', 'file_or_url', 'upload_folder',
                 'analysis_or_save', 'theme_return', 'paragraph_mode',
                 '_config', '_temp_files', '_resolved_pdf_path')

    def __init__(self, userid, file_or_url, upload_folder,
                 analysis_or_save, theme_return,
                 paragraph_mode: str = 'sentence',
                 config: Optional[TaskConfig] = None):
        """
        Inicializar tarea de análisis.

        Args:
            userid: ID del usuario
            file_or_url: Ruta del archivo o URL
            upload_folder: Carpeta de uploads
            analysis_or_save: Modo de análisis o guardado
            theme_return: Si debe retornar tema del documento
            paragraph_mode: 'sentence' o 'block' - modo de extracción de párrafos
            config: Configuración opcional
        """
        self.userid = userid
        self.file_or_url = file_or_url
        self.upload_folder = upload_folder
        self.analysis_or_save = analysis_or_save
        self.theme_return = theme_return

        # Validar modo de párrafos
        if paragraph_mode not in {'sentence', 'block'}:
            raise ValueError(f"paragraph_mode must be 'sentence' or 'block', got: {paragraph_mode}")
        self.paragraph_mode = paragraph_mode

        self._config = config or TaskConfig()
        self._temp_files: List[str] = []
        self._resolved_pdf_path: Optional[str] = None

    # =========================================================================
    # MÉTODOS HELPER - OPTIMIZADOS
    # =========================================================================

    def is_valid_paragraph_(self, paragraph: str) -> bool:
        """Check if paragraph meets minimum requirements."""
        if not paragraph or not isinstance(paragraph, str):
            return False
        word_count = len(paragraph.split())
        char_count = len(paragraph)
        return word_count >= MIN_WORDS and char_count >= MIN_CHARACTERS

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        Dividir texto según el modo configurado.

        MODOS:
        - 'sentence': Divide por puntos (fragmentos)
        - 'block': Divide por párrafos lógicos (inteligente)
        """
        if self.paragraph_mode == 'sentence':
            paragraphs = [p.strip() for p in text.split(".") if p.strip()]

        elif self.paragraph_mode == 'block':
            paragraphs = self._split_by_logical_blocks(text)

        return paragraphs

    def _split_by_logical_blocks(self, text: str) -> List[str]:
        """
        Dividir texto en bloques lógicos considerando:
        - Líneas vacías (bloques explícitos)
        - Punto/coma/etc + salto + mayúscula (bloques implícitos)
        """
        # Dividir por líneas vacías primero
        explicit_blocks = re.split(r'\n\s*\n+', text)

        final_blocks = []

        for block in explicit_blocks:
            block = block.strip()
            if not block:
                continue

            # Dividir por puntuación + salto + inicio de nuevo párrafo
            # [.|!|?|;|,] seguido de \n seguido de [mayúscula|número|bullet]
            pattern = r'([.!?;,])\s*\n+(?=[A-Z0-9•\-\*\d])'
            parts = re.split(pattern, block)

            # Reconstruir juntando texto + puntuación
            reconstructed = []
            current = ""

            for i, part in enumerate(parts):
                if part in '.!?;,':
                    current += part
                    if current.strip():
                        reconstructed.append(current.strip())
                    current = ""
                else:
                    current += part

            if current.strip():
                reconstructed.append(current.strip())

            final_blocks.extend(reconstructed)

        return final_blocks if final_blocks else [text.strip()]

    def _validate_file_path(self, file_path: str) -> None:
        """
        ✅ FIX 6: Validación robusta de rutas de archivo.
        Detecta argumentos inválidos de Jupyter/Colab.
        """
        # Detectar argumentos de IPython/Jupyter
        if file_path in {'-f', '--f', '-c', '--c', '--ip', '--port'}:
            raise ValueError(
                f"Invalid file path '{file_path}' - appears to be a Jupyter/IPython argument. "
                "Please provide a valid file path."
            )

        # Validar que sea una ruta válida
        if not file_path or file_path.strip() == '':
            raise ValueError("File path cannot be empty")

        # Si no es URL, verificar que el archivo existe
        if not file_path.startswith(('http://', 'https://')):
            if not os.path.exists(file_path):
                raise FileNotFoundError(
                    f"File not found: {file_path}\n"
                    f"Current directory: {os.getcwd()}\n"
                    f"Tip: Provide absolute path or check file exists"
                )

    @contextmanager
    def _open_document_safe(self, file_path: str):
        """Context manager para abrir documentos de forma segura."""

        # ✅ FIX 6: Validación mejorada
        self._validate_file_path(file_path)

        # Check size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > self._config.max_document_size_mb:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB")

        extension = os.path.splitext(file_path)[1].lower()

        # Validar formatos soportados
        if extension not in SUPPORTED_FORMATS and extension not in DOCUMENT_FORMATS:
            raise ValueError(
                f"Unsupported format: {extension}. "
                f"Supported: {', '.join(sorted(SUPPORTED_FORMATS | DOCUMENT_FORMATS))}"
            )

        # Handle Word documents (convertir a PDF)
        if extension in DOCUMENT_FORMATS:
            pdf_path = self.convert_docx_to_pdf(file_path)
            if pdf_path:
                file_path = pdf_path
                self._temp_files.append(pdf_path)
            else:
                raise ValueError(f"Failed to convert {extension} to PDF")

        # BUGFIX: exponer la ruta ya resuelta (post DOCX->PDF) para que la conversión
        # a HTML (result.html) use el PDF real y no el .doc/.docx original — antes,
        # extract_info()/extract_full_text() llamaban a convert_pdf_to_html() con la
        # variable local `file_path` de SU PROPIO scope (nunca reasignada), así que
        # para .doc/.docx siempre se le pasaba el archivo de Word original a un
        # conversor que solo sabe abrir PDF -> fallaba silenciosamente (result_view=None).
        self._resolved_pdf_path = file_path

        doc = None
        try:
            doc = fitz.open(file_path)

            page_count = len(doc)
            if page_count == 0:
                raise ValueError("Document has no pages")

            if page_count > self._config.max_document_pages:
                raise ValueError(f"Document too large: {page_count} pages")

            # Verificar si es searchable; si no, intentar OCR (solo PDFs)
            if not self._is_document_searchable(doc):
                if extension == '.pdf':
                    logger.info(f"Scanned PDF detected, attempting OCR: {os.path.basename(file_path)}")
                    doc.close()
                    doc = None
                    ocr_path = self._try_ocr(file_path)
                    if ocr_path:
                        doc = fitz.open(ocr_path)
                        if not self._is_document_searchable(doc):
                            raise ValueError("NO SEARCHABLE")
                        # El HTML view (result.html) debe generarse del PDF OCR'd (con capa
                        # de texto) y no del escaneado original: si no, el iframe no tiene
                        # texto que subrayar aunque el análisis sí lo tenga.
                        self._resolved_pdf_path = ocr_path
                        logger.info("OCR restored text searchability")
                    else:
                        raise ValueError("NO SEARCHABLE")
                else:
                    raise ValueError("NO SEARCHABLE")

            yield doc

        finally:
            if doc is not None:
                doc.close()
                logger.debug("Document closed safely")

    def _is_document_searchable(self, doc: fitz.Document) -> bool:
        """
        Verificar si el documento tiene texto extraíble.
        Verifica las primeras 3 páginas o todas si son menos.
        """
        pages_to_check = min(3, len(doc))

        for page_idx in range(pages_to_check):
            try:
                page = doc.load_page(page_idx)
                text = page.get_text("text").strip()

                # Si encuentra texto significativo, es searchable
                if text and len(text) > 20:
                    return True

            except Exception as e:
                logger.warning(f"Error checking page {page_idx}: {e}")
                continue

        logger.warning(f"Document appears to be scanned (no searchable text found)")
        return False

    @staticmethod
    def _find_soffice() -> Optional[str]:
        """Localiza el binario de LibreOffice: env SOFFICE_BIN, PATH o bundle macOS."""
        import shutil as _shutil
        cand = os.environ.get('SOFFICE_BIN')
        if cand and os.path.exists(cand):
            return cand
        for name in ('soffice', 'libreoffice'):
            p = _shutil.which(name)
            if p:
                return p
        mac = '/Applications/LibreOffice.app/Contents/MacOS/soffice'
        return mac if os.path.exists(mac) else None

    def _convert_docx_via_libreoffice(self, file_path: str) -> Optional[str]:
        """DOC/DOCX→PDF con LibreOffice headless: fidelidad ~completa (imágenes,
        tablas, estilos, encabezados/pies, columnas) y soporta el .doc binario
        antiguo. Devuelve la ruta del PDF generado o None si no hay LibreOffice
        o la conversión falla (el caller cae al fallback de texto plano)."""
        soffice = self._find_soffice()
        if not soffice:
            return None
        import subprocess
        import shutil as _shutil
        outdir = os.path.dirname(file_path) or '.'
        # Perfil de usuario ÚNICO por invocación: LibreOffice bloquea su perfil por
        # proceso; sin esto, conversiones concurrentes (varios workers de gunicorn)
        # fallan con "another instance of LibreOffice is running".
        profile = tempfile.mkdtemp(prefix='lo_profile_')
        try:
            subprocess.run(
                [soffice, '--headless', '--norestore', '--invisible',
                 f'-env:UserInstallation=file://{profile}',
                 '--convert-to', 'pdf', '--outdir', outdir, file_path],
                check=True, timeout=180,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.warning(f"LibreOffice conversion failed: {e}")
            return None
        finally:
            _shutil.rmtree(profile, ignore_errors=True)
        pdf_path = os.path.splitext(file_path)[0] + '.pdf'
        if not os.path.exists(pdf_path):
            logger.warning("LibreOffice reported success but no PDF was produced")
            return None
        try:
            with fitz.open(pdf_path) as test_doc:
                if len(test_doc) == 0:
                    return None
        except Exception:
            return None
        logger.info(f"DOCX converted to PDF via LibreOffice: {pdf_path}")
        return pdf_path

    def convert_docx_to_pdf(self, file_path: str) -> Optional[str]:
        """Convert DOC/DOCX files to PDF.

        1º LibreOffice headless — conversión FIEL (imágenes, tablas, estilos,
           encabezados, columnas; también .doc binario antiguo).
        2º Fallback texto-plano (python-docx + reportlab): solo párrafos — se
           conserva para entornos sin LibreOffice (p.ej. dev local); .doc NO
           es soportado por python-docx, solo .docx.
        """
        try:
            if not file_path.lower().endswith(('.docx', '.doc')):
                return None

            pdf_path = self._convert_docx_via_libreoffice(file_path)
            if pdf_path:
                return pdf_path
            logger.warning("LibreOffice unavailable/failed — falling back to text-only DOCX conversion")

            _lazy_import_docx()
            _lazy_import_reportlab()

            doc = Document(file_path)
            pdf_path = os.path.splitext(file_path)[0] + '.pdf'

            pdf = SimpleDocTemplate(pdf_path, pagesize=letter)
            styles = getSampleStyleSheet()
            content = []

            for paragraph in doc.paragraphs:
                ptext = paragraph.text.strip()
                if ptext:
                    try:
                        content.append(Paragraph(ptext, styles["Normal"]))
                    except Exception:
                        continue

            if not content:
                return None

            pdf.build(content)

            # Verify PDF
            with fitz.open(pdf_path) as test_doc:
                if len(test_doc) == 0:
                    return None

            logger.info(f"DOCX converted to PDF (text-only fallback): {pdf_path}")
            return pdf_path

        except Exception as e:
            logger.error(f"DOCX conversion failed: {e}")
            return None

    def is_searchable_doc(self, doc_path: str) -> bool:
        """DEPRECATED: Usar _is_document_searchable() internamente."""
        logger.warning("is_searchable_doc() is deprecated")
        try:
            with fitz.open(doc_path) as doc:
                return self._is_document_searchable(doc)
        except Exception:
            return False

    def open_document(self, file_path: str) -> Optional[fitz.Document]:
        """DEPRECATED: Usar _open_document_safe() en su lugar."""
        logger.warning("open_document() is deprecated, use context manager instead")
        try:
            return fitz.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open document: {e}")
            return None

    def download_file(self, url: str) -> Optional[str]:
        """Download file from URL with better error handling."""
        try:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or "downloaded_file"

            temp_dir = tempfile.gettempdir()
            local_filename = os.path.join(temp_dir, filename)

            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self._temp_files.append(local_filename)
            return local_filename

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None

    def get_file_type(self, file_or_url: str) -> str:
        """Determine if input is URL or file."""
        return 'url' if file_or_url.startswith(('http://', 'https://')) else 'file'

    def get_extension(self, file_or_url: str) -> str:
        """Get file extension."""
        return os.path.splitext(file_or_url)[1].lower()

    def document_type(self, file_or_url: str) -> Optional[fitz.Document]:
        """DEPRECATED: Usar _open_document_safe() en su lugar."""
        logger.warning("document_type() is deprecated")

        file_type = self.get_file_type(file_or_url)

        if file_type == 'url':
            local_file = self.download_file(file_or_url)
            if not local_file:
                return None
            file_or_url = local_file

        return self.open_document(file_or_url)

    def _detect_language_robust(self, text: str) -> Optional[str]:
        """
        ✅ FIX 1 + FIX 5: Detección robusta de idioma.
        Soporta dict, str, y list de fast_langdetect.
        Retorna código ISO 639-1 o None.
        """
        if not text or len(text.strip()) < 20:
            return None

        try:
            _lazy_import_langdetect()
            # ✅ FIX: fast-langdetect processes one line at a time
            clean_text = text.replace('\n', ' ').strip()
            if not clean_text:
                return None
            result = detect(clean_text)

            # ✅ FIX 5: Manejo de múltiples formatos
            # fast_langdetect puede retornar:
            # - dict: {'lang': 'en', 'score': 0.999}
            # - str: 'en'
            # - list: [{'lang': 'en', 'score': 0.999}]

            if isinstance(result, dict):
                # Formato: {'lang': 'en', 'score': 0.999}
                lang = result.get('lang')
                score = result.get('score', 0)

                if lang and score > 0.5:
                    logger.debug(f"Detected (dict): {lang} (score: {score:.3f})")
                    return lang
                else:
                    logger.debug(f"Low confidence (dict): {lang} (score: {score:.3f})")
                    return None

            elif isinstance(result, str):
                # Formato: 'en'
                logger.debug(f"Detected (str): {result}")
                return result

            elif isinstance(result, list) and len(result) > 0:
                # Formato: [{'lang': 'en', 'score': 0.999}, ...]
                # Tomar el primero (mayor confianza)
                first = result[0]
                if isinstance(first, dict):
                    lang = first.get('lang')
                    score = first.get('score', 0)

                    if lang and score > 0.5:
                        logger.debug(f"Detected (list): {lang} (score: {score:.3f})")
                        return lang
                    else:
                        logger.debug(f"Low confidence (list): {lang} (score: {score:.3f})")
                        return None
                elif isinstance(first, str):
                    logger.debug(f"Detected (list-str): {first}")
                    return first

            logger.warning(f"Unexpected detect() format: {type(result)} - {result}")
            return None

        except Exception as e:
            logger.debug(f"Language detection failed: {e}")
            return None

    def _aggregate_languages(self, lang_detections: List[str]) -> str:
        """
        Agregación correcta de idiomas detectados.
        Retorna el idioma más frecuente.
        """
        if not lang_detections:
            logger.warning("No language detections available")
            return 'unknown'

        # Contar frecuencias
        lang_counts = {}
        for lang in lang_detections:
            if lang:  # Ignorar None
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

        if not lang_counts:
            logger.warning("All language detections were None")
            return 'unknown'

        # Retornar el más frecuente
        dominant = max(lang_counts, key=lang_counts.get)
        total = sum(lang_counts.values())
        percentage = (lang_counts[dominant] / total) * 100

        logger.info(f"Language distribution: {lang_counts}")
        logger.info(f"Dominant language: {dominant} ({percentage:.1f}% of detections)")

        return dominant

    def _process_single_page(self, page: fitz.Page, page_index: int) -> Dict[str, Any]:
        """Process a single page (threaded)."""
        result = {
            'page_index': page_index,
            'paragraphs': [],
            'images': [],
            'annotations': [],
            'urls': []
        }

        try:
            # Extract text
            text = page.get_text("text").strip()
            if text:
                result['paragraphs'] = [text]

            # Extract images
            images = page.get_images()
            result['images'] = [
                {"xref": img[0], "page": page_index}
                for img in images[:10]
            ]

            # Extract annotations
            annots = page.annots()
            if annots:
                result['annotations'] = [
                    annot.info.get("content", "")
                    for annot in annots
                    if annot.info
                ]

            # Extract URLs
            links = page.get_links()
            for link in links:
                if "uri" in link:
                    result['urls'].append(link["uri"])

        except Exception as e:
            logger.warning(f"Error processing page {page_index}: {e}")
            result['error'] = str(e)

        return result

    def _extract_and_save_images(self, doc: fitz.Document, image_refs: List[Dict], output_folder: str) -> List[str]:
        """
        Extract actual image bytes from PDF and save to disk.
        
        Args:
            doc: The fitz Document object (must be open)
            image_refs: List of {"xref": int, "page": int} from _process_single_page
            output_folder: Path to the 'images' folder where images should be saved
            
        Returns:
            List of saved image file paths
        """
        saved_images = []
        
        if not output_folder or not os.path.exists(output_folder):
            logger.warning(f"Image output folder does not exist: {output_folder}")
            return saved_images
        
        if not image_refs:
            logger.info("No images to extract from document")
            return saved_images
        
        logger.info(f"🖼️  Extracting {len(image_refs)} images to {output_folder}")
        
        for idx, img_ref in enumerate(image_refs):
            try:
                xref = img_ref.get('xref')
                page_num = img_ref.get('page', 0)
                
                if not xref:
                    continue
                
                # Extract image bytes from PDF using xref
                base_image = doc.extract_image(xref)
                
                if not base_image:
                    logger.warning(f"Could not extract image xref={xref}")
                    continue
                
                image_bytes = base_image.get("image")
                image_ext = base_image.get("ext", "png")
                
                if not image_bytes:
                    continue
                
                # Generate unique filename
                filename = f"page_{page_num + 1}_img_{idx + 1}.{image_ext}"
                filepath = os.path.join(output_folder, filename)
                
                # Save image to disk
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                
                saved_images.append(filepath)
                logger.debug(f"  ✅ Saved: {filename} ({len(image_bytes)} bytes)")
                
            except Exception as e:
                logger.warning(f"Error extracting image {idx}: {e}")
                continue
        
        logger.info(f"✅ Extracted {len(saved_images)}/{len(image_refs)} images successfully")
        return saved_images

    def process_pages_threaded(self, doc: fitz.Document, num_pages: int) -> List[Dict]:
        """Process pages using threading."""
        results = [None] * num_pages

        with ThreadPoolExecutor(max_workers=self._config.max_workers) as executor:
            future_to_page = {}

            for page_idx in range(num_pages):
                page = doc.load_page(page_idx)
                future = executor.submit(self._process_single_page, page, page_idx)
                future_to_page[future] = page_idx

            for future in as_completed(
                future_to_page,
                timeout=self._config.document_timeout_sec
            ):
                page_idx = future_to_page[future]

                try:
                    result = future.result(timeout=self._config.page_timeout_sec)
                    results[page_idx] = result
                except FuturesTimeoutError:
                    logger.warning(f"Page {page_idx} timeout")
                    results[page_idx] = {
                        'page_index': page_idx,
                        'paragraphs': [],
                        'error': 'timeout'
                    }
                except Exception as e:
                    logger.error(f"Page {page_idx} failed: {e}")
                    results[page_idx] = {
                        'page_index': page_idx,
                        'paragraphs': [],
                        'error': str(e)
                    }

        # Ensure all results
        for i in range(num_pages):
            if results[i] is None:
                results[i] = {
                    'page_index': i,
                    'paragraphs': [],
                    'error': 'no result'
                }

        return results

    def process_single_page(self, page_index: int, doc: fitz.Document) -> Dict[str, Any]:
        """Process a single page sequentially."""
        page = doc.load_page(page_index)
        return self._process_single_page(page, page_index)

    def _try_ocr(self, file_path: str) -> Optional[str]:
        """
        Attempt OCR on a scanned PDF using ocr_to_pdf.ocr_pdf_to_searchable().
        The output temp file is registered in self._temp_files for automatic cleanup.
        Returns the path to the OCR'd PDF, or None on failure.
        """
        try:
            _lazy_import_ocr()
            fd, ocr_path = tempfile.mkstemp(suffix='_ocr.pdf')
            os.close(fd)
            self._temp_files.append(ocr_path)
            result = ocr_pdf_to_searchable(file_path, output_path=ocr_path)
            return result
        except Exception as e:
            logger.warning(f"OCR attempt failed: {e}")
            return None

    def _cleanup_temp_files(self):
        """Cleanup automático de archivos temporales."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.debug(f"Cleaned temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean {temp_file}: {e}")
        self._temp_files.clear()

    # =========================================================================
    # MÉTODOS PRINCIPALES - MANTIENEN FIRMA ORIGINAL
    # =========================================================================

    def extract_info(self) -> List[Dict[str, Any]]:
        """
        Extract document information using threading.

        ✅ ALL FIXES APPLIED
        """
        try:
            with self._circuit_breaker.protect():
                return self._extract_info_internal()

        except ValueError as e:
            error_msg = str(e)
            if "NO SEARCHABLE" in error_msg:
                return [{
                    "error": "NO SEARCHABLE",
                    "message": "Document is scanned/image-based with no extractable text",
                    "suggestion": "Please use OCR to convert this document to searchable format"
                }]
            else:
                return [{"error": f"Validation error: {error_msg}"}]

        except FileNotFoundError as e:
            return [{"error": f"File not found: {str(e)}"}]

        except Exception as e:
            logger.error(f"extract_info failed: {e}", exc_info=True)
            return [{"error": f"Processing error: {str(e)}"}]

        finally:
            self._cleanup_temp_files()

    def _extract_info_internal(self) -> List[Dict[str, Any]]:
        """Implementación interna de extract_info."""

        # Handle URL
        file_path = self.file_or_url
        if self.get_file_type(self.file_or_url) == 'url':
            downloaded = self.download_file(self.file_or_url)
            if not downloaded:
                return [{"error": "Failed to download file"}]
            file_path = downloaded

        # Open document safely
        with self._open_document_safe(file_path) as doc:
            metadata = doc.metadata or {}
            num_pages = len(doc)

            # Process pages concurrently
            page_results = self.process_pages_threaded(doc, num_pages)

            # Aggregate results
            all_paragraphs = []
            all_annotations = []
            all_images = []
            all_urls = []
            lang_detections = []

            for result in sorted(page_results, key=lambda x: x['page_index']):
                page_index = result['page_index']

                if not result.get('paragraphs'):
                    continue

                # ✅ FIX 1: Detectar idioma del texto COMPLETO primero
                full_page_text = " ".join(result['paragraphs'])

                detected_lang = self._detect_language_robust(full_page_text)
                if detected_lang:
                    lang_detections.append(detected_lang)
                    logger.debug(f"Page {page_index + 1} language: {detected_lang}")

                # Luego dividir en párrafos
                cleaned_text = textwrap.dedent(full_page_text)
                paragraphs = self._split_paragraphs(cleaned_text)

                # Procesar párrafos
                parraf_count = 0
                for paragraph in paragraphs:
                    parraf_count += 1
                    cleaned_para = paragraph.replace('\n', ' ')
                    all_paragraphs.append((page_index + 1, parraf_count, cleaned_para))

                # Aggregate other data
                if result.get('images'):
                    all_images.extend(result['images'])

                if result.get('annotations'):
                    all_annotations.append((page_index + 1, 1, result['annotations']))

                if result.get('urls'):
                    all_urls.extend(result['urls'])

            # Agregación del idioma dominante
            dominant_lang = self._aggregate_languages(lang_detections)

            # ✅ NEW: Extract and save images to disk
            saved_image_paths = []
            if all_images and self.upload_folder:
                try:
                    saved_image_paths = self._extract_and_save_images(doc, all_images, self.upload_folder)
                    logger.info(f"📸 Total images saved: {len(saved_image_paths)}")
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")

            # Generate HTML preview if requested
            new_path = self.upload_folder.replace("images", "result.html")
            try:
                _lazy_import_pdf_converter()
                converter = PDFToHTMLConverter(embed_fonts=True, preserve_layout=True)
                converter.convert_pdf_to_html(self._resolved_pdf_path, new_path)
            except Exception as e:
                logger.warning(f"HTML conversion failed: {e}")
                new_path = None

            # FORMATO ORIGINAL MANTENIDO
            page_data = {
                "paragraphs": all_paragraphs,
                "metadata": metadata,
                "idiom": dominant_lang,
                "annotations": all_annotations,
                "images": all_images,
                "urls": all_urls,
                "pages": num_pages,
                "theme": 'None',
                "result_view": new_path,
                "paragraph_mode": self.paragraph_mode
            }

            return [page_data]

    # =========================================================================
    # EXTRACCIÓN PARA ANÁLISIS DE TEXTO — TEXTO COMPLETO + METADATOS
    # =========================================================================
    # Pensado para el flujo de análisis de documentos que envía el texto a los
    # servicios de texto (AI detection / FinderX). A diferencia de extract_info(),
    # devuelve el TEXTO COMPLETO (sin trocear en párrafos), pero SÍ extrae de forma
    # normal: imágenes, annotations, urls, idioma y metadata. Conserva además la
    # apertura segura (DOCX→PDF), validación, OCR de PDFs escaneados, el guardado
    # de imágenes y la generación del result.html. Usa el procesamiento de páginas
    # en paralelo (process_pages_threaded).

    def extract_full_text(self) -> Dict[str, Any]:
        """Extrae el texto completo del documento + metadata, idioma, imágenes,
        annotations, urls y preview HTML.

        Returns:
            {'text', 'metadata', 'idiom', 'images', 'annotations', 'urls',
             'result_view'} en éxito, o {'error': str, ...} en fallo.
        """
        try:
            with self._circuit_breaker.protect():
                return self._extract_full_text_internal()

        except ValueError as e:
            error_msg = str(e)
            if "NO SEARCHABLE" in error_msg:
                return {
                    "error": "NO SEARCHABLE",
                    "message": "Document is scanned/image-based with no extractable text",
                    "suggestion": "Please use OCR to convert this document to searchable format"
                }
            return {"error": f"Validation error: {error_msg}"}

        except FileNotFoundError as e:
            return {"error": f"File not found: {str(e)}"}

        except Exception as e:
            logger.error(f"extract_full_text failed: {e}", exc_info=True)
            return {"error": f"Processing error: {str(e)}"}

        finally:
            self._cleanup_temp_files()

    def _extract_full_text_internal(self) -> Dict[str, Any]:
        """Implementación interna de extract_full_text."""

        # Handle URL
        file_path = self.file_or_url
        if self.get_file_type(self.file_or_url) == 'url':
            downloaded = self.download_file(self.file_or_url)
            if not downloaded:
                return {"error": "Failed to download file"}
            file_path = downloaded

        # Abrir documento de forma segura (DOCX→PDF, validación, OCR si aplica)
        with self._open_document_safe(file_path) as doc:
            metadata = doc.metadata or {}
            num_pages = len(doc)

            # Procesar páginas EN PARALELO: texto, imágenes, annotations, urls.
            page_results = self.process_pages_threaded(doc, num_pages)

            all_text = []
            all_annotations = []
            all_images = []
            all_urls = []
            lang_detections = []

            for result in sorted(page_results, key=lambda x: x['page_index']):
                page_index = result['page_index']

                if not result.get('paragraphs'):
                    continue

                # Texto completo de la página (sin trocear en párrafos)
                full_page_text = " ".join(result['paragraphs'])
                all_text.append(full_page_text)

                # Idioma a partir del texto completo de la página
                detected_lang = self._detect_language_robust(full_page_text)
                if detected_lang:
                    lang_detections.append(detected_lang)

                if result.get('images'):
                    all_images.extend(result['images'])

                if result.get('annotations'):
                    all_annotations.append((page_index + 1, 1, result['annotations']))

                if result.get('urls'):
                    all_urls.extend(result['urls'])

            # Idioma dominante
            dominant_lang = self._aggregate_languages(lang_detections)

            # Guardar imágenes a disco (se conserva)
            saved_image_paths = []
            if all_images and self.upload_folder:
                try:
                    saved_image_paths = self._extract_and_save_images(doc, all_images, self.upload_folder)
                    logger.info(f"📸 Total images saved: {len(saved_image_paths)}")
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")

            # Preview HTML (se conserva la conversión PDF→HTML)
            new_path = self.upload_folder.replace("images", "result.html") if self.upload_folder else None
            if new_path:
                try:
                    _lazy_import_pdf_converter()
                    converter = PDFToHTMLConverter(embed_fonts=True, preserve_layout=True)
                    converter.convert_pdf_to_html(self._resolved_pdf_path, new_path)
                except Exception as e:
                    logger.warning(f"HTML conversion failed: {e}")
                    new_path = None

        full_text = "\n".join(t for t in all_text if t).strip()

        return {
            "text": full_text,
            "metadata": metadata,
            "idiom": dominant_lang,
            "images": saved_image_paths,
            "annotations": all_annotations,
            "urls": all_urls,
            "result_view": new_path,
        }

    def extract_content_info(self) -> Tuple[str, str, str, str, str, str, str]:
        """
        Extract content information using sequential processing.

        ✅ ALL FIXES APPLIED
        """
        try:
            with self._circuit_breaker.protect():
                return self._extract_content_info_internal()

        except ValueError as e:
            error_msg = str(e)
            if "NO SEARCHABLE" in error_msg:
                return (
                    "NO SEARCHABLE",
                    "N/A",
                    "This document is scanned/image-based with no extractable text. Please use OCR.",
                    "Unknown",
                    "unknown",
                    self.upload_folder,
                    "None"
                )
            else:
                return (
                    "Error", "Error", f"Validation error: {error_msg}",
                    "Unknown", "unknown", self.upload_folder, "None"
                )

        except FileNotFoundError as e:
            return (
                "Error", "Error", f"File not found: {str(e)}",
                "Unknown", "unknown", self.upload_folder, "None"
            )

        except Exception as e:
            logger.error(f"extract_content_info failed: {e}", exc_info=True)
            return (
                "Error", "Error", f"General error: {str(e)}",
                "Unknown", "unknown", self.upload_folder, "None"
            )

        finally:
            self._cleanup_temp_files()

    def _extract_content_info_internal(self) -> Tuple[str, str, str, str, str, str, str]:
        """Implementación interna de extract_content_info."""

        # Handle URL
        file_path = self.file_or_url
        if self.get_file_type(self.file_or_url) == 'url':
            downloaded = self.download_file(self.file_or_url)
            if not downloaded:
                return (
                    "Error", "Error", "Failed to download",
                    "Unknown", "unknown", self.upload_folder, "None"
                )
            file_path = downloaded

        # Open document safely
        with self._open_document_safe(file_path) as doc:
            metadata = doc.metadata or {}
            num_pages = len(doc)

            # Process pages sequentially
            all_text = []
            all_images = []  # ✅ NEW: Collect image references
            lang_detections = []

            for page_index in range(num_pages):
                result = self.process_single_page(page_index, doc)

                if not result.get('paragraphs'):
                    continue

                # ✅ FIX 1: Detectar idioma del texto COMPLETO
                full_page_text = " ".join(result['paragraphs'])

                detected_lang = self._detect_language_robust(full_page_text)
                if detected_lang:
                    lang_detections.append(detected_lang)
                    logger.debug(f"Page {page_index + 1} language: {detected_lang}")

                # Luego dividir en párrafos
                cleaned_text = textwrap.dedent(full_page_text)
                paragraphs = self._split_paragraphs(cleaned_text)

                for paragraph in paragraphs:
                    cleaned_para = paragraph.replace('\n', ' ')
                    all_text.append(cleaned_para)

                # ✅ NEW: Collect image references from this page
                if result.get('images'):
                    all_images.extend(result['images'])

            # ✅ NEW: Extract and save images to disk
            saved_image_paths = []
            if all_images and self.upload_folder:
                try:
                    saved_image_paths = self._extract_and_save_images(doc, all_images, self.upload_folder)
                    logger.info(f"📸 Total images saved: {len(saved_image_paths)}")
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")

            # Agregación del idioma dominante
            dominant_lang = self._aggregate_languages(lang_detections)

            # Get theme if requested
            theme = "None"
            if self.theme_return and all_text:
                try:
                    _lazy_import_classifier()
                    classifier = OptimizedTopicClassifier()
                    theme_result = classifier.predict(" ".join(all_text))
                    theme = theme_result.topic if hasattr(theme_result, 'topic') else str(theme_result)
                except Exception as e:
                    logger.warning(f"Theme detection failed: {e}")

            # FORMATO ORIGINAL MANTENIDO
            return (
                metadata.get('title') or os.path.basename(file_path),
                metadata.get('author', 'Unknown'),
                " ".join(all_text),
                metadata.get('date', 'Unknown'),
                dominant_lang,
                self.upload_folder,
                theme
            )


# Mantener compatibilidad con imports existentes
__all__ = ['DocAnalysisTask', 'MIN_WORDS', 'MIN_CHARACTERS']


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # ✅ FIX 6: Validación mejorada de argumentos
    # Filtrar argumentos de IPython/Jupyter
    valid_args = [
        arg for arg in sys.argv[1:]
        if not arg.startswith('-') or arg.endswith('.pdf')  # Permitir archivos que empiecen con -
    ]

    if len(valid_args) < 1:
        print("="*70)
        print("❌ ERROR: No document path provided")
        print("="*70)
        print("\nUsage:")
        print("  python doc_analysis_optimized.py <document_path>")
        print("\nExamples:")
        print("  python doc_analysis_optimized.py /path/to/document.pdf")
        print("  python doc_analysis_optimized.py document.epub")
        print("  python doc_analysis_optimized.py https://example.com/file.pdf")
        print("\nSupported formats:")
        print(f"  {', '.join(sorted(SUPPORTED_FORMATS | DOCUMENT_FORMATS))}")
        print("\nNote: If running in Jupyter/Colab, provide the full path:")
        print("  task = DocAnalysisTask(..., file_or_url='/content/document.pdf', ...)")
        print("="*70)
        sys.exit(1)

    doc_path = valid_args[0]

    # Validar que el archivo existe si no es URL
    if not doc_path.startswith(('http://', 'https://')):
        if not os.path.exists(doc_path):
            print("="*70)
            print(f"❌ ERROR: File not found: {doc_path}")
            print("="*70)
            print(f"\nCurrent directory: {os.getcwd()}")
            print("\nFiles in current directory:")
            for f in os.listdir('.')[:10]:
                print(f"  - {f}")
            print("\nTip: Use absolute path or cd to the correct directory")
            print("="*70)
            sys.exit(1)

    print("\n" + "="*70)
    print("TEST 1: MODO 'sentence' (divide por puntos - original)")
    print("="*70)

    task1 = DocAnalysisTask(
        userid=1,
        file_or_url=doc_path,
        upload_folder='/uploads',
        analysis_or_save=True,
        theme_return=True,
        paragraph_mode='sentence'
    )

    result_info1 = task1.extract_info()

    if result_info1 and 'error' not in result_info1[0]:
        data = result_info1[0]
        print(f"✅ Paragraphs: {len(data.get('paragraphs', []))}")
        print(f"✅ Pages: {data.get('pages')}")
        print(f"✅ Language: {data.get('idiom')}")
        print(f"✅ Images: {len(data.get('images', []))}")
        print(f"✅ Mode: {data.get('paragraph_mode')}")

        # Mostrar primeros 3 párrafos
        print("\n📄 Primeros 3 párrafos:")
        for i, (page, num, text) in enumerate(data['paragraphs'][:3], 1):
            preview = text[:100] + "..." if len(text) > 100 else text
            print(f"   {i}. Página {page}, #{num}: {preview}")

    elif 'error' in result_info1[0]:
        error_type = result_info1[0].get('error')
        if error_type == "NO SEARCHABLE":
            print(f"⚠️  {error_type}: {result_info1[0].get('message')}")
            print(f"💡 {result_info1[0].get('suggestion')}")
        else:
            print(f"❌ Error: {result_info1[0]}")

    result_content1 = task1.extract_content_info()

    if result_content1[0] != "NO SEARCHABLE" and result_content1[0] != "Error":
        print(f"\n✅ Title: {result_content1[0]}")
        print(f"✅ Author: {result_content1[1]}")
        print(f"✅ Text length: {len(result_content1[2])}")
        print(f"✅ Language: {result_content1[4]}")
        print(f"✅ Theme: {result_content1[6]}")
    else:
        print(f"\n⚠️  {result_content1[0]}: {result_content1[2]}")

    print("\n" + "="*70)
    print("TEST 2: MODO 'block' (divide por saltos de línea - nuevo)")
    print("="*70)

    task2 = DocAnalysisTask(
        userid=1,
        file_or_url="/content/Climate Change and the Role of Technology.pdf",
        upload_folder='/uploads',
        analysis_or_save=True,
        theme_return=True,
        paragraph_mode='block' #sentence
    )

    result_info2 = task2.extract_info()

    if result_info2 and 'error' not in result_info2[0]:
        data = result_info2[0]
        print(f"✅ Paragraphs: {len(data.get('paragraphs', []))}")
        print(f"✅ Pages: {data.get('pages')}")
        print(f"✅ Language: {data.get('idiom')}")
        print(f"✅ Images: {len(data.get('images', []))}")
        print(f"✅ Mode: {data.get('paragraph_mode')}")

        # Mostrar primeros 3 párrafos
        print("\n📄 Primeros 3 párrafos:")
        for i, (page, num, text) in enumerate(data['paragraphs'][:3], 1):
            preview = text[:100] + "..." if len(text) > 100 else text
            print(f"   {i}. Página {page}, #{num}: {preview}")

    elif 'error' in result_info2[0]:
        print(f"❌ Error: {result_info2[0]}")

    result_content2 = task2.extract_content_info()

    if result_content2[0] != "NO SEARCHABLE" and result_content2[0] != "Error":
        print(f"\n✅ Title: {result_content2[0]}")
        print(f"✅ Author: {result_content2[1]}")
        print(f"✅ Text length: {len(result_content2[2])}")
        print(f"✅ Language: {result_content2[4]}")
        print(f"✅ Theme: {result_content2[6]}")

    print("\n" + "="*70)
    print("COMPARACIÓN DE MODOS")
    print("="*70)
    if result_info1 and 'error' not in result_info1[0] and result_info2 and 'error' not in result_info2[0]:
        print(f"Modo 'sentence': {len(result_info1[0].get('paragraphs', []))} párrafos")
        print(f"Modo 'block':    {len(result_info2[0].get('paragraphs', []))} párrafos")
        print("\n💡 'block' preserva oraciones completas en cada bloque")
    print("="*70)

    print(result_content2)

    print(result_info2)