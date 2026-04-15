param(
    [string]$LaunchKey,
    [string]$SignatureOutputPath = ".tmp\workspace_push_signature.json",
    [string]$PublicationReportPath = ".tmp\publication_scope_review.json",
    [switch]$SkipLocalHookInstall,
    [switch]$SkipWorkspaceHealth,
    [switch]$StagePublishableSet
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $PSCommandPath
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot "..")).Path

function Invoke-WorkspaceHealth {
    param([string]$RepoRoot)

    $workspaceHealth = Join-Path $RepoRoot "tools\workspace_health.py"
    if (-not (Test-Path -LiteralPath $workspaceHealth)) {
        Write-Host "Workspace health script not found; skipping." -ForegroundColor Yellow
        return
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        & $pythonCommand.Source $workspaceHealth --skip-pip-check
        return
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        & $pyCommand.Source -3 $workspaceHealth --skip-pip-check
        return
    }

    Write-Host "Python launcher not found; skipping workspace health." -ForegroundColor Yellow
}

Set-Location $repoRoot

if (-not $LaunchKey) {
    $LaunchKey = Read-Host "Type DRIPTECH-LAUNCH to authorize full-workspace push preparation"
}

if ($LaunchKey -cne "DRIPTECH-LAUNCH") {
    throw "Launch key acknowledgement did not match DRIPTECH-LAUNCH. Push preparation aborted."
}

& (Join-Path $scriptRoot "pre_push_security_check.ps1") -AllFiles

& (Join-Path $scriptRoot "publication_scope_pass.ps1") -OutputPath $PublicationReportPath -StagePublishableSet:$StagePublishableSet

if (-not $SkipWorkspaceHealth) {
    Invoke-WorkspaceHealth -RepoRoot $repoRoot
}

if (-not $SkipLocalHookInstall) {
    & (Join-Path $scriptRoot "install_local_pre_push_hook.ps1") -Quiet
}

& (Join-Path $scriptRoot "write_workspace_signature.ps1") -OutputPath $SignatureOutputPath

Write-Host "Workspace push preparation complete." -ForegroundColor Green
Write-Host "Publication scope report: $PublicationReportPath" -ForegroundColor Cyan
Write-Host "Review WORKSPACE_PUSH_PROTOCOL.md and the generated signature before the final manual push." -ForegroundColor Cyan
