#include "npc.h"
#include "generator.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static NPC g_npcs[MAX_NPCS];
static int g_npc_count = 0;

static void make_name(char* buf, int n) {
    static const char* syll[] = {"ur","ben","den","mar","lo","xi","pa","ri","ton","vek","sol","gar"};
    int scount = sizeof(syll)/sizeof(syll[0]);
    int len = 0;
    for (int i=0;i<3 && len+6 < n;i++) {
        const char* part = syll[generator_range(0, scount-1)];
        int need = snprintf(buf+len, n-len, "%s", part);
        if (need < 0) break;
        len += need;
    }
}

void npc_generate_for_world(int count) {
    if (count < 0) count = 0;
    if (count > MAX_NPCS) count = MAX_NPCS;
    g_npc_count = count;
    for (int i=0;i<count;i++) {
        NPC* p = &g_npcs[i];
        make_name(p->name, sizeof(p->name));
        p->x = generator_range(0, 11);
        p->y = generator_range(0, 11);
        p->moral_tendency = generator_range(-1, 1);
        p->is_rival = (i == (generator_range(0, count-1)));
        p->influence = 0.0f;
    }
}

int npc_count() { return g_npc_count; }

const NPC* npc_get(int idx) {
    if (idx < 0 || idx >= g_npc_count) return NULL;
    return &g_npcs[idx];
}

char* npc_list_summary() {
    int max = 1024;
    char* out = (char*)malloc(max);
    if (!out) return NULL;
    out[0] = '\0';
    for (int i=0;i<g_npc_count;i++) {
        char line[128];
        const NPC* p = &g_npcs[i];
        snprintf(line, sizeof(line), "%d: %s @(%d,%d)%s\n", i, p->name, p->x, p->y, p->is_rival?" [RIVAL]":"");
        strncat(out, line, max - strlen(out) - 1);
    }
    return out;
}

// Precompute influence for every NPC so runtime queries are cheap.
void npc_compute_influence() {
    for (int i = 0; i < g_npc_count; ++i) {
        NPC* a = &g_npcs[i];
        float sum = (float)a->moral_tendency;
        for (int j = 0; j < g_npc_count; ++j) {
            if (i == j) continue;
            NPC* b = &g_npcs[j];
            int dx = a->x - b->x;
            int dy = a->y - b->y;
            int d2 = dx*dx + dy*dy;
            float decay = 1.0f / (1.0f + (float)d2);
            sum += (float)b->moral_tendency * decay;
        }
        a->influence = sum;
    }
}

float npc_get_influence(int idx) {
    const NPC* p = npc_get(idx);
    return p ? p->influence : 0.0f;
}
