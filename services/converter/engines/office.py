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
    # Conversions non natives LibreOffice : bridge 2 passes via format intermédiaire
    out.append(ConversionRoute("document", "docx", "pptx", NAME, _convert_bridge, "DOCX -> PPTX"))
    out.append(ConversionRoute("document", "pptx", "docx", NAME, _convert_bridge, "PPTX -> DOCX"))
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


# Mapping des conversions bridge : source -> intermédiaire LibreOffice, puis intermédiaire -> cible
_BRIDGE_MAP = {
    ("docx", "pptx"): ("docx", "odp", "pptx"),  # docx -> odp -> pptx
    ("pptx", "docx"): ("pptx", "odp", "docx"),  # pptx -> odp -> docx
}


def _convert_bridge(ctx: ConvertContext) -> None:
    """Conversion en 2 passes via un format intermédiaire ODP.
    LibreOffice ne sait pas convertir docx<->pptx directement ;
    on passe par ODP qui est le format intermédiaire commun."""
    key = (ctx.source, ctx.target)
    if key not in _BRIDGE_MAP:
        raise RuntimeError(f"Bridge non defini pour {key}")
    _, mid_fmt, final_fmt = _BRIDGE_MAP[key]

    exe = _soffice()
    # Pass 1 : source -> format intermédiaire
    ctx.set_progress(10, f"Passage 1 : {ctx.source} -> {mid_fmt}")
    tmpdir = tempfile.mkdtemp()
    try:
        cmd1 = [
            exe, "--headless", "--norestore", "--nolockcheck",
            "--convert-to", mid_fmt, "--outdir", tmpdir, str(ctx.input_path),
        ]
        r1 = subprocess.run(cmd1, capture_output=True, timeout=600)
        if r1.returncode != 0:
            raise RuntimeError(r1.stderr.decode("utf-8", "replace")[:500] or "LibreOffice a echoue (pass 1)")
        produced = os.listdir(tmpdir)
        if not produced:
            raise RuntimeError("Aucun fichier produit par LibreOffice (pass 1)")
        mid_path = os.path.join(tmpdir, produced[0])

        # Pass 2 : intermédiaire -> cible
        ctx.set_progress(50, f"Passage 2 : {mid_fmt} -> {ctx.target}")
        tmpdir2 = tempfile.mkdtemp()
        try:
            cmd2 = [
                exe, "--headless", "--norestore", "--nolockcheck",
                "--convert-to", final_fmt, "--outdir", tmpdir2, mid_path,
            ]
            r2 = subprocess.run(cmd2, capture_output=True, timeout=600)
            if r2.returncode != 0:
                raise RuntimeError(r2.stderr.decode("utf-8", "replace")[:500] or "LibreOffice a echoue (pass 2)")
            produced2 = os.listdir(tmpdir2)
            if not produced2:
                raise RuntimeError("Aucun fichier produit par LibreOffice (pass 2)")
            shutil.move(os.path.join(tmpdir2, produced2[0]), ctx.output_path)
        finally:
            shutil.rmtree(tmpdir2, ignore_errors=True)
        ctx.set_progress(100, "Termine")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
