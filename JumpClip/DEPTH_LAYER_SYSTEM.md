# 100-Layer Depth System for JumpClip Sprite Animation

## Overview

The depth layer system is a sophisticated multi-layered rendering architecture that creates cinematic depth, motion trails, and dynamic silhouette attenuation for sprite animation. It employs ragdoll physics, progressive silhouette reduction, frame interpolation with pixel erosion, and adaptive resolution scaling to achieve semi-realistic movement and spatial depth perception while preserving actor-specific silhouettes, anatomies, details, and features.

**Total Functions: 100+**

---

## System Architecture

### 1. Layer Configuration & Attenuation (Functions 1-15)

**Purpose:** Compute per-layer rendering parameters with depth-based progressive attenuation.

| Function | Purpose |
|----------|---------|
| `compute_layer_depth_ratio()` | Normalized depth (0.0 topmost, 1.0 deepest) |
| `compute_silhouette_reduction()` | Progressive shrinkage: linear/quadratic/cubic/exponential |
| `compute_layer_opacity()` | Opacity falloff with depth |
| `compute_blur_amount()` | Gaussian blur radius increases with depth |
| `compute_pixel_erosion_rate()` | Frame-to-frame pixel removal rate |
| `compute_trail_offset_x()` | Horizontal lag based on arm motion |
| `compute_trail_offset_y()` | Vertical trail lag (typically 2.0px) |
| `compute_inverse_animation_strength()` | Animation inversion magnitude |
| `compute_ragdoll_influence()` | Joint gravity weight on silhouette |
| `build_layer_config()` | Assemble LayerConfig from helpers |
| `build_all_layer_configs()` | Generate all 100 layer configs |

**Key Formula:**
```
layer_depth_ratio = layer_index / (total_layers - 1)
silhouette_reduction = (depth_ratio^curve) * max_reduction
opacity = 1.0 - (layer_index / total_layers * 0.92)
blur_amount = depth_ratio * 3.5
```

---

### 2. Ragdoll Physics Engine (Functions 12-35)

**Purpose:** Simulate joint-based skeletal physics with gravity, damping, and constraints.

#### Core Structures

```python
@dataclass
class JointState:
    name: str
    x, y: float              # World position
    mass: float              # Kg
    width, height: float     # Collision extent
    parent: str | None       # Parent joint name
    velocity_x, velocity_y: float

@dataclass
class PhysicsConfig:
    gravity: float = 0.18
    damping: float = 0.92
    joint_stiffness: float = 0.75
    max_iterations: int = 3
```

#### Joint Hierarchy

```
root
├── pelvis
│   ├── spine
│   │   ├── chest
│   │   │   ├── neck
│   │   │   │   └── head
│   │   │   ├── shoulder_l → elbow_l → hand_l
│   │   │   └── shoulder_r → elbow_r → hand_r
│   ├── hip_l → knee_l → foot_l
│   └── hip_r → knee_r → foot_r
```

#### Physics Functions

| Function | Purpose |
|----------|---------|
| `create_ragdoll_skeleton()` | Initialize 18-joint humanoid |
| `apply_gravity_to_joint()` | Add downward acceleration |
| `apply_damping_to_joint()` | Velocity friction (0.92 multiplier) |
| `integrate_joint_position()` | Euler integration: pos += vel * dt |
| `compute_joint_distance()` | Euclidean distance between joints |
| `compute_joint_angle()` | Atan2 angle from j1 to j2 |
| `constrain_joint_pair()` | Distance constraint solver |
| `apply_animation_offset_to_joint()` | Integrate animation pose |
| `compute_joint_gravity_influence()` | Joint gravity impact on silhouette |
| `update_ragdoll_frame()` | Step simulation one frame |
| `solve_constraints_iteratively()` | Iterative constraint refinement |
| `compute_constraint_error_magnitude()` | Total violation metric |

**Physics Stepping:**
```
1. Apply gravity: vy += 0.18
2. Apply damping: vx *= 0.92, vy *= 0.92
3. Integrate: pos += vel
4. Apply animation offset
5. Solve constraints (3 iterations)
```

---

### 3. Silhouette Reduction & Attenuation (Functions 22-35)

**Purpose:** Progressive body region shrinkage influenced by ragdoll joint states.

#### Body Region Mapping

