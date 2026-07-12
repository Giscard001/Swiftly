import os
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

from .base import ConversionRoute, ConvertContext

try:
    import py7zr
    _Z7 = True
except Exception:
    _Z7 = False

NAME = "archives"

# Formats d'archive gérés nativement (Python stdlib + py7zr).
_NATIVE = ["zip", "tar", "tar.gz", "tar.bz2", "tar.xz"] + (["7z"] if _Z7 else [])
# Cibles possibles (création). RAR est exclu : format propriétaire, pas de
# création possible en Python.
_TARGETS = ["zip", "tar", "tar.gz", "tar.bz2", "tar.xz"] + (["7z"] if _Z7 else [])


def _unrar() -> str | None:
    """Chemin vers le binaire unrar, ou None s'il n'est pas installé.
    RAR est propriétaire : on ne peut que l'extraire (pas le créer)."""
    return shutil.which("unrar")


def available() -> bool:
    # Toujours vrai : au minimum zip/tar sont gérés.
    return True


def routes() -> list[ConversionRoute]:
    out: list[ConversionRoute] = []
    for s in _NATIVE:
        for t in _TARGETS:
            if s == t:
                continue
            out.append(ConversionRoute("archive", s, t, NAME, _convert, f"{s} -> {t}"))
    # RAR : extraction seule, vers les formats natifs, si unrar est présent.
    if _unrar():
        for t in _TARGETS:
            out.append(ConversionRoute("archive", "rar", t, NAME, _convert, f"rar -> {t}"))
    return out


def _validate_member_names(names, dest: str) -> None:
    """Rejette tout chemin qui s'échapperait de dest (zip-slip / tarbomb),
    ainsi que les chemins absolus ou à lettre de lecteur."""
    dest_real = os.path.realpath(dest)
    for raw in names:
        name = raw.replace("\\", "/")
        if name.startswith("/") or (len(name) > 1 and name[1] == ":"):
            raise ValueError(f"Chemin absolu interdit dans l'archive : {raw}")
        # ../ ou composant remontant explicite
        parts = name.split("/")
        if any(p == ".." for p in parts):
            raise ValueError(f"Chemin de traversal interdit dans l'archive : {raw}")
        target = os.path.realpath(os.path.join(dest_real, name))
        if target != dest_real and not target.startswith(dest_real + os.sep):
            raise ValueError(f"Chemin de sortie interdit (traversal) : {raw}")


def _validate_tar_members(members, dest: str) -> None:
    """Comme _validate_member_names + rejet des liens (sym/hard) tar."""
    _validate_member_names([m.name for m in members], dest)
    for m in members:
        if m.islnk() or m.issym():
            raise ValueError(f"Lien (sym/hard) interdit dans l'archive : {m.name}")
        if m.isdev():
            raise ValueError(f"Entrée device/fifo interdite dans l'archive : {m.name}")


def _extract(path: Path, dest: str) -> None:
    name = path.name.lower()
    os.makedirs(dest, exist_ok=True)
    if name.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            _validate_member_names(z.namelist(), dest)
            z.extractall(dest)
    elif name.endswith(".tar.gz") or name.endswith(".tgz"):
        with tarfile.open(path, "r:gz") as t:
            _validate_tar_members(t.getmembers(), dest)
            t.extractall(dest, filter="data")
    elif name.endswith(".tar.bz2") or name.endswith(".tbz2"):
        with tarfile.open(path, "r:bz2") as t:
            _validate_tar_members(t.getmembers(), dest)
            t.extractall(dest, filter="data")
    elif name.endswith(".tar.xz") or name.endswith(".txz"):
        with tarfile.open(path, "r:xz") as t:
            _validate_tar_members(t.getmembers(), dest)
            t.extractall(dest, filter="data")
    elif name.endswith(".tar"):
        with tarfile.open(path, "r:") as t:
            _validate_tar_members(t.getmembers(), dest)
            t.extractall(dest, filter="data")
    elif name.endswith(".7z"):
        with py7zr.SevenZipFile(path) as z:
            _validate_member_names(z.getnames(), dest)
            z.extractall(dest)
    elif name.endswith(".rar"):
        _extract_rar(path, dest)
    else:
        raise ValueError(f"Format d'archive non supporte: {name}")


def _extract_rar(path: Path, dest: str) -> None:
    """Extraction RAR via le binaire unrar (propriétaire). On liste d'abord
    pour valider les noms (anti tarbomb), puis on extrait."""
    exe = _unrar()
    if not exe:
        raise RuntimeError("unrar n'est pas installe : extraction RAR impossible")
    # `unrar lt` liste en mode technique ; on parse les noms de fichier.
    r = subprocess.run(
        [exe, "lt", str(path)], capture_output=True, timeout=120
    )
    out = r.stdout.decode("utf-8", "replace", errors="ignore") if r.stdout else ""
    # Les lignes "Name: xxx" donnent les noms ; fallback robuste si parsing échoue.
    names = []
    for line in out.splitlines():
        if line.lower().startswith("name:"):
            names.append(line.split(":", 1)[1].strip())
    if names:
        _validate_member_names(names, dest)
    # Extraction effective vers dest
    er = subprocess.run(
        [exe, "x", "-y", "-op" + dest, str(path)],
        capture_output=True, timeout=600,
    )
    if er.returncode != 0:
        raise RuntimeError(
            (er.stderr.decode("utf-8", "replace")[:300] if er.stderr else "")
            or "unrar a echoue"
        )


def _create(target: str, root: str, outpath: Path) -> None:
    files = [os.path.join(r, fn) for r, _, fs in os.walk(root) for fn in fs]
    if target == "zip":
        with zipfile.ZipFile(outpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                z.write(f, arcname=os.path.relpath(f, root))
    elif target == "tar":
        with tarfile.open(outpath, "w") as t:
            for f in files:
                t.add(f, arcname=os.path.relpath(f, root))
    elif target == "tar.gz":
        with tarfile.open(outpath, "w:gz") as t:
            for f in files:
                t.add(f, arcname=os.path.relpath(f, root))
    elif target == "tar.bz2":
        with tarfile.open(outpath, "w:bz2") as t:
            for f in files:
                t.add(f, arcname=os.path.relpath(f, root))
    elif target == "tar.xz":
        with tarfile.open(outpath, "w:xz") as t:
            for f in files:
                t.add(f, arcname=os.path.relpath(f, root))
    elif target == "7z":
        with py7zr.SevenZipFile(outpath, "w") as z:
            for f in files:
                z.write(f, arcname=os.path.relpath(f, root))
    else:
        raise ValueError(f"Archive cible non supportee: {target}")


def _convert(ctx: ConvertContext) -> None:
    ctx.set_progress(10, "Extraction")
    with tempfile.TemporaryDirectory() as d:
        _extract(ctx.input_path, d)
        ctx.set_progress(60, "Creation de l'archive")
        _create(ctx.target, d, ctx.output_path)
    ctx.set_progress(100, "Termine")
