#include <stddef.h>
#include <stdint.h>
#include "../build/gba_assets/tommybeta_mode3_assets.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define REG_DISPCNT (*(volatile u16 *)0x04000000)
#define REG_VCOUNT (*(volatile u16 *)0x04000006)
#define REG_KEYINPUT (*(volatile u16 *)0x04000130)

#define REG_DMA3SAD (*(volatile u32 *)0x040000D4)
#define REG_DMA3DAD (*(volatile u32 *)0x040000D8)
#define REG_DMA3CNT (*(volatile u32 *)0x040000DC)

#define REG_SOUNDCNT_L (*(volatile u16 *)0x04000080)
#define REG_SOUNDCNT_H (*(volatile u16 *)0x04000082)
#define REG_SOUNDCNT_X (*(volatile u16 *)0x04000084)
#define REG_SOUND1CNT_L (*(volatile u16 *)0x04000060)
#define REG_SOUND1CNT_H (*(volatile u16 *)0x04000062)
#define REG_SOUND1CNT_X (*(volatile u16 *)0x04000064)
#define REG_SOUND4CNT_L (*(volatile u16 *)0x04000078)
#define REG_SOUND4CNT_H (*(volatile u16 *)0x0400007C)

#define MODE3 0x0003
#define BG2_ENABLE 0x0400

#define DMA_ENABLE 0x80000000u
#define DMA_16BIT 0x00000000u

#define KEY_A 0x0001
#define KEY_B 0x0002
#define KEY_SELECT 0x0004
#define KEY_START 0x0008
#define KEY_RIGHT 0x0010
#define KEY_LEFT 0x0020
#define KEY_UP 0x0040
#define KEY_DOWN 0x0080

#define SCREEN_W 240
#define SCREEN_H 160
#define PLAY_MIN_X 20
#define PLAY_MAX_X 220
#define PLAY_MIN_Y 44
#define PLAY_MAX_Y 124
#define HEAL_HOLD_FRAMES 24
#define TUTORIAL_SKIP_FRAMES 180
#define TUTORIAL_PAGE_COUNT 4
#define CINEMATIC_SKIP_FRAMES 45
#define LOGO_SPLASH_FRAMES 110
#define EWRAM_DATA __attribute__((section(".ewram"), aligned(4)))
#define RGB15(r,g,b) ((r) | ((g) << 5) | ((b) << 10))

typedef enum {
    STATE_LOGO_SPLASH,
    STATE_INTRO_CINEMATIC,
    STATE_TITLE_MENU,
    STATE_FALL_INTRO,
    STATE_TUTORIAL,
    STATE_EXPLORE,
    STATE_PAUSE,
    STATE_CODEX,
    STATE_TITLE_CONFIRM,
    STATE_WIN,
    STATE_GAME_OVER
} GameState;

typedef enum {
    ACTION_IDLE,
    ACTION_BITE,
    ACTION_SPECIAL,
    ACTION_ATTACK,
    ACTION_DODGE,
    ACTION_BLOCK,
    ACTION_PARRY,
    ACTION_HEAL
} ActionKind;

typedef struct {
    const char *name;
    int damage;
    int stamina_cost;
    int heal_gain;
    u16 color;
} SpecialMove;

typedef struct {
    int x;
    int y;
    int prev_x;
    int prev_y;
    int health;
    int max_health;
    int stamina;
    int max_stamina;
    int invuln_timer;
    int stun_timer;
    int attack_cooldown;
    int special_cooldown;
    int action_frame;
    int action_timer;
    int action_kind;
    int facing_x;
    int facing_y;
    int finisher_state;
    int alive;
    int guard_timer;
    int parry_timer;
    int dodge_timer;
    int heal_timer;
    int behavior_id;
    int behavior_timer;
    int behavior_phase;
} Actor;

typedef struct {
    int x;
    int y;
    int frame;
} Prop;

typedef struct {
    int x;
    int y;
    int prev_x;
    int prev_y;
    int frame;
    int timer;
    int dx;
    int dy;
} Critter;

typedef struct {
    int active;
    int x;
    int y;
    int frame;
    int timer;
    int special;
} Effect;

typedef struct {
    int active;
    int timer;
    int damage;
    int stun;
    int frame;
    int special;
    int radius;
    int reach;
    int heal_gain;
    int combo_hit;
    int stamina_drain;
    int special_index;
    int source_is_tommy;
} PendingStrike;

typedef struct {
    int id;
    int move_style;
    int attack_style;
    int aggression;
    int preferred_range;
    int guard_bias;
    int dodge_bias;
    int heal_bias;
    int strafe_dir;
    int cadence;
} EnemyBehavior;

typedef struct {
    u32 magic;
    u32 version;
    u32 checksum;
    int persistent_level;
    int persistent_xp;
    u32 persistent_codex_flags;
    int persistent_runs;
    int persistent_wins;
    int run_valid;
    u32 rng;
    int current_quadrant;
    int current_special;
    int unlocked_specials;
    int defeats_this_run;
    u32 finisher_mask;
    int heal_points;
    int tutorial_pending;
    int level;
    int xp;
    int banner_timer;
    int difficulty;
    int combo_best;
    u32 quadrants_visited;
    Actor tommy;
    Actor mareaou;
} SaveBlock;

typedef struct {
    const char *title;
    const char *body;
} CodexPage;

static volatile u16 *const video = (volatile u16 *)0x06000000;
static volatile u8 *const cart_sram = (volatile u8 *)0x0E000000;
static const int g_cart_persistence_enabled = 1;

static const SpecialMove g_specials[8] = {
    {"CHARGE DASH", 14, 14, 6, RGB15(31, 20, 6)},
    {"SKY CHOMP", 17, 16, 7, RGB15(25, 28, 10)},
    {"TAIL CYCLONE", 15, 15, 8, RGB15(14, 23, 28)},
    {"EMBER SPIT", 16, 17, 7, RGB15(31, 12, 5)},
    {"IRON GUT SLAM", 22, 20, 10, RGB15(20, 20, 23)},
    {"PHANTOM POUNCE", 18, 18, 8, RGB15(22, 12, 28)},
    {"HUNGER HOWL", 12, 14, 12, RGB15(18, 28, 10)},
    {"CROWNBREAKER", 26, 24, 12, RGB15(31, 8, 12)}
};

static const char *const g_attack_names[9] = {
    "SNAP BITE",
    "DASH CLAW",
    "SPORE BURST",
    "ROOT UPPERCUT",
    "MUD LARIAT",
    "DIVE KICK",
    "THRONE HAMMER",
    "TWIN FEINT",
    "GUT ROAR"
};

static const CodexPage g_codex_pages[] = {
    {"TOMMY", "BITE WITH A\nPRESS B WITH A SPECIAL\nHOLD A PLUS B TO HEAL\nSTART OPENS THE MENU"},
    {"FINISHERS", "MAREAOU ENTERS A FINISHER\nSTATE AT ZERO HEALTH\nEND THE FIGHT WITH A\nSPECIAL TO CLAIM A MASK"},
    {"SAVE FLOW", "SAVE GAME WRITES AN\nIMMEDIATE STATE SNAPSHOT\nLOAD GAME RESUMES A RUN\nNEW RUN KEEPS GROWTH"},
    {"CHARGE DASH", "STRAIGHT BURST FINISHER\nLOW WINDUP\nGOOD FOR OPENINGS\nLOW TO MID STAMINA"},
    {"SKY CHOMP", "HIGH ARC CHOMP\nFAST GAP CLOSER\nGOOD VERSUS RETREAT\nMEDIUM STAMINA"},
    {"TAIL CYCLONE", "CLOSE RANGE SPIN\nWIDE CONTACT WINDOW\nGOOD UNDER PRESSURE\nMEDIUM STAMINA"},
    {"EMBER SPIT", "SHORT RANGED FLARE\nTHROWS HEAT FORWARD\nGOOD FOR ZONING\nMEDIUM STAMINA"},
    {"IRON GUT SLAM", "HEAVY BODY DROP\nSLOW BUT DAMAGING\nHIGH STUN OUTPUT\nHIGH STAMINA"},
    {"PHANTOM POUNCE", "FAST REPOSITION STRIKE\nCUTS TO THE FLANK\nGOOD VERSUS GUARDS\nMID HIGH STAMINA"},
    {"HUNGER HOWL", "RECOVERY DRIVEN SPECIAL\nDRAINS ENEMY STAMINA\nBOOSTS HEAL GAINS\nMEDIUM STAMINA"},
    {"CROWNBREAKER", "LATE RUN FINISHER\nMULTI HIT RUSH\nBEST WHEN THE MASK OPENS\nHIGHEST STAMINA"},
    {"BEHAVIOR CORE", "MAREAOU SWAPS AMONG\nONE HUNDRED SIXTY SEVEN\nPARAMETERIZED BEHAVIORS\nDURING EACH QUADRANT"},
    {"BEHAVIOR 1", "STALKER TYPES HOLD RANGE\nTHEN LUNGE INTO A BITE\nWATCH FOR SPORE BURSTS\nAND DODGE TO THE SIDE"},
    {"BEHAVIOR 2", "STRAFER TYPES CIRCLE YOU\nBLOCK INTO FEINTS\nPARRY FLASH MEANS WAIT\nTHEN ANSWER AFTERWARDS"},
    {"BEHAVIOR 3", "RUSH TYPES OVERCOMMIT\nUSE BITE TO BUILD HEAL\nTHEN CASH IT IN WITH\nA PLUS B HOLD"},
    {"BEHAVIOR 4", "LOW HEALTH TYPES MAY HEAL\nBREAK THE CHANNEL WITH\nAGGRESSION OR A SPECIAL\nBEFORE STAMINA RECOVERS"},
    {"GROWTH", "LEVEL AND XP PERSIST\nBETWEEN RUNS\nSPECIAL UNLOCKS RESET\nBUT YOUR BASE STATS STAY"}
};

static GameState g_state = STATE_LOGO_SPLASH;
static u16 g_keys = 0;
static u16 g_prev_keys = 0;
static u32 g_rng = 0xC0FFEE01u;
static int g_frame = 0;
static int g_level = 1;
static int g_xp = 0;
static int g_persistent_level = 1;
static int g_persistent_xp = 0;
static u32 g_persistent_codex_flags = 0x1FFFFu;
static int g_persistent_runs = 0;
static int g_persistent_wins = 0;
static int g_current_special = 0;
static int g_unlocked_specials = 1;
static int g_defeats_this_run = 0;
static u32 g_finisher_mask = 0;
static int g_current_quadrant = 0;
static int g_logo_timer = LOGO_SPLASH_FRAMES;
static int g_intro_panel = 0;
static int g_intro_panel_timer = 0;
static int g_fall_intro_timer = 0;
static int g_tutorial_pending = 1;
static int g_tutorial_page = 0;
static int g_tutorial_skip_timer = 0;
static int g_cinematic_skip_timer = 0;
static int g_pause_selection = 0;
static int g_title_selection = 0;
static int g_title_confirm_selection = 1;
static int g_codex_page = 0;
static int g_banner_timer = 0;
static int g_notice_timer = 0;
#ifndef TOMMYBETA_AUTOPLAY
static int g_heal_hold_timer = 0;
#endif
static int g_heal_points = 0;
static int g_has_saved_run = 0;
static int g_unsaved_progress = 0;
static int g_difficulty = 1;
static int g_sound_enabled = 1;
static int g_combo_count = 0;
static int g_combo_timer = 0;
static int g_combo_best = 0;
static u32 g_quadrants_visited = 0;
static const char *g_notice_text = 0;
static const u16 *g_active_background = 0;
static Actor g_tommy;
static Actor g_mareaou;
static Prop g_props[4];
static Critter g_critters[4];
static Effect g_fx;
static PendingStrike g_player_strike;
static PendingStrike g_enemy_strike;
static EWRAM_DATA SaveBlock g_save_block;
static EWRAM_DATA u16 g_framebuffer[TOMMYBETA_SCREEN_PIXELS];

