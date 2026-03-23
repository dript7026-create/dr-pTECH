/* ===================================================================
   Crepulin: Enfant; .xxDetnDimension
   Win32 + GDI+ graphical prototype with Xbox Series controller support
   Build: g++ -std=c++17 -municode Crepulin_Enfant_DetnDimension.cpp
          -lgdiplus -lgdi32 -luser32 -lshell32 -o Crepulin_Enfant_DetnDimension.exe
   =================================================================== */
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

using namespace Gdiplus;

namespace {

/* ── Palette (GDD colours) ──────────────────────────────────────── */
static const COLORREF COL_BG_DEEP       = RGB(9, 11, 14);
static const COLORREF COL_BG_PANEL      = RGB(18, 20, 26);
static const COLORREF COL_NICOTINE      = RGB(190, 175, 100);
static const COLORREF COL_DEAD_TEAL     = RGB(70, 115, 105);
static const COLORREF COL_STAIRWELL     = RGB(60, 90, 55);
static const COLORREF COL_SODIUM        = RGB(225, 165, 60);
static const COLORREF COL_BRUISED       = RGB(108, 70, 135);
static const COLORREF COL_CHALK_WHITE   = RGB(240, 240, 235);
static const COLORREF COL_RUST_RED      = RGB(175, 55, 45);
static const COLORREF COL_BLACK_LACQUER = RGB(14, 14, 20);
static const COLORREF COL_WARM_ORANGE   = RGB(230, 145, 55);
static const COLORREF COL_GAUGE_BG      = RGB(35, 38, 42);

/* ── Gameplay constants ─────────────────────────────────────────── */
#define CREP_ROOM_COUNT   6
#define CREP_TOOL_COUNT   9
#define CREP_THREAT_COUNT 4

#define ABILITY_HOUSE_LISTENING    (1u << 0)
#define ABILITY_CURTAIN_CUT        (1u << 1)
#define ABILITY_STOVE_BLESSING     (1u << 2)
#define ABILITY_WARMTH_CARRY       (1u << 3)
#define ABILITY_BLACK_ROAD_REFUSAL (1u << 4)

enum RoomKind {
    ROOM_COURTYARD,
    ROOM_STAIRWELL,
    ROOM_CURTAIN_FLAT,
    ROOM_STOVE_NICHE,
    ROOM_SERVICE_SHAFT,
    ROOM_BLACK_ROAD_VAULT,
};

enum RuleKind {
    RULE_BREAD_OFF_FLOOR,
    RULE_NAME_THE_CORRIDOR,
    RULE_CURTAINS_TIED,
    RULE_CROSS_STEAM_WARM,
    RULE_DO_NOT_ANSWER_AFTER_MIDNIGHT,
    RULE_MIRROR_COVERED,
    RULE_COUNT,
};

enum ToolKind {
    TOOL_CANDLE_STUB,
    TOOL_BOX_CUTTER,
    TOOL_KEY_RING,
    TOOL_IRON_SPOON,
    TOOL_THREAD_SPOOL,
    TOOL_CHALK,
    TOOL_BREAD_SALT,
    TOOL_HAND_BELL,
    TOOL_GLASS_MARBLE,
};

enum ThreatKind {
    THREAT_DOMOV_KEEPER,
    THREAT_KEYHOLE_KIKIMORA,
    THREAT_BLACK_ROAD_CHAUFFEUR,
    THREAT_CREPULIN_BLOOM,
};

enum GameScreen {
    SCREEN_TITLE,
    SCREEN_PLAY,
    SCREEN_ENDING,
    SCREEN_GAME_OVER,
};

/* ── Data structs ───────────────────────────────────────────────── */
struct ToolState {
    ToolKind kind;
    const wchar_t *name;
    int available;
};

struct RoomState {
    RoomKind kind;
    const wchar_t *name;
    const wchar_t *description;
    int rule_respected[RULE_COUNT];
    float corruption;
    float shelter;
    int hidden_route_revealed;
    int visited;
};

struct ThreatState {
    ThreatKind kind;
    const wchar_t *name;
    float pressure;
    int active;
};

struct EnfantState {
    RoomKind room;
    float dread;
    float warmth;
    float health;
    unsigned int abilities;
    int children_rescued;
    int hide_streak;
};

struct CrepulinState {
    RoomState rooms[CREP_ROOM_COUNT];
    ThreatState threats[CREP_THREAT_COUNT];
    ToolState tools[CREP_TOOL_COUNT];
    EnfantState enfant;
    float domov_favor;
    float babka_favor;
    int turns;
    int story_gate;
    wchar_t status[256];
};

/* ── Asset / image types ────────────────────────────────────────── */
struct AssetImage {
    std::wstring path;
    Image *image;
};

/* ── Controller types ───────────────────────────────────────────── */
struct ControllerState {
    bool connected;
    WORD buttons;
    WORD previousButtons;
    float lx, ly, rx, ry, lt, rt;
    bool lsUp, lsDown, lsLeft, lsRight;
    bool prevLsUp, prevLsDown, prevLsLeft, prevLsRight;
};

typedef DWORD(WINAPI *XInputGetStateProc)(DWORD, XINPUT_STATE *);

/* ── Asset store ────────────────────────────────────────────────── */
struct CrepAssets {
    std::wstring root;
    std::vector<AssetImage> rooms;       // 6 room backgrounds
    std::vector<AssetImage> enfant;      // idle/walk/fear/hide/ritual
    std::vector<AssetImage> threats;     // domov/kikimora/chauffeur/bloom
    std::vector<AssetImage> npcs;        // babka/bird
    std::vector<AssetImage> tools;       // 9 tool icons
    std::vector<AssetImage> fx;          // dread/warmth/crepulin/headlights
    std::vector<AssetImage> ui;          // gauges
    std::vector<AssetImage> screens;     // title/ending/game_over
};

/* ── Global game state ──────────────────────────────────────────── */
struct AppState {
    HWND window;
    ULONG_PTR gdiplusToken;
    HMODULE xinputModule;
    XInputGetStateProc xinputGetState;
    ControllerState controller;

    bool keyDown[256];
    bool keyPressed[256];
    bool keyReleased[256];

    CrepulinState game;
    CrepAssets assets;
    GameScreen screen;

