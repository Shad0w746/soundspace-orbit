# SoundSpace Orbit

SoundSpace Orbit is a planned standalone desktop app for turning local audio files or supported web audio URLs into an "8D" style listening experience.

The core effect will move audio smoothly between the left and right stereo channels, with controls for pan speed, pan depth, output format, and optional spatial ambience.

## Planned Version 1

- Import local audio files such as MP3, WAV, FLAC, M4A, and AAC.
- Accept supported public web audio URLs.
- Convert mono or stereo input into a moving stereo output.
- Export processed audio as MP3 or WAV.
- Provide simple controls for pan speed, pan depth, and optional reverb.
- Run locally as a self-contained Windows app.

## Working Approach

The first implementation target is a Python desktop app using FFmpeg for audio decoding and encoding. URL support will likely use `yt-dlp` for public, non-DRM sources.

SoundSpace Orbit will not bypass DRM, paid streaming protections, private login-only content, or service terms.
