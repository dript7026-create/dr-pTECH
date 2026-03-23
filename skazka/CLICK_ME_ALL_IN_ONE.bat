@echo off
setlocal
title SKAZKA All-in-One Setup

set "ROOT=c:\Users\rrcar\Documents\drIpTECH\skazka"
cd /d "%ROOT%" || (
  echo [ERROR] Folder not found: %ROOT%
  pause
  exit /b 1
)

echo [1/8] Ensuring folders...
if not exist "scripts" mkdir "scripts"
if not exist "notebooks" mkdir "notebooks"

echo [2/8] Writing requirements-dev.txt...
> "requirements-dev.txt" (
  echo jupyter
  echo ipykernel
  echo notebook
  echo numpy
  echo pandas
  echo matplotlib
)

echo [3/8] Writing SKAZKA_GDD.txt...
> "SKAZKA_GDD.txt" (
  echo SKAZKA - GAME DESIGN DOCUMENT ^(GDD^)
  echo Version: 1.0
  echo Date: 2026-03-08
  echo.
  echo - Startup: drIpTech -^> Do9Graphics -^> DripSkullTechnologies -^> SKAZKA title -^> skippable cinematic
  echo - Main Menu: New Game / Continue / Settings / Exit
  echo - Settings: Master, Music, SFX knobs + Performance/Quality toggle
  echo - New Game overwrite prompt when save exists
  echo - Core content: 123 minions, 14 overworld bosses, 8 plot bosses, 436 puzzles
  echo - Companion: demon-cherub fairy morality system
  echo - Platform: Windows + Xbox Series Controller support ^(XInput^)
  echo.
  echo END OF DOCUMENT
)

echo [4/8] Writing ASSET_TRACKER.csv...
> "ASSET_TRACKER.csv" (
  echo AssetID,Category,AssetName,QuantityRequired,Priority,Owner,Status,TargetMilestone
  echo SKZ-BRAND-001,Branding,drIpTech Splash,1,P0,Art,TODO,M1
  echo SKZ-BRAND-002,Branding,Do9Graphics Splash,1,P0,Art,TODO,M1
  echo SKZ-BRAND-003,Branding,DripSkullTechnologies Splash,1,P0,Art,TODO,M1
  echo SKZ-UI-001,UI,Main Menu Kit,1,P0,UI,TODO,M1
  echo SKZ-PLY-001,Player,Warrior Set,1,P0,CharacterArt,TODO,M2
  echo SKZ-ENM-001,Enemies,Minion Sets T1-T3,18,P0,CharacterArt,TODO,M2
  echo SKZ-BOSS-OW-001,Bosses,Overworld Boss Sets,14,P0,CharacterArt,TODO,M3
  echo SKZ-BOSS-PL-001,Bosses,Plot Boss Sets,8,P0,CharacterArt,TODO,M4
  echo SKZ-COMP-001,Companion,Demon-Cherub Fairy Set,1,P0,CharacterArt,TODO,M3
  echo SKZ-AUD-001,Audio,Core Music+SFX Pack,1,P0,Audio,TODO,M2
)

echo [5/8] Creating .venv and installing tools...

set "PYCMD="
where py >nul 2>nul && set "PYCMD=py -3"
if not defined PYCMD where python >nul 2>nul && set "PYCMD=python"
if not defined PYCMD where python3 >nul 2>nul && set "PYCMD=python3"

if not defined PYCMD (
  echo [WARN] Python launcher not found. Skipping venv/notebook setup.
  goto :open_files
)

if not exist ".venv\Scripts\python.exe" (
  %PYCMD% -m venv .venv
)

if not exist ".venv\Scripts\python.exe" (
  echo [WARN] venv creation failed. Skipping Python steps.
  goto :open_files
)

set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r requirements-dev.txt
"%PY%" -m ipykernel install --user --name skazka-dev --display-name "Python (skazka-dev)"

echo [6/8] Creating notebook...
if not exist "notebooks\dev_session.ipynb" (
  "%PY%" -c "import json,pathlib;p=pathlib.Path(r'notebooks/dev_session.ipynb');p.parent.mkdir(parents=True,exist_ok=True);nb={'cells':[{'cell_type':'markdown','metadata':{},'source':['# SKAZKA Dev Session']}],'metadata':{'kernelspec':{'display_name':'Python (skazka-dev)','language':'python','name':'skazka-dev'},'language_info':{'name':'python'}},'nbformat':4,'nbformat_minor':5};p.write_text(json.dumps(nb,indent=2),encoding='utf-8')"
)

echo [7/8] Building skazavR.c (if compiler exists)...
where gcc >nul 2>nul
if %errorlevel%==0 (
  gcc "skazavR.c" -o "skazavR.exe"
) else (
  echo [INFO] gcc not found. Skipping build.
)

:open_files
echo [8/8] Opening files...
start "" notepad "%ROOT%\SKAZKA_GDD.txt"
start "" notepad "%ROOT%\ASSET_TRACKER.csv"
where code >nul 2>nul && start "" code "%ROOT%\notebooks\dev_session.ipynb"
if exist "%ROOT%\skazavR.exe" start "" "%ROOT%\skazavR.exe"

echo.
echo Done.
pause
endlocal