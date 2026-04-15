#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmsystem.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SCREEN_W 320
#define SCREEN_H 192
#define TILE_SIZE 16
#define MAP_W 20
#define MAP_H 12
#define INITIAL_WINDOW_SCALE 3
#define MAX_SEEDS 16
#define MAX_ENEMIES 16
#define STAGE_COUNT 3

#define XINPUT_GAMEPAD_DPAD_UP        0x0001
#define XINPUT_GAMEPAD_DPAD_DOWN      0x0002
#define XINPUT_GAMEPAD_DPAD_LEFT      0x0004
#define XINPUT_GAMEPAD_DPAD_RIGHT     0x0008
#define XINPUT_GAMEPAD_START          0x0010
#define XINPUT_GAMEPAD_BACK           0x0020
#define XINPUT_GAMEPAD_A              0x1000
#define XINPUT_GAMEPAD_B              0x2000
#define XINPUT_GAMEPAD_X              0x4000
#define XINPUT_GAMEPAD_Y              0x8000

typedef struct XInputGamepad {
    WORD wButtons;
    BYTE bLeftTrigger;
    BYTE bRightTrigger;
    SHORT sThumbLX;
    SHORT sThumbLY;
    SHORT sThumbRX;
    SHORT sThumbRY;
} XInputGamepad;

typedef struct XInputState {
    DWORD dwPacketNumber;
    XInputGamepad Gamepad;
} XInputState;

typedef DWORD (WINAPI *XInputGetStateFn)(DWORD, XInputState *);

typedef enum GameMode {
    MODE_TITLE,
    MODE_OPTIONS,
    MODE_ASSET_PREVIEW,
    MODE_PLAYING,
    MODE_STAGE_CLEAR,
    MODE_GAME_OVER,
    MODE_WIN
} GameMode;

typedef enum EnemyType {
    ENEMY_BEETLE,
    ENEMY_WISP
} EnemyType;

typedef enum SoundEvent {
    SOUND_UI_MOVE,
    SOUND_UI_CONFIRM,
    SOUND_SEED_COLLECT,
    SOUND_GATE_OPEN,
    SOUND_PLAYER_HIT,
    SOUND_STAGE_CLEAR,
    SOUND_GAME_WIN
} SoundEvent;

typedef struct Sprite {
    HBITMAP bitmap;
    HDC dc;
    int width;
    int height;
    int loaded;
} Sprite;

typedef struct BackBuffer {
    HDC dc;
    HBITMAP bitmap;
    HBITMAP old_bitmap;
    uint32_t *pixels;
    int width;
    int height;
} BackBuffer;

typedef struct Seed {
    float x;
    float y;
    int active;
} Seed;

typedef struct Enemy {
    EnemyType type;
    float x;
    float y;
    float dir_x;
    float dir_y;
    float speed;
    float timer;
    int dir;
    int frame;
    int active;
} Enemy;

typedef struct Player {
    float x;
    float y;
    float spawn_x;
    float spawn_y;
    int dir;
    int frame;
    float anim_timer;
    int hearts;
    float invuln_timer;
} Player;

typedef struct Assets {
    Sprite tile_sheet;
    Sprite player;
    Sprite beetle;
    Sprite wisp;
    Sprite seed;
    Sprite hud;
    Sprite title;
    Sprite backdrop;
} Assets;

typedef struct ControllerState {
    int supported;
    int connected;
    WORD buttons;
    WORD pressed;
    float move_x;
    float move_y;
} ControllerState;

typedef struct StageDefinition {
    char name[64];
    char rows[MAP_H][MAP_W + 1];
} StageDefinition;

typedef struct AssetPreviewEntry {
    const char *label;
    const char *filename;
    int expected_w;
    int expected_h;
    const char *line_a;
    const char *line_b;
} AssetPreviewEntry;

typedef struct Game {
    HWND window;
    BackBuffer buffer;
    Assets assets;
    GameMode mode;
    GameMode return_mode;
    Player player;
    Seed seeds[MAX_SEEDS];
    Enemy enemies[MAX_ENEMIES];
    StageDefinition stages[STAGE_COUNT];
    char map[MAP_H][MAP_W + 1];
    char current_stage_name[64];
    int stage_index;
    int total_stages;
    int total_seeds;
    int collected_seeds;
    int gate_open;
    int gate_tile_x;
    int gate_tile_y;
    int keys[256];
    int score;
    int options_index;
    int preview_index;
    int window_scale;
    int sound_enabled;
    int controller_enabled;
    int show_input_hint;
    float stage_time;
    uint64_t last_tick;
    ControllerState controller;
    HMODULE xinput_module;
    XInputGetStateFn xinput_get_state;
} Game;

static Game g_game;

static const char *k_fallback_stage_names[STAGE_COUNT] = {
    "Lantern Verge",
    "Reed Crossing",
    "Hushwater Maze"
};

static const char *k_stage_maps[STAGE_COUNT][MAP_H] = {
    {
        "####################",
        "#S..*......B....*.G#",
        "#..####........##..#",
        "#..#..#..~~....#...#",
        "#..#..#......W.#...#",
        "#..#..#####.####...#",
        "#..*..............##",
        "#..####..####..#...#",
        "#......W....*..##..#",
        "#...######........##",
        "#....*.............#",
        "####################"
    },
    {
        "####################",
        "#S...B....#....*..G#",
        "#.####.##.#.####...#",
        "#...*..##....W.....#",
        "#.~~~~....####..##.#",
        "#....####....#..##.#",
        "#.B.....*....#.....#",
        "#.####..####.#.###.#",
        "#....W.....#.#...*.#",
        "#..######..#.#.##..#",
        "#...*......#....B..#",
        "####################"
    },
    {
        "####################",
        "#S..B...#..*.....WG#",
        "#.##.#..#.####.##..#",
        "#....#..#....#..*..#",
        "#.W..#..####.#.###.#",
        "#....#......#....*.#",
        "#.######.##.####...#",
        "#...*....##....#B..#",
        "#.##.##..##.##.#...#",
        "#....W...*..##.#...#",
        "#..########....#...#",
        "####################"
    }
};

