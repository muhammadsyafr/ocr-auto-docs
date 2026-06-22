"""Academic certificate extractor (PRD §8).

Footer-region OCR priority + pattern matching for cert number, LLM for the rest.
Fields: certificate_number, full_name, place_of_birth, date_of_birth.
"""
import re

from app.extractors.base import Extraction
from app.services.llm import LLMClient
from app.services.ocr import OcrPage
from app.validators.date import normalize_date

LLM_PROMPT = (
    "Extract the following from this Indonesian academic certificate OCR text:\n"
    "1. certificate_number\n2. full_name\n3. place_of_birth\n4. date_of_birth\n"
    "Return ONLY a valid JSON object with these exact keys. "
    "Use null for any field you cannot find. date_of_birth as YYYY-MM-DD if possible."
)

# Common certificate-number formats (PRD §8)
CERT_PATTERNS = [
    re.compile(r"\b[A-Z]{2}-\d{2}\s+[A-Z]{2}\s+\d{6,7}\b"),   # DN-01 MA 0000001
    re.compile(r"\b[A-Z]-[A-Z]{2,4}/\d{2}/\d{4,6}\b"),         # M-SMA/13/123456
    re.compile(r"\b\d{10,}\b"),                                 # 0123456789
]
FOOTER_KEYWORDS = ["nomor", "no.", "no ", "seri", "sttb", "number"]


def _footer_lines(pages: list[OcrPage]):
    """Lines in bottom third of any page (cert number lives near footer)."""
    out = []
    for p in pages:
        out += [ln for ln in p.lines if ln.y_frac >= 0.66]
    return out


def _find_cert_number(pages: list[OcrPage]) -> tuple[str | None, float]:
    # Prefer footer region, then full doc
    for scope in (_footer_lines(pages), [ln for p in pages for ln in p.lines]):
        for ln in scope:
            for pat in CERT_PATTERNS:
                m = pat.search(ln.text)
                if m:
                    return m.group(0).strip(), ln.confidence
    return None, 0.0


def extract(pages: list[OcrPage], llm: LLMClient | None) -> Extraction:
    ex = Extraction()
    text = "\n".join(ln.text for p in pages for ln in p.lines)

    # Cert number via pattern (footer priority)
    cert, cert_conf = _find_cert_number(pages)

    # Remaining fields via LLM (semi-structured)
    llm_fields = {}
    if llm is not None:
        try:
            llm_fields = llm.extract_json(LLM_PROMPT, text)
        except Exception:
            llm_fields = {}

    cert = cert or llm_fields.get("certificate_number")
    ex.set("certificate_number", cert, cert_conf or (0.7 if cert else 0.0))
    ex.set("full_name", _s(llm_fields.get("full_name")), 0.75 if llm_fields.get("full_name") else 0.0)
    ex.set("place_of_birth", _s(llm_fields.get("place_of_birth")), 0.7 if llm_fields.get("place_of_birth") else 0.0)
    dob = normalize_date(_s(llm_fields.get("date_of_birth")) or "")
    ex.set("date_of_birth", dob, 0.7 if dob else 0.0)
    return ex


def _s(v):
    return v.strip() if isinstance(v, str) and v.strip() else None
