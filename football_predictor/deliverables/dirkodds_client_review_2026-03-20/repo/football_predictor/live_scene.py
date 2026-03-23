from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees
from typing import Dict, List, Tuple

import numpy as np

from .sport_rules import get_sport_ruleset
from .sports import normalize_sport


SURFACE_CONFIG = {
    "football": {"length": 105.0, "width": 68.0, "zmax": 24.0, "minutes": 90.0, "players": 11, "match_seconds": 75.0},
    "baseball": {"length": 127.0, "width": 127.0, "zmax": 32.0, "minutes": 36.0, "players": 9, "match_seconds": 72.0},
    "basketball": {"length": 94.0, "width": 50.0, "zmax": 26.0, "minutes": 48.0, "players": 5, "match_seconds": 66.0},
}

SPORT_PHYSICS = {
    "football": {"max_speed": 8.8, "max_accel": 5.2, "turn_gain": 0.22, "ball_gain": 9.0, "ball_drag": 0.42, "gravity": 9.81, "control_radius": 1.6},
    "baseball": {"max_speed": 7.6, "max_accel": 5.6, "turn_gain": 0.20, "ball_gain": 10.5, "ball_drag": 0.35, "gravity": 9.81, "control_radius": 1.8},
    "basketball": {"max_speed": 8.2, "max_accel": 6.0, "turn_gain": 0.28, "ball_gain": 12.0, "ball_drag": 0.38, "gravity": 9.81, "control_radius": 1.4},
}

FORMATION_ANCHORS = {
    "football": [
        ("keeper", 0.06, 0.50),
        ("left_back", 0.20, 0.15),
        ("left_center_back", 0.22, 0.38),
        ("right_center_back", 0.22, 0.62),
        ("right_back", 0.20, 0.85),
        ("left_mid", 0.42, 0.18),
        ("pivot", 0.40, 0.50),
        ("right_mid", 0.42, 0.82),
        ("left_forward", 0.70, 0.24),
        ("striker", 0.78, 0.50),
        ("right_forward", 0.70, 0.76),
    ],
    "baseball": [
        ("pitcher", 0.16, 0.50),
        ("catcher", 0.08, 0.50),
        ("first_base", 0.28, 0.65),
        ("second_base", 0.40, 0.50),
        ("third_base", 0.28, 0.35),
        ("shortstop", 0.37, 0.38),
        ("left_field", 0.62, 0.24),
        ("center_field", 0.72, 0.50),
        ("right_field", 0.62, 0.76),
    ],
    "basketball": [
        ("point_guard", 0.24, 0.50),
        ("shooting_guard", 0.38, 0.23),
        ("small_forward", 0.42, 0.77),
        ("power_forward", 0.60, 0.35),
        ("center", 0.64, 0.65),
    ],
}


@dataclass(frozen=True)
class SceneEvent:
    team: str
    start_time: float
    end_time: float
    minute: float
    points: List[Tuple[float, Tuple[float, float, float]]]
    phase_state: str
    primary_action: str
    pressure_window: str
    attention_focus: str
    reflex_intensity: float
    focus_radius: float
    hotspot: Tuple[float, float, float]
    spectator_prompt: str


def default_ball_position(sport: str) -> Tuple[float, float, float]:
    sport = normalize_sport(sport)
    surface = SURFACE_CONFIG[sport]
    if sport == "baseball":
        return (14.0, 14.0, 1.0)
    if sport == "basketball":
        return (surface["length"] / 2.0, surface["width"] / 2.0, 2.0)
    return (surface["length"] / 2.0, surface["width"] / 2.0, 0.22)


