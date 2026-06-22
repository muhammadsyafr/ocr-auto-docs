"""LLM provider selection (PRD FR-013)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import resolve_llm
from app.db import get_db
from app.models import Setting
from app.models.schemas import LLMSelection
from app.services import llm as llm_service

router = APIRouter(prefix="/api", tags=["llm"])


@router.get("/llm/providers")
def list_providers(db: Session = Depends(get_db)):
    provider, model = resolve_llm(db, None)
    return llm_service.list_providers(provider, model)


@router.put("/settings/llm")
def set_default_llm(sel: LLMSelection, db: Session = Depends(get_db)):
    try:
        p = llm_service.get_provider(sel.provider)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if sel.model not in p.models:
        raise HTTPException(400, f"Model {sel.model} not available for {sel.provider}")
    row = db.get(Setting, 1)
    if not row:
        row = Setting(id=1)
        db.add(row)
    row.llm_provider = sel.provider
    row.llm_model = sel.model
    db.commit()
    return {"provider": sel.provider, "model": sel.model}