    int selectedAction;       // 0..7 action menu index
    int selectedTool;         // current tool tab
    bool actionExecuted;      // flag to drive one-shot per input
    float statusFlash;        // flash timer
    float animTimer;          // general animation tick
};

static AppState g_app;

/* ── Rule name table ────────────────────────────────────────────── */
static const wchar_t *k_rule_names[RULE_COUNT] = {
    L"Keep bread off the floor.",
    L"Name the corridor before crossing it.",
    L"Do not leave curtains half-tied.",
    L"Cross steam rooms warm, not cold.",
    L"Do not answer corridor voices after midnight.",
    L"Keep the mirror covered when you sleep.",
};

static const wchar_t *k_action_names[] = {
    L"Listen",
    L"Hide",
    L"Offer bread & salt",
    L"Cut curtains",
    L"Light candle / warmth",
    L"Bargain / Refuse",
    L"Move forward",
    L"Status",
};
#define ACTION_COUNT 8

/* ── Utility ────────────────────────────────────────────────────── */
static float clampf(float v, float lo, float hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

static void set_status(const wchar_t *text) {
    wcsncpy(g_app.game.status, text, 255);
    g_app.game.status[255] = L'\0';
    g_app.statusFlash = 1.0f;
}

static RoomState *current_room(void) {
    return &g_app.game.rooms[g_app.game.enfant.room];
}

static ThreatState *get_threat(ThreatKind k) {
    return &g_app.game.threats[k];
}

static ToolState *get_tool(ToolKind k) {
    return &g_app.game.tools[k];
}

static void increase_dread(float a) {
    g_app.game.enfant.dread = clampf(g_app.game.enfant.dread + a, 0.0f, 100.0f);
}

static void increase_warmth(float a) {
    g_app.game.enfant.warmth = clampf(g_app.game.enfant.warmth + a, 0.0f, 100.0f);
}

/* ── Init rooms / threats / tools ───────────────────────────────── */
static void init_rooms(void) {
    g_app.game.rooms[ROOM_COURTYARD] = {
        ROOM_COURTYARD,
        L"Courtyard Warning",
        L"A cracked shared courtyard beneath dead windows and one broken lamp. Children whisper about the Black Car here.",
        {0}, 0.10f, 0.40f, 0, 1
    };
    g_app.game.rooms[ROOM_STAIRWELL] = {
        ROOM_STAIRWELL,
        L"Stairwell Mouth",
        L"The stairwell is longer than the building should allow. A corridor hum waits for a true name.",
        {0}, 0.24f, 0.35f, 0, 0
    };
    g_app.game.rooms[ROOM_CURTAIN_FLAT] = {
        ROOM_CURTAIN_FLAT,
        L"Curtain Flat 12",
        L"A child's room with yellowed drapes, black lining, and a window that watches harder than it should.",
        {0}, 0.42f, 0.20f, 0, 0
    };
    g_app.game.rooms[ROOM_STOVE_NICHE] = {
        ROOM_STOVE_NICHE,
        L"Stove Niche",
        L"A hidden domestic chamber behind old plaster where a household spirit still expects courtesy.",
        {0}, 0.28f, 0.72f, 0, 0
    };
    g_app.game.rooms[ROOM_SERVICE_SHAFT] = {
        ROOM_SERVICE_SHAFT,
        L"Service Shaft",
        L"A steam-warm maintenance vein leading toward the under-road. Someone drags tires where no car should fit.",
        {0}, 0.46f, 0.30f, 0, 0
    };
    g_app.game.rooms[ROOM_BLACK_ROAD_VAULT] = {
        ROOM_BLACK_ROAD_VAULT,
        L"Black Road Vault",
        L"A parking chamber below the district where curtains, headlights, and service markings collapse into one moving law.",
        {0}, 0.66f, 0.10f, 0, 0
    };
}

static void init_threats(void) {
    g_app.game.threats[THREAT_DOMOV_KEEPER]       = {THREAT_DOMOV_KEEPER,       L"Domov Keeper",    0.10f, 1};
    g_app.game.threats[THREAT_KEYHOLE_KIKIMORA]    = {THREAT_KEYHOLE_KIKIMORA,   L"Keyhole Kikimora",0.18f, 1};
    g_app.game.threats[THREAT_BLACK_ROAD_CHAUFFEUR]= {THREAT_BLACK_ROAD_CHAUFFEUR, L"Chauffeur",     0.08f, 0};
    g_app.game.threats[THREAT_CREPULIN_BLOOM]      = {THREAT_CREPULIN_BLOOM,    L"Crepulin Bloom",  0.20f, 1};
}

static void init_tools(void) {
    g_app.game.tools[TOOL_CANDLE_STUB]  = {TOOL_CANDLE_STUB,  L"candle stub",           1};
    g_app.game.tools[TOOL_BOX_CUTTER]   = {TOOL_BOX_CUTTER,   L"box cutter",            1};
    g_app.game.tools[TOOL_KEY_RING]     = {TOOL_KEY_RING,     L"key ring",              1};
    g_app.game.tools[TOOL_IRON_SPOON]   = {TOOL_IRON_SPOON,   L"iron spoon",            1};
    g_app.game.tools[TOOL_THREAD_SPOOL] = {TOOL_THREAD_SPOOL, L"thread spool",          1};
    g_app.game.tools[TOOL_CHALK]        = {TOOL_CHALK,        L"chalk",                 1};
    g_app.game.tools[TOOL_BREAD_SALT]   = {TOOL_BREAD_SALT,   L"bread and salt packet", 1};
    g_app.game.tools[TOOL_HAND_BELL]    = {TOOL_HAND_BELL,    L"hand bell",             1};
    g_app.game.tools[TOOL_GLASS_MARBLE] = {TOOL_GLASS_MARBLE, L"glass marble",          1};
}

static void init_game(void) {
    memset(&g_app.game, 0, sizeof(g_app.game));
    init_rooms();
    init_threats();
    init_tools();
    g_app.game.enfant.room = ROOM_COURTYARD;
    g_app.game.enfant.dread = 12.0f;
    g_app.game.enfant.warmth = 18.0f;
    g_app.game.enfant.health = 100.0f;
    g_app.game.domov_favor = 0.20f;
    g_app.game.babka_favor = 0.00f;
    g_app.game.story_gate = 0;
    g_app.selectedAction = 0;
    g_app.selectedTool = 0;
    set_status(L"A blackout swallows Block Nine. Someone is missing.");
}

/* ── Game actions (ported from C console version) ───────────────── */
static void update_room_rule(RuleKind rule, int respected) {
    current_room()->rule_respected[rule] = respected;
}

static void listen_in_room(void) {
    RoomState *room = current_room();
    if (room->kind == ROOM_STAIRWELL) {
        g_app.game.enfant.abilities |= ABILITY_HOUSE_LISTENING;
        room->hidden_route_revealed = 1;
        increase_dread(4.0f);
        set_status(L"Enfant hears the corridor's true cadence. The stairwell accepts a spoken name.");
        return;
    }
    if (room->kind == ROOM_CURTAIN_FLAT) {
        get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure = clampf(get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure + 0.10f, 0.0f, 1.0f);
        increase_dread(6.0f);
        set_status(L"Something breathes behind the drapes. Listening too long feeds the Kikimora.");
        return;
    }
    if (room->kind == ROOM_SERVICE_SHAFT) {
        get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->active = 1;
        get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure = clampf(get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure + 0.15f, 0.0f, 1.0f);
        set_status(L"A distant engine purr answers through the pipes. The Black Road has found the district.");
        return;
    }
    increase_dread(2.0f);
    set_status(L"The building answers in knocks, steam, and old plaster settling.");
}

static void hide_in_room(void) {
    RoomState *room = current_room();
    float shelter = room->shelter + g_app.game.domov_favor * 0.15f - get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure * 0.10f;
    if (shelter > 0.45f) {
        g_app.game.enfant.hide_streak += 1;
        increase_dread(-8.0f);
        set_status(L"Enfant holds still until the room remembers how to be ordinary.");
    } else {
        g_app.game.enfant.hide_streak = 0;
        increase_dread(9.0f);
        set_status(L"The hiding place is wrong for this threat. Something notices the breath under it.");
    }
}

static void offer_bread_and_salt(void) {
    ToolState *bread_salt = get_tool(TOOL_BREAD_SALT);
    RoomState *room = current_room();
    if (!bread_salt->available) {
        set_status(L"The bread and salt offering has already been used.");
        return;
    }
    bread_salt->available = 0;
    g_app.game.domov_favor = clampf(g_app.game.domov_favor + 0.35f, 0.0f, 1.0f);
    update_room_rule(RULE_BREAD_OFF_FLOOR, 1);
    if (room->kind == ROOM_STOVE_NICHE) {
        g_app.game.enfant.abilities |= ABILITY_STOVE_BLESSING;
        increase_warmth(18.0f);
        set_status(L"The Domov Keeper accepts the offering and blesses the stove path.");
    } else {
        increase_warmth(8.0f);
        set_status(L"The domestic air shifts. Something old and house-bound is less hostile now.");
    }
}

static void cut_curtains(void) {
    ToolState *box_cutter = get_tool(TOOL_BOX_CUTTER);
    if (!box_cutter->available) {
        set_status(L"No cutting edge remains in Enfant's pocket.");
        return;
    }
    if (g_app.game.enfant.room != ROOM_CURTAIN_FLAT) {
        increase_dread(4.0f);
        set_status(L"There is nothing here that should be cut open yet.");
        return;
    }
    g_app.game.enfant.abilities |= ABILITY_CURTAIN_CUT;
    update_room_rule(RULE_CURTAINS_TIED, 1);
    current_room()->hidden_route_revealed = 1;
    get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure = clampf(get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure - 0.12f, 0.0f, 1.0f);
    set_status(L"Enfant cuts the drapes in the right order. The looping room finally breaks open.");
}

static void light_candle(void) {
    ToolState *candle = get_tool(TOOL_CANDLE_STUB);
    if (!candle->available) {
        set_status(L"The candle stub is already spent.");
        return;
    }
    candle->available = 0;
    increase_warmth(24.0f);
    if (g_app.game.enfant.room == ROOM_STOVE_NICHE || g_app.game.enfant.room == ROOM_SERVICE_SHAFT) {
        g_app.game.enfant.abilities |= ABILITY_WARMTH_CARRY;
        update_room_rule(RULE_CROSS_STEAM_WARM, 1);
        set_status(L"Warmth takes hold in Enfant's hands. Steam passages no longer reject the body outright.");
    } else {
        set_status(L"The candle makes the air feel inhabited rather than empty.");
    }
}

static void bargain_or_refuse(void) {
    if (g_app.game.enfant.room == ROOM_SERVICE_SHAFT) {
        if ((g_app.game.enfant.abilities & ABILITY_WARMTH_CARRY) == 0u) {
            increase_dread(10.0f);
            set_status(L"Babka Kuroles laughs from the steam. Cold children do not pass under roads alive.");
            return;
        }
        g_app.game.babka_favor = clampf(g_app.game.babka_favor + 0.30f, 0.0f, 1.0f);
        g_app.game.enfant.abilities |= ABILITY_BLACK_ROAD_REFUSAL;
        set_status(L"Babka Kuroles trades a refusal phrase for one future favor. Enfant can now deny the Black Road's invitation.");
        return;
    }
    if (g_app.game.enfant.room == ROOM_BLACK_ROAD_VAULT) {
        if ((g_app.game.enfant.abilities & ABILITY_BLACK_ROAD_REFUSAL) == 0u) {
            increase_dread(18.0f);
            set_status(L"The Chauffeur hears fear instead of refusal. The engine comes closer.");
            return;
        }
        g_app.game.enfant.children_rescued = 1;
        get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure = 0.0f;
        set_status(L"Enfant speaks the refusal. Headlights dim, curtains slacken, and the road releases one stolen child-route.");
        return;
    }
    set_status(L"No bargain presents itself here.");
}

static int can_move_forward(void) {
    switch (g_app.game.enfant.room) {
        case ROOM_COURTYARD:    return 1;
        case ROOM_STAIRWELL:    return (g_app.game.enfant.abilities & ABILITY_HOUSE_LISTENING) != 0u;
        case ROOM_CURTAIN_FLAT: return (g_app.game.enfant.abilities & ABILITY_CURTAIN_CUT) != 0u;
        case ROOM_STOVE_NICHE:  return (g_app.game.enfant.abilities & ABILITY_STOVE_BLESSING) != 0u;
        case ROOM_SERVICE_SHAFT:return (g_app.game.enfant.abilities & ABILITY_BLACK_ROAD_REFUSAL) != 0u;
        default:                return 0;
    }
}

static void move_forward(void) {
    if (!can_move_forward()) {
        increase_dread(5.0f);
        set_status(L"The next threshold refuses Enfant. A room rule or bargain is still unresolved.");
        return;
    }
    if (g_app.game.enfant.room + 1 >= CREP_ROOM_COUNT) {
        set_status(L"There is no further room beyond the current threshold.");
        return;
    }
    g_app.game.enfant.room = (RoomKind)(g_app.game.enfant.room + 1);
    current_room()->visited = 1;
    increase_dread(3.0f + current_room()->corruption * 8.0f);
    if (g_app.game.enfant.room == ROOM_BLACK_ROAD_VAULT) {
        get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->active = 1;
        get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure = 0.72f;
        set_status(L"Enfant reaches the Black Road Vault. The Chauffeur is already waiting.");
    } else {
        set_status(current_room()->description);
    }
}

static void update_world(void) {
    ThreatState *kikimora  = get_threat(THREAT_KEYHOLE_KIKIMORA);
    ThreatState *chauffeur = get_threat(THREAT_BLACK_ROAD_CHAUFFEUR);
    ThreatState *bloom     = get_threat(THREAT_CREPULIN_BLOOM);

    g_app.game.turns += 1;
    increase_dread(current_room()->corruption * 1.8f);
    increase_warmth(-1.5f);

    if (g_app.game.enfant.room == ROOM_CURTAIN_FLAT && (g_app.game.enfant.abilities & ABILITY_CURTAIN_CUT) == 0u) {
        kikimora->pressure = clampf(kikimora->pressure + 0.08f, 0.0f, 1.0f);
    }
    if (g_app.game.enfant.room == ROOM_SERVICE_SHAFT || g_app.game.enfant.room == ROOM_BLACK_ROAD_VAULT) {
        chauffeur->active = 1;
        chauffeur->pressure = clampf(chauffeur->pressure + 0.05f, 0.0f, 1.0f);
    }
    bloom->pressure = clampf(bloom->pressure + current_room()->corruption * 0.03f, 0.0f, 1.0f);

    if (g_app.game.enfant.warmth < 5.0f && current_room()->kind == ROOM_SERVICE_SHAFT) {
        increase_dread(6.0f);
        set_status(L"Cold steam bites through Enfant's clothes. The shaft wants a warmer body than this.");
    }
}

static void execute_action(int action) {
    switch (action) {
        case 0: listen_in_room();      break;
        case 1: hide_in_room();        break;
        case 2: offer_bread_and_salt();break;
        case 3: cut_curtains();        break;
        case 4: light_candle();        break;
        case 5: bargain_or_refuse();   break;
        case 6: move_forward();        break;
        case 7: /* status — no-op, just refreshes display */ return;
    }
    update_world();
}

/* ── Path / asset helpers ───────────────────────────────────────── */
static std::wstring joinPath(const std::wstring &a, const std::wstring &b) {
    if (a.empty()) return b;
    if (a.back() == L'\\') return a + b;
    return a + L"\\" + b;
}

static bool directoryExists(const std::wstring &path) {
    DWORD attr = GetFileAttributesW(path.c_str());
    return attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY) != 0;
}

static std::vector<std::wstring> listPngFiles(const std::wstring &directory) {
    std::vector<std::wstring> files;
    std::wstring pattern = joinPath(directory, L"*.png");
    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW(pattern.c_str(), &fd);
    if (h == INVALID_HANDLE_VALUE) return files;
    do {
        if ((fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) == 0)
            files.push_back(joinPath(directory, fd.cFileName));
    } while (FindNextFileW(h, &fd));
    FindClose(h);
    std::sort(files.begin(), files.end());
    return files;
}

static Image *loadImage(const std::wstring &path) {
    Image *img = new Image(path.c_str());
    Status st = img->GetLastStatus();
    if (st != Ok) {
        // Debug: log the failed load
        FILE *logf = _wfopen(L"asset_debug.log", L"a");
        if (logf) {
            fwprintf(logf, L"  LOAD FAIL: %ls  status=%d\n", path.c_str(), (int)st);
            wchar_t abs[MAX_PATH];
            GetFullPathNameW(path.c_str(), MAX_PATH, abs, NULL);
            fwprintf(logf, L"    abs: %ls  exists=%d\n", abs,
                     GetFileAttributesW(abs) != INVALID_FILE_ATTRIBUTES);
            fclose(logf);
        }
        delete img; return nullptr;
    }
    return img;
}

static void loadAssetFolder(const std::wstring &folder, std::vector<AssetImage> &out) {
    auto found = listPngFiles(folder);
    // Debug: log what listPngFiles returned
    FILE *logf = _wfopen(L"asset_debug.log", L"a");
    if (logf) { fwprintf(logf, L"loadAssetFolder(\"%ls\") => %d files\n", folder.c_str(), (int)found.size()); fclose(logf); }
    for (auto &f : found) {
        Image *img = loadImage(f);
        if (img) out.push_back({f, img});
    }
}

static void freeAssetList(std::vector<AssetImage> &list) {
    for (auto &a : list) { delete a.image; a.image = nullptr; }
    list.clear();
}

static void freeAssets(CrepAssets &assets) {
    freeAssetList(assets.rooms);
    freeAssetList(assets.enfant);
    freeAssetList(assets.threats);
    freeAssetList(assets.npcs);
    freeAssetList(assets.tools);
    freeAssetList(assets.fx);
    freeAssetList(assets.ui);
    freeAssetList(assets.screens);
}

static int totalAssetsLoaded(const CrepAssets &a) {
    return (int)(a.rooms.size() + a.enfant.size() + a.threats.size() +
                 a.npcs.size() + a.tools.size() + a.fx.size() +
                 a.ui.size() + a.screens.size());
}

static void discoverAndLoadAssets(CrepAssets &assets) {
    const wchar_t *roots[] = {
        L"assets",
        L"crepulinenfant\\assets",
        L"..\\crepulinenfant\\assets",
        L"..\\assets",
    };
    assets.root.clear();
    for (auto &r : roots) {
        if (directoryExists(r)) { assets.root = r; break; }
    }
    if (assets.root.empty()) return;

    loadAssetFolder(joinPath(assets.root, L"rooms"),   assets.rooms);
    loadAssetFolder(joinPath(assets.root, L"enfant"),  assets.enfant);
    loadAssetFolder(joinPath(assets.root, L"threats"), assets.threats);
    loadAssetFolder(joinPath(assets.root, L"npcs"),    assets.npcs);
    loadAssetFolder(joinPath(assets.root, L"tools"),   assets.tools);
    loadAssetFolder(joinPath(assets.root, L"fx"),      assets.fx);
    loadAssetFolder(joinPath(assets.root, L"ui"),      assets.ui);
    loadAssetFolder(joinPath(assets.root, L"screens"), assets.screens);
}

/* ── XInput ─────────────────────────────────────────────────────── */
static float normalizeAxis(SHORT value, SHORT deadzone) {
    float n = 0.0f;
    if (value > deadzone) n = (float)(value - deadzone) / (32767.0f - (float)deadzone);
    else if (value < -deadzone) n = (float)(value + deadzone) / (32768.0f - (float)deadzone);
    return std::max(-1.0f, std::min(1.0f, n));
}

static float normalizeTrigger(BYTE value) {
    const float threshold = 30.0f;
    if ((float)value <= threshold) return 0.0f;
    return ((float)value - threshold) / (255.0f - threshold);
}

static void loadXInput(void) {
    const wchar_t *dlls[] = {L"xinput1_4.dll", L"xinput1_3.dll", L"xinput9_1_0.dll"};
    g_app.xinputModule = nullptr;
    g_app.xinputGetState = nullptr;
    for (auto &dll : dlls) {
        HMODULE mod = LoadLibraryW(dll);
        if (mod) {
            FARPROC proc = GetProcAddress(mod, "XInputGetState");
            if (proc) {
                g_app.xinputModule = mod;
                g_app.xinputGetState = (XInputGetStateProc)proc;
                return;
            }
            FreeLibrary(mod);
        }
    }
}

static void pollController(void) {
    ControllerState &c = g_app.controller;
    c.previousButtons = c.buttons;
    c.prevLsUp = c.lsUp;   c.prevLsDown = c.lsDown;
    c.prevLsLeft = c.lsLeft; c.prevLsRight = c.lsRight;

    if (!g_app.xinputGetState) {
        c.connected = false; c.buttons = 0; return;
    }

    XINPUT_STATE xs = {};
    DWORD result = g_app.xinputGetState(0, &xs);
    if (result != ERROR_SUCCESS) {
        c.connected = false; c.buttons = 0;
        c.lx = c.ly = c.rx = c.ry = c.lt = c.rt = 0.0f;
        c.lsUp = c.lsDown = c.lsLeft = c.lsRight = false;
        return;
    }
    c.connected = true;
    c.buttons = xs.Gamepad.wButtons;
    c.lx = normalizeAxis(xs.Gamepad.sThumbLX, XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE);
    c.ly = normalizeAxis(xs.Gamepad.sThumbLY, XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE);
    c.rx = normalizeAxis(xs.Gamepad.sThumbRX, XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE);
    c.ry = normalizeAxis(xs.Gamepad.sThumbRY, XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE);
    c.lt = normalizeTrigger(xs.Gamepad.bLeftTrigger);
    c.rt = normalizeTrigger(xs.Gamepad.bRightTrigger);
    c.lsUp    = c.ly >  0.55f;
    c.lsDown  = c.ly < -0.55f;
    c.lsLeft  = c.lx < -0.55f;
    c.lsRight = c.lx >  0.55f;
}

static bool padPressed(WORD mask) {
    auto &c = g_app.controller;
    return (c.buttons & mask) != 0 && (c.previousButtons & mask) == 0;
}

static bool keyPressed(int vk) {
    return vk >= 0 && vk < 256 && g_app.keyPressed[vk];
}

/* ── Drawing helpers ────────────────────────────────────────────── */
static void drawTextLine(HDC hdc, int x, int y, COLORREF colour, const wchar_t *text) {
    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, colour);
    TextOutW(hdc, x, y, text, (int)wcslen(text));
}

