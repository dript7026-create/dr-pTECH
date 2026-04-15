#pragma bank 255

#include "../include/pxgbprog.h"

static uint8_t pxgbprog_pipeline_clamp_u8(int16_t value) {
    if (value < 0) return 0u;
    if (value > 255) return 255u;
    return (uint8_t)value;
}

static int8_t pxgbprog_pipeline_clamp_i8(int16_t value, int8_t minimum, int8_t maximum) {
    if (value < minimum) return minimum;
    if (value > maximum) return maximum;
    return (int8_t)value;
}

static uint8_t pxgbprog_pipeline_overlay_enabled(const PxGbProgTileProgram *program, const PxGbProgCompileOptions *options) {
    if (program->overlay == PXGBPROG_OVERLAY_CLOAK) return (options->armor_rank > 0u) ? 1u : 0u;
    if (program->overlay == PXGBPROG_OVERLAY_BLADE) return (options->weapon_rank > 0u) ? 1u : 0u;
    if (program->overlay == PXGBPROG_OVERLAY_HALO) return (options->honor > 120u || options->boss_active || options->pressure > 140u) ? 1u : 0u;
    return 1u;
}

static void pxgbprog_pipeline_plot(PxGbProgPipeline *pipeline, uint8_t target_tile, int8_t x, int8_t y, uint8_t shade) {
    uint16_t pixel_index;
    if (!pipeline) return;
    if (target_tile >= pipeline->tile_count) return;
    if (x < 0 || x > 7 || y < 0 || y > 7) return;
    pixel_index = (uint16_t)target_tile * PXGBPROG_TILE_PIXELS;
    pixel_index += (uint16_t)y * 8u;
    pixel_index += (uint16_t)x;
    if (shade > pipeline->pixels[pixel_index]) {
        pipeline->pixels[pixel_index] = shade;
    }
}

static void pxgbprog_pipeline_draw_line(PxGbProgPipeline *pipeline, const PxGbProgPrimitive *primitive) {
    int8_t x0;
    int8_t y0;
    int8_t x1;
    int8_t y1;
    int8_t dx;
    int8_t sx;
    int8_t dy;
    int8_t sy;
    int8_t err;
    int8_t e2;

    x0 = primitive->x0;
    y0 = primitive->y0;
    x1 = primitive->x1;
    y1 = primitive->y1;
    dx = (x0 < x1) ? (int8_t)(x1 - x0) : (int8_t)(x0 - x1);
    sx = (x0 < x1) ? 1 : -1;
    dy = (y0 < y1) ? (int8_t)(y0 - y1) : (int8_t)(y1 - y0);
    sy = (y0 < y1) ? 1 : -1;
    err = dx + dy;

    while (1) {
        pxgbprog_pipeline_plot(pipeline, primitive->target_tile, x0, y0, primitive->shade);
        if (x0 == x1 && y0 == y1) break;
        e2 = (int8_t)(err << 1u);
        if (e2 >= dy) {
            err = (int8_t)(err + dy);
            x0 = (int8_t)(x0 + sx);
        }
        if (e2 <= dx) {
            err = (int8_t)(err + dx);
            y0 = (int8_t)(y0 + sy);
        }
    }
}

static void pxgbprog_pipeline_draw_box(PxGbProgPipeline *pipeline, const PxGbProgPrimitive *primitive) {
    int8_t x;
    int8_t y;
    for (y = primitive->y0; y <= primitive->y1; ++y) {
        for (x = primitive->x0; x <= primitive->x1; ++x) {
            if ((primitive->flags & 0x01u) || y == primitive->y0 || y == primitive->y1 || x == primitive->x0 || x == primitive->x1) {
                pxgbprog_pipeline_plot(pipeline, primitive->target_tile, x, y, primitive->shade);
            }
        }
    }
}

