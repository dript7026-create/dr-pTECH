from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

import numpy as np
import pandas as pd

from .sport_rules import get_role_sequence
from .sports import normalize_sport


@dataclass(frozen=True)
class PlayerEntityState:
    entity_id: str
    squad_number: int
    role: str
    readiness: float
    fatigue: float
    hydration: float
    sodium_balance: float
    cramp_risk: float
    injury_risk: float
    discipline: float
    morale: float
    focus: float
    aggression: float
    grudge: float
    accident_risk: float
    confusion: float
    vision_disruption: float
    reaction_delay: float
    spatial_awareness: float
    coordination: float
    balance: float
    composure: float
    crowd_disruption: float
    decision_noise: float
    hesitation: float
    locomotion_integrity: float
    egosphere_id: float
    egosphere_ego: float
    egosphere_superego: float
    egosphere_resonance: float
    godai_pressure: float
    godai_mercy: float
    godai_novelty: float

    def to_dict(self) -> Dict[str, float | int | str]:
        return asdict(self)


@dataclass(frozen=True)
class TeamEntityState:
    team: str
    sport: str
    team_preparedness: float
    pregame_readiness: float
    fatigue_pressure: float
    hydration_state: float
    sodium_state: float
    morale_state: float
    discipline_state: float
    temper_pressure: float
    confusion_pressure: float
    perception_stability: float
    decision_cohesion: float
    crowd_noise_pressure: float
    coach_motivation: float
    coach_reflection: float
    coach_progressive_drive: float
    injury_pressure: float
    cramp_pressure: float
    egosphere_alignment: float
    godai_pressure: float
    godai_mercy: float
    godai_novelty: float
    artisapien_hook_ready: bool
    source_stat_signature: Dict[str, float]
    simulated_state_signature: Dict[str, float]
    delta_signature: Dict[str, float]
    influence_network: List[Dict[str, object]]
    roster: List[PlayerEntityState]

    def to_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["roster"] = [player.to_dict() for player in self.roster]
        return payload


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return float(np.clip(value, lower, upper))


def _stable_seed(*parts: str) -> int:
    text = "::".join(parts)
    value = 2166136261
    for char in text:
        value ^= ord(char)
        value = (value * 16777619) % (2 ** 32)
    return int(value)


def _row_value(row: pd.Series, key: str, default: float = 0.0) -> float:
    return float(pd.to_numeric(pd.Series([row.get(key, default)]), errors="coerce").fillna(default).iloc[0])


def _side_metrics(row: pd.Series, side: str) -> Dict[str, float]:
    quality = _row_value(row, f"{side}_player_quality", 0.0)
    sentiment = _row_value(row, f"media_sentiment_{side}", 0.0)
    buzz = _row_value(row, f"media_buzz_{side}", 0.0)
    goals_form = _row_value(row, f"{side}_goals_for_form", 1.2)
    weather = _row_value(row, "weather_severity", 0.0)
    form_edge = _row_value(row, "form_diff", 0.0) * (1.0 if side == "home" else -1.0)
    confidence = _row_value(row, f"prob_{side}_win" if side in {"home", "away"} else "confidence", 1.0 / 3.0)
    return {
        "quality": quality,
        "sentiment": sentiment,
        "buzz": buzz,
        "goals_form": goals_form,
        "weather": weather,
        "form_edge": form_edge,
        "confidence": confidence,
    }


def _coach_state(metrics: Dict[str, float], rng: np.random.Generator) -> Dict[str, float]:
    motivation = _bounded(0.5 + 0.18 * np.tanh(metrics["form_edge"]) + 0.12 * metrics["sentiment"] + rng.normal(0.0, 0.05))
    reflection = _bounded(0.46 + 0.1 * metrics["buzz"] + 0.08 * metrics["confidence"] + rng.normal(0.0, 0.04))
    progressive_drive = _bounded(0.44 + 0.14 * np.tanh(metrics["quality"]) + 0.09 * metrics["goals_form"] / 2.5 + rng.normal(0.0, 0.04))
    return {
        "motivation": motivation,
        "reflection": reflection,
        "progressive_drive": progressive_drive,
    }


