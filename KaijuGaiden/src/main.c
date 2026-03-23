#include <gba.h>
#include <stdio.h>
#include "game.h"

int main(void) {
    irqInit();
    irqEnable(IRQ_VBLANK);

    // Show title sequence
    game_title_sequence();

    while (1) {
        VBlankIntrWait();
        scanKeys();
        u16 keys = keysDown();
        if (keys & KEY_START) {
            consoleDemoInit();
            game_main_menu();
            // After menu returns, show title again
            consoleDemoInit();
            game_title_sequence();
        }
    }
    return 0;
}
