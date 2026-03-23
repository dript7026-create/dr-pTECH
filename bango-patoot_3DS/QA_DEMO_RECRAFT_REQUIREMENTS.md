# Bango-Patoot QA Demo Recraft Requirements

Date: 2026-03-12

## Objective

This document defines the bare minimum Recraft generation pass required to support a playable Bango-Patoot vertical-slice demo with the full intended systems layer implemented and ready for QA play testing on both Windows and Nintendo 3DS hardware.

This pass must be written and reviewed as an integration-first production specification, not just as an art-direction brief.

## Integration Truth

Recraft outputs are image masters. They are not native meshes, rigs, UV layouts, or authored animation clips.

Because of that, literal 100 percent integration accuracy cannot be guaranteed by generation alone. The only honest way to lock this pass down is to define 100 percent integration accuracy as follows:

- Every generated master is structurally compliant with the runtime slicing, atlas, pivot, scale, and alpha rules in this document.
- Every generated master is suitable as a direct source for billboards, impostors, UI slices, collision silhouettes, and rig-reference tracing.
- Every generated master is suitable as orthographic or pseudo-orthographic reference for later mesh blockout, retopo, UV planning, rig setup, and animation authoring.
- Every generated master passes a post-generation validation pass before being treated as production-ready.

That is the strongest reliable contract this generation pass can support.

## Integration-First Contract

Every asset in this pass must be authored as if it will be used in all of these downstream roles:

- Runtime sprite export source.
- Billboard or impostor source for the current hybrid renderer.
- Orthographic blockout reference for later mesh modelling.
- Rig anchor and volume reference for later skeletal setup.
- Animation keypose reference for later authored clips.
- UI or interaction-state source for player feedback and QA capture.

## Non-Negotiable Capture Rules

These rules apply to every Recraft master in the pass.

- Camera must be orthographic or effectively orthographic. No cinematic foreshortening.
- Turnaround sheets must use true front, left, right, and rear views only.
- Multi-frame action sheets must keep the same camera, scale, horizon, and baseline in every cell.
- Subject must be centered in the cell with a stable grounded baseline.
- Subject height within each cell should occupy roughly 70 to 82 percent of the usable cell height unless the asset is intentionally oversized.
- Silhouette must be fully contained inside the cell with no crop and at least 2 percent empty margin on every side.
- Background must be fully transparent.
- Alpha fringe must be clean. No soft ghost halo around the sprite.
- Lighting must be simple and descriptive: one readable key, one soft fill, minimal rim. No scene lighting that destroys form readability.
- Material regions must remain separable at small scale. Leather, fur, brass, wax, cloth, bone, and machine parts must not collapse into one noisy cluster.
- Interior detail must serve shape definition, not texture noise.
- Every prompt must avoid requesting atmospheric camera effects, depth of field, film grain, bloom, motion blur, or painterly smudging.

## Mesh, Rig, And Animation Readiness Rules

The pass must support later mesh or rig work even when the current runtime is still billboard-heavy.

- Character and enemy turnarounds must preserve stable body volume between front, side, and rear views.
- Major joints must remain readable in silhouette and in local shape breaks: shoulder, elbow, wrist, hip, knee, ankle, neck, jaw, and wing root where applicable.
- Costume pieces must read as layered forms rather than painted surface patterns.
- Accessories must be attached in physically sensible locations that can later be rigged or socketed.
- Props and interactables must read as complete objects with obvious facing, support, and collision mass.
- Modular world pieces must present believable seam edges and repeat-safe side boundaries.
- Boss and elite sheets must expose attack-source anatomy and weak-point logic clearly enough for later hitbox and VFX hookup.
- Portrait-capable character sheets must keep the head, face, and upper torso readable enough for 96x96 dialogue crops.

## Post-Generation Validation Gates

No asset is considered production-safe until it passes all applicable validation gates.

- Cell alignment gate: all cells share the same baseline and camera orientation.
- Scale gate: downsampled runtime exports match the intended target size without losing identity.
- Alpha gate: no matte fringe or dirty transparency.
- Slice gate: automatic or semi-automatic slicing can isolate the asset cleanly.
- Pivot gate: a stable pivot can be assigned from the generated master without guesswork.
- Collision gate: collision mass can be inferred from the silhouette without contradiction.
- Rig gate: body segmentation is clean enough for bone placement or overdraw trace work.
- Animation gate: action poses show unmistakable anticipation, contact, recoil, and recovery moments where needed.
- UI gate: icons and interface slices remain legible on both dark and warm in-game backgrounds.

The target demo must be able to exercise:

- Title flow and boot presentation.
- Save/load and return-to-hub continuity.
- Hub traversal and shrine interaction.
- One combat route with standard enemies.
- One elite encounter and one boss encounter.
- Dodge, attack, hurt, interaction, pickup, and shrine feedback.
- Collectibles, wildlife, and forage interaction.
- NPC dialogue and objective delivery.
- HUD, menu, and QA-readable debug overlays.

## Demo Scope

The minimum QA demo content target is:

- Zone 1: Underhive Hub / Apiary Junction.
- Zone 2: Brassroot Borough combat route.
- One shrine/save point.
- Four key NPCs.
- Four standard enemy families.
- One elite enemy.
- One boss.
- One full player move set sufficient for locomotion, melee, dodge, shrine interaction, and Patoot support.
- One pass of pickup, HUD, VFX, and UI assets.

## Platform Targets

The pass must support both targets from one source asset set.

- Windows target: nearest-neighbor preview and QA capture build using the same logical sprite and UI export sizes as the 3DS build.
- 3DS top screen target: 400x240 per eye.
- 3DS bottom screen target: 320x240.

## Runtime Export Rules

These are the exact export sizes that downstream tooling should produce from the Recraft masters.

- Standard character world sprite: 24x36.
- Standard NPC world sprite: 24x36.
- Standard enemy world sprite: 24x36.
- Elite enemy world sprite: 32x48.
- Boss world sprite: 32x48.
- Small collectible sprite: 16x16.
- Medium collectible or icon sprite: 24x24.
- Standard prop sprite: 24x36.
- Large prop sprite: 48x48.
- Portrait crop: 96x96.
- HUD icon: 16x16 or 24x24.
- Full-width top HUD strip target: 400x32.
- Bottom panel target blocks: 320x240 assembled from exported slices.

## Generation Rules

Every Recraft output in this pass must satisfy all of the following:

- Transparent background only.
- No text, no logos, no watermark.
- Strong silhouette readability at 24x36 after downsampling.
- Lighting and materials must survive nearest-neighbor reduction.
- Forms must remain legible in both dark underhive scenes and bright shrine scenes.
- Every sprite master must reserve a 2 percent empty margin on all sides to prevent crop loss during slicing.
- Every standard character or enemy sheet must center the subject within the cell and keep feet grounded on a consistent baseline.
- Every UI sheet must leave a 32 pixel outer safe margin on the master canvas for manual slicing.
- Every master intended for sprite export must avoid soft airbrush noise and micro-detail that will collapse at 3DS scale.
- Final exported sprite variants should stay at or below 15 visible colors per local sprite where possible so the current generator remains practical.

## Prompt Appendix Contract

Every asset prompt in the machine-readable manifest must be read together with the shared appendix contract stored in the manifest metadata.

That appendix must enforce all of the following prompt-language requirements:

- Orthographic or pseudo-orthographic technical presentation.
- Transparent background only.
- Stable centered subject.
- Fixed grounded baseline.
- Full silhouette inside frame.
- Clean alpha edge.
- Shape-first readability after nearest-neighbor downsampling.
- Modular, segmentation-friendly, rig-trace-friendly form language.
- No perspective distortion, no atmospheric blur, no camera FX.

## Integration Pipeline

The expected path from generation to runtime is:

1. Generate the Recraft masters using the detailed manifest and its shared prompt appendix.
2. Review every master against the validation gates above.
3. Reject and regenerate any master that fails silhouette, baseline, alpha, or segmentation checks.
4. Slice the approved masters into exact runtime exports.
5. Assign pivots, collision silhouettes, and rig-reference anchors.
6. Load the exports into the Windows QA build and the 3DS build.
7. Perform in-engine visual verification before declaring the pass locked.

## Pixel-Precise Master Formats

Use these exact master canvas formats.

- Standard 4-angle turnaround sheet: 1536x576, grid 4x1, cell 384x576, exports to four 24x36 runtime frames.
- Standard 6-frame action sheet: 2304x576, grid 6x1, cell 384x576, exports to six 24x36 runtime frames.
- NPC story sheet: 1152x576, grid 3x1, cell 384x576, exports to one 24x36 standee plus one 96x96 portrait crop.
- Elite or boss 4-angle turnaround: 2048x768, grid 4x1, cell 512x768, exports to four 32x48 runtime frames.
- Elite or boss 6-frame action sheet: 3072x768, grid 6x1, cell 512x768, exports to six 32x48 runtime frames.
- Environment or object kit: 1536x1536, grid 6x6, cell 256x256, exports to mixed 24x24, 24x36, and 48x48 props.
- Small pickup or wildlife kit: 1024x1024, grid 4x4, cell 256x256, exports to mixed 16x16, 24x24, and 24x36 assets.
- FX kit: 1536x768, grid 6x3, cell 256x256, exports to mixed 24x24 and 48x48 effects.
- UI kit: 2048x1024, free layout with 32 pixel master-safe margin, exports to top HUD strips, icons, bottom-panel slices, and menu widgets.

