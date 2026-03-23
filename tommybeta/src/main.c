#include <gb/gb.h>
#include <stdio.h>

// If a generated sprites file exists, it will create HAVE_GENERATED_SPRITES
#include "sprites.generated.h"
#ifdef HAVE_GENERATED_SPRITES
#include "sprites.generated.c"
#else
#include "sprites.c"
#endif

void main(void) {
    UINT8 joy;
    // Initialize
    DISPLAY_ON;
#ifdef HAVE_GENERATED_SPRITES
    set_sprite_data(0, NUM_SPRITE_TILES, sprites_generated);
    set_sprite_tile(0, 0);
#else
    set_sprite_data(0, 1, sprites);
    set_sprite_tile(0, 0);
#endif
    move_sprite(0, 88, 78);
    SHOW_SPRITES;

    printf("TommyBeta\n");

    while(1) {
        wait_vbl_done();
        joy = joypad();
        if (joy & J_LEFT) {
            scroll_sprite(0, -2, 0);
        }
        if (joy & J_RIGHT) {
            scroll_sprite(0, 2, 0);
        }
        if (joy & J_UP) {
            scroll_sprite(0, 0, -2);
        }
        if (joy & J_DOWN) {
            scroll_sprite(0, 0, 2);
        }
    }
}
