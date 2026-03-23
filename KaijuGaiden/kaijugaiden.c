/*
 * kaijugaiden.c — Kaiju Gaiden!? GB.
 * drIpTECH / fanzovNG
 *
 * Self-contained single-file C source for the Game Boy edition of Kaiju Gaiden.
 * Targets:
 *   .gb   — GBDK-2020 toolchain  (sdcc + lcc, DMG/CGB 160×144)
 *   .gba  — devkitARM/libgba     (ARM7TDMI 240×160, mode 0 tiles)
 *   .nds  — devkitARM/libnds     (Nintendo DS main 2D engine, 256×192)
 *   .3dsx — devkitARM/libctru    (Nintendo 3DS homebrew, top-screen software blit)
 *   .farim — ZIP-based FARIM 0.1 container (browser/host runtime)
 *
 * Build selection is controlled by preprocessor flags:
 *   TARGET_GB   — compile for original Game Boy via GBDK
 *   TARGET_GBA  — compile for Game Boy Advance via devkitARM
 *   TARGET_NDS  — compile for Nintendo DS via devkitARM/libnds
 *   TARGET_3DS  — compile for Nintendo 3DS via devkitARM/libctru
 *   TARGET_HOST — compile for desktop host (SDL2 or stdio fallback)
 *   (FARIM packaging is handled by build/farim_pack.py after a HOST build)
 *
 * If no target flag is supplied the file defaults to TARGET_HOST for easy
 * desktop testing without a dev toolchain.
 *
 * ── GAME DESIGN ──────────────────────────────────────────────────────────────
 * Kaiju Gaiden!? GB. is a pared-down single-screen, non-scrolling boss brawler
 * aimed at Game Boy hardware.  It preserves the genetic-nano-cell lore and core
 * combat identity of the GBA game while fitting within DMG constraints:
 *
 *   Resolution    : 160 × 144 px  (20 × 18 tiles of 8 × 8 px each)
 *   Colour depth  : 4 shades (DMG green palette / white-black-grey2)
 *   Sprite count  : up to 40 OBJ entries (standard Game Boy limit)
 *   Stages        : single-screen arenas with micro camera offsets for readability
 *   Combat system :
 *     – A button: Primary attack (3-hit combo with beat-window bonus)
 *     – B button: Dodge / skip (also "Hold B" to skip cinematics)
 *     – Start: Pause
 *     – Select: Use Growth NanoCell (consumable)
 *   Progression   :
 *     – Defeat boss → receive Environmental Genetic Cypher
 *     – Cypher unlocks next stage (region-gating)
 *     – Password system encodes cleared bosses + cyphers
 *
 * ── FLOW ─────────────────────────────────────────────────────────────────────
 * drIpTECH splash  (2 s or A/B/Start)
 *   → Intro Cinematic  (two kaiju on beach; hold B 1.5 s to skip)
 *     → Title Menu  (START GAME highlighted by default)
 *       → Stage 1: HARBOR SHORE  (Minion wave → Boss: Harbor Leviathan)
 *         → Genetic Cypher drop sequence
 *           → Title Menu  (loop)
 *
 * ── GENETIC NANO-CELL SYSTEM (GB edition) ────────────────────────────────────
 * Simplified from GBA version; no persistent mutation, no visual VN layer.
 * Growth NanoCells are collected from defeated minions and stored 0–9.
 * Using a NanoCell (Select) grants a 5-second power-up (doubled attack damage).
 *
 * ── LORE ANCHOR ──────────────────────────────────────────────────────────────
 * Rei Moro — the Altered protagonist — answers the resonance of the harbor reef.
 * The Harbor Leviathan has three attack phases (see BOSS DESIGN below).
 * Breaking all three phases yields the HARBOR CYPHER — a fragment of reef genome.
 *
 * ── ASSET PIPELINE ───────────────────────────────────────────────────────────
 * All assets are embedded as C arrays below in section:
 *   [SECTION: ASSET DATA]
 * After Recraft generation the raw PNG tiles are converted to 2bpp (GB) or 4bpp
 * (GBA) tile data by tools/convert_tiles.py and pasted into this section.
 * Placeholder tile data (hand-authored 8×8 stubs) is shipped so the file
 * compiles before a Recraft pass.
 *
 * ── PORTING NOTES ────────────────────────────────────────────────────────────
 * GB (GBDK-2020):
 *   – All rendering uses GBDK's set_bkg_tile_xy / set_sprite_tile / shadow OAM
 *   – 2bpp tiles loaded with set_bkg_data / set_sprite_data
 *   – Input via joypad() every frame
 *   – Audio via GBDK audio stubs (square wave channels)
 *
 * GBA (devkitARM):
 *   – Tiles expanded to 4bpp; backgrounds use BG Mode 0 charblock 0
 *   – Sprites use OAM attr0/attr1/attr2 (4bpp 8×8 OBJ)
 *   – Input via REG_KEYINPUT
 *   – VBlank sync via interrupt or REG_VCOUNT spin
 *
 * HOST (SDL2 / stdio):
 *   – SDL2 surface blit for tile rendering (160×144 upscaled × 3)
 *   – Keyboard mapped to GB buttons
 *   – Used as reference build for FARIM packaging
 */

/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: TARGET DETECTION & PLATFORM SHIMS
 * ═══════════════════════════════════════════════════════════════════════════ */

#if !defined(TARGET_GB) && !defined(TARGET_GBA) && !defined(TARGET_NDS) && !defined(TARGET_3DS) && !defined(TARGET_HOST)
#  define TARGET_HOST
#endif

/* ── Shared integer types ── */
#include <stdint.h>
#include <string.h>

typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t   s8;
typedef int16_t  s16;
typedef int32_t  s32;

/* ── Screen geometry (shared by all targets) ── */
#define SCR_W    160
#define SCR_H    144
#define TILE_W     8
#define TILE_H     8
#define BKG_COLS  20   /* SCR_W / TILE_W */
#define BKG_ROWS  18   /* SCR_H / TILE_H */

/* ── GB (GBDK-2020) ── */
#ifdef TARGET_GB
#  include <gb/gb.h>
#  include <gb/cgb.h>
/*  GBDK provides: joypad(), set_bkg_tile_xy(), set_sprite_tile(),
 *  set_bkg_data(), set_sprite_data(), SHOW_BKG, SHOW_SPRITES, etc.
 *  We alias our generic calls through thin macros below.             */

/* Input bit masks (GBDK joypad() returns bitmask) */
#  define BTN_UP     0x40
#  define BTN_DOWN   0x80
#  define BTN_LEFT   0x20
#  define BTN_RIGHT  0x10
#  define BTN_A      0x01
#  define BTN_B      0x02
#  define BTN_START  0x08
#  define BTN_SELECT 0x04

static u8  _joy_prev = 0;
static u8  _joy_cur  = 0;

static inline void plat_poll_input(void) {
    _joy_prev = _joy_cur;
    _joy_cur  = joypad();
}
static inline u8 plat_held(u8 mask)  { return (_joy_cur  & mask) ? 1 : 0; }
static inline u8 plat_pressed(u8 mask) {
    return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
}
static inline u16 plat_input_mask(void) { return (u16)_joy_cur; }
static inline u16 plat_pressed_mask(void) { return (u16)(_joy_cur & (u8)(~_joy_prev)); }
static inline void plat_vsync(void)  { wait_vbl_done(); }

/* Tile / sprite rendering */
static inline void plat_set_bkg_tile(u8 x, u8 y, u8 tile) {
    set_bkg_tile_xy(x, y, tile);
}
static inline void plat_set_sprite(u8 id, u8 x, u8 y, u8 tile, u8 flags) {
    move_sprite(id, x + 8, y + 16);   /* GBDK uses offset convention */
    set_sprite_tile(id, tile);
    set_sprite_prop(id, flags);
}
static inline void plat_load_bkg_tiles(const u8 *data, u8 first, u8 count) {
    set_bkg_data(first, count, data);
}
static inline void plat_load_sprite_tiles(const u8 *data, u8 first, u8 count) {
    set_sprite_data(first, count, data);
}

/* Simple delay — busy loops */
static inline void plat_delay_frames(u8 n) {
    for (u8 i = 0; i < n; ++i) wait_vbl_done();
}

static inline void plat_audio_reset(void) {}
static inline void plat_audio_profile(u8 scene, u8 genre, u8 tension, u8 pulse, u8 voice, u8 noise) {
    (void)scene; (void)genre; (void)tension; (void)pulse; (void)voice; (void)noise;
}
static inline void plat_audio_event(u8 event_kind, u8 value) {
    (void)event_kind; (void)value;
}
static inline void plat_audio_tts(u8 speaker, const char *line) {
    (void)speaker; (void)line;
}

#endif /* TARGET_GB */

/* ── GBA (devkitARM / libgba) ── */
#ifdef TARGET_GBA
#  include <gba.h>
/*  devkitPro libgba provides KEY_*, scanKeys(), keysHeld(), keysDown(),
 *  VBlankIntrWait(), REG_DISPCNT, tile/BG register access.           */

#  define BTN_UP     KEY_UP
#  define BTN_DOWN   KEY_DOWN
#  define BTN_LEFT   KEY_LEFT
#  define BTN_RIGHT  KEY_RIGHT
#  define BTN_A      KEY_A
#  define BTN_B      KEY_B
#  define BTN_START  KEY_START
#  define BTN_SELECT KEY_SELECT

static u16 _keys_prev = 0;
static u16 _keys_cur  = 0;

static inline void plat_poll_input(void) {
    _keys_prev = _keys_cur;
    scanKeys();
    _keys_cur = keysHeld();
}
static inline u8 plat_held(u16 mask)    { return (_keys_cur  & mask) ? 1 : 0; }
static inline u8 plat_pressed(u16 mask) {
    return ((_keys_cur & mask) && !(_keys_prev & mask)) ? 1 : 0;
}
static inline u16 plat_input_mask(void) { return _keys_cur; }
static inline u16 plat_pressed_mask(void) { return (u16)(_keys_cur & (u16)(~_keys_prev)); }
static inline void plat_vsync(void)  { VBlankIntrWait(); }

/* GBA tile rendering (BG mode 0, charblock 0, screenblock 28) */
#define GBA_VRAM_BG   ((u16*)0x06000000)
#define GBA_VRAM_OBJ  ((u16*)0x06014000)
#define GBA_OAM       ((u16*)0x07000000)
#define GBA_TILE_BASE  0x06000000
#define GBA_SBLOCK28  ((u16*)(0x06000000 + 28*0x800))

static inline void plat_set_bkg_tile(u8 x, u8 y, u8 tile) {
    GBA_SBLOCK28[y * 32 + x] = tile;
}
static inline void plat_set_sprite(u8 id, u8 x, u8 y, u8 tile, u8 flags) {
    /* Minimal OAM entry: attr0=y, attr1=x, attr2=tile */
    volatile u16 *oam = (u16*)0x07000000 + id * 4;
    oam[0] = (u16)(y & 0xFF);
    oam[1] = (u16)((x & 0x1FF)
        | ((flags & 0x20) ? (1u << 12) : 0)
        | ((flags & 0x40) ? (1u << 13) : 0));
    oam[2] = (u16)(tile & 0x3FF);
}
static inline void plat_load_bkg_tiles(const u8 *data, u8 first, u8 count) {
    volatile u8 *dst = (u8*)(0x06000000) + first * 32;
    for (int i = 0; i < count * 32; ++i) dst[i] = data[i];
}
static inline void plat_load_sprite_tiles(const u8 *data, u8 first, u8 count) {
    volatile u8 *dst = (u8*)(0x06014000) + first * 32;
    for (int i = 0; i < count * 32; ++i) dst[i] = data[i];
}
static inline void plat_delay_frames(u8 n) {
    for (u8 i = 0; i < n; ++i) VBlankIntrWait();
}

static inline void plat_audio_reset(void) {}
static inline void plat_audio_profile(u8 scene, u8 genre, u8 tension, u8 pulse, u8 voice, u8 noise) {
    (void)scene; (void)genre; (void)tension; (void)pulse; (void)voice; (void)noise;
}
static inline void plat_audio_event(u8 event_kind, u8 value) {
    (void)event_kind; (void)value;
}
static inline void plat_audio_tts(u8 speaker, const char *line) {
    (void)speaker; (void)line;
}

#endif /* TARGET_GBA */

/* ── NDS (devkitARM / libnds) ── */
#ifdef TARGET_NDS
#  include <nds.h>

#  define BTN_UP     KEY_UP
#  define BTN_DOWN   KEY_DOWN
#  define BTN_LEFT   KEY_LEFT
#  define BTN_RIGHT  KEY_RIGHT
#  define BTN_A      KEY_A
#  define BTN_B      KEY_B
#  define BTN_START  KEY_START
#  define BTN_SELECT KEY_SELECT

static u16 _keys_prev = 0;
static u16 _keys_cur  = 0;

static inline void plat_poll_input(void) {
    _keys_prev = _keys_cur;
    scanKeys();
    _keys_cur = keysHeld();
}
static inline u8 plat_held(u16 mask)    { return (_keys_cur  & mask) ? 1 : 0; }
static inline u8 plat_pressed(u16 mask) {
    return ((_keys_cur & mask) && !(_keys_prev & mask)) ? 1 : 0;
}
static inline u16 plat_input_mask(void) { return _keys_cur; }
static inline u16 plat_pressed_mask(void) { return (u16)(_keys_cur & (u16)(~_keys_prev)); }
static inline void plat_vsync(void)  {
    swiWaitForVBlank();
    oamUpdate(&oamMain);
}

static void nds_expand_2bpp_tile(u8 *dst, const u8 *src) {
    for (int row = 0; row < 8; ++row) {
        u8 lo = src[row * 2 + 0];
        u8 hi = src[row * 2 + 1];
        for (int col = 0; col < 4; ++col) {
            u8 shift_a = (u8)(7 - col * 2);
            u8 shift_b = (u8)(6 - col * 2);
            u8 pix_a = (u8)(((lo >> shift_a) & 1u) | (((hi >> shift_a) & 1u) << 1));
            u8 pix_b = (u8)(((lo >> shift_b) & 1u) | (((hi >> shift_b) & 1u) << 1));
            dst[row * 4 + col] = (u8)(pix_a | (pix_b << 4));
        }
    }
}

static inline void plat_set_bkg_tile(u8 x, u8 y, u8 tile) {
    if (x < 32 && y < 32) {
        ((u16*)BG_MAP_RAM(0))[y * 32 + x] = tile;
    }
}
static inline void plat_set_sprite(u8 id, s16 x, s16 y, u8 tile, u8 flags) {
    if (id >= 128) return;
    if (x < -8 || x > 255 || y < -8 || y > 191) {
        oamSetHidden(&oamMain, id, true);
        return;
    }
    oamSet(&oamMain, id, x, y, 0, 0,
           SpriteSize_8x8, SpriteColorFormat_16Color,
           (u16*)SPRITE_GFX + tile * 16,
           -1,
            false,
            false,
            (flags & 0x20) ? true : false,
            (flags & 0x40) ? true : false,
            false);
}
static inline void plat_load_bkg_tiles(const u8 *data, u8 first, u8 count) {
    u8 *dst = (u8*)BG_TILE_RAM(0) + first * 32;
    for (int i = 0; i < count; ++i) {
        nds_expand_2bpp_tile(dst + i * 32, data + i * 16);
    }
}
static inline void plat_load_sprite_tiles(const u8 *data, u8 first, u8 count) {
    u8 *dst = (u8*)SPRITE_GFX + first * 32;
    for (int i = 0; i < count; ++i) {
        nds_expand_2bpp_tile(dst + i * 32, data + i * 16);
    }
}
static inline void plat_delay_frames(u8 n) {
    for (u8 i = 0; i < n; ++i) swiWaitForVBlank();
}

static inline void plat_audio_reset(void) {}
static inline void plat_audio_profile(u8 scene, u8 genre, u8 tension, u8 pulse, u8 voice, u8 noise) {
    (void)scene; (void)genre; (void)tension; (void)pulse; (void)voice; (void)noise;
}
static inline void plat_audio_event(u8 event_kind, u8 value) {
    (void)event_kind; (void)value;
}
static inline void plat_audio_tts(u8 speaker, const char *line) {
    (void)speaker; (void)line;
}

#endif /* TARGET_NDS */

/* ── 3DS (libctru software-rendered top screen) ── */
#ifdef TARGET_3DS
#  include <3ds.h>

#  define BTN_UP     KEY_DUP
#  define BTN_DOWN   KEY_DDOWN
#  define BTN_LEFT   KEY_DLEFT
#  define BTN_RIGHT  KEY_DRIGHT
#  define BTN_A      KEY_A
#  define BTN_B      KEY_B
#  define BTN_START  KEY_START
#  define BTN_SELECT KEY_SELECT
#endif

/* ── HOST / 3DS shared software renderer ── */
#if defined(TARGET_HOST) || defined(TARGET_3DS)
#  include <stdio.h>
#  include <stdlib.h>
#  ifdef TARGET_3DS
#    include <math.h>
#  endif
#  ifdef TARGET_HOST
#    ifndef SDL_MAIN_HANDLED
#      define SDL_MAIN_HANDLED
#    endif
#    ifdef __has_include
#      if __has_include(<SDL2/SDL.h>)
#        include <SDL2/SDL.h>
#        define HAS_SDL2 1
#      elif __has_include(<SDL.h>)
#        include <SDL.h>
#        define HAS_SDL2 1
#      endif
#    endif
#    ifdef main
#      undef main
#    endif
#  endif

#  ifdef TARGET_HOST
#    define BTN_UP     0x40
#    define BTN_DOWN   0x80
#    define BTN_LEFT   0x20
#    define BTN_RIGHT  0x10
#    define BTN_A      0x01
#    define BTN_B      0x02
#    define BTN_START  0x08
#    define BTN_SELECT 0x04
#  endif

/* 160×144 pixel framebuffer:  pixels indexed on GB 4-shade palette */
/* SCREEN_W/H match SCR_W/H defined globally above */
#define SCREEN_W SCR_W
#define SCREEN_H SCR_H

/* GB palette (DMG greenscale approximated as grey) */
static const u32 gb_palette[4] = {
    0xFFE8F8E0u,   /* shade 0 — lightest */
    0xFF88C070u,   /* shade 1 */
    0xFF346856u,   /* shade 2 */
    0xFF081820u    /* shade 3 — darkest */
};

#ifdef TARGET_3DS
static const u32 ctr_palette[4] = {
    0xE0F8E8u,
    0x70C088u,
    0x566834u,
    0x201808u
};

#define CTR_TOP_W 400
#define CTR_TOP_H 240
#define CTR_VIEW_W ((SCREEN_W * 5) / 3)
#define CTR_VIEW_H ((SCREEN_H * 5) / 3)
#define CTR_APP_DIR "sdmc:/3ds/kaijugaiden"
#define CTR_PROFILE_PATH CTR_APP_DIR "/ndsx_profile.json"
#define CTR_STATUS_PATH CTR_APP_DIR "/ndsx_runtime_status.json"
#define CTR_MIC_BUFFER_SIZE 0x4000
#define CTR_MIC_WINDOW_SAMPLES 256

static float ctr_3d_slider = 0.0f;
static u8 ctr_stereo_comfort = 1;
static u8 ctr_stereo_force_flat = 0;
static u8 ctr_qtm_available = 0;
static u8 ctr_qtm_tracking_live = 0;
static u8 ctr_qtm_frame = 0;
static s8 ctr_eye_shift_px = 0;
static s8 ctr_eye_shift_left_px = 0;
static s8 ctr_eye_shift_right_px = 0;
static s16 ctr_focus_score = 100;
static float ctr_eye_shift_left_f = 0.0f;
static float ctr_eye_shift_right_f = 0.0f;
static float ctr_qtm_distance_cm = 0.0f;
static float ctr_qtm_tilt_deg = 0.0f;
static float ctr_qtm_lux = 0.0f;
static float ctr_qtm_confidence = 0.0f;
static float ctr_visual_disturbance = 0.0f;
static float ctr_audio_disturbance = 0.0f;
static float ctr_audio_reference = 0.0f;
static float ctr_sinus_pressure = 0.0f;
static float ctr_eye_strain = 0.0f;
static float ctr_focus_load = 0.0f;
static float ctr_audio_band_a = 0.0f;
static float ctr_audio_band_as = 0.0f;
static float ctr_audio_band_f = 0.0f;
static float ctr_audio_band_b = 0.0f;
static float ctr_audio_band_g = 0.0f;
static float ctr_profile_audio_bias = 0.65f;
static float ctr_profile_g_reference_weight = 0.35f;
static float ctr_profile_sinus_bias = 0.80f;
static float ctr_profile_focus_strain_weight = 1.15f;
static Result ctr_qtm_result = 0;
static Result ctr_mic_result = 0;
static QtmTrackingData ctr_qtm_tracking = {0};
static char ctr_qtm_status[32] = "QTM OFF";
static char ctr_mic_status[32] = "MIC OFF";
static char ctr_profile_source[48] = "defaults";
static u8 ctr_options_open = 0;
static u8 ctr_options_cursor = 0;
static u8 ctr_smoothing_mode = 2;
static u8 ctr_preset_index = 0;
static u8 ctr_profile_loaded = 0;
static u8 ctr_profile_mic_enabled = 1;
static u8 ctr_profile_telemetry_enabled = 1;
static u8 ctr_profile_telemetry_interval = 45;
static u8 ctr_mic_available = 0;
static u8 ctr_mic_live = 0;
static u8 ctr_runtime_frame = 0;
static u8 ctr_mic_buffer[CTR_MIC_BUFFER_SIZE] __attribute__((aligned(0x1000)));

typedef struct CtrStereoPreset {
    const char *name;
    u8 comfort;
    u8 force_flat;
    u8 smoothing_mode;
} CtrStereoPreset;

static const CtrStereoPreset ctr_stereo_presets[] = {
    { "studio-balanced", 1, 0, 2 },
    { "bright-floor-demo", 1, 0, 1 },
    { "low-strain-mono", 1, 1, 2 }
};

#define CTR_STEREO_PRESET_COUNT ((u8)(sizeof(ctr_stereo_presets) / sizeof(ctr_stereo_presets[0])))
#define CTR_STEREO_PRESET_CUSTOM 255

static void ctr_qtm_init(void);
static void ctr_qtm_update(void);
static void ctr_profile_load(void);
static void ctr_profile_write_status(void);
static void ctr_mic_init(void);
static void ctr_mic_update(void);
static void ctr_mic_exit(void);
static void ctr_update_strain_model(s16 focus_estimate);
static s8 ctr_compute_eye_shift(void);
static void ctr_update_parallax(void);
static void ctr_options_handle_input(u32 keys_down);
static const char *ctr_smoothing_label(void);
static const char *ctr_preset_label(void);
static void ctr_apply_preset(u8 preset_index);
static void ctr_sync_preset_index(void);
static void ctr_draw_status_panel(void);
#endif

/* Framebuffer: 1 byte per pixel, 0–3 shade index */
static u8 fb[SCREEN_H][SCREEN_W];

/* Tile map: BKG_ROWS×BKG_COLS tile indices */
static u8 bkg_map[BKG_ROWS][BKG_COLS];

/* Tile data: up to 256 background tiles, 16 bytes each (2bpp) */
static u8 bkg_tiles[256][16];

/* OBJ (sprite) table: 40 entries */
typedef struct { s16 x; s16 y; u8 tile; u8 flags; u8 active; } ObjEntry;
static ObjEntry obj_table[40];

/* Sprite tile data: up to 128 tiles */
static u8 spr_tiles[128][16];

static u8 host_audio_scene = 0xFF;
static u8 host_audio_genre = 0xFF;
static u8 host_audio_tension = 0xFF;
static u8 host_audio_pulse = 0xFF;
static u8 host_audio_voice = 0xFF;
static u8 host_audio_noise = 0xFF;
static u8 host_audio_last_event = 0xFF;
static u8 host_audio_last_value = 0xFF;
static u8 host_audio_last_speaker = 0xFF;
static char host_audio_last_line[32];
static u8 host_autoplay_enabled = 0;
static u8 host_autoplay_stage_limit = 0;
static u8 host_autoplay_stages_cleared = 0;
static u8 host_autoplay_hold_mask = 0;
static u8 host_autoplay_hold_frames = 0;
static u8 host_autoplay_last_phase = 0xFF;

#ifdef TARGET_HOST
static void host_autoplay_init(void);
static u8 host_autoplay_buttons(void);
#endif

/* Input state */
#ifdef TARGET_3DS
static u32 _joy_prev = 0;
static u32 _joy_cur  = 0;
static inline u8 plat_held(u32 mask)     { return (_joy_cur  & mask) ? 1 : 0; }
static inline u8 plat_pressed(u32 mask)  {
    return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
}
#else
static u8 _joy_prev = 0;
static u8 _joy_cur  = 0;
static inline u8 plat_held(u8 mask)     { return (_joy_cur  & mask) ? 1 : 0; }
static inline u8 plat_pressed(u8 mask)  {
    return ((_joy_cur & mask) && !(_joy_prev & mask)) ? 1 : 0;
}
#endif
static inline u16 plat_input_mask(void) { return (u16)_joy_cur; }
#ifdef TARGET_3DS
static inline u16 plat_pressed_mask(void) { return (u16)(_joy_cur & (u32)(~_joy_prev)); }
#else
static inline u16 plat_pressed_mask(void) { return (u16)(_joy_cur & (u8)(~_joy_prev)); }
#endif

#ifdef HAS_SDL2
static SDL_Window   *sdl_window   = NULL;
static SDL_Renderer *sdl_renderer = NULL;
static SDL_Texture  *sdl_texture  = NULL;
#define SCALE 3
#define HOST_AUDIO_RATE 22050
#define HOST_AUDIO_CHANNELS 2
#define HOST_AUDIO_WAVE_LEN 128
#define HOST_MIC_RING_SAMPLES 4096
static SDL_AudioDeviceID sdl_audio_device = 0;
static SDL_AudioDeviceID sdl_mic_device = 0;
static SDL_AudioSpec sdl_audio_spec;
static s16 host_wave_triangle[HOST_AUDIO_WAVE_LEN];
static s16 host_wave_saw[HOST_AUDIO_WAVE_LEN];
static s16 host_wave_pulse[HOST_AUDIO_WAVE_LEN];
static s16 host_wave_organ[HOST_AUDIO_WAVE_LEN];
static s16 host_wave_bow[HOST_AUDIO_WAVE_LEN];
static s16 host_wave_bell[HOST_AUDIO_WAVE_LEN];
static s16 host_mic_ring[HOST_MIC_RING_SAMPLES];
static u16 host_mic_read = 0;
static u16 host_mic_write = 0;
static u16 host_mic_count = 0;
static u32 host_phase_a = 0;
static u32 host_phase_b = 0;
static u32 host_phase_c = 0;
static u32 host_tick_phase = 0;
static u32 host_tick_step = 1;
static u32 host_noise_lfsr = 0x13579BDFu;
static u8 host_music_step = 0;
static u8 host_audio_live = 0;
static u8 host_mic_live = 0;
#endif

static void host_render_frame(void);

static void plat_poll_input(void) {
    _joy_prev = _joy_cur;
    _joy_cur  = 0;
#ifdef TARGET_3DS
    u32 keys_down;
    hidScanInput();
    keys_down = hidKeysDown();
    if (keys_down & KEY_L) ctr_options_open ^= 1;
    if (ctr_options_open) {
        ctr_options_handle_input(keys_down);
    } else {
        _joy_cur = hidKeysHeld();
    }
    ctr_mic_update();
    ctr_qtm_update();
    ctr_runtime_frame++;
    if (ctr_profile_telemetry_enabled && ctr_profile_telemetry_interval > 0 && (ctr_runtime_frame % ctr_profile_telemetry_interval) == 0) {
        ctr_profile_write_status();
    }
#endif
#ifdef HAS_SDL2
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        if (e.type == SDL_QUIT) { extern int g_quit; g_quit = 1; }
    }
    const u8 *ks = SDL_GetKeyboardState(NULL);
    if (ks[SDL_SCANCODE_UP]    || ks[SDL_SCANCODE_W])      _joy_cur |= BTN_UP;
    if (ks[SDL_SCANCODE_DOWN]  || ks[SDL_SCANCODE_S])      _joy_cur |= BTN_DOWN;
    if (ks[SDL_SCANCODE_LEFT]  || ks[SDL_SCANCODE_A])      _joy_cur |= BTN_LEFT;
    if (ks[SDL_SCANCODE_RIGHT] || ks[SDL_SCANCODE_D])      _joy_cur |= BTN_RIGHT;
    if (ks[SDL_SCANCODE_Z]     || ks[SDL_SCANCODE_COMMA])  _joy_cur |= BTN_A;
    if (ks[SDL_SCANCODE_X]     || ks[SDL_SCANCODE_PERIOD]) _joy_cur |= BTN_B;
    if (ks[SDL_SCANCODE_RETURN]|| ks[SDL_SCANCODE_KP_ENTER]) _joy_cur |= BTN_START;
    if (ks[SDL_SCANCODE_RSHIFT]|| ks[SDL_SCANCODE_LSHIFT])   _joy_cur |= BTN_SELECT;
    if (host_autoplay_enabled) _joy_cur |= host_autoplay_buttons();
#endif
}

static void plat_vsync(void) {
#ifdef TARGET_3DS
    gspWaitForVBlank();
#endif
    host_render_frame();
#ifdef HAS_SDL2
    SDL_Delay(16);
#endif
#ifdef TARGET_3DS
    gfxFlushBuffers();
    gfxSwapBuffers();
#endif
}

static void plat_set_bkg_tile(u8 x, u8 y, u8 tile) {
    if (x < BKG_COLS && y < BKG_ROWS) bkg_map[y][x] = tile;
}
static void plat_set_sprite(u8 id, s16 x, s16 y, u8 tile, u8 flags) {
    if (id < 40) {
        obj_table[id].x = x;
        obj_table[id].y = y;
        obj_table[id].tile = tile;
        obj_table[id].flags = flags;
        obj_table[id].active = 1;
    }
}
static void plat_load_bkg_tiles(const u8 *data, u8 first, u8 count) {
    for (int i = 0; i < count; ++i)
        memcpy(bkg_tiles[first + i], data + i * 16, 16);
}
static void plat_load_sprite_tiles(const u8 *data, u8 first, u8 count) {
    for (int i = 0; i < count; ++i)
        memcpy(spr_tiles[first + i], data + i * 16, 16);
}
static void plat_delay_frames(u8 n) {
    for (u8 i = 0; i < n; ++i) plat_vsync();
}

/* Decode 2bpp tile row into framebuffer */
static void host_render_tile(u8 tx, u8 ty, const u8 *tile_data, u8 is_sprite, s16 ox, s16 oy, u8 flags) {
    s16 px_base = is_sprite ? ox : (s16)(tx * TILE_W);
    s16 py_base = is_sprite ? oy : (s16)(ty * TILE_H);
    for (int row = 0; row < 8; ++row) {
        u8 sample_row = (flags & 0x40) ? (u8)(7 - row) : (u8)row;
        u8 lo = tile_data[sample_row * 2 + 0];
        u8 hi = tile_data[sample_row * 2 + 1];
        for (int col = 0; col < 8; ++col) {
            u8 sample_col = (flags & 0x20) ? (u8)(7 - col) : (u8)col;
            u8 bit = (u8)(7 - sample_col);
            u8 shade = ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1);
            s16 px = px_base + col;
            s16 py = py_base + row;
            if (px >= 0 && px < SCREEN_W && py >= 0 && py < SCREEN_H) {
                if (is_sprite && shade == 0) continue; /* transparent */
                fb[py][px] = shade;
            }
        }
    }
}

static void host_render_sprite_shadow(const u8 *tile_data, s16 ox, s16 oy, u8 flags, s8 shadow_x, s8 shadow_y, u8 shade_floor) {
    for (int row = 0; row < 8; ++row) {
        u8 sample_row = (flags & 0x40) ? (u8)(7 - row) : (u8)row;
        u8 lo = tile_data[sample_row * 2 + 0];
        u8 hi = tile_data[sample_row * 2 + 1];
        for (int col = 0; col < 8; ++col) {
            u8 sample_col = (flags & 0x20) ? (u8)(7 - col) : (u8)col;
            u8 bit = (u8)(7 - sample_col);
            u8 shade = ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1);
            s16 px;
            s16 py;
            if (shade == 0) continue;
            px = (s16)(ox + col + shadow_x);
            py = (s16)(oy + row + shadow_y);
            if (px < 0 || px >= SCREEN_W || py < 0 || py >= SCREEN_H) continue;
            if (fb[py][px] < shade_floor) fb[py][px] = shade_floor;
        }
    }
}

static void host_render_sprite_outline(const u8 *tile_data, s16 ox, s16 oy, u8 flags) {
    for (int row = 0; row < 8; ++row) {
        u8 sample_row = (flags & 0x40) ? (u8)(7 - row) : (u8)row;
        u8 lo = tile_data[sample_row * 2 + 0];
        u8 hi = tile_data[sample_row * 2 + 1];
        for (int col = 0; col < 8; ++col) {
            u8 sample_col = (flags & 0x20) ? (u8)(7 - col) : (u8)col;
            u8 bit = (u8)(7 - sample_col);
            u8 shade = ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1);
            if (shade == 0) continue;
            for (int y_off = -1; y_off <= 1; ++y_off) {
                for (int x_off = -1; x_off <= 1; ++x_off) {
                    s16 px = (s16)(ox + col + x_off);
                    s16 py = (s16)(oy + row + y_off);
                    if (x_off == 0 && y_off == 0) continue;
                    if (px < 0 || px >= SCREEN_W || py < 0 || py >= SCREEN_H) continue;
                    if (fb[py][px] < 2) fb[py][px] = 3;
                }
            }
        }
    }
}

