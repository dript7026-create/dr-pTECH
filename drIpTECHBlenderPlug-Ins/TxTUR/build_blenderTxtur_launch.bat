@echo off
REM Build script using LaunchDevCmd to initialize environment
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\LaunchDevCmd.bat"
cl /LD /O2 /MD "C:\Users\rrcar\Documents\drIpTECH\drIpTECHBlenderPlug-Ins\TxTUR\blenderTxTUR.c" /Fe:"C:\Users\rrcar\Documents\drIpTECH\drIpTECHBlenderPlug-Ins\TxTUR\blenderTxTUR.dll"
if %ERRORLEVEL% neq 0 pause