#ifdef TOMMYBETA_AUTOPLAY
static int g_auto_delay = 0;
#endif

static const u16 g_color_black = RGB15(0, 0, 0);
static const u16 g_color_white = RGB15(31, 31, 31);
static const u16 g_color_panel = RGB15(2, 4, 6);
static const u16 g_color_panel_alt = RGB15(4, 8, 10);
static const u16 g_color_warning = RGB15(31, 24, 8);
static const u16 g_color_heal = RGB15(10, 28, 12);
static const u16 g_color_dim = RGB15(12, 12, 12);
static const u16 g_color_save = RGB15(14, 22, 31);

static const uint8_t font_space[7] = {0, 0, 0, 0, 0, 0, 0};
static const uint8_t font_dash[7] = {0, 0, 0, 31, 0, 0, 0};
static const uint8_t font_colon[7] = {0, 4, 0, 0, 4, 0, 0};
static const uint8_t font_period[7] = {0, 0, 0, 0, 0, 12, 12};
static const uint8_t font_slash[7] = {1, 2, 4, 8, 16, 0, 0};
static const uint8_t font_plus[7] = {0, 4, 4, 31, 4, 4, 0};

static void dma_copy16(const u16 *source, u16 *dest, u32 count) {
    REG_DMA3CNT = 0;
    REG_DMA3SAD = (u32)source;
    REG_DMA3DAD = (u32)dest;
    REG_DMA3CNT = DMA_ENABLE | DMA_16BIT | count;
}

static void wait_vblank(void) {
    while (REG_VCOUNT >= 160) { }
    while (REG_VCOUNT < 160) { }
}

static void present_framebuffer(void) {
    dma_copy16(g_framebuffer, (u16 *)video, TOMMYBETA_SCREEN_PIXELS);
}

static void poll_keys(void) {
    g_prev_keys = g_keys;
    g_keys = (u16)(~REG_KEYINPUT) & 0x03FF;
}

static int key_pressed(u16 key) {
    return (g_keys & key) && !(g_prev_keys & key);
}

static u32 next_rand(void) {
    g_rng = g_rng * 1664525u + 1013904223u;
    return g_rng;
}

static void audio_init(void) {
    REG_SOUNDCNT_X = 0x0080;
    REG_SOUNDCNT_L = 0x1177;
    REG_SOUNDCNT_H = 0x0B0F;
}

static void audio_square(int hz, int envelope) {
    int freq;
    if (!g_sound_enabled) return;
    freq = 2048 - (131072 / hz);
    if (freq < 0) freq = 0;
    if (freq > 2047) freq = 2047;
    REG_SOUND1CNT_L = 0;
    REG_SOUND1CNT_H = (u16)(0x8000 | ((envelope & 0xF) << 12) | 0x0080);
    REG_SOUND1CNT_X = (u16)(0x8000 | (freq & 2047));
}

static void audio_noise(int shape) {
    if (!g_sound_enabled) return;
    REG_SOUND4CNT_L = 0xF000;
    REG_SOUND4CNT_H = (u16)(0x8000 | (shape & 7) | 0x0008);
}

static void plot(int x, int y, u16 color) {
    if (x >= 0 && x < SCREEN_W && y >= 0 && y < SCREEN_H) {
        g_framebuffer[y * SCREEN_W + x] = color;
    }
}

static void rect_fill(int x, int y, int w, int h, u16 color) {
    int px;
    int py;
    if (x < 0) {
        w += x;
        x = 0;
    }
    if (y < 0) {
        h += y;
        y = 0;
    }
    if (x + w > SCREEN_W) w = SCREEN_W - x;
    if (y + h > SCREEN_H) h = SCREEN_H - y;
    if (w <= 0 || h <= 0) return;
    for (py = 0; py < h; ++py) {
        for (px = 0; px < w; ++px) {
            plot(x + px, y + py, color);
        }
    }
}

static void rect_frame(int x, int y, int w, int h, u16 color) {
    rect_fill(x, y, w, 1, color);
    rect_fill(x, y + h - 1, w, 1, color);
    rect_fill(x, y, 1, h, color);
    rect_fill(x + w - 1, y, 1, h, color);
}

static void draw_line(int x0, int y0, int x1, int y1, u16 color) {
    int dx = x1 - x0;
    int dy = y1 - y0;
    int steps = (dx < 0 ? -dx : dx);
    int index;
    if ((dy < 0 ? -dy : dy) > steps) steps = (dy < 0 ? -dy : dy);
    if (steps <= 0) {
        plot(x0, y0, color);
        return;
    }
    for (index = 0; index <= steps; ++index) {
        int px = x0 + (dx * index) / steps;
        int py = y0 + (dy * index) / steps;
        plot(px, py, color);
    }
}

static void m3_blit(const u16 *bitmap) {
    dma_copy16(bitmap, g_framebuffer, TOMMYBETA_SCREEN_PIXELS);
}

static void blit_sprite(const u16 *bitmap, int width, int height, int x, int y) {
    int px;
    int py;
    for (py = 0; py < height; ++py) {
        for (px = 0; px < width; ++px) {
            u16 color = bitmap[py * width + px];
            if (color != TOMMYBETA_TRANSPARENT_COLOR) {
                plot(x + px, y + py, color);
            }
        }
    }
}

static void blit_opaque(const u16 *bitmap, int width, int height, int x, int y) {
    int py;
    for (py = 0; py < height; ++py) {
        int dest_y = y + py;
        if (dest_y < 0 || dest_y >= SCREEN_H) continue;
        if (x >= 0 && x + width <= SCREEN_W) {
            dma_copy16(bitmap + py * width, &g_framebuffer[dest_y * SCREEN_W + x], (u32)width);
        } else {
            int px;
            for (px = 0; px < width; ++px) {
                plot(x + px, dest_y, bitmap[py * width + px]);
            }
        }
    }
}

static const uint8_t *glyph_for(char c) {
    static const uint8_t digits[10][7] = {
        {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},{30,1,1,14,1,1,30},
        {2,6,10,18,31,2,2},{31,16,16,30,1,1,30},{14,16,16,30,17,17,14},{31,1,2,4,8,8,8},
        {14,17,17,14,17,17,14},{14,17,17,15,1,1,14}
    };
    static const uint8_t letters[26][7] = {
        {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{14,17,16,16,16,17,14},{30,17,17,17,17,17,30},
        {31,16,16,30,16,16,31},{31,16,16,30,16,16,16},{14,17,16,23,17,17,15},{17,17,17,31,17,17,17},
        {14,4,4,4,4,4,14},{1,1,1,1,17,17,14},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},
        {17,27,21,17,17,17,17},{17,25,21,19,17,17,17},{14,17,17,17,17,17,14},{30,17,17,30,16,16,16},
        {14,17,17,17,21,18,13},{30,17,17,30,20,18,17},{15,16,16,14,1,1,30},{31,4,4,4,4,4,4},
        {17,17,17,17,17,17,14},{17,17,17,17,17,10,4},{17,17,17,17,21,27,17},{17,17,10,4,10,17,17},
        {17,17,10,4,4,4,4},{31,1,2,4,8,16,31}
    };
    if (c >= '0' && c <= '9') return digits[c - '0'];
    if (c >= 'A' && c <= 'Z') return letters[c - 'A'];
    if (c == '-') return font_dash;
    if (c == ':') return font_colon;
    if (c == '.') return font_period;
    if (c == '/') return font_slash;
    if (c == '+') return font_plus;
    return font_space;
}

static void draw_char(int x, int y, char c, u16 color, int scale) {
    const uint8_t *glyph = glyph_for(c);
    int row;
    int col;
    int sx;
    int sy;
    for (row = 0; row < 7; ++row) {
        for (col = 0; col < 5; ++col) {
            if (glyph[row] & (1 << (4 - col))) {
                for (sy = 0; sy < scale; ++sy) {
                    for (sx = 0; sx < scale; ++sx) {
                        plot(x + col * scale + sx, y + row * scale + sy, color);
                    }
                }
            }
        }
    }
}

static void draw_text(int x, int y, const char *text, u16 color, int scale) {
    int start_x = x;
    while (*text) {
        if (*text == '\n') {
            y += 8 * scale;
            x = start_x;
        } else {
            draw_char(x, y, *text, color, scale);
            x += 6 * scale;
        }
        ++text;
    }
}

static void draw_number(int x, int y, int value, u16 color) {
    char buffer[16];
    int index = 0;
    if (value == 0) {
        buffer[index++] = '0';
    } else {
        char reverse[12];
        int count = 0;
        if (value < 0) {
            buffer[index++] = '-';
            value = -value;
        }
        while (value > 0 && count < 11) {
            reverse[count++] = (char)('0' + (value % 10));
            value /= 10;
        }
        while (count > 0) {
            buffer[index++] = reverse[--count];
        }
    }
    buffer[index] = '\0';
    draw_text(x, y, buffer, color, 1);
}

static int clampi(int value, int minimum, int maximum) {
    if (value < minimum) return minimum;
    if (value > maximum) return maximum;
    return value;
}

static int distance_sq(int ax, int ay, int bx, int by) {
    int dx = ax - bx;
    int dy = ay - by;
    return dx * dx + dy * dy;
}

static int min_i(int left, int right) {
    return left < right ? left : right;
}

static int max_i(int left, int right) {
    return left > right ? left : right;
}

static int count_bits(u32 value) {
    int count = 0;
    while (value) {
        count += (int)(value & 1u);
        value >>= 1;
    }
    return count;
}

static void set_notice(const char *text, int timer) {
    g_notice_text = text;
    g_notice_timer = timer;
}

static void clear_pending_strikes(void) {
    g_player_strike.active = 0;
    g_enemy_strike.active = 0;
}

static void queue_strike(PendingStrike *strike, int source_is_tommy, int timer, int damage, int stun, int frame, int special, int radius, int reach, int heal_gain, int combo_hit, int stamina_drain, int special_index) {
    strike->active = 1;
    strike->source_is_tommy = source_is_tommy;
    strike->timer = timer;
    strike->damage = damage;
    strike->stun = stun;
    strike->frame = frame;
    strike->special = special;
    strike->radius = radius;
    strike->reach = reach;
    strike->heal_gain = heal_gain;
    strike->combo_hit = combo_hit;
    strike->stamina_drain = stamina_drain;
    strike->special_index = special_index;
}

static void clear_run_snapshot_only(void) {
    g_save_block.run_valid = 0;
}

static u32 checksum_save_block(const SaveBlock *block) {
    const u8 *bytes = (const u8 *)block;
    u32 checksum = 0x9E3779B9u;
    int index;
    for (index = 0; index < (int)sizeof(SaveBlock); ++index) {
        if (index >= 8 && index < 12) continue;
        checksum = (checksum << 5) | (checksum >> 27);
        checksum ^= bytes[index];
    }
    return checksum;
}