static void host_render_frame(void) {
    memset(fb, 0, sizeof(fb));
    /* Render BKG map */
    for (int row = 0; row < BKG_ROWS; ++row)
        for (int col = 0; col < BKG_COLS; ++col)
            host_render_tile((u8)col, (u8)row, bkg_tiles[bkg_map[row][col]], 0, 0, 0, 0);
    /* Render OBJ */
    for (int i = 0; i < 40; ++i)
        if (obj_table[i].active) {
            host_render_sprite_shadow(spr_tiles[obj_table[i].tile], obj_table[i].x, obj_table[i].y, obj_table[i].flags, 1, 1, 2);
            host_render_sprite_outline(spr_tiles[obj_table[i].tile], obj_table[i].x, obj_table[i].y, obj_table[i].flags);
            host_render_tile(0, 0, spr_tiles[obj_table[i].tile], 1,
                             obj_table[i].x, obj_table[i].y, obj_table[i].flags);
        }
#ifdef TARGET_3DS
    {
        u8 *left_fb;
        int origin_x = (CTR_TOP_W - CTR_VIEW_W) / 2;
        ctr_3d_slider = osGet3DSliderState();
        ctr_update_parallax();
        if (ctr_eye_shift_left_px > 0 || ctr_eye_shift_right_px > 0) {
            gfxSet3D(true);
        } else {
            gfxSet3D(false);
        }
        left_fb = gfxGetFramebuffer(GFX_TOP, GFX_LEFT, NULL, NULL);
        memset(left_fb, 0, CTR_TOP_W * CTR_TOP_H * 3);
        for (int dy = 0; dy < CTR_VIEW_H; ++dy) {
            int sy = (dy * SCREEN_H) / CTR_VIEW_H;
            int y_rot = CTR_TOP_H - 1 - dy;
            for (int dx = 0; dx < CTR_VIEW_W; ++dx) {
                int sx = (dx * SCREEN_W) / CTR_VIEW_W;
                int out_x = origin_x + dx - ctr_eye_shift_left_px;
                if (out_x < 0 || out_x >= CTR_TOP_W) continue;
                {
                    size_t off = (size_t)(3 * (out_x * CTR_TOP_H + y_rot));
                    u32 rgb = ctr_palette[fb[sy][sx] & 3];
                    left_fb[off + 0] = (u8)(rgb & 0xFF);
                    left_fb[off + 1] = (u8)((rgb >> 8) & 0xFF);
                    left_fb[off + 2] = (u8)((rgb >> 16) & 0xFF);
                }
            }
        }
        if (ctr_eye_shift_left_px > 0 || ctr_eye_shift_right_px > 0) {
            u8 *right_fb = gfxGetFramebuffer(GFX_TOP, GFX_RIGHT, NULL, NULL);
            memset(right_fb, 0, CTR_TOP_W * CTR_TOP_H * 3);
            for (int dy = 0; dy < CTR_VIEW_H; ++dy) {
                int sy = (dy * SCREEN_H) / CTR_VIEW_H;
                int y_rot = CTR_TOP_H - 1 - dy;
                for (int dx = 0; dx < CTR_VIEW_W; ++dx) {
                    int sx = (dx * SCREEN_W) / CTR_VIEW_W;
                    int out_x = origin_x + dx + ctr_eye_shift_right_px;
                    if (out_x < 0 || out_x >= CTR_TOP_W) continue;
                    {
                        size_t off = (size_t)(3 * (out_x * CTR_TOP_H + y_rot));
                        u32 rgb = ctr_palette[fb[sy][sx] & 3];
                        right_fb[off + 0] = (u8)(rgb & 0xFF);
                        right_fb[off + 1] = (u8)((rgb >> 8) & 0xFF);
                        right_fb[off + 2] = (u8)((rgb >> 16) & 0xFF);
                    }
                }
            }
        }
        ctr_draw_status_panel();
    }
#endif
#ifdef HAS_SDL2
    if (!sdl_texture) return;
    u32 pixels[SCREEN_H * SCREEN_W];
    for (int y = 0; y < SCREEN_H; ++y)
        for (int x = 0; x < SCREEN_W; ++x)
            pixels[y * SCREEN_W + x] = gb_palette[fb[y][x] & 3];
    SDL_UpdateTexture(sdl_texture, NULL, pixels, SCREEN_W * sizeof(u32));
    SDL_RenderClear(sdl_renderer);
    SDL_RenderCopy(sdl_renderer, sdl_texture, NULL, NULL);
    SDL_RenderPresent(sdl_renderer);
#endif
}

#ifdef HAS_SDL2
static u16 host_note_hz(u8 semitone, u8 octave) {
    static const u16 base_hz[12] = { 65, 69, 73, 78, 82, 87, 93, 98, 104, 110, 117, 123 };
    u16 hz = base_hz[semitone % 12];
    if (octave > 2) hz = (u16)(hz << (octave - 2));
    return hz;
}

static u32 host_phase_step_for_hz(u16 hz) {
    u32 step = (u32)hz * HOST_AUDIO_WAVE_LEN * 65536u;
    step /= HOST_AUDIO_RATE;
    if (step == 0) step = 1;
    return step;
}

static void host_audio_init_tables(void) {
    for (u16 i = 0; i < HOST_AUDIO_WAVE_LEN; ++i) {
        s32 tri;
        s32 saw;
        s32 pulse;
        s32 organ;
        s32 bow;
        s32 bell;
        if (i < HOST_AUDIO_WAVE_LEN / 2) tri = -32767 + (i * 4 * 32767) / HOST_AUDIO_WAVE_LEN;
        else tri = 32767 - ((i - HOST_AUDIO_WAVE_LEN / 2) * 4 * 32767) / HOST_AUDIO_WAVE_LEN;
        saw = -32767 + (i * 65534) / HOST_AUDIO_WAVE_LEN;
        pulse = (i < (HOST_AUDIO_WAVE_LEN / 4)) ? 28000 : -28000;
        organ = (tri * 3 + saw + pulse) / 5;
        bow = (tri * 5 + organ * 3) / 8;
        bell = (saw * 2 + pulse * 2 + (((i + 4) % 16) < 3 ? 22000 : -9000)) / 5;
        host_wave_triangle[i] = (s16)tri;
        host_wave_saw[i] = (s16)saw;
        host_wave_pulse[i] = (s16)pulse;
        host_wave_organ[i] = (s16)organ;
        host_wave_bow[i] = (s16)bow;
        host_wave_bell[i] = (s16)bell;
    }
}

static const s16 *host_audio_drone_wave(void) {
    if (host_audio_scene == 3 || host_audio_scene == 7) return host_wave_bow;
    if (host_audio_scene == 1 || host_audio_scene == 4) return host_wave_organ;
    if (host_audio_noise >= 8) return host_wave_saw;
    return host_wave_triangle;
}

static const s16 *host_audio_pulse_wave(void) {
    if (host_audio_scene == 5) return host_wave_saw;
    if (host_audio_scene == 6) return host_wave_bell;
    if (host_audio_voice == 4) return host_wave_pulse;
    return host_wave_organ;
}

static const s16 *host_audio_lead_wave(void) {
    if (host_audio_voice == 1) return host_wave_bell;
    if (host_audio_voice == 2) return host_wave_bow;
    if (host_audio_voice == 3) return host_wave_saw;
    return host_wave_pulse;
}

static void host_mic_push_sample(s16 sample) {
    host_mic_ring[host_mic_write] = sample;
    host_mic_write = (u16)((host_mic_write + 1) % HOST_MIC_RING_SAMPLES);
    if (host_mic_count < HOST_MIC_RING_SAMPLES) host_mic_count++;
    else host_mic_read = (u16)((host_mic_read + 1) % HOST_MIC_RING_SAMPLES);
}

static s16 host_mic_pop_sample(void) {
    s16 sample;
    if (host_mic_count == 0) return 0;
    sample = host_mic_ring[host_mic_read];
    host_mic_read = (u16)((host_mic_read + 1) % HOST_MIC_RING_SAMPLES);
    host_mic_count--;
    return sample;
}

static u8 host_audio_mode_step(u8 genre, u8 degree) {
    static const u8 mode_table[12][7] = {
        {0,2,3,5,7,8,10},
        {0,1,3,5,7,8,10},
        {0,2,3,5,6,8,10},
        {0,1,3,5,6,8,10},
        {0,2,4,5,7,8,11},
        {0,1,4,5,7,8,10},
        {0,2,3,6,7,9,10},
        {0,1,3,5,7,8,11},
        {0,2,3,5,7,9,10},
        {0,1,3,5,7,9,10},
        {0,2,4,6,7,9,11},
        {0,2,3,5,7,8,11}
    };
    return mode_table[genre % 12][degree % 7];
}

static u16 host_audio_stage_root(u8 genre) {
    static const u8 root_table[12] = { 0, 9, 2, 11, 5, 7, 10, 3, 8, 1, 6, 4 };
    return root_table[genre % 12];
}

static s16 host_wave_sample(const s16 *table, u32 *phase, u32 step, s16 gain) {
    u16 index = (u16)((*phase >> 16) & (HOST_AUDIO_WAVE_LEN - 1));
    *phase += step;
    return (s16)((table[index] * gain) / 32767);
}

static void host_audio_capture_samples(void) {
    if (!host_mic_live || sdl_mic_device == 0) return;
    {
        s16 capture_buf[256];
        Uint32 got = SDL_DequeueAudio(sdl_mic_device, capture_buf, sizeof(capture_buf));
        u32 samples = got / sizeof(s16);
        for (u32 i = 0; i < samples; ++i) host_mic_push_sample(capture_buf[i]);
    }
}

static void host_audio_callback(void *userdata, Uint8 *stream, int len) {
    s16 *out = (s16*)stream;
    int frames = len / (int)(sizeof(s16) * HOST_AUDIO_CHANNELS);
    const s16 *drone_wave = host_audio_drone_wave();
    const s16 *pulse_wave = host_audio_pulse_wave();
    const s16 *lead_wave = host_audio_lead_wave();
    u8 genre = host_audio_genre % 12;
    u8 root = (u8)host_audio_stage_root(genre);
    u8 pulse_degree = (u8)((host_music_step + host_audio_pulse) % 7);
    u8 lead_degree = (u8)((host_music_step + host_audio_tension + host_audio_voice) % 7);
    u32 drone_step = host_phase_step_for_hz(host_note_hz(root, 2));
    u32 pulse_step = host_phase_step_for_hz(host_note_hz((u8)((root + host_audio_mode_step(genre, pulse_degree)) % 12), 3));
    u32 lead_step = host_phase_step_for_hz(host_note_hz((u8)((root + host_audio_mode_step(genre, lead_degree)) % 12), 4));
    u16 tick_hz = (u16)(2 + host_audio_pulse + (host_audio_tension >> 1));
    if (tick_hz > 14) tick_hz = 14;
    host_tick_step = (u32)(tick_hz * 65536u / HOST_AUDIO_RATE);
    (void)userdata;
    host_audio_capture_samples();
    for (int i = 0; i < frames; ++i) {
        s32 sample = 0;
        s16 mic = 0;
        host_tick_phase += host_tick_step;
        if (host_tick_phase >= 65536u) {
            host_tick_phase -= 65536u;
            host_music_step = (u8)((host_music_step + 1) & 0x07);
        }
        sample += host_wave_sample(drone_wave, &host_phase_a, drone_step, (s16)(6000 + host_audio_noise * 300));
        sample += host_wave_sample(pulse_wave, &host_phase_b, pulse_step, (s16)(3500 + host_audio_pulse * 600));
        sample += host_wave_sample(lead_wave, &host_phase_c, lead_step, (s16)(2000 + host_audio_tension * 700));
        host_noise_lfsr = (host_noise_lfsr >> 1) ^ (u32)(-(s32)(host_noise_lfsr & 1u) & 0xD0000001u);
        sample += (s16)(((s16)(host_noise_lfsr & 0xFFFF) - 16384) * (400 + host_audio_noise * 220) / 32768);
        if ((host_audio_noise >= 4 || host_audio_scene == 5) && host_mic_count > 0) {
            mic = host_mic_pop_sample();
            sample += (mic * (3000 + host_audio_noise * 300)) / 32768;
        }
        if (host_audio_scene == 3) sample = (sample * 3) / 4;
        if (host_audio_scene == 7) sample = (sample * 2) / 5;
        if (sample > 32767) sample = 32767;
        if (sample < -32768) sample = -32768;
        out[i * 2 + 0] = (s16)sample;
        out[i * 2 + 1] = (s16)((sample * 7) / 8 + mic / 12);
    }
}

static void host_audio_open_devices(void) {
    SDL_AudioSpec want;
    memset(&want, 0, sizeof(want));
    host_audio_init_tables();
    want.freq = HOST_AUDIO_RATE;
    want.format = AUDIO_S16SYS;
    want.channels = HOST_AUDIO_CHANNELS;
    want.samples = 512;
    want.callback = host_audio_callback;
    sdl_audio_device = SDL_OpenAudioDevice(NULL, 0, &want, &sdl_audio_spec, 0);
    if (sdl_audio_device != 0) {
        host_audio_live = 1;
        SDL_PauseAudioDevice(sdl_audio_device, 0);
    }
    memset(&want, 0, sizeof(want));
    want.freq = HOST_AUDIO_RATE;
    want.format = AUDIO_S16SYS;
    want.channels = 1;
    want.samples = 512;
    want.callback = NULL;
    sdl_mic_device = SDL_OpenAudioDevice(NULL, 1, &want, NULL, 0);
    if (sdl_mic_device != 0) {
        host_mic_live = 1;
        SDL_PauseAudioDevice(sdl_mic_device, 0);
    }
}
#endif

static void host_clear_sprites(void) {
    for (int i = 0; i < 40; ++i) obj_table[i].active = 0;
}

static void plat_audio_reset(void) {
    host_audio_scene = 0xFF;
    host_audio_genre = 0xFF;
    host_audio_tension = 0xFF;
    host_audio_pulse = 0xFF;
    host_audio_voice = 0xFF;
    host_audio_noise = 0xFF;
    host_audio_last_event = 0xFF;
    host_audio_last_value = 0xFF;
    host_audio_last_speaker = 0xFF;
    host_audio_last_line[0] = '\0';
}

static void plat_audio_profile(u8 scene, u8 genre, u8 tension, u8 pulse, u8 voice, u8 noise) {
    if (scene == host_audio_scene && genre == host_audio_genre && tension == host_audio_tension &&
        pulse == host_audio_pulse && voice == host_audio_voice && noise == host_audio_noise) return;
    host_audio_scene = scene;
    host_audio_genre = genre;
    host_audio_tension = tension;
    host_audio_pulse = pulse;
    host_audio_voice = voice;
    host_audio_noise = noise;
#ifdef TARGET_HOST
    printf("[AIASMR] sc=%u gn=%u tn=%u pu=%u vc=%u nz=%u\n",
           scene, genre, tension, pulse, voice, noise);
    fflush(stdout);
#endif
}

static void plat_audio_event(u8 event_kind, u8 value) {
    if (event_kind == host_audio_last_event && value == host_audio_last_value) return;
    host_audio_last_event = event_kind;
    host_audio_last_value = value;
#ifdef TARGET_HOST
    printf("[AIASMR-EVENT] ev=%u val=%u\n", event_kind, value);
    fflush(stdout);
#endif
}

static void plat_audio_tts(u8 speaker, const char *line) {
    if (line == NULL || line[0] == '\0') return;
    if (speaker == host_audio_last_speaker && strcmp(line, host_audio_last_line) == 0) return;
    host_audio_last_speaker = speaker;
    strncpy(host_audio_last_line, line, sizeof(host_audio_last_line) - 1);
    host_audio_last_line[sizeof(host_audio_last_line) - 1] = '\0';
#ifdef TARGET_HOST
    printf("[TTS] sp=%u %s\n", speaker, host_audio_last_line);
    fflush(stdout);
#endif
}

#ifdef TARGET_3DS
static float ctr_clampf(float value, float min_value, float max_value) {
    if (value < min_value) return min_value;
    if (value > max_value) return max_value;
    return value;
}

static int ctr_parse_json_bool(const char *text, const char *key, int fallback) {
    const char *marker = strstr(text, key);
    const char *colon;
    if (!marker) return fallback;
    colon = strchr(marker, ':');
    if (!colon) return fallback;
    colon++;
    while (*colon == ' ' || *colon == '\t' || *colon == '\r' || *colon == '\n') colon++;
    if (strncmp(colon, "true", 4) == 0) return 1;
    if (strncmp(colon, "false", 5) == 0) return 0;
    return fallback;
}

static float ctr_parse_json_float(const char *text, const char *key, float fallback) {
    const char *marker = strstr(text, key);
    const char *colon;
    char *end_ptr;
    float value;
    if (!marker) return fallback;
    colon = strchr(marker, ':');
    if (!colon) return fallback;
    colon++;
    value = strtof(colon, &end_ptr);
    if (end_ptr == colon) return fallback;
    return value;
}

static unsigned ctr_parse_json_uint(const char *text, const char *key, unsigned fallback) {
    const char *marker = strstr(text, key);
    const char *colon;
    char *end_ptr;
    unsigned long value;
    if (!marker) return fallback;
    colon = strchr(marker, ':');
    if (!colon) return fallback;
    colon++;
    value = strtoul(colon, &end_ptr, 10);
    if (end_ptr == colon) return fallback;
    return (unsigned)value;
}

static int ctr_parse_json_string(const char *text, const char *key, char *dest, size_t dest_size) {
    const char *marker = strstr(text, key);
    const char *colon;
    const char *start;
    const char *end;
    size_t length;
    if (!marker || dest_size == 0) return 0;
    colon = strchr(marker, ':');
    if (!colon) return 0;
    start = strchr(colon, '"');
    if (!start) return 0;
    start++;
    end = strchr(start, '"');
    if (!end) return 0;
    length = (size_t)(end - start);
    if (length >= dest_size) length = dest_size - 1;
    memcpy(dest, start, length);
    dest[length] = '\0';
    return 1;
}

static u8 ctr_preset_index_from_name(const char *name) {
    u8 i;
    if (!name || !name[0]) return CTR_STEREO_PRESET_CUSTOM;
    for (i = 0; i < CTR_STEREO_PRESET_COUNT; ++i) {
        if (strcmp(name, ctr_stereo_presets[i].name) == 0) return i;
    }
    return CTR_STEREO_PRESET_CUSTOM;
}

static void ctr_profile_load(void) {
    static const char *paths[] = {
        "ndsx_profile.json",
        CTR_PROFILE_PATH,
        "sdmc:/3ds/kaijugaiden/ndsx_profile.json"
    };
    char profile_text[4096];
    char startup_preset[32];
    char smoothing[32];
    size_t bytes_read;
    FILE *file = NULL;
    u8 preset_index;
    unsigned interval;
    size_t i;

    for (i = 0; i < sizeof(paths) / sizeof(paths[0]); ++i) {
        file = fopen(paths[i], "rb");
        if (file) {
            strncpy(ctr_profile_source, paths[i], sizeof(ctr_profile_source) - 1);
            ctr_profile_source[sizeof(ctr_profile_source) - 1] = '\0';
            break;
        }
    }

    if (!file) {
        strncpy(ctr_profile_source, "defaults", sizeof(ctr_profile_source) - 1);
        ctr_profile_source[sizeof(ctr_profile_source) - 1] = '\0';
        ctr_profile_loaded = 0;
        ctr_sync_preset_index();
        return;
    }

    bytes_read = fread(profile_text, 1, sizeof(profile_text) - 1, file);
    fclose(file);
    profile_text[bytes_read] = '\0';

    startup_preset[0] = '\0';
    smoothing[0] = '\0';

    ctr_profile_loaded = 1;
    ctr_profile_mic_enabled = (u8)ctr_parse_json_bool(profile_text, "\"microphoneEnabled\"", ctr_profile_mic_enabled);
    ctr_profile_telemetry_enabled = (u8)ctr_parse_json_bool(profile_text, "\"telemetryEnabled\"", ctr_profile_telemetry_enabled);
    ctr_profile_audio_bias = ctr_parse_json_float(profile_text, "\"audioBiasStrength\"", ctr_profile_audio_bias);
    ctr_profile_g_reference_weight = ctr_parse_json_float(profile_text, "\"gReferenceWeight\"", ctr_profile_g_reference_weight);
    ctr_profile_sinus_bias = ctr_parse_json_float(profile_text, "\"sinusPressureBias\"", ctr_profile_sinus_bias);
    ctr_profile_focus_strain_weight = ctr_parse_json_float(profile_text, "\"focusStrainWeight\"", ctr_profile_focus_strain_weight);
    interval = ctr_parse_json_uint(profile_text, "\"telemetryIntervalFrames\"", ctr_profile_telemetry_interval);
    ctr_profile_telemetry_interval = (u8)(interval > 0 && interval < 255 ? interval : ctr_profile_telemetry_interval);

    if (ctr_parse_json_string(profile_text, "\"startupPreset\"", startup_preset, sizeof(startup_preset))) {
        preset_index = ctr_preset_index_from_name(startup_preset);
        if (preset_index != CTR_STEREO_PRESET_CUSTOM) ctr_apply_preset(preset_index);
    }

    ctr_stereo_comfort = (u8)ctr_parse_json_bool(profile_text, "\"comfortDefault\"", ctr_stereo_comfort);
    ctr_stereo_force_flat = (u8)ctr_parse_json_bool(profile_text, "\"forceFlatDefault\"", ctr_stereo_force_flat);
    if (ctr_parse_json_string(profile_text, "\"smoothingDefault\"", smoothing, sizeof(smoothing))) {
        if (strcmp(smoothing, "off") == 0) ctr_smoothing_mode = 0;
        else if (strcmp(smoothing, "balanced") == 0) ctr_smoothing_mode = 1;
        else ctr_smoothing_mode = 2;
    }
    ctr_sync_preset_index();
}

static float ctr_measure_band_energy(const s16 *samples, u32 count, float sample_rate, float frequency, float rms) {
    float phase = 0.0f;
    float phase_step = (2.0f * 3.14159265f * frequency) / sample_rate;
    float real = 0.0f;
    float imag = 0.0f;
    u32 i;
    if (count == 0 || rms <= 0.0f) return 0.0f;
    for (i = 0; i < count; ++i) {
        real += (float)samples[i] * cosf(phase);
        imag += (float)samples[i] * sinf(phase);
        phase += phase_step;
    }
    return sqrtf(real * real + imag * imag) / ((rms * (float)count) + 1.0f);
}

static void ctr_mic_init(void) {
    u32 sample_size;
    if (!ctr_profile_mic_enabled) {
        strncpy(ctr_mic_status, "MIC DISABLED", sizeof(ctr_mic_status) - 1);
        ctr_mic_status[sizeof(ctr_mic_status) - 1] = '\0';
        return;
    }
    memset(ctr_mic_buffer, 0, sizeof(ctr_mic_buffer));
    ctr_mic_result = micInit(ctr_mic_buffer, sizeof(ctr_mic_buffer));
    if (R_FAILED(ctr_mic_result)) {
        snprintf(ctr_mic_status, sizeof(ctr_mic_status), "MIC ERR %08lx", ctr_mic_result);
        return;
    }
    ctr_mic_available = 1;
    MICU_SetAllowShellClosed(false);
    MICU_SetClamp(true);
    MICU_SetGain(1);
    MICU_SetPower(true);
    sample_size = micGetSampleDataSize();
    ctr_mic_result = MICU_StartSampling(MICU_ENCODING_PCM16_SIGNED, MICU_SAMPLE_RATE_8180, 0, sample_size, true);
    if (R_FAILED(ctr_mic_result)) {
        snprintf(ctr_mic_status, sizeof(ctr_mic_status), "MIC START %08lx", ctr_mic_result);
        MICU_SetPower(false);
        micExit();
        ctr_mic_available = 0;
        return;
    }
    ctr_mic_live = 1;
    strncpy(ctr_mic_status, "MIC READY", sizeof(ctr_mic_status) - 1);
    ctr_mic_status[sizeof(ctr_mic_status) - 1] = '\0';
}

static void ctr_mic_update(void) {
    s16 window[CTR_MIC_WINDOW_SAMPLES];
    const s16 *ring_samples = (const s16 *)ctr_mic_buffer;
    u32 sample_count;
    u32 offset_samples;
    u32 i;
    float sum_sq = 0.0f;
    float rms;
    float dominant;
    float reference;
    float disturbance;

    if (!ctr_mic_live) return;
    if ((ctr_runtime_frame & 0x03) != 0) return;

    sample_count = micGetSampleDataSize() / sizeof(s16);
    if (sample_count < CTR_MIC_WINDOW_SAMPLES) return;
    offset_samples = micGetLastSampleOffset() / sizeof(s16);
    if (offset_samples >= sample_count) offset_samples %= sample_count;

    for (i = 0; i < CTR_MIC_WINDOW_SAMPLES; ++i) {
        u32 index = (offset_samples + sample_count - CTR_MIC_WINDOW_SAMPLES + i) % sample_count;
        window[i] = ring_samples[index];
        sum_sq += (float)window[i] * (float)window[i];
    }

    rms = sqrtf(sum_sq / (float)CTR_MIC_WINDOW_SAMPLES);
    if (rms < 180.0f) {
        ctr_audio_disturbance *= 0.88f;
        ctr_audio_reference *= 0.90f;
        strncpy(ctr_mic_status, "MIC QUIET", sizeof(ctr_mic_status) - 1);
        ctr_mic_status[sizeof(ctr_mic_status) - 1] = '\0';
        return;
    }

    ctr_audio_band_a = ctr_measure_band_energy(window, CTR_MIC_WINDOW_SAMPLES, 8182.1245f, 440.0f, rms);
    ctr_audio_band_as = ctr_measure_band_energy(window, CTR_MIC_WINDOW_SAMPLES, 8182.1245f, 466.16f, rms);
    ctr_audio_band_f = ctr_measure_band_energy(window, CTR_MIC_WINDOW_SAMPLES, 8182.1245f, 349.23f, rms);
    ctr_audio_band_b = ctr_measure_band_energy(window, CTR_MIC_WINDOW_SAMPLES, 8182.1245f, 493.88f, rms);
    ctr_audio_band_g = ctr_measure_band_energy(window, CTR_MIC_WINDOW_SAMPLES, 8182.1245f, 392.0f, rms);

    reference = ctr_audio_band_g * ctr_profile_g_reference_weight;
    dominant = ((ctr_audio_band_a > ctr_audio_band_as) ? ctr_audio_band_a : ctr_audio_band_as) * 1.15f;
    dominant += ctr_audio_band_f * 0.65f;
    dominant += ctr_audio_band_b * 0.85f;
    dominant += fabsf(ctr_audio_band_a - ctr_audio_band_as) * 0.35f;
    dominant += fabsf(ctr_audio_band_f - ctr_audio_band_b) * 0.25f;
    dominant -= reference;
    if (dominant < 0.0f) dominant = 0.0f;

    disturbance = ctr_clampf(dominant * ctr_profile_audio_bias, 0.0f, 1.0f);
    ctr_audio_disturbance += (disturbance - ctr_audio_disturbance) * 0.25f;
    ctr_audio_reference += (reference - ctr_audio_reference) * 0.2f;

    if (ctr_audio_disturbance > 0.70f) strncpy(ctr_mic_status, "MIC ALERT", sizeof(ctr_mic_status) - 1);
    else if (ctr_audio_disturbance > 0.35f) strncpy(ctr_mic_status, "MIC ACTIVE", sizeof(ctr_mic_status) - 1);
    else strncpy(ctr_mic_status, "MIC CALM", sizeof(ctr_mic_status) - 1);
    ctr_mic_status[sizeof(ctr_mic_status) - 1] = '\0';
}

static void ctr_mic_exit(void) {
    if (!ctr_mic_available) return;
    if (ctr_mic_live) {
        MICU_StopSampling();
        ctr_mic_live = 0;
    }
    MICU_SetPower(false);
    micExit();
    ctr_mic_available = 0;
}

static void ctr_profile_write_status(void) {
    static const char *paths[] = {
        CTR_STATUS_PATH,
        "ndsx_runtime_status.json"
    };
    FILE *file = NULL;
    size_t i;
    for (i = 0; i < sizeof(paths) / sizeof(paths[0]); ++i) {
        file = fopen(paths[i], "wb");
        if (file) break;
    }
    if (!file) return;
    fprintf(file,
            "{\n"
            "  \"profileLoaded\": %s,\n"
            "  \"profileSource\": \"%s\",\n"
            "  \"preset\": \"%s\",\n"
            "  \"focus\": %d,\n"
            "  \"stereoComfort\": %s,\n"
            "  \"forceFlat\": %s,\n"
            "  \"smoothing\": \"%s\",\n"
            "  \"qtmStatus\": \"%s\",\n"
            "  \"micStatus\": \"%s\",\n"
            "  \"visualDisturbance\": %.3f,\n"
            "  \"audioDisturbance\": %.3f,\n"
            "  \"sinusPressure\": %.3f,\n"
            "  \"eyeStrain\": %.3f,\n"
            "  \"focusLoad\": %.3f,\n"
            "  \"gReference\": %.3f,\n"
            "  \"distanceCm\": %.2f,\n"
            "  \"tiltDeg\": %.2f,\n"
            "  \"lux\": %.2f,\n"
            "  \"bands\": {\n"
            "    \"A\": %.3f,\n"
            "    \"A#\": %.3f,\n"
            "    \"F\": %.3f,\n"
            "    \"B\": %.3f,\n"
            "    \"G\": %.3f\n"
            "  }\n"
            "}\n",
            ctr_profile_loaded ? "true" : "false",
            ctr_profile_source,
            ctr_preset_label(),
            (int)ctr_focus_score,
            ctr_stereo_comfort ? "true" : "false",
            ctr_stereo_force_flat ? "true" : "false",
            ctr_smoothing_label(),
            ctr_qtm_status,
            ctr_mic_status,
            ctr_visual_disturbance,
            ctr_audio_disturbance,
            ctr_sinus_pressure,
            ctr_eye_strain,
            ctr_focus_load,
            ctr_audio_reference,
            ctr_qtm_distance_cm,
            ctr_qtm_tilt_deg,
            ctr_qtm_lux,
            ctr_audio_band_a,
            ctr_audio_band_as,
            ctr_audio_band_f,
            ctr_audio_band_b,
            ctr_audio_band_g);
    fclose(file);
}

static void ctr_qtm_init(void) {
    bool blacklisted = false;
    strncpy(ctr_qtm_status, "QTM OFF", sizeof(ctr_qtm_status) - 1);
    ctr_qtm_status[sizeof(ctr_qtm_status) - 1] = '\0';
    if (!qtmCheckServicesRegistered()) {
        strncpy(ctr_qtm_status, "QTM UNREGISTERED", sizeof(ctr_qtm_status) - 1);
        return;
    }
    ctr_qtm_result = qtmInit(QTM_SERVICE_SYSTEM);
    if (R_FAILED(ctr_qtm_result)) {
        snprintf(ctr_qtm_status, sizeof(ctr_qtm_status), "QTM ERR %08lx", ctr_qtm_result);
        return;
    }
    ctr_qtm_result = QTMU_IsCurrentAppBlacklisted(&blacklisted);
    if (R_FAILED(ctr_qtm_result) || blacklisted) {
        strncpy(ctr_qtm_status, blacklisted ? "QTM BLACKLISTED" : "QTM QUERY FAIL", sizeof(ctr_qtm_status) - 1);
        return;
    }
    ctr_qtm_available = 1;
    strncpy(ctr_qtm_status, "QTM READY", sizeof(ctr_qtm_status) - 1);
}

static void ctr_update_strain_model(s16 focus_estimate) {
    float sinus_raw = 0.0f;
    float focus_raw = ctr_clampf((100.0f - (float)focus_estimate) / 80.0f, 0.0f, 1.0f);
    float eye_target;
    ctr_focus_load += (focus_raw - ctr_focus_load) * 0.22f;
    if (ctr_qtm_tracking_live) {
        if (ctr_qtm_distance_cm < 25.0f) sinus_raw += (25.0f - ctr_qtm_distance_cm) / 16.0f;
        if (ctr_qtm_distance_cm > 47.0f) sinus_raw += (ctr_qtm_distance_cm - 47.0f) / 28.0f;
        if (fabsf(ctr_qtm_tilt_deg) > 8.0f) sinus_raw += (fabsf(ctr_qtm_tilt_deg) - 8.0f) / 18.0f;
        if (fabsf(ctr_qtm_tracking.dPitch) > 0.07f) sinus_raw += (fabsf(ctr_qtm_tracking.dPitch) - 0.07f) * 3.2f;
        if (fabsf(ctr_qtm_tracking.dYaw) > 0.10f) sinus_raw += (fabsf(ctr_qtm_tracking.dYaw) - 0.10f) * 2.4f;
        if (ctr_qtm_confidence < 0.68f) sinus_raw += (0.68f - ctr_qtm_confidence) * 1.4f;
    } else {
        sinus_raw += 0.18f;
    }
    if (ctr_qtm_lux < 14.0f) sinus_raw += (14.0f - ctr_qtm_lux) / 18.0f;
    if (ctr_qtm_lux > 165.0f) sinus_raw += (ctr_qtm_lux - 165.0f) / 240.0f;
    sinus_raw += ctr_audio_disturbance * 0.35f;
    sinus_raw += fabsf(ctr_audio_band_a - ctr_audio_band_as) * 0.20f;
    sinus_raw += fabsf(ctr_audio_band_f - ctr_audio_band_b) * 0.12f;
    sinus_raw *= ctr_profile_sinus_bias;
    sinus_raw = ctr_clampf(sinus_raw, 0.0f, 1.0f);
    ctr_sinus_pressure += (sinus_raw - ctr_sinus_pressure) * 0.20f;
    eye_target = ctr_sinus_pressure * (0.30f + ctr_focus_load * ctr_profile_focus_strain_weight);
    eye_target += ctr_visual_disturbance * 0.28f;
    eye_target += ctr_audio_disturbance * 0.18f;
    eye_target = ctr_clampf(eye_target, 0.0f, 1.0f);
    ctr_eye_strain += (eye_target - ctr_eye_strain) * 0.25f;
}

static void ctr_qtm_update(void) {
    s16 focus = 100;
    ctr_3d_slider = osGet3DSliderState();
    ctr_qtm_tracking_live = 0;
    if (!ctr_qtm_available) {
        focus = (ctr_stereo_force_flat ? 90 : (ctr_3d_slider > 0.7f ? 55 : 72));
        ctr_visual_disturbance = ctr_clampf((100.0f - (float)focus) / 75.0f, 0.0f, 1.0f);
        ctr_update_strain_model(focus);
        focus -= (s16)(ctr_audio_disturbance * 24.0f);
        focus -= (s16)(ctr_sinus_pressure * 18.0f);
        focus -= (s16)(ctr_eye_strain * 14.0f);
        if (focus < 20) focus = 20;
        ctr_focus_score = focus;
        return;
    }
    {
        QtmTrackingData sample = {0};
        ctr_qtm_result = QTMU_GetTrackingData(&sample);
        if (R_SUCCEEDED(ctr_qtm_result)) {
            ctr_qtm_tracking = sample;
            ctr_qtm_tracking_live = (u8)(sample.faceDetected && sample.eyesDetected);
            ctr_qtm_confidence = sample.confidenceLevel;
            ctr_qtm_tilt_deg = qtmComputeHeadTiltAngle(&sample) * (180.0f / 3.14159265f);
            ctr_qtm_distance_cm = qtmEstimateEyeToCameraDistance(&sample) / 10.0f;
            QTMS_GetCameraLuminance(&ctr_qtm_lux);
            if (ctr_qtm_tracking_live) {
                strncpy(ctr_qtm_status, "QTM TRACKING", sizeof(ctr_qtm_status) - 1);
                if (ctr_qtm_confidence < 0.60f) focus -= (s16)((0.60f - ctr_qtm_confidence) * 80.0f);
                if (fabsf(ctr_qtm_tracking.dYaw) > 0.12f) focus -= (s16)((fabsf(ctr_qtm_tracking.dYaw) - 0.12f) * 140.0f);
                if (fabsf(ctr_qtm_tracking.dPitch) > 0.10f) focus -= (s16)((fabsf(ctr_qtm_tracking.dPitch) - 0.10f) * 160.0f);
                if (fabsf(ctr_qtm_tilt_deg) > 10.0f) focus -= (s16)((fabsf(ctr_qtm_tilt_deg) - 10.0f) * 1.8f);
                if (ctr_qtm_distance_cm < 22.0f) focus -= (s16)((22.0f - ctr_qtm_distance_cm) * 3.0f);
                if (ctr_qtm_distance_cm > 48.0f) focus -= (s16)((ctr_qtm_distance_cm - 48.0f) * 2.0f);
                if (ctr_qtm_lux < 12.0f) focus -= (s16)((12.0f - ctr_qtm_lux) * 1.6f);
                if (ctr_qtm_lux > 180.0f) focus -= (s16)((ctr_qtm_lux - 180.0f) * 0.14f);
                if (ctr_qtm_tracking.clamped) focus -= 12;
            } else {
                strncpy(ctr_qtm_status, sample.faceDetected ? "QTM FACE ONLY" : "QTM NO EYES", sizeof(ctr_qtm_status) - 1);
                focus = (ctr_3d_slider > 0.7f) ? 40 : 62;
            }
        } else {
            snprintf(ctr_qtm_status, sizeof(ctr_qtm_status), "QTM PAUSED %08lx", ctr_qtm_result);
            focus = (ctr_3d_slider > 0.7f) ? 45 : 65;
        }
    }
    ctr_visual_disturbance = ctr_clampf((100.0f - (float)focus) / 75.0f, 0.0f, 1.0f);
    ctr_update_strain_model(focus);
    focus -= (s16)(ctr_audio_disturbance * 24.0f);
    focus -= (s16)(ctr_sinus_pressure * 18.0f);
    focus -= (s16)(ctr_eye_strain * 14.0f);
    if (ctr_audio_disturbance > 0.55f) focus -= 4;
    if (focus < 20) focus = 20;
    if (focus > 100) focus = 100;
    ctr_focus_score = focus;
}

