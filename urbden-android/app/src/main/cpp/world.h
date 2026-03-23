#ifndef URBDEN_WORLD_H
#define URBDEN_WORLD_H

#include <stddef.h>

#define MAX_NPCS 64

typedef struct {
    int w, h;
    int npc_count;
} World;

void world_generate(const char* seed);
const World* world_get();
char* world_summary(); // caller must free
// Export a snapshot of the generated world (JSON) into `out_path`. Returns 0 on success.
int world_export_snapshot(const char* out_path, const char* seed);

#endif
