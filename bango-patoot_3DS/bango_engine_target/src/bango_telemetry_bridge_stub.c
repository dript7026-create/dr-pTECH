#include "../include/bango_telemetry_bridge.h"

#include <string.h>

void bango_telemetry_bridge_init(BangoTelemetryBridge *bridge, BangoPlatformKind platform, BangoTelemetryConsent consent) {
    if (!bridge) return;
    memset(bridge, 0, sizeof(*bridge));
    bridge->platform = platform;
    bridge->consent = consent;
    bridge->initialized = 1;
}

void bango_telemetry_bridge_shutdown(BangoTelemetryBridge *bridge) {
    if (!bridge) return;
    memset(bridge, 0, sizeof(*bridge));
}

BangoTelemetrySample bango_telemetry_bridge_sample(const BangoTelemetryBridge *bridge, float fallback_luma, float fallback_audio) {
    BangoTelemetrySample sample;
    memset(&sample, 0, sizeof(sample));
    if (!bridge || !bridge->initialized || !bridge->consent.local_only) {
        return sample;
    }
    sample.ambient_luma = fallback_luma;
    sample.ambient_motion = 0.0f;
    sample.ambient_audio_level = fallback_audio;
    sample.player_voice_energy = 0.0f;
    sample.player_breath_proxy = 0.0f;
    sample.player_focus_proxy = fallback_luma * 0.25f;
    return sample;
}