def _build_source_stat_signature(metrics: Dict[str, float]) -> Dict[str, float]:
    return {
        "quality_signal": float(np.tanh(metrics["quality"])),
        "sentiment_signal": _bounded(0.5 + 0.5 * metrics["sentiment"]),
        "buzz_signal": _bounded(metrics["buzz"]),
        "form_signal": _bounded(metrics["goals_form"] / 3.0),
        "weather_drag": _bounded(metrics["weather"]),
        "confidence_signal": _bounded(metrics["confidence"]),
        "context_signal": _bounded(0.5 + 0.5 * np.tanh(metrics["form_edge"])),
    }


def _build_delta_signature(source_stat_signature: Dict[str, float], simulated_state_signature: Dict[str, float]) -> Dict[str, float]:
    mappings = {
        "quality_signal": "preparedness_signal",
        "sentiment_signal": "morale_signal",
        "buzz_signal": "temper_signal",
        "form_signal": "readiness_signal",
        "weather_drag": "fatigue_signal",
        "confidence_signal": "coach_signal",
        "context_signal": "egosphere_signal",
    }
    delta = {
        f"{source_key}_to_{target_key}": round(float(simulated_state_signature[target_key] - source_value), 4)
        for source_key, target_key in mappings.items()
        for source_value in [source_stat_signature[source_key]]
    }
    delta["delta_magnitude"] = round(
        float(
            np.mean(
                [
                    abs(simulated_state_signature[target_key] - source_stat_signature[source_key])
                    for source_key, target_key in mappings.items()
                ]
            )
        ),
        4,
    )
    return delta


def _build_influence_network(metrics: Dict[str, float], team_preparedness: float, morale_state: float, discipline_state: float, fatigue_pressure: float, hydration_state: float, sodium_state: float, coach: Dict[str, float], egosphere_alignment: float) -> List[Dict[str, object]]:
    return [
        {"source": "quality_signal", "target": "team_preparedness", "weight": round(0.34 + 0.22 * abs(np.tanh(metrics["quality"])), 3)},
        {"source": "weather_drag", "target": "fatigue_pressure", "weight": round(0.28 + 0.3 * metrics["weather"], 3)},
        {"source": "hydration_state", "target": "sodium_state", "weight": round(0.18 + 0.24 * hydration_state, 3)},
        {"source": "sodium_state", "target": "cramp_pressure", "weight": round(0.24 + 0.24 * (1.0 - sodium_state), 3)},
        {"source": "sentiment_signal", "target": "morale_state", "weight": round(0.24 + 0.2 * abs(metrics["sentiment"]), 3)},
        {"source": "buzz_signal", "target": "discipline_state", "weight": round(0.18 + 0.16 * metrics["buzz"], 3)},
        {"source": "coach_motivation", "target": "team_preparedness", "weight": round(0.2 + 0.18 * coach["motivation"], 3)},
        {"source": "coach_reflection", "target": "egosphere_alignment", "weight": round(0.2 + 0.16 * coach["reflection"], 3)},
        {"source": "morale_state", "target": "egosphere_alignment", "weight": round(0.16 + 0.18 * morale_state, 3)},
        {"source": "discipline_state", "target": "egosphere_alignment", "weight": round(0.16 + 0.18 * discipline_state, 3)},
        {"source": "fatigue_pressure", "target": "team_preparedness", "weight": round(0.14 + 0.2 * fatigue_pressure, 3)},
    ]


