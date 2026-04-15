# Kin Dark Runtime And Controller Spec

## Core Runtime Shape

- simulated 3D world with 2D actor prefabs
- one giant contiguous city map
- three interlocking protagonist timelines active on the same world state
- camera fixed behind the protagonist body with aim-follow reticle bias
- real-time combat, traversal, and interaction

## Controller Mapping

- Left Stick: omnidirectional movement
- Right Stick: omnidirectional aim reticle and camera rotation bias
- LT: zoom in, focus, and soft lock-on to object, enemy, boss, NPC, or target
- RT: primary attack / context-fire / active power discharge
- LB / RB: stance modifiers, spell modifiers, telepathic mode shifts, traversal assists
- X / Y / B: combat, mobility, item use, or protagonist-specific system actions
- A: adaptive context action; hold for 1.0 second to interact whenever interaction is available
- View: maps, investigative overlays, timeline state, district index
- Menu: pause, inventory, quest log, accessibility, save and quit

## Camera Rules

- default camera anchor: directly behind the active protagonist, slightly elevated
- camera orbit follows right-stick aim reticle rather than raw movement vector
- LT focus tightens FOV and increases target stickiness
- target lock can prioritize enemies, NPCs, interactive objects, doors, ladders, ritual devices, or evidence points

## Save / Boot Rules

- opening menu is one selectable Play Game option only
- if no save is present, Play Game launches a fresh timeline bootstrap
- the fresh timeline bootstrap is the Dark Arrival / TweenKin First Breach tutorial slice
- if save data is present, Play Game immediately continues the last stable checkpoint
- checkpoints are cross-timeline and preserve district state changes caused by other protagonists

## Actor Prefab Contract

- Moe: light sidearm gunplay, flashlight cone management, desperate close-range scrapping, and recoil-heavy finishers; traversal focus: door breaching, ledge vaulting, flashlight tracing, shove interactions, and grounded urban scrambling; 12 animations: idle, walk, run, aim_reticle, flashlight_scan, quickdraw, pistol_fire, reload, dodge_roll, vault, inspect, hold_interact
- Yil: rune-charged casts, turret sigils, reality hinge repairs, area denial glyphs, and burst-navigation spells; traversal focus: blink stepping, levitation rails, rune climbing, machinery bridging, and magical short-range glide control; 12 animations: idle, walk, run, aim_spell, wrench_cast, sigil_burst, ward_raise, blink_step, glide_rune, mechanic_climb, inspect, hold_interact
- Lou: telepathic domination, enemy hijack chains, crowd steering, stealth disruption, and evidence-tagging misdirection; traversal focus: all-surface climbing, vent slipping, pipe swinging, perch hopping, and remote interaction through mind-thread focus; 12 animations: idle, walk, run, aim_focus, telepathic_mark, mind_puppet, command_release, wall_climb, ceiling_traverse, perch_leap, inspect, hold_interact

## Environment Contract

- 3D city geometry assembled from sprite-built prefabs and artificially photographed surface textures
- districts include city blocks, sewers, abandoned factories, docks, transit ruins, reliquaries, and civic towers
- every interaction surface supports dedicated VFX and an interaction classification in the manifest

## Tutorial Slice Contract

- new-game boot opens with a multi-character tutorial slice that teaches Moe, Yil, and Lou in sequence before converging them
- the tutorial introduces Dark as a contiguous city and names the invading TweenKin as the first legible threat layer
- movement, combat, interaction, map, and timeline state rules are taught through one shared controller grammar rather than disconnected bespoke modes
- the tutorial exits into free-roam only after the player has used direct combat, magic traversal, telepathic manipulation, rescue interactions, and district orientation tools

## Title Screen Direction

- sketchy, rusty, blood-red lettering for Kin Dark
- blackened city silhouette and damp paper texture underlay
- no extra menu nesting at boot
