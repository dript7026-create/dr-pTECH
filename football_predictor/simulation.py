from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping

import numpy as np
import pandas as pd

from .challenge_mode import build_challenge_cue_profile
from .entity_state import (
    build_artisapien_hooks,
    build_match_entity_states,
    summarize_match_entity_effects,
    synthesize_match_incidents,
)
from .regulated_session import build_regulated_session_hooks
from .sport_rules import get_action_catalog, get_sport_ruleset
from .sports import entropy_normalizer, get_sport_config, normalize_sport, outcome_label


PLAY_SURFACE = {
    "football": {"length": 105.0, "width": 68.0, "target_height": 2.44},
    "baseball": {"length": 127.0, "width": 127.0, "target_height": 3.2},
    "basketball": {"length": 94.0, "width": 50.0, "target_height": 3.05},
}
BALL_GRAVITY = 9.81

EVENT_ACTIONS = {
    "football": {"build": ["short_pass", "switch_pass", "through_ball", "cross"], "finish": ["shoot", "header", "release"]},
    "baseball": {"build": ["set_pitch", "receive_pitch", "relay_throw", "lead_off"], "finish": ["swing_contact", "drive_gap", "sacrifice_fly"]},
    "basketball": {"build": ["dribble_probe", "swing_pass", "post_entry", "screen_reject"], "finish": ["pull_up", "catch_and_shoot", "layup", "dunk"]},
}


@dataclass
class SimulationConfig:
    simulation_count: int = 2000
    time_step: float = 0.08
    drag: float = 0.015
    restitution: float = 0.62


def _expected_goals_from_row(row: Mapping[str, object], entity_effects: Dict[str, float] | None = None) -> tuple[float, float]:
    effects = entity_effects or {}
    total_goals = 2.35
    total_goals += 0.12 * float(row.get("home_goals_for_form", 0.0) + row.get("away_goals_for_form", 0.0) - 2.4)
    total_goals -= 0.15 * float(row.get("weather_severity", 0.0))
    total_goals += 0.07 * float(row.get("home_player_quality", 0.0) + row.get("away_player_quality", 0.0))
    total_goals += 0.24 * float(effects.get("salt_variance", 0.0))
    total_goals += 0.15 * float(effects.get("draw_bias", 0.0))
    total_goals -= 0.08 * float(effects.get("home_error_pressure", 0.0) + effects.get("away_error_pressure", 0.0))
    total_goals = float(np.clip(total_goals, 1.2, 4.8))

    edge = (
        0.65 * (float(row["prob_home_win"]) - float(row["prob_away_win"]))
        + 0.08 * np.tanh(float(row.get("form_diff", 0.0)))
        + 0.1 * np.tanh(float(row.get("player_quality_diff", 0.0)))
        + float(effects.get("home_attack_delta", 0.0))
        - float(effects.get("away_attack_delta", 0.0))
        + float(effects.get("discipline_swing", 0.0))
        + 0.08 * float(effects.get("perception_gap", 0.0))
    )
    home_share = float(np.clip(0.5 + edge, 0.18, 0.82))
    home_xg = float(np.clip(total_goals * home_share, 0.2, 4.2))
    away_xg = float(np.clip(total_goals - home_xg, 0.2, 4.2))
    return home_xg, away_xg


def _generate_goal_minutes(goal_count: int, rng: np.random.Generator) -> List[float]:
    if goal_count <= 0:
        return []
    samples = np.sort(rng.uniform(2.0, 92.0, size=goal_count))
    return [float(round(sample, 2)) for sample in samples]


