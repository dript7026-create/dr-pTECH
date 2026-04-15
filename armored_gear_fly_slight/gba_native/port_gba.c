#include "port_gba.h"

#include <gba_interrupt.h>
#include <gba_systemcalls.h>
#include <gba_video.h>

#define MODE4_PAGE_FLAG 0x0010u
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

static volatile uint16_t *const k_mode4_pages[2] = {
    (volatile uint16_t *)0x06000000,
    (volatile uint16_t *)0x0600A000,
};

static uint8_t s_draw_page = 1u;
static uint8_t s_music_step = 0u;

static uint16_t tone_reg_from_hz(uint16_t hz) {
    uint32_t value;
    if (hz < 64u) hz = 64u;
    if (hz > 2000u) hz = 2000u;
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

void port_gba_audio_init(void) {
    REG_AUDIO_SOUNDCNT_X = 0x0080u;
    REG_AUDIO_SOUNDCNT_L = 0x1177u;
    REG_AUDIO_SOUNDCNT_H = 0x000Bu;
    s_music_step = 0u;
}

void port_gba_init(void) {
    irqInit();
    irqEnable(IRQ_VBLANK);
    REG_DISPCNT = MODE_4 | BG2_ENABLE;
    s_draw_page = 1u;
    port_gba_audio_init();
}

void port_gba_wait_vblank(void) {
    VBlankIntrWait();
}

void port_gba_poll_input(PortInputState *input) {
    if (!input) {
        return;
    }

    scanKeys();
    input->held = keysHeld();
    input->pressed = keysDown();
    input->released = keysUp();
}

void port_gba_audio_step(uint16_t frame, uint8_t pressure) {
    static const uint16_t calm_notes[8] = {262u, 330u, 392u, 330u, 440u, 392u, 330u, 294u};
    static const uint16_t tense_notes[8] = {220u, 262u, 294u, 220u, 330u, 294u, 262u, 196u};
    const uint16_t *sequence = (pressure > 120u) ? tense_notes : calm_notes;

    if ((frame & 15u) == 0u) {
        play_square_2(sequence[s_music_step & 7u], (uint8_t)(1u + ((pressure >> 5) & 1u)), 8u);
        if ((frame & 31u) == 0u) {
            play_square_1((uint16_t)(sequence[(s_music_step + 2u) & 7u] / 2u), 2u, 5u);
        }
        ++s_music_step;
    }
}

void port_gba_audio_fire(uint8_t weapon_rank) {
    play_square_1((uint16_t)(700u + weapon_rank * 90u), 2u, 11u);
}

void port_gba_audio_dash(void) {
    play_noise(9u, 2u);
    play_square_2(180u, 3u, 8u);
}

void port_gba_audio_spawn(uint8_t threat_rank) {
    play_square_2((uint16_t)(180u + threat_rank * 40u), 1u, 7u);
}

void port_gba_audio_hit(uint8_t defeated) {
    if (defeated) {
        play_square_1(220u, 1u, 10u);
        play_noise(8u, 1u);
    } else {
        play_square_1(420u, 2u, 7u);
    }
}

volatile uint16_t *port_gba_get_draw_buffer(void) {
    return k_mode4_pages[s_draw_page];
}

void port_gba_present(void) {
    if (s_draw_page == 0u) {
        REG_DISPCNT &= (uint16_t)(~MODE4_PAGE_FLAG);
    } else {
        REG_DISPCNT |= MODE4_PAGE_FLAG;
    }

    s_draw_page ^= 1u;
}