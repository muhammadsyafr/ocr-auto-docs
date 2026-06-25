# OCR PDF Scan Pipeline Documentation

## Problem
Model AI tidak bisa read PDF directly. PDF "IJAZAH - NANANG.pdf" is scanned image — no embedded text. PyPDF2 returns empty.

## Solution Pipeline

### Step 1: Locate PDF
```bash
find /Users/mekari -name "IJAZAH - NANANG.pdf"
```

### Step 2: Check PDF content type
```bash
python3 -c "
from PyPDF2 import PdfReader
r = PdfReader('path/to/pdf')
for p in r.pages:
    text = p.extract_text()
    print(text if text else '[no extractable text - likely image/scan]')
"
```
If empty → PDF is scanned image, need OCR.

### Step 3: Install dependencies
```bash
brew install poppler        # pdftoppm: PDF → image
brew install tesseract      # OCR engine
brew install tesseract-lang # Language packs (ind, eng, etc)
pip3 install Pillow         # Image processing
pip3 install pytesseract    # Python OCR wrapper
```

### Step 4: PDF → Image (pdftoppm)
```bash
pdftoppm -png -r 300 "input.pdf" /tmp/output_prefix
```
- `-png`: output format PNG
- `-r 300`: 300 DPI resolution (higher = better OCR accuracy)
- Output: `/tmp/output_prefix-1.png`, `/tmp/output_prefix-2.png`, etc.

### Step 5: OCR (pytesseract)
tesseract CLI gagal di macOS karena leptonica path issue. Solusi: use Python wrapper.

```python
import pytesseract
from PIL import Image

img = Image.open('/tmp/output_prefix-1.png')
text = pytesseract.image_to_string(img, lang='ind+eng')
print(text)
```

- `lang='ind+eng'`: Indonesian + English language pack
- `--psm 6`: Assume uniform block of text (optional, for structured docs)

### Step 6: Write output
OCR result → structured markdown file.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| tesseract "Image file not found" | macOS leptonica path bug | Use `pytesseract` Python wrapper instead of CLI |
| OCR result gibberish | Low DPI scan | Increase `pdftoppm -r` to 400-600 |
| Partial fields missing | Scan quality too low | Manual verification needed |
| Wrong language detected | Missing lang pack | `brew install tesseract-lang` adds all 165 languages |

## Flow Diagram

```
PDF (scanned image)
  → pdftoppm (PDF → PNG, 300 DPI)
  → PIL Image.open()
  → pytesseract.image_to_string(lang='ind+eng')
  → Markdown output
```

## Tools Installed

| Tool | Purpose |
|------|---------|
| poppler | pdftoppm: PDF → raster image |
| tesseract | OCR engine |
| tesseract-lang | Language data (ind, eng, 165 languages) |
| Pillow | Image load/convert for pytesseract |
| pytesseract | Python bridge to tesseract |
| PyPDF2 | Check if PDF has embedded text |
