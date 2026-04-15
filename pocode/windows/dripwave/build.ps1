$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $projectRoot 'src\dripwave.c'
$buildDir = Join-Path $projectRoot 'build'
$outExe = Join-Path $buildDir 'dripwave.exe'
$runtimeDir = Join-Path $projectRoot 'runtime'

New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

$gcc = (Get-Command gcc -ErrorAction Stop).Source

& $gcc $src -o $outExe -std=c11 -O2 -municode -mwindows -static -static-libgcc -DUNICODE -D_UNICODE -lcomctl32 -lcomdlg32 -lshell32 -lz

if ($LASTEXITCODE -ne 0) {
	throw "gcc failed with exit code $LASTEXITCODE"
}

$runtimeCandidates = @()

if ($env:DRIPWAVE_BACKEND_SOURCE) {
	$runtimeCandidates += $env:DRIPWAVE_BACKEND_SOURCE
}

$runtimeCandidates += @(
	(Join-Path $runtimeDir 'ruffle_desktop.exe'),
	(Join-Path $runtimeDir 'flashplayer_32_sa.exe'),
	(Join-Path $runtimeDir 'flashplayer_sa.exe')
)

foreach ($candidate in $runtimeCandidates) {
	if (-not $candidate) {
		continue
	}
	if (Test-Path $candidate -PathType Leaf) {
		$target = Join-Path $buildDir (Split-Path -Leaf $candidate)
		Copy-Item $candidate $target -Force
		Write-Host "Bundled runtime $target"
	}
}

Write-Host "Built $outExe"