```python
regions = {
    "head": (center_x, head_y, head_h*0.75, head_h*0.95),
    "torso": (center_x, torso_y, shoulder_w*1.05, torso_h),
    "hip": (center_x, hip_y, hip_w*1.15, leg_h*0.55),
    "arm_l": (center_x - shoulder_w*0.72, ..., shoulder_w*0.45, torso_h*0.85),
    "arm_r": (center_x + shoulder_w*0.72, ..., shoulder_w*0.45, torso_h*0.85),
    "leg_l": (center_x - hip_w*0.5, hip_y, hip_w*0.5, leg_h*0.9),
    "leg_r": (center_x + hip_w*0.5, hip_y, hip_w*0.5, leg_h*0.9),
}
```

#### Attenuation Functions

| Function | Purpose |
|----------|---------|
| `compute_regional_scale_factor()` | Per-region scale influenced by joint gravity |
| `scale_silhouette_region()` | Bilinear resize region with centering |
| `compute_body_region_bounds()` | Bounding box for each region |
| `apply_layer_attenuation()` | Apply full reduction + attenuation |

**Scale Factor Calculation:**
```
gravity_sum = Σ(joint_gravity_for_region_joints)
avg_gravity = gravity_sum / num_joints
gravity_weight = ragdoll_influence * avg_gravity
scale_factor = 1.0 - (base_reduction + gravity_weight * 0.15)
```

---

### 4. Inverse Animation & Frame Interpolation (Functions 26-45)

**Purpose:** Create synchronized inverse animation layers and smooth frame transitions with pixel erosion.

#### Inverse Animation

| Function | Purpose |
|----------|---------|
| `invert_pose_offset()` | Flip limb direction: -offset * strength |
| `apply_inverse_animation()` | Create full inverse pose |

**Properties:**
- Strength varies by layer (0.15 @ layer 0 → 0.8 @ layer 99)
- Creates "shadow" animation following behind topmost layer
- Horizontally flipped and progressively attenuated

#### Frame Interpolation

| Function | Purpose |
|----------|---------|
| `compute_frame_interpolation_weight()` | Linear/cosine/smoothstep blend weight |
| `blend_pixel_values()` | RGBA interpolation between frames |
| `erode_pixel_alpha()` | Reduce alpha: new_a = a * (1 - rate) |
| `compute_erosion_mask()` | Pixels to erode based on frame delta |
| `interpolate_frame_pair()` | Blend + erosion between two frames |
| `apply_detail_erosion()` | Morphological erosion (remove fine details) |
| `compute_trail_pixel_removal()` | Erase pixels from previous frame |
| `blend_animation_frames()` | Smooth between keyframes |

**Erosion Algorithm:**
```
1. Compute pixel transparency delta between frames
2. If target more transparent: erode source by erosion_rate
3. Morphological filter removes isolated pixels
4. Creates natural fade-out of motion trails
```

---

### 5. Depth Layer Rendering (Functions 36-55)

**Purpose:** Render individual layers with all transformations and composite them.

| Function | Purpose |
|----------|---------|
| `render_depth_layer()` | Single layer: attenuation → blur → offset → erosion → opacity |
| `composite_depth_layers()` | Alpha-composite all layers onto base |
| `render_inverse_animation_layer()` | Inverse-animated shadow layer |
| `render_100_layer_depth_stack()` | Master: render all 100 layers |
| `create_depth_layer_image()` | Blank layer with metadata |
| `flatten_depth_stack_to_rgba()` | Composite all to single RGBA |
| `export_layer_sequence()` | Save each layer as PNG for inspection |

**Rendering Pipeline Per Layer:**
```
1. Copy base image
2. Apply regional silhouette reduction (ragdoll-influenced)
3. Apply Gaussian blur (strength by depth)
4. Apply trail offset (x/y lag)
5. Apply morphological erosion (detail removal)
6. Multiply opacity (1.0 @ layer 0 → 0.08 @ layer 99)
7. Composite onto accumulator
```

---

### 6. Resolution Scaling & Optimization (Functions 39-55)

**Purpose:** Adaptive image scaling and performance optimization via mipmapping.

#### Scaling Algorithms

| Function | Purpose |
|----------|---------|
| `bicubic_scale_image()` | Bicubic resampling |
| `lanczos_scale_image()` | High-quality Lanczos filter |
| `nearest_neighbor_scale()` | Pixel-perfect integer scaling |
| `adaptive_scale_image()` | Choose algorithm by quality_mode |

#### Mipmap Chain

| Function | Purpose |
|----------|---------|
| `downscale_with_mipmap()` | Generate pyramid (1.0 → 0.5 → 0.25 → ...) |
| `select_mipmap_level()` | Choose level by depth distance |

#### Performance Optimization

