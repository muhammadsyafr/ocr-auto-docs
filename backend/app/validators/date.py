"""Date validation/normalization (PRD FR-010) -> YYYY-MM-DD."""
import re
from datetime import datetime

# Accept DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD (and / variants)
_FORMATS = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"]
_DATE_RE = re.compile(r"\b(\d{1,4}[/-]\d{1,2}[/-]\d{1,4})\b")


def normalize_date(value: str) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    m = _DATE_RE.search(candidate)
    if m:
        candidate = m.group(1)
    for fmt in _FORMATS:
        try:
            return datetime.strptime(candidate, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None
