# InnsmouthIsland Dimensional Asset Protocol

Date: 2026-03-11

## Purpose

This protocol defines how 2D PNG asset families should be authored and generated so they translate coherently into the InnsmouthIsland pseudo-3D runtime.

## Core Rules

1. Every graphical asset family must preserve a readable primary silhouette before any atmospheric detail is added.
2. Every asset canvas must reserve transparent-margin space for invisible anchor metadata.
3. Anchor metadata should be represented in source art and generation prompts as hidden alpha-zero distinct-color tether markers positioned in the canvas margins, never inside the visible art body.
4. Every asset must support coherent depth translation through consistent highlight direction, shadow falloff, curvature cues, and layer separation.
5. Every gameplay-relevant asset must define an invisible detection silhouette that is tighter than the decorative silhouette and suitable for collision, interaction, or hit logic.

## Anchor Node Schema

Each asset family should target the following anchor classes where applicable:

- `corner_nw`, `corner_ne`, `corner_se`, `corner_sw`: dimensional frame anchors for cubic-space linking.
- `top_plane`, `mid_plane`, `foot_plane`: depth registration anchors for pseudo-3D stacking.
- `head_socket`, `shoulder_socket_l`, `shoulder_socket_r`, `hand_socket_l`, `hand_socket_r`, `hip_socket`, `foot_socket_l`, `foot_socket_r`: character equipment anchors.
- `effect_stack_low`, `effect_stack_mid`, `effect_stack_high`: FX placement anchors.
- `adjacency_forward`, `adjacency_back`, `adjacency_left`, `adjacency_right`: environment stitching anchors.

## Detection Silhouette Rules

- Characters: separate cosmetic silhouette from hit silhouette; hit silhouette must favor readable combat fairness.
- Weapons: include grip, striking edge, and collision sweep guidance distinct from decorative flourishes.
- Props: collision silhouette should represent traversal blockers, not hanging detail or overgrowth.
- Ground/decals: detection silhouettes define traversable, slippery, harmful, or sticky zones rather than visible paint edges alone.
- Shelters/interactives: interaction silhouette, traversal silhouette, and occlusion silhouette may differ and should be treated separately.

## Shading And Curvature Rules

- Use one dominant light family per sheet.
- Use highlight ramps that imply stable curvature when projected into a pseudo-3D top/front hybrid view.
- Avoid ambiguous internal shading that reads as contradictory depth when layered with adjacent PNGs.
- Reserve rim-lighting for gameplay readability and anchor exposure, not general ornament.

## Pseudo-3D Translation Rules

- Large props and landmarks must read in three planes: foot contact, mass body, upper cap/roof/canopy.
- Ground assets must imply top-plane directionality and edge breakup suitable for stitched floor segments.
- Micro props must compose into adjacency clusters without destroying the parent prop silhouette.
- FX must support low, mid, and high stacking bands for volumetric placement.

## Runtime Integration Targets

- Use invisible silhouette data for player blocking, proximity checks, and occlusion selection.
- Use anchor-node metadata to derive foreground occlusion, top-cap projection, and layered plane linking.
- Use character socket metadata to drive equipment overlays or later explicit attachment maps.

## Generation Workflow

1. Generate a clean full pass using the protocol profile across all asset families.
2. Cross-reference outputs against approved research baselines.
3. Run a polish pass using the same protocol plus research-informed refinement goals.
4. Stage approved outputs for production intake and runtime translation.

## Future Use

This protocol is the default source of truth for future InnsmouthIsland rerolls, polish passes, and runtime asset-translation work.