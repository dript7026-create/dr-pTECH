#include "game.h"
#include "state.h"
#include "player.h"
#include "actors.h"
#include "combat.h"
#include "world_map.h"
#include "stage_manager.h"
#include "save_system.h"

void initialize_game() {
    // Initialize game components
    initialize_player();
    initialize_actors();
    initialize_world_map();
    initialize_stage_manager();
    initialize_save_system();
    initialize_state_manager();
}

void update_game() {
    // Handle user input
    handle_input();

    // Update game state
    update_player();
    update_actors();
    update_combat();
    update_world_map();
    update_stage_manager();
}

void game_loop() {
    while (1) {
        update_game();
        // Render game graphics here
        wait_vbl_done(); // Wait for vertical blanking interval
    }
}

void start_game() {
    initialize_game();
    game_loop();
}