def _role_bias(sport: str, role: str) -> tuple[float, float, float, float]:
    if sport == "baseball":
        return {
            "P": (0.03, 0.08, 0.12, -0.02),
            "C": (-0.02, 0.05, 0.14, -0.04),
            "1B": (0.02, 0.03, 0.08, 0.02),
            "2B": (0.03, 0.05, 0.06, 0.04),
            "3B": (0.04, 0.05, 0.04, 0.06),
            "SS": (0.04, 0.06, 0.06, 0.06),
            "LF": (0.06, 0.07, 0.0, 0.08),
            "CF": (0.07, 0.08, 0.02, 0.08),
            "RF": (0.06, 0.07, 0.0, 0.08),
        }.get(role, (0.0, 0.0, 0.0, 0.0))
    if sport == "basketball":
        return {
            "PG": (0.08, 0.06, 0.04, 0.08),
            "SG": (0.08, 0.05, 0.02, 0.1),
            "SF": (0.06, 0.06, 0.04, 0.08),
            "PF": (0.04, 0.07, 0.08, 0.04),
            "C": (0.03, 0.08, 0.1, 0.0),
        }.get(role, (0.0, 0.0, 0.0, 0.0))
    return {
        "GK": (-0.08, -0.05, 0.12, -0.12),
        "CB": (-0.03, 0.04, 0.1, -0.02),
        "LB": (0.02, 0.06, 0.03, 0.04),
        "RB": (0.02, 0.06, 0.03, 0.04),
        "DM": (0.0, 0.02, 0.08, 0.02),
        "CM": (0.03, 0.04, 0.02, 0.03),
        "AM": (0.05, 0.03, -0.02, 0.08),
        "LW": (0.08, 0.07, -0.04, 0.12),
        "RW": (0.08, 0.07, -0.04, 0.12),
        "ST": (0.1, 0.05, -0.06, 0.14),
    }.get(role, (0.0, 0.0, 0.0, 0.0))


