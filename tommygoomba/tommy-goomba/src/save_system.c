#include "save_system.h"
#include <gb/gb.h>
#include <gb/drawing.h>
#include <stdio.h>

#define SAVE_FILE_SIZE 128

typedef struct {
    uint8_t player_health;
    uint8_t player_stage;
    uint8_t brothers_defeated[2]; // Track which brothers have been defeated
    uint8_t wife_found; // 1 if wife is found, 0 otherwise
} SaveData;

SaveData current_save;

void save_game() {
    FILE *file = fopen("save.dat", "wb");
    if (file) {
        fwrite(&current_save, sizeof(SaveData), 1, file);
        fclose(file);
    }
}

void load_game() {
    FILE *file = fopen("save.dat", "rb");
    if (file) {
        fread(&current_save, sizeof(SaveData), 1, file);
        fclose(file);
    } else {
        // Initialize default save data if no save file exists
        current_save.player_health = 3; // Example starting health
        current_save.player_stage = 1; // Start at stage 1
        current_save.brothers_defeated[0] = 0; // None defeated
        current_save.brothers_defeated[1] = 0; // None defeated
        current_save.wife_found = 0; // Wife not found
    }
}

void reset_save() {
    current_save.player_health = 3;
    current_save.player_stage = 1;
    current_save.brothers_defeated[0] = 0;
    current_save.brothers_defeated[1] = 0;
    current_save.wife_found = 0;
}