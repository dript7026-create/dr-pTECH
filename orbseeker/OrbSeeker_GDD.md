# OrbSeeker Game Design Document

Version: 1.0  
Date: 2026-03-10

## Overview

OrbSeeker is an exploratory action-adventure built around island-hub progression, survival pressure, tournament gating, map traversal, orb recovery, and ritualized boss encounters. The current project exists as both a playable Pygame prototype and an idtech2 port skeleton. The next intended target is the standalone ORBEngine, which will become the long-term runtime for OrbSeeker.

This document consolidates:
- the latest repository state,
- the latest progress memory,
- the existing Pygame prototype loop,
- the existing idtech2 port skeleton,
- and the new ORBEngine-directed technical vision.

## Current Project State

### Progress Snapshot

- Latest progress note date: 2026-03-08.
- Current status: ready for immediate continuation.
- Existing artifacts:
  - `orbseeker.py`: playable Pygame prototype.
  - `requirements.txt`: Pygame dependency.
  - `idtech2_mod/`: Quake II mod skeleton with game stub, map placeholder, and build notes.
- Immediate previously recommended next step: choose between polishing the Pygame prototype or pushing the idtech2 compilation route.

### Implemented Prototype Features

The current Pygame build already expresses the core gameplay loop at a prototype level:

- Island hub.
- Survival stats: hunger, thirst, health.
- Farming loop with planting and harvesting.
- Mandatory winged-monkey rock-paper-scissors tournament to unlock travel.
- Map selection and map exploration.
- Seven orb nodes scattered across unlocked maps.
- OrbGuardian boss encounter implemented as a timed QTE sequence.
- Island return loop after success or failure.

### Existing idtech2 Work

The idtech2 material is not a finished port; it is a port skeleton. It includes:

- orb pickup hooks.
- orb guardian spawn stub.
- island initialization stub.
- placeholder entity setup.
- map and build notes for Quake II SDK integration.

This remains useful as reference for entity lifecycle thinking, but ORBEngine is now the long-term architectural direction.

## Vision

OrbSeeker should feel like a mythic expedition threaded through layered, recursive spaces. The player moves between lived-in hub spaces, ritual combat sites, traversal maps, and orb chambers that challenge perception, timing, and spatial reasoning. The world should feel hand-drawn and dreamlike, but systemically exact.

The eventual presentation target is a 2D-asset-driven pseudo-3D experience where depth, rotation, scale recursion, and collision coherence are simulated from authored 2D source material.

## Pillars

1. Exploration With Purpose  
The player is always searching for a next meaningful discovery: a map, a route, an orb site, a shortcut, a resource, or a ritual confrontation.

2. Survival With Momentum  
Survival systems create urgency without becoming passive busywork. Hunger and thirst should shape route planning, not stall the game.

3. Ritual Combat  
Orb encounters should feel like high-stakes tests of pattern-reading, timing, spatial awareness, and execution.

4. Recursive Spatial Wonder  
The world should present impossible-looking scale transitions while remaining mechanically legible.

5. Precision From Art  
Collision, targeting, and environment logic should be derived directly from asset-authored boundaries and masks.

## Narrative Frame

The current progress note describes the project as “Roju’s odyssey.” Roju’s journey begins from a hub island and expands outward into linked territories, tournament rituals, environmental challenges, and orb recoveries. The Rare Earth Orbs are both collectible objectives and world-structuring anchors. Guardians protect them through live-response combat or ritualized trial sequences.

The narrative tone should balance:
- mythic stakes,
- playful surrealism,
- intimate survival,
- and escalating cosmological weirdness.

## Core Loop

1. Recover at the island hub.
2. Manage survival state and supplies.
3. Farm or prepare for expedition.
4. Use the monkey companion and tournament path to unlock travel access.
5. Select or discover maps.
6. Explore traversal spaces for orb nodes and route knowledge.
7. Trigger OrbGuardian encounter.
8. Win orb challenge and return with progression unlocked.
9. Expand access to more spaces and systems.

## Systems

### Player State

- Health.
- Hunger.
- Thirst.
- Gold.
- Inventory.
- Maps unlocked.
- Orbs collected.

### Hub Systems

- Farming.
- Resource replenishment.
- Companion interactions.
- Route and map preparation.

### Tournament System

Currently represented by a best-of-three rock-paper-scissors gate. In final form, this can grow into a more characterful ritual/tournament system that mixes chance-reading, opponent tells, and wagered progression rewards.

### Expedition Maps

- Multiple maps with unique orb sites.
- Back-and-forth movement between island and field locations.
- Unlock-gated access.
- Potential for hazards, enemies, secrets, and recursive-space anomalies.

### Orb Encounters

Currently implemented as a timed QTE. Final design should expand toward:
- timing chains,
- movement-reactive phases,
- state shifts across recursive space layers,
- and attack/counterplay readable from visual transformation.

## World Structure

### Hub

The island is the narrative and logistical center:
- safety,
- farming,
- recovery,
- launching expeditions,
- tournament access,
- and narrative grounding.

