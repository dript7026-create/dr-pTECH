# XenoBloods Game Design Document

## High Concept

XenoBloods is a single-player real-time action game for PC built around blood economy, metaphysical rebirth, and adaptive combat pressure.

The player lives across three planes of existence:

- `Up`: the radiant upper dominion beneath Gramatos, where the tetrarchs reside
- `Land`: mortal embodied life, where blood, flesh, memory, and ambition are fully bound together
- `Low`: the underworld of sorrow, confusion, grief, and collapsed identity

Between them lies the ether, a navigable state of pure energy reached through death or at soul shrines.

The player's lifecycle is not a simple respawn loop. Every death and every deliberate soul-shrine crossing re-enters the rebirth chain. To return to Land, the player first manifests as an infant sealed in an amniotic gourd and must struggle free into full embodied life again.

## Product Pillars

1. Real-time action that feels brutally intense but legible.
2. Blood as the center of economy, growth, stamina, healing, and cognition.
3. Three-plane metaphysics that matter mechanically, not only in lore.
4. Rebirth that is playable, risky, and emotionally charged.
5. Adaptive enemy pressure that studies weakness patterns without cheating.
6. High-end CGI presentation that remains within plausible production limits.

## Target Experience

- Platform: PC
- Camera: third-person action
- Length: 12 hours first clear
- Difficulty posture: aggressive but fair, approximately an 89% stress threshold rather than total overload
- Structure: authored campaign with adaptive encounter dressing and reinforcement routing

## World Cosmology

### Up

Up is the seat of law, mandate, and elevated design. The tetrarchs rule here under Gramatos, whose order shapes the upper grammar of existence.

Mechanical traits:

- clean geometry
- strong signal clarity
- difficult but readable enemies
- soul pressure favors order, precision, and vow-keeping

Typical hazards:

- radiant lances
- collapsing verdict bridges
- harmonic seals
- cognition taxes that punish panic decisions

### Land

Land is embodied life. Blood moves value, stamina, memory, hunger, and selfhood. Here, blood is everything:

- currency
- health reserve
- stamina charge
- acuity fuel
- growth medium

Land is where most combat, traversal, commerce, and factional conflict occur.

### Low

Low is the underworld of sorrow and confusion. Identity degrades here if not reinforced. Spatial logic is less stable, enemies are more emotionally contagious, and grief mutates perception.

Mechanical traits:

- unreliable footing and memory haze
- status confusion
- heavy punishment for greed and panic
- easier soul shedding, harder blood recovery

### Ether

Ether is not one of the three civic planes. It is the transit state between them, the field of pure energy, prayer, memory, and direction.

The player enters ether when:

- dying
- using a soul shrine
- crossing certain high-order gates

In ether, the player becomes pure energy and can navigate toward aligned anchors.

## Three Life-Form Lifecycle

XenoBloods uses a three-form lifecycle that spans the planes.

### Form 1: Gourd Infant

This is the larval rebirth form.

Triggers:

- entering Land from ether through a soul shrine
- returning after death

Characteristics:

- sealed inside an amniotic gourd
- nearly helpless movement
- vulnerable but spiritually dense
- must build rupture pressure to hatch into embodied life

Gameplay:

- short but active rebirth struggle sequence
- directional strain, pulse timing, and shell cracking
- danger if enemies or hostile fields reach the gourd before emergence

### Form 2: Landborne Vessel

This is the standard living form.

Characteristics:

- full combat toolkit
- full blood metabolism
- commerce, growth, crafting, and stamina all active
- can spend or spill blood tactically

Gameplay:

- core exploration and combat form
- uses weapons, shrines, gourds, and bloodcraft

### Form 3: Etheric Current

This is the pure-energy form.

Triggers:

- death
- soul-shrine traversal
- certain boss mechanics and upper-plane rites

Characteristics:

- no standard weapon use
- navigates shrines, currents, memory gates, and alignment paths
- can scout metaphysical topology
- cannot spend blood directly because blood is not actively embodied here

Gameplay:

- navigation through ether streams
- selecting descent anchor to Land, ascent anchor to Up, or drift-risk toward Low
- solving short energy-routing sequences

## Player Economy

### Blood

Blood is the primary universal resource in Land.

Uses:

- buy goods and rites
- fuel stamina recovery
- restore health
- sharpen mental acuity
- unlock blood growth upgrades
- empower weapon arts and ritual actions

Risks:

- spending too much blood reduces resilience
- losing blood lowers max performance
- low blood makes the player physically weaker and mentally less precise

### Mental Acuity

Mental acuity controls:

- lock-on stability
- parry clarity window
- ritual decoding speed
- resistance to confusion and fear fields

Mental acuity is partly derived from blood density. Thin blood means a dimmer mind.

### Amniotic Gourds

Amniotic gourds are both sacred and practical.

Uses:

- collect spilled blood from the field
- preserve blood outside the body
- incubate rebirth after death or shrine descent into Land
- carry special essence strains

Player verbs:

- decant blood into gourd
- refill from gourd
- stabilize a cracked gourd
- enter rebirth incubation

## Core Loop

1. Explore a hostile region of Land, Up, or Low.
2. Fight enemies and collect blood.
3. Spend blood on survival, growth, and equipment.
4. Reach a soul shrine or major anchor.
5. Choose to remain embodied, traverse planes, or bank blood in gourds.
6. Adapt to enemy paradigm shifts and new pressure patterns.
7. Survive boss gates and advance the world-state.

## Combat Design

### Combat Goals

- high responsiveness
- weighty melee
- readable ranged denial
- pressure systems that reward discipline rather than mash play
- strong encounter identity via enemy logic families

### Player Combat Resources

- health
- stamina
- blood reserve
- acuity
- rupture charge
- shrine charge

### Weapon Families

1. Blood blades
2. Verdict polearms
3. Gourd hammers
4. Ether bows
5. Sibeline wands

The wand line covers the user's requested "Sibelius wand" idea, translated into original setting language as a class of resonant ritual rods associated with tonal law, harmonic wounds, and energy shaping.

### Blood Actions

- blood burn: trade blood for immediate burst stamina
- blood veil: pay blood to dampen incoming ritual damage
- blood mark: spend blood to prime a target for juggle or rupture
- blood reclaim: vacuum spilled blood from the environment into a gourd or directly into the body

## Soul Shrines

Soul shrines are the metaphysical junctions of the whole game.

Functions:

- checkpoint
- plane transfer
- rebirth initiation
- blood banking
- memory review
- adaptive routing node

At a soul shrine, the player may:

- remain in current plane
- enter ether deliberately
- route toward Up, Land, or Low if conditions allow
- bank blood before dangerous travel

When routing into Land from ether, the player always returns as a gourd infant first. This keeps rebirth diegetic and playable.

## Enemy Paradigm Schisms

Enemy design revolves around schisms: distinct logic families with incompatible assumptions about range, timing, and pressure.

### Schism 1: Rendline

- close-range aggression
- short punish windows
- anti-hesitation

### Schism 2: Lattice

- formation combat
- linked defense logic
- denial geometry

### Schism 3: Mirecast

- delayed hazard creation
- curse pressure
- anti-positioning control

### Schism 4: Idolwrought

- heavy posture warfare
- false vulnerability traps
- slow lethal commitment

### Schism 5: Mirrorblood

- rival duelists that answer repeated player habits
- authored counterstyle logic based on saved performance tags

## Adaptive Enemy Patterning

XenoBloods does not use fake omniscient AI.

Instead, it uses a production-safe hybrid system:

1. authored behavior trees / action graphs
2. utility scoring per action
3. short-horizon memory inside fights
4. longer-profile tags across the campaign
5. director-controlled outfit and squad variation within strict limits

Allowed adaptation:

- choose between authored weapon kits
- bias aggression windows
- choose among telegraph clarity packages
- alter mixed-unit composition inside an encounter pool

Disallowed adaptation:

- reading player inputs directly
- inventing new attacks live
- infinite stat inflation
- impossible counters with no scoutability

## Campaign Structure

### Chapter 1: Gourdwake Breach

