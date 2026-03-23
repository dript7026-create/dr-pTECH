# InnsmouthIsland Asset Bible

## Progress Note

- The standalone executable path is validated through `ORBEngine/build_innsmouth_island.ps1` and currently supports the InnsmouthIsland player, 10 total enemy entities, 23 weapons, 14 armor sets, persistent pickups, MurkShelters, shrine flow, lock-on, aerial actions, and a software atmospheric lighting pass.
- The next gameplay-side engineering steps are intentionally deferred: boss-specific aerial phases, visible armor silhouette swaps, richer shrine upgrade consequences, fast-travel map choice, and full NG+ carryover.
- This document freezes the asset-production pass so art, audio, pseudo-3D translation, physics mapping, and gameplay binding can proceed without losing the current gameplay state.

## Production Doctrine

- Tone: black-tide ooze-punk, wet New England ruin-horror, fungal bioluminescence, industrial fishing salvage, barnacle-metal, ceremonial abyss iconography.
- Readability rule: every gameplay-significant silhouette must remain legible at gameplay camera distance before atmospheric treatment is added.
- Material rule: surfaces should always communicate one of these states: soaked, salt-crusted, fungal, tar-black, oxidized brass, cracked basalt, eel-slick hide, or pearl-lit ritual polish.
- Competitive-quality target: every asset needs three simultaneous readings: immediate gameplay silhouette, mid-range material storytelling, and close inspection micro-detail.
- Animation doctrine: each motion set must have anticipation, commit, impact, settle, and recovery beats even if the runtime currently compresses them into fewer frames.
- Audio doctrine: every action-worthy state requires a dry one-shot, a wet tail, and a systemic layer hook for ambience/music ducking.

## External Benchmark Integration

- OpenGameArt benchmarking reinforced breadth expectations across art, UI, sound, and music, and it also reinforced that any future imported reference must be tracked per asset rather than by host site alone.
- Kenney benchmarking reinforced modular completeness: every mechanic should ship with a whole supporting asset family rather than a few isolated hero pieces.
- Liberated Pixel Cup benchmarking reinforced the need for a hard style guide, shared perspective assumptions, and consistent construction rules that survive collaborative or batched generation.
- These benchmark findings were incorporated into this document as production standards only. No third-party assets were copied into the repo as part of this pass.

## Naming And Export Rules

- Prefix all final InnsmouthIsland art with `innsmouth_`.
- Split sheets by role: `player`, `enemy`, `boss`, `weapon`, `armor`, `pickup`, `shelter`, `prop`, `landmark`, `ui`, `fx`, `codex`.
- Store authored pivots in metadata using foot-anchor for characters, center-anchor for pickups, base-anchor for props, and entry-anchor for traversable landmarks.
- Keep collision-authoring masks separate from paint layers.
- Author silhouette-safe versions first, then atmospheric overpaint variants second.
- Preserve a neutral-light reference render for each asset so ORBdimensionView can derive pseudo-depth and collision extents consistently.

## Entity Animation And Moveset Specification

### Player: Fish-Man Drifter

- Core silhouette: broad shoulders, amphibious neck frill, digitigrade lower legs, ribbed forearms, tide-wrapped waist gear, luminous throat sacs, salvage weapon harness.
- Required animation suite:
  - crawl_beach_intro: 12 frames.
  - idle_breathing: 10 frames with throat pulse and shoulder drift.
  - heal_moisture_draw: 12 frames with palm-to-chest resonance.
  - walk_8dir_feel sheet posed for forward/strafe readability: 12 frames.
  - run_8dir_feel: 12 frames with stronger shoulder lead.
  - jump_start: 6 frames.
  - jump_airborne: 8 frames.
  - double_jump_or_air_kick transition: 6 frames.
  - dodge_ground: 8 frames.
  - dodge_air: 8 frames.
  - crouch_lower: 4 frames.
  - crouch_idle: 6 frames.
  - slide: 8 frames with spray trail.
  - focus_lock_stance: 8 frames.
  - light_attack_chain_a_b_c: 8 plus 8 plus 10 frames.
  - heavy_attack_chain_a_b: 12 plus 14 frames.
  - aerial_light: 8 frames.
  - aerial_heavy_plunge: 10 frames.
  - block_start_hold_release: 4 plus 6 plus 4 frames.
  - parry_flash: 6 frames.
  - hurt_front and hurt_back: 6 plus 6 frames.
  - stagger_short and stagger_long: 6 plus 10 frames.
  - consume_throwable and consumable_use: 8 plus 8 frames.
  - projectile_throw and projectile_aim: 8 plus 6 frames.
  - shrine_rest_kneel: 12 frames.
  - shrine_upgrade_resonance: 12 frames.
  - victory_tide_ascend: 16 frames.
  - defeat_sink: 12 frames.
- Audio one-shots:
  - wet footstep light, wet footstep heavy, stone footstep, wood footstep, shallow water splash, dodge splash, jump launch, landing thud, block shell ring, parry sting, light hit flesh, heavy hit crack, hurt hiss, healing resonance, seed pod throw, flask toss, knife fan release, shrine kneel, shrine awaken, death exhale.

### Standard Enemies

- Deep One Raider:
  - silhouette: spear or hook profile, hunched dorsal fin, ragged tide-cloth.
  - animations: idle, patrol, alert, rush, 2-hit combo, grab feint, recoil, stagger, collapse, wet roar.
  - audio: gill-click chatter, spear scrape, body slap, short aggro bark.
- Shoggoth Spawn:
  - silhouette: low gelatinous mound with eye clusters and bone shards.
  - animations: pulsate idle, creep, split-lunge, pseudopod slam, recoil wobble, rupture death.
  - audio: bassy mucus churn, bubble pop, slap impact, squelch collapse.
- Nightgaunt Stalker:
  - silhouette: winged negative-space body, thin tail, hook limbs.
  - animations: perch idle, glide, burst dive, talon slash, air recoil, perch reset, death fold.
  - audio: dry leather flutter, whisper shriek, passing wind shear, claw rake.
- Mi-Go Scavenger:
  - silhouette: insectoid fungal shell, gear satchel, saw-limb.
  - animations: idle twitch, sidestep, probe strike, scavenger harvest, recoil, alarm call, collapse.
  - audio: chitin chatter, drill-click, sack rattle, fungal hiss.
- Ghoul Woodsman:
  - silhouette: heavy axe body, bark cloak, exposed jaw.
  - animations: idle sway, trudge, overhead chop, shoulder rush, howl, recoil, kneel death.
  - audio: wood handle creak, throat growl, heavy stomp, chop bite.
- Cultist Harpooner:
  - silhouette: raincloak, harpoon coil, lantern mask.
  - animations: idle prayer, strafe, aim, throw, reel-back, panic retreat, collapse.
  - audio: rope whip, harpoon launch, chant whisper, cloth snap.
- Star-Spawn Wretch:
  - silhouette: dense torso, star-shaped shoulder mass, pressure vents.
  - animations: idle vent, stalk, crush swipe, pressure burst, recoil, eruption death.
  - audio: pressure hiss, sub-bass groan, vent pop, meat-metal impact.
- Drowned Pilgrim:
  - silhouette: robe columns, censer chain, face shroud, salt lantern.
  - animations: kneel idle, drift walk, blessing channel, staff strike, heal pulse, recoil, robe slump death.
  - audio: chain clink, drowned prayer, salt burn crackle, hollow staff hit.

### Bosses

- Reptilian Abyss Prince:
  - body language: ritual authority, coiled patience, sudden forward puncture.
  - phase set:
    - phase_1 idle throne rise, spear cast, tail sweep, command roar, leap slam, recoil.
    - phase_2 venom spray, double sweep, pillar perch, aerial dive, summon seal pulse.
    - phase_3 enraged crawl, triple strike, tidal shockwave, death unravel.
  - audio: obsidian scrape, hiss-roar hybrid, temple bass pulse, wet tail boom.
- Jaguar Eclipse Tyrant:
  - body language: elastic stalking, moon-slice pounce arcs, smoke-fast recoveries.
  - phase set:
    - phase_1 crouch stalk, claw fan, shadow pounce, wall cling, recoil.
    - phase_2 aerial rake, eclipse dash, roar burst, decoy fade, blood-moon slam.
    - phase_3 chain pounce, corkscrew maul, collapsing roar, death disintegration.
  - audio: predator rasp, bass pounce impact, eclipse ring, claw shriek, body drag.

