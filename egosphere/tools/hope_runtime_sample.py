from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass
class SceneRuntimeState:
    scene_id: str
    scene_type: str
    theta: float
    clog_risk: float
    misalignment: float
    sanctuary_strength: float
    predictive_share: float
    adaptive_share: float
    tail_ms: float
    practical_ms: float
    target_profile: dict[str, object]
    matter_profile: dict[str, float]
    causality_profile: dict[str, float]


@dataclass
class SanctuaryState:
    harmony: float
    care: float
    memory: float
    transitions: int
    current_scene: str


def load_project(project_path: Path) -> dict:
    return json.loads(project_path.read_text(encoding="utf-8"))


def build_scene_state(scene: dict) -> SceneRuntimeState:
    hope = scene["hope"]
    family = hope["family_hub_signal"]
    return SceneRuntimeState(
        scene_id=scene["id"],
        scene_type=scene.get("scene_type", "exploration"),
        theta=float(hope["theta"]),
        clog_risk=float(hope["clog_risk"]),
        misalignment=float(hope["frame_buffer_misalignment"]),
        sanctuary_strength=float(family["sanctuary_strength"]),
        predictive_share=float(hope["predictive_share"]),
        adaptive_share=float(hope["adaptive_share"]),
        tail_ms=float(hope["worst_case_tail_ms"]),
        practical_ms=float(hope["practical_frame_cost_ms"]),
        target_profile=dict(hope.get("target_profile", {})),
        matter_profile=dict(scene.get("matter", hope.get("matter_plan", {}))),
        causality_profile=dict(scene.get("causality", hope.get("causality_plan", {}))),
    )


def reality_cell_system(state: SceneRuntimeState) -> dict[str, float]:
    coherence = _clamp(1.0 - state.theta * 0.26 - state.clog_risk * 0.22 + state.sanctuary_strength * 0.31, 0.0, 1.0)
    recursion_tension = _clamp(state.theta * 0.42 + state.clog_risk * 0.38 - state.sanctuary_strength * 0.14, 0.0, 1.0)
    return {"reality_coherence": round(coherence, 4), "recursion_tension": round(recursion_tension, 4)}


def kinship_hub_system(state: SceneRuntimeState) -> dict[str, float]:
    refuge_stability = _clamp(state.sanctuary_strength * 0.8 + (1.0 - state.clog_risk) * 0.2, 0.0, 1.0)
    soul_link_gain = _clamp(state.sanctuary_strength * 0.72 + state.predictive_share * 0.16, 0.0, 1.0)
    return {"refuge_stability": round(refuge_stability, 4), "soul_link_gain": round(soul_link_gain, 4)}


def ecology_state_system(state: SceneRuntimeState) -> dict[str, float]:
    habitat_load = _clamp(state.clog_risk * 0.42 + state.theta * 0.24 + state.misalignment * 0.16, 0.0, 1.0)
    migration_pressure = _clamp(habitat_load * 0.7 + (1.0 - state.sanctuary_strength) * 0.22, 0.0, 1.0)
    ecology_stability = _clamp(1.0 - habitat_load * 0.54 + state.sanctuary_strength * 0.18, 0.0, 1.0)
    return {
        "habitat_load": round(habitat_load, 4),
        "migration_pressure": round(migration_pressure, 4),
        "ecology_stability": round(ecology_stability, 4),
    }


def input_causality_system(state: SceneRuntimeState) -> dict[str, float]:
    input_pressure = float(state.causality_profile.get("input_pressure", 0.5))
    affordance_span = float(state.causality_profile.get("affordance_span", 0.5))
    latency_pressure = float(state.target_profile.get("latency_pressure", 0.0))
    reactivity = _clamp(input_pressure * 0.42 + affordance_span * 0.24 + (1.0 - latency_pressure) * 0.24 + state.sanctuary_strength * 0.1, 0.0, 1.0)
    input_bandwidth = _clamp(affordance_span * 0.46 + float(state.target_profile.get("sensor_pressure", 0.0)) * 0.16 + state.predictive_share * 0.18 + (1.0 - state.theta) * 0.12, 0.0, 1.0)
    return {"input_reactivity": round(reactivity, 4), "input_bandwidth": round(input_bandwidth, 4)}


