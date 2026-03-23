#ifndef BANGO_ENGINE_TARGET_H
#define BANGO_ENGINE_TARGET_H

#ifdef __cplusplus
extern "C" {
#endif

typedef enum BangoPlatformKind {
    BANGO_PLATFORM_WINDOWS = 0,
    BANGO_PLATFORM_N3DS = 1,
    BANGO_PLATFORM_IDTECH2 = 2
} BangoPlatformKind;

enum {
    BANGO_BTN_ATTACK_LIGHT = 1 << 0,
    BANGO_BTN_ATTACK_HEAVY = 1 << 1,
    BANGO_BTN_JUMP = 1 << 2,
    BANGO_BTN_CROUCH_SLIDE = 1 << 3,
    BANGO_BTN_HEAL = 1 << 4,
    BANGO_BTN_BLOCK = 1 << 5,
    BANGO_BTN_PARRY = 1 << 6,
    BANGO_BTN_FOCUS_LOCK = 1 << 7,
    BANGO_BTN_MENU = 1 << 8,
    BANGO_BTN_GAME_MENU = 1 << 9,
    BANGO_BTN_INTERACT_MASS = 1 << 10,
    BANGO_BTN_SPECIAL_WHEEL = 1 << 11,
    BANGO_BTN_SPRINT = 1 << 12
};

typedef struct BangoTelemetryConsent {
    int local_only;
    int allow_camera;
    int allow_microphone;
    int allow_environmental_inference;
} BangoTelemetryConsent;

typedef struct BangoTelemetrySample {
    float ambient_luma;
    float ambient_motion;
    float ambient_audio_level;
    float player_voice_energy;
    float player_breath_proxy;
    float player_focus_proxy;
} BangoTelemetrySample;

typedef struct BangoInputFrame {
    float move_x;
    float move_y;
    float look_x;
    float look_y;
    unsigned int buttons_held;
    unsigned int buttons_pressed;
    float haptic_pressure_left;
    float haptic_pressure_right;
    int touch_active;
    float touch_x;
    float touch_y;
    float stereo_depth_strength;
} BangoInputFrame;

typedef struct BangoDoEngineBridgeState {
    float tension;
    float pressure;
    float temperature;
    float mass;
    float velocity;
} BangoDoEngineBridgeState;

typedef struct BangoEngineTargetConfig {
    BangoPlatformKind platform;
    int require_new_3ds;
    int enable_stereo_depth;
    int enable_touch_controls;
    int enable_controller_support;
    BangoTelemetryConsent telemetry;
} BangoEngineTargetConfig;

typedef struct BangoEngineTargetState {
    BangoEngineTargetConfig config;
    BangoInputFrame frame;
    BangoTelemetrySample telemetry;
    BangoDoEngineBridgeState doengine;
    float combat_precision;
    float combat_force;
    float movement_weight_relief;
    float environmental_intensity;
} BangoEngineTargetState;

BangoEngineTargetConfig bango_engine_target_default_config(BangoPlatformKind platform);
void bango_engine_target_init(BangoEngineTargetState *state, const BangoEngineTargetConfig *config);
void bango_engine_target_shutdown(BangoEngineTargetState *state);
void bango_engine_target_begin_frame(BangoEngineTargetState *state);
void bango_engine_target_ingest_touch(BangoEngineTargetState *state, int active, float x, float y);
void bango_engine_target_ingest_analog(BangoEngineTargetState *state, float move_x, float move_y, float look_x, float look_y);
void bango_engine_target_ingest_buttons(BangoEngineTargetState *state, unsigned int buttons_held, unsigned int buttons_pressed);
void bango_engine_target_ingest_haptics(BangoEngineTargetState *state, float left_force, float right_force);
void bango_engine_target_ingest_stereo(BangoEngineTargetState *state, float slider_state);
void bango_engine_target_ingest_telemetry(BangoEngineTargetState *state, const BangoTelemetrySample *sample);
void bango_engine_target_update(BangoEngineTargetState *state, float dt);

#ifdef __cplusplus
}
#endif

#endif
