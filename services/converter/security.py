import re
import unicodedata
from pathlib import Path

COMPOUND = (".tar.gz", ".tar.bz2", ".tar.xz")

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "tif", "heic", "svg",
    "pdf", "txt", "html", "md",
    "docx", "doc", "pptx", "ppt", "xlsx", "xls", "odt", "ods", "odp", "rtf",
    "csv", "json", "xml",
    "zip", "tar", "tar.gz", "tar.bz2", "tar.xz", "7z", "rar",
    "mp3", "wav", "flac", "aac", "ogg", "m4a",
    "mp4", "avi", "mov", "mkv", "webm",
}

# RAR nécessite le binaire unrar (format propriétaire). Si unrar n'est pas
# présent, on retire 'rar' de l'allowlist pour éviter un 500 silencieux.
import shutil as _shutil
if not _shutil.which("unrar"):
    ALLOWED_EXTENSIONS.discard("rar")

# Extensions autorisées uniquement si le binaire unrar est présent à l'exécution
# (résolu dynamiquement ; voir routes/convert.py qui retire 'rar' de l'allowlist
# si unrar manque).

_MAX_NAME_LEN = 200

# Magic-bytes pour les formats clés. Chaque entrée : (signature, extensions compatibles).
# On compare l'extension déclarée à l'une des extensions compatibles sniffées.
_MAGIC_SIGNATURES = (
    (b"%PDF", ("pdf",)),
    (b"\xff\xd8\xff", ("jpg", "jpeg")),
    (b"\x89PNG\r\n\x1a\n", ("png",)),
    (b"GIF87a", ("gif",)),
    (b"GIF89a", ("gif",)),
    (b"BM", ("bmp",)),
    (b"II*\x00", ("tif", "tiff")),
    (b"MM\x00*", ("tif", "tiff")),
    (b"RIFF", ("webp", "wav", "avi")),  # affiné plus bas
    (b"\x1a\x45\xdf\xa3", ("mkv", "webm")),  # EBML/Matroska
    (b"ftyp", ("mp4", "mov")),  # offset 4 pour ISO BMFF
    (b"ID3", ("mp3",)),
    (b"\xff\xfb", ("mp3",)),
    (b"\xff\xf3", ("mp3",)),
    (b"\xff\xf2", ("mp3",)),
    (b"OggS", ("ogg",)),
    (b"fLaC", ("flac",)),
    (b"PK\x03\x04", ("zip",)),  # Office OOXML affiné plus bas en ouvrant le zip
    (b"7z\xbc\xaf\x27\x1c", ("7z",)),
    (b"Rar!\x1a\x07\x00", ("rar",)),
    (b"Rar!\x1a\x07\x01\x00", ("rar",)),
)

# Conteneurs ZIP : un .docx/.pptx/.xlsx/odt contient toujours [Content_Types].xml
_ZIP_OFFICE_MARKERS = {
    b"[Content_Types].xml",
    b"word/document.xml",
    b"xl/workbook.xml",
    b"ppt/presentation.xml",
}


def sanitize_filename(name: str) -> str:
    # 1) ne garder que le nom de fichier (supprime tout chemin)
    base = Path(name).name
    # 2) normaliser Unicode + retirer caractères de contrôle
    base = unicodedata.normalize("NFC", base)
    base = "".join(ch for ch in base if unicodedata.category(ch)[0] != "C" or ch in "\t ")
    # 3) retirer les points de début (cachait parfois des extensions trompeuses)
    base = base.lstrip(".")
    # 4) plafonner la longueur sans couper l'extension
    if len(base) > _MAX_NAME_LEN:
        stem, dot, suf = base.rpartition(".")
        if dot and len(suf) <= 24:
            base = stem[: _MAX_NAME_LEN - len(suf) - 1] + "." + suf
        else:
            base = base[:_MAX_NAME_LEN]
    return base or "file"


def split_ext(name: str) -> str:
    low = name.lower()
    for c in COMPOUND:
        if low.endswith(c):
            return c.lstrip(".")
    return Path(name).suffix.lower().lstrip(".")


