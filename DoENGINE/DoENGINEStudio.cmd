@echo off
setlocal
set ROOT=%~dp0
if exist "%ROOT%..\.venv\Scripts\pythonw.exe" (
  start "DoENGINE Studio" "%ROOT%..\.venv\Scripts\pythonw.exe" "%ROOT%apps\doengine_studio.py"
  exit /b 0
)
if exist "%ROOT%..\.venv\Scripts\python.exe" (
  start "DoENGINE Studio" "%ROOT%..\.venv\Scripts\python.exe" "%ROOT%apps\doengine_studio.py"
  exit /b 0
)
start "DoENGINE Studio" python "%ROOT%apps\doengine_studio.py"