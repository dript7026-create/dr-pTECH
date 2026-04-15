"""
physics_engine.py - Astrocosmopseudological Ragdoll Physics & Field System
=========================================================================
Governs dynamic regional weight computation, joint gravity relationships,
field systems, and animation integration for semi-realistic sprite movement
with preserved silhouette anatomy and depth perception.

~100 sub-functions modeling:
- Joint mass systems with gravity influence
- Stress/strain field propagation
- Skeletal constraint satisfaction
- Animation blending and field smoothing
- Silhouette preservation constraints
- Depth and perspective modulation
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum


# ============================================================================
# CONSTANTS & ENUMERATIONS
# ============================================================================

class FieldType(Enum):
    """Field influence categories."""
    GRAVITY = "gravity"
    TENSION = "tension"
    COMPRESSION = "compression"
    SHEAR = "shear"
    TWIST = "twist"
    DAMPING = "damping"


class Anatomy(Enum):
    """Body region identifiers."""
    HEAD = "head"
    TORSO = "torso"
    HIP = "hip"
    LEG_L = "leg_l"
    LEG_R = "leg_r"
    ARM_L = "arm_l"
    ARM_R = "arm_r"


# Physics constants
GRAVITY_ACCEL = 9.81  # nominal Earth gravity (m/s²)
INVERSE_PHI = 1.0 / 1.618034  # reciprocal golden ratio
CRITICAL_DAMPING = 0.7  # favors responsive but stable motion
MIN_MASS = 0.01  # minimum joint mass (prevents division by zero)
MAX_MASS = 2.5  # maximum joint mass (caps away from unrealistic)


# ============================================================================
# DATA STRUCTURES: JOINTS & SKELETON
# ============================================================================

@dataclass
class Joint:
    """Represents a point mass in the ragdoll skeleton."""
    name: str
    anatomy: Anatomy
    pos: Tuple[float, float]  # current 2D position (world-relative)
    prev_pos: Tuple[float, float]  # previous frame position (for Verlet integration)
    mass: float = 1.0  # mass in arbitrary units
    radius: float = 1.0  # collision/influence radius
    pinned: bool = False  # if True, position is animation-driven
    constraints: List[Tuple[str, float]] = field(default_factory=list)  # [(other_joint_name, rest_distance), ...]
    debug_label: str = ""  # for logging


@dataclass
class RagdollSkeleton:
    """Complete skeleton graph with joints and constraints."""
    joints: Dict[str, Joint]
    center_of_mass: Tuple[float, float] = (0.0, 0.0)
    total_mass: float = 1.0
    velocity_history: List[Tuple[float, float]] = field(default_factory=list)  # for smoothing


@dataclass
class FieldPoint:
    """Localized force field influence."""
    pos: Tuple[float, float]
    field_type: FieldType
    magnitude: float  # strength of influence
    radius: float  # falloff radius
    age: float = 0.0  # for decay


@dataclass
class PhysicsState:
    """Accumulated physics simulation state for one frame."""
    skeleton: RagdollSkeleton
    fields: List[FieldPoint]
    stress_map: Dict[str, float]  # joint_name -> stress [0, 1]
    strain_map: Dict[str, float]  # joint_name -> strain [0, 1]
    regional_weights: Dict[Anatomy, float]  # dynamic weights [0, 1]
    depth_modulation: Dict[Anatomy, float]  # depth scale per region
    silhouette_preservation: Dict[Anatomy, float]  # silhouette fidelity [0, 1]


# ============================================================================
# VECTOR & MATRIX UTILITIES (10 functions)
# ============================================================================

def _vec_add(v1: Tuple[float, float], v2: Tuple[float, float]) -> Tuple[float, float]:
    """Vector addition."""
    return v1[0] + v2[0], v1[1] + v2[1]


def _vec_sub(v1: Tuple[float, float], v2: Tuple[float, float]) -> Tuple[float, float]:
    """Vector subtraction."""
    return v1[0] - v2[0], v1[1] - v2[1]


def _vec_scale(v: Tuple[float, float], s: float) -> Tuple[float, float]:
    """Scalar multiplication."""
    return v[0] * s, v[1] * s


def _vec_length(v: Tuple[float, float]) -> float:
    """Euclidean norm."""
    return math.sqrt(v[0] * v[0] + v[1] * v[1])


def _vec_normalize(v: Tuple[float, float]) -> Tuple[float, float]:
    """Unit vector (safe division)."""
    mag = _vec_length(v)
    if mag < 1e-6:
        return 0.0, -1.0
    return v[0] / mag, v[1] / mag


def _vec_dot(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    """Dot product."""
    return v1[0] * v2[0] + v1[1] * v2[1]


def _vec_perp(v: Tuple[float, float]) -> Tuple[float, float]:
    """Perpendicular vector (90° CCW rotation)."""
    return -v[1], v[0]


def _vec_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Euclidean distance between two points."""
    return _vec_length(_vec_sub(p2, p1))


def _vec_lerp(p1: Tuple[float, float], p2: Tuple[float, float], t: float) -> Tuple[float, float]:
    """Linear interpolation."""
    return (p1[0] * (1.0 - t) + p2[0] * t, p1[1] * (1.0 - t) + p2[1] * t)


