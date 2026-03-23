# InnsmouthIsland Research Bibliography

Date: 2026-03-11

## Purpose

This bibliography records the actual references consulted, generated, or relied upon during the InnsmouthIsland standalone demo expansion, asset-bible drafting, Recraft prompt generation planning, and ORBEngine integration planning. It is intended as an audit-support document for provenance review, copyright-risk review, and internal reconstruction of how design and prompt decisions were formed.

## Scope Notes

- This document only lists sources that were directly accessed in the workspace during the session or were already present as project documentation.
- No external third-party asset files were imported into the repo during this session.
- No public-domain or open-course art packs were copied into the project during this session.
- A planned comparative public-asset web lookup was attempted but canceled before retrieval, so no external website content was actually incorporated into the resulting asset bible.

## Primary Internal Sources Consulted

1. [ORBEngine/src/innsmouth_island_demo.cpp](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/src/innsmouth_island_demo.cpp)
   Used as the authoritative gameplay taxonomy source for:
   - player animation states,
   - enemy roster,
   - pickup classes,
   - MurkShelter behavior,
   - weapon catalog,
   - armor set catalog,
   - environment prop count and placement,
   - and current HUD/view-menu semantics.

2. [drIpTECH/ReCraftGenerationStreamline/innsmouth_island_manifest.json](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/innsmouth_island_manifest.json)
   Used as the prior-generation source of truth for the first InnsmouthIsland Recraft asset batch and prior prompt wording.

3. [ORBEngine/assets/innsmouth_island](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/assets/innsmouth_island)
   Existing generated asset directory inspected to confirm the currently available art families:
   - player sheet,
   - opening storyboard,
   - enemy roster,
   - enemy animation sheet,
   - boss animation sheet,
   - environment prop sheet,
   - map,
   - key art,
   - HUD,
   - icons,
   - UI panel.

4. [ORBEngine/ORBEngine_ARCHITECTURE.md](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/ORBEngine_ARCHITECTURE.md)
   Used to align the ORBdimensionView, ORBKinetics, and ORBGlue naming and integration plan with the engine’s existing subsystem architecture.

5. [ORBEngine/include/orbengine.h](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/include/orbengine.h)
   Used as the core engine public interface reference before introducing non-breaking config scaffolding for InnsmouthIsland-oriented module profiles.

6. [ORBEngine/src/orbengine.c](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/src/orbengine.c)
   Used to validate where core sandbox initialization and engine-facing configuration should be attached.

7. [ORBEngine/src/orbengine_sandbox.c](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/src/orbengine_sandbox.c)
   Used to confirm the current sandbox launch path and non-breaking compile expectations after the ORB module config additions.

## Generated Internal Research Outputs

1. [ORBEngine/reports/INNSMOUTH_ISLAND_ASSET_BIBLE.md](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/reports/INNSMOUTH_ISLAND_ASSET_BIBLE.md)
   Generated in this session as the canonical asset-production and integration planning document.

2. [ORBEngine/reports/INNSMOUTH_ISLAND_ASSET_BIBLE.txt](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/reports/INNSMOUTH_ISLAND_ASSET_BIBLE.txt)
   Plain-text review copy of the same asset bible, opened in Notepad for inspection.

3. [drIpTECH/ReCraftGenerationStreamline/innsmouth_island_master_manifest.json](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/innsmouth_island_master_manifest.json)
   Generated in this session as the detailed next-pass Recraft prompt manifest for asset-family regeneration.

## Existing Tooling And Documentation Relevant To Asset Generation

1. [drIpTECH/ReCraftGenerationStreamline/README.md](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/README.md)
   Existing repo documentation for local Recraft-generation workflow and manifest usage.

2. [drIpTECH/ReCraftGenerationStreamline/batch_run_manifest.py](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/batch_run_manifest.py)
   Used to dry-run validate the newly generated InnsmouthIsland master manifest without consuming credits.

3. [drIpTECH/ReCraftGenerationStreamline/recraft documentation urls.txt](c:/Users/rrcar/Documents/drIpTECH/drIpTECH/ReCraftGenerationStreamline/recraft%20documentation%20urls.txt)
   Existing reference list in the workspace pointing to official Recraft documentation endpoints and limits.

## Build And Validation Evidence

1. [ORBEngine/build_innsmouth_island.ps1](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/build_innsmouth_island.ps1)
   Used to validate the standalone InnsmouthIsland executable after gameplay, shrine, pickup, and render expansions.

2. [ORBEngine/innsmouth_island_demo.exe](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/innsmouth_island_demo.exe)
   Rebuilt successfully during the session after integration of the new systems and render changes.

3. [ORBEngine/src/orbengine.c](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/src/orbengine.c)
   Recompiled successfully with [ORBEngine/src/orbengine_sandbox.c](c:/Users/rrcar/Documents/drIpTECH/ORBEngine/src/orbengine_sandbox.c) after ORBdimensionView, ORBKinetics, and ORBGlue configuration scaffolding was added.

## External References Consulted

1. OpenGameArt. Home and community art index. https://opengameart.org/ Accessed 2026-03-11.
   Used to benchmark breadth of public game-asset ecosystems across art, UI, sound, and music families.

2. OpenGameArt. Art marketplace cross-promotion. https://opengameart.org/content/art-marketplace-cross-promotion Accessed 2026-03-11.
   Used to benchmark licensing/provenance caution and reinforce per-asset rights logging instead of platform-wide assumptions.

3. Kenney. Assets index. https://kenney.nl/assets Accessed 2026-03-11.
   Used to benchmark modular kit completeness across environments, UI, prompts, textures, and support families.

4. Liberated Pixel Cup. Project overview and style-guide framing. https://lpc.opengameart.org/ Accessed 2026-03-11.
   Used to benchmark style-guide discipline, consistency expectations, and deliberately constrained perspective rules for reusable asset families.

## External References Status

- External public-asset benchmark content is now incorporated into the saved research outputs as cited production standards only.
- No external website images, audio, or packaged assets were downloaded into the repo during this session.
- No prompt text from those sites was copied verbatim into the InnsmouthIsland manifests.

## Provenance And Risk Notes

- The InnsmouthIsland art planning in this session was derived from in-repo gameplay definitions, prior in-repo prompt manifests, and newly authored descriptive prompt language.
- The output documents are planning and prompt documents, not copies of third-party art.
- If future image-conditioned generation is performed using outside reference images, those source files should be logged here with:
  - source URL or local acquisition path,
  - date accessed,
  - license or rights basis,
  - whether used for inspiration, control image conditioning, overpaint, or direct editing.
- If user-supplied audio stems or one-shots are later added, they should be cataloged in a follow-up appendix with ownership and usage scope.

## Recommended Audit Additions For Future Sessions

1. Save exact generation timestamps and prompt revisions for every Recraft batch.
2. Store hashes for generated images and any source control/reference images.
3. Keep a per-asset provenance table linking prompt, control image, output file, and intended runtime use.
4. Record any external visual references before they are used in prompt-conditioning workflows.
5. Record license notes for any user-supplied audio or reference packs before import.