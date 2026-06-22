"""Ingestion endpoints (PRD §11): process-folder, process-zip, upload."""
import os

import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import active_session_id, resolve_llm
from app.config import get_settings
from app.db import get_db
from app.models import Job
from app.models.schemas import JobOut, ProcessFolderRequest, ProcessZipRequest
from app.workers.tasks import ingest_job

router = APIRouter(prefix="/api", tags=["process"])
settings = get_settings()


def _start(db: Session, source_type: str, path: str, llm) -> Job:
    provider, model = resolve_llm(db, llm)
    job = Job(source_type=source_type, source_path=path,
              llm_provider=provider, llm_model=model,
              session_id=active_session_id(db))
    db.add(job)
    db.commit()
    db.refresh(job)
    ingest_job.delay(job.id)
    return job


@router.post("/process-folder", response_model=JobOut)
def process_folder(req: ProcessFolderRequest, db: Session = Depends(get_db)):
    if not os.path.isdir(req.path):
        raise HTTPException(400, f"Folder not found: {req.path}")
    return _start(db, "folder", req.path, req.llm)


@router.post("/process-zip", response_model=JobOut)
def process_zip(req: ProcessZipRequest, db: Session = Depends(get_db)):
    if not os.path.isfile(req.path):
        raise HTTPException(400, f"ZIP not found: {req.path}")
    return _start(db, "zip", req.path, req.llm)


@router.post("/upload", response_model=JobOut)
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Drag-drop / ZIP upload. Saves to input storage then processes."""
    os.makedirs(settings.storage_input, exist_ok=True)
    dest = os.path.join(settings.storage_input, file.filename)
    with open(dest, "wb") as f:
        f.write(await file.read())
    source_type = "zip" if file.filename.lower().endswith(".zip") else "folder"
    # single file -> wrap in its own folder for the scanner
    if source_type == "folder":
        folder = os.path.join(settings.storage_input, os.path.splitext(file.filename)[0])
        os.makedirs(folder, exist_ok=True)
        os.replace(dest, os.path.join(folder, file.filename))
        return _start(db, "folder", folder, None)
    return _start(db, "zip", dest, None)


def _safe_dir(name: str) -> str:
    name = os.path.basename((name or "").strip().rstrip("/")) or "upload"
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


@router.post("/upload-folder", response_model=JobOut)
async def upload_folder(
    files: list[UploadFile] = File(...),
    folder_name: str = Form("upload"),
    db: Session = Depends(get_db),
):
    """Browser folder upload (webkitdirectory). All files = one person/job."""
    folder = os.path.join(settings.storage_input, _safe_dir(folder_name))
    os.makedirs(folder, exist_ok=True)
    saved = 0
    for f in files:
        base = os.path.basename(f.filename or "")
        if not base:
            continue
        with open(os.path.join(folder, base), "wb") as out:
            out.write(await f.read())
        saved += 1
    if saved == 0:
        raise HTTPException(400, "No files received")
    return _start(db, "folder", folder, None)
