#define _CRT_SECURE_NO_WARNINGS

#include "../include/orbengine.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#define ORB_WORLD_WIDTH 1024.0f
#define ORB_WORLD_HEIGHT 768.0f
#define ORB_PI 3.1415926535f
#define ORB_GRAVITATIONAL_CONSTANT 6.67430e-11f
#define ORB_COULOMB_CONSTANT 8.9875517923e9f
#define ORB_BOLTZMANN_CONSTANT 1.380649e-23f
#define ORB_SPEED_OF_LIGHT 299792458.0f
#define ORB_PHYSICS_SOFTENING_METERS 0.05f

static ORBColor orb_make_color(uint8_t r, uint8_t g, uint8_t b, uint8_t a);
static ORBVec2 orb_vec2_add(ORBVec2 a, ORBVec2 b);
static ORBVec2 orb_vec2_sub(ORBVec2 a, ORBVec2 b);
static ORBVec2 orb_vec2_scale(ORBVec2 value, float scalar);
static float orb_vec2_length_sq(ORBVec2 value);
static float orb_vec2_length(ORBVec2 value);
static ORBVec2 orb_vec2_normalize(ORBVec2 value);
static float orb_clampf(float value, float minValue, float maxValue);
static float orb_lerp(float a, float b, float t);
static int orb_round_to_int(float value);
static float orb_random_signed(void);
static COLORREF orb_colorref_from_orb(ORBColor color);
static COLORREF orb_lerp_color(COLORREF a, COLORREF b, float t);
static ORBSpaceNode *orb_get_space(ORBEngineWorld *world, int id);
static void orb_configure_entity_body(ORBRenderEntity *entity, ORBScaleDomain scaleDomain, float metersPerWorldUnit, float massKg, float chargeCoulombs, float temperatureKelvin, float dragCoefficient, float areaSquareMeters, float radiusMeters, int dynamicBody, int pinned, float anchorSpring, float anchorDamping, float cohesion, int affectedByThermal);
static void orb_sync_entity_collision(ORBRenderEntity *entity);
static float orb_compute_relativistic_gamma(ORBRenderEntity *entity);
static void orb_step_world_physics(ORBEngineSandbox *sandbox, float deltaSeconds);
static void orb_apply_space_forces(ORBRenderEntity *entity, const ORBSpaceNode *space);
static void orb_apply_anchor_force(ORBRenderEntity *entity);
static void orb_apply_drag_force(ORBRenderEntity *entity, const ORBSpaceNode *space);
static void orb_apply_thermal_motion(ORBRenderEntity *entity, const ORBSpaceNode *space, float deltaSeconds);
static void orb_apply_pair_force(ORBRenderEntity *a, ORBRenderEntity *b);
static void orb_integrate_entity(ORBRenderEntity *entity, float deltaSeconds);
static void orb_constrain_entity_to_space(ORBRenderEntity *entity);
static float orb_measure_entity_coherency(const ORBRenderEntity *entity);
static void orb_step_open_arena(ORBEngineSandbox *sandbox, float deltaSeconds);
static void orb_add_default_spaces(ORBEngineSandbox *sandbox);
static void orb_add_default_entities(ORBEngineSandbox *sandbox);
static void orb_generate_open_arena(ORBEngineSandbox *sandbox, int seed);
static void orb_set_status(ORBEngineSandbox *sandbox, const wchar_t *status);
static int orb_select_root_space(const ORBEngineSandbox *sandbox);
static void orb_draw_surface_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect);
static void orb_draw_agriculture_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect);
static void orb_draw_simulator_menu(ORBEngineSandbox *sandbox, HDC hdc, RECT rect);
static void orb_draw_tactical_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect);
static void orb_draw_qte_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect);
static void orb_draw_open_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect);
static void orb_draw_scene_frame(ORBEngineSandbox *sandbox, HDC hdc, RECT rect, int rootSpaceId, const wchar_t *title, const wchar_t *subtitle);
static void orb_render_space_recursive(ORBEngineSandbox *sandbox, HDC hdc, RECT viewport, int spaceId, int depth);
static RECT orb_compute_child_viewport(ORBEngineSandbox *sandbox, const ORBSpaceNode *parent, const ORBSpaceNode *child, RECT parentViewport, int childIndex, int depth);
static void orb_draw_space_backdrop(ORBEngineSandbox *sandbox, HDC hdc, const ORBSpaceNode *space, RECT viewport, int depth, float breathScale, float orbitAngle);
static void orb_draw_mode7_floor(ORBEngineSandbox *sandbox, HDC hdc, const ORBSpaceNode *space, RECT viewport, int depth, float breathScale, float orbitAngle);
static void orb_draw_space_entities(ORBEngineSandbox *sandbox, HDC hdc, const ORBSpaceNode *space, RECT viewport, int depth, float breathScale, float orbitAngle);
static void orb_draw_entity_projection(HDC hdc, const ORBSpaceNode *space, const ORBRenderEntity *entity, RECT viewport, int depth, float breathScale, float orbitAngle);
static void orb_draw_space_border(HDC hdc, RECT viewport, COLORREF color);
static void orb_draw_orbital_rings(HDC hdc, RECT viewport, COLORREF color, float orbitAngle, int depth);
static int orb_ui_bitmap_ready(const ORBUIBitmapAsset *asset);
static void orb_draw_bitmap_asset(HDC hdc, const ORBUIBitmapAsset *asset, RECT rect, BYTE alpha);
static void orb_draw_bitmap_asset_region(HDC hdc, const ORBUIBitmapAsset *asset, RECT rect, RECT sourceRect, BYTE alpha);
static const ORBUIBitmapAsset *orb_get_toolbar_asset(const ORBEngineSandbox *sandbox);
static void orb_draw_ui_chrome(ORBEngineSandbox *sandbox, HDC hdc, RECT rect);
static void orb_draw_overlay_panel(ORBEngineSandbox *sandbox, HDC hdc, RECT rect, COLORREF panelColor, COLORREF borderColor, const ORBUIBitmapAsset *asset);
static void orb_draw_status_bar(ORBEngineSandbox *sandbox, HDC hdc, RECT clientRect, const wchar_t *text);
static void orb_fill_rect(HDC hdc, int left, int top, int right, int bottom, COLORREF color);
static int orb_resolve_font_glyph(const ORBUIShellAssets *uiShell, wchar_t glyph, const ORBUIBitmapAsset **asset, int *glyphIndex);
static int orb_draw_atlas_text(ORBEngineSandbox *sandbox, HDC hdc, int x, int y, COLORREF color, const wchar_t *text, int glyphHeight);
static void orb_draw_label_sized(ORBEngineSandbox *sandbox, HDC hdc, int x, int y, COLORREF color, const wchar_t *text, int glyphHeight);
static void orb_draw_label(ORBEngineSandbox *sandbox, HDC hdc, int x, int y, COLORREF color, const wchar_t *text);

void orb_vec2_set(ORBVec2 *value, float x, float y)
{
    value->x = x;
    value->y = y;
}

void orb_collision_make_rect(ORBCollisionShape *shape, float x, float y, float width, float height, COLORREF debugColor, int usesGreenBoundary)
{
    shape->pointCount = 4;
    orb_vec2_set(&shape->points[0], x, y);
    orb_vec2_set(&shape->points[1], x + width, y);
    orb_vec2_set(&shape->points[2], x + width, y + height);
    orb_vec2_set(&shape->points[3], x, y + height);
    shape->debugColor = debugColor;
    shape->usesGreenBoundary = usesGreenBoundary;
}

void orb_world_init(ORBEngineWorld *world)
{
    ZeroMemory(world, sizeof(*world));
}

ORBSpaceNode *orb_world_add_space(ORBEngineWorld *world, ORBSpaceKind kind, int parentId, const wchar_t *name, float x, float y, float scale, float rotationWarp)
{
    ORBSpaceNode *space;
    if (world->spaceCount >= ORB_MAX_SPACE_NODES)
    {
        return NULL;
    }

    space = &world->spaces[world->spaceCount];
    ZeroMemory(space, sizeof(*space));
    space->id = world->spaceCount;
    space->parentId = parentId;
    space->kind = kind;
    orb_vec2_set(&space->origin, x, y);
    space->scale = scale;
    space->rotationWarp = rotationWarp;
    space->breathingAmplitude = 0.03f;
    space->breathingRate = 1.0f;
    space->orbitalRadius = 0.0f;
    space->orbitalSpeed = 0.0f;
    wcsncpy(space->name, name, 63);
    space->name[63] = 0;

    if (parentId >= 0 && parentId < world->spaceCount)
    {
        ORBSpaceNode *parent = &world->spaces[parentId];
        if (parent->childCount < ORB_MAX_CHILDREN)
        {
            parent->childIds[parent->childCount++] = space->id;
        }
    }

    world->spaceCount += 1;
    return space;
}

ORBRenderEntity *orb_world_add_entity(ORBEngineWorld *world, int spaceId, ORBEntityKind kind, const wchar_t *label, float x, float y, float width, float height, ORBColor tint)
{
    ORBRenderEntity *entity;
    if (world->entityCount >= ORB_MAX_ENTITIES)
    {
        return NULL;
    }

    entity = &world->entities[world->entityCount];
    ZeroMemory(entity, sizeof(*entity));
    entity->id = world->entityCount;
    entity->spaceId = spaceId;
    entity->kind = kind;
    entity->active = 1;
    entity->renderLayer = 0;
    entity->depthBias = 0.0f;
    orb_vec2_set(&entity->position, x, y);
    orb_vec2_set(&entity->size, width, height);
    entity->tint = tint;
    orb_collision_make_rect(&entity->collision, x, y, width, height, RGB(0, 255, 0), 1);
    wcsncpy(entity->label, label, 63);
    entity->label[63] = 0;
    world->entityCount += 1;
    return entity;
}