static void pxgbprog_pipeline_draw_disc(PxGbProgPipeline *pipeline, const PxGbProgPrimitive *primitive) {
    int8_t x;
    int8_t y;
    int16_t radius_sq;
    radius_sq = (int16_t)primitive->radius * primitive->radius;
    for (y = (int8_t)(primitive->y0 - primitive->radius); y <= (int8_t)(primitive->y0 + primitive->radius); ++y) {
        for (x = (int8_t)(primitive->x0 - primitive->radius); x <= (int8_t)(primitive->x0 + primitive->radius); ++x) {
            int16_t dx;
            int16_t dy;
            dx = (int16_t)x - primitive->x0;
            dy = (int16_t)y - primitive->y0;
            if ((dx * dx) + (dy * dy) <= radius_sq) {
                pxgbprog_pipeline_plot(pipeline, primitive->target_tile, x, y, primitive->shade);
            }
        }
    }
}

static void pxgbprog_pipeline_draw_ring(PxGbProgPipeline *pipeline, const PxGbProgPrimitive *primitive) {
    int8_t x;
    int8_t y;
    int16_t radius_sq;
    int16_t inner_sq;
    radius_sq = (int16_t)primitive->radius * primitive->radius;
    inner_sq = (primitive->radius > 1u) ? (int16_t)(primitive->radius - 1u) * (primitive->radius - 1u) : 0u;
    for (y = (int8_t)(primitive->y0 - primitive->radius); y <= (int8_t)(primitive->y0 + primitive->radius); ++y) {
        for (x = (int8_t)(primitive->x0 - primitive->radius); x <= (int8_t)(primitive->x0 + primitive->radius); ++x) {
            int16_t dx;
            int16_t dy;
            int16_t dist_sq;
            dx = (int16_t)x - primitive->x0;
            dy = (int16_t)y - primitive->y0;
            dist_sq = (dx * dx) + (dy * dy);
            if (dist_sq <= radius_sq && dist_sq >= inner_sq) {
                pxgbprog_pipeline_plot(pipeline, primitive->target_tile, x, y, primitive->shade);
            }
        }
    }
}

static void pxgbprog_pipeline_scene_push(PxGbProgVectorScene *scene, uint8_t target_tile, uint8_t kind, uint8_t shade, uint8_t flags, int8_t x0, int8_t y0, int8_t x1, int8_t y1, int8_t vx, int8_t vy, uint8_t radius) {
    PxGbProgPrimitive *primitive;
    if (!scene) return;
    if (scene->primitive_count >= PXGBPROG_MAX_PRIMITIVES) return;
    primitive = &scene->primitives[scene->primitive_count++];
    primitive->target_tile = target_tile;
    primitive->kind = kind;
    primitive->shade = shade;
    primitive->flags = flags;
    primitive->x0 = x0;
    primitive->y0 = y0;
    primitive->x1 = x1;
    primitive->y1 = y1;
    primitive->vx = vx;
    primitive->vy = vy;
    primitive->radius = radius;
}

static void pxgbprog_pipeline_append_program(PxGbProgVectorScene *scene, const PxGbProgTileProgram *program, const PxGbProgCompileOptions *options) {
    uint8_t shade;
    if (!scene || !program || !options) return;
    shade = (options->pressure > 132u) ? 3u : ((options->honor > 148u) ? 2u : 1u);

    if (program->overlay == PXGBPROG_OVERLAY_CLOAK) {
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_BOX, shade, 0x01u, 1, 4, 6, 7, 0, 1, 0u);
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_LINE, (uint8_t)(shade + 1u), 0u, 2, 3, 1, 6, -1, 1, 0u);
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_LINE, (uint8_t)(shade + 1u), 0u, 5, 3, 6, 6, 1, 1, 0u);
    } else if (program->overlay == PXGBPROG_OVERLAY_BLADE) {
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_LINE, 3u, 0u, 4, 3, 7, 0, 1, -1, 0u);
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_DISC, 2u, 0u, 6, 1, 0, 0, 1, -1, 1u);
    } else if (program->overlay == PXGBPROG_OVERLAY_HORNS) {
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_LINE, 3u, 0u, 2, 2, 1, 0, -1, -1, 0u);
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_LINE, 3u, 0u, 5, 2, 6, 0, 1, -1, 0u);
    } else if (program->overlay == PXGBPROG_OVERLAY_SPINES) {
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_LINE, 2u, 0u, 6, 2, 7, 1, 1, 0, 0u);
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_LINE, 2u, 0u, 6, 4, 7, 4, 1, 0, 0u);
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_LINE, 2u, 0u, 5, 6, 7, 7, 1, 1, 0u);
    } else if (program->overlay == PXGBPROG_OVERLAY_HALO) {
        pxgbprog_pipeline_scene_push(scene, program->target_tile, PXGBPROG_PRIM_RING, 2u, 0u, 3, 1, 0, 0, 0, -1, 2u);
    }
}

