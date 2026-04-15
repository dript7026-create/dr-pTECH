# Ryzom Core Clean-Room Analysis

## Purpose

This document captures a legal-safe, engineering-focused analysis of the public Saga of Ryzom / Ryzom Core project so this workspace can learn from its scale, service boundaries, tooling, and world-simulation patterns without reusing its protected code, assets, lore, names, data files, or game-specific content.

## Scope And Boundaries

- Source examined: public official site material and the public `ryzom/ryzomcore` repository.
- Intended use: architecture study, systems decomposition, production-process lessons, and design heuristics.
- Not allowed for a proprietary game: copying AGPL source into the product, reusing CC-BY-SA or FAL art, cloning factions/lore/setting/species, copying quests/content/data sheets, or training internal models directly on protected assets for imitation output.
- Safe use: extract abstractions, service patterns, pipeline structure, simulation concerns, content-authoring workflow lessons, and performance/operability ideas.

## Public Facts Observed

- Ryzom Core is the community open-source codebase related to the MMORPG Ryzom.
- Repository scope includes client, server, tools, and content/build pipeline components.
- Main language mix is dominated by C++ with supporting PHP, Lua, C, HTML, and pipeline scripts.
- Source code is AGPL-3.0.
- Art assets are released under share-alike style licenses, not suitable for direct inclusion in a closed proprietary product.
- The codebase is organized as a full MMO stack rather than a single monolith.

## Structural Readout

Top-level public structure indicates several major pillars:

- `nel/`: core engine and foundational libraries.
- `ryzom/`: game-specific client, server, shared code, and tools.
- `studio/`, `tool/`, `web/`: tooling, support surfaces, and operational interfaces.
- `snowballs2/`: a smaller game/module showing reuse of engine/network infrastructure.

Within the game stack:

- `ryzom/common/src/game_share`: shared gameplay and protocol-adjacent definitions.
- `ryzom/client`: client runtime.
- `ryzom/server/src`: service-oriented MMO backend.
- `ryzom/tools`: authoring, installers, generators, exporters, sheet/random/content tools.

## Server Architecture Pattern

The public server tree suggests a service-oriented MMO backend composed of many executables instead of one giant process. Observed service categories include:

- AI service
- AI data service
- backup service
- entities game service
- frontend service
- input/output service
- naming service
- welcome service
- logger and monitor services
- mail/forum and admin-oriented services
- mirror and persistence-related support modules

What this implies:

- World simulation is decomposed into bounded services.
- Shared contracts live in common server/game-share libraries.
- Operational concerns like patching, backups, monitoring, and admin control are treated as first-class systems.
- MMO scale is handled through separation of concerns rather than a single game-server binary.

## AI And World Simulation Pattern

The public code layout strongly suggests a layered AI stack:

- World-map and pathing data are prebuilt offline.
- AI data files are scanned, compiled, and loaded into runtime services.
- Runtime AI references continents, regions, roads, cells, zones, fauna populations, NPC groups, and spawn points.
- Distinct managers exist for fauna, NPCs, players, pets, and outpost-like structures.

Important engineering lesson:

- High-scale MMO AI is not authored purely as code. It depends on a data pipeline that converts authored primitives into optimized runtime representations.

Useful abstraction for this workspace:

- Authoring format -> compiled world graph -> runtime shard cache -> live manager processes.

## Content Pipeline Pattern

The repository exposes a mature build-data pipeline with multiple staged scripts such as setup, export, build, install, client-dev, shard-data, and shard-dev phases.

That indicates a repeatable content pipeline with these characteristics:

- Authoring and source assets live separately from runtime-ready assets.
- World, AI, collision, and packed-zone data are built offline.
- The same content goes through different packaging/install targets for client and shard/server.
- Tooling generates configuration files and directory layouts automatically.

This is one of the strongest takeaways. Game quality at MMO scale comes as much from pipeline reliability as from engine features.

## Tooling Pattern

Public tool directories indicate support for:

- level design
- translation/localization
- installer/client distribution
- world editing
- content generation and randomization
- patch generation
- build-world and AI world-map compilers
- sheet packing and content processing

The key lesson is that high-end MMO production is tool-led. The runtime is only one slice of the system.

## Quality Signals Behind The Project

The project exhibits traits that correlate with production-grade MMO quality:

- long-lived build system with CMake and packaging support
- separate client/server/tools composition
- offline baking of heavy data sets
- world and AI compilation steps
- explicit backup, patch, installer, and repository management
- support for monitoring, logging, testing, and admin control

These are more important to emulate than any specific combat rule or lore device.

## Clean-Room Lessons To Reuse

### 1. Separate Engine, Game, And Pipeline