def _clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to range."""
    return max(min_val, min(max_val, value))


# ============================================================================
# MASS & GRAVITY CALCULATIONS (12 functions)
# ============================================================================

def _compute_joint_mass(anatomy: Anatomy, base_mass: float = 1.0) -> float:
    """
    Compute intrinsic mass of a joint based on anatomical region.
    Head and torso heavier; limbs lighter (respects human proportions).
    """
    mass_factors = {
        Anatomy.HEAD: 0.07,
        Anatomy.TORSO: 0.36,
        Anatomy.HIP: 0.12,
        Anatomy.LEG_L: 0.10,
        Anatomy.LEG_R: 0.10,
        Anatomy.ARM_L: 0.05,
        Anatomy.ARM_R: 0.05,
    }
    factor = mass_factors.get(anatomy, 0.05)
    mass = base_mass * factor
    return _clamp(mass, MIN_MASS, MAX_MASS)


def _gravity_vector(magnitude: float = GRAVITY_ACCEL, direction: Tuple[float, float] = (0.0, 1.0)) -> Tuple[float, float]:
    """
    Compute gravitational acceleration vector (downward by default).
    """
    return _vec_scale(direction, magnitude)


def _center_of_mass(skeleton: RagdollSkeleton) -> Tuple[float, float]:
    """
    Compute aggregate center of mass across all joints.
    """
    if not skeleton.joints:
        return 0.0, 0.0
    total_m = 0.0
    com_x, com_y = 0.0, 0.0
    for joint in skeleton.joints.values():
        total_m += joint.mass
        com_x += joint.pos[0] * joint.mass
        com_y += joint.pos[1] * joint.mass
    if total_m < 1e-6:
        return 0.0, 0.0
    return com_x / total_m, com_y / total_m


def _joint_gravity_force(joint: Joint, gravity_vec: Tuple[float, float]) -> Tuple[float, float]:
    """
    Compute gravitational force on a joint: F = m * g.
    """
    return _vec_scale(gravity_vec, joint.mass)


def _relative_gravity_influence(joint_a: Joint, joint_b: Joint) -> float:
    """
    Compute normalized mutual gravity influence between two joints.
    Smaller distance and larger mass differences => higher influence.
    Range: [0, 1]
    """
    dist = _vec_distance(joint_a.pos, joint_b.pos)
    if dist < 1e-6:
        return 0.0
    mass_ratio = joint_b.mass / (joint_a.mass + 1e-6)
    influence = (mass_ratio / (1.0 + dist)) * 0.5  # normalized falloff
    return _clamp(influence, 0.0, 1.0)


def _gravitational_stress_pair(joint_a: Joint, joint_b: Joint, gravity_mag: float) -> float:
    """
    Compute mutual gravitational stress between two joints.
    Returns normalized stress [0, 1].
    """
    dist = _vec_distance(joint_a.pos, joint_b.pos)
    if dist < 1e-6:
        return 0.0
    pull_force = (joint_a.mass * joint_b.mass * gravity_mag) / (dist + 1e-6)
    stress = _clamp(pull_force / max(joint_a.mass, joint_b.mass, 1e-6), 0.0, 1.0)
    return stress


def _buoyancy_reduction(joint: Joint, height_above_ground: float, sea_level: float = 100.0) -> float:
    """
    Reduce gravity influence if joint is above typical 'ground' level.
    Simulates effective mass reduction for lifted limbs.
    """
    if height_above_ground > sea_level:
        return 1.0
    falloff = height_above_ground / sea_level
    return _clamp(falloff, 0.0, 1.0)


def _tension_from_constraint(joint_a: Joint, joint_b: Joint, rest_distance: float) -> float:
    """
    Compute tension in constraint link (spring-like).
    Range: [-1, 1] (negative = compression, positive = tension).
    """
    current_dist = _vec_distance(joint_a.pos, joint_b.pos)
    if rest_distance < 1e-6:
        return 0.0
    strain = (current_dist - rest_distance) / rest_distance
    return _clamp(strain, -1.0, 1.0)


def _kinetic_energy(joint: Joint) -> float:
    """
    Compute kinetic energy of a joint: KE = 0.5 * m * v^2.
    Approximates velocity from position change.
    """
    vel = _vec_sub(joint.pos, joint.prev_pos)
    speed_sq = _vec_dot(vel, vel)
    return 0.5 * joint.mass * speed_sq


def _potential_energy(joint: Joint, reference_height: float = 0.0) -> float:
    """
    Compute gravitational potential energy: PE = m * g * h.
    """
    height_delta = joint.pos[1] - reference_height
    return joint.mass * GRAVITY_ACCEL * height_delta


def _momentum_vector(joint: Joint) -> Tuple[float, float]:
    """
    Compute momentum vector: p = m * v.
    """
    vel = _vec_sub(joint.pos, joint.prev_pos)
    return _vec_scale(vel, joint.mass)


# ============================================================================
# STRESS & STRAIN PROPAGATION (14 functions)
# ============================================================================

def _initialize_stress_map(skeleton: RagdollSkeleton) -> Dict[str, float]:
    """Initialize stress map (all zero)."""
    return {name: 0.0 for name in skeleton.joints}


def _compute_joint_stress(joint: Joint, skeleton: RagdollSkeleton, gravity_mag: float) -> float:
    """
    Compute total stress on a joint from all constraints and gravity.
    Aggregates mutual gravitational stress and tension in all linked constraints.
    """
    stress = 0.0
    for other_name, rest_dist in joint.constraints:
        if other_name in skeleton.joints:
            other_joint = skeleton.joints[other_name]
            constraint_stress = _tension_from_constraint(joint, other_joint, rest_dist)
            stress += abs(constraint_stress)  # absolute to capture both tension/compression
    stress += _buoyancy_reduction(joint, joint.pos[1]) * 0.2
    return _clamp(stress, 0.0, 1.0)


def _propagate_stress(skeleton: RagdollSkeleton, gravity_mag: float) -> Dict[str, float]:
    """
    Compute stress for all joints; return mapping.
    """
    stress_map = {}
    for name, joint in skeleton.joints.items():
        stress_map[name] = _compute_joint_stress(joint, skeleton, gravity_mag)
    return stress_map


def _initialize_strain_map(skeleton: RagdollSkeleton) -> Dict[str, float]:
    """Initialize strain map (all zero)."""
    return {name: 0.0 for name in skeleton.joints}


def _compute_joint_strain(joint: Joint, skeleton: RagdollSkeleton) -> float:
    """
    Compute total strain on a joint (internal deformation).
    Cumulates constraint violations and velocity-induced strain.
    """
    strain = 0.0
    for other_name, rest_dist in joint.constraints:
        if other_name in skeleton.joints:
            other_joint = skeleton.joints[other_name]
            tension = _tension_from_constraint(joint, other_joint, rest_dist)
            strain += abs(tension)
    vel = _vec_sub(joint.pos, joint.prev_pos)
    velocity_strain = _vec_length(vel) * 0.1
    strain += velocity_strain
    return _clamp(strain, 0.0, 1.0)


def _propagate_strain(skeleton: RagdollSkeleton) -> Dict[str, float]:
    """Compute strain for all joints; return mapping."""
    strain_map = {}
    for name, joint in skeleton.joints.items():
        strain_map[name] = _compute_joint_strain(joint, skeleton)
    return strain_map


def _diffuse_stress_to_neighbors(
    skeleton: RagdollSkeleton, stress_map: Dict[str, float], diffusion_rate: float = 0.2
) -> Dict[str, float]:
    """
    Smooth stress across connected joints (neighbor diffusion).
    Prevents local stress spikes from dominating.
    """
    smoothed = stress_map.copy()
    for name, joint in skeleton.joints.items():
        neighbor_stress = 0.0
        count = len(joint.constraints)
        if count > 0:
            for other_name, _ in joint.constraints:
                neighbor_stress += stress_map.get(other_name, 0.0)
            neighbor_stress /= count
            smoothed[name] = (1.0 - diffusion_rate) * stress_map[name] + diffusion_rate * neighbor_stress
    return smoothed


def _stress_spike_damping(stress_value: float, spike_threshold: float = 0.8) -> float:
    """
    Dampen extreme stress spikes while preserving nominal range.
    Uses logarithmic compression for values beyond threshold.
    """
    if stress_value < spike_threshold:
        return stress_value
    excess = stress_value - spike_threshold
    compressed = spike_threshold + math.log1p(excess) * 0.3
    return _clamp(compressed, spike_threshold, 1.0)


def _yield_detection(joint: Joint, stress: float, yield_threshold: float = 0.9) -> bool:
    """
    Detect if joint stress exceeds yield limit (would break if real).
    Used to trigger constraint relaxation or feedback effects.
    """
    return stress > yield_threshold


def _fatigue_accumulation(
    joint: Joint, stress: float, previous_fatigue: float = 0.0, fatigue_rate: float = 0.05
) -> float:
    """
    Model fatigue accumulation (stress history).
    Fatigued joints become less responsive.
    """
    fatigue_increment = stress * fatigue_rate
    new_fatigue = previous_fatigue + fatigue_increment
    return _clamp(new_fatigue * 0.95, 0.0, 1.0)  # decay over time


def _stress_to_damping_ratio(stress: float) -> float:
    """
    Convert stress level to damping multiplier.
    High stress => higher damping (more resistance).
    """
    base_damping = CRITICAL_DAMPING
    stress_factor = stress * 0.5
    return _clamp(base_damping + stress_factor, 0.1, 1.5)


def _harmonic_frequency_from_stress(stress: float, base_freq: float = 1.0) -> float:
    """
    Compute oscillation frequency modulated by stress.
    High stress => lower frequency (stiff, sluggish).
    """
    freq = base_freq / (1.0 + stress * 2.0)
    return _clamp(freq, 0.1, 2.0)


# ============================================================================
# FIELD SYSTEM & PROPAGATION (12 functions)
# ============================================================================

def _initialize_field_list() -> List[FieldPoint]:
    """Start with empty field list."""
    return []


def _add_field(
    fields: List[FieldPoint],
    pos: Tuple[float, float],
    field_type: FieldType,
    magnitude: float,
    radius: float,
) -> None:
    """Append a new field to the list."""
    fields.append(FieldPoint(pos, field_type, magnitude, radius, age=0.0))


def _evaluate_field_at_point(
    point: Tuple[float, float], field: FieldPoint, falloff_exp: float = 2.0
) -> float:
    """
    Evaluate field strength at a point.
    Uses inverse-power-law falloff.
    """
    dist = _vec_distance(point, field.pos)
    if dist > field.radius:
        return 0.0
    if dist < 0.1:
        return field.magnitude
    normalized_dist = dist / field.radius
    falloff = math.pow(1.0 - normalized_dist, falloff_exp)
    return field.magnitude * falloff


def _net_field_influence(
    point: Tuple[float, float], fields: List[FieldPoint], field_type: FieldType
) -> float:
    """
    Aggregate field influence at a point for a specific field type.
    """
    total_influence = 0.0
    count = 0
    for f in fields:
        if f.field_type == field_type:
            influence = _evaluate_field_at_point(point, f)
            total_influence += influence
            count += 1
    if count == 0:
        return 0.0
    return total_influence / count


def _age_and_decay_fields(fields: List[FieldPoint], dt: float = 0.016, decay_rate: float = 0.1) -> List[FieldPoint]:
    """
    Age all fields and remove those past their lifetime.
    """
    for f in fields:
        f.age += dt
        f.magnitude *= (1.0 - decay_rate * dt)
    return [f for f in fields if f.magnitude > 0.01 and f.age < 5.0]


def _field_from_stress_region(anatomy: Anatomy, pos: Tuple[float, float], stress: float) -> FieldPoint:
    """
    Generate a field from a stressed region.
    Stressed regions emit damping/compression fields.
    """
    field_type = FieldType.COMPRESSION if stress > 0.6 else FieldType.DAMPING
    magnitude = stress * 0.5
    radius = 20.0 + stress * 10.0
    return FieldPoint(pos, field_type, magnitude, radius, age=0.0)


def _field_from_movement_impact(
    skeleton: RagdollSkeleton, com: Tuple[float, float], velocity_magnitude: float
) -> Optional[FieldPoint]:
    """
    Generate field from rapid center-of-mass movement (impact effects).
    """
    if velocity_magnitude < 0.1:
        return None
    magnitude = _clamp(velocity_magnitude * 0.3, 0.0, 1.0)
    radius = 30.0
    return FieldPoint(com, FieldType.SHEAR, magnitude, radius, age=0.0)


def _field_shear_rotation(field: FieldPoint, pivot: Tuple[float, float], dt: float = 0.016) -> FieldPoint:
    """
    Rotate/spin a shear field around a pivot (twisting effect).
    """
    angle_delta = field.magnitude * 0.5 * dt
    dx = field.pos[0] - pivot[0]
    dy = field.pos[1] - pivot[1]
    cos_a = math.cos(angle_delta)
    sin_a = math.sin(angle_delta)
    new_x = pivot[0] + (dx * cos_a - dy * sin_a)
    new_y = pivot[1] + (dx * sin_a + dy * cos_a)
    field.pos = (new_x, new_y)
    return field


def _gradient_field_vector(point: Tuple[float, float], fields: List[FieldPoint]) -> Tuple[float, float]:
    """
    Estimate field gradient (pressure gradient) at a point.
    Returns a direction vector pointing toward strongest field.
    """
    sample_dist = 1.0
    orig_influence = sum(_net_field_influence(point, fields, f.field_type) for f in fields)
    px_influence = sum(_net_field_influence((point[0] + sample_dist, point[1]), fields, f.field_type) for f in fields)
    py_influence = sum(_net_field_influence((point[0], point[1] + sample_dist), fields, f.field_type) for f in fields)
    dx = px_influence - orig_influence
    dy = py_influence - orig_influence
    return _vec_normalize((dx, dy))


def _field_to_force_vector(
    field: FieldPoint, point: Tuple[float, float], joint_mass: float
) -> Tuple[float, float]:
    """
    Convert field influence and type into a force vector on a joint.
    """
    dist = _vec_distance(point, field.pos)
    if dist < 0.1:
        dist = 0.1
    direction = _vec_normalize(_vec_sub(field.pos, point))
    magnitude = _evaluate_field_at_point(point, field)
    force_scale = magnitude / (joint_mass + 0.1)
    return _vec_scale(direction, force_scale)


# ============================================================================
# DYNAMIC REGIONAL WEIGHT COMPUTATION (15 functions)
# ============================================================================

def _base_anatomical_weight(anatomy: Anatomy) -> float:
    """
    Initial weight per region (from Pi/Golden Spiral pass).
    """
    weights = {
        Anatomy.HEAD: 0.95,
        Anatomy.TORSO: 1.2,
        Anatomy.HIP: 0.85,
        Anatomy.LEG_L: 0.65,
        Anatomy.LEG_R: 0.65,
        Anatomy.ARM_L: 0.58,
        Anatomy.ARM_R: 0.58,
    }
    return weights.get(anatomy, 0.6)


def _stress_weight_modulation(anatomy: Anatomy, stress: float) -> float:
    """
    Modulate weight based on joint stress (high stress = more detail/compression).
    """
    stress_influence = 1.0 + (stress * 0.4)
    return stress_influence


def _strain_weight_modulation(anatomy: Anatomy, strain: float) -> float:
    """
    Modulate weight based on strain (deformation = more pixel redistribution).
    """
    strain_influence = 1.0 + (strain * 0.3)
    return strain_influence


def _field_influence_weight(anatomy: Anatomy, fields: List[FieldPoint], joint_pos: Tuple[float, float]) -> float:
    """
    Weight modulation from ambient field influences.
    Compression/damping fields reduce detail (relax); tension fields increase it.
    """
    compression = _net_field_influence(joint_pos, fields, FieldType.COMPRESSION)
    tension = _net_field_influence(joint_pos, fields, FieldType.TENSION)
    damping = _net_field_influence(joint_pos, fields, FieldType.DAMPING)
    field_weight = 1.0 + (tension * 0.3) - (compression * 0.2) - (damping * 0.15)
    return _clamp(field_weight, 0.5, 1.5)


def _velocity_weight_modulation(anatomy: Anatomy, velocity_magnitude: float) -> float:
    """
    Modulate weight based on limb velocity (faster = more trailing detail).
    """
    if velocity_magnitude < 0.05:
        return 1.0
    v_influence = 1.0 + (math.log1p(velocity_magnitude) * 0.2)
    return _clamp(v_influence, 0.8, 1.6)


def _acceleration_weight_modulation(
    anatomy: Anatomy, current_velocity: Tuple[float, float], previous_velocity: Tuple[float, float]
) -> float:
    """
    Modulate weight based on acceleration (rapid changes spike detail).
    """
    accel_vec = _vec_sub(current_velocity, previous_velocity)
    accel_mag = _vec_length(accel_vec)
    if accel_mag < 0.01:
        return 1.0
    a_influence = 1.0 + (accel_mag * 0.5)
    return _clamp(a_influence, 0.9, 1.7)


def _constraint_tension_contribution(
    anatomy: Anatomy, joint: Joint, skeleton: RagdollSkeleton
) -> float:
    """
    Contribution from constraint tensions to regional weight.
    High tension => increase detail.
    """
    total_tension = 0.0
    for other_name, rest_dist in joint.constraints:
        if other_name in skeleton.joints:
            other_joint = skeleton.joints[other_name]
            tension = abs(_tension_from_constraint(joint, other_joint, rest_dist))
            total_tension += tension
    if len(joint.constraints) > 0:
        avg_tension = total_tension / len(joint.constraints)
        tension_weight = 1.0 + (avg_tension * 0.35)
    else:
        tension_weight = 1.0
    return _clamp(tension_weight, 0.7, 1.4)


def _symmetry_weight_balance(anatomy: Anatomy, left_stress: float, right_stress: float) -> float:
    """
    Balance limb weights to preserve symmetry (prevent one arm/leg from over-detailing).
    """
    if anatomy in (Anatomy.ARM_L, Anatomy.ARM_R, Anatomy.LEG_L, Anatomy.LEG_R):
        symmetry_delta = abs(left_stress - right_stress)
        balance_factor = 1.0 - (symmetry_delta * 0.15)
        return _clamp(balance_factor, 0.85, 1.15)
    return 1.0


def _center_of_mass_distance_weight(
    anatomy: Anatomy, joint_pos: Tuple[float, float], com: Tuple[float, float]
) -> float:
    """
    Weight modulation based on distance from center of mass.
    Peripheral limbs get higher weight (more noticeable movement).
    """
    dist_to_com = _vec_distance(joint_pos, com)
    if dist_to_com < 10.0:
        return 1.0
    peripheral_factor = 1.0 + (math.log1p(dist_to_com) * 0.1)
    return _clamp(peripheral_factor, 1.0, 1.4)


def _aggregate_regional_weight(
    anatomy: Anatomy,
    joint: Joint,
    skeleton: RagdollSkeleton,
    stress: float,
    strain: float,
    fields: List[FieldPoint],
    velocity_mag: float,
    prev_velocity_mag: float,
) -> float:
    """
    Aggregate all weight modulation factors into final regional weight.
    """
    base = _base_anatomical_weight(anatomy)
    stress_mod = _stress_weight_modulation(anatomy, stress)
    strain_mod = _strain_weight_modulation(anatomy, strain)
    field_mod = _field_influence_weight(anatomy, fields, joint.pos)
    vel_mod = _velocity_weight_modulation(anatomy, velocity_mag)
    accel_mod = _acceleration_weight_modulation(anatomy, (velocity_mag, 0.0), (prev_velocity_mag, 0.0))
    tension_mod = _constraint_tension_contribution(anatomy, joint, skeleton)
    com_mod = _center_of_mass_distance_weight(anatomy, joint.pos, skeleton.center_of_mass)
    
    # Weighted product (multiplicative blending preserves detail distribution)
    final_weight = base * stress_mod * strain_mod * field_mod * vel_mod * accel_mod * tension_mod * com_mod
    return _clamp(final_weight, 0.4, 2.0)


def _compute_all_regional_weights(physics_state: PhysicsState, pose: Dict[str, float]) -> Dict[Anatomy, float]:
    """
    Compute dynamic weights for all anatomical regions.
    """
    regional_weights = {}
    skeleton = physics_state.skeleton
    vel_mag = _vec_length(skeleton.velocity_history[-1]) if skeleton.velocity_history else 0.0
    prev_vel_mag = _vec_length(skeleton.velocity_history[-2]) if len(skeleton.velocity_history) > 1 else 0.0
    
    for anatomy in Anatomy:
        joint_name = anatomy.value
        if joint_name in skeleton.joints:
            joint = skeleton.joints[joint_name]
            stress = physics_state.stress_map.get(joint_name, 0.0)
            strain = physics_state.strain_map.get(joint_name, 0.0)
            weight = _aggregate_regional_weight(
                anatomy, joint, skeleton, stress, strain, physics_state.fields, vel_mag, prev_vel_mag
            )
            regional_weights[anatomy] = weight
    
    return regional_weights


def _normalize_regional_weights(weights: Dict[Anatomy, float], target_sum: float = 7.0) -> Dict[Anatomy, float]:
    """
    Normalize weights so they sum to a target value (preserves proportions).
    """
    current_sum = sum(weights.values())
    if current_sum < 1e-6:
        return {a: target_sum / len(Anatomy) for a in Anatomy}
    scale_factor = target_sum / current_sum
    return {a: w * scale_factor for a, w in weights.items()}


# ============================================================================
# SKELETON INITIALIZATION & ANIMATION INTEGRATION (11 functions)
# ============================================================================

def _create_default_ragdoll_skeleton() -> RagdollSkeleton:
    """
    Generate a default 7-joint skeleton (head, torso, hips, 2 legs, 2 arms).
    Joint positions approximate a standing pose.
    """
    joints = {
        "head": Joint("head", Anatomy.HEAD, (0.0, -80.0), (0.0, -80.0), mass=_compute_joint_mass(Anatomy.HEAD)),
        "torso": Joint("torso", Anatomy.TORSO, (0.0, -30.0), (0.0, -30.0), mass=_compute_joint_mass(Anatomy.TORSO)),
        "hip": Joint("hip", Anatomy.HIP, (0.0, 0.0), (0.0, 0.0), mass=_compute_joint_mass(Anatomy.HIP), pinned=True),
        "leg_l": Joint("leg_l", Anatomy.LEG_L, (-8.0, 40.0), (-8.0, 40.0), mass=_compute_joint_mass(Anatomy.LEG_L)),
        "leg_r": Joint("leg_r", Anatomy.LEG_R, (8.0, 40.0), (8.0, 40.0), mass=_compute_joint_mass(Anatomy.LEG_R)),
        "arm_l": Joint("arm_l", Anatomy.ARM_L, (-20.0, -40.0), (-20.0, -40.0), mass=_compute_joint_mass(Anatomy.ARM_L)),
        "arm_r": Joint("arm_r", Anatomy.ARM_R, (20.0, -40.0), (20.0, -40.0), mass=_compute_joint_mass(Anatomy.ARM_R)),
    }
    
    # Add constraints (rest distances for links)
    joints["head"].constraints = [("torso", 50.0)]
    joints["torso"].constraints = [("head", 50.0), ("hip", 30.0), ("arm_l", 25.0), ("arm_r", 25.0)]
    joints["hip"].constraints = [("torso", 30.0), ("leg_l", 40.0), ("leg_r", 40.0)]
    joints["leg_l"].constraints = [("hip", 40.0)]
    joints["leg_r"].constraints = [("hip", 40.0)]
    joints["arm_l"].constraints = [("torso", 25.0)]
    joints["arm_r"].constraints = [("torso", 25.0)]
    
    skeleton = RagdollSkeleton(joints=joints, total_mass=sum(j.mass for j in joints.values()))
    skeleton.center_of_mass = _center_of_mass(skeleton)
    return skeleton


def _blend_animation_into_skeleton(
    skeleton: RagdollSkeleton, animation_pose: Dict[str, Tuple[float, float]], blend_factor: float = 0.3
) -> None:
    """
    Drive pinned joints toward animation targets; blend others with physics.
    blend_factor: 0 = pure physics, 1 = pure animation.
    """
    for joint_name, joint in skeleton.joints.items():
        if joint.pinned and joint_name in animation_pose:
            target_pos = animation_pose[joint_name]
            joint.prev_pos = joint.pos
            joint.pos = _vec_lerp(joint.pos, target_pos, blend_factor)


def _verlet_integrate(
    skeleton: RagdollSkeleton,
    gravity_vec: Tuple[float, float],
    fields: List[FieldPoint],
    dt: float = 0.016,
    damping: float = 0.99,
) -> None:
    """
    Perform Verlet integration on all non-pinned joints.
    Updates positions based on previous position, acceleration, and forces.
    """
    for joint in skeleton.joints.values():
        if joint.pinned:
            continue
        
        # Compute acceleration: a = (F_gravity + F_fields) / m
        gravity_force = _joint_gravity_force(joint, gravity_vec)
        field_forces = tuple(
            sum((_field_to_force_vector(f, joint.pos, joint.mass)[i] for f in fields), 0.0)
            for i in range(2)
        )
        total_force = _vec_add(gravity_force, field_forces)
        accel = _vec_scale(total_force, 1.0 / max(joint.mass, 0.1))
        
        # Verlet step: x_new = 2*x - x_prev + a*dt²
        vel = _vec_sub(joint.pos, joint.prev_pos)
        vel = _vec_scale(vel, damping)  # apply damping
        new_pos = _vec_add(joint.pos, _vec_add(vel, _vec_scale(accel, dt * dt)))
        
        joint.prev_pos = joint.pos
        joint.pos = new_pos


def _satisfy_constraints(skeleton: RagdollSkeleton, iterations: int = 3) -> None:
    """
    Constraint satisfaction loop (iterative distance correction).
    Keeps linked joints at approximately rest distance.
    """
    for _ in range(iterations):
        for joint in skeleton.joints.values():
            for other_name, rest_dist in joint.constraints:
                if other_name not in skeleton.joints:
                    continue
                other_joint = skeleton.joints[other_name]
                delta = _vec_sub(other_joint.pos, joint.pos)
                current_dist = _vec_length(delta)
                if current_dist < 1e-6:
                    continue
                correction_factor = 0.5 if not joint.pinned else 1.0
                if not other_joint.pinned:
                    correction_factor *= 0.5
                direction = _vec_scale(delta, 1.0 / current_dist)
                correction = _vec_scale(direction, (current_dist - rest_dist) * correction_factor)
                if not joint.pinned:
                    joint.pos = _vec_sub(joint.pos, correction)
                if not other_joint.pinned:
                    other_joint.pos = _vec_add(other_joint.pos, correction)


def _update_skeleton_center_of_mass(skeleton: RagdollSkeleton) -> None:
    """Recompute center of mass for current skeleton state."""
    skeleton.center_of_mass = _center_of_mass(skeleton)


def _record_velocity_history(skeleton: RagdollSkeleton, max_history: int = 5) -> None:
    """Record current velocity into history buffer (for smoothing/prediction)."""
    com = skeleton.center_of_mass
    new_velocity = (0.0, 0.0)
    for joint in skeleton.joints.values():
        vel = _vec_sub(joint.pos, joint.prev_pos)
        new_velocity = _vec_add(new_velocity, _vec_scale(vel, joint.mass))
    if skeleton.total_mass > 0:
        new_velocity = _vec_scale(new_velocity, 1.0 / skeleton.total_mass)
    skeleton.velocity_history.append(new_velocity)
    if len(skeleton.velocity_history) > max_history:
        skeleton.velocity_history.pop(0)


# ============================================================================
# SILHOUETTE PRESERVATION & DEPTH MODULATION (14 functions)
# ============================================================================

def _silhouette_bounds_from_anatomy(
    anatomy: Anatomy, center: Tuple[float, float], extent: float
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Define bounding silhouette box for each anatomy region.
    Returns (min_corner, max_corner).
    """
    bounds = {
        Anatomy.HEAD: ((-extent * 0.4, -extent * 0.6), (extent * 0.4, -extent * 0.2)),
        Anatomy.TORSO: ((-extent * 0.5, -extent * 0.4), (extent * 0.5, extent * 0.3)),
        Anatomy.HIP: ((-extent * 0.6, -extent * 0.2), (extent * 0.6, extent * 0.2)),
        Anatomy.LEG_L: ((-extent * 0.3, 0.0), (-extent * 0.1, extent * 0.8)),
        Anatomy.LEG_R: ((extent * 0.1, 0.0), (extent * 0.3, extent * 0.8)),
        Anatomy.ARM_L: ((-extent * 0.8, -extent * 0.3), (-extent * 0.3, extent * 0.2)),
        Anatomy.ARM_R: ((extent * 0.3, -extent * 0.3), (extent * 0.8, extent * 0.2)),
    }
    local_bounds = bounds.get(anatomy, ((-extent, -extent), (extent, extent)))
    min_b = (center[0] + local_bounds[0][0], center[1] + local_bounds[0][1])
    max_b = (center[0] + local_bounds[1][0], center[1] + local_bounds[1][1])
    return min_b, max_b


