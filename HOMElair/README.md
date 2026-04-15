# HOMElair

HOMElair is the proposed central drIpTECH engine and habitation hub.

It is not a replacement name pasted over every existing subsystem. It is the unification layer that absorbs the current workspace stack into one runtime family built for three connected product targets:

- PlayHub: the primary living-room and social dock target
- NanoPlay_t: the portable and modular handheld target
- HomeViuPlay: the detachable monitor-console precursor that proves the display, dock, and peer-link assumptions

## Purpose

HOMElair consolidates the current split between:

- ORBEngine as presentation runtime
- DoENGINE as orchestration and packaging controller
- HOPE and EgoSphere as adaptive cognition and frame-governance layers
- NeoWakeUP as AI runtime and state conductor
- authoring and synthesis pipelines across Clip Studio, Blender, Recraft, readAIpolish, and idTech-facing bundle tools

The result is a single engine-of-engines architecture with one shared contract for:

- authoring
- synthesis
- simulation
- runtime presentation
- platform adaptation
- telemetry and recovery

## HOMElair Stack

1. Hearth Core
   - boot, packaging, runtime selection, artifact registry, telemetry, peer-link session control
   - primary source: DoENGINE
2. Lair Render
   - signature presentation, depth staging, pseudo-3D and true 3D scene composition, UI and overlay routing
   - primary source: ORBEngine plus current DODO/Illusion 3D work
3. Breath Control
   - frame pacing, recursion governance, causality pressure, sanctuary stabilization, matter and volumetric adaptation
   - primary source: HOPE and egosphere synthesis/runtime tooling
4. Mind Conductor
   - world-state, AI runtime, campaign pressure, actor cognition, scenario stepping, live API control
   - primary source: NeoWakeUP, EgoSphere, ArchesAndAngels
5. Forge Pipeline
   - art generation, refinement, bundle export, asset contracts, plug-in bridges, engine bundle handoff
   - primary source: Blender plug-ins, Clip Studio plug-ins, ReCraftGenerationStreamline, readAIpolish, egosphere pipeline
6. Vessel Adapters
   - PlayHub, NanoPlay_t, HomeViuPlay, legacy handhelds, 3DS-style validation builds, host runtime, optional mobile/console adapters

## Product Targets

### PlayHub

PlayHub is the primary social and household target.

- couch-first and controller-first
- dock-aware and peer-aware
- optimized for room-scale readability and shared-session play
- receives the full HOMElair stack including peer-link orchestration, hub UI, adaptive comfort routing, and display-depth control

### NanoPlay_t

NanoPlay_t is the low-power portable member of the same runtime family.

- offline-first where possible
- battery-constrained adaptation profile
- reduced sensor dependence compared with PlayHub
- same content contract as PlayHub, but with lower display-cost, lower thermal budget, and tighter pacing discipline

### HomeViuPlay

HomeViuPlay is the precursor pseudo-home-console and detachable monitor base.

- 32-inch display-first proof unit
- detachable from the compute body for modular transport and peer exchange
- used to validate the display-depth stack, local peer docking, and social viewing ergonomics before broader hardware rollout
- should run the same HOMElair software shell as PlayHub with a stronger focus on display instrumentation and calibration

## Display Thesis

HOMElair assumes a window-depth presentation target rather than a flat-panel-only target.

The current display thesis is exploratory and should be treated as a hardware R and D direction, not as a proven manufacturing claim.

Working concept:

- crystal-sheet depth layering
- bio-led or fluid electrorefraction routing
- magnetically tuned refraction control for layered inward depth projection
- low-frequency depth-field modulation so foreground detail stays clean and avoids high-frequency visual noise

Software implication:

- HOMElair should render in depth bands, not only flat composited layers
- foreground clarity gets priority over decorative high-frequency shimmer
- comfort governance belongs in the engine core, not as an afterthought in game-specific shaders

## Files In This Package

