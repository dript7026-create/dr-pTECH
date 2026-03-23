#define NOMINMAX
#define WIN32_LEAN_AND_MEAN

#include <windows.h>
#include <objidl.h>
#ifndef PROPID
typedef ULONG PROPID;
#endif
#include <gdiplus.h>
#include <xinput.h>

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

#include <algorithm>

extern "C" {
#include "bango_engine_target/include/bango_ai_stack.h"
#include "bango_engine_target/include/bango_engine_target.h"
#include "bango_engine_target/include/bango_space_frame.h"
#include "bango_engine_target/include/bango_telemetry_bridge.h"
}

#ifndef _countof
#define _countof(array) (sizeof(array) / sizeof((array)[0]))
#endif

#pragma comment(lib, "gdiplus.lib")

using namespace Gdiplus;

struct Vec2 {
    float x;
    float y;
};

struct Vec3 {
    float x;
    float y;
    float z;
};

struct ScreenPoint {
    float x;
    float y;
    float depth;
    bool visible;
};

struct GameplayViewport {
    float left;
    float top;
    float width;
    float height;
};

struct CameraRig {
    Vec3 position;
    Vec3 forward;
    Vec3 right;
    Vec3 up;
    float focalLength;
    float panoramaWarp;
    float seamBlend;
    float motionBlurPixels;
    float pseudo3dBias;
};

struct PreviewTileDef {
    const char *name;
    int baseR;
    int baseG;
    int baseB;
    int accentR;
    int accentG;
    int accentB;
    const char *pattern;
};

struct PreviewPointLightDef {
    const char *name;
    float x;
    float y;
    float z;
    float r;
    float g;
    float b;
    float intensity;
    float radius;
};

struct PreviewObjectSpawnDef {
    const char *name;
    float x;
    float z;
    float halfX;
    float halfY;
    float halfZ;
    int interactive;
    int solid;
    int kind;
};

struct PreviewEnemySpawnDef {
    const char *name;
    float x;
    float z;
    float health;
    float speed;
    int kind;
};

struct PreviewBoneDef {
    const char *name;
    int parentIndex;
    float x;
    float y;
    float z;
};

struct PreviewSectionDef {
    const char *name;
    int boneIndex;
    float offsetX;
    float offsetY;
    float offsetZ;
    float halfX;
    float halfY;
    float halfZ;
    int r;
    int g;
    int b;
};

#include "generated/bango_test_level.h"
#include "generated/windows_preview/generated_bango_actor.h"

#define PREVIEW_WORLD_W BANGO_TEST_LEVEL_W
#define PREVIEW_WORLD_H BANGO_TEST_LEVEL_H
#define PREVIEW_OBJECT_COUNT BANGO_TEST_LEVEL_OBJECT_COUNT
#define PREVIEW_ENEMY_COUNT BANGO_TEST_LEVEL_ENEMY_COUNT
#define kPreviewCellSize g_bango_test_level_cell_size

static const float kPreviewPlayerSpawn[3] = {g_bango_test_spawn_x, 0.0f, g_bango_test_spawn_z};
static const float kPreviewGoalSlot[3] = {g_bango_test_goal_x, 0.0f, g_bango_test_goal_z};
static const float kPreviewObjectiveDrop[3] = {g_bango_test_goal_x, 0.0f, g_bango_test_goal_z - g_bango_test_level_cell_size * 2.0f};

static const PreviewPointLightDef kPreviewPointLights[] = {
    {"altar_slot", g_bango_test_goal_x, 2.6f, g_bango_test_goal_z, 1.00f, 0.82f, 0.46f, 1.55f, 10.5f},
    {"sewer_lantern_left", g_bango_test_level_origin_x + g_bango_test_level_cell_size * 7.0f, 2.1f, g_bango_test_level_origin_z + g_bango_test_level_cell_size * 11.0f, 0.48f, 0.86f, 0.75f, 0.90f, 7.0f},
    {"sewer_lantern_right", g_bango_test_level_origin_x + g_bango_test_level_cell_size * 17.0f, 2.1f, g_bango_test_level_origin_z + g_bango_test_level_cell_size * 17.0f, 0.55f, 0.72f, 0.95f, 0.82f, 7.4f},
    {"brazier", g_bango_test_level_origin_x + g_bango_test_level_cell_size * 7.0f, 1.7f, g_bango_test_level_origin_z + g_bango_test_level_cell_size * 16.0f, 1.00f, 0.48f, 0.18f, 0.95f, 6.2f},
};

enum { PREVIEW_POINT_LIGHT_COUNT = (int)_countof(kPreviewPointLights) };

enum ObjectKind {
    OBJECT_CRATE = 0,
    OBJECT_LIGHT = 1,
    OBJECT_SLOT = 2,
    OBJECT_CACHE = 3,
};

enum ClipKind {
    CLIP_IDLE,
    CLIP_LOCOMOTION,
    CLIP_ATTACK,
    CLIP_CARRY,
    CLIP_CELEBRATE,
    CLIP_HIT,
};

struct BonePoseTarget {
    float rotation;
    float offsetX;
    float offsetY;
};

struct BonePoseState {
    float rotation;
    float rotationVelocity;
    float offsetX;
    float offsetXVelocity;
    float offsetY;
    float offsetYVelocity;
    Vec3 worldPosition;
};

struct PreviewObject {
    const char *name;
    Vec3 position;
    Vec3 halfExtents;
    int interactive;
    int solid;
    int kind;
    int active;
    int toggled;
};

struct PreviewEnemy {
    const char *name;
    Vec3 position;
    Vec3 velocity;
    float health;
    float speed;
    int kind;
    int active;
    float cooldown;
    float hurtFlash;
};

struct XInputApi {
    HMODULE module;
    DWORD (WINAPI *getState)(DWORD, XINPUT_STATE *);
};

struct InputFrame {
    float moveX;
    float moveZ;
    float lookX;
    float lookY;
    int attackPressed;
    int dodgePressed;
    int interactPressed;
    int restartPressed;
    int specialWheelHeld;
};

struct GameState {
    ULONG_PTR gdiplusToken;
    HWND window;
    int keys[256];
    XInputApi xinput;
    XINPUT_STATE previousPad;
    int controllerConnected;
    Vec3 playerPosition;
    Vec3 playerVelocity;
    float playerFacingYaw;
    float playerHealth;
    float playerStamina;
    float playerMagic;
    float attackTimer;
    float dodgeTimer;
    float hitTimer;
    float cameraYaw;
    float cameraDistance;
    float cameraHeight;
    float cameraTurnVelocity;
    float clipTime;
    ClipKind clip;
    int clipLocked;
    int selectedMove;
    int enemiesAlive;
    int objectiveDropped;
    int objectiveHeld;
    int won;
    int lost;
    Vec3 objectivePosition;
    float objectiveSpin;
    PreviewObject objects[PREVIEW_OBJECT_COUNT];
    PreviewEnemy enemies[PREVIEW_ENEMY_COUNT];
    BonePoseState bones[PREVIEW_BANGO_BONE_COUNT];
    int bonePelvis;
    int boneSpine;
    int boneChest;
    int boneNeck;
    int boneHead;
    int boneArmL;
    int boneArmR;
    int boneHandL;
    int boneHandR;
    int boneLegL;
    int boneLegR;
    int boneFootL;
    int boneFootR;
    int boneHornL;
    int boneHornR;
    wchar_t statusLine[192];
    int statusTimer;
};

static GameState g_game = {};
static BangoEngineTargetState g_engine_target = {};
static BangoAIStackState g_ai_stack = {};
static BangoAICameraAdvisory g_ai_camera = {};
static BangoAISimulationAdvisory g_ai_simulation = {};
static BangoAIRenderAdvisory g_ai_render = {};
static BangoSpaceFrame g_space_frame = {};
static BangoTelemetryBridge g_telemetry_bridge = {};
static GameplayViewport g_viewport = {};
static CameraRig g_camera = {};
static const wchar_t *kWindowClass = L"BangoPatootTestWorld";
static const wchar_t *kWindowTitle = L"Bango-Patoot Test World";

static Vec3 vec3_make(float x, float y, float z)
{
    Vec3 value = {x, y, z};
    return value;
}

static Vec3 vec3_add(Vec3 a, Vec3 b)
{
    return vec3_make(a.x + b.x, a.y + b.y, a.z + b.z);
}

static Vec3 vec3_sub(Vec3 a, Vec3 b)
{
    return vec3_make(a.x - b.x, a.y - b.y, a.z - b.z);
}

static Vec3 vec3_scale(Vec3 value, float scalar)
{
    return vec3_make(value.x * scalar, value.y * scalar, value.z * scalar);
}

