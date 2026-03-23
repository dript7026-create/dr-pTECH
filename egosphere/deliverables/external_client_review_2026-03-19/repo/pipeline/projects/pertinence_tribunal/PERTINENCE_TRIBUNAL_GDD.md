# Pertinence: Tribunal - Game Design Document

## High Concept
Pertinence: Tribunal is a side-scrolling souls-like metroidvania action-platformer RPG about Kier, a rat-man ronin forced to cross a procedurally recomposed fiefdom and tribunal-state to disprove the myth that his ancestors brought disease to the continent.

## Aesthetic Direction
- Painterly 2D spritesheets with transparent backgrounds and hard-read silhouettes.
- Dense swamp, cathedral, ossuary, and cosmic courtroom biomes with rich warm-cold palette contrast.
- ORBEngine-style pseudo-3D depth strips, layered parallax, and reality-render overlays for astral transitions.
- Costume language: reed-wrapped ronin cloth, lacquered tribunal armor, salt-eroded stone, moonlit brass, wet ink blacks, and fungal whites.

## Core Pillars
- Exacting melee combat with block, parry, dodge, and stance commitment.
- Procedural narrative assembly through witness testimony, Goduly interventions, and regional rumor graphs.
- Reputation-driven world response that changes exploration routes, boss context, and available truths.

## Asset Program
- Sprite sheets: 88
- Environmental/parallax/depth sheets: 8
- Dialogue portraits: 6
- Dedicated combat/traversal/environment FX sheets: 16
- Seven entity classes: player, low-tier enemy, mid-tier enemy, top-tier enemy, NPC, fauna, and Goduly.

## Animation Bible
### Kier, the Player Rat-Man Ronin
- Expanded player combat and traversal suite: idle (8f), idle_breath (8f), walk (8f), run (8f), sprint_stop (6f), crouch (6f), crouch_walk (6f), ledge_hang (6f), ledge_climb (8f), jump_start (6f), jump_air (6f), double_jump (8f), air_dash (8f), slide (8f), ladder_climb (8f), light_attack_1 (8f), light_attack_2 (8f), light_attack_3 (8f), heavy_attack (10f), charged_slash (12f), launcher (10f), aerial_combo (10f), dodge (8f), backstep (8f), block (6f), parry (8f), counter_slash (10f), wall_cling (6f), wall_jump (8f), grapple_hook (10f), dash_slash (10f), plunge_attack (10f), heal_focus (10f), relic_cast (10f), hit_react (6f), death (12f)
- Frame plan: anticipation 2f, action 2-4f, recovery 2-4f, silhouette break on each attack apex, sword readable at every key frame.

### Low-Tier Enemies (24 types)
- Archetype sets: skirmisher, ambush, ranged, brute.
- Skirmisher set: idle (6f), patrol_walk (8f), alert_run (8f), feint (6f), thrust (8f), retreat (6f), sidehop (6f), lunge (8f), stagger (6f), death (8f)
- Ambush set: idle (6f), creep (8f), ceiling_drop (8f), scuttle (8f), swipe (8f), poison_spit (8f), burrow (8f), evade (6f), stagger (6f), death (8f)
- Ranged set: idle (6f), patrol_walk (8f), backpedal (8f), aim_fire (10f), reload (8f), trap_set (8f), panic_run (8f), melee_panic (6f), stagger (6f), death (8f)
- Brute set: idle (6f), stomp_walk (8f), guard_up (6f), shield_bash (8f), overhead_slam (10f), charge (10f), grab (8f), roar (6f), stagger (6f), death (8f)
- Function: harassment, attrition, environmental pressure, plague-ridden crowd control.

### Mid-Tier Enemies (14 types)
- Archetype sets: duelist, caster, siege.
- Duelist set: idle (6f), walk (8f), run (8f), jump (6f), feint (6f), light_attack (8f), heavy_attack (10f), combo_finisher (10f), dodge (8f), block (6f), parry (8f), grab (8f), stagger (6f), recover (6f), death (10f)
- Caster set: idle (6f), walk (8f), hover_step (8f), ward_raise (8f), projectile_cast (10f), sigil_drop (10f), beam_sweep (12f), teleport (8f), summon (10f), panic_dash (8f), stagger (6f), death (10f)
- Siege set: idle (6f), deploy_walk (8f), brace (6f), aim (8f), fire_volley (10f), reload (10f), backstep (8f), mine_drop (8f), shield_turn (8f), stagger (6f), collapse (8f)
- Function: gatekeeping traversal checks, mixed melee-ranged pressure, elite arena anchors.

### Top-Tier Enemies (7 types)
- Boss set: idle (8f), walk (8f), run (8f), crouch (6f), jump (8f), light_attack_1 (8f), light_attack_2 (8f), heavy_attack_1 (10f), heavy_attack_2 (10f), dodge (8f), block (6f), parry (8f), phase_shift (10f), summon (12f), projectile_cast (10f), beam_cleave (12f), aerial_slam (10f), ground_spike (12f), grapple (8f), roar (8f), arena_lock (8f), teleport (8f), counter_stance (8f), curse_pulse (10f), stagger (6f), recover (8f), enrage (10f), death (12f), finisher (12f)
- Function: major bosses with phase changes, summon states, and arena-control attacks.

