#!/usr/bin/env python3
import json
import time
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from .. import jobs, security, storage
from ..capabilities import find_route
from ..config import settings
from ..ratelimit import rate_limit

router = APIRouter()


def _make_job(data: bytes, filename: str, target: str, category: str | None, options: dict, batch_id: str | None = None) -> tuple[str, str, dict]:
    src_ext = security.split_ext(filename)
    if len(data) == 0:
        raise HTTPException(400, "Fichier vide")
    if src_ext not in security.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Extension non supportee: .{src_ext}")
    route = find_route(src_ext, target, category, prefer_ocr=bool((options or {}).get("ocr")))
    if not route:
        raise HTTPException(
            400,
            f"Conversion .{src_ext} -> .{target} non disponible (binaire ou dependance manquant ?)",
        )

    job_id = uuid.uuid4().hex
    storage.ensure_job_dir(job_id)
    in_path = storage.input_path(job_id, src_ext)
    in_path.write_bytes(data)

    # Validation du contenu réel (magic-bytes) vs extension déclarée.
    ok, msg = security.validate_upload(in_path, src_ext)
    if not ok:
        storage.cleanup_job(job_id)
        raise HTTPException(400, msg)

    out_name = f"output.{target}"
    now = time.time()
    jobs.create_job(
        id=job_id,
        kind="convert",
        operation=None,
        batch_id=batch_id,
        category=route.category,
        source=src_ext,
        target=target,
        status="queued",
        progress=0,
        message="En attente",
        input_name=filename,
        output_name=out_name,
        error=None,
        options=json.dumps(options or {}),
        user_email=None,
        plan="free",
        size_bytes=len(data),
        created_at=now,
        updated_at=now,
        expires_at=now + settings.retention_seconds,
    )
    jobs.enqueue(job_id)
    return job_id, src_ext, {"job_id": job_id, "input_name": filename, "target": target}


@router.post("/convert")
@rate_limit()
async def convert(
    request: Request,
    file: UploadFile = File(...),
    target: str = Form(...),
    category: str = Form(None),
    options: str = Form(None),
):
    data = await file.read()
    limit = settings.limit_for()
    if len(data) > limit:
        raise HTTPException(413, f"Fichier trop volumineux (limite {limit // 1024 // 1024} Mo)")
    filename = security.sanitize_filename(file.filename or "file")
    opts: dict = {}
    if options:
        try:
            opts = json.loads(options)
        except Exception:
            opts = {}
    job_id, _, payload = _make_job(data, filename, target, category, opts, batch_id=None)
    payload["status"] = "queued"
    payload["expires_at"] = time.time() + settings.retention_seconds
    return payload


@router.post("/convert/batch")
@rate_limit()
async def convert_batch(
    request: Request,
    files: list[UploadFile] = File(...),
    target: str = Form(...),
    category: str = Form(None),
    options: str = Form(None),
):
    if not files:
        raise HTTPException(400, "Aucun fichier fourni")
    limit = settings.limit_for()
    opts: dict = {}
    if options:
        try:
            opts = json.loads(options)
        except Exception:
            opts = {}

    batch_id = uuid.uuid4().hex
    total = 0
    created: list[dict] = []
    for f in files:
        data = await f.read()
        total += len(data)
        if total > limit:
            raise HTTPException(413, f"Total trop volumineux (limite {limit // 1024 // 1024} Mo)")
        filename = security.sanitize_filename(f.filename or f"file_{len(created)}")
        try:
            job_id, _, item = _make_job(data, filename, target, category, opts, batch_id=batch_id)
            created.append(item)
        except HTTPException as e:
            # nettoyer les jobs deja crees du batch avant d'echouer
            for it in created:
                storage.cleanup_job(it["job_id"])
            raise
    return {
        "batch_id": batch_id,
        "count": len(created),
        "jobs": created,
        "expires_at": time.time() + settings.retention_seconds,
    }