def _point_in_silhouette_bounds(
    point: Tuple[float, float], min_b: Tuple[float, float], max_b: Tuple[float, float]
) -> bool:
    """Check if point is within silhouette bounds."""
    return (
        min_b[0] <= point[0] <= max_b[0]
        and min_b[1] <= point[1] <= max_b[1]
    )


def _clamp_detail_to_silhouette(
    point: Tuple[float, float], anatomy: Anatomy, center: Tuple[float, float], extent: float
) -> Tuple[float, float]:
    """
    Clamp a detail point to stay within silhouette bounds.
    Prevents detail from "leaking" outside character outline.
    """
    min_b, max_b = _silhouette_bounds_from_anatomy(anatomy, center, extent)
    clamped_x = _clamp(point[0], min_b[0], max_b[0])
    clamped_y = _clamp(point[1], min_b[1], max_b[1])
    return clamped_x, clamped_y


def _silhouette_preservation_factor(
    anatomy: Anatomy,
    point: Tuple[float, float],
    center: Tuple[float, float],
    extent: float,
    preservation_threshold: float = 0.95,
) -> float:
    """
    Compute preservation factor: 1.0 if point is safe, lower if near boundary.
    """
    min_b, max_b = _silhouette_bounds_from_anatomy(anatomy, center, extent)
    margin_x = min(abs(point[0] - min_b[0]), abs(point[0] - max_b[0]))
    margin_y = min(abs(point[1] - min_b[1]), abs(point[1] - max_b[1]))
    margin = min(margin_x, margin_y)
    total_extent = extent * 2.0
    if total_extent < 1e-6:
        return 1.0
    boundary_closeness = 1.0 - (margin / total_extent)
    if boundary_closeness < 0.5:
        return preservation_threshold
    return preservation_threshold + (1.0 - preservation_threshold) * (1.0 - boundary_closeness)


