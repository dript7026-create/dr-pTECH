# DoENGINE Threefold Backup Script
# Mirrors the current workspace contents into the normalized threefold backup tree.

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$backupRoot = Join-Path $projectRoot "ops\backup"
$tiers = @(
    (Join-Path $backupRoot "primary"),
    (Join-Path $backupRoot "secondary"),
    (Join-Path $backupRoot "tertiary")
)

foreach ($tier in $tiers) {
    New-Item -ItemType Directory -Path $tier -Force | Out-Null
    Get-ChildItem -Path $tier -Force | Where-Object { $_.Name -ne '.gitkeep' } | Remove-Item -Recurse -Force
}

$excludedRoots = $tiers | ForEach-Object { (Resolve-Path $_).Path }
$projectRootPath = $projectRoot.Path.TrimEnd('\\')

Get-ChildItem -Path $projectRoot -Recurse -File | Where-Object {
    $filePath = $_.FullName
    foreach ($excluded in $excludedRoots) {
        if ($filePath.StartsWith($excluded, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $false
        }
    }
    return $true
} | ForEach-Object {
    $relativePath = $_.FullName.Substring($projectRootPath.Length).TrimStart('\\')
    foreach ($tier in $tiers) {
        $destination = Join-Path $tier $relativePath
        $destinationDir = Split-Path -Parent $destination
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
        Copy-Item $_.FullName -Destination $destination -Force
    }
}

Write-Host "Threefold backup complete for DoENGINE at $projectRoot."