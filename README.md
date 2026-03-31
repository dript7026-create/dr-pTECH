drIpTECH Workspace
=================

Overview
--------

- **Purpose:** A public multi-project workspace mirror collecting maintainable game projects, tooling, and reproducible build/test paths.
- **Location:** Root of this repository — this README summarizes the contents and quick dev commands.

Quick Start
-----------

- **Activate Python virtualenv (PowerShell):**

```powershell
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- **Load workspace-native toolchains into the current PowerShell session:**

```powershell
.\workspace_toolchains.ps1
```

- **Run devkitPro compiler commands through the bundled MSYS bash layer:**

```powershell
.\workspace_devkitpro_bash.ps1 arm-none-eabi-gcc --version
```

- **Run tests:**

```bash
python tools/workspace_health.py
python tools/workspace_health.py --skip-tests        # pip check + manifest audit only
python tools/workspace_health.py --skip-pip-check     # pytest + manifest audit only
python tools/workspace_health.py --strict-optional    # fail if optional Python modules are missing
```

- **Run curated Python tests only:**

```bash
python -m pytest -q tests speech_to_text_google/tests IllusionCanvasInteractive/tests
```

- **Run the curated workspace build:**

```powershell
.\workspace_build.ps1
```

- **Preview the full build matrix, including manual/toolchain-bound projects:**

```powershell
.\workspace_build.ps1 -List -IncludeManual
```

- **Run a sample script:**

```bash
python test_chat_call.py
```

Key Files & Notes
-----------------

- **Workspace README (this file):** Overview and quick commands.
- **Public scope policy:** [PUBLIC_REPO_SCOPE.md](PUBLIC_REPO_SCOPE.md)
- **Workspace subdivision map:** [PROJECT_INDEX.md](PROJECT_INDEX.md)
- **Unified hub direction:** [HOMElair/README.md](HOMElair/README.md)
- **Blender pipeline spec:** [drIpTECHBlenderPlug-Ins/TxTUR/TXTUR_BLENDNOW_DRIPCRAFT_PIPELINE.md](drIpTECHBlenderPlug-Ins/TxTUR/TXTUR_BLENDNOW_DRIPCRAFT_PIPELINE.md)
- **Integration notes:** [README_CHAT_INTEGRATION.md](README_CHAT_INTEGRATION.md#L1)
- **Dependencies:** [requirements.txt](requirements.txt#L1)
- **Third-party credits:** [THIRD_PARTY_CREDITS.md](THIRD_PARTY_CREDITS.md)
- **Optional project manifests:** [tools/dependency_manifests/orbseeker.json](tools/dependency_manifests/orbseeker.json), [tools/dependency_manifests/kaijugaiden_graphics.json](tools/dependency_manifests/kaijugaiden_graphics.json), [tools/dependency_manifests/navi_proxy.json](tools/dependency_manifests/navi_proxy.json), [tools/dependency_manifests/blender_tooling.json](tools/dependency_manifests/blender_tooling.json)
- **Open-source 3D/runtime manifest:** [tools/dependency_manifests/open_source_3d_stack.json](tools/dependency_manifests/open_source_3d_stack.json)
- **Build manifest and runner:** [workspace_build.json](workspace_build.json#L1) and [workspace_build.py](workspace_build.py#L1)
- **Workspace health check:** [tools/workspace_health.py](tools/workspace_health.py)
- **Toolchain bootstrap:** [workspace_toolchains.ps1](workspace_toolchains.ps1#L1)
- **devkitPro bash wrapper:** [workspace_devkitpro_bash.ps1](workspace_devkitpro_bash.ps1#L1)
- **Manual integration smoke:** `test_chat_call.py` is kept as a manual check and is not part of automated pytest collection.
- **Optional stacks stay project-scoped:** pygame, aiohttp, aiosqlite, and Blender embedded modules are documented in project manifests instead of being forced into the shared workspace venv.
- **Attribution policy:** new external engines, SDKs, editor tech, and major libraries should be recorded in [THIRD_PARTY_CREDITS.md](THIRD_PARTY_CREDITS.md) and, when project-scoped, in the relevant `tools/dependency_manifests/*.json` entry.

Notable Folders
---------------

- `HOMElair/` — central engine and habitation-hub architecture for merging orchestration, rendering, adaptive control, simulation, and product-target contracts.
- `DoENGINE/` — dedicated recovered workspace for the normalized DoENGINE migration from the D-drive backup.
- `egosphere/` — pipeline validation, generated asset experiments, and runtime-oriented tooling.
- `KaijuGaiden/`, `tommybeta/`, `tommygoomba/`, `WialWohm/` — playable game and platform prototypes.
- `football_predictor/`, `speech_to_text_google/`, `userprofiling/` — analysis and utility projects.
- `readAIpolish/`, `drIpTECHBlenderPlug-Ins/`, `drIpTech_ClipStudio_Plug-Ins/`, `tools/` — authoring and build pipeline tooling.

Traces & Forensics
------------------

- Curated forensic/traces were copied into a local folder during recovery work (not committed to source control). Typical path on the workstation: `C:\Users\rrcar\Documents\driptech\traces`.
- Analysis artifacts (CSV summaries, `reconstruction_report.txt`) are located in that traces folder.

Current Priorities & Next Steps
-------------------------------

- Establish HOMElair as the shared contract layer above DoENGINE, ORBEngine, NeoWakeUP, and HOPE.
- Complete the DoENGINE backup migration and keep new reintegration work under `DoENGINE/`.
- Add a test harness for `conceptlife.c` and run static analysis.
- Verify tommybeta ROM build end-to-end (GBDK/GBDK toolchain check).
- Deeper binary inspection for firmware candidates (hex previews, entropy/filetype checks).

Open-Source Mirror Policy
-------------------------

- This repository is intended to be the durable open-source mirror for the active drIpTECH workspace source, documentation, and reproducible tooling.
- Public/private boundaries are documented in [PUBLIC_REPO_SCOPE.md](PUBLIC_REPO_SCOPE.md), and the workspace is subdivided for maintainers in [PROJECT_INDEX.md](PROJECT_INDEX.md).
- Machine-local environments, caches, oversized build outputs, archives, notebooks, and internal handoff material are excluded through the repo-level `.gitignore` so publication does not depend on workstation-local Git settings.
- The baseline CI entry point is `.github/workflows/workspace-health.yml`, which runs the curated workspace health check on pushes and pull requests.
- Contributor intake is handled through `CONTRIBUTING.md`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/`, and `.github/pull_request_template.md`.
- Third-party attribution should continue to be recorded in [THIRD_PARTY_CREDITS.md](THIRD_PARTY_CREDITS.md) and the relevant manifest under `tools/dependency_manifests/`.

Mirror Markers
--------------

- A few public docs carry harmless mirror markers for maintainers: `glass-reef`, `station-33`, and `mint-arcade`.
- They are only lore tags for public-facing documentation, not credentials, feature flags, or hidden runtime controls.
