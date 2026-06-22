"""FastAPI entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import doc, export, jobs, llm, process, results, sessions
from app.db import init_db
from app.services import storage

app = FastAPI(title="Document OCR & Extraction System", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # trusted-network deployment; tighten if auth added
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()
    storage.ensure_dirs()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(process.router)
app.include_router(jobs.router)
app.include_router(results.router)
app.include_router(export.router)
app.include_router(llm.router)
app.include_router(doc.router)
app.include_router(sessions.router)
