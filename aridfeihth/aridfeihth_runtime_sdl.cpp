#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#ifndef SDL_MAIN_HANDLED
#define SDL_MAIN_HANDLED
#endif

#include <windows.h>
#include <xinput.h>

#include <SDL.h>
#include <SDL_image.h>
#include <SDL_ttf.h>

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <string>
#include <vector>

extern "C" {
#include "aridfeihth_prototype_package.c"
}

static const char *kWindowTitle = "Aridfeihth Ash-Reliquary Demo (SDL)";
static const int kWindowWidth = 1280;
static const int kWindowHeight = 720;
static const float kGroundY = 560.0f;
static const float kPlayerScale = 2.0f;
static const int kAnimationStepMs = 70;

enum DemoScene {
    DEMO_SCENE_TITLE = 0,
    DEMO_SCENE_CONTROLS,
    DEMO_SCENE_SHIP_TEST,
    DEMO_SCENE_CAMPAIGN
};

enum TextAlign {
    TEXT_ALIGN_NEAR = 0,
    TEXT_ALIGN_CENTER,
    TEXT_ALIGN_FAR
};

struct AnimationFrame {
    int row;
    int col;
    int duration_ms;
};

struct AnimationClip {
    const char *name;
    const AnimationFrame *frames;
    size_t frame_count;
    bool loop;
};

struct TextureAsset {
    SDL_Texture *texture;
    int width;
    int height;
};

struct SpriteSheet {
    TextureAsset texture_asset;
    int frame_width;
    int frame_height;
    int columns;
    int rows;
};

struct Fonts {
    TTF_Font *title;
    TTF_Font *heading;
    TTF_Font *body;
    TTF_Font *small;
};

struct Particle {
    bool active;
    float x;
    float y;
    float vx;
    float vy;
    float size;
    float life_ms;
    float max_life_ms;
    float rotation_deg;
    float spin_deg;
    SDL_Color color;
};

struct EffectState {
    bool active;
    float elapsed_ms;
    float total_ms;
};

struct CampaignState {
    float player_x;
    float player_y;
    float velocity_y;
    int facing;
    bool airborne;
    bool mirror_newt;
    bool latch_spider;
    bool salt_ram;
    bool refraction_munki;
    bool room_cleared[64];
    int room_damage[64];
    float banner_ms;
    char banner[256];
    const AnimationClip *clip;
    const AnimationClip *override_clip;
    size_t frame_index;
    float frame_elapsed_ms;
    float override_remaining_ms;
    int next_combo;
    bool wind_kite;
    EffectState bond_weave;
};

struct ShipState {
    float x;
    float y;
    float heading_deg;
    float speed;
};

struct Assets {
    TextureAsset backdrop_refuge;
    TextureAsset backdrop_choir;
    TextureAsset backdrop_glasswind;
    TextureAsset backdrop_ember;
    TextureAsset hud_pack;
    SpriteSheet field_handler;
    SpriteSheet mirror_newt;
    SpriteSheet latch_spider;
    SpriteSheet salt_ram;
    SpriteSheet bond_weave;
    Fonts fonts;
};

struct XInputRuntime {
    HMODULE module;
    DWORD (WINAPI *get_state)(DWORD, XINPUT_STATE *);
};

struct InputFrame {
    bool menu_up_pressed;
    bool menu_down_pressed;
    bool confirm_pressed;
    bool back_pressed;
    bool left_held;
    bool right_held;
    bool up_held;
    bool down_held;
    bool run_held;
    bool attack_pressed;
    bool interact_pressed;
    bool jump_pressed;
    bool bond_pressed;
    bool wind_pressed;
    float horizontal_axis;
};

struct DemoState {
    SDL_Window *window;
    SDL_Renderer *renderer;
    bool running;
    bool smoke_mode;
    DemoScene scene;
    int title_index;
    Uint64 last_counter;
    Uint64 perf_frequency;
    Assets assets;
    XInputRuntime xinput;
    const AridfeihthPrototypePackage *package;
    AridfeihthRuntimeState runtime;
    CampaignState campaign;
    ShipState ship;
    Particle particles[256];
};

static DemoState g_demo = {};
static bool g_key_held[SDL_NUM_SCANCODES] = {};
static bool g_key_pressed[SDL_NUM_SCANCODES] = {};
static WORD g_previous_pad_buttons = 0;

static const AnimationFrame kIdleFrames[] = {
    {0, 0, kAnimationStepMs}, {0, 1, kAnimationStepMs}, {0, 2, kAnimationStepMs}, {0, 3, kAnimationStepMs}
};

static const AnimationFrame kWalkFrames[] = {
    {1, 0, kAnimationStepMs}, {1, 1, kAnimationStepMs}, {1, 2, kAnimationStepMs}, {1, 3, kAnimationStepMs}
};

static const AnimationFrame kRunFrames[] = {
    {2, 0, kAnimationStepMs}, {2, 1, kAnimationStepMs}, {2, 2, kAnimationStepMs}, {2, 3, kAnimationStepMs}
};

static const AnimationFrame kCombo1Frames[] = {
    {3, 0, kAnimationStepMs}, {3, 0, kAnimationStepMs}, {3, 1, kAnimationStepMs}, {3, 1, kAnimationStepMs},
    {3, 2, kAnimationStepMs}, {3, 3, kAnimationStepMs}, {4, 0, kAnimationStepMs}, {4, 0, kAnimationStepMs},
    {4, 1, kAnimationStepMs}, {4, 1, kAnimationStepMs}, {4, 2, kAnimationStepMs}, {4, 3, kAnimationStepMs}
};

static const AnimationFrame kCombo2Frames[] = {
    {5, 0, kAnimationStepMs}, {5, 0, kAnimationStepMs}, {5, 1, kAnimationStepMs},
    {5, 2, kAnimationStepMs}, {5, 2, kAnimationStepMs}, {5, 3, kAnimationStepMs}
};

static const AnimationFrame kCombo3Frames[] = {
    {6, 0, kAnimationStepMs}, {6, 0, kAnimationStepMs}, {6, 1, kAnimationStepMs},
    {6, 2, kAnimationStepMs}, {6, 2, kAnimationStepMs}, {6, 3, kAnimationStepMs}
};

static const AnimationFrame kJumpFrames[] = {
    {7, 0, kAnimationStepMs}, {7, 0, kAnimationStepMs}, {7, 1, kAnimationStepMs},
    {7, 2, kAnimationStepMs}, {7, 3, kAnimationStepMs}, {7, 3, kAnimationStepMs}
};

static const AnimationClip kIdleClip = {"idle", kIdleFrames, sizeof(kIdleFrames) / sizeof(kIdleFrames[0]), true};
static const AnimationClip kWalkClip = {"walk", kWalkFrames, sizeof(kWalkFrames) / sizeof(kWalkFrames[0]), true};
static const AnimationClip kRunClip = {"run", kRunFrames, sizeof(kRunFrames) / sizeof(kRunFrames[0]), true};
static const AnimationClip kCombo1Clip = {"combo_1", kCombo1Frames, sizeof(kCombo1Frames) / sizeof(kCombo1Frames[0]), false};
static const AnimationClip kCombo2Clip = {"combo_2", kCombo2Frames, sizeof(kCombo2Frames) / sizeof(kCombo2Frames[0]), false};
static const AnimationClip kCombo3Clip = {"combo_3", kCombo3Frames, sizeof(kCombo3Frames) / sizeof(kCombo3Frames[0]), false};
static const AnimationClip kJumpClip = {"jump", kJumpFrames, sizeof(kJumpFrames) / sizeof(kJumpFrames[0]), false};

static float clampf(float value, float min_value, float max_value)
{
    if (value < min_value) {
        return min_value;
    }
    if (value > max_value) {
        return max_value;
    }
    return value;
}

static float absf(float value)
{
    return value < 0.0f ? -value : value;
}

static Uint8 lerp_u8(Uint8 a, Uint8 b, float t)
{
    return (Uint8)(a + (float)(b - a) * t);
}

static std::string get_executable_directory(void)
{
    char buffer[MAX_PATH];
    DWORD length = GetModuleFileNameA(NULL, buffer, MAX_PATH);
    while (length > 0 && buffer[length - 1] != '\\' && buffer[length - 1] != '/') {
        --length;
    }
    buffer[length] = 0;
    return std::string(buffer);
}

static std::string get_current_directory_string(void)
{
    char buffer[MAX_PATH];
    DWORD length = GetCurrentDirectoryA(MAX_PATH, buffer);
    if (length == 0 || length >= MAX_PATH) {
        return std::string();
    }
    return std::string(buffer);
}

static std::string join_path(const std::string &base, const std::string &tail)
{
    if (base.empty()) {
        return tail;
    }
    if (base[base.size() - 1] == '\\' || base[base.size() - 1] == '/') {
        return base + tail;
    }
    return base + "\\" + tail;
}

static void release_texture(TextureAsset *asset)
{
    if (asset->texture != NULL) {
        SDL_DestroyTexture(asset->texture);
    }
    asset->texture = NULL;
    asset->width = 0;
    asset->height = 0;
}

static TextureAsset load_texture_relative(const char *relative_path)
{
    std::string exe_dir = get_executable_directory();
    std::string cwd = get_current_directory_string();
    std::string candidate_roots[4];
    TextureAsset asset = {};
    int index;

    candidate_roots[0] = join_path(join_path(exe_dir, ".."), "..");
    candidate_roots[1] = exe_dir;
    candidate_roots[2] = cwd;
    candidate_roots[3] = join_path(cwd, "build");

    for (index = 0; index < 4; ++index) {
        std::string candidate = join_path(candidate_roots[index], relative_path);
        asset.texture = IMG_LoadTexture(g_demo.renderer, candidate.c_str());
        if (asset.texture != NULL) {
            SDL_QueryTexture(asset.texture, NULL, NULL, &asset.width, &asset.height);
            SDL_SetTextureBlendMode(asset.texture, SDL_BLENDMODE_BLEND);
            return asset;
        }
    }

    asset.texture = NULL;
    return asset;
}

static void release_sheet(SpriteSheet *sheet)
{
    release_texture(&sheet->texture_asset);
    sheet->frame_width = 0;
    sheet->frame_height = 0;
    sheet->columns = 0;
    sheet->rows = 0;
}

static SpriteSheet load_sheet(const char *relative_path, int frame_width, int frame_height)
{
    SpriteSheet sheet = {};
    sheet.texture_asset = load_texture_relative(relative_path);
    if (sheet.texture_asset.texture != NULL && frame_width > 0 && frame_height > 0) {
        sheet.frame_width = frame_width;
        sheet.frame_height = frame_height;
        sheet.columns = sheet.texture_asset.width / frame_width;
        sheet.rows = sheet.texture_asset.height / frame_height;
    }
    return sheet;
}

static SpriteSheet load_quad_sheet(const char *relative_path)
{
    SpriteSheet sheet = {};
    sheet.texture_asset = load_texture_relative(relative_path);
    if (sheet.texture_asset.texture != NULL) {
        sheet.columns = 4;
        sheet.rows = 4;
        sheet.frame_width = sheet.texture_asset.width / 4;
        sheet.frame_height = sheet.texture_asset.height / 4;
    }
    return sheet;
}

static SpriteSheet load_strip_sheet(const char *relative_path, int columns)
{
    SpriteSheet sheet = {};
    sheet.texture_asset = load_texture_relative(relative_path);
    if (sheet.texture_asset.texture != NULL && columns > 0) {
        sheet.columns = columns;
        sheet.rows = 1;
        sheet.frame_width = sheet.texture_asset.width / columns;
        sheet.frame_height = sheet.texture_asset.height;
    }
    return sheet;
}

static TTF_Font *load_font_from_candidates(int size, bool bold)
{
    const char *regular_candidates[] = {
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf"
    };
    const char *bold_candidates[] = {
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\tahomabd.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf"
    };
    const char **candidates = bold ? bold_candidates : regular_candidates;
    size_t count = bold ? (sizeof(bold_candidates) / sizeof(bold_candidates[0])) : (sizeof(regular_candidates) / sizeof(regular_candidates[0]));
    size_t index;

    for (index = 0; index < count; ++index) {
        TTF_Font *font = TTF_OpenFont(candidates[index], size);
        if (font != NULL) {
            return font;
        }
    }
    return NULL;
}

static bool load_assets(Assets *assets)
{
    ZeroMemory(assets, sizeof(*assets));

    assets->backdrop_refuge = load_texture_relative("aridfeihth\\production_raw\\spaces\\latchspire_refuge_backdrop.png");
    assets->backdrop_choir = load_texture_relative("aridfeihth\\production_raw\\spaces\\choir_stair_backdrop.png");
    assets->backdrop_glasswind = load_texture_relative("aridfeihth\\production_raw\\spaces\\glasswind_causeway_backdrop.png");
    assets->backdrop_ember = load_texture_relative("aridfeihth\\production_raw\\spaces\\ember_nave_backdrop.png");
    assets->hud_pack = load_texture_relative("aridfeihth\\production_raw\\interface\\aridfeihth_hud_pack.png");
    assets->field_handler = load_sheet("aridfeihth\\production_raw\\actors\\field_handler_sheet.png", 64, 64);
    assets->mirror_newt = load_quad_sheet("aridfeihth\\production_raw\\actors\\mirror_newt_sheet.png");
    assets->latch_spider = load_quad_sheet("aridfeihth\\production_raw\\actors\\latch_spider_sheet.png");
    assets->salt_ram = load_quad_sheet("aridfeihth\\production_raw\\actors\\salt_ram_sheet.png");
    assets->bond_weave = load_strip_sheet("aridfeihth\\production_raw\\effects\\bond_weave_fx.png", 8);
    assets->fonts.title = load_font_from_candidates(42, true);
    assets->fonts.heading = load_font_from_candidates(28, true);
    assets->fonts.body = load_font_from_candidates(20, false);
    assets->fonts.small = load_font_from_candidates(16, false);

    return assets->backdrop_refuge.texture != NULL
        && assets->backdrop_choir.texture != NULL
        && assets->backdrop_glasswind.texture != NULL
        && assets->backdrop_ember.texture != NULL
        && assets->hud_pack.texture != NULL
        && assets->field_handler.texture_asset.texture != NULL
        && assets->mirror_newt.texture_asset.texture != NULL
        && assets->latch_spider.texture_asset.texture != NULL
        && assets->salt_ram.texture_asset.texture != NULL
        && assets->bond_weave.texture_asset.texture != NULL
        && assets->fonts.title != NULL
        && assets->fonts.heading != NULL
        && assets->fonts.body != NULL
        && assets->fonts.small != NULL;
}

static void unload_assets(Assets *assets)
{
    release_texture(&assets->backdrop_refuge);
    release_texture(&assets->backdrop_choir);
    release_texture(&assets->backdrop_glasswind);
    release_texture(&assets->backdrop_ember);
    release_texture(&assets->hud_pack);
    release_sheet(&assets->field_handler);
    release_sheet(&assets->mirror_newt);
    release_sheet(&assets->latch_spider);
    release_sheet(&assets->salt_ram);
    release_sheet(&assets->bond_weave);
    if (assets->fonts.title != NULL) {
        TTF_CloseFont(assets->fonts.title);
    }
    if (assets->fonts.heading != NULL) {
        TTF_CloseFont(assets->fonts.heading);
    }
    if (assets->fonts.body != NULL) {
        TTF_CloseFont(assets->fonts.body);
    }
    if (assets->fonts.small != NULL) {
        TTF_CloseFont(assets->fonts.small);
    }
    ZeroMemory(&assets->fonts, sizeof(assets->fonts));
}

static void load_xinput_runtime(XInputRuntime *runtime)
{
    const char *dlls[] = {"xinput1_4.dll", "xinput9_1_0.dll", "xinput1_3.dll"};
    size_t index;

    ZeroMemory(runtime, sizeof(*runtime));

    for (index = 0; index < sizeof(dlls) / sizeof(dlls[0]); ++index) {
        runtime->module = LoadLibraryA(dlls[index]);
        if (runtime->module != NULL) {
            runtime->get_state = (DWORD (WINAPI *)(DWORD, XINPUT_STATE *))GetProcAddress(runtime->module, "XInputGetState");
            if (runtime->get_state != NULL) {
                return;
            }
            FreeLibrary(runtime->module);
            runtime->module = NULL;
        }
    }
}

static void unload_xinput_runtime(XInputRuntime *runtime)
{
    if (runtime->module != NULL) {
        FreeLibrary(runtime->module);
        runtime->module = NULL;
    }
    runtime->get_state = NULL;
}

static void set_banner(const char *text)
{
    strncpy_s(g_demo.campaign.banner, sizeof(g_demo.campaign.banner), text != NULL ? text : "", _TRUNCATE);
    g_demo.campaign.banner_ms = 2400.0f;
}

static int room_index_from_id(const char *room_id)
{
    size_t index;

    if (room_id == NULL) {
        return -1;
    }

    for (index = 0; index < g_demo.package->room_count; ++index) {
        if (strcmp(g_demo.package->rooms[index].id, room_id) == 0) {
            return (int)index;
        }
    }
    return -1;
}

static const AridfeihthRoom *find_room(const char *room_id)
{
    int index = room_index_from_id(room_id);
    if (index < 0) {
        return NULL;
    }
    return &g_demo.package->rooms[index];
}

static void add_inventory_item(const char *item_id)
{
    size_t index;

    if (item_id == NULL) {
        return;
    }

    for (index = 0; index < g_demo.runtime.inventory_count; ++index) {
        if (g_demo.runtime.inventory[index] != NULL && strcmp(g_demo.runtime.inventory[index], item_id) == 0) {
            return;
        }
    }

    if (g_demo.runtime.inventory_count < sizeof(g_demo.runtime.inventory) / sizeof(g_demo.runtime.inventory[0])) {
        g_demo.runtime.inventory[g_demo.runtime.inventory_count++] = item_id;
    }
}

