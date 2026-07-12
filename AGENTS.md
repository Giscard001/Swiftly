# AGENTS.md — commands & conventions for this repo

## Stack
- Frontend: Next.js 15 (App Router, TypeScript, Tailwind) in `web/`
- Backend: FastAPI (Python) conversion microservice in `services/converter/`
- Job queue: in-process ThreadPoolExecutor + SQLite job store (swap to RQ/Celery+Redis later)
- Storage: local `storage/` dir, auto-deleted after 1h

## Setup (first time)
```
npm run setup          # installs web deps + creates Python venv + base pip deps
# optional, unlocks 7z / OCR:
npm run setup:api:optional
```
Then copy `.env.example` to `.env` (and `services/converter/.env` if overriding defaults).

## Run (both services)
```
npm run dev            # web :3000 + api :8000 (concurrently)
```
Run one at a time: `npm run dev:web` / `npm run dev:api`

## Checks (run before considering work done)
```
npm run typecheck      # tsc --noEmit in web/
npm run lint           # next lint in web/
```
Python service has no linter wired; keep it clean and PEP8-ish.

## Env
- `CONVERTER_URL` (web) → FastAPI base URL, default http://127.0.0.1:8000
- `CONV_*` (api) → storage dir, retention, size limit, CORS

## Binaries (optional, enable more conversions)
- LibreOffice (`soffice`) → Office↔PDF / Office↔Office
- FFmpeg (`ffmpeg`) → audio/video conversion, video→mp3, video→gif
- Tesseract (`tesseract`) → OCR (image→text)
The service probes these at startup; missing ones are simply disabled. See README for install.
