#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include <windows.h>
#include <mmsystem.h>
#include <objidl.h>
#include <gdiplus.h>
#include <xinput.h>

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string>
#include <vector>
#include <cwchar>

#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "winmm.lib")

extern "C" {
#include "aridfeihth_prototype_package.c"
}

using namespace Gdiplus;

static const wchar_t *kWindowClassName = L"AridfeihthGDIPlusDemoWindow";
static const wchar_t *kWindowTitle = L"Aridfeihth Ash-Reliquary Demo";
static const int kWindowWidth = 1280;
static const int kWindowHeight = 720;
static const float kGroundY = 560.0f;
static const float kPlayerScale = 2.0f;
static const int kAnimationStepMs = 70;
static const float kJumpVelocity = -455.0f;
static const float kGravityAccel = 980.0f;
static const float kCoyoteTimeMs = 110.0f;
static const float kJumpBufferMs = 110.0f;
static const float kSupportSnapTolerance = 26.0f;
static const float kPlayerFootHalfWidth = 26.0f;

enum DemoScene {
    DEMO_SCENE_TITLE = 0,
    DEMO_SCENE_CONTROLS,
    DEMO_SCENE_SHIP_TEST,
    DEMO_SCENE_CAMPAIGN
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

struct SpriteSheet {
    Image *image;
    UINT frame_width;
    UINT frame_height;
    UINT columns;
    UINT rows;
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
    Color color;
};

struct EffectState {
    bool active;
    float elapsed_ms;
    float total_ms;
};

struct PlatformSegment {
    const char *room_id;
    float left_x;
    float right_x;
    float top_y;
    float thickness;
    float motion_amplitude;
    float motion_speed;
    float motion_phase;
};

struct AudioState {
    bool available;
    bool muted;
    bool playing;
    wchar_t theme_path[MAX_PATH];
};

struct CampaignState {
    float player_x;
    float player_y;
    float velocity_y;
    float coyote_ms;
    float jump_buffer_ms;
    float room_time_ms;
    int facing;
    bool airborne;
    bool mirror_newt;
    bool latch_spider;
    bool salt_ram;
    bool refraction_munki;
    bool room_cleared[64];
    int room_damage[64];
    float banner_ms;
    wchar_t banner[256];
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
    Image *backdrop_refuge;
    Image *backdrop_choir;
    Image *backdrop_glasswind;
    Image *backdrop_ember;
    Image *hud_pack;
    SpriteSheet field_handler;
    SpriteSheet mirror_newt;
    SpriteSheet latch_spider;
    SpriteSheet salt_ram;
    SpriteSheet bond_weave;
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
    bool mute_pressed;
    float horizontal_axis;
};

struct DemoState {
    ULONG_PTR gdiplus_token;
    HWND window;
    Bitmap *framebuffer;
    bool running;
    bool smoke_mode;
    DemoScene scene;
    int title_index;
    LARGE_INTEGER last_counter;
    LARGE_INTEGER perf_frequency;
    Assets assets;
    AudioState audio;
    XInputRuntime xinput;
    const AridfeihthPrototypePackage *package;
    AridfeihthRuntimeState runtime;
    CampaignState campaign;
    ShipState ship;
    Particle particles[256];
};

static DemoState g_demo = {};
static bool g_key_held[256] = {};
static bool g_key_pressed[256] = {};
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

static const PlatformSegment kPlatformSegments[] = {
    {"aerie_spur", 308.0f, 530.0f, 486.0f, 24.0f, 0.0f, 0.0f, 0.0f},
    {"aerie_spur", 628.0f, 816.0f, 430.0f, 22.0f, 0.0f, 0.0f, 0.0f},
    {"aerie_spur", 918.0f, 1072.0f, 372.0f, 20.0f, 0.0f, 0.0f, 0.0f},
    {"chain_lift_annex", 248.0f, 430.0f, 502.0f, 24.0f, 28.0f, 1.80f, 0.20f},
    {"chain_lift_annex", 554.0f, 736.0f, 450.0f, 22.0f, 18.0f, 1.25f, 1.40f},
    {"chain_lift_annex", 848.0f, 1036.0f, 396.0f, 22.0f, 32.0f, 1.55f, 2.10f},
    {"pilgrim_skywalk", 294.0f, 474.0f, 498.0f, 22.0f, 0.0f, 0.0f, 0.0f},
    {"pilgrim_skywalk", 578.0f, 760.0f, 442.0f, 20.0f, 0.0f, 0.0f, 0.0f},
    {"pilgrim_skywalk", 864.0f, 1060.0f, 388.0f, 20.0f, 0.0f, 0.0f, 0.0f}
};

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

static float hash01(int seed)
{
    float value = sinf((float)seed * 12.9898f) * 43758.5453f;
    return value - floorf(value);
}

static bool room_has_platforms(const AridfeihthRoom *room)
{
    size_t index;

    if (room == NULL) {
        return false;
    }

    for (index = 0; index < sizeof(kPlatformSegments) / sizeof(kPlatformSegments[0]); ++index) {
        if (strcmp(kPlatformSegments[index].room_id, room->id) == 0) {
            return true;
        }
    }

    return false;
}

static float platform_top_y(const PlatformSegment *segment)
{
    float time_s;

    if (segment == NULL) {
        return kGroundY;
    }

    time_s = g_demo.campaign.room_time_ms / 1000.0f;
    return segment->top_y + sinf(time_s * segment->motion_speed + segment->motion_phase) * segment->motion_amplitude;
}

static bool platform_supports_x(const PlatformSegment *segment, float player_x)
{
    if (segment == NULL) {
        return false;
    }

    return player_x + kPlayerFootHalfWidth >= segment->left_x
        && player_x - kPlayerFootHalfWidth <= segment->right_x;
}

static bool find_surface_near_feet(const AridfeihthRoom *room, float player_x, float foot_y, float tolerance, float *out_surface_y)
{
    bool found = false;
    float best_distance = tolerance + 1.0f;
    float best_surface_y = kGroundY;
    float distance;
    size_t index;

    distance = absf(foot_y - kGroundY);
    if (distance <= tolerance) {
        found = true;
        best_distance = distance;
        best_surface_y = kGroundY;
    }

    for (index = 0; index < sizeof(kPlatformSegments) / sizeof(kPlatformSegments[0]); ++index) {
        float top_y;

        if (room == NULL || strcmp(kPlatformSegments[index].room_id, room->id) != 0 || !platform_supports_x(&kPlatformSegments[index], player_x)) {
            continue;
        }

        top_y = platform_top_y(&kPlatformSegments[index]);
        distance = absf(foot_y - top_y);
        if (distance <= tolerance && (!found || distance < best_distance || (absf(distance - best_distance) < 0.2f && top_y < best_surface_y))) {
            found = true;
            best_distance = distance;
            best_surface_y = top_y;
        }
    }

    if (found && out_surface_y != NULL) {
        *out_surface_y = best_surface_y;
    }

    return found;
}

static bool find_landing_surface(const AridfeihthRoom *room, float player_x, float previous_foot_y, float next_foot_y, float *out_surface_y)
{
    bool found = false;
    float landing_y = kGroundY;
    size_t index;

    if (previous_foot_y <= kGroundY && next_foot_y >= kGroundY) {
        found = true;
        landing_y = kGroundY;
    }

    for (index = 0; index < sizeof(kPlatformSegments) / sizeof(kPlatformSegments[0]); ++index) {
        float top_y;

        if (room == NULL || strcmp(kPlatformSegments[index].room_id, room->id) != 0 || !platform_supports_x(&kPlatformSegments[index], player_x)) {
            continue;
        }

        top_y = platform_top_y(&kPlatformSegments[index]);
        if (previous_foot_y <= top_y && next_foot_y >= top_y && (!found || top_y < landing_y)) {
            found = true;
            landing_y = top_y;
        }
    }

    if (found && out_surface_y != NULL) {
        *out_surface_y = landing_y;
    }

    return found;
}

static float find_projection_surface_y(const AridfeihthRoom *room, float player_x, float foot_y)
{
    float best_surface_y = kGroundY;
    size_t index;

    for (index = 0; index < sizeof(kPlatformSegments) / sizeof(kPlatformSegments[0]); ++index) {
        float top_y;

        if (room == NULL || strcmp(kPlatformSegments[index].room_id, room->id) != 0 || !platform_supports_x(&kPlatformSegments[index], player_x)) {
            continue;
        }

        top_y = platform_top_y(&kPlatformSegments[index]);
        if (top_y >= foot_y && top_y < best_surface_y) {
            best_surface_y = top_y;
        }
    }

    return best_surface_y;
}

static std::wstring utf8_to_wide(const char *text)
{
    int wide_count;
    std::wstring result;

    if (text == NULL) {
        return L"";
    }

    wide_count = MultiByteToWideChar(CP_UTF8, 0, text, -1, NULL, 0);
    if (wide_count <= 1) {
        return L"";
    }

    result.resize((size_t)(wide_count - 1));
    MultiByteToWideChar(CP_UTF8, 0, text, -1, &result[0], wide_count);
    return result;
}

static std::wstring get_executable_directory(void)
{
    wchar_t buffer[MAX_PATH];
    DWORD length = GetModuleFileNameW(NULL, buffer, MAX_PATH);
    while (length > 0 && buffer[length - 1] != L'\\' && buffer[length - 1] != L'/') {
        --length;
    }
    buffer[length] = 0;
    return std::wstring(buffer);
}

static std::wstring get_current_directory_string(void)
{
    wchar_t buffer[MAX_PATH];
    DWORD length = GetCurrentDirectoryW(MAX_PATH, buffer);
    if (length == 0 || length >= MAX_PATH) {
        return L"";
    }
    return std::wstring(buffer);
}

static std::wstring join_path(const std::wstring &base, const std::wstring &tail)
{
    if (base.empty()) {
        return tail;
    }
    if (base[base.size() - 1] == L'\\' || base[base.size() - 1] == L'/') {
        return base + tail;
    }
    return base + L"\\" + tail;
}

static std::wstring resolve_relative_path(const wchar_t *relative_path)
{
    std::wstring exe_dir = get_executable_directory();
    std::wstring cwd = get_current_directory_string();
    std::wstring candidate_roots[4];
    int index;

    candidate_roots[0] = join_path(join_path(exe_dir, L".."), L"..");
    candidate_roots[1] = exe_dir;
    candidate_roots[2] = cwd;
    candidate_roots[3] = join_path(cwd, L"build");

    for (index = 0; index < 4; ++index) {
        std::wstring candidate = join_path(candidate_roots[index], relative_path);
        DWORD attributes = GetFileAttributesW(candidate.c_str());
        if (attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_DIRECTORY) == 0) {
            return candidate;
        }
    }

