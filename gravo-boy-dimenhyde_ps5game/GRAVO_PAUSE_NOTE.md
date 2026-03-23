# Gravo Pause Note

Date: 2026-03-11

Current executable state:
- `gravo_demo.exe` builds from `build_gravo_demo.ps1`.
- `gravo_demo.cpp` hosts the standalone ORBEngine kernel entry point.
- `gravo.c` contains the current runtime slice.
- `egosphere` now exposes `MindSphereRivalary` and Gravo consumes it for tracked rivals.

Current playable slice:
- First biome loop: Street of Grievances.
- Player movement and traversal are active.
- Medicine Glass mirror shrine is interactive.
- Three rivals move in real time using EgoSphere-backed threat logic.
- HUD overlays expose biome, narrative beat, shrine state, and rival threat.

Working design direction:
- Surreal action-horror with bossless exploration and escalation.
- Beamshot Eye for ranged pressure.
- Beamsword for melee spacing and poise play.
- Mirror shrines as respite, progression, reflection, and growth checkpoints.
- Nightmare effigies and memory constructs instead of literal real-world targets.
- MindSphereRivalary should be the persistent enemy-social layer across all biomes.

Immediate next production phase after art intake:
1. Integrate incoming concept sheets into a coherent asset inventory.
2. Lock Gravo visual language, enemy families, and biome identity per zone.
3. Generate the broad Recraft completion pass from the approved intake set.
4. Wire the resulting assets into `gravo.c` / `gravo_demo.cpp` and the ORBSystems pipeline.

Important constraint:
- Do not attempt to preserve or reintroduce overdose/revenge-on-real-people framing. Keep the project centered on hallucinated nightmare constructs, restraint, accountability, and psychological surrealism.