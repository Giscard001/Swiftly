import importlib
import shutil

from .config import settings
from .engines import archives, av, data, images, markdown_engine, ocr_pdf, office, office_bridge, ocr, pdf_engine, pdf_images, pdf_office

_ENGINES = [images, pdf_engine, pdf_images, pdf_office, ocr_pdf, markdown_engine, data, archives, office, office_bridge, av, ocr]


def probe_binaries() -> dict:
    def which(*names):
        for n in names:
            p = shutil.which(n)
            if p:
                return p
        return None

    return {
        "libreoffice": which("soffice", "libreoffice"),
        "ffmpeg": which("ffmpeg"),
        "tesseract": which("tesseract"),
        "pdftoppm": which("pdftoppm"),
    }


def probe_libs() -> dict:
    out = {}
    for m in ("PIL", "pypdf", "fpdf", "openpyxl", "py7zr", "pytesseract", "pillow_heif", "pdf2image", "pdf2docx", "pdfplumber", "pptx", "weasyprint", "cairosvg"):
        try:
            importlib.import_module(m)
            out[m] = True
        except Exception:
            out[m] = False
    return out


def all_routes() -> list:
    routes = []
    for e in _ENGINES:
        try:
            if e.available():
                routes.extend(e.routes())
        except Exception:
            pass
    return routes


def find_route(source: str, target: str, category: str | None = None, prefer_ocr: bool = False):
    source = (source or "").lower()
    target = (target or "").lower()
    routes = all_routes()
    if prefer_ocr:
        for r in routes:
            if r.source == source and r.target == target and r.engine == "ocr_pdf" and (not category or r.category == category):
                return r
    for r in routes:
        if r.source == source and r.target == target and r.engine != "ocr_pdf" and (not category or r.category == category):
            return r
    return None


def capabilities_payload() -> dict:
    routes = all_routes()
    by_source: dict[str, list] = {}
    for r in routes:
        by_source.setdefault(r.source, []).append(
            {"category": r.category, "target": r.target, "engine": r.engine, "label": r.label}
        )
    categories = sorted({r.category for r in routes})
    return {
        "categories": categories,
        "by_source": by_source,
        "routes": [
            {
                "category": r.category,
                "source": r.source,
                "target": r.target,
                "engine": r.engine,
                "label": r.label,
            }
            for r in routes
        ],
        "binaries": probe_binaries(),
        "libs": probe_libs(),
        "limit": settings.max_file_size,
        "retention_seconds": settings.retention_seconds,
    }
