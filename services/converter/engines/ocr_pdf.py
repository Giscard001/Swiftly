import shutil

from .base import ConversionRoute, ConvertContext

try:
    from pdf2image import convert_from_path
    _PDF2IMG = True
except Exception:
    _PDF2IMG = False

try:
    import pytesseract
    from PIL import Image
    _PYT = True
except Exception:
    _PYT = False

NAME = "ocr_pdf"


def available() -> bool:
    return _PDF2IMG and _PYT and bool(shutil.which("tesseract")) and bool(shutil.which("pdftoppm"))


def routes() -> list[ConversionRoute]:
    if not available():
        return []
    return [ConversionRoute("document", "pdf", "txt", NAME, _ocr_pdf, "PDF -> Texte (OCR)")]


def _ocr_pdf(ctx: ConvertContext) -> None:
    ctx.set_progress(5, "OCR PDF - rendu des pages")
    lang = (ctx.options or {}).get("lang") or "eng"
    pages = convert_from_path(str(ctx.input_path), dpi=200)
    n = len(pages)
    parts: list[str] = []
    for i, page in enumerate(pages):
        parts.append(pytesseract.image_to_string(page, lang=lang))
        ctx.set_progress(int(5 + 90 * (i + 1) / n), f"OCR page {i + 1}/{n}")
    ctx.output_path.write_text("\n".join(parts), encoding="utf-8")
    ctx.set_progress(100, "Termine")