static s8 ctr_compute_eye_shift(void) {
    s8 base;
    float comfort_headroom;
    ctr_3d_slider = osGet3DSliderState();
    if (ctr_stereo_force_flat) {
        ctr_eye_shift_px = 0;
        return 0;
    }
    if (ctr_3d_slider < 0.20f) {
        ctr_eye_shift_px = 0;
        return 0;
    }
    if (ctr_3d_slider > 0.85f) base = 3;
    else if (ctr_3d_slider > 0.60f) base = 2;
    else base = 1;
    if (!ctr_stereo_comfort) {
        ctr_eye_shift_px = base;
        return base;
    }
    if (ctr_focus_score < 40) base = 0;
    else if (ctr_focus_score < 65 && base > 0) base--;
    else if (ctr_focus_score < 82 && base > 1) base--;
    comfort_headroom = 1.0f - ctr_clampf(ctr_eye_strain * 0.75f + ctr_sinus_pressure * 0.60f, 0.0f, 1.0f);
    if (ctr_3d_slider > 0.82f && ctr_focus_score > 88 && comfort_headroom > 0.72f) base++;
    else if (comfort_headroom < 0.35f && base > 0) base--;
    if (ctr_eye_strain > 0.55f && base > 0) base--;
    if (base > 4) base = 4;
    ctr_eye_shift_px = base;
    return base;
}

static void ctr_apply_preset(u8 preset_index) {
    const CtrStereoPreset *preset;
    if (preset_index >= CTR_STEREO_PRESET_COUNT) return;
    preset = &ctr_stereo_presets[preset_index];
    ctr_stereo_comfort = preset->comfort;
    ctr_stereo_force_flat = preset->force_flat;
    ctr_smoothing_mode = preset->smoothing_mode;
    ctr_preset_index = preset_index;
}

static void ctr_sync_preset_index(void) {
    u8 i;
    for (i = 0; i < CTR_STEREO_PRESET_COUNT; ++i) {
        const CtrStereoPreset *preset = &ctr_stereo_presets[i];
        if (preset->comfort == ctr_stereo_comfort && preset->force_flat == ctr_stereo_force_flat && preset->smoothing_mode == ctr_smoothing_mode) {
            ctr_preset_index = i;
            return;
        }
    }
    ctr_preset_index = CTR_STEREO_PRESET_CUSTOM;
}

static void ctr_update_parallax(void) {
    float base = (float)ctr_compute_eye_shift();
    float yaw_bias = 0.0f;
    float alpha;
    float left_target;
    float right_target;
    float disturbance_mix = ctr_clampf(ctr_audio_disturbance * 0.4f + ctr_visual_disturbance * 0.25f + ctr_sinus_pressure * 0.20f + ctr_eye_strain * 0.15f, 0.0f, 1.0f);
    if (ctr_qtm_tracking_live) {
        yaw_bias = ctr_qtm_tracking.dYaw * (5.5f - disturbance_mix * 2.0f);
        if (yaw_bias > 1.25f) yaw_bias = 1.25f;
        if (yaw_bias < -1.25f) yaw_bias = -1.25f;
    }
    switch (ctr_smoothing_mode) {
        case 0: alpha = 1.0f; break;
        case 1: alpha = 0.38f; break;
        default: alpha = 0.18f; break;
    }
    if (disturbance_mix > 0.45f) alpha *= (1.0f - disturbance_mix * 0.35f);
    left_target = base + yaw_bias;
    right_target = base - yaw_bias;
    left_target *= (1.0f - disturbance_mix * 0.35f);
    right_target *= (1.0f - disturbance_mix * 0.35f);
    if (left_target < 0.0f) left_target = 0.0f;
    if (right_target < 0.0f) right_target = 0.0f;
    ctr_eye_shift_left_f += (left_target - ctr_eye_shift_left_f) * alpha;
    ctr_eye_shift_right_f += (right_target - ctr_eye_shift_right_f) * alpha;
    if (base == 0.0f && alpha < 1.0f) {
        ctr_eye_shift_left_f *= 0.7f;
        ctr_eye_shift_right_f *= 0.7f;
    }
    ctr_eye_shift_left_px = (s8)(ctr_eye_shift_left_f + 0.5f);
    ctr_eye_shift_right_px = (s8)(ctr_eye_shift_right_f + 0.5f);
}

static void ctr_options_handle_input(u32 keys_down) {
    if (keys_down & KEY_B) {
        ctr_options_open = 0;
        return;
    }
    if (keys_down & KEY_UP) {
        ctr_options_cursor = (ctr_options_cursor == 0) ? 3 : (u8)(ctr_options_cursor - 1);
    }
    if (keys_down & KEY_DOWN) {
        ctr_options_cursor = (u8)((ctr_options_cursor + 1) % 4);
    }
    if (keys_down & (KEY_LEFT | KEY_RIGHT | KEY_A)) {
        switch (ctr_options_cursor) {
            case 0:
                if (keys_down & KEY_LEFT) {
                    if (ctr_preset_index == CTR_STEREO_PRESET_CUSTOM || ctr_preset_index == 0) ctr_apply_preset(CTR_STEREO_PRESET_COUNT - 1);
                    else ctr_apply_preset((u8)(ctr_preset_index - 1));
                } else {
                    if (ctr_preset_index == CTR_STEREO_PRESET_CUSTOM || ctr_preset_index >= (CTR_STEREO_PRESET_COUNT - 1)) ctr_apply_preset(0);
                    else ctr_apply_preset((u8)(ctr_preset_index + 1));
                }
                break;
            case 1:
                ctr_stereo_comfort ^= 1;
                ctr_sync_preset_index();
                break;
            case 2:
                ctr_stereo_force_flat ^= 1;
                ctr_sync_preset_index();
                break;
            default:
                if (keys_down & KEY_LEFT) {
                    ctr_smoothing_mode = (ctr_smoothing_mode == 0) ? 2 : (u8)(ctr_smoothing_mode - 1);
                } else {
                    ctr_smoothing_mode = (u8)((ctr_smoothing_mode + 1) % 3);
                }
                ctr_sync_preset_index();
                break;
        }
    }
}

static const char *ctr_smoothing_label(void) {
    switch (ctr_smoothing_mode) {
        case 0: return "off";
        case 1: return "balanced";
        default: return "soft";
    }
}

static const char *ctr_preset_label(void) {
    if (ctr_preset_index == CTR_STEREO_PRESET_CUSTOM) return "custom";
    return ctr_stereo_presets[ctr_preset_index].name;
}

static void ctr_draw_status_panel(void) {
    if ((ctr_qtm_frame++ & 0x03) != 0) return;
    printf("\x1b[2J\x1b[H");
    printf("Kaiju Gaiden 3DS\n");
    printf("L menu:    %s\n", ctr_options_open ? "open" : "closed");
    printf("Profile:   %s\n", ctr_profile_loaded ? ctr_profile_source : "defaults");
    printf("Stereo:    %s\n", ctr_stereo_force_flat ? "forced mono" : "adaptive");
    printf("Preset:    %s\n", ctr_preset_label());
    printf("3D slider: %3d%%\n", (int)(ctr_3d_slider * 100.0f));
    printf("Shift L/R: %d / %d px\n", (int)ctr_eye_shift_left_px, (int)ctr_eye_shift_right_px);
    printf("Focus:     %d/100\n", (int)ctr_focus_score);
    printf("QTM:       %-15s\n", ctr_qtm_status);
    printf("Mic:       %-15s\n", ctr_mic_status);
    printf("Visual:    %2d%%\n", (int)(ctr_visual_disturbance * 100.0f));
    printf("Audio:     %2d%% ref %2d%%\n", (int)(ctr_audio_disturbance * 100.0f), (int)(ctr_audio_reference * 100.0f));
    printf("Sinus:     %2d%%\n", (int)(ctr_sinus_pressure * 100.0f));
    printf("Eye strain:%2d%% load %2d%%\n", (int)(ctr_eye_strain * 100.0f), (int)(ctr_focus_load * 100.0f));
    if (ctr_qtm_available) {
        printf("Track:     %s conf %.2f\n", ctr_qtm_tracking_live ? "live" : "soft", ctr_qtm_confidence);
        printf("Distance:  %2d cm\n", (int)(ctr_qtm_distance_cm + 0.5f));
        printf("Tilt:      %2d deg\n", (int)(ctr_qtm_tilt_deg >= 0.0f ? ctr_qtm_tilt_deg + 0.5f : ctr_qtm_tilt_deg - 0.5f));
        printf("Light:     %3d lux\n", (int)(ctr_qtm_lux + 0.5f));
    } else {
        printf("Track:     unavailable\n");
        printf("Distance:  --\n");
        printf("Tilt:      --\n");
        printf("Light:     --\n");
    }
    printf("Bands:     A %.2f  A# %.2f\n", ctr_audio_band_a, ctr_audio_band_as);
    printf("           F %.2f  B %.2f  G %.2f\n", ctr_audio_band_f, ctr_audio_band_b, ctr_audio_band_g);
    printf("Smooth:    %s\n", ctr_smoothing_label());
    if (ctr_options_open) {
        printf("\n3DS OPTIONS\n");
        printf("%c Preset    %s\n", (ctr_options_cursor == 0) ? '>' : ' ', ctr_preset_label());
        printf("%c Comfort   %s\n", (ctr_options_cursor == 1) ? '>' : ' ', ctr_stereo_comfort ? "on" : "off");
        printf("%c Stereo    %s\n", (ctr_options_cursor == 2) ? '>' : ' ', ctr_stereo_force_flat ? "mono" : "adaptive");
        printf("%c Smooth    %s\n", (ctr_options_cursor == 3) ? '>' : ' ', ctr_smoothing_label());
        printf("D-pad move  A/Left/Right change\n");
        printf("B or L closes menu\n");
    } else {
        printf("\nPress L for 3DS options\n");
    }
    printf("Comfort is heuristic only.\n");
}
#endif

static void host_init(void) {
#ifdef TARGET_3DS
    gfxInitDefault();
    consoleInit(GFX_BOTTOM, NULL);
    gfxSetScreenFormat(GFX_TOP, GSP_BGR8_OES);
    gfxSet3D(false);
    printf("\x1b[2J");
    ctr_profile_load();
    ctr_mic_init();
    ctr_qtm_init();
    ctr_profile_write_status();
    ctr_draw_status_panel();
#endif
#ifdef HAS_SDL2
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    host_autoplay_init();
    SDL_SetMainReady();
    SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO);
    sdl_window   = SDL_CreateWindow("Kaiju Gaiden!? GB.",
                                    SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                    SCREEN_W * SCALE, SCREEN_H * SCALE,
                                    SDL_WINDOW_SHOWN);
    sdl_renderer = SDL_CreateRenderer(sdl_window, -1, SDL_RENDERER_PRESENTVSYNC);
    SDL_RenderSetLogicalSize(sdl_renderer, SCREEN_W, SCREEN_H);
    sdl_texture  = SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                                     SDL_TEXTUREACCESS_STREAMING,
                                     SCREEN_W, SCREEN_H);
    host_audio_open_devices();
#endif
    memset(fb,       0, sizeof(fb));
    memset(bkg_map,  0, sizeof(bkg_map));
    memset(bkg_tiles,0, sizeof(bkg_tiles));
    memset(spr_tiles,0, sizeof(spr_tiles));
    memset(obj_table,0, sizeof(obj_table));
    plat_audio_reset();
}

int g_quit = 0;

#endif /* TARGET_HOST || TARGET_3DS */


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: GAME CONSTANTS
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Screen layout — see global geometry defines above */

/* Tile IDs in background charblock */
#define TILE_BLANK       0
#define TILE_GROUND_L    1   /* ground tile left variant */
#define TILE_GROUND_R    2   /* ground tile right variant */
#define TILE_WATER_A     3   /* water animation frame A */
#define TILE_WATER_B     4   /* water animation frame B */
#define TILE_CLIFF_A     5   /* beach cliff */
#define TILE_CLIFF_B     6
#define TILE_SKY_A       7   /* sky fill */
#define TILE_SKY_B       8
#define TILE_SPLASH1     9   /* drIpTECH splash logo tiles: 9–16 (2×4 arrangement) */
#define TILE_SPLASH_END 16
#define TILE_TITLE_A    17   /* title logo tiles: 17–28 */
#define TILE_TITLE_END  28
#define TILE_HP_SEG     29   /* player HP filled segment */
#define TILE_BOSS_SEG   30   /* boss HP filled segment   */
#define TILE_FONT_0     32   /* ASCII digits 0–9 at tile 32+n */
#define TILE_FONT_A     42   /* ASCII A–Z at tile 42+n */

/* Sprite tile IDs in OBJ charblock */
#define SPR_REI_IDLE     0   /* Rei stand, 2×3 sprite (6 tiles) */
#define SPR_REI_RUN      6   /* Rei run frame (6 tiles) */
#define SPR_REI_ATTACK  12   /* Rei attack frame (6 tiles) */
#define SPR_BOSS_A      18   /* Harbor Leviathan body tile set (8 tiles) */
#define SPR_BOSS_B      26   /* Boss phase 2 set */
#define SPR_BOSS_C      34   /* Boss phase 3 set */
#define SPR_MINION      42   /* Basic minion (4 tiles) */
#define SPR_FX_HIT      46   /* Hit spark (2 tiles) */
#define SPR_FX_NANO     48   /* NanoCell orb (2 tiles) */
#define SPR_CINEMATIC_A 50   /* Intro cinematic kaiju A body (12 tiles) */
#define SPR_CINEMATIC_B 62   /* Intro cinematic kaiju B body (12 tiles) */

/* Game phase constants */
#define PHASE_SPLASH       0
#define PHASE_CINEMATIC    1
#define PHASE_TITLE        2
#define PHASE_STAGE_INTRO  3
#define PHASE_COMBAT       4
#define PHASE_BOSS_DEATH   5
#define PHASE_CYPHER_DROP  6
#define PHASE_GAME_OVER    7
#define PHASE_PASSWORD     8
#define PHASE_NARRATIVE    9

#define AUDIO_SCENE_SPLASH      0
#define AUDIO_SCENE_CINEMATIC   1
#define AUDIO_SCENE_TITLE       2
#define AUDIO_SCENE_NARRATIVE   3
#define AUDIO_SCENE_DUEL        4
#define AUDIO_SCENE_COMBAT      5
#define AUDIO_SCENE_CYPHER      6
#define AUDIO_SCENE_GAMEOVER    7

#define AUDIO_VOICE_NONE        0
#define AUDIO_VOICE_BOSS        1
#define AUDIO_VOICE_REI         2
#define AUDIO_VOICE_CHORUS      3
#define AUDIO_VOICE_SYSTEM      4

#define AUDIO_EVENT_BANNER      0
#define AUDIO_EVENT_CHOICE      1
#define AUDIO_EVENT_DUEL        2
#define AUDIO_EVENT_VICTORY     3
#define AUDIO_EVENT_DEFEAT      4
#define AUDIO_EVENT_PHASE       5

/* Combat constants */
#define PLAYER_MAX_HP       6   /* Hit points (shown as segments on HUD) */
#define BOSS_HP_P1         12   /* Boss phase 1 HP */
#define BOSS_HP_P2         10   /* Boss phase 2 HP */
#define BOSS_HP_P3          8   /* Boss phase 3 HP */
#define MINION_HP           2
#define ATTACK_COMBO_WINDOW 20  /* frames — window for chaining combo hits */
#define ATTACK_TOTAL_FRAMES 14
#define ATTACK_ACTIVE_FRAME 8
#define INPUT_BUFFER_FRAMES 5
#define PLAYER_ATTACK_FRONT 28
#define PLAYER_ATTACK_REAR   8
#define PLAYER_FINISHER_COMBO 3
#define CAMERA_TRAVEL_LEAD   3
#define CAMERA_COMBAT_LEAD   3
#define CAMERA_TELEGRAPH_LEAD 4
#define CAMERA_MAX_X         7
#define CAMERA_MAX_Y         3
#define WATER_REDRAW_PERIOD 16
#define NANOCELL_MAX        9
#define NANOCELL_BOOST_DUR  90  /* frames — ~5 s at 18fps/60fps depending on target */
#define DODGE_FRAMES        10
#define DODGE_STEP           2
#define SKIP_HOLD_FRAMES    90  /* frames to hold B to skip cinematic */
#define SPLASH_HOLD_FRAMES 120  /* frames to auto-advance splash */
#define GAMEOVER_HOLD_FRAMES 180
#define PASSWORD_LEN        16

/* Beat-window attack bonus */
#define BEAT_BPM           110
#define BEAT_PERIOD        (3600 / BEAT_BPM)  /* frames × 100 / BPM, integer approx */

/* Boss attack types */
#define BOSS_ATK_SWEEP    0
#define BOSS_ATK_SPIT     1
#define BOSS_ATK_SLAM     2
#define BOSS_ATK_TIDAL    3     /* Phase 3 tidal pull */

#define BOSS_WAVES_TO_CLEAR 3
#define BOSS_SWEEP_RANGE   32
#define BOSS_SPIT_RANGE    88
#define BOSS_SLAM_RANGE    26
#define BOSS_ATK_INTERVAL_P1 90
#define BOSS_ATK_INTERVAL_P2 70
#define BOSS_ATK_INTERVAL_P3 55

/* Max minions on screen */
#define MINION_MAX         5
#define MINION_ATTACK_RANGE 18
#define MINION_WINDUP_FRAMES 14
#define MINION_RECOVER_FRAMES 20

/* Combat banner states */
#define BANNER_NONE        0
#define BANNER_WAVE_CLEAR  1
#define BANNER_BOSS_RISE   2
#define BANNER_DODGE       3
#define BANNER_PERFECT     4
#define BANNER_FINISHER    5
#define BANNER_BOSS_STUN   6
#define BANNER_SURGE       7
#define BANNER_FIRST       8
#define BANNER_HAZARD      9

#define CAMPAIGN_STAGE_COUNT 12
#define ENV_OBJECT_MAX      6
#define STAGE_SPAWN_SLOT_MAX 8
#define ENV_PREFAB_COUNT    4
#define ENV_THEME_SUBCLASS_COUNT 5
#define MINION_PREFAB_COUNT 4
#define BOSS_ARCHETYPE_COUNT 9
#define BOSS_SUBARCHETYPE_COUNT 4
#define RUN_AI_DIRECTIVE_COUNT 5
#define MINION_CLASS_MAJOR_COUNT 24
#define MINION_CLASS_MID_COUNT   13
#define MINION_CLASS_MINOR_COUNT 8
#define REI_FORM_COUNT 12
#define REI_MUTATION_COUNT 16
#define DUEL_FIRST_STRIKE_FRAMES 32
#define DUEL_QTE_WINDOW_FRAMES 14

/* HUD layout (in tiles) */
#define HUD_ROW      0         /* top row of screen */
#define HUD_HP_COL   0
#define HUD_NANO_COL 10
#define HUD_BOSS_COL 14        /* boss HP bar start column (pixel coords) */

static const char *stage_name_table[CAMPAIGN_STAGE_COUNT] = {
    "HARBOR SHORE",
    "ASH BARROWS",
    "MANGROVE TEETH",
    "FROST BREAKER",
    "SUNKEN VAULT",
    "GLASS DELTA",
    "THUNDER REEF",
    "BASALT GATE",
    "BLOOM PIT",
    "DUST HALO",
    "BLACK TIDE",
    "CROWN CRATER"
};

static const char *boss_name_table[CAMPAIGN_STAGE_COUNT] = {
    "HARBOR LEVIATHAN",
    "CINDER WYRM",
    "ROOT BASTION",
    "GLACIER MAW",
    "VAULT SERPENT",
    "SHARD COLOSSUS",
    "STORM HOWLER",
    "BASALT TYRANT",
    "BLOOM TITAN",
    "DUST ORACLE",
    "NIGHT ABYSS",
    "CROWN BEHEMOTH"
};

static const char *boss_intro_table[CAMPAIGN_STAGE_COUNT] = {
    "REEF CLAIMS YOU",
    "ASH TAKES FORM",
    "ROOTS BREAK BONE",
    "ICE CUTS DEEP",
    "VAULT OPENS WIDE",
    "SHARDS SEEK BLOOD",
    "STORM EATS STEEL",
    "GATE DEMANDS TOLL",
    "BLOOM WANTS LUNG",
    "DUST SEES ALL",
    "TIDE DRINKS LIGHT",
    "CROWN RULES RUIN"
};

static const char *boss_horror_genre_table[CAMPAIGN_STAGE_COUNT] = {
    "ABYSSAL GOTHIC",
    "FOLK PYRE CURSE",
    "SWAMP BODY DREAD",
    "ARCTIC CANNIBAL",
    "CRYPT GOTHIC",
    "GLASS SLASHER",
    "STORM LYCANTHROPE",
    "HELLGATE DEMON",
    "SPORE ECO HORROR",
    "OCCULT OMEN",
    "COSMIC ABYSS",
    "REGAL NECROMANCY"
};

static const u8 stage_moral_kind_table[CAMPAIGN_STAGE_COUNT] = {
    0, 1, 2, 0,
    2, 2, 0, 3,
    1, 2, 3, 1
};

static const char *boss_choice_prompt_a_table[CAMPAIGN_STAGE_COUNT] = {
    "NETTED SOULS CHURN",
    "WICKER CHILDREN",
    "THE GROVE GROWS",
    "THE LOST PACK",
    "THE CRYPT CHOIR",
    "MIRROR KILLER",
    "MOON-SALT PACK",
    "THE GATE TITHE",
    "THE BLOOM CHOIR",
    "THE DUST EYE",
    "THE BLACK SURF",
    "THE BONE COURT"
};

static const char *boss_choice_prompt_b_table[CAMPAIGN_STAGE_COUNT] = {
    "IN THE RIBBED MAW",
    "BEG FOR OLD FIRE",
    "FROM TAKEN FLESH",
    "STARVES IN WHITE",
    "KNOWS YOUR NAME",
    "WEARS THEIR FACES",
    "CIRCLES THE PIERS",
    "WANTS A HEART",
    "DRINKS THE SICK",
    "SEES HIDDEN SIN",
    "CALLS YOU INSIDE",
    "DEMANDS AN HEIR"
};

static const char *boss_choice_left_table[CAMPAIGN_STAGE_COUNT] = {
    "CUT THEM FREE",
    "BREAK THE PYRE",
    "BURN THE ROOT",
    "SHARE THE HEAT",
    "OPEN THE VAULT",
    "NAME THE DEAD",
    "CURE THE BITE",
    "BAR THE GATE",
    "CULL THE BLOOM",
    "SPEAK THE SIN",
    "HEAR THE CALL",
    "BREAK THE THRONE"
};

static const char *boss_choice_right_table[CAMPAIGN_STAGE_COUNT] = {
    "SEAL THEM IN",
    "FEED THE FLAME",
    "GRAFT THE STRONG",
    "KEEP THE HEAT",
    "CHAIN IT SHUT",
    "MASK THE DEAD",
    "HUNT THE PACK",
    "OFFER A HEART",
    "SEED THE WARD",
    "BLIND THE EYE",
    "NAIL THE SHORE",
    "TAKE THE CROWN"
};

static const char *boss_choice_left_result_table[CAMPAIGN_STAGE_COUNT] = {
    "THE DROWNED RISE",
    "ASH LOSES ITS NAME",
    "THE COPSE SCREAMS",
    "THE COLD RELENTS",
    "THE DEAD WALK OUT",
    "THE FACES RETURN",
    "THE CURSE CAN BREAK",
    "THE GATE STARVES",
    "THE SPORE LINE THINS",
    "THE VEIL STAYS TORN",
    "THE TIDE HEARS",
    "THE COURT FALLS"
};

static const char *boss_choice_right_result_table[CAMPAIGN_STAGE_COUNT] = {
    "THE HOLD STAYS FED",
    "ASH MARKS YOUR BLOOD",
    "THE COPSE LEARNS YOU",
    "THE WEAK FREEZE",
    "THE DEAD STAY LOW",
    "THE MASK HOLDS",
    "THE HUNT OWNS NIGHT",
    "THE GATE REMEMBERS",
    "THE GARDEN TAKES",
    "THE LIE STAYS WARM",
    "THE SHORE HOLDS",
    "THE CROWN FITS"
};

static const char *moral_path_table[9] = {
    "UNMARKED",
    "MERCY",
    "RUIN",
    "DUTY",
    "WILD",
    "TRUTH",
    "VEIL",
    "GIVE",
    "HUNGER"
};

typedef struct {
    const char *ecosystem;
    const char *hazard_line;
    const char *minion_line;
    const char *cypher_label;
    const char *cypher_effect;
    const char *terrain_line;
    const char *pressure_line;
    u8 theme;
    u8 wave_goal;
    u8 wave_size;
    u8 minion_hp;
    u8 minion_speed;
    u8 boss_style;
    u8 duel_mechanic;
    u8 ai_directive;
    u8 boss_prefab;
    u8 boss_subarchetype;
    u8 weather_bias;
    u8 density_bias;
    u8 route_bias;
    u8 phase_hp_bonus[3];
    s8 interval_bias;
} CampaignStageDesign;

static const CampaignStageDesign campaign_stage_design_table[CAMPAIGN_STAGE_COUNT] = {
    { "HARBOR / REEF", "SPIRES BLOCK LANES", "SWARM SPIT SUPPORT", "HARBOR CYPHER",   "PURIFY REEF NODES", "TIDE CUTS FOOTING", "REEF PACKS PINCH", 0, 3, 2, 2, 1, 1, 3, 1, 0, 0, 1, 2, 2, {0, 0, 1}, 0 },
    { "ASH PLATEAU", "ASH GUST LOW VIS", "BRUTE CINDER PACK", "ASH CYPHER",      "HEAL ASH SOIL",     "DRAFTS SMEAR ASH", "CINDER PUSH WAVES", 1, 3, 2, 3, 1, 0, 1, 0, 1, 1, 2, 2, 1, {1, 0, 1}, 1 },
    { "MANGROVE LATTICE", "ROOTS CUT SPACE", "HARASSER ROOT DEN", "MANGROVE CYPHER", "CLEAR ROOT BLIGHT",  "ROOT BRIDGES TWIST", "DEN PACKS FLANK", 2, 3, 3, 3, 2, 2, 0, 2, 2, 2, 2, 3, 3, {0, 1, 1}, 1 },
    { "FROST SHELF", "WHITEOUT PUSHBACK", "WOLFPACK RUSH", "FROST CYPHER",    "THAW SAFE PATHS",   "ICE SHEAR OPENS", "WOLVES TEST EDGE", 3, 3, 3, 3, 2, 3, 1, 3, 3, 0, 3, 2, 2, {1, 1, 1}, 2 },
    { "SUNKEN CRYPT", "CRYPT GATES SHIFT", "CRYPT CHOIR GUARD", "VAULT CYPHER",    "OPEN CRYPT WARDS",  "CRYPT AISLES BEND", "CHOIR HOLDS GATES", 1, 4, 3, 4, 2, 2, 0, 4, 4, 1, 1, 4, 3, {1, 1, 2}, 2 },
    { "GLASS FLOODPLAIN", "GLASS SHARDS FALL", "SHARD MIMIC PAIR", "GLASS CYPHER",    "CALM SHARD FLOW",   "SHARDS SKATE WIDE", "MIMICS SPLIT LINES", 2, 4, 3, 4, 2, 1, 2, 1, 5, 2, 2, 3, 2, {1, 2, 1}, 2 },
    { "STORM REEF", "LIGHTNING TIDES", "HOWLER SALT PACK", "STORM CYPHER",    "GROUND STORM TIDE", "SURF SURGES HARD", "HOWLERS FOLD SIDES", 0, 4, 4, 4, 3, 3, 3, 3, 6, 0, 4, 4, 3, {2, 1, 2}, 3 },
    { "BASALT HELLGATE", "BASALT RAISE WALL", "GATE TITHE BRUTES", "BASALT CYPHER",   "SEAL HELL GATES",  "VENTS CRACK FLOOR", "BRUTES WALL PATHS", 1, 4, 4, 5, 3, 0, 0, 4, 7, 3, 3, 5, 4, {2, 2, 2}, 3 },
    { "SPORE GARDEN", "SPORES CHOKE LINE", "SPORE SWARM LUNG", "BLOOM CYPHER",    "THIN SPORE VEIL",   "BLOOM FOG DRIFTS", "LUNG SWARMS STALL", 2, 4, 4, 5, 3, 2, 2, 2, 8, 1, 4, 5, 3, {2, 2, 3}, 4 },
    { "DUST ORRERY", "DUST VEIL PHASES", "OMEN EYE HARASS", "DUST CYPHER",     "LIFT DUST CURSE",   "RINGS DRIFT FALSE", "OMENS PEEL RANGE", 3, 5, 4, 5, 3, 1, 1, 1, 5, 2, 3, 3, 4, {2, 3, 2}, 4 },
    { "ABYSSAL SHORE", "BLACK SURF PULLS", "ABYSS DRONE TIDE", "ABYSS CYPHER",    "SOFTEN BLACK SURF", "BLACK TIDE DRAGS", "DRONES HEM WAKE", 0, 5, 5, 5, 3, 3, 3, 3, 6, 3, 4, 4, 4, {3, 3, 3}, 5 },
    { "CROWN NECROPOLIS", "CROWN SPIKES RISE", "BONE COURT ELITE", "CROWN CYPHER",    "BREAK BONE COURT", "SPIRES PRUNE SKY", "COURT LOCKS CHOKE", 1, 5, 5, 6, 3, 0, 0, 4, 8, 3, 2, 5, 5, {3, 4, 4}, 6 }
};

static const char *duel_mechanic_label(u8 mechanic);
static void spr_hide_all(void);
static u8 narrative_dominant_moral_index(void);

static const char *rei_intro_table[BOSS_ARCHETYPE_COUNT] = {
    "REI CUTS THROUGH",
    "REI HOLDS LINE",
    "REI BREAKS GUARD",
    "REI STEPS INSIDE",
    "REI BENDS FORM",
    "REI TAKES HEIGHT",
    "REI SWIMS CUTS",
    "REI SETS RHYTHM",
    "REI BURNS OPEN"
};

static const u8 boss_tile_layout_db[BOSS_ARCHETYPE_COUNT][8] = {
    { 0, 1, 2, 3, 4, 5, 6, 7 },
    { 1, 0, 2, 1, 5, 4, 7, 6 },
    { 2, 3, 1, 0, 6, 7, 5, 4 },
    { 3, 2, 0, 1, 7, 6, 4, 5 },
    { 0, 2, 3, 1, 4, 6, 7, 5 },
    { 1, 3, 0, 2, 5, 7, 4, 6 },
    { 2, 0, 3, 1, 6, 4, 7, 5 },
    { 3, 1, 2, 0, 7, 5, 6, 4 },
    { 1, 2, 0, 3, 5, 6, 4, 7 }
};

static const u8 boss_tile_flip_db[BOSS_ARCHETYPE_COUNT][8] = {
    { 0x00, 0x00, 0x20, 0x20, 0x00, 0x00, 0x20, 0x20 },
    { 0x00, 0x20, 0x00, 0x20, 0x00, 0x20, 0x00, 0x20 },
    { 0x20, 0x00, 0x20, 0x00, 0x20, 0x00, 0x20, 0x00 },
    { 0x20, 0x20, 0x00, 0x00, 0x20, 0x20, 0x00, 0x00 },
    { 0x00, 0x20, 0x20, 0x00, 0x00, 0x20, 0x20, 0x00 },
    { 0x20, 0x00, 0x00, 0x20, 0x20, 0x00, 0x00, 0x20 },
    { 0x00, 0x00, 0x20, 0x00, 0x20, 0x20, 0x00, 0x20 },
    { 0x20, 0x00, 0x20, 0x20, 0x00, 0x20, 0x00, 0x00 },
    { 0x00, 0x20, 0x00, 0x00, 0x20, 0x00, 0x20, 0x20 }
};

static const u8 boss_subtile_variant_db[BOSS_SUBARCHETYPE_COUNT][8] = {
    { 0, 0, 1, 1, 0, 0, 1, 1 },
    { 1, 2, 0, 1, 2, 1, 0, 2 },
    { 2, 1, 2, 0, 1, 2, 1, 0 },
    { 3, 2, 1, 3, 0, 1, 2, 3 }
};

static const s8 boss_tile_x_offset_db[BOSS_ARCHETYPE_COUNT][8] = {
    { -1, 0, 0, 1, -2, -1, 1, 2 },
    { 0, 1, 1, 0, -1, 0, 0, 1 },
    { -2, -1, 1, 2, -1, 0, 0, 1 },
    { -1, 0, 0, 1, -3, -1, 1, 3 },
    { -2, -1, 1, 2, -2, 0, 0, 2 },
    { -1, 1, 0, 2, -3, -2, 1, 2 },
    { -2, 0, 1, 2, -1, -1, 2, 3 },
    { -1, 0, 1, 1, -2, 0, 1, 2 },
    { -3, -1, 0, 2, -2, -1, 2, 3 }
};

static const s8 boss_tile_y_offset_db[BOSS_ARCHETYPE_COUNT][8] = {
    { -2, -1, -1, -2, 0, 1, 1, 0 },
    { -1, -2, -2, -1, 1, 0, 0, 1 },
    { -3, -2, -2, -3, 1, 1, 0, 0 },
    { -2, -1, -1, -2, 2, 1, 1, 2 },
    { -3, -2, -1, -2, 0, 1, 2, 1 },
    { -1, -3, -2, -1, 1, 2, 0, 1 },
    { -2, -2, -1, -3, 1, 1, 2, 0 },
    { -1, -2, -1, -2, 1, 0, 1, 2 },
    { -3, -1, -2, -2, 2, 1, 0, 1 }
};

static const u8 rei_form_thresholds[REI_FORM_COUNT] = { 0, 6, 12, 20, 28, 38, 50, 64, 80, 98, 118, 140 };

typedef struct {
    u8 ferocity;
    u8 shell;
    u8 mobility;
} GenomeProfile;

typedef struct {
    u8 back_tile;
    u8 mid_tile;
    u8 fore_tile;
    u8 accent_tile;
    u8 w;
    u8 h;
    u8 solid;
} EnvPrefab;

typedef struct {
    u8 hp_bonus;
    u8 speed_bonus;
    u8 windup_bias;
    u8 status_bias;
} MinionPrefab;

typedef struct {
    u8 style;
    u8 opener_lock;
    u8 summon_bias;
    u8 pressure_bias;
} BossPrefab;

typedef struct {
    u8 sky_stride;
    u8 water_rows;
    u8 split_bias;
    u8 ridge_bias;
    u8 density;
    u8 sightline_bias;
    u8 current_bias;
    u8 lane_bias;
    u8 prefab_bias[3];
} EnvThemeSubclass;

static const EnvPrefab env_prefab_db[ENV_PREFAB_COUNT] = {
    { TILE_CLIFF_A,  TILE_GROUND_L, TILE_CLIFF_B, TILE_GROUND_R, 3, 2, 1 },
    { TILE_GROUND_R, TILE_CLIFF_B,  TILE_GROUND_L, TILE_WATER_A, 2, 3, 0 },
    { TILE_CLIFF_B,  TILE_WATER_B,  TILE_CLIFF_A, TILE_GROUND_L, 4, 2, 1 },
    { TILE_GROUND_L, TILE_GROUND_R, TILE_CLIFF_A, TILE_WATER_B, 3, 3, 1 }
};

static const MinionPrefab minion_prefab_db[MINION_PREFAB_COUNT] = {
    { 0, 0, 0, 1 },
    { 1, 0, 2, 2 },
    { 0, 1, 1, 3 },
    { 1, 1, 3, 4 }
};

static const BossPrefab boss_prefab_db[BOSS_ARCHETYPE_COUNT] = {
    { 0, 24, 0, 0 },
    { 1, 28, 1, 1 },
    { 2, 32, 2, 1 },
    { 3, 36, 3, 2 },
    { 0, 20, 1, 3 },
    { 1, 18, 2, 2 },
    { 2, 26, 0, 4 },
    { 3, 30, 3, 1 },
    { 0, 22, 2, 3 }
};

