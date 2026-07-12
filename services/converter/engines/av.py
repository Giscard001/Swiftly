import shutil
import subprocess

from .base import ConversionRoute, ConvertContext

NAME = "av"
_AUDIO = ["mp3", "wav", "flac", "aac", "ogg", "m4a"]
_VIDEO = ["mp4", "avi", "mov", "mkv", "webm"]


def available() -> bool:
    return bool(shutil.which("ffmpeg"))


def routes() -> list[ConversionRoute]:
    if not available():
        return []
    out: list[ConversionRoute] = []
    for s in _AUDIO:
        for t in _AUDIO:
            if s != t:
                out.append(ConversionRoute("audio", s, t, NAME, _convert, f"{s.upper()} -> {t.upper()}"))
    for s in _VIDEO:
        for t in _VIDEO:
            if s != t:
                out.append(ConversionRoute("video", s, t, NAME, _convert, f"{s.upper()} -> {t.upper()}"))
        out.append(ConversionRoute("video", s, "mp3", NAME, _extract_audio, f"{s.upper()} -> MP3"))
        out.append(ConversionRoute("video", s, "gif", NAME, _to_gif, f"{s.upper()} -> GIF"))
    return out


def _run(args: list[str]) -> None:
    r = subprocess.run(args, capture_output=True, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[:500] or "FFmpeg a echoue")


def _convert(ctx: ConvertContext) -> None:
    ctx.set_progress(10, "Conversion FFmpeg")
    _run(["ffmpeg", "-y", "-i", str(ctx.input_path), str(ctx.output_path)])
    ctx.set_progress(100, "Termine")


def _extract_audio(ctx: ConvertContext) -> None:
    ctx.set_progress(10, "Extraction audio")
    _run(["ffmpeg", "-y", "-i", str(ctx.input_path), "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(ctx.output_path)])
    ctx.set_progress(100, "Termine")


def _to_gif(ctx: ConvertContext) -> None:
    ctx.set_progress(10, "Generation du GIF")
    _run(["ffmpeg", "-y", "-i", str(ctx.input_path), "-vf", "fps=10,scale=480:-1:flags=lanczos", str(ctx.output_path)])
    ctx.set_progress(100, "Termine")
