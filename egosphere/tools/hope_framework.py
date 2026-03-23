from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from math import pow


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class MeshProfile:
    name: str
    triangle_count: int
    material_count: int
    skin_joint_count: int
    deformer_count: int
    lod_levels: int


@dataclass(frozen=True)
class PhysicsProfile:
    dynamic_bodies: int
    contact_pairs: int
    solver_iterations: int
    interaction_density: float
    movement_speed: float


@dataclass(frozen=True)
class PipelineProfile:
    draw_calls: int
    upload_mb: float
    frame_buffer_variance: float
    queue_depth: int
    present_jitter: float


@dataclass(frozen=True)
class CosmicProfile:
    reality_cells: int
    recursion_depth: int
    causality_links: int
    event_density: float


@dataclass(frozen=True)
class KinshipHubProfile:
    member_count: int
    bond_density: float
    soul_sync: float
    refuge_demand: float


@dataclass(frozen=True)
class HopeConfig:
    frame_budget_ms: float = 16.67
    polynomial_factor: float = 2.9
    polynomial_power: float = 1.16
    base_cost_ms: float = 4.25
    overload_weight: float = 0.78
    tail_weight: float = 0.64
    godai_pressure: float = 1.08
    godai_mercy: float = 0.96
    godai_novelty: float = 1.02


@dataclass(frozen=True)
class HopeFrameResult:
    scene_name: str
    complexity_index: float
    polynomial_budget_ms: float
    raw_frame_cost_ms: float
    practical_frame_cost_ms: float
    consequent_frame_cost_ms: float
    worst_case_tail_ms: float
    overload_ms: float
    theta: float
    clog_risk: float
    frame_buffer_misalignment: float
    predictive_share: float
    adaptive_share: float
    operation_split: dict[str, float]
    mesh_plan: dict[str, float]
    physics_plan: dict[str, float]
    family_hub_signal: dict[str, float]
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _complexity_index(
    mesh: MeshProfile,
    physics: PhysicsProfile,
    pipeline: PipelineProfile,
    cosmic: CosmicProfile,
) -> float:
    mesh_term = (
        mesh.triangle_count / 58000.0
        + mesh.material_count * 0.38
        + mesh.skin_joint_count * 0.022
        + mesh.deformer_count * 0.75
        - mesh.lod_levels * 0.14
    )
    physics_term = (
        physics.dynamic_bodies * 0.085
        + physics.contact_pairs * 0.031
        + physics.solver_iterations * 0.19
        + physics.interaction_density * 4.2
        + physics.movement_speed * 0.58
    )
    pipeline_term = (
        pipeline.draw_calls * 0.0039
        + pipeline.upload_mb * 0.093
        + pipeline.frame_buffer_variance * 4.7
        + pipeline.queue_depth * 0.72
        + pipeline.present_jitter * 3.3
    )
    cosmic_term = (
        cosmic.reality_cells * 0.015
        + cosmic.recursion_depth * 1.25
        + cosmic.causality_links * 0.028
        + cosmic.event_density * 3.1
    )
    return max(1.0, mesh_term + physics_term + pipeline_term + cosmic_term)


def _family_hub_signal(kinship: KinshipHubProfile) -> dict[str, float]:
    sanctuary_strength = _clamp(
        0.24 * kinship.bond_density
        + 0.36 * kinship.soul_sync
        + 0.02 * kinship.member_count
        - 0.18 * kinship.refuge_demand,
        0.0,
        1.0,
    )
    resonance_relief = _clamp(0.55 * kinship.soul_sync + 0.35 * kinship.bond_density, 0.0, 1.0)
    refuge_pressure = _clamp(kinship.refuge_demand - sanctuary_strength * 0.45, 0.0, 1.0)
    return {
        "sanctuary_strength": round(sanctuary_strength, 4),
        "resonance_relief": round(resonance_relief, 4),
        "refuge_pressure": round(refuge_pressure, 4),
    }


