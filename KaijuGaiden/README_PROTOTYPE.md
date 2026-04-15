# Kaiju Gaiden — Prototype README

This folder contains three practical Kaiju Gaiden targets, but the current priority target is the Windows build driven by an Xbox Series controller.

- `kaijugaiden.c` is the dedicated Game Boy game source used for the `.gb` ROM line.
- `kaijugaiden_gba.c` is the dedicated Game Boy Advance entrypoint used for the modular `.gba` prototype under `src/`.
- `host_graphical.py` is the Windows-first graphical prototype with Xbox Series controller support through XInput and a pygame joystick fallback.
- The current Windows target is a single central build: original Harbor Shore combat flow and pixel-faithful composition, enhanced with higher-resolution staging, layered shoreline detail, and the HOPE inward-depth presentation path.
- Pixel-art runtime sprites now come from the generated handheld asset headers in `assets/gb`, while `assets/source/gb` remains the preferred editable source-art root when those PNGs are available.

## Priority Target: Windows + Xbox Series Controller

If the goal is a controller-first Windows build, use the graphical host path first.

- primary input: Xbox Series controller through `xinput1_4.dll`, `xinput1_3.dll`, or `xinput9_1_0.dll`
- fallback input: pygame joystick mapping when native XInput is unavailable
- keyboard remains available for debugging, but the intended lead path is controller-first
- packaging target: `dist/kaijugaiden_windows_xbox/kaijugaiden_windows_xbox.exe`
- HOPE adaptive depth now reuses the 3DS preset vocabulary on Windows and can optionally read a live camera feed to tune inward-depth illusions on a traditional single screen
- the Windows host now targets a centered `1920x1080` fullscreen presentation with a `1440x960` gameplay viewport derived from the original `240x160` scene

Quick build:

```powershell
powershell -ExecutionPolicy Bypass -File .\KaijuGaiden\tools\build_windows_xbox_host.ps1
```

Quick run without packaging:

```powershell
py -3 .\KaijuGaiden\host_graphical.py
```

## Running the Prototype

Run the host graphical prototype:

```powershell
py -3 KaijuGaiden\host_graphical.py
```

Optional graphical host dependencies:

- Install [KaijuGaiden/requirements-graphical.txt](KaijuGaiden/requirements-graphical.txt) when you want pygame-backed joystick fallback or the richer graphical host path.
- `opencv-python` is optional but recommended when you want the camera-fed adaptive-depth processor to react to lighting, face proximity, and eye state.
- The workspace health manifest for this stack is [tools/dependency_manifests/kaijugaiden_graphics.json](tools/dependency_manifests/kaijugaiden_graphics.json).
- For packaged Windows builds, install `pyinstaller` into the same Python environment used to launch `host_graphical.py`.

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

## Windows Build Lane

The repository now treats the Windows Xbox-controller build as the most direct playable target.

What the build script does:

- verifies Python and Tkinter availability
- optionally installs graphical Python dependencies
- tries to build `build/xinput_wrapper.dll` with GCC when available
- assembles `asm/hope_depth_core_x64.asm` into `build/asm/hope_depth_core_x64.obj` when `nasm` is available
- packages the graphical host with PyInstaller when available
- emits a Windows-first executable named `kaijugaiden_windows_xbox.exe`

Expected controller mapping:

- left stick or d-pad: movement
- `A` or `X`: primary attack
- `B`: dodge or nanocell use depending on state
- `LB` and `RB`: shoulder actions
- `Start`: start or pause
- `Back/View`: tutorial close or select-equivalent behavior

Adaptive depth controls:

- `F3`: toggle HOPE adaptive inward depth on or off
- `F4`: cycle the shared 3DS preset vocabulary: `studio-balanced`, `bright-floor-demo`, `low-strain-mono`
- `F5`: start or stop the optional camera-fed depth processor

The Windows host does not reproduce Nintendo's physical 3D display. It reuses the Kaiju Gaiden `.ndsx` stereoadaptive semantics and applies them to a single-screen inward-depth illusion that responds to HOPE runtime bias plus live camera estimates for brightness, face distance, eye openness, and pupil-darkness heuristics.

Assembly pipeline note:

- `nasm` is now available from the user `PATH`, so the repo can assemble the first x64 depth-core scaffold into a Windows object file
- `ml64`, `cl.exe`, and `link.exe` are still not available in the current shell, so the active playable Windows implementation remains the high-level host runtime
- the assembly-port decomposition, memory layout, and full render pipeline contract are documented in [KaijuGaiden/ASSEMBLY_DEPTH_PIPELINE.md](KaijuGaiden/ASSEMBLY_DEPTH_PIPELINE.md)

Standalone assembly build:

```powershell
powershell -ExecutionPolicy Bypass -File .\KaijuGaiden\tools\build_depth_asm.ps1
```

This currently produces a NASM `win64` object file that stages the first inward-depth strength and reprojection entrypoints for the future native Windows render lane.

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
- The Windows controller-first build currently rides the `host_graphical.py` path rather than the GBA toolchain.
- Assets are placeholder text files under `assets/` and will need conversion to GBA tiles/sprites.
- Boss-facing art direction for the twelve-boss campaign is tracked in `BOSS_DESIGN_PROFILES.md`.
- Sprite prompt sheets, ecology-linked minion briefs, and the per-boss asset manifest are tracked in `BOSS_SPRITE_PROMPT_SHEETS.md`, `BOSS_MINION_ECOLOGY_PROFILES.md`, and `boss_asset_manifest.json`.

Prototype controls (console demo):

- Press `START` to open the title menu.
- In the menu: `A` starts the boss demo, `B` triggers the password stub, `START` plays the VN stub.
- `SELECT` applies one Growth NanoCell to the prototype player (debug) and prints the new growth tier and visual variant.

Next steps

- Replace placeholder assets with tile sheets and palettes, add tools/ tile conversion scripts, and iterate on gameplay code in `src/`.
- Tighten the Windows controller lane further by moving from the Python host toward a native C or SDL Windows shell only after the controller-first gameplay loop is locked.
