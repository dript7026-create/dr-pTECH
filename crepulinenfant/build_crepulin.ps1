$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

# Build graphical Win32+GDI+ version (C++)
$gpp = (Get-Command g++.exe -ErrorAction Stop).Source
& $gpp -std=c++17 -O2 -Wall -municode `
    ".\Crepulin_Enfant_DetnDimension.cpp" `
    -o ".\Crepulin_Enfant_DetnDimension.exe" `
    -lgdiplus -lgdi32 -luser32 -lshell32 -lole32 -lmsimg32 -mwindows