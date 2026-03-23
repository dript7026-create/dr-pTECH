from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Optional

import numpy as np
import pandas as pd


HEAD_SIZE_M = 0.1524
MIN_HEIGHT_M = 1.6256
MAX_HEIGHT_M = 2.0574
MIN_WEIGHT_KG = 72.5748
MAX_WEIGHT_KG = 158.7573
MIN_BODY_FAT = 0.02
MAX_BODY_FAT = 0.30


@dataclass(frozen=True)
class AvatarProfile:
    team: str
    role: str
    seed: int
    height_m: float
    weight_kg: float
    body_fat_pct: float
    muscle_ratio: float
    bone_ratio: float
    head_size_m: float
    shoulder_width_m: float
    torso_depth_m: float
    torso_length_m: float
    leg_length_m: float

    def to_dict(self) -> Dict[str, float | int | str]:
        return asdict(self)


def _bounded(value: float, lower: float, upper: float) -> float:
    return float(np.clip(value, lower, upper))


def _stable_seed(*parts: str) -> int:
    text = "::".join(parts)
    value = 2166136261
    for char in text:
        value ^= ord(char)
        value = (value * 16777619) % (2 ** 32)
    return int(value)


def _team_stat_row(team: str, players_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if players_df is None or players_df.empty or "team" not in players_df.columns:
        return pd.DataFrame()
    working = players_df.copy()
    working["team"] = working["team"].astype(str).str.strip()
    return working.loc[working["team"] == team]


def _performance_index(team_rows: pd.DataFrame) -> float:
    if team_rows.empty:
        return 0.5
    numeric_columns = [
        "minutes",
        "goals",
        "assists",
        "shots_on_target",
        "key_passes",
        "tackles",
        "interceptions",
        "saves",
    ]
    working = team_rows.copy()
    for column in numeric_columns:
        if column not in working.columns:
            working[column] = 0.0
        working[column] = pd.to_numeric(working[column], errors="coerce").fillna(0.0)
    minutes = working["minutes"].clip(lower=1.0)
    output = (
        1.0 * working["goals"]
        + 0.7 * working["assists"]
        + 0.25 * working["shots_on_target"]
        + 0.18 * working["key_passes"]
        + 0.22 * working["tackles"]
        + 0.22 * working["interceptions"]
        + 0.35 * working["saves"]
    ) / minutes * 90.0
    stamina = np.clip(minutes / 1200.0, 0.0, 1.0)
    raw = float(0.72 * output.mean() + 0.28 * stamina.mean())
    return float(1.0 / (1.0 + np.exp(-2.2 * (raw - 1.1))))


def build_avatar_profile(
    team: str,
    role: str,
    player_quality: float = 0.0,
    players_df: Optional[pd.DataFrame] = None,
    match_date: str = "",
) -> AvatarProfile:
    """Build an abstract avatar body profile.

    The profile is deliberately non-biometric: it uses coarse public performance intensity
    and optional licensed/user-supplied physical columns if present, but it does not infer
    genetics or claim to reproduce a real player's body.
    """
    team_rows = _team_stat_row(team, players_df)
    performance_index = _performance_index(team_rows)
    quality_index = float(np.clip((player_quality + 2.0) / 4.0, 0.0, 1.0))
    role_bias = {"attacker": 0.12, "keeper": 0.2, "support": 0.0}.get(role, 0.0)
    body_seed = _stable_seed(team, role, match_date)
    rng = np.random.default_rng(body_seed)

    supplied_height_m = None
    supplied_weight_kg = None
    supplied_body_fat = None
    if not team_rows.empty:
        if "height_in" in team_rows.columns:
            supplied_height_m = float(pd.to_numeric(team_rows["height_in"], errors="coerce").dropna().median() * 0.0254)
        elif "height_cm" in team_rows.columns:
            supplied_height_m = float(pd.to_numeric(team_rows["height_cm"], errors="coerce").dropna().median() / 100.0)
        if "weight_lb" in team_rows.columns:
            supplied_weight_kg = float(pd.to_numeric(team_rows["weight_lb"], errors="coerce").dropna().median() * 0.45359237)
        elif "weight_kg" in team_rows.columns:
            supplied_weight_kg = float(pd.to_numeric(team_rows["weight_kg"], errors="coerce").dropna().median())
        if "body_fat_pct" in team_rows.columns:
            supplied_body_fat = float(pd.to_numeric(team_rows["body_fat_pct"], errors="coerce").dropna().median() / 100.0)

    height_bias = 0.48 + 0.18 * quality_index + 0.12 * performance_index + role_bias
    height_m = supplied_height_m if supplied_height_m is not None and np.isfinite(supplied_height_m) else MIN_HEIGHT_M + (MAX_HEIGHT_M - MIN_HEIGHT_M) * _bounded(height_bias + rng.normal(0.0, 0.06), 0.0, 1.0)
    height_m = _bounded(height_m, MIN_HEIGHT_M, MAX_HEIGHT_M)

    body_fat_bias = 0.52 - 0.23 * performance_index - 0.12 * quality_index + rng.normal(0.0, 0.08)
    body_fat_pct = supplied_body_fat if supplied_body_fat is not None and np.isfinite(supplied_body_fat) else MIN_BODY_FAT + (MAX_BODY_FAT - MIN_BODY_FAT) * _bounded(body_fat_bias, 0.0, 1.0)
    body_fat_pct = _bounded(body_fat_pct, MIN_BODY_FAT, MAX_BODY_FAT)

    lean_index = _bounded(0.65 * quality_index + 0.35 * performance_index + rng.normal(0.0, 0.05), 0.0, 1.0)
    base_mass_bias = 0.28 + 0.42 * lean_index + 0.2 * ((height_m - MIN_HEIGHT_M) / (MAX_HEIGHT_M - MIN_HEIGHT_M))
    weight_kg = supplied_weight_kg if supplied_weight_kg is not None and np.isfinite(supplied_weight_kg) else MIN_WEIGHT_KG + (MAX_WEIGHT_KG - MIN_WEIGHT_KG) * _bounded(base_mass_bias, 0.0, 1.0)
    weight_kg = _bounded(weight_kg, MIN_WEIGHT_KG, MAX_WEIGHT_KG)

    bone_ratio = _bounded(0.12 + 0.05 * ((height_m - MIN_HEIGHT_M) / (MAX_HEIGHT_M - MIN_HEIGHT_M)) + rng.normal(0.0, 0.008), 0.1, 0.22)
    muscle_ratio = _bounded(0.42 + 0.24 * lean_index - 0.18 * body_fat_pct + rng.normal(0.0, 0.02), 0.35, 0.72)
    shoulder_width_m = _bounded(0.19 * height_m + 0.0012 * weight_kg + 0.18 * body_fat_pct, 0.33, 0.66)
    torso_depth_m = _bounded(0.12 * height_m + 0.0011 * weight_kg + 0.22 * body_fat_pct, 0.2, 0.52)
    torso_length_m = _bounded(0.29 * height_m, 0.45, 0.68)
    leg_length_m = _bounded(0.48 * height_m, 0.72, 1.05)

    return AvatarProfile(
        team=team,
        role=role,
        seed=body_seed,
        height_m=height_m,
        weight_kg=weight_kg,
        body_fat_pct=body_fat_pct,
        muscle_ratio=muscle_ratio,
        bone_ratio=bone_ratio,
        head_size_m=HEAD_SIZE_M,
        shoulder_width_m=shoulder_width_m,
        torso_depth_m=torso_depth_m,
        torso_length_m=torso_length_m,
        leg_length_m=leg_length_m,
    )