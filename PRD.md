# PRD - Document OCR & Extraction System

**Version:** 1.1
**Status:** Draft
**Last Updated:** 2026-06-22

---

# 1. Overview

The Document OCR & Extraction System is a locally deployed (offline/on-premise) application designed to process PDF and image-based documents, extract key information, and generate structured JSON outputs.

The system is intended for HR operations, employee onboarding, background verification, document digitization, and enterprise document processing workflows.

## Supported Document Types

### National ID Card (KTP)

Extracted Fields:

* National ID Number (NIK)
* Full Name
* Place of Birth
* Date of Birth

### Academic Certificate (Ijazah)

Supported Levels:

* Elementary School (SD)
* Junior High School (SLTP)
* Senior High School (SLTA)
* Diploma 3 (D3)
* Diploma 4 (D4)
* Bachelor Degree (S1)
* Master Degree (S2)

Extracted Fields:

* Certificate Number
* Full Name
* Place of Birth
* Date of Birth

### Employment Certificate

Extracted Fields:

* Company Name
* Company Address

---

# 2. Business Goals

The primary objectives of the system are:

1. Eliminate manual document data entry.
2. Increase extraction accuracy.
3. Support batch document processing.
4. Produce structured JSON outputs for downstream systems.
5. Run OCR and rule-based extraction fully offline; LLM-based extraction may call an external API (see §7) so the system runs on low-resource hosts (mini VPS, no GPU).

---

# 3. Scope

## In Scope

* PDF OCR
* Image OCR
* Batch Processing
* Folder Processing
* ZIP Processing
* JSON Export
* Document Classification
* Confidence Scoring
* Validation Engine
* Frontend Monitoring Dashboard

## Out of Scope (Phase 1)

* Face Recognition
* QR Code Verification
* Government Identity Validation
* Academic Database Verification
* Digital Signature Verification
* Handwriting Recognition

---

# 4. Functional Requirements

## FR-001 Folder Processing

Users can specify a local folder as an input source.

Example:

```bash
process --input ./documents
```

---

## FR-002 ZIP Processing

Users can process ZIP archives containing multiple documents.

Example:

```bash
process --zip ./documents.zip
```

---

## FR-003 Supported Formats

### Input Formats

* PDF
* JPG
* JPEG
* PNG
* TIFF
* BMP

---

## FR-004 OCR Processing

The system shall perform OCR on all pages of supported documents.

---

## FR-005 Document Classification

The system shall automatically classify documents into one of the following categories:

* ktp
* academic_certificate
* employment_certificate

Example:

```json
{
  "document_type": "academic_certificate"
}
```

---

## FR-006 KTP Extraction

Required fields:

```json
{
  "nik": "3174123456789012",
  "full_name": "John Doe",
  "place_of_birth": "Jakarta",
  "date_of_birth": "1990-10-10"
}
```

---

## FR-007 Academic Certificate Extraction

Required fields:

```json
{
  "certificate_number": "DN-01 MA 0000001",
  "full_name": "John Doe",
  "place_of_birth": "Jakarta",
  "date_of_birth": "1990-10-10"
}
```

---

## FR-008 Employment Certificate Extraction

Required fields:

```json
{
  "company_name": "ABC Indonesia Ltd.",
  "company_address": "Jl. Sudirman No. 10 Jakarta"
}
```

---

## FR-009 Confidence Score

Each extracted field shall include a confidence score.

Example:

```json
{
  "nik": {
    "value": "3174123456789012",
    "confidence": 0.98
  }
}
```

---

## FR-010 Validation

### NIK Validation

Regex:

```regex
^\d{16}$
```

### Date Validation

Accepted formats:

```text
10-10-1990
10/10/1990
1990-10-10
```

Standardized output:

```text
1990-10-10
```

---

## FR-011 Batch Processing

The system shall support processing at least:

```text
100 documents per batch
```

---

## FR-012 JSON Export

The system shall generate JSON output files for each processed document.

---

## FR-013 LLM Provider Selection

Users can select the LLM provider and model from the frontend (no redeploy required).

* The backend exposes the list of configured providers and their available models.
* Users pick provider + model in a Settings page; selection is persisted as the system default.
* Users may also override provider/model per processing job at upload time.
* API key is configured server-side (env / secret), never entered or exposed in the frontend.
* "Offline (local Ollama)" appears as a selectable provider when configured.

Example — list providers:

```http
GET /api/llm/providers
```

```json
{
  "active": { "provider": "deepseek", "model": "deepseek-chat" },
  "providers": [
    { "provider": "deepseek", "models": ["deepseek-chat", "deepseek-reasoner"], "configured": true },
    { "provider": "openai", "models": ["gpt-4o-mini"], "configured": false },
    { "provider": "ollama", "models": ["qwen2.5", "minicpm-v"], "configured": true, "offline": true }
  ]
}
```

Example — set default:

```http
PUT /api/settings/llm
```

```json
{
  "provider": "deepseek",
  "model": "deepseek-chat"
}
```

---

# 5. Non-Functional Requirements

## Performance

### OCR Processing

Target:

```text
≤ 5 seconds per page
```

### Batch Processing

Target:

```text
100 documents in less than 10 minutes
```

---

## Availability

* Low-resource host support (mini VPS, no GPU required)
* Offline OCR + rule-based extraction; LLM extraction via external API (or local Ollama when offline mode required)
* Docker Deployment
* Linux Support
* Windows Support

---

## Scalability

* Multi-worker processing
* Queue-based architecture

---

## Security

* OCR and rule-based extraction performed fully locally — no external transmission
* LLM-based extraction (academic & employment certificates) sends OCR text to an external LLM API; only extracted text is sent, never raw document files
* Optional fully-offline mode: switch LLM provider to local (Ollama) to keep all processing on-host
* Configurable provider via environment (base_url + api_key)
* Audit logging available — every external API call is logged

---

# 6. Architecture

```text
Folder / ZIP Input
        │
        ▼
   File Scanner
        │
        ▼
 PDF Converter
        │
        ▼
 OCR Engine
        │
        ▼
Document Classifier
        │
        ▼
Extraction Engine
        │
        ▼
Validation Engine
        │
        ▼
 JSON Generator
        │
        ▼
 Output Folder
```

---

# 7. OCR Strategy

## OCR Engine Priority

### Primary OCR Engine

PaddleOCR

Benefits:

* High OCR accuracy
* Strong Indonesian language support
* Fast processing
* Fully offline

---

### Secondary OCR Engine

Tesseract OCR

Used as fallback.

---

### AI Extraction Engine

For semi-structured and unstructured documents, the system calls an external LLM via an **OpenAI-compatible API** (chat completions). This avoids running heavy VLMs locally, so the app runs on a mini VPS with no GPU.

Input to the LLM is the **OCR text** produced by PaddleOCR/Tesseract (text-in, JSON-out) — raw document images are not transmitted.

**Default provider:** DeepSeek (`deepseek-v4-flash`; `deepseek-v4-pro` for higher accuracy)

**Compatible providers (swap via `base_url` + `api_key`):**

* DeepSeek
* OpenAI
* Together / Groq / OpenRouter
* Any OpenAI-compatible endpoint

**Optional local fallback (fully offline):** Ollama serving Qwen2.5 / MiniCPM, selected by config when on-prem isolation is required.

Configuration (environment):

```text
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=deepseek-v4-flash
LLM_PROVIDER=deepseek   # deepseek | openai | ollama | custom
```

---

# 8. Extraction Strategy

## KTP

Methods:

* OCR
* Regex
* Rule-Based Parsing

Keywords:

```text
NIK
Name
Place/Date of Birth
```

Regex:

```regex
\d{16}
```

---

## Academic Certificate

Methods:

* OCR
* Footer Detection
* Pattern Matching
* LLM-Based Extraction

