#define _CRT_SECURE_NO_WARNINGS

#include "gravo.h"

#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

typedef enum GravoBiomeKind
{
    GRAVO_BIOME_BEDROOM_BLOCK,
    GRAVO_BIOME_BATHROOM_GLASSWAY,
    GRAVO_BIOME_BACKYARD_STATIC_GARDEN,
    GRAVO_BIOME_STREET_OF_GRIEVANCES,
    GRAVO_BIOME_DRAINAGE_MAZE,
    GRAVO_BIOME_PLAYGROUND_RUIN
} GravoBiomeKind;

typedef enum GravoEnemyTier
{
    GRAVO_ENEMY_SCUTTLER,
    GRAVO_ENEMY_HUNTER,
    GRAVO_ENEMY_WITNESS,
    GRAVO_ENEMY_ARCHIVE
} GravoEnemyTier;

typedef struct GravoWeaponProfile
{
    const wchar_t *name;
    float reach;
    float cadence;
    float poiseDamage;
} GravoWeaponProfile;

typedef struct GravoEnemyFamily
{
    const wchar_t *name;
    const char *mindName;
    const char *archetype;
    GravoEnemyTier tier;
    const wchar_t *temperament;
    int moveVariantCount;
} GravoEnemyFamily;

typedef struct GravoMirrorShrine
{
    const wchar_t *name;
    const wchar_t *growthVector;
    float respiteBias;
} GravoMirrorShrine;

typedef struct GravoNarrativeBeat
{
    const wchar_t *chapterName;
    const wchar_t *focus;
} GravoNarrativeBeat;

typedef struct GravoMoveProfile
{
    const wchar_t *name;
    int actionSlot;
    float desiredRange;
    float travelSpeed;
    const wchar_t *intent;
} GravoMoveProfile;

typedef struct GravoBiomeNode
{
    const wchar_t *name;
    float x;
    float y;
    int grantsInsight;
    int sanctuaryNode;
    const wchar_t *note;
} GravoBiomeNode;

static const GravoWeaponProfile k_gravo_weapons[] = {
    {L"Beamshot Eye", 10.5f, 0.75f, 0.35f},
    {L"Beamsword", 2.6f, 1.15f, 1.00f}
};

static const GravoEnemyFamily k_gravo_enemy_families[] = {
    {L"Scrub Swarm", "Scrub Swarm", "rushdown", GRAVO_ENEMY_SCUTTLER, L"rushdown", 12},
    {L"Porch Howlers", "Porch Howler", "flank", GRAVO_ENEMY_HUNTER, L"flank", 18},
    {L"Window Witnesses", "Window Witness", "counter", GRAVO_ENEMY_WITNESS, L"counter", 24},
    {L"Archive Reclaimers", "Archive Reclaimer", "adaptive", GRAVO_ENEMY_ARCHIVE, L"adaptive", 32}
};

static const GravoMirrorShrine k_gravo_shrines[] = {
    {L"Medicine Glass", L"stamina discipline", 0.90f},
    {L"Sink Halo", L"beam focus", 0.75f},
    {L"Closet Mercury", L"mobility control", 0.70f},
    {L"Hallway Reflection", L"nemesis insight", 0.85f}
};

static const GravoNarrativeBeat k_gravo_beats[] = {
    {L"The Punishment", L"boyhood grievance and isolation"},
    {L"The Split", L"robot persona formation under stress"},
    {L"The Neighborhood Warps", L"hallucinated streets and hostile effigies"},
    {L"The Mirrors Answer", L"self-examination and restraint"},
    {L"The Dawn Choice", L"accountability instead of escalation"}
};

static const GravoMoveProfile k_gravo_moves[] = {
    {L"Skitter Feint", 0, 6.5f, 3.4f, L"side-step and test spacing"},
    {L"Porch Hook", 1, 9.0f, 2.6f, L"circle for an angle"},
    {L"Witness Counterflash", 2, 5.0f, 2.1f, L"bait and punish"},
    {L"Archive Dive", 2, 3.4f, 4.0f, L"commit to pressure"}
};

