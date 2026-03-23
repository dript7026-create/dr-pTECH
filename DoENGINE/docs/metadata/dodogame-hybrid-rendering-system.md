# DODOGame Hybrid Rendering System

Date: 2026-03-13

## Purpose

DODOGame is the standalone launchable host for a combined DoENGINE and ORBEngine runtime. It is not a replacement for either system.

- DoENGINE owns orchestration, manifests, controller routing, safe telemetry, and application-shell state.
- ORBEngine owns recursive pseudo-3D scene traversal, layered dimensional composition, and space-graph presentation.
- Game profiles own authored meshes, sprite sheets, collision anchors, and feature-specific rules.
- PlayNOW owns runtime staging, tutorial handoff, and generated asset-pass bookkeeping.

This gives Bango-Patoot a dedicated hybrid engine path while preserving a reusable engine surface for unrelated games.

## Rendering Stack

1. Scene ingest
The engine loads the selected game profile, manifest references, and controller profile before any render work begins.

2. Recursive space graph
ORBEngine resolves visible parent and child spaces, remagnification, recursion bounds, viewport ownership, and floor-warp context.

3. Full-3D proxy evaluation
The game profile contributes mesh-backed transforms, socket maps, collision anchors, and authored depth metrics for actors or environmental setpieces that need literal spatial coherence.

4. Pseudo-3D composite
ORBEngine performs billboard placement, top-cap projection, pseudo-volumetric layering, horizon lift, floor warping, and overlay ordering for the parts of the world that should feel dimensional without requiring full mesh rendering.

5. UI and telemetry composition
DoENGINE presents application chrome, controller diagnostics, runtime profile state, build status, and tutorial/test reporting.

6. PlayNOW staging
The runtime binds tutorial specs, generated player bundles, and pass-specific manifest references into a single handoff surface for validation and automation.

## Why This Supports Bango-Patoot

Bango-Patoot needs three things at once:

- authored, readable combat and traversal states
- handheld-friendly pseudo-3D presentation
- a path for richer full-3D data where proxy geometry is worth it

The hybrid stack handles this by keeping scene logic deterministic while letting presentation switch between literal mesh-backed proxy data and ORBEngine's dimensional sprite-and-layer system.

## Why This Is Still A General Engine

The generic game profile in the runtime contract does not assume Bango-Patoot-specific nouns. A non-Bango game can reuse the same stack if it can provide:

- a controller profile
- a game profile with feature declarations
- content manifests or direct runtime assets
- optional PlayNOW staging references

The result is a reusable engine host with one proven profile already wired in.

## Controller Support Policy

DODOGame treats controller support as first-class runtime data. The primary XInput profile explicitly maps:

- both sticks
- both stick clicks
- dpad directions
- A, B, X, Y
- LB, RB
- LT, RT
- Start, Back

The Bango tutorial contract is represented with the same semantics in the runtime profile:

- tap `B` for jump
- hold `B` for sprint
- tap `A` for crouch or slide while sprinting
- `LB` and `RT` for attacks
- `LeftThumb` and `RightThumb` for block and parry
- hold `LT` and steer `right_stick` for the ability wheel

This keeps the shell, tutorial simulator, and runtime profile consistent with the Bango tutorial spec.

## Asset Strategy

DODOGame has two parallel asset paths:

- Recraft production path: a 1500-credit themed GUI manifest for final art generation
- Local fallback path: generated placeholder PNG shell assets and two bitmap font atlases so the app can run immediately without waiting for paid generation

## Current Implementation Surface

- `DoENGINE/tools/build_dodogame_gui_asset_manifest.py`
- `DoENGINE/tools/generate_dodogame_placeholder_assets.py`
- `DoENGINE/tools/build_dodo_hybrid_runtime.py`
- `DoENGINE/apps/dodogame.py`
- `bango-patoot_3DS/tools/simulate_bango_tutorial_completion.py`

## Current Limits

- Live Recraft execution is intentionally separate from local placeholder generation because it consumes external credits.
- The tutorial simulation is rule-based against the current tutorial spec, not a computer-vision playthrough of a rendered game session.
- ORBEngine native rendering and DODOGame shell hosting are integrated at the runtime-contract level in this pass, not fused into a single compiled executable.
