param()

Push-Location $PSScriptRoot
try {
    powershell -ExecutionPolicy Bypass -File .\build.ps1 -Target gba-autoplay
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}