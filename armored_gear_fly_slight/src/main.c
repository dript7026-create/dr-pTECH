#include <gb/gb.h>
#include <gbdk/console.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "audio_runtime.h"
#include "passage_modules.h"
#include "save_data.h"
#include "game_types.h"
#include "runtime_exports.h"
#include "title_profile.h"
#include "field_state.h"

#define WORLD_GRID_TILES 4096u
#define SCREEN_TILE_W 20u
#define SCREEN_TILE_H 18u
#define STREAM_TILE_W 21u
#define STREAM_TILE_H 19u
#define WORLD_SCREEN_HUD_Y 128u
#define PLAYER_CENTER_X 80u
#define PLAYER_CENTER_Y 64u
#define WORLD_PIXEL_MAX ((WORLD_GRID_TILES * 8u) - 8u)
#define CAMERA_MAX_X ((WORLD_GRID_TILES * 8u) - 160u)
#define CAMERA_MAX_Y ((WORLD_GRID_TILES * 8u) - 144u)
#define WORLD_CHUNK_SHIFT 4u
#define DISC_CENTER_TILE (WORLD_GRID_TILES / 2u)
#define DISC_RADIUS_TILES 1788u
#define DISC_SAFE_RADIUS 1460u
#define DISC_BEACH_RADIUS 1660u
#define DISC_HARD_RADIUS 1768u
#define MAX_ENEMIES 5u
#define MAX_IMPACTS 8u
#define MAX_PROJECTILES 4u
#define PHASE_LENGTH 360u
#define PLOT_BASE_GROWTH 240u
#define SAVE_DELAY_FRAMES 90u
#define PHASE_TIMER_STORAGE_MASK 0x01FFu

#define TUTORIAL_STAGE_WAKE 0u
#define TUTORIAL_STAGE_GEAR 1u
#define TUTORIAL_STAGE_COMBAT 2u
#define TUTORIAL_STAGE_TILL 3u
#define TUTORIAL_STAGE_PLANT 4u
#define TUTORIAL_STAGE_HARVEST 5u
#define TUTORIAL_STAGE_BUILD 6u
#define TUTORIAL_STAGE_REST 7u
#define TUTORIAL_STAGE_COMPLETE 8u

#define TUTORIAL_WEAPON_OFFSET_X 2u
#define TUTORIAL_ARMOR_OFFSET_X 4u
#define TUTORIAL_COMBAT_OFFSET_X 14u
#define TUTORIAL_FARM_OFFSET_X 10u
#define TUTORIAL_FARM_OFFSET_Y 5u
#define TUTORIAL_SETTLEMENT_OFFSET_X 28u

#define DIR_UP 0u
#define DIR_DOWN 1u
#define DIR_LEFT 2u
#define DIR_RIGHT 3u

#define ENEMY_NONE 0u
#define ENEMY_KIN 1u
#define ENEMY_BOSS 2u

#define AI_ROAM 0u
#define AI_WINDUP 1u
#define AI_LUNGE 2u
#define AI_STUN 3u

#define TILE_WATER 0u
#define TILE_SAND 1u
#define TILE_GRASS 2u
#define TILE_SOIL 3u
#define TILE_CROP 4u
#define TILE_RIPE 5u
#define TILE_TREE 6u
#define TILE_ROCK 7u
#define TILE_SITE 8u
#define TILE_HUT 9u
#define TILE_FEATHER 10u
#define TILE_SHRINE 11u
#define TILE_CRATER 12u
#define TILE_BAR0 13u
#define TILE_BAR1 14u
#define TILE_BAR2 15u
#define TILE_BAR3 16u
#define TILE_HEART_FULL 17u
#define TILE_HEART_EMPTY 18u
#define TILE_WOOD_ICON 19u
#define TILE_BLANK 20u
#define TILE_MOON0 21u
#define TILE_MOON1 22u
#define TILE_MOON2 23u
#define TILE_MOON3 24u
#define TILE_MOON4 25u
#define TILE_MOON5 26u
#define TILE_MOON6 27u
#define TILE_MOON7 28u
#define TILE_SEED_ICON 29u
#define TILE_RAFT 30u
#define TILE_RAKE 31u
#define TILE_ARMOR 32u

#define AUDIO_TRACK_NONE 0u
#define AUDIO_TRACK_TITLE 1u
#define AUDIO_TRACK_SAFE_FIELDS 2u
#define AUDIO_TRACK_SETTLEMENT 3u
#define AUDIO_TRACK_SHRINE_RESEED 4u
#define AUDIO_TRACK_OUTER_RIM 5u
#define AUDIO_TRACK_BOSS 6u
#define AUDIO_TRACK_FEATHER_VICTORY 7u

#define AUDIO_NOTE_REST 0u
#define AUDIO_NOTE_C3 1046u
#define AUDIO_NOTE_D3 1155u
#define AUDIO_NOTE_E3 1253u
#define AUDIO_NOTE_F3 1297u
#define AUDIO_NOTE_G3 1379u
#define AUDIO_NOTE_A3 1452u
#define AUDIO_NOTE_B3 1517u
#define AUDIO_NOTE_C4 1547u
#define AUDIO_NOTE_D4 1602u
#define AUDIO_NOTE_E4 1650u
#define AUDIO_NOTE_F4 1673u
#define AUDIO_NOTE_G4 1714u
#define AUDIO_NOTE_A4 1750u
#define AUDIO_NOTE_B4 1783u
#define AUDIO_NOTE_C5 1798u
#define AUDIO_NOTE_D5 1825u
#define AUDIO_NOTE_E5 1849u
#define AUDIO_NOTE_F5 1860u
#define AUDIO_NOTE_G5 1881u
#define AUDIO_NOTE_A5 1899u

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
#define PROJECTILE_SPRITE_BASE (MAX_ENEMIES + 1u)
#define TOTAL_ACTION_SPRITES (1u + MAX_ENEMIES + MAX_PROJECTILES)
#define SPRITE_TILE_COUNT 8u
#define PROJECTILE_SPEED_BASE 3u
#define PROJECTILE_TTL_BASE 20u

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

typedef struct {
    uint8_t active;
    uint8_t tile_index;
    int8_t vx;
    int8_t vy;
    uint8_t ttl;
    uint16_t x;
    uint16_t y;
} Projectile;

static const unsigned char bg_tiles[] = {
    0x00,0x00, 0x44,0x00, 0x00,0x00, 0x22,0x00, 0x00,0x00, 0x88,0x00, 0x00,0x00, 0x11,0x00,
    0x00,0x00, 0x44,0x00, 0x00,0x00, 0x22,0x00, 0x00,0x00, 0x88,0x00, 0x00,0x00, 0x11,0x00,

    0xff,0x00, 0xf3,0x00, 0xff,0x00, 0xcf,0x00, 0xff,0x00, 0x3f,0x00, 0xff,0x00, 0xfc,0x00,
    0xff,0x00, 0xf3,0x00, 0xff,0x00, 0xcf,0x00, 0xff,0x00, 0x3f,0x00, 0xff,0x00, 0xfc,0x00,

    0x24,0x00, 0x00,0x00, 0x42,0x00, 0x18,0x00, 0x81,0x00, 0x24,0x00, 0x00,0x00, 0x42,0x00,
    0x18,0x00, 0x81,0x00, 0x24,0x00, 0x00,0x00, 0x42,0x00, 0x18,0x00, 0x81,0x00, 0x24,0x00,

    0xff,0x00, 0x81,0x00, 0xbd,0x00, 0x81,0x00, 0xa5,0x00, 0x81,0x00, 0xbd,0x00, 0xff,0x00,
    0xff,0x00, 0x81,0x00, 0xbd,0x00, 0x81,0x00, 0xa5,0x00, 0x81,0x00, 0xbd,0x00, 0xff,0x00,

    0x18,0x00, 0x3c,0x00, 0x5a,0x00, 0x99,0x00, 0x18,0x00, 0x3c,0x00, 0x24,0x00, 0x24,0x00,
    0x18,0x00, 0x3c,0x00, 0x5a,0x00, 0x99,0x00, 0x18,0x00, 0x3c,0x00, 0x24,0x00, 0x24,0x00,

    0x18,0x00, 0x3c,0x00, 0x5a,0x00, 0xbd,0x00, 0x5a,0x00, 0x3c,0x00, 0x24,0x00, 0x66,0x00,
    0x18,0x00, 0x3c,0x00, 0x5a,0x00, 0xbd,0x00, 0x5a,0x00, 0x3c,0x00, 0x24,0x00, 0x66,0x00,

    0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x18,0x00, 0x18,0x00, 0x3c,0x00, 0x24,0x00, 0x24,0x00,
    0x5a,0x00, 0x81,0x00, 0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x18,0x00, 0x18,0x00, 0x3c,0x00,

    0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0xdb,0x00, 0xff,0x00, 0x18,0x00, 0x3c,0x00, 0x66,0x00,
    0xc3,0x00, 0x81,0x00, 0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0xdb,0x00, 0xff,0x00, 0x18,0x00,

    0x18,0x00, 0x3c,0x00, 0x5a,0x00, 0x99,0x00, 0x5a,0x00, 0x3c,0x00, 0x18,0x00, 0x00,0x00,
    0x18,0x00, 0x3c,0x00, 0x5a,0x00, 0x99,0x00, 0x5a,0x00, 0x3c,0x00, 0x18,0x00, 0x00,0x00,

    0x7e,0x00, 0x42,0x00, 0x5a,0x00, 0x42,0x00, 0x42,0x00, 0x5a,0x00, 0x42,0x00, 0x7e,0x00,
    0x7e,0x00, 0x42,0x00, 0x5a,0x00, 0x42,0x00, 0x42,0x00, 0x5a,0x00, 0x42,0x00, 0x7e,0x00,

    0x18,0x00, 0x3c,0x00, 0x24,0x00, 0x18,0x00, 0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x24,0x00,
    0x18,0x00, 0x3c,0x00, 0x24,0x00, 0x18,0x00, 0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x24,0x00,

    0x18,0x00, 0x24,0x00, 0x5a,0x00, 0xbd,0x00, 0x5a,0x00, 0x24,0x00, 0x18,0x00, 0x00,0x00,
    0x18,0x00, 0x24,0x00, 0x5a,0x00, 0xbd,0x00, 0x5a,0x00, 0x24,0x00, 0x18,0x00, 0x00,0x00,

    0x00,0x00, 0x18,0x00, 0x24,0x00, 0x42,0x00, 0x81,0x00, 0x42,0x00, 0x24,0x00, 0x18,0x00,
    0x00,0x00, 0x18,0x00, 0x24,0x00, 0x42,0x00, 0x81,0x00, 0x42,0x00, 0x24,0x00, 0x18,0x00,

    0xff,0x00, 0x81,0x00, 0x81,0x00, 0x81,0x00, 0x81,0x00, 0x81,0x00, 0x81,0x00, 0xff,0x00,
    0xff,0x00, 0x81,0x00, 0x81,0x00, 0x81,0x00, 0x81,0x00, 0x81,0x00, 0x81,0x00, 0xff,0x00,

    0xff,0x00, 0xff,0x00, 0xc3,0x00, 0xc3,0x00, 0x81,0x00, 0x81,0x00, 0x00,0x00, 0x00,0x00,
    0xff,0x00, 0xff,0x00, 0xc3,0x00, 0xc3,0x00, 0x81,0x00, 0x81,0x00, 0x00,0x00, 0x00,0x00,

    0x7e,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x7e,0x00,
    0x7e,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x7e,0x00,

    0x7e,0x00, 0x7e,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00,
    0x7e,0x00, 0x7e,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00,

    0x7e,0x00, 0x7e,0x00, 0x7e,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00,
    0x7e,0x00, 0x7e,0x00, 0x7e,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00,

    0x7e,0x00, 0x7e,0x00, 0x7e,0x00, 0x7e,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00,
    0x7e,0x00, 0x7e,0x00, 0x7e,0x00, 0x7e,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00, 0x42,0x00,

    0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0xff,0x00, 0xff,0x00, 0x7e,0x00, 0x3c,0x00, 0x18,0x00,
    0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0xff,0x00, 0xff,0x00, 0x7e,0x00, 0x3c,0x00, 0x18,0x00,

    0x18,0x00, 0x24,0x00, 0x5a,0x00, 0x7e,0x00, 0x7e,0x00, 0x5a,0x00, 0x24,0x00, 0x18,0x00,
    0x18,0x00, 0x24,0x00, 0x5a,0x00, 0x7e,0x00, 0x7e,0x00, 0x5a,0x00, 0x24,0x00, 0x18,0x00,

    0x18,0x00, 0x3c,0x00, 0x5a,0x00, 0x99,0x00, 0xbd,0x00, 0x5a,0x00, 0x24,0x00, 0x24,0x00,
    0x18,0x00, 0x3c,0x00, 0x5a,0x00, 0x99,0x00, 0xbd,0x00, 0x5a,0x00, 0x24,0x00, 0x24,0x00,

    0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00,
    0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00,

    0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00,
    0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00,

    0x00,0x00, 0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x7e,0x00, 0x3c,0x00, 0x18,0x00, 0x00,0x00,
    0x00,0x00, 0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x7e,0x00, 0x3c,0x00, 0x18,0x00, 0x00,0x00,

    0x00,0x00, 0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0xff,0x00, 0x7e,0x00, 0x3c,0x00, 0x18,0x00,
    0x00,0x00, 0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0xff,0x00, 0x7e,0x00, 0x3c,0x00, 0x18,0x00,

    0x00,0x00, 0x38,0x00, 0x7c,0x00, 0xfe,0x00, 0xfe,0x00, 0x7c,0x00, 0x38,0x00, 0x00,0x00,
    0x00,0x00, 0x38,0x00, 0x7c,0x00, 0xfe,0x00, 0xfe,0x00, 0x7c,0x00, 0x38,0x00, 0x00,0x00,

    0x00,0x00, 0x70,0x00, 0xf8,0x00, 0xfe,0x00, 0xfe,0x00, 0xf8,0x00, 0x70,0x00, 0x00,0x00,
    0x00,0x00, 0x70,0x00, 0xf8,0x00, 0xfe,0x00, 0xfe,0x00, 0xf8,0x00, 0x70,0x00, 0x00,0x00,

    0x00,0x00, 0xe0,0x00, 0xf8,0x00, 0xfe,0x00, 0xfe,0x00, 0xf8,0x00, 0xe0,0x00, 0x00,0x00,
    0x00,0x00, 0xe0,0x00, 0xf8,0x00, 0xfe,0x00, 0xfe,0x00, 0xf8,0x00, 0xe0,0x00, 0x00,0x00,

    0x00,0x00, 0xc0,0x00, 0xf0,0x00, 0xfc,0x00, 0xfc,0x00, 0xf0,0x00, 0xc0,0x00, 0x00,0x00,
    0x00,0x00, 0xc0,0x00, 0xf0,0x00, 0xfc,0x00, 0xfc,0x00, 0xf0,0x00, 0xc0,0x00, 0x00,0x00,

    0x00,0x00, 0x80,0x00, 0xe0,0x00, 0xf8,0x00, 0xf8,0x00, 0xe0,0x00, 0x80,0x00, 0x00,0x00,
    0x00,0x00, 0x80,0x00, 0xe0,0x00, 0xf8,0x00, 0xf8,0x00, 0xe0,0x00, 0x80,0x00, 0x00,0x00,

    0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x18,0x00, 0x18,0x00, 0x7e,0x00, 0x3c,0x00, 0x18,0x00,
    0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x18,0x00, 0x18,0x00, 0x7e,0x00, 0x3c,0x00, 0x18,0x00,

    0x7e,0x00, 0xdb,0x00, 0x7e,0x00, 0xdb,0x00, 0x7e,0x00, 0xdb,0x00, 0x7e,0x00, 0x00,0x00,
    0x18,0x00, 0x18,0x00, 0x18,0x00, 0x7e,0x00, 0x7e,0x00, 0x18,0x00, 0x18,0x00, 0x18,0x00,
    0x66,0x00, 0x7e,0x00, 0x3c,0x00, 0x3c,0x00, 0x3c,0x00, 0x24,0x00, 0x24,0x00, 0x66,0x00
};

