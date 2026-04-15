@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON_EXE=%ROOT%..\.venv\Scripts\python.exe"
if exist "%PYTHON_EXE%" goto run_script

py -3 -V >nul 2>nul
if errorlevel 1 (
  set "PYTHON_EXE=python"
) else (
  set "PYTHON_EXE=py -3"
)

:run_script
pushd "%ROOT%"
%PYTHON_EXE% "tools\build_kindark_foundation.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
if not errorlevel 1 (
  %PYTHON_EXE% "tools\extend_kindark_project.py"
  set "EXIT_CODE=%ERRORLEVEL%"
)
popd
exit /b %EXIT_CODE%