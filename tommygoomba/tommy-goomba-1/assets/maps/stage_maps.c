#include "stages.h"

// Define the layout for each stage in the game
const StageMap stage_maps[66] = {
    // Stage 1
    {
        .layout = {
            // Define the tile layout for stage 1
            // Example: 0 = empty, 1 = solid ground, 2 = enemy, etc.
            1, 1, 1, 1, 1, 1, 1, 1,
            1, 0, 0, 2, 0, 0, 0, 1,
            1, 0, 1, 1, 1, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 1,
            1, 1, 1, 1, 1, 1, 1, 1,
        },
        .enemy_count = 1,
        .enemies = { { .type = ENEMY_TYPE_1, .x = 3, .y = 1 } }
    },
    // Stage 2
    {
        .layout = {
            // Define the tile layout for stage 2
            1, 1, 1, 1, 1, 1, 1, 1,
            1, 0, 0, 1, 0, 0, 0, 1,
            1, 0, 2, 0, 1, 0, 0, 1,
            1, 0, 0, 0, 0, 0, 0, 1,
            1, 1, 1, 1, 1, 1, 1, 1,
        },
        .enemy_count = 2,
        .enemies = { { .type = ENEMY_TYPE_2, .x = 2, .y = 1 }, { .type = ENEMY_TYPE_1, .x = 4, .y = 1 } }
    },
    // Continue defining stages up to stage 66...
    // Stage 3 to Stage 66 would follow a similar structure
};