static const AssetPreviewEntry k_preview_entries[] = {
    {"Tile Sheet", "assets\\tile_sheet.bmp", 64, 64, "4x4 tile sheet, 16x16 cells.", "Includes hedge, water, gate open and closed."},
    {"Courier Sheet", "assets\\player_courier.bmp", 72, 96, "3x4 frames, 24x24 each.", "Down/left/right/up rows; idle-walkA-walkB."},
    {"Briar Beetle", "assets\\enemy_beetle.bmp", 48, 96, "2x4 frames, 24x24 each.", "Dense silhouette with readable facing."},
    {"Spore Wisp", "assets\\enemy_wisp.bmp", 64, 16, "4x1 frames, 16x16 each.", "Glow pulse and directional stretch."},
    {"Pickup Seed", "assets\\pickup_seed.bmp", 64, 16, "4x1 frames, 16x16 each.", "Primary collectible should visibly glow."},
    {"HUD Icons", "assets\\hud_icons.bmp", 48, 16, "3x1 frames, 16x16 each.", "Heart, seed icon, stage icon."},
    {"Title Logo", "assets\\title_logo.bmp", 256, 64, "Single image title card.", "Centered banner with clean margins."},
    {"Backdrop", "assets\\backdrop_day.bmp", 320, 192, "Full-screen dusk marsh backdrop.", "Large shapes only so gameplay stays readable."}
};

static int preview_entry_count(void) {
    return (int)(sizeof(k_preview_entries) / sizeof(k_preview_entries[0]));
}

static void safe_copy_line(char *dst, const char *src, size_t size) {
    size_t len = 0;
    while (src[len] != '\0' && src[len] != '\r' && src[len] != '\n' && len + 1 < size) {
        dst[len] = src[len];
        len += 1;
    }
    dst[len] = '\0';
}

static void free_sprite(Sprite *sprite) {
    if (sprite->dc != NULL) {
        DeleteDC(sprite->dc);
        sprite->dc = NULL;
    }
    if (sprite->bitmap != NULL) {
        DeleteObject(sprite->bitmap);
        sprite->bitmap = NULL;
    }
    sprite->loaded = 0;
}

static void load_sprite(Sprite *sprite, const char *path) {
    BITMAP bmp;
    free_sprite(sprite);
    sprite->bitmap = (HBITMAP)LoadImageA(NULL, path, IMAGE_BITMAP, 0, 0, LR_LOADFROMFILE | LR_CREATEDIBSECTION);
    if (sprite->bitmap == NULL) {
        return;
    }
    sprite->dc = CreateCompatibleDC(NULL);
    SelectObject(sprite->dc, sprite->bitmap);
    GetObject(sprite->bitmap, sizeof(bmp), &bmp);
    sprite->width = bmp.bmWidth;
    sprite->height = bmp.bmHeight;
    sprite->loaded = 1;
}

static void load_assets(Assets *assets) {
    load_sprite(&assets->tile_sheet, "assets\\tile_sheet.bmp");
    load_sprite(&assets->player, "assets\\player_courier.bmp");
    load_sprite(&assets->beetle, "assets\\enemy_beetle.bmp");
    load_sprite(&assets->wisp, "assets\\enemy_wisp.bmp");
    load_sprite(&assets->seed, "assets\\pickup_seed.bmp");
    load_sprite(&assets->hud, "assets\\hud_icons.bmp");
    load_sprite(&assets->title, "assets\\title_logo.bmp");
    load_sprite(&assets->backdrop, "assets\\backdrop_day.bmp");
}

static void destroy_assets(Assets *assets) {
    free_sprite(&assets->tile_sheet);
    free_sprite(&assets->player);
    free_sprite(&assets->beetle);
    free_sprite(&assets->wisp);
    free_sprite(&assets->seed);
    free_sprite(&assets->hud);
    free_sprite(&assets->title);
    free_sprite(&assets->backdrop);
}

static void create_backbuffer(BackBuffer *buffer, HDC window_dc, int width, int height) {
    BITMAPINFO bmi;
    ZeroMemory(&bmi, sizeof(bmi));
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height;
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    buffer->dc = CreateCompatibleDC(window_dc);
    buffer->bitmap = CreateDIBSection(window_dc, &bmi, DIB_RGB_COLORS, (void **)&buffer->pixels, NULL, 0);
    buffer->old_bitmap = (HBITMAP)SelectObject(buffer->dc, buffer->bitmap);
    buffer->width = width;
    buffer->height = height;
}

static void destroy_backbuffer(BackBuffer *buffer) {
    if (buffer->dc != NULL) {
        SelectObject(buffer->dc, buffer->old_bitmap);
        DeleteObject(buffer->bitmap);
        DeleteDC(buffer->dc);
        buffer->dc = NULL;
        buffer->bitmap = NULL;
        buffer->old_bitmap = NULL;
    }
}

static void fill_rect_color(HDC dc, int x, int y, int w, int h, COLORREF color) {
    HBRUSH brush = CreateSolidBrush(color);
    RECT rect = {x, y, x + w, y + h};
    FillRect(dc, &rect, brush);
    DeleteObject(brush);
}

static void draw_text_line(HDC dc, int x, int y, COLORREF color, const char *text) {
    SetBkMode(dc, TRANSPARENT);
    SetTextColor(dc, color);
    TextOutA(dc, x, y, text, (int)strlen(text));
}

static void clear_screen(BackBuffer *buffer, COLORREF color) {
    fill_rect_color(buffer->dc, 0, 0, buffer->width, buffer->height, color);
}

static void apply_window_scale(Game *game) {
    RECT rect = {0, 0, SCREEN_W * game->window_scale, SCREEN_H * game->window_scale};
    AdjustWindowRect(&rect, WS_OVERLAPPEDWINDOW, FALSE);
    SetWindowPos(
        game->window,
        NULL,
        0,
        0,
        rect.right - rect.left,
        rect.bottom - rect.top,
        SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE
    );
}

static void play_sound_event(Game *game, SoundEvent event) {
    const char *alias = NULL;
    if (!game->sound_enabled) {
        return;
    }
    switch (event) {
        case SOUND_UI_MOVE: alias = "SystemAsterisk"; break;
        case SOUND_UI_CONFIRM: alias = "SystemQuestion"; break;
        case SOUND_SEED_COLLECT: alias = "SystemExclamation"; break;
        case SOUND_GATE_OPEN: alias = "SystemAsterisk"; break;
        case SOUND_PLAYER_HIT: alias = "SystemHand"; break;
        case SOUND_STAGE_CLEAR: alias = "SystemExit"; break;
        case SOUND_GAME_WIN: alias = "SystemStart"; break;
        default: break;
    }
    if (alias != NULL) {
        PlaySoundA(alias, NULL, SND_ALIAS | SND_ASYNC | SND_NODEFAULT);
    }
}

static void load_controller_backend(Game *game) {
    static const char *dll_names[] = {"xinput1_4.dll", "xinput9_1_0.dll", "xinput1_3.dll"};
    int i;
    FARPROC proc;
    game->xinput_get_state = NULL;
    game->xinput_module = NULL;
    for (i = 0; i < 3; ++i) {
        game->xinput_module = LoadLibraryA(dll_names[i]);
        if (game->xinput_module != NULL) {
            proc = GetProcAddress(game->xinput_module, "XInputGetState");
            if (proc != NULL) {
                memcpy(&game->xinput_get_state, &proc, sizeof(proc));
            }
            if (game->xinput_get_state != NULL) {
                game->controller.supported = 1;
                return;
            }
            FreeLibrary(game->xinput_module);
            game->xinput_module = NULL;
        }
    }
    game->controller.supported = 0;
}

static void unload_controller_backend(Game *game) {
    if (game->xinput_module != NULL) {
        FreeLibrary(game->xinput_module);
        game->xinput_module = NULL;
    }
    game->xinput_get_state = NULL;
    game->controller.supported = 0;
    game->controller.connected = 0;
}

static float normalize_axis(SHORT value) {
    const int deadzone = 9000;
    if (value > -deadzone && value < deadzone) {
        return 0.0f;
    }
    if (value >= 0) {
        return (float)(value - deadzone) / (32767.0f - deadzone);
    }
    return (float)(value + deadzone) / (32768.0f - deadzone);
}

static void poll_controller(Game *game) {
    XInputState state;
    WORD previous_buttons = game->controller.buttons;
    DWORD result;
    ZeroMemory(&state, sizeof(state));
    game->controller.pressed = 0;
    game->controller.move_x = 0.0f;
    game->controller.move_y = 0.0f;

    if (!game->controller_enabled || game->xinput_get_state == NULL) {
        game->controller.connected = 0;
        game->controller.buttons = 0;
        return;
    }

    result = game->xinput_get_state(0, &state);
    if (result != 0) {
        game->controller.connected = 0;
        game->controller.buttons = 0;
        return;
    }

    game->controller.connected = 1;
    game->controller.buttons = state.Gamepad.wButtons;
    game->controller.pressed = (WORD)(game->controller.buttons & ~previous_buttons);
    game->controller.move_x = normalize_axis(state.Gamepad.sThumbLX);
    game->controller.move_y = -normalize_axis(state.Gamepad.sThumbLY);
}

static void set_fallback_stage(StageDefinition *stage, int stage_index) {
    int row;
    safe_copy_line(stage->name, k_fallback_stage_names[stage_index], sizeof(stage->name));
    for (row = 0; row < MAP_H; ++row) {
        safe_copy_line(stage->rows[row], k_stage_maps[stage_index][row], sizeof(stage->rows[row]));
    }
}

static int load_stage_from_file(StageDefinition *stage, int stage_index) {
    char path[MAX_PATH];
    FILE *file;
    char line[256];
    int row = 0;

    snprintf(path, sizeof(path), "data\\stage_%02d.txt", stage_index + 1);
    file = fopen(path, "rb");
    if (file == NULL) {
        return 0;
    }

    if (fgets(line, sizeof(line), file) == NULL) {
        fclose(file);
        return 0;
    }

    if (strncmp(line, "name=", 5) == 0) {
        safe_copy_line(stage->name, line + 5, sizeof(stage->name));
    } else {
        safe_copy_line(stage->name, k_fallback_stage_names[stage_index], sizeof(stage->name));
        safe_copy_line(stage->rows[row], line, sizeof(stage->rows[row]));
        if ((int)strlen(stage->rows[row]) != MAP_W) {
            fclose(file);
            return 0;
        }
        row += 1;
    }

    while (row < MAP_H && fgets(line, sizeof(line), file) != NULL) {
        safe_copy_line(stage->rows[row], line, sizeof(stage->rows[row]));
        if ((int)strlen(stage->rows[row]) != MAP_W) {
            fclose(file);
            return 0;
        }
        row += 1;
    }
    fclose(file);
    return row == MAP_H;
}

static void load_stage_definitions(Game *game) {
    int index;
    for (index = 0; index < STAGE_COUNT; ++index) {
        if (!load_stage_from_file(&game->stages[index], index)) {
            set_fallback_stage(&game->stages[index], index);
        }
    }
}

static int tile_index_for_char(char c, int gate_open) {
    switch (c) {
        case '#': return 2;
        case '~': return 3;
        case 'G': return gate_open ? 7 : 6;
        default: return 0;
    }
}

static void draw_tile_placeholder(HDC dc, char tile, int x, int y, int gate_open) {
    COLORREF color = RGB(64, 110, 72);
    switch (tile) {
        case '#': color = RGB(34, 74, 44); break;
        case '~': color = RGB(30, 78, 118); break;
        case 'G': color = gate_open ? RGB(240, 214, 96) : RGB(120, 72, 48); break;
        default: color = RGB(78, 128, 86); break;
    }
    fill_rect_color(dc, x, y, TILE_SIZE, TILE_SIZE, color);
    if (tile == '#') {
        fill_rect_color(dc, x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4, RGB(48, 92, 56));
    }
}

static void draw_tile(Game *game, char tile, int x, int y) {
    int index = tile_index_for_char(tile, game->gate_open);
    Sprite *sheet = &game->assets.tile_sheet;
    if (sheet->loaded) {
        int src_x = (index % 4) * TILE_SIZE;
        int src_y = (index / 4) * TILE_SIZE;
        TransparentBlt(game->buffer.dc, x, y, TILE_SIZE, TILE_SIZE, sheet->dc, src_x, src_y, TILE_SIZE, TILE_SIZE, RGB(255, 0, 255));
        return;
    }
    draw_tile_placeholder(game->buffer.dc, tile, x, y, game->gate_open);
}

static void draw_backdrop(Game *game) {
    if (game->assets.backdrop.loaded) {
        StretchBlt(game->buffer.dc, 0, 0, SCREEN_W, SCREEN_H, game->assets.backdrop.dc, 0, 0, game->assets.backdrop.width, game->assets.backdrop.height, SRCCOPY);
        return;
    }
    clear_screen(&game->buffer, RGB(18, 44, 38));
    fill_rect_color(game->buffer.dc, 0, 120, SCREEN_W, 72, RGB(40, 88, 62));
    fill_rect_color(game->buffer.dc, 0, 144, SCREEN_W, 48, RGB(28, 62, 44));
}

static void draw_sprite_frame(HDC dc, Sprite *sprite, int x, int y, int w, int h, int src_x, int src_y, COLORREF fallback_color) {
    if (sprite->loaded) {
        TransparentBlt(dc, x, y, w, h, sprite->dc, src_x, src_y, w, h, RGB(255, 0, 255));
    } else {
        fill_rect_color(dc, x, y, w, h, fallback_color);
    }
}

