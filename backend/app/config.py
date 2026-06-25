"""Application settings loaded from environment."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database / queue
    database_url: str = "postgresql+psycopg2://ocr:ocr@postgres:5432/ocr"
    redis_url: str = "redis://redis:6379/0"

    # Storage roots
    storage_input: str = "/data/input"
    storage_output: str = "/data/output"
    storage_temp: str = "/data/temp"

    # OCR
    ocr_lang: str = "id"
    ocr_min_confidence: float = 0.5  # below -> try Tesseract fallback

    # LLM — custom OpenAI-compatible endpoint. Keys are server-side only.
    llm_provider: str = "custom"
    llm_model_default: str = ""
    llm_api_key_custom: str = ""
    llm_base_url_custom: str = ""
    llm_models_custom: str = ""  # comma-separated, e.g. "gpt-4o-mini,deepseek-chat"
    llm_timeout: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
