@echo off
setlocal
set ROOT=%~dp0
if exist "%ROOT%..\.venv\Scripts\pythonw.exe" (
  start "drIpTECH Demo Hub" "%ROOT%..\.venv\Scripts\pythonw.exe" "%ROOT%apps\demo_hub.py"
  exit /b 0
)
if exist "%ROOT%..\.venv\Scripts\python.exe" (
  start "drIpTECH Demo Hub" "%ROOT%..\.venv\Scripts\python.exe" "%ROOT%apps\demo_hub.py"
  exit /b 0
)
start "drIpTECH Demo Hub" python "%ROOT%apps\demo_hub.py"