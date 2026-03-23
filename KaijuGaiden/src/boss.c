#include <gba.h>
#include <stdio.h>
#include "boss.h"
#include "boss_manager.h"
#include "minion.h"
#include "genetics.h"
#include "state.h"
#include "password.h"
#include "ui.h"
#include "audio.h"

// Enhanced console-driven boss fight demo with nanocell drops wired to genetics.
void boss_fight_demo(void) {
    consoleDemoInit();
    iprintf("Prepare: Boss Encounter\n");
    // 3-2-1 Duel countdown
    for (int i = 3; i >= 1; --i) {
        iprintf("%d...\n", i);
        VBlankIntrWait();
        for (int f = 0; f < 30; ++f) VBlankIntrWait();
    }
    iprintf("DUEL!\n");

    // Prototype local player entity for the encounter
    Entity player = { .genome_id = 0, .growth_tier = 0, .variant = 0, .vib_signature = 0,
                      .hp = 100, .max_hp = 100, .regen_rate = 2,
                      .pending_nanocell_amount = 0, .pending_nanocell_polarity = 0, .pending_nanocell_timer_ms = 0,
                      .visual_cue = 0 };

    int boss_hp = 100;
    int phase = 1;
    int frame = 0;

    minion_manager_init();
    ui_init();
    audio_init();

    while (boss_hp > 0) {
        VBlankIntrWait();
        scanKeys();
        u16 keys = keysDown();

        // Tick genetics for player (simulate 16ms frame)
        genetics_tick(&player, 16);
        ui_draw_hud(&player);

        // Spawn minion periodically
        if ((frame % 120) == 0) minion_spawn();

        // Update minions (console-only)
        minion_update_all();

        // Player input: A attacks (prioritize minions)
        if (keys & KEY_A) {
            if (minion_count() > 0) {
                int killed = minion_damage_first(20);
                if (killed) {
                    // Minion drops growth nanoCells; wire to deposit on player
                    deposit_nanocells(&player, 12, +1, 1500);
                    iprintf("Minion killed. Benevolent Nanocells deposited (+12)\n");
                }
            } else {
                boss_hp -= 8;
                iprintf("Hit boss! HP = %d\n", boss_hp);
            }
        }

        // B clears a minion instantly
        if (keys & KEY_B) {
            if (minion_count() > 0) {
                minion_kill_first();
                // Purging minions sometimes releases malignant nanocells
                deposit_nanocells(&player, 8, -1, 1200);
                iprintf("Minion purged. Malignant Nanocells deposited (-8)\n");
            }
        }

        // Phase changes
        if (phase == 1 && boss_hp <= 66) { phase = 2; iprintf("Boss enrages: Phase 2!\n"); }
        if (phase == 2 && boss_hp <= 33) { phase = 3; iprintf("Boss furious: Phase 3!\n"); }

        // Boss attack can emit nanocell clouds: higher phases more malignant
        if ((frame % (80 - phase*10)) == 0) {
            iprintf("Boss attack pattern (phase %d)\n", phase);
            if (phase >= 2) {
                // boss emits malignant nanocell burst
                deposit_nanocells(&player, 20, -1, 800);
                iprintf("Boss emitted malignant nanocells!\n");
            }
        }

        // Debug keys while in fight: UP benevolent, DOWN malignant
        if (keys & KEY_UP) {
            deposit_nanocells(&player, 40, +1, 3000);
            iprintf("Debug: deposited benevolent nanocells to player\n");
        }
        if (keys & KEY_DOWN) {
            deposit_nanocells(&player, 40, -1, 3000);
            iprintf("Debug: deposited malignant nanocells to player\n");
        }

        // Advance frame
        frame++;
    }

    iprintf("Boss defeated! Dropped: Harbor Cypher (example)\n");
    iprintf("Apply cypher? Press A to Purify (heal) or B to Recode (mutate)\n");

    // Wait for input
    while (1) {
        VBlankIntrWait();
        scanKeys();
        u16 keys2 = keysDown();
        if (keys2 & KEY_A) {
            iprintf("Purify applied. Biome healed. Applying benevolent nanocells...\n");
            deposit_nanocells(&player, 200, +1, 5000);
            break;
        }
        if (keys2 & KEY_B) {
            iprintf("Recode applied. Mutation enabled. Applying malignant nanocells...\n");
            deposit_nanocells(&player, 200, -1, 5000);
            break;
        }
    }

    // Example: encode progress to password using current state
    char pwd[33];
    encode_password(pwd, sizeof(pwd), g_state.cleared_bosses, g_state.collected_cyphers);
    iprintf("Save Password: %s\n", pwd);
    iprintf("Player status: HP=%u/%u vib=%u variant=%u\n", player.hp, player.max_hp, player.vib_signature, player.variant);
    iprintf("Press START to return to title.\n");
    while (!(keysDown() & KEY_START)) { VBlankIntrWait(); scanKeys(); }
}
