from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from .data_loader import build_fixture_feature_frame
from .media_signals import fixture_key
from .model import DirkOddsBundle, predict_matches
from .sports import entropy_normalizer, get_sport_config, normalize_sport, outcome_label, resolve_frame_sport


PROBABILITY_COLUMNS = ["prob_away_win", "prob_draw", "prob_home_win"]


def _renormalize_triplet(away: float, draw: float, home: float) -> tuple[float, float, float]:
    clipped = np.clip([away, draw, home], 1e-6, None)
    total = float(np.sum(clipped))
    return float(clipped[0] / total), float(clipped[1] / total), float(clipped[2] / total)


def _renormalize_two_way(away: float, home: float) -> tuple[float, float]:
    clipped = np.clip([away, home], 1e-6, None)
    total = float(np.sum(clipped))
    return float(clipped[0] / total), float(clipped[1] / total)


def apply_context_adjustments(
    predictions_df: pd.DataFrame,
    media_df: Optional[pd.DataFrame] = None,
    weather_df: Optional[pd.DataFrame] = None,
    player_quality_df: Optional[pd.DataFrame] = None,
    sport: Optional[str] = None,
) -> pd.DataFrame:
    resolved_sport = normalize_sport(sport or resolve_frame_sport(predictions_df.get("sport", []), default="football"))
    allows_draws = get_sport_config(resolved_sport).allows_draws
    adjusted = predictions_df.copy()
    adjusted["sport"] = resolved_sport
    adjusted["fixture_key"] = [fixture_key(row.home_team, row.away_team, row.date) for row in adjusted.itertuples(index=False)]

    if media_df is not None and not media_df.empty:
        adjusted = adjusted.merge(media_df, on="fixture_key", how="left")
    if weather_df is not None and not weather_df.empty:
        adjusted = adjusted.merge(weather_df, on="fixture_key", how="left")
    if player_quality_df is not None and not player_quality_df.empty:
        adjusted = adjusted.merge(player_quality_df, on="fixture_key", how="left")

    for column in [
        "media_sentiment_home",
        "media_sentiment_away",
        "media_buzz_home",
        "media_buzz_away",
        "media_signal_gap",
        "weather_temperature_c",
        "weather_wind_speed",
        "weather_precipitation_mm",
        "weather_severity",
        "home_player_quality",
        "away_player_quality",
        "player_quality_diff",
    ]:
        if column not in adjusted.columns:
            adjusted[column] = 0.0
        adjusted[column] = pd.to_numeric(adjusted[column], errors="coerce").fillna(0.0)

    if "weather_summary" not in adjusted.columns:
        adjusted["weather_summary"] = "unavailable"
    adjusted["weather_summary"] = adjusted["weather_summary"].fillna("unavailable")

    media_shift = 0.035 * np.tanh(adjusted["media_signal_gap"].to_numpy(dtype=float))
    weather_drag = 0.08 * adjusted["weather_severity"].to_numpy(dtype=float)
    home_prob = adjusted["prob_home_win"].to_numpy(dtype=float) + media_shift - 0.5 * weather_drag
    away_prob = adjusted["prob_away_win"].to_numpy(dtype=float) - media_shift - 0.5 * weather_drag

    if allows_draws:
        draw_prob = adjusted["prob_draw"].to_numpy(dtype=float) + weather_drag
        probability_matrix = np.column_stack([away_prob, draw_prob, home_prob])
        probability_matrix = np.clip(probability_matrix, 1e-6, None)
        probability_matrix /= probability_matrix.sum(axis=1, keepdims=True)
        adjusted["prob_away_win"] = probability_matrix[:, 0]
        adjusted["prob_draw"] = probability_matrix[:, 1]
        adjusted["prob_home_win"] = probability_matrix[:, 2]
    else:
        probability_matrix = np.column_stack([away_prob, home_prob])
        probability_matrix = np.clip(probability_matrix, 1e-6, None)
        probability_matrix /= probability_matrix.sum(axis=1, keepdims=True)
        adjusted["prob_away_win"] = probability_matrix[:, 0]
        adjusted["prob_draw"] = 0.0
        adjusted["prob_home_win"] = probability_matrix[:, 1]

    probability_matrix = adjusted[PROBABILITY_COLUMNS].to_numpy(dtype=float)
    adjusted["prediction_code"] = probability_matrix.argmax(axis=1)
    adjusted["confidence"] = probability_matrix.max(axis=1)
    adjusted["uncertainty"] = 1.0 - adjusted["confidence"]
    adjusted["entropy"] = -np.sum(probability_matrix * np.log(np.clip(probability_matrix, 1e-9, 1.0)), axis=1) / entropy_normalizer(resolved_sport)
    adjusted["prediction"] = adjusted["prediction_code"].map(lambda code: outcome_label(int(code), resolved_sport))
    return adjusted


def predict_upcoming_fixtures(
    bundle: DirkOddsBundle,
    history_df: pd.DataFrame,
    fixtures_df: pd.DataFrame,
    media_df: Optional[pd.DataFrame] = None,
    weather_df: Optional[pd.DataFrame] = None,
    player_quality_df: Optional[pd.DataFrame] = None,
    sport: Optional[str] = None,
) -> pd.DataFrame:
    resolved_sport = normalize_sport(sport or getattr(bundle, "sport", None) or resolve_frame_sport(fixtures_df.get("sport", []), default="football"))
    metadata_rows = []
    fixture_features_input = fixtures_df.loc[:, [column for column in ["home_team", "away_team", "date"] if column in fixtures_df.columns]].copy()
    feature_df = build_fixture_feature_frame(
        history_df,
        fixture_features_input,
        sport=resolved_sport,
    )
    for fixture in fixtures_df.itertuples(index=False):
        metadata_rows.append(
            {
                "sport": resolved_sport,
                "source": getattr(fixture, "source", ""),
                "external_id": getattr(fixture, "external_id", ""),
                "status": getattr(fixture, "status", "SCHEDULED"),
                "competition_code": getattr(fixture, "competition_code", ""),
                "competition_name": getattr(fixture, "competition_name", ""),
                "season": getattr(fixture, "season", ""),
                "venue": getattr(fixture, "venue", ""),
                "latitude": getattr(fixture, "latitude", None),
                "longitude": getattr(fixture, "longitude", None),
            }
        )
    metadata_df = pd.DataFrame(metadata_rows)
    base_predictions = predict_matches(bundle, feature_df, sport=resolved_sport)
    enriched = pd.concat([base_predictions.reset_index(drop=True), metadata_df.reset_index(drop=True)], axis=1)
    return apply_context_adjustments(
        enriched,
        media_df=media_df,
        weather_df=weather_df,
        player_quality_df=player_quality_df,
        sport=resolved_sport,
    )