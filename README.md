# FilesConvert

Plateforme de conversion de fichiers tout-en-un (documents, images, audio, vidéo, archives, données). Next.js 15 côté UI + microservice FastAPI (Python) pour le traitement. Aucune inscription requise.

> MVP fonctionnel. Le cœur (images, PDF↔texte/HTML/Office, fusion/split/compression PDF, données, archives, OCR) fonctionne avec de simples paquets pip. Office / vidéo / audio / OCR s'activent dès que vous installez LibreOffice / FFmpeg / Tesseract — le service les détecte au démarrage.

## Démarrage rapide

```bash
npm run setup          # installe web + crée le venv Python + pip install de base
npm run dev            # web :3000 + api :8000 (concurrently)
```

Puis ouvrez http://localhost:3000.

Pour activer plus de conversions (optionnel) :
```bash
npm run setup:api:optional   # py7zr (7z), pytesseract (OCR), pillow-heif (HEIC), pdf2image (poppler)
```
Et installez les binaires système (voir « Binaires » plus bas).

Pour activer les conversions PDF→Office (pdf2docx, pdfplumber, python-pptx) et HTML→PDF (WeasyPrint) :
```bash
cd services/converter && .venv/Scripts/python.exe -m pip install -r requirements-optional.txt
```

### Lancer un seul service
```bash
npm run dev:web
npm run dev:api
```

### Vérifs
```bash
npm run typecheck      # tsc --noEmit (web/)
npm run lint           # next lint (web/)
npm run build          # build prod Next.js
```

## Architecture

```
Navigateur ──► Next.js (web :3000)  ──fetch──► FastAPI (api :8000)
              App Router, Tailwind,                Routes /convert, /jobs,
              dark/light, sélecteur intelligent   /operations, /capabilities
                                                  │
                                                  ├─ ThreadPoolExecutor (2 workers)
                                                  ├─ SQLite (jobs.sqlite)
                                                  └─ storage/  (1 dossier/job, auto-delete 1h)

Engines (tous conditionnels : available() = import + shutil.which)
  images.py      Pillow + cairosvg   jpg/png/webp/gif/bmp/tiff ↔ + image→pdf (+HEIC), svg→image/pdf
  pdf_engine.py  pypdf + fpdf2 + WeasyPrint + python-docx  pdf→txt, txt→pdf, txt→docx, pdf→html, html→pdf
  pdf_office.py  pdf2docx + pdfplumber + python-pptx  pdf→docx, pdf→xlsx, pdf→pptx
  pdf_images.py  pdf2image+poppler  pdf→png, pdf→jpg (pages)
  ocr_pdf.py      pytesseract+pdf2image  pdf→txt (OCR)
  markdown_engine.py  fpdf2 + soffice  md→html, md→pdf, md→docx
  data.py         openpyxl + fpdf2 + stdlib csv/json/xlsx/xml ↔ + →pdf
  archives.py     stdlib + py7zr + unrar  zip/tar/tar.gz/tar.bz2/tar.xz/7z ↔ ; rar→ (extraction)
  office.py       LibreOffice       docx/pptx/xlsx/odt/... → pdf/txt/html + inter-office + docx↔pptx (bridge)
  av.py           FFmpeg             audio ↔, vidéo ↔, vidéo→mp3, vidéo→gif
  ocr.py          Tesseract + pytesseract  image→txt
```

**Files de traitement** : `ThreadPoolExecutor(max_workers=2)` + table SQLite `jobs`. chaque job a un statut (`queued|processing|completed|failed|expired`) et une `progress` 0-100. L'UI poll `/jobs/{id}` toutes 1.5s.
- Upgrade path vers queue distribuée : remplacer `jobs.enqueue`/`run_job` par RQ ou Celery+Redis. L'interface moteur (`available()`/`routes()`/`handler`) reste inchangée.

**Sélecteur intelligent** : `/capabilities` renvoie `by_source[ext] = [{category,target,label}]`. L'UI détecte l'extension du fichier déposé et ne propose que les cibles pertinentes, regroupées par catégorie.

## Structure du projet

