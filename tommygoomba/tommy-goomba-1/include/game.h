#ifndef GAME_H
#define GAME_H

#include <gb/gb.h>
#include <gb/drawing.h>
#include <stdint.h>

// Game States
typedef enum {
    STATE_INTRO,
    STATE_GAMEPLAY,
    STATE_COMBAT,
    STATE_ENDING
} GameState;

// Player structure
typedef struct {
    uint8_t x;
    uint8_t y;
    uint8_t health;
    uint8_t speed;
    uint8_t charge_speed;
} Player;

// Function declarations
void init_game();
void update_game();
void draw_game();
void change_state(GameState new_state);
void handle_input();
void reset_game();

#endif // GAME_H