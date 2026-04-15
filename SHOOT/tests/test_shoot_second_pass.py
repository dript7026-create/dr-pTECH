from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"


def test_shoot_second_pass_matches_requested_features() -> None:
    project = json.loads((CONFIG / "project.json").read_text(encoding="utf-8"))
    level = json.loads((CONFIG / "level_01.json").read_text(encoding="utf-8"))

    controller = project.get("controller_support", {})
    assert controller.get("enabled") is True
    assert controller.get("preferred_device") == "xbox_series"

    enemy_weapons = project.get("enemy_weapon_types", [])
    boss_weapons = project.get("boss_weapon_types", [])
    upgrades = project.get("temporary_ammo_upgrades", [])

    assert len(enemy_weapons) == 5
    assert len(boss_weapons) == 3
    assert len(upgrades) >= 3
    assert all(item["duration_seconds"] > 0 for item in upgrades)

    room_counts = {
        room["id"]: len(room.get("enemies", []))
        for room in level["rooms"]
        if room["id"] in {"room_01", "room_02"}
    }
    assert sum(room_counts.values()) == 15
    assert room_counts["room_01"] > 0
    assert room_counts["room_02"] > 0

    for model in project["models"]:
        assert model["polygons"] <= model["polygon_budget"] <= 1000
