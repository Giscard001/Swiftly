FROM python:3.11-slim

# ── Binaires système (conversions lourdes) ──────────────────────────────────
# LibreOffice : Office ↔ PDF, docx ↔ pptx (bridge), md → docx
# FFmpeg : audio ↔, vidéo ↔, vidéo → mp3/gif
# Tesseract : OCR image → txt, PDF scanné → txt
# poppler-utils (pdftoppm) : PDF → images PNG/JPG
# unrar : extraction archives RAR
# libs WeasyPrint/cairosvg : HTML → PDF, SVG → image/PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-fra \
    poppler-utils \
    unrar \
    libpango-1.0-0 \
    libharfbuzz0b \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dépendances Python (cache Docker optimisé) ──────────────────────────────
COPY services/converter/requirements.txt services/converter/requirements-optional.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-optional.txt

# ── Code de l'application ─────────────────────────────────────────────────
COPY services/converter/ ./services/converter/

# Render injecte $PORT. On expose 8000 par défaut (fallback local).
EXPOSE 8000
CMD python -m uvicorn converter.main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir services
