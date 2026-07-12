import shutil

from .base import ConversionRoute, ConvertContext

try:
    import pytesseract
    from PIL import Image
    _PYT = True
except Exception:
    _PYT = False

NAME = "ocr"
_IMG = ["png", "jpg", "jpeg", "tiff", "tif", "bmp", "webp"]


def available() -> bool:
    return _PYT and bool(shutil.which("tesseract"))


def routes() -> list[ConversionRoute]:
    if not available():
        return []
    return [ConversionRoute("document", s, "txt", NAME, _ocr, f"{s.upper()} -> TXT (OCR)") for s in _IMG]


def _ocr(ctx: ConvertContext) -> None:
    ctx.set_progress(10, "OCR en cours")
    img = Image.open(ctx.input_path)
    lang = (ctx.options or {}).get("lang") or "eng"
    text = pytesseract.image_to_string(img, lang=lang)
    ctx.output_path.write_text(text, encoding="utf-8")
    ctx.set_progress(100, "Termine")
