/*
 * kaijugaiden_gba.c — Kaiju Gaiden GBA prototype entrypoint.
 *
 * This file is the explicit C root for the Game Boy Advance game, which is
 * separate from the Game Boy game implemented in kaijugaiden.c.
 *
 * The GBA build uses the modular runtime under src/ and links against libgba.
 */

#if defined(__has_include)
#  if __has_include(<gba.h>)
#    include <gba.h>
#  else
#    include "include/gba.h"
#  endif
#else
#  include "include/gba.h"
#endif
#include "src/game.h"

#ifndef IRQ_VBLANK
#  define IRQ_VBLANK 1
#endif

int main(void) {
    irqInit();
    irqEnable(IRQ_VBLANK);

    game_title_sequence();

    while (1) {
        VBlankIntrWait();
        scanKeys();
        u16 keys = keysDown();
        if (keys & KEY_START) {
            consoleDemoInit();
            game_main_menu();
            consoleDemoInit();
            game_title_sequence();
        }
    }

    return 0;
}