static float vec3_dot(Vec3 a, Vec3 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

static float vec3_length(Vec3 value)
{
    return sqrtf(vec3_dot(value, value));
}

static Vec3 vec3_normalize(Vec3 value)
{
    float length = vec3_length(value);
    if (length <= 0.0001f) {
        return vec3_make(0.0f, 1.0f, 0.0f);
    }
    return vec3_scale(value, 1.0f / length);
}

static Vec3 vec3_cross(Vec3 a, Vec3 b)
{
    return vec3_make(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x);
}

static float clampf(float value, float lo, float hi)
{
    if (value < lo) return lo;
    if (value > hi) return hi;
    return value;
}

static float lerpf(float a, float b, float t)
{
    return a + (b - a) * t;
}

static float wrap_radians(float angle)
{
    while (angle > 3.1415926535f) {
        angle -= 6.283185307f;
    }
    while (angle < -3.1415926535f) {
        angle += 6.283185307f;
    }
    return angle;
}

static Vec3 rotate_y(Vec3 value, float yaw)
{
    float s = sinf(yaw);
    float c = cosf(yaw);
    return vec3_make(value.x * c - value.z * s, value.y, value.x * s + value.z * c);
}

static Vec2 rotate_2d(Vec2 value, float angle)
{
    float radians = angle * 3.1415926535f / 180.0f;
    float s = sinf(radians);
    float c = cosf(radians);
    Vec2 result = {value.x * c - value.y * s, value.x * s + value.y * c};
    return result;
}

static int find_bone_index(const char *name)
{
    for (int i = 0; i < PREVIEW_BANGO_BONE_COUNT; ++i) {
        if (strcmp(kPreviewBangoBones[i].name, name) == 0) {
            return i;
        }
    }
    return -1;
}

static void set_status(const wchar_t *text)
{
    wcsncpy_s(g_game.statusLine, _countof(g_game.statusLine), text, _TRUNCATE);
    g_game.statusTimer = 240;
}

static float grid_height(int x, int z)
{
    x = std::max(0, std::min(PREVIEW_WORLD_W - 1, x));
    z = std::max(0, std::min(PREVIEW_WORLD_H - 1, z));
    return g_bango_test_level_heights[z * PREVIEW_WORLD_W + x];
}

static int grid_tile(int x, int z)
{
    x = std::max(0, std::min(PREVIEW_WORLD_W - 1, x));
    z = std::max(0, std::min(PREVIEW_WORLD_H - 1, z));
    return g_bango_test_level_tile_indices[z * PREVIEW_WORLD_W + x];
}

static int wrap_tile_sample(int value)
{
    int size = BANGO_TEST_TILE_SAMPLE_SIZE;
    value %= size;
    if (value < 0) {
        value += size;
    }
    return value;
}

static const RuntimeLandscapeTileDef &get_level_tile(int index)
{
    index = std::max(0, std::min(BANGO_TEST_TILE_COUNT - 1, index));
    return g_bango_test_tiles[index];
}

static Color sample_tile_albedo(const RuntimeLandscapeTileDef &tile, float u, float v)
{
    int sx = wrap_tile_sample((int)floorf(u * (float)BANGO_TEST_TILE_SAMPLE_SIZE));
    int sy = wrap_tile_sample((int)floorf(v * (float)BANGO_TEST_TILE_SAMPLE_SIZE));
    uint32_t packed = tile.albedo_samples[sy * BANGO_TEST_TILE_SAMPLE_SIZE + sx];
    return Color(255, (BYTE)((packed >> 24) & 0xFF), (BYTE)((packed >> 16) & 0xFF), (BYTE)((packed >> 8) & 0xFF));
}

static float sample_tile_height_relief(const RuntimeLandscapeTileDef &tile, float u, float v)
{
    int sx = wrap_tile_sample((int)floorf(u * (float)BANGO_TEST_TILE_SAMPLE_SIZE));
    int sy = wrap_tile_sample((int)floorf(v * (float)BANGO_TEST_TILE_SAMPLE_SIZE));
    return (float)tile.height_samples[sy * BANGO_TEST_TILE_SAMPLE_SIZE + sx] / 255.0f;
}

static float sample_height_world(float worldX, float worldZ)
{
    float gx = (worldX - g_bango_test_level_origin_x) / kPreviewCellSize;
    float gz = (worldZ - g_bango_test_level_origin_z) / kPreviewCellSize;
    int x0 = (int)floorf(gx);
    int z0 = (int)floorf(gz);
    int x1 = x0 + 1;
    int z1 = z0 + 1;
    float tx = gx - (float)x0;
    float tz = gz - (float)z0;
    float h00 = grid_height(x0, z0);
    float h10 = grid_height(x1, z0);
    float h01 = grid_height(x0, z1);
    float h11 = grid_height(x1, z1);
    float hx0 = lerpf(h00, h10, tx);
    float hx1 = lerpf(h01, h11, tx);
    return lerpf(hx0, hx1, tz);
}

static void reset_space_frame(void)
{
    float originX = g_bango_test_level_origin_x;
    float originZ = g_bango_test_level_origin_z;
    float sizeX = (float)(PREVIEW_WORLD_W - 1) * kPreviewCellSize;
    float sizeZ = (float)(PREVIEW_WORLD_H - 1) * kPreviewCellSize;
    float highest = 0.0f;
    for (int z = 0; z < PREVIEW_WORLD_H; ++z) {
        for (int x = 0; x < PREVIEW_WORLD_W; ++x) {
            highest = std::max(highest, grid_height(x, z));
        }
    }
    bango_space_frame_init(&g_space_frame, originX, 0.0f, originZ, sizeX, highest + 3.2f, sizeZ, 10, 6, 10);
}

static Vec3 sample_normal_world(float worldX, float worldZ)
{
    float step = 0.35f;
    float left = sample_height_world(worldX - step, worldZ);
    float right = sample_height_world(worldX + step, worldZ);
    float back = sample_height_world(worldX, worldZ - step);
    float front = sample_height_world(worldX, worldZ + step);
    return vec3_normalize(vec3_make(left - right, 2.0f * step, back - front));
}

static float sun_shadow(Vec3 point)
{
    Vec3 sunDir = vec3_normalize(vec3_make(-0.42f, 0.88f, -0.21f));
    Vec3 ray = point;
    for (int step = 1; step <= 14; ++step) {
        float t = (float)step * 1.15f;
        ray.x += -sunDir.x * t;
        ray.y += -sunDir.y * t;
        ray.z += -sunDir.z * t;
        if (ray.z < g_bango_test_level_origin_z || ray.z > g_bango_test_level_origin_z + PREVIEW_WORLD_H * kPreviewCellSize) {
            break;
        }
        if (sample_height_world(ray.x, ray.z) > ray.y - 0.05f) {
            return 0.42f;
        }
    }
    return 1.0f;
}

static Color shade_color(const PreviewTileDef &tile, Vec3 point, Vec3 normal, float emissive)
{
    Vec3 sunDir = vec3_normalize(vec3_make(-0.42f, 0.88f, -0.21f));
    float shadow = sun_shadow(vec3_add(point, vec3_make(0.0f, 0.04f, 0.0f)));
    float diffuse = std::max(0.0f, vec3_dot(normal, sunDir)) * shadow;
    float ambient = 0.23f;
    float red = (float)tile.baseR * (ambient + diffuse * 0.9f);
    float green = (float)tile.baseG * (ambient + diffuse * 0.9f);
    float blue = (float)tile.baseB * (ambient + diffuse * 0.9f);
    for (int i = 0; i < PREVIEW_POINT_LIGHT_COUNT; ++i) {
        Vec3 lightPos = vec3_make(kPreviewPointLights[i].x, kPreviewPointLights[i].y, kPreviewPointLights[i].z);
        Vec3 toLight = vec3_sub(lightPos, point);
        float dist = vec3_length(toLight);
        if (dist < kPreviewPointLights[i].radius) {
            Vec3 lightDir = vec3_normalize(toLight);
            float influence = (1.0f - dist / kPreviewPointLights[i].radius) * std::max(0.0f, vec3_dot(normal, lightDir)) * kPreviewPointLights[i].intensity * 0.5f;
            red += influence * 255.0f * kPreviewPointLights[i].r;
            green += influence * 255.0f * kPreviewPointLights[i].g;
            blue += influence * 255.0f * kPreviewPointLights[i].b;
        }
    }
    red += emissive * (float)tile.accentR;
    green += emissive * (float)tile.accentG;
    blue += emissive * (float)tile.accentB;
    return Color(255, (BYTE)clampf(red, 0.0f, 255.0f), (BYTE)clampf(green, 0.0f, 255.0f), (BYTE)clampf(blue, 0.0f, 255.0f));
}

static Color shade_tile_sample(const RuntimeLandscapeTileDef &tile, float u, float v, Vec3 point, Vec3 normal, float emissive)
{
    Vec3 sunDir = vec3_normalize(vec3_make(-0.42f, 0.88f, -0.21f));
    float shadow = sun_shadow(vec3_add(point, vec3_make(0.0f, 0.04f, 0.0f)));
    float diffuse = std::max(0.0f, vec3_dot(normal, sunDir)) * shadow;
    float ambient = 0.24f;
    Color albedo = sample_tile_albedo(tile, u, v);
    float relief = sample_tile_height_relief(tile, u, v);
    float red = (float)albedo.GetR() * (ambient + diffuse * 0.92f);
    float green = (float)albedo.GetG() * (ambient + diffuse * 0.92f);
    float blue = (float)albedo.GetB() * (ambient + diffuse * 0.92f);
    float highlight = (relief - 0.5f) * tile.relief_strength * 95.0f;
    for (int i = 0; i < PREVIEW_POINT_LIGHT_COUNT; ++i) {
        Vec3 lightPos = vec3_make(kPreviewPointLights[i].x, kPreviewPointLights[i].y, kPreviewPointLights[i].z);
        Vec3 toLight = vec3_sub(lightPos, point);
        float dist = vec3_length(toLight);
        if (dist < kPreviewPointLights[i].radius) {
            Vec3 lightDir = vec3_normalize(toLight);
            float influence = (1.0f - dist / kPreviewPointLights[i].radius) * std::max(0.0f, vec3_dot(normal, lightDir)) * kPreviewPointLights[i].intensity * 0.5f;
            red += influence * 255.0f * kPreviewPointLights[i].r;
            green += influence * 255.0f * kPreviewPointLights[i].g;
            blue += influence * 255.0f * kPreviewPointLights[i].b;
        }
    }
    red += highlight + emissive * (float)tile.accent_r;
    green += highlight * 0.78f + emissive * (float)tile.accent_g;
    blue += highlight * 0.62f + emissive * (float)tile.accent_b;
    return Color(255, (BYTE)clampf(red, 0.0f, 255.0f), (BYTE)clampf(green, 0.0f, 255.0f), (BYTE)clampf(blue, 0.0f, 255.0f));
}

static GameplayViewport build_gameplay_viewport(RECT rect)
{
    GameplayViewport viewport = {};
    float fullWidth = (float)(rect.right - rect.left);
    float fullHeight = (float)(rect.bottom - rect.top);
    float targetAspect = g_ai_render.gameplay_aspect_ratio > 0.01f ? g_ai_render.gameplay_aspect_ratio : 2.0f;
    viewport.width = fullWidth;
    viewport.height = viewport.width / targetAspect;
    if (viewport.height > fullHeight) {
        viewport.height = fullHeight;
        viewport.width = viewport.height * targetAspect;
    }
    viewport.left = ((fullWidth - viewport.width) * 0.5f);
    viewport.top = ((fullHeight - viewport.height) * 0.5f);
    return viewport;
}

static void prepare_camera_rig(void)
{
    Vec3 shoulderLocal = vec3_make(g_ai_camera.shoulder_side, g_game.cameraHeight + (g_ai_camera.shoulder_up - 1.62f), -g_game.cameraDistance);
    Vec3 focusLocal = vec3_make(g_ai_camera.focus_side, g_ai_camera.focus_up + (g_game.cameraHeight - 1.62f) * 0.85f, g_ai_camera.focus_forward);
    Vec3 worldUp = vec3_make(0.0f, 1.0f, 0.0f);
    Vec3 focus = vec3_add(g_game.playerPosition, rotate_y(focusLocal, g_game.playerFacingYaw));

    g_camera.position = vec3_add(g_game.playerPosition, rotate_y(shoulderLocal, g_game.cameraYaw));
    g_camera.forward = vec3_normalize(vec3_sub(focus, g_camera.position));
    g_camera.right = vec3_normalize(vec3_cross(worldUp, g_camera.forward));
    if (vec3_length(g_camera.right) < 0.001f) {
        g_camera.right = vec3_make(1.0f, 0.0f, 0.0f);
    }
    g_camera.up = vec3_normalize(vec3_cross(g_camera.forward, g_camera.right));
    g_camera.focalLength = g_viewport.width * (g_ai_camera.focal_length > 0.01f ? g_ai_camera.focal_length : 0.66f);
    g_camera.panoramaWarp = g_ai_camera.panorama_warp * g_ai_render.terrain_morph_strength;
    g_camera.seamBlend = g_ai_render.edge_stitch;
    g_camera.motionBlurPixels = clampf(g_game.cameraTurnVelocity * 0.10f, -1.0f, 1.0f) * g_ai_render.motion_blur_pixels;
    g_camera.pseudo3dBias = g_ai_camera.pseudo3d_bias;
}

static ScreenPoint project_world_point(Vec3 world, bool allowMorph = true)
{
    Vec3 rel = vec3_sub(world, g_camera.position);
    float viewX = vec3_dot(rel, g_camera.right);
    float viewY = vec3_dot(rel, g_camera.up);
    float viewZ = vec3_dot(rel, g_camera.forward);
    float fieldDisplacement = bango_space_frame_sample_displacement(&g_space_frame, world.x, world.y, world.z);
    ScreenPoint point;
    point.visible = viewZ > 0.22f;
    point.depth = viewZ;
    if (!point.visible) {
        point.x = g_viewport.left + g_viewport.width * 0.5f;
        point.y = g_viewport.top + g_viewport.height * 0.5f;
        return point;
    }

    float normalizedX = viewX / (viewZ + 0.001f);
    float normalizedY = (viewY + fieldDisplacement * 0.18f) / (viewZ + 0.001f);
    float screenX = g_viewport.left + g_viewport.width * 0.5f + normalizedX * g_camera.focalLength;
    float screenY = g_viewport.top + g_viewport.height * 0.58f - normalizedY * (g_camera.focalLength * 0.82f);
    if (allowMorph) {
        float turnInfluence = clampf(g_game.cameraTurnVelocity * 0.016f, -1.0f, 1.0f);
        float curvature = normalizedX * fabsf(normalizedX);
        float edgeBlend = clampf(fabsf(normalizedX), 0.0f, 1.0f);
        screenX += curvature * g_camera.panoramaWarp * 132.0f * turnInfluence;
        screenX += edgeBlend * g_camera.seamBlend * 18.0f * turnInfluence;
        screenX += fieldDisplacement * 16.0f * g_ai_render.terrain_morph_strength;
        screenY -= fabsf(curvature) * g_camera.pseudo3dBias * 22.0f;
        screenY -= fieldDisplacement * 12.0f * g_space_frame.metrics.gravity_focus;
    }
    point.x = screenX;
    point.y = screenY;
    return point;
}

static void fill_gradient_background(Graphics &graphics, int width, int height)
{
    float left = g_viewport.left;
    float top = g_viewport.top;
    for (int y = 0; y < height; ++y) {
        float t = (float)y / (float)std::max(1, height - 1);
        int red = (int)lerpf(18.0f, 8.0f, t);
        int green = (int)lerpf(28.0f, 14.0f, t);
        int blue = (int)lerpf(52.0f, 20.0f, t);
        if (t > 0.55f) {
            float glow = (t - 0.55f) / 0.45f;
            red = (int)clampf(red + glow * 50.0f, 0.0f, 255.0f);
            green = (int)clampf(green + glow * 22.0f, 0.0f, 255.0f);
            blue = (int)clampf(blue + glow * 6.0f, 0.0f, 255.0f);
        }
        Pen pen(Color(255, red, green, blue));
        graphics.DrawLine(&pen, left, top + (float)y, left + (float)width, top + (float)y);
    }
    SolidBrush haze(Color(70, 244, 184, 94));
    graphics.FillEllipse(&haze, left + width * 0.22f, top + height * 0.10f, width * 0.48f, height * 0.22f);
}

static void draw_horizon(Graphics &graphics)
{
    PointF farLand[10];
    PointF nearLand[10];
    float horizonY = g_viewport.top + g_viewport.height * (0.28f + (1.0f - g_ai_render.horizon_bias) * 0.10f);
    for (int i = 0; i < 10; ++i) {
        float t = (float)i / 9.0f;
        float x = g_viewport.left + t * g_viewport.width;
        float waveA = sinf(t * 8.0f + 0.35f) * g_viewport.height * 0.020f;
        float waveB = cosf(t * 4.0f + 0.7f) * g_viewport.height * 0.016f;
        farLand[i] = PointF(x, horizonY + waveA + waveB);
        nearLand[i] = PointF(x, horizonY + g_viewport.height * (0.06f + 0.02f * sinf(t * 5.5f + 0.4f)) + waveA * 0.55f);
    }
    SolidBrush farBrush(Color(205, 24, 30, 43));
    SolidBrush nearBrush(Color(220, 34, 40, 54));
    graphics.FillClosedCurve(&farBrush, farLand, 10);
    graphics.FillClosedCurve(&nearBrush, nearLand, 10);
    Pen ridge(Color(120, 88, 102, 118), 1.0f);
    graphics.DrawCurve(&ridge, nearLand, 10);
}

static void draw_polygon(Graphics &graphics, const PointF *points, int count, Color fillColor, Color lineColor)
{
    if (fabsf(g_camera.motionBlurPixels) > 0.25f) {
        PointF blurPoints[8];
        for (int i = 0; i < count && i < 8; ++i) {
            blurPoints[i] = PointF(points[i].X + g_camera.motionBlurPixels, points[i].Y + fabsf(g_camera.motionBlurPixels) * 0.10f);
        }
        SolidBrush blurFill(Color(52, fillColor.GetR(), fillColor.GetG(), fillColor.GetB()));
        graphics.FillPolygon(&blurFill, blurPoints, count);
    }
    SolidBrush fill(fillColor);
    Pen pen(lineColor, 1.0f);
    graphics.FillPolygon(&fill, points, count);
    graphics.DrawPolygon(&pen, points, count);
}

struct FaceInfo {
    PointF points[4];
    float depth;
    Vec3 normal;
};

static void draw_box(Graphics &graphics, Vec3 center, Vec3 half, float yaw, Color baseColor, float emissive)
{
    Vec3 corners[8];
    Vec3 local[8] = {
        vec3_make(-half.x, -half.y, -half.z), vec3_make(half.x, -half.y, -half.z), vec3_make(half.x, half.y, -half.z), vec3_make(-half.x, half.y, -half.z),
        vec3_make(-half.x, -half.y, half.z), vec3_make(half.x, -half.y, half.z), vec3_make(half.x, half.y, half.z), vec3_make(-half.x, half.y, half.z),
    };
    for (int i = 0; i < 8; ++i) {
        corners[i] = vec3_add(center, rotate_y(local[i], yaw));
    }

    const int faces[3][4] = {
        {3, 2, 6, 7},
        {1, 2, 6, 5},
        {4, 5, 6, 7},
    };
    FaceInfo info[3];
    for (int i = 0; i < 3; ++i) {
        Vec3 a = corners[faces[i][0]];
        Vec3 b = corners[faces[i][1]];
        Vec3 c = corners[faces[i][2]];
        Vec3 ab = vec3_sub(b, a);
        Vec3 ac = vec3_sub(c, a);
        info[i].normal = vec3_normalize(vec3_cross(ab, ac));
        info[i].depth = 0.0f;
        bool visible = true;
        for (int j = 0; j < 4; ++j) {
            ScreenPoint point = project_world_point(corners[faces[i][j]], true);
            if (!point.visible) {
                visible = false;
            }
            info[i].points[j] = PointF(point.x, point.y);
            info[i].depth += point.depth;
        }
        if (!visible) {
            info[i].depth = -1000.0f;
        }
    }
    std::sort(info, info + 3, [](const FaceInfo &a, const FaceInfo &b) { return a.depth > b.depth; });

    PreviewTileDef fauxTile = {"mesh", baseColor.GetR(), baseColor.GetG(), baseColor.GetB(), std::min(255, baseColor.GetR() + 40), std::min(255, baseColor.GetG() + 40), std::min(255, baseColor.GetB() + 30), "mesh"};
    for (int i = 0; i < 3; ++i) {
        if (info[i].depth <= 0.0f) {
            continue;
        }
        Color shaded = shade_color(fauxTile, center, info[i].normal, emissive);
        draw_polygon(graphics, info[i].points, 4, shaded, Color(120, 10, 10, 14));
    }
}

static void draw_terrain(Graphics &graphics)
{
    const int subDiv = 4;
    for (int z = PREVIEW_WORLD_H - 2; z >= 0; --z) {
        for (int x = 0; x < PREVIEW_WORLD_W - 1; ++x) {
            float x0 = g_bango_test_level_origin_x + (float)x * kPreviewCellSize;
            float x1 = g_bango_test_level_origin_x + (float)(x + 1) * kPreviewCellSize;
            float z0 = g_bango_test_level_origin_z + (float)z * kPreviewCellSize;
            float z1 = g_bango_test_level_origin_z + (float)(z + 1) * kPreviewCellSize;
            Vec3 p00 = vec3_make(x0, grid_height(x, z), z0);
            Vec3 p10 = vec3_make(x1, grid_height(x + 1, z), z0);
            Vec3 p01 = vec3_make(x0, grid_height(x, z + 1), z1);
            Vec3 p11 = vec3_make(x1, grid_height(x + 1, z + 1), z1);
            const RuntimeLandscapeTileDef &tile = get_level_tile(grid_tile(x, z));
            Vec3 cellNormal = vec3_normalize(vec3_cross(vec3_sub(p10, p00), vec3_sub(p01, p00)));
            for (int subZ = 0; subZ < subDiv; ++subZ) {
                for (int subX = 0; subX < subDiv; ++subX) {
                    float u0 = (float)subX / (float)subDiv;
                    float u1 = (float)(subX + 1) / (float)subDiv;
                    float v0 = (float)subZ / (float)subDiv;
                    float v1 = (float)(subZ + 1) / (float)subDiv;
                    float reliefScale = 0.22f + tile.relief_strength * 0.18f;
                    Vec3 q00 = vec3_make(lerpf(p00.x, p10.x, u0), lerpf(lerpf(p00.y, p10.y, u0), lerpf(p01.y, p11.y, u0), v0), lerpf(p00.z, p01.z, v0));
                    Vec3 q10 = vec3_make(lerpf(p00.x, p10.x, u1), lerpf(lerpf(p00.y, p10.y, u1), lerpf(p01.y, p11.y, u1), v0), lerpf(p00.z, p01.z, v0));
                    Vec3 q01 = vec3_make(lerpf(p00.x, p10.x, u0), lerpf(lerpf(p00.y, p10.y, u0), lerpf(p01.y, p11.y, u0), v1), lerpf(p00.z, p01.z, v1));
                    Vec3 q11 = vec3_make(lerpf(p00.x, p10.x, u1), lerpf(lerpf(p00.y, p10.y, u1), lerpf(p01.y, p11.y, u1), v1), lerpf(p00.z, p01.z, v1));
                    q00.y += (sample_tile_height_relief(tile, u0, v0) - 0.5f) * reliefScale;
                    q10.y += (sample_tile_height_relief(tile, u1, v0) - 0.5f) * reliefScale;
                    q01.y += (sample_tile_height_relief(tile, u0, v1) - 0.5f) * reliefScale;
                    q11.y += (sample_tile_height_relief(tile, u1, v1) - 0.5f) * reliefScale;
                    ScreenPoint s00 = project_world_point(q00, true);
                    ScreenPoint s10 = project_world_point(q10, true);
                    ScreenPoint s01 = project_world_point(q01, true);
                    ScreenPoint s11 = project_world_point(q11, true);
                    if (!s00.visible || !s10.visible || !s01.visible || !s11.visible) {
                        continue;
                    }
                    PointF triA[3] = {PointF(s00.x, s00.y), PointF(s10.x, s10.y), PointF(s11.x, s11.y)};
                    PointF triB[3] = {PointF(s00.x, s00.y), PointF(s11.x, s11.y), PointF(s01.x, s01.y)};
                    Vec3 center = vec3_make((q00.x + q11.x) * 0.5f, (q00.y + q10.y + q01.y + q11.y) * 0.25f, (q00.z + q11.z) * 0.5f);
                    Color shaded = shade_tile_sample(tile, (u0 + u1) * 0.5f, (v0 + v1) * 0.5f, center, cellNormal, 0.0f);
                    SolidBrush fill(shaded);
                    Pen pen(Color(80, tile.accent_r, tile.accent_g, tile.accent_b), 1.0f);
                    graphics.FillPolygon(&fill, triA, 3);
                    graphics.FillPolygon(&fill, triB, 3);
                    graphics.DrawPolygon(&pen, triA, 3);
                    graphics.DrawPolygon(&pen, triB, 3);
                }
            }
        }
    }
}

static void render_crate_prop(Graphics &graphics, const PreviewObject &object)
{
    Vec3 base = vec3_add(object.position, vec3_make(0.0f, object.halfExtents.y, 0.0f));
    draw_box(graphics, base, object.halfExtents, 0.0f, Color(255, 106, 98, 84), 0.02f);
    draw_box(graphics, vec3_add(base, vec3_make(0.0f, object.halfExtents.y * 0.35f, 0.0f)), vec3_make(object.halfExtents.x * 0.88f, object.halfExtents.y * 0.12f, object.halfExtents.z * 0.88f), 0.0f, Color(255, 138, 124, 96), 0.06f);
    draw_box(graphics, vec3_add(base, vec3_make(0.0f, 0.0f, 0.0f)), vec3_make(object.halfExtents.x * 0.15f, object.halfExtents.y * 0.92f, object.halfExtents.z * 1.02f), 0.0f, Color(255, 72, 62, 52), 0.0f);
    draw_box(graphics, vec3_add(base, vec3_make(0.0f, 0.0f, 0.0f)), vec3_make(object.halfExtents.x * 1.02f, object.halfExtents.y * 0.92f, object.halfExtents.z * 0.15f), 0.0f, Color(255, 72, 62, 52), 0.0f);
}

static void render_light_prop(Graphics &graphics, const PreviewObject &object)
{
    float glow = object.toggled ? 0.95f : 0.35f;
    Vec3 pole = vec3_add(object.position, vec3_make(0.0f, object.halfExtents.y * 0.95f, 0.0f));
    draw_box(graphics, pole, vec3_make(object.halfExtents.x * 0.22f, object.halfExtents.y * 1.15f, object.halfExtents.z * 0.22f), 0.0f, Color(255, 76, 88, 98), 0.02f);
    draw_box(graphics, vec3_add(pole, vec3_make(0.0f, object.halfExtents.y * 0.95f, 0.0f)), vec3_make(object.halfExtents.x * 0.95f, object.halfExtents.y * 0.18f, object.halfExtents.z * 0.95f), 0.0f, Color(255, 118, 96, 70), 0.08f);
    draw_box(graphics, vec3_add(pole, vec3_make(0.0f, object.halfExtents.y * 1.38f, 0.0f)), vec3_make(object.halfExtents.x * 0.48f, object.halfExtents.y * 0.38f, object.halfExtents.z * 0.48f), 0.0f, Color(255, 228, 176, 92), glow);
    draw_box(graphics, vec3_add(pole, vec3_make(0.0f, object.halfExtents.y * 1.82f, 0.0f)), vec3_make(object.halfExtents.x * 0.22f, object.halfExtents.y * 0.12f, object.halfExtents.z * 0.22f), 0.0f, Color(255, 90, 74, 56), 0.02f);
}

static void render_slot_prop(Graphics &graphics, const PreviewObject &object)
{
    float charge = g_game.objectiveHeld ? 0.62f : 0.18f;
    Vec3 dais = vec3_add(object.position, vec3_make(0.0f, object.halfExtents.y * 0.78f, 0.0f));
    draw_box(graphics, dais, vec3_make(object.halfExtents.x * 1.05f, object.halfExtents.y * 0.78f, object.halfExtents.z * 1.05f), 0.0f, Color(255, 124, 92, 54), 0.04f);
    draw_box(graphics, vec3_add(dais, vec3_make(0.0f, object.halfExtents.y * 0.58f, 0.0f)), vec3_make(object.halfExtents.x * 0.56f, object.halfExtents.y * 0.15f, object.halfExtents.z * 0.56f), 0.0f, Color(255, 198, 164, 86), charge);
    draw_box(graphics, vec3_add(dais, vec3_make(0.0f, object.halfExtents.y * 0.84f, 0.0f)), vec3_make(object.halfExtents.x * 0.28f, object.halfExtents.y * 0.18f, object.halfExtents.z * 0.28f), g_game.objectiveSpin, Color(255, 238, 214, 118), charge + 0.18f);
}

static void render_cache_prop(Graphics &graphics, const PreviewObject &object)
{
    Vec3 core = vec3_add(object.position, vec3_make(0.0f, object.halfExtents.y, 0.0f));
    draw_box(graphics, core, vec3_make(object.halfExtents.x * 0.82f, object.halfExtents.y * 0.95f, object.halfExtents.z * 0.82f), 0.0f, Color(255, 82, 118, 88), 0.04f);
    draw_box(graphics, vec3_add(core, vec3_make(0.0f, object.halfExtents.y * 0.55f, 0.0f)), vec3_make(object.halfExtents.x * 0.58f, object.halfExtents.y * 0.16f, object.halfExtents.z * 0.58f), 0.0f, Color(255, 148, 178, 120), 0.10f);
    draw_box(graphics, vec3_add(core, vec3_make(-object.halfExtents.x * 0.72f, 0.0f, 0.0f)), vec3_make(object.halfExtents.x * 0.14f, object.halfExtents.y * 0.62f, object.halfExtents.z * 0.94f), 0.0f, Color(255, 60, 82, 66), 0.0f);
    draw_box(graphics, vec3_add(core, vec3_make(object.halfExtents.x * 0.72f, 0.0f, 0.0f)), vec3_make(object.halfExtents.x * 0.14f, object.halfExtents.y * 0.62f, object.halfExtents.z * 0.94f), 0.0f, Color(255, 60, 82, 66), 0.0f);
}

static void render_object(Graphics &graphics, const PreviewObject &object)
{
    if (!object.active) {
        return;
    }
    if (object.kind == OBJECT_LIGHT) {
        render_light_prop(graphics, object);
    } else if (object.kind == OBJECT_SLOT) {
        render_slot_prop(graphics, object);
    } else if (object.kind == OBJECT_CACHE) {
        render_cache_prop(graphics, object);
    } else {
        render_crate_prop(graphics, object);
    }
}

static void render_enemy(Graphics &graphics, const PreviewEnemy &enemy)
{
    if (!enemy.active) {
        return;
    }
    Color color = enemy.kind == 2 ? Color(255, 148, 66, 86) : enemy.kind == 1 ? Color(255, 128, 82, 120) : Color(255, 110, 78, 102);
    draw_box(graphics, vec3_add(enemy.position, vec3_make(0.0f, 0.8f, 0.0f)), vec3_make(0.42f, 0.82f, 0.35f), 0.0f, color, enemy.hurtFlash > 0.0f ? 0.35f : 0.0f);
}

static void build_pose_targets(ClipKind clip, float clipTime, BonePoseTarget *targets)
{
    for (int i = 0; i < PREVIEW_BANGO_BONE_COUNT; ++i) {
        targets[i].rotation = 0.0f;
        targets[i].offsetX = 0.0f;
        targets[i].offsetY = 0.0f;
    }

    float phase = clipTime * 4.0f;
    if (clip == CLIP_IDLE) {
        float breath = sinf(phase * 0.7f) * 4.0f;
        targets[g_game.boneSpine].rotation = breath;
        targets[g_game.boneHead].rotation = -breath * 0.4f;
        targets[g_game.boneArmL].rotation = -6.0f + sinf(phase) * 4.0f;
        targets[g_game.boneArmR].rotation = 6.0f - sinf(phase) * 4.0f;
    } else if (clip == CLIP_LOCOMOTION) {
        float stride = sinf(phase * 1.6f);
        float bounce = fabsf(cosf(phase * 1.6f)) * 0.08f;
        targets[g_game.boneLegL].rotation = stride * 24.0f;
        targets[g_game.boneLegR].rotation = -stride * 24.0f;
        targets[g_game.boneArmL].rotation = -stride * 20.0f;
        targets[g_game.boneArmR].rotation = stride * 20.0f;
        targets[g_game.boneSpine].rotation = stride * 6.0f;
        targets[g_game.bonePelvis].offsetY = bounce;
    } else if (clip == CLIP_ATTACK) {
        float t = clampf(clipTime / 0.42f, 0.0f, 1.0f);
        float windup = t < 0.45f ? t / 0.45f : (1.0f - t) / 0.55f;
        targets[g_game.boneSpine].rotation = lerpf(0.0f, 12.0f, windup);
        targets[g_game.boneHead].rotation = lerpf(0.0f, 9.0f, windup);
        targets[g_game.boneArmL].rotation = lerpf(0.0f, -25.0f, windup);
        targets[g_game.boneArmR].rotation = lerpf(0.0f, 38.0f, windup);
        targets[g_game.boneLegL].rotation = lerpf(0.0f, 15.0f, windup);
        targets[g_game.boneLegR].rotation = lerpf(0.0f, -20.0f, windup);
        targets[g_game.bonePelvis].offsetY = t > 0.5f ? -0.06f : 0.03f;
    } else if (clip == CLIP_CARRY) {
        targets[g_game.boneArmL].rotation = -34.0f;
        targets[g_game.boneArmR].rotation = 34.0f;
        targets[g_game.boneArmL].offsetY = 0.12f;
        targets[g_game.boneArmR].offsetY = 0.12f;
        targets[g_game.boneSpine].rotation = 4.0f;
    } else if (clip == CLIP_CELEBRATE) {
        float cheer = sinf(phase * 2.2f);
        targets[g_game.boneArmL].rotation = -60.0f + cheer * 10.0f;
        targets[g_game.boneArmR].rotation = 60.0f - cheer * 10.0f;
        targets[g_game.boneHead].rotation = 9.0f;
        targets[g_game.bonePelvis].offsetY = fabsf(cheer) * 0.12f;
    } else if (clip == CLIP_HIT) {
        targets[g_game.boneSpine].rotation = -14.0f;
        targets[g_game.boneHead].rotation = -10.0f;
        targets[g_game.boneArmL].rotation = -16.0f;
        targets[g_game.boneArmR].rotation = 18.0f;
        targets[g_game.bonePelvis].offsetY = -0.1f;
    }
}

static void update_bango_pose(float dt)
{
    BonePoseTarget targets[PREVIEW_BANGO_BONE_COUNT];
    build_pose_targets(g_game.clip, g_game.clipTime, targets);
    for (int i = 0; i < PREVIEW_BANGO_BONE_COUNT; ++i) {
        float stiffness = g_ai_simulation.animation_stiffness > 0.0f ? g_ai_simulation.animation_stiffness : 16.0f;
        float damping = g_ai_simulation.animation_damping > 0.0f ? g_ai_simulation.animation_damping : 9.0f;
        float deltaRot = targets[i].rotation - g_game.bones[i].rotation;
        g_game.bones[i].rotationVelocity += deltaRot * stiffness * dt;
        g_game.bones[i].rotationVelocity *= expf(-damping * dt);
        g_game.bones[i].rotation += g_game.bones[i].rotationVelocity * dt;

        float deltaX = targets[i].offsetX - g_game.bones[i].offsetX;
        g_game.bones[i].offsetXVelocity += deltaX * stiffness * dt;
        g_game.bones[i].offsetXVelocity *= expf(-damping * dt);
        g_game.bones[i].offsetX += g_game.bones[i].offsetXVelocity * dt;

        float deltaY = targets[i].offsetY - g_game.bones[i].offsetY;
        g_game.bones[i].offsetYVelocity += deltaY * stiffness * dt;
        g_game.bones[i].offsetYVelocity *= expf(-damping * dt);
        g_game.bones[i].offsetY += g_game.bones[i].offsetYVelocity * dt;
    }

    for (int i = 0; i < PREVIEW_BANGO_BONE_COUNT; ++i) {
        Vec2 local2 = {(kPreviewBangoBones[i].x / 18.0f) + g_game.bones[i].offsetX, (kPreviewBangoBones[i].y / 18.0f) + g_game.bones[i].offsetY};
        Vec2 rotated2 = rotate_2d(local2, g_game.bones[i].rotation);
        Vec3 local3 = rotate_y(vec3_make(rotated2.x, rotated2.y + 1.1f, 0.0f), g_game.playerFacingYaw);
        g_game.bones[i].worldPosition = vec3_add(g_game.playerPosition, local3);
    }
}

static void render_bango(Graphics &graphics)
{
    for (int i = 0; i < PREVIEW_BANGO_SECTION_COUNT; ++i) {
        const PreviewSectionDef &section = kPreviewBangoSections[i];
        Vec3 anchor = g_game.bones[section.boneIndex].worldPosition;
        Vec3 localOffset = rotate_y(vec3_make(section.offsetX, section.offsetY, section.offsetZ), g_game.playerFacingYaw);
        Vec3 center = vec3_add(anchor, localOffset);
        Color color(255, section.r, section.g, section.b);
        draw_box(graphics, center, vec3_make(section.halfX, section.halfY, section.halfZ), g_game.playerFacingYaw, color, 0.05f);
    }
}

static void render_patoot(Graphics &graphics)
{
    float bob = sinf(g_game.clipTime * 4.2f) * 0.12f;
    Vec3 center = vec3_add(g_game.playerPosition, rotate_y(vec3_make(0.85f, 1.5f + bob, -0.75f), g_game.playerFacingYaw));
    draw_box(graphics, center, vec3_make(0.25f, 0.18f, 0.18f), g_game.playerFacingYaw, Color(255, 230, 212, 146), 0.1f);
    draw_box(graphics, vec3_add(center, rotate_y(vec3_make(-0.28f, 0.0f, 0.0f), g_game.playerFacingYaw)), vec3_make(0.17f, 0.05f, 0.14f), g_game.playerFacingYaw, Color(255, 192, 164, 92), 0.05f);
    draw_box(graphics, vec3_add(center, rotate_y(vec3_make(0.28f, 0.0f, 0.0f), g_game.playerFacingYaw)), vec3_make(0.17f, 0.05f, 0.14f), g_game.playerFacingYaw, Color(255, 192, 164, 92), 0.05f);
}

static void render_objective(Graphics &graphics)
{
    if (!g_game.objectiveDropped || g_game.objectiveHeld || g_game.won) {
        return;
    }
    Vec3 position = vec3_add(g_game.objectivePosition, vec3_make(0.0f, 0.6f + sinf(g_game.objectiveSpin * 2.0f) * 0.15f, 0.0f));
    draw_box(graphics, position, vec3_make(0.22f, 0.22f, 0.22f), g_game.objectiveSpin, Color(255, 240, 204, 92), 0.55f);
}

static void draw_hud(HDC hdc, RECT rect)
{
    wchar_t buffer[256];
    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, RGB(240, 232, 210));
    swprintf_s(buffer, L"Bango-Patoot Test World  HP %.0f  ST %.0f  MA %.0f  Enemies %d  Move %d", g_game.playerHealth, g_game.playerStamina, g_game.playerMagic, g_game.enemiesAlive, g_game.selectedMove + 1);
    TextOutW(hdc, 18, 18, buffer, (int)wcslen(buffer));
    swprintf_s(buffer, L"Objective: %ls", g_game.won ? L"Win triggered" : g_game.objectiveHeld ? L"Carry relic to slot altar" : g_game.objectiveDropped ? L"Recover dropped relic" : L"Defeat all enemies");
    TextOutW(hdc, 18, 42, buffer, (int)wcslen(buffer));
    swprintf_s(buffer, L"Space frame  Dist %.2f  Press %.2f  Pore %.2f  Grav %.2f", g_space_frame.metrics.disturbance, g_space_frame.metrics.pressure_density, g_space_frame.metrics.pore_flux, g_space_frame.metrics.gravity_focus);
    TextOutW(hdc, 18, 66, buffer, (int)wcslen(buffer));
    TextOutW(hdc, 18, rect.bottom - 64, L"Controls: WASD or left stick move | right stick camera | Space/X attack | Shift/B dodge | E/A interact | LT+right stick move wheel | R/Menu restart | Esc quit", 164);
    TextOutW(hdc, 18, rect.bottom - 88, L"Camera: over-right-shoulder 2:1 gameplay frame | terrain morph + blur active on camera turns", 96);
    if (g_game.statusTimer > 0) {
        SetTextColor(hdc, RGB(255, 214, 164));
        TextOutW(hdc, 18, rect.bottom - 36, g_game.statusLine, (int)wcslen(g_game.statusLine));
    }
}

