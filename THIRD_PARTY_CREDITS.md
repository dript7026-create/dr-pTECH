# Third-Party Credits

This workspace uses a mix of original code, generated assets, and external open-source tooling. This file is the canonical place to record third-party engines, SDKs, runtimes, and DCC tools that materially shape builds, runtime behavior, or asset conversion.

Attribution rule:

- When a project starts depending on a new external tool, engine, SDK, or library, add it here.
- Add or update the matching entry under `tools/dependency_manifests/` when the dependency is project-scoped.
- If code, assets, or notices are vendored locally, keep the upstream license or notice text with the vendored content.
- Do not imply ownership of upstream engines, SDKs, or editor technology.

Related records:

- Python package license inventory: `pip_licenses.md`
- Machine-readable open-source 3D/runtime stack manifest: `tools/dependency_manifests/open_source_3d_stack.json`
- Machine-readable live football/weather source manifest: `tools/dependency_manifests/football_live_data_sources.json`

## Open-source 3D and engine stack

### Blender

- Upstream: Blender Foundation and Blender contributors
- Site: <https://www.blender.org/>
- Use here: asset conversion, Blender-side ingest helpers, rig/material pipeline work, and pseudo-3D lift/extrusion workflows in `egosphere/`, `drIpTECHBlenderPlug-Ins/`, and related pipeline tooling.
- Notes: Blender-provided Python modules such as `bpy`, `bmesh`, and `mathutils` come from Blender's embedded Python runtime, not the workspace venv.

### id Tech 2 / Quake II source release

- Upstream: id Software and open-source maintainers building on the released codebase
- Site: <https://github.com/id-Software/Quake-2>
- Use here: idTech2-facing runtime registries, generated glue code, mod/bootstrap targets, and engine integration experiments in `egosphere/`, `bango-patoot_3DS/`, and related projects.
- Notes: credit applies to the engine/runtime lineage only. Do not claim ownership of the upstream engine or original game assets.

## Supporting open-source runtime and toolchain stack

### SDL2

- Upstream: Sam Lantinga and SDL contributors
- Site: <https://www.libsdl.org/>
- Use here: host runtime windowing, rendering, audio, and input paths such as the `TARGET_HOST` path in `KaijuGaiden/kaijugaiden.c`.

### GBDK-2020

- Upstream: GBDK contributors
- Site: <https://github.com/gbdk-2020/gbdk-2020>
- Use here: original Game Boy builds and APIs referenced by `KaijuGaiden` and other GB-targeted work.

### devkitARM / libgba

- Upstream: devkitPro, devkitARM, and libgba contributors
- Site: <https://devkitpro.org/>
- Use here: Game Boy Advance build targets and APIs referenced by `KaijuGaiden` and related handheld prototypes.

## Live football and forecast data sources

### football-data.org

- Upstream: football-data.org
- Site: <https://www.football-data.org/>
- Use here: live and scheduled football match synchronization for `football_predictor/live_data.py` and `football_predictor/predict_live.py`.
- Notes: access is plan- and key-dependent. Coverage and rate limits come from the upstream service, not this workspace.

### TheSportsDB

- Upstream: TheSportsDB
- Site: <https://www.thesportsdb.com/>
- Use here: supplementary football event schedule and season sync paths for `football_predictor/live_data.py`.
- Notes: free and premium tiers differ. Any coverage, freshness, or API limits come from the upstream provider.

### OpenWeather One Call API 3.0

- Upstream: OpenWeather
- Site: <https://openweathermap.org/api/one-call-3>
- Use here: optional weather severity adjustments and weather-aware forecast context in `football_predictor/weather.py` and `football_predictor/predict_live.py`.
- Notes: weather calls are optional and key-dependent. The predictor uses this only as contextual input, not as a guarantee engine.

## Maintenance checklist

- Add the upstream project name, home page, and where it is used.
- Add a project-scoped manifest entry if the dependency is not workspace-wide.
- Add README notes near the project that uses the dependency.
- Preserve any upstream notice files when binaries, SDKs, or source snapshots are checked in.
