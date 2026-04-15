#pragma once

#include <stdint.h>
#include "game_types.h"

void evaluate_field_state(uint16_t tile_x, uint16_t tile_y, FieldState *state);
uint8_t shrine_tile_at(uint16_t tile_x, uint16_t tile_y);
uint8_t plot_tile_at(uint16_t tile_x, uint16_t tile_y);
uint8_t impact_tile_at(uint16_t tile_x, uint16_t tile_y);
uint8_t settlement_tile_at(uint16_t tile_x, uint16_t tile_y);
uint8_t world_tile_at(uint16_t tile_x, uint16_t tile_y);