def build_team_entity_state(team: str, row: pd.Series, side: str) -> TeamEntityState:
    sport = normalize_sport(row.get("sport", "football"))
    metrics = _side_metrics(row, side)
    rng = np.random.default_rng(_stable_seed(team, side, str(row.get("date", ""))))
    coach = _coach_state(metrics, rng)
    source_stat_signature = _build_source_stat_signature(metrics)

    base_readiness = _bounded(0.56 + 0.16 * np.tanh(metrics["quality"]) + 0.14 * metrics["sentiment"] + 0.08 * coach["motivation"] - 0.08 * metrics["weather"])
    fatigue_pressure = _bounded(0.24 + 0.08 * metrics["buzz"] + 0.06 * metrics["weather"] + rng.normal(0.0, 0.03))
    hydration_state = _bounded(0.74 - 0.12 * metrics["weather"] + 0.05 * coach["reflection"] + rng.normal(0.0, 0.03))
    sodium_state = _bounded(0.71 - 0.11 * metrics["weather"] + 0.03 * coach["progressive_drive"] + rng.normal(0.0, 0.025))
    morale_state = _bounded(0.52 + 0.18 * metrics["sentiment"] + 0.12 * np.tanh(metrics["form_edge"]) + 0.1 * coach["motivation"])
    discipline_state = _bounded(0.58 - 0.08 * metrics["buzz"] + 0.09 * coach["reflection"] + rng.normal(0.0, 0.03))
    temper_pressure = _bounded(0.28 + 0.16 * (1.0 - discipline_state) + 0.08 * metrics["buzz"] + rng.normal(0.0, 0.03))
    confusion_pressure = _bounded(0.14 + 0.12 * metrics["weather"] + 0.1 * metrics["buzz"] + 0.1 * (1.0 - discipline_state) + rng.normal(0.0, 0.03))
    perception_stability = _bounded(0.7 - 0.16 * metrics["weather"] - 0.08 * metrics["buzz"] + 0.08 * coach["reflection"] + rng.normal(0.0, 0.03))
    readiness = base_readiness
    injury_pressure = _bounded(0.14 + 0.24 * fatigue_pressure + 0.18 * (1.0 - readiness) + 0.08 * metrics["weather"])
    cramp_pressure = _bounded(0.1 + 0.3 * (1.0 - hydration_state) + 0.24 * (1.0 - sodium_state) + 0.12 * fatigue_pressure)
    team_preparedness = _bounded(0.45 * base_readiness + 0.2 * morale_state + 0.15 * discipline_state + 0.1 * coach["motivation"] + 0.1 * coach["progressive_drive"])
    egosphere_alignment = _bounded(0.4 * discipline_state + 0.32 * morale_state + 0.28 * coach["reflection"])
    decision_cohesion = _bounded(0.42 * team_preparedness + 0.2 * discipline_state + 0.2 * morale_state + 0.18 * egosphere_alignment)
    crowd_noise_pressure = _bounded(0.16 + 0.18 * metrics["buzz"] + 0.08 * abs(metrics["sentiment"]) + rng.normal(0.0, 0.03))
    godai_pressure = _bounded(0.34 + 0.26 * coach["progressive_drive"] + 0.14 * temper_pressure)
    godai_mercy = _bounded(0.32 + 0.22 * discipline_state + 0.12 * coach["reflection"])
    godai_novelty = _bounded(0.36 + 0.18 * coach["progressive_drive"] + 0.12 * metrics["buzz"])
    simulated_state_signature = {
        "preparedness_signal": round(team_preparedness, 4),
        "readiness_signal": round(base_readiness, 4),
        "fatigue_signal": round(fatigue_pressure, 4),
        "hydration_signal": round(hydration_state, 4),
        "sodium_signal": round(sodium_state, 4),
        "morale_signal": round(morale_state, 4),
        "discipline_signal": round(discipline_state, 4),
        "temper_signal": round(temper_pressure, 4),
        "coach_signal": round((coach["motivation"] + coach["reflection"] + coach["progressive_drive"]) / 3.0, 4),
        "egosphere_signal": round(egosphere_alignment, 4),
        "confusion_signal": round(confusion_pressure, 4),
        "perception_signal": round(perception_stability, 4),
        "decision_signal": round(decision_cohesion, 4),
        "crowd_signal": round(crowd_noise_pressure, 4),
    }
    delta_signature = _build_delta_signature(source_stat_signature, simulated_state_signature)
    influence_network = _build_influence_network(
        metrics,
        team_preparedness,
        morale_state,
        discipline_state,
        fatigue_pressure,
        hydration_state,
        sodium_state,
        coach,
        egosphere_alignment,
    )

    roster: List[PlayerEntityState] = []
    for index, role in enumerate(get_role_sequence(sport), start=1):
        role_bias = _role_bias(sport, role)
        performance = _bounded(0.5 + 0.16 * np.tanh(metrics["quality"]) + role_bias[0] + rng.normal(0.0, 0.05))
        fatigue = _bounded(fatigue_pressure + role_bias[1] + rng.normal(0.0, 0.04))
        hydration = _bounded(hydration_state - 0.04 * role_bias[1] + rng.normal(0.0, 0.03))
        sodium_balance = _bounded(sodium_state - 0.03 * role_bias[1] + rng.normal(0.0, 0.03))
        discipline = _bounded(discipline_state + role_bias[2] + rng.normal(0.0, 0.04))
        aggression = _bounded(0.34 + 0.22 * temper_pressure - 0.14 * discipline + role_bias[3] + rng.normal(0.0, 0.05))
        focus = _bounded(0.5 + 0.18 * performance + 0.1 * discipline - 0.1 * fatigue + rng.normal(0.0, 0.04))
        morale = _bounded(morale_state + 0.06 * performance + rng.normal(0.0, 0.04))
        readiness = _bounded(base_readiness + 0.08 * performance - 0.08 * fatigue + 0.05 * focus + rng.normal(0.0, 0.03))
        grudge = _bounded(0.22 + 0.18 * metrics["buzz"] + 0.1 * aggression + rng.normal(0.0, 0.04))
        confusion = _bounded(confusion_pressure + 0.08 * (1.0 - discipline) + 0.06 * aggression + rng.normal(0.0, 0.03))
        vision_disruption = _bounded(0.08 + 0.24 * (1.0 - perception_stability) + 0.08 * metrics["weather"] + 0.05 * fatigue + rng.normal(0.0, 0.03))
        reaction_delay = _bounded(0.08 + 0.2 * fatigue + 0.1 * confusion + 0.08 * (1.0 - focus) + rng.normal(0.0, 0.03))
        spatial_awareness = _bounded(0.48 + 0.18 * focus + 0.12 * discipline - 0.12 * vision_disruption - 0.08 * fatigue + rng.normal(0.0, 0.03))
        coordination = _bounded(0.56 + 0.12 * readiness - 0.1 * fatigue + 0.08 * hydration + 0.06 * sodium_balance - 0.08 * confusion + rng.normal(0.0, 0.03))
        accident_risk = _bounded(0.08 + 0.16 * fatigue + 0.1 * (1.0 - focus) + 0.08 * aggression)
        injury_risk = _bounded(0.08 + 0.2 * fatigue + 0.18 * (1.0 - readiness) + 0.14 * (1.0 - hydration))
        cramp_risk = _bounded(0.06 + 0.24 * (1.0 - hydration) + 0.18 * (1.0 - sodium_balance) + 0.1 * fatigue)
        balance = _bounded(0.56 + 0.12 * readiness + 0.08 * coordination - 0.12 * fatigue - 0.12 * accident_risk + rng.normal(0.0, 0.03))
        composure = _bounded(0.48 + 0.14 * morale + 0.14 * discipline - 0.1 * aggression - 0.12 * confusion + rng.normal(0.0, 0.03))
        crowd_disruption = _bounded(crowd_noise_pressure + 0.08 * (1.0 - focus) + 0.08 * (1.0 - composure) + rng.normal(0.0, 0.03))
        decision_noise = _bounded(0.1 + 0.18 * confusion + 0.16 * reaction_delay + 0.12 * (1.0 - spatial_awareness) + 0.08 * crowd_disruption)
        hesitation = _bounded(0.08 + 0.18 * decision_noise + 0.16 * (1.0 - composure) + 0.08 * (1.0 - readiness) + rng.normal(0.0, 0.03))
        locomotion_integrity = _bounded(0.42 * readiness + 0.18 * coordination + 0.18 * balance + 0.12 * hydration + 0.1 * sodium_balance - 0.16 * fatigue)
        roster.append(
            PlayerEntityState(
                entity_id=f"{team.lower().replace(' ', '_')}_{index:02d}",
                squad_number=index,
                role=role,
                readiness=readiness,
                fatigue=fatigue,
                hydration=hydration,
                sodium_balance=sodium_balance,
                cramp_risk=cramp_risk,
                injury_risk=injury_risk,
                discipline=discipline,
                morale=morale,
                focus=focus,
                aggression=aggression,
                grudge=grudge,
                accident_risk=accident_risk,
                confusion=confusion,
                vision_disruption=vision_disruption,
                reaction_delay=reaction_delay,
                spatial_awareness=spatial_awareness,
                coordination=coordination,
                balance=balance,
                composure=composure,
                crowd_disruption=crowd_disruption,
                decision_noise=decision_noise,
                hesitation=hesitation,
                locomotion_integrity=locomotion_integrity,
                egosphere_id=_bounded(0.4 + 0.18 * aggression + 0.06 * grudge),
                egosphere_ego=_bounded(0.46 + 0.16 * focus + 0.08 * performance),
                egosphere_superego=_bounded(0.42 + 0.22 * discipline + 0.1 * coach["reflection"]),
                egosphere_resonance=_bounded(0.4 + 0.16 * morale + 0.1 * coach["motivation"]),
                godai_pressure=_bounded(godai_pressure + 0.08 * aggression),
                godai_mercy=_bounded(godai_mercy + 0.08 * discipline),
                godai_novelty=_bounded(godai_novelty + 0.06 * performance),
            )
        )

    return TeamEntityState(
        team=team,
        sport=sport,
        team_preparedness=team_preparedness,
        pregame_readiness=base_readiness,
        fatigue_pressure=fatigue_pressure,
        hydration_state=hydration_state,
        sodium_state=sodium_state,
        morale_state=morale_state,
        discipline_state=discipline_state,
        temper_pressure=temper_pressure,
        confusion_pressure=confusion_pressure,
        perception_stability=perception_stability,
        decision_cohesion=decision_cohesion,
        crowd_noise_pressure=crowd_noise_pressure,
        coach_motivation=coach["motivation"],
        coach_reflection=coach["reflection"],
        coach_progressive_drive=coach["progressive_drive"],
        injury_pressure=injury_pressure,
        cramp_pressure=cramp_pressure,
        egosphere_alignment=egosphere_alignment,
        godai_pressure=godai_pressure,
        godai_mercy=godai_mercy,
        godai_novelty=godai_novelty,
        artisapien_hook_ready=False,
        source_stat_signature=source_stat_signature,
        simulated_state_signature=simulated_state_signature,
        delta_signature=delta_signature,
        influence_network=influence_network,
        roster=roster,
    )