static void write_save_block_to_storage(const SaveBlock *block) {
    const u8 *bytes = (const u8 *)block;
    int index;
    if (!g_cart_persistence_enabled) return;
    for (index = 0; index < (int)sizeof(SaveBlock); ++index) {
        cart_sram[index] = bytes[index];
    }
}

static void read_save_block_from_storage(SaveBlock *block) {
    u8 *bytes = (u8 *)block;
    int index;
    if (!g_cart_persistence_enabled) {
        for (index = 0; index < (int)sizeof(SaveBlock); ++index) {
            bytes[index] = 0;
        }
        return;
    }
    for (index = 0; index < (int)sizeof(SaveBlock); ++index) {
        bytes[index] = cart_sram[index];
    }
}

static void sync_persistent_progress_to_save(void) {
    g_save_block.magic = 0x54424741u;
    g_save_block.version = 3u;
    g_save_block.persistent_level = g_persistent_level;
    g_save_block.persistent_xp = g_persistent_xp;
    g_save_block.persistent_codex_flags = g_persistent_codex_flags;
    g_save_block.persistent_runs = g_persistent_runs;
    g_save_block.persistent_wins = g_persistent_wins;
}

static void save_persistent_progress(void) {
    sync_persistent_progress_to_save();
    g_save_block.checksum = checksum_save_block(&g_save_block);
    write_save_block_to_storage(&g_save_block);
}

static void save_current_run(void) {
    sync_persistent_progress_to_save();
    g_save_block.run_valid = 1;
    g_save_block.rng = g_rng;
    g_save_block.current_quadrant = g_current_quadrant;
    g_save_block.current_special = g_current_special;
    g_save_block.unlocked_specials = g_unlocked_specials;
    g_save_block.defeats_this_run = g_defeats_this_run;
    g_save_block.finisher_mask = g_finisher_mask;
    g_save_block.heal_points = g_heal_points;
    g_save_block.tutorial_pending = g_tutorial_pending;
    g_save_block.level = g_level;
    g_save_block.xp = g_xp;
    g_save_block.banner_timer = g_banner_timer;
    g_save_block.difficulty = g_difficulty;
    g_save_block.combo_best = g_combo_best;
    g_save_block.quadrants_visited = g_quadrants_visited;
    g_save_block.tommy = g_tommy;
    g_save_block.mareaou = g_mareaou;
    g_save_block.checksum = checksum_save_block(&g_save_block);
    write_save_block_to_storage(&g_save_block);
    g_has_saved_run = 1;
    g_unsaved_progress = 0;
    set_notice("GAME SAVED", 90);
}

static void load_save_block(void) {
    SaveBlock loaded;
    read_save_block_from_storage(&loaded);
    if (loaded.magic == 0x54424741u && (loaded.version == 2u || loaded.version == 3u) && loaded.checksum == checksum_save_block(&loaded)) {
        g_save_block = loaded;
    } else {
        g_save_block.magic = 0x54424741u;
        g_save_block.version = 3u;
        g_save_block.checksum = 0;
        g_save_block.persistent_level = 1;
        g_save_block.persistent_xp = 0;
        g_save_block.persistent_codex_flags = 0x1FFFFu;
        g_save_block.persistent_runs = 0;
        g_save_block.persistent_wins = 0;
        g_save_block.run_valid = 0;
    }
    g_persistent_level = max_i(1, g_save_block.persistent_level);
    g_persistent_xp = max_i(0, g_save_block.persistent_xp);
    g_persistent_codex_flags = g_save_block.persistent_codex_flags ? g_save_block.persistent_codex_flags : 0x1FFFFu;
    g_persistent_runs = max_i(0, g_save_block.persistent_runs);
    g_persistent_wins = max_i(0, g_save_block.persistent_wins);
    g_has_saved_run = g_save_block.run_valid;
}

static void audio_menu_move(void) {
    audio_square(330, 8);
}

static void audio_menu_accept(void) {
    audio_square(392, 10);
}

static void audio_menu_reject(void) {
    audio_noise(4);
}

static void add_xp(int amount) {
    g_xp += amount;
    while (g_xp >= g_level * 100) {
        g_xp -= g_level * 100;
        g_level += 1;
    }
    g_persistent_level = g_level;
    g_persistent_xp = g_xp;
}

static void spend_stamina(Actor *actor, int amount) {
    actor->stamina -= amount;
    if (actor->stamina < 0) actor->stamina = 0;
    if (actor->stamina == 0) {
        actor->stun_timer += 18;
    }
}

static void restore_actor_defaults(Actor *actor) {
    actor->invuln_timer = 0;
    actor->stun_timer = 0;
    actor->attack_cooldown = 0;
    actor->special_cooldown = 0;
    actor->action_frame = 0;
    actor->action_timer = 0;
    actor->action_kind = ACTION_IDLE;
    actor->guard_timer = 0;
    actor->parry_timer = 0;
    actor->dodge_timer = 0;
    actor->heal_timer = 0;
    actor->behavior_id = 0;
    actor->behavior_timer = 0;
    actor->behavior_phase = 0;
    actor->finisher_state = 0;
    actor->alive = 1;
}

static void layout_quadrant(void) {
    int index;
    static const int base_prop_x[4] = {28, 76, 150, 196};
    static const int base_prop_y[4] = {48, 92, 58, 98};
    static const int base_critter_x[4] = {44, 98, 136, 184};
    static const int base_critter_y[4] = {64, 78, 104, 54};
    for (index = 0; index < 4; ++index) {
        int shift = (int)((g_current_quadrant * 11 + index * 17) % 24) - 12;
        g_props[index].frame = (g_current_quadrant + index) % 4;
        g_props[index].x = clampi(base_prop_x[index] + shift, 8, 200);
        g_props[index].y = clampi(base_prop_y[index] + shift / 2, 36, 112);

        g_critters[index].frame = index & 3;
        g_critters[index].x = clampi(base_critter_x[index] - shift, 18, 206);
        g_critters[index].y = clampi(base_critter_y[index] + shift / 3, 42, 118);
        g_critters[index].prev_x = g_critters[index].x;
        g_critters[index].prev_y = g_critters[index].y;
        g_critters[index].timer = 12 + index * 4;
        g_critters[index].dx = (index & 1) ? 1 : -1;
        g_critters[index].dy = (index & 2) ? 1 : -1;
    }
}

static int difficulty_hp_scale(int base) {
    if (g_difficulty == 0) return base * 4 / 5;
    if (g_difficulty == 2) return base * 13 / 10;
    return base;
}

static int difficulty_dmg_scale(int base) {
    if (g_difficulty == 0) return max_i(1, base * 3 / 4);
    if (g_difficulty == 2) return base * 5 / 4;
    return base;
}

static void load_quadrant(int quadrant_index) {
    g_current_quadrant = quadrant_index % TOMMYBETA_QUADRANT_COUNT;
    g_active_background = tommybeta_quadrant_bitmaps[g_current_quadrant];
    g_quadrants_visited |= (1u << g_current_quadrant);

    g_tommy.max_health = 84 + g_level * 6;
    g_tommy.max_stamina = 72 + g_level * 3;
    g_tommy.health = g_tommy.max_health;
    g_tommy.stamina = g_tommy.max_stamina;
    g_tommy.x = 40;
    g_tommy.y = 108;
    g_tommy.prev_x = g_tommy.x;
    g_tommy.prev_y = g_tommy.y;
    g_tommy.facing_x = 0;
    g_tommy.facing_y = 1;
    restore_actor_defaults(&g_tommy);

    g_mareaou.max_health = difficulty_hp_scale(56 + g_current_quadrant * 8 + g_level * 2);
    g_mareaou.max_stamina = difficulty_hp_scale(62 + g_current_quadrant * 4 + g_level * 2);
    g_mareaou.health = g_mareaou.max_health;
    g_mareaou.stamina = g_mareaou.max_stamina;
    g_mareaou.x = 184;
    g_mareaou.y = 72;
    g_mareaou.prev_x = g_mareaou.x;
    g_mareaou.prev_y = g_mareaou.y;
    g_mareaou.facing_x = -1;
    g_mareaou.facing_y = 0;
    restore_actor_defaults(&g_mareaou);
    g_mareaou.attack_cooldown = 18;
    g_mareaou.special_cooldown = 42;

    g_fx.active = 0;
    clear_pending_strikes();
    g_combo_count = 0;
    g_combo_timer = 0;
    g_banner_timer = 72;
    layout_quadrant();
}

static void begin_run(void) {
    g_persistent_runs += 1;
    g_level = g_persistent_level;
    g_xp = g_persistent_xp;
    g_current_special = 0;
    g_unlocked_specials = 1;
    g_defeats_this_run = 0;
    g_finisher_mask = 0;
    g_heal_points = 0;
    g_tutorial_pending = 1;
    g_tutorial_page = 0;
    g_pause_selection = 0;
    g_unsaved_progress = 1;
    g_combo_count = 0;
    g_combo_timer = 0;
    g_quadrants_visited = 0;
    load_quadrant((int)(next_rand() % TOMMYBETA_QUADRANT_COUNT));
    g_fall_intro_timer = TOMMYBETA_HAVE_FALL_INTRO ? 90 : 0;
    g_state = STATE_FALL_INTRO;
}

static void restore_saved_run(void) {
    if (!g_has_saved_run || !g_save_block.run_valid) {
        audio_menu_reject();
        set_notice("NO SAVE GAME", 90);
        return;
    }

    g_rng = g_save_block.rng;
    g_level = max_i(1, g_save_block.level);
    g_xp = max_i(0, g_save_block.xp);
    g_persistent_level = max_i(g_persistent_level, g_level);
    g_persistent_xp = g_xp;
    load_quadrant(g_save_block.current_quadrant);
    g_current_special = clampi(g_save_block.current_special, 0, 7);
    g_unlocked_specials = clampi(g_save_block.unlocked_specials, 1, 8);
    g_defeats_this_run = max_i(0, g_save_block.defeats_this_run);
    g_finisher_mask = g_save_block.finisher_mask;
    g_heal_points = max_i(0, g_save_block.heal_points);
    g_tutorial_pending = g_save_block.tutorial_pending;
    g_tutorial_page = 0;
    g_banner_timer = g_save_block.banner_timer;
    g_difficulty = clampi(g_save_block.difficulty, 0, 2);
    g_combo_best = max_i(0, g_save_block.combo_best);
    g_quadrants_visited = g_save_block.quadrants_visited;
    g_tommy = g_save_block.tommy;
    g_mareaou = g_save_block.mareaou;
    g_state = STATE_EXPLORE;
    g_pause_selection = 0;
    g_codex_page = 0;
    g_unsaved_progress = 0;
    set_notice("RUN LOADED", 90);
    audio_menu_accept();
}

static void move_actor(Actor *actor, int dx, int dy, int speed) {
    if (actor->stun_timer > 0 || actor->dodge_timer > 0) speed = max_i(speed, 3);
    actor->prev_x = actor->x;
    actor->prev_y = actor->y;
    actor->x = clampi(actor->x + dx * speed, PLAY_MIN_X, PLAY_MAX_X);
    actor->y = clampi(actor->y + dy * speed, PLAY_MIN_Y, PLAY_MAX_Y);
    if (dx != 0 || dy != 0) {
        actor->facing_x = dx;
        actor->facing_y = dy;
    }
}

static int actor_in_front(const Actor *attacker, const Actor *target, int radius) {
    int dx = target->x - attacker->x;
    int dy = target->y - attacker->y;
    if (distance_sq(attacker->x, attacker->y, target->x, target->y) > radius * radius) {
        return 0;
    }
    if (attacker->facing_x == 0 && attacker->facing_y == 0) return 1;
    return dx * attacker->facing_x + dy * attacker->facing_y >= -8;
}

