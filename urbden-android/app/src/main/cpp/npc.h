#ifndef URBDEN_NPC_H
#define URBDEN_NPC_H

#include <stdbool.h>

typedef struct {
    char name[32];
    int x, y;
    bool is_rival;
    int moral_tendency; // -1..1
    float influence; // precomputed influence score (aggregated from neighbors)
} NPC;

void npc_generate_for_world(int count);
int npc_count();
const NPC* npc_get(int idx);
char* npc_list_summary(); // caller must free
void npc_compute_influence();
float npc_get_influence(int idx);

#endif
