#ifndef ORBENGINE_H
#define ORBENGINE_H

#include <windows.h>
#include <stdint.h>

#define ORB_MAX_SPACE_NODES 64
#define ORB_MAX_CHILDREN 8
#define ORB_MAX_ENTITIES 128
#define ORB_MAX_COLLISION_POINTS 64
#define ORB_MAX_OPEN_ARENA_ENEMIES 16

typedef enum ORBSpaceKind
{
    ORB_SPACE_SURFACE,
    ORB_SPACE_AGRICULTURE,
    ORB_SPACE_SIMULATOR,
    ORB_SPACE_RECURSIVE_POCKET
} ORBSpaceKind;

typedef enum ORBEntityKind
{
    ORB_ENTITY_PLAYER,
    ORB_ENTITY_RAFT,
    ORB_ENTITY_CROP_BED,
    ORB_ENTITY_GATE,
    ORB_ENTITY_ENEMY,
    ORB_ENTITY_ORB_NODE,
    ORB_ENTITY_DECOR
} ORBEntityKind;

typedef enum ORBCombatMode
{
    ORB_COMBAT_NONE,
    ORB_COMBAT_TACTICAL,
    ORB_COMBAT_QTE,
    ORB_COMBAT_OPEN
} ORBCombatMode;

typedef enum ORBScaleDomain
{
    ORB_SCALE_SUBATOMIC,
    ORB_SCALE_MOLECULAR,
    ORB_SCALE_MESOSCOPIC,
    ORB_SCALE_HUMAN
} ORBScaleDomain;

typedef struct ORBVec2
{
    float x;
    float y;
} ORBVec2;

typedef struct ORBColor
{
    uint8_t r;
    uint8_t g;
    uint8_t b;
    uint8_t a;
} ORBColor;

typedef struct ORBPhysicsBody
{
    int enabled;
    int dynamicBody;
    int pinned;
    int affectedByGravity;
    int affectedByCharge;
    int affectedByThermal;
    ORBScaleDomain scaleDomain;
    float metersPerWorldUnit;
    float massKg;
    float chargeCoulombs;
    float temperatureKelvin;
    float dragCoefficient;
    float areaSquareMeters;
    float restitution;
    float cohesion;
    float anchorSpring;
    float anchorDamping;
    float radiusMeters;
    ORBVec2 velocity;
    ORBVec2 accumulatedForce;
    ORBVec2 anchorPosition;
    float visualEnergy;
} ORBPhysicsBody;

typedef struct ORBCollisionShape
{
    ORBVec2 points[ORB_MAX_COLLISION_POINTS];
    int pointCount;
    COLORREF debugColor;
    int usesGreenBoundary;
} ORBCollisionShape;

typedef struct ORBRenderEntity
{
    int id;
    int spaceId;
    ORBEntityKind kind;
    ORBVec2 position;
    ORBVec2 size;
    ORBColor tint;
    ORBCollisionShape collision;
    wchar_t label[64];
    float depthBias;
    int renderLayer;
    int active;
    ORBPhysicsBody physics;
} ORBRenderEntity;

typedef struct ORBSpaceNode
{
    int id;
    int parentId;
    int childIds[ORB_MAX_CHILDREN];
    int childCount;
    ORBSpaceKind kind;
    ORBVec2 origin;
    float scale;
    float rotationWarp;
    float breathingAmplitude;
    float breathingRate;
    float orbitalRadius;
    float orbitalSpeed;
    ORBVec2 gravityVector;
    float ambientTemperatureKelvin;
    float mediumDensity;
    float staticPressure;
    float simulationRate;
    wchar_t name[64];
} ORBSpaceNode;

typedef struct ORBEngineWorld
{
    ORBSpaceNode spaces[ORB_MAX_SPACE_NODES];
    int spaceCount;
    ORBRenderEntity entities[ORB_MAX_ENTITIES];
    int entityCount;
} ORBEngineWorld;

typedef struct ORBOpenArenaState
{
    int seed;
    ORBVec2 enemyPositions[ORB_MAX_OPEN_ARENA_ENEMIES];
    ORBVec2 enemyVelocities[ORB_MAX_OPEN_ARENA_ENEMIES];
    int enemyAlive[ORB_MAX_OPEN_ARENA_ENEMIES];
    float enemyMassKg[ORB_MAX_OPEN_ARENA_ENEMIES];
    float enemyChargeCoulombs[ORB_MAX_OPEN_ARENA_ENEMIES];
    float enemyTemperatureKelvin[ORB_MAX_OPEN_ARENA_ENEMIES];
    float enemyVisualEnergy[ORB_MAX_OPEN_ARENA_ENEMIES];
    int enemyCount;
} ORBOpenArenaState;

typedef struct ORBDimensionViewConfig
{
    float depthScale;
    float horizonLift;
    float spriteVerticalBias;
    float fogDensity;
    float volumetricScatter;
    float collisionVisualInset;
    float anchorNodeShearBias;
    int layeredFogEnabled;
    int spriteShearEnabled;
    int groundedShadowEnabled;
    int dimensionalAnchorNodesEnabled;
    int curvatureDepthTranslationEnabled;
    int topCapTetherProjectionEnabled;
} ORBDimensionViewConfig;

