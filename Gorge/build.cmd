@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
pushd "%ROOT%"

if not exist "src\generated" mkdir "src\generated"
if not exist "generated" mkdir "generated"

if exist "..\.venv\Scripts\python.exe" (
  set "PYTHON_EXE=..\.venv\Scripts\python.exe"
) else (
  set "PYTHON_EXE=python"
)

%PYTHON_EXE% tools\generate_gorge_content.py
if errorlevel 1 (
  popd
  exit /b 1
)

powershell -ExecutionPolicy Bypass -File ..\workspace_toolchains.ps1 -Quiet >nul
if errorlevel 1 (
  echo Failed to configure workspace toolchains.
  popd
  exit /b 1
)

powershell -ExecutionPolicy Bypass -File ..\workspace_devkitpro_bash.ps1 -Command "make","-C","Gorge","clean","all"
if errorlevel 1 (
  popd
  exit /b 1
)

echo Built %ROOT%gorge.gba
popd
exit /b 0
