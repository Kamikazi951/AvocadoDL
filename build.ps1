param(
    [string]$AddonDir = "AvocadoDL FDM Addon",
    [string]$Version = "",
    [string]$OutputFile = ""
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AddonPath = Join-Path $RootDir $AddonDir
if (-not (Test-Path $AddonPath)) {
    $AddonPath = $RootDir
}

# Read version from manifest
$ManifestPath = Join-Path $AddonPath "manifest.json"
if (Test-Path $ManifestPath) {
    $manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
    if (-not $Version) { $Version = $manifest.version }
}
if (-not $Version) { $Version = "1.0.0" }
if (-not $OutputFile) { $OutputFile = "avocadodl-$Version.fda" }

$OutputPath = Join-Path $RootDir $OutputFile
$YtdlpTarget = Join-Path $AddonPath "yt-dlp"
$YtdlpSitePkg = "$(python -c 'import sys, os; sys.path.insert(0, os.path.expandvars(r\"%APPDATA%\avocadodl\packages\")); import yt_dlp; print(os.path.dirname(yt_dlp.__file__))' 2>$null)"
if (-not $YtdlpSitePkg -or -not (Test-Path $YtdlpSitePkg)) {
    $YtdlpSitePkg = "$(python -c 'import yt_dlp; import os; print(os.path.dirname(yt_dlp.__file__))' 2>$null)"
}

Write-Host "=== AvocadoDL v$Version Builder ===" -ForegroundColor Green
Write-Host ""

if (-not $YtdlpSitePkg -or -not (Test-Path $YtdlpSitePkg)) {
    Write-Host "ERROR: yt-dlp not found. Install with: pip install yt-dlp" -ForegroundColor Red
    exit 1
}

# Step 1: Clean and copy yt-dlp
if (Test-Path $YtdlpTarget) {
    Write-Host "Removing previous yt-dlp..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $YtdlpTarget
}

Write-Host "Bundling yt-dlp from $YtdlpSitePkg..." -ForegroundColor Cyan
$YtdlpPkgTarget = Join-Path $YtdlpTarget "yt_dlp"
New-Item -ItemType Directory -Path $YtdlpPkgTarget -Force | Out-Null
Copy-Item -Recurse "$YtdlpSitePkg\*" $YtdlpPkgTarget

# Step 2: Package .fda
Write-Host "Packaging $OutputFile..." -ForegroundColor Cyan

if (Test-Path $OutputPath) { Remove-Item -Force $OutputPath }

$TempDir = Join-Path $env:TEMP "avocadodl-build"
if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

$FilesToInclude = @(
    "manifest.json",
    "icon.svg",
    "tools.js",
    "msabstractparser.js",
    "msparser.js",
    "msbatchparser.js",
    "config_loader.py",
    "ytdlp_helper.py",
    "ytdlp_runner.py",
    "settings.template.json"
)

foreach ($f in $FilesToInclude) {
    $src = Join-Path $AddonPath $f
    if (Test-Path $src) {
        Copy-Item $src $TempDir
    }
}

$ytSrc = Join-Path $AddonPath "yt-dlp"
if (Test-Path $ytSrc) {
    Copy-Item -Recurse $ytSrc (Join-Path $TempDir "yt-dlp")
}

# Create ZIP archive ensuring all internal entry paths use POSIX '/' separators
# (Fixes macOS/Linux extracting entries as literal backslash filenames)
python -c @"
import zipfile, os
output = r'$OutputPath'
temp_dir = r'$TempDir'
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(temp_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, temp_dir).replace('\\', '/')
            zf.write(full_path, rel_path)
"@

Remove-Item -Recurse -Force $TempDir

$FileInfo = Get-Item $OutputPath
Write-Host ""
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Version: $Version" -ForegroundColor White
Write-Host "Output:  $OutputFile" -ForegroundColor White
Write-Host "Size:    $([Math]::Round($FileInfo.Length / 1KB)) KB"
Write-Host ""
Write-Host "Install: FDM > Tools > Add-ons > Install from file" -ForegroundColor Yellow