def sniff_extensions(path: Path) -> set[str]:
    """Retourne les extensions compatibles avec le contenu réel du fichier,
    d'après ses magic-bytes. Ensemble vide = inconnu (on ne bloque pas tout seul)."""
    try:
        with open(path, "rb") as f:
            head = f.read(512)
    except OSError:
        return set()
    if not head:
        return set()

    found: set[str] = set()
    for sig, exts in _MAGIC_SIGNATURES:
        if head.startswith(sig):
            # affinages
            if sig == b"RIFF" and len(head) >= 12:
                fmt = head[8:12]
                if fmt == b"WEBP":
                    found.add("webp")
                elif fmt == b"WAVE":
                    found.add("wav")
                elif fmt == b"AVI ":
                    found.add("avi")
                else:
                    found.update(exts)
            elif sig == b"ftyp" and len(head) >= 8:
                # ISO BMFF : la marque "ftyp" est à l'offset 4
                if head[4:8] == b"ftyp":
                    found.update(("mp4", "mov", "m4a"))
            else:
                found.update(exts)

    # Distinguer un vrai ZIP d'un Office OOXML : si on a la signature PK,
    # on ouvre et on cherche les marqueurs XML internes.
    if head.startswith(b"PK"):
        found.discard("zip")  # retirer le zip générique, on affinera
        try:
            import zipfile

            with zipfile.ZipFile(path) as z:
                names = set(z.namelist())
                is_office = False
                if "word/document.xml" in names:
                    found.add("docx"); is_office = True
                if "xl/workbook.xml" in names:
                    found.add("xlsx"); is_office = True
                if "ppt/presentation.xml" in names:
                    found.add("pptx"); is_office = True
                if "content.xml" in names and "meta.xml" in names:
                    found.update(("odt", "ods", "odp")); is_office = True
                if not is_office:
                    found.add("zip")
        except Exception:
            # zip corrompu / trop petit : on garde zip comme hypothèse faible
            found.add("zip")

    # Cas texte : pas de magic-bytes ; si tout est imprimable, on propose txt/csv/json/xml/html/md
    if not found and _looks_like_text(head):
        sample = head.decode("utf-8", "ignore")
        found.update(_guess_text_format(sample))

    return found


def _looks_like_text(head: bytes) -> bool:
    if not head:
        return False
    # accepte NULL binaire exclusivement pour UTF-16/32, sinon exige ~95% imprimable
    text_chars = bytes(range(32, 127)) + b"\n\r\t\f\b"
    nontext = sum(1 for b in head if b not in text_chars)
    return nontext <= len(head) * 0.05


def _guess_text_format(sample: str) -> set[str]:
    out: set[str] = set()
    s = sample.lstrip()
    if s.startswith("<"):
        out.add("xml" if s.startswith("<?xml") else "html")
    elif s.startswith("{") or s.startswith("["):
        out.add("json")
    elif "," in sample and "\n" in sample:
        out.add("csv")
    else:
        out.update(("txt", "md"))
    return out


# Alias acceptés : l'extension déclarée et l'extension sniffée sont considérées équivalentes
_ALIASES = {
    "jpg": "jpeg",
    "tif": "tiff",
    "html": "htm",
    "tar.gz": "gzip",
}


def validate_upload(file_path: Path, declared_ext: str) -> tuple[bool, str]:
    """Vérifie la cohérence extension déclarée ↔ contenu réel.
    Retourne (ok, message). On ne bloque que sur une contradiction nette
    (contenu identifié ET incompatible avec l'extension déclarée)."""
    declared = (declared_ext or "").lower()
    if declared not in ALLOWED_EXTENSIONS:
        return False, f"Extension non supportee: .{declared}"

    sniffed = sniff_extensions(file_path)
    if not sniffed:
        # contenu inconnu (ex: format exotique, binaire propriétaire) : on laisse passer
        return True, ""

    # Normalise via alias (jpg<->jpeg, tif<->tiff, ...) des deux côtés.
    norm_sniffed = {_ALIASES.get(e, e) for e in sniffed}
    norm_declared = _ALIASES.get(declared, declared)

    if norm_declared in norm_sniffed:
        return True, ""

    # Un Office OOXML déclaré en variante legacy (doc/xls/ppt) est accepté
    # si on a sniffé la version OOXML correspondante.
    legacy_to_ooxml = {"doc": "docx", "xls": "xlsx", "ppt": "pptx"}
    if legacy_to_ooxml.get(norm_declared) in norm_sniffed:
        return True, ""

    return False, (
        f"Le contenu du fichier ne correspond pas a l'extension .{declared} "
        f"(detecte: {', '.join(sorted(sniffed))})"
    )
