# Docker Cheatsheet — ocr-auto-docs

Quick command reference for running this project with Docker Compose.
Run all commands from the project root (where `docker-compose.yml` lives).

See also: [DEVELOPMENT.md](DEVELOPMENT.md) · [DEPLOYMENT.md](DEPLOYMENT.md) · [README.md](README.md)

---

## Services

| Service | Role | Port |
|---|---|---|
| `frontend` | React SPA + nginx (proxies `/api`) | 5173 → 80 |
| `api` | FastAPI | 8000 |
| `worker` | Celery — OCR + extraction | — |
| `postgres` | DB (jobs, documents, results) | internal |
| `redis` | Celery broker + result backend | internal |
| `ollama` | offline LLM (opt-in `--profile offline`) | 11434 |

**URLs:** frontend http://localhost:5173 · API docs http://localhost:8000/docs · health http://localhost:8000/health

---

## Lifecycle

```bash
docker compose up --build -d        # build + start all (detached)
docker compose up -d                 # start (no rebuild)
docker compose stop                  # stop, keep containers
docker compose start                 # restart stopped containers
docker compose down                  # stop + remove containers
docker compose down -v               # + WIPE db & storage volumes (full reset)
docker compose restart api worker    # restart specific services
```

---

## Dev Mode (hot reload, no rebuild)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up        # foreground
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d     # detached
```

- **api** — `uvicorn --reload`, source mounted → reloads on `.py` save
- **worker** — `watchmedo` restarts Celery on `.py` save
- **frontend** — Vite dev server (HMR) on :5173, proxies `/api` → `api:8000`

Code edits apply live. Rebuild still needed only when `requirements.txt`,
`package.json`, or a `Dockerfile` changes. Plain prod run = `docker compose up --build -d`.

Tip: shorten the dev command with an alias —

```bash
alias dcdev='docker compose -f docker-compose.yml -f docker-compose.dev.yml'
dcdev up -d && dcdev logs -f api
```

---

## Status + Logs

```bash
docker compose ps                    # service states
docker compose logs -f api           # follow API logs
docker compose logs -f worker        # follow OCR pipeline / Celery
docker compose logs --tail=100 api worker
curl http://localhost:8000/health    # {"status":"ok"}
curl http://localhost:8000/api/metrics
```

---

## Rebuild After Code Change

```bash
docker compose up --build -d api worker   # rebuild backend only
docker compose up --build -d frontend     # rebuild frontend only
docker compose build --no-cache api       # force clean rebuild (ignore cache)
```

---

## Scale Workers (throughput)

```bash
docker compose up -d --scale worker=4     # 4 OCR workers in parallel
```

Concurrency per worker is set in `docker-compose.yml` (`--concurrency=2`). It's **RAM-bound**: each parallel OCR task loads its own PaddleOCR engine (~1.2–1.5 GB). Budget ~1.5 GB per unit; too high → OOM kills (a 4-doc batch at concurrency=4 can exhaust an 8 GB VM).

---

## Shell / DB / Queue Access

```bash
docker compose exec api bash                       # shell in API container
docker compose exec worker bash                    # shell in worker
docker compose exec postgres psql -U ocr -d ocr    # DB console
docker compose exec redis redis-cli llen celery    # pending queue depth
```

---

## Offline LLM Profile (Ollama)

```bash
docker compose --profile offline up -d --build
docker compose exec ollama ollama pull qwen2.5     # pull a model once
# then Settings page -> select provider "ollama"
```

---

## Trigger a Job (test the pipeline)

```bash
# Folder already inside the storage volume (/data/input)
curl -X POST http://localhost:8000/api/process-folder \
  -H 'Content-Type: application/json' -d '{"path":"/data/input"}'

# With LLM override
curl -X POST http://localhost:8000/api/process-folder \
  -H 'Content-Type: application/json' \
  -d '{"path":"/data/input","llm":{"provider":"deepseek","model":"deepseek-v4-flash"}}'

curl http://localhost:8000/api/jobs          # watch status
curl http://localhost:8000/api/results       # extracted docs
curl http://localhost:8000/api/export/json   # full export + batch summary
```

Copy files into the input volume:

```bash
docker compose cp ./samples/. api:/data/input/
```

---

## Backup / Restore

```bash
# DB
docker compose exec postgres pg_dump -U ocr ocr > backup.sql
cat backup.sql | docker compose exec -T postgres psql -U ocr -d ocr   # restore

# Storage files
docker run --rm -v ocr-auto-docs_storage:/data -v "$PWD":/out alpine \
  tar czf /out/storage.tgz /data
```

---

## Cleanup (free disk)

```bash
docker compose down --rmi local      # remove this project's built images
docker compose down -v               # remove volumes (DATA LOSS)
docker system prune -f               # remove dangling images/build cache (global)
docker builder prune -f              # clear build cache only
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Cannot connect to the Docker daemon` | Start Docker/OrbStack: `open -a OrbStack`, wait for `docker info` |
| Backend build slow / stuck | `paddlepaddle` wheel is large — first build only; it caches |
| First OCR very slow | PaddleOCR downloads model weights on first run |
| Extraction fields all null | LLM key missing/invalid → `docker compose logs api`; falls back to rules |
| `Folder not found` on process | Path must be inside container (`/data/input`), not a host path |
| Port already in use | Change host port in `docker-compose.yml` `ports:` |
| Reset everything | `docker compose down -v && docker compose up --build -d` |