typedef struct ORBKineticsConfig
{
    float collisionSkinWidth;
    float pickupRadius;
    float shelterRadius;
    float projectileHeightBias;
    float aerialRecoveryWindow;
    float silhouettePrecisionBias;
    int exactMaskCollisionEnabled;
    int perFrameHitboxEnabled;
    int authoredSurfaceTagsEnabled;
    int invisibleHitSilhouetteEnabled;
    int anchorLinkedCollisionEnabled;
    int pixelPreciseDetectionIntentEnabled;
} ORBKineticsConfig;

typedef struct ORBGlueConfig
{
    float focusTurnRate;
    float moistureHealingBias;
    float breathingResonanceBias;
    int audioZoneBindingEnabled;
    int animationCollisionBindingEnabled;
    int shrineProgressionBindingEnabled;
    int codexDiscoveryBindingEnabled;
    int dimensionalAnchorBindingEnabled;
    int equipmentSocketBindingEnabled;
    int precisionTelemetryBindingEnabled;
} ORBGlueConfig;

typedef struct ORBUIBitmapAsset
{
    HBITMAP bitmap;
    int width;
    int height;
} ORBUIBitmapAsset;

typedef struct ORBUIShellAssets
{
    int loaded;
    ORBUIBitmapAsset mainWindowFrame;
    ORBUIBitmapAsset sceneHierarchyPanel;
    ORBUIBitmapAsset inspectorPanel;
    ORBUIBitmapAsset assetBrowserPanel;
    ORBUIBitmapAsset consoleLogPanel;
    ORBUIBitmapAsset timelinePanel;
    ORBUIBitmapAsset toolPropertiesFloat;
    ORBUIBitmapAsset modalTemplate;
    ORBUIBitmapAsset contextMenuShell;
    ORBUIBitmapAsset dropdownShell;
    ORBUIBitmapAsset notificationToast;
    ORBUIBitmapAsset tooltipShell;
    ORBUIBitmapAsset dialogChoiceGrid;
    ORBUIBitmapAsset workspaceSwitcher;
    ORBUIBitmapAsset primaryTabs;
    ORBUIBitmapAsset secondaryTabs;
    ORBUIBitmapAsset toolbarWorld;
    ORBUIBitmapAsset toolbarScripting;
    ORBUIBitmapAsset toolbarAnimation;
    ORBUIBitmapAsset toolbarMaterials;
    ORBUIBitmapAsset statusIndicators;
    ORBUIBitmapAsset windowControls;
    ORBUIBitmapAsset fontUppercase;
    ORBUIBitmapAsset fontLowercase;
    ORBUIBitmapAsset fontNumeric;
    ORBUIBitmapAsset fontExtendedUi;
    ORBUIBitmapAsset cursorPrecision;
    HCURSOR precisionCursor;
} ORBUIShellAssets;

typedef struct ORBEngineSandbox
{
    ORBEngineWorld world;
    ORBCombatMode currentCombatMode;
    int playerEntityId;
    int tacticalPlayerHp;
    int tacticalEnemyHp;
    wchar_t qteSequence[16];
    int qteLength;
    int qteIndex;
    ORBOpenArenaState openArena;
    int showAgriculture;
    int showSimulatorMenu;
    int playerOnRaft;
    int raftTraveling;
    float raftTravelProgress;
    float renderTime;
    int recursionDepthLimit;
    int activeRootSpaceId;
    int physicsEnabled;
    float physicsTimeScale;
    float worldVisualCoherency;
    ORBDimensionViewConfig dimensionView;
    ORBKineticsConfig kinetics;
    ORBGlueConfig glue;
    ORBUIShellAssets uiShell;
    wchar_t statusLine[256];
} ORBEngineSandbox;

void orb_vec2_set(ORBVec2 *value, float x, float y);
void orb_collision_make_rect(ORBCollisionShape *shape, float x, float y, float width, float height, COLORREF debugColor, int usesGreenBoundary);
void orb_world_init(ORBEngineWorld *world);
ORBSpaceNode *orb_world_add_space(ORBEngineWorld *world, ORBSpaceKind kind, int parentId, const wchar_t *name, float x, float y, float scale, float rotationWarp);
ORBRenderEntity *orb_world_add_entity(ORBEngineWorld *world, int spaceId, ORBEntityKind kind, const wchar_t *label, float x, float y, float width, float height, ORBColor tint);
void orb_apply_innsmouth_profiles(ORBEngineSandbox *sandbox);
void orb_sandbox_init(ORBEngineSandbox *sandbox);
void orb_sandbox_step(ORBEngineSandbox *sandbox, float deltaSeconds);
void orb_sandbox_handle_key(ORBEngineSandbox *sandbox, WPARAM key);
void orb_sandbox_render(ORBEngineSandbox *sandbox, HDC hdc, RECT clientRect);

#endif