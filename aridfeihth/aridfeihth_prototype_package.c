#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define ARIDFEIHTH_ARRAY_COUNT(array) (sizeof(array) / sizeof((array)[0]))

#define ARIDFEIHTH_ROOM_FLAG_SAFE         (1u << 0)
#define ARIDFEIHTH_ROOM_FLAG_HUB          (1u << 1)
#define ARIDFEIHTH_ROOM_FLAG_INTERACTABLE (1u << 2)
#define ARIDFEIHTH_ROOM_FLAG_PUZZLE       (1u << 3)
#define ARIDFEIHTH_ROOM_FLAG_RESCUE       (1u << 4)
#define ARIDFEIHTH_ROOM_FLAG_SHIP_CAMEO   (1u << 5)
#define ARIDFEIHTH_ROOM_FLAG_AERIAL       (1u << 6)
#define ARIDFEIHTH_ROOM_FLAG_BOSS         (1u << 7)
#define ARIDFEIHTH_ROOM_FLAG_TUTORIAL     (1u << 8)

#define ARIDFEIHTH_GEAR_FLAG_SHIP_UNLOCK  (1u << 0)
#define ARIDFEIHTH_GEAR_FLAG_GATE_BONUS   (1u << 1)
#define ARIDFEIHTH_GEAR_FLAG_PET_TUTORIAL (1u << 2)

#define ARIDFEIHTH_NO_EXIT { NULL, NULL, false }
#define ARIDFEIHTH_EXIT(room_id_value, requires_value, clear_value) { room_id_value, requires_value, clear_value }

typedef enum AridfeihthMode {
    ARIDFEIHTH_MODE_TITLE = 0,
    ARIDFEIHTH_MODE_CONTROLS,
    ARIDFEIHTH_MODE_SHIP_ADVENTURE,
    ARIDFEIHTH_MODE_PET_TUTORIAL,
    ARIDFEIHTH_MODE_CAMPAIGN
} AridfeihthMode;

typedef struct AridfeihthRoomExit {
    const char *room_id;
    const char *requires;
    bool requires_room_clear;
} AridfeihthRoomExit;

typedef struct AridfeihthRoom {
    const char *id;
    const char *name;
    const char *scene_family;
    unsigned scene_index;
    unsigned danger;
    unsigned flags;
    const char *objective;
    const char *tutorial_tip;
    AridfeihthRoomExit left;
    AridfeihthRoomExit right;
    AridfeihthRoomExit alternate_right;
} AridfeihthRoom;

typedef struct AridfeihthPlayerMove {
    const char *id;
    const char *name;
    const char *input;
    const char *category;
    float base_power;
    unsigned precision_window;
    unsigned weapon_points;
} AridfeihthPlayerMove;

typedef struct AridfeihthPetTutorialMove {
    const char *id;
    const char *name;
    const char *input;
    const char *effect;
} AridfeihthPetTutorialMove;

typedef struct AridfeihthGearItem {
    const char *id;
    const char *name;
    const char *slot;
    float power;
    int precision_bonus;
    float defense;
    float xp_bonus;
    float tension_relief;
    float aerial_control;
    float bond_charge_bonus;
    unsigned flags;
} AridfeihthGearItem;

typedef struct AridfeihthCombatMove {
    const char *name;
    int damage;
    unsigned cooldown;
    unsigned range;
    unsigned windup;
} AridfeihthCombatMove;

typedef struct AridfeihthEnemyArchetype {
    const char *id;
    const char *display_name;
    unsigned xp;
    size_t move_count;
    const AridfeihthCombatMove *moves;
} AridfeihthEnemyArchetype;

typedef struct AridfeihthProgressionGate {
    const char *id;
    const char *name;
    const char *room_a;
    const char *room_b;
    const char *sequence[3];
    size_t sequence_count;
} AridfeihthProgressionGate;

typedef struct AridfeihthMilestone {
    const char *id;
    const char *label;
    const char *criteria_kind;
    const char *criteria_value;
    const char *requires_previous[3];
    size_t requires_previous_count;
} AridfeihthMilestone;

typedef struct AridfeihthShipMove {
    const char *name;
    const char *input;
    const char *effect;
} AridfeihthShipMove;

typedef struct AridfeihthShipAdventureMode {
    const char *title_menu_label;
    const char *description;
    size_t move_count;
    const AridfeihthShipMove *moves;
} AridfeihthShipAdventureMode;

typedef struct AridfeihthControllerProfile {
    const char *target;
    const char *move_axis;
    const char *light_attack;
    const char *burst_command;
    const char *dodge;
    const char *jump;
    const char *bond_weave;
} AridfeihthControllerProfile;

typedef struct AridfeihthLoadoutDefaults {
    unsigned level;
    unsigned experience;
    unsigned weapon_points;
    const char *equipped_weapon;
    const char *equipped_sidearm;
    const char *equipped_relic;
    const char *inventory[4];
    size_t inventory_count;
    const char *boss_required_pets[4];
    size_t boss_required_pet_count;
    const char *tutorial_pet_id;
} AridfeihthLoadoutDefaults;

typedef struct AridfeihthPrototypeMetadata {
    const char *title;
    const char *project;
    const char *engine;
    const char *experience_goal;
    const char *render_style;
    const char *camera_mode;
    float camera_horizon;
    const char *player_identity;
    const char *start_room_id;
    const char *controller_target;
    unsigned novice_hours_min;
    unsigned novice_hours_max;
    unsigned projected_move_count;
    const char *const *palette_notes;
    size_t palette_note_count;
    const char *const *core_loop;
    size_t core_loop_count;
} AridfeihthPrototypeMetadata;

typedef struct AridfeihthIntegrationSettings {
    const char *egosphere_mode;
    const char *egosphere_focus;
    const char *egosphere_agent_name;
    bool egosphere_auto_build;
    float godai_difficulty_floor;
    float godai_difficulty_ceiling;
    const char *godai_focus;
    const char *const *orbengine_capabilities;
    size_t orbengine_capability_count;
    const char *const *doengine_capabilities;
    size_t doengine_capability_count;
} AridfeihthIntegrationSettings;

