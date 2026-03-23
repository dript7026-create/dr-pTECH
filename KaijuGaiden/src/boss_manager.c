#include "boss_manager.h"
#include <gba.h>

void boss_manager_init(Boss* b, int id) {
    if (!b) return;
    b->id = id;
    b->hp = 100; // prototype HP
    b->phase = 1;
    b->ecosystem_id = id % 4;
}

void boss_manager_update(Boss* b) {
    if (!b) return;
    if (b->hp <= 66 && b->phase == 1) b->phase = 2;
    if (b->hp <= 33 && b->phase == 2) b->phase = 3;
}

int boss_manager_is_defeated(Boss* b) {
    return b && b->hp <= 0;
}

int boss_manager_spawn_minion_drops(void) {
    // prototype: each call returns 1 growth nanoCell
    return 1;
}

int boss_manager_get_cypher_drop(Boss* b) {
    if (!b) return -1;
    // map ecosystem to cypher id
    return (int)b->ecosystem_id;
}