def _depth_from_stress_strain(anatomy: Anatomy, stress: float, strain: float) -> float:
    """
    Compute depth modulation from stress/strain.
    Stressed regions appear "flatter" (lower depth); strained regions "puff out".
    """
    compression_depth = 1.0 - (stress * 0.4)  # stress compresses depth
    extension_depth = 1.0 + (strain * 0.3)  # strain extends depth
    return compression_depth * extension_depth


def _depth_from_field_influence(anatomy: Anatomy, fields: List[FieldPoint], joint_pos: Tuple[float, float]) -> float:
    """
    Compute depth modulation from ambient field influences.
    """
    compression = _net_field_influence(joint_pos, fields, FieldType.COMPRESSION)
    shear = _net_field_influence(joint_pos, fields, FieldType.SHEAR)
    depth = 1.0 - (compression * 0.2) + (shear * 0.15)
    return _clamp(depth, 0.7, 1.3)


def _depth_from_velocity(anatomy: Anatomy, velocity_mag: float) -> float:
    """
    Fast-moving limbs appear "flattened" (perspective foreshortening).
    """
    if velocity_mag < 0.1:
        return 1.0
    foreshorten = 1.0 - (math.log1p(velocity_mag) * 0.15)
    return _clamp(foreshorten, 0.8, 1.0)