def synthesize_live_match_scene(
    simulation_result: Dict[str, object],
    match_seconds: float | None = None,
    fps: int = 20,
) -> Dict[str, object]:
    sport = normalize_sport(simulation_result.get("sport", "football"))
    surface = SURFACE_CONFIG[sport]
    physics = SPORT_PHYSICS[sport]
    ruleset = simulation_result.get("sport_ruleset") or get_sport_ruleset(sport)
    scene_seconds = float(match_seconds or surface["match_seconds"])
    events = _scene_events(simulation_result, scene_seconds, surface["minutes"])
    keyframes = _build_ball_keyframes(sport, scene_seconds, events)
    times = np.linspace(0.0, scene_seconds, max(2, int(scene_seconds * fps) + 1))
    dt = float(scene_seconds / max(len(times) - 1, 1))
    entity_states = simulation_result.get("entity_states", {}) or {}
    home_states = _initial_player_states(sport, "home", surface, entity_states.get("home"))
    away_states = _initial_player_states(sport, "away", surface, entity_states.get("away"))
    ball_state = {
        "pos": np.array(default_ball_position(sport), dtype=float),
        "vel": np.zeros(3, dtype=float),
        "speed": 0.0,
        "recovered": False,
    }
    frames = []
    for frame_index, time_value in enumerate(times):
        desired_ball = np.array(_interpolate_ball(keyframes, float(time_value)), dtype=float)
        next_time = float(times[min(frame_index + 1, len(times) - 1)])
        next_ball = np.array(_interpolate_ball(keyframes, next_time), dtype=float)
        desired_ball_velocity = (next_ball - desired_ball) / max(next_time - float(time_value), 1e-6)
        active_event = _active_event(events, float(time_value))
        possession_team = active_event.team if active_event is not None else _ambient_possession(float(time_value))
        control = _pressure_indices(home_states, away_states, ball_state["pos"], possession_team)
        _advance_ball(ball_state, desired_ball, desired_ball_velocity, dt, physics, surface)
        _advance_team(home_states, sport, "home", ball_state["pos"], possession_team, surface, physics, ruleset, float(time_value), dt, control, active_event)
        _advance_team(away_states, sport, "away", ball_state["pos"], possession_team, surface, physics, ruleset, float(time_value), dt, control, active_event)
        frames.append(
            _snapshot_frame(
                simulation_result,
                sport,
                surface,
                scene_seconds,
                float(time_value),
                events,
                ball_state,
                home_states,
                away_states,
                possession_team,
                active_event,
                ruleset,
            )
        )
    return {
        "sport": sport,
        "surface": surface,
        "physics": physics,
        "ruleset": ruleset,
        "match_seconds": scene_seconds,
        "fps": fps,
        "frames": frames,
    }


def scene_from_report(
    report: Dict[str, object],
    fixture_index: int = 0,
    match_seconds: float | None = None,
    fps: int = 20,
) -> Dict[str, object]:
    simulations = list(report.get("simulations", []))
    if not simulations:
        raise ValueError("The report does not contain simulations to render.")
    if fixture_index < 0 or fixture_index >= len(simulations):
        raise IndexError("Fixture index is out of range for the report simulations.")
    return synthesize_live_match_scene(simulations[fixture_index], match_seconds=match_seconds, fps=fps)


def _scene_events(simulation_result: Dict[str, object], match_seconds: float, scene_minutes: float) -> List[SceneEvent]:
    processed: List[SceneEvent] = []
    trajectories = simulation_result.get("event_trajectories", []) or []
    for event in sorted(trajectories, key=lambda item: float(item.get("minute", 0.0))):
        points = event.get("trajectory", []) or []
        if not points:
            continue
        minute = float(event.get("minute", 0.0))
        start_time = (minute / max(scene_minutes, 1e-6)) * match_seconds
        mapped_points = []
        for point in points:
            mapped_points.append(
                (
                    start_time + float(point.get("t", 0.0)),
                    (float(point["x"]), float(point["y"]), float(point["z"])),
                )
            )
        processed.append(
            SceneEvent(
                team=str(event.get("team", "home")),
                start_time=start_time,
                end_time=mapped_points[-1][0],
                minute=minute,
                points=mapped_points,
                phase_state=str(event.get("phase_state", "transition")),
                primary_action=str(event.get("primary_action", event.get("event_type", "release"))),
                pressure_window=str(event.get("pressure_window", "standard_window")),
                attention_focus=str(event.get("attention_focus", "central_balance")),
                reflex_intensity=float(event.get("reflex_intensity", 0.5)),
                focus_radius=float(event.get("focus_radius", 6.0)),
                hotspot=(
                    float((event.get("hotspot") or {}).get("x", mapped_points[-1][1][0])),
                    float((event.get("hotspot") or {}).get("y", mapped_points[-1][1][1])),
                    float((event.get("hotspot") or {}).get("z", mapped_points[-1][1][2])),
                ),
                spectator_prompt=str(event.get("spectator_prompt", "Track the whole flow.")),
            )
        )
    return processed