static void start_fx(int x, int y, int frame, int special) {
    g_fx.active = 1;
    g_fx.x = x;
    g_fx.y = y;
    g_fx.frame = frame;
    g_fx.special = special;
    g_fx.timer = special ? 14 : 10;
}

static int actor_contact_x(const Actor *actor, int reach) {
    return actor->x + actor->facing_x * reach;
}

static int actor_contact_y(const Actor *actor, int reach) {
    return actor->y - 10 + actor->facing_y * max_i(4, reach / 2);
}

static void start_actor_fx(const Actor *source, const Actor *target, int frame, int special, int reach) {
    int anchor_x = source ? actor_contact_x(source, reach) : (target ? target->x : SCREEN_W / 2);
    int anchor_y = source ? actor_contact_y(source, reach) : (target ? target->y - 10 : SCREEN_H / 2);
    if (target) {
        anchor_x = (anchor_x + target->x) / 2;
        anchor_y = (anchor_y + target->y - 10) / 2;
    }
    start_fx(anchor_x - (TOMMYBETA_FX_W / 2), anchor_y - (TOMMYBETA_FX_H / 2), frame, special);
}

static int deal_damage(Actor *attacker, Actor *target, int damage, int stun, int effect_frame, int effect_special) {
    if (!target->alive) return 0;
    if (target->dodge_timer > 0) return 0;
    if (target->parry_timer > 0) {
        target->parry_timer = 0;
        attacker->stun_timer += 18;
        attacker->action_kind = ACTION_PARRY;
        attacker->action_timer = 12;
        start_actor_fx(target, attacker, effect_frame, effect_special, 12);
        audio_noise(6);
        return 0;
    }
    if (target->guard_timer > 0) {
        damage = max_i(1, damage / 2);
        stun = max_i(1, stun / 2);
        audio_square(220, 6);
    }
    if (target->invuln_timer > 0) return 0;

    target->health -= damage;
    target->invuln_timer = 10;
    target->stun_timer += stun;
    start_actor_fx(attacker, target, effect_frame, effect_special, 14);
    audio_noise(3);
    return 1;
}

static void heal_tommy_between_quadrants(void) {
    g_tommy.health += 16;
    if (g_tommy.health > g_tommy.max_health) g_tommy.health = g_tommy.max_health;
    g_tommy.stamina = g_tommy.max_stamina;
}

static void unlock_next_special(void) {
    if (g_unlocked_specials < 8) {
        g_unlocked_specials += 1;
        audio_square(440, 12);
        set_notice("SPECIAL UNLOCKED", 90);
    }
}

static int next_unvisited_quadrant(void) {
    int index;
    int start = (g_current_quadrant + 1) % TOMMYBETA_QUADRANT_COUNT;
    for (index = 0; index < TOMMYBETA_QUADRANT_COUNT; ++index) {
        int candidate = (start + index) % TOMMYBETA_QUADRANT_COUNT;
        if (!(g_quadrants_visited & (1u << candidate))) return candidate;
    }
    return (g_current_quadrant + 1) % TOMMYBETA_QUADRANT_COUNT;
}

static void victory_finish(int special_index) {
    g_finisher_mask |= (1u << special_index);
    g_defeats_this_run += 1;
    if (g_combo_count > g_combo_best) g_combo_best = g_combo_count;
    if ((g_defeats_this_run % 3) == 0) {
        unlock_next_special();
    }
    add_xp(30 + special_index * 8);
    g_persistent_codex_flags |= (1u << min_i(15, 3 + special_index));
    heal_tommy_between_quadrants();
    audio_square(330, 10);
    g_unsaved_progress = 1;
    if (g_finisher_mask == 0xFFu) {
        g_persistent_wins += 1;
        g_state = STATE_WIN;
        set_notice("FULL MASK COMPLETE", 120);
        save_persistent_progress();
    } else {
        load_quadrant(next_unvisited_quadrant());
        set_notice("NEXT QUADRANT", 90);
    }
}

static void player_bite(void) {
    int combo = (g_frame / 6) % 3;
    if (g_tommy.attack_cooldown > 0 || g_tommy.stun_timer > 0) return;
    spend_stamina(&g_tommy, 8);
    g_tommy.attack_cooldown = 14;
    g_tommy.action_timer = 12;
    g_tommy.action_frame = combo;
    g_tommy.action_kind = ACTION_BITE;
    queue_strike(&g_player_strike, 1, 4, 8 + combo * 2 + min_i(8, g_combo_count / 3), 6, combo, 0, 30, 14, 6 + combo * 2, 1, 0, -1);
    audio_square(176 + combo * 18, 8);
    g_unsaved_progress = 1;
}

static void player_special(void) {
    const SpecialMove *move = &g_specials[g_current_special];
    if (g_tommy.special_cooldown > 0 || g_tommy.stun_timer > 0) return;
    if (g_tommy.stamina < move->stamina_cost) return;
    spend_stamina(&g_tommy, move->stamina_cost);
    g_tommy.special_cooldown = 28;
    g_tommy.action_timer = 18;
    g_tommy.action_frame = g_current_special;
    g_tommy.action_kind = ACTION_SPECIAL;
    start_actor_fx(&g_tommy, NULL, g_current_special, 1, 18);
    queue_strike(&g_player_strike, 1, 6, move->damage, 12, g_current_special, 1, 48, 18, move->heal_gain, 0, 0, g_current_special);
    audio_square(218 + g_current_special * 14, 12);
    g_unsaved_progress = 1;
}

static void player_heal(void) {
    int spend = min_i(g_heal_points, 24 + g_level * 2);
    int heal_amount;
    if (g_heal_points < 18) return;
    heal_amount = max_i(8, spend / 2);
    g_heal_points -= spend;
    g_tommy.health += heal_amount;
    if (g_tommy.health > g_tommy.max_health) g_tommy.health = g_tommy.max_health;
    g_tommy.action_kind = ACTION_HEAL;
    g_tommy.action_frame = 6;
    g_tommy.action_timer = 18;
    g_tommy.heal_timer = 18;
    spend_stamina(&g_tommy, 6);
    start_actor_fx(&g_tommy, NULL, 6, 1, 2);
    audio_square(262, 12);
    g_unsaved_progress = 1;
}

static EnemyBehavior behavior_from_id(int id) {
    EnemyBehavior behavior;
    int normalized = id % 167;
    behavior.id = normalized;
    behavior.move_style = normalized % 5;
    behavior.attack_style = (normalized / 5) % 9;
    behavior.aggression = 1 + ((normalized / 9) % 4);
    behavior.preferred_range = 18 + ((normalized / 7) % 4) * 8;
    behavior.guard_bias = (normalized / 27) % 3;
    behavior.dodge_bias = (normalized / 18) % 3;
    behavior.heal_bias = (normalized / 54) % 3;
    behavior.strafe_dir = ((normalized / 13) & 1) ? 1 : -1;
    behavior.cadence = 12 + (normalized % 6) * 3;
    return behavior;
}

static void choose_enemy_behavior(void) {
    int seed = (int)(next_rand() % 167u);
    int health_band = (g_mareaou.health * 100) / max_i(1, g_mareaou.max_health);
    int offset = g_current_quadrant * 19 + g_defeats_this_run * 7;
    if (health_band < 35) offset += 81;
    else if (health_band < 60) offset += 33;
    g_mareaou.behavior_id = (seed + offset) % 167;
    g_mareaou.behavior_timer = 30 + (g_mareaou.behavior_id % 5) * 9;
    g_mareaou.behavior_phase += 1;
}

static void enemy_block(void) {
    if (g_mareaou.guard_timer > 0 || g_mareaou.dodge_timer > 0) return;
    g_mareaou.guard_timer = 12;
    g_mareaou.action_kind = ACTION_BLOCK;
    g_mareaou.action_timer = 12;
    g_mareaou.action_frame = 0;
    audio_square(240, 6);
}

static void enemy_parry(void) {
    if (g_mareaou.parry_timer > 0 || g_mareaou.dodge_timer > 0) return;
    g_mareaou.parry_timer = 8;
    g_mareaou.action_kind = ACTION_PARRY;
    g_mareaou.action_timer = 10;
    g_mareaou.action_frame = 1;
    audio_square(280, 6);
}

static void enemy_dodge(int side) {
    if (g_mareaou.dodge_timer > 0) return;
    g_mareaou.dodge_timer = 10;
    g_mareaou.action_kind = ACTION_DODGE;
    g_mareaou.action_timer = 10;
    g_mareaou.action_frame = 2;
    move_actor(&g_mareaou, g_tommy.facing_y * side, -g_tommy.facing_x * side, 4);
    audio_square(320, 8);
}

static void enemy_heal(void) {
    if (g_mareaou.heal_timer > 0 || g_mareaou.stamina < 12) return;
    g_mareaou.heal_timer = 20;
    g_mareaou.action_kind = ACTION_HEAL;
    g_mareaou.action_timer = 20;
    g_mareaou.action_frame = 6;
    g_mareaou.health += 10 + g_current_quadrant * 2;
    if (g_mareaou.health > g_mareaou.max_health) g_mareaou.health = g_mareaou.max_health;
    spend_stamina(&g_mareaou, 12);
    start_actor_fx(&g_mareaou, NULL, 6, 1, 2);
    audio_square(210, 10);
}

static void enemy_attack_style(int style) {
    int attack_frame = style % 7;
    int range = 28;
    int damage = difficulty_dmg_scale(5 + style);
    int stun = 4 + (style % 4) * 2;

    if (!g_mareaou.alive || g_mareaou.finisher_state) return;
    if (g_mareaou.attack_cooldown > 0 || g_mareaou.stun_timer > 0) return;

    if (style == 2 || style == 8) range = 40;
    if (style == 4 || style == 6) damage += 4;
    if (style == 7) stun += 6;
    if (distance_sq(g_mareaou.x, g_mareaou.y, g_tommy.x, g_tommy.y) > range * range) return;

    g_mareaou.attack_cooldown = 18 + (style % 3) * 4;
    g_mareaou.action_kind = ACTION_ATTACK;
    g_mareaou.action_timer = 15 + (style % 3) * 2;
    g_mareaou.action_frame = attack_frame;
    spend_stamina(&g_mareaou, 5 + (style % 4));

    if (style == 1 || style == 5) {
        move_actor(&g_mareaou, g_mareaou.facing_x, g_mareaou.facing_y, 3);
    }
    queue_strike(&g_enemy_strike, 0, 5, damage, stun, attack_frame, 0, range + 6, 16, 0, 0, style == 8 ? 8 : 0, -1);
    audio_square(144 + style * 12, 7);
}

