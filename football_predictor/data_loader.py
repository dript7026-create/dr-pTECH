from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .sports import get_sport_config, normalize_sport, resolve_frame_sport


FEATURE_COLUMNS = [
    "home_form",
    "away_form",
    "form_diff",
    "home_points_form",
    "away_points_form",
    "points_form_diff",
    "home_goals_for_form",
    "away_goals_for_form",
    "goals_for_diff",
    "home_goals_against_form",
    "away_goals_against_form",
    "goals_against_diff",
    "home_win_rate",
    "away_win_rate",
    "win_rate_diff",
    "rest_days_home",
    "rest_days_away",
    "rest_days_diff",
    "home_matches_played",
    "away_matches_played",
    "experience_diff",
    "home_advantage",
]


def _rename_first_match(df: pd.DataFrame, canonical: str, candidates: List[str]) -> None:
    if canonical in df.columns:
        return
    for candidate in candidates:
        if candidate in df.columns:
            df.rename(columns={candidate: canonical}, inplace=True)
            return


def _mean_tail(values: List[float], window: int) -> float:
    if not values:
        return 0.0
    return float(np.mean(values[-window:]))


def _win_rate_tail(values: List[float], window: int) -> float:
    if not values:
        return 0.0
    return float(np.mean(values[-window:]))


def _points_for_score_diff(score_diff: float, sport: str) -> int:
    if not get_sport_config(sport).allows_draws:
        return 1 if score_diff > 0 else 0
    if score_diff > 0:
        return 3
    if score_diff == 0:
        return 1
    return 0


def _outcome_from_scores(home_score: float, away_score: float, sport: str) -> int:
    if home_score > away_score:
        return 2
    if home_score == away_score:
        if not get_sport_config(sport).allows_draws:
            raise ValueError(f"{sport.title()} training data cannot contain tied final scores.")
        return 1
    return 0


def _resolve_sport(df: pd.DataFrame, sport: Optional[str] = None) -> str:
    if sport is not None:
        return normalize_sport(sport)
    if "sport" in df.columns:
        return resolve_frame_sport(df["sport"].tolist(), default="football")
    return "football"


def _init_team_state() -> Dict[str, object]:
    return {
        "goal_diffs": [],
        "points": [],
        "goals_for": [],
        "goals_against": [],
        "wins": [],
        "last_date": None,
        "matches_played": 0,
    }


def _team_snapshot(team_state: Dict[str, object], match_date: Optional[pd.Timestamp], window: int) -> Dict[str, float]:
    last_date = team_state["last_date"]
    rest_days = 7.0
    if match_date is not None and last_date is not None and not pd.isna(match_date) and not pd.isna(last_date):
        delta = (match_date - last_date).days
        if delta >= 0:
            rest_days = float(delta)

    return {
        "form": _mean_tail(team_state["goal_diffs"], window),
        "points_form": _mean_tail(team_state["points"], window),
        "goals_for_form": _mean_tail(team_state["goals_for"], window),
        "goals_against_form": _mean_tail(team_state["goals_against"], window),
        "win_rate": _win_rate_tail(team_state["wins"], window),
        "rest_days": rest_days,
        "matches_played": float(team_state["matches_played"]),
    }


def _prepare_history_frame(history_df: pd.DataFrame, sport: Optional[str] = None) -> tuple[pd.DataFrame, str]:
    prepared = load_csv(history_df, sport=sport) if isinstance(history_df, str) else history_df.copy()
    resolved_sport = _resolve_sport(prepared, sport=sport)
    prepared["sport"] = resolved_sport
    if "date" in prepared.columns:
        prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
        prepared = prepared.sort_values(["date", "home_team", "away_team"], na_position="last").reset_index(drop=True)
    else:
        prepared = prepared.reset_index(drop=True)
    return prepared, resolved_sport


def _history_base_date(history_df: pd.DataFrame) -> Optional[pd.Timestamp]:
    if "date" not in history_df.columns or not history_df["date"].notna().any():
        return None
    return pd.to_datetime(history_df["date"], errors="coerce").max()


