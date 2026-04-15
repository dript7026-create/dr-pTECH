#ifndef GORGE_GAME_TYPES_H
#define GORGE_GAME_TYPES_H

#include <stdint.h>

#define GORGE_DECK_COUNT 14
#define GORGE_CARDS_PER_DECK 52
#define GORGE_TOTAL_CARDS (GORGE_DECK_COUNT * GORGE_CARDS_PER_DECK)
#define GORGE_MAX_HAND 8
#define GORGE_ROSTER_SIZE 3
#define GORGE_MAX_REWARDS 64
#define GORGE_PASSWORD_LEN 16

typedef enum GorgeCardKind {
    GORGE_CARD_CREATURE = 0,
    GORGE_CARD_HABITAT_JOOL = 1,
    GORGE_CARD_HABITAT_GAORG = 2
} GorgeCardKind;

typedef enum GorgeFamily {
    GORGE_FAMILY_GAOLITE = 0,
    GORGE_FAMILY_JEURGREN = 1,
    GORGE_FAMILY_FALLOWS = 2,
    GORGE_FAMILY_JOOLS = 3,
    GORGE_FAMILY_GAORG = 4
} GorgeFamily;

typedef enum GorgeAction {
    GORGE_ACTION_AGGRESS = 0,
    GORGE_ACTION_GUARD = 1,
    GORGE_ACTION_FOCUS = 2,
    GORGE_ACTION_PULSE = 3,
    GORGE_ACTION_HABITAT = 4,
    GORGE_ACTION_COUPLE = 5,
    GORGE_ACTION_EVOLVE = 6,
    GORGE_ACTION_SHIFT = 7,
    GORGE_ACTION_PURGE = 8,
    GORGE_ACTION_RALLY = 9,
    GORGE_ACTION_HUNT = 10,
    GORGE_ACTION_SWAP = 11,
    GORGE_ACTION_COUNT = 12
} GorgeAction;

typedef enum GorgeRole {
    GORGE_ROLE_STRIKER = 0,
    GORGE_ROLE_BULWARK = 1,
    GORGE_ROLE_ORACLE = 2,
    GORGE_ROLE_HARRIER = 3,
    GORGE_ROLE_CONDUIT = 4,
    GORGE_ROLE_BROOD = 5,
    GORGE_ROLE_COUNT = 6
} GorgeRole;

typedef enum GorgeInstinct {
    GORGE_INSTINCT_BALANCE = 0,
    GORGE_INSTINCT_RUSH = 1,
    GORGE_INSTINCT_SHELL = 2,
    GORGE_INSTINCT_TRICK = 3,
    GORGE_INSTINCT_COUNT = 4
} GorgeInstinct;

typedef enum GorgeAbility {
    GORGE_ABILITY_EMBERHEART = 0,
    GORGE_ABILITY_TIDEGLASS = 1,
    GORGE_ABILITY_SHELLSCRIPT = 2,
    GORGE_ABILITY_CANOPY_VEIL = 3,
    GORGE_ABILITY_VAULT_MEMORY = 4,
    GORGE_ABILITY_SNARE_HUNGER = 5,
    GORGE_ABILITY_CHORUS_ROOT = 6,
    GORGE_ABILITY_RIFT_QUARRY = 7,
    GORGE_ABILITY_COUNT = 8
} GorgeAbility;

typedef enum GorgeTechnique {
    GORGE_TECHNIQUE_CLEAVE = 0,
    GORGE_TECHNIQUE_TORRENT = 1,
    GORGE_TECHNIQUE_PRISM = 2,
    GORGE_TECHNIQUE_BRIAR = 3,
    GORGE_TECHNIQUE_QUARRY = 4,
    GORGE_TECHNIQUE_VOLT = 5,
    GORGE_TECHNIQUE_LEECH = 6,
    GORGE_TECHNIQUE_RUIN = 7,
    GORGE_TECHNIQUE_COUNT = 8
} GorgeTechnique;

typedef enum GorgeStance {
    GORGE_STANCE_BALANCE = 0,
    GORGE_STANCE_RUSH = 1,
    GORGE_STANCE_SHELL = 2,
    GORGE_STANCE_TRICK = 3,
    GORGE_STANCE_COUNT = 4
} GorgeStance;

typedef enum GorgeStatus {
    GORGE_STATUS_SCORCH = 1 << 0,
    GORGE_STATUS_SNARE = 1 << 1,
    GORGE_STATUS_HUSH = 1 << 2,
    GORGE_STATUS_FRAIL = 1 << 3,
    GORGE_STATUS_SPORE = 1 << 4
} GorgeStatus;

typedef struct GorgeCardDef {
    uint16_t id;
    uint8_t deck_id;
    uint8_t card_kind;
    uint8_t family;
    uint8_t stage;
    uint8_t habitat_mask;
    uint8_t role;
    uint8_t instinct;
    uint8_t ability;
    uint8_t technique;
    uint8_t degree;
    uint8_t angle;
    uint8_t cut;
    uint8_t range;
    uint8_t flow;
    uint8_t arc;
    uint8_t gauge;
    uint8_t hit_points;
    uint8_t patience_threshold;
    uint8_t speed;
    uint8_t power;
    int16_t evolve_a;
    int16_t evolve_b;
    const char *name;
    const char *flavor;
} GorgeCardDef;

typedef struct GorgeDeckDef {
    uint8_t id;
    uint8_t route_row;
    uint8_t route_col;
    uint8_t pressure;
    const char *name;
    const char *theme;
    const char *boss_title;
    const char *relic_name;
    uint8_t reward_cards[3];
} GorgeDeckDef;

typedef struct GorgeSongEvent {
    uint16_t hz_a;
    uint16_t hz_b;
    uint8_t volume_a;
    uint8_t volume_b;
    uint8_t noise_pitch;
    uint8_t frames;
} GorgeSongEvent;

typedef struct GorgeSongDef {
    const char *name;
    const GorgeSongEvent *events;
    uint16_t event_count;
} GorgeSongDef;

#endif
