drIpTECH Workspace
=================

Overview
--------

- **Purpose:** A personal multi-project workspace collecting game projects, tooling, and analysis artifacts (traces, asset pipelines, prototypes).
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
- **Portfolio execution plan:** [drIpTECH_PORTFOLIO_EXECUTION_PLAN.md](drIpTECH_PORTFOLIO_EXECUTION_PLAN.md)
- **Stack architecture:** [drIpTECH_STACK_ARCHITECTURE.md](drIpTECH_STACK_ARCHITECTURE.md)
- **Lender budget sheet:** [drIpTECH_LENDER_BUDGET_AND_MILESTONE_SHEET.md](drIpTECH_LENDER_BUDGET_AND_MILESTONE_SHEET.md)
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
- **Useful scripts:** `set_openai_key.ps1` and `test_chat_call.py` — the chat script is a manual smoke test, not part of automated pytest collection.
- **Optional stacks stay project-scoped:** pygame, aiohttp, aiosqlite, and Blender embedded modules are documented in project manifests instead of being forced into the shared workspace venv.
- **Attribution policy:** new external engines, SDKs, editor tech, and major libraries should be recorded in [THIRD_PARTY_CREDITS.md](THIRD_PARTY_CREDITS.md) and, when project-scoped, in the relevant `tools/dependency_manifests/*.json` entry.

Notable Folders
---------------

- `DoENGINE/` — dedicated recovered workspace for the normalized DoENGINE migration from the D-drive backup.
-- `drIpTECH/` — primary project folder containing subprojects and tools.
-- `football_predictor/` — a small ML project (see its README inside the folder).
-- `WialWohm/`, `readAIpolish/`, `ruggedhusk/`, `YOIT/` — experimental projects and utilities.

Traces & Forensics
------------------

- Curated forensic/traces were copied into a local folder during recovery work (not committed to source control). Typical path on the workstation: `C:\Users\rrcar\Documents\driptech\traces`.
- Analysis artifacts (CSV summaries, `reconstruction_report.txt`) are located in that traces folder.

Current Priorities & Next Steps
-------------------------------

- Complete the DoENGINE backup migration and keep new reintegration work under `DoENGINE/`.
- Add a test harness for `conceptlife.c` and run static analysis.
- Verify tommybeta ROM build end-to-end (GBDK/GBDK toolchain check).
- Deeper binary inspection for firmware candidates (hex previews, entropy/filetype checks).

Open-Source Mirror Policy
-------------------------

- This repository is intended to be the durable open-source mirror for the active drIpTECH workspace source, documentation, and reproducible tooling.
- Machine-local environments, caches, oversized build outputs, archives, and handoff bundles are excluded through the repo-level `.gitignore` so publication does not depend on workstation-local Git settings.
- The baseline CI entry point is `.github/workflows/workspace-health.yml`, which runs the curated workspace health check on pushes and pull requests.
- Third-party attribution should continue to be recorded in [THIRD_PARTY_CREDITS.md](THIRD_PARTY_CREDITS.md) and the relevant manifest under `tools/dependency_manifests/`.

If you'd like, I can: add CI config, scaffold the `conceptlife.c` tests, or produce hex previews for firmware candidates now. Which would you prefer?