static void resolve_pending_strike(PendingStrike *strike) {
    Actor *attacker;
    Actor *target;
    if (!strike->active) return;
    if (strike->timer > 0) {
        strike->timer -= 1;
        if (strike->timer > 0) return;
    }

    attacker = strike->source_is_tommy ? &g_tommy : &g_mareaou;
    target = strike->source_is_tommy ? &g_mareaou : &g_tommy;
    strike->active = 0;
    if (!attacker->alive || !target->alive) return;
    if (!actor_in_front(attacker, target, strike->radius)) return;

    if (deal_damage(attacker, target, strike->damage, strike->stun, strike->frame, strike->special)) {
        if (strike->source_is_tommy) {
            if (strike->combo_hit) {
                g_combo_count += 1;
                g_combo_timer = 60;
            }
            if (strike->heal_gain > 0) {
                g_heal_points = min_i(160, g_heal_points + strike->heal_gain);
            }
            if (strike->special_index >= 0 && (g_mareaou.finisher_state || g_mareaou.health <= 0)) {
                g_mareaou.health = 0;
                g_mareaou.alive = 0;
                victory_finish(strike->special_index);
                return;
            }
            if (strike->combo_hit && g_mareaou.health <= 0) {
                g_mareaou.health = 1;
                g_mareaou.finisher_state = 1;
                g_mareaou.stun_timer = 999;
                g_mareaou.action_kind = ACTION_PARRY;
                g_mareaou.action_timer = 22;
                set_notice("USE A SPECIAL TO FINISH", 90);
            }
        } else if (strike->stamina_drain > 0) {
            g_tommy.stamina = max_i(0, g_tommy.stamina - strike->stamina_drain);
        }
    }
}

static void update_pending_strikes(void) {
    resolve_pending_strike(&g_player_strike);
    resolve_pending_strike(&g_enemy_strike);
}

static void update_critters(void) {
    int index;
    for (index = 0; index < 4; ++index) {
        Critter *critter = &g_critters[index];
        critter->prev_x = critter->x;
        critter->prev_y = critter->y;
        critter->timer -= 1;
        if (critter->timer <= 0) {
            critter->dx = ((int)(next_rand() % 3u)) - 1;
            critter->dy = ((int)(next_rand() % 3u)) - 1;
            critter->timer = 16 + (int)(next_rand() % 20u);
        }
        critter->x = clampi(critter->x + critter->dx, PLAY_MIN_X, PLAY_MAX_X - 8);
        critter->y = clampi(critter->y + critter->dy, PLAY_MIN_Y, PLAY_MAX_Y - 8);
        critter->frame = (critter->frame + 1) & 3;
    }
}

static void tick_actor(Actor *actor) {
    if (actor->invuln_timer > 0) actor->invuln_timer -= 1;
    if (actor->stun_timer > 0) actor->stun_timer -= 1;
    if (actor->attack_cooldown > 0) actor->attack_cooldown -= 1;
    if (actor->special_cooldown > 0) actor->special_cooldown -= 1;
    if (actor->action_timer > 0) actor->action_timer -= 1;
    else actor->action_kind = ACTION_IDLE;
    if (actor->guard_timer > 0) actor->guard_timer -= 1;
    if (actor->parry_timer > 0) actor->parry_timer -= 1;
    if (actor->dodge_timer > 0) actor->dodge_timer -= 1;
    if (actor->heal_timer > 0) actor->heal_timer -= 1;
}

static void update_enemy_ai(void) {
    EnemyBehavior behavior;
    int distance;
    int dx = 0;
    int dy = 0;
    int lateral = 0;

    if (!g_mareaou.alive || g_mareaou.finisher_state) return;

    if (g_mareaou.behavior_timer <= 0) {
        choose_enemy_behavior();
    }
    g_mareaou.behavior_timer -= 1;
    behavior = behavior_from_id(g_mareaou.behavior_id);
    distance = distance_sq(g_mareaou.x, g_mareaou.y, g_tommy.x, g_tommy.y);

    if (g_mareaou.health < g_mareaou.max_health / 3 && behavior.heal_bias > 0 && g_mareaou.stamina > 14 && (next_rand() & 7u) == 0) {
        enemy_heal();
        return;
    }

    if (g_tommy.action_timer > 0 && actor_in_front(&g_tommy, &g_mareaou, 34)) {
        if (behavior.guard_bias == 2 && (next_rand() & 3u) == 0) {
            enemy_parry();
            return;
        }
        if (behavior.guard_bias >= 1 && (next_rand() & 1u) == 0) {
            enemy_block();
        }
        if (behavior.dodge_bias >= 1 && (next_rand() & 1u) == 0) {
            enemy_dodge(behavior.strafe_dir);
            return;
        }
    }

    if (g_mareaou.stun_timer <= 0 && !(g_enemy_strike.active && g_enemy_strike.timer > 1)) {
        if (g_tommy.x > g_mareaou.x + 10) dx = 1;
        if (g_tommy.x < g_mareaou.x - 10) dx = -1;
        if (g_tommy.y > g_mareaou.y + 10) dy = 1;
        if (g_tommy.y < g_mareaou.y - 10) dy = -1;

        lateral = behavior.strafe_dir;
        if (behavior.move_style == 0) {
            if (distance > behavior.preferred_range * behavior.preferred_range) {
                move_actor(&g_mareaou, dx, dy, 1 + (behavior.aggression > 2));
            }
        } else if (behavior.move_style == 1) {
            move_actor(&g_mareaou, lateral * dy, -lateral * dx, 2);
        } else if (behavior.move_style == 2) {
            if (distance < 22 * 22) move_actor(&g_mareaou, -dx, -dy, 2);
            else move_actor(&g_mareaou, dx, dy, 1 + behavior.aggression / 2);
        } else if (behavior.move_style == 3) {
            if ((g_mareaou.behavior_phase & 1) == 0) move_actor(&g_mareaou, dx + lateral * dy, dy - lateral * dx, 2);
            else move_actor(&g_mareaou, -dx + lateral * dy, -dy - lateral * dx, 2);
        } else {
            if (distance > 26 * 26) move_actor(&g_mareaou, dx, dy, 3);
            else move_actor(&g_mareaou, lateral * dy, -lateral * dx, 2);
        }
    }

    if (g_frame % max_i(8, behavior.cadence - behavior.aggression) == 0) {
        enemy_attack_style(behavior.attack_style);
    }
}

#ifdef TOMMYBETA_AUTOPLAY
static int autoplay_choose_target_special(void) {
    int index;
    for (index = g_unlocked_specials - 1; index >= 0; --index) {
        if ((g_finisher_mask & (1u << index)) == 0) return index;
    }
    return g_unlocked_specials - 1;
}

static void autoplay_update(void) {
    int target_special;
    int dx;
    int dy;
    if (g_auto_delay > 0) {
        g_auto_delay -= 1;
        return;
    }

    if (g_state == STATE_LOGO_SPLASH) {
        g_logo_timer = 0;
        g_state = STATE_INTRO_CINEMATIC;
        g_intro_panel = 0;
        g_intro_panel_timer = 90;
        return;
    }
    if (g_state == STATE_INTRO_CINEMATIC) {
        g_state = STATE_TITLE_MENU;
        return;
    }
    if (g_state == STATE_TITLE_MENU) {
        begin_run();
        g_auto_delay = 12;
        return;
    }
    if (g_state == STATE_FALL_INTRO) {
        g_fall_intro_timer = 0;
        g_state = STATE_TUTORIAL;
        g_auto_delay = 8;
        return;
    }
    if (g_state == STATE_TUTORIAL) {
        g_tutorial_pending = 0;
        g_state = STATE_EXPLORE;
        g_auto_delay = 8;
        return;
    }
    if (g_state != STATE_EXPLORE) return;

    target_special = autoplay_choose_target_special();
    g_current_special = target_special;
    dx = (g_mareaou.x > g_tommy.x + 10) ? 1 : (g_mareaou.x < g_tommy.x - 10 ? -1 : 0);
    dy = (g_mareaou.y > g_tommy.y + 10) ? 1 : (g_mareaou.y < g_tommy.y - 10 ? -1 : 0);
    if (!g_mareaou.finisher_state && distance_sq(g_tommy.x, g_tommy.y, g_mareaou.x, g_mareaou.y) > 30 * 30) {
        move_actor(&g_tommy, dx, dy, 2);
        g_auto_delay = 1;
        return;
    }
    if (g_tommy.health < g_tommy.max_health / 2 && g_heal_points >= 24) {
        player_heal();
        g_auto_delay = 10;
        return;
    }
    if (g_mareaou.finisher_state || g_mareaou.health <= g_specials[target_special].damage + 4) {
        player_special();
        g_auto_delay = 4;
    } else {
        player_bite();
        g_auto_delay = 3;
    }
}
#endif

static void handle_tutorial_skip(void) {
    if ((g_keys & (KEY_START | KEY_SELECT)) == (KEY_START | KEY_SELECT)) {
        g_tutorial_skip_timer += 1;
        if (g_tutorial_skip_timer >= TUTORIAL_SKIP_FRAMES) {
            g_tutorial_pending = 0;
            g_state = STATE_EXPLORE;
            g_tutorial_skip_timer = 0;
            set_notice("TUTORIAL SKIPPED", 90);
            audio_menu_accept();
        }
    } else {
        g_tutorial_skip_timer = 0;
    }
}

static void update_explore(void) {
#ifndef TOMMYBETA_AUTOPLAY
    int move_x = 0;
    int move_y = 0;
#endif

    if (key_pressed(KEY_START)) {
        g_pause_selection = 0;
        g_state = STATE_PAUSE;
        return;
    }

#ifdef TOMMYBETA_AUTOPLAY
    autoplay_update();
#endif

    tick_actor(&g_tommy);
    tick_actor(&g_mareaou);
    if (g_combo_timer > 0) {
        g_combo_timer -= 1;
        if (g_combo_timer == 0) g_combo_count = 0;
    }
    if (g_banner_timer > 0) g_banner_timer -= 1;
    if (g_notice_timer > 0) g_notice_timer -= 1;
    if (g_fx.active) {
        g_fx.timer -= 1;
        if (g_fx.timer <= 0) g_fx.active = 0;
    }
    if ((g_frame & 7) == 0) {
        if (g_tommy.stamina < g_tommy.max_stamina) g_tommy.stamina += 1;
        if (g_mareaou.stamina < g_mareaou.max_stamina) g_mareaou.stamina += 1;
    }

#ifndef TOMMYBETA_AUTOPLAY
    if (g_keys & KEY_LEFT) move_x = -1;
    if (g_keys & KEY_RIGHT) move_x = 1;
    if (g_keys & KEY_UP) move_y = -1;
    if (g_keys & KEY_DOWN) move_y = 1;

    if (g_tommy.stun_timer <= 0) {
        if (!(g_player_strike.active && g_player_strike.timer > 1)) {
            move_actor(&g_tommy, move_x, move_y, 2);
        }

        if ((g_keys & (KEY_A | KEY_B)) == (KEY_A | KEY_B)) {
            g_heal_hold_timer += 1;
            if (g_heal_hold_timer >= HEAL_HOLD_FRAMES) {
                player_heal();
                g_heal_hold_timer = 0;
            }
        } else {
            g_heal_hold_timer = 0;
            if (key_pressed(KEY_SELECT) && g_unlocked_specials > 1) {
                g_current_special = (g_current_special + 1) % g_unlocked_specials;
                audio_menu_move();
            }
            if (key_pressed(KEY_A)) player_bite();
            if (key_pressed(KEY_B)) player_special();
        }
    }
#endif

    update_enemy_ai();
    update_pending_strikes();
    update_critters();

    if (g_tommy.health <= 0) {
        g_state = STATE_GAME_OVER;
        audio_noise(7);
        save_persistent_progress();
    }
    g_unsaved_progress = 1;
}

