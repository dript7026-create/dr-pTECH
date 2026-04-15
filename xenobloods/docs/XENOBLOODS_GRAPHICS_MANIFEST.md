# XenoBloods Graphics Asset Manifest

## Manifest Standard

This manifest now serves two connected tracks:

1. a 2D-first prototype production path driven by sprite sheets, UI atlases, timing maps, and JumpClip-linked asset bundles
2. a preserved high-end 3D/CGI production-planning path for worldpack studies, material lookdev, and long-range presentation targets

The live prototype should assume 2D-facing delivery first. The 3D asset inventory remains valid and intentionally preserved for the retained DoENGINE branch.

For each asset, the manifest defines:

- asset id
- category
- target resolution or texture budget
- state coverage
- frame or variation count
- pixel-detail priorities for paint-over and texture work
- plane/lifecycle relationships

## Lifecycle Coverage Rule

Every major living asset family must define state variants for:

1. `gourd_infant`
2. `landborne`
3. `etheric`

Where required, additional plane variants include:

- `up_aspected`
- `low_aspected`

## Player Character Set

### XB_CHAR_PLAYER_BASE
- category: hero character
- mesh budget: 120k hero LOD0
- texture set: 4 x 4k (skin, cloth/armor, blood mask, material effects)
- lifecycle states: gourd_infant, landborne, etheric, up_aspected, low_aspected
- pixel-detail priorities:
  - iris striation readable at 64 px face crop
  - blood vessel normal detail readable in 512 px torso crop
  - ritual seam stitching readable in 256 px forearm crop
  - ether crackle mask readable in 128 px silhouette crop
- notes:
  - landborne silhouette must stay readable under heavy blood saturation
  - etheric state removes flesh-density occlusion and adds flowing filament energy
  - current 2D prototype preview target: a humanoid botanical spider read for Ishtasha, keeping a human torso and hooded ritual identity while secondary spider limbs read as grown vine architecture rather than pure arachnid anatomy

### XB_CHAR_PLAYER_GOURD_INFANT
- category: lifecycle variant
- mesh budget: 40k
- texture set: 2 x 2k
- animation states: curl, pulse, strain_left, strain_right, shell_kick, rupture_burst, emerge_collapse
- pixel-detail priorities:
  - translucent amniotic membrane veining at 128 px crop
  - shell fracture edge detail at 64 px crop
  - eye glow readable through fluid haze

### XB_CHAR_PLAYER_ETHERIC_CURRENT
- category: lifecycle variant
- mesh budget: 28k plus GPU ribbons
- texture set: 1 x 2k flow mask, 1 x 2k emissive atlas
- shader layers: directional energy flow, memory motes, shrine tether lines
- pixel-detail priorities:
  - edge breakup readable against dark and bright backgrounds
  - energy core shape identifiable in 48 px gameplay silhouette

## Core NPC Families

### XB_NPC_GOURD_KEEPER
- category: service NPC
- states: landborne, etheric
- texture set: 2 x 2k
- unique props: cradle harness, siphon staff, blood measure beads
- pixel-detail priorities:
  - bead count readable at kiosk distance
  - gourd stains and seal wax need hand-painted asymmetry

### XB_NPC_SOUL_SHRINE_ATTENDANT
- category: shrine NPC
- states: landborne, up_aspected, etheric
- texture set: 3 x 2k
- notes:
  - upper-plane threads must read cleaner and more geometric than Land fabrics

### XB_NPC_LOW_MOURNER
- category: Low inhabitant
- states: low_aspected, etheric
- texture set: 2 x 2k
- pixel-detail priorities:
  - grief tears, silt trails, and identity blur masks

## Enemy Schism Families

### Rendline Family

#### XB_EN_RND_SCOUT
- category: enemy basic
- mesh budget: 55k
- texture set: 2 x 2k
- outfit variants: hooked knives, tendon wire, split buckler
- states: landborne, low_aspected, etheric death burst
- animation count: 78 clips
- pixel-detail priorities:
  - tendon wire catchlights
  - tooth blood occlusion
  - heel spike silhouettes at 32 px gameplay distance
  - current 2D prototype preview target: small scarab-child silhouettes in hoods with plague doctor masks, preserving swarm readability and child-scale menace without flattening them into comic relief

#### XB_EN_RND_CAPTAIN
- category: enemy elite
- mesh budget: 80k
- texture set: 3 x 2k
- outfit variants: execution sabre, gore banner, lunging greaves
- states: landborne, up_aspected, etheric death burst

### Lattice Family

#### XB_EN_LAT_WARD
- category: enemy basic
- mesh budget: 62k
- texture set: 2 x 2k
- outfit variants: tower shield, relay pike, oath mask
- states: landborne, up_aspected, etheric
- pixel-detail priorities:
  - formation glyph readability at 64 px shield crop
  - relay cable glow map clear under rain

