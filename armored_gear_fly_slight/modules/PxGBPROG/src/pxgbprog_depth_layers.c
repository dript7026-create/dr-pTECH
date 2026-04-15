#include "pxgbprog_depth_layers.h"
#include <string.h>

/* ============================================================================
   Fixed-Point Math Utilities
   ============================================================================ */

static inline uint8_t fp_mul_q8(uint8_t a, uint8_t b) {
    return (uint16_t)a * b / 255u;
}

static inline uint8_t fp_mul_q4(uint8_t a, uint8_t b) {
    return ((uint16_t)a * b) >> 4u;
}

static inline uint8_t fp_clamp_q8(uint16_t value) {
    if (value > 255u) return 255u;
    return (uint8_t)value;
}

/* ============================================================================
   Context-Adaptive Layer Generation (Functions 1-15)
   ============================================================================ */

uint8_t pxgbprog_depth_compute_ratio_q8(uint8_t layer_index, uint8_t total_layers) {
    /**
     * Compute normalized depth ratio (0.0 at surface, 1.0 at deepest layer).
     * Q8 Fixed-point: 0-255 represents 0.0-1.0
     */
    if (total_layers <= 1u) return layer_index ? 255u : 0u;
    return (uint16_t)layer_index * 255u / (total_layers - 1u);
}

uint8_t pxgbprog_depth_compute_silhouette_reduction_q8(uint8_t layer_index, uint8_t total_layers, uint8_t curve_mode) {
    /**
     * Cubic attenuation curve: (depth_ratio^3) * 0.88
     * At surface: 0, at depth: ~224/255 (88%)
     */
    uint8_t depth_q8 = pxgbprog_depth_compute_ratio_q8(layer_index, total_layers);
    
    switch (curve_mode) {
        case 0u: {
            /* Cubic: depth^3 * 0.88 */
            uint16_t depth_q4 = (uint16_t)depth_q8 * depth_q8 / 256u;
            uint16_t depth_cubed = depth_q4 * depth_q8 / 256u;
            return fp_clamp_q8(depth_cubed * 224u / 255u);
        }
        case 1u: {
            /* Quadratic: depth^2 * 0.80 */
            uint16_t squared = (uint16_t)depth_q8 * depth_q8 / 256u;
            return fp_clamp_q8(squared * 204u / 255u);
        }
        case 2u: {
            /* Linear: depth * 0.88 */
            return fp_mul_q8(depth_q8, 224u);
        }
        default:
            return 0u;
    }
}

uint8_t pxgbprog_depth_compute_adaptive_layer_count(
    uint8_t weapon_rank,
    uint8_t armor_rank,
    uint8_t pressure,
    uint8_t phase,
    uint8_t boss_active) {
    /**
     * Map game context to layer count (4-16 GameBoy-optimized range).
     * - weapon_rank weights toward visible detail
     * - pressure (boss danger) reduces layers for perf
     * - boss_active may force minimal layers
     */
    uint8_t base_layers = 8u + (weapon_rank / 4u);  /* 8-10 base */
    uint8_t pressure_factor = pressure > 128u ? 2u : 1u;
    uint8_t adjusted = base_layers / pressure_factor;
    
    /* Clamp to GB-safe range */
    if (adjusted > PXGBPROG_DEPTH_MAX_LAYERS) adjusted = PXGBPROG_DEPTH_MAX_LAYERS;
    if (adjusted < 4u) adjusted = 4u;
    
    return adjusted;
}

uint8_t pxgbprog_depth_compute_blur_kernel_size(uint8_t depth_ratio_q8) {
    /**
     * Blur kernel scaling: 0 (no blur) at surface, 2 (3x3 kernel) at depth.
     */
    if (depth_ratio_q8 < 85u) return 0u;   /* 0-33% depth: no blur */
    if (depth_ratio_q8 < 170u) return 1u;  /* 33-66% depth: 1x blur */
    return 2u;                              /* 66%+ depth: 2x blur */
}