def matter_state_system(state: SceneRuntimeState) -> dict[str, float]:
    solid_density = float(state.matter_profile.get("solid_density", state.matter_profile.get("solid_retention", 0.4)))
    liquid_flow = float(state.matter_profile.get("liquid_flow", state.matter_profile.get("liquid_responsiveness", 0.3)))
    gas_diffusion = float(state.matter_profile.get("gas_diffusion", state.matter_profile.get("gas_resonance", 0.25)))
    fluid_turbulence = float(state.matter_profile.get("fluid_turbulence", 0.2))
    matter_coherence = _clamp(solid_density * 0.34 + liquid_flow * 0.22 + gas_diffusion * 0.16 + (1.0 - fluid_turbulence) * 0.18 + state.sanctuary_strength * 0.1, 0.0, 1.0)
    volumetric_flux = _clamp(liquid_flow * 0.32 + gas_diffusion * 0.24 + fluid_turbulence * 0.22 + state.adaptive_share * 0.14, 0.0, 1.0)
    return {
        "solid_stability": round(solid_density, 4),
        "liquid_motion": round(liquid_flow, 4),
        "gas_resonance": round(gas_diffusion, 4),
        "fluid_turbulence": round(fluid_turbulence, 4),
        "matter_coherence": round(matter_coherence, 4),
        "volumetric_flux": round(volumetric_flux, 4),
    }


def entity_influence_system(state: SceneRuntimeState, input_causality: dict, matter_state: dict) -> dict[str, float]:
    entity_feedback = float(state.causality_profile.get("entity_feedback", 0.5))
    render_reactivity = float(state.causality_profile.get("render_reactivity", 0.5))
    input_possibility_span = _clamp(entity_feedback * 0.38 + input_causality["input_bandwidth"] * 0.26 + matter_state["volumetric_flux"] * 0.18 + state.sanctuary_strength * 0.1, 0.0, 1.0)
    cosmetic_feedback = _clamp(render_reactivity * 0.42 + entity_feedback * 0.22 + matter_state["gas_resonance"] * 0.12 + state.predictive_share * 0.08, 0.0, 1.0)
    return {"input_possibility_span": round(input_possibility_span, 4), "cosmetic_feedback": round(cosmetic_feedback, 4)}


def sanctuary_state_system(state: SceneRuntimeState, sanctuary: SanctuaryState, kinship: dict, ecology: dict) -> dict[str, float]:
    sanctuary.harmony = _clamp(sanctuary.harmony * 0.82 + kinship["refuge_stability"] * 0.18 - ecology["migration_pressure"] * 0.04, 0.0, 1.0)
    sanctuary.care = _clamp(sanctuary.care * 0.74 + kinship["soul_link_gain"] * 0.26, 0.0, 1.0)
    sanctuary.memory = _clamp(sanctuary.memory * 0.9 + (1.0 - state.theta) * 0.08 + state.sanctuary_strength * 0.06 + ecology["ecology_stability"] * 0.03, 0.0, 1.0)
    sanctuary.current_scene = state.scene_id
    return {
        "harmony": round(sanctuary.harmony, 4),
        "care": round(sanctuary.care, 4),
        "memory": round(sanctuary.memory, 4),
    }


def hope_controller_system(state: SceneRuntimeState, cell: dict, kinship: dict) -> dict[str, float]:
    moderation = _clamp(state.theta * 0.62 + state.adaptive_share * 0.28 - kinship["refuge_stability"] * 0.16, 0.0, 1.0)
    tail_target = max(16.67, state.tail_ms * (1.0 - moderation * 0.18 - kinship["soul_link_gain"] * 0.06))
    return {"adaptive_moderation": round(moderation, 4), "tail_target_ms": round(tail_target, 4)}