static const GravoBiomeNode k_gravo_first_biome[] = {
    {L"Bedroom Spill", 6.0f, 0.0f, 0, 0, L"The night breaks open behind Gravo."},
    {L"Mailbox Cairn", 18.0f, 4.0f, 1, 0, L"A warped landmark records the first grievance."},
    {L"Medicine Glass", 12.5f, -2.0f, 0, 1, L"The mirror shrine offers a brief lucid refuge."},
    {L"Drain Mouth", 34.0f, -12.0f, 1, 0, L"The street folds into a deeper recursive pocket."}
};

#if defined(GRAVO_HAS_RUNTIME_DEPS)

#define GRAVO_MAX_KEYS 256
#define GRAVO_MAX_TRACKED_RIVALS 3

typedef struct GravoRivalBinding
{
    int entityId;
    int rivalIndex;
    int familyIndex;
} GravoRivalBinding;

struct GravoRuntimeState
{
    ORBEngineSandbox *sandbox;
    MindSphereRivalary rivalary;
    GravoRivalBinding rivalBindings[GRAVO_MAX_TRACKED_RIVALS];
    int rivalBindingCount;
    int keys[GRAVO_MAX_KEYS];
    int autoplayEnabled;
    int sanctuaryActive;
    int currentBiomeNode;
    int insights;
    int restraint;
    int beatIndex;
    float biomePulse;
    float sanctuaryCooldown;
    float autopilotTimer;
    int shouldClose;
    wchar_t headline[128];
    wchar_t subline[160];
};

static void gravo_copy_wstr(wchar_t *dest, size_t dest_count, const wchar_t *src)
{
    if (!dest || dest_count == 0)
    {
        return;
    }
    if (!src)
    {
        dest[0] = L'\0';
        return;
    }
    wcsncpy(dest, src, dest_count - 1);
    dest[dest_count - 1] = L'\0';
}

static float gravo_clampf(float value, float min_value, float max_value)
{
    if (value < min_value)
    {
        return min_value;
    }
    if (value > max_value)
    {
        return max_value;
    }
    return value;
}

static float gravo_distance(float ax, float ay, float bx, float by)
{
    float dx = ax - bx;
    float dy = ay - by;
    return sqrtf(dx * dx + dy * dy);
}

static ORBColor gravo_color(uint8_t r, uint8_t g, uint8_t b)
{
    ORBColor color;
    color.r = r;
    color.g = g;
    color.b = b;
    color.a = 255;
    return color;
}

static ORBRenderEntity *gravo_get_player(ORBEngineSandbox *sandbox)
{
    if (!sandbox || sandbox->playerEntityId < 0 || sandbox->playerEntityId >= sandbox->world.entityCount)
    {
        return NULL;
    }
    return &sandbox->world.entities[sandbox->playerEntityId];
}

static ORBRenderEntity *gravo_get_entity(ORBEngineSandbox *sandbox, int entity_id)
{
    if (!sandbox || entity_id < 0 || entity_id >= sandbox->world.entityCount)
    {
        return NULL;
    }
    return &sandbox->world.entities[entity_id];
}

static void gravo_set_status(ORBEngineSandbox *sandbox, const wchar_t *status)
{
    if (!sandbox)
    {
        return;
    }
    gravo_copy_wstr(sandbox->statusLine, 256, status);
}

