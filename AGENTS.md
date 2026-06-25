# Project Instructions

## OCR Pipeline for PDFs

When a PDF has no extractable text (scanned/image PDF), follow this pipeline:
1. Check PDF content: `PyPDF2 PdfReader` → `extract_text()`. Empty = scanned image.
2. Convert PDF → image: `pdftoppm -png -r 300 "input.pdf" /tmp/output_prefix` (or `PyMuPDF/fitz` at 300 DPI).
3. OCR image: `pytesseract.image_to_string(img, lang='ind+eng')` (or PaddleOCR primary with Tesseract fallback).
4. Output → structured markdown.

Dependencies: poppler, tesseract, tesseract-lang, Pillow, pytesseract, PyPDF2, PyMuPDF (fitz).

See `ocr-pdf-documentation.md` for full pipeline details and troubleshooting.

## Reference Architecture

Backend (`backend/app/`) implements this pipeline in code:
- `services/pdf_converter.py`: PyMuPDF renders PDF→image, PyPDF2 checks embedded text
- `services/ocr.py`: PaddleOCR primary, Tesseract fallback, `ocr_file()` entry point
- `services/preprocess.py`: grayscale + deskew + denoise before OCR
- `pipeline.py`: orchestrates OCR → classify → extract → validate