void orb_apply_innsmouth_profiles(ORBEngineSandbox *sandbox)
{
    sandbox->dimensionView.depthScale = 1.18f;
    sandbox->dimensionView.horizonLift = 0.12f;
    sandbox->dimensionView.spriteVerticalBias = 0.08f;
    sandbox->dimensionView.fogDensity = 0.34f;
    sandbox->dimensionView.volumetricScatter = 0.48f;
    sandbox->dimensionView.collisionVisualInset = 3.0f;
    sandbox->dimensionView.anchorNodeShearBias = 0.22f;
    sandbox->dimensionView.layeredFogEnabled = 1;
    sandbox->dimensionView.spriteShearEnabled = 1;
    sandbox->dimensionView.groundedShadowEnabled = 1;
    sandbox->dimensionView.dimensionalAnchorNodesEnabled = 1;
    sandbox->dimensionView.curvatureDepthTranslationEnabled = 1;
    sandbox->dimensionView.topCapTetherProjectionEnabled = 1;

    sandbox->kinetics.collisionSkinWidth = 2.0f;
    sandbox->kinetics.pickupRadius = 28.0f;
    sandbox->kinetics.shelterRadius = 64.0f;
    sandbox->kinetics.projectileHeightBias = 10.0f;
    sandbox->kinetics.aerialRecoveryWindow = 0.16f;
    sandbox->kinetics.silhouettePrecisionBias = 0.92f;
    sandbox->kinetics.exactMaskCollisionEnabled = 1;
    sandbox->kinetics.perFrameHitboxEnabled = 1;
    sandbox->kinetics.authoredSurfaceTagsEnabled = 1;
    sandbox->kinetics.invisibleHitSilhouetteEnabled = 1;
    sandbox->kinetics.anchorLinkedCollisionEnabled = 1;
    sandbox->kinetics.pixelPreciseDetectionIntentEnabled = 1;

    sandbox->glue.focusTurnRate = 3.0f;
    sandbox->glue.moistureHealingBias = 0.85f;
    sandbox->glue.breathingResonanceBias = 1.10f;
    sandbox->glue.audioZoneBindingEnabled = 1;
    sandbox->glue.animationCollisionBindingEnabled = 1;
    sandbox->glue.shrineProgressionBindingEnabled = 1;
    sandbox->glue.codexDiscoveryBindingEnabled = 1;
    sandbox->glue.dimensionalAnchorBindingEnabled = 1;
    sandbox->glue.equipmentSocketBindingEnabled = 1;
    sandbox->glue.precisionTelemetryBindingEnabled = 1;
}

void orb_sandbox_init(ORBEngineSandbox *sandbox)
{
    ZeroMemory(sandbox, sizeof(*sandbox));
    orb_world_init(&sandbox->world);
    sandbox->currentCombatMode = ORB_COMBAT_NONE;
    sandbox->tacticalPlayerHp = 30;
    sandbox->tacticalEnemyHp = 24;
    sandbox->recursionDepthLimit = 3;
    sandbox->activeRootSpaceId = 0;
    sandbox->physicsEnabled = 1;
    sandbox->physicsTimeScale = 1.0f;
    sandbox->worldVisualCoherency = 1.0f;
    orb_apply_innsmouth_profiles(sandbox);
    wcscpy(sandbox->qteSequence, L"ASDJKL");
    sandbox->qteLength = 6;
    sandbox->qteIndex = 0;
    orb_add_default_spaces(sandbox);
    orb_add_default_entities(sandbox);
    orb_generate_open_arena(sandbox, 7);
    orb_set_status(sandbox, L"ORBEngine sandbox ready. ORBdimensionView anchors depth translation, ORBKinetics owns invisible silhouettes, and ORBGlue binds those authored signals to gameplay and equipment state.");
}

void orb_sandbox_step(ORBEngineSandbox *sandbox, float deltaSeconds)
{
    deltaSeconds = orb_clampf(deltaSeconds, 0.001f, 0.05f);
    sandbox->renderTime += deltaSeconds * sandbox->physicsTimeScale;

    if (sandbox->physicsEnabled)
    {
        orb_step_world_physics(sandbox, deltaSeconds * sandbox->physicsTimeScale);
        if (sandbox->currentCombatMode == ORB_COMBAT_OPEN)
        {
            orb_step_open_arena(sandbox, deltaSeconds * sandbox->physicsTimeScale);
        }
    }

    sandbox->activeRootSpaceId = orb_select_root_space(sandbox);

    if (sandbox->raftTraveling)
    {
        sandbox->raftTravelProgress += deltaSeconds * 0.55f;
        if (sandbox->raftTravelProgress >= 1.0f)
        {
            sandbox->raftTravelProgress = 1.0f;
            sandbox->raftTraveling = 0;
            sandbox->playerOnRaft = 0;
            sandbox->showSimulatorMenu = 1;
            sandbox->currentCombatMode = ORB_COMBAT_NONE;
            sandbox->activeRootSpaceId = 2;
            orb_set_status(sandbox, L"Arrived at simulator shore. Choose Tactical [1], QTE [2], or Open [3].");
        }
    }
}

void orb_sandbox_handle_key(ORBEngineSandbox *sandbox, WPARAM key)
{
    if (key == 'G')
    {
        sandbox->showAgriculture = !sandbox->showAgriculture;
        sandbox->showSimulatorMenu = 0;
        sandbox->currentCombatMode = ORB_COMBAT_NONE;
        sandbox->activeRootSpaceId = sandbox->showAgriculture ? 1 : 0;
        orb_set_status(sandbox,
                       sandbox->showAgriculture
                           ? L"Agriculture complex opened. Breathing depth and orbital recursion remain active under the island."
                           : L"Returned to island surface root view.");
        return;
    }

    if (key == 'R' && !sandbox->showAgriculture && !sandbox->raftTraveling && !sandbox->showSimulatorMenu)
    {
        sandbox->playerOnRaft = 1;
        sandbox->raftTraveling = 1;
        sandbox->raftTravelProgress = 0.0f;
        sandbox->activeRootSpaceId = 0;
        orb_set_status(sandbox, L"Raft leaving island shore for the combat simulator gate.");
        return;
    }

    if (key == VK_ESCAPE)
    {
        sandbox->showSimulatorMenu = 0;
        sandbox->showAgriculture = 0;
        sandbox->currentCombatMode = ORB_COMBAT_NONE;
        sandbox->activeRootSpaceId = 0;
        orb_set_status(sandbox, L"Returned to island sandbox root view.");
        return;
    }

    if (sandbox->showSimulatorMenu)
    {
        if (key == '1')
        {
            sandbox->currentCombatMode = ORB_COMBAT_TACTICAL;
            sandbox->showSimulatorMenu = 0;
            sandbox->activeRootSpaceId = 3;
            sandbox->tacticalPlayerHp = 30;
            sandbox->tacticalEnemyHp = 24;
            orb_set_status(sandbox, L"Tactical simulator loaded. Press A to attack, D to defend, ESC to leave.");
        }
        else if (key == '2')
        {
            sandbox->currentCombatMode = ORB_COMBAT_QTE;
            sandbox->showSimulatorMenu = 0;
            sandbox->activeRootSpaceId = 3;
            sandbox->qteIndex = 0;
            orb_set_status(sandbox, L"QTE simulator loaded. Match the OrbGuardian key string from left to right.");
        }
        else if (key == '3')
        {
            sandbox->currentCombatMode = ORB_COMBAT_OPEN;
            sandbox->showSimulatorMenu = 0;
            sandbox->activeRootSpaceId = 3;
            orb_generate_open_arena(sandbox, sandbox->openArena.seed + 11);
            orb_set_status(sandbox, L"Open combat simulator loaded. Procedural arena generated for real-time combat testing.");
        }
        return;
    }

    if (sandbox->currentCombatMode == ORB_COMBAT_TACTICAL)
    {
        if (key == 'A')
        {
            sandbox->tacticalEnemyHp -= 6;
            if (sandbox->tacticalEnemyHp > 0)
            {
                sandbox->tacticalPlayerHp -= 4;
                orb_set_status(sandbox, L"Tactical attack exchange resolved. Continue testing turn order and response rules.");
            }
            else
            {
                orb_set_status(sandbox, L"Tactical simulator victory. Reset from simulator menu when ready.");
            }
        }
        else if (key == 'D')
        {
            sandbox->tacticalPlayerHp -= 1;
            orb_set_status(sandbox, L"Defense stance held. Reduced damage confirms simple turn-based mitigation path.");
        }
        return;
    }

    if (sandbox->currentCombatMode == ORB_COMBAT_QTE)
    {
        wchar_t expected = sandbox->qteSequence[sandbox->qteIndex];
        if ((wchar_t)key == expected)
        {
            sandbox->qteIndex += 1;
            if (sandbox->qteIndex >= sandbox->qteLength)
            {
                orb_set_status(sandbox, L"OrbGuardian QTE simulation cleared. Timing chain validated for current sandbox rules.");
            }
        }
        else if ((wchar_t)key >= 'A' && (wchar_t)key <= 'Z')
        {
            sandbox->qteIndex = 0;
            orb_set_status(sandbox, L"QTE sequence broken. Reset to verify failure and retry pacing.");
        }
        return;
    }

    if (sandbox->currentCombatMode == ORB_COMBAT_OPEN)
    {
        if (key == 'N')
        {
            orb_generate_open_arena(sandbox, sandbox->openArena.seed + 5);
            orb_set_status(sandbox, L"Generated a new open-combat procedural test arena.");
        }
        return;
    }
}

void orb_sandbox_render(ORBEngineSandbox *sandbox, HDC hdc, RECT clientRect)
{
    HBRUSH background = CreateSolidBrush(RGB(14, 18, 28));
    FillRect(hdc, &clientRect, background);
    DeleteObject(background);

    if (sandbox->showAgriculture)
    {
        orb_draw_agriculture_scene(sandbox, hdc, clientRect);
    }
    else if (sandbox->raftTraveling)
    {
        orb_draw_surface_scene(sandbox, hdc, clientRect);
        orb_draw_label(sandbox, hdc, 40, 98, RGB(230, 235, 240), L"Traveling by raft through the surface recursion lane to the combat simulator gate...");
    }
    else if (sandbox->showSimulatorMenu)
    {
        orb_draw_simulator_menu(sandbox, hdc, clientRect);
    }
    else if (sandbox->currentCombatMode == ORB_COMBAT_TACTICAL)
    {
        orb_draw_tactical_scene(sandbox, hdc, clientRect);
    }
    else if (sandbox->currentCombatMode == ORB_COMBAT_QTE)
    {
        orb_draw_qte_scene(sandbox, hdc, clientRect);
    }
    else if (sandbox->currentCombatMode == ORB_COMBAT_OPEN)
    {
        orb_draw_open_scene(sandbox, hdc, clientRect);
    }
    else
    {
        orb_draw_surface_scene(sandbox, hdc, clientRect);
    }

    orb_draw_status_bar(sandbox, hdc, clientRect, sandbox->statusLine);
}

static ORBColor orb_make_color(uint8_t r, uint8_t g, uint8_t b, uint8_t a)
{
    ORBColor color;
    color.r = r;
    color.g = g;
    color.b = b;
    color.a = a;
    return color;
}

static ORBVec2 orb_vec2_add(ORBVec2 a, ORBVec2 b)
{
    ORBVec2 result;
    result.x = a.x + b.x;
    result.y = a.y + b.y;
    return result;
}

static ORBVec2 orb_vec2_sub(ORBVec2 a, ORBVec2 b)
{
    ORBVec2 result;
    result.x = a.x - b.x;
    result.y = a.y - b.y;
    return result;
}

static ORBVec2 orb_vec2_scale(ORBVec2 value, float scalar)
{
    ORBVec2 result;
    result.x = value.x * scalar;
    result.y = value.y * scalar;
    return result;
}

static float orb_vec2_length_sq(ORBVec2 value)
{
    return value.x * value.x + value.y * value.y;
}

