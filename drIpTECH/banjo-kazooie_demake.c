#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define MAX_WORLDS 8
#define MAX_ENTITIES 256
#define MAX_APIARY_POINTS 4

typedef struct { float x, y, z; } Vec3;

static inline Vec3 vec3(float x, float y, float z) { Vec3 v = {x,y,z}; return v; }
static inline float vec3_dist2(const Vec3 *a, const Vec3 *b) {
    float dx = a->x - b->x, dy = a->y - b->y, dz = a->z - b->z; return dx*dx+dy*dy+dz*dz;
}

typedef struct {
    char name[48];
    Vec3 pos;
    float health;
    float stamina;
    int unlocked_worlds;
    int current_world; // -1 = hub
} Player;

typedef struct { Vec3 pos; int world_id; int is_active; char name[32]; } ApiaryPoint;

typedef struct {
    int id;
    char name[64];
    Vec3 hub_entrance;
    int unlocked;
    int completion_percent;
    ApiaryPoint apiaries[MAX_APIARY_POINTS];
    int apiary_count;
    char description[256];
} SubWorld;

typedef struct { SubWorld worlds[MAX_WORLDS]; Vec3 player_spawn; int world_count; } GameHub;

typedef enum { ETYPE_ENEMY=0, ETYPE_ITEM=1, ETYPE_NPC=2 } EntityType;
typedef struct {
    Vec3 pos;
    Vec3 rot;
    EntityType type;
    float health;
    int is_focused;
    int alive;
    char tag[32];
} Entity;

typedef struct {
    Player player;
    GameHub hub;
    Entity entities[MAX_ENTITIES];
    int entity_count;
    int focused_index; /* -1 none */
    int souls_like_mode;
} GameState;

/* Forward */
void init_game(GameState* state);
void create_subworld(GameState* state, int id, const char* name, const char* desc);
void spawn_entities_for_world(GameState* state, int world_id, int count);
int lock_on_nearest(GameState* state);
void clear_focus(GameState* state);
int attack_focused(GameState* state);
void rest_at_apiary(GameState* state, int world_id, int apiary_idx);
void fast_travel_apiary(GameState* state, int dest_world, int dest_apiary);

void init_game(GameState* state) {
    memset(state, 0, sizeof(*state));
    strncpy(state->player.name, "Banji & Kazooie", sizeof(state->player.name)-1);
    state->player.health = 100.0f;
    state->player.stamina = 100.0f;
    state->player.unlocked_worlds = 1;
    state->player.current_world = -1; // hub

    state->hub.world_count = MAX_WORLDS;
    state->hub.player_spawn = vec3(0,0,0);
    state->entity_count = 0;
    state->focused_index = -1;
    state->souls_like_mode = 1;

    /* Create a set of compact, demake-friendly worlds (inspired by classic platformer locales)
       Names and descriptions are brief and original to avoid reproducing copyrighted text. */
    create_subworld(state, 0, "Windsprout Grove", "A bright forested hub-adjacent glade with curious critters.");
    create_subworld(state, 1, "Gingerbread Dunes", "Sandy plates and mechanical sandworms; platform puzzles.");
    create_subworld(state, 2, "Clockwork Cove", "A gear-filled island where rhythm and timing matter.");
    create_subworld(state, 3, "Mossy Hollow", "A damp, living cavern full of fungi and bioluminescence.");
    create_subworld(state, 4, "Skyloft Ruins", "Aerial ruins with bird-like enemies and floating platforms.");
    create_subworld(state, 5, "Mirror Marsh", "Misty wetlands where reflections change reality.");
    create_subworld(state, 6, "Frostbit Farm", "Cold farm-lands with icy puzzles and robust enemies.");
    create_subworld(state, 7, "Ember Peak", "Volcanic, high-risk trial world for late-game mastery.");

    /* Set simple apiaries per world (two each) */
    for (int i=0;i<state->hub.world_count;i++) {
        SubWorld *w = &state->hub.worlds[i];
        w->apiary_count = 2;
        for (int a=0;a<w->apiary_count;a++) {
            w->apiaries[a].pos = vec3( (float)(i*10 + a*2), 0.0f, (float)(a*3) );
            w->apiaries[a].world_id = i;
            w->apiaries[a].is_active = 1;
            snprintf(w->apiaries[a].name, sizeof(w->apiaries[a].name), "Apiary %d-%d", i, a);
        }
        w->unlocked = (i==0) ? 1 : 0;
        w->completion_percent = 0;
    }

    /* Spawn a small set of demo enemies in hub for early lock-on testing */
    spawn_entities_for_world(state, -1, 6);
}

