param(
    [switch]$SmokeTest,
    [int]$Frames = 2400,
    [string]$OutputBasename = "smoke_test_preview"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv/Scripts/python.exe"

if (-not (Test-Path $python)) {
    $python = "python"
}

$arguments = @((Join-Path $PSScriptRoot "prototype.py"))

if ($SmokeTest) {
    $env:SDL_VIDEODRIVER = "dummy"
    $env:SDL_AUDIODRIVER = "dummy"
    $arguments += "--smoke-test"
    $arguments += "--frames"
    $arguments += "$Frames"
    $arguments += "--output-basename"
    $arguments += $OutputBasename
}

& $python @arguments