param(
    [int]$MaxSensitiveAgeSeconds = 90,
    [int]$MaxPasteEvents = 3,
    [int]$PollIntervalMilliseconds = 750,
    [int]$RemoteCheckEveryLoops = 6,
    [int]$RunForSeconds = 0,
    [switch]$NoInitialClear,
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

$script:GuardRoot = Split-Path -Parent $PSCommandPath
$script:StatusPath = Join-Path $script:GuardRoot 'clipboard_guard.status.json'
$script:LogPath = Join-Path $script:GuardRoot 'clipboard_guard.log'
$script:PidPath = Join-Path $script:GuardRoot 'clipboard_guard.pid'

Add-Type -AssemblyName System.Security
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class ClipboardGuardNative {
    [DllImport("user32.dll")]
    public static extern short GetAsyncKeyState(int vKey);

    [DllImport("user32.dll")]
    public static extern uint GetClipboardSequenceNumber();

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int maxCount);
}
"@

function Write-GuardLog {
    param(
        [string]$Message,
        [string]$Level = 'INFO'
    )

    $line = '{0} [{1}] {2}' -f (Get-Date).ToString('s'), $Level.ToUpperInvariant(), $Message
    Add-Content -Path $script:LogPath -Value $line
    if (-not $Quiet) {
        Write-Host $line
    }
}

function Get-ClipboardText {
    try {
        $value = Get-Clipboard -Raw -ErrorAction Stop
        if ($null -eq $value) {
            return ''
        }
        return [string]$value
    } catch {
        return ''
    }
}

    function Test-ClipboardHasContent {
        $text = Get-ClipboardText
        return -not [string]::IsNullOrWhiteSpace($text)
    }

function Clear-ClipboardSafe {
    param([string]$Reason = 'manual-clear')

    try {
        Set-Clipboard -Value ''
    } catch {
        try {
            [System.Windows.Forms.Clipboard]::Clear()
        } catch {
        }
    }

    Write-GuardLog -Message ("Clipboard cleared ({0})." -f $Reason)
}

function Get-ClipboardHash {
    param([string]$Text)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return ([Convert]::ToHexString($hash))
}

function Test-SensitiveClipboardText {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $false
    }

    $patterns = @(
        '-----BEGIN [A-Z ]*PRIVATE KEY-----',
        '(?i)\b(?:ghp|gho|ghu|ghs)_[A-Za-z0-9_]{20,}\b',
        '(?i)\bgithub_pat_[A-Za-z0-9_]{20,}\b',
        '(?i)\bsk-[A-Za-z0-9]{20,}\b',
        '\bAKIA[0-9A-Z]{16}\b',
        '\bASIA[0-9A-Z]{16}\b',
        '(?i)\bxox[baprs]-[A-Za-z0-9-]{10,}\b',
        '\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b',
        '(?im)^\s*(?:password|secret|token|api[_ -]?key|connectionstring|client[_ -]?secret)\s*[:=]\s*\S+',
        '(?i)\b(?:ssh-rsa|ssh-ed25519)\s+[A-Za-z0-9+/=]{40,}',
        '(?i)(?:authorization:\s*bearer\s+\S+)',
        '(?i)(?:openai|github|slack|aws).{0,20}(?:token|secret|key)',
        '(?i)-----BEGIN PGP PRIVATE KEY BLOCK-----'
    )

    foreach ($pattern in $patterns) {
        if ($Text -match $pattern) {
            return $true
        }
    }

    if ($Text.Length -ge 24 -and $Text -match '(?i)\b(?:password|passphrase|recovery code|seed phrase|mnemonic|private key|secret|token|api[_ -]?key)\b') {
        return $true
    }

    return $false
}

function Get-ForegroundWindowTitle {
    $builder = New-Object System.Text.StringBuilder 512
    $handle = [ClipboardGuardNative]::GetForegroundWindow()
    if ($handle -eq [IntPtr]::Zero) {
        return ''
    }
    [void][ClipboardGuardNative]::GetWindowText($handle, $builder, $builder.Capacity)
    return $builder.ToString()
}

function Test-KeyDown {
    param([int]$VirtualKey)
    return (([ClipboardGuardNative]::GetAsyncKeyState($VirtualKey) -band 0x8000) -ne 0)
}

