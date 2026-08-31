# SoundSpace Orbit

Current version: **0.1.0**

SoundSpace Orbit is a planned standalone desktop app for turning local audio files or supported web audio URLs into an "8D" style listening experience.

The core effect will move audio smoothly between the left and right stereo channels, with controls for pan speed, pan depth, output format, and optional spatial ambience.

## Versioning

Versioning is intentionally visible in a few places:

- `VERSION` contains the release number.
- `soundspace_orbit/version.py` displays the version in the desktop app and CLI.
- `CHANGELOG.md` records what changed in each version.
- Git tags should use `vX.Y.Z`, starting with `v0.1.0`.

## Version 0.1.0

- Import local audio files such as MP3, WAV, FLAC, M4A, and AAC.
- Accept supported public web audio URLs.
- Convert mono or stereo input into a moving stereo output.
- Export processed audio as MP3 or WAV.
- Provide simple controls for pan speed, pan depth, and optional reverb.
- Run through either a desktop app or command-line interface.

## Quick Start

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Launch the desktop app:

```powershell
.\.venv\Scripts\python -m soundspace_orbit
```

Convert from the command line:

```powershell
.\.venv\Scripts\python -m soundspace_orbit "C:\path\to\song.mp3" --cycle 8 --depth 0.85 --format mp3
```

Show the installed app version:

```powershell
.\.venv\Scripts\python -m soundspace_orbit --version
```

## Build a Windows App

The first packaging path uses PyInstaller:

```powershell
.\.venv\Scripts\python -m pip install -e ".[build]"
.\scripts\build-windows.ps1
```

The generated app is written to:

```text
dist\SoundSpace Orbit.exe
```

## Release Checklist

1. Update `VERSION`.
2. Update `soundspace_orbit/version.py`.
3. Update `pyproject.toml`.
4. Add a new section to `CHANGELOG.md`.
5. Run tests.
6. Commit and tag the release as `vX.Y.Z`.

## Working Approach

The first implementation target is a Python desktop app using FFmpeg for audio decoding and encoding. URL support will likely use `yt-dlp` for public, non-DRM sources.

SoundSpace Orbit will not bypass DRM, paid streaming protections, private login-only content, or service terms.
