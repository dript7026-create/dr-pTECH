#ifndef STATE_H
#define STATE_H

// Enumeration for different game states
typedef enum {
    STATE_INTRO,
    STATE_GAMEPLAY,
    STATE_COMBAT,
    STATE_ENDING,
    STATE_SAVE,
    STATE_LOAD,
    STATE_EXIT
} GameState;

// Function prototypes for state management
void initState();
void updateState();
void changeState(GameState newState);
GameState getCurrentState();

#endif // STATE_H