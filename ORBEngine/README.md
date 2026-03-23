# ORBEngine

ORBEngine stands for OrbitalRenderBreathing.

ORBEngine is the planned standalone runtime and tooling stack for OrbSeeker and other projects that require a 2D-authored world to be presented as a pseudo-3D recursive-space experience.

## Mission

ORBEngine is being prepared as a specialized engine for:
- Mode-7-inspired traversal and ground warping,
- multi-layer parallax depth simulation,
- recursive space-within-space rendering,
- 2D asset ingestion with 3D-feeling presentation,
- and collision/physics logic derived from authored art boundaries.

## Core Idea

The engine treats the world as a hierarchy of spaces. Each space can contain subspaces that remagnify and recurse back into higher-order spaces through controlled transform relationships. Rendering and simulation are pipelined through this hierarchy so the player experiences dimensional rotation, scale shifts, and impossible-looking spatial continuity while the underlying asset source remains 2D.

## Rendering Status

Current sandbox rendering now includes:
- recursive space traversal from the authored space graph,
- Mode-7-inspired floor warping built from scanline bands instead of mesh geometry,
- nested child-space viewports derived from parent-child space relationships,
- per-space breathing scale modulation,
- per-space orbital motion for recursive pocket placement,
- and entity projection that gives 2D-authored objects a pseudo-3D depth feel.

This is still a debug renderer, but it is now a real engine-side render pipeline instead of a placeholder scene mockup.

## Physics Status

Current sandbox simulation now includes:
- per-space physical environment values such as gravity, density, pressure, and ambient temperature,
- per-entity multiscale body state from subatomic and molecular regimes up through human-scale bodies,
- deterministic force accumulation using gravity, electrostatic interaction, short-range cohesion/repulsion, drag, and thermal agitation,
- anchored-body integration so authored scenes remain stable while still being physically active,
- open-arena enemy motion driven by the same effective physical model,
- and render feedback from simulated energy/coherency metrics.

This is an effective multiscale game-physics model grounded in real formulas and constants. It is not a literal full-universe solver.

## Initial Deliverables

1. Recursive render-space graph.
2. 2D asset import pipeline for `.swf`, `.piskel`, and `.clip` source workflows.
3. Green-outline collision-boundary extraction.
4. Deterministic recursion-aware collision and physics pipeline.
5. OrbSeeker-first sandbox scene.
6. Island shore raft gate into the combat simulator.
7. Beneath-island agriculture sandbox.
8. Three combat simulator modes: Tactical, QTE, and Open.

## Current Prep Files

- `README.md`.
- `ORBEngine_ARCHITECTURE.md`.
- `ORBEngine_DEVELOPMENT_PLAN.md`.
- `ORBEngine_FULL_TODO.md`.
- `include/orbengine.h`.
- `src/orbengine.c`.
- `src/orbengine_sandbox.c`.
- `src/orbengine_tutorial_demo.cpp`.
- `src/innsmouth_island_demo.cpp`.

## Current Sandbox Controls

- `R`: travel by raft from the island shore to the combat simulator gate.
- `G`: toggle the beneath-island agriculture complex view.
- `1`: Tactical simulator.
- `2`: QTE simulator.
- `3`: Open simulator.
- `ESC`: return to the island root view.

## Build

MSVC Developer PowerShell:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH\ORBEngine
cl /EHsc /DUNICODE /D_UNICODE /I include src\orbengine.c src\orbengine_sandbox.c user32.lib gdi32.lib gdiplus.lib msimg32.lib
```

MinGW g++:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH\ORBEngine
C:\tools\msys64\mingw64\bin\g++.exe -std=gnu++17 -municode -I include src\orbengine.c src\orbengine_sandbox.c -lgdiplus -lgdi32 -luser32 -lmsimg32 -o orbengine_sandbox.exe
```

Run:

```powershell
.\orbengine_sandbox.exe
```

## Standalone Tutorial Demo

The tutorial/combat vertical slice lives in its own source file and builds to a separate executable so the core ORBEngine sandbox stays untouched.

MinGW build:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH\ORBEngine
C:\tools\msys64\mingw64\bin\g++.exe -municode src\orbengine_tutorial_demo.cpp -lgdiplus -lgdi32 -luser32 -o orbengine_tutorial_demo.exe
```

Or use the dedicated build script:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH\ORBEngine
.\build_tutorial_demo.ps1
```

Run:

```powershell
.\orbengine_tutorial_demo.exe
```

The standalone demo expects the generated Recraft images to be present under `assets\recraft_demo\`.

## Standalone InnsmouthIsland Demo

The larger controller-driven InnsmouthIsland slice is also isolated from the core ORBEngine sandbox and builds to its own executable.

MinGW build:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH\ORBEngine
C:\tools\msys64\mingw64\bin\g++.exe -municode src\innsmouth_island_demo.cpp -lgdiplus -lgdi32 -luser32 -lshell32 -o innsmouth_island_demo.exe
```

Or use the dedicated build script:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH\ORBEngine
.\build_innsmouth_island.ps1
```

Run:

```powershell
.\innsmouth_island_demo.exe
```

The InnsmouthIsland demo expects the generated Recraft images to be present under `assets\innsmouth_island\`.

## Standalone InnsmouthIsland Research Demo

The benchmark-informed research branch is isolated in its own source file and executable so cited public-asset benchmarking, provenance discipline, and research-facing notes do not overwrite the main InnsmouthIsland demo path.

MinGW build:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH\ORBEngine
C:\tools\msys64\mingw64\bin\g++.exe -municode src\innsmouth_island_research_demo.cpp -lgdiplus -lgdi32 -luser32 -lshell32 -o innsmouth_island_research_demo.exe
```

Or use the dedicated build script:

```powershell
cd C:\Users\rrcar\Documents\drIpTECH\ORBEngine
.\build_innsmouth_island_research.ps1
```

Run:

```powershell
.\innsmouth_island_research_demo.exe
```

Supporting research artifacts for this branch live under `ORBEngine\reports\` and `drIpTECH\ReCraftGenerationStreamline\`, including the public benchmark report, bibliography, and the per-asset provenance ledger.