## Weapon Visual Asset Specification

### Melee Weapons

- Barnacle Shiv: chipped shell blade, gut-rope wrap, salt-pitted spine.
- Tide Hook: iron hook with eelbone grip and rope tassel.
- Coral Mace: dead coral bulb with embedded teeth.
- Dock Cleaver: broad rusted fish-processing blade.
- Shell Glaive: crescent shell edge on slim pole.
- Pearl Pike: narrow thrusting spear with pearl core.
- Kelp Lash: braided kelp whip with wet tendrils. Crafted.
- Mud-Saw Hatchet: serrated mud-caked hatchet. Crafted.
- Ooze Hammer: short two-hand maul with pressure blisters. Crafted.
- Brine Falx: inward-curved ceremonial blade.
- Eelbone Saber: pale hooked saber with translucent grain.
- Ruin Breaker: blocky ruin-hammer, broken glyphs, chain wrap.
- Temple Harrow: forked sacrificial polearm.
- Jetty Reaper: long salvage scythe with wharf bolts.
- Black Pearl Axe: dense pearl-veined execution axe.
- Newgame+ Abyss Halberd: royal black-metal halberd with breathing light seams.

### Projectile And Throwable Weapons

- Throwing Knives: fan-balanced wet steel shards.
- Mudglass Darts: brittle transparent darts with murk-tint cores.
- Harpoon Coil: compact reel launcher with hooked shots.
- Molotov Brine Flask: glass ampoule with luminous fuel and rag fuse. Crafted.
- Dust Seed Pod: burst pod that throws fungal opacity and dry spores. Crafted.
- Pearl Bolt Caster: shrine-forged launcher using pearl pressure bolts.
- Newgame+ Eclipse Launcher: ceremonial artillery tube with moon-slit vents.

### Weapon Animation Support

- Each melee weapon requires idle carry, light wind-up, light impact, heavy wind-up, heavy impact, block pose compatibility, and aerial silhouette pass.
- Each projectile requires aim pose, release frame, projectile silhouette, impact burst, and spent-state pickup icon.

## Armor Set Visual Asset Specification

All armor sets must be authored as eight swappable pieces:

- Upper Right Arm
- Lower Right Arm
- Upper Left Arm
- Lower Left Arm
- Upper Right Leg
- Lower Right Leg
- Upper Left Leg
- Lower Left Leg

Each set also needs a chest-torso paint guide, waist drape guide, back silhouette callout, hand-fin compatibility note, and alternate wetness pass.

- Shore Rag Harness: beach-cast cloth, rope, shell tabs.
- Dockworker Saltmail: chain patches, netting, shoulder hooks.
- Kelp-Wrap Strider: green-black wraps, reed plates, high mobility. Crafted.
- Mudplate Forager: hand-packed mud armor over wicker frames. Crafted.
- Pearl-Lashed Raider: pearl cords, rib plates, raider fins. Crafted.
- Ooze-Forged Pilgrim: glossy black ritual plates, spore cloth. Crafted.
- Brackish Duelist Rig: slim dueling coat, guarded forearms.
- Murk Templar Shell: shrine knight shell plates, brass rivets.
- Nightgaunt Veilweave: layered membranes, dark aerodynamic drape.
- Star-Spawn Pressure Suit: dense pressure ribs and vent chimneys.
- Cult Tide Mantle: ceremonial cloak, harpoon belts, prayer tags.
- Basalt Canopy Guard: blocky plated guardian silhouette.
- Abyss Prince Husk: boss-derived royal shell remains.
- Newgame+ Eclipse Regalia: final reward set, pearl-black ceremonial armor with eclipse seams.

## Pickups, Shelters, And Interactive World Objects

- Throwing knife pile: 3 presentation variants.
- Brine flask cache: intact, cracked, ignited variants.
- Seed pod bundle: dry, mature, ruptured variants.
- Brine salt cluster: loose crystals, ritual bowl, pearl-frost clump variants.
- MurkShelter architecture set:
  - distant silhouette.
  - mid-range exterior.
  - activated pearl beacon.
  - interior menu backdrop.
  - upgrade resonance flare.
  - fast-travel activation ring.
  - save-memory pulse.