static float orb_vec2_length(ORBVec2 value)
{
    return sqrtf(orb_vec2_length_sq(value));
}

static ORBVec2 orb_vec2_normalize(ORBVec2 value)
{
    float length = orb_vec2_length(value);
    ORBVec2 result;

    if (length <= 0.00001f)
    {
        orb_vec2_set(&result, 0.0f, 0.0f);
        return result;
    }

    result = orb_vec2_scale(value, 1.0f / length);
    return result;
}

static float orb_clampf(float value, float minValue, float maxValue)
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

static float orb_lerp(float a, float b, float t)
{
    return a + (b - a) * t;
}

static int orb_round_to_int(float value)
{
    return (int)(value >= 0.0f ? value + 0.5f : value - 0.5f);
}

static float orb_random_signed(void)
{
    return ((float)rand() / (float)RAND_MAX) * 2.0f - 1.0f;
}

static COLORREF orb_colorref_from_orb(ORBColor color)
{
    return RGB(color.r, color.g, color.b);
}

static COLORREF orb_lerp_color(COLORREF a, COLORREF b, float t)
{
    int r = orb_round_to_int(orb_lerp((float)GetRValue(a), (float)GetRValue(b), t));
    int g = orb_round_to_int(orb_lerp((float)GetGValue(a), (float)GetGValue(b), t));
    int bValue = orb_round_to_int(orb_lerp((float)GetBValue(a), (float)GetBValue(b), t));
    return RGB(r, g, bValue);
}

static ORBSpaceNode *orb_get_space(ORBEngineWorld *world, int id)
{
    if (!world || id < 0 || id >= world->spaceCount)
    {
        return NULL;
    }
    return &world->spaces[id];
}

static void orb_configure_entity_body(ORBRenderEntity *entity, ORBScaleDomain scaleDomain, float metersPerWorldUnit, float massKg, float chargeCoulombs, float temperatureKelvin, float dragCoefficient, float areaSquareMeters, float radiusMeters, int dynamicBody, int pinned, float anchorSpring, float anchorDamping, float cohesion, int affectedByThermal)
{
    ORBPhysicsBody *body;

    if (!entity)
    {
        return;
    }

    body = &entity->physics;
    ZeroMemory(body, sizeof(*body));
    body->enabled = 1;
    body->dynamicBody = dynamicBody;
    body->pinned = pinned;
    body->affectedByGravity = dynamicBody;
    body->affectedByCharge = (chargeCoulombs != 0.0f);
    body->affectedByThermal = affectedByThermal;
    body->scaleDomain = scaleDomain;
    body->metersPerWorldUnit = metersPerWorldUnit;
    body->massKg = massKg;
    body->chargeCoulombs = chargeCoulombs;
    body->temperatureKelvin = temperatureKelvin;
    body->dragCoefficient = dragCoefficient;
    body->areaSquareMeters = areaSquareMeters;
    body->restitution = 0.22f;
    body->cohesion = cohesion;
    body->anchorSpring = anchorSpring;
    body->anchorDamping = anchorDamping;
    body->radiusMeters = radiusMeters;
    body->anchorPosition = entity->position;
    body->visualEnergy = 0.0f;
}

static void orb_sync_entity_collision(ORBRenderEntity *entity)
{
    COLORREF debugColor;

    if (!entity)
    {
        return;
    }

    debugColor = entity->collision.debugColor ? entity->collision.debugColor : RGB(0, 255, 0);
    orb_collision_make_rect(
        &entity->collision,
        entity->position.x - entity->size.x * 0.5f,
        entity->position.y - entity->size.y,
        entity->size.x,
        entity->size.y,
        debugColor,
        entity->collision.usesGreenBoundary);
}

static float orb_compute_relativistic_gamma(ORBRenderEntity *entity)
{
    ORBPhysicsBody *body;
    float speedMetersPerSecond;
    float ratio;

    if (!entity || !entity->physics.enabled)
    {
        return 1.0f;
    }

    body = &entity->physics;
    speedMetersPerSecond = orb_vec2_length(body->velocity) * body->metersPerWorldUnit;
    ratio = orb_clampf(speedMetersPerSecond / ORB_SPEED_OF_LIGHT, 0.0f, 0.9999f);
    return 1.0f / sqrtf(1.0f - ratio * ratio);
}

static void orb_step_world_physics(ORBEngineSandbox *sandbox, float deltaSeconds)
{
    int index;
    int otherIndex;
    float coherencySum = 0.0f;
    int coherencyCount = 0;

    for (index = 0; index < sandbox->world.entityCount; ++index)
    {
        ORBRenderEntity *entity = &sandbox->world.entities[index];
        ORBSpaceNode *space = orb_get_space(&sandbox->world, entity->spaceId);

        if (!entity->active || !entity->physics.enabled || !space)
        {
            continue;
        }

        entity->physics.accumulatedForce.x = 0.0f;
        entity->physics.accumulatedForce.y = 0.0f;

        if (entity->physics.dynamicBody)
        {
            orb_apply_space_forces(entity, space);
            orb_apply_anchor_force(entity);
            orb_apply_drag_force(entity, space);
            orb_apply_thermal_motion(entity, space, deltaSeconds);
        }
    }

    for (index = 0; index < sandbox->world.entityCount; ++index)
    {
        ORBRenderEntity *entity = &sandbox->world.entities[index];

        if (!entity->active || !entity->physics.enabled || !entity->physics.dynamicBody)
        {
            continue;
        }

        for (otherIndex = index + 1; otherIndex < sandbox->world.entityCount; ++otherIndex)
        {
            ORBRenderEntity *other = &sandbox->world.entities[otherIndex];
            if (!other->active || !other->physics.enabled || entity->spaceId != other->spaceId)
            {
                continue;
            }

            orb_apply_pair_force(entity, other);
        }
    }

    for (index = 0; index < sandbox->world.entityCount; ++index)
    {
        ORBRenderEntity *entity = &sandbox->world.entities[index];

        if (!entity->active || !entity->physics.enabled)
        {
            continue;
        }

        orb_integrate_entity(entity, deltaSeconds);
        orb_constrain_entity_to_space(entity);
        orb_sync_entity_collision(entity);
        coherencySum += orb_measure_entity_coherency(entity);
        coherencyCount += 1;
    }

    sandbox->worldVisualCoherency = coherencyCount > 0 ? coherencySum / (float)coherencyCount : 1.0f;
}

static void orb_apply_space_forces(ORBRenderEntity *entity, const ORBSpaceNode *space)
{
    ORBPhysicsBody *body = &entity->physics;
    ORBVec2 force;

    if (!body->affectedByGravity || body->massKg <= 0.0f)
    {
        return;
    }

    force = orb_vec2_scale(space->gravityVector, body->massKg * space->simulationRate);
    body->accumulatedForce = orb_vec2_add(body->accumulatedForce, force);
}

static void orb_apply_anchor_force(ORBRenderEntity *entity)
{
    ORBPhysicsBody *body = &entity->physics;
    ORBVec2 displacementWorld;
    ORBVec2 displacementMeters;
    ORBVec2 velocityMeters;
    ORBVec2 springForce;
    ORBVec2 dampingForce;

    if (body->anchorSpring <= 0.0f && body->anchorDamping <= 0.0f)
    {
        return;
    }

    displacementWorld = orb_vec2_sub(entity->position, body->anchorPosition);
    displacementMeters = orb_vec2_scale(displacementWorld, body->metersPerWorldUnit);
    velocityMeters = orb_vec2_scale(body->velocity, body->metersPerWorldUnit);
    springForce = orb_vec2_scale(displacementMeters, -body->anchorSpring);
    dampingForce = orb_vec2_scale(velocityMeters, -body->anchorDamping);
    body->accumulatedForce = orb_vec2_add(body->accumulatedForce, orb_vec2_add(springForce, dampingForce));
}

static void orb_apply_drag_force(ORBRenderEntity *entity, const ORBSpaceNode *space)
{
    ORBPhysicsBody *body = &entity->physics;
    ORBVec2 velocityMeters;
    float speed;
    float dragMagnitude;
    ORBVec2 dragForce;

    if (body->dragCoefficient <= 0.0f || body->areaSquareMeters <= 0.0f)
    {
        return;
    }

    velocityMeters = orb_vec2_scale(body->velocity, body->metersPerWorldUnit);
    speed = orb_vec2_length(velocityMeters);
    if (speed <= 0.0001f)
    {
        return;
    }

    dragMagnitude = 0.5f * space->mediumDensity * speed * speed * body->dragCoefficient * body->areaSquareMeters;
    dragForce = orb_vec2_scale(orb_vec2_normalize(velocityMeters), -dragMagnitude);
    body->accumulatedForce = orb_vec2_add(body->accumulatedForce, dragForce);
}

static void orb_apply_thermal_motion(ORBRenderEntity *entity, const ORBSpaceNode *space, float deltaSeconds)
{
    ORBPhysicsBody *body = &entity->physics;
    float effectiveTemperature;
    float rmsSpeed;
    float domainScale;

    if (!body->affectedByThermal || body->massKg <= 0.0f)
    {
        return;
    }

    effectiveTemperature = 0.5f * (body->temperatureKelvin + space->ambientTemperatureKelvin);
    rmsSpeed = sqrtf((2.0f * ORB_BOLTZMANN_CONSTANT * effectiveTemperature) / body->massKg);

    switch (body->scaleDomain)
    {
    case ORB_SCALE_SUBATOMIC:
        domainScale = 1.0f;
        break;
    case ORB_SCALE_MOLECULAR:
        domainScale = 0.35f;
        break;
    case ORB_SCALE_MESOSCOPIC:
        domainScale = 0.08f;
        break;
    default:
        domainScale = 0.01f;
        break;
    }

    body->velocity.x += orb_random_signed() * (rmsSpeed / body->metersPerWorldUnit) * domainScale * deltaSeconds;
    body->velocity.y += orb_random_signed() * (rmsSpeed / body->metersPerWorldUnit) * domainScale * deltaSeconds;
}

