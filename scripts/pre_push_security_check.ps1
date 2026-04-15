param(
    [switch]$AllFiles
)

$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot
if (-not $scriptRoot) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if (-not $scriptRoot) {
    $scriptRoot = Get-Location
}

$resolvedScriptRoot = (Resolve-Path -LiteralPath $scriptRoot).Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $resolvedScriptRoot "..")).Path
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) {
    Write-Error "Not inside a git repository."
}

Set-Location $repoRoot

$sensitivePathPatterns = @(
    '(?i)(^|[\\/])\.env($|\.)',
    '(?i)(^|[\\/]).*secret.*\.json$',
    '(?i)(^|[\\/]).*credential.*\.json$',
    '(?i)(^|[\\/]).*token.*\.json$',
    '(?i)(^|[\\/]).*service-account.*\.json$',
    '(?i)(^|[\\/])google-credentials\.json$',
    '(?i)(^|[\\/]).*\.(pem|p12|pfx|jks|keystore|key|crt|cer)$'
)

$sensitiveContentPatterns = @(
    '(?i)\bOPENAI_API_KEY\b\s*[=:]\s*(?:["''][^"'']{12,}["'']|sk-[A-Za-z0-9]{20,}|[A-Za-z0-9_-]{32,})',
    '(?i)\bRECRAFT_API_KEY\b\s*[=:]\s*(?:["''][^"'']{12,}["'']|[A-Za-z0-9_-]{32,})',
    '(?i)\bAZURE_OPENAI_API_KEY\b\s*[=:]\s*(?:["''][^"'']{12,}["'']|[A-Za-z0-9_-]{32,})',
    '(?i)\bAWS_SECRET_ACCESS_KEY\b\s*[=:]\s*(?:["''][^"'']{12,}["'']|[A-Za-z0-9_-]{32,})',
    '(?i)\bclient_secret\b\s*[=:]\s*(?:["''][^"'']{12,}["'']|[A-Za-z0-9._-]{20,})',
    '(?i)\bauthorization\b\s*[:=]\s*bearer\s+(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|[A-Za-z0-9._\-]{20,})',
    '(?i)-----BEGIN [A-Z ]*PRIVATE KEY-----',
    '(?i)\bgithub_pat_[A-Za-z0-9_]{20,}\b',
    '(?i)\bgh[pousr]_[A-Za-z0-9_]{20,}\b',
    '(?i)\bsk-[A-Za-z0-9]{20,}\b',
    '(?i)\bapi[_-]?key\b\s*[=:]\s*(?:["''][^"'']{12,}["'']|sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|[A-Za-z0-9_-]{32,})'
)

$allowlistedContentPatterns = @(
    '(?i)OPENAI_API_KEY not set',
    '(?i)RECRAFT_API_KEY not set',
    '(?i)Set the environment variable `OPENAI_API_KEY`',
    '(?i)Set the environment variable `RECRAFT_API_KEY`',
    '(?i)required_env',
    '(?i)api_key_present',
    '(?i)password system',
    '(?i)rcon_password',
    '(?i)client_secret.*placeholder',
    '(?i)authorization\s*[:=]\s*bearer\s+<',
    '(?i)example',
    '(?i)sample',
    '(?i)placeholder',
    '(?i)redacted'
)

$skipDirectories = @(
    '.git\',
    '.venv\',
    '.jdk\',
    '.android-bootstrap\',
    '.tmp\',
    '.tools\',
    '.vscode\',
    '__pycache__\',
    '.pytest_cache\'
)

$allowlistedPathPatterns = @(
    '(?i)(^|[\\/])certifi[\\/]cacert\.pem$'
)

$textExtensions = @(
    '.ps1', '.psm1', '.py', '.pyi', '.c', '.h', '.cpp', '.hpp', '.cs', '.java', '.kt', '.ts', '.tsx', '.js', '.jsx',
    '.json', '.jsonl', '.md', '.txt', '.yml', '.yaml', '.ini', '.cfg', '.conf', '.toml', '.xml', '.html', '.css',
    '.sql', '.sh', '.bat', '.cmd', '.properties', '.gradle', '.kts', '.env', '.gitignore'
)

function Test-SkippedPath {
    param([string]$Path)
    foreach ($prefix in $skipDirectories) {
        if ($Path.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Test-TextFile {
    param([string]$Path)
    $extension = [System.IO.Path]::GetExtension($Path)
    if ($textExtensions -contains $extension.ToLowerInvariant()) {
        return $true
    }
    return $false
}

function Test-AllowlistedLine {
    param([string]$Line)
    foreach ($pattern in $allowlistedContentPatterns) {
        if ($Line -match $pattern) {
            return $true
        }
    }
    return $false
}

function Test-AllowlistedPath {
    param([string]$Path)
    foreach ($pattern in $allowlistedPathPatterns) {
        if ($Path -match $pattern) {
            return $true
        }
    }
    return $false
}

if ($AllFiles) {
    $candidatePaths = git -C $repoRoot -c core.quotepath=false ls-files --cached --others --exclude-standard
} else {
    $statusLines = git -C $repoRoot -c core.quotepath=false status --porcelain
    $candidatePaths = foreach ($line in $statusLines) {
        if ($line.Length -lt 4) { continue }
        $path = $line.Substring(3)
        if ($path.Contains(' -> ')) {
            $path = $path.Split(' -> ')[-1]
        }
        if ($path.StartsWith('"') -and $path.EndsWith('"')) {
            $path = $path.Trim('"')
        }
        $path
    }
}

$candidatePaths = $candidatePaths |
    Where-Object { $_ -and -not (Test-SkippedPath $_) } |
    Sort-Object -Unique

$findings = [System.Collections.Generic.List[string]]::new()

foreach ($path in $candidatePaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        continue
    }

    if (Test-AllowlistedPath $path) {
        continue
    }

    foreach ($pattern in $sensitivePathPatterns) {
        if ($path -match $pattern) {
            $findings.Add("Sensitive filename/path: $path")
            break
        }
    }

    if (-not (Test-TextFile $path)) {
        continue
    }

    try {
        $content = Get-Content -LiteralPath $path -Raw -ErrorAction Stop
    } catch {
        continue
    }

    if ([string]::IsNullOrWhiteSpace($content)) {
        continue
    }

    $lines = $content -split "`r?`n"
    for ($index = 0; $index -lt $lines.Count; $index++) {
        $line = $lines[$index]
        if (Test-AllowlistedLine $line) {
            continue
        }
        foreach ($pattern in $sensitiveContentPatterns) {
            if ($line -match $pattern) {
                $findings.Add("Sensitive content: ${path}:$($index + 1)")
                break
            }
        }
    }
}

if ($findings.Count -gt 0) {
    Write-Host "Security pre-push check FAILED" -ForegroundColor Red
    $findings | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    exit 1
}

Write-Host "Security pre-push check passed." -ForegroundColor Green
Write-Host "Scanned $($candidatePaths.Count) candidate paths from $(if ($AllFiles) { 'the full repository view' } else { 'current local changes' })."
Write-Host "For a full-workspace push, run powershell -File scripts/prepare_workspace_push.ps1 next." -ForegroundColor Cyan