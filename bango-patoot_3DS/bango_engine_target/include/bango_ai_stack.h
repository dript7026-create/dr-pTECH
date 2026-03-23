#ifndef BANGO_AI_STACK_H
#define BANGO_AI_STACK_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct BangoAICameraAdvisory {
    float shoulder_side;
    float shoulder_up;
    float shoulder_back;
    float focus_side;
    float focus_up;
    float focus_forward;
    float focal_length;
    float panorama_warp;
    float pseudo3d_bias;
    float landmass_depth;
} BangoAICameraAdvisory;

typedef struct BangoAISimulationAdvisory {
    float animation_stiffness;
    float animation_damping;
    float ground_stickiness;
    float collision_bias;
    float chemistry_flux;
    float biology_drive;
    float quantum_sidehook;
    float favorable_probability;
} BangoAISimulationAdvisory;

typedef struct BangoAIRenderAdvisory {
    float terrain_morph_strength;
    float occlusion_feather;
    float motion_blur_pixels;
    float edge_stitch;
    float horizon_bias;
    float skybox_nonmorph_depth;
    float gameplay_aspect_ratio;
} BangoAIRenderAdvisory;

typedef struct BangoAIStackState {
    float movement_signal;
    float look_signal;
    float button_pressure;
    float terrain_relief;
    float horizon_separation;
    float sky_depth;
    float occlusion_pressure;
    float arithmetic_confidence;
    float algebra_confidence;
    float physics_confidence;
    float chemistry_confidence;
    float biology_confidence;
    float rendering_confidence;
    float semantics_confidence;
    float quantum_confidence;
    float predictive_reasoning;
    float favorable_probability;
} BangoAIStackState;

void bango_ai_stack_init(BangoAIStackState *state);
void bango_ai_stack_begin_frame(BangoAIStackState *state);
void bango_ai_stack_ingest_input_signal(BangoAIStackState *state, float movement_signal, float look_signal, unsigned int buttons_held, unsigned int buttons_pressed);
void bango_ai_stack_ingest_environment(BangoAIStackState *state, float terrain_relief, float horizon_separation, float sky_depth, float occlusion_pressure);
void bango_ai_stack_resolve_semantics(BangoAIStackState *state, const char *verb, const char *noun, float expectation_weight, float influence_weight);
void bango_ai_stack_generate_camera(const BangoAIStackState *state, BangoAICameraAdvisory *out_camera);
void bango_ai_stack_generate_simulation(const BangoAIStackState *state, BangoAISimulationAdvisory *out_simulation);
void bango_ai_stack_generate_render(const BangoAIStackState *state, BangoAIRenderAdvisory *out_render);

#ifdef __cplusplus
}
#endif

#endif