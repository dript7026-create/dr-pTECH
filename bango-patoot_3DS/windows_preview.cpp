#define _USE_MATH_DEFINES

#include <windows.h>
#include <gdiplus.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string>
#include <cwchar>

#pragma comment(lib, "gdiplus.lib")

using namespace Gdiplus;

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

struct SpriteSheet {
    Image *image;
    int angleCount;
};

struct WorldNode {
    const wchar_t *name;
    float horrorPressure;
    float verticality;
};

struct EnvironmentObject {
    Vec3 position;
    Vec3 halfExtents;
    bool interactive;
};

struct EnemyActor {
    Vec3 position;
    float health;
    float hurtFlash;
    bool active;
};

struct WildlifeEntity {
    Vec3 position;
    bool flora;
    bool active;
};

struct PreviewState {
    ULONG_PTR gdiplusToken;
    HWND window;
    SpriteSheet bango;
    SpriteSheet patoot;
    WorldNode worlds[8];
    EnvironmentObject objects[24];
    EnemyActor enemies[10];
    WildlifeEntity wildlife[16];
    int objectCount;
    int enemyCount;
    int wildlifeCount;
    int currentWorld;
    Vec3 playerPosition;
    int facingAngle;
    float cameraYaw;
    float cameraDistance;
    float cameraHeight;
    float stamina;
    float magic;
    float health;
    int selectedMove;
    uint64_t frameCounter;
    int messageTimer;
    wchar_t statusLine[160];
    bool keys[256];
};

static PreviewState g_state = {};

static const wchar_t *kWindowClass = L"BangoPatootWindowsPreview";
static const wchar_t *kWindowTitle = L"Bango-Patoot Windows QA Preview";