def _build_ball_keyframes(sport: str, match_seconds: float, events: List[SceneEvent]) -> List[Tuple[float, Tuple[float, float, float]]]:
    keys: List[Tuple[float, Tuple[float, float, float]]] = [(0.0, default_ball_position(sport))]
    current_ball = keys[0][1]
    current_time = 0.0
    for event in events:
        first_time, first_ball = event.points[0]
        travel_start = max(current_time + 0.3, first_time - 1.4)
        if travel_start > keys[-1][0]:
            keys.append((travel_start, current_ball))
        if first_time > keys[-1][0]:
            keys.append((first_time, first_ball))
        for point_time, point_ball in event.points:
            keys.append((point_time, point_ball))
        current_time = event.end_time
        current_ball = event.points[-1][1]
    if match_seconds > keys[-1][0]:
        keys.append((match_seconds, current_ball))
    keys.sort(key=lambda item: item[0])
    return keys


def _snapshot_frame(
    simulation_result: Dict[str, object],
    sport: str,
    surface: Dict[str, float],
    match_seconds: float,
    time_value: float,
    events: List[SceneEvent],
    ball_state: Dict[str, object],
    home_states: List[Dict[str, object]],
    away_states: List[Dict[str, object]],
    possession_team: str,
    active_event: SceneEvent | None,
    ruleset: Dict[str, object],
) -> Dict[str, object]:
    ball = tuple(float(value) for value in ball_state["pos"])
    home_score = sum(1 for event in events if event.team == "home" and event.end_time <= time_value)
    away_score = sum(1 for event in events if event.team == "away" and event.end_time <= time_value)
    crowd_intensity = _crowd_intensity(float(time_value), events)
    camera_target = (
        0.55 * ball[0] + 0.45 * surface["length"] / 2.0,
        0.55 * ball[1] + 0.45 * surface["width"] / 2.0,
        max(ball[2], 1.5),
    )
    phase = _phase_state(sport, possession_team, active_event, bool(ball_state.get("recovered", False)), float(time_value))
    focus_spot = active_event.hotspot if active_event is not None else camera_target
    pressure_window = active_event.pressure_window if active_event is not None else ("tight_window" if crowd_intensity > 0.72 else "standard_window")
    attention_focus = active_event.attention_focus if active_event is not None else "whole_field_read"
    spectator_prompt = active_event.spectator_prompt if active_event is not None else "Read both teams and react to the pressure swing."
    reflex_intensity = active_event.reflex_intensity if active_event is not None else float(np.clip(0.34 + crowd_intensity * 0.42, 0.0, 1.0))
    return {
        "sport": sport,
        "time": float(time_value),
        "minute": round(float(time_value) / max(match_seconds, 1e-6) * surface["minutes"], 2),
        "ball": ball,
        "ball_speed": float(ball_state.get("speed", 0.0)),
        "home_players": [_serialize_player_state(player) for player in home_states],
        "away_players": [_serialize_player_state(player) for player in away_states],
        "home_score": home_score,
        "away_score": away_score,
        "crowd_intensity": crowd_intensity,
        "camera_target": camera_target,
        "home_team": simulation_result.get("home_team", "Home"),
        "away_team": simulation_result.get("away_team", "Away"),
        "possession": possession_team,
        "phase": phase,
        "rules_phase": phase,
        "behavior_catalog": list(ruleset.get("control_actions", [])),
        "primary_action": active_event.primary_action if active_event is not None else "scan",
        "pressure_window": pressure_window,
        "attention_focus": attention_focus,
        "spectator_prompt": spectator_prompt,
        "reflex_intensity": reflex_intensity,
        "focus_spot": focus_spot,
        "focus_radius": active_event.focus_radius if active_event is not None else 6.0,
    }