static void gravo_configure_engine(ORBEngineSandbox *sandbox)
{
    sandbox->currentCombatMode = ORB_COMBAT_NONE;
    sandbox->showAgriculture = 0;
    sandbox->showSimulatorMenu = 0;
    sandbox->raftTraveling = 0;
    sandbox->physicsEnabled = 1;
    sandbox->physicsTimeScale = 0.75f;
    sandbox->worldVisualCoherency = 0.82f;
    sandbox->recursionDepthLimit = 3;
    sandbox->dimensionView.depthScale = 0.88f;
    sandbox->dimensionView.horizonLift = 0.18f;
    sandbox->dimensionView.spriteVerticalBias = 0.14f;
    sandbox->dimensionView.fogDensity = 0.18f;
    sandbox->dimensionView.volumetricScatter = 0.38f;
    sandbox->dimensionView.layeredFogEnabled = 1;
    sandbox->dimensionView.groundedShadowEnabled = 1;
    sandbox->dimensionView.dimensionalAnchorNodesEnabled = 1;
    sandbox->dimensionView.curvatureDepthTranslationEnabled = 1;
    sandbox->kinetics.collisionSkinWidth = 0.28f;
    sandbox->kinetics.pickupRadius = 1.8f;
    sandbox->kinetics.shelterRadius = 3.0f;
    sandbox->kinetics.aerialRecoveryWindow = 0.20f;
    sandbox->kinetics.exactMaskCollisionEnabled = 1;
    sandbox->kinetics.perFrameHitboxEnabled = 1;
    sandbox->kinetics.invisibleHitSilhouetteEnabled = 1;
    sandbox->glue.focusTurnRate = 5.5f;
    sandbox->glue.shrineProgressionBindingEnabled = 1;
    sandbox->glue.dimensionalAnchorBindingEnabled = 1;
    sandbox->glue.precisionTelemetryBindingEnabled = 1;
    gravo_set_status(sandbox, L"Gravo enters the Street of Grievances. Reach the mirror and move deeper into the block.");
}

static void gravo_add_spaces(ORBEngineSandbox *sandbox)
{
    ORBEngineWorld *world = &sandbox->world;
    ORBSpaceNode *bedroom = orb_world_add_space(world, ORB_SPACE_SURFACE, -1, L"Bedroom Block", -8.0f, 2.0f, 1.0f, 0.03f);
    ORBSpaceNode *bathroom = orb_world_add_space(world, ORB_SPACE_SIMULATOR, bedroom ? bedroom->id : -1, L"Bathroom Glassway", 14.0f, -4.0f, 0.92f, -0.05f);
    ORBSpaceNode *street = orb_world_add_space(world, ORB_SPACE_SURFACE, -1, L"Street of Grievances", 46.0f, 6.0f, 1.30f, 0.08f);
    ORBSpaceNode *drainage = orb_world_add_space(world, ORB_SPACE_RECURSIVE_POCKET, street ? street->id : -1, L"Drainage Maze", 72.0f, -26.0f, 0.74f, 0.16f);

    if (bedroom)
    {
        bedroom->breathingAmplitude = 0.05f;
        bedroom->breathingRate = 0.80f;
    }
    if (bathroom)
    {
        bathroom->breathingAmplitude = 0.18f;
        bathroom->breathingRate = 1.35f;
    }
    if (street)
    {
        street->orbitalRadius = 2.4f;
        street->orbitalSpeed = 0.22f;
    }
    if (drainage)
    {
        drainage->gravityVector.x = 0.3f;
        drainage->gravityVector.y = 0.8f;
    }

    sandbox->activeRootSpaceId = street ? street->id : 0;
}

