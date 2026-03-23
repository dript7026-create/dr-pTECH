# DoENGINE

DoENGINE is the dedicated recovered workspace for the D-drive `doengine-backup` snapshot. This normalized hierarchy turns the backup into a clean package-first project structure instead of leaving it as a flat recovery dump.

## Workspace Layout

- `packages/core/src/` — runtime engine entrypoints and orchestration.
- `packages/encryption/src/` — encryption primitives and trace protection.
- `packages/shared/src/` — shared engine, trace, and bridge contracts.
- `packages/telemetry/src/` — trace writing, metadata emission, and backup-facing I/O.
- `packages/bango-target/src/` — normalized TypeScript reintegration of the Bango engine-target bridge.
- `packages/hybrid-engine/src/` — cross-DoENGINE and ORBEngine runtime profile builder for DODOGame-hosted hybrid rendering.
- `packages/donow/src/` — DoENGINE automated implementation module for clip-blend-id runtime ingest.
- `apps/` — standalone DoENGINE GUI application sources.
- `tools/` — Python-side manifest and runtime builders for DoENGINE operations.
- `docs/philosophy/` — theory, nomenclature, and hardware-trace concepts.
- `docs/metadata/` — reintegration notes and metadata contracts.
- `docs/migration/` — source backup snapshots and migration mapping.
- `ops/backup/` — threefold backup tiers and scripts.
- `.github/` — workspace-specific Copilot instructions.

## Recovery Source

The source snapshot was recovered from `D:\doengine-backup` and preserved as read-only reference material under `docs/migration/`.

## DODO 3D Runtime

`apps/dodogame.py` now includes an embedded `Illusion 3D` viewport driven by `apps/dodo_engine3d.py`. The renderer is a mesh-and-camera pipeline with shader-style passes for sky gradient, floor warp, stepped lambert/rim lighting, fog, and scanline/canvas grain so the output lands in the intended IllusionCanvas pseudo-3D space instead of a flat launcher mockup.

The renderer also supports manifest-driven scene loading, billboard cards, lightweight script directives, OBJ mesh ingestion, and binary glTF (`.glb`) mesh ingestion so DODO can present an actual BangoNOW pipeline gallery instead of only a hard-coded tech demo. `tools/build_bangonow_showcase.py` scans the best playable BangoNOW package it can find and emits a scene manifest consumed by the launcher. When a real BangoNOW `player_glb` is present, the showcase now instantiates that asset directly instead of falling back to a proxy monolith.

For headless validation or artifact export:

`python apps/dodogame.py --render-engine-preview generated/dodogame_gui/dodo_engine_preview.png`

That writes both a PNG preview and a sibling JSON report describing the active shader stack and scene stats.

## Demo Hub Adaptive Prototype

`apps/demo_hub.py` is a standalone Tk prototype for the Adaptive Resonance Hub direction. It exposes:

- a shared adaptive contract for NanoPlay_t and PlayHub
- provisional high-, mid-, and low-response spectral routing windows
- haptic fiber feedback profiles
- wireless-isolation and no-backdoor local transport assumptions
- runtime-state and recommendation snapshots for the PlayHub and NanoPlay_t profiles

Launch options:

- `python apps/demo_hub.py`
- `python apps/demo_hub.py --dump-state`
- `DemoHub.cmd`

## Next Reintegration Steps

1. Restore a working Node.js toolchain on this machine so `npm install` and `npm run typecheck` can execute inside `DoENGINE/`.
2. Replace placeholder hardware/session key generation with deterministic providers.
3. Wire `packages/bango-target` and `packages/donow` into a higher-level package registry or runtime selection layer.
4. Iterate the standalone GUI in `apps/doengine_studio.py`, the DODOGame launcher in `apps/dodogame.py`, and their Windows launchers once the preferred packaging strategy for a compiled `.exe` is available.
5. Decide whether the threefold backup stays inside the repo workspace or moves to a configured external root via `DOENGINE_BACKUP_ROOT`.