def _ballistic_trajectory(start: np.ndarray, target: np.ndarray, rng: np.random.Generator, config: SimulationConfig, vertical_range: tuple[float, float] = (4.5, 9.0)) -> List[Dict[str, float]]:
    duration = float(rng.uniform(0.6, 1.8))
    frames: List[Dict[str, float]] = []
    horizontal = (target[:2] - start[:2]) / duration
    vertical_velocity = float(rng.uniform(*vertical_range))
    for t in np.arange(0.0, duration + config.time_step, config.time_step):
        x = start[0] + horizontal[0] * t
        y = start[1] + horizontal[1] * t
        z = start[2] + vertical_velocity * t - 0.5 * BALL_GRAVITY * t * t
        z *= max(0.55, 1.0 - config.drag * t)
        if z < 0.0:
            z = abs(z) * config.restitution
        frames.append({"t": float(round(t, 3)), "x": float(round(x, 3)), "y": float(round(y, 3)), "z": float(round(z, 3))})
    return frames


def _synthesize_football_trajectories(home_goals: int, away_goals: int, rng: np.random.Generator, config: SimulationConfig) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    for team_name, goal_count, attacking_from_left in [("home", home_goals, True), ("away", away_goals, False)]:
        for minute in _generate_goal_minutes(goal_count, rng):
            start_x = rng.uniform(68.0, 88.0) if attacking_from_left else rng.uniform(17.0, 37.0)
            target_x = PLAY_SURFACE["football"]["length"] if attacking_from_left else 0.0
            start = np.array([start_x, rng.uniform(18.0, 50.0), 0.18])
            target = np.array([target_x, PLAY_SURFACE["football"]["width"] / 2.0 + rng.uniform(-3.6, 3.6), rng.uniform(0.4, PLAY_SURFACE["football"]["target_height"])])
            events.append(
                {
                    "team": team_name,
                    "minute": minute,
                    "event_type": "goal_shot",
                    "trajectory": _ballistic_trajectory(start, target, rng, config),
                }
            )
    events.sort(key=lambda item: item["minute"])
    return events


def _synthesize_basketball_trajectories(home_scores: int, away_scores: int, rng: np.random.Generator, config: SimulationConfig) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    court = PLAY_SURFACE["basketball"]
    for team_name, score_count, shooting_right in [("home", home_scores, True), ("away", away_scores, False)]:
        for minute in _generate_goal_minutes(score_count, rng):
            hoop_x = court["length"] - 5.25 if shooting_right else 5.25
            start_x = rng.uniform(court["length"] * 0.58, court["length"] * 0.78) if shooting_right else rng.uniform(court["length"] * 0.22, court["length"] * 0.42)
            start = np.array([start_x, court["width"] / 2.0 + rng.uniform(-12.0, 12.0), 2.0])
            target = np.array([hoop_x, court["width"] / 2.0, court["target_height"]])
            events.append(
                {
                    "team": team_name,
                    "minute": minute,
                    "event_type": "basket_shot",
                    "trajectory": _ballistic_trajectory(start, target, rng, config, vertical_range=(5.5, 9.5)),
                }
            )
    events.sort(key=lambda item: item["minute"])
    return events


def _synthesize_baseball_trajectories(home_scores: int, away_scores: int, rng: np.random.Generator, config: SimulationConfig) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    field = PLAY_SURFACE["baseball"]
    home_plate = np.array([14.0, 14.0, 1.0])
    for team_name, score_count in [("home", home_scores), ("away", away_scores)]:
        for minute in _generate_goal_minutes(score_count, rng):
            angle = float(rng.uniform(np.pi / 6.0, np.pi / 3.0))
            distance = float(rng.uniform(60.0, 110.0))
            target = np.array([
                home_plate[0] + np.cos(angle) * distance,
                home_plate[1] + np.sin(angle) * distance,
                rng.uniform(3.0, field["target_height"]),
            ])
            target[0] = float(np.clip(target[0], 0.0, field["length"]))
            target[1] = float(np.clip(target[1], 0.0, field["width"]))
            events.append(
                {
                    "team": team_name,
                    "minute": minute,
                    "event_type": "scoring_hit",
                    "trajectory": _ballistic_trajectory(home_plate, target, rng, config, vertical_range=(8.0, 14.0)),
                }
            )
    events.sort(key=lambda item: item["minute"])
    return events


