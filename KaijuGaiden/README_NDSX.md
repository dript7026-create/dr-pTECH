# Kaiju Gaiden NDSX Wrapper

`NDSX` stands for `Nintendequed Display Sensory Xchange`.

This project uses `.ndsx` as a self-contained distribution wrapper for the live Nintendo 3DS homebrew build and its adaptive stereo profile.

## What NDSX Is

- A single archive containing the current runnable `.3dsx`
- The matching `.smdh` metadata
- The adaptive stereo profile used by the 3DS build
- Release instructions and branding assets

## What NDSX Is Not

- It is not a native 3DS executable format
- A stock 3DS does not launch `.ndsx` directly
- The directly runnable payload inside the wrapper remains the embedded `.3dsx`

## Archive Layout

- `ndsx/manifest.json`
- `adaptive/profile.json`
- `payload/kaijugaiden.3dsx`
- `payload/kaijugaiden.smdh`
- `payload/icon.png`
- `docs/LAUNCH.txt`

## Adaptive Presets

The wrapper profile currently carries named presets for:

- `studio-balanced`
- `bright-floor-demo`
- `low-strain-mono`

## Build The Wrapper

```powershell
Set-Location C:\Users\rrcar\Documents\drIpTECH\KaijuGaiden
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py pack `
  --exe .\dist\kaijugaiden.3dsx `
  --smdh .\dist\kaijugaiden.smdh `
  --profile .\3ds\ndsx_adaptive_profile.json `
  --icon .\3ds\icon.png `
  --out .\dist\kaijugaiden.ndsx
```

## Inspect The Wrapper

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py inspect .\dist\kaijugaiden.ndsx
```

## Environment Doctor

Before a public release, check the workspace state and tool availability:

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py doctor
```

This reports:

- whether the expected `.3dsx`, `.smdh`, `.ndsx`, `.cia`, profile, RSF, and banner assets exist
- whether `makerom` and `bannertool` were found
- whether the workspace is ready to pack NDSX, build CIA, and assemble a release bundle

## Unpack The Wrapper

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py unpack .\dist\kaijugaiden.ndsx .\dist\kaijugaiden_ndsx_unpacked
```

## Deploy The Embedded 3DS Payload

Preflight the target first if you want the tool to confirm the card layout before copying:

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py verify-target `
  --archive .\dist\kaijugaiden.ndsx `
  --target-dir E:\ `
  --target-layout sd-root `
  --app-name kaijugaiden
```

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py deploy `
  --archive .\dist\kaijugaiden.ndsx `
  --target-dir E:\ `
  --target-layout sd-root `
  --verify-first `
  --app-name kaijugaiden
```

This copies the runnable embedded `.3dsx` payload, `.smdh`, and the wrapper profile into `E:\3ds\kaijugaiden`.

`--target-layout` supports:

- `sd-root`: deploy to `<target>\3ds\<app-name>`
- `homebrew-root`: deploy to `<target>\<app-name>`
- `app-dir`: deploy directly into `<target>`
- `auto`: infer the layout from the path you pass

The release helper script also supports:

```powershell
.\dist\kaijugaiden_3ds_release\verify_3ds_sd_layout.ps1 -TargetPath E:\
.\dist\kaijugaiden_3ds_release\deploy_ndsx_to_3ds_sd.ps1 -TargetPath E:\
.\dist\kaijugaiden_3ds_release\deploy_ndsx_to_3ds_sd.ps1 -AutoDetect
```

If exactly one mounted drive already looks like a 3DS SD card, it will deploy straight to that card.

## Build The End-User Release Folder

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py release `
  --dist-dir .\dist `
  --out-dir .\dist\kaijugaiden_3ds_release
```

If CIA packaging tools are available and `dist\kaijugaiden.cia` exists, the release folder will include that installable title automatically.

The release folder also includes:

- `SHA256SUMS.txt`
- `release_manifest.json`
- `install_kaijugaiden_cia_to_3ds_sd.ps1`

## Build The Installable CIA

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py cia-build
```

This uses the current 3DS ELF plus the project banner assets and writes `dist\kaijugaiden.cia`.

## One-Command Public Release Build

```powershell
..\.venv\Scripts\python.exe .\tools\ndsx_tool.py build-release
```

This command:

- ensures `dist\kaijugaiden.3dsx` and `dist\kaijugaiden.smdh` exist, copying them from `3ds\` if needed
- packs `dist\kaijugaiden.ndsx`
- builds `dist\kaijugaiden.cia` when the CIA packagers and banner assets are available
- regenerates `dist\kaijugaiden_3ds_release`

Useful options:

- `--skip-cia`: release bundle without trying to build the `.cia`
- `--require-cia`: fail the release build if `.cia` packaging is not available
