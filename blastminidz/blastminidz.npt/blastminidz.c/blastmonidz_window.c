#include "blastmonidz_window.h"
#include "blastmonidz_bridge.h"

#ifdef _WIN32

#define COBJMACROS

#include <objbase.h>
#include <ctype.h>
#include <math.h>
#include <mmsystem.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <wincodec.h>

#define BLASTMONIDZ_WINDOW_LOGICAL_WIDTH 320
#define BLASTMONIDZ_WINDOW_LOGICAL_HEIGHT 180
#define BLASTMONIDZ_WINDOW_ASSET_GRID 4

#define BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_UP        0x0001
#define BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_DOWN      0x0002
#define BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_LEFT      0x0004
#define BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_RIGHT     0x0008
#define BLASTMONIDZ_XINPUT_GAMEPAD_START          0x0010
#define BLASTMONIDZ_XINPUT_GAMEPAD_BACK           0x0020
#define BLASTMONIDZ_XINPUT_GAMEPAD_LEFT_SHOULDER  0x0100
#define BLASTMONIDZ_XINPUT_GAMEPAD_RIGHT_SHOULDER 0x0200
#define BLASTMONIDZ_XINPUT_GAMEPAD_A              0x1000
#define BLASTMONIDZ_XINPUT_GAMEPAD_B              0x2000
#define BLASTMONIDZ_XINPUT_GAMEPAD_X              0x4000
#define BLASTMONIDZ_XINPUT_GAMEPAD_Y              0x8000

typedef struct {
    WORD wButtons;
    BYTE bLeftTrigger;
    BYTE bRightTrigger;
    SHORT sThumbLX;
    SHORT sThumbLY;
    SHORT sThumbRX;
    SHORT sThumbRY;
} BlastmonidzXInputGamepad;

typedef struct {
    DWORD dwPacketNumber;
    BlastmonidzXInputGamepad Gamepad;
} BlastmonidzXInputState;

typedef DWORD (WINAPI *BlastmonidzXInputGetStateFn)(DWORD, BlastmonidzXInputState *);

typedef struct {
    int available;
    WORD buttons;
    SHORT lx;
    SHORT ly;
    BYTE lt;
    BYTE rt;
} BlastmonidzControllerSnapshot;

typedef enum {
    WINDOW_SCENE_TITLE = 0,
    WINDOW_SCENE_LORE,
    WINDOW_SCENE_ARCHIVE,
    WINDOW_SCENE_STARTER,
    WINDOW_SCENE_ARENA,
    WINDOW_SCENE_SUMMARY
} WindowScene;

typedef struct {
    HBITMAP bitmap;
    int width;
    int height;
    int loaded;
    char source_path[MAX_PATH];
    BlastmonidzPixelArray pixels;
    BlastmonidzAssetProfile profile;
    int analyzed;
} ArchiveBitmap;

static const char kWindowClassName[] = "BlastmonidzWindowClass";
static HWND g_hwnd = NULL;
static int g_initialized = 0;
static const GameState *g_state = NULL;
static WindowScene g_scene = WINDOW_SCENE_TITLE;
static IWICImagingFactory *g_wic_factory = NULL;
static int g_com_initialized = 0;
static ArchiveBitmap g_title_backdrop = {0};
static ArchiveBitmap g_title_logo = {0};
static ArchiveBitmap g_floor_tile = {0};
static ArchiveBitmap g_crate_variants[BLASTMONIDZ_CRATE_VARIANTS] = {0};
static ArchiveBitmap g_bomb_frames[BLASTMONIDZ_PLAYER_FRAMES] = {0};
static ArchiveBitmap g_bomb_pouch = {0};
static ArchiveBitmap g_gem_paints[BLASTMONIDZ_PAINT_VARIANTS] = {0};
static ArchiveBitmap g_player_sprites[BLASTMONIDZ_HERO_FAMILIES][BLASTMONIDZ_PLAYER_DIRECTIONS][BLASTMONIDZ_PLAYER_FRAMES] = {0};
static ArchiveBitmap g_rival_back_sprites[BLASTMONIDZ_PLAYER_FRAMES] = {0};
static ArchiveBitmap g_rival_side_sprites[BLASTMONIDZ_RIVAL_FAMILIES][BLASTMONIDZ_PLAYER_FRAMES] = {0};
static BlastmonidzDesignOrganism g_design_organism = {0};
static const UINT_PTR kTitleTimerId = 77;
static char g_title_fanfare_path[MAX_PATH] = {0};
static int g_title_fanfare_ready = 0;
static int g_title_fanfare_playing = 0;
static int g_close_requested = 0;
static int g_input_queue[64] = {0};
static int g_input_queue_head = 0;
static int g_input_queue_tail = 0;
static HMODULE g_xinput_module = NULL;
static BlastmonidzXInputGetStateFn g_xinput_get_state = NULL;
static BlastmonidzControllerSnapshot g_prev_controller = {0};

static void queue_input(int ch);
static void poll_window_controller(void);

static const char *const kTitleRhymes[] = {
    "Cheap talk folds when the real light climbs. Leave Amanda out the noise; this stage speaks in prime time.",
    "Rumor smoke gets rinsed when the comeback glows. No dogpile bars here, only heavyweight flows.",
    "Loose chatter stays little when the archive ignites. Keep the gossip off her name; this whole screen writes rights.",
    "Static mouths go quiet when the signal hits gold. Art stands tall, weak takes crack, and the truth stays bold."
};

static const char *const kTitleFeatureBursts[] = {
    "FULL-SCREEN ARCHIVE RECOMPOSITION",
    "18-FRAME BOMB PULSE REEL",
    "CHEMISTRY-REACTIVE PAINT FIELDS",
    "RIVAL MOTION FAMILIES ONLINE"
};

static const char *const kTitleArrangementModes[] = {
    "CHOIR GRID",
    "RIFT CASCADE",
    "ARCHIVE FAN",
    "DISTRICT TERRACE",
    "SIGNAL CONSTELLATION"
};

typedef struct {
    unsigned int seed;
    int pulse;
    int rhyme_index;
    int burst_index;
    int arrangement_index;
    int preview_offset;
    int direction_offset;
    int frame_stride;
    int district_offset;
    int chemistry_mode;
    int active_button;
    int switch_progress;
    int ecology_phase;
    int meter_values[4];
    Color primary_tint;
    Color secondary_tint;
    Color tertiary_tint;
} TitleVisualState;

static Color mix_color(Color a, Color b, int amount, int scale);

static void draw_text_block(HDC hdc, int x, int y, int w, int h, const char *text, int size, int weight, Color color);
static void draw_panel(HDC hdc, const RECT *rect, Color top, Color bottom, Color edge, int radius);
static void draw_home_tile_pattern(HDC hdc, const RECT *tile, const BlastmonidzHomeTile *home_tile, Color base_color);
static void draw_centered_tile_label(HDC hdc, const RECT *tile, const char *text, int size, Color color);
static void start_title_fanfare(void);
static void stop_title_fanfare(void);
static int build_runtime_output_path(const char *file_name, char *buffer, size_t size);

static int organism_frame_offset(const GameState *state) {
    int state_bias = 0;
    if (state) {
        state_bias = state->world_feed.balance / 18;
    }
    return ((int)(g_design_organism.animation_elasticity * 7.0f) + state_bias) % BLASTMONIDZ_PLAYER_FRAMES;
}

static int organism_overlay_alpha(int base_alpha) {
    int alpha = base_alpha + (int)(g_design_organism.environmental_mutation_bias * 54.0f);
    if (alpha < 0) {
        alpha = 0;
    }
    if (alpha > 255) {
        alpha = 255;
    }
    return alpha;
}

static int clamp_visual_int(int value, int min_value, int max_value) {
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}

static unsigned int hash_text_seed(const char *text) {
    unsigned int hash = 2166136261u;
    if (!text) {
        return hash;
    }
    while (*text) {
        hash ^= (unsigned char)(*text++);
        hash *= 16777619u;
    }
    return hash;
}

static Color shift_color(Color color, int dr, int dg, int db) {
    color.r = (unsigned char)clamp_visual_int((int)color.r + dr, 0, 255);
    color.g = (unsigned char)clamp_visual_int((int)color.g + dg, 0, 255);
    color.b = (unsigned char)clamp_visual_int((int)color.b + db, 0, 255);
    color.a = 255;
    return color;
}

static Color doctrine_color(int doctrine) {
    switch (doctrine) {
        case BLASTMONIDZ_DOCTRINE_HARMONIZER:
            return (Color){102, 188, 170, 255};
        case BLASTMONIDZ_DOCTRINE_STEWARD:
            return (Color){190, 166, 92, 255};
        case BLASTMONIDZ_DOCTRINE_MEDIATOR:
            return (Color){110, 166, 224, 255};
        case BLASTMONIDZ_DOCTRINE_KINWEAVER:
            return (Color){196, 120, 184, 255};
        default:
            return blastmonidz_style.accent;
    }
}

static Color organism_color_slot(int slot, Color fallback) {
    if (slot >= 0 && slot < 3) {
        Color candidate = g_design_organism.dominant_colors[slot];
        if (candidate.a != 0 || candidate.r != 0 || candidate.g != 0 || candidate.b != 0) {
            candidate.a = 255;
            return candidate;
        }
    }
    fallback.a = 255;
    return fallback;
}

static RECT inset_rect(RECT rect, int dx, int dy) {
    rect.left += dx;
    rect.right -= dx;
    rect.top += dy;
    rect.bottom -= dy;
    return rect;
}

static RECT snap_rect_to_grid(RECT rect, int grid) {
    if (grid <= 1) {
        return rect;
    }
    rect.left = (rect.left / grid) * grid;
    rect.top = (rect.top / grid) * grid;
    rect.right = ((rect.right + grid - 1) / grid) * grid;
    rect.bottom = ((rect.bottom + grid - 1) / grid) * grid;
    if (rect.right <= rect.left) {
        rect.right = rect.left + grid;
    }
    if (rect.bottom <= rect.top) {
        rect.bottom = rect.top + grid;
    }
    return rect;
}

static void build_title_visual_state(DWORD now, TitleVisualState *visual) {
    unsigned int seed;
    unsigned int bridge_hash;
    if (!visual) {
        return;
    }
    ZeroMemory(visual, sizeof(*visual));
    bridge_hash = hash_text_seed(blastmonidz_bridge_latest_inbox()) ^ (hash_text_seed(blastmonidz_bridge_latest_status()) << 1);
    seed = bridge_hash ^ (unsigned int)(now / 120) ^ (unsigned int)(g_design_organism.assets_analyzed * 97) ^ (unsigned int)(g_design_organism.structural_discipline * 1000.0f);
    visual->seed = seed;
    visual->pulse = (int)((now / (90 + (int)((1.0f - g_design_organism.animation_elasticity) * 80.0f))) % BLASTMONIDZ_PLAYER_FRAMES);
    visual->rhyme_index = (int)((now / 3200) % (sizeof(kTitleRhymes) / sizeof(kTitleRhymes[0])));
    visual->burst_index = (int)((now / 2400) % (sizeof(kTitleFeatureBursts) / sizeof(kTitleFeatureBursts[0])));
    visual->arrangement_index = (int)(seed % (sizeof(kTitleArrangementModes) / sizeof(kTitleArrangementModes[0])));
    visual->preview_offset = (int)((seed >> 3) % MAX_ARCHIVE_ITEMS);
    visual->direction_offset = (int)((seed >> 6) % BLASTMONIDZ_PLAYER_DIRECTIONS);
    visual->frame_stride = 1 + (int)((seed >> 9) % 4u);
    visual->district_offset = (int)((seed >> 12) % BLASTMONIDZ_HOME_TILES);
    visual->chemistry_mode = (int)((seed >> 16) % 3u);
    visual->active_button = (int)((now / 2200u) % 2u);
    visual->switch_progress = (int)(((now % 2200u) * 100u) / 2199u);
    visual->ecology_phase = (int)((now / 340u) % BLASTMONIDZ_PAINT_VARIANTS);
    visual->primary_tint = mix_color(organism_color_slot(0, blastmonidz_style.accent), blastmonidz_style.accent, 1, 2);
    visual->secondary_tint = mix_color(organism_color_slot(1, blastmonidz_style.panel_edge), blastmonidz_style.panel_edge, 1, 2);
    visual->tertiary_tint = mix_color(organism_color_slot(2, blastmonidz_style.text), blastmonidz_style.background, 1, 4);
    visual->meter_values[0] = clamp_visual_int((int)(g_design_organism.structural_discipline * 100.0f), 0, 100);
    visual->meter_values[1] = clamp_visual_int((int)(g_design_organism.ornamental_bias * 100.0f), 0, 100);
    visual->meter_values[2] = clamp_visual_int((int)(g_design_organism.animation_elasticity * 100.0f), 0, 100);
    visual->meter_values[3] = clamp_visual_int((int)(g_design_organism.environmental_mutation_bias * 100.0f), 0, 100);
}

static void write_wave_u16(FILE *stream, unsigned int value) {
    unsigned char bytes[2];
    bytes[0] = (unsigned char)(value & 0xFFu);
    bytes[1] = (unsigned char)((value >> 8) & 0xFFu);
    fwrite(bytes, 1, 2, stream);
}

static void write_wave_u32(FILE *stream, unsigned int value) {
    unsigned char bytes[4];
    bytes[0] = (unsigned char)(value & 0xFFu);
    bytes[1] = (unsigned char)((value >> 8) & 0xFFu);
    bytes[2] = (unsigned char)((value >> 16) & 0xFFu);
    bytes[3] = (unsigned char)((value >> 24) & 0xFFu);
    fwrite(bytes, 1, 4, stream);
}

static int ensure_title_fanfare_file(void) {
    static const double kMelody[8] = {261.63, 329.63, 392.00, 523.25, 493.88, 440.00, 392.00, 329.63};
    const unsigned int sample_rate = 22050u;
    const unsigned int seconds = 6u;
    const unsigned int sample_count = sample_rate * seconds;
    const unsigned int data_size = sample_count * 2u;
    FILE *stream;
    unsigned int index;

    if (g_title_fanfare_ready && g_title_fanfare_path[0] != '\0') {
        return 1;
    }
    if (!build_runtime_output_path("blastmonidz_title_fanfare.wav", g_title_fanfare_path, sizeof(g_title_fanfare_path))) {
        return 0;
    }
    if (GetFileAttributesA(g_title_fanfare_path) != INVALID_FILE_ATTRIBUTES) {
        g_title_fanfare_ready = 1;
        return 1;
    }
    stream = fopen(g_title_fanfare_path, "wb");
    if (!stream) {
        return 0;
    }
    fwrite("RIFF", 1, 4, stream);
    write_wave_u32(stream, 36u + data_size);
    fwrite("WAVE", 1, 4, stream);
    fwrite("fmt ", 1, 4, stream);
    write_wave_u32(stream, 16u);
    write_wave_u16(stream, 1u);
    write_wave_u16(stream, 1u);
    write_wave_u32(stream, sample_rate);
    write_wave_u32(stream, sample_rate * 2u);
    write_wave_u16(stream, 2u);
    write_wave_u16(stream, 16u);
    fwrite("data", 1, 4, stream);
    write_wave_u32(stream, data_size);

    for (index = 0; index < sample_count; ++index) {
        double t = (double)index / (double)sample_rate;
        unsigned int melody_step = (unsigned int)(t / 0.75) % 8u;
        double pulse = 0.55 + 0.45 * sin(6.283185307179586 * (0.25 * t));
        double envelope = 0.68 + 0.32 * sin(6.283185307179586 * (0.5 * t));
        double lead = sin(6.283185307179586 * kMelody[melody_step] * t) * 0.26;
        double harmony = sin(6.283185307179586 * (kMelody[(melody_step + 2) % 8u] / 2.0) * t) * 0.14;
        double drone = sin(6.283185307179586 * 130.81 * t) * 0.12;
        double shimmer = sin(6.283185307179586 * 783.99 * t) * 0.04 * pulse;
        double wave = (lead + harmony + drone + shimmer) * envelope;
        int sample = (int)(wave * 24576.0);
        if (sample < -32768) {
            sample = -32768;
        }
        if (sample > 32767) {
            sample = 32767;
        }
        write_wave_u16(stream, (unsigned int)(sample & 0xFFFF));
    }
    fclose(stream);
    g_title_fanfare_ready = 1;
    return 1;
}

static void start_title_fanfare(void) {
    if (g_title_fanfare_playing) {
        return;
    }
    if (!ensure_title_fanfare_file()) {
        return;
    }
    if (PlaySoundA(g_title_fanfare_path, NULL, SND_ASYNC | SND_LOOP | SND_FILENAME | SND_NODEFAULT)) {
        g_title_fanfare_playing = 1;
    }
}

static void stop_title_fanfare(void) {
    if (!g_title_fanfare_playing) {
        return;
    }
    PlaySoundA(NULL, NULL, 0);
    g_title_fanfare_playing = 0;
}

static void queue_input(int ch) {
    int next_tail = (g_input_queue_tail + 1) % (int)(sizeof(g_input_queue) / sizeof(g_input_queue[0]));
    if (next_tail == g_input_queue_head || ch == 0) {
        return;
    }
    g_input_queue[g_input_queue_tail] = ch;
    g_input_queue_tail = next_tail;
}