static void init_xinput(void)
{
    const wchar_t *candidates[] = {L"xinput1_4.dll", L"xinput1_3.dll", L"xinput9_1_0.dll"};
    for (int i = 0; i < 3; ++i) {
        HMODULE module = LoadLibraryW(candidates[i]);
        if (module) {
            g_game.xinput.module = module;
            g_game.xinput.getState = (DWORD (WINAPI *)(DWORD, XINPUT_STATE *))GetProcAddress(module, "XInputGetState");
            if (g_game.xinput.getState) {
                return;
            }
            FreeLibrary(module);
        }
    }
}

static InputFrame poll_input(void)
{
    InputFrame input = {};
    unsigned int engineHeld = 0;
    unsigned int enginePressed = 0;
    if (g_game.keys['A']) input.moveX -= 1.0f;
    if (g_game.keys['D']) input.moveX += 1.0f;
    if (g_game.keys['W']) input.moveZ += 1.0f;
    if (g_game.keys['S']) input.moveZ -= 1.0f;

    bango_engine_target_begin_frame(&g_engine_target);

    if (g_game.xinput.getState) {
        XINPUT_STATE state = {};
        DWORD result = g_game.xinput.getState(0, &state);
        g_game.controllerConnected = (result == ERROR_SUCCESS);
        if (g_game.controllerConnected) {
            float lx = (float)state.Gamepad.sThumbLX / 32767.0f;
            float ly = (float)state.Gamepad.sThumbLY / 32767.0f;
            float rx = (float)state.Gamepad.sThumbRX / 32767.0f;
            float ry = (float)state.Gamepad.sThumbRY / 32767.0f;
            if (fabsf(lx) > 0.18f) input.moveX += lx;
            if (fabsf(ly) > 0.18f) input.moveZ += ly;
            if (fabsf(rx) > 0.18f) input.lookX = rx;
            if (fabsf(ry) > 0.18f) input.lookY = ry;
            WORD changed = state.Gamepad.wButtons & ~g_game.previousPad.Gamepad.wButtons;
            input.attackPressed = (changed & XINPUT_GAMEPAD_X) != 0;
            input.dodgePressed = (changed & XINPUT_GAMEPAD_B) != 0;
            input.interactPressed = (changed & XINPUT_GAMEPAD_A) != 0;
            input.restartPressed = (changed & XINPUT_GAMEPAD_START) != 0;
            input.specialWheelHeld = state.Gamepad.bLeftTrigger > 48;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_LEFT_SHOULDER) engineHeld |= BANGO_BTN_ATTACK_LIGHT;
            if (state.Gamepad.bRightTrigger > 48) engineHeld |= BANGO_BTN_ATTACK_HEAVY;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_B) engineHeld |= BANGO_BTN_JUMP | BANGO_BTN_SPRINT;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_A) engineHeld |= BANGO_BTN_CROUCH_SLIDE;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_X) engineHeld |= BANGO_BTN_HEAL;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_Y) engineHeld |= BANGO_BTN_INTERACT_MASS;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_RIGHT_SHOULDER) engineHeld |= BANGO_BTN_FOCUS_LOCK;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_LEFT_THUMB) engineHeld |= BANGO_BTN_BLOCK;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_RIGHT_THUMB) engineHeld |= BANGO_BTN_PARRY;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_START) engineHeld |= BANGO_BTN_MENU;
            if (state.Gamepad.wButtons & XINPUT_GAMEPAD_BACK) engineHeld |= BANGO_BTN_GAME_MENU;
            if (state.Gamepad.bLeftTrigger > 48) engineHeld |= BANGO_BTN_SPECIAL_WHEEL;
            if (changed & XINPUT_GAMEPAD_LEFT_SHOULDER) enginePressed |= BANGO_BTN_ATTACK_LIGHT;
            if (state.Gamepad.bRightTrigger > 48 && g_game.previousPad.Gamepad.bRightTrigger <= 48) enginePressed |= BANGO_BTN_ATTACK_HEAVY;
            if (changed & XINPUT_GAMEPAD_Y) enginePressed |= BANGO_BTN_INTERACT_MASS;
            if (changed & XINPUT_GAMEPAD_START) enginePressed |= BANGO_BTN_MENU;
            if (changed & XINPUT_GAMEPAD_BACK) enginePressed |= BANGO_BTN_GAME_MENU;
            if (state.Gamepad.bLeftTrigger > 48 && g_game.previousPad.Gamepad.bLeftTrigger <= 48) enginePressed |= BANGO_BTN_SPECIAL_WHEEL;
            bango_engine_target_ingest_analog(&g_engine_target, input.moveX, input.moveZ, input.lookX, input.lookY);
            bango_engine_target_ingest_buttons(&g_engine_target, engineHeld, enginePressed);
            bango_engine_target_ingest_haptics(&g_engine_target, state.Gamepad.bLeftTrigger / 255.0f, state.Gamepad.bRightTrigger / 255.0f);
            g_game.previousPad = state;
        }
    }

    if (g_game.keys[VK_SPACE]) {
        input.attackPressed = 1;
        g_game.keys[VK_SPACE] = 0;
    }
    if (g_game.keys[VK_SHIFT]) {
        input.dodgePressed = 1;
        g_game.keys[VK_SHIFT] = 0;
    }
    if (g_game.keys['E']) {
        input.interactPressed = 1;
        g_game.keys['E'] = 0;
    }
    if (g_game.keys['R']) {
        input.restartPressed = 1;
        g_game.keys['R'] = 0;
    }
    {
        BangoTelemetrySample sample = bango_telemetry_bridge_sample(&g_telemetry_bridge, 0.35f, 0.0f);
        bango_engine_target_ingest_telemetry(&g_engine_target, &sample);
    }
    bango_engine_target_update(&g_engine_target, 1.0f / 60.0f);
    return input;
}

