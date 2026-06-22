# Implementation Plan — Document OCR & Extraction System

**Source:** [PRD.md](PRD.md) v1.1
**Created:** 2026-06-22

---

## 1. Guiding Principles

- **Local OCR, cloud LLM (hybrid).** OCR + rule-based extraction run fully local. LLM extraction calls an external OpenAI-compatible API (default DeepSeek) so the app runs on a mini VPS with no GPU. Only OCR *text* is sent, never raw files. Fully-offline mode available by switching provider to local Ollama.
- **Vertical slices.** Ship one end-to-end path (upload KTP → OCR → classify → extract → JSON → view) before breadth. Proves the pipeline early.
- **Schema is the contract.** The unified JSON schema (PRD §9) is frozen first; backend and frontend code against it.
- **Async by default.** Ingestion returns a job ID immediately; Celery workers process; frontend polls.

---

## 2. Tech Stack (locked from PRD)

| Layer | Choice |
|---|---|
| API | FastAPI |
| OCR primary | PaddleOCR |
| OCR fallback | Tesseract |
| PDF/Image | PyMuPDF, OpenCV |
| LLM extraction | External OpenAI-compatible API — default DeepSeek (`deepseek-chat`); base_url/api_key/model swappable. Local Ollama optional for offline mode |
| Queue | Celery + Redis |
| DB | PostgreSQL |
| Deploy | Docker Compose |
| Frontend | React 19, TanStack Router/Query/Table/Form, Tailwind, Shadcn, Zustand |

---

## 3. Architecture Decisions (gaps PRD leaves open)

1. **LLM serving.** Decision: **external OpenAI-compatible API**, default **DeepSeek** — mini VPS can't run local VLMs (RAM/GPU). `LLMClient` interface wraps the OpenAI SDK pointed at `LLM_BASE_URL`; works for DeepSeek/OpenAI/Together/Groq/OpenRouter and local Ollama (offline mode) with no code change. Text-in (OCR output), JSON-out. Retry + timeout + fallback to rule-only on API failure.
   - **Provider registry + frontend selection.** A server-side registry maps each configured provider → base_url, models, api_key (from env/secret), offline flag. Frontend lists it via `GET /api/llm/providers` and sets the default via `PUT /api/settings/llm`; per-job override flows through the process endpoints onto the job row. `LLMClient` is constructed per-task from the chosen provider+model. API keys never leave the server.
2. **File storage.** Local filesystem under `storage/{input,output,temp}` (per PRD folder layout). DB stores paths + metadata, not blobs.
3. **Job model.** A "job" = one folder/ZIP submission. A job has N documents. Add a `jobs` table (PRD §12 only defines `documents` + `extraction_results` — gap).
4. **Classification.** Rule-based keyword/regex classifier first (cheap, offline). LLM zero-shot fallback when confidence low.
5. **Confidence.** OCR confidence from PaddleOCR per-line scores; field confidence = aggregate of source tokens. LLM-extracted fields get a fixed prior unless model returns logprobs.

---

## 4. Workstreams & Phases

### Phase 0 — Foundations (scaffold)
- Repo layout: `backend/`, `frontend/`, `docker/`, root `docker-compose.yml`.
- Backend: FastAPI skeleton, settings (pydantic-settings), health endpoint.
- DB: Postgres + Alembic, migrations for `jobs`, `documents`, `extraction_results`.
- Redis + Celery wiring, a no-op task proving the queue round-trips.
- Docker Compose: api, worker, postgres, redis. (No local LLM — uses external API; Ollama added only as opt-in profile for offline mode.) Single `docker compose up`.
- Frontend: Vite + React 19 + Tailwind + Shadcn init, TanStack Router shell, base layout.
- **Design system (Coral Stay, see [DESIGN.md](DESIGN.md)):** encode tokens into `tailwind.config` + CSS variables — colors (coral `#FF5A5F` primary, `#222222` text, status palette), spacing scale (8px base), radius (4/8/12/16/9999), Level 1–3 shadows. Self-host Nunito Sans / DM Sans / JetBrains Mono (no CDN — offline-friendly). Theme Shadcn primitives (button/card/input/badge) to the system. Build a small primitives showcase to lock the look before pages.

**Exit:** `docker compose up` serves API + empty dashboard; Celery task runs.

### Phase 1 — Ingestion & OCR core
- `POST /api/process-folder`, `POST /api/process-zip` → create job + document rows, enqueue tasks.
- File scanner: walk folder / unzip, filter by supported formats (PDF, JPG, JPEG, PNG, TIFF, BMP).
- PDF converter (PyMuPDF): PDF pages → images.
- OpenCV preprocessing: deskew, denoise, threshold.
- OCR service: PaddleOCR primary, Tesseract fallback on low confidence or failure.
- Per-page OCR result persisted (text + boxes + confidence).

**Exit:** Submit a folder of images, get OCR text + confidence stored per document.

### Phase 2 — Classification & Extraction
- **Classifier:** keyword/regex rules → `ktp | academic_certificate | employment_certificate`. LLM fallback.
- **KTP extractor:** regex + rule-based (NIK `^\d{16}$`, name/POB/DOB by label proximity).
- **Academic extractor:** footer-region OCR priority + pattern matching for cert-number formats + LLM extraction. Prompt from PRD §8.
- **Employment extractor:** LLM extraction (company name + address). Prompt from PRD §8.
- **Validation engine:** NIK regex, date normalization (`DD-MM-YYYY`/`DD/MM/YYYY`/`YYYY-MM-DD` → `YYYY-MM-DD`).
- **JSON generator:** emit unified schema (§9) per document; write to `storage/output`; persist fields + confidence to `extraction_results`.

