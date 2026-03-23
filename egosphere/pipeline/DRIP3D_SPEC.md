drIpTECH Scene Format

Overview

The drIpTECH scene format is a proprietary JSON-based interchange file for authoring one project once and translating it in three directions:

1. Into depth-mapped 2D authoring/runtime data for Clip Studio Paint.
2. Sideways into Blender as lifted depth cards and scene bootstrap instructions.
3. Forward into idTech2 manifests and generated native glue.

File Extension

- `.drip3d.json`

Compiler

- `egosphere/tools/drip3d_pipeline.py`

Build Command

```bash
python egosphere/tools/drip3d_pipeline.py build --project egosphere/pipeline/sample_project/game_project.drip3d.json --out egosphere/pipeline/out/drip3d-sample
```

Top-Level Fields

- `project_name`: human-readable project identifier.
- `driptech_scene_version`: format version string.
- `seed`: deterministic generation seed.
- `canvas`: Clip Studio canvas dimensions.
- `translation_profile`: declares translation mode for Clip Studio, Blender, and idTech2.
- `bindings`: shared symbols, tags, hitboxes, and script bindings.
- `bridges`: per-target settings for Clip Studio, Blender, and idTech2.
- `assets`: tilesets, depth cards, portraits.
- `scenes`: gameplay scenes and timeline triggers.
- `entities`: spawnable runtime entities.
- `systems`: runtime systems and dispatch ordering.
- `targets`: downstream bundle folder names.

Depth Cards

Each `assets.depth_cards[]` entry binds:

- `color_path`: the authored 2D color sprite.
- `depth_map`: grayscale or packed depth representation.
- `normal_map`: optional surface normal texture.
- `lift_mode`: how Blender should lift the card into 3D.
- `collider`: gameplay collision profile.

Compilation Output

The compiler first emits a canonical egosphere manifest named `game_project.generated.json`, then runs the existing bundle generators:

- `clipstudio_bundle/clipstudio_export.json`
- `clipstudio_bundle/clipstudio_runtime_manifest.json`
- `blender_bundle/blender_conversion.json`
- `blender_bundle/blender_ingest.py`
- `idtech2_bundle/idtech2_manifest.json`
- `idtech2_bundle/g_driptech_pipeline_autogen.c`
- `idtech2_bundle/g_driptech_pipeline_autogen.h`

Compatibility Notes

- The format is intentionally close to the canonical egosphere manifest so existing established software remains the execution backbone.
- drIpTECH-specific fields are additive and preserved in bundle metadata where downstream tools may need them.