Adopt three layers in your proprietary stack:

- Core engine/runtime layer
- Game rules and content layer
- Build/import/analysis pipeline layer

Do not let content formats be hardcoded into the engine.

### 2. Build The MMO As Services

Recommended proprietary service partition:

- gateway service
- identity/account service
- shard/session coordinator
- world simulation service
- entity/state service
- combat/ability service
- ecology simulation service
- AI orchestration service
- chat/social service
- analytics/event service
- persistence and backup service
- patch/content delivery service

### 3. Make World Data Compiled, Not Hand-Parsed At Runtime

Use an offline compiler pipeline for:

- navigation meshes or world graphs
- spawn ecosystems
- biome/ecology descriptors
- encounter graphs
- quest topology
- collision and packed world data
- localized text bundles

### 4. Treat Live Operations As Product Features

Plan for:

- telemetry
- admin dashboards
- patch rollouts
- data versioning
- backups and restore drills
- simulation replay or audit trails

### 5. Build A Shared Schema Library

Maintain a neutral schema package used by tools, services, and clients for:

- entity IDs
- messages/events
- stat definitions
- world tags
- behavior trees or utility-AI descriptors
- inventory and crafting schemas

## Translation Into This Workspace

For this workspace, the useful target is not “make a Ryzom clone.” The useful target is:

- a proprietary MMO framework with a data-first world simulation pipeline
- adaptive historical modeling for gameplay events
- a distinct setting, faction graph, ecology, and combat vocabulary
- clean separation between authored knowledge and learned/systemic inference

## Proprietary Adaptation Proposal

### Proposed Product Shape

Build a new MMO platform around these modules:

- `DoENGINE` or another internal runtime as the real-time simulation base
- `egosphere` as the player/world state memory and event topology layer
- `godai` as the elemental or systemic balancing grammar
- a new content compiler pipeline for zones, ecosystems, NPC populations, behaviors, and live events

### Mapping To Godai

Use `godai` as a balancing coordinate system, not as borrowed game content. One possible structure:

- Earth: durability, infrastructure, persistence, logistics
- Water: adaptation, flow, trade, healing, migration
- Fire: aggression, transformation, conflict, risk
- Wind: mobility, communication, stealth, scouting
- Void: memory, anomaly, cognition, myth, simulation drift

Every authored system can project onto a Godai vector:

- biome
- creature archetype
- faction temperament
- spell family
- item material
- settlement style
- world-event type

## Mapping To Egosphere

Use `egosphere` as historical player/world memory. Recommended event model:

- player action events
- encounter outcomes
- travel and route preference
- trade flows
- guild/faction influence shifts
- biome pressure and extraction intensity
- social graph interactions
- world-state deltas

From that event log, derive:

- persistent player affinity vectors
- regional pressure metrics
- ecology stress scores
- faction sentiment heatmaps
- procedural content weighting inputs
- adaptive quest surfacing

## Adaptive Neuronal Mapping Recommendation

Do not frame this as “train on Ryzom assets.” Frame it as:

- ingest your own telemetry and authored taxonomy
- learn embeddings over player behavior, place identity, encounter sequences, and economic movement
- use those embeddings to bias future content selection and world response

Recommended model layers:

1. Event ontology
2. Feature extraction over sessions, regions, actors, and economies
3. Embedding model for player-style and region-state similarity
4. Policy layer that chooses adaptive content weights
5. Safety/rule layer that enforces authored boundaries

Example event schema:

- actor_id
- party_id
- shard_id
- zone_id
- biome_id
- godai_vector
- action_type
- target_type
- difficulty_band
- result_state
- reward_vector
- social_context
- timestamp

## What To Emulate Versus What To Avoid

Emulate:

- service decomposition
- offline world and AI compilation
- strong tooling and data pipeline discipline
- shared schema libraries
- operational services as first-class components
- world-state and AI authored through data

Avoid:

- copying names, factions, map structures, species, or lore
- copying exact service interfaces or code organization verbatim
- importing AGPL code into proprietary modules
- using share-alike assets as placeholders in a closed pipeline
- reproducing the exact progression, resource, or ecology vocabulary of Ryzom

## Visual Craft Study

This section is about craft, not imitation. The goal is to understand why the presentation reads as commercially credible and alive, then build an original proprietary look that reaches similar quality without inheriting protected expression.

### High-Level Visual Read

From public-facing material, the strongest visual impression is not raw polygon complexity. It is coherence.

The look appears to be built from a few stable principles:

- environments are large, legible, and ecosystem-first
- cultures read through silhouette and material bias more than through noise-detail
- creatures feel anchored to habitat and behavior, not just arbitrary fantasy decoration
- animation and ecology presentation sell the world as living even when geometry is relatively restrained

