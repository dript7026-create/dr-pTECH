$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$distRoot = Join-Path $root 'dist'
$packageDir = Join-Path $distRoot 'blastmonidz_deliverable'
$zipPath = Join-Path $distRoot 'blastmonidz_deliverable.zip'

Set-Location $root

& (Join-Path $root 'build_blastmonidz.ps1')

if (Test-Path $packageDir) {
    Remove-Item $packageDir -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

New-Item -ItemType Directory -Path $packageDir | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageDir 'profiles') | Out-Null

Copy-Item (Join-Path $root 'blastmonidz_host.exe') $packageDir
Copy-Item (Join-Path $root 'launch_blastmonidz.cmd') $packageDir
Copy-Item (Join-Path $root 'BLASTMONIDZ_DELIVERABLE.md') $packageDir
Copy-Item (Join-Path $root 'bomberman_archive_cache') $packageDir -Recurse

if (Test-Path (Join-Path $root 'blastmonidz_run_profile.txt')) {
    Copy-Item (Join-Path $root 'blastmonidz_run_profile.txt') (Join-Path $packageDir 'profiles')
}
if (Test-Path (Join-Path $root 'blastmonidz_replay_summary.txt')) {
    Copy-Item (Join-Path $root 'blastmonidz_replay_summary.txt') (Join-Path $packageDir 'profiles')
}

Compress-Archive -Path (Join-Path $packageDir '*') -DestinationPath $zipPath -Force

Write-Output "Packaged deliverable: $packageDir"
Write-Output "Packaged zip: $zipPath"