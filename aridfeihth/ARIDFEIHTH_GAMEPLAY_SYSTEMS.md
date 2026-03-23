# Aridfeihth Gameplay Systems

Date: 2026-03-13

This document converts the earlier research foundation into an implementation-facing gameplay model for `aridfeihth`.

It keeps the structural lessons that made the reference games strong while moving the actual rules, fiction, pacing, and interaction language into an original direction built around `SimIAM` rescue, `bond tension`, EgoSphere-guided encounter reading, and `godAI`-paced world pressure.

## Experience Target

The desired feel is an exploration action RPG where each room asks three questions at once:

- Can the player read the space fast enough?
- Can the current SimIAM roster answer the local ecology?
- Can the player control bond tension before the situation spirals?

The tone should be pressure-and-care, not corruption-and-harvest.

## Full Loop

The game loop should run in five repeating layers.

### 1. Refuge Layer

The player returns to a refuge to:

- rest and reduce `bond tension`
- reassign Burst, Chorus, Crest, and Key pets
- hatch or rehabilitate newly recovered SimIAM creatures
- convert salvage into gear upgrades or habitat improvements
- gather route rumors and rescue leads

This is the calm planning layer.

### 2. Sortie Layer

The player enters a hostile region with a chosen pet loadout and a specific route hypothesis.

That route hypothesis may be:

- find a missing SimIAM
- reach a sealed junction
- recover workshop salvage
- break a boss lock

This is the preparation payoff layer.

### 3. Encounter Layer

The player reads side-view combat rooms with a hybrid kit:

- modest melee competence
- evasive movement
- one active Burst pet
- one toggleable Chorus pet
- passive Crest support
- progression-gating Key verbs

This is the minute-to-minute action layer.

### 4. Rescue Layer

When an area stabilizes, the player can rescue or pacify a SimIAM instead of absorbing a power drop.

Rescue actions can require:

- room clearance
- environmental setup
- staying inside a protective Chorus field
- bringing the right bait, tool, or Key pet

This is the emotional and progression layer.

### 5. Reconfiguration Layer

The new SimIAM shifts the build and makes older rooms newly solvable or newly profitable.

This is what keeps the map from becoming one-directional.

## Core Systems

## Player Baseline

The protagonist should never feel powerless, but also should never be so complete that the SimIAM roster becomes optional.

Baseline verbs:

- three-hit melee string with reliable cancel windows
- slide or dodge burst for spacing correction
- upward vault or low-air correction
- quick command input for Burst pets
- Chorus toggle
- bond weave finisher when charge is full

The melee kit exists to hold a fight together. The pets create the actual build identity.

## SimIAM Lanes

### Burst

Burst pets are short-cooldown tactical commands.

Combat purpose:

- break posture
- tag weak points
- root or displace targets
- punish enemy recovery windows

Design rule:

Burst actions should be strong enough to change decisions, but short enough that the player still has to participate directly.

### Chorus

Chorus pets are held-state companions that alter the room over time.

Combat purpose:

- shape projectile behavior
- soften falling or knockback
- widen perfect-dodge windows
- reveal invisible hazards or targets

Design rule:

Every Chorus pet must provide a visible advantage and a visible cost. The cost is usually bond-tension accumulation, noise, attraction, or reduced speed.

### Crest

Crest pets are passive build shapers.

Combat purpose:

- resistance and recovery tuning
- salvage economy modifiers
- terrain adaptation
- status translation into advantages

Design rule:

Crest pets should make a build lean in a direction without locking it into one answer.

### Key

Key pets open authored route verbs.

Examples:

- reflective slip through fissures
- bridge threading across gaps
- mineral barricade breach
- water clock retuning

Design rule:

Key pets must unlock traversal in physically readable ways. Avoid menu-only permission checks.

## Combat Logic

Combat should be implemented around posture, interruption, and bond pressure instead of only raw damage races.

### Core Meters

- Health: survival margin.
- Posture: enemy break state. Burst actions and clean melee timing should crush posture faster than raw chipping.
- Bond Tension: shared stress across the active pet relationship.
- Bond Weave Charge: earned through disciplined play, then spent on a native boss-resolution action.

### Tension Rules

Bond tension increases when:

- a Burst pet is overused
- a Chorus pet stays active too long
- the player takes direct hits
- the region ecology naturally frightens the active roster

Bond tension decreases when:

- the player lands perfect dodges
- a room is stabilized
- the player rests at refuge nodes
- the active roster contains strong affinity matches

At high tension, pets should hesitate, commands should lengthen slightly, and some routes should become unsafe until the player regains control.

### Encounter Rhythm

The intended loop inside a single fight is:

1. Probe the enemy and learn its reach.
2. Use melee or environment pressure to create a posture opening.
3. Spend a Burst command or Chorus window at the right moment.
4. Dodge or reposition before retaliation.
5. Rebuild tempo and push toward a bond weave.

That rhythm keeps pets central without turning the game into passive auto-combat.

## Boss Logic

Bosses should not end with a detached gimmick.

They should move through three phases:

### 1. Pattern Read

The player learns the arena and the boss ecology.

### 2. Stabilization

The player uses the right SimIAM combination to expose the boss by breaking armor, pinning limbs, redirecting pressure, or calming an environmental hazard.

### 3. Bond Weave

When the boss enters a vulnerable state, the player executes a short finisher that still uses the main control language.

Rules for bond weaves:

- no tracing
- no detached touchscreen-style interlude
- no separate minigame grammar
- keep the finisher about room control, timing, and active pets

## EgoSphere And godAI

## EgoSphere Role

EgoSphere should read encounter context rather than acting as a black-box replacement for combat design.

Use it for:

- focus target selection
- encounter pressure reading
- suggested combat style shifts such as `probe`, `commit`, `stabilize`, or `dodge_counter`
- long-form rivalry memory for recurring enemies or region handlers later in development

That keeps EgoSphere as a systems intelligence layer.

## godAI Role

`godAI` should act as the world-pressure conductor above individual actors.

Use it for:

- omen pacing
- mercy windows when the player is near collapse
- enemy pressure scaling within authored bounds
- rescue calm states after room stabilization
- region-wide event cadence during longer expeditions

That keeps `godAI` from becoming pure cheating difficulty inflation.

## IllusionCanvasInteractive Runtime Role

IllusionCanvasInteractive should express the game with three presentation rules:

- side-view combat remains readable first
- ORB-style parallax and floor staging create depth without obscuring collision truth
- DoENGINE-style manifests keep the content intake deterministic and automation-friendly

The runtime does not need to replace ORBEngine or DoENGINE. It needs to stand between them as the project-specific hybrid layer.

## Vertical Slice Structure

The initial vertical slice should prove:

- refuge rest and loadout clarity
- one Burst pet in combat
- one Chorus pet cost-benefit loop
- one Crest support effect
- two Key-pet route unlocks
- one miniboss-quality bond weave payoff

That is enough to validate the full system direction without needing the entire world first.

## Implemented Slice Notes

The current IllusionCanvasInteractive prototype now expresses this as a concrete route:

- `Latchspire Refuge` for rest and retuning
- `Choir Stair` for dodge and Chorus onboarding under pressure
- `Glasswind Causeway` for the `Mirror Newt` rescue
- `Mirror Cistern` for the `Latch Spider` rescue
- `Scribe Gullet` for a mid-run bond reset and pacing tutorial
- `Ossuary Switchyard` as the pressure gate into the final chamber
- `Ember Nave` as a boss room where the player must root the target, sustain the active Chorus, and complete a bond weave under authored conditions
- `Ram Gate` for the post-boss `Salt Ram` route proof
- `Tutorial Sanctum` as the demo-end refuge confirming the full introductory loop
- `Reliquary Bazaar` as the first post-tutorial widening room using the market shell language
- `Atlas Choir` as a map-framed overlook that turns the solved tutorial into a wider world promise

That gives the prototype a real end-state instead of stopping at route theory.

It also means the current demo now touches, in introductory form:

- refuge rest
- movement and dodge timing
- Burst commands
- Chorus upkeep cost
- Crest-style passive support awareness
- rescue-state progression
- key-verb route locks
- clear-gated exits
- boss-state bond weave resolution
- post-boss key payoff and safe return
- a post-tutorial handoff into future trade and world-map facing systems

The most recent authoring pass also binds the Recraft-generated UI shells directly into those authored beats:

- refuge and sanctum moments use sanctuary/save shell language
- rescue and codex teaching beats now use authored dialogue and codex shell moments
- the switchyard and boss lessons now use distinct quest and death-shell framing instead of a single generic tutorial prompt

That makes the vertical slice read more like a real game route and less like a debug harness with text overlaid on it.
