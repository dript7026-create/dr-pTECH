$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot
cmake -S . -B build
cmake --build build --config Release