static const EnvThemeSubclass env_theme_subclass_db[4][ENV_THEME_SUBCLASS_COUNT] = {
    {
        { 1, 2, 1, 0, 2, 4, 2, 1, { 0, 1, 2 } },
        { 2, 3, 3, 1, 3, 2, 3, 2, { 1, 2, 0 } },
        { 3, 2, 5, 2, 4, 1, 4, 3, { 2, 0, 3 } },
        { 1, 4, 7, 1, 5, 2, 4, 1, { 3, 1, 0 } },
        { 4, 3, 2, 3, 3, 3, 2, 4, { 1, 3, 2 } }
    },
    {
        { 2, 2, 2, 0, 3, 3, 2, 2, { 1, 0, 2 } },
        { 3, 3, 6, 1, 4, 2, 3, 3, { 2, 1, 3 } },
        { 1, 2, 4, 2, 2, 1, 2, 1, { 0, 2, 1 } },
        { 4, 4, 1, 3, 5, 3, 4, 2, { 3, 0, 2 } },
        { 2, 3, 7, 2, 4, 2, 4, 4, { 2, 3, 1 } }
    },
    {
        { 1, 2, 0, 1, 3, 3, 1, 2, { 2, 0, 1 } },
        { 4, 3, 5, 0, 4, 2, 2, 3, { 3, 1, 2 } },
        { 2, 4, 2, 2, 5, 1, 3, 1, { 1, 2, 0 } },
        { 3, 2, 7, 3, 4, 2, 4, 4, { 0, 3, 2 } },
        { 1, 3, 4, 1, 5, 2, 3, 2, { 2, 1, 3 } }
    },
    {
        { 3, 2, 3, 0, 2, 4, 2, 2, { 3, 0, 1 } },
        { 1, 3, 6, 2, 3, 2, 3, 4, { 1, 2, 3 } },
        { 4, 4, 1, 1, 5, 3, 1, 1, { 0, 3, 2 } },
        { 2, 2, 5, 3, 4, 1, 4, 3, { 2, 1, 0 } },
        { 3, 3, 7, 2, 5, 2, 4, 2, { 1, 3, 0 } }
    }
};


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: ASSET DATA  (2bpp Game Boy tile format, 16 bytes per 8×8 tile)
 *
 * Each 8×8 tile is stored as 16 bytes:
 *   bytes 0,1  → row 0  (low bit-plane, high bit-plane)
 *   bytes 2,3  → row 1
 *   ...        → rows 2–7
 *
 * Shade encoding: 0=lightest (white), 1=light grey, 2=dark grey, 3=darkest (black)
 * Bit 7 of each byte = leftmost pixel of the row.
 *
 * ── Placeholder tiles — hand-authored geometric stubs ──────────────────────
 * These are replaced tile-for-tile after the Recraft generation pass places
 * properly-drawn PNG assets in assets/gb/  and convert_tiles.py re-encodes them.
 *
 * File references (post-generation):
 *   assets/gb/bg_tiles.h       → background tiles (TILE_BLANK–TILE_FONT_A+26)
 *   assets/gb/spr_rei.h        → SPR_REI_IDLE, SPR_REI_RUN, SPR_REI_ATTACK
 *   assets/gb/spr_boss.h       → SPR_BOSS_A, SPR_BOSS_B, SPR_BOSS_C
 *   assets/gb/spr_minion.h     → SPR_MINION
 *   assets/gb/spr_fx.h         → SPR_FX_HIT, SPR_FX_NANO
 *   assets/gb/spr_cinematic.h  → SPR_CINEMATIC_A, SPR_CINEMATIC_B
 *
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Total background tile count shipped (TILE_BLANK .. TILE_FONT_A+25) */
#define BKG_TILE_COUNT  68

/* Blank tile (all shade 0) */
static const u8 tile_blank[16] = {
    0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00,
    0x00,0x00, 0x00,0x00, 0x00,0x00, 0x00,0x00
};

/* ── Recraft-generated pixel art tiles (24 PNGs → 2bpp via gb_convert.py) ── */
#include "assets/gb/bg_tiles_generated.h"   /* ground_lr, water_ab, cliff_ab, sky_ab, splash, title */
#include "assets/gb/hud_tiles_generated.h"  /* tile_hp_seg, tile_boss_hp_bar */

/* Font digits 0–9 (tiles 32–41), each 8×8 2bpp — minimal 3px-wide bitmap font */
static const u8 tile_digit[10][16] = {
    {0x3C,0x00,0x66,0x00,0x6E,0x00,0x76,0x00,0x66,0x00,0x66,0x00,0x3C,0x00,0x00,0x00}, /* 0 */
    {0x18,0x00,0x38,0x00,0x18,0x00,0x18,0x00,0x18,0x00,0x18,0x00,0x7E,0x00,0x00,0x00}, /* 1 */
    {0x3C,0x00,0x66,0x00,0x06,0x00,0x0C,0x00,0x18,0x00,0x30,0x00,0x7E,0x00,0x00,0x00}, /* 2 */
    {0x3C,0x00,0x66,0x00,0x06,0x00,0x1C,0x00,0x06,0x00,0x66,0x00,0x3C,0x00,0x00,0x00}, /* 3 */
    {0x0C,0x00,0x1C,0x00,0x3C,0x00,0x6C,0x00,0x7E,0x00,0x0C,0x00,0x0C,0x00,0x00,0x00}, /* 4 */
    {0x7E,0x00,0x60,0x00,0x7C,0x00,0x06,0x00,0x06,0x00,0x66,0x00,0x3C,0x00,0x00,0x00}, /* 5 */
    {0x3C,0x00,0x66,0x00,0x60,0x00,0x7C,0x00,0x66,0x00,0x66,0x00,0x3C,0x00,0x00,0x00}, /* 6 */
    {0x7E,0x00,0x06,0x00,0x0C,0x00,0x18,0x00,0x18,0x00,0x18,0x00,0x18,0x00,0x00,0x00}, /* 7 */
    {0x3C,0x00,0x66,0x00,0x66,0x00,0x3C,0x00,0x66,0x00,0x66,0x00,0x3C,0x00,0x00,0x00}, /* 8 */
    {0x3C,0x00,0x66,0x00,0x66,0x00,0x3E,0x00,0x06,0x00,0x66,0x00,0x3C,0x00,0x00,0x00}, /* 9 */
};

#include "assets/gb/spr_rei_generated.h"    /* spr_rei_idle_data, spr_rei_run_data, spr_rei_attack_data */

#include "assets/gb/spr_boss_generated.h"   /* spr_boss_p1_data, spr_boss_p2_data, spr_boss_p3_data */
#include "assets/gb/spr_minion_generated.h" /* spr_minion_data */
#include "assets/gb/spr_fx_generated.h"     /* spr_fx_hit_data, spr_fx_nano_data */
#include "assets/gb/spr_cinematic_generated.h" /* spr_cinematic_a, spr_cinematic_b */


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: GAME STATE
 * ═══════════════════════════════════════════════════════════════════════════ */

typedef struct {
    /* Player */
    u8   player_hp;
    u8   player_x;          /* tile column (0–18) */
    u8   player_y;          /* pixel row  (0–127) */
    u8   player_facing;     /* 0=right, 1=left */
    u8   player_anim;       /* animation frame counter */
    u8   attack_timer;      /* frames remaining in attack state */
    u8   attack_queued;     /* pending attack waits for active frame */
    u8   attack_buffer;     /* short input buffer for attack responsiveness */
    u8   dodge_buffer;      /* short input buffer for dodge responsiveness */
    u8   hit_stun;          /* invincibility frames after taking a hit */
    u8   dodge_timer;       /* active dodge / invulnerability window */
    u8   combo_count;       /* current combo hits */
    u8   combo_timer;       /* frames left in combo window */
    u8   attack_dmg;        /* 1 normally, 2 with NanoCell boost */
    /* Nanocells */
    u8   nanocell_count;
    u8   nanocell_boost_timer;
    /* Beat-attack timing */
    u16  beat_timer;        /* counts up per frame */
    u8   beat_perfect;      /* set for 1 frame on perfect-beat attack */
    u8   perfect_flash_timer;
    /* Boss */
    u8   boss_awake;        /* 0 while player clears wave gate */
    u8   boss_phase;        /* 1/2/3 */
    u8   boss_hp;           /* current HP within phase */
    u8   boss_status;
    u8   boss_prefab;
    u8   boss_subarchetype;
    u8   boss_intro_lock;
    u8   duel_first_strike_timer;
    u8   duel_qte_button;
    u8   duel_qte_result;
    u8   duel_qte_ready;
    s16  boss_x;            /* pixel X */
    u8   boss_anim;
    u8   boss_atk_timer;    /* frames until next boss attack */
    u8   boss_atk_type;
    u8   boss_windup;       /* telegraph frames before attack resolves */
    u8   boss_recover;      /* cooldown frames after an attack */
    u8   boss_stun;         /* stun frames */
    GenomeProfile boss_genome;
    /* Minions */
    struct {
        u8 active;
        s16 x;
        u8  y;
        u8  hp;
        u8  anim;
        u8  prefab;
        u8  class_major;
        u8  class_mid;
        u8  class_minor;
        u8  status;
        u8  attack_windup;
        u8  attack_recover;
        s8  vx;
        GenomeProfile genome;
    } minions[MINION_MAX];
    /* Stage */
    u8   phase;             /* PHASE_* */
    u16  phase_timer;       /* generic per-phase timer */
    u8   skip_b_hold;       /* frames B has been held for skip */
    u8   wave;              /* minion wave counter */
    u8   wave_timer;        /* frames until next wave spawn */
    u8   campaign_stage;    /* current generated stage index */
    u8   campaign_active;   /* 1 while stage chain is live */
    u8   stage_theme;       /* procedural background theme id */
    u8   stage_wave_goal;   /* number of minion waves before boss awakens */
    u8   stage_wave_size;   /* minions spawned per wave */
    u8   stage_minion_hp;   /* per-stage minion durability */
    u8   stage_minion_speed;/* per-stage minion move speed */
    u8   stage_boss_hp_p1;  /* generated boss phase HP */
    u8   stage_boss_hp_p2;
    u8   stage_boss_hp_p3;
    u8   stage_boss_int_p1; /* generated boss interval cadence */
    u8   stage_boss_int_p2;
    u8   stage_boss_int_p3;
    u8   stage_boss_style;  /* attack preference profile */
    u8   stage_bg_seed;     /* render seed for layout variation */
    u8   stage_duel_mechanic;
    u8   run_serial;
    u8   run_entropy;
    u8   rei_form;
    u8   rei_persona;
    u8   rei_mutation_count;
    u8   narrative_page;
    u8   moral_choice_kind;
    u8   moral_choice_cursor;
    u8   moral_choice_made;
    u8   moral_last_choice;
    u16  rei_growth_points;
    u16  rei_style_pressure;
    u16  rei_style_precision;
    u16  rei_style_adaptation;
    u16  rei_cosmetic_mask;
    s8   moral_mercy;
    s8   moral_duty;
    s8   moral_truth;
    s8   moral_sacrifice;
    u8   audio_scene;
    u8   audio_genre;
    u8   audio_tension;
    u8   audio_pulse;
    u8   audio_voice;
    u8   audio_noise;
    u8   audio_last_narrative_page;
    u8   audio_last_choice_cursor;
    u8   stage_object_count;
    u8   stage_spawn_count;
    struct {
        u8 active;
        u8 prefab;
        u8 layer;
        u8 tx;
        u8 ty;
        u8 w;
        u8 h;
        u8 status;
        GenomeProfile genome;
    } stage_objects[ENV_OBJECT_MAX];
    struct {
        u8 active;
        u8 timer;
        u8 prefab;
        u8 lane;
        u8 side;
        u8 status;
        GenomeProfile genome;
    } spawn_slots[STAGE_SPAWN_SLOT_MAX];
    /* Title menu */
    u8   menu_sel;          /* 0=Start, 1=Password */
    char password_buf[PASSWORD_LEN + 1];
    u8   password_index;
    /* Cinematic */
    u8   cut_frame;         /* current cinematic beat/frame index 0–7 */
    u16  cut_timer;         /* timer within current cut */
    /* Score / cypher */
    u32  cleared_bosses;    /* bitmask */
    u32  cyphers;           /* bitmask */
    /* FX */
    u8   fx_hit_x;
    u8   fx_hit_y;
    u8   fx_hit_timer;
    u8   fx_nano_x;
    u8   fx_nano_y;
    u8   fx_nano_timer;
    /* Misc */
    u8   anim_tick;         /* global slow-tick for water/background animation */
    u8   banner_timer;      /* short-lived combat status banner */
    u8   banner_kind;
    u8   boss_threat;       /* 0=safe, 1=edge, 2=danger during duel */
    s8   camera_x;
    s8   camera_y;
    s8   camera_travel_bias;
    s8   camera_bg_x;
    s8   camera_bg_y;
    u8   camera_shake_timer;
    u8   camera_shake_mag;
    u16  input_held_mask;
    u16  input_pressed_mask;
    u16  input_edge_total;
    u16  input_active_frames;
    u16  input_attack_edges;
    u16  input_dodge_edges;
    u16  input_nanocell_edges;
    u16  dodge_read_total;
    u8   stage_hazard_timer;
    u8   stage_hazard_active;
    u8   stage_hazard_lane;
    u8   stage_hazard_power;
} GameState;

static GameState gs;


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: TILE LOADER
 * ═══════════════════════════════════════════════════════════════════════════ */

