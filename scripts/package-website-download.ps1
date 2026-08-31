param(
  [switch]$Build
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Version = (Get-Content -LiteralPath (Join-Path $ProjectRoot "VERSION") -Raw).Trim()
$DownloadsRoot = Join-Path $ProjectRoot "website-downloads"
$PackageName = "SoundSpace-Orbit-v$Version-Windows"
$PackageRoot = Join-Path $DownloadsRoot $PackageName
$ZipPath = Join-Path $DownloadsRoot "$PackageName.zip"
$ZipHashPath = Join-Path $DownloadsRoot "$PackageName.sha256.txt"
$ExeSource = Join-Path $ProjectRoot "dist\SoundSpace Orbit.exe"

if ($Build -or -not (Test-Path -LiteralPath $ExeSource)) {
  & (Join-Path $PSScriptRoot "build-windows.ps1")
}

if (-not (Test-Path -LiteralPath $ExeSource)) {
  throw "Missing built executable: $ExeSource"
}

New-Item -ItemType Directory -Force -Path $DownloadsRoot | Out-Null
$ResolvedDownloadsRoot = (Resolve-Path -LiteralPath $DownloadsRoot).Path

if (Test-Path -LiteralPath $PackageRoot) {
  $ResolvedPackageRoot = (Resolve-Path -LiteralPath $PackageRoot).Path
  if (-not $ResolvedPackageRoot.StartsWith($ResolvedDownloadsRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside website-downloads: $ResolvedPackageRoot"
  }
  Remove-Item -LiteralPath $ResolvedPackageRoot -Recurse -Force
}

if (Test-Path -LiteralPath $ZipPath) {
  Remove-Item -LiteralPath $ZipPath -Force
}

if (Test-Path -LiteralPath $ZipHashPath) {
  Remove-Item -LiteralPath $ZipHashPath -Force
}

New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null

$ExeTarget = Join-Path $PackageRoot "SoundSpace Orbit.exe"
Copy-Item -LiteralPath $ExeSource -Destination $ExeTarget -Force

$ExeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ExeTarget).Hash
$ReleaseUrl = "https://github.com/Shad0w746/soundspace-orbit/releases/tag/v$Version"

$Readme = @"
SoundSpace Orbit v$Version

Free Windows Download

What it does:
SoundSpace Orbit turns a local audio file or supported public audio URL into an 8D-style stereo audio file that shifts smoothly between the left and right channels.

How to run:
1. Unzip this folder.
2. Double-click SoundSpace Orbit.exe.
3. In Source, choose a local audio file or paste a public audio URL.
4. Choose an output folder.
5. Click CREATE 8D AUDIO.

Supported output:
- MP3
- WAV

Known limits:
- This app does not bypass DRM.
- This app does not access paid/private/login-only streams.
- Only convert audio you own, created, licensed, or otherwise have permission to use.

Windows note:
Because this early free build is not code-signed yet, Windows SmartScreen may warn that the publisher is unknown.

Version:
$Version

Release page:
$ReleaseUrl

Executable SHA-256:
$ExeHash
"@

Set-Content -LiteralPath (Join-Path $PackageRoot "README-FIRST.txt") -Value $Readme -Encoding UTF8

$WebsiteCopy = @"
SoundSpace Orbit

Free Windows download

Create 8D-style audio from a local music file or supported public audio URL. SoundSpace Orbit applies a smooth left-right stereo movement effect and exports a new MP3 or WAV file.

Download button text:
Download SoundSpace Orbit for Windows

Download file:
$PackageName.zip

Version:
$Version

Suggested note:
This is an early free Windows build. Windows may show an unknown-publisher warning because the app is not code-signed yet.

SHA-256 checksum:
$ExeHash
"@

Set-Content -LiteralPath (Join-Path $PackageRoot "WEBSITE-COPY.txt") -Value $WebsiteCopy -Encoding UTF8
Set-Content -LiteralPath (Join-Path $PackageRoot "SHA256SUMS.txt") -Value "$ExeHash *SoundSpace Orbit.exe" -Encoding UTF8

Compress-Archive -LiteralPath $PackageRoot -DestinationPath $ZipPath -CompressionLevel Optimal

$ZipHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ZipPath).Hash
Set-Content -LiteralPath $ZipHashPath -Value "$ZipHash *$PackageName.zip" -Encoding UTF8

Write-Host "Website package created:"
Write-Host $ZipPath
Write-Host "ZIP SHA-256:"
Write-Host $ZipHash
