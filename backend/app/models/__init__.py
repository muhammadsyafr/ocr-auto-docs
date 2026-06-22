"""ORM models. Extends PRD §12 with jobs + settings tables."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    source_type = Column(String, nullable=False)        # folder | zip | upload
    source_path = Column(Text, nullable=False)
    status = Column(String, default="queued")            # queued|processing|completed|failed
    total = Column(Integer, default=0)
    successful = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    llm_provider = Column(String, nullable=True)         # resolved override / default
    llm_model = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    documents = relationship("Document", back_populates="job", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id"))
    filename = Column(Text, nullable=False)
    source_path = Column(Text, nullable=False)
    document_type = Column(String, nullable=True)
    status = Column(String, default="queued")
    confidence = Column(Float, nullable=True)
    output_path = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="documents")
    results = relationship("ExtractionResult", back_populates="document", cascade="all, delete-orphan")


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"))
    field_name = Column(String, nullable=False)
    field_value = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)

    document = relationship("Document", back_populates="results")


class Setting(Base):
    """Single-row app settings (default LLM)."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    llm_provider = Column(String, nullable=True)
    llm_model = Column(String, nullable=True)
