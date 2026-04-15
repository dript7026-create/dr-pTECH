#ifndef PORT_GAME_H
#define PORT_GAME_H

#include "port_gba.h"

#include <stdint.h>

#define PORT_MAX_PROJECTILES 8u
#define PORT_MAX_ENEMIES 10u

typedef struct PortProjectile {
    uint8_t active;
    int32_t x;
    int32_t y;
    int16_t vx;
    int16_t vy;
    uint8_t ttl;
} PortProjectile;

typedef struct PortEnemy {
    uint8_t active;
    int32_t x;
    int32_t y;
    int16_t vx;
    int16_t vy;
    uint8_t hp;
    uint8_t cooldown;
} PortEnemy;

typedef struct PortGameState {
    int32_t player_x;
    int32_t player_y;
    int16_t player_vx;
    int16_t player_vy;
    int32_t camera_x;
    int32_t camera_y;
    uint16_t frame;
    uint16_t spawn_timer;
    uint8_t weapon_rank;
    uint8_t armor_rank;
    uint8_t pressure;
    uint8_t dash_cooldown;
    uint8_t fire_cooldown;
    uint8_t exit_requested;
    uint8_t move_flash;
    int8_t aim_x;
    int8_t aim_y;
    PortProjectile projectiles[PORT_MAX_PROJECTILES];
    PortEnemy enemies[PORT_MAX_ENEMIES];
} PortGameState;

void port_game_init(PortGameState *state);
void port_game_update(PortGameState *state, const PortInputState *input);
void port_game_render(const PortGameState *state, volatile uint16_t *buffer);

#endif