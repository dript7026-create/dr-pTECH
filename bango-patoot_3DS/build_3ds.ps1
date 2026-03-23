$ErrorActionPreference = "Stop"

if (-not $env:DEVKITPRO) {
    $env:DEVKITPRO = "C:\devkitPro"
}

if (-not $env:DEVKITARM) {
    $env:DEVKITARM = Join-Path $env:DEVKITPRO "devkitARM"
}

if (-not $env:CTRULIB) {
    $env:CTRULIB = Join-Path $env:DEVKITPRO "libctru"
}

Set-Location $PSScriptRoot
$python = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\Scripts\python.exe"
if (Test-Path $python) {
    & $python (Join-Path $PSScriptRoot "tools\generate_placeholder_rig_assets.py")
    & $python (Join-Path $PSScriptRoot "tools\build_runtime_asset_pack.py")
    & $python (Join-Path $PSScriptRoot "tools\build_test_level_from_tiles.py")
}
make clean
make