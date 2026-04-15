# XenoBloods Gameplay Prototype Pack

This document defines the current 2D-first asset pack intended to support a full gameplay prototype pass of XenoBloods.

## Coverage

The pack is designed to cover:

- all three life states: gourd infant, landborne vessel, etheric current
- one full Land zone with sparse navigation encounters and eye-lock initiation flow
- two Land enemy lanes: scarab-child rushers and lattice-ward formation pressure
- one active boss lane: Lahgroid hierophant
- three Up dialogue-pressure NPCs representing tetrarch authority
- three Low curgz puzzle-combat entities for energy-routing encounters
- cinematic battle staging assets with explicit foreground, midground, and background reads
- Xbox Series controller-facing UI and binding reference art

## Prototype Flow

### Land

- Exploration is metroidvania-style navigation through the Veinmarket prototype zone.
- Encounters begin when Ishtasha and an enemy achieve eye contact.
- The immediate pre-battle verb is a race-to-collision using only navigation movement.
- A timed attack confirm at collision can award preemptive damage.
- Regular combat then transitions into a cinematic battle scene.

### Battle Scene

- The battle scene is staged like a compact animated duel sequence.
- Telegraphs are nontext visual reads expressed by timing-ring and glyph assets.
- The player reads whether the opponent demands dodge, block, parry, or attack.
- Standard enemies use rapid turn exchanges with shrinking windows of opportunity.
- Bosses use the same visual language but stay fully real-time.

### Up

- Up has no physical combat in the prototype pack.
- Tetrarch encounters are dialogue-pressure scenes with instant smite risk.
- The danger strip and portrait assets exist to sell that tension nonverbally.

### Low

- Low prototype encounters are curgz energy-routing puzzle-combat scenarios.
- Directed currents are fed, bounced, and resisted through refractor and resistor reads.
- There is no normal melee loop here; the puzzle is the combat.

## Controller Posture

The pack is authored around an Xbox Series controller profile:

- `A`: attack / confirm
- `B`: dodge / cancel
- `X`: block / redirect
- `Y`: parry / interject
- `LT`: eye-lock / aim / focus
- `RT`: ranged release / blood burst / current feed
- `LB` and `RB`: depth shifting for foreground and background staging
- left stick: navigation and collision race steering
- right stick: lane bias and battle framing support

## Build Outputs

Run the gameplay pack build to regenerate both the static asset pack and the staged JumpClip previews:

```powershell
python xenobloods/tools/build_gameplay_prototype_asset_pack.py
```

Primary outputs:

- `xenobloods/assets/generated/prototype_gameplay_asset_manifest.json`
- `xenobloods/assets/generated/gameplay_prototype_asset_pack.json`
- `xenobloods/assets/generated/jumpclip_runtime/asset_service_summary.json`

These files together define the current prototype asset readiness state.