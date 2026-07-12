import shutil
import time
from pathlib import Path

from .config import settings


def job_dir(job_id: str) -> Path:
    return settings.storage_dir / job_id


def ensure_job_dir(job_id: str) -> Path:
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def input_path(job_id: str, ext: str) -> Path:
    return job_dir(job_id) / f"input.{ext}"


def output_path(job_id: str, name: str) -> Path:
    return job_dir(job_id) / name


def cleanup_job(job_id: str) -> None:
    shutil.rmtree(job_dir(job_id), ignore_errors=True)


def sweep_orphans(max_age_seconds: int) -> None:
    if not settings.storage_dir.exists():
        return
    now = time.time()
    for d in settings.storage_dir.iterdir():
        try:
            if d.is_dir() and now - d.stat().st_mtime > max_age_seconds:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass
