#ifndef FARMERS_FEATHER_SAVE_DATA_H
#define FARMERS_FEATHER_SAVE_DATA_H

#include <stdint.h>

#define SAVE_PROFILE_COUNT 3u
#define MAX_SETTLEMENTS 12u
#define MAX_PLOTS 16u

#define SAVE_MAGIC 0xF473u
#define SAVE_VERSION 5u

typedef struct {
    uint8_t A;
    uint8_t K;
    uint8_t B;
    uint8_t L;
    uint8_t gC;
    uint8_t gW;
    uint8_t gU;
    uint8_t gZ;
    uint8_t gSg;
    uint8_t gM;
    uint8_t emb;
    uint8_t dev;
    uint8_t inst;
    uint8_t lang;
    uint8_t cult;
    uint8_t ext;
    uint8_t frag;
    uint8_t hs_a;
    uint8_t hs_b;
    uint8_t hs_g;
} FarmerVector;

typedef struct {
    uint8_t active;
    uint8_t built;
    uint8_t feather_ready;
    uint16_t tile_x;
    uint16_t tile_y;
} Settlement;

typedef struct {
    uint8_t active;
    uint8_t stage;
    uint16_t tile_x;
    uint16_t tile_y;
    uint16_t timer;
} Plot;

typedef struct {
    uint16_t magic;
    uint8_t version;
    uint8_t slot_index;
    uint16_t world_seed;
    uint16_t player_x;
    uint16_t player_y;
    uint16_t phase_timer;
    uint8_t health;
    uint8_t max_health;
    uint8_t wood;
    uint8_t grain;
    uint8_t level;
    uint8_t xp;
    uint8_t phase;
    uint8_t boss_active;
    uint8_t boss_defeated;
    uint8_t weapon_level;
    uint8_t armor_level;
    FarmerVector farmer;
    Settlement settlements[MAX_SETTLEMENTS];
    Plot plots[MAX_PLOTS];
    uint16_t checksum;
} SaveSlot;

extern SaveSlot g_save_slots[SAVE_PROFILE_COUNT];

#endif