#pragma bank 255

#include "audio_runtime.h"

#define AUDIO_TRACK_NONE 0u

#define AUDIO_NOTE_REST 0u
#define AUDIO_NOTE_C3 1046u
#define AUDIO_NOTE_G3 1379u
#define AUDIO_NOTE_A3 1452u
#define AUDIO_NOTE_C4 1547u
#define AUDIO_NOTE_D4 1602u
#define AUDIO_NOTE_E4 1650u
#define AUDIO_NOTE_F4 1673u
#define AUDIO_NOTE_G4 1714u
#define AUDIO_NOTE_A4 1750u
#define AUDIO_NOTE_C5 1798u
#define AUDIO_NOTE_D5 1825u
#define AUDIO_NOTE_E5 1849u
#define AUDIO_NOTE_F5 1860u

#define AUDIO_NR10_REG (*(volatile uint8_t *)0xFF10u)
#define AUDIO_NR11_REG (*(volatile uint8_t *)0xFF11u)
#define AUDIO_NR12_REG (*(volatile uint8_t *)0xFF12u)
#define AUDIO_NR13_REG (*(volatile uint8_t *)0xFF13u)
#define AUDIO_NR14_REG (*(volatile uint8_t *)0xFF14u)
#define AUDIO_NR21_REG (*(volatile uint8_t *)0xFF16u)
#define AUDIO_NR22_REG (*(volatile uint8_t *)0xFF17u)
#define AUDIO_NR23_REG (*(volatile uint8_t *)0xFF18u)
#define AUDIO_NR24_REG (*(volatile uint8_t *)0xFF19u)
#define AUDIO_NR41_REG (*(volatile uint8_t *)0xFF20u)
#define AUDIO_NR42_REG (*(volatile uint8_t *)0xFF21u)
#define AUDIO_NR43_REG (*(volatile uint8_t *)0xFF22u)
#define AUDIO_NR44_REG (*(volatile uint8_t *)0xFF23u)
#define AUDIO_NR50_REG (*(volatile uint8_t *)0xFF24u)
#define AUDIO_NR51_REG (*(volatile uint8_t *)0xFF25u)
#define AUDIO_NR52_REG (*(volatile uint8_t *)0xFF26u)

typedef struct {
    uint16_t note;
    uint8_t frames;
    uint8_t volume;
    uint8_t duty;
} MusicStep;

typedef struct {
    const MusicStep *steps;
    uint8_t step_count;
} MusicTrackDef;

static const MusicStep kTrackTitle[] = {
    {AUDIO_NOTE_C4, 18u, 10u, 2u}, {AUDIO_NOTE_E4, 18u, 10u, 2u}, {AUDIO_NOTE_G4, 18u, 10u, 2u}, {AUDIO_NOTE_C5, 24u, 11u, 2u},
    {AUDIO_NOTE_A4, 18u, 10u, 2u}, {AUDIO_NOTE_G4, 18u, 10u, 2u}, {AUDIO_NOTE_E4, 18u, 10u, 2u}, {AUDIO_NOTE_D4, 18u, 9u, 2u}
};

static const MusicStep kTrackSafeFields[] = {
    {AUDIO_NOTE_C4, 12u, 8u, 2u}, {AUDIO_NOTE_E4, 12u, 8u, 2u}, {AUDIO_NOTE_G4, 18u, 9u, 2u}, {AUDIO_NOTE_E4, 12u, 8u, 2u},
    {AUDIO_NOTE_D4, 12u, 8u, 2u}, {AUDIO_NOTE_F4, 12u, 8u, 2u}, {AUDIO_NOTE_A4, 18u, 9u, 2u}, {AUDIO_NOTE_F4, 12u, 8u, 2u},
    {AUDIO_NOTE_E4, 12u, 8u, 2u}, {AUDIO_NOTE_G4, 12u, 8u, 2u}, {AUDIO_NOTE_C5, 18u, 9u, 2u}, {AUDIO_NOTE_G4, 12u, 8u, 2u},
    {AUDIO_NOTE_E4, 12u, 8u, 2u}, {AUDIO_NOTE_D4, 12u, 8u, 2u}, {AUDIO_NOTE_C4, 24u, 8u, 2u}, {AUDIO_NOTE_REST, 6u, 0u, 2u}
};

