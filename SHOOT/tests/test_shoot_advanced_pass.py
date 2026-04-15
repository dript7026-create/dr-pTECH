from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"


def test_advanced_controller_bindings_and_profiles_exist() -> None:
    project = json.loads((CONFIG / "project.json").read_text(encoding="utf-8"))
    profile = json.loads((CONFIG / "xbox_series_input.json").read_text(encoding="utf-8"))

    assert profile["move"] == "left_stick"
    assert profile["aim"] == "right_stick"
    assert profile["shoot"] == "right_trigger"
    assert profile["dodge"] == "b"
    assert profile["jump"] == "a"
    assert profile["reload"] == "x"
    assert profile["swap_mode"] == "y"
    assert profile["sprint"] == "left_trigger"
    assert profile["melee"] == "right_shoulder"
    assert profile["parry"] == "left_shoulder"

    style = project.get("render_style", {})
    assert style.get("presentation") == "enhanced_photoreal_anthropomorphic_3d"
    assert style.get("projectile_trails") is True

    player_design = project.get("character_design", {}).get("player_robot", {})
    assert player_design.get("silhouette") == "slender_android"
    assert "chrome plating" in " ".join(player_design.get("features", [])).lower()

    enemy_archetypes = project.get("enemy_archetypes", [])
    ids = {entry["id"] for entry in enemy_archetypes}
    assert "lizard_brute" in ids
    assert "lizard_raptor" in ids


def test_runtime_smoke_summary_reports_advanced_features() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "shoot_game.py"), "--smoke-test"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    summary = json.loads(result.stdout.strip())
    assert summary["renderer_mode"] == "obj_low_poly_3d"
    assert summary["camera_mode"] == "over_the_shoulder"
    assert summary["movement_mode"] == "omnidirectional"
    assert summary["projectile_trails"] is True
    assert summary["melee_enabled"] is True
    assert summary["parry_enabled"] is True
    assert summary["boss_behavior"] == "arena_leap_furniture_throw"
    assert summary["audio_enabled"] is True
    assert summary["gating_mode"] == "multi_stage_security_shutters"
