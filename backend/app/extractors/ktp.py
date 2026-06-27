"""KTP extractor (PRD §8): OCR + regex + rule-based label proximity.

Fields: nik, full_name, place_of_birth, date_of_birth.
Falls back to KTP-OCR (Tesseract ind + threshold) when PaddleOCR rules miss NIK.
"""
import logging
import re

import cv2
import numpy as np

from app.extractors.base import Extraction
from app.services.ocr import OcrPage
from app.validators.date import normalize_date
from app.validators.nik import clean_nik

log = logging.getLogger("ktp.extractor")

NIK_RE = re.compile(r"\d{16}")
DIGIT_MAP = str.maketrans("OoIlLiSsBZ", "0011115582")


def _normalize_digits(s: str) -> str:
    """Translate common OCR misreads to digits."""
    return re.sub(r"\s+", "", s).translate(DIGIT_MAP)


# Identifier label "Tempat/Tgl Lahir" -> value "JAKARTA, 10-10-1990"
TTL_LABEL_RE = re.compile(
    r"(?:tempat\s*/?\s*tgl\.?\s*lahir|tempat\s*(?:dan|/)?\s*tanggal\s*lahir)\s*[:\-]?\s*",
    re.IGNORECASE,
)
# Date inside the value (10-10-1990, 10/10/1990, 1990-10-10)
DATE_IN_TEXT_RE = re.compile(r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b")
NAME_RE = re.compile(r"\bnama\s*[:\-]?\s*(.+)", re.IGNORECASE)


def extract(pages: list[OcrPage], path: str = "") -> Extraction:
    ex = Extraction()
    lines = [ln for p in pages for ln in p.lines]
    text = "\n".join(ln.text for ln in lines)

    # NIK
    nik_val, nik_conf = None, 0.0
    for ln in lines:
        m = NIK_RE.search(_normalize_digits(ln.text))
        if m:
            nik_val = clean_nik(m.group(0))
            nik_conf = ln.confidence
            break
    ex.set("nik", nik_val, nik_conf)

    # Name
    m = NAME_RE.search(text)
    ex.set("full_name", _clean(m.group(1)) if m else None, 0.85 if m else 0.0)

    # Place + Date of birth
    pob, dob = _extract_birth(lines)
    ex.set("place_of_birth", pob, 0.8 if pob else 0.0)
    ex.set("date_of_birth", dob, 0.8 if dob else 0.0)

    # Fallback 1: ROI crop around NIK label → re-OCR at 2x (cheap, targeted)
    if not ex.fields.get("nik") and path:
        _nik_roi_fallback(ex, pages, path)
    # Fallback 2: KTP-OCR (Tesseract ind + threshold) full image when ROI also misses
    if not ex.fields.get("nik") and path:
        _ktpocr_fallback(ex, path)
    return ex


def _find_nik_label_line(pages: list[OcrPage]):
    """Find the OCR line containing the 'NIK' label (without a valid 16-digit value)."""
    for p in pages:
        for ln in p.lines:
            if "NIK" in ln.text.upper() and not NIK_RE.search(_normalize_digits(ln.text)):
                return ln
    return None


def _nik_roi_fallback(ex: Extraction, pages: list[OcrPage], path: str):
    """Crop a horizontal band around the 'NIK' label, upscale 2x, re-OCR, regex NIK.

    KTP layout: NIK value sits on (or just below) the 'NIK :' label row.
    Cropping that band + upscaling boosts effective DPI on the 16 digits.
    """
    nik_line = _find_nik_label_line(pages)
    if nik_line is None or not nik_line.box:
        return
    try:
        from app.services import pdf_converter
        from app.services.ocr import _paddle_ocr_numpy
        images = pdf_converter.to_images(path)
    except Exception as e:
        log.warning("NIK ROI: cannot load images: %s", e)
        return
    if not images:
        return
    img = images[0]
    h, w = img.shape[:2]
    box = nik_line.box
    ys = [pt[1] for pt in box]
    y_min, y_max = min(ys), max(ys)
    line_h = max(1, y_max - y_min)
    y1 = max(0, int(y_min - line_h * 0.5))
    y2 = min(h, int(y_max + line_h * 1.5))
    crop = img[y1:y2, :]
    crop = cv2.resize(crop, (crop.shape[1] * 2, crop.shape[0] * 2),
                      interpolation=cv2.INTER_CUBIC)
    try:
        page = _paddle_ocr_numpy(crop)
    except Exception as e:
        log.warning("NIK ROI: PaddleOCR error: %s", e)
        return
    for ln in page.lines:
        m = NIK_RE.search(_normalize_digits(ln.text))
        if m:
            nik = clean_nik(m.group(0))
            if nik:
                ex.set("nik", nik, max(ln.confidence, 0.7))
                log.info("NIK ROI fallback found NIK: %s", nik)
                return


def _ktpocr_fallback(ex: Extraction, path: str):
    """Re-OCR with Tesseract ind + KTP-OCR extraction when PaddleOCR rules miss NIK."""
    try:
        from app.services.ktpocr import KTPOCR
        from app.services import pdf_converter
        images = pdf_converter.to_images(path)
    except Exception as e:
        log.warning("KTP-OCR fallback: cannot load images: %s", e)
        return
    for img in images:
        try:
            ktp = KTPOCR(img)
            r = ktp.result
        except Exception as e:
            log.warning("KTP-OCR extraction error: %s", e)
            continue
        if r.nik and not ex.fields.get("nik"):
            nik = clean_nik(r.nik)
            if nik:
                ex.set("nik", nik, 0.6)
                log.info("KTP-OCR fallback found NIK: %s", nik)
        if r.nama and not ex.fields.get("full_name"):
            ex.set("full_name", _clean(r.nama), 0.6)
        if r.tempat_lahir and not ex.fields.get("place_of_birth"):
            ex.set("place_of_birth", _clean(r.tempat_lahir), 0.5)
        if r.tanggal_lahir and not ex.fields.get("date_of_birth"):
            dob = normalize_date(r.tanggal_lahir)
            if dob:
                ex.set("date_of_birth", dob, 0.6)
        if ex.fields.get("nik"):
            return


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