```
files_convert/
├── package.json            workspaces ["web"], scripts, concurrently
├── .env.example            variables d'env
├── AGENTS.md               conventions & commandes
├── storage/                fichiers temporaires (ignoré, auto-delete 1h)
├── services/converter/     microservice FastAPI
│   ├── requirements.txt / requirements-optional.txt
│   ├── config.py            CONV_* (stockage, rétention, limite de taille, CORS)
│   ├── security.py         allowlist extensions, sanitize filename, validate MIME, split_ext
│   ├── storage.py          dossiers de job, sweep orphelins
│   ├── jobs.py             SQLite + ThreadPoolExecutor + run_job
│   ├── capabilities.py     registry + probe binaires/libs → /capabilities
│   ├── ratelimit.py         slowapi rate-limiter par IP
│   ├── engines/             11 moteurs (voir Architecture)
│   ├── routes/              capabilities, convert, jobs, operations
│   └── main.py              app, CORS, sweeper thread auto-delete 1h
└── web/                    Next.js 15 (App Router, TS, Tailwind)
    ├── app/                 layout, page(home), convert, dashboard, pricing, api-docs
    ├── components/          Navbar, Footer, ThemeToggle, Dropzone, FormatSelector, ConversionProgress
    └── lib/                 converter-client, formats, utils
```

## API REST

Base URL (dev) : `http://127.0.0.1:8000`

| Méthode | Route | Description |
|--------|-------|-------------|
| GET  | `/health` | Healthcheck |
| GET  | `/capabilities` | Conversions disponibles selon binaires/libs détectés |
| POST | `/convert` | multipart: `file`, `target`, `category?`, `options?` → `{job_id}` |
| POST | `/operations/{op}` | op ∈ `merge`·`split`·`compress`, multipart `files` → `{job_id}` |
| GET  | `/jobs/{id}` | Statut + progression |
| GET  | `/jobs/{id}/download` | Fichier converti (binaire) |
| GET  | `/jobs?limit=50` | Historique récent |

Exemple :
```bash
curl -F file=@photo.png -F target=jpg http://127.0.0.1:8000/convert
# => {"job_id":"...","status":"queued","expires_at":...}
curl http://127.0.0.1:8000/jobs/<job_id>
curl -OJ http://127.0.0.1:8000/jobs/<job_id>/download
```

## Prise en charge des formats

| Catégorie | Conversions | Dépendance |
|-----------|-------------|-----------|
| Image | jpg/png/webp/gif/bmp/tiff ↔ + image→pdf ; HEIC→ (optionnel) ; **SVG→ image/pdf** (optionnel) | Pillow (pip) ; cairosvg (optionnel) |
| Document | pdf→txt, txt→pdf, **txt→docx**, pdf→html, html→pdf ; **Office** docx/pptx/xlsx/odt/ods/odp/rtf → pdf/txt/html + inter-office ; **docx↔pptx** (bridge 2 passes) | pypdf, fpdf2, python-docx ; LibreOffice |
| PDF→Office | pdf→docx, pdf→xlsx, pdf→pptx | pdf2docx, pdfplumber, python-pptx (optionnel) |
| PDF→images | pdf→png, pdf→jpg (1 page ou zip de pages) | pdf2image + poppler (optionnel) |
| Markdown | md→html, md→pdf, md→docx | fpdf2 ; LibreOffice (docx) |
| Opérations PDF | fusion, découpage (zip de pages), compression (réenregistrement + compress_identical_objects) | pypdf |
| Données | csv/json/xlsx/xml ↔ ; **csv/json/xlsx/xml → PDF** | openpyxl + fpdf2 + stdlib |
| Archive | zip/tar/tar.gz/tar.bz2/tar.xz/7z ↔ ; rar→ extraction (optionnel) | stdlib + py7zr ; unrar |
| Audio | mp3/wav/flac/aac/ogg/m4a ↔ | FFmpeg |
| Vidéo | mp4/avi/mov/mkv/webm ↔ ; vidéo→mp3 ; vidéo→gif | FFmpeg |
| OCR | image(png/jpg/tiff/bmp/webp)→txt ; pdf→txt (OCR) | Tesseract + pytesseract + poppler |

