#include "../include/pxgbprog.h"

static const PxGbProgManifest kPlayerManifest = {
    4u,
    {
        {0u, PXGBPROG_OVERLAY_CLOAK, 1u, 0u},
        {1u, PXGBPROG_OVERLAY_CLOAK, 1u, 0u},
        {2u, PXGBPROG_OVERLAY_BLADE, 2u, 0u},
        {3u, PXGBPROG_OVERLAY_BLADE, 2u, 0u}
    }
};

static const PxGbProgManifest kKinManifest = {
    2u,
    {
        {4u, PXGBPROG_OVERLAY_HORNS, 1u, 0u},
        {4u, PXGBPROG_OVERLAY_SPINES, 2u, 0u}
    }
};

static const PxGbProgManifest kBossManifest = {
    3u,
    {
        {5u, PXGBPROG_OVERLAY_HORNS, 2u, 0u},
        {5u, PXGBPROG_OVERLAY_HALO, 2u, 0u},
        {5u, PXGBPROG_OVERLAY_SPINES, 2u, 0u}
    }
};

void pxgbprog_copy_tiles(uint8_t *dst_tiles, const uint8_t *src_tiles, uint8_t tile_count) {
    uint16_t index;
    uint16_t total_bytes;
    if (tile_count > PXGBPROG_MAX_TILES) tile_count = PXGBPROG_MAX_TILES;
    total_bytes = (uint16_t)tile_count * PXGBPROG_TILE_BYTES;
    for (index = 0u; index < total_bytes; ++index) {
        dst_tiles[index] = src_tiles[index];
    }
}

void pxgbprog_apply_manifest(uint8_t *tiles, uint8_t tile_count, const PxGbProgManifest *manifest, const PxGbProgCompileOptions *options) {
    PxGbProgPipeline pipeline;
    if (!tiles || !manifest || !options) return;
    pxgbprog_pipeline_begin(&pipeline, tiles, tile_count);
    pxgbprog_pipeline_enqueue_manifest(&pipeline, manifest, options);
    pxgbprog_pipeline_simulate(&pipeline, options);
    pxgbprog_pipeline_render(&pipeline, tiles);
}

const PxGbProgManifest *pxgbprog_manifest_player(void) {
    return &kPlayerManifest;
}

const PxGbProgManifest *pxgbprog_manifest_kin(void) {
    return &kKinManifest;
}

const PxGbProgManifest *pxgbprog_manifest_boss(void) {
    return &kBossManifest;
}