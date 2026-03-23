#include "blastmonidz.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int rng_range(int min_value, int max_value) {
    if (max_value <= min_value) {
        return min_value;
    }
    return min_value + (rand() % (max_value - min_value + 1));
}

static int clamp_int(int value, int min_value, int max_value) {
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}

static int tile_bonus(float bias, int scale) {
    int bonus = (int)(bias * (float)scale + 0.5f);
    if (bonus < 0) {
        bonus = 0;
    }
    return bonus;
}

static int genome_bonus(float factor, int scale) {
    int bonus = (int)(factor * (float)scale + 0.5f);
    if (bonus < 0) {
        bonus = 0;
    }
    return bonus;
}

static void apply_doctrine_social_effects(GameState *state, int player_id);

const char *blastmonidz_doctrine_name(int doctrine) {
    switch (doctrine) {
        case BLASTMONIDZ_DOCTRINE_HARMONIZER:
            return "Harmonizer";
        case BLASTMONIDZ_DOCTRINE_STEWARD:
            return "Steward";
        case BLASTMONIDZ_DOCTRINE_MEDIATOR:
            return "Mediator";
        case BLASTMONIDZ_DOCTRINE_KINWEAVER:
            return "Kinweaver";
        default:
            return "Unaffiliated";
    }
}

static const BlastmonidzHomeTile *player_home_tile(const GameState *state, int player_id) {
    if (!state || player_id < 0 || player_id >= MAX_PLAYERS) {
        return NULL;
    }
    return blastmonidz_select_home_tile(state, state->players[player_id].mon.x, state->players[player_id].mon.y);
}

static void refresh_self_feed_balance(BlastmonidzSelfFeed *feed) {
    if (!feed) {
        return;
    }
    feed->balance = clamp_int(
        ((feed->inner_signal + feed->world_signal) / 2) - (feed->rival_signal / 3) - (feed->ghost_signal / 4) + 24,
        0,
        100);
}

static void tune_self_feed(Blastonid *mon, int inner_delta, int world_delta, int rival_delta, int ghost_delta) {
    if (!mon) {
        return;
    }
    mon->self_feed.inner_signal = clamp_int(mon->self_feed.inner_signal + inner_delta, 0, 100);
    mon->self_feed.world_signal = clamp_int(mon->self_feed.world_signal + world_delta, 0, 100);
    mon->self_feed.rival_signal = clamp_int(mon->self_feed.rival_signal + rival_delta, 0, 100);
    mon->self_feed.ghost_signal = clamp_int(mon->self_feed.ghost_signal + ghost_delta, 0, 100);
    refresh_self_feed_balance(&mon->self_feed);
}

static void refresh_world_feed(GameState *state) {
    int i;
    int alive_count = 0;
    int inner_total = 0;
    int world_total = 0;
    int rival_total = 0;
    int ghost_total = 0;
    if (!state) {
        return;
    }
    for (i = 0; i < MAX_PLAYERS; ++i) {
        const Blastonid *mon = &state->players[i].mon;
        inner_total += mon->self_feed.inner_signal;
        world_total += mon->self_feed.world_signal;
        rival_total += mon->self_feed.rival_signal;
        ghost_total += mon->self_feed.ghost_signal;
        if (mon->alive) {
            ++alive_count;
        }
    }
    if (MAX_PLAYERS > 0) {
        state->world_feed.inner_signal = clamp_int(inner_total / MAX_PLAYERS, 0, 100);
        state->world_feed.world_signal = clamp_int(world_total / MAX_PLAYERS + (state->arena.chemistry[0] + state->arena.chemistry[1] + state->arena.chemistry[2]) / 12, 0, 100);
        state->world_feed.rival_signal = clamp_int(rival_total / MAX_PLAYERS + state->arena.last_explosion_kills * 7 + state->arena.last_explosion_gems * 2, 0, 100);
        state->world_feed.ghost_signal = clamp_int(ghost_total / MAX_PLAYERS + (MAX_PLAYERS - alive_count) * 9, 0, 100);
    } else {
        state->world_feed.inner_signal = 0;
        state->world_feed.world_signal = 0;
        state->world_feed.rival_signal = 0;
        state->world_feed.ghost_signal = 0;
    }
    refresh_self_feed_balance(&state->world_feed);
}

static unsigned char *arena_tile(Arena *arena, int x, int y) {
    return &arena->tiles[y * arena->width + x];
}

static void init_blastonid(Blastonid *mon, const StarterSeed *seed, const char *owner_name, int x, int y) {
    int i;
    snprintf(mon->name, MAX_NAME_LEN, "%s of %s", seed->name, owner_name);
    mon->starter = seed;
    mon->x = x;
    mon->y = y;
    mon->health = seed->base_health;
    mon->max_health = seed->base_health;
    mon->delay_ticks = 0;
    mon->growth_stage = 0;
    mon->evo_points = 0;
    mon->bomb_cooldown = 0;
    mon->alive = 1;
    mon->ghost_timer = 0;
    mon->ghost_target_id = -1;
    mon->qte_charge = 0;
    mon->concoction_id = 0;
    mon->round_kills = 0;
    mon->gems_cleared = 0;
    mon->precision_chain = 0;
    mon->stage_penalties_applied = 0;
    mon->self_feed.inner_signal = clamp_int(44 + seed->metabolic_bias * 5, 0, 100);
    mon->self_feed.world_signal = clamp_int(36 + seed->base_frequency / 2, 0, 100);
    mon->self_feed.rival_signal = clamp_int(18 + seed->volatility * 4, 0, 100);
    mon->self_feed.ghost_signal = clamp_int(8 + seed->metabolic_bias, 0, 100);
    refresh_self_feed_balance(&mon->self_feed);
    for (i = 0; i < 6; ++i) {
        mon->genome[i] = rng_range(6, 24) + (seed->base_frequency % 7) + i;
    }
}

static void seed_player(BlastKin *player, const char *name, int is_human, int artisapien, int doctrine, const StarterSeed *seed, int x, int y) {
    snprintf(player->name, MAX_NAME_LEN, "%s", name);
    player->is_human = is_human;
    player->artisapien = artisapien;
    player->doctrine = doctrine;
    player->profile_rank = rng_range(1, 9);
    snprintf(player->ai_debug_line, sizeof(player->ai_debug_line), "%s", is_human ? "human pilot" : "awaiting doctrine pass");
    init_blastonid(&player->mon, seed, name, x, y);
}

static int tile_blocks(const Arena *arena, int x, int y) {
    if (x < 0 || y < 0 || x >= arena->width || y >= arena->height) {
        return 1;
    }
    if (arena->tiles[y * arena->width + x] == TILE_WALL) {
        return 1;
    }
    if (arena->tiles[y * arena->width + x] == TILE_CRATE) {
        return 1;
    }
    if (blastmonidz_gem_at(arena, x, y) >= 0) {
        return 1;
    }
    return blastmonidz_bomb_at(arena, x, y) >= 0;
}

static void move_player(GameState *state, int player_id, int dx, int dy) {
    Blastonid *mon = &state->players[player_id].mon;
    const BlastmonidzGenomeProfile *profile = &mon->cosmetic_genome;
    const BlastmonidzHomeTile *home_tile;
    int target_x;
    int target_y;
    if (!mon->alive) {
        return;
    }
    target_x = mon->x + dx;
    target_y = mon->y + dy;
    if (blastmonidz_player_at(state, target_x, target_y) >= 0) {
        return;
    }
    if (!tile_blocks(&state->arena, target_x, target_y)) {
        mon->x = target_x;
        mon->y = target_y;
        home_tile = player_home_tile(state, player_id);
        if (home_tile) {
            mon->delay_ticks = clamp_int(mon->delay_ticks + tile_bonus(1.0f - home_tile->structural_bias, 2) - tile_bonus(home_tile->shelter_bias, 1) - genome_bonus(profile->animation_factor, 1), 0, 99);
            mon->evo_points += tile_bonus(home_tile->growth_bias, 2) + genome_bonus(profile->mutation_factor, 2);
        }
        mon->delay_ticks = clamp_int(mon->delay_ticks - genome_bonus(profile->animation_factor, 1), 0, 99);
        tune_self_feed(mon, 1, 2, -1, 0);
        blastmonidz_refresh_player_genome(state, player_id);
        blastmonidz_refresh_asset_genome(state);
    }
}

static void apply_leader_penalty(GameState *state, int source_id) {
    int i;
    int leader_id = -1;
    int best_wins = -1;
    (void)source_id;
    for (i = 0; i < MAX_PLAYERS; ++i) {
        if (state->players[i].run_wins > best_wins) {
            best_wins = state->players[i].run_wins;
            leader_id = i;
        }
    }
    if (leader_id >= 0 && state->players[leader_id].run_wins > 0) {
        --state->players[leader_id].run_wins;
        tune_self_feed(&state->players[leader_id].mon, -2, 0, 4, 0);
        blastmonidz_push_log(state, "A growth surge steals a win from the leader.");
    }
}

