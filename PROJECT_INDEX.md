# Project Index

This workspace is a multi-project monorepo. The public mirror is subdivided by responsibility so maintenance stays tractable even though the codebase spans many experiments.

## Runtime And Engine Work

- `DoENGINE/` for engine/runtime packages and related orchestration work
- `egosphere/` for pipeline validation, asset generation, and runtime experiments
- `ORBEngine/` and `NeoWakeUP/` for engine-adjacent runtime prototypes and supporting systems

## Games And Playable Prototypes

- `KaijuGaiden/`, `tommybeta/`, `tommygoomba/`, `WialWohm/`, `orbseeker/`, `zipSongAI/`
- project-local READMEs and build scripts define the supported public surface for each prototype

## Creative Tooling And Pipelines

- `drIpTECHBlenderPlug-Ins/`, `drIpTech_ClipStudio_Plug-Ins/`, `readAIpolish/`, and `tools/`
- shared manifests under `tools/dependency_manifests/` describe optional stacks without forcing them into the root environment

## Analysis, Data, And Utilities

- `football_predictor/`, `speech_to_text_google/`, `userprofiling/`, and smaller focused utilities
- keep datasets, reports, and generated outputs trimmed to what is required for reproducible tests or examples

## Maintenance Boundary

- root-level docs should explain the public repo contract, not private financing or internal operator process
- project-specific strategic planning should live outside the public mirror unless it is needed to build, test, or govern the published code