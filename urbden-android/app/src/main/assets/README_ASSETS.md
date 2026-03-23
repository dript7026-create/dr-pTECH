Asset Guidelines for Urbden

Place your game art under these folders in this order:

- `tiles/` : tile images (street, sidewalks, buildings) - use uniform tile size (recommended 32x32 or 16x16)
- `sprites/` : in-world character sprites (player + NPCs). Use consistent baseline and frame sizes.
- `portraits/` : portrait images for dialogues (recommended 256x256 or 128x128)
- `ui/` : UI icons (buttons, icons) and fonts

Recommended workflow
1. Create individual PNGs for tiles and sprites with transparent backgrounds.
2. Use the included `tools/generate_atlas.py` to pack tiles into `atlas.png` and produce `atlas.json` metadata.
   - Install Pillow: `python -m pip install pillow`
   - Run: `python tools/generate_atlas.py --input app/src/main/assets/tiles --out app/src/main/assets/atlas.png --meta app/src/main/assets/atlas.json --tile 32`
3. Place portrait and UI images directly in `portraits/` and `ui/` folders.
4. Add a `manifest.txt` (see template) describing semantic mapping (e.g., which tile indexes correspond to `pizzeria`, `bank`, `bike_shop`). The procedural generator reads this to assign semantics.

Atlas metadata format
The generated `atlas.json` will look like:

{
  "tile_w": 32,
  "tile_h": 32,
  "cols": 8,
  "rows": 8,
  "frames": {
    "tile_street_01": {"x":0,"y":0,"w":32,"h":32},
    ...
  }
}

Loading assets on Android
- Put all art under `app/src/main/assets/` so native code can access via `AAssetManager` or Java via `AssetManager`.
- For fast runtime rendering, load `atlas.png` into a GL texture and use `atlas.json` to map UVs for tiles/sprites.

Performance tips
- Use power-of-two texture sizes when targeting older devices (not strictly necessary on modern OpenGL ES 3.0+).
- Keep tile sizes small (16 or 32) to reduce memory.
- Use a single atlas per asset category (tiles, sprites) to keep texture binds low.