static void resolve_player_collisions(void)
{
    for (int i = 0; i < PREVIEW_OBJECT_COUNT; ++i) {
        PreviewObject &object = g_game.objects[i];
        if (!object.active || !object.solid) {
            continue;
        }
        float dx = g_game.playerPosition.x - object.position.x;
        float dz = g_game.playerPosition.z - object.position.z;
        float overlapX = (0.42f + object.halfExtents.x) - fabsf(dx);
        float overlapZ = (0.42f + object.halfExtents.z) - fabsf(dz);
        if (overlapX > 0.0f && overlapZ > 0.0f) {
            if (overlapX < overlapZ) {
                g_game.playerPosition.x += dx < 0.0f ? -overlapX : overlapX;
            } else {
                g_game.playerPosition.z += dz < 0.0f ? -overlapZ : overlapZ;
            }
        }
    }
}

static void trigger_attack(void)
{
    if (g_game.attackTimer > 0.0f || g_game.lost || g_game.won) {
        return;
    }
    g_game.attackTimer = 0.42f;
    g_game.clip = CLIP_ATTACK;
    g_game.clipTime = 0.0f;
    g_game.clipLocked = 1;
    g_game.selectedMove = (g_game.selectedMove + 1) % 8;
    set_status(L"Horn-rush chain triggered.");

    int enemiesAlive = 0;
    for (int i = 0; i < PREVIEW_ENEMY_COUNT; ++i) {
        PreviewEnemy &enemy = g_game.enemies[i];
        if (!enemy.active) {
            continue;
        }
        Vec3 delta = vec3_sub(enemy.position, g_game.playerPosition);
        float dist = vec3_length(delta);
        Vec3 facing = vec3_make(sinf(g_game.playerFacingYaw), 0.0f, cosf(g_game.playerFacingYaw));
        float facingDot = dist > 0.001f ? vec3_dot(vec3_normalize(delta), facing) : 1.0f;
        if (dist < 2.0f && facingDot > -0.35f) {
            enemy.health -= enemy.kind == 2 ? 12.0f : 16.0f;
            enemy.hurtFlash = 0.35f;
            if (enemy.health <= 0.0f) {
                enemy.active = 0;
            }
        }
    }
    for (int i = 0; i < PREVIEW_ENEMY_COUNT; ++i) {
        if (g_game.enemies[i].active) {
            enemiesAlive += 1;
        }
    }
    g_game.enemiesAlive = enemiesAlive;
    if (enemiesAlive == 0 && !g_game.objectiveDropped) {
        g_game.objectiveDropped = 1;
        g_game.objectivePosition = vec3_make(kPreviewObjectiveDrop[0], sample_height_world(kPreviewObjectiveDrop[0], kPreviewObjectiveDrop[2]), kPreviewObjectiveDrop[2]);
        set_status(L"The hive relic dropped. Recover it and take it to the altar slot.");
    }
}

