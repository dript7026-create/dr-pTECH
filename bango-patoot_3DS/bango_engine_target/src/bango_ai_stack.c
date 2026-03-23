#include "../include/bango_ai_stack.h"

#include <math.h>
#include <string.h>

static float bango_ai_clampf(float value, float minimum, float maximum) {
    if (value < minimum) return minimum;
    if (value > maximum) return maximum;
    return value;
}

static float bango_ai_strlen_score(const char *text) {
    size_t length = text ? strlen(text) : 0;
    return bango_ai_clampf((float)length / 12.0f, 0.0f, 1.0f);
}

static unsigned int bango_ai_popcount(unsigned int value) {
    unsigned int count = 0;
    while (value != 0u) {
        count += value & 1u;
        value >>= 1u;
    }
    return count;
}

void bango_ai_stack_init(BangoAIStackState *state) {
    if (!state) return;
    memset(state, 0, sizeof(*state));
    state->arithmetic_confidence = 0.55f;
    state->algebra_confidence = 0.55f;
    state->physics_confidence = 0.58f;
    state->chemistry_confidence = 0.50f;
    state->biology_confidence = 0.52f;
    state->rendering_confidence = 0.60f;
    state->semantics_confidence = 0.50f;
    state->quantum_confidence = 0.25f;
    state->predictive_reasoning = 0.50f;
    state->favorable_probability = 0.50f;
}

void bango_ai_stack_begin_frame(BangoAIStackState *state) {
    if (!state) return;
    state->movement_signal = 0.0f;
    state->look_signal = 0.0f;
    state->button_pressure = 0.0f;
    state->terrain_relief = 0.0f;
    state->horizon_separation = 0.0f;
    state->sky_depth = 0.0f;
    state->occlusion_pressure = 0.0f;
}

void bango_ai_stack_ingest_input_signal(BangoAIStackState *state, float movement_signal, float look_signal, unsigned int buttons_held, unsigned int buttons_pressed) {
    float hold_pressure;
    float press_pressure;
    if (!state) return;
    hold_pressure = bango_ai_clampf((float)bango_ai_popcount(buttons_held) / 8.0f, 0.0f, 1.0f);
    press_pressure = bango_ai_clampf((float)bango_ai_popcount(buttons_pressed) / 6.0f, 0.0f, 1.0f);
    state->movement_signal = bango_ai_clampf(movement_signal, 0.0f, 1.0f);
    state->look_signal = bango_ai_clampf(look_signal, 0.0f, 1.0f);
    state->button_pressure = bango_ai_clampf(hold_pressure * 0.65f + press_pressure * 0.35f, 0.0f, 1.0f);
}

void bango_ai_stack_ingest_environment(BangoAIStackState *state, float terrain_relief, float horizon_separation, float sky_depth, float occlusion_pressure) {
    if (!state) return;
    state->terrain_relief = bango_ai_clampf(terrain_relief, 0.0f, 1.0f);
    state->horizon_separation = bango_ai_clampf(horizon_separation, 0.0f, 1.0f);
    state->sky_depth = bango_ai_clampf(sky_depth, 0.0f, 1.0f);
    state->occlusion_pressure = bango_ai_clampf(occlusion_pressure, 0.0f, 1.0f);
}

void bango_ai_stack_resolve_semantics(BangoAIStackState *state, const char *verb, const char *noun, float expectation_weight, float influence_weight) {
    float meaning_weight;
    float expectation;
    float influence;
    if (!state) return;
    meaning_weight = bango_ai_strlen_score(verb) * 0.55f + bango_ai_strlen_score(noun) * 0.45f;
    expectation = bango_ai_clampf(expectation_weight, 0.0f, 1.0f);
    influence = bango_ai_clampf(influence_weight, 0.0f, 1.0f);
    state->semantics_confidence = bango_ai_clampf(0.35f + meaning_weight * 0.30f + expectation * 0.20f + influence * 0.15f, 0.0f, 1.0f);
    state->arithmetic_confidence = bango_ai_clampf(0.48f + state->movement_signal * 0.22f + state->button_pressure * 0.14f, 0.0f, 1.0f);
    state->algebra_confidence = bango_ai_clampf(0.46f + state->look_signal * 0.18f + state->semantics_confidence * 0.22f, 0.0f, 1.0f);
    state->physics_confidence = bango_ai_clampf(0.44f + state->terrain_relief * 0.28f + influence * 0.18f + state->movement_signal * 0.12f, 0.0f, 1.0f);
    state->chemistry_confidence = bango_ai_clampf(0.30f + state->occlusion_pressure * 0.24f + state->button_pressure * 0.16f + state->horizon_separation * 0.12f, 0.0f, 1.0f);
    state->biology_confidence = bango_ai_clampf(0.34f + expectation * 0.18f + state->movement_signal * 0.16f + state->terrain_relief * 0.12f, 0.0f, 1.0f);
    state->rendering_confidence = bango_ai_clampf(0.40f + state->look_signal * 0.24f + state->sky_depth * 0.18f + state->horizon_separation * 0.18f, 0.0f, 1.0f);
    state->quantum_confidence = bango_ai_clampf(0.12f + state->semantics_confidence * 0.18f + state->rendering_confidence * 0.16f, 0.0f, 0.72f);
    state->predictive_reasoning = bango_ai_clampf((state->arithmetic_confidence + state->algebra_confidence + state->physics_confidence + state->rendering_confidence + state->semantics_confidence) / 5.0f, 0.0f, 1.0f);
    state->favorable_probability = bango_ai_clampf(0.28f + state->predictive_reasoning * 0.32f + expectation * 0.18f + influence * 0.12f + state->biology_confidence * 0.10f, 0.0f, 1.0f);
}

void bango_ai_stack_generate_camera(const BangoAIStackState *state, BangoAICameraAdvisory *out_camera) {
    if (!state || !out_camera) return;
    out_camera->shoulder_side = 1.08f + state->rendering_confidence * 0.22f;
    out_camera->shoulder_up = 1.54f + state->biology_confidence * 0.18f;
    out_camera->shoulder_back = 2.36f - state->favorable_probability * 0.28f;
    out_camera->focus_side = -0.78f + state->semantics_confidence * 0.08f;
    out_camera->focus_up = 1.66f + state->biology_confidence * 0.16f;
    out_camera->focus_forward = 0.36f + state->predictive_reasoning * 0.24f;
    out_camera->focal_length = 0.60f + state->rendering_confidence * 0.12f + state->favorable_probability * 0.08f;
    out_camera->panorama_warp = 0.18f + state->rendering_confidence * 0.28f + state->algebra_confidence * 0.10f;
    out_camera->pseudo3d_bias = 0.10f + state->physics_confidence * 0.26f;
    out_camera->landmass_depth = 0.76f + state->sky_depth * 0.18f;
}

void bango_ai_stack_generate_simulation(const BangoAIStackState *state, BangoAISimulationAdvisory *out_simulation) {
    if (!state || !out_simulation) return;
    out_simulation->animation_stiffness = 14.5f + state->physics_confidence * 6.0f + state->predictive_reasoning * 3.0f;
    out_simulation->animation_damping = 7.2f + state->chemistry_confidence * 2.8f + state->biology_confidence * 1.8f;
    out_simulation->ground_stickiness = 0.54f + state->physics_confidence * 0.28f;
    out_simulation->collision_bias = 0.42f + state->terrain_relief * 0.28f + state->quantum_confidence * 0.08f;
    out_simulation->chemistry_flux = 0.30f + state->chemistry_confidence * 0.42f;
    out_simulation->biology_drive = 0.34f + state->biology_confidence * 0.38f;
    out_simulation->quantum_sidehook = state->quantum_confidence;
    out_simulation->favorable_probability = state->favorable_probability;
}

void bango_ai_stack_generate_render(const BangoAIStackState *state, BangoAIRenderAdvisory *out_render) {
    if (!state || !out_render) return;
    out_render->terrain_morph_strength = 0.20f + state->rendering_confidence * 0.34f + state->algebra_confidence * 0.12f;
    out_render->occlusion_feather = 0.24f + state->occlusion_pressure * 0.48f;
    out_render->motion_blur_pixels = 6.0f + state->look_signal * 18.0f + state->rendering_confidence * 6.0f;
    out_render->edge_stitch = 0.18f + state->rendering_confidence * 0.42f;
    out_render->horizon_bias = 0.26f + state->horizon_separation * 0.44f;
    out_render->skybox_nonmorph_depth = 0.72f + state->sky_depth * 0.24f;
    out_render->gameplay_aspect_ratio = 2.0f;
}