function Test-PasteChordDown {
    $ctrlV = (Test-KeyDown -VirtualKey 0x11) -and (Test-KeyDown -VirtualKey 0x56)
    $shiftInsert = (Test-KeyDown -VirtualKey 0x10) -and (Test-KeyDown -VirtualKey 0x2D)
    return ($ctrlV -or $shiftInsert)
}

function Get-RemoteAccessIndicator {
    if ($env:SESSIONNAME -like 'RDP-*' -or $env:SESSIONNAME -like 'ICA-*') {
        return 'interactive session is remote'
    }

    try {
        $remoteNames = @(
            'AnyDesk',
            'TeamViewer',
            'TeamViewer_Service',
            'RustDesk',
            'rustdesk',
            'ScreenConnect.ClientService',
            'ScreenConnect.WindowsClient',
            'ScreenConnect.Service',
            'Parsec',
            'parsecd',
            'AeroAdmin',
            'Ammyy',
            'UltraViewer',
            'rutserv',
            'rutview',
            'winvnc',
            'tvnserver',
            'vncviewer',
            'msra',
            'QuickAssist',
            'Bomgar',
            'LogMeIn',
            'GoToAssist'
        )

        $process = Get-Process -ErrorAction SilentlyContinue | Where-Object { $remoteNames -contains $_.Name } | Select-Object -First 1
        if ($null -ne $process) {
            return ("remote-access process running: {0}" -f $process.Name)
        }
    } catch {
    }

    try {
        $quserOutput = (& quser 2>$null | Out-String)
        if ($quserOutput -match 'rdp-tcp') {
            return 'RDP session detected in session table'
        }
    } catch {
    }

    return $null
}

function Update-GuardStatus {
    param(
        [hashtable]$Tracked,
        [string]$LastAction,
        [string]$RemoteIndicator
    )

    $payload = [ordered]@{
        updatedAt = (Get-Date).ToString('o')
        processId = $PID
        maxSensitiveAgeSeconds = $MaxSensitiveAgeSeconds
        maxPasteEvents = $MaxPasteEvents
        clipboardSequence = [ClipboardGuardNative]::GetClipboardSequenceNumber()
        activeSensitiveTracking = ($null -ne $Tracked)
        trackedHash = if ($Tracked) { $Tracked.Hash } else { $null }
        trackedSince = if ($Tracked) { $Tracked.FirstSeen.ToString('o') } else { $null }
        pasteCount = if ($Tracked) { $Tracked.PasteCount } else { 0 }
        lastAction = $LastAction
        remoteAccessIndicator = $RemoteIndicator
        foregroundWindow = Get-ForegroundWindowTitle
    }

    $payload | ConvertTo-Json -Depth 4 | Set-Content -Path $script:StatusPath
}

function Remove-StalePidFile {
    if (-not (Test-Path $script:PidPath)) {
        return
    }

    try {
        $existingPid = [int](Get-Content -Path $script:PidPath -ErrorAction Stop | Select-Object -First 1)
        $existing = Get-CimInstance Win32_Process -Filter "ProcessId = $existingPid" -ErrorAction SilentlyContinue
        if ($null -eq $existing -or $existing.CommandLine -notmatch 'clipboard_guard\.ps1') {
            Remove-Item -Path $script:PidPath -Force -ErrorAction SilentlyContinue
        }
    } catch {
        Remove-Item -Path $script:PidPath -Force -ErrorAction SilentlyContinue
    }
}

function Assert-SingleInstance {
    Remove-StalePidFile
    if (Test-Path $script:PidPath) {
        $existingPid = Get-Content -Path $script:PidPath | Select-Object -First 1
        Write-GuardLog -Level 'WARN' -Message ("Clipboard guard already running with PID {0}." -f $existingPid)
        exit 0
    }
    Set-Content -Path $script:PidPath -Value $PID
}

Assert-SingleInstance

$tracked = $null
$lastAction = 'started'
$lastPasteChordDown = $false
$loopCount = 0
$startedAt = Get-Date
$sequence = [ClipboardGuardNative]::GetClipboardSequenceNumber()

