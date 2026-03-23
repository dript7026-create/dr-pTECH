#include <gb/gb.h>
#include <gb/drawing.h>
#include <gb/font.h>
#include "sprites.h"

// Define sprite IDs
#define TOMMY_SPRITE 0
#define WIFE_SPRITE 1
#define BROTHER1_SPRITE 2
#define BROTHER2_SPRITE 3
#define COUSIN_SPRITE 4

// Sprite data for Tommy, his wife, brothers, and cousins
const UINT8 tommy_sprite[] = {
    // Define sprite data for Tommy
};

const UINT8 wife_sprite[] = {
    // Define sprite data for Tommy's wife
};

const UINT8 brother1_sprite[] = {
    // Define sprite data for Brother 1
};

const UINT8 brother2_sprite[] = {
    // Define sprite data for Brother 2
};

const UINT8 cousin_sprite[] = {
    // Define sprite data for Cousin
};

// Function to load sprites into VRAM
void load_sprites() {
    set_sprite_data(0, 5, tommy_sprite);
    set_sprite_data(1, 5, wife_sprite);
    set_sprite_data(2, 5, brother1_sprite);
    set_sprite_data(3, 5, brother2_sprite);
    set_sprite_data(4, 5, cousin_sprite);
}

// Function to initialize sprites
void init_sprites() {
    load_sprites();
    // Set initial positions for sprites
    move_sprite(TOMMY_SPRITE, 88, 78); // Example position for Tommy
    move_sprite(WIFE_SPRITE, 80, 78); // Example position for Wife
    move_sprite(BROTHER1_SPRITE, 100, 78); // Example position for Brother 1
    move_sprite(BROTHER2_SPRITE, 120, 78); // Example position for Brother 2
    move_sprite(COUSIN_SPRITE, 140, 78); // Example position for Cousin
}

// Function to update sprite positions
void update_sprites() {
    // Logic to update sprite positions based on game state
}

// Function to hide all sprites
void hide_sprites() {
    for (UINT8 i = 0; i < 5; i++) {
        move_sprite(i, 0, 0); // Move sprite off-screen
    }
}