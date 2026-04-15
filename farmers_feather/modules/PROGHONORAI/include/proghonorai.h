#ifndef PROGHONORAI_H
#define PROGHONORAI_H

#include <stdint.h>

#ifndef FARMERS_FEATHER_BANKED
#if defined(__SDCC) || defined(SDCC)
#define FARMERS_FEATHER_BANKED __banked
#else
#define FARMERS_FEATHER_BANKED
#endif
#endif

#define PROGHONORAI_PASSAGE_COUNT 5u

typedef enum {
    PROGHONORAI_PASSAGE_SPAWN = 0u,
    PROGHONORAI_PASSAGE_APPROACH = 1u,
    PROGHONORAI_PASSAGE_WINDUP = 2u,
    PROGHONORAI_PASSAGE_LUNGE = 3u,
    PROGHONORAI_PASSAGE_RENDER = 4u
} ProgHonorAiPassage;

typedef struct {
    uint16_t world_seed;
    uint8_t commitment;
    uint8_t patience;
    uint8_t footwork;
    uint8_t honor;
    uint8_t bond;
    uint8_t pressure;
    uint8_t passage_bias[PROGHONORAI_PASSAGE_COUNT];
} ProgHonorAiContext;

typedef struct {
    int8_t tier_delta;
    int8_t windup_delta;
    int8_t lunge_frames_delta;
    int8_t stun_delta;
    int8_t speed_delta;
    uint8_t visual_pressure;
    uint8_t render_mode;
    uint8_t passage_score;
} ProgHonorAiDirective;

void proghonorai_init(ProgHonorAiContext *context, uint16_t world_seed, uint8_t level, uint8_t weapon_rank, uint8_t armor_rank) FARMERS_FEATHER_BANKED;
void proghonorai_record_movement(ProgHonorAiContext *context, uint8_t moved, uint8_t tile_kind) FARMERS_FEATHER_BANKED;
void proghonorai_record_rake(ProgHonorAiContext *context, uint8_t connected) FARMERS_FEATHER_BANKED;
void proghonorai_record_use(ProgHonorAiContext *context, uint8_t restorative) FARMERS_FEATHER_BANKED;
void proghonorai_update(ProgHonorAiContext *context, uint8_t phase, uint8_t boss_active, uint8_t health, uint8_t max_health) FARMERS_FEATHER_BANKED;
void proghonorai_route(const ProgHonorAiContext *context, ProgHonorAiPassage passage, uint8_t threat, uint8_t tier, ProgHonorAiDirective *directive) FARMERS_FEATHER_BANKED;

#endif