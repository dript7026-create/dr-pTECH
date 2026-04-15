#ifndef PXGBPROG_H
#define PXGBPROG_H

#include <stdint.h>

#ifndef FARMERS_FEATHER_BANKED
#if defined(__SDCC) || defined(SDCC)
#define FARMERS_FEATHER_BANKED __banked
#else
#define FARMERS_FEATHER_BANKED
#endif
#endif

#define PXGBPROG_TILE_BYTES 16u
#define PXGBPROG_TILE_PIXELS 64u
#define PXGBPROG_MAX_TILES 8u
#define PXGBPROG_MAX_PROGRAMS 8u
#define PXGBPROG_MAX_PRIMITIVES 48u

typedef enum {
    PXGBPROG_OVERLAY_NONE = 0u,
    PXGBPROG_OVERLAY_HORNS = 1u,
    PXGBPROG_OVERLAY_SPINES = 2u,
    PXGBPROG_OVERLAY_CLOAK = 3u,
    PXGBPROG_OVERLAY_HALO = 4u,
    PXGBPROG_OVERLAY_BLADE = 5u
} PxGbProgOverlay;

typedef struct {
    uint8_t target_tile;
    uint8_t overlay;
    uint8_t intensity;
    uint8_t flags;
} PxGbProgTileProgram;

typedef struct {
    uint8_t program_count;
    PxGbProgTileProgram programs[PXGBPROG_MAX_PROGRAMS];
} PxGbProgManifest;

typedef struct {
    uint8_t weapon_rank;
    uint8_t armor_rank;
    uint8_t honor;
    uint8_t pressure;
    uint8_t passage_bias;
    uint8_t phase;
    uint8_t boss_active;
    uint8_t render_mode;
} PxGbProgCompileOptions;

typedef enum {
    PXGBPROG_PRIM_LINE = 0u,
    PXGBPROG_PRIM_BOX = 1u,
    PXGBPROG_PRIM_DISC = 2u,
    PXGBPROG_PRIM_RING = 3u
} PxGbProgPrimitiveKind;

typedef struct {
    uint8_t target_tile;
    uint8_t kind;
    uint8_t shade;
    uint8_t flags;
    int8_t x0;
    int8_t y0;
    int8_t x1;
    int8_t y1;
    int8_t vx;
    int8_t vy;
    uint8_t radius;
} PxGbProgPrimitive;

typedef struct {
    uint8_t primitive_count;
    PxGbProgPrimitive primitives[PXGBPROG_MAX_PRIMITIVES];
} PxGbProgVectorScene;

typedef struct {
    uint8_t tile_count;
    uint8_t pixels[PXGBPROG_MAX_TILES * PXGBPROG_TILE_PIXELS];
    PxGbProgVectorScene scene;
} PxGbProgPipeline;

void pxgbprog_copy_tiles(uint8_t *dst_tiles, const uint8_t *src_tiles, uint8_t tile_count);
void pxgbprog_apply_manifest(uint8_t *tiles, uint8_t tile_count, const PxGbProgManifest *manifest, const PxGbProgCompileOptions *options);
void pxgbprog_pipeline_begin(PxGbProgPipeline *pipeline, const uint8_t *base_tiles, uint8_t tile_count) FARMERS_FEATHER_BANKED;
void pxgbprog_pipeline_enqueue_manifest(PxGbProgPipeline *pipeline, const PxGbProgManifest *manifest, const PxGbProgCompileOptions *options) FARMERS_FEATHER_BANKED;
void pxgbprog_pipeline_simulate(PxGbProgPipeline *pipeline, const PxGbProgCompileOptions *options) FARMERS_FEATHER_BANKED;
void pxgbprog_pipeline_render(const PxGbProgPipeline *pipeline, uint8_t *tiles_out) FARMERS_FEATHER_BANKED;

const PxGbProgManifest *pxgbprog_manifest_player(void);
const PxGbProgManifest *pxgbprog_manifest_kin(void);
const PxGbProgManifest *pxgbprog_manifest_boss(void);

#endif