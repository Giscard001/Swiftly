from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from .. import jobs, storage

router = APIRouter()


@router.get("/jobs")
def list_jobs(limit: int = 50, batch_id: str | None = None):
    return {"jobs": jobs.list_jobs(None, batch_id, limit)}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    j = jobs.get_job(job_id)
    if not j:
        raise HTTPException(404, "Job introuvable")
    return j


@router.get("/jobs/{job_id}/download")
def download(job_id: str):
    j = jobs.get_job(job_id)
    if not j:
        raise HTTPException(404, "Job introuvable")
    if j["status"] != "completed":
        raise HTTPException(409, "Conversion non terminee")
    p = storage.output_path(job_id, j["output_name"])
    if not p.exists():
        raise HTTPException(410, "Fichier expire ou supprime")
    return FileResponse(p, filename=j["output_name"], media_type="application/octet-stream")
