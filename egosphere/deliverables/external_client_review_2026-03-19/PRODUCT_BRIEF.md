# egosphere Product Brief

Prepared for the current review snapshot on 2026-03-19.

Use `DEPLOYMENT_STATUS.json` for current rebuild context.
Use `VALIDATION_SNAPSHOT.json` for the validated technical snapshot date and results.

## Product Definition

egosphere is a reusable C gameplay cognition module plus a deterministic authoring pipeline.

The runtime side is designed for games that need lightweight, inspectable behavioral state instead of opaque black-box AI. The pipeline side is designed to take a single manifest-driven source of truth and emit integration bundles for downstream art and engine tooling.

## What Is Proven In This Package

- A portable C API for persistent rival-memory and gameplay cognition.
- Save/load of rivalary state.
- Replay rehearsal against stored outcomes.
- Player-style, dialogue, and consequence inputs feeding the same systemic state model.
- Resonance and dormant narrative-pressure fields present in the public runtime model.
- Deterministic pipeline bundle generation for Clip Studio, Blender, and idTech2-oriented integration targets.
- One suite-based validator covering the sample pipeline and the larger-scale Pertinence Tribunal validation run.

## What The Core Runtime Does

- tracks recurring rivals as inspectable gameplay identities;
- records outcomes, tactical tendencies, and moral-history signals;
- supports player-profile participation in the same memory model;
- exposes resonance and dormant narrative hooks for games that want to consume them later;
- persists state to disk and rehydrates it for later sessions;
- provides replay rehearsal helpers so stored history can shape later action choice.

## What The Pipeline Does

- accepts a canonical manifest and a drIpTECH scene source format;
- emits Clip Studio bundle metadata;
- emits Blender conversion and ingest-helper artifacts;
- emits idTech2-oriented manifests and generated native glue;
- validates expected outputs through deterministic build checks.

## What This Package Does Not Claim

- It does not claim finished in-repo host integration for every downstream tool.
- It does not claim production signoff.
- It does not claim that the Pertinence Tribunal example is the core product; it is a scaled validation example.

## Review Lens

Review egosphere as software with two linked surfaces:

1. a reusable runtime cognition module;
2. a manifest-driven bundle-generation pipeline.

Review Pertinence Tribunal as the current proof that the pipeline and package structure can carry a larger content set.

Use `HANDOFF_NOTE.md` if the reviewer needs a one-page orientation before reading deeper material.
