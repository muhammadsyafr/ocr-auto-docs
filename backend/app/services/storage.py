"""Filesystem storage helpers for input/output/temp roots."""
import json
import os

from app.config import get_settings

settings = get_settings()


def ensure_dirs():
    for d in (settings.storage_input, settings.storage_output, settings.storage_temp):
        os.makedirs(d, exist_ok=True)


def write_output_json(filename: str, payload: dict) -> str:
    ensure_dirs()
    base = os.path.splitext(os.path.basename(filename))[0]
    out_path = os.path.join(settings.storage_output, f"{base}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path
