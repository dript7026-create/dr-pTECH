# JumpClip

JumpClip is a prompt-driven sprite animation toolkit for building sprite sheets, PNG frame sequences, and animated GIF previews from a character concept, animation prompt, and a synthesized style profile.

This first-pass project focuses on three things:

- public-domain and user-supplied reference discovery
- grid and proportion analysis over reference images
- procedural sprite rendering driven by animation prompts and synthesized design profiles

## Scope

JumpClip does not copy proprietary game art. The reference pipeline is designed for:

- public-domain image sources
- openly licensed image databases
- user-provided local references

The rendering system synthesizes a new profile from measured proportions, palette tendencies, silhouette coverage, line density, and grid-relative spatial statistics.

## Current Pipeline

1. Collect public references from Openverse or Wikimedia Commons into a manifest.
2. Analyze those references into a design profile.
3. Render a new sprite animation as:
   - sprite sheet PNG
   - PNG frame sequence
   - animated GIF preview
4. Export a game-ready atlas bundle with metadata for an engine render pipeline.

## Artistic Bias

Prompt parsing can weight the renderer toward generalized influences such as:

- gothic composition
- anatomical sketch structure
- surreal elongation
- Goya-like shadow pressure
- Bosch-like ornamental density

These are treated as broad public-domain art-study influences, not as instructions to reproduce specific copyrighted works.

## Designer Module

JumpClip now includes a generation designer layer that critically steers the renderer toward readable silhouettes and controlled texture density across a non-photoreal sprite spectrum. It is meant to keep assets legible and game-ready instead of drifting toward noisy or quasi-photographic output.

JumpClip can also ingest a gameplay-history learning profile and blend it into the resolved style and motion plan. This is intended for advisory biasing of designer choices, not for replacing authored direction.

The designer currently distinguishes broad families such as:

- `8bit`: very limited palette, bold silhouettes, low texture clutter
- `16bit`: classic sprite readability with moderate material detail
- `hd2d`: richer palette and layered texture while staying sprite-native
- `bitmap-traced`: traced or painted bitmap-feeling sprites with stronger cosmetic detail
- `cel-shaded-2.5d`: toon-lit sprite sheets that mimic traced CG staging without photoreal rendering

You can push direction through prompt language like `8bit`, `16bit`, `bitmap traced`, `cel-shaded`, `2.5d`, `distinct silhouette`, `readable silhouette`, `low detail`, `ornate`, or `cosmetic fine detail`.

For tighter control, the renderer and bundle pipeline also accept explicit overrides for style family, silhouette emphasis, texture detail, palette limit, cel shading, outline weight, accessory density, and tracing bias. Use those when you need a deliberate art-direction target instead of prompt-only steering.

There are also named art-direction presets for common targets:

- `retro-arcade`: hard silhouette readability with aggressive palette reduction
- `snes-rpg`: classic 16-bit readability with moderate ornament and clean outlines
- `hd2d-rpg`: richer palette and layered surface treatment while staying sprite-native
- `cel-brawler`: traced cel-shaded staging with stronger impact and cosmetic finish
- `space-shooter`: sharp small-craft readability, low clutter, and arcade-friendly silhouettes
- `soulslike-action`: heavier ornament, darker material treatment, and traced-combat staging

Use presets when you want a fast starting point, then layer explicit overrides on top if needed.

## Install

