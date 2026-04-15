#include <gba.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "audio.h"
#include "game_types.h"
#include "password.h"
#include "generated/gorge_content.h"

#define iprintf printf

typedef enum ScreenState {
    SCREEN_TITLE = 0,
    SCREEN_STARTER = 1,
    SCREEN_WORLD = 2,
    SCREEN_BATTLE = 3,
    SCREEN_REWARD = 4,
    SCREEN_PASSWORD = 5
} ScreenState;

typedef struct BattleCreature {
    int card_index;
    int current_hp;
    int patience;
    int aggression;
    int stability;
    int coupling;
    int vulnerable_turns;
    int habitat_card_index;
    int status;
    int alive;
} BattleCreature;

typedef struct BattleSide {
    int deck_id;
    int draw_order_total;
    int deck_cards[GORGE_CARDS_PER_DECK];
    int habitat_cards[GORGE_MAX_HAND];
    int habitat_count;
    BattleCreature roster[GORGE_ROSTER_SIZE];
    int active_index;
} BattleSide;

typedef struct BattleState {
    BattleSide player;
    BattleSide enemy;
    int opponent_deck;
    int turn_number;
    int player_action_cursor;
    int player_branch_choice;
    int init_roll_player[3];
    int init_roll_enemy[3];
    int over;
    int player_won;
    char log_a[64];
    char log_b[64];
} BattleState;

typedef struct CampaignState {
    uint32_t cleared_mask;
    uint32_t reward_mask;
    uint8_t starter_deck;
    uint8_t active;
    uint8_t selection;
    uint8_t password_index;
    int reward_preview[3];
    int reward_source_deck;
    char password_buf[GORGE_PASSWORD_LEN + 1];
} CampaignState;

static ScreenState g_screen = SCREEN_TITLE;
static CampaignState g_campaign = {0};
static BattleState g_battle = {0};
static uint32_t g_rng_state = 0xC0FFEE11u;

static const char *k_action_labels[GORGE_ACTION_COUNT] = {
    "Aggress",
    "Patience",
    "Habitat",
    "Couple",
    "Evolve",
    "Swap"
};

static int clampi(int value, int minimum, int maximum) {
    if (value < minimum) return minimum;
    if (value > maximum) return maximum;
    return value;
}

static int first_uncleared_opponent(void) {
    int deck_id;
    for (deck_id = 0; deck_id < GORGE_DECK_COUNT; ++deck_id) {
        if (deck_id == (int)g_campaign.starter_deck) {
            continue;
        }
        if ((g_campaign.cleared_mask & (1u << deck_id)) == 0u) {
            return deck_id;
        }
    }
    return -1;
}

static uint32_t campaign_payload(void) {
    return (g_campaign.reward_mask & 0x0FFFFFFFu) | ((uint32_t)g_campaign.starter_deck << 28);
}

static void campaign_password_refresh(void) {
    gorge_password_encode(g_campaign.password_buf, sizeof(g_campaign.password_buf), g_campaign.cleared_mask, campaign_payload());
}

static void campaign_apply_password(uint32_t cleared_mask, uint32_t payload) {
    g_campaign.cleared_mask = cleared_mask;
    g_campaign.reward_mask = payload & 0x0FFFFFFFu;
    g_campaign.starter_deck = (payload >> 28) & 0x0Fu;
    if (g_campaign.starter_deck >= GORGE_DECK_COUNT) {
        g_campaign.starter_deck = 0;
    }
    g_campaign.active = 1;
    g_campaign.selection = (uint8_t)(first_uncleared_opponent() >= 0 ? first_uncleared_opponent() : 0);
    campaign_password_refresh();
}

static void campaign_begin(uint8_t starter_deck) {
    memset(&g_campaign, 0, sizeof(g_campaign));
    g_campaign.active = 1;
    g_campaign.starter_deck = starter_deck;
    g_campaign.cleared_mask = (1u << starter_deck);
    g_campaign.selection = (uint8_t)(first_uncleared_opponent() >= 0 ? first_uncleared_opponent() : 0);
    campaign_password_refresh();
}

static uint32_t rng_next(void) {
    g_rng_state = g_rng_state * 1664525u + 1013904223u;
    return g_rng_state;
}

static int rng_roll(int sides) {
    return (int)(rng_next() % (uint32_t)sides) + 1;
}

static const GorgeCardDef *card_def(int card_index_value) {
    if (card_index_value < 0) {
        return &g_gorge_cards[0];
    }
    return &g_gorge_cards[card_index_value];
}