static void orb_apply_pair_force(ORBRenderEntity *a, ORBRenderEntity *b)
{
    ORBVec2 deltaWorld;
    ORBVec2 direction;
    float metersPerWorldUnit;
    float distanceMeters;
    float distanceSquared;
    float gravitationalMagnitude;
    float electroMagnitude = 0.0f;
    float sigma;
    float epsilon;
    float sr;
    float shortRangeMagnitude = 0.0f;
    ORBVec2 totalForce;

    if ((!a->physics.dynamicBody && !b->physics.dynamicBody) || a->physics.massKg <= 0.0f || b->physics.massKg <= 0.0f)
    {
        return;
    }

    deltaWorld = orb_vec2_sub(b->position, a->position);
    direction = orb_vec2_normalize(deltaWorld);
    metersPerWorldUnit = 0.5f * (a->physics.metersPerWorldUnit + b->physics.metersPerWorldUnit);
    distanceMeters = orb_vec2_length(deltaWorld) * metersPerWorldUnit + ORB_PHYSICS_SOFTENING_METERS;
    distanceSquared = distanceMeters * distanceMeters;
    gravitationalMagnitude = ORB_GRAVITATIONAL_CONSTANT * a->physics.massKg * b->physics.massKg / distanceSquared;

    if (a->physics.affectedByCharge || b->physics.affectedByCharge)
    {
        electroMagnitude = ORB_COULOMB_CONSTANT * a->physics.chargeCoulombs * b->physics.chargeCoulombs / distanceSquared;
    }

    sigma = a->physics.radiusMeters + b->physics.radiusMeters;
    epsilon = sqrtf(a->physics.cohesion * b->physics.cohesion);
    if (sigma > 0.0f && epsilon > 0.0f && distanceMeters < sigma * 2.5f)
    {
        sr = sigma / distanceMeters;
        shortRangeMagnitude = (24.0f * epsilon / distanceMeters) * (2.0f * powf(sr, 12.0f) - powf(sr, 6.0f));
    }

    totalForce = orb_vec2_scale(direction, gravitationalMagnitude - electroMagnitude + shortRangeMagnitude);

    if (a->physics.dynamicBody && !a->physics.pinned)
    {
        a->physics.accumulatedForce = orb_vec2_add(a->physics.accumulatedForce, totalForce);
    }
    if (b->physics.dynamicBody && !b->physics.pinned)
    {
        b->physics.accumulatedForce = orb_vec2_add(b->physics.accumulatedForce, orb_vec2_scale(totalForce, -1.0f));
    }
}

static void orb_integrate_entity(ORBRenderEntity *entity, float deltaSeconds)
{
    ORBPhysicsBody *body = &entity->physics;
    ORBVec2 accelerationWorld;
    float kineticEnergy;
    float thermalEnergy;

    if (!body->enabled)
    {
        return;
    }

    if (body->pinned || !body->dynamicBody || body->massKg <= 0.0f)
    {
        entity->position = body->anchorPosition;
        body->velocity.x = 0.0f;
        body->velocity.y = 0.0f;
        body->visualEnergy = 0.0f;
        return;
    }

    accelerationWorld = orb_vec2_scale(body->accumulatedForce, 1.0f / (body->massKg * body->metersPerWorldUnit));
    body->velocity = orb_vec2_add(body->velocity, orb_vec2_scale(accelerationWorld, deltaSeconds));
    entity->position = orb_vec2_add(entity->position, orb_vec2_scale(body->velocity, deltaSeconds));

    kineticEnergy = 0.5f * body->massKg * orb_vec2_length_sq(orb_vec2_scale(body->velocity, body->metersPerWorldUnit));
    thermalEnergy = 1.5f * ORB_BOLTZMANN_CONSTANT * body->temperatureKelvin;
    body->visualEnergy = orb_clampf(log10f(1.0f + kineticEnergy + thermalEnergy) / 6.0f, 0.0f, 1.0f);
}

static void orb_constrain_entity_to_space(ORBRenderEntity *entity)
{
    ORBPhysicsBody *body = &entity->physics;
    float halfWidth;

    if (!body->dynamicBody || body->pinned)
    {
        return;
    }

    halfWidth = entity->size.x * 0.5f;
    if (entity->position.x < halfWidth)
    {
        entity->position.x = halfWidth;
        body->velocity.x = -body->velocity.x * body->restitution;
    }
    else if (entity->position.x > ORB_WORLD_WIDTH - halfWidth)
    {
        entity->position.x = ORB_WORLD_WIDTH - halfWidth;
        body->velocity.x = -body->velocity.x * body->restitution;
    }

    if (entity->position.y < entity->size.y)
    {
        entity->position.y = entity->size.y;
        body->velocity.y = -body->velocity.y * body->restitution;
    }
    else if (entity->position.y > ORB_WORLD_HEIGHT)
    {
        entity->position.y = ORB_WORLD_HEIGHT;
        body->velocity.y = -body->velocity.y * body->restitution;
    }
}

static float orb_measure_entity_coherency(const ORBRenderEntity *entity)
{
    ORBVec2 anchorOffset;
    float anchorDistance;
    float speed;

    if (!entity->physics.enabled)
    {
        return 1.0f;
    }

    anchorOffset = orb_vec2_sub(entity->position, entity->physics.anchorPosition);
    anchorDistance = orb_vec2_length(anchorOffset);
    speed = orb_vec2_length(entity->physics.velocity);
    return 1.0f / (1.0f + anchorDistance * 0.05f + speed * 0.03f);
}

static void orb_step_open_arena(ORBEngineSandbox *sandbox, float deltaSeconds)
{
    int index;
    int otherIndex;
    ORBVec2 arenaCenter;
    const float metersPerWorldUnit = 0.04f;
    const float arenaCoreMassKg = 1.2e14f;

    arenaCenter.x = ORB_WORLD_WIDTH * 0.5f;
    arenaCenter.y = ORB_WORLD_HEIGHT * 0.52f;

    for (index = 0; index < sandbox->openArena.enemyCount; ++index)
    {
        ORBVec2 toCenter;
        ORBVec2 direction;
        float distanceMeters;
        float distanceSquared;
        float attraction;
        ORBVec2 velocityMeters;
        float speed;
        float dragMagnitude;
        float rmsSpeed;

        if (!sandbox->openArena.enemyAlive[index])
        {
            continue;
        }

        toCenter = orb_vec2_sub(arenaCenter, sandbox->openArena.enemyPositions[index]);
        direction = orb_vec2_normalize(toCenter);
        distanceMeters = orb_vec2_length(toCenter) * metersPerWorldUnit + ORB_PHYSICS_SOFTENING_METERS;
        distanceSquared = distanceMeters * distanceMeters;
        attraction = ORB_GRAVITATIONAL_CONSTANT * arenaCoreMassKg * sandbox->openArena.enemyMassKg[index] / distanceSquared;
        sandbox->openArena.enemyVelocities[index] = orb_vec2_add(
            sandbox->openArena.enemyVelocities[index],
            orb_vec2_scale(direction, (attraction / sandbox->openArena.enemyMassKg[index]) / metersPerWorldUnit * deltaSeconds));

        for (otherIndex = index + 1; otherIndex < sandbox->openArena.enemyCount; ++otherIndex)
        {
            ORBVec2 deltaWorld;
            ORBVec2 repelDirection;
            float pairDistanceMeters;
            float pairForce;

            if (!sandbox->openArena.enemyAlive[otherIndex])
            {
                continue;
            }

            deltaWorld = orb_vec2_sub(sandbox->openArena.enemyPositions[otherIndex], sandbox->openArena.enemyPositions[index]);
            repelDirection = orb_vec2_normalize(deltaWorld);
            pairDistanceMeters = orb_vec2_length(deltaWorld) * metersPerWorldUnit + ORB_PHYSICS_SOFTENING_METERS;
            pairForce = ORB_COULOMB_CONSTANT * sandbox->openArena.enemyChargeCoulombs[index] * sandbox->openArena.enemyChargeCoulombs[otherIndex] / (pairDistanceMeters * pairDistanceMeters);
            sandbox->openArena.enemyVelocities[index] = orb_vec2_add(
                sandbox->openArena.enemyVelocities[index],
                orb_vec2_scale(repelDirection, -(pairForce / sandbox->openArena.enemyMassKg[index]) / metersPerWorldUnit * deltaSeconds));
            sandbox->openArena.enemyVelocities[otherIndex] = orb_vec2_add(
                sandbox->openArena.enemyVelocities[otherIndex],
                orb_vec2_scale(repelDirection, (pairForce / sandbox->openArena.enemyMassKg[otherIndex]) / metersPerWorldUnit * deltaSeconds));
        }

        velocityMeters = orb_vec2_scale(sandbox->openArena.enemyVelocities[index], metersPerWorldUnit);
        speed = orb_vec2_length(velocityMeters);
        if (speed > 0.0001f)
        {
            dragMagnitude = 0.5f * 1.1f * speed * speed * 1.02f * 0.55f;
            sandbox->openArena.enemyVelocities[index] = orb_vec2_add(
                sandbox->openArena.enemyVelocities[index],
                orb_vec2_scale(orb_vec2_normalize(velocityMeters), -(dragMagnitude / sandbox->openArena.enemyMassKg[index]) / metersPerWorldUnit * deltaSeconds));
        }

        rmsSpeed = sqrtf((2.0f * ORB_BOLTZMANN_CONSTANT * sandbox->openArena.enemyTemperatureKelvin[index]) / sandbox->openArena.enemyMassKg[index]);
        sandbox->openArena.enemyVelocities[index].x += orb_random_signed() * (rmsSpeed / metersPerWorldUnit) * 0.02f * deltaSeconds;
        sandbox->openArena.enemyVelocities[index].y += orb_random_signed() * (rmsSpeed / metersPerWorldUnit) * 0.02f * deltaSeconds;
        sandbox->openArena.enemyPositions[index] = orb_vec2_add(
            sandbox->openArena.enemyPositions[index],
            orb_vec2_scale(sandbox->openArena.enemyVelocities[index], deltaSeconds));

        if (sandbox->openArena.enemyPositions[index].x < 120.0f || sandbox->openArena.enemyPositions[index].x > 904.0f)
        {
            sandbox->openArena.enemyVelocities[index].x = -sandbox->openArena.enemyVelocities[index].x * 0.35f;
        }
        if (sandbox->openArena.enemyPositions[index].y < 170.0f || sandbox->openArena.enemyPositions[index].y > 620.0f)
        {
            sandbox->openArena.enemyVelocities[index].y = -sandbox->openArena.enemyVelocities[index].y * 0.35f;
        }

        sandbox->openArena.enemyPositions[index].x = orb_clampf(sandbox->openArena.enemyPositions[index].x, 120.0f, 904.0f);
        sandbox->openArena.enemyPositions[index].y = orb_clampf(sandbox->openArena.enemyPositions[index].y, 170.0f, 620.0f);
        sandbox->openArena.enemyVisualEnergy[index] = orb_clampf(log10f(1.0f + speed * speed * sandbox->openArena.enemyMassKg[index]) / 4.0f, 0.0f, 1.0f);
    }
}

