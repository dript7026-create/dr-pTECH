#define _CRT_SECURE_NO_WARNINGS
#define NOMINMAX

#include <windows.h>
#include <gdiplus.h>

#include <algorithm>
#include <cmath>
#include <cwchar>
#include <fstream>
#include <shellapi.h>
#include <string>

using namespace Gdiplus;

namespace
{
const wchar_t *kWindowClass = L"ORBEngineTutorialDemoWindow";
const int kWindowWidth = 1280;
const int kWindowHeight = 820;
const int kMaxEnemies = 8;
const int kMaxParticles = 24;
const int kMaxProjectiles = 32;
const int kTreasureCount = 3;
const float kWorldWidth = 100.0f;
const float kWorldHeight = 60.0f;

enum EnemyType
{
    ENEMY_OOZE_SCOUT,
    ENEMY_OOZE_MIRE,
    ENEMY_OOZE_HORROR
};

enum AIDisposition
{
    AI_PASSIVE,
    AI_INQUISITIVE,
    AI_HOSTILE,
    AI_TERRITORIAL
};

enum TutorialVariant
{
    TUTORIAL_PROTOTYPE,
    TUTORIAL_FINAL_PREVIEW
};

struct Vec2
{
    float x;
    float y;
};

struct Particle
{
    Vec2 position;
    Vec2 velocity;
    float life;
    float size;
    int active;
};

struct Projectile
{
    Vec2 position;
    Vec2 velocity;
    float life;
    float radius;
    int damage;
    int active;
};

struct TickGnosisFrame
{
    float anchorScaleConstant;
    float cameraCoherency;
    float framebufferRelativity;
    float sensoryEntropy;
    float consensusBias;
    float modulationBias;
    float mitigationBias;
    float recursionDepth;
};

struct Enemy
{
    EnemyType type;
    AIDisposition disposition;
    Vec2 position;
    Vec2 velocity;
    int hp;
    int maxHp;
    float cooldown;
    float stagger;
    float flash;
    float hoverPhase;
    float frequencyCoherency;
    int alive;
};

struct Treasure
{
    Vec2 position;
    int collected;
};

struct AssetBank
{
    Image *world;
    Image *player;
    Image *smoke;
    Image *slime;
    Image *wolf;
    Image *skeleton;
    Image *panel;
    Image *hud;
    Image *treasure;
    Image *boss;
    Image *healing;
    Image *lockon;
};

struct DemoState
{
    ULONG_PTR gdiplusToken;
    AssetBank assets;
    int keys[256];
    int titleScreenActive;
    int pauseActive;
    int showControlsCard;
    Vec2 playerPosition;
    Vec2 playerVelocity;
    Vec2 lastMoveDirection;
    int playerHp;
    int playerMaxHp;
    float stamina;
    float maxStamina;
    int healingCharges;
    int healingMaxCharges;
    float healRecharge;
    float blockTimer;
    float specialCharge;
    int focusHeld;
    int focusTarget;
    int promptVisible;
    int promptPage;
    int tutorialStage;
    int tutorialVariant;
    int waveSeed;
    int victory;
    int playerDead;
    int deathCount;
    int treasuresCollected;
    int archesFeedLoaded;
    int archesCampaignWeek;
    int archesCampaignStability;
    int archesFlashpointPressure;
    float worldTime;
    float spawnFxTime;
    float dodgeTimer;
    float attackCooldown;
    float hitFlash;
    float cameraShake;
    float scenePulse;
    float cameraPerception;
    float cameraMotion;
    float dreadPressure;
    float patootPresence;
    float bangoResolve;
    int comboCount;
    float comboTimer;
    Enemy enemies[kMaxEnemies];
    int enemyCount;
    Treasure treasures[kTreasureCount];
    Particle particles[kMaxParticles];
    Projectile projectiles[kMaxProjectiles];
    TickGnosisFrame tickGnosis;
    wchar_t archesActivePolicy[64];
    wchar_t archesFlashpointDistrict[96];
    wchar_t archesFlashpointCondition[64];
    wchar_t archesMissionLabel[96];
    wchar_t archesMissionDistrict[96];
    wchar_t archesMissionOperation[64];
    wchar_t archesMissionProtagonist[96];
};

DemoState g_demo = {};

std::wstring widen(const std::string &text)
{
    if (text.empty())
    {
        return std::wstring();
    }
    int length = MultiByteToWideChar(CP_UTF8, 0, text.c_str(), -1, NULL, 0);
    if (length <= 0)
    {
        return std::wstring(text.begin(), text.end());
    }
    std::wstring result((size_t)length - 1, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, text.c_str(), -1, &result[0], length);
    return result;
}

void copyWideField(wchar_t *target, size_t targetCount, const std::wstring &value)
{
    if (!target || targetCount == 0)
    {
        return;
    }
    wcsncpy(target, value.c_str(), targetCount - 1);
    target[targetCount - 1] = L'\0';
}

std::string readTextFile(const char *path)
{
    std::ifstream stream(path, std::ios::binary);
    if (!stream)
    {
        return std::string();
    }
    return std::string((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
}

std::string extractQuotedValue(const std::string &source, const std::string &key, size_t start)
{
    size_t keyPos = source.find(key, start);
    if (keyPos == std::string::npos)
    {
        return std::string();
    }
    size_t firstQuote = source.find('"', keyPos + key.size());
    if (firstQuote == std::string::npos)
    {
        return std::string();
    }
    size_t secondQuote = source.find('"', firstQuote + 1);
    if (secondQuote == std::string::npos)
    {
        return std::string();
    }
    return source.substr(firstQuote + 1, secondQuote - firstQuote - 1);
}

int extractIntValue(const std::string &source, const std::string &key, size_t start)
{
    size_t keyPos = source.find(key, start);
    if (keyPos == std::string::npos)
    {
        return 0;
    }
    keyPos += key.size();
    while (keyPos < source.size() && (source[keyPos] == ' ' || source[keyPos] == '\t'))
    {
        ++keyPos;
    }
    int sign = 1;
    if (keyPos < source.size() && source[keyPos] == '-')
    {
        sign = -1;
        ++keyPos;
    }
    int value = 0;
    while (keyPos < source.size() && source[keyPos] >= '0' && source[keyPos] <= '9')
    {
        value = value * 10 + (source[keyPos] - '0');
        ++keyPos;
    }
    return value * sign;
}

void loadArchesCampaignFeed()
{
    std::string payload = readTextFile("..\\ArchesAndAngels\\campaign_state.json");
    if (payload.empty())
    {
        g_demo.archesFeedLoaded = 0;
        return;
    }

    g_demo.archesCampaignWeek = extractIntValue(payload, "\"week\":", 0);
    g_demo.archesCampaignStability = extractIntValue(payload, "\"stability\":", 0);
    copyWideField(g_demo.archesActivePolicy, 64, widen(extractQuotedValue(payload, "\"activePolicy\":", 0)));

    size_t districtsStart = payload.find("\"districts\": [");
    size_t agendasStart = payload.find("\"agendas\": [");
    if (districtsStart != std::string::npos && agendasStart != std::string::npos && agendasStart > districtsStart)
    {
        std::string districtsBlock = payload.substr(districtsStart, agendasStart - districtsStart);
        size_t pos = 0;
        int bestPressure = -1;
        std::string bestName;
        std::string bestCondition;
        while ((pos = districtsBlock.find("\"name\":", pos)) != std::string::npos)
        {
            std::string name = extractQuotedValue(districtsBlock, "\"name\":", pos);
            int pressure = extractIntValue(districtsBlock, "\"pressure\":", pos);
            std::string condition = extractQuotedValue(districtsBlock, "\"condition\":", pos);
            if (pressure > bestPressure)
            {
                bestPressure = pressure;
                bestName = name;
                bestCondition = condition;
            }
            pos += 8;
        }
        g_demo.archesFlashpointPressure = bestPressure;
        copyWideField(g_demo.archesFlashpointDistrict, 96, widen(bestName));
        copyWideField(g_demo.archesFlashpointCondition, 64, widen(bestCondition));
    }

    size_t missionsStart = payload.find("\"missions\": [");
    size_t incidentsStart = payload.find("\"incidents\": [");
    if (missionsStart != std::string::npos && incidentsStart != std::string::npos && incidentsStart > missionsStart)
    {
        std::string missionsBlock = payload.substr(missionsStart, incidentsStart - missionsStart);
        copyWideField(g_demo.archesMissionLabel, 96, widen(extractQuotedValue(missionsBlock, "\"label\":", 0)));
        copyWideField(g_demo.archesMissionDistrict, 96, widen(extractQuotedValue(missionsBlock, "\"targetDistrict\":", 0)));
        copyWideField(g_demo.archesMissionOperation, 64, widen(extractQuotedValue(missionsBlock, "\"requiredOperation\":", 0)));
        copyWideField(g_demo.archesMissionProtagonist, 96, widen(extractQuotedValue(missionsBlock, "\"assignedProtagonist\":", 0)));
    }

    g_demo.archesFeedLoaded = 1;
}

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

float distance(Vec2 a, Vec2 b)
{
    return length({a.x - b.x, a.y - b.y});
}

float randomSigned(unsigned int *seed)
{
    *seed = (*seed * 1103515245u) + 12345u;
    return (float)((*seed >> 8) & 0xFFFF) / 32767.5f - 1.0f;
}

void resetParticles()
{
    for (int index = 0; index < kMaxParticles; ++index)
    {
        g_demo.particles[index].active = 0;
    }
}

void resetProjectiles()
{
    for (int index = 0; index < kMaxProjectiles; ++index)
    {
        g_demo.projectiles[index].active = 0;
    }
}

void spawnSmoke()
{
    unsigned int seed = 17u + (unsigned int)g_demo.deathCount * 31u;
    g_demo.spawnFxTime = 1.2f;
    for (int index = 0; index < kMaxParticles; ++index)
    {
        Particle &particle = g_demo.particles[index];
        particle.active = 1;
        particle.position = g_demo.playerPosition;
        particle.velocity.x = randomSigned(&seed) * 4.0f;
        particle.velocity.y = -1.5f + randomSigned(&seed) * 3.0f;
        particle.life = 0.6f + (float)(index % 4) * 0.08f;
        particle.size = 0.8f + (float)(index % 5) * 0.18f;
    }
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
    delete g_demo.assets.world;
    delete g_demo.assets.player;
    delete g_demo.assets.smoke;
    delete g_demo.assets.slime;
    delete g_demo.assets.wolf;
    delete g_demo.assets.skeleton;
    delete g_demo.assets.panel;
    delete g_demo.assets.hud;
    delete g_demo.assets.treasure;
    delete g_demo.assets.boss;
    delete g_demo.assets.healing;
    delete g_demo.assets.lockon;
    ZeroMemory(&g_demo.assets, sizeof(g_demo.assets));
}

void loadAssets()
{
    g_demo.assets.world = loadAsset(L"assets\\recraft_demo\\amazonian_island_world_keyart.png");
    g_demo.assets.player = loadAsset(L"assets\\recraft_demo\\player_reptilian_assassin_concept.png");
    g_demo.assets.smoke = loadAsset(L"assets\\recraft_demo\\player_spawn_smoke_fx.png");
    g_demo.assets.slime = loadAsset(L"assets\\recraft_demo\\enemy_slime_concept.png");
    g_demo.assets.wolf = loadAsset(L"assets\\recraft_demo\\enemy_wolf_concept.png");
    g_demo.assets.skeleton = loadAsset(L"assets\\recraft_demo\\enemy_skeleton_man_concept.png");
    g_demo.assets.panel = loadAsset(L"assets\\recraft_demo\\tutorial_prompt_ui_panel.png");
    g_demo.assets.hud = loadAsset(L"assets\\recraft_demo\\hud_health_stamina_compass.png");
    g_demo.assets.treasure = loadAsset(L"assets\\recraft_demo\\treasure_loot_chest_concept.png");
    g_demo.assets.boss = loadAsset(L"assets\\recraft_demo\\boss_duo_mesoamerican_hybrids.png");
    g_demo.assets.healing = loadAsset(L"assets\\recraft_demo\\healing_item_concept.png");
    g_demo.assets.lockon = loadAsset(L"assets\\recraft_demo\\focus_lockon_icon_set.png");
}

const wchar_t *enemyName(EnemyType type)
{
    switch (type)
    {
    case ENEMY_OOZE_SCOUT:
        return L"Ooze-Orb Scout";
    case ENEMY_OOZE_MIRE:
        return L"Ooze-Orb Mire";
    default:
        return L"Ooze-Orb Horror";
    }
}

const wchar_t *dispositionName(AIDisposition disposition)
{
    switch (disposition)
    {
    case AI_PASSIVE:
        return L"Passive";
    case AI_INQUISITIVE:
        return L"Inquisitive";
    case AI_HOSTILE:
        return L"Hostile";
    default:
        return L"Territorial";
    }
}

const wchar_t *tutorialVariantName()
{
    return g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW
               ? L"Tutorial 2: Final Game Preview"
               : L"Tutorial 1: Prototype Calibration";
}

const wchar_t *titleScreenSubtitle()
{
    if (g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW)
    {
        return L"A marketplace-facing final tutorial preview. Patoot is the heavy support signal, Bango carries the action load, and a persistent social-anxiety dread field pushes TickGnosis harder with denser orb-drone pacing.\n\nPress 1 for the prototype calibration slice. Press 2 for the final game preview slice. Press Enter, Space, or B to launch the selected tutorial. Press Tab to toggle the control reference card.";
    }

    return L"A least-trouble playable hybrid ORB tutorial slice: movement, jump, sprint, dodge, block, parry, focus hold, healing, special release, and three ooze-orb projectile drone archetypes inside a minimal coherency-testing simulator pocket.\n\nPress 1 for the prototype calibration slice. Press 2 for the final game preview slice. Press Enter, Space, or B to launch the selected tutorial. Press Tab to toggle the control reference card.";
}

Image *enemyImage(EnemyType type)
{
    switch (type)
    {
    case ENEMY_OOZE_SCOUT:
        return g_demo.assets.slime;
    case ENEMY_OOZE_MIRE:
        return g_demo.assets.skeleton;
    default:
        return g_demo.assets.lockon;
    }
}

void addEnemy(int slot, EnemyType type, AIDisposition disposition, float x, float y, int hp)
{
    Enemy &enemy = g_demo.enemies[slot];
    enemy.type = type;
    enemy.disposition = disposition;
    enemy.position = {x, y};
    enemy.velocity = {0.0f, 0.0f};
    enemy.hp = hp;
    enemy.maxHp = hp;
    enemy.cooldown = 0.0f;
    enemy.stagger = 0.0f;
    enemy.flash = 0.0f;
    enemy.hoverPhase = (x + y) * 0.11f;
    enemy.frequencyCoherency = clampf(0.52f + hp * 0.004f, 0.4f, 0.96f);
    enemy.alive = 1;
}

void spawnWave(int tutorialStage)
{
    g_demo.enemyCount = 0;
    ZeroMemory(g_demo.enemies, sizeof(g_demo.enemies));

    if (g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW)
    {
        if (tutorialStage == 1)
        {
            g_demo.enemyCount = 2;
            addEnemy(0, ENEMY_OOZE_SCOUT, AI_INQUISITIVE, 28.0f, 22.0f, 26);
            addEnemy(1, ENEMY_OOZE_SCOUT, AI_HOSTILE, 32.0f, 28.0f, 28);
        }
        else if (tutorialStage == 2)
        {
            g_demo.enemyCount = 2;
            addEnemy(0, ENEMY_OOZE_MIRE, AI_HOSTILE, 48.0f, 24.0f, 38);
            addEnemy(1, ENEMY_OOZE_SCOUT, AI_INQUISITIVE, 52.0f, 31.0f, 24);
        }
        else if (tutorialStage == 3)
        {
            g_demo.enemyCount = 2;
            addEnemy(0, ENEMY_OOZE_HORROR, AI_TERRITORIAL, 68.0f, 24.0f, 54);
            addEnemy(1, ENEMY_OOZE_MIRE, AI_HOSTILE, 72.0f, 31.0f, 36);
        }
        else if (tutorialStage == 4)
        {
            g_demo.enemyCount = 4;
            addEnemy(0, ENEMY_OOZE_SCOUT, AI_INQUISITIVE, 81.0f, 20.0f, 28);
            addEnemy(1, ENEMY_OOZE_MIRE, AI_HOSTILE, 86.0f, 26.0f, 40);
            addEnemy(2, ENEMY_OOZE_HORROR, AI_TERRITORIAL, 91.0f, 32.0f, 56);
            addEnemy(3, ENEMY_OOZE_SCOUT, AI_HOSTILE, 94.0f, 24.0f, 30);
        }
        return;
    }

    if (tutorialStage == 1)
    {
        g_demo.enemyCount = 1;
        addEnemy(0, ENEMY_OOZE_SCOUT, AI_INQUISITIVE, 28.0f, 24.0f, 28);
    }
    else if (tutorialStage == 2)
    {
        g_demo.enemyCount = 1;
        addEnemy(0, ENEMY_OOZE_MIRE, AI_HOSTILE, 46.0f, 28.0f, 38);
    }
    else if (tutorialStage == 3)
    {
        g_demo.enemyCount = 1;
        addEnemy(0, ENEMY_OOZE_HORROR, AI_TERRITORIAL, 66.0f, 26.0f, 52);
    }
    else if (tutorialStage == 4)
    {
        g_demo.enemyCount = 3;
        addEnemy(0, ENEMY_OOZE_SCOUT, AI_INQUISITIVE, 82.0f, 22.0f, 30);
        addEnemy(1, ENEMY_OOZE_MIRE, AI_HOSTILE, 87.0f, 28.0f, 42);
        addEnemy(2, ENEMY_OOZE_HORROR, AI_TERRITORIAL, 92.0f, 34.0f, 56);
    }
}

void resetWorld()
{
    int tutorialVariant = g_demo.tutorialVariant;
    ZeroMemory(g_demo.keys, sizeof(g_demo.keys));
    g_demo.titleScreenActive = 1;
    g_demo.pauseActive = 0;
    g_demo.showControlsCard = 1;
    g_demo.tutorialVariant = tutorialVariant == TUTORIAL_FINAL_PREVIEW ? TUTORIAL_FINAL_PREVIEW : TUTORIAL_PROTOTYPE;
    g_demo.playerPosition = {14.0f, 24.0f};
    g_demo.playerVelocity = {0.0f, 0.0f};
    g_demo.lastMoveDirection = {1.0f, 0.0f};
    g_demo.playerMaxHp = 100;
    g_demo.playerHp = 100;
    g_demo.maxStamina = 100.0f;
    g_demo.stamina = 100.0f;
    g_demo.healingMaxCharges = 2;
    g_demo.healingCharges = 2;
    g_demo.healRecharge = 0.0f;
    g_demo.blockTimer = 0.0f;
    g_demo.specialCharge = 0.0f;
    g_demo.focusHeld = 0;
    g_demo.focusTarget = -1;
    g_demo.promptVisible = 1;
    g_demo.promptPage = 0;
    g_demo.tutorialStage = 0;
    g_demo.waveSeed = 17;
    g_demo.victory = 0;
    g_demo.playerDead = 0;
    g_demo.treasuresCollected = 0;
    g_demo.worldTime = 0.0f;
    g_demo.dodgeTimer = 0.0f;
    g_demo.attackCooldown = 0.0f;
    g_demo.hitFlash = 0.0f;
    g_demo.cameraShake = 0.0f;
    g_demo.scenePulse = 0.0f;
    g_demo.cameraPerception = 0.84f;
    g_demo.cameraMotion = 0.0f;
    g_demo.dreadPressure = 0.22f;
    g_demo.patootPresence = 0.76f;
    g_demo.bangoResolve = 0.58f;
    g_demo.comboCount = 0;
    g_demo.comboTimer = 0.0f;
    g_demo.enemyCount = 0;
    g_demo.treasures[0] = {{26.0f, 18.0f}, 0};
    g_demo.treasures[1] = {{58.0f, 42.0f}, 0};
    g_demo.treasures[2] = {{78.0f, 18.0f}, 0};
    resetParticles();
    resetProjectiles();
    spawnSmoke();
    g_demo.tickGnosis = {1.0f, 0.84f, 0.72f, 0.22f, 0.76f, 0.74f, 0.68f, 2.3f};

    if (g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW)
    {
        g_demo.playerPosition = {12.0f, 24.0f};
        g_demo.playerMaxHp = 112;
        g_demo.playerHp = 112;
        g_demo.healingMaxCharges = 3;
        g_demo.healingCharges = 3;
        g_demo.specialCharge = 35.0f;
        g_demo.dreadPressure = 0.34f;
        g_demo.patootPresence = 0.84f;
        g_demo.bangoResolve = 0.46f;
        g_demo.treasures[0] = {{24.0f, 20.0f}, 0};
        g_demo.treasures[1] = {{54.0f, 42.0f}, 0};
        g_demo.treasures[2] = {{84.0f, 18.0f}, 0};
        g_demo.tickGnosis = {1.08f, 0.81f, 0.76f, 0.30f, 0.72f, 0.70f, 0.62f, 2.7f};
    }
}

void initializeDemo()
{
    GdiplusStartupInput startupInput;
    GdiplusStartup(&g_demo.gdiplusToken, &startupInput, NULL);
    loadAssets();
    resetWorld();
    loadArchesCampaignFeed();
}

void shutdownDemo()
{
    releaseAssets();
    GdiplusShutdown(g_demo.gdiplusToken);
}

Vec2 worldToScreen(Vec2 world, int clientWidth, int clientHeight, float *outScale)
{
    float cameraX = g_demo.playerPosition.x;
    float cameraY = g_demo.playerPosition.y - 8.0f;
    float relativeX = world.x - cameraX;
    float relativeY = world.y - cameraY;
    float horizon = clientHeight * 0.36f;
    float scale = clampf((0.55f + relativeY * 0.018f) * g_demo.tickGnosis.anchorScaleConstant, 0.42f, 1.95f);
    float shakeX = std::sin(g_demo.worldTime * 64.0f) * g_demo.cameraShake * 18.0f;
    float shakeY = std::cos(g_demo.worldTime * 52.0f) * g_demo.cameraShake * 12.0f;
    Vec2 screen;
    screen.x = clientWidth * 0.5f + relativeX * 22.0f + shakeX;
    screen.y = horizon + relativeY * 11.0f + shakeY;
    *outScale = scale;
    return screen;
}

void spawnProjectile(Vec2 origin, Vec2 direction, int damage, float speed, float radius)
{
    for (int index = 0; index < kMaxProjectiles; ++index)
    {
        Projectile &projectile = g_demo.projectiles[index];
        if (projectile.active)
        {
            continue;
        }
        projectile.active = 1;
        projectile.position = origin;
        projectile.velocity = {direction.x * speed, direction.y * speed};
        projectile.life = 2.6f;
        projectile.radius = radius;
        projectile.damage = damage;
        return;
    }
}

void updateTickGnosis(float deltaSeconds)
{
    int livingEnemies = 0;
    float coherencySum = 0.0f;
    for (int index = 0; index < g_demo.enemyCount; ++index)
    {
        if (!g_demo.enemies[index].alive)
        {
            continue;
        }
        livingEnemies += 1;
        coherencySum += g_demo.enemies[index].frequencyCoherency;
    }

    float enemyAverage = livingEnemies > 0 ? coherencySum / (float)livingEnemies : 0.6f;
    float playerMotion = clampf(length(g_demo.playerVelocity) / 18.0f, 0.0f, 1.0f);
    float hpRatio = (float)g_demo.playerHp / (float)g_demo.playerMaxHp;
    float staminaRatio = g_demo.stamina / g_demo.maxStamina;
    float comboBias = clampf((float)g_demo.comboCount / 6.0f, 0.0f, 1.0f);
    float dreadTarget = 0.14f + livingEnemies * 0.08f + (1.0f - hpRatio) * 0.34f + (g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW ? 0.08f : 0.0f);
    float patootTarget = (g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW ? 0.82f : 0.74f) + (g_demo.focusHeld ? 0.08f : -0.02f) + (g_demo.healingCharges > 0 ? 0.04f : -0.05f);
    float bangoTarget = 0.36f + hpRatio * 0.18f + staminaRatio * 0.14f + comboBias * 0.18f;
    g_demo.cameraMotion = playerMotion;
    g_demo.dreadPressure = clampf(g_demo.dreadPressure + (dreadTarget - g_demo.dreadPressure) * deltaSeconds * 1.6f, 0.08f, 0.96f);
    g_demo.patootPresence = clampf(g_demo.patootPresence + (patootTarget - g_demo.patootPresence) * deltaSeconds * 1.8f - g_demo.dreadPressure * deltaSeconds * 0.05f, 0.2f, 1.0f);
    g_demo.bangoResolve = clampf(g_demo.bangoResolve + (bangoTarget - g_demo.bangoResolve) * deltaSeconds * 1.6f - g_demo.dreadPressure * deltaSeconds * 0.08f, 0.15f, 1.0f);
    g_demo.tickGnosis.anchorScaleConstant = clampf(1.0f + enemyAverage * 0.18f + g_demo.scenePulse * 0.24f + g_demo.dreadPressure * 0.08f, 0.88f, 1.42f);
    g_demo.tickGnosis.cameraCoherency = clampf(0.92f - playerMotion * 0.30f + enemyAverage * 0.06f + g_demo.patootPresence * 0.10f - g_demo.dreadPressure * 0.08f, 0.32f, 0.98f);
    g_demo.tickGnosis.framebufferRelativity = clampf(0.58f + (1.0f - g_demo.tickGnosis.cameraCoherency) * 0.30f + g_demo.scenePulse * 0.22f + g_demo.dreadPressure * 0.12f, 0.3f, 1.06f);
    g_demo.tickGnosis.sensoryEntropy = clampf(0.12f + playerMotion * 0.24f + livingEnemies * 0.05f + g_demo.dreadPressure * 0.12f, 0.1f, 0.92f);
    g_demo.tickGnosis.consensusBias = clampf(0.48f + g_demo.tickGnosis.cameraCoherency * 0.36f, 0.2f, 1.0f);
    g_demo.tickGnosis.modulationBias = clampf(0.40f + g_demo.tickGnosis.anchorScaleConstant * 0.22f + g_demo.bangoResolve * 0.12f, 0.2f, 1.0f);
    g_demo.tickGnosis.mitigationBias = clampf(0.40f + (1.0f - g_demo.tickGnosis.sensoryEntropy) * 0.24f + g_demo.patootPresence * 0.22f, 0.2f, 1.0f);
    g_demo.tickGnosis.recursionDepth = clampf((g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW ? 2.6f : 2.3f) + livingEnemies * 0.20f + g_demo.dreadPressure * 0.36f, 2.3f, 4.0f);
    g_demo.cameraPerception = clampf(g_demo.tickGnosis.cameraCoherency * 0.52f + g_demo.patootPresence * 0.30f + g_demo.bangoResolve * 0.18f - g_demo.dreadPressure * 0.14f, 0.2f, 1.0f);
}

void updatePromptState()
{
    if (g_demo.playerDead || g_demo.victory)
    {
        g_demo.promptVisible = 1;
        g_demo.promptPage = 0;
    }
}

void dismissPromptsForAction()
{
    if (g_demo.titleScreenActive)
    {
        g_demo.titleScreenActive = 0;
        g_demo.promptVisible = 1;
        g_demo.promptPage = 0;
        return;
    }

    if (g_demo.promptVisible)
    {
        g_demo.promptVisible = 0;
    }
}

void advanceTutorialIfNeeded()
{
    int livingEnemies = 0;
    for (int index = 0; index < g_demo.enemyCount; ++index)
    {
        if (g_demo.enemies[index].alive)
        {
            livingEnemies += 1;
        }
    }

    if (g_demo.tutorialStage == 0 && g_demo.playerPosition.x > 18.0f)
    {
        g_demo.tutorialStage = 1;
        g_demo.promptVisible = 1;
        g_demo.promptPage = 0;
        spawnWave(1);
    }
    else if (g_demo.tutorialStage == 1 && livingEnemies == 0)
    {
        g_demo.tutorialStage = 2;
        g_demo.promptVisible = 1;
        g_demo.promptPage = 0;
        spawnWave(2);
    }
    else if (g_demo.tutorialStage == 2 && livingEnemies == 0 && g_demo.playerPosition.x > 42.0f)
    {
        g_demo.tutorialStage = 3;
        g_demo.promptVisible = 1;
        g_demo.promptPage = 0;
        spawnWave(3);
    }
    else if (g_demo.tutorialStage == 3 && livingEnemies == 0 && g_demo.playerPosition.x > 74.0f)
    {
        g_demo.tutorialStage = 4;
        g_demo.promptVisible = 1;
        g_demo.promptPage = 0;
        spawnWave(4);
    }
    else if (g_demo.tutorialStage == 4 && livingEnemies == 0)
    {
        g_demo.tutorialStage = 5;
        g_demo.victory = 1;
        g_demo.promptVisible = 1;
        g_demo.promptPage = 0;
    }
}

void collectTreasures()
{
    for (int index = 0; index < kTreasureCount; ++index)
    {
        Treasure &treasure = g_demo.treasures[index];
        if (!treasure.collected && distance(g_demo.playerPosition, treasure.position) < 3.4f)
        {
            treasure.collected = 1;
            g_demo.treasuresCollected += 1;
            g_demo.playerHp = std::min(g_demo.playerMaxHp, g_demo.playerHp + 16);
            g_demo.healingCharges = g_demo.healingMaxCharges;
            g_demo.specialCharge = std::min(100.0f, g_demo.specialCharge + 30.0f);
        }
    }
}

void refreshFocusTarget()
{
    float bestDistance = 9999.0f;
    g_demo.focusTarget = -1;
    if (!g_demo.focusHeld)
    {
        return;
    }

    for (int index = 0; index < g_demo.enemyCount; ++index)
    {
        if (!g_demo.enemies[index].alive)
        {
            continue;
        }
        float candidate = distance(g_demo.playerPosition, g_demo.enemies[index].position);
        if (candidate < bestDistance && candidate < 24.0f)
        {
            bestDistance = candidate;
            g_demo.focusTarget = index;
        }
    }
}

void damageEnemy(int index, int amount, float stagger)
{
    if (index < 0 || index >= g_demo.enemyCount || !g_demo.enemies[index].alive)
    {
        return;
    }

    Enemy &enemy = g_demo.enemies[index];
    enemy.hp -= amount;
    enemy.stagger = std::max(enemy.stagger, stagger);
    enemy.flash = 0.2f;
    enemy.frequencyCoherency = clampf(enemy.frequencyCoherency - 0.05f, 0.2f, 1.0f);
    g_demo.specialCharge = std::min(100.0f, g_demo.specialCharge + 12.0f);
    if (enemy.hp <= 0)
    {
        enemy.hp = 0;
        enemy.alive = 0;
        g_demo.specialCharge = std::min(100.0f, g_demo.specialCharge + 18.0f);
    }
}

void handleAttack(int heavy)
{
    float range = heavy ? 7.0f : 5.6f;
    int damage = heavy ? 24 : 13;
    float cost = heavy ? 28.0f : 12.0f;
    int target = g_demo.focusTarget;

    if (g_demo.promptVisible || g_demo.pauseActive || g_demo.playerDead || g_demo.victory || g_demo.stamina < cost || g_demo.attackCooldown > 0.0f)
    {
        return;
    }

    g_demo.stamina -= cost;
    g_demo.attackCooldown = heavy ? 0.44f : 0.24f;
    g_demo.cameraShake = std::max(g_demo.cameraShake, heavy ? 0.32f : 0.18f);
    g_demo.scenePulse = std::max(g_demo.scenePulse, heavy ? 0.24f : 0.14f);
    g_demo.comboTimer = 1.2f;
    g_demo.comboCount = std::min(g_demo.comboCount + 1, 4);
    if (target >= 0 && g_demo.enemies[target].alive && distance(g_demo.playerPosition, g_demo.enemies[target].position) <= range)
    {
        damageEnemy(target, damage, heavy ? 0.6f : 0.25f);
        return;
    }

    for (int index = 0; index < g_demo.enemyCount; ++index)
    {
        if (g_demo.enemies[index].alive && distance(g_demo.playerPosition, g_demo.enemies[index].position) <= range)
        {
            damageEnemy(index, damage, heavy ? 0.6f : 0.25f);
            return;
        }
    }
}

void handleSpecial()
{
    if (g_demo.promptVisible || g_demo.playerDead || g_demo.victory || g_demo.specialCharge < 100.0f)
    {
        return;
    }

    g_demo.specialCharge = 0.0f;
    g_demo.cameraShake = std::max(g_demo.cameraShake, 0.45f);
    g_demo.scenePulse = std::max(g_demo.scenePulse, 0.35f);
    for (int index = 0; index < g_demo.enemyCount; ++index)
    {
        if (g_demo.enemies[index].alive && distance(g_demo.playerPosition, g_demo.enemies[index].position) < 10.5f)
        {
            damageEnemy(index, 38, 0.9f);
        }
    }
}

void handleHeal()
{
    if (g_demo.promptVisible || g_demo.playerDead || g_demo.victory || g_demo.healingCharges <= 0 || g_demo.playerHp >= g_demo.playerMaxHp)
    {
        return;
    }

    g_demo.healingCharges -= 1;
    g_demo.healRecharge = 14.0f;
    g_demo.playerHp = std::min(g_demo.playerMaxHp, g_demo.playerHp + 34);
}

void respawnPlayer()
{
    g_demo.playerDead = 0;
    g_demo.deathCount += 1;
    resetWorld();
    g_demo.titleScreenActive = 0;
}

void handleDodge()
{
    if (g_demo.titleScreenActive || g_demo.promptVisible || g_demo.pauseActive || g_demo.playerDead || g_demo.victory)
    {
        return;
    }
    if (g_demo.dodgeTimer > 0.0f || g_demo.stamina < 18.0f)
    {
        return;
    }

    Vec2 dashDirection = normalize(g_demo.lastMoveDirection);
    if (length(dashDirection) < 0.01f)
    {
        dashDirection = {1.0f, 0.0f};
    }

    g_demo.stamina -= 18.0f;
    g_demo.dodgeTimer = 0.28f;
    g_demo.playerVelocity.x = dashDirection.x * 26.0f;
    g_demo.playerVelocity.y = dashDirection.y * 26.0f;
    g_demo.cameraShake = std::max(g_demo.cameraShake, 0.12f);
}

void updatePlayer(float deltaSeconds)
{
    Vec2 input = {0.0f, 0.0f};
    float speed = g_demo.focusHeld ? 8.0f : 11.5f;

    if (g_demo.titleScreenActive || g_demo.promptVisible || g_demo.pauseActive || g_demo.playerDead || g_demo.victory)
    {
        g_demo.playerVelocity = {0.0f, 0.0f};
        return;
    }

    if (g_demo.keys['W'])
    {
        input.y -= 1.0f;
    }
    if (g_demo.keys['S'])
    {
        input.y += 1.0f;
    }
    if (g_demo.keys['A'])
    {
        input.x -= 1.0f;
    }
    if (g_demo.keys['D'])
    {
        input.x += 1.0f;
    }

    input = normalize(input);
    if (length(input) > 0.0f)
    {
        g_demo.lastMoveDirection = input;
    }

    if (g_demo.dodgeTimer > 0.0f)
    {
        g_demo.playerVelocity.x *= 0.94f;
        g_demo.playerVelocity.y *= 0.94f;
    }
    else
    {
        g_demo.playerVelocity.x = input.x * speed;
        g_demo.playerVelocity.y = input.y * speed;
    }
    g_demo.playerPosition.x = clampf(g_demo.playerPosition.x + g_demo.playerVelocity.x * deltaSeconds, 4.0f, kWorldWidth - 4.0f);
    g_demo.playerPosition.y = clampf(g_demo.playerPosition.y + g_demo.playerVelocity.y * deltaSeconds, 8.0f, kWorldHeight - 4.0f);
}

void updateEnemies(float deltaSeconds)
{
    for (int index = 0; index < g_demo.enemyCount; ++index)
    {
        Enemy &enemy = g_demo.enemies[index];
        if (!enemy.alive)
        {
            continue;
        }

        Vec2 toPlayer = {g_demo.playerPosition.x - enemy.position.x, g_demo.playerPosition.y - enemy.position.y};
        float playerDistance = length(toPlayer);
        Vec2 desired = {0.0f, 0.0f};
        float baseSpeed = 4.0f;

        enemy.cooldown = std::max(0.0f, enemy.cooldown - deltaSeconds);
        enemy.stagger = std::max(0.0f, enemy.stagger - deltaSeconds);
        enemy.flash = std::max(0.0f, enemy.flash - deltaSeconds);

        if (enemy.stagger > 0.0f)
        {
            continue;
        }

        enemy.hoverPhase += deltaSeconds * (enemy.type == ENEMY_OOZE_HORROR ? 2.2f : 1.7f);

        if (enemy.disposition == AI_PASSIVE)
        {
            desired.x = std::sinf(g_demo.worldTime + index) * 1.6f;
            desired.y = std::cosf(g_demo.worldTime * 0.7f + index) * 1.0f;
            baseSpeed = 1.5f;
        }
        else if (enemy.disposition == AI_INQUISITIVE)
        {
            desired = normalize({toPlayer.x + std::cosf(g_demo.worldTime + index) * 3.0f, toPlayer.y + std::sinf(g_demo.worldTime * 0.9f) * 3.0f});
            baseSpeed = 2.4f;
        }
        else
        {
            desired = normalize(toPlayer);
            baseSpeed = enemy.type == ENEMY_OOZE_HORROR ? 4.6f : 3.5f;
        }

        enemy.velocity.x = desired.x * baseSpeed;
        enemy.velocity.y = desired.y * baseSpeed + std::sinf(enemy.hoverPhase) * 0.25f;
        enemy.position.x = clampf(enemy.position.x + enemy.velocity.x * deltaSeconds, 4.0f, kWorldWidth - 4.0f);
        enemy.position.y = clampf(enemy.position.y + enemy.velocity.y * deltaSeconds, 8.0f, kWorldHeight - 4.0f);

        if (playerDistance < 18.0f && enemy.cooldown <= 0.0f)
        {
            Vec2 shot = normalize(toPlayer);
            int damage = enemy.type == ENEMY_OOZE_HORROR ? 12 : (enemy.type == ENEMY_OOZE_MIRE ? 9 : 7);
            float speed = enemy.type == ENEMY_OOZE_SCOUT ? 9.4f : (enemy.type == ENEMY_OOZE_MIRE ? 7.8f : 6.8f);
            spawnProjectile(enemy.position, shot, damage, speed, enemy.type == ENEMY_OOZE_HORROR ? 1.0f : 0.72f);
            enemy.cooldown = enemy.type == ENEMY_OOZE_SCOUT ? 1.0f : (enemy.type == ENEMY_OOZE_MIRE ? 1.3f : 1.6f);
        }
    }
}

void updateProjectiles(float deltaSeconds)
{
    for (int index = 0; index < kMaxProjectiles; ++index)
    {
        Projectile &projectile = g_demo.projectiles[index];
        if (!projectile.active)
        {
            continue;
        }
        projectile.life -= deltaSeconds;
        if (projectile.life <= 0.0f)
        {
            projectile.active = 0;
            continue;
        }
        projectile.position.x += projectile.velocity.x * deltaSeconds;
        projectile.position.y += projectile.velocity.y * deltaSeconds;
        if (distance(projectile.position, g_demo.playerPosition) <= projectile.radius + 1.0f)
        {
            if (g_demo.blockTimer > 0.16f)
            {
                g_demo.specialCharge = std::min(100.0f, g_demo.specialCharge + 10.0f);
                g_demo.cameraShake = std::max(g_demo.cameraShake, 0.08f);
                projectile.active = 0;
                continue;
            }
            if (g_demo.blockTimer > 0.0f)
            {
                g_demo.stamina = std::max(0.0f, g_demo.stamina - 7.0f);
                projectile.active = 0;
                continue;
            }
            if (g_demo.dodgeTimer > 0.0f)
            {
                projectile.active = 0;
                continue;
            }

            g_demo.playerHp -= projectile.damage;
            g_demo.hitFlash = 0.25f;
            g_demo.cameraShake = std::max(g_demo.cameraShake, 0.16f);
            projectile.active = 0;
            if (g_demo.playerHp <= 0)
            {
                g_demo.playerHp = 0;
                g_demo.playerDead = 1;
                g_demo.promptVisible = 1;
                g_demo.promptPage = 0;
            }
        }
    }
}

void updateRecharge(float deltaSeconds)
{
    g_demo.stamina = std::min(g_demo.maxStamina, g_demo.stamina + deltaSeconds * 24.0f);
    g_demo.blockTimer = std::max(0.0f, g_demo.blockTimer - deltaSeconds);
    g_demo.dodgeTimer = std::max(0.0f, g_demo.dodgeTimer - deltaSeconds);
    g_demo.attackCooldown = std::max(0.0f, g_demo.attackCooldown - deltaSeconds);
    g_demo.hitFlash = std::max(0.0f, g_demo.hitFlash - deltaSeconds);
    g_demo.cameraShake = std::max(0.0f, g_demo.cameraShake - deltaSeconds * 1.8f);
    g_demo.scenePulse = std::max(0.0f, g_demo.scenePulse - deltaSeconds * 1.4f);
    g_demo.comboTimer = std::max(0.0f, g_demo.comboTimer - deltaSeconds);
    if (g_demo.comboTimer <= 0.0f)
    {
        g_demo.comboCount = 0;
    }
    if (g_demo.healingCharges < g_demo.healingMaxCharges)
    {
        g_demo.healRecharge -= deltaSeconds;
        if (g_demo.healRecharge <= 0.0f)
        {
            g_demo.healingCharges += 1;
            if (g_demo.healingCharges < g_demo.healingMaxCharges)
            {
                g_demo.healRecharge = 14.0f;
            }
            else
            {
                g_demo.healRecharge = 0.0f;
            }
        }
    }
}

void updateParticles(float deltaSeconds)
{
    for (int index = 0; index < kMaxParticles; ++index)
    {
        Particle &particle = g_demo.particles[index];
        if (!particle.active)
        {
            continue;
        }
        particle.life -= deltaSeconds;
        if (particle.life <= 0.0f)
        {
            particle.active = 0;
            continue;
        }
        particle.position.x += particle.velocity.x * deltaSeconds;
        particle.position.y += particle.velocity.y * deltaSeconds;
        particle.velocity.y -= 0.4f * deltaSeconds;
    }
}

void updateDemo(float deltaSeconds)
{
    g_demo.worldTime += deltaSeconds;
    g_demo.focusHeld = g_demo.keys[VK_SPACE] ? 1 : 0;
    updatePromptState();
    if (g_demo.pauseActive)
    {
        updateRecharge(deltaSeconds);
        updateParticles(deltaSeconds);
        return;
    }
    refreshFocusTarget();
    updatePlayer(deltaSeconds);
    collectTreasures();
    updateEnemies(deltaSeconds);
    updateProjectiles(deltaSeconds);
    updateRecharge(deltaSeconds);
    updateParticles(deltaSeconds);
    updateTickGnosis(deltaSeconds);
    advanceTutorialIfNeeded();
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

void drawGauge(HDC hdc, int x, int y, int width, int height, float ratio, COLORREF fill, const wchar_t *label)
{
    RECT border = {x, y, x + width, y + height};
    FrameRect(hdc, &border, (HBRUSH)GetStockObject(WHITE_BRUSH));
    fillRect(hdc, x + 2, y + 2, x + 2 + (int)((width - 4) * clampf(ratio, 0.0f, 1.0f)), y + height - 2, fill);
    drawTextLine(hdc, x, y - 18, RGB(235, 239, 243), label);
}

void drawBackdrop(Graphics &graphics, HDC hdc, RECT clientRect)
{
    int width = clientRect.right - clientRect.left;
    int height = clientRect.bottom - clientRect.top;
    int pulseLift = (int)(g_demo.scenePulse * 18.0f);
    for (int band = 0; band < 12; ++band)
    {
        int top = (height * band) / 12;
        int bottom = (height * (band + 1)) / 12;
        int r = 12 + band * 4 + pulseLift / 2;
        int g = 18 + band * 6 + pulseLift;
        int b = 28 + band * 7 + pulseLift / 2;
        fillRect(hdc, 0, top, width, bottom, RGB(r, g, b));
    }

    SolidBrush anchorBrush(Color(90, 164, 238, 255));
    graphics.FillEllipse(&anchorBrush, (REAL)(width - 240), 52.0f, 144.0f, 144.0f);

    for (int pocket = 0; pocket < 6; ++pocket)
    {
        float orbit = (float)pocket * 0.9f + g_demo.worldTime * (0.2f + pocket * 0.03f);
        float radius = 44.0f + pocket * 18.0f;
        float centerX = width * 0.72f + std::cos(orbit) * radius;
        float centerY = 124.0f + std::sin(orbit * 1.2f) * (16.0f + pocket * 2.0f);
        BYTE alpha = (BYTE)(40 + g_demo.tickGnosis.framebufferRelativity * 70.0f + pocket * 8);
        SolidBrush pocketBrush(Color(alpha, 88 + pocket * 18, 156 + pocket * 10, 214 + pocket * 6));
        graphics.FillEllipse(&pocketBrush, centerX - 18.0f, centerY - 18.0f, 36.0f, 36.0f);
    }

    int horizon = (int)(height * 0.36f);
    for (int line = 0; line < 18; ++line)
    {
        float t = (float)line / 17.0f;
        int y = horizon + (int)(t * (height - horizon - 50));
        int inset = (int)((1.0f - t) * width * 0.34f);
        fillRect(hdc, inset, y, width - inset, y + 2, RGB(58 + line * 4, 92 + line * 2, 74 + line));
    }

    for (int column = 0; column < 16; ++column)
    {
        int x = width / 2 + (column - 8) * 56;
        fillRect(hdc, x, horizon + 12, x + 2, height - 88, RGB(42, 70, 54));
    }

    for (int canopy = 0; canopy < 9; ++canopy)
    {
        int left = 40 + canopy * 142 - (int)(std::sin(g_demo.worldTime * 0.35f + canopy) * 18.0f);
        int top = 86 + (canopy % 3) * 14;
        fillRect(hdc, left, top, left + 120, top + 18, RGB(20, 34 + canopy * 3, 50 + canopy * 2));
    }
}

void drawWorldMarker(HDC hdc, RECT clientRect, Vec2 position, COLORREF color, const wchar_t *label)
{
    float scale = 1.0f;
    Vec2 screen = worldToScreen(position, clientRect.right, clientRect.bottom, &scale);
    int left = (int)screen.x - 8;
    int top = (int)screen.y - 28;
    fillRect(hdc, left, top, left + 16, top + 16, color);
    drawTextLine(hdc, left - 10, top - 18, RGB(236, 240, 244), label);
}

void drawTreasure(Graphics &graphics, HDC hdc, RECT clientRect, const Treasure &treasure)
{
    float scale = 1.0f;
    Vec2 screen = worldToScreen(treasure.position, clientRect.right, clientRect.bottom, &scale);
    int size = (int)(46.0f * scale);
    if (g_demo.assets.treasure)
    {
        drawImageAlpha(graphics, g_demo.assets.treasure, screen.x - size * 0.5f, screen.y - size, (float)size, (float)size, 0.92f);
    }
    else
    {
        fillRect(hdc, (int)screen.x - 12, (int)screen.y - 22, (int)screen.x + 12, (int)screen.y, RGB(184, 148, 62));
    }
}

void drawEnemy(Graphics &graphics, HDC hdc, RECT clientRect, const Enemy &enemy, int focused)
{
    float scale = 1.0f;
    Vec2 screen = worldToScreen(enemy.position, clientRect.right, clientRect.bottom, &scale);
    int width = (int)(62.0f * scale);
    int height = (int)(62.0f * scale);
    float hoverOffset = std::sinf(enemy.hoverPhase) * 10.0f;
    Color border = focused ? Color(255, 246, 214, 76) : Color(255, 86, 188, 196);
    Pen pen(border, focused ? 3.0f : 2.0f);
    BYTE red = enemy.type == ENEMY_OOZE_HORROR ? 214 : (enemy.type == ENEMY_OOZE_MIRE ? 126 : 98);
    BYTE green = enemy.type == ENEMY_OOZE_HORROR ? 92 : (enemy.type == ENEMY_OOZE_MIRE ? 210 : 224);
    BYTE blue = enemy.type == ENEMY_OOZE_HORROR ? 214 : (enemy.type == ENEMY_OOZE_MIRE ? 118 : 255);
    SolidBrush flashBrush(Color((BYTE)(enemy.flash > 0.0f ? 232 : 180), red, green, blue));
    SolidBrush haloBrush(Color(68, red, green, blue));

    graphics.FillEllipse(&haloBrush, screen.x - width * 0.8f, screen.y - height - hoverOffset - 8.0f, width * 1.6f, height * 1.6f);
    graphics.FillEllipse(&flashBrush, screen.x - width * 0.5f, screen.y - height - hoverOffset, (REAL)width, (REAL)height);
    graphics.DrawEllipse(&pen, screen.x - width * 0.5f, screen.y - height - hoverOffset, (REAL)width, (REAL)height);

    if (focused && g_demo.assets.lockon)
    {
        drawImageAlpha(graphics, g_demo.assets.lockon, screen.x - 28.0f, screen.y - height - hoverOffset - 34.0f, 56.0f, 56.0f, 0.95f);
    }

    wchar_t buffer[64];
    swprintf(buffer, 64, L"%ls %d/%d", enemyName(enemy.type), enemy.hp, enemy.maxHp);
    drawTextLine(hdc, (int)screen.x - width / 2, (int)screen.y - height - (int)hoverOffset - 18, RGB(244, 247, 250), buffer);
}

void drawPlayer(Graphics &graphics, HDC hdc, RECT clientRect)
{
    float scale = 1.0f;
    Vec2 screen = worldToScreen(g_demo.playerPosition, clientRect.right, clientRect.bottom, &scale);
    int width = (int)(88.0f * scale);
    int height = (int)(118.0f * scale);
    int blurOffset = (int)(g_demo.tickGnosis.framebufferRelativity * 14.0f);
    fillRect(hdc, (int)screen.x - 34, (int)screen.y - 4, (int)screen.x + 34, (int)screen.y + 4, RGB(14, 16, 18));
    fillRect(hdc, (int)screen.x - 28 - blurOffset, (int)screen.y - 56, (int)screen.x + 28 - blurOffset, (int)screen.y + 6, RGB(28, 60, 82));
    if (g_demo.assets.player)
    {
        drawImageAlpha(graphics, g_demo.assets.player, screen.x - width * 0.5f, screen.y - height, (float)width, (float)width, 0.98f);
    }
    else
    {
        fillRect(hdc, (int)screen.x - 20, (int)screen.y - 66, (int)screen.x + 20, (int)screen.y, RGB(82, 180, 132));
    }
    if (g_demo.dodgeTimer > 0.0f)
    {
        SolidBrush dodgeBrush(Color(80, 118, 224, 232));
        graphics.FillEllipse(&dodgeBrush, screen.x - 54.0f, screen.y - 96.0f, 108.0f, 88.0f);
    }
    drawTextLine(hdc, (int)screen.x - 44, (int)screen.y - height - 16, RGB(246, 248, 250), L"Bango: Unchained");
}

void drawProjectiles(Graphics &graphics, RECT clientRect)
{
    for (int index = 0; index < kMaxProjectiles; ++index)
    {
        Projectile &projectile = g_demo.projectiles[index];
        if (!projectile.active)
        {
            continue;
        }
        float scale = 1.0f;
        Vec2 screen = worldToScreen(projectile.position, clientRect.right, clientRect.bottom, &scale);
        float size = projectile.radius * 20.0f * scale;
        SolidBrush halo(Color(64, 182, 224, 255));
        SolidBrush core(Color(220, 214, 244, 255));
        graphics.FillEllipse(&halo, screen.x - size * 0.8f, screen.y - size * 0.8f, size * 1.6f, size * 1.6f);
        graphics.FillEllipse(&core, screen.x - size * 0.45f, screen.y - size * 0.45f, size * 0.9f, size * 0.9f);
    }
}

void drawParticles(Graphics &graphics, RECT clientRect)
{
    for (int index = 0; index < kMaxParticles; ++index)
    {
        Particle &particle = g_demo.particles[index];
        if (!particle.active)
        {
            continue;
        }
        float scale = 1.0f;
        Vec2 screen = worldToScreen(particle.position, clientRect.right, clientRect.bottom, &scale);
        float size = particle.size * 18.0f * scale;
        BYTE alpha = (BYTE)(clampf(particle.life, 0.0f, 1.0f) * 185.0f);
        SolidBrush brush(Color(alpha, 214, 228, 230));
        graphics.FillEllipse(&brush, screen.x - size * 0.5f, screen.y - size, size, size * 0.72f);
        if (g_demo.assets.smoke)
        {
            drawImageAlpha(graphics, g_demo.assets.smoke, screen.x - size * 0.6f, screen.y - size * 1.1f, size * 1.2f, size * 1.2f, particle.life * 0.8f);
        }
    }
}

const wchar_t *objectiveText()
{
    if (g_demo.playerDead)
    {
        return L"Death tutorial active: press R to respawn and revisit the encounter.";
    }
    if (g_demo.victory)
    {
        return g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW ? L"Final tutorial preview clear. Marketplace-facing slice complete." : L"Orb-drone tutorial clear. Demo slice complete.";
    }
    if (g_demo.tutorialStage == 0)
    {
        return g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW ? L"Move through the dread corridor and trigger the Patoot-guided first contact lesson." : L"Move through the calibration corridor to trigger the first orb lesson.";
    }
    if (g_demo.tutorialStage == 1)
    {
        return g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW ? L"Clear the opening scout pair and keep Patoot support above the dread floor." : L"Defeat the Ooze-Orb Scout with light and heavy attacks.";
    }
    if (g_demo.tutorialStage == 2)
    {
        return g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW ? L"Advance into the market-pressure pocket and stabilize block, dodge, and recovery timing." : L"Advance and clear the Ooze-Orb Mire while managing block and dodge timing.";
    }
    if (g_demo.tutorialStage == 3)
    {
        return g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW ? L"Break the Horror-led dread spike with focus hold, Patoot support, and special-charge control." : L"Face the Ooze-Orb Horror and learn focus hold plus special-charge management.";
    }
    return g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW ? L"Clear the full preview wave and prove the final tutorial contract is readable, tense, and finishable." : L"Clear the final combined orb wave and validate movement, combat, and coherency perception.";
}

const wchar_t *compassDirection()
{
    Vec2 target = {22.0f, 24.0f};
    if (g_demo.tutorialStage == 1)
    {
        target = {28.0f, 24.0f};
    }
    else if (g_demo.tutorialStage == 2)
    {
        target = {46.0f, 28.0f};
    }
    else if (g_demo.tutorialStage == 3)
    {
        target = {66.0f, 26.0f};
    }
    else if (g_demo.tutorialStage >= 4)
    {
        target = {88.0f, 28.0f};
    }

    Vec2 delta = {target.x - g_demo.playerPosition.x, target.y - g_demo.playerPosition.y};
    if (std::fabs(delta.x) > std::fabs(delta.y))
    {
        return delta.x >= 0.0f ? L"E" : L"W";
    }
    return delta.y >= 0.0f ? L"S" : L"N";
}

void drawHud(Graphics &graphics, HDC hdc, RECT clientRect)
{
    wchar_t buffer[128];
    fillRect(hdc, 18, clientRect.bottom - 144, 410, clientRect.bottom - 56, RGB(12, 16, 24));
    drawGauge(hdc, 34, clientRect.bottom - 116, 220, 18, (float)g_demo.playerHp / (float)g_demo.playerMaxHp, RGB(166, 58, 58), L"Health");
    drawGauge(hdc, 34, clientRect.bottom - 78, 220, 18, g_demo.stamina / g_demo.maxStamina, RGB(78, 164, 108), L"Stamina");
    swprintf(buffer, 128, L"Heals %d/%d  Special %.0f%%  Combo x%d  Anchors %d/%d", g_demo.healingCharges, g_demo.healingMaxCharges, g_demo.specialCharge, g_demo.comboCount, g_demo.treasuresCollected, kTreasureCount);
    drawTextLine(hdc, 274, clientRect.bottom - 106, RGB(230, 235, 240), buffer);
    drawTextLine(hdc, 274, clientRect.bottom - 78, RGB(188, 196, 204), L"Keyboard: WASD move, Shift dodge, J light, K heavy, L block/parry, I heal, Space focus hold, U special");

    fillRect(hdc, clientRect.right - 254, 18, clientRect.right - 18, 92, RGB(12, 16, 24));
    drawTextLine(hdc, clientRect.right - 234, 30, RGB(242, 245, 248), L"Compass");
    swprintf(buffer, 128, L"Objective %ls", compassDirection());
    drawTextLine(hdc, clientRect.right - 234, 56, RGB(224, 230, 236), buffer);
    drawTextLine(hdc, clientRect.right - 234, 74, RGB(188, 196, 204), objectiveText());

    if (g_demo.assets.hud)
    {
        drawImageAlpha(graphics, g_demo.assets.hud, clientRect.right - 244.0f, 20.0f, 210.0f, 62.0f, 0.18f);
    }
    if (g_demo.assets.healing)
    {
        drawImageAlpha(graphics, g_demo.assets.healing, 426.0f, clientRect.bottom - 142.0f, 64.0f, 64.0f, 0.85f);
    }

    if (g_demo.archesFeedLoaded)
    {
        RECT archesPanel = {18, 18, 382, 170};
        fillRect(hdc, archesPanel.left, archesPanel.top, archesPanel.right, archesPanel.bottom, RGB(14, 18, 26));
        FrameRect(hdc, &archesPanel, (HBRUSH)GetStockObject(WHITE_BRUSH));
        drawTextLine(hdc, archesPanel.left + 14, archesPanel.top + 12, RGB(244, 247, 250), L"ArchesAndAngels Feed");
        swprintf(buffer, 128, L"Week %d  Stability %d  Policy %ls", g_demo.archesCampaignWeek, g_demo.archesCampaignStability, g_demo.archesActivePolicy);
        drawTextLine(hdc, archesPanel.left + 14, archesPanel.top + 36, RGB(214, 220, 226), buffer);
        swprintf(buffer, 128, L"Flashpoint: %ls (%ls, pressure %d)", g_demo.archesFlashpointDistrict, g_demo.archesFlashpointCondition, g_demo.archesFlashpointPressure);
        drawTextLine(hdc, archesPanel.left + 14, archesPanel.top + 62, RGB(236, 198, 134), buffer);
        drawTextLine(hdc, archesPanel.left + 14, archesPanel.top + 88, RGB(244, 247, 250), L"Mission Board Lead");
        drawTextLine(hdc, archesPanel.left + 14, archesPanel.top + 110, RGB(214, 220, 226), g_demo.archesMissionLabel);
        swprintf(buffer, 128, L"District %ls  Focus %ls", g_demo.archesMissionDistrict, g_demo.archesMissionOperation);
        drawTextLine(hdc, archesPanel.left + 14, archesPanel.top + 132, RGB(188, 196, 204), buffer);
        swprintf(buffer, 128, L"Assigned %ls", g_demo.archesMissionProtagonist);
        drawTextLine(hdc, archesPanel.left + 14, archesPanel.top + 150, RGB(188, 196, 204), buffer);
    }

    RECT gnosisPanel = {18, 178, 382, 304};
    fillRect(hdc, gnosisPanel.left, gnosisPanel.top, gnosisPanel.right, gnosisPanel.bottom, RGB(12, 18, 28));
    FrameRect(hdc, &gnosisPanel, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, gnosisPanel.left + 14, gnosisPanel.top + 12, RGB(244, 247, 250), L"TickGnosis");
    swprintf(buffer, 128, L"Anchor %.2f  Camera %.2f  Frame %.2f", g_demo.tickGnosis.anchorScaleConstant, g_demo.tickGnosis.cameraCoherency, g_demo.tickGnosis.framebufferRelativity);
    drawTextLine(hdc, gnosisPanel.left + 14, gnosisPanel.top + 38, RGB(214, 220, 226), buffer);
    swprintf(buffer, 128, L"Entropy %.2f  Consensus %.2f  Mitigation %.2f", g_demo.tickGnosis.sensoryEntropy, g_demo.tickGnosis.consensusBias, g_demo.tickGnosis.mitigationBias);
    drawTextLine(hdc, gnosisPanel.left + 14, gnosisPanel.top + 62, RGB(188, 196, 204), buffer);
    swprintf(buffer, 128, L"Recursion %.2fD  Camera perception %.2f", g_demo.tickGnosis.recursionDepth, g_demo.cameraPerception);
    drawTextLine(hdc, gnosisPanel.left + 14, gnosisPanel.top + 86, RGB(236, 198, 134), buffer);
    swprintf(buffer, 128, L"Patoot %.0f%%  Bango %.0f%%  Dread %.0f%%", g_demo.patootPresence * 100.0f, g_demo.bangoResolve * 100.0f, g_demo.dreadPressure * 100.0f);
    drawTextLine(hdc, gnosisPanel.left + 14, gnosisPanel.top + 108, RGB(200, 212, 238), buffer);
    drawTextLine(hdc, gnosisPanel.left + 14, gnosisPanel.top + 130, RGB(188, 196, 204), L"Patoot-heavy support boosts mitigation. Dread reduces coherency. Bango resolve restores readability through successful pressure.");
}

void drawPromptPanel(Graphics &graphics, HDC hdc, RECT clientRect)
{
    const wchar_t *pages[3] = {};
    int pageCount = 0;
    RECT panel = {84, 88, clientRect.right - 84, 286};

    if (!g_demo.promptVisible)
    {
        return;
    }

    if (g_demo.playerDead)
    {
        pages[0] = L"Death Tutorial\n\nYou were dropped, which confirms the fail-state loop. Press R to respawn at the spawn-smoke checkpoint. Earlier blocks, cleaner parries, and shorter movement arcs will stabilize the run.";
        pageCount = 1;
    }
    else if (g_demo.victory)
    {
        pages[0] = g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW
                       ? L"Preview Tutorial Complete\n\nThe final-game-facing tutorial preview is clear. The slice now demonstrates Patoot-heavy support, Bango combat execution, social-anxiety dread pressure, readable orb-drone escalation, and a finish-ready onboarding contract for PlayNOW packaging."
                       : L"Tutorial Complete\n\nAll three ooze-orb drone archetypes are cleared. The slice now covers movement, dodge timing, block and parry, focus hold, healing, special release, projectile pressure, and TickGnosis-based camera moderation.";
        pageCount = 1;
    }
    else if (g_demo.tutorialStage == 0)
    {
        if (g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW)
        {
            pages[0] = L"Page 1\n\nTutorial 2 is the final game preview slice. Patoot is the heavy social-support presence, Bango is the lighter but actionable lead, and the tutorial should feel tense without becoming unreadable. Move through the corridor to trigger the first contact pair.";
            pages[1] = L"Page 2\n\nCombat contract: LB light attack, RT heavy attack, click left stick to block, click right stick to parry, hold LT for focus and ability steering. Keyboard fallback: J light, K heavy, L block/parry, Space focus, Shift dodge. Keep Patoot support high by focusing, healing on time, and not overextending.";
            pages[2] = L"Page 3\n\nThe social-anxiety dread system is represented as rising TickGnosis pressure: denser waves, stronger entropy, and reduced camera readability until Patoot mitigation and Bango resolve pull the frame back into alignment.";
        }
        else
        {
            pages[0] = L"Page 1\n\nBango: Unchained - Bango&Patoot starts in a minimal consensus-render simulator pocket. Move through the gradient lane to wake the first drone. Gamepad contract: left stick move, right stick camera, tap B to jump, hold B to sprint, A crouch or slide.";
            pages[1] = L"Page 2\n\nCombat contract: LB light attack, RT heavy attack, click left stick to block, click right stick to parry, hold LT for focus and ability steering. Keyboard fallback: J light, K heavy, L block/parry, Space focus, Shift dodge.";
            pages[2] = L"Page 3\n\nTickGnosis tracks anchor-scale, camera coherency, and framebuffer relativity so the demo can test layered depth, blur moderation, and 2.3D to 4D recursive-space presentation without depending on a full production scene.";
        }
        pageCount = 3;
    }
    else if (g_demo.tutorialStage == 1)
    {
        pages[0] = g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW
                       ? L"Opening Contact Pair\n\nTwo scouts open the final preview tutorial. This is the first check that tension stays readable: keep moving, stay in focus when needed, and avoid letting the dread meter own the camera."
                       : L"Ooze-Orb Scout\n\nThe Scout is fast and curious. It pressures with light projectiles and teaches movement, jump, sprint, and basic light-heavy confirmation.";
        pageCount = 1;
    }
    else if (g_demo.tutorialStage == 2)
    {
        pages[0] = g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW
                       ? L"Market Pressure Pocket\n\nThe Mire pair introduces heavier drag and more crowded spacing. This is where the preview tutorial starts selling the final game: support, dread, and recovery all matter at once."
                       : L"Ooze-Orb Mire\n\nThe Mire is slower but denser. Its shots drift with heavier coherency drag, forcing block and dodge timing while you hold focus on target.";
        pages[1] = g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW
                       ? L"Patoot Support Loop\n\nPatoot-heavy support is expressed through timely healing, focus discipline, and mitigation. Bango resolve comes from successful strings, movement confidence, and not freezing under pressure."
                       : L"Support Systems\n\nBlock just before impact to parry a projectile cleanly. Search for anchors to refill healing charges, restore health, and accelerate the special meter.";
        pageCount = 2;
    }
    else if (g_demo.tutorialStage == 3)
    {
        pages[0] = g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW
                       ? L"Horror Threshold\n\nThe Horror-led wave is the dread spike. It should feel like encroaching pressure, not visual collapse. Use focus, special release, and tighter lanes to hold the frame together."
                       : L"Ooze-Orb Horror\n\nThe Horror is the anchor-scale stress test. Its slower, heavier projectiles and stronger coherency signature are what the camera-perception system is judging against.";
        pageCount = 1;
    }
    else
    {
        pages[0] = g_demo.tutorialVariant == TUTORIAL_FINAL_PREVIEW
                       ? L"Marketplace-Ready Tutorial Finish\n\nThis combined wave is the shipping proof point: movement, readability, Patoot support, Bango action, dread pressure, healing, special release, and a clear finish state in one compact onboarding slice."
                       : L"Final Combined Wave\n\nAll three orb-drone archetypes share the void pocket. Use movement, focus hold, light-heavy strings, parries, healing, and special release to finish the tutorial.";
        pageCount = 1;
    }

    g_demo.promptPage = std::max(0, std::min(g_demo.promptPage, pageCount - 1));
    fillRect(hdc, panel.left, panel.top, panel.right, panel.bottom, RGB(20, 24, 34));
    if (g_demo.assets.panel)
    {
        drawImageAlpha(graphics, g_demo.assets.panel, (float)panel.left, (float)panel.top, (float)(panel.right - panel.left), (float)(panel.bottom - panel.top), 0.20f);
    }
    FrameRect(hdc, &panel, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, panel.left + 24, panel.top + 18, RGB(246, 248, 250), L"Tutorial Prompt");
    drawTextLine(hdc, panel.left + 24, panel.bottom - 28, RGB(214, 220, 226), L"B close  |  Q previous page  |  E next page");
    drawTextLine(hdc, panel.right - 96, panel.top + 18, RGB(214, 220, 226), pageCount > 0 ? L"Pages" : L"");

    RECT textRect = {panel.left + 24, panel.top + 50, panel.right - 24, panel.bottom - 42};
    DrawTextW(hdc, pages[g_demo.promptPage], -1, &textRect, DT_WORDBREAK);
}

void drawSideCards(Graphics &graphics, HDC hdc, RECT clientRect)
{
    RECT leftPanel = {clientRect.right - 282, 112, clientRect.right - 22, 420};
    fillRect(hdc, leftPanel.left, leftPanel.top, leftPanel.right, leftPanel.bottom, RGB(12, 16, 24));
    FrameRect(hdc, &leftPanel, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, leftPanel.left + 16, leftPanel.top + 14, RGB(244, 247, 250), L"Current Target");

    if (g_demo.focusTarget >= 0 && g_demo.enemies[g_demo.focusTarget].alive)
    {
        Enemy &enemy = g_demo.enemies[g_demo.focusTarget];
        drawImageAlpha(graphics, enemyImage(enemy.type), (float)leftPanel.left + 16.0f, (float)leftPanel.top + 42.0f, 228.0f, 152.0f, 0.96f);
        wchar_t buffer[128];
        swprintf(buffer, 128, L"%ls", enemyName(enemy.type));
        drawTextLine(hdc, leftPanel.left + 18, leftPanel.top + 208, RGB(244, 247, 250), buffer);
        swprintf(buffer, 128, L"AI %ls", dispositionName(enemy.disposition));
        drawTextLine(hdc, leftPanel.left + 18, leftPanel.top + 232, RGB(212, 220, 226), buffer);
        swprintf(buffer, 128, L"HP %d/%d", enemy.hp, enemy.maxHp);
        drawTextLine(hdc, leftPanel.left + 18, leftPanel.top + 256, RGB(212, 220, 226), buffer);
    }
    else
    {
        drawImageAlpha(graphics, g_demo.assets.player, (float)leftPanel.left + 16.0f, (float)leftPanel.top + 42.0f, 228.0f, 152.0f, 0.90f);
        drawTextLine(hdc, leftPanel.left + 18, leftPanel.top + 214, RGB(244, 247, 250), L"Roaming state");
        drawTextLine(hdc, leftPanel.left + 18, leftPanel.top + 238, RGB(212, 220, 226), L"Hold Space to lock focus and test coherency-guided camera perception.");
    }

    if (g_demo.tutorialStage >= 3 || g_demo.victory)
    {
        RECT bossPanel = {clientRect.right - 282, 438, clientRect.right - 22, clientRect.bottom - 166};
        fillRect(hdc, bossPanel.left, bossPanel.top, bossPanel.right, bossPanel.bottom, RGB(18, 14, 22));
        FrameRect(hdc, &bossPanel, (HBRUSH)GetStockObject(WHITE_BRUSH));
        drawTextLine(hdc, bossPanel.left + 16, bossPanel.top + 14, RGB(246, 248, 250), L"Orb Drone Suite");
        drawTextLine(hdc, bossPanel.left + 16, bossPanel.top + 48, RGB(214, 220, 226), L"Scout: fast, light, probing");
        drawTextLine(hdc, bossPanel.left + 16, bossPanel.top + 74, RGB(214, 220, 226), L"Mire: dense, dragging, sustained");
        drawTextLine(hdc, bossPanel.left + 16, bossPanel.top + 100, RGB(214, 220, 226), L"Horror: heavy, anchor-scale stressor");
        drawTextLine(hdc, bossPanel.left + 16, bossPanel.top + 134, RGB(236, 198, 134), L"All three validate recursive layer scaling and projectile readability.");
    }
}

void drawStateOverlay(HDC hdc, RECT clientRect, const wchar_t *title, const wchar_t *subtitle)
{
    RECT overlay = {clientRect.left + 180, clientRect.top + 130, clientRect.right - 180, clientRect.bottom - 150};
    fillRect(hdc, overlay.left, overlay.top, overlay.right, overlay.bottom, RGB(14, 18, 26));
    FrameRect(hdc, &overlay, (HBRUSH)GetStockObject(WHITE_BRUSH));
    drawTextLine(hdc, overlay.left + 34, overlay.top + 34, RGB(246, 248, 250), title);
    RECT textRect = {overlay.left + 34, overlay.top + 78, overlay.right - 34, overlay.bottom - 40};
    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, RGB(220, 226, 232));
    DrawTextW(hdc, subtitle, -1, &textRect, DT_WORDBREAK);
}

void renderDemo(HDC hdc, RECT clientRect)
{
    Graphics graphics(hdc);
    if (g_demo.hitFlash > 0.0f)
    {
        fillRect(hdc, 0, 0, clientRect.right, clientRect.bottom, RGB(36 + (int)(g_demo.hitFlash * 120.0f), 18, 18));
    }
    drawBackdrop(graphics, hdc, clientRect);

    drawWorldMarker(hdc, clientRect, {18.0f, 24.0f}, RGB(72, 176, 204), L"Calibration Gate");
    drawWorldMarker(hdc, clientRect, {82.0f, 24.0f}, RGB(182, 144, 64), L"Consensus Anchor");

    for (int index = 0; index < kTreasureCount; ++index)
    {
        if (!g_demo.treasures[index].collected)
        {
            drawTreasure(graphics, hdc, clientRect, g_demo.treasures[index]);
        }
    }

    for (int index = 0; index < g_demo.enemyCount; ++index)
    {
        if (g_demo.enemies[index].alive)
        {
            drawEnemy(graphics, hdc, clientRect, g_demo.enemies[index], index == g_demo.focusTarget);
        }
    }

    drawPlayer(graphics, hdc, clientRect);
    drawProjectiles(graphics, clientRect);
    drawParticles(graphics, clientRect);
    drawHud(graphics, hdc, clientRect);
    drawPromptPanel(graphics, hdc, clientRect);
    drawSideCards(graphics, hdc, clientRect);

    if (g_demo.titleScreenActive)
    {
        drawStateOverlay(hdc, clientRect, tutorialVariantName(), titleScreenSubtitle());
    }
    else if (g_demo.pauseActive)
    {
        drawStateOverlay(hdc, clientRect, L"Paused", L"Combat, movement, and tutorial progression are paused. Press P or Escape to resume.");
    }

    if (g_demo.showControlsCard)
    {
        RECT card = {22, 22, 336, 188};
        fillRect(hdc, card.left, card.top, card.right, card.bottom, RGB(12, 16, 22));
        FrameRect(hdc, &card, (HBRUSH)GetStockObject(WHITE_BRUSH));
        drawTextLine(hdc, card.left + 16, card.top + 14, RGB(244, 247, 250), L"Controls");
        drawTextLine(hdc, card.left + 16, card.top + 40, RGB(214, 220, 226), L"WASD move");
        drawTextLine(hdc, card.left + 16, card.top + 60, RGB(214, 220, 226), L"Shift dodge, hold movement for sprint feel");
        drawTextLine(hdc, card.left + 16, card.top + 80, RGB(214, 220, 226), L"J light, K heavy, chain for combo pressure");
        drawTextLine(hdc, card.left + 16, card.top + 100, RGB(214, 220, 226), L"L block and timed parry, Space hold focus");
        drawTextLine(hdc, card.left + 16, card.top + 120, RGB(214, 220, 226), L"I heal, U special, B close prompt");
        drawTextLine(hdc, card.left + 16, card.top + 140, RGB(214, 220, 226), L"Q/E page, P pause, R respawn, Tab hide card");
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
        updateDemo(0.016f);
        InvalidateRect(hwnd, NULL, TRUE);
        return 0;
    case WM_KEYDOWN:
        if (wParam < 256)
        {
            g_demo.keys[wParam] = 1;
        }
        if (wParam == VK_RETURN || wParam == VK_SPACE)
        {
            dismissPromptsForAction();
        }
        else if (wParam == '1' && g_demo.titleScreenActive)
        {
            g_demo.tutorialVariant = TUTORIAL_PROTOTYPE;
            resetWorld();
        }
        else if (wParam == '2' && g_demo.titleScreenActive)
        {
            g_demo.tutorialVariant = TUTORIAL_FINAL_PREVIEW;
            resetWorld();
        }
        else if (wParam == 'J')
        {
            handleAttack(0);
        }
        else if (wParam == 'K')
        {
            handleAttack(1);
        }
        else if (wParam == VK_SHIFT)
        {
            handleDodge();
        }
        else if (wParam == 'L')
        {
            g_demo.blockTimer = 0.28f;
        }
        else if (wParam == 'I')
        {
            handleHeal();
        }
        else if (wParam == 'U')
        {
            handleSpecial();
        }
        else if (wParam == 'B')
        {
            dismissPromptsForAction();
        }
        else if (wParam == 'Q' && g_demo.promptVisible)
        {
            g_demo.promptPage = std::max(0, g_demo.promptPage - 1);
        }
        else if (wParam == 'E' && g_demo.promptVisible)
        {
            g_demo.promptPage += 1;
        }
        else if (wParam == VK_TAB)
        {
            g_demo.showControlsCard = !g_demo.showControlsCard;
        }
        else if (wParam == 'P' || wParam == VK_ESCAPE)
        {
            if (!g_demo.titleScreenActive && !g_demo.playerDead && !g_demo.victory)
            {
                g_demo.pauseActive = !g_demo.pauseActive;
                g_demo.promptVisible = g_demo.pauseActive ? 0 : g_demo.promptVisible;
            }
        }
        else if (wParam == 'R' && g_demo.playerDead)
        {
            respawnPlayer();
        }
        InvalidateRect(hwnd, NULL, TRUE);
        return 0;
    case WM_KEYUP:
        if (wParam < 256)
        {
            g_demo.keys[wParam] = 0;
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
        L"Bango: Unchained - Bango&Patoot",
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