static Vec3 vec3_make(float x, float y, float z)
{
    Vec3 value = {x, y, z};
    return value;
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

static float world_height_noise(int x, int z, int worldIndex)
{
    float fx = (float)x * 0.46f;
    float fz = (float)z * 0.37f;
    float seed = (float)(worldIndex + 1) * 0.71f;
    return sinf(fx + seed) * 0.55f + cosf(fz * 1.3f - seed) * 0.35f + sinf((fx + fz) * 0.33f) * 0.22f;
}

static float landscape_height_at(float worldX, float worldZ)
{
    float localX = (worldX + 11.0f) / 1.25f;
    float localZ = (worldZ - 4.0f) / 1.25f;
    int x = (int)floorf(localX);
    int z = (int)floorf(localZ);
    return world_height_noise(x, z, g_state.currentWorld) * (0.75f + g_state.worlds[g_state.currentWorld].verticality * 1.4f);
}

static ScreenPoint project_world_point(Vec3 world)
{
    Vec3 camera;
    Vec3 rel;
    float sinYaw;
    float cosYaw;
    float viewX;
    float viewZ;
    ScreenPoint point;

    camera = vec3_make(
        g_state.playerPosition.x - sinf(g_state.cameraYaw) * g_state.cameraDistance,
        g_state.playerPosition.y + g_state.cameraHeight,
        g_state.playerPosition.z - cosf(g_state.cameraYaw) * g_state.cameraDistance);
    rel = vec3_make(world.x - camera.x, world.y - camera.y, world.z - camera.z);
    sinYaw = sinf(g_state.cameraYaw);
    cosYaw = cosf(g_state.cameraYaw);
    viewX = rel.x * cosYaw - rel.z * sinYaw;
    viewZ = rel.x * sinYaw + rel.z * cosYaw;

    point.visible = viewZ > 0.2f;
    point.depth = viewZ;
    point.x = 430.0f + (viewX / (viewZ + 0.001f)) * 320.0f;
    point.y = 260.0f - (rel.y / (viewZ + 0.001f)) * 220.0f;
    return point;
}

static void set_status(const wchar_t *text)
{
    wcsncpy_s(g_state.statusLine, _countof(g_state.statusLine), text, _TRUNCATE);
    g_state.messageTimer = 180;
}

static std::wstring build_asset_path(const wchar_t *relativePath)
{
    wchar_t buffer[MAX_PATH];
    DWORD length = GetModuleFileNameW(NULL, buffer, MAX_PATH);
    while (length > 0 && buffer[length - 1] != L'\\' && buffer[length - 1] != L'/') {
        --length;
    }
    buffer[length] = 0;
    std::wstring path = buffer;
    path += relativePath;
    return path;
}

static Image *load_image(const wchar_t *relativePath)
{
    std::wstring path = build_asset_path(relativePath);
    Image *image = new Image(path.c_str());
    if (!image || image->GetLastStatus() != Ok) {
        delete image;
        return NULL;
    }
    return image;
}

static void load_sheets(void)
{
    g_state.bango.image = load_image(L"assets\\source_sheets\\bango_tpose_4angle.png");
    g_state.bango.angleCount = 4;
    g_state.patoot.image = load_image(L"assets\\source_sheets\\patoot_tpose_4angle.png");
    g_state.patoot.angleCount = 4;
}

static void unload_sheets(void)
{
    delete g_state.bango.image;
    delete g_state.patoot.image;
    g_state.bango.image = NULL;
    g_state.patoot.image = NULL;
}

static void init_worlds(void)
{
    g_state.worlds[0] = {L"Brassroot Borough", 0.15f, 0.20f};
    g_state.worlds[1] = {L"Saint Voltage Arcade", 0.25f, 0.28f};
    g_state.worlds[2] = {L"Ossuary Transit", 0.35f, 0.36f};
    g_state.worlds[3] = {L"Gutterwake Sewers", 0.45f, 0.44f};
    g_state.worlds[4] = {L"Cinder Tenements", 0.55f, 0.20f};
    g_state.worlds[5] = {L"Aviary Broadcast", 0.65f, 0.28f};
    g_state.worlds[6] = {L"Witchcoil Spire", 0.75f, 0.36f};
    g_state.worlds[7] = {L"Underhive Hub", 0.85f, 0.44f};
}

static void populate_world_runtime(void)
{
    int i;
    g_state.objectCount = 10;
    g_state.enemyCount = 4 + (g_state.currentWorld % 3);
    g_state.wildlifeCount = 8 + (g_state.currentWorld % 3) * 2;

    for (i = 0; i < g_state.objectCount; ++i) {
        float lane = (float)((i % 5) - 2) * 1.9f;
        float depth = 7.0f + (float)(i / 2) * 1.9f;
        g_state.objects[i].position = vec3_make(lane + sinf((float)i * 0.8f) * 0.6f, 0.0f, depth);
        g_state.objects[i].position.y = landscape_height_at(g_state.objects[i].position.x, g_state.objects[i].position.z);
        g_state.objects[i].halfExtents = vec3_make(0.35f + 0.08f * (float)(i % 3), 0.5f + 0.18f * (float)(i % 4), 0.35f);
        g_state.objects[i].interactive = (i % 3 == 0);
    }

    for (i = 0; i < g_state.enemyCount; ++i) {
        g_state.enemies[i].position = vec3_make(-3.0f + (float)i * 1.8f, 0.0f, 10.0f + (float)(i % 3) * 1.7f);
        g_state.enemies[i].position.y = landscape_height_at(g_state.enemies[i].position.x, g_state.enemies[i].position.z) + 0.75f;
        g_state.enemies[i].health = 22.0f + g_state.worlds[g_state.currentWorld].horrorPressure * 12.0f;
        g_state.enemies[i].hurtFlash = 0.0f;
        g_state.enemies[i].active = true;
    }

    for (i = 0; i < g_state.wildlifeCount; ++i) {
        g_state.wildlife[i].position = vec3_make(-4.0f + (float)(i % 6) * 1.7f, 0.0f, 5.5f + (float)(i / 3) * 1.8f);
        g_state.wildlife[i].position.y = landscape_height_at(g_state.wildlife[i].position.x, g_state.wildlife[i].position.z);
        g_state.wildlife[i].flora = (i % 2 == 0);
        g_state.wildlife[i].active = true;
    }
}

static void init_state(void)
{
    ZeroMemory(&g_state.keys, sizeof(g_state.keys));
    init_worlds();
    load_sheets();
    g_state.currentWorld = 7;
    g_state.playerPosition = vec3_make(0.0f, 0.0f, 6.2f);
    g_state.playerPosition.y = landscape_height_at(g_state.playerPosition.x, g_state.playerPosition.z) + 0.85f;
    g_state.facingAngle = 0;
    g_state.cameraYaw = 0.08f;
    g_state.cameraDistance = 8.2f;
    g_state.cameraHeight = 3.8f;
    g_state.stamina = 72.0f;
    g_state.magic = 40.0f;
    g_state.health = 100.0f;
    g_state.selectedMove = 0;
    populate_world_runtime();
    set_status(L"Bango and Patoot descend into the Underhive Hub with current placeholder assets loaded.");
}

static void draw_text(HDC hdc, int x, int y, COLORREF color, const wchar_t *text)
{
    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, color);
    TextOutW(hdc, x, y, text, (int)wcslen(text));
}