    return L"";
}

static Image *load_image_relative(const wchar_t *relative_path)
{
    std::wstring resolved = resolve_relative_path(relative_path);
    Image *image;

    if (resolved.empty()) {
        return NULL;
    }

    image = new Image(resolved.c_str());
    if (image != NULL && image->GetLastStatus() == Ok) {
        return image;
    }

    delete image;
    return NULL;
}

static void release_sheet(SpriteSheet *sheet)
{
    delete sheet->image;
    sheet->image = NULL;
    sheet->frame_width = 0;
    sheet->frame_height = 0;
    sheet->columns = 0;
    sheet->rows = 0;
}

static SpriteSheet load_sheet(const wchar_t *relative_path, UINT frame_width, UINT frame_height)
{
    SpriteSheet sheet = {};
    sheet.image = load_image_relative(relative_path);
    if (sheet.image != NULL && frame_width > 0 && frame_height > 0) {
        sheet.frame_width = frame_width;
        sheet.frame_height = frame_height;
        sheet.columns = sheet.image->GetWidth() / frame_width;
        sheet.rows = sheet.image->GetHeight() / frame_height;
    }
    return sheet;
}

static SpriteSheet load_quad_sheet(const wchar_t *relative_path)
{
    SpriteSheet sheet = {};
    sheet.image = load_image_relative(relative_path);
    if (sheet.image != NULL) {
        sheet.columns = 4;
        sheet.rows = 4;
        sheet.frame_width = sheet.image->GetWidth() / 4;
        sheet.frame_height = sheet.image->GetHeight() / 4;
    }
    return sheet;
}

static SpriteSheet load_strip_sheet(const wchar_t *relative_path, UINT columns)
{
    SpriteSheet sheet = {};
    sheet.image = load_image_relative(relative_path);
    if (sheet.image != NULL && columns > 0) {
        sheet.columns = columns;
        sheet.rows = 1;
        sheet.frame_width = sheet.image->GetWidth() / columns;
        sheet.frame_height = sheet.image->GetHeight();
    }
    return sheet;
}

static bool load_assets(Assets *assets)
{
    ZeroMemory(assets, sizeof(*assets));

    assets->backdrop_refuge = load_image_relative(L"aridfeihth\\production_raw\\spaces\\latchspire_refuge_backdrop.png");
    assets->backdrop_choir = load_image_relative(L"aridfeihth\\production_raw\\spaces\\choir_stair_backdrop.png");
    assets->backdrop_glasswind = load_image_relative(L"aridfeihth\\production_raw\\spaces\\glasswind_causeway_backdrop.png");
    assets->backdrop_ember = load_image_relative(L"aridfeihth\\production_raw\\spaces\\ember_nave_backdrop.png");
    assets->hud_pack = load_image_relative(L"aridfeihth\\production_raw\\interface\\aridfeihth_hud_pack.png");
    assets->field_handler = load_sheet(L"aridfeihth\\production_raw\\actors\\field_handler_sheet.png", 64u, 64u);
    assets->mirror_newt = load_quad_sheet(L"aridfeihth\\production_raw\\actors\\mirror_newt_sheet.png");
    assets->latch_spider = load_quad_sheet(L"aridfeihth\\production_raw\\actors\\latch_spider_sheet.png");
    assets->salt_ram = load_quad_sheet(L"aridfeihth\\production_raw\\actors\\salt_ram_sheet.png");
    assets->bond_weave = load_strip_sheet(L"aridfeihth\\production_raw\\effects\\bond_weave_fx.png", 8u);

    return assets->backdrop_refuge != NULL
        && assets->backdrop_choir != NULL
        && assets->backdrop_glasswind != NULL
        && assets->backdrop_ember != NULL
        && assets->hud_pack != NULL
        && assets->field_handler.image != NULL
        && assets->mirror_newt.image != NULL
        && assets->latch_spider.image != NULL
        && assets->salt_ram.image != NULL
        && assets->bond_weave.image != NULL;
}

static void unload_assets(Assets *assets)
{
    delete assets->backdrop_refuge;
    delete assets->backdrop_choir;
    delete assets->backdrop_glasswind;
    delete assets->backdrop_ember;
    delete assets->hud_pack;
    assets->backdrop_refuge = NULL;
    assets->backdrop_choir = NULL;
    assets->backdrop_glasswind = NULL;
    assets->backdrop_ember = NULL;
    assets->hud_pack = NULL;
    release_sheet(&assets->field_handler);
    release_sheet(&assets->mirror_newt);
    release_sheet(&assets->latch_spider);
    release_sheet(&assets->salt_ram);
    release_sheet(&assets->bond_weave);
}

