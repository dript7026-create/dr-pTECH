import pandas as pd

from football_predictor.challenge_mode import build_challenge_cue_profile


def test_challenge_cue_profile_hides_exact_percentages_but_keeps_cues():
    row = pd.Series(
        {
            "confidence": 0.64,
            "uncertainty": 0.36,
            "entropy": 0.41,
        }
    )
    cues = build_challenge_cue_profile(row)
    assert cues["challenge_mode_enabled"] is True
    assert cues["exact_percentages_hidden"] is True
    assert cues["visible_label"] in {"Foggy Read", "Soft Lean", "Readable Lean", "Strong Tell", "Heavy Tell"}
    assert cues["timing_window_label"] in {"Wide Window", "Standard Window", "Tight Window"}
