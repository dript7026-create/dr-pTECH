# Pipeline Overview

This directory defines a streamlined authoring-to-engine chain for a new game project.

Stages

1. Clip Studio Paint authoring
   - 2D sprites, tiles, portraits, animation timelines, and visual-script bindings.
   - Export layers, frame tags, hitboxes, and symbol/script metadata into a runtime manifest.
2. Blender conversion
   - Lift/extrude 2D assets into 3D placeholders.
   - Build animation clips, node graphs, and scene/world layout instructions.
   - Generate a Blender Python ingest helper for collection/object bootstrap and dry-run validation.
3. idTech2 integration
   - Emit asset registries, precache tables, spawn tables, system dispatch wiring, and generated native C glue.

Canonical source of truth

- `sample_project/game_project.json`
  - A portable manifest describing assets, scenes, scripts, and engine targets.
- `sample_project/game_project.drip3d.json`

`sample_project/game_project.drip3d.json` is the drIpTECH proprietary scene file that compiles into the canonical pipeline manifest.

Generated outputs

- `out/<build-name>/clipstudio_bundle/clipstudio_export.json`
- `out/<build-name>/clipstudio_bundle/clipstudio_runtime_manifest.json`
- `out/<build-name>/blender_bundle/blender_conversion.json`
- `out/<build-name>/blender_bundle/blender_ingest.py`
- `out/<build-name>/idtech2_bundle/idtech2_manifest.json`
- `out/<build-name>/idtech2_bundle/g_driptech_pipeline_autogen.c`
- `out/<build-name>/idtech2_bundle/g_driptech_pipeline_autogen.h`

Design constraints

- No external Python dependencies.
- JSON as the interchange format.
- Deterministic generation from a single project manifest.
- Existing C plugin files remain the integration anchors for each authoring tool.

Rich data now carried across the chain

- Clip Studio: layer metadata, symbol bindings, frame tags, hitboxes, and script binding descriptors.
- Blender: material profiles, rig overrides, NodeCraft graphs, and scene build instructions.
- idTech2: precache groups, spawn metadata, bootstrap settings, and generated dispatch lookup tables.

Recommended workflow

1. Duplicate `sample_project/game_project.drip3d.json` into a project-specific drIpTECH scene file.
2. Point color, depth-map, and tileset asset paths to real Clip Studio exports and image files.
3. Run `tools/drip3d_pipeline.py build --project your_scene.drip3d.json --out out/your-build`.
4. Inspect the emitted canonical `game_project.generated.json` if you need the lower-level pipeline view.
5. Feed generated Blender instructions into Blender-side tooling.
6. Feed generated idTech2 outputs into the native gamecode repository.

Open-source tech credits

- Blender is the upstream DCC/runtime environment expected for the Blender stage of this pipeline.
- id Tech 2 / Quake II source lineage is the upstream engine family targeted by the generated idTech2 bundle artifacts.
- Workspace-wide attribution tracking for these tools lives in `../../THIRD_PARTY_CREDITS.md` from the workspace root and the machine-readable manifest at `../../tools/dependency_manifests/open_source_3d_stack.json`.

drIpTECH Scene Format

- Extension: `*.drip3d.json`
- Purpose: single-source project file for depth-mapped 2D authoring in Clip Studio Paint, sideways lift into Blender, and forward export into idTech2.
- Compile target: standard egosphere pipeline manifest plus all downstream bundles.

drIpTECH-specific additions carried through the pipeline

- `translation_profile`: declares how the scene should map into Clip Studio, Blender, and idTech2.
- `assets.depth_cards`: pairs a color sprite with its depth map and optional normal map.
- `bridges.clipstudio.depth_cards`: preserves depth-card metadata for 2D authoring/runtime tooling.
- Blender lift plans now carry `depth_map_path`, `normal_map_path`, and `lift_mode`.
- Clip Studio and idTech2 bundles now record the translation profile so downstream established tools can key off the same source metadata.
