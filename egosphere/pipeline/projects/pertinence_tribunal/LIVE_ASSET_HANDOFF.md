Date: 2026-03-11
Project: Pertinence: Tribunal

Status
- Live Recraft generation completed for the base 72-item pack.
- A 12-item refinement batch was completed and promoted into the live sprite set.
- The live egosphere bundles were rebuilt after promotion.

Current live quality state
- Sprite count: 58
- Tile count: 8
- Portrait count: 6
- Fully opaque sprite count: 0
- Sprite sheets below 0.35 alpha coverage threshold: 0

Downstream validation snapshot
- Blender ingest dry-run: 32 scenes, 58 lifts
- idTech2 manifest: 72 assets, 72 precaches, 5 systems, 14 entities
- Live bundle paths:
  - egosphere/pipeline/out/pertinence_tribunal_live/clipstudio_bundle/clipstudio_export.json
  - egosphere/pipeline/out/pertinence_tribunal_live/blender_bundle/blender_conversion.json
  - egosphere/pipeline/out/pertinence_tribunal_live/idtech2_bundle/idtech2_manifest.json

Review artifacts
- review/sprites_contact_sheet.png
- review/tiles_contact_sheet.png
- review/portraits_contact_sheet.png
- RECRAFT_REFINEMENT_REVIEW.md
- recraft_generation_log.txt
- recraft_generation_ledger.csv
- recraft_refinement_pass1_log.txt
- recraft_refinement_pass1_ledger.csv

Backup and promotion details
- Replaced originals were backed up under authoring/clipstudio/sprites/_backup_refinement_pass1/
- Promoted refined sprites:
  - kier_rat_ronin
  - village_elder
  - rope_ferryman
  - archive_child
  - penitent_poet
  - salt_toad
  - goduly_ink_saint
  - vermin_lantern
  - reed_sapper
  - tar_crow
  - goduly_fallow_crown
  - pale_usher

Recommended next integration step
- Use the live idTech2 bundle as the current gameplay-facing baseline.
- Use the contact sheets for art-direction review before any style-only reruns.
- If gameplay wiring begins immediately, treat the current promoted sprite set as canonical until a later aesthetic pass explicitly replaces it.