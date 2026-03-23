# ORBEngine Architecture Draft

Version: 0.1  
Date: 2026-03-10

## Purpose

This document prepares ORBEngine for implementation as a standalone engine that renders a 2D world as a recursive pseudo-3D space while preserving deterministic logic, exact collision, and asset-authored gameplay boundaries.

## Design Goals

1. Render 2D assets as if they occupy 3D-feeling space.
2. Support recursive world spaces that visually remagnify and fold back into parent spaces.
3. Keep gameplay logic deterministic and simulation-coherent across recursion layers.
4. Drive collision and hit detection from non-alpha pixel boundaries and authored boundary markup.
5. Preserve asset richness from source formats rather than flattening them too early.

## Engine Subsystems

### Named InnsmouthIsland Integration Profiles

The current InnsmouthIsland planning pass names three cross-cutting profiles that should sit on top of the existing subsystem layout rather than replace it:

- ORBdimensionView: pseudo-3D projection, depth-band presentation, layered fog, horizon lift, sprite shear, and grounded shadow policy.
- ORBKinetics: exact authored collision, interaction radii, per-frame hitbox support, aerial occupancy, and surface-tag-aware response.
- ORBGlue: binding between discovery, codex, shrine progression, audio state, animation state, equipment state, and combat warnings.

These names are now represented in the core sandbox configuration so future InnsmouthIsland migration work can bind authored assets and gameplay metadata into the engine without introducing a second parallel vocabulary.

### Anchor And Precision Pipeline Ownership

The invisible anchor-node and hit-detection pipeline is assigned explicitly across the three InnsmouthIsland profiles rather than left as a loose art-side convention:

- ORBdimensionView owns dimensional anchor interpretation, top-cap projection, foreground occlusion, curvature-consistent depth translation, and the pseudo-3D stitching rules that turn authored 2D planes into coherent cubic-feeling space.
- ORBKinetics owns invisible collision silhouettes, exact-mask intent, collision skin widths, anchor-linked hit-detection interpretation, and the runtime approximation path from pixel-authored silhouettes to deterministic gameplay boundaries.
- ORBGlue owns the binding between those authored anchor/silhouette assets and gameplay state, including animation-to-collision coherence, equipment socket attachment, codex/shrine/discovery bindings, and any telemetry needed to keep precision data synchronized with interactions.

This split matters because the runtime should be able to explain whether a failure came from dimensional translation, collision interpretation, or gameplay-state binding instead of treating the whole asset-precision stack as one opaque subsystem.

### 1. Space Graph

The world is modeled as a graph of spaces.

Each space node contains:
- local coordinate frame,
- parent-space linkage,
- scale transform,
- warp-rotation rules,
- render layers,
- collision domains,
- simulation entities,
- and optional child pockets.

The graph must support:
- parent-to-child descent,
- child-to-parent remagnification,
- deterministic traversal order,
- and recursion limits for debugging and safety.

### 2. Render Pipeline

The renderer should be staged as:

1. Collect visible spaces.
2. Resolve recursive projection chains.
3. Build layer stack for each visible space.
4. Apply Mode-7-inspired floor transforms where required.
5. Apply parallax and simulated rotational warp.
6. Composite back into screen space.

The engine should not pretend objects are truly 3D meshes. Instead, it should use transform and projection rules that make 2D assets feel rotationally dimensional.

### 3. Asset Pipeline

Supported source targets:
- `.swf`
- `.piskel`
- `.clip`

Import should preserve, where feasible:
- layers,
- frame/timeline data,
- pivot information,
- vector/shape grouping metadata,
- palette/paint semantics,
- animation ranges,
- and authored top-layer markers.

The runtime should generate intermediate ORB asset packages rather than consuming authoring formats raw during gameplay.

### 4. Collision Pipeline

Collision is based on:
- visible non-alpha pixels,
- explicit boundary-extraction metadata,
- and the user-authored bright-green top-layer outline.

Planned rule:
- the bright-green top-layer outline becomes the authoritative continuous gameplay boundary for the object.
- pixels outside that boundary remain irrelevant to logic.
- fully transparent space is culled from rendering and logic.

Recommended runtime representation:
- source mask,
- extracted outline spline or polygon chain,
- simplified collision hull,
- optional per-frame fine mask for exact checks,
- and per-recursion transformed collision proxies.

### 5. Physics and Combat Coherence

The target is recursion-aware collision and combat consistency.

Required traits:
- deterministic step order,
- stable transforms across parent/child spaces,
- authoritative world-space resolution for collisions,
- late-stage visual transform after logical resolution,
- frame-coherent hurtbox and hitbox mapping,
- and repeatable replay/debug behavior.

No honest engine spec can guarantee literal perfection. The correct requirement is deterministic, explainable, low-latency, player-consistent outcomes.

### 6. Simulation Layers

Suggested layers:
- render layer,
- gameplay layer,
- collision layer,
- physics layer,
- recursion transform layer,
- and debug overlay layer.

These should stay separable to simplify debugging and preserve correctness.

## Runtime Data Model

### SpaceNode

Contains:
- identity,
- parent id,
- children ids,
- transform state,
- scale ratio,
- warp parameters,
- render stack,
- collision domain,
- entity list.

### RenderEntity

Contains:
- asset reference,
- animation state,
- local transform,
- render depth policy,
- recursion visibility flags,
- mask reference,
- gameplay tags.

### CollisionShape

Contains:
- source mask,
- extracted outline,
- simplified hull,
- recursion-transformed proxy,
- frame revision.

## Development Sequence

1. Build a non-recursive sandbox with 2D layers and warp transforms.
2. Add the space graph with parent-child nesting.
3. Add recursive visibility traversal.
4. Add asset intermediate format and importers.
5. Add green-outline collision extraction.
6. Add deterministic collision and physics test scenes.
7. Recreate OrbSeeker island hub.
8. Add recursive orb chamber prototype.

## OrbSeeker First Vertical Slice

The first ORBEngine milestone should render:
- island ground plane,
- palm/tree layers,
- raft object,
- a shore gate that transitions the player into the combat simulator,
- player object,
- beneath-island agriculture complex access,
- combat simulator selection room,
- tactical simulator scene,
- QTE simulator scene,
- open procedural combat scene,
- one nested recursive pocket test volume,
- and mask-driven movement/collision.

That will validate the engine’s core promise before full game migration.

## Sandbox-Specific Structural Requirement

For OrbSeeker development, the engine sandbox must support an island-top and below-island split in the same authored environment. The sandbox should therefore validate:
- surface-to-below-island traversal,
- surface-to-simulator traversal by raft,
- recursion-aware rendering continuity between these authored spaces,
- and future promotion of the simulator into the final-game tutorial/training complex.