static void gravo_add_entities(ORBEngineSandbox *sandbox)
{
    ORBEngineWorld *world = &sandbox->world;
    ORBRenderEntity *entity;

    entity = orb_world_add_entity(world, sandbox->activeRootSpaceId, ORB_ENTITY_PLAYER, L"Gravo", 4.0f, 0.0f, 1.2f, 1.8f, gravo_color(120, 235, 255));
    if (entity)
    {
        sandbox->playerEntityId = entity->id;
        entity->renderLayer = 4;
        entity->physics.enabled = 1;
        entity->physics.dynamicBody = 1;
        entity->physics.affectedByGravity = 0;
        entity->physics.massKg = 38.0f;
        entity->physics.dragCoefficient = 0.28f;
        orb_collision_make_rect(&entity->collision, -0.4f, -0.8f, 0.8f, 1.6f, RGB(120, 235, 255), 0);
    }

    entity = orb_world_add_entity(world, sandbox->activeRootSpaceId, ORB_ENTITY_GATE, L"Medicine Glass", 12.5f, -2.0f, 2.2f, 3.4f, gravo_color(210, 245, 255));
    if (entity)
    {
        entity->renderLayer = 2;
        orb_collision_make_rect(&entity->collision, -1.0f, -1.7f, 2.0f, 3.2f, RGB(210, 245, 255), 1);
    }

    entity = orb_world_add_entity(world, sandbox->activeRootSpaceId, ORB_ENTITY_DECOR, L"Mailbox Cairn", 18.0f, 4.0f, 1.4f, 2.2f, gravo_color(180, 160, 120));
    if (entity)
    {
        entity->renderLayer = 1;
    }

    entity = orb_world_add_entity(world, sandbox->activeRootSpaceId, ORB_ENTITY_DECOR, L"Drain Mouth", 34.0f, -12.0f, 2.8f, 1.1f, gravo_color(110, 130, 160));
    if (entity)
    {
        entity->renderLayer = 1;
    }

    entity = orb_world_add_entity(world, sandbox->activeRootSpaceId, ORB_ENTITY_ENEMY, L"Porch Howler", 20.0f, 6.0f, 1.5f, 2.0f, gravo_color(255, 120, 120));
    if (entity)
    {
        entity->renderLayer = 3;
        entity->physics.enabled = 1;
        entity->physics.dynamicBody = 1;
        entity->physics.massKg = 65.0f;
    }

    entity = orb_world_add_entity(world, sandbox->activeRootSpaceId, ORB_ENTITY_ENEMY, L"Window Witness", 24.0f, -4.0f, 1.4f, 1.9f, gravo_color(255, 200, 90));
    if (entity)
    {
        entity->renderLayer = 3;
        entity->physics.enabled = 1;
        entity->physics.dynamicBody = 1;
        entity->physics.massKg = 58.0f;
    }

    entity = orb_world_add_entity(world, sandbox->activeRootSpaceId, ORB_ENTITY_ENEMY, L"Archive Reclaimer", 30.0f, -8.0f, 1.8f, 2.2f, gravo_color(255, 190, 90));
    if (entity)
    {
        entity->renderLayer = 3;
        entity->physics.enabled = 1;
        entity->physics.dynamicBody = 1;
        entity->physics.massKg = 92.0f;
    }
}

void gravo_seed_sandbox(ORBEngineSandbox *sandbox)
{
    if (!sandbox)
    {
        return;
    }

    orb_sandbox_init(sandbox);
    memset(&sandbox->world, 0, sizeof(sandbox->world));
    sandbox->playerEntityId = -1;
    gravo_configure_engine(sandbox);
    gravo_add_spaces(sandbox);
    gravo_add_entities(sandbox);
    sandbox->openArena.enemyCount = 0;
}

static void gravo_update_path_progress(GravoRuntimeState *state, ORBRenderEntity *player)
{
    const GravoBiomeNode *node;
    if (!state || !player || state->currentBiomeNode >= (int)(sizeof(k_gravo_first_biome) / sizeof(k_gravo_first_biome[0])))
    {
        return;
    }

    node = &k_gravo_first_biome[state->currentBiomeNode];
    if (gravo_distance(player->position.x, player->position.y, node->x, node->y) <= 3.2f)
    {
        if (node->grantsInsight)
        {
            state->insights += 1;
        }
        if (node->sanctuaryNode)
        {
            state->restraint += 1;
        }
        if (state->beatIndex + 1 < (int)(sizeof(k_gravo_beats) / sizeof(k_gravo_beats[0])))
        {
            state->beatIndex += 1;
        }
        state->currentBiomeNode += 1;
        gravo_copy_wstr(state->headline, 128, node->name);
        gravo_copy_wstr(state->subline, 160, node->note);
        gravo_set_status(state->sandbox, node->note);
    }
}

