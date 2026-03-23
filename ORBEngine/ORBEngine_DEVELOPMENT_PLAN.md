# ORBEngine Development Plan

Version: 0.1  
Date: 2026-03-10

## Goal

Prepare ORBEngine as the standalone runtime for OrbSeeker.

## Milestone 1: Foundation

- Choose implementation language and platform targets.
- Establish repository structure.
- Define core math types and transform conventions.
- Define deterministic frame-step policy.
- Build a debug render window and scene loop.

## Milestone 2: Recursive Space Prototype

- Implement `SpaceNode` graph.
- Implement parent-child transform propagation.
- Add recursion traversal with debug overlays.
- Add configurable recursion depth limits.
- Render one world containing one pocket-space remagnification test.

## Milestone 3: Asset Ingestion

- Define ORB intermediate asset format.
- Build import adapters for `.swf`, `.piskel`, and `.clip` workflows.
- Preserve layer and animation metadata where available.
- Export runtime-ready texture, mask, pivot, and marker data.

## Milestone 4: Collision and Combat Core

- Implement green-outline boundary extraction.
- Generate continuous edge chains and simplified collision hulls.
- Add exact pixel-mask overlap tests for final confirmation.
- Ensure recursion-transformed collision remains stable across space levels.
- Add debug views for masks, hulls, and transformed hit regions.

## Milestone 5: OrbSeeker Vertical Slice

- Rebuild island hub.
- Add raft travel from island shore to simulator gate.
- Add beneath-island agriculture complex.
- Add simulator/tutorial/training room beneath the island.
- Add Tactical combat simulation.
- Add QTE combat simulation.
- Add Open combat simulation with procedural micro-environments.
- Add player traversal.
- Add farming interaction test.
- Add one expedition map.
- Add one orb site.
- Add one OrbGuardian encounter.

## Milestone 6: Production Tooling

- Asset validation tools.
- Collision preview tool.
- Space graph editor or declarative scene format.
- Replay/debug capture.
- Performance instrumentation.

## Open Technical Questions

1. Preferred implementation language for ORBEngine.
2. Whether `.swf`, `.piskel`, and `.clip` will be imported directly or via converter tools.
3. Chosen representation for extracted green-boundary outlines.
4. Fixed timestep and target framerate policy.
5. Save-data representation and content pipeline conventions.

## Immediate Next Build Tasks

1. Create the ORBEngine repository scaffold.
2. Define `SpaceNode`, `RenderEntity`, and `CollisionShape` data structures.
3. Build a recursive-space render sandbox.
4. Build the first green-outline collision extractor.
5. Recreate the OrbSeeker island hub as the first engine integration test.
6. Add the raft route into the combat simulator gate.
7. Add the agriculture complex beneath the island.
8. Add Tactical, QTE, and Open simulator environments.