static void evolve_player(GameState *state, int player_id) {
    Blastonid *mon = &state->players[player_id].mon;
    const BlastmonidzGenomeProfile *profile = &mon->cosmetic_genome;
    const BlastmonidzHomeTile *home_tile = player_home_tile(state, player_id);
    int chemistry_drive;
    if (!mon->alive) {
        return;
    }
    chemistry_drive = state->arena.chemistry[mon->concoction_id % 3] + state->arena.mineral_pressure / 4 + mon->gems_cleared * 2;
    chemistry_drive += genome_bonus(profile->mutation_factor, 10) + genome_bonus(profile->depth_factor, 4);
    if (home_tile) {
        chemistry_drive += tile_bonus(home_tile->growth_bias, 8) + tile_bonus(home_tile->ornamental_bias, 2);
    }
    mon->evo_points += chemistry_drive / 10 + mon->starter->metabolic_bias;
    if (mon->growth_stage == 0 && mon->evo_points >= 45) {
        mon->growth_stage = 1;
        mon->max_health += 14;
        mon->health += 10;
        tune_self_feed(mon, 6, 5, 1, -2);
        apply_leader_penalty(state, player_id);
        blastmonidz_push_log(state, "A Blastonid enters Burst Form and the standings destabilize.");
    } else if (mon->growth_stage == 1 && mon->evo_points >= 95) {
        mon->growth_stage = 2;
        mon->max_health += 16;
        mon->health += 12;
        tune_self_feed(mon, 7, 6, 2, -3);
        apply_leader_penalty(state, player_id);
        blastmonidz_push_log(state, "A Blastonid enters Crown Form and steals momentum from the leader.");
    } else if (mon->growth_stage == 2 && mon->evo_points >= 155) {
        mon->growth_stage = 3;
        mon->max_health += 20;
        mon->health += 18;
        tune_self_feed(mon, 9, 8, 2, -4);
        apply_leader_penalty(state, player_id);
        blastmonidz_push_log(state, "A Blastonid hits Myth Form; consensus time shudders.");
    }
    mon->health = clamp_int(mon->health, 0, mon->max_health);
    blastmonidz_refresh_player_genome(state, player_id);
}

static void mark_player_dead(GameState *state, int victim_id, int owner_id) {
    Blastonid *victim = &state->players[victim_id].mon;
    char message[MAX_LOG_LEN];
    victim->alive = 0;
    victim->ghost_timer = 5 + rng_range(0, 4);
    victim->ghost_target_id = owner_id >= 0 ? owner_id : ((victim_id + 1) % MAX_PLAYERS);
    victim->qte_charge = 0;
    victim->precision_chain = 0;
    tune_self_feed(victim, -8, -5, 5, 28);
    if (owner_id >= 0 && owner_id < MAX_PLAYERS) {
        tune_self_feed(&state->players[owner_id].mon, 2, 1, 6, 0);
    }
    snprintf(message, sizeof(message), "%s is blown into a ghost timeline.", state->players[victim_id].name);
    blastmonidz_push_log(state, message);
}

static void apply_damage(GameState *state, int victim_id, int amount, int frequency, int owner_id) {
    Blastonid *victim = &state->players[victim_id].mon;
    const BlastmonidzGenomeProfile *victim_profile = &victim->cosmetic_genome;
    char message[MAX_LOG_LEN];
    int resonance;
    if (!victim->alive) {
        return;
    }
    resonance = abs(frequency - victim->starter->base_frequency);
    amount += clamp_int((18 - resonance) / 3, 0, 6);
    amount -= genome_bonus(victim_profile->structural_factor, 4);
    if (amount < 1) {
        amount = 1;
    }
    victim->health -= amount;
    victim->delay_ticks += 1 + amount / 5 + genome_bonus(1.0f - victim_profile->animation_factor, 2);
    tune_self_feed(victim, -(amount / 3), 0, 3 + amount / 4, 1 + amount / 7);
    if (owner_id >= 0 && owner_id < MAX_PLAYERS) {
        const BlastmonidzGenomeProfile *attacker_profile = &state->players[owner_id].mon.cosmetic_genome;
        tune_self_feed(&state->players[owner_id].mon, 1 + genome_bonus(attacker_profile->mutation_factor, 2), 0, 2 + amount / 6, 0);
        state->players[owner_id].mon.evo_points += genome_bonus(attacker_profile->mutation_factor, 2);
    }
    snprintf(message, sizeof(message), "%s takes %d; lag now %d.", state->players[victim_id].name, amount, victim->delay_ticks);
    blastmonidz_push_log(state, message);
    blastmonidz_refresh_player_genome(state, victim_id);
    if (owner_id >= 0 && owner_id < MAX_PLAYERS) {
        blastmonidz_refresh_player_genome(state, owner_id);
    }
    if (victim->health <= 0) {
        if (owner_id >= 0 && owner_id < MAX_PLAYERS) {
            state->players[owner_id].mon.round_kills += 1;
        }
        mark_player_dead(state, victim_id, owner_id);
    }
}

static void clear_gem(GameState *state, int gem_id, int owner_id, int chemistry) {
    BombGem *gem = &state->arena.gems[gem_id];
    char message[MAX_LOG_LEN];
    if (!gem->active) {
        return;
    }
    gem->active = 0;
    state->arena.chemistry[chemistry % 3] += gem->tier + 3;
    state->arena.mineral_pressure += 1 + gem->class_id % 3;
    state->arena.last_explosion_gems += 1;
    if (owner_id >= 0 && owner_id < MAX_PLAYERS) {
        const BlastmonidzHomeTile *home_tile = player_home_tile(state, owner_id);
        const BlastmonidzGenomeProfile *profile = &state->players[owner_id].mon.cosmetic_genome;
        state->players[owner_id].mon.gems_cleared += 1;
        state->players[owner_id].mon.evo_points += 5 + gem->tier + (home_tile ? tile_bonus(home_tile->growth_bias, 4) : 0) + genome_bonus(profile->mutation_factor, 3);
        tune_self_feed(&state->players[owner_id].mon, 3, 7 + gem->tier / 2, -1, -2);
        blastmonidz_refresh_player_genome(state, owner_id);
    }
    snprintf(message, sizeof(message), "Bomb Gem %c collapses into chemistry tier %d.", gem->glyph, gem->tier);
    blastmonidz_push_log(state, message);
}

