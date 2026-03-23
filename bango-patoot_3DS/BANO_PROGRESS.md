# Bango-Patoot 3DS Progress

Date: 2026-03-11

Direction locked for this branch:
- This project is now an original collectathon action-RPG for Nintendo 3DS, not a Banjo-Kazooie demake.
- Working duo: Bango and Patoot.
- Target shape: 3D hubworld-to-level structure, urban-underbelly horror exploration, stamina-based combat, apiary shrine progression, dense but open spaces, sprite-to-3D presentation, and EgoSphere-driven non-player-entity relationships.
- New tone lock: hybrid steam-punk/high-fantasy filtered through new-world urban legend, cult folklore, cryptozoological monstrosities, technological abominations, and religious blasphemy horror.

Requested feature translation into safe/original form:
- Merge the structural appeal of classic duo-platformer adventures into one original story arc.
- Keep major collectible, score collectible, and rescue-NPC loops.
- Add a full RPG attribute and skill-tree layer around those loops.
- Use a procedural move catalog system capable of scaling toward a 1000-move roster rather than hard-authoring 1000 unrelated moves.
- Use key-pose plus inbetweener planning as a runtime-ready animation concept rather than a baked offline-only feature.
- Keep the duo visually and behaviorally distinct from Banjo-Kazooie while preserving the broad two-character platformer/action-RPG appeal.

Current task set:
1. Rewrite the design brief and systems architecture around the Bango-Patoot horror direction.
2. Replace the empty C file with a compileable 3DS prototype skeleton.
3. Add devkitPro/libctru/citro2d/citro3d build files.
4. Attempt a local 3DS build.
5. Add a sprite rig and pose-import pipeline for future authored and generated animation content.

Completed in this pass:
- Added JSON skeletal rig definitions for Bango and Patoot in `rigs/entity_rigs.json`.
- Added transparent 4-angle T-pose source sheets in `assets/source_sheets/`.
- Added concept-loop GIFs in `assets/concept_loops/` to establish keypose feel before real authored animation playback exists.
- Added a single-pose import contract in `pose_imports/pose_import_template.json` and validated the registry-based import path into `pose_imports/imported_pose_registry.json`.
- Added a Recraft-facing manifest builder and generated `recraft/bango_patoot_recraft_manifest.json`.
- Updated the 3DS prototype to surface rig metadata and inbetweening parameters on the bottom-screen UI.
- Rebuilt successfully after the rig pipeline changes and confirmed the project still produces `BangoPatoot.3dsx`.
- Added `BANGO_PATOOT_FULL_GDD.md` and `BANGO_PATOOT_FULL_GDD.txt` as the complete narrative, system, and asset-bible handoff for the project's current design state.
- Recorded that the player intends to personally author later concept animation, T-pose, environment/object, and audio assets when returning to this project.

Open gaps after this pass:
- Imported pose data is registered on disk but not yet consumed by runtime animation playback.
- Inbetweening is currently metadata and planning structure, not a finished runtime animation system.
- Generated or imported sprite sheets are not yet loaded into Citro2D/Citro3D render assets.
- Combat actors, collision, and real move playback still need implementation beyond the current prototype UI/state loop.

Suggested next implementation order:
1. Parse the imported pose registry into runtime-friendly data.
2. Add texture loading and billboard/sprite hooks for rig-bound assets.
3. Wire a first real move animation to imported keyposes plus simple procedural inbetweening.
4. Expand the gameplay layer with enemies, hit detection, and collision.

All four open gaps above were resolved in the 2026-07-24 session — see checkpoint below.

Checkpoint saved: 2026-07-24 runtime systems implementation

Resolved all four previously documented open gaps:

1. **Spring-damper inbetweening system** — `update_character_rig()` replaced with physics-based bone animation: computes target bone positions from the active imported pose, applies spring force (stiffness × 120), velocity damping, and integrates position each frame. Smooth rotation lerp included. `CharacterRigState` struct extended with `target_bones[24]`, `bone_velocities[24]`, `inbetween_stiffness`, and `inbetween_damping` fields.

2. **Move-to-pose mapping** — Added `select_pose_for_move()` which maps a combat move to available imported poses via `(move->id + move->category) % pose_count`. `trigger_move()` updated to call this instead of hardcoded `poses[0]`.

