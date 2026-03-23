#ifndef STAGES_H
#define STAGES_H

// Function prototypes for stage management
void load_stage(int stage_number);
void unload_stage(int stage_number);
void update_stage(int stage_number);
void render_stage(int stage_number);

// Structure to define a stage
typedef struct {
    int stage_number;
    const char* stage_name;
    const char* stage_data; // Pointer to stage-specific data (e.g., layout, enemies)
    int enemy_count; // Number of enemies in the stage
    int boss_present; // Flag to indicate if a boss is present in the stage
} Stage;

// Array of stages
extern Stage stages[];

#endif // STAGES_H