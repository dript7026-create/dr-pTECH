<# PowerShell helper: Send-Notification.ps1
   - Usage: .\ps_notify.ps1 -Title 'T' -Message 'M'
   - Tries BurntToast (Toast notifications) if available, otherwise falls back to a MessageBox.
   - SECURITY: does not download remote modules. If you want BurntToast, install it explicitly:
       Install-Module -Name BurntToast -Scope CurrentUser
#>
param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)][string]$Message,
    [switch]$AllowUnsafe
)

Set-StrictMode -Version Latest

# Enforce that the script is signed with a valid Authenticode signature.
try {
    $sig = Get-AuthenticodeSignature $MyInvocation.MyCommand.Path
} catch {
    Write-Error "Failed to read script signature: $($_.Exception.Message)"
    exit 2
}
if (-not $AllowUnsafe -and $sig.Status -ne 'Valid') {
    Write-Error "Script signature is not valid. Please sign this script with a trusted certificate before running."
    exit 2
}

try {
    if (Get-Module -ListAvailable -Name BurntToast) {
        Import-Module BurntToast -ErrorAction Stop
        New-BurntToastNotification -Text $Title, $Message
    }
    else {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($Message, $Title) | Out-Null
    }
}
catch {
    Write-Error "Notification failed: $($_.Exception.Message)"
    exit 1
}
exit 0

# SIG # Begin signature block
 