uint8_t pxgbprog_depth_compute_erosion_rate_q8(uint8_t depth_ratio_q8, uint8_t phase) {
    /**
     * Erosion rate: 0.05 + depth_ratio * 0.35 (in Q8)
     * Phase modulates responsiveness.
     * Result: 0.05 (13/256) at surface, 0.40 (102/256) at depth
     */
    uint8_t phase_weight = (phase * 13u) >> 4u;
    uint8_t base_erosion = 13u;  /* 0.05 * 255 */
    uint8_t depth_erosion = fp_mul_q8(depth_ratio_q8, 89u);  /* 0.35 * 255 */
    
    return fp_clamp_q8((uint16_t)base_erosion + depth_erosion + phase_weight);
}

uint8_t pxgbprog_depth_build_layer_schedule(
    PxGbProgLayerSchedule *out_schedule,
    const PxGbProgAnimationPose *pose,
    const PxGbProgCompileOptions *options) {
    /**
     * Build all layer configs for this frame.
     * Respects game context from compile options.
     */
    if (!out_schedule || !pose || !options) return 0u;
    
    uint8_t layer_count = pxgbprog_depth_compute_adaptive_layer_count(
        options->weapon_rank,
        options->armor_rank,
        options->pressure,
        options->phase,
        options->boss_active
    );
    
    out_schedule->layer_count = layer_count;
    out_schedule->total_layers = layer_count;
    
    for (uint8_t i = 0u; i < layer_count; ++i) {
        PxGbProgLayerConfig *cfg = &out_schedule->configs[i];
        
        cfg->layer_index = i;
        cfg->depth_ratio_q8 = pxgbprog_depth_compute_ratio_q8(i, layer_count);
        cfg->silhouette_reduction_q8 = pxgbprog_depth_compute_silhouette_reduction_q8(i, layer_count, 0u);
        cfg->opacity_q8 = fp_clamp_q8(255u - cfg->silhouette_reduction_q8);
        cfg->blur_kernel_size = pxgbprog_depth_compute_blur_kernel_size(cfg->depth_ratio_q8);
        cfg->pixel_erosion_rate_q8 = pxgbprog_depth_compute_erosion_rate_q8(cfg->depth_ratio_q8, options->phase);
        
        /* Trail offsets increase with depth (2-6.5px range) */
        int16_t trail_y_base = 2u + ((uint16_t)cfg->depth_ratio_q8 * 9u / 255u);
        cfg->trail_offset_y = (int8_t)fp_clamp_q8(trail_y_base);
        cfg->trail_offset_x = (int8_t)((pose->arm_a_offset * cfg->depth_ratio_q8) >> 8u);
        
        /* Inverse animation strength: 0.15 at surface, 0.80 at depth */
        cfg->inverse_animation_strength_q8 = 38u + fp_mul_q8(cfg->depth_ratio_q8, 166u);
        
        /* Ragdoll influence: higher at depth layers */
        cfg->ragdoll_influence_q8 = fp_mul_q8(cfg->depth_ratio_q8, 200u);
    }
    
    return layer_count;
}

/* ============================================================================
   Ragdoll Physics Engine (Functions 12-35)
   ============================================================================ */