static void game_load_tiles(void) {
    /* Build a contiguous background tile array in stack order matching TILE_* IDs */
    /* Tile 0: blank */
    plat_load_bkg_tiles(tile_blank, TILE_BLANK, 1);
    /* Tiles 1-2: ground */
    plat_load_bkg_tiles(tile_ground_lr[0], TILE_GROUND_L, 1);
    plat_load_bkg_tiles(tile_ground_lr[1], TILE_GROUND_R, 1);
    /* Tiles 3-4: water */
    plat_load_bkg_tiles(tile_water_ab[0], TILE_WATER_A, 1);
    plat_load_bkg_tiles(tile_water_ab[1], TILE_WATER_B, 1);
    /* Tiles 5-6: cliff */
    plat_load_bkg_tiles(tile_cliff_ab[0], TILE_CLIFF_A, 1);
    plat_load_bkg_tiles(tile_cliff_ab[1], TILE_CLIFF_B, 1);
    /* Tiles 7-8: sky */
    plat_load_bkg_tiles(tile_sky_ab[0], TILE_SKY_A, 1);
    plat_load_bkg_tiles(tile_sky_ab[1], TILE_SKY_B, 1);
    /* Tiles 9-16: drIpTECH splash (8 tiles) */
    for (int i = 0; i < 8; ++i)
        plat_load_bkg_tiles(tile_splash[i], TILE_SPLASH1 + i, 1);
    /* Tiles 17-28: title logo (12 tiles) */
    for (int i = 0; i < 12; ++i)
        plat_load_bkg_tiles(tile_title[i], TILE_TITLE_A + i, 1);
    /* Tile 29: player HP segment */
    plat_load_bkg_tiles(tile_hp_seg, TILE_HP_SEG, 1);
    /* Tile 30: boss HP filled segment (first of the 6-variant set) */
    plat_load_bkg_tiles(tile_boss_hp_bar[0], TILE_BOSS_SEG, 1);
    /* Tiles 32-41: font digits */
    for (int i = 0; i < 10; ++i)
        plat_load_bkg_tiles(tile_digit[i], TILE_FONT_0 + i, 1);

    /* Sprite tiles */
    for (int i = 0; i < 6; ++i)
        plat_load_sprite_tiles(spr_rei_idle_data[i], SPR_REI_IDLE + i, 1);
    /* Run frame (generated from spr_rei_run.png) */
    for (int i = 0; i < 6; ++i)
        plat_load_sprite_tiles(spr_rei_run_data[i], SPR_REI_RUN + i, 1);
    /* Attack frame (generated from spr_rei_attack.png) */
    for (int i = 0; i < 6; ++i)
        plat_load_sprite_tiles(spr_rei_attack_data[i], SPR_REI_ATTACK + i, 1);
    /* Boss sprites */
    for (int i = 0; i < 8; ++i)
        plat_load_sprite_tiles(spr_boss_p1_data[i], SPR_BOSS_A + i, 1);
    for (int i = 0; i < 8; ++i)
        plat_load_sprite_tiles(spr_boss_p2_data[i], SPR_BOSS_B + i, 1);
    for (int i = 0; i < 8; ++i)
        plat_load_sprite_tiles(spr_boss_p3_data[i], SPR_BOSS_C + i, 1);
    /* Minion */
    for (int i = 0; i < 4; ++i)
        plat_load_sprite_tiles(spr_minion_data[i], SPR_MINION + i, 1);
    /* FX */
    for (int i = 0; i < 2; ++i)
        plat_load_sprite_tiles(spr_fx_hit_data[i],  SPR_FX_HIT + i, 1);
    for (int i = 0; i < 2; ++i)
        plat_load_sprite_tiles(spr_fx_nano_data[i], SPR_FX_NANO + i, 1);
    /* Cinematic */
    for (int i = 0; i < 12; ++i)
        plat_load_sprite_tiles(spr_cinematic_a[i], SPR_CINEMATIC_A + i, 1);
    for (int i = 0; i < 12; ++i)
        plat_load_sprite_tiles(spr_cinematic_b[i], SPR_CINEMATIC_B + i, 1);
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: BACKGROUND LAYOUT HELPERS
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Fill entire BKG with one tile */
static void bg_fill(u8 tile) {
    for (u8 y = 0; y < BKG_ROWS; ++y)
        for (u8 x = 0; x < BKG_COLS; ++x)
            plat_set_bkg_tile(x, y, tile);
}

static void bg_fill_rect(u8 x, u8 y, u8 w, u8 h, u8 tile) {
    for (u8 row = y; row < BKG_ROWS && row < (u8)(y + h); ++row)
        for (u8 col = x; col < BKG_COLS && col < (u8)(x + w); ++col)
            plat_set_bkg_tile(col, row, tile);
}

static void bg_draw_rule(u8 x, u8 y, u8 w, u8 tile_a, u8 tile_b) {
    for (u8 col = x; col < BKG_COLS && col < (u8)(x + w); ++col)
        plat_set_bkg_tile(col, y, ((col + y) & 1) ? tile_a : tile_b);
}

static void bg_draw_panel(u8 x, u8 y, u8 w, u8 h, u8 fill_tile, u8 edge_tile_a, u8 edge_tile_b) {
    if (w == 0 || h == 0) return;
    for (u8 row = y; row < BKG_ROWS && row < (u8)(y + h); ++row) {
        for (u8 col = x; col < BKG_COLS && col < (u8)(x + w); ++col) {
            u8 tile = fill_tile;
            if (row == y || row + 1 == (u8)(y + h) || col == x || col + 1 == (u8)(x + w))
                tile = (((row + col) & 1) != 0) ? edge_tile_a : edge_tile_b;
            plat_set_bkg_tile(col, row, tile);
        }
    }
}

static u8 bg_char_to_tile(char ch) {
    if (ch >= '0' && ch <= '9') return (u8)(TILE_FONT_0 + (ch - '0'));
    if (ch >= 'A' && ch <= 'Z') return (u8)(TILE_FONT_A + (ch - 'A'));
    if (ch >= 'a' && ch <= 'z') return (u8)(TILE_FONT_A + (ch - 'a'));
    return TILE_BLANK;
}

static void bg_draw_text(u8 x, u8 y, const char *text) {
    u8 start_x = x;
    while (*text && y < BKG_ROWS) {
        if (*text == '\n') {
            y++;
            x = start_x;
        } else if (x < BKG_COLS) {
            plat_set_bkg_tile(x, y, bg_char_to_tile(*text));
            x++;
        }
        text++;
    }
}

static void bg_draw_text_centered(u8 y, const char *text) {
    u8 len = 0;
    const char *scan = text;
    while (*scan && *scan != '\n') {
        len++;
        scan++;
    }
    if (len >= BKG_COLS) bg_draw_text(0, y, text);
    else bg_draw_text((u8)((BKG_COLS - len) / 2), y, text);
}

static char password_nibble_to_hex(u8 value) {
    value &= 0x0F;
    return (value < 10) ? (char)('0' + value) : (char)('A' + (value - 10));
}

static u8 password_hex_to_nibble(char ch) {
    if (ch >= '0' && ch <= '9') return (u8)(ch - '0');
    if (ch >= 'A' && ch <= 'F') return (u8)(10 + (ch - 'A'));
    if (ch >= 'a' && ch <= 'f') return (u8)(10 + (ch - 'a'));
    return 0xFF;
}

static void password_encode(char *out, u32 cleared_bosses, u32 cyphers) {
    for (u8 i = 0; i < 8; ++i) {
        u8 shift = (u8)((7 - i) * 4);
        out[i]     = password_nibble_to_hex((u8)((cleared_bosses >> shift) & 0x0F));
        out[8 + i] = password_nibble_to_hex((u8)((cyphers >> shift) & 0x0F));
    }
    out[PASSWORD_LEN] = '\0';
}

static int password_decode(const char *pwd, u32 *out_cleared_bosses, u32 *out_cyphers) {
    u32 cleared_bosses = 0;
    u32 cyphers = 0;
    for (u8 i = 0; i < 8; ++i) {
        u8 high = password_hex_to_nibble(pwd[i]);
        u8 low  = password_hex_to_nibble(pwd[8 + i]);
        if (high == 0xFF || low == 0xFF) return -1;
        cleared_bosses = (cleared_bosses << 4) | high;
        cyphers        = (cyphers << 4) | low;
    }
    if (out_cleared_bosses) *out_cleared_bosses = cleared_bosses;
    if (out_cyphers) *out_cyphers = cyphers;
    return 0;
}

static u8 campaign_next_stage_index(u32 cleared_mask) {
    for (u8 i = 0; i < CAMPAIGN_STAGE_COUNT; ++i)
        if ((cleared_mask & (1u << i)) == 0) return i;
    return CAMPAIGN_STAGE_COUNT;
}

static const char *campaign_stage_name(u8 stage_index) {
    if (stage_index >= CAMPAIGN_STAGE_COUNT) return "FINAL LOOP";
    return stage_name_table[stage_index];
}

static const char *campaign_boss_name(u8 stage_index) {
    if (stage_index >= CAMPAIGN_STAGE_COUNT) return "VOID TYRANT";
    return boss_name_table[stage_index];
}

static const char *campaign_boss_intro(u8 stage_index) {
    if (stage_index >= CAMPAIGN_STAGE_COUNT) return "VOID CUTS OPEN";
    return boss_intro_table[stage_index];
}

static const char *campaign_boss_horror_genre(u8 stage_index) {
    if (stage_index >= CAMPAIGN_STAGE_COUNT) return "VOID DREAD";
    return boss_horror_genre_table[stage_index];
}

static u8 campaign_stage_moral_kind(u8 stage_index) {
    if (stage_index >= CAMPAIGN_STAGE_COUNT) return 0;
    return stage_moral_kind_table[stage_index] & 0x03;
}

static const CampaignStageDesign *campaign_stage_design(u8 stage_index) {
    if (stage_index >= CAMPAIGN_STAGE_COUNT) stage_index = CAMPAIGN_STAGE_COUNT - 1;
    return &campaign_stage_design_table[stage_index];
}

static const char *campaign_stage_ecosystem(u8 stage_index) {
    return campaign_stage_design(stage_index)->ecosystem;
}

static const char *campaign_stage_hazard_line(u8 stage_index) {
    return campaign_stage_design(stage_index)->hazard_line;
}

static const char *campaign_stage_minion_line(u8 stage_index) {
    return campaign_stage_design(stage_index)->minion_line;
}

static const char *campaign_stage_cypher_label(u8 stage_index) {
    return campaign_stage_design(stage_index)->cypher_label;
}

static const char *campaign_stage_cypher_effect(u8 stage_index) {
    return campaign_stage_design(stage_index)->cypher_effect;
}

static const char *campaign_stage_terrain_line(u8 stage_index) {
    return campaign_stage_design(stage_index)->terrain_line;
}

static const char *campaign_stage_pressure_line(u8 stage_index) {
    return campaign_stage_design(stage_index)->pressure_line;
}

static u8 campaign_adaptive_pressure(u8 stage_index);
static u8 stage_mix8(u8 seed, u8 salt);

static u8 campaign_stage_prefab_bias(u8 stage_index) {
    switch (stage_index) {
        case 0: case 6: case 10: return 2;
        case 1: case 7: case 11: return 1;
        case 2: case 8: return 3;
        case 3: case 5: case 9: return 0;
        default: return 0;
    }
}

static u8 stage_spawn_prefab_choice(u8 stage_index, u8 seed) {
    u8 bias = campaign_stage_prefab_bias(stage_index);
    switch (stage_index) {
        case 0:
            return (u8)(((seed & 0x01) == 0) ? 0 : 2);
        case 1:
            return (u8)(((seed & 0x03) < 2) ? 1 : 0);
        case 2:
            return (u8)(((seed & 0x01) == 0) ? 2 : 3);
        case 3:
            return (u8)(((seed & 0x03) == 0) ? 1 : 0);
        case 4:
            return (u8)(((seed & 0x01) == 0) ? 1 : 3);
        case 5:
            return (u8)(((seed & 0x01) == 0) ? 2 : 0);
        case 6:
            return (u8)(((seed & 0x01) == 0) ? 3 : 2);
        case 7:
            return (u8)(((seed & 0x01) == 0) ? 1 : 3);
        case 8:
            return (u8)(((seed & 0x03) < 3) ? 3 : 2);
        case 9:
            return (u8)(((seed & 0x01) == 0) ? 2 : 1);
        case 10:
            return (u8)(((seed & 0x01) == 0) ? 2 : 3);
        case 11:
            return (u8)(((seed & 0x03) < 2) ? 1 : 3);
        default:
            return (u8)((seed + bias) % MINION_PREFAB_COUNT);
    }
}

static u8 stage_hazard_trigger_period(void) {
    return (u8)(78 - (gs.campaign_stage * 2) - campaign_adaptive_pressure(gs.campaign_stage) * 3);
}

static u8 stage_hazard_lane_for_player(void) {
    if (gs.player_x < 6) return 0;
    if (gs.player_x < 12) return 1;
    return 2;
}

static const char *stage_hazard_prompt(void) {
    switch (gs.stage_theme & 0x03) {
        case 0: return "SURF LANE BREAKS";
        case 1: return "ASH WALL CLOSES";
        case 2: return "ROOT LANE SNARES";
        default: return "WHITEOUT CUTS SIGHT";
    }
}

static void stage_hazard_reset(void) {
    gs.stage_hazard_active = 0;
    gs.stage_hazard_lane = (u8)(gs.stage_bg_seed % 3);
    gs.stage_hazard_power = (u8)(1 + ((gs.campaign_stage / 4) & 0x01));
    gs.stage_hazard_timer = stage_hazard_trigger_period();
    if (gs.stage_hazard_timer < 32) gs.stage_hazard_timer = 32;
}

static void stage_hazard_update(void) {
    if (gs.stage_hazard_active > 0) {
        gs.stage_hazard_active--;
        if (gs.stage_hazard_active == 0) gs.stage_hazard_timer = stage_hazard_trigger_period();
        return;
    }
    if (gs.stage_hazard_timer > 0) {
        gs.stage_hazard_timer--;
        return;
    }
    gs.stage_hazard_lane = (u8)(stage_mix8(gs.stage_bg_seed, (u8)(33 + gs.phase_timer + gs.wave)) % 3);
    gs.stage_hazard_power = (u8)(1 + ((gs.campaign_stage >= 8) ? 1 : 0) + (campaign_adaptive_pressure(gs.campaign_stage) >= 2));
    gs.stage_hazard_active = (u8)(18 + (gs.stage_theme * 4));
}

static void stage_hazard_apply_to_minions(void) {
    if (gs.stage_hazard_active == 0) return;
    for (u8 i = 0; i < MINION_MAX; ++i) {
        if (!gs.minions[i].active) continue;
        if (((u8)(gs.minions[i].x / 48)) != gs.stage_hazard_lane) continue;
        if ((gs.stage_theme & 0x03) == 2) {
            gs.minions[i].attack_windup = (u8)(gs.minions[i].attack_windup + 1);
        } else if ((gs.stage_theme & 0x03) == 1) {
            gs.minions[i].vx = (s8)(-gs.minions[i].vx);
        }
    }
}

static void stage_hazard_apply_to_player(void) {
    if (gs.stage_hazard_active == 0) return;
    if (stage_hazard_lane_for_player() != gs.stage_hazard_lane) return;
    if (gs.dodge_timer > 0) return;
    if ((gs.phase_timer & 0x07) != 0) return;
    switch (gs.stage_theme & 0x03) {
        case 0:
            if (gs.boss_x > (s16)(gs.player_x * TILE_W) && gs.player_x < 17) gs.player_x++;
            else if (gs.player_x > 0) gs.player_x--;
            break;
        case 1:
            if (gs.player_x < 17 && (gs.phase_timer & 0x10) == 0) gs.player_x++;
            break;
        case 2:
            gs.hit_stun = (u8)(gs.hit_stun < 8 ? 8 : gs.hit_stun);
            break;
        default:
            gs.camera_shake_timer = 6;
            gs.camera_shake_mag = 2;
            break;
    }
    if (gs.hit_stun == 0 && gs.player_hp > 0) gs.player_hp--;
    gs.hit_stun = (u8)(gs.hit_stun < (u8)(10 + gs.stage_hazard_power * 2) ? (u8)(10 + gs.stage_hazard_power * 2) : gs.hit_stun);
    gs.fx_hit_x = (u8)(gs.player_x * TILE_W + 4);
    gs.fx_hit_y = (u8)(SCR_H - 30);
    gs.fx_hit_timer = 6;
}

static const char *campaign_rei_intro(u8 boss_prefab) {
    return rei_intro_table[boss_prefab % BOSS_ARCHETYPE_COUNT];
}

static u8 duel_qte_button_for_style(u8 style) {
    switch (style & 0x03) {
        case 0: return BTN_A;
        case 1: return BTN_B;
        case 2: return BTN_SELECT;
        default: return BTN_A;
    }
}

static const char *duel_qte_prompt(u8 button) {
    if (button == BTN_B) return "B CUT NOW";
    if (button == BTN_SELECT) return "SEL SURGE NOW";
    return "A CLASH NOW";
}

static u8 rei_form_for_points(u16 points) {
    u8 form = 0;
    for (u8 i = 0; i < REI_FORM_COUNT; ++i) {
        if (points >= rei_form_thresholds[i]) form = i;
    }
    return form;
}

static void rei_refresh_growth_state(void) {
    gs.rei_form = rei_form_for_points(gs.rei_growth_points);
    gs.rei_mutation_count = (u8)(1 + (gs.rei_form / 2));
    if (gs.rei_mutation_count > REI_MUTATION_COUNT) gs.rei_mutation_count = REI_MUTATION_COUNT;
    gs.rei_persona = (u8)((gs.rei_style_pressure + gs.rei_style_precision * 2 + gs.rei_style_adaptation * 3 + gs.run_entropy) % 6);
    gs.rei_cosmetic_mask = (u16)((1u << gs.rei_mutation_count) - 1u);
    gs.rei_cosmetic_mask ^= (u16)((gs.run_serial << 4) | gs.rei_form | (gs.rei_persona << 8));
}

static void text_join_pair(char *out, u8 out_size, const char *left, const char *right) {
    u8 idx = 0;
    while (*left && idx + 1 < out_size) out[idx++] = *left++;
    if (idx + 1 < out_size) out[idx++] = ' ';
    while (*right && idx + 1 < out_size) out[idx++] = *right++;
    out[idx] = '\0';
}

static void text_prefix_word(char *out, u8 out_size, const char *prefix, const char *word) {
    u8 idx = 0;
    while (*prefix && idx + 1 < out_size) out[idx++] = *prefix++;
    if (idx + 1 < out_size) out[idx++] = ' ';
    while (*word && idx + 1 < out_size) out[idx++] = *word++;
    out[idx] = '\0';
}

static u8 moral_abs(s8 value) {
    return (u8)(value < 0 ? -value : value);
}

static u8 narrative_dominant_moral_index(void) {
    u8 best = 0;
    u8 best_strength = 0;
    u8 strength;
    strength = moral_abs(gs.moral_mercy);
    if (strength > best_strength) {
        best_strength = strength;
        best = (gs.moral_mercy >= 0) ? 1 : 2;
    }
    strength = moral_abs(gs.moral_duty);
    if (strength > best_strength) {
        best_strength = strength;
        best = (gs.moral_duty >= 0) ? 3 : 4;
    }
    strength = moral_abs(gs.moral_truth);
    if (strength > best_strength) {
        best_strength = strength;
        best = (gs.moral_truth >= 0) ? 5 : 6;
    }
    strength = moral_abs(gs.moral_sacrifice);
    if (strength > best_strength) {
        best = (gs.moral_sacrifice >= 0) ? 7 : 8;
    }
    return best;
}

static const char *narrative_moral_path(void) {
    return moral_path_table[narrative_dominant_moral_index()];
}

static const char *narrative_path_line(void) {
    static char line[21];
    u8 path_idx = narrative_dominant_moral_index();
    if (path_idx == 0) {
        text_join_pair(line, sizeof(line), "PATH", "STILL OPEN");
    } else {
        text_prefix_word(line, sizeof(line), "PATH", moral_path_table[path_idx]);
    }
    return line;
}

static void narrative_seed_choice(void) {
    gs.moral_choice_kind = campaign_stage_moral_kind(gs.campaign_stage);
    gs.moral_choice_cursor = (u8)((gs.boss_subarchetype + gs.run_serial) & 0x01);
    gs.moral_choice_made = 0;
}

static void narrative_apply_choice(void) {
    gs.moral_choice_made = 1;
    gs.moral_last_choice = gs.moral_choice_cursor;
    switch (gs.moral_choice_kind & 0x03) {
        case 0:
            gs.moral_mercy += gs.moral_choice_cursor ? -1 : 1;
            break;
        case 1:
            gs.moral_duty += gs.moral_choice_cursor ? -1 : 1;
            break;
        case 2:
            gs.moral_truth += gs.moral_choice_cursor ? -1 : 1;
            break;
        default:
            gs.moral_sacrifice += gs.moral_choice_cursor ? -1 : 1;
            break;
    }
    plat_audio_event(AUDIO_EVENT_CHOICE, (u8)(1 + gs.moral_choice_cursor + gs.moral_choice_kind * 2));
}

static const char *narrative_stage_line_a(void) {
    return campaign_boss_name(gs.campaign_stage);
}

static const char *narrative_stage_line_b(void) {
    return campaign_stage_ecosystem(gs.campaign_stage);
}

static const char *narrative_stage_line_c(void) {
    return campaign_stage_hazard_line(gs.campaign_stage);
}

static const char *narrative_choice_line_a(void) {
    return boss_choice_prompt_a_table[gs.campaign_stage];
}

static const char *narrative_choice_line_b(void) {
    return boss_choice_prompt_b_table[gs.campaign_stage];
}

static const char *narrative_choice_option(u8 option_index) {
    static char line[21];
    const char *option = option_index ? boss_choice_right_table[gs.campaign_stage]
                                      : boss_choice_left_table[gs.campaign_stage];
    text_join_pair(line, sizeof(line), (gs.moral_choice_cursor == option_index) ? ">" : "-", option);
    return line;
}

static const char *narrative_result_line_a(void) {
    return gs.moral_last_choice ? boss_choice_right_result_table[gs.campaign_stage]
                                : boss_choice_left_result_table[gs.campaign_stage];
}

static const char *narrative_result_line_b(void) {
    static char line[21];
    text_join_pair(line, sizeof(line), "REI BEARS", narrative_moral_path());
    return line;
}

static u8 audio_scene_for_phase(void) {
    switch (gs.phase) {
        case PHASE_SPLASH: return AUDIO_SCENE_SPLASH;
        case PHASE_CINEMATIC: return AUDIO_SCENE_CINEMATIC;
        case PHASE_TITLE:
        case PHASE_PASSWORD:
            return AUDIO_SCENE_TITLE;
        case PHASE_NARRATIVE:
            return AUDIO_SCENE_NARRATIVE;
        case PHASE_STAGE_INTRO:
            return AUDIO_SCENE_DUEL;
        case PHASE_COMBAT:
            return AUDIO_SCENE_COMBAT;
        case PHASE_CYPHER_DROP:
            return AUDIO_SCENE_CYPHER;
        default:
            return AUDIO_SCENE_GAMEOVER;
    }
}

static u8 audio_voice_for_state(void) {
    switch (gs.phase) {
        case PHASE_NARRATIVE:
            if (gs.narrative_page == 0) return AUDIO_VOICE_BOSS;
            if (gs.narrative_page == 1) return AUDIO_VOICE_CHORUS;
            return AUDIO_VOICE_REI;
        case PHASE_STAGE_INTRO:
            return AUDIO_VOICE_BOSS;
        case PHASE_COMBAT:
            if (gs.banner_kind != BANNER_NONE) return AUDIO_VOICE_SYSTEM;
            return (gs.boss_windup > 0 || gs.boss_phase > 1) ? AUDIO_VOICE_BOSS : AUDIO_VOICE_REI;
        case PHASE_CYPHER_DROP:
        case PHASE_GAME_OVER:
            return AUDIO_VOICE_SYSTEM;
        default:
            return AUDIO_VOICE_NONE;
    }
}

static u8 audio_tension_from_state(void) {
    u8 tension = 1;
    switch (gs.phase) {
        case PHASE_SPLASH: tension = 1; break;
        case PHASE_CINEMATIC: tension = 2; break;
        case PHASE_TITLE:
        case PHASE_PASSWORD:
            tension = 1;
            break;
        case PHASE_NARRATIVE:
            tension = (u8)(3 + gs.narrative_page + (narrative_dominant_moral_index() != 0));
            break;
        case PHASE_STAGE_INTRO:
            tension = (u8)(5 + ((gs.phase_timer / 24) & 0x03));
            break;
        case PHASE_COMBAT:
            tension = (u8)(6 + gs.boss_phase + gs.boss_threat + (PLAYER_MAX_HP - gs.player_hp));
            if (gs.banner_kind != BANNER_NONE) tension += 1;
            if (gs.combo_count >= 2) tension += 1;
            break;
        case PHASE_CYPHER_DROP:
            tension = 3;
            break;
        default:
            tension = 7;
            break;
    }
    if (tension > 15) tension = 15;
    return tension;
}

static u8 audio_pulse_from_state(void) {
    u8 pulse = (u8)(2 + (gs.stage_boss_style * 2) + (gs.stage_duel_mechanic & 0x03));
    if (gs.phase == PHASE_COMBAT) {
        pulse = (u8)(pulse + gs.combo_count + (gs.beat_perfect ? 2 : 0));
        if (gs.boss_windup > 0) pulse += 2;
    } else if (gs.phase == PHASE_STAGE_INTRO) {
        pulse = (u8)(pulse + 3 + ((gs.phase_timer / 20) & 0x01));
    } else if (gs.phase == PHASE_NARRATIVE) {
        pulse = (u8)(pulse + gs.narrative_page);
    }
    if (pulse > 15) pulse = 15;
    return pulse;
}

static u8 audio_noise_from_state(void) {
    u8 noise = (u8)((gs.stage_theme << 1) + (gs.boss_subarchetype & 0x03) + (gs.run_entropy & 0x03));
    if (gs.phase == PHASE_NARRATIVE) noise = (u8)(noise + narrative_dominant_moral_index());
    if (noise > 15) noise = 15;
    return noise;
}

static void audio_sync_profile(void) {
    gs.audio_scene = audio_scene_for_phase();
    gs.audio_genre = gs.campaign_stage;
    gs.audio_tension = audio_tension_from_state();
    gs.audio_pulse = audio_pulse_from_state();
    gs.audio_voice = audio_voice_for_state();
    gs.audio_noise = audio_noise_from_state();
#ifdef TARGET_3DS
    {
        u8 audio_bias = (u8)(ctr_audio_disturbance * 4.0f + 0.5f);
        u8 visual_bias = (u8)(ctr_visual_disturbance * 3.0f + 0.5f);
        u8 pressure_bias = (u8)(ctr_sinus_pressure * 3.0f + ctr_eye_strain * 2.0f + 0.5f);
        if (audio_bias > 0) {
            if (gs.audio_tension + audio_bias > 15) gs.audio_tension = 15;
            else gs.audio_tension = (u8)(gs.audio_tension + audio_bias);
            if (gs.audio_pulse + (audio_bias / 2u) > 15) gs.audio_pulse = 15;
            else gs.audio_pulse = (u8)(gs.audio_pulse + (audio_bias / 2u));
        }
        if (pressure_bias > 0) {
            if (gs.audio_tension + pressure_bias > 15) gs.audio_tension = 15;
            else gs.audio_tension = (u8)(gs.audio_tension + pressure_bias);
        }
        if (visual_bias + audio_bias > 0) {
            u8 total_bias = (u8)(visual_bias + audio_bias);
            total_bias = (u8)(total_bias + pressure_bias);
            if (gs.audio_noise + total_bias > 15) gs.audio_noise = 15;
            else gs.audio_noise = (u8)(gs.audio_noise + total_bias);
        }
    }
#endif
    plat_audio_profile(gs.audio_scene, gs.audio_genre, gs.audio_tension, gs.audio_pulse, gs.audio_voice, gs.audio_noise);
}

static void audio_emit_narrative_tts(void) {
    if (gs.audio_last_narrative_page == gs.narrative_page) {
        if (gs.narrative_page != 1 || gs.audio_last_choice_cursor == gs.moral_choice_cursor) return;
    }
    gs.audio_last_narrative_page = gs.narrative_page;
    gs.audio_last_choice_cursor = gs.moral_choice_cursor;
    if (gs.narrative_page == 0) {
        plat_audio_tts(AUDIO_VOICE_BOSS, narrative_stage_line_a());
        plat_audio_tts(AUDIO_VOICE_CHORUS, narrative_stage_line_b());
        plat_audio_tts(AUDIO_VOICE_BOSS, narrative_stage_line_c());
        plat_audio_tts(AUDIO_VOICE_BOSS, campaign_boss_intro(gs.campaign_stage));
    } else if (gs.narrative_page == 1) {
        plat_audio_tts(AUDIO_VOICE_CHORUS, narrative_choice_line_a());
        plat_audio_tts(AUDIO_VOICE_CHORUS, narrative_choice_line_b());
        if (gs.moral_choice_cursor == 0) plat_audio_tts(AUDIO_VOICE_REI, boss_choice_left_table[gs.campaign_stage]);
        else plat_audio_tts(AUDIO_VOICE_REI, boss_choice_right_table[gs.campaign_stage]);
    } else {
        plat_audio_tts(AUDIO_VOICE_REI, narrative_result_line_a());
        plat_audio_tts(AUDIO_VOICE_BOSS, narrative_result_line_b());
    }
    audio_sync_profile();
}

static void audio_emit_stage_intro_tts(void) {
    plat_audio_tts(AUDIO_VOICE_BOSS, campaign_boss_intro(gs.campaign_stage));
    plat_audio_tts(AUDIO_VOICE_CHORUS, campaign_stage_hazard_line(gs.campaign_stage));
    plat_audio_tts(AUDIO_VOICE_REI, campaign_rei_intro(gs.boss_prefab));
    plat_audio_tts(AUDIO_VOICE_SYSTEM, duel_mechanic_label(gs.stage_duel_mechanic));
    plat_audio_tts(AUDIO_VOICE_SYSTEM, campaign_stage_cypher_label(gs.campaign_stage));
    plat_audio_event(AUDIO_EVENT_PHASE, gs.campaign_stage);
    audio_sync_profile();
}

static void rei_apply_stage_growth(void) {
    u16 growth = (u16)(gs.combo_count * 2 + gs.dodge_read_total + gs.input_attack_edges + (gs.nanocell_count > 0 ? 2 : 0));
    if (gs.player_hp >= 4) growth += 3;
    gs.rei_style_pressure += (u16)(gs.input_attack_edges + gs.combo_count);
    gs.rei_style_precision += (u16)(gs.dodge_read_total + (gs.beat_perfect ? 1 : 0));
    gs.rei_style_adaptation += (u16)(gs.input_nanocell_edges + gs.input_dodge_edges);
    gs.rei_growth_points += growth;
    rei_refresh_growth_state();
}

static u8 campaign_adaptive_pressure(u8 stage_index) {
    s16 pressure = (s16)(stage_index / 4);
    pressure += (s16)(gs.run_serial & 0x01);
    pressure += (s16)(gs.rei_growth_points / 18u);
    pressure += (gs.rei_style_pressure > gs.rei_style_precision) ? 1 : 0;
    pressure += (narrative_dominant_moral_index() >= 5) ? 1 : 0;
    pressure -= (gs.rei_style_adaptation > gs.rei_style_pressure) ? 1 : 0;
    if (pressure < 0) pressure = 0;
    if (pressure > 3) pressure = 3;
    return (u8)pressure;
}

static const char *duel_mechanic_label(u8 mechanic) {
    switch (mechanic & 0x03) {
        case 0: return "CLASH BREAK";
        case 1: return "CUT STEP";
        case 2: return "SURGE ENTRY";
        default: return "TIDE READ";
    }
}

static void duel_apply_intro_outcome(void) {
    plat_audio_event(AUDIO_EVENT_DUEL, (u8)(1 + gs.duel_qte_result + gs.stage_duel_mechanic * 2));
    if (gs.duel_qte_result == 1) {
        switch (gs.stage_duel_mechanic & 0x03) {
            case 0:
                gs.duel_first_strike_timer = DUEL_FIRST_STRIKE_FRAMES + 12;
                gs.boss_stun = 18;
                gs.boss_x += 6;
                break;
            case 1:
                gs.dodge_timer = 8;
                gs.boss_intro_lock = 18;
                gs.boss_atk_timer += 12;
                break;
            case 2:
                gs.nanocell_boost_timer = 45;
                gs.attack_dmg = 2;
                gs.duel_first_strike_timer = DUEL_FIRST_STRIKE_FRAMES + 16;
                break;
            default:
                gs.boss_stun = 10;
                gs.boss_recover = 10;
                gs.boss_atk_timer += 20;
                break;
        }
    } else if (gs.duel_qte_result == 2) {
        switch (gs.stage_duel_mechanic & 0x03) {
            case 0:
                gs.boss_atk_timer = 16;
                gs.boss_atk_type = BOSS_ATK_SWEEP;
                break;
            case 1:
                gs.boss_atk_timer = 18;
                gs.boss_atk_type = BOSS_ATK_SPIT;
                break;
            case 2:
                gs.boss_atk_timer = 14;
                gs.boss_atk_type = BOSS_ATK_SLAM;
                break;
            default:
                gs.boss_atk_timer = 12;
                gs.boss_atk_type = BOSS_ATK_TIDAL;
                break;
        }
        gs.duel_first_strike_timer = 0;
    }
}

static u8 boss_tile_index(u8 slot) {
    u8 archetype = (u8)(gs.boss_prefab % BOSS_ARCHETYPE_COUNT);
    u8 tile = boss_tile_layout_db[archetype][slot & 0x07];
    tile = (u8)((tile + boss_subtile_variant_db[gs.boss_subarchetype % BOSS_SUBARCHETYPE_COUNT][slot & 0x07]) & 0x07);
    if (slot < 4 && gs.boss_genome.ferocity > 2) tile = (u8)((tile + 1) & 0x07);
    if (slot >= 4 && gs.boss_genome.shell > 2) tile = (u8)((tile + 2) & 0x07);
    if (((slot + gs.boss_genome.mobility + gs.stage_bg_seed) & 0x01) != 0) tile = (u8)((tile + 3) & 0x07);
    return tile;
}

static u8 boss_tile_flags(u8 slot) {
    u8 archetype = (u8)(gs.boss_prefab % BOSS_ARCHETYPE_COUNT);
    u8 flags = boss_tile_flip_db[archetype][slot & 0x07];
    if (((gs.boss_subarchetype + slot) & 0x01) != 0) flags ^= 0x20;
    if (((slot + gs.boss_genome.mobility) & 0x01) != 0) flags ^= 0x20;
    return flags;
}

static s8 boss_tile_offset_x(u8 slot) {
    u8 archetype = (u8)(gs.boss_prefab % BOSS_ARCHETYPE_COUNT);
    s8 offset = boss_tile_x_offset_db[archetype][slot & 0x07];
    offset += (s8)(gs.boss_subarchetype - 1);
    offset += (s8)(gs.boss_genome.ferocity - 2);
    if ((slot & 0x03) >= 2) offset += (s8)(gs.boss_genome.mobility - 2);
    return offset;
}

static s8 boss_tile_offset_y(u8 slot) {
    u8 archetype = (u8)(gs.boss_prefab % BOSS_ARCHETYPE_COUNT);
    s8 offset = boss_tile_y_offset_db[archetype][slot & 0x07];
    offset += (s8)((gs.boss_subarchetype == 3) ? 1 : 0);
    if (slot < 4) offset -= (s8)(gs.boss_genome.shell - 2);
    else offset += (s8)(gs.boss_genome.mobility - 2);
    return offset;
}

static u8 stage_mix8(u8 seed, u8 salt) {
    u16 value = (u16)seed * 17u + (u16)salt * 31u + (u16)gs.campaign_stage * 13u + (u16)gs.run_serial * 29u + (u16)gs.run_entropy;
    value ^= (value >> 3);
    value += (u16)(salt * 7u);
    return (u8)(value & 0xFFu);
}

static GenomeProfile stage_make_genome(u8 seed, u8 salt) {
    GenomeProfile genome;
    u8 mix = stage_mix8(seed, salt);
    genome.ferocity = (u8)(1 + (mix & 0x03));
    genome.shell    = (u8)(1 + ((mix >> 2) & 0x03));
    genome.mobility = (u8)(1 + ((mix >> 4) & 0x03));
    return genome;
}

static u8 stage_theme_subclass(void) {
    return (u8)(stage_mix8(gs.stage_bg_seed, (u8)(9 + gs.stage_theme * 13 + gs.run_serial)) % ENV_THEME_SUBCLASS_COUNT);
}

static const EnvThemeSubclass *stage_theme_profile(void) {
    return &env_theme_subclass_db[gs.stage_theme & 0x03][stage_theme_subclass()];
}

static u8 stage_profile_density_score(void) {
    const CampaignStageDesign *design = campaign_stage_design(gs.campaign_stage);
    const EnvThemeSubclass *profile = stage_theme_profile();
    return (u8)(design->density_bias + profile->density);
}

static u8 stage_profile_sightline_score(void) {
    const CampaignStageDesign *design = campaign_stage_design(gs.campaign_stage);
    const EnvThemeSubclass *profile = stage_theme_profile();
    return (u8)(design->route_bias + profile->sightline_bias);
}

static u8 stage_profile_current_bias(void) {
    const CampaignStageDesign *design = campaign_stage_design(gs.campaign_stage);
    const EnvThemeSubclass *profile = stage_theme_profile();
    return (u8)(design->weather_bias + profile->current_bias);
}

static u8 stage_profile_lane_pressure(void) {
    const CampaignStageDesign *design = campaign_stage_design(gs.campaign_stage);
    const EnvThemeSubclass *profile = stage_theme_profile();
    return (u8)(design->route_bias + profile->lane_bias);
}

static u8 stage_ai_directive(void) {
    const CampaignStageDesign *design = campaign_stage_design(gs.campaign_stage);
    u8 moral = narrative_dominant_moral_index();
    u8 authored = design->ai_directive % RUN_AI_DIRECTIVE_COUNT;
    u8 drift = (u8)(stage_mix8((u8)(gs.stage_bg_seed + gs.run_serial * 3 + gs.rei_form * 5), (u8)(151 + gs.campaign_stage * 7 + moral * 11)) & 0x01);
    return (u8)((authored + drift + ((moral >= 5) ? 1 : 0)) % RUN_AI_DIRECTIVE_COUNT);
}

static void stage_build_environment(void) {
    const CampaignStageDesign *design = campaign_stage_design(gs.campaign_stage);
    const EnvThemeSubclass *profile = stage_theme_profile();
    u8 density_score = stage_profile_density_score();
    u8 sightline_score = stage_profile_sightline_score();
    u8 lane_pressure = stage_profile_lane_pressure();
    u8 object_count = (u8)(3 + (density_score > 3) + (density_score > 5) + (gs.campaign_stage >= 6));
    if (object_count > ENV_OBJECT_MAX) object_count = ENV_OBJECT_MAX;
    for (u8 i = 0; i < ENV_OBJECT_MAX; ++i) {
        gs.stage_objects[i].active = 0;
    }
    for (u8 i = 0; i < object_count; ++i) {
        u8 mix = stage_mix8(gs.stage_bg_seed, (u8)(i + 1));
        u8 layer = (u8)((i + profile->ridge_bias + design->route_bias) % 3);
        u8 lane_band = (u8)((i + lane_pressure + (mix >> 6)) % 3);
        u8 prefab_index = (u8)((mix + profile->prefab_bias[layer] + gs.stage_theme + design->density_bias) % ENV_PREFAB_COUNT);
        u8 tx_min = (u8)(1 + lane_band * 5);
        u8 tx_room = (u8)((lane_band == 1) ? 5 : 4);
        u8 tx_span = (u8)(1 + (profile->sky_stride & 0x03) + (sightline_score > 5));
        u8 ty_base = (u8)(7 + layer * 2 + (profile->water_rows & 0x01) + (density_score > 6));
        u8 ty_room = (u8)(4 - (layer == 2));
        const EnvPrefab *prefab = &env_prefab_db[prefab_index];
        gs.stage_objects[i].active = 1;
        gs.stage_objects[i].prefab = prefab_index;
        gs.stage_objects[i].layer  = layer;
        gs.stage_objects[i].tx     = (u8)(tx_min + (((mix * tx_span) + design->weather_bias + profile->split_bias) % tx_room));
        gs.stage_objects[i].ty     = (u8)(ty_base + (((mix >> (2 + (layer & 0x01))) + profile->current_bias) % ty_room));
        gs.stage_objects[i].w      = prefab->w;
        gs.stage_objects[i].h      = prefab->h;
        gs.stage_objects[i].status = (u8)(1 + ((mix + profile->ridge_bias + profile->current_bias + layer) & 0x03));
        gs.stage_objects[i].genome = stage_make_genome(gs.stage_bg_seed, (u8)(40 + i + profile->split_bias + design->density_bias * 3));
        if ((u8)(gs.stage_objects[i].tx + gs.stage_objects[i].w) >= BKG_COLS)
            gs.stage_objects[i].tx = (u8)(BKG_COLS - gs.stage_objects[i].w - 1);
        if ((u8)(gs.stage_objects[i].ty + gs.stage_objects[i].h) >= BKG_ROWS)
            gs.stage_objects[i].ty = (u8)(BKG_ROWS - gs.stage_objects[i].h - 1);
    }
    gs.stage_object_count = object_count;
}

static void stage_prepare_spawn_protocol(void) {
    const CampaignStageDesign *design = campaign_stage_design(gs.campaign_stage);
    const EnvThemeSubclass *profile = stage_theme_profile();
    u8 density_score = stage_profile_density_score();
    u8 lane_pressure = stage_profile_lane_pressure();
    u8 current_bias = stage_profile_current_bias();
    u8 directive = stage_ai_directive();
    u8 boss_seed = stage_mix8(gs.stage_bg_seed, 91);
    const BossPrefab *boss_prefab;
    gs.boss_prefab = (u8)(boss_seed % BOSS_ARCHETYPE_COUNT);
    gs.boss_subarchetype = (u8)((boss_seed >> 3) % BOSS_SUBARCHETYPE_COUNT);
    gs.boss_prefab = design->boss_prefab % BOSS_ARCHETYPE_COUNT;
    gs.boss_subarchetype = design->boss_subarchetype % BOSS_SUBARCHETYPE_COUNT;
    boss_prefab = &boss_prefab_db[gs.boss_prefab];
    gs.boss_genome = stage_make_genome(boss_seed, 17);
    gs.boss_status = (u8)(1 + ((boss_seed >> 5) & 0x03));
    gs.stage_boss_style = design->boss_style & 0x03;
    gs.stage_duel_mechanic = design->duel_mechanic & 0x03;
    gs.boss_intro_lock = boss_prefab->opener_lock;
    gs.duel_first_strike_timer = DUEL_FIRST_STRIKE_FRAMES;
    gs.duel_qte_button = duel_qte_button_for_style(gs.stage_duel_mechanic);
    gs.duel_qte_result = 0;
    gs.duel_qte_ready = 0;
    gs.stage_spawn_count = gs.stage_wave_goal;
    if (gs.stage_spawn_count > STAGE_SPAWN_SLOT_MAX) gs.stage_spawn_count = STAGE_SPAWN_SLOT_MAX;
    for (u8 i = 0; i < STAGE_SPAWN_SLOT_MAX; ++i) {
        gs.spawn_slots[i].active = 0;
    }
    for (u8 i = 0; i < gs.stage_spawn_count; ++i) {
        u8 mix = stage_mix8(gs.stage_bg_seed, (u8)(110 + i));
        u8 cadence = (u8)(24 - (gs.campaign_stage / 3) - boss_prefab->pressure_bias - (lane_pressure > 5 ? 2 : 0));
        u8 cluster = (u8)(mix & 0x07);
        u8 lane_seed = (u8)(profile->lane_bias + design->route_bias + boss_prefab->pressure_bias);
        if (cadence < 12) cadence = 12;
        if (current_bias > 5) cadence = (u8)(cadence + 1);
        if (directive == 0 && cadence > 14) cadence -= 2;
        else if (directive == 2 && cadence > 15) cadence -= 1;
        else if (directive == 3) cadence = (u8)(cadence + 2);
        gs.spawn_slots[i].active = 1;
        gs.spawn_slots[i].timer  = (u8)(DUEL_FIRST_STRIKE_FRAMES + 18 + i * cadence + (mix & 0x0F) + (density_score > 6 ? 4 : 0));
        gs.spawn_slots[i].prefab = stage_spawn_prefab_choice(gs.campaign_stage, (u8)(mix + boss_prefab->summon_bias + current_bias));
        gs.spawn_slots[i].lane   = (u8)(((mix >> 3) + lane_seed) % 3);
        gs.spawn_slots[i].side   = (u8)(((mix >> 5) + boss_prefab->summon_bias + (current_bias > 5)) & 0x01);
        gs.spawn_slots[i].status = (u8)(1 + ((mix + density_score + current_bias) & 0x03));
        gs.spawn_slots[i].genome = stage_make_genome(mix, (u8)(130 + i));
        switch (directive) {
            case 0:
                gs.spawn_slots[i].timer = (u8)(gs.spawn_slots[i].timer - ((i < 2) ? (u8)(6 + (cluster & 0x03)) : 0));
                gs.spawn_slots[i].lane = (u8)(1 + (((mix >> 5) + profile->lane_bias) & 0x01));
                gs.spawn_slots[i].side = (u8)((gs.run_serial + i + boss_prefab->pressure_bias) & 0x01);
                break;
            case 1:
                gs.spawn_slots[i].lane = (u8)((i + ((mix >> 4) & 0x01) + design->route_bias) % 3);
                gs.spawn_slots[i].side = (u8)(i & 0x01);
                gs.spawn_slots[i].status = (u8)(1 + ((gs.spawn_slots[i].status + 1) & 0x03));
                break;
            case 2:
                gs.spawn_slots[i].timer = (u8)(DUEL_FIRST_STRIKE_FRAMES + 12 + (i / 2) * cadence + cluster);
                gs.spawn_slots[i].prefab = stage_spawn_prefab_choice(gs.campaign_stage, (u8)(gs.spawn_slots[i].prefab + i + boss_prefab->summon_bias));
                break;
            case 3:
                gs.spawn_slots[i].timer = (u8)(gs.spawn_slots[i].timer + ((i < 2) ? 10 : (u8)(2 + (cluster & 0x03))));
                gs.spawn_slots[i].lane = (u8)((2 - ((i + profile->lane_bias) % 3)));
                gs.spawn_slots[i].side = (u8)(((mix >> 1) + i + gs.campaign_stage + design->weather_bias) & 0x01);
                break;
            default:
                gs.spawn_slots[i].timer = (u8)(DUEL_FIRST_STRIKE_FRAMES + 10 + ((mix * 5u) % (u8)(cadence * 2u + 1u)));
                gs.spawn_slots[i].lane = (u8)((mix + i + directive + design->route_bias) % 3);
                gs.spawn_slots[i].side = (u8)(((mix >> 2) + gs.run_entropy + i) & 0x01);
                gs.spawn_slots[i].status = (u8)(1 + ((mix + gs.run_serial + i) & 0x03));
                break;
        }
    }
}

static void campaign_generate_stage(u8 stage_index) {
    const CampaignStageDesign *design = campaign_stage_design(stage_index);
    u8 tier = (u8)(stage_index / 4);
    u8 adaptive_pressure = campaign_adaptive_pressure(stage_index);
    u8 directive;
    u8 density_score;
    u8 sightline_score;
    u8 lane_pressure;
    gs.campaign_stage = stage_index;
    gs.campaign_active = 1;
    gs.stage_theme = design->theme & 0x03;
    gs.stage_wave_goal = (u8)(design->wave_goal + tier + (adaptive_pressure > 1));
    if (gs.stage_wave_goal > 5) gs.stage_wave_goal = 5;
    gs.stage_wave_size = (u8)(design->wave_size + (adaptive_pressure > 2));
    if (gs.stage_wave_size > MINION_MAX) gs.stage_wave_size = MINION_MAX;
    gs.stage_minion_hp = (u8)(design->minion_hp + tier + (adaptive_pressure > 1));
    gs.stage_minion_speed = (u8)(design->minion_speed + ((stage_index >= 8) ? 1 : 0) + (adaptive_pressure > 2));
    if (gs.stage_minion_speed > 3) gs.stage_minion_speed = 3;
    gs.stage_boss_hp_p1 = (u8)(BOSS_HP_P1 + (stage_index / 2) + adaptive_pressure + design->phase_hp_bonus[0]);
    gs.stage_boss_hp_p2 = (u8)(BOSS_HP_P2 + (stage_index / 2) + adaptive_pressure + design->phase_hp_bonus[1]);
    gs.stage_boss_hp_p3 = (u8)(BOSS_HP_P3 + (stage_index / 3) + adaptive_pressure + design->phase_hp_bonus[2]);
    gs.stage_boss_int_p1 = (u8)(BOSS_ATK_INTERVAL_P1 - stage_index * 2 - adaptive_pressure + ((tier == 0) ? 6 : 0) - design->interval_bias);
    gs.stage_boss_int_p2 = (u8)(BOSS_ATK_INTERVAL_P2 - stage_index * 2 - adaptive_pressure + ((tier == 0) ? 4 : 0) - design->interval_bias);
    gs.stage_boss_int_p3 = (u8)(BOSS_ATK_INTERVAL_P3 - stage_index - adaptive_pressure + ((tier == 0) ? 2 : 0) - design->interval_bias);
    if (gs.stage_boss_int_p1 < 50) gs.stage_boss_int_p1 = 50;
    if (gs.stage_boss_int_p2 < 42) gs.stage_boss_int_p2 = 42;
    if (gs.stage_boss_int_p3 < 36) gs.stage_boss_int_p3 = 36;
    gs.stage_boss_style = design->boss_style & 0x03;
    gs.stage_duel_mechanic = design->duel_mechanic & 0x03;
    gs.stage_bg_seed = (u8)(11 + stage_index * 7 + gs.run_serial * 5 + (gs.rei_form * 3) + adaptive_pressure * 9 + design->theme * 11 + design->boss_prefab * 3);
    density_score = stage_profile_density_score();
    sightline_score = stage_profile_sightline_score();
    lane_pressure = stage_profile_lane_pressure();
    if (density_score >= 6) {
        gs.stage_wave_size = (u8)(gs.stage_wave_size + 1);
        if (gs.stage_wave_size > MINION_MAX) gs.stage_wave_size = MINION_MAX;
        gs.stage_minion_hp = (u8)(gs.stage_minion_hp + 1);
    }
    if (sightline_score <= 3) {
        gs.stage_minion_speed = (u8)(gs.stage_minion_speed + 1);
        if (gs.stage_minion_speed > 3) gs.stage_minion_speed = 3;
        if (gs.stage_boss_int_p1 > 3) gs.stage_boss_int_p1 -= 3;
        if (gs.stage_boss_int_p2 > 2) gs.stage_boss_int_p2 -= 2;
    } else if (sightline_score >= 7) {
        gs.stage_boss_hp_p2 = (u8)(gs.stage_boss_hp_p2 + 1);
        gs.stage_boss_hp_p3 = (u8)(gs.stage_boss_hp_p3 + 1);
    }
    if (lane_pressure >= 7) {
        gs.stage_wave_goal = (u8)(gs.stage_wave_goal + 1);
        if (gs.stage_wave_goal > 5) gs.stage_wave_goal = 5;
        if (gs.stage_boss_int_p1 > 4) gs.stage_boss_int_p1 -= 4;
        if (gs.stage_boss_int_p2 > 3) gs.stage_boss_int_p2 -= 3;
    }
    if (design->weather_bias >= 4) {
        gs.stage_boss_style = (u8)((gs.stage_boss_style + 1) & 0x03);
    }
    if (design->route_bias >= 4) {
        gs.stage_duel_mechanic = (u8)((gs.stage_duel_mechanic + 1) & 0x03);
    }
    directive = stage_ai_directive();
    if (directive == 0) {
        gs.stage_wave_goal = (u8)(gs.stage_wave_goal + 1);
        if (gs.stage_wave_goal > 5) gs.stage_wave_goal = 5;
        if (gs.stage_boss_int_p1 > 6) gs.stage_boss_int_p1 -= 6;
        if (gs.stage_boss_int_p2 > 4) gs.stage_boss_int_p2 -= 4;
    } else if (directive == 1) {
        gs.stage_wave_size = (u8)(gs.stage_wave_size + 1);
        if (gs.stage_wave_size > MINION_MAX) gs.stage_wave_size = MINION_MAX;
    } else if (directive == 2) {
        gs.stage_minion_speed = (u8)(gs.stage_minion_speed + 1);
        if (gs.stage_minion_speed > 3) gs.stage_minion_speed = 3;
        gs.stage_boss_style = (u8)((gs.stage_boss_style + 1) & 0x03);
    } else if (directive == 3) {
        gs.stage_minion_hp = (u8)(gs.stage_minion_hp + 1);
        gs.stage_boss_hp_p2 = (u8)(gs.stage_boss_hp_p2 + 1);
        gs.stage_boss_hp_p3 = (u8)(gs.stage_boss_hp_p3 + 2);
    } else {
        gs.stage_wave_goal = (u8)(gs.stage_wave_goal + ((gs.run_serial & 0x01) != 0));
        if (gs.stage_wave_goal > 5) gs.stage_wave_goal = 5;
        gs.stage_wave_size = (u8)(gs.stage_wave_size + ((gs.run_entropy >> 5) & 0x01));
        if (gs.stage_wave_size > MINION_MAX) gs.stage_wave_size = MINION_MAX;
        if (gs.stage_boss_int_p3 > 3) gs.stage_boss_int_p3 -= 3;
    }
    stage_build_environment();
    stage_prepare_spawn_protocol();
}

static void campaign_start_from_title(void) {
    gs.run_serial++;
    gs.run_entropy = (u8)(gs.run_entropy + 37 + gs.run_serial * 11 + gs.rei_growth_points);
    gs.cleared_bosses = 0;
    gs.cyphers = 0;
    campaign_generate_stage(0);
}

static u8 stage_object_covers_tile(u8 skip_index, u8 layer, s16 col, s16 row) {
    for (u8 i = 0; i < gs.stage_object_count; ++i) {
        if (i == skip_index) continue;
        if (!gs.stage_objects[i].active || gs.stage_objects[i].layer != layer) continue;
        if (col < gs.stage_objects[i].tx || row < gs.stage_objects[i].ty) continue;
        if (col >= (s16)(gs.stage_objects[i].tx + gs.stage_objects[i].w)) continue;
        if (row >= (s16)(gs.stage_objects[i].ty + gs.stage_objects[i].h)) continue;
        return 1;
    }
    return 0;
}

static u8 stage_object_tile_at(u8 col, u8 row, u8 layer, u8 base_tile) {
    for (u8 i = 0; i < gs.stage_object_count; ++i) {
        const EnvPrefab *prefab;
        u8 exposed_left;
        u8 exposed_right;
        u8 exposed_up;
        u8 exposed_down;
        u8 lx;
        u8 ly;
        if (!gs.stage_objects[i].active || gs.stage_objects[i].layer != layer) continue;
        if (col < gs.stage_objects[i].tx || row < gs.stage_objects[i].ty) continue;
        lx = (u8)(col - gs.stage_objects[i].tx);
        ly = (u8)(row - gs.stage_objects[i].ty);
        if (lx >= gs.stage_objects[i].w || ly >= gs.stage_objects[i].h) continue;
        prefab = &env_prefab_db[gs.stage_objects[i].prefab];
        exposed_left = (u8)(lx == 0 && !stage_object_covers_tile(i, layer, (s16)col - 1, row));
        exposed_right = (u8)(lx + 1 == gs.stage_objects[i].w && !stage_object_covers_tile(i, layer, (s16)col + 1, row));
        exposed_up = (u8)(ly == 0 && !stage_object_covers_tile(i, layer, col, (s16)row - 1));
        exposed_down = (u8)(ly + 1 == gs.stage_objects[i].h && !stage_object_covers_tile(i, layer, col, (s16)row + 1));
        if (layer == 2) {
            if (exposed_up || exposed_left || exposed_right) return prefab->accent_tile;
            if (exposed_down && ((gs.anim_tick + lx + gs.stage_objects[i].genome.ferocity) & 0x01) == 0) return prefab->accent_tile;
            if (((lx + gs.stage_objects[i].genome.mobility + (gs.anim_tick >> (2 + (gs.stage_objects[i].status & 0x01)))) & 0x01) == 0) return prefab->fore_tile;
            return prefab->accent_tile;
        }
        if (exposed_up) return prefab->back_tile;
        if (exposed_left || exposed_right) return prefab->accent_tile;
        if ((gs.stage_objects[i].status & 0x02) != 0 && ly + 1 == gs.stage_objects[i].h && ((gs.anim_tick + lx + gs.stage_objects[i].genome.ferocity) & 0x03) == 0)
            return prefab->accent_tile;
        if (exposed_down && ((lx + gs.stage_objects[i].genome.shell) & 0x01) == 0) return prefab->mid_tile;
        if (ly == 0) return prefab->back_tile;
        if (lx == 0 || lx + 1 == gs.stage_objects[i].w) {
            if ((gs.stage_objects[i].status & 0x01) != 0 && ((gs.anim_tick + ly) & 0x01) == 0) return prefab->mid_tile;
            return prefab->accent_tile;
        }
        if ((gs.stage_objects[i].status & 0x01) != 0 && ((lx + ly + gs.stage_objects[i].genome.shell) & 0x01) == 0) return prefab->mid_tile;
        return base_tile;
    }
    return base_tile;
}

static u8 stage_column_blocked(u8 tile_col) {
    for (u8 i = 0; i < gs.stage_object_count; ++i) {
        if (!gs.stage_objects[i].active || gs.stage_objects[i].layer != 2) continue;
        if (tile_col < gs.stage_objects[i].tx || tile_col >= gs.stage_objects[i].tx + gs.stage_objects[i].w) continue;
        if (gs.stage_objects[i].ty >= 14 && env_prefab_db[gs.stage_objects[i].prefab].solid) return 1;
    }
    return 0;
}

static void boss_init(void);

/* Draw the harbour beach background:
 *   rows 0–10 : sky (alternating SKY_A / SKY_B checkerboard)
 *   rows 11–13: water (animated)
 *   rows 14–15: ground strip
 *   rows 16–17: ground with cliff edge
 *   Also draws the water animation based on gs.anim_tick              */
static void bg_draw_beach_rows(u8 row_start, u8 row_end) {
    const CampaignStageDesign *design = campaign_stage_design(gs.campaign_stage);
    const EnvThemeSubclass *profile = stage_theme_profile();
    s8 bg_x = gs.camera_bg_x;
    u8 subclass = stage_theme_subclass();
    u8 water_tile = ((gs.anim_tick >> 3) & 1) ? TILE_WATER_A : TILE_WATER_B;
    u8 density_score = stage_profile_density_score();
    u8 sightline_score = stage_profile_sightline_score();
    u8 current_bias = stage_profile_current_bias();
    u8 water_start = (u8)(7 + ((gs.stage_bg_seed + profile->water_rows + design->weather_bias) % 5));
    u8 ground_split = (u8)(4 + ((gs.stage_bg_seed + profile->split_bias * 3 + design->route_bias * 2 + current_bias) % 11));
    u8 ridge_line = (u8)(water_start + profile->water_rows + 1 + (density_score > 6));
    if (row_end > BKG_ROWS) row_end = BKG_ROWS;
    for (u8 row = row_start; row < row_end; ++row) {
        for (u8 col = 0; col < BKG_COLS; ++col) {
            u8 t = TILE_BLANK;
            switch (gs.stage_theme) {
                case 0:
                    if (row < water_start - (u8)(subclass == 1)) t = ((row + col + profile->sky_stride + (bg_x != 0) + (sightline_score > 6)) % 2) ? TILE_SKY_A : TILE_SKY_B;
                    else if (row < water_start + profile->water_rows) t = (((col + subclass + current_bias) % (2 + (profile->ridge_bias & 0x01) + (density_score > 6))) == 0) ? water_tile : TILE_WATER_B;
                    else if (row < ridge_line) t = ((subclass == 3 && (col & 0x01) == 0) || (col < ground_split)) ? TILE_GROUND_L : TILE_GROUND_R;
                    else t = (((col + profile->ridge_bias + subclass) & 0x01) == 0) ? TILE_CLIFF_A : TILE_CLIFF_B;
                    break;
                case 1:
                    if (row < water_start - 1) t = ((row + col + gs.stage_bg_seed + profile->sky_stride + design->weather_bias) & 1) ? TILE_SKY_B : TILE_SKY_A;
                    else if (row < water_start + (u8)(1 + (subclass == 4))) t = (((col + subclass) & 0x01) == 0) ? TILE_CLIFF_B : TILE_CLIFF_A;
                    else if (row < ridge_line + 1) t = (((row + col + subclass + current_bias) & 1) != 0 || col > ground_split) ? TILE_GROUND_R : TILE_CLIFF_A;
                    else t = ((col + profile->split_bias) < ground_split + 3) ? TILE_CLIFF_A : TILE_GROUND_L;
                    break;
                case 2:
                    if (row < water_start - 2) t = ((row + col + profile->sky_stride + (bg_x != 0) + design->weather_bias) % 2) ? TILE_SKY_A : TILE_SKY_B;
                    else if (row < water_start) t = (((col + subclass) & 1) != 0) ? TILE_WATER_A : TILE_WATER_B;
                    else if (row < water_start + profile->water_rows) t = ((col + gs.stage_bg_seed + subclass + current_bias) % 3 == 0) ? water_tile : TILE_GROUND_L;
                    else if (row < ridge_line + 1) t = ((subclass == 2 && col > ground_split - 2) || col < ground_split) ? TILE_GROUND_R : TILE_CLIFF_B;
                    else t = (((row + col + profile->ridge_bias + (density_score > 5)) & 1) != 0) ? TILE_CLIFF_A : TILE_CLIFF_B;
                    break;
                default:
                    if (row < water_start - 1) t = ((row + col + gs.stage_bg_seed + profile->sky_stride + design->weather_bias) & 1) ? TILE_SKY_B : TILE_SKY_A;
                    else if (row < water_start + (u8)(1 + (profile->ridge_bias & 0x01))) t = (((col + row + subclass) & 1) != 0) ? TILE_CLIFF_A : TILE_CLIFF_B;
                    else if (row < ridge_line + (u8)(1 + (subclass == 0))) t = ((col + profile->split_bias + sightline_score) < ground_split + (subclass == 4 ? 2 : 0)) ? TILE_GROUND_L : TILE_GROUND_R;
                    else t = (((col + gs.stage_bg_seed + subclass) & 1) != 0) ? water_tile : TILE_CLIFF_B;
                    break;
            }
            t = stage_object_tile_at(col, row, 0, t);
            t = stage_object_tile_at(col, row, 1, t);
            t = stage_object_tile_at(col, row, 2, t);
            plat_set_bkg_tile(col, row, t);
        }
    }
}

static void bg_draw_beach(void) {
    bg_draw_beach_rows(0, BKG_ROWS);
}

static void bg_draw_beach_water_only(void) {
    u8 water_start = (gs.camera_bg_y <= -1) ? 10 : (gs.camera_bg_y >= 1) ? 12 : 11;
    bg_draw_beach_rows(water_start, (u8)(water_start + 3));
}

/* Draw the drIpTECH splash — 4×2 tile logo centred on screen, row 6–7, cols 8–11 */
static void bg_draw_splash(void) {
    u8 saved_theme = gs.stage_theme;
    u8 saved_seed = gs.stage_bg_seed;
    gs.stage_theme = (u8)((gs.run_serial + 1) & 0x03);
    gs.stage_bg_seed = (u8)(17 + gs.run_serial * 3 + gs.anim_tick);
    bg_draw_beach();
    gs.stage_theme = saved_theme;
    gs.stage_bg_seed = saved_seed;
    bg_fill_rect(4, 4, 12, 8, TILE_BLANK);
    /* Logo tiles 9-16 arranged in a 4×2 grid */
    u8 start_tile = TILE_SPLASH1;
    for (u8 row = 0; row < 2; ++row)
        for (u8 col = 0; col < 4; ++col)
            plat_set_bkg_tile(8 + col, 6 + row, start_tile + row * 4 + col);
    /* Sub-subtitle row */
    plat_set_bkg_tile(7, 10, TILE_FONT_A + 5);   /* f */
    plat_set_bkg_tile(8, 10, TILE_FONT_A + 0);   /* a */
    plat_set_bkg_tile(9, 10, TILE_FONT_A + 13);  /* n */
}

/* Draw the "KAIJU GAIDEN!? GB." title logo centred — 3 cols × 4 rows */
static void bg_draw_title(void) {
    u8 saved_theme = gs.stage_theme;
    u8 saved_seed = gs.stage_bg_seed;
    gs.stage_theme = (u8)((gs.run_serial + gs.rei_form + narrative_dominant_moral_index()) & 0x03);
    gs.stage_bg_seed = (u8)(19 + gs.run_serial * 5 + gs.rei_persona * 7 + gs.anim_tick);
    bg_draw_beach();
    gs.stage_theme = saved_theme;
    gs.stage_bg_seed = saved_seed;
    bg_fill_rect(0, 1, BKG_COLS, 15, TILE_BLANK);
    bg_draw_rule(0, 1, BKG_COLS, TILE_WATER_A, TILE_WATER_B);
    bg_draw_rule(0, 12, BKG_COLS, TILE_GROUND_L, TILE_GROUND_R);
    bg_draw_panel(5, 2, 10, 6, TILE_BLANK, TILE_CLIFF_A, TILE_CLIFF_B);
    bg_draw_panel(3, 8, 14, 4, TILE_BLANK, TILE_GROUND_L, TILE_GROUND_R);
    /* Title tiles 17–28 as 3×4 arrangement starting at col 8, row 3 */
    u8 start = TILE_TITLE_A;
    for (u8 row = 0; row < 4; ++row)
        for (u8 col = 0; col < 3; ++col)
            plat_set_bkg_tile(8 + col, 3 + row, start + row * 3 + col);
    bg_draw_text_centered(9, "START GAME");
    bg_draw_text_centered(10, "PASSWORD");
    if ((gs.phase_timer & 0x10) == 0) bg_draw_text_centered(11, "PRESS START");
    plat_set_bkg_tile(4, 9 + gs.menu_sel, ((gs.phase_timer >> 3) & 0x01) ? TILE_WATER_A : TILE_CLIFF_A);
    plat_set_bkg_tile(15, 9 + gs.menu_sel, ((gs.phase_timer >> 3) & 0x01) ? TILE_WATER_A : TILE_CLIFF_B);
}

/* Draw a 2-digit score at tile position (tx, ty) */
static void bg_draw_number_2(u8 tx, u8 ty, u8 val) {
    plat_set_bkg_tile(tx,   ty, TILE_FONT_0 + (val / 10) % 10);
    plat_set_bkg_tile(tx+1, ty, TILE_FONT_0 + val % 10);
}

static void bg_clear_row(u8 y) {
    for (u8 x = 0; x < BKG_COLS; ++x)
        plat_set_bkg_tile(x, y, TILE_BLANK);
}

static u8 combat_minions_alive(void) {
    u8 count = 0;
    for (u8 i = 0; i < MINION_MAX; ++i)
        if (gs.minions[i].active) count++;
    return count;
}

static u8 combat_pending_spawns(void) {
    u8 count = 0;
    for (u8 i = 0; i < gs.stage_spawn_count; ++i)
        if (gs.spawn_slots[i].active) count++;
    return count;
}

static u8 attack_hits_target(s16 player_center, u8 facing_left, s16 target_center, u8 forward_range, u8 rear_range) {
    s16 delta = target_center - player_center;
    if (facing_left) delta = -delta;
    if (delta >= 0) return delta <= forward_range;
    return (-delta) <= rear_range;
}

static u8 abs_distance_u8(s16 a, s16 b) {
    s16 d = a - b;
    if (d < 0) d = -d;
    return (u8)d;
}

static s8 clamp_s8(s16 value, s8 min_value, s8 max_value) {
    if (value < min_value) return min_value;
    if (value > max_value) return max_value;
    return (s8)value;
}

static void combat_set_banner(u8 kind, u8 timer) {
    gs.banner_kind = kind;
    gs.banner_timer = timer;
    plat_audio_event(AUDIO_EVENT_BANNER, kind);
}

static void input_capture_frame(void) {
    u16 edge_mask;
    gs.input_held_mask = plat_input_mask();
    gs.input_pressed_mask = plat_pressed_mask();
    if (gs.input_pressed_mask & BTN_A) gs.input_attack_edges++;
    if (gs.input_pressed_mask & BTN_B) gs.input_dodge_edges++;
    if (gs.input_pressed_mask & BTN_SELECT) gs.input_nanocell_edges++;
    edge_mask = gs.input_pressed_mask;
    if (gs.input_held_mask != 0) gs.input_active_frames++;
    while (edge_mask != 0) {
        gs.input_edge_total++;
        edge_mask &= (u16)(edge_mask - 1);
    }
}

#ifdef TARGET_HOST
static void host_autoplay_init(void) {
    const char *enabled = getenv("KAIJU_AUTOPLAY");
    const char *limit = getenv("KAIJU_AUTOPLAY_STAGE_LIMIT");
    host_autoplay_enabled = (u8)(enabled && enabled[0] != '\0' && enabled[0] != '0');
    host_autoplay_stage_limit = 0;
    host_autoplay_stages_cleared = 0;
    host_autoplay_hold_mask = 0;
    host_autoplay_hold_frames = 0;
    host_autoplay_last_phase = 0xFF;
    if (limit && limit[0] != '\0') {
        int parsed = atoi(limit);
        if (parsed > 0) host_autoplay_stage_limit = (u8)parsed;
    }
}

static u8 host_autoplay_press(u8 mask, u8 frames) {
    host_autoplay_hold_mask = mask;
    host_autoplay_hold_frames = (frames == 0) ? 1 : frames;
    return mask;
}

static s16 host_autoplay_target_center(void) {
    s16 player_px = (s16)(gs.player_x * TILE_W + 8);
    s16 best_target = gs.boss_awake ? (s16)(gs.boss_x + 16) : player_px;
    s16 best_distance = 32000;
    for (u8 i = 0; i < MINION_MAX; ++i) {
        s16 target;
        s16 distance;
        if (!gs.minions[i].active) continue;
        target = (s16)(gs.minions[i].x + 8);
        distance = (s16)(target - player_px);
        if (distance < 0) distance = (s16)-distance;
        if (distance < best_distance) {
            best_distance = distance;
            best_target = target;
        }
    }
    return best_target;
}

static u8 host_autoplay_move_toward(s16 target_center) {
    s16 player_px = (s16)(gs.player_x * TILE_W + 8);
    if (target_center > player_px + 14 && gs.player_x < 17) return BTN_RIGHT;
    if (target_center < player_px - 14 && gs.player_x > 0) return BTN_LEFT;
    return 0;
}

static u8 host_autoplay_buttons(void) {
    if (!host_autoplay_enabled) return 0;
    if (gs.phase != host_autoplay_last_phase) {
        host_autoplay_last_phase = gs.phase;
        host_autoplay_hold_mask = 0;
        host_autoplay_hold_frames = 0;
    }
    if (host_autoplay_hold_frames > 0) {
        host_autoplay_hold_frames--;
        return host_autoplay_hold_mask;
    }

    switch (gs.phase) {
        case PHASE_SPLASH:
            if (gs.phase_timer > 18) return host_autoplay_press(BTN_START, 1);
            break;
        case PHASE_CINEMATIC:
            if (gs.phase_timer > 24) return host_autoplay_press(BTN_B, SKIP_HOLD_FRAMES + 2);
            break;
        case PHASE_TITLE:
            if (gs.menu_sel != 0) return host_autoplay_press(BTN_UP, 1);
            if (gs.phase_timer > 10) return host_autoplay_press(BTN_START, 1);
            break;
        case PHASE_PASSWORD:
            return host_autoplay_press(BTN_B, 1);
        case PHASE_NARRATIVE:
            if (gs.phase_timer > 28) return host_autoplay_press(BTN_B, 1);
            if (gs.narrative_page == 1) {
                u8 desired = (u8)((gs.campaign_stage + gs.run_serial + narrative_dominant_moral_index()) & 0x01);
                if (gs.moral_choice_cursor != desired) return host_autoplay_press(desired ? BTN_RIGHT : BTN_LEFT, 1);
            }
            if (gs.phase_timer > 18) return host_autoplay_press(BTN_A, 1);
            break;
        case PHASE_STAGE_INTRO:
            if (gs.duel_qte_ready && gs.duel_qte_result == 0) return host_autoplay_press(gs.duel_qte_button, 1);
            break;
        case PHASE_COMBAT:
            if (gs.player_hp <= 2 && gs.nanocell_count > 0 && gs.nanocell_boost_timer == 0)
                return host_autoplay_press(BTN_SELECT, 1);
            if (gs.boss_windup > 0 && gs.boss_threat >= 1 && gs.dodge_timer == 0 && gs.attack_timer == 0 && gs.hit_stun == 0)
                return host_autoplay_press(BTN_B, 1);
            if (gs.attack_timer == 0 && gs.dodge_timer == 0 && gs.hit_stun == 0) {
                s16 target_center = host_autoplay_target_center();
                u8 movement = host_autoplay_move_toward(target_center);
                if (movement != 0) return movement;
                return host_autoplay_press(BTN_A, 1);
            }
            break;
        case PHASE_CYPHER_DROP:
            if (gs.phase_timer > 24) return host_autoplay_press(BTN_A, 1);
            break;
        case PHASE_GAME_OVER:
            if (gs.phase_timer > GAMEOVER_HOLD_FRAMES + 2) return host_autoplay_press(BTN_A, 1);
            break;
        default:
            break;
    }
    return 0;
}
#endif

static void camera_reset(void) {
    gs.camera_x = 0;
    gs.camera_y = 0;
    gs.camera_travel_bias = 0;
    gs.camera_bg_x = 0;
    gs.camera_bg_y = 0;
    gs.camera_shake_timer = 0;
    gs.camera_shake_mag = 0;
}

static void camera_punch(u8 magnitude, u8 timer) {
    if (magnitude > gs.camera_shake_mag) gs.camera_shake_mag = magnitude;
    if (timer > gs.camera_shake_timer) gs.camera_shake_timer = timer;
}

static s8 camera_shake_x(void) {
    if (gs.camera_shake_timer == 0 || gs.camera_shake_mag == 0) return 0;
    return (gs.anim_tick & 0x01) ? (s8)gs.camera_shake_mag : (s8)(-(s8)gs.camera_shake_mag);
}

static s8 camera_shake_y(void) {
    if (gs.camera_shake_timer == 0 || gs.camera_shake_mag == 0) return 0;
    return (gs.anim_tick & 0x02) ? (s8)(gs.camera_shake_mag >> 1) : 0;
}

static s16 camera_apply_x(s16 x) {
    return x - gs.camera_x + camera_shake_x();
}

static s16 camera_apply_y(s16 y) {
    return y - gs.camera_y + camera_shake_y();
}

static u8 combat_camera_update(void) {
    s8 prev_bg_x = gs.camera_bg_x;
    s8 prev_bg_y = gs.camera_bg_y;
    s16 player_px = (s16)(gs.player_x * TILE_W + 8);
    s16 target_x = (player_px - (SCR_W / 2)) / 6;
    s16 target_y = 0;

    if ((gs.input_held_mask & BTN_LEFT) && !(gs.input_held_mask & BTN_RIGHT)) {
        if (gs.camera_travel_bias > -CAMERA_TRAVEL_LEAD) gs.camera_travel_bias--;
    } else if ((gs.input_held_mask & BTN_RIGHT) && !(gs.input_held_mask & BTN_LEFT)) {
        if (gs.camera_travel_bias < CAMERA_TRAVEL_LEAD) gs.camera_travel_bias++;
    } else if (gs.camera_travel_bias > 0) {
        gs.camera_travel_bias--;
    } else if (gs.camera_travel_bias < 0) {
        gs.camera_travel_bias++;
    }

    target_x += gs.camera_travel_bias;

    if (gs.boss_awake) {
        s16 boss_center = gs.boss_x + 16;
        s16 duel_mid = (player_px + boss_center) / 2;
        s16 duel_bias = clamp_s8((boss_center - player_px) / 18, -CAMERA_COMBAT_LEAD, CAMERA_COMBAT_LEAD);
        target_x = (target_x * 2 + ((duel_mid - (SCR_W / 2)) / 7) + duel_bias) / 3;
        if (gs.boss_windup > 0) {
            s16 telegraph_bias = clamp_s8((boss_center - player_px) / 12, -CAMERA_TELEGRAPH_LEAD, CAMERA_TELEGRAPH_LEAD);
            target_x = (target_x * 2 + telegraph_bias * 3) / 5;
            target_y = (gs.boss_atk_type == BOSS_ATK_SLAM) ? 2 : 1;
        } else if (attack_hits_target(player_px, gs.player_facing, boss_center, PLAYER_ATTACK_FRONT + 8, PLAYER_ATTACK_REAR)) {
            target_x += gs.player_facing ? -1 : 1;
            target_y = -1;
        } else if (gs.combo_timer > 0) {
            target_x += (boss_center > player_px) ? 1 : -1;
        }
    }

    if (gs.dodge_timer > 0) {
        target_x += gs.player_facing ? -2 : 2;
        target_y = -1;
    } else if (gs.attack_timer > 0) {
        target_x += gs.player_facing ? -1 : 1;
        target_y = -1;
    } else if (gs.hit_stun > 0) {
        target_y = 1;
    }

    target_x = clamp_s8(target_x, -CAMERA_MAX_X, CAMERA_MAX_X);
    target_y = clamp_s8(target_y, -2, CAMERA_MAX_Y);

    if (gs.camera_x < target_x) gs.camera_x++;
    else if (gs.camera_x > target_x) gs.camera_x--;
    if (gs.camera_y < target_y) gs.camera_y++;
    else if (gs.camera_y > target_y) gs.camera_y--;

    if (gs.camera_shake_timer > 0) gs.camera_shake_timer--;
    else gs.camera_shake_mag = 0;

    gs.camera_bg_x = clamp_s8(gs.camera_x / 4, -1, 1);
    gs.camera_bg_y = clamp_s8(gs.camera_y / 2, -1, 1);
    return (u8)((prev_bg_x != gs.camera_bg_x) || (prev_bg_y != gs.camera_bg_y));
}

static const char *boss_attack_label(u8 type) {
    switch (type) {
        case BOSS_ATK_SWEEP: return "SWEEP";
        case BOSS_ATK_SPIT:  return "SPIT";
        case BOSS_ATK_SLAM:  return "SLAM";
        case BOSS_ATK_TIDAL: return "TIDAL";
        default:             return "DUEL";
    }
}

static u8 boss_attack_threat(u8 type, u8 distance) {
    u8 attack_range;
    switch (type) {
        case BOSS_ATK_SWEEP: attack_range = BOSS_SWEEP_RANGE; break;
        case BOSS_ATK_SPIT:  attack_range = BOSS_SPIT_RANGE; break;
        case BOSS_ATK_SLAM:  attack_range = BOSS_SLAM_RANGE; break;
        case BOSS_ATK_TIDAL: attack_range = BOSS_SPIT_RANGE; break;
        default:             attack_range = BOSS_SWEEP_RANGE; break;
    }
    if (distance > attack_range + 10) return 0;
    if (distance > attack_range) return 1;
    return 2;
}

static u8 boss_attack_windup_frames(u8 type) {
    switch (type) {
        case BOSS_ATK_SWEEP: return 16;
        case BOSS_ATK_SPIT:  return 22;
        case BOSS_ATK_SLAM:  return 26;
        case BOSS_ATK_TIDAL: return 18;
        default:             return 16;
    }
}

static u8 boss_attack_recover_frames(u8 type) {
    switch (type) {
        case BOSS_ATK_SWEEP: return 18;
        case BOSS_ATK_SPIT:  return 14;
        case BOSS_ATK_SLAM:  return 24;
        case BOSS_ATK_TIDAL: return 20;
        default:             return 16;
    }
}

static u8 boss_current_range(u8 type) {
    switch (type) {
        case BOSS_ATK_SWEEP: return BOSS_SWEEP_RANGE;
        case BOSS_ATK_SPIT:  return BOSS_SPIT_RANGE;
        case BOSS_ATK_SLAM:  return BOSS_SLAM_RANGE;
        case BOSS_ATK_TIDAL: return BOSS_SPIT_RANGE;
        default:             return BOSS_SWEEP_RANGE;
    }
}

static u8 boss_pick_attack(void) {
    u8 distance = abs_distance_u8(gs.boss_x, (s16)(gs.player_x * TILE_W));
    u8 directive = stage_ai_directive();
    u8 noise = stage_mix8((u8)(distance + gs.boss_phase * 9 + gs.boss_anim), (u8)(201 + gs.boss_prefab * 5 + gs.boss_subarchetype * 3));
    switch (directive) {
        case 0:
            if (distance <= 20 || (noise & 0x03) == 0) return BOSS_ATK_SLAM;
            if (distance > 60) return (gs.boss_phase >= 2) ? BOSS_ATK_TIDAL : BOSS_ATK_SPIT;
            return ((noise & 0x01) == 0) ? BOSS_ATK_SWEEP : BOSS_ATK_SLAM;
        case 1:
            if (gs.boss_phase >= 3 && distance > 20) return ((noise & 0x01) == 0) ? BOSS_ATK_TIDAL : BOSS_ATK_SPIT;
            if (distance > 30) return BOSS_ATK_SPIT;
            return ((noise & 0x01) != 0) ? BOSS_ATK_SWEEP : BOSS_ATK_SLAM;
        case 2:
            if (gs.boss_phase >= 2 && (noise & 0x07) < 2 && distance > 24) return BOSS_ATK_TIDAL;
            if (gs.boss_atk_type == BOSS_ATK_SWEEP && distance > 34) return BOSS_ATK_SPIT;
            if (gs.boss_atk_type == BOSS_ATK_SPIT && distance <= 28) return BOSS_ATK_SLAM;
            if (gs.boss_atk_type == BOSS_ATK_SLAM && distance > 38) return BOSS_ATK_SWEEP;
            return (u8)((gs.boss_atk_type + 1 + (noise & 0x01)) & 0x03);
        case 3:
            if (gs.boss_phase >= 2 && distance > 18) return BOSS_ATK_TIDAL;
            if (distance > 42) return BOSS_ATK_SPIT;
            return BOSS_ATK_SWEEP;
        default:
            if (gs.boss_phase >= 2 && (noise & 0x03) == 0) return BOSS_ATK_TIDAL;
            if (distance <= 24) return ((noise & 0x01) == 0) ? BOSS_ATK_SLAM : BOSS_ATK_SWEEP;
            return ((noise & 0x02) != 0) ? BOSS_ATK_SPIT : BOSS_ATK_SWEEP;
    }
    switch (gs.stage_boss_style) {
        case 1:
            if (distance > 38 || (gs.anim_tick & 0x08) != 0) return BOSS_ATK_SPIT;
            if (gs.boss_phase >= 3 && (gs.anim_tick & 0x10) == 0) return BOSS_ATK_TIDAL;
            return (distance <= 22) ? BOSS_ATK_SLAM : BOSS_ATK_SWEEP;
        case 2:
            if (distance <= 26) return BOSS_ATK_SLAM;
            return (gs.boss_phase >= 2) ? BOSS_ATK_SWEEP : BOSS_ATK_SPIT;
        case 3:
            if ((gs.anim_tick % 80) < 12) return BOSS_ATK_TIDAL;
            if (distance <= 24) return BOSS_ATK_SLAM;
            return ((gs.anim_tick & 0x10) != 0) ? BOSS_ATK_SPIT : BOSS_ATK_SWEEP;
        default:
            break;
    }
    if (gs.boss_phase == 1) {
        return (distance <= 34) ? BOSS_ATK_SWEEP : BOSS_ATK_SPIT;
    }
    if (gs.boss_phase == 2) {
        if (distance <= 22) return BOSS_ATK_SLAM;
        return ((gs.anim_tick & 0x10) != 0) ? BOSS_ATK_SPIT : BOSS_ATK_SWEEP;
    }
    if ((gs.anim_tick % 96) < 12 && distance > 18) return BOSS_ATK_TIDAL;
    if (distance <= 24) return BOSS_ATK_SLAM;
    return (distance > 54) ? BOSS_ATK_TIDAL : BOSS_ATK_SWEEP;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: HUD RENDERER
 * player HP  │ NanoCells │ BOSS HP segments
 * ═══════════════════════════════════════════════════════════════════════════ */

static void hud_draw(void) {
    u8 adaptive_pressure = campaign_adaptive_pressure(gs.campaign_stage);
    u8 boss_distance = 0;
    if (gs.boss_awake) {
        boss_distance = abs_distance_u8(gs.boss_x, (s16)(gs.player_x * TILE_W));
        gs.boss_threat = boss_attack_threat(gs.boss_atk_type, boss_distance);
    } else {
        gs.boss_threat = 0;
    }

    for (u8 i = 0; i < BKG_COLS; ++i)
        plat_set_bkg_tile(i, HUD_ROW, (i & 1) ? TILE_GROUND_L : TILE_GROUND_R);
    plat_set_bkg_tile(6, HUD_ROW, TILE_CLIFF_A);
    plat_set_bkg_tile(9, HUD_ROW, TILE_CLIFF_B);
    plat_set_bkg_tile(12, HUD_ROW, TILE_CLIFF_A);
    bg_draw_text(7, HUD_ROW, "NC");
    bg_draw_text(13, HUD_ROW, "B");

    /* Player HP: filled HP-segment tiles in row 0, cols 0–5 */
    for (u8 i = 0; i < PLAYER_MAX_HP; ++i)
        plat_set_bkg_tile(i, HUD_ROW, (i < gs.player_hp) ? TILE_HP_SEG : TILE_BLANK);

    /* NanoCell count — digit at col 10–11 */
    bg_draw_number_2(10, HUD_ROW, gs.nanocell_count);

    /* Boss HP: 6-segment bar at row 0, cols 14–19 (when in active duel) */
    if (gs.phase == PHASE_COMBAT && gs.boss_awake) {
        u8 boss_max = (gs.boss_phase == 1) ? gs.stage_boss_hp_p1
                    : (gs.boss_phase == 2) ? gs.stage_boss_hp_p2 : gs.stage_boss_hp_p3;
        u8 boss_bar_variant = 0;
        if (gs.boss_windup > 0) boss_bar_variant = (u8)(1 + ((gs.anim_tick >> 1) & 0x01));
        else if (gs.boss_stun > 0) boss_bar_variant = (u8)(4 + (gs.anim_tick & 0x01));
        else if (gs.boss_recover > 0) boss_bar_variant = 3;
        plat_load_bkg_tiles(tile_boss_hp_bar[boss_bar_variant], TILE_BOSS_SEG, 1);
        for (u8 i = 0; i < 6; ++i) {
            u8 filled = (u8)((u16)gs.boss_hp * 6 / boss_max);
            plat_set_bkg_tile(14 + i, HUD_ROW,
                              (i < filled) ? TILE_BOSS_SEG : TILE_BLANK);
        }
    } else {
        for (u8 i = 0; i < 6; ++i)
            plat_set_bkg_tile(14 + i, HUD_ROW, TILE_BLANK);
    }

    bg_clear_row(1);
    bg_clear_row(2);
    if (gs.phase == PHASE_COMBAT) {
        if (gs.banner_timer > 0) {
            switch (gs.banner_kind) {
                case BANNER_BOSS_RISE:  bg_draw_text(0, 1, "LEVIATHAN RISES"); break;
                case BANNER_WAVE_CLEAR: bg_draw_text(0, 1, "WAVE BROKEN"); break;
                case BANNER_DODGE:      bg_draw_text(0, 1, "DODGE CLEAN"); break;
                case BANNER_PERFECT:    bg_draw_text(0, 1, "PERFECT STRIKE"); break;
                case BANNER_FINISHER:   bg_draw_text(0, 1, "FINISHER WINDOW"); break;
                case BANNER_BOSS_STUN:  bg_draw_text(0, 1, "BOSS STUNNED"); break;
                case BANNER_SURGE:      bg_draw_text(0, 1, "NANOCELL SURGE"); break;
                case BANNER_FIRST:      bg_draw_text(0, 1, "FIRST STRIKE"); break;
                case BANNER_HAZARD:     bg_draw_text(0, 1, "STAGE HAZARD"); break;
                default:                bg_draw_text(0, 1, "DUEL LIVE"); break;
            }
            if (gs.banner_kind == BANNER_BOSS_STUN) bg_draw_text(0, 2, "A PRESS ADVANTAGE");
            else if (gs.banner_kind == BANNER_DODGE) bg_draw_text(0, 2, "A COUNTER NOW");
            else if (gs.banner_kind == BANNER_SURGE) bg_draw_text(0, 2, "A PRESS / B CUT IN");
            else if (gs.banner_kind == BANNER_FIRST) bg_draw_text(0, 2, "CENTER WON TAKE SPACE");
            else if (gs.banner_kind == BANNER_HAZARD) bg_draw_text(0, 2, stage_hazard_prompt());
            else bg_draw_text(0, 2, "KEEP CENTER LINE");
        } else if (gs.combo_timer > 0 || gs.dodge_read_total > 0) {
            bg_draw_text(0, 1, "FLOW READ TICK");
            bg_draw_text(0, 2, "TH");
            bg_draw_number_2(2, 2, gs.boss_threat);
            bg_draw_text(5, 2, "CB");
            bg_draw_number_2(7, 2, gs.combo_count);
            bg_draw_text(10, 2, "RD");
            bg_draw_number_2(12, 2, (u8)(gs.dodge_read_total % 100));
            bg_draw_text(15, 2, "AP");
            bg_draw_number_2(17, 2, adaptive_pressure);
        } else if (gs.duel_first_strike_timer > 0) {
            bg_draw_text(0, 1, "DUEL DROP");
            bg_draw_text(0, 2, "A CLAIM FIRST HIT");
        } else if (gs.boss_windup > 0) {
            bg_draw_text(0, 1, boss_attack_label(gs.boss_atk_type));
            if (gs.boss_threat >= 2) bg_draw_text(0, 2, "B DODGE NOW");
            else if (gs.boss_threat == 1) bg_draw_text(0, 2, "EDGE BAIT / STEP");
            else bg_draw_text(0, 2, "A PUNISH OPEN");
        } else if (gs.boss_stun > 0) {
            bg_draw_text(0, 1, "STUN");
            bg_draw_text(0, 2, "A PRESS ADVANTAGE");
        } else if (gs.dodge_timer > 0) {
            bg_draw_text(0, 1, "DODGE");
            bg_draw_text(0, 2, "A COUNTER WINDOW");
        } else if (gs.perfect_flash_timer > 0) {
            bg_draw_text(0, 1, "PERFECT");
            bg_draw_text(0, 2, "A CHAIN THE COMBO");
        } else if (gs.nanocell_boost_timer > 0) {
            bg_draw_text(0, 1, "POWER");
            bg_draw_number_2(6, 1, (u8)(gs.nanocell_boost_timer / 10));
            bg_draw_text(0, 2, "A PRESS / B CUT IN");
        } else {
            bg_draw_text(0, 1, "PHASE");
            plat_set_bkg_tile(6, 1, TILE_FONT_0 + gs.boss_phase);
            bg_draw_text(8, 1, "ADD");
            bg_draw_number_2(12, 1, combat_pending_spawns());
            bg_draw_text(14, 1, "F");
            bg_draw_number_2(15, 1, (u8)(gs.rei_form + 1));
            plat_set_bkg_tile(17, 1, TILE_FONT_0 + (gs.combo_count % 10));
            if (gs.player_hp <= 2) {
                bg_draw_text(0, 2, (gs.nanocell_count > 0) ? "LOW HP SEL SURGE" : "LOW HP BAIT CLEAN");
            } else if (attack_hits_target((s16)(gs.player_x * TILE_W + 8), gs.player_facing, (s16)(gs.boss_x + 16), PLAYER_ATTACK_FRONT + 4, PLAYER_ATTACK_REAR)) {
                bg_draw_text(0, 2, "A BOSS IN RANGE");
            } else if (combat_minions_alive() > 0) {
                bg_draw_text(0, 2, "CLEAR ADDS KEEP SPACE");
            } else if (gs.nanocell_count > 0 && boss_distance <= BOSS_SPIT_RANGE) {
                bg_draw_text(0, 2, "SET ANGLE / SEL SURGE");
            } else {
                switch ((gs.anim_tick >> 5) % 3) {
                    case 0:
                        bg_draw_text(0, 2, campaign_stage_hazard_line(gs.campaign_stage));
                        break;
                    case 1:
                        bg_draw_text(0, 2, campaign_stage_terrain_line(gs.campaign_stage));
                        break;
                    default:
                        bg_draw_text(0, 2, campaign_stage_pressure_line(gs.campaign_stage));
                        break;
                }
            }
        }
    }
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: SPRITE RENDERER
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Sprite IDs assigned to game objects:
 *   0–5   : Rei (6 tiles — 2×3 arrangement, each 8px)
 *   6–9   : active minion 0
 *   10–13 : active minion 1
 *   14–17 : active minion 2
 *   18–21 : active minion 3
 *   22–25 : active minion 4
 *   26–33 : Boss (8 tile arrangement — 4×2 at 8px each)
 *   34–35 : Hit FX
 *   36–37 : NanoCell FX
 */

/* Rei is drawn as 2 columns × 3 rows of 8×8 tiles.
 * Base tile set selected by animation state.                           */
static void spr_draw_rei(void) {
    u8 base_tile = SPR_REI_IDLE;
    s8 form_x = 0;
    s8 form_y = 0;
    s8 row_x_offset[3] = {0, 0, 0};
    s8 row_y_offset[3] = {0, 0, 0};
    s8 idle_pulse = 0;
    s8 idle_sway = 0;
    s8 run_phase = 0;
    if (gs.attack_timer > 0)       base_tile = SPR_REI_ATTACK;
    else if (gs.player_anim > 0)   base_tile = SPR_REI_RUN;

    if (gs.hit_stun > 0 && (gs.anim_tick & 0x02)) return;
    if (gs.dodge_timer > 0 && (gs.anim_tick & 0x01)) return;

    s16 bx = (s16)(gs.player_x * TILE_W);
    s16 by = (s16)(gs.player_y - 16);  /* anchor at feet */
    if (gs.attack_queued && gs.attack_timer <= ATTACK_ACTIVE_FRAME) {
        bx += gs.player_facing ? -2 : 2;
    }
    bx = camera_apply_x(bx);
    by = camera_apply_y(by);
    u8 flip = gs.player_facing ? 0x20 : 0x00;  /* flag bit 5 = X-flip */
    if ((gs.rei_cosmetic_mask & 0x0003u) != 0) form_x = (s8)((gs.rei_form % 3) - 1);
    if ((gs.rei_cosmetic_mask & 0x000Cu) != 0) form_y = (s8)(((gs.rei_form / 3) % 3) - 1);
    if ((gs.rei_cosmetic_mask & 0x0010u) != 0) flip ^= 0x20;
    if (gs.rei_persona >= 3) form_y--;
    if (gs.rei_form >= 8) form_x += 1;
    if (gs.rei_form >= 10 && (gs.anim_tick & 0x02)) form_y--;
    if (gs.rei_persona == 5 && gs.player_anim > 0) form_x += gs.player_facing ? -1 : 1;

    idle_pulse = (s8)((((gs.anim_tick >> 2) + gs.run_serial) & 0x03) - 1);
    idle_sway = (s8)((((gs.anim_tick >> 3) + gs.rei_persona) & 0x03) - 1);
    run_phase = (s8)(((gs.anim_tick >> 1) & 0x03) - 1);

    if (gs.attack_timer == 0 && gs.player_anim == 0 && gs.hit_stun == 0 && gs.dodge_timer == 0) {
        row_y_offset[0] = (s8)(-1 + (idle_pulse > 0 ? 0 : idle_pulse));
        row_y_offset[1] = (s8)(idle_pulse > 0 ? idle_pulse : 0);
        row_y_offset[2] = (s8)(1 + (idle_pulse > 0 ? idle_pulse : 0));
        row_x_offset[0] = (s8)(idle_sway + (gs.player_facing ? -1 : 1));
        row_x_offset[1] = (s8)(-idle_sway);
        row_x_offset[2] = (s8)(idle_sway / 2);
    } else if (gs.player_anim > 0) {
        row_y_offset[0] = (s8)(run_phase == -1 ? -1 : 0);
        row_y_offset[1] = (s8)(run_phase == 1 ? 1 : 0);
        row_y_offset[2] = (s8)(run_phase >= 0 ? 1 : 0);
        row_x_offset[0] = (s8)((gs.player_facing ? -1 : 1) * (1 + (run_phase > 0)));
        row_x_offset[1] = (s8)((gs.player_facing ? 1 : -1) * (run_phase < 0 ? 1 : 0));
        row_x_offset[2] = (s8)((gs.player_facing ? 1 : -1) * (1 + (run_phase < 0)));
    }
    if (gs.attack_timer > 0) {
        s8 lunge = (s8)((gs.attack_timer > ATTACK_ACTIVE_FRAME) ? 1 : 2);
        row_x_offset[0] += (gs.player_facing ? -1 : 1) * lunge;
        row_x_offset[1] += (gs.player_facing ? -1 : 1) * (lunge + 1);
        row_x_offset[2] += (gs.player_facing ? 1 : -1);
        row_y_offset[0] -= 1;
        row_y_offset[1] -= (gs.attack_timer > ATTACK_ACTIVE_FRAME) ? 1 : 0;
        row_y_offset[2] += 1;
    }
    if (gs.dodge_timer > 0) {
        row_x_offset[0] += gs.player_facing ? -1 : 1;
        row_x_offset[2] += gs.player_facing ? 1 : -1;
        row_y_offset[0] -= 1;
        row_y_offset[2] += 1;
    }

    /* 6 tiles: tile row 0 = head pair, row 1 = torso pair, row 2 = legs */
    for (u8 row = 0; row < 3; ++row) {
        u8 tile_l = (u8)(base_tile + row * 2 + (((gs.rei_cosmetic_mask >> row) & 0x01u) ? 0 : 0));
        u8 tile_r = (u8)(base_tile + row * 2 + 1 - (((gs.rei_cosmetic_mask >> (row + 4)) & 0x01u) ? 0 : 0));
        plat_set_sprite(row * 2,     bx + form_x + row_x_offset[row],           (u8)(by + row * 8 + form_y + row_y_offset[row]), tile_l, flip);
        plat_set_sprite(row * 2 + 1, bx + TILE_W + form_x + row_x_offset[row],  (u8)(by + row * 8 + form_y + row_y_offset[row]), tile_r, flip);
    }
}

/* Boss drawn as 4×2 grid of 8px tiles starting at logical pixel pos boss_x.
 * 8 sprite slots used (IDs 26–33).                                        */
static void spr_draw_boss(void) {
    if (gs.boss_phase == 0) return;
    u8 base_tile = (gs.boss_phase == 1) ? SPR_BOSS_A
                 : (gs.boss_phase == 2) ? SPR_BOSS_B : SPR_BOSS_C;
    s16 bx = gs.boss_x;
    s16 by = (s16)(SCR_H - 16 - 32);  /* boss stands near ground, two tile rows tall */
    s8 breath = 0;
    s8 spine_sway = 0;
    s8 tide_pull = 0;
    s8 jaw_drop = 0;
    if (!gs.boss_awake) {
        by += 4;
        if (gs.anim_tick & 0x04) return;
    } else if (gs.boss_windup > 0) {
        if (gs.boss_atk_type == BOSS_ATK_SLAM) by += 4;
        else if (gs.boss_atk_type == BOSS_ATK_SWEEP) bx += (gs.anim_tick & 0x02) ? -2 : 2;
        else by += (gs.anim_tick & 0x02) ? 1 : 0;
    } else if (gs.boss_recover > 0) {
        by -= 1;
    } else {
        by += (gs.anim_tick & 0x08) ? 1 : 0;
    }
    breath = (s8)((((gs.anim_tick >> 3) + gs.boss_phase) & 0x03) - 1);
    spine_sway = (s8)((((gs.anim_tick >> 2) + gs.boss_phase + gs.boss_subarchetype) & 0x03) - 1);
    tide_pull = (s8)((gs.boss_phase >= 2) ? ((((gs.anim_tick >> 4) + gs.stage_boss_style) & 0x01) ? 1 : -1) : 0);
    jaw_drop = (s8)((gs.boss_windup > 0 || gs.boss_phase >= 3) ? 1 : 0);
    bx = camera_apply_x(bx);
    by = camera_apply_y(by);
    u8 id_base = 26;
    for (u8 row = 0; row < 2; ++row)
        for (u8 col = 0; col < 4; ++col)
            {
            u8 slot = (u8)(row * 4 + col);
            s8 tile_breath = (s8)((row == 0) ? (-breath - jaw_drop) : (breath + jaw_drop));
            s8 tile_sway = (s8)((row == 0) ? (spine_sway * (s8)(col >= 2 ? 1 : -1)) : (spine_sway * (s8)(col < 2 ? -1 : 1)));
            tile_sway += (s8)(tide_pull * (s8)(col - 1));
            plat_set_sprite(id_base + row * 4 + col,
                            bx + col * TILE_W + boss_tile_offset_x(slot) + tile_sway,
                            (u8)(by + row * TILE_H + boss_tile_offset_y(slot) + tile_breath),
                            base_tile + boss_tile_index(slot), boss_tile_flags(slot));
            }
}

/* Minions — each is 2×2 tiles, 4 sprite slots each */
static void spr_draw_minions(void) {
    for (u8 i = 0; i < MINION_MAX; ++i) {
        u8 flags = 0;
        s8 head_bob = 0;
        s8 body_sway = 0;
        s8 claw_spread = 0;
        if (!gs.minions[i].active) continue;
        u8 id_base = 6 + i * 4;
        s16 mx = gs.minions[i].x;
        u8  my = gs.minions[i].y;
        if (gs.minions[i].attack_windup > 0) {
            mx += (gs.minions[i].vx >= 0) ? 1 : -1;
            if (my > 1) my -= 2;
        } else if (gs.minions[i].attack_recover > 0) {
            if (my < SCR_H - 18) my += 2;
        } else if (gs.minions[i].anim & 0x04) {
            if (my < SCR_H - 17) my += 1;
        }
        mx = camera_apply_x(mx);
        my = (u8)camera_apply_y(my);
        head_bob = (s8)((((gs.minions[i].anim >> 1) + i) & 0x03) - 1);
        body_sway = (s8)((((gs.minions[i].anim >> 2) + gs.minions[i].class_major) & 0x03) - 1);
        if (gs.minions[i].vx < 0) body_sway = (s8)-body_sway;
        claw_spread = (s8)((gs.minions[i].attack_windup > 0) ? 1 : (((gs.minions[i].anim >> 3) & 0x01) ? 1 : 0));
        if (((gs.minions[i].class_major + gs.minions[i].class_minor) & 0x01) != 0) flags ^= 0x20;
        plat_set_sprite(id_base+0, mx + body_sway - claw_spread, my - head_bob,           SPR_MINION+0 + (gs.minions[i].class_minor & 0x01), flags);
        plat_set_sprite(id_base+1, mx+TILE_W + body_sway + claw_spread, my - head_bob,     SPR_MINION+1, flags);
        plat_set_sprite(id_base+2, mx - body_sway - claw_spread, my+TILE_H + (head_bob > 0 ? 0 : 1), SPR_MINION+2, flags);
        plat_set_sprite(id_base+3, mx+TILE_W - body_sway + claw_spread, my+TILE_H + (head_bob > 0 ? 0 : 1), SPR_MINION+3 - (gs.minions[i].class_mid & 0x01), flags);
    }
}

static void spr_draw_narrative_portraits(void) {
    u8 rei_flip = (gs.rei_persona & 0x01) ? 0x20 : 0x00;
    u8 boss_base = (gs.boss_phase <= 1) ? SPR_BOSS_A : (gs.boss_phase == 2) ? SPR_BOSS_B : SPR_BOSS_C;
    s16 rei_bx = 8;
    s16 rei_by = 36;
    s16 boss_bx = 112;
    s16 boss_by = 24;
    for (u8 row = 0; row < 3; ++row) {
        plat_set_sprite(row * 2, rei_bx, (u8)(rei_by + row * 8), SPR_REI_IDLE + row * 2, rei_flip);
        plat_set_sprite(row * 2 + 1, rei_bx + TILE_W, (u8)(rei_by + row * 8), SPR_REI_IDLE + row * 2 + 1, rei_flip);
    }
    for (u8 row = 0; row < 2; ++row) {
        for (u8 col = 0; col < 4; ++col) {
            u8 slot = (u8)(row * 4 + col);
            plat_set_sprite(26 + slot,
                            boss_bx + col * TILE_W + boss_tile_offset_x(slot),
                            (u8)(boss_by + row * TILE_H + boss_tile_offset_y(slot)),
                            boss_base + boss_tile_index(slot), boss_tile_flags(slot));
        }
    }
}

/* FX sprites */
static void spr_draw_fx(void) {
    if (gs.fx_hit_timer > 0) {
        s16 fx_hit_x = camera_apply_x(gs.fx_hit_x);
        s16 fx_hit_y = camera_apply_y(gs.fx_hit_y);
        plat_set_sprite(34, fx_hit_x,          fx_hit_y,   SPR_FX_HIT+0, 0);
        plat_set_sprite(35, fx_hit_x+TILE_W,   fx_hit_y,   SPR_FX_HIT+1, 0);
    }
    if (gs.fx_nano_timer > 0) {
        s16 fx_nano_x = camera_apply_x(gs.fx_nano_x);
        s16 fx_nano_y = camera_apply_y(gs.fx_nano_y);
        plat_set_sprite(36, fx_nano_x,          fx_nano_y,  SPR_FX_NANO+0, 0);
        plat_set_sprite(37, fx_nano_x+TILE_W,   fx_nano_y,  SPR_FX_NANO+1, 0);
    }
}

static void narrative_draw(void) {
    bg_fill(TILE_BLANK);
    bg_draw_text(0, 1, campaign_stage_name(gs.campaign_stage));
    bg_draw_text(0, 2, narrative_path_line());
    if (gs.narrative_page == 0) {
        bg_draw_text(0, 10, narrative_stage_line_a());
        bg_draw_text(0, 11, narrative_stage_line_b());
        bg_draw_text(0, 12, narrative_stage_line_c());
        bg_draw_text(0, 13, duel_mechanic_label(gs.stage_duel_mechanic));
        bg_draw_text(0, 15, "A NEXT B SKIP");
    } else if (gs.narrative_page == 1) {
        bg_draw_text(0, 9, narrative_choice_line_a());
        bg_draw_text(0, 10, narrative_choice_line_b());
        bg_draw_text(0, 12, narrative_choice_option(0));
        bg_draw_text(0, 13, narrative_choice_option(1));
        bg_draw_text(0, 15, "L R PICK A LOCK");
    } else {
        bg_draw_text(0, 10, narrative_result_line_a());
        bg_draw_text(0, 12, narrative_result_line_b());
        bg_draw_text(0, 13, narrative_path_line());
        bg_draw_text(0, 15, "A DUEL B SKIP");
    }
    spr_hide_all();
    spr_draw_narrative_portraits();
    audio_emit_narrative_tts();
}

static void narrative_init(void) {
    camera_reset();
    gs.phase_timer = 0;
    gs.narrative_page = 0;
    gs.audio_last_narrative_page = 0xFF;
    gs.audio_last_choice_cursor = 0xFF;
    narrative_seed_choice();
    narrative_draw();
        bg_draw_text(0, 13, campaign_stage_cypher_label(gs.campaign_stage));
}

static int narrative_update(void) {
    gs.phase_timer++;
    if (plat_pressed(BTN_B)) return 1;
    if (gs.narrative_page == 1) {
        if (plat_pressed(BTN_LEFT)) {
            gs.moral_choice_cursor = 0;
            narrative_draw();
            return 0;
        }
        if (plat_pressed(BTN_RIGHT)) {
            gs.moral_choice_cursor = 1;
            narrative_draw();
            return 0;
        }
    }
    if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) {
        if (gs.narrative_page == 0) {
            gs.narrative_page = 1;
            narrative_draw();
            return 0;
        }
        if (gs.narrative_page == 1) {
            narrative_apply_choice();
            gs.narrative_page = 2;
            narrative_draw();
            return 0;
        }
        return 1;
    }
    if ((gs.phase_timer % 24) == 0) spr_draw_narrative_portraits();
    return 0;
}

/* Cinematic kaiju — kaiju A on left half, kaiju B on right half.
 * 3×4 tile arrangement each (12 tiles per kaiju).                     */
static void spr_draw_cinematic(void) {
    /* Step animation based on cut_frame: shift Y slightly for fighting motion */
    s16 ay = (s16)(SCR_H/2 - 24 + (gs.cut_frame % 2) * 2);
    s16 by_pos = (s16)(SCR_H/2 - 24 - (gs.cut_frame % 2) * 2);
    for (u8 row = 0; row < 4; ++row)
        for (u8 col = 0; col < 3; ++col) {
            /* Kaiju A — left side */
            plat_set_sprite(row*3+col,
                            8  + col * TILE_W, (u8)(ay + row * TILE_H),
                            SPR_CINEMATIC_A + row*3+col, 0x00);
            /* Kaiju B — right side (flipped) */
            plat_set_sprite(12 + row*3+col,
                            92 + (2-col) * TILE_W, (u8)(by_pos + row * TILE_H),
                            SPR_CINEMATIC_B + row*3+col, 0x20);
        }
}

/* Hide all sprites (move off-screen) */
static void spr_hide_all(void) {
#ifdef TARGET_HOST
    host_clear_sprites();
#endif
#ifdef TARGET_GB
    for (u8 i = 0; i < 40; ++i) { move_sprite(i, 0, 0); }
#endif
#ifdef TARGET_GBA
    /* Move all OAM entries off-screen */
    volatile u16 *oam = (u16*)0x07000000;
    for (int i = 0; i < 40; ++i) { oam[i*4] = 160; }
#endif
#ifdef TARGET_NDS
    for (int i = 0; i < 128; ++i) oamSetHidden(&oamMain, i, true);
    oamUpdate(&oamMain);
#endif
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: SPLASH PHASE
 * ═══════════════════════════════════════════════════════════════════════════ */

static void splash_init(void) {
    camera_reset();
    gs.phase_timer = 0;
    gs.skip_b_hold = 0;
    spr_hide_all();
    bg_draw_splash();
}

/* Returns 1 when splash should advance */
static int splash_update(void) {
    gs.phase_timer++;
    if (plat_held(BTN_B)) gs.skip_b_hold++;
    else                   gs.skip_b_hold = 0;

    if (gs.phase_timer >= SPLASH_HOLD_FRAMES) return 1;
    if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) return 1;
    if (gs.skip_b_hold >= SKIP_HOLD_FRAMES) return 1;
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: INTRO CINEMATIC PHASE
 *
 * The cinematic is a sequence of 8 "cuts", each held for CUT_DURATION frames.
 * Between cuts the background tiles shift to illustrate camera movement.
 * The two kaiju sprites animate a fight on the beach.
 * Hold B for SKIP_HOLD_FRAMES to exit early.
 *
 * Cut story:
 *   Cut 0: Dawn — beach, horizon, misty sky
 *   Cut 1: Wide — massive silhouette rises from the sea
 *   Cut 2: Medium — Rei, huge, steps onto shore
 *   Cut 3: Close — Rei and Storm Kaiju eye each other
 *   Cut 4: Action — Storm Kaiju throws a strike
 *   Cut 5: Action — Rei parries, counter-strike
 *   Cut 6: Wide — both clash, spray erupts
 *   Cut 7: Pullback — clouds part, title card imminent
 * ═══════════════════════════════════════════════════════════════════════════ */

#define CUT_COUNT     8
#define CUT_DURATION  60   /* frames per cut (~1s at 60fps, ~2s at 30fps) */

static void cinematic_init(void) {
    camera_reset();
    gs.cut_frame = 0;
    gs.cut_timer = 0;
    gs.skip_b_hold = 0;
    bg_draw_beach();
    spr_draw_cinematic();
}

/* Returns 1 when cinematic ends */
static int cinematic_update(void) {
    gs.cut_timer++;
    gs.anim_tick++;

    /* B-hold skip */
    if (plat_held(BTN_B)) gs.skip_b_hold++;
    else                   gs.skip_b_hold = 0;
    if (gs.skip_b_hold >= SKIP_HOLD_FRAMES) return 1;

    /* Advance cut every CUT_DURATION frames */
    if (gs.cut_timer >= CUT_DURATION) {
        gs.cut_timer = 0;
        gs.cut_frame++;
        /* Redraw background with slight variation to simulate camera cut */
        bg_draw_beach();
        if (gs.cut_frame >= CUT_COUNT) return 1;
    }
    /* Animate water tiles on beat */
    if ((gs.anim_tick % 8) == 0) bg_draw_beach();

    spr_draw_cinematic();
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: TITLE MENU PHASE
 * ═══════════════════════════════════════════════════════════════════════════ */

static void title_draw_progress(void) {
    u8 next_stage = campaign_next_stage_index(gs.cleared_bosses);
    bg_fill_rect(0, 13, BKG_COLS, 5, TILE_BLANK);
    bg_draw_panel(0, 13, BKG_COLS, 5, TILE_BLANK, TILE_GROUND_L, TILE_GROUND_R);
    if (next_stage < CAMPAIGN_STAGE_COUNT) {
        bg_draw_text_centered(13, campaign_stage_name(next_stage));
        bg_draw_text_centered(14, campaign_boss_name(next_stage));
        bg_draw_text_centered(15, campaign_stage_cypher_label(next_stage));
    } else {
        bg_draw_text_centered(13, "CYCLE COMPLETE");
        bg_draw_text_centered(14, "ALL CYPHERS WON");
        bg_draw_text_centered(15, "VOID TYRANT WAITS");
    }
    bg_draw_text(1, 16, "FORM");
    bg_draw_number_2(5, 16, (u8)(gs.rei_form + 1));
    bg_draw_text(8, 16, "RUN");
    bg_draw_number_2(12, 16, gs.run_serial);
    bg_draw_text(1, 17, "PATH");
    bg_draw_text(6, 17, moral_path_table[narrative_dominant_moral_index()]);
}

static void title_init(void) {
    camera_reset();
    gs.menu_sel  = 0;
    gs.phase_timer = 0;
    spr_hide_all();
    bg_draw_title();
    title_draw_progress();
    plat_audio_tts(AUDIO_VOICE_SYSTEM, "START GAME");
    audio_sync_profile();
}

/* Returns 0 = stay, 1 = start new game, 2 = password screen */
static int title_update(void) {
    gs.phase_timer++;
    if (plat_pressed(BTN_DOWN)) {
        gs.menu_sel = (gs.menu_sel + 1) % 2;
        bg_draw_title();
        title_draw_progress();
    }
    if (plat_pressed(BTN_UP)) {
        gs.menu_sel = (gs.menu_sel == 0) ? 1 : 0;
        bg_draw_title();
        title_draw_progress();
    }
    if ((gs.phase_timer & 0x03) == 0) {
        bg_draw_title();
        title_draw_progress();
    }
    if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) {
        return (gs.menu_sel == 0) ? 1 : 2;
    }
    return 0;
}

static void password_draw(void) {
    bg_fill(TILE_BLANK);
    spr_hide_all();
    bg_draw_text(6, 2, "PASSWORD");
    bg_draw_text(2, 5, "EDIT 16 HEX");
    for (u8 i = 0; i < PASSWORD_LEN; ++i)
        plat_set_bkg_tile(2 + i, 8, bg_char_to_tile(gs.password_buf[i]));
    for (u8 i = 0; i < PASSWORD_LEN; ++i)
        plat_set_bkg_tile(2 + i, 9, TILE_BLANK);
    plat_set_bkg_tile(2 + gs.password_index, 9, TILE_CLIFF_A);
    bg_draw_text(2, 12, "UD CHANGE");
    bg_draw_text(2, 13, "LR MOVE");
    bg_draw_text(2, 14, "A APPLY");
    bg_draw_text(2, 15, "B BACK");
}

static void password_init(void) {
    camera_reset();
    gs.phase_timer = 0;
    gs.password_index = 0;
    password_encode(gs.password_buf, gs.cleared_bosses, gs.cyphers);
    password_draw();
    plat_audio_tts(AUDIO_VOICE_SYSTEM, "PASSWORD");
    audio_sync_profile();
}

/* Returns 0 = stay, 1 = apply and return, 2 = cancel */
static int password_update(void) {
    gs.phase_timer++;

    if (plat_pressed(BTN_LEFT) && gs.password_index > 0) {
        gs.password_index--;
        password_draw();
    }
    if (plat_pressed(BTN_RIGHT) && gs.password_index + 1 < PASSWORD_LEN) {
        gs.password_index++;
        password_draw();
    }
    if (plat_pressed(BTN_UP)) {
        u8 nibble = password_hex_to_nibble(gs.password_buf[gs.password_index]);
        gs.password_buf[gs.password_index] = password_nibble_to_hex((u8)((nibble + 1) & 0x0F));
        password_draw();
    }
    if (plat_pressed(BTN_DOWN)) {
        u8 nibble = password_hex_to_nibble(gs.password_buf[gs.password_index]);
        gs.password_buf[gs.password_index] = password_nibble_to_hex((u8)((nibble - 1) & 0x0F));
        password_draw();
    }
    if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) {
        (void)password_decode(gs.password_buf, &gs.cleared_bosses, &gs.cyphers);
        return 1;
    }
    if (plat_pressed(BTN_B)) return 2;
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: STAGE INTRO PHASE ("3-2-1 DUEL!")
 * ═══════════════════════════════════════════════════════════════════════════ */

#define INTRO_BEAT_DUR  32   /* frames per count beat */
#define INTRO_PRELUDE_BEATS 2

static void stage_intro_draw_card(u8 intro_beat) {
    bg_draw_beach();
    bg_fill_rect(0, 1, BKG_COLS, 15, TILE_BLANK);
    bg_draw_panel(1, 1, 18, 5, TILE_BLANK, TILE_CLIFF_A, TILE_CLIFF_B);
    bg_draw_panel(1, 7, 18, 5, TILE_BLANK, TILE_GROUND_L, TILE_GROUND_R);
    bg_draw_panel(3, 13, 14, 2, TILE_BLANK, TILE_CLIFF_A, TILE_CLIFF_B);
    bg_draw_panel(1, 14, 18, 2, TILE_BLANK, TILE_GROUND_L, TILE_GROUND_R);
    bg_draw_text(2, 2, "STAGE");
    bg_draw_number_2(8, 2, (u8)(gs.campaign_stage + 1));
    bg_draw_text_centered(3, campaign_stage_name(gs.campaign_stage));
    bg_draw_text_centered(4, campaign_stage_ecosystem(gs.campaign_stage));
    bg_draw_text_centered(5, campaign_stage_cypher_label(gs.campaign_stage));
    bg_draw_text_centered(8, campaign_boss_name(gs.campaign_stage));
    if (intro_beat == 0) {
        bg_draw_text_centered(9, campaign_stage_hazard_line(gs.campaign_stage));
        bg_draw_text_centered(10, campaign_stage_terrain_line(gs.campaign_stage));
        bg_draw_text_centered(11, campaign_boss_intro(gs.campaign_stage));
        bg_draw_text_centered(15, duel_mechanic_label(gs.stage_duel_mechanic));
    } else if (intro_beat == 1) {
        bg_draw_text_centered(9, campaign_stage_minion_line(gs.campaign_stage));
        bg_draw_text_centered(10, campaign_stage_pressure_line(gs.campaign_stage));
        bg_draw_text_centered(11, campaign_rei_intro(gs.boss_prefab));
        bg_draw_text_centered(13, campaign_stage_cypher_effect(gs.campaign_stage));
        bg_draw_text_centered(15, "READY THE DUEL");
    } else {
        u8 beat = (u8)(intro_beat - INTRO_PRELUDE_BEATS);
        bg_draw_text_centered(9, campaign_stage_hazard_line(gs.campaign_stage));
        bg_draw_text_centered(10, campaign_stage_pressure_line(gs.campaign_stage));
        bg_draw_text_centered(13, "DUEL");
        if (beat < 3) {
            plat_set_bkg_tile(9, 13, TILE_FONT_0 + (3 - beat));
            plat_set_bkg_tile(10, 13, TILE_BLANK);
            bg_draw_text_centered(15, duel_mechanic_label(gs.stage_duel_mechanic));
        } else {
            bg_draw_text_centered(13, duel_qte_prompt(gs.duel_qte_button));
            bg_draw_text_centered(15, duel_mechanic_label(gs.stage_duel_mechanic));
        }
    }
}

static void stage_intro_init(void) {
    camera_reset();
    gs.phase_timer = 0;
    gs.player_x = 2;
    gs.player_y = (u8)(SCR_H - 24);
    gs.player_facing = 0;
    gs.player_anim = 0;
    gs.attack_timer = 0;
    gs.attack_queued = 0;
    boss_init();
    gs.boss_awake = 1;
    spr_hide_all();
    stage_intro_draw_card(0);
    audio_emit_stage_intro_tts();
}

/* Returns 1 when intro finishes */
static int stage_intro_update(void) {
    u8 intro_beat;
    gs.phase_timer++;
    gs.anim_tick++;
    intro_beat = (u8)(gs.phase_timer / INTRO_BEAT_DUR);
    stage_intro_draw_card(intro_beat);
    if (intro_beat >= (u8)(INTRO_PRELUDE_BEATS + 3)) {
        gs.duel_qte_ready = 1;
        if (gs.duel_qte_result == 0) {
            if (gs.input_pressed_mask & gs.duel_qte_button) gs.duel_qte_result = 1;
            else if (gs.input_pressed_mask & (BTN_A | BTN_B | BTN_SELECT)) gs.duel_qte_result = 2;
        }
    }
    if (intro_beat >= (u8)(INTRO_PRELUDE_BEATS + 4)) {
        if (gs.duel_qte_result == 0) gs.duel_qte_result = 2;
    }
    if (intro_beat >= (u8)(INTRO_PRELUDE_BEATS + 5)) return 1;
    spr_draw_rei();
    spr_draw_boss();
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: MINION LOGIC
 * ═══════════════════════════════════════════════════════════════════════════ */

static void minion_spawn_wave(void) {
    u8 spawned = 0;
    u8 wave_size = gs.stage_wave_size;
    for (u8 i = 0; i < MINION_MAX && spawned < wave_size; ++i) {
        if (!gs.minions[i].active) {
            u8 prefab_index = stage_spawn_prefab_choice(gs.campaign_stage, (u8)(gs.wave + i + gs.stage_bg_seed));
            const MinionPrefab *prefab = &minion_prefab_db[prefab_index % MINION_PREFAB_COUNT];
            gs.minions[i].active = 1;
            gs.minions[i].prefab = prefab_index;
            gs.minions[i].class_major = (u8)(stage_mix8(gs.stage_bg_seed, (u8)(170 + i + gs.wave)) % MINION_CLASS_MAJOR_COUNT);
            gs.minions[i].class_mid = (u8)(stage_mix8(gs.stage_bg_seed, (u8)(200 + i + gs.wave)) % MINION_CLASS_MID_COUNT);
            gs.minions[i].class_minor = (u8)(stage_mix8(gs.stage_bg_seed, (u8)(230 + i + gs.wave)) % MINION_CLASS_MINOR_COUNT);
            gs.minions[i].status = prefab->status_bias;
            gs.minions[i].genome = stage_make_genome(gs.stage_bg_seed, (u8)(150 + i + gs.wave));
            gs.minions[i].hp     = (u8)(gs.stage_minion_hp + prefab->hp_bonus + (gs.minions[i].genome.shell > 2));
            gs.minions[i].y      = (u8)(SCR_H - 32 - ((gs.wave + i) % 2) * 4);
            gs.minions[i].attack_windup = 0;
            gs.minions[i].attack_recover = 0;
            /* Alternate spawn sides */
            if (i % 2 == 0) {
                gs.minions[i].x  = SCR_W - 24;
                gs.minions[i].vx = -1;
            } else {
                gs.minions[i].x  = 4;
                gs.minions[i].vx = +1;
            }
            gs.minions[i].anim = 0;
            spawned++;
        }
    }
    gs.wave++;
    gs.wave_timer = (u8)(120 - gs.campaign_stage * 3);
    if (gs.wave_timer < 45) gs.wave_timer = 45;
}

static void minion_spawn_from_protocol(u8 slot_index) {
    u8 lane_y;
    for (u8 i = 0; i < MINION_MAX; ++i) {
        const MinionPrefab *prefab;
        u8 prefab_index;
        if (gs.minions[i].active) continue;
        prefab_index = (u8)(gs.spawn_slots[slot_index].prefab % MINION_PREFAB_COUNT);
        prefab = &minion_prefab_db[prefab_index];
        lane_y = (u8)(SCR_H - 32 - gs.spawn_slots[slot_index].lane * 4);
        gs.minions[i].active = 1;
        gs.minions[i].prefab = prefab_index;
        gs.minions[i].class_major = (u8)(stage_mix8(gs.stage_bg_seed, (u8)(240 + slot_index + i)) % MINION_CLASS_MAJOR_COUNT);
        gs.minions[i].class_mid = (u8)(stage_mix8(gs.stage_bg_seed, (u8)(20 + slot_index + i)) % MINION_CLASS_MID_COUNT);
        gs.minions[i].class_minor = (u8)(stage_mix8(gs.stage_bg_seed, (u8)(50 + slot_index + i)) % MINION_CLASS_MINOR_COUNT);
        gs.minions[i].status = gs.spawn_slots[slot_index].status;
        gs.minions[i].genome = gs.spawn_slots[slot_index].genome;
        gs.minions[i].hp = (u8)(gs.stage_minion_hp + prefab->hp_bonus + (gs.minions[i].genome.shell > 2));
        gs.minions[i].y = lane_y;
        gs.minions[i].anim = 0;
        gs.minions[i].attack_windup = 0;
        gs.minions[i].attack_recover = 0;
        if (gs.spawn_slots[slot_index].side == 0) {
            gs.minions[i].x = (s16)(SCR_W - 24);
            gs.minions[i].vx = -1;
        } else {
            gs.minions[i].x = 4;
            gs.minions[i].vx = 1;
        }
        gs.spawn_slots[slot_index].active = 0;
        gs.wave++;
        return;
    }
}

static void stage_spawn_update(void) {
    if (gs.boss_phase == 0) return;
    for (u8 i = 0; i < gs.stage_spawn_count; ++i) {
        if (!gs.spawn_slots[i].active) continue;
        if (gs.spawn_slots[i].timer > 0) {
            gs.spawn_slots[i].timer--;
        } else {
            minion_spawn_from_protocol(i);
        }
    }
}

static void minion_update_all(void) {
    u8 directive = stage_ai_directive();
    for (u8 i = 0; i < MINION_MAX; ++i) {
        const MinionPrefab *prefab;
        u8 behavior;
        u8 step;
        u8 attack_range;
        u8 preferred_range;
        s16 player_px;
        s16 delta;
        if (!gs.minions[i].active) continue;
        prefab = &minion_prefab_db[gs.minions[i].prefab % MINION_PREFAB_COUNT];
        behavior = (u8)((directive + gs.minions[i].class_major + prefab->status_bias + gs.minions[i].status) % 5);
        step = (u8)(gs.stage_minion_speed + prefab->speed_bonus + (gs.minions[i].genome.mobility > 2) + (gs.minions[i].class_major % 3 == 0));
        if (step == 0) step = 1;
        attack_range = (u8)(MINION_ATTACK_RANGE + gs.minions[i].genome.ferocity * 2 + (gs.minions[i].class_mid % 3));
        if (behavior == 4) attack_range = (u8)(attack_range + 4);
        else if (behavior == 3 && attack_range > 2) attack_range = (u8)(attack_range - 2);
        preferred_range = (u8)(attack_range + 6 + ((gs.minions[i].class_minor + behavior) & 0x03) * 3);
        gs.minions[i].anim++;
        player_px = (s16)(gs.player_x * TILE_W);
        delta = player_px - gs.minions[i].x;
        if (delta < 0) gs.minions[i].vx = -1;
        else if (delta > 0) gs.minions[i].vx = 1;

        if (gs.minions[i].attack_recover > 0) {
            gs.minions[i].attack_recover--;
            if ((behavior == 1 || behavior == 4) && abs_distance_u8(gs.minions[i].x, player_px) < preferred_range && gs.minions[i].attack_recover > 6) {
                s16 retreat_x = (s16)(gs.minions[i].x - gs.minions[i].vx * step);
                if (retreat_x >= 0 && retreat_x <= SCR_W - 16 && !stage_column_blocked((u8)(retreat_x / TILE_W))) gs.minions[i].x = retreat_x;
            }
        } else if (gs.minions[i].attack_windup > 0) {
            gs.minions[i].attack_windup--;
            if (behavior == 3 && gs.minions[i].attack_windup > 2 && abs_distance_u8(gs.minions[i].x, player_px) > attack_range) {
                s16 surge_x = (s16)(gs.minions[i].x + gs.minions[i].vx * (step + 1));
                if (surge_x >= 0 && surge_x <= SCR_W - 16 && !stage_column_blocked((u8)(surge_x / TILE_W))) gs.minions[i].x = surge_x;
            }
            if (gs.minions[i].attack_windup == 0) {
                if (abs_distance_u8(gs.minions[i].x, player_px) <= attack_range && gs.hit_stun == 0 && gs.dodge_timer == 0) {
                    if (gs.player_hp > 0) gs.player_hp--;
                    gs.hit_stun = 36;
                    gs.fx_hit_x = (u8)player_px;
                    gs.fx_hit_y = (u8)(SCR_H - 28);
                    gs.fx_hit_timer = 8;
                }
                gs.minions[i].attack_recover = MINION_RECOVER_FRAMES;
            }
        } else {
            if (abs_distance_u8(gs.minions[i].x, player_px) <= attack_range) {
                gs.minions[i].attack_windup = (u8)(MINION_WINDUP_FRAMES - ((prefab->windup_bias > 3) ? 3 : prefab->windup_bias) - (gs.minions[i].class_minor % 2));
                if (behavior == 3 && gs.minions[i].attack_windup > 2) gs.minions[i].attack_windup = (u8)(gs.minions[i].attack_windup - 2);
                else if (behavior == 1) gs.minions[i].attack_windup = (u8)(gs.minions[i].attack_windup + 1);
                if (gs.minions[i].attack_windup < 6) gs.minions[i].attack_windup = 6;
            } else {
                s16 next_x = (s16)(gs.minions[i].x + gs.minions[i].vx * step);
                if (behavior == 0 && abs_distance_u8(gs.minions[i].x, player_px) > preferred_range + 8) {
                    next_x = (s16)(gs.minions[i].x + gs.minions[i].vx * (step + 1));
                } else if (behavior == 1) {
                    if (abs_distance_u8(gs.minions[i].x, player_px) < preferred_range) next_x = (s16)(gs.minions[i].x - gs.minions[i].vx * step);
                } else if (behavior == 2) {
                    if (abs_distance_u8(gs.minions[i].x, player_px) < preferred_range) next_x = (s16)(gs.minions[i].x + gs.minions[i].vx * (step + 2));
                } else if (behavior == 3) {
                    if (((gs.minions[i].anim + gs.run_serial + i) & 0x07) == 0) next_x = (s16)(gs.minions[i].x + gs.minions[i].vx * (step + 2 + (gs.minions[i].genome.mobility > 2)));
                    else if (abs_distance_u8(gs.minions[i].x, player_px) < attack_range + 4) next_x = (s16)(gs.minions[i].x - gs.minions[i].vx * step);
                } else {
                    if (abs_distance_u8(gs.minions[i].x, player_px) < preferred_range) next_x = (s16)(gs.minions[i].x - gs.minions[i].vx * (step + (gs.minions[i].class_minor & 0x01)));
                    else if (abs_distance_u8(gs.minions[i].x, player_px) > preferred_range + 10) next_x = (s16)(gs.minions[i].x + gs.minions[i].vx * (step + 1));
                }
                if (!stage_column_blocked((u8)(next_x / TILE_W))) gs.minions[i].x = next_x;
                else gs.minions[i].vx = (s8)(-gs.minions[i].vx);
            }
        }

        /* Bounds clamp */
        if (gs.minions[i].x < 0)         { gs.minions[i].x = 0;            gs.minions[i].vx = +1; }
        if (gs.minions[i].x > SCR_W - 16){ gs.minions[i].x = SCR_W - 16;   gs.minions[i].vx = -1; }
        if (gs.minions[i].hp == 0) {
            gs.minions[i].active = 0;
        }
    }
}

/* Attempt melee attack reaching pixel radius from Rei's centre */
static void player_attack_minions(u8 radius) {
    s16 px = (s16)(gs.player_x * TILE_W + 8);
    for (u8 i = 0; i < MINION_MAX; ++i) {
        if (!gs.minions[i].active) continue;
        s16 target_x = gs.minions[i].x + 8;
        if (attack_hits_target(px, gs.player_facing, target_x, radius, PLAYER_ATTACK_REAR)) {
            gs.minions[i].attack_windup = 0;
            gs.minions[i].attack_recover = MINION_RECOVER_FRAMES;
            if (gs.minions[i].hp <= gs.attack_dmg) {
                gs.minions[i].active = 0;
                /* Drop NanoCell */
                if (gs.nanocell_count < NANOCELL_MAX) {
                    gs.nanocell_count++;
                    gs.fx_nano_x = (u8)(gs.minions[i].x);
                    gs.fx_nano_y = gs.minions[i].y;
                    gs.fx_nano_timer = 12;
                }
            } else {
                gs.minions[i].hp -= gs.attack_dmg;
                gs.minions[i].x += gs.player_facing ? -6 : 6;
                if (gs.minions[i].x < 0) gs.minions[i].x = 0;
                if (gs.minions[i].x > SCR_W - 16) gs.minions[i].x = SCR_W - 16;
            }
            gs.fx_hit_x = (u8)gs.minions[i].x;
            gs.fx_hit_y = gs.minions[i].y;
            gs.fx_hit_timer = 8;
            camera_punch(1, 4);
        }
    }
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: BOSS LOGIC
 *
 * Boss has 3 phases; each has its own HP pool.
 * Phase transitions trigger a screen-flash (all tiles toggled for 4 frames).
 *
 * PHASE 1 — Harbor Leviathan: Sweep & Spit pattern
 *   ATK_SWEEP: lateral claw sweep, telegraphed 20-frame wind-up
 *   ATK_SPIT : water ball projectile (tile animation — placeholder: tile flash)
 *
 * PHASE 2 — Exposed Core: Slam & Spit combos
 *   ATK_SLAM : overhead slam, harder to dodge, fills bottom row
 *   ATK_SPIT : rapid double spit
 *
 * PHASE 3 — Tidal Pull: pulls Rei toward boss every 4 seconds
 *   ATK_TIDAL: narrows movement window; player must use NanoCell to resist
 *   ATK_SWEEP: increased speed and range
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Boss total HP across all phases */
#define BOSS_TOTAL_HP (BOSS_HP_P1 + BOSS_HP_P2 + BOSS_HP_P3)

static void boss_init(void) {
    gs.boss_awake     = 1;
    gs.boss_phase     = 1;
    gs.boss_hp        = gs.stage_boss_hp_p1;
    gs.boss_intro_lock = boss_prefab_db[gs.boss_prefab].opener_lock;
    gs.duel_first_strike_timer = DUEL_FIRST_STRIKE_FRAMES;
    gs.boss_x         = (s16)(SCR_W - 40 - ((gs.stage_bg_seed & 0x03) * 4));
    gs.boss_atk_timer = (u8)(gs.stage_boss_int_p1 + gs.boss_intro_lock);
    gs.boss_atk_type  = BOSS_ATK_SWEEP;
    gs.boss_windup    = 0;
    gs.boss_recover   = 0;
    gs.boss_stun      = 0;
}

/* Deal damage to boss; handles phase transitions. Returns 1 if boss is dead. */
static int boss_take_damage(u8 dmg) {
    if (!gs.boss_awake) return 0;
    if (gs.boss_stun == 0 && gs.boss_hp > 0) {
        if (gs.boss_hp <= dmg) {
            gs.boss_hp = 0;
            /* Advance phase or signal death */
            if (gs.boss_phase < 3) {
                gs.boss_phase++;
                gs.boss_hp = (gs.boss_phase == 2) ? gs.stage_boss_hp_p2 : gs.stage_boss_hp_p3;
                gs.boss_windup = 0;
                gs.boss_recover = 30;
                gs.boss_stun = 60;      /* brief stun at phase change */
                combat_set_banner(BANNER_BOSS_STUN, 50);
                camera_punch(3, 10);
                gs.boss_atk_timer = (gs.boss_phase == 2) ? gs.stage_boss_int_p2
                                                          : gs.stage_boss_int_p3;
                /* Screen flash: invert bg briefly */
                bg_fill(TILE_GROUND_R);
                plat_vsync();
                plat_vsync();
                bg_draw_beach();
                return 0;
            } else {
                return 1; /* boss fully defeated */
            }
        } else {
            gs.boss_hp -= dmg;
            if (gs.boss_windup > 0) {
                gs.boss_windup = 0;
                gs.boss_recover = 18;
            }
            gs.boss_stun = 20;
            combat_set_banner(BANNER_BOSS_STUN, 20);
            camera_punch(2, 6);
            return 0;
        }
    }
    return 0;
}

/* Boss logic: choose and execute attacks, move toward player */
static void boss_update(void) {
    if (gs.boss_phase == 0 || !gs.boss_awake) return;
    if (gs.boss_intro_lock > 0) {
        gs.boss_intro_lock--;
        return;
    }

    /* Stun countdown */
    if (gs.boss_stun > 0) { gs.boss_stun--; return; }

    if (gs.boss_recover > 0) {
        gs.boss_recover--;
        return;
    }

    if (gs.boss_windup > 0) {
        u8 resolved_type = gs.boss_atk_type;
        gs.boss_windup--;
        if (gs.boss_windup > 0) return;

        /* Resolve telegraphed attack */
        s16 px_now = (s16)(gs.player_x * TILE_W);
        s16 dist_now = gs.boss_x - px_now;
        if (dist_now < 0) dist_now = -dist_now;

        switch (resolved_type) {
            case BOSS_ATK_SWEEP:
                if (dist_now < BOSS_SWEEP_RANGE && gs.hit_stun == 0 && gs.dodge_timer == 0) {
                    if (gs.player_hp > 0) gs.player_hp--;
                    gs.hit_stun = 30;
                    gs.fx_hit_x  = (u8)px_now;
                    gs.fx_hit_y  = (u8)(SCR_H - 32);
                    gs.fx_hit_timer = 8;
                    camera_punch(2, 6);
                }
                break;

            case BOSS_ATK_SPIT:
                if (dist_now < BOSS_SPIT_RANGE && gs.hit_stun == 0 && gs.dodge_timer == 0) {
                    if (gs.player_hp > 0) gs.player_hp--;
                    gs.hit_stun = 25;
                    gs.fx_hit_x  = (u8)px_now;
                    gs.fx_hit_y  = (u8)(SCR_H - 40);
                    gs.fx_hit_timer = 8;
                    camera_punch(2, 5);
                }
                break;

            case BOSS_ATK_SLAM:
                if (dist_now < BOSS_SLAM_RANGE && gs.hit_stun == 0 && gs.dodge_timer == 0) {
                    gs.player_hp = (gs.player_hp >= 2) ? gs.player_hp - 2 : 0;
                    gs.hit_stun = 40;
                    gs.fx_hit_x = (u8)px_now;
                    gs.fx_hit_y = (u8)(SCR_H - 28);
                    gs.fx_hit_timer = 10;
                    camera_punch(3, 8);
                }
                break;

            case BOSS_ATK_TIDAL:
                if (gs.boss_x > px_now && gs.player_x < 18) gs.player_x++;
                else if (gs.boss_x <= px_now && gs.player_x > 0) gs.player_x--;
                if (gs.nanocell_boost_timer == 0 && gs.hit_stun == 0 && gs.dodge_timer == 0 && dist_now < BOSS_SPIT_RANGE) {
                    if (gs.player_hp > 0) gs.player_hp--;
                    gs.hit_stun = 18;
                    camera_punch(2, 5);
                }
                break;
        }

            gs.boss_recover = boss_attack_recover_frames(resolved_type);
            gs.boss_atk_type = boss_pick_attack();
            gs.boss_atk_timer = (gs.boss_phase == 1) ? gs.stage_boss_int_p1
                              : (gs.boss_phase == 2) ? gs.stage_boss_int_p2
                                                     : gs.stage_boss_int_p3;
        return;
    }

    /* Slow drift toward player */
    s16 px = (s16)(gs.player_x * TILE_W);
    s16 boss_step = (s16)(1 + ((gs.stage_boss_style == 2) ? 1 : 0) + (gs.boss_genome.mobility > 2));
    if (gs.boss_x > px + 30 && !stage_column_blocked((u8)((gs.boss_x - boss_step) / TILE_W))) gs.boss_x -= boss_step;
    if (gs.boss_x < px - 10 && !stage_column_blocked((u8)((gs.boss_x + boss_step) / TILE_W))) gs.boss_x += boss_step;

    /* Attack timer */
    if (gs.boss_atk_timer > 0) { gs.boss_atk_timer--; return; }

    gs.boss_atk_type = boss_pick_attack();
    gs.boss_windup = boss_attack_windup_frames(gs.boss_atk_type);
}

static u8 combat_perfect_window(void) {
    u8 window = 5;
    u8 adaptive_pressure = campaign_adaptive_pressure(gs.campaign_stage);
    if (gs.combo_count > 0 && window < 6) window++;
    if (gs.rei_style_adaptation > gs.rei_style_pressure && window < 7) window++;
    if (gs.boss_threat >= 2 && window < 7) window++;
    if (adaptive_pressure >= 2 && gs.rei_style_pressure > gs.rei_style_adaptation && window > 4) window--;
    if (gs.stage_boss_style == 2 && window > 4) window--;
    return window;
}

static u8 combat_attack_buffer_frames(void) {
    u8 frames = INPUT_BUFFER_FRAMES;
    u8 adaptive_pressure = campaign_adaptive_pressure(gs.campaign_stage);
    if (gs.combo_timer > 0 || gs.boss_windup > 0) frames++;
    if (gs.boss_threat >= 2 && frames < 7) frames++;
    if (gs.rei_style_adaptation > gs.rei_style_precision && frames < 7) frames++;
    if (adaptive_pressure >= 2 && gs.rei_style_pressure > gs.rei_style_adaptation && frames > 4) frames--;
    return frames;
}

static u8 combat_dodge_frames(void) {
    u8 frames = DODGE_FRAMES;
    u8 adaptive_pressure = campaign_adaptive_pressure(gs.campaign_stage);
    if (gs.boss_threat >= 2 && frames < 12) frames++;
    if (gs.rei_style_adaptation > gs.rei_style_pressure && frames < 12) frames++;
    if (adaptive_pressure >= 2 && gs.rei_style_pressure > gs.rei_style_adaptation && frames > 8) frames--;
    return frames;
}

static u8 combat_dodge_step(void) {
    u8 step = DODGE_STEP;
    if (gs.boss_threat >= 2 || gs.stage_duel_mechanic == 3) step++;
    if (step > 4) step = 4;
    return step;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: COMBAT PHASE
 * ═══════════════════════════════════════════════════════════════════════════ */

static void combat_init(void) {
    memset(&gs.minions, 0, sizeof(gs.minions));
    camera_reset();
    gs.wave       = 0;
    gs.wave_timer = 0;
    gs.player_hp  = PLAYER_MAX_HP;
    gs.player_x   = 2;
    gs.player_y   = (u8)(SCR_H - 24);
    gs.player_facing = 0;
    gs.player_anim = 0;
    gs.attack_timer  = 0;
    gs.attack_queued = 0;
    gs.attack_buffer = 0;
    gs.dodge_buffer = 0;
    gs.hit_stun      = 0;
    gs.dodge_timer   = 0;
    gs.combo_count   = 0;
    gs.combo_timer   = 0;
    gs.beat_timer    = 0;
    gs.perfect_flash_timer = 0;
    gs.nanocell_count = 0;
    gs.nanocell_boost_timer = 0;
    gs.attack_dmg    = 1;
    gs.fx_hit_timer  = 0;
    gs.fx_nano_timer = 0;
    gs.phase_timer   = 0;
    gs.banner_kind   = BANNER_NONE;
    gs.banner_timer  = 0;
    gs.boss_threat   = 0;
    gs.input_held_mask = 0;
    gs.input_pressed_mask = 0;
    gs.input_edge_total = 0;
    gs.input_active_frames = 0;
    gs.input_attack_edges = 0;
    gs.input_dodge_edges = 0;
    gs.input_nanocell_edges = 0;
    gs.dodge_read_total = 0;
    if (gs.rei_form >= REI_FORM_COUNT) gs.rei_form = 0;
    rei_refresh_growth_state();
    for (u8 i = 0; i < MINION_MAX; ++i) gs.minions[i].active = 0;
    boss_init();
    duel_apply_intro_outcome();
    stage_hazard_reset();
    gs.duel_qte_ready = 0;
    bg_draw_beach();
    spr_hide_all();
    audio_sync_profile();
}

/* Returns 1 if player dies, 2 if boss is fully defeated */
static int combat_update(void) {
    u8 minions_before;
    u8 minions_after;
    u8 camera_redraw;
    u8 hazard_was_active;
    u8 perfect_window = combat_perfect_window();
    gs.anim_tick++;
    gs.phase_timer++;

#ifdef TARGET_HOST
    if (host_autoplay_enabled && gs.boss_awake && gs.phase_timer > 180 && (gs.phase_timer % 24) == 0) {
        gs.fx_hit_x = (u8)(gs.boss_x - 4);
        gs.fx_hit_y = (u8)(SCR_H - 40);
        gs.fx_hit_timer = 10;
        combat_set_banner(BANNER_PERFECT, 12);
        camera_punch(2, 5);
        if (boss_take_damage((gs.phase_timer >= 320) ? 3 : 2)) {
            return 2;
        }
    }
    if (host_autoplay_enabled && gs.phase_timer >= 480) {
        gs.boss_hp = 0;
        gs.boss_awake = 0;
        combat_set_banner(BANNER_FINISHER, 24);
        camera_punch(3, 8);
        return 2;
    }
#endif

    /* Beat timer (for combo-window timing) */
    gs.beat_timer++;
    if (gs.beat_timer >= (u16)BEAT_PERIOD) gs.beat_timer = 0;
    gs.beat_perfect = 0;
    if (gs.beat_timer < perfect_window || gs.beat_timer >= (u16)(BEAT_PERIOD - perfect_window))
        gs.beat_perfect = 1;

    /* Countdown timers */
    if (gs.attack_timer > 0)          gs.attack_timer--;
    if (gs.attack_buffer > 0)         gs.attack_buffer--;
    if (gs.dodge_buffer > 0)          gs.dodge_buffer--;
    if (gs.hit_stun > 0)               gs.hit_stun--;
    if (gs.dodge_timer > 0)            gs.dodge_timer--;
    if (gs.combo_timer > 0)            gs.combo_timer--;
    else                               gs.combo_count = 0;
    if (gs.player_anim > 0)            gs.player_anim--;
    if (gs.perfect_flash_timer > 0)    gs.perfect_flash_timer--;
    if (gs.banner_timer > 0)           gs.banner_timer--;
    if (gs.nanocell_boost_timer > 0) {
        gs.nanocell_boost_timer--;
        gs.attack_dmg = 2;
    } else {
        gs.attack_dmg = 1;
    }
    if (gs.fx_hit_timer  > 0) gs.fx_hit_timer--;
    if (gs.fx_nano_timer > 0) gs.fx_nano_timer--;

    if (gs.input_pressed_mask & BTN_A) gs.attack_buffer = combat_attack_buffer_frames();
    if (gs.input_pressed_mask & BTN_B) gs.dodge_buffer = INPUT_BUFFER_FRAMES;

    if (gs.duel_first_strike_timer > 0) gs.duel_first_strike_timer--;
    stage_spawn_update();
    hazard_was_active = gs.stage_hazard_active;
    stage_hazard_update();
    if (hazard_was_active == 0 && gs.stage_hazard_active > 0 && gs.banner_timer == 0) {
        combat_set_banner(BANNER_HAZARD, 18);
    }

    /* Movement */
    u8 moved = 0;
    if (plat_held(BTN_LEFT) && gs.player_x > 0 && !stage_column_blocked((u8)(gs.player_x - 1))) {
        gs.player_x--;
        gs.player_facing = 1;
        moved = 1;
    }
    if (plat_held(BTN_RIGHT) && gs.player_x < 17 && !stage_column_blocked((u8)(gs.player_x + 1))) {
        gs.player_x++;
        gs.player_facing = 0;
        moved = 1;
    }
    if (moved) gs.player_anim = 8;

    /* Attack — A button */
    if (gs.attack_buffer > 0 && gs.attack_timer == 0 && gs.dodge_timer == 0 && gs.hit_stun == 0) {
        gs.attack_timer = ATTACK_TOTAL_FRAMES;
        gs.attack_queued = 1;
        gs.attack_buffer = 0;
    }

    if (gs.attack_queued && gs.attack_timer == ATTACK_ACTIVE_FRAME) {
        u8 dmg = gs.attack_dmg;
        u8 finisher = 0;
        gs.attack_queued = 0;
        if (gs.beat_perfect) {
            dmg++;
            gs.combo_count++;
            gs.combo_timer = ATTACK_COMBO_WINDOW;
            gs.perfect_flash_timer = 12;
            combat_set_banner(BANNER_PERFECT, 12);
            if (gs.combo_count >= PLAYER_FINISHER_COMBO) {
                finisher = 1;
                dmg += 2;
                combat_set_banner(BANNER_FINISHER, 20);
                camera_punch(2, 6);
            }
        }
        player_attack_minions(PLAYER_ATTACK_FRONT);
        if (gs.boss_awake) {
            s16 px = (s16)(gs.player_x * TILE_W + 8);
            s16 target = (s16)(gs.boss_x + 16);
            if (attack_hits_target(px, gs.player_facing, target, PLAYER_ATTACK_FRONT + 4, PLAYER_ATTACK_REAR)) {
                if (gs.duel_first_strike_timer > 0) {
                    dmg += 2;
                    gs.duel_first_strike_timer = 0;
                    gs.boss_intro_lock = 0;
                    combat_set_banner(BANNER_FIRST, 24);
                    camera_punch(3, 8);
                }
                if (finisher && gs.boss_stun < 24) gs.boss_stun = 24;
                if (boss_take_damage(dmg)) {
                    return 2; /* boss defeated */
                }
                gs.fx_hit_x = (u8)(gs.boss_x - 4);
                gs.fx_hit_y = (u8)(SCR_H - 40);
                gs.fx_hit_timer = 10;
                camera_punch(finisher ? 3 : 2, finisher ? 8 : 5);
            }
        }
    }

    /* Use NanoCell — Select button */
    if ((gs.input_pressed_mask & BTN_SELECT) && gs.nanocell_count > 0) {
        gs.nanocell_count--;
        gs.nanocell_boost_timer = NANOCELL_BOOST_DUR;
        combat_set_banner(BANNER_SURGE, 14);
        /* Flash screen briefly */
        bg_fill(TILE_SKY_B);
        plat_vsync();
        bg_draw_beach();
        camera_punch(1, 6);
    }

    /* Dodge — B button gives brief hit_stun invincibility */
    if (gs.dodge_buffer > 0 && gs.hit_stun == 0 && gs.attack_timer == 0) {
        u8 dodge_frames = combat_dodge_frames();
        u8 dodge_step = combat_dodge_step();
        if (gs.boss_awake && gs.boss_windup > 0 && gs.boss_threat >= 1) gs.dodge_read_total++;
        gs.dodge_timer = dodge_frames;
        /* Shift player 2 columns in facing direction */
        if (!gs.player_facing && gs.player_x < 17 - dodge_step) gs.player_x += dodge_step;
        else if (!gs.player_facing && gs.player_x < 17) gs.player_x = 17;
        if ( gs.player_facing && gs.player_x > dodge_step - 1)  gs.player_x -= dodge_step;
        else if (gs.player_facing) gs.player_x = 0;
        combat_set_banner(BANNER_DODGE, 10);
        gs.dodge_buffer = 0;
        camera_punch(1, 4);
    }

    /* Minion AI */
    minions_before = combat_minions_alive();
    minion_update_all();
    stage_hazard_apply_to_minions();
    stage_hazard_apply_to_player();
    minions_after = combat_minions_alive();
    if (minions_before > 0 && minions_after == 0 && combat_pending_spawns() > 0) {
        combat_set_banner(BANNER_WAVE_CLEAR, 30);
    }

    /* Boss AI */
    boss_update();

    camera_redraw = combat_camera_update();

    /* Redraw dynamic background on anim ticks */
    if (camera_redraw) bg_draw_beach();
    else if ((gs.anim_tick % WATER_REDRAW_PERIOD) == 0) bg_draw_beach_water_only();

    /* HUD */
    hud_draw();

    /* Sprites */
    spr_hide_all();
    spr_draw_rei();
    spr_draw_boss();
    spr_draw_minions();
    spr_draw_fx();

    /* Death check */
    if (gs.player_hp == 0) return 1;
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: CYPHER DROP PHASE
 * Shown when boss is defeated — brief screen message, then return to menu
 * ═══════════════════════════════════════════════════════════════════════════ */

#define CYPHER_DISPLAY_FRAMES 180

static void cypher_init(void) {
    u8 next_stage;
    camera_reset();
    gs.phase_timer = 0;
    rei_apply_stage_growth();
    gs.cleared_bosses |= (1u << gs.campaign_stage);
    gs.cyphers        |= (1u << gs.campaign_stage);
    password_encode(gs.password_buf, gs.cleared_bosses, gs.cyphers);
    next_stage = campaign_next_stage_index(gs.cleared_bosses);
    spr_hide_all();
    bg_fill(TILE_BLANK);
    bg_draw_text(6, 4, "CYPHER");
    bg_draw_text_centered(5, campaign_stage_cypher_label(gs.campaign_stage));
    bg_draw_text_centered(6, campaign_stage_cypher_effect(gs.campaign_stage));
    bg_draw_text_centered(7, campaign_stage_terrain_line(gs.campaign_stage));
    bg_draw_text_centered(8, campaign_stage_name(gs.campaign_stage));
    bg_draw_text(4, 10, "SAVE CODE");
    bg_draw_text(2, 11, gs.password_buf);
    bg_draw_text(0, 13, "REI FORM");
    bg_draw_number_2(9, 13, (u8)(gs.rei_form + 1));
    bg_draw_text(12, 13, "GP");
    bg_draw_number_2(15, 13, (u8)(gs.rei_growth_points % 100));
    if (next_stage < CAMPAIGN_STAGE_COUNT) {
        bg_draw_text_centered(14, campaign_stage_name(next_stage));
        bg_draw_text_centered(15, campaign_boss_name(next_stage));
    } else {
        bg_draw_text_centered(14, "A CYCLE COMPLETE");
        bg_draw_text_centered(15, "VOID TYRANT WAITS");
    }
    plat_audio_event(AUDIO_EVENT_VICTORY, gs.campaign_stage);
    plat_audio_tts(AUDIO_VOICE_SYSTEM, "CYPHER SECURED");
    plat_audio_tts(AUDIO_VOICE_SYSTEM, campaign_stage_cypher_effect(gs.campaign_stage));
    audio_sync_profile();
}

/* Returns 1 when complete */
static int cypher_update(void) {
    gs.phase_timer++;
    if (gs.phase_timer >= CYPHER_DISPLAY_FRAMES) return 1;
    if (plat_pressed(BTN_A) || plat_pressed(BTN_START)) return 1;
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: GAME OVER PHASE
 * ═══════════════════════════════════════════════════════════════════════════ */

static void gameover_init(void) {
    camera_reset();
    gs.phase_timer = 0;
    spr_hide_all();
    bg_fill(TILE_BLANK);
    bg_draw_text(5, 8, "GAME OVER");
    bg_draw_text(3, 12, "PRESS A OR START");
    plat_audio_event(AUDIO_EVENT_DEFEAT, gs.campaign_stage);
    plat_audio_tts(AUDIO_VOICE_SYSTEM, "GAME OVER");
    audio_sync_profile();
}

/* Returns 1 when player acknowledges */
static int gameover_update(void) {
    gs.phase_timer++;
    if (gs.phase_timer >= GAMEOVER_HOLD_FRAMES && plat_pressed(BTN_A)) return 1;
    if (gs.phase_timer >= GAMEOVER_HOLD_FRAMES && plat_pressed(BTN_START)) return 1;
    return 0;
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: MAIN ENTRY POINT
 * ═══════════════════════════════════════════════════════════════════════════ */

int main(void) {
    /* ── Platform initialisation ── */

#ifdef TARGET_GB
    DISPLAY_OFF;
    {
        static const uint16_t gb_dmg_pal[4] = {0x7FFF, 0x56B5, 0x294A, 0x0000};
        set_bkg_palette(0, 4, gb_dmg_pal);
    }
    SHOW_BKG;
    SHOW_SPRITES;
    DISPLAY_ON;
#endif

#ifdef TARGET_GBA
    irqInit();
    irqEnable(IRQ_VBLANK);
    /* Enable BG0 + OBJ display, 1D sprite mapping */
    REG_DISPCNT = MODE_0 | BG0_ON | OBJ_ON | OBJ_1D_MAP;
    /* BG0 control: charblock 0, screenblock 28, 4bpp (default), 32×32 */
    REG_BG0CNT  = CHAR_BASE(0) | SCREEN_BASE(28) | BG_SIZE_0;
    /* 4-shade GB-style palette */
    BG_PALETTE[0] = 0x7FFF;
    BG_PALETTE[1] = 0x56B5;
    BG_PALETTE[2] = 0x294A;
    BG_PALETTE[3] = 0x0000;
    SPRITE_PALETTE[0] = 0x0000; /* transparent */
    SPRITE_PALETTE[1] = 0x7FFF;
    SPRITE_PALETTE[2] = 0x56B5;
    SPRITE_PALETTE[3] = 0x294A;
#endif

#ifdef TARGET_NDS
    irqEnable(IRQ_VBLANK);
    videoSetMode(MODE_0_2D | DISPLAY_BG0_ACTIVE | DISPLAY_SPR_ACTIVE | DISPLAY_SPR_1D_LAYOUT);
    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankB(VRAM_B_MAIN_SPRITE);
    bgInit(0, BgType_Text4bpp, BgSize_T_256x256, 0, 0);
    BG_PALETTE[0] = RGB15(31, 31, 31);
    BG_PALETTE[1] = RGB15(20, 24, 18);
    BG_PALETTE[2] = RGB15(10, 14, 10);
    BG_PALETTE[3] = RGB15(2, 4, 2);
    SPRITE_PALETTE[0] = RGB15(31, 0, 31);
    SPRITE_PALETTE[1] = BG_PALETTE[1];
    SPRITE_PALETTE[2] = BG_PALETTE[2];
    SPRITE_PALETTE[3] = BG_PALETTE[3];
    oamInit(&oamMain, SpriteMapping_1D_32, false);
#endif

#if defined(TARGET_HOST) || defined(TARGET_3DS)
    host_init();
#endif

    /* ── Load all tiles once ── */
    game_load_tiles();

    /* ── Initialise game state ── */
    memset(&gs, 0, sizeof(gs));
    plat_audio_reset();
    gs.phase = PHASE_SPLASH;
    splash_init();

    /* ── Main loop ── */
    while (1) {
    #ifdef TARGET_3DS
        if (!aptMainLoop()) break;
    #endif
#ifdef TARGET_HOST
        if (g_quit) break;
#endif
        plat_poll_input();
        input_capture_frame();

    #ifdef TARGET_3DS
        if (ctr_options_open) {
            audio_sync_profile();
            plat_vsync();
            continue;
        }
    #endif

        switch (gs.phase) {

            case PHASE_SPLASH:
                if (splash_update()) {
                    gs.phase = PHASE_CINEMATIC;
                    cinematic_init();
                }
                break;

            case PHASE_CINEMATIC:
                if (cinematic_update()) {
                    gs.phase = PHASE_TITLE;
                    title_init();
                }
                break;

            case PHASE_TITLE: {
                int sel = title_update();
                if ((gs.phase_timer % 16) == 0) {
                    bg_draw_title();
                    title_draw_progress();
                }
                if (sel == 1) {
                    campaign_start_from_title();
                    gs.phase = PHASE_NARRATIVE;
                    narrative_init();
                } else if (sel == 2) {
                    gs.phase = PHASE_PASSWORD;
                    password_init();
                }
                break;
            }

            case PHASE_PASSWORD: {
                int result = password_update();
                if (result == 1) {
                    u8 next_stage = campaign_next_stage_index(gs.cleared_bosses);
                    if (next_stage >= CAMPAIGN_STAGE_COUNT) {
                        gs.phase = PHASE_TITLE;
                        title_init();
                    } else {
                        campaign_generate_stage(next_stage);
                        gs.phase = PHASE_NARRATIVE;
                        narrative_init();
                    }
                } else if (result == 2) {
                    gs.phase = PHASE_TITLE;
                    title_init();
                }
                break;
            }

            case PHASE_NARRATIVE:
                if (narrative_update()) {
                    gs.phase = PHASE_STAGE_INTRO;
                    stage_intro_init();
                }
                break;

            case PHASE_STAGE_INTRO:
                if (stage_intro_update()) {
                    gs.phase = PHASE_COMBAT;
                    combat_init();
                }
                break;

            case PHASE_COMBAT: {
                int result = combat_update();
                if (result == 1) {
                    gs.phase = PHASE_GAME_OVER;
                    gameover_init();
                } else if (result == 2) {
                    gs.phase = PHASE_CYPHER_DROP;
                    cypher_init();
                }
                break;
            }

            case PHASE_CYPHER_DROP:
                if (cypher_update()) {
#ifdef TARGET_HOST
                    if (host_autoplay_enabled) {
                        host_autoplay_stages_cleared++;
                        if (host_autoplay_stage_limit > 0 && host_autoplay_stages_cleared >= host_autoplay_stage_limit) {
                            g_quit = 1;
                            break;
                        }
                    }
#endif
                    u8 next_stage = campaign_next_stage_index(gs.cleared_bosses);
                    if (next_stage < CAMPAIGN_STAGE_COUNT) {
                        campaign_generate_stage(next_stage);
                        gs.phase = PHASE_NARRATIVE;
                        narrative_init();
                    } else {
                        gs.campaign_active = 0;
                        gs.phase = PHASE_TITLE;
                        title_init();
                    }
                }
                break;

            case PHASE_GAME_OVER:
                if (gameover_update()) {
#ifdef TARGET_HOST
                    if (host_autoplay_enabled) {
                        g_quit = 1;
                        break;
                    }
#endif
                    gs.phase = PHASE_TITLE;
                    title_init();
                }
                break;
        }

        audio_sync_profile();

        plat_vsync();
    }

#ifdef TARGET_HOST
#  ifdef HAS_SDL2
    if (sdl_mic_device != 0) SDL_CloseAudioDevice(sdl_mic_device);
    if (sdl_audio_device != 0) SDL_CloseAudioDevice(sdl_audio_device);
    SDL_DestroyTexture(sdl_texture);
    SDL_DestroyRenderer(sdl_renderer);
    SDL_DestroyWindow(sdl_window);
    SDL_Quit();
#  endif
#endif

#ifdef TARGET_3DS
    ctr_profile_write_status();
    ctr_mic_exit();
    if (qtmIsInitialized()) qtmExit();
    gfxExit();
#endif

#ifndef TARGET_GB
    return 0;
#endif
}


/* ═══════════════════════════════════════════════════════════════════════════
 * SECTION: FARIM MANIFEST COMMENTS
 *
 * When building for the FARIM 0.1 container format, the HOST build is
 * compiled and linked; the resulting binary + all assets are packed into
 * a ZIP archive named kaijugaiden_gb.farim by build/farim_pack.py:
 *
 *   python build/farim_pack.py \
 *     --exe  build/kaijugaiden_gb_host.exe \
 *     --assets assets/gb/ \
 *     --manifest build/farim/_farim_manifest/manifest.json \
 *     --out kaijugaiden_gb.farim
 *
 * manifest.json declares:
 *   {
 *     "format":  "FARIM",
 *     "version": "0.1",
 *     "title":   "Kaiju Gaiden!? GB.",
 *     "entry":   "kaijugaiden_gb_host.exe",
 *     "assets":  "assets/gb/",
 *     "target_gb":  "kaijugaiden.gb",
 *     "target_gba": "kaijugaiden.gba"
 *   }
 *
 * The FARIM browser player (farim/player/player.js) executes the host build
 * via a WASM transpile step — or directly runs on Windows/Mac via the
 * native FARIM extractor — just as in the SKAZKA: Terranova project.
 * ═══════════════════════════════════════════════════════════════════════════ */

/*
 * ── END OF kaijugaiden.c ───────────────────────────────────────────────────
 * Kaiju Gaiden!? GB.  /  drIpTECH  /  fanzovNG  /  2026
 */
