#include "../include/bango_engine_target.h"

#include <math.h>
#include <string.h>

static float bango_clampf(float value, float minimum, float maximum) {
    if (value < minimum) return minimum;
    if (value > maximum) return maximum;
    return value;
}

BangoEngineTargetConfig bango_engine_target_default_config(BangoPlatformKind platform) {
    BangoEngineTargetConfig config;
    memset(&config, 0, sizeof(config));
    config.platform = platform;
    config.require_new_3ds = (platform == BANGO_PLATFORM_N3DS);
    config.enable_stereo_depth = (platform == BANGO_PLATFORM_N3DS);
    config.enable_touch_controls = (platform == BANGO_PLATFORM_N3DS);
    config.enable_controller_support = 1;
    config.telemetry.local_only = 1;
    config.telemetry.allow_camera = 0;
    config.telemetry.allow_microphone = 0;
    config.telemetry.allow_environmental_inference = 0;
    return config;
}

void bango_engine_target_init(BangoEngineTargetState *state, const BangoEngineTargetConfig *config) {
    if (!state) return;
    memset(state, 0, sizeof(*state));
    state->config = config ? *config : bango_engine_target_default_config(BANGO_PLATFORM_WINDOWS);
}

void bango_engine_target_shutdown(BangoEngineTargetState *state) {
    if (!state) return;
    memset(state, 0, sizeof(*state));
}

void bango_engine_target_begin_frame(BangoEngineTargetState *state) {
    if (!state) return;
    state->frame.buttons_pressed = 0;
    state->frame.move_x = 0.0f;
    state->frame.move_y = 0.0f;
    state->frame.look_x = 0.0f;
    state->frame.look_y = 0.0f;
    state->frame.touch_active = 0;
    state->frame.touch_x = 0.0f;
    state->frame.touch_y = 0.0f;
    state->frame.haptic_pressure_left = 0.0f;
    state->frame.haptic_pressure_right = 0.0f;
}

void bango_engine_target_ingest_touch(BangoEngineTargetState *state, int active, float x, float y) {
    if (!state) return;
    state->frame.touch_active = active;
    state->frame.touch_x = x;
    state->frame.touch_y = y;
}

void bango_engine_target_ingest_analog(BangoEngineTargetState *state, float move_x, float move_y, float look_x, float look_y) {
    if (!state) return;
    state->frame.move_x = bango_clampf(move_x, -1.0f, 1.0f);
    state->frame.move_y = bango_clampf(move_y, -1.0f, 1.0f);
    state->frame.look_x = bango_clampf(look_x, -1.0f, 1.0f);
    state->frame.look_y = bango_clampf(look_y, -1.0f, 1.0f);
}

void bango_engine_target_ingest_buttons(BangoEngineTargetState *state, unsigned int buttons_held, unsigned int buttons_pressed) {
    if (!state) return;
    state->frame.buttons_held = buttons_held;
    state->frame.buttons_pressed = buttons_pressed;
}

void bango_engine_target_ingest_haptics(BangoEngineTargetState *state, float left_force, float right_force) {
    if (!state) return;
    state->frame.haptic_pressure_left = bango_clampf(left_force, 0.0f, 1.0f);
    state->frame.haptic_pressure_right = bango_clampf(right_force, 0.0f, 1.0f);
}

void bango_engine_target_ingest_stereo(BangoEngineTargetState *state, float slider_state) {
    if (!state) return;
    state->frame.stereo_depth_strength = bango_clampf(slider_state, 0.0f, 1.0f);
}

void bango_engine_target_ingest_telemetry(BangoEngineTargetState *state, const BangoTelemetrySample *sample) {
    if (!state || !sample) return;
    if (!state->config.telemetry.local_only) return;
    state->telemetry = *sample;
}

void bango_engine_target_update(BangoEngineTargetState *state, float dt) {
    float movement;
    float stick_pressure;
    if (!state) return;

    movement = sqrtf(state->frame.move_x * state->frame.move_x + state->frame.move_y * state->frame.move_y);
    stick_pressure = fabsf(state->frame.look_x) + fabsf(state->frame.look_y);

    state->combat_precision = bango_clampf(
        0.45f + stick_pressure * 0.20f + state->frame.haptic_pressure_right * 0.25f + state->telemetry.player_focus_proxy * 0.10f,
        0.0f,
        1.0f);
    state->combat_force = bango_clampf(
        0.30f + movement * 0.20f + state->frame.haptic_pressure_left * 0.25f + state->frame.haptic_pressure_right * 0.25f,
        0.0f,
        1.0f);
    state->movement_weight_relief = bango_clampf(
        (state->config.enable_touch_controls && state->frame.touch_active ? 0.25f : 0.0f) + state->frame.stereo_depth_strength * 0.15f,
        0.0f,
        1.0f);
    state->environmental_intensity = bango_clampf(
        state->telemetry.ambient_luma * 0.25f + state->telemetry.ambient_motion * 0.25f + state->telemetry.ambient_audio_level * 0.25f + state->telemetry.player_voice_energy * 0.25f,
        0.0f,
        1.0f);

    state->doengine.tension = 0.35f + movement * 0.20f + state->environmental_intensity * 0.15f;
    state->doengine.pressure = 0.40f + state->combat_force * 0.30f;
    state->doengine.temperature = 0.30f + state->environmental_intensity * 0.35f;
    state->doengine.mass = 0.50f + state->movement_weight_relief * 0.15f;
    state->doengine.velocity = movement * (1.0f + dt * 0.2f);
}
