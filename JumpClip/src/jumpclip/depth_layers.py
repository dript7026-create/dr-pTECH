"""Depth Layer System for Sprite Animation
==============================================

100-layer depth rendering with ragdoll physics influence,
progressive silhouette attenuation, frame-synchronized
inverse animation, and interpolative pixel erosion.

Author: JumpClip Depth Engine
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import NamedTuple

from PIL import Image, ImageDraw


# ============================================================================
# Core Structures
# ============================================================================


@dataclass
class LayerConfig:
    """Configuration for a single depth layer."""

    layer_index: int  # 0-99
    depth_ratio: float  # 0.0 (topmost) to 1.0 (deepest)
    silhouette_reduction: float  # 0.0 to 1.0; how much to shrink
    opacity: float  # 0.0 to 1.0; alpha multiplier
    blur_amount: int  # Gaussian blur radius
    pixel_erosion_rate: float  # 0.0 to 1.0; how much detail to remove
    trail_offset_x: float  # pixels to lag in X
    trail_offset_y: float  # pixels to lag in Y (typically 2.0)
    inverse_animation_strength: float  # 0.0 to 1.0; invert limb poses
    ragdoll_influence: float  # 0.0 to 1.0; apply joint gravity weighting


@dataclass
class JointState:
    """Represents a single joint in the ragdoll."""

    name: str
    x: float
    y: float
    mass: float  # kg
    width: float  # collision width
    height: float  # collision height
    parent: str | None  # parent joint name
    velocity_x: float = 0.0
    velocity_y: float = 0.0


@dataclass
class PhysicsConfig:
    """Physics parameters for ragdoll simulation."""

    gravity: float = 0.18  # pixels/frame^2 downward
    damping: float = 0.92  # velocity multiplier per frame
    joint_stiffness: float = 0.75  # constraint restoration
    joint_distance_tolerance: float = 1.5  # pixels
    max_iterations: int = 3  # constraint solve passes per frame


@dataclass
class AnimationFrameData:
    """Per-frame animation state."""

    frame_index: int
    timestamp: float
    pose_offsets: dict[str, float]  # "arm_a", "leg_b", etc.
    squash_stretch: float
    lift: float
    motion_type: str  # "run", "attack", "idle", etc.


class RagdollJoint(NamedTuple):
    """Simple joint definition."""

    name: str
    x: float
    y: float
    mass: float


# ============================================================================
# Layer Configuration Generation (Functions 1-15)
# ============================================================================


def compute_layer_depth_ratio(layer_index: int, total_layers: int = 100) -> float:
    """Function 1: Compute normalized depth ratio for a layer."""
    if total_layers <= 1:
        return 0.0
    return layer_index / (total_layers - 1)


def compute_silhouette_reduction(layer_index: int, total_layers: int = 100, curve: str = "cubic") -> float:
    """Function 2: Progressive silhouette shrinkage per layer.
    
    curve: "linear", "quadratic", "cubic", "exponential"
    """
    depth = compute_layer_depth_ratio(layer_index, total_layers)
    if curve == "linear":
        return depth * 0.95
    elif curve == "quadratic":
        return (depth ** 2.0) * 0.92
    elif curve == "cubic":
        return (depth ** 3.0) * 0.88
    elif curve == "exponential":
        return (1.0 - math.exp(-depth * 4.0)) * 0.90
    return depth * 0.95


def compute_layer_opacity(layer_index: int, total_layers: int = 100, falloff: str = "exponential") -> float:
    """Function 3: Per-layer opacity with falloff."""
    depth = compute_layer_depth_ratio(layer_index, total_layers)
    base_opacity = 1.0 - (layer_index / total_layers) * 0.92
    if falloff == "linear":
        return max(0.02, base_opacity)
    elif falloff == "quadratic":
        return max(0.02, base_opacity ** 1.5)
    elif falloff == "exponential":
        return max(0.01, base_opacity ** 2.2)
    return base_opacity


def compute_blur_amount(layer_index: int, total_layers: int = 100) -> int:
    """Function 4: Progressive blur increase with depth."""
    depth = compute_layer_depth_ratio(layer_index, total_layers)
    return int(0.5 + (depth * 3.5))


def compute_pixel_erosion_rate(layer_index: int, total_layers: int = 100) -> float:
    """Function 5: Frame-to-frame pixel removal rate."""
    depth = compute_layer_depth_ratio(layer_index, total_layers)
    return 0.05 + (depth * 0.35)


def compute_trail_offset_x(pose_offsets: dict[str, float], layer_index: int, total_layers: int = 100) -> float:
    """Function 6: Horizontal trail lag based on arm motion."""
    depth = compute_layer_depth_ratio(layer_index, total_layers)
    arm_motion = (pose_offsets.get("arm_a", 0.0) + pose_offsets.get("arm_b", 0.0)) * 0.5
    return arm_motion * depth * 0.8


def compute_trail_offset_y(layer_index: int, total_layers: int = 100, base_lag: float = 2.0) -> float:
    """Function 7: Vertical trail lag; typically ~2 pixels behind."""
    depth = compute_layer_depth_ratio(layer_index, total_layers)
    return base_lag + (depth * 4.5)


def compute_inverse_animation_strength(layer_index: int, total_layers: int = 100) -> float:
    """Function 8: How much to invert animation (flip limb directions)."""
    depth = compute_layer_depth_ratio(layer_index, total_layers)
    return 0.15 + (depth * 0.65)


def compute_ragdoll_influence(layer_index: int, total_layers: int = 100) -> float:
    """Function 9: Influence of joint gravity on silhouette reduction."""
    depth = compute_layer_depth_ratio(layer_index, total_layers)
    return 0.32 + (depth * 0.55)


def build_layer_config(
    layer_index: int,
    pose_offsets: dict[str, float],
    total_layers: int = 100,
    attenuation_curve: str = "cubic",
) -> LayerConfig:
    """Function 10: Assemble complete LayerConfig from helper functions."""
    return LayerConfig(
        layer_index=layer_index,
        depth_ratio=compute_layer_depth_ratio(layer_index, total_layers),
        silhouette_reduction=compute_silhouette_reduction(layer_index, total_layers, attenuation_curve),
        opacity=compute_layer_opacity(layer_index, total_layers),
        blur_amount=compute_blur_amount(layer_index, total_layers),
        pixel_erosion_rate=compute_pixel_erosion_rate(layer_index, total_layers),
        trail_offset_x=compute_trail_offset_x(pose_offsets, layer_index, total_layers),
        trail_offset_y=compute_trail_offset_y(layer_index, total_layers),
        inverse_animation_strength=compute_inverse_animation_strength(layer_index, total_layers),
        ragdoll_influence=compute_ragdoll_influence(layer_index, total_layers),
    )


def build_all_layer_configs(
    pose_offsets: dict[str, float],
    total_layers: int = 100,
) -> list[LayerConfig]:
    """Function 11: Generate all 100 layer configs for this frame."""
    return [build_layer_config(i, pose_offsets, total_layers) for i in range(total_layers)]


# ============================================================================
# Ragdoll Physics (Functions 12-35)
# ============================================================================


def create_ragdoll_skeleton() -> dict[str, JointState]:
    """Function 12: Initialize a humanoid ragdoll skeleton."""
    joints = {
        "root": JointState("root", 0.0, 0.0, 1.0, 4.0, 4.0, None),
        "pelvis": JointState("pelvis", 0.0, -8.0, 3.0, 8.0, 6.0, "root"),
        "spine": JointState("spine", 0.0, -18.0, 2.5, 5.0, 12.0, "pelvis"),
        "chest": JointState("chest", 0.0, -28.0, 2.8, 7.0, 10.0, "spine"),
        "neck": JointState("neck", 0.0, -36.0, 1.2, 4.0, 5.0, "chest"),
        "head": JointState("head", 0.0, -44.0, 1.8, 8.0, 10.0, "neck"),
        "shoulder_l": JointState("shoulder_l", -6.0, -26.0, 1.0, 3.0, 3.0, "chest"),
        "shoulder_r": JointState("shoulder_r", 6.0, -26.0, 1.0, 3.0, 3.0, "chest"),
        "elbow_l": JointState("elbow_l", -14.0, -20.0, 1.2, 3.0, 3.0, "shoulder_l"),
        "elbow_r": JointState("elbow_r", 14.0, -20.0, 1.2, 3.0, 3.0, "shoulder_r"),
        "hand_l": JointState("hand_l", -20.0, -12.0, 0.8, 2.0, 2.0, "elbow_l"),
        "hand_r": JointState("hand_r", 20.0, -12.0, 0.8, 2.0, 2.0, "elbow_r"),
        "hip_l": JointState("hip_l", -4.0, -6.0, 2.0, 4.0, 4.0, "pelvis"),
        "hip_r": JointState("hip_r", 4.0, -6.0, 2.0, 4.0, 4.0, "pelvis"),
        "knee_l": JointState("knee_l", -4.0, 6.0, 1.5, 3.0, 3.0, "hip_l"),
        "knee_r": JointState("knee_r", 4.0, 6.0, 1.5, 3.0, 3.0, "hip_r"),
        "foot_l": JointState("foot_l", -3.0, 16.0, 1.0, 3.0, 2.0, "knee_l"),
        "foot_r": JointState("foot_r", 3.0, 16.0, 1.0, 3.0, 2.0, "knee_r"),
    }
    return joints


def apply_gravity_to_joint(joint: JointState, physics_cfg: PhysicsConfig) -> JointState:
    """Function 13: Apply downward gravitational acceleration."""
    new_vy = joint.velocity_y + physics_cfg.gravity
    return JointState(
        name=joint.name,
        x=joint.x,
        y=joint.y,
        mass=joint.mass,
        width=joint.width,
        height=joint.height,
        parent=joint.parent,
        velocity_x=joint.velocity_x,
        velocity_y=new_vy,
    )


def apply_damping_to_joint(joint: JointState, physics_cfg: PhysicsConfig) -> JointState:
    """Function 14: Apply velocity damping (air resistance)."""
    return JointState(
        name=joint.name,
        x=joint.x,
        y=joint.y,
        mass=joint.mass,
        width=joint.width,
        height=joint.height,
        parent=joint.parent,
        velocity_x=joint.velocity_x * physics_cfg.damping,
        velocity_y=joint.velocity_y * physics_cfg.damping,
    )


def integrate_joint_position(joint: JointState, time_step: float = 1.0) -> JointState:
    """Function 15: Update position from velocity (Euler integration)."""
    new_x = joint.x + (joint.velocity_x * time_step)
    new_y = joint.y + (joint.velocity_y * time_step)
    return JointState(
        name=joint.name,
        x=new_x,
        y=new_y,
        mass=joint.mass,
        width=joint.width,
        height=joint.height,
        parent=joint.parent,
        velocity_x=joint.velocity_x,
        velocity_y=joint.velocity_y,
    )


def compute_joint_distance(j1: JointState, j2: JointState) -> float:
    """Function 16: Euclidean distance between two joints."""
    dx = j2.x - j1.x
    dy = j2.y - j1.y
    return math.sqrt((dx * dx) + (dy * dy))


def compute_joint_angle(j1: JointState, j2: JointState) -> float:
    """Function 17: Angle from j1 to j2 in radians."""
    dx = j2.x - j1.x
    dy = j2.y - j1.y
    return math.atan2(dy, dx)


def constrain_joint_pair(
    parent: JointState,
    child: JointState,
    target_distance: float,
    physics_cfg: PhysicsConfig,
) -> tuple[JointState, JointState]:
    """Function 18: Constraint solver for parent-child joint pair."""
    current_dist = compute_joint_distance(parent, child)
    if current_dist < 0.01:
        return parent, child
    
    error = current_dist - target_distance
    correction = error * physics_cfg.joint_stiffness
    angle = compute_joint_angle(parent, child)
    
    correction_x = math.cos(angle) * correction
    correction_y = math.sin(angle) * correction
    
    # Move child toward target distance
    new_child_x = child.x - (correction_x * 0.6)
    new_child_y = child.y - (correction_y * 0.6)
    
    new_child = JointState(
        name=child.name,
        x=new_child_x,
        y=new_child_y,
        mass=child.mass,
        width=child.width,
        height=child.height,
        parent=child.parent,
        velocity_x=child.velocity_x,
        velocity_y=child.velocity_y,
    )
    return parent, new_child


def apply_animation_offset_to_joint(
    joint: JointState,
    pose_offset: float,
    animation_axis: str = "horizontal",
) -> JointState:
    """Function 19: Apply animation pose offset to joint position."""
    if animation_axis == "horizontal":
        return JointState(
            name=joint.name,
            x=joint.x + pose_offset,
            y=joint.y,
            mass=joint.mass,
            width=joint.width,
            height=joint.height,
            parent=joint.parent,
            velocity_x=joint.velocity_x,
            velocity_y=joint.velocity_y,
        )
    else:  # vertical
        return JointState(
            name=joint.name,
            x=joint.x,
            y=joint.y + pose_offset,
            mass=joint.mass,
            width=joint.width,
            height=joint.height,
            parent=joint.parent,
            velocity_x=joint.velocity_x,
            velocity_y=joint.velocity_y,
        )


def compute_joint_gravity_influence(
    joint: JointState,
    skeleton: dict[str, JointState],
    physics_cfg: PhysicsConfig,
) -> float:
    """Function 20: Compute how much gravity affects silhouette of this joint."""
    if joint.parent is None:
        return 0.0
    parent_joint = skeleton.get(joint.parent)
    if parent_joint is None:
        return 0.0
    
    # Distance from parent: larger distance = more gravity influence
    dist = compute_joint_distance(joint, parent_joint)
    return min(1.0, dist / 20.0)


def update_ragdoll_frame(
    skeleton: dict[str, JointState],
    pose_offsets: dict[str, float],
    physics_cfg: PhysicsConfig,
) -> dict[str, JointState]:
    """Function 21: Step ragdoll physics simulation one frame."""
    updated = {}
    for name, joint in skeleton.items():
        j = apply_gravity_to_joint(joint, physics_cfg)
        j = apply_damping_to_joint(j, physics_cfg)
        j = integrate_joint_position(j)
        
        # Apply animation offset if available
        if name in pose_offsets:
            j = apply_animation_offset_to_joint(j, pose_offsets[name])
        
        updated[name] = j
    
    # Constraint solving (multiple iterations)
    for _ in range(physics_cfg.max_iterations):
        for name, joint in updated.items():
            if joint.parent is not None and joint.parent in updated:
                parent = updated[joint.parent]
                target_dist = 12.0  # Default constraint distance
                parent, child = constrain_joint_pair(parent, joint, target_dist, physics_cfg)
                updated[joint.parent] = parent
                updated[name] = child
    
    return updated


# ============================================================================
# Silhouette Reduction & Attenuation (Functions 22-35)
# ============================================================================


def compute_regional_scale_factor(
    layer_cfg: LayerConfig,
    region_name: str,
    skeleton: dict[str, JointState],
) -> float:
    """Function 22: Per-region scale factor influenced by ragdoll gravity."""
    base_reduction = layer_cfg.silhouette_reduction
    
    # Map region to relevant joints
    region_joints = {
        "head": ["head", "neck"],
        "torso": ["chest", "spine"],
        "hip": ["pelvis"],
        "arm_l": ["shoulder_l", "elbow_l", "hand_l"],
        "arm_r": ["shoulder_r", "elbow_r", "hand_r"],
        "leg_l": ["hip_l", "knee_l", "foot_l"],
        "leg_r": ["hip_r", "knee_r", "foot_r"],
    }
    
    if region_name not in region_joints:
        return 1.0 - base_reduction
    
    joint_names = region_joints[region_name]
    gravity_sum = 0.0
    for jname in joint_names:
        if jname in skeleton:
            joint = skeleton[jname]
            gravity_sum += compute_joint_gravity_influence(joint, skeleton, PhysicsConfig())
    
    avg_gravity = gravity_sum / max(1, len(joint_names))
    gravity_weight = layer_cfg.ragdoll_influence * avg_gravity
    
    return 1.0 - (base_reduction + gravity_weight * 0.15)


def scale_silhouette_region(
    image: Image.Image,
    region_bounds: tuple[int, int, int, int],
    scale_factor: float,
) -> Image.Image:
    """Function 23: Scale a rectangular region of the image."""
    x0, y0, x1, y1 = region_bounds
    region_width = x1 - x0
    region_height = y1 - y0
    
    if region_width <= 0 or region_height <= 0:
        return image
    
    # Extract region
    region = image.crop((x0, y0, x1, y1))
    
    # Scale
    new_width = max(1, int(region_width * scale_factor))
    new_height = max(1, int(region_height * scale_factor))
    scaled = region.resize((new_width, new_height), Image.Resampling.BILINEAR)
    
    # Paste back centered
    offset_x = (region_width - new_width) // 2
    offset_y = (region_height - new_height) // 2
    output = image.copy()
    output.paste(scaled, (x0 + offset_x, y0 + offset_y), scaled)
    
    return output


def compute_body_region_bounds(
    canvas_size: int,
    center_x: float,
    head_top: float,
    head_h: float,
    torso_h: float,
    hip_y: float,
    floor_y: float,
    shoulder_w: float,
    hip_w: float,
    region_name: str,
) -> tuple[int, int, int, int]:
    """Function 24: Compute bounding box for a body region."""
    definitions = {
        "head": (
            int(center_x - (head_h * 0.5)),
            int(head_top),
            int(center_x + (head_h * 0.5)),
            int(head_top + head_h),
        ),
        "torso": (
            int(center_x - (shoulder_w * 0.6)),
            int(head_top + head_h),
            int(center_x + (shoulder_w * 0.6)),
            int(head_top + head_h + torso_h),
        ),
        "hip": (
            int(center_x - (hip_w * 0.6)),
            int(hip_y),
            int(center_x + (hip_w * 0.6)),
            int(hip_y + 8),
        ),
        "arm_l": (
            int(center_x - (shoulder_w * 1.0)),
            int(head_top + head_h),
            int(center_x - (shoulder_w * 0.3)),
            int(floor_y - 2),
        ),
        "arm_r": (
            int(center_x + (shoulder_w * 0.3)),
            int(head_top + head_h),
            int(center_x + (shoulder_w * 1.0)),
            int(floor_y - 2),
        ),
        "leg_l": (
            int(center_x - (hip_w * 0.5)),
            int(hip_y),
            int(center_x - (hip_w * 0.1)),
            int(floor_y),
        ),
        "leg_r": (
            int(center_x + (hip_w * 0.1)),
            int(hip_y),
            int(center_x + (hip_w * 0.5)),
            int(floor_y),
        ),
    }
    
    if region_name in definitions:
        bounds = definitions[region_name]
        x0, y0, x1, y1 = bounds
        x0 = max(0, min(canvas_size, x0))
        y0 = max(0, min(canvas_size, y0))
        x1 = max(0, min(canvas_size, x1))
        y1 = max(0, min(canvas_size, y1))
        return (x0, y0, x1, y1)
    
    return (0, 0, 0, 0)


def apply_layer_attenuation(
    image: Image.Image,
    layer_cfg: LayerConfig,
    skeleton: dict[str, JointState],
    geometry: dict[str, float],
) -> Image.Image:
    """Function 25: Apply full silhouette reduction and attenuation."""
    result = image.copy()
    
    region_names = ["head", "torso", "hip", "arm_l", "arm_r", "leg_l", "leg_r"]
    for region in region_names:
        bounds = compute_body_region_bounds(
            image.size[0],
            geometry["center_x"],
            geometry["head_top"],
            geometry["head_h"],
            geometry["torso_h"],
            geometry["hip_y"],
            geometry["floor_y"],
            geometry["shoulder_w"],
            geometry["hip_w"],
            region,
        )
        
        scale = compute_regional_scale_factor(layer_cfg, region, skeleton)
        result = scale_silhouette_region(result, bounds, scale)
    
    return result


# ============================================================================
# Inverse Animation & Frame Interpolation (Functions 26-45)
# ============================================================================


def invert_pose_offset(offset: float, invert_strength: float) -> float:
    """Function 26: Reverse a pose offset (flip limb direction)."""
    return -offset * invert_strength


def apply_inverse_animation(
    pose_offsets: dict[str, float],
    inverse_strength: float,
) -> dict[str, float]:
    """Function 27: Create inverse pose from current pose."""
    return {
        key: invert_pose_offset(val, inverse_strength)
        for key, val in pose_offsets.items()
    }


def compute_frame_interpolation_weight(
    current_frame_index: int,
    total_frames: int,
    interp_mode: str = "linear",
) -> float:
    """Function 28: Interpolation weight for frame blending."""
    phase = (current_frame_index % max(1, total_frames)) / max(1, total_frames)
    if interp_mode == "linear":
        return phase
    elif interp_mode == "cosine":
        return (1.0 - math.cos(phase * math.pi)) * 0.5
    elif interp_mode == "smoothstep":
        return phase * phase * (3.0 - 2.0 * phase)
    return phase


def blend_pixel_values(
    prev_pixel: tuple[int, int, int, int],
    curr_pixel: tuple[int, int, int, int],
    weight: float,
) -> tuple[int, int, int, int]:
    """Function 29: Linear blend between two RGBA pixels."""
    r = int((prev_pixel[0] * (1.0 - weight)) + (curr_pixel[0] * weight))
    g = int((prev_pixel[1] * (1.0 - weight)) + (curr_pixel[1] * weight))
    b = int((prev_pixel[2] * (1.0 - weight)) + (curr_pixel[2] * weight))
    a = int((prev_pixel[3] * (1.0 - weight)) + (curr_pixel[3] * weight))
    return (r, g, b, a)


def erode_pixel_alpha(
    pixel: tuple[int, int, int, int],
    erosion_rate: float,
) -> tuple[int, int, int, int]:
    """Function 30: Reduce alpha channel by erosion rate."""
    r, g, b, a = pixel
    new_a = max(0, int(a * (1.0 - erosion_rate)))
    return (r, g, b, new_a)


def compute_erosion_mask(
    source: Image.Image,
    target: Image.Image,
    erosion_rate: float,
) -> Image.Image:
    """Function 31: Compute which pixels should be eroded based on frame change."""
    result = source.copy()
    src_pix = source.load()
    tgt_pix = target.load()
    res_pix = result.load()
    
    for y in range(source.height):
        for x in range(source.width):
            src = src_pix[x, y]
            tgt = tgt_pix[x, y]
            
            # If target is more transparent, erode source
            if tgt[3] < src[3]:
                res_pix[x, y] = erode_pixel_alpha(src, erosion_rate)
            else:
                res_pix[x, y] = src
    
    return result


def interpolate_frame_pair(
    prev_frame: Image.Image,
    curr_frame: Image.Image,
    weight: float,
) -> Image.Image:
    """Function 32: Blend two frames with erosion."""
    result = Image.new("RGBA", prev_frame.size, (0, 0, 0, 0))
    prev_pix = prev_frame.load()
    curr_pix = curr_frame.load()
    res_pix = result.load()
    
    for y in range(result.height):
        for x in range(result.width):
            prev = prev_pix[x, y]
            curr = curr_pix[x, y]
            blended = blend_pixel_values(prev, curr, weight)
            res_pix[x, y] = blended
    
    return result


def apply_detail_erosion(
    image: Image.Image,
    erosion_rate: float,
    kernel_size: int = 3,
) -> Image.Image:
    """Function 33: Morphological erosion to remove fine detail."""
    from PIL import ImageFilter
    
    if erosion_rate <= 0.01:
        return image
    
    # Apply median filter to remove noise
    iterations = int(erosion_rate * 3)
    result = image
    for _ in range(iterations):
        result = result.filter(ImageFilter.MedianFilter(size=kernel_size))
    
    return result


def compute_trail_pixel_removal(
    image: Image.Image,
    prev_frame: Image.Image | None,
    erosion_rate: float,
) -> Image.Image:
    """Function 34: Remove pixels that were in previous frame."""
    if prev_frame is None:
        return image
    
    result = image.copy()
    result_pix = result.load()
    prev_pix = prev_frame.load()
    
    for y in range(image.height):
        for x in range(image.width):
            curr = result_pix[x, y]
            if prev_frame and prev_pix[x, y][3] > 0:
                # Erode pixels that existed in previous frame
                result_pix[x, y] = erode_pixel_alpha(curr, erosion_rate * 0.5)
    
    return result


def blend_animation_frames(
    frames: list[Image.Image],
    current_index: int,
    lerp_weight: float,
) -> Image.Image:
    """Function 35: Smoothly blend between animation keyframes."""
    if len(frames) < 2:
        return frames[current_index] if frames else Image.new("RGBA", (64, 64))
    
    next_index = (current_index + 1) % len(frames)
    return interpolate_frame_pair(frames[current_index], frames[next_index], lerp_weight)


# ============================================================================
# Depth Layer Rendering (Functions 36-55)
# ============================================================================


def render_depth_layer(
    base_image: Image.Image,
    layer_cfg: LayerConfig,
    skeleton: dict[str, JointState],
    geometry: dict[str, float],
    prev_frame: Image.Image | None = None,
) -> Image.Image:
    """Function 36: Render a single depth layer with all transformations."""
    result = base_image.copy()
    
    # 1. Apply ragdoll-influenced silhouette reduction
    result = apply_layer_attenuation(result, layer_cfg, skeleton, geometry)
    
    # 2. Apply blur
    if layer_cfg.blur_amount > 0:
        from PIL import ImageFilter
        result = result.filter(ImageFilter.GaussianBlur(radius=layer_cfg.blur_amount))
    
    # 3. Apply trail offset
    from PIL import Image as PILImage
    offset_image = PILImage.new("RGBA", result.size, (0, 0, 0, 0))
    offset_x = int(layer_cfg.trail_offset_x)
    offset_y = int(layer_cfg.trail_offset_y)
    if offset_x != 0 or offset_y != 0:
        offset_image.paste(result, (offset_x, offset_y), result)
        result = offset_image
    
    # 4. Apply pixel erosion
    if layer_cfg.pixel_erosion_rate > 0.01:
        result = apply_detail_erosion(result, layer_cfg.pixel_erosion_rate)
    
    # 5. Apply opacity
    if layer_cfg.opacity < 1.0:
        alpha = result.getchannel("A")
        alpha = alpha.point(lambda x: int(x * layer_cfg.opacity))
        result.putalpha(alpha)
    
    return result


def composite_depth_layers(
    base_image: Image.Image,
    layers: list[Image.Image],
    blend_mode: str = "over",
) -> Image.Image:
    """Function 37: Composite all depth layers onto base image."""
    result = base_image.copy()
    for layer in layers:
        if blend_mode == "over":
            result = Image.alpha_composite(result, layer)
        elif blend_mode == "screen":
            # Screen blend mode
            result_data = result.tobytes("RGBA")
            layer_data = layer.tobytes("RGBA")
    
    return result


def render_inverse_animation_layer(
    base_image: Image.Image,
    layer_cfg: LayerConfig,
    pose_offsets: dict[str, float],
    geometry: dict[str, float],
) -> Image.Image:
    """Function 38: Render inverse-animated shadow layer."""
    inverse_offsets = apply_inverse_animation(pose_offsets, layer_cfg.inverse_animation_strength)
    
    # Create inverse pose image (this would call back to sprite renderer)
    # For now, return attenuated version
    result = base_image.copy()
    
    # Simple horizontal flip and scale as proxy
    if layer_cfg.inverse_animation_strength > 0.3:
        result = result.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    
    return result


# ============================================================================
# Resolution Scaling & Optimization (Functions 39-55)
# ============================================================================


def bicubic_scale_image(image: Image.Image, scale_factor: float) -> Image.Image:
    """Function 39: High-quality bicubic scaling."""
    if abs(scale_factor - 1.0) < 0.01:
        return image
    
    new_width = max(1, int(image.width * scale_factor))
    new_height = max(1, int(image.height * scale_factor))
    return image.resize((new_width, new_height), Image.Resampling.BICUBIC)


def lanczos_scale_image(image: Image.Image, scale_factor: float) -> Image.Image:
    """Function 40: Ultra-high-quality Lanczos scaling."""
    if abs(scale_factor - 1.0) < 0.01:
        return image
    
    new_width = max(1, int(image.width * scale_factor))
    new_height = max(1, int(image.height * scale_factor))
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def nearest_neighbor_scale(image: Image.Image, scale_factor: float) -> Image.Image:
    """Function 41: Fast nearest-neighbor scaling (pixel-perfect)."""
    if abs(scale_factor - 1.0) < 0.01:
        return image
    
    new_width = max(1, int(image.width * scale_factor))
    new_height = max(1, int(image.height * scale_factor))
    return image.resize((new_width, new_height), Image.Resampling.NEAREST)


def adaptive_scale_image(
    image: Image.Image,
    scale_factor: float,
    quality_mode: str = "auto",
) -> Image.Image:
    """Function 42: Choose scaling algorithm based on quality mode and factor."""
    if quality_mode == "fast":
        return nearest_neighbor_scale(image, scale_factor)
    elif quality_mode == "high":
        return lanczos_scale_image(image, scale_factor)
    elif quality_mode == "auto":
        # Use nearest-neighbor for scale-up, Lanczos for scale-down
        if scale_factor >= 1.0:
            return nearest_neighbor_scale(image, scale_factor)
        else:
            return lanczos_scale_image(image, scale_factor)
    else:
        return bicubic_scale_image(image, scale_factor)


def downscale_with_mipmap(image: Image.Image, levels: int = 3) -> list[Image.Image]:
    """Function 43: Generate mipmap chain for progressive detail reduction."""
    pyramid = [image]
    current = image
    for _ in range(levels - 1):
        current = lanczos_scale_image(current, 0.5)
        pyramid.append(current)
    return pyramid


def select_mipmap_level(
    pyramid: list[Image.Image],
    distance: float,
) -> Image.Image:
    """Function 44: Select appropriate mipmap level based on depth distance."""
    level = min(len(pyramid) - 1, int(distance * (len(pyramid) - 1) / 100.0))
    return pyramid[max(0, level)]


# ============================================================================
# Composition & Output (Functions 46-60)
# ============================================================================


def render_100_layer_depth_stack(
    base_frame: Image.Image,
    pose_offsets: dict[str, float],
    geometry: dict[str, float],
    skeleton: dict[str, JointState] | None = None,
    prev_frame: Image.Image | None = None,
) -> Image.Image:
    """Function 45: Master function to render all 100 depth layers."""
    if skeleton is None:
        skeleton = create_ragdoll_skeleton()
    
    # Build all layer configs
    layer_configs = build_all_layer_configs(pose_offsets, total_layers=100)
    
    # Render each layer
    depth_layers = []
    for cfg in layer_configs:
        layer = render_depth_layer(base_frame, cfg, skeleton, geometry, prev_frame)
        depth_layers.append(layer)
    
    # Composite all layers
    final = composite_depth_layers(base_frame, depth_layers, blend_mode="over")
    
    return final


def create_depth_layer_image(
    width: int,
    height: int,
    layer_index: int,
    total_layers: int = 100,
) -> Image.Image:
    """Function 46: Create a blank layer image with metadata."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    return img


