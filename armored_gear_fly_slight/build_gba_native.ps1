param()

Push-Location $PSScriptRoot
try {
    $devkitPro = if ($env:DEVKITPRO) { $env:DEVKITPRO } else { "C:\devkitPro" }
    $gcc = Join-Path $devkitPro "devkitARM\bin\arm-none-eabi-gcc.exe"
    $objcopy = Join-Path $devkitPro "devkitARM\bin\arm-none-eabi-objcopy.exe"
    $gbafix = Join-Path $devkitPro "tools\bin\gbafix.exe"
    $includeDir = Join-Path $devkitPro "libgba\include"
    $libDir = Join-Path $devkitPro "libgba\lib"

    if (!(Test-Path $gcc)) {
        throw "arm-none-eabi-gcc not found at $gcc"
    }
    if (!(Test-Path $objcopy)) {
        throw "arm-none-eabi-objcopy not found at $objcopy"
    }
    if (!(Test-Path $gbafix)) {
        throw "gbafix not found at $gbafix"
    }
    if (!(Test-Path $includeDir) -or !(Test-Path $libDir)) {
        throw "libgba include/lib folders not found under $devkitPro"
    }

    $buildDir = Join-Path $PSScriptRoot "build\gba_native"
    if (!(Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }

    $sources = @(
        (Join-Path $PSScriptRoot "gba_native\main.c"),
        (Join-Path $PSScriptRoot "gba_native\port_gba.c"),
        (Join-Path $PSScriptRoot "gba_native\port_game.c")
    )
    $elf = Join-Path $buildDir "armored_gear_fly_slight_native.elf"
    $gba = Join-Path $PSScriptRoot "armored_gear_fly_slight_native.gba"

    Write-Host "Building armored_gear_fly_slight_native.gba (devkitARM/libgba)"
    & $gcc `
        -mthumb -mthumb-interwork -mcpu=arm7tdmi `
        -O2 -Wall -ffunction-sections -fdata-sections `
        --specs=gba.specs `
        -I "$includeDir" `
        -I (Join-Path $PSScriptRoot "gba_native") `
        $sources `
        -L "$libDir" -lgba `
        "-Wl,--gc-sections" `
        -o "$elf"

    if ($LASTEXITCODE -ne 0) {
        throw "Native GBA compile failed"
    }

    & $objcopy -O binary "$elf" "$gba"
    if ($LASTEXITCODE -ne 0) {
        throw "Native GBA objcopy failed"
    }

    # Ensure output has a valid GBA cart header and checksum metadata.
    & $gbafix "$gba" -p -tARMOREDGEAR -cAGFS -m01 -r0
    if ($LASTEXITCODE -ne 0) {
        throw "gbafix failed"
    }

    Write-Host "Built armored_gear_fly_slight_native.gba"
} catch {
    Write-Error "Native GBA build failed: $_"
    exit 3
} finally {
    Pop-Location
}
