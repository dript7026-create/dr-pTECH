# Kaiju Gaiden Consolidated GDD And Asset Manifest

## 1. Document Purpose

This document consolidates four previously split views of Kaiju Gaiden into one source of truth:

1. The broad GBA-era concept from the legacy design drafts.
2. The currently implemented gameplay truth in the live multi-target runtime.
3. The related modular GBA prototype codebase still present under `src/`.
4. The real asset inventory currently on disk, separated into active, legacy, and planned buckets.

The most important practical distinction is this:

- The active shipping gameplay runtime is `KaijuGaiden/kaijugaiden.c`.
- The related older modular GBA prototype remains under `KaijuGaiden/src/`.
- The current playable experience is materially closer to a focused GB boss brawler than to the older large-scrolling GBA draft, even though the codebase still carries GBA and host targets.

## 2. Project Identity

### Title

Kaiju Gaiden

### Expanded Title String

Kaiju Gaiden - gb.A.D.V.N.C

### Tone

Melancholic retro kaiju action with mutation-horror, ecological consequence, ritual duel framing, and compact arcade readability.

### Core Fantasy

The player controls Rei Moro, an Altered being empowered by Vibrational NanoCells, fighting biome-linked kaiju and deciding whether each victory restores the world or pushes it further into mutation.

### Product Modes Across Design History

- Current live runtime: single-stage, single-boss, password-backed boss brawler.
- Legacy modular GBA prototype: title flow, menu flow, boss demo, password stub, VN stub, genetics scaffolding.
- Long-range concept: multi-stage campaign, biome restoration, branching VN, multiplayer versus, arcade tournament.

## 3. Current Canonical Runtime Truth

### Canonical Runtime File

`KaijuGaiden/kaijugaiden.c`

### Supported Targets In The Canonical Runtime

- `TARGET_GB`: current strongest gameplay implementation.
- `TARGET_GBA`: retained target path for the GBA build.
- `TARGET_HOST`: desktop validation, tuning, and QAIJockey playtesting path.
- FARIM packaging path: built from host output after runtime build.

### Current Gameplay Scope Actually Implemented

- Splash screen.
- Intro cinematic.
- Title menu.
- Password entry and restore flow.
- Stage intro.
- One Harbor Shore encounter.
- Wave-gated minion combat.
- One boss, Harbor Leviathan.
- Three boss phases.
- Cypher reward sequence.
- Game over loop.

### Current Design Shape

The live game is not currently a fully scrolling exploration-heavy GBA action game. It is a highly compressed encounter-focused action loop with the following priorities:

- combat readability
- telegraphed boss and minion attacks
- short-run clarity
- DMG-safe presentation and budgets
- password continuity
- multi-target portability

## 4. High-Level GDD

### Genre

Boss-focused 2D kaiju action brawler with mutation-progression framing.

### Player Character

Rei Moro, a partially rewritten human whose body and memory are entangled with Vibrational NanoCells.

### Core Loop

1. Enter the ritualized encounter.
2. Clear minion waves to unlock the boss state.
3. Read telegraphs and spacing cues.
4. Manage attack rhythm, dodge timing, and NanoCell usage.
5. Break the boss through three phases.
6. Claim an Environmental Genetic Cypher.
7. Store progress through password data.
8. Return to the menu and continue the larger restoration-versus-mutation frame.

### Long-Form World Loop Intended By The Broader Design

1. Fight a biome-tied boss.
2. Obtain a cypher representing that biome's broken genome.
3. Purify or repurpose the cypher.
4. Alter future world state, unlocks, and story texture.
5. Advance to the next ecosystem.

### Core Combat Pillars

- Readability before spectacle.
- Telegraph before damage.
- Tight hit-confirm windows over mash-heavy output.
- Small-state combat with clear feedback banners.
- Boss behavior driven by spacing, phase, and recovery logic.
- Temporary power spikes through NanoCells instead of a permanently inflated move list.

### Current Controls

Live runtime controls:

- D-Pad or mapped directional input: horizontal movement and encounter positioning.
- `A`: primary attack and combo chain.
- `B`: dodge and cinematic skip hold path.
- `Start`: pause and menu confirmation role in some flows.
- `Select`: consume a Growth NanoCell.

Legacy broader design controls retained in draft intent:

- `L` and `R` were previously reserved for Nanoshift or phase movement in the larger GBA concept.
- Multiplayer and VN-specific menu mappings remain conceptual and not fully implemented in the live runtime.