static void fillRect(HDC hdc, int l, int t, int r, int b, COLORREF colour) {
    RECT rc = {l, t, r, b};
    HBRUSH brush = CreateSolidBrush(colour);
    FillRect(hdc, &rc, brush);
    DeleteObject(brush);
}

static void drawGauge(HDC hdc, int x, int y, int w, int h, float ratio, COLORREF fill, const wchar_t *label) {
    ratio = std::max(0.0f, std::min(1.0f, ratio));
    fillRect(hdc, x, y, x + w, y + h, COL_GAUGE_BG);
    fillRect(hdc, x, y, x + (int)(ratio * (float)w), y + h, fill);
    RECT border = {x, y, x + w, y + h};
    FrameRect(hdc, &border, (HBRUSH)GetStockObject(WHITE_BRUSH));
    wchar_t buf[128];
    swprintf(buf, 128, L"%ls: %d%%", label, (int)(ratio * 100.0f));
    drawTextLine(hdc, x + 6, y + 2, COL_CHALK_WHITE, buf);
}

static void drawImageAlpha(Graphics &g, Image *img, int x, int y, int w, int h, float alpha) {
    if (!img) return;
    alpha = std::max(0.0f, std::min(1.0f, alpha));
    ColorMatrix cm = {
        1,0,0,0,0, 0,1,0,0,0, 0,0,1,0,0, 0,0,0,alpha,0, 0,0,0,0,1,
    };
    ImageAttributes attrs;
    attrs.SetColorMatrix(&cm, ColorMatrixFlagsDefault, ColorAdjustTypeBitmap);
    Rect dest(x, y, w, h);
    g.DrawImage(img, dest, 0, 0, img->GetWidth(), img->GetHeight(), UnitPixel, &attrs);
}

