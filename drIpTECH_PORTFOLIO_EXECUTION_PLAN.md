# drIpTECH Portfolio Execution Plan

## Purpose

This document turns the current workspace into a practical execution roadmap across:

- AI software
- game engines
- tools and content pipelines
- creator plug-ins
- shared systems and infrastructure
- hardware and device strategy

It is written as an operating plan for the next working phase, not as a brand manifesto. The goal is to reduce sprawl, identify the core stack, and sequence delivery so the portfolio can produce usable software, credible demos, and lender-ready business artifacts.

## Current Portfolio Map

### AI Software

- `NeoWakeUP/`
  - active AI runtime home
  - planetary simulation, relationship modeling, QAIJockey runtime, control hub, local API server
- `drIpTECH/NaVi_AI_real-timeintercedencemodule/`
  - proxy/intercession layer for upstream AI calls
  - logging, hook points, genetic-policy stubs
- `readAIpolish/`
  - graphics-polish helper layer used inside asset automation flows
- `egosphere/`
  - interpersonal and state-modeling logic that already informs NeoWakeUP relationships

### Engines

- `ORBEngine/`
  - pseudo-3D recursive-space renderer and simulation sandbox
  - strongest candidate for the distinctive drIpTECH world-presentation layer
- `DoENGINE/`
  - orchestration and tooling workspace with telemetry, encryption, hybrid-engine, bango-target, and launcher direction
- `ArchesAndAngels/`
  - strategic simulation prototype with operations, agendas, scenarios, policies, and missions
- `skazka_terranova_c/`
  - larger C game base with SDL and cross-platform groundwork

### Tools and Pipelines

- `workspace_build.py` and `workspace_build.ps1`
  - shared build matrix entrypoint
- `tools/`
  - workspace health, manifest tooling, general scripts
- `egosphere/tools/`
  - Clip Studio to Blender to idTech2 bundle generation pipeline
- `bango-patoot_3DS/tools/`
  - autorig and Blender automation tied to TxTUR and BlendNow
- `drIpTECH/ReCraftGenerationStreamline/`
  - manifest-driven generation infrastructure

### Plug-ins and Creator Extensions

- `drIpTech_ClipStudio_Plug-Ins/`
  - native C prototype for brushes, timeline helpers, symbol/script linkage, and concept-book packaging
- `drIpTECHBlenderPlug-Ins/TxTUR/`
  - Blender add-ons, TxTUR bridge, BlendNow, DripCraft, autorig helpers
- `drIpTECH_idTech2Plug-Ins/`
  - idTech2-side extension area for ingest and runtime bridging

### Shared Systems

- workspace dependency manifests and scoped installers
- test harness under `tests/` plus project-scoped test folders
- traces, forensic artifacts, and hardware/toolchain recovery assets under `traces/`
- optional bridge and control metadata under `.copilot_bridge/`, `.vscode/`, and project-specific manifests

### Hardware Direction

- NanoPlay_t concept track now documented under `ArchesAndAngels/NANOPLAYT_PLAYHUB_STRATEGY.md`
- hardware-adjacent evidence already exists in `traces/`, devkitPro tooling, controller-driven game slices, and the Blender-to-runtime asset pipeline
- realistic near-term hardware work should be framed as device-enablement and pilot prototyping, not fully custom platform invention

## Core Stack Decision

The workspace is too broad to mature as a flat multi-project field. The next step is to designate a core stack and treat everything else as feeders, experiments, or later branches.

### Core stack

1. `NeoWakeUP` as the AI runtime and simulation layer.
2. `ORBEngine` as the signature presentation and world-rendering layer.
3. `DoENGINE` as orchestration, tooling, packaging, telemetry, and launcher infrastructure.
4. `drIpTech_ClipStudio_Plug-Ins` plus `drIpTECHBlenderPlug-Ins/TxTUR` as the authoring and conversion toolchain.
5. `ArchesAndAngels` and selected game projects as product-facing vertical slices built on top of the stack.

### Supporting or feeder projects

- `egosphere` for relationship and state logic
- `readAIpolish` for asset refinement helpers
- `bango-patoot_3DS` for automation and rigging experiments
- `skazka_terranova_c` for larger C/SDL gameplay learnings

## Immediate Execution Principles

- Prefer one shared runtime path over multiple overlapping AI runtimes.
- Prefer one engine presentation thesis over several unrelated rendering experiments.
- Make authoring pipelines deterministic and inspectable.
- Turn prototypes into repeatable build-and-test units before adding more feature surfaces.
- Push toolchain discipline first, then packaging, then public demos, then hardware pilots.

## 90-Day Program

## Phase 1: Stabilize the Stack

Target: next 2 to 3 weeks.

### AI software

- consolidate any new AI runtime work into `NeoWakeUP`
- define one stable local API contract between NeoWakeUP and engine-side consumers
- turn NaVi into an optional policy/intercession service rather than a separate product center
- add one metrics definition for preference fidelity, latency, and safety-reviewed intervention behavior

### Engines

- choose one near-term flagship engine demo: `ORBEngine`
- keep `DoENGINE` focused on orchestration and packaging rather than competing render logic
- keep `ArchesAndAngels` as the strategy-sim content testbed and mission generator

### Tools and plug-ins