static const unsigned char sprite_tiles[] = {
    0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x6e,0x00, 0xff,0x00, 0x3c,0x00, 0x66,0x00, 0x42,0x00,
    0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x66,0x00, 0xdb,0x00, 0x3c,0x00, 0x24,0x00, 0x66,0x00,
    0x10,0x00, 0x38,0x00, 0x7c,0x00, 0xee,0x00, 0xfe,0x00, 0x7c,0x00, 0x28,0x00, 0x6c,0x00,
    0x08,0x00, 0x1c,0x00, 0x3e,0x00, 0x7f,0x00, 0xff,0x00, 0x3e,0x00, 0x14,0x00, 0x36,0x00,
    0x18,0x00, 0x7e,0x00, 0xe7,0x00, 0xbd,0x00, 0xff,0x00, 0x7e,0x00, 0x5a,0x00, 0x24,0x00,
    0x24,0x00, 0x7e,0x00, 0xdb,0x00, 0xff,0x00, 0xff,0x00, 0x7e,0x00, 0x5a,0x00, 0xa5,0x00,
    0x18,0x00, 0x18,0x00, 0x3c,0x00, 0x7e,0x00, 0x3c,0x00, 0x18,0x00, 0x18,0x00, 0x00,0x00,
    0x00,0x00, 0x24,0x00, 0x66,0x00, 0xff,0x00, 0xff,0x00, 0x66,0x00, 0x24,0x00, 0x00,0x00
};

static const FarmerVector kDefaultFarmer = {
    188u, 96u, 82u, 144u,
    176u, 158u, 110u, 126u, 78u, 164u,
    138u, 104u, 82u, 120u, 130u, 142u, 90u,
    90u, 104u, 61u
};

static const uint16_t kProfileSeeds[SAVE_PROFILE_COUNT] = {
    0x3141u,
    0x6282u,
    0x9423u
};

FarmerVector g_farmer;
Settlement g_settlements[MAX_SETTLEMENTS];
Plot g_plots[MAX_PLOTS];
static Enemy g_enemies[MAX_ENEMIES];
Impact g_impacts[MAX_IMPACTS];
static Projectile g_projectiles[MAX_PROJECTILES];

static uint8_t g_row_buffer[STREAM_TILE_W];
static uint8_t g_col_buffer[STREAM_TILE_H];
static uint8_t g_hud_map[40];
static FieldState g_player_field;
uint8_t g_profile_index = 0u;
uint16_t g_world_seed = 0u;
static uint16_t g_player_x = 0u;
static uint16_t g_player_y = 0u;
static uint16_t g_camera_x = 0u;
static uint16_t g_camera_y = 0u;
static uint16_t g_old_camera_x = 0u;
static uint16_t g_old_camera_y = 0u;
static uint16_t g_map_pos_x = 0u;
static uint16_t g_map_pos_y = 0u;
static uint16_t g_old_map_pos_x = 0xFFFFu;
static uint16_t g_old_map_pos_y = 0xFFFFu;
uint16_t g_shrine_tile_x = DISC_CENTER_TILE;
uint16_t g_shrine_tile_y = DISC_CENTER_TILE;
uint16_t g_start_tile_x = DISC_CENTER_TILE;
uint16_t g_start_tile_y = DISC_CENTER_TILE;
static uint8_t g_redraw = 0u;
static uint8_t g_facing = DIR_RIGHT;
static uint8_t g_health = 3u;
static uint8_t g_max_health = 3u;
static uint8_t g_wood = 4u;
uint8_t g_grain = 2u;
static uint8_t g_level = 1u;
static uint8_t g_xp = 0u;
uint8_t g_phase = 0u;
static uint16_t g_phase_timer = 0u;
uint8_t g_boss_active = 0u;
static uint8_t g_boss_defeated = 0u;
static uint8_t g_attack_timer = 0u;
static uint8_t g_invuln_timer = 0u;
static uint8_t g_spawn_timer = 120u;
static uint8_t g_save_dirty = 0u;
static uint8_t g_save_cooldown = 0u;
static uint8_t g_weapon_level = 0u;
static uint8_t g_armor_level = 0u;
static uint8_t g_walk_anim_frame = 0u;
static uint8_t g_move_anim_timer = 0u;
static uint8_t g_tutorial_stage = TUTORIAL_STAGE_WAKE;
uint8_t g_tutorial_overlay_enabled = 0u;
static uint16_t g_frame_counter = 0u;

static uint8_t audio_world_track(void);
static void mark_save_dirty(void);
static uint8_t count_built_settlements(void);
static uint8_t spawn_impact_enemy(uint8_t enemy_type, uint8_t tier, uint16_t x, uint16_t y);
static uint8_t spawn_daemon_kin(void);
static void advance_phase(void);
static void set_tutorial_stage(uint8_t stage);
static void enemy_mark_damage(uint8_t index, uint8_t intensity);

uint8_t clamp_u8(int16_t value) {
    if (value < 0) return 0u;
    if (value > 255) return 255u;
    return (uint8_t)value;
}

static uint16_t clamp_world_pixel(int32_t value) {
    if (value < 0) return 0u;
    if ((uint32_t)value > WORLD_PIXEL_MAX) return WORLD_PIXEL_MAX;
    return (uint16_t)value;
}

static uint8_t abs_u8_diff(uint8_t left, uint8_t right) {
    return (left >= right) ? (left - right) : (right - left);
}

uint16_t abs_u16_diff(uint16_t left, uint16_t right) {
    return (left >= right) ? (left - right) : (right - left);
}

static uint8_t tutorial_complete(void) {
    return (g_tutorial_stage >= TUTORIAL_STAGE_COMPLETE) ? 1u : 0u;
}

static uint16_t tutorial_raft_tile_x(void) {
    return g_start_tile_x;
}

static uint16_t tutorial_raft_tile_y(void) {
    return g_start_tile_y;
}

static uint16_t tutorial_weapon_tile_x(void) {
    return (uint16_t)(g_start_tile_x + TUTORIAL_WEAPON_OFFSET_X);
}

static uint16_t tutorial_weapon_tile_y(void) {
    return g_start_tile_y;
}

static uint16_t tutorial_armor_tile_x(void) {
    return (uint16_t)(g_start_tile_x + TUTORIAL_ARMOR_OFFSET_X);
}

static uint16_t tutorial_armor_tile_y(void) {
    return g_start_tile_y;
}

static uint16_t tutorial_combat_tile_x(void) {
    return (uint16_t)(g_start_tile_x + TUTORIAL_COMBAT_OFFSET_X);
}

static uint16_t tutorial_combat_tile_y(void) {
    return g_start_tile_y;
}

static uint16_t tutorial_farm_tile_x(void) {
    return (uint16_t)(g_start_tile_x + TUTORIAL_FARM_OFFSET_X);
}

static uint16_t tutorial_farm_tile_y(void) {
    return (uint16_t)(g_start_tile_y - TUTORIAL_FARM_OFFSET_Y);
}

static uint16_t tutorial_settlement_tile_x(void) {
    return (uint16_t)(g_start_tile_x + TUTORIAL_SETTLEMENT_OFFSET_X);
}

static uint16_t tutorial_settlement_tile_y(void) {
    return g_start_tile_y;
}

static uint8_t tutorial_combat_zone(uint16_t tile_x, uint16_t tile_y) {
    if (abs_u16_diff(tile_x, tutorial_combat_tile_x()) > 2u) return 0u;
    if (abs_u16_diff(tile_y, tutorial_combat_tile_y()) > 2u) return 0u;
    return 1u;
}

static uint8_t tutorial_farm_tile(uint16_t tile_x, uint16_t tile_y) {
    if (tile_x < tutorial_farm_tile_x() || tile_x > (uint16_t)(tutorial_farm_tile_x() + 2u)) return 0u;
    if (tile_y < tutorial_farm_tile_y() || tile_y > (uint16_t)(tutorial_farm_tile_y() + 1u)) return 0u;
    return 1u;
}

static void tutorial_collect_gear(uint16_t player_tile_x, uint16_t player_tile_y) {
    if (player_tile_x == tutorial_weapon_tile_x() && player_tile_y == tutorial_weapon_tile_y() && g_weapon_level == 0u) {
        g_weapon_level = 1u;
        audio_sfx_gear_pickup();
        mark_save_dirty();
    }
    if (player_tile_x == tutorial_armor_tile_x() && player_tile_y == tutorial_armor_tile_y() && g_armor_level == 0u) {
        g_armor_level = 1u;
        audio_sfx_gear_pickup();
        mark_save_dirty();
    }
}

uint8_t tutorial_tile_override(uint16_t tile_x, uint16_t tile_y) {
    uint16_t settlement_x;
    uint16_t settlement_y;

    settlement_x = tutorial_settlement_tile_x();
    settlement_y = tutorial_settlement_tile_y();

    if (tile_x == tutorial_raft_tile_x() && tile_y == tutorial_raft_tile_y()) {
        return TILE_RAFT;
    }
    if (tile_x == tutorial_weapon_tile_x() && tile_y == tutorial_weapon_tile_y() && g_weapon_level == 0u) {
        return TILE_RAKE;
    }
    if (tile_x == tutorial_armor_tile_x() && tile_y == tutorial_armor_tile_y() && g_armor_level == 0u) {
        return TILE_ARMOR;
    }
    if (tile_x < g_start_tile_x && abs_u16_diff(tile_y, g_start_tile_y) <= 4u) {
        return TILE_WATER;
    }
    if (tile_x <= (uint16_t)(g_start_tile_x + 5u) && abs_u16_diff(tile_y, g_start_tile_y) <= 3u) {
        return TILE_SAND;
    }
    if (tile_x >= g_start_tile_x && tile_x <= settlement_x && abs_u16_diff(tile_y, g_start_tile_y) <= 1u) {
        return TILE_SAND;
    }
    if (abs_u16_diff(tile_x, tutorial_farm_tile_x()) <= 1u && tile_y >= tutorial_farm_tile_y() && tile_y <= g_start_tile_y) {
        return TILE_SAND;
    }
    if (tutorial_farm_tile(tile_x, tile_y)) {
        return TILE_SOIL;
    }
    if (tutorial_combat_zone(tile_x, tile_y)) {
        if (tile_x == tutorial_combat_tile_x() && tile_y == tutorial_combat_tile_y()) {
            return TILE_CRATER;
        }
        return TILE_SAND;
    }
    if (abs_u16_diff(tile_x, settlement_x) <= 1u && abs_u16_diff(tile_y, settlement_y) <= 1u) {
        return TILE_SAND;
    }
    return 255u;
}

