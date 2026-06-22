"""KTP extractor (PRD §8): OCR + regex + rule-based label proximity.

Fields: nik, full_name, place_of_birth, date_of_birth.
"""
import re

from app.extractors.base import Extraction
from app.services.ocr import OcrPage
from app.validators.date import normalize_date
from app.validators.nik import clean_nik

NIK_RE = re.compile(r"\d{16}")
# Identifier label "Tempat/Tgl Lahir" -> value "JAKARTA, 10-10-1990"
TTL_LABEL_RE = re.compile(
    r"(?:tempat\s*/?\s*tgl\.?\s*lahir|tempat\s*(?:dan|/)?\s*tanggal\s*lahir)\s*[:\-]?\s*",
    re.IGNORECASE,
)
# Date inside the value (10-10-1990, 10/10/1990, 1990-10-10)
DATE_IN_TEXT_RE = re.compile(r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b")
NAME_RE = re.compile(r"\bnama\s*[:\-]?\s*(.+)", re.IGNORECASE)


def extract(pages: list[OcrPage]) -> Extraction:
    ex = Extraction()
    lines = [ln for p in pages for ln in p.lines]
    text = "\n".join(ln.text for ln in lines)

    # NIK
    nik_val, nik_conf = None, 0.0
    for ln in lines:
        m = NIK_RE.search(ln.text.replace(" ", ""))
        if m:
            nik_val = clean_nik(m.group(0))
            nik_conf = ln.confidence
            break
    ex.set("nik", nik_val, nik_conf)

    # Name
    m = NAME_RE.search(text)
    ex.set("full_name", _clean(m.group(1)) if m else None, 0.85 if m else 0.0)

    # Place + Date of birth, keyed off the "Tempat/Tgl Lahir" identifier.
    # Tempat -> place_of_birth, Tgl Lahir -> date_of_birth.
    pob, dob = _extract_birth(lines)
    ex.set("place_of_birth", pob, 0.8 if pob else 0.0)
    ex.set("date_of_birth", dob, 0.8 if dob else 0.0)
    return ex


def _extract_birth(lines) -> tuple[str | None, str | None]:
    """Find the Tempat/Tgl Lahir line, split into place + date.

    Handles value on same line as label, or wrapping to the next line.
    """
    for i, ln in enumerate(lines):
        m = TTL_LABEL_RE.search(ln.text)
        if not m:
            continue
        value = ln.text[m.end():].strip()
        # Value may have wrapped to the next OCR line
        if not DATE_IN_TEXT_RE.search(value) and i + 1 < len(lines):
            value = f"{value} {lines[i + 1].text}".strip()

        dm = DATE_IN_TEXT_RE.search(value)
        if dm:
            dob = normalize_date(dm.group(0))
            place = value[: dm.start()].strip(" ,:-")
            return _clean(place) or None, dob
        # No date found -> treat comma split, place only
        place = re.split(r"[,]", value, maxsplit=1)[0]
        return _clean(place) or None, None
    return None, None


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" :-").strip()
