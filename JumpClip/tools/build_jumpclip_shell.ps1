$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (!(Test-Path $python)) {
    $python = 'python'
}

& $python -m pip install pyinstaller | Out-Host
& $python -m PyInstaller --noconfirm --clean --windowed --onefile --name JumpClipShell --paths src src\jumpclip\gui.py | Out-Host

Write-Host "Built dist\JumpClipShell.exe"
