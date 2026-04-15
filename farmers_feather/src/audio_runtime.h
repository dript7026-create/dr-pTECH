#ifndef FARMERS_FEATHER_AUDIO_RUNTIME_H
#define FARMERS_FEATHER_AUDIO_RUNTIME_H

#include <stdint.h>

#ifndef FARMERS_FEATHER_BANKED
#if defined(__SDCC) || defined(SDCC)
#define FARMERS_FEATHER_BANKED __banked
#else
#define FARMERS_FEATHER_BANKED
#endif
#endif

void audio_init(void) FARMERS_FEATHER_BANKED;
void audio_reset_runtime(void) FARMERS_FEATHER_BANKED;
void audio_set_music(uint8_t track) FARMERS_FEATHER_BANKED;
void audio_set_music_override(uint8_t track, uint16_t duration) FARMERS_FEATHER_BANKED;
void audio_sync_world_music(uint8_t world_track) FARMERS_FEATHER_BANKED;
void audio_update(void) FARMERS_FEATHER_BANKED;
void audio_try_footstep(uint8_t on_sand) FARMERS_FEATHER_BANKED;

void audio_sfx_profile_select(void) FARMERS_FEATHER_BANKED;
void audio_sfx_profile_erase(void) FARMERS_FEATHER_BANKED;
void audio_sfx_profile_start(void) FARMERS_FEATHER_BANKED;
void audio_sfx_autosave(void) FARMERS_FEATHER_BANKED;
void audio_sfx_rake_swing(void) FARMERS_FEATHER_BANKED;
void audio_sfx_till_soil(void) FARMERS_FEATHER_BANKED;
void audio_sfx_seed_plant(void) FARMERS_FEATHER_BANKED;
void audio_sfx_gear_pickup(void) FARMERS_FEATHER_BANKED;
void audio_sfx_harvest_bundle(void) FARMERS_FEATHER_BANKED;
void audio_sfx_wood_chop(void) FARMERS_FEATHER_BANKED;
void audio_sfx_settlement_build(void) FARMERS_FEATHER_BANKED;
void audio_sfx_settlement_rest(void) FARMERS_FEATHER_BANKED;
void audio_sfx_feather_gate(void) FARMERS_FEATHER_BANKED;
void audio_sfx_shrine_reseed(void) FARMERS_FEATHER_BANKED;
void audio_sfx_daemon_spawn(void) FARMERS_FEATHER_BANKED;
void audio_sfx_boss_spawn(void) FARMERS_FEATHER_BANKED;
void audio_sfx_enemy_stagger(void) FARMERS_FEATHER_BANKED;
void audio_sfx_player_hurt(void) FARMERS_FEATHER_BANKED;
void audio_sfx_player_respawn(void) FARMERS_FEATHER_BANKED;
void audio_sfx_heal(void) FARMERS_FEATHER_BANKED;
void audio_sfx_boss_lunge(void) FARMERS_FEATHER_BANKED;
void audio_sfx_boss_break(void) FARMERS_FEATHER_BANKED;
void audio_sfx_boss_defeat(void) FARMERS_FEATHER_BANKED;

#endif