void pxgbprog_depth_create_skeleton(PxGbProgSkeleton *out_skeleton) {
    /**
     * Initialize 8-joint GameBoy skeleton.
     * Structure: root, pelvis, spine, chest, arm_l, arm_r, leg_l, leg_r
     */
    if (!out_skeleton) return;
    
    out_skeleton->joint_count = 8u;
    
    /* Root: center of mass */
    out_skeleton->joints[0].x = 0;
    out_skeleton->joints[0].y = 0;
    out_skeleton->joints[0].mass_q4 = 80u;  /* 5.0 */
    out_skeleton->joints[0].vx = 0;
    out_skeleton->joints[0].vy = 0;
    out_skeleton->joints[0].parent = 255u;
    
    /* Pelvis */
    out_skeleton->joints[1].x = 0;
    out_skeleton->joints[1].y = -2;
    out_skeleton->joints[1].mass_q4 = 40u;  /* 2.5 */
    out_skeleton->joints[1].vx = 0;
    out_skeleton->joints[1].vy = 0;
    out_skeleton->joints[1].parent = 0u;
    
    /* Spine */
    out_skeleton->joints[2].x = 0;
    out_skeleton->joints[2].y = -4;
    out_skeleton->joints[2].mass_q4 = 48u;  /* 3.0 */
    out_skeleton->joints[2].vx = 0;
    out_skeleton->joints[2].vy = 0;
    out_skeleton->joints[2].parent = 1u;
    
    /* Chest (head proxy) */
    out_skeleton->joints[3].x = 0;
    out_skeleton->joints[3].y = -6;
    out_skeleton->joints[3].mass_q4 = 32u;  /* 2.0 */
    out_skeleton->joints[3].vx = 0;
    out_skeleton->joints[3].vy = 0;
    out_skeleton->joints[3].parent = 2u;
    
    /* Left arm */
    out_skeleton->joints[4].x = -3;
    out_skeleton->joints[4].y = -4;
    out_skeleton->joints[4].mass_q4 = 24u;  /* 1.5 */
    out_skeleton->joints[4].vx = 0;
    out_skeleton->joints[4].vy = 0;
    out_skeleton->joints[4].parent = 2u;
    
    /* Right arm */
    out_skeleton->joints[5].x = 3;
    out_skeleton->joints[5].y = -4;
    out_skeleton->joints[5].mass_q4 = 24u;  /* 1.5 */
    out_skeleton->joints[5].vx = 0;
    out_skeleton->joints[5].vy = 0;
    out_skeleton->joints[5].parent = 2u;
    
    /* Left leg */
    out_skeleton->joints[6].x = -2;
    out_skeleton->joints[6].y = 2;
    out_skeleton->joints[6].mass_q4 = 48u;  /* 3.0 */
    out_skeleton->joints[6].vx = 0;
    out_skeleton->joints[6].vy = 0;
    out_skeleton->joints[6].parent = 1u;
    
    /* Right leg */
    out_skeleton->joints[7].x = 2;
    out_skeleton->joints[7].y = 2;
    out_skeleton->joints[7].mass_q4 = 48u;  /* 3.0 */
    out_skeleton->joints[7].vx = 0;
    out_skeleton->joints[7].vy = 0;
    out_skeleton->joints[7].parent = 1u;
}

uint8_t pxgbprog_depth_compute_joint_gravity_influence_q8(
    const PxGbProgJointState *joint,
    const PxGbProgJointState *parent,
    uint8_t gravity_q4) {
    /**
     * Gravity influence: min(1.0, distance / 20) scaled by mass.
     */
    if (!joint || !parent) return 0u;
    
    int16_t dx = (int16_t)joint->x - parent->x;
    int16_t dy = (int16_t)joint->y - parent->y;
    uint16_t dist = (uint16_t)(((dx * dx) + (dy * dy)) >> 1u);  /* Approx distance */
    
    /* Normalize by limb reach (~20px) */
    uint16_t influence = (dist < 20u) ? (dist * 255u / 20u) : 255u;
    
    return (uint8_t)influence;
}

