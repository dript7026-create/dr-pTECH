<#
.SYNOPSIS
Launch Dress SparLE Light Envisioned SWF in Ruffle emulator

.DESCRIPTION
Verifies Ruffle Desktop installation, extracts SWF from FARIM if needed,
and launches the Flash game in the Ruffle runtime environment.

.PARAMETER ProjectPath
Path to the Dress SparLE project. Defaults to current directory if Dress SparLE found.

.PARAMETER GameFile
Specify 'swf', 'farim', or 'auto' (default). Auto tries FARIM first, falls back to SWF.

.EXAMPLE
.\play_in_ruffle.ps1

.EXAMPLE
.\play_in_ruffle.ps1 -GameFile swf
#>

param(
    [string]$ProjectPath = $(
        if (Test-Path ".\dress-sparle-light-envisioned.swf") { "." }
        elseif (Test-Path "..\projects\dress-sparle-light-envisioned") { "..\projects\dress-sparle-light-envisioned" }
        else { "..\..\..\..\..\pocode\windows\dripwave\projects\dress-sparle-light-envisioned" }
    ),
    [ValidateSet('swf', 'farim', 'auto')]
    [string]$GameFile = 'auto'
)

$ErrorActionPreference = "Stop"

# Color helpers
function Write-Status { Write-Host "[->] $($args -join ' ')" -ForegroundColor Cyan }
function Write-Success { Write-Host "[OK] $($args -join ' ')" -ForegroundColor Green }
function Write-Error { Write-Host "[!] $($args -join ' ')" -ForegroundColor Red }
function Write-Warn { Write-Host "[*] $($args -join ' ')" -ForegroundColor Yellow }

# Verify project path
Write-Status "Validating Dress SparLE project at: $ProjectPath"
if (!(Test-Path $ProjectPath)) {
    Write-Error "Project path not found: $ProjectPath"
    exit 1
}

$ProjectPath = (Resolve-Path $ProjectPath).Path
Write-Success "Project path resolved: $ProjectPath"

# Verify game assets exist
$swfPath = Join-Path $ProjectPath "bin\dress-sparle-light-envisioned.swf"
$farimPath = Join-Path $ProjectPath "bin\dress-sparle-light-envisioned.farim"

if ($GameFile -eq 'auto') {
    if (Test-Path $farimPath) {
        Write-Status "FARIM found, will use: $farimPath"
        $GameFile = 'farim'
    } elseif (Test-Path $swfPath) {
        Write-Status "SWF found (no FARIM), will use: $swfPath"
        $GameFile = 'swf'
    } else {
        Write-Error "Neither SWF nor FARIM found in: $(Join-Path $ProjectPath 'bin\')"
        exit 1
    }
}

if ($GameFile -eq 'farim' -and !(Test-Path $farimPath)) {
    Write-Error "FARIM not found: $farimPath"
    exit 1
}

if ($GameFile -eq 'swf' -and !(Test-Path $swfPath)) {
    Write-Error "SWF not found: $swfPath"
    exit 1
}

# Check for Ruffle Desktop
Write-Status "Checking for Ruffle Desktop installation..."

$ruffleExe = $null

# Try common installation paths
$searchPaths = @(
    "C:\Program Files (x86)\Ruffle\Ruffle.exe",
    "C:\Program Files\Ruffle\Ruffle.exe",
    "C:\Program Files\ruffle\bin\ruffle.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Ruffle\Ruffle.exe",
    "C:\tools\ruffle\Ruffle.exe"
)

foreach ($path in $searchPaths) {
    if (Test-Path $path) {
        $ruffleExe = $path
        Write-Success "Found Ruffle at: $ruffleExe"
        break
    }
}

# Try to find via where command if not found yet
if (!$ruffleExe) {
    try {
        $whereResult = @(where.exe Ruffle.exe 2>$null)
        if ($whereResult -and $whereResult[0]) {
            $ruffleExe = $whereResult[0].Trim()
            if ($ruffleExe) {
                Write-Success "Found Ruffle via PATH: $ruffleExe"
            }
        }
    } catch {
        $ruffleExe = $null
    }
}

# Try to find via Chocolatey
if (!$ruffleExe) {
    $chocoPath = "C:\ProgramData\chocolatey\bin\ruffle.exe"
    if (Test-Path $chocoPath) {
        $ruffleExe = $chocoPath
        Write-Success "Found Ruffle Desktop (Chocolatey): $ruffleExe"
    }
}

# If still not found, offer to install
if (!$ruffleExe) {
    Write-Warn "Ruffle Desktop not found"
    Write-Status "Ruffle Desktop can be installed via Chocolatey"
    
    $choco = (where.exe choco.exe)[0]
    if (!$choco) {
        Write-Error "Chocolatey not installed. Please install Chocolatey or manually download Ruffle from https://ruffle.rs"
        exit 1
    }
    
    $response = Read-Host "Install ruffle-desktop via Chocolatey? (y/n)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Warn "Skipping installation. Manual installation: https://ruffle.rs"
        exit 1
    }
    
    Write-Status "Installing ruffle-desktop..."
    & choco install ruffle-desktop -y
    
    if (!$?) {
        Write-Error "Failed to install ruffle-desktop"
        exit 1
    }
    
    Write-Success "Ruffle Desktop installed"
    
    # Retry search
    $ruffleExe = (where.exe Ruffle.exe)[0]
    if (!$ruffleExe) {
        $ruffleExe = "C:\Program Files (x86)\Ruffle\Ruffle.exe"
    }
    
    if (!(Test-Path $ruffleExe)) {
        Write-Error "Could not locate Ruffle.exe after installation"
        exit 1
    }
}

# Handle FARIM extraction if needed
$launchFile = $null

if ($GameFile -eq 'farim') {
    Write-Status "Extracting SWF from FARIM: $farimPath"
    
    $tempDir = [System.IO.Path]::GetTempPath()
    $extractDir = Join-Path $tempDir "dress-sparle-extract-$(Get-Random)"
    $tempZipPath = Join-Path $tempDir "temp-farim-$(Get-Random).zip"
    
    New-Item -ItemType Directory -Path $extractDir | Out-Null
    
    try {
        # Copy FARIM as ZIP (FARIM is ZIP internally)
        Copy-Item -Path $farimPath -Destination $tempZipPath -Force
        
        # FARIM is a ZIP file, extract with SWF inside
        Expand-Archive -Path $tempZipPath -DestinationPath $extractDir -Force
        
        $swfInFarim = Get-ChildItem $extractDir -Filter "*.swf" -Recurse | Select-Object -First 1
        
        if ($swfInFarim) {
            $launchFile = $swfInFarim.FullName
            Write-Success "Extracted SWF: $launchFile"
        } else {
            Write-Error "No SWF found in FARIM archive"
            Remove-Item -Path $extractDir -Recurse -Force
            Remove-Item -Path $tempZipPath -Force
            exit 1
        }
        
        # Cleanup temp ZIP
        Remove-Item -Path $tempZipPath -Force
    } catch {
        Write-Error "Failed to extract FARIM: $_"
        if (Test-Path $extractDir) {
            Remove-Item -Path $extractDir -Recurse -Force
        }
        if (Test-Path $tempZipPath) {
            Remove-Item -Path $tempZipPath -Force
        }
        exit 1
    }
} else {
    $launchFile = $swfPath
}

# Launch in Ruffle
Write-Status "Launching in Ruffle: "$launchFile""

try {
    & $ruffleExe "$launchFile"
    Write-Success "Ruffle launched successfully"
} catch {
    Write-Error "Failed to launch Ruffle: $_"
    exit 1
}

Write-Success "Game session complete"
