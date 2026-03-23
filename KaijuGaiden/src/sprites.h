#pragma once
#include <stdint.h>

// Simple OAM sprite helper (prototype)
// slot: 0..127
void sprite_set(int slot, int x, int y, int tile_index, int palette_bank);
void sprite_hide(int slot);