## 5. World And Fiction Design

### Setting

The Kurogane Archipelago, a scarred island chain where biotech repair systems have gone feral and begun rewriting ecosystems into colossal organisms.

### Fictional System

Vibrational NanoCells were intended to heal living environments, but their resonance became self-propagating and began restructuring biology at ecological scale.

### Current Narrative Function Of Bosses

Bosses are not only enemies. They are living ecological failures with encoded restoration value. Defeating them yields a genome fragment that can become either healing infrastructure or mutation leverage.

### Current Narrative Function Of Minions

Minions are lesser infection byproducts and resource feeders. Mechanically they serve three roles:

- pacing gate before boss readiness
- NanoCell economy source
- close-range pressure that forces position checks before the boss duel begins in earnest

### Current Named Implemented Biome And Boss

- Stage: Harbor Shore
- Boss: Harbor Leviathan
- Reward: Harbor Cypher

### Planned World Expansion Suggested By Existing Drafts

- harbor / reef biome
- ash plateau biome
- mangrove lattice biome
- additional mutation/restoration branches
- VN unlock chapters keyed to boss clears and cypher outcomes

## 6. Encounter Design

### Harbor Shore Encounter Structure

1. Stage intro frame establishes location and duel context.
2. Player clears three minion waves.
3. Boss awakens.
4. Boss cycles through three health-gated phases.
5. Boss death triggers reward state.
6. Cypher drop completes the run.

### Harbor Leviathan Phase Design

The current runtime implements a three-phase boss with phase-specific attack presentation and spacing checks.

Phase values:

- Phase 1 HP: `12`
- Phase 2 HP: `10`
- Phase 3 HP: `8`

Attack families defined in code:

- `BOSS_ATK_SWEEP`
- `BOSS_ATK_SPIT`
- `BOSS_ATK_SLAM`
- `BOSS_ATK_TIDAL`

Range tuning defined in code:

- sweep range: `32`
- spit range: `88`
- slam range: `26`

### Minion Design

Current live minion rules are intentionally compact:

- maximum on screen: `5`
- minion HP: `2`
- attack range: `18`
- windup frames: `14`
- recover frames: `20`

Minions are currently implemented as a lightweight wave-gate pressure system rather than a full archetype roster, even though the older GDD imagined multiple minion classes.

### Current Combat Reward Model

- Minions drop Growth NanoCells.
- NanoCells can be consumed for a temporary power-up.
- Boss defeat grants a cypher and updates progression state.

## 7. Current Progression Model

### Persistent State Variables

The live runtime tracks long-term progress through two bitfields:

- `cleared_bosses`
- `cyphers`

### Password Format

- fixed encoded length: `16` characters
- encoded values: cleared boss bitmask plus cypher bitmask

### Current Reward Types

- `Growth NanoCells`: temporary combat enhancement resource
- `Environmental Genetic Cypher`: long-form progression and world-state token

### Current NanoCell Tuning

- maximum held: `9`
- boost duration: `90` frames

## 8. UX And Presentation Design

### Live Game Phase Flow

The active phase machine uses these constants:

- `PHASE_SPLASH`
- `PHASE_CINEMATIC`
- `PHASE_TITLE`
- `PHASE_STAGE_INTRO`
- `PHASE_COMBAT`
- `PHASE_BOSS_DEATH`
- `PHASE_CYPHER_DROP`
- `PHASE_GAME_OVER`
- `PHASE_PASSWORD`

### Combat Feedback Devices

The active runtime uses a short-lived banner system to make combat state visible without a verbose HUD.

Banner states:

- `BANNER_NONE`
- `BANNER_WAVE_CLEAR`
- `BANNER_BOSS_RISE`
- `BANNER_DODGE`
- `BANNER_PERFECT`
- `BANNER_FINISHER`
- `BANNER_BOSS_STUN`

### Camera Design

The live runtime no longer behaves like a large camera-scroll GBA prototype. It now uses micro-camera biasing for legibility:

- travel lead
- combat lead
- telegraph lead
- bounded shake
- bounded background offset

Current camera tuning constants:

- travel lead: `3`
- combat lead: `3`
- telegraph lead: `4`
- max x offset: `7`
- max y offset: `3`

### HUD Model

Current HUD surfaces:

- player HP segments
- boss HP bar
- NanoCell count
- contextual banners

## 9. Live Code-Level Runtime Architecture