static const MusicStep kTrackSettlement[] = {
    {AUDIO_NOTE_G3, 18u, 7u, 1u}, {AUDIO_NOTE_C4, 18u, 8u, 1u}, {AUDIO_NOTE_E4, 24u, 8u, 1u}, {AUDIO_NOTE_C4, 18u, 7u, 1u},
    {AUDIO_NOTE_G3, 18u, 7u, 1u}, {AUDIO_NOTE_A3, 18u, 7u, 1u}, {AUDIO_NOTE_C4, 24u, 8u, 1u}, {AUDIO_NOTE_REST, 8u, 0u, 1u}
};

static const MusicStep kTrackShrineReseed[] = {
    {AUDIO_NOTE_E4, 12u, 9u, 3u}, {AUDIO_NOTE_G4, 12u, 9u, 3u}, {AUDIO_NOTE_C5, 18u, 10u, 3u}, {AUDIO_NOTE_G4, 12u, 9u, 3u},
    {AUDIO_NOTE_D5, 18u, 10u, 3u}, {AUDIO_NOTE_C5, 18u, 10u, 3u}, {AUDIO_NOTE_G4, 18u, 9u, 3u}, {AUDIO_NOTE_REST, 8u, 0u, 3u}
};

static const MusicStep kTrackOuterRim[] = {
    {AUDIO_NOTE_C4, 10u, 8u, 2u}, {AUDIO_NOTE_D4, 10u, 8u, 2u}, {AUDIO_NOTE_F4, 14u, 9u, 2u}, {AUDIO_NOTE_D4, 10u, 8u, 2u},
    {AUDIO_NOTE_C4, 10u, 8u, 2u}, {AUDIO_NOTE_G3, 14u, 8u, 2u}, {AUDIO_NOTE_A3, 14u, 8u, 2u}, {AUDIO_NOTE_C4, 18u, 9u, 2u},
    {AUDIO_NOTE_D4, 10u, 8u, 2u}, {AUDIO_NOTE_F4, 18u, 9u, 2u}, {AUDIO_NOTE_E4, 14u, 8u, 2u}, {AUDIO_NOTE_REST, 8u, 0u, 2u}
};

static const MusicStep kTrackBoss[] = {
    {AUDIO_NOTE_C4, 8u, 10u, 2u}, {AUDIO_NOTE_C4, 8u, 10u, 2u}, {AUDIO_NOTE_D4, 8u, 10u, 2u}, {AUDIO_NOTE_E4, 8u, 10u, 2u},
    {AUDIO_NOTE_G4, 10u, 11u, 2u}, {AUDIO_NOTE_E4, 8u, 10u, 2u}, {AUDIO_NOTE_D4, 8u, 10u, 2u}, {AUDIO_NOTE_C4, 12u, 10u, 2u},
    {AUDIO_NOTE_F4, 8u, 10u, 2u}, {AUDIO_NOTE_E4, 8u, 10u, 2u}, {AUDIO_NOTE_D4, 8u, 10u, 2u}, {AUDIO_NOTE_C4, 12u, 10u, 2u}
};

static const MusicStep kTrackFeatherVictory[] = {
    {AUDIO_NOTE_C4, 10u, 10u, 2u}, {AUDIO_NOTE_E4, 10u, 10u, 2u}, {AUDIO_NOTE_G4, 12u, 11u, 2u}, {AUDIO_NOTE_C5, 18u, 12u, 2u},
    {AUDIO_NOTE_E5, 12u, 11u, 2u}, {AUDIO_NOTE_G4, 12u, 10u, 2u}, {AUDIO_NOTE_C5, 18u, 11u, 2u}, {AUDIO_NOTE_REST, 8u, 0u, 2u}
};