def _interpolate_ball(keys: List[Tuple[float, Tuple[float, float, float]]], time_value: float) -> Tuple[float, float, float]:
    if time_value <= keys[0][0]:
        return keys[0][1]
    for index in range(1, len(keys)):
        previous_time, previous_ball = keys[index - 1]
        next_time, next_ball = keys[index]
        if time_value <= next_time:
            ratio = 0.0 if next_time <= previous_time else (time_value - previous_time) / (next_time - previous_time)
            return tuple(float(previous_ball[axis] + (next_ball[axis] - previous_ball[axis]) * ratio) for axis in range(3))
    return keys[-1][1]


def _active_event(events: List[SceneEvent], time_value: float) -> SceneEvent | None:
    for event in events:
        if event.start_time <= time_value <= event.end_time + 1.0:
            return event
    return None


def _ambient_possession(time_value: float) -> str:
    return "home" if np.sin(time_value / 4.5) >= 0.0 else "away"


def _phase_state(sport: str, possession_team: str, active_event: SceneEvent | None, recovered: bool, time_value: float) -> str:
    if active_event is not None and active_event.phase_state:
        return active_event.phase_state
    if recovered:
        if sport == "baseball":
            return "dead_ball_reset"
        if sport == "basketball":
            return "turnover_recovery"
        return "out_of_bounds_recovery"
    if active_event is not None:
        if sport == "baseball":
            return "scoring_contact"
        return "finishing_sequence"
    if sport == "baseball":
        return "base_running_pressure" if abs(np.sin(time_value / 3.8)) > 0.7 else "live_pitch"
    if sport == "basketball":
        return "transition_push" if abs(np.sin(time_value / 2.4)) > 0.68 else "half_court_set"
    return "counterattack" if possession_team == "home" and abs(np.sin(time_value / 4.2)) > 0.7 else "settled_possession"


def _initial_player_states(sport: str, side: str, surface: Dict[str, float], team_state: Dict[str, object] | None = None) -> List[Dict[str, object]]:
    players = []
    roster = list((team_state or {}).get("roster", []))
    for index, (role, x_norm, y_norm) in enumerate(FORMATION_ANCHORS[sport], start=1):
        profile = roster[index - 1] if index - 1 < len(roster) else {}
        x_value = x_norm * surface["length"] if side == "home" else (1.0 - x_norm) * surface["length"]
        y_value = y_norm * surface["width"]
        players.append(
            {
                "id": f"{side}_{index:02d}",
                "role": role,
                "entity_role": str(profile.get("role", role)),
                "number": index,
                "pos": np.array([x_value, y_value], dtype=float),
                "vel": np.zeros(2, dtype=float),
                "heading": 0.0,
                "speed": 0.0,
                "gait_phase": float(index) * 0.25,
                "action": "set",
                "behavior_state": "set",
                "decision_state": "scan",
                "mistake_state": "stable",
                "lean": 0.0,
                "fatigue": float(profile.get("fatigue", 0.2)),
                "confusion": float(profile.get("confusion", 0.1)),
                "vision_disruption": float(profile.get("vision_disruption", 0.1)),
                "reaction_delay": float(profile.get("reaction_delay", 0.1)),
                "spatial_awareness": float(profile.get("spatial_awareness", 0.72)),
                "coordination": float(profile.get("coordination", 0.72)),
                "balance": float(profile.get("balance", 0.72)),
                "composure": float(profile.get("composure", 0.72)),
                "decision_noise": float(profile.get("decision_noise", 0.1)),
                "hesitation": float(profile.get("hesitation", 0.1)),
                "locomotion_integrity": float(profile.get("locomotion_integrity", 0.78)),
            }
        )
    return players


