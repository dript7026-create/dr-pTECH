$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$apkPath = Join-Path $packageRoot 'artifacts\dirkodds_mobile_release.apk'
$adbPath = 'C:\Users\rrcar\Documents\drIpTECH\.android-bootstrap\android-sdk\platform-tools\adb.exe'

if (-not (Test-Path $apkPath)) {
    throw "APK not found: $apkPath"
}

if (-not (Test-Path $adbPath)) {
    Write-Host "ADB not found at expected path: $adbPath"
    Write-Host "Install manually from: $apkPath"
    exit 0
}

$devices = & $adbPath devices | Select-String '\tdevice$' | ForEach-Object { ($_ -split '\s+')[0] }
if (-not $devices) {
    Write-Host "No connected Android device found."
    Write-Host "Install manually from: $apkPath"
    exit 0
}

$target = $devices[0]
& $adbPath -s $target install -r $apkPath
Write-Host "Installed to device: $target"
