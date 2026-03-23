import pandas as pd
from PySide6 import QtWidgets

from football_predictor.playback import PlaybackWindow, build_playback_frames
from football_predictor.simulation import with_probability_override


def test_probability_override_preserves_normalization_and_quality_fields():
    row = pd.Series(
        {
            "prob_away_win": 0.2,
            "prob_draw": 0.3,
            "prob_home_win": 0.5,
        }
    )
    updated = with_probability_override(
        row,
        home_probability=0.65,
        draw_probability=0.2,
        away_probability=0.15,
        user_weight=0.75,
        home_player_quality=0.6,
        away_player_quality=-0.3,
    )
    total = updated["prob_away_win"] + updated["prob_draw"] + updated["prob_home_win"]
    assert round(float(total), 8) == 1.0
    assert round(float(updated["player_quality_diff"]), 8) == 0.9


def test_build_playback_frames_generates_score_progression():
    simulation_result = {
        "sport": "football",
        "event_trajectories": [
            {
                "team": "home",
                "minute": 12.0,
                "phase_state": "finishing_sequence",
                "primary_action": "shoot",
                "pressure_window": "tight_window",
                "attention_focus": "final_third_press",
                "spectator_prompt": "Watch the last line and react to the strike lane.",
                "focus_radius": 8.0,
                "hotspot": {"x": 105.0, "y": 34.0, "z": 1.0},
                "reflex_intensity": 0.78,
                "trajectory": [
                    {"t": 0.0, "x": 80.0, "y": 30.0, "z": 0.18},
                    {"t": 0.8, "x": 105.0, "y": 34.0, "z": 1.0},
                ],
            }
        ]
    }
    frames = build_playback_frames(simulation_result, match_seconds=20.0)
    assert len(frames) == 2
    assert frames[-1]["home_score"] == 1
    assert frames[-1]["away_score"] == 0
    assert frames[-1]["sport"] == "football"
    assert frames[-1]["pressure_window"] == "tight_window"
    assert frames[-1]["primary_action"] == "shoot"


def test_build_playback_frames_supports_basketball_surface():
    simulation_result = {
        "sport": "basketball",
        "event_trajectories": [
            {
                "team": "home",
                "minute": 8.0,
                "trajectory": [
                    {"t": 0.0, "x": 70.0, "y": 24.0, "z": 2.0},
                    {"t": 0.6, "x": 88.0, "y": 25.0, "z": 3.05},
                ],
            }
        ],
    }
    frames = build_playback_frames(simulation_result, match_seconds=18.0)
    assert frames[-1]["sport"] == "basketball"
    assert frames[-1]["attacker"][0] < frames[-1]["keeper"][0]


def test_build_playback_frames_supports_baseball_surface():
    simulation_result = {
        "sport": "baseball",
        "event_trajectories": [
            {
                "team": "away",
                "minute": 14.0,
                "trajectory": [
                    {"t": 0.0, "x": 14.0, "y": 14.0, "z": 1.0},
                    {"t": 1.2, "x": 80.0, "y": 85.0, "z": 4.2},
                ],
            }
        ],
    }
    frames = build_playback_frames(simulation_result, match_seconds=22.0)
    assert frames[-1]["sport"] == "baseball"
    assert frames[-1]["home_score"] == 0
    assert frames[-1]["away_score"] == 1


def test_saved_session_state_shape_is_stable():
    state = {
        "challenge_mode_enabled": True,
        "fixture_index": 0,
        "user_weight": 0.5,
        "home_quality": 0.2,
        "away_quality": -0.1,
        "home_probability": 0.55,
        "draw_probability": 0.25,
        "away_probability": 0.2,
        "match_seconds": 24.0,
        "current_time": 3.2,
    }
    assert state["challenge_mode_enabled"] is True
    assert sorted(state.keys()) == [
        "away_probability",
        "away_quality",
        "challenge_mode_enabled",
        "current_time",
        "draw_probability",
        "fixture_index",
        "home_probability",
        "home_quality",
        "match_seconds",
        "user_weight",
    ]


def test_playback_window_interaction_updates_timeline_labels():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    report = {
        "predictions": [
            {
                "sport": "basketball",
                "date": "2026-04-01",
                "home_team": "Home",
                "away_team": "Away",
                "prob_home_win": 0.58,
                "prob_draw": 0.0,
                "prob_away_win": 0.42,
                "prediction": "Home Win",
                "home_player_quality": 0.2,
                "away_player_quality": -0.1,
            }
        ],
        "simulations": [
            {
                "sport": "basketball",
                "home_team": "Home",
                "away_team": "Away",
                "match_date": "2026-04-01",
                "expected_goals_home": 2.0,
                "expected_goals_away": 1.0,
                "simulation_count": 10,
                "simulated_home_win_rate": 0.6,
                "simulated_draw_rate": 0.0,
                "simulated_away_win_rate": 0.4,
                "mean_home_goals": 2.0,
                "mean_away_goals": 1.0,
                "most_likely_score": {"home": 1, "away": 0},
                "entity_effects": {},
                "entity_states": {"home": {"team": "Home"}, "away": {"team": "Away"}},
                "match_incidents": [],
                "artisapien_hooks": {"enabled": False},
                "regulated_session": {"mode": "regulated_interactive_scaffold"},
                "challenge_cues": {
                    "visible_label": "Readable Lean",
                    "pressure_label": "Stable Pressure",
                    "timing_window_label": "Measured Window",
                    "rhythm_label": "Set Rhythm",
                    "attention_focus_label": "Two-Sided Pressure",
                    "reflex_window_label": "Active Reflex",
                    "spectator_prompt": "Track both teams and wait for the weak-side break.",
                    "focus_target": "paint_to_perimeter",
                },
                "event_trajectories": [
                    {
                        "team": "home",
                        "minute": 8.0,
                        "phase_state": "finishing_sequence",
                        "primary_action": "catch_and_shoot",
                        "pressure_window": "tight_window",
                        "attention_focus": "rim_pressure",
                        "spectator_prompt": "Track the weak-side tag and the catch window.",
                        "focus_radius": 7.0,
                        "hotspot": {"x": 88.0, "y": 25.0, "z": 3.05},
                        "reflex_intensity": 0.72,
                        "trajectory": [
                            {"t": 0.0, "x": 70.0, "y": 24.0, "z": 2.0},
                            {"t": 0.6, "x": 88.0, "y": 25.0, "z": 3.05},
                        ],
                    }
                ],
            }
        ],
    }
    window = PlaybackWindow(report=report)
    window._fixture_changed(0)
    window._seek(1000)
    assert window.fixture_status.text().startswith("Basketball | Home vs Away")
    assert window.score_label.text() == "Score 1-0"
    assert window.playhead_label.text().endswith("/ 00:24")
    assert "Focus " in window.cue_banner.text()
    assert "Window " in window.cue_banner.text()
    assert "Reflex " in window.cue_banner.text()
    window._step_frame(-1)
    assert window.score_label.text() == "Score 0-0"
    window.close()