static void short_name(const char *source, char *dest, int dest_size) {
    int index = 0;
    if (!dest || dest_size <= 0) {
        return;
    }
    while (source && source[index] && index < dest_size - 1) {
        dest[index] = source[index];
        ++index;
    }
    dest[index] = '\0';
}

static void battle_log(const char *primary, const char *secondary) {
    snprintf(g_battle.log_b, sizeof(g_battle.log_b), "%s", secondary ? secondary : "");
    snprintf(g_battle.log_a, sizeof(g_battle.log_a), "%s", primary ? primary : "");
}

static void screen_clear(void) {
    printf("\x1b[2J");
    printf("\x1b[0;0H");
}

static int family_advantage(int attacker, int defender) {
    if ((attacker == GORGE_FAMILY_GAOLITE && defender == GORGE_FAMILY_JEURGREN) ||
        (attacker == GORGE_FAMILY_JEURGREN && defender == GORGE_FAMILY_FALLOWS) ||
        (attacker == GORGE_FAMILY_FALLOWS && defender == GORGE_FAMILY_GAOLITE)) {
        return 1;
    }
    if ((defender == GORGE_FAMILY_GAOLITE && attacker == GORGE_FAMILY_JEURGREN) ||
        (defender == GORGE_FAMILY_JEURGREN && attacker == GORGE_FAMILY_FALLOWS) ||
        (defender == GORGE_FAMILY_FALLOWS && attacker == GORGE_FAMILY_GAOLITE)) {
        return -1;
    }
    return 0;
}

static int next_living_index(const BattleSide *side, int current) {
    int offset;
    for (offset = 1; offset <= GORGE_ROSTER_SIZE; ++offset) {
        int candidate = (current + offset) % GORGE_ROSTER_SIZE;
        if (side->roster[candidate].alive) {
            return candidate;
        }
    }
    return current;
}

static int alive_count(const BattleSide *side) {
    int count = 0;
    int index;
    for (index = 0; index < GORGE_ROSTER_SIZE; ++index) {
        if (side->roster[index].alive) {
            ++count;
        }
    }
    return count;
}

static BattleCreature *active_creature(BattleSide *side) {
    return &side->roster[side->active_index];
}

static void init_creature(BattleCreature *creature, int card_index_value) {
    const GorgeCardDef *card = card_def(card_index_value);
    creature->card_index = card_index_value;
    creature->current_hp = card->hit_points;
    creature->patience = card->patience_threshold;
    creature->aggression = 0;
    creature->stability = 2;
    creature->coupling = 0;
    creature->vulnerable_turns = 0;
    creature->habitat_card_index = -1;
    creature->status = 0;
    creature->alive = 1;
}

static void shuffle_cards(int *cards, int count) {
    int index;
    for (index = count - 1; index > 0; --index) {
        int swap_index = (int)(rng_next() % (uint32_t)(index + 1));
        int temp = cards[index];
        cards[index] = cards[swap_index];
        cards[swap_index] = temp;
    }
}

static void build_side_deck(BattleSide *side, int deck_id, int is_player) {
    int local_index;
    side->deck_id = deck_id;
    side->habitat_count = 0;
    side->active_index = 0;
    for (local_index = 0; local_index < GORGE_CARDS_PER_DECK; ++local_index) {
        side->deck_cards[local_index] = deck_id * GORGE_CARDS_PER_DECK + local_index;
    }
    if (is_player) {
        int replace_index = GORGE_CARDS_PER_DECK - 1;
        int reward_deck;
        for (reward_deck = 0; reward_deck < GORGE_DECK_COUNT; ++reward_deck) {
            int reward_slot;
            if ((g_campaign.reward_mask & (1u << reward_deck)) == 0u || reward_deck == deck_id) {
                continue;
            }
            for (reward_slot = 0; reward_slot < 3 && replace_index >= 40; ++reward_slot) {
                side->deck_cards[replace_index] = reward_deck * GORGE_CARDS_PER_DECK + g_gorge_decks[reward_deck].reward_cards[reward_slot];
                --replace_index;
            }
        }
    }
    shuffle_cards(side->deck_cards, GORGE_CARDS_PER_DECK);
}

