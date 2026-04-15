#ifndef FARMERS_FEATHER_GAME_TYPES_H
#define FARMERS_FEATHER_GAME_TYPES_H

#include <stdint.h>
#include "save_data.h"

/* Enemy data */
typedef struct {
    uint8_t active;
    uint8_t type;
    uint8_t tier;
    uint8_t state;
    uint8_t hp;
    uint8_t poise;
    uint8_t poise_max;
    uint8_t timer;
    int8_t vx;
    int8_t vy;
    uint16_t x;
    uint16_t y;
} Enemy;

/* Impact (collision/damage) data */
typedef struct {
    uint8_t active;
    uint16_t tile_x;
    uint16_t tile_y;
    uint8_t timer;
} Impact;

/* Ensembl data for field calculations */
typedef struct {
    uint8_t Wc;
    uint8_t Cp;
    uint8_t Mh;
    uint8_t Br;
    uint8_t Ep;
    uint8_t Cl;
} Ens;

/* Barycentric coordinates */
typedef struct {
    uint8_t h;
    uint8_t c;
    uint8_t t;
} Bary;

/* Frequency band data */
typedef struct {
    uint8_t con;
    uint8_t ctr;
    uint8_t itv;
    uint8_t can;
    uint8_t obs;
} Bands;

/* Object strata layers */
typedef struct {
    uint8_t Os;
    uint8_t Oc;
    uint8_t Oo;
} ObjStrata;

/* Hyper-dimensional state (3D projection) */
typedef struct {
    uint8_t kin;
    uint8_t dom;
    uint8_t obs;
} Hyper3;

/* Race result metrics */
typedef struct {
    uint8_t Pgoal;
    uint8_t Pfoul;
    uint8_t Gw;
    int16_t Psi;
} RaceResult;

/* Tier classification */
typedef struct {
    uint8_t id;
    uint8_t ego;
    uint8_t sup;
} Tiers;

/* Full field state evaluation */
typedef struct {
    Bary geo;
    ObjStrata objects;
    Hyper3 hyper;
    RaceResult race;
    Tiers tiers;
    Bands bands;
    uint8_t dom;
    uint8_t rest_h;
    uint8_t rest_c;
    uint8_t rest_t;
    uint8_t irv;
    uint8_t floor;
    uint8_t phi;
    uint8_t tension;
    uint8_t coherence_state;
    uint8_t delta;
    uint8_t r3;
    uint8_t border;
} FieldState;

#endif