static int is_blocking(Game *game, int tile_x, int tile_y) {
    char tile;
    if (tile_x < 0 || tile_y < 0 || tile_x >= MAP_W || tile_y >= MAP_H) {
        return 1;
    }
    tile = game->map[tile_y][tile_x];
    if (tile == '#') return 1;
    if (tile == '~') return 1;
    if (tile == 'G' && !game->gate_open) return 1;
    return 0;
}

static int collides_with_map(Game *game, float x, float y, float half) {
    int left = (int)((x - half) / TILE_SIZE);
    int right = (int)((x + half) / TILE_SIZE);
    int top = (int)((y - half) / TILE_SIZE);
    int bottom = (int)((y + half) / TILE_SIZE);
    return is_blocking(game, left, top) || is_blocking(game, right, top) || is_blocking(game, left, bottom) || is_blocking(game, right, bottom);
}

static void reset_player_to_spawn(Game *game) {
    game->player.x = game->player.spawn_x;
    game->player.y = game->player.spawn_y;
    game->player.invuln_timer = 1.25f;
}

static void begin_stage(Game *game, int stage_index) {
    int row;
    int col;
    int seed_count = 0;
    int enemy_count = 0;
    StageDefinition *stage = &game->stages[stage_index];

    game->stage_index = stage_index;
    game->collected_seeds = 0;
    game->total_seeds = 0;
    game->gate_open = 0;
    game->stage_time = 0.0f;
    safe_copy_line(game->current_stage_name, stage->name, sizeof(game->current_stage_name));

    for (row = 0; row < MAX_SEEDS; ++row) {
        game->seeds[row].active = 0;
    }
    for (row = 0; row < MAX_ENEMIES; ++row) {
        game->enemies[row].active = 0;
    }

    for (row = 0; row < MAP_H; ++row) {
        strcpy(game->map[row], stage->rows[row]);
        for (col = 0; col < MAP_W; ++col) {
            char c = game->map[row][col];
            float px = (float)(col * TILE_SIZE + TILE_SIZE / 2);
            float py = (float)(row * TILE_SIZE + TILE_SIZE / 2);
            if (c == 'S') {
                game->player.x = px;
                game->player.y = py;
                game->player.spawn_x = px;
                game->player.spawn_y = py;
                game->map[row][col] = '.';
            } else if (c == '*') {
                if (seed_count < MAX_SEEDS) {
                    game->seeds[seed_count].x = px;
                    game->seeds[seed_count].y = py;
                    game->seeds[seed_count].active = 1;
                    seed_count += 1;
                }
                game->map[row][col] = '.';
            } else if (c == 'B' || c == 'W') {
                if (enemy_count < MAX_ENEMIES) {
                    Enemy *enemy = &game->enemies[enemy_count];
                    enemy->active = 1;
                    enemy->x = px;
                    enemy->y = py;
                    enemy->timer = (float)(enemy_count * 0.35f);
                    enemy->frame = 0;
                    enemy->dir = 0;
                    if (c == 'B') {
                        enemy->type = ENEMY_BEETLE;
                        enemy->speed = 30.0f + (float)((stage_index + enemy_count) % 3) * 8.0f;
                        enemy->dir_x = (enemy_count % 2 == 0) ? 1.0f : 0.0f;
                        enemy->dir_y = (enemy_count % 2 == 0) ? 0.0f : 1.0f;
                    } else {
                        enemy->type = ENEMY_WISP;
                        enemy->speed = 24.0f + (float)((stage_index + enemy_count) % 2) * 6.0f;
                        enemy->dir_x = (enemy_count % 2 == 0) ? 1.0f : -1.0f;
                        enemy->dir_y = 0.0f;
                    }
                    enemy_count += 1;
                }
                game->map[row][col] = '.';
            } else if (c == 'G') {
                game->gate_tile_x = col;
                game->gate_tile_y = row;
            }
        }
    }
    game->total_seeds = seed_count;
    game->player.dir = 0;
    game->player.frame = 0;
    game->player.anim_timer = 0.0f;
    game->mode = MODE_PLAYING;
}

static void start_new_game(Game *game) {
    game->total_stages = STAGE_COUNT;
    game->score = 0;
    game->player.hearts = 3;
    game->player.invuln_timer = 0.0f;
    begin_stage(game, 0);
    play_sound_event(game, SOUND_UI_CONFIRM);
}

static void update_player(Game *game, float dt) {
    float move_x = 0.0f;
    float move_y = 0.0f;
    float speed = 70.0f;
    float next_x;
    float next_y;

    if (game->keys[VK_LEFT] || game->keys['A']) move_x -= 1.0f;
    if (game->keys[VK_RIGHT] || game->keys['D']) move_x += 1.0f;
    if (game->keys[VK_UP] || game->keys['W']) move_y -= 1.0f;
    if (game->keys[VK_DOWN] || game->keys['S']) move_y += 1.0f;

    move_x += game->controller.move_x;
    move_y += game->controller.move_y;
    if (move_x > 1.0f) move_x = 1.0f;
    if (move_x < -1.0f) move_x = -1.0f;
    if (move_y > 1.0f) move_y = 1.0f;
    if (move_y < -1.0f) move_y = -1.0f;

    if (move_x != 0.0f && move_y != 0.0f) {
        move_x *= 0.7071067f;
        move_y *= 0.7071067f;
    }

    next_x = game->player.x + move_x * speed * dt;
    next_y = game->player.y + move_y * speed * dt;

    if (!collides_with_map(game, next_x, game->player.y, 6.0f)) {
        game->player.x = next_x;
    }
    if (!collides_with_map(game, game->player.x, next_y, 6.0f)) {
        game->player.y = next_y;
    }

    if (move_x > 0.1f) game->player.dir = 2;
    else if (move_x < -0.1f) game->player.dir = 1;
    else if (move_y < -0.1f) game->player.dir = 3;
    else if (move_y > 0.1f) game->player.dir = 0;

    if (move_x != 0.0f || move_y != 0.0f) {
        game->player.anim_timer += dt;
        if (game->player.anim_timer >= 0.14f) {
            game->player.anim_timer = 0.0f;
            game->player.frame = (game->player.frame + 1) % 3;
        }
    } else {
        game->player.frame = 0;
        game->player.anim_timer = 0.0f;
    }

    if (game->player.invuln_timer > 0.0f) {
        game->player.invuln_timer -= dt;
        if (game->player.invuln_timer < 0.0f) {
            game->player.invuln_timer = 0.0f;
        }
    }
}

