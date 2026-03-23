# ArchesAndAngels Progress

## 2026-03-13

- Confirmed `ArchesAndAngels` has moved beyond the concept stub into a working C simulation prototype in `src/`.
- Extended the simulation with district pressure scoring, condition labels, per-district operation recommendations, and a campaign stability metric.
- Expanded the executable loop so each week now prints a pre-brief for the highest-pressure district, shows whether the chosen directive matched the current recommendation, and ends with a final campaign assessment.
- Updated the README to reflect the deeper prototype scope.
- Fixed the incident lifecycle so player-directed operations remain visible in the same weekly report instead of being cleared before summary output.
- Rebuilt `arches_and_angels_sim.exe` and verified the run output. Current outcome lands in `unstable coexistence` with campaign stability `504`, which gives a useful baseline for the next tuning pass.
- Added persistent faction agendas and district scenario cards so named pressures now survive across weeks instead of dissolving into one-turn flavor text.
- Bound the executable to the saved concept brief by exporting title, premise, format, story pillars, and faction signatures from `ArchesAndAngels_Sinner_of_Oblivion.c`.
- Added recommendation-history tracking so repeated compliance or repeated divergence now compounds scenario progress and intensity instead of resetting each week to isolated choice effects.
- Added local VS Code MinGW C/C++ configuration and a focused regression test that builds and runs the simulation.

## Next Targets

- Add stronger branching and replacement logic so scenario cards can mutate into successor cards instead of only intensifying or receding.
- Introduce director-level policy paths that can align with or suppress multiple faction agendas at once.
- Begin tying the strategic layer to a future traversal/combat shell with named protagonists, districts, and actionable missions.

## 2026-03-13 (continued)

- Added second-generation scenario card successor chains. Scenarios now evolve through three tiers: `active → escalated/stabilized → terminal/settled`. Each district has unique second-gen cards (e.g., Ash Basilica: `Unburial Convocation → Reliquary Audit Schism → Necropolitical Theocracy`). The `generation` field tracks mutation depth.
- Added director-level policy system with five policies: Unification Doctrine, Free Commerce, Martial Consolidation, Tolerance Edict, and Memoria Interdict. Policies affect all factions and districts simultaneously, expire after 3 weeks, and create strategic trade-offs.
- Added traversal/combat shell with three named protagonists: Vael Ashborne (Relay Auditor), Kez Thornmantle (Frontier Warden), and Sister Pyreth (Choir Dissident). Each has home districts, faction trust profiles, and combat/intel stats.
- Added mission generation system that produces up to 4 missions per week for high-pressure districts, assigning the best-fit protagonist based on faction trust and district affinity.
- Extended the opening plan from 6 turns to 10, with policies deployed on turns 2, 4, 6, 7, and 9 to exercise the full policy rotation.
- Campaign stability improved from 504 to 663 (fragile consolidation) with the longer, policy-assisted run. Two terminal crises emerged (Ash Basilica and one other).
- Rebuilt and verified. All existing tests pass.

## Next Targets

- Add protagonist stat changes from missions: combat readiness, intel access, and faction trust should update based on mission outcomes.
- Introduce mission success/failure resolution tied to protagonist stats and difficulty thresholds.
- Add inter-protagonist dialogue stubs that fire when multiple protagonists share a district or faction alignment.
- Begin implementing the tactical incident layer: named encounters within districts that a protagonist must resolve in real-time combat framing.

## 2026-03-13 (pass 2)

All three next targets from the previous pass are now implemented and verified:

- **Scenario successor chains**: `mutate_scenario_successor` (gen 1) and `mutate_scenario_second_gen` (gen 2) produce named successor and terminal/settled scenario cards with full narrative text per district. `evolve_scenarios` drives the branching logic each week.
- **Director policies**: Five named policies (Unification Doctrine, Free Commerce, Martial Consolidation, Tolerance Edict, Memoria Interdict) are wired into the main loop. Each planned turn can optionally apply a policy. `tick_policy` handles expiration.
- **Protagonists and missions**: Three named protagonists (Vael Ashborne, Kez Thornmantle, Sister Pyreth) with home districts and faction trust profiles. `aa_generate_missions` produces a mission board each week for districts above pressure threshold 75, assigning the best-fit protagonist.
- **JSON export**: `aa_export.c` serializes the full campaign state (factions, districts, scenarios, agendas, protagonists, missions, incidents) to JSON via `--json-out`.
- **Extended campaign**: Main loop now runs 10 planned turns (up from 6) with alternating policy/no-policy weeks.
- Verified: simulation builds clean with GCC, runs 10 weeks, final stability 663 (fragile consolidation), 2 terminal crises, 4 active missions, Unification Doctrine active at close.

## Next Targets

- Add protagonist stat evolution so combat readiness and intel access shift based on mission outcomes and district exposure.
- Implement mission resolution logic where protagonist stats and difficulty interact to produce success/failure/partial outcomes with narrative consequences.
- Wire scenario card phase into mission difficulty scaling so terminal-phase districts produce harder missions with higher narrative stakes.
- Begin planning the traversal/combat shell interface that the strategic layer will feed into.