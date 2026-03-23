param(
    [string]$EmulatorPath = "C:\Users\rrcar\Documents\visualboyadvance\visualboyadvance-m.exe",
    [string]$RomPath = "C:\Users\rrcar\Documents\drIpTECH\tommybeta\tommybeta_autoplay.gba",
    [string]$OutputAvi = "C:\Users\rrcar\Documents\drIpTECH\tommybeta\capture\tommybeta_100_percent_run.avi",
    [string]$LogPath = "C:\Users\rrcar\Documents\drIpTECH\tommybeta\capture\capture_session_log.txt",
    [int]$DurationSeconds = 255,
    [switch]$ProbeOnly
)

$ErrorActionPreference = 'Stop'

function Wait-ForVbaWindowTitle {
    param(
        [int]$ProcessId,
        [int]$TimeoutSeconds = 20
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $proc) {
            throw "VisualBoyAdvance-M exited before a window title became available."
        }
        if ($proc.MainWindowTitle -and $proc.MainWindowTitle.Trim().Length -gt 0) {
            return $proc.MainWindowTitle.Trim()
        }
        Start-Sleep -Milliseconds 250
    }
    throw "Timed out waiting for a non-empty VisualBoyAdvance-M window title."
}

if (!(Test-Path $EmulatorPath)) { throw "Emulator not found: $EmulatorPath" }
if (!(Test-Path $RomPath)) { throw "ROM not found: $RomPath" }
if (!(Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "ffmpeg not found in PATH" }

$captureDir = Split-Path -Parent $OutputAvi
if (!(Test-Path $captureDir)) { New-Item -ItemType Directory -Path $captureDir | Out-Null }

$ffmpegErr = Join-Path $captureDir ($(if ($ProbeOnly) { 'probe_ffmpeg.err.log' } else { 'capture_ffmpeg.err.log' }))
$ffmpegOut = Join-Path $captureDir ($(if ($ProbeOnly) { 'probe_ffmpeg.out.log' } else { 'capture_ffmpeg.out.log' }))
$sessionLines = @()
$sessionLines += "TommyBeta VBA-M capture session"
$sessionLines += "Timestamp: $(Get-Date -Format s)"
$sessionLines += "ROM: $RomPath"
$sessionLines += "Emulator: $EmulatorPath"
$sessionLines += "Output AVI: $OutputAvi"
$sessionLines += "DurationSeconds: $DurationSeconds"

$emu = Start-Process -FilePath $EmulatorPath -ArgumentList @($RomPath) -PassThru
try {
    Start-Sleep -Seconds 2
    $windowTitle = Wait-ForVbaWindowTitle -ProcessId $emu.Id -TimeoutSeconds 25
    $sessionLines += "ResolvedWindowTitle: $windowTitle"

    if (Test-Path $OutputAvi) { Remove-Item $OutputAvi -Force }
    if (Test-Path $ffmpegErr) { Remove-Item $ffmpegErr -Force }
    if (Test-Path $ffmpegOut) { Remove-Item $ffmpegOut -Force }

    $gdigrabTitle = "title=$windowTitle"
    $ffmpegArgs = @(
        '-y',
        '-f', 'gdigrab',
        '-framerate', '30',
        '-draw_mouse', '0',
        '-i', $gdigrabTitle,
        '-t', ([string]$DurationSeconds),
        '-c:v', 'mpeg4',
        '-q:v', '4',
        $OutputAvi
    )

    & ffmpeg @ffmpegArgs 1> $ffmpegOut 2> $ffmpegErr
    if ($LASTEXITCODE -ne 0) {
        throw "ffmpeg capture failed with exit code $LASTEXITCODE"
    }

    $sessionLines += "CaptureStatus: success"
    if (Test-Path $OutputAvi) {
        $avi = Get-Item $OutputAvi
        $sessionLines += "CaptureBytes: $($avi.Length)"
    }
}
finally {
    $proc = Get-Process -Id $emu.Id -ErrorAction SilentlyContinue
    if ($null -ne $proc) {
        Stop-Process -Id $emu.Id -Force
    }
    $sessionLines += "ffmpeg stdout log: $ffmpegOut"
    $sessionLines += "ffmpeg stderr log: $ffmpegErr"
    Set-Content -Path $LogPath -Value $sessionLines -Encoding UTF8
}