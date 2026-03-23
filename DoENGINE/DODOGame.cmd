@echo off
setlocal
set ROOT=%~dp0
if exist "%ROOT%..\.venv\Scripts\pythonw.exe" (
  start "DODOGame" "%ROOT%..\.venv\Scripts\pythonw.exe" "%ROOT%apps\dodogame.py"
  exit /b 0
)
if exist "%ROOT%..\.venv\Scripts\python.exe" (
  start "DODOGame" "%ROOT%..\.venv\Scripts\python.exe" "%ROOT%apps\dodogame.py"
  exit /b 0
)
start "DODOGame" python "%ROOT%apps\dodogame.py"
