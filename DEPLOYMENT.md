# Deployment Guide

Deploying the Document OCR & Extraction System to a server (mini VPS, on-prem, or Linux/Windows host).

See also: [README.md](README.md) · [DEVELOPMENT.md](DEVELOPMENT.md) · [PRD.md](PRD.md)

---

## 1. Topology

```
                 ┌─────────────┐
   browser ───▶  │  frontend   │  (nginx :80, serves SPA + proxies /api)
                 └──────┬──────┘
                        ▼
                 ┌─────────────┐      ┌──────────────┐
                 │     api     │◀────▶│  postgres    │
                 │ (FastAPI)   │      └──────────────┘
                 └──────┬──────┘      ┌──────────────┐
                        │             │    redis     │ (broker + result)
                        ▼             └──────┬───────┘
                 ┌─────────────┐             │
                 │   worker    │◀────────────┘
                 │  (Celery)   │   OCR + extraction
                 └──────┬──────┘
                        ▼  external OpenAI-compatible API (DeepSeek) — LLM extraction only
```

All services run via `docker-compose.yml`. OCR + rules are local; only OCR **text** leaves the host (LLM step), never raw documents. For full isolation, use the offline Ollama profile.

---

## 2. Minimum Hardware

| Mode | CPU | RAM | Disk |
|---|---|---|---|
| External LLM (default) | 2 vCPU | 4 GB | 10 GB | mini VPS OK — no GPU |
| Offline LLM (Ollama) | 4+ vCPU | 16+ GB (model dependent) | 20+ GB | GPU recommended |

PaddleOCR model weights (~a few hundred MB) download on first run — bake them into the image for air-gapped hosts (see §7).

---

## 3. Deploy Steps (Docker Compose)

```bash
git clone <repo> && cd ocr-auto-docs

cp backend/.env.example backend/.env
nano backend/.env          # set production values (see §4)

docker compose up --build -d
docker compose ps          # all services healthy/running
curl http://localhost:8000/health   # {"status":"ok"}
```

Update / redeploy:

```bash
git pull
docker compose up --build -d        # rebuilds changed images, recreates containers
```

Stop:

```bash
docker compose down                 # keep data
docker compose down -v              # DESTROY db + storage volumes
```

---

## 4. Configuration (`backend/.env`)

| Var | Prod guidance |
|---|---|
| `DATABASE_URL` | Strong password; managed Postgres if available |
| `REDIS_URL` | Add a password / private network in prod |
| `STORAGE_INPUT/OUTPUT/TEMP` | Keep on the mounted `storage` volume (`/data/...`) |
| `OCR_LANG` | `en` (latin) default; tune per documents |
| `OCR_MIN_CONFIDENCE` | Lower → more Tesseract fallback |
| `LLM_PROVIDER` / `LLM_MODEL` | Default provider; overridable in UI |
| `LLM_BASE_URL` | e.g. `https://api.deepseek.com/v1` |
| `LLM_API_KEY` | **Secret** — never commit; inject via secret manager |
| `LLM_TIMEOUT` | Raise for slow/large docs |
| `OPENAI_API_KEY`, `OLLAMA_BASE_URL` | Optional alt providers |

> `.env` is git-ignored. In production, inject secrets via your orchestrator's secret store (Docker secrets, K8s Secret, systemd `EnvironmentFile` with `chmod 600`), not a plaintext file in the repo.

---

## 5. Scaling

Throughput target (PRD): 100 docs < 10 min. Scale workers horizontally:

```bash
docker compose up -d --scale worker=4
```

- Each worker uses `--concurrency=2` (edit in `docker-compose.yml`). Concurrency is **RAM-bound, not CPU-bound**: each parallel OCR task loads its own PaddleOCR engine (~1.2–1.5 GB). Budget ~1.5 GB per unit of concurrency; raising it on a small VM causes OOM kills.
- Redis is the single broker — fine for one host. For multi-host, externalize Redis + Postgres.
- `worker_prefetch_multiplier=1` + `task_acks_late=True` already set for fair dispatch of long OCR tasks.

---

## 6. Reverse Proxy / TLS

The `frontend` container already runs nginx and proxies `/api` → `api:8000`. For public exposure, put a TLS-terminating proxy in front (Caddy / Traefik / nginx):

- Expose only the frontend (port 80/443). Keep `api` on the internal compose network.
- Remove the `api` `ports:` mapping from `docker-compose.yml` once the frontend proxy is the only entry.
- Add auth at the proxy (basic auth / SSO) — the app itself has **no auth** (trusted-network assumption). Tighten CORS in `backend/app/main.py` accordingly.

Example (Caddy):

```
ocr.example.com {
    reverse_proxy frontend:80
}
```

---

## 7. Offline / Air-Gapped Deployment

1. Use the offline LLM profile:

   ```bash
   docker compose --profile offline up -d --build
   docker compose exec ollama ollama pull qwen2.5
   ```
   Then set provider to `ollama` (Settings page or `LLM_PROVIDER=ollama`).

2. Pre-bake OCR weights into the backend image so no download is needed at runtime — add to `backend/Dockerfile`:

   ```dockerfile
   RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='en')"
   ```

3. Pre-pull/transfer all base images (`postgres`, `redis`, `nginx`, `ollama`) onto the host via `docker save` / `docker load`.

Result: zero outbound network at runtime.

---

## 8. Data & Storage

| Volume | Holds | Backup? |
|---|---|---|
| `pgdata` | Postgres (jobs, documents, results) | **Yes** |
| `storage` | `/data/{input,output,temp}` files + JSON | **Yes** (output) |
| `ollama` | local model weights | rebuildable |

Backup:

```bash
docker compose exec postgres pg_dump -U ocr ocr > backup_$(date +%F).sql
docker run --rm -v ocr-auto-docs_storage:/data -v "$PWD":/out alpine \
  tar czf /out/storage_$(date +%F).tgz /data
```

Retention: clear `/data/temp` and `/data/input` after successful processing per your policy (open question in the plan — decide before go-live).

---

## 9. Health & Monitoring

| Check | Command |
|---|---|
| API liveness | `curl http://host:8000/health` |
| DB metrics | `curl http://host:8000/api/metrics` |
| Service states | `docker compose ps` |
| Logs | `docker compose logs -f api worker` |
| Queue depth | `docker compose exec redis redis-cli llen celery` |

Audit logging (PRD §5): every external LLM call is logged in worker output — ship `docker compose logs` to your log aggregator.

---

## 10. Windows Hosts

Works via Docker Desktop (WSL2 backend). Same `docker compose up --build`. Use WSL2 paths for any host-mounted folders. For native (non-Docker) Windows, install Tesseract for Windows and set its path; Docker is strongly recommended instead.

---

## 11. Production Hardening Checklist

- [ ] Replace `create_all` with Alembic migrations
- [ ] Secrets via secret manager, not `.env` in repo
- [ ] Strong Postgres + Redis credentials, private network
- [ ] Add auth at reverse proxy; tighten CORS allow-origins
- [ ] TLS via reverse proxy
- [ ] Remove public `api` port mapping (proxy-only)
- [ ] Backups scheduled (pg_dump + storage)
- [ ] Decide data-retention purge policy for temp/input
- [ ] Bake OCR weights into image for fast/offline cold start
- [ ] Set worker count + concurrency to host vCPUs
