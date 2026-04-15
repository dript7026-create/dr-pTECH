from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from prototype_gameplay_flow import GameplayMode, GameplayPrototypeController
from prototype_metroidvania_runtime import BattlePhase, MetroidvaniaRuntime, PresentationMode, RuntimeInput
from xenobloods_systems import LifeForm, create_starting_player


def _advance_land_birth(runtime: MetroidvaniaRuntime) -> None:
    runtime.start_game()
    runtime.update(0.016, RuntimeInput(interact_pressed=True))
    runtime.update(0.5, RuntimeInput())
    runtime.update(0.016, RuntimeInput(move_y=1.0, block_pressed=True))
    runtime.update(0.016, RuntimeInput(move_y=-1.0, jump_pressed=True))
    runtime.update(0.5, RuntimeInput())
    runtime.update(0.016, RuntimeInput(move_y=1.0, dash_pressed=True))


def _advance_first_encounter_to_window(runtime: MetroidvaniaRuntime, move_y: float) -> None:
    runtime.update(0.016, RuntimeInput())
    runtime.update(0.34, RuntimeInput(move_y=move_y))
    runtime.update(0.16, RuntimeInput(move_y=move_y))
    runtime.update(0.84, RuntimeInput(move_y=move_y))
    runtime.update(0.2, RuntimeInput(move_y=move_y))


def test_title_confirm_starts_exploration() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))

    runtime.update(0.016, RuntimeInput(confirm_pressed=True))

    assert runtime.mode == PresentationMode.INCUBATION
    assert runtime.flow.player.life_form == LifeForm.GOURD_INFANT


def test_birth_sequence_hatches_into_land_navigation() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))

    _advance_land_birth(runtime)

    assert runtime.mode == PresentationMode.EXPLORATION
    assert runtime.flow.mode == GameplayMode.LAND_NAVIGATION
    assert runtime.flow.player.life_form == LifeForm.LANDBORNE


def test_birth_sequence_requires_lane_and_timing_for_qte_training() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    runtime.start_game()
    runtime.update(0.016, RuntimeInput(interact_pressed=True))

    runtime.update(0.016, RuntimeInput(block_pressed=True))

    assert runtime.mode == PresentationMode.INCUBATION
    assert runtime.incubation.stage_index == 1
    assert runtime.incubation.audio_event == "birth_fail"


def test_exploration_movement_advances_player() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    start_x = runtime.exploration.player_x

    runtime.update(0.2, RuntimeInput(move_x=1.0))

    assert runtime.exploration.player_x > start_x
    assert runtime.exploration.camera_x >= 0.0


def test_room_transition_advances_to_next_room() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.exploration.player_x = 1861.0

    runtime.update(0.016, RuntimeInput())

    assert runtime.mode == PresentationMode.EXPLORATION
    assert runtime.exploration.room_id == "ossuary_rise"
    assert runtime.exploration.room_transition > 0.0


def test_gate_blocks_progress_until_room_is_cleared() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.exploration.player_x = 1861.0
    runtime.update(0.016, RuntimeInput())

    runtime.exploration.player_x = 2141.0
    runtime.update(0.016, RuntimeInput())

    assert runtime.exploration.room_id == "ossuary_rise"
    assert runtime.exploration.player_x == 2140.0
    assert runtime.exploration.gate_locked is True
    assert runtime.exploration.gate_feedback > 0.0


def test_sludge_patch_adds_cling_in_exploration() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.exploration.player_x = 250.0
    runtime.exploration.player_y = runtime.current_room().ground_y

    runtime.update(0.1, RuntimeInput(move_x=1.0))

    assert runtime.mode == PresentationMode.EXPLORATION
    assert runtime.exploration.sludge_cling > 0.0


def test_interact_collects_amniotic_gourd_segment() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    segment = runtime.exploration.gourd_segments[0]
    base_capacity = runtime.flow.player.gourd.capacity
    runtime.exploration.player_x = segment.x
    runtime.exploration.player_y = segment.y

    runtime.update(0.016, RuntimeInput(interact_pressed=True))

    assert segment.consumed is True
    assert runtime.flow.player.gourd.capacity > base_capacity
    assert runtime.flow.player.gourd.stored_blood > 0.0


