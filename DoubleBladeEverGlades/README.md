# Double-Blade EverGlades

Double-Blade EverGlades is a third-person co-op action game set in a compact jungle horticultural settlement overrun by a once-sacred wondercrop. Two surviving workers cut a path through hostile sentient growth, awaken RootKnots as rest and fast-travel hubs, and push toward the MandrakeMother at the far edge of a diamond-shaped wilderness.

## Project Intent

- Target platforms: PC, Nintendo Switch / Switch 2, Xbox Series, PlayStation 5 / PS6-class targets, handheld controller PCs such as ROG Ally / Steam Deck
- Core perspective: behind-the-body third-person full-character view
- Play structure: solo or two-player co-op with identical control contracts
- Input identity: twin-stick hand aiming, bumper blade swings, trigger-stepping locomotion, D-pad item use, face-button skills

## Premise

KanBarilNucelotosc is the village's medicinal, culinary, textile, and spiritual wondercrop. Overuse, ritual dependence, and later commodification distort the village economy until only two villagers remain capable of labor. During a routine field pass, hyper-growth erupts. Dense purple smoke and the villagers' own breath chemistry have altered the crop into a hostile sentient ecosystem.

The two survivors become the playable pair. They must slash through violent tendrils, bloom-torsion predators, and crop-born guardians while stabilizing RootKnots that function as checkpoints, self-growth hubs, and fast-travel anchors.

## Canonical Scope

- World footprint: 35,687 square feet of traversable space
- World shape: diamond ground plane
- RootKnots: progression-spaced rest hubs generated along the diagonal route to the MandrakeMother
- Enemy catalog target: 230 hostile crop varieties plus the MandrakeMother
- Weapon catalog target: 1,064 blade variants generated from consistent archetype rules
- Item target: 32 auto-collected cull-drop items mapped to the D-pad
- Skill target: 13 face-button skills unlocked through RootKnot growth paths

## Controls

### Standard Controller Contract

- Left stick: left-hand aiming / positioning arc
- Right stick: right-hand aiming / positioning arc
- Left bumper: left-hand slash
- Right bumper: right-hand slash
- Alternate left/right triggers: step-walk forward
- Double-tap alternating triggers: retreat walk
- Hold either trigger: strafe using the planted foot cadence
- D-pad: cycle and consume cull-drop items
- Face buttons: 13 special skills by context page
- Menu / map buttons: pause, equipment, map, RootKnot travel

### Blade Handling Model

- Single-handed blades obey independent hand aim and swing timing
- Double-handed blades require simultaneous dual-stick rotation to maintain edge alignment and movement leverage
- Blow strength is determined by stick precision, timing precision, haptic rhythm, and angle match versus enemy anatomy

## Progression Backbone

The project keeps progression legible through five acts:

1. Withered Commons: collapse of the village edge and the first RootKnot recovery
2. Resin Walks: tighter enemy pressure and first branching item utility checks
3. Smoke Loom: stronger mutation density, vertical slicing spaces, skill synergies begin to matter
4. Knotfall Basin: route compression, elite crop guardians, multi-RootKnot routing choices
5. Mother Verge: maximum botanical aggression and the final MandrakeMother approach

Every act increases three values in a controlled way:

- route pressure
- enemy mutation complexity
- hand-precision demand

## Data Sources

- `double_blade_everglades_project.json`: canonical design seed
- `tools/build_progression_manifest.py`: deterministic compiler for acts, RootKnots, blades, enemies, items, and skills
- `generated/progression_manifest.json`: generated runtime-friendly progression manifest

## Build The Design Manifest

```powershell
cd DoubleBladeEverGlades
python tools\build_progression_manifest.py
```

This emits a deterministic JSON manifest that downstream runtime, combat, UI, and asset tooling can consume.