static void update_seeds(Game *game) {
    int i;
    for (i = 0; i < game->total_seeds; ++i) {
        Seed *seed = &game->seeds[i];
        float dx;
        float dy;
        if (!seed->active) continue;
        dx = game->player.x - seed->x;
        dy = game->player.y - seed->y;
        if ((dx * dx + dy * dy) <= 100.0f) {
            seed->active = 0;
            game->collected_seeds += 1;
            game->score += 100;
            play_sound_event(game, SOUND_SEED_COLLECT);
            if (game->collected_seeds >= game->total_seeds) {
                game->gate_open = 1;
                play_sound_event(game, SOUND_GATE_OPEN);
            }
        }
    }
}

static void hurt_player(Game *game) {
    if (game->player.invuln_timer > 0.0f) {
        return;
    }
    game->player.hearts -= 1;
    play_sound_event(game, SOUND_PLAYER_HIT);
    if (game->player.hearts <= 0) {
        game->mode = MODE_GAME_OVER;
        return;
    }
    reset_player_to_spawn(game);
}

static void update_enemies(Game *game, float dt) {
    int i;
    for (i = 0; i < MAX_ENEMIES; ++i) {
        Enemy *enemy = &game->enemies[i];
        float next_x;
        float next_y;
        float dx;
        float dy;
        if (!enemy->active) continue;

        enemy->timer += dt;
        enemy->frame = ((int)(enemy->timer * 6.0f)) % ((enemy->type == ENEMY_BEETLE) ? 2 : 4);

        if (enemy->type == ENEMY_BEETLE) {
            next_x = enemy->x + enemy->dir_x * enemy->speed * dt;
            next_y = enemy->y + enemy->dir_y * enemy->speed * dt;
            if (collides_with_map(game, next_x, next_y, 6.0f)) {
                enemy->dir_x = -enemy->dir_x;
                enemy->dir_y = -enemy->dir_y;
                next_x = enemy->x + enemy->dir_x * enemy->speed * dt;
                next_y = enemy->y + enemy->dir_y * enemy->speed * dt;
            }
            enemy->x = next_x;
            enemy->y = next_y;
            if (enemy->dir_x > 0.0f) enemy->dir = 2;
            else if (enemy->dir_x < 0.0f) enemy->dir = 1;
            else if (enemy->dir_y < 0.0f) enemy->dir = 3;
            else enemy->dir = 0;
        } else {
            dx = game->player.x - enemy->x;
            dy = game->player.y - enemy->y;
            if ((dx * dx + dy * dy) < 2304.0f) {
                enemy->dir_x = (dx > 1.0f) ? 1.0f : (dx < -1.0f ? -1.0f : 0.0f);
                enemy->dir_y = (dy > 1.0f) ? 1.0f : (dy < -1.0f ? -1.0f : 0.0f);
            } else if (enemy->timer > 1.2f) {
                enemy->timer = 0.0f;
                enemy->dir_x = -enemy->dir_x;
                enemy->dir_y = (enemy->dir_y == 0.0f) ? ((i % 2 == 0) ? 1.0f : -1.0f) : -enemy->dir_y;
            }
            next_x = enemy->x + enemy->dir_x * enemy->speed * dt;
            next_y = enemy->y + enemy->dir_y * enemy->speed * dt;
            if (collides_with_map(game, next_x, next_y, 4.0f)) {
                enemy->dir_x = -enemy->dir_x;
                enemy->dir_y = -enemy->dir_y;
            } else {
                enemy->x = next_x;
                enemy->y = next_y;
            }
        }

        dx = game->player.x - enemy->x;
        dy = game->player.y - enemy->y;
        if ((dx * dx + dy * dy) < 144.0f) {
            hurt_player(game);
        }
    }
}

static void check_gate(Game *game) {
    float gate_x = (float)(game->gate_tile_x * TILE_SIZE + TILE_SIZE / 2);
    float gate_y = (float)(game->gate_tile_y * TILE_SIZE + TILE_SIZE / 2);
    float dx = game->player.x - gate_x;
    float dy = game->player.y - gate_y;
    if (!game->gate_open) return;
    if ((dx * dx + dy * dy) <= 100.0f) {
        game->score += 250;
        if (game->stage_index + 1 >= game->total_stages) {
            game->mode = MODE_WIN;
            play_sound_event(game, SOUND_GAME_WIN);
        } else {
            game->mode = MODE_STAGE_CLEAR;
            play_sound_event(game, SOUND_STAGE_CLEAR);
        }
    }
}

static Sprite *preview_sprite_for_index(Game *game, int index) {
    switch (index) {
        case 0: return &game->assets.tile_sheet;
        case 1: return &game->assets.player;
        case 2: return &game->assets.beetle;
        case 3: return &game->assets.wisp;
        case 4: return &game->assets.seed;
        case 5: return &game->assets.hud;
        case 6: return &game->assets.title;
        case 7: return &game->assets.backdrop;
        default: return NULL;
    }
}

static void open_options(Game *game, GameMode return_mode) {
    game->return_mode = return_mode;
    game->mode = MODE_OPTIONS;
    game->options_index = 0;
    play_sound_event(game, SOUND_UI_MOVE);
}

static void open_asset_preview(Game *game, GameMode return_mode) {
    game->return_mode = return_mode;
    game->mode = MODE_ASSET_PREVIEW;
    play_sound_event(game, SOUND_UI_MOVE);
}

static void options_adjust(Game *game, int direction) {
    switch (game->options_index) {
        case 0:
            game->window_scale += direction;
            if (game->window_scale < 2) game->window_scale = 2;
            if (game->window_scale > 5) game->window_scale = 5;
            apply_window_scale(game);
            break;
        case 1:
            game->sound_enabled = !game->sound_enabled;
            break;
        case 2:
            game->controller_enabled = !game->controller_enabled;
            if (!game->controller_enabled) {
                game->controller.buttons = 0;
                game->controller.pressed = 0;
            }
            break;
        case 3:
            game->show_input_hint = !game->show_input_hint;
            break;
        default:
            break;
    }
    play_sound_event(game, SOUND_UI_MOVE);
}

static void handle_confirm(Game *game) {
    if (game->mode == MODE_TITLE) {
        start_new_game(game);
    } else if (game->mode == MODE_STAGE_CLEAR) {
        begin_stage(game, game->stage_index + 1);
        play_sound_event(game, SOUND_UI_CONFIRM);
    } else if (game->mode == MODE_GAME_OVER || game->mode == MODE_WIN) {
        game->mode = MODE_TITLE;
        play_sound_event(game, SOUND_UI_CONFIRM);
    } else if (game->mode == MODE_OPTIONS) {
        if (game->options_index == 4) {
            game->mode = game->return_mode;
        } else {
            options_adjust(game, 1);
        }
        play_sound_event(game, SOUND_UI_CONFIRM);
    } else if (game->mode == MODE_ASSET_PREVIEW) {
        game->mode = game->return_mode;
        play_sound_event(game, SOUND_UI_CONFIRM);
    }
}