static void orb_add_default_spaces(ORBEngineSandbox *sandbox)
{
    ORBSpaceNode *surface = orb_world_add_space(&sandbox->world, ORB_SPACE_SURFACE, -1, L"Island Surface", 0.0f, 0.0f, 1.0f, 0.09f);
    ORBSpaceNode *agriculture = orb_world_add_space(&sandbox->world, ORB_SPACE_AGRICULTURE, 0, L"Agriculture Complex", 30.0f, 150.0f, 0.74f, 0.06f);
    ORBSpaceNode *simulator = orb_world_add_space(&sandbox->world, ORB_SPACE_SIMULATOR, 0, L"Combat Simulator Gate", 610.0f, 120.0f, 0.92f, 0.14f);
    ORBSpaceNode *pocket = orb_world_add_space(&sandbox->world, ORB_SPACE_RECURSIVE_POCKET, 2, L"Pocket Arena", 700.0f, 240.0f, 0.58f, 0.22f);

    if (surface)
    {
        surface->breathingAmplitude = 0.018f;
        surface->breathingRate = 0.55f;
        surface->orbitalRadius = 0.0f;
        surface->orbitalSpeed = 0.0f;
        orb_vec2_set(&surface->gravityVector, 0.0f, 9.80665f);
        surface->ambientTemperatureKelvin = 293.15f;
        surface->mediumDensity = 1.225f;
        surface->staticPressure = 101325.0f;
        surface->simulationRate = 1.0f;
    }
    if (agriculture)
    {
        agriculture->breathingAmplitude = 0.040f;
        agriculture->breathingRate = 1.25f;
        agriculture->orbitalRadius = 0.08f;
        agriculture->orbitalSpeed = 0.80f;
        orb_vec2_set(&agriculture->gravityVector, 0.0f, 9.80665f);
        agriculture->ambientTemperatureKelvin = 298.15f;
        agriculture->mediumDensity = 1.280f;
        agriculture->staticPressure = 102200.0f;
        agriculture->simulationRate = 1.0f;
    }
    if (simulator)
    {
        simulator->breathingAmplitude = 0.030f;
        simulator->breathingRate = 0.95f;
        simulator->orbitalRadius = 0.06f;
        simulator->orbitalSpeed = 0.52f;
        orb_vec2_set(&simulator->gravityVector, 0.0f, 9.80665f);
        simulator->ambientTemperatureKelvin = 290.15f;
        simulator->mediumDensity = 1.160f;
        simulator->staticPressure = 99500.0f;
        simulator->simulationRate = 1.0f;
    }
    if (pocket)
    {
        pocket->breathingAmplitude = 0.085f;
        pocket->breathingRate = 1.75f;
        pocket->orbitalRadius = 0.14f;
        pocket->orbitalSpeed = 1.20f;
        orb_vec2_set(&pocket->gravityVector, 0.0f, 8.912f);
        pocket->ambientTemperatureKelvin = 286.15f;
        pocket->mediumDensity = 0.980f;
        pocket->staticPressure = 94400.0f;
        pocket->simulationRate = 1.08f;
    }
}

static void orb_add_default_entities(ORBEngineSandbox *sandbox)
{
    ORBRenderEntity *entity;
    entity = orb_world_add_entity(&sandbox->world, 0, ORB_ENTITY_PLAYER, L"Roju Test Avatar", 220.0f, 420.0f, 26.0f, 38.0f, orb_make_color(145, 92, 210, 255));
    if (entity)
    {
        entity->depthBias = 0.08f;
        sandbox->playerEntityId = entity->id;
        orb_configure_entity_body(entity, ORB_SCALE_HUMAN, 0.02f, 82.0f, 2.0e-7f, 310.15f, 1.05f, 0.55f, 0.32f, 1, 0, 18.0f, 22.0f, 0.015f, 0);
    }

    entity = orb_world_add_entity(&sandbox->world, 0, ORB_ENTITY_RAFT, L"Shore Raft Gate", 610.0f, 500.0f, 110.0f, 30.0f, orb_make_color(133, 88, 55, 255));
    if (entity)
    {
        entity->depthBias = 0.16f;
        orb_configure_entity_body(entity, ORB_SCALE_HUMAN, 0.03f, 140.0f, 0.0f, 291.15f, 1.25f, 1.10f, 0.80f, 1, 0, 6.0f, 30.0f, 0.030f, 0);
    }

    entity = orb_world_add_entity(&sandbox->world, 0, ORB_ENTITY_GATE, L"Simulator Intake", 864.0f, 280.0f, 90.0f, 120.0f, orb_make_color(78, 135, 160, 255));
    if (entity)
    {
        entity->depthBias = -0.02f;
        orb_configure_entity_body(entity, ORB_SCALE_HUMAN, 0.02f, 600.0f, 0.0f, 289.15f, 0.0f, 0.0f, 0.65f, 0, 1, 0.0f, 0.0f, 0.0f, 0);
    }

    entity = orb_world_add_entity(&sandbox->world, 1, ORB_ENTITY_CROP_BED, L"Hydro Bed A", 230.0f, 470.0f, 90.0f, 44.0f, orb_make_color(66, 133, 72, 255));
    orb_configure_entity_body(entity, ORB_SCALE_HUMAN, 0.025f, 120.0f, 0.0f, 296.15f, 0.0f, 0.0f, 0.55f, 0, 1, 0.0f, 0.0f, 0.0f, 0);
    entity = orb_world_add_entity(&sandbox->world, 1, ORB_ENTITY_CROP_BED, L"Hydro Bed B", 380.0f, 510.0f, 90.0f, 44.0f, orb_make_color(66, 133, 72, 255));
    orb_configure_entity_body(entity, ORB_SCALE_HUMAN, 0.025f, 120.0f, 0.0f, 296.15f, 0.0f, 0.0f, 0.55f, 0, 1, 0.0f, 0.0f, 0.0f, 0);
    entity = orb_world_add_entity(&sandbox->world, 1, ORB_ENTITY_CROP_BED, L"Hydro Bed C", 530.0f, 550.0f, 90.0f, 44.0f, orb_make_color(66, 133, 72, 255));
    orb_configure_entity_body(entity, ORB_SCALE_HUMAN, 0.025f, 120.0f, 0.0f, 296.15f, 0.0f, 0.0f, 0.55f, 0, 1, 0.0f, 0.0f, 0.0f, 0);
    entity = orb_world_add_entity(&sandbox->world, 2, ORB_ENTITY_GATE, L"Training Portal", 530.0f, 320.0f, 90.0f, 126.0f, orb_make_color(95, 156, 189, 255));
    orb_configure_entity_body(entity, ORB_SCALE_HUMAN, 0.02f, 540.0f, 0.0f, 289.15f, 0.0f, 0.0f, 0.60f, 0, 1, 0.0f, 0.0f, 0.0f, 0);
    entity = orb_world_add_entity(&sandbox->world, 2, ORB_ENTITY_ORB_NODE, L"Orbital Lens", 760.0f, 260.0f, 50.0f, 50.0f, orb_make_color(126, 210, 240, 255));
    orb_configure_entity_body(entity, ORB_SCALE_MOLECULAR, 0.006f, 0.002f, -0.00008f, 840.0f, 0.07f, 0.0015f, 0.10f, 1, 0, 14.0f, 0.08f, 2.0e-5f, 1);
    entity = orb_world_add_entity(&sandbox->world, 3, ORB_ENTITY_ENEMY, L"Pocket Guardian", 460.0f, 390.0f, 34.0f, 44.0f, orb_make_color(205, 112, 99, 255));
    orb_configure_entity_body(entity, ORB_SCALE_HUMAN, 0.02f, 78.0f, 4.0e-7f, 307.15f, 1.08f, 0.52f, 0.28f, 1, 0, 20.0f, 18.0f, 0.020f, 0);
    entity = orb_world_add_entity(&sandbox->world, 3, ORB_ENTITY_ORB_NODE, L"Breathing Core", 610.0f, 250.0f, 42.0f, 42.0f, orb_make_color(108, 201, 235, 255));
    orb_configure_entity_body(entity, ORB_SCALE_SUBATOMIC, 0.0008f, 5.0e-10f, 0.00016f, 1800.0f, 0.02f, 0.0002f, 0.02f, 1, 0, 24.0f, 0.05f, 5.0e-4f, 1);
}

static void orb_generate_open_arena(ORBEngineSandbox *sandbox, int seed)
{
    int index;
    sandbox->openArena.seed = seed;
    sandbox->openArena.enemyCount = 8;
    srand(seed);
    for (index = 0; index < sandbox->openArena.enemyCount; ++index)
    {
        sandbox->openArena.enemyPositions[index].x = 140.0f + (float)(rand() % 720);
        sandbox->openArena.enemyPositions[index].y = 200.0f + (float)(rand() % 260);
        sandbox->openArena.enemyVelocities[index].x = 0.0f;
        sandbox->openArena.enemyVelocities[index].y = 0.0f;
        sandbox->openArena.enemyAlive[index] = 1;
        sandbox->openArena.enemyMassKg[index] = 60.0f + (float)(rand() % 30);
        sandbox->openArena.enemyChargeCoulombs[index] = 0.00002f + (float)(rand() % 8) * 0.000001f;
        sandbox->openArena.enemyTemperatureKelvin[index] = 304.15f + (float)(rand() % 16);
        sandbox->openArena.enemyVisualEnergy[index] = 0.0f;
    }
}

static void orb_set_status(ORBEngineSandbox *sandbox, const wchar_t *status)
{
    wcsncpy(sandbox->statusLine, status, 255);
    sandbox->statusLine[255] = 0;
}

static int orb_select_root_space(const ORBEngineSandbox *sandbox)
{
    if (sandbox->showAgriculture)
    {
        return 1;
    }
    if (sandbox->showSimulatorMenu)
    {
        return 2;
    }
    if (sandbox->currentCombatMode != ORB_COMBAT_NONE)
    {
        return 3;
    }
    return 0;
}

static void orb_draw_surface_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect)
{
    orb_draw_scene_frame(
        sandbox,
        hdc,
        rect,
        0,
        L"ORBEngine Sandbox: Island Surface",
        L"Recursive island root with Mode-7-inspired sand and water bands, plus orbital pockets for simulator and agriculture."
    );
    orb_draw_label(sandbox, hdc, 36, rect.bottom - 86, RGB(236, 240, 244), L"Press G to descend into agriculture. Press R to travel by raft to the combat simulator.");
}

static void orb_draw_agriculture_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect)
{
    orb_draw_scene_frame(
        sandbox,
        hdc,
        rect,
        1,
        L"ORBEngine Sandbox: Beneath-Island Agriculture Complex",
        L"This space now renders as a breathing subworld instead of a flat panel, keeping crop beds inside the recursive world graph."
    );
    orb_draw_label(sandbox, hdc, 36, rect.bottom - 86, RGB(236, 240, 244), L"Press ESC to return to the island surface.");
}