static uint8_t tutorial_objective_tile(void) {
    switch (g_tutorial_stage) {
        case TUTORIAL_STAGE_WAKE:
            return TILE_RAFT;
        case TUTORIAL_STAGE_GEAR:
            return (g_weapon_level == 0u) ? TILE_RAKE : TILE_ARMOR;
        case TUTORIAL_STAGE_COMBAT:
            return TILE_CRATER;
        case TUTORIAL_STAGE_TILL:
            return (g_weapon_level <= g_armor_level) ? TILE_RAKE : TILE_ARMOR;
        case TUTORIAL_STAGE_PLANT:
            return TILE_SITE;
        case TUTORIAL_STAGE_HARVEST:
            return TILE_FEATHER;
        case TUTORIAL_STAGE_BUILD:
            return TILE_SHRINE;
        case TUTORIAL_STAGE_REST:
            return TILE_FEATHER;
        default:
            return TILE_FEATHER;
    }
}

static uint8_t tutorial_progress_tile(void) {
    if (tutorial_complete()) return TILE_FEATHER;
    return (uint8_t)(TILE_BAR0 + ((g_tutorial_stage > 3u) ? 3u : g_tutorial_stage));
}

static void set_tutorial_stage(uint8_t stage) {
    if (stage <= g_tutorial_stage) return;
    g_tutorial_stage = stage;
    if (g_tutorial_stage >= TUTORIAL_STAGE_BUILD && g_wood < 3u) {
        g_wood = 3u;
    }
    if (g_tutorial_stage == TUTORIAL_STAGE_COMPLETE) {
        g_spawn_timer = 120u;
    }
    mark_save_dirty();
}

static uint8_t tutorial_enemy_alive(void) {
    uint8_t index;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        if (!g_enemies[index].active || g_enemies[index].type != ENEMY_KIN) continue;
        if (tutorial_combat_zone((uint16_t)(g_enemies[index].x >> 3u), (uint16_t)(g_enemies[index].y >> 3u))) {
            return 1u;
        }
    }
    return 0u;
}

static void spawn_tutorial_enemy(void) {
    if (tutorial_complete() || tutorial_enemy_alive()) return;
    spawn_impact_enemy(ENEMY_KIN, 0u, (uint16_t)(tutorial_combat_tile_x() * 8u), (uint16_t)(tutorial_combat_tile_y() * 8u));
}

static void update_tutorial_state(void) {
    uint16_t player_tile_x;
    uint16_t player_tile_y;

    if (tutorial_complete()) return;

    player_tile_x = g_player_x >> 3u;
    player_tile_y = g_player_y >> 3u;
    tutorial_collect_gear(player_tile_x, player_tile_y);

    if (g_tutorial_stage == TUTORIAL_STAGE_WAKE) {
        if (player_tile_x != tutorial_raft_tile_x() || player_tile_y != tutorial_raft_tile_y()) {
            set_tutorial_stage(TUTORIAL_STAGE_GEAR);
        }
        return;
    }

    if (g_tutorial_stage == TUTORIAL_STAGE_GEAR) {
        if (g_weapon_level != 0u && g_armor_level != 0u) {
            set_tutorial_stage(TUTORIAL_STAGE_COMBAT);
        }
        return;
    }

    if (g_tutorial_stage == TUTORIAL_STAGE_COMBAT) {
        if (tutorial_combat_zone(player_tile_x, player_tile_y) && !tutorial_enemy_alive()) {
            spawn_tutorial_enemy();
        }
        return;
    }

    if (g_tutorial_stage == TUTORIAL_STAGE_TILL) {
        if (g_weapon_level > 1u || g_armor_level > 1u) {
            set_tutorial_stage(TUTORIAL_STAGE_COMPLETE);
        }
        return;
    }

    if (g_tutorial_stage == TUTORIAL_STAGE_BUILD && g_settlements[0].built) {
        set_tutorial_stage(TUTORIAL_STAGE_REST);
    }
}

static uint8_t tutorial_spawn_pressure(void) {
    if (g_player_field.coherence_state >= 1u) return 1u;
    if (g_player_field.geo.t > 94u) return 1u;
    if (g_player_field.border > 168u) return 1u;
    return 0u;
}

static uint8_t tutorial_spawn_delay(void) {
    if (g_player_field.border > 160u) {
        if (g_player_field.r3 > 128u) return 60u;
        return 90u;
    }
    if (g_player_field.r3 > 128u) return 80u;
    return 110u;
}

static void update_spawn_flow(void) {
    if (!tutorial_complete()) {
        return;
    }

    if (g_spawn_timer > 0u) {
        --g_spawn_timer;
        return;
    }

    if (!g_boss_active && tutorial_spawn_pressure()) {
        if (spawn_daemon_kin()) {
            g_spawn_timer = tutorial_spawn_delay();
        } else {
            g_spawn_timer = 18u;
        }
        return;
    }

    g_spawn_timer = 20u;
}

static void update_phase_flow(void) {
    if (!tutorial_complete()) {
        g_phase_timer = 0u;
        return;
    }

    ++g_phase_timer;
    if (g_phase_timer >= PHASE_LENGTH) {
        g_phase_timer = 0u;
        advance_phase();
    }
}

static uint8_t sign8(int16_t value) {
    if (value < 0) return 0u;
    if (value > 0) return 2u;
    return 1u;
}

uint16_t hash16(uint16_t x, uint16_t y, uint16_t salt) {
    uint16_t value;
    value = (uint16_t)(x * 251u + y * 463u + salt * 199u + 0x9e37u);
    value ^= (uint16_t)(x << 7u);
    value ^= (uint16_t)(y << 3u);
    value = (uint16_t)(value * 109u + 89u);
    value ^= (value >> 7u);
    value = (uint16_t)(value * 157u + 17u);
    return value;
}

uint16_t approx_disc_distance(uint16_t tile_x, uint16_t tile_y) {
    uint16_t dx;
    uint16_t dy;
    uint16_t hi;
    uint16_t lo;
    dx = abs_u16_diff(tile_x, DISC_CENTER_TILE);
    dy = abs_u16_diff(tile_y, DISC_CENTER_TILE);
    hi = (dx > dy) ? dx : dy;
    lo = (dx > dy) ? dy : dx;
    return (uint16_t)(hi + (lo >> 1u));
}

uint8_t border_pressure(uint16_t distance) {
    uint32_t scaled;
    if (distance <= DISC_SAFE_RADIUS) return 0u;
    if (distance >= DISC_HARD_RADIUS) return 255u;
    scaled = (uint32_t)(distance - DISC_SAFE_RADIUS) * 255u;
    scaled /= (uint32_t)(DISC_HARD_RADIUS - DISC_SAFE_RADIUS);
    return (uint8_t)scaled;
}

static uint8_t weighted5(uint8_t a, uint8_t wa, uint8_t b, uint8_t wb, uint8_t c, uint8_t wc, uint8_t d, uint8_t wd, uint8_t e, uint8_t we) {
    uint16_t sum;
    sum = (uint16_t)a * wa + (uint16_t)b * wb + (uint16_t)c * wc + (uint16_t)d * wd + (uint16_t)e * we;
    return (uint8_t)(sum / 100u);
}

static uint8_t weighted4(uint8_t a, uint8_t wa, uint8_t b, uint8_t wb, uint8_t c, uint8_t wc, uint8_t d, uint8_t wd) {
    uint16_t sum;
    sum = (uint16_t)a * wa + (uint16_t)b * wb + (uint16_t)c * wc + (uint16_t)d * wd;
    return (uint8_t)(sum / 100u);
}

static uint8_t normalize_channel(uint16_t value, uint16_t total) {
    if (total == 0u) return 0u;
    return (uint8_t)((value * 255u) / total);
}

uint8_t calc_x(const FarmerVector *c) {
    return weighted5(c->A, 30u, c->gC, 25u, c->gW, 20u, c->gU, 15u, c->gZ, 10u);
}

uint16_t calc_i(const FarmerVector *c) {
    uint16_t base;
    base = 256u;
    base += ((uint16_t)c->gSg * 35u) / 100u;
    base += ((uint16_t)c->K * 25u) / 100u;
    base += ((uint16_t)c->B * 20u) / 100u;
    base += ((uint16_t)c->L * 20u) / 100u;
    return base;
}

uint8_t calc_coh_floor(const FarmerVector *c) {
    int16_t value;
    value = 87;
    value += ((int16_t)c->emb * 14) / 100;
    value += ((int16_t)c->frag * 16) / 100;
    value += ((int16_t)c->inst * 10) / 100;
    value += ((int16_t)c->hs_b * 10) / 100;
    value += ((int16_t)c->hs_g * 12) / 100;
    value -= ((int16_t)c->hs_a * 10) / 100;
    return clamp_u8(value);
}

void calc_bands(const FarmerVector *c, const Ens *y, int16_t psi, uint8_t h_obs, Bands *bands) {
    uint8_t psi_norm;
    psi_norm = clamp_u8((psi + 255) / 2);
    bands->con = clamp_u8(weighted4(y->Br, 40u, c->emb, 25u, c->hs_b, 20u, y->Cl, 15u));
    bands->ctr = clamp_u8(weighted4(y->Wc, 35u, c->lang, 30u, c->inst, 20u, (uint8_t)(255u - y->Br), 15u));
    bands->itv = clamp_u8(weighted4((uint8_t)(255u - y->Br), 35u, c->cult, 25u, c->dev, 20u, c->hs_a, 20u));
    bands->can = clamp_u8(weighted4(y->Wc, 40u, c->ext, 25u, (uint8_t)(255u - c->frag), 20u, psi_norm, 15u));
    bands->obs = clamp_u8(weighted4(h_obs, 45u, c->hs_g, 35u, y->Mh, 20u, 0u, 0u));
}

uint8_t calc_tension(const FarmerVector *c, const Ens *y) {
    return weighted4(y->Mh, 40u, y->Br, 25u, y->Cl, 20u, c->hs_g, 15u);
}

uint8_t calc_phi(const Bands *bands, uint8_t tension) {
    int16_t phi;
    phi = ((int16_t)bands->con * 22) / 100;
    phi += ((int16_t)bands->ctr * 18) / 100;
    phi += ((int16_t)bands->itv * 18) / 100;
    phi += ((int16_t)bands->can * 20) / 100;
    phi += ((int16_t)bands->obs * 22) / 100;
    phi -= ((int16_t)tension * 20) / 100;
    return clamp_u8(phi);
}

static uint8_t min_band(const Bands *bands) {
    uint8_t minimum;
    minimum = bands->con;
    if (bands->ctr < minimum) minimum = bands->ctr;
    if (bands->itv < minimum) minimum = bands->itv;
    if (bands->can < minimum) minimum = bands->can;
    if (bands->obs < minimum) minimum = bands->obs;
    return minimum;
}

uint8_t calc_coh_state(uint8_t phi, uint8_t floor_value, const Bands *bands) {
    uint8_t band_min;
    band_min = min_band(bands);
    if ((phi + 36u) < floor_value || band_min < 26u) return 3u;
    if ((phi + 15u) < floor_value || band_min < 52u) return 2u;
    if (phi < floor_value || band_min < 72u) return 1u;
    return 0u;
}

void calc_geography(const Ens *y, uint8_t delta, Bary *geo) {
    uint16_t h;
    uint16_t c;
    uint16_t t;
    uint16_t sum;
    h = ((uint16_t)y->Wc * 45u) / 100u;
    h += ((uint16_t)y->Br * 35u) / 100u;
    h += ((uint16_t)(255u - y->Cp) * 20u) / 100u;
    c = ((uint16_t)y->Cp * 40u) / 100u;
    c += ((uint16_t)y->Cl * 35u) / 100u;
    c += ((uint16_t)y->Ep * 25u) / 100u;
    t = ((uint16_t)y->Mh * 40u) / 100u;
    t += ((uint16_t)y->Ep * 30u) / 100u;
    t += ((uint16_t)delta * 30u) / 100u;
    sum = h + c + t + 1u;
    geo->h = normalize_channel(h, sum);
    geo->c = normalize_channel(c, sum);
    geo->t = normalize_channel(t, sum);
}

uint8_t calc_irv(const Ens *y, uint8_t xi) {
    return weighted5(y->Ep, 30u, y->Cp, 25u, y->Cl, 15u, y->Mh, 15u, xi, 15u);
}

void calc_objects(const Bary *geo, const Ens *y, uint8_t irv, uint8_t delta, ObjStrata *objects) {
    objects->Os = weighted4(geo->h, 50u, y->Br, 30u, (uint8_t)(255u - y->Cl), 20u, 0u, 0u);
    objects->Oc = weighted4(geo->c, 50u, irv, 30u, y->Ep, 20u, 0u, 0u);
    objects->Oo = weighted4(geo->t, 50u, y->Mh, 30u, delta, 20u, 0u, 0u);
}

void calc_race(const Ens *y, uint8_t rt, RaceResult *race) {
    uint8_t goal;
    uint8_t foul;
    uint16_t total;
    goal = weighted4(y->Wc, 40u, y->Br, 20u, g_farmer.A, 20u, g_farmer.L, 20u);
    foul = weighted4(y->Cp, 35u, y->Mh, 25u, rt, 20u, g_farmer.B, 20u);
    total = goal + foul + 1u;
    race->Pgoal = goal;
    race->Pfoul = foul;
    race->Gw = (uint8_t)(((uint16_t)goal * 255u) / total);
    race->Psi = (int16_t)goal - (int16_t)foul;
}