## Credit Budget

Budget assumption: Recraft v4 image generation at 40 credits per output.

| Category | Asset Count | Credits |
| --- | ---: | ---: |
| Player and companion | 10 | 400 |
| NPCs | 4 | 160 |
| Enemies | 12 | 480 |
| World, props, interactables | 14 | 560 |
| Wildlife and VFX | 6 | 240 |
| UI | 4 | 160 |
| Total | 50 | 2000 |

## Manifest

| # | Asset | Master Canvas | Runtime Export Target | Credits | Required For |
| ---: | --- | --- | --- | ---: | --- |
| 1 | bango_turnaround_master | 1536x576 | 4x 24x36 | 40 | Player world render |
| 2 | bango_locomotion_sheet | 2304x576 | 6x 24x36 | 40 | Walk, idle, run loop |
| 3 | bango_melee_sheet | 2304x576 | 6x 24x36 | 40 | Attack chain |
| 4 | bango_dodge_interact_sheet | 2304x576 | 6x 24x36 | 40 | Dodge and shrine use |
| 5 | bango_hurt_fall_sheet | 2304x576 | 6x 24x36 | 40 | Hurt, knockback, recover |
| 6 | patoot_turnaround_master | 1536x576 | 4x 24x36 | 40 | Companion world render |
| 7 | patoot_locomotion_sheet | 2304x576 | 6x 24x36 | 40 | Strut and hover loop |
| 8 | patoot_support_attack_sheet | 2304x576 | 6x 24x36 | 40 | Support peck and cast |
| 9 | patoot_glide_perch_sheet | 2304x576 | 6x 24x36 | 40 | Glide, perch, scout |
| 10 | patoot_hurt_recall_sheet | 2304x576 | 6x 24x36 | 40 | Hit react and recall |
| 11 | tula_story_sheet | 1152x576 | 24x36 plus 96x96 | 40 | Narrative scenes |
| 12 | mother_comb_edda_sheet | 1152x576 | 24x36 plus 96x96 | 40 | Shrine mentor |
| 13 | vilm_siltcoat_sheet | 1152x576 | 24x36 plus 96x96 | 40 | Route and salvage NPC |
| 14 | sister_halceon_sheet | 1152x576 | 24x36 plus 96x96 | 40 | Quest and boss lead-in |
| 15 | waxbound_cultist_turnaround | 1536x576 | 4x 24x36 | 40 | Standard enemy family A |
| 16 | waxbound_cultist_action | 2304x576 | 6x 24x36 | 40 | Attack and stagger |
| 17 | boiler_jackal_turnaround | 1536x576 | 4x 24x36 | 40 | Standard enemy family B |
| 18 | boiler_jackal_action | 2304x576 | 6x 24x36 | 40 | Rush and strike |
| 19 | signal_heretic_turnaround | 1536x576 | 4x 24x36 | 40 | Standard enemy family C |
| 20 | signal_heretic_action | 2304x576 | 6x 24x36 | 40 | Cast and recoil |
| 21 | gutter_cryptid_turnaround | 1536x576 | 4x 24x36 | 40 | Standard enemy family D |
| 22 | gutter_cryptid_action | 2304x576 | 6x 24x36 | 40 | Leap and bite |
| 23 | debt_collector_elite_turnaround | 2048x768 | 4x 32x48 | 40 | Elite encounter |
| 24 | debt_collector_elite_action | 3072x768 | 6x 32x48 | 40 | Elite attack cycle |
| 25 | bishop_static_boss_turnaround | 2048x768 | 4x 32x48 | 40 | Boss world render |
| 26 | bishop_static_boss_action | 3072x768 | 6x 32x48 | 40 | Boss attack cycle |
| 27 | apiary_hub_tileset_kit | 1536x1536 | 24x24 and 48x48 | 40 | Hub floor, walls, trims |
| 28 | apiary_hub_prop_kit | 1536x1536 | 24x36 and 48x48 | 40 | Hub stalls and fixtures |
| 29 | apiary_shrine_kit | 1536x1536 | 24x36 and 48x48 | 40 | Shrine, save, refine node |
| 30 | brassroot_street_tileset_kit | 1536x1536 | 24x24 and 48x48 | 40 | Street route geometry |
| 31 | brassroot_verticality_kit | 1536x1536 | 24x36 and 48x48 | 40 | Ladders, lifts, catwalks |
| 32 | brassroot_prop_kit | 1536x1536 | 24x36 and 48x48 | 40 | Barrels, carts, vents |
| 33 | breakable_crate_barrel_kit | 1536x1536 | 24x36 | 40 | Combat and pickup props |
| 34 | door_gate_switch_kit | 1536x1536 | 24x36 and 48x48 | 40 | Lock, gate, switch logic |
| 35 | collectible_pickup_kit | 1024x1024 | 16x16 and 24x24 | 40 | Notes, sigils, honey, loot |
| 36 | lantern_kin_rescue_kit | 1024x1024 | 16x16, 24x24, 24x36 | 40 | Rescue loop |
| 37 | shrine_vendor_save_kit | 1536x1536 | 24x36 and 48x48 | 40 | Vendor and save props |
| 38 | hazard_effect_prop_kit | 1536x1536 | 24x24 and 48x48 | 40 | Steam vents and danger props |
| 39 | signage_wayfinding_kit | 1536x1536 | 24x24 and 24x36 | 40 | Navigation readability |
| 40 | world_map_marker_kit | 1024x1024 | 16x16 and 24x24 | 40 | Objective and map icons |
| 41 | flora_forage_kit | 1024x1024 | 16x16 and 24x24 | 40 | Harvestable flora |
| 42 | fauna_ambient_kit | 1024x1024 | 24x24 and 24x36 | 40 | Wildlife behavior loop |
| 43 | combat_fx_kit | 1536x768 | 24x24 and 48x48 | 40 | Hit sparks and slash arcs |
| 44 | magic_fx_kit | 1536x768 | 24x24 and 48x48 | 40 | Arcana and shrine effects |
| 45 | traversal_fx_kit | 1536x768 | 24x24 and 48x48 | 40 | Dodge, dust, glide trails |
| 46 | atmosphere_overlay_kit | 1536x768 | 48x48 and screen slices | 40 | Fog, pollen, embers |
| 47 | hud_core_kit | 2048x1024 | 16x16, 24x24, 400x32 | 40 | HP, stamina, magic, prompts |
| 48 | menu_inventory_kit | 2048x1024 | 24x24 and panel slices | 40 | Bottom-screen menus |
| 49 | dialogue_portrait_kit | 2048x1024 | 96x96 portraits | 40 | Dialogue, quest callouts |
| 50 | title_boot_kit | 2048x1024 | 400x240 plus slices | 40 | Start screen and boot flow |

