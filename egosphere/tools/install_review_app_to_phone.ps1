param(
    [string]$WorkspaceRoot = "C:\Users\rrcar\Documents\drIpTECH",
    [string]$ApkPath = "",
    [string]$PairAddress = "",
    [string]$PairCode = "",
    [string]$DeviceAddress = "",
    [switch]$AutoConnectMdns
)

$ErrorActionPreference = "Stop"

$adbPath = Join-Path $WorkspaceRoot ".android-bootstrap\android-sdk\platform-tools\adb.exe"
if (-not (Test-Path $adbPath)) {
    throw "adb not found at $adbPath"
}

if ([string]::IsNullOrWhiteSpace($ApkPath)) {
    $ApkPath = Join-Path $WorkspaceRoot "egosphere\deliverables\external_client_review_latest.apk"
}

if (-not (Test-Path $ApkPath)) {
    throw "APK not found at $ApkPath"
}

function Get-OnlineDevices {
    param([string]$Adb)

    $devicesOutput = & $Adb devices
    return $devicesOutput | Where-Object { $_ -match "\tdevice$" }
}

function Resolve-TargetSerial {
    param(
        [string[]]$DeviceLines,
        [string]$PreferredSerial
    )

    if (-not [string]::IsNullOrWhiteSpace($PreferredSerial)) {
        return $PreferredSerial
    }

    $parsed = @()
    foreach ($line in $DeviceLines) {
        $serial = ($line -split "\s+")[0]
        $parsed += $serial
    }

    $ipSerial = $parsed | Where-Object { $_ -match "^\d+\.\d+\.\d+\.\d+:\d+$" } | Select-Object -First 1
    if ($null -ne $ipSerial) {
        return $ipSerial
    }

    return $parsed | Select-Object -First 1
}

function Get-MdnsConnectAddress {
    param([string]$Adb)

    $services = & $Adb mdns services
    foreach ($line in $services) {
        if ($line -match "(?<name>adb-tls-connect|_adb-tls-connect\._tcp)" -and $line -match "(?<host>\d+\.\d+\.\d+\.\d+):(?<port>\d+)") {
            return "$($matches.host):$($matches.port)"
        }
    }
    return $null
}

if (-not [string]::IsNullOrWhiteSpace($PairAddress) -and -not [string]::IsNullOrWhiteSpace($PairCode)) {
    & $adbPath pair $PairAddress $PairCode
}

if (-not [string]::IsNullOrWhiteSpace($DeviceAddress)) {
    & $adbPath connect $DeviceAddress
} elseif ($AutoConnectMdns) {
    $mdnsAddress = Get-MdnsConnectAddress -Adb $adbPath
    if ($null -ne $mdnsAddress) {
        & $adbPath connect $mdnsAddress
    }
}

$deviceLines = Get-OnlineDevices -Adb $adbPath

if ($deviceLines.Count -eq 0) {
    Write-Host "NO_DEVICE_CONNECTED"
    Write-Host "APK_READY=" $ApkPath
    Write-Host "NEXT_STEP=Connect via USB debugging, or rerun with -PairAddress <ip:port> -PairCode <code> and optionally -AutoConnectMdns or -DeviceAddress <ip:port>."
    exit 1
}

$targetSerial = Resolve-TargetSerial -DeviceLines $deviceLines -PreferredSerial $DeviceAddress

& $adbPath -s $targetSerial install -r $ApkPath
Write-Host "INSTALLED_APK=" $ApkPath
Write-Host "TARGET_SERIAL=" $targetSerial
Write-Host "TARGET_DEVICES=" ($deviceLines -join "; ")