void create_subworld(GameState* state, int id, const char* name, const char* desc) {
    if (id < 0 || id >= MAX_WORLDS) return;
    SubWorld *w = &state->hub.worlds[id];
    w->id = id;
    strncpy(w->name, name, sizeof(w->name)-1);
    strncpy(w->description, desc, sizeof(w->description)-1);
    w->hub_entrance = vec3(id*8.0f, 0.0f, 0.0f);
    w->apiary_count = 0;
}

void spawn_entities_for_world(GameState* state, int world_id, int count) {
    /* world_id == -1 => hub */
    for (int i=0;i<count && state->entity_count < MAX_ENTITIES;i++) {
        Entity *e = &state->entities[state->entity_count++];
        e->pos = vec3((float)(rand()%20 - 10), 0.0f, (float)(rand()%20 - 10));
        e->rot = vec3(0,0,0);
        e->type = (i%3==0)?ETYPE_ENEMY:((i%3==1)?ETYPE_NPC:ETYPE_ITEM);
        e->health = (e->type==ETYPE_ENEMY)?50.0f:0.0f;
        e->is_focused = 0;
        e->alive = (e->type==ETYPE_ENEMY)?1:0;
        snprintf(e->tag, sizeof(e->tag), "%s-%d", (e->type==ETYPE_ENEMY)?"Grunt":((e->type==ETYPE_NPC)?"NPC":"Item"), state->entity_count);
    }
}

int lock_on_nearest(GameState* state) {
    /* Return index of focused entity or -1 */
    if (state->entity_count == 0) return -1;
    float best = 1e12f; int best_idx = -1;
    Vec3 player_pos = state->player.pos;
    for (int i=0;i<state->entity_count;i++) {
        Entity *e = &state->entities[i];
        if (!e->alive || e->type != ETYPE_ENEMY) continue;
        float d2 = vec3_dist2(&e->pos, &player_pos);
        if (d2 < best) { best = d2; best_idx = i; }
    }
    if (best_idx >= 0) {
        state->focused_index = best_idx;
        for (int i=0;i<state->entity_count;i++) state->entities[i].is_focused = (i==best_idx);
    }
    return state->focused_index;
}

void clear_focus(GameState* state) {
    state->focused_index = -1;
    for (int i=0;i<state->entity_count;i++) state->entities[i].is_focused = 0;
}

int attack_focused(GameState* state) {
    if (state->focused_index < 0) return -1;
    Entity *e = &state->entities[state->focused_index];
    if (!e->alive) return -2;
    /* simple stamina & health resolution */
    if (state->player.stamina < 10.0f) return -3; /* tired */
    state->player.stamina -= 10.0f;
    float dmg = 20.0f;
    e->health -= dmg;
    printf("[COMBAT] Attacked %s for %.1f dmg (hp=%.1f)\n", e->tag, dmg, e->health);
    if (e->health <= 0.0f) {
        e->alive = 0; printf("[COMBAT] %s defeated!\n", e->tag);
        /* small reward */
        state->player.unlocked_worlds = state->player.unlocked_worlds; /* placeholder: reward logic */
        clear_focus(state);
    }
    return 0;
}

void rest_at_apiary(GameState* state, int world_id, int apiary_idx) {
    if (world_id < 0 || world_id >= state->hub.world_count) return;
    SubWorld *w = &state->hub.worlds[world_id];
    if (apiary_idx < 0 || apiary_idx >= w->apiary_count) return;
    state->player.health = 100.0f;
    state->player.stamina = 100.0f;
    /* narrative placeholder: mark save point */
    printf("[APIARY] Rested at %s (%s). Health & Stamina restored.\n", w->apiaries[apiary_idx].name, w->name);
}

void fast_travel_apiary(GameState* state, int dest_world, int dest_apiary) {
    if (dest_world < 0 || dest_world >= state->hub.world_count) return;
    SubWorld *w = &state->hub.worlds[dest_world];
    if (dest_apiary < 0 || dest_apiary >= w->apiary_count) return;
    state->player.current_world = dest_world;
    state->player.pos = w->apiaries[dest_apiary].pos;
    printf("[FAST TRAVEL] Traveled to World %d (%s), Apiary %d (%s)\n", dest_world, w->name, dest_apiary, w->apiaries[dest_apiary].name);
}

/* small simulation tick to demonstrate systems */
void simulation_tick(GameState* state) {
    /* regen stamina slowly */
    state->player.stamina = fminf(100.0f, state->player.stamina + 1.0f);
}

/* --- Engine Hook API (idTech2-friendly, exported C hooks) --- */

