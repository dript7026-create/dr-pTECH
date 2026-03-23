# Kaiju Gaiden — Detailed GDD Draft

## 1. Executive Summary

Kaiju Gaiden (gb.A.D.V.N.C) is a boss‑focused, 2D kaiju action game designed for an authentic GBA ROM prototype and planned ports to Switch 1, Switch 2, and Windows. Gameplay centers on staged, large‑scale boss encounters across expansive, scrolling landscapes with layered parallax and foreground elements. Each fight includes minions and culminates in a genomic cipher drop that affects the world state.

Scope for prototype: single stage plus Boss encounter, placeholder art/sfx, deployable as a .gba using devkitPro. Networking and multiplayer design specified but implemented later.

## 2. Core Gameplay Loop

- Enter stage (large, scrollable arena with parallax layers).
- Opening ritual: "3‑2‑1 Duel!" countdown between Rei and Boss.
- Minions spawn in waves with distinct behaviors; they drop Growth NanoCells when defeated.
- Engage Boss: multi‑phase patterns tied to its ecosystem and genome.
- Boss defeat yields an Environmental Genetic Cypher; player can apply the cypher to heal that ecosystem or convert it for mutations.
- Progression: collect cyphers to restore biomes, unlock Visual Novel chapters, and open new boss stages.

## 3. Controls & Input (GBA baseline)

- D‑Pad: Move Rei (8‑directional movement across a large stage with inertia/weight).
- A: Primary attack (combo chain)
- B: Secondary attack / dodge
- L / R: Nanoshift (short teleport/phase) — limited charge meter
- Start: Pause / Menu
- Select: Quick‑use Growth NanoCell (consumable enhancement)

Design notes: On Switch and Windows, map to standard controller (left stick/dpad, face buttons, bumpers).

## 4. Screen & Camera

- Resolution (GBA): 240×160. Camera centers on Rei with bounded panning across a much larger tilemap.
- Parallax: 3 background layers + 1 foreground layer for depth; foreground can occlude sprites for cinematic effect.
- Bosses may occupy multiple screen columns/rows; camera behaviour adapts (smooth tracking with cinematic shake during special attacks).

## 5. Boss Design Template (per boss)

- Name & Ecosystem: (e.g., "Harbor Leviathan" — harbor/reef)
- Visual motif & silhouette
- Phases: 3 primary phases (HP thresholds at ~66% and ~33% trigger new behaviors)
- Unique mechanics: environmental hazard tied to ecosystem (e.g., tidal pull, coral spires, ash gusts)
- Minion pool: 2–4 minion types that support the boss and reflect eco theme
- Drops: Environmental Genetic Cypher (detailed encoding) + optional rare mutation fragment
- Contextual cypher effect: explicit mapping to in‑game biome healing or mutation options

## 6. Minions & Growth NanoCells

- Minion archetypes: Swarmers (fast, low HP), Brutes (slow, shielded), Harassers (ranged spit), Swarm‑Splicers (summon bursts)
- Growth NanoCells: dropped by minions, act as temporary power charges (short buffs) or fuel for risky Nanoshift mutations. Using Growth NanoCells increases mutation meter and may cause persistent changes.

## 7. Drops, Cyphers & Progression

- Environmental Genetic Cyphers: boss drops are biome‑specific. Applying a cypher to a node triggers a world change (visual + gameplay) and unlocks VN content.
- Player choices: Purify (heal biome; stable long‑term benefits) vs. Recode (convert cypher to mutation; immediate combat advantages, narrative consequences).
- Password system: short alphanumeric passwords store stage progress and acquired cyphers for GBA builds.

## 8. Visual Novel / Motion Comic

- Non‑interactive motion‑comic with selectable playback speed and jump points aligned to saved progress.
- Panels animated with parallax, voice stingers, and short loops. Unlock order depends on cleared bosses and applied cyphers.

## 9. Multiplayer

- GBA (Link‑Cable): peer‑to‑peer link for Vs. Mode (head‑to‑head) and Arcade Tournament via round‑robin. Synchronize minimal state (player positions, attacks, RNG seeds) to keep bandwidth low.
- Switch 1 / Switch 2 / Windows: support system‑link (local LAN) and internet peer‑to‑peer. Lobby discovery handled by platform services or direct IP for Windows. Use rollback‑style or input‑synced netcode for low lag on fighting interactions.

