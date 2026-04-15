from __future__ import annotations

import json
from pathlib import Path

from tools.xbox_series_input import translate_raw_state


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"


def test_requested_xbox_bindings_are_present() -> None:
    profile = json.loads((CONFIG / "xbox_series_input.json").read_text(encoding="utf-8"))
    assert profile["move"] == "left_stick"
    assert profile["aim"] == "right_stick"
    assert profile["shoot"] == "right_trigger"
    assert profile["dodge"] == "b"
    assert profile["jump"] == "a"
    assert profile["reload"] == "x"
    assert profile["swap_mode"] == "y"
    assert profile["sprint"] == "left_trigger"


def test_requested_bindings_translate_to_runtime_actions() -> None:
    frame = translate_raw_state(
        {
            "left_x": 0.5,
            "left_y": -0.25,
            "right_x": 0.6,
            "right_y": -0.4,
            "right_trigger": 0.9,
            "left_trigger": 0.7,
            "a": True,
            "b": True,
            "x": True,
            "y": True,
        }
    )
    assert frame.shoot is True
    assert frame.sprint is True
    assert frame.jump is True
    assert frame.evade is True
    assert frame.reload is True
    assert frame.swap_mode is True
    assert frame.move.x > 0
    assert frame.aim.x < 0