static bool has_requirement(const char *requirement)
{
    if (requirement == NULL) {
        return true;
    }
    if (strcmp(requirement, "mirror_newt") == 0) {
        return g_demo.campaign.mirror_newt;
    }
    if (strcmp(requirement, "latch_spider") == 0) {
        return g_demo.campaign.latch_spider;
    }
    if (strcmp(requirement, "salt_ram") == 0) {
        return g_demo.campaign.salt_ram;
    }
    if (strcmp(requirement, "refraction_munki") == 0) {
        return g_demo.campaign.refraction_munki;
    }
    return false;
}

static bool can_use_exit(const AridfeihthRoomExit *exit_spec)
{
    int room_index;

    if (exit_spec == NULL || exit_spec->room_id == NULL || g_demo.runtime.current_room == NULL) {
        return false;
    }
    if (!has_requirement(exit_spec->requires)) {
        return false;
    }

    room_index = room_index_from_id(g_demo.runtime.current_room->id);
    if (room_index >= 0 && exit_spec->requires_room_clear && !g_demo.campaign.room_cleared[room_index]) {
        return false;
    }
    return true;
}

static void start_clip(const AnimationClip *clip)
{
    if (clip == NULL) {
        return;
    }
    if (g_demo.campaign.clip != clip) {
        g_demo.campaign.clip = clip;
        g_demo.campaign.frame_index = 0;
        g_demo.campaign.frame_elapsed_ms = 0.0f;
    }
}

static void set_override_clip(const AnimationClip *clip)
{
    size_t index;
    int total_ms = 0;

    if (clip == NULL) {
        return;
    }

    g_demo.campaign.override_clip = clip;
    g_demo.campaign.clip = clip;
    g_demo.campaign.frame_index = 0;
    g_demo.campaign.frame_elapsed_ms = 0.0f;

    for (index = 0; index < clip->frame_count; ++index) {
        total_ms += clip->frames[index].duration_ms;
    }
    g_demo.campaign.override_remaining_ms = (float)total_ms;
}

static void move_to_room(const char *room_id, bool from_right)
{
    const AridfeihthRoom *room = find_room(room_id);

    if (room == NULL) {
        return;
    }

    g_demo.runtime.current_room = room;
    g_demo.campaign.player_x = from_right ? 1080.0f : 180.0f;
    g_demo.campaign.player_y = 0.0f;
    g_demo.campaign.velocity_y = 0.0f;
    g_demo.campaign.airborne = false;
    set_banner(room->name);
}

static int clear_threshold_for_room(const AridfeihthRoom *room)
{
    if (room == NULL) {
        return 0;
    }
    if ((room->flags & ARIDFEIHTH_ROOM_FLAG_SAFE) != 0u) {
        return 0;
    }
    return 2 + (int)(room->danger / 2u);
}

static void mark_room_cleared(const AridfeihthRoom *room)
{
    int index;

    if (room == NULL) {
        return;
    }

    index = room_index_from_id(room->id);
    if (index < 0 || g_demo.campaign.room_cleared[index]) {
        return;
    }

    g_demo.campaign.room_cleared[index] = true;
    if (strcmp(room->id, "ember_nave") == 0) {
        g_demo.campaign.salt_ram = true;
        add_inventory_item("salt_ram");
        set_banner("Ember Nave cleared. Salt Ram secured.");
    } else if (strcmp(room->id, "ashfall_dais") == 0) {
        set_banner("Ashfall Dais cleared. Prototype boss defeated.");
    } else {
        set_banner("Room pressure broken.");
    }
}

static const TextureAsset *pick_room_backdrop(const AridfeihthRoom *room)
{
    if (room == NULL) {
        return &g_demo.assets.backdrop_refuge;
    }
    if (strcmp(room->id, "latchspire_refuge") == 0 || strcmp(room->id, "ropewalk_harbor") == 0 || strcmp(room->id, "skiff_berth") == 0) {
        return &g_demo.assets.backdrop_refuge;
    }
    if (strcmp(room->scene_family, "choir") == 0) {
        return &g_demo.assets.backdrop_choir;
    }
    if (strcmp(room->scene_family, "glasswind") == 0) {
        return &g_demo.assets.backdrop_glasswind;
    }
    if (strcmp(room->scene_family, "ember") == 0) {
        return &g_demo.assets.backdrop_ember;
    }
    if (strstr(room->id, "ashfall") != NULL || strstr(room->id, "gatehouse") != NULL || strstr(room->id, "drydock") != NULL) {
        return &g_demo.assets.backdrop_ember;
    }
    return &g_demo.assets.backdrop_refuge;
}

static void reset_campaign_state(void)
{
    ZeroMemory(&g_demo.campaign, sizeof(g_demo.campaign));
    g_demo.campaign.player_x = 220.0f;
    g_demo.campaign.facing = 1;
    g_demo.campaign.clip = &kIdleClip;
    g_demo.campaign.next_combo = 0;
}

static void boot_runtime(void)
{
    g_demo.package = aridfeihth_get_prototype_package();
    aridfeihth_bootstrap_demo(&g_demo.runtime);
    reset_campaign_state();
}

static void start_campaign(void)
{
    aridfeihth_start_prototype(&g_demo.runtime);
    reset_campaign_state();
    set_banner("Prototype pilgrimage underway.");
}

static void begin_ship_test(void)
{
    g_demo.ship.x = 640.0f;
    g_demo.ship.y = 360.0f;
    g_demo.ship.heading_deg = -90.0f;
    g_demo.ship.speed = 0.0f;
}

static void spawn_particle(float x, float y, float vx, float vy, float size, float life_ms, SDL_Color color, float rotation_deg, float spin_deg)
{
    size_t index;

    for (index = 0; index < sizeof(g_demo.particles) / sizeof(g_demo.particles[0]); ++index) {
        if (!g_demo.particles[index].active) {
            g_demo.particles[index].active = true;
            g_demo.particles[index].x = x;
            g_demo.particles[index].y = y;
            g_demo.particles[index].vx = vx;
            g_demo.particles[index].vy = vy;
            g_demo.particles[index].size = size;
            g_demo.particles[index].life_ms = life_ms;
            g_demo.particles[index].max_life_ms = life_ms;
            g_demo.particles[index].color = color;
            g_demo.particles[index].rotation_deg = rotation_deg;
            g_demo.particles[index].spin_deg = spin_deg;
            return;
        }
    }
}

static void update_particles(float dt_ms)
{
    size_t index;

    for (index = 0; index < sizeof(g_demo.particles) / sizeof(g_demo.particles[0]); ++index) {
        if (!g_demo.particles[index].active) {
            continue;
        }

        g_demo.particles[index].life_ms -= dt_ms;
        if (g_demo.particles[index].life_ms <= 0.0f) {
            g_demo.particles[index].active = false;
            continue;
        }

        g_demo.particles[index].x += g_demo.particles[index].vx * (dt_ms / 1000.0f);
        g_demo.particles[index].y += g_demo.particles[index].vy * (dt_ms / 1000.0f);
        g_demo.particles[index].rotation_deg += g_demo.particles[index].spin_deg * (dt_ms / 1000.0f);
        g_demo.particles[index].vy += 22.0f * (dt_ms / 1000.0f);
    }
}

