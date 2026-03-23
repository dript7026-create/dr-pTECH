#ifndef SAVE_SYSTEM_H
#define SAVE_SYSTEM_H

#include <gb/gb.h>
#include <gb/drawing.h>

// Structure to hold player save data
typedef struct {
    UINT8 player_health;
    UINT8 player_position_x;
    UINT8 player_position_y;
    UINT8 stage_id;
    UINT8 brothers_defeated; // Bitmask for defeated brothers
    UINT8 cousins_encountered; // Bitmask for encountered cousins
} SaveData;

// Function to initialize save system
void init_save_system();

// Function to save game progress
void save_game(SaveData *data);

// Function to load game progress
void load_game(SaveData *data);

// Function to check if a save file exists
UINT8 save_file_exists();

// Function to delete the save file
void delete_save_file();

#endif // SAVE_SYSTEM_H