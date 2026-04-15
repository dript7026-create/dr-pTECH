# Kaiju Gaiden Assembly Depth Pipeline

This is the assembly-facing implementation map for the Windows HOPE adaptive-depth build.

It is not a claim that the current repository already ships a fully assembled x64 render stack. The current environment now has `nasm` on `PATH`, but still does not have `ml64`, `cl.exe`, or `link.exe`, so this document remains the exact low-level contract to build against while the first NASM object modules are being staged.

## Target Output

- presentation mode: full-screen `1920x1080`
- gameplay source surface: `240x160`
- upscale factor: `6x`
- centered gameplay viewport: `1440x960`
- pillarbox margins: `240 px` left and right
- letterbox margins: `60 px` top and bottom
- display model: single-screen inward-depth illusion, not physical dual-view stereo

## Runtime Layers

1. Sensor ingest layer
   - webcam frame capture
   - face box extraction
   - eye box extraction
   - brightness and edge-density sampling
   - face proximity and offset estimation
2. HOPE control layer
   - ingest `hope_runtime_contract.json`
   - compute volumetric support, reactivity, clog risk, predictive share, adaptive share
   - emit scalar depth drive and comfort clamp
3. Depth compositor layer
   - compute inward pull per band: far, near, entity, fx
   - compute center-of-attraction bias from face offset
   - reproject source positions toward the inward center
   - attenuate depth when comfort risk rises
4. Presentation layer
   - upscale assets to `6x`
   - center scene in `1920x1080`
   - apply framing bands and cosmetic overlays

## Assembly Module Split

Recommended x64 module split for Windows:

1. `sensor_metrics_x64.asm`
   - luma accumulation for webcam grayscale frame
   - Sobel or simple edge-energy kernel
   - face ROI statistics pass
   - eye ROI pupil-darkness approximation
2. `hope_depth_core_x64.asm`
   - first staged NASM x64 module now exists under `asm/`
   - scalar fusion of HOPE values plus sensor metrics
   - smoothing and comfort clamping
   - preset application for `studio-balanced`, `bright-floor-demo`, `low-strain-mono`
3. `depth_reproject_x64.asm`
   - inward-depth projection for sprite anchors and parallax layers
   - viewport centering and band-specific pull
4. `blit_scale6_x64.asm`
   - nearest-neighbor `240x160 -> 1440x960` expansion
   - optional outline pass and panel-tone overlay
5. `overlay_ink_x64.asm`
   - frame lines, halftone strips, manga impact bands, HUD primitives

## Frame Pipeline

Per-frame ordering:

1. Acquire camera frame into grayscale buffer.
2. Run luma and edge-density pass.
3. Run face and eye ROI pass.
4. Emit metrics:
   - `brightness`
   - `face_ratio`
   - `proximity`
   - `face_offset_x`
   - `face_offset_y`
   - `eye_open`
   - `dilation`
   - `space_open`
   - `confidence`
5. Load HOPE bridge values.
6. Fuse camera and HOPE values into:
   - `depth_strength`
   - `comfort`
   - `band_pull_far`
   - `band_pull_near`
   - `band_pull_entity`
   - `band_pull_fx`
   - `focus_bias_x`
   - `focus_bias_y`
7. Reproject far background anchors.
8. Reproject gameplay entities.
9. Reproject effects and foreground strips.
10. Upscale source art and composite into centered `1920x1080` framebuffer.
11. Draw HUD and depth frame overlays.

## Memory Layout

Suggested packed data blocks:

```c
typedef struct SensorMetrics {
    float brightness;
    float face_ratio;
    float proximity;
    float space_open;
    float eye_open;
    float dilation;
    float confidence;
    float face_offset_x;
    float face_offset_y;
    float edge_density;
} SensorMetrics;

typedef struct HopeDepthState {
    float strength;
    float comfort;
    float focus_bias_x;
    float focus_bias_y;
    float far_pull;
    float near_pull;
    float entity_pull;
    float fx_pull;
} HopeDepthState;
```

Assembly should keep these 16-byte aligned for SIMD-friendly loads.

## Core Equations

The current high-level host uses the following fused model and the assembly version should preserve it:

$$
\text{targetStrength} = \text{presetBase} \cdot \text{hopeDrive} \cdot \text{cameraDrive} - \text{comfortRisk} - 0.10 \cdot \text{clogRisk}
$$

$$
\text{projectedX} = x + (c_x - x) \cdot p_b
$$

$$
\text{projectedY} = y + (c_y - y) \cdot 0.60 \cdot p_b
$$

Where:

- `$c_x, c_y$` are the inward focal center plus face-offset bias
- `$p_b$` is the pull value for the render band

## Band Semantics

- `far`: strongest inward pull, used for distant background recession
- `near`: medium pull, used for foreground scenery bands
- `entity`: moderate pull, used for player, boss, minions
- `fx`: light pull, used for sparks, nanocells, hit effects

## Assembly Responsibilities By Stage

### Asset Generation

- decode PNG or source asset into RGBA
- optional comic stylization:
  - posterize
  - edge extraction
  - dark ink re-overlay
  - halftone mask blend
- convert to packed BGRA or XRGB for blitter consumption
- pre-scale to `6x` or scale on blit depending on CPU budget

### Render Submission

- write draw commands into a flat command buffer:
  - texture id
  - source rect
  - destination anchor
  - band id
  - z order

### Reprojection

- read band id
- load band pull
- adjust anchor toward inward center
- output final screen anchor inside centered viewport

### Fullscreen Presentation

- clear `1920x1080` backbuffer
- draw scene into the centered `1440x960` viewport
- leave outer frame for decorative HUD, comic captioning, and manga framing

## Cosmetic 20x Push Direction

The current host can support these appearance pushes without changing gameplay semantics:

- heavier black contour lines on entities
- halftone skies and water tone bands
- gold-ink or cyan energy accents in effects
- more assertive silhouette separation for boss forms
- layered frame gutters and comic-panel staging around the viewport

## Build Integration Plan

Once assembler tooling exists, the Windows path should add:

1. `asm/hope_depth_core_x64.asm`
2. `asm/depth_reproject_x64.asm`
3. `asm/blit_scale6_x64.asm`
4. `include/hope_depth_core.h`
5. `tools/build_windows_hope_depth.ps1`

Current staged build support:

1. `tools/build_depth_asm.ps1`
2. `asm/hope_depth_core_x64.asm`
3. `build/asm/hope_depth_core_x64.obj`

Expected build phases:

1. assemble `.asm` files to `.obj`
2. compile thin C shim or Python extension bridge
3. link into `hope_depth_core.dll`
4. load from the host runtime through `ctypes` or a native C entrypoint

## Current Practical State

The current repository now implements the adaptive-depth behavior in the Windows host at a high level in [host_graphical.py](host_graphical.py). That is the active behavior reference for the future assembly port.
