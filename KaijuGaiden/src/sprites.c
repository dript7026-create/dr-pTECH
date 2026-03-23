#include "sprites.h"
#include <gba.h>

void sprite_set(int slot, int x, int y, int tile_index, int palette_bank) {
    if (slot < 0 || slot >= 128) return;
    OBJATTR *oam = OAM + slot;
    // attr0: y coord, regular shape
    oam->attr0 = (uint16_t)(y & 0xFF);
    // attr1: x coord
    oam->attr1 = (uint16_t)(x & 0x1FF);
    // attr2: tile index & palette bank
    oam->attr2 = (uint16_t)((tile_index & 0x3FF) | ((palette_bank & 0xF) << 12));
}

void sprite_hide(int slot) {
    if (slot < 0 || slot >= 128) return;
    OBJATTR *oam = OAM + slot;
    oam->attr0 = ATTR0_DISABLED;
}
