param(
    [switch]$DryRun,
    [switch]$List,
    [switch]$IncludeManual,
    [switch]$StrictSkips,
    [string[]]$Project
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$toolchainScript = Join-Path $scriptDir "workspace_toolchains.ps1"

if (Test-Path $toolchainScript) {
    & $toolchainScript -Quiet
}

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = (Get-Command python -ErrorAction SilentlyContinue).Path
    if (-not $python) {
        $python = (Get-Command py -ErrorAction SilentlyContinue).Path
    }
}

if (-not $python) {
    Write-Error "Python executable not found. Create the workspace venv or install Python first."
    exit 1
}

$args = @("$scriptDir\workspace_build.py")
if ($DryRun) { $args += "--dry-run" }
if ($List) { $args += "--list" }
if ($IncludeManual) { $args += "--include-manual" }
if ($StrictSkips) { $args += "--strict-skips" }
foreach ($item in $Project) {
    $args += "--project"
    $args += $item
}

& $python @args
exit $LASTEXITCODE