static void ensure_xinput_loaded(void) {
    static const char *const dll_names[] = {
        "xinput1_4.dll",
        "xinput1_3.dll",
        "xinput9_1_0.dll"
    };
    size_t dll_index;
    if (g_xinput_get_state) {
        return;
    }
    for (dll_index = 0; dll_index < sizeof(dll_names) / sizeof(dll_names[0]); ++dll_index) {
        g_xinput_module = LoadLibraryA(dll_names[dll_index]);
        if (g_xinput_module) {
            union {
                FARPROC raw;
                BlastmonidzXInputGetStateFn typed;
            } xinput_proc;
            xinput_proc.raw = GetProcAddress(g_xinput_module, "XInputGetState");
            g_xinput_get_state = xinput_proc.typed;
            if (g_xinput_get_state) {
                return;
            }
            FreeLibrary(g_xinput_module);
            g_xinput_module = NULL;
        }
    }
}

static void poll_window_controller(void) {
    BlastmonidzControllerSnapshot current = {0};
    int left_edge;
    int right_edge;
    int up_edge;
    int down_edge;
    int a_edge;
    int b_edge;
    int x_edge;
    int y_edge;
    int start_edge;
    int back_edge;
    int lb_edge;
    int rb_edge;
    ensure_xinput_loaded();
    if (!g_xinput_get_state) {
        return;
    }
    {
        BlastmonidzXInputState state;
        ZeroMemory(&state, sizeof(state));
        if (g_xinput_get_state(0, &state) == ERROR_SUCCESS) {
            current.available = 1;
            current.buttons = state.Gamepad.wButtons;
            current.lx = state.Gamepad.sThumbLX;
            current.ly = state.Gamepad.sThumbLY;
            current.lt = state.Gamepad.bLeftTrigger;
            current.rt = state.Gamepad.bRightTrigger;
        }
    }
    if (!current.available) {
        ZeroMemory(&g_prev_controller, sizeof(g_prev_controller));
        return;
    }
    left_edge = (current.lx <= -16000 && g_prev_controller.lx > -12000) ||
        ((current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_LEFT) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_LEFT));
    right_edge = (current.lx >= 16000 && g_prev_controller.lx < 12000) ||
        ((current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_RIGHT) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_RIGHT));
    up_edge = (current.ly >= 16000 && g_prev_controller.ly < 12000) ||
        ((current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_UP) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_UP));
    down_edge = (current.ly <= -16000 && g_prev_controller.ly > -12000) ||
        ((current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_DOWN) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_DPAD_DOWN));
    a_edge = ((current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_A) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_A)) ||
        (current.rt >= 200 && g_prev_controller.rt < 160);
    b_edge = ((current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_B) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_B)) ||
        (current.lt >= 200 && g_prev_controller.lt < 160);
    x_edge = (current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_X) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_X);
    y_edge = (current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_Y) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_Y);
    start_edge = (current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_START) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_START);
    back_edge = (current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_BACK) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_BACK);
    lb_edge = (current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_LEFT_SHOULDER) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_LEFT_SHOULDER);
    rb_edge = (current.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_RIGHT_SHOULDER) && !(g_prev_controller.buttons & BLASTMONIDZ_XINPUT_GAMEPAD_RIGHT_SHOULDER);

    if (up_edge) queue_input('^');
    if (down_edge) queue_input('v');
    if (left_edge) queue_input('<');
    if (right_edge) queue_input('>');
    if (a_edge) queue_input('!');
    if (b_edge) queue_input('?');
    if (x_edge || rb_edge) queue_input('c');
    if (y_edge) queue_input('r');
    if (start_edge || lb_edge) queue_input('t');
    if (back_edge) queue_input('q');
    g_prev_controller = current;
}

static Color organism_environment_tint(void) {
    Color tint = blastmonidz_style.panel_edge;
    tint.r = (unsigned char)((tint.r + g_design_organism.dominant_colors[0].r + g_design_organism.dominant_colors[1].r) / 3);
    tint.g = (unsigned char)((tint.g + g_design_organism.dominant_colors[0].g + g_design_organism.dominant_colors[1].g) / 3);
    tint.b = (unsigned char)((tint.b + g_design_organism.dominant_colors[0].b + g_design_organism.dominant_colors[1].b) / 3);
    tint.a = 255;
    return tint;
}

static COLORREF to_rgb(Color color) {
    return RGB(color.r, color.g, color.b);
}

static TRIVERTEX make_vertex(LONG x, LONG y, Color color) {
    TRIVERTEX vertex;
    vertex.x = x;
    vertex.y = y;
    vertex.Red = (COLOR16)(color.r << 8);
    vertex.Green = (COLOR16)(color.g << 8);
    vertex.Blue = (COLOR16)(color.b << 8);
    vertex.Alpha = (COLOR16)(color.a << 8);
    return vertex;
}

static Color mix_color(Color a, Color b, int amount, int scale) {
    Color mixed;
    mixed.r = (unsigned char)((a.r * (scale - amount) + b.r * amount) / scale);
    mixed.g = (unsigned char)((a.g * (scale - amount) + b.g * amount) / scale);
    mixed.b = (unsigned char)((a.b * (scale - amount) + b.b * amount) / scale);
    mixed.a = (unsigned char)((a.a * (scale - amount) + b.a * amount) / scale);
    return mixed;
}

static Color alpha_mix(Color color, int alpha) {
    if (alpha < 0) {
        alpha = 0;
    }
    if (alpha > 255) {
        alpha = 255;
    }
    return mix_color(blastmonidz_style.background, color, alpha, 255);
}

static int rect_width(const RECT *rect) {
    return rect->right - rect->left;
}

static int rect_height(const RECT *rect) {
    return rect->bottom - rect->top;
}

static int path_has(const char *path, const char *needle) {
    return path && needle && strstr(path, needle) != NULL;
}

static void fill_ellipse_color(HDC hdc, const RECT *rect, Color color, Color edge) {
    HBRUSH brush = CreateSolidBrush(to_rgb(color));
    HPEN pen = CreatePen(PS_SOLID, 1, to_rgb(edge));
    HBRUSH old_brush = (HBRUSH)SelectObject(hdc, brush);
    HPEN old_pen = (HPEN)SelectObject(hdc, pen);
    Ellipse(hdc, rect->left, rect->top, rect->right, rect->bottom);
    SelectObject(hdc, old_pen);
    SelectObject(hdc, old_brush);
    DeleteObject(pen);
    DeleteObject(brush);
}

static void draw_blob_line(HDC hdc, int x0, int y0, int x1, int y1, int thickness, Color fill, Color edge) {
    HPEN pen = CreatePen(PS_SOLID, thickness, to_rgb(fill));
    HPEN old_pen = (HPEN)SelectObject(hdc, pen);
    HBRUSH brush = CreateSolidBrush(to_rgb(fill));
    HBRUSH old_brush = (HBRUSH)SelectObject(hdc, brush);
    int radius = thickness / 2;
    MoveToEx(hdc, x0, y0, NULL);
    LineTo(hdc, x1, y1);
    Ellipse(hdc, x0 - radius, y0 - radius, x0 + radius, y0 + radius);
    Ellipse(hdc, x1 - radius, y1 - radius, x1 + radius, y1 + radius);
    SelectObject(hdc, old_brush);
    DeleteObject(brush);
    SelectObject(hdc, old_pen);
    DeleteObject(pen);
    {
        HPEN outline = CreatePen(PS_SOLID, 1, to_rgb(edge));
        HPEN prev_outline = (HPEN)SelectObject(hdc, outline);
        MoveToEx(hdc, x0, y0, NULL);
        LineTo(hdc, x1, y1);
        SelectObject(hdc, prev_outline);
        DeleteObject(outline);
    }
}

static void draw_blob_rect(HDC hdc, int x, int y, int w, int h, int radius, Color fill, Color edge) {
    RECT rect = {x, y, x + w, y + h};
    draw_panel(hdc, &rect, fill, mix_color(fill, blastmonidz_style.background, 1, 5), edge, radius);
}

static void draw_norm_blob_line(HDC hdc, const RECT *rect, int x0, int y0, int x1, int y1, int thickness, Color fill, Color edge) {
    int left = rect->left + rect_width(rect) * x0 / 100;
    int top = rect->top + rect_height(rect) * y0 / 100;
    int right = rect->left + rect_width(rect) * x1 / 100;
    int bottom = rect->top + rect_height(rect) * y1 / 100;
    draw_blob_line(hdc, left, top, right, bottom, thickness, fill, edge);
}

static void draw_norm_blob_rect(HDC hdc, const RECT *rect, int x, int y, int w, int h, int radius, Color fill, Color edge) {
    int left = rect->left + rect_width(rect) * x / 100;
    int top = rect->top + rect_height(rect) * y / 100;
    int width = rect_width(rect) * w / 100;
    int height = rect_height(rect) * h / 100;
    draw_blob_rect(hdc, left, top, width, height, radius, fill, edge);
}

static void draw_norm_blob_ellipse(HDC hdc, const RECT *rect, int x, int y, int w, int h, Color fill, Color edge) {
    RECT ellipse = {
        rect->left + rect_width(rect) * x / 100,
        rect->top + rect_height(rect) * y / 100,
        rect->left + rect_width(rect) * (x + w) / 100,
        rect->top + rect_height(rect) * (y + h) / 100
    };
    fill_ellipse_color(hdc, &ellipse, fill, edge);
}

static void draw_bubble_glyph(HDC hdc, const RECT *rect, char raw_glyph, Color fill, Color edge) {
    char glyph = (char)toupper((unsigned char)raw_glyph);
    int stroke = rect_width(rect) / 8;
    if (stroke < 3) {
        stroke = 3;
    }
    if (glyph == ' ') {
        return;
    }
    switch (glyph) {
        case 'A':
            draw_norm_blob_line(hdc, rect, 18, 92, 50, 8, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 82, 92, 50, 8, stroke, fill, edge);
            draw_norm_blob_rect(hdc, rect, 26, 48, 48, 12, 8, fill, edge);
            break;
        case 'B':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 20, 8, 54, 38, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 20, 50, 56, 40, fill, edge);
            draw_norm_blob_rect(hdc, rect, 46, 18, 22, 18, 8, blastmonidz_style.background, edge);
            draw_norm_blob_rect(hdc, rect, 46, 60, 24, 18, 8, blastmonidz_style.background, edge);
            break;
        case 'C':
            draw_norm_blob_ellipse(hdc, rect, 10, 10, 78, 80, fill, edge);
            draw_norm_blob_rect(hdc, rect, 44, 18, 42, 64, 8, blastmonidz_style.background, edge);
            break;
        case 'D':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 18, 8, 60, 84, fill, edge);
            draw_norm_blob_rect(hdc, rect, 50, 18, 20, 64, 8, blastmonidz_style.background, edge);
            break;
        case 'E':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 8, 64, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 44, 52, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 80, 64, 12, 8, fill, edge);
            break;
        case 'F':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 8, 64, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 44, 50, 12, 8, fill, edge);
            break;
        case 'G':
            draw_norm_blob_ellipse(hdc, rect, 10, 10, 78, 80, fill, edge);
            draw_norm_blob_rect(hdc, rect, 50, 18, 34, 26, 8, blastmonidz_style.background, edge);
            draw_norm_blob_rect(hdc, rect, 48, 50, 28, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 62, 50, 12, 28, 8, fill, edge);
            break;
        case 'H':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_rect(hdc, rect, 74, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_rect(hdc, rect, 24, 44, 52, 12, 8, fill, edge);
            break;
        case 'I':
            draw_norm_blob_rect(hdc, rect, 18, 8, 64, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 44, 18, 12, 64, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 80, 64, 12, 8, fill, edge);
            break;
        case 'J':
            draw_norm_blob_rect(hdc, rect, 18, 8, 64, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 54, 18, 14, 54, 8, fill, edge);
            draw_norm_blob_line(hdc, rect, 54, 78, 36, 92, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 36, 92, 18, 74, stroke, fill, edge);
            break;
        case 'K':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_line(hdc, rect, 76, 10, 26, 50, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 26, 50, 78, 92, stroke, fill, edge);
            break;
        case 'L':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 80, 62, 12, 8, fill, edge);
            break;
        case 'M':
            draw_norm_blob_rect(hdc, rect, 10, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_rect(hdc, rect, 76, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_line(hdc, rect, 20, 8, 50, 54, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 80, 8, 50, 54, stroke, fill, edge);
            break;
        case 'N':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_rect(hdc, rect, 74, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_line(hdc, rect, 20, 10, 80, 90, stroke, fill, edge);
            break;
        case 'O':
            draw_norm_blob_ellipse(hdc, rect, 10, 10, 80, 80, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 28, 26, 44, 48, blastmonidz_style.background, edge);
            break;
        case 'P':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 20, 8, 56, 40, fill, edge);
            draw_norm_blob_rect(hdc, rect, 44, 18, 26, 16, 8, blastmonidz_style.background, edge);
            break;
        case 'Q':
            draw_norm_blob_ellipse(hdc, rect, 10, 10, 80, 80, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 28, 26, 44, 48, blastmonidz_style.background, edge);
            draw_norm_blob_line(hdc, rect, 58, 62, 84, 92, stroke, fill, edge);
            break;
        case 'R':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 84, 10, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 20, 8, 56, 40, fill, edge);
            draw_norm_blob_rect(hdc, rect, 44, 18, 26, 16, 8, blastmonidz_style.background, edge);
            draw_norm_blob_line(hdc, rect, 30, 48, 80, 92, stroke, fill, edge);
            break;
        case 'S':
            draw_norm_blob_ellipse(hdc, rect, 12, 8, 68, 38, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 20, 48, 68, 38, fill, edge);
            draw_norm_blob_rect(hdc, rect, 52, 18, 26, 16, 8, blastmonidz_style.background, edge);
            draw_norm_blob_rect(hdc, rect, 12, 58, 26, 16, 8, blastmonidz_style.background, edge);
            draw_norm_blob_rect(hdc, rect, 28, 40, 36, 14, 8, fill, edge);
            break;
        case 'T':
            draw_norm_blob_rect(hdc, rect, 12, 8, 76, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 44, 18, 12, 74, 8, fill, edge);
            break;
        case 'U':
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 64, 10, fill, edge);
            draw_norm_blob_rect(hdc, rect, 74, 8, 14, 64, 10, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 18, 54, 64, 36, fill, edge);
            draw_norm_blob_rect(hdc, rect, 28, 54, 44, 18, 8, blastmonidz_style.background, edge);
            break;
        case 'V':
            draw_norm_blob_line(hdc, rect, 16, 8, 50, 92, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 84, 8, 50, 92, stroke, fill, edge);
            break;
        case 'W':
            draw_norm_blob_line(hdc, rect, 12, 8, 28, 92, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 28, 92, 50, 44, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 50, 44, 72, 92, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 72, 92, 88, 8, stroke, fill, edge);
            break;
        case 'X':
            draw_norm_blob_line(hdc, rect, 16, 10, 84, 90, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 84, 10, 16, 90, stroke, fill, edge);
            break;
        case 'Y':
            draw_norm_blob_line(hdc, rect, 16, 10, 50, 46, stroke, fill, edge);
            draw_norm_blob_line(hdc, rect, 84, 10, 50, 46, stroke, fill, edge);
            draw_norm_blob_rect(hdc, rect, 44, 42, 12, 50, 8, fill, edge);
            break;
        case 'Z':
            draw_norm_blob_rect(hdc, rect, 12, 8, 76, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 12, 80, 76, 12, 8, fill, edge);
            draw_norm_blob_line(hdc, rect, 82, 16, 18, 84, stroke, fill, edge);
            break;
        case '0':
            draw_norm_blob_ellipse(hdc, rect, 12, 8, 76, 84, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 30, 26, 40, 48, blastmonidz_style.background, edge);
            draw_norm_blob_line(hdc, rect, 72, 18, 30, 82, stroke - 1, alpha_mix(fill, 180), edge);
            break;
        case '1':
            draw_norm_blob_rect(hdc, rect, 42, 12, 14, 80, 8, fill, edge);
            draw_norm_blob_line(hdc, rect, 30, 24, 48, 10, stroke, fill, edge);
            draw_norm_blob_rect(hdc, rect, 24, 80, 42, 12, 8, fill, edge);
            break;
        case '2':
            draw_norm_blob_ellipse(hdc, rect, 12, 8, 72, 36, fill, edge);
            draw_norm_blob_rect(hdc, rect, 52, 18, 24, 16, 8, blastmonidz_style.background, edge);
            draw_norm_blob_line(hdc, rect, 72, 38, 18, 84, stroke, fill, edge);
            draw_norm_blob_rect(hdc, rect, 14, 80, 72, 12, 8, fill, edge);
            break;
        case '3':
            draw_norm_blob_ellipse(hdc, rect, 14, 8, 66, 34, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 18, 46, 66, 38, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 40, 38, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 22, 28, 14, 8, blastmonidz_style.background, edge);
            draw_norm_blob_rect(hdc, rect, 18, 62, 28, 14, 8, blastmonidz_style.background, edge);
            break;
        case '4':
            draw_norm_blob_rect(hdc, rect, 58, 10, 14, 82, 8, fill, edge);
            draw_norm_blob_line(hdc, rect, 18, 58, 62, 8, stroke, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 54, 58, 12, 8, fill, edge);
            break;
        case '5':
            draw_norm_blob_rect(hdc, rect, 18, 8, 62, 12, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 12, 8, 14, 40, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 42, 50, 12, 8, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 18, 50, 62, 36, fill, edge);
            draw_norm_blob_rect(hdc, rect, 18, 58, 26, 14, 8, blastmonidz_style.background, edge);
            break;
        case '6':
            draw_norm_blob_ellipse(hdc, rect, 14, 8, 68, 78, fill, edge);
            draw_norm_blob_rect(hdc, rect, 54, 16, 20, 24, 8, blastmonidz_style.background, edge);
            draw_norm_blob_ellipse(hdc, rect, 24, 46, 52, 34, fill, edge);
            draw_norm_blob_rect(hdc, rect, 40, 54, 20, 14, 8, blastmonidz_style.background, edge);
            break;
        case '7':
            draw_norm_blob_rect(hdc, rect, 12, 8, 76, 12, 8, fill, edge);
            draw_norm_blob_line(hdc, rect, 80, 16, 30, 92, stroke, fill, edge);
            break;
        case '8':
            draw_norm_blob_ellipse(hdc, rect, 18, 8, 58, 34, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 14, 46, 68, 38, fill, edge);
            draw_norm_blob_rect(hdc, rect, 30, 22, 32, 10, 8, blastmonidz_style.background, edge);
            draw_norm_blob_rect(hdc, rect, 28, 60, 36, 12, 8, blastmonidz_style.background, edge);
            break;
        case '9':
            draw_norm_blob_ellipse(hdc, rect, 14, 8, 68, 78, fill, edge);
            draw_norm_blob_rect(hdc, rect, 20, 54, 20, 22, 8, blastmonidz_style.background, edge);
            draw_norm_blob_ellipse(hdc, rect, 22, 10, 52, 34, fill, edge);
            draw_norm_blob_rect(hdc, rect, 36, 20, 22, 12, 8, blastmonidz_style.background, edge);
            break;
        case '.':
            draw_norm_blob_ellipse(hdc, rect, 40, 78, 18, 18, fill, edge);
            break;
        case ':':
            draw_norm_blob_ellipse(hdc, rect, 40, 28, 18, 18, fill, edge);
            draw_norm_blob_ellipse(hdc, rect, 40, 68, 18, 18, fill, edge);
            break;
        case '/':
            draw_norm_blob_line(hdc, rect, 78, 8, 22, 92, stroke, fill, edge);
            break;
        case '-':
            draw_norm_blob_rect(hdc, rect, 20, 46, 60, 10, 8, fill, edge);
            break;
        case '|':
            draw_norm_blob_rect(hdc, rect, 44, 10, 12, 80, 8, fill, edge);
            break;
        case '[':
            draw_norm_blob_rect(hdc, rect, 24, 8, 14, 84, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 24, 8, 42, 10, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 24, 82, 42, 10, 8, fill, edge);
            break;
        case ']':
            draw_norm_blob_rect(hdc, rect, 62, 8, 14, 84, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 34, 8, 42, 10, 8, fill, edge);
            draw_norm_blob_rect(hdc, rect, 34, 82, 42, 10, 8, fill, edge);
            break;
        default:
            draw_norm_blob_ellipse(hdc, rect, 14, 10, 72, 76, fill, edge);
            draw_norm_blob_line(hdc, rect, 30, 30, 68, 68, stroke, edge, fill);
            draw_norm_blob_line(hdc, rect, 68, 30, 30, 68, stroke, edge, fill);
            break;
    }
}

