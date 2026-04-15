# HOMElair Architecture

## Intent

HOMElair is the central drIpTECH habitation engine: one hub that merges the workspace's engines, adaptive systems, authoring chains, and platform adapters into a single product-family architecture.

It should be understood as a system-of-systems runtime with clear internal ownership boundaries, not as one giant undifferentiated executable.

## Merger Rule

The workspace should not keep multiplying top-level flagship identities that overlap each other.

Inside HOMElair:

- DoENGINE becomes the hearth and orchestration layer.
- ORBEngine becomes the signature presentation and depth renderer.
- HOPE becomes the continuous frame-governance and recursion controller.
- EgoSphere becomes the local actor-memory and consequence layer.
- NeoWakeUP becomes the live AI conductor and world-state service layer.
- ArchesAndAngels becomes a campaign and pressure simulation module that feeds runtime worlds.
- Clip Studio, Blender, Recraft, readAIpolish, and egosphere synthesis become the forge pipeline.

The practical outcome is one central stack with multiple chambers instead of many unrelated top-level engine theses.

## Layer Model

### 1. Hearth Layer

Responsibility:

- package graph
- launch control
- runtime profile selection
- peer session routing
- backup and recovery
- telemetry and artifact index
- local-only trust boundaries and operator tools

Primary absorbed systems:

- DoENGINE packages/core
- DoENGINE packages/shared
- DoENGINE packages/telemetry
- workspace build and health tooling

Outputs:

- runtime profile manifest
- target selection state
- content and build registry
- peer-link session state

### 2. Lair Render Layer

Responsibility:

- world presentation
- scene composition
- depth-band placement
- pseudo-3D and full 3D coexistence
- UI overlays, tactical overlays, and sanctuary overlays
- display calibration hooks for HomeViuPlay and PlayHub

Primary absorbed systems:

- ORBEngine
- DoENGINE hybrid-engine work
- Illusion 3D and DODO rendering experiments

Target render expansion:

- full 3D static meshes for architecture and props
- full 3D landscape meshes for basins, plains, thresholds, and sanctuary terrain
- rigged character and creature model contracts
- billboard-only rendering kept as a secondary atmosphere layer rather than the primary world representation

Design rule:

- render in depth bands with foreground protection
- preserve clarity in the near field
- assign lower-frequency depth modulation to background and mid-field occlusion work

### 3. Breath Control Layer

Responsibility:

- frame-budget shaping
- recursion depth limits
- sanctuary stabilization
- input-to-render causality balancing
- matter-state and volumetric response
- tail-latency suppression
- comfort-aware display modulation

Primary absorbed systems:

- HOPE framework
- egosphere synthesis runtime metadata
- current KaijuGaiden HOPE bridge learnings

Key rule:

- HOMElair must treat performance, causality, and comfort as one controller, not three disconnected settings panels.

### 4. Mind Conductor Layer

Responsibility:

- live world-state
- actor cognition
- campaign pressure
- scenario progression
- directive APIs
- adaptive relationship state
- local simulation services and headless stepping

Primary absorbed systems:

- NeoWakeUP
- EgoSphere
- ArchesAndAngels
- selected NaVi and AI bridge modules where still useful

Outputs:

- runtime scenario packets
- actor-state packets
- campaign-pressure feeds
- adaptive recommendations for Hearth and Lair Render

### 5. Forge Pipeline Layer

Responsibility:

- authoring intake
- generated concept inputs
- refinement and polish
- mesh and bundle export
- translation between art tools and runtime contracts
- asset manifest validation

Primary absorbed systems:

- drIpTech_ClipStudio_Plug-Ins
- drIpTECHBlenderPlug-Ins
- ReCraftGenerationStreamline
- readAIpolish
- egosphere pipeline and synthesis tooling

Outputs:

- canonical content manifest
- render-ready bundles
- simulation-ready metadata
- platform-ready asset groups
- mesh-layer and texture-layer material profiles for future higher-fidelity surfaces

### 6. Vessel Adapter Layer

Responsibility:

- platform specialization without fragmenting the core stack
- device comfort profiles
- input routing and sensor abstraction
- local persistence and deploy packaging
- peer exchange and dock/undock transitions

Initial vessels:

- PlayHub
- NanoPlay_t
- HomeViuPlay
- host desktop runtime
- legacy handheld validation targets such as KaijuGaiden-style GB/GBA/NDS/3DS proof paths

Rule:

- vessels can constrain the stack, but must not fork the content contract.

## Product-Family Contract

### Shared Contract

Every HOMElair target should consume the same high-level contract:

- content identity
- runtime profile
- comfort profile
- depth profile
- simulation profile
- peer-link profile
- telemetry policy

### PlayHub Profile

- full dock and group-session support
- highest peer-link priority
- calibrated room-view depth display support
- broadest controller and accessory support
- strongest emphasis on living-room UX and social readability

### NanoPlay_t Profile

- portable-first thermal and battery governance
- reduced background simulation intensity
- reduced sensor assumptions
- offline-first caching and session continuity
- same save, world, and content identity as PlayHub

### HomeViuPlay Profile

- depth-display calibration and demonstration target
- detachable screen-plus-compute topology
- peer exchange, intermod, and monitor/dock transitions
- engineering-first instrumentation mode for validating the display field

## Depth Display Stack

HOMElair should explicitly model a depth display stack for HomeViuPlay and future PlayHub-compatible hardware.

The requested direction can be reframed as an exploratory depth-field display program:

- a crystal-sheet or layered refractive panel stack
- fluid or electroreactive depth sheet behavior
- magnetic or pulsed tuning to alter refractive layering
- inward z-axis impression through controlled layered occlusion rather than simple stereo separation

Software-side design consequences:

1. Scene output needs depth bands and comfort bands.
2. Foreground detail should remain high-clarity and low-noise.
3. Mid-field and background can carry the heavier depth illusion burden.
4. Breath Control should modulate depth intensity when congestion, fatigue, or noise risk increases.
5. HomeViuPlay calibration mode should expose per-band tuning rather than one global depth slider.

## Workspace Absorption Map

### Core to absorb directly

- DoENGINE
- ORBEngine
- NeoWakeUP
- EgoSphere and HOPE runtime layers
- egosphere synthesis pipeline
- ArchesAndAngels campaign-state logic

### Tooling to absorb as forge services

- Blender plug-ins
- Clip Studio plug-ins
- readAIpolish
- ReCraftGenerationStreamline
- idTech-facing plugin and bundle exporters

### Projects to keep as vessel proofs and content clients

- KaijuGaiden
- WialWohm
- orbseeker
- tommygoomba and related handheld experiments
- other game-specific runtime proofs

These projects should prove the HOMElair contracts, not redefine them.

## Implementation Sequence

1. Establish a HOMElair manifest schema.
2. Define the shared runtime shell and vessel profile schema.
3. Bind DoENGINE launch/orchestration into HOMElair Hearth terminology.
4. Bind ORBEngine render descriptors into HOMElair depth-band descriptors.
5. Bind HOPE runtime metadata into comfort, recursion, and depth-governance controls.
6. Bind NeoWakeUP and ArchesAndAngels outputs into the shared world-state contract.
7. Promote the existing authoring and synthesis tools into one Forge pipeline ledger.
8. Add PlayHub mode, NanoPlay_t mode, and HomeViuPlay calibration mode to the shell.

## Near-Term Deliverables

- HOMElair shell README and architecture package
- machine-readable subsystem map
- first shared manifest schema
- shell app scaffold under HOMElair
- ORBEngine depth-band prototype bound to HOPE comfort controls
- first full-3D preview scene with terrain mesh, character mesh, rig metadata, and environment depth bands
- PlayHub and NanoPlay_t runtime profile presets

## Constraint

HOMElair should reduce portfolio sprawl.

If a subsystem does not clearly strengthen Hearth, Lair Render, Breath Control, Mind Conductor, Forge Pipeline, or Vessel Adapters, it should stay project-scoped instead of being promoted into the central stack.
