#ifndef KAJ_STATE_H
#define KAJ_STATE_H

#include <stdint.h>

typedef struct GameState {
    uint32_t cleared_bosses; // bitfield per boss id
    uint32_t collected_cyphers; // bitfield per cypher id
} GameState;

extern GameState g_state;

void state_set_cleared(int boss_id);
int state_is_cleared(int boss_id);
void state_add_cypher(int cypher_id);
int state_has_cypher(int cypher_id);

#endif // KAJ_STATE_H
