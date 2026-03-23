#define _CRT_SECURE_NO_WARNINGS
#define NOMINMAX

#include <windows.h>
#include <gdiplus.h>
#include <xinput.h>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <cwchar>
#include <string>
#include <vector>

using namespace Gdiplus;

namespace
{
const wchar_t *kWindowClass = L"InnsmouthIslandResearchWindow";
const wchar_t *kWindowTitle = L"InnsmouthIsland Research Integrated";
const int kWindowWidth = 1440;
const int kWindowHeight = 900;
const float kWorldMetersX = 4000.0f;
const float kWorldMetersY = 3000.0f;
const int kEnvironmentObjectCount = 24;
const int kEnvironmentPlacementKeyMax = 64;
const int kBasicEnemyCount = 8;
const int kBossCount = 2;
const int kTotalEnemies = kBasicEnemyCount + kBossCount;
const int kPropSheetColumns = 6;
const int kPlayerSheetColumns = 4;
const int kPlayerSheetRows = 4;
const int kEnemyRosterColumns = 4;
const int kBasicAnimColumns = 4;
const int kBasicAnimRows = 3;
const int kBossAnimColumns = 4;
const int kBossAnimRows = 4;
const int kViewTabCount = 6;
const int kWeaponCount = 23;
const int kArmorSetCount = 14;
const int kArmorPieceCount = 8;
const int kPickupCount = 20;
const int kShelterCount = 5;

enum GameMode
{
    MODE_TITLE,
    MODE_OPENING,
    MODE_PLAY,
    MODE_PAUSE,
    MODE_VIEW_MENU,
    MODE_SHRINE,
    MODE_GAME_OVER,
    MODE_VICTORY
};

enum ViewTab
{
    TAB_CHARACTER,
    TAB_INVENTORY,
    TAB_EQUIPMENT,
    TAB_MAP,
    TAB_QUESTLOG,
    TAB_CODEX
};

enum PlayerAnim
{
    PLAYER_ANIM_CRAWL,
    PLAYER_ANIM_IDLE,
    PLAYER_ANIM_HEAL,
    PLAYER_ANIM_WALK,
    PLAYER_ANIM_RUN,
    PLAYER_ANIM_JUMP,
    PLAYER_ANIM_DODGE,
    PLAYER_ANIM_CROUCH,
    PLAYER_ANIM_SLIDE,
    PLAYER_ANIM_FOCUS,
    PLAYER_ANIM_LIGHT,
    PLAYER_ANIM_HEAVY,
    PLAYER_ANIM_BLOCK,
    PLAYER_ANIM_PARRY,
    PLAYER_ANIM_HURT,
    PLAYER_ANIM_VICTORY
};

enum EnemyKind
{
    ENEMY_DEEP_ONE,
    ENEMY_SHOGGOTH_SPAWN,
    ENEMY_NIGHTGAUNT,
    ENEMY_MI_GO,
    ENEMY_GHOUL,
    ENEMY_CULTIST,
    ENEMY_STAR_SPAWN,
    ENEMY_DROWNED_PILGRIM,
    ENEMY_REPTILIAN_DEITY,
    ENEMY_JAGUAR_DEITY
};

enum PickupKind
{
    PICKUP_THROWING_KNIFE,
    PICKUP_FIRE_BOMB,
    PICKUP_SEED_POD,
    PICKUP_BRINE_SALT
};

struct Vec2
{
    float x;
    float y;
};

struct AssetBank
{
    Image *playerSheet;
    Image *openingStoryboard;
    Image *enemyRosterSheet;
    Image *basicEnemyAnimSheet;
    Image *bossAnimSheet;
    Image *environmentPropsSheet;
    Image *worldMap;
    Image *worldKeyart;
    Image *uiMenuPanel;
    Image *hudSheet;
    Image *iconsSheet;
};

struct EnvironmentObject
{
    int type;
    char placementKey[kEnvironmentPlacementKeyMax];
    Vec2 position;
    float scale;
};

struct AssetAnchorNode
{
    float x;
    float y;
    float z;
};

struct CollisionSilhouette
{
    float radiusX;
    float radiusY;
    float occlusionDepth;
};

struct EnvironmentRenderProfile
{
    float topLift;
    float shadowWidth;
    float shadowDepth;
    CollisionSilhouette silhouette;
    AssetAnchorNode anchors[4];
};

enum AttachmentSocketKind
{
    SOCKET_HEAD,
    SOCKET_TORSO,
    SOCKET_RIGHT_HAND,
    SOCKET_LEFT_HAND,
    SOCKET_HIP,
    SOCKET_FEET,
    SOCKET_COUNT
};

struct AttachmentSocket
{
    float u;
    float v;
    float z;
};

struct PlayerAttachmentMap
{
    AttachmentSocket sockets[SOCKET_COUNT];
};

struct RuntimeAttachmentMetadata
{
    int loaded;
    PlayerAttachmentMap baseMap;
    PlayerAttachmentMap armorProfiles[kArmorSetCount];
    int armorProfileLoaded[kArmorSetCount];
    PlayerAttachmentMap meleeProfiles[kWeaponCount];
    int meleeProfileLoaded[kWeaponCount];
    PlayerAttachmentMap projectileProfiles[kWeaponCount];
    int projectileProfileLoaded[kWeaponCount];
};

struct RuntimeEnvironmentMetadata
{
    int loaded;
    EnvironmentRenderProfile profiles[kEnvironmentObjectCount];
    int profileLoaded[kEnvironmentObjectCount];
    int placementCount;
    char placementKeys[kEnvironmentObjectCount][kEnvironmentPlacementKeyMax];
    EnvironmentRenderProfile placementProfiles[kEnvironmentObjectCount];
    int placementProfileLoaded[kEnvironmentObjectCount];
};

#include "../include/orbengine_innsmouth_runtime_metadata.hpp"

struct Pickup
{
    PickupKind kind;
    Vec2 position;
    int active;
    int variant;
};

struct MurkShelter
{
    Vec2 position;
    int discovered;
    int activated;
};

struct WeaponDef
{
    const wchar_t *name;
    int melee;
    int damage;
    int staminaCost;
    int unlockCost;
    int crafted;
    int newGamePlus;
};

struct ArmorSetDef
{
    const wchar_t *name;
    int defense;
    int mobility;
    int crafted;
    int newGamePlus;
};

struct Enemy
{
    EnemyKind kind;
    Vec2 position;
    Vec2 velocity;
    int hp;
    int maxHp;
    int alive;
    int boss;
    int discovered;
    float attackCooldown;
    float staggerTimer;
    float animationTime;
    float specialTimer;
    int animationFrameCount;
};

struct PlayerState
{
    Vec2 position;
    Vec2 velocity;
    Vec2 facing;
    float hopHeight;
    float hopVelocity;
    int hp;
    int maxHp;
    float stamina;
    float maxStamina;
    float moisture;
    float breathingSync;
    float healAccumulator;
    float idleTimer;
    float dodgeTimer;
    float parryTimer;
    float blockTimer;
    float attackCooldown;
    float slideTimer;
    float hurtFlash;
    float actionTime;
    int airActions;
    PlayerAnim animation;
};

struct KeyboardState
{
    int down[256];
    int pressed[256];
    int released[256];
};

struct ControllerState
{
    int connected;
    WORD buttons;
    WORD prevButtons;
    float lx;
    float ly;
    float rx;
    float ry;
    float lt;
    float rt;
};

typedef DWORD(WINAPI *XInputGetStateProc)(DWORD, XINPUT_STATE *);

struct XInputRuntime
{
    HMODULE module;
    XInputGetStateProc getState;
};

struct DemoState
{
    ULONG_PTR gdiplusToken;
    AssetBank assets;
    XInputRuntime xinput;
    KeyboardState keyboard;
    ControllerState controller;
    GameMode mode;
    PlayerState player;
    EnvironmentObject environment[kEnvironmentObjectCount];
    Pickup pickups[kPickupCount];
    MurkShelter shelters[kShelterCount];
    Enemy enemies[kTotalEnemies];
    int selectedTitleOption;
    int selectedPauseOption;
    int selectedShrineOption;
    ViewTab currentViewTab;
    int currentViewSelection;
    int showPrompt;
    int showControlsCard;
    int activeQuestStage;
    int basicEnemiesRemaining;
    int bossesSpawned;
    int victoryUnlocked;
    float openingTimer;
    float worldTime;
    float cameraYaw;
    float cameraPitch;
    float cameraShake;
    float menuInputCooldown;
    float controllerBHold;
    float controllerRTHold;
    float notificationTimer;
    float focusPulse;
    int templeSeals;
    int blackKelp;
    int saltSigils;
    int brineSalt;
    int throwingKnives;
    int fireBombs;
    int seedPods;
    int currentConsumable;
    int equippedMeleeWeapon;
    int equippedProjectileWeapon;
    int equippedArmorSet;
    int weaponUnlocked[kWeaponCount];
    int armorUnlocked[kArmorSetCount];
    int nearestShelterIndex;
    int activeShelterIndex;
    int newGamePlusUnlocked;
    int vitalityRank;
    int staminaRank;
    int weaponRank;
    int armorRank;
    int focusTargetIndex;
    wchar_t notification[256];
};

DemoState g_demo = {};
RuntimeAttachmentMetadata g_attachmentMetadata = {};
RuntimeEnvironmentMetadata g_environmentMetadata = {};

const char *kSocketJsonNames[SOCKET_COUNT] = {
    "head",
    "torso",
    "right_hand",
    "left_hand",
    "hip",
    "feet"};

const char *kAttachmentMapSearchPaths[] = {
    "..\\drIpTECH\\ReCraftGenerationStreamline\\innsmouth_island_attachment_map_v1.json",
    "drIpTECH\\ReCraftGenerationStreamline\\innsmouth_island_attachment_map_v1.json"};

const char *kEnvironmentMetadataSearchPaths[] = {
    "..\\drIpTECH\\ReCraftGenerationStreamline\\innsmouth_island_environment_runtime_metadata_v1.json",
    "drIpTECH\\ReCraftGenerationStreamline\\innsmouth_island_environment_runtime_metadata_v1.json"};

const wchar_t *kArmorPieceLabels[kArmorPieceCount] = {
    L"Upper Right Arm",
    L"Lower Right Arm",
    L"Upper Left Arm",
    L"Lower Left Arm",
    L"Upper Right Leg",
    L"Lower Right Leg",
    L"Upper Left Leg",
    L"Lower Left Leg"};

const WeaponDef kWeapons[kWeaponCount] = {
    {L"Barnacle Shiv", 1, 16, 8, 0, 0, 0},
    {L"Tide Hook", 1, 18, 9, 20, 0, 0},
    {L"Coral Mace", 1, 20, 11, 35, 0, 0},
    {L"Dock Cleaver", 1, 23, 12, 55, 0, 0},
    {L"Shell Glaive", 1, 24, 12, 70, 0, 0},
    {L"Pearl Pike", 1, 25, 13, 90, 0, 0},
    {L"Kelp Lash", 1, 21, 10, 105, 1, 0},
    {L"Mud-Saw Hatchet", 1, 26, 13, 120, 1, 0},
    {L"Ooze Hammer", 1, 29, 15, 145, 1, 0},
    {L"Brine Falx", 1, 28, 14, 165, 0, 0},
    {L"Eelbone Saber", 1, 30, 15, 185, 0, 0},
    {L"Ruin Breaker", 1, 33, 17, 215, 0, 0},
    {L"Temple Harrow", 1, 35, 18, 245, 0, 0},
    {L"Jetty Reaper", 1, 38, 20, 275, 0, 0},
    {L"Black Pearl Axe", 1, 40, 21, 320, 0, 0},
    {L"Newgame+ Abyss Halberd", 1, 46, 22, 0, 0, 1},
    {L"Throwing Knives", 0, 12, 0, 0, 0, 0},
    {L"Mudglass Darts", 0, 14, 0, 24, 0, 0},
    {L"Harpoon Coil", 0, 16, 0, 48, 0, 0},
    {L"Molotov Brine Flask", 0, 21, 0, 0, 1, 0},
    {L"Dust Seed Pod", 0, 8, 0, 0, 1, 0},
    {L"Pearl Bolt Caster", 0, 24, 0, 140, 0, 0},
    {L"Newgame+ Eclipse Launcher", 0, 32, 0, 0, 0, 1}};

const ArmorSetDef kArmorSets[kArmorSetCount] = {
    {L"Shore Rag Harness", 4, 10, 0, 0},
    {L"Dockworker Saltmail", 6, 9, 0, 0},
    {L"Kelp-Wrap Strider", 5, 12, 1, 0},
    {L"Mudplate Forager", 8, 7, 1, 0},
    {L"Pearl-Lashed Raider", 9, 8, 1, 0},
    {L"Ooze-Forged Pilgrim", 11, 7, 1, 0},
    {L"Brackish Duelist Rig", 10, 10, 0, 0},
    {L"Murk Templar Shell", 13, 6, 0, 0},
    {L"Nightgaunt Veilweave", 8, 13, 0, 0},
    {L"Star-Spawn Pressure Suit", 14, 5, 0, 0},
    {L"Cult Tide Mantle", 11, 9, 0, 0},
    {L"Basalt Canopy Guard", 15, 4, 0, 0},
    {L"Abyss Prince Husk", 17, 5, 0, 0},
    {L"Newgame+ Eclipse Regalia", 22, 9, 0, 1}};

struct SaveData
{
    int brineSalt;
    int blackKelp;
    int saltSigils;
    int throwingKnives;
    int fireBombs;
    int seedPods;
    int equippedMeleeWeapon;
    int equippedProjectileWeapon;
    int equippedArmorSet;
    int weaponUnlocked[kWeaponCount];
    int armorUnlocked[kArmorSetCount];
    int shelterActivated[kShelterCount];
    int vitalityRank;
    int staminaRank;
    int weaponRank;
    int armorRank;
    int newGamePlusUnlocked;
};

void applyEnemyDamage(int index, int damage, float stagger);

float clampf(float value, float minValue, float maxValue)
{
    if (value < minValue)
    {
        return minValue;
    }
    if (value > maxValue)
    {
        return maxValue;
    }
    return value;
}

float length(Vec2 value)
{
    return std::sqrt(value.x * value.x + value.y * value.y);
}

Vec2 normalize(Vec2 value)
{
    float magnitude = length(value);
    if (magnitude < 0.0001f)
    {
        return {0.0f, 0.0f};
    }
    return {value.x / magnitude, value.y / magnitude};
}

Vec2 add(Vec2 a, Vec2 b)
{
    return {a.x + b.x, a.y + b.y};
}

Vec2 sub(Vec2 a, Vec2 b)
{
    return {a.x - b.x, a.y - b.y};
}

Vec2 scale(Vec2 value, float scalar)
{
    return {value.x * scalar, value.y * scalar};
}

EnvironmentRenderProfile proceduralEnvironmentRenderProfile(int type, float objectScale)
{
    int family = type % 6;
    int tier = type / 6;
    float scaleValue = clampf(objectScale, 0.80f, 1.40f);
    float radiusX = (42.0f + family * 7.0f + tier * 10.0f) * scaleValue;
    float radiusY = (24.0f + family * 4.0f + tier * 7.0f) * scaleValue;
    float topLift = (28.0f + tier * 12.0f + family * 2.0f) * scaleValue;
    float occlusionDepth = (96.0f + tier * 28.0f + family * 5.0f) * scaleValue;
    return {
        topLift,
        radiusX * 1.42f,
        radiusY * 1.55f,
        {radiusX, radiusY, occlusionDepth},
        {{-radiusX, -radiusY, 0.0f}, {radiusX, -radiusY, 0.0f}, {radiusX, radiusY, topLift}, {-radiusX, radiusY, topLift}}};
}

PlayerAttachmentMap proceduralPlayerAttachmentMap(int armorSet, int meleeWeapon, int projectileWeapon)
{
    float armorWeight = (float)kArmorSets[armorSet].defense / 22.0f;
    float mobilityBias = (float)kArmorSets[armorSet].mobility / 13.0f;
    float meleeBias = (float)(meleeWeapon % 4) * 0.012f;
    float projectileBias = (float)((projectileWeapon - 16) % 3) * 0.010f;
    PlayerAttachmentMap map = {
        {
            {0.50f, 0.18f - armorWeight * 0.01f, 0.92f},
            {0.50f, 0.41f + armorWeight * 0.01f, 0.72f},
            {0.66f + meleeBias, 0.55f - mobilityBias * 0.03f, 0.58f},
            {0.34f - projectileBias, 0.47f - mobilityBias * 0.02f, 0.60f},
            {0.49f, 0.60f + armorWeight * 0.01f, 0.44f},
            {0.50f, 0.90f, 0.08f},
        }};
    return map;
}

int loadAttachmentMetadata()
{
    return innsmouth_runtime::loadAttachmentMetadataFromJson(
        kAttachmentMapSearchPaths,
        2,
        kSocketJsonNames,
        SOCKET_COUNT,
        g_attachmentMetadata,
        kArmorSetCount,
        kWeaponCount);
}

int loadEnvironmentMetadata()
{
    return innsmouth_runtime::loadEnvironmentMetadataFromJson(
        kEnvironmentMetadataSearchPaths,
        2,
        g_environmentMetadata,
        kEnvironmentObjectCount);
}

void loadRuntimeMetadata()
{
    loadAttachmentMetadata();
    loadEnvironmentMetadata();
}

EnvironmentRenderProfile environmentRenderProfile(const EnvironmentObject &object)
{
    int placementIndex = innsmouth_runtime::findEnvironmentPlacementProfile(g_environmentMetadata, object.placementKey);
    if (placementIndex >= 0)
    {
        return innsmouth_runtime::scaleEnvironmentRenderProfile(g_environmentMetadata.placementProfiles[placementIndex], object.scale);
    }
    if (object.type >= 0 && object.type < kEnvironmentObjectCount &&
        g_environmentMetadata.loaded && g_environmentMetadata.profileLoaded[object.type])
    {
        return innsmouth_runtime::scaleEnvironmentRenderProfile(g_environmentMetadata.profiles[object.type], object.scale);
    }
    return proceduralEnvironmentRenderProfile(object.type, object.scale);
}

PlayerAttachmentMap playerAttachmentMap(int armorSet, int meleeWeapon, int projectileWeapon)
{
    if (!g_attachmentMetadata.loaded)
    {
        return proceduralPlayerAttachmentMap(armorSet, meleeWeapon, projectileWeapon);
    }

    PlayerAttachmentMap map = g_attachmentMetadata.baseMap;
    if (armorSet >= 0 && armorSet < kArmorSetCount && g_attachmentMetadata.armorProfileLoaded[armorSet])
    {
        map = g_attachmentMetadata.armorProfiles[armorSet];
    }
    if (meleeWeapon >= 0 && meleeWeapon < kWeaponCount && g_attachmentMetadata.meleeProfileLoaded[meleeWeapon])
    {
        map.sockets[SOCKET_RIGHT_HAND] = g_attachmentMetadata.meleeProfiles[meleeWeapon].sockets[SOCKET_RIGHT_HAND];
    }
    if (projectileWeapon >= 0 && projectileWeapon < kWeaponCount && g_attachmentMetadata.projectileProfileLoaded[projectileWeapon])
    {
        map.sockets[SOCKET_LEFT_HAND] = g_attachmentMetadata.projectileProfiles[projectileWeapon].sockets[SOCKET_LEFT_HAND];
    }
    return map;
}

void resolveEnvironmentCollisions()
{
    for (int index = 0; index < kEnvironmentObjectCount; ++index)
    {
        const EnvironmentObject &object = g_demo.environment[index];
        EnvironmentRenderProfile profile = environmentRenderProfile(object);
        Vec2 delta = sub(g_demo.player.position, object.position);
        float normalized = (delta.x * delta.x) / (profile.silhouette.radiusX * profile.silhouette.radiusX) +
                           (delta.y * delta.y) / (profile.silhouette.radiusY * profile.silhouette.radiusY);
        if (normalized < 1.0f)
        {
            if (length(delta) < 0.001f)
            {
                delta = {0.0f, profile.silhouette.radiusY};
            }
            float scaleOut = 1.04f / std::sqrt(std::max(normalized, 0.0001f));
            g_demo.player.position = add(object.position, scale(delta, scaleOut));
        }
    }
}

int environmentOccludesPlayer(const EnvironmentObject &object)
{
    EnvironmentRenderProfile profile = environmentRenderProfile(object);
    Vec2 delta = sub(g_demo.player.position, object.position);
    return std::fabs(delta.x) <= profile.silhouette.radiusX * 0.92f &&
           delta.y < profile.silhouette.radiusY * 0.35f &&
           delta.y > -profile.silhouette.occlusionDepth;
}

float distance(Vec2 a, Vec2 b)
{
    return length(sub(a, b));
}

float normalizeAxis(SHORT raw, SHORT deadzone)
{
    if (raw > deadzone)
    {
        return clampf((float)(raw - deadzone) / (32767.0f - deadzone), 0.0f, 1.0f);
    }
    if (raw < -deadzone)
    {
        return clampf((float)(raw + deadzone) / (32768.0f - deadzone), -1.0f, 0.0f);
    }
    return 0.0f;
}

float normalizeTrigger(BYTE value)
{
    if (value <= XINPUT_GAMEPAD_TRIGGER_THRESHOLD)
    {
        return 0.0f;
    }
    return clampf((float)(value - XINPUT_GAMEPAD_TRIGGER_THRESHOLD) / (255.0f - XINPUT_GAMEPAD_TRIGGER_THRESHOLD), 0.0f, 1.0f);
}

int keyboardPressed(int key)
{
    return key >= 0 && key < 256 ? g_demo.keyboard.pressed[key] : 0;
}

int keyboardDown(int key)
{
    return key >= 0 && key < 256 ? g_demo.keyboard.down[key] : 0;
}

int controllerButtonPressed(WORD mask)
{
    return (g_demo.controller.buttons & mask) && !(g_demo.controller.prevButtons & mask);
}

int controllerButtonReleased(WORD mask)
{
    return !(g_demo.controller.buttons & mask) && (g_demo.controller.prevButtons & mask);
}

void setNotification(const wchar_t *text)
{
    wcsncpy(g_demo.notification, text, 255);
    g_demo.notification[255] = 0;
    g_demo.notificationTimer = 3.8f;
}

Image *loadAsset(const wchar_t *relativePath)
{
    Image *image = new Image(relativePath);
    if (image->GetLastStatus() != Ok)
    {
        delete image;
        return NULL;
    }
    return image;
}

void releaseAssets()
{
    delete g_demo.assets.playerSheet;
    delete g_demo.assets.openingStoryboard;
    delete g_demo.assets.enemyRosterSheet;
    delete g_demo.assets.basicEnemyAnimSheet;
    delete g_demo.assets.bossAnimSheet;
    delete g_demo.assets.environmentPropsSheet;
    delete g_demo.assets.worldMap;
    delete g_demo.assets.worldKeyart;
    delete g_demo.assets.uiMenuPanel;
    delete g_demo.assets.hudSheet;
    delete g_demo.assets.iconsSheet;
    ZeroMemory(&g_demo.assets, sizeof(g_demo.assets));
}

void loadAssets()
{
    g_demo.assets.playerSheet = loadAsset(L"assets\\innsmouth_island\\innsmouth_player_fishman_sheet.png");
    g_demo.assets.openingStoryboard = loadAsset(L"assets\\innsmouth_island\\innsmouth_opening_storyboard.png");
    g_demo.assets.enemyRosterSheet = loadAsset(L"assets\\innsmouth_island\\innsmouth_enemy_roster_sheet.png");
    g_demo.assets.basicEnemyAnimSheet = loadAsset(L"assets\\innsmouth_island\\innsmouth_basic_enemy_anim_sheet.png");
    g_demo.assets.bossAnimSheet = loadAsset(L"assets\\innsmouth_island\\innsmouth_boss_duo_anim_sheet.png");
    g_demo.assets.environmentPropsSheet = loadAsset(L"assets\\innsmouth_island\\innsmouth_environment_props_sheet.png");
    g_demo.assets.worldMap = loadAsset(L"assets\\innsmouth_island\\innsmouth_world_map.png");
    g_demo.assets.worldKeyart = loadAsset(L"assets\\innsmouth_island\\innsmouth_world_keyart.png");
    g_demo.assets.uiMenuPanel = loadAsset(L"assets\\innsmouth_island\\innsmouth_ui_menu_panel.png");
    g_demo.assets.hudSheet = loadAsset(L"assets\\innsmouth_island\\innsmouth_hud_sheet.png");
    g_demo.assets.iconsSheet = loadAsset(L"assets\\innsmouth_island\\innsmouth_icons_sheet.png");
}

void clearTransientKeyboard()
{
    ZeroMemory(g_demo.keyboard.pressed, sizeof(g_demo.keyboard.pressed));
    ZeroMemory(g_demo.keyboard.released, sizeof(g_demo.keyboard.released));
}

void loadXInput()
{
    const wchar_t *dlls[] = {L"xinput1_4.dll", L"xinput1_3.dll", L"xinput9_1_0.dll"};
    for (int index = 0; index < 3; ++index)
    {
        g_demo.xinput.module = LoadLibraryW(dlls[index]);
        if (g_demo.xinput.module)
        {
            g_demo.xinput.getState = (XInputGetStateProc)GetProcAddress(g_demo.xinput.module, "XInputGetState");
            if (g_demo.xinput.getState)
            {
                return;
            }
            FreeLibrary(g_demo.xinput.module);
            g_demo.xinput.module = NULL;
        }
    }
}

void unloadXInput()
{
    if (g_demo.xinput.module)
    {
        FreeLibrary(g_demo.xinput.module);
    }
    ZeroMemory(&g_demo.xinput, sizeof(g_demo.xinput));
}

void pollController()
{
    g_demo.controller.prevButtons = g_demo.controller.buttons;
    g_demo.controller.buttons = 0;
    g_demo.controller.connected = 0;
    g_demo.controller.lx = 0.0f;
    g_demo.controller.ly = 0.0f;
    g_demo.controller.rx = 0.0f;
    g_demo.controller.ry = 0.0f;
    g_demo.controller.lt = 0.0f;
    g_demo.controller.rt = 0.0f;

    if (g_demo.xinput.getState)
    {
        XINPUT_STATE state;
        ZeroMemory(&state, sizeof(state));
        if (g_demo.xinput.getState(0, &state) == ERROR_SUCCESS)
        {
            g_demo.controller.connected = 1;
            g_demo.controller.buttons = state.Gamepad.wButtons;
            g_demo.controller.lx = normalizeAxis(state.Gamepad.sThumbLX, XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE);
            g_demo.controller.ly = -normalizeAxis(state.Gamepad.sThumbLY, XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE);
            g_demo.controller.rx = normalizeAxis(state.Gamepad.sThumbRX, XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE);
            g_demo.controller.ry = -normalizeAxis(state.Gamepad.sThumbRY, XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE);
            g_demo.controller.lt = normalizeTrigger(state.Gamepad.bLeftTrigger);
            g_demo.controller.rt = normalizeTrigger(state.Gamepad.bRightTrigger);
        }
    }
}

const wchar_t *enemyName(EnemyKind kind)
{
    switch (kind)
    {
    case ENEMY_DEEP_ONE:
        return L"Deep One Raider";
    case ENEMY_SHOGGOTH_SPAWN:
        return L"Shoggoth Spawn";
    case ENEMY_NIGHTGAUNT:
        return L"Nightgaunt Stalker";
    case ENEMY_MI_GO:
        return L"Mi-Go Scavenger";
    case ENEMY_GHOUL:
        return L"Ghoul Woodsman";
    case ENEMY_CULTIST:
        return L"Cultist Harpooner";
    case ENEMY_STAR_SPAWN:
        return L"Star-Spawn Wretch";
    case ENEMY_DROWNED_PILGRIM:
        return L"Drowned Pilgrim";
    case ENEMY_REPTILIAN_DEITY:
        return L"Reptilian Abyss Prince";
    default:
        return L"Jaguar Eclipse Tyrant";
    }
}

const wchar_t *pickupName(PickupKind kind)
{
    switch (kind)
    {
    case PICKUP_THROWING_KNIFE:
        return L"Throwing Knives";
    case PICKUP_FIRE_BOMB:
        return L"Brine Flask";
    case PICKUP_SEED_POD:
        return L"Dust Seed Pod";
    default:
        return L"Brine Salt";
    }
}

const wchar_t *currentConsumableName()
{
    switch (g_demo.currentConsumable)
    {
    case 0:
        return L"Throwing Knives";
    case 1:
        return L"Brine Flasks";
    default:
        return L"Dust Seed Pods";
    }
}

const wchar_t *saveFilePath()
{
    return L"innsmouth_island_save.dat";
}

void initializeUnlocks()
{
    ZeroMemory(g_demo.weaponUnlocked, sizeof(g_demo.weaponUnlocked));
    ZeroMemory(g_demo.armorUnlocked, sizeof(g_demo.armorUnlocked));
    for (int index = 0; index < kWeaponCount; ++index)
    {
        if (kWeapons[index].unlockCost == 0 && !kWeapons[index].newGamePlus)
        {
            g_demo.weaponUnlocked[index] = 1;
        }
    }
    for (int index = 0; index < kArmorSetCount; ++index)
    {
        if (index == 0 || (!kArmorSets[index].crafted && !kArmorSets[index].newGamePlus && index < 3))
        {
            g_demo.armorUnlocked[index] = 1;
        }
    }
    g_demo.equippedMeleeWeapon = 0;
    g_demo.equippedProjectileWeapon = 16;
    g_demo.equippedArmorSet = 0;
}

void resetShelters()
{
    const Vec2 shelterPositions[kShelterCount] = {
        {220.0f, 2580.0f},
        {1180.0f, 2060.0f},
        {2100.0f, 1550.0f},
        {2950.0f, 1120.0f},
        {3460.0f, 760.0f}};
    for (int index = 0; index < kShelterCount; ++index)
    {
        g_demo.shelters[index].position = shelterPositions[index];
        g_demo.shelters[index].discovered = index == 0 ? 1 : 0;
        g_demo.shelters[index].activated = index == 0 ? 1 : 0;
    }
    g_demo.nearestShelterIndex = 0;
    g_demo.activeShelterIndex = 0;
}

void resetPickups()
{
    const PickupKind kinds[kPickupCount] = {
        PICKUP_BRINE_SALT, PICKUP_THROWING_KNIFE, PICKUP_SEED_POD, PICKUP_BRINE_SALT,
        PICKUP_FIRE_BOMB, PICKUP_BRINE_SALT, PICKUP_THROWING_KNIFE, PICKUP_BRINE_SALT,
        PICKUP_SEED_POD, PICKUP_BRINE_SALT, PICKUP_THROWING_KNIFE, PICKUP_FIRE_BOMB,
        PICKUP_BRINE_SALT, PICKUP_SEED_POD, PICKUP_BRINE_SALT, PICKUP_THROWING_KNIFE,
        PICKUP_BRINE_SALT, PICKUP_FIRE_BOMB, PICKUP_SEED_POD, PICKUP_BRINE_SALT};
    const Vec2 positions[kPickupCount] = {
        {420.0f, 2480.0f}, {650.0f, 2330.0f}, {860.0f, 2210.0f}, {1040.0f, 2120.0f},
        {1280.0f, 1970.0f}, {1420.0f, 1880.0f}, {1650.0f, 1740.0f}, {1840.0f, 1660.0f},
        {2010.0f, 1560.0f}, {2190.0f, 1450.0f}, {2380.0f, 1360.0f}, {2570.0f, 1260.0f},
        {2730.0f, 1180.0f}, {2890.0f, 1080.0f}, {3070.0f, 980.0f}, {3250.0f, 900.0f},
        {3370.0f, 860.0f}, {3480.0f, 820.0f}, {3600.0f, 790.0f}, {3720.0f, 760.0f}};
    for (int index = 0; index < kPickupCount; ++index)
    {
        g_demo.pickups[index].kind = kinds[index];
        g_demo.pickups[index].position = positions[index];
        g_demo.pickups[index].active = 1;
        g_demo.pickups[index].variant = index % 3;
    }
}

void saveProgress()
{
    FILE *file = _wfopen(saveFilePath(), L"wb");
    if (!file)
    {
        return;
    }
    SaveData data = {};
    data.brineSalt = g_demo.brineSalt;
    data.blackKelp = g_demo.blackKelp;
    data.saltSigils = g_demo.saltSigils;
    data.throwingKnives = g_demo.throwingKnives;
    data.fireBombs = g_demo.fireBombs;
    data.seedPods = g_demo.seedPods;
    data.equippedMeleeWeapon = g_demo.equippedMeleeWeapon;
    data.equippedProjectileWeapon = g_demo.equippedProjectileWeapon;
    data.equippedArmorSet = g_demo.equippedArmorSet;
    data.vitalityRank = g_demo.vitalityRank;
    data.staminaRank = g_demo.staminaRank;
    data.weaponRank = g_demo.weaponRank;
    data.armorRank = g_demo.armorRank;
    data.newGamePlusUnlocked = g_demo.newGamePlusUnlocked;
    CopyMemory(data.weaponUnlocked, g_demo.weaponUnlocked, sizeof(data.weaponUnlocked));
    CopyMemory(data.armorUnlocked, g_demo.armorUnlocked, sizeof(data.armorUnlocked));
    for (int index = 0; index < kShelterCount; ++index)
    {
        data.shelterActivated[index] = g_demo.shelters[index].activated;
    }
    fwrite(&data, sizeof(data), 1, file);
    fclose(file);
}

void loadProgress()
{
    initializeUnlocks();
    FILE *file = _wfopen(saveFilePath(), L"rb");
    if (!file)
    {
        return;
    }
    SaveData data = {};
    size_t readCount = fread(&data, sizeof(data), 1, file);
    fclose(file);
    if (readCount != 1)
    {
        return;
    }
    g_demo.brineSalt = data.brineSalt;
    g_demo.blackKelp = data.blackKelp;
    g_demo.saltSigils = data.saltSigils;
    g_demo.throwingKnives = data.throwingKnives;
    g_demo.fireBombs = data.fireBombs;
    g_demo.seedPods = data.seedPods;
    g_demo.equippedMeleeWeapon = std::clamp(data.equippedMeleeWeapon, 0, 15);
    g_demo.equippedProjectileWeapon = std::clamp(data.equippedProjectileWeapon, 16, 22);
    g_demo.equippedArmorSet = std::clamp(data.equippedArmorSet, 0, kArmorSetCount - 1);
    g_demo.vitalityRank = data.vitalityRank;
    g_demo.staminaRank = data.staminaRank;
    g_demo.weaponRank = data.weaponRank;
    g_demo.armorRank = data.armorRank;
    g_demo.newGamePlusUnlocked = data.newGamePlusUnlocked;
    CopyMemory(g_demo.weaponUnlocked, data.weaponUnlocked, sizeof(g_demo.weaponUnlocked));
    CopyMemory(g_demo.armorUnlocked, data.armorUnlocked, sizeof(g_demo.armorUnlocked));
    for (int index = 0; index < kShelterCount; ++index)
    {
        g_demo.shelters[index].activated = data.shelterActivated[index];
        g_demo.shelters[index].discovered = g_demo.shelters[index].discovered || data.shelterActivated[index];
    }
    if (g_demo.newGamePlusUnlocked)
    {
        g_demo.weaponUnlocked[15] = 1;
        g_demo.weaponUnlocked[22] = 1;
        g_demo.armorUnlocked[13] = 1;
    }
}

void resetEnvironment()
{
    const char *placementKeys[kEnvironmentObjectCount] = {
        "shoreline_gate",
        "dock_shrine",
        "brine_pillar_west",
        "salt_jetty_arch",
        "kelp_shed_outer",
        "mud_altar_approach",
        "flooded_watchpost",
        "coral_bridge_low",
        "grave_mire_marker",
        "tidal_courtyard_edge",
        "eel_hatchery_bank",
        "basalt_stair_entry",
        "obsidian_pool_north",
        "sunken_causeway_mid",
        "bone_canopy_west",
        "reef_gate_inner",
        "temple_runoff_low",
        "mangrove_spine_mid",
        "shrine_basin_outer",
        "black_reef_ascent",
        "jaguar_temple_threshold",
        "reptile_dais_west",
        "eclipse_court_center",
        "boss_sanctum_backwall"};
    const int objectTypes[kEnvironmentObjectCount] = {
        0, 1, 2, 3, 4, 5,
        6, 7, 8, 9, 10, 11,
        12, 13, 14, 15, 16, 17,
        18, 19, 20, 21, 22, 23};
    const Vec2 positions[kEnvironmentObjectCount] = {
        {220.0f, 2520.0f}, {340.0f, 2460.0f}, {470.0f, 2380.0f}, {610.0f, 2260.0f},
        {820.0f, 2200.0f}, {980.0f, 2140.0f}, {1140.0f, 2090.0f}, {1320.0f, 2030.0f},
        {1500.0f, 1960.0f}, {1680.0f, 1880.0f}, {1840.0f, 1810.0f}, {2010.0f, 1720.0f},
        {2170.0f, 1660.0f}, {2340.0f, 1560.0f}, {2510.0f, 1490.0f}, {2660.0f, 1400.0f},
        {2810.0f, 1320.0f}, {2970.0f, 1240.0f}, {3120.0f, 1170.0f}, {3290.0f, 1100.0f},
        {3440.0f, 980.0f}, {3590.0f, 900.0f}, {3720.0f, 810.0f}, {3860.0f, 740.0f}};

    for (int index = 0; index < kEnvironmentObjectCount; ++index)
    {
        g_demo.environment[index].type = objectTypes[index];
        innsmouth_runtime::copyPlacementKey(
            g_demo.environment[index].placementKey,
            sizeof(g_demo.environment[index].placementKey),
            placementKeys[index]);
        g_demo.environment[index].position = positions[index];
        g_demo.environment[index].scale = 0.88f + (float)(index % 5) * 0.08f;
    }
}

void spawnEnemy(int slot, EnemyKind kind, float x, float y, int hp, int boss)
{
    Enemy &enemy = g_demo.enemies[slot];
    enemy.kind = kind;
    enemy.position = {x, y};
    enemy.velocity = {0.0f, 0.0f};
    enemy.hp = hp;
    enemy.maxHp = hp;
    enemy.alive = 1;
    enemy.boss = boss;
    enemy.discovered = 0;
    enemy.attackCooldown = 0.0f;
    enemy.staggerTimer = 0.0f;
    enemy.animationTime = 0.0f;
    enemy.specialTimer = 0.0f;
    enemy.animationFrameCount = boss ? 16 : 12;
}

void resetEnemies()
{
    ZeroMemory(g_demo.enemies, sizeof(g_demo.enemies));
    spawnEnemy(0, ENEMY_DEEP_ONE, 760.0f, 2120.0f, 42, 0);
    spawnEnemy(1, ENEMY_SHOGGOTH_SPAWN, 990.0f, 2040.0f, 46, 0);
    spawnEnemy(2, ENEMY_NIGHTGAUNT, 1260.0f, 1910.0f, 48, 0);
    spawnEnemy(3, ENEMY_MI_GO, 1590.0f, 1760.0f, 52, 0);
    spawnEnemy(4, ENEMY_GHOUL, 1910.0f, 1620.0f, 54, 0);
    spawnEnemy(5, ENEMY_CULTIST, 2230.0f, 1450.0f, 58, 0);
    spawnEnemy(6, ENEMY_STAR_SPAWN, 2580.0f, 1240.0f, 63, 0);
    spawnEnemy(7, ENEMY_DROWNED_PILGRIM, 2910.0f, 1040.0f, 60, 0);
    spawnEnemy(8, ENEMY_REPTILIAN_DEITY, 3520.0f, 720.0f, 160, 1);
    spawnEnemy(9, ENEMY_JAGUAR_DEITY, 3680.0f, 650.0f, 172, 1);
    g_demo.enemies[8].alive = 0;
    g_demo.enemies[9].alive = 0;
    g_demo.basicEnemiesRemaining = kBasicEnemyCount;
    g_demo.bossesSpawned = 0;
}

void resetPlayer()
{
    g_demo.player.position = {140.0f, 2680.0f};
    g_demo.player.velocity = {0.0f, 0.0f};
    g_demo.player.facing = {1.0f, 0.0f};
    g_demo.player.hopHeight = 0.0f;
    g_demo.player.hopVelocity = 0.0f;
    g_demo.player.maxHp = 100 + g_demo.vitalityRank * 10;
    g_demo.player.hp = g_demo.player.maxHp;
    g_demo.player.stamina = 100.0f;
    g_demo.player.maxStamina = 100.0f + g_demo.staminaRank * 10.0f;
    g_demo.player.stamina = g_demo.player.maxStamina;
    g_demo.player.moisture = 0.85f;
    g_demo.player.breathingSync = 0.5f;
    g_demo.player.healAccumulator = 0.0f;
    g_demo.player.idleTimer = 0.0f;
    g_demo.player.dodgeTimer = 0.0f;
    g_demo.player.parryTimer = 0.0f;
    g_demo.player.blockTimer = 0.0f;
    g_demo.player.attackCooldown = 0.0f;
    g_demo.player.slideTimer = 0.0f;
    g_demo.player.hurtFlash = 0.0f;
    g_demo.player.actionTime = 0.0f;
    g_demo.player.airActions = 2;
    g_demo.player.animation = PLAYER_ANIM_CRAWL;
}

void startOpeningSequence()
{
    resetPlayer();
    resetEnemies();
    resetEnvironment();
    g_demo.mode = MODE_OPENING;
    g_demo.openingTimer = 0.0f;
    g_demo.activeQuestStage = 0;
    g_demo.currentViewTab = TAB_CHARACTER;
    g_demo.currentViewSelection = 0;
    g_demo.showPrompt = 1;
    g_demo.showControlsCard = 1;
    g_demo.victoryUnlocked = 0;
    g_demo.cameraYaw = 0.08f;
    g_demo.cameraPitch = 0.06f;
    g_demo.cameraShake = 0.0f;
    g_demo.menuInputCooldown = 0.0f;
    g_demo.controllerBHold = 0.0f;
    g_demo.controllerRTHold = 0.0f;
    g_demo.focusPulse = 0.0f;
    g_demo.templeSeals = 0;
    g_demo.blackKelp = std::max(g_demo.blackKelp, 2);
    g_demo.saltSigils = std::max(g_demo.saltSigils, 1);
    g_demo.focusTargetIndex = -1;
    g_demo.currentConsumable = 0;
    setNotification(L"Research-integrated tidefall: benchmarked modularity, style discipline, and provenance now guide this shore.");
}

void resetToTitle()
{
    g_demo.mode = MODE_TITLE;
    g_demo.selectedTitleOption = 0;
    g_demo.selectedPauseOption = 0;
    g_demo.currentViewTab = TAB_CHARACTER;
    g_demo.currentViewSelection = 0;
    g_demo.showPrompt = 1;
    g_demo.showControlsCard = 1;
    g_demo.cameraYaw = 0.08f;
    g_demo.cameraPitch = 0.06f;
    g_demo.openingTimer = 0.0f;
    g_demo.worldTime = 0.0f;
    g_demo.notificationTimer = 0.0f;
    g_demo.notification[0] = 0;
    g_demo.focusPulse = 0.0f;
    g_demo.templeSeals = 0;
    g_demo.focusTargetIndex = -1;
    g_demo.currentConsumable = 0;
    resetEnvironment();
    resetPickups();
    resetPlayer();
    resetEnemies();
}

void initializeDemo()
{
    GdiplusStartupInput startupInput;
    GdiplusStartup(&g_demo.gdiplusToken, &startupInput, NULL);
    loadAssets();
    loadRuntimeMetadata();
    loadXInput();
    resetShelters();
    initializeUnlocks();
    g_demo.brineSalt = 0;
    g_demo.blackKelp = 2;
    g_demo.saltSigils = 1;
    g_demo.throwingKnives = 6;
    g_demo.fireBombs = 2;
    g_demo.seedPods = 3;
    g_demo.currentConsumable = 0;
    g_demo.vitalityRank = 0;
    g_demo.staminaRank = 0;
    g_demo.weaponRank = 0;
    g_demo.armorRank = 0;
    g_demo.newGamePlusUnlocked = 0;
    loadProgress();
    resetToTitle();
}

void shutdownDemo()
{
    unloadXInput();
    releaseAssets();
    GdiplusShutdown(g_demo.gdiplusToken);
}

void fillRect(HDC hdc, int left, int top, int right, int bottom, COLORREF color)
{
    RECT rect = {left, top, right, bottom};
    HBRUSH brush = CreateSolidBrush(color);
    FillRect(hdc, &rect, brush);
    DeleteObject(brush);
}

void drawTextLine(HDC hdc, int x, int y, COLORREF color, const wchar_t *text)
{
    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, color);
    TextOutW(hdc, x, y, text, (int)wcslen(text));
}

