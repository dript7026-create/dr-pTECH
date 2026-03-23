@echo off
setlocal
set SCRIPT_DIR=%~dp0
py -3 "%SCRIPT_DIR%run_illusioncanvas_studio.py" "%SCRIPT_DIR%sample_games\aridfeihth_vertical_slice.iig"
endlocal