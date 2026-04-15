from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from build_pikerel_worldpack import build_gameplay_bindings, build_scene_manifest


def test_build_scene_manifest_respects_asset_prefixes_for_standalone_package() -> None:
    variant_names = [f"pikerel_basket_house_{index:02d}" for index in range(1, 7)]
    prop_names = [
        "pikerel_walkway_segment",
        "pikerel_shrine_post",
        "pikerel_dock_platform",
        "pikerel_reed_cluster",
        "xenobloods_swamp_island",
        "xenobloods_lagoon_water_plane",
        "xenobloods_mangrove_root_cluster",
        "xenobloods_sewer_tunnel_blockout",
    ]

    scene_payload = build_scene_manifest(variant_names, prop_names, model_path_prefix="../models/", billboard_path_prefix="../billboards/")

    first_mesh = next(entry for entry in scene_payload["scene_entries"] if entry["kind"] == "mesh")
    landborne_billboard = next(entry for entry in scene_payload["scene_entries"] if entry["id"] == "player_life_landborne")
    assert first_mesh["mesh"].startswith("../models/")
    assert landborne_billboard["image_path"].startswith("../billboards/")
    assert "threshold_gate" in scene_payload["script_capabilities"]


def test_build_gameplay_bindings_preserves_billboard_metadata() -> None:
    variant_names = [f"pikerel_basket_house_{index:02d}" for index in range(1, 7)]
    prop_names = ["pikerel_walkway_segment"]

    scene_payload = build_scene_manifest(variant_names, prop_names, model_path_prefix="models/", billboard_path_prefix="billboards/")
    bindings = build_gameplay_bindings(scene_payload)

    assert bindings["player_life_landborne"]["life_form"] == "landborne"
    assert bindings["boss_lahgroid"]["actor_id"] == "lahgroid_hierophant"
    assert bindings["sewer_preview_gate"]["unlock_flag"] == "sewer_unlocked"