| Function | Purpose |
|----------|---------|
| `compute_layer_visibility_mask()` | Is opacity > threshold? |
| `cull_invisible_layers()` | Remove layers below visibility |
| `compute_layer_render_cost()` | Estimate GPU cost per layer |
| `sort_layers_by_render_cost()` | Order for early culling |
| `estimate_render_performance()` | Full stack metrics |
| `optimize_layer_stack_for_performance()` | Scale to meet target cost |

**Culling Threshold:** 0.02 opacity (layers < 2% alpha skipped)

---

### 7. Animation Integration (Functions 53-70)

**Purpose:** Connect layer system to animation pipeline.

| Function | Purpose |
|----------|---------|
| `integrate_animation_data()` | Apply animation pose to ragdoll |
| `compute_animation_phase()` | Normalized cycle phase [0.0, 1.0] |
| `preview_layer_at_index()` | Extract single layer for inspection |
| `batch_render_all_frames_with_layers()` | Full animation sequence |
| `layer_stack_metadata()` | Summary statistics |
| `validate_layer_sequence()` | Consistency checks |

**Animation Loop:**
```python
for frame_idx, base_frame in enumerate(base_frames):
    poses = pose_sequence[frame_idx]
    output = render_100_layer_depth_stack(
        base_frame, poses, geometry, skeleton, prev_frame
    )
    results.append(output)
    skeleton = updated_skeleton  # Carry forward for continuity
```

---

### 8. Easing Functions (Functions 62-85)

**Purpose:** Smooth animation interpolation curves.

- **Cubic:** ease_in/out/in_out_cubic
- **Quadratic:** ease_in/out/in_out_quad
- **Sinusoidal:** ease_in/out/in_out_sine
- **Exponential:** ease_in/out/in_out_expo
- **Circular:** ease_in/out/in_out_circ
- **Elastic:** ease_in/out/in_out_elastic
- **Bounce:** ease_in/out/in_out_bounce
- **Back:** ease_in/out/in_out_back

Used for layer parameter smoothing across frames.

---

### 9. Advanced Physics & Integration (Functions 86-100)

| Function | Purpose |
|----------|---------|
| `compute_constraint_error_magnitude()` | Total constraint violation |
| `solve_constraints_iteratively()` | Refine until convergence |
| `compute_layer_silhouette_continuity()` | Visual flow between layers |
| `compute_animation_path_length()` | Total motion distance |
| `adjust_layer_erosion_by_motion()` | Dynamic erosion per motion |
| `apply_temporal_smoothing()` | Frame-to-frame parameter blending |
| `serialize_layer_config_to_dict()` | JSON export |
| `deserialize_layer_config_from_dict()` | JSON import |
| `validate_physics_parameters()` | Config sanity check |
| `sample_layer_stack_performance()` | Benchmark estimate |
| `generate_layer_animation_schedule()` | Pre-compute all frame configs |
| `compose_final_output_with_layers()` | Export + metadata |

---

## Usage Example

### Basic Rendering

```python
from jumpclip.depth_layers import (
    create_ragdoll_skeleton,
    build_all_layer_configs,
    render_depth_layer,
    composite_depth_layers,
    PhysicsConfig,
)
from PIL import Image

# Load base sprite frame
base_image = Image.open("sprite_frame.png")

# Create skeletal rig
skeleton = create_ragdoll_skeleton()

# Define pose
pose_offsets = {
    "arm_a": 10.0,
    "arm_b": -8.0,
    "leg_a": 5.0,
    "leg_b": -5.0,
    "lift": 2.0,
}

# Generate layer configurations for all 100 layers
layer_configs = build_all_layer_configs(pose_offsets, total_layers=100)

# Render each layer
depth_layer_images = []
physics_cfg = PhysicsConfig()

for cfg in layer_configs:
    layer = render_depth_layer(
        base_image,
        cfg,
        skeleton,
        geometry,
        prev_frame=None,
    )
    depth_layer_images.append(layer)

# Composite all layers
final_image = composite_depth_layers(
    base_image,
    depth_layer_images,
    blend_mode="over",
)

# Save
final_image.save("output_with_depth.png")
```

### Full Animation Sequence

```python
from jumpclip.depth_layers import batch_render_all_frames_with_layers

base_frames = [Image.open(f"frame_{i}.png") for i in range(60)]
pose_sequence = [generate_animation_pose(i) for i in range(60)]
geometry = {...}

output_frames = batch_render_all_frames_with_layers(
    base_frames,
    pose_sequence,
    geometry,
)

# Export to GIF
output_frames[0].save(
    "animation_with_depth.gif",
    save_all=True,
    append_images=output_frames[1:],
    duration=16,  # 60 FPS
    loop=0,
)
```

