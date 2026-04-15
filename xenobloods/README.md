# XenoBloods

XenoBloods is now its own standalone project rather than a nested design branch inside Pocode.

This root contains:

- `XENOBLOODS_GDD.md` and `XENOBLOODS_GDD.txt`: the full game design document
- `docs/XENOBLOODS_GRAPHICS_MANIFEST.md` and `docs/XENOBLOODS_GRAPHICS_MANIFEST.txt`: the detailed graphical asset manifest
- `docs/XENOBLOODS_GAMEPLAY_PROTOTYPE_PACK.md`: the gameplay-prototype asset scope, controller posture, and readiness notes
- `src/generate_prototype_assets.py`: generates prototype PNG backgrounds, portraits, logo, and UI panels
- `src/jumpclip_xenobloods_pipeline.py`: 2D JumpClip asset-link bridge for staging sprite bundles into Xenobloods
- `src/prototype_shell.py`: a basic Tkinter graphical shell that uses the generated assets with the game systems prototype
- `tools/generate_pikerel_basket_house.py`: generates a true 3D OBJ/MTL picnic-basket house mesh for the village of Pikerel
- `tools/build_pikerel_worldpack.py`: generates a full Pikerel village kit, swamp-lagoon blockout meshes, and a DoENGINE-ready scene manifest
- `tools/build_jumpclip_xenobloods_preview.py`: generates and stages a 2D JumpClip bundle directly into the Xenobloods prototype pipeline
- `tools/build_gameplay_prototype_asset_pack.py`: regenerates the broader gameplay prototype pack and staged JumpClip previews in one pass
- `src/xenobloods_systems.py`: core world, lifecycle, blood-economy, and soul-shrine systems
- `src/xenobloods_adaptive_director.py`: adaptive campaign logic for enemy paradigm schisms, encounter pressure, and outfitting variation
- `src/demo.py`: a simple executable scenario showing rebirth, blood economy, and adaptive encounter generation

## Standalone Direction

Pocode remains a generic adaptive campaign compiler concept.

XenoBloods takes the combat-facing branch of that idea and applies it to a real-time action game with:

- three planes of existence: Up, Land, and Low
- an ether-navigation state used at soul shrines and on death
- a three-form lifecycle tied to blood, death, and rebirth
- blood as currency, stat fuel, and progression resource
- amniotic gourds used for storage, recovery, and rebirth pressure
- enemy paradigm schisms that adapt through authored guardrails rather than cheating

## Prototype Rendering Direction

The active prototype path is now 2D-first.

- JumpClip-linked sprite bundles and generated PNG shell assets drive the playable shell and early asset pipeline.
- The Tkinter shell is the fastest path for seeing XenoBloods visuals in action while the combat/lifecycle systems evolve.

The 3D DoENGINE path is preserved, not removed.

- The OBJ/MTL village kit and swamp showcase remain in place for world-layout, scene-packaging, and long-range presentation planning.
- Treat the DoENGINE worldpack as the retained 3D branch while the live prototype flow moves through 2D assets and sprite-facing iteration.

## Prototype Scope

The Python code here is not a full engine or shipping renderer.

It is a systems prototype that proves the game logic shape:

- plane transitions
- blood spill and collection
- gourd incubation and rebirth into Land
- soul shrine state changes
- combat mastery tracking
- encounter adaptation by enemy schism family and outfit package

## Quick Run

From the workspace root:

```powershell
python xenobloods/src/demo.py
```

That will print a short sample run covering:

- shrine traversal
- gourd infant rebirth
- blood economy updates
- adaptive encounter output

To generate the first prototype graphical assets:

```powershell
python xenobloods/src/generate_prototype_assets.py
```

That now emits a broader gameplay prototype pack including:

- plane backgrounds plus Up and Low room cards
- a Land zone map for metroidvania-style prototype navigation
- lifecycle state cards for the three player forms
- Up tetrarch portraits, Land enemy cards, Low curgz cards, and a Lahgroid boss card
- battle-scene staging art, timing-ring and telegraph assets, and Xbox Series controller layout art
- `xenobloods/assets/generated/prototype_gameplay_asset_manifest.json`

To generate the first 2D JumpClip-linked preview bundle for Xenobloods:

```powershell
python xenobloods/tools/build_jumpclip_xenobloods_preview.py
```

This writes a staged JumpClip bundle into the Xenobloods root, generates `jumpclip_pipeline_link.json`, and refreshes runtime sprite-facing assets for the shell.

