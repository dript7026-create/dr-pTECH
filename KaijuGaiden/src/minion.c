#include <gba.h>
#include <stdio.h>
#include "minion.h"

#define MAX_MINIONS 8

static int minion_hp[MAX_MINIONS];
static int minion_alive[MAX_MINIONS];

void minion_manager_init(void) {
    for (int i = 0; i < MAX_MINIONS; ++i) { minion_alive[i] = 0; minion_hp[i] = 0; }
}

void minion_spawn(void) {
    for (int i = 0; i < MAX_MINIONS; ++i) {
        if (!minion_alive[i]) {
            minion_alive[i] = 1;
            minion_hp[i] = 20;
            iprintf("Minion spawned (slot %d)\n", i);
            return;
        }
    }
}

int minion_count(void) {
    int c = 0;
    for (int i = 0; i < MAX_MINIONS; ++i) if (minion_alive[i]) c++;
    return c;
}

void minion_update_all(void) {
    // For console prototype, print existing minions periodically
    static int ticker = 0;
    ticker++;
    if ((ticker % 180) == 0) {
        iprintf("Minion status: ");
        for (int i = 0; i < MAX_MINIONS; ++i) if (minion_alive[i]) iprintf("[%d:HP=%d] ", i, minion_hp[i]);
        iprintf("\n");
    }
}

int minion_damage_first(int dmg) {
    for (int i = 0; i < MAX_MINIONS; ++i) {
        if (minion_alive[i]) {
            minion_hp[i] -= dmg;
            if (minion_hp[i] <= 0) { minion_alive[i] = 0; minion_hp[i] = 0; return 1; }
            return 0;
        }
    }
    return 0;
}

void minion_kill_first(void) {
    for (int i = 0; i < MAX_MINIONS; ++i) {
        if (minion_alive[i]) { minion_alive[i] = 0; minion_hp[i] = 0; iprintf("Minion killed (slot %d)\n", i); return; }
    }
}
