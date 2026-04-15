param(
    [switch]$IncludeNativeGba
)

Push-Location $PSScriptRoot
try {
    Write-Host "[1/4] Graphics compaction pass (shape cap 1000)"
    python tools/run_graphics_compaction_pass.py --shape-cap 1000
    if ($LASTEXITCODE -ne 0) { throw "Graphics compaction pass failed" }

    Write-Host "[2/4] Audio updated pass"
    python tools/generate_audio_assets.py --updated-pass
    if ($LASTEXITCODE -ne 0) { throw "Audio pass failed" }

    Write-Host "[3/4] Main build (.gb + .gba companion artifact)"
    powershell -ExecutionPolicy Bypass -File .\build.ps1
    if ($LASTEXITCODE -ne 0) { throw "Main build failed" }

    if ($IncludeNativeGba) {
        Write-Host "[4/4] Native GBA scaffold build"
        powershell -ExecutionPolicy Bypass -File .\build_gba_native.ps1
        if ($LASTEXITCODE -ne 0) { throw "Native GBA scaffold build failed" }
    } else {
        Write-Host "[4/4] Native GBA scaffold build skipped (use -IncludeNativeGba to enable)"
    }

    Write-Host "Pipeline complete"
} catch {
    Write-Error "Pipeline failed: $_"
    exit 3
} finally {
    Pop-Location
}
