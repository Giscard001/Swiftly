import json
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .config import settings

_DB = settings.storage_dir.parent / "jobs.sqlite"
_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=2)


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(_DB), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _lock:
        c = _conn()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                operation TEXT,
                batch_id TEXT,
                category TEXT,
                source TEXT,
                target TEXT,
                status TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                message TEXT,
                input_name TEXT,
                output_name TEXT,
                error TEXT,
                options TEXT,
                user_email TEXT,
                plan TEXT DEFAULT 'free',
                size_bytes INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                expires_at REAL NOT NULL
            )
            """
        )
        try:
            c.execute("ALTER TABLE jobs ADD COLUMN batch_id TEXT")
        except sqlite3.OperationalError:
            pass
        c.commit()
        c.close()


def create_job(**kw) -> None:
    cols = ",".join(kw.keys())
    ph = ",".join("?" for _ in kw)
    with _lock:
        c = _conn()
        c.execute(f"INSERT INTO jobs ({cols}) VALUES ({ph})", tuple(kw.values()))
        c.commit()
        c.close()


def get_job(job_id: str) -> dict | None:
    with _lock:
        c = _conn()
        row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        c.close()
    return dict(row) if row else None


def list_jobs(
    user_email: str | None = None,
    batch_id: str | None = None,
    limit: int = 50,
) -> list[dict]:
    with _lock:
        c = _conn()
        if batch_id:
            rows = c.execute(
                "SELECT * FROM jobs WHERE batch_id=? ORDER BY created_at ASC LIMIT ?",
                (batch_id, limit),
            ).fetchall()
        elif user_email:
            rows = c.execute(
                "SELECT * FROM jobs WHERE user_email=? ORDER BY created_at DESC LIMIT ?",
                (user_email, limit),
            ).fetchall()
        else:
            rows = c.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        c.close()
    return [dict(r) for r in rows]


def update_status(job_id: str, status: str | None = None, error: str | None = None, message: str | None = None) -> None:
    sets, vals = [], []
    if status is not None:
        sets.append("status=?")
        vals.append(status)
    if error is not None:
        sets.append("error=?")
        vals.append(error)
    if message is not None:
        sets.append("message=?")
        vals.append(message)
    if not sets:
        return
    sets.append("updated_at=?")
    vals.append(time.time())
    vals.append(job_id)
    with _lock:
        c = _conn()
        c.execute(f"UPDATE jobs SET {','.join(sets)} WHERE id=?", vals)
        c.commit()
        c.close()


def update_progress(job_id: str, progress: int, message: str = "") -> None:
    with _lock:
        c = _conn()
        c.execute(
            "UPDATE jobs SET progress=?, message=?, updated_at=? WHERE id=?",
            (progress, message, time.time(), job_id),
        )
        c.commit()
        c.close()


def update_output_name(job_id: str, name: str) -> None:
    with _lock:
        c = _conn()
        c.execute("UPDATE jobs SET output_name=?, updated_at=? WHERE id=?", (name, time.time(), job_id))
        c.commit()
        c.close()


def expire_old(retention_seconds: int) -> None:
    from . import storage
    now = time.time()
    with _lock:
        c = _conn()
        rows = c.execute(
            "SELECT id FROM jobs WHERE expires_at < ? AND status NOT IN ('expired')",
            (now,),
        ).fetchall()
        c.close()
    for r in rows:
        storage.cleanup_job(r["id"])
        update_status(r["id"], status="expired", message="Fichier supprimé (rétention 1h dépassée)")


def enqueue(job_id: str) -> None:
    _executor.submit(run_job, job_id)


def shutdown() -> None:
    _executor.shutdown(wait=False, cancel_futures=True)


def run_job(job_id: str) -> None:
    from . import storage
    from .capabilities import find_route
    from .engines.base import ConvertContext

    j = get_job(job_id)
    if not j:
        return
    update_status(job_id, status="processing", message="Démarrage")
    update_progress(job_id, 5, "Préparation")
    set_progress = lambda p, m="": update_progress(job_id, p, m)
    try:
        options = json.loads(j["options"] or "{}")
        if j["kind"] == "convert":
            route = find_route(j["source"], j["target"], j["category"])
            if not route:
                raise RuntimeError(f"Conversion .{j['source']} → .{j['target']} non disponible")
            in_path = storage.job_dir(job_id) / f"input.{j['source']}"
            out_path = storage.output_path(job_id, j["output_name"])
            ctx = ConvertContext(job_id, j["source"], j["target"], in_path, out_path, options, set_progress)
            route.handler(ctx)
        else:
            from .routes.operations import run_operation

            run_operation(job_id, j["operation"], options, set_progress)
        update_progress(job_id, 100, "Terminé")
        update_status(job_id, status="completed", message="Terminé")
    except Exception as e:
        update_status(job_id, status="failed", error=str(e)[:500], message="Échec de la conversion")
