# Document OCR & Extraction System

Local document OCR + structured extraction (KTP, academic certificates, employment certificates) → unified JSON. See [PRD.md](PRD.md), [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), [DESIGN.md](DESIGN.md).

## Architecture

```
Folder/ZIP → Scanner → PDF→Image → OCR (PaddleOCR / Tesseract)
  → Classifier → Extractor (rules + external LLM) → Validator → JSON
```

- **OCR + rule extraction**: fully local.
- **LLM extraction** (academic / employment): external OpenAI-compatible API (default DeepSeek), selectable from the UI. Only OCR *text* is sent — never raw files. Offline mode available via local Ollama.

## Stack

| | |
|---|---|
| Backend | FastAPI, Celery, Redis, PostgreSQL, PaddleOCR, Tesseract, PyMuPDF, OpenCV |
| Frontend | React 19, TanStack Router/Query/Table, Tailwind, Coral Stay design system |
| LLM | OpenAI-compatible API (DeepSeek default) / Ollama (offline) |

## Run

```bash
cp backend/.env.example backend/.env
# set LLM_API_KEY in backend/.env (DeepSeek key)
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

Offline LLM (no external API):

```bash
docker compose --profile offline up --build
# then in Settings page pick provider "ollama"
```

## Layout

```
backend/   FastAPI app, OCR pipeline, Celery workers
frontend/  React + Coral Stay UI
docker-compose.yml
```

## API (PRD §11)

| Method | Path | |
|---|---|---|
| POST | /api/process-folder | start job from folder (optional `llm` override) |
| POST | /api/process-zip | start job from ZIP |
| POST | /api/upload | drag-drop / ZIP upload |
| GET | /api/jobs | list jobs |
| GET | /api/metrics | dashboard counts |
| GET | /api/results | list documents |
| GET | /api/results/{id} | detail (unified schema) |
| GET | /api/results/{id}/file | original file preview |
| GET | /api/export/json | all results + batch summary |
| GET | /api/llm/providers | list providers/models (no keys) |
| PUT | /api/settings/llm | set default provider/model |

## Notes

- DB tables auto-create on startup (MVP; swap to Alembic migrations for prod).
- Self-host fonts in `frontend/public/fonts/` to match the design (see README there); falls back to system fonts otherwise.
- PaddleOCR first run downloads model weights — bake into the image for fully air-gapped deploys.
