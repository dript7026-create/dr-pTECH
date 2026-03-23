# Bango Engine Target

This module is the dedicated Bango-Patoot engine target layer.

It is derived from the external DoENGINE lineage discovered on `D:\doengine-backup` and `D:\Documents\god-ai\workspace\krabkombat\doengine`, then adapted for:

- Bango-Patoot gameplay hooks,
- true idTech2-facing game-module integration,
- new 3DS runtime support,
- Windows runtime support,
- controller support that lives in the engine target itself,
- explicit opt-in local telemetry bridges for camera and microphone style inputs.

Design constraints:

- Telemetry is local-only and opt-in.
- Sensor data is exposed as normalized samples; platform-specific capture remains outside this core layer.
- The module preserves a 3DS-first control path with touch and stereoscopic hooks.
- The same control schema is mirrored into Windows and idTech2-facing code.

Build integration:

- 3DS: compiled via `Makefile` (SOURCES includes `bango_engine_target/src`).
- Windows: compiled via `build_windows_preview.ps1`.
- idTech2: compiled via CMake in `idtech2_mod/CMakeLists.txt` against real Quake II SDK headers.
- All platforms: `.tools/bin/build-all-platforms.ps1` orchestrates every target in one pass.

Files:

- `include/bango_engine_target.h` — platform abstraction, input frames, DoENGINE bridge state.
- `include/bango_telemetry_bridge.h` — opt-in camera/mic telemetry sampling API.
- `src/bango_engine_target.c` — core implementation.
- `src/bango_telemetry_bridge_stub.c` — stub implementation returning safe defaults.
