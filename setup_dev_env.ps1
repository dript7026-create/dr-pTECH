<#
  setup_dev_env.ps1
  PowerShell installer for developer toolchain (Windows).

  WARNING: This script performs system installs and requires Administrator privileges.
  It downloads large toolchains and may require interactive installers for some components.
  Review before running. The script DOES NOT run Unity or Epic installers.
#>

param(
    [switch]$PerformInstall = $false
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

function Ensure-Admin {
    $current = [Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not $current.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error "This script must be run as Administrator. Re-launch PowerShell as Admin and re-run this script."
        exit 1
    }
}

function Get-UserHome {
    if ($env:HOMEDRIVE -and $env:HOMEPATH) {
        return "$($env:HOMEDRIVE)$($env:HOMEPATH)"
    }
    if ($env:USERPROFILE) {
        return $env:USERPROFILE
    }
    return [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)
}

function Get-PackageManager {
    if (Get-Command winget -ErrorAction SilentlyContinue) { return 'winget' }
    if (Get-Command choco -ErrorAction SilentlyContinue) { return 'choco' }
    return $null
}

function Install-Tool {
    param(
        [string]$WingetId,
        [string]$ChocoId,
        [string]$Label
    )

    $pm = Get-PackageManager
    if ($pm -eq 'winget') {
        Write-Host "Installing $Label via winget..."
        winget install --id $WingetId -e --source winget
        return
    }
    if ($pm -eq 'choco') {
        Write-Host "Installing $Label via choco..."
        choco install $ChocoId -y
        return
    }
    Write-Warning "No supported package manager found for $Label. Install it manually."
}

function Repair-GitConfiguration {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Warning "git not found yet; skipping git TLS repair."
        return
    }

    Write-Host "Repairing git TLS configuration for Windows..."
    git config --global --unset-all http.sslcainfo 2>$null
    git config --global http.sslbackend schannel
}

if ($PerformInstall) { Ensure-Admin }

Write-Host "This script will prepare the developer toolchain. Review and run with -PerformInstall to execute."

<# --- Configuration: change paths as needed --- #>
$UserHome = Get-UserHome
$ToolsRoot = "C:\Users\$env:USERNAME\Documents\drIpTECH\tools"
$VcpkgRoot = Join-Path $UserHome 'vcpkg'
$EmsdkRoot = Join-Path $UserHome 'emsdk'

Write-Host "Planned actions (dry-run):"
Write-Host " - Install Git, Visual Studio Build Tools, CMake, Ninja, MSYS2, Node, Haxe via winget or choco"
Write-Host " - Clone and bootstrap vcpkg; install sdl2, sdl2-image, sdl3 (if available), raylib"
Write-Host " - Clone and bootstrap emsdk (Emscripten) for WASM builds"
Write-Host " - Download devkitPro installer to Downloads (interactive)"
Write-Host " - Install Python pip packages (Pillow, etc.)"
Write-Host " - Clone open-source idTech ports to $ToolsRoot"
Write-Host " - Add $ToolsRoot to user PATH"

if (-not $PerformInstall) { return }

Ensure-Admin

Write-Host "Starting installation..."

# 1) winget installs
Write-Host "Installing base packages via available package manager..."
Install-Tool -WingetId 'Git.Git' -ChocoId 'git' -Label 'Git'
Install-Tool -WingetId 'Microsoft.VisualStudio.2022.BuildTools' -ChocoId 'visualstudio2022buildtools' -Label 'Visual Studio Build Tools'
Install-Tool -WingetId 'Kitware.CMake' -ChocoId 'cmake' -Label 'CMake'
Install-Tool -WingetId 'NinjaBuild.Ninja' -ChocoId 'ninja' -Label 'Ninja'
Install-Tool -WingetId 'MSYS2.MSYS2' -ChocoId 'msys2' -Label 'MSYS2'
Install-Tool -WingetId 'OpenJS.NodeJS' -ChocoId 'nodejs-lts' -Label 'Node.js LTS'
Install-Tool -WingetId 'HaxeFoundation.Haxe' -ChocoId 'haxe' -Label 'Haxe'

Repair-GitConfiguration

# 2) vcpkg: clone and bootstrap
Write-Host "Cloning and bootstrapping vcpkg..."
if (-not (Test-Path $VcpkgRoot)) {
    git clone https://github.com/microsoft/vcpkg.git $VcpkgRoot
}
Push-Location $VcpkgRoot
& .\bootstrap-vcpkg.bat
& .\vcpkg integrate install
# Install common dev libs
$rc = & .\vcpkg install sdl2:x64-windows sdl2-image:x64-windows raylib:x64-windows
if ($LASTEXITCODE -ne 0) { Write-Host "Some vcpkg packages may not be available on this platform; build from source if needed." }
$rc = & .\vcpkg install sdl3:x64-windows
if ($LASTEXITCODE -ne 0) { Write-Host "SDL3 not available in vcpkg; will attempt source build later." }
Pop-Location

# 3) Emscripten SDK (emsdk)
Write-Host "Cloning Emscripten SDK..."
if (-not (Test-Path $EmsdkRoot)) {
    git clone https://github.com/emscripten-core/emsdk.git $EmsdkRoot
}
Push-Location $EmsdkRoot
& .\emsdk.bat install latest
& .\emsdk.bat activate latest
# Note: You may need to run emsdk_env.bat in new shells to update PATH
& .\emsdk_env.bat
Pop-Location

# 4) Python packages
Write-Host "Installing Python packages via pip..."
python -m pip install --upgrade pip
python -m pip install Pillow

# 5) devkitPro installer (download only - interactive run recommended)
Write-Host "Downloading devkitPro installer to Downloads (interactive install required)..."
$dkp_url = 'https://github.com/devkitPro/pacman/releases/latest/download/devkitpro-installer.exe'
$dkp_path = Join-Path $UserHome 'Downloads\devkitpro-installer.exe'
Invoke-WebRequest -Uri $dkp_url -OutFile $dkp_path -UseBasicParsing

# 6) Clone open-source idTech ports and tools
Write-Host "Cloning open-source engine ports to $ToolsRoot..."
New-Item -ItemType Directory -Force -Path $ToolsRoot | Out-Null
Push-Location $ToolsRoot
if (-not (Test-Path ioquake3)) { git clone https://github.com/ioquake/ioq3.git ioquake3 }
if (-not (Test-Path vkquake)) { git clone https://github.com/DaemonEngine/vkQuake.git vkquake }
if (-not (Test-Path quakespasm)) { git clone https://github.com/jj1bdx/Quakespasm.git quakespasm }
Pop-Location

# 7) Add tools dir to user PATH persistently
Write-Host "Adding $ToolsRoot to user PATH (if missing)..."
$oldPath = [Environment]::GetEnvironmentVariable('Path',[EnvironmentVariableTarget]::User)
if ($oldPath -notlike "*$ToolsRoot*") {
    [Environment]::SetEnvironmentVariable('Path', "$oldPath;$ToolsRoot", [EnvironmentVariableTarget]::User)
}

Write-Host "Setup complete. Please restart PowerShell (or sign out/in) to pick up PATH changes."
Write-Host "Interactive installers requiring attention: devkitPro installer at $dkp_path."
Write-Host "If SDL3 or raylib builds failed in vcpkg, you may need to build from source or install prebuilt binaries."

Write-Host "Notes: Unity and Unreal installers were intentionally omitted per request."