static void trigger_dodge(void)
{
    if (g_game.playerStamina < 8.0f || g_game.dodgeTimer > 0.0f || g_game.lost || g_game.won) {
        return;
    }
    g_game.playerStamina -= 8.0f;
    g_game.dodgeTimer = 0.28f;
    g_game.playerVelocity.x += sinf(g_game.playerFacingYaw) * 3.2f;
    g_game.playerVelocity.z += cosf(g_game.playerFacingYaw) * 3.2f;
    set_status(L"Feather-ward dodge.");
}

static void handle_interaction(void)
{
    if (g_game.lost) {
        return;
    }
    if (g_game.objectiveDropped && !g_game.objectiveHeld) {
        Vec3 delta = vec3_sub(g_game.objectivePosition, g_game.playerPosition);
        if (vec3_length(delta) < 1.4f) {
            g_game.objectiveHeld = 1;
            set_status(L"Relic secured. Carry it to the altar slot.");
            return;
        }
    }
    for (int i = 0; i < PREVIEW_OBJECT_COUNT; ++i) {
        PreviewObject &object = g_game.objects[i];
        if (!object.active || !object.interactive) {
            continue;
        }
        Vec3 delta = vec3_sub(object.position, g_game.playerPosition);
        if (vec3_length(delta) > 1.7f) {
            continue;
        }
        if (object.kind == OBJECT_SLOT && g_game.objectiveHeld) {
            g_game.objectiveHeld = 0;
            g_game.won = 1;
            g_game.clip = CLIP_CELEBRATE;
            g_game.clipLocked = 0;
            g_game.clipTime = 0.0f;
            set_status(L"Relic inserted. Test win triggered.");
            return;
        }
        if (object.kind == OBJECT_LIGHT) {
            object.toggled = !object.toggled;
            g_game.playerMagic = clampf(g_game.playerMagic + 6.0f, 0.0f, 40.0f);
            set_status(object.toggled ? L"Lantern kindled." : L"Lantern dimmed.");
            return;
        }
        if (object.kind == OBJECT_CACHE) {
            g_game.playerHealth = clampf(g_game.playerHealth + 18.0f, 0.0f, 100.0f);
            object.active = 0;
            set_status(L"Supply cache recovered." );
            return;
        }
    }
}

