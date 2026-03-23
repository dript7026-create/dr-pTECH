Param(
    [switch]$Persist
)

Write-Host "This script will prompt for your OpenAI API key (input hidden)."
$keySecure = Read-Host -AsSecureString "Enter OpenAI API key"
# Convert SecureString to plain text only in memory
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($keySecure)
$keyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) | Out-Null

# Set for current session
Set-Item -Path Env:OPENAI_API_KEY -Value $keyPlain
Write-Host "OPENAI_API_KEY set for this PowerShell session."

if ($Persist) {
    setx OPENAI_API_KEY "$keyPlain" | Out-Null
    Write-Host "OPENAI_API_KEY persisted to user environment (setx). Restart terminals to pick it up."
}

# Clear plain-text variable from memory
$keyPlain = $null

Write-Host "Done."