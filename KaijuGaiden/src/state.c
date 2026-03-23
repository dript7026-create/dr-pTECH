#include "state.h"

GameState g_state = {0,0};

void state_set_cleared(int boss_id) {
    if (boss_id >= 0 && boss_id < 32) g_state.cleared_bosses |= (1u << boss_id);
}

int state_is_cleared(int boss_id) {
    if (boss_id < 0 || boss_id >= 32) return 0;
    return (g_state.cleared_bosses >> boss_id) & 1u;
}

void state_add_cypher(int cypher_id) {
    if (cypher_id >= 0 && cypher_id < 32) g_state.collected_cyphers |= (1u << cypher_id);
}

int state_has_cypher(int cypher_id) {
    if (cypher_id < 0 || cypher_id >= 32) return 0;
    return (g_state.collected_cyphers >> cypher_id) & 1u;
}
