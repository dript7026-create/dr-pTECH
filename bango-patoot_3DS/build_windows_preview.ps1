$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$compiler = "C:\tools\msys64\mingw64\bin\g++.exe"
$msvcVcvars = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
$python = Join-Path $projectRoot "..\.venv\Scripts\python.exe"
$source = Join-Path $projectRoot "windows_test_world.cpp"
$engineSource = Join-Path $projectRoot "bango_engine_target\src\bango_engine_target.c"
$aiSource = Join-Path $projectRoot "bango_engine_target\src\bango_ai_stack.c"
$spaceFrameSource = Join-Path $projectRoot "bango_engine_target\src\bango_space_frame.c"
$telemetrySource = Join-Path $projectRoot "bango_engine_target\src\bango_telemetry_bridge_stub.c"
$output = Join-Path $projectRoot "BangoPatootWindowsPreview.exe"
$includeRoot = Join-Path $projectRoot "bango_engine_target\include"

if (-not (Test-Path $msvcVcvars) -and -not (Test-Path $compiler)) {
    throw "Missing Windows preview compiler toolchains. Checked MSVC at $msvcVcvars and MinGW at $compiler"
}

if (-not (Test-Path $python)) {
    throw "Missing python interpreter: $python"
}

& $python (Join-Path $projectRoot "tools\build_rendering_pass_manifests.py")
if ($LASTEXITCODE -ne 0) {
    throw "Failed to build Recraft rendering manifests."
}

& $python (Join-Path $projectRoot "tools\generate_placeholder_rig_assets.py")
if ($LASTEXITCODE -ne 0) {
    throw "Failed to generate placeholder rig assets."
}

& $python (Join-Path $projectRoot "tools\build_test_level_from_tiles.py")
if ($LASTEXITCODE -ne 0) {
    throw "Failed to build tile-driven test level assets."
}

& $python (Join-Path $projectRoot "tools\build_actor_blockout.py")
if ($LASTEXITCODE -ne 0) {
    throw "Failed to build actor blockout assets."
}

if (Test-Path $msvcVcvars) {
    $tempDir = Join-Path $projectRoot ".tmp"
    $msvcBuildScript = Join-Path $tempDir "build_windows_preview_msvc.cmd"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    $scriptContent = @"
@echo off
call "$msvcVcvars" >nul
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /EHsc /Fe:"$output" "$source" "$engineSource" "$aiSource" "$spaceFrameSource" "$telemetrySource" /I "$includeRoot" /link gdiplus.lib gdi32.lib user32.lib msimg32.lib ole32.lib
exit /b %errorlevel%
"@
    Set-Content -Path $msvcBuildScript -Value $scriptContent -Encoding Ascii
    try {
        $buildProcess = Start-Process -FilePath "cmd.exe" -ArgumentList @("/d", "/c", "`"$msvcBuildScript`"") -Wait -NoNewWindow -PassThru
        $global:LASTEXITCODE = $buildProcess.ExitCode
    } finally {
        Remove-Item $msvcBuildScript -ErrorAction SilentlyContinue
    }
} else {
    & $compiler -std=gnu++17 -municode $source $engineSource $aiSource $spaceFrameSource $telemetrySource -I$includeRoot -lgdiplus -lgdi32 -luser32 -lmsimg32 -o $output
}

if ($LASTEXITCODE -ne 0) {
    throw "Windows preview build failed."
}

Write-Output "Built $output"