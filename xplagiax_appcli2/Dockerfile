# syntax=docker/dockerfile:1
# ════════════════════════════════════════════════════════════════════════════
#  xplagiax_appcli2 — Dockerfile de producción (multi-stage, ligero, no-root)
#
#  Base: python:3.11-slim (NO alpine).  numpy / PyMuPDF / Pillow / bcrypt usan
#  wheels manylinux (glibc); en alpine (musl) habría que compilarlos desde fuente.
# ════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
#  Stage 1 — builder: instala dependencias en un virtualenv aislado
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Toolchain de compilación: SOLO existe en el builder, no en la imagen final.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Virtualenv autocontenido para copiarlo limpio a la etapa final.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
#  Stage 2 — runtime: imagen final mínima (sin compiladores ni cache)
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    WEB_CONCURRENCY=3

# Nº de workers de gunicorn = WEB_CONCURRENCY (override por -e en docker run).

# Runtime: libgomp1 (OpenMP de numpy) + curl (healthcheck).
# libreoffice-writer-NOGUI: SOLO lo necesario para la conversión headless
#   DOC/DOCX→PDF (imágenes, tablas, estilos) del html view del análisis — la
#   variante -nogui de Debian omite los componentes gráficos (VCL/GTK/X11),
#   ~150-200MB menos que libreoffice-writer completo. Se instala al CONSTRUIR
#   la imagen (no en runtime); el binario queda como `soffice` en PATH y
#   convert_docx_to_pdf() lo detecta solo. Sin él, cae al fallback texto-plano.
# fonts-liberation / fonts-dejavu-core: métricamente compatibles con Arial/Times/
#   Calibri → el layout del PDF convertido coincide con el del Word original.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        curl \
        libreoffice-writer-nogui \
        fonts-liberation \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    # Recortes seguros: galerías, plantillas y autotexto no se usan en conversión headless.
    && rm -rf /usr/lib/libreoffice/share/gallery \
              /usr/lib/libreoffice/share/template \
              /usr/lib/libreoffice/share/autotext \
              /usr/lib/libreoffice/share/wizards

# Copia el virtualenv ya construido desde el builder.
COPY --from=builder /opt/venv /opt/venv

# Usuario y grupo no-root.
RUN groupadd --system app \
    && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Código de la app (el .dockerignore excluye venv, caches, tests, secretos, etc.)
COPY --chown=appuser:app . .

# Carpetas de runtime con permisos del usuario no-root.
RUN mkdir -p \
        /app/modules/doc_service/uploads/uploads_analysis \
        /app/modules/doc_service/uploads/uploads_save \
        /app/uploads \
    && chown -R appuser:app /app

USER appuser

# Solo se expone el puerto de la app.
EXPOSE 5003

# Healthcheck simple contra el endpoint /test_alive.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5003/test_alive', timeout=4)" || exit 1

# Servidor WSGI de producción (NUNCA app.run()). Config completa en
# gunicorn.conf.py — un CMD exec-array no expande WEB_CONCURRENCY/env vars,
# así que --workers tiene que venir de un archivo de config, no de flags acá.
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
