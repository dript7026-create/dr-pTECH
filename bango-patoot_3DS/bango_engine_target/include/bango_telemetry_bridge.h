#ifndef BANGO_TELEMETRY_BRIDGE_H
#define BANGO_TELEMETRY_BRIDGE_H

#include "bango_engine_target.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct BangoTelemetryBridge {
    BangoPlatformKind platform;
    BangoTelemetryConsent consent;
    int initialized;
} BangoTelemetryBridge;

void bango_telemetry_bridge_init(BangoTelemetryBridge *bridge, BangoPlatformKind platform, BangoTelemetryConsent consent);
void bango_telemetry_bridge_shutdown(BangoTelemetryBridge *bridge);
BangoTelemetrySample bango_telemetry_bridge_sample(const BangoTelemetryBridge *bridge, float fallback_luma, float fallback_audio);

#ifdef __cplusplus
}
#endif

#endif
