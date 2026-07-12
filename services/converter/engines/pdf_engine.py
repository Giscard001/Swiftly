from .base import ConversionRoute, ConvertContext

try:
    import pypdf
    _PYPDF = True
except Exception:
    _PYPDF = False

try:
    from fpdf import FPDF
    _FPDF = True
except Exception:
    _FPDF = False

try:
    from weasyprint import HTML
    _WEASY = True
except Exception:
    # WeasyPrint nécessite des libs système (Pango, GDK-PixBuf) ; en cas d'absence
    # la route HTML -> PDF n'est simplement pas proposée.
    _WEASY = False

try:
    from docx import Document
    from docx.shared import Pt
    _DOCX = True
except Exception:
    _DOCX = False

NAME = "pdf"


def available() -> bool:
    return _PYPDF or _DOCX


def routes() -> list[ConversionRoute]:
    out: list[ConversionRoute] = []
    if _PYPDF:
        out.append(ConversionRoute("document", "pdf", "txt", NAME, _pdf_to_txt, "PDF -> Texte"))
        out.append(ConversionRoute("document", "pdf", "html", NAME, _pdf_to_html, "PDF -> HTML"))
    if _FPDF:
        out.append(ConversionRoute("document", "txt", "pdf", NAME, _txt_to_pdf, "Texte -> PDF"))
    if _WEASY:
        out.append(ConversionRoute("document", "html", "pdf", NAME, _html_to_pdf, "HTML -> PDF"))
    if _DOCX:
        out.append(ConversionRoute("document", "txt", "docx", NAME, _txt_to_docx, "Texte -> Word"))
    return out


def _pdf_to_txt(ctx: ConvertContext) -> None:
    ctx.set_progress(10, "Lecture du PDF")
    reader = pypdf.PdfReader(str(ctx.input_path))
    n = len(reader.pages)
    parts: list[str] = []
    for i, page in enumerate(reader.pages):
        parts.append(page.extract_text() or "")
        ctx.set_progress(int(10 + 85 * (i + 1) / max(n, 1)), f"Page {i + 1}/{n}")
    ctx.output_path.write_text("\n".join(parts), encoding="utf-8")
    ctx.set_progress(100, "Termine")


def _txt_to_pdf(ctx: ConvertContext) -> None:
    ctx.set_progress(10, "Generation du PDF")
    text = ctx.input_path.read_text(encoding="utf-8", errors="replace")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    lines = text.splitlines() or [""]
    for line in lines:
        try:
            pdf.multi_cell(0, 6, line)
        except Exception:
            pdf.multi_cell(0, 6, line.encode("latin-1", "replace").decode("latin-1"))
    pdf.output(str(ctx.output_path))
    ctx.set_progress(100, "Termine")


def _html_to_pdf(ctx: ConvertContext) -> None:
    """HTML -> PDF via WeasyPrint (rendu CSS fidèle)."""
    ctx.set_progress(10, "Lecture du HTML")
    html = ctx.input_path.read_text(encoding="utf-8", errors="replace")
    ctx.set_progress(40, "Rendu PDF (WeasyPrint)")
    HTML(string=html, base_url=str(ctx.input_path.parent)).write_pdf(str(ctx.output_path))
    ctx.set_progress(100, "Termine")


def _pdf_to_html(ctx: ConvertContext) -> None:
    """PDF -> HTML via pypdf : extraction du texte, une <section> par page.
    Rendu basique (pas de mise en forme avancée) mais sans binaire externe."""
    ctx.set_progress(10, "Lecture du PDF")
    reader = pypdf.PdfReader(str(ctx.input_path))
    n = len(reader.pages)
    import html as _html

    parts = [
        "<!DOCTYPE html>",
        '<html lang="fr"><head><meta charset="utf-8">',
        f"<title>Document converti ({n} page(s))</title>",
        '<style>body{font-family:sans-serif;max-width:800px;margin:2em auto;'
        "line-height:1.5}.page{margin-bottom:2em;padding:1em;"
        'border:1px solid #ddd;border-radius:6px;white-space:pre-wrap}</style>',
        "</head><body>",
    ]
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        parts.append(f'<section class="page" id="page-{i + 1}">')
        parts.append(_html.escape(text))
        parts.append("</section>")
        ctx.set_progress(int(10 + 85 * (i + 1) / max(n, 1)), f"Page {i + 1}/{n}")
    parts.append("</body></html>")
    ctx.output_path.write_text("\n".join(parts), encoding="utf-8")
    ctx.set_progress(100, "Termine")


def _txt_to_docx(ctx: ConvertContext) -> None:
    """Texte -> Word (.docx) via python-docx. Chaque ligne devient un paragraphe."""
    ctx.set_progress(10, "Generation du document Word")
    text = ctx.input_path.read_text(encoding="utf-8", errors="replace")
    doc = Document()
    # Style par défaut
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    lines = text.splitlines() or [""]
    for i, line in enumerate(lines):
        p = doc.add_paragraph(line)
        ctx.set_progress(int(10 + 85 * (i + 1) / max(len(lines), 1)), f"Ligne {i + 1}/{len(lines)}")
    doc.save(str(ctx.output_path))
    ctx.set_progress(100, "Termine")