def test_landborne_can_use_gourd_for_healing() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.exploration.player_x = 340.0
    runtime.flow.player.health = 62.0
    runtime.flow.player.gourd.stored_blood = 28.0

    runtime.update(0.016, RuntimeInput(interact_pressed=True))

    assert runtime.flow.player.health > 62.0
    assert runtime.flow.player.gourd.stored_blood < 28.0


def test_sludge_patch_reduces_travel_speed() -> None:
    clear_runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(clear_runtime)
    clear_runtime.exploration.player_x = 340.0
    clear_start_x = clear_runtime.exploration.player_x

    sludge_runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(sludge_runtime)
    sludge_runtime.exploration.player_x = 250.0
    sludge_start_x = sludge_runtime.exploration.player_x

    clear_runtime.update(0.1, RuntimeInput(move_x=1.0))
    sludge_runtime.update(0.1, RuntimeInput(move_x=1.0))

    clear_delta = clear_runtime.exploration.player_x - clear_start_x
    sludge_delta = sludge_runtime.exploration.player_x - sludge_start_x
    assert sludge_delta < clear_delta


def test_spike_contact_damages_and_knocks_back_player() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    starting_health = runtime.flow.player.health
    runtime.exploration.player_x = 710.0
    runtime.exploration.player_y = runtime.current_room().ground_y

    runtime.update(0.016, RuntimeInput())

    assert runtime.mode == PresentationMode.EXPLORATION
    assert runtime.flow.player.health < starting_health
    assert runtime.exploration.damage_flash > 0.0
    assert runtime.exploration.hazard_impact_timer > 0.0
    assert runtime.exploration.player_x < 710.0


def test_encounter_zone_enters_eyecontact_before_battle_window() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.exploration.player_x = 1360.0

    runtime.update(0.016, RuntimeInput())

    assert runtime.mode == PresentationMode.BATTLE
    assert runtime.flow.mode == GameplayMode.COLLISION_RACE
    assert runtime.battle.phase == BattlePhase.EYECONTACT
    assert runtime.battle.sound_cue_pending is True
    assert runtime.battle.tutorial_active is True


def test_first_eyecontact_can_advance_combat_tutorial() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.exploration.player_x = 1360.0

    runtime.update(0.016, RuntimeInput())
    for _ in range(len(runtime.battle.tutorial_pages)):
        runtime.update(0.016, RuntimeInput(confirm_pressed=True))

    assert runtime.battle.tutorial_active is False
    assert runtime.tutorial_completed is True


def test_eyecontact_advances_into_battle_window() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.tutorial_completed = True
    runtime.exploration.player_x = 1360.0

    _advance_first_encounter_to_window(runtime, move_y=1.0)

    assert runtime.mode == PresentationMode.BATTLE
    assert runtime.battle.phase in {BattlePhase.WINDOW, BattlePhase.RESOLVE}


def test_eyecontact_builds_anticipation_before_intro() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.tutorial_completed = True
    runtime.exploration.player_x = 1360.0

    runtime.update(0.016, RuntimeInput())
    runtime.update(0.34, RuntimeInput())
    runtime.update(0.08, RuntimeInput())

    assert runtime.battle.phase == BattlePhase.EYECONTACT
    assert runtime.battle.eyecontact_hold > 0.0
    assert runtime.battle.line_of_sight_strength >= 1.0


def test_window_sets_explicit_telegraph_poses() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.tutorial_completed = True
    runtime.exploration.player_x = 1360.0

    _advance_first_encounter_to_window(runtime, move_y=-1.0)

    assert runtime.battle.phase == BattlePhase.WINDOW
    assert runtime.battle.enemy_pose.startswith(("strike", "brace", "coil", "feint"))
    assert runtime.battle.player_pose in {"guard_low", "ready", "lift_high"}
    assert runtime.battle.telegraph_strength > 0.0
    assert runtime.battle.camera_pan != 0.0


