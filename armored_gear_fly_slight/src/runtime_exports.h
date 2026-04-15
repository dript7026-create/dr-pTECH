#ifndef FARMERS_FEATHER_RUNTIME_EXPORTS_H
#define FARMERS_FEATHER_RUNTIME_EXPORTS_H

#include <stdint.h>

#include "game_types.h"

extern uint8_t g_profile_index;
extern uint8_t g_tutorial_overlay_enabled;
extern uint16_t g_world_seed;
extern uint16_t g_shrine_tile_x;
extern uint16_t g_shrine_tile_y;
extern uint16_t g_start_tile_x;
extern uint16_t g_start_tile_y;
extern uint8_t g_phase;
extern uint8_t g_boss_active;
extern uint8_t g_grain;

extern FarmerVector g_farmer;
extern Settlement g_settlements[];
extern Plot g_plots[];
extern Impact g_impacts[];

uint8_t profile_has_data(uint8_t profile_index);
void erase_profile_slot(uint8_t profile_index);
uint8_t clamp_u8(int16_t value);
uint16_t abs_u16_diff(uint16_t left, uint16_t right);
uint16_t hash16(uint16_t x, uint16_t y, uint16_t salt);
uint16_t approx_disc_distance(uint16_t tile_x, uint16_t tile_y);
uint8_t border_pressure(uint16_t distance);
uint8_t tutorial_tile_override(uint16_t tile_x, uint16_t tile_y);
uint8_t find_settlement_at(uint16_t tile_x, uint16_t tile_y);
uint8_t calc_x(const FarmerVector *c);
uint16_t calc_i(const FarmerVector *c);
void calc_geography(const Ens *y, uint8_t delta, Bary *geo);
uint8_t calc_irv(const Ens *y, uint8_t xi);
void calc_objects(const Bary *geo, const Ens *y, uint8_t irv, uint8_t delta, ObjStrata *objects);
void calc_race(const Ens *y, uint8_t rt, RaceResult *race);
uint8_t calc_dominion(const Bary *geo, const Ens *y, uint8_t gw, uint8_t rt);
void calc_rest(const Bary *geo, uint8_t dom, Bary *rest);
void calc_tiers(const Ens *y, const Bary *geo, uint8_t gw, Tiers *tiers);
void calc_hyper3(const Bary *geo, const Ens *y, uint8_t dom, uint8_t gw, uint8_t rt, int16_t psi, Hyper3 *hyper);
uint8_t calc_hyperself(const FarmerVector *c, const Hyper3 *hyper);
void calc_bands(const FarmerVector *c, const Ens *y, int16_t psi, uint8_t h_obs, Bands *bands);
uint8_t calc_tension(const FarmerVector *c, const Ens *y);
uint8_t calc_phi(const Bands *bands, uint8_t tension);
uint8_t calc_coh_floor(const FarmerVector *c);
uint8_t calc_coh_state(uint8_t phi, uint8_t floor_value, const Bands *bands);
uint8_t relative3_scalar(uint8_t q, uint8_t f, uint8_t s, uint8_t r, uint8_t g);

#endif