#define _CRT_SECURE_NO_WARNINGS
#define NOMINMAX

#include <windows.h>
#include <gdiplus.h>
#include <xinput.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cwchar>
#include <string>
#include <vector>

#include "data.h"

using namespace Gdiplus;

namespace {

enum DemoMode {
    MODE_TITLE = 0,
    MODE_NAVIGATION,
    MODE_COMBAT,
    MODE_FARM,
    MODE_COOKING,
    MODE_EVOLUTION,
    MODE_STATS,
    MODE_PAUSE,
};

struct AssetImage {
    std::wstring path;
    Image *image;
};

struct ControllerState {
    bool connected;
    WORD buttons;
    WORD previousButtons;
    float lx;
    float ly;
    float rx;
    float ry;
    float lt;
    float rt;
    bool lsUp;
    bool lsDown;
    bool lsLeft;
    bool lsRight;
    bool prevLsUp;
    bool prevLsDown;
    bool prevLsLeft;
    bool prevLsRight;
    bool rsUp;
    bool rsDown;
    bool rsLeft;
    bool rsRight;
    bool prevRsUp;
    bool prevRsDown;
    bool prevRsLeft;
    bool prevRsRight;
};

typedef DWORD(WINAPI *XInputGetStateProc)(DWORD, XINPUT_STATE *);

struct DemoAssets {
    std::wstring root;
    std::vector<AssetImage> wials;
    std::vector<AssetImage> combatFx;
    std::vector<AssetImage> ambientFx;
    std::vector<AssetImage> farm;
    std::vector<AssetImage> cooking;
    std::vector<AssetImage> enemies;
    std::vector<AssetImage> combatAnims;
    std::vector<AssetImage> cookingSim;
    std::vector<AssetImage> navigation[6];
};

enum CombatActionType {
    COMBAT_LIGHT = 0,
    COMBAT_HEAVY,
    COMBAT_SPECIAL,
    COMBAT_DEFEND,
    COMBAT_PARRY,
    COMBAT_DODGE,
};

struct CombatStats {
    int speed;
    int strength;
    int defense;
    int virility;
    int sagess;
    int nimbility;
    int balance;
};

enum EnemyArchetype {
    ARCHETYPE_BRUTE = 0,
    ARCHETYPE_NIMBLE,
    ARCHETYPE_TANK,
    ARCHETYPE_MYSTIC,
    ARCHETYPE_CHAOS,
    ARCHETYPE_COUNT,
};

struct ArchetypeProfile {
    float slowmoWindow;
    int precisionDie;
    int aimDie;
    int evadeDie;
    int parryBonus;
    int dodgeBonus;
    float specialMulti;
    int hitLocClampLo;
    int hitLocClampHi;
    int balanceSwingDie;
};

struct CombatEntity {
    const wchar_t *name;
    CombatStats stats;
    float health;
    float stamina;
    CombatActionType queuedAction;
    int initiative;
    EnemyArchetype archetype;
};

struct CookingIngredient {
    const wchar_t *name;
    float quantity;
    float quality;
    float cookness;
    float temperature;
    float moisture;
    float healthiness;
};

struct CookingState {
    bool active;
    float cauldronTemp;
    float fireIntensity;
    float stirRate;
    float totalCookTime;
    int selectedSlot;
    int recipeStage;
    CookingIngredient slots[6];
    float dishQuality;
    float dishHealthiness;
    wchar_t statusLine[160];
    wchar_t resultLine[160];
};

struct DemoState {
    HWND window;
    DemoMode mode;
    DemoMode prePauseMode;
    bool running;
    bool autoShowcase;
    float modeTimer;
    float assetTimer;
    int modeCursor;

    int currentEnvironment;
    int currentNavView;
    int currentEnemy;
    int currentCombatFx;
    int currentAmbientFx;
    int currentFarm;
    int currentCooking;
    int currentWial;
    int currentCombatAnim;
    int currentCookingSim;

    float playerHealth;
    float playerStamina;
    float enemyHealth;

    bool combatInitialized;
    bool combatRoundActive;
    bool combatSlowmo;
    float combatSlowmoTimer;
    float combatExecutionTimer;
    int combatExecutionStep;
    int combatOrder[2];
    int combatRoundIndex;
    int rngState;

    CombatEntity playerCombat;
    CombatEntity enemyCombat;
    CombatActionType selectedPlayerAction;
    CombatActionType telegraphedEnemyAction;

    wchar_t combatTelegraph[160];
    wchar_t combatLastLog[240];

    CookingState cook;

    bool keyDown[256];
    bool keyPressed[256];
    bool keyReleased[256];

    ControllerState controller;
    HMODULE xinputModule;
    XInputGetStateProc xinputGetState;

    ULONG_PTR gdiplusToken;
    DemoAssets assets;
};

DemoState g_demo = {};

const wchar_t *kEnvironmentNames[6] = {
    L"gloom_caverns",
    L"sunken_temple",
    L"mausoleum",
    L"sewer",
    L"frost_cavern",
    L"cyber_tunnels",
};

const wchar_t *kModeNames[] = {
    L"Title",
    L"Navigation",
    L"Combat",
    L"Farm",
    L"Cooking",
    L"Evolution",
    L"Stats",
    L"Pause",
};

const wchar_t *kCombatActionNames[] = {
    L"Light",
    L"Heavy",
    L"Special",
    L"Defend",
    L"Parry",
    L"Dodge",
};

int wrapIndex(int value, int count);

const ArchetypeProfile kArchetypes[ARCHETYPE_COUNT] = {
    // BRUTE: wide hit location, short window, heavy hitter
    {0.70f, 24, 16, 14, 2, 3, 1.10f, -6, 12, 16},
    // NIMBLE: tight evasion, longer window, precision evader
    {1.10f, 16, 24, 24, 4, 8, 1.05f, -3, 6, 12},
    // TANK: absurd defense, short window, immovable
    {0.65f, 20, 18, 12, 6, 2, 0.95f, -8, 14, 10},
    // MYSTIC: special-heavy, medium window, sagess-driven
    {0.95f, 18, 20, 16, 3, 5, 1.55f, -5, 10, 14},
    // CHAOS: wildly random, ultra-swingy precision
    {0.85f, 30, 30, 30, 1, 1, 1.30f, -10, 16, 24},
};

const wchar_t *kArchetypeNames[] = {
    L"Brute", L"Nimble", L"Tank", L"Mystic", L"Chaos",
};

EnemyArchetype archetypeFromSeed(int seed) {
    return (EnemyArchetype)(((unsigned int)(seed * 7 + 13)) % ARCHETYPE_COUNT);
}

void drawTextLine(HDC hdc, int x, int y, COLORREF color, const wchar_t *text) {
    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, color);
    TextOutW(hdc, x, y, text, (int)wcslen(text));
}

void fillRect(HDC hdc, int left, int top, int right, int bottom, COLORREF color) {
    RECT rect = {left, top, right, bottom};
    HBRUSH brush = CreateSolidBrush(color);
    FillRect(hdc, &rect, brush);
    DeleteObject(brush);
}

void drawGauge(HDC hdc, int x, int y, int width, int height, float ratio, COLORREF fill, const wchar_t *label) {
    ratio = std::max(0.0f, std::min(1.0f, ratio));
    fillRect(hdc, x, y, x + width, y + height, RGB(35, 38, 42));
    int fillWidth = (int)(ratio * (float)width);
    fillRect(hdc, x, y, x + fillWidth, y + height, fill);
    RECT border = {x, y, x + width, y + height};
    FrameRect(hdc, &border, (HBRUSH)GetStockObject(WHITE_BRUSH));

    wchar_t buf[128];
    swprintf(buf, 128, L"%ls: %d%%", label, (int)(ratio * 100.0f));
    drawTextLine(hdc, x + 6, y + 4, RGB(250, 250, 250), buf);
}

std::wstring joinPath(const std::wstring &a, const std::wstring &b) {
    if (a.empty()) return b;
    if (a.back() == L'\\') return a + b;
    return a + L"\\" + b;
}

bool directoryExists(const std::wstring &path) {
    DWORD attr = GetFileAttributesW(path.c_str());
    return attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY) != 0;
}

std::vector<std::wstring> listPngFiles(const std::wstring &directory) {
    std::vector<std::wstring> files;
    std::wstring pattern = joinPath(directory, L"*.png");

    WIN32_FIND_DATAW findData;
    HANDLE handle = FindFirstFileW(pattern.c_str(), &findData);
    if (handle == INVALID_HANDLE_VALUE) {
        return files;
    }

    do {
        if ((findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) == 0) {
            files.push_back(joinPath(directory, findData.cFileName));
        }
    } while (FindNextFileW(handle, &findData));
    FindClose(handle);

    std::sort(files.begin(), files.end());
    return files;
}

Image *loadImage(const std::wstring &path) {
    Image *image = new Image(path.c_str());
    if (image->GetLastStatus() != Ok) {
        delete image;
        return NULL;
    }
    return image;
}

