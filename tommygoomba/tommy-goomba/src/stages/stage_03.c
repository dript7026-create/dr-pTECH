#include "stages.h"

void load_stage_03() {
    // Initialize stage 03 specific variables
    int player_x = 10; // Starting X position of Tommy
    int player_y = 10; // Starting Y position of Tommy
    int enemies_defeated = 0; // Count of defeated enemies in this stage

    // Load the stage layout
    load_stage_map(3); // Function to load the map for stage 03

    // Set up enemies for this stage
    setup_enemies_for_stage(3);

    // Main loop for stage 03
    while (is_stage_active(3)) {
        // Handle player input
        handle_player_input(&player_x, &player_y);

        // Update enemy positions and behaviors
        update_enemies();

        // Check for collisions with enemies
        if (check_collision_with_enemies(player_x, player_y)) {
            // Handle combat if collision occurs
            initiate_combat();
        }

        // Check for stage completion conditions
        if (check_stage_completion(player_x, player_y)) {
            // Transition to the next stage or end the game
            transition_to_next_stage();
            break;
        }

        // Render the stage
        render_stage(player_x, player_y);
    }

    // Cleanup after exiting the stage
    cleanup_stage(3);
}