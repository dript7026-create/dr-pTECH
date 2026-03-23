GODHAX.aig — ArtificialIntelligenceGaming module (SAFE in-house scaffold)
======================================================================

Purpose
-------
This directory contains a safe scaffold for an adaptive, tick-level AI module
designed to be embedded inside games you own or develop. It provides:

- a per-session, ephemeral player-modeling / agent system driven by evolutionary
  search (genetic algorithms) that optimizes agent parameters during gameplay;
- hooks for integrating at the game-engine tick level (tick_update, on_spawn, etc.);
- an in-memory/ephemeral session datastore for aggregated, non-persistent
  profiles that expire when the session ends;
- placeholders to integrate runtime-generated graphical/audio assets for
  experiments (asset generation must be authorized and constrained to your own
  content pipelines);
- a minimal authorization layer so only approved developer/publisher admins
  can enable or export certain capabilities.

Limits and legal note
---------------------
This scaffold is explicitly NOT a hacking tool. It contains no code for
cracking, accessing, or modifying other games, servers, or hardware. Do not
use, adapt, or deploy this code for unauthorized access of third-party games
or services. The authors and maintainers will not assist in such activities.

Quick start
-----------
1. Add this package to your game project and call `hooks.tick_update(session_id, observation)` from your
   engine's tick/update loop.
2. Edit `auth.py` to configure authorized admin users for your studio.
3. Use the `evolution.py` utilities to run evolutionary searches in a
   sandboxed environment; evolution runs should be limited to in-memory
   simulations or dedicated test servers.

Developer integration guide
---------------------------
- Opt-in: Projects must explicitly enable GODHAX by setting the environment
  variable `GODHAX_ENABLED=1` in their build/runtime configuration. This
  ensures integrators consciously enable adaptive behavior.
- Engine hooks: call `hooks.tick_update(session_id, observation)` from your
  engine's tick/update loop. Map engine state to a serializable `observation`
  dict (for example, `{"features": [..], "entities": [...]}`) and map the
  returned action dict to engine commands.
- Asset pipelines: use `assets.generate_graphic_asset` and
  `assets.generate_audio_asset` and provide a `pipeline_callback` that
  integrates the generated temporary file into your engine's asset system.
- Admin-protected ops: functions that export or modify studio-level settings
  should be protected with `auth.require_admin`.

Packaging and distribution
-------------------------
This module is intentionally engine-agnostic. To distribute to third-party
developers or publishers:

1. Provide language bindings or examples for target engines (Unity/Unreal/Godot).
2. Supply an integration SDK (thin adapter layer) that maps engine events to
   `hooks.tick_update` and maps returned actions into engine-specific calls.
3. Include thorough security and legal docs stating that this package must
   only be used with games and assets you have rights to modify and that it
   must never be used to access or tamper with third-party games or systems.
