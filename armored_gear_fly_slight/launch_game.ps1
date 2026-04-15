#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launch Armored Gear: Fly Slight with Xbox Series Controller support
.DESCRIPTION
    Runs the compiled GameBoy ROM with full Xbox Series X/S controller support via mGBA emulator.
.EXAMPLE
    .\launch_game.ps1
#>

param(
    [switch]$SkipControllerCheck = $false,
    [switch]$SkipEmulatorCheck = $false,
    [switch]$Monitor = $false
)

function Get-RomType {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return "missing"
    }

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 0x108) {
        return "unknown"
    }

    if ($bytes[4] -eq 0x24 -and $bytes[5] -eq 0xFF -and $bytes[6] -eq 0xAE -and $bytes[7] -eq 0x51) {
        return "gba"
    }

    if ($bytes[0x104] -eq 0xCE -and $bytes[0x105] -eq 0xED -and $bytes[0x106] -eq 0x66 -and $bytes[0x107] -eq 0x66) {
        return "gb"
    }

    return "unknown"
}

function Select-Rom {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Dir
    )

    $candidates = @(
        (Join-Path $Dir "armored_gear_fly_slight.gba"),
        (Join-Path $Dir "armored_gear_fly_slight.gb"),
        (Join-Path $Dir "armored_gear_fly_slight_native.gba")
    )

    foreach ($candidate in $candidates) {
        if (-not (Test-Path $candidate)) {
            continue
        }

        $romType = Get-RomType -Path $candidate
        if ($candidate.ToLower().EndsWith('.gba') -and $romType -eq 'gb') {
            continue
        }
        if ($candidate.ToLower().EndsWith('.gb') -and $romType -eq 'gba') {
            continue
        }

        if ($romType -in @('gb', 'gba')) {
            return $candidate
        }
    }

    return $null
}

$ScriptDir = Split-Path -Parent $PSCommandPath
$RomPath = Select-Rom -Dir $ScriptDir
$PyLauncher = Join-Path $ScriptDir "launch_with_xbox_controller.py"

Write-Host "`n" -NoNewline
Write-Host "=" * 70
Write-Host "🎮 ARMORED GEAR: FLY SLIGHT" -ForegroundColor Cyan -NoNewline
Write-Host ""
Write-Host "   Xbox Series X/S Controller Launch" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host ""

# Check ROM exists
if (-not $RomPath) {
    Write-Host "❌ ROM not found: $RomPath" -ForegroundColor Red
    Write-Host "   Build the game first:"
    Write-Host "   cd $ScriptDir"
    Write-Host "   .\build.ps1"
    exit 1
}

$RomType = Get-RomType -Path $RomPath
$RomSize = (Get-Item $RomPath).Length / 1KB
Write-Host "✅ ROM found: $(Split-Path -Leaf $RomPath) ($($RomSize)KB, type=$($RomType.ToUpper()))" -ForegroundColor Green

$env:ARMORED_GEAR_ROM_PATH = $RomPath

# Check Python
$PythonExe = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $PythonExe) {
    $PythonExe = Get-Command python -ErrorAction SilentlyContinue
}

if (-not $PythonExe) {
    Write-Host "❌ Python not found in PATH" -ForegroundColor Red
    Write-Host "   Install Python 3.9+ from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Python found: $($PythonExe.Source)" -ForegroundColor Green

# Check pygame
try {
    & $PythonExe -c "import pygame; print('OK')" -ErrorAction Stop | Out-Null
    Write-Host "✅ pygame installed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  pygame not installed, installing..." -ForegroundColor Yellow
    & $PythonExe -m pip install pygame -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ pygame installed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install pygame" -ForegroundColor Red
        exit 1
    }
}

# Check mGBA
$MgbaPath = $null
$MgbaPaths = @(
    "C:\Program Files\mGBA\mgba.exe",
    "C:\Program Files (x86)\mGBA\mgba.exe",
    "C:\Games\mGBA\mgba.exe",
    "${env:PROGRAMFILES}\mGBA\mgba.exe",
    "${env:PROGRAMFILES(x86)}\mGBA\mgba.exe"
)

foreach ($Path in $MgbaPaths) {
    if (Test-Path $Path) {
        $MgbaPath = $Path
        break
    }
}

if (-not $MgbaPath) {
    # Try to find in PATH
    $MgbaCmd = Get-Command mgba -ErrorAction SilentlyContinue
    if ($MgbaCmd) {
        $MgbaPath = $MgbaCmd.Source
    }
}

if (-not $MgbaPath) {
    Write-Host "⚠️  mGBA not found" -ForegroundColor Yellow
    Write-Host "   Install from: https://mgba.io/downloads.html" -ForegroundColor Yellow
    Write-Host "   Or via: choco install mgba-qt" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Continuing without emulator verification..." -ForegroundColor Yellow
} else {
    Write-Host "✅ mGBA found: $MgbaPath" -ForegroundColor Green
}

# Check Xbox controller
if (-not $SkipControllerCheck) {
    Write-Host ""
    Write-Host "🕹️  Checking for Xbox Series Controller..." -ForegroundColor Cyan
    Write-Host "   Please connect your Xbox Series X/S controller now." -ForegroundColor Yellow
    Write-Host "   (Press any button to continue...)" -ForegroundColor Yellow
    Write-Host ""
}

# Launch Python launcher
Write-Host ""
Write-Host "🚀 Launching game launcher..." -ForegroundColor Cyan
Write-Host ""

& $PythonExe $PyLauncher

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Game launcher exited with error" -ForegroundColor Red
    exit 1
}