void drawParagraph(HDC hdc, RECT rect, COLORREF color, const wchar_t *text)
{
    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, color);
    DrawTextW(hdc, text, -1, &rect, DT_WORDBREAK);
}

void drawImageAlpha(Graphics &graphics, Image *image, float x, float y, float width, float height, float alpha)
{
    if (!image)
    {
        return;
    }

    ColorMatrix matrix = {
        1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 0.0f, alpha, 0.0f,
        0.0f, 0.0f, 0.0f, 0.0f, 1.0f};
    ImageAttributes attributes;
    RectF target(x, y, width, height);
    attributes.SetColorMatrix(&matrix);
    graphics.DrawImage(image, target, 0.0f, 0.0f, (REAL)image->GetWidth(), (REAL)image->GetHeight(), UnitPixel, &attributes);
}

void drawImageFrame(Graphics &graphics, Image *image, int frameIndex, int columns, int rows, float x, float y, float width, float height, float alpha)
{
    if (!image || columns <= 0 || rows <= 0)
    {
        return;
    }
    int frameCount = columns * rows;
    if (frameIndex < 0)
    {
        frameIndex = 0;
    }
    frameIndex %= frameCount;
    int frameWidth = (int)image->GetWidth() / columns;
    int frameHeight = (int)image->GetHeight() / rows;
    int sourceX = (frameIndex % columns) * frameWidth;
    int sourceY = (frameIndex / columns) * frameHeight;

    ColorMatrix matrix = {
        1.0f, 0.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 0.0f, alpha, 0.0f,
        0.0f, 0.0f, 0.0f, 0.0f, 1.0f};
    ImageAttributes attributes;
    RectF target(x, y, width, height);
    attributes.SetColorMatrix(&matrix);
    graphics.DrawImage(image, target, (REAL)sourceX, (REAL)sourceY, (REAL)frameWidth, (REAL)frameHeight, UnitPixel, &attributes);
}

