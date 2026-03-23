import pandas as pd

from football_predictor.live_data import (
    TheSportsDBBaseballSource,
    TheSportsDBBasketballSource,
    TheSportsDBSource,
    merge_match_frames,
    upsert_matches,
    read_warehouse_matches,
)


def test_thesportsdb_normalization_and_warehouse_roundtrip(tmp_path):
    source = TheSportsDBSource(api_key="test")
    frame = source._normalize_events(
        [
            {
                "idEvent": "evt-1",
                "strTimestamp": "2026-03-20T15:00:00+00:00",
                "strStatus": "Not Started",
                "idLeague": "4328",
                "strLeague": "English Premier League",
                "strSeason": "2025-2026",
                "strHomeTeam": "Arsenal",
                "strAwayTeam": "Chelsea",
                "idHomeTeam": "133604",
                "idAwayTeam": "133610",
                "strVenue": "Emirates Stadium",
                "strLatitude": "51.5549",
                "strLongitude": "-0.1084",
            }
        ]
    )
    assert frame.loc[0, "home_team"] == "Arsenal"
    assert frame.loc[0, "status"] == "NOT STARTED"

    db_path = tmp_path / "warehouse.sqlite"
    inserted = upsert_matches(str(db_path), frame)
    restored = read_warehouse_matches(str(db_path))

    assert inserted == 1
    assert len(restored) == 1
    assert restored.loc[0, "venue"] == "Emirates Stadium"


def test_merge_match_frames_deduplicates_by_source_and_external_id():
    frame_a = pd.DataFrame(
        [
            {
                "source": "football-data.org",
                "external_id": "100",
                "date": "2026-03-20",
                "status": "SCHEDULED",
                "competition_code": "PL",
                "competition_name": "Premier League",
                "season": "2025",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "home_team_id": "1",
                "away_team_id": "2",
                "home_score": None,
                "away_score": None,
                "venue": "Emirates",
                "latitude": None,
                "longitude": None,
            }
        ]
    )
    frame_b = frame_a.copy()
    frame_b.loc[0, "venue"] = "Emirates Stadium"
    merged = merge_match_frames([frame_a, frame_b])
    assert len(merged) == 1
    assert merged.loc[0, "venue"] == "Emirates Stadium"


def test_multisport_thesportsdb_adapters_mark_sport_column():
    baseball = TheSportsDBBaseballSource(api_key="test")
    baseball_frame = baseball._normalize_events(
        [
            {
                "idEvent": "mlb-1",
                "dateEvent": "2026-04-01",
                "strStatus": "Not Started",
                "idLeague": "4424",
                "strLeague": "MLB",
                "strSeason": "2026",
                "strHomeTeam": "Yankees",
                "strAwayTeam": "Red Sox",
            }
        ]
    )
    basketball = TheSportsDBBasketballSource(api_key="test")
    basketball_frame = basketball._normalize_events(
        [
            {
                "idEvent": "nba-1",
                "dateEvent": "2026-04-01",
                "strStatus": "Not Started",
                "idLeague": "4387",
                "strLeague": "NBA",
                "strSeason": "2025-2026",
                "strHomeTeam": "Celtics",
                "strAwayTeam": "Knicks",
            }
        ]
    )
    assert baseball_frame.loc[0, "sport"] == "baseball"
    assert basketball_frame.loc[0, "sport"] == "basketball"


def test_warehouse_roundtrip_preserves_sport_column(tmp_path):
    frame = pd.DataFrame(
        [
            {
                "sport": "basketball",
                "source": "thesportsdb:basketball",
                "external_id": "nba-1",
                "date": "2026-04-01T19:30:00+00:00",
                "status": "SCHEDULED",
                "competition_code": "4387",
                "competition_name": "NBA",
                "season": "2025-2026",
                "home_team": "Celtics",
                "away_team": "Knicks",
                "home_team_id": "1",
                "away_team_id": "2",
                "home_score": None,
                "away_score": None,
                "venue": "Garden",
                "latitude": None,
                "longitude": None,
            }
        ]
    )
    db_path = tmp_path / "warehouse.sqlite"
    upsert_matches(str(db_path), frame)
    restored = read_warehouse_matches(str(db_path), sport="basketball")
    assert len(restored) == 1
    assert restored.loc[0, "sport"] == "basketball"