uint8_t calc_dominion(const Bary *geo, const Ens *y, uint8_t gw, uint8_t rt) {
    return weighted5(geo->c, 34u, y->Ep, 24u, y->Cl, 18u, gw, 14u, rt, 10u);
}

void calc_rest(const Bary *geo, uint8_t dom, Bary *rest) {
    uint16_t rh;
    uint16_t rc;
    uint16_t rt;
    uint16_t sum;
    rh = geo->h + ((uint16_t)dom * 20u) / 100u;
    rc = geo->c + ((uint16_t)dom * 45u) / 100u;
    rt = geo->t + ((uint16_t)dom * 15u) / 100u;
    sum = rh + rc + rt + 1u;
    rest->h = normalize_channel(rh, sum);
    rest->c = normalize_channel(rc, sum);
    rest->t = normalize_channel(rt, sum);
}

void calc_tiers(const Ens *y, const Bary *geo, uint8_t gw, Tiers *tiers) {
    tiers->id = weighted4(y->Br, 45u, y->Mh, 30u, geo->t, 25u, 0u, 0u);
    tiers->ego = weighted4(y->Wc, 40u, gw, 30u, geo->h, 30u, 0u, 0u);
    tiers->sup = weighted4(y->Cp, 40u, y->Cl, 35u, geo->c, 25u, 0u, 0u);
}

void calc_hyper3(const Bary *geo, const Ens *y, uint8_t dom, uint8_t gw, uint8_t rt, int16_t psi, Hyper3 *hyper) {
    uint8_t psi_norm;
    psi_norm = clamp_u8((psi + 255) / 2);
    hyper->kin = weighted4(geo->h, 45u, y->Br, 25u, y->Wc, 20u, psi_norm, 10u);
    hyper->dom = weighted4(dom, 40u, y->Cp, 25u, y->Ep, 20u, gw, 15u);
    hyper->obs = weighted4(y->Mh, 40u, geo->t, 25u, rt, 20u, (uint8_t)(255u - y->Cl), 15u);
}

uint8_t calc_hyperself(const FarmerVector *c, const Hyper3 *hyper) {
    uint16_t sum;
    sum = ((uint16_t)hyper->kin * c->hs_a) / 255u;
    sum += ((uint16_t)hyper->dom * c->hs_b) / 255u;
    sum += ((uint16_t)hyper->obs * c->hs_g) / 255u;
    return (uint8_t)sum;
}

uint8_t relative3_scalar(uint8_t q, uint8_t f, uint8_t s, uint8_t r, uint8_t g) {
    uint8_t values[4];
    uint8_t distances[4];
    uint8_t worst;
    uint16_t sum;
    uint8_t count;
    uint8_t index;
    values[0] = f;
    values[1] = s;
    values[2] = r;
    values[3] = g;
    for (index = 0u; index < 4u; ++index) {
        distances[index] = abs_u8_diff(q, values[index]);
    }
    worst = 0u;
    for (index = 1u; index < 4u; ++index) {
        if (distances[index] > distances[worst]) {
            worst = index;
        }
    }
    sum = 0u;
    count = 0u;
    for (index = 0u; index < 4u; ++index) {
        if (index == worst) continue;
        sum += (uint16_t)(255u - distances[index]);
        ++count;
    }
    return (uint8_t)(sum / count);
}

static void clear_dynamic_state(void) {
    uint8_t index;
    for (index = 0u; index < MAX_PLOTS; ++index) {
        g_plots[index].active = 0u;
    }
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        g_enemies[index].active = 0u;
    }
    for (index = 0u; index < MAX_IMPACTS; ++index) {
        g_impacts[index].active = 0u;
    }
    for (index = 0u; index < MAX_PROJECTILES; ++index) {
        g_projectiles[index].active = 0u;
    }
}

static void clear_threat_state(void) {
    uint8_t index;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        g_enemies[index].active = 0u;
    }
    for (index = 0u; index < MAX_IMPACTS; ++index) {
        g_impacts[index].active = 0u;
    }
    for (index = 0u; index < MAX_PROJECTILES; ++index) {
        g_projectiles[index].active = 0u;
    }
}

static void clear_kin_enemies(void) {
    uint8_t index;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        if (g_enemies[index].active && g_enemies[index].type == ENEMY_KIN) {
            g_enemies[index].active = 0u;
        }
    }
}

static void reset_camera_stream_state(void) {
    g_old_map_pos_x = 0xFFFFu;
    g_old_map_pos_y = 0xFFFFu;
    g_redraw = 1u;
}

static void place_player_at_start(void) {
    g_player_x = (uint16_t)(g_start_tile_x * 8u);
    g_player_y = (uint16_t)(g_start_tile_y * 8u);
}

static void select_disc_point(uint16_t salt, uint16_t min_radius, uint16_t max_radius, uint16_t *tile_x_out, uint16_t *tile_y_out) {
    uint8_t attempt;
    for (attempt = 0u; attempt < 96u; ++attempt) {
        uint16_t sx;
        uint16_t sy;
        int16_t off_x;
        int16_t off_y;
        uint16_t candidate_x;
        uint16_t candidate_y;
        uint16_t distance;
        sx = hash16((uint16_t)(salt + (uint16_t)attempt * 17u), (uint16_t)(g_world_seed + 53u), 0x1234u);
        sy = hash16((uint16_t)(salt + (uint16_t)attempt * 31u), (uint16_t)(g_world_seed + 97u), 0x4321u);
        off_x = (int16_t)(sx & 0x0FFFu) - 2048;
        off_y = (int16_t)(sy & 0x0FFFu) - 2048;
        candidate_x = (uint16_t)((int16_t)DISC_CENTER_TILE + off_x);
        candidate_y = (uint16_t)((int16_t)DISC_CENTER_TILE + off_y);
        distance = approx_disc_distance(candidate_x, candidate_y);
        if (distance < min_radius || distance > max_radius) continue;
        *tile_x_out = candidate_x;
        *tile_y_out = candidate_y;
        return;
    }
    *tile_x_out = DISC_CENTER_TILE;
    *tile_y_out = DISC_CENTER_TILE;
}

static uint8_t settlement_too_close(uint16_t tile_x, uint16_t tile_y, uint8_t count) {
    uint8_t index;
    if (abs_u16_diff(tile_x, g_start_tile_x) < 64u && abs_u16_diff(tile_y, g_start_tile_y) < 48u) return 1u;
    if (abs_u16_diff(tile_x, g_shrine_tile_x) < 32u && abs_u16_diff(tile_y, g_shrine_tile_y) < 32u) return 1u;
    for (index = 0u; index < count; ++index) {
        if (abs_u16_diff(tile_x, g_settlements[index].tile_x) < 28u && abs_u16_diff(tile_y, g_settlements[index].tile_y) < 28u) {
            return 1u;
        }
    }
    return 0u;
}

static void generate_static_anchors(void) {
    int16_t start_y_offset;
    g_start_tile_x = (uint16_t)(DISC_CENTER_TILE - DISC_RADIUS_TILES + 58u + (g_world_seed & 0x07u));
    start_y_offset = (int16_t)((g_world_seed >> 5u) & 0x1Fu) - 16;
    g_start_tile_y = (uint16_t)((int16_t)DISC_CENTER_TILE + start_y_offset);
    select_disc_point(0xB00Bu, 420u, 1100u, &g_shrine_tile_x, &g_shrine_tile_y);
}

static void build_settlement_sites(void) {
    uint8_t index;
    g_settlements[0].active = 1u;
    g_settlements[0].built = 0u;
    g_settlements[0].feather_ready = 0u;
    g_settlements[0].tile_x = tutorial_settlement_tile_x();
    g_settlements[0].tile_y = tutorial_settlement_tile_y();

    for (index = 1u; index < MAX_SETTLEMENTS; ++index) {
        uint8_t attempt;
        uint16_t candidate_x;
        uint16_t candidate_y;
        candidate_x = DISC_CENTER_TILE;
        candidate_y = DISC_CENTER_TILE;
        for (attempt = 0u; attempt < 80u; ++attempt) {
            select_disc_point((uint16_t)(0x410u + (uint16_t)index * 97u + (uint16_t)attempt * 7u), 220u, 1320u, &candidate_x, &candidate_y);
            if (!settlement_too_close(candidate_x, candidate_y, index)) {
                break;
            }
        }
        g_settlements[index].active = 1u;
        g_settlements[index].built = 0u;
        g_settlements[index].feather_ready = 0u;
        g_settlements[index].tile_x = candidate_x;
        g_settlements[index].tile_y = candidate_y;
    }
}

static uint16_t compute_slot_checksum(const SaveSlot *slot) {
    const uint8_t *bytes;
    uint16_t sum;
    uint16_t index;
    bytes = (const uint8_t *)slot;
    sum = 0xA55Au;
    for (index = 0u; index < (uint16_t)(sizeof(SaveSlot) - sizeof(slot->checksum)); ++index) {
        sum = (uint16_t)((sum << 1u) | (sum >> 15u));
        sum ^= (uint16_t)bytes[index];
        sum = (uint16_t)(sum + 0x3Du);
    }
    return sum;
}

static uint8_t slot_is_valid(const SaveSlot *slot, uint8_t profile_index) {
    if (slot->magic != SAVE_MAGIC) return 0u;
    if (slot->version != SAVE_VERSION) return 0u;
    if (slot->slot_index != profile_index) return 0u;
    if (slot->checksum != compute_slot_checksum(slot)) return 0u;
    return 1u;
}

uint8_t profile_has_data(uint8_t profile_index) {
    SaveSlot slot;
    ENABLE_RAM;
    SWITCH_RAM(0);
    memcpy(&slot, &g_save_slots[profile_index], sizeof(SaveSlot));
    DISABLE_RAM;
    return slot_is_valid(&slot, profile_index);
}

void erase_profile_slot(uint8_t profile_index) {
    SaveSlot slot;
    memset(&slot, 0, sizeof(SaveSlot));
    ENABLE_RAM;
    SWITCH_RAM(0);
    memcpy(&g_save_slots[profile_index], &slot, sizeof(SaveSlot));
    DISABLE_RAM;
}

static void mark_save_dirty(void) {
    g_save_dirty = 1u;
    g_save_cooldown = SAVE_DELAY_FRAMES;
}

static void init_new_profile(uint8_t profile_index) {
    g_profile_index = profile_index;
    g_world_seed = kProfileSeeds[g_profile_index % SAVE_PROFILE_COUNT];
    g_farmer = kDefaultFarmer;
    generate_static_anchors();
    build_settlement_sites();
    clear_dynamic_state();
    place_player_at_start();
    g_health = 3u;
    g_max_health = 3u;
    g_wood = 0u;
    g_grain = 1u;
    g_level = 1u;
    g_xp = 0u;
    g_phase = 0u;
    g_phase_timer = 0u;
    g_boss_active = 0u;
    g_boss_defeated = 0u;
    g_weapon_level = 0u;
    g_armor_level = 0u;
    g_attack_timer = 0u;
    g_invuln_timer = 0u;
    g_spawn_timer = 120u;
    g_walk_anim_frame = 0u;
    g_move_anim_timer = 0u;
    g_tutorial_stage = TUTORIAL_STAGE_WAKE;
    g_tutorial_overlay_enabled = 0u;
    g_camera_x = 0u;
    g_camera_y = 0u;
    g_old_camera_x = 0u;
    g_old_camera_y = 0u;
    reset_camera_stream_state();
    g_save_dirty = 0u;
    g_save_cooldown = 0u;
    audio_reset_runtime();
    passage_modules_begin_session(g_world_seed, g_level, g_weapon_level, g_armor_level);
}

static void save_profile_now(void) {
    SaveSlot slot;
    memset(&slot, 0, sizeof(SaveSlot));
    slot.magic = SAVE_MAGIC;
    slot.version = SAVE_VERSION;
    slot.slot_index = g_profile_index;
    slot.world_seed = g_world_seed;
    slot.player_x = g_player_x;
    slot.player_y = g_player_y;
    slot.phase_timer = (uint16_t)((g_phase_timer & PHASE_TIMER_STORAGE_MASK) | ((uint16_t)g_tutorial_stage << 9u));
    slot.health = g_health;
    slot.max_health = g_max_health;
    slot.wood = g_wood;
    slot.grain = g_grain;
    slot.level = g_level;
    slot.xp = g_xp;
    slot.phase = g_phase;
    slot.boss_active = g_boss_active;
    slot.boss_defeated = g_boss_defeated;
    slot.weapon_level = g_weapon_level;
    slot.armor_level = g_armor_level;
    memcpy(&slot.farmer, &g_farmer, sizeof(FarmerVector));
    memcpy(slot.settlements, g_settlements, sizeof(g_settlements));
    memcpy(slot.plots, g_plots, sizeof(g_plots));
    slot.checksum = compute_slot_checksum(&slot);

    ENABLE_RAM;
    SWITCH_RAM(0);
    memcpy(&g_save_slots[g_profile_index], &slot, sizeof(SaveSlot));
    DISABLE_RAM;

    g_save_dirty = 0u;
    g_save_cooldown = 0u;
}

static void maybe_autosave(void) {
    if (!g_save_dirty) return;
    if (g_save_cooldown > 0u) {
        --g_save_cooldown;
    } else {
        audio_sfx_autosave();
        save_profile_now();
    }
}

