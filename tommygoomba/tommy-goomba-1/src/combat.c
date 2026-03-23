void combat_init();
void combat_update();
void combat_handle_input();
void combat_end();

typedef struct {
    int health;
    int attack_power;
    int defense;
} Actor;

typedef struct {
    Actor player;
    Actor enemy;
    int is_combat_active;
} CombatState;

CombatState combat_state;

void combat_init() {
    combat_state.player.health = 100;
    combat_state.player.attack_power = 20;
    combat_state.player.defense = 5;

    combat_state.enemy.health = 50;
    combat_state.enemy.attack_power = 15;
    combat_state.enemy.defense = 3;

    combat_state.is_combat_active = 1;
}

void combat_update() {
    if (combat_state.is_combat_active) {
        // Update combat logic here
        // Check for win/loss conditions
        if (combat_state.player.health <= 0) {
            combat_end();
        } else if (combat_state.enemy.health <= 0) {
            combat_end();
        }
    }
}

void combat_handle_input() {
    // Handle player input for combat actions (attack, defend, etc.)
    // Example: if player chooses to attack
    combat_state.enemy.health -= (combat_state.player.attack_power - combat_state.enemy.defense);
    combat_state.player.health -= (combat_state.enemy.attack_power - combat_state.player.defense);
}

void combat_end() {
    combat_state.is_combat_active = 0;
    // Transition back to the main game state or handle victory/defeat
}