Limites de périmètre (documentés) :
- **PDF→Office** : pdf2docx/docx préserve bien la mise en page ; pdfplumber/xlsx extrait tableaux (fallback texte) ; python-pptx/pptx produit des slides-images (non éditables). Requiert les deps optionnelles.
- **HTML→PDF** : WeasyPrint (rendu CSS fidèle). Requiert GTK/Pango au niveau système — fragile sur Windows.
- **docx↔pptx** : conversion en 2 passes via ODP intermédiaire (LibreOffice). La fidélité est limitée (Word→PowerPoint est fondamentalement imparfait : la structure n'est pas équivalente).
- **SVG→image/PDF** : cairosvg (rendu vectoriel fidèle). Requiert cairo natif — fragile sur Windows.
- **Auth / users** : non couverts (plateforme ouverte sans inscription).
- **Chiffrement au repos** : non implémenté (voir Sécurité).

## Binaires (optionnels, activent plus de conversions)

Le service les détecte automatiquement au démarrage via `shutil.which` ; s'ils sont absents, les routes correspondantes restent masquées côté UI.

### Windows
- **LibreOffice** : https://www.libreoffice.org/download/ → installe, puis ajoute `C:\Program Files\LibreOffice\program` au `PATH` (le binaire cherché est `soffice.exe`).
- **FFmpeg** : https://www.gyan.dev/ffmpeg/builds/ → dézippe, ajoute le dossier `bin` au `PATH` (`ffmpeg.exe`).
- **Tesseract** : https://github.com/UB-Mannheim/tesseract/wiki → installe, ajoute au `PATH` (`tesseract.exe`).
- **UnRAR** : https://www.rarlab.com/download.htm → installe, ajoute au `PATH` (`unrar.exe`). Active les conversions `rar → zip/tar/...` (extraction seulement).

### macOS
```bash
brew install --cask libreoffice
brew install ffmpeg tesseract unrar
```

### Linux (Debian/Ubuntu)
```bash
sudo apt install libreoffice ffmpeg tesseract-ocr unrar
```

> **WeasyPrint** (HTML→PDF) nécessite des bibliothèques système (GTK3, Pango, GDK-PixBuf). Sur Linux : `sudo apt install libpango-1.0-0 libharfbuzz0b libgdk-pixbuf2.0-0`. Sur Windows/macOS, cf. https://doc.courtbouillon.org/weasyprint/stable/first_steps.html

Vérifiez la détection :
```bash
curl http://127.0.0.1:8000/capabilities | python -m json.tool | grep binaries
```

## Sécurité

Implémenté :
- **Allowlist d'extensions** côté service (`security.ALLOWED_EXTENSIONS`). Les extensions sans moteur/binaire sont retirées dynamiquement (ex : `rar` si `unrar` absent).
- **Validation MIME / magic-bytes** : le contenu réel du fichier est vérifié contre l'extension déclarée avant la conversion. Les fichiers renommés (ex : `.pdf` contenant du texte) sont rejetés.
- **Sanitization des noms** : anti path traversal, normalisation Unicode, cap de longueur 200 chars, retrait des caractères de contrôle.
- **Protection zip-slip / tarbomb** : les chemins dans les archives (zip/tar/7z) sont validés avant extraction. Les liens symboliques et entrées device sont rejetés.
- **Rate-limiting par IP** : SlowAPI sur `/convert` et `/operations`, configurable via `CONV_RATE_LIMIT` (défaut 30 req/min).
- **Limite de taille** unique (défaut 2 Go), configurable via `CONV_MAX_FILE_SIZE`.
- **Stockage hors dossier web** (`storage/` à la racine, jamais servi statiquement).
- **IDs de job aléatoires** (`uuid4.hex`), fichiers servis uniquement via `/jobs/{id}/download` après vérification du statut.
- **Suppression automatique** des fichiers après 1h (sweeper thread : `jobs.expire_old` + `storage.sweep_orphans`).
- **CORS** restreint (`CONV_CORS_ORIGINS`, défaut `http://localhost:3000`).

Recommandé pour la mise en production :
- **TLS** : terminaison HTTPS (Caddy/NGINX/Cloudflare) devant les deux services ; jamais de HTTP en prod.
- **Anti-malware** : scan ClamAV des uploads avant conversion (hook dans `routes/convert.py`).
- **Chiffrement au repos** : Fernet/AES (clé dans le secret manager) ou KMS ; couche dans `storage.py`. L'auto-delete 1h couvre déjà une grande partie du risque.
- **Logs d'audit** des conversions (sans contenu) + rotation.

## Limite de taille

Voir `.env.example` (`CONV_MAX_FILE_SIZE`). Par défaut : 2 Go / fichier. Usage perso / proches — pas de plans ni de monétisation.

## Variables d'environnement

| Variable | Service | Défaut | Rôle |
|----------|---------|--------|------|
| `CONV_STORAGE_DIR` | api | `./storage` | Dossier de stockage temporaire |
| `CONV_RETENTION_SECONDS` | api | `3600` | Durée avant suppression (1h) |
| `CONV_CORS_ORIGINS` | api | `http://localhost:3000` | Origines CORS (CSV) |
| `CONV_MAX_FILE_SIZE` | api | `2147483648` (2 Go) | Taille max par fichier |
| `CONV_RATE_LIMIT` | api | `30/minute` | Rate-limit par IP (format slowapi) |
| `CONVERTER_URL` | web | `http://127.0.0.1:8000` | URL du microservice |

## Notes sur le dev

- `npm run dev:api` lance uvicorn avec `--reload` : la DB `jobs.sqlite` persiste mais les jobs en cours sont perdus à une recharge (worker en mémoire). Acceptable en dev.
- `--app-dir services` + target `converter.main:app` : nécessaire car les imports sont relatifs (`from . import jobs`).
