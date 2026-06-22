"""OCR service: PaddleOCR primary, Tesseract fallback on low confidence.

Returns OcrPage objects holding lines with text, bbox, confidence.
PaddleOCR is loaded lazily and cached (heavy init).
"""
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from app.config import get_settings
from app.services import pdf_converter
from app.services.preprocess import preprocess

settings = get_settings()


@dataclass
class OcrLine:
    text: str
    confidence: float
    box: list  # 4-point polygon or bbox
    # vertical center as fraction of page height (0=top, 1=bottom) for region logic
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


def _paddle_page(img: np.ndarray) -> OcrPage:
    h, w = img.shape[:2]
    result = _get_paddle().ocr(img, cls=True)
    page = OcrPage(height=h, width=w)
    if not result or not result[0]:
        return page
    for box, (text, conf) in result[0]:
        ys = [pt[1] for pt in box]
        y_center = sum(ys) / len(ys)
        page.lines.append(OcrLine(text=text, confidence=float(conf), box=box,
                                  y_frac=y_center / h if h else 0.0))
    return page


def _tesseract_page(img: np.ndarray) -> OcrPage:
    import pytesseract
    from pytesseract import Output
    h, w = img.shape[:2]
    data = pytesseract.image_to_data(img, output_type=Output.DICT)
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
    """OCR every page. Falls back to Tesseract when Paddle confidence is low."""
    pages: list[OcrPage] = []
    for raw in pdf_converter.to_images(path):
        img = preprocess(raw)
        try:
            page = _paddle_page(img)
        except Exception:
            page = OcrPage()
        if page.mean_confidence < settings.ocr_min_confidence:
            try:
                alt = _tesseract_page(img)
                if alt.mean_confidence > page.mean_confidence:
                    page = alt
            except Exception:
                pass
        pages.append(page)
    return pages


def full_text(pages: list[OcrPage]) -> str:
    return "\n".join(p.text for p in pages)
