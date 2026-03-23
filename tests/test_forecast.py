import pandas as pd

from football_predictor.data_loader import load_csv, prepare_training_frame
from football_predictor.forecast import apply_context_adjustments, predict_upcoming_fixtures
from football_predictor.media_signals import MediaArticle, build_fixture_media_frame
from football_predictor.model import train_model


def test_context_adjustments_shift_probabilities_but_preserve_normalization():
    predictions = pd.DataFrame(
        [
            {
                "date": "2026-03-20",
                "home_team": "TeamA",
                "away_team": "TeamB",
                "prob_away_win": 0.25,
                "prob_draw": 0.30,
                "prob_home_win": 0.45,
            }
        ]
    )
    media = pd.DataFrame(
        [
            {
                "fixture_key": "teama::teamb::2026-03-20",
                "media_sentiment_home": 2.0,
                "media_sentiment_away": -1.0,
                "media_buzz_home": 1.0,
                "media_buzz_away": 0.2,
                "media_signal_gap": 3.28,
            }
        ]
    )
    weather = pd.DataFrame(
        [
            {
                "fixture_key": "teama::teamb::2026-03-20",
                "weather_temperature_c": 9.0,
                "weather_wind_speed": 4.0,
                "weather_precipitation_mm": 0.0,
                "weather_severity": 0.0,
                "weather_summary": "clear sky",
            }
        ]
    )
    adjusted = apply_context_adjustments(predictions, media_df=media, weather_df=weather)
    assert round(float(adjusted.loc[0, ["prob_away_win", "prob_draw", "prob_home_win"]].sum()), 8) == 1.0
    assert adjusted.loc[0, "prob_home_win"] > 0.45


def test_predict_upcoming_fixtures_with_media_context():
    raw = load_csv("football_predictor/sample_data.csv")
    train_df = prepare_training_frame(raw)
    bundle, _ = train_model(train_df)
    fixtures = pd.DataFrame(
        [
            {
                "source": "manual",
                "external_id": "fixture-1",
                "date": "2025-08-28",
                "status": "SCHEDULED",
                "competition_code": "TEST",
                "competition_name": "Test League",
                "season": "2025",
                "home_team": "TeamA",
                "away_team": "TeamD",
                "venue": "Test Ground",
                "latitude": None,
                "longitude": None,
            }
        ]
    )
    articles = [MediaArticle(title="TeamA injury boost and sharp return", summary="TeamA look confident.", link="")]
    media = build_fixture_media_frame(fixtures, articles)
    predictions = predict_upcoming_fixtures(bundle, raw, fixtures, media_df=media)
    assert len(predictions) == 1
    assert predictions.loc[0, "prediction"] in {"Home Win", "Draw", "Away Win"}
    assert predictions.loc[0, "competition_name"] == "Test League"


def test_basketball_context_adjustments_keep_draw_at_zero():
    predictions = pd.DataFrame(
        [
            {
                "sport": "basketball",
                "date": "2026-03-20",
                "home_team": "TeamA",
                "away_team": "TeamB",
                "prob_away_win": 0.35,
                "prob_draw": 0.0,
                "prob_home_win": 0.65,
            }
        ]
    )
    adjusted = apply_context_adjustments(predictions, sport="basketball")
    assert adjusted.loc[0, "prob_draw"] == 0.0
    assert round(float(adjusted.loc[0, ["prob_away_win", "prob_home_win"]].sum()), 8) == 1.0
    assert adjusted.loc[0, "prediction"] in {"Home Win", "Away Win"}