static void gravo_step_player(GravoRuntimeState *state, float delta_seconds)
{
    ORBRenderEntity *player;
    float move_x = 0.0f;
    float move_y = 0.0f;
    float speed = state->sanctuaryActive ? 1.8f : 6.5f;

    player = gravo_get_player(state->sandbox);
    if (!player)
    {
        return;
    }

    if (state->keys['A'] || state->keys[VK_LEFT]) move_x -= 1.0f;
    if (state->keys['D'] || state->keys[VK_RIGHT]) move_x += 1.0f;
    if (state->keys['W'] || state->keys[VK_UP]) move_y -= 1.0f;
    if (state->keys['S'] || state->keys[VK_DOWN]) move_y += 1.0f;

    if (state->autoplayEnabled && move_x == 0.0f && move_y == 0.0f && state->currentBiomeNode < (int)(sizeof(k_gravo_first_biome) / sizeof(k_gravo_first_biome[0])))
    {
        const GravoBiomeNode *node = &k_gravo_first_biome[state->currentBiomeNode];
        float dx = node->x - player->position.x;
        float dy = node->y - player->position.y;
        float length = sqrtf(dx * dx + dy * dy);
        if (length > 0.001f)
        {
            move_x = dx / length;
            move_y = dy / length;
        }
    }

    player->position.x += move_x * speed * delta_seconds;
    player->position.y += move_y * speed * delta_seconds;
    player->position.x = gravo_clampf(player->position.x, -4.0f, 42.0f);
    player->position.y = gravo_clampf(player->position.y, -18.0f, 12.0f);
    orb_collision_make_rect(&player->collision, -0.4f, -0.8f, 0.8f, 1.6f, RGB(120, 235, 255), 0);

    gravo_update_path_progress(state, player);
}

static void gravo_step_sanctuary(GravoRuntimeState *state, float delta_seconds)
{
    ORBRenderEntity *player;
    float distance_to_shrine;
    ORBRenderEntity *shrine = gravo_get_entity(state->sandbox, 1);
    if (!state || !shrine)
    {
        return;
    }

    player = gravo_get_player(state->sandbox);
    if (!player)
    {
        return;
    }

    distance_to_shrine = gravo_distance(player->position.x, player->position.y, shrine->position.x, shrine->position.y);
    if (state->sanctuaryCooldown > 0.0f)
    {
        state->sanctuaryCooldown -= delta_seconds;
    }

    if (distance_to_shrine <= 3.2f && state->keys['E'] && state->sanctuaryCooldown <= 0.0f)
    {
        state->sanctuaryActive = !state->sanctuaryActive;
        state->sanctuaryCooldown = 0.35f;
        if (state->sanctuaryActive)
        {
            state->restraint += 1;
            gravo_copy_wstr(state->headline, 128, L"Mirror Respite");
            gravo_copy_wstr(state->subline, 160, L"Gravo steps into the Medicine Glass and steadies the hallucinated street.");
            gravo_set_status(state->sandbox, L"Mirror shrine active. Press E to step back into the block.");
        }
        else
        {
            gravo_set_status(state->sandbox, L"Leaving the mirror. The street remembers every wrong and every restraint.");
        }
    }
}