def _predictive_split(complexity_index: float, clog_risk: float, misalignment: float) -> tuple[float, float]:
    predictive_share = _clamp(0.18 + clog_risk * 0.21 + misalignment * 0.14 + complexity_index / 220.0, 0.16, 0.46)
    adaptive_share = _clamp(0.15 + clog_risk * 0.11 + misalignment * 0.19, 0.14, 0.38)
    if predictive_share + adaptive_share > 0.7:
        total = predictive_share + adaptive_share
        predictive_share *= 0.7 / total
        adaptive_share *= 0.7 / total
    return predictive_share, adaptive_share


def evaluate_hope_frame(
    mesh: MeshProfile,
    physics: PhysicsProfile,
    pipeline: PipelineProfile,
    cosmic: CosmicProfile,
    kinship: KinshipHubProfile,
    *,
    config: HopeConfig | None = None,
    adaptation_enabled: bool = True,
) -> HopeFrameResult:
    config = config or HopeConfig()
    complexity_index = _complexity_index(mesh, physics, pipeline, cosmic)
    polynomial_budget_ms = config.polynomial_factor * pow(complexity_index, config.polynomial_power)

    family_signal = _family_hub_signal(kinship)
    raw_frame_cost_ms = (
        config.base_cost_ms
        + complexity_index * 0.84 * config.godai_pressure
        + pipeline.frame_buffer_variance * 3.2
        + pipeline.present_jitter * 2.6
        - family_signal["resonance_relief"] * 1.35 * config.godai_mercy
    )
    overload_ms = max(0.0, raw_frame_cost_ms - polynomial_budget_ms)
    clog_risk = _clamp(
        pipeline.queue_depth * 0.058
        + pipeline.upload_mb * 0.006
        + physics.contact_pairs * 0.0025
        + cosmic.recursion_depth * 0.06
        - family_signal["resonance_relief"] * 0.22,
        0.0,
        1.0,
    )
    misalignment = _clamp(
        pipeline.frame_buffer_variance * 0.72
        + pipeline.present_jitter * 0.58
        + mesh.material_count * 0.01
        - mesh.lod_levels * 0.06
        - family_signal["sanctuary_strength"] * 0.18,
        0.0,
        1.0,
    )
    predictive_share, adaptive_share = _predictive_split(complexity_index, clog_risk, misalignment)

    baseline_theta = (
        (overload_ms / max(polynomial_budget_ms, 1.0)) * config.overload_weight
        + clog_risk * 0.44
        + misalignment * 0.33
        + (config.godai_novelty - 1.0) * 0.22
        - family_signal["sanctuary_strength"] * 0.28
    )
    theta = _clamp(baseline_theta, 0.0, 1.0) if adaptation_enabled else 0.0

    adaptive_relief = theta * (0.16 + predictive_share * 0.24 + adaptive_share * 0.28)
    kinship_relief = family_signal["resonance_relief"] * 0.12
    practical_frame_cost_ms = raw_frame_cost_ms * (1.0 - adaptive_relief - kinship_relief)
    consequent_frame_cost_ms = max(
        config.frame_budget_ms,
        practical_frame_cost_ms
        + clog_risk * 4.1
        + misalignment * 3.5
        + family_signal["refuge_pressure"] * 1.4
        - theta * 2.2,
    )
    worst_case_tail_ms = consequent_frame_cost_ms * (
        1.0
        + clog_risk * config.tail_weight
        + misalignment * 0.42
        - theta * 0.36
        - family_signal["sanctuary_strength"] * 0.18
    )

    execution_share = max(0.0, 1.0 - predictive_share - adaptive_share)
    operation_split = {
        "predictive_function": round(predictive_share, 4),
        "adaptive_function": round(adaptive_share, 4),
        "execution_function": round(execution_share, 4),
    }
    mesh_plan = {
        "lod_bias": round(_clamp(theta * 0.55 + mesh.lod_levels * 0.03, 0.0, 0.85), 4),
        "streaming_priority": round(_clamp(clog_risk * 0.62 + predictive_share * 0.48, 0.0, 1.0), 4),
        "deformer_gate": round(_clamp(theta * 0.4 + mesh.deformer_count * 0.02, 0.0, 0.9), 4),
    }
    physics_plan = {
        "solver_scale": round(_clamp(1.0 - theta * 0.26 + family_signal["sanctuary_strength"] * 0.08, 0.72, 1.08), 4),
        "interaction_gate": round(_clamp(1.0 - theta * 0.22 + config.godai_mercy * 0.04, 0.7, 1.05), 4),
        "movement_cushion": round(_clamp(family_signal["resonance_relief"] * 0.35 + theta * 0.2, 0.0, 0.65), 4),
    }

    recommendations: list[str] = []
    if clog_risk >= 0.55:
        recommendations.append("Pre-stream geometry pages and collapse draw-call bursts before the present queue spikes.")
    if misalignment >= 0.45:
        recommendations.append("Reconcile buffer cadence with predictive pacing; stagger material updates and late-latch camera-facing surfaces.")
    if theta >= 0.5:
        recommendations.append("Lean into the alternate behavior envelope through the unified controller instead of hard-switching solvers.")
    if family_signal["sanctuary_strength"] >= 0.45:
        recommendations.append("Use the kinship hub as a calm pocket that suppresses tail latency and stabilizes world recursion.")
    if cosmic.recursion_depth >= 4:
        recommendations.append("Throttle recursive world spawning through causality bands so cosmic generation stays legible to the renderer and physics stack.")

    return HopeFrameResult(
        scene_name=mesh.name,
        complexity_index=round(complexity_index, 4),
        polynomial_budget_ms=round(polynomial_budget_ms, 4),
        raw_frame_cost_ms=round(raw_frame_cost_ms, 4),
        practical_frame_cost_ms=round(practical_frame_cost_ms, 4),
        consequent_frame_cost_ms=round(consequent_frame_cost_ms, 4),
        worst_case_tail_ms=round(worst_case_tail_ms, 4),
        overload_ms=round(overload_ms, 4),
        theta=round(theta, 4),
        clog_risk=round(clog_risk, 4),
        frame_buffer_misalignment=round(misalignment, 4),
        predictive_share=round(predictive_share, 4),
        adaptive_share=round(adaptive_share, 4),
        operation_split=operation_split,
        mesh_plan=mesh_plan,
        physics_plan=physics_plan,
        family_hub_signal=family_signal,
        recommendations=recommendations,
    )


