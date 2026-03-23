#include "stages.h"

void load_stage_01() {
    // Initialize stage variables
    int player_x = 10;
    int player_y = 10;
    int enemies_defeated = 0;
    int total_enemies = 5;

    // Load the stage layout
    load_stage_layout(1);

    // Main stage loop
    while (1) {
        // Check for player input
        handle_player_input(&player_x, &player_y);

        // Update enemy positions and check for collisions
        update_enemies(player_x, player_y, &enemies_defeated);

        // Check for victory conditions
        if (enemies_defeated >= total_enemies) {
            break; // Exit stage if all enemies are defeated
        }

        // Render the stage
        render_stage(player_x, player_y);
    }

    // Transition to the next stage or return to the world map
    transition_to_next_stage();
}