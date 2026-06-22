"""Convert PDF pages to images (PyMuPDF) + load raster images via OpenCV."""
import os

import cv2
import fitz  # PyMuPDF
import numpy as np

RASTER_EXT = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}


def to_images(path: str, dpi: int = 200) -> list[np.ndarray]:
    """Return a list of BGR numpy images, one per page."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _pdf_to_images(path, dpi)
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return [img]


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
