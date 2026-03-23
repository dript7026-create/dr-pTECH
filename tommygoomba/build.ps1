<#
PowerShell build helper for TommyGoomba (GBDK).

This script will:
- run the PNG asset generator (Pillow) to create placeholder assets
- convert PNGs into a C tile source using `convert_assets.py`
- compile a Game Boy ROM using the workspace GBDK toolchain

Usage: Open PowerShell in the `tommygoomba` folder and run:
    .\build.ps1

#>

$toolchainScript = Join-Path (Split-Path -Parent $PSScriptRoot) "workspace_toolchains.ps1"
if (Test-Path $toolchainScript) {
    & $toolchainScript -Quiet
}

if (-not (Get-Command lcc -ErrorAction SilentlyContinue)) {
    Write-Error "lcc not found in PATH. Ensure the workspace GBDK toolchain is configured."
    exit 2
}

$python = "C:/Users/rrcar/Documents/drIpTECH/.venv/Scripts/python.exe"
$buildDir = Join-Path $PSScriptRoot "build"
$sourceCopy = Join-Path $buildDir "tommygoomba_gb_main.c"
$romName = "tg.gb"
$romPath = Join-Path $buildDir $romName
$finalRomPath = Join-Path $buildDir "tommygoomba_rom.gb"

Push-Location $PSScriptRoot
try {
    if (-not (Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }

    Write-Host "Running asset generator..."
    & $python .\generate_assets.py
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Asset generation failed."
        exit 3
    }

    Write-Host "Converting assets to C tile arrays (tiles.c)..."
    & $python .\convert_assets.py --output tiles.c
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Asset conversion failed."
        exit 4
    }

    Copy-Item .\tommygoomba.gb $sourceCopy -Force

    Write-Host "Building ROM with GBDK lcc..."
    Push-Location $buildDir
    try {
        lcc -Wf--disable-warning=110 -o $romName tommygoomba_gb_main.c
    }
    finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Error "GBDK build failed."
        exit 5
    }

    Copy-Item $romPath $finalRomPath -Force

    Write-Host "Built $finalRomPath" -ForegroundColor Green
}
finally {
    Pop-Location
}
