<div align="center">

# XPlagiaX · `appcli2`

**AI‑content detection, academic source matching & document analysis — for education.**

[![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-23.0-499848?logo=gunicorn&logoColor=white)](https://gunicorn.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Build](https://img.shields.io/badge/build-not%20configured-lightgrey)]()
[![Coverage](https://img.shields.io/badge/coverage-PENDIENTE-lightgrey)]()
[![Version](https://img.shields.io/badge/version-PENDIENTE-blue)]()
[![License](https://img.shields.io/badge/license-Proprietary-red)]()

</div>

---

`appcli2` is the **user‑facing web application** of the XPlagiaX platform: a Flask service where students and institutions upload documents (or paste text) and receive **AI‑generated‑content detection** and **academic source / plagiarism analysis**. It is a **modular monolith** (Flask blueprints) that runs as **one container inside a microservices ecosystem** (`xplagiax-net`), delegating the heavy ML inference to dedicated sibling services and sharing MySQL, Redis, Qdrant and SeaweedFS with the rest of the platform.

> © URYX TECHNOLOGIES SRL — Proprietary software.

---

## 📑 Table of Contents

- [Architecture](#-architecture)
- [Folder Structure](#-folder-structure)
- [Modules & Responsibilities](#-modules--responsibilities)
- [API Reference](#-api-reference)
- [External Services](#-external-services)
- [Analysis Pipeline & UI](#-analysis-pipeline--ui)
- [Environment Variables](#-environment-variables)
- [Prerequisites](#-prerequisites)
- [Local Setup](#-local-setup)
- [Running with Docker](#-running-with-docker)
- [Testing](#-testing)
- [CI/CD](#-cicd)
- [Code Conventions](#-code-conventions)
- [Troubleshooting / FAQ](#-troubleshooting--faq)
- [Changelog — Recent Improvements](#-changelog--recent-improvements)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License & Author](#-license--author)

---

## 🏛 Architecture

**Style:** Modular monolith (Flask blueprints) acting as a single node within a containerized microservices ecosystem.

**Key design decisions**

| Decision | Rationale |
|---|---|
| **Modular monolith** (one Flask app, many blueprints) | Simple deploy & shared session/auth, while keeping clear module boundaries by domain (`doc`, `billing`, `auth`, `bucket`…). |
| **ML offloaded to sibling services** | The web container stays lightweight (~450 MB). AI detection (`xota`) and source matching (`finderx`) run as independent services and scale separately. |
| **Backend proxy for analysis** (`/x_doc/analyze_text`, `/x_doc/finderx_check`) | Avoids browser CORS and keeps the upstream API keys server‑side instead of exposing them in the frontend. |
| **Shared infra over `xplagiax-net`** | MySQL, Redis, Qdrant and SeaweedFS are shared across the ecosystem; the app reaches them by container name. |
| **12‑factor config** | All hosts/credentials are read from environment variables (`config.py`) with safe local defaults. |
| **WSGI in production** | `gunicorn` (sync workers) — never the Flask dev server. |

```mermaid
flowchart TD
    User([Browser / User])

    subgraph net["Docker network: xplagiax-net"]
        APP["appcli2 (Flask + Gunicorn)\n:5003"]

        subgraph data["Shared data plane"]
            MySQL[("MySQL\nmysql-container:3306")]
            Redis[("Redis\nredis:6379")]
            Qdrant[("Qdrant\nqdrant:6333")]
            Seaweed[("SeaweedFS\nfiler:8888 / master:9333")]
        end

        subgraph ml["ML / analysis services"]
            Xota["AI Detection (xota)\nxplagiax-xota:5006"]
            Finderx["FinderX (sources/plagiarism)\nxplagiax_finderx_api:8000"]
            ImgSvc["Image Service\nxplagiax_image_service:5010"]
        end
    end

    subgraph ext["Third-party APIs"]
        SMTP["SMTP (IONOS)"]
        OAuth["Google / Microsoft / Dropbox / Box"]
        Pay["Stripe / PayPal"]
    end

    User -->|HTTPS| APP
    APP -->|SQLAlchemy| MySQL
    APP -->|cache / rate-limit / celery| Redis
    APP -->|vector search| Qdrant
    APP -->|document storage| Seaweed
    APP -->|"POST /analyze_document_async"| Xota
    APP -->|"POST /api/v1/academic-check"| Finderx
    APP -->|image search| ImgSvc
    APP --> SMTP
    APP --> OAuth
    APP --> Pay
```

**Document analysis data flow**

```mermaid
sequenceDiagram
    participant U as Browser
    participant A as appcli2
    participant X as xota (:5006)
    participant F as FinderX (:8000)

    U->>A: POST /x_doc/extract_text (file)
    A->>A: DocAnalysisTask → texto + metadata + PDF→HTML
    A-->>U: { text, word_count, result_view, ... }
    U->>A: POST /x_doc/analyze_text { text }
    A->>X: POST /analyze_document_async (X-API-Key)
    X-->>A: { ai_percentage, segments[] }
    U->>A: POST /x_doc/finderx_check { text }
    A->>F: POST /api/v1/academic-check (X-API-Key) → job_id
    loop polling
        A->>F: GET /api/v1/report/{job_id}
        F-->>A: status: completed → result
    end
    A-->>U: split view (AI + Sources)
```

---

## 🗂 Folder Structure

```text
xplagiax_appcli2/
├── app.py                      # Entry point: Flask app, blueprint registration, error handlers
├── Dockerfile                  # Multi-stage production image (python:3.11-slim, non-root)
├── .dockerignore
├── requirements.txt
├── migrations/                 # Flask-Migrate (Alembic) database migrations
│
├── settings/                   # Cross-cutting configuration & shared singletons
│   ├── config.py               #   Env-driven config (Dev/Test/Prod)
│   ├── connections.py          #   db, login_manager, mail, oauth, csrf, limiter
│   ├── redisconnect.py         #   Shared Redis client
│   └── ...
│
├── modules/                    # Domain blueprints (one folder per bounded context)
│   ├── apps_service/           #   Public pages: index, login, register, pricing
│   ├── auth_service/           #   Auth + OAuth (Google, Microsoft, Dropbox, Box)
│   ├── billing_service/        #   Subscriptions, Stripe & PayPal
│   ├── bucket_service/         #   SeaweedFS storage client & file ops
│   ├── cleanup_service/        #   Maintenance / housekeeping tasks
│   ├── doc_service/            #   ★ Core: document parsing, AI & source analysis
│   │   └── modules/            #     DocAnalysisTask, PDF→HTML, OCR, topic classifier
│   ├── image_service/          #   Image similarity search (Qdrant + CLIP)
│   ├── integration_service/    #   Cloud-storage integrations (OneDrive, Drive…)
│   ├── models/                 #   SQLAlchemy ORM models
│   ├── system_status_service/  #   Public status/metrics dashboard
│   └── users_service/          #   User dashboard, folders, tags, sharing
│
├── templates/                  # Jinja2 templates (auth, billing, user, emails, errors)
├── static/                     # css / js / img (WebP-optimized)
└── tests/                      # pytest suites
```

---

## 🧩 Modules & Responsibilities

| Blueprint | URL prefix | Responsibility | Main dependencies |
|---|---|---|---|
| `x_apps` | `/` | Public landing, login/register/pricing pages, error handlers | Flask, Jinja2 |
| `x_users` | `/` | User dashboard, folders, tags, sharing, history | SQLAlchemy, SeaweedFS |
| `auth_bp` | `/auth_bp` | Authentication + OAuth (Google, Microsoft, Dropbox, Box) | Authlib, Flask-Dance, bcrypt, PyJWT |
| `billing_bp` | `/billing_bp` | Plans, subscriptions, payments | Stripe, paypalrestsdk |
| `x_buck` | `/x_buck` | SeaweedFS object storage operations | requests |
| `x_doc` | `/x_doc` | **Core** — document parsing, AI detection & source analysis | PyMuPDF, Pillow, python-docx, reportlab, Qdrant, fast-langdetect |
| `x_image` | `/x_image` | Image similarity search | qdrant-client |
| `x_integ` | `/x_integ` | Cloud-storage integrations | requests |
| `x_analysiscounter` | `/x_analysiscounter` | Quota enforcement + analysis orchestration | Redis |
| `x_cleanup` | `/x_cleanup` | Maintenance / cleanup jobs | SQLAlchemy |
| `x_system_status` | `/x_system_status` | Public status & metrics (no auth) | Redis, psutil |

> Route count by module (live): `doc_service` 35 · `integration_service` 28 · `auth_service` 22 · `users_service` 21 · `bucket_service` 20 · `billing_service` 16 · `image_service` 9 · `cleanup_service` 8 · `system_status` 7 · `apps_service` 6 · `analysis_counter` 5.

---

## 🔌 API Reference

> Base URL (container): `http://xplagiax_appcli:5003` · (host) `http://localhost:5003`.
> Most write endpoints require an authenticated session (`@login_required`). Public exceptions: health, status, landing pages.

### Health

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/test_alive` | ❌ | Liveness probe used by the container `HEALTHCHECK`. Returns `200 OK`. |

### Core analysis — `x_doc`

#### `POST /x_doc/extract_text`
Extracts full text (+ metadata, language, images, annotations, URLs) from a document and generates an HTML preview.

```bash
curl -X POST http://localhost:5003/x_doc/extract_text \
  -H "Cookie: session=<session>" \
  -F "analysis_file=@thesis.pdf"
```
```json
{
  "success": true,
  "text": "Full document text…",
  "word_count": 1840,
  "language": "en",
  "metadata": { "...": "..." },
  "images": ["/x_doc/serve_analysis/…/page_1_img_1.png"],
  "annotations": [], "urls": [],
  "result_view": "/x_doc/serve_analysis/…/result.html"
}
```

| Param | In | Type | Required | Description |
|---|---|---|---|---|
| `analysis_file` | form-data | file | ✅ | PDF / DOC / DOCX / FB2 / MOBI / EPUB |

**Status:** `200` ok · `400` bad type / no file · `401` unauthenticated · `422` not enough text (min 10 words) · `500` extraction error.

#### `POST /x_doc/analyze_text`
Proxy to the AI‑detection service. Body: `{ "text": "...", "plugins": ["ai_detection"] }`.

```json
{ "status": "ok", "word_count": 620,
  "results": { "ai_detection": { "data": {
    "ai_percentage": 90.67, "human_percentage": 9.33,
    "detected_model": "gpt4",
    "segments": [{ "dominant_label": "AI", "score": 90.66, "text": "…" }]
  }}}}
```
**Status:** `200` · `400` <10 words · `401` · `502` upstream error.

#### `POST /x_doc/finderx_check`
Submits text to FinderX (academic source / plagiarism) and polls until completion.

```json
{ "success": true, "status": "completed", "result": {
    "scores": { "overall": 12.5, "exact": 8.0, "semantic": 20.0 },
    "fragment_decisions": [ { "decision_label": "Plagio detectado", "final_score": 87.0, "qdrant_sources": [ { "title": "…", "url": "https://doi.org/…" } ] } ],
    "citation_analysis": { "dominant_style": "APA", "citation_coverage": 75.0 },
    "academic_matches": [ { "title": "Attention Is All You Need", "doi": "10.48550/arXiv.1706.03762" } ]
}}
```
**Status:** `200` · `400` <10 words · `401` · `502` service error · `504` timeout (default 90 s).

#### `POST /x_doc/uploadanalysis`
Legacy full pipeline (parsing + Qdrant + AI + DB persistence). Multipart: `analysis_file`, `analysis_types[]`.

### Document management — `x_doc` (selected)

| Method | Path | Description |
|---|---|---|
| `GET` | `/x_doc/folders` | List user folders (tree) |
| `POST` | `/x_doc/folders/create` | Create folder |
| `POST` | `/x_doc/folders/rename/<folder_id>` | Rename folder |
| `POST` | `/x_doc/organize/move` · `/organize/trash` · `/organize/restore` · `/organize/permanent-delete` | Organize items |
| `POST`/`DELETE` | `/x_doc/share`, `/x_doc/share/<share_id>` | Collaborative sharing |
| `GET` | `/x_doc/serve_analysis/<path:filepath>` | Serve generated analysis HTML/images |

### Analysis quota — `x_analysiscounter`

| Method | Path | Description |
|---|---|---|
| `POST` | `/x_analysiscounter/api/analysis/validate-and-analyze` | Validate quota then run analysis |
| `GET` | `/x_analysiscounter/api/analysis/stats` | Remaining quota / usage |
| `GET` | `/x_analysiscounter/api/analysis/plans` | Plan limits |

### System status — `x_system_status` (public)

| Method | Path | Description |
|---|---|---|
| `GET` | `/x_system_status/api/status` | Aggregate health of dependencies |
| `GET` | `/x_system_status/api/metrics` · `/api/live-stats` · `/api/heatmap` · `/api/sparklines` | Metrics for the status dashboard |

> Full route inventory lives in each blueprint under `modules/*/`. The table above documents the high‑value endpoints; the remaining CRUD routes (tags, files, billing, integrations) follow the same conventions.

---

## 🛰 External Services

| Service | Address (`xplagiax-net`) | Protocol | Purpose |
|---|---|---|---|
| **MySQL** | `mysql-container:3306` | TCP (PyMySQL) | Primary relational store (`xplagiax_db`) |
| **Redis** | `redis:6379` | RESP | Rate-limiting (db 14), Celery broker/result (db 12/13), app cache (db 11) |
| **Qdrant** | `qdrant:6333` | HTTP | Vector search (essays, images) |
| **SeaweedFS** | `seaweedfs-filer:8888` / `seaweedfs-master:9333` | HTTP | Document & asset object storage |
| **AI Detection (xota)** | `xplagiax-xota:5006` | REST (`X-API-Key`) | AI-generated content detection |
| **FinderX** | `xplagiax_finderx_api:8000` | REST async + polling (`X-API-Key`) | Academic source / plagiarism analysis |
| **Image Service** | `xplagiax_image_service:5010` | REST | Image similarity search |
| **SMTP (IONOS)** | `smtp.ionos.com:587` | SMTP/TLS | Transactional & billing email |
| **OAuth** | Google / Microsoft / Dropbox / Box | OAuth 2.0 | Login & cloud-storage import |
| **Payments** | Stripe / PayPal | REST | Subscriptions & billing |

---

## 🔬 Analysis Pipeline & UI

The text/document analysis screen (`/analysiss`, [`templates/user/analysis_smartinput.html`](templates/user/analysis_smartinput.html)) runs **AI detection** (xota) and **source/plagiarism** (FinderX) and renders them in a resizable **split view** (input text · results). The flow mirrors `xplagiax_marktrack`'s `documentedit`, adapted to appcli2's light "glass" design.

### Data flow

```mermaid
flowchart LR
    U([User]) -->|paste text / upload doc| FE[analysis_smartinput.html]
    FE -->|doc only| EX["POST /x_doc/extract_text<br/>(server-side parsing)"]
    EX --> FE
    FE -->|AI| AT["POST /x_doc/analyze_text<br/>(sync proxy → xota)"]
    FE -->|FinderX| FX["POST /x_doc/finderx_check → job_id<br/>GET /x_doc/finderx_report/&lt;id&gt; (poll)"]
    AT --> MAP[_mapApiResponse]
    FX --> SRC[source result]
    MAP --> RENDER[Split view + tabs]
    SRC --> RENDER
```

### AI service mode — `sync` vs `async`

| Mode (`AI_SERVICE_MODE`) | Endpoint | Needs Celery worker? |
|---|---|---|
| **`sync` (default)** | `xota:5006/analyze_document` — processes inline, returns `{results}` | **No** |
| `async` | `xota:5006/analyze_document_async` → `task_id` → poll `/analyze_status/{id}` | **Yes** (xota worker) |

> The current xota deployment has **no Celery worker**, so `async` stays `pending` forever (affects all clients, marktrack included). appcli2 defaults to **`sync`** to work without it. FinderX **does** have a worker (`xplagiax_finderx_worker`), so its async + polling flow works.

### How results are processed (JS, in `AdvancedInputComponent`)

| Concern | Logic |
|---|---|
| **AI mapping** (`_mapApiResponse`) | Reads `results.ai_detection.data` (fallback `.ai_detection`); maps `ai_percentage`, `human_percentage`, `detected_model`, `segments[]` → blocks (`type`, `confidence`, `text`). |
| **Segment normalization** | Each segment's score is expressed as AI-probability; `dominant_label === 'human'` → green, `'ai'` → red. |
| **FinderX false-positive** (`_buildCorpusWarning`) | If academic sources are found **but all fragments are original** (0% direct, `similarity_score < 0.2`) and overall ≥ 20% → flags it as **thematic/semantic overlap, not plagiarism** (dedup + top-5 sources by snippet length). Ported from marktrack. |
| **Fragment status** (`_buildFragmentBlockHtml`) | Derives a coherent verdict from `similarity_score` + `has_citation` + `decision` (Plagiarism / Cited quote / Original…) instead of showing the raw `zone_type`. |

### UI components

- **Integrity card** (`_buildIntegrityCard` / `_animateIntegrityCard`) — glass card with an animated multi-ring gauge, count-up stats and legend. The combined view shows a single **Overview** card (5 rings: Human · Original · AI · Similarity · Reference).
- **Tabs** (`_wireSplitTabs`): `Overview` · `AI Detection` · `Sources` · `Citations` · `Academic`.
- **Segment highlighting** (`_highlightSegments` / `_focusSegment`): the input text is highlighted per segment (green = Human, red = AI); clicking a result block scrolls to and pulses the matching span (with prefix fallback for whitespace drift).
- **"Your text vs Academic source"** side-by-side comparison inside FinderX fragments.

---

## ⚙️ Environment Variables

All configuration is read from the environment (`settings/config.py`) with safe defaults for local dev.

| Variable | Description | Type | Default | Required |
|---|---|---|---|---|
| `FLASK_ENV` | Config profile: `development` / `testing` / `production` | str | `development` | ✅ (prod) |
| `SECRET_KEY` | Flask session signing key | str | *(insecure dev default)* | ✅ |
| `SECURITY_PASSWORD_SALT` | Password/token salt | str | *(dev default)* | ✅ |
| `DATABASE_URL` | SQLAlchemy URI | str | `mysql+pymysql://root:@localhost/xplagiax_db` | ✅ |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | Redis connection | str/int/int | `localhost` / `6379` / `11` | ✅ |
| `REDIS_URL` | Rate-limiter storage URI | str | `redis://localhost:6379/14` | ⬜ |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Celery transport | str | `redis://localhost:6379/12` · `/13` | ⬜ |
| `QDRANT_HOST` / `QDRANT_PORT` | Qdrant endpoint | str/int | `localhost` / `6333` | ⬜ |
| `QDRANT_API_KEY` | Qdrant auth | str | `None` | ⬜ |
| `SEAWEEDFS_FILER_URL` / `SEAWEEDFS_MASTER_URL` | SeaweedFS endpoints | str | `http://localhost:8333` | ⬜ |
| `SEAWEEDFS_BUCKET` | Storage bucket | str | `xplagiax-users-documents` | ⬜ |
| `AI_TEXT_SERVICE_URL` (or `XPLAGIAX_URL`) | AI detection endpoint | str | `http://localhost:5006/analyze_document_async` | ✅ |
| `AI_TEXT_SERVICE_API_KEY` | AI service key | str | *(default key)* | ✅ |
| `AI_SERVICE_MODE` | `sync` (inline, no worker) or `async` (worker + poll) | str | `sync` | ⬜ |
| `FINDERX_SERVICE_BASE` (or `FINDERX_URL`) | FinderX base URL | str | `http://localhost:8000` | ✅ |
| `FINDERX_SERVICE_API_KEY` (or `FINDERX_API_KEY`) | FinderX key | str | *(default key)* | ✅ |
| `FINDERX_POLL_INTERVAL` / `FINDERX_POLL_TIMEOUT` | Polling tuning (s) | float | `1.5` / `90` | ⬜ |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | SMTP credentials | str | *(dev default)* | ✅ (email) |
| `GOOGLE_REDIRECT_URI` / `MICROSOFT_REDIRECT_URI` | OAuth callbacks (must match the provider console exactly) | str | `localhost` callbacks | ✅ (OAuth) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` … (`ONEDRIVE_*`, `DROPBOX_*`, `BOX_*`) | OAuth credentials (shared with marktrack — register both redirect URIs) | str | *(defaults)* | ⬜ |
| `OAUTH_RELAX_STATE` | ⚠️ Temporary: skip OAuth `state` (CSRF) check when the session cookie doesn't persist. Set `false` once login is stable. | bool | `true` | ⬜ |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | Stripe | str | `""` | ⬜ |
| `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` / `PAYPAL_MODE` / `PAYPAL_WEBHOOK_ID` | PayPal | str | *(defaults)* / `live` | ⬜ |
| `SERPAPI_KEY` / `ZENSERP_KEY` | Web-search providers | str | *(defaults)* | ⬜ |
| `WEB_CONCURRENCY` | Gunicorn workers | int | `3` | ⬜ |

### `.env.example`

```dotenv
# Core
FLASK_ENV=production
SECRET_KEY=change-me-64-hex
SECURITY_PASSWORD_SALT=change-me-random
WEB_CONCURRENCY=2

# Database
DATABASE_URL=mysql+pymysql://xplagiaxadminuser:xplagiax001@mysql-container:3306/xplagiax_db?charset=utf8mb4

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=11
REDIS_URL=redis://redis:6379/14
CELERY_BROKER_URL=redis://redis:6379/12
CELERY_RESULT_BACKEND=redis://redis:6379/13

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# SeaweedFS
SEAWEEDFS_FILER_URL=http://seaweedfs-filer:8888
SEAWEEDFS_MASTER_URL=http://seaweedfs-master:9333

# Analysis services
AI_TEXT_SERVICE_URL=http://xplagiax-xota:5006/analyze_document_async
AI_TEXT_SERVICE_API_KEY=__set_me__
FINDERX_SERVICE_BASE=http://xplagiax_finderx_api:8000
FINDERX_SERVICE_API_KEY=__set_me__

# Email / OAuth (login)
MAIL_USERNAME=noreply@XplagiaX.ca
MAIL_PASSWORD=__set_me__
GOOGLE_CLIENT_ID=__set_me__
GOOGLE_CLIENT_SECRET=__set_me__          # login con Google (mismo cliente que Google Drive)
GOOGLE_REDIRECT_URI=https://app.xplagiax.ca/auth_bp/google/callbackx
MICROSOFT_REDIRECT_URI=https://app.xplagiax.ca/auth_bp/microsoft/callback

# Cloud Storage OAuth (pantalla /cloudstorage). Los secretos NO tienen default
# en el código: sin la env var el provider queda deshabilitado (callback 503).
DROPBOX_CLIENT_ID=__set_me__
DROPBOX_CLIENT_SECRET=__set_me__
BOX_CLIENT_ID=__set_me__
BOX_CLIENT_SECRET=__set_me__
ONEDRIVE_CLIENT_ID=__set_me__
ONEDRIVE_CLIENT_SECRET=__set_me__
# PKCE por-provider (default: Google/OneDrive on, Dropbox/Box off). Override:
# OAUTH_PKCE_DROPBOX=true

# Cifrado en reposo de los tokens OAuth de cloud storage (Fernet). Genera:
#   python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"
# Si falta, se deriva de SECRET_KEY (se recomienda una clave dedicada).
TOKEN_ENCRYPTION_KEY=__set_me__

# Límites de listado de cloud storage (performance)
STORAGE_MAX_FILES=500
STORAGE_MAX_PAGES=20
STORAGE_QUOTA_TTL=300
```

---

## 📋 Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 |
| Docker | 24+ (with a `xplagiax-net` network) |
| MySQL | 8.x (schema `xplagiax_db`) |
| Redis | 6+ |
| Qdrant | latest |
| SeaweedFS | latest (filer + master) |
| OS build deps (local, non-Docker) | `build-essential`, `libffi-dev`, `libgomp1` |

---

## 💻 Local Setup

```bash
# 1. Clone (private repo)
git clone https://github.com/UryxSoft/xplagiax_cli.git
cd xplagiax_cli/xplagiax_appcli2

# 2. Virtualenv
python3.11 -m venv .venv && source .venv/bin/activate

# 3. Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env      # edit values
export $(grep -v '^#' .env | xargs)   # or use python-dotenv

# 5. Database migrations (Flask-Migrate)
export FLASK_APP=app.py
flask db upgrade

# 6. Run (dev)
python app.py             # http://127.0.0.1:5003
```

---

## 🐳 Running with Docker

The image is a **multi-stage, non-root, slim** build that listens on **`:5003`**.

```bash
# Build (private repo, full secrets passed at runtime)
docker build --no-cache -t xplagiax_appcli2:latest .

# Run on the shared ecosystem network
docker run -d \
  --name xplagiax_appcli \
  --network xplagiax-net \
  --restart unless-stopped \
  --shm-size=128m --stop-timeout=35 --ulimit nofile=65535:65535 \
  --memory=1g --memory-reservation=768m --cpus=1.5 \
  --log-opt max-size=20m --log-opt max-file=5 \
  -p 5003:5003 \
  -v xplagiax_appcli2_uploads:/app/uploads \
  -v xplagiax_appcli2_docs:/app/modules/doc_service/uploads \
  --health-cmd="curl -f http://localhost:5003/test_alive || exit 1" \
  --health-interval=30s --health-timeout=10s --health-retries=3 --health-start-period=60s \
  -e FLASK_ENV="production" \
  -e WEB_CONCURRENCY="2" \
  -e SECRET_KEY="GENERA_UNO_NUEVO_64_HEX" \
  -e SECURITY_PASSWORD_SALT="GENERA_OTRO_ALEATORIO" \
  -e DATABASE_URL="mysql+pymysql://xplagiaxadminuser:xplagiax001@mysql-container:3306/xplagiax_db?charset=utf8mb4" \
  -e REDIS_HOST="redis" -e REDIS_PORT="6379" -e REDIS_DB="11" \
  -e REDIS_URL="redis://redis:6379/14" \
  -e CELERY_BROKER_URL="redis://redis:6379/12" \
  -e CELERY_RESULT_BACKEND="redis://redis:6379/13" \
  -e QDRANT_HOST="qdrant" -e QDRANT_PORT="6333" \
  -e SEAWEEDFS_FILER_URL="http://seaweedfs-filer:8888" \
  -e SEAWEEDFS_MASTER_URL="http://seaweedfs-master:9333" \
  -e AI_TEXT_SERVICE_URL="http://xplagiax-xota:5006/analyze_document_async" \
  -e AI_TEXT_SERVICE_API_KEY="7d9a2c4f8e1b3d5a6f7c9e2b4a1d8c3f" \
  -e FINDERX_SERVICE_BASE="http://xplagiax_finderx_api:8000" \
  -e FINDERX_SERVICE_API_KEY="xpx-3Td8C2oecnAXRT0-VioypUjMWTtSTQVj3k2kE8Q-5tc" \
  -e GOOGLE_REDIRECT_URI="https://app.xplagiax.ca/auth_bp/google/callbackx" \
  -e MICROSOFT_REDIRECT_URI="https://app.xplagiax.ca/auth_bp/microsoft/callback" \
  -e MAIL_USERNAME="noreply@XplagiaX.ca" \
  -e MAIL_PASSWORD="MYR1xkd2kqc_gat2hem" \
  xplagiax_appcli2:latest

# Verify
docker logs -f xplagiax_appcli
docker exec xplagiax_appcli curl -fsS http://localhost:5003/test_alive
```

> 💡 Prefer `--env-file xplagiax_appcli2.env` over many `-e` flags to keep secrets out of your shell history.
> `docker-compose.yml`: **[PENDIENTE DE DEFINIR]** (not yet in the repo).

---

## 🧪 Testing

Tests use **pytest** and live under `tests/` (`test_payment_config.py`, `test_routes_bucket.py`).

```bash
pip install pytest pytest-cov
pytest -v
pytest --cov=modules --cov-report=term-missing   # coverage
```

> Current coverage: **[PENDIENTE DE DEFINIR]**.

---

## 🔄 CI/CD

**[PENDIENTE DE DEFINIR]** — no pipeline is committed yet. Recommended baseline (GitHub Actions):

- `lint` → ruff/flake8 · `test` → pytest+coverage · `build` → docker build · `deploy` → push image & `docker run` on the VPS.

---

## 🎨 Code Conventions

| Area | Tool / Rule |
|---|---|
| Formatting | `black` (suggested) — **[PENDIENTE: adoptar]** |
| Linting | `ruff` / `flake8` — **[PENDIENTE: adoptar]** |
| Imports | stdlib → third-party → local |
| Commits | [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:` …) — recommended |
| Config | 12-factor: never hardcode hosts/secrets; read from env |

---

## 🆘 Troubleshooting / FAQ

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'X'` at boot | Missing dependency in `requirements.txt` | Add it and rebuild with `docker build --no-cache` |
| `RPC failed; HTTP 400` on `git push` | Blob >100 MB in history (e.g. `venv/`) | Purge from history (`git filter-repo`) / fresh history; keep `venv` ignored |
| Worker fails to boot — DB error | Wrong `DATABASE_URL` / MySQL not on `xplagiax-net` | Use container name `mysql-container`, not `localhost` |
| FinderX returns `504` | Upstream slow / timeout | Increase `FINDERX_POLL_TIMEOUT` |
| AI/Source analysis `502` | Sibling service down | Check `xplagiax-xota` / `xplagiax_finderx_api` containers |
| AI analysis stuck — status `pending` forever | xota has no Celery worker; `async` jobs never run | Use `AI_SERVICE_MODE=sync` (default) — uses the inline `/analyze_document` endpoint |
| Google login loops back to `/login` | Shared OAuth client; `app.xplagiax.ca` redirect URI not registered, **or** session `state` lost | Register the redirect URI in Google Cloud Console; keep `SECRET_KEY` fixed; temp bypass via `OAUTH_RELAX_STATE=true` |
| Logout redirects to `127.0.0.1:5000` | Stale cached `logout.js` / missing ProxyFix | Hard-refresh (`/static` is cached 1y); ProxyFix is enabled in `app.py` |
| Healthcheck unhealthy | `curl` missing or wrong port | Image ships `curl`; ensure probe hits `:5003/test_alive` |

---

## 📝 Changelog — Recent Improvements

### Cloud Storage integration audit (Google Drive · Dropbox · Box · OneDrive)

Full 5-phase hardening of the `/cloudstorage` OAuth integration
(`modules/integration_service/`).

**Phase 1 — Security (critical)**
- OAuth `state` (anti-CSRF) validation re-enabled with constant-time compare;
  works now that `SESSION_COOKIE_SAMESITE=Lax` (the cookie survives the OAuth
  callback).
- Removed the hardcoded `session['user_id']=1` fallback — it mixed one user's
  cloud tokens into user 1 (IDOR / cross-account leak). The callback now
  requires a real session.
- **Tokens encrypted at rest** with Fernet (`token_crypto.py`), transparently
  backward-compatible with legacy plaintext rows (`TOKEN_ENCRYPTION_KEY`).
- Removed the TLS `verify=False` fallback (MITM risk on the token exchange).
- Provider `client_secret`s moved to env-only (no defaults in code); a missing
  secret disables that provider with a `503` instead of using a leaked value.

**Phase 2 — Functional correctness**
- **PKCE (S256)** for Google & OneDrive (confidential-client-safe); per-provider
  toggle via `OAUTH_PKCE_<PROVIDER>`.
- Refresh tokens now actually issued: Dropbox `token_access_type=offline`,
  Google `access_type=offline&prompt=consent`; provider-aware auth params
  (the old blanket `access_type=offline` was a Google-only no-op elsewhere).
- Token expiry compared in **UTC** with a 60 s refresh margin.
- UI aligned to the 4 real providers (added OneDrive; removed pcloud/mega/yandex).

**Phase 3 — Architecture**
- `TokenRepository` (Repository pattern) — single, testable place for token
  persistence + encryption + expiry; the ~40 call sites keep working via thin
  facades.
- `documents` screen: removed a broken duplicate route (rendered a missing
  template → 500) and a stub API returning fake hardcoded data.

**Phase 4 — Performance**
- Bounded provider file-listing pagination (`STORAGE_MAX_FILES` /
  `STORAGE_MAX_PAGES`) — no more pulling an entire account into memory.
- Short-TTL Redis cache of storage quota (`STORAGE_QUOTA_TTL`), best-effort
  (tolerates Redis down).

**Phase 5 — UX**
- Frontend provider maps (name/icon/brand) made consistent with the 4 real
  providers.

> Manual follow-ups (not code): rotate the 4 OAuth `client_secret`s in each
> provider console, set the new env vars, and purge the old secrets from git
> history. See `.env.example`.

### Analysis screen & UI

- **Analysis counter** now decrements *after* results are delivered (was
  counting before).
- **Analysis history** (`/x_doc/history`): `Scholar Suite` added to the paid
  plans that save history; the frontend no longer silently swallows the `403`
  when a plan doesn't include history.
- **Confirmation modals** for the Trash / Archived / Auto-Archived offcanvases:
  professional delete & restore modals (`confirm_modal.css` + `xpConfirm()` in
  `base_page.js`), matching the app's modal standard — replaces the native
  `confirm()` dialogs and adds confirmation to restore actions.
- **Settings**: removed the *Watermark Detection* and *Citation Check* plugin
  toggles.

---

## 🗺 Roadmap

- [ ] `docker-compose.yml` for the full ecosystem (`appcli2` + mysql + redis + qdrant + seaweedfs)
- [ ] GitHub Actions CI (lint + test + build + deploy)
- [ ] Parameterize remaining internal calls (`/x_search`, `/enhanced_img`) via env (`*_SERVICE_URL`)
- [ ] WebSocket support for Flask-SocketIO (eventlet/gevent worker)
- [ ] Move all secrets out of `config.py` defaults and rotate exposed keys
- [ ] Test coverage ≥ 80%
- [ ] OpenAPI/Swagger spec for the public API
- [x] AI/FinderX split-view, integrity card, tabs & segment highlighting
- [x] FinderX false-positive (thematic vs direct-copy) detection
- [ ] Analysis tabs: **Style Analysis** (`stylometric_analysis`) & **References Integrity** (`citation_check`)
- [ ] Overview **alert cards** linking to each analysis tab
- [ ] Re-enable strict OAuth `state` once login is stable (`OAUTH_RELAX_STATE=false`)

---

## 🤝 Contributing

```bash
git checkout -b feat/my-feature
# … changes + tests …
git commit -m "feat: add my feature"
git push origin feat/my-feature
# open a Pull Request against main
```

1. Fork / branch from `main`.
2. Keep changes scoped; add tests where applicable.
3. Run `pytest` before pushing.
4. Use Conventional Commit messages.

---

## 📄 License & Author

| | |
|---|---|
| **License** | Proprietary — © URYX TECHNOLOGIES SRL (LICENSE file: **[PENDIENTE DE DEFINIR]**) |
| **Maintainer** | **[PENDIENTE DE DEFINIR]** (name / email) |
| **Links** | **[PENDIENTE DE DEFINIR]** (website / LinkedIn / GitHub org) |

<div align="center"><sub>Part of the <b>XPlagiaX</b> platform · Built with Flask 🐍</sub></div>
