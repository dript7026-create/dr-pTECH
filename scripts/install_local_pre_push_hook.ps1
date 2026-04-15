param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $PSCommandPath
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot "..")).Path
$hookPath = Join-Path $repoRoot ".git\hooks\pre-push"

$marker = "# drIpTECH pre-push guard"
$hookLines = @(
        '#!/bin/sh',
        $marker,
        'HOOK_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"',
        'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$HOOK_DIR/../../scripts/pre_push_security_check.ps1" -AllFiles',
        'RESULT=$?',
        'if [ $RESULT -ne 0 ]; then',
        '  exit $RESULT',
        'fi',
        'exit 0'
)
$hookBody = $hookLines -join "`n"

if (Test-Path -LiteralPath $hookPath) {
    $existing = Get-Content -LiteralPath $hookPath -Raw
    if ($existing -notmatch [regex]::Escape($marker)) {
        $timestamp = Get-Date -Format "yyyyMMddHHmmss"
        $backupPath = "$hookPath.backup.$timestamp"
        Copy-Item -LiteralPath $hookPath -Destination $backupPath
        if (-not $Quiet) {
            Write-Host "Existing pre-push hook backed up to $backupPath"
        }
    }
}

Set-Content -LiteralPath $hookPath -Value $hookBody -Encoding ASCII
if (-not $Quiet) {
    Write-Host "Installed drIpTECH pre-push hook at $hookPath"
}