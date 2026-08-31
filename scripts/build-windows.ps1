$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

& $Python -m pip install -e ".[build]"

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --name "SoundSpace Orbit" `
  --onefile `
  --windowed `
  --collect-binaries imageio_ffmpeg `
  --collect-all yt_dlp `
  soundspace_orbit_launcher.py

Write-Host "Built dist\SoundSpace Orbit.exe"