def flatten_depth_stack_to_rgba(layers: list[Image.Image]) -> Image.Image:
    """Function 47: Composite all layers into single RGBA image."""
    if not layers:
        return Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    
    result = layers[0].copy()
    for layer in layers[1:]:
        result = Image.alpha_composite(result, layer)
    
    return result


def export_layer_sequence(
    layers: list[Image.Image],
    output_dir: str,
    prefix: str = "depth_layer",
) -> list[str]:
    """Function 48: Export each layer as a separate PNG for inspection."""
    from pathlib import Path
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    paths = []
    for idx, layer in enumerate(layers):
        filepath = out_path / f"{prefix}_{idx:03d}.png"
        layer.save(filepath)
        paths.append(str(filepath))
    
    return paths


def compute_layer_visibility_mask(
    layer_index: int,
    total_layers: int = 100,
    visibility_threshold: float = 0.02,
) -> bool:
    """Function 49: Determine if a layer is visible enough to render."""
    opacity = compute_layer_opacity(layer_index, total_layers)
    return opacity > visibility_threshold


def cull_invisible_layers(
    layers: list[LayerConfig],
    total_layers: int = 100,
) -> list[LayerConfig]:
    """Function 50: Remove layers below visibility threshold."""
    return [
        cfg
        for cfg in layers
        if compute_layer_visibility_mask(cfg.layer_index, total_layers)
    ]


