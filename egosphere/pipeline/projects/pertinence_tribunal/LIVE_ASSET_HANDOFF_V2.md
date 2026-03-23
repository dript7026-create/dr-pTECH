Date: 2026-03-12
Project: Pertinence: Tribunal

Status
- Expanded character, enemy, boss, fauna, Goduly, and FX manifest completed through a fresh live Recraft pass.
- World-buildout tile pass was already complete and reused without rerunning its 120-item batch.
- Live bundles were rebuilt against the expanded manifest.

Expanded asset pass
- Manifest: recraft_manifest.json
- Completed items: 102
- Estimated units spent on this pass: 4080
- Ledger: recraft_generation_ledger_v3.csv
- Log: recraft_generation_log_v3.txt

World tile pass
- Manifest: recraft_world_tiles_pass_manifest.json
- Completed items: 120
- Estimated units previously spent on that pass: 4800
- Ledger: recraft_world_tiles_pass_ledger.csv
- Log: recraft_world_tiles_pass_log.txt

Current live bundle snapshot
- Clip Studio bundle: egosphere/pipeline/out/pertinence_tribunal_live_v2/clipstudio_bundle/clipstudio_export.json
- Blender bundle: egosphere/pipeline/out/pertinence_tribunal_live_v2/blender_bundle/blender_conversion.json
- idTech2 bundle: egosphere/pipeline/out/pertinence_tribunal_live_v2/idtech2_bundle/idtech2_manifest.json
- Blender dry-run: 32 scenes, 88 lifts
- idTech2 summary: 102 assets, 102 precaches, 6 systems, 19 entities

Review package
- review_v2/sprites_live_v2_contact_sheet.png
- review_v2/portraits_live_v2_contact_sheet.png
- review_v2/tiles_core_live_v2_contact_sheet.png
- review_v2/world_buildout_live_v2_contact_sheet.png

Notes
- The source generator is now the baseline for future Pertinence content growth; emitted JSON should not be hand-edited unless there is a one-off emergency fix.
- The world-buildout set and the expanded combat/FX set now exist together for manual art-direction review and gameplay-facing integration.