"""Results endpoints (PRD §11): list results, detail, file preview."""
import mimetypes

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document
from app.models.schemas import DocumentOut, ResultDetail, UnifiedFields, UnifiedResult

router = APIRouter(prefix="/api", tags=["results"])


@router.get("/results", response_model=list[DocumentOut])
def list_results(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.get("/results/{doc_id}", response_model=ResultDetail)
def result_detail(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    fields, conf = {}, {}
    for r in doc.results:
        fields[r.field_name] = r.field_value
        conf[r.field_name] = r.confidence or 0.0
    unified = UnifiedResult(
        file_name=doc.filename,
        document_type=doc.document_type,
        confidence=doc.confidence,
        fields=UnifiedFields(**{k: fields.get(k) for k in UnifiedFields.model_fields}),
        field_confidence=conf,
    )
    return ResultDetail(document=DocumentOut.model_validate(doc), result=unified)


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