def compute_layer_render_cost(layer_cfg: LayerConfig) -> float:
    """Function 51: Estimate GPU/CPU cost for rendering this layer."""
    # Higher opacity, larger blur, more erosion = higher cost
    base_cost = 1.0
    cost = base_cost + (layer_cfg.opacity * 0.5)
    cost += (layer_cfg.blur_amount * 0.1)
    cost += (layer_cfg.pixel_erosion_rate * 0.3)
    return cost


def sort_layers_by_render_cost(layers: list[LayerConfig]) -> list[LayerConfig]:
    """Function 52: Sort layers from cheapest to most expensive."""
    return sorted(layers, key=compute_layer_render_cost)


# ============================================================================
# Animation Integration (Functions 53-70)
# ============================================================================


def integrate_animation_data(
    anim_frame: AnimationFrameData,
    ragdoll: dict[str, JointState],
) -> dict[str, JointState]:
    """Function 53: Integrate animation pose data into ragdoll state."""
    result = ragdoll.copy()
    for joint_name, pose_offset in anim_frame.pose_offsets.items():
        if joint_name in result:
            result[joint_name] = apply_animation_offset_to_joint(
                result[joint_name],
                pose_offset,
                "horizontal",
            )
    return result


def compute_animation_phase(
    frame_index: int,
    total_frames: int,
) -> float:
    """Function 54: Normalized phase in animation cycle [0.0, 1.0]."""
    return (frame_index % max(1, total_frames)) / max(1, total_frames)


