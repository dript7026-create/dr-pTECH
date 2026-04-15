#pragma bank 255

#include <gb/gb.h>
#include <stdint.h>
#include <stdio.h>

#include "game_types.h"
#include "runtime_exports.h"
#include "save_data.h"
#include "field_state.h"

#define WORLD_GRID_TILES 4096u
#define WORLD_CHUNK_SHIFT 4u
#define DISC_CENTER_TILE (WORLD_GRID_TILES / 2u)
#define DISC_RADIUS_TILES 1788u
#define DISC_SAFE_RADIUS 1460u
#define DISC_BEACH_RADIUS 1660u
#define DISC_HARD_RADIUS 1768u
#define MAX_IMPACTS 8u
#define MAX_SETTLEMENTS 12u
#define TILE_WATER 0u
#define TILE_SAND 1u
#define TILE_GRASS 2u
#define TILE_SOIL 3u
#define TILE_CROP 4u
#define TILE_RIPE 5u
#define TILE_TREE 6u
#define TILE_ROCK 7u
#define TILE_SITE 8u
#define TILE_HUT 9u
#define TILE_FEATHER 10u
#define TILE_SHRINE 11u
#define TILE_CRATER 12u

void evaluate_field_state(uint16_t tile_x, uint16_t tile_y, FieldState *state) {
    uint16_t chunk_x;
    uint16_t chunk_y;
    uint16_t seed0;
    uint16_t seed1;
    uint16_t seed2;
    uint16_t seed3;
    uint16_t seed4;
    uint16_t distance;
    uint16_t i_value;
    uint8_t support;
    uint8_t peril;
    uint8_t built;
    uint8_t nearby_plots;
    uint8_t index;
    uint8_t x_value;
    uint8_t h_obs;
    Bary rest;

    chunk_x = tile_x >> WORLD_CHUNK_SHIFT;
    chunk_y = tile_y >> WORLD_CHUNK_SHIFT;
    seed0 = hash16(chunk_x, chunk_y, g_world_seed);
    seed1 = hash16((uint16_t)(chunk_x + 5u), (uint16_t)(chunk_y + 11u), (uint16_t)(g_world_seed + 17u));
    seed2 = hash16((uint16_t)(chunk_x + 7u), (uint16_t)(chunk_y + 3u), (uint16_t)(g_world_seed + 43u));
    seed3 = hash16((uint16_t)(chunk_x + 13u), (uint16_t)(chunk_y + 9u), (uint16_t)(g_world_seed + 71u));
    seed4 = hash16((uint16_t)(chunk_x + 2u), (uint16_t)(chunk_y + 15u), (uint16_t)(g_world_seed + 97u));
    distance = approx_disc_distance(tile_x, tile_y);
    state->border = border_pressure(distance);
    support = 0u;
    peril = 0u;
    built = 0u;
    nearby_plots = 0u;

    for (index = 0u; index < MAX_SETTLEMENTS; ++index) {
        if (!g_settlements[index].active) continue;
        if (abs_u16_diff(tile_x, g_settlements[index].tile_x) < 24u && abs_u16_diff(tile_y, g_settlements[index].tile_y) < 24u) {
            support = clamp_u8((int16_t)support + 18);
            if (g_settlements[index].built) {
                support = clamp_u8((int16_t)support + 24);
                ++built;
            }
        }
    }
    for (index = 0u; index < MAX_PLOTS; ++index) {
        if (g_plots[index].active && abs_u16_diff(tile_x, g_plots[index].tile_x) < 10u && abs_u16_diff(tile_y, g_plots[index].tile_y) < 10u) {
            nearby_plots = clamp_u8((int16_t)nearby_plots + 8);
        }
    }
    for (index = 0u; index < MAX_IMPACTS; ++index) {
        if (g_impacts[index].active && abs_u16_diff(tile_x, g_impacts[index].tile_x) < 18u && abs_u16_diff(tile_y, g_impacts[index].tile_y) < 18u) {
            peril = clamp_u8((int16_t)peril + 34);
        }
    }
    if (g_boss_active) peril = clamp_u8((int16_t)peril + 72);

    state->delta = clamp_u8((int16_t)((seed3 & 0xFFu) ^ (g_phase * 17u)) + peril / 2u + state->border / 3u);

    {
        Ens y;
        i_value = calc_i(&g_farmer);
        y.Wc = clamp_u8(96 + (int16_t)(seed0 & 0x5Fu) + support / 2u - peril / 4u - state->border / 5u);
        y.Cp = clamp_u8(34 + (int16_t)(seed1 & 0x4Fu) + peril / 3u + state->border / 3u + (int16_t)((i_value - 256u) >> 3u));
        y.Mh = clamp_u8(22 + (int16_t)(seed2 & 0x7Fu) + g_phase * 14u + peril / 2u + state->border / 2u);
        y.Br = clamp_u8(74 + (int16_t)((seed0 >> 3u) & 0x6Fu) + state->border / 4u + ((tile_x < (g_start_tile_x + 36u)) ? 24 : 0));
        y.Ep = clamp_u8(18 + (int16_t)((seed4 >> 2u) & 0x5Fu) + peril / 2u + state->border / 4u);
        y.Cl = clamp_u8(84 + (int16_t)((seed1 >> 1u) & 0x4Fu) + support / 2u + nearby_plots + built * 6u - g_phase * 3u - state->border / 4u);

        x_value = calc_x(&g_farmer);
        calc_geography(&y, state->delta, &state->geo);
        state->irv = calc_irv(&y, x_value);
        calc_objects(&state->geo, &y, state->irv, state->delta, &state->objects);
        calc_race(&y, state->geo.t, &state->race);
        state->dom = calc_dominion(&state->geo, &y, state->race.Gw, state->geo.t);
        calc_rest(&state->geo, state->dom, &rest);
        state->rest_h = rest.h;
        state->rest_c = rest.c;
        state->rest_t = rest.t;
        calc_tiers(&y, &state->geo, state->race.Gw, &state->tiers);
        calc_hyper3(&state->geo, &y, state->dom, state->race.Gw, state->rest_t, state->race.Psi, &state->hyper);
        h_obs = calc_hyperself(&g_farmer, &state->hyper);
        calc_bands(&g_farmer, &y, state->race.Psi, h_obs, &state->bands);
        state->tension = calc_tension(&g_farmer, &y);
        state->phi = calc_phi(&state->bands, state->tension);
        state->floor = calc_coh_floor(&g_farmer);
        state->coherence_state = calc_coh_state(state->phi, state->floor, &state->bands);
        state->r3 = relative3_scalar(y.Wc, state->floor, clamp_u8(g_grain * 32u), clamp_u8(peril * 2u + state->border), state->race.Gw);
    }
}

