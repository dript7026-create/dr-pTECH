#ifndef ACTORS_H
#define ACTORS_H

// Define constants for actor types
#define ACTOR_TYPE_PLAYER 0
#define ACTOR_TYPE_NPC 1
#define ACTOR_TYPE_ENEMY 2

// Structure to represent an actor in the game
typedef struct {
    int id;                // Unique identifier for the actor
    int type;              // Type of actor (player, NPC, enemy)
    int x;                 // X position on the screen
    int y;                 // Y position on the screen
    int health;            // Health points of the actor
    int attack;            // Attack power of the actor
    int defense;           // Defense power of the actor
    void (*update)(struct Actor*); // Pointer to function for updating actor state
} Actor;

// Function prototypes
void init_actor(Actor* actor, int id, int type, int x, int y, int health, int attack, int defense);
void update_actor(Actor* actor);
void draw_actor(Actor* actor);
void handle_actor_interaction(Actor* actor1, Actor* actor2);

#endif // ACTORS_H