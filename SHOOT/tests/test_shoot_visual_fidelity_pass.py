from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))


def test_visual_fidelity_pass_raises_polygon_density_and_material_detail() -> None:
    render_style = PROJECT.get("render_style", {})
    assert render_style.get("presentation") == "enhanced_photoreal_anthropomorphic_3d"

    models = {item["id"]: item for item in PROJECT["models"]}
    assert models["robot_player"]["polygons"] >= 800
    assert models["lizard_enemy_a"]["polygons"] >= 400
    assert models["lizard_enemy_b"]["polygons"] >= 400
    assert models["ape_robot_boss"]["polygons"] >= 500

    for item in models.values():
        assert item["polygons"] <= item["polygon_budget"] <= 1000