static const u16 *select_tommy_frame(void) {
    int pulse = (g_frame / 4) & 1;
    if (g_tommy.action_timer > 0) {
        if (g_tommy.action_kind == ACTION_BITE) return tommybeta_tommy_bite_frames[g_tommy.action_frame % 3];
        if (g_tommy.action_kind == ACTION_SPECIAL) return tommybeta_tommy_special_frames[g_tommy.action_frame % 8];
        if (g_tommy.action_kind == ACTION_DODGE) return tommybeta_tommy_support_frames[(2 + pulse) % TOMMYBETA_SUPPORT_FRAME_COUNT];
        if (g_tommy.action_kind == ACTION_BLOCK) return tommybeta_tommy_support_frames[0];
        if (g_tommy.action_kind == ACTION_PARRY) return tommybeta_tommy_support_frames[(1 + pulse) % TOMMYBETA_SUPPORT_FRAME_COUNT];
        if (g_tommy.action_kind == ACTION_HEAL) return tommybeta_tommy_support_frames[(6 + pulse) % TOMMYBETA_SUPPORT_FRAME_COUNT];
        return tommybeta_tommy_support_frames[g_tommy.action_frame % TOMMYBETA_SUPPORT_FRAME_COUNT];
    }
    return tommybeta_tommy_idle_frames[(g_frame / 8) % 4];
}

static const u16 *select_mareaou_frame(void) {
    int pulse = (g_frame / 4) & 1;
    if (g_mareaou.action_timer > 0) {
        if (g_mareaou.action_kind != ACTION_ATTACK) {
            if (g_mareaou.action_kind == ACTION_DODGE) return tommybeta_mareaou_support_frames[(2 + pulse) % TOMMYBETA_SUPPORT_FRAME_COUNT];
            if (g_mareaou.action_kind == ACTION_BLOCK) return tommybeta_mareaou_support_frames[0];
            if (g_mareaou.action_kind == ACTION_PARRY) return tommybeta_mareaou_support_frames[(1 + pulse) % TOMMYBETA_SUPPORT_FRAME_COUNT];
            if (g_mareaou.action_kind == ACTION_HEAL) return tommybeta_mareaou_support_frames[(6 + pulse) % TOMMYBETA_SUPPORT_FRAME_COUNT];
            return tommybeta_mareaou_support_frames[g_mareaou.action_frame % TOMMYBETA_SUPPORT_FRAME_COUNT];
        }
        return tommybeta_mareaou_attack_frames[g_mareaou.action_frame % 7];
    }
    return tommybeta_mareaou_idle_frames[(g_frame / 8) % 4];
}

static void draw_terrain_overlay_layer(int start, int count) {
    static const int overlay_x[4] = {18, 72, 140, 192};
    static const int overlay_y[4] = {46, 88, 58, 102};
    int index;
    int end = min_i(4, start + count);
    for (index = start; index < end; ++index) {
        int frame = (g_current_quadrant * 3 + index + ((g_frame / 24) % 2) * 4) % TOMMYBETA_TERRAIN_OVERLAY_COUNT;
        blit_sprite(tommybeta_terrain_overlay_frames[frame], TOMMYBETA_PROP_W, TOMMYBETA_PROP_H, overlay_x[index], overlay_y[index]);
    }
}

static void draw_actor_shadow(const Actor *actor, u16 color) {
    rect_fill(actor->x - 10, actor->y + 16, 20, 3, color);
    rect_fill(actor->x - 6, actor->y + 15, 12, 5, color);
}

static void draw_status_chip(int x, int y, const char *text, u16 outline, u16 text_color) {
    int width = 12;
    const char *cursor = text;
    while (*cursor) {
        width += 6;
        ++cursor;
    }
    rect_fill(x, y, width, 10, g_color_panel_alt);
    rect_frame(x, y, width, 10, outline);
    draw_text(x + 4, y + 2, text, text_color, 1);
}

static void draw_actor_status(const Actor *actor, int is_tommy) {
    int left = actor->x - 18;
    int top = actor->y - 40;
    if (!actor->alive) return;
    if (!is_tommy && g_mareaou.finisher_state) {
        draw_status_chip(left - 2, top, "FINISH", g_color_warning, g_color_warning);
        return;
    }
    if (actor->stun_timer > 10) {
        draw_status_chip(left, top, "STUN", g_color_warning, g_color_white);
    } else if (actor->parry_timer > 0) {
        draw_status_chip(left, top, "PARRY", g_color_save, g_color_white);
    } else if (actor->guard_timer > 0) {
        draw_status_chip(left, top, "GUARD", g_color_save, g_color_white);
    } else if (actor->heal_timer > 0) {
        draw_status_chip(left, top, "HEAL", g_color_heal, g_color_heal);
    }
}

static void draw_world_cohesion(void) {
    int index;
    rect_fill(0, 34, SCREEN_W, 2, RGB15(3, 5, 4));
    rect_fill(0, 122, SCREEN_W, 4, RGB15(4, 5, 3));
    rect_fill(0, 126, SCREEN_W, 2, RGB15(2, 3, 2));
    for (index = 0; index < 3; ++index) {
        draw_line(g_props[index].x + 16, g_props[index].y + 22, g_props[index + 1].x + 16, g_props[index + 1].y + 22, RGB15(5, 8, 5));
    }
}

static void draw_actor_sprite(const Actor *actor, const u16 *frame, u16 highlight, int finisher) {
    int left = actor->x - (TOMMYBETA_SPRITE_W / 2);
    int top = actor->y - (TOMMYBETA_SPRITE_H / 2);
    blit_sprite(frame, TOMMYBETA_SPRITE_W, TOMMYBETA_SPRITE_H, left, top);

    if (actor->invuln_timer > 0 && ((g_frame / 2) & 1)) {
        rect_frame(left, top, TOMMYBETA_SPRITE_W, TOMMYBETA_SPRITE_H, highlight);
    }
    if (finisher) {
        rect_frame(left - 1, top - 1, TOMMYBETA_SPRITE_W + 2, TOMMYBETA_SPRITE_H + 2, g_color_warning);
        if ((g_frame / 4) & 1) {
            rect_fill(actor->x - 10, actor->y - 28, 20, 2, g_color_warning);
            rect_fill(actor->x - 2, actor->y - 34, 4, 14, g_color_warning);
            rect_frame(left - 6, top - 6, TOMMYBETA_SPRITE_W + 12, TOMMYBETA_SPRITE_H + 12, g_color_warning);
        }
    }
}

static void draw_combat_link(const Actor *attacker, const Actor *target, int reach, u16 color) {
    int origin_x = actor_contact_x(attacker, reach);
    int origin_y = actor_contact_y(attacker, reach);
    int target_x = target->x;
    int target_y = target->y - 10;
    draw_line(origin_x, origin_y, target_x, target_y, color);
    rect_frame(target_x - 7, target_y - 7, 14, 14, color);
    rect_fill(origin_x - 1, origin_y - 1, 3, 3, color);
}

static void draw_combat_cues(void) {
    if (g_player_strike.active && g_mareaou.alive && actor_in_front(&g_tommy, &g_mareaou, g_player_strike.radius)) {
        u16 color = (g_player_strike.special && g_player_strike.special_index >= 0) ? g_specials[g_player_strike.special_index].color : g_color_warning;
        draw_combat_link(&g_tommy, &g_mareaou, g_player_strike.reach - g_player_strike.timer, color);
        draw_status_chip(g_tommy.x - 16, g_tommy.y - 52, g_player_strike.special ? "CAST" : "BITE", color, g_color_white);
    }
    if (g_enemy_strike.active && g_tommy.alive && actor_in_front(&g_mareaou, &g_tommy, g_enemy_strike.radius)) {
        draw_combat_link(&g_mareaou, &g_tommy, g_enemy_strike.reach - g_enemy_strike.timer, RGB15(31, 10, 10));
        draw_status_chip(g_mareaou.x - 18, g_mareaou.y - 52, "THREAT", RGB15(31, 10, 10), g_color_white);
    }
}

static void draw_actor_frames(void) {
    const u16 *tommy = select_tommy_frame();
    const u16 *mareaou = select_mareaou_frame();
    draw_actor_shadow(&g_tommy, RGB15(2, 2, 2));
    draw_actor_shadow(&g_mareaou, RGB15(5, 1, 1));
    if (g_tommy.y <= g_mareaou.y) {
        draw_actor_sprite(&g_tommy, tommy, g_color_white, 0);
        draw_actor_sprite(&g_mareaou, mareaou, g_color_warning, g_mareaou.finisher_state);
    } else {
        draw_actor_sprite(&g_mareaou, mareaou, g_color_warning, g_mareaou.finisher_state);
        draw_actor_sprite(&g_tommy, tommy, g_color_white, 0);
    }
    draw_actor_status(&g_tommy, 1);
    draw_actor_status(&g_mareaou, 0);
}

static void draw_props(void) {
    int index;
    for (index = 0; index < 4; ++index) {
        blit_sprite(tommybeta_prop_frames[g_props[index].frame], TOMMYBETA_PROP_W, TOMMYBETA_PROP_H, g_props[index].x, g_props[index].y);
    }
}

static void draw_critters(void) {
    int index;
    for (index = 0; index < 4; ++index) {
        blit_sprite(tommybeta_critter_frames[g_critters[index].frame], TOMMYBETA_CRITTER_W, TOMMYBETA_CRITTER_H, g_critters[index].x, g_critters[index].y);
    }
}

static void draw_ambience(void) {
    int index;
    for (index = 0; index < 4; ++index) {
        int ax = 12 + ((g_frame * (index + 1) + g_current_quadrant * 17 + index * 41) % 192);
        int ay = 34 + index * 18 + ((g_frame / (index + 2)) % 10);
        blit_sprite(tommybeta_ambience_frames[index], TOMMYBETA_ICON_W, TOMMYBETA_ICON_H, ax, ay);
    }
}

static void draw_fx(void) {
    if (!g_fx.active) return;
    if (g_fx.special) {
        blit_sprite(tommybeta_combat_special_fx_frames[g_fx.frame % 8], TOMMYBETA_FX_W, TOMMYBETA_FX_H, g_fx.x, g_fx.y);
    } else {
        blit_sprite(tommybeta_combat_basic_fx_frames[g_fx.frame % 3], TOMMYBETA_FX_W, TOMMYBETA_FX_H, g_fx.x, g_fx.y);
    }
}

static void draw_bar(int x, int y, int width, int value, int max_value, u16 fill, u16 back) {
    int filled = (max_value > 0) ? (width * value) / max_value : 0;
    rect_fill(x, y, width, 6, back);
    rect_fill(x, y, filled, 6, fill);
    rect_frame(x - 1, y - 1, width + 2, 8, g_color_black);
}

static void draw_notice_overlay(void) {
    if (!g_notice_text || g_notice_timer <= 0) return;
    rect_fill(46, 36, 148, 14, g_color_panel_alt);
    rect_frame(46, 36, 148, 14, g_color_save);
    draw_text(54, 40, g_notice_text, g_color_white, 1);
}

