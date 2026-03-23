#include <gba.h>
#include <stdio.h>
#include "game.h"
#include "genetics.h"
#include "boss.h"
#include "state.h"
#include "password.h"
#include "vn.h"
#include "ui.h"
#include "audio.h"

// Simple title/menu implementation using consoleDemoInit/iprintf

void game_title_sequence(void) {
    consoleDemoInit();
    iprintf("drIpTECH\n");
    iprintf("by a fanzovNG\n\n");
    iprintf("Kaiju Gaiden\n\n");
    iprintf("Press START\n");
}

void game_main_menu(void) {
    int running = 1;
    ui_init();
    audio_init();
    while (running) {
        VBlankIntrWait();
        scanKeys();
        u16 keys = keysDown();
            iprintf("\n\nMenu:\nA: New Game  B: Use Password\nSTART: Visual Novel\nSELECT: Apply Growth NanoCell (debug)\n");
        if (keys & KEY_A) {
            iprintf("Starting New Game...\n");
            // Enter boss demo for prototype
            consoleDemoInit();
            boss_fight_demo();
            consoleDemoInit();
            game_title_sequence();
        }
        if (keys & KEY_B) {
            iprintf("Enter Password: (stub)\n");
            // Password input stub
            game_handle_password("stub");
        }
        if (keys & KEY_START) {
            iprintf("Opening Visual Novel (stub)\n");
            consoleDemoInit();
            vn_play();
            consoleDemoInit();
            game_title_sequence();
        }
            // create a prototype player entity for genetics testing
            static Entity player = { .genome_id = 0, .growth_tier = 0, .variant = 0, .vib_signature = 0,
                                     .hp = 100, .max_hp = 100, .regen_rate = 2,
                                     .pending_nanocell_amount = 0, .pending_nanocell_polarity = 0, .pending_nanocell_timer_ms = 0,
                                     .visual_cue = 0 };
            // tick genetics each loop (approx 16ms per frame)
            genetics_tick(&player, 16);
            ui_draw_hud(&player);
            if (keys & KEY_SELECT) {
                int tier = apply_growth_nano(&player);
                iprintf("Applied Growth NanoCell. new tier=%d\n", tier);
                iprintf("Player variant: %s\n", get_variant_name(&player));
            }
            if (keys & KEY_UP) {
                deposit_nanocells(&player, 80, +1, 2000);
                iprintf("Deposited benevolent nanocells. HP=%u/%u\n", player.hp, player.max_hp);
            }
            if (keys & KEY_DOWN) {
                deposit_nanocells(&player, 80, -1, 2000);
                iprintf("Deposited malignant nanocells. HP=%u/%u\n", player.hp, player.max_hp);
            }
            // Debug: apply vibrational affectation with L/R
            if (keys & KEY_L) {
                apply_vibrational_affectation(&player, 50);
                iprintf("Applied vibration 50. %s\n", get_variant_name(&player));
            }
            if (keys & KEY_R) {
                apply_vibrational_affectation(&player, 220);
                iprintf("Applied vibration 220. %s\n", get_variant_name(&player));
            }
    }
}

void game_handle_password(const char* pwd) {
    // If pwd is NULL or empty, print an encoded password for current state
    if (!pwd || pwd[0] == '\0') {
        char out[32];
        encode_password(out, sizeof(out), g_state.cleared_bosses, g_state.collected_cyphers);
        iprintf("Encoded password: %s\n", out);
        return;
    }
    // Otherwise attempt to decode and apply
    uint32_t cb=0, cy=0;
    if (decode_password(pwd, &cb, &cy) == 0) {
        g_state.cleared_bosses = cb;
        g_state.collected_cyphers = cy;
        iprintf("Password applied. cleared=0x%08lX cyphers=0x%08lX\n", (unsigned long)cb, (unsigned long)cy);
    } else {
        iprintf("Invalid password.\n");
    }
}
