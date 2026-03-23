from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from .media_signals import fixture_key


def _normalize_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "approved", "allow", "allowed", "y"}


def load_player_consent_csv(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path).copy()
    return _normalize_consent_frame(frame)


def load_player_consent_manifest(path: str) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        records = payload.get("consents", [])
    elif isinstance(payload, list):
        records = payload
    else:
        raise ValueError("Consent manifest must be a JSON object with a 'consents' list or a top-level list.")
    frame = pd.DataFrame(records)
    return _normalize_consent_frame(frame)


def _normalize_consent_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    required = {"team", "approved"}
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Player consent CSV missing required columns: {', '.join(missing)}")
    if "fixture_key" not in frame.columns:
        for column in ["home_team", "away_team", "date"]:
            if column not in frame.columns:
                frame[column] = ""
        frame["fixture_key"] = [fixture_key(row.home_team, row.away_team, row.date) for row in frame.itertuples(index=False)]
    frame["team"] = frame["team"].astype(str).str.strip()
    frame["approved"] = frame["approved"].map(_normalize_bool)
    if "entity_id" not in frame.columns:
        frame["entity_id"] = [f"{team.lower().replace(' ', '_')}_{index + 1:02d}" for index, team in enumerate(frame["team"])]
    if "approval_scope" not in frame.columns:
        frame["approval_scope"] = "lineup"
    if "approval_source" not in frame.columns:
        frame["approval_source"] = "consent_csv"
    if "approval_granted_at" not in frame.columns:
        frame["approval_granted_at"] = ""
    if "approval_expires_at" not in frame.columns:
        frame["approval_expires_at"] = ""
    if "audit_ref" not in frame.columns:
        frame["audit_ref"] = ""
    if "play_scope" not in frame.columns:
        frame["play_scope"] = "match"
    if "consent_version" not in frame.columns:
        frame["consent_version"] = "v1"
    return frame


def _team_registry(team_frame: pd.DataFrame, roster_size: int = 11) -> tuple[float, List[Dict[str, object]]]:
    if team_frame.empty:
        return 0.0, []
    working = team_frame.copy()
    if "approval_scope" not in working.columns:
        working["approval_scope"] = "lineup"
    if "approval_source" not in working.columns:
        working["approval_source"] = "consent_frame"
    for column in ["approval_granted_at", "approval_expires_at", "audit_ref", "play_scope", "consent_version"]:
        if column not in working.columns:
            working[column] = ""
    registry: List[Dict[str, object]] = []
    for row in working.itertuples(index=False):
        registry.append(
            {
                "entity_id": str(row.entity_id),
                "team": str(row.team),
                "approved": bool(row.approved),
                "approval_scope": str(row.approval_scope),
                "approval_source": str(row.approval_source),
                "approval_granted_at": str(row.approval_granted_at),
                "approval_expires_at": str(row.approval_expires_at),
                "audit_ref": str(row.audit_ref),
                "play_scope": str(row.play_scope),
                "consent_version": str(row.consent_version),
            }
        )
    approved_count = sum(1 for item in registry if item["approved"])
    ratio = approved_count / float(max(roster_size, len(registry)))
    return float(ratio), registry


def build_fixture_consent_frame(fixtures_df: pd.DataFrame, consent_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    working = consent_df.copy()
    for fixture in fixtures_df.itertuples(index=False):
        key = fixture_key(fixture.home_team, fixture.away_team, fixture.date)
        fixture_rows = working.loc[working["fixture_key"] == key]
        home_rows = fixture_rows.loc[fixture_rows["team"] == fixture.home_team]
        away_rows = fixture_rows.loc[fixture_rows["team"] == fixture.away_team]
        home_ratio, home_registry = _team_registry(home_rows)
        away_ratio, away_registry = _team_registry(away_rows)
        rows.append(
            {
                "fixture_key": key,
                "lineup_approval_ratio": float(min(home_ratio, away_ratio)),
                "home_lineup_approval_ratio": float(home_ratio),
                "away_lineup_approval_ratio": float(away_ratio),
                "home_consent_registry_json": json.dumps(home_registry),
                "away_consent_registry_json": json.dumps(away_registry),
            }
        )
    return pd.DataFrame(rows)