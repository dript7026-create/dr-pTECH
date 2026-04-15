from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from prototype_gameplay_flow import GameplayMode, GameplayPrototypeController
from xenobloods_systems import LifeForm, create_starting_player


def test_eye_lock_collision_enters_battle_with_preemptive_damage() -> None:
    controller = GameplayPrototypeController(create_starting_player("Ishtasha"))

    controller.begin_eye_lock_encounter("scarab_child_acolyte")
    controller.resolve_collision(0.5)

    assert controller.mode == GameplayMode.BATTLE_SCENE
    assert controller.battle_state is not None
    assert controller.battle_state.enemy_id == "scarab_child_acolyte"
    assert controller.battle_state.enemy_health == 32.0
    assert "Preemptive damage" in controller.battle_state.last_resolution


def test_wrong_up_dialogue_card_routes_into_low() -> None:
    controller = GameplayPrototypeController(create_starting_player("Ishtasha"))

    controller.route_to_up_dialogue("opal_tetrarch")
    controller.play_dialogue_card("answer")

    assert controller.mode == GameplayMode.LOW_PUZZLE
    assert controller.low_puzzle_state is not None
    assert controller.low_puzzle_state.curgz_id == "curgz_alpha"
    assert "cast down into Low" in controller.status_text


def test_low_puzzle_clear_returns_landborne_to_land() -> None:
    controller = GameplayPrototypeController(create_starting_player("Ishtasha"))

    controller.route_to_low_puzzle("curgz_alpha")
    controller.redirect_curgz_current("refract")
    controller.redirect_curgz_current("resist")
    controller.redirect_curgz_current("collapse")

    assert controller.mode == GameplayMode.LAND_NAVIGATION
    assert controller.current_zone == "veinmarket"
    assert controller.player.life_form == LifeForm.LANDBORNE
    assert "route back toward Land" in controller.status_text


def test_boss_clear_routes_into_up_denouement() -> None:
    controller = GameplayPrototypeController(create_starting_player("Ishtasha"))

    controller.begin_boss_sequence()
    assert controller.battle_state is not None
    controller.battle_state.enemy_health = 4.0
    controller.resolve_boss_exchange("dodge", 0.5, "background", ranged=True)

    assert controller.mode == GameplayMode.UP_DIALOGUE
    assert controller.dialogue_state is not None
    assert controller.dialogue_state.target_exchanges == 2
    assert controller.dialogue_state.safe_card == "answer"