3. **GPU texture upload for sprites** — Added `GpuSpriteSlot` struct and `g_gpu_sprites[48]` cache. `upload_sprite_to_gpu()` converts palette-indexed pixels to RGBA8 in Morton/Z-order tile format (8×8 tiles, power-of-2 texture dimensions), uploads via `C3D_TexInit` + `C3D_TexFlush`. `draw_runtime_sprite_frame()` now tries GPU textured quad (`C2D_DrawImageAt`) first, falls back to per-pixel software rendering if cache is full.

4. **Runtime pose-registry consumption** — Imported pose data from `bango_runtime_asset_pack.h` is now consumed at init (stiffness/damping copied from rig specs to rig states) and at runtime (spring-damper drives bones toward active pose targets, pose selection maps combat moves to registered poses).

Additional fixes:
- Fixed idTech2 build script (`.tools/bin/bango-idtech2-build.ps1`): resolved MSYS2 cmake compiler detection failure by converting gcc path to POSIX format and passing as explicit `-DCMAKE_C_COMPILER`.
- Added `free_gpu_sprites()` to shutdown sequence for proper GPU memory cleanup.
- All 3 platform builds verified passing: 3DS (BangoPatoot.3dsx), Windows (BangoPatootWindowsPreview.exe), idTech2 (game.dll).

Checkpoint saved: 2026-03-12
- Current saved state includes the 3DS prototype, rig and pose pipeline scaffold, generated placeholder assets, Recraft manifest, and the full Bango-Patoot GDD handoff.
- Runtime graphical asset loading and real gameplay animation playback are still pending and remain the next implementation step.

Checkpoint saved: 2026-03-12 project analysis pass
- Completed a full project analysis across docs, runtime code, build files, and pipeline artifacts.
- Confirmed `BANGO_PATOOT_FULL_GDD.md` is still the most up-to-date primary GDD in the repo.
- Revalidated the current 3DS build through `build_3ds.ps1`, which regenerated `generated/bango_runtime_asset_pack.h` and rebuilt `BangoPatoot.3dsx` successfully.
- Saved the analysis handoff at `BANGO_PATOOT_PROJECT_ANALYSIS_REPORT.md`.
- Noted one non-blocking maintenance item: `tools/build_runtime_asset_pack.py` emits Pillow deprecation warnings due to `Image.getdata()` usage.

Checkpoint saved: 2026-03-12 engine runtime pass
- Expanded `tools/build_runtime_asset_pack.py` so the generated runtime pack now emits rig bones, imported pose clips, and optional environment object-sheet assets from `assets/object_sheets/`.
- Replaced the 3DS runtime in `bango-patoot_3DS.c` with a fuller internal engine pass: procedural polygonal landscape mesh generation, terrain and object collision, enemy wave spawning, real-time combat resolution, attack/dodge flow, dynamic camera projection, and live rig-to-world pose playback for Bango and Patoot.
- Added a projected 3D-presented render path that combines generated terrain triangles, environment-object rendering, sprite billboards, and skeletal overlay debug/preview visuals.
- Rebuilt successfully through `build_3ds.ps1`, which regenerated `generated/bango_runtime_asset_pack.h`, linked the updated runtime, and produced `BangoPatoot.3dsx` without errors.
- Resolved the previously noted Pillow maintenance issue by switching the generator's frame extraction from `Image.getdata()` to `tobytes()`.

Checkpoint saved: 2026-03-13 rename cleanup and handoff
- Renamed the main 3DS runtime source from `banjo-kazooie_demake_3DS.c` to `bango-patoot_3DS.c`.
- Updated the active `Makefile` build input and cleaned stale old-name references from the project docs.
- Removed outdated generated build artifacts that still carried the previous source filename.
- Parked Bango-Patoot in a consistent state and shifted focus to the new `aridfeihth` concept-research pass.

*** Add File: c:\Users\rrcar\Documents\drIpTECH\aridfeihth\PROGRESS.md
# Aridfeihth Progress

Checkpoint saved: 2026-03-13 research foundation

- Established `aridfeihth` as a new design-focus workspace folder because no existing `aridfiehth` or `aridfeihth` project directory was present in the repo.
- Completed a text-first research pass using public Wikipedia articles on *Castlevania: Aria of Sorrow* and *Castlevania: Dawn of Sorrow*.
- Converted the useful structural lessons into an original gameplay direction rather than cloning content, terminology, encounters, maps, or story beats.
- Replaced enemy-soul collection with a `SimIAM` pet-bonding framework centered on rescue, trust, growth, and squad composition.
- Wrote a tracked research dossier with citations, references, and bibliography for future development guidance.