void loadAssetFolder(const std::wstring &folder, std::vector<AssetImage> &out) {
    std::vector<std::wstring> files = listPngFiles(folder);
    for (size_t i = 0; i < files.size(); ++i) {
        Image *img = loadImage(files[i]);
        if (img != NULL) {
            out.push_back({files[i], img});
        }
    }
}

void freeAssetList(std::vector<AssetImage> &list) {
    for (size_t i = 0; i < list.size(); ++i) {
        delete list[i].image;
        list[i].image = NULL;
    }
    list.clear();
}

void freeAssets(DemoAssets &assets) {
    freeAssetList(assets.wials);
    freeAssetList(assets.combatFx);
    freeAssetList(assets.ambientFx);
    freeAssetList(assets.farm);
    freeAssetList(assets.cooking);
    freeAssetList(assets.enemies);
    freeAssetList(assets.combatAnims);
    freeAssetList(assets.cookingSim);
    for (int i = 0; i < 6; ++i) {
        freeAssetList(assets.navigation[i]);
    }
}

int totalAssetsLoaded(const DemoAssets &assets) {
    int total = 0;
    total += (int)assets.wials.size();
    total += (int)assets.combatFx.size();
    total += (int)assets.ambientFx.size();
    total += (int)assets.farm.size();
    total += (int)assets.cooking.size();
    total += (int)assets.enemies.size();
    total += (int)assets.combatAnims.size();
    total += (int)assets.cookingSim.size();
    for (int i = 0; i < 6; ++i) {
        total += (int)assets.navigation[i].size();
    }
    return total;
}

void discoverAndLoadAssets(DemoAssets &assets) {
    const wchar_t *roots[] = {
        L"assets\\wial_wohm",
        L"ORBEngine\\assets\\wial_wohm",
        L"..\\ORBEngine\\assets\\wial_wohm",
        L"..\\assets\\wial_wohm",
    };

    assets.root.clear();
    for (size_t i = 0; i < sizeof(roots) / sizeof(roots[0]); ++i) {
        if (directoryExists(roots[i])) {
            assets.root = roots[i];
            break;
        }
    }

    if (assets.root.empty()) {
        return;
    }

    loadAssetFolder(joinPath(assets.root, L"wials"), assets.wials);
    loadAssetFolder(joinPath(assets.root, L"combat_fx"), assets.combatFx);
    loadAssetFolder(joinPath(assets.root, L"ambient_fx"), assets.ambientFx);
    loadAssetFolder(joinPath(assets.root, L"farm"), assets.farm);
    loadAssetFolder(joinPath(assets.root, L"cooking"), assets.cooking);
    loadAssetFolder(joinPath(assets.root, L"enemies"), assets.enemies);
    loadAssetFolder(joinPath(assets.root, L"combat_anims"), assets.combatAnims);
    loadAssetFolder(joinPath(assets.root, L"cooking_sim"), assets.cookingSim);

    std::wstring navRoot = joinPath(assets.root, L"navigation");
    for (int i = 0; i < 6; ++i) {
        loadAssetFolder(joinPath(navRoot, kEnvironmentNames[i]), assets.navigation[i]);
    }
}

void drawImageAlpha(Graphics &graphics, Image *image, int x, int y, int width, int height, float alpha) {
    if (image == NULL) return;
    alpha = std::max(0.0f, std::min(1.0f, alpha));

    ColorMatrix matrix = {
        1.0f, 0, 0, 0, 0,
        0, 1.0f, 0, 0, 0,
        0, 0, 1.0f, 0, 0,
        0, 0, 0, alpha, 0,
        0, 0, 0, 0, 1.0f,
    };

    ImageAttributes attrs;
    attrs.SetColorMatrix(&matrix, ColorMatrixFlagsDefault, ColorAdjustTypeBitmap);

    Rect dest(x, y, width, height);
    graphics.DrawImage(image, dest, 0, 0, image->GetWidth(), image->GetHeight(), UnitPixel, &attrs);
}

void drawPrimaryImage(Graphics &graphics, const std::vector<AssetImage> &list, int index, int x, int y, int width, int height, float alpha) {
    if (list.empty()) return;
    int safe = index % (int)list.size();
    if (safe < 0) safe += (int)list.size();
    drawImageAlpha(graphics, list[safe].image, x, y, width, height, alpha);
}

float normalizeAxis(SHORT value, SHORT deadzone) {
    float normalized = 0.0f;
    if (value > deadzone) {
        normalized = (float)(value - deadzone) / (32767.0f - (float)deadzone);
    } else if (value < -deadzone) {
        normalized = (float)(value + deadzone) / (32768.0f - (float)deadzone);
    }
    if (normalized > 1.0f) normalized = 1.0f;
    if (normalized < -1.0f) normalized = -1.0f;
    return normalized;
}

float normalizeTrigger(BYTE value) {
    const float threshold = 30.0f;
    if ((float)value <= threshold) return 0.0f;
    return ((float)value - threshold) / (255.0f - threshold);
}

void loadXInput(DemoState &state) {
    const wchar_t *dlls[] = {L"xinput1_4.dll", L"xinput1_3.dll", L"xinput9_1_0.dll"};
    state.xinputModule = NULL;
    state.xinputGetState = NULL;

    for (size_t i = 0; i < sizeof(dlls) / sizeof(dlls[0]); ++i) {
        HMODULE module = LoadLibraryW(dlls[i]);
        if (module != NULL) {
            FARPROC proc = GetProcAddress(module, "XInputGetState");
            if (proc != NULL) {
                state.xinputModule = module;
                state.xinputGetState = (XInputGetStateProc)proc;
                return;
            }
            FreeLibrary(module);
        }
    }
}

void pollController(DemoState &state) {
    ControllerState &controller = state.controller;
    controller.previousButtons = controller.buttons;

    controller.prevLsUp = controller.lsUp;
    controller.prevLsDown = controller.lsDown;
    controller.prevLsLeft = controller.lsLeft;
    controller.prevLsRight = controller.lsRight;
    controller.prevRsUp = controller.rsUp;
    controller.prevRsDown = controller.rsDown;
    controller.prevRsLeft = controller.rsLeft;
    controller.prevRsRight = controller.rsRight;

    if (state.xinputGetState == NULL) {
        controller.connected = false;
        controller.buttons = 0;
        return;
    }

    XINPUT_STATE xstate = {};
    DWORD result = state.xinputGetState(0, &xstate);
    if (result != ERROR_SUCCESS) {
        controller.connected = false;
        controller.buttons = 0;
        controller.lx = controller.ly = controller.rx = controller.ry = 0.0f;
        controller.lt = controller.rt = 0.0f;
        controller.lsUp = controller.lsDown = controller.lsLeft = controller.lsRight = false;
        controller.rsUp = controller.rsDown = controller.rsLeft = controller.rsRight = false;
        return;
    }

    controller.connected = true;
    controller.buttons = xstate.Gamepad.wButtons;
    controller.lx = normalizeAxis(xstate.Gamepad.sThumbLX, XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE);
    controller.ly = normalizeAxis(xstate.Gamepad.sThumbLY, XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE);
    controller.rx = normalizeAxis(xstate.Gamepad.sThumbRX, XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE);
    controller.ry = normalizeAxis(xstate.Gamepad.sThumbRY, XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE);
    controller.lt = normalizeTrigger(xstate.Gamepad.bLeftTrigger);
    controller.rt = normalizeTrigger(xstate.Gamepad.bRightTrigger);

    controller.lsUp = controller.ly > 0.55f;
    controller.lsDown = controller.ly < -0.55f;
    controller.lsLeft = controller.lx < -0.55f;
    controller.lsRight = controller.lx > 0.55f;

    controller.rsUp = controller.ry > 0.55f;
    controller.rsDown = controller.ry < -0.55f;
    controller.rsLeft = controller.rx < -0.55f;
    controller.rsRight = controller.rx > 0.55f;
}

bool controllerPressed(const ControllerState &controller, WORD mask) {
    return (controller.buttons & mask) != 0 && (controller.previousButtons & mask) == 0;
}

bool keyPressed(int virtualKey) {
    return virtualKey >= 0 && virtualKey < 256 && g_demo.keyPressed[virtualKey];
}

bool keyDown(int virtualKey) {
    return virtualKey >= 0 && virtualKey < 256 && g_demo.keyDown[virtualKey];
}

int nextRandomInt(DemoState &state, int maxExclusive) {
    if (maxExclusive <= 1) return 0;
    state.rngState = state.rngState * 1664525 + 1013904223;
    unsigned int value = (unsigned int)state.rngState;
    return (int)(value % (unsigned int)maxExclusive);
}

int rollDie(DemoState &state, int sides) {
    return 1 + nextRandomInt(state, sides);
}

int rollStatCheck(DemoState &state, int statA, int statB, int swingDie) {
    return (statA + rollDie(state, swingDie)) - (statB + rollDie(state, swingDie));
}

