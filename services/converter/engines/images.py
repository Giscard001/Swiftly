from .base import ConversionRoute, ConvertContext

try:
    from PIL import Image
    _PIL = True
except Exception:
    _PIL = False

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    _HEIF = True
except Exception:
    _HEIF = False

try:
    import cairosvg
    _CAIRO = True
except Exception:
    _CAIRO = False

NAME = "images"
_IMG = ["jpg", "jpeg", "png", "webp", "gif", "bmp", "tiff", "tif"]
_PIL_FMT = {
    "jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP",
    "gif": "GIF", "bmp": "BMP", "tiff": "TIFF", "tif": "TIFF", "pdf": "PDF",
}


def available() -> bool:
    return _PIL or _CAIRO


def routes() -> list[ConversionRoute]:
    srcs = list(_IMG)
    if _HEIF:
        srcs.append("heic")
    out: list[ConversionRoute] = []
    for s in srcs:
        for t in _IMG:
            if t == s:
                continue
            if s == "heic" and t in ("tiff", "tif", "gif", "bmp"):
                continue
            out.append(ConversionRoute("image", s, t, NAME, _convert, f"{s.upper()} -> {t.upper()}"))
        out.append(ConversionRoute("image", s, "pdf", NAME, _convert, f"{s.upper()} -> PDF"))
    # SVG -> raster via cairosvg
    if _CAIRO:
        for t in _IMG:
            out.append(ConversionRoute("image", "svg", t, NAME, _svg_to_image, f"SVG -> {t.upper()}"))
        out.append(ConversionRoute("image", "svg", "pdf", NAME, _svg_to_image, "SVG -> PDF"))
    return out


def _convert(ctx: ConvertContext) -> None:
    ctx.set_progress(10, "Ouverture de l'image")
    img = Image.open(ctx.input_path)
    opts = ctx.options or {}
    w = opts.get("width")
    h = opts.get("height")
    if w or h:
        nw = int(w) if w else img.width
        nh = int(h) if h else img.height
        img.thumbnail((nw, nh))
    target = ctx.target.lower()
    fmt = _PIL_FMT.get(target, target.upper())
    save_kwargs: dict = {}
    if target == "png":
        save_kwargs["optimize"] = True
    if target in ("jpg", "jpeg", "webp"):
        if target in ("jpg", "jpeg") and img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        save_kwargs["quality"] = int(opts.get("quality", 85))
    ctx.set_progress(60, "Enregistrement")
    img.save(ctx.output_path, format=fmt, **save_kwargs)
    ctx.set_progress(100, "Termine")


def _svg_to_image(ctx: ConvertContext) -> None:
    """SVG -> image raster ou PDF via cairosvg.
    Nécessite cairosvg + cairo (bibliothèque système)."""
    ctx.set_progress(10, "Lecture du SVG")
    svg_data = ctx.input_path.read_bytes()
    target = ctx.target.lower()
    opts = ctx.options or {}
    output_width = opts.get("width")
    output_height = opts.get("height")

    # cairosvg accepte pdf, png, ps, eps ; pour les autres formats raster
    # on passe d'abord par PNG puis on convertit via Pillow.
    cairo_formats = {"png", "pdf"}
    if target in cairo_formats:
        ctx.set_progress(50, f"Rendu SVG -> {target.upper()}")
        kw: dict = {}
        if output_width:
            kw["output_width"] = int(output_width)
        if output_height:
            kw["output_height"] = int(output_height)
        if target == "png":
            cairosvg.svg2png(bytestring=svg_data, write_to=str(ctx.output_path), **kw)
        elif target == "pdf":
            cairosvg.svg2pdf(bytestring=svg_data, write_to=str(ctx.output_path), **kw)
        ctx.set_progress(100, "Termine")
    else:
        # Rendu SVG -> PNG intermédiaire, puis conversion PIL vers le format cible
        ctx.set_progress(30, "Rendu SVG -> PNG (intermediaire)")
        import io
        png_bytes = cairosvg.svg2png(bytestring=svg_data)
        img = Image.open(io.BytesIO(png_bytes))
        if output_width or output_height:
            nw = int(output_width) if output_width else img.width
            nh = int(output_height) if output_height else img.height
            img.thumbnail((nw, nh))
        fmt = _PIL_FMT.get(target, target.upper())
        save_kw: dict = {}
        if target == "png":
            save_kw["optimize"] = True
        if target in ("jpg", "jpeg", "webp"):
            if target in ("jpg", "jpeg") and img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            save_kw["quality"] = int(opts.get("quality", 85))
        ctx.set_progress(70, f"Conversion PNG -> {target.upper()}")
        img.save(ctx.output_path, format=fmt, **save_kw)
        ctx.set_progress(100, "Termine")
