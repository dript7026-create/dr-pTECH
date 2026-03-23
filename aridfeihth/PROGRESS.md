# Aridfeihth Progress

Checkpoint saved: 2026-03-13 research foundation

- Established `aridfeihth` as a new design-focus workspace folder because no existing `aridfiehth` or `aridfeihth` project directory was present in the repo.
- Completed a text-first research pass using public Wikipedia articles on *Castlevania: Aria of Sorrow* and *Castlevania: Dawn of Sorrow*.
- Converted the useful structural lessons into an original gameplay direction rather than cloning content, terminology, encounters, maps, or story beats.
- Replaced enemy-soul collection with a `SimIAM` pet-bonding framework centered on rescue, trust, growth, and squad composition.
- Wrote a tracked research dossier with citations, references, and bibliography for future development guidance.

Checkpoint saved: 2026-03-13 IllusionCanvasInteractive vertical-slice scaffold

- Added a standalone `IllusionCanvasInteractive/` runtime with a native `.iig` file type for `illusioninteractivegame` bundles.
- Implemented a Tkinter-based prototype app, validated `.iig` loader/saver, `godAI` conductor, EgoSphere bridge, combat loop, and ORB-inspired projection helpers.
- Added `aridfeihth/ARIDFEIHTH_GAMEPLAY_SYSTEMS.md` to define the full gameplay loop, combat logic, boss logic, and the roles of EgoSphere and `godAI`.
- Created an `aridfeihth` vertical-slice `.iig` sample covering refuge play, route gating, SimIAM rescue, and bond-weave combat flow.
- Extended the clip-blend-id-do path so it can emit IllusionCanvas runtime outputs alongside DoNOW and idTech2 artifacts.

Checkpoint saved: 2026-03-13 native EgoSphere bridge and studio pass

- Expanded the sample `aridfeihth` route into a fuller vertical slice with a dedicated boss chamber and authored bond-weave requirements.
- Replaced the earlier bridge-only EgoSphere path with a native `ctypes` bridge that can load or auto-build `egosphere.dll` from the existing C source.
- Added a standalone `.iig` authoring utility so IllusionCanvasInteractive can edit, save, and run bundles instead of only consuming them.

Checkpoint saved: 2026-03-13 tutorial demo authoring and post-sanctum branch

- Upgraded the sample from a strict vertical slice into a fuller tutorial demo with a named tutorial-demo title, richer milestone chain, and a post-sanctum authored branch.
- Added `Reliquary Bazaar` and `Atlas Choir` to carry the merchant-shell and map-shell art into actual playable room content instead of leaving them as unused generated assets.
- Fixed an engine regression in enemy AI so the current slotted `EnemyState` no longer attempts to mutate an undeclared `y` field during simulation.
- Extended focused IllusionCanvas coverage with a post-tutorial route test so the widened authored branch stays reachable.
