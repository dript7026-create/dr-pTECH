# Synthesis Engine

The current egosphere pipeline already builds game bundles from a canonical project manifest. The synthesis extension moves one level higher: it generates the project manifest itself from a world seed, so the engine can produce a whole playable reality-plan rather than only packaging pre-authored assets.

`egosphere/tools/synthesis_pipeline.py` is the first pass of that system.

## Purpose

The synthesis engine treats a game as a recursively generated reality field made of:

- reality cells
- sanctuary and family hubs
- actor populations
- render and mesh recipes
- physics and interaction recipes
- world-pressure conductors
- repercussive timing forecasts driven by HOPE

Instead of requiring a designer to hand-author every canonical asset entry, the synthesis compiler accepts a high-level seed and emits:

- a canonical egosphere game project manifest
- full Clip Studio / Blender / idTech2 bundle instructions through the existing pipeline
- synthesized asset recipes for sprites, tilesets, meshes, materials, physics rigs, and ambience
- scene-level HOPE annotations for frame cost, tail risk, clog risk, and stabilization recommendations

## High-Level Flow

1. A world seed defines reality cells, family hubs, and generation bias.
2. The synthesis compiler derives scenes, entities, systems, and asset recipes.
3. HOPE evaluates each reality cell to predict practical cost and consequent tail risk.
4. The generated canonical project is handed off to the existing `game_pipeline.py` builder.
5. The builder emits the same downstream bundles already used by egosphere.

## What “Full Game Assets” Means In This Pass

This pass generates the entire asset plan and bundle-ready project description for a game reality, including:

- world tilesets
- playable and non-player sprites
- portraits
- terrain and sanctuary mesh recipes
- material recipes
- physics rig recipes
- ambience/audio recipes
- scene, entity, and system manifests

This does not yet synthesize final binary image, mesh, or audio content from a model backend. It establishes the deterministic project graph that those synthesis backends can consume.

That distinction matters:

- the engine now produces the whole game reality specification from generation systems
- the next layer would connect that specification to image, mesh, and audio synthesis executors

## HOPE Integration

Every reality cell is compiled into:

- mesh profile
- physics profile
- pipeline profile
- cosmic profile
- kinship profile

These are fed through HOPE so each generated scene carries a predictive control reading before the engine builds it.

That gives the synthesis engine a way to produce reality while also forecasting whether the resulting scene will clog the pipeline, destabilize frame pacing, or require stronger sanctuary balancing.

## Open Arms And Sanctuary Use

The synthesis compiler includes family-hub and sanctuary-facing fields so a game can preserve recovery, kinship, and refuge spaces as first-class runtime structures rather than incidental levels. This is especially useful for Open Arms-style projects where the emotional grammar of family and care needs to remain mechanically real inside the world model.

## Sample Seed

See:

- `egosphere/pipeline/projects/hope_synthesis/hope_world.seed.json`

Build it with:

```sh
python egosphere/tools/synthesis_pipeline.py build --project egosphere/pipeline/projects/hope_synthesis/hope_world.seed.json --out egosphere/pipeline/out/hope_synthesis
```

## Extension Direction

The synthesis engine is now positioned to become the outer game generator for a 3D drIpTECH engine:

- HOPE governs frame-time and repercussive cost.
- EgoSphere governs local memory and consequence.
- godAI governs world-pressure and pacing.
- The synthesis compiler governs world fabrication itself.

The next useful step would be to connect the generated asset recipes to actual synthesis executors for textures, meshes, animation clips, and audio motifs.