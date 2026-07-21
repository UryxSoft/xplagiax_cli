"""
Pipeline de logotipos institucionales: auto-fetch best-effort desde el
dominio/sitio web, validación, optimización y almacenamiento anti-duplicados.
Si el auto-fetch falla (dominio sin logo público, timeout, formato raro), la
institución queda sin logo y el admin puede subir uno manualmente desde el
panel — nunca bloquea la creación/edición.
"""
import hashlib
import io
import logging
import os
import re

import requests
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'static', 'institution_logos')
MAX_DIM = 512
FETCH_TIMEOUT = 5
MAX_UPLOAD_BYTES = 3 * 1024 * 1024  # 3MB


def _ensure_dir():
    os.makedirs(LOGO_DIR, exist_ok=True)


def domain_from(website=None, domain=None):
    """Normaliza a un hostname puro (sin esquema/ruta) para las fuentes de logo."""
    if domain and domain.strip():
        d = domain.strip().lower()
    elif website and website.strip():
        d = re.sub(r'^https?://', '', website.strip(), flags=re.I).split('/')[0]
    else:
        return None
    return d.lstrip('.').split(':')[0] or None


def _save_bytes(data, ext):
    """Nombre = sha256 del contenido → dos instituciones con el mismo logo
    comparten archivo en disco (anti-duplicados) sin necesidad de índice aparte."""
    _ensure_dir()
    digest = hashlib.sha256(data).hexdigest()[:32]
    fname = f'{digest}.{ext}'
    path = os.path.join(LOGO_DIR, fname)
    if not os.path.exists(path):
        with open(path, 'wb') as f:
            f.write(data)
    return f'institution_logos/{fname}'


def _optimize_raster(data):
    """Valida que sea una imagen real (no solo la extensión) y la reduce a
    MAX_DIM preservando aspecto. Devuelve (bytes, ext) o None si es inválida."""
    try:
        probe = Image.open(io.BytesIO(data))
        probe.verify()  # detecta corrupción; deja el objeto inutilizable después
        img = Image.open(io.BytesIO(data))  # reabrir para poder procesarla
        img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        return None
    ext = 'jpg' if str(img.format).upper() == 'JPEG' else 'png'
    if ext == 'png' and img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGBA')
    elif ext == 'jpg' and img.mode != 'RGB':
        img = img.convert('RGB')
    img.thumbnail((MAX_DIM, MAX_DIM))
    buf = io.BytesIO()
    img.save(buf, format='PNG' if ext == 'png' else 'JPEG', optimize=True)
    return buf.getvalue(), ext


def _is_safe_svg(data):
    """SVG puede llevar <script>/on* handlers — rechazar cualquier logo con
    contenido ejecutable en vez de sanitizarlo (mejor un logo vacío que XSS
    almacenado servido desde /static)."""
    try:
        text = data.decode('utf-8', errors='ignore')
    except Exception:
        return False
    if '<svg' not in text.lower():
        return False
    lowered = text.lower()
    return not any(bad in lowered for bad in ('<script', 'javascript:', 'onload=', 'onerror='))


def validate_and_store(data, filename_hint=''):
    """Punto de entrada único (auto-fetch y upload manual comparten esta
    validación). Devuelve logo_path relativo a /static, o None si no es una
    imagen válida/segura — nunca lanza excepción."""
    if not data or len(data) < 16:
        return None
    hint = (filename_hint or '').lower()
    looks_svg = hint.endswith('.svg') or data.lstrip()[:5].lower() in (b'<?xml', b'<svg\n') \
        or data.lstrip()[:4].lower() == b'<svg'
    if looks_svg:
        return _save_bytes(data, 'svg') if _is_safe_svg(data) else None
    opt = _optimize_raster(data)
    return _save_bytes(*opt) if opt else None


def fetch_official_logo(website=None, domain=None):
    """Best-effort: Clearbit Logo API (sin API key) → favicon de Google como
    respaldo universal. Nunca lanza — devuelve None si nada sirvió."""
    d = domain_from(website, domain)
    if not d:
        return None
    for url in (f'https://logo.clearbit.com/{d}?size=256',
               f'https://www.google.com/s2/favicons?domain={d}&sz=128'):
        try:
            r = requests.get(url, timeout=FETCH_TIMEOUT)
            if r.ok and r.content and len(r.content) > 200:
                stored = validate_and_store(r.content)
                if stored:
                    return stored
        except requests.RequestException:
            logger.info('Logo fetch failed for %s via %s', d, url)
    return None
