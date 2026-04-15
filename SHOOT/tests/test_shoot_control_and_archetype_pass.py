from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))
LEVEL = json.loads((ROOT / "config" / "level_01.json").read_text(encoding="utf-8"))
CONTROLS = json.loads((ROOT / "config" / "xbox_series_input.json").read_text(encoding="utf-8"))


def test_requested_xbox_layout_is_present() -> None:
    profile = PROJECT["controller_support"]["xbox_series"]
    assert profile["aim"] == "right_stick"
    assert profile["shoot"] == "right_trigger"
    assert profile["dodge"] == "b"
    assert profile["jump"] == "a"
    assert profile["reload"] == "x"
    assert profile["swap_mode"] == "y"
    assert profile["sprint"] == "left_trigger"
    assert profile["parry"] == "left_shoulder"
    assert profile["melee"] == "right_shoulder"
    assert CONTROLS["parry"] == "left_shoulder"
    assert CONTROLS["melee"] == "right_shoulder"


def test_enemy_archetypes_and_boss_movement_match_requested_pass() -> None:
    weapons = {item["id"] for item in PROJECT["enemy_weapon_types"]}
    assert "raptor_claws" in weapons
    archetypes = {item["id"]: item["traits"] for item in PROJECT["enemy_archetypes"]}
    assert "lizard_brute" in archetypes
    assert "slow" in archetypes["lizard_brute"]
    assert "lizard_raptor" in archetypes
    assert "claw_attacker" in archetypes["lizard_raptor"]

    room_03 = next(room for room in LEVEL["rooms"] if room["id"] == "room_03")
    boss = room_03["enemies"][0]
    assert boss["movement_profile"] == "arena_leap_furniture_throw"
    assert boss["weapon_cycle"] == ["furnace_cannon", "arc_maul", "missile_fist"]