static void gravo_step_rivals(GravoRuntimeState *state, float delta_seconds)
{
    ORBRenderEntity *player = gravo_get_player(state->sandbox);
    int index;
    if (!state || !player)
    {
        return;
    }

    for (index = 0; index < state->rivalBindingCount; ++index)
    {
        GravoRivalBinding *binding = &state->rivalBindings[index];
        ORBRenderEntity *enemy = gravo_get_entity(state->sandbox, binding->entityId);
        RivalIdentity *rival = &state->rivalary.rivals[binding->rivalIndex];
        float dx;
        float dy;
        float distance_to_player;
        int proximity_bucket;
        int planner_state;
        int action;
        float move_speed;
        double reward;
        int move_index;
        if (!enemy)
        {
            continue;
        }

        dx = player->position.x - enemy->position.x;
        dy = player->position.y - enemy->position.y;
        distance_to_player = sqrtf(dx * dx + dy * dy);
        proximity_bucket = distance_to_player < 4.0f ? 0 : (distance_to_player < 8.0f ? 1 : (distance_to_player < 14.0f ? 2 : 3));
        planner_state = state->currentBiomeNode * 4 + proximity_bucket;
        action = mindsphere_choose_action(rival, planner_state);
        move_index = (binding->familyIndex + action) % (int)(sizeof(k_gravo_moves) / sizeof(k_gravo_moves[0]));
        move_speed = k_gravo_moves[move_index].travelSpeed * (float)(0.8 + rival->adaptability * 0.4);

        if (distance_to_player > 0.001f)
        {
            dx /= distance_to_player;
            dy /= distance_to_player;
        }

        if (action == 0)
        {
            enemy->position.x += -dy * move_speed * delta_seconds;
            enemy->position.y += dx * move_speed * delta_seconds;
        }
        else if (action == 1)
        {
            enemy->position.x += dx * move_speed * 0.65f * delta_seconds;
            enemy->position.y += dy * move_speed * 0.65f * delta_seconds;
        }
        else
        {
            enemy->position.x += dx * move_speed * 1.2f * delta_seconds;
            enemy->position.y += dy * move_speed * 1.2f * delta_seconds;
        }

        enemy->position.x = gravo_clampf(enemy->position.x, 8.0f, 40.0f);
        enemy->position.y = gravo_clampf(enemy->position.y, -16.0f, 10.0f);

        reward = distance_to_player <= k_gravo_moves[move_index].desiredRange ? 0.18 : -0.06;
        if (state->sanctuaryActive)
        {
            reward -= 0.10;
        }
        if (distance_to_player < 2.4f && action == 2)
        {
            reward += 0.22;
        }
        mindsphere_record_outcome(&state->rivalary, rival, planner_state, action, reward, planner_state, 0);
    }
}

static void gravo_sync_overlay(GravoRuntimeState *state)
{
    if (!state)
    {
        return;
    }

    if (!state->headline[0])
    {
        gravo_copy_wstr(state->headline, 128, L"Street of Grievances");
    }
    if (!state->subline[0])
    {
        gravo_copy_wstr(state->subline, 160, k_gravo_beats[state->beatIndex].focus);
    }
}

GravoRuntimeState *gravo_runtime_create(ORBEngineSandbox *sandbox, int autoplayEnabled)
{
    GravoRuntimeState *state;
    if (!sandbox)
    {
        return NULL;
    }

    state = (GravoRuntimeState*)calloc(1, sizeof(*state));
    if (!state)
    {
        return NULL;
    }

    state->sandbox = sandbox;
    state->autoplayEnabled = autoplayEnabled;
    state->beatIndex = 0;
    gravo_seed_sandbox(sandbox);

    if (!mindsphere_init(&state->rivalary, GRAVO_MAX_TRACKED_RIVALS))
    {
        free(state);
        return NULL;
    }

    mindsphere_add_rival(&state->rivalary, k_gravo_enemy_families[1].mindName, k_gravo_enemy_families[1].archetype, 101u);
    mindsphere_add_rival(&state->rivalary, k_gravo_enemy_families[2].mindName, k_gravo_enemy_families[2].archetype, 202u);
    mindsphere_add_rival(&state->rivalary, k_gravo_enemy_families[3].mindName, k_gravo_enemy_families[3].archetype, 303u);

    state->rivalBindingCount = 3;
    state->rivalBindings[0].entityId = 4;
    state->rivalBindings[0].rivalIndex = 0;
    state->rivalBindings[0].familyIndex = 1;
    state->rivalBindings[1].entityId = 5;
    state->rivalBindings[1].rivalIndex = 1;
    state->rivalBindings[1].familyIndex = 2;
    state->rivalBindings[2].entityId = 6;
    state->rivalBindings[2].rivalIndex = 2;
    state->rivalBindings[2].familyIndex = 3;

    gravo_copy_wstr(state->headline, 128, L"Street of Grievances");
    gravo_copy_wstr(state->subline, 160, L"Move with WASD or arrows. Press E at the mirror shrine for respite.");
    return state;
}

