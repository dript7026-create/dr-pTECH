param(
    [int]$StageLimit = 1,
    [switch]$NoRenderer
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root 'kaijugaiden_sdl_console.exe'
$daemon = Join-Path $PSScriptRoot 'aiasmr_daemon.py'
$renderer = Join-Path $PSScriptRoot 'aiasmr_renderer.py'
$python = 'c:\Users\rrcar\Documents\drIpTECH\.venv\Scripts\python.exe'
$reports = Join-Path $root 'reports\aiasmr'
$renderOut = Join-Path $reports 'render'

if (-not (Test-Path $exe)) {
    throw "Missing host executable: $exe"
}

if (-not (Test-Path $daemon)) {
    throw "Missing daemon script: $daemon"
}

if (-not (Test-Path $python)) {
    $python = 'python'
}

if (Test-Path $reports) {
    Remove-Item $reports -Recurse -Force
}
New-Item $reports -ItemType Directory | Out-Null

$env:KAIJU_AUTOPLAY = '1'
$env:KAIJU_AUTOPLAY_STAGE_LIMIT = [string]$StageLimit

$rendererJob = $null
if (-not $NoRenderer) {
    if (-not (Test-Path $renderer)) {
        throw "Missing renderer script: $renderer"
    }
    $rendererArgs = @($renderer, '--state', (Join-Path $reports 'aiasmr_state.json'), '--out-dir', $renderOut, '--idle-exit-seconds', '6')
    $rendererJob = Start-Job -ScriptBlock {
        param($pythonPath, $argList)
        & $pythonPath @argList
    } -ArgumentList $python, $rendererArgs
}

try {
    & $python $daemon --out-dir $reports --exe $exe
    $exitCode = $LASTEXITCODE
}
finally {
    if ($rendererJob) {
        Wait-Job $rendererJob -Timeout 12 | Out-Null
        Receive-Job $rendererJob | Write-Output
        Remove-Job $rendererJob -Force
    }
}

exit $exitCode