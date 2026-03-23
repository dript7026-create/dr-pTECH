param(
    [switch]$RebuildVenv
)

$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Join-Path $packageRoot 'repo'
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'

if ($RebuildVenv -and (Test-Path (Join-Path $repoRoot '.venv'))) {
    Remove-Item (Join-Path $repoRoot '.venv') -Recurse -Force
}

if (-not (Test-Path $venvPython)) {
    Push-Location $repoRoot
    try {
        python -m venv .venv
        & .\.venv\Scripts\python.exe -m pip install --upgrade pip
        & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    }
    finally {
        Pop-Location
    }
}

Push-Location $repoRoot
try {
    & $venvPython -m football_predictor.main
}
finally {
    Pop-Location
}