CombatActionType chooseEnemyAction(DemoState &state) {
    int tactical = state.enemyCombat.stats.sagess + rollDie(state, 8);
    int pressure = state.enemyCombat.stats.strength + rollDie(state, 6);
    int survival = state.enemyCombat.stats.defense + state.enemyCombat.stats.balance + rollDie(state, 6);

    if (state.enemyCombat.stamina < 0.20f && tactical > survival) {
        return COMBAT_DEFEND;
    }
    if (state.playerCombat.stamina < 0.25f && tactical > pressure) {
        return COMBAT_PARRY;
    }
    if (pressure > tactical + 3) {
        return (rollDie(state, 2) == 1) ? COMBAT_HEAVY : COMBAT_LIGHT;
    }
    if (tactical > pressure + 2 && state.enemyCombat.stamina > 0.25f) {
        return COMBAT_SPECIAL;
    }

    int mode = rollDie(state, 6);
    if (mode == 1) return COMBAT_DODGE;
    if (mode == 2) return COMBAT_PARRY;
    return COMBAT_LIGHT;
}

void combatSyncGauges(DemoState &state) {
    state.playerHealth = std::max(0.0f, std::min(1.0f, state.playerCombat.health));
    state.playerStamina = std::max(0.0f, std::min(1.0f, state.playerCombat.stamina));
    state.enemyHealth = std::max(0.0f, std::min(1.0f, state.enemyCombat.health));
}

float staminaCostForAction(CombatActionType action) {
    if (action == COMBAT_HEAVY) return 0.16f;
    if (action == COMBAT_SPECIAL) return 0.20f;
    if (action == COMBAT_DODGE) return 0.12f;
    if (action == COMBAT_PARRY) return 0.10f;
    if (action == COMBAT_DEFEND) return 0.06f;
    return 0.08f;
}

void setupCombatForEnemy(DemoState &state) {
    int enemySeed = state.currentEnemy + 7;

    state.playerCombat.name = L"Player Wial";
    state.playerCombat.stats = {14, 12, 11, 13, 10, 12, 11};
    state.playerCombat.health = std::max(0.40f, state.playerHealth);
    state.playerCombat.stamina = std::max(0.35f, state.playerStamina);
    state.playerCombat.queuedAction = COMBAT_LIGHT;
    state.playerCombat.archetype = ARCHETYPE_NIMBLE;

    state.enemyCombat.name = L"Enemy Wohm";
    state.enemyCombat.archetype = archetypeFromSeed(enemySeed);
    const ArchetypeProfile &arch = kArchetypes[(int)state.enemyCombat.archetype];

    state.enemyCombat.stats.speed = 10 + (enemySeed % 6);
    state.enemyCombat.stats.strength = 10 + ((enemySeed * 3) % 7);
    state.enemyCombat.stats.defense = 9 + ((enemySeed * 5) % 7);
    state.enemyCombat.stats.virility = 11 + ((enemySeed * 7) % 6);
    state.enemyCombat.stats.sagess = 8 + ((enemySeed * 11) % 8);
    state.enemyCombat.stats.nimbility = 9 + ((enemySeed * 13) % 8);
    state.enemyCombat.stats.balance = 9 + ((enemySeed * 17) % 7);

    // Archetype stat tweaks
    if (state.enemyCombat.archetype == ARCHETYPE_BRUTE) {
        state.enemyCombat.stats.strength += 4;
        state.enemyCombat.stats.nimbility -= 2;
    } else if (state.enemyCombat.archetype == ARCHETYPE_NIMBLE) {
        state.enemyCombat.stats.nimbility += 5;
        state.enemyCombat.stats.speed += 3;
        state.enemyCombat.stats.strength -= 2;
    } else if (state.enemyCombat.archetype == ARCHETYPE_TANK) {
        state.enemyCombat.stats.defense += 5;
        state.enemyCombat.stats.balance += 3;
        state.enemyCombat.stats.speed -= 3;
    } else if (state.enemyCombat.archetype == ARCHETYPE_MYSTIC) {
        state.enemyCombat.stats.sagess += 6;
        state.enemyCombat.stats.defense -= 2;
    } else if (state.enemyCombat.archetype == ARCHETYPE_CHAOS) {
        // Chaos: random stat perturbations
        state.enemyCombat.stats.speed += rollDie(state, 6) - 3;
        state.enemyCombat.stats.strength += rollDie(state, 8) - 4;
        state.enemyCombat.stats.nimbility += rollDie(state, 10) - 5;
        state.enemyCombat.stats.balance += rollDie(state, 10) - 5;
    }

    state.enemyCombat.health = 1.0f;
    state.enemyCombat.stamina = 1.0f;
    state.enemyCombat.queuedAction = COMBAT_LIGHT;

    state.selectedPlayerAction = COMBAT_LIGHT;
    state.telegraphedEnemyAction = COMBAT_LIGHT;
    state.combatRoundActive = false;
    state.combatSlowmo = false;
    state.combatSlowmoTimer = 0.0f;
    state.combatExecutionTimer = 0.0f;
    state.combatExecutionStep = 0;
    state.combatRoundIndex = 0;
    swprintf(state.combatLastLog, 240, L"Combat initialized vs %ls. Awaiting telegraph.",
        kArchetypeNames[(int)state.enemyCombat.archetype]);
    swprintf(state.combatTelegraph, 160, L"%ls enemy studies your stance.",
        kArchetypeNames[(int)state.enemyCombat.archetype]);
    combatSyncGauges(state);
}

void prepareCombatRound(DemoState &state) {
    state.enemyCombat.queuedAction = chooseEnemyAction(state);
    state.telegraphedEnemyAction = state.enemyCombat.queuedAction;

    const ArchetypeProfile &arch = kArchetypes[(int)state.enemyCombat.archetype];

    swprintf(state.combatTelegraph, 160, L"%ls %ls telegraph: %ls",
        kArchetypeNames[(int)state.enemyCombat.archetype],
        state.enemyCombat.name,
        kCombatActionNames[(int)state.telegraphedEnemyAction]);
    state.combatSlowmo = true;
    // Archetype-varied window: Chaos enemies add a random jitter
    float windowJitter = 0.0f;
    if (state.enemyCombat.archetype == ARCHETYPE_CHAOS) {
        windowJitter = (float)(rollDie(state, 40) - 20) / 100.0f;
    }
    state.combatSlowmoTimer = arch.slowmoWindow + windowJitter;
    state.combatRoundActive = true;
    state.combatExecutionStep = 0;
    state.combatExecutionTimer = 0.0f;
}

int rollInitiative(DemoState &state, const CombatEntity &entity) {
    int speedRoll = entity.stats.speed + rollDie(state, 20);
    int nimbleRoll = entity.stats.nimbility + rollDie(state, 12);
    int balanceRoll = entity.stats.balance + rollDie(state, 10);
    return speedRoll + (nimbleRoll / 2) + (balanceRoll / 3);
}

void finalizeSelectionAndQueue(DemoState &state) {
    state.playerCombat.queuedAction = state.selectedPlayerAction;
    state.playerCombat.initiative = rollInitiative(state, state.playerCombat);
    state.enemyCombat.initiative = rollInitiative(state, state.enemyCombat);

    if (state.playerCombat.initiative >= state.enemyCombat.initiative) {
        state.combatOrder[0] = 0;
        state.combatOrder[1] = 1;
    } else {
        state.combatOrder[0] = 1;
        state.combatOrder[1] = 0;
    }

    state.combatSlowmo = false;
    state.combatExecutionStep = 0;
    state.combatExecutionTimer = 0.0f;
    ++state.combatRoundIndex;
    swprintf(state.combatLastLog, 240, L"Round %d queue: %ls then %ls", state.combatRoundIndex,
        state.combatOrder[0] == 0 ? state.playerCombat.name : state.enemyCombat.name,
        state.combatOrder[1] == 0 ? state.playerCombat.name : state.enemyCombat.name);
}

