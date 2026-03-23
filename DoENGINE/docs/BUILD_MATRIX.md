# Krab/Do/Drip Engine Build Matrix

This workspace now includes a unified orchestration script at `ops/krab_do_drip_build_matrix.ps1`.

## Current live targets

- `windows`: builds `bango-patoot_3DS` preview executable.
- `windows` + idTech2: if `Q2_SDK_DIR` is configured, builds the Bango Quake II game module.
- `n3ds`: builds `BangoPatoot.3dsx` via devkitPro toolchain.

## Planned targets

- `linux`: native desktop toolchain target (CMake superbuild pending).
- `macos`: AppleClang target (CMake superbuild pending).
- `android`: NDK target (toolchain file + ABI matrix pending).
- `web`: Emscripten target (runtime abstraction pending).

## Usage

From `DoENGINE`:

```powershell
.\ops\krab_do_drip_build_matrix.ps1 -Platform all
```

Run one target:

```powershell
.\ops\krab_do_drip_build_matrix.ps1 -Platform windows
.\ops\krab_do_drip_build_matrix.ps1 -Platform n3ds
```

## Environment

For idTech2 builds, run:

```powershell
..\.tools\bin\q2sdk-env.ps1
```

Then call:

```powershell
..\.tools\bin\bango-idtech2-build.ps1
```

Deploy into the Quake II SDK mod folder:

```powershell
..\.tools\bin\bango-idtech2-deploy.ps1 -ModName bango
```