def preview_layer_at_index(
    layers: list[Image.Image],
    index: int,
) -> Image.Image:
    """Function 55: Extract and return a single layer for inspection."""
    if 0 <= index < len(layers):
        return layers[index]
    return Image.new("RGBA", (64, 64), (0, 0, 0, 0))


def batch_render_all_frames_with_layers(
    base_frames: list[Image.Image],
    pose_sequence: list[dict[str, float]],
    geometry: dict[str, float],
) -> list[Image.Image]:
    """Function 56: Render all animation frames with 100-layer depth."""
    results = []
    skeleton = create_ragdoll_skeleton()
    prev_frame = None
    
    for frame_idx, base_frame in enumerate(base_frames):
        poses = pose_sequence[frame_idx] if frame_idx < len(pose_sequence) else {}
        
        output = render_100_layer_depth_stack(
            base_frame,
            poses,
            geometry,
            skeleton,
            prev_frame,
        )
        results.append(output)
        prev_frame = output
    
    return results


def layer_stack_metadata(layers: list[LayerConfig]) -> dict:
    """Function 57: Generate metadata summary of layer stack."""
    return {
        "total_layers": len(layers),
        "avg_opacity": sum(l.opacity for l in layers) / max(1, len(layers)),
        "total_blur": sum(l.blur_amount for l in layers),
        "avg_erosion": sum(l.pixel_erosion_rate for l in layers) / max(1, len(layers)),
        "total_trail_offset_y": sum(l.trail_offset_y for l in layers),
    }


