import pandas as pd

from football_predictor.entity_state import build_match_entity_states, summarize_match_entity_effects
from football_predictor.sport_rules import get_role_sequence


def test_build_match_entity_states_returns_rosters_and_team_state():
    row = pd.Series(
        {
            "date": "2026-03-20",
            "home_team": "TeamA",
            "away_team": "TeamB",
            "prob_home_win": 0.5,
            "prob_draw": 0.28,
            "prob_away_win": 0.22,
            "home_player_quality": 0.4,
            "away_player_quality": -0.2,
            "weather_severity": 0.12,
            "media_sentiment_home": 0.2,
            "media_sentiment_away": -0.1,
            "media_buzz_home": 0.05,
            "media_buzz_away": 0.12,
            "home_goals_for_form": 1.8,
            "away_goals_for_form": 1.1,
            "form_diff": 0.5,
        }
    )
    states = build_match_entity_states(row)
    assert len(states["home"].roster) == 11
    assert len(states["away"].roster) == 11
    assert 0.0 <= states["home"].sodium_state <= 1.0
    assert 0.0 <= states["away"].coach_motivation <= 1.0
    assert "delta_magnitude" in states["home"].delta_signature
    assert states["home"].influence_network


def test_entity_effects_stay_bounded():
    row = pd.Series(
        {
            "date": "2026-03-20",
            "home_team": "TeamA",
            "away_team": "TeamB",
            "prob_home_win": 0.45,
            "prob_draw": 0.3,
            "prob_away_win": 0.25,
            "home_player_quality": 0.1,
            "away_player_quality": 0.0,
            "weather_severity": 0.05,
        }
    )
    effects = summarize_match_entity_effects(build_match_entity_states(row))
    assert -0.45 <= effects["home_attack_delta"] <= 0.55
    assert -0.45 <= effects["away_attack_delta"] <= 0.55
    assert -0.15 <= effects["salt_variance"] <= 0.12


def test_delta_signatures_are_non_identifying_but_traceable():
    row = pd.Series(
        {
            "date": "2026-03-20",
            "home_team": "TeamA",
            "away_team": "TeamB",
            "prob_home_win": 0.52,
            "prob_draw": 0.24,
            "prob_away_win": 0.24,
            "home_player_quality": 0.5,
            "away_player_quality": -0.1,
            "home_goals_for_form": 2.0,
            "weather_severity": 0.08,
            "media_sentiment_home": 0.2,
        }
    )
    home_state = build_match_entity_states(row)["home"]
    assert "quality_signal" in home_state.source_stat_signature
    assert "preparedness_signal" in home_state.simulated_state_signature
    assert "quality_signal_to_preparedness_signal" in home_state.delta_signature
    assert 0.0 <= home_state.delta_signature["delta_magnitude"] <= 1.0


def test_build_match_entity_states_supports_multisport_roster_sizes_and_impairments():
    row = pd.Series(
        {
            "sport": "basketball",
            "date": "2026-03-20",
            "home_team": "TeamA",
            "away_team": "TeamB",
            "prob_home_win": 0.54,
            "prob_draw": 0.0,
            "prob_away_win": 0.46,
            "home_player_quality": 0.3,
            "away_player_quality": 0.1,
            "weather_severity": 0.06,
            "media_buzz_home": 0.22,
        }
    )
    states = build_match_entity_states(row)
    assert states["home"].sport == "basketball"
    assert len(states["home"].roster) == len(get_role_sequence("basketball"))
    player = states["home"].roster[0]
    assert 0.0 <= player.confusion <= 1.0
    assert 0.0 <= player.vision_disruption <= 1.0
    assert 0.0 <= player.locomotion_integrity <= 1.0
    assert 0.0 <= states["home"].decision_cohesion <= 1.0