# Rig And Pose Pipeline

Files added in this pass:
- `rigs/entity_rigs.json`: skeletal rig definitions for Bango and Patoot.
- `assets/source_sheets/*.png`: four-angle transparent T-pose sheets.
- `assets/concept_loops/*.gif`: key-pose loop previews to establish posture and movement feel.
- `pose_imports/pose_import_template.json`: single-pose import contract.
- `tools/import_pose_keyframe.py`: registry importer for newly drawn pose keyframes.
- `tools/build_recraft_manifest.py`: Recraft manifest generator for rig-facing sprite passes.

Workflow:
1. Generate or replace the transparent PNG/GIF placeholders.
2. Draw a new single-pose keyframe as PNG.
3. Copy and edit `pose_import_template.json` for that keyframe.
4. Run `tools/import_pose_keyframe.py` to register it.
5. Use the registry plus rig JSON as the source of truth for later inbetweening and runtime mapping.
6. Run `tools/build_recraft_manifest.py` to emit a Recraft manifest for additional turnaround or key-pose sheet generation.

Current inbetweener status:
- The prototype stores inbetween hints as JSON parameters for a future AI/physics interpolation pass.
- No claim is made that a learned inbetweener is already implemented in the 3DS runtime.
- The project is now structured so authored key poses can be imported incrementally without changing the core rig format.