void applyActionResolution(
    DemoState &state,
    CombatEntity &attacker,
    CombatEntity &defender,
    CombatActionType attackAction,
    CombatActionType defenderAction,
    bool attackerIsPlayer) {

    float cost = staminaCostForAction(attackAction);
    attacker.stamina = std::max(0.0f, attacker.stamina - cost);

    if (attackAction == COMBAT_DEFEND || attackAction == COMBAT_PARRY || attackAction == COMBAT_DODGE) {
        swprintf(state.combatLastLog, 240, L"%ls commits to %ls.", attacker.name, kCombatActionNames[(int)attackAction]);
        return;
    }

    const ArchetypeProfile &atkArch = kArchetypes[(int)attacker.archetype];
    const ArchetypeProfile &defArch = kArchetypes[(int)defender.archetype];

    int attackRoll = attacker.stats.strength + attacker.stats.balance + rollDie(state, 20);
    int aimRoll = attacker.stats.nimbility + rollDie(state, atkArch.aimDie);
    int evadeRoll = defender.stats.nimbility + rollDie(state, defArch.evadeDie);
    int defenseRoll = defender.stats.defense + defender.stats.balance + rollDie(state, 20);

    if (defenderAction == COMBAT_DODGE) {
        evadeRoll += defArch.dodgeBonus + defender.stats.balance / 2;
    }
    if (defenderAction == COMBAT_DEFEND) {
        defenseRoll += 7 + defender.stats.defense / 2;
    }
    if (defenderAction == COMBAT_PARRY) {
        int parryRoll = defender.stats.balance + defender.stats.nimbility + rollDie(state, 20);
        parryRoll += defArch.parryBonus;
        if (parryRoll > attackRoll + 2) {
            attacker.stamina = std::max(0.0f, attacker.stamina - 0.14f);
            swprintf(state.combatLastLog, 240, L"%ls parries %ls and staggers them.", defender.name, attacker.name);
            return;
        }
    }

    if (aimRoll < evadeRoll) {
        swprintf(state.combatLastLog, 240, L"%ls misses (%ls evades).", attacker.name, defender.name);
        return;
    }

    int specialBoost = 0;
    if (attackAction == COMBAT_HEAVY) {
        specialBoost += 5;
    } else if (attackAction == COMBAT_SPECIAL) {
        specialBoost += (int)(((float)attacker.stats.sagess + (float)rollDie(state, 10)) * atkArch.specialMulti) + 3;
    }

    int impact = attackRoll + specialBoost;
    int mitigation = defenseRoll;

    // Archetype-driven hit location precision: swingy!
    int precisionRoll = attacker.stats.nimbility + attacker.stats.balance + rollDie(state, atkArch.precisionDie);
    int defenderLocationDef = defender.stats.balance + rollDie(state, defArch.balanceSwingDie);
    int rawLocShift = (precisionRoll - defenderLocationDef) / 3;
    int hitLocationShift = std::max(atkArch.hitLocClampLo, std::min(atkArch.hitLocClampHi, rawLocShift));

    int rawDamage = impact - (mitigation / 2) + hitLocationShift;
    if (attackAction == COMBAT_LIGHT) rawDamage += 1;
    if (attackAction == COMBAT_HEAVY) rawDamage += 3;
    if (attackAction == COMBAT_SPECIAL) rawDamage += attacker.stats.sagess / 2;

    float damage = (float)std::max(1, rawDamage) / 40.0f;
    if (attackAction == COMBAT_HEAVY) damage *= 1.30f;
    if (attackAction == COMBAT_SPECIAL) damage *= 1.35f;

    defender.health = std::max(0.0f, defender.health - damage);
    defender.stamina = std::max(0.0f, defender.stamina - damage * 0.5f);

    if (attackAction == COMBAT_SPECIAL) {
        attacker.stamina = std::max(0.0f, attacker.stamina - 0.06f);
    }

    state.currentCombatFx = wrapIndex(state.currentCombatFx + 1 + rollDie(state, 3), (int)state.assets.combatFx.size());
    state.currentAmbientFx = wrapIndex(state.currentAmbientFx + 1, (int)state.assets.ambientFx.size());
    if (!state.assets.combatAnims.empty()) {
        state.currentCombatAnim = wrapIndex(state.currentCombatAnim + 1 + (int)attackAction, (int)state.assets.combatAnims.size());
    }

    swprintf(state.combatLastLog, 240, L"%ls uses %ls for %.0f%% dmg (loc:%+d).",
        attacker.name,
        kCombatActionNames[(int)attackAction],
        damage * 100.0f,
        hitLocationShift);

    (void)attackerIsPlayer;
}

void initCookingSession(DemoState &state) {
    CookingState &ck = state.cook;
    ck.active = true;
    ck.cauldronTemp = 20.0f;
    ck.fireIntensity = 0.5f;
    ck.stirRate = 0.0f;
    ck.totalCookTime = 0.0f;
    ck.selectedSlot = 0;
    ck.recipeStage = 0;
    ck.dishQuality = 0.0f;
    ck.dishHealthiness = 0.0f;

    const wchar_t *ingredientNames[] = {
        L"Root Mash", L"Cave Mushroom", L"Swamp Fish",
        L"Dark Meat", L"Ember Grain", L"Wohm Herb"
    };

    for (int i = 0; i < 6; ++i) {
        ck.slots[i].name = ingredientNames[i];
        ck.slots[i].quantity = 0.30f + (float)(((state.currentCooking + i) * 37) % 50) / 100.0f;
        ck.slots[i].quality = 0.40f + (float)(((state.currentCooking + i) * 53) % 45) / 100.0f;
        ck.slots[i].cookness = 0.0f;
        ck.slots[i].temperature = 20.0f;
        ck.slots[i].moisture = 0.50f + (float)(((state.currentCooking + i) * 19) % 40) / 100.0f;
        ck.slots[i].healthiness = 0.60f + (float)(((state.currentCooking + i) * 29) % 30) / 100.0f;
    }
    swprintf(ck.statusLine, 160, L"Eggshell cauldron ready. Adjust fire and stir.");
    swprintf(ck.resultLine, 160, L"Add ingredients, manage heat, stir to cook.");
}

void updateCookingSimulation(DemoState &state, float dt) {
    CookingState &ck = state.cook;
    if (!ck.active) return;

    ck.totalCookTime += dt;

    // Fire heats the cauldron
    float targetTemp = 20.0f + ck.fireIntensity * 200.0f;
    float heatRate = 0.6f + ck.fireIntensity * 0.4f;
    if (ck.cauldronTemp < targetTemp) {
        ck.cauldronTemp += heatRate * dt * 40.0f;
        if (ck.cauldronTemp > targetTemp) ck.cauldronTemp = targetTemp;
    } else {
        ck.cauldronTemp -= 0.3f * dt * 30.0f;
        if (ck.cauldronTemp < targetTemp) ck.cauldronTemp = targetTemp;
    }

    // Simulate each ingredient
    for (int i = 0; i < 6; ++i) {
        CookingIngredient &ing = ck.slots[i];
        if (ing.quantity <= 0.0f) continue;

        // Temperature transfer from cauldron
        float tempDelta = (ck.cauldronTemp - ing.temperature) * 0.25f * dt;
        ing.temperature += tempDelta;

        // Cooking progress: depends on temp being in sweet spot (80-160)
        float cookSpeed = 0.0f;
        if (ing.temperature > 80.0f && ing.temperature < 160.0f) {
            cookSpeed = (ing.temperature - 60.0f) / 300.0f;
        } else if (ing.temperature >= 160.0f) {
            cookSpeed = 0.3f; // fast but risky
        }
        if (ck.stirRate > 0.0f) cookSpeed *= (1.0f + ck.stirRate * 0.5f);
        ing.cookness = std::min(1.0f, ing.cookness + cookSpeed * dt);

        // Moisture loss: higher temps evaporate moisture
        float moistureLoss = (ing.temperature / 600.0f) * dt;
        if (ck.stirRate > 0.3f) moistureLoss *= 0.7f; // stirring retains moisture
        ing.moisture = std::max(0.0f, ing.moisture - moistureLoss);

        // Quality degrades if overcooked or over-dried
        if (ing.cookness > 0.85f) {
            ing.quality -= 0.04f * dt;
        }
        if (ing.moisture < 0.1f) {
            ing.quality -= 0.06f * dt;
        }
        if (ing.temperature > 180.0f) {
            ing.quality -= 0.10f * dt; // burning
            ing.healthiness -= 0.08f * dt;
        }
        ing.quality = std::max(0.0f, std::min(1.0f, ing.quality));

        // Healthiness: stirring at good temp improves; overcooking degrades
        if (ing.temperature > 70.0f && ing.temperature < 140.0f && ck.stirRate > 0.2f) {
            ing.healthiness = std::min(1.0f, ing.healthiness + 0.012f * dt);
        }
        ing.healthiness = std::max(0.0f, std::min(1.0f, ing.healthiness));

        // Quantity slowly reduces as cooking concentrates
        if (ing.cookness > 0.3f) {
            ing.quantity = std::max(0.05f, ing.quantity - 0.002f * dt);
        }
    }

    // Stir decays if not actively stirring
    ck.stirRate = std::max(0.0f, ck.stirRate - 0.4f * dt);

    // Calculate dish outputs
    float totalQ = 0.0f, totalH = 0.0f, totalC = 0.0f;
    int activeCount = 0;
    for (int i = 0; i < 6; ++i) {
        if (ck.slots[i].quantity > 0.0f) {
            totalQ += ck.slots[i].quality;
            totalH += ck.slots[i].healthiness;
            totalC += ck.slots[i].cookness;
            ++activeCount;
        }
    }
    if (activeCount > 0) {
        ck.dishQuality = totalQ / (float)activeCount;
        ck.dishHealthiness = totalH / (float)activeCount;
    }

    float avgCookness = activeCount > 0 ? totalC / (float)activeCount : 0.0f;

    if (avgCookness > 0.65f && avgCookness < 0.90f) {
        swprintf(ck.statusLine, 160, L"Cooking well! Quality:%.0f%% Health:%.0f%%",
            ck.dishQuality * 100.0f, ck.dishHealthiness * 100.0f);
    } else if (avgCookness >= 0.90f) {
        swprintf(ck.statusLine, 160, L"Careful! Overcooking risk! Q:%.0f%% H:%.0f%%",
            ck.dishQuality * 100.0f, ck.dishHealthiness * 100.0f);
    } else {
        swprintf(ck.statusLine, 160, L"Still raw... Temp:%.0fC Fire:%.0f%%",
            ck.cauldronTemp, ck.fireIntensity * 100.0f);
    }
}

