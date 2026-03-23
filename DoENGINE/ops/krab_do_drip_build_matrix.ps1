param(
    [ValidateSet("windows", "linux", "macos", "android", "web", "n3ds", "all")]
    [string]$Platform = "all"
)

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$dripRoot = Split-Path -Parent $repoRoot

function Invoke-Step($name, [scriptblock]$action) {
    Write-Host "==> $name"
    & $action
    if ($LASTEXITCODE -ne 0) {
        throw "$name failed with exit code $LASTEXITCODE"
    }
}

function Build-Windows {
    $project = Join-Path $dripRoot "bango-patoot_3DS"
    Push-Location $project
    try {
        Invoke-Step "Windows preview build" { .\build_windows_preview.ps1 }
        if (Test-Path (Join-Path $project "idtech2_mod")) {
            if (Test-Path (Join-Path $dripRoot ".tools\bin\q2sdk-env.ps1")) {
                . (Join-Path $dripRoot ".tools\bin\q2sdk-env.ps1")
                Invoke-Step "Windows idTech2 module build" { . (Join-Path $dripRoot ".tools\bin\bango-idtech2-build.ps1") }
            }
        }
    }
    finally {
        Pop-Location
    }
}

function Build-N3DS {
    $project = Join-Path $dripRoot "bango-patoot_3DS"
    Push-Location $project
    try {
        Invoke-Step "new 3DS build" { .\build_3ds.ps1 }
    }
    finally {
        Pop-Location
    }
}

function Build-Web {
    Write-Host "Web build placeholder: wire Emscripten target when runtime abstraction is finalized."
}

function Build-Linux {
    Write-Host "Linux build placeholder: add GCC/Clang native target in CMake superbuild."
}

function Build-MacOS {
    Write-Host "macOS build placeholder: add AppleClang target in CMake superbuild."
}

function Build-Android {
    Write-Host "Android build placeholder: add NDK toolchain preset in CMake superbuild."
}

switch ($Platform) {
    "windows" { Build-Windows }
    "n3ds" { Build-N3DS }
    "web" { Build-Web }
    "linux" { Build-Linux }
    "macos" { Build-MacOS }
    "android" { Build-Android }
    "all" {
        Build-Windows
        Build-N3DS
        Build-Web
        Build-Linux
        Build-MacOS
        Build-Android
    }
}
