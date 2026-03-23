from football_predictor.avatar_profile import (
    HEAD_SIZE_M,
    MAX_BODY_FAT,
    MAX_HEIGHT_M,
    MAX_WEIGHT_KG,
    MIN_BODY_FAT,
    MIN_HEIGHT_M,
    MIN_WEIGHT_KG,
    build_avatar_profile,
)


def test_avatar_profile_respects_requested_body_ranges():
    profile = build_avatar_profile("TeamA", role="attacker", player_quality=0.8, match_date="2026-03-15")
    assert profile.head_size_m == HEAD_SIZE_M
    assert MIN_HEIGHT_M <= profile.height_m <= MAX_HEIGHT_M
    assert MIN_WEIGHT_KG <= profile.weight_kg <= MAX_WEIGHT_KG
    assert MIN_BODY_FAT <= profile.body_fat_pct <= MAX_BODY_FAT
    assert 0.35 <= profile.muscle_ratio <= 0.72
    assert 0.1 <= profile.bone_ratio <= 0.22


def test_avatar_profile_uses_supplied_physical_columns_when_present():
    import pandas as pd

    players = pd.DataFrame(
        [
            {
                "team": "TeamA",
                "minutes": 900,
                "goals": 5,
                "assists": 2,
                "shots_on_target": 14,
                "key_passes": 9,
                "tackles": 3,
                "interceptions": 1,
                "saves": 0,
                "height_in": 78,
                "weight_lb": 220,
                "body_fat_pct": 12,
            }
        ]
    )
    profile = build_avatar_profile("TeamA", role="keeper", players_df=players, match_date="2026-03-15")
    assert round(profile.height_m, 4) == round(78 * 0.0254, 4)
    assert round(profile.weight_kg, 4) == round(220 * 0.45359237, 4)
    assert round(profile.body_fat_pct, 4) == 0.12