#include "world.h"
#include "generator.h"
#include "npc.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

static World g_world = {0};

void world_generate(const char* seed) {
    generator_seed_from_string(seed);
    g_world.w = generator_range(6, 12);
    g_world.h = generator_range(6, 12);
    int npc_ct = generator_range(6, 20);
    g_world.npc_count = npc_ct;
    npc_generate_for_world(npc_ct);
    // Precompute NPC influence weights so runtime moral logic is fast.
    npc_compute_influence();
}

const World* world_get() { return &g_world; }

char* world_summary() {
    char* out = (char*)malloc(512);
    if (!out) return NULL;
    snprintf(out, 512, "World %dx%d - NPCs: %d", g_world.w, g_world.h, g_world.npc_count);
    return out;
}

int world_export_snapshot(const char* out_path, const char* seed) {
    if (!out_path) return -1;
    FILE* f = fopen(out_path, "wb");
    if (!f) return -2;
    // Simple JSON export
    fprintf(f, "{\n");
    fprintf(f, "  \"seed\": \"%s\",\n", seed?seed:"");
    fprintf(f, "  \"width\": %d,\n", g_world.w);
    fprintf(f, "  \"height\": %d,\n", g_world.h);
    fprintf(f, "  \"npc_count\": %d,\n", g_world.npc_count);
    fprintf(f, "  \"npcs\": [\n");
    for (int i=0;i<g_world.npc_count;i++) {
        const NPC* p = npc_get(i);
        if (!p) continue;
        fprintf(f, "    { \"name\": \"%s\", \"x\": %d, \"y\": %d, \"moral\": %d, \"rival\": %s, \"influence\": %.3f }%s\n",
                p->name, p->x, p->y, p->moral_tendency, p->is_rival?"true":"false", p->influence, (i==g_world.npc_count-1)?"":" ,");
    }
    fprintf(f, "  ]\n}");
    fclose(f);
    return 0;
}
