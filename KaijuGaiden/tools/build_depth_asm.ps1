param(
    [switch]$VerboseOutput
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$asmRoot = Join-Path $repoRoot 'asm'
$buildRoot = Join-Path $repoRoot 'build\asm'
$sourceFile = Join-Path $asmRoot 'hope_depth_core_x64.asm'
$objectFile = Join-Path $buildRoot 'hope_depth_core_x64.obj'

$nasm = Get-Command nasm -ErrorAction SilentlyContinue
if (-not $nasm) {
    $fallbackCandidates = @(
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\nasm.exe')
    )
    $toolsRoot = Join-Path $env:USERPROFILE 'Tools'
    if (Test-Path $toolsRoot) {
        $toolsNasm = Get-ChildItem -Path $toolsRoot -Filter 'nasm.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
        if ($toolsNasm) {
            $fallbackCandidates += $toolsNasm
        }
    }
    $fallbackPath = $fallbackCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    if ($fallbackPath) {
        $nasm = [pscustomobject]@{ Source = $fallbackPath }
    }
}
if (-not $nasm) {
    throw 'nasm was not found on PATH and no known per-user fallback path was present.'
}

if (-not (Test-Path $sourceFile)) {
    throw "Assembly source not found: $sourceFile"
}

if (-not (Test-Path $buildRoot)) {
    New-Item -ItemType Directory -Path $buildRoot | Out-Null
}

Write-Host 'Assembling NASM x64 depth core...'
if ($VerboseOutput) {
    $listingFile = Join-Path $buildRoot 'hope_depth_core_x64.lst'
    & $nasm.Source '-f' 'win64' $sourceFile '-o' $objectFile '-l' $listingFile
}
else {
    & $nasm.Source '-f' 'win64' $sourceFile '-o' $objectFile
}

if (-not (Test-Path $objectFile)) {
    throw 'NASM completed without producing the expected object file.'
}

Write-Host "Built: $objectFile"