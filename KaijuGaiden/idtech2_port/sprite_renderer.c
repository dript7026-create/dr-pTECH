#include "sprite_renderer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// This implementation uses SDL2 and SDL_image (libpng) for quick prototyping.
// It's intentionally small and suitable for porting into an idtech2 client or a Windows prototype.

#include <SDL.h>
#include <SDL_image.h>

static SDL_Window *g_window = NULL;
static SDL_Renderer *g_renderer = NULL;

Sprite *sprite_load(const char *path) {
    if (!g_renderer) return NULL;
    SDL_Surface *surf = IMG_Load(path);
    if (!surf) {
        fprintf(stderr, "IMG_Load failed: %s\n", IMG_GetError());
        return NULL;
    }
    // Expect single-row animation: width = frame width * frames
    // If file naming/metadata required, caller should ensure frames via filename convention.
    int w = surf->w;
    int h = surf->h;
    // Heuristic: if width is divisible by height, treat frames = width/height
    int frames = 1;
    if (h > 0 && w % h == 0) frames = w / h;
    SDL_Texture *tex = SDL_CreateTextureFromSurface(g_renderer, surf);
    SDL_FreeSurface(surf);
    if (!tex) return NULL;
    Sprite *s = (Sprite*)calloc(1, sizeof(Sprite));
    s->width = w / frames;
    s->height = h;
    s->frames = frames;
    s->texture = tex;
    return s;
}

void sprite_free(Sprite *s) {
    if (!s) return;
    if (s->texture) SDL_DestroyTexture((SDL_Texture*)s->texture);
    free(s);
}

void sprite_draw(Sprite *s, int frame, int x, int y) {
    if (!s || !s->texture) return;
    frame = frame % s->frames;
    SDL_Rect src = { frame * s->width, 0, s->width, s->height };
    SDL_Rect dst = { x, y, s->width, s->height };
    SDL_RenderCopy(g_renderer, (SDL_Texture*)s->texture, &src, &dst);
}

int renderer_init(int w, int h, const char *title) {
    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return 0;
    }
    int flags = IMG_INIT_PNG;
    if (!(IMG_Init(flags) & flags)) {
        fprintf(stderr, "IMG_Init failed: %s\n", IMG_GetError());
        SDL_Quit();
        return 0;
    }
    g_window = SDL_CreateWindow(title, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, w, h, 0);
    if (!g_window) {
        fprintf(stderr, "SDL_CreateWindow failed: %s\n", SDL_GetError());
        IMG_Quit();
        SDL_Quit();
        return 0;
    }
    g_renderer = SDL_CreateRenderer(g_window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!g_renderer) {
        fprintf(stderr, "SDL_CreateRenderer failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(g_window);
        IMG_Quit();
        SDL_Quit();
        return 0;
    }
    return 1;
}

void renderer_shutdown(void) {
    if (g_renderer) SDL_DestroyRenderer(g_renderer);
    if (g_window) SDL_DestroyWindow(g_window);
    IMG_Quit();
    SDL_Quit();
}

void renderer_present(void) {
    SDL_RenderPresent(g_renderer);
}

void renderer_clear(uint8_t r, uint8_t g, uint8_t b) {
    SDL_SetRenderDrawColor(g_renderer, r, g, b, 255);
    SDL_RenderClear(g_renderer);
}

int renderer_poll_quit(void) {
    SDL_Event ev;
    while (SDL_PollEvent(&ev)) {
        if (ev.type == SDL_QUIT) return 1;
        if (ev.type == SDL_KEYDOWN && ev.key.keysym.sym == SDLK_ESCAPE) return 1;
    }
    return 0;
}
