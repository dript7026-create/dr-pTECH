#include "actors.h"
#include "game.h"
#include "combat.h"
#include "player.h"

// Define the structure for NPCs and enemies
typedef struct {
    int id;
    int x, y; // Position on the map
    int health;
    int isAlive;
    int type; // 0 for NPC, 1 for enemy
} Actor;

// Array to hold all actors in the game
#define MAX_ACTORS 100
Actor actors[MAX_ACTORS];
int actorCount = 0;

// Function to initialize an actor
void initActor(int id, int x, int y, int health, int type) {
    if (actorCount < MAX_ACTORS) {
        actors[actorCount].id = id;
        actors[actorCount].x = x;
        actors[actorCount].y = y;
        actors[actorCount].health = health;
        actors[actorCount].isAlive = 1;
        actors[actorCount].type = type;
        actorCount++;
    }
}

// Function to update actors' positions and behaviors
void updateActors() {
    for (int i = 0; i < actorCount; i++) {
        if (actors[i].isAlive) {
            // Update logic for each actor
            // For example, simple movement or AI behavior can be implemented here
        }
    }
}

// Function to handle combat with an enemy
void handleCombat(int actorId) {
    for (int i = 0; i < actorCount; i++) {
        if (actors[i].id == actorId && actors[i].isAlive && actors[i].type == 1) {
            // Implement combat logic here
            // For example, reduce health, check for death, etc.
            actors[i].health -= 10; // Example damage
            if (actors[i].health <= 0) {
                actors[i].isAlive = 0; // Mark as dead
            }
            break;
        }
    }
}

// Function to check for interactions with the player
void checkInteractions(Player *player) {
    for (int i = 0; i < actorCount; i++) {
        if (actors[i].isAlive && actors[i].x == player->x && actors[i].y == player->y) {
            // Trigger interaction based on actor type
            if (actors[i].type == 0) {
                // Interact with NPC
            } else if (actors[i].type == 1) {
                // Engage in combat
                handleCombat(actors[i].id);
            }
        }
    }
}