Color alphaColor(COLORREF color, BYTE alpha)
{
    return Color(alpha, GetRValue(color), GetGValue(color), GetBValue(color));
}

COLORREF blendColor(COLORREF a, COLORREF b, float ratio)
{
    ratio = clampf(ratio, 0.0f, 1.0f);
    BYTE red = (BYTE)((1.0f - ratio) * GetRValue(a) + ratio * GetRValue(b));
    BYTE green = (BYTE)((1.0f - ratio) * GetGValue(a) + ratio * GetGValue(b));
    BYTE blue = (BYTE)((1.0f - ratio) * GetBValue(a) + ratio * GetBValue(b));
    return RGB(red, green, blue);
}

struct ArmorVisualStyle
{
    COLORREF shellColor;
    COLORREF trimColor;
    COLORREF clothColor;
    COLORREF glowColor;
    int helmStyle;
    int mantleStyle;
    int shoulderStyle;
};

ArmorVisualStyle armorVisualStyle(int armorSet)
{
    switch (std::clamp(armorSet, 0, kArmorSetCount - 1))
    {
    case 0:
        return {RGB(118, 124, 126), RGB(188, 178, 150), RGB(86, 92, 84), RGB(108, 144, 136), 0, 0, 0};
    case 1:
        return {RGB(128, 136, 144), RGB(196, 204, 194), RGB(82, 88, 92), RGB(110, 138, 146), 1, 0, 1};
    case 2:
        return {RGB(102, 140, 124), RGB(180, 214, 156), RGB(72, 98, 82), RGB(96, 176, 138), 0, 1, 0};
    case 3:
        return {RGB(112, 104, 92), RGB(178, 152, 118), RGB(84, 72, 66), RGB(144, 126, 104), 2, 0, 2};
    case 4:
        return {RGB(134, 138, 150), RGB(216, 216, 200), RGB(86, 80, 92), RGB(126, 170, 196), 1, 1, 1};
    case 5:
        return {RGB(106, 118, 96), RGB(196, 190, 156), RGB(80, 92, 74), RGB(122, 166, 114), 0, 2, 0};
    case 6:
        return {RGB(126, 118, 122), RGB(210, 192, 168), RGB(92, 72, 82), RGB(170, 150, 174), 1, 0, 1};
    case 7:
        return {RGB(132, 138, 146), RGB(212, 220, 224), RGB(64, 74, 78), RGB(120, 170, 180), 2, 2, 2};
    case 8:
        return {RGB(86, 78, 116), RGB(196, 184, 236), RGB(74, 62, 108), RGB(150, 146, 214), 1, 1, 0};
    case 9:
        return {RGB(98, 118, 136), RGB(210, 228, 234), RGB(60, 76, 88), RGB(118, 188, 214), 2, 2, 2};
    case 10:
        return {RGB(118, 96, 110), RGB(214, 180, 162), RGB(98, 70, 78), RGB(182, 126, 144), 1, 1, 1};
    case 11:
        return {RGB(98, 102, 106), RGB(188, 170, 130), RGB(72, 82, 74), RGB(152, 164, 116), 2, 2, 2};
    case 12:
        return {RGB(116, 104, 138), RGB(228, 212, 160), RGB(78, 64, 98), RGB(182, 154, 212), 2, 2, 2};
    default:
        return {RGB(74, 72, 110), RGB(238, 216, 120), RGB(86, 56, 98), RGB(212, 106, 154), 2, 2, 2};
    }
}

void fillPolygonColor(Graphics &graphics, const PointF *points, int count, COLORREF color, BYTE alpha)
{
    SolidBrush brush(alphaColor(color, alpha));
    graphics.FillPolygon(&brush, points, count);
}