- `docs/HOMELAIR_ARCHITECTURE.md` — full subsystem merge plan and hardware/runtime architecture
- `config/homelair_system_map.json` — machine-readable map from current workspace systems into HOMElair layers
- `config/homelair_manifest.schema.json` — shared runtime bundle schema for the HOMElair shell
- `config/homelair_runtime_contract.json` — first merged DoENGINE, ORBEngine, and HOPE-facing runtime contract
- `config/runtime_profiles.json` — PlayHub, NanoPlay_t, and HomeViuPlay runtime profiles
- `apps/homelair_shell.py` — local shell scaffold with bundle inspection and 3D preview rendering
- `assets/scenes/homeviuplay_depth_lair.scene.json` — full-3D sample scene using landscape mesh, character mesh, rig metadata, and depth-band atmosphere
- `assets/scenes/playhub_sanctuary_plaza.scene.json` — PlayHub-facing social 3D habitat scene
- `assets/scenes/nanoplay_t_fieldtrail.scene.json` — NanoPlay_t-facing reduced-budget 3D field scene
- `assets/materials/*.json` and `assets/textures/*.ppm` — first mesh material and texture-layer stack for HOMElair rigs and landscapes
- `assets/meshes/*.wavefold.json` — proprietary-open WaveFold geometry assets with inward fold-space encoding
- `config/capability.example.json` — example signed capability payload shape; keep real private signing keys off-repo

## WaveFold Geometry

HOMElair now includes a drIpTECH-native alternative to `.glb` for selected assets: `wavefold_geometry/v1`.

WaveFold is designed around:

- compact quantized geometry packing
- base64 + zlib encoded vertex and face blocks
- inward fold-space deformation metadata
- optional premium fold amplitude unlocked through a signed capability file

The runtime model is intentionally open source and auditable.

- the verifier and public keys live in the repo
- private signing keys do not live in the repo
- premium capability files are signed offline and provided separately

That means the software stays open, while advanced licensed features still require a valid signature from your signing infrastructure.

Example generation command:

```powershell
python .\DoENGINE\apps\wavefold_cli.py .\HOMElair\assets\meshes\homelair_guardian_avatar.obj .\HOMElair\assets\meshes\homelair_guardian_avatar.wavefold.json --material bone --premium-feature wavefold.pro
```

If you want the runtime to consume a signed capability bundle, set:

```powershell
$env:HOMELAIR_CAPABILITY_PATH = "C:\path\to\homelair_capability.json"
```

If you need to add extra trusted public keys for staging or partner-issued capabilities without modifying the built-in trust store, set:

```powershell
$env:HOMELAIR_TRUSTED_KEYS_PATH = "C:\path\to\trusted_public_keys.json"
```

Without a valid capability bundle, WaveFold assets still load, but the runtime falls back to reduced fold amplitude and reduced inward-bias settings.

## Shell Commands

```powershell
python .\HOMElair\apps\homelair_shell.py --dump-profiles
python .\HOMElair\apps\homelair_shell.py --dump-bundle --profile playhub_depth_lounge
python .\HOMElair\apps\homelair_shell.py --render-preview .\HOMElair\generated\homeviuplay_depth_lair.png --profile homeviuplay_calibration_bay
```

If no CLI export flag is provided, the shell launches a local Tk UI.

## Immediate Next Steps

1. Build the shared HOMElair runtime contract from the current DoENGINE, ORBEngine, NeoWakeUP, and HOPE contracts.
2. Stand up a HOMElair shell app that can launch PlayHub mode, NanoPlay_t mode, and HomeViuPlay calibration mode.
3. Move current demo-hub and adaptive-resonance work under HOMElair naming while keeping DoENGINE as the recovered source package.
4. Define depth-band rendering and comfort budgets in ORBEngine-facing terms.
5. Promote the current Kaiju/3DS HOPE bridge into a general vessel-adapter contract for all HOMElair targets.
