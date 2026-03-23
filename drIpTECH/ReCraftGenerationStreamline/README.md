ReCraftGenerationStreamline
==========================

This folder contains tooling to call a Recraft-like image generation API from C and
to integrate generated textures into Blender via a Python addon (TxTUR bridge).

Files
- `recraft_generation_streamline.c` — manifest-enabled C client using libcurl and cJSON.
- `blender_recraft_txtr_addon.py` — Blender addon (Python) to import textures and run a placeholder TxTUR/readAIpolish integration.
- `ccp_manifest.py` — ClipConceptBook parser/translator for `.ccp` containers.
- `ccp_to_recraft_manifest.py` — CLI wrapper to emit standard Recraft manifest JSON from a `.ccp`.

Build (C client)

Requirements:
- libcurl dev files
- cJSON (place `cJSON.c` / `cJSON.h` next to the C file or install system-wide)

Example build:

```sh
gcc recraft_generation_streamline.c cJSON.c -o recraft_gen -lcurl
```

Usage

- Single generate:

```sh
./recraft_gen "a small chibi sprite" 16 16 assets/tommy_sprite.png
```

- Bulk (manifest): create `manifest.json` (see example in file header) and run:

```sh
./recraft_gen --manifest manifest.json
```

- ClipConceptBook input: `batch_run_manifest.py` can now accept a `.ccp` file directly via `--manifest`.

```sh
python batch_run_manifest.py --manifest pages.ccp --dry-run
python ccp_to_recraft_manifest.py pages.ccp pages_manifest.json
```

ClipConceptBook notes
- `.ccp` is a custom container with a fixed header, embedded JSON manifest, and the raw source zip payload.
- The source zip should contain `.clip` files named `pg1.clip`, `pg2.clip`, ... `pgn.clip`.
- Recraft translation relies on the embedded `prompt_map` metadata inside the `.ccp`; `.clip` page contents are currently treated as opaque authored sources rather than parsed art data.

Blender addon

Install `blender_recraft_txtr_addon.py` as a Blender addon (place in `~/.config/blender/<version>/scripts/addons/` or install via Preferences → Add-ons → Install).
After enabling, use File → Import → Recraft TxTUR Bridge to run the import + placeholder TxTUR workflow.

Notes & Next Steps
- The C client currently expects the API to return JSON in the form `{"data": [ { "b64_json": "..." } ] }` or similar. If the Recraft API uses different field names or streaming, adapt the parsing logic.
- For robust production use, add retries, configurable model/size parameters, rate limiting, and better error reporting.
- To integrate deeply with `readAIpolish`, install `readAIpolish`'s Python package into Blender's Python environment and implement the call in `blender_recraft_txtr_addon.py` where marked.

InnsmouthIsland Protocol Files
- `innsmouth_island_dimensional_protocol_profile.json` defines the reusable anchor-node, invisible silhouette, shading, and pseudo-3D translation requirements for future passes.
- `innsmouth_island_attachment_map_v1.json` defines the formal ORBGlue runtime socket format and authored runtime socket profiles that bind generated anchor-node metadata to equipment and support attachment points.
- `innsmouth_island_environment_runtime_metadata_v1.json` defines authored environment silhouette, occlusion, shadow, and anchor-node metadata for runtime ORBDimensionView and ORBKinetics consumption.
- `innsmouth_island_protocol_full_manifest.json` is the clean full generation pass that applies the saved protocol to the entire InnsmouthIsland asset set.
- `innsmouth_island_protocol_polish_manifest.json` is the research-cross-referenced polish pass that reapplies the protocol against the established benchmark-informed baseline.
- The saved protocol explicitly assigns ownership of anchor-depth translation to ORBdimensionView, invisible hit-detection precision to ORBKinetics, and gameplay/equipment binding of those authored signals to ORBGlue, with the Innsmouth demos now loading the attachment and environment runtime JSON directly at startup.