static void handle_back(Game *game) {
    if (game->mode == MODE_OPTIONS || game->mode == MODE_ASSET_PREVIEW) {
        game->mode = game->return_mode;
        play_sound_event(game, SOUND_UI_CONFIRM);
    } else if (game->mode == MODE_PLAYING) {
        open_options(game, MODE_PLAYING);
    } else if (game->mode == MODE_TITLE) {
        PostQuitMessage(0);
    } else if (game->mode == MODE_STAGE_CLEAR || game->mode == MODE_GAME_OVER || game->mode == MODE_WIN) {
        game->mode = MODE_TITLE;
        play_sound_event(game, SOUND_UI_CONFIRM);
    }
}

static void handle_menu_vertical(Game *game, int delta) {
    if (game->mode == MODE_OPTIONS) {
        game->options_index += delta;
        if (game->options_index < 0) game->options_index = 4;
        if (game->options_index > 4) game->options_index = 0;
        play_sound_event(game, SOUND_UI_MOVE);
    }
}

static void handle_menu_horizontal(Game *game, int delta) {
    if (game->mode == MODE_OPTIONS) {
        options_adjust(game, delta);
    } else if (game->mode == MODE_ASSET_PREVIEW) {
        int total = preview_entry_count();
        game->preview_index += delta;
        if (game->preview_index < 0) game->preview_index = total - 1;
        if (game->preview_index >= total) game->preview_index = 0;
        play_sound_event(game, SOUND_UI_MOVE);
    }
}

static void handle_controller_actions(Game *game) {
    WORD pressed = game->controller.pressed;
    if (!game->controller.connected) {
        return;
    }
    if (pressed & XINPUT_GAMEPAD_A) handle_confirm(game);
    if (pressed & XINPUT_GAMEPAD_B) handle_back(game);
    if (pressed & XINPUT_GAMEPAD_Y) {
        if (game->mode == MODE_TITLE || game->mode == MODE_PLAYING) open_options(game, game->mode);
    }
    if (pressed & XINPUT_GAMEPAD_X) {
        if (game->mode == MODE_TITLE || game->mode == MODE_PLAYING) open_asset_preview(game, game->mode);
    }
    if (pressed & XINPUT_GAMEPAD_DPAD_UP) handle_menu_vertical(game, -1);
    if (pressed & XINPUT_GAMEPAD_DPAD_DOWN) handle_menu_vertical(game, 1);
    if (pressed & XINPUT_GAMEPAD_DPAD_LEFT) handle_menu_horizontal(game, -1);
    if (pressed & XINPUT_GAMEPAD_DPAD_RIGHT) handle_menu_horizontal(game, 1);
    if (pressed & XINPUT_GAMEPAD_START) {
        if (game->mode == MODE_PLAYING) open_options(game, MODE_PLAYING);
    }
}

static void update_game(Game *game, float dt) {
    poll_controller(game);
    handle_controller_actions(game);
    if (game->mode == MODE_PLAYING) {
        game->stage_time += dt;
        update_player(game, dt);
        update_seeds(game);
        update_enemies(game, dt);
        check_gate(game);
    }
}

static void draw_world(Game *game) {
    int row;
    int col;
    int i;
    draw_backdrop(game);
    for (row = 0; row < MAP_H; ++row) {
        for (col = 0; col < MAP_W; ++col) {
            draw_tile(game, game->map[row][col], col * TILE_SIZE, row * TILE_SIZE);
        }
    }
    for (i = 0; i < game->total_seeds; ++i) {
        int frame = ((int)(game->stage_time * 8.0f) + i) % 4;
        Seed *seed = &game->seeds[i];
        if (!seed->active) continue;
        if (game->assets.seed.loaded) {
            draw_sprite_frame(game->buffer.dc, &game->assets.seed, (int)seed->x - 8, (int)seed->y - 8, 16, 16, frame * 16, 0, RGB(250, 216, 76));
        } else {
            fill_rect_color(game->buffer.dc, (int)seed->x - 4, (int)seed->y - 4, 8, 8, RGB(250, 216, 76));
        }
    }
    for (i = 0; i < MAX_ENEMIES; ++i) {
        Enemy *enemy = &game->enemies[i];
        if (!enemy->active) continue;
        if (enemy->type == ENEMY_BEETLE) {
            int src_x = enemy->frame * 24;
            int src_y = enemy->dir * 24;
            draw_sprite_frame(game->buffer.dc, &game->assets.beetle, (int)enemy->x - 12, (int)enemy->y - 12, 24, 24, src_x, src_y, RGB(152, 64, 48));
        } else {
            int src_x = enemy->frame * 16;
            draw_sprite_frame(game->buffer.dc, &game->assets.wisp, (int)enemy->x - 8, (int)enemy->y - 8, 16, 16, src_x, 0, RGB(122, 224, 210));
        }
    }
    if (!(game->player.invuln_timer > 0.0f && ((int)(game->player.invuln_timer * 10.0f) % 2 == 0))) {
        int src_x = game->player.frame * 24;
        int src_y = game->player.dir * 24;
        draw_sprite_frame(game->buffer.dc, &game->assets.player, (int)game->player.x - 12, (int)game->player.y - 12, 24, 24, src_x, src_y, RGB(240, 192, 72));
    }
}

static void draw_hud(Game *game) {
    char line[160];
    int i;
    fill_rect_color(game->buffer.dc, 4, 4, 196, 24, RGB(12, 24, 22));
    for (i = 0; i < game->player.hearts; ++i) {
        if (game->assets.hud.loaded) {
            draw_sprite_frame(game->buffer.dc, &game->assets.hud, 8 + i * 14, 7, 16, 16, 0, 0, RGB(220, 88, 88));
        } else {
            fill_rect_color(game->buffer.dc, 8 + i * 14, 9, 10, 10, RGB(220, 88, 88));
        }
    }
    snprintf(line, sizeof(line), "%s  Seeds %d/%d  Stage %d", game->current_stage_name, game->collected_seeds, game->total_seeds, game->stage_index + 1);
    draw_text_line(game->buffer.dc, 56, 10, RGB(240, 244, 228), line);
}