try {
    if (-not $NoInitialClear) {
        Clear-ClipboardSafe -Reason 'startup'
        $sequence = [ClipboardGuardNative]::GetClipboardSequenceNumber()
        $lastAction = 'startup-clear'
    }

    Write-GuardLog -Message ("Clipboard guard started. age={0}s pasteLimit={1}" -f $MaxSensitiveAgeSeconds, $MaxPasteEvents)

    while ($true) {
        Start-Sleep -Milliseconds $PollIntervalMilliseconds
        $loopCount++

        $remoteIndicator = $null
        if (($loopCount % [Math]::Max($RemoteCheckEveryLoops, 1)) -eq 0) {
            $remoteIndicator = Get-RemoteAccessIndicator
            if ($remoteIndicator -and (Test-ClipboardHasContent)) {
                Clear-ClipboardSafe -Reason 'remote-access-indicator'
                Write-GuardLog -Level 'WARN' -Message ("Remote-access activity detected: {0}" -f $remoteIndicator)
                $tracked = $null
                $sequence = [ClipboardGuardNative]::GetClipboardSequenceNumber()
                $lastAction = 'culled-after-remote-access-detection'
            }
        }

        $currentSequence = [ClipboardGuardNative]::GetClipboardSequenceNumber()
        if ($currentSequence -ne $sequence) {
            $sequence = $currentSequence
            $text = Get-ClipboardText
            if (Test-SensitiveClipboardText -Text $text) {
                $tracked = @{
                    Hash = Get-ClipboardHash -Text $text
                    FirstSeen = Get-Date
                    PasteCount = 0
                    Preview = if ($text.Length -gt 12) { $text.Substring(0, 12) + '...' } else { $text }
                }
                $lastAction = 'tracking-sensitive-clipboard'
                Write-GuardLog -Message 'Sensitive clipboard content detected and tracking started.'
            } else {
                if ($null -ne $tracked) {
                    Write-GuardLog -Message 'Clipboard content changed to non-sensitive content; tracking cleared.'
                }
                $tracked = $null
                $lastAction = 'clipboard-changed'
            }
        }

        if ($null -ne $tracked) {
            $currentText = Get-ClipboardText
            $currentHash = if ([string]::IsNullOrEmpty($currentText)) { '' } else { Get-ClipboardHash -Text $currentText }
            if ($currentHash -ne $tracked.Hash) {
                $tracked = $null
                $lastAction = 'tracked-content-replaced'
            } else {
                $pasteChordDown = Test-PasteChordDown
                if ($pasteChordDown -and -not $lastPasteChordDown) {
                    $tracked.PasteCount++
                    $lastAction = 'paste-detected'
                    Write-GuardLog -Message ("Sensitive clipboard paste detected in '{0}'. Count={1}" -f (Get-ForegroundWindowTitle), $tracked.PasteCount)
                }
                $lastPasteChordDown = $pasteChordDown

                $age = ((Get-Date) - $tracked.FirstSeen).TotalSeconds
                if ($tracked.PasteCount -ge $MaxPasteEvents) {
                    Clear-ClipboardSafe -Reason 'paste-threshold'
                    $tracked = $null
                    $lastAction = 'culled-after-paste-threshold'
                } elseif ($age -ge $MaxSensitiveAgeSeconds) {
                    Clear-ClipboardSafe -Reason 'age-threshold'
                    $tracked = $null
                    $lastAction = 'culled-after-age-threshold'
                } elseif ($remoteIndicator) {
                    Clear-ClipboardSafe -Reason 'remote-access-indicator'
                    Write-GuardLog -Level 'WARN' -Message ("Remote-access activity detected: {0}" -f $remoteIndicator)
                    $tracked = $null
                    $sequence = [ClipboardGuardNative]::GetClipboardSequenceNumber()
                    $lastAction = 'culled-after-remote-access-detection'
                }
            }
        } else {
            $lastPasteChordDown = Test-PasteChordDown
        }

        Update-GuardStatus -Tracked $tracked -LastAction $lastAction -RemoteIndicator $remoteIndicator

        if ($RunForSeconds -gt 0 -and ((Get-Date) - $startedAt).TotalSeconds -ge $RunForSeconds) {
            Write-GuardLog -Message 'Clipboard guard finished requested timed run.'
            break
        }
    }
} finally {
    Remove-Item -Path $script:PidPath -Force -ErrorAction SilentlyContinue
}