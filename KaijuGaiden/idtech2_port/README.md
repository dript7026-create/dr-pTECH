KaijuGaiden idtech2 port

This folder contains scaffolding to integrate KaijuGaiden placeholder assets into an id Tech 2 (Quake II) based mod or a standalone prototype for Windows, and tools to convert assets for Game Boy Advance (devkitPro).

Components:
- sprite_renderer.c/h: Minimal C sprite-sheet loader + renderer using SDL2 + libpng. Intended as a drop-in helper for prototyping and as a reference for porting into an idtech2 renderer/mod.
- CMakeLists.txt: Build file for Windows prototype using SDL2 and libpng.
- tools/convert_to_gba.py: Python script that converts PNG sprite-sheets (single row = frames) into GBA-compatible tile arrays and palette data and emits .h/.c for devkitPro projects.

Notes:
- This is scaffolding. Integrating into ioquake2/Yamagi requires creating a Quake II mod (a pk3) and wiring these rendering calls into the appropriate client or mod code.
- For a GBA build, use devkitPro and the provided Makefile at the repo root. The converter outputs header data that can be included in a libgba-based project.

Next steps:
- Review `sprite_renderer.c` and build with SDL2+libpng on Windows (CMake). Update as needed for your chosen idtech2 target.
- Run `python tools/convert_to_gba.py --src ../assets/placeholderassets --out build/gba` to generate tile/palette headers.

