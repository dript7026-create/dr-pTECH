#include "gba_assets_loader.h"
#include <string.h>

// GBA memory addresses
#define VRAM ((volatile void*)0x06000000)
#define OBJ_PALETTE_MEM ((volatile uint16_t*)0x05000200)

void load_tiles_to_vram(const void* tiles, unsigned size_bytes, unsigned vram_offset) {
    volatile uint8_t* dest = (volatile uint8_t*)((uintptr_t)VRAM + vram_offset);
    // Simple memcpy; for production builds prefer DMA for speed.
    memcpy((void*)dest, tiles, size_bytes);
}

void load_obj_palette(const void* palette, unsigned palette_count) {
    const uint16_t* src = (const uint16_t*)palette;
    for (unsigned i = 0; i < palette_count; ++i) {
        OBJ_PALETTE_MEM[i] = src[i];
    }
}