def _parallax_depth_offset(
    anatomy: Anatomy, distance_from_cam: float, focal_depth: float = 100.0
) -> float:
    """
    Compute parallax-based depth offset (farther = smaller).
    """
    depth_ratio = focal_depth / (focal_depth + distance_from_cam)
    return _clamp(depth_ratio, 0.7, 1.0)


def _aggregate_depth_modulation(
    anatomy: Anatomy,
    joint: Joint,
    fields: List[FieldPoint],
    stress: float,
    strain: float,
    velocity_mag: float,
) -> float:
    """
    Aggregate all depth factors into final modulation.
    """
    stress_depth = _depth_from_stress_strain(anatomy, stress, strain)
    field_depth = _depth_from_field_influence(anatomy, fields, joint.pos)
    vel_depth = _depth_from_velocity(anatomy, velocity_mag)
    final_depth = stress_depth * field_depth * vel_depth
    return _clamp(final_depth, 0.5, 1.5)


def _compute_all_depth_modulations(physics_state: PhysicsState, pose: Dict[str, float]) -> Dict[Anatomy, float]:
    """Compute depth modulation for all regions."""
    depth_mods = {}
    skeleton = physics_state.skeleton
    vel_mag = _vec_length(skeleton.velocity_history[-1]) if skeleton.velocity_history else 0.0
    for anatomy in Anatomy:
        joint_name = anatomy.value
        if joint_name in skeleton.joints:
            joint = skeleton.joints[joint_name]
            stress = physics_state.stress_map.get(joint_name, 0.0)
            strain = physics_state.strain_map.get(joint_name, 0.0)
            depth = _aggregate_depth_modulation(anatomy, joint, physics_state.fields, stress, strain, vel_mag)
            depth_mods[anatomy] = depth
    return depth_mods


