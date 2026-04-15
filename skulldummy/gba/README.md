# SkullDummy GBA Prototype

This folder contains a first-pass Game Boy Advance demake of the current SkullDummy encounter slice from the Android build.

Current prototype scope:

- adapted original Android art for Blunin, the skull plain background, and the relic icon
- denser Blunin animation sampling across idle, walk, and attack states
- more distinct per-zone backdrop treatment from the original layered art
- three-zone encounter loop
- Blunin boss mode cycling
- timed QTE windows mapped to GBA controls
- relic charge and relic burst
- recurring two-channel PSG leitmotif with event stings for prompts, hits, relic use, and resolve states
- player and boss health bars
- win, loss, and restart flow

Controls:

- D-pad: answer directional prompts
- A: answer `A` prompts / restart after resolve
- B: answer `B` prompts
- L: relic burst when the gauge is charged
- Start: restart encounter
- Select: advance zone manually

Build from PowerShell:

```powershell
cd skulldummy\gba
.\build.ps1
```

The ROM output is `skulldummy_gba.gba` by default.

Launch in an emulator:

```powershell
cd skulldummy\gba
.\launch.ps1
```

Notes:

- defaults to `%USERPROFILE%\Documents\visualboyadvance\visualboyadvance-m.exe` if present
- pass `-Build` to rebuild before launching
- override with `-EmulatorPath` or the `GBA_EMULATOR` environment variable

Quick window capture:

```powershell
cd skulldummy\gba
.\capture_run.ps1 -DurationSeconds 45
```

This records the active emulator window to `skulldummy/gba/capture/skulldummy_session.avi` using `ffmpeg` and writes session logs alongside it.

If `gdigrab` cannot bind the emulator window title on your machine, the script automatically falls back to full-desktop capture for the requested duration.

Asset pipeline:

- source art comes from `skulldummy/android/app/src/main/res/drawable-nodpi`
- `tools/convert_assets.py` scales, crops, and quantizes the art into GBA BGR555 arrays
- generated outputs land in `build/gba_assets`