uint8_t shrine_tile_at(uint16_t tile_x, uint16_t tile_y) {
    return (tile_x == g_shrine_tile_x && tile_y == g_shrine_tile_y) ? 1u : 0u;
}

uint8_t plot_tile_at(uint16_t tile_x, uint16_t tile_y) {
    uint8_t index;
    for (index = 0u; index < MAX_PLOTS; ++index) {
        if (g_plots[index].active && g_plots[index].tile_x == tile_x && g_plots[index].tile_y == tile_y) {
            if (g_plots[index].stage == 1u) return TILE_SOIL;
            if (g_plots[index].stage == 2u) return TILE_CROP;
            return TILE_RIPE;
        }
    }
    return 255u;
}

uint8_t impact_tile_at(uint16_t tile_x, uint16_t tile_y) {
    uint8_t index;
    for (index = 0u; index < MAX_IMPACTS; ++index) {
        if (g_impacts[index].active && g_impacts[index].tile_x == tile_x && g_impacts[index].tile_y == tile_y) {
            return TILE_CRATER;
        }
    }
    return 255u;
}

uint8_t settlement_tile_at(uint16_t tile_x, uint16_t tile_y) {
    uint8_t index;
    index = find_settlement_at(tile_x, tile_y);
    if (index == 255u) return 255u;
    if (g_settlements[index].built) {
        if (g_settlements[index].feather_ready) return TILE_FEATHER;
        return TILE_HUT;
    }
    return TILE_SITE;
}

uint8_t world_tile_at(uint16_t tile_x, uint16_t tile_y) {
    uint16_t distance;
    uint16_t noise;
    uint8_t tile_value;
    FieldState state;

    if (tile_x >= WORLD_GRID_TILES || tile_y >= WORLD_GRID_TILES) return TILE_WATER;
    if (shrine_tile_at(tile_x, tile_y)) return TILE_SHRINE;

    tile_value = settlement_tile_at(tile_x, tile_y);
    if (tile_value != 255u) return tile_value;

    tile_value = plot_tile_at(tile_x, tile_y);
    if (tile_value != 255u) return tile_value;

    tile_value = impact_tile_at(tile_x, tile_y);
    if (tile_value != 255u) return tile_value;

    if (g_tutorial_overlay_enabled) {
        tile_value = tutorial_tile_override(tile_x, tile_y);
        if (tile_value != 255u) return tile_value;
    }

    distance = approx_disc_distance(tile_x, tile_y);
    noise = hash16(tile_x, tile_y, (uint16_t)(g_world_seed + 211u));
    if (distance >= DISC_HARD_RADIUS) {
        if (((noise >> 3u) & 0x03u) != 0u) return TILE_WATER;
        return TILE_ROCK;
    }
    if (distance >= DISC_BEACH_RADIUS) {
        if ((noise & 0xFFu) < 96u) return TILE_WATER;
        if (((noise >> 8u) & 0xFFu) > 208u) return TILE_CRATER;
        return TILE_SAND;
    }

    evaluate_field_state(tile_x, tile_y, &state);
    if (distance > DISC_SAFE_RADIUS && ((noise & 0xFFu) < state.border)) {
        if (((noise >> 8u) & 0x03u) == 0u) return TILE_SAND;
        return TILE_ROCK;
    }
    if (state.objects.Oo + state.border > 178u && ((noise >> 6u) & 0xFFu) > 156u) return TILE_ROCK;
    if (state.geo.h > 108u && ((noise >> 2u) & 0xFFu) > (uint8_t)(176u - (state.border >> 2u))) return TILE_TREE;
    if (state.geo.c > 92u && state.border < 176u && ((noise >> 4u) & 0xFFu) > 84u && ((noise >> 4u) & 0xFFu) < 168u) return TILE_SOIL;
    if (state.coherence_state >= 2u && ((noise >> 7u) & 0xFFu) > (uint8_t)(214u - (state.border >> 3u))) return TILE_CRATER;
    if (state.border > 150u && ((noise >> 5u) & 0xFFu) > 132u) return TILE_SAND;
    return TILE_GRASS;
}