def _advance_team(
    players: List[Dict[str, object]],
    sport: str,
    side: str,
    ball: np.ndarray,
    possession_team: str,
    surface: Dict[str, float],
    physics: Dict[str, float],
    ruleset: Dict[str, object],
    time_value: float,
    dt: float,
    control: Dict[str, Tuple[int, int]],
    active_event: SceneEvent | None,
) -> None:
    anchors = FORMATION_ANCHORS[sport]
    orientation = 1.0 if side == "home" else -1.0
    attack_bias = 0.22 if possession_team == side else 0.10
    retreat_bias = 0.04 if possession_team == side else 0.14
    max_speed = float(physics["max_speed"])
    max_accel = float(physics["max_accel"])
    control_index = control["attackers"][0] if side == possession_team else control["defenders"][0]
    for index, (role, x_norm, y_norm) in enumerate(anchors):
        player = players[index]
        base_x = x_norm * surface["length"] if side == "home" else (1.0 - x_norm) * surface["length"]
        base_y = y_norm * surface["width"]
        chase_x = (ball[0] - base_x) * attack_bias
        chase_y = (ball[1] - base_y) * (0.12 if possession_team == side else 0.09)
        structure_x = orientation * (surface["length"] * (0.02 if role == "keeper" else 0.05))
        if role == "keeper":
            chase_x *= 0.16
            chase_y *= 0.08
            structure_x = orientation * surface["length"] * 0.015
        drift_x = np.sin(time_value * 0.9 + index * 0.7) * (0.6 if sport == "basketball" else 0.9)
        drift_y = np.cos(time_value * 0.75 + index * 1.1) * (0.7 if sport == "baseball" else 1.1)
        if possession_team != side:
            chase_x *= 0.7
            structure_x *= -retreat_bias / max(attack_bias, 1e-6)
        target = np.array(
            [
                float(np.clip(base_x + chase_x + structure_x + drift_x, 0.0, surface["length"])),
                float(np.clip(base_y + chase_y + drift_y, 0.0, surface["width"])),
            ],
            dtype=float,
        )
        if index == control_index:
            ball_offset = np.array([-1.0 if side == "home" else 1.0, 0.0], dtype=float)
            if side != possession_team:
                ball_offset = np.array([1.4 if side == "home" else -1.4, 0.8], dtype=float)
            target = _clamp_xy(ball[:2] + ball_offset, surface, inset=0.9)
        perception_drift = (player["confusion"] + player["vision_disruption"] + (1.0 - player["spatial_awareness"])) / 3.0
        target = _clamp_xy(
            target
            + np.array(
                [
                    np.sin(time_value * 1.3 + index * 0.4) * (0.2 + 2.1 * perception_drift),
                    np.cos(time_value * 1.1 + index * 0.6) * (0.2 + 1.8 * perception_drift),
                ],
                dtype=float,
            ),
            surface,
            inset=0.45,
        )
        to_target = target - player["pos"]
        distance = float(np.linalg.norm(to_target))
        direction = to_target / max(distance, 1e-6)
        speed_ratio = min(1.0, distance / (3.5 if sport == "basketball" else 5.5))
        locomotion_cap = float(np.clip(player["locomotion_integrity"] - 0.16 * player["fatigue"] - 0.14 * player["reaction_delay"], 0.18, 1.0))
        decision_drag = float(np.clip(1.0 - 0.32 * player["decision_noise"] - 0.38 * player["hesitation"], 0.28, 1.0))
        desired_speed = max_speed * locomotion_cap * (0.25 + 0.75 * speed_ratio)
        if index == control_index:
            desired_speed = max_speed * locomotion_cap * (0.92 if side == possession_team else 0.98)
        desired_velocity = direction * desired_speed * decision_drag
        accel = desired_velocity - player["vel"]
        accel_norm = float(np.linalg.norm(accel))
        accel_cap = max_accel * float(np.clip(0.44 + 0.56 * player["coordination"] * player["balance"], 0.22, 1.0))
        if accel_norm > accel_cap:
            accel = accel / accel_norm * accel_cap
        player["vel"] = player["vel"] + accel * dt
        speed = float(np.linalg.norm(player["vel"]))
        speed_limit = max_speed * locomotion_cap
        if speed > speed_limit:
            player["vel"] = player["vel"] / speed * speed_limit
            speed = speed_limit
        player["pos"] = _clamp_xy(player["pos"] + player["vel"] * dt, surface, inset=0.45)
        player["speed"] = speed
        if speed > 0.05:
            player["heading"] = float(degrees(atan2(player["vel"][1], player["vel"][0])))
        player["gait_phase"] = float((player["gait_phase"] + speed * 0.19) % (2.0 * np.pi))
        player["lean"] = float(np.clip(speed / max(speed_limit, 1e-6), 0.0, 1.0))
        action, decision_state, mistake_state = _player_action(sport, side, possession_team, index, control_index, active_event, time_value, speed, player, ruleset)
        player["action"] = action
        player["behavior_state"] = action
        player["decision_state"] = decision_state
        player["mistake_state"] = mistake_state
    _apply_team_spacing(players, surface, control_index)


