"""Document processing pipeline (PRD §6 / §16 flow).

scan -> OCR -> classify -> extract -> validate -> unified JSON.
Pure function over a file path; persistence handled by the worker task.
"""
from app.classifiers import rule_based
from app.extractors import academic, employment, ktp
from app.services import ocr
from app.services.llm import LLMClient

CLASSIFIER_LLM_THRESHOLD = 0.34


def process_document(path: str, llm: LLMClient | None) -> dict:
    """Run the full pipeline for one file. Returns unified-schema dict + per-field confidence."""
    pages = ocr.ocr_file(path)
    text = ocr.full_text(pages)

    doc_type, cls_conf = rule_based.classify(text)
    # Low rule confidence -> ask LLM to classify (offline-degradable: skip if no llm)
    if cls_conf < CLASSIFIER_LLM_THRESHOLD and llm is not None:
        doc_type = _llm_classify(text, llm) or doc_type

    if doc_type == "ktp":
        ex = ktp.extract(pages)
    elif doc_type == "employment_certificate":
        ex = employment.extract(pages, llm)
    else:
        doc_type = "academic_certificate"
        ex = academic.extract(pages, llm)

    fields = {
        "nik": None, "full_name": None, "certificate_number": None,
        "place_of_birth": None, "date_of_birth": None,
        "company_name": None, "company_address": None,
    }
    fields.update(ex.fields)

    overall = round((ex.overall + cls_conf) / 2, 2) if ex.overall else cls_conf
    return {
        "document_type": doc_type,
        "confidence": overall,
        "fields": fields,
        "field_confidence": ex.confidence,
    }


def _llm_classify(text: str, llm: LLMClient) -> str | None:
    prompt = (
        "Classify this document as exactly one of: ktp, academic_certificate, "
        "employment_certificate. Return JSON {\"document_type\": \"...\"}."
    )
    try:
        out = llm.extract_json(prompt, text)
        dt = out.get("document_type")
        if dt in {"ktp", "academic_certificate", "employment_certificate"}:
            return dt
    except Exception:
        pass
    return None
