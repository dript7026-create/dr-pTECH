from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .consent import build_fixture_consent_frame, load_player_consent_csv, load_player_consent_manifest
from .forecast import predict_upcoming_fixtures
from .live_data import (
    finished_history_frame,
    upcoming_fixtures_frame,
    update_warehouse_from_sources,
    seed_warehouse_from_csv,
)
from .media_signals import fetch_rss_articles, build_fixture_media_frame
from .model import load_model
from .player_stats import build_fixture_player_quality_frame, load_player_stats_csv
from .simulation import SimulationConfig, simulate_prediction_frame
from .sports import normalize_sport
from .weather import build_fixture_weather_frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync live sports data, predict upcoming fixtures, and export 3D trajectory simulations.")
    parser.add_argument("--bundle", required=True, help="Path to a trained DirkOdds joblib bundle")
    parser.add_argument("--db", default=".pytest_cache/dirkodds_live.sqlite", help="SQLite warehouse path")
    parser.add_argument("--sport", help="Optional sport override: football, baseball, or basketball")
    parser.add_argument("--history-csv", help="Optional local historical CSV to seed the warehouse")
    parser.add_argument("--football-data-competition", action="append", default=[], help="football-data.org competition code, e.g. PL")
    parser.add_argument("--thesportsdb-league-id", action="append", default=[], help="TheSportsDB league id for the selected sport")
    parser.add_argument("--season", help="Season identifier for TheSportsDB, e.g. 2025-2026")
    parser.add_argument("--date-from", help="Lower bound for fixture sync, YYYY-MM-DD")
    parser.add_argument("--date-to", help="Upper bound for fixture sync, YYYY-MM-DD")
    parser.add_argument("--rss-url", action="append", default=[], help="Optional football RSS/news feeds for media sentiment")
    parser.add_argument("--player-stats-csv", help="Optional licensed or user-supplied player stats CSV for aggregate team-quality adjustments")
    parser.add_argument("--player-consent-csv", help="Optional consent scaffold CSV for lineup and entity approval tracking")
    parser.add_argument("--player-consent-manifest", help="Optional JSON consent manifest with scope, expiry, and audit fields")
    parser.add_argument("--lineup-approval-ratio", type=float, default=0.0, help="Fallback lineup approval ratio when no per-entity consent registry is provided")
    parser.add_argument("--simulate-count", type=int, default=1500, help="Monte Carlo simulations per fixture")
    parser.add_argument("--output-json", help="Optional path to write the prediction and simulation report")
    args = parser.parse_args()

    bundle = load_model(args.bundle)
    sport = normalize_sport(args.sport or getattr(bundle, "sport", "football"))

    if args.history_csv:
        seed_warehouse_from_csv(args.db, args.history_csv)

    sync_report = update_warehouse_from_sources(
        args.db,
        sport=sport,
        football_data_competitions=args.football_data_competition,
        thesportsdb_league_ids=args.thesportsdb_league_id,
        season=args.season,
        date_from=args.date_from,
        date_to=args.date_to,
    )

    history_df = finished_history_frame(args.db)
    history_df = history_df[history_df["sport"] == sport].reset_index(drop=True) if not history_df.empty else history_df
    fixtures_df = upcoming_fixtures_frame(args.db, sport=sport, date_from=args.date_from, date_to=args.date_to)
    if fixtures_df.empty:
        report = {"sync": sync_report, "predictions": [], "simulations": [], "message": "No upcoming fixtures available in the warehouse."}
        print(json.dumps(report, indent=2))
        if args.output_json:
            Path(args.output_json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return

    articles = fetch_rss_articles(args.rss_url) if args.rss_url else []
    media_df = build_fixture_media_frame(fixtures_df, articles) if articles else None
    weather_df = build_fixture_weather_frame(fixtures_df) if sport in {"football", "baseball"} else None
    player_quality_df = None
    if args.player_stats_csv:
        player_quality_df = build_fixture_player_quality_frame(fixtures_df, load_player_stats_csv(args.player_stats_csv))

    predictions = predict_upcoming_fixtures(
        bundle,
        history_df,
        fixtures_df,
        media_df=media_df,
        weather_df=weather_df,
        player_quality_df=player_quality_df,
        sport=sport,
    )
    predictions["lineup_approval_ratio"] = float(args.lineup_approval_ratio)
    predictions["home_lineup_approval_ratio"] = float(args.lineup_approval_ratio)
    predictions["away_lineup_approval_ratio"] = float(args.lineup_approval_ratio)
    predictions["home_consent_registry_json"] = "[]"
    predictions["away_consent_registry_json"] = "[]"
    consent_input = None
    if args.player_consent_manifest:
        consent_input = load_player_consent_manifest(args.player_consent_manifest)
    elif args.player_consent_csv:
        consent_input = load_player_consent_csv(args.player_consent_csv)
    if consent_input is not None:
        consent_frame = build_fixture_consent_frame(fixtures_df, consent_input)
        predictions = predictions.merge(consent_frame, on="fixture_key", how="left", suffixes=("", "_consent"))
        for column in [
            "lineup_approval_ratio",
            "home_lineup_approval_ratio",
            "away_lineup_approval_ratio",
            "home_consent_registry_json",
            "away_consent_registry_json",
        ]:
            consent_column = f"{column}_consent"
            if consent_column in predictions.columns:
                predictions[column] = predictions[consent_column].combine_first(predictions[column])
                predictions = predictions.drop(columns=[consent_column])
        for column, default in [
            ("lineup_approval_ratio", float(args.lineup_approval_ratio)),
            ("home_lineup_approval_ratio", float(args.lineup_approval_ratio)),
            ("away_lineup_approval_ratio", float(args.lineup_approval_ratio)),
        ]:
            predictions[column] = pd.to_numeric(predictions[column], errors="coerce").fillna(default)
        for column in ["home_consent_registry_json", "away_consent_registry_json"]:
            predictions[column] = predictions[column].fillna("[]")
    simulations = simulate_prediction_frame(predictions, config=SimulationConfig(simulation_count=args.simulate_count))

    report = {
        "sync": sync_report,
        "prediction_count": len(predictions),
        "predictions": predictions.to_dict(orient="records"),
        "simulations": simulations,
        "notes": [
            "Live sync is bounded by whichever providers are configured through environment variables and available network access.",
            "3D simulations are physics-inspired kinematic reconstructions driven by forecast probabilities, form, weather, and media signals, not literal tracking-data replays.",
            "Player-stat adjustments are designed for licensed or user-supplied numerical stats only; the playback path does not require player names, likenesses, or portraits.",
            "Entity-state outputs use abstract readiness, fatigue, hydration, sodium-balance, discipline, morale, and coach-pressure models for simulation flavor only; they are not medical, psychiatric, or biometric reconstructions of real athletes.",
            "Source-to-simulation delta signatures capture how public performance inputs are transformed into non-identifying in-app entity states.",
            "ArtiSapien hooks are placeholders and remain disabled until licensed data and deployment-side approval inputs are present.",
            "Regulated-session hooks provide transparent consent gates, previous-game datastream stubs, simulation channels, and human-presence prompts only; they do not implement hidden switching or wagering guarantees.",
            "Consent CSV and JSON manifest inputs can scaffold per-entity approval state, audit refs, and expiry windows, but they are not a substitute for a production consent service.",
        ],
    }
    print(json.dumps(report, indent=2, default=str))
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()