def _resolve_fixture_date(match_date: Optional[object], base_date: Optional[pd.Timestamp]) -> pd.Timestamp:
    if match_date is not None:
        fixture_date = pd.to_datetime(match_date, errors="coerce")
    elif base_date is not None and not pd.isna(base_date):
        fixture_date = base_date + pd.Timedelta(days=7)
    else:
        fixture_date = pd.NaT
    return fixture_date


def _build_team_feature_cache(history_df: pd.DataFrame, window: int, sport: str) -> Dict[str, Dict[str, object]]:
    history: Dict[str, Dict[str, object]] = {}
    for row in history_df.itertuples(index=False):
        home_team = row.home_team
        away_team = row.away_team
        match_date = getattr(row, "date", None)
        home_state = history.setdefault(home_team, _init_team_state())
        away_state = history.setdefault(away_team, _init_team_state())

        home_score = float(row.home_score)
        away_score = float(row.away_score)
        home_goal_diff = home_score - away_score
        away_goal_diff = -home_goal_diff

        home_state["goal_diffs"].append(home_goal_diff)
        home_state["points"].append(_points_for_score_diff(home_goal_diff, sport))
        home_state["goals_for"].append(home_score)
        home_state["goals_against"].append(away_score)
        home_state["wins"].append(1.0 if home_goal_diff > 0 else 0.0)
        home_state["matches_played"] += 1
        home_state["last_date"] = match_date

        away_state["goal_diffs"].append(away_goal_diff)
        away_state["points"].append(_points_for_score_diff(away_goal_diff, sport))
        away_state["goals_for"].append(away_score)
        away_state["goals_against"].append(home_score)
        away_state["wins"].append(1.0 if away_goal_diff > 0 else 0.0)
        away_state["matches_played"] += 1
        away_state["last_date"] = match_date

    cache: Dict[str, Dict[str, object]] = {}
    for team_name, team_state in history.items():
        cache[team_name] = {
            "form": _mean_tail(team_state["goal_diffs"], window),
            "points_form": _mean_tail(team_state["points"], window),
            "goals_for_form": _mean_tail(team_state["goals_for"], window),
            "goals_against_form": _mean_tail(team_state["goals_against"], window),
            "win_rate": _win_rate_tail(team_state["wins"], window),
            "matches_played": float(team_state["matches_played"]),
            "last_date": team_state["last_date"],
        }
    return cache


def _team_snapshot_from_cache(team_cache: Dict[str, Dict[str, object]], team_name: str, fixture_date: pd.Timestamp) -> Dict[str, float]:
    team_state = team_cache.get(team_name)
    if team_state is None:
        raise ValueError(f"Unknown team: {team_name}")

    rest_days = 7.0
    last_date = team_state.get("last_date")
    if fixture_date is not pd.NaT and last_date is not None and not pd.isna(last_date) and not pd.isna(fixture_date):
        delta = (fixture_date - last_date).days
        if delta >= 0:
            rest_days = float(delta)

    return {
        "form": float(team_state["form"]),
        "points_form": float(team_state["points_form"]),
        "goals_for_form": float(team_state["goals_for_form"]),
        "goals_against_form": float(team_state["goals_against_form"]),
        "win_rate": float(team_state["win_rate"]),
        "rest_days": rest_days,
        "matches_played": float(team_state["matches_played"]),
    }


def load_csv(path: str, sport: Optional[str] = None) -> pd.DataFrame:
    """Load CSV and normalize common team-vs-team match columns."""
    df = pd.read_csv(path)
    df = df.copy()

    _rename_first_match(df, "date", ["Date", "match_date"])
    _rename_first_match(df, "home_team", ["HomeTeam", "home", "homeClub", "home_name"])
    _rename_first_match(df, "away_team", ["AwayTeam", "away", "awayClub", "away_name"])
    _rename_first_match(df, "home_score", ["home_goals", "homeGoals", "FTHG", "home_points", "home_runs", "HomeScore"])
    _rename_first_match(df, "away_score", ["away_goals", "awayGoals", "FTAG", "away_points", "away_runs", "AwayScore"])

    if "home_team" not in df.columns or "away_team" not in df.columns:
        raise ValueError("CSV must contain home/away team columns.")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if "home_score" in df.columns:
        df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    if "away_score" in df.columns:
        df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")

    df["home_team"] = df["home_team"].astype(str).str.strip()
    df["away_team"] = df["away_team"].astype(str).str.strip()
    resolved_sport = _resolve_sport(df, sport=sport)
    df["sport"] = resolved_sport
    return df