Network design decisions (prototype): document protocols and later implement platform‑specific layers. For GBA, prioritize deterministic simulation with sync frames; for Switch/Windows, use input sync with frame delay compensation.

## 10. UI / HUD

- HUD shows HP, mutation meter, Nanoshift charges, Growth NanoCell count, mini‑radar of boss phase markers, and a contextual action prompt for cypher application.
- Title/menu flow as in lore file: drIpTECH splash → by a fanzovNG → Title Menu.

## 11. Art & Audio Direction

- Art: limited palette with bold silhouettes; large boss sprites composed from multiple hardware sprites (for GBA size constraints). Foreground occlusion for spectacle.
- Audio: short chiptune loops (4–8 bars) per stage; per‑boss leitmotifs; limited sfx budget (GBA: small sample set, prioritized attack and impact cues).

## 12. Technical Constraints (GBA prototype)

- Resolution: 240×160.
- Sprite limits: hardware limit (max 128 sprites, 64 per scanline considerations). Use compositing where necessary; break boss into multi‑sprite chunks.
- Tile map: use tile banks and streaming for large levels; reuse tilesets across stages to save space.
- Audio: use ADPCM or short samples and channel mixing; keep music loops small.

## 13. Build & Toolchain

- DevkitPro for GBA ROM building; C + libgba baseline. Use Makefile + example project structure. Include placeholder assets to iterate.
- Switch builds: plan for Unity or native libs later; not part of prototype build.

## 14. Prototype Scope & Milestones

Milestone 1: Single stage + boss prototype (core loop, minions, 3‑2‑1 Duel, boss phases, cypher drop)
Milestone 2: Password save implementation + title/menu + Visual Novel stub
Milestone 3: Multiplayer design doc and basic net sync tests (non‑GBA)

## 15. Next Steps

- Create placeholder sprites and a single boss sprite sheet.
- Implement a simple GBA camera that pans across a larger tilemap.
- Implement boss phase system and minion spawn manager.
- Add password save and title/menu sequence.

## 16. Boss Templates, Attack Patterns & Example Entries

Each boss entry should be created from this template to ensure consistency across design and implementation.

- ID / Name: unique identifier and display name.
- Ecosystem: the biome the boss is tied to (harbor, reef, ash plateau, mangrove lattice, etc.).
- Visuals: silhouette, dominant palette, notable foreground/occluding parts.
- Size / Sprite Layout: width×height in pixels; number of 8×8 tiles required; recommended sprite chunking.
- HP & Phase Thresholds: total HP and values at which phases change (default: phase2 @66%, phase3 @33%).
- Phase Behaviors: list of attack patterns and environmental triggers per phase.
- Unique Mechanics: special mechanics tied to genome (e.g., reef spires that grow and block sections, ash gusts that reduce visibility).
- Minion Pool: list of minion types, spawn schedule, and interactions.
- Drops: Environmental Genetic Cypher description + rarity table.
- Reward / Cypher Effect: explicit mapping of cypher application outcomes.

Example: Harbor Leviathan
- Ecosystem: Harbor / Reef
- Size: 192×128 pixels (24×16 tiles). Sprite layout: 6×4 chunks (use 48 sprites at 32×32 chunking where possible).
- Phases:
  - Phase 1 (100–66%): tail sweep + harpoon spit from the reef mouth; spawns Swarmers.
  - Phase 2 (65–33%): reef spires erupt; area traps appear; periodic tidal pull that drags player toward boss.
  - Phase 3 (32–0%): enraged roar — spawns barrage of homing spores; increases movement speed and reduces attack windup.
- Unique mechanic: reef spires provide cover for minions and can be purified using cypher fragments to change battlefield topology.
- Drops: Harbor Cypher — can be applied to coastal nodes to restore reef biodiversity (clears venomous growth and spawns new fishlife that grants passive regen to nearby areas).

### Genetic Growth System (Design)

Growth NanoCells should interact with entity genomes to create meaningful, persistent change. Each entity has a `genome_id` and a growth meter. Growth tiers unlocked by consuming Growth NanoCells modify:
- Movesets (add/alter attacks)
- Visual variants (palette/sprite augmentation)
- Passive traits (regen, resistances)

Implementation notes: compact genome tables, palette swaps for visuals, parameterized attack data for movesets. Prototype will include debug hooks to apply Growth NanoCells to the player and print resulting variant and tier.


## 17. Enemy Tables

