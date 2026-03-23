@echo off
REM Build script for blenderTxTUR.dll using MSVC vcvarsall
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
cl /LD /O2 /MD "C:\Users\rrcar\Documents\drIpTECH\drIpTECHBlenderPlug-Ins\TxTUR\blenderTxTUR.c" /Fe:"C:\Users\rrcar\Documents\drIpTECH\drIpTECHBlenderPlug-Ins\TxTUR\blenderTxTUR.dll"
if %ERRORLEVEL% neq 0 pause