void finishCooking(DemoState &state) {
    CookingState &ck = state.cook;
    // Apply dish to player health/stamina
    float healthGain = ck.dishHealthiness * 0.15f;
    float staminaGain = ck.dishQuality * 0.12f;
    state.playerHealth = std::min(1.0f, state.playerHealth + healthGain);
    state.playerStamina = std::min(1.0f, state.playerStamina + staminaGain);
    swprintf(ck.resultLine, 160, L"Dish served! +%.0f%% HP +%.0f%% STA (Q:%.0f%% H:%.0f%%)",
        healthGain * 100.0f, staminaGain * 100.0f,
        ck.dishQuality * 100.0f, ck.dishHealthiness * 100.0f);
    ck.active = false;
}

void clearTransientInput(DemoState &state) {
    for (int i = 0; i < 256; ++i) {
        state.keyPressed[i] = false;
        state.keyReleased[i] = false;
    }
}

int wrapIndex(int value, int count) {
    if (count <= 0) return 0;
    int result = value % count;
    if (result < 0) result += count;
    return result;
}

void changeMode(DemoState &state, DemoMode newMode) {
    state.mode = newMode;
    state.modeTimer = 0.0f;
    if (newMode == MODE_COMBAT) {
        state.combatInitialized = false;
    }
    if (newMode == MODE_COOKING) {
        state.cook.active = false;
    }
}

void cycleMainMode(DemoState &state, int direction) {
    DemoMode modes[] = {
        MODE_NAVIGATION,
        MODE_COMBAT,
        MODE_FARM,
        MODE_COOKING,
        MODE_EVOLUTION,
        MODE_STATS,
    };
    int count = (int)(sizeof(modes) / sizeof(modes[0]));
    state.modeCursor = wrapIndex(state.modeCursor + direction, count);
    changeMode(state, modes[state.modeCursor]);
}

void updateShowcase(DemoState &state, float dt) {
    state.assetTimer += dt;
    if (state.assetTimer < 1.2f) return;
    state.assetTimer = 0.0f;

    if (state.mode == MODE_NAVIGATION) {
        int envCount = 6;
        state.currentNavView++;
        int viewCount = (int)state.assets.navigation[state.currentEnvironment].size();
        if (viewCount > 0 && state.currentNavView >= viewCount) {
            state.currentNavView = 0;
            state.currentEnvironment = wrapIndex(state.currentEnvironment + 1, envCount);
        }
        state.currentAmbientFx = wrapIndex(state.currentAmbientFx + 1, (int)state.assets.ambientFx.size());
    } else if (state.mode == MODE_COMBAT) {
        state.currentEnemy = wrapIndex(state.currentEnemy + 1, (int)state.assets.enemies.size());
        state.currentCombatFx = wrapIndex(state.currentCombatFx + 1, (int)state.assets.combatFx.size());
        state.enemyHealth = std::max(0.0f, state.enemyHealth - 0.08f);
        if (state.enemyHealth <= 0.0f) state.enemyHealth = 1.0f;
    } else if (state.mode == MODE_FARM) {
        state.currentFarm = wrapIndex(state.currentFarm + 1, (int)state.assets.farm.size());
    } else if (state.mode == MODE_COOKING) {
        state.currentCooking = wrapIndex(state.currentCooking + 1, (int)state.assets.cooking.size());
    } else if (state.mode == MODE_EVOLUTION) {
        state.currentWial = wrapIndex(state.currentWial + 1, (int)state.assets.wials.size());
    }

    if (!state.autoShowcase) {
        return;
    }

    state.modeTimer += dt;
    if (state.modeTimer > 7.0f && state.mode != MODE_PAUSE && state.mode != MODE_TITLE) {
        cycleMainMode(state, +1);
    }
}