static void pxgbprog_pipeline_simulate_scene(PxGbProgVectorScene *scene, const PxGbProgCompileOptions *options) {
    uint8_t index;
    int8_t wave;
    if (!scene || !options) return;
    wave = (int8_t)((options->passage_bias + options->phase + options->render_mode) & 0x03u);
    wave = (int8_t)(wave - 1);

    for (index = 0u; index < scene->primitive_count; ++index) {
        PxGbProgPrimitive *primitive;
        int8_t drift_x;
        int8_t drift_y;
        primitive = &scene->primitives[index];
        drift_x = (int8_t)((primitive->vx * ((options->pressure >> 6u) + options->render_mode + 1u)) / 2);
        drift_y = (int8_t)((primitive->vy * ((options->phase & 0x03u) + 1u)) / 2);
        primitive->x0 = pxgbprog_pipeline_clamp_i8((int16_t)primitive->x0 + drift_x + wave, 0, 7);
        primitive->y0 = pxgbprog_pipeline_clamp_i8((int16_t)primitive->y0 + drift_y, 0, 7);
        primitive->x1 = pxgbprog_pipeline_clamp_i8((int16_t)primitive->x1 + drift_x + ((options->render_mode == 1u) ? 1 : 0), 0, 7);
        primitive->y1 = pxgbprog_pipeline_clamp_i8((int16_t)primitive->y1 + drift_y + ((options->boss_active && primitive->kind == PXGBPROG_PRIM_LINE) ? 1 : 0), 0, 7);
        if (primitive->kind == PXGBPROG_PRIM_RING) {
            primitive->radius = pxgbprog_pipeline_clamp_u8((int16_t)primitive->radius + ((options->honor > 148u) ? 1 : 0) - ((options->pressure > 160u) ? 1 : 0));
            if (primitive->radius == 0u) primitive->radius = 1u;
        }
    }
}

static void pxgbprog_pipeline_decode(PxGbProgPipeline *pipeline, const uint8_t *base_tiles, uint8_t tile_count) {
    uint8_t tile;
    if (!pipeline || !base_tiles) return;
    for (tile = 0u; tile < tile_count; ++tile) {
        uint8_t row;
        uint16_t tile_base;
        tile_base = (uint16_t)tile * PXGBPROG_TILE_BYTES;
        for (row = 0u; row < 8u; ++row) {
            uint8_t low;
            uint8_t high;
            uint8_t col;
            low = base_tiles[tile_base + (uint16_t)row * 2u];
            high = base_tiles[tile_base + (uint16_t)row * 2u + 1u];
            for (col = 0u; col < 8u; ++col) {
                uint8_t bit;
                uint16_t pixel_index;
                bit = (uint8_t)(7u - col);
                pixel_index = (uint16_t)tile * PXGBPROG_TILE_PIXELS;
                pixel_index += (uint16_t)row * 8u + col;
                pipeline->pixels[pixel_index] = (uint8_t)(((high >> bit) & 0x01u) << 1u);
                pipeline->pixels[pixel_index] |= (uint8_t)((low >> bit) & 0x01u);
            }
        }
    }
}