static void draw_sheet_frame(Graphics &graphics, const SpriteSheet &sheet, int angleIndex, float centerX, float baselineY, float scale)
{
    if (!sheet.image || sheet.angleCount <= 0) {
        SolidBrush fallback(Color(255, 230, 200, 120));
        graphics.FillEllipse(&fallback, centerX - 12.0f, baselineY - 28.0f, 24.0f, 24.0f);
        return;
    }

    UINT width = sheet.image->GetWidth();
    UINT height = sheet.image->GetHeight();
    UINT frameWidth = width / (UINT)sheet.angleCount;
    int clampedAngle = angleIndex % sheet.angleCount;
    RectF dest(centerX - frameWidth * scale * 0.5f, baselineY - height * scale, frameWidth * scale, height * scale);
    graphics.DrawImage(sheet.image, dest, (REAL)(clampedAngle * frameWidth), 0.0f, (REAL)frameWidth, (REAL)height, UnitPixel);
}

static void draw_landscape(Graphics &graphics)
{
    int z;
    for (z = 16; z >= 0; --z) {
        int x;
        for (x = 0; x < 17; ++x) {
            Vec3 p00 = vec3_make(-11.0f + (float)x * 1.25f, world_height_noise(x, z, g_state.currentWorld), 4.0f + (float)z * 1.25f);
            Vec3 p10 = vec3_make(-11.0f + (float)(x + 1) * 1.25f, world_height_noise(x + 1, z, g_state.currentWorld), 4.0f + (float)z * 1.25f);
            Vec3 p01 = vec3_make(-11.0f + (float)x * 1.25f, world_height_noise(x, z + 1, g_state.currentWorld), 4.0f + (float)(z + 1) * 1.25f);
            Vec3 p11 = vec3_make(-11.0f + (float)(x + 1) * 1.25f, world_height_noise(x + 1, z + 1, g_state.currentWorld), 4.0f + (float)(z + 1) * 1.25f);
            ScreenPoint s00 = project_world_point(p00);
            ScreenPoint s10 = project_world_point(p10);
            ScreenPoint s01 = project_world_point(p01);
            ScreenPoint s11 = project_world_point(p11);
            if (!s00.visible || !s10.visible || !s01.visible || !s11.visible) {
                continue;
            }
            float avg = (p00.y + p10.y + p01.y + p11.y) * 0.25f;
            int red = (int)clampf(52.0f + g_state.worlds[g_state.currentWorld].horrorPressure * 48.0f + avg * 18.0f, 0.0f, 255.0f);
            int green = (int)clampf(58.0f + avg * 18.0f, 0.0f, 255.0f);
            int blue = (int)clampf(72.0f + g_state.worlds[g_state.currentWorld].verticality * 80.0f, 0.0f, 255.0f);
            PointF triA[3] = {PointF(s00.x, s00.y), PointF(s10.x, s10.y), PointF(s11.x, s11.y)};
            PointF triB[3] = {PointF(s00.x, s00.y), PointF(s11.x, s11.y), PointF(s01.x, s01.y)};
            SolidBrush fill(Color(255, red, green, blue));
            Pen pen(Color(180, 18, 16, 26), 1.0f);
            graphics.FillPolygon(&fill, triA, 3);
            graphics.FillPolygon(&fill, triB, 3);
            graphics.DrawPolygon(&pen, triA, 3);
            graphics.DrawPolygon(&pen, triB, 3);
        }
    }
}

