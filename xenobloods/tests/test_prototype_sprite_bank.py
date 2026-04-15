from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from prototype_sprite_bank import ROOT, build_sprite_bank


def test_build_sprite_bank_contains_expected_animation_sets() -> None:
    metadata = build_sprite_bank(force=True)

    sprites = metadata["sprites"]
    assert "ishtasha" in sprites
    assert "scarab_child" in sprites
    assert "lahgroid" in sprites

    assert len(sprites["ishtasha"]["animations"]["run"]) == 6
    assert len(sprites["ishtasha"]["animations"]["parry"]) == 5
    assert len(sprites["ishtasha"]["animations"]["jump"]) == 4
    assert len(sprites["ishtasha"]["animations"]["dash"]) == 5
    assert len(sprites["ishtasha"]["animations"]["surge"]) == 6
    assert len(sprites["scarab_child"]["animations"]["attack"]) == 5
    assert len(sprites["scarab_child"]["animations"]["feint"]) == 4
    assert len(sprites["scarab_child"]["animations"]["transition"]) == 4
    assert len(sprites["scarab_child"]["animations"]["recoil"]) == 5
    assert len(sprites["scarab_child"]["animations"]["death"]) == 6
    assert len(sprites["lattice_ward"]["animations"]["flare"]) == 4
    assert len(sprites["lattice_ward"]["animations"]["death"]) == 6
    assert len(sprites["lahgroid"]["animations"]["feint"]) == 4
    assert len(sprites["lahgroid"]["animations"]["transition"]) == 4

    for relative_path in sprites["ishtasha"]["animations"]["idle"]:
        assert (ROOT / relative_path).exists()