static void explode_bomb(GameState *state, int bomb_id) {
    static const int directions[5][2] = {{0, 0}, {1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    int d;
    int step;
    Bomb *bomb = &state->arena.bombs[bomb_id];
    char message[MAX_LOG_LEN];
    int effective_power = bomb->power;
    if (!bomb->active) {
        return;
    }
    state->arena.last_explosion_owner = bomb->owner_id;
    state->arena.last_explosion_kills = 0;
    state->arena.last_explosion_gems = 0;
    if (bomb->owner_id >= 0 && bomb->owner_id < MAX_PLAYERS) {
        const BlastmonidzHomeTile *home_tile = player_home_tile(state, bomb->owner_id);
        const BlastmonidzGenomeProfile *profile = &state->players[bomb->owner_id].mon.cosmetic_genome;
        if (home_tile) {
            effective_power += tile_bonus(home_tile->ornamental_bias, 2);
            effective_power -= tile_bonus(home_tile->shelter_bias, 1);
            if (effective_power < 1) {
                effective_power = 1;
            }
        }
        effective_power += genome_bonus(profile->depth_factor, 2);
        tune_self_feed(&state->players[bomb->owner_id].mon, 1, 0, 4, 0);
    }
    snprintf(message, sizeof(message), "%s detonates a %s bomb.", state->players[bomb->owner_id].name, blastmonidz_concoctions[bomb->chemistry]);
    blastmonidz_push_log(state, message);
    for (d = 0; d < 5; ++d) {
        int dx = directions[d][0];
        int dy = directions[d][1];
        for (step = 0; step <= effective_power; ++step) {
            int x = bomb->x + dx * step;
            int y = bomb->y + dy * step;
            int victim_id;
            int gem_id;
            if (x < 0 || y < 0 || x >= state->arena.width || y >= state->arena.height) {
                break;
            }
            if (*arena_tile(&state->arena, x, y) == TILE_WALL) {
                break;
            }
            victim_id = blastmonidz_player_at(state, x, y);
            if (victim_id >= 0) {
                int was_alive = state->players[victim_id].mon.alive;
                apply_damage(state, victim_id, 15 + bomb->chemistry * 2 + effective_power, bomb->frequency, bomb->owner_id);
                if (was_alive && !state->players[victim_id].mon.alive) {
                    state->arena.last_explosion_kills += 1;
                }
            }
            gem_id = blastmonidz_gem_at(&state->arena, x, y);
            if (gem_id >= 0) {
                clear_gem(state, gem_id, bomb->owner_id, bomb->chemistry);
                break;
            }
            if (*arena_tile(&state->arena, x, y) == TILE_CRATE) {
                *arena_tile(&state->arena, x, y) = TILE_EMPTY;
                break;
            }
        }
    }
    state->arena.chemistry[bomb->chemistry % 3] += 5 + effective_power;
    bomb->active = 0;
}

static void tick_bombs(GameState *state) {
    int i;
    for (i = 0; i < MAX_BOMBS; ++i) {
        Bomb *bomb = &state->arena.bombs[i];
        if (!bomb->active) {
            continue;
        }
        --bomb->timer;
        if (bomb->timer <= 0) {
            explode_bomb(state, i);
        }
    }
}

static void emit_metabolic_chemistry(GameState *state) {
    int i;
    state->arena.chemistry[0] = clamp_int(state->arena.chemistry[0] - 1, 0, 999);
    state->arena.chemistry[1] = clamp_int(state->arena.chemistry[1] - 1, 0, 999);
    state->arena.chemistry[2] = clamp_int(state->arena.chemistry[2] - 1, 0, 999);
    state->arena.mineral_pressure = clamp_int(state->arena.mineral_pressure - 1, 0, 999);
    for (i = 0; i < MAX_PLAYERS; ++i) {
        Blastonid *mon = &state->players[i].mon;
        const BlastmonidzGenomeProfile *profile = &mon->cosmetic_genome;
        const BlastmonidzHomeTile *home_tile = player_home_tile(state, i);
        if (!mon->alive) {
            continue;
        }
        state->arena.chemistry[0] += (mon->genome[0] + mon->growth_stage + mon->starter->metabolic_bias + genome_bonus(profile->silhouette_factor, 2)) % 3;
        state->arena.chemistry[1] += (mon->genome[2] + mon->concoction_id + 1 + genome_bonus(profile->shading_factor, 3)) % 4;
        state->arena.chemistry[2] += (mon->genome[4] + mon->starter->volatility + genome_bonus(profile->depth_factor, 2)) % 3;
        if (home_tile) {
            state->arena.mineral_pressure += tile_bonus(home_tile->structural_bias, 1);
            state->arena.chemistry[mon->concoction_id % 3] += tile_bonus(home_tile->growth_bias, 1);
        }
        state->arena.mineral_pressure += genome_bonus(profile->structural_factor, 1);
        tune_self_feed(mon,
            1 + mon->growth_stage,
            1 + (state->arena.chemistry[mon->concoction_id % 3] % 2) + genome_bonus(profile->animation_factor, 1),
            mon->delay_ticks > 0 ? 1 : -1,
            0);
        apply_doctrine_social_effects(state, i);
        blastmonidz_refresh_player_genome(state, i);
    }
    blastmonidz_refresh_asset_genome(state);
}

static void tick_ghosts(GameState *state) {
    int i;
    for (i = 0; i < MAX_PLAYERS; ++i) {
        Blastonid *mon = &state->players[i].mon;
        if (mon->alive || mon->ghost_timer <= 0) {
            continue;
        }
        --mon->ghost_timer;
        if (mon->ghost_timer == 0) {
            blastmonidz_push_log(state, "A ghost timeline aligns; a fallen Blastonid can manifest back in.");
        } else {
            tune_self_feed(mon, 0, 0, 0, 1);
        }
    }
}

static void try_respawn_player(GameState *state, int player_id, int manual_trigger) {
    if (!state || player_id < 0 || player_id >= MAX_PLAYERS) {
        return;
    }
    Blastonid *mon = &state->players[player_id].mon;
    const BlastmonidzHomeTile *home_tile;
    int chemistry_alignment;
    char message[MAX_LOG_LEN];
    if (mon->alive || mon->ghost_timer > 0) {
        return;
    }
    chemistry_alignment = state->arena.chemistry[(mon->starter->base_frequency / 10) % 3] + state->arena.mineral_pressure;
    if (!manual_trigger && chemistry_alignment < 26) {
        return;
    }
    mon->alive = 1;
    mon->health = mon->max_health / 2;
    mon->delay_ticks += 4;
    mon->x = (player_id % 2 == 0) ? 3 : ARENA_W - 4;
    mon->y = (player_id < 2) ? 3 : ARENA_H - 4;
    home_tile = player_home_tile(state, player_id);
    mon->ghost_timer = 0;
    mon->qte_charge = 0;
    if (home_tile) {
        mon->health = clamp_int(mon->health + tile_bonus(home_tile->shelter_bias, mon->max_health / 4), 1, mon->max_health);
        mon->delay_ticks = clamp_int(mon->delay_ticks - tile_bonus(home_tile->structural_bias, 2), 0, 99);
    }
    mon->health = clamp_int(mon->health + genome_bonus(mon->cosmetic_genome.structural_factor, mon->max_health / 5), 1, mon->max_health);
    mon->delay_ticks = clamp_int(mon->delay_ticks - genome_bonus(mon->cosmetic_genome.animation_factor, 2), 0, 99);
    tune_self_feed(mon, 6, 5, -2, -18);
    blastmonidz_refresh_player_genome(state, player_id);
    blastmonidz_refresh_asset_genome(state);
    snprintf(message, sizeof(message), "%s re-manifests from the ghost line with %d health.", state->players[player_id].name, mon->health);
    blastmonidz_push_log(state, message);
}

static void place_bomb(GameState *state, int player_id) {
    int i;
    Blastonid *mon = &state->players[player_id].mon;
    const BlastmonidzHomeTile *home_tile = player_home_tile(state, player_id);
    const BlastmonidzGenomeProfile *profile = &mon->cosmetic_genome;
    char message[MAX_LOG_LEN];
    if (!mon->alive || mon->bomb_cooldown > 0 || blastmonidz_bomb_at(&state->arena, mon->x, mon->y) >= 0) {
        return;
    }
    for (i = 0; i < MAX_BOMBS; ++i) {
        Bomb *bomb = &state->arena.bombs[i];
        if (!bomb->active) {
            bomb->active = 1;
            bomb->x = mon->x;
            bomb->y = mon->y;
            bomb->timer = 3 + (mon->concoction_id == 1 ? 1 : 0) - genome_bonus(profile->animation_factor, 1);
            if (bomb->timer < 1) {
                bomb->timer = 1;
            }
            bomb->power = 2 + mon->growth_stage + (mon->starter->volatility > 6 ? 1 : 0) + genome_bonus(profile->depth_factor, 1);
            if (home_tile) {
                bomb->power += tile_bonus(home_tile->ornamental_bias, 1);
            }
            bomb->owner_id = player_id;
            bomb->chemistry = mon->concoction_id;
            bomb->frequency = mon->starter->base_frequency + mon->genome[1] + mon->concoction_id * 3 + genome_bonus(profile->shading_factor, 6);
            mon->bomb_cooldown = clamp_int(3 - genome_bonus(profile->animation_factor, 1), 1, 9);
            tune_self_feed(mon, 2, 0, 4, 0);
            blastmonidz_refresh_player_genome(state, player_id);
            blastmonidz_refresh_asset_genome(state);
            snprintf(message, sizeof(message), "%s plants a %s bomb.", state->players[player_id].name, blastmonidz_concoctions[mon->concoction_id]);
            blastmonidz_push_log(state, message);
            break;
        }
    }
}

static void cycle_concoction(Blastonid *mon) {
    mon->concoction_id = (mon->concoction_id + 1) % 4;
    tune_self_feed(mon, 3, 2, 0, 0);
}

static void tick_cooldowns(GameState *state) {
    int i;
    for (i = 0; i < MAX_PLAYERS; ++i) {
        Blastonid *mon = &state->players[i].mon;
        if (mon->delay_ticks > 0) {
            --mon->delay_ticks;
        }
        if (mon->bomb_cooldown > 0) {
            --mon->bomb_cooldown;
        }
    }
}

static void maybe_spawn_new_gem(GameState *state) {
    if (rng_range(0, 100) < 14) {
        int i;
        for (i = 0; i < MAX_GEMS; ++i) {
            BombGem *gem = &state->arena.gems[i];
            if (!gem->active) {
                gem->active = 1;
                gem->x = rng_range(2, ARENA_W - 3);
                gem->y = rng_range(2, ARENA_H - 3);
                gem->class_id = rng_range(0, 197);
                gem->tier = rng_range(0, 12);
                gem->frequency = rng_range(18, 64);
                gem->stability = rng_range(10, 40);
                gem->glyph = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[(gem->class_id + gem->tier) % 36];
                state->world_feed.world_signal = clamp_int(state->world_feed.world_signal + 2, 0, 100);
                refresh_self_feed_balance(&state->world_feed);
                blastmonidz_push_log(state, "A new Bomb Gem mineralizes under the arena.");
                break;
            }
        }
    }
}

enum {
    BOT_ACTION_WAIT = 0,
    BOT_ACTION_MOVE_GEM,
    BOT_ACTION_MOVE_RIVAL,
    BOT_ACTION_MOVE_SAFETY,
    BOT_ACTION_PLACE_BOMB,
    BOT_ACTION_CYCLE_CONCOCTION
};

typedef struct {
    int action_type;
    int target_id;
    int dx;
    int dy;
    int deterministic_score;
    int dice_score;
    int final_score;
    int favor_deterministic;
} BotActionCandidate;

static int manhattan_distance(int x0, int y0, int x1, int y1) {
    return abs(x0 - x1) + abs(y0 - y1);
}

static int estimate_bomb_hazard(const GameState *state, int x, int y) {
    int hazard = 0;
    int i;
    for (i = 0; i < MAX_BOMBS; ++i) {
        const Bomb *bomb = &state->arena.bombs[i];
        int step;
        int blocked = 0;
        if (!bomb->active) {
            continue;
        }
        if (bomb->x != x && bomb->y != y) {
            continue;
        }
        if (manhattan_distance(bomb->x, bomb->y, x, y) > bomb->power + 1) {
            continue;
        }
        if (bomb->x == x) {
            int direction = (y > bomb->y) ? 1 : -1;
            for (step = bomb->y + direction; step != y; step += direction) {
                if (*arena_tile((Arena *)&state->arena, x, step) == TILE_WALL) {
                    blocked = 1;
                    break;
                }
            }
        } else {
            int direction = (x > bomb->x) ? 1 : -1;
            for (step = bomb->x + direction; step != x; step += direction) {
                if (*arena_tile((Arena *)&state->arena, step, y) == TILE_WALL) {
                    blocked = 1;
                    break;
                }
            }
        }
        if (!blocked) {
            hazard += 18 + bomb->power * 4 + (4 - bomb->timer) * 3;
        }
    }
    return hazard;
}

static int estimate_rival_pressure(const GameState *state, int player_id, int x, int y) {
    int pressure = 0;
    int i;
    for (i = 0; i < MAX_PLAYERS; ++i) {
        const Blastonid *other = &state->players[i].mon;
        int distance;
        if (i == player_id || !other->alive) {
            continue;
        }
        distance = manhattan_distance(x, y, other->x, other->y);
        if (distance <= 8) {
            pressure += clamp_int(10 - distance, 0, 10) * 3;
        }
    }
    return pressure;
}

static int choose_step_toward(const GameState *state, int player_id, int target_x, int target_y, int *out_dx, int *out_dy) {
    static const int fallback_moves[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    const Blastonid *mon = &state->players[player_id].mon;
    int primary_dx = 0;
    int primary_dy = 0;
    int secondary_dx = 0;
    int secondary_dy = 0;
    int i;

    if (target_x > mon->x) {
        primary_dx = 1;
    } else if (target_x < mon->x) {
        primary_dx = -1;
    }
    if (target_y > mon->y) {
        secondary_dy = 1;
    } else if (target_y < mon->y) {
        secondary_dy = -1;
    }
    if (abs(target_y - mon->y) > abs(target_x - mon->x)) {
        secondary_dx = primary_dx;
        primary_dx = 0;
        primary_dy = secondary_dy;
        secondary_dy = 0;
    } else {
        primary_dy = 0;
        secondary_dx = 0;
    }

    if ((primary_dx != 0 || primary_dy != 0) && !tile_blocks(&state->arena, mon->x + primary_dx, mon->y + primary_dy) && blastmonidz_player_at(state, mon->x + primary_dx, mon->y + primary_dy) < 0) {
        *out_dx = primary_dx;
        *out_dy = primary_dy;
        return 1;
    }
    if ((secondary_dx != 0 || secondary_dy != 0) && !tile_blocks(&state->arena, mon->x + secondary_dx, mon->y + secondary_dy) && blastmonidz_player_at(state, mon->x + secondary_dx, mon->y + secondary_dy) < 0) {
        *out_dx = secondary_dx;
        *out_dy = secondary_dy;
        return 1;
    }
    for (i = 0; i < 4; ++i) {
        int dx = fallback_moves[i][0];
        int dy = fallback_moves[i][1];
        if (!tile_blocks(&state->arena, mon->x + dx, mon->y + dy) && blastmonidz_player_at(state, mon->x + dx, mon->y + dy) < 0) {
            *out_dx = dx;
            *out_dy = dy;
            return 1;
        }
    }
    return 0;
}

static int choose_nearest_gem(const GameState *state, int player_id, int *target_x, int *target_y) {
    const Blastonid *mon = &state->players[player_id].mon;
    int best_distance = 9999;
    int best_id = -1;
    int i;
    for (i = 0; i < MAX_GEMS; ++i) {
        const BombGem *gem = &state->arena.gems[i];
        int distance;
        if (!gem->active) {
            continue;
        }
        distance = manhattan_distance(mon->x, mon->y, gem->x, gem->y);
        if (distance < best_distance) {
            best_distance = distance;
            best_id = i;
        }
    }
    if (best_id < 0) {
        return 0;
    }
    *target_x = state->arena.gems[best_id].x;
    *target_y = state->arena.gems[best_id].y;
    return 1;
}

static int choose_rival_target(const GameState *state, int player_id, int *target_id) {
    const Blastonid *mon = &state->players[player_id].mon;
    int best_score = -9999;
    int best_id = -1;
    int i;
    for (i = 0; i < MAX_PLAYERS; ++i) {
        const Blastonid *other = &state->players[i].mon;
        int distance;
        int score;
        if (i == player_id || !other->alive) {
            continue;
        }
        distance = manhattan_distance(mon->x, mon->y, other->x, other->y);
        score = (other->max_health - other->health) + other->delay_ticks * 2 + other->gems_cleared * 3 - distance * 2;
        if (score > best_score) {
            best_score = score;
            best_id = i;
        }
    }
    if (best_id < 0) {
        return 0;
    }
    *target_id = best_id;
    return 1;
}

static int choose_safest_step(const GameState *state, int player_id, int *out_dx, int *out_dy) {
    static const int options[5][2] = {{0, 0}, {1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    const Blastonid *mon = &state->players[player_id].mon;
    int best_score = -9999;
    int best_index = -1;
    int i;
    for (i = 0; i < 5; ++i) {
        int dx = options[i][0];
        int dy = options[i][1];
        int x = mon->x + dx;
        int y = mon->y + dy;
        int score;
        if (i != 0 && (tile_blocks(&state->arena, x, y) || blastmonidz_player_at(state, x, y) >= 0)) {
            continue;
        }
        score = 120 - estimate_bomb_hazard(state, x, y) - estimate_rival_pressure(state, player_id, x, y);
        if (score > best_score) {
            best_score = score;
            best_index = i;
        }
    }
    if (best_index < 0) {
        return 0;
    }
    *out_dx = options[best_index][0];
    *out_dy = options[best_index][1];
    return 1;
}

static int count_gems_near(const GameState *state, int x, int y, int radius) {
    int i;
    int count = 0;
    for (i = 0; i < MAX_GEMS; ++i) {
        const BombGem *gem = &state->arena.gems[i];
        if (!gem->active) {
            continue;
        }
        if (manhattan_distance(x, y, gem->x, gem->y) <= radius) {
            ++count;
        }
    }
    return count;
}

static int score_doctrine_destination(const GameState *state, int player_id, int x, int y) {
    const BlastKin *player = &state->players[player_id];
    const BlastmonidzHomeTile *home_tile = blastmonidz_select_home_tile(state, x, y);
    int center_x = state->arena.width / 2;
    int center_y = state->arena.height / 2;
    int centrality = 24 - manhattan_distance(x, y, center_x, center_y) / 3;
    int hazard = estimate_bomb_hazard(state, x, y);
    int pressure = estimate_rival_pressure(state, player_id, x, y);
    int nearby_gems = count_gems_near(state, x, y, 8);
    int shelter = home_tile ? tile_bonus(home_tile->shelter_bias, 12) : 0;
    int structure = home_tile ? tile_bonus(home_tile->structural_bias, 12) : 0;
    int growth = home_tile ? tile_bonus(home_tile->growth_bias, 12) : 0;
    int ornament = home_tile ? tile_bonus(home_tile->ornamental_bias, 12) : 0;

    switch (player->doctrine) {
        case BLASTMONIDZ_DOCTRINE_HARMONIZER:
            return shelter + structure + state->world_feed.balance / 5 - hazard / 8 - pressure / 8;
        case BLASTMONIDZ_DOCTRINE_STEWARD:
            return nearby_gems * 8 + growth + structure + state->arena.mineral_pressure / 5 - hazard / 10;
        case BLASTMONIDZ_DOCTRINE_MEDIATOR: {
            int contest_band = 24 - abs(pressure - 18);
            return centrality + contest_band + ornament - hazard / 9;
        }
        case BLASTMONIDZ_DOCTRINE_KINWEAVER:
            return centrality + growth + ornament + state->world_feed.world_signal / 6 - pressure / 10;
        default:
            return 0;
    }
}

static const char *bot_action_name(int action_type) {
    switch (action_type) {
        case BOT_ACTION_MOVE_GEM:
            return "gather";
        case BOT_ACTION_MOVE_RIVAL:
            return "mediate";
        case BOT_ACTION_MOVE_SAFETY:
            return "stabilize";
        case BOT_ACTION_PLACE_BOMB:
            return "detonate";
        case BOT_ACTION_CYCLE_CONCOCTION:
            return "realign";
        case BOT_ACTION_WAIT:
        default:
            return "wait";
    }
}

static int current_concoction_alignment(const GameState *state, const Blastonid *mon) {
    int dominant = 0;
    int i;
    for (i = 1; i < 3; ++i) {
        if (state->arena.chemistry[i] > state->arena.chemistry[dominant]) {
            dominant = i;
        }
    }
    if ((mon->concoction_id % 3) == dominant) {
        return 18;
    }
    return 4;
}

static int derive_social_doctrine(const GameState *state, int player_id) {
    const BlastKin *player = &state->players[player_id];
    const Blastonid *mon = &player->mon;
    int health_ratio = (mon->health * 100) / (mon->max_health > 0 ? mon->max_health : 1);
    int hazard = estimate_bomb_hazard(state, mon->x, mon->y);
    int pressure = estimate_rival_pressure(state, player_id, mon->x, mon->y);
    int alignment_gap = 24 - current_concoction_alignment(state, mon);

    if (hazard > 24 || health_ratio < 42) {
        return BLASTMONIDZ_DOCTRINE_HARMONIZER;
    }
    if (state->arena.mineral_pressure > 22 || blastmonidz_count_active_gems(&state->arena) > 18) {
        return BLASTMONIDZ_DOCTRINE_STEWARD;
    }
    if (pressure > 16 || state->world_feed.rival_signal > 52 || alignment_gap > 12) {
        return BLASTMONIDZ_DOCTRINE_MEDIATOR;
    }
    return BLASTMONIDZ_DOCTRINE_KINWEAVER;
}

static void refresh_artisapien_doctrine(GameState *state, int player_id) {
    BlastKin *player;
    int next_doctrine;
    char message[MAX_LOG_LEN];

    if (!state || player_id < 0 || player_id >= MAX_PLAYERS) {
        return;
    }
    player = &state->players[player_id];
    if (!player->artisapien) {
        return;
    }
    next_doctrine = derive_social_doctrine(state, player_id);
    if (player->doctrine == next_doctrine) {
        return;
    }
    player->doctrine = next_doctrine;
    snprintf(player->ai_debug_line, sizeof(player->ai_debug_line), "reframed %s", blastmonidz_doctrine_name(player->doctrine));
    snprintf(message, sizeof(message), "%s reframes as %s.", player->name, blastmonidz_doctrine_name(player->doctrine));
    blastmonidz_push_log(state, message);
}

static void apply_doctrine_social_effects(GameState *state, int player_id) {
    BlastKin *player;
    Blastonid *mon;
    if (!state || player_id < 0 || player_id >= MAX_PLAYERS) {
        return;
    }
    player = &state->players[player_id];
    mon = &player->mon;
    if (!player->artisapien || !mon->alive) {
        return;
    }
    switch (player->doctrine) {
        case BLASTMONIDZ_DOCTRINE_HARMONIZER:
            tune_self_feed(mon, 1, 2, -2, -1);
            state->world_feed.world_signal = clamp_int(state->world_feed.world_signal + 1, 0, 100);
            state->world_feed.rival_signal = clamp_int(state->world_feed.rival_signal - 1, 0, 100);
            break;
        case BLASTMONIDZ_DOCTRINE_STEWARD:
            tune_self_feed(mon, 1, 2, -1, 0);
            state->arena.mineral_pressure = clamp_int(state->arena.mineral_pressure + 1, 0, 999);
            state->arena.chemistry[mon->concoction_id % 3] = clamp_int(state->arena.chemistry[mon->concoction_id % 3] + 1, 0, 999);
            break;
        case BLASTMONIDZ_DOCTRINE_MEDIATOR:
            tune_self_feed(mon, 0, 1, -3, -1);
            state->world_feed.rival_signal = clamp_int(state->world_feed.rival_signal - 2, 0, 100);
            state->world_feed.balance = clamp_int(state->world_feed.balance + 1, 0, 100);
            break;
        case BLASTMONIDZ_DOCTRINE_KINWEAVER:
            tune_self_feed(mon, 2, 2, -1, -1);
            state->world_feed.inner_signal = clamp_int(state->world_feed.inner_signal + 1, 0, 100);
            state->world_feed.world_signal = clamp_int(state->world_feed.world_signal + 1, 0, 100);
            break;
        default:
            break;
    }
}

static int doctrine_social_bias(const GameState *state, int player_id, const BotActionCandidate *candidate) {
    const BlastKin *player = &state->players[player_id];
    const Blastonid *mon = &player->mon;
    int alignment = current_concoction_alignment(state, mon);
    int low_health = ((mon->health * 100) / (mon->max_health > 0 ? mon->max_health : 1)) < 45;
    switch (player->doctrine) {
        case BLASTMONIDZ_DOCTRINE_HARMONIZER:
            switch (candidate->action_type) {
                case BOT_ACTION_MOVE_SAFETY: return 24 + state->world_feed.balance / 6;
                case BOT_ACTION_CYCLE_CONCOCTION: return 22 + (24 - alignment);
                case BOT_ACTION_MOVE_GEM: return 16 + state->world_feed.world_signal / 8;
                case BOT_ACTION_PLACE_BOMB: return low_health ? -28 : -14;
                case BOT_ACTION_MOVE_RIVAL: return -10;
                default: return 14;
            }
        case BLASTMONIDZ_DOCTRINE_STEWARD:
            switch (candidate->action_type) {
                case BOT_ACTION_MOVE_GEM: return 28 + state->arena.mineral_pressure / 6;
                case BOT_ACTION_MOVE_SAFETY: return 20;
                case BOT_ACTION_CYCLE_CONCOCTION: return 16 + (24 - alignment) / 2;
                case BOT_ACTION_PLACE_BOMB: return -12;
                case BOT_ACTION_MOVE_RIVAL: return -6;
                default: return 10;
            }
        case BLASTMONIDZ_DOCTRINE_MEDIATOR:
            switch (candidate->action_type) {
                case BOT_ACTION_MOVE_RIVAL: return 14 + state->world_feed.rival_signal / 10;
                case BOT_ACTION_CYCLE_CONCOCTION: return 18 + (24 - alignment);
                case BOT_ACTION_MOVE_SAFETY: return 18;
                case BOT_ACTION_PLACE_BOMB: return low_health ? -30 : -18;
                case BOT_ACTION_MOVE_GEM: return 12;
                default: return 11;
            }
        case BLASTMONIDZ_DOCTRINE_KINWEAVER:
            switch (candidate->action_type) {
                case BOT_ACTION_MOVE_GEM: return 18 + state->world_feed.world_signal / 7;
                case BOT_ACTION_MOVE_SAFETY: return 22 + state->world_feed.balance / 7;
                case BOT_ACTION_CYCLE_CONCOCTION: return 20 + (24 - alignment);
                case BOT_ACTION_PLACE_BOMB: return -16;
                case BOT_ACTION_MOVE_RIVAL: return -4;
                default: return 16;
            }
        default:
            return 0;
    }
}

static int deterministic_profile_factor(const GameState *state, int player_id, const BotActionCandidate *candidate) {
    const Blastonid *mon = &state->players[player_id].mon;
    const BlastmonidzGenomeProfile *profile = &mon->cosmetic_genome;
    const BlastmonidzHomeTile *home_tile = player_home_tile(state, player_id);
    int hazard_here = estimate_bomb_hazard(state, mon->x, mon->y);
    int pressure_here = estimate_rival_pressure(state, player_id, mon->x, mon->y);
    int health_ratio = (mon->health * 100) / (mon->max_health > 0 ? mon->max_health : 1);
    int score = 0;

    score += genome_bonus(profile->mutation_factor, 18);
    score += genome_bonus(profile->animation_factor, 12);
    score += genome_bonus(profile->depth_factor, 10);
    score += mon->growth_stage * 6;
    score += mon->gems_cleared * 2;
    score += state->players[player_id].profile_rank;
    if (home_tile) {
        score += tile_bonus(home_tile->growth_bias, 8);
        score += tile_bonus(home_tile->structural_bias, 6);
    }

    switch (candidate->action_type) {
        case BOT_ACTION_MOVE_GEM:
            score += 26 + (100 - health_ratio) / 8;
            score += 28 - estimate_bomb_hazard(state, mon->x + candidate->dx, mon->y + candidate->dy) / 8;
            score += score_doctrine_destination(state, player_id, mon->x + candidate->dx, mon->y + candidate->dy);
            break;
        case BOT_ACTION_MOVE_RIVAL:
            score += 18 + genome_bonus(profile->mutation_factor, 16) + pressure_here / 6;
            score -= hazard_here / 7;
            score += score_doctrine_destination(state, player_id, mon->x + candidate->dx, mon->y + candidate->dy);
            break;
        case BOT_ACTION_MOVE_SAFETY:
            score += 20 + hazard_here / 4 + pressure_here / 5;
            score += genome_bonus(profile->structural_factor, 16);
            score += (100 - health_ratio) / 3;
            score += score_doctrine_destination(state, player_id, mon->x + candidate->dx, mon->y + candidate->dy);
            break;
        case BOT_ACTION_PLACE_BOMB:
            score += 12 + genome_bonus(profile->shading_factor, 10) + genome_bonus(profile->depth_factor, 12);
            score += pressure_here / 5;
            score -= hazard_here / 8;
            score -= score_doctrine_destination(state, player_id, mon->x, mon->y) / 4;
            if (mon->bomb_cooldown > 0) {
                score -= 40;
            }
            break;
        case BOT_ACTION_CYCLE_CONCOCTION:
            score += 10 + genome_bonus(profile->cosmetic_factor, 8);
            score += 24 - current_concoction_alignment(state, mon);
            break;
        case BOT_ACTION_WAIT:
        default:
            score += 6 + genome_bonus(profile->structural_factor, 8);
            score -= pressure_here / 8;
            break;
    }

    score += doctrine_social_bias(state, player_id, candidate);

    return score;
}

static int weighted_die_roll(const GameState *state, int player_id, int sides, float genome_factor, int salt) {
    const Blastonid *mon = &state->players[player_id].mon;
    int expectation = 1 + (int)(genome_factor * (float)(sides - 1) + 0.5f);
    int roll = rng_range(1, sides);
    int drift = (state->consensus_tick + mon->genome[salt % 6] + salt * 7 + mon->self_feed.balance) % sides;
    int weighted = (roll + expectation * 2 + drift + 1) / 4;
    return clamp_int(weighted, 1, sides);
}

static int genome_dice_profile_score(const GameState *state, int player_id, const BotActionCandidate *candidate) {
    const Blastonid *mon = &state->players[player_id].mon;
    const BlastmonidzGenomeProfile *profile = &mon->cosmetic_genome;
    float action_factor = 0.4f;
    int d4;
    int d8;
    int d32;

    switch (candidate->action_type) {
        case BOT_ACTION_MOVE_GEM:
            action_factor = (profile->cosmetic_factor + profile->mutation_factor + profile->animation_factor) / 3.0f;
            break;
        case BOT_ACTION_MOVE_RIVAL:
            action_factor = (profile->mutation_factor + profile->depth_factor + profile->silhouette_factor) / 3.0f;
            break;
        case BOT_ACTION_MOVE_SAFETY:
            action_factor = (profile->structural_factor + profile->depth_factor) / 2.0f;
            break;
        case BOT_ACTION_PLACE_BOMB:
            action_factor = (profile->mutation_factor + profile->shading_factor + profile->depth_factor) / 3.0f;
            break;
        case BOT_ACTION_CYCLE_CONCOCTION:
            action_factor = (profile->shading_factor + profile->cosmetic_factor) / 2.0f;
            break;
        default:
            action_factor = (profile->structural_factor + profile->animation_factor) / 2.0f;
            break;
    }

    d4 = weighted_die_roll(state, player_id, 4, action_factor, candidate->action_type + 1);
    d8 = weighted_die_roll(state, player_id, 8, (action_factor + profile->animation_factor) * 0.5f, candidate->action_type + 3);
    d32 = weighted_die_roll(state, player_id, 32, (action_factor + profile->mutation_factor) * 0.5f, candidate->action_type + 5);
    return d32 + d8 * 2 + d4 * 3;
}

static void godai_deliberation(const GameState *state, int player_id, const BotActionCandidate *candidate, int *favor_deterministic, int *deterministic_score, int *dice_score) {
    const BlastKin *player = &state->players[player_id];
    const Blastonid *mon = &player->mon;
    const BlastmonidzGenomeProfile *profile = &mon->cosmetic_genome;
    int health_ratio = (mon->health * 100) / (mon->max_health > 0 ? mon->max_health : 1);
    int earth = genome_bonus(profile->structural_factor, 32) + health_ratio / 4;
    int water = genome_bonus(profile->depth_factor, 18) + state->world_feed.world_signal / 5 + mon->gems_cleared * 3;
    int fire = genome_bonus(profile->mutation_factor, 24) + state->world_feed.rival_signal / 4 + mon->round_kills * 5;
    int wind = genome_bonus(profile->animation_factor, 20) + genome_bonus(profile->silhouette_factor, 12);
    int void_score = genome_bonus(profile->cosmetic_factor, 14) + genome_bonus(state->visuals.asset_genome.mutation_factor, 10) + (state->consensus_tick % 17);
    int historical_realism = mon->growth_stage * 8 + state->players[player_id].run_wins * 10 + current_concoction_alignment(state, mon);
    int pro_deterministic = earth + water + void_score + historical_realism + doctrine_social_bias(state, player_id, candidate);
    int con_deterministic = fire / 2 + wind / 3;
    int uncertainty = estimate_bomb_hazard(state, mon->x, mon->y) / 4 + estimate_rival_pressure(state, player_id, mon->x, mon->y) / 5;
    int pro_dice = fire + wind + uncertainty;
    int con_dice = earth / 2 + historical_realism / 2;

    if (player->artisapien) {
        switch (player->doctrine) {
            case BLASTMONIDZ_DOCTRINE_HARMONIZER:
                pro_deterministic += 18;
                con_dice += 10;
                break;
            case BLASTMONIDZ_DOCTRINE_STEWARD:
                pro_deterministic += 14;
                con_dice += 8;
                break;
            case BLASTMONIDZ_DOCTRINE_MEDIATOR:
                pro_deterministic += 12;
                con_dice += 6;
                break;
            case BLASTMONIDZ_DOCTRINE_KINWEAVER:
                pro_deterministic += 16;
                con_dice += 7;
                break;
            default:
                break;
        }
        if (candidate->action_type == BOT_ACTION_PLACE_BOMB) {
            con_dice += 12;
        }
    }

    *deterministic_score = pro_deterministic - con_deterministic;
    *dice_score = pro_dice - con_dice;
    *favor_deterministic = (*deterministic_score >= *dice_score) ? 1 : 0;

    if (candidate->action_type == BOT_ACTION_MOVE_SAFETY || candidate->action_type == BOT_ACTION_WAIT) {
        *favor_deterministic = 1;
    } else if (candidate->action_type == BOT_ACTION_PLACE_BOMB && fire > earth) {
        *favor_deterministic = 0;
    }
}

static int integrate_zero_divergence(int favored_score, int alternate_score, int adaptability) {
    int picostep_categories[4];
    int integration = favored_score;
    int divergence = alternate_score - favored_score;
    int step;

    picostep_categories[0] = adaptability / 4;
    picostep_categories[1] = adaptability / 5;
    picostep_categories[2] = adaptability / 6;
    picostep_categories[3] = adaptability / 7;

    for (step = 0; step < 4; ++step) {
        int remaining = 4 - step;
        int pico = picostep_categories[step];
        int alignment = divergence / remaining;
        if (alignment == 0 && divergence != 0) {
            alignment = (divergence > 0) ? 1 : -1;
        }
        integration += alignment;
        divergence -= alignment;
        if (pico > 0) {
            integration += pico / remaining;
        }
    }

    integration += divergence;
    divergence = 0;
    return integration + divergence;
}

static int score_bot_action(const GameState *state, int player_id, BotActionCandidate *candidate) {
    int deliberation_det;
    int deliberation_dice;
    int adaptability;
    int favored_score;
    int alternate_score;

    candidate->deterministic_score = deterministic_profile_factor(state, player_id, candidate);
    candidate->dice_score = genome_dice_profile_score(state, player_id, candidate);
    godai_deliberation(state, player_id, candidate, &candidate->favor_deterministic, &deliberation_det, &deliberation_dice);
    adaptability = clamp_int((state->world_feed.balance + state->arena.mineral_pressure + state->players[player_id].profile_rank * 3) / 3, 0, 96);
    if (candidate->favor_deterministic) {
        favored_score = candidate->deterministic_score + deliberation_det;
        alternate_score = candidate->dice_score + deliberation_dice;
    } else {
        favored_score = candidate->dice_score + deliberation_dice;
        alternate_score = candidate->deterministic_score + deliberation_det;
    }
    candidate->final_score = integrate_zero_divergence(favored_score, alternate_score, adaptability);
    return candidate->final_score;
}

static void choose_bot_action(GameState *state, int player_id) {
    Blastonid *mon = &state->players[player_id].mon;
    BlastKin *player = &state->players[player_id];
    BotActionCandidate candidates[6];
    int candidate_count = 0;
    int best_index = -1;
    int best_score = -999999;
    int target_x;
    int target_y;
    int target_id;
    int dx;
    int dy;
    int i;

    if (!mon->alive) {
        try_respawn_player(state, player_id, 0);
        return;
    }
    if (mon->delay_ticks > 0) {
        return;
    }

    refresh_artisapien_doctrine(state, player_id);

    candidates[candidate_count++] = (BotActionCandidate){BOT_ACTION_WAIT, -1, 0, 0, 0, 0, 0, 1};

    if (choose_nearest_gem(state, player_id, &target_x, &target_y) && choose_step_toward(state, player_id, target_x, target_y, &dx, &dy)) {
        candidates[candidate_count++] = (BotActionCandidate){BOT_ACTION_MOVE_GEM, -1, dx, dy, 0, 0, 0, 1};
    }
    if (choose_rival_target(state, player_id, &target_id) && choose_step_toward(state, player_id, state->players[target_id].mon.x, state->players[target_id].mon.y, &dx, &dy)) {
        candidates[candidate_count++] = (BotActionCandidate){BOT_ACTION_MOVE_RIVAL, target_id, dx, dy, 0, 0, 0, 0};
    }
    if (choose_safest_step(state, player_id, &dx, &dy)) {
        candidates[candidate_count++] = (BotActionCandidate){BOT_ACTION_MOVE_SAFETY, -1, dx, dy, 0, 0, 0, 1};
    }
    if (mon->bomb_cooldown <= 0 && blastmonidz_bomb_at(&state->arena, mon->x, mon->y) < 0) {
        candidates[candidate_count++] = (BotActionCandidate){BOT_ACTION_PLACE_BOMB, -1, 0, 0, 0, 0, 0, 0};
    }
    candidates[candidate_count++] = (BotActionCandidate){BOT_ACTION_CYCLE_CONCOCTION, -1, 0, 0, 0, 0, 0, 1};

    for (i = 0; i < candidate_count; ++i) {
        int score = score_bot_action(state, player_id, &candidates[i]);
        if (score > best_score) {
            best_score = score;
            best_index = i;
        }
    }

    if (best_index < 0) {
        return;
    }

    snprintf(player->ai_debug_line, sizeof(player->ai_debug_line), "%s | %s | det %d dice %d final %d",
        blastmonidz_doctrine_name(player->doctrine),
        bot_action_name(candidates[best_index].action_type),
        candidates[best_index].deterministic_score,
        candidates[best_index].dice_score,
        candidates[best_index].final_score);

    switch (candidates[best_index].action_type) {
        case BOT_ACTION_MOVE_GEM:
        case BOT_ACTION_MOVE_RIVAL:
        case BOT_ACTION_MOVE_SAFETY:
            if (candidates[best_index].dx != 0 || candidates[best_index].dy != 0) {
                if (player->artisapien && candidates[best_index].action_type != BOT_ACTION_MOVE_RIVAL) {
                    char message[MAX_LOG_LEN];
                    snprintf(message, sizeof(message), "%s %s via %s %s-led profile.",
                        player->name,
                        bot_action_name(candidates[best_index].action_type),
                        blastmonidz_doctrine_name(player->doctrine),
                        candidates[best_index].favor_deterministic ? "deterministic" : "dice");
                    blastmonidz_push_log(state, message);
                }
                move_player(state, player_id, candidates[best_index].dx, candidates[best_index].dy);
            }
            break;
        case BOT_ACTION_PLACE_BOMB:
            if (player->artisapien) {
                char message[MAX_LOG_LEN];
                snprintf(message, sizeof(message), "%s detonate check via %s %s-led profile.",
                    player->name,
                    blastmonidz_doctrine_name(player->doctrine),
                    candidates[best_index].favor_deterministic ? "deterministic" : "dice");
                blastmonidz_push_log(state, message);
            }
            place_bomb(state, player_id);
            break;
        case BOT_ACTION_CYCLE_CONCOCTION:
            cycle_concoction(mon);
            if (player->artisapien) {
                char message[MAX_LOG_LEN];
                snprintf(message, sizeof(message), "%s realigns chemistry through %s.", player->name, blastmonidz_doctrine_name(player->doctrine));
                blastmonidz_push_log(state, message);
            }
            break;
        case BOT_ACTION_WAIT:
        default:
            tune_self_feed(mon, 0, 1, -1, 0);
            break;
    }
}

void blastmonidz_push_log(GameState *state, const char *message) {
    int i;
    for (i = MAX_LOG_LINES - 1; i > 0; --i) {
        memcpy(state->log_lines[i], state->log_lines[i - 1], MAX_LOG_LEN);
    }
    snprintf(state->log_lines[0], MAX_LOG_LEN, "%s", message);
}

void blastmonidz_load_archive_notice(GameState *state) {
    char message[MAX_LOG_LEN];
    snprintf(message, sizeof(message), "Archive engine online: %s theme, %s phase, seed %08X.",
        blastmonidz_visual_theme_name(state),
        blastmonidz_world_phase_name(state),
        state->visuals.run_seed);
    blastmonidz_push_log(state, message);
}

void blastmonidz_init_arena(Arena *arena) {
    int x;
    int y;
    int i;
    arena->width = ARENA_W;
    arena->height = ARENA_H;
    arena->tiles = (unsigned char *)calloc((size_t)arena->width * (size_t)arena->height, sizeof(unsigned char));
    if (!arena->tiles) {
        fprintf(stderr, "Failed to allocate arena tiles.\n");
        exit(1);
    }
    arena->chemistry[0] = 24;
    arena->chemistry[1] = 18;
    arena->chemistry[2] = 14;
    arena->mineral_pressure = 20;
    arena->last_explosion_owner = -1;
    arena->last_explosion_kills = 0;
    arena->last_explosion_gems = 0;

    for (y = 0; y < arena->height; ++y) {
        for (x = 0; x < arena->width; ++x) {
            unsigned char tile = TILE_EMPTY;
            if (x == 0 || y == 0 || x == arena->width - 1 || y == arena->height - 1) {
                tile = TILE_WALL;
            } else if ((x % 9 == 0 && y % 6 == 0) || (rng_range(0, 100) < 8 && x > 4 && y > 4)) {
                tile = TILE_CRATE;
            }
            *arena_tile(arena, x, y) = tile;
        }
    }

    for (i = 0; i < MAX_GEMS; ++i) {
        BombGem *gem = &arena->gems[i];
        gem->active = 1;
        gem->x = rng_range(2, arena->width - 3);
        gem->y = rng_range(2, arena->height - 3);
        gem->class_id = rng_range(0, 197);
        gem->tier = rng_range(0, 12);
        gem->frequency = rng_range(20, 60);
        gem->stability = rng_range(14, 40);
        gem->glyph = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789*+"[(gem->class_id + gem->tier) % 38];
    }
    for (i = 0; i < MAX_BOMBS; ++i) {
        arena->bombs[i].active = 0;
    }
}

void blastmonidz_free_arena(Arena *arena) {
    if (arena->tiles) {
        free(arena->tiles);
        arena->tiles = NULL;
    }
}

void blastmonidz_setup_players(GameState *state) {
    const int spawn_x[MAX_PLAYERS] = {4, ARENA_W - 5, 4, ARENA_W - 5};
    const int spawn_y[MAX_PLAYERS] = {4, 4, ARENA_H - 5, ARENA_H - 5};
    int picks[MAX_PLAYERS] = {0, 1, 2, 3};
    int i;
    for (i = MAX_PLAYERS - 1; i > 0; --i) {
        int j = rng_range(0, i);
        int temp = picks[i];
        picks[i] = picks[j];
        picks[j] = temp;
    }
    seed_player(&state->players[0], "Player BlastKin", 1, 0, BLASTMONIDZ_DOCTRINE_HARMONIZER, &blastmonidz_starter_seeds[picks[0]], spawn_x[0], spawn_y[0]);
    seed_player(&state->players[1], "ArtiSapien Kestrel", 0, 1, BLASTMONIDZ_DOCTRINE_HARMONIZER, &blastmonidz_starter_seeds[picks[1]], spawn_x[1], spawn_y[1]);
    seed_player(&state->players[2], "ArtiSapien Morrow", 0, 1, BLASTMONIDZ_DOCTRINE_STEWARD, &blastmonidz_starter_seeds[picks[2]], spawn_x[2], spawn_y[2]);
    seed_player(&state->players[3], "ArtiSapien Vanta", 0, 1, BLASTMONIDZ_DOCTRINE_KINWEAVER, &blastmonidz_starter_seeds[picks[3]], spawn_x[3], spawn_y[3]);
}

void blastmonidz_init_game(GameState *state) {
    memset(state, 0, sizeof(*state));
    state->round_index = 1;
    state->optical_buffer = 10;
    state->running = 1;
    blastmonidz_setup_players(state);
    blastmonidz_configure_visual_profile(state);
    blastmonidz_init_arena(&state->arena);
    blastmonidz_refresh_all_genomes(state);
    refresh_world_feed(state);
    blastmonidz_load_archive_notice(state);
}

void blastmonidz_begin_round(GameState *state) {
    int i;
    blastmonidz_free_arena(&state->arena);
    blastmonidz_init_arena(&state->arena);
    for (i = 0; i < MAX_PLAYERS; ++i) {
        Blastonid *mon = &state->players[i].mon;
        mon->x = (i % 2 == 0) ? 4 : ARENA_W - 5;
        mon->y = (i < 2) ? 4 : ARENA_H - 5;
        mon->health = mon->max_health;
        mon->alive = 1;
        mon->delay_ticks = 0;
        mon->ghost_timer = 0;
        mon->round_kills = 0;
        mon->gems_cleared = 0;
        mon->precision_chain = 0;
        mon->bomb_cooldown = 0;
        tune_self_feed(mon, 2, 2, -2, -3);
    }
    state->turns_this_round = 0;
    blastmonidz_configure_visual_profile(state);
    blastmonidz_refresh_all_genomes(state);
    refresh_world_feed(state);
    blastmonidz_load_archive_notice(state);
}

int blastmonidz_count_active_gems(const Arena *arena) {
    int i;
    int count = 0;
    for (i = 0; i < MAX_GEMS; ++i) {
        if (arena->gems[i].active) {
            ++count;
        }
    }
    return count;
}

int blastmonidz_gem_at(const Arena *arena, int x, int y) {
    int i;
    for (i = 0; i < MAX_GEMS; ++i) {
        if (arena->gems[i].active && arena->gems[i].x == x && arena->gems[i].y == y) {
            return i;
        }
    }
    return -1;
}

int blastmonidz_bomb_at(const Arena *arena, int x, int y) {
    int i;
    for (i = 0; i < MAX_BOMBS; ++i) {
        if (arena->bombs[i].active && arena->bombs[i].x == x && arena->bombs[i].y == y) {
            return i;
        }
    }
    return -1;
}

int blastmonidz_player_at(const GameState *state, int x, int y) {
    int i;
    for (i = 0; i < MAX_PLAYERS; ++i) {
        if (state->players[i].mon.alive && state->players[i].mon.x == x && state->players[i].mon.y == y) {
            return i;
        }
    }
    return -1;
}

ArenaView blastmonidz_calculate_view(const GameState *state) {
    ArenaView view;
    int focus_x = state->players[0].mon.x;
    int focus_y = state->players[0].mon.y;
    int tension = 0;
    int zoom = 0;
    int half_w;
    int half_h;
    int i;
    for (i = 0; i < MAX_PLAYERS; ++i) {
        tension += state->players[i].mon.delay_ticks + (state->players[i].mon.max_health - state->players[i].mon.health) / 6;
    }
    zoom = clamp_int(tension / 8, 0, 4);
    half_w = clamp_int(VIEWPORT_W / 2 - zoom, 5, VIEWPORT_W / 2);
    half_h = clamp_int(VIEWPORT_H / 2 - zoom / 2, 4, VIEWPORT_H / 2);
    view.left = clamp_int(focus_x - half_w, 0, state->arena.width - (half_w * 2));
    view.top = clamp_int(focus_y - half_h, 0, state->arena.height - (half_h * 2));
    view.width = half_w * 2;
    view.height = half_h * 2;
    return view;
}

int blastmonidz_handle_player_command(GameState *state, int player_id, char command) {
    Blastonid *mon = &state->players[player_id].mon;
    switch ((char)tolower((unsigned char)command)) {
        case 'w': move_player(state, player_id, 0, -1); break;
        case 's': move_player(state, player_id, 0, 1); break;
        case 'a': move_player(state, player_id, -1, 0); break;
        case 'd': move_player(state, player_id, 1, 0); break;
        case 'b': place_bomb(state, player_id); break;
        case 'c': cycle_concoction(mon); blastmonidz_push_log(state, "Concoction cycled for the player BlastKin."); break;
        case 'r': try_respawn_player(state, player_id, 1); break;
        case 'q': return 0;
        default: break;
    }
    return 1;
}

void blastmonidz_run_bot_turns(GameState *state) {
    int i;
    for (i = 1; i < MAX_PLAYERS; ++i) {
        choose_bot_action(state, i);
    }
}

void blastmonidz_advance_world(GameState *state) {
    int i;
    tick_bombs(state);
    emit_metabolic_chemistry(state);
    tick_ghosts(state);
    tick_cooldowns(state);
    maybe_spawn_new_gem(state);
    for (i = 0; i < MAX_PLAYERS; ++i) {
        evolve_player(state, i);
    }
    ++state->consensus_tick;
    ++state->turns_this_round;
    blastmonidz_refresh_asset_genome(state);
    refresh_world_feed(state);
}

int blastmonidz_determine_round_winner(GameState *state) {
    int i;
    int alive_count = 0;
    int alive_id = -1;
    for (i = 0; i < MAX_PLAYERS; ++i) {
        if (state->players[i].mon.alive) {
            alive_id = i;
            ++alive_count;
        }
    }
    if (alive_count == 1 && blastmonidz_count_active_gems(&state->arena) == 0 && state->arena.last_explosion_owner == alive_id) {
        return alive_id;
    }
    if (state->turns_this_round >= MAX_TURNS_PER_ROUND || alive_count <= 1) {
        int best_score = -9999;
        int best_id = 0;
        for (i = 0; i < MAX_PLAYERS; ++i) {
            int score = state->players[i].mon.health + state->players[i].mon.gems_cleared * 8 + state->players[i].mon.round_kills * 25 + state->players[i].mon.growth_stage * 18;
            if (!state->players[i].mon.alive) {
                score -= 20;
            }
            if (score > best_score) {
                best_score = score;
                best_id = i;
            }
        }
        return best_id;
    }
    return -1;
}

void blastmonidz_announce_round_winner(GameState *state, int round_winner) {
    char message[MAX_LOG_LEN];
    ++state->players[round_winner].run_wins;
    snprintf(message, sizeof(message), "%s wins round %d.", state->players[round_winner].name, state->round_index);
    blastmonidz_push_log(state, message);
}

int blastmonidz_check_run_winner(const GameState *state) {
    int i;
    for (i = 0; i < MAX_PLAYERS; ++i) {
        if (state->players[i].run_wins >= TARGET_RUN_WINS) {
            return i;
        }
    }
    return -1;
}

void blastmonidz_save_run_profile(const GameState *state) {
    FILE *profile = fopen(blastmonidz_run_profile_path, "w");
    FILE *replay = fopen(blastmonidz_replay_summary_path, "w");
    int i;
    char genome_summary[256];
    if (profile) {
        blastmonidz_describe_genome_profile(&state->visuals.asset_genome, genome_summary, (int)sizeof(genome_summary));
        fprintf(profile, "BLASTMONIDZ RUN PROFILE\n");
        fprintf(profile, "winner=%s\n", state->players[state->winner_id].name);
        fprintf(profile, "rounds=%d\n", state->round_index);
        fprintf(profile, "consensus_tick=%d\n", state->consensus_tick);
        fprintf(profile, "visual_theme=%s\n", blastmonidz_visual_theme_name(state));
        fprintf(profile, "world_phase=%s\n", blastmonidz_world_phase_name(state));
        fprintf(profile, "visual_seed=%08X\n", state->visuals.run_seed);
        fprintf(profile, "asset_genome=%s\n", genome_summary);
        fprintf(profile, "world_feed=%d,%d,%d,%d,%d\n",
            state->world_feed.inner_signal,
            state->world_feed.world_signal,
            state->world_feed.rival_signal,
            state->world_feed.ghost_signal,
            state->world_feed.balance);
        for (i = 0; i < MAX_PLAYERS; ++i) {
            const BlastKin *player = &state->players[i];
            blastmonidz_describe_genome_profile(&player->mon.cosmetic_genome, genome_summary, (int)sizeof(genome_summary));
            fprintf(profile,
                "player=%s|wins=%d|starter=%s|form=%s|gems=%d|kills=%d|rank=%d|doctrine=%s|family=%d|stride=%d|feed=%d,%d,%d,%d,%d|ai=%s|genome=%s\n",
                player->name,
                player->run_wins,
                player->mon.starter->name,
                blastmonidz_growth_title(player->mon.growth_stage),
                player->mon.gems_cleared,
                player->mon.round_kills,
                player->profile_rank,
                blastmonidz_doctrine_name(player->doctrine),
                state->visuals.player_family[i],
                state->visuals.player_frame_stride[i],
                player->mon.self_feed.inner_signal,
                player->mon.self_feed.world_signal,
                player->mon.self_feed.rival_signal,
                player->mon.self_feed.ghost_signal,
                player->mon.self_feed.balance,
                player->ai_debug_line,
                genome_summary);
        }
        fclose(profile);
    }
    if (replay) {
        fprintf(replay, "Blastmonidz adaptive replay summary\n");
        fprintf(replay, "Future ArtiSapiens should mutate from these standings and chemistry totals.\n");
        fprintf(replay, "chemistry=%d,%d,%d\n", state->arena.chemistry[0], state->arena.chemistry[1], state->arena.chemistry[2]);
        fprintf(replay, "theme=%s\n", blastmonidz_visual_theme_name(state));
        fprintf(replay, "world_phase=%s\n", blastmonidz_world_phase_name(state));
        for (i = 0; i < MAX_PLAYERS; ++i) {
            blastmonidz_describe_genome_profile(&state->players[i].mon.cosmetic_genome, genome_summary, (int)sizeof(genome_summary));
            fprintf(replay, "%s -> doctrine=%s delay=%d form=%s alive=%d feed=%d,%d,%d,%d,%d ai=%s genome=%s\n",
                state->players[i].name,
                blastmonidz_doctrine_name(state->players[i].doctrine),
                state->players[i].mon.delay_ticks,
                blastmonidz_growth_title(state->players[i].mon.growth_stage),
                state->players[i].mon.alive,
                state->players[i].mon.self_feed.inner_signal,
                state->players[i].mon.self_feed.world_signal,
                state->players[i].mon.self_feed.rival_signal,
                state->players[i].mon.self_feed.ghost_signal,
                state->players[i].mon.self_feed.balance,
                state->players[i].ai_debug_line,
                genome_summary);
        }
        fclose(replay);
    }
}