### NPC, Fauna, and Goduly
- NPCs and fauna use the basic set: idle (8f), walk (8f), run (8f), turn (6f), crouch (6f), jump (6f), light_attack (8f), heavy_attack (10f), dodge (8f), block (6f), parry (8f)
- Godulies use the basic set plus interactions: blessing_offer (10f), memory_projection (10f), verdict_gaze (8f), astral_shift (10f), halo_flare (10f), seal_inscription (10f), lore_reveal (10f), trial_mark (8f), time_fold (10f), departure (8f)
- FX sheets use a shared six-stage timing plan: startup (6f), burst (8f), loop (8f), impact (8f), trail (8f), dissipate (8f)

## Environment Requirements
- Flooded rice terraces, salt forests, ossuary caverns, tribunal cathedrals, archive ferries, and cosmic witness chambers.
- Every exploration zone needs foreground, midground, and backdrop layers plus a depth or reality-render overlay when narrative pressure spikes.
- Environmental sheets must support parallax and pseudo-3D strip extrusion in Blender/ORB-style staging.

## Narrative Structure
## Arc I: Ash of the Oath
Kier returns to the reedbound fief of Hallowfen to investigate plague writs naming rat clans as originators of the continent's wasting blight.

1. The Reed Gate [exploration] - Kier crosses the flood-barrier and learns the tribunal has sealed the ancestral district.
2. Salt in the Wells [combat] - Low-tier bailiffs and censer monks attack as Kier uncovers forged disease ledgers.
3. Writ of Cinders [exploration] - A hidden archive reveals that the accusation predates the plague by generations.
4. The Bell Below [combat] - Kier defeats the Plague Bell pack-master beneath the ferry crypts.
5. Ancestral Silt [exploration] - A Goduly offers a memory shard showing human merchants importing the true contagion.

## Arc II: Litigants of the Fen
The tribunal's deputies pursue Kier through marsh villages while local houses bargain over truth, fear, and grain routes.

1. Fen Market Interdiction [exploration] - NPC factions react to Kier's reputation as rumors spread through the open-world settlements.
2. Ballad of Moss and Iron [exploration] - The Penitent Poet unlocks a side route into the Salt Forest via a metered verse challenge.
3. Abbey Ballista [combat] - A mid-tier siege keeper turns the canopy paths into a projectile gauntlet.
4. Ferryman's Ledger [exploration] - Travel records prove the plague entered by war-barge from the western principalities.
5. Marsh Inquisitor [combat] - A mounted inquisitor attempts to burn the evidence and brand Kier a heretic.
6. Witnesses in Amber [exploration] - Goduly avatars preserve testimonies in suspended resin, expanding the procedural lore graph.

## Arc III: Cathedral of Rotated Truth
Kier infiltrates the tribunal cathedral where verdicts are literally carved into shifting architecture and history is rearranged by ritual.

1. The Rotating Nave [exploration] - Pseudo-3D parallax chambers rotate while Kier navigates orbital lifts and hidden judgment shafts.
2. Notary Blades [combat] - Clockwork scribes and top-tier duelist bailiffs guard the chamber of inherited blame.
3. The False Origin [exploration] - A secret mural shows the tribunal needed a foreign culprit to unify the warring fiefdoms.
4. Sable Notary [combat] - Kier duels the Sable Notary, who weaponizes edited memories as phase attacks.

## Arc IV: Godulies in Session
Cosmic deity avatars descend to test whether Kier seeks justice, vengeance, or simply a replacement lie.

1. Amber Accord [exploration] - The first Goduly demands that Kier reenact the first trial in a memory theater.
2. Trial of Mercy [combat] - Optional duels against mirrored ronin examine how the player treats neutral factions.
3. Lantern Grace [exploration] - Traversing astral reed bridges unlocks parallax reality layers over the main world.
4. Verdict Gaze [combat] - A Goduly interaction sequence becomes a combat test if Kier's reputation falls too low.
5. Ink Saint Deposition [exploration] - The last living plague survivor reveals a state-sponsored coverup.
6. Orbit of Hollow Names [combat] - Twelve deity avatars overlap their arenas in a multi-phase boss council.
7. The Open Record [exploration] - Kier chooses which truths to release, altering final world-state generation.

## Arc V: Tribunal of Pertinence
The accusation against Kier's ancestors is retried in the ruins of the high court as the entire continent watches the result ripple outward.

1. The Continent Listens [exploration] - Settlements reflect accumulated player reputation, alliances, and witness testimony.
2. Sepulchral Judge [combat] - The high judge enters a souls-like duel phase with summons from every prior arc.
3. Cartographer of Blight [combat] - The final boss remaps the arena using plague routes and cosmic star-lines.
4. Pertinence Rendered [exploration] - Kier delivers a final verdict: absolution, condemnation, or shared culpability.
5. After the Record [exploration] - The world regenerates under the chosen truth, seeding New Game Plus myth variants.

## Technical Test Intent
- Asset pack is organized to validate Clip Studio export metadata, Blender conversion plans, and idTech2 spawn/precache/dispatch generation.
- Placeholder sheets retain transparency and category-specific silhouette language so automated validation can inspect alpha usage and bundle coverage.