static void draw_objects(Graphics &graphics)
{
    int i;
    for (i = 0; i < g_state.objectCount; ++i) {
        ScreenPoint base = project_world_point(g_state.objects[i].position);
        ScreenPoint top = project_world_point(vec3_make(g_state.objects[i].position.x, g_state.objects[i].position.y + g_state.objects[i].halfExtents.y * 2.0f, g_state.objects[i].position.z));
        if (!base.visible || !top.visible) {
            continue;
        }
        float width = clampf(26.0f / (base.depth + 0.5f), 6.0f, 38.0f);
        SolidBrush brush(g_state.objects[i].interactive ? Color(220, 196, 168, 92) : Color(220, 96, 112, 138));
        graphics.FillRectangle(&brush, base.x - width * 0.5f, top.y, width, base.y - top.y);
    }
}

static void draw_enemies(Graphics &graphics)
{
    int i;
    for (i = 0; i < g_state.enemyCount; ++i) {
        if (!g_state.enemies[i].active) {
            continue;
        }
        ScreenPoint base = project_world_point(g_state.enemies[i].position);
        ScreenPoint top = project_world_point(vec3_make(g_state.enemies[i].position.x, g_state.enemies[i].position.y + 1.5f, g_state.enemies[i].position.z));
        if (!base.visible || !top.visible) {
            continue;
        }
        float width = clampf(24.0f / (base.depth + 0.4f), 8.0f, 26.0f);
        int red = g_state.enemies[i].hurtFlash > 0.0f ? 255 : 158;
        int green = g_state.enemies[i].hurtFlash > 0.0f ? 120 : 78;
        int blue = g_state.enemies[i].hurtFlash > 0.0f ? 120 : 86;
        PointF points[3] = {PointF(base.x, top.y), PointF(base.x - width * 0.5f, base.y), PointF(base.x + width * 0.5f, base.y)};
        SolidBrush brush(Color(255, red, green, blue));
        graphics.FillPolygon(&brush, points, 3);
    }
}

static void draw_wildlife(Graphics &graphics)
{
    int i;
    for (i = 0; i < g_state.wildlifeCount; ++i) {
        if (!g_state.wildlife[i].active) {
            continue;
        }
        ScreenPoint point = project_world_point(g_state.wildlife[i].position);
        if (!point.visible) {
            continue;
        }
        float size = clampf(9.0f / (point.depth + 0.3f), 3.0f, 12.0f);
        if (g_state.wildlife[i].flora) {
            SolidBrush brush(Color(255, 68, 148, 92));
            graphics.FillEllipse(&brush, point.x - size, point.y - size, size * 2.0f, size * 2.0f);
        } else {
            PointF tri[3] = {PointF(point.x, point.y - size), PointF(point.x - size * 0.6f, point.y), PointF(point.x + size * 0.6f, point.y)};
            SolidBrush brush(Color(255, 220, 195, 160));
            graphics.FillPolygon(&brush, tri, 3);
        }
    }
}