*** Add File: c:\Users\rrcar\Documents\drIpTECH\aridfeihth\ARIDFEIHTH_RESEARCH_AND_GAMEPLAY_FOUNDATION.md
# Aridfeihth Research And Gameplay Foundation

Date: 2026-03-13

## Purpose

This document translates useful high-level design lessons from *Castlevania: Aria of Sorrow* and *Castlevania: Dawn of Sorrow* into an original direction for `aridfeihth`.

The goal is not imitation. The goal is to preserve what makes that style of game compelling at a systems level while rebuilding every major feature in our own language, with our own fiction, and with fresh mechanics built around `SimIAM` pets instead of soul absorption.

This file is intentionally text-first and citation-tracked so it can guide implementation without drifting into copying visual motifs, exact room structures, enemy concepts, names, or plot beats.

## Source Rules

- Use public text references as design inputs, with Wikipedia as the primary baseline source for this pass.
- Borrow structural insight only: exploration pacing, progression layering, combat-build expression, and alternate-mode philosophy.
- Do not copy names, lore framing, enemy lists, map layouts, UI taxonomy, or signature encounter gimmicks.
- Every translated mechanic in this document adds at least one original twist so the result moves away from resemblance rather than toward it.

## Research Summary

### What Aria Of Sorrow Contributes

Aria shows the value of a side-scrolling exploration RPG where the player steadily opens a dense environment by earning movement and combat options over time [C1]. The experience works because it combines several loops into one steady rhythm: defeat enemies, gain power, revisit blocked paths, find equipment, and test new combinations in combat [C1].

Its major structural strength is not the fiction of absorbing monsters. Its real strength is that every encounter can feed long-term build expression. The player is rarely collecting for collection's sake alone. They are collecting to reshape how traversal, offense, defense, and utility feel minute to minute [C1].

Aria also demonstrates that an interconnected map becomes more memorable when progression is only partly linear. Early play can be directed, but the sense of ownership grows when new abilities cause older spaces to become newly legible and newly profitable [C1].

### What Dawn Of Sorrow Contributes

Dawn reinforces the same exploration-combat foundation while expanding the value of loadout management, distinct ability categories, and optional secondary modes [C2]. It shows that a system-driven action RPG gets more depth when the player can build contrasting profiles instead of chasing one best answer [C2].

Dawn also highlights two cautionary lessons. First, sustained build variety is valuable. Second, hardware-specific gimmicks can interrupt a strong action loop if they feel bolted on or if they slow down the player's combat flow [C2].

The useful takeaway is not to reproduce any stylus ritual or finishing minigame. The useful takeaway is to create high-tension boss resolution moments that fit the core controls and reinforce the game's identity instead of distracting from it [C2].

### Shared Lessons From Both Games

- Strong progression comes from layered rewards rather than raw stat increases alone [C1] [C2].
- A collectible ability system becomes sticky when categories are readable and combinations are surprising [C1] [C2].
- Shops, equipment, and alternate modes work best as support systems around exploration rather than separate pillars [C1] [C2].
- The setting can feel cohesive when each region has a distinct mechanical personality, enemy ecology, and mood [C1] [C2].
- Difficulty should come from encounter texture and route choice, not only inflated numbers [C1] [C2].

## Design Translation For Aridfeihth

## Core Pitch

`aridfeihth` should be a side-scrolling exploration action RPG set in a harsh, layered world where the player rebuilds a living bond-network of rescued `SimIAM` pets.

The player does not harvest power from slain enemies. Instead, they locate, calm, rescue, hatch, befriend, and train unusual companion entities whose instincts alter traversal, combat rhythm, survivability, and puzzle-solving.

The result should feel less like dominion over creatures and more like building a volatile expedition ecology.

## What Must Be Preserved

Because there is no existing `aridfeihth` directory in the workspace yet, the safest preservation rule is conceptual:

- Keep the project original-first.
- Keep the design systemic and portable, not overbuilt around one platform trick.
- Keep player expression centered on readable combinations.
- Keep the fiction oriented around relationship, rescue, and survival rather than corruption, inheritance, or gothic lineage.

The research should refine direction, not replace identity.

## The SimIAM Bond System

The soul system should be replaced with a four-lane `SimIAM` pet framework. This preserves the clarity of a categorized build system while changing the fantasy, acquisition method, and emotional tone.

### 1. Burst Pets

Burst pets are quick, directed actions tied to deliberate button presses. They are the short-cooldown attack or utility layer.

Examples of original uses:

- A glass-beaked pet that ricochets between lanterns and weak points.
- A burrow-mole pet that erupts under shielded enemies.
- A static moth pet that chains sparks across wet terrain.

Original twist:

Burst pets improve not by duplicates alone, but by field behavior milestones such as precise hits, chain timing, or terrain interactions.

### 2. Chorus Pets

Chorus pets are maintained stance companions. When active, they reshape the local combat state or movement state over time.

Examples of original uses:

- A wind-kite pet that softens falls and bends projectile arcs.
- A shell-drum pet that pulses stagger resistance while draining a stamina-like bond meter.
- A glow-larva cluster that reveals hidden routes but draws predators.

Original twist:

Chorus pets create tradeoffs instead of flat upgrades. The player maintains one because of what it enables, while accepting a clear cost in resource drain, noise, visibility, or mobility.

### 3. Crest Pets

Crest pets are passive roster effects. They tune statistics, resistances, economy, drop behavior, status recovery, or perception.

Examples of original uses:

- A scrap-hound pet that sniffs out salvage caches.
- A reed-fin pet that improves swamp footing and poison recovery.
- An ember-lung pet that converts burn buildup into temporary attack gain.

Original twist:

Crest pets do not merely sit in a menu. They have habitat preferences and social affinities. Certain Crest pets become more effective when paired with specific Burst or Chorus pets, creating a soft synergy web rather than a rigid recipe list.

### 4. Key Pets

Key pets are progression pets that unlock new routes and interaction verbs.

Examples of original uses:

- A latch-spider pet that threads bridge lines across chasms.
- A mirror-newt pet that lets the player slip through reflective fissures.
- A salt-ram pet that breaks mineral barricades after enough charge space.

Original twist:

Key pets should unlock traversal through authored world interactions, not abstract permission checks. The player should understand why a route opens because the pet physically changes what can be done in the space.

## Acquisition Philosophy

The `SimIAM` pets should not be random enemy-soul drops.

Instead, acquisition should come from five original channels:

- Rescue: free trapped pets from hazards, cages, collapsed tunnels, or hostile ecosystems.
- Pacification: calm frightened wild pets through movement, rhythm, bait, or environmental manipulation.
- Restoration: rebuild dormant pet shrines, nests, or incubators.
- Exchange: trade with survivors, handlers, or caravans for eggs, fragments, or trust permits.
- Consequence: some pets join only after the player resolves local problems without excessive destruction.

This immediately changes the tone from extraction to caretaking.

## Progression Loop

The high-level loop for `aridfeihth` should be:

1. Enter a region and map its dangers.
2. Rescue or befriend new `SimIAM` pets.
3. Use new pet verbs to access fresh routes.
4. Recover materials, relics, and habitat upgrades.
5. Return to a refuge hub to hatch, train, pair, and reconfigure the active roster.
6. Push into deeper layers where route complexity and pet synergy matter more.

That keeps the collectible system tied to navigation and preparation rather than making it a disconnected inventory hobby.

## Combat Design Direction

Combat should stay fast, readable, and side-view, but distinct from the source inspiration in tone and execution.

### Player Combat Identity

The protagonist should fight with a modest direct toolkit and rely on `SimIAM` combinations to broaden tactics. That prevents the pets from feeling cosmetic.

Suggested base kit:

- A close-range primary tool with reliable startup and cancel windows.
- A mobility action such as a slide, vault, or low-air dash.
- A bond command button that triggers active pet behavior.
- A tether wheel or quick-swap for rotating pet loadouts outside of animation-heavy menus.

### Encounter Texture

Encounters should reward three styles of thinking:

- Spatial reading: understanding ledges, hazards, blind angles, and breakable terrain.
- Timing: using Burst pets or melee strings at the right interrupt windows.
- Composition: picking a roster that handles the region's ecology instead of using a universal best build.

### Resource Model

Do not reuse a standard magic-point fantasy by default.

Use a `bond tension` resource instead. It rises when pets are frightened, overused, or exposed to hostile conditions. Strong pet actions increase tension. Safe movement, refuge nodes, perfect dodges, and affinity matches reduce it.

This creates an original pressure model tied to companionship rather than spellcasting.

## Boss Design Direction

The source games use special boss-resolution ideas, but `aridfeihth` should resolve bosses through a native system called `bond weaves`.

### Bond Weaves

After the boss is broken into a vulnerable state, the player must complete a short, core-controls-based finish sequence using one or more active pets.

Examples:

- Direct a latch-spider to pin a limb while the player climbs for a finishing strike.
- Maintain a Chorus pet aura while dodging a retaliation burst and then landing a Burst command.
- Use the right pet pairing to stabilize a collapsing arena long enough to expose the boss core.

Original twist:

These finishes stay inside the main control language. No tracing. No platform gimmick. No sudden mode shift.

## World Structure

The environment should be interconnected like a classic exploration action RPG, but the fiction should move away from a single castle and toward a layered, living ruin network.

Suggested regional model:

- Surface refuge and market ring.
- Dry cistern galleries.
- Glass-wind spires.
- Saltroot undergroves.
- Machine ossuary.
- Drowned archive.
- Ember trench.

Each region should have:

- A traversal problem.
- A dominant ecological threat.
- At least one pet acquisition opportunity.
- A revisitation payoff after later pet unlocks.

## Hub Design

The safe hub should be more than a shop.

It should function as a care-and-planning refuge where the player:

- Hatches or rehabilitates pets.
- Builds habitat modules that improve pet loyalty and utility.
- Assigns pets to nursery, scouting, salvage, or defense roles.
- Receives rumors that hint at hidden routes or distressed creatures in the field.

This is a major originality lever. It gives the collectible system a home and a social texture.

## Equipment And Crafting

Weapons and gear should still matter, but pet integration should drive how crafting works.

Original direction:

- Gear recipes require region salvage and specific pet-assisted processes.
- Some pets refine materials better than others.
- Upgrades should unlock conditional traits, not only larger numbers.
- Certain crafted tools open alternate route solutions so pet progression and equipment progression intersect.

This replaces the source idea of consuming collected powers for weapon transformation with a more world-grounded workshop loop [C2].

## Alternate Modes And Replay Value

The research suggests that alternate modes matter when they reinterpret the main systems instead of merely repeating content [C1] [C2].

`aridfeihth` should plan for:

- `Refuge Run`: New Game Plus with expanded pet ecology and shifted rescue locations.
- `Handler Mode`: fixed protagonist stats, but stronger pet micromanagement and harsher bond tension.
- `Boss Circuit`: a remixed gauntlet focused on bond-weave execution.
- `Expedition Seeds`: challenge variants where region hazards and pet placements rotate within authored rules.

## Originality Guardrails

To keep the project safely inspired rather than derivative, use these rules during implementation:

- Avoid gothic vampire mythology as the narrative engine.
- Avoid the exact four source category names even if a four-lane structure remains useful.
- Avoid castle-copy cartography, throne-room logic, eclipse inheritance framing, and cult resurrection plotting.
- Avoid direct parallels to named characters, iconic weapons, or recognizable enemy archetypes.
- Favor ecology, refuge-building, pet trust, and layered ruin survival as the project's own center of gravity.

## Immediate Development Recommendations

1. Define the fiction of `SimIAM`: what they are, how they bond, why they gather around the protagonist, and what ethical limits govern their use.
2. Write a one-page player verb list covering movement, melee, Burst pet use, Chorus pet activation, swapping, healing, and bond-weave finishing.
3. Prototype the four pet lanes with placeholder data before writing any story-heavy content.
4. Draft a small interconnected test map with three traversal locks and two revisit rewards.
5. Build the refuge hub early so acquisition, growth, and loadout iteration have a home.
6. Keep a source-to-design trace table so every borrowed structural lesson is visibly transformed.

## Source-To-Design Trace Table

| Research lesson | Our translation | Originalizing change |
| --- | --- | --- |
| Collectible powers drive build variety [C1] [C2] | `SimIAM` pet roster shapes combat and traversal | Abilities come from rescue and bonding, not enemy harvesting |
| Ability categories make loadouts legible [C1] [C2] | Four pet lanes: Burst, Chorus, Crest, Key | New language, social ecology, and synergy system |
| Interconnected world benefits from gated revisits [C1] [C2] | Layered ruin network with pet-verb route unlocks | Region ecology and refuge support change the tone and structure |
| Extra modes extend lifespan [C1] [C2] | Refuge Run, Handler Mode, Boss Circuit, Expedition Seeds | Rebuilt around pet handling and route variance |
| Boss finish mechanics should create tension [C2] | Bond weaves | Uses core controls and pet cooperation instead of hardware gimmicks |

## Citations