void pxgbprog_depth_update_ragdoll_frame(
    PxGbProgSkeleton *skeleton,
    const PxGbProgAnimationPose *pose,
    const PxGbProgPhysicsConfig *physics) {
    /**
     * Physics step: gravity → damping → integration → constraints.
     */
    if (!skeleton || !pose || !physics) return;
    
    /* Step 1: Apply gravity to all joints */
    for (uint8_t i = 0u; i < skeleton->joint_count; ++i) {
        PxGbProgJointState *j = &skeleton->joints[i];
        j->vy += (int8_t)physics->gravity_q4;  /* Gravity accumulation */
    }
    
    /* Step 2: Apply damping */
    for (uint8_t i = 0u; i < skeleton->joint_count; ++i) {
        PxGbProgJointState *j = &skeleton->joints[i];
        j->vx = (int8_t)fp_mul_q8((uint8_t)j->vx, physics->damping_q8);
        j->vy = (int8_t)fp_mul_q8((uint8_t)j->vy, physics->damping_q8);
    }
    
    /* Step 3: Integrate position */
    for (uint8_t i = 0u; i < skeleton->joint_count; ++i) {
        PxGbProgJointState *j = &skeleton->joints[i];
        j->x += j->vx;
        j->y += j->vy;
    }
    
    /* Step 4: Apply animation offsets */
    if (skeleton->joint_count > 4u) {
        skeleton->joints[4].x += pose->arm_a_offset / 4;  /* Left arm */
    }
    if (skeleton->joint_count > 5u) {
        skeleton->joints[5].x += pose->arm_b_offset / 4;  /* Right arm */
    }
    if (skeleton->joint_count > 6u) {
        skeleton->joints[6].y += pose->leg_a_offset / 4;  /* Left leg */
    }
    if (skeleton->joint_count > 7u) {
        skeleton->joints[7].y += pose->leg_b_offset / 4;  /* Right leg */
    }
    
    /* Step 5: Solve constraints (3 iterations) */
    for (uint8_t iter = 0u; iter < physics->max_iterations; ++iter) {
        pxgbprog_depth_solve_constraints(skeleton, 1u, physics->stiffness_q8);
    }
}

void pxgbprog_depth_solve_constraints(
    PxGbProgSkeleton *skeleton,
    uint8_t iterations,
    uint8_t stiffness_q8) {
    /**
     * Distance constraint solver: maintain parent-child distances.
     * Three iterations stabilizes skeleton against animation jitter.
     */
    if (!skeleton) return;
    
    for (uint8_t iter = 0u; iter < iterations; ++iter) {
        for (uint8_t i = 1u; i < skeleton->joint_count; ++i) {
            PxGbProgJointState *joint = &skeleton->joints[i];
            if (joint->parent >= skeleton->joint_count) continue;
            
            PxGbProgJointState *parent = &skeleton->joints[joint->parent];
            
            /* Compute current distance */
            int16_t dx = (int16_t)joint->x - parent->x;
            int16_t dy = (int16_t)joint->y - parent->y;
            int16_t dist_sq = (dx * dx) + (dy * dy);
            
            /* Target distance (preset for each joint) */
            int16_t target_dist = 4;  /* Base limb length */
            int16_t target_dist_sq = target_dist * target_dist;
            
            if (dist_sq < 1) {
                dist_sq = 1;  /* Prevent division by zero */
            }
            
            /* Correct positions to restore constraint */
            int16_t delta = (target_dist_sq - dist_sq) / 2;
            int16_t correction = (delta * (int16_t)stiffness_q8) / 256;
            
            if (dx != 0 || dy != 0) {
                int16_t correction_x = (correction * dx) / target_dist;
                int16_t correction_y = (correction * dy) / target_dist;
                
                joint->x += (int8_t)(correction_x / 4);
                joint->y += (int8_t)(correction_y / 4);
                parent->x -= (int8_t)(correction_x / 8);
                parent->y -= (int8_t)(correction_y / 8);
            }
        }
    }
}

/* ============================================================================
   Silhouette Attenuation (Functions 22-35)
   ============================================================================ */

