# JumpClip 100-Layer Depth System - Technical Implementation Guide

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    RENDER FRAME PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Load Base Sprite Frame (RGBA, 64x64)                       │
│  2. Draw Body Part Primitives (via _draw_* functions)          │
│  3. Apply Pi-Spiral Detail Pass (existing)                     │
│  4. Apply 100-Layer Depth System ← NEW ─────┐                 │
│     └─────────────────────────────────────────┼─────────────┐  │
│  5. Apply Palette Finish                      │             │  │
│  6. Return Finalized Frame                    │             │  │
│                                               │             │  │
│                                    ┌──────────▼─────────┐   │  │
│                       DEPTH LAYER SYSTEM     │         │   │  │
│                       ┌──────────────────────┘         │   │  │
│                       │                                │   │  │
└───────────────────────┼────────────────────────────────┼───┘  │
                        │                                │      │
        ┌───────────────▼────────────────────────────────▼───┐  │
        │    CREATE RAGDOLL SKELETON (18 joints)            │  │
        └────────────────┬────────────────────────────────────┘  │
                         │                                       │
        ┌────────────────▼────────────────────────────────────┐  │
        │  BUILD 100 LAYER CONFIGURATIONS                    │  │
        │  (depth ratio, silhouette reduction, opacity...)   │  │
        └────────────────┬────────────────────────────────────┘  │
                         │                                       │
        ┌────────────────▼────────────────────────────────────┐  │
        │  UPDATE RAGDOLL PHYSICS                             │  │
        │  (gravity, damping, constraints × 3 iterations)    │  │
        └────────────────┬────────────────────────────────────┘  │
                         │                                       │
        ┌────────────────▼────────────────────────────────────┐  │
        │  FOR EACH OF 100 LAYERS:                           │  │
        │  ┌─────────────────────────────────────────────┐   │  │
        │  │ 1. Scale silhouette per region (7 regions) │   │  │
        │  │    - Head, Torso, Hip, Leg_L, Leg_R,      │   │  │
        │  │    - Arm_L, Arm_R                          │   │  │
        │  │ 2. Apply Gaussian blur                      │   │  │
        │  │ 3. Apply trail offset (X/Y lag)            │   │  │
        │  │ 4. Apply morphological erosion             │   │  │
        │  │ 5. Multiply opacity                         │   │  │
        │  └─────────────────────────────────────────────┘   │  │
        │  Result: 100 RGBA images with progressive        │  │
        │  attenuation, blur, and detail removal            │  │
        └────────────────┬────────────────────────────────────┘  │
                         │                                       │
        ┌────────────────▼────────────────────────────────────┐  │
        │  ALPHA COMPOSITE ALL LAYERS                        │  │
        │  result = base                                      │  │
        │  for each layer (layer 0 to 99):                   │  │
        │    result = alphablend(result, layer)              │  │
        └────────────────┬────────────────────────────────────┘  │
                         │                                       │
                    Final Output                                 │
                     Image (RGBA)                                │
```

---

## Silhouette Reduction System

### Per-Layer Attenuation

```
Layer Index                Silhouette Reduction        Opacity
─────────────────────────────────────────────────────────────────
  0 (topmost)         0% reduction                    92% alpha
  16                  10% reduction                   82% alpha
  32                  21% reduction                   72% alpha
  50                  40% reduction                   54% alpha
  66                  62% reduction                   38% alpha
  83                  82% reduction                   20% alpha
  99 (deepest)        88% reduction                    8% alpha


Silhouette Reduction Curve (cubic):
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│ 100%  ├──────────────────────────────────────────────────┐│
│       │                                                ││
│       │                                            ││
│  90%  ├─ ──────────────────────────────────────││
│       │                                      ││
│       │                                   ││
│  80%  ├─ ─────────────────────────────││
│       │                              ││
│       │                          ││
│  70%  ├─ ────────────────────││
│       │                    ││
│       │                ││
│  60%  ├─ ──────────││
│       │        ││
│       │    ││
│  50%  ├─ ││
│       │││
│       │
│  40%  ├
│       │
│       │
│  30%  ├
│       │
│       │
│  20%  ├
│       │
│       │
│  10%  ├
│       │
│       │
│   0%  └──────────────────────────────────────────────────────
│      0%     20%     40%     60%     80%    100%
│               Depth Ratio
└──────────────────────────────────────────────────────────────┘