static const MusicTrackDef kMusicTracks[] = {
    {0, 0u},
    {kTrackTitle, (uint8_t)(sizeof(kTrackTitle) / sizeof(kTrackTitle[0]))},
    {kTrackSafeFields, (uint8_t)(sizeof(kTrackSafeFields) / sizeof(kTrackSafeFields[0]))},
    {kTrackSettlement, (uint8_t)(sizeof(kTrackSettlement) / sizeof(kTrackSettlement[0]))},
    {kTrackShrineReseed, (uint8_t)(sizeof(kTrackShrineReseed) / sizeof(kTrackShrineReseed[0]))},
    {kTrackOuterRim, (uint8_t)(sizeof(kTrackOuterRim) / sizeof(kTrackOuterRim[0]))},
    {kTrackBoss, (uint8_t)(sizeof(kTrackBoss) / sizeof(kTrackBoss[0]))},
    {kTrackFeatherVictory, (uint8_t)(sizeof(kTrackFeatherVictory) / sizeof(kTrackFeatherVictory[0]))}
};

static uint8_t g_music_track = AUDIO_TRACK_NONE;
static uint8_t g_music_step = 0u;
static uint8_t g_music_timer = 0u;
static uint8_t g_music_override_track = AUDIO_TRACK_NONE;
static uint16_t g_music_override_timer = 0u;
static uint8_t g_footstep_timer = 0u;

static void audio_stop_square1(void) {
    AUDIO_NR12_REG = 0u;
}

static void audio_stop_square2(void) {
    AUDIO_NR22_REG = 0u;
}

static void audio_play_square1(uint16_t note, uint8_t volume, uint8_t duty, uint8_t decay) {
    if (note == AUDIO_NOTE_REST || volume == 0u) {
        audio_stop_square1();
        return;
    }
    AUDIO_NR10_REG = 0u;
    AUDIO_NR11_REG = (uint8_t)(((duty & 0x03u) << 6u) | 0x00u);
    AUDIO_NR12_REG = (uint8_t)(((volume & 0x0Fu) << 4u) | (decay & 0x07u));
    AUDIO_NR13_REG = (uint8_t)(note & 0xFFu);
    AUDIO_NR14_REG = (uint8_t)(0x80u | ((note >> 8u) & 0x07u));
}

static void audio_play_square2(uint16_t note, uint8_t volume, uint8_t duty) {
    if (note == AUDIO_NOTE_REST || volume == 0u) {
        audio_stop_square2();
        return;
    }
    AUDIO_NR21_REG = (uint8_t)(((duty & 0x03u) << 6u) | 0x00u);
    AUDIO_NR22_REG = (uint8_t)((volume & 0x0Fu) << 4u);
    AUDIO_NR23_REG = (uint8_t)(note & 0xFFu);
    AUDIO_NR24_REG = (uint8_t)(0x80u | ((note >> 8u) & 0x07u));
}

static void audio_play_noise(uint8_t volume, uint8_t polynomial, uint8_t decay) {
    if (volume == 0u) {
        AUDIO_NR42_REG = 0u;
        return;
    }
    AUDIO_NR41_REG = 0u;
    AUDIO_NR42_REG = (uint8_t)(((volume & 0x0Fu) << 4u) | (decay & 0x07u));
    AUDIO_NR43_REG = polynomial;
    AUDIO_NR44_REG = 0x80u;
}

void audio_init(void) FARMERS_FEATHER_BANKED {
    AUDIO_NR52_REG = 0x80u;
    AUDIO_NR50_REG = 0x77u;
    AUDIO_NR51_REG = 0xFFu;
    AUDIO_NR10_REG = 0u;
    AUDIO_NR12_REG = 0u;
    AUDIO_NR22_REG = 0u;
    AUDIO_NR42_REG = 0u;
    g_music_track = AUDIO_TRACK_NONE;
    g_music_step = 0u;
    g_music_timer = 0u;
    g_music_override_track = AUDIO_TRACK_NONE;
    g_music_override_timer = 0u;
    g_footstep_timer = 0u;
}

void audio_reset_runtime(void) FARMERS_FEATHER_BANKED {
    g_music_override_track = AUDIO_TRACK_NONE;
    g_music_override_timer = 0u;
    g_footstep_timer = 0u;
}

void audio_set_music(uint8_t track) FARMERS_FEATHER_BANKED {
    if (track == g_music_track) return;
    g_music_track = track;
    g_music_step = 0u;
    g_music_timer = 0u;
    audio_stop_square2();
}

void audio_set_music_override(uint8_t track, uint16_t duration) FARMERS_FEATHER_BANKED {
    g_music_override_track = track;
    g_music_override_timer = duration;
    audio_set_music(track);
}

