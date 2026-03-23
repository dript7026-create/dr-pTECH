#include "g_local.h"
#include "../generated/bango_asset_bootstrap.h"
#include "../../bango_engine_target/include/bango_engine_target.h"

static BangoEngineTargetState g_bango_engine;

static void Bango_InitEngineHooks(void) {
    BangoEngineTargetConfig config = bango_engine_target_default_config(BANGO_PLATFORM_IDTECH2);
    config.enable_touch_controls = 0;
    config.enable_stereo_depth = 0;
    config.telemetry.local_only = 1;
    bango_engine_target_init(&g_bango_engine, &config);
}

static void Bango_TickEngineHooks(float dt) {
    bango_engine_target_begin_frame(&g_bango_engine);
    bango_engine_target_update(&g_bango_engine, dt);
}

void Bango_InitGameModule(void) {
    Bango_InitEngineHooks();
    Bango_RegisterGeneratedAssets();
#ifdef BANGO_Q2_RUNTIME_LINKED
    gi.dprintf("Bango idTech2 module initialized.\n");
#endif
}

void Bango_ShutdownGameModule(void) {
    bango_engine_target_shutdown(&g_bango_engine);
}

void Bango_RunFrame(void) {
    Bango_TickEngineHooks(0.1f);
}

void SP_bango_playerstart(edict_t *self) {
    if (!self) return;
    self->classname = "info_player_start";
#ifdef BANGO_Q2_RUNTIME_LINKED
    gi.linkentity(self);
#endif
}

void SP_bango_training_prompt(edict_t *self) {
    if (!self) return;
    self->classname = "bango_training_prompt";
#ifdef BANGO_Q2_RUNTIME_LINKED
    gi.linkentity(self);
#endif
}