void drawPlayerEquipmentOverlay(Graphics &graphics, float x, float y, float width, float height, float alpha)
{
    BYTE alphaByte = (BYTE)std::clamp((int)(alpha * 255.0f), 0, 255);
    ArmorVisualStyle style = armorVisualStyle(g_demo.equippedArmorSet);
    const WeaponDef &melee = kWeapons[g_demo.equippedMeleeWeapon];
    const WeaponDef &projectile = kWeapons[g_demo.equippedProjectileWeapon];
    PlayerAttachmentMap attachmentMap = playerAttachmentMap(g_demo.equippedArmorSet, g_demo.equippedMeleeWeapon, g_demo.equippedProjectileWeapon);

    float centerX = x + width * 0.5f;
    float headY = y + height * 0.16f;
    float chestY = y + height * 0.34f;
    float waistY = y + height * 0.58f;
    float kneeY = y + height * 0.79f;
    float hemY = y + height * 0.93f;
    float shoulderSpan = width * 0.24f;
    float headX = x + width * attachmentMap.sockets[SOCKET_HEAD].u;
    float headSocketY = y + height * attachmentMap.sockets[SOCKET_HEAD].v;
    float torsoX = x + width * attachmentMap.sockets[SOCKET_TORSO].u;
    float torsoY = y + height * attachmentMap.sockets[SOCKET_TORSO].v;
    float rightHandX = x + width * attachmentMap.sockets[SOCKET_RIGHT_HAND].u;
    float rightHandY = y + height * attachmentMap.sockets[SOCKET_RIGHT_HAND].v;
    float leftHandX = x + width * attachmentMap.sockets[SOCKET_LEFT_HAND].u;
    float leftHandY = y + height * attachmentMap.sockets[SOCKET_LEFT_HAND].v;
    float hipX = x + width * attachmentMap.sockets[SOCKET_HIP].u;
    float hipY = y + height * attachmentMap.sockets[SOCKET_HIP].v;

    PointF torso[] = {
        PointF(torsoX - width * 0.16f, torsoY - height * 0.07f),
        PointF(torsoX + width * 0.16f, torsoY - height * 0.07f),
        PointF(torsoX + width * 0.12f, hipY),
        PointF(torsoX - width * 0.12f, hipY)};
    fillPolygonColor(graphics, torso, 4, style.shellColor, alphaByte);

    PointF mantle[] = {
        PointF(torsoX - width * 0.21f, torsoY - height * 0.05f),
        PointF(torsoX + width * 0.21f, torsoY - height * 0.05f),
        PointF(torsoX + width * 0.10f, hipY + height * 0.08f),
        PointF(torsoX - width * 0.10f, hipY + height * 0.08f)};
    fillPolygonColor(graphics, mantle, 4, style.clothColor, (BYTE)(alphaByte * 0.78f));

    SolidBrush trimBrush(alphaColor(style.trimColor, alphaByte));
    SolidBrush glowBrush(alphaColor(style.glowColor, (BYTE)(alphaByte * 0.70f)));
    SolidBrush clothBrush(alphaColor(style.clothColor, (BYTE)(alphaByte * 0.82f)));
    Pen trimPen(alphaColor(blendColor(style.trimColor, RGB(255, 255, 255), 0.16f), alphaByte), 2.0f);
    Pen darkPen(alphaColor(blendColor(style.shellColor, RGB(0, 0, 0), 0.36f), (BYTE)(alphaByte * 0.95f)), 2.0f);

    graphics.FillRectangle(&trimBrush, torsoX - width * 0.055f, torsoY - height * 0.01f, width * 0.11f, height * 0.08f);
    graphics.FillEllipse(&glowBrush, torsoX - width * 0.035f, torsoY + height * 0.02f, width * 0.07f, height * 0.05f);

    graphics.FillEllipse(&trimBrush, headX - width * 0.11f, headSocketY - height * 0.01f, width * 0.22f, height * 0.14f);
    if (style.helmStyle == 1)
    {
        PointF crest[] = {
            PointF(headX, headSocketY - height * 0.05f),
            PointF(headX + width * 0.04f, headSocketY + height * 0.03f),
            PointF(headX - width * 0.04f, headSocketY + height * 0.03f)};
        fillPolygonColor(graphics, crest, 3, style.glowColor, alphaByte);
    }
    else if (style.helmStyle == 2)
    {
        PointF leftHorn[] = {
            PointF(headX - width * 0.05f, headSocketY + height * 0.01f),
            PointF(headX - width * 0.15f, headSocketY - height * 0.04f),
            PointF(headX - width * 0.10f, headSocketY + height * 0.05f)};
        PointF rightHorn[] = {
            PointF(headX + width * 0.05f, headSocketY + height * 0.01f),
            PointF(headX + width * 0.15f, headSocketY - height * 0.04f),
            PointF(headX + width * 0.10f, headSocketY + height * 0.05f)};
        fillPolygonColor(graphics, leftHorn, 3, style.trimColor, alphaByte);
        fillPolygonColor(graphics, rightHorn, 3, style.trimColor, alphaByte);
    }

    graphics.FillEllipse(&clothBrush, torsoX - shoulderSpan - width * 0.05f, torsoY - height * 0.09f, width * 0.11f, height * 0.08f);
    graphics.FillEllipse(&clothBrush, torsoX + shoulderSpan - width * 0.06f, torsoY - height * 0.09f, width * 0.11f, height * 0.08f);

    graphics.FillRectangle(&trimBrush, torsoX - shoulderSpan - width * 0.02f, torsoY + height * 0.01f, width * 0.06f, height * 0.18f);
    graphics.FillRectangle(&trimBrush, torsoX + shoulderSpan - width * 0.04f, torsoY + height * 0.01f, width * 0.06f, height * 0.18f);
    graphics.FillRectangle(&trimBrush, hipX - width * 0.12f, hipY + height * 0.03f, width * 0.08f, height * 0.20f);
    graphics.FillRectangle(&trimBrush, hipX + width * 0.04f, hipY + height * 0.03f, width * 0.08f, height * 0.20f);

    if (style.mantleStyle > 0)
    {
        PointF skirt[] = {
            PointF(hipX - width * 0.15f, hipY),
            PointF(hipX + width * 0.15f, hipY),
            PointF(hipX + width * 0.10f, hemY),
            PointF(hipX - width * 0.10f, hemY)};
        fillPolygonColor(graphics, skirt, 4, blendColor(style.clothColor, style.shellColor, 0.30f), (BYTE)(alphaByte * 0.75f));
    }

    PointF collar[] = {
        PointF(torsoX - width * 0.14f, torsoY - height * 0.05f),
        PointF(torsoX + width * 0.14f, torsoY - height * 0.05f),
        PointF(torsoX + width * 0.09f, torsoY + height * 0.03f),
        PointF(torsoX - width * 0.09f, torsoY + height * 0.03f)};
    graphics.DrawPolygon(&trimPen, collar, 4);

    int meleeForm = g_demo.equippedMeleeWeapon % 4;
    float weaponBaseX = rightHandX;
    float weaponBaseY = rightHandY;
    Pen haftPen(alphaColor(blendColor(style.trimColor, RGB(70, 52, 38), 0.45f), alphaByte), 3.0f);
    Pen bladePen(alphaColor(style.trimColor, alphaByte), 2.5f);
    graphics.DrawLine(&haftPen, weaponBaseX, weaponBaseY, weaponBaseX + width * 0.12f, weaponBaseY - height * 0.18f);
    if (meleeForm == 0)
    {
        PointF blade[] = {
            PointF(weaponBaseX + width * 0.11f, weaponBaseY - height * 0.19f),
            PointF(weaponBaseX + width * 0.18f, weaponBaseY - height * 0.31f),
            PointF(weaponBaseX + width * 0.15f, weaponBaseY - height * 0.13f)};
        fillPolygonColor(graphics, blade, 3, style.trimColor, alphaByte);
    }
    else if (meleeForm == 1)
    {
        graphics.DrawArc(&bladePen, weaponBaseX + width * 0.07f, weaponBaseY - height * 0.30f, width * 0.16f, height * 0.16f, 210.0f, 180.0f);
    }
    else if (meleeForm == 2)
    {
        graphics.DrawLine(&bladePen, weaponBaseX + width * 0.12f, weaponBaseY - height * 0.18f, weaponBaseX + width * 0.20f, weaponBaseY - height * 0.34f);
        graphics.DrawLine(&bladePen, weaponBaseX + width * 0.11f, weaponBaseY - height * 0.20f, weaponBaseX + width * 0.03f, weaponBaseY - height * 0.33f);
    }
    else
    {
        graphics.FillRectangle(&trimBrush, weaponBaseX + width * 0.10f, weaponBaseY - height * 0.27f, width * 0.11f, height * 0.08f);
    }

    float rangedX = leftHandX;
    float rangedY = leftHandY;
    Pen rangedPen(alphaColor(blendColor(style.glowColor, RGB(24, 28, 34), 0.25f), alphaByte), 2.4f);
    if (projectile.unlockCost == 0 || projectile.unlockCost == 24 || projectile.unlockCost == 48)
    {
        graphics.DrawLine(&rangedPen, rangedX, rangedY + height * 0.12f, rangedX - width * 0.06f, rangedY - height * 0.04f);
        graphics.DrawLine(&rangedPen, rangedX - width * 0.06f, rangedY - height * 0.04f, rangedX - width * 0.01f, rangedY - height * 0.06f);
    }
    else
    {
        graphics.DrawArc(&rangedPen, rangedX - width * 0.10f, rangedY - height * 0.04f, width * 0.13f, height * 0.15f, 300.0f, 220.0f);
        graphics.DrawLine(&rangedPen, rangedX - width * 0.08f, rangedY - height * 0.02f, rangedX + width * 0.01f, rangedY + height * 0.08f);
    }

    if (melee.damage >= 33)
    {
        graphics.DrawLine(&darkPen, hipX + width * 0.01f, kneeY, hipX + width * 0.22f, kneeY - height * 0.06f);
    }
}

void drawPlayerPresentation(Graphics &graphics, float x, float y, float width, float height, int frame, float alpha)
{
    drawImageFrame(graphics, g_demo.assets.playerSheet, frame, kPlayerSheetColumns, kPlayerSheetRows, x, y, width, height, alpha);
    drawPlayerEquipmentOverlay(graphics, x, y, width, height, alpha);
}

int enemyRosterFrame(EnemyKind kind)
{
    return (int)kind < 8 ? (int)kind : ((int)kind - 8) + 6;
}

Vec2 worldToScreen(Vec2 world, int clientWidth, int clientHeight, float *outScale)
{
    Vec2 camera = g_demo.player.position;
    Vec2 relative = sub(world, camera);
    float cs = std::cos(g_demo.cameraYaw);
    float sn = std::sin(g_demo.cameraYaw);
    float rotatedX = relative.x * cs - relative.y * sn;
    float rotatedY = relative.x * sn + relative.y * cs;
    float horizon = clientHeight * (0.38f + g_demo.cameraPitch * 0.08f);
    float scaleValue = clampf(0.38f + (2800.0f - rotatedY) / 3000.0f, 0.22f, 1.7f);
    float shakeX = std::sin(g_demo.worldTime * 60.0f) * g_demo.cameraShake * 16.0f;
    float shakeY = std::cos(g_demo.worldTime * 48.0f) * g_demo.cameraShake * 10.0f;
    Vec2 screen;
    screen.x = clientWidth * 0.5f + rotatedX * 0.20f + shakeX;
    screen.y = horizon + (rotatedY - 1200.0f) * 0.12f + shakeY;
    *outScale = scaleValue;
    return screen;
}

float moistureAtPosition(Vec2 position)
{
    float shoreline = clampf((kWorldMetersY - position.y) / kWorldMetersY, 0.0f, 1.0f);
    float swamp = 1.0f - clampf(std::fabs(position.x - 2200.0f) / 1200.0f, 0.0f, 1.0f);
    float rainHumidity = 0.64f + 0.18f * std::sin(g_demo.worldTime * 0.2f);
    return clampf(0.35f + shoreline * 0.45f + swamp * 0.20f + rainHumidity * 0.20f, 0.0f, 1.0f);
}

float breathingResonance(void)
{
    float environmentPulse = 0.5f + 0.5f * std::sin(g_demo.worldTime * 0.95f);
    float playerPulse = 0.5f + 0.5f * std::sin(g_demo.worldTime * 0.95f + g_demo.player.idleTimer * 0.15f);
    return 1.0f - std::fabs(environmentPulse - playerPulse);
}

int nearestEnemyIndex(float maxDistance, int onlyAlive)
{
    int bestIndex = -1;
    float bestDistance = maxDistance;
    for (int index = 0; index < kTotalEnemies; ++index)
    {
        Enemy &enemy = g_demo.enemies[index];
        if (onlyAlive && !enemy.alive)
        {
            continue;
        }
        if (!enemy.discovered && !enemy.alive)
        {
            continue;
        }
        float candidate = distance(g_demo.player.position, enemy.position);
        if (candidate < bestDistance)
        {
            bestDistance = candidate;
            bestIndex = index;
        }
    }
    return bestIndex;
}

int discoveredEnemyCount()
{
    int count = 0;
    for (int index = 0; index < kTotalEnemies; ++index)
    {
        if (g_demo.enemies[index].discovered || g_demo.enemies[index].alive)
        {
            count += 1;
        }
    }
    return count;
}

int isSealBearer(EnemyKind kind)
{
    return kind == ENEMY_MI_GO || kind == ENEMY_CULTIST || kind == ENEMY_STAR_SPAWN || kind == ENEMY_DROWNED_PILGRIM;
}

void updateFocusTarget(int focusHeld)
{
    if (focusHeld)
    {
        g_demo.focusTargetIndex = nearestEnemyIndex(620.0f, 1);
        g_demo.focusPulse += 0.016f;
    }
    else
    {
        g_demo.focusTargetIndex = -1;
        g_demo.focusPulse = 0.0f;
    }
}

void applyPlayerHit(int damage, float shake)
{
    if (damage <= 0)
    {
        return;
    }
    damage = std::max(1, damage - kArmorSets[g_demo.equippedArmorSet].defense / 4 - g_demo.armorRank);
    g_demo.player.hp -= damage;
    g_demo.player.hurtFlash = 0.35f;
    g_demo.cameraShake = std::max(g_demo.cameraShake, shake);
    if (g_demo.player.hp <= 0)
    {
        g_demo.player.hp = 0;
        g_demo.mode = MODE_GAME_OVER;
    }
}

int resolveIncomingAttack(int enemyIndex, int baseDamage)
{
    if (g_demo.player.parryTimer > 0.0f)
    {
        applyEnemyDamage(enemyIndex, g_demo.enemies[enemyIndex].boss ? 18 : 10, 0.75f);
        setNotification(L"Parry window matched. The wet rhythm breaks their strike.");
        return 0;
    }
    if (g_demo.player.blockTimer > 0.0f)
    {
        g_demo.player.stamina = std::max(0.0f, g_demo.player.stamina - 8.0f);
        return std::max(1, baseDamage / 3);
    }
    if (g_demo.player.dodgeTimer > 0.0f)
    {
        return 0;
    }
    return baseDamage;
}

void spawnBossesIfReady()
{
    if (g_demo.bossesSpawned || g_demo.basicEnemiesRemaining > 0 || g_demo.templeSeals < 4)
    {
        return;
    }
    if (g_demo.player.position.x < 3320.0f || g_demo.player.position.y > 900.0f)
    {
        return;
    }
    g_demo.bossesSpawned = 1;
    g_demo.enemies[8].alive = 1;
    g_demo.enemies[9].alive = 1;
    setNotification(L"The temple wakes. Reptilian abyss and jaguar eclipse deities descend.");
}

void applyEnemyDamage(int index, int damage, float stagger)
{
    if (index < 0 || index >= kTotalEnemies)
    {
        return;
    }
    Enemy &enemy = g_demo.enemies[index];
    if (!enemy.alive)
    {
        return;
    }
    enemy.hp -= damage;
    enemy.staggerTimer = std::max(enemy.staggerTimer, stagger);
    enemy.animationTime = 0.0f;
    g_demo.cameraShake = std::max(g_demo.cameraShake, enemy.boss ? 0.26f : 0.16f);
    if (enemy.hp <= 0)
    {
        enemy.hp = 0;
        enemy.alive = 0;
        if (isSealBearer(enemy.kind))
        {
            g_demo.templeSeals = std::min(4, g_demo.templeSeals + 1);
            g_demo.saltSigils += 1;
        }
        g_demo.blackKelp += enemy.boss ? 2 : 1;
        if (!enemy.boss)
        {
            g_demo.basicEnemiesRemaining -= 1;
            if (g_demo.basicEnemiesRemaining < 0)
            {
                g_demo.basicEnemiesRemaining = 0;
            }
        }
        else if (!g_demo.enemies[8].alive && !g_demo.enemies[9].alive)
        {
            g_demo.victoryUnlocked = 1;
            g_demo.mode = MODE_VICTORY;
        }
        if (!enemy.boss && isSealBearer(enemy.kind))
        {
            setNotification(L"A temple seal and salt sigil surface from the corpse-tide.");
        }
        else
        {
            setNotification(enemy.boss ? L"An eldritch deity falls back into the wet stone dark." : L"A lesser horror collapses into the ooze.");
        }
    }
}

void startDodge(Vec2 direction)
{
    if (g_demo.player.stamina < 16.0f || g_demo.player.dodgeTimer > 0.0f)
    {
        return;
    }
    if (g_demo.player.hopHeight > 0.0f && g_demo.player.airActions <= 0)
    {
        return;
    }
    if (length(direction) < 0.01f)
    {
        direction = g_demo.player.facing;
    }
    direction = normalize(direction);
    g_demo.player.stamina -= 16.0f;
    g_demo.player.dodgeTimer = 0.26f;
    g_demo.player.velocity = scale(direction, 240.0f);
    if (g_demo.player.hopHeight > 0.0f)
    {
        g_demo.player.airActions -= 1;
        g_demo.player.hopVelocity = std::max(g_demo.player.hopVelocity, 180.0f);
    }
    g_demo.player.animation = PLAYER_ANIM_DODGE;
    g_demo.player.actionTime = 0.0f;
    g_demo.cameraShake = std::max(g_demo.cameraShake, 0.12f);
}

void startParry(void)
{
    g_demo.player.parryTimer = 0.20f;
    g_demo.player.animation = PLAYER_ANIM_PARRY;
    g_demo.player.actionTime = 0.0f;
}

void handlePlayerAttack(int heavy)
{
    int target = g_demo.focusTargetIndex >= 0 ? g_demo.focusTargetIndex : nearestEnemyIndex(230.0f, 1);
    int damage = kWeapons[g_demo.equippedMeleeWeapon].damage + g_demo.weaponRank * 2 + (heavy ? 8 : 0);
    if (g_demo.player.hopHeight > 0.0f)
    {
        damage += 6;
    }
    float cost = (float)(kWeapons[g_demo.equippedMeleeWeapon].staminaCost + (heavy ? 8 : 0));
    if (g_demo.player.attackCooldown > 0.0f || g_demo.player.stamina < cost)
    {
        return;
    }
    g_demo.player.stamina -= cost;
    g_demo.player.attackCooldown = heavy ? 0.58f : 0.30f;
    g_demo.player.animation = heavy ? PLAYER_ANIM_HEAVY : PLAYER_ANIM_LIGHT;
    g_demo.player.actionTime = 0.0f;
    g_demo.cameraShake = std::max(g_demo.cameraShake, heavy ? 0.18f : 0.10f);

    if (target >= 0)
    {
        Enemy &enemy = g_demo.enemies[target];
        if (enemy.alive && distance(g_demo.player.position, enemy.position) < (heavy ? 300.0f : 225.0f))
        {
            applyEnemyDamage(target, damage, heavy ? 0.65f : 0.35f);
        }
    }
}