def validate_layer_sequence(layers: list[Image.Image]) -> bool:
    """Function 58: Validate layer sequence for consistency."""
    if not layers:
        return False
    
    # All layers should have same dimensions
    width, height = layers[0].size
    for layer in layers[1:]:
        if layer.size != (width, height):
            return False
    
    # Opacity should generally decrease with depth
    opacities = [compute_layer_opacity(i, len(layers)) for i in range(len(layers))]
    for i in range(1, len(opacities)):
        if opacities[i] > opacities[i - 1] + 0.01:  # Allow small tolerance
            return False
    
    return True


# ============================================================================
# Utility & Debugging Functions (59-100+)
# ============================================================================


def debug_layer_parameters(layer_cfg: LayerConfig) -> str:
    """Function 59: Human-readable layer configuration."""
    return f"""Layer {layer_cfg.layer_index}:
  Depth Ratio: {layer_cfg.depth_ratio:.3f}
  Silhouette Reduction: {layer_cfg.silhouette_reduction:.3f}
  Opacity: {layer_cfg.opacity:.3f}
  Blur: {layer_cfg.blur_amount}px
  Erosion Rate: {layer_cfg.pixel_erosion_rate:.3f}
  Trail Offset: ({layer_cfg.trail_offset_x:.1f}, {layer_cfg.trail_offset_y:.1f})
  Inverse Animation: {layer_cfg.inverse_animation_strength:.3f}
  Ragdoll Influence: {layer_cfg.ragdoll_influence:.3f}
"""


