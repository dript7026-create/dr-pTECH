Date: 2026-03-11
Project: Pertinence: Tribunal
Source run: full live Recraft pass from recraft_manifest.json

Summary
- The live Recraft pass completed successfully for all 72 requested assets.
- The egosphere live bundle rebuild also completed successfully.
- Blender ingest still dry-runs cleanly outside Blender with 32 scenes and 58 lifts.
- idTech2 live bundle summary remained stable at 72 assets, 72 precaches, 5 systems, and 14 entities.

Objective review notes
- Sprite transparency compliance is mostly good but not complete.
- 52 of 58 sprites contain transparency.
- 6 of 58 sprites are fully opaque even though the sprite prompts asked for transparent backgrounds.
- Tiles and portraits being fully opaque is expected for this pack and is not treated as a defect.

Highest-priority refinement targets
- Opaque sprites that should be rerun with a stricter transparency instruction:
  - kier_rat_ronin
  - village_elder
  - rope_ferryman
  - archive_child
  - penitent_poet
  - salt_toad
- Sparse or low-fill sprites that are likely underutilizing the sheet and should be rerun with stronger framing / silhouette instructions:
  - goduly_ink_saint
  - vermin_lantern
  - reed_sapper
  - tar_crow
  - goduly_fallow_crown
  - pale_usher

Heuristic basis
- Lowest alpha coverage observed among sprites:
  - goduly_ink_saint: 0.0851
  - vermin_lantern: 0.2192
  - reed_sapper: 0.2481
  - tar_crow: 0.3501
  - goduly_fallow_crown: 0.3542
  - pale_usher: 0.3561
- Fully opaque sprite count: 6

Refinement guidance
- Keep sprites isolated on a fully transparent background.
- Explicitly forbid backdrop, floor plane, decorative framing, fog bank, or painted environment behind the character.
- Ask for the character or creature to occupy more of the canvas so the sheet is denser and easier to lift into the current pipeline.
- Preserve the existing color and thematic direction unless a later art pass chooses to revise style globally.

Queued follow-up
- See recraft_refinement_pass1_manifest.json for the ready-to-run second-pass subset.
- Estimated additional cost for that subset is 480 units.

Completed refinement outcome
- The 12-item refinement pass was executed successfully with 12 successes and 0 failures.
- All 12 refined outputs scored as improvements over their originals using the same transparency and coverage heuristics.
- The improved reruns were promoted into the live sprite paths.
- Original pre-refinement sprite files were preserved under `authoring/clipstudio/sprites/_backup_refinement_pass1/`.
- After promotion, the live project has 0 fully opaque sprites and 0 sprite sheets below the 0.35 coverage threshold used in this review.
- The egosphere live bundles were rebuilt again after promotion and Blender ingest still dry-runs cleanly with 32 scenes and 58 lifts.

Artifacts
- refinement log: `recraft_refinement_pass1_log.txt`
- refinement ledger: `recraft_refinement_pass1_ledger.csv`