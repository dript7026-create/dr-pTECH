# JumpClip Art Bible

## Purpose

This art bible defines how JumpClip should steer original asset generation toward a commercially credible, game-ready look without imitating any external protected property. It is keyed to JumpClip's existing controls so art direction can be expressed through the current designer and render pipeline.

## Core Rule

JumpClip should optimize for readable, ownable, shippable assets.

That means:

- strong silhouette before surface noise
- controlled palette behavior before uncontrolled detail accumulation
- animation readability before cosmetic clutter
- original ontology before borrowed aesthetic signatures

## Visual Priorities

JumpClip should resolve decisions in this order:

1. silhouette
2. pose clarity
3. proportion logic
4. material family
5. palette hierarchy
6. accessory load
7. texture detail

If two goals conflict, keep the earlier one and reduce the later one.

## Primary Read

The first read of a JumpClip asset should answer:

- what is it
- what does it do
- how heavy or agile is it
- what mood or role does it carry

That first read should survive at gameplay size, not just zoomed inspection.

## Shape Language

JumpClip should use a controlled vocabulary of shape bias rather than ad hoc ornament.

Recommended shape axes:

- compact versus elongated
- blunt versus tapered
- grounded versus lifted
- smooth versus segmented
- symmetrical versus biased
- ritual versus utilitarian

Every character, creature, prop, and effect should intentionally score across those axes.

## Proportion Rules

### Characters

- keep locomotion-credible torso, pelvis, and leg relationships
- let role identity come from shoulder width, limb taper, stance, and gear profile before micro detail
- make hands, face framing, and tool zones slightly more legible than strict realism would require
- exaggerate role posture more than anatomical distortion

### Creatures

- derive body design from locomotion, feeding logic, and rest posture
- place mass where the creature's motion suggests it must be supported
- keep head, forelimb, or dorsal silhouette readable as the species signature
- separate herbivore, predator, scavenger, burrower, glider, and sentinel posture grammars

### Props And Weapons

- exaggerate grip zones, strike zones, hinge logic, and carried weight
- make the functional end dominant in silhouette
- keep ornament subordinate to action readability

## Surface Detail Strategy

JumpClip should follow a three-band detail hierarchy:

- low-frequency: big mass blocks, large value groups, major trims
- mid-frequency: seams, banding, panels, layered materials, secondary contour breaks
- high-frequency: filigree, wear marks, stitching, studs, hair clumps, cracks, fine runes

Only one or two focal zones should carry sustained high-frequency detail.

## Palette Rules

Use three palette bands per asset family:

- anchor colors
- structural secondary colors
- accent or signal colors

Guidelines:

- anchor colors should define the role and faction or biome family
- secondary colors should separate mass groups
- accent colors should be reserved for focal read, VFX, ritual marks, eyes, or interface importance
- palette richness should never erase silhouette boundaries

## Material Families

JumpClip should treat materials as logic systems, not just colors.

Each material family should define:

- reflectance range
- edge sharpness
- fracture or wear mode
- layering logic
- stain or dirt behavior
- motion response if cloth, foliage, membrane, or chain-based

Examples of proprietary material families:

- kiln-ceramic shell
- lacquered reed composite
- salt-bloom leather
- lampglass resin
- ash-forged alloy
- pollen silk
- memory crystal

## Biome Readability

Every biome should have:

- a dominant mass language
- a dominant substrate color range
- a dominant weathering behavior
- one primary vegetation rhythm
- one primary threat silhouette family

JumpClip outputs should inherit those biome cues through costume edges, surface damage, and pose language when a biome tag is present.

## JumpClip Parameter Mapping

### `style_family`

Use this as the broad production bucket:

- `8bit`: iconic, low-noise, arcade clarity
- `16bit`: classic gameplay readability, controlled ornament
- `hd2d`: richer palette and layered surfaces while remaining sprite-native
- `bitmap-traced`: denser material cues and more illustrated finish
- `cel-shaded-2.5d`: animation-first staging with stronger line and lighting separation

### `silhouette_emphasis`

Controls how aggressively the asset should preserve role readability at small size.

- low: nuanced, less iconic, more naturalistic
- medium: balanced gameplay read
- high: hero-friendly or enemy-readable iconicity

### `texture_detail`

Controls how much mid and high-frequency surface language is permitted.

- low: flat or clean
- medium: layered but readable
- high: cosmetic or illustrated density

### `palette_limit`

Controls color discipline. Lower counts improve gameplay readability and faction coherence.

### `outline_weight`

Controls contour authority. Heavier outlines suit high-speed readability and lower-resolution targets.

### `accessory_density`

Controls how many secondary forms are permitted. Increase only after the primary silhouette already works.

### `tracing_bias`

Controls whether the finish leans toward illustrative/painted contour behavior instead of strongly quantized sprite logic.

## Focal Zones

JumpClip should concentrate detail and contrast in these zones first:

- face framing or gaze zone
- weapon/tool interaction zone
- chest or core identity zone
- feet/contact zone for motion readability

Do not spread peak contrast evenly across the whole asset.

## Designer Templates For JumpClip

### Courier Template

- silhouette: fast forward lean, readable carried mass
- detail: low on limbs, medium on bag/tool zones
- palette: two anchors plus one signal accent
- motion read: stride clarity over costume richness

### Duelist Template

- silhouette: tapered torso, long weapon line, asymmetric off-hand read
- detail: guard, sleeve, hem, and weapon hilt focalization
- palette: restrained body palette plus high-contrast weapon accent
- motion read: anticipation, extension, recovery

### Heavy Template

- silhouette: broad pelvis and shoulder block, compact limbs, grounded stance
- detail: plates, straps, reinforcement joints
- palette: heavy anchor values with limited accent signals
- motion read: compression and delayed recovery

### Mystic Template

- silhouette: verticality, layered cloth, halo or totem shapes
- detail: mid-frequency symbolic patterning, not all-over clutter
- palette: calm anchor tones with one luminous accent system
- motion read: float, pause, gesture emphasis, non-combat hand language

## Animation-Aware Art Rules

An asset is only successful if it survives motion.

Therefore:

- avoid accessories that destroy limb readability in key poses
- ensure the line of action remains visible in anticipation and impact frames
- keep knees, elbows, hands, feet, and head readable as motion anchors
- bias costume shapes to support the character's motion family

## Anti-Derivation Rules

JumpClip must not:

- target named protected games, factions, races, or costume kits as generation goals
- reproduce iconic silhouette combinations from protected IP
- use copyrighted screenshots, textures, model sheets, or turnarounds as direct production guides unless the user owns or licenses them appropriately
- use “make it like X game's nation/race/faction” as a valid prompt mode

## Approval Checklist

Before an art direction is accepted, confirm:

- the silhouette works at gameplay size
- the role is readable within one second
- the palette separates mass groups cleanly
- accessories do not hide the action path
- material logic is consistent with the setting
- the asset family is clearly original

## Bottom Line

JumpClip should not optimize for novelty alone. It should optimize for readable originality. The best outputs will feel authored, functional, and alive before they feel ornate.