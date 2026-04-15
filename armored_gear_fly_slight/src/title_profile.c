#pragma bank 255

#include <gb/gb.h>
#include <gbdk/console.h>
#include <stdint.h>
#include <stdio.h>

#include "audio_runtime.h"
#include "runtime_exports.h"
#include "save_data.h"
#include "title_profile.h"

#define AUDIO_TRACK_TITLE 1u

void draw_title_slot_status(void) {
    gotoxy(0u, 7u);
    printf("PROFILE: %u   ", g_profile_index + 1u);
    gotoxy(0u, 8u);
    if (profile_has_data(g_profile_index)) {
        printf("MODE: LOAD   ");
    } else {
        printf("MODE: NEW    ");
    }
    gotoxy(0u, 9u);
    printf("D-PAD SLOT GLIDE");
    gotoxy(0u, 10u);
    printf("A SCRAP START");
}

void title_screen(void) {
    uint8_t joy;
    uint8_t prev;
    uint8_t pressed;
    uint8_t jingle_delay;
    prev = 0u;
    DISPLAY_ON;
    cls();
    printf("ARMORED GEAR:\n");
    printf("FLY SLIGHT\n\n");
    printf("WIREPUNK WRECKSUIT\n");
    printf("D-PAD GLIDE CHOOSE\n");
    printf("B FIRE // A SHIFT\n");
    printf("SCAV-CHIC EXOSHELL\n");
    printf("START BREACH ORBIT\n\n");
    draw_title_slot_status();
    audio_set_music(AUDIO_TRACK_TITLE);
    while (1) {
        wait_vbl_done();
        audio_update();
        joy = joypad();
        pressed = (uint8_t)(joy & (uint8_t)(~prev));
        if (pressed & (J_LEFT | J_UP)) {
            if (g_profile_index == 0u) g_profile_index = (uint8_t)(SAVE_PROFILE_COUNT - 1u);
            else --g_profile_index;
            audio_sfx_profile_select();
            draw_title_slot_status();
        }
        if (pressed & (J_RIGHT | J_DOWN)) {
            g_profile_index = (uint8_t)((g_profile_index + 1u) % SAVE_PROFILE_COUNT);
            audio_sfx_profile_select();
            draw_title_slot_status();
        }
        if (pressed & J_A) {
            erase_profile_slot(g_profile_index);
            audio_sfx_profile_erase();
            draw_title_slot_status();
        }
        if (pressed & J_START) {
            audio_sfx_profile_start();
            for (jingle_delay = 0u; jingle_delay < 8u; ++jingle_delay) {
                wait_vbl_done();
                audio_update();
            }
            break;
        }
        prev = joy;
    }
}
