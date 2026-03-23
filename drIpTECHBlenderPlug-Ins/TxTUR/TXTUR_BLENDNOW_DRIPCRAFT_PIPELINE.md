<!-- markdownlint-disable MD032 MD047 -->

# TxTUR, BlendNow, and DripCraft Pipeline

## Purpose

This document defines the current intended handoff between the three Blender-side toolchain components in `drIpTECHBlenderPlug-Ins/TxTUR/`.

The goal is to stop treating them as overlapping experiments and instead use them as one staged authoring pipeline.

## Roles

### TxTUR

Primary role:
- trial-layer texture, surface, and NodeCraft bridge inside Blender

Current artifacts:
- `blenderTxTUR.c`
- `blender_txtur_addon.py`
- `blenderTxTUR.dll`

Current function:
- exposes a C bridge and Blender UI scaffold for brush presets, surface mappings, and a NodeCraft graph concept
- best used as the lightweight in-Blender experimentation and projection layer

Current limitation:
- not yet a fully integrated production Blender tool with robust mesh or texture mutation logic

### BlendNow

Primary role:
- VIP conversion-plan and import-spec authoring layer

Current artifacts:
- `BlendNow_core.py`
- `BlendNow_addon.py`

Current function:
- emits structured JSON handoff files such as `BlendNow_TxTUR_conversion_plan.json` and `BlendNow_TxTUR_import_spec.json`
- defines the formal scene, rig, material, and NodeCraft import contract for the Blender side of the pipeline

Current limitation:
- still mostly a structured handoff and packaging layer, not the whole runtime ingest itself

### DripCraft

Primary role:
- pipeline execution bridge between generated images, local conversion CLI, readAIpolish, and `.blend` output

Current artifacts:
- `DripCraft_addon.py`
- `DripCraft.c`

Current function:
- orchestrates optional Recraft generation, DripCraft CLI conversion, readAIpolish refinement, image import, and Blender scene save
- best used as the operator-level pipeline runner once the source asset exists

Current limitation:
- still depends on external executables, optional modules, and path assumptions that need normalization

## Intended Handoff Contract

### Stage 1: Author or package source assets

Inputs:
- Clip Studio pages
- generated sprite sheets
- polished atlas images
- rig metadata

Outputs:
- stable source images and metadata bundles

Primary systems:
- ClipConceptBook and related authoring-side tooling
- readAIpolish where needed

### Stage 2: Trial projection and graphing in Blender via TxTUR

Inputs:
- source sheet or atlas
- texture and mapping presets
- NodeCraft graph ideas

Outputs:
- exploratory brush, surface, and graph state
- early visual and structural decisions for scene lift

Primary systems:
- `blender_txtur_addon.py`
- `blenderTxTUR.dll`

### Stage 3: Formal conversion contract via BlendNow

Inputs:
- nomenclature metadata
- polished atlas path
- rig data
- scene intent

Outputs:
- `BlendNow_TxTUR_conversion_plan.json`
- `BlendNow_TxTUR_import_spec.json`

Primary systems:
- `BlendNow_core.py`

### Stage 4: Executable scene build via DripCraft

Inputs:
- image path
- optional Recraft pass
- conversion plans and import assumptions

Outputs:
- generated Blender scene
- pipeline work directory
- saved `.blend` output

Primary systems:
- `DripCraft_addon.py`
- `DripCraft.exe` or `DripCraft`
- `readAIpolish`

## Recommended Operating Rule

- use `TxTUR` for experimentation and in-Blender surface ideation
- use `BlendNow` for formal handoff metadata and import specification
- use `DripCraft` for operator-driven execution and saved scene output

This keeps the three tools from competing for the same responsibility.

## Reproducible Path for Current Bango Flow

The current Bango-related reference path is:

1. Prepare the source sheet and rig metadata.
2. Run `bango-patoot_3DS/tools/run_bango_sheet_autorig.py`.
3. Let the script generate keyed frames, polished atlas metadata, and BlendNow handoff JSON.
4. Launch Blender automation through `bango_sheet_autorig_blender.py`.
5. Treat generated `.blend`, `.glb`, and related bundles as outputs, not hand-edited sources.

## Near-Term Cleanup Tasks

1. Normalize all executable and module path discovery so the toolchain does not depend on hard-coded workstation assumptions.
2. Add one wrapper script that runs the full TxTUR to BlendNow to DripCraft chain from a single manifest.
3. Document required environment variables and optional dependencies.
4. Add one smoke test that verifies the JSON handoff files can be produced without Blender UI interaction.

## Bottom Line

The current clean interpretation is:

- `TxTUR` is the interactive bridge and experimental surface layer.
- `BlendNow` is the formal conversion contract generator.
- `DripCraft` is the operator-facing execution runner that turns prepared assets into Blender scene outputs.