- [C1] Wikipedia contributors. *Castlevania: Aria of Sorrow*. Wikipedia. https://en.wikipedia.org/wiki/Castlevania:_Aria_of_Sorrow . Accessed 2026-03-13.
- [C2] Wikipedia contributors. *Castlevania: Dawn of Sorrow*. Wikipedia. https://en.wikipedia.org/wiki/Castlevania:_Dawn_of_Sorrow . Accessed 2026-03-13.

## References

1. Wikipedia contributors. *Castlevania: Aria of Sorrow*. Wikipedia, The Free Encyclopedia. Public article consulted for gameplay structure, Tactical Soul overview, progression framing, setting summary, development context, and reception notes. https://en.wikipedia.org/wiki/Castlevania:_Aria_of_Sorrow . Accessed 2026-03-13.
2. Wikipedia contributors. *Castlevania: Dawn of Sorrow*. Wikipedia, The Free Encyclopedia. Public article consulted for gameplay structure, Tactical Soul categorization, boss-finish ritual summary, alternate modes, setting summary, development context, and reception notes. https://en.wikipedia.org/wiki/Castlevania:_Dawn_of_Sorrow . Accessed 2026-03-13.

## Bibliography

Wikipedia contributors. *Castlevania: Aria of Sorrow*. Wikipedia, The Free Encyclopedia. https://en.wikipedia.org/wiki/Castlevania:_Aria_of_Sorrow . Accessed 2026-03-13.

Wikipedia contributors. *Castlevania: Dawn of Sorrow*. Wikipedia, The Free Encyclopedia. https://en.wikipedia.org/wiki/Castlevania:_Dawn_of_Sorrow . Accessed 2026-03-13.

Checkpoint saved: 2026-03-12 QA demo asset planning pass
- Saved a fresh status summary of the internal rendering/runtime stack and confirmed the project has a real stereo render loop, projected terrain pass, rig-driven character billboards, object hooks, enemy and wildlife rendering, and terrain-aware collision.
- Defined the minimum playable QA demo content target as a two-zone vertical slice that exercises title flow, save/load, shrine refinement, combat, dodge, collectibles, wildlife interaction, NPC dialogue, relationship telemetry, one elite encounter, and one boss gate for both Windows-side testing and actual 3DS hardware testing.
- Wrote a pixel-precise Recraft requirements brief for the QA demo pass, including exact master canvas sizes, export targets, palette/alpha constraints, and acceptance gates tuned for 3DS top-screen and bottom-screen runtime limits.
- Authored a fixed-budget Recraft manifest for a 50-asset generation pass at 40 credits per asset for an exact 2000-credit minimum-content demo build.
- Saved the planning artifacts at `QA_DEMO_RECRAFT_REQUIREMENTS.md` and `recraft/bango_patoot_qa_demo_manifest.json` for future production use.

Checkpoint saved: 2026-03-12 2D-to-3D reconstruction planning pass
- Added an explicit asset reconstruction contract at `ASSET_TO_3D_RECONSTRUCTION_PIPELINE.md` describing the ordered pipeline from per-pixel matrices and 32-neighbor color analysis through region segmentation, symbol-object graphs, depth-hint maps, spatial metrics, mesh contracts, rig mapping, surface contracts, and keypose intake.
- Added a machine-readable reconstruction spec at `recraft/bango_patoot_qa_demo_3d_reconstruction_spec.json` so the future analysis pass can emit deterministic outputs per asset instead of relying on loose interpretation.
- Locked the meaning of the requested per-pixel object breakdown into a concrete symbolic-space model: each meaningful contiguous image region becomes a symbol object with boundaries, material hints, pivots, collision hints, deformation class, and occlusion order.
- Recorded the practical blocker honestly: the repo does not yet contain the approved generated QA demo masters required to execute the full reconstruction and mesh-generation workflow, so this pass defines the contract to run once the Recraft outputs exist.

Checkpoint saved: 2026-03-12 manifest tooling and slicer pass
- Added `tools/enrich_qa_demo_manifest.py` to apply per-asset 3D translation metadata, reconstruction outputs, and slice plans across the full QA demo manifest.
- Added `tools/validate_qa_demo_manifest.py` to assert every asset includes the required translation metadata and a valid slice plan.
- Added `tools/slice_qa_demo_assets.py` to slice generated masters into runtime exports for grid-based assets and emit manual region-template JSON files for free-layout UI masters.
- Ran the enricher and validator successfully: all 50 assets in `recraft/bango_patoot_qa_demo_manifest.json` now carry complete translation metadata and slicer metadata.
- Exercised the slicer against the current `generated/` folder; no QA demo masters exist there yet, so zero runtime exports were produced, but four manual UI template files were emitted and the missing-source behavior was verified.