void updateGameplay(float dt) {
    DemoState &state = g_demo;
    pollController(state);
    ControllerState &pad = state.controller;

    if (keyPressed(VK_ESCAPE) || controllerPressed(pad, XINPUT_GAMEPAD_START)) {
        if (state.mode == MODE_PAUSE) {
            changeMode(state, state.prePauseMode);
        } else {
            state.prePauseMode = state.mode;
            changeMode(state, MODE_PAUSE);
        }
    }

    if (keyPressed('P') || controllerPressed(pad, XINPUT_GAMEPAD_BACK)) {
        changeMode(state, MODE_TITLE);
    }

    if (keyPressed('T')) {
        state.autoShowcase = !state.autoShowcase;
    }

    if (state.mode == MODE_TITLE) {
        if (keyPressed(VK_RETURN) || keyPressed(VK_SPACE) || controllerPressed(pad, XINPUT_GAMEPAD_A)) {
            changeMode(state, MODE_NAVIGATION);
        }
        clearTransientInput(state);
        return;
    }

    if (state.mode == MODE_PAUSE) {
        clearTransientInput(state);
        return;
    }

    bool nextMode = keyPressed(VK_OEM_PERIOD) || keyPressed('E') || controllerPressed(pad, XINPUT_GAMEPAD_RIGHT_SHOULDER);
    bool prevMode = keyPressed(VK_OEM_COMMA) || keyPressed('Q') || controllerPressed(pad, XINPUT_GAMEPAD_LEFT_SHOULDER);
    if (nextMode) cycleMainMode(state, +1);
    if (prevMode) cycleMainMode(state, -1);

    bool up = keyPressed(VK_UP) || controllerPressed(pad, XINPUT_GAMEPAD_DPAD_UP) || (pad.lsUp && !pad.prevLsUp);
    bool down = keyPressed(VK_DOWN) || controllerPressed(pad, XINPUT_GAMEPAD_DPAD_DOWN) || (pad.lsDown && !pad.prevLsDown);
    bool left = keyPressed(VK_LEFT) || controllerPressed(pad, XINPUT_GAMEPAD_DPAD_LEFT) || (pad.lsLeft && !pad.prevLsLeft);
    bool right = keyPressed(VK_RIGHT) || controllerPressed(pad, XINPUT_GAMEPAD_DPAD_RIGHT) || (pad.lsRight && !pad.prevLsRight);

    bool primary = keyPressed(VK_SPACE) || keyPressed('Z') || controllerPressed(pad, XINPUT_GAMEPAD_A);
    bool secondary = keyPressed('X') || controllerPressed(pad, XINPUT_GAMEPAD_B);
    bool lightAttack = keyPressed('C') || controllerPressed(pad, XINPUT_GAMEPAD_X);
    bool heavyAttack = keyPressed('V') || controllerPressed(pad, XINPUT_GAMEPAD_Y);

    bool rapidPrev = keyDown(VK_PRIOR) || pad.lt > 0.65f;
    bool rapidNext = keyDown(VK_NEXT) || pad.rt > 0.65f;

    if (state.mode == MODE_NAVIGATION) {
        if (up) {
            state.currentNavView = wrapIndex(state.currentNavView + 1, (int)state.assets.navigation[state.currentEnvironment].size());
        }
        if (down) {
            state.currentNavView = wrapIndex(state.currentNavView - 1, (int)state.assets.navigation[state.currentEnvironment].size());
        }
        if (left) {
            state.currentEnvironment = wrapIndex(state.currentEnvironment - 1, 6);
            state.currentNavView = 0;
        }
        if (right) {
            state.currentEnvironment = wrapIndex(state.currentEnvironment + 1, 6);
            state.currentNavView = 0;
        }
        if (primary || heavyAttack) {
            changeMode(state, MODE_COMBAT);
        }
        if (secondary) {
            changeMode(state, MODE_FARM);
        }
        if (rapidPrev) {
            state.currentAmbientFx = wrapIndex(state.currentAmbientFx - 1, (int)state.assets.ambientFx.size());
        }
        if (rapidNext) {
            state.currentAmbientFx = wrapIndex(state.currentAmbientFx + 1, (int)state.assets.ambientFx.size());
        }
    } else if (state.mode == MODE_COMBAT) {
        if (!state.combatInitialized) {
            setupCombatForEnemy(state);
            state.combatInitialized = true;
        }

        if (!state.combatRoundActive) {
            prepareCombatRound(state);
        }

        bool chooseLight = keyPressed('C') || controllerPressed(pad, XINPUT_GAMEPAD_X);
        bool chooseHeavy = keyPressed('V') || controllerPressed(pad, XINPUT_GAMEPAD_Y);
        bool chooseSpecial = keyPressed('F') || controllerPressed(pad, XINPUT_GAMEPAD_RIGHT_SHOULDER);
        bool chooseDefend = keyPressed('X') || controllerPressed(pad, XINPUT_GAMEPAD_B);
        bool chooseParry = keyPressed('R') || controllerPressed(pad, XINPUT_GAMEPAD_LEFT_SHOULDER);
        bool chooseDodge = keyPressed('Z') || controllerPressed(pad, XINPUT_GAMEPAD_A);

        if (state.combatSlowmo) {
            if (left) {
                state.selectedPlayerAction = (CombatActionType)wrapIndex((int)state.selectedPlayerAction - 1, 6);
            }
            if (right) {
                state.selectedPlayerAction = (CombatActionType)wrapIndex((int)state.selectedPlayerAction + 1, 6);
            }

            if (chooseLight) state.selectedPlayerAction = COMBAT_LIGHT;
            if (chooseHeavy) state.selectedPlayerAction = COMBAT_HEAVY;
            if (chooseSpecial) state.selectedPlayerAction = COMBAT_SPECIAL;
            if (chooseDefend) state.selectedPlayerAction = COMBAT_DEFEND;
            if (chooseParry) state.selectedPlayerAction = COMBAT_PARRY;
            if (chooseDodge) state.selectedPlayerAction = COMBAT_DODGE;

            bool lockSelection = keyPressed(VK_SPACE) || primary || rapidNext || rapidPrev ||
                chooseLight || chooseHeavy || chooseSpecial || chooseDefend || chooseParry || chooseDodge;

            state.combatSlowmoTimer -= dt;
            if (lockSelection || state.combatSlowmoTimer <= 0.0f) {
                finalizeSelectionAndQueue(state);
            }
        } else {
            state.combatExecutionTimer += dt;
            if (state.combatExecutionStep == 0 && state.combatExecutionTimer >= 0.28f) {
                int actor = state.combatOrder[0];
                CombatEntity &attacker = (actor == 0) ? state.playerCombat : state.enemyCombat;
                CombatEntity &defender = (actor == 0) ? state.enemyCombat : state.playerCombat;
                CombatActionType defenderAction = (actor == 0) ? state.enemyCombat.queuedAction : state.playerCombat.queuedAction;
                applyActionResolution(state, attacker, defender, attacker.queuedAction, defenderAction, actor == 0);
                state.combatExecutionStep = 1;
            } else if (state.combatExecutionStep == 1 && state.combatExecutionTimer >= 0.56f) {
                int actor = state.combatOrder[1];
                CombatEntity &attacker = (actor == 0) ? state.playerCombat : state.enemyCombat;
                CombatEntity &defender = (actor == 0) ? state.enemyCombat : state.playerCombat;
                CombatActionType defenderAction = (actor == 0) ? state.enemyCombat.queuedAction : state.playerCombat.queuedAction;
                applyActionResolution(state, attacker, defender, attacker.queuedAction, defenderAction, actor == 0);

                state.combatExecutionStep = 2;
                state.combatRoundActive = false;
                state.combatExecutionTimer = 0.0f;

                float playerRecover = (float)(state.playerCombat.stats.virility + state.playerCombat.stats.balance) / 800.0f;
                float enemyRecover = (float)(state.enemyCombat.stats.virility + state.enemyCombat.stats.balance) / 850.0f;
                state.playerCombat.stamina = std::min(1.0f, state.playerCombat.stamina + playerRecover);
                state.enemyCombat.stamina = std::min(1.0f, state.enemyCombat.stamina + enemyRecover);

                if (state.enemyCombat.health <= 0.0f) {
                    state.currentEnemy = wrapIndex(state.currentEnemy + 1, (int)state.assets.enemies.size());
                    setupCombatForEnemy(state);
                    swprintf(state.combatLastLog, 240, L"Enemy defeated. New enemy enters.");
                } else if (state.playerCombat.health <= 0.0f) {
                    state.playerCombat.health = 0.72f;
                    state.playerCombat.stamina = 0.65f;
                    swprintf(state.combatLastLog, 240, L"Player recovers from collapse and continues.");
                }
            }
        }

        if (up) {
            state.currentCombatFx = wrapIndex(state.currentCombatFx + 1, (int)state.assets.combatFx.size());
        }
        if (down) {
            state.currentCombatFx = wrapIndex(state.currentCombatFx - 1, (int)state.assets.combatFx.size());
        }

        combatSyncGauges(state);
    } else if (state.mode == MODE_FARM) {
        if (left || secondary || rapidPrev) {
            state.currentFarm = wrapIndex(state.currentFarm - 1, (int)state.assets.farm.size());
        }
        if (right || primary || rapidNext) {
            state.currentFarm = wrapIndex(state.currentFarm + 1, (int)state.assets.farm.size());
        }
        if (up) {
            state.playerStamina = std::min(1.0f, state.playerStamina + 0.04f);
        }
        if (down) {
            state.playerStamina = std::max(0.0f, state.playerStamina - 0.04f);
        }
    } else if (state.mode == MODE_COOKING) {
        if (!state.cook.active) {
            initCookingSession(state);
        }

        // Left/Right: select ingredient slot
        if (left) state.cook.selectedSlot = wrapIndex(state.cook.selectedSlot - 1, 6);
        if (right) state.cook.selectedSlot = wrapIndex(state.cook.selectedSlot + 1, 6);

        // Up/Down: adjust fire intensity
        if (up) state.cook.fireIntensity = std::min(1.0f, state.cook.fireIntensity + 0.08f);
        if (down) state.cook.fireIntensity = std::max(0.0f, state.cook.fireIntensity - 0.08f);

        // Primary (A/Space): Stir the cauldron
        if (primary || keyDown(VK_SPACE) || keyDown('Z')) {
            state.cook.stirRate = std::min(1.0f, state.cook.stirRate + 2.5f * dt);
        }

        // Light attack (X/C): Add more of selected ingredient
        if (lightAttack) {
            CookingIngredient &slot = state.cook.slots[state.cook.selectedSlot];
            slot.quantity = std::min(1.0f, slot.quantity + 0.10f);
        }

        // Heavy attack (Y/V): Remove some of selected ingredient
        if (heavyAttack) {
            CookingIngredient &slot = state.cook.slots[state.cook.selectedSlot];
            slot.quantity = std::max(0.0f, slot.quantity - 0.10f);
        }

        // Secondary (B/X): Splash water (add moisture, cool slightly)
        if (secondary) {
            for (int i = 0; i < 6; ++i) {
                state.cook.slots[i].moisture = std::min(1.0f, state.cook.slots[i].moisture + 0.08f);
                state.cook.slots[i].temperature = std::max(20.0f, state.cook.slots[i].temperature - 8.0f);
            }
            state.cook.cauldronTemp = std::max(20.0f, state.cook.cauldronTemp - 12.0f);
        }

        // Triggers cycle cooking asset views
        if (rapidPrev) {
            state.currentCooking = wrapIndex(state.currentCooking - 1, (int)state.assets.cooking.size());
        }
        if (rapidNext) {
            state.currentCooking = wrapIndex(state.currentCooking + 1, (int)state.assets.cooking.size());
        }

        // RB (F): finish/serve the dish
        bool serve = keyPressed('F') || controllerPressed(pad, XINPUT_GAMEPAD_RIGHT_SHOULDER);
        if (serve && state.cook.active) {
            finishCooking(state);
        }

        updateCookingSimulation(state, dt);

        if (!state.assets.cookingSim.empty()) {
            state.currentCookingSim = wrapIndex(state.currentCookingSim + ((state.cook.stirRate > 0.3f) ? 1 : 0), (int)state.assets.cookingSim.size());
        }
    } else if (state.mode == MODE_EVOLUTION) {
        if (left || secondary || rapidPrev) {
            state.currentWial = wrapIndex(state.currentWial - 1, (int)state.assets.wials.size());
        }
        if (right || primary || rapidNext) {
            state.currentWial = wrapIndex(state.currentWial + 1, (int)state.assets.wials.size());
        }
        if (up || heavyAttack) {
            state.playerHealth = std::min(1.0f, state.playerHealth + 0.02f);
        }
    }

    updateShowcase(state, dt);
    clearTransientInput(state);
}

