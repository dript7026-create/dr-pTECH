import json
from pathlib import Path

from egosphere.tools import synthesis_pipeline
from egosphere.tools import hope_runtime_sample


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "egosphere" / "pipeline" / "projects" / "hope_synthesis" / "hope_world.seed.json"


def test_compile_world_seed_generates_full_project_graph():
    seed = synthesis_pipeline.load_seed(SEED)
    project = synthesis_pipeline.compile_world_seed(seed)

    assert project["project_name"] == "HopeOpenArms"
    assert project["synthesis"]["framework"] == "HOPE"
    assert project["assets"]["meshes"]
    assert project["assets"]["materials"]
    assert project["assets"]["physics_rigs"]
    assert project["assets"]["structures"]
    assert project["assets"]["animations"]
    assert project["assets"]["ecology"]
    assert project["assets"]["audio"]
    assert any(system["name"] == "hope_ecology_system" for system in project["gameplay"]["systems"])
    assert any(system["name"] == "hope_world_system" for system in project["gameplay"]["systems"])
    assert all("hope" in scene for scene in project["gameplay"]["scenes"])
    assert any(entity["classname"] == "kinship_hub" for entity in project["gameplay"]["entities"])


def test_transpile_writes_canonical_manifest(tmp_path):
    out_path = tmp_path / "hope_project.generated.json"
    synthesis_pipeline.transpile(SEED, out_path)

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["project_name"] == "HopeOpenArms"
    assert payload["authoring"]["engine"]["module_name"] == "g_hopeopenarms"
    assert payload["gameplay"]["scenes"][0]["hope"]["scene_name"]


def test_build_generates_pipeline_outputs(tmp_path):
    synthesis_pipeline.build(SEED, tmp_path)

    assert (tmp_path / "game_project.generated.json").exists()
    assert (tmp_path / "generation" / "generation_manifest.json").exists()
    assert (tmp_path / "generation" / "hopeopenarms" / "meshes" / "open_arms_courtyard_terrain_mesh.obj").exists()
    assert (tmp_path / "generation" / "hopeopenarms" / "structures" / "open_arms_courtyard_gateway_arch.obj").exists()
    assert (tmp_path / "generation" / "hopeopenarms" / "animations" / "open_arms_courtyard_player_motion.json").exists()
    assert (tmp_path / "generation" / "hopeopenarms" / "ecology" / "open_arms_courtyard_population.json").exists()
    assert (tmp_path / "generation" / "hopeopenarms" / "audio" / "open_arms_courtyard_ambience.wav").exists()
    assert (tmp_path / "generation" / "hopeopenarms" / "sprites" / "open_arms_courtyard_player_avatar.png").exists()
    assert (tmp_path / "art_bundle" / "art_export.json").exists()
    assert (tmp_path / "blender_bundle" / "blender_conversion.json").exists()
    assert (tmp_path / "engine_bundle" / "engine_manifest.json").exists()

    sprite_bytes = (tmp_path / "generation" / "hopeopenarms" / "sprites" / "open_arms_courtyard_player_avatar.png").read_bytes()
    mesh_text = (tmp_path / "generation" / "hopeopenarms" / "meshes" / "open_arms_courtyard_terrain_mesh.obj").read_text(encoding="utf-8")
    structure_text = (tmp_path / "generation" / "hopeopenarms" / "structures" / "open_arms_courtyard_gateway_arch.obj").read_text(encoding="utf-8")
    animation_payload = json.loads((tmp_path / "generation" / "hopeopenarms" / "animations" / "open_arms_courtyard_player_motion.json").read_text(encoding="utf-8"))
    ecology_payload = json.loads((tmp_path / "generation" / "hopeopenarms" / "ecology" / "open_arms_courtyard_population.json").read_text(encoding="utf-8"))
    audio_bytes = (tmp_path / "generation" / "hopeopenarms" / "audio" / "open_arms_courtyard_ambience.wav").read_bytes()

    assert sprite_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert "v " in mesh_text and "f " in mesh_text
    assert "o open_arms_courtyard_gateway_arch" in structure_text
    assert animation_payload["frame_count"] >= 6
    assert "root_x" in animation_payload["channels"]
    assert ecology_payload["spawn_budget"] >= 2
    assert ecology_payload["population"][0]["archetype"]
    assert audio_bytes.startswith(b"RIFF")


def test_runtime_sample_consumes_generated_hope_metadata(tmp_path):
    project_path = synthesis_pipeline.build(SEED, tmp_path)
    save_path = tmp_path / "sanctuary_state.json"
    runtime = hope_runtime_sample.run_project(project_path, ticks=2, cycles=2, save_path=save_path)

    assert runtime["project_name"] == "HopeOpenArms"
    assert runtime["system_graph"][0] == "reality_cell_system"
    assert "ecology_state_system" in runtime["system_graph"]
    assert "sanctuary_state_system" in runtime["system_graph"]
    assert "preview_loop_system" in runtime["system_graph"]
    assert len(runtime["scenes"]) == 6
    first_scene = runtime["scenes"][0]
    assert first_scene["frames"][0]["hope_controller_system"]["tail_target_ms"] >= 16.67
    assert "presentation_system" in first_scene["frames"][0]
    assert "scene_transition_system" in first_scene["frames"][0]
    assert save_path.exists()
    saved_state = json.loads(save_path.read_text(encoding="utf-8"))
    assert saved_state["transitions"] >= 1


def test_preview_snapshot_summarizes_generated_runtime(tmp_path):
    project_path = synthesis_pipeline.build(SEED, tmp_path)
    snapshot = hope_runtime_sample.build_preview_snapshot(project_path, ticks=1, cycles=1)

    assert snapshot["project_name"] == "HopeOpenArms"
    assert snapshot["scene_cards"]
    assert snapshot["scene_cards"][0]["ecology_stability"] >= 0.0
    assert snapshot["sanctuary_state"]["memory"] >= 0.0


def test_singular_asset_type_handles_irregular_plural_keys():
    assert synthesis_pipeline._singular_asset_type("meshes") == "mesh"
    assert synthesis_pipeline._singular_asset_type("physics_rigs") == "physics_rig"
    assert synthesis_pipeline._singular_asset_type("animations") == "animation"