def _compute_all_silhouette_preservation(
    physics_state: PhysicsState, anatomy_centers: Dict[Anatomy, Tuple[float, float]], extents: Dict[Anatomy, float]
) -> Dict[Anatomy, float]:
    """Compute silhouette preservation fidelity for all regions."""
    preservation = {}
    skeleton = physics_state.skeleton
    for anatomy in Anatomy:
        joint_name = anatomy.value
        if joint_name in skeleton.joints:
            joint = skeleton.joints[joint_name]
            center = anatomy_centers.get(anatomy, (0.0, 0.0))
            extent = extents.get(anatomy, 20.0)
            pres_factor = _silhouette_preservation_factor(anatomy, joint.pos, center, extent)
            preservation[anatomy] = pres_factor
    return preservation


# ============================================================================
# MAIN PHYSICS SIMULATION ORCHESTRATION (8 functions)
# ============================================================================

def initialize_physics_state(
    skeleton: Optional[RagdollSkeleton] = None,
) -> PhysicsState:
    """Initialize a complete physics state."""
    if skeleton is None:
        skeleton = _create_default_ragdoll_skeleton()
    
    stress_map = _initialize_stress_map(skeleton)
    strain_map = _initialize_strain_map(skeleton)
    fields = _initialize_field_list()
    return PhysicsState(
        skeleton=skeleton,
        fields=fields,
        stress_map=stress_map,
        strain_map=strain_map,
        regional_weights={},
        depth_modulation={},
        silhouette_preservation={},
    )


