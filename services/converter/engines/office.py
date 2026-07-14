import os
import shutil
import subprocess
import tempfile

from .base import ConversionRoute, ConvertContext

NAME = "office"
_IN = ["docx", "doc", "pptx", "ppt", "xlsx", "xls", "odt", "ods", "odp", "rtf"]


def _soffice():
    return shutil.which("soffice") or shutil.which("libreoffice")


def available() -> bool:
    return bool(_soffice())


def routes() -> list[ConversionRoute]:
    if not available():
        return []
    out: list[ConversionRoute] = []
    for s in _IN:
        out.append(ConversionRoute("document", s, "pdf", NAME, _convert, f"{s.upper()} -> PDF"))
        out.append(ConversionRoute("document", s, "txt", NAME, _convert, f"{s.upper()} -> TXT"))
        out.append(ConversionRoute("document", s, "html", NAME, _convert, f"{s.upper()} -> HTML"))
    for s, t in [
        ("docx", "odt"), ("odt", "docx"),
        ("xlsx", "ods"), ("ods", "xlsx"),
        ("pptx", "odp"), ("odp", "pptx"),
    ]:
        out.append(ConversionRoute("document", s, t, NAME, _convert, f"{s.upper()} -> {t.upper()}"))
    # docx <-> pptx : géré par l'engine office_bridge (python-docx + python-pptx),
    # plus fiable qu'un bridge LibreOffice via ODP.
    return out


def _convert(ctx: ConvertContext) -> None:
    exe = _soffice()
    ctx.set_progress(10, "Conversion via LibreOffice")
    outdir = tempfile.mkdtemp()
    try:
        cmd = [
            exe, "--headless", "--norestore", "--nolockcheck",
            "--convert-to", ctx.target, "--outdir", outdir, str(ctx.input_path),
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode("utf-8", "replace")[:500] or "LibreOffice a echoue")
        produced = os.listdir(outdir)
        if not produced:
            raise RuntimeError("Aucun fichier produit par LibreOffice")
        shutil.move(os.path.join(outdir, produced[0]), ctx.output_path)
        ctx.set_progress(100, "Termine")
    finally:
        shutil.rmtree(outdir, ignore_errors=True)

