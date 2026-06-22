"""NIK validation (PRD FR-010): 16 digits."""
import re

NIK_RE = re.compile(r"^\d{16}$")


def is_valid_nik(value: str) -> bool:
    return bool(NIK_RE.match(value or ""))


def clean_nik(value: str) -> str | None:
    """Strip non-digits; return 16-digit NIK or None."""
    digits = re.sub(r"\D", "", value or "")
    return digits if is_valid_nik(digits) else None
