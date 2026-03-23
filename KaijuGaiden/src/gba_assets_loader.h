#pragma once
#include <stdint.h>

// Prototype helpers for loading tile & palette data into GBA VRAM.
// These are minimal examples for the prototype pipeline.

// Load a block of tile bytes into VRAM at the given VRAM offset (bytes).
// tiles: pointer to tile data (4bpp, 32 bytes per 8x8 tile)
// size_bytes: size of tiles in bytes
// vram_offset: offset from 0x06000000 where to copy the tiles (e.g., 0x0000, 0x1000, ...)
void load_tiles_to_vram(const void* tiles, unsigned size_bytes, unsigned vram_offset);

// Load OBJ (sprite) palette to OBJ palette memory (0x05000200). palette is 16-bit BGR555 entries.
// palette_count: number of palette entries (typically 16)
void load_obj_palette(const void* palette, unsigned palette_count);
