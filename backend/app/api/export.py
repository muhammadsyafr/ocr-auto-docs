"""Export endpoint (PRD §11 + §10 batch summary)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document
from app.models.schemas import BatchSummary

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export/json")
def export_json(db: Session = Depends(get_db)):
    """Return all results as unified-schema JSON + batch summary (PRD §10)."""
    docs = db.query(Document).all()
    items = []
    for d in docs:
        fields = {r.field_name: r.field_value for r in d.results}
        items.append({
            "file_name": d.filename,
            "document_type": d.document_type,
            "confidence": d.confidence,
            "fields": fields,
        })
    summary = BatchSummary(
        total_files=len(docs),
        successful=sum(1 for d in docs if d.status == "completed"),
        failed=sum(1 for d in docs if d.status == "failed"),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    return {"summary": summary, "results": items}