By default the preview builder now seeds JumpClip from `xenobloods/examples/xenobloods_jumpclip_references.json`, which mixes Xenobloods-native generated portraits/backgrounds with a small number of in-repo silhouette sheets to bootstrap a stronger source profile than the old single-placeholder manifest.

The preview tool now builds a three-part roster from `xenobloods/examples/xenobloods_preview_roster.json`:

- `Ishtasha, botanical spider scout`: a humanoid botanical spider read for the player-facing preview sheet
- `Scarab child acolyte`: a hooded small enemy read with a plague doctor mask for the common enemy lane
- `Lahgroid hierophant`: the active linked boss preview, a reptilian serpent-feathered manticore humanoid with robe, lantern-chain channeling, cross, cannon, and ordered hovering drone cross-substrata

`jumpclip_pipeline_link.json` now points at the Lahgroid boss bundle by default so the shell preview reflects the requested boss build, while side manifests for the other preview bundles are emitted alongside it.

To regenerate the static gameplay prototype pack together with the staged JumpClip preview roster:

```powershell
python xenobloods/tools/build_gameplay_prototype_asset_pack.py
```

This writes `xenobloods/assets/generated/gameplay_prototype_asset_pack.json` as a combined readiness summary for the current prototype asset set.

To generate the preserved true 3D mesh asset branch:

```powershell
python xenobloods/tools/generate_pikerel_basket_house.py
```

This writes:

- `xenobloods/assets/models/pikerel_picnic_basket_house.obj`
- `xenobloods/assets/models/pikerel_picnic_basket_house.mtl`
- `xenobloods/assets/models/pikerel_picnic_basket_house_summary.txt`

To generate the preserved village kit plus swamp-lagoon worldpack for DoENGINE:

```powershell
python xenobloods/tools/build_pikerel_worldpack.py
```

This writes:

- multiple `xenobloods/assets/models/pikerel_basket_house_*.obj` variants
- support meshes for walkways, docks, shrine posts, reeds, mangroves, lagoon water, and sewer blockout
- `DoENGINE/generated/xenobloods_preview/xenobloods_pikerel_swamp_showcase.json`
- `DoENGINE/generated/xenobloods_preview/models/` with the packaged OBJ/MTL files used by the scene
- `DoENGINE/generated/xenobloods_preview/billboards/` with packaged lifecycle portraits plus encounter and Lahgroid boss media
- `DoENGINE/generated/dodogame_bangonow_showcase.json` updated to the Xenobloods scene for direct DoENGINE preview use
- `DoENGINE/games/xenobloods/` as a standalone saveable DoENGINE game package with:
	- `content/models/`
	- `content/billboards/`
	- `content/scenes/xenobloods_pikerel_swamp_showcase.json`
	- `scripts/doengine_xenobloods_bridge.py` and its packaged support modules
	- `game_profile.json`, `xenobloods_doengine_game.json`, and `saves/default_save.json`

If `XENO_WORLDPACK_BACKUP_ROOT` is set, the build also mirrors the packaged preview scene JSON plus its `models/` and `billboards/` payload into that backup location.

To inspect the standalone package and export the bridge-authored Xenobloods demo checkpoints:

```powershell
python DoENGINE/tools/doengine_game_project.py --game-profile DoENGINE/games/xenobloods/game_profile.json --describe --export-demo-saves
```

That writes a `saves/demo/` folder containing checkpoint saves for:

- Landborne entry
- Ether recall
- Gourd incubation
- Landborne rebirth
- Lahgroid boss intro, clash, and defeat

To render the current standalone package preview directly from the DoENGINE game profile:

```powershell
python DoENGINE/tools/doengine_game_project.py --game-profile DoENGINE/games/xenobloods/game_profile.json --write-preview
```

To smoke-test the graphical shell logic without opening the GUI:

```powershell
python xenobloods/src/prototype_shell.py --smoke
```

To launch the basic prototype graphical shell:

```powershell
python xenobloods/src/prototype_shell.py
```

When `jumpclip_pipeline_link.json` is present in the Xenobloods root, the shell will prefer staged JumpClip 2D assets and show the linked sprite/atlas preview. If the link manifest is missing, it falls back to the generated prototype PNG set.

## Production Intent

The target shipping experience remains a fully real-time PC action game with authored high-end CGI presentation.

The code in this folder now carries two intentional tracks:

- a 2D-first playable prototype and asset-ingest path for immediate iteration
- a preserved 3D scene/worldpack branch for long-range world and presentation development

This is the design and systems foundation for that path, not a false claim that a full 12-hour cinematic action game was implemented in one pass.
