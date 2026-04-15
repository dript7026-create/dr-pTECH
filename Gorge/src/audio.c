#include "audio.h"

#include <gba.h>

#include "game_types.h"
#include "generated/gorge_content.h"

#define REG_AUDIO_SOUNDCNT_L (*(volatile uint16_t *)0x04000080)
#define REG_AUDIO_SOUNDCNT_H (*(volatile uint16_t *)0x04000082)
#define REG_AUDIO_SOUNDCNT_X (*(volatile uint16_t *)0x04000084)
#define REG_AUDIO_SOUND1CNT_L (*(volatile uint16_t *)0x04000060)
#define REG_AUDIO_SOUND1CNT_H (*(volatile uint16_t *)0x04000062)
#define REG_AUDIO_SOUND1CNT_X (*(volatile uint16_t *)0x04000064)
#define REG_AUDIO_SOUND2CNT_L (*(volatile uint16_t *)0x04000068)
#define REG_AUDIO_SOUND2CNT_H (*(volatile uint16_t *)0x0400006C)
#define REG_AUDIO_SOUND4CNT_L (*(volatile uint16_t *)0x04000078)
#define REG_AUDIO_SOUND4CNT_H (*(volatile uint16_t *)0x0400007C)

static GorgeSongId s_current_song = GORGE_SONG_TITLE;
static uint16_t s_song_index = 0;
static uint8_t s_song_frames_left = 0;
static uint8_t s_sfx_frames_left = 0;
static uint16_t s_sfx_hz = 0;
static uint8_t s_sfx_volume = 0;
static uint8_t s_sfx_noise = 0;

static uint16_t tone_reg_from_hz(uint16_t hz) {
    uint32_t value;
    if (hz < 64u) hz = 64u;
    if (hz > 2047u) hz = 2047u;
    value = 2048u - (131072u / hz);
    if (value > 2047u) value = 2047u;
    return (uint16_t)value;
}

static void play_square_1(uint16_t hz, uint8_t duty, uint8_t volume) {
    REG_AUDIO_SOUND1CNT_L = 0u;
    REG_AUDIO_SOUND1CNT_H = (uint16_t)(((duty & 3u) << 6) | (2u << 8) | (1u << 11) | ((volume & 15u) << 12));
    REG_AUDIO_SOUND1CNT_X = (uint16_t)(0x8000u | tone_reg_from_hz(hz));
}

static void play_square_2(uint16_t hz, uint8_t duty, uint8_t volume) {
    REG_AUDIO_SOUND2CNT_L = (uint16_t)(((duty & 3u) << 6) | (2u << 8) | (1u << 11) | ((volume & 15u) << 12));
    REG_AUDIO_SOUND2CNT_H = (uint16_t)(0x8000u | tone_reg_from_hz(hz));
}

static void play_noise(uint8_t volume, uint8_t pitch) {
    REG_AUDIO_SOUND4CNT_L = (uint16_t)((2u << 8) | (1u << 11) | ((volume & 15u) << 12));
    REG_AUDIO_SOUND4CNT_H = (uint16_t)(0x8000u | ((pitch & 7u) << 4) | 0x0003u);
}

void gorge_audio_init(void) {
    REG_AUDIO_SOUNDCNT_X = 0x0080u;
    REG_AUDIO_SOUNDCNT_L = 0x1177u;
    REG_AUDIO_SOUNDCNT_H = 0x000Bu;
    s_current_song = GORGE_SONG_TITLE;
    s_song_index = 0;
    s_song_frames_left = 0;
    s_sfx_frames_left = 0;
}

void gorge_audio_play_song(GorgeSongId song_id) {
    if ((unsigned)song_id >= GORGE_SONG_COUNT) {
        return;
    }
    if (s_current_song == song_id && s_song_frames_left > 0) {
        return;
    }
    s_current_song = song_id;
    s_song_index = 0;
    s_song_frames_left = 0;
}

void gorge_audio_play_sfx(GorgeSfxId sfx_id) {
    switch (sfx_id) {
        case GORGE_SFX_MENU:
            s_sfx_hz = 660u;
            s_sfx_volume = 7u;
            s_sfx_noise = 0u;
            s_sfx_frames_left = 8u;
            break;
        case GORGE_SFX_DRAW:
            s_sfx_hz = 540u;
            s_sfx_volume = 8u;
            s_sfx_noise = 0u;
            s_sfx_frames_left = 10u;
            break;
        case GORGE_SFX_HIT:
            s_sfx_hz = 360u;
            s_sfx_volume = 10u;
            s_sfx_noise = 2u;
            s_sfx_frames_left = 14u;
            break;
        case GORGE_SFX_MISS:
            s_sfx_hz = 240u;
            s_sfx_volume = 6u;
            s_sfx_noise = 1u;
            s_sfx_frames_left = 12u;
            break;
        case GORGE_SFX_COUPLE:
            s_sfx_hz = 880u;
            s_sfx_volume = 9u;
            s_sfx_noise = 0u;
            s_sfx_frames_left = 18u;
            break;
        case GORGE_SFX_EVOLVE:
            s_sfx_hz = 990u;
            s_sfx_volume = 10u;
            s_sfx_noise = 0u;
            s_sfx_frames_left = 22u;
            break;
        case GORGE_SFX_REWARD:
            s_sfx_hz = 720u;
            s_sfx_volume = 9u;
            s_sfx_noise = 0u;
            s_sfx_frames_left = 20u;
            break;
        case GORGE_SFX_GUARD:
            s_sfx_hz = 420u;
            s_sfx_volume = 8u;
            s_sfx_noise = 1u;
            s_sfx_frames_left = 10u;
            break;
        case GORGE_SFX_PULSE:
            s_sfx_hz = 920u;
            s_sfx_volume = 10u;
            s_sfx_noise = 2u;
            s_sfx_frames_left = 16u;
            break;
        case GORGE_SFX_STATUS:
            s_sfx_hz = 280u;
            s_sfx_volume = 7u;
            s_sfx_noise = 3u;
            s_sfx_frames_left = 12u;
            break;
        default:
            break;
    }
}

void gorge_audio_tick(void) {
    const GorgeSongDef *song;
    const GorgeSongEvent *event;

    if ((unsigned)s_current_song >= GORGE_SONG_COUNT) {
        s_current_song = GORGE_SONG_TITLE;
    }

    song = &g_gorge_songs[(unsigned)s_current_song];
    if (song->event_count > 0u) {
        if (s_song_frames_left == 0u) {
            event = &song->events[s_song_index % song->event_count];
            if (event->hz_a > 0u && event->volume_a > 0u) {
                play_square_1(event->hz_a, 2u, event->volume_a);
            }
            if (event->hz_b > 0u && event->volume_b > 0u) {
                play_square_2(event->hz_b, 1u, event->volume_b);
            }
            if (event->noise_pitch > 0u) {
                play_noise(4u, event->noise_pitch);
            }
            s_song_frames_left = event->frames;
            s_song_index = (uint16_t)((s_song_index + 1u) % song->event_count);
        }
        if (s_song_frames_left > 0u) {
            --s_song_frames_left;
        }
    }

    if (s_sfx_frames_left > 0u) {
        play_square_2(s_sfx_hz, 3u, s_sfx_volume);
        if (s_sfx_noise > 0u) {
            play_noise(6u, s_sfx_noise);
        }
        --s_sfx_frames_left;
    }
}