void renderModeFrame(HDC hdc, RECT clientRect) {
    DemoState &state = g_demo;
    Graphics graphics(hdc);
    graphics.SetInterpolationMode(InterpolationModeHighQualityBicubic);

    int width = clientRect.right - clientRect.left;
    int height = clientRect.bottom - clientRect.top;

    fillRect(hdc, 0, 0, width, height, RGB(9, 12, 18));

    int panelLeft = 24;
    int panelTop = 72;
    int panelRight = width - 24;
    int panelBottom = height - 140;

    fillRect(hdc, panelLeft, panelTop, panelRight, panelBottom, RGB(18, 22, 30));

    if (state.mode == MODE_TITLE) {
        drawTextLine(hdc, 30, 24, RGB(250, 245, 220), L"WialWohm - ORBEngine Full Feature Demo");
        drawTextLine(hdc, 30, 56, RGB(180, 210, 255), L"Press Enter / Space / Xbox A to Start");

        if (!state.assets.wials.empty()) {
            drawPrimaryImage(graphics, state.assets.wials, state.currentWial, panelLeft + 80, panelTop + 30, 420, 420, 1.0f);
        }
        if (!state.assets.enemies.empty()) {
            drawPrimaryImage(graphics, state.assets.enemies, state.currentEnemy, panelLeft + 560, panelTop + 40, 340, 340, 0.95f);
        }
    } else if (state.mode == MODE_NAVIGATION) {
        const std::vector<AssetImage> &navList = state.assets.navigation[state.currentEnvironment];
        drawPrimaryImage(graphics, navList, state.currentNavView, panelLeft + 12, panelTop + 12, panelRight - panelLeft - 24, panelBottom - panelTop - 24, 1.0f);
        drawPrimaryImage(graphics, state.assets.ambientFx, state.currentAmbientFx, panelLeft + 12, panelTop + 12, panelRight - panelLeft - 24, panelBottom - panelTop - 24, 0.22f);
    } else if (state.mode == MODE_COMBAT) {
        drawPrimaryImage(graphics, state.assets.navigation[state.currentEnvironment], state.currentNavView, panelLeft + 12, panelTop + 12, panelRight - panelLeft - 24, panelBottom - panelTop - 24, 0.35f);
        drawPrimaryImage(graphics, state.assets.enemies, state.currentEnemy, width / 2 - 220, panelTop + 30, 440, 440, 1.0f);
        drawPrimaryImage(graphics, state.assets.combatFx, state.currentCombatFx, width / 2 - 260, panelTop + 6, 520, 520, 0.55f);
        drawPrimaryImage(graphics, state.assets.ambientFx, state.currentAmbientFx, panelLeft + 12, panelTop + 12, panelRight - panelLeft - 24, panelBottom - panelTop - 24, 0.15f);
        // Combat animation sheet overlay (over-the-shoulder view)
        if (!state.assets.combatAnims.empty()) {
            drawPrimaryImage(graphics, state.assets.combatAnims, state.currentCombatAnim, panelLeft + 30, panelBottom - 260, 240, 240, 0.75f);
        }

        fillRect(hdc, panelLeft + 24, panelTop + 24, panelLeft + 610, panelTop + 210, RGB(16, 18, 24));
        fillRect(hdc, panelRight - 430, panelTop + 24, panelRight - 24, panelTop + 240, RGB(16, 18, 24));

        wchar_t line[256];
        swprintf(line, 256, L"Time Dilation: %ls", state.combatSlowmo ? L"ACTIVE" : L"RESOLVING");
        drawTextLine(hdc, panelLeft + 36, panelTop + 34, RGB(240, 230, 180), line);
        drawTextLine(hdc, panelLeft + 36, panelTop + 58, RGB(210, 225, 255), state.combatTelegraph);
        swprintf(line, 256, L"Player queued: %ls", kCombatActionNames[(int)state.selectedPlayerAction]);
        drawTextLine(hdc, panelLeft + 36, panelTop + 82, RGB(170, 230, 190), line);
        swprintf(line, 256, L"Enemy queued: %ls", kCombatActionNames[(int)state.enemyCombat.queuedAction]);
        drawTextLine(hdc, panelLeft + 36, panelTop + 106, RGB(255, 190, 170), line);
        swprintf(line, 256, L"Round %d | Initiative P:%d E:%d | Archetype: %ls",
            state.combatRoundIndex, state.playerCombat.initiative, state.enemyCombat.initiative,
            kArchetypeNames[(int)state.enemyCombat.archetype]);
        drawTextLine(hdc, panelLeft + 36, panelTop + 130, RGB(205, 210, 240), line);
        drawTextLine(hdc, panelLeft + 36, panelTop + 154, RGB(240, 240, 240), state.combatLastLog);
        swprintf(line, 256, L"Window: %.2fs | Precision die: d%d | Balance swing: d%d",
            kArchetypes[(int)state.enemyCombat.archetype].slowmoWindow,
            kArchetypes[(int)state.enemyCombat.archetype].precisionDie,
            kArchetypes[(int)state.enemyCombat.archetype].balanceSwingDie);
        drawTextLine(hdc, panelLeft + 36, panelTop + 178, RGB(190, 185, 220), line);

        drawTextLine(hdc, panelRight - 412, panelTop + 36, RGB(255, 235, 165), L"Combat Prompts");
        drawTextLine(hdc, panelRight - 412, panelTop + 62, RGB(225, 235, 255), L"X/C: Light    Y/V: Heavy");
        drawTextLine(hdc, panelRight - 412, panelTop + 84, RGB(225, 235, 255), L"RB/F: Special A/Z: Dodge");
        drawTextLine(hdc, panelRight - 412, panelTop + 106, RGB(225, 235, 255), L"B/X: Defend   LB/R: Parry");
        drawTextLine(hdc, panelRight - 412, panelTop + 128, RGB(225, 235, 255), L"Space/A: Lock action during slowmo");
        drawTextLine(hdc, panelRight - 412, panelTop + 150, RGB(225, 235, 255), L"Roll model: speed/strength/defense");
        drawTextLine(hdc, panelRight - 412, panelTop + 172, RGB(225, 235, 255), L"virility/sagess/nimbility/balance");

        swprintf(line, 256, L"P Stats S%d Str%d Def%d Vir%d Sag%d Nim%d Bal%d",
            state.playerCombat.stats.speed,
            state.playerCombat.stats.strength,
            state.playerCombat.stats.defense,
            state.playerCombat.stats.virility,
            state.playerCombat.stats.sagess,
            state.playerCombat.stats.nimbility,
            state.playerCombat.stats.balance);
        drawTextLine(hdc, panelRight - 412, panelTop + 198, RGB(175, 230, 190), line);
        swprintf(line, 256, L"E Stats S%d Str%d Def%d Vir%d Sag%d Nim%d Bal%d",
            state.enemyCombat.stats.speed,
            state.enemyCombat.stats.strength,
            state.enemyCombat.stats.defense,
            state.enemyCombat.stats.virility,
            state.enemyCombat.stats.sagess,
            state.enemyCombat.stats.nimbility,
            state.enemyCombat.stats.balance);
        drawTextLine(hdc, panelRight - 412, panelTop + 220, RGB(255, 185, 170), line);
    } else if (state.mode == MODE_FARM) {
        drawPrimaryImage(graphics, state.assets.farm, state.currentFarm, panelLeft + 12, panelTop + 12, panelRight - panelLeft - 24, panelBottom - panelTop - 24, 1.0f);
    } else if (state.mode == MODE_COOKING) {
        // Background: cooking scene asset
        drawPrimaryImage(graphics, state.assets.cooking, state.currentCooking, panelLeft + 12, panelTop + 12, panelRight - panelLeft - 24, panelBottom - panelTop - 24, 0.55f);
        // Overlay: cooking sim assets (cauldron/fire/stir effects)
        if (!state.assets.cookingSim.empty()) {
            drawPrimaryImage(graphics, state.assets.cookingSim, state.currentCookingSim, width / 2 - 200, panelTop + 40, 400, 400, 0.85f);
        }

        // Cooking HUD
        fillRect(hdc, panelLeft + 24, panelTop + 24, panelLeft + 660, panelTop + 270, RGB(16, 14, 10));

        wchar_t line[256];
        CookingState &ck = state.cook;

        drawTextLine(hdc, panelLeft + 36, panelTop + 28, RGB(255, 220, 120), L"Eggshell Cauldron Cooking");
        swprintf(line, 256, L"Fire:%.0f%% | Cauldron Temp:%.0fC | Stir:%.0f%%",
            ck.fireIntensity * 100.0f, ck.cauldronTemp, ck.stirRate * 100.0f);
        drawTextLine(hdc, panelLeft + 36, panelTop + 50, RGB(240, 180, 100), line);

        for (int i = 0; i < 6; ++i) {
            CookingIngredient &ing = ck.slots[i];
            COLORREF slotColor = (i == ck.selectedSlot) ? RGB(255, 255, 180) : RGB(180, 195, 210);
            int yOff = panelTop + 76 + i * 28;
            swprintf(line, 256, L"%ls%ls Q:%.0f%% Qual:%.0f%% Cook:%.0f%% T:%.0f Mst:%.0f%% H:%.0f%%",
                (i == ck.selectedSlot) ? L"> " : L"  ",
                ing.name,
                ing.quantity * 100.0f,
                ing.quality * 100.0f,
                ing.cookness * 100.0f,
                ing.temperature,
                ing.moisture * 100.0f,
                ing.healthiness * 100.0f);
            drawTextLine(hdc, panelLeft + 36, yOff, slotColor, line);
        }

        drawTextLine(hdc, panelLeft + 36, panelTop + 248, RGB(210, 235, 255), ck.statusLine);

        // Controls panel
        fillRect(hdc, panelRight - 350, panelTop + 24, panelRight - 24, panelTop + 190, RGB(16, 14, 10));
        drawTextLine(hdc, panelRight - 332, panelTop + 28, RGB(255, 235, 165), L"Cooking Controls");
        drawTextLine(hdc, panelRight - 332, panelTop + 52, RGB(225, 235, 255), L"Up/Down: Fire intensity");
        drawTextLine(hdc, panelRight - 332, panelTop + 74, RGB(225, 235, 255), L"Left/Right: Select slot");
        drawTextLine(hdc, panelRight - 332, panelTop + 96, RGB(225, 235, 255), L"A/Space: Stir cauldron");
        drawTextLine(hdc, panelRight - 332, panelTop + 118, RGB(225, 235, 255), L"X: Add ingredient  Y: Remove");
        drawTextLine(hdc, panelRight - 332, panelTop + 140, RGB(225, 235, 255), L"B: Splash water (cool/moisten)");
        drawTextLine(hdc, panelRight - 332, panelTop + 162, RGB(225, 235, 255), L"RB/F: Serve dish");

        if (!ck.active) {
            drawTextLine(hdc, panelLeft + 36, panelBottom - 34, RGB(160, 255, 160), ck.resultLine);
        }
    } else if (state.mode == MODE_EVOLUTION) {
        drawPrimaryImage(graphics, state.assets.wials, state.currentWial, panelLeft + 110, panelTop + 12, panelRight - panelLeft - 220, panelBottom - panelTop - 24, 1.0f);
        drawPrimaryImage(graphics, state.assets.ambientFx, state.currentAmbientFx, panelLeft + 12, panelTop + 12, panelRight - panelLeft - 24, panelBottom - panelTop - 24, 0.18f);
    } else if (state.mode == MODE_STATS) {
        drawTextLine(hdc, panelLeft + 24, panelTop + 24, RGB(225, 240, 255), L"WialWohm world data loaded from C dataset:");

        wchar_t line[256];
        swprintf(line, 256, L"Wial evolutions: %d", WIAL_EVOLUTIONS_COUNT);
        drawTextLine(hdc, panelLeft + 24, panelTop + 60, RGB(190, 220, 190), line);
        swprintf(line, 256, L"Wohm types: %d", WOHM_TYPES_COUNT);
        drawTextLine(hdc, panelLeft + 24, panelTop + 86, RGB(190, 220, 190), line);
        swprintf(line, 256, L"Enemies: %d", ENEMIES_COUNT);
        drawTextLine(hdc, panelLeft + 24, panelTop + 112, RGB(190, 220, 190), line);
        swprintf(line, 256, L"Resources: %d", RESOURCES_COUNT);
        drawTextLine(hdc, panelLeft + 24, panelTop + 138, RGB(190, 220, 190), line);
        swprintf(line, 256, L"Crops: %d", CROPS_COUNT);
        drawTextLine(hdc, panelLeft + 24, panelTop + 164, RGB(190, 220, 190), line);
        swprintf(line, 256, L"Tools: %d", TOOLS_COUNT);
        drawTextLine(hdc, panelLeft + 24, panelTop + 190, RGB(190, 220, 190), line);

        swprintf(line, 256, L"Generated art assets loaded: %d / 195", totalAssetsLoaded(state.assets));
        drawTextLine(hdc, panelLeft + 24, panelTop + 232, RGB(255, 230, 170), line);
    } else if (state.mode == MODE_PAUSE) {
        drawTextLine(hdc, width / 2 - 60, height / 2 - 20, RGB(255, 245, 200), L"PAUSED");
        drawTextLine(hdc, width / 2 - 220, height / 2 + 12, RGB(180, 220, 255), L"Press Esc / Start to resume");
    }

    wchar_t header[256];
    swprintf(header, 256, L"Mode: %ls | Env: %ls | AutoShowcase: %ls | Xbox: %ls",
        kModeNames[(int)state.mode],
        kEnvironmentNames[state.currentEnvironment],
        state.autoShowcase ? L"ON" : L"OFF",
        state.controller.connected ? L"Connected" : L"Disconnected");
    drawTextLine(hdc, 28, 16, RGB(240, 245, 255), header);

    drawGauge(hdc, 30, height - 54, 260, 24, state.playerHealth, RGB(200, 70, 80), L"Wial Health");
    drawGauge(hdc, 308, height - 54, 260, 24, state.playerStamina, RGB(80, 180, 110), L"Wial Stamina");
    drawGauge(hdc, 586, height - 54, 260, 24, state.enemyHealth, RGB(180, 120, 50), L"Enemy Pressure");

    drawTextLine(hdc, 866, height - 54, RGB(196, 208, 225), L"Q/E or LB/RB: mode  Arrows/DPad/LS: navigate  A: confirm  B: back");
    drawTextLine(hdc, 866, height - 30, RGB(196, 208, 225), L"X: light  Y: heavy  LT/RT or PgUp/PgDn: rapid cycle  T: auto showcase  P: title");
}

