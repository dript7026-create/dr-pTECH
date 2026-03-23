#include "stage_manager.h"
#include "game.h"
#include "world_map.h"
#include "stages.h"

#define TOTAL_STAGES 66

typedef struct {
    int current_stage;
    void (*load_stage)(int stage);
    void (*unload_stage)(int stage);
} StageManager;

StageManager stage_manager;

void load_stage(int stage) {
    if (stage < 1 || stage > TOTAL_STAGES) {
        return; // Invalid stage
    }
    
    // Unload the current stage if necessary
    if (stage_manager.current_stage != 0) {
        stage_manager.unload_stage(stage_manager.current_stage);
    }

    // Load the new stage
    stage_manager.current_stage = stage;
    switch (stage) {
        case 1:
            stage_01_load();
            break;
        case 2:
            stage_02_load();
            break;
        case 3:
            stage_03_load();
            break;
        // Add cases for all stages up to 66
        case 66:
            stage_66_load();
            break;
        default:
            break;
    }
}

void unload_stage(int stage) {
    // Logic to unload the stage resources
    switch (stage) {
        case 1:
            stage_01_unload();
            break;
        case 2:
            stage_02_unload();
            break;
        case 3:
            stage_03_unload();
            break;
        // Add cases for all stages up to 66
        case 66:
            stage_66_unload();
            break;
        default:
            break;
    }
}

void initialize_stage_manager() {
    stage_manager.current_stage = 0;
    stage_manager.load_stage = load_stage;
    stage_manager.unload_stage = unload_stage;
}