static void draw_center_panel(Game *game, const char *title, const char *body, const char *footer) {
    int panel_w = 236;
    int panel_h = 90;
    int x = (SCREEN_W - panel_w) / 2;
    int y = (SCREEN_H - panel_h) / 2;
    fill_rect_color(game->buffer.dc, x, y, panel_w, panel_h, RGB(14, 28, 32));
    fill_rect_color(game->buffer.dc, x + 4, y + 4, panel_w - 8, panel_h - 8, RGB(28, 52, 60));
    draw_text_line(game->buffer.dc, x + 12, y + 12, RGB(255, 236, 160), title);
    draw_text_line(game->buffer.dc, x + 12, y + 34, RGB(236, 244, 240), body);
    draw_text_line(game->buffer.dc, x + 12, y + 60, RGB(180, 226, 196), footer);
}

static void render_title(Game *game) {
    draw_backdrop(game);
    if (game->assets.title.loaded) {
        draw_sprite_frame(game->buffer.dc, &game->assets.title, 32, 22, 256, 64, 0, 0, RGB(255, 210, 96));
    } else {
        draw_center_panel(game, "Mosslight Courier", "Collect every seed and reach the gate.", "Press Enter to begin.");
    }
    draw_text_line(game->buffer.dc, 24, 108, RGB(226, 242, 228), "Enter / A: Start   O or Y: Options   V or X: Asset Preview");
    draw_text_line(game->buffer.dc, 24, 124, RGB(226, 242, 228), "WASD or left stick to move. Beetles patrol; wisps drift and chase.");
    if (game->controller.supported) {
        draw_text_line(game->buffer.dc, 24, 140, game->controller.connected ? RGB(170, 240, 172) : RGB(226, 192, 120),
            game->controller.connected ? "Controller detected." : "Controller support available. Connect a pad to use it.");
    } else {
        draw_text_line(game->buffer.dc, 24, 140, RGB(226, 192, 120), "XInput backend not found; keyboard play remains available.");
    }
    draw_text_line(game->buffer.dc, 24, 156, RGB(255, 226, 142), "Esc quits. F1 opens options. F2 previews the current asset contract.");
}

static void render_options(Game *game) {
    char line[128];
    const char *labels[] = {"Window Scale", "Sound Hooks", "Controller Input", "Input Hint", "Back"};
    int index;
    int panel_x = 34;
    int panel_y = 24;
    draw_backdrop(game);
    fill_rect_color(game->buffer.dc, panel_x, panel_y, 252, 144, RGB(14, 28, 32));
    fill_rect_color(game->buffer.dc, panel_x + 4, panel_y + 4, 244, 136, RGB(24, 44, 52));
    draw_text_line(game->buffer.dc, panel_x + 12, panel_y + 10, RGB(255, 236, 160), "Options");
    for (index = 0; index < 5; ++index) {
        COLORREF color = (index == game->options_index) ? RGB(255, 226, 142) : RGB(228, 236, 232);
        int y = panel_y + 34 + index * 18;
        if (index == 0) snprintf(line, sizeof(line), "%s: %dx", labels[index], game->window_scale);
        else if (index == 1) snprintf(line, sizeof(line), "%s: %s", labels[index], game->sound_enabled ? "On" : "Off");
        else if (index == 2) snprintf(line, sizeof(line), "%s: %s", labels[index], game->controller_enabled ? "On" : "Off");
        else if (index == 3) snprintf(line, sizeof(line), "%s: %s", labels[index], game->show_input_hint ? "On" : "Off");
        else snprintf(line, sizeof(line), "%s", labels[index]);
        draw_text_line(game->buffer.dc, panel_x + 16, y, color, line);
    }
    draw_text_line(game->buffer.dc, panel_x + 12, panel_y + 122, RGB(180, 226, 196), "Up/Down select, Left/Right adjust, Enter/A accept, Esc/B back.");
}

static void render_asset_preview(Game *game) {
    AssetPreviewEntry entry = k_preview_entries[game->preview_index];
    Sprite *sprite = preview_sprite_for_index(game, game->preview_index);
    char line[128];
    int preview_x = 168;
    int preview_y = 30;
    int preview_w = 128;
    int preview_h = 104;

    draw_backdrop(game);
    fill_rect_color(game->buffer.dc, 8, 8, 304, 176, RGB(14, 28, 32));
    fill_rect_color(game->buffer.dc, 12, 12, 296, 168, RGB(24, 44, 52));
    draw_text_line(game->buffer.dc, 20, 18, RGB(255, 236, 160), "Asset Preview");
    snprintf(line, sizeof(line), "%d / %d", game->preview_index + 1, preview_entry_count());
    draw_text_line(game->buffer.dc, 258, 18, RGB(200, 228, 218), line);
    draw_text_line(game->buffer.dc, 20, 42, RGB(255, 226, 142), entry.label);
    draw_text_line(game->buffer.dc, 20, 58, RGB(220, 234, 228), entry.filename);
    snprintf(line, sizeof(line), "Expected size: %d x %d", entry.expected_w, entry.expected_h);
    draw_text_line(game->buffer.dc, 20, 74, RGB(220, 234, 228), line);
    draw_text_line(game->buffer.dc, 20, 96, RGB(186, 224, 196), entry.line_a);
    draw_text_line(game->buffer.dc, 20, 112, RGB(186, 224, 196), entry.line_b);
    fill_rect_color(game->buffer.dc, preview_x, preview_y, preview_w, preview_h, RGB(8, 18, 20));
    fill_rect_color(game->buffer.dc, preview_x + 2, preview_y + 2, preview_w - 4, preview_h - 4, RGB(18, 32, 36));

    if (sprite != NULL && sprite->loaded) {
        int draw_w = sprite->width;
        int draw_h = sprite->height;
        int scale = preview_w / draw_w;
        if (preview_h / draw_h < scale) scale = preview_h / draw_h;
        if (scale < 1) scale = 1;
        draw_w *= scale;
        draw_h *= scale;
        StretchBlt(game->buffer.dc, preview_x + (preview_w - draw_w) / 2, preview_y + (preview_h - draw_h) / 2, draw_w, draw_h, sprite->dc, 0, 0, sprite->width, sprite->height, SRCCOPY);
        snprintf(line, sizeof(line), "Loaded: %d x %d", sprite->width, sprite->height);
        draw_text_line(game->buffer.dc, 20, 138, RGB(170, 240, 172), line);
    } else {
        fill_rect_color(game->buffer.dc, preview_x + 20, preview_y + 20, preview_w - 40, preview_h - 40, RGB(255, 0, 255));
        draw_text_line(game->buffer.dc, preview_x + 24, preview_y + 44, RGB(255, 255, 255), "Missing BMP");
        draw_text_line(game->buffer.dc, 20, 138, RGB(255, 176, 144), "Current status: missing, fallback rendering is active.");
    }
    draw_text_line(game->buffer.dc, 20, 160, RGB(180, 226, 196), "Left/Right cycle assets. Enter/A or Esc/B returns.");
}

