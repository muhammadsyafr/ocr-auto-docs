"""Shared API helpers: LLM selection + active session resolution."""
from app.config import get_settings
from app.models import Setting
from app.models.schemas import LLMSelection

settings = get_settings()


def active_session_id(db) -> str | None:
    """Currently selected session (None only before init_db ran)."""
    row = db.get(Setting, 1)
    return row.active_session_id if row else None


def resolve_llm(db, override: LLMSelection | None) -> tuple[str, str]:
    if override:
        return override.provider, override.model
    row = db.get(Setting, 1)
    if row and row.llm_provider and row.llm_model:
        return row.llm_provider, row.llm_model
    return settings.llm_provider, settings.llm_model
