from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
LEVEL = json.loads((ROOT / "config" / "level_01.json").read_text(encoding="utf-8"))


def test_progression_audio_and_population_pass() -> None:
    render_style = PROJECT.get("render_style", {})
    assert render_style.get("presentation") == "enhanced_photoreal_anthropomorphic_3d"

    audio = PROJECT.get("audio", {})
    assert audio.get("music_enabled") is True
    assert audio.get("sfx_enabled") is True

    rooms = {room["id"]: room for room in LEVEL["rooms"]}
    total_regular = len(rooms["room_01"]["enemies"]) + len(rooms["room_02"]["enemies"])
    assert total_regular == 15

    gating = LEVEL.get("gating", [])
    assert len(gating) >= 2
    assert gating[0]["requirement"]["type"] == "enemy_clear_threshold"
    assert gating[1]["requirement"]["type"] in {"pickup_and_enemy_clear", "enemy_clear_threshold"}

    models = {item["id"]: item for item in PROJECT["models"]}
    assert models["robot_player"]["polygons"] >= 800
    assert models["lizard_enemy_a"]["polygons"] >= 400
    assert models["lizard_enemy_b"]["polygons"] >= 400
    assert models["ape_robot_boss"]["polygons"] >= 500