Checkpoint saved: 2026-03-12 reconstruction analyzer and Windows preview pass
- Added `tools/analyze_asset_reconstruction.py` to execute the first concrete reconstruction-analysis layer against source images, emitting per-pixel matrices, region maps, symbol-object graphs, depth maps, spatial metrics, mesh contracts, surface contracts, and rig-mapping/intake outputs for rigged entities.
- Ran the analyzer successfully against the current placeholder character sheets at `assets/source_sheets/bango_tpose_4angle.png` and `assets/source_sheets/patoot_tpose_4angle.png`, saving deterministic outputs under `generated/reconstruction_preview/bango/` and `generated/reconstruction_preview/patoot/`.
- Added a native Windows review target in `windows_preview.cpp` plus the build entrypoint `build_windows_preview.ps1` so the current integrated gameplay/rendering state can be inspected on this machine without relying on the 3DS runtime.
- Built the desktop review executable successfully as `BangoPatootWindowsPreview.exe`.
- Current limitation remains explicit: the Windows preview is using the currently available placeholder character sheets and procedural world/runtime stand-ins, not yet the future QA master asset exports, because those Recraft outputs still do not exist in the repo.

Checkpoint saved: 2026-03-12 end-to-end Windows test world rendering pass
- Added `tools/build_rendering_pass_manifests.py` and generated two concrete Recraft manifests: `recraft/bango_patoot_environment_surface_tiles_manifest.json` for the requested 1000-credit 128x128 environment tile pass, and `recraft/bango_character_500_credit_manifest.json` for the requested 500-credit Bango-only character pass.
- Added `tools/build_demo_world.py` to generate a contained Windows demo level with polygonal terrain data, mapped surface-tile assignments, point-light placement, object spawns, enemy spawns, and a fixed altar-slot objective target. The tool now emits `generated/windows_preview/demo_world.json`, `generated/windows_preview/generated_preview_world.h`, and placeholder 128x128 tile textures under `generated/windows_preview/env_tiles/` for local review builds.
- Added `tools/build_actor_blockout.py` to derive a Bango polygonal blockout from the reconstruction outputs and rig definitions, and to emit a Bango pose-chain data file for preview-time inbetweening and keypose-driven animation tests. The tool emits `generated/windows_preview/bango_model_blockout.json`, `generated/windows_preview/bango_pose_chain.json`, and `generated/windows_preview/generated_bango_actor.h`.
- Fixed `tools/analyze_asset_reconstruction.py` rig lookup so entity names resolve case-insensitively, preventing lowercase entity requests from losing rig references during reconstruction analysis.
- Added the new desktop executable source `windows_test_world.cpp` and updated `build_windows_preview.ps1` so the Windows build now regenerates manifests, world data, blockout data, and then compiles the test world into `BangoPatootWindowsPreview.exe`.
- The new Windows test world now includes: full contained 3D space generation, polygonal terrain, explicit sky-versus-landmass horizon separation, sun plus environmental point-light shading with CPU shadow-ray checks, Bango blockout rig rendering with pose chaining and spring inbetweening, keyboard plus Xbox controller support, enemies, interactive world objects, and a win/lose loop where the player defeats enemies, collects a relic, and inserts it into the altar slot to trigger victory.

Checkpoint saved: 2026-03-12 tile-driven 3D test level pass
- Added `tools/build_test_level_from_tiles.py` to analyze the real PNG files under `assets/tiles/bango-patoot-tiles/`, extract sampled albedo/relief data, and emit a rebuildable stage definition at `generated/bango_test_level.h` plus a JSON mirror at `generated/bango_test_level.json`.
- Updated `build_3ds.ps1` so the Bango-Patoot build now regenerates placeholder rig sheets/loops when needed, rebuilds the runtime asset pack, and regenerates the new tile-driven test level before compiling the 3DS target.
- Replaced the old world-0 generic terrain bands in `bango-patoot_3DS.c` with a full 24x24 polygonal Underhive test stage using the new tileset as the material source for cell assignments, spawn layout, object placement, and enemy placement.
- Updated terrain rendering so the landscape mesh now derives per-vertex color from sampled tile albedo data and uses sampled tile relief values to drive lighting/detail emphasis across the 3D landmass rather than flat fallback colors.
- Rebuilt successfully through `build_3ds.ps1`; the asset generators completed cleanly and the updated runtime produced `BangoPatoot.3dsx`.