That matters. A release-quality MMO look does not require copying a specific shape language. It requires internal consistency between biome, architecture, costume, fauna, and motion.

### How Details Appear Rich Without Looking Random

The detail strategy appears to follow a layered hierarchy:

- primary read: silhouette and massing
- secondary read: material breakup and large surface rhythms
- tertiary read: trims, accessories, bone plates, leaf forms, straps, masks, tools, and surface accents

The practical lesson is that “richness” is not achieved by filling every surface. It is achieved by controlling where detail density rises and falls.

Use this hierarchy in proprietary assets:

- keep heads, shoulders, hands, weapons, and faction-signaling zones high-clarity
- keep torso and limb masses readable from distance
- reserve micro-detail for focal areas and close camera states
- make large forms carry identity before texture does

### Proportion Techniques That Create Credibility

Public material suggests a believable stylization rather than extreme caricature. The proportions likely read as grounded because of the following traits:

- bodies stay within a plausible humanoid envelope even when culturally distinct
- height, width, and costume silhouette vary enough to separate groups at distance
- tools and weapons are readable but not absurdly oversized
- architecture uses structural rhythm and repeated modules to imply real construction
- flora and fauna use believable weight distribution even when exotic

For an original proprietary art bible, use these proportion rules:

- characters: preserve functional locomotion proportions first, stylize second
- creatures: design around locomotion logic, feeding logic, and rest posture
- settlements: express culture through support logic, openings, rooflines, bridges, and circulation routes
- props: exaggerate usage points, grip points, and load-bearing parts rather than arbitrary ornament

### Material And Surface Logic

The public presentation reads as convincing because materials seem to communicate origin and use:

- plant-grown forms look tensioned, layered, fibrous, or waxy
- crafted artifacts look assembled, reinforced, bound, or plated
- hostile or corrupted zones read through palette, contrast, and shape stress rather than only texture swap

To achieve a similarly strong result without derivation:

- build your own material families tied to `godai`
- define each family by edge behavior, reflectance range, fracture pattern, and wear pattern
- ensure every biome has a dominant substrate, a secondary accent material, and a rare anomaly material

Example proprietary material families:

- Earth: compacted mineral shell, terraced stone-bark, ceramic ash composite
- Water: pearl-fiber laminate, translucent gel resin, driftwood membrane
- Fire: ember-glass crust, heat-blued alloy, soot leather
- Wind: reed lattice, feathered membrane cloth, tension-cable bamboo analog
- Void: iridescent matte skin, interference glaze, memory-scar crystal

### Color And Atmosphere Principles

One public strength is ecosystem separation through environmental color scripting. The world reads as a set of distinct climatic identities.

For a proprietary equivalent:

- assign each region a climate palette, a social palette, and a danger palette
- let weather shift saturation and value, not just fog color
- keep creature accent colors partially ecosystem-bound so wildlife feels evolved for place
- reserve unnaturally high contrast for anomalies, sacred zones, elite enemies, or world events

### Animation Pipeline Lessons Visible In The Open Source Code

The public codebase strongly suggests a mature skeletal animation pipeline with:

- explicit skeleton files and animation sets
- modular character assembly from parts bound to a skeleton
- channel-mixer style animation playback and transition management
- animation playlists for runtime sequencing
- bone-specific controls for head/chest and attachment points
- blink handling and other small facial or upper-body life cues
- character LOD that can replace full skinned meshes with compact animated representations

The important lesson is not the exact implementation. It is the production model:

- rig once
- attach many interchangeable parts
- play stateful animation sets
- preserve character readability at long distance with dedicated animation-aware LOD

### Motion Techniques That Create A Sense Of Life

The public descriptions emphasize “realistic and dynamic animal motions,” migrations, predators attacking herds, prey defense, and species-specific behavior. That implies the feeling of life comes from layered motion systems, not only from authored attack animations.

Release-quality “aliveness” usually comes from these techniques:

- anticipation before major action
- overshoot and settle after turns, stops, and impacts
- gait-specific vertical motion in pelvis, shoulders, and head
- secondary motion in cloth, tools, antennae, tails, ears, crests, or hanging ornaments
- idle variance driven by breath, scanning, weight shift, grooming, or attention cues
- asynchronous group behavior so crowds do not pulse in lockstep
- locomotion matched to mass and terrain rather than a generic run cycle

### Creature Animation Heuristics

For proprietary fauna that feels comparably alive:

- define a rest pose, alert pose, flee pose, feed pose, and threat pose for every species
- give every species a turn signature: pivot, skid, hop, coil, crab-step, glide, or bound
- make predators commit weight forward and prey reserve fast lateral escape
- use head lead and spine follow so bodies feel articulated, not rigid
- introduce short observational micro-actions between locomotion states

### Human And Humanoid Animation Heuristics

For playable characters and NPCs:

- separate lower-body travel from upper-body intent where possible
- keep weapon handling and tool handling as distinct stance families
- use chest, neck, and eye-line orientation to express attention before full-body turn
- vary idle loops by role: guard, laborer, scholar, scout, ritualist, merchant
- keep combat readability stronger than realism during gameplay-critical frames

### Detail Generation Rules For Original Assets

To generate assets “fit to release alongside” a game of this class while remaining fully non-derivative, encode detail rules instead of copying shapes.

Recommended generator inputs:

- biome
- culture or faction
- godai vector
- function class
- wear level
- status tier
- ritual versus industrial bias
- ecology pressure

Recommended generator outputs:

- silhouette family
- material stack
- seam and joint pattern
- ornament density map
- color blocking plan
- animation tag set
- damage and weathering masks

### Clean-Room Art Direction Constraints

For legal and creative safety, enforce these rules:

- never train a generator to imitate named Ryzom factions, races, costumes, or creatures
- never use Ryzom textures, models, turnarounds, or rendered screenshots as direct source material for production assets
- never reuse naming prefixes, kit structures, or iconic silhouette combinations unique to that IP
- derive your asset rules from original taxonomy authored in this workspace

### Proprietary Replacement Strategy

If the target is comparable quality with distinct identity, the replacement strategy should be:

- keep the ecosystem-first readability
- replace the entire lore, biology, architecture, and costume ontology
- map every asset family to `godai` and `egosphere` states
- drive micro-variation from your own event history and region memory
- author your own skeleton standards, equipment sockets, and animation state machine vocabulary

### Direct Application To This Workspace

Use `egosphere` history to drive visible world memory:

- migration wear on routes
- faction banners and repairs after conflict
- ecology stress changing creature posture and color accents
- settlement props changing with trade and scarcity

Use `godai` to drive art and motion identity:

- Earth-heavy entities move with compression, pause, and grounded recovery
- Water-heavy entities move with flow, lag, and elastic follow-through
- Fire-heavy entities move with sharp acceleration and aggressive pose line
- Wind-heavy entities move with directional feints and reduced contact time
- Void-heavy entities move with timing irregularity, phase offsets, and uncanny stillness

## Release-Safe Visual Conclusion

The strongest lesson from studying the craft is that the sense of reality comes from alignment between:

- silhouette
- material logic
- ecosystem identity
- behavior ecology
- layered animation
- distance readability

That can be reproduced in quality without reproducing any protected expression. Build a new ontology, new proportions, new material families, new motion grammar, and new environmental history system, and the result can stand beside an MMO of this class while remaining wholly proprietary.

## Suggested Workspace Deliverables

To convert this research into usable internal assets, build these original documents and systems next:

- proprietary MMO service map
- event ontology for egosphere
- Godai balancing schema
- zone/ecology compiler spec
- AI population authoring format
- telemetry and adaptive-response design
- live-ops patch and backup architecture

## Immediate Technical Backlog

### Foundation

- Define canonical entity/event schema.
- Define shard, region, biome, faction, ecology, and encounter IDs.
- Define message bus contracts between runtime services.

### Toolchain

- Create a content compiler for zones, nav, spawn tables, and ecology descriptors.
- Create editors or text/JSON/YAML authoring formats with validators.
- Create deterministic packaging for client and shard data.

### Runtime

- Implement world state service.
- Implement ecology simulation service.
- Implement AI orchestration service.
- Implement telemetry/event ingestion service.
- Implement replayable audit log for adaptive systems.

### Intelligence Layer

- Build embeddings from gameplay history.
- Add regional memory and player-style clustering.
- Feed cluster outputs into authored content selectors, not raw generation.

## Recommendation For Proprietary Safety

Use a clean-room workflow:

- Research team produces abstract design notes only.
- Implementation team does not copy code or assets.
- Keep a provenance record for every reused idea.
- Tag anything derived from public research as “conceptual only.”
- Keep generated content grounded in your own ontology, names, art direction, and mechanics.

## Bottom Line

Ryzom Core is valuable here not as a template to copy, but as proof that MMO quality comes from:

- strong service boundaries
- robust content compilers
- world/AI data pipelines
- shared schemas
- serious live-ops infrastructure

If this workspace wants equivalent quality with fully proprietary IP, the right move is to adopt those production patterns while building a completely new ontology, simulation grammar, visual language, and adaptive-history layer around `godai` and `egosphere`.