def _synthesize_event_trajectories(home_scores: int, away_scores: int, sport: str, rng: np.random.Generator, config: SimulationConfig) -> List[Dict[str, object]]:
    if sport == "basketball":
        return _synthesize_basketball_trajectories(home_scores, away_scores, rng, config)
    if sport == "baseball":
        return _synthesize_baseball_trajectories(home_scores, away_scores, rng, config)
    return _synthesize_football_trajectories(home_scores, away_scores, rng, config)


def _choose_event_phase(sport: str, event_index: int, scoring: bool) -> str:
    ruleset = get_sport_ruleset(sport)
    phases = list(ruleset["phase_states"])
    if scoring:
        scoring_map = {
            "football": "finishing_sequence",
            "baseball": "scoring_contact",
            "basketball": "finishing_sequence",
        }
        return scoring_map[sport]
    return str(phases[event_index % len(phases)])


def _event_attention_prompt(sport: str, attention_focus: str, pressure_window: str, phase_state: str) -> str:
    if sport == "football":
        return f"Watch both lines and react to the {attention_focus.replace('_', ' ')} during {phase_state.replace('_', ' ')}."
    if sport == "baseball":
        return f"Track runner and fielder pressure through the {pressure_window.replace('_', ' ')} window."
    return f"Read weak-side help and ball pressure through the {phase_state.replace('_', ' ')}."


def _build_spectator_cues(
    sport: str,
    entity_effects: Dict[str, float],
    ruleset: Dict[str, object],
    event_trajectories: List[Dict[str, object]],
) -> Dict[str, object]:
    focus_load = float(
        np.clip(
            0.34 * entity_effects.get("home_error_pressure", 0.0)
            + 0.34 * entity_effects.get("away_error_pressure", 0.0)
            + 0.18 * abs(entity_effects.get("perception_gap", 0.0))
            + 0.14 * abs(entity_effects.get("discipline_swing", 0.0)) * 4.0,
            0.0,
            1.0,
        )
    )
    if sport == "football":
        focus_target = "ball_side_lane"
    elif sport == "baseball":
        focus_target = "base_path_pressure"
    else:
        focus_target = "paint_to_perimeter"
    top_phase = event_trajectories[0].get("phase_state") if event_trajectories else ruleset["phase_states"][0]
    return {
        "mode": "attention_reactive_broadcast",
        "focus_style": "whole_simulation_dual_team",
        "focus_target": focus_target,
        "focus_load": round(focus_load, 4),
        "top_phase": top_phase,
        "spectator_prompt": _event_attention_prompt(sport, focus_target, "tight_window" if focus_load > 0.58 else "standard_window", str(top_phase)),
    }


