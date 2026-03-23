import pandas as pd

from football_predictor.player_stats import aggregate_team_player_stats, build_fixture_player_quality_frame


def test_aggregate_team_player_stats_returns_normalized_profiles():
    players = pd.DataFrame(
        [
            {"team": "TeamA", "minutes": 900, "goals": 8, "assists": 3, "shots_on_target": 18, "key_passes": 12, "tackles": 9, "interceptions": 4, "saves": 0},
            {"team": "TeamA", "minutes": 850, "goals": 2, "assists": 6, "shots_on_target": 11, "key_passes": 21, "tackles": 12, "interceptions": 8, "saves": 0},
            {"team": "TeamB", "minutes": 900, "goals": 1, "assists": 1, "shots_on_target": 4, "key_passes": 6, "tackles": 15, "interceptions": 11, "saves": 0},
            {"team": "TeamB", "minutes": 900, "goals": 0, "assists": 0, "shots_on_target": 1, "key_passes": 2, "tackles": 6, "interceptions": 5, "saves": 10},
        ]
    )
    profiles = aggregate_team_player_stats(players)
    assert set(["team", "player_quality", "attack_quality", "defense_quality", "stamina_quality"]).issubset(profiles.columns)
    assert len(profiles) == 2


def test_build_fixture_player_quality_frame_maps_fixture_teams():
    players = pd.DataFrame(
        [
            {"team": "TeamA", "minutes": 900, "goals": 8, "assists": 3, "shots_on_target": 18, "key_passes": 12, "tackles": 9, "interceptions": 4, "saves": 0},
            {"team": "TeamD", "minutes": 900, "goals": 1, "assists": 1, "shots_on_target": 5, "key_passes": 5, "tackles": 13, "interceptions": 10, "saves": 0},
        ]
    )
    fixtures = pd.DataFrame([{"home_team": "TeamA", "away_team": "TeamD", "date": "2025-08-28"}])
    qualities = build_fixture_player_quality_frame(fixtures, players)
    assert len(qualities) == 1
    assert "player_quality_diff" in qualities.columns