static void draw_scene(HDC hdc, RECT clientRect)
{
    Graphics graphics(hdc);
    graphics.SetSmoothingMode(SmoothingModeNone);
    graphics.SetInterpolationMode(InterpolationModeNearestNeighbor);
    graphics.SetPixelOffsetMode(PixelOffsetModeHalf);

    SolidBrush bg(Color(255, 8, 10, 18));
    SolidBrush topBand(Color(255, 28, 22, 42));
    SolidBrush bottomBand(Color(255, 18, 16, 24));
    graphics.FillRectangle(&bg, 0.0f, 0.0f, (REAL)(clientRect.right - clientRect.left), (REAL)(clientRect.bottom - clientRect.top));
    graphics.FillRectangle(&topBand, 0.0f, 0.0f, (REAL)(clientRect.right - clientRect.left), 140.0f);
    graphics.FillRectangle(&bottomBand, 0.0f, 140.0f, (REAL)(clientRect.right - clientRect.left), (REAL)(clientRect.bottom - clientRect.top - 140));

    draw_landscape(graphics);
    draw_objects(graphics);
    draw_enemies(graphics);
    draw_wildlife(graphics);

    {
        ScreenPoint bangoPoint = project_world_point(g_state.playerPosition);
        ScreenPoint patootPoint = project_world_point(vec3_make(g_state.playerPosition.x + 0.55f, g_state.playerPosition.y + 0.45f, g_state.playerPosition.z - 0.35f));
        if (bangoPoint.visible) {
            draw_sheet_frame(graphics, g_state.bango, g_state.facingAngle, bangoPoint.x, bangoPoint.y, clampf(2.6f / (bangoPoint.depth * 0.12f + 0.2f), 1.2f, 3.8f));
        }
        if (patootPoint.visible) {
            draw_sheet_frame(graphics, g_state.patoot, (g_state.facingAngle + 1) % 4, patootPoint.x, patootPoint.y, clampf(2.4f / (patootPoint.depth * 0.12f + 0.2f), 1.1f, 3.6f));
        }
    }

    {
        wchar_t buffer[256];
        swprintf_s(buffer, L"Bango-Patoot Windows QA Preview: %ls", g_state.worlds[g_state.currentWorld].name);
        draw_text(hdc, 20, 20, RGB(240, 232, 208), buffer);
        swprintf_s(buffer, L"HP %.0f  ST %.0f  MA %.0f  Move %d  World %d", g_state.health, g_state.stamina, g_state.magic, g_state.selectedMove + 1, g_state.currentWorld + 1);
        draw_text(hdc, 20, 44, RGB(214, 214, 226), buffer);
        swprintf_s(buffer, L"Objects %d  Enemies %d  Wildlife %d  Horror %.2f", g_state.objectCount, g_state.enemyCount, g_state.wildlifeCount, g_state.worlds[g_state.currentWorld].horrorPressure);
        draw_text(hdc, 20, 68, RGB(210, 190, 120), buffer);
        draw_text(hdc, 20, clientRect.bottom - 64, RGB(220, 220, 220), L"Controls: WASD move  Space attack  Shift dodge  Tab cycle move  Q/E switch world  Esc quit");
        if (g_state.messageTimer > 0) {
            draw_text(hdc, 20, clientRect.bottom - 36, RGB(255, 214, 164), g_state.statusLine);
        }
    }
}

static void update_state(void)
{
    float inputX = 0.0f;
    float inputZ = 0.0f;
    float length;
    g_state.frameCounter += 1;

    if (g_state.keys['A']) inputX -= 1.0f;
    if (g_state.keys['D']) inputX += 1.0f;
    if (g_state.keys['W']) inputZ += 1.0f;
    if (g_state.keys['S']) inputZ -= 1.0f;

    length = sqrtf(inputX * inputX + inputZ * inputZ);
    if (length > 0.0f) {
        inputX /= length;
        inputZ /= length;
        g_state.playerPosition.x += inputX * 0.08f;
        g_state.playerPosition.z += inputZ * 0.08f;
        if (fabsf(inputX) >= fabsf(inputZ)) {
            g_state.facingAngle = inputX < 0.0f ? 1 : 2;
        } else {
            g_state.facingAngle = inputZ < 0.0f ? 3 : 0;
        }
    }

    g_state.playerPosition.y = landscape_height_at(g_state.playerPosition.x, g_state.playerPosition.z) + 0.85f;
    g_state.cameraYaw = lerpf(g_state.cameraYaw, ((float)g_state.facingAngle - 1.5f) * 0.18f, 0.05f);
    g_state.cameraDistance = 7.8f - g_state.worlds[g_state.currentWorld].verticality * 0.7f;
    g_state.cameraHeight = 3.7f + g_state.worlds[g_state.currentWorld].verticality * 0.6f;
    g_state.stamina = clampf(g_state.stamina + 0.12f, 0.0f, 72.0f);
    g_state.magic = clampf(g_state.magic + 0.05f, 0.0f, 40.0f);

    for (int i = 0; i < g_state.enemyCount; ++i) {
        if (g_state.enemies[i].hurtFlash > 0.0f) {
            g_state.enemies[i].hurtFlash -= 0.5f;
        }
    }

    if (g_state.messageTimer > 0) {
        g_state.messageTimer -= 1;
    }
}

