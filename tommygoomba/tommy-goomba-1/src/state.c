void init_game_state();
void update_game_state();
void transition_to_intro();
void transition_to_gameplay();
void transition_to_combat();
void transition_to_ending();

typedef enum {
    STATE_INTRO,
    STATE_GAMEPLAY,
    STATE_COMBAT,
    STATE_ENDING
} GameState;

GameState current_state;

void init_game_state() {
    current_state = STATE_INTRO;
}

void update_game_state() {
    switch (current_state) {
        case STATE_INTRO:
            // Logic for intro state
            break;
        case STATE_GAMEPLAY:
            // Logic for gameplay state
            break;
        case STATE_COMBAT:
            // Logic for combat state
            break;
        case STATE_ENDING:
            // Logic for ending state
            break;
    }
}

void transition_to_intro() {
    current_state = STATE_INTRO;
}

void transition_to_gameplay() {
    current_state = STATE_GAMEPLAY;
}

void transition_to_combat() {
    current_state = STATE_COMBAT;
}

void transition_to_ending() {
    current_state = STATE_ENDING;
}