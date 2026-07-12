import re
import tempfile
import shutil
import os
import subprocess

from .base import ConversionRoute, ConvertContext

try:
    from fpdf import FPDF
    _FPDF = True
except Exception:
    _FPDF = False

NAME = "markdown"


def _md_to_html(text: str) -> str:
    lines = text.splitlines()
    html: list[str] = []
    in_ul = False
    in_code = False
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                html.append("</code></pre>")
                in_code = False
            else:
                html.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            html.append(_esc(line))
            continue
        if not line:
            if in_ul:
                html.append("</ul>")
                in_ul = False
            html.append("")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            if in_ul:
                html.append("</ul>")
                in_ul = False
            lvl = len(m.group(1))
            html.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
            continue
        if line in ("---", "***", "___"):
            if in_ul:
                html.append("</ul>")
                in_ul = False
            html.append("<hr/>")
            continue
        m = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if m:
            if not in_ul:
                html.append("<ul>")
                in_ul = True
            html.append(f"<li>{_inline(m.group(1))}</li>")
            continue
        if in_ul:
            html.append("</ul>")
            in_ul = False
        html.append(f"<p>{_inline(line)}</p>")
    if in_ul:
        html.append("</ul>")
    if in_code:
        html.append("</code></pre>")
    body = "\n".join(html)
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>body{font-family:Inter,Arial,sans-serif;max-width:720px;margin:40px auto;"
        "padding:0 24px;line-height:1.6;color:#1f2937}"
        "pre{background:#f3f4f6;padding:12px;border-radius:8px;overflow:auto}"
        "code{background:#f3f4f6;padding:2px 5px;border-radius:4px}"
        "pre code{background:transparent;padding:0}"
        "h1,h2,h3{line-height:1.25}hr{border:none;border-top:1px solid #e5e7eb;margin:24px 0}"
        "</style></head><body>" + body + "</body></html>"
    )


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(s: str) -> str:
    s = _esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2"/>', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s


def _md_to_text_lines(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            out.append(m.group(2))
            continue
        m = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if m:
            out.append("• " + m.group(1))
            continue
        out.append(line)
    return out


def _is_office() -> bool:
    return bool(shutil.which("soffice") or shutil.which("libreoffice"))


def available() -> bool:
    return _FPDF


def routes() -> list[ConversionRoute]:
    out: list[ConversionRoute] = []
    if _FPDF:
        out.append(ConversionRoute("document", "md", "html", NAME, _md_to_html_file, "Markdown -> HTML"))
        out.append(ConversionRoute("document", "md", "pdf", NAME, _md_to_pdf, "Markdown -> PDF"))
    if _is_office():
        out.append(ConversionRoute("document", "md", "docx", NAME, _md_to_docx, "Markdown -> Word (.docx)"))
    return out


def _md_to_html_file(ctx: ConvertContext) -> None:
    ctx.set_progress(20, "Rendu Markdown -> HTML")
    text = ctx.input_path.read_text(encoding="utf-8", errors="replace")
    html = _md_to_html(text)
    ctx.output_path.write_text(html, encoding="utf-8")
    ctx.set_progress(100, "Termine")


def _md_to_pdf(ctx: ConvertContext) -> None:
    ctx.set_progress(20, "Markdown -> PDF")
    text = ctx.input_path.read_text(encoding="utf-8", errors="replace")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    w = pdf.epw
    for line in _md_to_text_lines(text):
        if not line:
            pdf.ln(4)
            continue
        try:
            pdf.multi_cell(w, 6, line)
        except Exception:
            pdf.multi_cell(w, 6, line.encode("latin-1", "replace").decode("latin-1"))
    pdf.output(str(ctx.output_path))
    ctx.set_progress(100, "Termine")


def _md_to_docx(ctx: ConvertContext) -> None:
    ctx.set_progress(20, "Markdown -> Word via LibreOffice")
    text = ctx.input_path.read_text(encoding="utf-8", errors="replace")
    html = _md_to_html(text)
    tmp_html = ctx.output_path.with_suffix(".html")
    tmp_html.write_text(html, encoding="utf-8")
    outdir = tempfile.mkdtemp()
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    try:
        r = subprocess.run(
            [exe, "--headless", "--norestore", "--nolockcheck", "--convert-to", "docx", "--outdir", outdir, str(tmp_html)],
            capture_output=True, timeout=600,
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode("utf-8", "replace")[:500] or "LibreOffice a echoue")
        produced = os.listdir(outdir)
        if not produced:
            raise RuntimeError("Aucun fichier produit")
        shutil.move(os.path.join(outdir, produced[0]), ctx.output_path)
        ctx.set_progress(100, "Termine")
    finally:
        shutil.rmtree(outdir, ignore_errors=True)
        try:
            tmp_html.unlink()
        except OSError:
            pass