void beginJump()
{
    if (g_demo.player.hopHeight > 0.0f && g_demo.player.airActions <= 0)
    {
        return;
    }
    if (g_demo.player.hopHeight > 0.0f)
    {
        g_demo.player.airActions -= 1;
        g_demo.player.hopVelocity = 380.0f;
    }
    else
    {
        g_demo.player.airActions = 2;
        g_demo.player.hopVelocity = 460.0f;
    }
    g_demo.player.animation = PLAYER_ANIM_JUMP;
    g_demo.player.actionTime = 0.0f;
}

void updateMenuNavigation(float deltaSeconds, int *stepX, int *stepY)
{
    *stepX = 0;
    *stepY = 0;
    g_demo.menuInputCooldown = std::max(0.0f, g_demo.menuInputCooldown - deltaSeconds);
    if (g_demo.menuInputCooldown > 0.0f)
    {
        return;
    }

    float axisX = g_demo.controller.connected ? g_demo.controller.lx : 0.0f;
    float axisY = g_demo.controller.connected ? g_demo.controller.ly : 0.0f;
    if (keyboardPressed(VK_LEFT) || keyboardPressed('A'))
    {
        *stepX = -1;
    }
    else if (keyboardPressed(VK_RIGHT) || keyboardPressed('D'))
    {
        *stepX = 1;
    }
    else if (std::fabs(axisX) > 0.55f && std::fabs(axisX) > std::fabs(axisY))
    {
        *stepX = axisX > 0.0f ? 1 : -1;
    }

    if (keyboardPressed(VK_UP) || keyboardPressed('W'))
    {
        *stepY = -1;
    }
    else if (keyboardPressed(VK_DOWN) || keyboardPressed('S'))
    {
        *stepY = 1;
    }
    else if (std::fabs(axisY) > 0.55f && std::fabs(axisY) > std::fabs(axisX))
    {
        *stepY = axisY > 0.0f ? 1 : -1;
    }

    if (*stepX != 0 || *stepY != 0)
    {
        g_demo.menuInputCooldown = 0.18f;
    }
}

int confirmPressed()
{
    return keyboardPressed(VK_RETURN) || keyboardPressed(VK_SPACE) || controllerButtonPressed(XINPUT_GAMEPAD_A);
}

int backPressed()
{
    return keyboardPressed(VK_BACK) || keyboardPressed('B') || controllerButtonPressed(XINPUT_GAMEPAD_B);
}

int menuButtonPressed()
{
    return keyboardPressed(VK_ESCAPE) || controllerButtonPressed(XINPUT_GAMEPAD_START);
}

int viewButtonPressed()
{
    return keyboardPressed(VK_TAB) || controllerButtonPressed(XINPUT_GAMEPAD_BACK);
}

int interactPressed()
{
    return keyboardPressed('R') || controllerButtonPressed(XINPUT_GAMEPAD_DPAD_UP);
}

int cycleConsumablePressed()
{
    return keyboardPressed('Z') || controllerButtonPressed(XINPUT_GAMEPAD_DPAD_LEFT);
}

int useConsumablePressed()
{
    return keyboardPressed('T') || controllerButtonPressed(XINPUT_GAMEPAD_DPAD_RIGHT);
}

int fireProjectilePressed()
{
    return keyboardPressed('L') || controllerButtonPressed(XINPUT_GAMEPAD_RIGHT_SHOULDER);
}

int nearestShelterIndex(float maxDistance)
{
    int bestIndex = -1;
    float bestDistance = maxDistance;
    for (int index = 0; index < kShelterCount; ++index)
    {
        float candidate = distance(g_demo.player.position, g_demo.shelters[index].position);
        if (candidate < bestDistance)
        {
            bestDistance = candidate;
            bestIndex = index;
        }
    }
    return bestIndex;
}

void unlockByBrineThresholds()
{
    for (int index = 0; index < kWeaponCount; ++index)
    {
        if (!kWeapons[index].newGamePlus && g_demo.brineSalt >= kWeapons[index].unlockCost)
        {
            g_demo.weaponUnlocked[index] = 1;
        }
    }
}

void collectPickups()
{
    for (int index = 0; index < kPickupCount; ++index)
    {
        if (!g_demo.pickups[index].active)
        {
            continue;
        }
        if (distance(g_demo.player.position, g_demo.pickups[index].position) > 92.0f)
        {
            continue;
        }
        g_demo.pickups[index].active = 0;
        switch (g_demo.pickups[index].kind)
        {
        case PICKUP_THROWING_KNIFE:
            g_demo.throwingKnives += 3;
            break;
        case PICKUP_FIRE_BOMB:
            g_demo.fireBombs += 1;
            break;
        case PICKUP_SEED_POD:
            g_demo.seedPods += 1;
            break;
        case PICKUP_BRINE_SALT:
            g_demo.brineSalt += 12 + g_demo.pickups[index].variant * 4;
            unlockByBrineThresholds();
            break;
        }
        wchar_t buffer[128];
        swprintf(buffer, 128, L"Collected %ls.", pickupName(g_demo.pickups[index].kind));
        setNotification(buffer);
    }
}

void useConsumable()
{
    switch (g_demo.currentConsumable)
    {
    case 0:
        if (g_demo.throwingKnives > 0)
        {
            g_demo.throwingKnives -= 1;
            int target = nearestEnemyIndex(420.0f, 1);
            if (target >= 0)
            {
                applyEnemyDamage(target, 14 + g_demo.weaponRank * 2, 0.24f);
            }
            setNotification(L"Throwing knife loosed through wet air.");
        }
        break;
    case 1:
        if (g_demo.fireBombs > 0)
        {
            g_demo.fireBombs -= 1;
            for (int index = 0; index < kTotalEnemies; ++index)
            {
                if (g_demo.enemies[index].alive && distance(g_demo.player.position, g_demo.enemies[index].position) < 260.0f)
                {
                    applyEnemyDamage(index, 18 + g_demo.weaponRank * 2, 0.30f);
                }
            }
            setNotification(L"Brine flask bursts into an ooze-punk fire bloom.");
        }
        break;
    default:
        if (g_demo.seedPods > 0)
        {
            g_demo.seedPods -= 1;
            for (int index = 0; index < kTotalEnemies; ++index)
            {
                if (g_demo.enemies[index].alive && distance(g_demo.player.position, g_demo.enemies[index].position) < 240.0f)
                {
                    g_demo.enemies[index].staggerTimer = std::max(g_demo.enemies[index].staggerTimer, 1.0f);
                }
            }
            setNotification(L"Seed pods rupture into a choking dust cloud.");
        }
        break;
    }
}

void fireProjectileWeapon()
{
    int target = g_demo.focusTargetIndex >= 0 ? g_demo.focusTargetIndex : nearestEnemyIndex(520.0f, 1);
    if (target < 0 || !g_demo.weaponUnlocked[g_demo.equippedProjectileWeapon])
    {
        return;
    }
    applyEnemyDamage(target, kWeapons[g_demo.equippedProjectileWeapon].damage + g_demo.weaponRank * 2, 0.28f);
    setNotification(L"Projectile weapon discharge tears a line through the fog.");
}

void activateNearestShelter()
{
    int shelterIndex = nearestShelterIndex(120.0f);
    if (shelterIndex < 0)
    {
        return;
    }
    g_demo.nearestShelterIndex = shelterIndex;
    g_demo.activeShelterIndex = shelterIndex;
    g_demo.shelters[shelterIndex].discovered = 1;
    g_demo.shelters[shelterIndex].activated = 1;
    g_demo.selectedShrineOption = 0;
    g_demo.mode = MODE_SHRINE;
    setNotification(L"MurkShelter pearl network opened.");
}

void restAtShelter()
{
    g_demo.player.hp = g_demo.player.maxHp;
    g_demo.player.stamina = g_demo.player.maxStamina;
    saveProgress();
    setNotification(L"Vitality restored. Pearl network memory secured.");
}

void upgradeAtShelter()
{
    if (g_demo.brineSalt < 40)
    {
        setNotification(L"Not enough brine salt to resonate with the pearl network.");
        return;
    }
    g_demo.brineSalt -= 40;
    if (g_demo.vitalityRank <= g_demo.staminaRank)
    {
        g_demo.vitalityRank += 1;
        g_demo.player.maxHp = 100 + g_demo.vitalityRank * 10;
    }
    else if (g_demo.staminaRank <= g_demo.weaponRank)
    {
        g_demo.staminaRank += 1;
        g_demo.player.maxStamina = 100.0f + g_demo.staminaRank * 10.0f;
    }
    else if (g_demo.weaponRank <= g_demo.armorRank)
    {
        g_demo.weaponRank += 1;
    }
    else
    {
        g_demo.armorRank += 1;
    }
    restAtShelter();
}

void fastTravelToNextShelter()
{
    for (int offset = 1; offset <= kShelterCount; ++offset)
    {
        int candidate = (g_demo.activeShelterIndex + offset) % kShelterCount;
        if (!g_demo.shelters[candidate].activated)
        {
            continue;
        }
        g_demo.activeShelterIndex = candidate;
        g_demo.player.position = g_demo.shelters[candidate].position;
        g_demo.player.position.y -= 40.0f;
        restAtShelter();
        setNotification(L"Pearl network fast travel completed.");
        return;
    }
    setNotification(L"No other MurkShelters are linked yet.");
}

void cycleEquipmentSelection()
{
    if (g_demo.currentViewTab != TAB_EQUIPMENT)
    {
        return;
    }
    switch (g_demo.currentViewSelection % 3)
    {
    case 0:
        for (int index = g_demo.equippedMeleeWeapon + 1; index < 16; ++index)
        {
            if (g_demo.weaponUnlocked[index])
            {
                g_demo.equippedMeleeWeapon = index;
                break;
            }
        }
        break;
    case 1:
        for (int index = g_demo.equippedProjectileWeapon + 1; index < kWeaponCount; ++index)
        {
            if (g_demo.weaponUnlocked[index])
            {
                g_demo.equippedProjectileWeapon = index;
                break;
            }
        }
        break;
    default:
        for (int index = g_demo.equippedArmorSet + 1; index < kArmorSetCount; ++index)
        {
            if (g_demo.armorUnlocked[index])
            {
                g_demo.equippedArmorSet = index;
                break;
            }
        }
        break;
    }
}

void updateTitleMenu(float deltaSeconds)
{
    int stepX = 0;
    int stepY = 0;
    updateMenuNavigation(deltaSeconds, &stepX, &stepY);
    if (stepY != 0)
    {
        g_demo.selectedTitleOption = std::clamp(g_demo.selectedTitleOption + stepY, 0, 1);
    }
    if (confirmPressed())
    {
        if (g_demo.selectedTitleOption == 0)
        {
            startOpeningSequence();
        }
        else
        {
            g_demo.showControlsCard = !g_demo.showControlsCard;
        }
    }
}

void updatePauseMenu(float deltaSeconds)
{
    int stepX = 0;
    int stepY = 0;
    updateMenuNavigation(deltaSeconds, &stepX, &stepY);
    if (stepY != 0)
    {
        g_demo.selectedPauseOption = std::clamp(g_demo.selectedPauseOption + stepY, 0, 2);
    }
    if (confirmPressed())
    {
        if (g_demo.selectedPauseOption == 0)
        {
            g_demo.mode = MODE_PLAY;
        }
        else if (g_demo.selectedPauseOption == 1)
        {
            startOpeningSequence();
        }
        else
        {
            resetToTitle();
        }
    }
    if (backPressed() || menuButtonPressed())
    {
        g_demo.mode = MODE_PLAY;
    }
}

void updateViewMenu(float deltaSeconds)
{
    int stepX = 0;
    int stepY = 0;
    updateMenuNavigation(deltaSeconds, &stepX, &stepY);
    if (stepX != 0)
    {
        int tab = (int)g_demo.currentViewTab + stepX;
        if (tab < 0)
        {
            tab = kViewTabCount - 1;
        }
        if (tab >= kViewTabCount)
        {
            tab = 0;
        }
        g_demo.currentViewTab = (ViewTab)tab;
    }
    if (stepY != 0)
    {
        if (g_demo.currentViewTab == TAB_EQUIPMENT)
        {
            g_demo.currentViewSelection = (g_demo.currentViewSelection + stepY + 3) % 3;
        }
        else
        {
            g_demo.currentViewSelection = std::max(0, g_demo.currentViewSelection + stepY);
        }
    }
    if (confirmPressed())
    {
        cycleEquipmentSelection();
    }
    if (backPressed() || viewButtonPressed())
    {
        g_demo.mode = MODE_PLAY;
    }
}

void updateShrineMenu(float deltaSeconds)
{
    int stepX = 0;
    int stepY = 0;
    updateMenuNavigation(deltaSeconds, &stepX, &stepY);
    if (stepY != 0)
    {
        g_demo.selectedShrineOption = std::clamp(g_demo.selectedShrineOption + stepY, 0, 4);
    }
    if (confirmPressed())
    {
        switch (g_demo.selectedShrineOption)
        {
        case 0:
            restAtShelter();
            break;
        case 1:
            saveProgress();
            setNotification(L"Pearl memory secured to the spirit network.");
            break;
        case 2:
            upgradeAtShelter();
            break;
        case 3:
            fastTravelToNextShelter();
            break;
        default:
            g_demo.mode = MODE_PLAY;
            break;
        }
    }
    if (backPressed() || interactPressed())
    {
        g_demo.mode = MODE_PLAY;
    }
}

void updateOpening(float deltaSeconds)
{
    g_demo.openingTimer += deltaSeconds;
    g_demo.player.animation = PLAYER_ANIM_CRAWL;
    g_demo.player.actionTime += deltaSeconds;
    g_demo.player.position.x = clampf(140.0f + g_demo.openingTimer * 160.0f, 140.0f, 420.0f);
    g_demo.player.position.y = 2680.0f - g_demo.openingTimer * 85.0f;
    g_demo.cameraYaw = 0.05f + std::sin(g_demo.openingTimer * 0.5f) * 0.03f;
    if (g_demo.openingTimer >= 4.8f || confirmPressed() || backPressed())
    {
        g_demo.mode = MODE_PLAY;
        setNotification(L"Humidity feeds your healing. Hold LT to focus. Reach the drowned temple.");
    }
}