static InputFrame sample_input(void)
{
    InputFrame input = {};
    XINPUT_STATE pad_state = {};
    bool controller_ok = false;
    WORD pressed_buttons = 0;
    SHORT lx = 0;
    float axis = 0.0f;

    input.menu_up_pressed = g_key_pressed[SDL_SCANCODE_UP] || g_key_pressed[SDL_SCANCODE_W];
    input.menu_down_pressed = g_key_pressed[SDL_SCANCODE_DOWN] || g_key_pressed[SDL_SCANCODE_S];
    input.confirm_pressed = g_key_pressed[SDL_SCANCODE_RETURN] || g_key_pressed[SDL_SCANCODE_J];
    input.back_pressed = g_key_pressed[SDL_SCANCODE_ESCAPE] || g_key_pressed[SDL_SCANCODE_BACKSPACE];
    input.left_held = g_key_held[SDL_SCANCODE_LEFT] || g_key_held[SDL_SCANCODE_A];
    input.right_held = g_key_held[SDL_SCANCODE_RIGHT] || g_key_held[SDL_SCANCODE_D];
    input.up_held = g_key_held[SDL_SCANCODE_UP] || g_key_held[SDL_SCANCODE_W];
    input.down_held = g_key_held[SDL_SCANCODE_DOWN] || g_key_held[SDL_SCANCODE_S];
    input.run_held = g_key_held[SDL_SCANCODE_LSHIFT] || g_key_held[SDL_SCANCODE_RSHIFT] || g_key_held[SDL_SCANCODE_K];
    input.attack_pressed = g_key_pressed[SDL_SCANCODE_Z] || g_key_pressed[SDL_SCANCODE_X];
    input.interact_pressed = g_key_pressed[SDL_SCANCODE_E];
    input.jump_pressed = g_key_pressed[SDL_SCANCODE_SPACE];
    input.bond_pressed = g_key_pressed[SDL_SCANCODE_V];
    input.wind_pressed = g_key_pressed[SDL_SCANCODE_C];
    input.horizontal_axis = (input.left_held ? -1.0f : 0.0f) + (input.right_held ? 1.0f : 0.0f);

    if (g_demo.xinput.get_state != NULL && g_demo.xinput.get_state(0, &pad_state) == ERROR_SUCCESS) {
        controller_ok = true;
        pressed_buttons = (WORD)(pad_state.Gamepad.wButtons & (WORD)~g_previous_pad_buttons);
        lx = pad_state.Gamepad.sThumbLX;
        if (lx > XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE || lx < -XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE) {
            axis = (float)lx / 32767.0f;
        }

        input.menu_up_pressed = input.menu_up_pressed || (pressed_buttons & XINPUT_GAMEPAD_DPAD_UP) != 0;
        input.menu_down_pressed = input.menu_down_pressed || (pressed_buttons & XINPUT_GAMEPAD_DPAD_DOWN) != 0;
        input.confirm_pressed = input.confirm_pressed || (pressed_buttons & XINPUT_GAMEPAD_START) != 0 || (pressed_buttons & XINPUT_GAMEPAD_A) != 0;
        input.back_pressed = input.back_pressed || (pressed_buttons & XINPUT_GAMEPAD_BACK) != 0 || (pressed_buttons & XINPUT_GAMEPAD_B) != 0;
        input.left_held = input.left_held || axis < -0.25f || (pad_state.Gamepad.wButtons & XINPUT_GAMEPAD_DPAD_LEFT) != 0;
        input.right_held = input.right_held || axis > 0.25f || (pad_state.Gamepad.wButtons & XINPUT_GAMEPAD_DPAD_RIGHT) != 0;
        input.up_held = input.up_held || (pad_state.Gamepad.wButtons & XINPUT_GAMEPAD_DPAD_UP) != 0;
        input.down_held = input.down_held || (pad_state.Gamepad.wButtons & XINPUT_GAMEPAD_DPAD_DOWN) != 0;
        input.run_held = input.run_held || pad_state.Gamepad.bLeftTrigger > 48;
        input.attack_pressed = input.attack_pressed || (pressed_buttons & XINPUT_GAMEPAD_X) != 0;
        input.interact_pressed = input.interact_pressed || (pressed_buttons & XINPUT_GAMEPAD_Y) != 0;
        input.jump_pressed = input.jump_pressed || (pressed_buttons & XINPUT_GAMEPAD_A) != 0;
        input.bond_pressed = input.bond_pressed || (pressed_buttons & XINPUT_GAMEPAD_RIGHT_SHOULDER) != 0;
        input.wind_pressed = input.wind_pressed || (pressed_buttons & XINPUT_GAMEPAD_LEFT_SHOULDER) != 0;
        if (absf(axis) > absf(input.horizontal_axis)) {
            input.horizontal_axis = axis;
        }
        g_previous_pad_buttons = pad_state.Gamepad.wButtons;
    }

    if (!controller_ok) {
        g_previous_pad_buttons = 0;
    }

    ZeroMemory(g_key_pressed, sizeof(g_key_pressed));
    return input;
}

static void advance_animation(float dt_ms)
{
    const AnimationClip *clip = g_demo.campaign.clip;

    if (clip == NULL || clip->frame_count == 0) {
        return;
    }

    g_demo.campaign.frame_elapsed_ms += dt_ms;
    while (g_demo.campaign.frame_elapsed_ms >= (float)clip->frames[g_demo.campaign.frame_index].duration_ms) {
        g_demo.campaign.frame_elapsed_ms -= (float)clip->frames[g_demo.campaign.frame_index].duration_ms;
        if (g_demo.campaign.frame_index + 1 < clip->frame_count) {
            g_demo.campaign.frame_index += 1;
        } else if (clip->loop) {
            g_demo.campaign.frame_index = 0;
        }
    }
}

static void trigger_bond_weave(void)
{
    size_t index;

    g_demo.campaign.bond_weave.active = true;
    g_demo.campaign.bond_weave.elapsed_ms = 0.0f;
    g_demo.campaign.bond_weave.total_ms = 900.0f;

    for (index = 0; index < 18; ++index) {
        float angle = (float)index * 20.0f;
        float radians = angle * 3.14159265f / 180.0f;
        SDL_Color color = {210, 176, 106, 220};
        spawn_particle(
            g_demo.campaign.player_x,
            kGroundY - 70.0f + g_demo.campaign.player_y,
            cosf(radians) * 120.0f,
            sinf(radians) * 120.0f - 30.0f,
            6.0f + (float)(index % 3),
            600.0f + (float)(index % 5) * 35.0f,
            color,
            angle,
            90.0f - (float)(index % 7) * 20.0f);
    }
}

static void update_title(const InputFrame *input)
{
    if (input->menu_up_pressed) {
        g_demo.title_index -= 1;
        if (g_demo.title_index < 0) {
            g_demo.title_index = (int)g_demo.package->title_option_count - 1;
        }
    }
    if (input->menu_down_pressed) {
        g_demo.title_index += 1;
        if (g_demo.title_index >= (int)g_demo.package->title_option_count) {
            g_demo.title_index = 0;
        }
    }
    if (!input->confirm_pressed) {
        return;
    }

    switch (g_demo.title_index) {
    case 0:
        start_campaign();
        g_demo.scene = DEMO_SCENE_CAMPAIGN;
        break;
    case 1:
        begin_ship_test();
        g_demo.scene = DEMO_SCENE_SHIP_TEST;
        break;
    case 2:
        g_demo.scene = DEMO_SCENE_CONTROLS;
        break;
    default:
        g_demo.running = false;
        break;
    }
}

static void update_controls(const InputFrame *input)
{
    if (input->back_pressed || input->confirm_pressed) {
        g_demo.scene = DEMO_SCENE_TITLE;
    }
}

static void update_ship_test(const InputFrame *input, float dt_ms)
{
    float dt = dt_ms / 1000.0f;
    float heading_radians;

    if (input->back_pressed) {
        g_demo.scene = DEMO_SCENE_TITLE;
        return;
    }

    if (input->left_held) {
        g_demo.ship.heading_deg -= 160.0f * dt;
    }
    if (input->right_held) {
        g_demo.ship.heading_deg += 160.0f * dt;
    }
    if (input->run_held || input->jump_pressed) {
        g_demo.ship.speed += 180.0f * dt;
    } else {
        g_demo.ship.speed -= 100.0f * dt;
    }
    g_demo.ship.speed = clampf(g_demo.ship.speed, 0.0f, 320.0f);

    heading_radians = (g_demo.ship.heading_deg - 90.0f) * 3.14159265f / 180.0f;
    g_demo.ship.x += cosf(heading_radians) * g_demo.ship.speed * dt;
    g_demo.ship.y += sinf(heading_radians) * g_demo.ship.speed * dt;

    if (g_demo.ship.x < 80.0f) g_demo.ship.x = (float)kWindowWidth - 80.0f;
    if (g_demo.ship.x > (float)kWindowWidth - 80.0f) g_demo.ship.x = 80.0f;
    if (g_demo.ship.y < 140.0f) g_demo.ship.y = (float)kWindowHeight - 140.0f;
    if (g_demo.ship.y > (float)kWindowHeight - 140.0f) g_demo.ship.y = 140.0f;

    if (g_demo.ship.speed > 10.0f) {
        SDL_Color color = {210, 176, 106, 170};
        spawn_particle(
            g_demo.ship.x - cosf(heading_radians) * 30.0f,
            g_demo.ship.y - sinf(heading_radians) * 30.0f,
            -cosf(heading_radians) * (90.0f + g_demo.ship.speed * 0.5f),
            -sinf(heading_radians) * (90.0f + g_demo.ship.speed * 0.5f),
            5.0f,
            450.0f,
            color,
            g_demo.ship.heading_deg,
            100.0f);
    }

    if (input->bond_pressed) {
        size_t index;
        SDL_Color color = {210, 176, 106, 200};
        for (index = 0; index < 20; ++index) {
            float angle = (float)index * 18.0f;
            float radians = angle * 3.14159265f / 180.0f;
            spawn_particle(
                g_demo.ship.x,
                g_demo.ship.y,
                cosf(radians) * 160.0f,
                sinf(radians) * 160.0f,
                7.0f,
                700.0f,
                color,
                angle,
                180.0f - angle);
        }
    }
}

