# PxGBPROG

`PxGBPROG` is the Game Boy-facing pixel program module for runtime-authored tile variants. It keeps the asset logic in C instead of an external generator.

## Layout

- `include/pxgbprog.h`: public manifest, vector-scene, and pipeline API.
- `src/pxgbprog.c`: base manifest catalog and compatibility entrypoints.
- `src/pxgbprog_pipeline.c`: full render pipeline from base input tiles to vector scene, simulated real-space offsets, and pixel-by-pixel raster output.

## Role

`PxGBPROG` accepts a base sprite bank plus manifest programs and runs a staged pipeline:

1. Decode incoming 2bpp DMG tiles into a pixel surface.
2. Build a vector scene from manifest primitives.
3. Simulate local real-space drift and render-mode offsets.
4. Rasterize the scene pixel-by-pixel.
5. Compile the result back to DMG 2bpp tiles.

In Armored Gear: Fly Slight it is used to restyle player and daemon kin sprites without replacing the current 8x8 renderer. `PROGHONORAI` supplies the render directive, and `PxGBPROG` handles the vector-oriented scene build, local real-space simulation, and final pixel raster.