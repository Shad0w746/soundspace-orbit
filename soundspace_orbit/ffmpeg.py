"""FFmpeg discovery and command helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class FFmpegNotFoundError(RuntimeError):
    """Raised when no usable FFmpeg executable can be found."""


def find_ffmpeg() -> str:
    """Return a usable FFmpeg executable path.

    Search order:
    1. SOUNDSPACE_FFMPEG environment variable.
    2. ffmpeg on PATH.
    3. imageio-ffmpeg's bundled executable.
    """

    configured = os.environ.get("SOUNDSPACE_FFMPEG")
    if configured:
        configured_path = Path(configured)
        if configured_path.exists():
            return str(configured_path)

    path_match = shutil.which("ffmpeg")
    if path_match:
        return path_match

    try:
        import imageio_ffmpeg

        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and Path(bundled).exists():
            return str(bundled)
    except Exception:
        pass

    raise FFmpegNotFoundError(
        "FFmpeg was not found. Install dependencies with `pip install -r requirements.txt` "
        "or set SOUNDSPACE_FFMPEG to an ffmpeg.exe path."
    )


def run_ffmpeg(args: list[str]) -> None:
    """Run FFmpeg and raise a readable error if it fails."""

    exe = find_ffmpeg()
    command = [exe, *args]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise RuntimeError(f"FFmpeg failed with exit code {completed.returncode}:\n{stderr}")
