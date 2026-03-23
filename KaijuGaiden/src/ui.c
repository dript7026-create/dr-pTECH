#include <gba.h>
#include <stdio.h>
#include "ui.h"
#include "gba_assets_loader.h"
#include "../assets/placeholder_assets.h"
// include converted headers (if present)
#include "../assets/rei_assets.h"
#include "../assets/minion1_assets.h"
#include "../assets/nanocell1_assets.h"
#include "sprites.h"

static int ui_initialized = 0;
static int ui_tick_acc = 0;

void ui_init(void) {
    if (ui_initialized) return;
    // Load placeholder tiles to VRAM at 0x0000 and palette to OBJ palette
    load_tiles_to_vram(placeholder_tiles, placeholder_tiles_size, 0x0000);
    load_obj_palette(placeholder_palette, placeholder_palette_size);
    // load some converted assets into VRAM at different offsets
    load_tiles_to_vram(rei_tiles, rei_tiles_size, 0x1000);
    load_tiles_to_vram(minion1_tiles, minion1_tiles_size, 0x2000);
    load_tiles_to_vram(nanocell1_tiles, nanocell1_tiles_size, 0x3000);
    ui_initialized = 1;
}

void ui_update(int delta_ms) {
    ui_tick_acc += delta_ms;
}

void ui_draw_hud(const Entity* e) {
    if (!ui_initialized) return;
    // Simple console HUD rendering for prototype
    iprintf("HP: %u/%u  Tier:%u Var:%u\n", e->hp, e->max_hp, e->growth_tier, e->variant);
    iprintf("Vib:%u Nanocells:%d pol=%d cues=0x%02X\n", e->vib_signature, e->pending_nanocell_amount, e->pending_nanocell_polarity, e->visual_cue);

    // Visual cue: if benevolent glow -> tint OBJ palette entry 1 to greenish
    if (e->visual_cue & 1) {
        // apply quick palette tweak (write directly for prototype)
        volatile uint16_t* pal = (volatile uint16_t*)0x05000200;
        pal[1] = 0x03E0; // green
    } else if (e->visual_cue & 2) {
        volatile uint16_t* pal = (volatile uint16_t*)0x05000200;
        pal[1] = 0x001F; // blue-ish corrosive
    } else {
        volatile uint16_t* pal = (volatile uint16_t*)0x05000200;
        pal[1] = placeholder_palette[1];
    }

    // Draw simple sprites: player and optional nanocell aura
    // rei_tiles loaded at VRAM offset 0x1000 -> tile index offset = 0x1000 / 32
    const int rei_tile_offset = 0x1000 / 32;
    const int nanocell_tile_offset = 0x3000 / 32;
    // show player sprite at slot 0
    sprite_set(0, 80, 64, rei_tile_offset, 0);
    // show nanocell effect if active
    if (e->visual_cue & 1) {
        sprite_set(1, 96, 64, nanocell_tile_offset, 0);
    } else if (e->visual_cue & 2) {
        sprite_set(1, 96, 64, nanocell_tile_offset, 0);
    } else {
        sprite_hide(1);
    }
}
