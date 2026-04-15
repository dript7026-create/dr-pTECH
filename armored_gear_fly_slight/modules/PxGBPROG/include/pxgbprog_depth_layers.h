#ifndef PXGBPROG_DEPTH_LAYERS_H
#define PXGBPROG_DEPTH_LAYERS_H

#include <stdint.h>
#include "pxgbprog.h"

/**
 * PxGBPROG Depth Layer System
 * 
 * Context-adaptive depth rendering for GameBoy sprite tiles.
 * Implements progressive silhouette reduction, physics-based movement,
 * and real-time animation integration adapted for 8x8 tile constraints.
 * 
 * Key Features:
 * - Adaptive layer count based on weapon_rank and pressure
 * - Per-tile silhouette reduction via attenuation curves
 * - Ragdoll physics constraints with gravity simulation
 * - Frame interpolation for smooth motion trails
 * - Zero external dependencies (GameBoy memory-friendly)
 */

/* ============================================================================
   Layer Configuration and Physics State
   ============================================================================ */

#define PXGBPROG_DEPTH_MAX_LAYERS 16u  /* GameBoy-optimized layer count */
#define PXGBPROG_DEPTH_MAX_JOINTS 8u   /* Constrained skeleton for GB */
#define PXGBPROG_DEPTH_FRAME_BUFFER_SIZE 512u

typedef enum {
    PXGBPROG_DEPTH_MODE_NONE = 0u,
    PXGBPROG_DEPTH_MODE_SIMPLE = 1u,
    PXGBPROG_DEPTH_MODE_RAGDOLL = 2u,
    PXGBPROG_DEPTH_MODE_FULL = 3u
} PxGbProgDepthMode;

typedef struct {
    uint8_t layer_index;
    uint8_t depth_ratio_q8;  /* Fixed-point 0.0-1.0 as 0-255 */
    uint8_t silhouette_reduction_q8;
    uint8_t opacity_q8;
    uint8_t blur_kernel_size;
    uint8_t pixel_erosion_rate_q8;
    int8_t trail_offset_x;
    int8_t trail_offset_y;
    uint8_t inverse_animation_strength_q8;
    uint8_t ragdoll_influence_q8;
} PxGbProgLayerConfig;

typedef struct {
    int8_t x;
    int8_t y;
    uint8_t mass_q4;
    int8_t vx;
    int8_t vy;
    uint8_t parent;  /* Joint index of parent, 255 = root */
} PxGbProgJointState;

typedef struct {
    uint8_t gravity_q4;      /* Gravity acceleration in 1/16 px/frame^2 */
    uint8_t damping_q8;      /* Velocity damping multiplier 0.0-1.0 */
    uint8_t stiffness_q8;    /* Constraint restoration strength 0.0-1.0 */
    uint8_t max_iterations;  /* Constraint solver iterations */
} PxGbProgPhysicsConfig;

typedef struct {
    uint8_t layer_count;
    uint8_t total_layers;
    PxGbProgLayerConfig configs[PXGBPROG_DEPTH_MAX_LAYERS];
} PxGbProgLayerSchedule;

typedef struct {
    uint8_t joint_count;
    PxGbProgJointState joints[PXGBPROG_DEPTH_MAX_JOINTS];
} PxGbProgSkeleton;

typedef struct {
    uint8_t frame_index;
    uint8_t total_frames;
    int8_t arm_a_offset;
    int8_t arm_b_offset;
    int8_t leg_a_offset;
    int8_t leg_b_offset;
    int8_t lift_offset;
} PxGbProgAnimationPose;

typedef struct {
    PxGbProgDepthMode mode;
    PxGbProgPhysicsConfig physics;
    PxGbProgSkeleton skeleton;
    PxGbProgAnimationPose pose;
    uint8_t frame_buffer[PXGBPROG_DEPTH_FRAME_BUFFER_SIZE];
    uint8_t frame_buffer_valid;
} PxGbProgDepthContext;

/* ============================================================================
   Context-Adaptive Layer Generation (Context 1: Layer Config Functions 1-15)
   ============================================================================ */

/**
 * Compute normalized depth ratio (0.0 at surface, 1.0 at deepest layer).
 * Uses fixed-point Q8 format (0-255 represents 0.0-1.0).
 */
uint8_t pxgbprog_depth_compute_ratio_q8(uint8_t layer_index, uint8_t total_layers);

/**
 * Compute cubic attenuation curve for silhouette reduction.
 * At surface: 0, at depth: ~88% reduction (224/255 in Q8).
 * Formula: (depth_ratio^3) * 0.88
 */
uint8_t pxgbprog_depth_compute_silhouette_reduction_q8(uint8_t layer_index, uint8_t total_layers, uint8_t curve_mode);

/**
 * Apply damage/pressure to modulate layer count in real-time.
 * Higher pressure (boss active, low health) = more visible layers.
 */
uint8_t pxgbprog_depth_compute_adaptive_layer_count(
    uint8_t weapon_rank,
    uint8_t armor_rank,
    uint8_t pressure,
    uint8_t phase,
    uint8_t boss_active
);

/**
 * Compute blur kernel size (0-2) based on depth.
 * Deeper layers = more blur for motion blur effect.
 */
uint8_t pxgbprog_depth_compute_blur_kernel_size(uint8_t depth_ratio_q8);

/**
 * Compute pixel erosion rate (0.0-0.35 in Q8 format).
 * Erodes detail based on depth to sell motion trail effect.
 */
uint8_t pxgbprog_depth_compute_erosion_rate_q8(uint8_t depth_ratio_q8, uint8_t phase);

/**
 * Generate all layer configs for current frame.
 * Respects game context (weapon_rank, pressure, etc.).
 */
