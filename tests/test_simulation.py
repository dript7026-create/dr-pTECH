import pandas as pd

from football_predictor.simulation import SimulationConfig, simulate_match, simulate_prediction_frame
from football_predictor.sport_rules import get_role_sequence


def test_simulate_match_returns_probabilities_and_trajectories():
    row = pd.Series(
        {
            "sport": "football",
            "date": "2026-03-20",
            "home_team": "TeamA",
            "away_team": "TeamB",
            "prob_away_win": 0.24,
            "prob_draw": 0.28,
            "prob_home_win": 0.48,
            "home_goals_for_form": 1.8,
            "away_goals_for_form": 1.2,
            "form_diff": 0.6,
            "weather_severity": 0.05,
        }
    )
    result = simulate_match(row, config=SimulationConfig(simulation_count=250), random_state=7)
    assert result["simulation_count"] == 250
    assert result["simulated_home_win_rate"] >= 0.0
    assert result["simulated_draw_rate"] >= 0.0
    assert result["simulated_away_win_rate"] >= 0.0
    assert result["event_trajectories"] is not None
    assert result["entity_states"]["home"]["team"] == "TeamA"
    assert result["artisapien_hooks"]["enabled"] is False
    assert result["regulated_session"]["mode"] == "regulated_interactive_scaffold"
    assert result["challenge_cues"]["exact_percentages_hidden"] is True
    assert "attention_focus_label" in result["challenge_cues"]
    assert "reflex_window_label" in result["challenge_cues"]
    assert result["spectator_cues"]["mode"] == "attention_reactive_broadcast"
    assert result["event_trajectories"][0]["phase_state"]
    assert result["event_trajectories"][0]["spectator_prompt"]


def test_basketball_simulation_resolves_ties_out_of_draw_bucket():
    row = pd.Series(
        {
            "sport": "basketball",
            "date": "2026-03-20",
            "home_team": "TeamA",
            "away_team": "TeamB",
            "prob_away_win": 0.48,
            "prob_draw": 0.0,
            "prob_home_win": 0.52,
            "home_goals_for_form": 110.0,
            "away_goals_for_form": 108.0,
            "form_diff": 0.2,
            "weather_severity": 0.0,
        }
    )
    result = simulate_match(row, config=SimulationConfig(simulation_count=200), random_state=11)
    assert result["sport"] == "basketball"
    assert result["simulated_draw_rate"] == 0.0


def test_simulate_match_exposes_ruleset_and_behavior_catalog():
    row = pd.Series(
        {
            "sport": "baseball",
            "date": "2026-03-20",
            "home_team": "TeamA",
            "away_team": "TeamB",
            "prob_away_win": 0.46,
            "prob_draw": 0.0,
            "prob_home_win": 0.54,
            "home_goals_for_form": 4.8,
            "away_goals_for_form": 4.2,
            "weather_severity": 0.1,
            "media_buzz_home": 0.25,
        }
    )
    result = simulate_match(row, config=SimulationConfig(simulation_count=120), random_state=5)
    assert result["sport_ruleset"]["phase_states"]
    assert "hesitation" in result["sport_ruleset"]["mistake_states"]
    assert result["behavior_catalog"]
    assert len(result["entity_states"]["home"]["roster"]) == len(get_role_sequence("baseball"))
    assert "decision_noise" in result["entity_states"]["home"]["roster"][0]
    assert result["event_trajectories"][0]["pressure_window"] in {"wide_window", "standard_window", "tight_window"}


def test_simulate_prediction_frame_returns_one_payload_per_row():
    predictions = pd.DataFrame(
        [
            {
                "sport": "football",
                "date": "2026-03-20",
                "home_team": "TeamA",
                "away_team": "TeamB",
                "prob_away_win": 0.24,
                "prob_draw": 0.28,
                "prob_home_win": 0.48,
                "home_goals_for_form": 1.8,
                "away_goals_for_form": 1.2,
                "form_diff": 0.6,
                "weather_severity": 0.05,
            },
            {
                "sport": "basketball",
                "date": "2026-03-21",
                "home_team": "TeamC",
                "away_team": "TeamD",
                "prob_away_win": 0.45,
                "prob_draw": 0.0,
                "prob_home_win": 0.55,
                "home_goals_for_form": 108.0,
                "away_goals_for_form": 104.0,
                "form_diff": 0.2,
                "weather_severity": 0.0,
            },
        ]
    )

    results = simulate_prediction_frame(predictions, config=SimulationConfig(simulation_count=80), random_state=13)

    assert len(results) == 2
    assert results[0]["home_team"] == "TeamA"
    assert results[1]["sport"] == "basketball"
    assert all(result["simulation_count"] == 80 for result in results)