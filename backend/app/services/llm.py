"""LLM client + provider registry.

External OpenAI-compatible API (default DeepSeek). Selectable per job/default.
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
    offline: bool = False

    @property
    def configured(self) -> bool:
        # Ollama needs no key; others need one.
        return self.offline or bool(self.api_key)


def _registry() -> dict[str, Provider]:
    return {
        "deepseek": Provider(
            "deepseek", settings.llm_base_url, settings.llm_api_key,
            # v4 names current (June 2026); chat/reasoner deprecate 2026-07-24
            ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-chat", "deepseek-reasoner"],
        ),
        "openai": Provider(
            "openai", settings.openai_base_url, settings.openai_api_key,
            ["gpt-4o-mini", "gpt-4o"],
        ),
        "ollama": Provider(
            "ollama", settings.ollama_base_url, "ollama",
            ["qwen2.5", "minicpm-v", "llama3.1"], offline=True,
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
            "offline": p.offline,
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
