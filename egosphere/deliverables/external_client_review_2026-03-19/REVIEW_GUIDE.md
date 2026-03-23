# Review Guide

## What egosphere is

egosphere currently has two reviewable layers:

1. A reusable C gameplay cognition module centered on persistent rivals, inspectable psyche state, replay rehearsal, player-style modeling, dialogue and consequence memory, resonance, and optional dormant narrative pressure.
2. A data-driven content pipeline that deterministically emits downstream integration bundles for Clip Studio, Blender, and idTech2-oriented tooling.

Pertinence Tribunal is included as a scaled validation example for the pipeline and review surface. It is not the core product itself.

## What to evaluate

### Core module

Focus on:

- API clarity and portability in `repo\egosphere.h`
- implementation coherence in `repo\egosphere.c`
- persistence and rehearsal coverage in `repo\smoke_test.c`
- save inspection utility in `repo\tools\inspect_mindsphere_save.py`

Specifically confirm that the explanation matches the implemented surface: rival persistence, player modeling, resonance links, dialogue/consequence tracking, narrative hooks, save/load, and replay rehearsal.

Questions to ask:

- Is the public API small enough to integrate cleanly into another game project?
- Do the persisted fields align with the intended rival-memory design?
- Is the smoke path sufficient for confidence in save/load and replay rehearsal behavior?

### Pipeline layer

Focus on:

- canonical manifest shape in `repo\pipeline\sample_project\game_project.json`
- proprietary source scene format in `repo\pipeline\sample_project\game_project.drip3d.json`
- generator behavior in `repo\tools\game_pipeline.py` and `repo\tools\drip3d_pipeline.py`
- generated outputs under `repo\pipeline\out\validation\`

Treat the validated surface here as bundle generation and dry-run verification. The package does not claim that full host-side Clip Studio or Blender integrations are completed in this repository snapshot.

Questions to ask:

- Is the manifest expressive enough for real project use?
- Are the generated outputs deterministic and legible?
- Does the bundle split map cleanly onto the target toolchain responsibilities?

### Pertinence Tribunal example

Focus on:

- source content and manifests under `repo\pipeline\projects\pertinence_tribunal\`
- validated generated outputs under `repo\pipeline\out\pertinence_tribunal_validation\`
- project generator and validation runner in `repo\tools\build_pertinence_test_pack.py` and `repo\tools\run_pertinence_e2e.py`

Questions to ask:

- Does this example prove the pipeline can carry a larger-scale content set?
- Are the generated counts and bundle outputs credible for downstream review?
- Is the project documentation good enough for handoff without walking the client through the source code live?

This section should be reviewed as evidence of scale and artifact quality, not as the product definition.

## Suggested Review Session Structure

1. Read `HANDOFF_NOTE.md` for package framing.
2. Read the top-level README for system intent.
3. Review the core C API and smoke test.
4. Review the sample manifest and the generated validation bundle.
5. Review Pertinence Tribunal as the scaled example.
6. Finish with the validation snapshot to confirm current status.

## Current Risks Worth Calling Out

- The Pertinence review-image folders referenced in prior notes are not populated in the current repo snapshot.
- The repo contains multiple exploratory branches of work; this package narrows review to the subset represented by `VALIDATION_SNAPSHOT.json`.
- Some documentation around Pertinence was generated quickly and is better treated as design-support material than polished client-facing narrative.