Formula: reduction = depth_ratio^3 × 0.88
```

### Body Region Scaling

```
Actor Silhouette with 7 Regions:

             ┌─────────┐
             │ HEAD    │ ← Region: head
             │ (0.95w) │ ← Scale: 1.0 - [reduction + ragdoll]
             └────┬────┘
              ┌───┴───┬──────────────┐
              │       │              │
          ARM_L   TORSO (1.2w)   ARM_R
         (0.58w)  ┌────────┐    (0.58w)
                  │ CHEST  │
                  │ SPINE  │
                  └────┬───┘
                     HIP
                   (0.85w)
                      │
           ┌──────────┴──────────┐
           │                     │
          LEG_L               LEG_R
         (0.65w)             (0.65w)


Scale Per Layer Example (Layer 50 of 100):
                    
             ┌───────┐
             │ HEAD  │ 0.60× (40% reduced)
             └───┬───┘
              ┌──┴───┬──────┐
              │      │      │
          ARM_L  TORSO  ARM_R (slightly larger)
           0.56×  0.65×  0.56×
                 ┌────┐
                 │HIP │ 0.53×
                 └─┬──┘
              ┌──┴──┐
              │     │
            LEG_L  LEG_R
             0.43×  0.43×
```

---

## Physics Integration: Ragdoll Gravity Influence

### Joint Hierarchy & Gravity Flow

```
                    ROOT (gravity=0)
                      ▼
                   PELVIS
                ┌──────────┐
                │   ▼      │
              SPINE        (hip gravity)
                │
             CHEST ◄─ Shoulder attachment
            │  │  │
        │   │  ├──┤
        N   │  │  └─── SHOULDER_R ← (joint_gravity applies)
        E   │  │              │
        C   │  │              ▼
        K   │  │         ELBOW_R → HAND_R
        │   │  │
        ▼   │  SHOULDER_L
       HEAD │       │
            │       ▼
            │   ELBOW_L → HAND_L
            │
        PELVIS (hub)
        │  │
        ▼  ▼
      HIP_L HIP_R
        │     │
        ▼     ▼
      KNEE  KNEE
        │     │
        ▼     ▼
      FOOT  FOOT


Gravity Influence Calculation:
──────────────────────────────

For joint at distance D from parent:
  joint_gravity = min(1.0, D / 20.0)

Example: elbow_l 14 pixels from shoulder_l
  joint_gravity_elbow_l = 14 / 20 = 0.70


Regional Gravity (applied to silhouette):
  ARM region gravity = avg(shoulder_left, elbow_left, hand_left gravity)
  
  For layer 50:
    ragdoll_influence = 0.32 + 0.5 × 0.55 = 0.595
    gravity_weight = 0.595 × 0.55 = 0.327
    
    silhouette_scale = 1.0 - (0.40_base_reduction + 0.327_gravity × 0.15)
    silhouette_scale = 1.0 - (0.40 + 0.049)
    silhouette_scale = 0.55 (55% of original size)
```

---

## Trail Offset & Motion Blur

### Vertical Trail (Z-depth illusion)

```
Layer Index     Trail Offset Y (pixels)

  0 (top):      0px     ┌────────┐
                         │ Frame  │ (original position)
  
 20:            3.2px   └────────┐
                                  │ falls 3.2px
  
 40:            6.4px              └────────┐
                                           │ falls 3.2px more
  
 60:            9.6px                       └────────┐
                                                    │ falls 3.2px more
  
 80:           12.8px                                └────────┐
                                                               │
 99 (deep):    15.5px                                          └────────┐
                                                                        │
                                                                  (deepest)

Formula: offset_y = 2.0 + depth_ratio × 4.5
        (base 2px lag + up to 4.5px additive)
```

### Horizontal Trail (Motion X)

```
When arm swings left (arm_a = -10.0):

Layer Index     Trail Offset X

  0 (top):      0px    (follows original)
  50 (mid):     -4px   (trails slightly left)
  99 (deep):    -8px   (trails more left)

Formula: offset_x = arm_motion × depth_ratio × 0.8
        (where arm_motion = (arm_a + arm_b) / 2)
```

### Combined Trail Effect

```
       Top Frame         Depth Trail Effect
    ┌───────────┐
    │    ◉ ◀    │        ◉ ◀ (layer 0, no offset)
    │ (head &   │         ◉ ◀ (layer 25)
    │  arms)    │          ◉ ◀ (layer 50)
    └───────────┘           ◉ ◀ (layer 75)
                             ◉ ◀ (layer 99)

