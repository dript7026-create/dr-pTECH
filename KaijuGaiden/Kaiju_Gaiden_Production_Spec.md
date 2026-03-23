# Kaiju Gaiden Production Spec

## 1. Purpose

This document converts the consolidated design and asset summary into a production-oriented execution spec. It is intended to answer four practical questions:

1. What is the current playable product?
2. What systems are already real in code?
3. What should be built next, in what order?
4. What content and engineering work is still missing before Kaiju Gaiden becomes a broader campaign-scale game?

This spec treats `kaijugaiden.c` as the current gameplay authority and uses the `src/` tree as related prototype/support code rather than the main runtime truth.

## 2. Current Product Definition

### Current Playable Product

Kaiju Gaiden is currently a compact boss-brawler prototype with:

- splash and intro cinematic flow
- title menu
- password input and restore
- one harbor stage intro
- three gated minion waves
- one three-phase boss fight
- one cypher reward loop
- game over return path

### Current Target Reality

- Most battle tuning and playtest validation are centered on the GB-compatible runtime.
- A `.gba` artifact exists and the codebase still carries GBA paths.
- Host builds are essential for iteration, feel tuning, and QAIJockey capture.

### Current Market Position

The project is not yet a full campaign game. It is currently a polished vertical slice encounter with real persistence, real combat readability work, and enough structure to scale into a larger action game.

## 3. Canonical Runtime And Related Code

### Canonical Gameplay Runtime

- `KaijuGaiden/kaijugaiden.c`

### Runtime Responsibilities In `kaijugaiden.c`

- target abstraction
- input polling
- tile and sprite loading
- splash/title/password flow
- stage intro
- combat systems
- boss logic
- minion logic
- HUD and FX composition
- cypher reward state
- password progression encoding/decoding

### Related Prototype And Support Code

- `KaijuGaiden/src/`
  - modular GBA prototype and scaffolding
- `KaijuGaiden/host_graphical.py`
  - host-side visual execution path
- `KaijuGaiden/run_qaijockey.py`
  - compatibility runner into NeoWakeUP QAIJockey runtime
- `KaijuGaiden/tools/verify_input_contract.py`
  - input-path contract verification
- `KaijuGaiden/tools/verify_dmg_constraints.py`
  - DMG-budget and runtime-budget verification

## 4. Production Pillars

### Pillar A: Tight Boss Combat

The game succeeds or fails on duel readability and the feeling of a kaiju confrontation in constrained screen space.

Current strengths:

- readable boss telegraphs
- minion windup/recovery states
- buffered attack/dodge input
- banners and HUD cues
- tuned micro-camera movement and shake

Required continuation:

- add a second boss without diluting the clarity already achieved on Harbor Leviathan
- preserve attack legibility as content scales
- keep combat deterministic and testable enough for AI and host validation

### Pillar B: Ecological Reward Loop

Bosses must remain more than HP bars. The cypher reward model is the main bridge from encounter design into world meaning.

Current strengths:

- cypher reward loop exists structurally
- password data already stores boss clears and cyphers

Required continuation:

- connect cyphers to actual stage unlocks and world-state branches
- define the difference between purify and recode outcomes in implemented systems, not only lore

### Pillar C: Portable Multi-Target Runtime

The project is strongest when one gameplay source drives GB, GBA, and host iterations.

Current strengths:

- single-file canonical runtime
- GBA, GB, and host paths are already represented
- host playtest and QAIJockey infrastructure exist

Required continuation:

- keep platform differences below the gameplay layer
- avoid forking core combat rules across targets

### Pillar D: Asset Discipline

There is already enough history in the repo for asset confusion to become a real problem.

Current strengths:

- active generated GB asset set is identifiable
- legacy and prototype headers are still present for reference

Required continuation:

- maintain an active-versus-legacy asset distinction
- avoid silently reviving prototype headers as if they are current production assets

## 5. Current Implemented Systems

### A. Flow State Machine

Implemented live phases:

- splash
- cinematic
- title
- stage intro
- combat
- boss death
- cypher drop
- game over
- password

Production status:

- stable enough to build on
- suitable for adding more stages if state transition logic is kept explicit

### B. Player Combat

Implemented live behaviors:

- primary combo attack
- dodge input path
- input buffering
- beat-window timing bonus
- NanoCell temporary boost

Production status:

- solid nucleus
- should be tuned through encounter expansion rather than rewritten wholesale

### C. Boss Combat

Implemented live behaviors:

- wave-gated boss unlock
- three boss phases
- attack selection based on range and phase
- telegraph and recovery timing
- stun state

Production status:

- stable enough to use as the pattern for boss 2

### D. Minion Combat

Implemented live behaviors:

- wave spawning
- simple locomotion and attack pressure
- windup and recover states
- NanoCell drop economy

Production status:

- sufficient for prototype pressure
- not yet a full archetype roster

### E. Progression Persistence

Implemented live behaviors:

- password encode/decode
- boss clear bitmask
- cypher bitmask

Production status:

- already a strong foundation for stage expansion
- should become the single progression contract before any deeper content scaling

### F. Camera And Readability

Implemented live behaviors:

- bounded travel lead
- bounded combat lead
- telegraph lead
- camera shake
- lower-cost redraw logic between layout shifts

Production status:

- one of the strongest refined systems in the current runtime
- should be preserved as a hard quality baseline when new content is added

### G. Validation And QA Support

Implemented live support:

- host runtime path
- QAIJockey capture path
- input contract verification
- DMG budget verification
- direct ROM build validation

Production status:

- above average for a project at this stage
- should be expanded into content regression checks rather than abandoned

## 6. Missing Systems

### Missing System: Stage Graph

Current gap:

- progression state exists
- actual stage selection logic beyond the first harbor encounter does not meaningfully exist yet

Needed implementation:

- stage table
- unlock requirements
- stage metadata lookup
- selected stage to boss/minion content routing

### Missing System: Multi-Boss Content Framework

Current gap:

- Harbor Leviathan exists as a bespoke boss
- future bosses are not yet formalized in code as content-driven entries

Needed implementation:

- boss definition table
- stage-to-boss binding
- per-boss phase data
- per-boss attack range and timing tables

### Missing System: Cypher Consequence Model

Current gap:

- cyphers are awarded and persisted
- ecological consequences are still mostly fictional framing

Needed implementation:

- purify outcome path
- recode outcome path
- world-state flags per biome
- unlock and mutation consequences

### Missing System: VN Integration

Current gap:

- VN exists strongly in lore and older drafts
- modular `src/` tree has VN scaffolding
- live runtime does not yet expose meaningful VN progression content

Needed implementation:

- chapter unlock table
- chapter playback state
- branch selection based on cypher use

### Missing System: Audio Production Layer

Current gap:

- broad audio direction exists in design
- repo still reads as placeholder-heavy on the asset side

Needed implementation:

- defined music banks
- stage stingers
- boss impact and telegraph SFX
- cypher reward cue set

## 7. Priority Roadmap

### Priority 1: Preserve And Lock Harbor Shore

Goal:

- freeze the current Harbor Shore encounter as the quality baseline

Tasks:

- keep current combat readability systems intact
- ensure all Harbor assets are tagged active in the manifest
- continue validating with host and QAIJockey runs after changes

Exit condition:

- Harbor Shore remains build-stable and playtest-stable while surrounding systems evolve

### Priority 2: Add Stage/Boss Data Model

Goal:

- stop hardcoding Harbor-only assumptions into the broader design trajectory

Tasks:

- create a stage definition structure
- create a boss definition structure
- route encounter initialization through those structures
- preserve the current Harbor fight as the first data entry

Exit condition:

- stage 2 can be added without cloning large amounts of Harbor-specific code

### Priority 3: Add Boss 2 And Biome 2

Goal:

- prove that the game expands beyond a single encounter without collapsing in readability or asset discipline

Tasks:

- define second biome theme
- define second boss phase set
- define second cypher reward
- implement unlock path from harbor completion

Exit condition:

- a second encounter is playable from the same runtime and progression layer

### Priority 4: Formalize Cypher Consequences

Goal:

- make the restoration-versus-mutation promise mechanically real

Tasks:

- add state flags for purify and recode outcomes
- branch unlocks or player modifiers from those choices
- connect outcome data to title/menu/stage selection feedback

Exit condition:

- cyphers are no longer only collectible tokens; they become actual game-state decisions

### Priority 5: Reconcile Architecture

Goal:

- decide whether the monolithic runtime remains canonical long-term or becomes the prototype reference for a re-modularized build

Tasks:

- identify which systems are safe to extract
- preserve parity tests between monolithic and modular paths if extraction begins

Exit condition:

- architecture direction is intentional rather than accidental

## 8. Production TODOs By System

### Combat

- add boss definition table
- add minion archetype slots beyond current generic wave pressure
- formalize combo-finisher and beat-window tuning as reusable data
- ensure second boss does not require rewriting camera logic

### Progression

- add stage unlock table
- connect `cleared_bosses` to actual selection/UI feedback
- connect `cyphers` to ecological consequence states

### UI And UX

- stage-select or region-select screen after first encounter expansion
- clearer cypher resolution messaging
- persistent unlock readout on title/menu side

### Story

- define chapter table for VN unlocks
- bind Harbor completion to chapter 1 unlock
- write the next biome's cypher consequence in concrete gameplay terms

### Asset Pipeline

- mark active generated GB assets as canonical
- mark top-level placeholder and legacy headers as deprecated or legacy
- define naming convention for future boss and biome assets

### QA

- keep novice and standard QAIJockey capture presets
- add multi-stage regression capture once boss 2 exists
- preserve DMG budget verification after every asset expansion

## 9. Asset Production Spec

### Active Asset Group

These are the assets directly supporting the current live runtime:

- Harbor background tiles
- HUD tiles
- Rei sprite tiles
- Harbor Leviathan phase sprite tiles
- minion sprite tiles
- hit and NanoCell FX tiles
- intro cinematic sprite tiles

### Legacy Asset Group

These exist in the repo but should not be treated as automatically current:

- old top-level asset headers in `assets/`
- placeholder authoring headers
- empty or staging-only authoring folders

### Planned Asset Group

Needed to reach a larger campaign-scale version:

- boss 2 full sprite set
- biome 2 background set
- expanded minion family sheets
- VN panel art
- real audio package
- stage selection UI art
- cypher consequence UI art

## 10. Technical Quality Bars

### Gameplay Quality Bar

- every new boss must preserve telegraph clarity
- every new combat addition must still be readable on constrained display targets

### Asset Quality Bar

- every active asset must be classifiable as active, legacy, or planned
- no ambiguous production status for visual content

### Code Quality Bar

- progression rules should move toward data-driven tables
- encounter-specific logic should avoid uncontrolled duplication

### Build Quality Bar

- GB build remains valid
- GBA artifact remains reproducible
- host path remains usable for rapid playtest

### QA Quality Bar

- QAIJockey capture should continue to complete the shipping encounter
- DMG budget verification should remain green after content changes

## 11. Definition Of Done For The Next Meaningful Milestone

The next milestone should not be defined as “more content exists.” It should be defined as:

- Harbor Shore still stable
- boss/stage data model added
- second boss playable
- second cypher unlock path functional
- progression reflected in UI or stage flow
- all builds and validation paths still green enough to iterate safely

## 12. Summary

Kaiju Gaiden’s most important production advantage is that it already has a coherent real encounter, a real persistence path, and real tuning infrastructure. The project should scale outward from that stable harbor fight, not sideways into disconnected prototype branches. The correct next move is structured expansion: formalize stage and boss data, add boss 2, then make cypher consequences mechanically real.