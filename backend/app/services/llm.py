"""LLM client + provider registry.

Custom OpenAI-compatible endpoint configurable via env.
Text-in (OCR output), JSON-out. Keys are server-side only — never returned to UI.
"""
import json
from dataclasses import dataclass

from openai import OpenAI

from app.config import get_settings

settings = get_settings()


@dataclass
class Provider:
    name: str
    base_url: str
    api_key: str
    models: list[str]

    @property
    def configured(self) -> bool:
        return bool(self.api_key)


def _registry() -> dict[str, Provider]:
    models = [m.strip() for m in settings.llm_models_custom.split(",") if m.strip()]
    if settings.llm_model_default and settings.llm_model_default not in models:
        models.insert(0, settings.llm_model_default)
    name = settings.llm_provider or "custom"
    return {
        name: Provider(
            name, settings.llm_base_url_custom, settings.llm_api_key_custom,
            models or [settings.llm_model_default or "default"],
        ),
    }


def list_providers(active_provider: str, active_model: str) -> dict:
    """Shape per PRD FR-013 GET /api/llm/providers (no keys exposed)."""
    providers = []
    for p in _registry().values():
        providers.append({
            "provider": p.name,
            "models": p.models,
            "configured": p.configured,
        })
    return {
        "active": {"provider": active_provider, "model": active_model},
        "providers": providers,
    }


def get_provider(name: str) -> Provider:
    reg = _registry()
    if name not in reg:
        raise ValueError(f"Unknown LLM provider: {name}")
    return reg[name]


class LLMClient:
    """Thin wrapper around an OpenAI-compatible endpoint."""

    def __init__(self, provider: str, model: str):
        p = get_provider(provider)
        self.model = model
        self.provider = provider
        self._client = OpenAI(base_url=p.base_url, api_key=p.api_key or "none",
                              timeout=settings.llm_timeout)

    def extract_json(self, system_prompt: str, ocr_text: str) -> dict:
        """Send OCR text, expect JSON object back. Raises on failure."""
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ocr_text},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)