uint8_t pxgbprog_depth_compute_regional_scale_q8(
    const PxGbProgLayerConfig *layer_cfg,
    uint8_t region_index,
    const PxGbProgSkeleton *skeleton) {
    /**
     * Per-region scale influenced by ragdoll gravity.
     * Regions: 0=head, 1=body, 2=arms, 3=legs
     */
    if (!layer_cfg || !skeleton) return 255u;
    
    uint8_t base_reduction = layer_cfg->silhouette_reduction_q8;
    uint8_t gravity_influence = 0u;
    
    /* Compute average gravity influence for region */
    switch (region_index) {
        case 0u: { /* Head (joint 3) */
            if (skeleton->joint_count > 3u && skeleton->joint_count > 2u) {
                gravity_influence = pxgbprog_depth_compute_joint_gravity_influence_q8(
                    &skeleton->joints[3],
                    &skeleton->joints[2],
                    3u  /* gravity_q4 */
                );
            }
            break;
        }
        case 1u: { /* Body (joint 2) */
            if (skeleton->joint_count > 2u && skeleton->joint_count > 1u) {
                gravity_influence = pxgbprog_depth_compute_joint_gravity_influence_q8(
                    &skeleton->joints[2],
                    &skeleton->joints[1],
                    3u
                );
            }
            break;
        }
        case 2u: { /* Arms average (joints 4, 5) */
            uint16_t sum = 0u;
            uint8_t count = 0u;
            if (skeleton->joint_count > 4u && skeleton->joint_count > 2u) {
                sum += pxgbprog_depth_compute_joint_gravity_influence_q8(&skeleton->joints[4], &skeleton->joints[2], 3u);
                count++;
            }
            if (skeleton->joint_count > 5u && skeleton->joint_count > 2u) {
                sum += pxgbprog_depth_compute_joint_gravity_influence_q8(&skeleton->joints[5], &skeleton->joints[2], 3u);
                count++;
            }
            gravity_influence = count > 0u ? (uint8_t)(sum / count) : 0u;
            break;
        }
        case 3u: { /* Legs average (joints 6, 7) */
            uint16_t sum = 0u;
            uint8_t count = 0u;
            if (skeleton->joint_count > 6u && skeleton->joint_count > 1u) {
                sum += pxgbprog_depth_compute_joint_gravity_influence_q8(&skeleton->joints[6], &skeleton->joints[1], 3u);
                count++;
            }
            if (skeleton->joint_count > 7u && skeleton->joint_count > 1u) {
                sum += pxgbprog_depth_compute_joint_gravity_influence_q8(&skeleton->joints[7], &skeleton->joints[1], 3u);
                count++;
            }
            gravity_influence = count > 0u ? (uint8_t)(sum / count) : 0u;
            break;
        }
    }
    
    /* Weighted ragdoll influence factor */
    uint16_t gravity_weight = fp_mul_q8(layer_cfg->ragdoll_influence_q8, (uint8_t)(gravity_influence * 15u / 255u));
    
    /* Final scale: 1.0 - (base_reduction + weighted_gravity) */
    uint16_t total_reduction = (uint16_t)base_reduction + gravity_weight;
    if (total_reduction > 255u) total_reduction = 255u;
    
    return (uint8_t)(255u - total_reduction);
}

void pxgbprog_depth_apply_attenuation(
    uint8_t *tile_pixels,
    uint8_t pixel_count,
    const PxGbProgLayerConfig *layer_cfg,
    const PxGbProgSkeleton *skeleton) {
    /**
     * Apply silhouette reduction by scaling opacity.
     */
    if (!tile_pixels || !layer_cfg) return;
    
    uint8_t scale_q8 = pxgbprog_depth_compute_regional_scale_q8(layer_cfg, 1u, skeleton);
    
    for (uint8_t i = 0u; i < pixel_count; ++i) {
        uint8_t pixel = tile_pixels[i];
        uint8_t alpha = (pixel >> 6u) & 0x3u;  /* Extract alpha bits from 2-bit color */
        
        if (alpha > 0u) {
            alpha = fp_mul_q8(alpha, scale_q8) >> 6u;  /* Scale alpha */
            tile_pixels[i] = (pixel & 0x3Fu) | (alpha << 6u);  /* Repack */
        }
    }
}

/* ============================================================================
   Inverse Animation & Frame Interpolation (Functions 26-45)
   ============================================================================ */

int8_t pxgbprog_depth_invert_pose_offset(int8_t offset, uint8_t invert_strength_q8) {
    /**
     * Invert pose offset: -offset * invert_strength
     * Used for shadow layers that animate opposite direction.
     */
    int16_t inverted = -((int16_t)offset * (int16_t)invert_strength_q8) / 256;
    
    if (inverted > 127) return 127;
    if (inverted < -128) return -128;
    
    return (int8_t)inverted;
}

