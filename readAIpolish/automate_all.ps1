param(
    [string]$MediaFolder = ".",
    [string]$OutFolder  = ".\blender_outputs"
)

function Ensure-Admin {
    $isAdmin = (New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "Elevating to administrator..."
        $args = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -MediaFolder `"$MediaFolder`" -OutFolder `"$OutFolder`""
        Start-Process -FilePath powershell -ArgumentList $args -Verb RunAs
        Exit
    }
}

function Install-Chocolatey {
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "Installing Chocolatey..."
        Set-ExecutionPolicy Bypass -Scope Process -Force
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    } else { Write-Host "Chocolatey already installed." }
}

function Choco-InstallIfMissing($pkg) {
    $installed = choco list --local-only --exact $pkg 2>$null
    if (-not $installed) {
        Write-Host "Installing $pkg..."
        choco install $pkg -y --no-progress
    } else { Write-Host "$pkg already installed." }
}

function Add-ToPathIfExists($p) {
    if ((Test-Path $p) -and -not ($env:PATH -split ';' | Where-Object { $_ -ieq $p })) {
        $env:PATH = "$($env:PATH);$p"
        setx PATH "$($env:PATH)" | Out-Null
        Write-Host "Added $p to PATH."
    }
}

Ensure-Admin
Install-Chocolatey

# Install required packages
Choco-InstallIfMissing "ffmpeg"
Choco-InstallIfMissing "blender"
Choco-InstallIfMissing "mingw"

# Common mingw path used by Chocolatey
$mingwPaths = @("C:\tools\mingw64\bin","C:\Program Files\mingw-w64\mingw64\bin")
foreach ($p in $mingwPaths) { Add-ToPathIfExists $p }

# refresh session PATH (merge machine+user)
$env:PATH = ([System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")).TrimEnd(';')

# verify tools
Write-Host "Verifying tools:"
Get-Command ffmpeg -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "ffmpeg -> $($_.Path)" }
Get-Command blender -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "blender -> $($_.Path)" }
Get-Command gcc -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "gcc -> $($_.Path)" }

# compile
$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $scriptDir
$buildLog = Join-Path $scriptDir "build_log.txt"
$runLog   = Join-Path $scriptDir "run_log.txt"

Write-Host "Compiling readAIpolish.c..."
if (Get-Command gcc -ErrorAction SilentlyContinue) {
    gcc -O2 -o readAIpolish.exe readAIpolish.c 2>&1 | Tee-Object $buildLog
} else {
    Write-Host "gcc not found. Build aborted. See installation steps."
    Exit 1
}

if (-not (Test-Path ".\readAIpolish.exe")) {
    Write-Host "Build failed. See $buildLog"
    Exit 1
}

# prepare folders
$media = (Resolve-Path $MediaFolder).Path
if (-not (Test-Path $OutFolder)) { New-Item -ItemType Directory -Path $OutFolder | Out-Null }
$out = (Resolve-Path -LiteralPath $OutFolder).Path

Write-Host "Running readAIpolish.exe on $media -> $out"
Start-Process -FilePath ".\readAIpolish.exe" -ArgumentList @("$media","$out") -NoNewWindow -Wait -RedirectStandardOutput $runLog -RedirectStandardError $runLog

Write-Host "Done. Build log: $buildLog ; Run log: $runLog"