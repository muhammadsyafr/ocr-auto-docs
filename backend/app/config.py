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
    ocr_lang: str = "en"  # PaddleOCR lang code; "id" not native, use "en"+latin
    ocr_min_confidence: float = 0.5  # below -> try Tesseract fallback

    # LLM (default provider). Keys are server-side only.
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-v4-flash"
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_timeout: int = 60

    # Optional secondary keys for other providers (selectable from UI)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    ollama_base_url: str = "http://ollama:11434/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