static void reset_game(void)
{
    ZeroMemory(&g_game.keys, sizeof(g_game.keys));
    g_game.playerPosition = vec3_make(kPreviewPlayerSpawn[0], sample_height_world(kPreviewPlayerSpawn[0], kPreviewPlayerSpawn[2]) + 0.95f, kPreviewPlayerSpawn[2]);
    g_game.playerVelocity = vec3_make(0.0f, 0.0f, 0.0f);
    g_game.playerFacingYaw = 0.0f;
    g_game.playerHealth = 100.0f;
    g_game.playerStamina = 72.0f;
    g_game.playerMagic = 40.0f;
    g_game.attackTimer = 0.0f;
    g_game.dodgeTimer = 0.0f;
    g_game.hitTimer = 0.0f;
    g_game.cameraYaw = 0.08f;
    g_game.cameraDistance = 2.34f;
    g_game.cameraHeight = 1.62f;
    g_game.cameraTurnVelocity = 0.0f;
    g_game.clip = CLIP_IDLE;
    g_game.clipLocked = 0;
    g_game.clipTime = 0.0f;
    g_game.selectedMove = 0;
    g_game.objectiveDropped = 0;
    g_game.objectiveHeld = 0;
    g_game.won = 0;
    g_game.lost = 0;
    g_game.objectiveSpin = 0.0f;
    g_game.statusTimer = 0;
    set_status(L"Tile-driven test world initialized. Defeat the enemies and slot the relic.");

    for (int i = 0; i < PREVIEW_OBJECT_COUNT; ++i) {
        const RuntimeLevelObjectSpawnDef &spawn = g_bango_test_level_objects[i];
        g_game.objects[i].name = spawn.name;
        g_game.objects[i].position = vec3_make(spawn.x, sample_height_world(spawn.x, spawn.z), spawn.z);
        g_game.objects[i].halfExtents = vec3_make(spawn.half_x, spawn.half_y, spawn.half_z);
        g_game.objects[i].interactive = spawn.interactive;
        g_game.objects[i].solid = spawn.solid;
        g_game.objects[i].kind = spawn.kind;
        g_game.objects[i].active = 1;
        g_game.objects[i].toggled = g_game.objects[i].kind == OBJECT_LIGHT ? 1 : 0;
    }

    g_game.enemiesAlive = PREVIEW_ENEMY_COUNT;
    for (int i = 0; i < PREVIEW_ENEMY_COUNT; ++i) {
        const RuntimeLevelEnemySpawnDef &spawn = g_bango_test_level_enemies[i];
        g_game.enemies[i].name = spawn.name;
        g_game.enemies[i].position = vec3_make(spawn.x, sample_height_world(spawn.x, spawn.z) + 0.1f, spawn.z);
        g_game.enemies[i].velocity = vec3_make(0.0f, 0.0f, 0.0f);
        g_game.enemies[i].health = spawn.health;
        g_game.enemies[i].speed = spawn.speed;
        g_game.enemies[i].kind = spawn.kind;
        g_game.enemies[i].active = 1;
        g_game.enemies[i].cooldown = 0.0f;
        g_game.enemies[i].hurtFlash = 0.0f;
    }

    for (int i = 0; i < PREVIEW_BANGO_BONE_COUNT; ++i) {
        g_game.bones[i] = {};
    }
}

