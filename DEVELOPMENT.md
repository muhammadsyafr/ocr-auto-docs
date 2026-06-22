# Development Guide

How to run, develop, and extend the Document OCR & Extraction System locally.

See also: [README.md](README.md) · [DEPLOYMENT.md](DEPLOYMENT.md) · [PRD.md](PRD.md) · [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

---

## 1. Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker + Compose | 24+ / v2 | Easiest full-stack run |
| Python | 3.11 | Backend, if running without Docker |
| Node | 20+ | Frontend |
| Tesseract | 5.x | OCR fallback (`tesseract-ocr` + `tesseract-ocr-ind`) |
| An LLM API key | — | DeepSeek (default) or any OpenAI-compatible; optional |

---

## 2. Quick Start (Docker — recommended)

```bash
cp backend/.env.example backend/.env
# edit backend/.env -> set LLM_API_KEY (DeepSeek key)
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

First backend build is slow — `paddlepaddle` + `paddleocr` are large pip wheels. PaddleOCR also downloads model weights on first OCR run.

Stop / reset:

```bash
docker compose down          # stop
docker compose down -v        # stop + wipe DB and storage volumes
```

---

## 3. Run Without Docker (native)

### Backend

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Need local Postgres + Redis running. Point .env at them:
export DATABASE_URL=postgresql+psycopg2://ocr:ocr@localhost:5432/ocr
export REDIS_URL=redis://localhost:6379/0
export STORAGE_INPUT=./storage/input STORAGE_OUTPUT=./storage/output STORAGE_TEMP=./storage/temp
export LLM_API_KEY=sk-...

# API
uvicorn app.main:app --reload --port 8000

# Worker (separate terminal, same venv + env)
celery -A app.workers.celery_app:celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api -> localhost:8000
```

### Docker dev mode (hot reload, no rebuild)

Use the dev override to run the full stack in Docker **with hot reload** — code
edits (`.py` / `.tsx`) apply live; no image rebuild needed.

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

- **api** — `uvicorn --reload`, source mounted → reloads on save
- **worker** — `watchmedo` restarts Celery on `.py` change
- **frontend** — Vite dev server with HMR (proxies `/api` → `api:8000`)

Rebuild is still required only when `requirements.txt`, `package.json`, or a
`Dockerfile` changes. Plain prod run (baked images) stays:

```bash
docker compose up --build -d
```

---

## 4. Project Layout

```
backend/app/
├── main.py            FastAPI app, routers, startup (init_db + ensure_dirs)
├── config.py          env settings (pydantic-settings)
├── db.py              SQLAlchemy engine/session, create_all
├── pipeline.py        orchestrates one document end-to-end
├── api/               routers: process, jobs, results, export, llm
├── services/          scanner, pdf_converter, preprocess, ocr, llm, storage
├── classifiers/       rule_based classifier
├── extractors/        ktp, academic, employment
├── validators/        nik, date
├── workers/           celery_app + tasks (ingest_job, process_document)
└── models/            ORM + pydantic schemas

frontend/src/
├── router.tsx         TanStack Router route tree
├── components/        Layout + ui/ primitives (Coral Stay)
├── routes/            Dashboard, Upload, Jobs, Results, Detail, SettingsPage
├── services/api.ts    typed API client
├── lib/utils.ts       cn(), statusColor(), confidenceColor()
└── types/             shared TS types
```

---

## 5. Processing Pipeline

```
Folder/ZIP → Scanner → PDF→Image (PyMuPDF) → Preprocess (OpenCV)
  → OCR (PaddleOCR, Tesseract fallback) → Classify (rules, LLM fallback)
  → Extract (KTP=rules, academic/employment=LLM) → Validate → Unified JSON
```

- `pipeline.process_document(path, llm)` is the pure entry point — no DB.
- `workers/tasks.py` handles persistence + job state.
- LLM is optional: if no key / provider down, extraction degrades to rules only.

---

## 6. Common Tasks

### Add a new document type

1. Add keywords to `classifiers/rule_based.py`.
2. Create `extractors/<type>.py` returning an `Extraction` (see `extractors/base.py`).
3. Wire it into `pipeline.process_document`.
4. Add fields to `models/schemas.py:UnifiedFields` if new fields appear.

### Add an LLM provider

Edit `services/llm.py:_registry()` — add a `Provider` with base_url, models, key (from `config.py`). It appears in the UI automatically via `GET /api/llm/providers`.

### Change OCR language / threshold

`backend/.env`: `OCR_LANG`, `OCR_MIN_CONFIDENCE`.

---

## 7. Testing the Pipeline by Hand

```bash
# Drop test files into the input volume, then trigger a folder job
curl -X POST http://localhost:8000/api/process-folder \
  -H 'Content-Type: application/json' \
  -d '{"path":"/data/input"}'

curl http://localhost:8000/api/jobs        # watch status
curl http://localhost:8000/api/results     # list extracted docs
curl http://localhost:8000/api/export/json # full export + batch summary
```

Per-job LLM override:

```bash
curl -X POST http://localhost:8000/api/process-folder \
  -H 'Content-Type: application/json' \
  -d '{"path":"/data/input","llm":{"provider":"deepseek","model":"deepseek-chat"}}'
```

---

## 8. Offline / No-API Development

Run the bundled local LLM instead of an external API:

```bash
docker compose --profile offline up --build
docker compose exec ollama ollama pull qwen2.5    # pull a model once
# Settings page -> provider "ollama"
```

Or skip LLM entirely (KTP works rules-only; academic/employment cert# still detected by regex).

---

## 9. Logs & Debugging

```bash
docker compose logs -f api        # FastAPI
docker compose logs -f worker     # Celery / OCR pipeline
docker compose exec postgres psql -U ocr -d ocr   # inspect DB
```

Common issues:

| Symptom | Cause / Fix |
|---|---|
| Build hangs on `paddlepaddle` | Large wheel — wait; it caches after first build |
| OCR slow on first doc | PaddleOCR downloading model weights |
| Extraction fields all null | LLM key missing/invalid → check `api` logs; falls back to rules |
| `Folder not found` on process | Path must be inside the container (`/data/input`), not host path |
| CORS / API 404 in dev | Frontend proxies `/api` to `:8000` — make sure API is up |

---

## 10. Notes / Tech Debt (MVP)

- DB uses `create_all` on startup — **add Alembic migrations before prod**.
- No auth (trusted-network assumption). CORS is `*`.
- Celery runs as root in the worker container (warning is benign for local).
- Self-hosted fonts not committed — see `frontend/public/fonts/README.md`.
