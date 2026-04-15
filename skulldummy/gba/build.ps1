param(
    [string]$Title = 'skulldummy_gba'
)

function Resolve-PythonCommand {
    $candidates = @(
        $env.SKULLDUMMY_PYTHON,
        'py -3',
        'python'
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates) {
        try {
            if ($candidate -eq 'py -3') {
                & py -3 -c "import sys; print(sys.executable)" *> $null
            } else {
                & $candidate -c "import sys; print(sys.executable)" *> $null
            }
            return $candidate
        } catch {
        }
    }

    throw 'No Python 3 interpreter found. Set SKULLDUMMY_PYTHON, or install py/python in PATH.'
}

function Resolve-MakeInvocation {
    $makeCommand = Get-Command make -ErrorAction SilentlyContinue
    if ($makeCommand) {
        return @{ Mode = 'direct'; Command = $makeCommand.Source }
    }

    $bashCandidates = @(
        $env.DEVKITPRO_BASH,
        $env.MSYS2_BASH,
        (Get-Command bash -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
        (Get-Command bash.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    ) | Where-Object { $_ } | Select-Object -Unique

    foreach ($candidate in $bashCandidates) {
        if (Test-Path $candidate) {
            return @{ Mode = 'bash'; Command = $candidate }
        }
    }

    throw 'No usable make toolchain found. Install make in PATH or set DEVKITPRO_BASH/MSYS2_BASH to a bash executable with make available.'
}

function Initialize-DevkitEnvironment {
    $devkitPro = @(
        $env.DEVKITPRO,
        'C:\devkitPro'
    ) | Where-Object { $_ } | Select-Object -Unique

    foreach ($root in $devkitPro) {
        $devkitArmBin = Join-Path $root 'devkitARM\bin'
        if (Test-Path $devkitArmBin) {
            $env.DEVKITPRO = $root
            if (-not $env.DEVKITARM) {
                $env.DEVKITARM = Join-Path $root 'devkitARM'
            }

            $pathEntries = ($env.PATH -split ';') | Where-Object { $_ }
            if ($pathEntries -notcontains $devkitArmBin) {
                $env.PATH = "$devkitArmBin;$env.PATH"
            }

            return
        }
    }
}

Push-Location $PSScriptRoot
try {
    $pythonCommand = Resolve-PythonCommand
    $makeInvocation = Resolve-MakeInvocation
    Initialize-DevkitEnvironment

    if ($pythonCommand -eq 'py -3') {
        & py -3 "$PSScriptRoot\tools\convert_assets.py"
    } else {
        & $pythonCommand "$PSScriptRoot\tools\convert_assets.py"
    }

    if ($LASTEXITCODE -ne 0) {
        throw 'asset conversion failed'
    }

    if ($makeInvocation.Mode -eq 'direct') {
        & $makeInvocation.Command clean "TITLE=$Title"
        if ($LASTEXITCODE -ne 0) {
            throw 'GBA clean failed'
        }
        & $makeInvocation.Command "TITLE=$Title"
    } else {
        $gbaPath = $PSScriptRoot.Replace('\', '/')
        $buildCommand = "cd '$gbaPath' && make clean TITLE=$Title && make TITLE=$Title"
        & $makeInvocation.Command -lc $buildCommand
    }

    if ($LASTEXITCODE -ne 0) {
        throw 'GBA build failed'
    }
    Write-Host "Built $Title.gba"
} catch {
    Write-Error "Build failed: $_"
    exit 3
} finally {
    Pop-Location
}