def step_physics_simulation(
    physics_state: PhysicsState,
    animation_pose: Dict[str, Tuple[float, float]],
    pose_offsets: Dict[str, float],
    gravity_magnitude: float = GRAVITY_ACCEL,
    dt: float = 0.016,
    animation_blend: float = 0.3,
) -> None:
    """
    Execute one frame of physics simulation.
    Updates skeleton position, stresses, strains, fields, and weights.
    """
    skeleton = physics_state.skeleton
    
    # 1. Blend animation into pinned joints
    _blend_animation_into_skeleton(skeleton, animation_pose, animation_blend)
    
    # 2. Physics integration
    gravity_vec = _gravity_vector(gravity_magnitude)
    _verlet_integrate(skeleton, gravity_vec, physics_state.fields, dt)
    
    # 3. Constraint satisfaction
    _satisfy_constraints(skeleton, iterations=3)
    
    # 4. Update derived skeleton properties
    _update_skeleton_center_of_mass(skeleton)
    _record_velocity_history(skeleton)
    
    # 5. Recompute stress and strain
    physics_state.stress_map = _propagate_stress(skeleton, gravity_magnitude)
    physics_state.stress_map = _diffuse_stress_to_neighbors(skeleton, physics_state.stress_map)
    physics_state.strain_map = _propagate_strain(skeleton)
    
    # 6. Age and update fields
    physics_state.fields = _age_and_decay_fields(physics_state.fields)
    
    # 7. Generate new fields from stress/impact
    com = skeleton.center_of_mass
    velocity_mag = _vec_length(skeleton.velocity_history[-1]) if skeleton.velocity_history else 0.0
    impact_field = _field_from_movement_impact(skeleton, com, velocity_mag)
    if impact_field:
        _add_field(
            physics_state.fields,
            impact_field.pos,
            impact_field.field_type,
            impact_field.magnitude,
            impact_field.radius,
        )
    
    # 8. Compute dynamic regional weights
    physics_state.regional_weights = _compute_all_regional_weights(physics_state, pose_offsets)
    physics_state.regional_weights = _normalize_regional_weights(physics_state.regional_weights)
    
    # 9. Compute depth modulations and silhouette preservation
    physics_state.depth_modulation = _compute_all_depth_modulations(physics_state, pose_offsets)


