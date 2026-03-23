# ORBEngine Full Development Completion TODOs

Version: 0.1  
Date: 2026-03-10

## Engine Foundation

- Finalize language/runtime target.
- Establish build system and binary layout.
- Define coding standards including declaration-before-use across C implementation files.
- Add math, memory, logging, and debug utilities.
- Add deterministic frame-step scheduler.

## Recursive Space Runtime

- Implement `SpaceNode` graph traversal.
- Add recursive render pass ordering.
- Add parent-child transform propagation.
- Add pocket-space remagnification rules.
- Add debugging overlays for recursion chains and depth limits.

## OrbSeeker Sandbox Completion

- Finish island surface sandbox.
- Keep the raft-to-simulator shore gate as permanent sandbox feature.
- Build the simulator-tutorial-training room beneath the island as a final-game carry-forward space.
- Build the beneath-island agriculture complex into the sandbox for live farm-system validation.

## Combat Simulator Completion

### Tactical

- Turn order.
- unit stats.
- actions, defense, buffs, and debuffs.
- deterministic combat logs.
- AI decision testing.

### QTE

- OrbGuardian timing chains.
- telegraph timing windows.
- hit/miss grading.
- audiovisual response hooks.
- difficulty tuning.

### Open

- free movement in pseudo-3D recursive space.
- small procedural encounter generation.
- standard enemy behavior sets.
- real-time hit logic and knockback.
- collision and combat debug overlays.

## Agriculture Completion

- crop bed definitions.
- growth stages.
- irrigation / hydro loops.
- survival-resource integration.
- harvest rules.
- debug telemetry and balancing tools.

## Asset Pipeline

- import contracts for `.swf`, `.piskel`, `.clip`.
- intermediate ORB asset package format.
- pivot, layer, and animation preservation.
- top-layer green-boundary extraction.
- collision mask preview tooling.

## Physics and Collision

- polygon extraction from green-outline authored boundaries.
- exact pixel confirmation tests.
- recursion-aware collision proxies.
- deterministic hit resolution.
- combat feel/performance instrumentation.

## OrbSeeker Migration

- recreate island hub.
- recreate agriculture complex.
- recreate simulator-tutorial-training room.
- recreate expedition map traversal.
- recreate orb chambers and guardian encounters.
- add save/load and controller input.

## Tooling

- scene authoring format.
- asset validation.
- collision visualization.
- replay/debug capture.
- performance tracing.