typedef struct AridfeihthRuntimeState {
    AridfeihthMode mode;
    const AridfeihthRoom *current_room;
    unsigned level;
    unsigned experience;
    unsigned weapon_points;
    const char *equipped_weapon;
    const char *equipped_sidearm;
    const char *equipped_relic;
    const char *inventory[8];
    size_t inventory_count;
    bool ship_mode_unlocked;
    bool pet_tutorial_unlocked;
    const char *tutorial_pet_id;
} AridfeihthRuntimeState;

struct AridfeihthPrototypePackage;

typedef struct AridfeihthRuntimeHooks {
    void (*reset_state)(AridfeihthRuntimeState *state);
    void (*seed_progression)(AridfeihthRuntimeState *state);
    void (*enter_title)(AridfeihthRuntimeState *state);
    void (*unlock_ship_mode)(AridfeihthRuntimeState *state);
    void (*unlock_pet_tutorial)(AridfeihthRuntimeState *state);
    void (*begin_campaign)(AridfeihthRuntimeState *state);
    void (*print_summary)(FILE *stream, const struct AridfeihthPrototypePackage *package);
} AridfeihthRuntimeHooks;

typedef struct AridfeihthPrototypePackage {
    AridfeihthPrototypeMetadata metadata;
    AridfeihthIntegrationSettings integrations;
    AridfeihthControllerProfile controller;
    AridfeihthLoadoutDefaults defaults;
    size_t title_option_count;
    const char *const *title_options;
    size_t milestone_count;
    const AridfeihthMilestone *milestones;
    size_t player_move_count;
    const AridfeihthPlayerMove *player_moves;
    size_t pet_tutorial_move_count;
    const AridfeihthPetTutorialMove *pet_tutorial_moves;
    size_t gear_count;
    const AridfeihthGearItem *gear_catalog;
    size_t enemy_archetype_count;
    const AridfeihthEnemyArchetype *enemy_archetypes;
    size_t boss_move_count;
    const AridfeihthCombatMove *boss_moves;
    size_t progression_gate_count;
    const AridfeihthProgressionGate *progression_gates;
    size_t room_count;
    const AridfeihthRoom *rooms;
    AridfeihthShipAdventureMode ship_adventure;
    AridfeihthRuntimeHooks hooks;
} AridfeihthPrototypePackage;

static void aridfeihth_reset_state(AridfeihthRuntimeState *state);
static void aridfeihth_seed_progression(AridfeihthRuntimeState *state);
static void aridfeihth_enter_title(AridfeihthRuntimeState *state);
static void aridfeihth_unlock_ship_mode(AridfeihthRuntimeState *state);
static void aridfeihth_unlock_pet_tutorial(AridfeihthRuntimeState *state);
static void aridfeihth_begin_campaign(AridfeihthRuntimeState *state);
static void aridfeihth_print_summary(FILE *stream, const AridfeihthPrototypePackage *package);
static const AridfeihthRoom *aridfeihth_find_room(const char *room_id);
#ifdef ARIDFEIHTH_PROTOTYPE_PACKAGE_SELFTEST
static const char *aridfeihth_mode_name(AridfeihthMode mode);
#endif

static const char *const kAridfeihthPaletteNotes[] = {
    "ash-cobalt dusk over a weathered horizon",
    "oxidized brass trims and reliquary glints",
    "ember rust, kiln brown, and grave-grey ground planes"
};

static const char *const kAridfeihthCoreLoop[] = {
    "sortie from refuge",
    "stabilize hostile room",
    "rescue or pacify SimIAM",
    "unlock route or new verb",
    "return to refuge to rest and retune loadout"
};

static const char *const kAridfeihthOrbengineCapabilities[] = {
    "parallax layering",
    "pseudo3d floor staging",
    "room-depth composition"
};

static const char *const kAridfeihthDoengineCapabilities[] = {
    "runtime bucket manifests",
    "deterministic asset intake",
    "automation-ready JSON outputs"
};

static const char *const kAridfeihthTitleOptions[] = {
    "Start Prototype",
    "Ship Adventure Test",
    "Controls",
    "Quit"
};

static const AridfeihthPlayerMove kAridfeihthPlayerMoves[] = {
    { "salt_cut", "Salt Cut", "X", "ground_combo", 1.00f, 4u, 1u },
    { "rust_hook", "Rust Hook", "X,X", "ground_combo", 1.18f, 4u, 1u },
    { "brass_splitter", "Brass Splitter", "X,X,X", "ground_combo", 1.42f, 5u, 2u },
    { "skiff_step", "Skiff Step", "A+Left/Right", "mobility", 0.00f, 0u, 0u },
    { "dash_slash", "Dash Slash", "Dash+X", "mobility_attack", 1.15f, 3u, 1u },
    { "rising_notch", "Rising Notch", "Up+X", "launcher", 1.12f, 3u, 1u },
    { "aerial_crescent", "Aerial Crescent", "Air+X", "air", 1.10f, 3u, 1u },
    { "dive_keel", "Dive Keel", "Down+Air+X", "air", 1.24f, 2u, 1u },
    { "feint_parry", "Feint Parry", "B then X", "counter", 1.35f, 2u, 1u },
    { "chorus_sweep", "Chorus Sweep", "RB+X", "chorus", 0.95f, 4u, 1u },
    { "burst_relay", "Burst Relay", "Y", "pet_command", 1.25f, 4u, 0u },
    { "anchor_breaker", "Anchor Breaker", "RT+X", "heavy", 1.50f, 2u, 2u },
    { "weave_lunge", "Weave Lunge", "LT+X", "finisher", 1.65f, 5u, 2u }
};

static const AridfeihthPetTutorialMove kAridfeihthPetTutorialMoves[] = {
    { "prism_flick", "Prism Flick", "X", "quick jab" },
    { "mirror_skate", "Mirror Skate", "A", "short dash" },
    { "refraction_roll", "Refraction Roll", "B", "invulnerable curl" },
    { "focus_pulse", "Focus Pulse", "Y", "stuns tutorial dummy" },
    { "shard_coil", "Shard Coil", "RB", "trap ring" },
    { "recall_arc", "Recall Arc", "LT", "returns to Munki anchor" }
};

