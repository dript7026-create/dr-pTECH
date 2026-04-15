#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// Enum definitions
typedef enum {
    GAOLITE,
    JEURGREN,
    FALLOWS
} CreatureType;

typedef enum {
    JOOLS,
    GAORG
} HabitatType;

typedef enum {
    BASE,
    STAGE1,
    STAGE2
} EvolutionStage;

// Statistics structure
typedef struct {
    uint8_t degree;
    uint8_t angle;
    uint8_t cut;
    uint8_t range;
    uint8_t flow;
    uint8_t arc;
    uint8_t gauge;
} Statistics;

// Card structure
typedef struct {
    uint16_t card_id;
    CreatureType creature_type;
    HabitatType habitat_type;
    EvolutionStage evolution;
    Statistics stats;
    uint16_t hitpoints;
    uint8_t is_coupled;
    char name[32];
} Card;

// Deck structure
typedef struct {
    Card cards[52];
    uint8_t card_count;
} Deck;

// Player structure
typedef struct {
    Card hand[3];
    Card roster[36];
    uint8_t hand_size;
    uint8_t roster_size;
    uint16_t patience;
    uint16_t aggression;
} Player;

// Battle state structure
typedef struct {
    Player players[2];
    Card attacking_card;
    Card defending_card;
    uint8_t active_player;
    uint16_t total_damage;
} BattleState;

// Function declarations
void initialize_deck(Deck *deck, uint8_t deck_number);
void shuffle_deck(Deck *deck);
Card* draw_card(Deck *deck);
uint8_t roll_die(uint8_t sides);
float calculate_hit_probability(Statistics attacker, Statistics defender, uint8_t aggression_roll, uint8_t speed_roll);
uint16_t calculate_damage(float hit_probability, uint8_t total_calculations);
void initialize_player(Player *player);

#endif