param(
    [switch]$SkipDependencyInstall,
    [switch]$SkipPackaging,
    [switch]$SkipWrapperBuild,
    [switch]$SkipAsmBuild
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) {
    throw 'Python launcher `py` was not found on PATH. Install Python for Windows first.'
}

Set-Location $repoRoot

Write-Host 'Kaiju Gaiden Windows Xbox host build'
Write-Host "Repo root: $repoRoot"

Write-Host 'Checking Tkinter availability...'
& py -3 .\host_check_tk.py

if (-not $SkipDependencyInstall) {
    Write-Host 'Installing graphical host dependencies...'
    & py -3 -m pip install -r .\requirements-graphical.txt pyinstaller
}

if (-not $SkipWrapperBuild) {
    $gcc = Get-Command gcc -ErrorAction SilentlyContinue
    if ($gcc) {
        if (-not (Test-Path .\build)) {
            New-Item -ItemType Directory -Path .\build | Out-Null
        }
        Write-Host 'Building optional XInput wrapper DLL...'
        & gcc -shared -o .\build\xinput_wrapper.dll .\src\xinput_wrapper.c '-Wl,--output-def,build\xinput_wrapper.def'
    }
    else {
        Write-Host 'GCC not found; skipping optional xinput_wrapper.dll build. Native ctypes XInput loading will still be attempted.'
    }
}

if (-not $SkipAsmBuild) {
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
    if ($nasm) {
        Write-Host 'Building NASM depth-core scaffold...'
        & powershell -ExecutionPolicy Bypass -File .\tools\build_depth_asm.ps1
        $gcc = Get-Command gcc -ErrorAction SilentlyContinue
        if ($gcc) {
            Write-Host 'Building HOPE depth bridge DLL...'
            & powershell -ExecutionPolicy Bypass -File .\tools\build_depth_dll.ps1
        }
        else {
            Write-Host 'GCC not found; skipping optional HOPE depth bridge DLL build.'
        }
    }
    else {
        Write-Host 'NASM not found; skipping optional x64 depth-core scaffold build.'
    }
}

Write-Host 'Running controller/input contract verification...'
& py -3 .\tools\verify_input_contract.py

if ($SkipPackaging) {
    Write-Host 'Packaging skipped. Launch with: py -3 .\host_graphical.py'
    exit 0
}

Write-Host 'Packaging Windows executable with PyInstaller...'
& py -3 -m PyInstaller --noconfirm .\kaijugaiden_gui.spec

$distExe = Join-Path $repoRoot 'dist\kaijugaiden_windows_xbox\kaijugaiden_windows_xbox.exe'
if (Test-Path $distExe) {
    Write-Host "Built: $distExe"
}
else {
    Write-Warning 'PyInstaller completed but the expected executable path was not found.'
}