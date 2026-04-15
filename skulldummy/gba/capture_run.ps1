param(
    [string]$RomPath,
    [string]$EmulatorPath,
    [string]$OutputAvi,
    [int]$DurationSeconds = 45,
    [switch]$Build
)

$ErrorActionPreference = 'Stop'

function Resolve-EmulatorPath {
    param([string]$RequestedPath)

    if ($RequestedPath) {
        if (Test-Path $RequestedPath) { return (Resolve-Path $RequestedPath).Path }
        throw "Emulator not found: $RequestedPath"
    }

    $documentsDir = [Environment]::GetFolderPath('MyDocuments')
    $candidates = @(
        $env:GBA_EMULATOR,
        (Join-Path $documentsDir 'visualboyadvance\visualboyadvance-m.exe'),
        'C:\Program Files\mGBA\mGBA.exe',
        'C:\Program Files (x86)\mGBA\mGBA.exe',
        'C:\Program Files\RetroArch\retroarch.exe'
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw 'No supported emulator was found. Pass -EmulatorPath or set GBA_EMULATOR.'
}

function Wait-ForWindowTitle {
    param(
        [int]$ProcessId,
        [int]$TimeoutSeconds = 20
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $proc) {
            throw 'Emulator exited before a window title became available.'
        }
        if ($proc.MainWindowTitle -and $proc.MainWindowTitle.Trim().Length -gt 0) {
            return $proc.MainWindowTitle.Trim()
        }
        Start-Sleep -Milliseconds 250
    }
    throw 'Timed out waiting for a non-empty emulator window title.'
}

    function Invoke-FfmpegCapture {
        param(
            [string[]]$Arguments,
            [string]$StdOutPath,
            [string]$StdErrPath
        )

        if (Test-Path $StdOutPath) { Remove-Item $StdOutPath -Force }
        if (Test-Path $StdErrPath) { Remove-Item $StdErrPath -Force }

        return Start-Process -FilePath 'ffmpeg' -ArgumentList $Arguments -Wait -PassThru -NoNewWindow `
            -RedirectStandardOutput $StdOutPath -RedirectStandardError $StdErrPath
    }

if (!(Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw 'ffmpeg not found in PATH.'
}

$root = $PSScriptRoot
$resolvedRom = if ($RomPath) {
    if (!(Test-Path $RomPath)) { throw "ROM not found: $RomPath" }
    (Resolve-Path $RomPath).Path
} else {
    Join-Path $root 'skulldummy_gba.gba'
}

if ($Build) {
    & (Join-Path $root 'build.ps1')
    if ($LASTEXITCODE -ne 0) {
        throw 'Build failed before capture.'
    }
}

if (!(Test-Path $resolvedRom)) {
    throw "ROM not found: $resolvedRom"
}

$resolvedEmulator = Resolve-EmulatorPath -RequestedPath $EmulatorPath
$captureDir = Join-Path $root 'capture'
if (!(Test-Path $captureDir)) {
    New-Item -ItemType Directory -Path $captureDir | Out-Null
}

$resolvedOutput = if ($OutputAvi) {
    $parent = Split-Path -Parent $OutputAvi
    if ($parent -and !(Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    $OutputAvi
} else {
    Join-Path $captureDir 'skulldummy_session.avi'
}

$ffmpegOut = Join-Path $captureDir 'capture_ffmpeg.out.log'
$ffmpegErr = Join-Path $captureDir 'capture_ffmpeg.err.log'
$logPath = Join-Path $captureDir 'capture_session_log.txt'

if (Test-Path $resolvedOutput) { Remove-Item $resolvedOutput -Force }
if (Test-Path $ffmpegOut) { Remove-Item $ffmpegOut -Force }
if (Test-Path $ffmpegErr) { Remove-Item $ffmpegErr -Force }
if (Test-Path $resolvedOutput) { Remove-Item $resolvedOutput -Force }

$emu = Start-Process -FilePath $resolvedEmulator -ArgumentList @($resolvedRom) -PassThru
$sessionLines = @(
    'SkullDummy GBA capture session',
    "Timestamp: $(Get-Date -Format s)",
    "ROM: $resolvedRom",
    "Emulator: $resolvedEmulator",
    "Output AVI: $resolvedOutput",
    "DurationSeconds: $DurationSeconds"
)

try {
    Start-Sleep -Seconds 2
    $windowTitle = Wait-ForWindowTitle -ProcessId $emu.Id -TimeoutSeconds 25
    $sessionLines += "ResolvedWindowTitle: $windowTitle"

    $ffmpegArgs = @(
        '-hide_banner',
        '-loglevel', 'error',
        '-y',
        '-f', 'gdigrab',
        '-framerate', '30',
        '-draw_mouse', '0',
        '-i', "title=$windowTitle",
        '-t', ([string]$DurationSeconds),
        '-c:v', 'mpeg4',
        '-q:v', '4',
        $resolvedOutput
    )

        $windowCaptureArgs = @(
            '-hide_banner',
            '-loglevel', 'error',
            '-y',
            '-f', 'gdigrab',
            '-framerate', '30',
            '-draw_mouse', '0',
            '-i', "title=$windowTitle",
            '-t', ([string]$DurationSeconds),
            '-c:v', 'mpeg4',
            '-q:v', '4',
            $resolvedOutput
        )

        $ffmpeg = Invoke-FfmpegCapture -Arguments $windowCaptureArgs -StdOutPath $ffmpegOut -StdErrPath $ffmpegErr
        $captureMode = 'window'

        if ($ffmpeg.ExitCode -ne 0) {
            if (Test-Path $resolvedOutput) { Remove-Item $resolvedOutput -Force }

            $desktopCaptureArgs = @(
                '-hide_banner',
                '-loglevel', 'error',
                '-y',
                '-f', 'gdigrab',
                '-framerate', '30',
                '-draw_mouse', '0',
                '-i', 'desktop',
                '-t', ([string]$DurationSeconds),
                '-c:v', 'mpeg4',
                '-q:v', '4',
                $resolvedOutput
            )

            $ffmpeg = Invoke-FfmpegCapture -Arguments $desktopCaptureArgs -StdOutPath $ffmpegOut -StdErrPath $ffmpegErr
            $captureMode = 'desktop'
        }

        if ($ffmpeg.ExitCode -ne 0) {
            throw "ffmpeg capture failed with exit code $($ffmpeg.ExitCode)"
    }

    if (Test-Path $resolvedOutput) {
        $avi = Get-Item $resolvedOutput
        $sessionLines += 'CaptureStatus: success'
            $sessionLines += "CaptureMode: $captureMode"
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
    Set-Content -Path $logPath -Value $sessionLines -Encoding UTF8
}