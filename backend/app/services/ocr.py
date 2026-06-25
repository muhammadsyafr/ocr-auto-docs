"""OCR service: PaddleOCR primary (structured lines with y_frac),
Tesseract fallback only. PaddleOCR gives cleaner Indonesian text.
"""
import logging
from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image as PILImage

from app.config import get_settings
from app.services import pdf_converter

settings = get_settings()
log = logging.getLogger("ocr.service")


@dataclass
class OcrLine:
    text: str
    confidence: float
    box: list
    y_frac: float = 0.0


@dataclass
class OcrPage:
    lines: list[OcrLine] = field(default_factory=list)
    height: int = 0
    width: int = 0

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)

    @property
    def mean_confidence(self) -> float:
        if not self.lines:
            return 0.0
        return sum(line.confidence for line in self.lines) / len(self.lines)


_paddle = None


def _get_paddle():
    global _paddle
    if _paddle is None:
        from paddleocr import PaddleOCR
        _paddle = PaddleOCR(use_angle_cls=True, lang=settings.ocr_lang, show_log=False)
    return _paddle


def _paddle_ocr_numpy(img: np.ndarray) -> OcrPage:
    h, w = img.shape[:2]
    result = _get_paddle().ocr(img, cls=True)
    page = OcrPage(height=h, width=w)
    if not result or not result[0]:
        return page
    for box, (text, conf) in result[0]:
        y_min = min(p[1] for p in box)
        y_max = max(p[1] for p in box)
        y_frac = ((y_min + y_max) / 2) / h if h else 0.0
        page.lines.append(OcrLine(text=text, confidence=round(conf, 3),
                                  box=box, y_frac=y_frac))
    return page


def _tesseract_fallback(pil_img: PILImage.Image) -> OcrPage:
    import pytesseract
    from pytesseract import Output
    w, h = pil_img.size
    config = "--psm 6"
    data = pytesseract.image_to_data(pil_img, output_type=Output.DICT,
                                      lang="ind+eng", config=config)
    page = OcrPage(height=h, width=w)
    n = len(data["text"])
    for i in range(n):
        txt = data["text"][i].strip()
        conf = float(data["conf"][i])
        if not txt or conf < 0:
            continue
        y_center = data["top"][i] + data["height"][i] / 2
        page.lines.append(OcrLine(text=txt, confidence=conf / 100.0,
                                    box=[[data["left"][i], data["top"][i]]],
                                    y_frac=y_center / h if h else 0.0))
    return page


def ocr_file(path: str) -> list[OcrPage]:
    """OCR every page. PaddleOCR primary with structured lines,
    Tesseract fallback if PaddleOCR fails. Skips OCR when PDF has embedded text."""
    pdf_texts = pdf_converter.try_extract_text(path)
    if pdf_texts is not None:
        log.info("PDF has embedded text, skipping OCR: %s", path)
        return _text_pages(pdf_texts)
    log.info("PDF is scanned/image, running OCR: %s", path)

    bgr_images = pdf_converter.to_images(path)

    pages: list[OcrPage] = []
    for i, bgr_img in enumerate(bgr_images):
        log.info("Page %d: BGR shape=%s", i + 1, bgr_img.shape)

        page = _paddle_ocr_numpy(bgr_img)
        if page.lines:
            log.info("Page %d: PaddleOCR conf=%.2f lines=%d", i + 1, page.mean_confidence, len(page.lines))
        else:
            log.warning("Page %d: PaddleOCR returned no lines, Tesseract fallback", i + 1)
            pil_img = PILImage.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB))
            page = _tesseract_fallback(pil_img)
            log.info("Page %d: Tesseract fallback conf=%.2f lines=%d", i + 1, page.mean_confidence, len(page.lines))

        pages.append(page)
    return pages


def _text_pages(texts: list[str]) -> list[OcrPage]:
    pages = []
    for i, t in enumerate(texts):
        page = OcrPage()
        for line in t.splitlines():
            stripped = line.strip()
            if stripped:
                page.lines.append(OcrLine(text=stripped, confidence=0.95,
                                          box=[], y_frac=0.5))
        pages.append(page)
    return pages


def full_text(pages: list[OcrPage]) -> str:
    return "\n".join(p.text for p in pages)