static void load_xinput_runtime(XInputRuntime *runtime)
{
    const wchar_t *dlls[] = {L"xinput1_4.dll", L"xinput9_1_0.dll", L"xinput1_3.dll"};
    size_t index;

    ZeroMemory(runtime, sizeof(*runtime));

    for (index = 0; index < sizeof(dlls) / sizeof(dlls[0]); ++index) {
        runtime->module = LoadLibraryW(dlls[index]);
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

static void set_banner(const wchar_t *text)
{
    wcsncpy_s(g_demo.campaign.banner, sizeof(g_demo.campaign.banner) / sizeof(g_demo.campaign.banner[0]), text, _TRUNCATE);
    g_demo.campaign.banner_ms = 2400.0f;
}

static void stop_theme_loop(void)
{
    if (g_demo.audio.playing) {
        PlaySoundW(NULL, NULL, 0);
        g_demo.audio.playing = false;
    }
}

static void start_theme_loop(void)
{
    if (!g_demo.audio.available || g_demo.audio.muted || g_demo.smoke_mode || g_demo.audio.theme_path[0] == 0) {
        return;
    }

    g_demo.audio.playing = PlaySoundW(g_demo.audio.theme_path, NULL, SND_ASYNC | SND_FILENAME | SND_LOOP | SND_NODEFAULT) ? true : false;
}

static void init_audio(AudioState *audio)
{
    std::wstring resolved;

    ZeroMemory(audio, sizeof(*audio));
    resolved = resolve_relative_path(L"aridfeihth\\production_raw\\audio\\aridfeihth_theme_loop.wav");
    if (resolved.empty()) {
        return;
    }

    audio->available = true;
    wcsncpy_s(audio->theme_path, sizeof(audio->theme_path) / sizeof(audio->theme_path[0]), resolved.c_str(), _TRUNCATE);
    start_theme_loop();
}

static void toggle_theme_mute(void)
{
    if (!g_demo.audio.available) {
        set_banner(L"Theme loop asset not found.");
        return;
    }

    g_demo.audio.muted = !g_demo.audio.muted;
    if (g_demo.audio.muted) {
        stop_theme_loop();
        set_banner(L"Theme loop muted.");
    } else {
        start_theme_loop();
        set_banner(g_demo.audio.playing ? L"Theme loop live." : L"Theme loop failed to start.");
    }
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
    std::wstring room_name;

    if (room == NULL) {
        return;
    }

    g_demo.runtime.current_room = room;
    g_demo.campaign.player_x = from_right ? 1080.0f : 180.0f;
    g_demo.campaign.player_y = 0.0f;
    g_demo.campaign.velocity_y = 0.0f;
    g_demo.campaign.coyote_ms = kCoyoteTimeMs;
    g_demo.campaign.jump_buffer_ms = 0.0f;
    g_demo.campaign.room_time_ms = 0.0f;
    g_demo.campaign.airborne = false;

    room_name = utf8_to_wide(room->name);
    set_banner(room_name.c_str());
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
        set_banner(L"Ember Nave cleared. Salt Ram secured.");
    } else if (strcmp(room->id, "ashfall_dais") == 0) {
        set_banner(L"Ashfall Dais cleared. Prototype boss defeated.");
    } else {
        set_banner(L"Room pressure broken.");
    }
}

static const Image *pick_room_backdrop(const AridfeihthRoom *room)
{
    if (room == NULL) {
        return g_demo.assets.backdrop_refuge;
    }
    if (strcmp(room->id, "latchspire_refuge") == 0 || strcmp(room->id, "ropewalk_harbor") == 0 || strcmp(room->id, "skiff_berth") == 0) {
        return g_demo.assets.backdrop_refuge;
    }
    if (strcmp(room->scene_family, "choir") == 0) {
        return g_demo.assets.backdrop_choir;
    }
    if (strcmp(room->scene_family, "glasswind") == 0) {
        return g_demo.assets.backdrop_glasswind;
    }
    if (strcmp(room->scene_family, "ember") == 0) {
        return g_demo.assets.backdrop_ember;
    }
    if (strstr(room->id, "ashfall") != NULL || strstr(room->id, "gatehouse") != NULL || strstr(room->id, "drydock") != NULL) {
        return g_demo.assets.backdrop_ember;
    }
    return g_demo.assets.backdrop_refuge;
}

static void reset_campaign_state(void)
{
    ZeroMemory(&g_demo.campaign, sizeof(g_demo.campaign));
    g_demo.campaign.player_x = 220.0f;
    g_demo.campaign.coyote_ms = kCoyoteTimeMs;
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
    set_banner(L"Prototype pilgrimage underway.");
}

static void begin_ship_test(void)
{
    g_demo.ship.x = 640.0f;
    g_demo.ship.y = 360.0f;
    g_demo.ship.heading_deg = -90.0f;
    g_demo.ship.speed = 0.0f;
}

static void spawn_particle(float x, float y, float vx, float vy, float size, float life_ms, Color color, float rotation_deg, float spin_deg)
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

static void spawn_landing_burst(float x, float y, bool elevated)
{
    size_t index;

    for (index = 0; index < 10; ++index) {
        float direction = (float)index - 4.5f;
        spawn_particle(
            x + direction * 6.0f,
            y - 4.0f,
            direction * 24.0f,
            -70.0f - (float)(index % 4) * 18.0f,
            4.0f + (float)(index % 3),
            280.0f + (float)(index % 5) * 36.0f,
            elevated ? Color(200, 210, 176, 106) : Color(180, 156, 124, 92),
            direction * 8.0f,
            120.0f - (float)index * 12.0f);
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

    input.menu_up_pressed = g_key_pressed[VK_UP] || g_key_pressed['W'];
    input.menu_down_pressed = g_key_pressed[VK_DOWN] || g_key_pressed['S'];
    input.confirm_pressed = g_key_pressed[VK_RETURN] || g_key_pressed['J'];
    input.back_pressed = g_key_pressed[VK_ESCAPE] || g_key_pressed[VK_BACK];
    input.left_held = g_key_held[VK_LEFT] || g_key_held['A'];
    input.right_held = g_key_held[VK_RIGHT] || g_key_held['D'];
    input.up_held = g_key_held[VK_UP] || g_key_held['W'];
    input.down_held = g_key_held[VK_DOWN] || g_key_held['S'];
    input.run_held = g_key_held[VK_SHIFT] || g_key_held['K'];
    input.attack_pressed = g_key_pressed['Z'] || g_key_pressed['X'];
    input.interact_pressed = g_key_pressed['E'];
    input.jump_pressed = g_key_pressed[VK_SPACE];
    input.bond_pressed = g_key_pressed['V'];
    input.wind_pressed = g_key_pressed['C'];
    input.mute_pressed = g_key_pressed['M'];
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
        spawn_particle(
            g_demo.campaign.player_x,
            kGroundY - 70.0f + g_demo.campaign.player_y,
            cosf(radians) * 120.0f,
            sinf(radians) * 120.0f - 30.0f,
            6.0f + (float)(index % 3),
            600.0f + (float)(index % 5) * 35.0f,
            Color(220, 210, 176, 106),
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
        PostQuitMessage(0);
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
        spawn_particle(
            g_demo.ship.x - cosf(heading_radians) * 30.0f,
            g_demo.ship.y - sinf(heading_radians) * 30.0f,
            -cosf(heading_radians) * (90.0f + g_demo.ship.speed * 0.5f),
            -sinf(heading_radians) * (90.0f + g_demo.ship.speed * 0.5f),
            5.0f,
            450.0f,
            Color(170, 210, 176, 106),
            g_demo.ship.heading_deg,
            100.0f);
    }

    if (input->bond_pressed) {
        size_t index;
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
                Color(200, 210, 176, 106),
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
        set_banner(L"Mirror Newt rescued.");
        return;
    }
    if (strcmp(room->id, "mirror_cistern") == 0 && g_demo.campaign.mirror_newt && !g_demo.campaign.latch_spider) {
        g_demo.campaign.latch_spider = true;
        add_inventory_item("latch_spider");
        set_banner(L"Latch Spider freed from the cistern.");
        return;
    }
    if (strcmp(room->id, "munki_refractionary") == 0 && !g_demo.campaign.refraction_munki) {
        g_demo.campaign.refraction_munki = true;
        add_inventory_item("refraction_munki");
        g_demo.runtime.pet_tutorial_unlocked = true;
        set_banner(L"Refraction Munki bonded. Pet tutorial unlocked.");
        return;
    }
    if ((strstr(room->id, "harbor") != NULL || strstr(room->id, "skiff") != NULL || strstr(room->id, "quay") != NULL) && !g_demo.runtime.ship_mode_unlocked) {
        g_demo.runtime.ship_mode_unlocked = true;
        add_inventory_item("pirate_chart");
        set_banner(L"Ship Adventure Test marked on the title menu.");
        return;
    }
    if ((room->flags & ARIDFEIHTH_ROOM_FLAG_SAFE) != 0u) {
        set_banner(L"You regroup under the brass lamps.");
        return;
    }

    set_banner(L"Nothing new responds here yet.");
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
        set_banner(L"Pressure is mounting. Bond Weave will finish this room.");
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
        set_banner(L"Bond Weave rings out, but the room still holds.");
    }
}

static void try_room_transition(const AridfeihthRoomExit *exit_spec, bool from_right)
{
    std::wstring requirement_text;

    if (exit_spec == NULL || exit_spec->room_id == NULL) {
        return;
    }

    if (!can_use_exit(exit_spec)) {
        if (exit_spec->requires != NULL) {
            requirement_text = L"Route blocked until ";
            requirement_text += utf8_to_wide(exit_spec->requires);
            requirement_text += L" is secured.";
            set_banner(requirement_text.c_str());
        } else {
            set_banner(L"The route will not open until this room is settled.");
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
    float dt_seconds = dt_ms / 1000.0f;
    float foot_y = kGroundY + g_demo.campaign.player_y;
    float landing_surface_y = kGroundY;
    float landing_speed = 0.0f;
    bool landed = false;
    int room_index;

    if (input->back_pressed) {
        g_demo.scene = DEMO_SCENE_TITLE;
        return;
    }

    if (g_demo.campaign.coyote_ms > 0.0f) {
        g_demo.campaign.coyote_ms -= dt_ms;
        if (g_demo.campaign.coyote_ms < 0.0f) {
            g_demo.campaign.coyote_ms = 0.0f;
        }
    }
    if (g_demo.campaign.jump_buffer_ms > 0.0f) {
        g_demo.campaign.jump_buffer_ms -= dt_ms;
        if (g_demo.campaign.jump_buffer_ms < 0.0f) {
            g_demo.campaign.jump_buffer_ms = 0.0f;
        }
    }
    g_demo.campaign.room_time_ms += dt_ms;

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
        set_banner(g_demo.campaign.wind_kite ? L"Wind Kite engaged." : L"Wind Kite stowed.");
    }
    if (input->jump_pressed) {
        g_demo.campaign.jump_buffer_ms = kJumpBufferMs;
    }

    g_demo.campaign.player_x += movement * move_speed * dt_seconds;
    g_demo.campaign.player_x = clampf(g_demo.campaign.player_x, 96.0f, (float)kWindowWidth - 96.0f);

    if (movement < -0.1f) {
        g_demo.campaign.facing = -1;
    } else if (movement > 0.1f) {
        g_demo.campaign.facing = 1;
    }

    if (!g_demo.campaign.airborne) {
        float support_y;

        if (find_surface_near_feet(room, g_demo.campaign.player_x, foot_y, kSupportSnapTolerance, &support_y)) {
            foot_y = support_y;
            g_demo.campaign.player_y = support_y - kGroundY;
            g_demo.campaign.coyote_ms = kCoyoteTimeMs;
        } else {
            g_demo.campaign.airborne = true;
        }
    }

    if (g_demo.campaign.jump_buffer_ms > 0.0f && (!g_demo.campaign.airborne || g_demo.campaign.coyote_ms > 0.0f)) {
        g_demo.campaign.airborne = true;
        g_demo.campaign.velocity_y = kJumpVelocity;
        g_demo.campaign.jump_buffer_ms = 0.0f;
        g_demo.campaign.coyote_ms = 0.0f;
        set_override_clip(&kJumpClip);
    }

    if (g_demo.campaign.airborne) {
        float previous_foot_y = foot_y;

        g_demo.campaign.velocity_y += kGravityAccel * dt_seconds;
        foot_y += g_demo.campaign.velocity_y * dt_seconds;
        if (g_demo.campaign.velocity_y >= 0.0f && find_landing_surface(room, g_demo.campaign.player_x, previous_foot_y, foot_y, &landing_surface_y)) {
            landing_speed = g_demo.campaign.velocity_y;
            foot_y = landing_surface_y;
            g_demo.campaign.velocity_y = 0.0f;
            g_demo.campaign.airborne = false;
            g_demo.campaign.coyote_ms = kCoyoteTimeMs;
            landed = true;
        }
        g_demo.campaign.player_y = foot_y - kGroundY;
    } else {
        g_demo.campaign.velocity_y = 0.0f;
    }

    if (landed && landing_speed > 140.0f) {
        spawn_landing_burst(g_demo.campaign.player_x, landing_surface_y + 2.0f, landing_surface_y < kGroundY - 4.0f);
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

    if (input.mute_pressed) {
        toggle_theme_mute();
    }

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

static void render_ornament_field(Graphics *graphics, const RectF &bounds, int seed_base, int shape_count, BYTE min_alpha, BYTE max_alpha, float drift_scale)
{
    float t;
    float travel_x;
    float travel_y;
    float alpha_range;
    int index;

    if (graphics == NULL || shape_count <= 0 || bounds.Width < 12.0f || bounds.Height < 12.0f) {
        return;
    }

    t = (float)(GetTickCount64() % 100000ull) * 0.001f;
    travel_x = bounds.Width - 12.0f;
    travel_y = bounds.Height - 12.0f;
    alpha_range = (float)(max_alpha - min_alpha);
    if (travel_x < 0.0f) {
        travel_x = 0.0f;
    }
    if (travel_y < 0.0f) {
        travel_y = 0.0f;
    }

    for (index = 0; index < shape_count; ++index) {
        int seed = seed_base + index * 13;
        int style = seed & 3;
        float px = bounds.X + 6.0f + hash01(seed + 1) * travel_x;
        float py = bounds.Y + 6.0f + hash01(seed + 2) * travel_y;
        float size = 1.2f + hash01(seed + 3) * 4.8f;
        BYTE a = (BYTE)(min_alpha + hash01(seed + 4) * alpha_range);
        Color color = (style == 0) ? Color(a, 210, 176, 106)
            : (style == 1) ? Color(a, 92, 112, 132)
            : (style == 2) ? Color(a, 148, 84, 58)
            : Color(a, 34, 25, 21);

        px += sinf(t * 0.75f + (float)seed * 0.11f) * drift_scale;
        py += cosf(t * 0.68f + (float)seed * 0.08f) * drift_scale;

        if (style == 0) {
            SolidBrush brush(color);
            graphics->FillEllipse(&brush, px - size * 0.5f, py - size * 0.5f, size, size);
        } else if (style == 1) {
            SolidBrush brush(color);
            graphics->FillRectangle(&brush, px - size * 0.45f, py - size * 0.45f, size * 0.9f, size * 0.9f);
        } else if (style == 2) {
            Pen pen(color, 1.0f);
            graphics->DrawLine(&pen, px - size, py, px + size, py);
        } else {
            PointF diamond[4] = {
                PointF(px, py - size),
                PointF(px + size * 0.82f, py),
                PointF(px, py + size),
                PointF(px - size * 0.82f, py)
            };
            SolidBrush brush(color);
            graphics->FillPolygon(&brush, diamond, 4);
        }
    }
}

static void draw_image_alpha(Graphics *graphics, Image *image, const RectF &dest, const Rect &source, float alpha, float rotation_deg)
{
    ImageAttributes attributes;
    ColorMatrix matrix = {{
        {1.0f, 0.0f, 0.0f, 0.0f, 0.0f},
        {0.0f, 1.0f, 0.0f, 0.0f, 0.0f},
        {0.0f, 0.0f, 1.0f, 0.0f, 0.0f},
        {0.0f, 0.0f, 0.0f, alpha, 0.0f},
        {0.0f, 0.0f, 0.0f, 0.0f, 1.0f}
    }};
    GraphicsState state;

    if (graphics == NULL || image == NULL) {
        return;
    }

    attributes.SetColorMatrix(&matrix, ColorMatrixFlagsDefault, ColorAdjustTypeBitmap);
    state = graphics->Save();
    graphics->TranslateTransform(dest.X + dest.Width * 0.5f, dest.Y + dest.Height * 0.5f);
    if (rotation_deg != 0.0f) {
        graphics->RotateTransform(rotation_deg);
    }
    graphics->DrawImage(
        image,
        RectF(-dest.Width * 0.5f, -dest.Height * 0.5f, dest.Width, dest.Height),
        (REAL)source.X,
        (REAL)source.Y,
        (REAL)source.Width,
        (REAL)source.Height,
        UnitPixel,
        &attributes);
    graphics->Restore(state);

    if (alpha >= 0.35f && dest.Width >= 48.0f && dest.Height >= 48.0f) {
        int shape_count = (int)(dest.Width * dest.Height / 1800.0f);

        if (shape_count < 24) {
            shape_count = 24;
        }
        if (shape_count > 96) {
            shape_count = 96;
        }
        render_ornament_field(graphics, RectF(dest.X + 4.0f, dest.Y + 4.0f, dest.Width - 8.0f, dest.Height - 8.0f), 401 + source.X + source.Y, shape_count, 52, 112, 0.85f);
    }
}

static void draw_sprite(Graphics *graphics, const SpriteSheet *sheet, int row, int col, float x, float y, float scale, float alpha, float rotation_deg, bool flip_h)
{
    Rect source;
    RectF dest;
    ImageAttributes attributes;
    ColorMatrix matrix = {{
        {flip_h ? -1.0f : 1.0f, 0.0f, 0.0f, 0.0f, 0.0f},
        {0.0f, 1.0f, 0.0f, 0.0f, 0.0f},
        {0.0f, 0.0f, 1.0f, 0.0f, 0.0f},
        {0.0f, 0.0f, 0.0f, alpha, 0.0f},
        {flip_h ? 1.0f : 0.0f, 0.0f, 0.0f, 0.0f, 1.0f}
    }};
    GraphicsState state;

    if (graphics == NULL || sheet == NULL || sheet->image == NULL) {
        return;
    }
    if (sheet->columns == 0 || sheet->rows == 0) {
        return;
    }

    col = col % (int)sheet->columns;
    row = row % (int)sheet->rows;
    source.X = col * (int)sheet->frame_width;
    source.Y = row * (int)sheet->frame_height;
    source.Width = (int)sheet->frame_width;
    source.Height = (int)sheet->frame_height;
    dest = RectF(x - sheet->frame_width * scale * 0.5f, y - sheet->frame_height * scale, sheet->frame_width * scale, sheet->frame_height * scale);

    attributes.SetColorMatrix(&matrix, ColorMatrixFlagsDefault, ColorAdjustTypeBitmap);
    state = graphics->Save();
    graphics->TranslateTransform(dest.X + dest.Width * 0.5f, dest.Y + dest.Height * 0.5f);
    if (rotation_deg != 0.0f) {
        graphics->RotateTransform(rotation_deg);
    }
    graphics->DrawImage(
        sheet->image,
        RectF(-dest.Width * 0.5f, -dest.Height * 0.5f, dest.Width, dest.Height),
        (REAL)source.X,
        (REAL)source.Y,
        (REAL)source.Width,
        (REAL)source.Height,
        UnitPixel,
        &attributes);
    graphics->Restore(state);

    if (alpha >= 0.35f && dest.Width >= 40.0f && dest.Height >= 40.0f) {
        int shape_count = (int)(dest.Width * dest.Height / 450.0f);

        if (shape_count < 18) {
            shape_count = 18;
        }
        if (shape_count > 52) {
            shape_count = 52;
        }
        render_ornament_field(graphics, RectF(dest.X + 4.0f, dest.Y + 4.0f, dest.Width - 8.0f, dest.Height - 8.0f), row * 97 + col * 53 + (flip_h ? 7 : 0), shape_count, 48, 110, 0.62f);
    }
}

static void draw_shadowed_text(Graphics *graphics, const wchar_t *text, const RectF &rect, REAL size, FontStyle style, const Color &color, StringAlignment alignment)
{
    Font font(L"Segoe UI", size, style, UnitPixel);
    StringFormat format;
    SolidBrush shadow(Color(220, 8, 9, 11));
    SolidBrush brush(color);
    RectF shadow_rect = rect;

    format.SetAlignment(alignment);
    format.SetLineAlignment(StringAlignmentNear);
    format.SetFormatFlags(StringFormatFlagsNoClip);

    shadow_rect.X += 2.0f;
    shadow_rect.Y += 2.0f;
    graphics->DrawString(text, -1, &font, shadow_rect, &format, &shadow);
    graphics->DrawString(text, -1, &font, rect, &format, &brush);
}

static void render_particles(Graphics *graphics)
{
    size_t index;

    for (index = 0; index < sizeof(g_demo.particles) / sizeof(g_demo.particles[0]); ++index) {
        float alpha;
        BYTE a;
        SolidBrush brush(Color(255, 255, 255, 255));

        if (!g_demo.particles[index].active) {
            continue;
        }

        alpha = g_demo.particles[index].life_ms / g_demo.particles[index].max_life_ms;
        if (alpha < 0.0f) {
            alpha = 0.0f;
        }
        a = (BYTE)(alpha * (float)g_demo.particles[index].color.GetAlpha());
        brush.SetColor(Color(a, g_demo.particles[index].color.GetRed(), g_demo.particles[index].color.GetGreen(), g_demo.particles[index].color.GetBlue()));
        graphics->FillEllipse(&brush, g_demo.particles[index].x - g_demo.particles[index].size * 0.5f, g_demo.particles[index].y - g_demo.particles[index].size * 0.5f, g_demo.particles[index].size, g_demo.particles[index].size);
    }
}

static void render_platforms(Graphics *graphics, const AridfeihthRoom *room)
{
    size_t index;
    float time_s = g_demo.campaign.room_time_ms / 1000.0f;

    for (index = 0; index < sizeof(kPlatformSegments) / sizeof(kPlatformSegments[0]); ++index) {
        RectF deck;
        SolidBrush deck_fill(Color(230, 146, 104, 66));
        SolidBrush under_fill(Color(210, 72, 44, 35));
        SolidBrush rivet_fill(Color(220, 210, 176, 106));
        Pen outline(Color(255, 20, 18, 20), 2.0f);
        Pen brace_pen(Color(210, 99, 79, 56), 2.0f);
        Pen chain_pen(Color(216, 78, 60, 44), 2.0f);
        float top_y;
        float width;
        int link;
        int rivet;

        if (room == NULL || strcmp(kPlatformSegments[index].room_id, room->id) != 0) {
            continue;
        }

        top_y = platform_top_y(&kPlatformSegments[index]);
        width = kPlatformSegments[index].right_x - kPlatformSegments[index].left_x;
        deck = RectF(kPlatformSegments[index].left_x, top_y, width, kPlatformSegments[index].thickness);

        graphics->FillRectangle(&deck_fill, deck);
        graphics->DrawRectangle(&outline, deck.X, deck.Y, deck.Width, deck.Height);
        graphics->FillRectangle(&under_fill, deck.X + 10.0f, deck.Y + deck.Height, deck.Width - 20.0f, 14.0f);

        for (link = 0; link < 4; ++link) {
            float x = deck.X + deck.Width * (0.14f + (float)link * 0.24f);
            float anchor_y = deck.Y - 96.0f - (float)(link % 2) * 18.0f;
            float sway = sinf(time_s * (0.8f + (float)link * 0.18f) + kPlatformSegments[index].motion_phase) * (kPlatformSegments[index].motion_amplitude > 0.0f ? 9.0f : 4.0f);
            int chain_node;

            graphics->DrawLine(&chain_pen, x + sway * 0.2f, anchor_y, x, deck.Y);
            for (chain_node = 0; chain_node < 6; ++chain_node) {
                float chain_t = (float)chain_node / 5.0f;
                float chain_y = anchor_y + (deck.Y - anchor_y) * chain_t;
                graphics->DrawEllipse(&brace_pen, x - 2.5f + sway * 0.08f, chain_y - 4.0f, 5.0f, 8.0f);
            }
        }

        for (link = 0; link < 5; ++link) {
            float brace_x = deck.X + 18.0f + (deck.Width - 36.0f) * ((float)link / 4.0f);
            graphics->DrawLine(&brace_pen, brace_x, deck.Y + deck.Height, brace_x - 18.0f, deck.Y + deck.Height + 16.0f);
            graphics->DrawLine(&brace_pen, brace_x, deck.Y + deck.Height, brace_x + 18.0f, deck.Y + deck.Height + 16.0f);
        }

        for (rivet = 0; rivet < 12; ++rivet) {
            float rivet_x = deck.X + 14.0f + (deck.Width - 28.0f) * ((float)rivet / 11.0f);
            graphics->FillEllipse(&rivet_fill, rivet_x - 3.0f, deck.Y + 6.0f + (float)(rivet % 2) * 4.0f, 6.0f, 6.0f);
        }

        render_ornament_field(graphics, RectF(deck.X + 4.0f, deck.Y - 10.0f, deck.Width - 8.0f, deck.Height + 24.0f), 900 + (int)index * 131, 64, 60, 144, 0.7f);
    }
}

static void render_player_shadow(Graphics *graphics, const AridfeihthRoom *room, float foot_y)
{
    float shadow_y = find_projection_surface_y(room, g_demo.campaign.player_x, foot_y);
    float height_delta = shadow_y - foot_y;
    float shrink = clampf(height_delta / 180.0f, 0.0f, 1.0f);
    float width = 92.0f - shrink * 32.0f;
    float depth = 18.0f - shrink * 7.0f;
    BYTE alpha = (BYTE)(112.0f - shrink * 46.0f);
    SolidBrush shadow(Color(alpha, 10, 12, 16));

    graphics->FillEllipse(&shadow, g_demo.campaign.player_x - width * 0.5f, shadow_y - depth * 0.4f, width, depth);
}

static void render_campaign(Graphics *graphics)
{
    const AridfeihthRoom *room = g_demo.runtime.current_room;
    const Image *backdrop = pick_room_backdrop(room);
    Rect window_rect(0, 0, kWindowWidth, kWindowHeight);
    RectF info_box(28.0f, 584.0f, 1224.0f, 112.0f);
    SolidBrush info_brush(Color(176, 16, 23, 32));
    Pen info_pen(Color(220, 181, 150, 87), 2.0f);
    int room_index = room != NULL ? room_index_from_id(room->id) : -1;
    float player_foot_y = kGroundY + g_demo.campaign.player_y;

    graphics->SetInterpolationMode(InterpolationModeNearestNeighbor);
    graphics->SetPixelOffsetMode(PixelOffsetModeHalf);
    graphics->SetCompositingMode(CompositingModeSourceOver);
    graphics->Clear(Color(255, 17, 23, 32));
    if (backdrop != NULL) {
        graphics->DrawImage((Image *)backdrop, window_rect);
    }
    render_ornament_field(graphics, RectF(20.0f, 18.0f, (REAL)kWindowWidth - 40.0f, 520.0f), 1200, 640, 26, 60, 1.2f);

    if (room != NULL) {
        BYTE overlay_alpha = (BYTE)(room->danger * 18u);
        SolidBrush overlay(Color(overlay_alpha, 20, 8, 8));
        graphics->FillRectangle(&overlay, 0.0f, 0.0f, (REAL)kWindowWidth, (REAL)kWindowHeight);
    }

    render_platforms(graphics, room);
    render_player_shadow(graphics, room, player_foot_y);

    if (g_demo.campaign.bond_weave.active) {
        int fx_frame = (int)(g_demo.campaign.bond_weave.elapsed_ms / 110.0f) % (int)g_demo.assets.bond_weave.columns;
        float fx_alpha = 1.0f - (g_demo.campaign.bond_weave.elapsed_ms / g_demo.campaign.bond_weave.total_ms);
        draw_sprite(graphics, &g_demo.assets.bond_weave, 0, fx_frame, g_demo.campaign.player_x, kGroundY - 44.0f + g_demo.campaign.player_y, 3.5f, fx_alpha, g_demo.campaign.bond_weave.elapsed_ms * 0.22f, false);
    }

    if (g_demo.assets.field_handler.image != NULL && g_demo.campaign.clip != NULL) {
        const AnimationFrame *frame = &g_demo.campaign.clip->frames[g_demo.campaign.frame_index];
        draw_sprite(graphics, &g_demo.assets.field_handler, frame->row, frame->col, g_demo.campaign.player_x, kGroundY + g_demo.campaign.player_y, kPlayerScale, 1.0f, 0.0f, g_demo.campaign.facing < 0);
    }

    if (g_demo.campaign.mirror_newt) {
        draw_sprite(graphics, &g_demo.assets.mirror_newt, 0, (int)((GetTickCount64() / 160) % 4), g_demo.campaign.player_x - 96.0f, player_foot_y + 8.0f, 2.0f, 0.95f, 0.0f, false);
    }
    if (g_demo.campaign.latch_spider) {
        draw_sprite(graphics, &g_demo.assets.latch_spider, 0, (int)((GetTickCount64() / 200) % 4), g_demo.campaign.player_x + 112.0f, player_foot_y + 12.0f, 2.0f, 0.95f, 0.0f, false);
    }
    if (g_demo.campaign.salt_ram) {
        draw_sprite(graphics, &g_demo.assets.salt_ram, 0, (int)((GetTickCount64() / 180) % 4), g_demo.campaign.player_x + 184.0f, player_foot_y + 18.0f, 2.0f, 0.95f, 0.0f, false);
    }

    render_particles(graphics);

    if (g_demo.assets.hud_pack != NULL) {
        Rect hud_source(0, 0, (INT)g_demo.assets.hud_pack->GetWidth(), (INT)g_demo.assets.hud_pack->GetHeight());
        draw_image_alpha(graphics, g_demo.assets.hud_pack, RectF(22.0f, 18.0f, 640.0f, 160.0f), hud_source, 1.0f, 0.0f);
    }

    graphics->FillRectangle(&info_brush, info_box);
    graphics->DrawRectangle(&info_pen, info_box.X, info_box.Y, info_box.Width, info_box.Height);
    render_ornament_field(graphics, RectF(info_box.X + 6.0f, info_box.Y + 6.0f, info_box.Width - 12.0f, info_box.Height - 12.0f), 1700, 120, 42, 90, 0.6f);

    if (room != NULL) {
        std::wstring name = utf8_to_wide(room->name);
        std::wstring objective = utf8_to_wide(room->objective);
        draw_shadowed_text(graphics, name.c_str(), RectF(48.0f, 596.0f, 500.0f, 40.0f), 28.0f, FontStyleBold, Color(255, 210, 176, 106), StringAlignmentNear);
        draw_shadowed_text(graphics, objective.c_str(), RectF(48.0f, 634.0f, 1020.0f, 50.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentNear);
        if (room->alternate_right.room_id != NULL) {
            draw_shadowed_text(graphics, L"Hold Down at the east edge for the detour route.", RectF(826.0f, 600.0f, 390.0f, 28.0f), 18.0f, FontStyleRegular, Color(255, 210, 176, 106), StringAlignmentFar);
        }
        if (room_index >= 0 && !g_demo.campaign.room_cleared[room_index] && clear_threshold_for_room(room) > 0) {
            wchar_t pressure[96];
            swprintf_s(pressure, L"Room pressure: %d / %d", g_demo.campaign.room_damage[room_index], clear_threshold_for_room(room));
            draw_shadowed_text(graphics, pressure, RectF(874.0f, 634.0f, 330.0f, 28.0f), 18.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentFar);
        }
        if (room_has_platforms(room)) {
            draw_shadowed_text(graphics, L"Buffered jumps and platform catches are active in this room.", RectF(756.0f, 600.0f, 454.0f, 28.0f), 17.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentFar);
        }
    }

    if (g_demo.campaign.banner_ms > 0.0f) {
        float alpha = clampf(g_demo.campaign.banner_ms / 900.0f, 0.0f, 1.0f);
        SolidBrush banner_brush(Color((BYTE)(alpha * 180.0f), 11, 14, 18));
        Pen banner_pen(Color((BYTE)(alpha * 220.0f), 210, 176, 106), 2.0f);
        RectF banner_rect(320.0f, 194.0f, 640.0f, 54.0f);
        graphics->FillRectangle(&banner_brush, banner_rect);
        graphics->DrawRectangle(&banner_pen, banner_rect.X, banner_rect.Y, banner_rect.Width, banner_rect.Height);
        draw_shadowed_text(graphics, g_demo.campaign.banner, RectF(334.0f, 208.0f, 612.0f, 26.0f), 20.0f, FontStyleRegular, Color((BYTE)(alpha * 255.0f), 240, 232, 215), StringAlignmentCenter);
    }

    draw_shadowed_text(graphics, g_demo.audio.available ? (g_demo.audio.muted ? L"Theme: muted" : L"Theme: live") : L"Theme: unavailable", RectF(1020.0f, 28.0f, 220.0f, 24.0f), 16.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentFar);
    draw_shadowed_text(graphics, L"Move: Arrow keys / Left Stick  Attack: Z or X  Interact: E or Y  Jump: Space or A  Bond Weave: V or RB  M: mute  Esc: Title", RectF(20.0f, 688.0f, 1240.0f, 24.0f), 16.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentCenter);
}

static void render_ship_test(Graphics *graphics)
{
    LinearGradientBrush sky(Point(0, 0), Point(0, kWindowHeight), Color(255, 21, 24, 39), Color(255, 72, 53, 38));
    SolidBrush dune(Color(255, 63, 34, 24));
    SolidBrush deck(Color(255, 181, 150, 87));
    SolidBrush accent(Color(240, 210, 176, 106));
    SolidBrush body(Color(255, 94, 115, 140));
    SolidBrush canopy(Color(180, 33, 17, 20));
    Pen outline(Color(255, 15, 18, 22), 3.0f);
    PointF hull[4];
    PointF sail[3];
    GraphicsState state;

    graphics->SetSmoothingMode(SmoothingModeHighQuality);
    graphics->Clear(Color(255, 18, 20, 26));
    graphics->FillRectangle(&sky, 0.0f, 0.0f, (REAL)kWindowWidth, (REAL)kWindowHeight);
    graphics->FillEllipse(&dune, -180.0f, 520.0f, 820.0f, 260.0f);
    graphics->FillEllipse(&dune, 560.0f, 500.0f, 920.0f, 280.0f);
    graphics->FillRectangle(&deck, 0.0f, 592.0f, (REAL)kWindowWidth, 128.0f);
    render_ornament_field(graphics, RectF(34.0f, 30.0f, 1212.0f, 628.0f), 2200, 360, 28, 68, 0.9f);

    render_particles(graphics);

    state = graphics->Save();
    graphics->TranslateTransform(g_demo.ship.x, g_demo.ship.y);
    graphics->RotateTransform(g_demo.ship.heading_deg);

    hull[0] = PointF(-40.0f, 12.0f);
    hull[1] = PointF(0.0f, -22.0f);
    hull[2] = PointF(46.0f, 10.0f);
    hull[3] = PointF(0.0f, 28.0f);
    sail[0] = PointF(-2.0f, -14.0f);
    sail[1] = PointF(26.0f, -6.0f);
    sail[2] = PointF(4.0f, 10.0f);

    graphics->FillPolygon(&body, hull, 4);
    graphics->DrawPolygon(&outline, hull, 4);
    graphics->FillPolygon(&accent, sail, 3);
    graphics->DrawPolygon(&outline, sail, 3);
    graphics->FillEllipse(&canopy, -10.0f, -10.0f, 22.0f, 22.0f);

    graphics->Restore(state);
    render_ornament_field(graphics, RectF(g_demo.ship.x - 58.0f, g_demo.ship.y - 44.0f, 116.0f, 92.0f), 2600, 64, 58, 136, 0.55f);

    draw_shadowed_text(graphics, L"Ship Adventure Test", RectF(0.0f, 36.0f, (REAL)kWindowWidth, 40.0f), 34.0f, FontStyleBold, Color(255, 210, 176, 106), StringAlignmentCenter);
    draw_shadowed_text(graphics, L"This mode exists to prove the GDI+ path can already handle rotation, alpha, and particles without an engine swap.", RectF(120.0f, 88.0f, 1040.0f, 28.0f), 19.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentCenter);
    draw_shadowed_text(graphics, L"Turn: Left/Right or Stick  Thrust: Shift/A  Burst ring: V or RB  M: mute  Esc: Title", RectF(0.0f, 678.0f, (REAL)kWindowWidth, 24.0f), 17.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentCenter);
}

static void render_title(Graphics *graphics)
{
    size_t index;
    SolidBrush frame(Color(255, 14, 18, 24));
    SolidBrush card(Color(220, 11, 14, 18));
    Pen border(Color(255, 181, 150, 87), 2.0f);

    graphics->SetInterpolationMode(InterpolationModeNearestNeighbor);
    graphics->SetPixelOffsetMode(PixelOffsetModeHalf);
    graphics->Clear(Color(255, 14, 18, 24));
    if (g_demo.assets.backdrop_refuge != NULL) {
        graphics->DrawImage(g_demo.assets.backdrop_refuge, Rect(0, 0, kWindowWidth, kWindowHeight));
    }
    graphics->FillRectangle(&frame, 0.0f, 0.0f, (REAL)kWindowWidth, (REAL)kWindowHeight);
    render_ornament_field(graphics, RectF(32.0f, 24.0f, 1216.0f, 516.0f), 2800, 420, 24, 64, 1.0f);

    if (g_demo.assets.field_handler.image != NULL) {
        draw_sprite(graphics, &g_demo.assets.field_handler, 0, (int)((GetTickCount64() / 180) % 4), 220.0f, 540.0f, 3.4f, 1.0f, 0.0f, false);
    }
    if (g_demo.assets.mirror_newt.image != NULL) {
        draw_sprite(graphics, &g_demo.assets.mirror_newt, 0, (int)((GetTickCount64() / 220) % 4), 1010.0f, 562.0f, 3.0f, 0.92f, 0.0f, false);
    }

    draw_shadowed_text(graphics, L"Aridfeihth", RectF(0.0f, 66.0f, (REAL)kWindowWidth, 48.0f), 42.0f, FontStyleBold, Color(255, 210, 176, 106), StringAlignmentCenter);
    draw_shadowed_text(graphics, L"Ash-Reliquary GDI+ Runtime Pass", RectF(0.0f, 118.0f, (REAL)kWindowWidth, 28.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentCenter);
    draw_shadowed_text(graphics, L"70 ms in the animation data means one playback step lasts 0.07 seconds before the next sprite frame advances.", RectF(140.0f, 164.0f, 1000.0f, 28.0f), 18.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentCenter);

    for (index = 0; index < g_demo.package->title_option_count; ++index) {
        RectF row_rect(430.0f, 248.0f + (REAL)index * 62.0f, 420.0f, 46.0f);
        SolidBrush row_fill(index == (size_t)g_demo.title_index ? Color(220, 181, 150, 87) : Color(168, 11, 14, 18));
        Pen row_pen(index == (size_t)g_demo.title_index ? Color(255, 240, 232, 215) : Color(190, 94, 115, 140), 2.0f);
        std::wstring label = utf8_to_wide(g_demo.package->title_options[index]);
        graphics->FillRectangle(&row_fill, row_rect);
        graphics->DrawRectangle(&row_pen, row_rect.X, row_rect.Y, row_rect.Width, row_rect.Height);
        draw_shadowed_text(graphics, label.c_str(), RectF(row_rect.X, row_rect.Y + 10.0f, row_rect.Width, 24.0f), 22.0f, FontStyleBold, index == (size_t)g_demo.title_index ? Color(255, 11, 14, 18) : Color(255, 240, 232, 215), StringAlignmentCenter);
    }

    graphics->FillRectangle(&card, 370.0f, 520.0f, 540.0f, 112.0f);
    graphics->DrawRectangle(&border, 370.0f, 520.0f, 540.0f, 112.0f);
    render_ornament_field(graphics, RectF(382.0f, 532.0f, 516.0f, 88.0f), 3000, 96, 44, 92, 0.5f);
    draw_shadowed_text(graphics, L"Start Prototype enters the playable room route. Ship Adventure Test is the backend stress pass for transform-heavy 2D rendering.", RectF(392.0f, 542.0f, 496.0f, 54.0f), 18.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentCenter);
    draw_shadowed_text(graphics, L"Up/Down to choose, Enter to confirm, M to mute.", RectF(0.0f, 684.0f, (REAL)kWindowWidth, 22.0f), 17.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentCenter);
}

static void render_controls(Graphics *graphics)
{
    SolidBrush panel(Color(210, 11, 14, 18));
    Pen border(Color(255, 181, 150, 87), 2.0f);

    graphics->Clear(Color(255, 16, 20, 26));
    if (g_demo.assets.backdrop_choir != NULL) {
        graphics->DrawImage(g_demo.assets.backdrop_choir, Rect(0, 0, kWindowWidth, kWindowHeight));
    }
    graphics->FillRectangle(&panel, 140.0f, 96.0f, 1000.0f, 528.0f);
    graphics->DrawRectangle(&border, 140.0f, 96.0f, 1000.0f, 528.0f);
    render_ornament_field(graphics, RectF(156.0f, 110.0f, 968.0f, 500.0f), 3200, 180, 32, 84, 0.55f);

    draw_shadowed_text(graphics, L"Controls", RectF(0.0f, 124.0f, (REAL)kWindowWidth, 38.0f), 36.0f, FontStyleBold, Color(255, 210, 176, 106), StringAlignmentCenter);
    draw_shadowed_text(graphics, L"Campaign", RectF(184.0f, 202.0f, 160.0f, 28.0f), 26.0f, FontStyleBold, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"Left / Right or Stick: move between gates and rooms", RectF(184.0f, 242.0f, 900.0f, 24.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"Shift or LT: run", RectF(184.0f, 276.0f, 900.0f, 24.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"Z / X or X: attack and build room-break pressure", RectF(184.0f, 310.0f, 900.0f, 24.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"E or Y: rescue pets, rest, or unlock route interactions", RectF(184.0f, 344.0f, 900.0f, 24.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"Space or A: jump", RectF(184.0f, 378.0f, 900.0f, 24.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"V or RB: trigger Bond Weave, required for the Ember Nave finish", RectF(184.0f, 412.0f, 900.0f, 24.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"C or LB: toggle Wind Kite status for feedback  |  M: mute or restore the theme loop", RectF(184.0f, 446.0f, 900.0f, 24.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"At branch rooms, hold Down while exiting right to take the optional detour. Aerial rooms now use coyote time and jump buffering.", RectF(184.0f, 480.0f, 900.0f, 24.0f), 20.0f, FontStyleRegular, Color(255, 210, 176, 106), StringAlignmentNear);

    draw_shadowed_text(graphics, L"Ship Adventure Test", RectF(184.0f, 540.0f, 220.0f, 28.0f), 26.0f, FontStyleBold, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"Left / Right turns the craft. Shift / A thrusts. V / RB emits a particle burst.", RectF(184.0f, 578.0f, 860.0f, 24.0f), 20.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentNear);
    draw_shadowed_text(graphics, L"Esc or Enter returns to the title. M toggles the theme loop.", RectF(0.0f, 666.0f, (REAL)kWindowWidth, 22.0f), 18.0f, FontStyleRegular, Color(255, 240, 232, 215), StringAlignmentCenter);
}

static void render_demo(Graphics *graphics)
{
    switch (g_demo.scene) {
    case DEMO_SCENE_TITLE:
        render_title(graphics);
        break;
    case DEMO_SCENE_CONTROLS:
        render_controls(graphics);
        break;
    case DEMO_SCENE_SHIP_TEST:
        render_ship_test(graphics);
        break;
    case DEMO_SCENE_CAMPAIGN:
        render_campaign(graphics);
        break;
    default:
        break;
    }
}

static void paint_window(HDC hdc)
{
    Graphics buffer_graphics(g_demo.framebuffer);
    Graphics screen_graphics(hdc);

    render_demo(&buffer_graphics);
    screen_graphics.DrawImage(g_demo.framebuffer, 0, 0);
}

static LRESULT CALLBACK window_proc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam)
{
    switch (message) {
    case WM_ERASEBKGND:
        return 1;
    case WM_KEYDOWN:
        if (wparam < 256) {
            if (!g_key_held[wparam]) {
                g_key_pressed[wparam] = true;
            }
            g_key_held[wparam] = true;
        }
        return 0;
    case WM_KEYUP:
        if (wparam < 256) {
            g_key_held[wparam] = false;
        }
        return 0;
    case WM_PAINT:
        {
            PAINTSTRUCT paint;
            HDC hdc = BeginPaint(hwnd, &paint);
            paint_window(hdc);
            EndPaint(hwnd, &paint);
        }
        return 0;
    case WM_DESTROY:
        g_demo.running = false;
        PostQuitMessage(0);
        return 0;
    default:
        return DefWindowProcW(hwnd, message, wparam, lparam);
    }
}

static bool init_window(HINSTANCE instance)
{
    WNDCLASSW window_class = {};
    RECT rect = {0, 0, kWindowWidth, kWindowHeight};
    DWORD style = WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX;

    window_class.lpfnWndProc = window_proc;
    window_class.hInstance = instance;
    window_class.lpszClassName = kWindowClassName;
    window_class.hCursor = LoadCursorW(NULL, MAKEINTRESOURCEW(32512));
    window_class.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);

    if (!RegisterClassW(&window_class)) {
        return false;
    }

    AdjustWindowRect(&rect, style, FALSE);
    g_demo.window = CreateWindowW(
        kWindowClassName,
        kWindowTitle,
        style,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        rect.right - rect.left,
        rect.bottom - rect.top,
        NULL,
        NULL,
        instance,
        NULL);

    if (g_demo.window == NULL) {
        return false;
    }

    ShowWindow(g_demo.window, SW_SHOWDEFAULT);
    UpdateWindow(g_demo.window);
    return true;
}

static void shutdown_demo(void)
{
    stop_theme_loop();
    unload_xinput_runtime(&g_demo.xinput);
    unload_assets(&g_demo.assets);
    delete g_demo.framebuffer;
    g_demo.framebuffer = NULL;
    if (g_demo.gdiplus_token != 0) {
        GdiplusShutdown(g_demo.gdiplus_token);
        g_demo.gdiplus_token = 0;
    }
}

static bool init_demo(void)
{
    GdiplusStartupInput startup = {};
    startup.GdiplusVersion = 1;

    if (GdiplusStartup(&g_demo.gdiplus_token, &startup, NULL) != Ok) {
        return false;
    }

    g_demo.framebuffer = new Bitmap(kWindowWidth, kWindowHeight, PixelFormat32bppPARGB);
    if (g_demo.framebuffer == NULL) {
        return false;
    }

    if (!load_assets(&g_demo.assets)) {
        return false;
    }

    init_audio(&g_demo.audio);

    load_xinput_runtime(&g_demo.xinput);
    QueryPerformanceFrequency(&g_demo.perf_frequency);
    QueryPerformanceCounter(&g_demo.last_counter);

    g_demo.running = true;
    g_demo.scene = DEMO_SCENE_TITLE;
    g_demo.title_index = 0;
    boot_runtime();
    begin_ship_test();
    return true;
}

static int run_smoke_check(void)
{
    FILE *stream = NULL;
    AridfeihthRuntimeState smoke_runtime = g_demo.runtime;

    if (AttachConsole(ATTACH_PARENT_PROCESS)) {
        freopen_s(&stream, "CONOUT$", "w", stdout);
    }

    aridfeihth_start_prototype(&smoke_runtime);

    printf("smoke=ok\n");
    printf("package=%s\n", g_demo.package->metadata.title);
    printf("rooms=%lu\n", (unsigned long)g_demo.package->room_count);
    printf("player_moves=%lu\n", (unsigned long)g_demo.package->player_move_count);
    printf("field_handler_loaded=%d\n", g_demo.assets.field_handler.image != NULL ? 1 : 0);
    printf("hud_loaded=%d\n", g_demo.assets.hud_pack != NULL ? 1 : 0);
    printf("backdrop_loaded=%d\n", g_demo.assets.backdrop_refuge != NULL ? 1 : 0);
    printf("theme_loaded=%d\n", g_demo.audio.available ? 1 : 0);
    printf("start_room=%s\n", smoke_runtime.current_room != NULL ? smoke_runtime.current_room->id : "(null)");
    fflush(stdout);
    return 0;
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR command_line, int)
{
    MSG message;

    ZeroMemory(&g_demo, sizeof(g_demo));
    g_demo.smoke_mode = (command_line != NULL && wcsstr(command_line, L"--smoke") != NULL);

    if (!init_demo()) {
        MessageBoxW(NULL, L"Failed to initialize the Aridfeihth GDI+ runtime.", kWindowTitle, MB_ICONERROR | MB_OK);
        shutdown_demo();
        return 1;
    }

    if (g_demo.smoke_mode) {
        int result = run_smoke_check();
        shutdown_demo();
        return result;
    }

    if (!init_window(instance)) {
        MessageBoxW(NULL, L"Failed to create the Aridfeihth runtime window.", kWindowTitle, MB_ICONERROR | MB_OK);
        shutdown_demo();
        return 1;
    }

    while (g_demo.running) {
        while (PeekMessageW(&message, NULL, 0, 0, PM_REMOVE)) {
            if (message.message == WM_QUIT) {
                g_demo.running = false;
                break;
            }
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }

        if (g_demo.running) {
            LARGE_INTEGER now;
            float dt_ms;
            QueryPerformanceCounter(&now);
            dt_ms = (float)((double)(now.QuadPart - g_demo.last_counter.QuadPart) * 1000.0 / (double)g_demo.perf_frequency.QuadPart);
            g_demo.last_counter = now;
            dt_ms = clampf(dt_ms, 1.0f, 33.0f);
            update_demo(dt_ms);
            InvalidateRect(g_demo.window, NULL, FALSE);
            Sleep(1);
        }
    }

    shutdown_demo();
    return 0;
}