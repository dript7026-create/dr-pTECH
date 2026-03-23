param(
    [switch]$Aggressive,
    [switch]$OpenTools,
    [switch]$SkipRebootPrompt
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Write-Section {
    param([string]$Title)
    Write-Host "`n=== $Title ===" -ForegroundColor Cyan
}

function Get-DisplayState {
    $gpu = Get-PnpDevice | Where-Object {
        $_.Class -eq 'Display' -and ($_.FriendlyName -match 'AMD Radeon' -or $_.InstanceId -match '^PCI\\VEN_1002')
    } | Select-Object -First 1

    $monitors = Get-PnpDevice | Where-Object { $_.Class -eq 'Monitor' } | Sort-Object FriendlyName
    $audio = Get-PnpDevice | Where-Object {
        $_.Class -in @('MEDIA', 'AudioEndpoint') -and $_.FriendlyName -match 'AMD|HDMI|Display|Monitor'
    } | Sort-Object FriendlyName
    $usbDisplay = Get-PnpDevice | Where-Object {
        $_.Present -and ($_.FriendlyName -match 'DisplayLink|Dock|USB Display|HDMI|USB-C' -or $_.InstanceId -match '^USB')
    } | Sort-Object Class, FriendlyName

    [pscustomobject]@{
        Gpu = $gpu
        Monitors = $monitors
        Audio = $audio
        UsbDisplay = $usbDisplay
    }
}

function Show-DisplayState {
    param([string]$Label)

    $state = Get-DisplayState
    Write-Section $Label

    if ($null -ne $state.Gpu) {
        $state.Gpu | Select-Object Status, Class, FriendlyName, InstanceId, Problem, ConfigManagerErrorCode |
            Format-List | Out-String -Width 240 | Write-Host
    } else {
        Write-Host 'No display adapter was returned by Get-PnpDevice.' -ForegroundColor Yellow
    }

    Write-Host 'Monitors:' -ForegroundColor DarkCyan
    ($state.Monitors | Select-Object Status, FriendlyName, InstanceId | Format-Table -AutoSize | Out-String -Width 240) | Write-Host

    Write-Host 'AMD / HDMI audio path:' -ForegroundColor DarkCyan
    ($state.Audio | Select-Object Status, Class, FriendlyName, InstanceId | Format-Table -AutoSize | Out-String -Width 240) | Write-Host

    Write-Host 'USB / dock style display-related devices:' -ForegroundColor DarkCyan
    ($state.UsbDisplay | Select-Object Status, Class, FriendlyName, InstanceId | Format-Table -AutoSize | Out-String -Width 240) | Write-Host

    return $state
}

function Invoke-HardwareRescan {
    Write-Section 'Hardware Rescan'
    & pnputil /scan-devices | Out-Host
    Start-Sleep -Seconds 3
}

function Restart-DisplayDevice {
    param([Parameter(Mandatory = $true)][string]$InstanceId)

    Write-Section 'Restarting Display Adapter'
    Disable-PnpDevice -InstanceId $InstanceId -Confirm:$false | Out-Host
    Start-Sleep -Seconds 2
    Enable-PnpDevice -InstanceId $InstanceId -Confirm:$false | Out-Host
    Start-Sleep -Seconds 4
}

function Invoke-AggressiveRepair {
    param([Parameter(Mandatory = $true)][string]$InstanceId)

    Write-Section 'Aggressive Display Re-enumeration'
    Write-Host 'Removing the current display device instance and forcing rediscovery. The driver package is not deleted.' -ForegroundColor Yellow
    & pnputil /remove-device "$InstanceId" | Out-Host
    Start-Sleep -Seconds 2
    Invoke-HardwareRescan
}

function Export-Diagnostics {
    param([Parameter(Mandatory = $true)][string]$LogPath)

    Write-Section 'Exporting Diagnostics'
    $display = Get-PnpDevice | Where-Object { $_.Class -in @('Display', 'Monitor', 'MEDIA', 'AudioEndpoint', 'USB') }
    $video = Get-CimInstance Win32_VideoController
    $signedDrivers = Get-CimInstance Win32_PnPSignedDriver | Where-Object { $_.DeviceClass -eq 'DISPLAY' -or $_.DeviceName -match 'AMD Radeon' }

    @(
        'HDMI / Display Adapter Repair Diagnostic'
        "Timestamp: $(Get-Date -Format s)"
        ''
        '=== Win32_VideoController ==='
        ($video | Select-Object Name, PNPDeviceID, DriverVersion, Status, VideoProcessor | Format-List | Out-String -Width 240)
        '=== Display Driver Bindings ==='
        ($signedDrivers | Select-Object DeviceName, DeviceID, DriverProviderName, DriverVersion, InfName, DriverDate, Manufacturer | Format-List | Out-String -Width 240)
        '=== PnP Display / Monitor / Media / AudioEndpoint / USB ==='
        ($display | Select-Object Status, Class, FriendlyName, InstanceId, Problem, ConfigManagerErrorCode | Format-Table -AutoSize | Out-String -Width 240)
    ) | Set-Content -Path $LogPath -Encoding UTF8

    Write-Host "Diagnostics written to $LogPath" -ForegroundColor Green
}

function Open-TroubleshootingTools {
    Write-Section 'Opening Troubleshooting Tools'
    Start-Process 'devmgmt.msc'
    Start-Process 'ms-settings:display'
    Start-Process 'ms-settings:windowsupdate'
}

$scriptRoot = Split-Path -Parent $PSCommandPath
$logPath = Join-Path $scriptRoot 'restore_hdmi_adapter.log'

if (-not (Test-IsAdmin)) {
    Write-Host 'This repair requires Administrator rights. Relaunching elevated...' -ForegroundColor Yellow
    $argList = @('-ExecutionPolicy', 'Bypass', '-File', ('"' + $PSCommandPath + '"'))
    if ($Aggressive) { $argList += '-Aggressive' }
    if ($OpenTools) { $argList += '-OpenTools' }
    if ($SkipRebootPrompt) { $argList += '-SkipRebootPrompt' }
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $argList
    exit 0
}

Write-Section 'System Context'
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, SystemType | Format-List | Out-String -Width 220 | Write-Host
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsBuildNumber | Format-List | Out-String -Width 220 | Write-Host

Export-Diagnostics -LogPath $logPath
$before = Show-DisplayState -Label 'Display State Before Repair'

if ($OpenTools) {
    Open-TroubleshootingTools
}

$gpu = $before.Gpu
if ($null -eq $gpu) {
    throw 'No AMD display adapter was found. Open Device Manager and use Action > Scan for hardware changes. If it still does not appear, reinstall the Acer graphics driver package manually.'
}

Invoke-HardwareRescan

if ($gpu.Status -ne 'OK') {
    Restart-DisplayDevice -InstanceId $gpu.InstanceId
}

$after = Show-DisplayState -Label 'Display State After Safe Repair'

if ($null -ne $after.Gpu -and $after.Gpu.Status -eq 'OK') {
    Write-Host 'The AMD display adapter is healthy again. Reconnect the HDMI adapter or cable and check Display Settings.' -ForegroundColor Green
    exit 0
}

if ($Aggressive -and $null -ne $after.Gpu) {
    Invoke-AggressiveRepair -InstanceId $after.Gpu.InstanceId
    $final = Show-DisplayState -Label 'Display State After Aggressive Repair'
    if ($null -ne $final.Gpu -and $final.Gpu.Status -eq 'OK') {
        Write-Host 'The aggressive re-enumeration restored the display adapter.' -ForegroundColor Green
        exit 0
    }
}

Write-Host 'The adapter is still not healthy.' -ForegroundColor Yellow
Write-Host 'Next actions:' -ForegroundColor Yellow
Write-Host '1. Reboot the laptop fully, then rerun this script as Administrator.'
Write-Host '2. In Device Manager, uninstall only AMD Radeon(TM) Graphics and scan for hardware changes.'
Write-Host '3. Reinstall the Acer Aspire A315-24PT graphics/chipset package, then reconnect the HDMI adapter.'

if (-not $SkipRebootPrompt) {
    $restart = Read-Host 'Type REBOOT to restart now, or press Enter to skip'
    if ($restart -eq 'REBOOT') {
        Restart-Computer -Force
    }
}