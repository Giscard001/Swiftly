#!/usr/bin/env python3
import io
import json
import time
import uuid
import zipfile

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from .. import jobs, security, storage
from ..config import settings
from ..ratelimit import rate_limit

router = APIRouter()

_OPS = {"merge", "split", "compress"}


@router.post("/operations/{op}")
@rate_limit()
async def operation(
    request: Request,
    op: str,
    files: list[UploadFile] = File(...),
    options: str = Form(None),
):
    if op not in _OPS:
        raise HTTPException(400, "Operation inconnue")
    if not files:
        raise HTTPException(400, "Aucun fichier fourni")
    if op == "split" and len(files) != 1:
        raise HTTPException(400, "Le decoupage n'accepte qu'un seul PDF")
    if op == "merge" and not all(security.split_ext(security.sanitize_filename(f.filename or "")) == "pdf" for f in files):
        raise HTTPException(400, "La fusion n'accepte que des PDF")

    job_id = uuid.uuid4().hex
    storage.ensure_job_dir(job_id)
    limit = settings.limit_for()
    total = 0
    for i, f in enumerate(files):
        data = await f.read()
        total += len(data)
        if total > limit:
            storage.cleanup_job(job_id)
            raise HTTPException(413, f"Total trop volumineux (limite {limit // 1024 // 1024} Mo)")
        name = security.sanitize_filename(f.filename or f"file_{i}")
        ext = security.split_ext(name)
        if ext not in security.ALLOWED_EXTENSIONS:
            storage.cleanup_job(job_id)
            raise HTTPException(400, f"Extension non supportee: .{ext}")
        in_path = storage.job_dir(job_id) / f"input_{i}.{ext}"
        in_path.write_bytes(data)
        # Validation du contenu réel vs extension déclarée.
        ok, msg = security.validate_upload(in_path, ext)
        if not ok:
            storage.cleanup_job(job_id)
            raise HTTPException(400, msg)

    opts: dict = {}
    if options:
        try:
            opts = json.loads(options)
        except Exception:
            opts = {}

    out_name = {"merge": "merged.pdf", "split": "pages.zip", "compress": "compressed"}[op]
    now = time.time()
    jobs.create_job(
        id=job_id,
        kind="operation",
        operation=op,
        category="operation",
        source=security.split_ext(security.sanitize_filename(files[0].filename or "")),
        target=None,
        status="queued",
        progress=0,
        message="En attente",
        input_name=",".join(security.sanitize_filename(f.filename or "") for f in files),
        output_name=out_name,
        error=None,
        options=json.dumps(opts),
        user_email=None,
        plan="free",
        size_bytes=total,
        created_at=now,
        updated_at=now,
        expires_at=now + settings.retention_seconds,
    )
    jobs.enqueue(job_id)
    return {"job_id": job_id, "status": "queued", "expires_at": now + settings.retention_seconds}


def run_operation(job_id: str, op: str, options: dict, set_progress) -> None:
    import pypdf
    from PIL import Image

    d = storage.job_dir(job_id)
    inputs = sorted(d.glob("input_*"))

    if op == "merge":
        set_progress(20, "Fusion PDF")
        writer = pypdf.PdfWriter()
        for p in inputs:
            reader = pypdf.PdfReader(str(p))
            for page in reader.pages:
                writer.add_page(page)
        with open(storage.output_path(job_id, "merged.pdf"), "wb") as f:
            writer.write(f)

    elif op == "split":
        set_progress(20, "Decoupage PDF")
        reader = pypdf.PdfReader(str(inputs[0]))
        n = len(reader.pages)
        zp = storage.output_path(job_id, "pages.zip")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for i, page in enumerate(reader.pages):
                w = pypdf.PdfWriter()
                w.add_page(page)
                buf = io.BytesIO()
                w.write(buf)
                z.writestr(f"page_{i + 1}.pdf", buf.getvalue())
                set_progress(int(20 + 75 * (i + 1) / max(n, 1)), f"Page {i + 1}/{n}")

    elif op == "compress":
        src = inputs[0]
        ext = src.name.split(".", 1)[1].lower() if "." in src.name else ""
        if ext == "pdf":
            set_progress(20, "Compression PDF")
            reader = pypdf.PdfReader(str(src))
            writer = pypdf.PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            try:
                writer.compress_identical_objects()
            except Exception:
                pass
            out = storage.output_path(job_id, "compressed.pdf")
            with open(out, "wb") as f:
                writer.write(f)
            jobs.update_output_name(job_id, "compressed.pdf")
        else:
            set_progress(20, "Compression image")
            img = Image.open(src)
            if ext in ("jpg", "jpeg") and img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            out = storage.output_path(job_id, f"compressed.{ext}")
            kwargs: dict = {"quality": int(options.get("quality", 70))}
            if ext == "png":
                kwargs = {"optimize": True}
            img.save(out, **kwargs)
            jobs.update_output_name(job_id, f"compressed.{ext}")

    set_progress(100, "Termine")
