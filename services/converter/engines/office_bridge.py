"""Conversions docx <-> pptx via python-docx + python-pptx.

LibreOffice ne sait pas convertir directement docx<->pptx (le bridge via ODP
échoue en silence). On utilise ici les bibliothèques Python dédiées :
  - docx -> pptx : lire les paragraphes du docx, créer un slide par paragraphe titre
  - pptx -> docx : lire le texte des slides, créer un paragraphe docx par slide

La fidélité est limitée (Word et PowerPoint n'ont pas la même structure),
mais la conversion est robuste et préserve le texte.
"""
from .base import ConversionRoute, ConvertContext

try:
    from docx import Document
    _DOCX = True
except Exception:
    _DOCX = False

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    _PPTX = True
except Exception:
    _PPTX = False

NAME = "office_bridge"


def available() -> bool:
    return _DOCX and _PPTX


def routes() -> list[ConversionRoute]:
    if not available():
        return []
    return [
        ConversionRoute("document", "docx", "pptx", NAME, _docx_to_pptx, "DOCX -> PPTX"),
        ConversionRoute("document", "pptx", "docx", NAME, _pptx_to_docx, "PPTX -> DOCX"),
    ]


def _docx_to_pptx(ctx: ConvertContext) -> None:
    """Word -> PowerPoint : un slide par titre de section + ses paragraphes.
    Si le document n'a pas de titres, on crée un slide par groupe de paragraphes."""
    ctx.set_progress(10, "Lecture du document Word")
    doc = Document(str(ctx.input_path))

    # Récupère les paragraphes avec leur style
    paragraphs = []
    for p in doc.paragraphs:
        text = (p.text or "").strip()
        if not text:
            continue
        is_heading = p.style is not None and "Heading" in (p.style.name or "")
        paragraphs.append((text, is_heading))
    if not paragraphs:
        raise RuntimeError("Document Word vide (aucun paragraphe de texte)")

    ctx.set_progress(30, "Construction des slides")
    prs = Presentation()
    # Utilise le layout par défaut "Title and Content" (index 1) s'il existe, sinon blank (6)
    title_layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[6]
    blank_layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]

    # Groupe les paragraphes : un nouveau slide démarre à chaque titre (ou tous les ~6 paragraphes)
    slides_content: list[tuple[str, list[str]]] = []
    current_title = ""
    current_body: list[str] = []

    for text, is_heading in paragraphs:
        if is_heading or (not current_title and not current_body):
            if current_title or current_body:
                slides_content.append((current_title, current_body))
            current_title = text
            current_body = []
        else:
            current_body.append(text)
            # découpe les longues sections sans titre
            if len(current_body) >= 8 and not is_heading:
                slides_content.append((current_title, current_body))
                current_title = ""
                current_body = []
    if current_title or current_body:
        slides_content.append((current_title, current_body))

    if not slides_content:
        slides_content = [("", [p[0] for p in paragraphs[:10]])]

    total = len(slides_content)
    for i, (title, body) in enumerate(slides_content):
        layout = title_layout if title else blank_layout
        slide = prs.slides.add_slide(layout)
        # Place le titre
        if slide.shapes.title:
            slide.shapes.title.text = title[:200] or f"Section {i + 1}"
        # Place le corps dans le premier placeholder de contenu (ou une zone de texte)
        body_text = "\n".join(body)[:1500]
        if body_text:
            content_ph = None
            for ph in slide.placeholders:
                if ph.placeholder_format.idx == 1:  # placeholder "body"
                    content_ph = ph
                    break
            if content_ph:
                content_ph.text = body_text
            else:
                # fallback : ajouter une textbox
                txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(5))
                txBox.text_frame.text = body_text
        ctx.set_progress(int(30 + 65 * (i + 1) / max(total, 1)), f"Slide {i + 1}/{total}")

    ctx.set_progress(98, "Enregistrement")
    prs.save(str(ctx.output_path))
    ctx.set_progress(100, "Termine")


def _pptx_to_docx(ctx: ConvertContext) -> None:
    """PowerPoint -> Word : un titre de niveau 1 par slide + le texte en paragraphes."""
    ctx.set_progress(10, "Lecture de la présentation")
    prs = Presentation(str(ctx.input_path))
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    total = len(prs.slides)
    if total == 0:
        raise RuntimeError("Présentation vide (aucun slide)")

    for i, slide in enumerate(prs.slides):
        title = ""
        body_lines: list[str] = []
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            text = shape.text_frame.text.strip()
            if not text:
                continue
            # Heuristique : si c'est le titre du slide (placeholder idx 0)
            is_title = (
                shape.is_placeholder
                and shape.placeholder_format.idx == 0
            )
            if is_title and not title:
                title = text
            else:
                body_lines.append(text)

        heading = title or f"Slide {i + 1}"
        doc.add_heading(heading, level=1)
        for line in body_lines:
            for sub in line.splitlines():
                if sub.strip():
                    doc.add_paragraph(sub.strip())
        if not body_lines:
            doc.add_paragraph("(slide sans contenu textuel)")
        ctx.set_progress(int(10 + 85 * (i + 1) / total), f"Slide {i + 1}/{total}")

    ctx.set_progress(98, "Enregistrement")
    doc.save(str(ctx.output_path))
    ctx.set_progress(100, "Termine")
