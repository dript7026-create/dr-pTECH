from pathlib import Path

import numpy as np

import pandas as pd

from football_predictor.data_loader import FEATURE_COLUMNS, build_fixture_feature_frame, build_fixture_feature_row, load_csv, prepare_training_frame
from football_predictor.model import (
    evolutionary_search_and_train,
    export_model,
    load_model,
    predict_matches,
    train_model,
)


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH = ROOT / "football_predictor" / "sample_data.csv"
MODEL_PATH = ROOT / ".pytest_cache" / "dirkodds_test_bundle.joblib"


def test_prepare_training_frame_generates_leak_free_features():
    raw_df = load_csv(str(SAMPLE_PATH))
    train_df = prepare_training_frame(raw_df)

    assert "outcome" in train_df.columns
    assert set(FEATURE_COLUMNS).issubset(train_df.columns)
    assert train_df.loc[0, "home_form"] == 0.0
    assert train_df.loc[0, "away_form"] == 0.0
    assert train_df[FEATURE_COLUMNS].isna().sum().sum() == 0


def test_train_predict_and_reload_bundle_roundtrip():
    raw_df = load_csv(str(SAMPLE_PATH))
    train_df = prepare_training_frame(raw_df)
    bundle, metrics = train_model(train_df)

    assert bundle.training_rows == len(train_df)
    assert bundle.sport == "football"
    assert metrics["accuracy"] >= 0.0
    assert metrics["log_loss"] >= 0.0

    predictions = predict_matches(bundle, train_df.tail(4))
    assert {
        "prob_away_win",
        "prob_draw",
        "prob_home_win",
        "prediction",
        "confidence",
        "uncertainty",
        "entropy",
    }.issubset(predictions.columns)
    np.testing.assert_allclose(
        predictions[["prob_away_win", "prob_draw", "prob_home_win"]].sum(axis=1).to_numpy(),
        np.ones(len(predictions)),
        atol=1e-6,
    )

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    export_model(bundle, str(MODEL_PATH))
    loaded_bundle = load_model(str(MODEL_PATH))
    loaded_predictions = predict_matches(loaded_bundle, train_df.tail(2))
    assert len(loaded_predictions) == 2


def test_build_fixture_feature_row_for_upcoming_match():
    raw_df = load_csv(str(SAMPLE_PATH))
    fixture_df = build_fixture_feature_row(raw_df, "TeamA", "TeamD", match_date="2025-08-27")

    assert len(fixture_df) == 1
    assert fixture_df.loc[0, "home_team"] == "TeamA"
    assert fixture_df.loc[0, "away_team"] == "TeamD"
    assert set(FEATURE_COLUMNS).issubset(fixture_df.columns)
    assert "outcome" not in fixture_df.columns


def test_build_fixture_feature_frame_matches_single_row_helper():
    raw_df = load_csv(str(SAMPLE_PATH))
    fixtures = pd.DataFrame(
        [
            {"home_team": "TeamA", "away_team": "TeamD", "date": "2025-08-27"},
            {"home_team": "TeamB", "away_team": "TeamC", "date": "2025-08-28"},
        ]
    )

    bulk_df = build_fixture_feature_frame(raw_df, fixtures)
    single_rows = [
        build_fixture_feature_row(raw_df, row["home_team"], row["away_team"], match_date=row["date"]).iloc[0].to_dict()
        for _, row in fixtures.iterrows()
    ]
    single_df = pd.DataFrame(single_rows)

    pd.testing.assert_frame_equal(bulk_df.reset_index(drop=True), single_df.reset_index(drop=True), check_like=False)


def test_evolutionary_search_training_smoke():
    raw_df = load_csv(str(SAMPLE_PATH))
    train_df = prepare_training_frame(raw_df)
    bundle, info = evolutionary_search_and_train(train_df, ngen=1, pop_size=4)

    assert bundle.model_name == "evolved_random_forest"
    assert "best_params" in info
    assert "metrics" in info


def test_basketball_training_uses_no_draw_probability_path():
    raw_df = load_csv(
        str(SAMPLE_PATH),
        sport="basketball",
    )
    raw_df["home_score"] = [102 + (index % 5) if index % 2 == 0 else 97 + (index % 4) for index in range(len(raw_df))]
    raw_df["away_score"] = [96 + (index % 4) if index % 2 == 0 else 104 + (index % 5) for index in range(len(raw_df))]
    train_df = prepare_training_frame(raw_df, sport="basketball")
    bundle, _ = train_model(train_df, sport="basketball")

    predictions = predict_matches(bundle, train_df.tail(3), sport="basketball")
    assert bundle.sport == "basketball"
    assert set(train_df["outcome"].unique()).issubset({0, 2})
    np.testing.assert_allclose(predictions["prob_draw"].to_numpy(), np.zeros(len(predictions)), atol=1e-9)
    np.testing.assert_allclose(
        predictions[["prob_away_win", "prob_home_win"]].sum(axis=1).to_numpy(),
        np.ones(len(predictions)),
        atol=1e-6,
    )
