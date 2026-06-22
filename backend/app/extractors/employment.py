"""Employment certificate extractor (PRD §8): OCR + LLM extraction.

Fields: company_name, company_address — taken from the document HEADER
(letterhead / kop surat) only, not the letter body.
"""
from app.extractors.base import Extraction
from app.services.llm import LLMClient
from app.services.ocr import OcrPage

# Top fraction of page 1 treated as the letterhead/header region.
HEADER_Y_FRAC = 0.25
# Minimum header lines before we trust the fractional region; else take top-N lines.
HEADER_MIN_LINES = 2
HEADER_TOPN = 6

LLM_PROMPT = (
    "The text below is ONLY the header / letterhead (kop surat) from the top of "
    "an employment letter. Extract the COMPANY identity from this letterhead:\n"
    "1. company_name — the company name shown in the letterhead.\n"
    "2. company_address — the FULL company address from the letterhead: street, "
    "building/number, city/regency, province, and postal code if present. Combine "
    "multi-line address fragments into one complete string. Do not omit the postal code.\n\n"
    "IMPORTANT:\n"
    "- The company address is the address printed in the letterhead, usually right "
    "below the company name and near the phone/website line.\n"
    "- IGNORE any line labeled 'Nama', 'Alamat', or 'Jabatan' — those describe a "
    "person (an employee), NOT the company. Never use a labeled 'Alamat' value.\n"
    "- Use ONLY this header text; do not infer from elsewhere.\n"
    "Return ONLY a valid JSON object with these exact keys. Use null if not found."
)


def _header_text(pages: list[OcrPage]) -> str:
    """Letterhead text: top region of page 1.

    Bounded to the header — never the body — so the employee's labeled 'Alamat'
    line cannot be mistaken for the company address. If the fractional region is
    too thin, take the first few lines (letterheads are always at the very top).
    """
    if not pages or not pages[0].lines:
        return ""
    lines = pages[0].lines
    header = [ln.text for ln in lines if ln.y_frac <= HEADER_Y_FRAC]
    if len(header) < HEADER_MIN_LINES:
        header = [ln.text for ln in lines[:HEADER_TOPN]]
    return "\n".join(header).strip()


def extract(pages: list[OcrPage], llm: LLMClient | None) -> Extraction:
    ex = Extraction()
    source = _header_text(pages)

    fields = {}
    if llm is not None and source:
        try:
            fields = llm.extract_json(LLM_PROMPT, source)
        except Exception:
            fields = {}

    name = _s(fields.get("company_name"))
    addr = _s(fields.get("company_address"))
    ex.set("company_name", name, 0.75 if name else 0.0)
    ex.set("company_address", addr, 0.7 if addr else 0.0)
    return ex


def _s(v):
    return v.strip() if isinstance(v, str) and v.strip() else None
