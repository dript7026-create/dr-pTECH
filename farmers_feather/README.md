# Armored Gear: Fly Slight

DMG Game Boy prototype built with GBDK-2020.

Armored Gear: Fly Slight reinterprets the original prototype as a compact outer-rim sortie game: a scavenger-built exoshell drifts through hostile void lanes, live-swaps salvaged weapon and armor modules, and fights through pressure spikes with sparse, icon-led feedback instead of text-heavy UI.

Aesthetic protocol:

- Wire-Punk / Scavenger-Chic silhouettes with androgynous modular exoshell reads
- Pseudo-aperegressed iconography: salvage halos, cable spines, relay glyphs, shrine circuitry, and wreck-tech debris motifs
- Minimal HUD and text so state changes read first through sprite posture, module recompilation, projectile rhythm, and a small set of DMG-safe icons

This slice uses a large streamed overworld instead of a fixed single screen. The world is generated from a deterministic seed and scrolled seamlessly by rewriting incoming background rows and columns as the camera moves.

Current slice:

- Top-down exploration across a procedural orbital disc with a calmer inner lane and a hostile outer-rim pressure band
- Chunk-aware streaming terrain generation over a much larger coordinate space than a single hardware background map
- Launch tutorial opener: wreck-start platform, salvaged weapon and shell pickups, guided combat, and a first live module-shift beat
- Visible ranged combat with DMG-safe projectile sprites and persistent weapon and armor module ranks
- Relay docks, shrine reseed gates, MoonFeather routing, and a minimal icon-led HUD
- Wire-Punk / Scavenger-Chic presentation translated into angular DMG silhouettes, salvage glyphs, and module-reactive sprite recompilation
- Adaptive runtime visuals and combat pressure driven through PxGBPROG, PROGHONORAI, and HONORSPHERE instead of collapsing those systems back into the main loop
- Boss phases now hold until the Daemon of Famine is resolved, clear out roaming kin on arrival, and reward victory with healing, grain, MoonFeathers, and level progression
- First-pass DMG audio is wired into the ROM: title, field, outer rim, settlement, shrine, boss, and victory music cues plus title, traversal, farming, healing, autosave, spawn, and combat SFX
- Hidden shrine reseed mechanic
- Battery-backed SRAM profile slots
- ScanTide-derived scalar, coherence, geography, dominion, rest, race, and relative3 logic ported into integer gameplay systems

Controls:

- Title screen: any D-pad direction cycles slots, `A` scraps the selected slot, `Start` begins
- D-pad: drift / move
- B: fire the active ranged module
- A: cycle weapon or shell modules in real time; at docks and shrines it also triggers relay, heal, or reseed interactions
- Start: begin from title screen
- The HUD stays minimal: health, pressure, current module ranks, a combat pulse, and objective icons

Saving:

- Profiles persist in cartridge SRAM when built with the included battery-backed cart flags
- The game auto-saves the selected profile after meaningful state changes

Review assets:

- Graphics review package: `python .\tools\build_graphics_review_package.py`
- Output book: `review_package/ArmoredGearFlySlight_graphics_review.ecbmps`
- Output ledger: `review_package/graphics_asset_ledger.json`
- Chibi-overhaul review package: `python .\tools\build_chibi_overhaul_review_package.py`
- Chibi-overhaul book: `review_package/chibi_overhaul/ArmoredGearFlySlight_chibi_overhaul_review.ecbmps`
- Chibi-overhaul summary: `review_package/chibi_overhaul/chibi_overhaul_summary.json`
- The current chibi-overhaul pass now pulls from medieval and gothic daemon folklore: cathedral grotesques, gargoyle guardian silhouettes, bestiary hybrids, vice relics, and explicit pixel-economy rules for denser 32x32 authoring
- Audio generation: `python .\tools\generate_audio_assets.py`
- Audio coverage: `audio/generated/AUDIO_COVERAGE.md`
- Generated audio manifest: `audio/generated/generated_manifest.json`
- The generated `.wav` files remain external review and pre-production reference assets; the ROM now uses a native DMG synthesis pass derived from the same cue coverage rather than streaming the WAVs directly
- Tutorial voice generation: `powershell -ExecutionPolicy Bypass -File .\tools\generate_tutorial_voice_assets.ps1`
- Tutorial voice map: `audio/tutorial_voice/character_voice_map.json`
- Tutorial dialogue script: `audio/tutorial_voice/dialogue_script.json`
- Tutorial voice coverage: `audio/generated/tutorial_voice/TUTORIAL_VOICE_COVERAGE.md`
- Spoken tutorial dialogue is generated as an external companion pack for Windows playtests; the DMG ROM itself uses icon-led guidance plus native music and SFX rather than streaming speech
- The chibi-overhaul package is authored at 32x32 for art direction and layering, then intended to slice down to DMG-safe 8x8 and 8x16 runtime chunks later

Build:

```powershell
.\build.ps1
```

The build now autosizes ROM banks with GBDK so the runtime module stack can exceed the original 32 KB default while keeping the SRAM-backed cartridge target.

Runtime module stack:

- `modules/PxGBPROG/`: C-native pixel-program manifests for DMG sprite variant compilation.
- `modules/PROGHONORAI/`: passage-channel routing logic for adaptive combat behavior.
- `modules/PROGHONORAI/submodules/HONORSPHERE/`: the honor router that scores each passage channel before game-side translation.

Armored Gear: Fly Slight bridges these standalone modules through `src/passage_modules.c` so spawn pressure, windup/lunge timing, and sprite accents can adapt without collapsing the module boundaries back into `src/main.c`.

The current live render path is now end-to-end inside the modules: player input and game state feed `PROGHONORAI`, `HONORSPHERE` scores the active passage channel, and `PxGBPROG` converts that directive into a vector-scene simulation that is rasterized pixel-by-pixel back into DMG sprite tiles.