static int measure_bubble_char(char glyph, int size) {
    if (glyph == ' ') {
        return size / 2;
    }
    if (glyph == 'I' || glyph == '1' || glyph == ':' || glyph == '.') {
        return (size * 2) / 3;
    }
    if (glyph == 'M' || glyph == 'W') {
        return (size * 7) / 6;
    }
    return size;
}

static void draw_bubble_char(HDC hdc, int x, int y, int size, int index, char glyph, Color color) {
    unsigned int seed = hash_text_seed("bubble") ^ (unsigned int)(glyph * 131u + index * 977u);
    double tick = (double)GetTickCount();
    double bounce = sin((tick + (double)(index * 97)) / 160.0);
    double wobble = cos((tick + (double)(index * 53)) / 210.0);
    int width = measure_bubble_char((char)toupper((unsigned char)glyph), size);
    int squash = (int)(bounce * size * 0.08);
    int stretch = (int)(wobble * size * 0.10);
    RECT glyph_rect;
    Color fill = mix_color(color, blastmonidz_style.text, (int)(seed % 2u), 3);
    Color edge = mix_color(blastmonidz_style.background, color, 2, 3);
    glyph_rect.left = x + (int)(seed % 3u) - 1;
    glyph_rect.top = y + (int)(fabs(bounce) * size * 0.10);
    glyph_rect.right = glyph_rect.left + width + stretch;
    glyph_rect.bottom = glyph_rect.top + size - squash;
    if (glyph_rect.right <= glyph_rect.left + 6) {
        glyph_rect.right = glyph_rect.left + 6;
    }
    if (glyph_rect.bottom <= glyph_rect.top + 6) {
        glyph_rect.bottom = glyph_rect.top + 6;
    }
    draw_bubble_glyph(hdc, &glyph_rect, glyph, fill, edge);
}

static void fill_rect_color(HDC hdc, const RECT *rect, Color color) {
    HBRUSH brush = CreateSolidBrush(to_rgb(color));
    FillRect(hdc, rect, brush);
    DeleteObject(brush);
}

static void fill_gradient_rect(HDC hdc, const RECT *rect, Color start, Color end, int vertical) {
    TRIVERTEX vertices[2];
    GRADIENT_RECT gradient = {0, 1};
    ULONG mode = vertical ? GRADIENT_FILL_RECT_V : GRADIENT_FILL_RECT_H;
    vertices[0] = make_vertex(rect->left, rect->top, start);
    vertices[1] = make_vertex(rect->right, rect->bottom, end);
    GradientFill(hdc, vertices, 2, &gradient, 1, mode);
}

static void frame_rect_color(HDC hdc, const RECT *rect, Color color) {
    HBRUSH brush = CreateSolidBrush(to_rgb(color));
    FrameRect(hdc, rect, brush);
    DeleteObject(brush);
}

static void draw_panel(HDC hdc, const RECT *rect, Color top, Color bottom, Color edge, int radius) {
    HBRUSH brush = CreateSolidBrush(to_rgb(top));
    HPEN pen = CreatePen(PS_SOLID, 1, to_rgb(edge));
    HBRUSH old_brush = (HBRUSH)SelectObject(hdc, brush);
    HPEN old_pen = (HPEN)SelectObject(hdc, pen);
    RoundRect(hdc, rect->left, rect->top, rect->right, rect->bottom, radius, radius);
    SelectObject(hdc, old_pen);
    DeleteObject(pen);
    SelectObject(hdc, old_brush);
    DeleteObject(brush);
    {
        RECT inner = {rect->left + 1, rect->top + 1, rect->right - 1, rect->bottom - 1};
        fill_gradient_rect(hdc, &inner, top, bottom, 1);
    }
    {
        HPEN glow_pen = CreatePen(PS_SOLID, 1, to_rgb(mix_color(edge, blastmonidz_style.text, 1, 4)));
        HPEN previous_pen = (HPEN)SelectObject(hdc, glow_pen);
        HGDIOBJ previous_brush = SelectObject(hdc, GetStockObject(HOLLOW_BRUSH));
        RoundRect(hdc, rect->left, rect->top, rect->right, rect->bottom, radius, radius);
        SelectObject(hdc, previous_brush);
        SelectObject(hdc, previous_pen);
        DeleteObject(glow_pen);
    }
}

static void draw_pill(HDC hdc, const RECT *rect, Color fill, Color edge, const char *text, Color text_color) {
    draw_panel(hdc, rect, fill, mix_color(fill, blastmonidz_style.background, 1, 3), edge, 18);
    draw_text_block(hdc, rect->left + 12, rect->top + 6, rect->right - rect->left - 24, rect->bottom - rect->top - 8, text, 16, FW_SEMIBOLD, text_color);
}

static void draw_meter(HDC hdc, int x, int y, int w, int h, const char *label, int value, int max_value, Color fill, Color glow) {
    RECT rail = {x, y + 18, x + w, y + 18 + h};
    RECT amount = rail;
    int clamped = value;
    if (max_value <= 0) {
        max_value = 1;
    }
    if (clamped < 0) {
        clamped = 0;
    }
    if (clamped > max_value) {
        clamped = max_value;
    }
    amount.right = rail.left + ((rail.right - rail.left) * clamped) / max_value;
    draw_text_block(hdc, x, y, w, 18, label, 14, FW_SEMIBOLD, blastmonidz_style.text);
    draw_panel(hdc, &rail, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 10);
    if (amount.right > amount.left) {
        RECT inner = {amount.left + 2, amount.top + 2, amount.right - 2, amount.bottom - 2};
        if (inner.right > inner.left) {
            draw_panel(hdc, &inner, fill, glow, glow, 8);
        }
    }
}

static void draw_text_block(HDC hdc, int x, int y, int w, int h, const char *text, int size, int weight, Color color) {
    int cursor_x = x;
    int cursor_y = y;
    int line_height;
    int index = 0;
    (void)weight;
    if (!text || size <= 0 || w <= 0 || h <= 0) {
        return;
    }
    line_height = size + size / 3;
    while (*text && cursor_y + line_height <= y + h) {
        char glyph = *text++;
        int char_width;
        if (glyph == '\r') {
            continue;
        }
        if (glyph == '\n') {
            cursor_x = x;
            cursor_y += line_height;
            continue;
        }
        char_width = measure_bubble_char((char)toupper((unsigned char)glyph), size) + size / 6;
        if (cursor_x + char_width > x + w && glyph != ' ') {
            cursor_x = x;
            cursor_y += line_height;
            if (cursor_y + line_height > y + h) {
                break;
            }
        }
        if (glyph != ' ') {
            draw_bubble_char(hdc, cursor_x, cursor_y, size, index, glyph, color);
            index += 1;
        }
        cursor_x += char_width;
    }
}

static void reset_archive_bitmap(ArchiveBitmap *bitmap) {
    if (bitmap->bitmap) {
        DeleteObject(bitmap->bitmap);
    }
    blastmonidz_pixel_array_reset(&bitmap->pixels);
    blastmonidz_asset_profile_reset(&bitmap->profile);
    ZeroMemory(bitmap, sizeof(*bitmap));
}

static int get_module_directory(char *buffer, size_t size) {
    DWORD length = GetModuleFileNameA(NULL, buffer, (DWORD)size);
    if (length == 0 || length >= size) {
        return 0;
    }
    while (length > 0 && buffer[length - 1] != '\\' && buffer[length - 1] != '/') {
        --length;
    }
    buffer[length] = '\0';
    return 1;
}

static int build_archive_asset_path(const char *entry, char *buffer, size_t size) {
    char module_dir[MAX_PATH];
    static const char archive_cache_dir[] = "bomberman_archive_cache\\";
    size_t module_len;
    size_t cache_len = sizeof(archive_cache_dir) - 1;
    size_t entry_len = strlen(entry);
    if (!get_module_directory(module_dir, sizeof(module_dir))) {
        return 0;
    }
    module_len = strlen(module_dir);
    if (module_len + cache_len + entry_len + 1 > size) {
        return 0;
    }
    memcpy(buffer, module_dir, module_len);
    memcpy(buffer + module_len, archive_cache_dir, cache_len);
    memcpy(buffer + module_len + cache_len, entry, entry_len + 1);
    return 1;
}

static int build_runtime_output_path(const char *file_name, char *buffer, size_t size) {
    char module_dir[MAX_PATH];
    size_t module_len;
    size_t file_len;
    if (!get_module_directory(module_dir, sizeof(module_dir))) {
        return 0;
    }
    module_len = strlen(module_dir);
    file_len = strlen(file_name);
    if (module_len + file_len + 1 > size) {
        return 0;
    }
    memcpy(buffer, module_dir, module_len);
    memcpy(buffer + module_len, file_name, file_len + 1);
    return 1;
}

static int load_archive_bitmap(const char *relative_entry, ArchiveBitmap *out_bitmap) {
    WCHAR wide_path[MAX_PATH];
    char path[MAX_PATH];
    IWICBitmapDecoder *decoder = NULL;
    IWICBitmapFrameDecode *frame = NULL;
    IWICFormatConverter *converter = NULL;
    HBITMAP bitmap = NULL;
    HDC screen_dc = NULL;
    BITMAPINFO bitmap_info;
    void *bits = NULL;
    UINT width = 0;
    UINT height = 0;
    UINT stride = 0;
    UINT image_size = 0;
    HRESULT hr;

    if (!g_wic_factory) {
        return 0;
    }
    if (!build_archive_asset_path(relative_entry, path, sizeof(path))) {
        return 0;
    }
    if (GetFileAttributesA(path) == INVALID_FILE_ATTRIBUTES) {
        return 0;
    }
    if (MultiByteToWideChar(CP_ACP, 0, path, -1, wide_path, MAX_PATH) == 0) {
        return 0;
    }

    hr = IWICImagingFactory_CreateDecoderFromFilename(
        g_wic_factory,
        wide_path,
        NULL,
        GENERIC_READ,
        WICDecodeMetadataCacheOnLoad,
        &decoder);
    if (FAILED(hr)) {
        goto cleanup;
    }
    hr = IWICBitmapDecoder_GetFrame(decoder, 0, &frame);
    if (FAILED(hr)) {
        goto cleanup;
    }
    hr = IWICImagingFactory_CreateFormatConverter(g_wic_factory, &converter);
    if (FAILED(hr)) {
        goto cleanup;
    }
    hr = IWICFormatConverter_Initialize(
        converter,
        (IWICBitmapSource *)frame,
        &GUID_WICPixelFormat32bppPBGRA,
        WICBitmapDitherTypeNone,
        NULL,
        0.0f,
        WICBitmapPaletteTypeCustom);
    if (FAILED(hr)) {
        goto cleanup;
    }
    hr = IWICBitmapSource_GetSize((IWICBitmapSource *)converter, &width, &height);
    if (FAILED(hr) || width == 0 || height == 0) {
        goto cleanup;
    }

    stride = width * 4;
    image_size = stride * height;
    ZeroMemory(&bitmap_info, sizeof(bitmap_info));
    bitmap_info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bitmap_info.bmiHeader.biWidth = (LONG)width;
    bitmap_info.bmiHeader.biHeight = -((LONG)height);
    bitmap_info.bmiHeader.biPlanes = 1;
    bitmap_info.bmiHeader.biBitCount = 32;
    bitmap_info.bmiHeader.biCompression = BI_RGB;

    screen_dc = GetDC(NULL);
    bitmap = CreateDIBSection(screen_dc, &bitmap_info, DIB_RGB_COLORS, &bits, NULL, 0);
    ReleaseDC(NULL, screen_dc);
    if (!bitmap || !bits) {
        goto cleanup;
    }

    hr = IWICBitmapSource_CopyPixels((IWICBitmapSource *)converter, NULL, stride, image_size, (BYTE *)bits);
    if (FAILED(hr)) {
        DeleteObject(bitmap);
        bitmap = NULL;
        goto cleanup;
    }

    reset_archive_bitmap(out_bitmap);
    out_bitmap->bitmap = bitmap;
    out_bitmap->width = (int)width;
    out_bitmap->height = (int)height;
    out_bitmap->loaded = 1;
    snprintf(out_bitmap->source_path, sizeof(out_bitmap->source_path), "%s", path);
    out_bitmap->pixels.width = (int)width;
    out_bitmap->pixels.height = (int)height;
    out_bitmap->pixels.stride = (int)stride;
    out_bitmap->pixels.rgba = (unsigned char *)malloc((size_t)image_size);
    if (out_bitmap->pixels.rgba) {
        memcpy(out_bitmap->pixels.rgba, bits, (size_t)image_size);
        out_bitmap->analyzed = blastmonidz_analyze_pixel_array(&out_bitmap->pixels, &out_bitmap->profile);
        if (out_bitmap->analyzed) {
            blastmonidz_design_organism_absorb(&g_design_organism, &out_bitmap->profile);
        }
    }

cleanup:
    if (converter) {
        IWICFormatConverter_Release(converter);
    }
    if (frame) {
        IWICBitmapFrameDecode_Release(frame);
    }
    if (decoder) {
        IWICBitmapDecoder_Release(decoder);
    }
    return out_bitmap->loaded;
}

static void load_title_archive_images(void) {
    load_archive_bitmap(blastmonidz_title_backdrop_asset()->archive_entry, &g_title_backdrop);
    load_archive_bitmap(blastmonidz_title_logo_asset()->archive_entry, &g_title_logo);
}

static void load_hero_sprite_family(int family, int direction, const char *direction_name) {
    static const int family_prefixes[BLASTMONIDZ_HERO_FAMILIES] = {0, 2, 3, 4};
    int frame;
    char path[128];
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
        if (family_prefixes[family] == 0) {
            snprintf(path, sizeof(path), "graphics/characters/bMan %s%04d.png", direction_name, frame + 1);
        } else {
            snprintf(path, sizeof(path), "graphics/characters/bMan %s%d%04d.png", direction_name, family_prefixes[family], frame + 1);
        }
        load_archive_bitmap(path, &g_player_sprites[family][direction][frame]);
    }
}

static void load_rival_sprite_family(void) {
    int frame;
    int family;
    char path[128];
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
        snprintf(path, sizeof(path), "graphics/characters/bMan baddieWalkback%04d.png", frame + 1);
        load_archive_bitmap(path, &g_rival_back_sprites[frame]);
    }
    for (family = 0; family < BLASTMONIDZ_RIVAL_FAMILIES; ++family) {
        for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
            if (family == 0) {
                snprintf(path, sizeof(path), "graphics/characters/bMan baddieWalkSide%04d.png", frame + 1);
            } else {
                snprintf(path, sizeof(path), "graphics/characters/bMan baddieWalkSide2%04d.png", frame + 1);
            }
            load_archive_bitmap(path, &g_rival_side_sprites[family][frame]);
        }
    }
}

