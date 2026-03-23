# drIpTECH Stack Architecture

## Intent

This document defines the current intended relationship between the major drIpTECH software layers so development can converge on one coherent stack instead of multiple overlapping prototypes.

## Primary Layers

### 1. Authoring Layer

Purpose:
- create 2D source art, concept-book packages, prompt metadata, and conversion-ready assets

Primary components:
- `drIpTech_ClipStudio_Plug-Ins/`
- `drIpTECHBlenderPlug-Ins/TxTUR/`
- `drIpTECH/ReCraftGenerationStreamline/`
- `egosphere/tools/game_pipeline.py`

Responsibilities:
- package authored concept material into stable `.ccp` containers
- carry prompt and page metadata forward into downstream generation and conversion
- turn 2D-authored assets into Blender-ready and runtime-ready bundles

Key outputs:
- concept-book bundles
- Blender conversion manifests
- runtime asset bundles

### 2. AI Runtime Layer

Purpose:
- host inspectable local AI-adjacent simulation, directive processing, and control interfaces

Primary components:
- `NeoWakeUP/neowakeup/planetary/`
- `NeoWakeUP/neowakeup/relationships.py`
- `NeoWakeUP/neowakeup/qaijockey/`
- `NeoWakeUP/neowakeup/api_server.py`
- `drIpTECH/NaVi_AI_real-timeintercedencemodule/`

Responsibilities:
- process directives into explicit simulation state
- expose local HTTP state and stepping surfaces
- support relationship-aware or preference-aware behavior modulation
- optionally intercede on upstream AI calls through NaVi when that path is justified

Key outputs:
- machine-readable simulation state
- directive-response reports
- local API endpoints for engine and tool consumers

### 3. Engine Layer

Purpose:
- present authored worlds and simulations as playable or navigable runtime experiences

Primary components:
- `ORBEngine/`
- `ArchesAndAngels/`
- `skazka_terranova_c/`

Responsibilities:
- `ORBEngine`: signature presentation runtime for pseudo-3D and recursive-space scenes
- `ArchesAndAngels`: strategy simulation and mission-generation testbed
- `skazka_terranova_c`: broader gameplay and SDL/C runtime experimentation

Key outputs:
- engine-side demos
- mission and state exports
- gameplay-facing vertical slices

### 4. Orchestration and Packaging Layer

Purpose:
- build, package, launch, and observe the stack

Primary components:
- `DoENGINE/`
- `workspace_build.py`
- `workspace_build.ps1`
- `tools/workspace_health.py`

Responsibilities:
- normalize build and launch flows
- provide telemetry and backup-aware packaging hooks
- select or launch runtime components in a controlled way

Key outputs:
- repeatable build artifacts
- launch surfaces
- operational metadata

## Data Flow

### Authoring to runtime

1. Clip Studio source pages and prompt metadata are packaged into concept-book or manifest form.
2. Blender-side conversion tooling translates those assets into geometry, rig, material, or bundle-ready outputs.
3. Runtime bundles are handed to engine-side consumers such as ORBEngine or downstream game projects.

### Simulation to gameplay

1. NeoWakeUP produces directive-aware simulation state.
2. ArchesAndAngels produces faction, district, scenario, mission, and campaign state.
3. Engine consumers ingest machine-readable outputs from those systems for visualization, mission loading, or dynamic world conditions.

### Packaging to distribution

1. DoENGINE and workspace build scripts collect the relevant runtime pieces.
2. Build/test/telemetry metadata is attached.
3. The selected demo or product slice is packaged for internal use, public preview, or lender-facing review.

## Near-Term Integration Contract

### ArchesAndAngels export contract

ArchesAndAngels should expose a machine-readable campaign export containing:
- campaign summary
- districts
- scenarios
- agendas
- missions
- protagonists
- incidents

This export becomes the first engine-facing content contract for ORBEngine and DoENGINE.

### NeoWakeUP API contract

NeoWakeUP should maintain a stable local API surface with at least:
- `GET /health`
- `GET /models`
- `GET /planetary/state`
- `POST /planetary/step`

This API is the first shared runtime-control surface for downstream consumers.

### ORBEngine ingestion contract

ORBEngine should be able to consume:
- authored asset bundles from the Clip Studio and Blender pipeline
- exported mission or scenario state from ArchesAndAngels
- optional directive/state overlays from NeoWakeUP

## Current Canonical Stack Decision

For the next working phase, the canonical stack is:

1. Clip Studio and Blender plug-ins for authoring.
2. NeoWakeUP for AI runtime and simulation.
3. ArchesAndAngels for strategy-state and mission-state generation.
4. ORBEngine for presentation and runtime demoing.
5. DoENGINE for orchestration, packaging, and launcher control.

## Immediate Technical Priorities

1. Keep ArchesAndAngels exportable to JSON.
2. Add smoke tests for NeoWakeUP API and ORBEngine tutorial build.
3. Make ORBEngine ingest exported ArchesAndAngels data.
4. Document the authoring-to-runtime pipeline in one reproducible path.
5. Use DoENGINE to package one cross-stack vertical slice once the above is working.