static uint8_t load_profile(uint8_t profile_index) {
    SaveSlot slot;
    uint8_t migrated_tutorial_state;
    ENABLE_RAM;
    SWITCH_RAM(0);
    memcpy(&slot, &g_save_slots[profile_index], sizeof(SaveSlot));
    DISABLE_RAM;
    if (!slot_is_valid(&slot, profile_index)) {
        return 0u;
    }

    g_profile_index = profile_index;
    migrated_tutorial_state = 0u;
    g_world_seed = slot.world_seed;
    memcpy(&g_farmer, &slot.farmer, sizeof(FarmerVector));
    generate_static_anchors();
    clear_dynamic_state();
    memcpy(g_settlements, slot.settlements, sizeof(g_settlements));
    memcpy(g_plots, slot.plots, sizeof(g_plots));
    g_player_x = slot.player_x;
    g_player_y = slot.player_y;
    g_health = slot.health;
    g_max_health = slot.max_health;
    g_wood = slot.wood;
    g_grain = slot.grain;
    g_level = slot.level;
    g_xp = slot.xp;
    g_phase = slot.phase;
    g_phase_timer = (uint16_t)(slot.phase_timer & PHASE_TIMER_STORAGE_MASK);
    g_tutorial_stage = (uint8_t)(slot.phase_timer >> 9u);
    if (g_tutorial_stage > TUTORIAL_STAGE_COMPLETE) {
        g_tutorial_stage = TUTORIAL_STAGE_COMPLETE;
    }
    g_boss_active = slot.boss_active;
    g_boss_defeated = slot.boss_defeated;
    g_weapon_level = slot.weapon_level;
    g_armor_level = slot.armor_level;
    g_attack_timer = 0u;
    g_invuln_timer = 0u;
    g_spawn_timer = 90u;
    g_walk_anim_frame = 0u;
    g_move_anim_timer = 0u;
    g_camera_x = 0u;
    g_camera_y = 0u;
    g_old_camera_x = 0u;
    g_old_camera_y = 0u;
    reset_camera_stream_state();
    g_save_dirty = 0u;
    g_save_cooldown = 0u;
    audio_reset_runtime();
    g_tutorial_overlay_enabled = 0u;
    passage_modules_begin_session(g_world_seed, g_level, g_weapon_level, g_armor_level);
    if (g_tutorial_stage == TUTORIAL_STAGE_WAKE && (count_built_settlements() > 0u || g_level > 1u || g_xp > 0u || g_phase != 0u || g_boss_active || g_boss_defeated || g_wood != 0u || g_grain != 1u || g_weapon_level != 0u || g_armor_level != 0u)) {
        g_tutorial_stage = TUTORIAL_STAGE_COMPLETE;
        migrated_tutorial_state = 1u;
    }
    if (migrated_tutorial_state) {
        mark_save_dirty();
    }
    return 1u;
}

static uint8_t count_built_settlements(void) {
    uint8_t count;
    uint8_t index;
    count = 0u;
    for (index = 0u; index < MAX_SETTLEMENTS; ++index) {
        if (g_settlements[index].active && g_settlements[index].built) {
            ++count;
        }
    }
    return count;
}

static uint8_t count_ready_feathers(void) {
    uint8_t count;
    uint8_t index;
    count = 0u;
    for (index = 0u; index < MAX_SETTLEMENTS; ++index) {
        if (g_settlements[index].active && g_settlements[index].built && g_settlements[index].feather_ready) {
            ++count;
        }
    }
    return count;
}

uint8_t find_settlement_at(uint16_t tile_x, uint16_t tile_y) {
    uint8_t index;
    for (index = 0u; index < MAX_SETTLEMENTS; ++index) {
        if (g_settlements[index].active && g_settlements[index].tile_x == tile_x && g_settlements[index].tile_y == tile_y) {
            return index;
        }
    }
    return 255u;
}

static uint8_t find_nearest_built_settlement(uint16_t tile_x, uint16_t tile_y) {
    uint8_t index;
    uint8_t best_index;
    uint16_t best_cost;
    best_index = 255u;
    best_cost = 0xFFFFu;
    for (index = 0u; index < MAX_SETTLEMENTS; ++index) {
        uint16_t cost;
        if (!g_settlements[index].active || !g_settlements[index].built) continue;
        cost = abs_u16_diff(tile_x, g_settlements[index].tile_x) + abs_u16_diff(tile_y, g_settlements[index].tile_y);
        if (cost < best_cost) {
            best_cost = cost;
            best_index = index;
        }
    }
    return best_index;
}

static uint8_t audio_world_track(void) {
    uint8_t settlement_index;
    if (g_boss_active) return AUDIO_TRACK_BOSS;
    settlement_index = find_settlement_at((uint16_t)(g_player_x >> 3u), (uint16_t)(g_player_y >> 3u));
    if (settlement_index != 255u && g_settlements[settlement_index].built) {
        return AUDIO_TRACK_SETTLEMENT;
    }
    if (g_player_field.border > 160u) {
        return AUDIO_TRACK_OUTER_RIM;
    }
    return AUDIO_TRACK_SAFE_FIELDS;
}



static uint8_t tile_passable(uint16_t tile_x, uint16_t tile_y) {
    uint8_t tile_value;
    tile_value = world_tile_at(tile_x, tile_y);
    if (tile_value == TILE_WATER) return 0u;
    if (tile_value == TILE_TREE) return 0u;
    if (tile_value == TILE_ROCK) return 0u;
    return 1u;
}

static void fill_row_buffer(uint16_t world_x, uint16_t world_y, uint8_t width) {
    uint8_t index;
    for (index = 0u; index < width; ++index) {
        g_row_buffer[index] = world_tile_at((uint16_t)(world_x + index), world_y);
    }
}

static void fill_col_buffer(uint16_t world_x, uint16_t world_y, uint8_t height) {
    uint8_t index;
    for (index = 0u; index < height; ++index) {
        g_col_buffer[index] = world_tile_at(world_x, (uint16_t)(world_y + index));
    }
}

static void draw_full_view(void) {
    uint16_t start_x;
    uint16_t start_y;
    uint8_t row;
    start_x = g_camera_x >> 3u;
    start_y = g_camera_y >> 3u;
    for (row = 0u; row < STREAM_TILE_H; ++row) {
        fill_row_buffer(start_x, (uint16_t)(start_y + row), STREAM_TILE_W);
        set_bkg_tiles((uint8_t)(start_x & 31u), (uint8_t)((start_y + row) & 31u), STREAM_TILE_W, 1u, g_row_buffer);
    }
}

static void update_camera_stream(void) {
    uint16_t incoming_row;
    uint16_t incoming_col;
    uint16_t start_x;
    uint16_t start_y;

    move_bkg((uint8_t)g_camera_x, (uint8_t)g_camera_y);
    g_map_pos_y = g_camera_y >> 3u;
    start_x = g_camera_x >> 3u;
    if (g_map_pos_y != g_old_map_pos_y) {
        incoming_row = (g_camera_y < g_old_camera_y) ? g_map_pos_y : (uint16_t)(g_map_pos_y + SCREEN_TILE_H);
        fill_row_buffer(start_x, incoming_row, STREAM_TILE_W);
        set_bkg_tiles((uint8_t)(start_x & 31u), (uint8_t)(incoming_row & 31u), STREAM_TILE_W, 1u, g_row_buffer);
        g_old_map_pos_y = g_map_pos_y;
    }

    g_map_pos_x = g_camera_x >> 3u;
    start_y = g_camera_y >> 3u;
    if (g_map_pos_x != g_old_map_pos_x) {
        incoming_col = (g_camera_x < g_old_camera_x) ? g_map_pos_x : (uint16_t)(g_map_pos_x + SCREEN_TILE_W);
        fill_col_buffer(incoming_col, start_y, STREAM_TILE_H);
        set_bkg_tiles((uint8_t)(incoming_col & 31u), (uint8_t)(start_y & 31u), 1u, STREAM_TILE_H, g_col_buffer);
        g_old_map_pos_x = g_map_pos_x;
    }

    g_old_camera_x = g_camera_x;
    g_old_camera_y = g_camera_y;
}

static void refresh_camera(void) {
    if (g_old_map_pos_x == 0xFFFFu || g_old_map_pos_y == 0xFFFFu) {
        draw_full_view();
        move_bkg((uint8_t)g_camera_x, (uint8_t)g_camera_y);
        g_map_pos_x = g_camera_x >> 3u;
        g_map_pos_y = g_camera_y >> 3u;
        g_old_map_pos_x = g_map_pos_x;
        g_old_map_pos_y = g_map_pos_y;
        g_old_camera_x = g_camera_x;
        g_old_camera_y = g_camera_y;
    } else {
        update_camera_stream();
    }
}

static void follow_player(void) {
    uint16_t target_x;
    uint16_t target_y;
    target_x = (g_player_x > PLAYER_CENTER_X) ? (g_player_x - PLAYER_CENTER_X) : 0u;
    target_y = (g_player_y > PLAYER_CENTER_Y) ? (g_player_y - PLAYER_CENTER_Y) : 0u;
    if (target_x > CAMERA_MAX_X) target_x = CAMERA_MAX_X;
    if (target_y > CAMERA_MAX_Y) target_y = CAMERA_MAX_Y;
    if (target_x != g_camera_x || target_y != g_camera_y) {
        g_camera_x = target_x;
        g_camera_y = target_y;
        g_redraw = 1u;
    }
}

static void move_player_sprite(void) {
    uint8_t screen_x;
    uint8_t screen_y;
    uint8_t tile_index;
    screen_x = (uint8_t)(g_player_x - g_camera_x) + 8u;
    screen_y = (uint8_t)(g_player_y - g_camera_y) + 16u;
    tile_index = 0u;
    if (g_attack_timer > 6u) {
        tile_index = 2u;
    } else if (g_attack_timer != 0u) {
        tile_index = 3u;
    } else if (g_move_anim_timer != 0u && g_walk_anim_frame != 0u) {
        tile_index = 1u;
        ++screen_y;
    }
    move_sprite(0u, screen_x, screen_y);
    set_sprite_tile(0u, tile_index);
}

static void hide_unused_sprites(void) {
    uint8_t index;
    for (index = 1u; index < TOTAL_ACTION_SPRITES; ++index) {
        move_sprite(index, 0u, 0u);
    }
}

static uint8_t active_boss_hp(void) {
    uint8_t index;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        if (g_enemies[index].active && g_enemies[index].type == ENEMY_BOSS) {
            return g_enemies[index].hp;
        }
    }
    return 0u;
}

static uint8_t active_boss_poise(void) {
    uint8_t index;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        if (g_enemies[index].active && g_enemies[index].type == ENEMY_BOSS) {
            return g_enemies[index].poise;
        }
    }
    return 0u;
}

static uint8_t enemy_damage_level(const Enemy *enemy) {
    uint8_t missing;
    if (enemy->max_hp == 0u || enemy->hp >= enemy->max_hp) {
        return 0u;
    }
    missing = (uint8_t)(enemy->max_hp - enemy->hp);
    if (missing >= (uint8_t)(enemy->max_hp - 1u)) {
        return 3u;
    }
    return (uint8_t)(1u + ((missing * 2u) / enemy->max_hp));
}

static uint8_t enemy_visual_tile(const Enemy *enemy, uint8_t index) {
    uint8_t damage_level;
    uint8_t phase;
    uint8_t tile;

    damage_level = enemy_damage_level(enemy);
    phase = (uint8_t)((g_frame_counter + enemy->visual_seed + enemy->damage_mark + (index * 13u)) & 0x03u);
    tile = (enemy->type == ENEMY_BOSS) ? 5u : 4u;

    if (damage_level == 0u) {
        if (enemy->state == AI_LUNGE && phase >= 2u) {
            return (enemy->type == ENEMY_BOSS) ? 7u : 6u;
        }
        return tile;
    }

    if (enemy->type == ENEMY_BOSS) {
        if (damage_level >= 3u) {
            tile = (phase & 1u) ? 6u : 7u;
        } else if (damage_level >= 2u) {
            tile = (phase <= 1u) ? 7u : 5u;
        } else {
            tile = (phase == 0u) ? 6u : 5u;
        }
    } else {
        if (damage_level >= 3u) {
            tile = (phase & 1u) ? 7u : 6u;
        } else if (damage_level >= 2u) {
            tile = (phase <= 1u) ? 6u : 7u;
        } else {
            tile = (phase == 0u) ? 6u : 4u;
        }
    }

    if (enemy->damage_flash != 0u) {
        if (((g_frame_counter + index + enemy->damage_mark) & 1u) != 0u) {
            tile = (tile == 6u) ? 7u : 6u;
        }
    }
    return tile;
}

static int8_t enemy_damage_jitter(const Enemy *enemy, uint8_t index, uint8_t axis_bias) {
    uint8_t phase;
    if (enemy->damage_flash == 0u) {
        return 0;
    }
    phase = (uint8_t)((g_frame_counter + enemy->visual_seed + enemy->damage_mark + (index * 11u) + axis_bias) & 0x03u);
    if (phase == 0u) return -1;
    if (phase == 2u) return 1;
    return 0;
}