def generate_layer_report(layers: list[LayerConfig]) -> str:
    """Function 60: Full report of layer stack configuration."""
    report_lines = [
        f"=== Depth Layer Stack Report ({len(layers)} layers) ===",
        "",
    ]
    
    for i in [0, len(layers) // 4, len(layers) // 2, (3 * len(layers)) // 4, len(layers) - 1]:
        if 0 <= i < len(layers):
            report_lines.append(debug_layer_parameters(layers[i]))
            report_lines.append("")
    
    metadata = layer_stack_metadata(layers)
    report_lines.append("Summary:")
    for key, val in metadata.items():
        report_lines.append(f"  {key}: {val}")
    
    return "\n".join(report_lines)


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Function 61: Clamp value to range."""
    return max(min_val, min(max_val, value))


def ease_in_cubic(t: float) -> float:
    """Function 62: Cubic ease-in function."""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Function 63: Cubic ease-out function."""
    return 1.0 - ((1.0 - t) ** 3.0)


def ease_in_out_cubic(t: float) -> float:
    """Function 64: Cubic ease-in-out function."""
    if t < 0.5:
        return 2.0 * t * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 3.0) * 0.5


def ease_in_quad(t: float) -> float:
    """Function 65: Quadratic ease-in."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Function 66: Quadratic ease-out."""
    return 1.0 - ((1.0 - t) ** 2.0)


def ease_in_out_quad(t: float) -> float:
    """Function 67: Quadratic ease-in-out."""
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 2.0) * 0.5


def ease_in_sine(t: float) -> float:
    """Function 68: Sinusoidal ease-in."""
    return 1.0 - math.cos((t * math.pi) * 0.5)


def ease_out_sine(t: float) -> float:
    """Function 69: Sinusoidal ease-out."""
    return math.sin((t * math.pi) * 0.5)


def ease_in_out_sine(t: float) -> float:
    """Function 70: Sinusoidal ease-in-out."""
    return -(math.cos(t * math.pi) - 1.0) * 0.5


def ease_in_expo(t: float) -> float:
    """Function 71: Exponential ease-in."""
    return 0.0 if t == 0.0 else (2.0 ** (10.0 * t - 10.0))


def ease_out_expo(t: float) -> float:
    """Function 72: Exponential ease-out."""
    return 1.0 if t == 1.0 else (1.0 - (2.0 ** (-10.0 * t)))


def ease_in_out_expo(t: float) -> float:
    """Function 73: Exponential ease-in-out."""
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    if t < 0.5:
        return (2.0 ** (20.0 * t - 10.0)) * 0.5
    return (2.0 - (2.0 ** (-20.0 * t + 10.0))) * 0.5


def ease_in_circ(t: float) -> float:
    """Function 74: Circular ease-in."""
    return 1.0 - math.sqrt(1.0 - (t * t))


def ease_out_circ(t: float) -> float:
    """Function 75: Circular ease-out."""
    return math.sqrt(1.0 - ((t - 1.0) ** 2.0))


def ease_in_out_circ(t: float) -> float:
    """Function 76: Circular ease-in-out."""
    if t < 0.5:
        return (1.0 - math.sqrt(1.0 - (2.0 * t) ** 2.0)) * 0.5
    return (math.sqrt(1.0 - ((2.0 * t - 2.0) ** 2.0)) + 1.0) * 0.5


def ease_in_elastic(t: float) -> float:
    """Function 77: Elastic ease-in."""
    c4 = (2.0 * math.pi) / 3.0
    return 0.0 if t == 0.0 else (1.0 if t == 1.0 else -(2.0 ** (10.0 * t - 10.0)) * math.sin((t * 10.0 - 10.75) * c4))


