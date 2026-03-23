param(
    [string]$Compiler = "C:\tools\msys64\mingw64\bin\g++.exe",
    [switch]$RunAfterBuild
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceFile = Join-Path $projectRoot "src\innsmouth_island_demo.cpp"
$outputFile = Join-Path $projectRoot "innsmouth_island_demo.exe"

if (-not (Test-Path $Compiler)) {
    throw "Compiler not found at '$Compiler'."
}

if (-not (Test-Path $sourceFile)) {
    throw "Source file not found at '$sourceFile'."
}

Push-Location $projectRoot
try {
    & $Compiler -municode $sourceFile -lgdiplus -lgdi32 -luser32 -lshell32 -o $outputFile
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed with exit code $LASTEXITCODE."
    }

    Write-Host "Built $outputFile"

    if ($RunAfterBuild) {
        Start-Process $outputFile -WorkingDirectory $projectRoot
    }
}
finally {
    Pop-Location
}