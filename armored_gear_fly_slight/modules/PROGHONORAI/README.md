# PROGHONORAI

`PROGHONORAI` is the combat-routing module that shapes how passage channels feed into game logic. It is intentionally standalone so any Game Boy or non-Game Boy gameplay layer can query it without depending on Armored Gear: Fly Slight internals.

## Layout

- `include/proghonorai.h`: public AI routing API.
- `src/proghonorai.c`: session telemetry, routing directives, and passage-level steering.
- `submodules/HONORSPHERE/`: per-passage honor router used inside every channel decision.

## Passage Model

`PROGHONORAI` exposes five passage channels: spawn, approach, windup, lunge, and render. Each channel runs through `HONORSPHERE`, which scores respect, tension, and pressure before handing back a directive that the game layer can translate into tier shifts, timing shifts, speed shifts, and visual pressure.