# Dress SparLE: Light Envisioned

Dress SparLE: Light Envisioned is an AVM2 Flash prototype for a combat dance rhythmbattle dress-up game.

Sparkle is a BlueNoMid: a cobalt performer whose body is only a torso, a disembodied head, and detached hands and feet. Sparkle fights the LiteMite army by catching rhythm seams, weaving clothing directly out of movement, then locking a finishing pose hard enough to collapse a syncrosequence tail of sentient light.

## Prototype Scope

- Four rhythm lanes with hit windows and miss penalties.
- Procedural dubstep playback driven by `SampleDataEvent` synthesis.
- Adaptive visible-spectrum framebuffer background that reacts to combo, disruption, emberence, and LiteMite presence.
- Dress-up state progression that changes Sparkle's silhouette as charge increases.
- Pose-lock finisher windows that can either obliterate a LiteMite tail or let it fall backward through the glue-stall field.

## Controls

- `A` or `Left Arrow`: Head Flick lane
- `S` or `Down Arrow`: Torso Pulse lane
- `K` or `Up Arrow`: Hand Halo lane
- `L` or `Right Arrow`: Foot Spark lane
- `Space`: Lock the current pose when the finisher window opens

## Files

- `src/Main.as`: stage setup and frame pump
- `src/GameScript.as`: full gameplay, rendering, and procedural audio prototype
- `prefabs.json`: project prefab registry for Sparkle, LiteMites, runway FX, and sound cues
- `generation/recraft_manifest.json`: queued visual asset prompts for character, enemy, runway, and finisher art
- `generation/audio_manifest.json`: queued audio prompts for reference loops and stingers
- `generation/jumpclip_runs.json`: queued motion-preview bundles for actor silhouettes
- `build/generate_runtime_pack.ps1`: compiles manifest data into runtime-ready combat animation descriptors
- `generated/runtime/dress_sparle_runtime_pack.json`: merged actor/enemy/cue animation pack used to drive combat art behavior
- `generated/runtime/combat_pattern_book.json`: per-archetype encounter phase and animation job book
- `farim/farim_manifest.json`: FARIM packaging metadata
- `build/bootstrap_flex_sdk.ps1`: repo-local Apache Flex bootstrap helper
- `build/build_swf.ps1`: compile script that prefers repo-local Flex and JDK paths
- `build/package_farim.ps1`: package the built `.swf` into `.farim`

## Build

1. Run `build\bootstrap_flex_sdk.ps1` if you do not already have `mxmlc` available.
2. Run `build\build_swf.ps1` to compile `bin\dress-sparle-light-envisioned.swf`.
3. Run `build\package_farim.ps1` to create the matching FARIM package.
4. Run `build\generate_runtime_pack.ps1` to emit runtime combat-animation descriptor packs from the art/audio/jumpclip manifests.

## Current Status

- The repo-local Apache Flex toolchain under `pocode/windows/dripwave/toolchain/` is configured and working.
- The project currently builds to `bin/dress-sparle-light-envisioned.swf` and packages to `bin/dress-sparle-light-envisioned.farim`.
- `dripwave.exe --smoke` validates both artifacts successfully and classifies the SWF as `AVM2 / ActionScript 3`.

To actually play the interactive SWF, use an AVM2-capable runtime such as Ruffle Desktop or a standalone Flash projector. `dripwave` can inspect and route the file, but AVM2 gameplay still needs an external runtime.