void initializeDemo(HWND window) {
    DemoState &state = g_demo;
    // Do NOT ZeroMemory — it corrupts std::vector/std::wstring internals in DemoAssets.
    // Zero only the POD fields explicitly.
    state.window = window;
    state.mode = MODE_TITLE;
    state.prePauseMode = MODE_TITLE;
    state.running = true;
    state.autoShowcase = true;
    state.modeTimer = 0.0f;
    state.assetTimer = 0.0f;
    state.modeCursor = 0;

    state.currentEnvironment = 0;
    state.currentNavView = 0;
    state.currentEnemy = 0;
    state.currentCombatFx = 0;
    state.currentAmbientFx = 0;
    state.currentFarm = 0;
    state.currentCooking = 0;
    state.currentWial = 0;
    state.currentCombatAnim = 0;
    state.currentCookingSim = 0;

    state.playerHealth = 1.0f;
    state.playerStamina = 1.0f;
    state.enemyHealth = 1.0f;

    state.combatInitialized = false;
    state.combatRoundActive = false;
    state.combatSlowmo = false;
    state.combatSlowmoTimer = 0.0f;
    state.combatExecutionTimer = 0.0f;
    state.combatExecutionStep = 0;
    memset(state.combatOrder, 0, sizeof(state.combatOrder));
    state.combatRoundIndex = 0;
    state.rngState = 0;

    memset(&state.playerCombat, 0, sizeof(state.playerCombat));
    memset(&state.enemyCombat, 0, sizeof(state.enemyCombat));
    state.selectedPlayerAction = {};
    state.telegraphedEnemyAction = {};

    memset(state.combatTelegraph, 0, sizeof(state.combatTelegraph));
    memset(state.combatLastLog, 0, sizeof(state.combatLastLog));
    memset(&state.cook, 0, sizeof(state.cook));

    memset(state.keyDown, 0, sizeof(state.keyDown));
    memset(state.keyPressed, 0, sizeof(state.keyPressed));
    memset(state.keyReleased, 0, sizeof(state.keyReleased));

    memset(&state.controller, 0, sizeof(state.controller));
    state.xinputModule = nullptr;
    state.xinputGetState = nullptr;
    state.gdiplusToken = 0;

    GdiplusStartupInput gdiplusStartupInput;
    GdiplusStartup(&state.gdiplusToken, &gdiplusStartupInput, NULL);

    init_game_data();
    discoverAndLoadAssets(state.assets);
    loadXInput(state);
}

void shutdownDemo() {
    DemoState &state = g_demo;
    freeAssets(state.assets);
    if (state.xinputModule != NULL) {
        FreeLibrary(state.xinputModule);
        state.xinputModule = NULL;
    }
    cleanup_game_data();
    GdiplusShutdown(state.gdiplusToken);
}

LRESULT CALLBACK windowProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    (void)lParam;
    switch (msg) {
        case WM_CREATE:
            SetTimer(hwnd, 1, 16, NULL);
            return 0;

        case WM_TIMER:
            updateGameplay(1.0f / 60.0f);
            InvalidateRect(hwnd, NULL, FALSE);
            return 0;

        case WM_KEYDOWN: {
            int key = (int)wParam;
            if (key >= 0 && key < 256) {
                if (!g_demo.keyDown[key]) {
                    g_demo.keyPressed[key] = true;
                }
                g_demo.keyDown[key] = true;
            }
            return 0;
        }

        case WM_KEYUP: {
            int key = (int)wParam;
            if (key >= 0 && key < 256) {
                g_demo.keyDown[key] = false;
                g_demo.keyReleased[key] = true;
            }
            return 0;
        }

        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hwnd, &ps);
            RECT clientRect;
            GetClientRect(hwnd, &clientRect);
            renderModeFrame(hdc, clientRect);
            EndPaint(hwnd, &ps);
            return 0;
        }

        case WM_DESTROY:
            KillTimer(hwnd, 1);
            PostQuitMessage(0);
            return 0;
    }

    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

} // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR commandLine, int showCommand) {
    (void)previous;
    (void)commandLine;

    const wchar_t *className = L"WialWohmDemoWindowClass";

    WNDCLASSEXW windowClass = {};
    windowClass.cbSize = sizeof(windowClass);
    windowClass.style = CS_HREDRAW | CS_VREDRAW;
    windowClass.lpfnWndProc = windowProc;
    windowClass.hInstance = instance;
    windowClass.hCursor = LoadCursor(NULL, IDC_ARROW);
    windowClass.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    windowClass.lpszClassName = className;

    if (!RegisterClassExW(&windowClass)) {
        return 1;
    }

    HWND window = CreateWindowExW(
        0,
        className,
        L"WialWohm - ORBEngine Gameplay Demo (Windows)",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        1366,
        820,
        NULL,
        NULL,
        instance,
        NULL);

    if (window == NULL) {
        return 1;
    }

    initializeDemo(window);

    ShowWindow(window, showCommand);
    UpdateWindow(window);

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    shutdownDemo();
    return (int)msg.wParam;
}
