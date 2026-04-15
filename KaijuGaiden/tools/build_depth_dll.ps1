param(
    [switch]$VerboseOutput
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$buildRoot = Join-Path $repoRoot 'build\asm'
$objectFile = Join-Path $buildRoot 'hope_depth_core_x64.obj'
$bridgeSource = Join-Path $repoRoot 'src\hope_depth_bridge.c'
$dllFile = Join-Path $buildRoot 'hope_depth_core.dll'
$defFile = Join-Path $buildRoot 'hope_depth_core.def'

$gcc = Get-Command gcc -ErrorAction SilentlyContinue
if (-not $gcc) {
    throw 'gcc was not found on PATH. Install MinGW-w64 or expose gcc.exe before building the HOPE bridge DLL.'
}

if (-not (Test-Path $objectFile)) {
    throw "Assembly object not found: $objectFile. Run tools/build_depth_asm.ps1 first."
}

if (-not (Test-Path $bridgeSource)) {
    throw "Bridge source not found: $bridgeSource"
}

if (-not (Test-Path $buildRoot)) {
    New-Item -ItemType Directory -Path $buildRoot | Out-Null
}

Write-Host 'Linking HOPE depth bridge DLL...'
$compileArgs = @(
    '-shared'
    '-O2'
    '-o', $dllFile
    $bridgeSource
    $objectFile
    "-Wl,--output-def,$defFile"
)

if ($VerboseOutput) {
    & $gcc.Source @compileArgs
}
else {
    & $gcc.Source @compileArgs | Out-Null
}

if (-not (Test-Path $dllFile)) {
    throw 'gcc completed without producing the expected depth bridge DLL.'
}

Write-Host "Built: $dllFile"