- tutorial through rebirth
- learn rupture struggle and first blood recovery
- boss: Shell Warden Noma

### Chapter 2: Veinmarket Mile

- economy chapter
- teaches blood spending versus banking
- schism emphasis: Rendline

### Chapter 3: Flood Archive of Lillypads

- introduces curse fields, drowned records, and buoyant traversal islands
- schism emphasis: Mirecast

### Chapter 4: Token Tong Causeway

- bridge district with blood toll economy and linked-defense guards
- schism emphasis: Lattice

### Chapter 5: Alibaba Furnace Ward

- industrial blood refineries and black-market gourd forges
- teaches risk-reward spending and reclaim routes

### Chapter 6: Opal Nervure Vault

- elegant crystalline district inspired by resilient opal surfaces and nervous, luminous curve language
- introduces acuity-focused cognition hazards

### Chapter 7: Gramatos Underscript

- first true Up incursion
- law-bound enemies, precise duel pacing, upper-plane judgment hazards

### Chapter 8: Sorrow Delta

- deep Low descent
- confusion mechanics, unreliable paths, grief manifestations

### Chapter 9: Tetrarch Fracture

- split-plane traversal
- repeated shrine routing and cross-plane consequence stacking

### Chapter 10: Oshin Ishtasha Tribunal

- final ascent and convergent judgment
- bosses test every learned mastery axis
- ending resolves blood, identity, and plane allegiance

## Boss Design Rules

Every major boss must embody one clear mastery demand and one corruption twist.

Examples:

- Shell Warden Noma: rebirth timing plus shell break pressure
- Auditor Sal Gramatos: precision, vow windows, and false-rhythm punishments
- Mourning Engine Ix: confusion resistance and blood reserve management
- Tetrarch of the Opal Nerve: acuity control and multi-plane punish routing

## Progression

### Growth Tracks

1. blood density
2. stamina refinement
3. acuity clarity
4. gourd resilience
5. ether control
6. weapon specialization

### Shrinkage State

If blood thins too far:

- lower stamina ceiling
- reduced healing efficiency
- blurrier parry timing
- weaker ritual focus

This makes blood management emotionally and mechanically central.

## Art Direction

Visual direction:

- fully real-time CGI
- dense material contrast between wet flesh, ritual metal, opal nerve surfaces, soot, and ether light
- Land feels organic, economic, and urgent
- Up feels severe, luminous, and mathematically beautiful
- Low feels flooded, grieving, and memory-blurred

Character design rule:

Every major entity should have readable states for:

- gourd infancy
- embodied life
- etheric or post-death transition

## Audio Direction

- blood pulse bass layers for low-resource danger
- ritual chimes and vowel choirs for Up
- broken sob-tone drones and submerged textures for Low
- percussion that tightens with enemy schism overlap

## Technology Direction

Target engine class:

- Unreal Engine 5.4+ or comparable internal renderer

Target features:

- high-end real-time character rendering
- motion matching or pose-search locomotion
- selective deformation tech for hero assets
- strong volumetrics and hybrid GI
- authored physics interaction rather than global simulation overload

## Production Boundaries

This design pushes very hard but stays inside plausible production reality.

Not promised in this pass:

- a finished engine implementation
- universal procedural world generation
- self-writing infinite AI
- unbounded content sprawl

Promised foundation:

- strong cosmology
- hard mechanical identity
- robust blood economy
- adaptive authored encounters
- clean path to a vertical slice and then a full campaign

## Vertical Slice Requirements

The first playable slice should include:

1. one Land district
2. one soul shrine
3. one rebirth sequence
4. one Up incursion room
5. one Low corruption room
6. two enemy schism families
7. one mini-boss
8. complete blood and gourd loops

## Success Condition

XenoBloods succeeds when the player feels that:

- blood matters every second
- death changes state instead of simply resetting position
- every plane has different metaphysical and combat logic
- soul shrines are sacred, strategic, and dangerous
- enemies become smarter in authored ways that still feel fair
- the whole campaign feels like one cohesive blood-and-soul ecology rather than disconnected levels