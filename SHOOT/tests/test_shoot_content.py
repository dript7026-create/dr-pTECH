from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
LEVEL = json.loads((ROOT / "config" / "level_01.json").read_text(encoding="utf-8"))


def test_regular_enemies_are_distributed_across_two_rooms() -> None:
    rooms = {room["id"]: room for room in LEVEL["rooms"]}
    room_01 = rooms["room_01"]["enemies"]
    room_02 = rooms["room_02"]["enemies"]
    assert len(room_01) > 0
    assert len(room_02) > 0
    assert len(room_01) + len(room_02) == 15
    assert all(enemy["hitpoints"] == 8 for enemy in room_01 + room_02)


def test_xbox_series_controller_profile_exists() -> None:
    controller = PROJECT["controller_support"]["xbox_series"]
    assert controller["enabled"] is True
    assert "left_stick" in controller["move"]
    assert controller["aim"] == "right_stick"
    assert controller["shoot"] == "right_trigger"


def test_weapons_and_ammo_upgrades_are_defined() -> None:
    enemy_weapons = PROJECT["enemy_weapon_types"]
    boss_weapons = PROJECT["boss_weapon_types"]
    upgrades = PROJECT["ammo_upgrades"]

    assert len(enemy_weapons) >= 5
    assert len(boss_weapons) >= 3
    assert all(weapon["boss_exclusive"] is True for weapon in boss_weapons)
    assert len(upgrades) >= 3
    assert all(upgrade["collectible"] is True for upgrade in upgrades)
    assert all(upgrade["temporary_seconds"] > 0 for upgrade in upgrades)


def test_models_stay_under_budget() -> None:
    for model in PROJECT["models"]:
        assert model["polygons"] <= model["polygon_budget"] <= 1000
