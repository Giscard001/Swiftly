#!/usr/bin/env python3
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from . import jobs, storage
from .config import settings
from .ratelimit import limiter, rate_limit
from .routes import capabilities as cap_routes
from .routes import convert, jobs as job_routes, operations


def _sweeper():
    while True:
        try:
            jobs.expire_old(settings.retention_seconds)
            storage.sweep_orphans(settings.retention_seconds * 2)
        except Exception:
            pass
        time.sleep(settings.sweeper_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    jobs.init_db()
    t = threading.Thread(target=_sweeper, daemon=True)
    t.start()
    yield
    jobs.shutdown()


app = FastAPI(title="FilesConvert API", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(cap_routes.router)
app.include_router(convert.router)
app.include_router(job_routes.router)
app.include_router(operations.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "converter"}