#### XB_EN_LAT_HERALD
- category: enemy support elite
- mesh budget: 74k
- texture set: 3 x 2k
- unique effect: linked shield ribbons between squad members

### Mirecast Family

#### XB_EN_MIR_SIBYL
- category: caster enemy
- mesh budget: 58k
- texture set: 2 x 2k plus 1 x 1k curse decal atlas
- states: landborne, low_aspected, etheric
- pixel-detail priorities:
  - mouth stitch normals
  - palm sigil emissive edges
  - curse puddle decal breakup by 256 px tile

#### XB_EN_MIR_BASIN_PRIEST
- category: elite caster
- mesh budget: 82k
- texture set: 3 x 2k
- props: amniotic censer, basin bell, rot scrolls

### Idolwrought Family

#### XB_EN_IDL_SENTINEL
- category: heavy enemy
- mesh budget: 90k
- texture set: 3 x 2k
- material mix: stone shell, wet brass joints, shrine wax packing
- states: landbound construct, ether fracture state
- pixel-detail priorities:
  - crack depth map at 128 px crop
  - wax seam drips

#### XB_EN_IDL_BELL_TORSO
- category: heavy elite
- mesh budget: 110k
- texture set: 1 x 4k body, 1 x 2k bell, 1 x 2k damage mask

### Mirrorblood Family

#### XB_EN_MIRROR_RIVAL_A
- category: adaptive rival
- mesh budget: 95k
- texture set: 3 x 2k plus 1 x 1k pattern response mask
- states: landborne, etheric duel afterimage, low_aspected corruption variant
- pixel-detail priorities:
  - mirrored costume details must echo but not duplicate player silhouette
  - reaction mask should flare on repeated player habit punish windows

#### XB_EN_MIRROR_RIVAL_B
- category: adaptive rival alternate
- mesh budget: 95k
- texture set: same as rival A

## Boss Asset Inventory

### XB_BOSS_NOMA_SHELL_WARDEN
- category: chapter boss
- mesh budget: 180k
- texture set: 1 x 4k body, 1 x 4k shell, 1 x 2k fracture mask, 1 x 2k blood fluid mask
- lifecycle relation: controls gourd birth violence
- key states: dormant, shell closed, shell cracked, rupture frenzy, ether collapse
- pixel-detail priorities:
  - fracture propagation atlas by 512 px shell quadrant
  - membrane translucency under backlight

### XB_BOSS_LAHGROID_HIEROPHANT
- category: prototype boss direction
- 2D preview target:
  - reptilian serpent feathered manticore humanoid
  - robe silhouette with readable torso and tail separation
  - lantern on a chain as the primary channeling prop
  - one cross and one cannon as asymmetrical carried weapons
  - ordered cross-pattern substrata of hovering drones as the boss support read
- pixel-detail priorities:
  - feathered neck crest readability at 64 px silhouette scale
  - lantern-chain arc clarity during magic windup frames
  - drone ordering must read as deliberate sacred geometry rather than random floating clutter

### XB_BOSS_OPAL_TETRARCH
- category: late-game boss
- mesh budget: 190k
- texture set: 4 x 4k plus 1 x 2k opal caustic mask
- plane relation: Up primary, ether bleed, Land intrusion
- pixel-detail priorities:
  - opal nerve shimmer at grazing angles
  - facial law-script microetching readable in photo mode

### XB_BOSS_MOURNING_ENGINE_IX
- category: Low boss
- mesh budget: 210k
- texture set: 4 x 4k plus 2 x 2k confusion overlays
- plane relation: Low primary

## Plane Environment Sets

### Land Set

#### XB_ENV_LAND_VEINMARKET_STREET_KIT
- category: modular environment kit
- pieces: 96
- texel density target: 512 px per meter hero surfaces, 256 px per meter secondary
- materials: blood brick, oil cloth, shrine bronze, wet stone, market canvas
- pixel-detail priorities:
  - blood channel trim sheets
  - coin scale readability
  - billboard script legibility in 256 px crop

#### XB_ENV_LAND_GOURD_FORGE
- category: landmark environment
- pieces: 34
- unique props: cradle vats, glass womb tubes, siphon presses, shell racks

### Up Set

#### XB_ENV_UP_GRAMATOS_HALL
- category: modular environment kit
- pieces: 72
- materials: radiant marble, vow gold, etched ceramic, disciplined light glass
- pixel-detail priorities:
  - law-script edge sharpness
  - shadow discipline on fluted columns

#### XB_ENV_UP_TETRARCH_BRIDGE
- category: landmark environment
- pieces: 21
- special shaders: luminous notation stream, verdict rain