static void drawAsset(Graphics &g, const std::vector<AssetImage> &list, int idx, int x, int y, int w, int h, float alpha) {
    if (list.empty()) return;
    int safe = idx % (int)list.size();
    if (safe < 0) safe += (int)list.size();
    drawImageAlpha(g, list[safe].image, x, y, w, h, alpha);
}

/* ── Rendering ──────────────────────────────────────────────────── */
static void renderFrame(HDC hdc, RECT clientRect) {
    Graphics graphics(hdc);
    graphics.SetInterpolationMode(InterpolationModeHighQualityBicubic);

    int width  = clientRect.right  - clientRect.left;
    int height = clientRect.bottom - clientRect.top;

    fillRect(hdc, 0, 0, width, height, COL_BG_DEEP);

    /* ── TITLE SCREEN ─────────────────────────────────────────── */
    if (g_app.screen == SCREEN_TITLE) {
        // title background
        drawAsset(graphics, g_app.assets.screens, 2, 0, 0, width, height, 0.85f); // title_screen.png (sorted: ending, game_over, title)
        fillRect(hdc, 0, 0, width, height, RGB(0, 0, 0)); // darken
        drawAsset(graphics, g_app.assets.screens, 2, 0, 0, width, height, 0.55f);

        drawTextLine(hdc, width / 2 - 220, height / 2 - 60, COL_NICOTINE,
                     L"Crepulin: Enfant; .xxDetnDimension");
        drawTextLine(hdc, width / 2 - 180, height / 2, COL_CHALK_WHITE,
                     L"Press ENTER / Xbox A to begin");
        drawTextLine(hdc, width / 2 - 140, height / 2 + 30, COL_DEAD_TEAL,
                     L"A child navigates Block Nine.");
        wchar_t assetLine[128];
        swprintf(assetLine, 128, L"Assets loaded: %d", totalAssetsLoaded(g_app.assets));
        drawTextLine(hdc, 20, height - 30, COL_STAIRWELL, assetLine);
        if (g_app.controller.connected)
            drawTextLine(hdc, 20, height - 50, COL_SODIUM, L"Xbox Controller connected");
        return;
    }

    /* ── ENDING SCREEN ────────────────────────────────────────── */
    if (g_app.screen == SCREEN_ENDING) {
        drawAsset(graphics, g_app.assets.screens, 0, 0, 0, width, height, 0.80f); // ending_screen.png
        drawTextLine(hdc, width / 2 - 260, height / 2 - 40, COL_WARM_ORANGE,
                     L"Enfant pulls one child-route back from the Black Road.");
        drawTextLine(hdc, width / 2 - 260, height / 2,      COL_CHALK_WHITE,
                     L"The district is not healed, but it is finally named honestly.");
        drawTextLine(hdc, width / 2 - 140, height / 2 + 50, COL_DEAD_TEAL,
                     L"Press ENTER / Xbox A to restart");
        return;
    }

    /* ── GAME OVER SCREEN ─────────────────────────────────────── */
    if (g_app.screen == SCREEN_GAME_OVER) {
        drawAsset(graphics, g_app.assets.screens, 1, 0, 0, width, height, 0.80f); // game_over.png
        drawTextLine(hdc, width / 2 - 260, height / 2 - 20, COL_RUST_RED,
                     L"Dread overwhelms Enfant. The DetnDimension closes like a throat.");
        drawTextLine(hdc, width / 2 - 140, height / 2 + 30, COL_DEAD_TEAL,
                     L"Press ENTER / Xbox A to restart");
        return;
    }

    /* ── PLAY SCREEN ──────────────────────────────────────────── */
    int panelL = 16, panelT = 16;
    int panelR = width - 16, panelB = height - 16;

    // Room background (full screen)
    int roomIdx = (int)g_app.game.enfant.room;
    drawAsset(graphics, g_app.assets.rooms, roomIdx, 0, 0, width, height, 0.85f);

    // Dread overlay (bruised violet darkening based on dread level)
    float dreadRatio = g_app.game.enfant.dread / 100.0f;
    drawAsset(graphics, g_app.assets.fx, 1, 0, 0, width, height, dreadRatio * 0.45f); // dread_overlay

    // Warmth glow (warm overlay based on warmth)
    float warmthRatio = g_app.game.enfant.warmth / 100.0f;
    drawAsset(graphics, g_app.assets.fx, 3, 0, 0, width, height, warmthRatio * 0.25f); // warmth_glow

    // Crepulin stain overlay based on bloom pressure
    float bloomP = get_threat(THREAT_CREPULIN_BLOOM)->pressure;
    drawAsset(graphics, g_app.assets.fx, 2, 0, 0, width, height, bloomP * 0.35f); // crepulin_stain

    // Black Road headlights in service shaft / vault
    if (g_app.game.enfant.room >= ROOM_SERVICE_SHAFT && get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->active) {
        float chauffP = get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure;
        drawAsset(graphics, g_app.assets.fx, 0, 0, 0, width, height, chauffP * 0.5f); // headlights
    }

    // ── Enfant character (centre-left) ───────────────────────
    int enfantX = panelL + 50;
    int enfantY = height / 2 - 180;
    int enfantIdx = 0; // idle
    if (g_app.game.enfant.dread > 70.0f)       enfantIdx = 2; // fear
    else if (g_app.game.enfant.hide_streak > 0) enfantIdx = 3; // hide
    drawAsset(graphics, g_app.assets.enfant, enfantIdx, enfantX, enfantY, 260, 260, 1.0f);

    // ── Active threat portrait (centre-right) ────────────────
    int threatIdx = -1;
    float maxThreat = 0.0f;
    for (int i = 0; i < CREP_THREAT_COUNT; ++i) {
        if (g_app.game.threats[i].active && g_app.game.threats[i].pressure > maxThreat) {
            maxThreat = g_app.game.threats[i].pressure;
            threatIdx = i;
        }
    }
    if (threatIdx >= 0) {
        int tx = width - 320, ty = height / 2 - 200;
        drawAsset(graphics, g_app.assets.threats, threatIdx, tx, ty, 280, 280, 0.6f + maxThreat * 0.4f);
    }

    // ── NPC portrait (Babka in service shaft, Bird in vault) ─
    if (g_app.game.enfant.room == ROOM_SERVICE_SHAFT && !g_app.assets.npcs.empty()) {
        drawAsset(graphics, g_app.assets.npcs, 0, width / 2 - 120, height / 2 - 140, 240, 240, 0.75f); // babka
    }
    if (g_app.game.enfant.room == ROOM_BLACK_ROAD_VAULT && g_app.assets.npcs.size() > 1) {
        drawAsset(graphics, g_app.assets.npcs, 1, width - 200, 20, 160, 160, 0.6f); // bird
    }

    // ── Semi-transparent HUD panels ──────────────────────────
    // Top bar: room info + gauges (semi-transparent overlay via alpha blend)
    {
        HDC tmpDC = CreateCompatibleDC(hdc);
        HBITMAP tmpBM = CreateCompatibleBitmap(hdc, panelR - panelL, 94);
        SelectObject(tmpDC, tmpBM);
        RECT tmpR = {0, 0, panelR - panelL, 94};
        HBRUSH br = CreateSolidBrush(RGB(10, 12, 16));
        FillRect(tmpDC, &tmpR, br);
        DeleteObject(br);
        BLENDFUNCTION bf = {AC_SRC_OVER, 0, 180, 0};
        AlphaBlend(hdc, panelL, panelT, panelR - panelL, 94, tmpDC, 0, 0, panelR - panelL, 94, bf);
        DeleteObject(tmpBM);
        DeleteDC(tmpDC);
    }
    SetBkMode(hdc, TRANSPARENT);

    wchar_t line[512];
    swprintf(line, 512, L"Room %d/6: %ls", roomIdx + 1, current_room()->name);
    drawTextLine(hdc, panelL + 10, panelT + 4, COL_NICOTINE, line);
    drawTextLine(hdc, panelL + 10, panelT + 22, COL_CHALK_WHITE, current_room()->description);

    // Gauges row
    int gy = panelT + 48;
    drawGauge(hdc, panelL + 10,  gy, 180, 18, dreadRatio,  COL_BRUISED,     L"Dread");
    drawGauge(hdc, panelL + 200, gy, 180, 18, warmthRatio, COL_WARM_ORANGE, L"Warmth");
    drawGauge(hdc, panelL + 390, gy, 180, 18, g_app.game.enfant.health / 100.0f, COL_RUST_RED, L"Health");

    swprintf(line, 512, L"Domov: %.0f%%  Babka: %.0f%%  Turn: %d",
             g_app.game.domov_favor * 100.0f, g_app.game.babka_favor * 100.0f, g_app.game.turns);
    drawTextLine(hdc, panelL + 590, gy + 2, COL_DEAD_TEAL, line);

    // Gauges for UI assets (small icons)
    if (!g_app.assets.ui.empty()) {
        drawAsset(graphics, g_app.assets.ui, 0, panelR - 210, panelT + 8, 60, 60, 0.70f);  // dread gauge icon
        if (g_app.assets.ui.size() > 1)
            drawAsset(graphics, g_app.assets.ui, 2, panelR - 140, panelT + 8, 60, 60, 0.70f); // warmth gauge icon
        if (g_app.assets.ui.size() > 2)
            drawAsset(graphics, g_app.assets.ui, 1, panelR - 70, panelT + 8, 60, 60, 0.70f);  // health gauge icon
    }

    // ── Threat pressure bar ──────────────────────────────────
    int threatBarY = panelT + 74;
    swprintf(line, 512, L"Threats: Domov %.0f%% | Kikimora %.0f%% | Chauffeur %.0f%% | Bloom %.0f%%",
             get_threat(THREAT_DOMOV_KEEPER)->pressure * 100.0f,
             get_threat(THREAT_KEYHOLE_KIKIMORA)->pressure * 100.0f,
             get_threat(THREAT_BLACK_ROAD_CHAUFFEUR)->pressure * 100.0f,
             get_threat(THREAT_CREPULIN_BLOOM)->pressure * 100.0f);
    drawTextLine(hdc, panelL + 10, threatBarY, COL_BRUISED, line);

    // ── Bottom panel: status + action menu + tools ───────────
    int botH = 210;
    int botTop = height - botH - 16;
    {
        int bw = panelR - panelL, bh = panelB - botTop;
        HDC tmpDC = CreateCompatibleDC(hdc);
        HBITMAP tmpBM = CreateCompatibleBitmap(hdc, bw, bh);
        SelectObject(tmpDC, tmpBM);
        RECT tmpR = {0, 0, bw, bh};
        HBRUSH br = CreateSolidBrush(RGB(10, 12, 16));
        FillRect(tmpDC, &tmpR, br);
        DeleteObject(br);
        BLENDFUNCTION bf = {AC_SRC_OVER, 0, 180, 0};
        AlphaBlend(hdc, panelL, botTop, bw, bh, tmpDC, 0, 0, bw, bh, bf);
        DeleteObject(tmpBM);
        DeleteDC(tmpDC);
    }

    // Status line with flash
    COLORREF statusCol = COL_CHALK_WHITE;
    if (g_app.statusFlash > 0.5f) statusCol = COL_SODIUM;
    drawTextLine(hdc, panelL + 14, botTop + 6, statusCol, g_app.game.status);

    // Abilities line
    swprintf(line, 512, L"Abilities: %ls%ls%ls%ls%ls",
             (g_app.game.enfant.abilities & ABILITY_HOUSE_LISTENING)    ? L"[Listening] " : L"",
             (g_app.game.enfant.abilities & ABILITY_CURTAIN_CUT)        ? L"[Curtain Cut] " : L"",
             (g_app.game.enfant.abilities & ABILITY_STOVE_BLESSING)     ? L"[Stove Blessing] " : L"",
             (g_app.game.enfant.abilities & ABILITY_WARMTH_CARRY)       ? L"[Warmth Carry] " : L"",
             (g_app.game.enfant.abilities & ABILITY_BLACK_ROAD_REFUSAL) ? L"[Road Refusal] " : L"");
    drawTextLine(hdc, panelL + 14, botTop + 28, COL_DEAD_TEAL, line);

    // Action menu (left side)
    int menuX = panelL + 14;
    int menuY = botTop + 52;
    drawTextLine(hdc, menuX, menuY - 2, COL_NICOTINE, L"Actions (DPad/Arrows + A/Enter):");
    for (int i = 0; i < ACTION_COUNT; ++i) {
        bool selected = (i == g_app.selectedAction);
        COLORREF ac = selected ? COL_SODIUM : COL_CHALK_WHITE;
        wchar_t marker[64];
        swprintf(marker, 64, L"%ls %ls", selected ? L"\x25B6" : L"  ", k_action_names[i]);
        drawTextLine(hdc, menuX, menuY + 18 + i * 18, ac, marker);
    }

    // Tools panel (right side)
    int toolX = panelL + 320;
    int toolY = botTop + 52;
    drawTextLine(hdc, toolX, toolY - 2, COL_NICOTINE, L"Inventory:");
    for (int i = 0; i < CREP_TOOL_COUNT; ++i) {
        COLORREF tc = g_app.game.tools[i].available ? COL_CHALK_WHITE : RGB(80, 80, 80);
        wchar_t toolLine[128];
        swprintf(toolLine, 128, L"%ls %ls", g_app.game.tools[i].available ? L"\x2022" : L"\x2013", g_app.game.tools[i].name);
        drawTextLine(hdc, toolX, toolY + 18 + i * 17, tc, toolLine);

        // Tool icon next to name
        if (g_app.game.tools[i].available && !g_app.assets.tools.empty()) {
            drawAsset(graphics, g_app.assets.tools, i, toolX + 200, toolY + 14 + i * 17, 20, 20, 0.9f);
        }
    }

    // Room rules panel (far right)
    int ruleX = panelL + 580;
    int ruleY = botTop + 52;
    drawTextLine(hdc, ruleX, ruleY - 2, COL_NICOTINE, L"House Rules:");
    for (int i = 0; i < RULE_COUNT; ++i) {
        bool respected = current_room()->rule_respected[i] != 0;
        COLORREF rc = respected ? COL_STAIRWELL : RGB(130, 60, 60);
        wchar_t ruleLine[256];
        swprintf(ruleLine, 256, L"[%ls] %ls", respected ? L"x" : L" ", k_rule_names[i]);
        drawTextLine(hdc, ruleX, ruleY + 18 + i * 17, rc, ruleLine);
    }

    // Controls help (bottom-right)
    int helpX = panelR - 340;
    int helpY = panelB - 55;
    drawTextLine(hdc, helpX, helpY,      COL_STAIRWELL, L"Up/Down or DPad: select action");
    drawTextLine(hdc, helpX, helpY + 16, COL_STAIRWELL, L"Enter/A: execute | ESC/Start: title");
    if (g_app.controller.connected)
        drawTextLine(hdc, helpX, helpY + 32, COL_SODIUM, L"\x25C9 Xbox Controller active");
}

