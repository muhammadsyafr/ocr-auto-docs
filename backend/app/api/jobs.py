"""Jobs endpoints (PRD §11): list jobs, dashboard metrics, stop/remove."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import active_session_id
from app.db import get_db
from app.models import Document, Job
from app.models.schemas import JobOut

router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    sid = active_session_id(db)
    return (
        db.query(Job)
        .filter(Job.session_id == sid)
        .order_by(Job.created_at.desc())
        .all()
    )


@router.post("/jobs/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Stop a job: queued docs are cancelled; in-flight tasks short-circuit
    at their next start (cooperative). Already-finished docs are kept."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job.status = "cancelled"
    for d in job.documents:
        if d.status in ("queued", "processing"):
            d.status = "cancelled"
    db.commit()
    db.refresh(job)
    return job


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Remove a job and all its documents + extraction results."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    # Mark cancelled first so any queued tasks short-circuit before we delete
    job.status = "cancelled"
    for d in job.documents:
        if d.status in ("queued", "processing"):
            d.status = "cancelled"
    db.commit()
    db.delete(job)   # cascades to documents + extraction_results
    db.commit()
    return {"deleted": job_id}


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    """Dashboard metrics (PRD §14), scoped to the active session."""
    sid = active_session_id(db)
    q = db.query(Document).join(Job, Document.job_id == Job.id).filter(Job.session_id == sid)
    return {
        "total": q.count(),
        "successful": q.filter(Document.status == "completed").count(),
        "failed": q.filter(Document.status == "failed").count(),
        "processing": q.filter(Document.status.in_(["queued", "processing"])).count(),
    }
