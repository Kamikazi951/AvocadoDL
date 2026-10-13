param(
    [string]$Version = "",
    [string]$OutputFile = "",
    [switch]$Offline
)
$ErrorActionPreference = "Stop"
$taskArgs = @((Join-Path $PSScriptRoot "build.py"))
if ($Version) { $taskArgs += @("--version", $Version) }
if ($OutputFile) { $taskArgs += @("--output", $OutputFile) }
if ($Offline) { $taskArgs += "--offline" }
& python @taskArgs
if ($LASTEXITCODE -ne 0) { throw "Add-on build failed (exit $LASTEXITCODE)." }