void updatePlayer(float deltaSeconds)
{
    float leftX = g_demo.controller.connected ? g_demo.controller.lx : 0.0f;
    float leftY = g_demo.controller.connected ? g_demo.controller.ly : 0.0f;
    float rightX = g_demo.controller.connected ? g_demo.controller.rx : 0.0f;
    float rightY = g_demo.controller.connected ? g_demo.controller.ry : 0.0f;
    Vec2 moveInput = {leftX, leftY};
    int keyboardUsed = 0;

    if (keyboardDown('W'))
    {
        moveInput.y -= 1.0f;
        keyboardUsed = 1;
    }
    if (keyboardDown('S'))
    {
        moveInput.y += 1.0f;
        keyboardUsed = 1;
    }
    if (keyboardDown('A'))
    {
        moveInput.x -= 1.0f;
        keyboardUsed = 1;
    }
    if (keyboardDown('D'))
    {
        moveInput.x += 1.0f;
        keyboardUsed = 1;
    }
    if (keyboardUsed)
    {
        moveInput = normalize(moveInput);
    }

    int jump = keyboardPressed(VK_SPACE) || controllerButtonPressed(XINPUT_GAMEPAD_A);
    int lightAttack = keyboardPressed('J') || controllerButtonPressed(XINPUT_GAMEPAD_X);
    int heavyAttack = keyboardPressed('K') || controllerButtonPressed(XINPUT_GAMEPAD_Y);
    int blockHeld = keyboardDown('Q') || (g_demo.controller.connected && (g_demo.controller.buttons & XINPUT_GAMEPAD_LEFT_SHOULDER));
    int focusHeld = keyboardDown('F') || (g_demo.controller.connected && g_demo.controller.lt > 0.35f);
    int runHeldKeyboard = keyboardDown(VK_SHIFT);
    int runHeldController = g_demo.controller.connected && g_demo.controllerBHold > 0.22f;
    int runHeld = runHeldKeyboard || runHeldController;
    int crouchHeldKeyboard = keyboardDown('C');
    int crouchHeldController = g_demo.controller.connected && g_demo.controllerRTHold > 0.22f;
    int crouchHeld = crouchHeldKeyboard || crouchHeldController;
    int parryTapKeyboard = keyboardPressed('E');

    updateFocusTarget(focusHeld);

    if (g_demo.controller.connected && (g_demo.controller.buttons & XINPUT_GAMEPAD_B))
    {
        g_demo.controllerBHold += deltaSeconds;
    }
    else
    {
        if (controllerButtonReleased(XINPUT_GAMEPAD_B) && g_demo.controllerBHold > 0.02f && g_demo.controllerBHold < 0.22f)
        {
            startDodge(moveInput);
        }
        g_demo.controllerBHold = 0.0f;
    }

    if (g_demo.controller.connected && g_demo.controller.rt > 0.35f)
    {
        g_demo.controllerRTHold += deltaSeconds;
    }
    else
    {
        if (g_demo.controllerRTHold > 0.02f && g_demo.controllerRTHold < 0.20f)
        {
            startParry();
        }
        g_demo.controllerRTHold = 0.0f;
    }

    if (parryTapKeyboard)
    {
        startParry();
    }

    if (keyboardPressed('X'))
    {
        startDodge(moveInput);
    }

    if (lightAttack)
    {
        handlePlayerAttack(0);
    }
    if (heavyAttack)
    {
        handlePlayerAttack(1);
    }
    if (jump)
    {
        beginJump();
    }

    g_demo.cameraYaw += rightX * deltaSeconds * 1.8f;
    g_demo.cameraPitch = clampf(g_demo.cameraPitch + rightY * deltaSeconds * 0.9f, -0.22f, 0.30f);

    if (focusHeld && g_demo.focusTargetIndex >= 0)
    {
        Vec2 toTarget = sub(g_demo.enemies[g_demo.focusTargetIndex].position, g_demo.player.position);
        g_demo.player.facing = normalize(toTarget);
        float desiredYaw = std::atan2(-toTarget.y, toTarget.x) * 0.18f;
        g_demo.cameraYaw = g_demo.cameraYaw + (desiredYaw - g_demo.cameraYaw) * clampf(deltaSeconds * 3.0f, 0.0f, 1.0f);
    }

    Vec2 wanted = normalize(moveInput);
    if (length(wanted) > 0.01f)
    {
        g_demo.player.facing = wanted;
    }

    float speed = runHeld ? 210.0f : 132.0f;
    if (focusHeld)
    {
        speed *= 0.75f;
    }
    if (crouchHeld)
    {
        speed *= runHeld ? 1.18f : 0.52f;
        g_demo.player.slideTimer = runHeld ? 0.24f : g_demo.player.slideTimer;
    }

    if (g_demo.player.dodgeTimer > 0.0f)
    {
        g_demo.player.dodgeTimer = std::max(0.0f, g_demo.player.dodgeTimer - deltaSeconds);
        g_demo.player.velocity = scale(g_demo.player.velocity, 0.92f);
    }
    else
    {
        g_demo.player.velocity = scale(wanted, speed);
    }

    g_demo.player.position = add(g_demo.player.position, scale(g_demo.player.velocity, deltaSeconds));
    g_demo.player.position.x = clampf(g_demo.player.position.x, 80.0f, kWorldMetersX - 80.0f);
    g_demo.player.position.y = clampf(g_demo.player.position.y, 520.0f, kWorldMetersY - 60.0f);
    resolveEnvironmentCollisions();
    g_demo.player.position.x = clampf(g_demo.player.position.x, 80.0f, kWorldMetersX - 80.0f);
    g_demo.player.position.y = clampf(g_demo.player.position.y, 520.0f, kWorldMetersY - 60.0f);

    if (g_demo.player.hopVelocity > 0.0f || g_demo.player.hopHeight > 0.0f)
    {
        g_demo.player.hopVelocity -= 960.0f * deltaSeconds;
        g_demo.player.hopHeight += g_demo.player.hopVelocity * deltaSeconds;
        if (g_demo.player.hopHeight < 0.0f)
        {
            g_demo.player.hopHeight = 0.0f;
            g_demo.player.hopVelocity = 0.0f;
            g_demo.player.airActions = 2;
        }
    }

    g_demo.player.moisture = moistureAtPosition(g_demo.player.position);
    g_demo.player.breathingSync = breathingResonance();

    if (length(wanted) < 0.05f)
    {
        g_demo.player.idleTimer += deltaSeconds;
    }
    else
    {
        g_demo.player.idleTimer = 0.0f;
    }

    if (g_demo.player.idleTimer > 1.2f)
    {
        g_demo.player.healAccumulator += deltaSeconds * g_demo.player.moisture * g_demo.player.breathingSync * 5.5f;
        if (g_demo.player.healAccumulator >= 1.0f)
        {
            int heal = (int)g_demo.player.healAccumulator;
            g_demo.player.hp = std::min(g_demo.player.maxHp, g_demo.player.hp + heal);
            g_demo.player.healAccumulator -= heal;
        }
    }
    else
    {
        g_demo.player.healAccumulator = 0.0f;
    }

    g_demo.player.stamina = std::min(g_demo.player.maxStamina, g_demo.player.stamina + deltaSeconds * (runHeld ? 10.0f : 18.0f));
    g_demo.player.attackCooldown = std::max(0.0f, g_demo.player.attackCooldown - deltaSeconds);
    g_demo.player.parryTimer = std::max(0.0f, g_demo.player.parryTimer - deltaSeconds);
    g_demo.player.blockTimer = blockHeld ? 0.12f : std::max(0.0f, g_demo.player.blockTimer - deltaSeconds);
    g_demo.player.slideTimer = std::max(0.0f, g_demo.player.slideTimer - deltaSeconds);
    g_demo.player.hurtFlash = std::max(0.0f, g_demo.player.hurtFlash - deltaSeconds);
    g_demo.player.actionTime += deltaSeconds;

    if (g_demo.player.hurtFlash > 0.0f)
    {
        g_demo.player.animation = PLAYER_ANIM_HURT;
    }
    else if (g_demo.mode == MODE_VICTORY)
    {
        g_demo.player.animation = PLAYER_ANIM_VICTORY;
    }
    else if (g_demo.player.dodgeTimer > 0.0f)
    {
        g_demo.player.animation = PLAYER_ANIM_DODGE;
    }
    else if (g_demo.player.parryTimer > 0.0f)
    {
        g_demo.player.animation = PLAYER_ANIM_PARRY;
    }
    else if (blockHeld)
    {
        g_demo.player.animation = PLAYER_ANIM_BLOCK;
    }
    else if (g_demo.player.attackCooldown > 0.32f)
    {
        g_demo.player.animation = PLAYER_ANIM_HEAVY;
    }
    else if (g_demo.player.attackCooldown > 0.0f)
    {
        g_demo.player.animation = PLAYER_ANIM_LIGHT;
    }
    else if (g_demo.player.hopHeight > 0.0f)
    {
        g_demo.player.animation = PLAYER_ANIM_JUMP;
    }
    else if (crouchHeld)
    {
        g_demo.player.animation = runHeld ? PLAYER_ANIM_SLIDE : PLAYER_ANIM_CROUCH;
    }
    else if (focusHeld)
    {
        g_demo.player.animation = PLAYER_ANIM_FOCUS;
    }
    else if (length(wanted) > 0.1f)
    {
        g_demo.player.animation = runHeld ? PLAYER_ANIM_RUN : PLAYER_ANIM_WALK;
    }
    else if (g_demo.player.idleTimer > 1.2f && g_demo.player.hp < g_demo.player.maxHp)
    {
        g_demo.player.animation = PLAYER_ANIM_HEAL;
    }
    else
    {
        g_demo.player.animation = PLAYER_ANIM_IDLE;
    }
}

void updateEnemies(float deltaSeconds)
{
    for (int index = 0; index < kTotalEnemies; ++index)
    {
        Enemy &enemy = g_demo.enemies[index];
        if (!enemy.alive)
        {
            continue;
        }

        enemy.discovered = 1;
        enemy.animationTime += deltaSeconds;
        enemy.attackCooldown = std::max(0.0f, enemy.attackCooldown - deltaSeconds);
        enemy.staggerTimer = std::max(0.0f, enemy.staggerTimer - deltaSeconds);
        enemy.specialTimer = std::max(0.0f, enemy.specialTimer - deltaSeconds);
        if (enemy.staggerTimer > 0.0f)
        {
            continue;
        }

        Vec2 toPlayer = sub(g_demo.player.position, enemy.position);
        float playerDistance = length(toPlayer);
        Vec2 direction = normalize(toPlayer);
        Vec2 movement = {0.0f, 0.0f};
        float attackRange = enemy.boss ? 160.0f : 120.0f;
        int damage = enemy.boss ? 13 : 7;
        float cooldown = enemy.boss ? 1.6f : 1.1f;

        switch (enemy.kind)
        {
        case ENEMY_DEEP_ONE:
            movement = scale(direction, playerDistance > 340.0f ? 18.0f : 66.0f);
            damage = 8;
            break;
        case ENEMY_SHOGGOTH_SPAWN:
            movement = scale(direction, playerDistance > 260.0f ? 20.0f : 44.0f);
            damage = 11;
            attackRange = 146.0f;
            cooldown = 1.8f;
            break;
        case ENEMY_NIGHTGAUNT:
            movement = scale(direction, playerDistance > 320.0f ? 24.0f : 72.0f);
            if (playerDistance > 180.0f && playerDistance < 340.0f && enemy.specialTimer <= 0.0f)
            {
                movement = scale(direction, 220.0f);
                enemy.specialTimer = 2.1f;
            }
            damage = 9;
            attackRange = 132.0f;
            break;
        case ENEMY_MI_GO:
            movement = {direction.y * 64.0f, -direction.x * 64.0f};
            if (playerDistance > 260.0f)
            {
                movement = add(movement, scale(direction, 34.0f));
            }
            damage = 8;
            cooldown = 1.0f;
            break;
        case ENEMY_GHOUL:
            movement = scale(direction, playerDistance > 280.0f ? 20.0f : 76.0f);
            damage = 9;
            break;
        case ENEMY_CULTIST:
            movement = playerDistance < 160.0f ? scale(direction, -48.0f) : scale(direction, 34.0f);
            damage = 7;
            attackRange = 300.0f;
            cooldown = 1.35f;
            break;
        case ENEMY_STAR_SPAWN:
            movement = scale(direction, playerDistance > 300.0f ? 22.0f : 50.0f);
            damage = 12;
            attackRange = 152.0f;
            cooldown = 1.9f;
            break;
        case ENEMY_DROWNED_PILGRIM:
            movement = scale(direction, playerDistance > 280.0f ? 16.0f : 54.0f);
            if (enemy.specialTimer <= 0.0f)
            {
                enemy.hp = std::min(enemy.maxHp, enemy.hp + 1);
                enemy.specialTimer = 1.2f;
            }
            damage = 8;
            cooldown = 1.25f;
            break;
        case ENEMY_REPTILIAN_DEITY:
            movement = scale(direction, playerDistance > 260.0f ? 68.0f : 44.0f);
            if (playerDistance > 220.0f && enemy.specialTimer <= 0.0f)
            {
                movement = scale(direction, 240.0f);
                enemy.specialTimer = 2.8f;
            }
            damage = 15;
            attackRange = 172.0f;
            cooldown = 1.55f;
            break;
        case ENEMY_JAGUAR_DEITY:
            movement = {direction.y * 94.0f, -direction.x * 94.0f};
            if (playerDistance > 220.0f)
            {
                movement = add(movement, scale(direction, 58.0f));
            }
            if (enemy.specialTimer <= 0.0f && playerDistance > 140.0f)
            {
                movement = add(movement, scale(direction, 180.0f));
                enemy.specialTimer = 2.2f;
            }
            damage = 14;
            attackRange = 164.0f;
            cooldown = 1.3f;
            break;
        }

        enemy.velocity = movement;
        enemy.position = add(enemy.position, scale(enemy.velocity, deltaSeconds));

        if (enemy.kind == ENEMY_CULTIST && playerDistance < attackRange && playerDistance > 160.0f && enemy.attackCooldown <= 0.0f)
        {
            int resolvedDamage = resolveIncomingAttack(index, damage);
            applyPlayerHit(resolvedDamage, 0.14f);
            enemy.attackCooldown = cooldown;
            setNotification(L"A harpoon prayer cuts through the rain line.");
        }
        else if (playerDistance < attackRange && enemy.attackCooldown <= 0.0f)
        {
            int resolvedDamage = resolveIncomingAttack(index, damage);
            applyPlayerHit(resolvedDamage, enemy.boss ? 0.22f : 0.14f);
            enemy.attackCooldown = cooldown;
        }
    }
}

void updatePlay(float deltaSeconds)
{
    if (menuButtonPressed())
    {
        g_demo.mode = MODE_PAUSE;
        g_demo.selectedPauseOption = 0;
        return;
    }
    if (viewButtonPressed())
    {
        g_demo.mode = MODE_VIEW_MENU;
        return;
    }

    if (interactPressed())
    {
        activateNearestShelter();
        if (g_demo.mode == MODE_SHRINE)
        {
            return;
        }
    }

    if (cycleConsumablePressed())
    {
        g_demo.currentConsumable = (g_demo.currentConsumable + 1) % 3;
    }

    if (useConsumablePressed())
    {
        useConsumable();
    }

    if (fireProjectilePressed())
    {
        fireProjectileWeapon();
    }

    updatePlayer(deltaSeconds);
    updateEnemies(deltaSeconds);
    collectPickups();
    spawnBossesIfReady();

    if (g_demo.basicEnemiesRemaining == 0 && !g_demo.bossesSpawned)
    {
        g_demo.activeQuestStage = 1;
    }
    else if (g_demo.bossesSpawned && !g_demo.victoryUnlocked)
    {
        g_demo.activeQuestStage = 2;
    }
    else if (g_demo.victoryUnlocked)
    {
        g_demo.activeQuestStage = 3;
    }
}

void updateMode(float deltaSeconds)
{
    g_demo.worldTime += deltaSeconds;
    pollController();
    g_demo.notificationTimer = std::max(0.0f, g_demo.notificationTimer - deltaSeconds);
    g_demo.cameraShake = std::max(0.0f, g_demo.cameraShake - deltaSeconds * 1.5f);
    if (g_demo.focusTargetIndex >= 0 && !g_demo.enemies[g_demo.focusTargetIndex].alive)
    {
        g_demo.focusTargetIndex = -1;
    }

    switch (g_demo.mode)
    {
    case MODE_TITLE:
        updateTitleMenu(deltaSeconds);
        break;
    case MODE_OPENING:
        updateOpening(deltaSeconds);
        break;
    case MODE_PLAY:
        updatePlay(deltaSeconds);
        break;
    case MODE_PAUSE:
        updatePauseMenu(deltaSeconds);
        break;
    case MODE_VIEW_MENU:
        updateViewMenu(deltaSeconds);
        break;
    case MODE_SHRINE:
        updateShrineMenu(deltaSeconds);
        break;
    case MODE_GAME_OVER:
        if (confirmPressed())
        {
            startOpeningSequence();
        }
        else if (backPressed())
        {
            resetToTitle();
        }
        break;
    case MODE_VICTORY:
        if (confirmPressed() || backPressed())
        {
            resetToTitle();
        }
        break;
    }

    clearTransientKeyboard();
}

void drawBackground(Graphics &graphics, HDC hdc, RECT clientRect)
{
    int width = clientRect.right - clientRect.left;
    int height = clientRect.bottom - clientRect.top;
    for (int band = 0; band < 14; ++band)
    {
        int top = (height * band) / 14;
        int bottom = (height * (band + 1)) / 14;
        int r = 10 + band * 3;
        int g = 16 + band * 4;
        int b = 22 + band * 3;
        fillRect(hdc, 0, top, width, bottom, RGB(r, g, b));
    }
    drawImageAlpha(graphics, g_demo.assets.worldKeyart, 0.0f, 0.0f, (float)width, (float)height, 0.32f);

    int horizon = (int)(height * (0.38f + g_demo.cameraPitch * 0.08f));
    for (int line = 0; line < 22; ++line)
    {
        float t = (float)line / 21.0f;
        int y = horizon + (int)(t * (height - horizon - 20));
        int inset = (int)((1.0f - t) * width * 0.36f);
        fillRect(hdc, inset, y, width - inset, y + 2, RGB(24 + line * 3, 44 + line * 2, 38 + line));
    }

    fillRect(hdc, 0, height - 90, width, height, RGB(8, 14, 18));
}

void drawEnvironmentInstance(Graphics &graphics, HDC hdc, RECT clientRect, int index, int foregroundPass)
{
    const EnvironmentObject &object = g_demo.environment[index];
    int drawForeground = environmentOccludesPlayer(object);
    if (foregroundPass != drawForeground)
    {
        return;
    }

    float scaleValue = 1.0f;
    Vec2 screen = worldToScreen(object.position, clientRect.right, clientRect.bottom, &scaleValue);
    float drawScale = scaleValue * object.scale;
    float width = 92.0f * drawScale;
    float height = 116.0f * drawScale;
    EnvironmentRenderProfile profile = environmentRenderProfile(object);

    SolidBrush shadowBrush(Color(foregroundPass ? 76 : 58, 8, 10, 12));
    graphics.FillEllipse(&shadowBrush, screen.x - profile.shadowWidth * drawScale * 0.5f, screen.y - profile.shadowDepth * drawScale * 0.20f,
                         profile.shadowWidth * drawScale, profile.shadowDepth * drawScale);

    if (!foregroundPass)
    {
        float topLift = (10.0f + profile.topLift * 0.12f) * drawScale;
        float shear = g_demo.cameraYaw * 40.0f * drawScale;
        PointF cap[4] = {
            PointF(screen.x - width * 0.21f + shear * 0.40f, screen.y - height * 0.76f - topLift),
            PointF(screen.x + width * 0.21f + shear * 0.56f, screen.y - height * 0.76f - topLift),
            PointF(screen.x + width * 0.16f + shear * 0.14f, screen.y - height * 0.59f),
            PointF(screen.x - width * 0.16f - shear * 0.14f, screen.y - height * 0.59f)};
        SolidBrush capBrush(Color(56, 112, 128, 142));
        Pen capPen(Color(72, 176, 194, 202), 1.6f);
        graphics.FillPolygon(&capBrush, cap, 4);
        graphics.DrawPolygon(&capPen, cap, 4);
    }

    drawImageFrame(graphics, g_demo.assets.environmentPropsSheet, object.type, kPropSheetColumns, 4, screen.x - width * 0.5f, screen.y - height, width, height, foregroundPass ? 0.98f : 0.92f);
    fillRect(hdc, (int)(screen.x - profile.shadowWidth * drawScale * 0.36f), (int)(screen.y - 2.0f), (int)(screen.x + profile.shadowWidth * drawScale * 0.36f), (int)(screen.y + 3.0f), RGB(8, 10, 12));
}