void audio_sync_world_music(uint8_t world_track) FARMERS_FEATHER_BANKED {
    if (g_music_override_timer != 0u) {
        if (g_music_track != g_music_override_track) {
            audio_set_music(g_music_override_track);
        }
        return;
    }
    audio_set_music(world_track);
}

void audio_update(void) FARMERS_FEATHER_BANKED {
    const MusicTrackDef *track;
    const MusicStep *step;
    if (g_footstep_timer > 0u) {
        --g_footstep_timer;
    }
    if (g_music_override_timer > 0u) {
        --g_music_override_timer;
    }
    if (g_music_track == AUDIO_TRACK_NONE) return;
    if (g_music_timer > 0u) {
        --g_music_timer;
        return;
    }
    track = &kMusicTracks[g_music_track];
    if (track->step_count == 0u) return;
    step = &track->steps[g_music_step];
    audio_play_square2(step->note, step->volume, step->duty);
    g_music_timer = (step->frames > 0u) ? (uint8_t)(step->frames - 1u) : 0u;
    ++g_music_step;
    if (g_music_step >= track->step_count) {
        g_music_step = 0u;
    }
}

void audio_try_footstep(uint8_t on_sand) FARMERS_FEATHER_BANKED {
    if (g_footstep_timer != 0u) return;
    if (on_sand) {
        audio_play_noise(4u, 0x35u, 2u);
    } else {
        audio_play_noise(4u, 0x23u, 2u);
    }
    g_footstep_timer = 6u;
}

void audio_sfx_profile_select(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_C5, 8u, 2u, 3u);
}

void audio_sfx_profile_erase(void) FARMERS_FEATHER_BANKED {
    audio_play_noise(10u, 0x35u, 3u);
}

void audio_sfx_profile_start(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_G4, 10u, 2u, 2u);
}

void audio_sfx_autosave(void) FARMERS_FEATHER_BANKED {
    audio_play_noise(5u, 0x61u, 2u);
}

void audio_sfx_rake_swing(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_D4, 9u, 1u, 3u);
}

void audio_sfx_till_soil(void) FARMERS_FEATHER_BANKED {
    audio_play_noise(7u, 0x33u, 3u);
}

void audio_sfx_seed_plant(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_E4, 8u, 2u, 4u);
}

void audio_sfx_gear_pickup(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_A4, 10u, 2u, 3u);
}

void audio_sfx_harvest_bundle(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_G4, 10u, 2u, 3u);
}

void audio_sfx_wood_chop(void) FARMERS_FEATHER_BANKED {
    audio_play_noise(9u, 0x17u, 3u);
}

void audio_sfx_settlement_build(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_C4, 11u, 1u, 3u);
    audio_play_noise(7u, 0x26u, 3u);
}

void audio_sfx_settlement_rest(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_A4, 9u, 2u, 4u);
}

void audio_sfx_feather_gate(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_C5, 11u, 2u, 3u);
}

void audio_sfx_shrine_reseed(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_D5, 11u, 3u, 3u);
}

void audio_sfx_daemon_spawn(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_C3, 10u, 1u, 2u);
}

void audio_sfx_boss_spawn(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_C3, 12u, 1u, 2u);
    audio_play_noise(9u, 0x52u, 2u);
}

void audio_sfx_enemy_stagger(void) FARMERS_FEATHER_BANKED {
    audio_play_noise(8u, 0x14u, 2u);
}

void audio_sfx_player_hurt(void) FARMERS_FEATHER_BANKED {
    audio_play_noise(10u, 0x54u, 2u);
}

void audio_sfx_player_respawn(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_C4, 8u, 2u, 4u);
}

void audio_sfx_heal(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_A4, 9u, 2u, 4u);
}

void audio_sfx_boss_lunge(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_A3, 11u, 1u, 2u);
}

void audio_sfx_boss_break(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_F5, 11u, 2u, 2u);
    audio_play_noise(9u, 0x11u, 2u);
}

void audio_sfx_boss_defeat(void) FARMERS_FEATHER_BANKED {
    audio_play_square1(AUDIO_NOTE_C5, 12u, 2u, 2u);
}