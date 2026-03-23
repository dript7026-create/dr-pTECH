#include "player.h"

typedef struct {
    int x;
    int y;
    int health;
    int speed;
    int charge_speed;
    int is_alive;
} Player;

Player tommy;

void init_player() {
    tommy.x = 0;
    tommy.y = 0;
    tommy.health = 100;
    tommy.speed = 2;
    tommy.charge_speed = 5;
    tommy.is_alive = 1;
}

void move_player(int dx, int dy) {
    if (tommy.is_alive) {
        tommy.x += dx * tommy.speed;
        tommy.y += dy * tommy.speed;
    }
}

void charge_player() {
    if (tommy.is_alive) {
        tommy.x += tommy.charge_speed;
    }
}

void take_damage(int damage) {
    if (tommy.is_alive) {
        tommy.health -= damage;
        if (tommy.health <= 0) {
            tommy.is_alive = 0;
        }
    }
}

int is_player_alive() {
    return tommy.is_alive;
}

int get_player_health() {
    return tommy.health;
}

int get_player_position_x() {
    return tommy.x;
}

int get_player_position_y() {
    return tommy.y;
}