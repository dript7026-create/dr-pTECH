<#
.SYNOPSIS
    Build script for ECBMPS/CCP Studio - compilers and viewers.
.DESCRIPTION
    Compiles ecbmps_compiler, ccp_compiler, ecbmps_viewer, ccp_viewer.
    Tries MSVC (cl.exe) first, falls back to MinGW (gcc).
#>

$ErrorActionPreference = "Stop"
$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$buildDir = Join-Path $baseDir "build"
if (!(Test-Path $buildDir)) { New-Item -ItemType Directory -Path $buildDir | Out-Null }

# Download stb_image.h if missing
$stbPath = Join-Path $baseDir "viewer/stb_image.h"
if (!(Test-Path $stbPath)) {
    Write-Host "Downloading stb_image.h ..." -ForegroundColor Cyan
    $stbUrl = "https://raw.githubusercontent.com/nothings/stb/master/stb_image.h"
    try {
        Invoke-WebRequest -Uri $stbUrl -OutFile $stbPath -UseBasicParsing
        Write-Host "  Downloaded stb_image.h" -ForegroundColor Green
    } catch {
        Write-Host "  WARNING: Could not download stb_image.h - PNG assets will use BMP fallback" -ForegroundColor Yellow
    }
}

# Detect compiler
$useMSVC = $false
$useGCC  = $false
if (Get-Command cl.exe -ErrorAction SilentlyContinue) {
    $useMSVC = $true
    Write-Host "Using MSVC (cl.exe)" -ForegroundColor Cyan
} elseif (Get-Command gcc.exe -ErrorAction SilentlyContinue) {
    $useGCC = $true
    Write-Host "Using MinGW (gcc)" -ForegroundColor Cyan
} else {
    Write-Host "ERROR: No C compiler found. Install MSVC or MinGW." -ForegroundColor Red
    exit 1
}

$targets = @(
    @{
        Name   = "ecbmps_compiler"
        Source = "compiler/ecbmps_compiler.c"
        IsGUI  = $false
    },
    @{
        Name   = "ccp_compiler"
        Source = "compiler/ccp_compiler.c"
        IsGUI  = $false
    },
    @{
        Name   = "ecbmps_viewer"
        Source = @("viewer/ecbmps_viewer.c", "viewer/stb_image_impl.c")
        IsGUI  = $true
    },
    @{
        Name   = "ccp_viewer"
        Source = @("viewer/ccp_viewer.c", "viewer/ccp_gameplay_vm.c", "viewer/stb_image_impl.c")
        IsGUI  = $true
    }
)

$failed = @()

foreach ($t in $targets) {
    $sources = @()
    if ($t.Source -is [array]) {
        foreach ($s in $t.Source) { $sources += Join-Path $baseDir $s }
    } else {
        $sources += Join-Path $baseDir $t.Source
    }
    $out = Join-Path $buildDir "$($t.Name).exe"
    Write-Host "`nBuilding $($t.Name)..." -ForegroundColor Yellow

    if ($useMSVC) {
        $libs = @()
        if ($t.IsGUI) {
            $libs = @("/link", "user32.lib", "gdi32.lib", "comctl32.lib", "comdlg32.lib", "shell32.lib", "ole32.lib", "windowscodecs.lib")
        }
        $args = @("/nologo", "/W4", "/O2", "/Fe:$out") + $sources + $libs
        & cl.exe @args
    } else {
        $libs = @()
        if ($t.IsGUI) {
            $libs = @("-lgdi32", "-lcomctl32", "-lcomdlg32", "-lshell32", "-lole32", "-lwindowscodecs", "-mwindows", "-municode")
        }
        $args = @("-O2", "-Wall", "-Wextra") + $sources + @("-o", $out) + $libs
        & gcc.exe @args
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAILED: $($t.Name)" -ForegroundColor Red
        $failed += $t.Name
    } else {
        $size = (Get-Item $out).Length
        Write-Host "  OK: $out - $size bytes" -ForegroundColor Green
    }
}

Write-Host ""
if ($failed.Count -gt 0) {
    $failList = $failed -join ", "
    Write-Host "Build completed with errors: $failList" -ForegroundColor Red
    exit 1
} else {
    Write-Host "All 4 targets built successfully." -ForegroundColor Green
    Get-ChildItem $buildDir -Filter "*.exe" | ForEach-Object {
        $fn = $_.Name; $fl = $_.Length
        Write-Host "  $fn - $fl bytes"
    }
}