static void render_enemies(void) {
    uint8_t index;
    uint8_t sprite_id;
    sprite_id = 1u;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        if (!g_enemies[index].active) continue;
        if (sprite_id > MAX_ENEMIES) break;
        {
            uint8_t screen_x;
            uint8_t screen_y;
            int16_t jittered_x;
            int16_t jittered_y;
            jittered_x = (int16_t)((uint8_t)(g_enemies[index].x - g_camera_x) + 8u) + enemy_damage_jitter(&g_enemies[index], index, 3u);
            jittered_y = (int16_t)((uint8_t)(g_enemies[index].y - g_camera_y) + 16u) + enemy_damage_jitter(&g_enemies[index], index, 9u);
            screen_x = (uint8_t)jittered_x;
            screen_y = (uint8_t)jittered_y;
            if (screen_x < 8u || screen_x > 168u || screen_y < 16u || screen_y > 152u) {
                move_sprite(sprite_id, 0u, 0u);
            } else {
                move_sprite(sprite_id, screen_x, screen_y);
                set_sprite_tile(sprite_id, enemy_visual_tile(&g_enemies[index], index));
            }
        }
        ++sprite_id;
    }
    while (sprite_id <= MAX_ENEMIES) {
        move_sprite(sprite_id, 0u, 0u);
        ++sprite_id;
    }
}

static void render_projectiles(void) {
    uint8_t index;
    for (index = 0u; index < MAX_PROJECTILES; ++index) {
        uint8_t sprite_id;
        sprite_id = (uint8_t)(PROJECTILE_SPRITE_BASE + index);
        if (!g_projectiles[index].active) {
            move_sprite(sprite_id, 0u, 0u);
            continue;
        }
        {
            uint8_t screen_x;
            uint8_t screen_y;
            screen_x = (uint8_t)(g_projectiles[index].x - g_camera_x) + 8u;
            screen_y = (uint8_t)(g_projectiles[index].y - g_camera_y) + 16u;
            if (screen_x < 8u || screen_x > 168u || screen_y < 16u || screen_y > 152u) {
                move_sprite(sprite_id, 0u, 0u);
            } else {
                move_sprite(sprite_id, screen_x, screen_y);
                set_sprite_tile(sprite_id, g_projectiles[index].tile_index);
            }
        }
    }
}

static void update_hud(void) {
    uint8_t index;
    uint8_t built;
    uint8_t ready;
    uint8_t boss_hp;
    uint8_t boss_poise;
    for (index = 0u; index < 40u; ++index) {
        g_hud_map[index] = TILE_BLANK;
    }
    for (index = 0u; index < g_max_health; ++index) {
        g_hud_map[index] = (index < g_health) ? TILE_HEART_FULL : TILE_HEART_EMPTY;
    }
    g_hud_map[5] = (uint8_t)(TILE_MOON0 + (g_phase & 0x07u));
    g_hud_map[7] = g_boss_active ? TILE_CRATER : TILE_BLANK;
    boss_hp = active_boss_hp();
    boss_poise = active_boss_poise();
    g_hud_map[8] = (uint8_t)(TILE_BAR0 + ((boss_hp > 3u) ? 3u : boss_hp));
    g_hud_map[9] = (uint8_t)(TILE_BAR0 + ((boss_poise > 3u) ? 3u : boss_poise));
    g_hud_map[11] = (uint8_t)(TILE_BAR0 + (g_player_field.border >> 6u));
    g_hud_map[12] = tutorial_objective_tile();
    g_hud_map[13] = tutorial_progress_tile();
    g_hud_map[14] = (g_attack_timer != 0u) ? TILE_CRATER : TILE_BLANK;
    g_hud_map[15] = TILE_RAKE;
    g_hud_map[16] = (uint8_t)(TILE_BAR0 + ((g_weapon_level > 3u) ? 3u : g_weapon_level));
    g_hud_map[17] = TILE_ARMOR;
    g_hud_map[18] = (uint8_t)(TILE_BAR0 + ((g_armor_level > 3u) ? 3u : g_armor_level));

    built = count_built_settlements();
    ready = count_ready_feathers();
    g_hud_map[20] = TILE_SEED_ICON;
    g_hud_map[21] = (uint8_t)(TILE_BAR0 + ((g_grain > 3u) ? 3u : g_grain));
    g_hud_map[23] = TILE_HUT;
    g_hud_map[24] = (uint8_t)(TILE_BAR0 + ((built > 3u) ? 3u : built));
    g_hud_map[26] = TILE_FEATHER;
    g_hud_map[27] = (uint8_t)(TILE_BAR0 + ((ready > 3u) ? 3u : ready));
    g_hud_map[29] = TILE_SITE;
    g_hud_map[30] = (uint8_t)(TILE_BAR0 + ((g_level > 3u) ? 3u : g_level));
    g_hud_map[32] = g_save_dirty ? TILE_SEED_ICON : TILE_BLANK;
    g_hud_map[33] = (uint8_t)(TILE_BAR0 + ((g_xp > 3u) ? 3u : g_xp));

    set_win_tiles(0u, 0u, 20u, 2u, g_hud_map);
}

static uint8_t find_plot(uint16_t tile_x, uint16_t tile_y) {
    uint8_t index;
    for (index = 0u; index < MAX_PLOTS; ++index) {
        if (g_plots[index].active && g_plots[index].tile_x == tile_x && g_plots[index].tile_y == tile_y) {
            return index;
        }
    }
    return 255u;
}

static uint8_t alloc_plot(void) {
    uint8_t index;
    for (index = 0u; index < MAX_PLOTS; ++index) {
        if (!g_plots[index].active) return index;
    }
    return 255u;
}

static uint16_t plot_growth_duration(uint16_t tile_x, uint16_t tile_y) {
    FieldState field;
    int16_t duration;
    if (!tutorial_complete() && tutorial_farm_tile(tile_x, tile_y)) {
        return 54u;
    }
    evaluate_field_state(tile_x, tile_y, &field);
    duration = PLOT_BASE_GROWTH;
    duration -= (int16_t)(g_level * 16u);
    duration -= (int16_t)(field.rest_h / 12u);
    duration -= (int16_t)(field.rest_c / 14u);
    duration += (int16_t)(field.border / 6u);
    if (duration < 90) duration = 90;
    return (uint16_t)duration;
}

static uint8_t plot_growth_step(uint16_t tile_x, uint16_t tile_y) {
    uint8_t step;
    uint8_t settlement_index;
    step = 1u;
    settlement_index = find_nearest_built_settlement(tile_x, tile_y);
    if (settlement_index != 255u && abs_u16_diff(tile_x, g_settlements[settlement_index].tile_x) < 18u && abs_u16_diff(tile_y, g_settlements[settlement_index].tile_y) < 18u) {
        ++step;
    }
    if (g_phase >= 2u && g_phase <= 5u) ++step;
    return step;
}

static void update_plots(void) {
    uint8_t index;
    for (index = 0u; index < MAX_PLOTS; ++index) {
        if (!g_plots[index].active) continue;
        if (g_plots[index].stage != 2u) continue;
        if (g_plots[index].timer > 0u) {
            uint8_t step;
            step = plot_growth_step(g_plots[index].tile_x, g_plots[index].tile_y);
            if (g_plots[index].timer > step) {
                g_plots[index].timer = (uint16_t)(g_plots[index].timer - step);
            } else {
                g_plots[index].timer = 0u;
                g_plots[index].stage = 3u;
                mark_save_dirty();
            }
        }
    }
}

static void clear_feathers(void) {
    uint8_t index;
    for (index = 0u; index < MAX_SETTLEMENTS; ++index) {
        g_settlements[index].feather_ready = 0u;
    }
}

static void grant_feathers(void) {
    uint8_t index;
    for (index = 0u; index < MAX_SETTLEMENTS; ++index) {
        if (g_settlements[index].active && g_settlements[index].built) {
            g_settlements[index].feather_ready = 1u;
        }
    }
    mark_save_dirty();
}

static void collapse_settlements(void) {
    uint8_t index;
    for (index = 0u; index < MAX_SETTLEMENTS; ++index) {
        g_settlements[index].built = 0u;
        g_settlements[index].feather_ready = 0u;
    }
    mark_save_dirty();
}

static uint8_t free_enemy_slot(void) {
    uint8_t index;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        if (!g_enemies[index].active) return index;
    }
    return 255u;
}

static uint8_t free_impact_slot(void) {
    uint8_t index;
    for (index = 0u; index < MAX_IMPACTS; ++index) {
        if (!g_impacts[index].active) return index;
    }
    return 255u;
}

static void place_impact(uint16_t tile_x, uint16_t tile_y, uint8_t timer) {
    uint8_t impact_index;
    impact_index = free_impact_slot();
    if (impact_index == 255u) return;
    g_impacts[impact_index].active = 1u;
    g_impacts[impact_index].tile_x = tile_x;
    g_impacts[impact_index].tile_y = tile_y;
    g_impacts[impact_index].timer = timer;
}

static uint8_t enemy_windup_frames(const Enemy *enemy) {
    uint8_t base_frames;
    if (enemy->type == ENEMY_BOSS) base_frames = 30u;
    else if (enemy->tier == 0u) base_frames = 22u;
    else if (enemy->tier == 1u) base_frames = 18u;
    else base_frames = 12u;
    return passage_modules_adjust_windup(enemy->type, enemy->tier, base_frames);
}

static uint8_t enemy_lunge_frames(const Enemy *enemy) {
    uint8_t base_frames;
    if (enemy->type == ENEMY_BOSS) base_frames = 24u;
    else if (enemy->tier == 0u) base_frames = 12u;
    else if (enemy->tier == 1u) base_frames = 14u;
    else base_frames = 16u;
    return passage_modules_adjust_lunge_frames(enemy->type, enemy->tier, base_frames);
}

static uint8_t enemy_stun_frames(const Enemy *enemy) {
    uint8_t base_frames;
    if (enemy->type == ENEMY_BOSS) base_frames = 34u;
    else if (enemy->tier == 0u) base_frames = 18u;
    else if (enemy->tier == 1u) base_frames = 14u;
    else base_frames = 10u;
    return passage_modules_adjust_stun(enemy->type, enemy->tier, base_frames);
}

static uint8_t enemy_lunge_speed(const Enemy *enemy) {
    uint8_t base_speed;
    if (enemy->type == ENEMY_BOSS) base_speed = 2u;
    else base_speed = (uint8_t)(1u + enemy->tier);
    return passage_modules_adjust_lunge_speed(enemy->type, enemy->tier, base_speed);
}

static uint8_t spawn_impact_enemy(uint8_t enemy_type, uint8_t tier, uint16_t x, uint16_t y) {
    uint8_t enemy_index;
    enemy_index = free_enemy_slot();
    if (enemy_index == 255u) return 0u;
    g_enemies[enemy_index].active = 1u;
    g_enemies[enemy_index].type = enemy_type;
    g_enemies[enemy_index].tier = tier;
    g_enemies[enemy_index].state = AI_ROAM;
    g_enemies[enemy_index].timer = 0u;
    g_enemies[enemy_index].vx = 0;
    g_enemies[enemy_index].vy = 0;
    g_enemies[enemy_index].x = x;
    g_enemies[enemy_index].y = y;
    if (enemy_type == ENEMY_BOSS) {
        g_enemies[enemy_index].hp = 6u;
        g_enemies[enemy_index].poise = 3u;
        g_enemies[enemy_index].poise_max = 3u;
    } else {
        g_enemies[enemy_index].hp = (uint8_t)(1u + tier);
        g_enemies[enemy_index].poise = (uint8_t)(1u + tier);
        g_enemies[enemy_index].poise_max = (uint8_t)(1u + tier);
    }
    g_enemies[enemy_index].max_hp = g_enemies[enemy_index].hp;
    g_enemies[enemy_index].visual_seed = (uint8_t)(hash16((uint16_t)(x >> 3u), (uint16_t)(y >> 3u), (uint16_t)(g_world_seed + enemy_type * 31u + tier * 17u + enemy_index * 13u)) & 0xFFu);
    g_enemies[enemy_index].damage_mark = (uint8_t)(g_enemies[enemy_index].visual_seed ^ (uint8_t)(enemy_index * 29u + tier * 7u));
    g_enemies[enemy_index].damage_flash = 0u;
    place_impact((uint16_t)(x >> 3u), (uint16_t)(y >> 3u), (enemy_type == ENEMY_BOSS) ? 120u : 90u);
    return 1u;
}

static void enemy_mark_damage(uint8_t index, uint8_t intensity) {
    uint8_t next;
    if (index >= MAX_ENEMIES || !g_enemies[index].active) {
        return;
    }
    next = (uint8_t)(g_enemies[index].damage_mark * 37u + 17u + (g_phase_timer & 0x0Fu) + intensity * 11u);
    g_enemies[index].damage_mark = next;
    g_enemies[index].visual_seed = (uint8_t)((g_enemies[index].visual_seed << 1u) | (g_enemies[index].visual_seed >> 7u));
    g_enemies[index].visual_seed ^= (uint8_t)(0x5Au + index * 9u + intensity * 5u + g_level * 3u);
    g_enemies[index].damage_flash = (uint8_t)(6u + intensity * 3u);
}

