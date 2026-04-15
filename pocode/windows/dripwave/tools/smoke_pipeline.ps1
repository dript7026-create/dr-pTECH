$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = (Resolve-Path (Join-Path $projectRoot '..\..\..')).Path
$buildScript = Join-Path $projectRoot 'build.ps1'
$buildDir = Join-Path $projectRoot 'build'
$sampleSwf = Join-Path $buildDir 'sample_valid.swf'
$sampleFarim = Join-Path $buildDir 'sample_valid.farim'
$packScript = Join-Path $PSScriptRoot 'make_farim_from_swf.py'

$pythonCandidates = @(
    (Join-Path $workspaceRoot '.venv\Scripts\python.exe'),
    (Get-Command py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
) | Where-Object { $_ -and (Test-Path $_ -ErrorAction SilentlyContinue) }

if (-not $pythonCandidates) {
    throw 'No usable Python interpreter was found for the dripwave smoke pipeline.'
}

$python = $pythonCandidates[0]

& $buildScript

New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

@'
from pathlib import Path

def pack_rect(nbits, xmin, xmax, ymin, ymax):
    values = [xmin, xmax, ymin, ymax]
    bits = []
    for shift in range(4, -1, -1):
        bits.append((nbits >> shift) & 1)
    for value in values:
        if value < 0:
            value = (1 << nbits) + value
        for shift in range(nbits - 1, -1, -1):
            bits.append((value >> shift) & 1)
    while len(bits) % 8 != 0:
        bits.append(0)
    out = bytearray()
    for index in range(0, len(bits), 8):
        byte = 0
        for bit in bits[index:index + 8]:
            byte = (byte << 1) | bit
        out.append(byte)
    return bytes(out)

rect = pack_rect(6, 0, 20, 0, 20)
payload = rect + bytes([0x00, 0x01, 0x01, 0x00])
swf = b'FWS' + bytes([9]) + (8 + len(payload)).to_bytes(4, 'little') + payload
path = Path(r'__SAMPLE_SWF__')
path.write_bytes(swf)
print(path)
'@.Replace('__SAMPLE_SWF__', $sampleSwf.Replace('\', '\\')) | & $python -

& $python $packScript $sampleSwf $sampleFarim

Set-Location $buildDir
$proc = Start-Process -FilePath (Join-Path $buildDir 'dripwave.exe') -ArgumentList '--smoke', 'sample_valid.swf', 'sample_valid.farim' -NoNewWindow -Wait -PassThru
Write-Host "SMOKE_EXIT=$($proc.ExitCode)"
if ($proc.ExitCode -ne 0) {
    throw "dripwave smoke pipeline failed with exit code $($proc.ExitCode)"
}