static const AridfeihthGearItem kAridfeihthGearCatalog[] = {
    { "brass_hookblade", "Brass Hookblade", "weapon", 0.35f, 1, 0.00f, 0.00f, 0.00f, 0.00f, 0.00f, 0u },
    { "cobalt_scimitar", "Cobalt Scimitar", "weapon", 0.55f, 1, 0.00f, 0.00f, 0.00f, 0.00f, 0.00f, 0u },
    { "dune_falcata", "Dune Falcata", "weapon", 0.80f, 2, 0.00f, 0.00f, 0.00f, 0.00f, 0.00f, 0u },
    { "ember_pistol", "Ember Pistol", "sidearm", 0.40f, 0, 0.00f, 0.00f, 0.00f, 0.00f, 0.00f, 0u },
    { "glass_buckler", "Glass Buckler", "offhand", 0.00f, 0, 0.08f, 0.00f, 0.00f, 0.00f, 0.00f, 0u },
    { "rift_compass", "Rift Compass", "relic", 0.00f, 0, 0.00f, 0.10f, 0.00f, 0.00f, 0.00f, 0u },
    { "tea_satchel", "Tea Satchel", "tool", 0.00f, 0, 0.00f, 0.00f, 5.00f, 0.00f, 0.00f, 0u },
    { "dock_chain_boots", "Dock Chain Boots", "boots", 0.00f, 0, 0.00f, 0.00f, 0.00f, 0.12f, 0.00f, 0u },
    { "quartz_gorget", "Quartz Gorget", "relic", 0.00f, 0, 0.00f, 0.00f, 0.00f, 0.00f, 4.00f, 0u },
    { "pirate_chart", "Pirate Chart Fragment", "quest", 0.00f, 0, 0.00f, 0.00f, 0.00f, 0.00f, 0.00f, ARIDFEIHTH_GEAR_FLAG_SHIP_UNLOCK },
    { "domino_key", "Domino Gate Key", "quest", 0.00f, 0, 0.00f, 0.00f, 0.00f, 0.00f, 0.00f, ARIDFEIHTH_GEAR_FLAG_GATE_BONUS },
    { "munki_hologem", "Munki Hologem", "quest", 0.00f, 0, 0.00f, 0.00f, 0.00f, 0.00f, 0.00f, ARIDFEIHTH_GEAR_FLAG_PET_TUTORIAL }
};

static const AridfeihthCombatMove kStairWatcherMoves[] = {
    { "Slate Jab", 5, 18u, 6u, 4u },
    { "Lantern Bash", 6, 20u, 5u, 5u },
    { "Riser Snap", 4, 16u, 7u, 3u },
    { "Guard Tilt", 3, 22u, 4u, 4u },
    { "Dust Shoulder", 5, 19u, 5u, 4u }
};

static const AridfeihthCombatMove kGlassReaverMoves[] = {
    { "Shard Slice", 6, 16u, 7u, 4u },
    { "Cleft Step", 5, 15u, 8u, 3u },
    { "Mirror Rip", 7, 20u, 6u, 5u },
    { "Brass Elbow", 4, 17u, 5u, 3u },
    { "Silt Backstep", 3, 14u, 4u, 2u }
};

static const AridfeihthCombatMove kWindScourerMoves[] = {
    { "Gale Peck", 4, 14u, 8u, 2u },
    { "Sky Hook", 6, 18u, 7u, 4u },
    { "Turbine Sweep", 5, 17u, 9u, 3u },
    { "Slip Draft", 3, 15u, 6u, 2u },
    { "Needle Gust", 5, 19u, 8u, 4u }
};

static const AridfeihthCombatMove kMirrorEelMoves[] = {
    { "Wet Lash", 6, 16u, 7u, 3u },
    { "Reflect Coil", 5, 18u, 6u, 4u },
    { "Prism Bite", 7, 19u, 5u, 4u },
    { "Current Roll", 4, 15u, 7u, 2u },
    { "Flood Snap", 6, 20u, 8u, 4u }
};

static const AridfeihthCombatMove kHuskArchivistMoves[] = {
    { "Ink Pike", 6, 18u, 8u, 4u },
    { "Ledger Hammer", 7, 20u, 5u, 5u },
    { "Dust Sermon", 4, 16u, 7u, 3u },
    { "Archive Step", 3, 15u, 4u, 2u },
    { "Spine Arc", 5, 17u, 6u, 3u }
};

static const AridfeihthCombatMove kReliquaryMarauderMoves[] = {
    { "Hook Lunge", 7, 18u, 7u, 4u },
    { "Powder Kick", 5, 16u, 6u, 3u },
    { "Sling Burst", 6, 17u, 9u, 4u },
    { "Deck Chop", 8, 21u, 5u, 5u },
    { "Red Wake", 5, 14u, 8u, 2u }
};

static const AridfeihthCombatMove kGatePikemanMoves[] = {
    { "Pike Thrust", 7, 18u, 9u, 4u },
    { "Ferrule Crush", 6, 17u, 6u, 3u },
    { "Brace Wall", 4, 22u, 4u, 5u },
    { "Gate Sweep", 7, 19u, 7u, 4u },
    { "Latch Snap", 5, 15u, 6u, 3u }
};

static const AridfeihthCombatMove kEmberPrivateerMoves[] = {
    { "Cinder Volley", 7, 17u, 9u, 3u },
    { "Anchor Sweep", 8, 20u, 7u, 5u },
    { "Heat Pike", 6, 18u, 8u, 4u },
    { "Coal Feint", 4, 15u, 5u, 2u },
    { "Ash Wake", 7, 16u, 8u, 3u }
};