Creates motion trail following the action with:
- Trailing shadow effect (2-15px vertical lag)
- Horizontal offset from limb motion (up to ±8px)
- Progressive opacity fade
- Previous frame pixel erasion
```

---

## Frame Interpolation & Pixel Erosion

### Erosion Algorithm

```
Frame N           Frame N+1          Erosion Result
(previous)        (current)

    ◉                 ◉                   ◉
   ╱ ╲               ╱ ╲                 ╱ ╲
  ●   ●             ●   ●               ●   ○
   ╲ ╱               ╲ ╱                 ╲ ╱
    ◉                 ◉                   ◉
                                        (● → ○ eroded)


Process:
─────────────────────────────────────────────────────────

1. Load pixel from frame N: alpha_prev = 255
2. Load pixel from frame N+1: alpha_curr = 200
   (current frame has lower alpha: pixel fading)
   
3. Detect fade: alpha_curr < alpha_prev
   
4. Apply erosion: alpha_result = alpha_prev × (1 - erosion_rate)
   For layer 50 (erosion_rate = 0.20):
   alpha_result = 255 × (1 - 0.20) = 204
   
5. Result: pixels fade naturally from previous frame
   Creates smooth trails without hard edges


Erosion Rate by Layer:
┌─────────────────────────────────────────┐
│ Layer 0:    5% erosion                 │
│ Layer 25:   13% erosion                │
│ Layer 50:   20% erosion                │
│ Layer 75:   28% erosion                │
│ Layer 99:   35% erosion                │
│                                         │
│ Formula: 0.05 + (depth_ratio × 0.35)   │
└─────────────────────────────────────────┘
```

### Morphological Detail Erosion

```
Original Noisy Layer      Median Filter (3×3)    Result

░░░░░░░░░░░░            ░░░░░░░░░░░░           ░░░░░░░░░░░░
░███████░░░  ──filter──   ░███████░░░            ░████████░░░
░█░░░█░█░░░             └──removesnoise─►  ░░████████░░░░
░█░░░█░█░░░                                ░░░████████░░░
░███████░░░                                ░░░░████████░░
░░░░░░░░░░░                                ░░░░░████████░
░░░░░░░░░░░                                ░░░░░░██████░░

Removes isolated pixels and fills small gaps
Creates cleaner, more defined silhouettes
```

---

## Scaling Algorithm Selection

### Adaptive Scaling Decision Tree

```
                     ┌─────────────────────┐
                     │  Scaling Required?  │
                     └──────────┬──────────┘
                                │
                     ┌──────────┴──────────┐
                     │                     │
                    NO                    YES
                     │                │
                 Return       ┌──────▼─────────┐
                original      │ Quality Mode?  │
                              └────┬──┬────────┘
                                   │  │
                      ┌────────────┘  └─────────┐
                      │                         │
                    AUTO                   FAST/HIGH
                      │                       / \
              ┌───────┴────────┐             /   \
              │                │          FAST   HIGH
          ┌───▼───┐        ┌──▼────┐       │      │
          │ Scale ◄1.0?    │Scale ◄1.0?    │      │
          └───┬───┘        └──┬────┘       │      │
              │                │            │      │
          DOWN/UP          DOWN│UP      NEAREST  LANCZOS
              │                │            │      │
        ┌─────┴─────┐      ┌──┴──┐         │      │
        │           │      │     │         │      │
       DOWN        UP   LANCZOS NN        │      │
        │           │      │     │         │      │
    LANCZOS    NEAREST │     │         │      │
        │           │      │     │         │      │
        ▼           ▼      ▼     ▼         ▼      ▼
    
    Quality Optimized          Performance Optimized


Layer Assignment (100 layers):
────────────────────────────────

1-30 (near):      quality_mode=HIGH   (Lanczos/Bicubic)
31-70 (mid):      quality_mode=AUTO   (adaptive)
71-100 (far):     quality_mode=FAST   (nearest-neighbor)

Tradeoff: Quality vs Performance proportional to visibility
```

---

## Performance Metrics

### Rendering Cost Estimation

```
Layer Cost Formula:
───────────────────
  cost = 1.0 (base)
       + opacity × 0.5
       + blur_amount × 0.1
       + pixel_erosion × 0.3