static void draw_opening_roster(BattleSide *side) {
    int roster_index = 0;
    int draw_index;
    for (draw_index = 0; draw_index < GORGE_CARDS_PER_DECK && roster_index < GORGE_ROSTER_SIZE; ++draw_index) {
        const GorgeCardDef *card = card_def(side->deck_cards[draw_index]);
        if (card->card_kind == GORGE_CARD_CREATURE) {
            init_creature(&side->roster[roster_index], side->deck_cards[draw_index]);
            ++roster_index;
        } else if (side->habitat_count < GORGE_MAX_HAND) {
            side->habitat_cards[side->habitat_count++] = side->deck_cards[draw_index];
        }
    }
    while (roster_index < GORGE_ROSTER_SIZE) {
        init_creature(&side->roster[roster_index], side->deck_id * GORGE_CARDS_PER_DECK + roster_index);
        ++roster_index;
    }
}

static void battle_prepare(int opponent_deck) {
    int index;
    memset(&g_battle, 0, sizeof(g_battle));
    g_battle.opponent_deck = opponent_deck;
    g_battle.player_action_cursor = 0;
    g_battle.player_branch_choice = 0;
    g_battle.turn_number = 1;
    build_side_deck(&g_battle.player, g_campaign.starter_deck, 1);
    build_side_deck(&g_battle.enemy, opponent_deck, 0);
    draw_opening_roster(&g_battle.player);
    draw_opening_roster(&g_battle.enemy);
    for (index = 0; index < 3; ++index) {
        g_battle.init_roll_player[index] = rng_roll(9);
        g_battle.init_roll_enemy[index] = rng_roll(9);
        g_battle.player.draw_order_total += g_battle.init_roll_player[index];
        g_battle.enemy.draw_order_total += g_battle.init_roll_enemy[index];
    }
    gorge_audio_play_song(GORGE_SONG_BATTLE);
    battle_log("Spectral Reader engaged.", g_battle.player.draw_order_total >= g_battle.enemy.draw_order_total ? "You drew first." : "Rival drew first.");
}

static int habitat_home_match(const GorgeCardDef *creature, const GorgeCardDef *habitat) {
    return (creature->habitat_mask & habitat->habitat_mask) != 0u;
}

static void apply_upkeep(BattleCreature *creature) {
    const GorgeCardDef *card;
    if (!creature->alive) {
        return;
    }
    card = card_def(creature->card_index);
    if (creature->habitat_card_index >= 0) {
        const GorgeCardDef *habitat = card_def(creature->habitat_card_index);
        if (habitat_home_match(card, habitat)) {
            creature->stability = clampi(creature->stability + 1, 0, 7);
            creature->coupling = clampi(creature->coupling + 1, 0, 7);
        } else {
            creature->stability = clampi(creature->stability - 1, 0, 7);
        }
    }
    if (creature->vulnerable_turns > 0) {
        --creature->vulnerable_turns;
    }
    creature->patience = clampi(creature->patience, 0, card->patience_threshold);
    if (creature->current_hp <= 0) {
        creature->alive = 0;
    }
}

static int spectrum_damage(BattleCreature *attacker, BattleCreature *defender, int strong, char *detail, int detail_size) {
    const GorgeCardDef *atk = card_def(attacker->card_index);
    const GorgeCardDef *def = card_def(defender->card_index);
    int stats_a[7] = {atk->degree, atk->angle, atk->cut, atk->range, atk->flow, atk->arc, atk->gauge};
    int stats_b[7] = {def->degree, def->angle, def->cut, def->range, def->flow, def->arc, def->gauge};
    int d6 = rng_roll(6);
    int d9 = rng_roll(9);
    int advantage = family_advantage(atk->family, def->family);
    int aggression_gate = d6 + atk->power / 3 + attacker->aggression / 3 + strong + (advantage > 0 ? 1 : 0);
    int speed_gate = d9 + atk->speed / 2 + attacker->stability - defender->status - (advantage < 0 ? 1 : 0);
    int threshold;
    int sum = 0;
    int steps = 0;
    int i;
    int j;
    if (aggression_gate < 5 || speed_gate < 5) {
        snprintf(detail, detail_size, "d6 %d d9 %d miss", d6, d9);
        return 0;
    }
    threshold = clampi(18 + d6 * 6 + d9 * 5 + attacker->stability * 2 + attacker->coupling * 3 + strong * 12 + advantage * 8 - defender->stability * 2, 24, 100);
    for (i = 0; i < 7; ++i) {
        for (j = 0; j < 7; ++j) {
            int contribution = stats_a[i] + atk->power + attacker->coupling - stats_b[j] + 6 + advantage * 2;
            if (contribution < 1) {
                contribution = 1;
            }
            sum += contribution;
            ++steps;
            if (sum >= threshold) {
                int damage = clampi(steps / 2 + strong + (advantage > 0 ? 1 : 0), 1, 14);
                snprintf(detail, detail_size, "d6 %d d9 %d hit %d", d6, d9, damage);
                return damage;
            }
        }
    }
    snprintf(detail, detail_size, "d6 %d d9 %d glance", d6, d9);
    return 0;
}