def ease_out_elastic(t: float) -> float:
    """Function 78: Elastic ease-out."""
    c4 = (2.0 * math.pi) / 3.0
    return 1.0 if t == 0.0 else (0.0 if t == 1.0 else (2.0 ** (-10.0 * t)) * math.sin((t * 10.0 - 0.75) * c4) + 1.0)


def ease_in_out_elastic(t: float) -> float:
    """Function 79: Elastic ease-in-out."""
    c5 = (2.0 * math.pi) / 4.5
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    if t < 0.5:
        return -(2.0 ** (20.0 * t - 10.0)) * math.sin((20.0 * t - 11.125) * c5) * 0.5
    return (2.0 ** (-20.0 * t + 10.0)) * math.sin((20.0 * t - 11.125) * c5) * 0.5 + 1.0


def ease_out_bounce(t: float) -> float:
    """Function 80: Bounce ease-out."""
    n1 = 7.5625
    d1 = 2.75
    if t < 1.0 / d1:
        return n1 * t * t
    elif t < 2.0 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def ease_in_bounce(t: float) -> float:
    """Function 81: Bounce ease-in."""
    return 1.0 - ease_out_bounce(1.0 - t)


def ease_in_out_bounce(t: float) -> float:
    """Function 82: Bounce ease-in-out."""
    if t < 0.5:
        return (1.0 - ease_out_bounce(1.0 - 2.0 * t)) * 0.5
    return (1.0 + ease_out_bounce(2.0 * t - 1.0)) * 0.5


def ease_in_back(t: float, c1: float = 1.70158) -> float:
    """Function 83: Back ease-in."""
    c3 = c1 + 1.0
    return c3 * t * t * t - c1 * t * t


def ease_out_back(t: float, c1: float = 1.70158) -> float:
    """Function 84: Back ease-out."""
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3.0) + c1 * ((t - 1.0) ** 2.0)


def ease_in_out_back(t: float, c1: float = 1.70158) -> float:
    """Function 85: Back ease-in-out."""
    c2 = c1 * 1.525
    if t < 0.5:
        return ((2.0 * t) ** 2.0) * ((c2 + 1.0) * 2.0 * t - c2) * 0.5
    return (((2.0 * t - 2.0) ** 2.0) * ((c2 + 1.0) * (t * 2.0 - 2.0) + c2) + 2.0) * 0.5


# ============================================================================
# Advanced Physics & Integration (Functions 86-100)
# ============================================================================


def compute_constraint_error_magnitude(
    skeleton: dict[str, JointState],
) -> float:
    """Function 86: Measure total constraint violation in skeleton."""
    error_sum = 0.0
    for name, joint in skeleton.items():
        if joint.parent is not None and joint.parent in skeleton:
            parent = skeleton[joint.parent]
            dist = compute_joint_distance(joint, parent)
            target = 12.0
            error_sum += abs(dist - target)
    return error_sum


def solve_constraints_iteratively(
    skeleton: dict[str, JointState],
    physics_cfg: PhysicsConfig,
    max_error: float = 1.0,
) -> dict[str, JointState]:
    """Function 87: Iteratively refine constraints until convergence."""
    working = skeleton.copy()
    iteration = 0
    while iteration < physics_cfg.max_iterations:
        error = compute_constraint_error_magnitude(working)
        if error < max_error:
            break
        
        for name, joint in working.items():
            if joint.parent is not None and joint.parent in working:
                parent = working[joint.parent]
                parent, child = constrain_joint_pair(parent, joint, 12.0, physics_cfg)
                working[joint.parent] = parent
                working[name] = child
        
        iteration += 1
    
    return working


def compute_layer_silhouette_continuity(
    prev_layer: Image.Image,
    curr_layer: Image.Image,
) -> float:
    """Function 88: Measure visual continuity between successive layers."""
    prev_pix = prev_layer.load()
    curr_pix = curr_layer.load()
    
    diff_sum = 0.0
    for y in range(prev_layer.height):
        for x in range(prev_layer.width):
            prev = prev_pix[x, y]
            curr = curr_pix[x, y]
            # Alpha difference is primary
            diff = abs(prev[3] - curr[3]) / 255.0
            diff_sum += diff
    
    total_pixels = prev_layer.width * prev_layer.height
    return 1.0 - (diff_sum / max(1.0, total_pixels))


def compute_animation_path_length(
    pose_offsets_sequence: list[dict[str, float]],
) -> float:
    """Function 89: Total distance traveled by all joints through animation."""
    if len(pose_offsets_sequence) < 2:
        return 0.0
    
    total = 0.0
    for prev_poses, curr_poses in zip(pose_offsets_sequence[:-1], pose_offsets_sequence[1:]):
        for key in prev_poses:
            if key in curr_poses:
                delta = curr_poses[key] - prev_poses.get(key, 0.0)
                total += abs(delta)
    
    return total


def adjust_layer_erosion_by_motion(
    layer_cfg: LayerConfig,
    motion_path_length: float,
) -> LayerConfig:
    """Function 90: Increase erosion on high-motion frames."""
    motion_factor = min(1.0, motion_path_length / 50.0)
    new_erosion = layer_cfg.pixel_erosion_rate + (motion_factor * 0.1)
    
    return LayerConfig(
        layer_index=layer_cfg.layer_index,
        depth_ratio=layer_cfg.depth_ratio,
        silhouette_reduction=layer_cfg.silhouette_reduction,
        opacity=layer_cfg.opacity,
        blur_amount=layer_cfg.blur_amount,
        pixel_erosion_rate=min(0.6, new_erosion),
        trail_offset_x=layer_cfg.trail_offset_x,
        trail_offset_y=layer_cfg.trail_offset_y,
        inverse_animation_strength=layer_cfg.inverse_animation_strength,
        ragdoll_influence=layer_cfg.ragdoll_influence,
    )


def compute_frame_time_delta(prev_time: float, curr_time: float) -> float:
    """Function 91: Time elapsed between frame timestamps."""
    return max(0.001, curr_time - prev_time)


def apply_temporal_smoothing(
    layer_cfg: LayerConfig,
    prev_cfg: LayerConfig | None,
    smoothing_factor: float = 0.3,
) -> LayerConfig:
    """Function 92: Smooth layer parameters across frames."""
    if prev_cfg is None:
        return layer_cfg
    
    blended_opacity = (layer_cfg.opacity * smoothing_factor) + (prev_cfg.opacity * (1.0 - smoothing_factor))
    blended_offset_y = (layer_cfg.trail_offset_y * smoothing_factor) + (prev_cfg.trail_offset_y * (1.0 - smoothing_factor))
    blended_erosion = (layer_cfg.pixel_erosion_rate * smoothing_factor) + (prev_cfg.pixel_erosion_rate * (1.0 - smoothing_factor))
    
    return LayerConfig(
        layer_index=layer_cfg.layer_index,
        depth_ratio=layer_cfg.depth_ratio,
        silhouette_reduction=layer_cfg.silhouette_reduction,
        opacity=blended_opacity,
        blur_amount=layer_cfg.blur_amount,
        pixel_erosion_rate=blended_erosion,
        trail_offset_x=layer_cfg.trail_offset_x,
        trail_offset_y=blended_offset_y,
        inverse_animation_strength=layer_cfg.inverse_animation_strength,
        ragdoll_influence=layer_cfg.ragdoll_influence,
    )