def streaming_system(state: SceneRuntimeState, controller: dict) -> dict[str, float]:
    stream_pressure = _clamp(state.clog_risk * 0.68 + state.predictive_share * 0.24 - controller["adaptive_moderation"] * 0.22, 0.0, 1.0)
    queue_relief = _clamp(controller["adaptive_moderation"] * 0.48 + state.sanctuary_strength * 0.18, 0.0, 1.0)
    return {"stream_pressure": round(stream_pressure, 4), "queue_relief": round(queue_relief, 4)}


def physics_system(state: SceneRuntimeState, controller: dict) -> dict[str, float]:
    interaction_budget = _clamp(1.0 - state.theta * 0.21 + state.sanctuary_strength * 0.12, 0.58, 1.1)
    movement_stability = _clamp(1.0 - state.misalignment * 0.34 + controller["adaptive_moderation"] * 0.18, 0.5, 1.1)
    return {"interaction_budget": round(interaction_budget, 4), "movement_stability": round(movement_stability, 4)}


def presentation_system(state: SceneRuntimeState, streaming: dict, physics: dict) -> dict[str, float]:
    frame_alignment = _clamp(1.0 - state.misalignment * 0.72 + streaming["queue_relief"] * 0.18, 0.0, 1.0)
    present_window = max(16.67, state.practical_ms * (1.0 + state.misalignment * 0.18 - physics["movement_stability"] * 0.08))
    return {"frame_alignment": round(frame_alignment, 4), "present_window_ms": round(present_window, 4)}


def frame_reality_system(state: SceneRuntimeState, presentation: dict, input_causality: dict, entity_influence: dict, matter_state: dict) -> dict[str, float]:
    game_reality_coherence = _clamp(
        presentation["frame_alignment"] * 0.32
        + input_causality["input_reactivity"] * 0.18
        + entity_influence["input_possibility_span"] * 0.2
        + matter_state["matter_coherence"] * 0.16
        + (1.0 - state.clog_risk) * 0.14,
        0.0,
        1.0,
    )
    input_to_output_latency_ms = max(
        8.0,
        float(state.target_profile.get("input_latency_ms", 8.0))
        + presentation["present_window_ms"] * (1.0 - input_causality["input_reactivity"] * 0.18)
        - entity_influence["cosmetic_feedback"] * 2.6,
    )
    render_reactivity = _clamp(
        float(state.causality_profile.get("render_reactivity", 0.5)) * 0.38
        + entity_influence["cosmetic_feedback"] * 0.24
        + matter_state["volumetric_flux"] * 0.16
        + presentation["frame_alignment"] * 0.12,
        0.0,
        1.0,
    )
    return {
        "game_reality_coherence": round(game_reality_coherence, 4),
        "input_to_output_latency_ms": round(input_to_output_latency_ms, 4),
        "render_reactivity": round(render_reactivity, 4),
    }


def scene_transition_system(state: SceneRuntimeState, sanctuary: SanctuaryState, presentation: dict) -> dict[str, object]:
    transition_bias = _clamp((sanctuary.harmony + sanctuary.memory) * 0.5 - state.clog_risk * 0.18, 0.0, 1.0)
    ready = (presentation["present_window_ms"] <= 34.0 and sanctuary.harmony >= 0.42) or (
        presentation["present_window_ms"] <= 39.5 and transition_bias >= 0.25
    )
    if ready:
        sanctuary.transitions += 1
    return {"ready_to_transition": ready, "transition_bias": round(transition_bias, 4), "transition_count": sanctuary.transitions}


def preview_loop_system(state: SceneRuntimeState, sanctuary: SanctuaryState, transition: dict) -> dict[str, float]:
    preview_stability = _clamp(1.0 - state.clog_risk * 0.32 - state.misalignment * 0.22 + sanctuary.harmony * 0.24, 0.0, 1.0)
    continuity = _clamp(sanctuary.memory * 0.52 + transition["transition_bias"] * 0.28 + preview_stability * 0.2, 0.0, 1.0)
    return {"preview_stability": round(preview_stability, 4), "continuity": round(continuity, 4)}


def interaction_graph_system(state: SceneRuntimeState, physics: dict, input_causality: dict) -> dict[str, float]:
    affordance_span = float(state.causality_profile.get("affordance_span", 0.5) if hasattr(state, "causality_profile") else 0.5)
    affordance_coverage = _clamp(affordance_span * 0.44 + physics["interaction_budget"] * 0.32 + input_causality["input_bandwidth"] * 0.24, 0.0, 1.0)
    hit_contact_probability = _clamp(physics["interaction_budget"] * 0.52 + (1.0 - state.theta) * 0.28 + state.sanctuary_strength * 0.1, 0.0, 1.0)
    interaction_density = _clamp(affordance_span * 0.38 + input_causality["input_bandwidth"] * 0.32 + state.sanctuary_strength * 0.1, 0.0, 1.0)
    return {
        "affordance_coverage": round(affordance_coverage, 4),
        "hit_contact_probability": round(hit_contact_probability, 4),
        "interaction_density": round(interaction_density, 4),
    }


def hitbox_resolution_system(state: SceneRuntimeState, physics: dict, interaction: dict) -> dict[str, float]:
    hitbox_active_ratio = _clamp(interaction["interaction_density"] * 0.48 + (1.0 - state.clog_risk) * 0.32 + state.sanctuary_strength * 0.1, 0.0, 1.0)
    collision_budget = _clamp(physics["interaction_budget"] * 0.58 + (1.0 - state.theta) * 0.24 + state.sanctuary_strength * 0.08, 0.0, 1.0)
    contact_accuracy = _clamp(collision_budget * 0.52 + (1.0 - state.misalignment) * 0.28 + interaction["hit_contact_probability"] * 0.2, 0.0, 1.0)
    return {
        "hitbox_active_ratio": round(hitbox_active_ratio, 4),
        "collision_budget": round(collision_budget, 4),
        "contact_accuracy": round(contact_accuracy, 4),
    }


def vfx_dispatch_system(state: SceneRuntimeState, hitbox: dict, streaming: dict) -> dict[str, float]:
    vfx_load = _clamp(hitbox["hitbox_active_ratio"] * 0.36 + streaming["stream_pressure"] * 0.28 + state.theta * 0.18, 0.0, 1.0)
    particle_budget = _clamp(1.0 - vfx_load * 0.44 + state.sanctuary_strength * 0.14, 0.2, 1.0)
    visual_clarity = _clamp(state.sanctuary_strength * 0.4 + hitbox["contact_accuracy"] * 0.3 + (1.0 - vfx_load * 0.3), 0.0, 1.0)
    return {
        "vfx_load": round(vfx_load, 4),
        "particle_budget": round(particle_budget, 4),
        "visual_clarity": round(visual_clarity, 4),
    }


