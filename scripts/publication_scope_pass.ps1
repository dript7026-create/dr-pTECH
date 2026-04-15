param(
    [string]$OutputPath = ".tmp\publication_scope_review.json",
    [switch]$StagePublishableSet,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot
if (-not $scriptRoot) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot "..")).Path
Set-Location $repoRoot

$publishNowPaths = @(
    ".github/workflows/workspace-health.yml",
    ".gitignore",
    "PUBLIC_REPO_SCOPE.md",
    "README_CHAT_INTEGRATION.md",
    "SECURITY.md",
    "WORKSPACE_PUSH_PROTOCOL.md",
    "scripts/install_local_pre_push_hook.ps1",
    "scripts/pre_push_security_check.ps1",
    "scripts/prepare_workspace_push.ps1",
    "scripts/publication_scope_pass.ps1",
    "scripts/write_workspace_signature.ps1"
)

$excludePatterns = @(
    '(?i)(^|[\\/])AssetGenerator[\\/]migrated_d_drive([\\/]|$)',
    '(?i)(^|[\\/])assets archive([\\/]|$)',
    '(?i)(^|[\\/])deliverables([\\/]|$)',
    '(?i)(^|[\\/])backup_secondary([\\/]|$)',
    '(?i)\.(blend|blend1|sav)$',
    '(?i)_validation\.(out|err)$'
)

function Get-ChangedEntries {
    $statusLines = git -C $repoRoot -c core.quotepath=false status --porcelain=v1
    foreach ($line in $statusLines) {
        if ($line.Length -lt 4) {
            continue
        }

        $statusCode = $line.Substring(0, 2).Trim()
        $path = $line.Substring(3)
        if ($path.Contains(' -> ')) {
            $path = $path.Split(' -> ')[-1]
        }
        if ($path.StartsWith('"') -and $path.EndsWith('"')) {
            $path = $path.Trim('"')
        }

        [PSCustomObject]@{
            status = $statusCode
            path = $path
        }
    }
}

function Test-ExcludedPath {
    param([string]$Path)

    foreach ($pattern in $excludePatterns) {
        if ($Path -match $pattern) {
            return $true
        }
    }

    return $false
}

$publishNow = [System.Collections.Generic.List[object]]::new()
$reviewRequired = [System.Collections.Generic.List[object]]::new()
$excluded = [System.Collections.Generic.List[object]]::new()

foreach ($entry in Get-ChangedEntries) {
    $path = $entry.path
    $status = $entry.status

    if (Test-ExcludedPath -Path $path) {
        $excluded.Add([PSCustomObject]@{
                path = $path
                status = $status
                reason = "archive, deliverable, backup, or local runtime artifact"
            })
        continue
    }

    if ($status -match 'D') {
        $reviewRequired.Add([PSCustomObject]@{
                path = $path
                status = $status
                reason = "tracked deletion requires explicit publication review"
            })
        continue
    }

    if ($publishNowPaths -contains $path) {
        $publishNow.Add([PSCustomObject]@{
                path = $path
                status = $status
                reason = "governance or push-prep boundary file"
            })
        continue
    }

    $reviewRequired.Add([PSCustomObject]@{
            path = $path
            status = $status
            reason = "project change not auto-promoted into the publish-now set"
        })
}

$report = [ordered]@{
    schema_version = 1
    repository = "drIpTECH"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    publish_now = $publishNow
    review_required = $reviewRequired
    exclude_from_push_now = $excluded
    summary = [ordered]@{
        publish_now_count = $publishNow.Count
        review_required_count = $reviewRequired.Count
        exclude_from_push_now_count = $excluded.Count
    }
}

$resolvedOutputPath = Join-Path $repoRoot $OutputPath
$outputDirectory = Split-Path -Parent $resolvedOutputPath
if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resolvedOutputPath -Encoding ASCII

if ($StagePublishableSet -and $publishNow.Count -gt 0) {
    $pathsToStage = $publishNow | ForEach-Object { $_.path }
    git -C $repoRoot add -- $pathsToStage
}

if (-not $Quiet) {
    Write-Host "Publication scope pass complete." -ForegroundColor Green
    Write-Host "Publish now: $($publishNow.Count)" -ForegroundColor Cyan
    Write-Host "Review required: $($reviewRequired.Count)" -ForegroundColor Yellow
    Write-Host "Exclude from push now: $($excluded.Count)" -ForegroundColor Yellow
    Write-Host "Report written to $resolvedOutputPath" -ForegroundColor Cyan
    if ($StagePublishableSet) {
        Write-Host "Explicit publish-now subset staged." -ForegroundColor Cyan
    }
}