static void render_game(Game *game) {
    char subtitle[128];
    if (game->mode == MODE_TITLE) {
        render_title(game);
        return;
    }
    if (game->mode == MODE_OPTIONS) {
        render_options(game);
        return;
    }
    if (game->mode == MODE_ASSET_PREVIEW) {
        render_asset_preview(game);
        return;
    }

    draw_world(game);
    draw_hud(game);
    if (game->show_input_hint && game->mode == MODE_PLAYING) {
        draw_text_line(game->buffer.dc, 10, SCREEN_H - 14, RGB(230, 236, 212), "F1 options  F2 asset preview  Esc options");
    }

    if (game->mode == MODE_STAGE_CLEAR) {
        snprintf(subtitle, sizeof(subtitle), "%s cleared. Score %d.", game->current_stage_name, game->score);
        draw_center_panel(game, "District Cleared", subtitle, "Press Enter or A for the next district.");
    } else if (game->mode == MODE_GAME_OVER) {
        snprintf(subtitle, sizeof(subtitle), "Final score: %d", game->score);
        draw_center_panel(game, "Courier Lost", subtitle, "Press Enter or A to return to title.");
    } else if (game->mode == MODE_WIN) {
        snprintf(subtitle, sizeof(subtitle), "All three districts cleared. Score %d.", game->score);
        draw_center_panel(game, "Run Complete", subtitle, "Press Enter or A to return to title.");
    }
}

static void present_backbuffer(Game *game, HDC window_dc) {
    RECT client;
    int client_w;
    int client_h;
    int scale;
    int draw_w;
    int draw_h;
    int offset_x;
    int offset_y;

    GetClientRect(game->window, &client);
    client_w = client.right - client.left;
    client_h = client.bottom - client.top;
    scale = client_w / SCREEN_W;
    if (client_h / SCREEN_H < scale) scale = client_h / SCREEN_H;
    if (scale < 1) scale = 1;
    draw_w = SCREEN_W * scale;
    draw_h = SCREEN_H * scale;
    offset_x = (client_w - draw_w) / 2;
    offset_y = (client_h - draw_h) / 2;
    fill_rect_color(window_dc, 0, 0, client_w, client_h, RGB(0, 0, 0));
    StretchBlt(window_dc, offset_x, offset_y, draw_w, draw_h, game->buffer.dc, 0, 0, SCREEN_W, SCREEN_H, SRCCOPY);
}

static void handle_key_press(Game *game, WPARAM key) {
    if (key == VK_RETURN) {
        handle_confirm(game);
        return;
    }
    if (key == VK_ESCAPE) {
        handle_back(game);
        return;
    }
    if (key == 'O' || key == VK_F1) {
        if (game->mode == MODE_TITLE || game->mode == MODE_PLAYING) open_options(game, game->mode);
        return;
    }
    if (key == 'V' || key == VK_F2) {
        if (game->mode == MODE_TITLE || game->mode == MODE_PLAYING) open_asset_preview(game, game->mode);
        return;
    }
    if (key == VK_UP) {
        handle_menu_vertical(game, -1);
        return;
    }
    if (key == VK_DOWN) {
        handle_menu_vertical(game, 1);
        return;
    }
    if (key == VK_LEFT) {
        handle_menu_horizontal(game, -1);
        return;
    }
    if (key == VK_RIGHT) {
        handle_menu_horizontal(game, 1);
        return;
    }
}

static LRESULT CALLBACK window_proc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam) {
    switch (message) {
        case WM_CREATE: {
            HDC dc = GetDC(hwnd);
            g_game.window = hwnd;
            g_game.window_scale = INITIAL_WINDOW_SCALE;
            g_game.sound_enabled = 1;
            g_game.controller_enabled = 1;
            g_game.show_input_hint = 1;
            create_backbuffer(&g_game.buffer, dc, SCREEN_W, SCREEN_H);
            ReleaseDC(hwnd, dc);
            load_assets(&g_game.assets);
            load_stage_definitions(&g_game);
            load_controller_backend(&g_game);
            g_game.mode = MODE_TITLE;
            g_game.return_mode = MODE_TITLE;
            g_game.total_stages = STAGE_COUNT;
            g_game.last_tick = GetTickCount64();
            apply_window_scale(&g_game);
            SetTimer(hwnd, 1, 16, NULL);
            return 0;
        }
        case WM_TIMER: {
            uint64_t now = GetTickCount64();
            float dt = (float)(now - g_game.last_tick) / 1000.0f;
            if (dt > 0.05f) dt = 0.05f;
            g_game.last_tick = now;
            update_game(&g_game, dt);
            InvalidateRect(hwnd, NULL, FALSE);
            return 0;
        }
        case WM_KEYDOWN:
            if (wparam < 256) {
                int was_down = g_game.keys[wparam];
                g_game.keys[wparam] = 1;
                if (!was_down) {
                    handle_key_press(&g_game, wparam);
                }
            }
            return 0;
        case WM_KEYUP:
            if (wparam < 256) g_game.keys[wparam] = 0;
            return 0;
        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC dc = BeginPaint(hwnd, &ps);
            render_game(&g_game);
            present_backbuffer(&g_game, dc);
            EndPaint(hwnd, &ps);
            return 0;
        }
        case WM_DESTROY:
            KillTimer(hwnd, 1);
            unload_controller_backend(&g_game);
            destroy_assets(&g_game.assets);
            destroy_backbuffer(&g_game.buffer);
            PostQuitMessage(0);
            return 0;
        default:
            return DefWindowProc(hwnd, message, wparam, lparam);
    }
}

int WINAPI WinMain(HINSTANCE instance, HINSTANCE prev_instance, LPSTR cmd_line, int show_cmd) {
    WNDCLASSA wc;
    HWND window;
    MSG msg;
    (void)prev_instance;
    (void)cmd_line;

    ZeroMemory(&wc, sizeof(wc));
    wc.lpfnWndProc = window_proc;
    wc.hInstance = instance;
    wc.lpszClassName = "MosslightCourierWindowClass";
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);

    if (!RegisterClassA(&wc)) {
        return 1;
    }

    window = CreateWindowExA(
        0,
        wc.lpszClassName,
        "Mosslight Courier",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        SCREEN_W * INITIAL_WINDOW_SCALE + 32,
        SCREEN_H * INITIAL_WINDOW_SCALE + 48,
        NULL,
        NULL,
        instance,
        NULL
    );

    if (window == NULL) {
        return 1;
    }

    ShowWindow(window, show_cmd);
    UpdateWindow(window);

    while (GetMessage(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return (int)msg.wParam;
}