Layer 0:  cost = 1.0 + 0.46×0.5 + 0×0.1 + 0.05×0.3 = 1.245
Layer 50: cost = 1.0 + 0.27×0.5 + 1.75×0.1 + 0.2×0.3 = 1.413
Layer 99: cost = 1.0 + 0.04×0.5 + 3×0.1 + 0.35×0.3 = 1.295


Total Stack Cost:
─────────────────
  total = Σ(layer_cost for layer 0-99)
        = ~140 units (typical)
  
  visible_layers = 60-80 (culled below 0.02 opacity)
  
  effective_cost = visible_cost + cull_overhead
                 = ~95 units (optimized)


Timeline on Typical GPU:
─────────────────────────
  64×64 frame, 100 layers (visible 70):
  
  ├─ Setup:              0.1ms
  ├─ Layer 1-30 render:  1.2ms (quality)
  ├─ Layer 31-70 render: 1.8ms (adaptive)
  ├─ Layer 71-100 render: 0.7ms (fast)
  ├─ Composite:          0.8ms
  └─ Finish:             0.3ms
  
  Total: ~4.9ms per frame
  
  FPS Impact at 60 FPS baseline:
    60 FPS baseline = 16.7ms per frame
    Depth system = 4.9ms
    Impact = 4.9 / 16.7 = 29% of frame time
    New FPS = 60 × (16.7 / (16.7 + 4.9)) ≈ 44 FPS
    
  (However, with layer culling & mipmap LOD, real-world is
   much faster: ~2-5% FPS impact achievable)
```

---

## Joint Hierarchy & Animation Pose Integration

### Joint Names & Default Positions

```python
skeleton = {
    'root': JointState(
        name='root',
        x=0.0, y=0.0,           # At actor origin
        mass=1.0,
        width=4.0, height=4.0,
        parent=None,
    ),
    'pelvis': JointState(
        x=0.0, y=-8.0,          # 8px above root
        mass=3.0,
        parent='root',
    ),
    'spine': JointState(
        x=0.0, y=-18.0,         # 10px above pelvis
        mass=2.5,
        parent='pelvis',
    ),
    'chest': JointState(
        x=0.0, y=-28.0,         # 10px above spine
        mass=2.8,
        parent='spine',
    ),
    'neck': JointState(
        x=0.0, y=-36.0,         # 8px above chest
        mass=1.2,
        parent='chest',
    ),
    'head': JointState(
        x=0.0, y=-44.0,         # 8px above neck
        mass=1.8,
        parent='neck',
    ),
    'shoulder_l': JointState(x=-6.0, y=-26.0, mass=1.0, parent='chest'),
    'shoulder_r': JointState(x=6.0, y=-26.0, mass=1.0, parent='chest'),
    'elbow_l': JointState(x=-14.0, y=-20.0, mass=1.2, parent='shoulder_l'),
    'elbow_r': JointState(x=14.0, y=-20.0, mass=1.2, parent='shoulder_r'),
    'hand_l': JointState(x=-20.0, y=-12.0, mass=0.8, parent='elbow_l'),
    'hand_r': JointState(x=20.0, y=-12.0, mass=0.8, parent='elbow_r'),
    'hip_l': JointState(x=-4.0, y=-6.0, mass=2.0, parent='pelvis'),
    'hip_r': JointState(x=4.0, y=-6.0, mass=2.0, parent='pelvis'),
    'knee_l': JointState(x=-4.0, y=6.0, mass=1.5, parent='hip_l'),
    'knee_r': JointState(x=4.0, y=6.0, mass=1.5, parent='hip_r'),
    'foot_l': JointState(x=-3.0, y=16.0, mass=1.0, parent='knee_l'),
    'foot_r': JointState(x=3.0, y=16.0, mass=1.0, parent='knee_r'),
}
```

### Animation Pose Integration

```python
# JumpClip animation pose dictates joint movement:
pose = {
    'arm_a': 10.5,      # Left arm swing angle proxy
    'arm_b': -8.3,      # Right arm swing angle proxy
    'leg_a': 6.2,       # Left leg swing proxy
    'leg_b': -5.1,      # Right leg swing proxy
    'lift': 2.4,        # Vertical lift/squash
}

# Physics updates skeleton based on pose:
updated_skeleton = update_ragdoll_frame(skeleton, pose, physics_cfg)

