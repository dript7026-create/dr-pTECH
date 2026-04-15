param(
    [string]$RomPath,
    [string]$EmulatorPath,
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
        throw 'Build failed before launch.'
    }
}

if (!(Test-Path $resolvedRom)) {
    throw "ROM not found: $resolvedRom"
}

$resolvedEmulator = Resolve-EmulatorPath -RequestedPath $EmulatorPath
Write-Host "Launching $resolvedRom"
Write-Host "Emulator: $resolvedEmulator"
Start-Process -FilePath $resolvedEmulator -ArgumentList @($resolvedRom) | Out-Null