Structure: enemy entries should contain the following fields:
- ID / Name
- Archetype (Swarm, Brute, Harasser, Splicer)
- HP, Speed, Damage
- Behavior (patrol, seek, ranged, kamikaze)
- Growth NanoCell drop chance

Example enemy table (CSV style):
ID,Archetype,HP,Speed,Damage,Behavior,DropChance
SWRM01,Swarm,10,High,2,DirectCharge,0.35
BRTE01,Brute,40,Low,6,ShieldedMelee,0.15
HRSS01,Harasser,18,Med,3,RangedSpit,0.25
SPLC01,Splicer,22,Med,1,SummonBurst,0.20

## 18. Attack Pattern Definitions

Patterns should be modular and composed of primitives:
- Telegraphed Strike: windup animation → telegraph line → strike area.
- Sweeping Arc: angle, radius, sweep duration.
- Projectile Burst: count, spread, speed, homing factor.
- Environmental Spawn: spawn type, location, interval.

Example Harbor Leviathan attack (Phase 2):
- Reef Spire Eruption: every 6–10s spawn a spire at randomized points along the arena edge. Spire persists 8s and creates blocked tiles; stepping on tiles applies slow.

## 19. GBA Sprite / Tile / Audio Budget Guidelines

Design emphasis: keep within GBA hardware constraints while maintaining cinematic scale.

- Sprites (OBJs): 128 total hardware sprites available. Practical limits: avoid exceeding 64 simultaneous sprite chunks during boss spectacle to prevent flicker.
- Per-scanline limit: 32 sprites per scanline (design to avoid stacking >32 on the same line).
- Sprite sizes: use 32×32 and 64×64 chunks for large bosses; break bosses into composited chunks to allow partial culling and parallax layering.
- Tiles: 8×8 tiles, 4bpp (16 colors) preferred for palette memory savings; use shared tilesets across stages to reduce ROM footprint.
- Backgrounds: use 3–4 parallax layers; reuse tiles where possible and stream zone data.
- Palette: GBA supports 15‑bit color; aim for limited palettes per stage (e.g., 4 palettes of 16 colors each) to stay memory efficient.
- Audio: constrain to short loops (4–8 bars) per stage, small ADPCM samples for key SFX. Prioritize music→impact→voice stinger order for asset budgeting.

## 20. Password Save Format (GBA)

- Use compact alphanumeric password (e.g., 12–16 chars) encoding:
  - Cleared stages bitfield
  - Collected cypher IDs (hashing to small indexes)
  - Player selected mutation state (small set)

Security: password is a deterministic encoding readable by the ROM; provide a desktop utility to encode/decode for editing and backups.

## 21. Visual Novel Unlock Mapping

- Each cleared boss unlocks a VN chapter tied to that ecosystem. Applying cyphers (purify vs recode) toggles 1–2 branching VN lines that change characters’ epilogues and minor scene variants.

## 22. Multiplayer Sync & Netcode Notes

- GBA Link‑Cable: deterministic simulation with frame ticks and rollover; keep messages minimal (input frames, minor state deltas). Consider lockstep with rollback not feasible on GBA.
- Switch/Windows: implement input‑sync with adjustable frame delay and optional rollback for better latency handling. Use UDP with reliable sequencing of input packets and prediction for client‑side responsiveness.

Network design decisions (prototype): document protocols and later implement platform‑specific layers. For GBA, prioritize deterministic simulation with sync frames; for Switch/Windows, use input sync with frame delay compensation.

## 23. Competitive Quality Targets & Timeline

User requested delivery: marketable deliverable by 2026‑03‑04 12:00 PM.
- Current system time: 2026‑03‑06 18:23:14 -05:00 — the requested deadline has passed. Please confirm a new target date/time. I will continue with the GDD now and then begin prototype implementation on your confirmation of schedule.

Minimum viable marketable deliverable (realistic):
- Content: 3 polished boss encounters, core combat tuned, menu/title, password saves, VN stub, local multiplayer support stub.
- Time estimate: ~2–4 weeks with an experienced small team for GBA‑grade polish; faster for minimal prototype but not a fully marketable product.

## 24. Implementation Notes & File Conventions

- Asset naming: boss_<id>_sheet.png, minion_<id>.png, bg_<stage>_layer<n>.png, sfx_<name>.wav, music_<stage>.mod.
- Code: C source under src/, hardware abstraction hw/, assets under assets/ with a conversion script for GBA tiles (include tools/convert_tiles.py placeholder).

-- End GDD Draft --
