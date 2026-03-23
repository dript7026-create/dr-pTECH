from egosphere.tools.hope_framework import (
    CosmicProfile,
    HopeConfig,
    KinshipHubProfile,
    MeshProfile,
    PhysicsProfile,
    PipelineProfile,
    evaluate_hope_frame,
    sample_scenarios,
)


def test_hope_adaptation_reduces_tail_for_overloaded_scene():
    mesh = MeshProfile("overload_mesh", 460000, 19, 88, 6, 3)
    physics = PhysicsProfile(84, 260, 14, 0.9, 1.36)
    pipeline = PipelineProfile(1480, 68.0, 0.49, 10, 0.28)
    cosmic = CosmicProfile(24, 5, 38, 0.78)
    kinship = KinshipHubProfile(4, 0.42, 0.35, 0.61)

    baseline = evaluate_hope_frame(mesh, physics, pipeline, cosmic, kinship, adaptation_enabled=False)
    adaptive = evaluate_hope_frame(mesh, physics, pipeline, cosmic, kinship)

    assert adaptive.theta > 0.0
    assert adaptive.practical_frame_cost_ms < baseline.practical_frame_cost_ms
    assert adaptive.worst_case_tail_ms < baseline.worst_case_tail_ms
    assert adaptive.clog_risk == baseline.clog_risk


def test_kinship_hub_stabilizes_sanctuary_scene():
    mesh = MeshProfile("sanctuary", 210000, 8, 24, 2, 5)
    physics = PhysicsProfile(24, 64, 9, 0.4, 0.62)
    pipeline = PipelineProfile(470, 14.0, 0.18, 3, 0.09)
    cosmic = CosmicProfile(9, 3, 12, 0.32)
    strained = KinshipHubProfile(5, 0.32, 0.28, 0.62)
    coherent = KinshipHubProfile(8, 0.86, 0.93, 0.16)

    strained_result = evaluate_hope_frame(mesh, physics, pipeline, cosmic, strained)
    coherent_result = evaluate_hope_frame(mesh, physics, pipeline, cosmic, coherent)

    assert coherent_result.family_hub_signal["sanctuary_strength"] > strained_result.family_hub_signal["sanctuary_strength"]
    assert coherent_result.worst_case_tail_ms < strained_result.worst_case_tail_ms
    assert coherent_result.frame_buffer_misalignment <= strained_result.frame_buffer_misalignment


def test_operation_split_stays_normalized_and_scenarios_are_json_ready():
    results = sample_scenarios()

    assert len(results) == 3
    for result in results:
        total = sum(result.operation_split.values())
        assert 0.99 <= total <= 1.01
        assert result.to_dict()["scene_name"]


def test_high_pressure_config_pushes_theta_higher():
    mesh = MeshProfile("pressure_test", 300000, 12, 48, 4, 4)
    physics = PhysicsProfile(42, 108, 11, 0.63, 0.94)
    pipeline = PipelineProfile(760, 28.0, 0.27, 5, 0.14)
    cosmic = CosmicProfile(14, 4, 20, 0.48)
    kinship = KinshipHubProfile(6, 0.68, 0.72, 0.24)

    calm = evaluate_hope_frame(mesh, physics, pipeline, cosmic, kinship, config=HopeConfig(godai_pressure=0.92))
    pressured = evaluate_hope_frame(mesh, physics, pipeline, cosmic, kinship, config=HopeConfig(godai_pressure=1.24))

    assert pressured.theta >= calm.theta
    assert pressured.raw_frame_cost_ms > calm.raw_frame_cost_ms