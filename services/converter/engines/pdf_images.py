import shutil
import tempfile
import zipfile

from .base import ConversionRoute, ConvertContext

try:
    from pdf2image import convert_from_path
    _PDF2IMG = True
except Exception:
    _PDF2IMG = False

NAME = "pdf_images"


def available() -> bool:
    return _PDF2IMG and bool(shutil.which("pdftoppm"))


def routes() -> list[ConversionRoute]:
    if not available():
        return []
    return [
        ConversionRoute("document", "pdf", "png", NAME, _pdf_to_images, "PDF -> PNG (pages)"),
        ConversionRoute("document", "pdf", "jpg", NAME, _pdf_to_images, "PDF -> JPG (pages)"),
    ]


def _pdf_to_images(ctx: ConvertContext) -> None:
    ctx.set_progress(10, "Rendu des pages via poppler")
    fmt = "jpeg" if ctx.target == "jpg" else "png"
    with tempfile.TemporaryDirectory() as d:
        pages = convert_from_path(str(ctx.input_path), dpi=int((ctx.options or {}).get("dpi", 150)))
        n = len(pages)
        if n == 1:
            pages[0].save(ctx.output_path, format=fmt.upper())
        else:
            with zipfile.ZipFile(ctx.output_path, "w", zipfile.ZIP_DEFLATED) as z:
                for i, page in enumerate(pages):
                    buf_path = f"{d}/page_{i + 1}.{ctx.target}"
                    page.save(buf_path, format=fmt.upper())
                    z.write(buf_path, arcname=f"page_{i + 1}.{ctx.target}")
                    ctx.set_progress(int(10 + 85 * (i + 1) / n), f"Page {i + 1}/{n}")
    ctx.set_progress(100, "Termine")

