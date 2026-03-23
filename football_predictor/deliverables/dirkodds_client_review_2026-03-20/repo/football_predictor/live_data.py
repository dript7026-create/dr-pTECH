from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence

import pandas as pd
import requests

from .data_loader import load_csv
from .sports import normalize_sport


CANONICAL_MATCH_COLUMNS = [
    "sport",
    "source",
    "external_id",
    "date",
    "status",
    "competition_code",
    "competition_name",
    "season",
    "home_team",
    "away_team",
    "home_team_id",
    "away_team_id",
    "home_score",
    "away_score",
    "venue",
    "latitude",
    "longitude",
]

FINISHED_STATUSES = {"FINISHED", "FT", "AET", "PEN"}
UPCOMING_STATUSES = {"SCHEDULED", "TIMED", "NS", "NOT STARTED"}


def _empty_match_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=CANONICAL_MATCH_COLUMNS)


def _normalize_match_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return _empty_match_frame()

    normalized = df.copy()
    for column in CANONICAL_MATCH_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = None
    normalized = normalized.loc[:, CANONICAL_MATCH_COLUMNS]
    normalized["sport"] = normalized["sport"].fillna("football").map(normalize_sport)
    normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce", utc=True).dt.tz_convert(None)
    normalized["status"] = normalized["status"].fillna("UNKNOWN").astype(str).str.upper()
    for score_column in ["home_score", "away_score", "latitude", "longitude"]:
        normalized[score_column] = pd.to_numeric(normalized[score_column], errors="coerce")
    for text_column in [
        "sport",
        "source",
        "external_id",
        "competition_code",
        "competition_name",
        "season",
        "home_team",
        "away_team",
        "home_team_id",
        "away_team_id",
        "venue",
    ]:
        normalized[text_column] = normalized[text_column].fillna("").astype(str).str.strip()
    return normalized


def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


