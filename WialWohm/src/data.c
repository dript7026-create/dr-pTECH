#include "data.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char* mkname(const char* fmt, int idx) {
    char buf[128];
    int n = snprintf(buf, sizeof(buf), fmt, idx);
    if (n < 0) return NULL;
    char* s = malloc((size_t)n + 1);
    if (!s) return NULL;
    memcpy(s, buf, (size_t)n + 1);
    return s;
}

char* wial_evolutions[WIAL_EVOLUTIONS_COUNT];
char* enemies[ENEMIES_COUNT];
char* wohm_types[WOHM_TYPES_COUNT];
char* resources[RESOURCES_COUNT];
Crop crops[CROPS_COUNT];
char* tools[TOOLS_COUNT];

void init_game_data(void) {
    for (int i = 0; i < WIAL_EVOLUTIONS_COUNT; ++i) {
        wial_evolutions[i] = mkname("Wial Evolution %03d", i + 1);
    }

    for (int i = 0; i < ENEMIES_COUNT; ++i) {
        enemies[i] = mkname("Enemy Type %02d", i + 1);
    }

    const char* base_wohms[WOHM_TYPES_COUNT] = {
        "Gloom Caverns",
        "Sunken Farm",
        "Frost Vault",
        "Ashen Warrens",
        "Sacred Archive"
    };
    for (int i = 0; i < WOHM_TYPES_COUNT; ++i) {
        wohm_types[i] = malloc(strlen(base_wohms[i]) + 1);
        strcpy(wohm_types[i], base_wohms[i]);
    }

    for (int i = 0; i < RESOURCES_COUNT; ++i) {
        if ((i % 15) == 0) {
            resources[i] = mkname("Meal %03d", i + 1);
        } else if ((i % 7) == 0) {
            resources[i] = mkname("Ore %03d", i + 1);
        } else if ((i % 5) == 0) {
            resources[i] = mkname("Wood %03d", i + 1);
        } else {
            resources[i] = mkname("Resource %03d", i + 1);
        }
    }

    for (int i = 0; i < CROPS_COUNT; ++i) {
        char* id = mkname("Crop_%03d", i + 1);
        char* seed = mkname("Crop_%03d_Seed", i + 1);
        char* plant = mkname("Crop_%03d_Plant", i + 1);
        char* fruit = mkname("Crop_%03d_Fruit", i + 1);
        crops[i].id = id;
        crops[i].seed = seed;
        crops[i].plant = plant;
        crops[i].fruit = fruit;
    }

    tools[0] = mkname("Hand Axe", 0);
    tools[1] = mkname("Pick Axe", 0);
    tools[2] = mkname("Hoe", 0);
}

void cleanup_game_data(void) {
    for (int i = 0; i < WIAL_EVOLUTIONS_COUNT; ++i) free(wial_evolutions[i]);
    for (int i = 0; i < ENEMIES_COUNT; ++i) free(enemies[i]);
    for (int i = 0; i < WOHM_TYPES_COUNT; ++i) free(wohm_types[i]);
    for (int i = 0; i < RESOURCES_COUNT; ++i) free(resources[i]);
    for (int i = 0; i < CROPS_COUNT; ++i) {
        free(crops[i].id);
        free(crops[i].seed);
        free(crops[i].plant);
        free(crops[i].fruit);
    }
    for (int i = 0; i < TOOLS_COUNT; ++i) free(tools[i]);
}
