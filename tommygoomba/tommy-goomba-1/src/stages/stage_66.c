#include "stages.h"

void load_stage_66() {
    // Initialize stage 66 specific variables
    int player_x = 10; // Starting X position
    int player_y = 10; // Starting Y position
    int enemies_remaining = 5; // Number of enemies in this stage
    int stage_completed = 0; // Flag to check if the stage is completed

    // Load the stage layout and assets
    load_stage_assets(66);
    
    // Main loop for stage 66
    while (!stage_completed) {
        // Handle player input
        handle_player_input(&player_x, &player_y);

        // Update enemy positions and check for interactions
        update_enemies(player_x, player_y, &enemies_remaining);

        // Check for stage completion conditions
        if (enemies_remaining <= 0) {
            stage_completed = 1; // Mark stage as completed
        }

        // Render the stage
        render_stage(player_x, player_y, enemies_remaining);
    }

    // Transition to the next stage or ending
    transition_to_next_stage();
}