@dataclass
class FootballDataOrgSource:
    api_key: Optional[str] = None
    base_url: str = "https://api.football-data.org/v4"

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.environ.get("FOOTBALL_DATA_API_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def fetch_matches(
        self,
        competitions: Optional[Sequence[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[str] = None,
    ) -> pd.DataFrame:
        if not self.is_configured:
            return _empty_match_frame()

        params: Dict[str, object] = {}
        if competitions:
            params["competitions"] = ",".join(competitions)
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if status:
            params["status"] = status

        payload = _http_get_json(
            f"{self.base_url}/matches",
            headers={"X-Auth-Token": self.api_key or ""},
            params=params,
        )
        matches = payload.get("matches", [])
        rows = []
        for match in matches:
            score = match.get("score", {}) or {}
            full_time = score.get("fullTime", {}) or {}
            competition = match.get("competition", {}) or {}
            home_team = match.get("homeTeam", {}) or {}
            away_team = match.get("awayTeam", {}) or {}
            venue = match.get("venue")
            rows.append(
                {
                    "source": "football-data.org",
                    "external_id": str(match.get("id", "")),
                    "date": match.get("utcDate"),
                    "status": match.get("status"),
                    "competition_code": competition.get("code"),
                    "competition_name": competition.get("name"),
                    "season": (match.get("season") or {}).get("startDate", "")[:4],
                    "home_team": home_team.get("name"),
                    "away_team": away_team.get("name"),
                    "home_team_id": home_team.get("id"),
                    "away_team_id": away_team.get("id"),
                    "home_score": full_time.get("home"),
                    "away_score": full_time.get("away"),
                    "venue": venue,
                    "latitude": None,
                    "longitude": None,
                }
            )
        return _normalize_match_frame(pd.DataFrame(rows))


@dataclass
class TheSportsDBSource:
    api_key: Optional[str] = None
    base_url: str = "https://www.thesportsdb.com/api/v1/json"
    sport: str = "football"

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.environ.get("THESPORTSDB_API_KEY", "3")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _endpoint(self, path: str) -> str:
        return f"{self.base_url}/{self.api_key}/{path}"

    def fetch_league_season(self, league_id: str, season: str) -> pd.DataFrame:
        if not self.is_configured:
            return _empty_match_frame()
        try:
            payload = _http_get_json(self._endpoint("eventsseason.php"), params={"id": league_id, "s": season})
        except requests.RequestException:
            return _empty_match_frame()
        return self._normalize_events(payload.get("events") or [])

    def fetch_upcoming(self, league_id: str) -> pd.DataFrame:
        if not self.is_configured:
            return _empty_match_frame()
        try:
            payload = _http_get_json(self._endpoint("eventsnextleague.php"), params={"id": league_id})
        except requests.RequestException:
            return _empty_match_frame()
        return self._normalize_events(payload.get("events") or [])

    def _normalize_events(self, events: Sequence[Dict[str, object]]) -> pd.DataFrame:
        rows = []
        for event in events:
            rows.append(
                {
                    "sport": normalize_sport(self.sport),
                    "source": f"thesportsdb:{normalize_sport(self.sport)}",
                    "external_id": str(event.get("idEvent", "")),
                    "date": event.get("strTimestamp") or event.get("dateEvent"),
                    "status": event.get("strStatus") or ("FINISHED" if event.get("intHomeScore") not in (None, "") else "SCHEDULED"),
                    "competition_code": event.get("idLeague"),
                    "competition_name": event.get("strLeague"),
                    "season": event.get("strSeason"),
                    "home_team": event.get("strHomeTeam"),
                    "away_team": event.get("strAwayTeam"),
                    "home_team_id": event.get("idHomeTeam"),
                    "away_team_id": event.get("idAwayTeam"),
                    "home_score": event.get("intHomeScore"),
                    "away_score": event.get("intAwayScore"),
                    "venue": event.get("strVenue"),
                    "latitude": event.get("strLatitude"),
                    "longitude": event.get("strLongitude"),
                }
            )
        return _normalize_match_frame(pd.DataFrame(rows))


@dataclass
class TheSportsDBBaseballSource(TheSportsDBSource):
    sport: str = "baseball"


@dataclass
class TheSportsDBBasketballSource(TheSportsDBSource):
    sport: str = "basketball"


def merge_match_frames(frames: Iterable[pd.DataFrame]) -> pd.DataFrame:
    usable = [frame for frame in frames if frame is not None and not frame.empty]
    if not usable:
        return _empty_match_frame()
    merged = _normalize_match_frame(pd.concat(usable, ignore_index=True))
    merged = merged.drop_duplicates(subset=["source", "external_id"], keep="last")
    return merged.sort_values(["date", "competition_name", "home_team", "away_team"], na_position="last").reset_index(drop=True)


def ensure_warehouse(db_path: str) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                sport TEXT NOT NULL DEFAULT 'football',
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                match_date TEXT,
                status TEXT,
                competition_code TEXT,
                competition_name TEXT,
                season TEXT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_team_id TEXT,
                away_team_id TEXT,
                home_score REAL,
                away_score REAL,
                venue TEXT,
                latitude REAL,
                longitude REAL,
                last_synced TEXT NOT NULL,
                PRIMARY KEY (sport, source, external_id)
            )
            """
        )
        existing_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(matches)").fetchall()
        }
        if "sport" not in existing_columns:
            connection.execute("ALTER TABLE matches ADD COLUMN sport TEXT NOT NULL DEFAULT 'football'")
        connection.commit()
    finally:
        connection.close()


def upsert_matches(db_path: str, frame: pd.DataFrame) -> int:
    normalized = _normalize_match_frame(frame)
    if normalized.empty:
        return 0
    ensure_warehouse(db_path)
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for row in normalized.itertuples(index=False):
        rows.append(
            (
                row.sport,
                row.source,
                row.external_id,
                row.date.isoformat() if pd.notna(row.date) else None,
                row.status,
                row.competition_code,
                row.competition_name,
                row.season,
                row.home_team,
                row.away_team,
                row.home_team_id,
                row.away_team_id,
                row.home_score,
                row.away_score,
                row.venue,
                row.latitude,
                row.longitude,
                now,
            )
        )
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            """
            INSERT INTO matches (
                sport, source, external_id, match_date, status, competition_code, competition_name, season,
                home_team, away_team, home_team_id, away_team_id,
                home_score, away_score, venue, latitude, longitude, last_synced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sport, source, external_id) DO UPDATE SET
                match_date=excluded.match_date,
                status=excluded.status,
                competition_code=excluded.competition_code,
                competition_name=excluded.competition_name,
                season=excluded.season,
                home_team=excluded.home_team,
                away_team=excluded.away_team,
                home_team_id=excluded.home_team_id,
                away_team_id=excluded.away_team_id,
                home_score=excluded.home_score,
                away_score=excluded.away_score,
                venue=excluded.venue,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                last_synced=excluded.last_synced
            """,
            rows,
        )
        connection.commit()
    finally:
        connection.close()
    return len(rows)


def seed_warehouse_from_csv(db_path: str, csv_path: str, source_name: str = "local_csv") -> int:
    history = load_csv(csv_path)
    if history.empty:
        return 0
    frame = history.copy().reset_index(drop=True)
    if "date" not in frame.columns:
        frame["date"] = pd.NaT
    frame["sport"] = frame.get("sport", "football")
    frame["source"] = source_name
    frame["external_id"] = [
        f"{source_name}:{index}:{row.home_team}:{row.away_team}:{str(row.date) if pd.notna(row.date) else 'undated'}"
        for index, row in frame.iterrows()
    ]
    frame["status"] = "FINISHED"
    frame["competition_code"] = frame.get("competition_code", "")
    frame["competition_name"] = frame.get("competition_name", "")
    frame["season"] = frame["date"].dt.year.astype("Int64").astype(str).replace("<NA>", "")
    frame["home_team_id"] = frame.get("home_team_id", "")
    frame["away_team_id"] = frame.get("away_team_id", "")
    frame["venue"] = frame.get("venue", "")
    frame["latitude"] = frame.get("latitude", None)
    frame["longitude"] = frame.get("longitude", None)
    return upsert_matches(db_path, frame)


def read_warehouse_matches(
    db_path: str,
    sport: Optional[str] = None,
    statuses: Optional[Sequence[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> pd.DataFrame:
    ensure_warehouse(db_path)
    query = "SELECT sport, source, external_id, match_date, status, competition_code, competition_name, season, home_team, away_team, home_team_id, away_team_id, home_score, away_score, venue, latitude, longitude FROM matches WHERE 1=1"
    params: List[object] = []
    if sport:
        query += " AND sport = ?"
        params.append(normalize_sport(sport))
    if statuses:
        placeholders = ",".join("?" for _ in statuses)
        query += f" AND status IN ({placeholders})"
        params.extend([status.upper() for status in statuses])
    if date_from:
        query += " AND match_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND match_date <= ?"
        params.append(date_to)
    query += " ORDER BY match_date ASC, competition_name ASC, home_team ASC, away_team ASC"
    connection = sqlite3.connect(db_path)
    try:
        frame = pd.read_sql_query(query, connection, params=params)
    finally:
        connection.close()
    frame.rename(columns={"match_date": "date"}, inplace=True)
    return _normalize_match_frame(frame)


def finished_history_frame(db_path: str) -> pd.DataFrame:
    history = read_warehouse_matches(db_path, statuses=sorted(FINISHED_STATUSES))
    if history.empty:
        return pd.DataFrame(columns=["sport", "date", "home_team", "away_team", "home_score", "away_score"])
    return history.loc[:, ["sport", "date", "home_team", "away_team", "home_score", "away_score"]].copy()


def upcoming_fixtures_frame(db_path: str, sport: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None) -> pd.DataFrame:
    return read_warehouse_matches(db_path, sport=sport, statuses=sorted(UPCOMING_STATUSES), date_from=date_from, date_to=date_to)


def update_warehouse_from_sources(
    db_path: str,
    sport: str = "football",
    football_data_competitions: Optional[Sequence[str]] = None,
    thesportsdb_league_ids: Optional[Sequence[str]] = None,
    season: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, object]:
    ensure_warehouse(db_path)
    resolved_sport = normalize_sport(sport)
    football_data = FootballDataOrgSource()
    sportsdb: TheSportsDBSource
    if resolved_sport == "baseball":
        sportsdb = TheSportsDBBaseballSource()
    elif resolved_sport == "basketball":
        sportsdb = TheSportsDBBasketballSource()
    else:
        sportsdb = TheSportsDBSource()

    synced = 0
    details: Dict[str, object] = {"sport": resolved_sport, "sources": {}}

    fd_frames = []
    if resolved_sport == "football" and football_data_competitions and football_data.is_configured:
        for status in ["FINISHED", "SCHEDULED"]:
            frame = football_data.fetch_matches(
                competitions=football_data_competitions,
                date_from=date_from,
                date_to=date_to,
                status=status,
            )
            fd_frames.append(frame)
        merged = merge_match_frames(fd_frames)
        synced += upsert_matches(db_path, merged)
        details["sources"]["football-data.org"] = {"rows": len(merged), "configured": True}
    else:
        details["sources"]["football-data.org"] = {"rows": 0, "configured": football_data.is_configured}

    sportsdb_frames = []
    if thesportsdb_league_ids and sportsdb.is_configured:
        for league_id in thesportsdb_league_ids:
            if season:
                sportsdb_frames.append(sportsdb.fetch_league_season(league_id, season))
            sportsdb_frames.append(sportsdb.fetch_upcoming(league_id))
        merged = merge_match_frames(sportsdb_frames)
        synced += upsert_matches(db_path, merged)
        details["sources"][f"thesportsdb:{resolved_sport}"] = {"rows": len(merged), "configured": True}
    else:
        details["sources"][f"thesportsdb:{resolved_sport}"] = {"rows": 0, "configured": sportsdb.is_configured}

    details["rows_synced"] = synced
    details["warehouse_path"] = db_path
    return details