### Low Set

#### XB_ENV_LOW_SORROW_DELTA
- category: modular environment kit
- pieces: 88
- materials: mud glass, silt membrane, grief moss, drowned bone, black water
- pixel-detail priorities:
  - soft silhouette breakup under fog
  - confusion smear decals

#### XB_ENV_LOW_MOURN_CHANNEL
- category: landmark environment
- pieces: 27
- special shaders: memory drift, submerged face ripples

## Soul Shrine Set

### XB_ENV_SHRINE_CORE
- category: critical gameplay structure
- model variants: 9
- texture set: 2 x 4k per major shrine, 2 x 2k per minor shrine
- interaction states: dormant, listening, blood-fed, ether-open, rebirth-active, low-tainted, up-sanctified
- pixel-detail priorities:
  - soul knot emissive pulses
  - shrine basin blood fill readability from top-down camera glance

### XB_PROP_AMNIOTIC_GOURD_SERIES
- category: critical interactive props
- variants: 18
- states: whole, filled, half-filled, cracked, mended, infant-active, ether-empty
- texture budget: 1 x 1k to 1 x 2k each depending on rarity
- pixel-detail priorities:
  - glass depth coloration
  - fluid meniscus
  - shell-label iconography

## Weapons and Equipment

### Blood Blades
- asset ids: XB_WPN_BLD_01 through XB_WPN_BLD_08
- texture budget: 2 x 2k each
- state masks: clean, blooded, overheated, ether-lit

### Verdict Polearms
- asset ids: XB_WPN_VDT_01 through XB_WPN_VDT_06
- texture budget: 2 x 2k each
- pixel priorities: edge law script, haft wear, resonant ring emitters

### Gourd Hammers
- asset ids: XB_WPN_GRD_01 through XB_WPN_GRD_05
- texture budget: 2 x 2k each
- pixel priorities: shell crack propagation, fluid chamber fill level

### Ether Bows
- asset ids: XB_WPN_ETH_01 through XB_WPN_ETH_05
- texture budget: 2 x 2k each plus 1 x 1k projectile ribbon atlas

### Sibeline Wands
- asset ids: XB_WPN_SIB_01 through XB_WPN_SIB_07
- texture budget: 2 x 2k each
- pixel priorities: tonal rune notches, resonance caps, emission choreography markers

## FX Library

### Blood FX
- XB_FX_BLOOD_SPILL_GROUND
- XB_FX_BLOOD_RECLAIM_SWIRL
- XB_FX_BLOOD_BURN_AURA
- XB_FX_BLOOD_MARK_RUPTURE
- atlas target: 4 x 2k flipbook sheets

### Ether FX
- XB_FX_ETHER_STREAM
- XB_FX_SHRINE_EXIT_RIBBON
- XB_FX_SOUL_NAV_SPARKS
- atlas target: 3 x 2k plus shader flow maps

### Plane-Specific FX
- Up: verdict rain, law sigil fractures, harmonic lensing
- Land: blood mist, forge sparks, wet grit impacts
- Low: grief fog, confusion halos, drowned whisper ripples

## UI Asset Set

### HUD
- health bar atlas: 2048 x 512
- stamina bar atlas: 2048 x 512
- blood reserve gauge: 1024 x 1024 circular atlas
- acuity meter: 1024 x 512
- gourd inventory strip: 2048 x 512

### Menus
- shrine routing map
- blood banking panel
- rebirth rupture prompt icons
- schism ledger and weakness history card frames

Pixel-detail rules:

- all HUD numerals readable at 1080p and 1440p
- blood reserve warnings must hold contrast over bright and dark scenes
- shrine routing glyphs must stay legible at 80 px icon size

## Cinematic Asset Set

### Pre-render support plates
- chapter opener skies
- low-plane memory smears
- upper-plane glyph storms

### In-engine cinematics
- hero close facial rigs
- boss intro cloth and hair grooms
- gourd rupture camera-only shell sim meshes

## Asset Count Summary

- hero and lifecycle variants: 3 primary forms + 2 plane-aspected overlays
- core NPCs: 12 named variants
- common enemies: 20
- elite enemies: 12
- adaptive rivals: 4
- bosses: 8
- weapon assets: 31
- shrine variants: 9 major, 12 minor
- gourd props: 18
- modular environment pieces: approximately 338
- major VFX families: 14
- HUD/menu atlases: 11

## Approval Rule

No character, enemy, or shrine asset is approved unless its lifecycle and plane-state readability survives all of the following:

1. full-resolution beauty render
2. gameplay camera mid-distance silhouette check
3. heavy blood saturation state
4. low-light fog check
5. ether-overlay readability pass