static void draw_hud(void) {
    EnemyBehavior behavior = behavior_from_id(g_mareaou.behavior_id);
    blit_opaque(tommybeta_hud_panel_bitmap, TOMMYBETA_HUD_W, TOMMYBETA_HUD_H, 0, 0);
    blit_opaque(tommybeta_hud_panel_bitmap, TOMMYBETA_HUD_W, TOMMYBETA_HUD_H, 0, 128);
    draw_text(8, 8, "TOMMY", g_color_white, 1);
    draw_text(178, 8, "MAREAOU", g_color_white, 1);
    draw_bar(44, 8, 72, g_tommy.health, g_tommy.max_health, RGB15(28, 6, 6), RGB15(8, 2, 2));
    draw_bar(44, 18, 72, g_tommy.stamina, g_tommy.max_stamina, RGB15(8, 26, 6), RGB15(2, 8, 2));
    draw_bar(148, 8, 72, g_mareaou.health, g_mareaou.max_health, RGB15(28, 6, 6), RGB15(8, 2, 2));
    draw_bar(148, 18, 72, g_mareaou.stamina, g_mareaou.max_stamina, RGB15(8, 26, 6), RGB15(2, 8, 2));
    rect_frame(4, 132, 232, 24, g_color_white);
    blit_sprite(tommybeta_special_icon_frames[g_current_special], TOMMYBETA_ICON_W, TOMMYBETA_ICON_H, 8, 132);
    draw_text(36, 136, "SPECIAL", g_color_white, 1);
    draw_text(78, 136, g_specials[g_current_special].name, g_specials[g_current_special].color, 1);
    draw_text(36, 146, "HEAL", g_color_heal, 1);
    draw_number(66, 146, g_heal_points, g_color_heal);
    draw_text(92, 146, "BHV", g_color_white, 1);
    draw_number(116, 146, behavior.id + 1, g_color_warning);
    draw_text(138, 146, g_attack_names[behavior.attack_style], g_color_white, 1);
    if (g_combo_count > 0) {
        draw_text(8, 28, "COMBO", g_color_warning, 1);
        draw_number(50, 28, g_combo_count, g_color_warning);
    }
    if (g_mareaou.finisher_state) {
        rect_fill(116, 132, 120, 22, g_color_panel_alt);
        rect_frame(116, 132, 120, 22, g_color_warning);
        draw_text(124, 136, "FINISH STATE", g_color_warning, 1);
        draw_text(124, 146, "USE SPECIAL NOW", g_color_white, 1);
    }
}

static void render_explore_scene(void) {
    m3_blit(g_active_background);
    draw_world_cohesion();
    draw_terrain_overlay_layer(0, 2);
    draw_props();
    draw_ambience();
    draw_critters();
    draw_actor_frames();
    draw_terrain_overlay_layer(2, 2);
    draw_fx();
    draw_combat_cues();
    draw_hud();

    if (g_banner_timer > 0) {
        rect_fill(30, 34, 180, 16, g_color_panel);
        rect_frame(30, 34, 180, 16, g_color_save);
        draw_text(38, 39, "QUADRANT", g_color_white, 1);
        draw_number(92, 39, g_current_quadrant + 1, g_color_warning);
        draw_text(110, 39, tommybeta_quadrant_names[g_current_quadrant], g_color_heal, 1);
    }
    draw_notice_overlay();
}

static void render_logo(void) {
    if (TOMMYBETA_HAVE_LOGO_SPLASH) {
        m3_blit(tommybeta_logo_splash_bitmap);
    } else {
        rect_fill(0, 0, SCREEN_W, SCREEN_H, g_color_black);
    }
    rect_fill(22, 18, 196, 30, g_color_panel_alt);
    rect_frame(22, 18, 196, 30, g_color_save);
    draw_text(76, 28, "drIPTECH", g_color_white, 2);
    rect_fill(34, 104, 172, 22, g_color_panel);
    rect_frame(34, 104, 172, 22, g_color_heal);
    draw_text(44, 110, "TOMMYBETA GBA PRESENTATION", g_color_warning, 1);
    draw_text(70, 134, "PRESS A OR START", g_color_white, 1);
}

static const u16 *intro_background_for_panel(int panel) {
    if (TOMMYBETA_HAVE_INTRO_PANELS) {
        return tommybeta_intro_panel_bitmaps[panel % TOMMYBETA_INTRO_PANEL_COUNT];
    }
    switch (panel) {
        case 0: return TOMMYBETA_HAVE_TITLE_MENU ? tommybeta_title_menu_bitmap : tommybeta_quadrant_bitmaps[0];
        case 1: return TOMMYBETA_HAVE_ENDINGS ? tommybeta_menu_endings_bitmap : tommybeta_quadrant_bitmaps[7];
        case 2: return tommybeta_quadrant_bitmaps[7];
        case 3: return tommybeta_quadrant_bitmaps[4];
        default: return TOMMYBETA_HAVE_FALL_INTRO ? tommybeta_fall_intro_bitmap : tommybeta_quadrant_bitmaps[0];
    }
}

static const char *intro_caption_for_panel(int panel) {
    static const char *const captions[] = {
        "MAREAOU TOOK TOMMYS WIFE",
        "THE KIDNAPPING CUT ACROSS\nTHE TOADSTOOL WILDS",
        "TOMMY FOUND A SLANTED\nROCK OUTCROP RAMP",
        "HE CHARGED OFF THE STONE\nAND LAUNCHED AFTER THEM",
        "THE HUNT DROPS INTO A\nRANDOM QUADRANT"
    };
    return captions[panel < 4 ? panel : 4];
}

static void render_intro_cinematic(void) {
    m3_blit(intro_background_for_panel(g_intro_panel));
    rect_fill(14, 12, 52, 18, g_color_panel_alt);
    rect_frame(14, 12, 52, 18, g_color_save);
    draw_text(24, 18, "PANEL", g_color_white, 1);
    draw_number(54, 18, g_intro_panel + 1, g_color_warning);
    rect_fill(10, 110, 220, 36, g_color_panel);
    rect_frame(10, 110, 220, 36, g_color_white);
    draw_text(20, 118, intro_caption_for_panel(g_intro_panel), g_color_warning, 1);
    rect_fill(20, 136, 140, 3, g_color_dim);
    rect_fill(20, 136, ((g_intro_panel + 1) * 140) / 5, 3, g_color_heal);
    draw_text(162, 132, "HOLD B TO SKIP", g_color_white, 1);
}

static const char *difficulty_label(int d) {
    if (d == 0) return "EASY";
    if (d == 2) return "HARD";
    return "NORMAL";
}

static void render_title_menu(void) {
    m3_blit(TOMMYBETA_HAVE_TITLE_MENU ? tommybeta_title_menu_bitmap : tommybeta_quadrant_bitmaps[0]);
    rect_fill(16, 14, 152, 118, g_color_panel);
    rect_frame(16, 14, 152, 118, g_color_warning);
    rect_fill(176, 20, 48, 90, g_color_panel_alt);
    rect_frame(176, 20, 48, 90, g_color_heal);
    draw_text(28, 26, "TOMMYBETA", g_color_white, 2);
    draw_text(28, 46, "NEW RUN", g_title_selection == 0 ? g_color_warning : g_color_white, 1);
    draw_text(28, 60, "LOAD GAME", (g_title_selection == 1) ? g_color_warning : (g_has_saved_run ? g_color_white : g_color_dim), 1);
    draw_text(28, 74, "DIFFICULTY", g_title_selection == 2 ? g_color_warning : g_color_white, 1);
    draw_text(96, 74, difficulty_label(g_difficulty), g_title_selection == 2 ? g_color_heal : g_color_white, 1);
    draw_text(28, 96, "LEVEL", g_color_white, 1);
    draw_number(66, 96, g_persistent_level, g_color_heal);
    draw_text(28, 108, "BEST COMBO", g_color_white, 1);
    draw_number(112, 108, g_combo_best, g_color_warning);
    draw_text(186, 28, "WINS", g_color_white, 1);
    draw_number(188, 42, g_persistent_wins, g_color_heal);
    draw_text(186, 62, "RUNS", g_color_white, 1);
    draw_number(188, 76, g_persistent_runs, g_color_warning);
    draw_text(180, 96, "MASKS", g_color_white, 1);
    draw_number(194, 110, count_bits(g_finisher_mask), g_color_heal);
    rect_fill(16, 136, 208, 14, g_color_panel_alt);
    rect_frame(16, 136, 208, 14, g_color_save);
    draw_text(26, 140, "A START SELECT  B CANCELS PROMPTS", g_color_white, 1);
}

static void render_fall_intro(void) {
    m3_blit(TOMMYBETA_HAVE_FALL_INTRO ? tommybeta_fall_intro_bitmap : g_active_background);
    rect_fill(38, 114, 164, 26, g_color_panel);
    rect_frame(38, 114, 164, 26, g_color_white);
    draw_text(50, 120, "ENTRY INTO THE HUNT", g_color_warning, 1);
    draw_text(82, 130, "PRESS A", g_color_white, 1);
}

static const char *tutorial_title_for_page(int page) {
    static const char *const titles[TUTORIAL_PAGE_COUNT] = {
        "MOVE",
        "ACTIONS",
        "FINISH",
        "FLOW"
    };
    return titles[page % TUTORIAL_PAGE_COUNT];
}

static const char *tutorial_body_for_page(int page) {
    static const char *const bodies[TUTORIAL_PAGE_COUNT] = {
        "DPAD MOVES THROUGH\nTHE QUADRANT\nKEEP MAERAOU IN\nFRONT OF TOMMY",
        "A STARTS BITE WINDUP\nB STARTS SPECIAL\nSELECT CYCLES YOUR\nACTIVE SPECIAL",
        "HOLD A PLUS B TO HEAL\nZERO HEALTH OPENS\nA FINISH STATE\nEND IT WITH SPECIAL",
        "START OPENS PAUSE\nLEFT RIGHT FLIP PAGES\nHOLD START SELECT\nTO SKIP TUTORIAL"
    };
    return bodies[page % TUTORIAL_PAGE_COUNT];
}

static void render_tutorial(void) {
    m3_blit(TOMMYBETA_HAVE_STATE_MENU ? tommybeta_state_menu_bitmap : g_active_background);
    rect_fill(28, 72, 184, 72, g_color_panel);
    rect_frame(28, 72, 184, 72, g_color_white);
    rect_fill(28, 58, 82, 12, g_color_panel_alt);
    rect_frame(28, 58, 82, 12, g_color_save);
    draw_text(36, 60, "TUTORIAL", g_color_white, 1);
    rect_fill(150, 58, 62, 12, g_color_panel_alt);
    rect_frame(150, 58, 62, 12, g_color_heal);
    draw_text(160, 60, "PAGE", g_color_white, 1);
    draw_number(190, 60, g_tutorial_page + 1, g_color_warning);
    draw_text(40, 82, tutorial_title_for_page(g_tutorial_page), g_color_warning, 1);
    draw_text(40, 96, tutorial_body_for_page(g_tutorial_page), g_color_white, 1);
    if (g_tutorial_page == 2 || g_persistent_level >= 3) {
        draw_text(124, 82, "COMBO HITS", g_color_heal, 1);
    }
    draw_text(40, 130, "A NEXT  B BACK", g_color_white, 1);
    draw_text(126, 130, g_tutorial_page == TUTORIAL_PAGE_COUNT - 1 ? "START DROP" : "RIGHT NEXT", g_color_heal, 1);
}

static void render_pause_menu(void) {
    static const char *const options[5] = {
        "SAVE GAME",
        "CODEX LOG",
        "SOUND",
        "RETURN TO TITLE",
        "CLOSE"
    };
    int index;
    m3_blit(TOMMYBETA_HAVE_PAUSE_WINDOW ? tommybeta_pause_window_bitmap : (TOMMYBETA_HAVE_STATE_MENU ? tommybeta_state_menu_bitmap : g_active_background));
    rect_fill(58, 42, 124, 82, g_color_panel);
    rect_frame(58, 42, 124, 82, g_color_white);
    draw_text(96, 48, "PAUSED", g_color_white, 1);
    for (index = 0; index < 5; ++index) {
        draw_text(68, 60 + index * 10, options[index], g_pause_selection == index ? g_color_warning : g_color_white, 1);
    }
    draw_text(110, 80, g_sound_enabled ? "ON" : "OFF", g_pause_selection == 2 ? g_color_heal : g_color_white, 1);
    draw_text(68, 110, "Q", g_color_white, 1);
    draw_number(80, 110, g_current_quadrant + 1, g_color_heal);
    draw_text(92, 110, "COMBO", g_color_white, 1);
    draw_number(128, 110, g_combo_count, g_color_warning);
}