void drawEnvironment(Graphics &graphics, HDC hdc, RECT clientRect)
{
    for (int index = 0; index < kEnvironmentObjectCount; ++index)
    {
        drawEnvironmentInstance(graphics, hdc, clientRect, index, 0);
    }
}

void drawEnvironmentForeground(Graphics &graphics, HDC hdc, RECT clientRect)
{
    for (int index = 0; index < kEnvironmentObjectCount; ++index)
    {
        drawEnvironmentInstance(graphics, hdc, clientRect, index, 1);
    }
}

void drawPickups(Graphics &graphics, HDC hdc, RECT clientRect)
{
    for (int index = 0; index < kPickupCount; ++index)
    {
        if (!g_demo.pickups[index].active)
        {
            continue;
        }
        float scaleValue = 1.0f;
        Vec2 screen = worldToScreen(g_demo.pickups[index].position, clientRect.right, clientRect.bottom, &scaleValue);
        int radius = (int)(8.0f + scaleValue * 8.0f + g_demo.pickups[index].variant * 2.0f);
        COLORREF color = RGB(202, 214, 220);
        if (g_demo.pickups[index].kind == PICKUP_FIRE_BOMB)
        {
            color = RGB(214, 118, 82);
        }
        else if (g_demo.pickups[index].kind == PICKUP_SEED_POD)
        {
            color = RGB(124, 168, 102);
        }
        else if (g_demo.pickups[index].kind == PICKUP_BRINE_SALT)
        {
            color = RGB(188, 206, 132);
        }
        HBRUSH brush = CreateSolidBrush(color);
        HGDIOBJ oldBrush = SelectObject(hdc, brush);
        Ellipse(hdc, (int)screen.x - radius, (int)screen.y - radius, (int)screen.x + radius, (int)screen.y + radius);
        SelectObject(hdc, oldBrush);
        DeleteObject(brush);
    }
}

void drawMurkShelters(Graphics &graphics, HDC hdc, RECT clientRect)
{
    for (int index = 0; index < kShelterCount; ++index)
    {
        float scaleValue = 1.0f;
        Vec2 screen = worldToScreen(g_demo.shelters[index].position, clientRect.right, clientRect.bottom, &scaleValue);
        int width = (int)(50.0f * scaleValue);
        int height = (int)(42.0f * scaleValue);
        fillRect(hdc, (int)screen.x - width / 2, (int)screen.y - height, (int)screen.x + width / 2, (int)screen.y, RGB(56, 44, 34));
        POINT roof[3] = {{(LONG)screen.x - width / 2, (LONG)screen.y - height}, {(LONG)screen.x, (LONG)screen.y - height - height / 2}, {(LONG)screen.x + width / 2, (LONG)screen.y - height}};
        HBRUSH roofBrush = CreateSolidBrush(RGB(72, 58, 45));
        HGDIOBJ oldBrush = SelectObject(hdc, roofBrush);
        Polygon(hdc, roof, 3);
        SelectObject(hdc, oldBrush);
        DeleteObject(roofBrush);
        int pearlRadius = (int)(6.0f + std::sin(g_demo.worldTime * 2.0f + index) * 2.0f);
        HBRUSH pearlBrush = CreateSolidBrush(g_demo.shelters[index].activated ? RGB(180, 224, 210) : RGB(118, 138, 138));
        oldBrush = SelectObject(hdc, pearlBrush);
        Ellipse(hdc, (int)screen.x - pearlRadius, (int)screen.y - height - pearlRadius, (int)screen.x + pearlRadius, (int)screen.y - height + pearlRadius);
        SelectObject(hdc, oldBrush);
        DeleteObject(pearlBrush);
        if (distance(g_demo.player.position, g_demo.shelters[index].position) < 130.0f)
        {
            drawTextLine(hdc, (int)screen.x - 42, (int)screen.y - height - 30, RGB(228, 235, 238), L"MurkShelter");
        }
    }
}

void drawVolumetricLighting(Graphics &graphics, RECT clientRect)
{
    SolidBrush fogBrush(Color(56, 14, 18, 22));
    graphics.FillRectangle(&fogBrush, 0, 0, clientRect.right, clientRect.bottom);

    float playerScale = 1.0f;
    Vec2 playerLight = worldToScreen(g_demo.player.position, clientRect.right, clientRect.bottom, &playerScale);
    int playerRadius = (int)(170.0f + g_demo.player.moisture * 110.0f);
    SolidBrush playerGlow(Color(70, 116, 174, 168));
    graphics.FillEllipse(&playerGlow, playerLight.x - playerRadius * 0.5f, playerLight.y - playerRadius * 0.7f, (REAL)playerRadius, (REAL)playerRadius);

    for (int index = 0; index < kShelterCount; ++index)
    {
        if (!g_demo.shelters[index].activated)
        {
            continue;
        }
        float scaleValue = 1.0f;
        Vec2 light = worldToScreen(g_demo.shelters[index].position, clientRect.right, clientRect.bottom, &scaleValue);
        int radius = (int)(100.0f + scaleValue * 60.0f);
        SolidBrush shrineGlow(Color(64, 186, 210, 194));
        graphics.FillEllipse(&shrineGlow, light.x - radius * 0.5f, light.y - radius, (REAL)radius, (REAL)radius);
        Pen shaftPen(Color(42, 164, 202, 186), 2.0f);
        graphics.DrawLine(&shaftPen, light.x, light.y - radius * 0.5f, light.x + radius * 0.3f, light.y - radius * 1.4f);
        graphics.DrawLine(&shaftPen, light.x, light.y - radius * 0.5f, light.x - radius * 0.3f, light.y - radius * 1.4f);
    }

    for (int index = 0; index < kTotalEnemies; ++index)
    {
        if (!g_demo.enemies[index].alive || !g_demo.enemies[index].boss)
        {
            continue;
        }
        float scaleValue = 1.0f;
        Vec2 light = worldToScreen(g_demo.enemies[index].position, clientRect.right, clientRect.bottom, &scaleValue);
        int radius = (int)(120.0f + scaleValue * 70.0f);
        SolidBrush bossGlow(Color(48, 210, 72, 62));
        graphics.FillEllipse(&bossGlow, light.x - radius * 0.55f, light.y - radius * 0.9f, (REAL)(radius * 1.1f), (REAL)radius);
    }
}

void drawEnemies(Graphics &graphics, HDC hdc, RECT clientRect)
{
    for (int index = 0; index < kTotalEnemies; ++index)
    {
        Enemy &enemy = g_demo.enemies[index];
        if (!enemy.alive)
        {
            continue;
        }
        float scaleValue = 1.0f;
        Vec2 screen = worldToScreen(enemy.position, clientRect.right, clientRect.bottom, &scaleValue);
        int frame = (int)(enemy.animationTime * (enemy.boss ? 9.0f : 7.5f)) % enemy.animationFrameCount;
        float width = enemy.boss ? 132.0f * scaleValue : 94.0f * scaleValue;
        float height = enemy.boss ? 164.0f * scaleValue : 116.0f * scaleValue;
        if (index == g_demo.focusTargetIndex)
        {
            int ringRadius = (int)(26.0f + std::sin(g_demo.focusPulse * 7.0f) * 4.0f + width * 0.12f);
            HPEN pen = CreatePen(PS_SOLID, 2, RGB(118, 196, 176));
            HGDIOBJ oldPen = SelectObject(hdc, pen);
            HGDIOBJ oldBrush = SelectObject(hdc, GetStockObject(HOLLOW_BRUSH));
            Ellipse(hdc, (int)screen.x - ringRadius, (int)screen.y - ringRadius, (int)screen.x + ringRadius, (int)screen.y + ringRadius);
            SelectObject(hdc, oldBrush);
            SelectObject(hdc, oldPen);
            DeleteObject(pen);
        }
        fillRect(hdc, (int)(screen.x - width * 0.28f), (int)(screen.y - 3.0f), (int)(screen.x + width * 0.28f), (int)(screen.y + 3.0f), RGB(8, 10, 12));
        drawImageFrame(graphics, enemy.boss ? g_demo.assets.bossAnimSheet : g_demo.assets.basicEnemyAnimSheet, frame, enemy.boss ? kBossAnimColumns : kBasicAnimColumns, enemy.boss ? kBossAnimRows : kBasicAnimRows, screen.x - width * 0.5f, screen.y - height, width, height, 0.96f);
        wchar_t buffer[64];
        swprintf(buffer, 64, L"%ls %d/%d", enemyName(enemy.kind), enemy.hp, enemy.maxHp);
        drawTextLine(hdc, (int)(screen.x - width * 0.5f), (int)(screen.y - height - 18.0f), RGB(238, 242, 245), buffer);
    }
}

void drawPlayer(Graphics &graphics, HDC hdc, RECT clientRect)
{
    float scaleValue = 1.0f;
    Vec2 screen = worldToScreen(g_demo.player.position, clientRect.right, clientRect.bottom, &scaleValue);
    float width = 128.0f * scaleValue;
    float height = 154.0f * scaleValue + g_demo.player.hopHeight * 0.03f;
    int frame = (int)g_demo.player.animation;
    fillRect(hdc, (int)(screen.x - 34.0f * scaleValue), (int)(screen.y - 3.0f), (int)(screen.x + 34.0f * scaleValue), (int)(screen.y + 3.0f), RGB(6, 8, 10));
    drawPlayerPresentation(graphics, screen.x - width * 0.5f, screen.y - height - g_demo.player.hopHeight * 0.07f, width, height, frame, 0.98f);
    drawTextLine(hdc, (int)(screen.x - 56.0f), (int)(screen.y - height - 18.0f), RGB(244, 247, 249), L"Fish-Man Wanderer");
}

const wchar_t *currentObjective()
{
    switch (g_demo.activeQuestStage)
    {
    case 0:
        return L"Purge the lesser horrors and recover four temple seals from the inland carriers.";
    case 1:
        return L"With four seals secured, reach the drowned temple in the northern basalt canopy.";
    case 2:
        return L"Defeat the reptilian abyss prince and jaguar eclipse tyrant.";
    default:
        return L"InnsmouthIsland end-state reached.";
    }
}

const wchar_t *viewTabName(ViewTab tab)
{
    switch (tab)
    {
    case TAB_CHARACTER:
        return L"Character";
    case TAB_INVENTORY:
        return L"Inventory";
    case TAB_EQUIPMENT:
        return L"Equipment";
    case TAB_MAP:
        return L"Map";
    case TAB_QUESTLOG:
        return L"Questlog";
    default:
        return L"Codex";
    }
}

void drawGauge(HDC hdc, int x, int y, int width, int height, float ratio, COLORREF fill, const wchar_t *label)
{
    RECT rect = {x, y, x + width, y + height};
    FrameRect(hdc, &rect, (HBRUSH)GetStockObject(WHITE_BRUSH));
    fillRect(hdc, x + 2, y + 2, x + 2 + (int)((width - 4) * clampf(ratio, 0.0f, 1.0f)), y + height - 2, fill);
    drawTextLine(hdc, x, y - 16, RGB(230, 235, 240), label);
}

void drawHud(Graphics &graphics, HDC hdc, RECT clientRect)
{
    wchar_t buffer[160];
    fillRect(hdc, 20, clientRect.bottom - 156, 460, clientRect.bottom - 52, RGB(10, 14, 20));
    drawImageAlpha(graphics, g_demo.assets.hudSheet, 22.0f, (float)(clientRect.bottom - 154), 432.0f, 94.0f, 0.18f);
    drawGauge(hdc, 34, clientRect.bottom - 124, 220, 18, (float)g_demo.player.hp / (float)g_demo.player.maxHp, RGB(150, 52, 58), L"Health");
    drawGauge(hdc, 34, clientRect.bottom - 88, 220, 18, g_demo.player.stamina / g_demo.player.maxStamina, RGB(64, 144, 104), L"Stamina");
    drawGauge(hdc, 270, clientRect.bottom - 124, 156, 18, g_demo.player.moisture, RGB(70, 112, 178), L"Moisture");
    drawGauge(hdc, 270, clientRect.bottom - 88, 156, 18, g_demo.player.breathingSync, RGB(128, 182, 162), L"Breathing Sync");
    swprintf(buffer, 160, L"Map Area 12 sq km  |  Horrors Remaining %d  |  Temple Seals %d/4", g_demo.basicEnemiesRemaining, g_demo.templeSeals);
    drawTextLine(hdc, 34, clientRect.bottom - 58, RGB(212, 220, 226), buffer);
    if (g_demo.focusTargetIndex >= 0 && g_demo.enemies[g_demo.focusTargetIndex].alive)
    {
        swprintf(buffer, 160, L"Focus Lock: %ls", enemyName(g_demo.enemies[g_demo.focusTargetIndex].kind));
        drawTextLine(hdc, 34, clientRect.bottom - 38, RGB(160, 214, 201), buffer);
    }
    swprintf(buffer, 160, L"Brine %d  |  %ls ready", g_demo.brineSalt, currentConsumableName());
    drawTextLine(hdc, 34, clientRect.bottom - 18, RGB(206, 214, 221), buffer);

    fillRect(hdc, clientRect.right - 328, 20, clientRect.right - 22, 130, RGB(10, 14, 20));
    drawTextLine(hdc, clientRect.right - 304, 34, RGB(244, 247, 250), L"Objective");
    RECT objectiveRect = {clientRect.right - 304, 56, clientRect.right - 36, 116};
    drawParagraph(hdc, objectiveRect, RGB(214, 220, 226), currentObjective());
}

void drawNotification(HDC hdc, RECT clientRect)
{
    if (g_demo.notificationTimer <= 0.0f || g_demo.notification[0] == 0)
    {
        return;
    }
    RECT panel = {clientRect.left + 420, clientRect.bottom - 124, clientRect.right - 360, clientRect.bottom - 72};
    fillRect(hdc, panel.left, panel.top, panel.right, panel.bottom, RGB(12, 16, 24));
    FrameRect(hdc, &panel, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, panel.left + 16, panel.top + 16, RGB(236, 241, 244), g_demo.notification);
}

void drawTitle(Graphics &graphics, HDC hdc, RECT clientRect)
{
    fillRect(hdc, 0, 0, clientRect.right, clientRect.bottom, RGB(6, 8, 12));
    drawImageAlpha(graphics, g_demo.assets.worldKeyart, 0.0f, 0.0f, (float)clientRect.right, (float)clientRect.bottom, 0.45f);
    drawTextLine(hdc, 88, 74, RGB(248, 250, 252), L"InnsmouthIsland Research Integrated");
    drawTextLine(hdc, 88, 106, RGB(198, 206, 214), L"Benchmark-informed ooze-punk action research branch.");
    drawImageAlpha(graphics, g_demo.assets.openingStoryboard, (float)(clientRect.right - 690), 78.0f, 612.0f, 350.0f, 0.85f);

    RECT menu = {88, 170, 470, 330};
    drawImageAlpha(graphics, g_demo.assets.uiMenuPanel, (float)menu.left, (float)menu.top, (float)(menu.right - menu.left), (float)(menu.bottom - menu.top), 0.20f);
    FrameRect(hdc, &menu, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, menu.left + 24, menu.top + 26, RGB(238, 242, 245), g_demo.selectedTitleOption == 0 ? L"> Begin Shore Crawl" : L"  Begin Shore Crawl");
    drawTextLine(hdc, menu.left + 24, menu.top + 60, RGB(238, 242, 245), g_demo.selectedTitleOption == 1 ? L"> Toggle Controls Card" : L"  Toggle Controls Card");
    drawTextLine(hdc, menu.left + 24, menu.top + 110, RGB(198, 206, 214), L"Menu navigation: Left Stick or Arrow keys");
    drawTextLine(hdc, menu.left + 24, menu.top + 136, RGB(198, 206, 214), L"A confirm, B back. Start opens pause in-game, View opens codex stack.");
    drawTextLine(hdc, menu.left + 24, menu.top + 162, RGB(160, 196, 204), L"Benchmarked against OpenGameArt breadth, Kenney modularity, LPC style discipline.");
}

void drawOpening(Graphics &graphics, HDC hdc, RECT clientRect)
{
    drawImageAlpha(graphics, g_demo.assets.openingStoryboard, 0.0f, 0.0f, (float)clientRect.right, (float)clientRect.bottom, 0.76f);
    drawTextLine(hdc, 76, 66, RGB(244, 247, 250), L"InnsmouthIsland Research Opening");
    drawTextLine(hdc, 76, 92, RGB(206, 214, 221), L"The sea spits a fish-man onto a rainforest-black New England shore.");
    drawPlayer(graphics, hdc, clientRect);
}