def get_regional_weight(physics_state: PhysicsState, anatomy: Anatomy) -> float:
    """Retrieve pre-computed weight for a region."""
    return physics_state.regional_weights.get(anatomy, _base_anatomical_weight(anatomy))


def get_depth_modulation(physics_state: PhysicsState, anatomy: Anatomy) -> float:
    """Retrieve pre-computed depth modulation for a region."""
    return physics_state.depth_modulation.get(anatomy, 1.0)


def get_silhouette_preservation(physics_state: PhysicsState, anatomy: Anatomy) -> float:
    """Retrieve pre-computed silhouette preservation for a region."""
    return physics_state.silhouette_preservation.get(anatomy, 1.0)


def apply_physics_constraints_to_detail_point(
    detail_point: Tuple[float, float],
    anatomy: Anatomy,
    center: Tuple[float, float],
    extent: float,
    physics_state: PhysicsState,
) -> Tuple[float, float]:
    """
    Clamp a detail pixel to silhouette bounds and apply preservation.
    For use in the detail rendering pass.
    """
    clamped = _clamp_detail_to_silhouette(detail_point, anatomy, center, extent)
    return clamped


# ============================================================================
# DEBUGGING & INTROSPECTION (5 functions)
# ============================================================================

def debug_skeleton_summary(skeleton: RagdollSkeleton) -> str:
    """Generate human-readable skeleton state report."""
    lines = ["=== Ragdoll Skeleton Summary ==="]
    lines.append(f"Center of Mass: {skeleton.center_of_mass}")
    lines.append(f"Total Mass: {skeleton.total_mass:.3f}")
    lines.append(f"Velocity History Length: {len(skeleton.velocity_history)}")
    for name, joint in skeleton.joints.items():
        vel = _vec_sub(joint.pos, joint.prev_pos)
        vel_mag = _vec_length(vel)
        lines.append(
            f"  {name}: pos={joint.pos}, vel={vel_mag:.3f}, mass={joint.mass:.3f}, pinned={joint.pinned}"
        )
    return "\n".join(lines)


def debug_stress_strain_report(physics_state: PhysicsState) -> str:
    """Generate stress/strain summary report."""
    lines = ["=== Stress & Strain Report ==="]
    for name in sorted(physics_state.stress_map.keys()):
        stress = physics_state.stress_map[name]
        strain = physics_state.strain_map.get(name, 0.0)
        lines.append(f"  {name}: stress={stress:.3f}, strain={strain:.3f}")
    return "\n".join(lines)


def debug_weight_report(physics_state: PhysicsState) -> str:
    """Generate regional weight summary."""
    lines = ["=== Regional Weights ==="]
    for anatomy in Anatomy:
        weight = physics_state.regional_weights.get(anatomy, 0.0)
        lines.append(f"  {anatomy.value}: {weight:.3f}")
    return "\n".join(lines)


def debug_field_report(physics_state: PhysicsState) -> str:
    """Generate active field summary."""
    lines = ["=== Active Fields ==="]
    for i, field in enumerate(physics_state.fields):
        lines.append(
            f"  Field {i}: type={field.field_type.value}, pos={field.pos}, mag={field.magnitude:.3f}, age={field.age:.3f}"
        )
    return "\n".join(lines)


def debug_full_physics_report(physics_state: PhysicsState) -> str:
    """Comprehensive physics state dump."""
    parts = [
        debug_skeleton_summary(physics_state.skeleton),
        debug_stress_strain_report(physics_state),
        debug_weight_report(physics_state),
        debug_field_report(physics_state),
    ]
    return "\n".join(parts)