static void init_state(void)
{
    BangoEngineTargetConfig engineConfig = bango_engine_target_default_config(BANGO_PLATFORM_WINDOWS);
    engineConfig.enable_touch_controls = 0;
    engineConfig.telemetry.local_only = 1;
    bango_engine_target_init(&g_engine_target, &engineConfig);
    bango_ai_stack_init(&g_ai_stack);
    bango_telemetry_bridge_init(&g_telemetry_bridge, BANGO_PLATFORM_WINDOWS, engineConfig.telemetry);
    g_game.bonePelvis = find_bone_index("pelvis");
    g_game.boneSpine = find_bone_index("spine");
    g_game.boneChest = find_bone_index("chest");
    g_game.boneNeck = find_bone_index("neck");
    g_game.boneHead = find_bone_index("head");
    g_game.boneArmL = find_bone_index("arm_l");
    g_game.boneArmR = find_bone_index("arm_r");
    g_game.boneHandL = find_bone_index("hand_l");
    g_game.boneHandR = find_bone_index("hand_r");
    g_game.boneLegL = find_bone_index("leg_l");
    g_game.boneLegR = find_bone_index("leg_r");
    g_game.boneFootL = find_bone_index("foot_l");
    g_game.boneFootR = find_bone_index("foot_r");
    g_game.boneHornL = find_bone_index("horn_l");
    g_game.boneHornR = find_bone_index("horn_r");
    reset_space_frame();
    init_xinput();
    reset_game();
}