static void orb_draw_simulator_menu(ORBEngineSandbox *sandbox, HDC hdc, RECT rect)
{
    RECT panel = {84, 132, rect.right - 84, rect.bottom - 140};
    orb_draw_scene_frame(
        sandbox,
        hdc,
        rect,
        2,
        L"Combat Simulator Gate",
        L"The simulator is now staged inside the recursive render graph, with the pocket arena visible as an actual nested orbital viewport."
    );
    orb_draw_overlay_panel(sandbox, hdc, panel, RGB(17, 23, 36), RGB(104, 146, 198), &sandbox->uiShell.dialogChoiceGrid);
    orb_draw_label(sandbox, hdc, panel.left + 30, panel.top + 34, RGB(248, 250, 252), L"Select a mode for engine and combat-system testing:");
    orb_draw_label_sized(sandbox, hdc, panel.left + 40, panel.top + 100, RGB(248, 250, 252), L"[1] Tactical Simulator", 18);
    orb_draw_label(sandbox, hdc, panel.left + 40, panel.top + 132, RGB(218, 224, 232), L"Turn-order validation layered over the recursive pocket arena.");
    orb_draw_label_sized(sandbox, hdc, panel.left + 40, panel.top + 214, RGB(248, 250, 252), L"[2] QTE Simulator", 18);
    orb_draw_label(sandbox, hdc, panel.left + 40, panel.top + 246, RGB(218, 224, 232), L"OrbGuardian timing-chain room wrapped in orbital breathing transforms.");
    orb_draw_label_sized(sandbox, hdc, panel.left + 40, panel.top + 328, RGB(248, 250, 252), L"[3] Open Simulator", 18);
    orb_draw_label(sandbox, hdc, panel.left + 40, panel.top + 360, RGB(218, 224, 232), L"Real-time pseudo-3D test arena with recursive pocket rendering.");
    if (orb_ui_bitmap_ready(&sandbox->uiShell.fontUppercase))
    {
        RECT fontPreview = {panel.right - 238, panel.top + 34, panel.right - 34, panel.top + 134};
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.fontUppercase, fontPreview, 228);
    }
    orb_draw_label(sandbox, hdc, 36, rect.bottom - 86, RGB(236, 240, 244), L"Press 1, 2, or 3. Press ESC to return to island root view.");
}

static void orb_draw_tactical_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect)
{
    RECT panel = {88, rect.bottom - 240, rect.right - 88, rect.bottom - 110};
    wchar_t buffer[128];
    orb_draw_scene_frame(
        sandbox,
        hdc,
        rect,
        3,
        L"Tactical Combat Simulator",
        L"The combat board sits inside the recursive pocket so the turn layer can inherit breathing and orbital distortion without changing logic order."
    );
    orb_draw_overlay_panel(sandbox, hdc, panel, RGB(20, 26, 42), RGB(116, 144, 210), &sandbox->uiShell.modalTemplate);
    swprintf(buffer, 128, L"Player HP: %d", sandbox->tacticalPlayerHp);
    orb_draw_label(sandbox, hdc, panel.left + 28, panel.top + 30, RGB(250, 250, 252), buffer);
    swprintf(buffer, 128, L"Enemy HP: %d", sandbox->tacticalEnemyHp);
    orb_draw_label(sandbox, hdc, panel.left + 248, panel.top + 30, RGB(250, 250, 252), buffer);
    orb_draw_label(sandbox, hdc, panel.left + 28, panel.top + 68, RGB(225, 230, 236), L"Press A to attack, D to defend, ESC to leave.");
}

static void orb_draw_qte_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect)
{
    RECT panel = {88, rect.bottom - 250, rect.right - 88, rect.bottom - 110};
    wchar_t buffer[128];
    orb_draw_scene_frame(
        sandbox,
        hdc,
        rect,
        3,
        L"OrbGuardian QTE Simulator",
        L"The guardian chamber reuses the same recursive pocket renderer, so timing gameplay sits on top of a breathing orbital chamber instead of a separate mock scene."
    );
    orb_draw_overlay_panel(sandbox, hdc, panel, RGB(34, 18, 42), RGB(151, 99, 188), &sandbox->uiShell.dropdownShell);
    swprintf(buffer, 128, L"Sequence: %ls", sandbox->qteSequence);
    orb_draw_label(sandbox, hdc, panel.left + 28, panel.top + 30, RGB(250, 250, 252), buffer);
    swprintf(buffer, 128, L"Progress: %d / %d", sandbox->qteIndex, sandbox->qteLength);
    orb_draw_label(sandbox, hdc, panel.left + 28, panel.top + 64, RGB(250, 250, 252), buffer);
    orb_draw_label(sandbox, hdc, panel.left + 28, panel.top + 102, RGB(225, 230, 236), L"Press the exact key chain from left to right. Press ESC to leave.");
}

static void orb_draw_open_scene(ORBEngineSandbox *sandbox, HDC hdc, RECT rect)
{
    int index;
    RECT panel = {88, rect.bottom - 210, rect.right - 88, rect.bottom - 110};
    orb_draw_scene_frame(
        sandbox,
        hdc,
        rect,
        3,
        L"Open Combat Simulator",
        L"This is the first ORB-style gameworld pass: a recursive 2D-authored arena rendered with a Mode-7-inspired floor, breathing scale modulation, and orbital pocket transforms."
    );

    for (index = 0; index < sandbox->openArena.enemyCount; ++index)
    {
        if (sandbox->openArena.enemyAlive[index])
        {
            ORBRenderEntity temp;
            float energyMix;
            ZeroMemory(&temp, sizeof(temp));
            temp.spaceId = 3;
            temp.kind = ORB_ENTITY_ENEMY;
            temp.position = sandbox->openArena.enemyPositions[index];
            temp.size.x = 24.0f;
            temp.size.y = 34.0f;
            energyMix = sandbox->openArena.enemyVisualEnergy[index];
            temp.tint = orb_make_color(
                (uint8_t)orb_round_to_int(orb_lerp(189.0f, 240.0f, energyMix)),
                (uint8_t)orb_round_to_int(orb_lerp(102.0f, 210.0f, energyMix * 0.7f)),
                (uint8_t)orb_round_to_int(orb_lerp(92.0f, 125.0f, energyMix * 0.5f)),
                255);
            temp.active = 1;
            temp.depthBias = 0.10f;
            temp.collision.usesGreenBoundary = 1;
            temp.collision.debugColor = RGB(0, 255, 0);
            temp.physics.enabled = 1;
            temp.physics.visualEnergy = energyMix;
            orb_draw_entity_projection(hdc, orb_get_space(&sandbox->world, 3), &temp, rect, 0, 1.0f, sandbox->renderTime);
        }
    }

    orb_draw_overlay_panel(sandbox, hdc, panel, RGB(16, 24, 28), RGB(96, 176, 132), &sandbox->uiShell.notificationToast);
    orb_draw_label(sandbox, hdc, panel.left + 28, panel.top + 28, RGB(245, 248, 250), L"Press N for a new procedural arena. Press ESC to leave.");
    orb_draw_label(sandbox, hdc, panel.left + 28, panel.top + 62, RGB(218, 225, 232), L"This mode is the strongest current expression of the recursive 2D-to-3D-feel renderer.");
}

static void orb_draw_scene_frame(ORBEngineSandbox *sandbox, HDC hdc, RECT rect, int rootSpaceId, const wchar_t *title, const wchar_t *subtitle)
{
    RECT worldRect;
    worldRect.left = 28;
    worldRect.top = 84;
    worldRect.right = rect.right - 28;
    worldRect.bottom = rect.bottom - 104;

    orb_render_space_recursive(sandbox, hdc, worldRect, rootSpaceId, 0);
    orb_draw_ui_chrome(sandbox, hdc, rect);
    orb_draw_label_sized(sandbox, hdc, 34, 22, RGB(244, 247, 251), title, 22);
    orb_draw_label_sized(sandbox, hdc, 34, 52, RGB(221, 228, 234), subtitle, 12);
}

static void orb_render_space_recursive(ORBEngineSandbox *sandbox, HDC hdc, RECT viewport, int spaceId, int depth)
{
    ORBSpaceNode *space = orb_get_space(&sandbox->world, spaceId);
    float breathScale;
    float orbitAngle;
    int saveState;
    int childIndex;

    if (!space || depth > sandbox->recursionDepthLimit)
    {
        return;
    }

    breathScale = 1.0f + space->breathingAmplitude * sinf((sandbox->renderTime * space->breathingRate) + (float)space->id * 0.85f);
    orbitAngle = (sandbox->renderTime * space->orbitalSpeed) + (float)space->id * 0.91f;

    saveState = SaveDC(hdc);
    IntersectClipRect(hdc, viewport.left, viewport.top, viewport.right, viewport.bottom);

    orb_draw_space_backdrop(sandbox, hdc, space, viewport, depth, breathScale, orbitAngle);
    orb_draw_mode7_floor(sandbox, hdc, space, viewport, depth, breathScale, orbitAngle);
    orb_draw_space_entities(sandbox, hdc, space, viewport, depth, breathScale, orbitAngle);

    for (childIndex = 0; childIndex < space->childCount; ++childIndex)
    {
        RECT childViewport = orb_compute_child_viewport(sandbox, space, orb_get_space(&sandbox->world, space->childIds[childIndex]), viewport, childIndex, depth);
        orb_render_space_recursive(sandbox, hdc, childViewport, space->childIds[childIndex], depth + 1);
    }

    orb_draw_space_border(hdc, viewport, RGB(86, 124, 164));
    orb_draw_label_sized(sandbox, hdc, viewport.left + 12, viewport.top + 10, RGB(247, 249, 252), space->name, 12);
    RestoreDC(hdc, saveState);
}

static RECT orb_compute_child_viewport(ORBEngineSandbox *sandbox, const ORBSpaceNode *parent, const ORBSpaceNode *child, RECT parentViewport, int childIndex, int depth)
{
    RECT childViewport;
    float parentWidth = (float)(parentViewport.right - parentViewport.left);
    float parentHeight = (float)(parentViewport.bottom - parentViewport.top);
    float baseScale = child->scale * (0.88f - depth * 0.08f);
    float breath = 1.0f + child->breathingAmplitude * sinf((sandbox->renderTime * child->breathingRate) + childIndex * 0.9f);
    float orbitAngle = (sandbox->renderTime * child->orbitalSpeed) + childIndex * 1.7f;
    float orbitRadiusPx = (parentWidth < parentHeight ? parentWidth : parentHeight) * child->orbitalRadius;
    float normalizedX = orb_clampf(child->origin.x / ORB_WORLD_WIDTH, 0.10f, 0.90f);
    float normalizedY = orb_clampf(child->origin.y / ORB_WORLD_HEIGHT, 0.14f, 0.86f);
    float centerX = parentViewport.left + parentWidth * normalizedX + cosf(orbitAngle) * orbitRadiusPx;
    float centerY = parentViewport.top + parentHeight * normalizedY + sinf(orbitAngle * 0.8f) * orbitRadiusPx * 0.55f;
    float width = parentWidth * baseScale * breath * 0.78f;
    float height = parentHeight * baseScale * breath * 0.70f;

    (void)parent;
    childViewport.left = orb_round_to_int(centerX - width * 0.5f);
    childViewport.top = orb_round_to_int(centerY - height * 0.5f);
    childViewport.right = orb_round_to_int(centerX + width * 0.5f);
    childViewport.bottom = orb_round_to_int(centerY + height * 0.5f);
    return childViewport;
}