/* ── Gameplay update (called on timer) ──────────────────────────── */
static void updateGameplay(float dt) {
    pollController();
    auto &pad = g_app.controller;

    // Decay status flash
    if (g_app.statusFlash > 0.0f) g_app.statusFlash -= dt * 2.0f;
    g_app.animTimer += dt;

    /* ── TITLE ────────────────────────────────────────────────── */
    if (g_app.screen == SCREEN_TITLE) {
        if (keyPressed(VK_RETURN) || keyPressed(VK_SPACE) || padPressed(XINPUT_GAMEPAD_A)) {
            init_game();
            g_app.screen = SCREEN_PLAY;
        }
    }

    /* ── ENDING / GAME OVER ───────────────────────────────────── */
    else if (g_app.screen == SCREEN_ENDING || g_app.screen == SCREEN_GAME_OVER) {
        if (keyPressed(VK_RETURN) || keyPressed(VK_SPACE) || padPressed(XINPUT_GAMEPAD_A)) {
            g_app.screen = SCREEN_TITLE;
        }
    }

    /* ── PLAY ─────────────────────────────────────────────────── */
    else if (g_app.screen == SCREEN_PLAY) {
        // Check end conditions
        if (g_app.game.enfant.children_rescued > 0) {
            g_app.screen = SCREEN_ENDING;
        } else if (g_app.game.enfant.dread >= 100.0f) {
            g_app.screen = SCREEN_GAME_OVER;
        } else {
            // ESC / Start → return to title
            if (keyPressed(VK_ESCAPE) || padPressed(XINPUT_GAMEPAD_START)) {
                g_app.screen = SCREEN_TITLE;
            }

            // Navigate action menu
            bool up   = keyPressed(VK_UP)   || padPressed(XINPUT_GAMEPAD_DPAD_UP)   || (pad.lsUp && !pad.prevLsUp);
            bool down = keyPressed(VK_DOWN) || padPressed(XINPUT_GAMEPAD_DPAD_DOWN) || (pad.lsDown && !pad.prevLsDown);

            if (up)   g_app.selectedAction = (g_app.selectedAction - 1 + ACTION_COUNT) % ACTION_COUNT;
            if (down) g_app.selectedAction = (g_app.selectedAction + 1) % ACTION_COUNT;

            // Execute action
            if (keyPressed(VK_RETURN) || keyPressed(VK_SPACE) || padPressed(XINPUT_GAMEPAD_A)) {
                execute_action(g_app.selectedAction);
            }

            // Quick keys (keyboard shortcuts matching original console commands)
            if (keyPressed('L')) { execute_action(0); }
            if (keyPressed('H')) { execute_action(1); }
            if (keyPressed('O')) { execute_action(2); }
            if (keyPressed('C')) { execute_action(3); }
            if (keyPressed('W')) { execute_action(4); }
            if (keyPressed('B')) { execute_action(5); }
            if (keyPressed('M')) { execute_action(6); }
            if (keyPressed('S')) { execute_action(7); }

            // Controller face button shortcuts
            if (padPressed(XINPUT_GAMEPAD_X))                execute_action(0); // Listen
            if (padPressed(XINPUT_GAMEPAD_Y))                execute_action(1); // Hide
            if (padPressed(XINPUT_GAMEPAD_B))                execute_action(5); // Bargain/Refuse
            if (padPressed(XINPUT_GAMEPAD_RIGHT_SHOULDER))   execute_action(6); // Move forward
            if (padPressed(XINPUT_GAMEPAD_LEFT_SHOULDER))     execute_action(4); // Light candle
        }
    }

    memset(g_app.keyPressed, 0, sizeof(g_app.keyPressed));
    memset(g_app.keyReleased, 0, sizeof(g_app.keyReleased));
}

