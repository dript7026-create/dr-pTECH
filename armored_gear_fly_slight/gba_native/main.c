#include "port_gba.h"
#include "port_game.h"

int main(void) {
    PortGameState game;

    port_gba_init();
    port_game_init(&game);

    while (!game.exit_requested) {
        PortInputState input;
        volatile uint16_t *buffer;

        port_gba_wait_vblank();
        port_gba_poll_input(&input);

        if (input.pressed & KEY_START) {
            game.exit_requested = 1;
        }

        port_game_update(&game, &input);

        buffer = port_gba_get_draw_buffer();
        port_game_render(&game, buffer);
        port_gba_present();
    }

    return 0;
}
