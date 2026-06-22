"""Celery tasks: ingest a job, process each document."""
import logging
import os
from datetime import datetime

from app.db import SessionLocal
from app.models import Document, Job
from app.pipeline import process_document
from app.services import scanner, storage
from app.services.llm import LLMClient
from app.workers.celery_app import celery_app

log = logging.getLogger("ocr.worker")


def _build_llm(provider: str | None, model: str | None) -> LLMClient | None:
    if not provider or not model:
        return None
    try:
        return LLMClient(provider, model)
    except Exception as e:  # misconfigured provider -> rule-only degrade
        log.warning("LLM disabled: %s", e)
        return None


@celery_app.task(name="ingest_job")
def ingest_job(job_id: str):
    """Expand a job's source into Document rows + queue per-doc processing."""
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if not job:
            return
        job.status = "processing"
        db.commit()

        if job.source_type == "zip":
            dest = os.path.join(storage.settings.storage_temp, job.id)
            files = scanner.extract_zip(job.source_path, dest)
        else:
            files = scanner.scan_folder(job.source_path)

        job.total = len(files)
        db.commit()

        for path in files:
            doc = Document(job_id=job.id, filename=os.path.basename(path),
                           source_path=path, status="queued")
            db.add(doc)
            db.commit()
            process_document_task.delay(doc.id)

        if not files:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


@celery_app.task(name="process_document", bind=True, max_retries=2, default_retry_delay=10)
def process_document_task(self, document_id: str):
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return
        job = db.get(Job, doc.job_id)
        # Cooperative cancellation: a stopped/removed job short-circuits queued
        # tasks instead of running expensive OCR.
        if doc.status == "cancelled" or (job and job.status == "cancelled"):
            doc.status = "cancelled"
            db.commit()
            return
        doc.status = "processing"
        db.commit()
        llm = _build_llm(job.llm_provider, job.llm_model)

        result = process_document(doc.source_path, llm)

        doc.document_type = result["document_type"]
        doc.confidence = result["confidence"]
        payload = {
            "file_name": doc.filename,
            "document_type": result["document_type"],
            "confidence": result["confidence"],
            "fields": result["fields"],
        }
        doc.output_path = storage.write_output_json(doc.filename, payload)

        # Persist per-field results
        from app.models import ExtractionResult
        for name, value in result["fields"].items():
            db.add(ExtractionResult(
                document_id=doc.id, field_name=name, field_value=value,
                confidence=result["field_confidence"].get(name),
            ))
        doc.status = "completed"
        db.commit()
    except Exception as e:
        log.exception("doc %s failed", document_id)
        doc = db.get(Document, document_id)
        if doc:
            doc.status = "failed"
            doc.error = str(e)[:500]
            db.commit()
    finally:
        _finalize_job(db, document_id)
        db.close()


def _finalize_job(db, document_id: str):
    doc = db.get(Document, document_id)
    if not doc:
        return
    job = db.get(Job, doc.job_id)
    if not job:
        return
    if job.status == "cancelled":
        return  # don't flip a stopped job back to completed
    done = [d for d in job.documents if d.status in ("completed", "failed", "cancelled")]
    if len(done) >= job.total and job.total > 0:
        job.successful = sum(1 for d in job.documents if d.status == "completed")
        job.failed = sum(1 for d in job.documents if d.status == "failed")
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
