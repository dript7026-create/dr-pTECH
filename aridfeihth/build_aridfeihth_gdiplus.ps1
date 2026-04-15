$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path $projectRoot "..\build\aridfeihth"
$outputExe = Join-Path $outputDir "AridfeihthGDIPlusDemo.exe"
$source = Join-Path $projectRoot "aridfeihth_runtime_gdiplus.cpp"
$buildLog = Join-Path $projectRoot "build_aridfeihth_gdiplus_build.log"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
Set-Content -Path $buildLog -Value "Building $source" -Encoding Ascii

$msvcVcvars = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
$mingw = (Get-Command g++ -ErrorAction SilentlyContinue)

if (Test-Path $msvcVcvars) {
    $tempDir = Join-Path $projectRoot ".tmp"
    $buildScript = Join-Path $tempDir "build_aridfeihth_gdiplus.cmd"
    $objectFile = Join-Path $tempDir "aridfeihth_runtime_gdiplus.obj"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    @"
@echo off
echo batch_start> "$buildLog"
call "$msvcVcvars" >nul
echo vcvars_exit=%errorlevel%>> "$buildLog"
if errorlevel 1 exit /b 1
echo cl_launch>> "$buildLog"
    cl /nologo /std:c++17 /EHsc /Fo"$objectFile" /Fe:"$outputExe" "$source" /link gdiplus.lib gdi32.lib user32.lib ole32.lib winmm.lib > "$buildLog" 2>&1
echo cl_exit=%errorlevel%>> "$buildLog"
exit /b %errorlevel%
"@ | Set-Content -Path $buildScript -Encoding Ascii
    try {
        & $buildScript
        if ($LASTEXITCODE -ne 0) {
            throw "MSVC build failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Remove-Item $buildScript -ErrorAction SilentlyContinue
    }
}
elseif ($mingw) {
    & $mingw.Source -std=gnu++17 -municode "$source" -lgdiplus -lgdi32 -luser32 -lole32 -lwinmm -luuid -o "$outputExe" *> $buildLog
    if ($LASTEXITCODE -ne 0) {
        throw "MinGW build failed with exit code $LASTEXITCODE."
    }
}
else {
    throw "No supported C++ toolchain found. Install MSVC Build Tools or ensure g++ is on PATH."
}

& "$outputExe" --smoke | Tee-Object -FilePath $buildLog -Append
if ($LASTEXITCODE -ne 0) {
    throw "Runtime smoke check failed with exit code $LASTEXITCODE."
}

Write-Output "Built $outputExe"