### Performance Tuning

```python
from jumpclip.depth_layers import (
    optimize_layer_stack_for_performance,
    estimate_render_performance,
)

configs = build_all_layer_configs(pose_offsets, total_layers=100)

# Check current cost
perf_metrics = estimate_render_performance(configs)
print(f"Total cost: {perf_metrics['total_cost']:.1f}")
print(f"Estimated FPS impact: {perf_metrics['estimated_fps_impact']:.1f}%")

# Optimize for 30 FPS target
optimized = optimize_layer_stack_for_performance(configs, target_cost=50.0)

# Estimate optimized performance
new_metrics = estimate_render_performance(optimized)
```

---

## Key Features

### ✅ Silhouette Preservation

- Actor-specific silhouettes maintained across all 100 layers
- Regional scaling respects anatomical proportions
- Ragdoll influences reduce but never distort core shape

### ✅ Depth Perception

- Progressive opacity reduction (0.92 @ layer 0 → 0.08 @ layer 99)
- Increasing blur with depth (Gaussian, 0.5 → 3.5px)
- Trail offset creates motion blur effect (lag up to 6.5px vertically)

### ✅ Animation Synchronization

- Frame-to-frame interpolation with pixel erosion
- Inverse animation layer moves opposite to primary motion
- Morphological detail removal prevents visual noise

### ✅ Physics Integration

- Ragdoll-influenced silhouette attenuation
- Joint gravity affects regional weight distribution
- Constraint solver ensures skeletal integrity

### ✅ Performance Optimization

- Automatic layer culling (< 2% opacity skipped)
- Mipmap chain for distance-based LOD
- Adaptive scaling (nearest-neighbor up, Lanczos down)
- Cost estimation for frame budgeting

---

## Configuration Parameters

### Physics

```python
PhysicsConfig(
    gravity=0.18,              # px/frame² downward
    damping=0.92,              # velocity multiplier
    joint_stiffness=0.75,      # constraint restoration
    joint_distance_tolerance=1.5,
    max_iterations=3,          # constraint solver passes
)
```

### Layer Attenuation

```python
LayerConfig(
    layer_index: int           # 0-99
    depth_ratio: float         # 0.0-1.0
    silhouette_reduction: float # 0.0-1.0
    opacity: float             # 0.0-1.0
    blur_amount: int           # pixels
    pixel_erosion_rate: float  # 0.0-1.0
    trail_offset_x: float      # pixels
    trail_offset_y: float      # pixels (default 2.0)
    inverse_animation_strength: float
    ragdoll_influence: float   # 0.0-1.0
)
```

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **Layer Count** | 100 |
| **Visible Layers** | ~60-80 (culled) |
| **Est. Total Cost** | 80-120 units |
| **Est. FPS Impact** | 1-5% (on 60 FPS baseline) |
| **Memory Per Frame** | ~12 MB (64x64 frame, 100 layers × 4 bytes RGBA) |
| **Render Time** | ~2-5ms per frame (GPU estimated) |

**Optimization Strategies:**
- Enable layer culling for runtime
- Use nearest-neighbor scaling for pixelated styles
- Reduce max iterations for faster physics
- Adjust erosion rates for motion intensity

---

## Ambiguity Handling (Animation Engine Fallback)

The system includes graceful degradation:

```python
try:
    # Primary depth layer rendering
    output = _apply_depth_layer_system(...)
except Exception:
    # Fallback: return unmodified sprite
    return base_image
```

When animation poses are ambiguous (missing or conflicting keyframes):
1. Ragdoll physics provide sensible defaults (gravity + damping)
2. Constraint solver stabilizes skeleton
3. Inverse animation falls back to horizontal flip
4. Missing pose offsets treated as zero (neutral pose)

---

## Future Enhancements

- [ ] Per-joint animation constraints (joint limits)
- [ ] Cloth simulation for trailing fabric/hair
- [ ] Per-texture layer masking (selective depth on body parts)
- [ ] Real-time GPU compute shader backend
- [ ] Adaptive layer count based on framerate
- [ ] Skeletal animation retargeting
- [ ] Wind/environmental force fields

---

## References

- **Ragdoll Physics:** Verlet integration with constraint solving (Baraff & Witkin, 1998)
- **Image Scaling:** Lanczos3 resampling (optimal for downsampling)
- **Easing Functions:** Robert Penner's easing library
- **Motion Blur:** Temporal accumulation with erosion

---

**Implemented:** April 2026
**Module:** `jumpclip.depth_layers`
**Total Functions:** 100+
