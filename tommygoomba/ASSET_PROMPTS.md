Asset prompts for Recraft.ai (pixel-art, Game Boy 4-shade)

General style: pixel-art, crisp silhouettes, clear readability at small sizes, limited to a 4-shade Game Boy palette. Prefer slightly exaggerated head proportions for clarity at 16x16.

Prompts (suggested):

- `tommy_sprite` (16x16):
  "16x16 pixel art sprite of a small chibi hero. Simple expressive face, round head, tiny limbs, clear silhouette. Limited 4-shade Game Boy palette. Emphasize readable silhouette and head/body separation. No background."

- `enemy_sprite` (16x16):
  "16x16 pixel art sprite of a hostile goomba-like enemy. Clear single-frame sprite, menacing expression, compact silhouette, Game Boy 4-shade palette, no background."

- `hud_tommy` (24x24):
  "24x24 pixel art head portrait, simplified features, strong silhouette, Game Boy 4-shade palette. Centered on transparent background."

- `bg_day` (160x144):
  "160x144 pixel-art background scene for Game Boy: simple sky gradient, a strip of ground/grass, distant hills simplified, limited to 4 shades so it can be tiled into 8x8 tiles."

- `tile_grass` / `tile_block` (8x8):
  "8x8 tile, pixel art, tileable edges, 4-shade palette, simple grass texture / stone block texture respectively."

Notes on palette and output:
- Request outputs as PNG with transparent background when appropriate (e.g., sprites, HUD head).
- Because Game Boy uses 4 shades per tile, request the model to use flat shading with clear dithering avoided; we'll later remap to the exact GB palette.

If you want variations, include `--seed` parameters in `recraft_generate.py` call or edit ASSETS to duplicate entries with `v1`, `v2` suffixes.
