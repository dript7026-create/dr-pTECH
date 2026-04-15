#include "passage_modules.h"

#include "../modules/PxGBPROG/include/pxgbprog.h"
#include "../modules/PxGBPROG/include/pxgbprog_depth_layers.h"
#include "../modules/PROGHONORAI/include/proghonorai.h"

#define PASSAGE_MODULE_TILE_CAPACITY 8u

static ProgHonorAiContext g_proghonorai;
static PxGbProgPipeline g_pxgbprog_pipeline;
static PxGbProgDepthContext g_depth_context;
static unsigned char g_runtime_sprite_tiles[PASSAGE_MODULE_TILE_CAPACITY * PXGBPROG_TILE_BYTES];
static uint8_t g_visual_dirty = 1u;
static uint8_t g_last_weapon_rank = 0xFFu;
static uint8_t g_last_armor_rank = 0xFFu;
static uint8_t g_last_phase = 0xFFu;
static uint8_t g_last_boss_active = 0xFFu;
static uint8_t g_frame_counter = 0u;

static uint8_t passage_modules_apply_delta(uint8_t base_value, int8_t delta, uint8_t minimum, uint8_t maximum) {
    int16_t value;
    value = (int16_t)base_value + delta;
    if (value < minimum) value = minimum;
    if (value > maximum) value = maximum;
    return (uint8_t)value;
}

void passage_modules_begin_session(uint16_t world_seed, uint8_t level, uint8_t weapon_rank, uint8_t armor_rank) {
    proghonorai_init(&g_proghonorai, world_seed, level, weapon_rank, armor_rank);
    pxgbprog_depth_context_init(&g_depth_context, PXGBPROG_DEPTH_MODE_RAGDOLL);
    g_visual_dirty = 1u;
    g_last_weapon_rank = 0xFFu;
    g_last_armor_rank = 0xFFu;
    g_last_phase = 0xFFu;
    g_last_boss_active = 0xFFu;
    g_frame_counter = 0u;
}

void passage_modules_record_move(uint8_t moved, uint8_t tile_kind) {
    proghonorai_record_movement(&g_proghonorai, moved, tile_kind);
    if (moved) g_visual_dirty = 1u;
}

void passage_modules_record_rake(uint8_t connected) {
    proghonorai_record_rake(&g_proghonorai, connected);
    g_visual_dirty = 1u;
}

void passage_modules_record_use(uint8_t restorative) {
    proghonorai_record_use(&g_proghonorai, restorative);
    if (restorative) g_visual_dirty = 1u;
}

void passage_modules_update(uint8_t phase, uint8_t boss_active, uint8_t health, uint8_t max_health) {
    proghonorai_update(&g_proghonorai, phase, boss_active, health, max_health);
    g_visual_dirty = 1u;
}

uint8_t passage_modules_adjust_spawn_tier(uint8_t base_tier, uint8_t border, uint8_t coherence_state) {
    ProgHonorAiDirective directive;
    uint8_t threat;
    threat = (uint8_t)(border + coherence_state * 36u);
    proghonorai_route(&g_proghonorai, PROGHONORAI_PASSAGE_SPAWN, threat, base_tier, &directive);
    return passage_modules_apply_delta(base_tier, directive.tier_delta, 0u, 2u);
}

uint8_t passage_modules_adjust_windup(uint8_t enemy_type, uint8_t tier, uint8_t base_frames) {
    ProgHonorAiDirective directive;
    uint8_t threat;
    threat = (uint8_t)(72u + enemy_type * 40u + tier * 18u);
    proghonorai_route(&g_proghonorai, PROGHONORAI_PASSAGE_WINDUP, threat, tier, &directive);
    return passage_modules_apply_delta(base_frames, directive.windup_delta, 6u, 48u);
}

uint8_t passage_modules_adjust_lunge_frames(uint8_t enemy_type, uint8_t tier, uint8_t base_frames) {
    ProgHonorAiDirective directive;
    uint8_t threat;
    threat = (uint8_t)(96u + enemy_type * 42u + tier * 20u);
    proghonorai_route(&g_proghonorai, PROGHONORAI_PASSAGE_LUNGE, threat, tier, &directive);
    return passage_modules_apply_delta(base_frames, directive.lunge_frames_delta, 8u, 36u);
}

uint8_t passage_modules_adjust_stun(uint8_t enemy_type, uint8_t tier, uint8_t base_frames) {
    ProgHonorAiDirective directive;
    uint8_t threat;
    threat = (uint8_t)(60u + enemy_type * 28u + tier * 16u);
    proghonorai_route(&g_proghonorai, PROGHONORAI_PASSAGE_APPROACH, threat, tier, &directive);
    return passage_modules_apply_delta(base_frames, directive.stun_delta, 8u, 48u);
}

uint8_t passage_modules_adjust_lunge_speed(uint8_t enemy_type, uint8_t tier, uint8_t base_speed) {
    ProgHonorAiDirective directive;
    uint8_t threat;
    threat = (uint8_t)(88u + enemy_type * 36u + tier * 22u);
    proghonorai_route(&g_proghonorai, PROGHONORAI_PASSAGE_LUNGE, threat, tier, &directive);
    return passage_modules_apply_delta(base_speed, directive.speed_delta, 1u, 4u);
}

uint8_t passage_modules_sync_visuals(const unsigned char *base_tiles, uint8_t tile_count, uint8_t weapon_rank, uint8_t armor_rank, uint8_t phase, uint8_t boss_active) {
    ProgHonorAiDirective directive;
    PxGbProgCompileOptions options;
    PxGbProgAnimationPose pose;

    if (!base_tiles) return 0u;
    if (tile_count > PASSAGE_MODULE_TILE_CAPACITY) tile_count = PASSAGE_MODULE_TILE_CAPACITY;

    if (!g_visual_dirty && g_last_weapon_rank == weapon_rank && g_last_armor_rank == armor_rank && g_last_phase == phase && g_last_boss_active == boss_active) {
        return 0u;
    }

    proghonorai_route(&g_proghonorai, PROGHONORAI_PASSAGE_RENDER, (uint8_t)(phase * 24u + (boss_active ? 96u : 0u)), boss_active ? 2u : 1u, &directive);

    options.weapon_rank = weapon_rank;
    options.armor_rank = armor_rank;
    options.honor = g_proghonorai.honor;
    options.pressure = directive.visual_pressure;
    options.passage_bias = directive.passage_score;
    options.phase = phase;
    options.boss_active = boss_active;
    options.render_mode = directive.render_mode;

    pxgbprog_pipeline_begin(&g_pxgbprog_pipeline, base_tiles, tile_count);
    pxgbprog_pipeline_enqueue_manifest(&g_pxgbprog_pipeline, pxgbprog_manifest_player(), &options);
    pxgbprog_pipeline_enqueue_manifest(&g_pxgbprog_pipeline, pxgbprog_manifest_kin(), &options);
    pxgbprog_pipeline_enqueue_manifest(&g_pxgbprog_pipeline, pxgbprog_manifest_boss(), &options);
    pxgbprog_pipeline_simulate(&g_pxgbprog_pipeline, &options);
    pxgbprog_pipeline_render(&g_pxgbprog_pipeline, g_runtime_sprite_tiles);

    /* Apply context-adaptive depth layer system */
    pose.frame_index = g_frame_counter;
    pose.total_frames = 60u;
    pose.arm_a_offset = (int8_t)((directive.visual_pressure / 8u) - 8);
    pose.arm_b_offset = (int8_t)(8 - (directive.visual_pressure / 8u));
    pose.leg_a_offset = (int8_t)((phase * 2u) - 6);
    pose.leg_b_offset = (int8_t)(6 - (phase * 2u));
    pose.lift_offset = boss_active ? 2 : 0;
    
    pxgbprog_depth_context_set_pose(&g_depth_context, &pose);
    pxgbprog_depth_apply_to_tiles(g_runtime_sprite_tiles, tile_count, &g_depth_context, &options);
    
    g_frame_counter = (g_frame_counter + 1u) % 60u;

    g_last_weapon_rank = weapon_rank;
    g_last_armor_rank = armor_rank;
    g_last_phase = phase;
    g_last_boss_active = boss_active;
    g_visual_dirty = 0u;
    return 1u;
}

const unsigned char *passage_modules_sprite_tiles(void) {
    return g_runtime_sprite_tiles;
}