static void load_runtime_archive_images(void) {
    static const char *const paint_assets[BLASTMONIDZ_PAINT_VARIANTS] = {
        "graphics/bomb, crate, tile, paint/redPaint.png",
        "graphics/bomb, crate, tile, paint/greenPaint.png",
        "graphics/bomb, crate, tile, paint/bluePaint.png",
        "graphics/bomb, crate, tile, paint/goldPaint.png",
        "graphics/bomb, crate, tile, paint/purplePaint.png"
    };
    static const char *const crate_assets[BLASTMONIDZ_CRATE_VARIANTS] = {
        "graphics/bomb, crate, tile, paint/crate.png",
        "graphics/bomb, crate, tile, paint/bMan door.png",
        "graphics/bomb, crate, tile, paint/bMan gunPowder.png"
    };
    int family;
    int chemistry_index;
    int frame;

    load_archive_bitmap("graphics/bomb, crate, tile, paint/bMan tile.png", &g_floor_tile);
    load_archive_bitmap("graphics/bomb, crate, tile, paint/bMan bombPouch.png", &g_bomb_pouch);
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_CRATE_VARIANTS; ++chemistry_index) {
        load_archive_bitmap(crate_assets[chemistry_index], &g_crate_variants[chemistry_index]);
    }
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
        char path[128];
        snprintf(path, sizeof(path), "graphics/bomb, crate, tile, paint/bMan bomb%04d.png", frame + 1);
        load_archive_bitmap(path, &g_bomb_frames[frame]);
    }
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_PAINT_VARIANTS; ++chemistry_index) {
        load_archive_bitmap(paint_assets[chemistry_index], &g_gem_paints[chemistry_index]);
    }
    for (family = 0; family < BLASTMONIDZ_HERO_FAMILIES; ++family) {
        load_hero_sprite_family(family, 0, "forWalk");
        load_hero_sprite_family(family, 1, "backWalk");
        load_hero_sprite_family(family, 2, "sideWalk");
    }
    load_rival_sprite_family();
}

static void write_bitmap_profile(FILE *stream, const char *label, const ArchiveBitmap *bitmap) {
    char line[320];
    if (!stream || !label || !bitmap || !bitmap->loaded || !bitmap->analyzed) {
        return;
    }
    blastmonidz_describe_asset_profile(&bitmap->profile, line, (int)sizeof(line));
    fprintf(stream, "%s\n  path=%s\n  %s\n", label, bitmap->source_path, line);
}

static void write_design_profile_report(void) {
    char output_path[MAX_PATH];
    FILE *report;
    char organism_line[320];
    int family;
    int direction;
    int frame;
    int chemistry_index;
    if (!build_runtime_output_path(blastmonidz_design_profile_path, output_path, sizeof(output_path))) {
        return;
    }
    report = fopen(output_path, "w");
    if (!report) {
        return;
    }
    blastmonidz_design_organism_finalize(&g_design_organism);
    blastmonidz_describe_design_organism(&g_design_organism, organism_line, (int)sizeof(organism_line));

    fprintf(report, "BLASTMONIDZ DESIGN ORGANISM REPORT\n\n");
    fprintf(report, "Aggregate profile\n%s\n\n", organism_line);
    fprintf(report, "Theory synthesis\n%s\n\n", g_design_organism.theory_summary);
    if (g_state) {
        char genome_line[256];
        int player_index;
        blastmonidz_describe_genome_profile(&g_state->visuals.asset_genome, genome_line, (int)sizeof(genome_line));
        fprintf(report, "Runtime asset genome\n%s\n\n", genome_line);
        fprintf(report, "Active character genomes\n");
        for (player_index = 0; player_index < MAX_PLAYERS; ++player_index) {
            blastmonidz_describe_genome_profile(&g_state->players[player_index].mon.cosmetic_genome, genome_line, (int)sizeof(genome_line));
            fprintf(report, "- %s: %s\n", g_state->players[player_index].name, genome_line);
        }
        fprintf(report, "\n");
    }
    fprintf(report, "Applied reading\n");
    fprintf(report, "- Art theory: silhouette control outranks interior texture, so identity is carried by contour rhythm and color hierarchy.\n");
    fprintf(report, "- Design theory: the asset base behaves like a modular kit where repeated primitives are varied through timing, hue reassignment, and local ornament.\n");
    fprintf(report, "- Architecture: massing is bottom-weighted and foundation-biased, which makes forms read as stable and load-bearing rather than floating.\n");
    fprintf(report, "- Civil and construction logic: crate, tile, bomb, and body forms all privilege prefabrication, repeatability, and reliable joint logic over bespoke one-off detailing.\n");
    fprintf(report, "- Evolution pipeline: animation elasticity, environmental mutation bias, structural discipline, and ornamental bias can be treated as phenotype controls for runtime adaptation.\n\n");
    fprintf(report, "Ten home tiles\n");
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_HOME_TILES; ++chemistry_index) {
        fprintf(report, "- %c %s: %s | structure %.2f | ornament %.2f | growth %.2f | shelter %.2f\n",
            blastmonidz_home_tiles[chemistry_index].glyph,
            blastmonidz_home_tiles[chemistry_index].name,
            blastmonidz_home_tiles[chemistry_index].theory_role,
            blastmonidz_home_tiles[chemistry_index].structural_bias,
            blastmonidz_home_tiles[chemistry_index].ornamental_bias,
            blastmonidz_home_tiles[chemistry_index].growth_bias,
            blastmonidz_home_tiles[chemistry_index].shelter_bias);
    }
    fprintf(report, "\n");

    write_bitmap_profile(report, "title.logo", &g_title_logo);
    write_bitmap_profile(report, "title.backdrop", &g_title_backdrop);
    write_bitmap_profile(report, "arena.floor", &g_floor_tile);
    write_bitmap_profile(report, "arena.bombPouch", &g_bomb_pouch);
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_CRATE_VARIANTS; ++chemistry_index) {
        char label[64];
        snprintf(label, sizeof(label), "arena.crate[%d]", chemistry_index);
        write_bitmap_profile(report, label, &g_crate_variants[chemistry_index]);
    }
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_PAINT_VARIANTS; ++chemistry_index) {
        char label[64];
        snprintf(label, sizeof(label), "paint[%d]", chemistry_index);
        write_bitmap_profile(report, label, &g_gem_paints[chemistry_index]);
    }
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; frame += 3) {
        char label[64];
        snprintf(label, sizeof(label), "bomb.frame[%d]", frame);
        write_bitmap_profile(report, label, &g_bomb_frames[frame]);
    }
    for (family = 0; family < BLASTMONIDZ_HERO_FAMILIES; ++family) {
        for (direction = 0; direction < BLASTMONIDZ_PLAYER_DIRECTIONS; ++direction) {
            char label[64];
            snprintf(label, sizeof(label), "hero[%d][%d][0]", family, direction);
            write_bitmap_profile(report, label, &g_player_sprites[family][direction][0]);
        }
    }
    for (family = 0; family < BLASTMONIDZ_RIVAL_FAMILIES; ++family) {
        char label[64];
        snprintf(label, sizeof(label), "rival.side[%d][0]", family);
        write_bitmap_profile(report, label, &g_rival_side_sprites[family][0]);
    }
    write_bitmap_profile(report, "rival.back[0]", &g_rival_back_sprites[0]);
    fclose(report);
}

static void draw_archive_bitmap(HDC hdc, const RECT *dest, const ArchiveBitmap *bitmap, int alpha) {
    unsigned int seed;
    Color primary;
    Color secondary;
    Color tertiary;
    RECT snapped_dest;
    RECT inner;
    int pulse;
    if (!bitmap) {
        return;
    }
    seed = hash_text_seed(bitmap->source_path[0] ? bitmap->source_path : "regenerated") ^ (unsigned int)(bitmap->profile.edge_density * 1000.0f);
    pulse = (int)((GetTickCount() / 120u + (seed % 17u)) % 9u);
    primary = alpha_mix(organism_color_slot((int)(seed % 3u), blastmonidz_style.accent), alpha);
    secondary = alpha_mix(mix_color(organism_environment_tint(), blastmonidz_style.ghost, (int)(seed % 3u), 4), alpha);
    tertiary = alpha_mix(mix_color(blastmonidz_style.text, blastmonidz_style.background, 1, 5), alpha);
    snapped_dest = snap_rect_to_grid(*dest, BLASTMONIDZ_WINDOW_ASSET_GRID);
    inner = inset_rect(snapped_dest, 2, 2);
    draw_panel(hdc, &snapped_dest, mix_color(primary, secondary, 1, 2), mix_color(secondary, blastmonidz_style.background, 1, 3), tertiary, 18);

    if (path_has(bitmap->source_path, "Paint")) {
        RECT pool = inset_rect(inner, 4, 4);
        draw_norm_blob_ellipse(hdc, &pool, 8, 18, 58, 56, primary, tertiary);
        draw_norm_blob_ellipse(hdc, &pool, 34, 8, 46, 46, secondary, tertiary);
        draw_norm_blob_ellipse(hdc, &pool, 54, 44, 20, 22, mix_color(primary, blastmonidz_style.text, 1, 4), tertiary);
        draw_norm_blob_line(hdc, &pool, 28, 18, 68, 62, rect_width(&pool) / 10, tertiary, primary);
    } else if (path_has(bitmap->source_path, "bombPouch")) {
        draw_norm_blob_rect(hdc, &inner, 20, 18, 58, 60, 12, secondary, tertiary);
        draw_norm_blob_line(hdc, &inner, 24, 26, 78, 14, rect_width(&inner) / 12, primary, tertiary);
        draw_norm_blob_ellipse(hdc, &inner, 34, 34, 24, 20, primary, tertiary);
    } else if (path_has(bitmap->source_path, "bomb") || path_has(bitmap->source_path, "core")) {
        draw_norm_blob_ellipse(hdc, &inner, 18, 24, 64, 60, primary, tertiary);
        draw_norm_blob_line(hdc, &inner, 58, 22, 78, 6, rect_width(&inner) / 12, secondary, tertiary);
        draw_norm_blob_ellipse(hdc, &inner, 74, 2 + (pulse % 3) * 5, 10, 10, blastmonidz_style.text, tertiary);
        draw_norm_blob_rect(hdc, &inner, 34, 40, 16, 16, 8, secondary, tertiary);
    } else if (path_has(bitmap->source_path, "crate") || path_has(bitmap->source_path, "door") || path_has(bitmap->source_path, "gunPowder")) {
        int slat;
        draw_norm_blob_rect(hdc, &inner, 10, 12, 80, 76, 14, secondary, tertiary);
        for (slat = 0; slat < 3; ++slat) {
            draw_norm_blob_rect(hdc, &inner, 18 + slat * 22, 20, 14, 60, 8, primary, tertiary);
        }
        draw_norm_blob_line(hdc, &inner, 16, 20, 84, 82, rect_width(&inner) / 14, tertiary, primary);
        draw_norm_blob_line(hdc, &inner, 84, 20, 16, 82, rect_width(&inner) / 16, tertiary, primary);
    } else if (path_has(bitmap->source_path, "titleScreen")) {
        draw_norm_blob_ellipse(hdc, &inner, 4, 14, 34, 52, secondary, tertiary);
        draw_norm_blob_ellipse(hdc, &inner, 30, 10, 38, 60, primary, tertiary);
        draw_norm_blob_ellipse(hdc, &inner, 62, 18, 26, 44, mix_color(primary, blastmonidz_style.text, 1, 5), tertiary);
        draw_text_block(hdc, inner.left + rect_width(&inner) / 6, inner.top + rect_height(&inner) / 5, rect_width(&inner) * 2 / 3, rect_height(&inner) * 2 / 3, "BM", rect_height(&inner) / 3, FW_BOLD, tertiary);
    } else if (path_has(bitmap->source_path, "Walk") || path_has(bitmap->source_path, "baddie")) {
        RECT body = {inner.left + rect_width(&inner) / 5, inner.top + rect_height(&inner) / 4, inner.right - rect_width(&inner) / 5, inner.bottom - rect_height(&inner) / 7};
        RECT head = {inner.left + rect_width(&inner) / 3, inner.top + rect_height(&inner) / 10, inner.right - rect_width(&inner) / 3, inner.top + rect_height(&inner) / 2};
        Color body_color = path_has(bitmap->source_path, "baddie") ? secondary : primary;
        Color accent = path_has(bitmap->source_path, "baddie") ? blastmonidz_style.ghost : blastmonidz_style.accent;
        fill_ellipse_color(hdc, &body, body_color, tertiary);
        fill_ellipse_color(hdc, &head, accent, tertiary);
        draw_blob_line(hdc, body.left + rect_width(&body) / 4, body.bottom - 4, body.left + rect_width(&body) / 5, inner.bottom - 2, rect_width(&inner) / 10, tertiary, body_color);
        draw_blob_line(hdc, body.right - rect_width(&body) / 4, body.bottom - 4, body.right - rect_width(&body) / 5, inner.bottom - 2, rect_width(&inner) / 10, tertiary, body_color);
        draw_blob_line(hdc, body.left + 4, body.top + rect_height(&body) / 3, inner.left + 4, body.top + rect_height(&body) / 2 + (pulse % 2) * 3, rect_width(&inner) / 12, accent, tertiary);
        draw_blob_line(hdc, body.right - 4, body.top + rect_height(&body) / 3, inner.right - 4, body.top + rect_height(&body) / 2 + ((pulse + 1) % 2) * 3, rect_width(&inner) / 12, accent, tertiary);
        draw_norm_blob_ellipse(hdc, &head, 26, 34, 12, 14, tertiary, body_color);
        draw_norm_blob_ellipse(hdc, &head, 62, 34, 12, 14, tertiary, body_color);
    } else if (path_has(bitmap->source_path, "tile")) {
        draw_norm_blob_rect(hdc, &inner, 8, 8, 84, 84, 12, secondary, tertiary);
        draw_norm_blob_line(hdc, &inner, 12, 30, 88, 30, rect_width(&inner) / 14, primary, tertiary);
        draw_norm_blob_line(hdc, &inner, 22, 58, 78, 58, rect_width(&inner) / 16, tertiary, primary);
        draw_norm_blob_line(hdc, &inner, 30, 12, 30, 88, rect_width(&inner) / 18, primary, tertiary);
    } else {
        draw_norm_blob_ellipse(hdc, &inner, 14, 16, 72, 68, primary, tertiary);
        draw_norm_blob_rect(hdc, &inner, 22, 28, 56, 40, 10, secondary, tertiary);
    }
}

static void draw_archive_bitmap_warped(HDC hdc, const POINT points[3], const ArchiveBitmap *bitmap) {
    RECT bounds;
    if (!bitmap) {
        return;
    }
    bounds.left = points[0].x < points[2].x ? points[0].x : points[2].x;
    bounds.top = points[0].y < points[1].y ? points[0].y : points[1].y;
    bounds.right = points[1].x > points[2].x ? points[1].x : points[2].x;
    bounds.bottom = points[2].y;
    draw_archive_bitmap(hdc, &bounds, bitmap, 255);
}

static const char *player_direction_name(int direction) {
    switch (direction) {
        case 1: return "back";
        case 2: return "side";
        default: return "front";
    }
}

static const ArchiveBitmap *get_crate_bitmap(const GameState *state, int world_x, int world_y) {
    int variant = blastmonidz_select_crate_variant(state, world_x, world_y);
    if (variant < 0 || variant >= BLASTMONIDZ_CRATE_VARIANTS) {
        variant = 0;
    }
    return g_crate_variants[variant].loaded ? &g_crate_variants[variant] : &g_crate_variants[0];
}

static const ArchiveBitmap *get_player_sprite_bitmap(const GameState *state, int player_id, int *use_rival, int *family, int *direction, int *frame) {
    int selected_rival = 0;
    int selected_family = 0;
    int selected_direction = 0;
    int selected_frame = 0;
    blastmonidz_select_player_visual(state, player_id, &selected_rival, &selected_family, &selected_direction, &selected_frame);
    if (use_rival) {
        *use_rival = selected_rival;
    }
    if (family) {
        *family = selected_family;
    }
    if (direction) {
        *direction = selected_direction;
    }
    if (frame) {
        *frame = selected_frame;
    }
    selected_frame = (selected_frame + organism_frame_offset(state)) % BLASTMONIDZ_PLAYER_FRAMES;
    if (selected_rival) {
        if (selected_direction == 1 && g_rival_back_sprites[selected_frame].loaded) {
            return &g_rival_back_sprites[selected_frame];
        }
        if (selected_family < 0 || selected_family >= BLASTMONIDZ_RIVAL_FAMILIES) {
            selected_family = 0;
        }
        if (g_rival_side_sprites[selected_family][selected_frame].loaded) {
            return &g_rival_side_sprites[selected_family][selected_frame];
        }
    }
    if (selected_family < 0 || selected_family >= BLASTMONIDZ_HERO_FAMILIES) {
        selected_family = 0;
    }
    if (selected_direction < 0 || selected_direction >= BLASTMONIDZ_PLAYER_DIRECTIONS) {
        selected_direction = 0;
    }
    return &g_player_sprites[selected_family][selected_direction][selected_frame];
}

static int count_active_bombs(const GameState *state) {
    int active = 0;
    int bomb_id;
    if (!state) {
        return 0;
    }
    for (bomb_id = 0; bomb_id < MAX_BOMBS; ++bomb_id) {
        if (state->arena.bombs[bomb_id].active) {
            ++active;
        }
    }
    return active;
}