### Target Fields

```json
{
  "certificate_number": "",
  "full_name": "",
  "place_of_birth": "",
  "date_of_birth": ""
}
```

---

### Footer Region Priority

Most Indonesian academic certificates place the certificate number near the footer.

Priority OCR Regions:

```text
TOP AREA
- Full Name

MIDDLE AREA
- Place of Birth
- Date of Birth

BOTTOM AREA
- Certificate Number
```

---

### Common Certificate Number Formats

```text
DN-01 MA 0000001
DN-01 DI 1234567
M-SMA/13/123456
0123456789
```

---

### Footer Keywords

```text
Certificate Number
Number
No.
Serial Number
STTB
```

---

### LLM Prompt

```text
Extract:

1. Certificate Number
2. Full Name
3. Place of Birth
4. Date of Birth

Return valid JSON only.
```

---

## Employment Certificate

Methods:

* OCR
* Named Entity Recognition (NER)
* LLM Extraction

### Target Fields

```json
{
  "company_name": "",
  "company_address": ""
}
```

---

### LLM Prompt

```text
Identify:

1. Company Name
2. Company Address

Return valid JSON only.
```

---

# 9. Standard Output Schema

## Unified JSON Schema

```json
{
  "file_name": "document.pdf",
  "document_type": "academic_certificate",
  "confidence": 0.96,
  "fields": {
    "nik": null,
    "full_name": "John Doe",
    "certificate_number": "DN-01 MA 0000001",
    "place_of_birth": "Jakarta",
    "date_of_birth": "1990-10-10",
    "company_name": null,
    "company_address": null
  }
}
```

---

## Confidence Schema

```json
{
  "certificate_number": {
    "value": "DN-01 MA 0000001",
    "confidence": 0.97
  }
}
```

---

# 10. Batch Summary Output

```json
{
  "total_files": 100,
  "successful": 95,
  "failed": 5,
  "generated_at": "2026-06-22T10:00:00Z"
}
```

---

# 11. Backend PRD

## Technology Stack

```text
FastAPI
PaddleOCR
PyMuPDF
OpenCV
PostgreSQL
Redis
Celery
Docker
```

---

## Backend Folder Structure

```text
backend/
├── app
│   ├── api
│   ├── services
│   ├── extractors
│   ├── validators
│   ├── classifiers
│   ├── workers
│   └── models
│
├── storage
│   ├── input
│   ├── output
│   └── temp
│
└── docker
```

---

## REST APIs

### Process Folder

```http
POST /api/process-folder
```

Request:

```json
{
  "path": "/documents/input"
}
```

---

### Process ZIP

```http
POST /api/process-zip
```

Request:

```json
{
  "path": "/documents/batch.zip"
}
```

---

### Get Jobs

```http
GET /api/jobs
```

---

### Get Results

```http
GET /api/results
```

---

### Get Result Details

```http
GET /api/results/{id}
```

---

### Export JSON

```http
GET /api/export/json
```

---

### List LLM Providers

```http
GET /api/llm/providers
```

---

### Set Default LLM

```http
PUT /api/settings/llm
```

Request:

```json
{
  "provider": "deepseek",
  "model": "deepseek-chat"
}
```

---

### Process with LLM override

`POST /api/process-folder` and `POST /api/process-zip` accept an optional `llm` object to override the default for that job:

```json
{
  "path": "/documents/input",
  "llm": { "provider": "deepseek", "model": "deepseek-chat" }
}
```

---

# 12. Database Design

## documents

| Field         | Type      |
| ------------- | --------- |
| id            | UUID      |
| filename      | TEXT      |
| document_type | TEXT      |
| status        | TEXT      |
| created_at    | TIMESTAMP |

---

## extraction_results

| Field       | Type  |
| ----------- | ----- |
| id          | UUID  |
| document_id | UUID  |
| field_name  | TEXT  |
| field_value | TEXT  |
| confidence  | FLOAT |

---

