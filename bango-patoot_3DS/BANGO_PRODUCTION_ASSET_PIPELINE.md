# Bango-Patoot Production Asset Pipeline

Date: 2026-03-13

This document defines the production-scale Bango-Patoot asset program for the Clip Studio Paint to auto-polish to Blender to idTech2 path.

## Budget Decision

The earlier 15000-credit ceiling is not large enough once the full production request is represented as packed master sheets plus required downstream depth and hit-precision derivatives.

This pass therefore escalates the planned budget ceiling to 21000 credits.

The generated manifest targets an exact allocated total of 21000 planned credits.

## Core Intake Rules

- Every generated master uses a transparent background.
- Character, environmental object, item, weapon, armor, and apiary sheets use 4-angle quadrant layout.
- Front view sits in the top-left quadrant.
- Right view sits in the top-right quadrant.
- Left view sits in the bottom-left quadrant.
- Back view sits in the bottom-right quadrant.
- Every master declares congruent derived outputs for texture-depth and hit-precision map generation.
- Combat effect sheets use horizontally arranged frames, with lower rows reserved for depth and hit-mapped derivatives.
- Environmental effect sheets are treated as 360-degree angle-mapped transparent atmospheric masters.

## Packing Strategy

The request contains more raw content obligations than is practical as one prompt per sequence.

The production pass therefore uses packed masters:

- Character/reference obligations are emitted as 501 character-sheet masters.
- Raw keypose requirements are compressed into 1109 packed animation masters with up to 4 sequence groups per master.
- Environment obligations are emitted as 137 environment set masters, each holding 13 tile types.
- HUD, item, weapon, ammunition, and armor content is emitted as structured atlas packs.
- FX, animated environmental objects, and apiaries remain dedicated masters because their downstream slicing and runtime routing differ materially.

## Automation Flow

1. Generate packed masters from `recraft/bango_patoot_production_21000_credit_manifest.json`.
2. Feed raw masters into `readAIpolish` for transparent-edge cleanup and polish.
3. Emit Clip Studio intake queues and runtime bindings.
4. Emit Blender ingest queues for riggable and environment-conversion assets.
5. Emit DoNOW runtime ingest data so the same stream is immediately mountable inside DoENGINE.
6. Emit idTech2 runtime registry and bootstrap targets for final game-facing asset integration.

## Produced Artifacts

- `recraft/bango_patoot_production_21000_credit_manifest.json`
- `generated/clip_blend_id/bango_patoot_clip_blend_id_protocol.json`
- `generated/clip_blend_id/clipstudio_ingest_manifest.json`
- `generated/clip_blend_id/auto_polish_queue.json`
- `generated/clip_blend_id/blender_ingest_manifest.json`
- `generated/clip_blend_id/donow_runtime_manifest.json`
- `generated/clip_blend_id/idtech2_runtime_registry.json`
- `generated/clip_blend_id/pipeline_report.json`