static void handle_campaign_interact(void)
{
    const AridfeihthRoom *room = g_demo.runtime.current_room;

    if (room == NULL) {
        return;
    }

    if (strcmp(room->id, "glasswind_causeway") == 0 && !g_demo.campaign.mirror_newt) {
        g_demo.campaign.mirror_newt = true;
        add_inventory_item("mirror_newt");
        set_banner("Mirror Newt rescued.");
        return;
    }
    if (strcmp(room->id, "mirror_cistern") == 0 && g_demo.campaign.mirror_newt && !g_demo.campaign.latch_spider) {
        g_demo.campaign.latch_spider = true;
        add_inventory_item("latch_spider");
        set_banner("Latch Spider freed from the cistern.");
        return;
    }
    if (strcmp(room->id, "munki_refractionary") == 0 && !g_demo.campaign.refraction_munki) {
        g_demo.campaign.refraction_munki = true;
        add_inventory_item("refraction_munki");
        g_demo.runtime.pet_tutorial_unlocked = true;
        set_banner("Refraction Munki bonded. Pet tutorial unlocked.");
        return;
    }
    if ((strstr(room->id, "harbor") != NULL || strstr(room->id, "skiff") != NULL || strstr(room->id, "quay") != NULL) && !g_demo.runtime.ship_mode_unlocked) {
        g_demo.runtime.ship_mode_unlocked = true;
        add_inventory_item("pirate_chart");
        set_banner("Ship Adventure Test marked on the title menu.");
        return;
    }
    if ((room->flags & ARIDFEIHTH_ROOM_FLAG_SAFE) != 0u) {
        set_banner("You regroup under the brass lamps.");
        return;
    }

    set_banner("Nothing new responds here yet.");
}

static void handle_campaign_attack(void)
{
    static const AnimationClip *combos[] = {&kCombo1Clip, &kCombo2Clip, &kCombo3Clip};
    const AridfeihthRoom *room = g_demo.runtime.current_room;
    int room_index;
    int threshold;

    set_override_clip(combos[g_demo.campaign.next_combo % 3]);
    g_demo.campaign.next_combo += 1;

    if (room == NULL) {
        return;
    }
    room_index = room_index_from_id(room->id);
    if (room_index < 0) {
        return;
    }

    threshold = clear_threshold_for_room(room);
    if (threshold <= 0 || g_demo.campaign.room_cleared[room_index]) {
        return;
    }

    g_demo.campaign.room_damage[room_index] += 1;
    if (strcmp(room->id, "ember_nave") != 0 && strcmp(room->id, "ashfall_dais") != 0 && g_demo.campaign.room_damage[room_index] >= threshold) {
        mark_room_cleared(room);
    } else if (strcmp(room->id, "ember_nave") == 0 || strcmp(room->id, "ashfall_dais") == 0) {
        set_banner("Pressure is mounting. Bond Weave will finish this room.");
    }
}

static void handle_campaign_bond(void)
{
    const AridfeihthRoom *room = g_demo.runtime.current_room;
    int room_index;
    int threshold;

    trigger_bond_weave();
    if (room == NULL) {
        return;
    }

    room_index = room_index_from_id(room->id);
    if (room_index < 0) {
        return;
    }

    threshold = clear_threshold_for_room(room);
    if (threshold > 0 && g_demo.campaign.room_damage[room_index] >= threshold) {
        mark_room_cleared(room);
    } else {
        set_banner("Bond Weave rings out, but the room still holds.");
    }
}

static void try_room_transition(const AridfeihthRoomExit *exit_spec, bool from_right)
{
    std::string requirement_text;

    if (exit_spec == NULL || exit_spec->room_id == NULL) {
        return;
    }

    if (!can_use_exit(exit_spec)) {
        if (exit_spec->requires != NULL) {
            requirement_text = "Route blocked until ";
            requirement_text += exit_spec->requires;
            requirement_text += " is secured.";
            set_banner(requirement_text.c_str());
        } else {
            set_banner("The route will not open until this room is settled.");
        }
        return;
    }

    move_to_room(exit_spec->room_id, from_right);
}

static void update_campaign(const InputFrame *input, float dt_ms)
{
    const AridfeihthRoom *room = g_demo.runtime.current_room;
    float move_speed = input->run_held ? 320.0f : 210.0f;
    float movement = input->horizontal_axis;
    const AnimationClip *target_clip;
    int room_index;

    if (input->back_pressed) {
        g_demo.scene = DEMO_SCENE_TITLE;
        return;
    }

    if (input->interact_pressed) {
        handle_campaign_interact();
    }
    if (input->attack_pressed) {
        handle_campaign_attack();
    }
    if (input->bond_pressed) {
        handle_campaign_bond();
    }
    if (input->wind_pressed) {
        g_demo.campaign.wind_kite = !g_demo.campaign.wind_kite;
        set_banner(g_demo.campaign.wind_kite ? "Wind Kite engaged." : "Wind Kite stowed.");
    }
    if (input->jump_pressed && !g_demo.campaign.airborne) {
        g_demo.campaign.airborne = true;
        g_demo.campaign.velocity_y = -420.0f;
        set_override_clip(&kJumpClip);
    }

    g_demo.campaign.player_x += movement * move_speed * (dt_ms / 1000.0f);
    g_demo.campaign.player_x = clampf(g_demo.campaign.player_x, 96.0f, (float)kWindowWidth - 96.0f);

    if (movement < -0.1f) {
        g_demo.campaign.facing = -1;
    } else if (movement > 0.1f) {
        g_demo.campaign.facing = 1;
    }

    if (g_demo.campaign.airborne) {
        g_demo.campaign.velocity_y += 980.0f * (dt_ms / 1000.0f);
        g_demo.campaign.player_y += g_demo.campaign.velocity_y * (dt_ms / 1000.0f);
        if (g_demo.campaign.player_y >= 0.0f) {
            g_demo.campaign.player_y = 0.0f;
            g_demo.campaign.velocity_y = 0.0f;
            g_demo.campaign.airborne = false;
        }
    }

    if (g_demo.campaign.override_remaining_ms > 0.0f) {
        g_demo.campaign.override_remaining_ms -= dt_ms;
        if (g_demo.campaign.override_remaining_ms <= 0.0f) {
            g_demo.campaign.override_clip = NULL;
        }
    }

    if (g_demo.campaign.override_clip != NULL) {
        target_clip = g_demo.campaign.override_clip;
    } else if (g_demo.campaign.airborne) {
        target_clip = &kJumpClip;
    } else if (absf(movement) > 0.4f && input->run_held) {
        target_clip = &kRunClip;
    } else if (absf(movement) > 0.1f) {
        target_clip = &kWalkClip;
    } else {
        target_clip = &kIdleClip;
    }

    start_clip(target_clip);
    advance_animation(dt_ms);

    if (g_demo.campaign.banner_ms > 0.0f) {
        g_demo.campaign.banner_ms -= dt_ms;
    }

    if (g_demo.campaign.bond_weave.active) {
        g_demo.campaign.bond_weave.elapsed_ms += dt_ms;
        if (g_demo.campaign.bond_weave.elapsed_ms >= g_demo.campaign.bond_weave.total_ms) {
            g_demo.campaign.bond_weave.active = false;
        }
    }

    room_index = room_index_from_id(room != NULL ? room->id : NULL);
    if (room != NULL && room_index >= 0 && (room->flags & ARIDFEIHTH_ROOM_FLAG_SAFE) != 0u) {
        g_demo.campaign.room_cleared[room_index] = true;
    }

    if (room != NULL && g_demo.campaign.player_x <= 102.0f) {
        try_room_transition(&room->left, true);
    } else if (room != NULL && g_demo.campaign.player_x >= (float)kWindowWidth - 102.0f) {
        if (room->alternate_right.room_id != NULL && input->down_held) {
            try_room_transition(&room->alternate_right, false);
        } else {
            try_room_transition(&room->right, false);
        }
    }
}

static void update_demo(float dt_ms)
{
    InputFrame input = sample_input();

    switch (g_demo.scene) {
    case DEMO_SCENE_TITLE:
        update_title(&input);
        break;
    case DEMO_SCENE_CONTROLS:
        update_controls(&input);
        break;
    case DEMO_SCENE_SHIP_TEST:
        update_ship_test(&input, dt_ms);
        break;
    case DEMO_SCENE_CAMPAIGN:
        update_campaign(&input, dt_ms);
        break;
    default:
        break;
    }

    update_particles(dt_ms);
}

static void set_draw_color(SDL_Color color)
{
    SDL_SetRenderDrawColor(g_demo.renderer, color.r, color.g, color.b, color.a);
}

static void fill_rect(const SDL_FRect &rect, SDL_Color color)
{
    set_draw_color(color);
    SDL_RenderFillRectF(g_demo.renderer, &rect);
}

static void draw_rect(const SDL_FRect &rect, SDL_Color color)
{
    set_draw_color(color);
    SDL_RenderDrawRectF(g_demo.renderer, &rect);
}

static void draw_texture_region(const TextureAsset *asset, const SDL_Rect *source, const SDL_FRect &dest, Uint8 alpha, double rotation_deg, SDL_RendererFlip flip)
{
    if (asset == NULL || asset->texture == NULL) {
        return;
    }
    SDL_SetTextureBlendMode(asset->texture, SDL_BLENDMODE_BLEND);
    SDL_SetTextureAlphaMod(asset->texture, alpha);
    SDL_RenderCopyExF(g_demo.renderer, asset->texture, source, &dest, rotation_deg, NULL, flip);
    SDL_SetTextureAlphaMod(asset->texture, 255);
}