## Environment Asset Stack From Smallest To Largest

### Micro Props

- tide pebbles
- shell shards
- fish bones
- barnacle crust decals
- eel slime streak decals
- fungal caps cluster
- rope knots
- wet leaves scatter
- salt crystals
- blood-in-water ripple decals

### Existing Core Prop Sheet Targets

- twisted cedar tree
- mangrove root cluster
- black rock
- tidepool stone
- ruined wharf post
- fog lamp
- barnacled shrine
- fishing crate
- driftwood arch
- fungus stump
- vine gate
- gravestone
- skull totem
- broken skiff
- eel basket
- rope coil
- wet fern cluster
- dead coral
- standing stone
- tide altar
- fungus boulder
- lantern pole
- rib cage ruin
- ritual obelisk

### Medium Structures

- collapsed dock span
- flooded watch hut
- shrine bridge segment
- fungus-choked fence line
- ritual boat cradle
- eel smoke kiln
- half-sunk chapel room
- coral ossuary mound

### Large Landmarks

- drowned village street
- black basalt ridge
- fungal grove basin
- tidal caverns entrance
- central murk marsh
- cyclopean seal temple
- boss crown terrace
- storm shore arrival beach

### Atmospheric Layers

- ground fog low
- mid-canopy fog ribbons
- rain sheets near camera
- hanging spores
- pearl motes
- swamp flies
- temple light shafts
- water reflection streak bands

## HUD, Codex, And UI Asset Needs

- shrine menu panel skin
- brine salt currency icon
- throwing knife, flask, seed pod item icons
- weapon family icons for all 23 weapons
- armor set crests for all 14 sets
- discovery and codex portrait frames for all enemies and bosses
- focus reticle states: neutral, locked, staggered, airborne, boss.
- resonance bars: moisture, stamina, vitality, breathing sync.
- fast-travel node map symbols for all MurkShelters.

## Audio Specification

### Combat And Interaction One-Shots

- player locomotion per surface: black sand, wet wood, basalt, shrine stone, muck, shallow water.
- player exertion set: inhale, exhale, jump, land, hurt, heavy hurt, heal, parry, block, dodge, death.
- weapon impacts by family: blade flesh, blade shell, blunt flesh, blunt stone, polearm stab, thrown knife hit, flask shatter, fire bloom, seed pod burst, bolt impact.
- enemy vocals: idle, alert, attack, hurt, death for each of the 8 field enemy types.
- boss vocals: phase start, special telegraph, stagger, enraged loop, death for each boss.
- shrine audio: dormant hum, discovery ping, activation bloom, heal bed, save chime, upgrade surge, travel swell.
- pickup audio: knife gather, flask pickup, seed gather, salt collect.

### Fade-Compatible Atmospheric Soundscapes

- Arrival Shore: surf roar, rigging knock, low gull cries, black-sand hiss, distant thunder.
- Drowned Village: hollow wood creak, waterlogged room tone, chain sway, far chanting.
- Fungal Grove: wet insect bed, spore puffs, bioluminescent fizz, muffled drips.
- Basalt Ridge: exposed wind, grit skitter, cliff water drops, stone resonance.
- Murk Marsh: low bubble churn, eel splash, reed friction, sub-bass swamp pressure.
- Tidal Caverns: multi-tap drips, enclosed surf, shell clatter, deep cave moan.
- Temple Approaches: ritual hum, pressure vents, distant drums, pearl tone glissandos.
- Boss Crown: storm-bed rumble, low ceremonial horn, body-scale wind tear, ritual fire hiss.

### Music Tracks And Stems

- Title: 5 stems. Drone, bowed metal, bass heartbeat, wet percussion, pearl choir.
- Exploration Low Threat: 6 stems. Bass drone, muted hand drum, glass harmonics, water taps, low brass swell, spore shimmer.
- Exploration High Threat: add pulse percussion and dissonant breath choir.
- Shrine Safe State: stripped 4-stem arrangement with slow pearl pulses.
- Seal Hunt Combat: 7 stems. Percussion, bass, hiss strings, metal impacts, chant fragments, air pressure pad, emergency rhythm.
- Boss Duo Phase 1: 6 stems.
- Boss Duo Phase 2: 8 stems with added ritual brass and high percussion.
- Boss Duo Phase 3: 9 stems with broken meter stress layer.
- Victory: 4 stems, exhausted uplift without full tonal release.