static const AridfeihthEnemyArchetype kAridfeihthEnemyArchetypes[] = {
    { "stair_watcher", "Stair Watcher", 18u, ARIDFEIHTH_ARRAY_COUNT(kStairWatcherMoves), kStairWatcherMoves },
    { "glass_reaver", "Glass Reaver", 21u, ARIDFEIHTH_ARRAY_COUNT(kGlassReaverMoves), kGlassReaverMoves },
    { "wind_scourer", "Wind Scourer", 20u, ARIDFEIHTH_ARRAY_COUNT(kWindScourerMoves), kWindScourerMoves },
    { "mirror_eel", "Mirror Eel", 24u, ARIDFEIHTH_ARRAY_COUNT(kMirrorEelMoves), kMirrorEelMoves },
    { "husk_archivist", "Husk Archivist", 26u, ARIDFEIHTH_ARRAY_COUNT(kHuskArchivistMoves), kHuskArchivistMoves },
    { "reliquary_marauder", "Reliquary Marauder", 29u, ARIDFEIHTH_ARRAY_COUNT(kReliquaryMarauderMoves), kReliquaryMarauderMoves },
    { "gate_pikeman", "Gate Pikeman", 31u, ARIDFEIHTH_ARRAY_COUNT(kGatePikemanMoves), kGatePikemanMoves },
    { "ember_privateer", "Ember Privateer", 34u, ARIDFEIHTH_ARRAY_COUNT(kEmberPrivateerMoves), kEmberPrivateerMoves }
};

static const AridfeihthCombatMove kAridfeihthBossMoves[] = {
    { "Broadside Sigil", 10, 20u, 10u, 5u },
    { "Anchor Halo", 11, 22u, 8u, 6u },
    { "Cinder Helm", 9, 18u, 7u, 4u },
    { "Gale Tax", 8, 17u, 9u, 3u },
    { "Powder Prayer", 12, 23u, 10u, 6u },
    { "Hull Crash", 11, 21u, 7u, 5u },
    { "Brass Tempest", 9, 18u, 9u, 4u },
    { "Privateer Cut", 10, 19u, 6u, 4u },
    { "Keel Break", 12, 24u, 8u, 6u },
    { "Ashen Vane", 8, 17u, 9u, 3u },
    { "Signal Harrow", 9, 18u, 8u, 4u },
    { "Reef Charge", 11, 22u, 7u, 5u },
    { "Burnished Ram", 10, 19u, 6u, 4u },
    { "Smoke Ledger", 7, 16u, 10u, 3u },
    { "Domino Wake", 12, 24u, 9u, 6u },
    { "Final Broadglass", 14, 26u, 11u, 7u }
};

static const AridfeihthMilestone kAridfeihthMilestones[] = {
    { "refuge_reset", "Refuge hearth steadied", "rested_in_room", "latchspire_refuge", { NULL, NULL, NULL }, 0u },
    { "mirror_newt_rescued", "Mirror Newt trust earned", "rescued_pet", "mirror_newt", { "refuge_reset", NULL, NULL }, 1u },
    { "latch_spider_rescued", "Latch Spider anchored", "rescued_pet", "latch_spider", { "mirror_newt_rescued", NULL, NULL }, 1u },
    { "switchyard_stabilized", "Switchyard pressure broken", "room_clear_in_room", "ossuary_switchyard", { "latch_spider_rescued", NULL, NULL }, 1u },
    { "ember_nave_weave", "Ember sanction unwoven", "boss_defeated_in_room", "ember_nave", { "switchyard_stabilized", NULL, NULL }, 1u },
    { "sanctum_return", "Ash sanctum reclaimed", "entered_room", "tutorial_sanctum", { "ember_nave_weave", NULL, NULL }, 1u },
    { "reliquary_bazaar_reached", "Reliquary market reached", "entered_room", "reliquary_bazaar", { "sanctum_return", NULL, NULL }, 1u },
    { "atlas_choir_reached", "Atlas overlook opened", "entered_room", "atlas_choir", { "reliquary_bazaar_reached", NULL, NULL }, 1u }
};

static const AridfeihthProgressionGate kAridfeihthProgressionGates[] = {
    { "quay_domino_gate", "Quay Domino Gate", "ropewalk_harbor", "brass_battery", { "capstan_release", "weight_drop", "mirror_baffle" }, 3u },
    { "cistern_domino_gate", "Cistern Domino Gate", "mirror_cistern", "prism_grotto", { "sluice_turn", "glass_rod", "echo_plate" }, 3u },
    { "choir_domino_gate", "Choir Domino Gate", "bell_foundry", "chain_lift_annex", { "bell_strike", "counterweight", "choir_latch" }, 3u },
    { "switchyard_domino_gate", "Switchyard Domino Gate", "ossuary_switchyard", "cinder_drydock", { "rail_lock", "ember_basin", "lever_spine" }, 3u },
    { "boss_domino_gate", "Blackglass Gate", "blackglass_gatehouse", "ashfall_dais", { "signal_mast", "brass_orrery", "final_keel" }, 3u }
};

static const AridfeihthShipMove kAridfeihthShipMoves[] = {
    { "Dune Rudder", "Left Stick", "turn and drift" },
    { "Skim Lift", "A", "short aerial rise" },
    { "Broadside", "X", "port cannon volley" },
    { "Burn Boost", "RT", "speed burst" },
    { "Anchor Brake", "LT", "hard stop and pivot" }
};