static int find_live_leader_id(const GameState *state) {
    int player_id;
    int best_score = -9999;
    int leader_id = -1;
    if (!state) {
        return -1;
    }
    for (player_id = 0; player_id < MAX_PLAYERS; ++player_id) {
        const BlastKin *player = &state->players[player_id];
        int score = player->run_wins * 30 + player->mon.round_kills * 12 + player->mon.gems_cleared * 4 + player->mon.self_feed.balance;
        if (!player->mon.alive) {
            score -= 40;
        }
        if (score > best_score) {
            best_score = score;
            leader_id = player_id;
        }
    }
    return leader_id;
}

static Color chemistry_color_live(int index) {
    switch (index % 3) {
        case 1:
            return (Color){116, 214, 134, 255};
        case 2:
            return (Color){244, 184, 108, 255};
        default:
            return (Color){118, 180, 255, 255};
    }
}

static Color player_live_core_color(const GameState *state, int player_id) {
    const BlastKin *player = &state->players[player_id];
    const Blastonid *mon = &player->mon;
    Color doctrine_tint = doctrine_color(player->doctrine);
    Color starter_tint = mon->starter->color;
    Color live;
    if (!mon->alive) {
        return mix_color(blastmonidz_style.ghost, doctrine_tint, 1, 4);
    }
    live = mix_color(starter_tint, doctrine_tint, clamp_visual_int(mon->growth_stage + mon->round_kills, 0, 3), 4);
    live = mix_color(live, chemistry_color_live(mon->concoction_id), clamp_visual_int(mon->self_feed.world_signal / 28, 0, 2), 4);
    if (state->world_feed.rival_signal > state->world_feed.balance) {
        live = shift_color(live, 10, -4, 8);
    }
    return live;
}

static void draw_live_floor_tile(HDC hdc, const RECT *tile, const GameState *state, int world_x, int world_y, unsigned char tile_type) {
    const BlastmonidzHomeTile *home_tile = blastmonidz_select_home_tile(state, world_x, world_y);
    int chemistry_index = (world_x + world_y + state->consensus_tick / 5) % 3;
    int chemistry_value = state->arena.chemistry[chemistry_index];
    int pressure = clamp_visual_int(state->arena.mineral_pressure + count_active_bombs(state) * 6 + state->world_feed.rival_signal / 2, 0, 180);
    Color chemistry_tint = chemistry_color_live(chemistry_index);
    Color top = mix_color(blastmonidz_style.floor, chemistry_tint, clamp_visual_int(chemistry_value / 10, 0, 3), 5);
    Color bottom = mix_color(blastmonidz_style.background, chemistry_tint, clamp_visual_int(state->world_feed.world_signal / 25, 0, 2), 5);
    Color edge = mix_color(blastmonidz_style.panel_edge, chemistry_tint, pressure > 90 ? 2 : 1, 4);
    RECT inner = inset_rect(*tile, 1, 1);
    if (tile_type == TILE_WALL) {
        fill_gradient_rect(hdc, tile, mix_color(blastmonidz_style.wall, chemistry_tint, 1, 5), shift_color(blastmonidz_style.wall, -18, -14, -6), 1);
        draw_norm_blob_rect(hdc, &inner, 18, 16, 64, 20, 8, shift_color(blastmonidz_style.wall, 12, 8, 6), edge);
        draw_norm_blob_rect(hdc, &inner, 10, 52, 54, 18, 8, shift_color(blastmonidz_style.wall, -8, -2, 4), edge);
        draw_norm_blob_line(hdc, &inner, 16, 28, 84, 26, rect_width(&inner) / 12, edge, blastmonidz_style.wall);
        draw_norm_blob_line(hdc, &inner, 24, 68, 70, 66, rect_width(&inner) / 14, edge, blastmonidz_style.wall);
        return;
    }
    draw_panel(hdc, tile, top, bottom, edge, 10);
    draw_home_tile_pattern(hdc, &inner, home_tile, mix_color(chemistry_tint, blastmonidz_style.text, 1, 2));
    if ((world_x + world_y + state->consensus_tick / 8) % 3 == 0) {
        draw_norm_blob_line(hdc, &inner, 16, 26, 82, 30, rect_width(&inner) / 14, alpha_mix(chemistry_tint, 160), edge);
    }
    if (pressure > 55) {
        draw_norm_blob_ellipse(hdc, &inner, 20 + (world_x % 3) * 10, 54 - (world_y % 2) * 10, 18, 14, alpha_mix(chemistry_tint, 120), edge);
    }
    if (state->world_feed.ghost_signal > 44 && ((world_x * 3 + world_y + state->consensus_tick / 4) % 5 == 0)) {
        draw_norm_blob_ellipse(hdc, &inner, 56, 20, 18, 24, alpha_mix(blastmonidz_style.ghost, 120), edge);
    }
}

static void draw_live_gem(HDC hdc, const RECT *tile, const GameState *state, int gem_id) {
    const BombGem *gem = &state->arena.gems[gem_id];
    RECT inner = inset_rect(*tile, rect_width(tile) / 7, rect_height(tile) / 7);
    RECT core = inset_rect(inner, rect_width(&inner) / 5, rect_height(&inner) / 5);
    Color base = chemistry_color_live((gem->class_id + gem->tier) % 3);
    Color hot = shift_color(base, gem->tier * 4, gem->stability / 6, 18 - gem->stability / 4);
    int orbit_count = 1 + (gem->tier / 4);
    int orbit;
    draw_norm_blob_ellipse(hdc, &inner, 12, 12, 76, 76, alpha_mix(hot, 180), blastmonidz_style.text);
    draw_norm_blob_rect(hdc, &core, 20, 18, 60, 64, 8, mix_color(hot, blastmonidz_style.text, 1, 4), blastmonidz_style.panel_edge);
    for (orbit = 0; orbit < orbit_count; ++orbit) {
        int orbit_x = 16 + ((orbit * 19 + state->consensus_tick / 2) % 58);
        int orbit_y = 14 + ((orbit * 23 + state->consensus_tick / 3) % 58);
        draw_norm_blob_ellipse(hdc, &inner, orbit_x, orbit_y, 10 + (orbit % 2) * 4, 10 + ((orbit + 1) % 2) * 4, alpha_mix(mix_color(base, blastmonidz_style.text, orbit % 2, 3), 180), blastmonidz_style.panel_edge);
    }
    draw_centered_tile_label(hdc, tile, (char[2]){gem->glyph, '\0'}, rect_width(tile) > 24 ? 14 : 10, blastmonidz_style.text);
}

static void draw_live_bomb(HDC hdc, const RECT *tile, const GameState *state, int bomb_id) {
    const Bomb *bomb = &state->arena.bombs[bomb_id];
    Color chemistry_tint = chemistry_color_live(bomb->chemistry);
    Color owner_tint = (bomb->owner_id >= 0 && bomb->owner_id < MAX_PLAYERS) ? player_live_core_color(state, bomb->owner_id) : blastmonidz_style.accent;
    RECT shell = inset_rect(*tile, 1, 1);
    int spark_shift = (int)((GetTickCount() / 90u + (unsigned int)(bomb_id * 7)) % 18u);
    draw_norm_blob_ellipse(hdc, &shell, 10, 16, 78, 72, mix_color(owner_tint, chemistry_tint, 1, 2), blastmonidz_style.text);
    draw_norm_blob_rect(hdc, &shell, 34, 34, 30, 26, 9, mix_color(chemistry_tint, blastmonidz_style.text, 1, 5), blastmonidz_style.panel_edge);
    draw_norm_blob_line(hdc, &shell, 56, 18, 74, 4 + spark_shift / 4, rect_width(&shell) / 11, chemistry_tint, blastmonidz_style.text);
    draw_norm_blob_ellipse(hdc, &shell, 72, 2 + spark_shift / 2, 12, 12, blastmonidz_style.text, chemistry_tint);
    if (bomb->timer <= 1) {
        draw_norm_blob_ellipse(hdc, &shell, 4, 8, 92, 84, alpha_mix(chemistry_tint, 110), chemistry_tint);
    }
}

static void draw_swallow_nest_motif(HDC hdc, const RECT *rect, Color twig, Color egg, int longing_bias) {
    int lift = clamp_visual_int(longing_bias / 8, 0, 8);
    draw_norm_blob_line(hdc, rect, 18, 82 - lift, 48, 90 - lift, rect_width(rect) / 18, twig, blastmonidz_style.text);
    draw_norm_blob_line(hdc, rect, 48, 90 - lift, 82, 82 - lift, rect_width(rect) / 18, twig, blastmonidz_style.text);
    draw_norm_blob_line(hdc, rect, 22, 76 - lift, 46, 84 - lift, rect_width(rect) / 22, alpha_mix(twig, 170), blastmonidz_style.text);
    draw_norm_blob_line(hdc, rect, 54, 84 - lift, 78, 76 - lift, rect_width(rect) / 22, alpha_mix(twig, 170), blastmonidz_style.text);
    draw_norm_blob_ellipse(hdc, rect, 38, 72 - lift, 10, 14, egg, blastmonidz_style.text);
    draw_norm_blob_ellipse(hdc, rect, 50, 70 - lift, 10, 14, egg, blastmonidz_style.text);
}

static void draw_doctrine_gesture_motif(HDC hdc, const RECT *aura, const RECT *body, const RECT *head, const GameState *state, int player_id, Color accent, Color core, Color edge) {
    const BlastKin *player = &state->players[player_id];
    const Blastonid *mon = &player->mon;
    int gesture_phase = (int)((GetTickCount() / 120u + (unsigned int)(player_id * 9)) % 14u);
    int sweep = 6 + gesture_phase;
    int longing = clamp_visual_int(100 - mon->self_feed.ghost_signal + mon->self_feed.world_signal / 2 + mon->gems_cleared * 6, 18, 120);
    switch (player->doctrine) {
        case BLASTMONIDZ_DOCTRINE_HARMONIZER:
            draw_norm_blob_line(hdc, aura, 16, 46, 46, 26 - gesture_phase / 4, rect_width(aura) / 14, accent, edge);
            draw_norm_blob_line(hdc, aura, 84, 46, 54, 26 - gesture_phase / 4, rect_width(aura) / 14, accent, edge);
            draw_norm_blob_line(hdc, aura, 20, 62, 48, 54, rect_width(aura) / 16, alpha_mix(core, 180), edge);
            draw_norm_blob_line(hdc, aura, 80, 62, 52, 54, rect_width(aura) / 16, alpha_mix(core, 180), edge);
            break;
        case BLASTMONIDZ_DOCTRINE_STEWARD:
            draw_norm_blob_rect(hdc, body, 24, 54, 52, 14, 7, alpha_mix(core, 190), edge);
            draw_norm_blob_line(hdc, aura, 34, 28, 24, 66 + gesture_phase / 2, rect_width(aura) / 16, accent, edge);
            draw_norm_blob_line(hdc, aura, 66, 28, 76, 66 + gesture_phase / 2, rect_width(aura) / 16, accent, edge);
            draw_swallow_nest_motif(hdc, aura, alpha_mix(accent, 190), alpha_mix(blastmonidz_style.text, 215), longing);
            break;
        case BLASTMONIDZ_DOCTRINE_MEDIATOR:
            draw_norm_blob_line(hdc, aura, 18, 58, 42, 34 - gesture_phase / 5, rect_width(aura) / 15, accent, edge);
            draw_norm_blob_line(hdc, aura, 82, 58, 58, 34 - gesture_phase / 5, rect_width(aura) / 15, accent, edge);
            draw_norm_blob_line(hdc, aura, 42, 34, 58, 34, rect_width(aura) / 18, blastmonidz_style.text, edge);
            draw_norm_blob_ellipse(hdc, head, 42, 8, 16, 12, alpha_mix(blastmonidz_style.text, 170), accent);
            break;
        case BLASTMONIDZ_DOCTRINE_KINWEAVER:
            draw_norm_blob_line(hdc, aura, 28, 44, 12, 22 + sweep / 3, rect_width(aura) / 16, accent, edge);
            draw_norm_blob_line(hdc, aura, 72, 44, 88, 22 + sweep / 3, rect_width(aura) / 16, accent, edge);
            draw_norm_blob_line(hdc, aura, 34, 78, 18, 92, rect_width(aura) / 18, alpha_mix(core, 190), edge);
            draw_norm_blob_line(hdc, aura, 66, 78, 82, 92, rect_width(aura) / 18, alpha_mix(core, 190), edge);
            draw_swallow_nest_motif(hdc, aura, alpha_mix(core, 170), alpha_mix(accent, 180), longing / 2);
            break;
        default:
            break;
    }
}

static void draw_live_player(HDC hdc, const RECT *tile, const GameState *state, int player_id) {
    const BlastKin *player = &state->players[player_id];
    const Blastonid *mon = &player->mon;
    Color core = player_live_core_color(state, player_id);
    Color accent = doctrine_color(player->doctrine);
    Color edge = mix_color(blastmonidz_style.text, core, 1, 4);
    RECT aura = inset_rect(*tile, -1, -1);
    RECT body = {tile->left + rect_width(tile) / 5, tile->top + rect_height(tile) / 3, tile->right - rect_width(tile) / 5, tile->bottom - rect_height(tile) / 10};
    RECT head = {tile->left + rect_width(tile) / 4, tile->top + rect_height(tile) / 10, tile->right - rect_width(tile) / 4, tile->top + rect_height(tile) / 2};
    RECT face = inset_rect(head, rect_width(&head) / 5, rect_height(&head) / 4);
    int leader = find_live_leader_id(state) == player_id;
    int orbit_count = clamp_visual_int(mon->gems_cleared, 0, 3);
    int orbit;
    if (!mon->alive) {
        int ghost_shift = (int)((GetTickCount() / 130u + (unsigned int)(player_id * 11)) % 10u);
        draw_norm_blob_ellipse(hdc, &aura, 8, 8 + ghost_shift / 2, 84, 78, alpha_mix(blastmonidz_style.ghost, 120), blastmonidz_style.panel_edge);
        fill_ellipse_color(hdc, &body, alpha_mix(blastmonidz_style.ghost, 180), blastmonidz_style.text);
        fill_ellipse_color(hdc, &head, alpha_mix(accent, 150), blastmonidz_style.text);
        draw_norm_blob_line(hdc, &aura, 26, 78, 74, 26, rect_width(&aura) / 12, alpha_mix(blastmonidz_style.text, 160), blastmonidz_style.ghost);
        return;
    }
    if (state->world_feed.balance < 40 || mon->self_feed.rival_signal > mon->self_feed.balance) {
        draw_norm_blob_ellipse(hdc, &aura, 4, 6, 92, 84, alpha_mix(shift_color(accent, 16, -8, 8), 110), accent);
    } else {
        draw_norm_blob_ellipse(hdc, &aura, 10, 10, 80, 76, alpha_mix(core, 90), edge);
    }
    draw_doctrine_gesture_motif(hdc, &aura, &body, &head, state, player_id, accent, core, edge);
    fill_ellipse_color(hdc, &body, mix_color(core, accent, mon->growth_stage, 5), edge);
    fill_ellipse_color(hdc, &head, mix_color(accent, blastmonidz_style.text, mon->precision_chain > 0 ? 1 : 0, 6), edge);
    draw_norm_blob_rect(hdc, &body, 26, 32, 48, 18, 8, alpha_mix(blastmonidz_style.text, 160), edge);
    draw_norm_blob_ellipse(hdc, &face, 20, 34, mon->health * 2 < mon->max_health ? 12 : 10, 10, blastmonidz_style.text, core);
    draw_norm_blob_ellipse(hdc, &face, 66, 34, mon->health * 2 < mon->max_health ? 12 : 10, 10, blastmonidz_style.text, core);
    if (mon->growth_stage > 0) {
        draw_norm_blob_ellipse(hdc, &head, 10, 2, 16, 18, accent, edge);
        draw_norm_blob_ellipse(hdc, &head, 42, 0, 18, 20, chemistry_color_live(mon->concoction_id), edge);
        draw_norm_blob_ellipse(hdc, &head, 74, 2, 16, 18, accent, edge);
    }
    if (leader) {
        draw_norm_blob_rect(hdc, &aura, 30, 2, 40, 12, 6, mix_color(blastmonidz_style.text, chemistry_color_live(mon->concoction_id), 1, 4), edge);
        draw_norm_blob_ellipse(hdc, &aura, 28, 0, 10, 10, blastmonidz_style.text, edge);
        draw_norm_blob_ellipse(hdc, &aura, 46, 0, 10, 10, blastmonidz_style.text, edge);
        draw_norm_blob_ellipse(hdc, &aura, 64, 0, 10, 10, blastmonidz_style.text, edge);
    }
    for (orbit = 0; orbit < orbit_count; ++orbit) {
        int orbit_x = 8 + ((orbit * 27 + state->consensus_tick / 2) % 70);
        int orbit_y = 14 + ((orbit * 19 + state->consensus_tick / 3) % 56);
        draw_norm_blob_ellipse(hdc, &aura, orbit_x, orbit_y, 10, 10, alpha_mix(chemistry_color_live((mon->concoction_id + orbit) % 3), 180), edge);
    }
    if (mon->round_kills > 0) {
        draw_norm_blob_line(hdc, &body, 20, 18, 80, 78, rect_width(&body) / 16, alpha_mix(blastmonidz_style.text, 190), accent);
    }
    if (mon->precision_chain > 0) {
        draw_norm_blob_line(hdc, &aura, 50, 12, 50, 30, rect_width(&aura) / 16, blastmonidz_style.text, accent);
        draw_norm_blob_line(hdc, &aura, 40, 21, 60, 21, rect_width(&aura) / 16, blastmonidz_style.text, accent);
    }
    if (mon->bomb_cooldown > 0) {
        draw_norm_blob_rect(hdc, &body, 56, 56, 20, 18, 6, chemistry_color_live(mon->concoction_id), edge);
    }
    if (mon->self_feed.world_signal > mon->self_feed.rival_signal && mon->ghost_timer == 0) {
        draw_swallow_nest_motif(hdc, &aura, alpha_mix(mix_color(core, accent, 1, 2), 160), alpha_mix(blastmonidz_style.text, 220), mon->self_feed.world_signal);
    }
}

