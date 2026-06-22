"""Shared extractor result type."""
from dataclasses import dataclass, field


@dataclass
class Extraction:
    fields: dict[str, str | None] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)

    def set(self, name: str, value: str | None, conf: float):
        self.fields[name] = value
        self.confidence[name] = round(conf, 2) if value else 0.0

    @property
    def overall(self) -> float:
        vals = [c for c in self.confidence.values() if c > 0]
        return round(sum(vals) / len(vals), 2) if vals else 0.0
