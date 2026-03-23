#include <gba.h>
#include <stdio.h>
#include "audio.h"

void audio_init(void) {
    iprintf("Audio init (stub)\n");
}

void audio_play_bgm(const char* name) {
    iprintf("Play BGM: %s (stub)\n", name);
}

void audio_play_sfx(const char* name) {
    iprintf("Play SFX: %s (stub)\n", name);
}
