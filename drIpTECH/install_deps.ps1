<#
install_deps.ps1

Downloads and extracts the dependencies listed in master_deps.json into
the workspace `deps/` folder. Requires internet access. Run from an
elevated PowerShell if writing to protected folders.
#>

Param(
    [string]$Manifest = "$PSScriptRoot\master_deps.json",
    [string]$OutDir = "$PSScriptRoot\deps"
)

if (-not (Test-Path $Manifest)) {
    Write-Error "Manifest not found: $Manifest"
    exit 1
}

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

$json = Get-Content $Manifest -Raw | ConvertFrom-Json

foreach ($k in $json.PSObject.Properties.Name) {
    $entry = $json.$k
    $url = $entry.url
    $name = $entry.name
    $ver = $entry.version
    $type = $entry.type
    $dest = Join-Path $OutDir "$k-$ver"
    if (Test-Path $dest) {
        Write-Host "$name $ver already present at $dest"
        continue
    }
    $zipfile = Join-Path $OutDir "$k-$ver.zip"
    Write-Host "Downloading $name $ver from $url ..."
    try {
        Invoke-WebRequest -Uri $url -OutFile $zipfile -UseBasicParsing
    } catch {
        Write-Warning "Failed to download $url : $_"
        continue
    }
    Write-Host "Extracting to $dest ..."
    try {
        Expand-Archive -Path $zipfile -DestinationPath $dest -Force
    } catch {
        Write-Warning "Failed to extract $zipfile : $_"
        continue
    }
    Remove-Item $zipfile -Force
    Write-Host "Installed $name $ver -> $dest"
}

Write-Host "Dependency installation complete. Check $OutDir for extracted SDKs." 
