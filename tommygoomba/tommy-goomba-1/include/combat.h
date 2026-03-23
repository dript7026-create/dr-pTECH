#ifndef COMBAT_H
#define COMBAT_H

// Function to initiate combat with an enemy
void initiate_combat(int enemy_id);

// Function to handle player attacks
void player_attack(int attack_type);

// Function to handle enemy attacks
void enemy_attack(int enemy_id);

// Function to calculate damage dealt
int calculate_damage(int attack_power, int defense);

// Function to check if the player or enemy is defeated
int check_defeat(int health);

// Function to manage combat flow
void manage_combat(int enemy_id);

// Function to display combat results
void display_combat_results(int player_health, int enemy_health);

#endif // COMBAT_H