/* ── Window proc ────────────────────────────────────────────────── */
static LRESULT CALLBACK windowProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
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
                if (!g_app.keyDown[key]) g_app.keyPressed[key] = true;
                g_app.keyDown[key] = true;
            }
            return 0;
        }
        case WM_KEYUP: {
            int key = (int)wParam;
            if (key >= 0 && key < 256) {
                g_app.keyDown[key] = false;
                g_app.keyReleased[key] = true;
            }
            return 0;
        }
        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hwnd, &ps);
            RECT cr;
            GetClientRect(hwnd, &cr);

            // Double-buffer
            HDC memDC = CreateCompatibleDC(hdc);
            HBITMAP memBM = CreateCompatibleBitmap(hdc, cr.right, cr.bottom);
            HBITMAP oldBM = (HBITMAP)SelectObject(memDC, memBM);

            renderFrame(memDC, cr);

            BitBlt(hdc, 0, 0, cr.right, cr.bottom, memDC, 0, 0, SRCCOPY);
            SelectObject(memDC, oldBM);
            DeleteObject(memBM);
            DeleteDC(memDC);

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

/* ── Entry point ────────────────────────────────────────────────── */
int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand) {
    // g_app is already zero-initialized as a namespace-scope static;
    // do NOT ZeroMemory it — that would corrupt std::vector/std::wstring internals.
    g_app.screen = SCREEN_TITLE;
    memset(g_app.keyDown, 0, sizeof(g_app.keyDown));
    memset(g_app.keyPressed, 0, sizeof(g_app.keyPressed));
    memset(g_app.keyReleased, 0, sizeof(g_app.keyReleased));

    GdiplusStartupInput gdiplusInput;
    Status gdipStatus = GdiplusStartup(&g_app.gdiplusToken, &gdiplusInput, NULL);
    // Log GDI+ init result
    {
        _wremove(L"asset_debug.log"); // fresh start
        FILE *logf = _wfopen(L"asset_debug.log", L"w");
        if (logf) { fwprintf(logf, L"GdiplusStartup status=%d\n", (int)gdipStatus); fclose(logf); }
    }

    const wchar_t *className = L"CrepulinEnfantWindowClass";
    WNDCLASSEXW wc = {};
    wc.cbSize        = sizeof(wc);
    wc.style         = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc   = windowProc;
    wc.hInstance     = instance;
    wc.hCursor       = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.lpszClassName = className;

    if (!RegisterClassExW(&wc)) return 1;

    HWND window = CreateWindowExW(0, className,
        L"Crepulin: Enfant; .xxDetnDimension",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 1366, 820,
        NULL, NULL, instance, NULL);
    if (!window) return 1;

    g_app.window = window;

    // Set CWD to exe directory so relative asset paths resolve correctly
    {
        wchar_t exePath[MAX_PATH];
        GetModuleFileNameW(NULL, exePath, MAX_PATH);
        wchar_t *lastSlash = wcsrchr(exePath, L'\\');
        if (lastSlash) { *lastSlash = L'\0'; SetCurrentDirectoryW(exePath); }
    }

    discoverAndLoadAssets(g_app.assets);
    loadXInput();

    // Diagnostic log — remove after debugging
    {
        wchar_t cwd[MAX_PATH]; GetCurrentDirectoryW(MAX_PATH, cwd);
        FILE *logf = _wfopen(L"asset_debug.log", L"a");
        if (logf) {
            fwprintf(logf, L"\n=== POST LOAD ===\n");
            fwprintf(logf, L"CWD: %ls\n", cwd);
            fwprintf(logf, L"assets.root: %ls\n", g_app.assets.root.c_str());
            fwprintf(logf, L"total: %d\n", totalAssetsLoaded(g_app.assets));

            // Probe each subfolder
            const wchar_t *subs[] = {L"rooms",L"enfant",L"threats",L"npcs",L"tools",L"fx",L"ui",L"screens"};
            for (auto &s : subs) {
                std::wstring subDir = joinPath(g_app.assets.root, s);
                bool exists = directoryExists(subDir);
                fwprintf(logf, L"\n[%ls] dir exists=%d  path=\"%ls\"\n", s, exists, subDir.c_str());
                if (exists) {
                    std::wstring pat = joinPath(subDir, L"*.png");
                    fwprintf(logf, L"  pattern=\"%ls\"\n", pat.c_str());
                    WIN32_FIND_DATAW fd;
                    HANDLE h = FindFirstFileW(pat.c_str(), &fd);
                    if (h == INVALID_HANDLE_VALUE) {
                        fwprintf(logf, L"  FindFirstFile FAILED err=%lu\n", GetLastError());
                    } else {
                        int count = 0;
                        do {
                            fwprintf(logf, L"  found: %ls\n", fd.cFileName);
                            ++count;
                        } while (FindNextFileW(h, &fd));
                        FindClose(h);
                        fwprintf(logf, L"  total found: %d\n", count);
                    }
                }
            }

            // Also check: are the sizes after loadAssetFolder calls still 0?
            fwprintf(logf, L"\nrooms=%d enfant=%d threats=%d npcs=%d tools=%d fx=%d ui=%d screens=%d\n",
                (int)g_app.assets.rooms.size(), (int)g_app.assets.enfant.size(),
                (int)g_app.assets.threats.size(), (int)g_app.assets.npcs.size(),
                (int)g_app.assets.tools.size(), (int)g_app.assets.fx.size(),
                (int)g_app.assets.ui.size(), (int)g_app.assets.screens.size());
            fclose(logf);
        }
    }

    ShowWindow(window, showCommand);
    UpdateWindow(window);

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    freeAssets(g_app.assets);
    if (g_app.xinputModule) { FreeLibrary(g_app.xinputModule); g_app.xinputModule = nullptr; }
    GdiplusShutdown(g_app.gdiplusToken);
    return (int)msg.wParam;
}