static void update_game(float dt)
{
    InputFrame input = poll_input();
    Vec3 groundNormal = sample_normal_world(g_game.playerPosition.x, g_game.playerPosition.z);
    float terrainRelief = clampf(1.0f - groundNormal.y, 0.0f, 1.0f);
    float inputEnergy = clampf(fabsf(input.moveX) + fabsf(input.moveZ) + fabsf(input.lookX) + fabsf(input.lookY), 0.0f, 2.5f);
    float semanticExpectation = clampf(g_engine_target.combat_precision, 0.0f, 1.0f);
    float semanticInfluence = clampf(g_engine_target.combat_force, 0.0f, 1.0f);
    const char *semanticVerb = input.attackPressed ? "attack" : input.interactPressed ? "interact" : input.specialWheelHeld ? "adapt" : "advance";
    const char *semanticNoun = g_game.objectiveHeld ? "relic" : g_game.enemiesAlive > 0 ? "enemy" : "altar";

    bango_space_frame_update(&g_space_frame, dt, g_game.playerPosition.x, g_game.playerPosition.y, g_game.playerPosition.z, g_game.playerVelocity.x, 0.0f, g_game.playerVelocity.z, clampf(fabsf(g_game.cameraTurnVelocity) * 0.01f, 0.0f, 1.0f), inputEnergy);

    bango_ai_stack_begin_frame(&g_ai_stack);
    bango_ai_stack_ingest_input_signal(&g_ai_stack, clampf(sqrtf(input.moveX * input.moveX + input.moveZ * input.moveZ), 0.0f, 1.0f), clampf(fabsf(input.lookX) + fabsf(input.lookY), 0.0f, 1.0f), g_engine_target.frame.buttons_held, g_engine_target.frame.buttons_pressed);
    bango_ai_stack_ingest_environment(
        &g_ai_stack,
        clampf(terrainRelief + g_space_frame.metrics.disruption * 0.65f, 0.0f, 1.0f),
        clampf(0.62f + g_space_frame.metrics.gravity_focus * 0.45f, 0.0f, 1.0f),
        clampf(0.55f + g_space_frame.metrics.radiation * 0.65f, 0.0f, 1.0f),
        clampf(g_space_frame.metrics.pressure_density + g_space_frame.metrics.pore_flux * 0.35f, 0.0f, 1.0f));
    bango_ai_stack_resolve_semantics(&g_ai_stack, semanticVerb, semanticNoun, semanticExpectation, semanticInfluence);
    bango_ai_stack_generate_camera(&g_ai_stack, &g_ai_camera);
    bango_ai_stack_generate_simulation(&g_ai_stack, &g_ai_simulation);
    bango_ai_stack_generate_render(&g_ai_stack, &g_ai_render);

    if (input.restartPressed) {
        reset_game();
        return;
    }
    if (g_game.won || g_game.lost) {
        g_game.clip = g_game.won ? CLIP_CELEBRATE : CLIP_HIT;
        g_game.clipLocked = 0;
    }

    float moveX = input.moveX;
    float moveZ = input.moveZ;
    float moveLen = sqrtf(moveX * moveX + moveZ * moveZ);
    if (moveLen > 1.0f) {
        moveX /= moveLen;
        moveZ /= moveLen;
    }

    if (!g_game.won && !g_game.lost) {
        float flowBoost = 1.0f + g_space_frame.metrics.gravity_focus * 0.12f - g_space_frame.metrics.pressure_density * 0.08f;
        float blendRate = 0.14f + g_space_frame.metrics.disturbance * 0.04f;
        g_game.playerVelocity.x = lerpf(g_game.playerVelocity.x, moveX * 3.2f * flowBoost, blendRate);
        g_game.playerVelocity.z = lerpf(g_game.playerVelocity.z, moveZ * 3.2f * flowBoost, blendRate);
        if (moveLen > 0.12f) {
            g_game.playerFacingYaw = atan2f(moveX, moveZ);
        }
        g_game.playerPosition.x += g_game.playerVelocity.x * dt;
        g_game.playerPosition.z += g_game.playerVelocity.z * dt;
    }

    resolve_player_collisions();
    g_game.playerPosition.y = sample_height_world(g_game.playerPosition.x, g_game.playerPosition.z) + 0.95f + g_space_frame.metrics.displacement * 0.035f;

    if (input.specialWheelHeld) {
        float wheelLen = sqrtf(input.lookX * input.lookX + input.lookY * input.lookY);
        if (wheelLen > 0.55f) {
            float wheelAngle = atan2f(input.lookX, input.lookY);
            if (wheelAngle < 0.0f) {
                wheelAngle += 6.2831853f;
            }
            g_game.selectedMove = ((int)floorf((wheelAngle / 6.2831853f) * 8.0f + 0.5f)) % 8;
        }
    }

    float previousCameraYaw = g_game.cameraYaw;
    float cameraLook = fabsf(input.lookX);
    if (cameraLook > 0.12f && !input.specialWheelHeld) {
        g_game.cameraYaw += input.lookX * dt * (2.0f + g_ai_camera.panorama_warp * 1.25f);
    } else {
        g_game.cameraYaw = lerpf(g_game.cameraYaw, g_game.playerFacingYaw * 0.35f, 0.06f);
    }
    g_game.cameraTurnVelocity = lerpf(g_game.cameraTurnVelocity, wrap_radians(g_game.cameraYaw - previousCameraYaw) / std::max(dt, 0.0001f), 0.22f);
    g_game.cameraDistance = lerpf(g_game.cameraDistance, g_ai_camera.shoulder_back - g_space_frame.metrics.gravity_focus * 0.18f, 0.10f);
    g_game.cameraHeight = clampf(g_game.cameraHeight + (-input.lookY * dt * 1.05f) + g_space_frame.metrics.pore_flux * 0.015f, 1.36f, 1.92f);
    g_game.playerStamina = clampf(g_game.playerStamina + 12.0f * dt, 0.0f, 72.0f);
    g_game.playerMagic = clampf(g_game.playerMagic + 4.0f * dt, 0.0f, 40.0f);
    g_game.objectiveSpin += dt * 1.8f;

    if (input.attackPressed) {
        trigger_attack();
    }
    if (input.dodgePressed) {
        trigger_dodge();
    }
    if (input.interactPressed) {
        handle_interaction();
    }

    if (g_game.attackTimer > 0.0f) {
        g_game.attackTimer -= dt;
    } else if (g_game.clip == CLIP_ATTACK) {
        g_game.clipLocked = 0;
    }
    if (g_game.dodgeTimer > 0.0f) {
        g_game.dodgeTimer -= dt;
    }
    if (g_game.hitTimer > 0.0f) {
        g_game.hitTimer -= dt;
    }

    for (int i = 0; i < PREVIEW_ENEMY_COUNT; ++i) {
        PreviewEnemy &enemy = g_game.enemies[i];
        if (!enemy.active) {
            continue;
        }
        Vec3 delta = vec3_sub(g_game.playerPosition, enemy.position);
        delta.y = 0.0f;
        float dist = vec3_length(delta);
        if (dist < 10.0f && !g_game.won && !g_game.lost) {
            Vec3 dir = dist > 0.001f ? vec3_scale(delta, 1.0f / dist) : vec3_make(0.0f, 0.0f, 1.0f);
            if (dist > 1.35f) {
                float densityDrag = 1.0f - g_space_frame.metrics.pressure_density * 0.10f;
                enemy.position.x += dir.x * enemy.speed * densityDrag;
                enemy.position.z += dir.z * enemy.speed * densityDrag;
            } else if (enemy.cooldown <= 0.0f && g_game.hitTimer <= 0.0f) {
                g_game.playerHealth -= enemy.kind == 2 ? 18.0f : 11.0f;
                g_game.hitTimer = 0.42f;
                enemy.cooldown = 1.0f;
                set_status(L"Bango took a hit.");
                if (g_game.playerHealth <= 0.0f) {
                    g_game.playerHealth = 0.0f;
                    g_game.lost = 1;
                    set_status(L"Bango fell. Restart the test world.");
                }
            }
        }
        enemy.position.y = sample_height_world(enemy.position.x, enemy.position.z) + 0.1f;
        enemy.cooldown = std::max(0.0f, enemy.cooldown - dt);
        enemy.hurtFlash = std::max(0.0f, enemy.hurtFlash - dt);
    }

    if (g_game.objectiveHeld) {
        g_game.objectivePosition = vec3_add(g_game.playerPosition, rotate_y(vec3_make(0.0f, 1.55f, 0.7f), g_game.playerFacingYaw));
    }

    if (!g_game.clipLocked) {
        if (g_game.won) {
            g_game.clip = CLIP_CELEBRATE;
        } else if (g_game.lost || g_game.hitTimer > 0.0f) {
            g_game.clip = CLIP_HIT;
        } else if (g_game.objectiveHeld) {
            g_game.clip = CLIP_CARRY;
        } else if (moveLen > 0.12f) {
            g_game.clip = CLIP_LOCOMOTION;
        } else {
            g_game.clip = CLIP_IDLE;
        }
    }

    g_game.clipTime += dt;
    update_bango_pose(dt);
    if (g_game.statusTimer > 0) {
        g_game.statusTimer -= 1;
    }
}

static void draw_scene(HDC hdc, RECT rect)
{
    Graphics graphics(hdc);
    graphics.SetSmoothingMode(SmoothingModeAntiAlias);
    graphics.SetInterpolationMode(InterpolationModeNearestNeighbor);
    graphics.SetPixelOffsetMode(PixelOffsetModeHalf);

    g_viewport = build_gameplay_viewport(rect);
    prepare_camera_rig();

    SolidBrush matte(Color(255, 0, 0, 0));
    graphics.FillRectangle(&matte, (REAL)rect.left, (REAL)rect.top, (REAL)(rect.right - rect.left), (REAL)(rect.bottom - rect.top));

    RectF gameplayRect(g_viewport.left, g_viewport.top, g_viewport.width, g_viewport.height);
    graphics.SetClip(gameplayRect);

    fill_gradient_background(graphics, (int)g_viewport.width, (int)g_viewport.height);
    draw_horizon(graphics);
    draw_terrain(graphics);
    for (int i = 0; i < PREVIEW_OBJECT_COUNT; ++i) {
        render_object(graphics, g_game.objects[i]);
    }
    for (int i = 0; i < PREVIEW_ENEMY_COUNT; ++i) {
        render_enemy(graphics, g_game.enemies[i]);
    }
    render_objective(graphics);
    render_bango(graphics);
    render_patoot(graphics);

    graphics.ResetClip();
    Pen framePen(Color(255, 88, 76, 58), 2.0f);
    graphics.DrawRectangle(&framePen, gameplayRect);
    draw_hud(hdc, rect);
}

static LRESULT CALLBACK window_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message) {
    case WM_CREATE:
        SetTimer(hwnd, 1, 16, NULL);
        return 0;
    case WM_TIMER:
        update_game(1.0f / 60.0f);
        InvalidateRect(hwnd, NULL, FALSE);
        return 0;
    case WM_KEYDOWN:
        if (wParam < 256) {
            g_game.keys[wParam] = 1;
        }
        if (wParam == VK_ESCAPE) {
            DestroyWindow(hwnd);
        }
        return 0;
    case WM_KEYUP:
        if (wParam < 256) {
            g_game.keys[wParam] = 0;
        }
        return 0;
    case WM_PAINT:
        {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hwnd, &ps);
            RECT rect;
            GetClientRect(hwnd, &rect);
            draw_scene(hdc, rect);
            EndPaint(hwnd, &ps);
        }
        return 0;
    case WM_DESTROY:
        KillTimer(hwnd, 1);
        if (g_game.xinput.module) {
            FreeLibrary(g_game.xinput.module);
        }
        GdiplusShutdown(g_game.gdiplusToken);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, message, wParam, lParam);
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand)
{
    GdiplusStartupInput startupInput = {};
    WNDCLASSEXW windowClass = {};
    MSG message;

    startupInput.GdiplusVersion = 1;
    GdiplusStartup(&g_game.gdiplusToken, &startupInput, NULL);
    init_state();

    windowClass.cbSize = sizeof(windowClass);
    windowClass.style = CS_HREDRAW | CS_VREDRAW;
    windowClass.lpfnWndProc = window_proc;
    windowClass.hInstance = instance;
    windowClass.hCursor = LoadCursor(NULL, IDC_ARROW);
    windowClass.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    windowClass.lpszClassName = kWindowClass;
    RegisterClassExW(&windowClass);

    g_game.window = CreateWindowExW(
        0,
        kWindowClass,
        kWindowTitle,
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        1440,
        900,
        NULL,
        NULL,
        instance,
        NULL);

    ShowWindow(g_game.window, showCommand);
    UpdateWindow(g_game.window);

    while (GetMessageW(&message, NULL, 0, 0)) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }

    return (int)message.wParam;
}