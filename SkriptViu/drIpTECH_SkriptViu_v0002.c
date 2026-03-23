#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_ENTITIES 1000
#define MAX_TERRAIN_VERTICES 10000
#define MAX_MENU_ITEMS 50
#define GRID_SIZE 100

// ============= CORE STRUCTURES =============

typedef struct Entity Entity;

typedef struct {
    float x, y, z;
} Vector3;

typedef struct {
    float x, y;
} Vector2;

typedef struct {
    Vector3 position;
    Vector3 rotation;
    Vector3 scale;
} Transform;

struct Entity {
    int id;
    char name[64];
    char prefab_path[256];
    char sprite_path[256];
    Transform transform;
    int entity_type; // 0=static, 1=dynamic, 2=player, 3=npc
    int is_active;
    void (*update_func)(Entity*);
    void (*interact_func)(Entity*);
};

typedef struct {
    Vector3 vertices[MAX_TERRAIN_VERTICES];
    int vertex_count;
    float height_map[GRID_SIZE][GRID_SIZE];
    char texture_path[256];
} Terrain;

typedef struct {
    int id;
    char label[64];
    int x, y, w, h;
    int (*on_click)(void);
} MenuItem;

typedef struct {
    MenuItem items[MAX_MENU_ITEMS];
    int item_count;
    int is_visible;
} Menu;

typedef struct {
    Entity entities[MAX_ENTITIES];
    int entity_count;
    Terrain terrain;
    Menu main_menu;
    Menu game_menu;
    int is_playing;
    float delta_time;
} GameWorld;

// ============= UTILITY FUNCTIONS =============

static void copy_string(char *dst, size_t dst_size, const char *src) {
    if (!dst || dst_size == 0) return;
    if (!src) {
        dst[0] = '\0';
        return;
    }
    snprintf(dst, dst_size, "%s", src);
}

Vector3 vector3_add(Vector3 a, Vector3 b) {
    return (Vector3){a.x + b.x, a.y + b.y, a.z + b.z};
}

float vector3_distance(Vector3 a, Vector3 b) {
    float dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
    return sqrtf(dx*dx + dy*dy + dz*dz);
}

// ============= TERRAIN SYSTEM =============

void terrain_initialize(Terrain *terrain, int width, int height) {
    terrain->vertex_count = 0;
    copy_string(terrain->texture_path, sizeof(terrain->texture_path), "assets/terrain_default.png");

    int max_x = width;
    int max_z = height;

    if (max_x < 0) max_x = 0;
    if (max_z < 0) max_z = 0;
    if (max_x > GRID_SIZE) max_x = GRID_SIZE;
    if (max_z > GRID_SIZE) max_z = GRID_SIZE;

    for (int x = 0; x < max_x; x++) {
        for (int z = 0; z < max_z; z++) {
            terrain->height_map[x][z] = sinf(x * 0.1f) * cosf(z * 0.1f) * 5.0f;
        }
    }
}

void terrain_set_height(Terrain *terrain, int x, int z, float height) {
    if (x >= 0 && x < GRID_SIZE && z >= 0 && z < GRID_SIZE) {
        terrain->height_map[x][z] = height;
    }
}

void terrain_set_texture(Terrain *terrain, const char *texture_path) {
    copy_string(terrain->texture_path, sizeof(terrain->texture_path), texture_path);
}

// ============= ENTITY/PREFAB SYSTEM =============

void entity_create(GameWorld *world, const char *name, const char *prefab_path,
                   Vector3 pos, int entity_type) {
    if (world->entity_count >= MAX_ENTITIES) return;

    Entity *e = &world->entities[world->entity_count];
    e->id = world->entity_count;
    copy_string(e->name, sizeof(e->name), name);
    copy_string(e->prefab_path, sizeof(e->prefab_path), prefab_path);
    e->transform.position = pos;
    e->transform.scale = (Vector3){1, 1, 1};
    e->entity_type = entity_type;
    e->is_active = 1;
    e->update_func = NULL;
    e->interact_func = NULL;

    world->entity_count++;
}

