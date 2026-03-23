OrbSeeker — idtech2 (Quake II) mod skeleton

What this is
- A starting skeleton to port the OrbSeeker design into an idtech2 (Quake II) mod.
- It contains: a minimal `game` source stub (`orbseeker_game.c`), build notes, and packaging guidance.

Important notes
- This is a skeleton only — compiling and running requires a Quake II SDK/engine and toolchain (Visual Studio on Windows or gcc/MinGW). The `game` code for Quake II is native C and must be built into the engine's game DLL/so (e.g., `game.dll` on Windows or `game.so` on Linux) and placed into the `baseq2` folder or packaged into a PK3.
- Creating playable maps requires a Quake II map editor (e.g., TrenchBroom) and BSP compiler (q2map2). This repository does not include compiled BSP files.

Files added
- `game/orbseeker_game.c` — C stub with entity hooks, orb pickup logic, and island hub comments.
- `build_instructions.txt` — step-by-step instructions to build and package the mod.

Next steps you can ask me to do
- Flesh out the `orbseeker_game.c` with full Quake II API calls for spawning, linking, and save/load.
- Create sample maps (.map) suitable for q2map2, or provide a TrenchBroom-friendly map template.
- Help set up a Visual Studio solution or Makefile to compile the game DLL and test locally.

Quick build notes (summary)
1. Install Quake II engine (e.g., Yamagi Quake II on Windows) and Quake II dedicated SDK sources.
2. Place the `OrbSeeker` mod folder under your `baseq2` or `mods/` directory.
3. Compile the `game` code into `game.dll` (Windows) or `game.so` (Linux) following Quake II SDK build instructions.
4. Start the engine and run `map <mapname>` to test.

License
- You own the code created. This skeleton uses no external proprietary assets.
