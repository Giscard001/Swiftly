FROM python:3.11-slim

# ── Activer les sections contrib/non-free de Debian ─────────────────────────
# Nécessaire car 'unrar' (extraction RAR) est dans non-free.
# L'image slim n'inclut que 'main' par défaut → exit code 100 au build sans ceci.
RUN { \
        [ -f /etc/apt/sources.list.d/debian.sources ] \
        && sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources ; \
    } || sed -i 's/ main/ main contrib non-free/g' /etc/apt/sources.list

# ── Binaires système (conversions lourdes) ──────────────────────────────────
# LibreOffice : Office ↔ PDF, docx ↔ pptx (bridge), md → docx
# FFmpeg : audio ↔, vidéo ↔, vidéo → mp3/gif
# Tesseract : OCR image → txt, PDF scanné → txt
# poppler-utils (pdftoppm) : PDF → images PNG/JPG
# unrar : extraction archives RAR (paquet non-free)
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
