Tommy Goomba — Build & Run

This folder contains Game Boy-target source and notes. The workspace also includes a Windows console C program at `../tommygoomba.c`.

Windows Console (canonical C source)
- File: `../tommygoomba.c`
- Notes: RNG seed is initialized at program start (seed fixed to call `srand()` before `rand()`), and the program uses `<conio.h>` (`_kbhit()`, `_getch()`), which is MSVC/MinGW specific.

Build (Windows, MinGW):
```powershell
# From workspace root
gcc -o tommygoomba.exe tommygoomba.c
.\tommygoomba.exe
```

If using MSVC/Visual Studio, create a new console project and add `tommygoomba.c`.

Game Boy (GBDK)
- File: `tommygoomba.gb` (C source using GBDK headers)
- Status: skeleton (input and state management present; rendering/sprites and assets not included).

Build (GBDK-2020 or compatible):
```bash
# Example (adjust per your GBDK install):
# from the tommygoomba/ directory
lcc -o tommygoomba.gb tommygoomba.gb
```

Notes and Recommendations
- Keep `tommygoomba.c` as the canonical desktop source. Remove or clearly rename any `.gb` files that are plain C source to avoid confusion (`.gb` normally denotes a ROM image).
- For the Game Boy target, add tiles, sprites, map data and complete the render loop; configure GBDK include paths.
- If you want, I can (a) apply a small rendering stub, (b) add build scripts, or (c) create a CI task to build binaries.

Build and assets
 - Generate placeholder assets (uses Pillow): run `python generate_assets.py` from the `tommygoomba` folder. This creates `tommygoomba/assets/` with PNG placeholders.
 - Convert PNGs to GBDK tile data: `python convert_assets.py assets\*.png > tiles.c`
 - Build (requires GBDK or gbdk-clang installed): example:
	 - `lcc -o tommygoomba.gb tommygoomba.c tiles.c -Wl,--oformat=gb`
	 - or `gbdk-clang -o tommygoomba.gb tommygoomba.c tiles.c`
 - There's a helper `build.ps1` that runs the generator + converter and prints compile commands.

AI-generated assets / credits
 - By default this repo includes locally-generated placeholder assets created using Pillow (no external API).
 - I can automate generation with an open-source image model (Stable Diffusion variants) or hosted APIs if you provide API credentials and consent. If a service requires credits/payment, I'll stop and ask before proceeding.
 - See `ASSET_CREDITS.md` for current credits/attribution.
