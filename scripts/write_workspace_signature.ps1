param(
    [string]$OutputPath = ".tmp\workspace_push_signature.json"
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $PSCommandPath
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot "..")).Path

if ([System.IO.Path]::IsPathRooted($OutputPath)) {
    $resolvedOutput = $OutputPath
} else {
    $resolvedOutput = Join-Path $repoRoot $OutputPath
}

$signatureEntries = @(
    [ordered]@{ path = ".gitignore"; classification = "workspace-boundary" },
    [ordered]@{ path = "PUBLIC_REPO_SCOPE.md"; classification = "publication-scope" },
    [ordered]@{ path = "SECURITY.md"; classification = "security-policy" },
    [ordered]@{ path = "WORKSPACE_PUSH_PROTOCOL.md"; classification = "push-governance" },
    [ordered]@{ path = "scripts\install_local_pre_push_hook.ps1"; classification = "local-hook-installer" },
    [ordered]@{ path = "scripts\prepare_workspace_push.ps1"; classification = "push-prep" },
    [ordered]@{ path = "scripts\pre_push_security_check.ps1"; classification = "security-gate" },
    [ordered]@{ path = "scripts\write_workspace_signature.ps1"; classification = "signature-generator" },
    [ordered]@{ path = "set_openai_key.ps1"; classification = "launch-key-helper" },
    [ordered]@{ path = "set_recraft_key.ps1"; classification = "launch-key-helper" }
)

$filePayload = @()
foreach ($entry in $signatureEntries) {
    $absolutePath = Join-Path $repoRoot $entry.path
    if (-not (Test-Path -LiteralPath $absolutePath)) {
        throw "Signature entry is missing: $($entry.path)"
    }

    $item = Get-Item -LiteralPath $absolutePath
    $hash = (Get-FileHash -LiteralPath $absolutePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $filePayload += [ordered]@{
        path = ($entry.path -replace '\\', '/')
        classification = $entry.classification
        size_bytes = [int64]$item.Length
        sha256 = $hash
    }
}

$aggregateSource = ($filePayload | ForEach-Object { "{0}:{1}" -f $_.path, $_.sha256 }) -join "`n"
$aggregateBytes = [System.Text.Encoding]::UTF8.GetBytes($aggregateSource)
$aggregateHashBytes = [System.Security.Cryptography.SHA256]::Create().ComputeHash($aggregateBytes)
$aggregateHash = [System.BitConverter]::ToString($aggregateHashBytes).Replace("-", "").ToLowerInvariant()

$payload = [ordered]@{
    schema_version = 1
    repository = "drIpTECH"
    generated_utc = (Get-Date).ToUniversalTime().ToString("o")
    signature_scope = "workspace-governance-boundary"
    contact = [ordered]@{
        name = "Ryan Richard Carell"
        email = "rrcarell@gmail.com"
        phone = "(613) 808 - 4968"
    }
    launch_key_protocol = [ordered]@{
        helpers = @(
            "set_openai_key.ps1",
            "set_recraft_key.ps1"
        )
        push_prepare_script = "scripts/prepare_workspace_push.ps1"
        note = "Helpers prompt for keys and set local environment only; live key material must never be stored in the repository."
    }
    files = $filePayload
    aggregate_sha256 = $aggregateHash
}

$outputDirectory = Split-Path -Parent $resolvedOutput
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resolvedOutput -Encoding UTF8
Write-Host "Wrote workspace signature to $resolvedOutput"