def simulate_scene(scene: dict, sanctuary: SanctuaryState, ticks: int = 3) -> dict:
    state = build_scene_state(scene)
    frames = []
    for tick in range(ticks):
        cell = reality_cell_system(state)
        ecology = ecology_state_system(state)
        kinship = kinship_hub_system(state)
        input_causality = input_causality_system(state)
        matter_state = matter_state_system(state)
        entity_influence = entity_influence_system(state, input_causality, matter_state)
        sanctuary_frame = sanctuary_state_system(state, sanctuary, kinship, ecology)
        controller = hope_controller_system(state, cell, kinship)
        streaming = streaming_system(state, controller)
        physics = physics_system(state, controller)
        interaction = interaction_graph_system(state, physics, input_causality)
        hitbox = hitbox_resolution_system(state, physics, interaction)
        vfx = vfx_dispatch_system(state, hitbox, streaming)
        presentation = presentation_system(state, streaming, physics)
        frame_reality = frame_reality_system(state, presentation, input_causality, entity_influence, matter_state)
        transition = scene_transition_system(state, sanctuary, presentation)
        preview = preview_loop_system(state, sanctuary, transition)
        frames.append(
            {
                "tick": tick,
                "reality_cell_system": cell,
                "ecology_state_system": ecology,
                "kinship_hub_system": kinship,
                "input_causality_system": input_causality,
                "matter_state_system": matter_state,
                "entity_influence_system": entity_influence,
                "sanctuary_state_system": sanctuary_frame,
                "hope_controller_system": controller,
                "streaming_system": streaming,
                "physics_system": physics,
                "interaction_graph_system": interaction,
                "hitbox_resolution_system": hitbox,
                "vfx_dispatch_system": vfx,
                "presentation_system": presentation,
                "frame_reality_system": frame_reality,
                "scene_transition_system": transition,
                "preview_loop_system": preview,
            }
        )
        state.tail_ms = controller["tail_target_ms"]
        state.practical_ms = presentation["present_window_ms"]
        state.clog_risk = _clamp(state.clog_risk - streaming["queue_relief"] * 0.08 + streaming["stream_pressure"] * 0.03, 0.0, 1.0)
        state.misalignment = _clamp(state.misalignment - presentation["frame_alignment"] * 0.07 + 0.02, 0.0, 1.0)
    return {
        "scene_id": scene["id"],
        "scene_type": scene.get("scene_type", "exploration"),
        "frames": frames,
        "final_tail_ms": round(state.tail_ms, 4),
        "sanctuary_memory": round(sanctuary.memory, 4),
    }


def run_project(project_path: Path, ticks: int = 3, cycles: int = 1, save_path: Path | None = None) -> dict:
    project = load_project(project_path)
    sanctuary = SanctuaryState(harmony=0.38, care=0.44, memory=0.32, transitions=0, current_scene=project["runtime"]["entry_scene"])
    scenes = []
    for _ in range(cycles):
        for scene in project["gameplay"]["scenes"]:
            scenes.append(simulate_scene(scene, sanctuary, ticks=ticks))
    payload = {
        "project_name": project["project_name"],
        "entry_scene": project["gameplay"]["scenes"][0]["id"],
        "system_graph": project.get("runtime", {}).get("system_graph", []),
        "scenes": scenes,
        "sanctuary_state": {
            "harmony": round(sanctuary.harmony, 4),
            "care": round(sanctuary.care, 4),
            "memory": round(sanctuary.memory, 4),
            "transitions": sanctuary.transitions,
            "current_scene": sanctuary.current_scene,
        },
    }
    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(payload["sanctuary_state"], indent=2), encoding="utf-8")
        payload["sanctuary_state_path"] = str(save_path)
    return payload


def build_preview_snapshot(project_path: Path, ticks: int = 2, cycles: int = 1) -> dict:
    runtime = run_project(project_path, ticks=ticks, cycles=cycles)
    scene_cards = []
    for scene in runtime["scenes"]:
        first_frame = scene["frames"][0]
        scene_cards.append(
            {
                "scene_id": scene["scene_id"],
                "scene_type": scene["scene_type"],
                "tail_ms": scene["final_tail_ms"],
                "coherence": first_frame["reality_cell_system"]["reality_coherence"],
                "ecology_stability": first_frame["ecology_state_system"]["ecology_stability"],
                "game_reality_coherence": first_frame["frame_reality_system"]["game_reality_coherence"],
                "input_reactivity": first_frame["input_causality_system"]["input_reactivity"],
                "transition_bias": first_frame["scene_transition_system"]["transition_bias"],
                "affordance_coverage": first_frame["interaction_graph_system"]["affordance_coverage"],
                "contact_accuracy": first_frame["hitbox_resolution_system"]["contact_accuracy"],
                "visual_clarity": first_frame["vfx_dispatch_system"]["visual_clarity"],
            }
        )
    return {
        "project_name": runtime["project_name"],
        "system_graph": runtime["system_graph"],
        "sanctuary_state": runtime["sanctuary_state"],
        "scene_cards": scene_cards,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the HOPE system-of-systems runtime sample")
    parser.add_argument("project", type=Path)
    parser.add_argument("--ticks", type=int, default=3)
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_project(args.project, ticks=args.ticks, cycles=args.cycles, save_path=args.save), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())