static uint8_t spawn_daemon_kin(void) {
    uint8_t attempt;
    for (attempt = 0u; attempt < 6u; ++attempt) {
        uint16_t seed;
        int16_t off_x;
        int16_t off_y;
        uint8_t tier;
        uint16_t spawn_x;
        uint16_t spawn_y;
        seed = hash16((uint16_t)((g_player_x >> 3u) + attempt * 5u), (uint16_t)((g_player_y >> 3u) + attempt * 3u), (uint16_t)(g_world_seed + g_phase_timer + 331u + attempt * 97u));
        tier = (g_player_field.border > 172u) ? 2u : (uint8_t)(((seed >> 5u) % 2u) + (g_player_field.coherence_state >= 2u));
        tier = passage_modules_adjust_spawn_tier(tier, g_player_field.border, g_player_field.coherence_state);
        off_x = (int16_t)(seed & 0x7Fu) - 64;
        off_y = (int16_t)((seed >> 8u) & 0x7Fu) - 64;
        if (off_x < 0) off_x -= 40;
        else off_x += 40;
        if (off_y < 0) off_y -= 24;
        else off_y += 24;
        spawn_x = clamp_world_pixel((int32_t)g_player_x + (off_x * 2));
        spawn_y = clamp_world_pixel((int32_t)g_player_y + (off_y * 2));
        if (abs_u16_diff(spawn_x, g_player_x) < 24u && abs_u16_diff(spawn_y, g_player_y) < 24u) continue;
        if (!tile_passable((uint16_t)(spawn_x >> 3u), (uint16_t)(spawn_y >> 3u))) continue;
        if (spawn_impact_enemy(ENEMY_KIN, tier, spawn_x, spawn_y)) {
            audio_sfx_daemon_spawn();
            return 1u;
        }
    }
    return 0u;
}

static void spawn_boss(void) {
    uint8_t index;
    uint16_t spawn_tile_x;
    uint16_t spawn_tile_y;
    clear_feathers();
    clear_kin_enemies();
    index = find_nearest_built_settlement((uint16_t)(g_player_x >> 3u), (uint16_t)(g_player_y >> 3u));
    if (index != 255u) {
        spawn_tile_x = g_settlements[index].tile_x;
        spawn_tile_y = g_settlements[index].tile_y;
    } else {
        spawn_tile_x = (uint16_t)(g_player_x >> 3u) + 8u;
        spawn_tile_y = (uint16_t)(g_player_y >> 3u);
    }
    place_impact(spawn_tile_x, spawn_tile_y, 120u);
    place_impact((uint16_t)(spawn_tile_x + 2u), spawn_tile_y, 90u);
    place_impact((uint16_t)(spawn_tile_x - 2u), spawn_tile_y, 90u);
    if (!spawn_impact_enemy(ENEMY_BOSS, 2u, (uint16_t)(spawn_tile_x * 8u), (uint16_t)(spawn_tile_y * 8u))) {
        return;
    }
    g_boss_active = 1u;
    g_boss_defeated = 0u;
    g_spawn_timer = 150u;
    audio_sfx_boss_spawn();
    audio_set_music(AUDIO_TRACK_BOSS);
    mark_save_dirty();
}

static void update_impacts(void) {
    uint8_t index;
    for (index = 0u; index < MAX_IMPACTS; ++index) {
        if (!g_impacts[index].active) continue;
        if (g_impacts[index].timer > 0u) {
            --g_impacts[index].timer;
        } else {
            g_impacts[index].active = 0u;
        }
    }
}

static void respawn_player(void) {
    uint8_t settlement_index;
    settlement_index = find_nearest_built_settlement((uint16_t)(g_player_x >> 3u), (uint16_t)(g_player_y >> 3u));
    if (settlement_index != 255u) {
        g_player_x = (uint16_t)(g_settlements[settlement_index].tile_x * 8u);
        g_player_y = (uint16_t)(g_settlements[settlement_index].tile_y * 8u);
    } else {
        place_player_at_start();
    }
    g_health = (g_max_health > 1u) ? 2u : 1u;
    if (g_grain > 0u) --g_grain;
    audio_sfx_player_respawn();
    reset_camera_stream_state();
    follow_player();
}

static void damage_player(uint8_t amount) {
    if (g_invuln_timer != 0u) return;
    if (g_armor_level > 0u && amount > 1u) {
        amount = (uint8_t)(amount - ((g_armor_level > 2u) ? 2u : g_armor_level));
    }
    if (amount == 0u) amount = 1u;
    if (amount >= g_health) {
        respawn_player();
    } else {
        g_health -= amount;
        audio_sfx_player_hurt();
    }
    g_invuln_timer = 48u;
    mark_save_dirty();
}

static void award_xp(uint8_t amount) {
    while (amount > 0u) {
        --amount;
        if (g_level >= 4u) {
            g_xp = 0u;
            continue;
        }
        ++g_xp;
        if (g_xp >= 3u) {
            g_xp = 0u;
            ++g_level;
            g_farmer.A = clamp_u8((int16_t)g_farmer.A + 18);
            g_farmer.L = clamp_u8((int16_t)g_farmer.L + 12);
            if (g_max_health < 5u) {
                ++g_max_health;
            }
            g_health = g_max_health;
        }
    }
}

static void defeat_enemy(uint8_t index) {
    uint8_t enemy_type;
    uint16_t enemy_tile_x;
    uint16_t enemy_tile_y;
    enemy_type = g_enemies[index].type;
    enemy_tile_x = g_enemies[index].x >> 3u;
    enemy_tile_y = g_enemies[index].y >> 3u;
    g_enemies[index].active = 0u;
    if (enemy_type == ENEMY_BOSS) {
        g_boss_active = 0u;
        g_boss_defeated = 1u;
        grant_feathers();
        award_xp(2u);
        g_health = g_max_health;
        g_grain = clamp_u8((int16_t)g_grain + 2);
        audio_sfx_boss_defeat();
        audio_set_music_override(AUDIO_TRACK_FEATHER_VICTORY, 180u);
    } else {
        award_xp(1u);
        if (!tutorial_complete() && g_tutorial_stage == TUTORIAL_STAGE_COMBAT && tutorial_combat_zone(enemy_tile_x, enemy_tile_y)) {
            set_tutorial_stage(TUTORIAL_STAGE_TILL);
        }
    }
    mark_save_dirty();
}

static uint8_t on_special_vulnerability_tile(uint16_t x, uint16_t y) {
    uint8_t tile_value;
    tile_value = world_tile_at((uint16_t)(x >> 3u), (uint16_t)(y >> 3u));
    if (tile_value == TILE_SITE || tile_value == TILE_FEATHER || tile_value == TILE_SHRINE || tile_value == TILE_CRATER) return 1u;
    return 0u;
}

static void update_enemy_ai(void) {
    uint8_t index;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        if (!g_enemies[index].active) continue;
        if (g_enemies[index].damage_flash > 0u) {
            --g_enemies[index].damage_flash;
        }
        {
            int16_t delta_x;
            int16_t delta_y;
            delta_x = (int16_t)g_player_x - (int16_t)g_enemies[index].x;
            delta_y = (int16_t)g_player_y - (int16_t)g_enemies[index].y;
            if (g_enemies[index].state == AI_ROAM) {
                if (abs_u16_diff(g_enemies[index].x, g_player_x) < 56u && abs_u16_diff(g_enemies[index].y, g_player_y) < 56u) {
                    g_enemies[index].state = AI_WINDUP;
                    g_enemies[index].timer = enemy_windup_frames(&g_enemies[index]);
                } else {
                    uint8_t move_step;
                    move_step = (g_enemies[index].type == ENEMY_BOSS) ? 1u : (uint8_t)(1u + (g_enemies[index].tier > 1u));
                    while (move_step--) {
                        if ((delta_x < 0) && tile_passable((uint16_t)((g_enemies[index].x - 1u) >> 3u), (uint16_t)(g_enemies[index].y >> 3u))) {
                            --g_enemies[index].x;
                        }
                        if ((delta_x > 0) && tile_passable((uint16_t)((g_enemies[index].x + 1u) >> 3u), (uint16_t)(g_enemies[index].y >> 3u))) {
                            ++g_enemies[index].x;
                        }
                        if ((delta_y < 0) && tile_passable((uint16_t)(g_enemies[index].x >> 3u), (uint16_t)((g_enemies[index].y - 1u) >> 3u))) {
                            --g_enemies[index].y;
                        }
                        if ((delta_y > 0) && tile_passable((uint16_t)(g_enemies[index].x >> 3u), (uint16_t)((g_enemies[index].y + 1u) >> 3u))) {
                            ++g_enemies[index].y;
                        }
                    }
                }
            } else if (g_enemies[index].state == AI_WINDUP) {
                if (g_enemies[index].timer > 0u) {
                    --g_enemies[index].timer;
                } else {
                    uint8_t step_x;
                    uint8_t step_y;
                    if (g_enemies[index].type == ENEMY_BOSS) {
                        audio_sfx_boss_lunge();
                    }
                    g_enemies[index].state = AI_LUNGE;
                    g_enemies[index].timer = enemy_lunge_frames(&g_enemies[index]);
                    step_x = sign8(delta_x);
                    step_y = sign8(delta_y);
                    g_enemies[index].vx = (step_x == 0u) ? -(int8_t)enemy_lunge_speed(&g_enemies[index]) : ((step_x == 2u) ? (int8_t)enemy_lunge_speed(&g_enemies[index]) : 0);
                    g_enemies[index].vy = (step_y == 0u) ? -(int8_t)enemy_lunge_speed(&g_enemies[index]) : ((step_y == 2u) ? (int8_t)enemy_lunge_speed(&g_enemies[index]) : 0);
                }
            } else if (g_enemies[index].state == AI_LUNGE) {
                if (g_enemies[index].timer > 0u) {
                    --g_enemies[index].timer;
                    g_enemies[index].x = clamp_world_pixel((int32_t)g_enemies[index].x + g_enemies[index].vx);
                    g_enemies[index].y = clamp_world_pixel((int32_t)g_enemies[index].y + g_enemies[index].vy);
                    if (!tile_passable((uint16_t)(g_enemies[index].x >> 3u), (uint16_t)(g_enemies[index].y >> 3u))) {
                        g_enemies[index].state = AI_STUN;
                        g_enemies[index].timer = enemy_stun_frames(&g_enemies[index]);
                    }
                    if (g_enemies[index].type == ENEMY_BOSS && on_special_vulnerability_tile(g_enemies[index].x, g_enemies[index].y)) {
                        g_enemies[index].state = AI_STUN;
                        g_enemies[index].timer = 40u;
                        enemy_mark_damage(index, 2u);
                        audio_sfx_boss_break();
                    }
                } else {
                    g_enemies[index].state = AI_STUN;
                    g_enemies[index].timer = enemy_stun_frames(&g_enemies[index]);
                }
            } else {
                if (g_enemies[index].timer > 0u) {
                    --g_enemies[index].timer;
                } else {
                    g_enemies[index].state = AI_ROAM;
                    g_enemies[index].poise = g_enemies[index].poise_max;
                }
            }

            if (abs_u16_diff(g_enemies[index].x, g_player_x) < 8u && abs_u16_diff(g_enemies[index].y, g_player_y) < 8u) {
                if (g_enemies[index].state == AI_LUNGE || g_enemies[index].type == ENEMY_BOSS) {
                    damage_player((g_enemies[index].type == ENEMY_BOSS) ? 2u : 1u);
                }
            }
        }
    }
}

static uint8_t enemy_in_front(uint8_t *enemy_index_out) {
    uint8_t index;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        int16_t delta_x;
        int16_t delta_y;
        if (!g_enemies[index].active) continue;
        delta_x = (int16_t)g_enemies[index].x - (int16_t)g_player_x;
        delta_y = (int16_t)g_enemies[index].y - (int16_t)g_player_y;
        if (abs_u16_diff(g_enemies[index].x, g_player_x) > 16u || abs_u16_diff(g_enemies[index].y, g_player_y) > 16u) continue;
        if (g_facing == DIR_LEFT && delta_x <= 0 && abs_u16_diff(g_enemies[index].y, g_player_y) < 12u) {
            *enemy_index_out = index;
            return 1u;
        }
        if (g_facing == DIR_RIGHT && delta_x >= 0 && abs_u16_diff(g_enemies[index].y, g_player_y) < 12u) {
            *enemy_index_out = index;
            return 1u;
        }
        if (g_facing == DIR_UP && delta_y <= 0 && abs_u16_diff(g_enemies[index].x, g_player_x) < 12u) {
            *enemy_index_out = index;
            return 1u;
        }
        if (g_facing == DIR_DOWN && delta_y >= 0 && abs_u16_diff(g_enemies[index].x, g_player_x) < 12u) {
            *enemy_index_out = index;
            return 1u;
        }
    }
    return 0u;
}

static void attack_enemy(uint8_t index) {
    uint8_t damage;
    uint8_t damage_dealt;
    g_attack_timer = 10u;
    passage_modules_record_rake(1u);
    if (g_weapon_level == 0u) {
        return;
    }
    if (g_enemies[index].state == AI_WINDUP || (g_enemies[index].state == AI_LUNGE && g_enemies[index].type != ENEMY_BOSS)) {
        if (g_enemies[index].poise > 0u) {
            --g_enemies[index].poise;
        }
        if (g_enemies[index].poise == 0u) {
            g_enemies[index].state = AI_STUN;
            g_enemies[index].timer = enemy_stun_frames(&g_enemies[index]);
            enemy_mark_damage(index, 1u);
            if (g_enemies[index].type == ENEMY_BOSS) {
                audio_sfx_boss_break();
            } else {
                audio_sfx_enemy_stagger();
            }
        }
    } else if (g_enemies[index].state == AI_STUN) {
        damage = (g_weapon_level > 1u) ? 2u : 1u;
        damage_dealt = 0u;
        while (damage > 0u && g_enemies[index].hp > 0u) {
            --g_enemies[index].hp;
            --damage;
            ++damage_dealt;
        }
        if (damage_dealt > 0u) {
            enemy_mark_damage(index, (uint8_t)(1u + damage_dealt));
        }
        if (g_enemies[index].hp == 0u) {
            defeat_enemy(index);
        } else {
            g_enemies[index].poise = g_enemies[index].poise_max;
            g_enemies[index].timer = enemy_stun_frames(&g_enemies[index]);
        }
    }
}