void entity_set_sprite(Entity *entity, const char *sprite_path) {
    copy_string(entity->sprite_path, sizeof(entity->sprite_path), sprite_path);
}

void entity_assign_ai_script(Entity *entity, void (*ai_func)(Entity*)) {
    entity->update_func = ai_func;
}

void entity_assign_interaction_script(Entity *entity, void (*interact_func)(Entity*)) {
    entity->interact_func = interact_func;
}

void entity_update_all(GameWorld *world) {
    for (int i = 0; i < world->entity_count; i++) {
        Entity *e = &world->entities[i];
        if (e->is_active && e->update_func) {
            e->update_func(e);
        }
    }
}

// ============= MENU SYSTEM =============

void menu_initialize(Menu *menu) {
    menu->item_count = 0;
    menu->is_visible = 0;
}

void menu_add_item(Menu *menu, const char *label, int x, int y,
                   int w, int h, int (*callback)(void)) {
    if (menu->item_count >= MAX_MENU_ITEMS) return;

    MenuItem *item = &menu->items[menu->item_count];
    copy_string(item->label, sizeof(item->label), label);
    item->x = x;
    item->y = y;
    item->w = w;
    item->h = h;
    item->on_click = callback;

    menu->item_count++;
}

void menu_show(Menu *menu) {
    menu->is_visible = 1;
}

void menu_hide(Menu *menu) {
    menu->is_visible = 0;
}

// ============= SIMULATION & PLAYBACK =============

void game_update(GameWorld *world, float dt) {
    world->delta_time = dt;
    entity_update_all(world);
}

void game_play(GameWorld *world) {
    world->is_playing = 1;
}

void game_pause(GameWorld *world) {
    world->is_playing = 0;
}

// ============= VISUAL FLOW SCRIPTING =============

typedef struct {
    int id;
    char name[64];
    void (*execute)(GameWorld*);
} Script;

void script_execute(Script *script, GameWorld *world) {
    if (script->execute) {
        script->execute(world);
    }
}

// ============= EXAMPLE AI BEHAVIORS =============

void ai_patrol(Entity *entity) {
    entity->transform.position.x += 0.1f;
    if (entity->transform.position.x > 50.0f) {
        entity->transform.position.x = -50.0f;
    }
}

void ai_wander(Entity *entity) {
    entity->transform.position.x += (rand() % 3 - 1) * 0.05f;
    entity->transform.position.z += (rand() % 3 - 1) * 0.05f;
}

// ============= MAIN INITIALIZATION =============

GameWorld* game_world_create(void) {
    GameWorld *world = (GameWorld*)malloc(sizeof(GameWorld));
    if (!world) {
        return NULL;
    }

    memset(world, 0, sizeof(GameWorld));

    terrain_initialize(&world->terrain, GRID_SIZE, GRID_SIZE);
    menu_initialize(&world->main_menu);
    menu_initialize(&world->game_menu);

    return world;
}

void game_world_destroy(GameWorld *world) {
    free(world);
}

int main(void) {
    GameWorld *world = game_world_create();
    if (!world) {
        fprintf(stderr, "Failed to allocate GameWorld\n");
        return 1;
    }

    // Create example entities
    entity_create(world, "Player", "prefabs/player.prefab",
                  (Vector3){0, 1, 0}, 2);
    entity_create(world, "NPC_Guard", "prefabs/npc.prefab",
                  (Vector3){10, 1, 10}, 3);

    // Assign behaviors
    if (world->entity_count > 1) {
        world->entities[1].update_func = ai_patrol;
    }

    // Setup terrain
    terrain_set_texture(&world->terrain, "assets/grass.png");

    // Setup menus
    menu_add_item(&world->main_menu, "New Game", 100, 100, 200, 50, NULL);
    menu_add_item(&world->main_menu, "Load Game", 100, 160, 200, 50, NULL);

    printf("Game World initialized with %d entities\n", world->entity_count);

    // Simulation loop (simplified)
    for (int frame = 0; frame < 100; frame++) {
        game_update(world, 0.016f);
    }

    game_world_destroy(world);
    return 0;
}