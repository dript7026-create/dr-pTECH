import pandas as pd

from football_predictor.entity_state import build_match_entity_states
from football_predictor.regulated_session import build_regulated_session_hooks


def test_regulated_session_hooks_expose_transparent_channels_and_consent_gate():
    row = pd.Series(
        {
            "confidence": 0.61,
            "uncertainty": 0.39,
            "home_goals_for_form": 1.8,
            "rest_days_diff": 2.0,
            "lineup_approval_ratio": 0.75,
        }
    )
    hooks = build_regulated_session_hooks(
        row,
        entity_effects={"discipline_swing": 0.04},
        trajectories=[{"minute": 17.0}, {"minute": 68.0}],
        incidents=[],
        entity_states=build_match_entity_states(pd.Series({"date": "2026-03-20", "home_team": "TeamA", "away_team": "TeamB"})),
    )
    assert hooks["mode"] == "regulated_interactive_scaffold"
    assert hooks["consent_gate"]["live_activation_allowed"] is False
    assert hooks["simulation_channels"][1]["visible_to_user"] is True
    assert hooks["transparent_channel_switching_required"] is True
    assert hooks["human_presence_prompts"]
    assert hooks["player_consent_registry"]["home"]["required_count"] == 11