static void perform_attack(BattleCreature *attacker, BattleCreature *defender, int strong, const char *attacker_name, const char *defender_name) {
    char detail[32];
    int damage;
    if (!defender->alive) {
        return;
    }
    if (defender->vulnerable_turns <= 0) {
        snprintf(g_battle.log_a, sizeof(g_battle.log_a), "%s needs a break.", defender_name);
        snprintf(g_battle.log_b, sizeof(g_battle.log_b), "%s is not vulnerable.", defender_name);
        gorge_audio_play_sfx(GORGE_SFX_MISS);
        return;
    }
    damage = spectrum_damage(attacker, defender, strong, detail, sizeof(detail));
    if (damage <= 0) {
        snprintf(g_battle.log_a, sizeof(g_battle.log_a), "%s missed %s.", attacker_name, defender_name);
        snprintf(g_battle.log_b, sizeof(g_battle.log_b), "%s", detail);
        gorge_audio_play_sfx(GORGE_SFX_MISS);
        return;
    }
    defender->current_hp -= damage;
    defender->aggression = 0;
    defender->vulnerable_turns = 0;
    if (defender->current_hp <= 0) {
        defender->alive = 0;
        defender->current_hp = 0;
    }
    snprintf(g_battle.log_a, sizeof(g_battle.log_a), "%s struck %s.", attacker_name, defender_name);
    snprintf(g_battle.log_b, sizeof(g_battle.log_b), "%s", detail);
    gorge_audio_play_sfx(GORGE_SFX_HIT);
}

static void action_aggress(BattleSide *actor_side, BattleSide *target_side, int strong) {
    BattleCreature *actor = active_creature(actor_side);
    BattleCreature *target = active_creature(target_side);
    const GorgeCardDef *card = card_def(actor->card_index);
    const GorgeCardDef *target_card = card_def(target->card_index);
    char actor_name[20];
    char target_name[20];
    short_name(card->name, actor_name, sizeof(actor_name));
    short_name(target_card->name, target_name, sizeof(target_name));
    actor->aggression += 3 + rng_roll(6) / 2 + (strong ? 2 : 0);
    target->patience -= 2 + card->power / 3 + (strong ? 2 : 0);
    if (target->patience <= 0) {
        target->patience = 0;
        target->vulnerable_turns = 2;
    }
    perform_attack(actor, target, strong, actor_name, target_name);
}

static void action_patience(BattleSide *side) {
    BattleCreature *actor = active_creature(side);
    const GorgeCardDef *card = card_def(actor->card_index);
    actor->patience = clampi(actor->patience + 4, 0, card->patience_threshold);
    actor->stability = clampi(actor->stability + 1, 0, 7);
    actor->aggression = clampi(actor->aggression - 1, 0, 99);
    if (actor->vulnerable_turns > 0) {
        actor->vulnerable_turns = clampi(actor->vulnerable_turns - 1, 0, 4);
    }
    snprintf(g_battle.log_a, sizeof(g_battle.log_a), "%.18s steadies.", card->name);
    snprintf(g_battle.log_b, sizeof(g_battle.log_b), "Patience rises.");
}

static void action_habitat(BattleSide *side) {
    BattleCreature *actor = active_creature(side);
    const GorgeCardDef *card = card_def(actor->card_index);
    int index;
    for (index = 0; index < side->habitat_count; ++index) {
        if (side->habitat_cards[index] >= 0) {
            const GorgeCardDef *habitat = card_def(side->habitat_cards[index]);
            actor->habitat_card_index = side->habitat_cards[index];
            side->habitat_cards[index] = -1;
            actor->stability = clampi(actor->stability + (habitat_home_match(card, habitat) ? 2 : 1), 0, 7);
            actor->coupling = clampi(actor->coupling + (habitat_home_match(card, habitat) ? 2 : 1), 0, 7);
            snprintf(g_battle.log_a, sizeof(g_battle.log_a), "%.18s loads %.18s.", card->name, habitat->name);
            snprintf(g_battle.log_b, sizeof(g_battle.log_b), habitat_home_match(card, habitat) ? "Coupling rising." : "Stability held.");
            gorge_audio_play_sfx(GORGE_SFX_DRAW);
            return;
        }
    }
    action_patience(side);
}