uint8_t pxgbprog_depth_compute_interpolation_weight_q8(uint8_t frame_index, uint8_t total_frames) {
    /**
     * Interpolation weight that phases in erosion over animation.
     * Smoothly advances from 0 to full erosion rate.
     */
    if (total_frames <= 1u) return 255u;
    return (uint16_t)frame_index * 255u / total_frames;
}

void pxgbprog_depth_apply_detail_erosion(
    uint8_t *tile_pixels,
    uint8_t erosion_rate_q8,
    uint8_t kernel_size) {
    /**
     * 3x3 morphological median filter erosion.
     * Removes isolated pixels and fine detail.
     */
    if (!tile_pixels || kernel_size == 0u) return;
    
    /* For GameBoy tiles (8x8, 64 pixels), apply simple erosion */
    for (uint8_t i = 0u; i < 64u; ++i) {
        uint8_t pixel = tile_pixels[i];
        uint8_t alpha = (pixel >> 6u) & 0x3u;
        
        if (alpha > 0u) {
            /* Apply erosion: remove some alpha */
            uint8_t eroded = fp_mul_q8(alpha, (255u - erosion_rate_q8));
            tile_pixels[i] = (pixel & 0x3Fu) | ((eroded >> 6u) << 6u);
        }
    }
}

void pxgbprog_depth_erode_pixel_alpha(
    uint8_t *tile_pixels,
    uint8_t pixel_count,
    uint8_t erosion_rate_q8) {
    /**
     * Direct alpha erosion: reduce each pixel's alpha by erosion rate.
     */
    if (!tile_pixels) return;
    
    for (uint8_t i = 0u; i < pixel_count; ++i) {
        uint8_t pixel = tile_pixels[i];
        uint8_t alpha = (pixel >> 6u) & 0x3u;
        
        if (alpha > 0u) {
            alpha = fp_mul_q8(alpha, (255u - erosion_rate_q8));
            tile_pixels[i] = (pixel & 0x3Fu) | ((alpha >> 6u) << 6u);
        }
    }
}

/* ============================================================================
   Pipeline Integration & Context Management
   ============================================================================ */

void pxgbprog_depth_context_init(
    PxGbProgDepthContext *ctx,
    PxGbProgDepthMode mode) {
    /**
     * Initialize depth context with default physics and skeleton.
     */
    if (!ctx) return;
    
    ctx->mode = mode;
    ctx->frame_buffer_valid = 0u;
    
    /* Default physics config */
    ctx->physics.gravity_q4 = 3u;          /* ~0.18 px/frame^2 */
    ctx->physics.damping_q8 = 235u;        /* ~0.92 damping */
    ctx->physics.stiffness_q8 = 191u;      /* ~0.75 stiffness */
    ctx->physics.max_iterations = 3u;
    
    /* Initialize skeleton */
    pxgbprog_depth_create_skeleton(&ctx->skeleton);
    
    /* Zero out animation pose */
    memset(&ctx->pose, 0, sizeof(PxGbProgAnimationPose));
}

void pxgbprog_depth_context_reset(PxGbProgDepthContext *ctx) {
    /**
     * Reset context for new frame.
     */
    if (!ctx) return;
    ctx->frame_buffer_valid = 0u;
}

void pxgbprog_depth_context_set_pose(
    PxGbProgDepthContext *ctx,
    const PxGbProgAnimationPose *pose) {
    /**
     * Update context with current animation pose.
     */
    if (!ctx || !pose) return;
    memcpy(&ctx->pose, pose, sizeof(PxGbProgAnimationPose));
}

