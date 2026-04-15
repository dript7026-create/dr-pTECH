param(
    [switch]$BuildNativeGba = $false
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

    # GBA header includes Nintendo logo bytes at 0x04-0x07.
    if ($bytes[4] -eq 0x24 -and $bytes[5] -eq 0xFF -and $bytes[6] -eq 0xAE -and $bytes[7] -eq 0x51) {
        return "gba"
    }

    # GB header has Nintendo logo marker starting at 0x104.
    if ($bytes[0x104] -eq 0xCE -and $bytes[0x105] -eq 0xED -and $bytes[0x106] -eq 0x66 -and $bytes[0x107] -eq 0x66) {
        return "gb"
    }

    return "unknown"
}

$toolchainScript = Join-Path (Split-Path -Parent $PSScriptRoot) "workspace_toolchains.ps1"
if (Test-Path $toolchainScript) {
    & $toolchainScript -Quiet
}

Push-Location $PSScriptRoot
try {
    if (-not (Get-Command lcc -ErrorAction SilentlyContinue)) {
        throw "lcc not found in PATH. Run workspace_toolchains.ps1 or install the local GBDK toolchain."
    }

    Write-Host "Building armored_gear_fly_slight.gb (GBDK)"
    lcc -Wl-yt0x1B -Wl-j -Wm-yoA -Wm-ya4 -autobank -Wb-v -o armored_gear_fly_slight.gb src\main.c src\audio_runtime.c src\title_profile.c src\field_state.c src\save_ram.c src\passage_modules.c modules\PxGBPROG\src\pxgbprog.c modules\PxGBPROG\src\pxgbprog_pipeline.c modules\PxGBPROG\src\pxgbprog_depth_layers.c modules\PROGHONORAI\src\proghonorai.c modules\PROGHONORAI\submodules\HONORSPHERE\src\honorsphere.c
    if ($LASTEXITCODE -ne 0) {
        throw "GB build failed"
    }

    Write-Host "Built armored_gear_fly_slight.gb"

    $mainGbaPath = Join-Path $PSScriptRoot "armored_gear_fly_slight.gba"
    if (Test-Path $mainGbaPath) {
        $mainGbaType = Get-RomType -Path $mainGbaPath
        if ($mainGbaType -eq "gb") {
            Remove-Item -Path $mainGbaPath -Force
            Write-Host "Removed invalid armored_gear_fly_slight.gba (it was a GB ROM with .gba extension)" -ForegroundColor Yellow
        }
    }

    if ($BuildNativeGba) {
        $nativeBuildScript = Join-Path $PSScriptRoot "build_gba_native.ps1"
        if (-not (Test-Path $nativeBuildScript)) {
            throw "Native GBA build requested, but build_gba_native.ps1 was not found."
        }

        & $nativeBuildScript
        if ($LASTEXITCODE -ne 0) {
            throw "Native GBA build failed"
        }

        $nativeGbaPath = Join-Path $PSScriptRoot "armored_gear_fly_slight_native.gba"
        if ((Get-RomType -Path $nativeGbaPath) -ne "gba") {
            throw "Native output exists but is not a valid GBA ROM: $nativeGbaPath"
        }

        Copy-Item -Path $nativeGbaPath -Destination $mainGbaPath -Force
        Write-Host "Built armored_gear_fly_slight.gba (native GBA image)"
    } else {
        Write-Host "Skipped armored_gear_fly_slight.gba output to avoid mislabeled GB binaries." -ForegroundColor Yellow
        Write-Host "Use .\\build.ps1 -BuildNativeGba to generate a real GBA image." -ForegroundColor Yellow
    }
} catch {
    Write-Error "Build failed: $_"
    exit 3
} finally {
    Pop-Location
}