void drawPauseMenu(HDC hdc, RECT clientRect)
{
    RECT menu = {clientRect.left + 460, clientRect.top + 180, clientRect.right - 460, clientRect.bottom - 180};
    fillRect(hdc, menu.left, menu.top, menu.right, menu.bottom, RGB(10, 14, 20));
    FrameRect(hdc, &menu, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, menu.left + 28, menu.top + 28, RGB(246, 248, 250), L"In-Game Menu");
    drawTextLine(hdc, menu.left + 28, menu.top + 80, RGB(232, 236, 240), g_demo.selectedPauseOption == 0 ? L"> Resume" : L"  Resume");
    drawTextLine(hdc, menu.left + 28, menu.top + 112, RGB(232, 236, 240), g_demo.selectedPauseOption == 1 ? L"> Restart Shore Crawl" : L"  Restart Shore Crawl");
    drawTextLine(hdc, menu.left + 28, menu.top + 144, RGB(232, 236, 240), g_demo.selectedPauseOption == 2 ? L"> Return To Title" : L"  Return To Title");
}

void drawShrineMenu(HDC hdc, RECT clientRect)
{
    RECT menu = {clientRect.left + 380, clientRect.top + 150, clientRect.right - 380, clientRect.bottom - 150};
    fillRect(hdc, menu.left, menu.top, menu.right, menu.bottom, RGB(12, 16, 20));
    FrameRect(hdc, &menu, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, menu.left + 26, menu.top + 24, RGB(244, 247, 250), L"MurkShelter Pearl Network");
    drawTextLine(hdc, menu.left + 26, menu.top + 52, RGB(204, 212, 218), L"Rest, save, upgrade, and fast travel through linked pearls.");
    drawTextLine(hdc, menu.left + 26, menu.top + 96, RGB(232, 236, 240), g_demo.selectedShrineOption == 0 ? L"> Restore vitality and save" : L"  Restore vitality and save");
    drawTextLine(hdc, menu.left + 26, menu.top + 126, RGB(232, 236, 240), g_demo.selectedShrineOption == 1 ? L"> Save memory state" : L"  Save memory state");
    drawTextLine(hdc, menu.left + 26, menu.top + 156, RGB(232, 236, 240), g_demo.selectedShrineOption == 2 ? L"> Spend 40 brine salt on progression" : L"  Spend 40 brine salt on progression");
    drawTextLine(hdc, menu.left + 26, menu.top + 186, RGB(232, 236, 240), g_demo.selectedShrineOption == 3 ? L"> Fast travel to next linked MurkShelter" : L"  Fast travel to next linked MurkShelter");
    drawTextLine(hdc, menu.left + 26, menu.top + 216, RGB(232, 236, 240), g_demo.selectedShrineOption == 4 ? L"> Return to the marsh" : L"  Return to the marsh");
}

void drawViewMenu(Graphics &graphics, HDC hdc, RECT clientRect)
{
    RECT panel = {80, 60, clientRect.right - 80, clientRect.bottom - 60};
    drawImageAlpha(graphics, g_demo.assets.uiMenuPanel, (float)panel.left, (float)panel.top, (float)(panel.right - panel.left), (float)(panel.bottom - panel.top), 0.28f);
    fillRect(hdc, panel.left, panel.top, panel.right, panel.bottom, RGB(10, 14, 20));
    FrameRect(hdc, &panel, (HBRUSH)GetStockObject(WHITE_BRUSH));

    for (int index = 0; index < kViewTabCount; ++index)
    {
        int tabLeft = panel.left + 24 + index * 170;
        fillRect(hdc, tabLeft, panel.top + 18, tabLeft + 150, panel.top + 50, index == g_demo.currentViewTab ? RGB(46, 62, 76) : RGB(18, 24, 30));
        drawTextLine(hdc, tabLeft + 14, panel.top + 28, RGB(234, 238, 241), viewTabName((ViewTab)index));
    }

    RECT body = {panel.left + 28, panel.top + 74, panel.right - 28, panel.bottom - 28};
    if (g_demo.currentViewTab == TAB_MAP)
    {
        drawImageAlpha(graphics, g_demo.assets.worldMap, (float)body.left, (float)body.top, 540.0f, 540.0f, 0.92f);
        drawTextLine(hdc, body.left + 566, body.top + 18, RGB(244, 247, 250), L"Island Survey");
        drawTextLine(hdc, body.left + 566, body.top + 50, RGB(214, 220, 226), L"Area: 4 km by 3 km. Wet ruins, tidal caverns, basalt ridge, drowned village, temple crown.");
    }
    else if (g_demo.currentViewTab == TAB_QUESTLOG)
    {
        drawTextLine(hdc, body.left + 12, body.top + 12, RGB(244, 247, 250), L"Questlog");
        drawTextLine(hdc, body.left + 12, body.top + 44, RGB(214, 220, 226), currentObjective());
        drawTextLine(hdc, body.left + 12, body.top + 76, RGB(190, 200, 208), L"Seal progression: Mi-Go, Cultist, Star-Spawn, and Drowned Pilgrim carry the temple keys.");
        drawTextLine(hdc, body.left + 12, body.top + 104, RGB(190, 200, 208), L"Once four seals are held, approach the northern temple to wake the final duel.");
    }
    else if (g_demo.currentViewTab == TAB_CODEX)
    {
        int nearest = nearestEnemyIndex(99999.0f, 0);
        drawTextLine(hdc, body.left + 12, body.top + 12, RGB(244, 247, 250), L"Codex");
        wchar_t buffer[128];
        swprintf(buffer, 128, L"Discovered entities %d/%d", discoveredEnemyCount(), kTotalEnemies);
        drawTextLine(hdc, body.left + 12, body.top + 36, RGB(190, 200, 208), buffer);
        if (nearest >= 0)
        {
            drawImageFrame(graphics, g_demo.assets.enemyRosterSheet, enemyRosterFrame(g_demo.enemies[nearest].kind), kEnemyRosterColumns, 2, (float)body.left + 12.0f, (float)body.top + 56.0f, 280.0f, 180.0f, 0.96f);
            drawTextLine(hdc, body.left + 320, body.top + 70, RGB(214, 220, 226), enemyName(g_demo.enemies[nearest].kind));
            drawTextLine(hdc, body.left + 320, body.top + 102, RGB(190, 200, 208), isSealBearer(g_demo.enemies[nearest].kind) ? L"Seal carrier. Drops one temple seal on death." : L"Standard horror strain. No seal drop.");
            drawTextLine(hdc, body.left + 320, body.top + 130, RGB(190, 200, 208), g_demo.enemies[nearest].boss ? L"Boss archetype. Multi-phase pressure and higher cadence." : L"Field archetype. Tracks, dashes, strafes, or harpoons depending on breed.");
            drawTextLine(hdc, body.left + 320, body.top + 158, RGB(160, 196, 204), L"Research branch target: family-complete animation coverage and license-safe originality.");
        }
    }
    else if (g_demo.currentViewTab == TAB_CHARACTER)
    {
        wchar_t buffer[128];
        drawPlayerPresentation(graphics, (float)body.left + 18.0f, (float)body.top + 22.0f, 240.0f, 240.0f, PLAYER_ANIM_IDLE, 0.98f);
        drawTextLine(hdc, body.left + 280, body.top + 24, RGB(244, 247, 250), L"Character");
        drawTextLine(hdc, body.left + 280, body.top + 54, RGB(214, 220, 226), L"Fish-man drifter, black-tide survivor, resonance healer.");
        swprintf(buffer, 128, L"Seal Bindings %d/4  |  Moisture %.0f%%  |  Breath Sync %.0f%%", g_demo.templeSeals, g_demo.player.moisture * 100.0f, g_demo.player.breathingSync * 100.0f);
        drawTextLine(hdc, body.left + 280, body.top + 84, RGB(190, 200, 208), buffer);
        swprintf(buffer, 128, L"Vitality Rank %d  |  Stamina Rank %d  |  Air Actions %d", g_demo.vitalityRank, g_demo.staminaRank, g_demo.player.airActions);
        drawTextLine(hdc, body.left + 280, body.top + 112, RGB(190, 200, 208), buffer);
        drawTextLine(hdc, body.left + 280, body.top + 140, RGB(190, 200, 208), L"Lock-on turns your facing and camera into the active target while focus is held.");
    }
    else if (g_demo.currentViewTab == TAB_INVENTORY)
    {
        wchar_t buffer[128];
        drawTextLine(hdc, body.left + 12, body.top + 12, RGB(244, 247, 250), L"Inventory");
        swprintf(buffer, 128, L"Black Kelp %d  |  Salt Sigils %d  |  Temple Seals %d/4  |  Brine Salt %d", g_demo.blackKelp, g_demo.saltSigils, g_demo.templeSeals, g_demo.brineSalt);
        drawTextLine(hdc, body.left + 12, body.top + 44, RGB(214, 220, 226), buffer);
        swprintf(buffer, 128, L"Knives %d  |  Fire Bombs %d  |  Seed Pods %d", g_demo.throwingKnives, g_demo.fireBombs, g_demo.seedPods);
        drawTextLine(hdc, body.left + 12, body.top + 76, RGB(190, 200, 208), buffer);
        drawTextLine(hdc, body.left + 12, body.top + 108, RGB(190, 200, 208), L"Black kelp stabilizes breathing cadence. Brine salt powers MurkShelter upgrades and travel.");
    }
    else
    {
        wchar_t buffer[160];
        drawTextLine(hdc, body.left + 12, body.top + 12, RGB(244, 247, 250), L"Equipment");
        swprintf(buffer, 160, L"Melee: %ls  |  Projectile: %ls", kWeapons[g_demo.equippedMeleeWeapon].name, kWeapons[g_demo.equippedProjectileWeapon].name);
        drawTextLine(hdc, body.left + 12, body.top + 44, RGB(214, 220, 226), buffer);
        swprintf(buffer, 160, L"Armor Set: %ls  |  Defense %d  |  Mobility %d", kArmorSets[g_demo.equippedArmorSet].name, kArmorSets[g_demo.equippedArmorSet].defense, kArmorSets[g_demo.equippedArmorSet].mobility);
        drawTextLine(hdc, body.left + 12, body.top + 76, RGB(190, 200, 208), buffer);
        drawTextLine(hdc, body.left + 12, body.top + 108, RGB(190, 200, 208), L"Confirm cycles equipped gear here. Crafted suits bias ooze handling, salt insulation, or aerial control.");
    }
}

void drawControlsCard(HDC hdc)
{
    if (!g_demo.showControlsCard)
    {
        return;
    }
    RECT card = {22, 22, 470, 254};
    fillRect(hdc, card.left, card.top, card.right, card.bottom, RGB(10, 14, 20));
    FrameRect(hdc, &card, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, card.left + 18, card.top + 14, RGB(244, 247, 250), L"Xbox Series Controls + Research Notes");
    drawTextLine(hdc, card.left + 18, card.top + 42, RGB(214, 220, 226), L"Menu: Left Stick navigate, A confirm, B back");
    drawTextLine(hdc, card.left + 18, card.top + 62, RGB(214, 220, 226), L"Play: Start pause, View character/inventory/equipment/map/questlog/codex");
    drawTextLine(hdc, card.left + 18, card.top + 82, RGB(214, 220, 226), L"Left Stick move, Right Stick camera");
    drawTextLine(hdc, card.left + 18, card.top + 102, RGB(214, 220, 226), L"A jump, tap B dodge, hold B run");
    drawTextLine(hdc, card.left + 18, card.top + 122, RGB(214, 220, 226), L"X light, Y heavy, hold LT focus");
    drawTextLine(hdc, card.left + 18, card.top + 142, RGB(214, 220, 226), L"LB block, tap RT parry, hold RT crouch/slide while running");
    drawTextLine(hdc, card.left + 18, card.top + 170, RGB(190, 200, 208), L"Keyboard fallback: WASD, Space, Shift, J, K, Q, E, C, F, Esc, Tab");
    drawTextLine(hdc, card.left + 18, card.top + 198, RGB(160, 196, 204), L"Research docs: asset benchmark, bibliography, and provenance ledger live beside this build.");
}

void drawGameOver(HDC hdc, RECT clientRect)
{
    RECT panel = {clientRect.left + 360, clientRect.top + 190, clientRect.right - 360, clientRect.bottom - 190};
    fillRect(hdc, panel.left, panel.top, panel.right, panel.bottom, RGB(10, 12, 18));
    FrameRect(hdc, &panel, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, panel.left + 28, panel.top + 26, RGB(246, 248, 250), L"Returned To The Black Tide");
    RECT body = {panel.left + 28, panel.top + 72, panel.right - 28, panel.bottom - 30};
    drawParagraph(hdc, body, RGB(214, 220, 226), L"Your cadence broke and the island folded you back into its humid dark. Press A or Enter to crawl ashore again, or B to return to the title screen.");
}

void drawVictory(HDC hdc, RECT clientRect)
{
    RECT panel = {clientRect.left + 300, clientRect.top + 160, clientRect.right - 300, clientRect.bottom - 160};
    fillRect(hdc, panel.left, panel.top, panel.right, panel.bottom, RGB(12, 18, 16));
    FrameRect(hdc, &panel, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, panel.left + 28, panel.top + 24, RGB(246, 248, 250), L"InnsmouthIsland Research Cleared");
    RECT body = {panel.left + 28, panel.top + 74, panel.right - 28, panel.bottom - 30};
    drawParagraph(hdc, body, RGB(214, 220, 226), L"The reptilian abyss prince and jaguar eclipse tyrant are broken. Moisture, breath, and black jungle rhythm carried the fish-man through the island's 12 square kilometer nightmare. Press A or Enter to return to the title screen.");
}

void renderDemo(HDC hdc, RECT clientRect)
{
    Graphics graphics(hdc);
    drawBackground(graphics, hdc, clientRect);

    if (g_demo.mode == MODE_TITLE)
    {
        drawTitle(graphics, hdc, clientRect);
        drawControlsCard(hdc);
        return;
    }

    if (g_demo.mode == MODE_OPENING)
    {
        drawOpening(graphics, hdc, clientRect);
        drawControlsCard(hdc);
        return;
    }

    drawEnvironment(graphics, hdc, clientRect);
    drawPickups(graphics, hdc, clientRect);
    drawMurkShelters(graphics, hdc, clientRect);
    drawEnemies(graphics, hdc, clientRect);
    drawPlayer(graphics, hdc, clientRect);
    drawEnvironmentForeground(graphics, hdc, clientRect);
    drawVolumetricLighting(graphics, clientRect);
    drawHud(graphics, hdc, clientRect);
    drawNotification(hdc, clientRect);
    drawControlsCard(hdc);

    if (g_demo.mode == MODE_PAUSE)
    {
        drawPauseMenu(hdc, clientRect);
    }
    else if (g_demo.mode == MODE_VIEW_MENU)
    {
        drawViewMenu(graphics, hdc, clientRect);
    }
    else if (g_demo.mode == MODE_SHRINE)
    {
        drawShrineMenu(hdc, clientRect);
    }
    else if (g_demo.mode == MODE_GAME_OVER)
    {
        drawGameOver(hdc, clientRect);
    }
    else if (g_demo.mode == MODE_VICTORY)
    {
        drawVictory(hdc, clientRect);
    }
}

LRESULT CALLBACK demoWndProc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_CREATE:
        initializeDemo();
        SetTimer(hwnd, 1, 16, NULL);
        return 0;
    case WM_TIMER:
        updateMode(0.016f);
        InvalidateRect(hwnd, NULL, TRUE);
        return 0;
    case WM_KEYDOWN:
        if (wParam < 256)
        {
            if (!g_demo.keyboard.down[wParam])
            {
                g_demo.keyboard.pressed[wParam] = 1;
            }
            g_demo.keyboard.down[wParam] = 1;
        }
        return 0;
    case WM_KEYUP:
        if (wParam < 256)
        {
            g_demo.keyboard.down[wParam] = 0;
            g_demo.keyboard.released[wParam] = 1;
        }
        return 0;
    case WM_PAINT:
    {
        PAINTSTRUCT paint;
        RECT clientRect;
        HDC hdc = BeginPaint(hwnd, &paint);
        GetClientRect(hwnd, &clientRect);
        renderDemo(hdc, clientRect);
        EndPaint(hwnd, &paint);
        return 0;
    }
    case WM_DESTROY:
        KillTimer(hwnd, 1);
        shutdownDemo();
        PostQuitMessage(0);
        return 0;
    }

    return DefWindowProcW(hwnd, message, wParam, lParam);
}
} // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR commandLine, int showCommand)
{
    WNDCLASSEXW windowClass;
    HWND window;
    MSG message;

    (void)previous;
    (void)commandLine;

    ZeroMemory(&windowClass, sizeof(windowClass));
    windowClass.cbSize = sizeof(windowClass);
    windowClass.lpfnWndProc = demoWndProc;
    windowClass.hInstance = instance;
    windowClass.lpszClassName = kWindowClass;
    windowClass.hCursor = LoadCursor(NULL, IDC_ARROW);
    windowClass.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassExW(&windowClass);

    window = CreateWindowExW(
        WS_EX_APPWINDOW,
        kWindowClass,
        kWindowTitle,
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        kWindowWidth,
        kWindowHeight,
        NULL,
        NULL,
        instance,
        NULL);

    ShowWindow(window, showCommand);
    UpdateWindow(window);

    while (GetMessageW(&message, NULL, 0, 0) > 0)
    {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }

    return (int)message.wParam;
}