### Architectural Summary

The active runtime is a monolithic single-file game implementation built around a platform shim layer, a shared game state struct, phase-specific update routines, and a tile/sprite-driven presentation path.

Primary architectural layers:

1. target detection and platform shims
2. asset embedding and tile loading
3. background and HUD draw helpers
4. combat systems and camera/input helpers
5. phase initializers and phase update routines
6. target-specific main loop behavior

### Core Shared Runtime Structure

The central live state container is `GameState` in `kaijugaiden.c`.

Key state groups:

- player combat state
- beat-timing state
- boss state
- minion array state
- stage phase state
- title/password state
- cinematic state
- reward/progression state
- FX state
- camera state
- input telemetry state

### Important `GameState` Fields

Player and combat:

- attack combo timing
- dodge state
- NanoCell count and boost timer
- facing and movement state

Beat system:

- `beat_timer`
- `beat_perfect`
- `perfect_flash_timer`

Boss block:

- `boss_awake`
- `boss_phase`
- `boss_hp`
- `boss_x`
- `boss_anim`
- `boss_atk_timer`
- `boss_atk_type`
- `boss_windup`
- `boss_recover`
- `boss_stun`

Minion block:

- `active`
- `x`
- `y`
- `hp`
- `anim`
- `attack_windup`
- `attack_recover`
- `vx`

Flow and persistence:

- `phase`
- `phase_timer`
- `wave`
- `wave_timer`
- `menu_sel`
- `password_buf`
- `password_index`
- `cleared_bosses`
- `cyphers`

FX and camera:

- `fx_hit_*`
- `fx_nano_*`
- `banner_timer`
- `banner_kind`
- `camera_x`
- `camera_y`
- `camera_travel_bias`
- `camera_bg_x`
- `camera_bg_y`
- `camera_shake_timer`
- `camera_shake_mag`

Input tracking:

- `input_held_mask`
- `input_pressed_mask`
- `input_edge_total`
- `input_active_frames`

## 10. Live Runtime Function Surface

### Platform And Rendering Functions

- `plat_poll_input`
- `plat_vsync`
- `plat_set_bkg_tile`
- `plat_set_sprite`
- `plat_load_bkg_tiles`
- `plat_load_sprite_tiles`
- `plat_delay_frames`
- `host_render_tile`
- `host_render_frame`
- `host_clear_sprites`
- `host_init`

These functions isolate target-specific IO, rendering, and input handling from gameplay logic.

### Asset And Background Functions

- `game_load_tiles`
- `bg_fill`
- `bg_char_to_tile`
- `bg_draw_text`
- `bg_draw_beach_rows`
- `bg_draw_beach`
- `bg_draw_beach_water_only`
- `bg_draw_splash`
- `bg_draw_title`
- `bg_draw_number_2`
- `bg_clear_row`

These functions establish tile memory, stage composition, splash/title presentation, and HUD text behavior.

### Password And Progression Functions

- `password_hex_to_nibble`
- `password_encode`
- `password_decode`

These are the actual live persistence interface for the current build.

### Combat And Utility Functions

- `combat_minions_alive`
- `attack_hits_target`
- `abs_distance_u8`
- `combat_set_banner`
- `input_capture_frame`
- `camera_reset`
- `camera_punch`
- `combat_camera_update`
- `boss_attack_windup_frames`
- `boss_attack_recover_frames`
- `boss_current_range`
- `boss_pick_attack`

These functions define the encounter readability layer, the combat decision rules, and the player-feedback layer.

### HUD And Sprite Composition Functions

- `hud_draw`
- `spr_draw_rei`
- `spr_draw_boss`
- `spr_draw_minions`
- `spr_draw_fx`
- `spr_draw_cinematic`
- `spr_hide_all`

These map runtime state into visible object composition.

### Flow-State Initializers And Updaters

- `splash_init` / `splash_update`
- `cinematic_init` / `cinematic_update`
- `title_init` / `title_update`
- `password_draw`
- `password_init` / `password_update`
- `stage_intro_init` / `stage_intro_update`
- `minion_spawn_wave`
- `minion_update_all`
- `player_attack_minions`
- `boss_init`
- `boss_take_damage`
- `boss_update`
- `combat_init` / `combat_update`
- `cypher_init` / `cypher_update`
- `gameover_init` / `gameover_update`

This is the most useful implementation map for future work. Each pair or cluster corresponds to a discrete gameplay responsibility.

