"""Pydantic schemas. The unified output schema (PRD §9) is the frozen contract."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

# ---- Field value with confidence (PRD §9 confidence schema) ----


class FieldValue(BaseModel):
    value: Optional[str] = None
    confidence: Optional[float] = None


class UnifiedFields(BaseModel):
    nik: Optional[str] = None
    full_name: Optional[str] = None
    certificate_number: Optional[str] = None
    place_of_birth: Optional[str] = None
    date_of_birth: Optional[str] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None


class UnifiedResult(BaseModel):
    """PRD §9 unified JSON schema."""
    file_name: str
    document_type: Optional[str] = None
    confidence: Optional[float] = None
    fields: UnifiedFields
    field_confidence: dict[str, float] = {}


# ---- API requests ----


class LLMSelection(BaseModel):
    provider: str
    model: str


class ProcessFolderRequest(BaseModel):
    path: str
    llm: Optional[LLMSelection] = None


class ProcessZipRequest(BaseModel):
    path: str
    llm: Optional[LLMSelection] = None


# ---- API responses ----


class JobOut(BaseModel):
    id: str
    source_type: str
    source_path: str
    status: str
    total: int
    successful: int
    failed: int
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: str
    job_id: Optional[str] = None
    filename: str
    document_type: Optional[str] = None
    status: str
    confidence: Optional[float] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class ResultDetail(BaseModel):
    document: DocumentOut
    result: UnifiedResult


class BatchSummary(BaseModel):
    total_files: int
    successful: int
    failed: int
    generated_at: str