def _annotate_event_trajectories(
    trajectories: List[Dict[str, object]],
    sport: str,
    entity_effects: Dict[str, float],
    rng: np.random.Generator,
) -> List[Dict[str, object]]:
    annotated: List[Dict[str, object]] = []
    home_error = float(entity_effects.get("home_error_pressure", 0.0))
    away_error = float(entity_effects.get("away_error_pressure", 0.0))
    for index, event in enumerate(trajectories):
        team = str(event.get("team", "home"))
        pressure = float(np.clip((away_error if team == "home" else home_error) * 0.58 + abs(entity_effects.get("discipline_swing", 0.0)) * 1.8 + rng.uniform(0.08, 0.22), 0.0, 1.0))
        error_window = float(np.clip((home_error if team == "home" else away_error) * 0.44 + rng.uniform(0.04, 0.18), 0.0, 1.0))
        if pressure < 0.34:
            pressure_window = "wide_window"
        elif pressure < 0.62:
            pressure_window = "standard_window"
        else:
            pressure_window = "tight_window"
        if sport == "football":
            attention_focus = "final_third_press" if pressure > 0.56 else "central_build_lane"
        elif sport == "baseball":
            attention_focus = "runner_fielder_clash" if pressure > 0.56 else "flight_path_read"
        else:
            attention_focus = "rim_pressure" if pressure > 0.56 else "weak_side_shift"
        phase_state = _choose_event_phase(sport, index, scoring=True)
        build_action = EVENT_ACTIONS[sport]["build"][index % len(EVENT_ACTIONS[sport]["build"])]
        finish_action = EVENT_ACTIONS[sport]["finish"][index % len(EVENT_ACTIONS[sport]["finish"])]
        hotspot = event.get("trajectory", [])[-1] if event.get("trajectory") else {"x": 0.0, "y": 0.0, "z": 0.0}
        enriched = dict(event)
        enriched.update(
            {
                "phase_state": phase_state,
                "build_action": build_action,
                "primary_action": finish_action,
                "pressure_window": pressure_window,
                "attention_focus": attention_focus,
                "reflex_intensity": round(float(np.clip(0.52 * pressure + 0.48 * error_window, 0.0, 1.0)), 4),
                "error_window": round(error_window, 4),
                "focus_radius": round(float(np.clip(4.0 + 8.0 * pressure, 4.0, 12.0)), 3),
                "hotspot": {"x": float(hotspot.get("x", 0.0)), "y": float(hotspot.get("y", 0.0)), "z": float(hotspot.get("z", 0.0))},
                "spectator_prompt": _event_attention_prompt(sport, attention_focus, pressure_window, phase_state),
            }
        )
        annotated.append(enriched)
    return annotated


def simulate_match(row: Mapping[str, object], config: SimulationConfig | None = None, random_state: int = 42) -> Dict[str, object]:
    sim_config = config or SimulationConfig()
    rng = np.random.default_rng(random_state)
    sport = normalize_sport(row.get("sport", "football"))
    match_timestamp = pd.to_datetime(row.get("date"), errors="coerce")
    allows_draws = get_sport_config(sport).allows_draws
    entity_states = build_match_entity_states(row)
    entity_effects = summarize_match_entity_effects(entity_states)
    ruleset = get_sport_ruleset(sport)
    home_xg, away_xg = _expected_goals_from_row(row, entity_effects=entity_effects)
    home_goals = rng.poisson(home_xg, size=sim_config.simulation_count)
    away_goals = rng.poisson(away_xg, size=sim_config.simulation_count)

    if not allows_draws:
        tie_mask = home_goals == away_goals
        if np.any(tie_mask):
            home_edge = float(row.get("prob_home_win", 0.5))
            away_edge = float(row.get("prob_away_win", 0.5))
            home_tiebreak_share = home_edge / max(home_edge + away_edge, 1e-6)
            home_extra = rng.random(np.count_nonzero(tie_mask)) < home_tiebreak_share
            tied_home = home_goals[tie_mask]
            tied_away = away_goals[tie_mask]
            tied_home = tied_home + home_extra.astype(int)
            tied_away = tied_away + (~home_extra).astype(int)
            home_goals[tie_mask] = tied_home
            away_goals[tie_mask] = tied_away

    home_win_rate = float(np.mean(home_goals > away_goals))
    draw_rate = float(np.mean(home_goals == away_goals)) if allows_draws else 0.0
    away_win_rate = float(np.mean(home_goals < away_goals))

    score_pairs, counts = np.unique(np.column_stack([home_goals, away_goals]), axis=0, return_counts=True)
    most_likely_index = int(np.argmax(counts))
    most_likely_score = score_pairs[most_likely_index]
    trajectories = _synthesize_event_trajectories(int(most_likely_score[0]), int(most_likely_score[1]), sport, rng, sim_config)
    trajectories = _annotate_event_trajectories(trajectories, sport, entity_effects, rng)
    spectator_cues = _build_spectator_cues(sport, entity_effects, ruleset, trajectories)
    incidents = synthesize_match_incidents(entity_states, rng)
    regulated_session = build_regulated_session_hooks(row, entity_effects, trajectories, incidents, entity_states)
    challenge_cues = build_challenge_cue_profile(row, {"regulated_session": regulated_session, "entity_effects": entity_effects, "spectator_cues": spectator_cues})

    return {
        "sport": sport,
        "home_team": row["home_team"],
        "away_team": row["away_team"],
        "match_date": str(match_timestamp.date()) if pd.notna(match_timestamp) else None,
        "expected_goals_home": round(home_xg, 3),
        "expected_goals_away": round(away_xg, 3),
        "simulation_count": sim_config.simulation_count,
        "simulated_home_win_rate": round(home_win_rate, 4),
        "simulated_draw_rate": round(draw_rate, 4),
        "simulated_away_win_rate": round(away_win_rate, 4),
        "mean_home_goals": round(float(np.mean(home_goals)), 4),
        "mean_away_goals": round(float(np.mean(away_goals)), 4),
        "most_likely_score": {"home": int(most_likely_score[0]), "away": int(most_likely_score[1])},
        "entity_effects": {key: round(float(value), 4) for key, value in entity_effects.items()},
        "entity_states": {side: state.to_dict() for side, state in entity_states.items()},
        "sport_ruleset": ruleset,
        "behavior_catalog": get_action_catalog(sport),
        "spectator_cues": spectator_cues,
        "match_incidents": incidents,
        "artisapien_hooks": build_artisapien_hooks(entity_states),
        "regulated_session": regulated_session,
        "challenge_cues": challenge_cues,
        "event_trajectories": trajectories,
    }