/* Global game state used by engine hooks */
static GameState g_game;

/* Initialize engine-level systems and load base resources */
int engine_init(void) {
    memset(&g_game, 0, sizeof(g_game));
    init_game(&g_game);
    /* Placeholder: load engine resources, textures, sounds */
    printf("[ENGINE] Initialized game engine hooks.\n");
    return 0;
}

/* Load resources required by the engine (called after renderer ready) */
int engine_load_resources(void) {
    /* In a real integration, load assets here and register with engine subsystems */
    printf("[ENGINE] Resources loaded (placeholder).\n");
    return 0;
}

/* Per-frame update called by engine; dt in seconds */
int engine_frame(float dt) {
    (void)dt; /* dt can be used for physics/time based updates */
    simulation_tick(&g_game);
    /* Example: process simple AI or world events */
    return 0;
}

/* Simple render hook (engine would supply renderer contexts) */
void engine_render(void) {
    /* Placeholder: the real engine would draw the hub/world here */
    printf("[ENGINE] Render tick. Player pos=(%.1f,%.1f,%.1f)\n", g_game.player.pos.x, g_game.player.pos.y, g_game.player.pos.z);
}

/* Input hook: minimal event codes enumerated by the embedding engine */
int engine_handle_input(int event_code, void* event_data) {
    /* Example event codes:
       1 = RT pressed, 2 = RT released, 3 = attack, 4 = fast-travel request
       event_data may carry supplemental info (ints, Vec3 pointers, etc.) */
    switch (event_code) {
        case 1: /* RT pressed */
            lock_on_nearest(&g_game);
            return 0;
        case 2: /* RT released */
            clear_focus(&g_game);
            return 0;
        case 3: /* attack */
            attack_focused(&g_game);
            return 0;
        case 4: /* fast-travel: event_data -> int[2] {world,apiary} */
            if (event_data) {
                int* arr = (int*)event_data;
                fast_travel_apiary(&g_game, arr[0], arr[1]);
            }
            return 0;
        default:
            return -1;
    }
}

/* Spawn entity via engine hook */
int engine_spawn_entity_at(Vec3 pos, EntityType type) {
    if (g_game.entity_count >= MAX_ENTITIES) return -1;
    Entity *e = &g_game.entities[g_game.entity_count++];
    e->pos = pos; e->rot = vec3(0,0,0); e->type = type; e->health = (type==ETYPE_ENEMY)?50.0f:0.0f; e->alive = (type==ETYPE_ENEMY); e->is_focused = 0;
    snprintf(e->tag, sizeof(e->tag), "spawn-%d", g_game.entity_count);
    return g_game.entity_count-1;
}

/* Save/load hooks (engine can call these to manage persistent state) */
int engine_save_game(const char* path) {
    (void)path;
    /* Minimal placeholder: a real implementation would write player/world state */
    printf("[ENGINE] Save requested: %s (placeholder)\n", path?path:"<default>");
    return 0;
}

int engine_load_game(const char* path) {
    (void)path;
    /* Minimal placeholder */
    printf("[ENGINE] Load requested: %s (placeholder)\n", path?path:"<default>");
    return 0;
}

/* Shutdown hook */
void engine_shutdown(void) {
    printf("[ENGINE] Shutdown called. Cleaning up.\n");
    /* Free/cleanup subsystems as needed */
}


int main(void) {
    srand((unsigned int)time(NULL));
    /* Initialize engine and resources via hooks */
    engine_init();
    engine_load_resources();

    printf("=== Compact Demake: Hub + Subworlds (idTech2-ready C hooks) ===\n");
    printf("7-hour completion target (75%% run) — balancing TBD\n");
    printf("Worlds available: %d\n", g_game.hub.world_count);
    printf("Player: %s; Health=%.1f Stamina=%.1f\n", g_game.player.name, g_game.player.health, g_game.player.stamina);

    /* demo: lock on nearest enemy and attack a few times using hooks */
    lock_on_nearest(&g_game);
    if (g_game.focused_index >= 0) printf("Locked on: %s (idx=%d)\n", g_game.entities[g_game.focused_index].tag, g_game.focused_index);

    for (int i=0;i<3;i++) {
        engine_handle_input(3, NULL); /* attack */
        engine_frame(1.0f/60.0f);
        engine_render();
    }

    /* demo fast travel and rest via hooks */
    int loc[2] = {0, 0};
    engine_handle_input(4, loc);
    rest_at_apiary(&g_game, 0, 0);

    printf("Entities total (slots used): %d (demo)\n", g_game.entity_count);
    engine_shutdown();
    return 0;
}