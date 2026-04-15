#ifndef PASSAGE_MODULES_H
#define PASSAGE_MODULES_H

#include <stdint.h>

void passage_modules_begin_session(uint16_t world_seed, uint8_t level, uint8_t weapon_rank, uint8_t armor_rank);
void passage_modules_record_move(uint8_t moved, uint8_t tile_kind);
void passage_modules_record_rake(uint8_t connected);
void passage_modules_record_use(uint8_t restorative);
void passage_modules_update(uint8_t phase, uint8_t boss_active, uint8_t health, uint8_t max_health);

uint8_t passage_modules_adjust_spawn_tier(uint8_t base_tier, uint8_t border, uint8_t coherence_state);
uint8_t passage_modules_adjust_windup(uint8_t enemy_type, uint8_t tier, uint8_t base_frames);
uint8_t passage_modules_adjust_lunge_frames(uint8_t enemy_type, uint8_t tier, uint8_t base_frames);
uint8_t passage_modules_adjust_stun(uint8_t enemy_type, uint8_t tier, uint8_t base_frames);
uint8_t passage_modules_adjust_lunge_speed(uint8_t enemy_type, uint8_t tier, uint8_t base_speed);

uint8_t passage_modules_sync_visuals(const unsigned char *base_tiles, uint8_t tile_count, uint8_t weapon_rank, uint8_t armor_rank, uint8_t phase, uint8_t boss_active);
const unsigned char *passage_modules_sprite_tiles(void);

#endif