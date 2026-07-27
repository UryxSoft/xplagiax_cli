# syntax=docker/dockerfile:1
#
# xplagiax_adm — imagen de producción (Flask + Flask-SocketIO)
#
# Auditoría que motiva este diseño (ver requirements.txt para el detalle):
#   - requirements.txt traía 13 dependencias sin un solo `import` en todo el
#     código (elasticsearch, qdrant_client, minio, pika, docker_py, paramiko,
#     cryptography, numpy, psutil, structlog, Flask_Limiter, Flask_Cors,
#     python_bcrypt) — sobrantes de módulos legacy ya eliminados de app.py.
#     qdrant_client/elasticsearch por sí solos arrastran grpcio+protobuf
#     (decenas de MB). Podarlas es la optimización de tamaño más grande
#     posible aquí, muy por delante de cualquier ajuste al Dockerfile.
#   - `xplagiax_db.sql` (766 KB) contiene INSERTs con datos reales
#     (párrafos de análisis, texto de usuarios) — nunca debe viajar dentro
#     de una imagen; se excluye vía .dockerignore.
#   - CMD usa gunicorn con worker eventlet (no `python app.py` / dev
#     server): es el patrón de despliegue documentado de Flask-SocketIO.
#     1 solo worker porque SocketIO mantiene el estado de sockets en
#     memoria de proceso — escalar a N workers necesitaría un message
#     queue (Redis) para el pub/sub entre procesos, fuera de alcance aquí.

# ─────────────────────────────────────────────────────────────────────────
# Stage 1/2 — builder: resuelve e instala dependencias en un venv aislado.
# Ningún compilador ni caché de pip llega a la imagen final.
# ─────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Todas las dependencias restantes publican wheels manylinux para
# linux/amd64 y linux/arm64 — no se necesita build-essential/gcc. Si en el
# futuro se agrega un paquete que compile código nativo, instalarlo SOLO
# en esta etapa (nunca en runtime).
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────
# Stage 2/2 — runtime: intérprete + venv + código de la app. Sin
# compiladores, sin gestor de paquetes de sistema, usuario no root.
# ─────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Usuario de sistema sin home ni shell de login — mínimo privilegio posible.
RUN groupadd --system appuser \
    && useradd --system --gid appuser --no-create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 5001

# HEALTHCHECK con stdlib (sin curl/wget: cero paquetes extra en la imagen).
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5001/healthz', timeout=2).status == 200 else 1)"

# Logs a stdout/stderr (access/error logfile '-'), nunca a un archivo
# dentro del contenedor. Puerto 5001: el mismo que usaba
# socketio.run(app, port=5001) en el entrypoint de desarrollo — el
# Dockerfile anterior exponía 5000 mientras el código escuchaba en 5001,
# un mismatch que nunca llegó a notarse porque nada lo probó end-to-end.
CMD ["gunicorn", \
     "--worker-class", "eventlet", "--workers", "1", \
     "--bind", "0.0.0.0:5001", "--timeout", "60", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "app:app"]
