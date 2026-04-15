# Xenobloods Via Pocode

## Purpose

Use the existing Pocode campaign compiler and adaptive learning runtime as a game-balancing framework for Xenobloods.

Instead of teaching syntax, Pocode teaches combat literacy. Instead of lessons about variables or loops, it generates encounter sequences that train the player to read enemy intent, pressure windows, weapon cadence, stance shifts, and boss-specific punish routes.

The point is not to turn Xenobloods into an educational app. The point is to use Pocode's adaptive structure to keep a high-stress action game readable, fair, and progressively demanding across a full 12-hour single-player campaign.

## Core Translation

Pocode already knows how to do these things:

- break a large goal into dependency-ordered units
- measure mistakes per concept
- add reinforcement loops without flattening the whole campaign
- raise or lower obscurity and pacing based on player performance
- insert restorative nodes that reduce upcoming pressure without deleting challenge

Xenobloods should reuse that structure like this:

- `project request` -> campaign seed for a chapter, character build, or route style
- `feature intent` -> combat pillar or mission pressure type
- `concept unit` -> concrete mastery target such as parry timing, flank denial, aerial juggle stabilizing, bleed spread control, or anti-caster spacing
- `lesson blueprint` -> authored encounter packet
- `mini-game prompt` -> micro-combat test, tutorialized drill, duel phase, elite pack, traversal hazard, or boss exchange pattern
- `concept mistakes` -> tracked weakness ledger by combat competency
- `rest stop` -> low-pressure recovery room, forge pause, omen chamber, clinic, or equipment re-thread station

## Xenobloods Campaign Shape

Target length: 12 hours for a first clear.

Structure:

1. Prologue breach, 45 minutes
2. Blood district ascent, 90 minutes
3. Flooded archive descent, 75 minutes
4. Glass kiln siege, 75 minutes
5. Oathbreak market sweep, 60 minutes
6. Midpoint nemesis hunt, 60 minutes
7. Verdigris engine trench, 90 minutes
8. Idol reef incursion, 60 minutes
9. The split court, 75 minutes
10. Endgame climb and final tribunal, 90 minutes

That gives Xenobloods a real campaign instead of a padded loop. Every chapter owns one primary mastery axis and one secondary pressure axis so difficulty rises by composition rather than by raw health inflation.

## Enemy Paradigm Schisms

"Enemy paradigm schisms" should mean incompatible combat logics that force the player to read the field differently, not just recolored enemies.

Suggested schism families:

1. `Rendline`
Behavior:
- melee-biased pursuers
- fast commitment windows
- punish hesitation and poor spacing
What they teach:
- dodge timing
- short-window punishes
- crowd collapse management

2. `Lattice`
Behavior:
- formation enemies and shield-linked elites
- project safe zones and denial geometry
What they teach:
- angle breaking
- guard split tools
- target-priority discipline

3. `Mirecast`
Behavior:
- curse casters, delayed bursts, zone corruption
- weaker bodies but strong map control
What they teach:
- disruption routing
- projectile line reading
- anti-caster pathing

4. `Idolwrought`
Behavior:
- heavy constructs, posture monsters, counter-hit traps
- slower but devastating when respected poorly
What they teach:
- stamina economy
- posture break sequencing
- greed control

5. `Bloodkin Mirrors`
Behavior:
- elite duelists and late-game rivals that copy or answer the player's dominant habits
- they do not use magical omniscience; they bias against repeated player patterns
What they teach:
- mix-up discipline
- route variation
- tempo masking

The schisms are important because Pocode should not only track whether the player wins. It should track which enemy logic families are producing ugly wins, sloppy wins, clean wins, or repeated failures.

## Outfitting Loop

Enemy outfitting should also be adaptive, but only within authored guardrails.

Allowed adaptive variation:

- select one of 2 to 4 approved weapon packages per enemy role
- change resistance emphasis inside narrow bounds
- enable one supplemental behavior module, such as feinting, pursuit extension, delayed detonation, or shield relay support
- alter squad composition weights in authored encounter pools

Forbidden adaptive variation:

- inventing brand-new moves at runtime
- reading player inputs directly
- hard-countering the current build in a way the player cannot scout
- scaling enemy health or damage without an authored budget

That keeps the game competitive and fair. The adaptation should push the player's learning curve, not cheat.