static void draw_sprite(const SpriteSheet *sheet, int row, int col, float x, float y, float scale, float alpha, float rotation_deg, bool flip_h)
{
    SDL_Rect source;
    SDL_FRect dest;

    if (sheet == NULL || sheet->texture_asset.texture == NULL || sheet->columns == 0 || sheet->rows == 0) {
        return;
    }

    col = col % sheet->columns;
    row = row % sheet->rows;
    source.x = col * sheet->frame_width;
    source.y = row * sheet->frame_height;
    source.w = sheet->frame_width;
    source.h = sheet->frame_height;
    dest.x = x - sheet->frame_width * scale * 0.5f;
    dest.y = y - sheet->frame_height * scale;
    dest.w = sheet->frame_width * scale;
    dest.h = sheet->frame_height * scale;

    draw_texture_region(&sheet->texture_asset, &source, dest, (Uint8)(alpha * 255.0f), rotation_deg, flip_h ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
}

static void render_text_once(TTF_Font *font, const char *text, const SDL_FRect &box, SDL_Color color, TextAlign align)
{
    SDL_Surface *surface;
    SDL_Texture *texture;
    SDL_FRect dest;
    Uint32 wrap_width;

    if (font == NULL || text == NULL || text[0] == 0) {
        return;
    }

    wrap_width = box.w > 0.0f ? (Uint32)box.w : 4096u;
    surface = TTF_RenderUTF8_Blended_Wrapped(font, text, color, wrap_width);
    if (surface == NULL) {
        return;
    }
    texture = SDL_CreateTextureFromSurface(g_demo.renderer, surface);
    if (texture == NULL) {
        SDL_FreeSurface(surface);
        return;
    }

    dest.x = box.x;
    dest.y = box.y;
    dest.w = (float)surface->w;
    dest.h = (float)surface->h;
    if (align == TEXT_ALIGN_CENTER) {
        dest.x = box.x + (box.w - dest.w) * 0.5f;
    } else if (align == TEXT_ALIGN_FAR) {
        dest.x = box.x + box.w - dest.w;
    }
    SDL_RenderCopyF(g_demo.renderer, texture, NULL, &dest);
    SDL_DestroyTexture(texture);
    SDL_FreeSurface(surface);
}

static void draw_text_shadowed(TTF_Font *font, const char *text, const SDL_FRect &box, SDL_Color color, TextAlign align)
{
    SDL_FRect shadow_box = {box.x + 2.0f, box.y + 2.0f, box.w, box.h};
    SDL_Color shadow = {8, 9, 11, 220};

    render_text_once(font, text, shadow_box, shadow, align);
    render_text_once(font, text, box, color, align);
}

static void fill_polygon(const SDL_FPoint *points, int count, SDL_Color color)
{
    std::vector<SDL_Vertex> vertices;
    std::vector<int> indices;
    int index;

    if (count < 3) {
        return;
    }

    vertices.resize((size_t)count);
    indices.resize((size_t)(count - 2) * 3u);
    for (index = 0; index < count; ++index) {
        vertices[(size_t)index].position = points[index];
        vertices[(size_t)index].color = color;
        vertices[(size_t)index].tex_coord.x = 0.0f;
        vertices[(size_t)index].tex_coord.y = 0.0f;
    }
    for (index = 0; index < count - 2; ++index) {
        indices[(size_t)index * 3u + 0u] = 0;
        indices[(size_t)index * 3u + 1u] = index + 1;
        indices[(size_t)index * 3u + 2u] = index + 2;
    }
    SDL_RenderGeometry(g_demo.renderer, NULL, vertices.data(), count, indices.data(), (int)indices.size());
}

static void draw_polygon_outline(const SDL_FPoint *points, int count, SDL_Color color)
{
    std::vector<SDL_FPoint> outline;
    int index;

    if (count < 2) {
        return;
    }

    outline.resize((size_t)count + 1u);
    for (index = 0; index < count; ++index) {
        outline[(size_t)index] = points[index];
    }
    outline[(size_t)count] = points[0];
    set_draw_color(color);
    SDL_RenderDrawLinesF(g_demo.renderer, outline.data(), count + 1);
}

static void transform_points(const SDL_FPoint *source, SDL_FPoint *dest, int count, float origin_x, float origin_y, float rotation_deg)
{
    float radians = rotation_deg * 3.14159265f / 180.0f;
    float c = cosf(radians);
    float s = sinf(radians);
    int index;

    for (index = 0; index < count; ++index) {
        dest[index].x = origin_x + source[index].x * c - source[index].y * s;
        dest[index].y = origin_y + source[index].x * s + source[index].y * c;
    }
}

static void render_particles(void)
{
    size_t index;

    for (index = 0; index < sizeof(g_demo.particles) / sizeof(g_demo.particles[0]); ++index) {
        if (!g_demo.particles[index].active) {
            continue;
        }

        SDL_Color color = g_demo.particles[index].color;
        SDL_FRect rect;
        float alpha = g_demo.particles[index].life_ms / g_demo.particles[index].max_life_ms;
        if (alpha < 0.0f) {
            alpha = 0.0f;
        }
        color.a = (Uint8)(alpha * (float)color.a);
        rect.x = g_demo.particles[index].x - g_demo.particles[index].size * 0.5f;
        rect.y = g_demo.particles[index].y - g_demo.particles[index].size * 0.5f;
        rect.w = g_demo.particles[index].size;
        rect.h = g_demo.particles[index].size;
        fill_rect(rect, color);
    }
}

static void render_campaign(void)
{
    const AridfeihthRoom *room = g_demo.runtime.current_room;
    const TextureAsset *backdrop = pick_room_backdrop(room);
    SDL_FRect fullscreen = {0.0f, 0.0f, (float)kWindowWidth, (float)kWindowHeight};
    SDL_FRect info_box = {28.0f, 584.0f, 1224.0f, 112.0f};
    int room_index = room != NULL ? room_index_from_id(room->id) : -1;

    SDL_SetRenderDrawBlendMode(g_demo.renderer, SDL_BLENDMODE_BLEND);
    set_draw_color(SDL_Color{17, 23, 32, 255});
    SDL_RenderClear(g_demo.renderer);
    if (backdrop != NULL && backdrop->texture != NULL) {
        draw_texture_region(backdrop, NULL, fullscreen, 255, 0.0, SDL_FLIP_NONE);
    }

    if (room != NULL) {
        Uint8 overlay_alpha = (Uint8)(room->danger * 18u);
        if (overlay_alpha > 180u) {
            overlay_alpha = 180u;
        }
        fill_rect(fullscreen, SDL_Color{20, 8, 8, overlay_alpha});
    }

    if (g_demo.campaign.bond_weave.active) {
        int fx_frame = (int)(g_demo.campaign.bond_weave.elapsed_ms / 110.0f) % g_demo.assets.bond_weave.columns;
        float fx_alpha = 1.0f - (g_demo.campaign.bond_weave.elapsed_ms / g_demo.campaign.bond_weave.total_ms);
        draw_sprite(&g_demo.assets.bond_weave, 0, fx_frame, g_demo.campaign.player_x, kGroundY - 44.0f + g_demo.campaign.player_y, 3.5f, fx_alpha, g_demo.campaign.bond_weave.elapsed_ms * 0.22f, false);
    }

    if (g_demo.assets.field_handler.texture_asset.texture != NULL && g_demo.campaign.clip != NULL) {
        const AnimationFrame *frame = &g_demo.campaign.clip->frames[g_demo.campaign.frame_index];
        draw_sprite(&g_demo.assets.field_handler, frame->row, frame->col, g_demo.campaign.player_x, kGroundY + g_demo.campaign.player_y, kPlayerScale, 1.0f, 0.0f, g_demo.campaign.facing < 0);
    }

    if (g_demo.campaign.mirror_newt) {
        draw_sprite(&g_demo.assets.mirror_newt, 0, (int)((SDL_GetTicks64() / 160u) % 4u), g_demo.campaign.player_x - 96.0f, kGroundY + 8.0f, 2.0f, 0.95f, 0.0f, false);
    }
    if (g_demo.campaign.latch_spider) {
        draw_sprite(&g_demo.assets.latch_spider, 0, (int)((SDL_GetTicks64() / 200u) % 4u), g_demo.campaign.player_x + 112.0f, kGroundY + 12.0f, 2.0f, 0.95f, 0.0f, false);
    }
    if (g_demo.campaign.salt_ram) {
        draw_sprite(&g_demo.assets.salt_ram, 0, (int)((SDL_GetTicks64() / 180u) % 4u), g_demo.campaign.player_x + 184.0f, kGroundY + 18.0f, 2.0f, 0.95f, 0.0f, false);
    }

    render_particles();

    if (g_demo.assets.hud_pack.texture != NULL) {
        SDL_Rect source = {0, 0, g_demo.assets.hud_pack.width, g_demo.assets.hud_pack.height};
        SDL_FRect dest = {22.0f, 18.0f, 640.0f, 160.0f};
        draw_texture_region(&g_demo.assets.hud_pack, &source, dest, 255, 0.0, SDL_FLIP_NONE);
    }

    fill_rect(info_box, SDL_Color{16, 23, 32, 176});
    draw_rect(info_box, SDL_Color{181, 150, 87, 220});

    if (room != NULL) {
        SDL_FRect name_box = {48.0f, 596.0f, 500.0f, 32.0f};
        SDL_FRect objective_box = {48.0f, 634.0f, 1020.0f, 48.0f};
        draw_text_shadowed(g_demo.assets.fonts.heading, room->name, name_box, SDL_Color{210, 176, 106, 255}, TEXT_ALIGN_NEAR);
        draw_text_shadowed(g_demo.assets.fonts.body, room->objective, objective_box, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
        if (room->alternate_right.room_id != NULL) {
            SDL_FRect detour_box = {826.0f, 600.0f, 390.0f, 24.0f};
            draw_text_shadowed(g_demo.assets.fonts.small, "Hold Down at the east edge for the detour route.", detour_box, SDL_Color{210, 176, 106, 255}, TEXT_ALIGN_FAR);
        }
        if (room_index >= 0 && !g_demo.campaign.room_cleared[room_index] && clear_threshold_for_room(room) > 0) {
            char pressure[96];
            SDL_FRect pressure_box = {874.0f, 634.0f, 330.0f, 24.0f};
            snprintf(pressure, sizeof(pressure), "Room pressure: %d / %d", g_demo.campaign.room_damage[room_index], clear_threshold_for_room(room));
            draw_text_shadowed(g_demo.assets.fonts.small, pressure, pressure_box, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_FAR);
        }
    }

    if (g_demo.campaign.banner_ms > 0.0f) {
        float alpha = clampf(g_demo.campaign.banner_ms / 900.0f, 0.0f, 1.0f);
        SDL_FRect banner_rect = {320.0f, 194.0f, 640.0f, 54.0f};
        fill_rect(banner_rect, SDL_Color{11, 14, 18, (Uint8)(alpha * 180.0f)});
        draw_rect(banner_rect, SDL_Color{210, 176, 106, (Uint8)(alpha * 220.0f)});
        draw_text_shadowed(g_demo.assets.fonts.body, g_demo.campaign.banner, SDL_FRect{334.0f, 208.0f, 612.0f, 26.0f}, SDL_Color{240, 232, 215, (Uint8)(alpha * 255.0f)}, TEXT_ALIGN_CENTER);
    }

    draw_text_shadowed(g_demo.assets.fonts.small, "Move: Arrow keys / Left Stick  Attack: Z or X  Interact: E or Y  Jump: Space or A  Bond Weave: V or RB  Esc: Title", SDL_FRect{20.0f, 688.0f, 1240.0f, 20.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_CENTER);
}

static void render_ship_test(void)
{
    SDL_FPoint hull_src[4] = {{-40.0f, 12.0f}, {0.0f, -22.0f}, {46.0f, 10.0f}, {0.0f, 28.0f}};
    SDL_FPoint sail_src[3] = {{-2.0f, -14.0f}, {26.0f, -6.0f}, {4.0f, 10.0f}};
    SDL_FPoint dune_near[3] = {{-180.0f, 720.0f}, {140.0f, 520.0f}, {580.0f, 720.0f}};
    SDL_FPoint dune_far[3] = {{420.0f, 720.0f}, {980.0f, 500.0f}, {1460.0f, 720.0f}};
    SDL_FPoint hull[4];
    SDL_FPoint sail[3];
    int y;

    SDL_SetRenderDrawBlendMode(g_demo.renderer, SDL_BLENDMODE_BLEND);
    for (y = 0; y < kWindowHeight; y += 8) {
        float t = (float)y / (float)kWindowHeight;
        SDL_FRect strip = {0.0f, (float)y, (float)kWindowWidth, 8.0f};
        SDL_Color color = {
            lerp_u8(21, 72, t),
            lerp_u8(24, 53, t),
            lerp_u8(39, 38, t),
            255
        };
        fill_rect(strip, color);
    }

    fill_polygon(dune_near, 3, SDL_Color{63, 34, 24, 255});
    fill_polygon(dune_far, 3, SDL_Color{72, 42, 28, 255});
    fill_rect(SDL_FRect{0.0f, 592.0f, (float)kWindowWidth, 128.0f}, SDL_Color{181, 150, 87, 255});

    render_particles();

    transform_points(hull_src, hull, 4, g_demo.ship.x, g_demo.ship.y, g_demo.ship.heading_deg);
    transform_points(sail_src, sail, 3, g_demo.ship.x, g_demo.ship.y, g_demo.ship.heading_deg);
    fill_polygon(hull, 4, SDL_Color{94, 115, 140, 255});
    draw_polygon_outline(hull, 4, SDL_Color{15, 18, 22, 255});
    fill_polygon(sail, 3, SDL_Color{210, 176, 106, 240});
    draw_polygon_outline(sail, 3, SDL_Color{15, 18, 22, 255});
    fill_rect(SDL_FRect{g_demo.ship.x - 10.0f, g_demo.ship.y - 10.0f, 22.0f, 22.0f}, SDL_Color{33, 17, 20, 180});

    draw_text_shadowed(g_demo.assets.fonts.title, "Ship Adventure Test", SDL_FRect{0.0f, 36.0f, (float)kWindowWidth, 40.0f}, SDL_Color{210, 176, 106, 255}, TEXT_ALIGN_CENTER);
    draw_text_shadowed(g_demo.assets.fonts.body, "This mode exists to prove the SDL path can already handle rotation, alpha, and particles without the GDI+ renderer.", SDL_FRect{120.0f, 88.0f, 1040.0f, 28.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_CENTER);
    draw_text_shadowed(g_demo.assets.fonts.small, "Turn: Left/Right or Stick  Thrust: Shift/A  Burst ring: V or RB  Esc: Title", SDL_FRect{0.0f, 678.0f, (float)kWindowWidth, 24.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_CENTER);
}

static void render_title(void)
{
    size_t index;

    set_draw_color(SDL_Color{14, 18, 24, 255});
    SDL_RenderClear(g_demo.renderer);
    if (g_demo.assets.backdrop_refuge.texture != NULL) {
        draw_texture_region(&g_demo.assets.backdrop_refuge, NULL, SDL_FRect{0.0f, 0.0f, (float)kWindowWidth, (float)kWindowHeight}, 255, 0.0, SDL_FLIP_NONE);
    }
    fill_rect(SDL_FRect{0.0f, 0.0f, (float)kWindowWidth, (float)kWindowHeight}, SDL_Color{14, 18, 24, 170});

    if (g_demo.assets.field_handler.texture_asset.texture != NULL) {
        draw_sprite(&g_demo.assets.field_handler, 0, (int)((SDL_GetTicks64() / 180u) % 4u), 220.0f, 540.0f, 3.4f, 1.0f, 0.0f, false);
    }
    if (g_demo.assets.mirror_newt.texture_asset.texture != NULL) {
        draw_sprite(&g_demo.assets.mirror_newt, 0, (int)((SDL_GetTicks64() / 220u) % 4u), 1010.0f, 562.0f, 3.0f, 0.92f, 0.0f, false);
    }

    draw_text_shadowed(g_demo.assets.fonts.title, "Aridfeihth", SDL_FRect{0.0f, 66.0f, (float)kWindowWidth, 48.0f}, SDL_Color{210, 176, 106, 255}, TEXT_ALIGN_CENTER);
    draw_text_shadowed(g_demo.assets.fonts.body, "Ash-Reliquary SDL Runtime Pass", SDL_FRect{0.0f, 118.0f, (float)kWindowWidth, 28.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_CENTER);
    draw_text_shadowed(g_demo.assets.fonts.small, "70 ms in the animation data means one playback step lasts 0.07 seconds before the next sprite frame advances.", SDL_FRect{140.0f, 164.0f, 1000.0f, 28.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_CENTER);

    for (index = 0; index < g_demo.package->title_option_count; ++index) {
        SDL_FRect row_rect = {430.0f, 248.0f + (float)index * 62.0f, 420.0f, 46.0f};
        SDL_Color fill = index == (size_t)g_demo.title_index ? SDL_Color{181, 150, 87, 220} : SDL_Color{11, 14, 18, 168};
        SDL_Color border = index == (size_t)g_demo.title_index ? SDL_Color{240, 232, 215, 255} : SDL_Color{94, 115, 140, 190};
        SDL_Color text = index == (size_t)g_demo.title_index ? SDL_Color{11, 14, 18, 255} : SDL_Color{240, 232, 215, 255};
        fill_rect(row_rect, fill);
        draw_rect(row_rect, border);
        draw_text_shadowed(g_demo.assets.fonts.heading, g_demo.package->title_options[index], SDL_FRect{row_rect.x, row_rect.y + 10.0f, row_rect.w, 24.0f}, text, TEXT_ALIGN_CENTER);
    }

    fill_rect(SDL_FRect{370.0f, 520.0f, 540.0f, 112.0f}, SDL_Color{11, 14, 18, 220});
    draw_rect(SDL_FRect{370.0f, 520.0f, 540.0f, 112.0f}, SDL_Color{181, 150, 87, 255});
    draw_text_shadowed(g_demo.assets.fonts.body, "Start Prototype enters the playable room route. Ship Adventure Test is the backend stress pass for transform-heavy 2D rendering.", SDL_FRect{392.0f, 542.0f, 496.0f, 54.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_CENTER);
    draw_text_shadowed(g_demo.assets.fonts.small, "Up/Down to choose, Enter to confirm.", SDL_FRect{0.0f, 684.0f, (float)kWindowWidth, 22.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_CENTER);
}

static void render_controls(void)
{
    set_draw_color(SDL_Color{16, 20, 26, 255});
    SDL_RenderClear(g_demo.renderer);
    if (g_demo.assets.backdrop_choir.texture != NULL) {
        draw_texture_region(&g_demo.assets.backdrop_choir, NULL, SDL_FRect{0.0f, 0.0f, (float)kWindowWidth, (float)kWindowHeight}, 255, 0.0, SDL_FLIP_NONE);
    }
    fill_rect(SDL_FRect{140.0f, 96.0f, 1000.0f, 528.0f}, SDL_Color{11, 14, 18, 210});
    draw_rect(SDL_FRect{140.0f, 96.0f, 1000.0f, 528.0f}, SDL_Color{181, 150, 87, 255});

    draw_text_shadowed(g_demo.assets.fonts.title, "Controls", SDL_FRect{0.0f, 124.0f, (float)kWindowWidth, 38.0f}, SDL_Color{210, 176, 106, 255}, TEXT_ALIGN_CENTER);
    draw_text_shadowed(g_demo.assets.fonts.heading, "Campaign", SDL_FRect{184.0f, 202.0f, 160.0f, 28.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.body, "Left / Right or Stick: move between gates and rooms", SDL_FRect{184.0f, 242.0f, 900.0f, 24.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.body, "Shift or LT: run", SDL_FRect{184.0f, 276.0f, 900.0f, 24.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.body, "Z / X or X: attack and build room-break pressure", SDL_FRect{184.0f, 310.0f, 900.0f, 24.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.body, "E or Y: rescue pets, rest, or unlock route interactions", SDL_FRect{184.0f, 344.0f, 900.0f, 24.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.body, "Space or A: jump", SDL_FRect{184.0f, 378.0f, 900.0f, 24.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.body, "V or RB: trigger Bond Weave, required for the Ember Nave finish", SDL_FRect{184.0f, 412.0f, 900.0f, 24.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.body, "C or LB: toggle Wind Kite status for feedback", SDL_FRect{184.0f, 446.0f, 900.0f, 24.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.body, "At branch rooms, hold Down while exiting right to take the optional detour.", SDL_FRect{184.0f, 480.0f, 900.0f, 24.0f}, SDL_Color{210, 176, 106, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.heading, "Ship Adventure Test", SDL_FRect{184.0f, 540.0f, 220.0f, 28.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.body, "Left / Right turns the craft. Shift / A thrusts. V / RB emits a particle burst.", SDL_FRect{184.0f, 578.0f, 860.0f, 24.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_NEAR);
    draw_text_shadowed(g_demo.assets.fonts.small, "Esc or Enter returns to the title.", SDL_FRect{0.0f, 666.0f, (float)kWindowWidth, 22.0f}, SDL_Color{240, 232, 215, 255}, TEXT_ALIGN_CENTER);
}

static void render_demo(void)
{
    switch (g_demo.scene) {
    case DEMO_SCENE_TITLE:
        render_title();
        break;
    case DEMO_SCENE_CONTROLS:
        render_controls();
        break;
    case DEMO_SCENE_SHIP_TEST:
        render_ship_test();
        break;
    case DEMO_SCENE_CAMPAIGN:
        render_campaign();
        break;
    default:
        break;
    }
}

static void handle_sdl_events(void)
{
    SDL_Event event;

    while (SDL_PollEvent(&event)) {
        switch (event.type) {
        case SDL_QUIT:
            g_demo.running = false;
            break;
        case SDL_KEYDOWN:
            if (event.key.repeat == 0 && event.key.keysym.scancode < SDL_NUM_SCANCODES) {
                if (!g_key_held[event.key.keysym.scancode]) {
                    g_key_pressed[event.key.keysym.scancode] = true;
                }
                g_key_held[event.key.keysym.scancode] = true;
            }
            break;
        case SDL_KEYUP:
            if (event.key.keysym.scancode < SDL_NUM_SCANCODES) {
                g_key_held[event.key.keysym.scancode] = false;
            }
            break;
        default:
            break;
        }
    }
}

static bool init_demo(void)
{
    Uint32 window_flags;

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS) != 0) {
        return false;
    }
    if ((IMG_Init(IMG_INIT_PNG) & IMG_INIT_PNG) == 0) {
        return false;
    }
    if (TTF_Init() != 0) {
        return false;
    }

    window_flags = g_demo.smoke_mode ? SDL_WINDOW_HIDDEN : SDL_WINDOW_SHOWN;
    g_demo.window = SDL_CreateWindow(kWindowTitle, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, kWindowWidth, kWindowHeight, window_flags);
    if (g_demo.window == NULL) {
        return false;
    }

    g_demo.renderer = SDL_CreateRenderer(g_demo.window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (g_demo.renderer == NULL) {
        g_demo.renderer = SDL_CreateRenderer(g_demo.window, -1, SDL_RENDERER_SOFTWARE);
    }
    if (g_demo.renderer == NULL) {
        return false;
    }

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");
    SDL_SetRenderDrawBlendMode(g_demo.renderer, SDL_BLENDMODE_BLEND);
    if (!load_assets(&g_demo.assets)) {
        return false;
    }

    load_xinput_runtime(&g_demo.xinput);
    g_demo.perf_frequency = SDL_GetPerformanceFrequency();
    g_demo.last_counter = SDL_GetPerformanceCounter();
    g_demo.running = true;
    g_demo.scene = DEMO_SCENE_TITLE;
    g_demo.title_index = 0;
    boot_runtime();
    begin_ship_test();
    return true;
}

static void shutdown_demo(void)
{
    unload_xinput_runtime(&g_demo.xinput);
    unload_assets(&g_demo.assets);
    if (g_demo.renderer != NULL) {
        SDL_DestroyRenderer(g_demo.renderer);
    }
    if (g_demo.window != NULL) {
        SDL_DestroyWindow(g_demo.window);
    }
    g_demo.renderer = NULL;
    g_demo.window = NULL;
    TTF_Quit();
    IMG_Quit();
    SDL_Quit();
}

static int run_smoke_check(void)
{
    AridfeihthRuntimeState smoke_runtime = g_demo.runtime;

    aridfeihth_start_prototype(&smoke_runtime);
    printf("smoke=ok\n");
    printf("package=%s\n", g_demo.package->metadata.title);
    printf("rooms=%lu\n", (unsigned long)g_demo.package->room_count);
    printf("player_moves=%lu\n", (unsigned long)g_demo.package->player_move_count);
    printf("field_handler_loaded=%d\n", g_demo.assets.field_handler.texture_asset.texture != NULL ? 1 : 0);
    printf("hud_loaded=%d\n", g_demo.assets.hud_pack.texture != NULL ? 1 : 0);
    printf("backdrop_loaded=%d\n", g_demo.assets.backdrop_refuge.texture != NULL ? 1 : 0);
    printf("start_room=%s\n", smoke_runtime.current_room != NULL ? smoke_runtime.current_room->id : "(null)");
    fflush(stdout);
    return 0;
}

int main(int argc, char **argv)
{
    int index;

    ZeroMemory(&g_demo, sizeof(g_demo));
    for (index = 1; index < argc; ++index) {
        if (strcmp(argv[index], "--smoke") == 0) {
            g_demo.smoke_mode = true;
        }
    }

    if (!init_demo()) {
        fprintf(stderr, "Failed to initialize the Aridfeihth SDL runtime. SDL=%s IMG=%s TTF=%s\n", SDL_GetError(), IMG_GetError(), TTF_GetError());
        shutdown_demo();
        return 1;
    }

    if (g_demo.smoke_mode) {
        int result = run_smoke_check();
        shutdown_demo();
        return result;
    }

    while (g_demo.running) {
        Uint64 now;
        float dt_ms;

        handle_sdl_events();
        if (!g_demo.running) {
            break;
        }

        now = SDL_GetPerformanceCounter();
        dt_ms = (float)((double)(now - g_demo.last_counter) * 1000.0 / (double)g_demo.perf_frequency);
        g_demo.last_counter = now;
        dt_ms = clampf(dt_ms, 1.0f, 33.0f);

        update_demo(dt_ms);
        render_demo();
        SDL_RenderPresent(g_demo.renderer);
        SDL_Delay(1);
    }

    shutdown_demo();
    return 0;
}