static void action_couple(BattleSide *actor_side, BattleSide *target_side) {
    BattleCreature *actor = active_creature(actor_side);
    if (actor->coupling < 3 || actor->habitat_card_index < 0) {
        action_aggress(actor_side, target_side, 0);
        return;
    }
    actor->coupling -= 3;
    action_aggress(actor_side, target_side, 1);
    gorge_audio_play_sfx(GORGE_SFX_COUPLE);
}

static void action_evolve(BattleSide *side, int branch_choice) {
    BattleCreature *actor = active_creature(side);
    const GorgeCardDef *card = card_def(actor->card_index);
    int next_card = branch_choice == 0 ? card->evolve_a : card->evolve_b;
    if (card->card_kind != GORGE_CARD_CREATURE || card->stage != 0 || next_card < 0 || actor->stability < 3) {
        action_patience(side);
        return;
    }
    {
        const GorgeCardDef *evolved = card_def(next_card);
        int hp_gain = evolved->hit_points - card->hit_points;
        actor->card_index = next_card;
        actor->current_hp = clampi(actor->current_hp + hp_gain, 1, evolved->hit_points);
        actor->patience = evolved->patience_threshold;
        actor->stability = 1;
        actor->coupling = clampi(actor->coupling + 1, 0, 7);
        snprintf(g_battle.log_a, sizeof(g_battle.log_a), "%.18s evolved.", evolved->name);
        snprintf(g_battle.log_b, sizeof(g_battle.log_b), branch_choice == 0 ? "Prime branch." : "Flux branch.");
        gorge_audio_play_sfx(GORGE_SFX_EVOLVE);
    }
}

static void action_swap(BattleSide *side) {
    int next = next_living_index(side, side->active_index);
    if (next == side->active_index) {
        action_patience(side);
        return;
    }
    side->active_index = next;
    snprintf(g_battle.log_a, sizeof(g_battle.log_a), "Reader slot changed.");
    snprintf(g_battle.log_b, sizeof(g_battle.log_b), "New creature inserted.");
    gorge_audio_play_sfx(GORGE_SFX_MENU);
}

static int ai_choose_action(BattleSide *actor_side, BattleSide *target_side) {
    BattleCreature *actor = active_creature(actor_side);
    const GorgeCardDef *card = card_def(actor->card_index);
    if (actor->current_hp <= card->hit_points / 3 && alive_count(actor_side) > 1) {
        return GORGE_ACTION_SWAP;
    }
    if (card->stage == 0 && actor->stability >= 3 && (card->evolve_a >= 0 || card->evolve_b >= 0)) {
        return GORGE_ACTION_EVOLVE;
    }
    if (actor->habitat_card_index < 0 && actor_side->habitat_count > 0) {
        return GORGE_ACTION_HABITAT;
    }
    if (actor->coupling >= 3 && active_creature(target_side)->vulnerable_turns > 0) {
        return GORGE_ACTION_COUPLE;
    }
    if (actor->patience <= card->patience_threshold / 2) {
        return GORGE_ACTION_PATIENCE;
    }
    return GORGE_ACTION_AGGRESS;
}

static void resolve_side_action(BattleSide *actor_side, BattleSide *target_side, int action, int branch_choice) {
    if (!active_creature(actor_side)->alive) {
        actor_side->active_index = next_living_index(actor_side, actor_side->active_index);
        if (!active_creature(actor_side)->alive) {
            return;
        }
    }

    switch (action) {
        case GORGE_ACTION_AGGRESS:
            action_aggress(actor_side, target_side, 0);
            break;
        case GORGE_ACTION_PATIENCE:
            action_patience(actor_side);
            break;
        case GORGE_ACTION_HABITAT:
            action_habitat(actor_side);
            break;
        case GORGE_ACTION_COUPLE:
            action_couple(actor_side, target_side);
            break;
        case GORGE_ACTION_EVOLVE:
            action_evolve(actor_side, branch_choice);
            break;
        case GORGE_ACTION_SWAP:
            action_swap(actor_side);
            break;
        default:
            break;
    }
}

static void check_battle_outcome(void) {
    if (alive_count(&g_battle.enemy) == 0) {
        g_battle.over = 1;
        g_battle.player_won = 1;
    } else if (alive_count(&g_battle.player) == 0) {
        g_battle.over = 1;
        g_battle.player_won = 0;
    }
}

