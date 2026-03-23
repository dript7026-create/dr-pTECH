#ifndef WORLD_MAP_H
#define WORLD_MAP_H

#include <gb/gb.h>
#include <gb/drawing.h>
#include "stages.h"

// Function to initialize the world map
void init_world_map();

// Function to update the world map state
void update_world_map();

// Function to draw the world map
void draw_world_map();

// Function to transition to a specific stage
void enter_stage(uint8_t stage_id);

// Function to check if the player has reached a stage
uint8_t check_stage_reached(uint8_t stage_id);

// Function to handle interactions on the world map
void handle_world_map_interactions();

#endif // WORLD_MAP_H