# 13. Frontend PRD

## Technology Stack

```text
React 19
TanStack Router
TanStack Query
TanStack Table
TanStack Form
TailwindCSS
Shadcn UI
Zustand
```

## Design System

Frontend follows the **Coral Stay** design system — see [DESIGN.md](DESIGN.md).

* Tokens (colors, typography, spacing, radius, elevation) implemented as Tailwind theme + CSS variables; Shadcn components themed to match.
* Fonts: Nunito Sans (display), DM Sans (body), JetBrains Mono (code/JSON) — self-hosted (no Google Fonts CDN call, keeps offline-friendly).
* Accent coral `#FF5A5F` reserved for primary CTAs only (Start Processing, primary actions). Text `#222222`, never pure black.
* Status colors map to job states: Success `#008A05` (Completed), Warning `#E07912` (Processing), Error `#C13515` (Failed), Neutral `#767676` (Queued).
* Confidence scores rendered with semantic color (high=Success, mid=Warning, low=Error).
* Cards: image/preview-top, content-bottom, 12px radius, Level 1→2 shadow on hover.

---

# 14. Frontend Pages

## Dashboard

Metrics:

* Total Documents
* Successful
* Failed
* Processing

---

## Upload Page

Features:

* ZIP Upload
* Drag & Drop Upload
* Folder Path Input
* LLM provider + model selector (defaults to system default; optional per-job override)
* Start Processing

---

## Settings Page

Features:

* List configured LLM providers + available models (`GET /api/llm/providers`)
* Select default provider + model (`PUT /api/settings/llm`)
* Show which providers are configured / offline-capable
* API keys are not shown or edited here (server-side secret)

---

## Job Monitoring

Polling Interval:

```text
3 seconds
```

Statuses:

* Queued
* Processing
* Completed
* Failed

Table:

| File    | Type | Status    |
| ------- | ---- | --------- |
| ktp.jpg | KTP  | Completed |

---

## Results Page

| File | Type | NIK | Full Name | Certificate Number |
| ---- | ---- | --- | --------- | ------------------ |

---

## Result Details Page

### Document Preview

* PDF Viewer
* Image Viewer

### Extracted Data

```json
{
  "certificate_number": "DN-01 MA 0000001",
  "full_name": "John Doe",
  "place_of_birth": "Jakarta",
  "date_of_birth": "1990-10-10"
}
```

### Confidence Scores

```text
Certificate Number = 97%
Full Name = 99%
Place of Birth = 95%
Date of Birth = 94%
```

---

# 15. Frontend Structure

```text
frontend/
├── src
│
├── routes
│   ├── dashboard
│   ├── upload
│   ├── jobs
│   ├── results
│   ├── detail
│   └── settings
│
├── features
│   ├── upload
│   ├── jobs
│   └── extraction
│
├── services
│   └── api.ts
│
├── components
│   ├── tables
│   ├── viewers
│   └── cards
│
├── hooks
├── store
└── types
```

---

# 16. Recommended MVP

## Backend

```text
FastAPI
PaddleOCR
PyMuPDF
OpenCV
PostgreSQL
Redis
Celery
Docker
```

## Frontend

```text
React
TanStack Router
TanStack Query
TanStack Table
TailwindCSS
Shadcn UI
```

## Processing Flow

```text
Folder / ZIP
      │
      ▼
PDF / Image
      │
      ▼
PaddleOCR
      │
      ▼
Document Classification
      │
      ▼
Rule-Based Extraction (KTP)
      │
      ▼
LLM Extraction (Certificates & Employment Letters)
      │
      ▼
Validation
      │
      ▼
JSON Output
      │
      ▼
Frontend Viewer
```

# Success Criteria

### KTP

* Accuracy ≥ 95%

### Academic Certificate

* Accuracy ≥ 90%

### Employment Certificate

* Accuracy ≥ 85%

### JSON Output

* 100% valid JSON

### Batch Processing

* Minimum 100 documents per batch
