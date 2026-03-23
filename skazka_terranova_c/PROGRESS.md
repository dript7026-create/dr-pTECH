SKAZKA: Terranova — Progress Note
Date: 2026-03-11

Status:
- Created C/SDL2 prototype scaffold: `CMakeLists.txt`, `src/main.c`, `src/game.h`, `src/game.c`, `README.md`.
- Tracked TODOs for core systems (navigation, tempo manager, media deck, controller support).

Next steps (short):
1. Implement Tempo Manager and one rhythm combat encounter (Leshy) in C.
2. Add Media Deck logic and sample rituals (3 recipes).
3. Integrate Xbox controller profiles and latency calibration.
4. Build asset pipeline (recraft vectors → multi-layered PNG/SVG + mask/gradient data) and wire into renderer.
5. Prototype AS3/SWF export path (evaluate Haxe, Apache Flex, or Adobe tooling) and Ruffle test harness.

Environment checklist (to verify): CMake, C compiler (MSVC/MinGW/clang), SDL2 dev libs, Emscripten or Haxe/Flex SDK, Python, Node, Ruffle runtime.

Notes on goals and constraints:
- Targeting `.swf` as final output is feasible via AS3 toolchains (Haxe/Flex) but will require adaptation; direct C→AS3 translation is manual or via higher-level asset/logic export.
- Browser-embedded proprietary `.farim` format and absolute anti-reverse-engineering guarantees are unrealistic; recommend packaging/encryption, server-side verification, and legal protections instead. We'll design for obfuscation and authenticated assets.

Saved by: GitHub Copilot agent
