from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd

from .media_signals import fixture_key


PLAYER_STAT_COLUMNS = [
    "minutes",
    "goals",
    "assists",
    "shots_on_target",
    "key_passes",
    "tackles",
    "interceptions",
    "saves",
]


def load_player_stats_csv(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path).copy()
    if "team" not in frame.columns:
        raise ValueError("Player stats CSV must contain a 'team' column.")
    for column in PLAYER_STAT_COLUMNS:
        if column not in frame.columns:
            frame[column] = 0.0
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    frame["team"] = frame["team"].astype(str).str.strip()
    return frame


def aggregate_team_player_stats(players_df: pd.DataFrame) -> pd.DataFrame:
    if players_df.empty:
        return pd.DataFrame(columns=["team", "player_quality", "attack_quality", "defense_quality", "stamina_quality"])

    working = players_df.copy()
    working["minutes"] = working["minutes"].clip(lower=1.0)
    working["attack_component"] = (
        0.7 * working["goals"]
        + 0.45 * working["assists"]
        + 0.18 * working["shots_on_target"]
        + 0.12 * working["key_passes"]
    ) / working["minutes"] * 90.0
    working["defense_component"] = (
        0.35 * working["tackles"]
        + 0.35 * working["interceptions"]
        + 0.45 * working["saves"]
    ) / working["minutes"] * 90.0
    working["stamina_component"] = np.clip(working["minutes"] / 900.0, 0.0, 1.25)

    team = working.groupby("team", as_index=False).agg(
        attack_quality=("attack_component", "mean"),
        defense_quality=("defense_component", "mean"),
        stamina_quality=("stamina_component", "mean"),
    )
    team["player_quality"] = (
        0.5 * team["attack_quality"]
        + 0.35 * team["defense_quality"]
        + 0.15 * team["stamina_quality"]
    )

    for column in ["attack_quality", "defense_quality", "stamina_quality", "player_quality"]:
        mean = float(team[column].mean()) if not team.empty else 0.0
        std = float(team[column].std(ddof=0)) if not team.empty else 0.0
        if std > 1e-9:
            team[column] = (team[column] - mean) / std
        else:
            team[column] = 0.0
        team[column] = team[column].clip(-2.0, 2.0)
    return team


def build_fixture_player_quality_frame(fixtures_df: pd.DataFrame, players_df: pd.DataFrame) -> pd.DataFrame:
    team_profiles = aggregate_team_player_stats(players_df)
    lookup: Dict[str, Dict[str, float]] = team_profiles.set_index("team").to_dict(orient="index") if not team_profiles.empty else {}
    rows = []
    for fixture in fixtures_df.itertuples(index=False):
        home_profile = lookup.get(fixture.home_team, {})
        away_profile = lookup.get(fixture.away_team, {})
        home_quality = float(home_profile.get("player_quality", 0.0))
        away_quality = float(away_profile.get("player_quality", 0.0))
        rows.append(
            {
                "fixture_key": fixture_key(fixture.home_team, fixture.away_team, fixture.date),
                "home_player_quality": home_quality,
                "away_player_quality": away_quality,
                "player_quality_diff": home_quality - away_quality,
            }
        )
    return pd.DataFrame(rows)


def fixture_player_qualities(home_team: str, away_team: str, match_date: str, players_df: Optional[pd.DataFrame]) -> Dict[str, float]:
    if players_df is None or players_df.empty:
        return {"home_player_quality": 0.0, "away_player_quality": 0.0, "player_quality_diff": 0.0}
    fixture_frame = pd.DataFrame([{"home_team": home_team, "away_team": away_team, "date": match_date}])
    qualities = build_fixture_player_quality_frame(fixture_frame, players_df)
    if qualities.empty:
        return {"home_player_quality": 0.0, "away_player_quality": 0.0, "player_quality_diff": 0.0}
    record = qualities.iloc[0]
    return {
        "home_player_quality": float(record["home_player_quality"]),
        "away_player_quality": float(record["away_player_quality"]),
        "player_quality_diff": float(record["player_quality_diff"]),
    }