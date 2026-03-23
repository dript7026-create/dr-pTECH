# Bango-Patoot Project Analysis Report

Date: 2026-03-12

## Executive Summary

Bango-Patoot is currently a viable Nintendo 3DS prototype branch with a stable build path, a clear original creative direction, a substantial full-game design handoff, and a working content scaffold for future authored assets. The project has already crossed the threshold from concept-only work into a playable vertical-slice-style prototype, but it is still systems-heavy and asset-light. The strongest current value is design clarity plus runtime scaffolding; the weakest current area is real gameplay embodiment through authored animation, collision, enemy actors, and save/load persistence.

## Current Project State

- Project identity is locked as an original 3DS action-RPG with Bango and Patoot rather than a direct demake.
- The current codebase builds successfully to `BangoPatoot.3dsx` and `BangoPatoot.elf` through the devkitPro pipeline.
- The main runtime lives in `bango-patoot_3DS.c` as a single translation unit, which is consistent with the project's current prototyping phase.
- The latest primary design reference is `BANGO_PATOOT_FULL_GDD.md`, with the `.txt` version acting as a plain-text companion export.

## Build And Validation Status

Validated on 2026-03-12:

- `build_3ds.ps1` completed successfully.
- The runtime asset pack header was regenerated at `generated/bango_runtime_asset_pack.h`.
- The 3DS build completed and produced `BangoPatoot.3dsx`.

Observed warning:

- `tools/build_runtime_asset_pack.py` currently emits Pillow deprecation warnings because it uses `Image.getdata()`. This is not a current build blocker, but it should be cleaned up before Pillow 14.

## Codebase Analysis

### Architecture Strengths

- The runtime state model is coherent and easy to reason about: `GameState` centralizes worlds, moves, shrine state, quest state, relationships, player state, and current UI state.
- The project already separates major gameplay concepts into initializer and update functions such as `init_worlds`, `init_moves`, `init_rigs`, `init_relationships`, `update_relationships`, `refine_at_shrine`, `unlock_next_world`, and `update_game`.
- The bottom-screen UI is not decorative only; it surfaces useful live data about shrine state, relationship state, rig metadata, and runtime asset preview state.
- Runtime asset preview integration is already partially real through `generated/bango_runtime_asset_pack.h` and the sprite-frame drawing path.

### Runtime Gameplay Coverage

Implemented now:

- 8 world nodes with unlock gating and atmosphere metadata.
- 1000 generated move definitions.
- 48 skill nodes.
- 6 EgoSphere-backed relationship entities.
- Shrine refinement, attribute spending, district unlocking, and move triggering loops.
- Stereoscopic top-screen scene rendering with simple parallax and sprite preview.
- Bottom-screen systems UI with rig and relationship telemetry.

Not yet implemented as real gameplay:

- Combat hitboxes and enemy actors.
- Traversal collision and interactable world geometry.
- Imported pose playback and inbetween-driven motion.
- Save/load and durable progression persistence.
- Real environment art loading beyond placeholder/generated runtime sprite content.

### Content Pipeline Status

The project has a stronger pipeline scaffold than the runtime currently exploits:

- `rigs/entity_rigs.json` defines core rig concepts.
- `pose_imports/pose_import_template.json` and `pose_imports/imported_pose_registry.json` establish an import contract.
- `recraft/bango_patoot_recraft_manifest.json` exists for later production asset generation.
- `tools/build_runtime_asset_pack.py` converts current asset inputs into a runtime header.

This means the project is well-prepared for resumed content production, but the runtime still needs a parsing/playback layer to consume more of that authored/imported data directly.

## Document Analysis

Primary design docs present:

- `BANGO_PATOOT_FULL_GDD.md`: most complete and current design handoff.
- `BANGO_PATOOT_FULL_GDD.txt`: text export of the same handoff.
- `BANO_GDD.md`: shorter directional GDD.
- `BANO_SYSTEM_ARCHITECTURE.md`: concise systems/technical structure note.
- `BANO_PROGRESS.md`: checkpoint and resume log.

Assessment:

- Documentation quality is ahead of runtime completeness, which is good for resumption but means implementation now needs to catch up to the spec.
- The full GDD appears to be the correct source of truth for future execution planning.

## Risks And Gaps

### Immediate Technical Risks

- Single-file architecture will become harder to maintain once real combat, collision, animation, and persistence are added.
- Runtime currently depends heavily on generated/static tables and placeholder render primitives rather than loaded authored assets.
- Imported pose data exists on disk but is not yet part of the live animation loop, which creates a gap between content pipeline work and gameplay value.

### Production Risks

- The game's intended final feel depends on user-authored art, animation, environment, object, and audio assets that are not yet integrated.
- The design scope is large relative to the current prototype size, especially because the project combines collectathon progression, RPG systems, social/relationship state, and stylized 3DS presentation.

## Recommended Next Steps

Priority 1:

- Parse `pose_imports/imported_pose_registry.json` into runtime structures and expose one real move animation using imported keyposes.

Priority 2:

- Replace placeholder collision-free movement with basic world collision and at least one enemy actor/update loop.

Priority 3:

- Split the single main C file into a few focused modules only after the first real gameplay loop lands, so refactoring serves stable behavior instead of speculative structure.

Priority 4:

- Update `tools/build_runtime_asset_pack.py` to remove deprecated Pillow API usage.

Priority 5:

- Add save/load for player, shrine, world unlock, and relationship state so the prototype can function as an actual progression testbed.

## Overall Assessment

Bango-Patoot is in a good pre-production-to-prototype state. The project is not content-complete and not feature-complete, but it is not blocked by missing direction. The next work should be implementation-heavy rather than more ideation-heavy: animation playback, collision, enemy presence, and persistence will produce the biggest jump in project maturity.