def build_match_entity_states(row: pd.Series) -> Dict[str, TeamEntityState]:
    return {
        "home": build_team_entity_state(str(row["home_team"]), row, "home"),
        "away": build_team_entity_state(str(row["away_team"]), row, "away"),
    }


def summarize_match_entity_effects(states: Dict[str, TeamEntityState]) -> Dict[str, float]:
    home = states["home"]
    away = states["away"]
    home_attack = 0.18 * home.team_preparedness + 0.1 * home.morale_state + 0.06 * home.coach_motivation - 0.1 * home.fatigue_pressure - 0.06 * home.cramp_pressure
    away_attack = 0.18 * away.team_preparedness + 0.1 * away.morale_state + 0.06 * away.coach_motivation - 0.1 * away.fatigue_pressure - 0.06 * away.cramp_pressure
    draw_bias = 0.05 * ((home.discipline_state + away.discipline_state) / 2.0) + 0.04 * ((home.injury_pressure + away.injury_pressure) / 2.0)
    discipline_swing = (home.temper_pressure - away.temper_pressure) * 0.08
    home_error_pressure = 0.34 * home.confusion_pressure + 0.22 * (1.0 - home.perception_stability) + 0.18 * home.crowd_noise_pressure + 0.14 * (1.0 - home.decision_cohesion)
    away_error_pressure = 0.34 * away.confusion_pressure + 0.22 * (1.0 - away.perception_stability) + 0.18 * away.crowd_noise_pressure + 0.14 * (1.0 - away.decision_cohesion)
    return {
        "home_attack_delta": float(np.clip(home_attack - away_attack * 0.35 - away_error_pressure * 0.06, -0.45, 0.55)),
        "away_attack_delta": float(np.clip(away_attack - home_attack * 0.35 - home_error_pressure * 0.06, -0.45, 0.55)),
        "draw_bias": float(np.clip(draw_bias, 0.0, 0.14)),
        "discipline_swing": float(np.clip(discipline_swing, -0.12, 0.12)),
        "salt_variance": float(np.clip(((home.sodium_state + away.sodium_state) / 2.0) - 0.7, -0.15, 0.12)),
        "home_error_pressure": float(np.clip(home_error_pressure, 0.0, 1.0)),
        "away_error_pressure": float(np.clip(away_error_pressure, 0.0, 1.0)),
        "perception_gap": float(np.clip(home.perception_stability - away.perception_stability, -0.4, 0.4)),
    }