def simulate_prediction_frame(predictions_df: pd.DataFrame, config: SimulationConfig | None = None, random_state: int = 42) -> List[Dict[str, object]]:
    results = []
    columns = list(predictions_df.columns)
    for offset, values in enumerate(predictions_df.itertuples(index=False, name=None)):
        results.append(simulate_match(dict(zip(columns, values)), config=config, random_state=random_state + offset))
    return results


def with_probability_override(
    row: pd.Series,
    home_probability: float,
    draw_probability: float,
    away_probability: float,
    user_weight: float = 1.0,
    home_player_quality: float = 0.0,
    away_player_quality: float = 0.0,
) -> pd.Series:
    working = row.copy()
    sport = normalize_sport(working.get("sport", "football"))
    allows_draws = get_sport_config(sport).allows_draws
    model_triplet = np.array([
        float(working.get("prob_away_win", 1.0 / 3.0)),
        float(working.get("prob_draw", 1.0 / 3.0 if allows_draws else 0.0)),
        float(working.get("prob_home_win", 1.0 / 3.0)),
    ])
    user_triplet = np.array([float(away_probability), float(draw_probability if allows_draws else 0.0), float(home_probability)])
    user_triplet = np.clip(user_triplet, 1e-6, None)
    if not allows_draws:
        user_triplet[1] = 0.0
        model_triplet[1] = 0.0
    user_triplet = user_triplet / user_triplet.sum()
    weight = float(np.clip(user_weight, 0.0, 1.0))
    blended = (1.0 - weight) * model_triplet + weight * user_triplet
    blended = blended / blended.sum()

    working["prob_away_win"] = float(blended[0])
    working["prob_draw"] = float(blended[1])
    working["prob_home_win"] = float(blended[2])
    working["home_player_quality"] = float(home_player_quality)
    working["away_player_quality"] = float(away_player_quality)
    working["player_quality_diff"] = float(home_player_quality - away_player_quality)
    working["sport"] = sport

    prediction_code = int(np.argmax(blended))
    working["prediction_code"] = prediction_code
    working["prediction"] = outcome_label(prediction_code, sport)
    working["confidence"] = float(np.max(blended))
    working["uncertainty"] = 1.0 - float(np.max(blended))
    working["entropy"] = float(-np.sum(blended * np.log(np.clip(blended, 1e-9, 1.0))) / entropy_normalizer(sport))
    return working