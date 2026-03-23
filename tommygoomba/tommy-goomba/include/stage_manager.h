#ifndef STAGE_MANAGER_H
#define STAGE_MANAGER_H

#include "game.h"
#include "stages.h"

// Function to load a specific stage
void load_stage(int stage_number);

// Function to unload the current stage
void unload_stage(void);

// Function to update stage-specific events
void update_stage_events(void);

// Function to check for player interactions within the stage
void check_stage_interactions(Player *player);

// Function to reset the stage to its initial state
void reset_stage(void);

#endif // STAGE_MANAGER_H