uint8_t pxgbprog_depth_build_layer_schedule(
    PxGbProgLayerSchedule *out_schedule,
    const PxGbProgAnimationPose *pose,
    const PxGbProgCompileOptions *options
);

/* ============================================================================
   Ragdoll Physics Engine (Context 2: Physics Functions 12-35)
   ============================================================================ */

/**
 * Initialize 8-joint GameBoy-optimized skeleton.
 * Structure: root, pelvis, spine, chest, 2×arm, 2×leg
 */
void pxgbprog_depth_create_skeleton(PxGbProgSkeleton *out_skeleton);

/**
 * Compute joint gravity influence (0.0-1.0) based on distance from parent.
 * Limbs further from root = more gravity influence.
 */
uint8_t pxgbprog_depth_compute_joint_gravity_influence_q8(
    const PxGbProgJointState *joint,
    const PxGbProgJointState *parent,
    uint8_t gravity_q4
);

/**
 * Apply gravity, damping, and integration to skeleton.
 * Three-iteration constraint solver for limb stiffness.
 */
void pxgbprog_depth_update_ragdoll_frame(
    PxGbProgSkeleton *skeleton,
    const PxGbProgAnimationPose *pose,
    const PxGbProgPhysicsConfig *physics
);

/**
 * Solve distance constraints between parent/child joints.
 * Stabilizes skeleton to prevent impossible poses.
 */
void pxgbprog_depth_solve_constraints(
    PxGbProgSkeleton *skeleton,
    uint8_t iterations,
    uint8_t stiffness_q8
);

/* ============================================================================
   Silhouette Attenuation (Context 3: Attenuation Functions 22-35)
   ============================================================================ */

/**
 * Compute per-region scale factor influenced by ragdoll gravity.
 * Regions: head, body, arms, legs.
 * Formula: 1.0 - (base_reduction + ragdoll_influence * avg_gravity * 0.15)
 */
uint8_t pxgbprog_depth_compute_regional_scale_q8(
    const PxGbProgLayerConfig *layer_cfg,
    uint8_t region_index,
    const PxGbProgSkeleton *skeleton
);

/**
 * Apply progressive attenuation to tile pixels.
 * Reduces opacity and sharpness based on layer depth.
 */
void pxgbprog_depth_apply_attenuation(
    uint8_t *tile_pixels,
    uint8_t pixel_count,
    const PxGbProgLayerConfig *layer_cfg,
    const PxGbProgSkeleton *skeleton
);

/* ============================================================================
   Inverse Animation & Frame Interpolation (Context 4: Functions 26-45)
   ============================================================================ */

/**
 * Invert pose offset (flip limb direction).
 * Formula: -offset * invert_strength
 */
int8_t pxgbprog_depth_invert_pose_offset(int8_t offset, uint8_t invert_strength_q8);

/**
 * Compute frame interpolation weight based on erosion phase.
 * Smoothly advances erosion rate across animation.
 */
uint8_t pxgbprog_depth_compute_interpolation_weight_q8(uint8_t frame_index, uint8_t total_frames);

/**
 * Apply morphological erosion to tile (remove isolated pixels).
 * 3×3 median filter to clean silhouettes.
 */
void pxgbprog_depth_apply_detail_erosion(
    uint8_t *tile_pixels,
    uint8_t erosion_rate_q8,
    uint8_t kernel_size
);

/**
 * Erode alpha channel of tile pixels.
 * Reduces alpha by erosion_rate.
 */
void pxgbprog_depth_erode_pixel_alpha(
    uint8_t *tile_pixels,
    uint8_t pixel_count,
    uint8_t erosion_rate_q8
);

/* ============================================================================
   Pipeline Integration & Context Management (Context 5)
   ============================================================================ */

/**
 * Initialize depth context with physics config and skeleton.
 */
void pxgbprog_depth_context_init(
    PxGbProgDepthContext *ctx,
    PxGbProgDepthMode mode
);

/**
 * Reset depth context for new frame.
 */
void pxgbprog_depth_context_reset(PxGbProgDepthContext *ctx);

/**
 * Update context with current animation pose.
 */
void pxgbprog_depth_context_set_pose(
    PxGbProgDepthContext *ctx,
    const PxGbProgAnimationPose *pose
);

/**
 * Apply depth layer system to tile batch in-place.
 * Modulates tiles based on depth context and layer config.
 */
void pxgbprog_depth_apply_to_tiles(
    uint8_t *tiles,
    uint8_t tile_count,
    PxGbProgDepthContext *ctx,
    const PxGbProgCompileOptions *options
);

/* ============================================================================
   Performance & Adaptivity (Advanced)
   ============================================================================ */

/**
 * Estimate memory cost of depth system for frame.
 * Returns percentage of GB WRAM budget (0-100).
 */
uint8_t pxgbprog_depth_estimate_cost_percent(
    uint8_t layer_count,
    uint8_t tile_count
);

/**
 * Compute quality level (0-3) based on available budget.
 * 0=disabled, 1=simple attenuation, 2=active ragdoll, 3=full system.
 */
PxGbProgDepthMode pxgbprog_depth_select_quality_mode(
    uint8_t remaining_cycles,
    uint8_t weapon_rank,
    uint8_t boss_active
);

/**
 * Fast layer culling pass: skip layers below opacity threshold.
 * Saves computation cost by not rendering invisible layers.
 */
uint8_t pxgbprog_depth_cull_invisible_layers(
    PxGbProgLayerSchedule *schedule,
    uint8_t opacity_threshold_q8
);

#endif /* PXGBPROG_DEPTH_LAYERS_H */