static void execute_turn(int player_action) {
    int enemy_action = ai_choose_action(&g_battle.enemy, &g_battle.player);
    BattleCreature *player_active = active_creature(&g_battle.player);
    BattleCreature *enemy_active = active_creature(&g_battle.enemy);
    const GorgeCardDef *player_card = card_def(player_active->card_index);
    const GorgeCardDef *enemy_card = card_def(enemy_active->card_index);
    int player_priority = player_card->speed + rng_roll(9) + player_active->stability;
    int enemy_priority = enemy_card->speed + rng_roll(9) + enemy_active->stability;

    if (player_priority >= enemy_priority) {
        resolve_side_action(&g_battle.player, &g_battle.enemy, player_action, g_battle.player_branch_choice);
        check_battle_outcome();
        if (!g_battle.over) {
            resolve_side_action(&g_battle.enemy, &g_battle.player, enemy_action, rng_roll(2) - 1);
        }
    } else {
        resolve_side_action(&g_battle.enemy, &g_battle.player, enemy_action, rng_roll(2) - 1);
        check_battle_outcome();
        if (!g_battle.over) {
            resolve_side_action(&g_battle.player, &g_battle.enemy, player_action, g_battle.player_branch_choice);
        }
    }

    apply_upkeep(active_creature(&g_battle.player));
    apply_upkeep(active_creature(&g_battle.enemy));

    if (!active_creature(&g_battle.player)->alive) {
        g_battle.player.active_index = next_living_index(&g_battle.player, g_battle.player.active_index);
    }
    if (!active_creature(&g_battle.enemy)->alive) {
        g_battle.enemy.active_index = next_living_index(&g_battle.enemy, g_battle.enemy.active_index);
    }

    check_battle_outcome();
    ++g_battle.turn_number;
}

static void campaign_award_current_opponent(void) {
    int reward_slot;
    int opponent_deck = g_battle.opponent_deck;
    g_campaign.cleared_mask |= (1u << opponent_deck);
    g_campaign.reward_mask |= (1u << opponent_deck);
    g_campaign.reward_source_deck = opponent_deck;
    for (reward_slot = 0; reward_slot < 3; ++reward_slot) {
        g_campaign.reward_preview[reward_slot] = opponent_deck * GORGE_CARDS_PER_DECK + g_gorge_decks[opponent_deck].reward_cards[reward_slot];
    }
    g_campaign.selection = (uint8_t)(first_uncleared_opponent() >= 0 ? first_uncleared_opponent() : 0);
    campaign_password_refresh();
}

static void render_title(void) {
    screen_clear();
    iprintf("GORGE\n");
    iprintf("ELEMENTAL CARD\n");
    iprintf("SPECTRUMS\n\n");
    iprintf("A/START: PLAY GAME\n");
    iprintf("B: PASSWORD VAULT\n\n");
    iprintf("Two-slot reader and\n");
    iprintf("wireless dice are\n");
    iprintf("simulated in-ROM.\n\n");
    if (g_campaign.active) {
        iprintf("Current run ready.\n");
    }
}

static void render_starter_select(void) {
    const GorgeDeckDef *deck = &g_gorge_decks[g_campaign.selection];
    screen_clear();
    iprintf("SELECT STARTER DECK\n\n");
    iprintf("Deck %d/%d\n", g_campaign.selection + 1, GORGE_DECK_COUNT);
    iprintf("%.20s\n", deck->name);
    iprintf("%.27s\n\n", deck->theme);
    iprintf("A: choose starter\n");
    iprintf("L/R or LEFT/RIGHT\n");
    iprintf("to browse decks\n");
}

static void render_world(void) {
    int uncleared = first_uncleared_opponent();
    screen_clear();
    iprintf("GORGE CAMPAIGN\n\n");
    iprintf("Starter: %.20s\n", g_gorge_decks[g_campaign.starter_deck].name);
    iprintf("Chosen Rival:\n%.20s\n", g_gorge_decks[g_campaign.selection].name);
    iprintf("Cleared decks: %d/14\n", __builtin_popcount((unsigned)g_campaign.cleared_mask));
    iprintf("Rewards claimed: %d\n\n", __builtin_popcount((unsigned)g_campaign.reward_mask));
    if (uncleared < 0) {
        iprintf("All rivals defeated.\n");
        iprintf("A: rematch chosen deck\n\n");
    } else {
        iprintf("A: battle this rival\n\n");
    }
    iprintf("START: password vault\n");
    iprintf("SELECT: restart run\n");
    iprintf("L/R: choose rival\n\n");
    iprintf("Password %.16s\n", g_campaign.password_buf);
}

