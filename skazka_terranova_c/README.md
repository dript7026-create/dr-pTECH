SKAZKA: Terranova - C prototype

This folder contains a minimal SDL2 C prototype scaffolding for the SKAZKA: Terranova prototype.

Requirements:
- SDL2 development libraries installed (headers + libs)
- SDL2_image installed
- CMake and a C compiler (MSVC or MinGW/clang)

Build (example with Ninja on Windows or Unix):

```bash
mkdir build && cd build
cmake -G "Ninja" ..
cmake --build . --config Release
./skazka_terranova
```

Or with default generator:

```powershell
mkdir build; cd build
cmake ..
cmake --build . --config Release
.\skazka_terranova.exe
```

Notes:
- The runtime now supports loading generated textures from an extracted FARIM bundle and applies joint-anchor metadata from `runtime_anchors.csv` for simple puppet-style animation.
- If the extracted runtime folder exists at `skazka_terranova_c/build/runtime_farim`, the prototype will render the generated backgrounds, HUD, Media Deck panel, Misha rig parts, Leshy, vendor, and FX.

Asset pipeline:

```powershell
.\.venv\Scripts\python.exe .\drIpTECH\ReCraftGenerationStreamline\batch_run_manifest.py --manifest .\drIpTECH\ReCraftGenerationStreamline\skazka_terranova_demo_manifest.json --direct-api --yes --ledger .\skazka_terranova_c\build\skazka_asset_ledger.csv
.\.venv\Scripts\python.exe .\skazka_terranova_c\tools\build_farim.py --manifest .\drIpTECH\ReCraftGenerationStreamline\skazka_terranova_demo_manifest.json --output .\skazka_terranova_c\build\skazka_terranova_demo.farim
.\.venv\Scripts\python.exe .\skazka_terranova_c\tools\unpack_farim.py --input .\skazka_terranova_c\build\skazka_terranova_demo.farim --output .\skazka_terranova_c\build\runtime_farim
```

Current limitations:
- FARIM is currently a ZIP-based asset container with metadata, not a secure browser runtime.
- The editor still reports missing SDL headers until SDL2/SDL2_image are installed and visible to the toolchain.