## 11. Related Modular GBA Prototype Codebase

### Purpose Of `src/`

The `src/` tree preserves an older modularized GBA prototype architecture. It is still relevant as related code, but it is no longer the clearest expression of the current gameplay truth.

### Key Files

- `main.c`: GBA entrypoint and title/menu bootstrap.
- `game.c` / `game.h`: title sequence, menu, password handler, boss demo entrypoints.
- `state.c` / `state.h`: basic boss-clear and cypher bitfield tracking.
- `password.c` / `password.h`: password encoding and decoding layer.
- `genetics.c` / `genetics.h`: entity mutation, vibration, and NanoCell logic scaffold.
- `boss.c` / `boss.h`: boss fight demo scaffold.
- `boss_manager.c`, `minion.c`, `sprites.c`, `ui.c`, `vn.c`, `audio.c`: modular systems planned for a fuller GBA build.
- `gba_assets_loader.c`: asset ingest path for the modular build.
- `host_gba.c`, `xinput_wrapper.c`: testing and wrapper support.

### Important Structures In The Modular Prototype

`state.h` defines a minimal long-term state model:

- `cleared_bosses`
- `collected_cyphers`

`genetics.h` defines a broader mutation-oriented `Entity` structure with:

- `genome_id`
- `growth_tier`
- `variant`
- `vib_signature`
- `hp`
- `max_hp`
- `regen_rate`
- pending NanoCell amount, polarity, and timer
- `visual_cue`

### Important Functions In The Modular Prototype

From headers currently present:

- `game_main_menu`
- `game_title_sequence`
- `game_handle_password`
- `game_boss_demo`
- `state_set_cleared`
- `state_is_cleared`
- `state_add_cypher`
- `state_has_cypher`
- `encode_password`
- `decode_password`
- `apply_growth_nano`
- `apply_vibrational_affectation`
- `compute_mutational_shift`
- `deposit_nanocells`
- `genetics_tick`
- `genetics_check_combo_unlocks`
- `get_variant_name`
- `boss_fight_demo`

### Recommended Interpretation Of `src/`

Treat `src/` as a concept reservoir and modular prototype branch, not as the primary gameplay spec. The live runtime in `kaijugaiden.c` is the authoritative gameplay source.

## 12. Consolidated Asset Manifest

### Asset Manifest Categories

This manifest separates assets into three practical buckets:

- Active runtime assets: directly referenced by the live canonical runtime.
- Legacy or prototype assets: older headers and scaffolds still present in the repository.
- Planned or implied assets: documented in design and comments but not yet realized as complete production content.

### A. Active Runtime Assets

#### Background And HUD Tiles

- `assets/gb/bg_tiles_generated.h`
  - beach ground left/right
  - water A/B animation
  - cliff A/B
  - sky A/B
  - drIpTECH splash tiles
  - title logo tiles

- `assets/gb/hud_tiles_generated.h`
  - player HP segment tile
  - boss HP bar tile set

#### Player Sprite Assets

- `assets/gb/spr_rei_generated.h`
  - Rei idle frame set
  - Rei run frame set
  - Rei attack frame set

#### Boss Sprite Assets

- `assets/gb/spr_boss_generated.h`
  - Harbor Leviathan phase 1 tiles
  - Harbor Leviathan phase 2 tiles
  - Harbor Leviathan phase 3 tiles

#### Minion And FX Assets

- `assets/gb/spr_minion_generated.h`
  - live minion sprite tiles

- `assets/gb/spr_fx_generated.h`
  - hit spark tiles
  - NanoCell orb tiles

#### Cinematic Assets

- `assets/gb/spr_cinematic_generated.h`
  - intro cinematic kaiju A tiles
  - intro cinematic kaiju B tiles

### B. Active Runtime Tile And Sprite Slot Allocation

Background tile slots:

- `TILE_BLANK`
- `TILE_GROUND_L`
- `TILE_GROUND_R`
- `TILE_WATER_A`
- `TILE_WATER_B`
- `TILE_CLIFF_A`
- `TILE_CLIFF_B`
- `TILE_SKY_A`
- `TILE_SKY_B`
- `TILE_SPLASH1` through `TILE_SPLASH_END`
- `TILE_TITLE_A` through `TILE_TITLE_END`
- `TILE_HP_SEG`
- `TILE_BOSS_SEG`
- `TILE_FONT_0`
- `TILE_FONT_A`

