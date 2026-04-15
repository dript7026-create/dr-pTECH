param(
    [switch]$SkipSmoke,
    [switch]$Launch
)

$ErrorActionPreference = 'Stop'

function Get-VcVarsPath {
    $vsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-Path $vsWhere) {
        $installPath = & $vsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
        if ($LASTEXITCODE -eq 0 -and $installPath) {
            $vcVars = Join-Path $installPath 'VC\Auxiliary\Build\vcvars64.bat'
            if (Test-Path $vcVars) {
                return $vcVars
            }
        }
    }

    $fallbacks = @(
        'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
    )

    foreach ($candidate in $fallbacks) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw 'Unable to locate vcvars64.bat. Install Visual Studio C++ tools or adjust the build script.'
}

function Get-DepsRoot {
    param(
        [string]$RepoRoot
    )

    $candidates = @(
        (Join-Path $RepoRoot 'deps'),
        (Join-Path $RepoRoot 'drIpTECH\deps')
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw 'Unable to locate the SDL dependency root. Expected deps or drIpTECH\deps under the workspace root.'
}

$projectDir = Split-Path -Parent $PSCommandPath
$repoRoot = Split-Path -Parent $projectDir
$tempDir = Join-Path $repoRoot '.tmp'
$outputDir = Join-Path $repoRoot 'build\aridfeihth'
$sourceFile = Join-Path $projectDir 'aridfeihth_runtime_sdl.cpp'
$outputExe = Join-Path $outputDir 'AridfeihthSDLDemo.exe'
$objectFile = Join-Path $tempDir 'aridfeihth_runtime_sdl.obj'
$batchFile = Join-Path $tempDir 'build_aridfeihth_sdl.cmd'
$logFile = Join-Path $repoRoot 'build_aridfeihth_sdl_build.log'

$depsRoot = Get-DepsRoot -RepoRoot $repoRoot
$sdlRoot = Join-Path $depsRoot 'sdl2-2.28.4\SDL2-2.28.4'
$imageRoot = Join-Path $depsRoot 'sdl2_image-2.0.5\SDL2_image-2.0.5'
$ttfRoot = Join-Path $depsRoot 'sdl2_ttf-2.20.1\SDL2_ttf-2.20.1'

foreach ($path in @($sourceFile, $sdlRoot, $imageRoot, $ttfRoot)) {
    if (-not (Test-Path $path)) {
        throw "Required path is missing: $path"
    }
}

New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$vcVars = Get-VcVarsPath

$clArguments = @(
    '/nologo',
    '/std:c++17',
    '/EHsc',
    '/O2',
    '/W3',
    '/D_CRT_SECURE_NO_WARNINGS',
    ('/I"{0}"' -f $projectDir),
    ('/I"{0}"' -f (Join-Path $sdlRoot 'include')),
    ('/I"{0}"' -f (Join-Path $imageRoot 'include')),
    ('/I"{0}"' -f (Join-Path $ttfRoot 'include')),
    ('/Fo"{0}"' -f $objectFile),
    ('/Fe:"{0}"' -f $outputExe),
    ('"{0}"' -f $sourceFile),
    '/link',
    ('/LIBPATH:"{0}"' -f (Join-Path $sdlRoot 'lib\x64')),
    ('/LIBPATH:"{0}"' -f (Join-Path $imageRoot 'lib\x64')),
    ('/LIBPATH:"{0}"' -f (Join-Path $ttfRoot 'lib\x64')),
    'SDL2main.lib',
    'SDL2.lib',
    'SDL2_image.lib',
    'SDL2_ttf.lib',
    'user32.lib',
    'gdi32.lib',
    'shell32.lib',
    'ole32.lib',
    'advapi32.lib',
    'winmm.lib',
    'imm32.lib',
    'version.lib'
)

$batchContent = @(
    '@echo off',
    ('call "{0}" >nul 2>nul' -f $vcVars),
    'if errorlevel 1 exit /b 1',
    ('cl {0}' -f ($clArguments -join ' '))
) -join "`r`n"

Set-Content -Path $batchFile -Value $batchContent -Encoding ASCII

if (Test-Path $logFile) {
    Remove-Item $logFile -Force
}

$buildOutput = & cmd.exe /c ('"{0}"' -f $batchFile) 2>&1
$buildOutput | Tee-Object -FilePath $logFile
if ($LASTEXITCODE -ne 0) {
    throw "SDL build failed. See $logFile"
}

foreach ($dllFolder in @(
    (Join-Path $sdlRoot 'lib\x64'),
    (Join-Path $imageRoot 'lib\x64'),
    (Join-Path $ttfRoot 'lib\x64')
)) {
    Get-ChildItem -Path $dllFolder -Filter *.dll | Copy-Item -Destination $outputDir -Force
}

if (-not $SkipSmoke) {
    $smokeOutput = & $outputExe --smoke 2>&1
    $smokeOutput | Tee-Object -FilePath $logFile -Append
    if ($LASTEXITCODE -ne 0) {
        throw "SDL smoke check failed. See $logFile"
    }
}

Write-Host "Built $outputExe"

if ($Launch) {
    Start-Process -FilePath $outputExe -WorkingDirectory $outputDir
}