# Bango-Patoot 2D To 3D Reconstruction Pipeline

Date: 2026-03-12

## Scope

This document defines the exact asset-analysis and 2D-to-3D reconstruction workflow for the Bango-Patoot QA demo asset pass.

The goal is not to pretend that image generation alone can produce shippable 3D models automatically. The goal is to define a deterministic analysis pipeline that converts approved 2D masters into:

- Per-pixel analysis matrices.
- Symbol-object region maps.
- Depth-hint maps.
- Spatial metric tables.
- Mesh blockout constraints.
- Rig projection constraints.
- Surface material and texture guidance.
- Animation keypose intake data.

## Core Principle

Every approved 2D master is treated as a structured spatial document.

That document is decomposed in this order:

1. Pixel matrix.
2. Local-neighborhood comparison grid.
3. Edge and boundary map.
4. Region segmentation map.
5. Symbol-object graph.
6. Depth-hint field.
7. Spatial metric table.
8. Mesh-blockout proxy.
9. Rig-constrained deformation zones.
10. Surface material and height-texture projections.
11. Keypose and animation intake layers.

## Pixel Matrix Definition

Every source image is transformed into a pixel matrix where each pixel stores:

- Integer coordinates: x and y.
- RGBA.
- Linear RGB.
- Perceptual color values in Lab.
- Alpha occupancy state.
- Local gradient magnitude.
- Local gradient direction.
- Edge confidence.
- Region identifier.
- Symbol-object identifier.
- Depth-hint value.
- Surface-normal hint.

## 32-Neighbor Stencil

The required neighborhood analysis stencil is 32 pixels per source pixel.

The 32-reference neighborhood consists of:

- Radius 1 ring: 8 neighbors.
- Radius 2 cardinal and diagonal ring: 8 neighbors.
- Radius 2 knight-offset ring: 8 neighbors.
- Radius 3 cardinal ring plus near-cardinal offsets: 8 neighbors.

The exact ordered offsets are:

- Radius 1: (-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)
- Radius 2 axial-diagonal: (-2,-2), (0,-2), (2,-2), (-2,0), (2,0), (-2,2), (0,2), (2,2)
- Radius 2 knight: (-2,-1), (-1,-2), (1,-2), (2,-1), (-2,1), (-1,2), (1,2), (2,1)
- Radius 3 near-cardinal: (0,-3), (-1,-3), (1,-3), (-3,0), (3,0), (0,3), (-1,3), (1,3)

For each center pixel, the pipeline compares the center against all 32 neighbors using:

- Delta alpha.
- Delta luminance.
- Delta chroma.
- Delta hue proxy.
- Perceptual Delta E in Lab.
- Gradient direction change.

## Boundary Classification

Every pixel receives one of these boundary states:

- Empty space.
- Interior stable fill.
- Soft material transition.
- Hard material transition.
- Silhouette boundary.
- Occlusion boundary.
- Highlight boundary.
- Noise or artifact candidate.

Hard and silhouette boundaries are defined by strong contrast, alpha discontinuity, or persistent local Delta E break across the 32-neighbor stencil.

## Region Segmentation

Pixels are grouped into self-contained symbolic spaces called symbol objects.

Each symbol object is a contiguous or intentionally linked region that represents one meaningful piece of the source asset, such as:

- Head.
- Horn.
- Beak.
- Hand.
- Wing.
- Cloak flap.
- Boot.
- Weapon head.
- Shrine bell.
- Floor tile face.
- Prop body.
- Emissive rune.
- Pickup core.

Segmentation is driven by:

- Alpha continuity.
- Color similarity.
- Boundary strength.
- Enclosed contour shape.
- Repeat-safe tile edges for environment kits.
- Expected rig or gameplay semantics.

## Symbol-Object Record

Every symbol object stores:

- Symbol id.
- Parent symbol id, if nested.
- Category: body, costume, prop, tile, ornament, emissive, FX, UI, background-empty.
- Bounding box.
- Pixel count.
- Boundary contour.
- Centroid.
- Primary color family.
- Material family.
- Local thickness hint.
- Suggested pivot points.
- Suggested socket points.
- Suggested collision mask type.
- Suggested deformation type: rigid, semi-rigid, cloth-like, flesh-like, emissive-only.
- Adjacent symbol ids.
- Occlusion order hint.

## Depth Map Construction

Each approved asset must receive a pixel-by-pixel simulated depth field.

The depth field is not treated as an artistic grayscale map alone. It is treated as a structured combination of:

- Silhouette depth assumption.
- Internal form convexity and concavity hints.
- Material stack order.
- Region overlap priority.
- Front-facing versus recessed surface confidence.

Depth is inferred using:

- Local brightness under normalized lighting assumptions.
- Edge shadow and highlight pairing.
- Region enclosure logic.
- Known anatomy or prop conventions.
- Cross-view consistency for front, side, rear, and action sheets.

Output fields per pixel:

- z_depth_normalized.
- x_surface_tilt.
- y_surface_tilt.
- confidence score.

## Spatial Metric Translation

The simulated 2D-to-3D depth field is translated into engine-facing spatial metrics.

Per symbol object, the pipeline derives:

- Width in source pixels.
- Height in source pixels.
- Estimated thickness in source pixels.
- Estimated convex hull volume.
- Local facing direction.
- Pivot anchor candidates.
- Collision proxy type.
- Recommended mesh blockout primitive set.

These metrics then map into engine-space units using runtime export scale.

Example conversion targets:

- Standard 24x36 actor sprite becomes one actor blockout reference volume.
- Standard 24x36 enemy sprite becomes one collision proxy plus one mesh envelope reference.
- 48x48 prop tile becomes one modular prop blockout volume.

## Environment Mapping Rules

Environment kits must be translated into 3D space as modular blockout pieces, not as arbitrary sculpt data.

Each tile or prop symbol object must provide:

- Front face region.
- Side seam regions.
- Top cap region when visible.
- Repeat boundary tags.
- Walkable or non-walkable classification.
- Collision solidity classification.
- Decorative-only classification if applicable.

The reconstruction target for environment assets is:

- Engine-space modular pieces.
- Repeat-safe UV islands.
- Height or relief hints for surface detail.
- Collision and traversal-ready proxy meshes.

## Character And Creature Mapping Rules

For characters, companions, enemies, elites, and bosses, the reconstruction target is a rig-informed mesh envelope.

The pipeline must project symbol objects onto the declared skeleton in this order:

1. Root and pelvis mass.
2. Spine and chest mass.
3. Neck and head mass.
4. Limb volumes.
5. Secondary anatomy such as horns, beak, tail, wings.
6. Costume and accessory shells.
7. Weapon and held-item rigid components.

Each body-linked symbol object must be tagged as one of:

- Bone-owned rigid volume.
- Bone-owned deforming volume.
- Multi-bone blend zone.
- Socketed accessory.
- Cloth or flap secondary volume.

## Mesh Modelling Contract

The output of the 2D-to-3D analysis stage is not a final sculpt. It is a mesh contract.

That contract must define:

- Required mesh sections.
- Section ownership by rig or environment module.
- Recommended primitive blockout shape per section.
- Thickness and extrusion hints.
- Surface relief hints.
- UV density intent.
- Material slots.
- Collision and occlusion notes.

## Surface And Texture Projection

Fine surface detail from the 2D source must be translated into texture and height intent, not blindly baked as geometry.

For every symbol object, the pipeline records:

- Base albedo color group.
- Accent color groups.
- Surface roughness hint.
- Emissive hint.
- Height-detail hint.
- Normal-detail hint.
- Tiling or unique texture classification.

The expected texture outputs are:

- Base color map.
- Depth or height hint map.
- Normal hint map.
- Material mask map.
- Emissive mask when needed.

## Keypose Intake Preparation

Once the reconstructed 3D forms exist, the pipeline prepares them for animation keypose intake.

Each animated object must define:

- Bind pose.
- Key deformation zones.
- Rigid-only regions.
- Blend-only regions.
- IK-relevant endpoints.
- Contact-critical points such as feet, hands, beak, horn tips, weapon heads.

## Animation Finalization Rules

Animation is completed in three layers.

1. Authored keyposes.
2. Preset basic interpolation clips.
3. Runtime inbetween refinement.

Runtime inbetween refinement may use AI-guided or physics-guided interpolation, but only after the following are already locked:

- Stable keypose library.
- Stable rig weights.
- Stable collision and contact rules.
- Stable gameplay timing windows.

The runtime system should only solve for:

- Minor overlap.
- Secondary motion.
- Contact settling.
- Procedural balance adjustment.
- Soft anticipation and recovery smoothing.

It must not invent core silhouette-changing motion that should have been authored in the keyposes.

## Minimum Deliverables Per Asset

Every final approved asset must eventually have these derived outputs:

- Pixel matrix file.
- Region segmentation file.
- Symbol-object graph file.
- Depth map file.
- Spatial metrics file.
- Mesh contract file.
- Rig mapping file if the asset is animated.
- Material or texture contract file.

## Practical Constraint

This repo does not currently contain the generated QA demo masters needed to run the full pipeline. The correct next step is therefore to lock the analysis contract now, then run the actual decomposition after the Recraft pass produces the approved source masters.