static void draw_player_personality_emblem(HDC hdc, const RECT *rect, const GameState *state, int player_id) {
    const BlastKin *player = &state->players[player_id];
    const Blastonid *mon = &player->mon;
    Color fill = player_live_core_color(state, player_id);
    Color accent = doctrine_color(player->doctrine);
    RECT badge = inset_rect(*rect, 2, 2);
    draw_panel(hdc, &badge, mix_color(fill, accent, 1, 2), mix_color(fill, blastmonidz_style.background, 1, 3), blastmonidz_style.text, 12);
    draw_live_player(hdc, &badge, state, player_id);
    if (mon->alive && mon->self_feed.balance > 65) {
        draw_norm_blob_rect(hdc, &badge, 14, 72, 72, 10, 6, alpha_mix(chemistry_color_live(mon->concoction_id), 160), blastmonidz_style.text);
    }
    if (mon->alive && (mon->gems_cleared > 0 || mon->self_feed.world_signal > 58)) {
        draw_swallow_nest_motif(hdc, &badge, alpha_mix(accent, 170), alpha_mix(blastmonidz_style.text, 220), mon->self_feed.world_signal + mon->gems_cleared * 8);
    }
}

static void draw_home_tile_pattern(HDC hdc, const RECT *tile, const BlastmonidzHomeTile *home_tile, Color base_color) {
    HPEN pen;
    HPEN old_pen;
    int mid_x;
    int mid_y;
    if (!tile || !home_tile) {
        return;
    }
    mid_x = (tile->left + tile->right) / 2;
    mid_y = (tile->top + tile->bottom) / 2;
    pen = CreatePen(PS_SOLID, 1, to_rgb(base_color));
    old_pen = (HPEN)SelectObject(hdc, pen);
    switch (home_tile->glyph) {
        case 'a':
            MoveToEx(hdc, tile->left + 2, tile->bottom - 3, NULL);
            LineTo(hdc, tile->right - 2, tile->bottom - 3);
            break;
        case 'c':
            MoveToEx(hdc, tile->left + 2, mid_y, NULL);
            LineTo(hdc, tile->right - 2, mid_y);
            MoveToEx(hdc, mid_x, tile->top + 2, NULL);
            LineTo(hdc, mid_x, tile->bottom - 2);
            break;
        case 's':
            Arc(hdc, tile->left + 1, tile->top + 1, tile->right - 1, tile->bottom - 1, tile->left + 1, mid_y, tile->right - 1, mid_y);
            break;
        case 'b':
            Arc(hdc, tile->left + 2, tile->top + 2, tile->right - 2, tile->bottom - 2, tile->left + 2, tile->bottom - 2, tile->right - 2, tile->bottom - 2);
            break;
        case 'g':
            MoveToEx(hdc, tile->left + 3, tile->top + 3, NULL);
            LineTo(hdc, tile->right - 3, tile->bottom - 3);
            break;
        case 'k':
            MoveToEx(hdc, tile->left + 2, tile->top + 3, NULL);
            LineTo(hdc, tile->right - 2, tile->bottom - 3);
            MoveToEx(hdc, tile->right - 2, tile->top + 3, NULL);
            LineTo(hdc, tile->left + 2, tile->bottom - 3);
            break;
        case 'r':
            MoveToEx(hdc, mid_x, tile->top + 2, NULL);
            LineTo(hdc, mid_x, tile->bottom - 2);
            MoveToEx(hdc, mid_x, tile->bottom - 4, NULL);
            LineTo(hdc, tile->left + 3, tile->bottom - 2);
            MoveToEx(hdc, mid_x, tile->bottom - 4, NULL);
            LineTo(hdc, tile->right - 3, tile->bottom - 2);
            break;
        case 'p':
            Rectangle(hdc, tile->left + 3, tile->top + 3, tile->right - 3, tile->bottom - 3);
            break;
        case 'v':
            MoveToEx(hdc, tile->left + 2, tile->bottom - 3, NULL);
            LineTo(hdc, mid_x, tile->top + 2);
            LineTo(hdc, tile->right - 2, tile->bottom - 3);
            break;
        case 'm':
            MoveToEx(hdc, tile->left + 2, tile->bottom - 4, NULL);
            LineTo(hdc, tile->right - 2, tile->bottom - 4);
            MoveToEx(hdc, tile->left + 4, mid_y, NULL);
            LineTo(hdc, tile->right - 4, mid_y);
            break;
        default:
            break;
    }
    SelectObject(hdc, old_pen);
    DeleteObject(pen);
}

static void draw_centered_tile_label(HDC hdc, const RECT *tile, const char *text, int size, Color color) {
    draw_text_block(hdc,
        tile->left,
        tile->top + ((tile->bottom - tile->top) - size - 2) / 2,
        tile->right - tile->left,
        size + 8,
        text,
        size,
        FW_BOLD,
        color);
}

static const ArchiveBitmap *get_archive_preview_bitmap(int index) {
    switch (index) {
        case 0: return &g_title_logo;
        case 1: return &g_title_backdrop;
        case 2: return &g_player_sprites[0][0][0];
        case 3: return &g_player_sprites[0][1][0];
        case 4: return &g_player_sprites[1][2][0];
        case 5: return &g_bomb_frames[3];
        case 6: return &g_bomb_frames[9];
        case 7: return &g_title_backdrop;
        case 8: return &g_floor_tile;
        case 9: return &g_player_sprites[2][0][6];
        case 10: return &g_player_sprites[3][1][10];
        case 11: return &g_rival_side_sprites[0][4];
        case 12: return &g_rival_back_sprites[7];
        case 13: return &g_player_sprites[1][0][11];
        case 14: return &g_player_sprites[2][1][13];
        case 15: return &g_player_sprites[3][2][15];
        default: return NULL;
    }
}

static void draw_title_cobblestone_arena(HDC hdc, const RECT *rect, const TitleVisualState *visual) {
    int row;
    int column;
    int tile_w = 72;
    int tile_h = 42;
    int active_x = rect->left + ((visual->active_button == 0) ? (rect->right - rect->left) / 2 - 96 : (rect->right - rect->left) / 2 + 96);
    int active_y = rect->top + (rect->bottom - rect->top) / 2 + 18;
    fill_gradient_rect(hdc, rect, mix_color(visual->secondary_tint, blastmonidz_style.background, 1, 3), mix_color(blastmonidz_style.background, visual->tertiary_tint, 1, 4), 1);
    for (row = 0; row < 9; ++row) {
        int row_offset = (row & 1) ? tile_w / 2 : 0;
        for (column = 0; column < 11; ++column) {
            RECT tile = {
                rect->left + 28 + column * tile_w - row_offset,
                rect->top + 30 + row * tile_h,
                rect->left + 28 + column * tile_w - row_offset + tile_w - 10,
                rect->top + 30 + row * tile_h + tile_h - 8
            };
            int center_x = (tile.left + tile.right) / 2;
            int center_y = (tile.top + tile.bottom) / 2;
            int influence = 255 - (abs(center_x - active_x) + abs(center_y - active_y)) / 2;
            int paint_index = (visual->ecology_phase + row + column + visual->active_button) % BLASTMONIDZ_PAINT_VARIANTS;
            Color edge = shift_color(mix_color(visual->secondary_tint, visual->primary_tint, (row + column) % 2, 2), row * 2, column, influence > 140 ? 12 : 0);
            draw_panel(hdc, &tile, mix_color(blastmonidz_style.floor, visual->tertiary_tint, 1, 5), mix_color(blastmonidz_style.floor, blastmonidz_style.background, 1, 2), edge, 12);
            if (g_floor_tile.loaded) {
                RECT preview = inset_rect(tile, 3, 3);
                draw_archive_bitmap(hdc, &preview, &g_floor_tile, 220);
            }
            if (influence > 74 && g_gem_paints[paint_index].loaded) {
                RECT overlay = inset_rect(tile, 2, 2);
                int alpha = clamp_visual_int(36 + influence / 4 + (visual->switch_progress / 4), 48, 188);
                draw_archive_bitmap(hdc, &overlay, &g_gem_paints[paint_index], alpha);
            }
        }
    }
}

static void draw_title_button_object(HDC hdc, const RECT *rect, const char *label, const TitleVisualState *visual, int active, int paint_index) {
    RECT pedestal = *rect;
    RECT core = inset_rect(*rect, 18, 18);
    RECT glyph = {core.left + 20, core.top + 14, core.right - 20, core.bottom - 44};
    Color edge = active ? visual->primary_tint : mix_color(visual->secondary_tint, blastmonidz_style.panel_edge, 1, 2);
    Color top = active ? mix_color(visual->primary_tint, blastmonidz_style.panel, 1, 3) : mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2);
    Color bottom = active ? mix_color(visual->secondary_tint, blastmonidz_style.background, 1, 3) : blastmonidz_style.panel;
    draw_panel(hdc, &pedestal, top, bottom, edge, 26);
    if (g_bomb_frames[(visual->pulse + paint_index * 3) % BLASTMONIDZ_PLAYER_FRAMES].loaded) {
        RECT bomb = {glyph.left + 24, glyph.top + 8, glyph.right - 24, glyph.bottom - 16};
        draw_archive_bitmap(hdc, &bomb, &g_bomb_frames[(visual->pulse + paint_index * 3) % BLASTMONIDZ_PLAYER_FRAMES], active ? 232 : 150);
    }
    if (g_gem_paints[paint_index].loaded) {
        RECT mist = inset_rect(pedestal, 6, 6);
        draw_archive_bitmap(hdc, &mist, &g_gem_paints[paint_index], active ? organism_overlay_alpha(160) : organism_overlay_alpha(90));
    }
    draw_text_block(hdc, core.left, core.bottom - 26, core.right - core.left, 24, label, 22, FW_BOLD, blastmonidz_style.text);
}

static void draw_title_character_pose(HDC hdc, const RECT *rect, const TitleVisualState *visual) {
    const ArchiveBitmap *sprite = &g_player_sprites[0][2][(visual->pulse + visual->frame_stride) % BLASTMONIDZ_PLAYER_FRAMES];
    POINT warp[3];
    RECT bomb = {rect->left - 26, rect->top - 6, rect->left + 92, rect->top + 118};
    RECT shadow = {rect->right - 58, rect->bottom - 18, rect->right - 10, rect->bottom - 6};
    RECT aura = {rect->left - 32, rect->top + 12, rect->right + 22, rect->bottom + 6};
    if (g_gem_paints[(visual->ecology_phase + 1) % BLASTMONIDZ_PAINT_VARIANTS].loaded) {
        draw_archive_bitmap(hdc, &aura, &g_gem_paints[(visual->ecology_phase + 1) % BLASTMONIDZ_PAINT_VARIANTS], organism_overlay_alpha(128));
    }
    fill_gradient_rect(hdc, &shadow, mix_color(blastmonidz_style.background, visual->secondary_tint, 1, 4), blastmonidz_style.background, 0);
    if (sprite->loaded) {
        warp[0].x = rect->left + 30;
        warp[0].y = rect->top + 6;
        warp[1].x = rect->right - 18;
        warp[1].y = rect->top + 24;
        warp[2].x = rect->left + 18;
        warp[2].y = rect->bottom - 8;
        draw_archive_bitmap_warped(hdc, warp, sprite);
    }
    if (g_bomb_frames[(visual->pulse + visual->frame_stride * 2) % BLASTMONIDZ_PLAYER_FRAMES].loaded) {
        draw_archive_bitmap(hdc, &bomb, &g_bomb_frames[(visual->pulse + visual->frame_stride * 2) % BLASTMONIDZ_PLAYER_FRAMES], 255);
    }
    draw_text_block(hdc, rect->left - 4, rect->bottom - 78, rect->right - rect->left + 40, 34, "INTREPID BALANCE", 22, FW_BOLD, visual->primary_tint);
    draw_text_block(hdc, rect->left - 4, rect->bottom - 42, rect->right - rect->left + 36, 38, "Right-foot tip stance // left-hand bomb hoist", 15, FW_NORMAL, blastmonidz_style.text);
}

static void draw_title_scene(HDC hdc, RECT client) {
    RECT full = {0, 0, client.right, client.bottom};
    RECT logo_rect = {74, 34, client.right / 2 + 84, 178};
    RECT arena_rect = {72, 188, client.right - 72, client.bottom - 118};
    RECT left_button = {client.right / 2 - 210, client.bottom / 2 - 34, client.right / 2 - 34, client.bottom / 2 + 172};
    RECT right_button = {client.right / 2 + 34, client.bottom / 2 - 34, client.right / 2 + 210, client.bottom / 2 + 172};
    RECT character_rect = {client.right - client.right / 5 - 64, 92, client.right - 54, client.bottom / 2 + 116};
    RECT ecology_panel = {82, client.bottom - 104, client.right / 2 + 40, client.bottom - 34};
    RECT signal_panel = {client.right / 2 + 54, client.bottom - 104, client.right - 82, client.bottom - 34};
    const AssetArchetype *logo_asset = blastmonidz_title_logo_asset();
    const AssetArchetype *backdrop_asset = blastmonidz_title_backdrop_asset();
    const AssetArchetype *motion_asset = blastmonidz_primary_motion_asset();
    DWORD now = GetTickCount();
    TitleVisualState visual;
    char status[512];
    char feature_text[512];
    const char *backdrop_status = g_title_backdrop.loaded ? blastmonidz_title_backdrop_asset()->archive_entry : "not loaded";
    const char *logo_status = g_title_logo.loaded ? blastmonidz_title_logo_asset()->archive_entry : "not loaded";
    const char *arena_status = g_floor_tile.loaded ? "procedural pool online" : "not loaded";

    build_title_visual_state(now, &visual);

    fill_gradient_rect(hdc, &full, mix_color(blastmonidz_style.background, visual.secondary_tint, 1, 2), shift_color(blastmonidz_style.background, -4, -2, 10), 1);
    if (g_title_backdrop.loaded) {
        draw_archive_bitmap(hdc, &full, &g_title_backdrop, 138);
    }
    draw_title_cobblestone_arena(hdc, &arena_rect, &visual);
    if (g_gem_paints[visual.ecology_phase].loaded) {
        RECT ecology = {arena_rect.left + 12, arena_rect.top + 12, arena_rect.right - 12, arena_rect.bottom - 12};
        draw_archive_bitmap(hdc, &ecology, &g_gem_paints[visual.ecology_phase], organism_overlay_alpha(82 + visual.switch_progress / 2));
    }
    if (g_title_logo.loaded) {
        draw_panel(hdc, &logo_rect, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 3), blastmonidz_style.panel, visual.primary_tint, 26);
        draw_archive_bitmap(hdc, &logo_rect, &g_title_logo, 255);
    }

    draw_text_block(hdc, 88, 42, client.right - 176, 64, "BLASTMONIDZ", 60, FW_BOLD, visual.primary_tint);
    draw_text_block(hdc, 92, 108, client.right - 420, 32, "CONSENSUS ARENA // COBBLESTONE CORONATION", 22, FW_SEMIBOLD, blastmonidz_style.text);
    draw_text_block(hdc, 92, 136, client.right - 520, 46,
        "Play and Load stand as central arena relics. Their switching pulse vents bomb-born biochemical atmosphere that steers the living color of the floor.",
        16, FW_NORMAL, blastmonidz_style.text);

    {
        RECT badge_left = {92, 18, 284, 52};
        RECT badge_right = {client.right - 312, 18, client.right - 92, 52};
        draw_pill(hdc, &badge_left, mix_color(visual.primary_tint, blastmonidz_style.background, 1, 3), visual.primary_tint, "AMBIENT FANFARE ONLINE", blastmonidz_style.text);
        draw_pill(hdc, &badge_right, mix_color(visual.secondary_tint, blastmonidz_style.background, 1, 2), visual.secondary_tint, "BIO-CHEM TITLE REACTOR", blastmonidz_style.text);
    }

    draw_title_button_object(hdc, &left_button, "PLAY", &visual, visual.active_button == 0, visual.ecology_phase);
    draw_title_button_object(hdc, &right_button, "LOAD", &visual, visual.active_button == 1, (visual.ecology_phase + 2) % BLASTMONIDZ_PAINT_VARIANTS);
    draw_title_character_pose(hdc, &character_rect, &visual);

    snprintf(feature_text, sizeof(feature_text),
        "Feature burst: %s\nArchive plate: %s\nBackdrop: %s\nMotion source: %s\nSwitch pulse: %d%% toward %s",
        kTitleFeatureBursts[visual.burst_index],
        logo_asset->archive_entry,
        backdrop_asset->archive_entry,
        motion_asset->archive_entry,
        visual.switch_progress,
        visual.active_button == 0 ? "PLAY" : "LOAD");

    snprintf(status, sizeof(status),
        "Arena render status: backdrop %s // logo %s // cobblestone %s // pulse frame %02d // ecology mode %s // active core %s",
        backdrop_status,
        logo_status,
        arena_status,
        visual.pulse + 1,
        kTitleArrangementModes[visual.arrangement_index],
        visual.active_button == 0 ? "PLAY" : "LOAD");
    draw_panel(hdc, &ecology_panel, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, visual.secondary_tint, 22);
    draw_text_block(hdc, ecology_panel.left + 18, ecology_panel.top + 10, ecology_panel.right - ecology_panel.left - 36, 22, status, 16, FW_NORMAL, blastmonidz_style.text);
    draw_text_block(hdc, ecology_panel.left + 18, ecology_panel.top + 30, ecology_panel.right - ecology_panel.left - 36, 34, feature_text, 12, FW_NORMAL, visual.tertiary_tint);
    draw_panel(hdc, &signal_panel, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, visual.primary_tint, 22);
    draw_text_block(hdc, signal_panel.left + 18, signal_panel.top + 10, signal_panel.right - signal_panel.left - 36, 24, kTitleRhymes[visual.rhyme_index], 18, FW_BOLD, blastmonidz_style.text);
    draw_text_block(hdc, signal_panel.left + 18, signal_panel.top + 52, signal_panel.right - signal_panel.left - 36, 22, blastmonidz_bridge_latest_status(), 14, FW_NORMAL, visual.primary_tint);
    draw_text_block(hdc, signal_panel.left + 18, signal_panel.top + 70, signal_panel.right - signal_panel.left - 36, 22, blastmonidz_bridge_latest_inbox(), 13, FW_NORMAL, visual.tertiary_tint);
}

