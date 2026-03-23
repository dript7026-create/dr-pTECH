param(
    [ValidateSet('gba', 'gb', 'gba-autoplay')]
    [string]$Target = 'gba'
)

$toolchainScript = Join-Path (Split-Path -Parent $PSScriptRoot) "workspace_toolchains.ps1"
if (Test-Path $toolchainScript) {
    & $toolchainScript -Quiet
}

Push-Location $PSScriptRoot
try {
    if ($Target -eq 'gb') {
        Write-Host "Building tommybeta.gb (GBDK)"
        if (-not (Get-Command lcc -ErrorAction SilentlyContinue)) {
            throw "lcc not found in PATH. Install GBDK 2020 and ensure lcc is available."
        }
        lcc -o tommybeta.gb src\main.c
        if ($LASTEXITCODE -ne 0) { throw "GB build failed" }
        Write-Host "Built tommybeta.gb"
    } else {
        Write-Host "Generating GBA Mode 3 assets"
        & "c:\Users\rrcar\Documents\drIpTECH\.venv\Scripts\python.exe" "$PSScriptRoot\tools\generate_end_state_screens.py"
        if ($LASTEXITCODE -ne 0) { throw "presentation screen generation failed" }
        & "c:\Users\rrcar\Documents\drIpTECH\.venv\Scripts\python.exe" "$PSScriptRoot\tools\convert_mode3_assets.py"
        if ($LASTEXITCODE -ne 0) { throw "asset conversion failed" }

        $bashScript = Join-Path (Split-Path -Parent $PSScriptRoot) "workspace_devkitpro_bash.ps1"
        if (-not (Test-Path $bashScript)) {
            throw "workspace_devkitpro_bash.ps1 not found"
        }

        if ($Target -eq 'gba-autoplay') {
            Write-Host "Building tommybeta_autoplay.gba"
            & $bashScript "cd tommybeta && make -f Makefile.gba clean TITLE=tommybeta_autoplay EXTRA_DEFINES=-DTOMMYBETA_AUTOPLAY && make -f Makefile.gba TITLE=tommybeta_autoplay EXTRA_DEFINES=-DTOMMYBETA_AUTOPLAY"
        } else {
            Write-Host "Building tommybeta.gba"
            & $bashScript "cd tommybeta && make -f Makefile.gba clean && make -f Makefile.gba"
        }
        if ($LASTEXITCODE -ne 0) { throw "GBA build failed" }
        if ($Target -eq 'gba-autoplay') {
            Write-Host "Built tommybeta_autoplay.gba"
        } else {
            Write-Host "Built tommybeta.gba"
        }
    }
} catch {
    Write-Error "Build failed: $_"
    exit 3
} finally {
    Pop-Location
}