def prepare_training_frame(df: pd.DataFrame, window: int = 5, sport: Optional[str] = None) -> pd.DataFrame:
    """Create a pre-match feature frame suitable for training.

    Features are computed strictly from matches that happened before each row,
    so the model can be used for real pre-match inference without target leakage.
    """
    df, resolved_sport = _prepare_history_frame(df, sport=sport)
    required = {"home_score", "away_score"}
    if not required.issubset(df.columns):
        raise ValueError("Training data requires home_score and away_score columns.")

    history: Dict[str, Dict[str, object]] = {}
    rows: List[Dict[str, object]] = []

    for _, row in df.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]
        match_date = row["date"] if "date" in row.index else None

        home_state = history.setdefault(home_team, _init_team_state())
        away_state = history.setdefault(away_team, _init_team_state())

        home_snapshot = _team_snapshot(home_state, match_date, window)
        away_snapshot = _team_snapshot(away_state, match_date, window)

        home_score = float(row["home_score"])
        away_score = float(row["away_score"])
        home_goal_diff = home_score - away_score
        away_goal_diff = -home_goal_diff

        feature_row = row.to_dict()
        feature_row.update(
            {
                "sport": resolved_sport,
                "outcome": _outcome_from_scores(home_score, away_score, resolved_sport),
                "home_form": home_snapshot["form"],
                "away_form": away_snapshot["form"],
                "form_diff": home_snapshot["form"] - away_snapshot["form"],
                "home_points_form": home_snapshot["points_form"],
                "away_points_form": away_snapshot["points_form"],
                "points_form_diff": home_snapshot["points_form"] - away_snapshot["points_form"],
                "home_goals_for_form": home_snapshot["goals_for_form"],
                "away_goals_for_form": away_snapshot["goals_for_form"],
                "goals_for_diff": home_snapshot["goals_for_form"] - away_snapshot["goals_for_form"],
                "home_goals_against_form": home_snapshot["goals_against_form"],
                "away_goals_against_form": away_snapshot["goals_against_form"],
                "goals_against_diff": home_snapshot["goals_against_form"] - away_snapshot["goals_against_form"],
                "home_win_rate": home_snapshot["win_rate"],
                "away_win_rate": away_snapshot["win_rate"],
                "win_rate_diff": home_snapshot["win_rate"] - away_snapshot["win_rate"],
                "rest_days_home": home_snapshot["rest_days"],
                "rest_days_away": away_snapshot["rest_days"],
                "rest_days_diff": home_snapshot["rest_days"] - away_snapshot["rest_days"],
                "home_matches_played": home_snapshot["matches_played"],
                "away_matches_played": away_snapshot["matches_played"],
                "experience_diff": home_snapshot["matches_played"] - away_snapshot["matches_played"],
                "home_advantage": 1.0,
            }
        )
        rows.append(feature_row)

        home_state["goal_diffs"].append(home_goal_diff)
        home_state["points"].append(_points_for_score_diff(home_goal_diff, resolved_sport))
        home_state["goals_for"].append(home_score)
        home_state["goals_against"].append(away_score)
        home_state["wins"].append(1.0 if home_goal_diff > 0 else 0.0)
        home_state["matches_played"] += 1
        home_state["last_date"] = match_date

        away_state["goal_diffs"].append(away_goal_diff)
        away_state["points"].append(_points_for_score_diff(away_goal_diff, resolved_sport))
        away_state["goals_for"].append(away_score)
        away_state["goals_against"].append(home_score)
        away_state["wins"].append(1.0 if away_goal_diff > 0 else 0.0)
        away_state["matches_played"] += 1
        away_state["last_date"] = match_date

    feature_df = pd.DataFrame(rows)
    for column in FEATURE_COLUMNS:
        feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce").fillna(0.0)
    return feature_df


