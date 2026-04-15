import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_manifest() -> dict:
    builder = load_module("double_blade_builder_runtime", "DoubleBladeEverGlades/tools/build_progression_manifest.py")
    source_path = ROOT / "DoubleBladeEverGlades" / "double_blade_everglades_project.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    return builder.build_progression(source)


def test_blades_and_enemies_have_unique_runtime_curve_signatures():
    manifest = load_manifest()
    blades = manifest["blades"]
    enemies = manifest["enemy_varieties"]

    blade_signatures = {
        (
            blade["weight_rating"],
            blade["movement_arc_degrees"],
            blade["pace_response_curve"]["tempo_bias"],
        )
        for blade in blades
    }
    enemy_signatures = {
        (
            enemy["spawn_profile"]["base_weight"],
            enemy["behavior_profile"]["aggression"],
            enemy["threat_response_curve"]["tempo_gain"],
        )
        for enemy in enemies
    }

    assert len(blade_signatures) > 300
    assert len(enemy_signatures) > 120


def test_route_runtime_covers_all_rootknots_in_order():
    manifest = load_manifest()
    route_runtime = load_module("double_blade_route_runtime", "DoubleBladeEverGlades/runtime/route_runtime.py")
    route = route_runtime.build_route_runtime(manifest)

    rootknots = manifest["progression"]["rootknots"]
    assert route["rootknot_order"] == [rootknot["id"] for rootknot in rootknots]
    assert len(route["segments"]) == len(rootknots) - 1
    assert route["route_total_distance"] > 0


def test_navigation_pace_uses_player_tempo_and_rootknot_distances():
    variation_runtime = load_module("double_blade_variation_runtime", "DoubleBladeEverGlades/runtime/variation_runtime.py")
    pace = variation_runtime.compute_navigation_pace(
        character_traverse_rate=6.0,
        idle_time_between_progressive_actions=1.5,
        distance_to_nearest_rootknot=12.0,
        distance_from_previous_rootknot=4.0,
    )
    assert pace == 44.0


def test_run_variation_is_deterministic_per_seed_but_changes_across_runs():
    manifest = load_manifest()
    variation_runtime = load_module("double_blade_variation_runtime", "DoubleBladeEverGlades/runtime/variation_runtime.py")

    run_a = variation_runtime.build_run_variation_tables(manifest, run_seed=77, navigation_pace=9.5)
    run_b = variation_runtime.build_run_variation_tables(manifest, run_seed=77, navigation_pace=9.5)
    run_c = variation_runtime.build_run_variation_tables(manifest, run_seed=91, navigation_pace=9.5)

    assert run_a["enemy_profiles"][0] == run_b["enemy_profiles"][0]
    assert run_a["blade_profiles"][0] == run_b["blade_profiles"][0]
    assert run_a["enemy_profiles"][0] != run_c["enemy_profiles"][0]


def test_save_runtime_autosaves_and_saves_at_rootknots(tmp_path):
    session_runtime = load_module("double_blade_session_runtime", "DoubleBladeEverGlades/runtime/session_runtime.py")
    save_runtime = session_runtime.SaveRuntime(tmp_path)
    state = session_runtime.GameState(
        run_seed=404,
        active_rootknot_id="rootknot_01",
        previous_rootknot_id=None,
        distance_to_nearest_rootknot=18.0,
        distance_from_previous_rootknot=0.0,
        blade_ids=["amber_steel_serrated_pruner"],
        defeated_enemy_ids=["vine_snare_feral"],
        rootknot_visits=[],
    )

    slot_path = save_runtime.save("slot_a", state)
    autosave_path = save_runtime.autosave(state)
    rootknot_save_path = save_runtime.save_at_rootknot(state, "rootknot_02", 0.1)
    restored = save_runtime.load("slot_a")

    assert slot_path.exists()
    assert autosave_path.exists()
    assert rootknot_save_path.exists()
    assert restored.run_seed == 404
    autosave_payload = json.loads(rootknot_save_path.read_text(encoding="utf-8"))
    assert autosave_payload["active_rootknot_id"] == "rootknot_02"
    assert autosave_payload["distance_to_nearest_rootknot"] == 0.0
    assert autosave_payload["rootknot_visits"][0]["rootknot_id"] == "rootknot_02"