def test_window_exposes_eased_progress_and_time_dilation() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.tutorial_completed = True
    runtime.exploration.player_x = 1360.0

    _advance_first_encounter_to_window(runtime, move_y=-1.0)

    assert runtime.battle.phase == BattlePhase.WINDOW
    assert 0.0 < runtime.battle.window_progress < 1.0
    assert runtime.battle.time_dilation > 1.0
    assert runtime.battle.window_duration == 1.32
    assert runtime.battle.cadence_label == "Opening lesson"


def test_cadence_curve_grows_space_and_tightens_timing_toward_boss() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.tutorial_completed = True

    runtime._start_battle("scarab_child_acolyte")
    opening_window = runtime.battle.window_duration
    opening_center = runtime.battle.timing_window_half
    opening_span = runtime.battle.arena_span

    runtime._start_battle("lattice_ward")
    middle_window = runtime.battle.window_duration
    middle_center = runtime.battle.timing_window_half
    middle_span = runtime.battle.arena_span

    runtime._start_battle("lahgroid_hierophant")
    boss_window = runtime.battle.window_duration
    boss_center = runtime.battle.timing_window_half
    boss_span = runtime.battle.arena_span

    assert opening_window > middle_window > boss_window
    assert opening_center > middle_center > boss_center
    assert opening_span < middle_span < boss_span


def test_battle_movement_advances_ishtasha_inside_arena() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.tutorial_completed = True
    runtime.exploration.player_x = 1360.0

    runtime.update(0.016, RuntimeInput())
    runtime.update(0.3, RuntimeInput(move_y=1.0))
    runtime.update(0.3, RuntimeInput(move_y=1.0))
    runtime.update(0.2, RuntimeInput(move_y=1.0))

    start_battle_x = runtime.battle.player_battle_x
    runtime.update(0.2, RuntimeInput(move_x=1.0, move_y=1.0))

    assert runtime.mode == PresentationMode.BATTLE
    assert runtime.battle.phase in {BattlePhase.INTRO, BattlePhase.WINDOW}
    assert runtime.battle.player_battle_x > start_battle_x
    assert runtime.battle.proximity >= 0.0


def test_perfect_block_executes_parry() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.tutorial_completed = True
    runtime.exploration.player_x = 1360.0

    _advance_first_encounter_to_window(runtime, move_y=1.0)
    runtime.perform_action("block", timing=0.5)

    assert runtime.battle.phase == BattlePhase.RESOLVE
    assert runtime.battle.resolution_action == "parry"
    assert runtime.battle.resolution_lane == "foreground"
    assert runtime.battle.resolution_quality == "success"
    assert runtime.battle.resolution_timing_bucket == "center"
    assert runtime.battle.player_pose == "surge_low"


def test_boss_clear_flows_into_up_denouement_then_low_epilogue() -> None:
    runtime = MetroidvaniaRuntime(GameplayPrototypeController(create_starting_player("Ishtasha")))
    _advance_land_birth(runtime)
    runtime.tutorial_completed = True
    runtime._start_battle("lahgroid_hierophant")
    runtime.battle.lane_bias = "background"
    assert runtime.flow.battle_state is not None
    runtime.flow.battle_state.enemy_health = 4.0

    runtime.perform_action("light_attack", timing=0.5)

    assert runtime.mode == PresentationMode.UP_DIALOGUE
    assert runtime.flow.mode == GameplayMode.UP_DIALOGUE

    runtime.update(0.016, RuntimeInput(interact_pressed=True))
    assert runtime.mode == PresentationMode.UP_DIALOGUE
    runtime.update(0.016, RuntimeInput(interact_pressed=True))

    assert runtime.mode == PresentationMode.LOW_PUZZLE
    assert runtime.flow.mode == GameplayMode.LOW_PUZZLE

    runtime.update(0.016, RuntimeInput(dash_pressed=True))
    runtime.update(0.016, RuntimeInput(block_pressed=True))
    runtime.update(0.016, RuntimeInput(interact_pressed=True))

    assert runtime.mode == PresentationMode.EXPLORATION
    assert runtime.exploration.room_id == "sunken_sanctum"
    assert runtime.flow.current_zone == "sunken_sanctum"