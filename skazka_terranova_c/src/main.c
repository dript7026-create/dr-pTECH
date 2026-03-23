#include <stdio.h>
#include <SDL.h>
#include "game.h"

int main(int argc, char **argv) {
    (void)argc; (void)argv;
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMECONTROLLER | SDL_INIT_AUDIO) != 0) {
        fprintf(stderr, "SDL_Init Error: %s\n", SDL_GetError());
        return 1;
    }

    GameState game;
    if (!game_init(&game, 1280, 720)) {
        SDL_Quit();
        return 1;
    }

    Uint32 last = SDL_GetTicks();
    while (!game.quit) {
        Uint32 now = SDL_GetTicks();
        float dt = (now - last) / 1000.0f;
        if (dt > 0.05f) dt = 0.05f;
        last = now;

        game_process_input(&game);
        game_update(&game, dt);
        game_render(&game);
        SDL_Delay(1);
    }

    game_shutdown(&game);
    SDL_Quit();
    return 0;
}