void gravo_runtime_destroy(GravoRuntimeState *state)
{
    if (!state)
    {
        return;
    }
    mindsphere_free(&state->rivalary);
    free(state);
}

void gravo_runtime_step(GravoRuntimeState *state, float deltaSeconds)
{
    if (!state)
    {
        return;
    }

    state->biomePulse += deltaSeconds;
    state->autopilotTimer += deltaSeconds;

    gravo_step_player(state, deltaSeconds);
    gravo_step_sanctuary(state, deltaSeconds);
    if (!state->sanctuaryActive)
    {
        gravo_step_rivals(state, deltaSeconds);
    }
    gravo_sync_overlay(state);

    if (state->currentBiomeNode >= (int)(sizeof(k_gravo_first_biome) / sizeof(k_gravo_first_biome[0])) && state->autoplayEnabled)
    {
        state->shouldClose = 1;
    }
}

void gravo_runtime_render(GravoRuntimeState *state, HDC hdc, RECT clientRect)
{
    RECT panel;
    RECT subpanel;
    int text_y;
    wchar_t line[256];
    ORBRenderEntity *player;
    HBRUSH panel_brush;
    HBRUSH frame_brush;
    HBRUSH subpanel_brush;
    HBRUSH subframe_brush;
    if (!state)
    {
        return;
    }

    panel.left = 28;
    panel.top = 24;
    panel.right = clientRect.right - 28;
    panel.bottom = 124;
    subpanel.left = 28;
    subpanel.top = clientRect.bottom - 164;
    subpanel.right = clientRect.right - 28;
    subpanel.bottom = clientRect.bottom - 28;

    panel_brush = CreateSolidBrush(RGB(12, 18, 30));
    frame_brush = CreateSolidBrush(RGB(120, 235, 255));
    subpanel_brush = CreateSolidBrush(RGB(18, 16, 26));
    subframe_brush = CreateSolidBrush(RGB(255, 190, 90));
    FillRect(hdc, &panel, panel_brush);
    FrameRect(hdc, &panel, frame_brush);
    FillRect(hdc, &subpanel, subpanel_brush);
    FrameRect(hdc, &subpanel, subframe_brush);
    DeleteObject(panel_brush);
    DeleteObject(frame_brush);
    DeleteObject(subpanel_brush);
    DeleteObject(subframe_brush);
    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, RGB(236, 242, 255));

    TextOutW(hdc, 42, 36, state->headline, (int)wcslen(state->headline));
    TextOutW(hdc, 42, 62, state->subline, (int)wcslen(state->subline));
    _snwprintf(line, 256, L"Weapons: %ls / %ls | Insight %d | Restraint %d | Shrine %ls", k_gravo_weapons[0].name, k_gravo_weapons[1].name, state->insights, state->restraint, state->sanctuaryActive ? L"ACTIVE" : L"READY");
    line[255] = 0;
    TextOutW(hdc, 42, 88, line, (int)wcslen(line));

    text_y = clientRect.bottom - 152;
    _snwprintf(line, 256, L"Biome Loop: %ls", state->currentBiomeNode < (int)(sizeof(k_gravo_first_biome) / sizeof(k_gravo_first_biome[0])) ? k_gravo_first_biome[state->currentBiomeNode].name : L"Drainage descent unlocked");
    line[255] = 0;
    TextOutW(hdc, 42, text_y, line, (int)wcslen(line));
    text_y += 24;
    _snwprintf(line, 256, L"Narrative Beat: %ls", k_gravo_beats[state->beatIndex].chapterName);
    line[255] = 0;
    TextOutW(hdc, 42, text_y, line, (int)wcslen(line));
    text_y += 24;
    if (state->rivalary.count > 0)
    {
        _snwprintf(line, 256, L"MindSphereRivalary Lead: %S threat=%.2f", state->rivalary.rivals[0].name, mindsphere_compute_threat(&state->rivalary.rivals[0]));
        line[255] = 0;
        TextOutW(hdc, 42, text_y, line, (int)wcslen(line));
    }

    player = gravo_get_player(state->sandbox);
    if (player)
    {
        _snwprintf(line, 256, L"Player Position: (%.1f, %.1f)", player->position.x, player->position.y);
        line[255] = 0;
        TextOutW(hdc, clientRect.right - 260, clientRect.bottom - 60, line, (int)wcslen(line));
    }
}