static void render_codex(void) {
    const CodexPage *page = &g_codex_pages[g_codex_page % (int)(sizeof(g_codex_pages) / sizeof(g_codex_pages[0]))];
    m3_blit(TOMMYBETA_HAVE_CODEX_SCREEN ? tommybeta_codex_bitmap : (TOMMYBETA_HAVE_STATE_MENU ? tommybeta_state_menu_bitmap : g_active_background));
    rect_fill(16, 18, 208, 116, g_color_panel);
    rect_frame(16, 18, 208, 116, g_color_white);
    draw_text(28, 28, "CODEX LOG", g_color_white, 1);
    draw_text(160, 28, "PAGE", g_color_white, 1);
    draw_number(190, 28, g_codex_page + 1, g_color_heal);
    draw_text(28, 44, page->title, g_color_warning, 1);
    draw_text(28, 60, page->body, g_color_white, 1);
    draw_text(26, 122, "LEFT RIGHT CHANGES PAGE  B RETURNS", g_color_white, 1);
}

static void render_title_confirm(void) {
    m3_blit(TOMMYBETA_HAVE_PAUSE_WINDOW ? tommybeta_pause_window_bitmap : (TOMMYBETA_HAVE_STATE_MENU ? tommybeta_state_menu_bitmap : g_active_background));
    rect_fill(52, 56, 136, 42, g_color_panel_alt);
    rect_frame(52, 56, 136, 42, g_color_warning);
    draw_text(70, 62, "RETURN TO TITLE", g_color_warning, 1);
    draw_text(64, 74, g_unsaved_progress ? "UNSAVED RUN LOST" : "CLOSE CURRENT RUN", g_color_white, 1);
    draw_text(74, 88, "YES", g_title_confirm_selection == 0 ? g_color_warning : g_color_white, 1);
    draw_text(126, 88, "NO", g_title_confirm_selection == 1 ? g_color_warning : g_color_white, 1);
}

static void render_end(const char *title, const char *line) {
    const u16 *backdrop = TOMMYBETA_HAVE_ENDINGS ? tommybeta_menu_endings_bitmap : tommybeta_quadrant_bitmaps[g_current_quadrant];
    if (g_state == STATE_WIN && TOMMYBETA_HAVE_VICTORY_SCREEN) backdrop = tommybeta_victory_screen_bitmap;
    else if (g_state == STATE_GAME_OVER && TOMMYBETA_HAVE_DEFEAT_SCREEN) backdrop = tommybeta_defeat_screen_bitmap;
    else if (TOMMYBETA_HAVE_STATE_MENU) backdrop = tommybeta_state_menu_bitmap;
    m3_blit(backdrop);
    rect_fill(20, 96, 200, 44, g_color_panel);
    rect_frame(20, 96, 200, 44, g_state == STATE_WIN ? g_color_heal : g_color_warning);
    draw_text(30, 104, title, g_color_warning, 2);
    draw_text(30, 120, line, g_color_white, 1);
    draw_text(30, 132, "PRESS A TO RETURN TO MENU", g_state == STATE_WIN ? g_color_heal : g_color_white, 1);
    rect_fill(20, 14, 132, 16, g_color_panel_alt);
    rect_frame(20, 14, 132, 16, g_color_save);
    draw_text(28, 18, "MASKS CLAIMED", g_color_white, 1);
    draw_number(116, 18, count_bits(g_finisher_mask), g_color_warning);
}

static void update_logo_splash(void) {
    if (g_logo_timer > 0) g_logo_timer -= 1;
    if (key_pressed(KEY_A) || key_pressed(KEY_START) || g_logo_timer == 0) {
        g_state = STATE_INTRO_CINEMATIC;
        g_intro_panel = 0;
        g_intro_panel_timer = 110;
    }
}

static void update_intro_cinematic(void) {
    if (g_keys & KEY_B) {
        g_cinematic_skip_timer += 1;
        if (g_cinematic_skip_timer >= CINEMATIC_SKIP_FRAMES) {
            g_state = STATE_TITLE_MENU;
            g_cinematic_skip_timer = 0;
            return;
        }
    } else {
        g_cinematic_skip_timer = 0;
    }

    g_intro_panel_timer -= 1;
    if (key_pressed(KEY_A) || key_pressed(KEY_START) || g_intro_panel_timer <= 0) {
        g_intro_panel += 1;
        if (g_intro_panel >= 5) {
            g_state = STATE_TITLE_MENU;
        } else {
            g_intro_panel_timer = 110;
        }
    }
}

static void update_title_menu(void) {
    if (key_pressed(KEY_UP)) {
        g_title_selection = (g_title_selection + 2) % 3;
        audio_menu_move();
    }
    if (key_pressed(KEY_DOWN)) {
        g_title_selection = (g_title_selection + 1) % 3;
        audio_menu_move();
    }
    if (key_pressed(KEY_A) || key_pressed(KEY_START)) {
        if (g_title_selection == 0) {
            audio_menu_accept();
            begin_run();
        } else if (g_title_selection == 1) {
            restore_saved_run();
        } else {
            g_difficulty = (g_difficulty + 1) % 3;
            audio_menu_move();
        }
    }
    if (key_pressed(KEY_LEFT) && g_title_selection == 2) {
        g_difficulty = (g_difficulty + 2) % 3;
        audio_menu_move();
    }
    if (key_pressed(KEY_RIGHT) && g_title_selection == 2) {
        g_difficulty = (g_difficulty + 1) % 3;
        audio_menu_move();
    }
}

static void update_fall_intro(void) {
    if (g_fall_intro_timer > 0) g_fall_intro_timer -= 1;
    if (key_pressed(KEY_A) || key_pressed(KEY_START) || g_fall_intro_timer == 0) {
        g_tutorial_page = 0;
        g_state = g_tutorial_pending ? STATE_TUTORIAL : STATE_EXPLORE;
    }
}

static void update_tutorial(void) {
    handle_tutorial_skip();
    if (key_pressed(KEY_LEFT) || key_pressed(KEY_B)) {
        if (g_tutorial_page > 0) {
            g_tutorial_page -= 1;
            audio_menu_move();
        }
    }
    if (key_pressed(KEY_RIGHT) || key_pressed(KEY_A)) {
        if (g_tutorial_page < TUTORIAL_PAGE_COUNT - 1) {
            g_tutorial_page += 1;
            audio_menu_move();
            return;
        }
    }
    if ((key_pressed(KEY_A) && g_tutorial_page == TUTORIAL_PAGE_COUNT - 1) || key_pressed(KEY_START)) {
        g_tutorial_pending = 0;
        g_state = STATE_EXPLORE;
        g_unsaved_progress = 1;
    }
}

static void update_pause_menu(void) {
    if (key_pressed(KEY_UP)) {
        g_pause_selection = (g_pause_selection + 4) % 5;
        audio_menu_move();
    }
    if (key_pressed(KEY_DOWN)) {
        g_pause_selection = (g_pause_selection + 1) % 5;
        audio_menu_move();
    }
    if (key_pressed(KEY_B) || key_pressed(KEY_START)) {
        g_state = STATE_EXPLORE;
        return;
    }
    if (key_pressed(KEY_A)) {
        audio_menu_accept();
        if (g_pause_selection == 0) {
            save_current_run();
        } else if (g_pause_selection == 1) {
            g_state = STATE_CODEX;
        } else if (g_pause_selection == 2) {
            g_sound_enabled ^= 1;
        } else if (g_pause_selection == 3) {
            g_title_confirm_selection = 1;
            g_state = STATE_TITLE_CONFIRM;
        } else {
            g_state = STATE_EXPLORE;
        }
    }
}

static void update_codex(void) {
    int page_count = (int)(sizeof(g_codex_pages) / sizeof(g_codex_pages[0]));
    if (key_pressed(KEY_LEFT)) {
        g_codex_page = (g_codex_page + page_count - 1) % page_count;
        audio_menu_move();
    }
    if (key_pressed(KEY_RIGHT) || key_pressed(KEY_A)) {
        g_codex_page = (g_codex_page + 1) % page_count;
        audio_menu_move();
    }
    if (key_pressed(KEY_B) || key_pressed(KEY_START)) {
        g_state = STATE_PAUSE;
    }
}

static void update_title_confirm(void) {
    if (key_pressed(KEY_LEFT) || key_pressed(KEY_RIGHT) || key_pressed(KEY_UP) || key_pressed(KEY_DOWN)) {
        g_title_confirm_selection ^= 1;
        audio_menu_move();
    }
    if (key_pressed(KEY_B)) {
        g_state = STATE_PAUSE;
        return;
    }
    if (key_pressed(KEY_A)) {
        if (g_title_confirm_selection == 0) {
            g_state = STATE_TITLE_MENU;
            g_pause_selection = 0;
            clear_run_snapshot_only();
            save_persistent_progress();
        } else {
            g_state = STATE_PAUSE;
        }
    }
}

static void update_end_state(void) {
    if (key_pressed(KEY_A) || key_pressed(KEY_START)) {
        g_state = STATE_TITLE_MENU;
    }
}

static void update_state(void) {
    if (g_state == STATE_LOGO_SPLASH) update_logo_splash();
    else if (g_state == STATE_INTRO_CINEMATIC) update_intro_cinematic();
    else if (g_state == STATE_TITLE_MENU) update_title_menu();
    else if (g_state == STATE_FALL_INTRO) update_fall_intro();
    else if (g_state == STATE_TUTORIAL) update_tutorial();
    else if (g_state == STATE_EXPLORE) update_explore();
    else if (g_state == STATE_PAUSE) update_pause_menu();
    else if (g_state == STATE_CODEX) update_codex();
    else if (g_state == STATE_TITLE_CONFIRM) update_title_confirm();
    else update_end_state();
}

static void render_state(void) {
    if (g_state == STATE_LOGO_SPLASH) render_logo();
    else if (g_state == STATE_INTRO_CINEMATIC) render_intro_cinematic();
    else if (g_state == STATE_TITLE_MENU) render_title_menu();
    else if (g_state == STATE_FALL_INTRO) render_fall_intro();
    else if (g_state == STATE_TUTORIAL) render_tutorial();
    else if (g_state == STATE_EXPLORE) render_explore_scene();
    else if (g_state == STATE_PAUSE) render_pause_menu();
    else if (g_state == STATE_CODEX) render_codex();
    else if (g_state == STATE_TITLE_CONFIRM) render_title_confirm();
    else if (g_state == STATE_WIN) render_end("YOU WIN", "ALL EIGHT SPECIALS FINISHED THE HUNT");
    else render_end("GAME OVER", "THE EMPIRE PUSHED TOMMY BACK");
}

int main(void) {
    REG_DISPCNT = MODE3 | BG2_ENABLE;
    audio_init();
    load_save_block();
    g_active_background = tommybeta_quadrant_bitmaps[0];
    render_state();
    wait_vblank();
    present_framebuffer();

    while (1) {
        poll_keys();
        update_state();
        render_state();
        wait_vblank();
        present_framebuffer();
        g_frame += 1;
    }
}