```powershell
cd JumpClip
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Desktop Shell

JumpClip now ships with a desktop shell for linking generated assets into a selected game's source centerpiece and staging the bundle at the start of the game's asset pipeline.

Launch it from source with:

```powershell
jumpclip-shell
```

The shell lets you pick:

- a game root folder
- a centerpiece source file inside that game
- a profile or manifest
- a pipeline config
- an output bundle directory
- visual and motion controls for the generated asset bundle

When you run `Generate + Link To Game`, the shell exports the bundle, stages it into the game project under `JumpClipAssets` by default, and writes `jumpclip_pipeline_link.json` into the game root so the project has a stable handoff manifest to the generated assets.

To build a standalone Windows executable shell:

```powershell
pwsh .\tools\build_jumpclip_shell.ps1
```

That produces `dist\JumpClipShell.exe` via PyInstaller.

## Usage

There are two supported authoring workflows:

1. Analyze first, then render from a stable design profile when you want repeatable results.
2. Render or bundle directly from a reference manifest when you want a shorter iteration loop.

Collect references:

```powershell
jumpclip collect --provider openverse --query "public domain pixel art gothic sprite" --out refs.json
```

Analyze references:

```powershell
jumpclip analyze --manifest refs.json --out profile.json --download-dir .cache\refs
```

Render a sprite sheet:

```powershell
jumpclip render --profile profile.json --character "clockwork revenant duelist" --animation "run cycle" --prompt "gothic pixel art, anatomical sketch logic, surreal dali stretch, goya shadows, bosch detail" --out out\revenant_sheet.png --format sheet
```

Render with explicit designer controls:

```powershell
jumpclip render --profile profile.json --character "lantern courier" --animation "run cycle" --prompt "courier silhouette study" --out out\courier_sheet.png --format sheet --style-family 8bit --silhouette-emphasis 1.8 --texture-detail 0.18 --palette-limit 8
```

Render from a named preset instead of hand-tuning every knob:

```powershell
jumpclip render --profile profile.json --character "arcade courier" --animation "run cycle" --prompt "readable courier silhouette" --out out\arcade_courier.png --format sheet --art-preset retro-arcade
```

For traced or cel-shaded sprites, the additional controls let you tune line assertiveness and ornamental load directly:

```powershell
jumpclip render --profile profile.json --character "cathedral revenant" --animation "attack combo" --prompt "duelist staging" --out out\revenant_attack.png --format sheet --style-family cel-shaded-2.5d --texture-detail 0.92 --cel-shading 1.0 --outline-weight 0.9 --accessory-density 0.78 --tracing-bias 0.86
```

Animation motion can also be styled explicitly when you need stronger squash, lift, or impact in a particular move:

```powershell
jumpclip render --profile profile.json --character "cathedral revenant" --animation "attack combo" --prompt "duelist staging" --out out\revenant_attack_motion.png --format sheet --art-preset cel-brawler --motion-impact 0.96 --motion-squash-stretch 0.3 --motion-lift 1.2
```

Blend in a gameplay-history learning profile to bias the resulting art direction and key-pose motion values:

```powershell
jumpclip render --profile profile.json --learning-profile examples\learned_style_profile.json --learning-weight 0.75 --character "delta courier" --animation "jump arc" --prompt "readable courier silhouette" --out out\delta_courier.png --format sheet
```

Render an animated GIF:

```powershell
jumpclip render --profile profile.json --character "clockwork revenant duelist" --animation "attack combo" --prompt "gothic pixel art with anatomical sketch structure" --out out\revenant.gif --format gif
```

Render directly from a reference manifest without a separate analyze step:

```powershell
jumpclip render --profile examples\sample_references.json --character "cathedral revenant" --animation "run cycle" --prompt "gothic pixel art, anatomical sketch logic, surreal dali stretch, goya shadows, bosch detail" --out out\cathedral_revenant_sheet.png --format sheet
```

When `--profile` points to a manifest instead of a synthesized design profile, JumpClip analyzes the references on the fly before rendering.

Render from a manifest with remote references by supplying a cache directory for downloaded images:

```powershell
jumpclip render --profile refs.json --character "lantern courier" --animation "jump arc" --prompt "pixel art courier with gothic silhouette" --out out\lantern_courier.png --format sheet --download-dir .cache\refs
```

Export a standard bundle for a game render pipeline:

```powershell
jumpclip bundle --profile profile.json --character "clockwork revenant duelist" --animation "run cycle" --prompt "gothic pixel art, anatomical sketch logic" --out-dir build\revenant_run --pipeline examples\game_pipeline.json
```

Export a traced cel-shaded bundle with direct designer overrides:

```powershell
jumpclip bundle --profile profile.json --character "cathedral revenant" --animation "attack combo" --prompt "duelist staging" --out-dir build\revenant_attack --pipeline examples\game_pipeline.json --style-family cel-shaded-2.5d --texture-detail 0.92 --cel-shading 1.0 --silhouette-emphasis 1.32 --palette-limit 28
```

Learning profiles also work in bundle exports, and the resolved influence is written into `metadata.json`:

```powershell
jumpclip bundle --profile profile.json --learning-profile examples\learned_style_profile.json --character "wind scout" --animation "run cycle" --prompt "clean courier silhouette" --out-dir build\wind_scout --pipeline examples\game_pipeline.json
```

The sample pipeline now enables visual regression outputs by default, so each bundle also includes:

- `visual_regression.png`: contact-sheet style frame review output
- `visual_regression.json`: frame hashes and bounding boxes for lightweight regression tracking
- `visual_regression.html`: a lightweight browser viewer over the same regression data

Export multiple bundles from one manifest-driven build description:

```powershell
jumpclip bundle-batch --batch-manifest examples\bundle_batch_manifest.json --out-dir build\batch_export --pipeline examples\game_pipeline.json
```

The bundle command emits a stable toolchain contract for game integration:

- `atlas.png`: packed sprite atlas sized to the pipeline's texture-width constraint
- `metadata.json`: frame rects, pivot, frame timing, pixels-per-unit, and profile summary
- `profile.json`: the synthesized design profile used for the bundle
- `preview.gif`: optional quick-look animation for review
- `frames\`: optional per-frame PNG exports when the pipeline asks for them

`examples\game_pipeline.json` is the baseline config for adapting output to a game's render pipeline. It standardizes frame size, pixels-per-unit, timing, atlas width, pivot, and whether preview artifacts or frame sequences are emitted.

The pipeline config can also emit engine-specific sidecars for common pipelines:

- `unity_import.json`: sprite rects and pivots for Unity import tooling
- `godot_spriteframes.json`: animation frame layout for Godot sprite-frame construction
- `aseprite.json`: atlas metadata in an Aseprite-style frame map shape

`examples\bundle_batch_manifest.json` shows the expected batch schema for generating multiple animations in one pass.
It also demonstrates shared `design_templates` and `motion_templates`, so one batch can mix low-bit silhouette-first assets, space shooters, and higher-detail traced or soulslike outputs without repeating the whole control block in every job.

## Files

- `src/jumpclip/reference_sources.py`: public-image collectors and manifest normalization
- `src/jumpclip/analysis.py`: grid-statistics, silhouette, palette, and design-profile synthesis
- `src/jumpclip/designer.py`: style-spectrum classification and silhouette/detail direction
- `src/jumpclip/learning.py`: gameplay-history influence loading and blending into style and motion decisions
- `src/jumpclip/render.py`: procedural animation renderer and exporters
- `src/jumpclip/pipeline.py`: game-ready atlas bundle export and pipeline config handling
- `src/jumpclip/cli.py`: command line interface

## Design Docs

- `docs/JUMPCLIP_ART_BIBLE.md`: JumpClip-native visual craft rules keyed to current designer controls
- `docs/JUMPCLIP_ANIMATION_POSE_STANDARD.md`: key-pose, motion-family, and animation readability standard
- `docs/JUMPCLIP_GODAI_EGOSPHERE_SIDE_PROJECT.md`: side-project spec for learning from gameplay history to bias stylistic and key-pose suggestions

## Next Steps

- plug in a model-backed image synthesis stage behind the current procedural renderer
- add sprite cleanup and frame inbetweening tools
- add reference clustering for genre and era snapshots
- add a UI for pose tuning and frame review