def add_team_form_features(df: pd.DataFrame, window: int = 5, date_col: Optional[str] = "date") -> pd.DataFrame:
    """Backwards-compatible wrapper around the richer feature pipeline."""
    del date_col
    return prepare_training_frame(df, window=window)


def build_fixture_feature_row(
    history_df: pd.DataFrame,
    home_team: str,
    away_team: str,
    match_date: Optional[str] = None,
    window: int = 5,
    sport: Optional[str] = None,
) -> pd.DataFrame:
    """Build a single pre-match feature row for an upcoming fixture."""
    fixture_df = pd.DataFrame(
        [{
            "home_team": home_team,
            "away_team": away_team,
            "date": match_date,
        }]
    )
    return build_fixture_feature_frame(history_df, fixture_df, window=window, sport=sport)


def build_fixture_feature_frame(
    history_df: pd.DataFrame,
    fixtures_df: pd.DataFrame,
    window: int = 5,
    sport: Optional[str] = None,
) -> pd.DataFrame:
    """Build pre-match feature rows for upcoming fixtures in one history pass."""
    history_df, resolved_sport = _prepare_history_frame(history_df, sport=sport)
    fixtures = fixtures_df.copy().reset_index(drop=True)
    if "home_team" not in fixtures.columns or "away_team" not in fixtures.columns:
        raise ValueError("Fixture data requires home_team and away_team columns.")

    teams = set(history_df["home_team"].astype(str)).union(set(history_df["away_team"].astype(str)))
    team_cache = _build_team_feature_cache(history_df, window=window, sport=resolved_sport)
    base_date = _history_base_date(history_df)
    rows: List[Dict[str, object]] = []

    for fixture in fixtures.itertuples(index=False):
        home_team = str(fixture.home_team)
        away_team = str(fixture.away_team)
        if home_team not in teams:
            raise ValueError(f"Unknown home team: {home_team}")
        if away_team not in teams:
            raise ValueError(f"Unknown away team: {away_team}")
        if home_team == away_team:
            raise ValueError("Home and away teams must differ.")

        fixture_date = _resolve_fixture_date(getattr(fixture, "date", None), base_date)
        home_snapshot = _team_snapshot_from_cache(team_cache, home_team, fixture_date)
        away_snapshot = _team_snapshot_from_cache(team_cache, away_team, fixture_date)
        rows.append(
            {
                "sport": resolved_sport,
                "date": fixture_date,
                "home_team": home_team,
                "away_team": away_team,
                "home_form": home_snapshot["form"],
                "away_form": away_snapshot["form"],
                "form_diff": home_snapshot["form"] - away_snapshot["form"],
                "home_points_form": home_snapshot["points_form"],
                "away_points_form": away_snapshot["points_form"],
                "points_form_diff": home_snapshot["points_form"] - away_snapshot["points_form"],
                "home_goals_for_form": home_snapshot["goals_for_form"],
                "away_goals_for_form": away_snapshot["goals_for_form"],
                "goals_for_diff": home_snapshot["goals_for_form"] - away_snapshot["goals_for_form"],
                "home_goals_against_form": home_snapshot["goals_against_form"],
                "away_goals_against_form": away_snapshot["goals_against_form"],
                "goals_against_diff": home_snapshot["goals_against_form"] - away_snapshot["goals_against_form"],
                "home_win_rate": home_snapshot["win_rate"],
                "away_win_rate": away_snapshot["win_rate"],
                "win_rate_diff": home_snapshot["win_rate"] - away_snapshot["win_rate"],
                "rest_days_home": home_snapshot["rest_days"],
                "rest_days_away": away_snapshot["rest_days"],
                "rest_days_diff": home_snapshot["rest_days"] - away_snapshot["rest_days"],
                "home_matches_played": home_snapshot["matches_played"],
                "away_matches_played": away_snapshot["matches_played"],
                "experience_diff": home_snapshot["matches_played"] - away_snapshot["matches_played"],
                "home_advantage": 1.0,
            }
        )

    feature_df = pd.DataFrame(rows)
    for column in FEATURE_COLUMNS:
        feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce").fillna(0.0)
    return feature_df