static void orb_draw_space_backdrop(ORBEngineSandbox *sandbox, HDC hdc, const ORBSpaceNode *space, RECT viewport, int depth, float breathScale, float orbitAngle)
{
    int width = viewport.right - viewport.left;
    int height = viewport.bottom - viewport.top;
    int band;
    COLORREF topColor;
    COLORREF bottomColor;

    switch (space->kind)
    {
    case ORB_SPACE_SURFACE:
        topColor = RGB(56, 96, 146);
        bottomColor = RGB(32, 61, 98);
        break;
    case ORB_SPACE_AGRICULTURE:
        topColor = RGB(42, 62, 48);
        bottomColor = RGB(23, 34, 26);
        break;
    case ORB_SPACE_SIMULATOR:
        topColor = RGB(34, 54, 83);
        bottomColor = RGB(20, 28, 42);
        break;
    default:
        topColor = RGB(47, 34, 64);
        bottomColor = RGB(22, 19, 37);
        break;
    }

    for (band = 0; band < 12; ++band)
    {
        int top = viewport.top + (height * band) / 12;
        int bottom = viewport.top + (height * (band + 1)) / 12;
        float t = (float)band / 11.0f;
        float drift = sinf((sandbox->renderTime * 0.4f) + orbitAngle + band * 0.4f) * 12.0f * breathScale;
        orb_fill_rect(hdc, viewport.left + orb_round_to_int(drift), top, viewport.right, bottom, orb_lerp_color(topColor, bottomColor, t));
    }

    orb_draw_orbital_rings(hdc, viewport, RGB(96 + depth * 24, 150 + depth * 10, 200 + depth * 8), orbitAngle, depth);
    orb_fill_rect(hdc, viewport.left, viewport.top + orb_round_to_int(height * 0.54f), viewport.right, viewport.bottom, RGB(14, 18, 25));
    (void)width;
}

static void orb_draw_mode7_floor(ORBEngineSandbox *sandbox, HDC hdc, const ORBSpaceNode *space, RECT viewport, int depth, float breathScale, float orbitAngle)
{
    int horizon = viewport.top + (viewport.bottom - viewport.top) / 2 + orb_round_to_int(sinf(orbitAngle) * 10.0f);
    int y;
    COLORREF nearColor;
    COLORREF farColor;

    switch (space->kind)
    {
    case ORB_SPACE_SURFACE:
        farColor = RGB(207, 183, 114);
        nearColor = RGB(28, 85, 130);
        break;
    case ORB_SPACE_AGRICULTURE:
        farColor = RGB(70, 110, 74);
        nearColor = RGB(34, 63, 39);
        break;
    case ORB_SPACE_SIMULATOR:
        farColor = RGB(88, 118, 150);
        nearColor = RGB(38, 56, 82);
        break;
    default:
        farColor = RGB(96, 74, 140);
        nearColor = RGB(39, 28, 66);
        break;
    }

    for (y = horizon; y < viewport.bottom; ++y)
    {
        float t = (float)(y - horizon) / (float)((viewport.bottom - horizon) > 0 ? (viewport.bottom - horizon) : 1);
        float width = (viewport.right - viewport.left) * (0.16f + t * (0.92f + depth * 0.05f)) * breathScale;
        float sway = sinf((sandbox->renderTime * 1.1f) + (t * 8.0f) + orbitAngle) * 28.0f * space->rotationWarp;
        float lineCenter = (viewport.left + viewport.right) * 0.5f + sway;
        int left = orb_round_to_int(lineCenter - width * 0.5f);
        int right = orb_round_to_int(lineCenter + width * 0.5f);
        COLORREF lineColor = orb_lerp_color(farColor, nearColor, t);
        orb_fill_rect(hdc, left, y, right, y + 1, lineColor);

        if (((y - horizon) % (10 + depth * 2)) == 0)
        {
            orb_fill_rect(hdc, left, y, right, y + 1, orb_lerp_color(lineColor, RGB(235, 238, 243), 0.18f));
        }
        if (((y - horizon) % (22 + depth * 2)) == 0)
        {
            int cx;
            for (cx = left; cx < right; cx += 36)
            {
                orb_fill_rect(hdc, cx, y, cx + 2, y + 8, orb_lerp_color(lineColor, RGB(240, 243, 246), 0.26f));
            }
        }
    }
}

static void orb_draw_space_entities(ORBEngineSandbox *sandbox, HDC hdc, const ORBSpaceNode *space, RECT viewport, int depth, float breathScale, float orbitAngle)
{
    int index;
    for (index = 0; index < sandbox->world.entityCount; ++index)
    {
        ORBRenderEntity *entity = &sandbox->world.entities[index];
        if (!entity->active || entity->spaceId != space->id)
        {
            continue;
        }
        orb_draw_entity_projection(hdc, space, entity, viewport, depth, breathScale, orbitAngle);
    }
}

static void orb_draw_entity_projection(HDC hdc, const ORBSpaceNode *space, const ORBRenderEntity *entity, RECT viewport, int depth, float breathScale, float orbitAngle)
{
    float localX = entity->position.x - space->origin.x;
    float localY = entity->position.y - space->origin.y;
    float normalizedX = orb_clampf(localX / ORB_WORLD_WIDTH, 0.02f, 0.98f);
    float normalizedY = orb_clampf(localY / ORB_WORLD_HEIGHT, 0.06f, 0.98f);
    float projectedDepth = orb_clampf(0.18f + normalizedY * 0.92f + entity->depthBias, 0.08f, 1.32f);
    float xSpan = (viewport.right - viewport.left) * (0.58f + projectedDepth * 0.22f);
    int horizon = viewport.top + (viewport.bottom - viewport.top) / 2;
    float orbitLift = cosf(orbitAngle + entity->id * 0.65f) * 6.0f * space->orbitalRadius;
    float baseX = (viewport.left + viewport.right) * 0.5f + ((normalizedX - 0.5f) * xSpan) + sinf(orbitAngle + entity->id * 0.33f) * 18.0f * space->rotationWarp;
    float baseY = horizon + projectedDepth * (viewport.bottom - horizon - 26) + orbitLift;
    float scale = breathScale * (0.34f + projectedDepth * 0.88f) * space->scale;
    float gamma = orb_compute_relativistic_gamma((ORBRenderEntity *)entity);
    float energyGlow = entity->physics.enabled ? entity->physics.visualEnergy : 0.0f;
    int width = orb_round_to_int(entity->size.x * scale);
    int height = orb_round_to_int(entity->size.y * scale);
    int left = orb_round_to_int(baseX - width * 0.5f);
    int top = orb_round_to_int(baseY - height);
    int shadowWidth = width + 10;
    COLORREF bodyColor = orb_lerp_color(orb_colorref_from_orb(entity->tint), RGB(245, 247, 250), energyGlow * 0.42f);
    COLORREF outlineColor = entity->collision.usesGreenBoundary ? RGB(0, 255, 0) : RGB(224, 230, 236);
    RECT bodyRect;

    bodyRect.left = left;
    bodyRect.top = top;
    bodyRect.right = left + width + orb_round_to_int((gamma - 1.0f) * 3.0f);
    bodyRect.bottom = top + height;

    orb_fill_rect(hdc, orb_round_to_int(baseX - shadowWidth * 0.5f), orb_round_to_int(baseY - 3.0f), orb_round_to_int(baseX + shadowWidth * 0.5f), orb_round_to_int(baseY + 3.0f), RGB(10, 14, 18));
    orb_fill_rect(hdc, bodyRect.left, bodyRect.top, bodyRect.right, bodyRect.bottom, bodyColor);
    orb_draw_space_border(hdc, bodyRect, outlineColor);

    if (entity->kind == ORB_ENTITY_ORB_NODE)
    {
        RECT ringRect;
        ringRect.left = bodyRect.left - 14;
        ringRect.top = bodyRect.top - 14;
        ringRect.right = bodyRect.right + 14;
        ringRect.bottom = bodyRect.bottom + 14;
        orb_draw_orbital_rings(hdc, ringRect, RGB(139, 214, 247), orbitAngle + entity->id * 0.2f, depth + 1);
    }
    if (width > 32)
    {
        orb_draw_label_sized(NULL, hdc, left + 4, top + 4, RGB(246, 248, 250), entity->label, 10);
    }
}

static void orb_draw_space_border(HDC hdc, RECT viewport, COLORREF color)
{
    HPEN pen = CreatePen(PS_SOLID, 1, color);
    HPEN oldPen = (HPEN)SelectObject(hdc, pen);
    HBRUSH oldBrush = (HBRUSH)SelectObject(hdc, GetStockObject(HOLLOW_BRUSH));
    Rectangle(hdc, viewport.left, viewport.top, viewport.right, viewport.bottom);
    SelectObject(hdc, oldBrush);
    SelectObject(hdc, oldPen);
    DeleteObject(pen);
}

static void orb_draw_orbital_rings(HDC hdc, RECT viewport, COLORREF color, float orbitAngle, int depth)
{
    HPEN pen = CreatePen(PS_SOLID, 1, color);
    HPEN oldPen = (HPEN)SelectObject(hdc, pen);
    HBRUSH oldBrush = (HBRUSH)SelectObject(hdc, GetStockObject(HOLLOW_BRUSH));
    int width = viewport.right - viewport.left;
    int height = viewport.bottom - viewport.top;
    int ringWidth = orb_round_to_int(width * (0.26f + depth * 0.04f));
    int ringHeight = orb_round_to_int(height * (0.18f + depth * 0.03f));
    int centerX = (viewport.left + viewport.right) / 2;
    int centerY = viewport.top + orb_round_to_int(height * 0.26f + sinf(orbitAngle) * 7.0f);
    int orbX = centerX + orb_round_to_int(cosf(orbitAngle) * (ringWidth * 0.5f));
    int orbY = centerY + orb_round_to_int(sinf(orbitAngle) * (ringHeight * 0.5f));

    Ellipse(hdc, centerX - ringWidth, centerY - ringHeight, centerX + ringWidth, centerY + ringHeight);
    Ellipse(hdc, centerX - ringWidth / 2, centerY - ringHeight / 2, centerX + ringWidth / 2, centerY + ringHeight / 2);
    SelectObject(hdc, oldBrush);
    SelectObject(hdc, oldPen);
    DeleteObject(pen);

    orb_fill_rect(hdc, orbX - 6, orbY - 6, orbX + 6, orbY + 6, color);
}

static int orb_ui_bitmap_ready(const ORBUIBitmapAsset *asset)
{
    return asset && asset->bitmap != NULL && asset->width > 0 && asset->height > 0;
}

static void orb_draw_bitmap_asset(HDC hdc, const ORBUIBitmapAsset *asset, RECT rect, BYTE alpha)
{
    RECT sourceRect = {0, 0, asset != NULL ? asset->width : 0, asset != NULL ? asset->height : 0};
    orb_draw_bitmap_asset_region(hdc, asset, rect, sourceRect, alpha);
}