Checkpoint saved: 2026-03-13 shared tile-level preview and UV terrain pass
- Updated `windows_test_world.cpp` and `build_windows_preview.ps1` so the desktop preview now regenerates and consumes the same `generated/bango_test_level.h` data as the 3DS runtime instead of the older synthetic preview-world header.
- The Windows preview now loads the same generated heightfield, tile assignments, object spawns, enemy spawns, player spawn, and altar goal positions as the tile-driven Underhive test level.
- Upgraded the 3DS terrain pass in `bango-patoot_3DS.c` from single-quad color sampling to subdivided UV-style tile paging: each terrain cell is now tessellated into sampled subquads, with tile albedo paging and relief-driven micro-displacement across the polygonal landmass.
- Rebuilt both targets successfully: `build_windows_preview.ps1` produced `BangoPatootWindowsPreview.exe` and `build_3ds.ps1` produced `BangoPatoot.3dsx`.

Checkpoint saved: 2026-03-13 active runtime cleanup, prop polish, and drIpTECH scene-format pass
- Confirmed the real 3DS build target is `bango-patoot_3DS.c`, not `banjo-kazooie_demake_3DS.c`, and ported the generated world-0 load path into the active runtime.
- The shipped 3DS runtime now consumes `generated/bango_test_level.h` directly for shared landscape heights, tile assignments, object placements, enemy placements, and player spawn.
- Replaced the older terrain-layer path in the active runtime with subdivided tiled-UV relief terrain rendering and removed the stale unused XP-name table.
- Upgraded `windows_test_world.cpp` object rendering from single generic boxes to composed authored-looking props for crates, lights, altar slots, and cache structures.
- Added a proprietary drIpTECH scene format and compiler path through the existing egosphere pipeline: `egosphere/tools/drip3d_pipeline.py`, `egosphere/pipeline/sample_project/game_project.drip3d.json`, and `egosphere/pipeline/DRIP3D_SPEC.md`.
- Extended `egosphere/tools/game_pipeline.py` so translation-profile and depth-card metadata now flow through the Clip Studio, Blender, and idTech2 bundle outputs.
- Revalidated all three affected build paths successfully: `build_3ds.ps1`, `build_windows_preview.ps1`, and the sample drIpTECH scene build into `egosphere/pipeline/out/drip3d-sample/`.

Checkpoint saved: 2026-03-13 Bango production asset-program escalation pass
- Switched focus from generic pipeline scaffolding to the full Bango-Patoot production asset flow.
- Added `tools/build_bango_production_asset_program.py` to generate a production-scale Recraft manifest plus clip-blend-id protocol outputs for Bango-specific assets.
- Escalated the planned Recraft program from 15000 to 21000 credits because the full packed-master representation of the requested production content exceeds the earlier cap once character sheets, packed animation masters, environment sets, FX, HUD, gear, and derived-map obligations are counted together.
- Added `tools/run_bango_clip_blend_id_pipeline.py` so the new manifest now feeds concrete Clip Studio intake, auto-polish, Blender ingest, and idTech2 registry queue files under `generated/clip_blend_id/`.
- Updated `egosphere/tools/run_recraft_manifest.py` so dict-based manifests with metadata plus `assets` arrays are executable by the shared generation runner instead of only flat list manifests.
- Added `BANGO_PRODUCTION_ASSET_PIPELINE.md` as the production-facing protocol and budgeting note for the new pass.

Checkpoint saved: 2026-03-13 DoNOW and standalone DoENGINE tooling pass
- Added `DoENGINE/packages/donow/src/donow.ts` plus `DoENGINE/tools/build_donow_runtime_manifest.py` so the Bango clip-blend-id stream now has a DoENGINE automated implementation target adjacent to idTech2.
- Updated the Bango pipeline so all generated production assets now declare a `donow` pipeline target and the queue build emits `generated/clip_blend_id/donow_runtime_manifest.json` automatically.
- Added `tools/build_bango_idtech2_bootstrap.py` so the idTech2 registry now produces generated bootstrap code under `idtech2_mod/generated/` instead of stopping at JSON only.
- Updated `idtech2_mod/game/bango_game.c` to mount the generated asset bootstrap during module initialization.
- Added a standalone DoENGINE GUI application at `DoENGINE/apps/doengine_studio.py`, a Windows launcher at `DoENGINE/DoENGINEStudio.cmd`, and a 3000-credit MOTION-themed GUI asset manifest builder at `DoENGINE/tools/build_doengine_gui_asset_manifest.py`.
