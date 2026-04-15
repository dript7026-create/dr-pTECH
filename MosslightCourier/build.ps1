$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $root "src\mosslight_courier.c"
$out = Join-Path $root "mosslight_courier.exe"
$gcc = "C:\ProgramData\mingw64\mingw64\bin\gcc.exe"
if (-not (Test-Path $gcc)) {
    $gcc = (Get-Command gcc -ErrorAction Stop).Source
}

Push-Location $root
try {
    & $gcc $src -std=c11 -O2 -Wall -Wextra -pedantic -mwindows -lgdi32 -luser32 -lmsimg32 -lwinmm -o $out
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    Write-Host "Built $out"
}
finally {
    Pop-Location
}