## ORBdimensionView Translation Rules

- Use authored foot anchors as world contact points. No collision or depth ordering should be computed from sprite bounds alone.
- Split every character into depth bands: feet, shins, torso, head, carried gear, overhead effects.
- Treat pseudo-height as authored metadata, not inferred transparency.
- Props need base polygons for collision and separate visual overhang polygons for canopy, arches, hooks, and shrine fins.
- Large landmarks need traversal masks plus occlusion silhouettes so the player can pass behind upper foliage or arch elements while keeping exact ground collision.
- Atmospherics should stack in three planes: foreground veil, gameplay plane, far-depth body.
- Light shafts and fog volumes should never hide active enemy telegraphs or pickups at the same gameplay depth.
- Recommended metadata per asset:
  - `pivot_base_x`, `pivot_base_y`
  - `visual_height`
  - `depth_band_count`
  - `shadow_radius`
  - `occlusion_class`
  - `collision_proxy`
  - `hurtbox_proxy`
  - `pickup_radius` or `interact_radius` where applicable

## ORBKinetics Mapping Rules

- Exact collision should resolve against authored gameplay hulls, not painted silhouette fringe.
- Every animation that changes stance must publish updated hurtbox and hurt-footprint metadata.
- Aerial attacks require separate vertical occupancy lanes so plunge attacks can feel elevated without breaking 2D collision clarity.
- Pickups use circular interact proxies; shelters use capsule interact proxies; enemies use hull plus hurtbox sets.
- Weapons require arc metadata:
  - horizontal reach
  - vertical threat band
  - startup
  - active
  - recovery
  - stagger impulse
- Landmarks require surface tags:
  - slick
  - shallow_water
  - loose_rock
  - shrine_stone
  - fungal_soft
  - wood_decay
- Boss arenas need authored anti-snag collision strips around major pillars and stairs.

## ORBGlue Gameplay Binding Rules

- Discovery, codex entries, audio reveals, and lighting accents should all unlock from the same discovery event.
- Shrine state should simultaneously control save availability, fast-travel availability, nearby light color, ambient mix, and codex note injection.
- Weapon unlocks should trigger equipment UI highlight, codex update, and a unique pickup or forge sound.
- Armor unlocks should drive defense values, movement feel descriptors, and visible limb-piece swaps.
- Brine salt should bind to drop VFX, pickup SFX, shrine UI counters, and unlock notification copy from a single progression event.
- Boss phase changes should publish a unified state packet to animation, lighting, music stem intensity, projectile frequency, and HUD warning logic.

## Recraft Pass Guidance

- Use the current asset sheets in `ORBEngine/assets/innsmouth_island` as reference controls when working in the Recraft UI or any image-conditioned workflow.
- Use the generated manifest in `drIpTECH/ReCraftGenerationStreamline/innsmouth_island_master_manifest.json` for the text prompt base. The local manifest runner in this repo is text-first, so image-control fields are documented here but not yet automated in the JSON schema.
- Favor atlas generation over isolated single assets for cohesion: one pass per family, then derive crop-ready pieces.
- Keep every prompt explicit about gameplay readability, wet material breakup, silhouette uniqueness, and anchor clarity.

## Deliverable Checklist

- Player master sheet
- Enemy field roster sheet
- Enemy action atlas
- Boss duo action atlas
- Melee weapon atlas
- Projectile and throwable atlas
- Armor set atlas with eight limb pieces per set
- Pickup and MurkShelter atlas
- Micro prop atlas
- Core prop atlas
- Landmark panorama sheet
- Biome ground and decal sheet
- HUD and icon atlas
- Fog, light, ooze, and impact FX atlas
- Audio implementation list with one-shots, atmospheres, and music stems
- ORBdimensionView, ORBKinetics, and ORBGlue integration notes