static void render_battle(void) {
    BattleCreature *player = active_creature(&g_battle.player);
    BattleCreature *enemy = active_creature(&g_battle.enemy);
    const GorgeCardDef *player_card = card_def(player->card_index);
    const GorgeCardDef *enemy_card = card_def(enemy->card_index);
    screen_clear();
    iprintf("BATTLE %d\n", g_battle.turn_number);
    iprintf("Rival: %.20s\n\n", g_gorge_decks[g_battle.opponent_deck].name);
    iprintf("READER A %.18s\n", player_card->name);
    iprintf("HP %d/%d PT %d ST %d CP %d\n", player->current_hp, player_card->hit_points, player->patience, player->stability, player->coupling);
    iprintf("READER B %.18s\n", enemy_card->name);
    iprintf("HP %d/%d PT %d ST %d CP %d\n\n", enemy->current_hp, enemy_card->hit_points, enemy->patience, enemy->stability, enemy->coupling);
    iprintf("Bench %d:%d\n", alive_count(&g_battle.player), alive_count(&g_battle.enemy));
    iprintf("Action: %s\n", k_action_labels[g_battle.player_action_cursor]);
    if (g_battle.player_action_cursor == GORGE_ACTION_EVOLVE) {
        iprintf("Branch: %s\n", g_battle.player_branch_choice == 0 ? "Prime" : "Flux");
    }
    iprintf("\n%s\n%s\n", g_battle.log_a, g_battle.log_b);
    iprintf("UP/DOWN action\nA confirm  L/R alt\n");
}

static void render_reward(void) {
    const GorgeDeckDef *deck = &g_gorge_decks[g_campaign.reward_source_deck];
    screen_clear();
    iprintf("RIVAL DEFEATED\n\n");
    iprintf("Reward cards from\n%.20s\n\n", deck->name);
    iprintf("1 %.18s\n", card_def(g_campaign.reward_preview[0])->name);
    iprintf("2 %.18s\n", card_def(g_campaign.reward_preview[1])->name);
    iprintf("3 %.18s\n\n", card_def(g_campaign.reward_preview[2])->name);
    iprintf("A: continue campaign\n");
}

static void render_password(void) {
    screen_clear();
    iprintf("PASSWORD VAULT\n\n");
    iprintf("%.16s\n", g_campaign.password_buf);
    iprintf("^");
    {
        int index;
        for (index = 0; index < g_campaign.password_index; ++index) {
            iprintf(" ");
        }
    }
    iprintf("\n\n");
    iprintf("LEFT/RIGHT move\n");
    iprintf("A increment\nB decrement\n");
    iprintf("START apply\nSELECT cancel\n");
}

static void handle_title_input(uint16_t keys) {
    if (keys & (KEY_A | KEY_START)) {
        if (g_campaign.active) {
            g_screen = SCREEN_WORLD;
            gorge_audio_play_song(GORGE_SONG_WORLD);
        } else {
            g_campaign.selection = 0;
            g_screen = SCREEN_STARTER;
        }
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & KEY_B) {
        memset(&g_campaign, 0, sizeof(g_campaign));
        memset(g_campaign.password_buf, '0', GORGE_PASSWORD_LEN);
        g_campaign.password_buf[GORGE_PASSWORD_LEN] = '\0';
        g_campaign.password_index = 0;
        g_screen = SCREEN_PASSWORD;
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    }
}

static void cycle_selection(int delta) {
    int next = (int)g_campaign.selection + delta;
    if (next < 0) {
        next = GORGE_DECK_COUNT - 1;
    }
    if (next >= GORGE_DECK_COUNT) {
        next = 0;
    }
    g_campaign.selection = (uint8_t)next;
}

static void handle_starter_input(uint16_t keys) {
    if (keys & (KEY_LEFT | KEY_L)) {
        cycle_selection(-1);
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & (KEY_RIGHT | KEY_R)) {
        cycle_selection(1);
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & KEY_A) {
        campaign_begin(g_campaign.selection);
        g_screen = SCREEN_WORLD;
        gorge_audio_play_song(GORGE_SONG_WORLD);
        gorge_audio_play_sfx(GORGE_SFX_REWARD);
    }
}

static void handle_world_input(uint16_t keys) {
    if (keys & (KEY_LEFT | KEY_L)) {
        cycle_selection(-1);
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & (KEY_RIGHT | KEY_R)) {
        cycle_selection(1);
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & KEY_A) {
        if (g_campaign.selection == g_campaign.starter_deck) {
            cycle_selection(1);
        }
        battle_prepare(g_campaign.selection);
        g_screen = SCREEN_BATTLE;
        gorge_audio_play_sfx(GORGE_SFX_DRAW);
    } else if (keys & KEY_START) {
        campaign_password_refresh();
        g_campaign.password_index = 0;
        g_screen = SCREEN_PASSWORD;
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & KEY_SELECT) {
        g_campaign.active = 0;
        g_screen = SCREEN_STARTER;
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    }
}

