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
    '(?i)(^|[\\/]).*\.(pem|p12|pfx|jks|keystore|key|crt|cer)$',
    '(?i)(^|[\\/]).*(invoice|financial|payroll|tax.?return|bank.?account|budget.?private|lender|confidential|nda).*'
)

$sensitiveContentPatterns = @(
    '(?i)OPENAI_API_KEY\s*[=:]\s*[^\s"'']+',
    '(?i)AZURE_OPENAI_API_KEY\s*[=:]\s*[^\s"'']+',
    '(?i)AWS_SECRET_ACCESS_KEY\s*[=:]\s*[^\s"'']+',
    '(?i)client_secret\s*[=:]\s*[^\s"'']+',
    '(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._\-]+',
    '(?i)-----BEGIN [A-Z ]*PRIVATE KEY-----',
    '(?i)github_pat_[A-Za-z0-9_]+',
    '(?i)gh[pousr]_[A-Za-z0-9]+',
    '(?i)sk-[A-Za-z0-9]{20,}',
    '(?i)api[_-]?key\s*[=:]\s*[^\s"'']{12,}'
)

$allowlistedContentPatterns = @(
    '(?i)OPENAI_API_KEY not set',
    '(?i)Set the environment variable `OPENAI_API_KEY`',
    '(?i)required_env',
    '(?i)api_key_present',
    '(?i)password system',
    '(?i)rcon_password',
    '(?i)token',
    '(?i)client_secret.*placeholder',
    '(?i)example',
    '(?i)sample'
)

$skipDirectories = @(
    '.git\',
    '.venv\',
    '.jdk\',
    '.android-bootstrap\',
    '.tools\',
    '__pycache__\',
    '.pytest_cache\'
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