static void orb_draw_bitmap_asset_region(HDC hdc, const ORBUIBitmapAsset *asset, RECT rect, RECT sourceRect, BYTE alpha)
{
    HDC memoryDc;
    HBITMAP oldBitmap;
    BLENDFUNCTION blend;
    if (!orb_ui_bitmap_ready(asset))
    {
        return;
    }

    memoryDc = CreateCompatibleDC(hdc);
    oldBitmap = (HBITMAP)SelectObject(memoryDc, asset->bitmap);
    blend.BlendOp = AC_SRC_OVER;
    blend.BlendFlags = 0;
    blend.SourceConstantAlpha = alpha;
    blend.AlphaFormat = AC_SRC_ALPHA;
    AlphaBlend(
        hdc,
        rect.left,
        rect.top,
        rect.right - rect.left,
        rect.bottom - rect.top,
        memoryDc,
        sourceRect.left,
        sourceRect.top,
        sourceRect.right - sourceRect.left,
        sourceRect.bottom - sourceRect.top,
        blend);
    SelectObject(memoryDc, oldBitmap);
    DeleteDC(memoryDc);
}

static const ORBUIBitmapAsset *orb_get_toolbar_asset(const ORBEngineSandbox *sandbox)
{
    switch (sandbox->currentCombatMode)
    {
    case ORB_COMBAT_TACTICAL:
        return &sandbox->uiShell.toolbarScripting;
    case ORB_COMBAT_QTE:
        return &sandbox->uiShell.toolbarAnimation;
    case ORB_COMBAT_OPEN:
        return &sandbox->uiShell.toolbarWorld;
    default:
        return &sandbox->uiShell.toolbarMaterials;
    }
}

static void orb_draw_ui_chrome(ORBEngineSandbox *sandbox, HDC hdc, RECT rect)
{
    RECT leftDock = {10, 126, 214, rect.bottom - 202};
    RECT rightDock = {rect.right - 226, 126, rect.right - 10, rect.bottom - 202};
    RECT workspaceTabs = {224, 8, rect.right - 224, 76};
    RECT primaryTabStrip = {224, 78, 620, 118};
    RECT secondaryTabStrip = {636, 78, 980, 118};
    RECT toolbarStrip = {rect.right - 392, 78, rect.right - 82, 126};
    RECT windowControls = {rect.right - 174, 12, rect.right - 22, 56};
    RECT timelinePanel = {236, rect.bottom - 190, rect.right - 236, rect.bottom - 52};
    RECT assetBrowserPanel = {18, rect.bottom - 194, 226, rect.bottom - 52};
    RECT consolePanel = {rect.right - 238, rect.bottom - 194, rect.right - 18, rect.bottom - 52};
    RECT toolFloat = {rect.right - 330, 142, rect.right - 44, 264};
    RECT tooltipRect = {rect.right - 376, rect.bottom - 238, rect.right - 34, rect.bottom - 190};

    if (orb_ui_bitmap_ready(&sandbox->uiShell.mainWindowFrame))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.mainWindowFrame, rect, 242);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.sceneHierarchyPanel))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.sceneHierarchyPanel, leftDock, 218);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.inspectorPanel))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.inspectorPanel, rightDock, 218);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.workspaceSwitcher))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.workspaceSwitcher, workspaceTabs, 245);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.primaryTabs))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.primaryTabs, primaryTabStrip, 235);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.secondaryTabs))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.secondaryTabs, secondaryTabStrip, 232);
    }
    if (orb_ui_bitmap_ready(orb_get_toolbar_asset(sandbox)))
    {
        orb_draw_bitmap_asset(hdc, orb_get_toolbar_asset(sandbox), toolbarStrip, 245);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.windowControls))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.windowControls, windowControls, 245);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.timelinePanel))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.timelinePanel, timelinePanel, 220);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.assetBrowserPanel))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.assetBrowserPanel, assetBrowserPanel, 214);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.consoleLogPanel))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.consoleLogPanel, consolePanel, 214);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.toolPropertiesFloat))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.toolPropertiesFloat, toolFloat, 226);
    }
    if (orb_ui_bitmap_ready(&sandbox->uiShell.tooltipShell))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.tooltipShell, tooltipRect, 236);
    }
}

static void orb_draw_overlay_panel(ORBEngineSandbox *sandbox, HDC hdc, RECT rect, COLORREF panelColor, COLORREF borderColor, const ORBUIBitmapAsset *asset)
{
    orb_fill_rect(hdc, rect.left, rect.top, rect.right, rect.bottom, panelColor);
    if (sandbox->uiShell.loaded && orb_ui_bitmap_ready(asset))
    {
        orb_draw_bitmap_asset(hdc, asset, rect, 236);
    }
    orb_draw_space_border(hdc, rect, borderColor);
}

static void orb_draw_status_bar(ORBEngineSandbox *sandbox, HDC hdc, RECT clientRect, const wchar_t *text)
{
    wchar_t buffer[384];
    RECT barRect;

    barRect.left = 18;
    barRect.top = clientRect.bottom - 42;
    barRect.right = clientRect.right - 18;
    barRect.bottom = clientRect.bottom - 14;
    orb_fill_rect(hdc, barRect.left, barRect.top, barRect.right, barRect.bottom, RGB(12, 16, 24));
    if (sandbox->uiShell.loaded && orb_ui_bitmap_ready(&sandbox->uiShell.notificationToast))
    {
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.notificationToast, barRect, 224);
    }
    orb_draw_space_border(hdc, barRect, RGB(63, 88, 120));
    if (sandbox->uiShell.loaded && orb_ui_bitmap_ready(&sandbox->uiShell.statusIndicators))
    {
        RECT iconRect = {barRect.left + 6, barRect.top + 2, barRect.left + 74, barRect.bottom - 2};
        orb_draw_bitmap_asset(hdc, &sandbox->uiShell.statusIndicators, iconRect, 236);
    }
    swprintf(buffer, 384, L"%ls | Physics coherence %.0f%%", text, sandbox->worldVisualCoherency * 100.0f);
    orb_draw_label_sized(sandbox, hdc, 84, clientRect.bottom - 36, RGB(224, 230, 236), buffer, 12);
}

static void orb_fill_rect(HDC hdc, int left, int top, int right, int bottom, COLORREF color)
{
    RECT rect;
    HBRUSH brush = CreateSolidBrush(color);
    rect.left = left;
    rect.top = top;
    rect.right = right;
    rect.bottom = bottom;
    FillRect(hdc, &rect, brush);
    DeleteObject(brush);
}

static int orb_resolve_font_glyph(const ORBUIShellAssets *uiShell, wchar_t glyph, const ORBUIBitmapAsset **asset, int *glyphIndex)
{
    const wchar_t *upperGlyphs = L"ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const wchar_t *lowerGlyphs = L"abcdefghijklmnopqrstuvwxyz.,!?':;-";
    const wchar_t *numericGlyphs = L"0123456789:+-*/=%.,$#@";
    const wchar_t *extendedGlyphs = L"[](){}<>/\\_|~^&;\"'`";
    const wchar_t *match;

    *asset = NULL;
    *glyphIndex = -1;
    if (glyph == 0 || uiShell == NULL)
    {
        return 0;
    }

    match = wcschr(upperGlyphs, glyph);
    if (match != NULL && orb_ui_bitmap_ready(&uiShell->fontUppercase))
    {
        *asset = &uiShell->fontUppercase;
        *glyphIndex = (int)(match - upperGlyphs);
        return 1;
    }

    match = wcschr(lowerGlyphs, glyph);
    if (match != NULL && orb_ui_bitmap_ready(&uiShell->fontLowercase))
    {
        *asset = &uiShell->fontLowercase;
        *glyphIndex = (int)(match - lowerGlyphs);
        return 1;
    }

    match = wcschr(numericGlyphs, glyph);
    if (match != NULL && orb_ui_bitmap_ready(&uiShell->fontNumeric))
    {
        *asset = &uiShell->fontNumeric;
        *glyphIndex = (int)(match - numericGlyphs);
        return 1;
    }

    match = wcschr(extendedGlyphs, glyph);
    if (match != NULL && orb_ui_bitmap_ready(&uiShell->fontExtendedUi))
    {
        *asset = &uiShell->fontExtendedUi;
        *glyphIndex = (int)(match - extendedGlyphs);
        return 1;
    }

    return 0;
}

static int orb_draw_atlas_text(ORBEngineSandbox *sandbox, HDC hdc, int x, int y, COLORREF color, const wchar_t *text, int glyphHeight)
{
    int cursorX = x;
    int usedAtlas = 0;

    if (sandbox == NULL || text == NULL || text[0] == 0 || !sandbox->uiShell.loaded)
    {
        return 0;
    }

    while (*text)
    {
        const ORBUIBitmapAsset *asset;
        int glyphIndex;

        if (*text == L' ')
        {
            cursorX += glyphHeight / 2;
            ++text;
            continue;
        }
        if (*text == L'\t')
        {
            cursorX += glyphHeight * 2;
            ++text;
            continue;
        }

        if (orb_resolve_font_glyph(&sandbox->uiShell, *text, &asset, &glyphIndex))
        {
            RECT sourceRect;
            RECT destRect;
            int cellWidth = asset->width / 8;
            int cellHeight = asset->height / 8;
            int column = glyphIndex % 8;
            int row = glyphIndex / 8;
            int drawWidth = orb_round_to_int(glyphHeight * 0.72f);

            sourceRect.left = column * cellWidth;
            sourceRect.top = row * cellHeight;
            sourceRect.right = sourceRect.left + cellWidth;
            sourceRect.bottom = sourceRect.top + cellHeight;
            destRect.left = cursorX;
            destRect.top = y;
            destRect.right = cursorX + drawWidth;
            destRect.bottom = y + glyphHeight;
            orb_draw_bitmap_asset_region(hdc, asset, destRect, sourceRect, 255);
            cursorX += drawWidth + 1;
            usedAtlas = 1;
        }
        else
        {
            SIZE extent;
            wchar_t fallback[2];
            fallback[0] = *text;
            fallback[1] = 0;
            SetBkMode(hdc, TRANSPARENT);
            SetTextColor(hdc, color);
            TextOutW(hdc, cursorX, y, fallback, 1);
            GetTextExtentPoint32W(hdc, fallback, 1, &extent);
            cursorX += extent.cx > 0 ? extent.cx : glyphHeight / 2;
        }

        ++text;
    }

    return usedAtlas;
}

static void orb_draw_label_sized(ORBEngineSandbox *sandbox, HDC hdc, int x, int y, COLORREF color, const wchar_t *text, int glyphHeight)
{
    if (!orb_draw_atlas_text(sandbox, hdc, x, y, color, text, glyphHeight))
    {
        SetBkMode(hdc, TRANSPARENT);
        SetTextColor(hdc, color);
        TextOutW(hdc, x, y, text, (int)wcslen(text));
    }
}

static void orb_draw_label(ORBEngineSandbox *sandbox, HDC hdc, int x, int y, COLORREF color, const wchar_t *text)
{
    orb_draw_label_sized(sandbox, hdc, x, y, color, text, 16);
}