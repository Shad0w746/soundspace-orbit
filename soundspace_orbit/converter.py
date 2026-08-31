"""Core conversion logic for SoundSpace Orbit."""

from __future__ import annotations

import math
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from .ffmpeg import run_ffmpeg


SUPPORTED_FORMATS = {"mp3", "wav"}
DIRECT_AUDIO_EXTENSIONS = {".aac", ".aiff", ".alac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav", ".wma"}


@dataclass(frozen=True)
class OrbitSettings:
    """User-facing 8D conversion settings."""

    cycle_seconds: float = 8.0
    depth: float = 0.85
    output_format: str = "mp3"
    spatial_reverb: bool = False
    mp3_bitrate: str = "192k"

    def normalized(self) -> "OrbitSettings":
        output_format = self.output_format.lower().lstrip(".")
        if output_format not in SUPPORTED_FORMATS:
            raise ValueError(f"Output format must be one of: {', '.join(sorted(SUPPORTED_FORMATS))}")

        if not math.isfinite(self.cycle_seconds) or self.cycle_seconds <= 0:
            raise ValueError("Cycle seconds must be greater than 0.")

        if not math.isfinite(self.depth):
            raise ValueError("Depth must be a number.")

        return OrbitSettings(
            cycle_seconds=max(1.0, min(float(self.cycle_seconds), 60.0)),
            depth=max(0.0, min(float(self.depth), 0.95)),
            output_format=output_format,
            spatial_reverb=bool(self.spatial_reverb),
            mp3_bitrate=self.mp3_bitrate,
        )


@dataclass(frozen=True)
class ConversionResult:
    """Details about a completed conversion."""

    source: str
    output_path: Path
    settings: OrbitSettings


def is_url(source: str) -> bool:
    parsed = urlparse(source)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def convert_to_8d(source: str, output_dir: Path | str, settings: OrbitSettings | None = None) -> ConversionResult:
    """Convert a local file or supported URL into an 8D-style stereo audio file."""

    clean_source = source.strip()
    if not clean_source:
        raise ValueError("Choose an audio file or paste a URL first.")

    output_root = Path(output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    active_settings = (settings or OrbitSettings()).normalized()

    with tempfile.TemporaryDirectory(prefix="soundspace-orbit-") as temp_name:
        temp_dir = Path(temp_name)
        input_path, display_name, fallback_url = _resolve_source(clean_source, temp_dir)
        output_path = _next_output_path(output_root, display_name, active_settings.output_format)
        try:
            _run_orbit_filter(input_path, output_path, active_settings)
        except RuntimeError:
            if not fallback_url:
                raise
            if output_path.exists():
                output_path.unlink()
            downloaded_path, display_name = _download_url(fallback_url, temp_dir)
            output_path = _next_output_path(output_root, display_name, active_settings.output_format)
            _run_orbit_filter(downloaded_path, output_path, active_settings)

    return ConversionResult(source=clean_source, output_path=output_path, settings=active_settings)


def _resolve_source(source: str, temp_dir: Path) -> tuple[Path | str, str, str | None]:
    if is_url(source):
        if _looks_like_direct_audio_url(source):
            return source, _display_name_from_url(source), source
        downloaded_path, display_name = _download_url(source, temp_dir)
        return downloaded_path, display_name, None

    input_path = Path(source).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")
    return input_path, input_path.stem, None


def _download_url(url: str, temp_dir: Path) -> tuple[Path, str]:
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("URL support requires yt-dlp. Install dependencies with `pip install -r requirements.txt`.") from exc

    outtmpl = str(temp_dir / "%(title).120s.%(ext)s")
    options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        if "entries" in info:
            info = next((entry for entry in info["entries"] if entry), None)
            if info is None:
                raise RuntimeError("No downloadable audio entry was found at that URL.")

        downloaded = Path(downloader.prepare_filename(info))
        if not downloaded.exists():
            matches = sorted(temp_dir.glob("*"), key=lambda item: item.stat().st_mtime, reverse=True)
            if not matches:
                raise RuntimeError("yt-dlp completed but no downloaded file was found.")
            downloaded = matches[0]

        title = str(info.get("title") or downloaded.stem)
        return downloaded, title


def _run_orbit_filter(input_path: Path | str, output_path: Path, settings: OrbitSettings) -> None:
    filter_graph = _build_filter_graph(settings)

    args = [
        "-y",
        "-hide_banner",
        "-i",
        str(input_path),
        "-filter_complex",
        filter_graph,
        "-map",
        "[orbit]",
        "-vn",
    ]

    if settings.output_format == "mp3":
        args.extend(["-codec:a", "libmp3lame", "-b:a", settings.mp3_bitrate])
    else:
        args.extend(["-codec:a", "pcm_s16le"])

    args.append(str(output_path))
    run_ffmpeg(args)


def _build_filter_graph(settings: OrbitSettings) -> str:
    depth = settings.depth
    period = settings.cycle_seconds

    left_gain = f"1-{depth:.4f}*((sin(2*PI*t/{period:.4f})+1)/2)"
    right_gain = f"1-{depth:.4f}*((1-sin(2*PI*t/{period:.4f}))/2)"

    graph = (
        "[0:a]"
        "aformat=channel_layouts=mono,"
        "asplit=2[left][right];"
        f"[left]volume='{left_gain}':eval=frame[leftv];"
        f"[right]volume='{right_gain}':eval=frame[rightv];"
        "[leftv][rightv]amerge=inputs=2,"
        "aformat=channel_layouts=stereo"
    )

    if settings.spatial_reverb:
        graph += ",aecho=0.8:0.88:60:0.25"

    return graph + "[orbit]"


def _next_output_path(output_dir: Path, source_name: str, extension: str) -> Path:
    base = _safe_filename(source_name)
    candidate = output_dir / f"{base}_soundspace_orbit.{extension}"
    counter = 2
    while candidate.exists():
        candidate = output_dir / f"{base}_soundspace_orbit_{counter}.{extension}"
        counter += 1
    return candidate


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^\w .()-]+", "_", value, flags=re.ASCII).strip(" ._")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:80] or "audio"


def _looks_like_direct_audio_url(url: str) -> bool:
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix in DIRECT_AUDIO_EXTENSIONS


def _display_name_from_url(url: str) -> str:
    stem = unquote(Path(urlparse(url).path).stem)
    return stem or "web-audio"
