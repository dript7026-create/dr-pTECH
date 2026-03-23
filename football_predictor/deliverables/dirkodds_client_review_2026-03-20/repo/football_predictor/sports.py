from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import numpy as np


@dataclass(frozen=True)
class SportConfig:
    name: str
    display_name: str
    allows_draws: bool


SPORTS: Dict[str, SportConfig] = {
    "football": SportConfig(name="football", display_name="Football", allows_draws=True),
    "baseball": SportConfig(name="baseball", display_name="Baseball", allows_draws=False),
    "basketball": SportConfig(name="basketball", display_name="Basketball", allows_draws=False),
}

SPORT_ALIASES = {
    "soccer": "football",
    "footy": "football",
    "mlb": "baseball",
    "nba": "basketball",
    "hoops": "basketball",
}

PROBABILITY_COLUMNS = ["prob_away_win", "prob_draw", "prob_home_win"]


def normalize_sport(sport: Optional[str]) -> str:
    value = (sport or "football").strip().lower()
    value = SPORT_ALIASES.get(value, value)
    if value not in SPORTS:
        supported = ", ".join(sorted(SPORTS))
        raise ValueError(f"Unsupported sport '{sport}'. Expected one of: {supported}")
    return value


def get_sport_config(sport: Optional[str]) -> SportConfig:
    return SPORTS[normalize_sport(sport)]


def resolve_frame_sport(values: Optional[Iterable[object]], default: Optional[str] = "football") -> str:
    normalized = []
    source_values = [] if values is None else values
    for value in source_values:
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        normalized.append(normalize_sport(text))
    unique = sorted(set(normalized))
    if not unique:
        return normalize_sport(default)
    if len(unique) > 1:
        raise ValueError("Expected a single sport in the input frame.")
    return unique[0]


def outcome_label(code: int, sport: Optional[str]) -> str:
    if code == 0:
        return "Away Win"
    if code == 2:
        return "Home Win"
    if get_sport_config(sport).allows_draws:
        return "Draw"
    return "Draw"


def probability_matrix_from_classes(probabilities: np.ndarray, classes: Iterable[object]) -> np.ndarray:
    full = np.zeros((len(probabilities), 3), dtype=float)
    for index, label in enumerate(classes):
        full[:, int(label)] = probabilities[:, index]
    return full


def entropy_normalizer(sport: Optional[str]) -> float:
    config = get_sport_config(sport)
    return float(np.log(3.0 if config.allows_draws else 2.0))