## What Pocode Measures In Xenobloods

Replace academic mastery with combat mastery metrics:

- parry success rate
- late dodge rate
- overcommit frequency
- heal panic frequency
- ranged interruption success
- launcher conversion success
- crowd separation success
- boss phase retry count
- damage taken during greed windows
- build dependency stress, such as whether the player collapses when one favorite tool is unavailable

Each metric feeds one or more combat concepts. Example:

- repeated late dodges against `Rendline` enemies raise `close_pressure_timing` mistakes
- inability to break shield formations raises `angle_breaking` and `priority_collapse`
- repeated hits from delayed detonations raises `hazard_reading`

## Adaptive Encounter Rules

When the player is struggling:

- keep chapter order stable
- reduce simultaneous enemy logic overlap for the next 1 to 2 encounters
- prefer clearer telegraph packages
- add one easier reinforcement encounter that isolates the failed mastery target
- move one recovery node earlier if the player is in a steep failure cluster

When the player is excelling:

- increase logic overlap without changing encounter fairness
- promote more advanced enemy outfit packages from the approved pool
- shorten safe recovery windows
- add optional elite ambush branches and higher-tier reward caches
- bias rival enemies toward punishing repeated dominant player habits

The game should feel like it is tightening around the player, not rubber-banding wildly.

## Combat AI Patterning And Learning

The AI target is not infinite self-modifying learning. The AI target is a production-safe hybrid:

1. Hand-authored action trees for every archetype
2. Utility scoring per action based on distance, posture, ally state, zone control, and recent player habits
3. Short-horizon memory for what the player repeats in the current fight
4. Long-horizon profile tags per campaign save, such as `parry_hungry`, `panic_healer`, `launcher_fisher`, `backstep_defensive`
5. Encounter director rules that choose from authored package variants using those tags

This is aggressive but feasible. It feels smart without requiring unreliable runtime neural retraining or anti-player cheating.

## Real-Time CGI Target

Xenobloods should aim for a high-end but plausible PC visual stack:

- Unreal Engine 5.4+ or equivalent proprietary renderer
- Nanite-scale dense environments where appropriate
- Lumen or equivalent hybrid GI for moody interior/exterior transitions
- virtual shadow maps
- Niagara-grade volumetrics, blood mist, ash, embers, ritual weather, and cloth sparks
- motion matching or authored pose-search locomotion for player and elite duelists
- ML Deformer or equivalent selective hero-character deformation where worth the cost
- strand-based hair only on hero-tier characters and a few bosses
- heavily instanced crowd/background set dressing rather than full simulation everywhere

The realistic production rule: spend the extreme rendering budget on bosses, hero characters, and a few landmark spaces. Do not try to make every corridor a tech demo.

## 12-Hour Content Spine

The campaign should teach the player in this order:

1. survive one-on-one pressure
2. punish overextension safely
3. read ranged denial and cursed zones
4. break formations and split enemy roles
5. stabilize air and ground combo routing
6. handle mixed-pressure rooms with traversal hazards
7. adapt when rivals answer your favorite habits
8. carry your own style into a final gauntlet where every learned pattern matters

By the last two chapters, the player should feel hunted by the game's intelligence, but still able to explain why every death happened.

## Practical Implementation Path

Phase 1:

- extend `FeatureIntent` and `ConceptUnit` usage from coding concepts to combat competencies
- generate combat campaign packets from chapter seeds instead of software-project requests
- keep the same remediation and pacing machinery

Phase 2:

- build encounter tags for every enemy archetype, outfit package, and schism family
- store player weakness ledgers and dominant-style tags in local progression state
- feed those tags into encounter packet generation

Phase 3:

- connect the campaign packet system to the real combat runtime
- expose telemetry hooks from combat to the adaptive layer
- validate that adaptation improves readability and retention instead of simply increasing fail states

## Design Standard

Xenobloods should aim for an 89% stress threshold, not 100% chaos.

That means:

- beautiful, fully real-time visuals
- brutally high but legible combat demand
- AI that feels observant and personal
- adaptation that respects authored fairness
- no fake claims about infinite learning or impossible procedural miracles

If Pocode does its job, Xenobloods becomes a campaign that studies how the player learns combat and then sharpens the next chapter accordingly.