TommyBeta

This project now has two runtime paths:

- `gb`: the older minimal Game Boy prototype built through GBDK.
- `gba`: the active top-down Game Boy Advance proof-of-concept built through devkitARM/libgba with generated Mode 3 art assets.

Current GBA runtime scope:

- title screen
- fall intro screen
- tutorial screen
- top-down real-time exploration and combat loop
- pause, win, and game-over states
- unlocked-special cycling and finisher-mask progression
- generated quadrant backgrounds, character sheets, props, critters, HUD, ambience, and combat FX

Build usage:

Windows PowerShell:
```powershell
cd tommybeta
.\build.ps1 -Target gba
```

Autoplay validation ROM:
```powershell
cd tommybeta
.\build.ps1 -Target gba-autoplay
```

Autoplay rebuild wrapper:
```powershell
cd tommybeta
.\build_autoplay.ps1
```

Legacy GB prototype:
```powershell
cd tommybeta
.\build.ps1 -Target gb
```

Important files:

- `src/gba_main.c`: active GBA runtime
- `build/gba_assets/tommybeta_mode3_assets.[ch]`: generated Mode 3 asset pack
- `tools/convert_mode3_assets.py`: PNG-to-C asset conversion
- `Makefile.gba`: GBA build entry
- `TOMMYBETA_GBA_PREPRODUCTION_BRIEF.txt`: project direction and combat design
- `TOMMYBETA_GBA_RUNTIME_ASSET_MANIFEST.txt`: generated asset inventory

Notes:

- The active GBA runtime now includes the generated asset header directly from `build/gba_assets`, which removes the editor warning about an unused forwarding include while keeping the generated asset API authoritative.
- The current GBA flow includes the fall-intro bitmap before tutorial or exploration when that asset is present.
- GBA builds now regenerate polished splash, title, intro, fall, victory, and defeat presentation screens from the shipped Recraft sheets before converting the full Mode 3 asset pack.

