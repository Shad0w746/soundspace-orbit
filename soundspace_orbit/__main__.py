"""Command-line entrypoint for SoundSpace Orbit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import OrbitSettings, convert_to_8d
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="soundspace-orbit",
        description="Convert local or supported web audio into an 8D-style stereo file.",
    )
    parser.add_argument("source", nargs="?", help="Audio file path or supported web URL. Omit to launch the desktop app.")
    parser.add_argument("-o", "--output-dir", default="output", help="Folder for converted audio. Default: output")
    parser.add_argument("-f", "--format", choices=("mp3", "wav"), default="mp3", help="Output format. Default: mp3")
    parser.add_argument("--cycle", type=float, default=8.0, help="Seconds per left/right movement cycle. Default: 8")
    parser.add_argument("--depth", type=float, default=0.85, help="Pan depth from 0.0 to 0.95. Default: 0.85")
    parser.add_argument("--reverb", action="store_true", help="Add light spatial ambience.")
    parser.add_argument("--gui", action="store_true", help="Launch the desktop app.")
    parser.add_argument("--version", action="version", version=f"SoundSpace Orbit {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.gui or not args.source:
        from .gui import run_app

        run_app()
        return 0

    settings = OrbitSettings(
        cycle_seconds=args.cycle,
        depth=args.depth,
        output_format=args.format,
        spatial_reverb=args.reverb,
    )

    try:
        result = convert_to_8d(args.source, Path(args.output_dir), settings)
    except Exception as exc:
        print(f"SoundSpace Orbit failed: {exc}", file=sys.stderr)
        return 1

    print(f"Created: {result.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
