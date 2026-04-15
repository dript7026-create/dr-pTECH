from __future__ import annotations

import json
from pathlib import Path

from tools.xbox_series_input import translate_raw_state

ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))


def test_right_stick_horizontal_is_not_inverted() -> None:
    frame = translate_raw_state({"right_x": 0.7, "right_y": 0.0})
    assert frame.aim.x < 0


def test_controller_deadzone_is_tightened() -> None:
    profile = PROJECT["controller_support"]["xbox_series"]
    assert profile["deadzone"]["left_stick"] <= 0.12
    assert profile["deadzone"]["right_stick"] <= 0.1
