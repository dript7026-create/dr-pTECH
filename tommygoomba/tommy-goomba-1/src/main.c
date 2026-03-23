#include <gb/gb.h>
#include <stdio.h>
#include "game.h"
#include "state.h"
#include "player.h"
#include "actors.h"
#include "combat.h"
#include "world_map.h"
#include "stage_manager.h"
#include "save_system.h"
#include "intro_scene.h"
#include "ending_scene.h"

void main() {
    // Initialize the Game Boy environment
    gb_init();
    
    // Load the intro scene
    load_intro_scene();

    // Main game loop
    while (1) {
        // Update game state
        update_game_state();

        // Handle user input
        handle_input();

        // Update game components
        update_game_components();

        // Check for state transitions
        check_state_transitions();

        // Wait for the next frame
        wait_vbl_done();
    }
}