void pxgbprog_pipeline_begin(PxGbProgPipeline *pipeline, const uint8_t *base_tiles, uint8_t tile_count) FARMERS_FEATHER_BANKED {
    uint16_t index;
    if (!pipeline || !base_tiles) return;
    if (tile_count > PXGBPROG_MAX_TILES) tile_count = PXGBPROG_MAX_TILES;
    pipeline->tile_count = tile_count;
    pipeline->scene.primitive_count = 0u;
    for (index = 0u; index < (uint16_t)(PXGBPROG_MAX_TILES * PXGBPROG_TILE_PIXELS); ++index) {
        pipeline->pixels[index] = 0u;
    }
    pxgbprog_pipeline_decode(pipeline, base_tiles, tile_count);
}

void pxgbprog_pipeline_enqueue_manifest(PxGbProgPipeline *pipeline, const PxGbProgManifest *manifest, const PxGbProgCompileOptions *options) FARMERS_FEATHER_BANKED {
    uint8_t index;
    if (!pipeline || !manifest || !options) return;
    for (index = 0u; index < manifest->program_count; ++index) {
        const PxGbProgTileProgram *program;
        program = &manifest->programs[index];
        if (program->target_tile >= pipeline->tile_count) continue;
        if (!pxgbprog_pipeline_overlay_enabled(program, options)) continue;
        pxgbprog_pipeline_append_program(&pipeline->scene, program, options);
    }
}

void pxgbprog_pipeline_simulate(PxGbProgPipeline *pipeline, const PxGbProgCompileOptions *options) FARMERS_FEATHER_BANKED {
    if (!pipeline || !options) return;
    pxgbprog_pipeline_simulate_scene(&pipeline->scene, options);
}

void pxgbprog_pipeline_render(const PxGbProgPipeline *pipeline, uint8_t *tiles_out) FARMERS_FEATHER_BANKED {
    PxGbProgPipeline mutable_pipeline;
    uint8_t index;
    if (!pipeline || !tiles_out) return;

    mutable_pipeline = *pipeline;
    for (index = 0u; index < mutable_pipeline.scene.primitive_count; ++index) {
        const PxGbProgPrimitive *primitive;
        primitive = &mutable_pipeline.scene.primitives[index];
        if (primitive->kind == PXGBPROG_PRIM_LINE) {
            pxgbprog_pipeline_draw_line(&mutable_pipeline, primitive);
        } else if (primitive->kind == PXGBPROG_PRIM_BOX) {
            pxgbprog_pipeline_draw_box(&mutable_pipeline, primitive);
        } else if (primitive->kind == PXGBPROG_PRIM_DISC) {
            pxgbprog_pipeline_draw_disc(&mutable_pipeline, primitive);
        } else if (primitive->kind == PXGBPROG_PRIM_RING) {
            pxgbprog_pipeline_draw_ring(&mutable_pipeline, primitive);
        }
    }

    for (index = 0u; index < mutable_pipeline.tile_count; ++index) {
        uint8_t row;
        uint16_t tile_base;
        tile_base = (uint16_t)index * PXGBPROG_TILE_BYTES;
        for (row = 0u; row < 8u; ++row) {
            uint8_t col;
            uint8_t low;
            uint8_t high;
            low = 0u;
            high = 0u;
            for (col = 0u; col < 8u; ++col) {
                uint8_t pixel;
                uint8_t bit;
                uint16_t pixel_index;
                bit = (uint8_t)(7u - col);
                pixel_index = (uint16_t)index * PXGBPROG_TILE_PIXELS;
                pixel_index += (uint16_t)row * 8u + col;
                pixel = mutable_pipeline.pixels[pixel_index] & 0x03u;
                low |= (uint8_t)((pixel & 0x01u) << bit);
                high |= (uint8_t)(((pixel >> 1u) & 0x01u) << bit);
            }
            tiles_out[tile_base + (uint16_t)row * 2u] = low;
            tiles_out[tile_base + (uint16_t)row * 2u + 1u] = high;
        }
    }
}