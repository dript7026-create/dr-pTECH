#ifndef PLAYER_H
#define PLAYER_H

#include <gb/gb.h>
#include <gb/drawing.h>
#include "actors.h"

// Player structure definition
typedef struct {
    UINT8 x;          // Player's x position
    UINT8 y;          // Player's y position
    UINT8 health;     // Player's health
    UINT8 speed;      // Player's movement speed
    UINT8 charge;     // Player's charge ability status
    UINT8 state;      // Current state of the player (e.g., normal, charging)
} Player;

// Function declarations
void init_player(Player* player);
void update_player(Player* player);
void move_player(Player* player, UINT8 direction);
void player_attack(Player* player, Actor* target);
void player_charge(Player* player);
void player_reset(Player* player);

#endif // PLAYER_H