def estimate_render_performance(layers: list[LayerConfig]) -> dict:
    """Function 93: Estimate performance metrics for layer render."""
    total_cost = sum(compute_layer_render_cost(cfg) for cfg in layers)
    avg_blur = sum(cfg.blur_amount for cfg in layers) / max(1, len(layers))
    avg_erosion = sum(cfg.pixel_erosion_rate for cfg in layers) / max(1, len(layers))
    
    return {
        "total_cost": total_cost,
        "average_blur": avg_blur,
        "average_erosion": avg_erosion,
        "visible_layers": sum(1 for cfg in layers if compute_layer_visibility_mask(cfg.layer_index, len(layers))),
        "estimated_fps_impact": (total_cost / 100.0) * 30.0,  # Rough estimate
    }


def optimize_layer_stack_for_performance(
    layers: list[LayerConfig],
    target_cost: float = 50.0,
) -> list[LayerConfig]:
    """Function 94: Reduce layer quality to meet performance target."""
    current_cost = sum(compute_layer_render_cost(cfg) for cfg in layers)
    if current_cost <= target_cost:
        return layers
    
    scale_factor = target_cost / max(1.0, current_cost)
    
    optimized = []
    for cfg in layers:
        new_cfg = LayerConfig(
            layer_index=cfg.layer_index,
            depth_ratio=cfg.depth_ratio,
            silhouette_reduction=cfg.silhouette_reduction,
            opacity=cfg.opacity * scale_factor,
            blur_amount=max(0, int(cfg.blur_amount * scale_factor)),
            pixel_erosion_rate=cfg.pixel_erosion_rate * scale_factor,
            trail_offset_x=cfg.trail_offset_x,
            trail_offset_y=cfg.trail_offset_y,
            inverse_animation_strength=cfg.inverse_animation_strength,
            ragdoll_influence=cfg.ragdoll_influence,
        )
        optimized.append(new_cfg)
    
    return optimized


def serialize_layer_config_to_dict(cfg: LayerConfig) -> dict:
    """Function 95: Convert LayerConfig to JSON-serializable dict."""
    return {
        "layer_index": cfg.layer_index,
        "depth_ratio": float(cfg.depth_ratio),
        "silhouette_reduction": float(cfg.silhouette_reduction),
        "opacity": float(cfg.opacity),
        "blur_amount": int(cfg.blur_amount),
        "pixel_erosion_rate": float(cfg.pixel_erosion_rate),
        "trail_offset_x": float(cfg.trail_offset_x),
        "trail_offset_y": float(cfg.trail_offset_y),
        "inverse_animation_strength": float(cfg.inverse_animation_strength),
        "ragdoll_influence": float(cfg.ragdoll_influence),
    }


def deserialize_layer_config_from_dict(d: dict) -> LayerConfig:
    """Function 96: Reconstruct LayerConfig from dict."""
    return LayerConfig(
        layer_index=d.get("layer_index", 0),
        depth_ratio=float(d.get("depth_ratio", 0.0)),
        silhouette_reduction=float(d.get("silhouette_reduction", 0.0)),
        opacity=float(d.get("opacity", 1.0)),
        blur_amount=int(d.get("blur_amount", 0)),
        pixel_erosion_rate=float(d.get("pixel_erosion_rate", 0.0)),
        trail_offset_x=float(d.get("trail_offset_x", 0.0)),
        trail_offset_y=float(d.get("trail_offset_y", 2.0)),
        inverse_animation_strength=float(d.get("inverse_animation_strength", 0.0)),
        ragdoll_influence=float(d.get("ragdoll_influence", 0.0)),
    )


def validate_physics_parameters(physics_cfg: PhysicsConfig) -> bool:
    """Function 97: Check physics config is sensible."""
    if physics_cfg.gravity < 0.0 or physics_cfg.gravity > 1.0:
        return False
    if physics_cfg.damping < 0.8 or physics_cfg.damping > 1.0:
        return False
    if physics_cfg.joint_stiffness < 0.0 or physics_cfg.joint_stiffness > 1.0:
        return False
    if physics_cfg.max_iterations < 1 or physics_cfg.max_iterations > 10:
        return False
    return True


def sample_layer_stack_performance(
    layers: list[LayerConfig],
    iterations: int = 100,
) -> dict:
    """Function 98: Run benchmark samples to estimate performance."""
    total_cost = 0.0
    for _ in range(iterations):
        total_cost += sum(compute_layer_render_cost(cfg) for cfg in layers)
    
    avg_cost_per_frame = total_cost / iterations
    estimated_time_ms = avg_cost_per_frame * 0.5  # Rough estimate
    
    return {
        "iterations": iterations,
        "average_cost_per_frame": avg_cost_per_frame,
        "estimated_time_ms": estimated_time_ms,
        "estimated_fps": 1000.0 / max(1.0, estimated_time_ms),
    }


def generate_layer_animation_schedule(
    total_frames: int,
    total_layers: int = 100,
) -> list[dict]:
    """Function 99: Pre-compute layer configurations for all animation frames."""
    schedule = []
    for frame_idx in range(total_frames):
        phase = frame_idx / max(1, total_frames)
        pose_offsets = {
            "arm_a": math.sin(phase * math.tau) * 10.0,
            "arm_b": math.sin(phase * math.tau + math.pi) * 10.0,
            "leg_a": math.sin(phase * math.tau) * 8.0,
            "leg_b": math.sin(phase * math.tau + math.pi) * 8.0,
            "lift": abs(math.sin(phase * math.pi)) * 3.0,
        }
        
        configs = build_all_layer_configs(pose_offsets, total_layers)
        schedule.append({
            "frame": frame_idx,
            "phase": float(phase),
            "layers": [serialize_layer_config_to_dict(cfg) for cfg in configs],
        })
    
    return schedule


def compose_final_output_with_layers(
    base_image: Image.Image,
    layers: list[Image.Image],
    output_path: str,
    include_metadata: bool = True,
) -> bool:
    """Function 100: Final composition and export."""
    try:
        final = flatten_depth_stack_to_rgba(layers)
        final.save(output_path)
        
        if include_metadata:
            # Could save metadata JSON beside image
            pass
        
        return True
    except Exception:
        return False
