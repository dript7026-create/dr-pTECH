#pragma once

// Minimal sprite-sheet loader/renderer API for prototyping.
// Uses SDL2 surfaces/textures + libpng when built.

#include <stdint.h>

typedef struct Sprite {
    int width;      // frame width
    int height;     // frame height
    int frames;     // number of frames (single row assumed)
    void *texture;  // backend texture pointer (SDL_Texture* when using SDL)
} Sprite;

// Load a sprite sheet: PNG with frames laid out in a single row.
// Returns NULL on failure.
Sprite *sprite_load(const char *path);

// Free sprite
void sprite_free(Sprite *s);

// Draw a frame at integer coordinates. Backend-specific.
void sprite_draw(Sprite *s, int frame, int x, int y);

// Initialize / shutdown renderer
int renderer_init(int w, int h, const char *title);
void renderer_shutdown(void);

// Present frame (swap buffers)
void renderer_present(void);

// Clear screen with RGB color
void renderer_clear(uint8_t r, uint8_t g, uint8_t b);

// Simple poll for quit. Returns non-zero if should quit.
int renderer_poll_quit(void);
