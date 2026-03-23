param(
    [switch]$PersistUserEnvironment,
    [switch]$Quiet
)

$workspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$gbdkRoot = Join-Path $workspaceRoot ".tools\gbdk\gbdk"
$gbdkRootForward = (($gbdkRoot -replace '\\', '/') + '/')
$devkitProRoot = "C:\devkitPro"
$mingwRoot = "C:\tools\msys64\mingw64\bin"

$requiredPaths = @(
    $mingwRoot,
    (Join-Path $devkitProRoot "msys2\usr\bin"),
    (Join-Path $devkitProRoot "devkitARM\bin"),
    (Join-Path $devkitProRoot "devkitA64\bin"),
    (Join-Path $devkitProRoot "devkitPPC\bin"),
    (Join-Path $devkitProRoot "tools\bin"),
    (Join-Path $gbdkRoot "bin")
)

$envVars = @{
    DEVKITPRO = $devkitProRoot
    DEVKITARM = Join-Path $devkitProRoot "devkitARM"
    DEVKITPPC = Join-Path $devkitProRoot "devkitPPC"
    DEVKITA64 = Join-Path $devkitProRoot "devkitA64"
    GBDKDIR   = $gbdkRootForward
}

foreach ($item in $envVars.GetEnumerator()) {
    Set-Item -Path "Env:$($item.Key)" -Value $item.Value
}

$sessionSegments = @()
if ($env:PATH) {
    $sessionSegments = $env:PATH -split ';' | Where-Object { $_ }
}

foreach ($path in $requiredPaths) {
    if ((Test-Path $path) -and -not ($sessionSegments -contains $path)) {
        $sessionSegments = @($path) + $sessionSegments
    }
}

$env:PATH = $sessionSegments -join ';'

if ($PersistUserEnvironment) {
    foreach ($item in $envVars.GetEnumerator()) {
        [Environment]::SetEnvironmentVariable($item.Key, $item.Value, 'User')
    }

    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $userSegments = @()
    if ($userPath) {
        $userSegments = $userPath -split ';' | Where-Object { $_ }
    }
    foreach ($path in $requiredPaths) {
        if ((Test-Path $path) -and -not ($userSegments -contains $path)) {
            $userSegments += $path
        }
    }
    [Environment]::SetEnvironmentVariable('Path', ($userSegments -join ';'), 'User')
}

if (-not $Quiet) {
    Write-Host "Workspace toolchains configured for this session."
    Get-Command gcc, make, arm-none-eabi-gcc, lcc -ErrorAction SilentlyContinue |
        Select-Object Name, Source |
        Format-Table -AutoSize
    Write-Host "Note: devkitPro compiler drivers are MSYS launchers here; use .\\workspace_devkitpro_bash.ps1 for direct compiler invocations from PowerShell."
}