The island sandbox should now explicitly include:
- a shore raft gate used to travel to a dedicated combat simulator space,
- an agriculture complex beneath the island for live farming-system validation,
- and a training/simulator-tutorial room that can transition directly into the final game as a permanent facility beneath the island.

### Beneath-Island Complex

The beneath-island complex should be split into at least two functional areas:
- Agriculture complex: crop beds, irrigation/hydro systems, survival-resource tuning, and sandbox telemetry.
- Combat simulator / tutorial-training room: controlled environments for combat-system validation before content is deployed into the wider world.

### Combat Simulator Modes

The combat simulator should provide three player-selectable modes:

1. Tactical  
Turn-based battle simulations used for validating simple combat rules, stat balance, turn order, defenses, and combat logs.

2. QTE  
Dedicated OrbGuardian battle-system testing focused on timing chains, telegraphs, inputs, and fail-state clarity.

3. Open  
Player-movement-enabled real-time combat within small procedurally generated spaces populated by standard enemies. This mode exists to test the fullest intended ORBEngine combat and space logic.

### Outer Spaces

Outer maps contain orb locations, traversal challenges, environmental storytelling, and the first serious use of ORBEngine’s layered pseudo-3D recursion presentation.

### Recursive Chambers

Orb sites and certain environmental spaces should visually imply that the world folds into itself. Large-scale spaces can contain re-magnified subspaces which resolve back into higher-order reality through render recursion and vector transforms.

## Visual Direction

OrbSeeker should use 2D-authored assets but present them as volumetric, rotating, layered, and space-reactive through ORBEngine.

Desired characteristics:
- hand-authored art sources,
- strong silhouette readability,
- clear mask-driven collision boundaries,
- parallax-rich landscapes,
- recursive scale transitions,
- dreamlike but mechanically exact presentation.

## Audio Direction

Audio should support:
- hub calm,
- expedition tension,
- orb-site ritual intensity,
- spatialized feedback for recursive transitions,
- and crisp response cues for live combat timing.

## Controls

### Current Prototype

- Movement.
- interaction key.
- travel/return keys.
- tournament input keys.
- boss QTE keys.

### Target

- keyboard and controller parity,
- clean action buffering,
- deterministic combat timing windows,
- immediate audiovisual hit confirmation.

## Technical Transition Plan

### Phase 1: Preserve Prototype Knowledge

Retain the Pygame prototype as a gameplay reference implementation for:
- loop pacing,
- inventory structure,
- orb encounter cadence,
- and menu-state flow.

### Phase 2: Build ORBEngine

Create a standalone engine focused on:
- recursive pseudo-3D rendering from 2D assets,
- exact mask-driven collision,
- deterministic simulation,
- and OrbSeeker-first tooling.

### Phase 3: Rebuild OrbSeeker on ORBEngine

Reimplement gameplay systems against ORBEngine runtime services rather than against Pygame or idtech2.

## ORBEngine Fit

OrbSeeker is the correct first game for ORBEngine because its core identity depends on:
- impossible-but-readable space,
- layered depth illusion,
- precision timing,
- authored 2D asset richness,
- and exact collision logic.

OrbSeeker should therefore serve as ORBEngine’s flagship proving project and reference game.

## ORBEngine Requirements for OrbSeeker

ORBEngine must provide:

- Mode-7-inspired ground and world warping.
- Parallax stacks and rotation-simulated depth.
- Recursive render-vector spaces.
- Hierarchical space nodes with parent-child scale relationships.
- Deterministic simulation across recursive layers.
- Pixel-precise collision and combat masks.
- Asset ingestion for `.swf`, `.piskel`, and `.clip` derived content.
- Non-alpha render culling and logic culling.
- Boundary extraction from bright-green marker outlines on the top art layer.
- Coherent hit logic across every recursion level.

## Collision and Combat Design Standard

The design target is extremely high responsiveness and coherence. That said, no honest engineering document can promise literal “100% realism” in every timing circumstance. The correct goal is:

- deterministic update order,
- frame-coherent mask tests,
- stable collision transforms through recursive spaces,
- low-latency control response,
- and consistent player-visible outcomes.

That standard should govern all future combat and physics work.

## Development Priorities

1. Finalize OrbSeeker high-level design and scope lock.
2. Establish ORBEngine architecture and asset pipeline.
3. Define recursive-space math model and transform rules.
4. Define collision-mask extraction and green-outline boundary standard.
5. Build a minimal ORBEngine sandbox scene.
6. Build the island shore raft gate to the combat simulator.
7. Build the beneath-island agriculture complex sandbox.
8. Build all three combat simulator modes: Tactical, QTE, and Open.
9. Port OrbSeeker hub traversal into ORBEngine.
10. Port orb encounter loop.
11. Add save/load, controller input, and polished combat feedback.

## Immediate Next Work

1. Stand up ORBEngine repository structure and architecture docs.
2. Build the first ORBEngine render sandbox with layered 2D assets.
3. Specify asset import contracts for `.swf`, `.piskel`, `.clip`.
4. Define collision-mask extraction from the bright-green authored outline.
5. Recreate the island hub in ORBEngine as the first vertical slice.