- freeze the current ClipConceptBook `.ccp` format as the authored-concept package format
- freeze the TxTUR / BlendNow / DripCraft handoff contract for Blender automation
- add a project manifest that describes the full Clip Studio to Blender to runtime flow in one place

### Systems

- add missing automated smoke tests for the core stack
- make sure each core stack project has a README with build/run/test commands
- normalize output folders and artifact names so builds are auditable

Deliverables:

- one stack diagram
- one local API contract doc
- one end-to-end asset pipeline spec
- one smoke-test suite spanning NeoWakeUP, ORBEngine, and ArchesAndAngels

## Phase 2: Build the Vertical Slice

Target: weeks 4 to 8.

### Flagship slice

Use `ArchesAndAngels` as the first cross-stack slice because it already has:

- world premise
- strategic simulation
- missions and protagonists
- NanoPlay_t and PlayHub framing

### Work items

- export scenario and mission data from `ArchesAndAngels` in a machine-readable form
- feed that output into an `ORBEngine` presentation prototype
- use NeoWakeUP as the live directive and simulation coprocessor where appropriate
- package the slice through DoENGINE launch tooling

### Plug-in work

- use ClipConceptBook `.ccp` to package authored visual references and prompt metadata
- run Blender automation from TxTUR / BlendNow against a single controlled asset set
- document the exact path from concept pages to runtime-ready package

Deliverables:

- one playable or watchable ArchesAndAngels vertical slice
- one recorded pipeline pass from concept-book to runtime assets
- one packaged launcher flow through DoENGINE

## Phase 3: Public-Facing and Lender-Facing Materials

Target: weeks 9 to 12.

### Product materials

- public portfolio page or repo summary for the core stack
- sanitized screenshots and clips from NeoWakeUP, ORBEngine, and the vertical slice
- concise technical summaries for each core project

### Business materials

- 12-month budget and cashflow model
- debt-aware financing note using the user-provided constraints already discussed
- hardware pilot scope for NanoPlay_t framed as a limited off-the-shelf Linux handheld pilot
- software-first revenue path via PlayHub / DripDungeons-style releases

Deliverables:

- lender deck outline
- budget sheet
- core-stack one-pager
- hardware pilot specification sheet

## Project-Specific Next Steps

### NeoWakeUP

- formalize API schema for planetary state, directives, and node inspection
- add project-scoped tests for API and control hub smoke behavior
- define how relationship signals feed game/runtime systems without overcomplicating the simulation layer

### ORBEngine

- select one demo branch as the primary branch for the next cycle
- define a data-ingest format that can consume outputs from the Blender toolchain and ArchesAndAngels mission data
- add one automated build smoke test for the primary demo executable

### DoENGINE

- restore Node toolchain and typecheck path
- decide packaging role: launcher, registry, orchestration, or all three
- reduce placeholder providers and stabilize config for backup roots and runtime selection

### Clip Studio Plug-ins

- separate the native prototype layer from host-integration plans
- implement one real non-stub feature to prove value, likely inbetween stroke interpolation or concept-book packaging UX
- document memory ownership, build, and packaging requirements

### Blender Plug-ins

- document TxTUR, BlendNow, and DripCraft responsibilities in one file
- make the Bango autorig pipeline reproducible from a single command
- treat generated bundles as outputs, not hand-maintained assets

### ArchesAndAngels

- export simulation state to JSON or a similar bridgeable format
- connect one mission board output to a traversal or tactical layer mockup
- keep it as the first flagship cross-stack product testbed

## Hardware Plan

The near-term hardware program should be framed as three practical layers.

### Layer 1: Device enablement

- controller support
- suspend/resume assumptions
- low-power rendering targets
- small-display UI rules
- offline-first save and update logic

### Layer 2: Pilot prototyping

- choose off-the-shelf Linux handheld architecture
- define display, battery, input, and enclosure constraints
- produce one software image and launcher shell concept

### Layer 3: Business readiness

- quote first 1,000-unit pilot range
- isolate debt cleanup from product capital accounting
- prepare lender-facing hardware risk note

## What Not to Do Next

- do not start a fresh custom engine in parallel with ORBEngine and DoENGINE
- do not start a fresh AI runtime outside NeoWakeUP
- do not expand hardware ambition into custom silicon or a bespoke OS fork yet
- do not add more experimental projects to the core stack until the first vertical slice is packaged and testable

## Operating Sequence

1. Stabilize the core stack.
2. Produce one cross-stack vertical slice.
3. Produce lender-ready and public-facing materials from that slice.
4. Only then increase hardware scope or portfolio breadth.

## Immediate Action Queue

1. Write a stack architecture doc connecting NeoWakeUP, ORBEngine, DoENGINE, the plug-in pipeline, and ArchesAndAngels.
2. Add a machine-readable export path from ArchesAndAngels to engine-side consumers.
3. Add smoke tests for NeoWakeUP API and one ORBEngine build target.
4. Document the TxTUR / BlendNow / DripCraft pipeline as one reproducible toolchain.
5. Build a lender-ready budget and milestone sheet using the NanoPlay_t and PlayHub strategy as the base.

Current status:
- item 1 completed in `drIpTECH_STACK_ARCHITECTURE.md`
- item 2 completed through the ArchesAndAngels `--json-out` export path
- item 3 completed through focused smoke tests in `tests/`