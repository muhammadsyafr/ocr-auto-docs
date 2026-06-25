"""Results endpoints (PRD §11): list results, detail, file preview."""
import json
import mimetypes

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import active_session_id
from app.db import get_db
from app.models import Document, ExtractionResult, Job
from app.models.schemas import DocumentOut, ResultDetail, UnifiedFields, UnifiedResult

router = APIRouter(prefix="/api", tags=["results"])


@router.get("/results", response_model=list[DocumentOut])
def list_results(db: Session = Depends(get_db)):
    sid = active_session_id(db)
    return (
        db.query(Document)
        .join(Job, Document.job_id == Job.id)
        .filter(Job.session_id == sid)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.get("/results/{doc_id}", response_model=ResultDetail)
def result_detail(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    unified = _load_result_json(doc)
    if unified is None:
        unified = _build_from_db_rows(doc, db)

    return ResultDetail(document=DocumentOut.model_validate(doc), result=unified)


def _load_result_json(doc: Document) -> UnifiedResult | None:
    if not doc.output_path or doc.status not in ("completed", "failed"):
        return None
    try:
        with open(doc.output_path, encoding="utf-8") as f:
            payload = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    fc = payload.get("field_confidence", {})
    return UnifiedResult(
        file_name=payload.get("file_name", doc.filename),
        document_type=payload.get("document_type", doc.document_type),
        confidence=payload.get("confidence", doc.confidence),
        fields=UnifiedFields(**{k: payload.get("fields", {}).get(k) for k in UnifiedFields.model_fields}),
        field_confidence=fc,
    )


def _build_from_db_rows(doc: Document, db: Session) -> UnifiedResult:
    db.refresh(doc)
    fields, conf = {}, {}
    for r in doc.results:
        fields[r.field_name] = r.field_value
        conf[r.field_name] = r.confidence or 0.0
    return UnifiedResult(
        file_name=doc.filename,
        document_type=doc.document_type,
        confidence=doc.confidence,
        fields=UnifiedFields(**{k: fields.get(k) for k in UnifiedFields.model_fields}),
        field_confidence=conf,
    )


@router.get("/results/{doc_id}/file")
def result_file(doc_id: str, db: Session = Depends(get_db)):
    """Serve the original document inline (for preview, not download)."""
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    media_type, _ = mimetypes.guess_type(doc.filename)
    # inline disposition -> browser renders in iframe/img instead of downloading
    return FileResponse(
        doc.source_path,
        media_type=media_type or "application/octet-stream",
        content_disposition_type="inline",
    )
