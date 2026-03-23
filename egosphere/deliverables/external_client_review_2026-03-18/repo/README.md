# egosphere

Reusable C AI/gameplay module for lightweight psyche modeling, replay learning, and persistent rival-memory systems grounded in gameplay telemetry, consequence history, and cross-entity resonance state.

Intent:

- Make `egosphere` the shared AI/gameplay cognition layer for drIpTECH projects rather than a one-off demo.
- Keep the core portable and dependency-light so it can drop into small C runtimes, prototypes, and engine-side gameplay modules.
- Provide a practical middle layer between simple reactive NPC logic and heavyweight external ML stacks: memory-shaped action choice, replay learning, persistent rival adaptation, and systemic behavior histories.
- Support game-facing integration first: saveable rivals, inspectable state, configurable planner sizing, and smoke-testable behavior.

Build:

```sh
gcc -std=c11 -O2 -Wall -o demo egosphere.c demo.c -lm
```

Run:

```sh
./demo
```

Files:

- `egosphere.h` — public API and types
- `egosphere.c` — implementation (id / ego / superego tiers, memory, replay, Q-learning, DQN, rival persistence)
- `demo.c` — tiny runner that simulates an agent and save/load roundtrip

Module coverage:

- Agent psyche model with memory-backed decision shaping.
- Prioritized replay buffer and tabular Q-learning helpers.
- Simple linear DQN approximator with no external ML dependencies.
- Configurable `MindSphereRivalary` persistent rival layer for recurring enemy state.
- Tactical history metrics: move usage, successful tactics, combo-chain preferences, and pressure/counter/spacing tendencies.
- Moral history metrics: dialogue leaning, mercy, duty, candor, ambition, and downstream consequence memory.
- AntithEntity actor profiles: player/NPC personality, intellect, and ethical genome traits persisted inside MindSphere state.
- Consciousness spectrum and resonance links: unconscious/subconscious/conscious pulls, discovery drive, shared frequency bands, and per-rival player resonance.
- Dormant narrative hooks: revelation, alliance, rupture, ending, and omen pressures that can stay inactive until a game decides to consume them.
- Binary save/load helpers: `mindsphere_save(...)` and `mindsphere_load(...)`.
- Replay rehearsal helpers: `mindsphere_rehearse_rival(...)` and `mindsphere_rehearse_all(...)` to train planners from stored outcomes.
- Dialogue and consequence hooks: `mindsphere_record_dialogue_choice(...)` and `mindsphere_record_consequence(...)`.
- Save inspector/export utility: `tools/inspect_mindsphere_save.py`.
- Executable smoke test via `make smoke-test`.

Design guardrails:

- Keep rival identity grounded in measurable play history: move usage, tactic success/failure, combo chaining, spacing, pressure, counterplay, and encounter outcomes.
- Feed narrative state through the same simulation layer by recording dialogue leaning and downstream consequences rather than maintaining a separate scripted morality track.
- Prefer world-state accumulation over hierarchy mechanics: recurring characters should feel authored by history, not by rank ladders or title promotion loops.
- Keep the system decentralized: player profile, antithentity self-models, resonance links, and dormant narrative pressure should accumulate locally rather than depend on a single global director state.
- Treat combat, dialogue, and consequence data as one system so minute choices can propagate through later behavior in a mechanically legible way.
- Treat external IP references as negative guidance only: study them for contrast or risk avoidance, then push the result into original egosphere-specific terminology and new conceptual directions rather than copying wording, taxonomies, progression semantics, or concept-linked framing. Shared real-world causal principles can remain, but only inside a distinctly re-authored egosphere design philosophy.
- Let lore drive specialization: faction history, local cosmology, environmental pressures, and remembered consequences should determine how new subsystems are framed and differentiated instead of adding abstract mechanics that sit outside the world model.

Common workflow:

```sh
gcc -std=c11 -O2 -Wall -o demo egosphere.c demo.c -lm
./demo
python tools/inspect_mindsphere_save.py egosphere_rivals.dat --full
make smoke-test
```

Notes:

- Use `mindsphere_default_config()` and `mindsphere_init_with_config(...)` when a project needs more than the default 16-state / 3-action planner.
- Use `mindsphere_seed_player_profile(...)`, `mindsphere_record_player_style(...)`, and `mindsphere_record_player_choice(...)` if the player should participate in the same systemic mind model as recurring NPCs.
- Use `mindsphere_add_antithentity(...)` if you want the public gameplay vocabulary to stay centered on antithentities while still using the same runtime object as a rival identity.
- Enable `config.narrative_protocol_enabled` when the game is ready to consume dormant narrative pressure from `mindsphere_collect_narrative_hooks(...)`.
- Use `mindsphere_rehearse_rival(...)` after enough outcomes accumulate if you want rivals to learn from stored replay rather than only from online updates.
- Use `mindsphere_record_dialogue_choice(...)` and `mindsphere_record_consequence(...)` to feed non-combat world-state into rival identity, so combat behavior and narrative stance evolve from the same history.
- `mindsphere_load(...)` is intended for a zero-initialized or already-freed `MindSphereRivalary` destination.
- The demo writes a local `egosphere_rivals.dat` file to prove the persistence path.