Sprite tile slots:

- `SPR_REI_IDLE`
- `SPR_REI_RUN`
- `SPR_REI_ATTACK`
- `SPR_BOSS_A`
- `SPR_BOSS_B`
- `SPR_BOSS_C`
- `SPR_MINION`
- `SPR_FX_HIT`
- `SPR_FX_NANO`
- `SPR_CINEMATIC_A`
- `SPR_CINEMATIC_B`

Live runtime budgets currently documented by code and verification:

- background tile count: `68`
- sprite tile span used: `74 / 128`
- sprite slots reserved peak: `38 / 40`

### C. Legacy / Prototype Asset Headers

Top-level `assets/` headers preserved from earlier prototype passes:

- `rei_assets.h`
- `boss_assets.h`
- `minion1_assets.h`
- `minion2_assets.h`
- `minion3_assets.h`
- `nanocell1_assets.h`
- `nanocell2_assets.h`
- `attackfx1_assets.h`
- `attackfx2_assets.h`
- `blodfx1_assets.h`
- `menunewgame_assets.h`
- `titlescreen_assets.h`
- `placeholder_assets.h`

These should be treated as prototype or transitional assets unless they are explicitly remapped into the live runtime.

### D. Raw / Authoring Asset Folders

- `assets/placeholderassets/Audio`
- `assets/placeholderassets/Graphical`
- `assets/titlescreen/`

Current observed state:

- the `titlescreen` folder is currently empty
- placeholder authoring directories still exist as staging scaffolds

### E. Planned Asset Families Suggested By Design But Not Fully Realized

- additional bosses beyond Harbor Leviathan
- biome-unique background sets for ash plateau, mangrove, reef variants, and later zones
- more minion archetype sheets
- VN panel art and motion-comic layer assets
- multiplayer interface and tournament UI assets
- broader audio package for stages, bosses, reward states, and story scenes

## 13. Build And Artifact Manifest

### Current Important Runtime Artifacts

- `kaijugaiden.gb`
- `kaijugaiden.gba`
- `kaijugaiden.elf`
- `dist/kaijugaiden.gb`
- `dist/kaijugaiden.gba`
- `dist/kaijugaiden_host.exe`

### Runtime Support And Playtest Files

- `run_qaijockey.py`
- `qaijockey/`
- `tools/verify_input_contract.py`
- `tools/verify_dmg_constraints.py`

### Prototype Documentation Files Already In Repo

- `README_PROTOTYPE.md`
- `Kaiju_Gaiden_GDD_draft.md`
- `Kaiju_Gaiden_GDD_full.txt`
- `Kaiju_Gaiden_lore.txt`

## 14. Consolidated Design Direction Recommendation

### What Should Be Treated As Canonical Going Forward

Canonical truth should be defined in this order:

1. `kaijugaiden.c` live runtime behavior
2. this consolidated document
3. legacy design drafts
4. modular `src/` prototype files

### Recommended Production Direction

If Kaiju Gaiden continues from the current codebase, the cleanest approach is:

1. Keep `kaijugaiden.c` as the gameplay reference implementation while the combat loop is still being tuned.
2. Treat the GBA `src/` tree as a future extraction target, not as the authoritative spec.
3. Continue expanding content through additional bosses, biomes, and cypher consequences only after the Harbor Shore encounter is locked.
4. Maintain separate asset manifests for `active`, `legacy`, and `planned` content to avoid confusion.

## 15. Immediate Expansion Checklist

The highest-value next expansions suggested by the combined design and code are:

1. Add boss 2 with a second biome and second cypher.
2. Connect `cleared_bosses` and `cyphers` to real stage-unlock logic beyond the first harbor fight.
3. Formalize the NanoCell mutation branch currently represented only as temporary combat boost plus broader lore intent.
4. Decide whether the long-term architecture should remain monolithic or migrate the stabilized runtime back into `src/` modules.
5. Replace remaining legacy and placeholder asset headers with a single declared pipeline path.

## 16. Summary

Kaiju Gaiden currently exists as a strong, focused encounter prototype with a larger unrealized world design around it. The code already contains a coherent playable nucleus: Rei, Harbor Shore, Harbor Leviathan, Growth NanoCells, a cypher reward loop, and password persistence. The repo also still carries the skeleton of a larger GBA-first architecture and a much bigger campaign concept. This consolidated document should be used as the practical bridge between those two realities.