def _advance_ball(
    ball_state: Dict[str, object],
    desired_ball: np.ndarray,
    desired_velocity: np.ndarray,
    dt: float,
    physics: Dict[str, float],
    surface: Dict[str, float],
) -> None:
    gain = float(physics["ball_gain"])
    drag = float(physics["ball_drag"])
    gravity = float(physics["gravity"])
    velocity = ball_state["vel"]
    velocity[:2] = velocity[:2] + np.clip(desired_velocity[:2] - velocity[:2], -gain * dt, gain * dt)
    velocity[:2] *= max(0.0, 1.0 - drag * dt)
    velocity[2] = velocity[2] + np.clip(desired_velocity[2] - velocity[2], -gain * dt, gain * dt) - gravity * dt * 0.12
    desired_out_of_bounds = bool(
        desired_ball[0] < 0.25
        or desired_ball[0] > surface["length"] - 0.25
        or desired_ball[1] < 0.25
        or desired_ball[1] > surface["width"] - 0.25
    )
    desired_ball[:2] = _clamp_xy(desired_ball[:2], surface, inset=0.25)
    next_pos = ball_state["pos"] + velocity * dt
    next_pos[:2] += (desired_ball[:2] - next_pos[:2]) * 0.18
    if next_pos[2] < 0.12:
        next_pos[2] = 0.12 + (0.12 - next_pos[2]) * 0.28
        velocity[2] = abs(velocity[2]) * 0.42
    next_pos[2] += (desired_ball[2] - next_pos[2]) * 0.35
    recovered = False
    min_xy = np.array([0.25, 0.25], dtype=float)
    max_xy = np.array([surface["length"] - 0.25, surface["width"] - 0.25], dtype=float)
    for axis in range(2):
        if next_pos[axis] < min_xy[axis]:
            next_pos[axis] = min_xy[axis]
            velocity[axis] = abs(velocity[axis]) * 0.35
            recovered = True
        elif next_pos[axis] > max_xy[axis]:
            next_pos[axis] = max_xy[axis]
            velocity[axis] = -abs(velocity[axis]) * 0.35
            recovered = True
    ball_state["pos"] = next_pos
    ball_state["vel"] = velocity
    ball_state["speed"] = float(np.linalg.norm(velocity))
    ball_state["recovered"] = recovered or desired_out_of_bounds


def _pressure_indices(
    home_players: List[Dict[str, object]],
    away_players: List[Dict[str, object]],
    ball: np.ndarray,
    possession_team: str,
) -> Dict[str, Tuple[int, int]]:
    attack_players = home_players if possession_team == "home" else away_players
    defend_players = away_players if possession_team == "home" else home_players
    attack_index = min(range(len(attack_players)), key=lambda idx: _distance_xy(attack_players[idx], ball, attack=True))
    defend_index = min(range(len(defend_players)), key=lambda idx: _distance_xy(defend_players[idx], ball, attack=False))
    return {"attackers": (attack_index, len(attack_players)), "defenders": (defend_index, len(defend_players))}


def _distance_xy(player: Dict[str, object], ball: Tuple[float, float, float] | np.ndarray, attack: bool) -> float:
    penalty = 30.0 if (not attack and str(player.get("role")) == "keeper") else 0.0
    if "pos" in player:
        return float((player["pos"][0] - ball[0]) ** 2 + (player["pos"][1] - ball[1]) ** 2 + penalty)
    return float((player["x"] - ball[0]) ** 2 + (player["y"] - ball[1]) ** 2 + penalty)


def _cycled_choice(options: List[str], time_value: float, index: int) -> str:
    if not options:
        return "set"
    choice_index = int(abs(np.sin(time_value * 0.73 + index * 0.61)) * len(options)) % len(options)
    return str(options[choice_index])


