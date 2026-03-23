# Kaiju Gaiden CIA Tooling Path

The workspace can now build both the 3DS homebrew `.3dsx` output and an installable `.cia` when `makerom.exe` and `bannertool.exe` are available.

## Required Tools

- `makerom.exe`
- `bannertool.exe`
- existing devkitPro `3dsxtool.exe`

## Current Check

Run:

```powershell
Set-Location C:\Users\rrcar\Documents\drIpTECH\KaijuGaiden
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py cia-tools --devkitpro C:/devkitPro
```

The tool also checks local parent-directory folders such as `..\makerom\makerom.exe` and `..\bannertool\windows-x86_64\bannertool.exe`.

## Why This Matters

- `.3dsx` is directly launchable from the Homebrew Launcher
- `.cia` is the installable title path that behaves more like a native game install
- `.ndsx` in this repo is a wrapper/container around the live `.3dsx` release, not a native 3DS executable format

## Build The CIA

```powershell
Set-Location C:\Users\rrcar\Documents\drIpTECH\KaijuGaiden
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py cia-build
```

For a full public-facing package refresh, use:

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py build-release --require-cia
```

Default inputs:

- `3ds\kaijugaiden.elf`
- `3ds\kaijugaiden.smdh`
- `3ds\kaijugaiden.rsf`
- `3ds\banner.png`
- `3ds\banner.wav`
- output `dist\kaijugaiden.cia`

Optional overrides are available for all inputs and both packager executables:

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py cia-build `
	--makerom ..\makerom\makerom.exe `
	--bannertool ..\bannertool\windows-x86_64\bannertool.exe `
	--out .\dist\kaijugaiden.cia
```

## Relationship To NDSX

- `.ndsx` remains the branded adaptive-distribution wrapper
- `.3dsx` remains the Homebrew Launcher payload
- `.cia` is the installable title built from the ELF, SMDH, RSF, and banner assets

## Release Quality Of Life

The public release bundle can now include:

- `kaijugaiden.cia`
- `SHA256SUMS.txt`
- `release_manifest.json`
- `install_kaijugaiden_cia_to_3ds_sd.ps1`