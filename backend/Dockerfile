FROM python:3.11-slim

# System deps for OpenCV, PyMuPDF, Tesseract, PaddleOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-ind \
    poppler-utils \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Pre-download PaddleOCR model weights at build time so concurrent workers
# don't race to download them on the first batch (and cold start is faster).
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='id', show_log=False)" || true

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
