"""Convert PDF pages to images via pdftoppm (primary) or PyMuPDF (fallback).
Also checks for embedded text (PyPDF2) to skip OCR when possible."""
import os
import subprocess
import tempfile

import cv2
import fitz
import numpy as np
from PIL import Image as PILImage

RASTER_EXT = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}


def to_images(path: str, dpi: int = 300) -> list[np.ndarray]:
    """Return list of BGR numpy images, one per page (for PaddleOCR/OpenCV)."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _pdf_to_images(path, dpi)
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return [img]


def to_pil_images(path: str, dpi: int = 300) -> list[PILImage.Image]:
    """Return list of PIL Images via pdftoppm (matches manual pipeline).
    Fallback to PyMuPDF if pdftoppm unavailable."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _pdf_to_pil_images(path, dpi)
    return [PILImage.open(path)]


def _pdf_to_pil_images(path: str, dpi: int) -> list[PILImage.Image]:
    try:
        return _pdftoppm_to_pil(path, dpi)
    except Exception:
        return _fitz_to_pil(path, dpi)


def _pdftoppm_to_pil(path: str, dpi: int) -> list[PILImage.Image]:
    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = os.path.join(tmpdir, "page")
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), path, prefix],
                        check=True, capture_output=True)
        files = sorted(f for f in os.listdir(tmpdir) if f.endswith(".png"))
        if not files:
            raise RuntimeError("pdftoppm produced no images")
        return [PILImage.open(os.path.join(tmpdir, f)) for f in files]


def _fitz_to_pil(path: str, dpi: int) -> list[PILImage.Image]:
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    images = []
    with fitz.open(path) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            if pix.n == 4:
                pil = PILImage.fromarray(arr, mode="RGBA").convert("RGB")
            elif pix.n == 3:
                pil = PILImage.fromarray(arr, mode="RGB")
            else:
                pil = PILImage.fromarray(arr)
            images.append(pil)
    return images


def _pdf_to_images(path: str, dpi: int) -> list[np.ndarray]:
    images = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(path) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            if pix.n == 4:
                arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            images.append(arr)
    return images


def try_extract_text(path: str) -> list[str] | None:
    ext = os.path.splitext(path)[1].lower()
    if ext != ".pdf":
        return None
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(path)
        pages = []
        for p in reader.pages:
            t = p.extract_text()
            pages.append(t if t else "")
        if any(pages):
            return pages
    except Exception:
        pass
    return None