def sample_scenarios() -> list[HopeFrameResult]:
    scenarios = [
        (
            MeshProfile("hope_star_forge", 340000, 14, 68, 5, 4),
            PhysicsProfile(54, 160, 12, 0.74, 1.1),
            PipelineProfile(980, 46.0, 0.38, 7, 0.19),
            CosmicProfile(18, 4, 26, 0.62),
            KinshipHubProfile(6, 0.71, 0.78, 0.28),
        ),
        (
            MeshProfile("hope_open_arms_courtyard", 190000, 9, 34, 2, 5),
            PhysicsProfile(26, 72, 10, 0.44, 0.72),
            PipelineProfile(520, 18.0, 0.21, 4, 0.11),
            CosmicProfile(10, 3, 14, 0.36),
            KinshipHubProfile(8, 0.84, 0.91, 0.18),
        ),
        (
            MeshProfile("hope_threshold_run", 420000, 18, 82, 6, 3),
            PhysicsProfile(82, 240, 14, 0.88, 1.34),
            PipelineProfile(1340, 62.0, 0.47, 9, 0.26),
            CosmicProfile(22, 5, 34, 0.75),
            KinshipHubProfile(4, 0.46, 0.39, 0.58),
        ),
    ]
    return [evaluate_hope_frame(*scenario) for scenario in scenarios]


def main() -> None:
    payload = {
        "framework": "HOPE",
        "expansion": "Hierarchical Operations and Predictive Ecology",
        "results": [result.to_dict() for result in sample_scenarios()],
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()