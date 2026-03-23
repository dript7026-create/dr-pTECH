<#
build.ps1 - Convenience wrapper to run the GBA Makefile using MSYS2/devkitPro

Usage:
  .\build.ps1
  .\build.ps1 -MsysPath "C:\msys64\usr\bin\bash.exe"

Behavior:
 - If MSYS2 bash is found at the default path (or provided via -MsysPath), this
   script will invoke bash -lc "cd /c/.../KaijuGaiden && make" so the devkitPro
   environment is used.
 - Otherwise, it will try to run `make` or `mingw32-make` directly if available.
#>

param(
    [string]$MsysPath = "C:\\devkitPro\\msys2\\usr\\bin\\bash.exe",
    [string]$MakeCmd = "make"
)

function To-BashPath($winPath) {
    $p = (Resolve-Path $winPath).Path
    $p = $p -replace '\\', '/'
    if ($p -match '^([A-Za-z]):/') {
        $drive = $matches[1].ToLower()
        $p = $p -replace '^[A-Za-z]:', "/$drive"
    }
    return $p
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectDir = Join-Path $scriptDir "KaijuGaiden"

Write-Host "Project:" $projectDir

if (Test-Path $MsysPath) {
    $bash = $MsysPath
    $bashProj = To-BashPath $projectDir
    $bashCommand = "export DEVKITPRO=/c/devkitPro; export DEVKITARM=/c/devkitPro/devkitARM; export DEVKITPPC=/c/devkitPro/devkitPPC; export DEVKITA64=/c/devkitPro/devkitA64; export PATH=/c/devkitPro/devkitARM/bin:/c/devkitPro/devkitA64/bin:/c/devkitPro/devkitPPC/bin:/c/devkitPro/tools/bin:/c/devkitPro/msys2/usr/bin:`$PATH; cd $bashProj && $MakeCmd"
    Write-Host "Running MSYS2 bash: $bash -lc '$bashCommand'"
    & $bash -lc $bashCommand
    exit $LASTEXITCODE
}

if (Get-Command $MakeCmd -ErrorAction SilentlyContinue) {
    Write-Host "Running $MakeCmd in PowerShell (project directory)"
    Push-Location $projectDir
    & $MakeCmd
    $rc = $LASTEXITCODE
    Pop-Location
    exit $rc
}

if (Get-Command mingw32-make -ErrorAction SilentlyContinue) {
    Write-Host "Running mingw32-make in PowerShell (project directory)"
    Push-Location $projectDir
    & mingw32-make -f Makefile
    $rc = $LASTEXITCODE
    Pop-Location
    exit $rc
}

Write-Error "MSYS2 bash or make/mingw32-make not found. Ensure devkitPro/MSYS2 is installed and on PATH."
exit 1
