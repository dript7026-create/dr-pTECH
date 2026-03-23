param(
    [string]$Compiler = "C:\tools\msys64\mingw64\bin\g++.exe",
    [switch]$RunAfterBuild,
    [switch]$Autoplay
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputFile = Join-Path $projectRoot "gravo_demo.exe"

if (-not (Test-Path $Compiler)) {
    throw "Compiler not found at '$Compiler'."
}

Push-Location $projectRoot
try {
    & $Compiler -std=gnu++17 -municode -I ..\ORBEngine\include -I ..\egosphere gravo_demo.cpp gravo.c ..\ORBEngine\src\orbengine.c ..\ORBEngine\src\orbengine_game_kernel.cpp ..\egosphere\egosphere.c -lgdiplus -lgdi32 -luser32 -lshell32 -o $outputFile
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed with exit code $LASTEXITCODE."
    }

    Write-Host "Built $outputFile"

    if ($RunAfterBuild) {
        $arguments = @()
        if ($Autoplay) {
            $arguments += "--autoplay"
            $arguments += "--exit-on-completion"
        }
        Start-Process $outputFile -ArgumentList $arguments -WorkingDirectory $projectRoot
    }
}
finally {
    Pop-Location
}