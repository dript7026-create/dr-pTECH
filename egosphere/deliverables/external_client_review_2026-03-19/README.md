# egosphere External Client Review

Prepared for the current review snapshot on 2026-03-19.

Use `DEPLOYMENT_STATUS.json` for current rebuild context and artifact paths.
Use `VALIDATION_SNAPSHOT.json` for the underlying validated technical snapshot.

This package is a curated review snapshot for the egosphere repository. It is intended to give an external client a fast, defensible overview of what is present, what was validated, and which artifacts are the correct entry points for review.

## Review Scope

- Core egosphere module for lightweight gameplay cognition, persistent rival memory, replay rehearsal, player-style modeling, dialogue and consequence tracking, resonance state, dormant narrative pressure, and save inspection.
- Manifest-driven authoring pipeline that emits integration bundles for Clip Studio Paint, Blender, and idTech2-oriented downstream tooling.
- Current validated sample pipeline output.
- Current validated Pertinence Tribunal scaled validation example for content volume and bundle generation.

## Current Validation Status

- Core smoke test: passed.
- Full pipeline validation suite: passed.
- Demo runtime save/load snapshot: passed.

See `VALIDATION_SNAPSHOT.json` for the exact validated counts, command results, and current demo-runtime snapshot captured for this package.

## Recommended Review Order

1. `HANDOFF_NOTE.md`
2. `CLIENT_PRESENTATION_SCRIPT.md`
3. `CLIENT_EXEC_SUMMARY.md`
4. `PRODUCT_BRIEF.md`
5. `PACKAGE_MANIFEST.json`
6. `REVIEW_GUIDE.md`
7. `repo\README.md`
8. `repo\pipeline\README.md`
9. `repo\egosphere.h`
10. `repo\pipeline\sample_project\game_project.json`
11. `repo\pipeline\sample_project\game_project.drip3d.json`
12. `repo\pipeline\out\validation\`
13. `repo\pipeline\projects\pertinence_tribunal\`
14. `repo\pipeline\out\pertinence_tribunal_validation\`

## Known Notes

- Historical Pertinence handoff notes reference contact-sheet review images under `review/` and `review_v2/`, but those folders are currently empty in the repository snapshot used to assemble this package.
- Some legacy markdown files in the repository have markdown-lint formatting issues. Those issues do not affect the validated build and pipeline outputs included here.
- This package is review-oriented. It is not a legal, financial, or production-signoff document.

## Package Intent

The goal is to reduce client review friction:

- one clear starting point;
- one executive summary for non-implementation review;
- one short product-definition page;
- one current validation snapshot;
- a bounded set of source, manifest, and generated artifacts;
- explicit notes where repository history and present-state artifacts diverge;
- one short-notice deployment checklist for rapid rebuilds.

For a fast product summary before reviewing source and generated outputs, start with `PRODUCT_BRIEF.md`.
For a non-technical stakeholder pass, start with `CLIENT_EXEC_SUMMARY.md`.
For a live meeting walkthrough, start with `CLIENT_PRESENTATION_SCRIPT.md`.
For the fastest external handoff, start with `HANDOFF_NOTE.md`.
For a self-describing package inventory, use `PACKAGE_MANIFEST.json`.
For short-notice handoff, prefer the stable archive path `deliverables\external_client_review_latest.zip`.