static const AridfeihthRoom kAridfeihthRooms[] = {
    {
        "latchspire_refuge",
        "Latchspire Refuge",
        "refuge",
        1u,
        0u,
        ARIDFEIHTH_ROOM_FLAG_SAFE | ARIDFEIHTH_ROOM_FLAG_HUB | ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_TUTORIAL,
        "Steady the refuge hearth, read the roster, and leave the tower with a bond profile fit for the ash corridor beyond.",
        "Press R to rest beneath the brass warding lamps. Movement is on the arrow keys, and the first wind-cut route begins at the lamp-dark threshold to the right.",
        ARIDFEIHTH_EXIT("ropewalk_harbor", NULL, false),
        ARIDFEIHTH_EXIT("choir_stair", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "choir_stair",
        "Choir Stair",
        "choir",
        1u,
        1u,
        ARIDFEIHTH_ROOM_FLAG_TUTORIAL,
        "Learn dodge timing and Chorus discipline while the broken stair throws grit, shadow, and bad footing across your path.",
        "Press Space to dodge through pressure and C to toggle Wind Kite. Chorus buys breathing room, but the ash wind and worn stair edges make wasted tension expensive.",
        ARIDFEIHTH_EXIT("latchspire_refuge", NULL, false),
        ARIDFEIHTH_EXIT("glasswind_causeway", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "glasswind_causeway",
        "Glasswind Causeway",
        "glasswind",
        1u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_RESCUE | ARIDFEIHTH_ROOM_FLAG_TUTORIAL,
        "Break the bridge predators, then rescue Mirror Newt so the route can bend through cobalt reflections, riveted iron, and exposed wind instead of brute force.",
        "Use Z for melee and X for Glass Beak. Burst commands crack posture faster than chip damage, which matters once the causeway starts hunting back through the open span.",
        ARIDFEIHTH_EXIT("latchspire_refuge", NULL, false),
        ARIDFEIHTH_EXIT("mirror_cistern", "mirror_newt", false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "mirror_cistern",
        "Mirror Cistern",
        "glasswind",
        2u,
        3u,
        ARIDFEIHTH_ROOM_FLAG_RESCUE,
        "Read the mirrored kill-lines in the cistern and free Latch Spider from drowned clockwork before the chamber folds in on itself.",
        "Reed Fin is a Crest pet. This room is about noticing quiet protection while wet stone, red reflections, and cobalt glare try to convince you the pressure is larger than it is.",
        ARIDFEIHTH_EXIT("glasswind_causeway", NULL, false),
        ARIDFEIHTH_EXIT("scribe_gullet", "latch_spider", false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "scribe_gullet",
        "Scribe Gullet",
        "refuge",
        2u,
        1u,
        ARIDFEIHTH_ROOM_FLAG_SAFE | ARIDFEIHTH_ROOM_FLAG_HUB | ARIDFEIHTH_ROOM_FLAG_INTERACTABLE,
        "Use the soot-quiet pocket to settle bond tension, then step from ledgers, cages, and braziers into the harsher iron logic of the switchyard.",
        "This is a mid-run calm pocket. Rest again if bond tension is spiking before the next hard gate starts speaking in sparks and locking rails.",
        ARIDFEIHTH_EXIT("glasswind_causeway", NULL, false),
        ARIDFEIHTH_EXIT("ossuary_switchyard", NULL, false),
        ARIDFEIHTH_EXIT("munki_refractionary", NULL, false)
    },
    {
        "ossuary_switchyard",
        "Ossuary Switchyard",
        "ember",
        1u,
        4u,
        ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Break the switchyard bailiff and wrench the signal lane open into the Ember Nave by force of presence, not momentum, while the rails keep spitting back.",
        "Clear-gated exits matter here. The iron lane does not yield until the active threat has been fully broken out of the room and the rails stop answering to it.",
        ARIDFEIHTH_EXIT("mirror_cistern", NULL, false),
        ARIDFEIHTH_EXIT("ember_nave", NULL, true),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "ember_nave",
        "Ember Nave",
        "ember",
        2u,
        5u,
        ARIDFEIHTH_ROOM_FLAG_BOSS,
        "Root the sanctioner in the ash-lit nave, sustain Wind Kite through the heat, and end the rite with a full bond weave in front of the altar.",
        "Lower posture, keep Wind Kite active, make sure the boss is rooted, then press V for Bond Weave when the brass window opens and the altar line is clear.",
        ARIDFEIHTH_EXIT("ossuary_switchyard", NULL, false),
        ARIDFEIHTH_EXIT("ram_gate", NULL, true),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "ram_gate",
        "Ram Gate",
        "ember",
        3u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Use Salt Ram to break the reliquary barricade and prove that the boss reward changes stone, iron, and map state immediately, not abstractly.",
        "This is the post-boss key test. The corridor only yields because Salt Ram can answer stone and iron with impact the moment you arrive.",
        ARIDFEIHTH_EXIT("ember_nave", NULL, false),
        ARIDFEIHTH_EXIT("tutorial_sanctum", "salt_ram", false),
        ARIDFEIHTH_EXIT("blackglass_gatehouse", NULL, false)
    },
    {
        "tutorial_sanctum",
        "Tutorial Sanctum",
        "choir",
        2u,
        0u,
        ARIDFEIHTH_ROOM_FLAG_SAFE | ARIDFEIHTH_ROOM_FLAG_HUB | ARIDFEIHTH_ROOM_FLAG_TUTORIAL,
        "Reach shelter with the full opening rite intact: rest, route, fight, rescue, breach, weave, and return with the roster still coherent under calmer light.",
        "The core loop is established. From here the next pass can widen the map without changing the ash-reliquary identity, dark detail language, and cobalt-brass accents that already hold the route together.",
        ARIDFEIHTH_EXIT("ram_gate", NULL, false),
        ARIDFEIHTH_EXIT("reliquary_bazaar", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "reliquary_bazaar",
        "Reliquary Bazaar",
        "glasswind",
        3u,
        1u,
        ARIDFEIHTH_ROOM_FLAG_SAFE | ARIDFEIHTH_ROOM_FLAG_HUB | ARIDFEIHTH_ROOM_FLAG_INTERACTABLE,
        "Step into the market lane and preview how barter, tuning, and habitat care can extend the rescue loop without softening its wasteland edge or its dark detailing.",
        "This room is calm on purpose. After the combat proof, it widens the horizon with traders, ash cloth, brass fittings, dark awnings, and companion upkeep instead of more immediate violence.",
        ARIDFEIHTH_EXIT("tutorial_sanctum", NULL, false),
        ARIDFEIHTH_EXIT("atlas_choir", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "atlas_choir",
        "Atlas Choir",
        "choir",
        3u,
        0u,
        ARIDFEIHTH_ROOM_FLAG_SAFE | ARIDFEIHTH_ROOM_FLAG_HUB,
        "End at the overlook where the first corridor opens into a larger pilgrimage map of ash basins, cobalt distances, brass-lit holds, and darker country between them.",
        "This final room frames scale rather than instruction. The first authored loop is complete, and the world now visibly stretches beyond it in the same palette language and surface logic.",
        ARIDFEIHTH_EXIT("reliquary_bazaar", NULL, false),
        ARIDFEIHTH_EXIT("pilgrim_skywalk", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "ropewalk_harbor",
        "Ropewalk Harbor",
        "base",
        0u,
        1u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE | ARIDFEIHTH_ROOM_FLAG_SHIP_CAMEO,
        "Trace the harbor ropes, glimpse the pirate ship silhouette, and begin the first domino gate chain.",
        "Use E near interactables to release the ropewalk machinery. The anchored ship beyond the ash tide is a cameo and a test-route promise.",
        ARIDFEIHTH_NO_EXIT,
        ARIDFEIHTH_EXIT("latchspire_refuge", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "brass_battery",
        "Brass Battery",
        "base",
        0u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Kick the battery weight through a chain reaction to power the harbor gate.",
        "Strike the suspended battery after arming the relay to continue the domino sequence.",
        ARIDFEIHTH_EXIT("latchspire_refuge", NULL, false),
        ARIDFEIHTH_EXIT("scribe_gullet", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "munki_refractionary",
        "Munki Refractionary",
        "base",
        0u,
        1u,
        ARIDFEIHTH_ROOM_FLAG_SAFE | ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_RESCUE | ARIDFEIHTH_ROOM_FLAG_TUTORIAL,
        "Optional detour: recover the Munki hologem and enter the projected pet tutorial chamber.",
        "Rescue the Refraction Munki, then interact with the hologem visualizer to assume SimIAM control and test six pet inputs.",
        ARIDFEIHTH_EXIT("scribe_gullet", NULL, false),
        ARIDFEIHTH_EXIT("tutorial_sanctum", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "skiff_berth",
        "Skiff Berth",
        "base",
        0u,
        1u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_SHIP_CAMEO,
        "Read the desert-pirate ship cameo at close range and unlock a title-menu route to ship tests.",
        "Interact with the mooring post to mark the ship adventure test on the title menu.",
        ARIDFEIHTH_EXIT("latchspire_refuge", NULL, false),
        ARIDFEIHTH_EXIT("ropewalk_harbor", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "aerie_spur",
        "Aerie Spur",
        "base",
        0u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_AERIAL,
        "Taste a brief aerial route over chain lifts and falling sails.",
        "This room is a short aerial tease. Keep jumps tight and use the dock-chain boots if you find them.",
        ARIDFEIHTH_EXIT("tutorial_sanctum", NULL, false),
        ARIDFEIHTH_EXIT("atlas_choir", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "dust_rail_span",
        "Dust Rail Span",
        "base",
        0u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Cross a rail bridge while learning how interactable machinery and enemy pressure overlap.",
        "Toggle the rail latch before the enemy push closes in.",
        ARIDFEIHTH_EXIT("glasswind_causeway", NULL, false),
        ARIDFEIHTH_EXIT("mirror_cistern", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "prism_grotto",
        "Prism Grotto",
        "base",
        0u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Work through a reflective flood puzzle before opening the cistern gate.",
        "This grotto combines movement, switch order, and enemy pressure into a small chain reaction problem.",
        ARIDFEIHTH_EXIT("mirror_cistern", NULL, false),
        ARIDFEIHTH_EXIT("reliquary_bazaar", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "windlass_quay",
        "Windlass Quay",
        "base",
        0u,
        3u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_SHIP_CAMEO,
        "Meet the ship again from the canyon edge and fight across a cable quay.",
        "The ship cameo returns here as a horizon marker while the quay tests grounded combat spacing.",
        ARIDFEIHTH_EXIT("reliquary_bazaar", NULL, false),
        ARIDFEIHTH_EXIT("atlas_choir", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "relay_basin",
        "Relay Basin",
        "base",
        0u,
        3u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Solve a rail-and-basin relay that foreshadows the larger switchyard gates.",
        "Set the basin weight and then escape the closing threat wave.",
        ARIDFEIHTH_EXIT("glasswind_causeway", NULL, false),
        ARIDFEIHTH_EXIT("ossuary_switchyard", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "bell_foundry",
        "Bell Foundry",
        "base",
        0u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Hit the bell in rhythm to start a three-link choir gate puzzle.",
        "The foundry is a Rube Goldberg room: strike, weight, latch, then run the route before enemies reset the pressure.",
        ARIDFEIHTH_EXIT("choir_stair", NULL, false),
        ARIDFEIHTH_EXIT("tutorial_sanctum", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "chain_lift_annex",
        "Chain Lift Annex",
        "base",
        0u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Run a lift sequence under pressure to understand moving-platform cause and effect.",
        "The annex is still hand-authored, but it gestures toward more kinetic traversal later.",
        ARIDFEIHTH_EXIT("tutorial_sanctum", NULL, false),
        ARIDFEIHTH_EXIT("atlas_choir", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "abbot_stair",
        "Abbot Stair",
        "base",
        0u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE,
        "Climb a narrow procession stair for experience, salvage, and one more gear read.",
        "This room exists to broaden the novice playtime without changing the main route tone.",
        ARIDFEIHTH_EXIT("choir_stair", NULL, false),
        ARIDFEIHTH_EXIT("tutorial_sanctum", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "pilgrim_skywalk",
        "Pilgrim Skywalk",
        "base",
        0u,
        2u,
        ARIDFEIHTH_ROOM_FLAG_AERIAL,
        "A second brief aerial taste framed by the kingdom on one mountain and the spiritual fief on the other.",
        "This skywalk is a thematic hinge: desert-pirate frontier between worldly and spiritual powers.",
        ARIDFEIHTH_EXIT("atlas_choir", NULL, false),
        ARIDFEIHTH_EXIT("windlass_quay", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "cinder_drydock",
        "Cinder Drydock",
        "base",
        0u,
        3u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Push into the dockyard where ember privateers and domino machinery converge.",
        "The drydock introduces prototype-scale enemy density and interactables in the same room.",
        ARIDFEIHTH_EXIT("ossuary_switchyard", NULL, false),
        ARIDFEIHTH_EXIT("blackglass_gatehouse", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "scorched_capstan",
        "Scorched Capstan",
        "base",
        0u,
        3u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Finish the drydock domino chain under boss-adjacent pressure.",
        "This room is the strongest example of the cause-and-effect gate series before the final prototype boss.",
        ARIDFEIHTH_EXIT("cinder_drydock", NULL, false),
        ARIDFEIHTH_EXIT("blackglass_gatehouse", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "blackglass_gatehouse",
        "Blackglass Gatehouse",
        "base",
        0u,
        4u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_PUZZLE,
        "Prime the final prototype gate through one last three-step contraption puzzle.",
        "This is the last gate room before the prototype boss. Solve the chain and prepare your gear.",
        ARIDFEIHTH_EXIT("ram_gate", NULL, false),
        ARIDFEIHTH_EXIT("ashfall_dais", NULL, false),
        ARIDFEIHTH_NO_EXIT
    },
    {
        "ashfall_dais",
        "Ashfall Dais",
        "base",
        0u,
        5u,
        ARIDFEIHTH_ROOM_FLAG_INTERACTABLE | ARIDFEIHTH_ROOM_FLAG_BOSS,
        "Face the prototype final boss in a pressure-heavy relic dock beneath falling ash.",
        "The Commodore has sixteen named moves in this prototype and expects full use of gear, pets, and timing discipline.",
        ARIDFEIHTH_EXIT("blackglass_gatehouse", NULL, false),
        ARIDFEIHTH_NO_EXIT,
        ARIDFEIHTH_NO_EXIT
    }
};

static const AridfeihthPrototypePackage ARIDFEIHTH_PROTOTYPE_PACKAGE = {
    {
        "Aridfeihth Ash-Reliquary Demo",
        "aridfeihth",
        "IllusionCanvasInteractive",
        "A 1-6 hour novice-friendly prototype pilgrimage through a desert-pirate frontier, mixing hack-slash precision, optional pet rescue/tutorial detours, gear-driven growth, domino-gated traversal, and a final reliquary dock boss.",
        "2.5D pseudo3D 2D pixel-art hybrid",
        "side_view_with_orbstyle_parallax",
        0.56f,
        "light melee plus pet-directed encounter control",
        "latchspire_refuge",
        "Xbox Series gamepad",
        1u,
        6u,
        23040u,
        kAridfeihthPaletteNotes,
        ARIDFEIHTH_ARRAY_COUNT(kAridfeihthPaletteNotes),
        kAridfeihthCoreLoop,
        ARIDFEIHTH_ARRAY_COUNT(kAridfeihthCoreLoop)
    },
    {
        "native-preferred",
        "encounter reading, pressure interpretation, and target emphasis",
        "aridfeihth_field_agent",
        true,
        0.88f,
        1.28f,
        "omen pacing, mercy windows, and encounter escalation",
        kAridfeihthOrbengineCapabilities,
        ARIDFEIHTH_ARRAY_COUNT(kAridfeihthOrbengineCapabilities),
        kAridfeihthDoengineCapabilities,
        ARIDFEIHTH_ARRAY_COUNT(kAridfeihthDoengineCapabilities)
    },
    {
        "Xbox Series gamepad",
        "Left Stick or D-pad",
        "X or Z",
        "Y or X",
        "A or Space",
        "B or Up+Jump",
        "LT+X or V"
    },
    {
        1u,
        0u,
        0u,
        "brass_hookblade",
        "ember_pistol",
        "rift_compass",
        { "brass_hookblade", "glass_buckler", NULL, NULL },
        2u,
        { "mirror_newt", "latch_spider", "salt_ram", "refraction_munki" },
        4u,
        "refraction_munki"
    },
    ARIDFEIHTH_ARRAY_COUNT(kAridfeihthTitleOptions),
    kAridfeihthTitleOptions,
    ARIDFEIHTH_ARRAY_COUNT(kAridfeihthMilestones),
    kAridfeihthMilestones,
    ARIDFEIHTH_ARRAY_COUNT(kAridfeihthPlayerMoves),
    kAridfeihthPlayerMoves,
    ARIDFEIHTH_ARRAY_COUNT(kAridfeihthPetTutorialMoves),
    kAridfeihthPetTutorialMoves,
    ARIDFEIHTH_ARRAY_COUNT(kAridfeihthGearCatalog),
    kAridfeihthGearCatalog,
    ARIDFEIHTH_ARRAY_COUNT(kAridfeihthEnemyArchetypes),
    kAridfeihthEnemyArchetypes,
    ARIDFEIHTH_ARRAY_COUNT(kAridfeihthBossMoves),
    kAridfeihthBossMoves,
    ARIDFEIHTH_ARRAY_COUNT(kAridfeihthProgressionGates),
    kAridfeihthProgressionGates,
    ARIDFEIHTH_ARRAY_COUNT(kAridfeihthRooms),
    kAridfeihthRooms,
    {
        "Ship Adventure Test",
        "Brief desert-pirate ship drill with boost, broadside, brake, and skimming lift.",
        ARIDFEIHTH_ARRAY_COUNT(kAridfeihthShipMoves),
        kAridfeihthShipMoves
    },
    {
        aridfeihth_reset_state,
        aridfeihth_seed_progression,
        aridfeihth_enter_title,
        aridfeihth_unlock_ship_mode,
        aridfeihth_unlock_pet_tutorial,
        aridfeihth_begin_campaign,
        aridfeihth_print_summary
    }
};

const AridfeihthPrototypePackage *aridfeihth_get_prototype_package(void)
{
    return &ARIDFEIHTH_PROTOTYPE_PACKAGE;
}

void aridfeihth_bootstrap_demo(AridfeihthRuntimeState *state)
{
    const AridfeihthPrototypePackage *package = aridfeihth_get_prototype_package();

    if (state == NULL) {
        return;
    }

    package->hooks.reset_state(state);
    package->hooks.seed_progression(state);
    package->hooks.unlock_ship_mode(state);
    package->hooks.unlock_pet_tutorial(state);
    package->hooks.enter_title(state);
}

void aridfeihth_start_prototype(AridfeihthRuntimeState *state)
{
    const AridfeihthPrototypePackage *package = aridfeihth_get_prototype_package();

    if (state == NULL) {
        return;
    }

    aridfeihth_bootstrap_demo(state);
    package->hooks.begin_campaign(state);
}

static void aridfeihth_reset_state(AridfeihthRuntimeState *state)
{
    if (state == NULL) {
        return;
    }

    memset(state, 0, sizeof(*state));
    state->mode = ARIDFEIHTH_MODE_TITLE;
}

static void aridfeihth_seed_progression(AridfeihthRuntimeState *state)
{
    size_t index;

    if (state == NULL) {
        return;
    }

    state->level = ARIDFEIHTH_PROTOTYPE_PACKAGE.defaults.level;
    state->experience = ARIDFEIHTH_PROTOTYPE_PACKAGE.defaults.experience;
    state->weapon_points = ARIDFEIHTH_PROTOTYPE_PACKAGE.defaults.weapon_points;
    state->equipped_weapon = ARIDFEIHTH_PROTOTYPE_PACKAGE.defaults.equipped_weapon;
    state->equipped_sidearm = ARIDFEIHTH_PROTOTYPE_PACKAGE.defaults.equipped_sidearm;
    state->equipped_relic = ARIDFEIHTH_PROTOTYPE_PACKAGE.defaults.equipped_relic;
    state->inventory_count = ARIDFEIHTH_PROTOTYPE_PACKAGE.defaults.inventory_count;
    state->tutorial_pet_id = ARIDFEIHTH_PROTOTYPE_PACKAGE.defaults.tutorial_pet_id;

    for (index = 0; index < ARIDFEIHTH_ARRAY_COUNT(state->inventory); ++index) {
        state->inventory[index] = NULL;
    }
    for (index = 0; index < state->inventory_count && index < ARIDFEIHTH_ARRAY_COUNT(state->inventory); ++index) {
        state->inventory[index] = ARIDFEIHTH_PROTOTYPE_PACKAGE.defaults.inventory[index];
    }
}

static void aridfeihth_enter_title(AridfeihthRuntimeState *state)
{
    if (state == NULL) {
        return;
    }

    state->mode = ARIDFEIHTH_MODE_TITLE;
    state->current_room = NULL;
}

static void aridfeihth_unlock_ship_mode(AridfeihthRuntimeState *state)
{
    if (state == NULL) {
        return;
    }

    state->ship_mode_unlocked = true;
}

static void aridfeihth_unlock_pet_tutorial(AridfeihthRuntimeState *state)
{
    if (state == NULL) {
        return;
    }

    state->pet_tutorial_unlocked = true;
}

static void aridfeihth_begin_campaign(AridfeihthRuntimeState *state)
{
    if (state == NULL) {
        return;
    }

    state->mode = ARIDFEIHTH_MODE_CAMPAIGN;
    state->current_room = aridfeihth_find_room(ARIDFEIHTH_PROTOTYPE_PACKAGE.metadata.start_room_id);
}

static const AridfeihthRoom *aridfeihth_find_room(const char *room_id)
{
    size_t index;

    if (room_id == NULL) {
        return NULL;
    }

    for (index = 0; index < ARIDFEIHTH_ARRAY_COUNT(kAridfeihthRooms); ++index) {
        if (strcmp(kAridfeihthRooms[index].id, room_id) == 0) {
            return &kAridfeihthRooms[index];
        }
    }
    return NULL;
}

#ifdef ARIDFEIHTH_PROTOTYPE_PACKAGE_SELFTEST
static const char *aridfeihth_mode_name(AridfeihthMode mode)
{
    switch (mode) {
    case ARIDFEIHTH_MODE_TITLE:
        return "title";
    case ARIDFEIHTH_MODE_CONTROLS:
        return "controls";
    case ARIDFEIHTH_MODE_SHIP_ADVENTURE:
        return "ship_adventure";
    case ARIDFEIHTH_MODE_PET_TUTORIAL:
        return "pet_tutorial";
    case ARIDFEIHTH_MODE_CAMPAIGN:
        return "campaign";
    default:
        return "unknown";
    }
}
#endif

static void aridfeihth_print_summary(FILE *stream, const AridfeihthPrototypePackage *package)
{
    if (stream == NULL || package == NULL) {
        return;
    }

    fprintf(stream, "title=%s\n", package->metadata.title);
    fprintf(stream, "engine=%s\n", package->metadata.engine);
    fprintf(stream, "hours=%u-%u\n", package->metadata.novice_hours_min, package->metadata.novice_hours_max);
    fprintf(stream, "rooms=%lu\n", (unsigned long)package->room_count);
    fprintf(stream, "player_moves=%lu\n", (unsigned long)package->player_move_count);
    fprintf(stream, "pet_moves=%lu\n", (unsigned long)package->pet_tutorial_move_count);
    fprintf(stream, "gear=%lu\n", (unsigned long)package->gear_count);
    fprintf(stream, "enemy_varieties=%lu\n", (unsigned long)package->enemy_archetype_count);
    fprintf(stream, "boss_moves=%lu\n", (unsigned long)package->boss_move_count);
    fprintf(stream, "progression_gates=%lu\n", (unsigned long)package->progression_gate_count);
    fprintf(stream, "projected_moves=%u\n", package->metadata.projected_move_count);
    fprintf(stream, "controller_target=%s\n", package->controller.target);
    fprintf(stream, "start_room=%s\n", package->metadata.start_room_id);
}

#ifdef ARIDFEIHTH_PROTOTYPE_PACKAGE_SELFTEST
int main(void)
{
    AridfeihthRuntimeState state;
    const AridfeihthPrototypePackage *package = aridfeihth_get_prototype_package();

    package->hooks.print_summary(stdout, package);
    aridfeihth_bootstrap_demo(&state);
    fprintf(stdout, "boot_mode=%s\n", aridfeihth_mode_name(state.mode));
    fprintf(stdout, "ship_mode_unlocked=%d\n", state.ship_mode_unlocked ? 1 : 0);
    fprintf(stdout, "pet_tutorial_unlocked=%d\n", state.pet_tutorial_unlocked ? 1 : 0);
    aridfeihth_start_prototype(&state);
    fprintf(stdout, "campaign_mode=%s\n", aridfeihth_mode_name(state.mode));
    fprintf(stdout, "campaign_room=%s\n", state.current_room != NULL ? state.current_room->id : "(null)");
    return 0;
}
#endif