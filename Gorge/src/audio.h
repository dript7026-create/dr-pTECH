#ifndef GORGE_AUDIO_H
#define GORGE_AUDIO_H

#include <stdint.h>

typedef enum GorgeSongId {
    GORGE_SONG_TITLE = 0,
    GORGE_SONG_WORLD = 1,
    GORGE_SONG_BATTLE = 2,
    GORGE_SONG_VICTORY = 3,
    GORGE_SONG_DEFEAT = 4,
    GORGE_SONG_COUNT = 5
} GorgeSongId;

typedef enum GorgeSfxId {
    GORGE_SFX_MENU = 0,
    GORGE_SFX_DRAW = 1,
    GORGE_SFX_HIT = 2,
    GORGE_SFX_MISS = 3,
    GORGE_SFX_COUPLE = 4,
    GORGE_SFX_EVOLVE = 5,
    GORGE_SFX_REWARD = 6,
    GORGE_SFX_GUARD = 7,
    GORGE_SFX_PULSE = 8,
    GORGE_SFX_STATUS = 9,
    GORGE_SFX_COUNT = 10
} GorgeSfxId;

void gorge_audio_init(void);
void gorge_audio_play_song(GorgeSongId song_id);
void gorge_audio_play_sfx(GorgeSfxId sfx_id);
void gorge_audio_tick(void);

#endif
