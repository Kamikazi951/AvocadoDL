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
$YtdlpSitePkg = "$(python -c 'import yt_dlp; import os; print(os.path.dirname(yt_dlp.__file__))' 2>$null)"

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

Write-Host "Bundling yt-dlp..." -ForegroundColor Cyan
$YtdlpPkgTarget = Join-Path $YtdlpTarget "yt_dlp"
New-Item -ItemType Directory -Path $YtdlpPkgTarget -Force | Out-Null
Copy-Item -Recurse "$YtdlpSitePkg\*" $YtdlpPkgTarget

# Step 2: Package .fda
Write-Host "Packaging $OutputFile..." -ForegroundColor Cyan

if (Test-Path $OutputPath) { Remove-Item -Force $OutputPath }

$TempDir = Join-Path $env:TEMP "avocadodl-build"
if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

Copy-Item -Recurse "$AddonPath\*" $TempDir

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($TempDir, $OutputPath)

Remove-Item -Recurse -Force $TempDir

$FileInfo = Get-Item $OutputPath
Write-Host ""
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Version: $Version" -ForegroundColor White
Write-Host "Output:  $OutputFile" -ForegroundColor White
Write-Host "Size:    $([Math]::Round($FileInfo.Length / 1KB)) KB"
Write-Host ""
Write-Host "Install: FDM > Tools > Add-ons > Install from file" -ForegroundColor Yellow
