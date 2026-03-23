// Minimal demo that loads KaijuGaiden placeholder sprite sheets and shows them
#include "sprite_renderer.h"
#include <stdio.h>
int main(int argc, char **argv) {
    if (!renderer_init(640, 480, "KaijuGaiden idtech2_port Demo")) return 1;
    // Try to load assets from KaijuGaiden/assets/placeholderassets
    const char *base = "KaijuGaiden/assets/placeholderassets/";
    const char *files[] = {
        "KaijuGaiden_placeholderasset_Rei_0001.png",
        "KaijuGaiden_placeholderasset_minion_0001.png",
        "KaijuGaiden_placeholderasset_attackfx_0001.png",
        NULL
    };
    Sprite *sprites[4] = {0};
    int i=0;
    for (; files[i]; ++i) {
        char path[1024];
        snprintf(path, sizeof(path), "%s%s", base, files[i]);
        sprites[i] = sprite_load(path);
        if (!sprites[i]) fprintf(stderr, "Failed to load %s\n", path);
    }
    int frame = 0;
    while (!renderer_poll_quit()) {
        renderer_clear(0x10, 0x18, 0x28);
        if (sprites[0]) sprite_draw(sprites[0], frame/6 % sprites[0]->frames, 100, 120);
        if (sprites[1]) sprite_draw(sprites[1], frame/6 % sprites[1]->frames, 200, 120);
        if (sprites[2]) sprite_draw(sprites[2], frame/6 % sprites[2]->frames, 300, 120);
        renderer_present();
        SDL_Delay(16);
        frame++;
    }
    for (i=0;i<3;i++) if (sprites[i]) sprite_free(sprites[i]);
    renderer_shutdown();
    return 0;
}