**Exit:** Each doc type produces valid unified JSON with per-field confidence.

### Phase 3 — Read APIs & Batch summary
- `GET /api/jobs`, `GET /api/results`, `GET /api/results/{id}`, `GET /api/export/json`.
- `GET /api/llm/providers` (list configured providers + models + active), `PUT /api/settings/llm` (set default).
- `process-folder`/`process-zip` accept optional `llm` override object; stored on the job and passed to the extractor task.
- Batch summary output (§10): total/successful/failed/generated_at.
- Serve original file for preview (download endpoint).

**Exit:** All PRD REST endpoints live and returning schema-valid payloads.

### Phase 4 — Frontend

All pages built on the Coral Stay tokens/components from Phase 0. Conventions: status→color (Completed=Success green, Processing=Warning orange, Failed=Error red, Queued=Neutral gray); confidence→color (high green / mid orange / low red); coral reserved for primary CTAs; cards image/preview-top + content-bottom, hover lift Level 1→2; JSON shown in JetBrains Mono.

- **Dashboard:** metric cards (total/successful/failed/processing) via TanStack Query, Coral Stay card style.
- **Upload:** ZIP upload + drag-drop + folder path input + LLM provider/model selector (per-job override) + start processing.
- **Settings:** LLM provider + model picker (lists `GET /api/llm/providers`, saves via `PUT /api/settings/llm`); shows configured/offline flags. No API-key entry (server-side secret).
- **Job Monitoring:** TanStack Table, 3s polling, status badges colored per convention (Queued/Processing/Completed/Failed).
- **Results:** table (File/Type/NIK/Name/Cert#).
- **Result Details:** PDF/image viewer + extracted data + confidence scores (color-coded); JSON in mono.
- **Settings:** LLM provider/model picker (see Phase 3), Coral Stay form styling.
- Zustand for UI state; `services/api.ts` typed client matching schema.

**Exit:** Full upload → monitor → results → detail flow in browser.

### Phase 5 — NFR hardening
- Performance: OCR ≤5s/page, 100 docs <10min. Profile, tune worker concurrency.
- Multi-worker Celery scaling; queue backpressure.
- Audit logging (structured logs of every process step).
- Accuracy harness: labeled fixture set, measure vs success criteria (KTP ≥95%, academic ≥90%, employment ≥85%, 100% valid JSON).
- Windows + Linux Docker verification.

**Exit:** Success criteria (PRD §16) measured and met.

---

## 5. Backend Layout (per PRD §11)

```
backend/app/
├── api/          # routers: process, jobs, results, export
├── services/     # scanner, pdf_converter, ocr, storage
├── extractors/   # ktp, academic, employment
├── validators/   # nik, date
├── classifiers/  # rule_based, llm_fallback
├── workers/      # celery tasks
└── models/       # SQLAlchemy + pydantic schemas
```

LLM client lives in `services/llm.py` behind an interface.

---

## 6. Data Model (extends PRD §12)

- **jobs** (new): `id UUID, source_type TEXT, source_path TEXT, status TEXT, total INT, successful INT, failed INT, llm_provider TEXT, llm_model TEXT, created_at, completed_at` (provider/model = per-job override or resolved default)
- **settings** (new, single-row or key/value): stores default `llm_provider`, `llm_model`. Provider list + keys come from env/registry, not this table.
- **documents:** add `job_id UUID FK`, `confidence FLOAT`, `output_path TEXT` to PRD fields.
- **extraction_results:** as PRD (`id, document_id, field_name, field_value, confidence`).

---

## 7. Key Risks

| Risk | Mitigation |
|---|---|
| External LLM API: cost / rate limits / downtime | Retry+timeout; cache by OCR-text hash; fall back to rule-only extraction; log every call |
| Data leaves host (privacy) | Send only OCR text, never raw files; offline mode (Ollama) for sensitive deployments; document in security review |
| PaddleOCR install pain (deps) | Pin versions, bake into Docker image |
| Indonesian cert format variance | Footer-region priority + multiple regex patterns + LLM fallback |
| 5s/page on CPU-only hosts | GPU optional; degrade gracefully, surface in audit log |
| Accuracy targets unmet | Build labeled fixture harness early (Phase 2), iterate prompts/rules |

---

## 8. Open Questions for Stakeholders

1. Which external LLM account/budget? (DeepSeek key provisioned? monthly token cap?)
2. Any document types too sensitive to send to external API → require offline Ollama path?
3. Expected peak batch size beyond 100 (sizing workers/Redis + API rate limits)?
4. Auth needed on the dashboard, or trusted-network only?
5. Data retention — purge `temp`/`input` after processing?

---

## 9. Suggested Build Order (first 2 weeks)

1. Phase 0 scaffold + Compose.
2. Frozen unified-schema pydantic models + JSON-schema test.
3. KTP vertical slice (ingest → OCR → rule extract → JSON → results table). Proves pipeline.
4. Add academic + employment extractors.
5. Frontend monitoring + detail.
6. NFR/accuracy harness.
