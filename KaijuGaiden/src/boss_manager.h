#ifndef KAJ_BOSS_MANAGER_H
#define KAJ_BOSS_MANAGER_H

#include <stdint.h>

typedef struct Boss {
    int id;
    int hp;
    int phase;
    uint8_t ecosystem_id;
} Boss;

void boss_manager_init(Boss* b, int id);
void boss_manager_update(Boss* b);
int boss_manager_is_defeated(Boss* b);

// simulate minion drops: returns number of growth nanocells dropped
int boss_manager_spawn_minion_drops(void);

// on defeat, return cypher id
int boss_manager_get_cypher_drop(Boss* b);

#endif // KAJ_BOSS_MANAGER_H