static void attack(void)
{
    int hits = 0;
    for (int i = 0; i < g_state.enemyCount; ++i) {
        float dx;
        float dz;
        float dist;
        if (!g_state.enemies[i].active) {
            continue;
        }
        dx = g_state.enemies[i].position.x - g_state.playerPosition.x;
        dz = g_state.enemies[i].position.z - g_state.playerPosition.z;
        dist = sqrtf(dx * dx + dz * dz);
        if (dist <= 1.5f) {
            g_state.enemies[i].health -= 8.0f;
            g_state.enemies[i].hurtFlash = 12.0f;
            if (g_state.enemies[i].health <= 0.0f) {
                g_state.enemies[i].active = false;
            }
            ++hits;
        }
    }
    if (hits > 0) {
        set_status(L"Move connected inside the Windows QA preview arena.");
    } else {
        set_status(L"Attack input registered.");
    }
}

static void dodge(void)
{
    if (g_state.stamina < 8.0f) {
        set_status(L"Too exhausted to dodge.");
        return;
    }
    g_state.stamina -= 8.0f;
    switch (g_state.facingAngle) {
    case 1: g_state.playerPosition.x -= 0.65f; break;
    case 2: g_state.playerPosition.x += 0.65f; break;
    case 3: g_state.playerPosition.z -= 0.65f; break;
    default: g_state.playerPosition.z += 0.65f; break;
    }
    set_status(L"Feather-ward sidestep.");
}

static void switch_world(int delta)
{
    g_state.currentWorld += delta;
    if (g_state.currentWorld < 0) g_state.currentWorld = 7;
    if (g_state.currentWorld > 7) g_state.currentWorld = 0;
    populate_world_runtime();
    g_state.playerPosition.y = landscape_height_at(g_state.playerPosition.x, g_state.playerPosition.z) + 0.85f;
    set_status(delta > 0 ? L"Shifted route toward a deeper district." : L"Shifted route toward an earlier district.");
}

static LRESULT CALLBACK window_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message) {
    case WM_CREATE:
        SetTimer(hwnd, 1, 16, NULL);
        return 0;
    case WM_TIMER:
        update_state();
        InvalidateRect(hwnd, NULL, FALSE);
        return 0;
    case WM_KEYDOWN:
        if (wParam < 256) g_state.keys[wParam] = true;
        if (wParam == VK_ESCAPE) {
            DestroyWindow(hwnd);
        } else if (wParam == VK_SPACE) {
            attack();
        } else if (wParam == VK_SHIFT) {
            dodge();
        } else if (wParam == VK_TAB) {
            g_state.selectedMove = (g_state.selectedMove + 1) % 8;
            set_status(L"Cycled move catalog entry.");
        } else if (wParam == 'Q') {
            switch_world(-1);
        } else if (wParam == 'E') {
            switch_world(1);
        }
        return 0;
    case WM_KEYUP:
        if (wParam < 256) g_state.keys[wParam] = false;
        return 0;
    case WM_PAINT:
        {
            PAINTSTRUCT paint;
            RECT rect;
            HDC hdc = BeginPaint(hwnd, &paint);
            GetClientRect(hwnd, &rect);
            draw_scene(hdc, rect);
            EndPaint(hwnd, &paint);
        }
        return 0;
    case WM_DESTROY:
        KillTimer(hwnd, 1);
        unload_sheets();
        GdiplusShutdown(g_state.gdiplusToken);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, message, wParam, lParam);
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand)
{
    GdiplusStartupInput startupInput;
    WNDCLASSEXW windowClass = {};
    MSG message;

    startupInput.GdiplusVersion = 1;
    startupInput.DebugEventCallback = NULL;
    startupInput.SuppressBackgroundThread = FALSE;
    startupInput.SuppressExternalCodecs = FALSE;
    GdiplusStartup(&g_state.gdiplusToken, &startupInput, NULL);

    init_state();

    windowClass.cbSize = sizeof(windowClass);
    windowClass.style = CS_HREDRAW | CS_VREDRAW;
    windowClass.lpfnWndProc = window_proc;
    windowClass.hInstance = instance;
    windowClass.hCursor = LoadCursor(NULL, IDC_ARROW);
    windowClass.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    windowClass.lpszClassName = kWindowClass;
    RegisterClassExW(&windowClass);

    g_state.window = CreateWindowExW(
        0,
        kWindowClass,
        kWindowTitle,
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        1280,
        820,
        NULL,
        NULL,
        instance,
        NULL);

    ShowWindow(g_state.window, showCommand);
    UpdateWindow(g_state.window);

    while (GetMessageW(&message, NULL, 0, 0)) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }

    return (int)message.wParam;
}