void pxgbprog_depth_apply_to_tiles(
    uint8_t *tiles,
    uint8_t tile_count,
    PxGbProgDepthContext *ctx,
    const PxGbProgCompileOptions *options) {
    /**
     * Apply depth layer system to tile batch.
     * Main integration point: orchestrates all layer/physics/rendering operations.
     */
    if (!tiles || !ctx || !options) return;
    if (ctx->mode == PXGBPROG_DEPTH_MODE_NONE) return;
    
    /* Build layer schedule for this frame */
    PxGbProgLayerSchedule schedule;
    uint8_t layer_count = pxgbprog_depth_build_layer_schedule(&schedule, &ctx->pose, options);
    
    /* Update ragdoll physics if in active mode */
    if (ctx->mode >= PXGBPROG_DEPTH_MODE_RAGDOLL) {
        pxgbprog_depth_update_ragdoll_frame(&ctx->skeleton, &ctx->pose, &ctx->physics);
    }
    
    /* Apply depth processing to each tile */
    for (uint8_t tile_idx = 0u; tile_idx < tile_count && tile_idx < PXGBPROG_MAX_TILES; ++tile_idx) {
        uint8_t *tile = &tiles[tile_idx * PXGBPROG_TILE_BYTES];
        
        for (uint8_t layer_idx = 0u; layer_idx < layer_count; ++layer_idx) {
            const PxGbProgLayerConfig *cfg = &schedule.configs[layer_idx];
            
            /* Skip layer if too transparent */
            if (cfg->opacity_q8 < 13u) continue;  /* < 5% opacity */
            
            /* Apply layer transformations */
            pxgbprog_depth_apply_attenuation(tile, PXGBPROG_TILE_BYTES, cfg, &ctx->skeleton);
            pxgbprog_depth_apply_detail_erosion(tile, cfg->pixel_erosion_rate_q8, cfg->blur_kernel_size);
            pxgbprog_depth_erode_pixel_alpha(tile, PXGBPROG_TILE_BYTES, cfg->erosion_rate_q8);
        }
    }
    
    ctx->frame_buffer_valid = 1u;
}

/* ============================================================================
   Performance & Adaptivity
   ============================================================================ */

uint8_t pxgbprog_depth_estimate_cost_percent(
    uint8_t layer_count,
    uint8_t tile_count) {
    /**
     * Estimate memory cost as percentage of GB WRAM budget (~8KB usable).
     * Depth system uses ~layer_count * tile_count * 16 bytes.
     */
    uint16_t usage_bytes = (uint16_t)layer_count * tile_count * PXGBPROG_TILE_BYTES;
    uint8_t percent = (usage_bytes > 8192u) ? 100u : (uint8_t)((usage_bytes * 100u) / 8192u);
    
    return percent;
}

PxGbProgDepthMode pxgbprog_depth_select_quality_mode(
    uint8_t remaining_cycles,
    uint8_t weapon_rank,
    uint8_t boss_active) {
    /**
     * Select depth quality level based on performance headroom.
     * Conservative: boss_active reduces quality to preserve gameplay responsiveness.
     */
    if (boss_active) {
        return remaining_cycles > 50u ? PXGBPROG_DEPTH_MODE_SIMPLE : PXGBPROG_DEPTH_MODE_NONE;
    }
    
    if (remaining_cycles < 30u) {
        return PXGBPROG_DEPTH_MODE_NONE;
    } else if (remaining_cycles < 60u) {
        return PXGBPROG_DEPTH_MODE_SIMPLE;
    } else if (remaining_cycles < 100u) {
        return PXGBPROG_DEPTH_MODE_RAGDOLL;
    } else {
        return PXGBPROG_DEPTH_MODE_FULL;
    }
}

uint8_t pxgbprog_depth_cull_invisible_layers(
    PxGbProgLayerSchedule *schedule,
    uint8_t opacity_threshold_q8) {
    /**
     * Skip rendering layers below opacity threshold.
     * Saves computation by culling imperceptible layers.
     */
    if (!schedule) return 0u;
    
    uint8_t visible_count = 0u;
    for (uint8_t i = 0u; i < schedule->layer_count; ++i) {
        if (schedule->configs[i].opacity_q8 >= opacity_threshold_q8) {
            visible_count++;
        }
    }
    
    return visible_count;
}
