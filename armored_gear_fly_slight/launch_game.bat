@echo off
REM Armored Gear: Fly Slight - Xbox Controller Launch Batch File
REM Windows CMD version of launch_game.ps1

setlocal enabledelayedexpansion

cd /d "%~dp0" || exit /b 1

set ROM_PATH=%cd%\armored_gear_fly_slight.gb
if not exist "%ROM_PATH%" set ROM_PATH=%cd%\armored_gear_fly_slight.gba
if not exist "%ROM_PATH%" set ROM_PATH=%cd%\armored_gear_fly_slight_native.gba
set PY_LAUNCHER=%cd%\launch_with_xbox_controller.py

echo.
echo ======================================================================
echo.
echo   [91m╔═══════════════════════════════════════════════════════════════╗[0m
echo   [91m║ 🎮 ARMORED GEAR: FLY SLIGHT                                  ║[0m
echo   [91m║    Xbox Series X/S Controller Launch                         ║[0m
echo   [91m╚═══════════════════════════════════════════════════════════════╝[0m
echo.
echo ======================================================================
echo.

REM Check ROM
if not exist "%ROM_PATH%" (
    echo [91m❌ ROM not found: %ROM_PATH%[0m
    echo.
    echo Build the game first:
    echo   cd %cd%
    echo   .\build.ps1
    echo.
    exit /b 1
)

for /f %%A in ('powershell -Command "& {Write-Host ([math]::Round((Get-Item '%ROM_PATH%').Length / 1KB, 1))}"') do (
    set ROM_SIZE=%%A
)

echo [92m✅ ROM found: %ROM_PATH% (!ROM_SIZE! KB)[0m
echo.

set ARMORED_GEAR_ROM_PATH=%ROM_PATH%

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo [91m❌ Python not found[0m
        echo.
        echo Install Python 3.9+ from: https://www.python.org/
        echo Ensure "Add Python to PATH" is checked during installation.
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON=py
    )
) else (
    set PYTHON=python
)

echo [92m✅ Python found[0m
echo.

REM Check pygame
%PYTHON% -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [93m⚠️  pygame not installed, installing...[0m
    %PYTHON% -m pip install pygame -q
    if errorlevel 1 (
        echo [91m❌ Failed to install pygame[0m
        pause
        exit /b 1
    )
    echo [92m✅ pygame installed successfully[0m
    echo.
) else (
    echo [92m✅ pygame installed[0m
    echo.
)

REM Check mGBA
set MGBA_FOUND=0
for %%P in (
    "C:\Program Files\mGBA\mgba.exe"
    "C:\Program Files (x86)\mGBA\mgba.exe"
    "C:\Games\mGBA\mgba.exe"
) do (
    if exist %%P (
        echo [92m✅ mGBA found: %%P[0m
        set MGBA_FOUND=1
    )
)

if !MGBA_FOUND! equ 0 (
    where mgba >nul 2>&1
    if errorlevel 1 (
        echo [93m⚠️  mGBA not found[0m
        echo    Install from: https://mgba.io/downloads.html
        echo.
    ) else (
        echo [92m✅ mGBA found in PATH[0m
        echo.
    )
) else (
    echo.
)

REM Check for controller
echo [96m🕹️  Checking for Xbox Series Controller...[0m
echo    Please connect your Xbox Series X/S controller now.
echo    (The game launcher will detect it automatically.)
echo.
echo [96m🚀 Launching game...[0m
echo.

REM Launch Python launcher
%PYTHON% "%PY_LAUNCHER%"

if errorlevel 1 (
    echo.
    echo [91m❌ Game launcher exited with error[0m
    pause
    exit /b 1
)

exit /b 0