static uint8_t projectile_hits_enemy(uint16_t x, uint16_t y, uint8_t *enemy_index_out) {
    uint8_t index;
    for (index = 0u; index < MAX_ENEMIES; ++index) {
        if (!g_enemies[index].active) continue;
        if (abs_u16_diff(g_enemies[index].x, x) < 8u && abs_u16_diff(g_enemies[index].y, y) < 8u) {
            *enemy_index_out = index;
            return 1u;
        }
    }
    return 0u;
}

static void update_projectiles(void) {
    uint8_t index;
    for (index = 0u; index < MAX_PROJECTILES; ++index) {
        uint16_t next_x;
        uint16_t next_y;
        uint8_t enemy_index;
        if (!g_projectiles[index].active) continue;
        if (g_projectiles[index].ttl == 0u) {
            g_projectiles[index].active = 0u;
            continue;
        }
        next_x = clamp_world_pixel((int32_t)g_projectiles[index].x + g_projectiles[index].vx);
        next_y = clamp_world_pixel((int32_t)g_projectiles[index].y + g_projectiles[index].vy);
        if (!tile_passable((uint16_t)(next_x >> 3u), (uint16_t)(next_y >> 3u))) {
            g_projectiles[index].active = 0u;
            continue;
        }
        g_projectiles[index].x = next_x;
        g_projectiles[index].y = next_y;
        if (projectile_hits_enemy(next_x, next_y, &enemy_index)) {
            attack_enemy(enemy_index);
            g_projectiles[index].active = 0u;
            continue;
        }
        --g_projectiles[index].ttl;
    }
}

static void spawn_projectile(void) {
    uint8_t index;
    uint8_t speed;
    if (g_weapon_level == 0u || g_attack_timer != 0u) {
        return;
    }
    for (index = 0u; index < MAX_PROJECTILES; ++index) {
        if (!g_projectiles[index].active) {
            g_projectiles[index].active = 1u;
            g_projectiles[index].ttl = (uint8_t)(PROJECTILE_TTL_BASE + (g_weapon_level * 4u));
            speed = (uint8_t)(PROJECTILE_SPEED_BASE + ((g_weapon_level > 1u) ? 1u : 0u) + ((g_weapon_level > 2u) ? 1u : 0u));
            g_projectiles[index].x = g_player_x;
            g_projectiles[index].y = g_player_y;
            g_projectiles[index].vx = 0;
            g_projectiles[index].vy = 0;
            if (g_facing == DIR_LEFT) {
                g_projectiles[index].x = clamp_world_pixel((int32_t)g_player_x - 6);
                g_projectiles[index].vx = -(int8_t)speed;
                g_projectiles[index].tile_index = 7u;
            } else if (g_facing == DIR_RIGHT) {
                g_projectiles[index].x = clamp_world_pixel((int32_t)g_player_x + 6);
                g_projectiles[index].vx = (int8_t)speed;
                g_projectiles[index].tile_index = 7u;
            } else if (g_facing == DIR_UP) {
                g_projectiles[index].y = clamp_world_pixel((int32_t)g_player_y - 6);
                g_projectiles[index].vy = -(int8_t)speed;
                g_projectiles[index].tile_index = 6u;
            } else {
                g_projectiles[index].y = clamp_world_pixel((int32_t)g_player_y + 6);
                g_projectiles[index].vy = (int8_t)speed;
                g_projectiles[index].tile_index = 6u;
            }
            g_attack_timer = (g_weapon_level > 2u) ? 4u : 6u;
            passage_modules_record_rake(1u);
            audio_sfx_rake_swing();
            return;
        }
    }
}

static void front_tile(uint16_t *tile_x_out, uint16_t *tile_y_out) {
    int32_t target_x;
    int32_t target_y;
    target_x = g_player_x;
    target_y = g_player_y;
    if (g_facing == DIR_LEFT) target_x -= 8;
    if (g_facing == DIR_RIGHT) target_x += 8;
    if (g_facing == DIR_UP) target_y -= 8;
    if (g_facing == DIR_DOWN) target_y += 8;
    *tile_x_out = (uint16_t)(clamp_world_pixel(target_x) >> 3u);
    *tile_y_out = (uint16_t)(clamp_world_pixel(target_y) >> 3u);
}

static void rake_action(void) {
    spawn_projectile();
}

static void reseed_world(void) {
    audio_sfx_shrine_reseed();
    audio_set_music_override(AUDIO_TRACK_SHRINE_RESEED, 96u);
    g_world_seed = hash16(g_world_seed, (uint16_t)(g_phase * 61u + g_level * 17u), 0x9B1Du);
    generate_static_anchors();
    build_settlement_sites();
    clear_dynamic_state();
    place_player_at_start();
    if (!tutorial_complete()) {
        g_weapon_level = 0u;
        g_armor_level = 0u;
        g_tutorial_stage = TUTORIAL_STAGE_WAKE;
    }
    g_phase = 0u;
    g_phase_timer = 0u;
    g_boss_active = 0u;
    g_boss_defeated = 0u;
    g_spawn_timer = 120u;
    reset_camera_stream_state();
    follow_player();
    passage_modules_begin_session(g_world_seed, g_level, g_weapon_level, g_armor_level);
    mark_save_dirty();
}

static void cycle_weapon_module(void) {
    if (g_weapon_level == 0u) return;
    g_weapon_level = (g_weapon_level >= 3u) ? 1u : (uint8_t)(g_weapon_level + 1u);
    g_attack_timer = 6u;
    audio_sfx_gear_pickup();
    mark_save_dirty();
}

static void cycle_armor_module(void) {
    if (g_armor_level == 0u) return;
    g_armor_level = (g_armor_level >= 3u) ? 1u : (uint8_t)(g_armor_level + 1u);
    g_attack_timer = 6u;
    audio_sfx_gear_pickup();
    mark_save_dirty();
}

static void use_action(uint8_t joy) {
    uint16_t player_tile_x;
    uint16_t player_tile_y;
    uint8_t settlement_index;
    player_tile_x = g_player_x >> 3u;
    player_tile_y = g_player_y >> 3u;

    if (shrine_tile_at(player_tile_x, player_tile_y)) {
        passage_modules_record_use(1u);
        reseed_world();
        return;
    }

    settlement_index = find_settlement_at(player_tile_x, player_tile_y);
    if (settlement_index != 255u && g_settlements[settlement_index].built) {
        if (!tutorial_complete() && settlement_index == 0u && g_tutorial_stage == TUTORIAL_STAGE_REST) {
            if (g_health < g_max_health) {
                ++g_health;
            }
            g_spawn_timer = 160u;
            passage_modules_record_use(1u);
            audio_sfx_settlement_rest();
            set_tutorial_stage(TUTORIAL_STAGE_COMPLETE);
            return;
        }
        if (g_settlements[settlement_index].feather_ready && count_ready_feathers() > 1u) {
            uint8_t next;
            next = (uint8_t)((settlement_index + 1u) % MAX_SETTLEMENTS);
            while (next != settlement_index) {
                if (g_settlements[next].built && g_settlements[next].feather_ready) {
                    g_player_x = (uint16_t)(g_settlements[next].tile_x * 8u);
                    g_player_y = (uint16_t)(g_settlements[next].tile_y * 8u);
                    passage_modules_record_use(1u);
                    audio_sfx_feather_gate();
                    reset_camera_stream_state();
                    follow_player();
                    mark_save_dirty();
                    return;
                }
                next = (uint8_t)((next + 1u) % MAX_SETTLEMENTS);
            }
        } else {
            if (g_health < g_max_health) {
                ++g_health;
                g_spawn_timer = 160u;
                passage_modules_record_use(1u);
                audio_sfx_settlement_rest();
                mark_save_dirty();
                return;
            }
        }
    }

    if (g_grain > 0u && g_health < g_max_health) {
        --g_grain;
        ++g_health;
        passage_modules_record_use(1u);
        audio_sfx_heal();
        mark_save_dirty();
        return;
    }

    if (joy & (J_UP | J_DOWN)) {
        cycle_armor_module();
    } else {
        cycle_weapon_module();
    }
}

static void advance_phase(void) {
    if (g_boss_active && !g_boss_defeated) {
        g_phase = 7u;
        return;
    }
    ++g_phase;
    if (g_phase == 7u && !g_boss_active && !g_boss_defeated) {
        spawn_boss();
        return;
    }
    if (g_phase >= 8u) {
        g_phase = 0u;
        clear_threat_state();
        if (!g_boss_defeated) {
            collapse_settlements();
        }
        g_boss_active = 0u;
        g_boss_defeated = 0u;
    }
    mark_save_dirty();
}

static void try_move_player(int8_t dx, int8_t dy, uint8_t facing) {
    uint16_t next_x;
    uint16_t next_y;
    uint8_t moved;
    uint8_t step_tile;
    g_facing = facing;
    next_x = clamp_world_pixel((int32_t)g_player_x + dx);
    next_y = clamp_world_pixel((int32_t)g_player_y + dy);
    moved = 0u;
    if (tile_passable((uint16_t)(next_x >> 3u), (uint16_t)(g_player_y >> 3u))) {
        g_player_x = next_x;
        moved = 1u;
    }
    if (tile_passable((uint16_t)(g_player_x >> 3u), (uint16_t)(next_y >> 3u))) {
        g_player_y = next_y;
        moved = 1u;
    }
    if (moved) {
        step_tile = world_tile_at((uint16_t)(g_player_x >> 3u), (uint16_t)(g_player_y >> 3u));
        audio_try_footstep((step_tile == TILE_SAND) ? 1u : 0u);
    }
    step_tile = world_tile_at((uint16_t)(g_player_x >> 3u), (uint16_t)(g_player_y >> 3u));
    passage_modules_record_move(moved, step_tile);
    if (moved) {
        g_walk_anim_frame ^= 1u;
        g_move_anim_timer = 8u;
    }
}

static void handle_input(uint8_t joy, uint8_t pressed) {
    if (joy & J_LEFT) try_move_player(-1, 0, DIR_LEFT);
    if (joy & J_RIGHT) try_move_player(1, 0, DIR_RIGHT);
    if (joy & J_UP) try_move_player(0, -1, DIR_UP);
    if (joy & J_DOWN) try_move_player(0, 1, DIR_DOWN);
    if (pressed & J_B) rake_action();
    if (pressed & J_A) use_action(joy);
}

static void init_graphics(void) {
    DISPLAY_OFF;
    SPRITES_8x8;
    set_bkg_data(0u, 33u, bg_tiles);
    passage_modules_sync_visuals(sprite_tiles, SPRITE_TILE_COUNT, g_weapon_level, g_armor_level, g_phase, g_boss_active);
    set_sprite_data(0u, SPRITE_TILE_COUNT, passage_modules_sprite_tiles());
    set_sprite_tile(0u, 0u);
    hide_unused_sprites();
    move_win(7u, WORLD_SCREEN_HUD_Y);
    follow_player();
    refresh_camera();
    update_hud();
    move_player_sprite();
    render_enemies();
    render_projectiles();
    SHOW_BKG;
    SHOW_WIN;
    SHOW_SPRITES;
    DISPLAY_ON;
}



void main(void) {
    uint8_t joy;
    uint8_t prev;
    uint8_t pressed;

    audio_init();
    g_profile_index = 0u;
    title_screen();
    if (!load_profile(g_profile_index)) {
        init_new_profile(g_profile_index);
    }
    evaluate_field_state((uint16_t)(g_player_x >> 3u), (uint16_t)(g_player_y >> 3u), &g_player_field);
    init_graphics();
    audio_sync_world_music(audio_world_track());
    prev = 0u;

    if (g_boss_active) {
        spawn_boss();
    }

    g_tutorial_overlay_enabled = 1u;
    reset_camera_stream_state();
    g_redraw = 1u;

    while (1) {
        wait_vbl_done();
        ++g_frame_counter;
        audio_update();
        joy = joypad();
        pressed = (uint8_t)(joy & (uint8_t)(~prev));

        handle_input(joy, pressed);
        evaluate_field_state((uint16_t)(g_player_x >> 3u), (uint16_t)(g_player_y >> 3u), &g_player_field);
        audio_sync_world_music(audio_world_track());
        follow_player();
        if (g_redraw) {
            refresh_camera();
            g_redraw = 0u;
        }

        update_plots();
        update_enemy_ai();
        update_projectiles();
        update_impacts();
        update_tutorial_state();

        update_spawn_flow();

        if (g_attack_timer > 0u) --g_attack_timer;
        if (g_move_anim_timer > 0u) --g_move_anim_timer;
        if (g_invuln_timer > 0u) --g_invuln_timer;

        update_phase_flow();
        passage_modules_update(g_phase, g_boss_active, g_health, g_max_health);
        if (passage_modules_sync_visuals(sprite_tiles, SPRITE_TILE_COUNT, g_weapon_level, g_armor_level, g_phase, g_boss_active)) {
            set_sprite_data(0u, SPRITE_TILE_COUNT, passage_modules_sprite_tiles());
        }

        maybe_autosave();
        move_player_sprite();
        render_enemies();
        render_projectiles();
        update_hud();
        prev = joy;
    }
}