static void handle_battle_input(uint16_t keys) {
    if (g_battle.over) {
        if (g_battle.player_won) {
            campaign_award_current_opponent();
            g_screen = SCREEN_REWARD;
            gorge_audio_play_song(GORGE_SONG_VICTORY);
            gorge_audio_play_sfx(GORGE_SFX_REWARD);
        } else {
            g_screen = SCREEN_WORLD;
            gorge_audio_play_song(GORGE_SONG_WORLD);
            gorge_audio_play_sfx(GORGE_SFX_MISS);
        }
        return;
    }

    if (keys & (KEY_UP | KEY_L)) {
        g_battle.player_action_cursor = (g_battle.player_action_cursor + GORGE_ACTION_COUNT - 1) % GORGE_ACTION_COUNT;
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & (KEY_DOWN | KEY_R)) {
        g_battle.player_action_cursor = (g_battle.player_action_cursor + 1) % GORGE_ACTION_COUNT;
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if ((keys & KEY_LEFT) && g_battle.player_action_cursor == GORGE_ACTION_EVOLVE) {
        g_battle.player_branch_choice = 0;
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if ((keys & KEY_RIGHT) && g_battle.player_action_cursor == GORGE_ACTION_EVOLVE) {
        g_battle.player_branch_choice = 1;
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & KEY_A) {
        execute_turn(g_battle.player_action_cursor);
    }
}

static void handle_reward_input(uint16_t keys) {
    if (keys & (KEY_A | KEY_START)) {
        g_screen = SCREEN_WORLD;
        gorge_audio_play_song(GORGE_SONG_WORLD);
    }
}

static char increment_hex(char value, int delta) {
    const char *alphabet = "0123456789ABCDEF";
    int index;
    for (index = 0; index < 16; ++index) {
        if (alphabet[index] == value) {
            return alphabet[(index + delta + 16) % 16];
        }
    }
    return '0';
}

static void handle_password_input(uint16_t keys) {
    if (keys & KEY_LEFT) {
        if (g_campaign.password_index > 0) {
            --g_campaign.password_index;
        }
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & KEY_RIGHT) {
        if (g_campaign.password_index + 1 < GORGE_PASSWORD_LEN) {
            ++g_campaign.password_index;
        }
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & KEY_A) {
        g_campaign.password_buf[g_campaign.password_index] = increment_hex(g_campaign.password_buf[g_campaign.password_index], 1);
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & KEY_B) {
        g_campaign.password_buf[g_campaign.password_index] = increment_hex(g_campaign.password_buf[g_campaign.password_index], -1);
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    } else if (keys & KEY_START) {
        uint32_t cleared = 0;
        uint32_t payload = 0;
        if (gorge_password_decode(g_campaign.password_buf, &cleared, &payload) == 0) {
            campaign_apply_password(cleared, payload);
            g_screen = SCREEN_WORLD;
            gorge_audio_play_song(GORGE_SONG_WORLD);
            gorge_audio_play_sfx(GORGE_SFX_REWARD);
        }
    } else if (keys & KEY_SELECT) {
        g_screen = g_campaign.active ? SCREEN_WORLD : SCREEN_TITLE;
        gorge_audio_play_sfx(GORGE_SFX_MENU);
    }
}

int main(void) {
    irqInit();
    irqEnable(IRQ_VBLANK);
    consoleDemoInit();
    memset(g_campaign.password_buf, '0', GORGE_PASSWORD_LEN);
    g_campaign.password_buf[GORGE_PASSWORD_LEN] = '\0';
    gorge_audio_init();
    gorge_audio_play_song(GORGE_SONG_TITLE);

    while (1) {
        uint16_t keys;
        VBlankIntrWait();
        gorge_audio_tick();
        scanKeys();
        keys = keysDown();

        switch (g_screen) {
            case SCREEN_TITLE:
                handle_title_input(keys);
                render_title();
                break;
            case SCREEN_STARTER:
                handle_starter_input(keys);
                render_starter_select();
                break;
            case SCREEN_WORLD:
                handle_world_input(keys);
                render_world();
                break;
            case SCREEN_BATTLE:
                handle_battle_input(keys);
                render_battle();
                break;
            case SCREEN_REWARD:
                handle_reward_input(keys);
                render_reward();
                break;
            case SCREEN_PASSWORD:
                handle_password_input(keys);
                render_password();
                break;
            default:
                g_screen = SCREEN_TITLE;
                break;
        }
    }

    return 0;
}