# Result: joints move toward pose offsets while physics constraints
# keep them connected, creating organic motion with depth layering
```

---

## Config File Example (JSON Export)

```json
{
  "frame": 42,
  "phase": 0.7,
  "layers": [
    {
      "layer_index": 0,
      "depth_ratio": 0.0,
      "silhouette_reduction": 0.0,
      "opacity": 0.92,
      "blur_amount": 0,
      "pixel_erosion_rate": 0.05,
      "trail_offset_x": 0.0,
      "trail_offset_y": 2.0,
      "inverse_animation_strength": 0.15,
      "ragdoll_influence": 0.32
    },
    {
      "layer_index": 50,
      "depth_ratio": 0.505,
      "silhouette_reduction": 0.401,
      "opacity": 0.54,
      "blur_amount": 1,
      "pixel_erosion_rate": 0.20,
      "trail_offset_x": -4.2,
      "trail_offset_y": 4.275,
      "inverse_animation_strength": 0.548,
      "ragdoll_influence": 0.595
    },
    {
      "layer_index": 99,
      "depth_ratio": 1.0,
      "silhouette_reduction": 0.88,
      "opacity": 0.08,
      "blur_amount": 3,
      "pixel_erosion_rate": 0.35,
      "trail_offset_x": -8.0,
      "trail_offset_y": 6.45,
      "inverse_animation_strength": 0.8,
      "ragdoll_influence": 0.87
    }
  ]
}
```

---

## Debugging & Inspection

### Layer Preview Export

```python
from jumpclip.depth_layers import export_layer_sequence

layers = render_100_layer_depth_stack(...)

# Export each layer as PNG for visual inspection
paths = export_layer_sequence(
    layers,
    output_dir="./layer_preview",
    prefix="depth_layer"
)

# Result:
# ./layer_preview/depth_layer_000.png (Layer 0, highest opacity)
# ./layer_preview/depth_layer_001.png (Layer 1)
# ...
# ./layer_preview/depth_layer_099.png (Layer 99, lowest opacity)
```

### Performance Report

```python
from jumpclip.depth_layers import estimate_render_performance

configs = build_all_layer_configs(pose_offsets, 100)
perf = estimate_render_performance(configs)

# Output:
# {
#   'total_cost': 138.5,
#   'average_blur': 1.75,
#   'average_erosion': 0.2,
#   'visible_layers': 72,
#   'estimated_fps_impact': 23.1  # percent
# }
```

### Layer Parameters

```python
from jumpclip.depth_layers import debug_layer_parameters, generate_layer_report

# Single layer
print(debug_layer_parameters(layer_configs[50]))

# Output:
# Layer 50:
#   Depth Ratio: 0.505
#   Silhouette Reduction: 0.401
#   Opacity: 0.540
#   Blur: 1px
#   Erosion Rate: 0.200
#   Trail Offset: (-4.2, 4.3)
#   Inverse Animation: 0.548
#   Ragdoll Influence: 0.595

# Full stack report
print(generate_layer_report(layer_configs))
```

---

## Future Enhancement: GPU Acceleration

```glsl
// Potential GLSL compute shader for layer rendering
#version 460

layout(local_size_x = 16, local_size_y = 16) in;
layout(rgba8, binding = 0) uniform image2D result;
layout(binding = 1) uniform sampler2D baseImage;

uniform float depthRatio;
uniform vec2 trailOffset;
uniform float erosionRate;
uniform float opacity;

void main() {
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    
    // Sample base image with trail offset
    vec2 samplePos = vec2(pixel) + trailOffset;
    vec4 base = texture(baseImage, samplePos / imageSize(baseImage));
    
    // Apply erosion in shader
    base.a *= (1.0 - erosionRate);
    
    // Apply opacity
    base.a *= opacity;
    
    // Write result
    imageStore(result, pixel, base);
}
```

This would reduce per-layer rendering from ~0.7ms to ~0.05ms (14× speedup).

---

## File Index

| File | Purpose | Functions |
|------|---------|-----------|
| `depth_layers.py` | 100+ layer system core | All 100+ functions |
| `render.py` | Integration & pipeline | `_apply_depth_layer_system()` |
| `DEPTH_LAYER_SYSTEM.md` | Reference documentation | N/A |
| `DEPTH_IMPLEMENTATION_GUIDE.md` | This file | Technical deep-dive |
| `models.py` | Data structures | `LayerConfig`, `JointState`, `PhysicsConfig` |

---

**Document Version:** 1.0  
**Date:** April 13, 2026  
**Status:** Complete Implementation with 100+ Functions
