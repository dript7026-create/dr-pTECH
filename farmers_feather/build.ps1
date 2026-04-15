param()

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
    lcc -Wl-yt0x1B -Wl-j -Wm-yoA -Wm-ya4 -autobank -Wb-v -o armored_gear_fly_slight.gb src\main.c src\audio_runtime.c src\title_profile.c src\field_state.c src\save_ram.c src\passage_modules.c modules\PxGBPROG\src\pxgbprog.c modules\PxGBPROG\src\pxgbprog_pipeline.c modules\PROGHONORAI\src\proghonorai.c modules\PROGHONORAI\submodules\HONORSPHERE\src\honorsphere.c
    if ($LASTEXITCODE -ne 0) {
        throw "GB build failed"
    }

    Write-Host "Built armored_gear_fly_slight.gb"
} catch {
    Write-Error "Build failed: $_"
    exit 3
} finally {
    Pop-Location
}