void gravo_runtime_key_down(GravoRuntimeState *state, WPARAM key)
{
    if (!state)
    {
        return;
    }
    if (key < GRAVO_MAX_KEYS)
    {
        state->keys[key] = 1;
    }
    if (key == VK_ESCAPE)
    {
        state->shouldClose = 1;
    }
}

void gravo_runtime_key_up(GravoRuntimeState *state, WPARAM key)
{
    if (!state)
    {
        return;
    }
    if (key < GRAVO_MAX_KEYS)
    {
        state->keys[key] = 0;
    }
}

int gravo_runtime_should_close(GravoRuntimeState *state)
{
    return state ? state->shouldClose : 0;
}

#else

struct GravoRuntimeState
{
    int unused;
};

void gravo_seed_sandbox(ORBEngineSandbox *sandbox)
{
    (void)sandbox;
}

GravoRuntimeState *gravo_runtime_create(ORBEngineSandbox *sandbox, int autoplayEnabled)
{
    (void)sandbox;
    (void)autoplayEnabled;
    return NULL;
}

void gravo_runtime_destroy(GravoRuntimeState *state)
{
    (void)state;
}

void gravo_runtime_step(GravoRuntimeState *state, float deltaSeconds)
{
    (void)state;
    (void)deltaSeconds;
}

void gravo_runtime_render(GravoRuntimeState *state, HDC hdc, RECT clientRect)
{
    (void)state;
    (void)hdc;
    (void)clientRect;
}

void gravo_runtime_key_down(GravoRuntimeState *state, WPARAM key)
{
    (void)state;
    (void)key;
}

void gravo_runtime_key_up(GravoRuntimeState *state, WPARAM key)
{
    (void)state;
    (void)key;
}

int gravo_runtime_should_close(GravoRuntimeState *state)
{
    (void)state;
    return 0;
}

#endif

const wchar_t *gravo_get_concept_summary(void)
{
    return L"Gravo: Boy Dimenhyde is a surreal real-time action-horror concept for ORBEngine. The working version centers a frightened child externalizing into the robot avatar Gravo, fighting hostile nightmare effigies across a warped neighborhood with beamshot-eye ranged pressure, beamsword melee spacing, mirror-shrine respite, and a bossless MindSphereRivalary enemy ecology.";
}

int gravo_get_weapon_count(void)
{
    return (int)(sizeof(k_gravo_weapons) / sizeof(k_gravo_weapons[0]));
}

int gravo_get_shrine_count(void)
{
    return (int)(sizeof(k_gravo_shrines) / sizeof(k_gravo_shrines[0]));
}

int gravo_get_narrative_beat_count(void)
{
    return (int)(sizeof(k_gravo_beats) / sizeof(k_gravo_beats[0]));
}

int gravo_get_biome_count(void)
{
    return 6;
}

int gravo_get_enemy_family_count(void)
{
    return (int)(sizeof(k_gravo_enemy_families) / sizeof(k_gravo_enemy_families[0]));
}