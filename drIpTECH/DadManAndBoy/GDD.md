DadMan and Boy — Game Design Document
Version: 0.2
Date: 2026-03-09

Overview
- High Concept: DadMan and Boy is a 2.5D action-platformer blending cinematic single-player spectacle (inspired by God of War), quirky supernatural tone (Hellboy-esque), and asynchronous traversal/puzzle focus (a la Death Stranding). Players control two complementary characters — the hulking DadMan and the agile Boy — switching between them to solve environmental puzzles, traverse the world, and face encounters.

Top-Level Goals
- Create an emotionally resonant single-player experience with tactile physics interactions and emergent puzzle scenarios.
- Ship a focused MVP that demonstrates character complementarity and a memorable traversal puzzle.
- Build a pipeline that supports quick iteration of sprite-based art and modular levels for fast prototyping on PC and later porting to Switch2.

Core Pillars
- Complementary Play: Each character has distinct movement and interaction affordances that must be combined to progress.
- Tactile Interaction: Physics-forward object interactions (push/pull, carrying, levers) that produce emergent puzzle solutions.
- Atmospheric Tone: Surreal, slightly melancholic world with moments of humor and spectacle.
- Accessible Design: Responsive controls and adjustable difficulty to make puzzles approachable.

Core Loop
1. Inspect environment and identify obstacles.
2. Choose which character to control and use abilities to change world state.
3. Combine actions (DadMan moves heavy objects; Boy accesses tight spaces, manipulates small mechanisms) to open new areas.
4. Collect upgrades and narrative fragments; repeat with increased complexity.

Gameplay Systems (Overview)
- Character Abilities
	- DadMan: heavy interactions (push/pull, pick up crates, ground-pound/stomp to break fragile floors, carry Boy for reach), high HP, slower move speed.
	- Boy: agility (double-jump, climb, vault, squeeze through vents, throw small items), low HP, quick speed.
- Switching: instant switch between characters; active character performs actions while the other can be placed in a passive hold state (e.g., DadMan holds Boy on shoulders).
- Objects: weighted crates, levers, pulleys, fragile tiles, ziplines, one-way platforms, environmental hazards (water, steam vents).
- Puzzles: multi-step puzzles that require sequencing, timed coordination, and stateful objects; optional hidden solutions for collectibles.
- Combat: light, knockback-focused encounters; enemies are hazards that encourage strategic use of both characters rather than deep combat systems.

Narrative & Tone
- Premise: In a fractured coastal archipelago, DadMan and Boy are tasked with reconnecting isolated communities and restoring strange mechanical bridges. The story mixes quiet father-son beats, oddball supernatural encounters, and a sense of travel-as-repair.
- Delivery: World-building via environmental storytelling and collectible audio/text fragments. Short cinematic set pieces punctuate key milestones.

Art Direction
- Style: Stylized low-res 2.5D sprites with a detailed parallax background and a limited palette for mood. Motion should feel weighty for DadMan and snappy for Boy.
- Visual Language: Distinct silhouettes for interactable objects; readable foreground/background separation; color-coding for puzzle states.

Audio Direction
- Score: Sparse, atmospheric motifs with occasional rhythmic pulses for traversal sequences.
- SFX: Distinct cues for heavy interactions, jumping, and successful puzzle completions. Implement spatialized audio where possible.

Platform & Tech
- Primary target: Nintendo Switch 2 (research required for devkit access). Secondary: PC for prototyping.
- Prototype engine: SDL2-based C/C++ prototype or Unity/Evo-lite depending on lead dev preference. Priority: deterministic physics for puzzle reliability.
- Asset pipeline: leverage existing `tommybeta` tools for sprite repalettizing and atlasing; standardize export formats for prototype engine.

Accessibility
- Options for simplified puzzles, toggleable hints, adjustable input sensitivity, remappable controls, and UI scaling.

Scope & MVP
- MVP scope (6 weeks):
	- Basic movement & switching implemented.
	- One biome with 4–6 puzzle rooms showcasing core mechanics.
	- One enemy type and minimal combat interactions.
	- Basic audio and UI (save/load, HUD).

Milestones (High-Level)
- Week 1–2: Prototype movement/switching and a single puzzle room; validate character feel on PC.
- Week 3–6: Build first biome, implement core puzzle objects, add collectibles and small audio palette.
- Week 7–12: Polish, add two more biomes, accessibility features, and prepare port/technical design for Switch2.

Risks & Mitigations
- Devkit access: prototype thoroughly on PC; document porting plan and keep code modular.
- Physics nondeterminism: lock physics step and write deterministic tests for puzzle states.
- Scope creep: prioritize MVP items and freeze feature additions until vertical slice is validated.

Next Immediate Tasks
- Expand puzzle design docs with 6 exemplar puzzles and object states.
- Create a control prototype in `DadManAndBoy/src` using SDL2 on PC.
- Set up `assets/sprites/proto` and integrate `tommybeta` repalettize tools to import placeholder art.

Owner: rrcrell

Change Log
- v0.2: Expanded structure, added pillars, systems, milestones, and next steps (2026-03-09).
