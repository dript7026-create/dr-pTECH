Param(
    [string]$ScriptPath = "readAIpolish\ps_notify.ps1",
    [string]$CertName = "driptech-local-signing",
    [int]$YearsValid = 5
)

$fullScriptPath = Resolve-Path $ScriptPath -ErrorAction Stop
Write-Host "Signing script: $fullScriptPath"

# Create a self-signed certificate in CurrentUser\My
$notAfter = (Get-Date).AddYears($YearsValid)
# Create a Code Signing certificate suitable for Authenticode
$cert = New-SelfSignedCertificate -Subject "CN=$CertName" -CertStoreLocation "Cert:\\CurrentUser\\My" -KeyExportPolicy Exportable -Type CodeSigning -KeyLength 2048 -NotAfter $notAfter
if (-not $cert) { Write-Error "Certificate creation failed."; exit 1 }
Write-Host "Created cert with thumbprint: $($cert.Thumbprint)"

# Export the public cert to a temp file
$cerFile = Join-Path $env:TEMP "${CertName}.cer"
Export-Certificate -Cert $cert -FilePath $cerFile -Force | Out-Null
Write-Host "Exported certificate to $cerFile"

# Import the public cert into CurrentUser\TrustedPublisher so signatures validate for this user
Import-Certificate -FilePath $cerFile -CertStoreLocation "Cert:\CurrentUser\TrustedPublisher" | Out-Null
Write-Host "Imported certificate into CurrentUser\TrustedPublisher"

# Also import into CurrentUser\Root (Trusted Root) so the cert is fully trusted for this user
Import-Certificate -FilePath $cerFile -CertStoreLocation "Cert:\CurrentUser\Root" | Out-Null
Write-Host "Imported certificate into CurrentUser\Root (Trusted Root)"

# Sign the script
$sig = Set-AuthenticodeSignature -FilePath $fullScriptPath -Certificate $cert -HashAlgorithm SHA256
Write-Host "Signature status: $($sig.Status)"
if ($sig.Status -ne 'Valid') {
    Write-Warning "Signature created but status is not 'Valid'. You may need to trust the cert in Trusted Root or Trusted Publishers."
}

# Clean up exported cert file
Remove-Item $cerFile -Force -ErrorAction SilentlyContinue

Write-Host "Done."