static void draw_lore_scene(HDC hdc, RECT client) {
    RECT frame = {34, 24, client.right - 34, client.bottom - 24};
    draw_panel(hdc, &frame, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 28);
    draw_text_block(hdc, 58, 48, client.right - 116, 42, "BLASTMONIDZ WORLD BRIEF", 28, FW_BOLD, blastmonidz_style.accent);
    draw_text_block(hdc, 58, 106, client.right - 116, client.bottom - 210,
        "BlastKin are sentient AI entities inhabiting a collective stream-consciousness.\n\n"
        "ArtiSapiens persist as rival profiles inside the same data spectrum. Their encounters are filtered through a consensus timeline buffered at ten times human optical registration.\n\n"
        "Bomb Gems are electromineral obstacles. Explosions rewrite the local chemical atmosphere, while each Blastmonid evolves metabolically and cosmetically against that shifting chemistry field.\n\n"
        "Each combatant also carries a decentralized self-communication feed: inner signal, world attunement, rival pressure, ghost noise, and a rolling balance score. Combat, chemistry, and re-entry all push the same feed.\n\n"
        "Blastminidz remains the handheld spinoff line in-world: micro-cellular descendants cultivated through wireless eco-chemical turf conflicts.",
        18, FW_NORMAL, blastmonidz_style.text);
    {
        RECT badge = {58, client.bottom - 92, 356, client.bottom - 54};
        draw_pill(hdc, &badge, mix_color(blastmonidz_style.accent, blastmonidz_style.background, 1, 3), blastmonidz_style.accent, "LORE MODE // FOCUS READING", blastmonidz_style.text);
    }
    draw_text_block(hdc, 380, client.bottom - 88, client.right - 438, 30, blastmonidz_bridge_latest_status(), 14, FW_NORMAL, blastmonidz_style.text);
}

static void draw_archive_scene(HDC hdc, RECT client) {
    int i;
    int y = 92;
    RECT shell = {32, 22, client.right - 32, client.bottom - 24};
    draw_panel(hdc, &shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 28);
    draw_text_block(hdc, 50, y + 4, client.right - 100, 36, "ARCHIVE COHERENCY MAP", 28, FW_BOLD, blastmonidz_style.accent);
    {
        char organism_line[320];
        blastmonidz_describe_design_organism(&g_design_organism, organism_line, (int)sizeof(organism_line));
        draw_text_block(hdc, 50, 58, client.right - 100, 40, organism_line, 14, FW_NORMAL, blastmonidz_style.text);
    }
    draw_text_block(hdc, 50, 76, client.right - 100, 24, "Representative preview cards from the remapped archive. The console catalog still lists the full source lineage.", 15, FW_NORMAL, blastmonidz_style.text);
    for (i = 0; i < MAX_ARCHIVE_ITEMS; ++i) {
        int column = i / 8;
        int row = i % 8;
        int left = 50 + column * ((client.right - 124) / 2);
        int right = left + ((client.right - 156) / 2);
        RECT card = {left, y + row * 84, right, y + row * 84 + 72};
        RECT preview = {card.left + 10, card.top + 8, card.left + 74, card.bottom - 8};
        const ArchiveBitmap *preview_bitmap = get_archive_preview_bitmap(i);
        char metrics[256];
        draw_panel(hdc, &card, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 18);
        if (preview_bitmap && preview_bitmap->loaded) {
            draw_archive_bitmap(hdc, &preview, preview_bitmap, 255);
        } else {
            fill_rect_color(hdc, &preview, mix_color(blastmonidz_style.panel_edge, blastmonidz_style.background, 1, 2));
        }
        frame_rect_color(hdc, &preview, blastmonidz_style.panel_edge);
        draw_text_block(hdc, card.left + 84, card.top + 8, card.right - card.left - 94, 18, blastmonidz_archive_map[i].blastmonidz_id, 13, FW_BOLD, blastmonidz_style.text);
        draw_text_block(hdc, card.left + 84, card.top + 26, card.right - card.left - 94, 16, blastmonidz_archive_map[i].role, 12, FW_SEMIBOLD, blastmonidz_style.accent);
        if (preview_bitmap && preview_bitmap->analyzed) {
            blastmonidz_describe_asset_profile(&preview_bitmap->profile, metrics, (int)sizeof(metrics));
        } else {
            snprintf(metrics, sizeof(metrics), "%s", blastmonidz_archive_map[i].archive_entry);
        }
        draw_text_block(hdc, card.left + 84, card.top + 42, card.right - card.left - 94, 24, metrics, 11, FW_NORMAL, blastmonidz_style.text);
        if (i == 15) {
            draw_text_block(hdc, 52, client.bottom - 40, client.right - 104, 20, "Archive lineage is analyzed off-screen, but every visible plate here is procedurally regenerated into the Blastmonidz house style.", 13, FW_NORMAL, blastmonidz_style.text);
        }
    }
}

static void draw_starter_scene(HDC hdc, RECT client) {
    int i;
    draw_text_block(hdc, 42, 34, client.right - 84, 36, "STARTER TOKEN DRAW", 28, FW_BOLD, blastmonidz_style.accent);
    if (!g_state) {
        return;
    }
    {
        char world_line[160];
        snprintf(world_line, sizeof(world_line), "Whole-self phase %s | balance %d", blastmonidz_world_phase_name(g_state), g_state->world_feed.balance);
        draw_text_block(hdc, 44, 70, client.right - 88, 24, world_line, 16, FW_SEMIBOLD, blastmonidz_style.text);
    }
    for (i = 0; i < MAX_PLAYERS; ++i) {
        RECT card = {54, 104 + i * 118, client.right - 54, 196 + i * 118};
        int use_rival = 0;
        int family = 0;
        int direction = 0;
        int frame = 0;
        draw_panel(hdc, &card, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 22);
        {
            RECT portrait = {card.left + 12, card.top + 12, card.left + 84, card.bottom - 12};
            const ArchiveBitmap *sprite = get_player_sprite_bitmap(g_state, i, &use_rival, &family, &direction, &frame);
            if (sprite->loaded) {
                draw_archive_bitmap(hdc, &portrait, sprite, 255);
            } else {
                HBRUSH brush = CreateSolidBrush(to_rgb(g_state->players[i].mon.starter->color));
                FillRect(hdc, &portrait, brush);
                DeleteObject(brush);
            }
            frame_rect_color(hdc, &portrait, blastmonidz_style.panel_edge);
        }
        draw_text_block(hdc, card.left + 100, card.top + 10, 360, 28, g_state->players[i].name, 20, FW_BOLD, blastmonidz_style.text);
        draw_text_block(hdc, card.left + 100, card.top + 38, 420, 24, g_state->players[i].mon.starter->name, 18, FW_SEMIBOLD, blastmonidz_style.accent);
        draw_text_block(hdc, card.left + 100, card.top + 62, client.right - card.left - 124, 24, g_state->players[i].mon.starter->growth_family, 15, FW_NORMAL, blastmonidz_style.text);
        {
            char visual_line[256];
            snprintf(visual_line, sizeof(visual_line), "%s | doctrine %s | %s frame %02d | %s | feed %d/%d/%d/%d/%d",
                blastmonidz_growth_title(g_state->players[i].mon.growth_stage),
                blastmonidz_doctrine_name(g_state->players[i].doctrine),
                player_direction_name(direction),
                frame + 1,
                use_rival ? "rival silhouette" : "blastkin silhouette",
                g_state->players[i].mon.self_feed.inner_signal,
                g_state->players[i].mon.self_feed.world_signal,
                g_state->players[i].mon.self_feed.rival_signal,
                g_state->players[i].mon.self_feed.ghost_signal,
                g_state->players[i].mon.self_feed.balance);
            draw_text_block(hdc, card.left + 100, card.top + 82, client.right - card.left - 124, 24, visual_line, 15, FW_NORMAL, blastmonidz_style.text);
        }
    }
}

static void draw_arena_scene(HDC hdc, RECT client) {
    int map_left = 32;
    int map_top = 72;
    int map_width = (client.right * 2) / 3;
    int map_height = client.bottom - 220;
    int side_left = map_left + map_width + 24;
    int i;
    ArenaView view;
    if (!g_state || !g_state->arena.tiles) {
        draw_text_block(hdc, 40, 40, client.right - 80, 40, "Arena unavailable", 22, FW_BOLD, blastmonidz_style.accent);
        return;
    }
    view = blastmonidz_calculate_view(g_state);
    {
        RECT header = {22, 16, client.right - 22, 60};
        char header_line[256];
        draw_panel(hdc, &header, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 22);
        snprintf(header_line, sizeof(header_line), "BLASTMONIDZ ARENA VIEW // %s // seed %08X", blastmonidz_visual_theme_name(g_state), g_state->visuals.run_seed);
        draw_text_block(hdc, 36, 26, client.right - 72, 24, header_line, 24, FW_BOLD, blastmonidz_style.accent);
    }
    draw_meter(hdc, 34, 68, 180, 18, "Ion", g_state->arena.chemistry[0], 24, (Color){118, 180, 255, 255}, (Color){82, 132, 230, 255});
    draw_meter(hdc, 226, 68, 180, 18, "Spore", g_state->arena.chemistry[1], 24, (Color){116, 214, 134, 255}, (Color){66, 148, 90, 255});
    draw_meter(hdc, 418, 68, 180, 18, "Brine", g_state->arena.chemistry[2], 24, (Color){244, 184, 108, 255}, (Color){208, 116, 72, 255});
    {
        int cell_w = map_width / view.width;
        int cell_h = map_height / view.height;
        int cell = cell_w < cell_h ? cell_w : cell_h;
        RECT frame = {map_left - 2, map_top - 2, map_left + view.width * cell + 2, map_top + view.height * cell + 2};
        draw_panel(hdc, &frame, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 16);
        for (i = 0; i < view.height; ++i) {
            int j;
            for (j = 0; j < view.width; ++j) {
                int world_x = view.left + j;
                int world_y = view.top + i;
                RECT tile = {map_left + j * cell, map_top + i * cell, map_left + (j + 1) * cell, map_top + (i + 1) * cell};
                int player_id = blastmonidz_player_at(g_state, world_x, world_y);
                int bomb_id = blastmonidz_bomb_at(&g_state->arena, world_x, world_y);
                int gem_id = blastmonidz_gem_at(&g_state->arena, world_x, world_y);
                unsigned char tile_type = g_state->arena.tiles[world_y * g_state->arena.width + world_x];
                draw_live_floor_tile(hdc, &tile, g_state, world_x, world_y, tile_type);
                if (tile_type == TILE_CRATE) {
                    const ArchiveBitmap *crate_bitmap = get_crate_bitmap(g_state, world_x, world_y);
                    if (crate_bitmap && crate_bitmap->loaded) {
                        RECT inner = {tile.left + 1, tile.top + 1, tile.right - 1, tile.bottom - 1};
                        draw_archive_bitmap(hdc, &inner, crate_bitmap, 255);
                    } else {
                        fill_rect_color(hdc, &tile, blastmonidz_style.crate);
                    }
                }
                frame_rect_color(hdc, &tile, mix_color(blastmonidz_style.panel_edge, blastmonidz_style.background, 1, 3));
                if (gem_id >= 0) {
                    draw_live_gem(hdc, &tile, g_state, gem_id);
                }
                if (bomb_id >= 0) {
                    draw_live_bomb(hdc, &tile, g_state, bomb_id);
                }
                if (player_id >= 0) {
                    draw_live_player(hdc, &tile, g_state, player_id);
                    frame_rect_color(hdc, &tile, mix_color(blastmonidz_style.accent, player_live_core_color(g_state, player_id), 1, 2));
                }
            }
        }
    }
    {
        RECT profile_shell = {side_left - 12, 72, client.right - 26, client.bottom - 150};
        draw_panel(hdc, &profile_shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 22);
    }
    draw_text_block(hdc, side_left, 82, client.right - side_left - 24, 26, "Profiles", 22, FW_BOLD, blastmonidz_style.accent);
    {
        RECT world_shell = {side_left - 6, 114, client.right - 34, 186};
        char world_line[192];
        draw_panel(hdc, &world_shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 18);
        snprintf(world_line, sizeof(world_line), "%s | inner %d | world %d | rival %d | ghost %d | balance %d",
            blastmonidz_world_phase_name(g_state),
            g_state->world_feed.inner_signal,
            g_state->world_feed.world_signal,
            g_state->world_feed.rival_signal,
            g_state->world_feed.ghost_signal,
            g_state->world_feed.balance);
        draw_text_block(hdc, side_left, 126, client.right - side_left - 24, 22, "Whole-Self Communication Feed", 16, FW_BOLD, blastmonidz_style.accent);
        draw_text_block(hdc, side_left, 148, client.right - side_left - 24, 26, world_line, 14, FW_NORMAL, blastmonidz_style.text);
    }
    for (i = 0; i < MAX_PLAYERS; ++i) {
        char line[256];
        Color doctrine_tint = doctrine_color(g_state->players[i].doctrine);
        int use_rival = 0;
        int family = 0;
        int direction = 0;
        int frame = 0;
        RECT icon_rect = {side_left + 4, 204 + i * 84, side_left + 40, 240 + i * 84};
        get_player_sprite_bitmap(g_state, i, &use_rival, &family, &direction, &frame);
        draw_player_personality_emblem(hdc, &icon_rect, g_state, i);
        {
            RECT player_card = {side_left - 6, 194 + i * 84, client.right - 34, 266 + i * 84};
            RECT doctrine_badge = {player_card.right - 132, player_card.top + 8, player_card.right - 12, player_card.top + 34};
            draw_panel(hdc, &player_card, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, doctrine_tint, 18);
            draw_pill(hdc, &doctrine_badge, mix_color(doctrine_tint, blastmonidz_style.background, 1, 3), doctrine_tint, blastmonidz_doctrine_name(g_state->players[i].doctrine), blastmonidz_style.text);
        }
        snprintf(line, sizeof(line), "%s\nDoctrine %s  Wins %d  HP %d/%d  Lag %d\n%s | %s\nFeed %d/%d/%d/%d/%d | %s f%02d\nStyle K%d G%d P%d",
            g_state->players[i].name,
            blastmonidz_doctrine_name(g_state->players[i].doctrine),
            g_state->players[i].run_wins,
            g_state->players[i].mon.health,
            g_state->players[i].mon.max_health,
            g_state->players[i].mon.delay_ticks,
            blastmonidz_growth_title(g_state->players[i].mon.growth_stage),
            blastmonidz_concoctions[g_state->players[i].mon.concoction_id],
            g_state->players[i].mon.self_feed.inner_signal,
            g_state->players[i].mon.self_feed.world_signal,
            g_state->players[i].mon.self_feed.rival_signal,
            g_state->players[i].mon.self_feed.ghost_signal,
            g_state->players[i].mon.self_feed.balance,
            player_direction_name(direction),
            frame + 1,
            g_state->players[i].mon.round_kills,
            g_state->players[i].mon.gems_cleared,
            g_state->players[i].mon.precision_chain);
        draw_text_block(hdc, side_left, 200 + i * 84, client.right - side_left - 24, 72, line, 14, FW_NORMAL, blastmonidz_style.text);
        draw_text_block(hdc, side_left, 254 + i * 84, client.right - side_left - 24, 16, g_state->players[i].ai_debug_line, 12, FW_SEMIBOLD, doctrine_tint);
    }
    {
        RECT events_shell = {24, client.bottom - 144, client.right - 24, client.bottom - 20};
        draw_panel(hdc, &events_shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 20);
    }
    draw_text_block(hdc, 36, client.bottom - 136, client.right - 72, 28, "Recent Events + Bridge", 20, FW_BOLD, blastmonidz_style.accent);
    for (i = 0; i < MAX_LOG_LINES; ++i) {
        if (g_state->log_lines[i][0] != '\0') {
            draw_text_block(hdc, 44, client.bottom - 104 + i * 16, client.right - 88, 18, g_state->log_lines[i], 13, FW_NORMAL, blastmonidz_style.text);
        }
    }
    {
        char tile_line[384];
        char tile_effects[320];
        const BlastmonidzHomeTile *focus_tile = blastmonidz_select_home_tile(g_state, g_state->players[0].mon.x, g_state->players[0].mon.y);
        snprintf(tile_line, sizeof(tile_line), "Home Tile Focus: %s [%c] | %s",
            focus_tile->name,
            focus_tile->glyph,
            focus_tile->theory_role);
        draw_text_block(hdc, 44, client.bottom - 120, client.right - 88, 16, tile_line, 13, FW_SEMIBOLD, blastmonidz_style.accent);
        blastmonidz_describe_home_tile(focus_tile, tile_effects, (int)sizeof(tile_effects));
        draw_text_block(hdc, 44, client.bottom - 104, client.right - 88, 16, tile_effects, 12, FW_NORMAL, blastmonidz_style.text);
    }
    draw_text_block(hdc, 44, client.bottom - 88, client.right - 88, 16, blastmonidz_bridge_latest_status(), 12, FW_NORMAL, blastmonidz_style.text);
    draw_text_block(hdc, 44, client.bottom - 72, client.right - 88, 16, blastmonidz_bridge_latest_inbox(), 12, FW_NORMAL, blastmonidz_style.text);
}