## Asset-Level Acceptance Requirements

### Player and Companion

- Bango and Patoot must remain readable at 24x36 with distinct head, torso, and limb separation.
- Idle, locomotion, attack, hurt, and dodge silhouettes must be distinguishable in single-frame QA captures.
- Patoot glide and perch poses must read without relying on motion blur.

### NPCs

- Every NPC sheet must produce one world standee and one portrait crop from the same render.
- Tula must support both captive and active-echo presentation inside one sheet.

### Enemies

- Each standard enemy family must have one unmistakable silhouette and one readable attack language.
- Elite and boss sheets must preserve readable weak-point or attack-source anatomy after downsampling.

### World and Prop Kits

- Hub and Brassroot kits must provide enough visual difference that QA can identify the active zone in a static screenshot.
- Doors, switches, breakables, pickups, and shrine props must each have one unmistakable interactable silhouette.

### Wildlife and VFX

- Forage assets must be distinct from combat pickups.
- Ambient wildlife must read as non-hostile at first glance.
- Combat, magic, and traversal FX must remain readable without additive blending.

### UI

- HP, stamina, and magic must each have separate shapes, not just color differences.
- All UI icons must remain readable on both dark and warm backgrounds.
- Title art must work at 400x240 without requiring subtitle text to explain the scene.

## Recommended Production Order

1. Player and companion sheets.
2. HUD core kit and title boot kit.
3. Hub shrine, pickup, and map-marker kits.
4. Standard enemy sheets.
5. Brassroot environment kits.
6. NPC story sheets.
7. Elite and boss sheets.
8. Wildlife and final FX kits.

## Deliverables

This pass is complete only when all of the following exist:

- The machine-readable manifest at `recraft/bango_patoot_qa_demo_manifest.json`.
- The 2D-to-3D reconstruction contract at `ASSET_TO_3D_RECONSTRUCTION_PIPELINE.md`.
- The machine-readable reconstruction spec at `recraft/bango_patoot_qa_demo_3d_reconstruction_spec.json`.
- The metadata enrichment tool at `tools/enrich_qa_demo_manifest.py`.
- The manifest validation tool at `tools/validate_qa_demo_manifest.py`.
- The reconstruction analyzer at `tools/analyze_asset_reconstruction.py`.
- The runtime slicer at `tools/slice_qa_demo_assets.py`.
- The Windows QA preview build script at `build_windows_preview.ps1`.
- The 50 generated Recraft masters in category folders.
- A post-process export pass that slices masters into the runtime sizes defined above.
- A Windows QA build using those runtime exports.
- A 3DS build using the same export set.
