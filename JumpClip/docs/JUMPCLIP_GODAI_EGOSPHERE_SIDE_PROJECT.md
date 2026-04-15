# JumpClip Godai And Egosphere Side Project

## Purpose

This document defines a side-project learning layer for JumpClip. It is not the core renderer. It is a designer-assistance system that learns from gameplay histories and suggests stylistic inclinations, motif shifts, and key-pose biases for future JumpClip generation choices.

## Separation Rule

The side project must remain advisory.

It should:

- observe gameplay history
- summarize stylistic signals
- bias generation defaults
- propose motion and art-direction tendencies

It should not:

- directly replace authored art direction
- generate protected-IP imitation
- override explicit designer intent
- become a hidden black-box source of final content decisions

## Roles

### JumpClip Core

- renders assets
- interprets prompts and explicit overrides
- applies art and motion presets
- exports production assets

### Egosphere Side Layer

- stores structured gameplay history
- derives player-style and region-style embeddings
- tracks recurrence of favored silhouettes, color tensions, motion energies, and prop grammars

### Godai Side Layer

- provides an authored conceptual balancing frame
- lets style suggestions be categorized as Earth, Water, Fire, Wind, or Void leaning
- acts as a readable semantic bridge between raw history and designer-facing suggestions

## Why This Exists

The target is not procedural chaos. The target is historically informed taste.

If players consistently express specific motion or visual preferences through how they play, JumpClip can expose those tendencies to designers as optional nudges.

Examples:

- a player population that favors high-mobility evasive play may justify lighter silhouettes and stronger airborne poses
- a region with slow defensive play may justify heavier stance templates and denser grounded prop grammars
- a faction identity may accumulate preference for ritual symmetry, asymmetrical scavenger kits, or aggressive impact frames

## Godai Mapping

Use Godai as an interpretable style lens.

### Earth

- silhouette: broad, stable, grounded
- material tendency: ceramic, stone, layered shell, reinforced cloth
- motion tendency: compression, hold, delayed recovery
- key-pose bias: low center, braced stance, planted feet

### Water

- silhouette: flowing, tapering, layered
- material tendency: lacquer, membrane, fiber, polished organic surfaces
- motion tendency: arc continuity, elastic settle, circular hand paths
- key-pose bias: soft transitions, flowing anticipation, long follow-through

### Fire

- silhouette: sharp, flared, thrust-forward
- material tendency: scorched metal, ember-glass, aggressive accent lighting
- motion tendency: violent release, hard acceleration, abrupt punctuation
- key-pose bias: coiled anticipation, extended strike, harsh recoil

### Wind

- silhouette: lifted, narrow, directional
- material tendency: reed, feather, cable, banner, wing-like trims
- motion tendency: quick contact, feints, glides, low drag
- key-pose bias: airborne extension, diagonal lean, asymmetrical balance

### Void

- silhouette: uncanny spacing, interruption, hollowness, offset symmetry
- material tendency: iridescent matte, memory scar, interference glow
- motion tendency: timing irregularity, stillness before burst, off-beat recovery
- key-pose bias: suspended holds, nonstandard facing, phase-shift posture

## Egosphere Data Model

Recommended gameplay-history inputs:

- player or guild identifier
- shard or campaign identifier
- biome or zone identifier
- encounter type
- classless role expression inferred from actions
- mobility level
- aggression level
- support or utility level
- equipment family usage
- win/loss outcome
- damage intake pattern
- traversal preference
- session duration
- timestamp

Recommended derived style features:

- silhouette preference vector
- ornament tolerance
- color contrast preference
- mobility posture bias
- anticipation severity preference
- impact readability preference
- ritual versus utilitarian bias
- symmetry versus asymmetry bias

## Learning Outputs For Designers

The system should output suggestions, not commands.

Suggested outputs:

- recommended `style_family`
- recommended silhouette and texture ranges
- recommended accessory-density ceiling
- recommended motion template family
- preferred key-pose tags
- biome or faction-specific accent motifs
- “history tension” note when current direction goes against player behavior trends

## Example Influence Record

```json
{
  "subject": "jumpclip-region-amber-delta",
  "godai": {
    "earth": 0.18,
    "water": 0.24,
    "fire": 0.14,
    "wind": 0.31,
    "void": 0.13
  },
  "style_signals": {
    "style_family": "16bit",
    "silhouette_emphasis": 1.46,
    "texture_detail": 0.34,
    "palette_limit": 15,
    "outline_weight": 1.28,
    "accessory_density": 0.37
  },
  "motion_signals": {
    "motion_silhouette_bias": 1.18,
    "motion_squash_stretch": 0.22,
    "motion_impact": 0.48,
    "motion_lift": 1.16,
    "preferred_key_pose_tags": [
      "airborne_extension",
      "landing_catch",
      "look_focus"
    ]
  }
}
```

## How Designers Should Use It

Recommended workflow:

1. start from authored art direction
2. inspect `egosphere` influence report for the target audience, region, faction, or game mode
3. accept, reject, or partially adopt suggested biases
4. feed accepted values into JumpClip as explicit overrides or preset adjustments

This keeps final authorship with the designer.

## JumpClip Integration Surface

The side project should eventually be able to propose values for:

- `style_family`
- `silhouette_emphasis`
- `texture_detail`
- `palette_limit`
- `outline_weight`
- `accessory_density`
- `motion_silhouette_bias`
- `motion_squash_stretch`
- `motion_impact`
- `motion_lift`

It can also suggest named design templates like:

- `jumpclip-courier-windlight`
- `jumpclip-heavy-earthguard`
- `jumpclip-fireduelist-impact`
- `jumpclip-void-ritualist-offset`

## Guardrails

The learning layer must not:

- infer “similar to protected game X” as a target label
- use copyrighted assets as feedback exemplars for style matching
- collapse all outputs toward majority preference and erase authored range
- rewrite generation prompts invisibly

The system should always preserve:

- provenance of inputs
- explicit authored overrides
- opt-out for side-project influence
- auditability of why a suggestion was made

## Suggested Technical Phases

### Phase 1

- define event schema
- define Godai style mapping
- emit simple static influence reports

### Phase 2

- cluster gameplay histories by player archetype and region
- derive style and motion preference summaries
- expose suggested JumpClip override sets

### Phase 3

- add designer dashboard
- add comparison view between authored preset and history-informed variant
- add approval workflow for accepted side-project suggestions

## Bottom Line

Treat `godai` and `egosphere` as a learning sidecar for JumpClip. Their job is to translate gameplay history into interpretable style and key-pose inclinations so designers can make better original choices, not to automate taste or imitate outside properties.