static void draw_summary_scene(HDC hdc, RECT client) {
    int i;
    if (!g_state) {
        return;
    }
    {
        RECT shell = {28, 20, client.right - 28, client.bottom - 24};
        draw_panel(hdc, &shell, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, blastmonidz_style.panel_edge, 28);
    }
    draw_text_block(hdc, 42, 34, client.right - 84, 36, "RUN COMPLETE", 28, FW_BOLD, blastmonidz_style.accent);
    draw_text_block(hdc, 48, 84, client.right - 96, 30, g_state->players[g_state->winner_id].name, 24, FW_BOLD, blastmonidz_style.text);
    {
        RECT crown = {client.right - 300, 34, client.right - 56, 76};
        draw_pill(hdc, &crown, mix_color(blastmonidz_style.accent, blastmonidz_style.background, 1, 3), blastmonidz_style.accent, "SHOWCASE CLEAR", blastmonidz_style.text);
    }
    for (i = 0; i < MAX_PLAYERS; ++i) {
        char line[192];
        Color doctrine_tint = doctrine_color(g_state->players[i].doctrine);
        RECT card = {44, 136 + i * 48, client.right - 52, 176 + i * 48};
        draw_panel(hdc, &card, mix_color(blastmonidz_style.panel, blastmonidz_style.background, 1, 2), blastmonidz_style.panel, doctrine_tint, 16);
        snprintf(line, sizeof(line), "%s | doctrine %s | wins %d | %s | gems %d | kills %d | feed %d/%d/%d/%d/%d | ai %s",
            g_state->players[i].name,
            blastmonidz_doctrine_name(g_state->players[i].doctrine),
            g_state->players[i].run_wins,
            blastmonidz_growth_title(g_state->players[i].mon.growth_stage),
            g_state->players[i].mon.gems_cleared,
            g_state->players[i].mon.round_kills,
            g_state->players[i].mon.self_feed.inner_signal,
            g_state->players[i].mon.self_feed.world_signal,
            g_state->players[i].mon.self_feed.rival_signal,
            g_state->players[i].mon.self_feed.ghost_signal,
            g_state->players[i].mon.self_feed.balance,
            g_state->players[i].ai_debug_line);
        draw_text_block(hdc, 56, 146 + i * 48, client.right - 116, 28, line, 18, FW_NORMAL, doctrine_tint);
    }
    draw_text_block(hdc, 54, client.bottom - 150, client.right - 108, 92,
        "This vertical-slice deliverable packages the simulation state, a seeded procedural archive renderer, the whole-self communication world feed, and saved run-profile output into a shippable Windows host bundle.\n"
        "Theme, bomb cadence, floor paint field, crate props, motion-frame families, world phase, and analysis-derived phenotype biases are recombined each run while the arena formulas stay unchanged.",
        17, FW_NORMAL, blastmonidz_style.text);
    {
        char visual_summary[224];
        snprintf(visual_summary, sizeof(visual_summary), "Visual profile: %s | %s | feed %d/%d/%d/%d/%d | elastic %.2f | env %.2f | seed %08X",
            blastmonidz_visual_theme_name(g_state),
            blastmonidz_world_phase_name(g_state),
            g_state->world_feed.inner_signal,
            g_state->world_feed.world_signal,
            g_state->world_feed.rival_signal,
            g_state->world_feed.ghost_signal,
            g_state->world_feed.balance,
            g_design_organism.animation_elasticity,
            g_design_organism.environmental_mutation_bias,
            g_state->visuals.run_seed);
        draw_text_block(hdc, 54, client.bottom - 52, client.right - 108, 26, visual_summary, 16, FW_SEMIBOLD, blastmonidz_style.accent);
    }
}

static void draw_scene(HDC hdc, RECT client) {
    fill_rect_color(hdc, &client, blastmonidz_style.background);
    switch (g_scene) {
        case WINDOW_SCENE_TITLE: draw_title_scene(hdc, client); break;
        case WINDOW_SCENE_LORE: draw_lore_scene(hdc, client); break;
        case WINDOW_SCENE_ARCHIVE: draw_archive_scene(hdc, client); break;
        case WINDOW_SCENE_STARTER: draw_starter_scene(hdc, client); break;
        case WINDOW_SCENE_ARENA: draw_arena_scene(hdc, client); break;
        case WINDOW_SCENE_SUMMARY: draw_summary_scene(hdc, client); break;
    }
}

static LRESULT CALLBACK blastmonidz_window_proc(HWND hwnd, UINT message, WPARAM w_param, LPARAM l_param) {
    switch (message) {
        case WM_CLOSE:
            stop_title_fanfare();
            g_close_requested = 1;
            DestroyWindow(hwnd);
            return 0;
        case WM_DESTROY:
            g_hwnd = NULL;
            return 0;
        case WM_KEYDOWN:
            switch ((int)w_param) {
                case VK_UP: queue_input('^'); return 0;
                case VK_DOWN: queue_input('v'); return 0;
                case VK_LEFT: queue_input('<'); return 0;
                case VK_RIGHT: queue_input('>'); return 0;
                case VK_RETURN: queue_input('!'); return 0;
                case VK_ESCAPE: queue_input('q'); return 0;
                case VK_SPACE: queue_input('b'); return 0;
                default: break;
            }
            break;
        case WM_CHAR: {
            int ch = (int)tolower((unsigned char)w_param);
            switch (ch) {
                case 'w': case 'a': case 's': case 'd':
                case 'b': case 'c': case 'r': case 't': case 'q':
                case '1': case '2': case '3': case '4': case '5':
                    queue_input(ch);
                    return 0;
                default:
                    break;
            }
            break;
        }
        case WM_ERASEBKGND:
            return 1;
        case WM_TIMER:
            poll_window_controller();
            InvalidateRect(hwnd, NULL, FALSE);
            return 0;
        case WM_PAINT: {
            PAINTSTRUCT paint;
            RECT client;
            RECT pixel_client;
            RECT viewport;
            HDC hdc = BeginPaint(hwnd, &paint);
            HDC buffer_dc;
            HBITMAP buffer_bitmap;
            HBITMAP old_bitmap;
            HDC pixel_dc;
            HBITMAP pixel_bitmap;
            HBITMAP old_pixel_bitmap;
            int width;
            int height;
            int pixel_width;
            int pixel_height;
            int scale_x;
            int scale_y;
            int scale;
            int viewport_width;
            int viewport_height;
            (void)w_param;
            (void)l_param;
            GetClientRect(hwnd, &client);
            width = client.right - client.left;
            height = client.bottom - client.top;
            pixel_width = BLASTMONIDZ_WINDOW_LOGICAL_WIDTH;
            pixel_height = BLASTMONIDZ_WINDOW_LOGICAL_HEIGHT;
            pixel_client.left = 0;
            pixel_client.top = 0;
            pixel_client.right = pixel_width;
            pixel_client.bottom = pixel_height;
            viewport.left = 0;
            viewport.top = 0;
            viewport.right = width;
            viewport.bottom = height;
            scale_x = width / pixel_width;
            scale_y = height / pixel_height;
            scale = scale_x < scale_y ? scale_x : scale_y;
            if (scale > 0) {
                viewport_width = pixel_width * scale;
                viewport_height = pixel_height * scale;
            } else {
                viewport_width = width;
                viewport_height = MulDiv(width, pixel_height, pixel_width);
                if (viewport_height > height) {
                    viewport_height = height;
                    viewport_width = MulDiv(height, pixel_width, pixel_height);
                }
            }
            viewport.left = (width - viewport_width) / 2;
            viewport.top = (height - viewport_height) / 2;
            viewport.right = viewport.left + viewport_width;
            viewport.bottom = viewport.top + viewport_height;
            buffer_dc = CreateCompatibleDC(hdc);
            buffer_bitmap = CreateCompatibleBitmap(hdc, width, height);
            pixel_dc = CreateCompatibleDC(hdc);
            pixel_bitmap = CreateCompatibleBitmap(hdc, pixel_width, pixel_height);
            if (buffer_dc && buffer_bitmap && pixel_dc && pixel_bitmap) {
                old_bitmap = (HBITMAP)SelectObject(buffer_dc, buffer_bitmap);
                old_pixel_bitmap = (HBITMAP)SelectObject(pixel_dc, pixel_bitmap);
                PatBlt(buffer_dc, 0, 0, width, height, BLACKNESS);
                draw_scene(pixel_dc, pixel_client);
                SetStretchBltMode(buffer_dc, COLORONCOLOR);
                StretchBlt(buffer_dc,
                    viewport.left,
                    viewport.top,
                    viewport.right - viewport.left,
                    viewport.bottom - viewport.top,
                    pixel_dc,
                    0,
                    0,
                    pixel_width,
                    pixel_height,
                    SRCCOPY);
                BitBlt(hdc, 0, 0, width, height, buffer_dc, 0, 0, SRCCOPY);
                SelectObject(pixel_dc, old_pixel_bitmap);
                SelectObject(buffer_dc, old_bitmap);
                DeleteObject(pixel_bitmap);
                DeleteDC(pixel_dc);
                DeleteObject(buffer_bitmap);
                DeleteDC(buffer_dc);
            } else {
                if (pixel_bitmap) {
                    DeleteObject(pixel_bitmap);
                }
                if (pixel_dc) {
                    DeleteDC(pixel_dc);
                }
                if (buffer_bitmap) {
                    DeleteObject(buffer_bitmap);
                }
                if (buffer_dc) {
                    DeleteDC(buffer_dc);
                }
                draw_scene(hdc, client);
            }
            EndPaint(hwnd, &paint);
            return 0;
        }
    }
    return DefWindowProc(hwnd, message, w_param, l_param);
}

int blastmonidz_window_init(void) {
    WNDCLASSA window_class;
    HINSTANCE instance;
    HRESULT hr;
    if (g_initialized) {
        return 1;
    }
    hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    if (hr == S_OK || hr == S_FALSE) {
        g_com_initialized = 1;
    }
    hr = CoCreateInstance(&CLSID_WICImagingFactory, NULL, CLSCTX_INPROC_SERVER,
        &IID_IWICImagingFactory, (LPVOID *)&g_wic_factory);
    if (FAILED(hr)) {
        g_wic_factory = NULL;
    }
    instance = GetModuleHandleA(NULL);
    ZeroMemory(&window_class, sizeof(window_class));
    window_class.lpfnWndProc = blastmonidz_window_proc;
    window_class.hInstance = instance;
    window_class.lpszClassName = kWindowClassName;
    window_class.hCursor = LoadCursor(NULL, IDC_ARROW);
    window_class.hbrBackground = NULL;
    RegisterClassA(&window_class);
        g_hwnd = CreateWindowExA(0, kWindowClassName, "Blastmonidz Visual Companion", WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 1120, 860, NULL, NULL, instance, NULL);
    if (!g_hwnd) {
        return 0;
    }
    blastmonidz_design_organism_reset(&g_design_organism);
    SetTimer(g_hwnd, kTitleTimerId, 120, NULL);
    ShowWindow(g_hwnd, SW_MAXIMIZE);
    SetFocus(g_hwnd);
    UpdateWindow(g_hwnd);
    load_title_archive_images();
    load_runtime_archive_images();
    write_design_profile_report();
    g_initialized = 1;
    return 1;
}

void blastmonidz_window_shutdown(void) {
    int family;
    int direction;
    int frame;
    int chemistry_index;
    reset_archive_bitmap(&g_title_backdrop);
    reset_archive_bitmap(&g_title_logo);
    reset_archive_bitmap(&g_floor_tile);
    reset_archive_bitmap(&g_bomb_pouch);
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_CRATE_VARIANTS; ++chemistry_index) {
        reset_archive_bitmap(&g_crate_variants[chemistry_index]);
    }
    for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
        reset_archive_bitmap(&g_bomb_frames[frame]);
        reset_archive_bitmap(&g_rival_back_sprites[frame]);
    }
    for (chemistry_index = 0; chemistry_index < BLASTMONIDZ_PAINT_VARIANTS; ++chemistry_index) {
        reset_archive_bitmap(&g_gem_paints[chemistry_index]);
    }
    for (family = 0; family < BLASTMONIDZ_HERO_FAMILIES; ++family) {
        for (direction = 0; direction < BLASTMONIDZ_PLAYER_DIRECTIONS; ++direction) {
            for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
                reset_archive_bitmap(&g_player_sprites[family][direction][frame]);
            }
        }
    }
    for (family = 0; family < BLASTMONIDZ_RIVAL_FAMILIES; ++family) {
        for (frame = 0; frame < BLASTMONIDZ_PLAYER_FRAMES; ++frame) {
            reset_archive_bitmap(&g_rival_side_sprites[family][frame]);
        }
    }
    if (g_wic_factory) {
        IWICImagingFactory_Release(g_wic_factory);
        g_wic_factory = NULL;
    }
    if (g_com_initialized) {
        CoUninitialize();
        g_com_initialized = 0;
    }
    if (g_hwnd) {
        KillTimer(g_hwnd, kTitleTimerId);
        DestroyWindow(g_hwnd);
        g_hwnd = NULL;
    }
    stop_title_fanfare();
    if (g_xinput_module) {
        FreeLibrary(g_xinput_module);
        g_xinput_module = NULL;
        g_xinput_get_state = NULL;
    }
    ZeroMemory(&g_prev_controller, sizeof(g_prev_controller));
    g_input_queue_head = 0;
    g_input_queue_tail = 0;
    blastmonidz_design_organism_reset(&g_design_organism);
    g_initialized = 0;
    g_state = NULL;
}

void blastmonidz_window_pump(void) {
    MSG message;
    blastmonidz_bridge_poll();
    poll_window_controller();
    while (PeekMessage(&message, NULL, 0, 0, PM_REMOVE)) {
        TranslateMessage(&message);
        DispatchMessage(&message);
    }
}

int blastmonidz_window_pop_input(void) {
    int ch;
    if (g_input_queue_head == g_input_queue_tail) {
        return 0;
    }
    ch = g_input_queue[g_input_queue_head];
    g_input_queue_head = (g_input_queue_head + 1) % (int)(sizeof(g_input_queue) / sizeof(g_input_queue[0]));
    return ch;
}

int blastmonidz_window_should_close(void) {
    return g_close_requested;
}

void blastmonidz_window_reset_close_request(void) {
    g_close_requested = 0;
}

static void present_scene(WindowScene scene, const GameState *state) {
    if (!g_initialized || !g_hwnd) {
        return;
    }
    if (!IsWindowVisible(g_hwnd)) {
        ShowWindow(g_hwnd, SW_SHOW);
    }
    if (scene == WINDOW_SCENE_TITLE) {
        start_title_fanfare();
    } else {
        stop_title_fanfare();
    }
    g_scene = scene;
    g_state = state;
    InvalidateRect(g_hwnd, NULL, FALSE);
    UpdateWindow(g_hwnd);
    blastmonidz_window_pump();
}

void blastmonidz_window_present_title(void) {
    present_scene(WINDOW_SCENE_TITLE, NULL);
}

void blastmonidz_window_present_lore(void) {
    present_scene(WINDOW_SCENE_LORE, NULL);
}

void blastmonidz_window_present_archive(void) {
    present_scene(WINDOW_SCENE_ARCHIVE, NULL);
}

void blastmonidz_window_present_starter_draw(const GameState *state) {
    present_scene(WINDOW_SCENE_STARTER, state);
}

void blastmonidz_window_present_arena(const GameState *state) {
    present_scene(WINDOW_SCENE_ARENA, state);
}

void blastmonidz_window_present_summary(const GameState *state) {
    present_scene(WINDOW_SCENE_SUMMARY, state);
}

#else

int blastmonidz_window_init(void) { return 1; }
void blastmonidz_window_shutdown(void) {}
void blastmonidz_window_pump(void) {}
int blastmonidz_window_pop_input(void) { return 0; }
int blastmonidz_window_should_close(void) { return 0; }
void blastmonidz_window_reset_close_request(void) {}
void blastmonidz_window_present_title(void) {}
void blastmonidz_window_present_lore(void) {}
void blastmonidz_window_present_archive(void) {}
void blastmonidz_window_present_starter_draw(const GameState *state) { (void)state; }
void blastmonidz_window_present_arena(const GameState *state) { (void)state; }
void blastmonidz_window_present_summary(const GameState *state) { (void)state; }

#endif
