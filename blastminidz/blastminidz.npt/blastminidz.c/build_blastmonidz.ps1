$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$gcc = 'C:\ProgramData\mingw64\mingw64\bin\gcc.exe'
$archiveZip = Join-Path (Split-Path -Parent (Split-Path -Parent $root)) 'Bomberman.zip'
$archiveCache = Join-Path $root 'bomberman_archive_cache'

Set-Location $root

if (Test-Path $archiveZip) {
    if (Test-Path $archiveCache) {
        Remove-Item $archiveCache -Recurse -Force
    }
    Expand-Archive -LiteralPath $archiveZip -DestinationPath $archiveCache -Force
}

$sources = @(
    'blastmonidz.c',
    'blastmonidz_bridge.c',
    'blastmonidz_assets.c',
    'blastmonidz_analysis.c',
    'blastmonidz_game.c',
    'blastmonidz_window.c'
)

$buildArgs = @(
    '-std=c11',
    '-Wall',
    '-Wextra',
    '-pedantic',
    '-O2'
) + $sources + @(
    '-o', 'blastmonidz_host.exe',
    '-lgdi32', '-luser32', '-lmsimg32', '-lole32', '-lwindowscodecs', '-luuid'
)

& $gcc @buildArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$smokeArgs = @(
    '-std=c11',
    '-Wall',
    '-Wextra',
    '-pedantic',
    '-O2',
    'blastmonidz_assets.c',
    'blastmonidz_game.c',
    'blastmonidz_smoke_test.c',
    '-o', 'blastmonidz_smoke_test.exe'
)

& $gcc @smokeArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Output 'Built blastmonidz_host.exe and blastmonidz_smoke_test.exe'