def _player_action(
    sport: str,
    side: str,
    possession_team: str,
    index: int,
    control_index: int,
    active_event: SceneEvent | None,
    time_value: float,
    speed: float,
    player: Dict[str, object],
    ruleset: Dict[str, object],
) -> Tuple[str, str, str]:
    mistake_pressure = float(
        0.24 * player["confusion"]
        + 0.18 * player["vision_disruption"]
        + 0.18 * player["reaction_delay"]
        + 0.16 * player["decision_noise"]
        + 0.14 * player["hesitation"]
        + 0.1 * (1.0 - player["balance"])
    )
    mistake_pressure += 0.08 * (0.5 + 0.5 * np.sin(time_value * 1.2 + index * 0.7))
    if mistake_pressure > 0.58:
        mistake_state = _cycled_choice(list(ruleset.get("mistake_states", [])), time_value, index)
        recovery_action = _cycled_choice(list(ruleset.get("recovery_actions", [])), time_value + 0.4, index)
        decision_state = "hesitate" if player["hesitation"] >= player["composure"] * 0.7 else "recover"
        return recovery_action, decision_state, mistake_state
    if index == control_index and side == possession_team:
        decision_state = "commit" if active_event is not None or player["composure"] >= player["hesitation"] else "anticipate"
        if active_event is not None:
            return _cycled_choice(list(ruleset.get("scoring_actions", [])), time_value, index), decision_state, "stable"
        return _cycled_choice(list(ruleset.get("control_actions", [])), time_value, index), decision_state, "stable"
    if index == control_index and side != possession_team:
        decision_state = "anticipate" if player["reaction_delay"] < 0.34 else "defer"
        return _cycled_choice(list(ruleset.get("defensive_actions", [])), time_value, index), decision_state, "stable"
    if speed > SPORT_PHYSICS[sport]["max_speed"] * 0.58:
        decision_state = "commit" if side == possession_team else "anticipate"
        return _cycled_choice(list(ruleset.get("support_actions", [])), time_value, index), decision_state, "stable"
    if player["hesitation"] > 0.46:
        return _cycled_choice(list(ruleset.get("recovery_actions", [])), time_value, index), "defer", "stable"
    return _cycled_choice(list(ruleset.get("support_actions", [])), time_value, index), "scan", "stable"


def _clamp_xy(point: np.ndarray, surface: Dict[str, float], inset: float) -> np.ndarray:
    return np.array(
        [
            float(np.clip(point[0], inset, surface["length"] - inset)),
            float(np.clip(point[1], inset, surface["width"] - inset)),
        ],
        dtype=float,
    )


def _serialize_player_state(player: Dict[str, object]) -> Dict[str, object]:
    return {
        "id": player["id"],
        "role": player["role"],
        "number": player["number"],
        "x": float(player["pos"][0]),
        "y": float(player["pos"][1]),
        "z": 0.0,
        "heading": float(player["heading"]),
        "speed": float(player["speed"]),
        "gait_phase": float(player["gait_phase"]),
        "action": player["action"],
        "behavior_state": player.get("behavior_state", player["action"]),
        "decision_state": player.get("decision_state", "scan"),
        "mistake_state": player.get("mistake_state", "stable"),
        "lean": float(player["lean"]),
    }


def _apply_team_spacing(players: List[Dict[str, object]], surface: Dict[str, float], control_index: int) -> None:
    min_gap = 1.45
    for index, player in enumerate(players):
        repel = np.zeros(2, dtype=float)
        for other_index, other in enumerate(players):
            if other_index == index:
                continue
            delta = player["pos"] - other["pos"]
            distance = float(np.linalg.norm(delta))
            if distance <= 1e-6 or distance >= min_gap:
                continue
            repel += (delta / distance) * ((min_gap - distance) / min_gap)
        if index == control_index:
            repel *= 0.28
        elif str(player.get("role")) == "keeper":
            repel *= 0.18
        else:
            repel *= 0.55
        if float(np.linalg.norm(repel)) > 0.0:
            player["pos"] = _clamp_xy(player["pos"] + repel, surface, inset=0.45)


def _crowd_intensity(time_value: float, events: List[SceneEvent]) -> float:
    intensity = 0.34 + 0.05 * np.sin(time_value * 0.65)
    for event in events:
        delta = time_value - event.end_time
        intensity += float(0.38 * np.exp(-(delta * delta) / 6.0))
    return float(np.clip(intensity, 0.15, 1.0))