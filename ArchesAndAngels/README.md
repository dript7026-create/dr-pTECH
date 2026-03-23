# ArchesAndAngels

`ArchesAndAngels: Sinner of Oblivion` is beginning here as a C simulation prototype that turns the earlier concept brief into executable systems work.

The initial prototype focuses on three layers:

- faction pressure between industrial, simian, narcotic, spiritual, and hybrid empires
- district-level vice, doctrine, labor, and order drift
- incident generation that produces the kind of civic instability the larger action-RPG layer will eventually sit on top of

The current pass adds a fourth layer:

- player-directed civic operations that let the prototype choose how each week is shaped instead of only observing autonomous drift

The current development pass adds a fifth layer:

- campaign pressure analysis that scores district collapse risk, recommends operations, and produces a final strategic assessment instead of only printing raw stats

The latest pass adds a sixth layer:

- recommendation-history tracking so repeated compliance or repeated divergence now pushes scenario cards into different medium-term states instead of treating each directive as isolated

## Build

With GCC or Clang:

```powershell
gcc ArchesAndAngels/src/main.c ArchesAndAngels/src/aa_sim.c ArchesAndAngels/src/aa_export.c ArchesAndAngels/ArchesAndAngels_Sinner_of_Oblivion.c -IArchesAndAngels/src -IArchesAndAngels -o ArchesAndAngels/arches_and_angels_sim.exe
```

## Current Scope

The current executable is not the full game. It is a deterministic simulation slice that helps lock down:

- faction identities
- district economy and doctrine pressures
- incident generation language
- player operations such as public works, processions, crackdowns, census sweeps, militia musters, and smuggling compacts
- district pressure scoring and condition labels such as holding, strained, combustible, insurrection risk, and collapse brink
- operation recommendations for the hottest districts each week
- persistent faction agendas that keep pushing named demands across multiple weeks
- district scenario cards that track ongoing crises instead of treating every event as disposable text
- scenario successor chains where cards mutate into escalated or stabilized successors, then into terminal or settled second-generation endpoints
- director-level policies (Unification Doctrine, Free Commerce, Martial Consolidation, Tolerance Edict, Memoria Interdict) that reshape faction stats and suppress or inflate agendas
- three named protagonists with home districts, faction trust profiles, and combat/intel stats
- a mission board generated each week for high-pressure districts, assigning the best-fit protagonist
- recommendation streaks and ignored-recommendation streaks that alter scenario intensity and progress over multiple interventions
- concept-brief integration so the executable now reports against the authored world premise and story pillars
- final campaign stability assessment for tuning scenario direction
- turn-by-turn summary output for tuning

## Export

Write a machine-readable campaign snapshot for engine-side consumers with:

```powershell
.\ArchesAndAngels\arches_and_angels_sim.exe --json-out .\ArchesAndAngels\campaign_state.json
```

The export includes campaign summary, factions, districts, scenarios, agendas, protagonists, missions, and incidents.

## Test

Run the focused regression for the simulation with:

```powershell
pytest tests/test_arches_and_angels_sim.py
```

That gives the project a real codebase to extend into tactical, traversal, and combat layers next.