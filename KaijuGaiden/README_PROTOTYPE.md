# Kaiju Gaiden — Prototype README

This folder contains two distinct Kaiju Gaiden codepaths:

- `kaijugaiden.c` is the dedicated Game Boy game source used for the `.gb` ROM line.
- `kaijugaiden_gba.c` is the dedicated Game Boy Advance entrypoint used for the modular `.gba` prototype under `src/`.

## Running the Prototype

Run the host graphical prototype:

```powershell
py -3 KaijuGaiden\host_graphical.py
```

Optional graphical host dependencies:

- Install [KaijuGaiden/requirements-graphical.txt](KaijuGaiden/requirements-graphical.txt) when you want pygame-backed joystick fallback or the richer graphical host path.
- The workspace health manifest for this stack is [tools/dependency_manifests/kaijugaiden_graphics.json](tools/dependency_manifests/kaijugaiden_graphics.json).

Open-source stack credits:

- `KaijuGaiden` targets GBDK-2020 for the Game Boy path, devkitARM/libgba for the GBA path, and SDL2 for the richer host runtime path.
- Workspace-wide attribution tracking for these dependencies is kept in [THIRD_PARTY_CREDITS.md](../THIRD_PARTY_CREDITS.md).
- The broader open-source 3D/runtime stack manifest is [tools/dependency_manifests/open_source_3d_stack.json](../tools/dependency_manifests/open_source_3d_stack.json).

Dependency management:

- A workspace-level dependency manifest and installer script are available at `drIpTECH/master_deps.json` and `drIpTECH/install_deps.ps1`.
- To fetch prebuilt SDL2 and raylib SDKs for Windows, run:

```powershell
cd drIpTECH
.\install_deps.ps1
```

After extraction, copy the appropriate DLLs from `drIpTECH\deps\*` into the project's `KaijuGaiden\build` or `dist` folder before packaging.

Prerequisites

- Install devkitPro (includes devkitARM). On Windows, use the devkitPro installer and MSYS2 shell.

Build (example)

1. Open MSYS2 MinGW shell provided by devkitPro.
2. cd to this folder.
3. run `make` to produce `kaijugaiden.gba` from `kaijugaiden_gba.c` plus the `src/` runtime modules (Makefile assumes `arm-none-eabi-gcc` on PATH).

Notes

- The Makefile is a simple example — you may need to adapt linker scripts and crt0 for full GBA compatibility. For a production build, prefer devkitPro's project templates or the `libgba` build rules.
- The `.gb` game lives in `kaijugaiden.c` as a separate design and runtime track.
- The `.gba` game lives in `kaijugaiden_gba.c` plus the modular sources in `src/`.
- Assets are placeholder text files under `assets/` and will need conversion to GBA tiles/sprites.

Prototype controls (console demo):

- Press `START` to open the title menu.
- In the menu: `A` starts the boss demo, `B` triggers the password stub, `START` plays the VN stub.
- `SELECT` applies one Growth NanoCell to the prototype player (debug) and prints the new growth tier and visual variant.

Next steps

- Replace placeholder assets with tile sheets and palettes, add tools/ tile conversion scripts, and iterate on gameplay code in `src/`.