def synthesize_match_incidents(states: Dict[str, TeamEntityState], rng: np.random.Generator) -> List[Dict[str, object]]:
    incidents: List[Dict[str, object]] = []
    for side, team_state in states.items():
        team = team_state.team
        for player in team_state.roster:
            if player.cramp_risk > 0.58 and rng.random() < (player.cramp_risk - 0.54) * 0.18:
                incidents.append(
                    {
                        "minute": float(round(rng.uniform(54.0, 88.0), 2)),
                        "team": team,
                        "side": side,
                        "entity_id": player.entity_id,
                        "role": player.role,
                        "incident_type": "cramp",
                        "severity": float(round(player.cramp_risk, 3)),
                        "note": "Abstract hydration-electrolyte fatigue event.",
                    }
                )
            if player.injury_risk > 0.54 and rng.random() < (player.injury_risk - 0.5) * 0.15:
                incidents.append(
                    {
                        "minute": float(round(rng.uniform(18.0, 84.0), 2)),
                        "team": team,
                        "side": side,
                        "entity_id": player.entity_id,
                        "role": player.role,
                        "incident_type": "minor_injury",
                        "severity": float(round(player.injury_risk, 3)),
                        "note": "Abstract non-medical contact/strain event.",
                    }
                )
            temper_trigger = 0.5 * player.aggression + 0.35 * player.grudge + 0.15 * (1.0 - player.discipline)
            if temper_trigger > 0.52 and rng.random() < (temper_trigger - 0.48) * 0.13:
                incidents.append(
                    {
                        "minute": float(round(rng.uniform(8.0, 90.0), 2)),
                        "team": team,
                        "side": side,
                        "entity_id": player.entity_id,
                        "role": player.role,
                        "incident_type": "discipline_penalty",
                        "severity": float(round(temper_trigger, 3)),
                        "note": "Abstract temper or grudge penalty event.",
                    }
                )
            if player.accident_risk > 0.44 and rng.random() < (player.accident_risk - 0.4) * 0.09:
                incidents.append(
                    {
                        "minute": float(round(rng.uniform(6.0, 90.0), 2)),
                        "team": team,
                        "side": side,
                        "entity_id": player.entity_id,
                        "role": player.role,
                        "incident_type": "accident",
                        "severity": float(round(player.accident_risk, 3)),
                        "note": "Abstract loss-of-balance or collision event.",
                    }
                )
            if player.confusion > 0.56 and rng.random() < (player.confusion - 0.5) * 0.12:
                incidents.append(
                    {
                        "minute": float(round(rng.uniform(10.0, 90.0), 2)),
                        "team": team,
                        "side": side,
                        "entity_id": player.entity_id,
                        "role": player.role,
                        "incident_type": "misread_play",
                        "severity": float(round(player.confusion, 3)),
                        "note": "Abstract confusion or anticipation breakdown event.",
                    }
                )
            if player.vision_disruption > 0.56 and rng.random() < (player.vision_disruption - 0.5) * 0.11:
                incidents.append(
                    {
                        "minute": float(round(rng.uniform(12.0, 90.0), 2)),
                        "team": team,
                        "side": side,
                        "entity_id": player.entity_id,
                        "role": player.role,
                        "incident_type": "vision_break",
                        "severity": float(round(player.vision_disruption, 3)),
                        "note": "Abstract line-of-sight or tracking disruption event.",
                    }
                )
            if player.hesitation > 0.58 and rng.random() < (player.hesitation - 0.52) * 0.11:
                incidents.append(
                    {
                        "minute": float(round(rng.uniform(6.0, 90.0), 2)),
                        "team": team,
                        "side": side,
                        "entity_id": player.entity_id,
                        "role": player.role,
                        "incident_type": "hesitation_window",
                        "severity": float(round(player.hesitation, 3)),
                        "note": "Abstract decision-lag or lost-window event.",
                    }
                )
    incidents.sort(key=lambda item: (item["minute"], item["team"], item["entity_id"]))
    return incidents[:10]


def build_artisapien_hooks(states: Dict[str, TeamEntityState]) -> Dict[str, object]:
    return {
        "enabled": False,
        "license_required": True,
        "governing_body_approval_required": True,
        "decision_protocol": "egosphere_artisapiens_scaffold",
        "entity_mappings": [
            {
                "team": team_state.team,
                "roster_size": len(team_state.roster),
                "status": "placeholder_only",
            }
            for team_state in states.values()
        ],
        "notes": [
            "Placeholder hooks only. Do not map to real players without licensed data and deployment-side approval inputs.",
            "This layer is abstract and non-identifying by default.",
            "Decision-spectrum fields can drive simulation behavior without claiming access to any real athlete inner state.",
        ],
    }