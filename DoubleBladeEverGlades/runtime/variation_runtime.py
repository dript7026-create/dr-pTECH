from __future__ import annotations

import random
from typing import Any


def stable_hash(text: str) -> int:
    value = 23
    for char in text:
        value = (value * 37 + ord(char)) % 1_000_003
    return value


def compute_navigation_pace(
    character_traverse_rate: float,
    idle_time_between_progressive_actions: float,
    distance_to_nearest_rootknot: float,
    distance_from_previous_rootknot: float,
) -> float:
    safe_idle = max(idle_time_between_progressive_actions, 0.35)
    raw = (character_traverse_rate / safe_idle) * distance_to_nearest_rootknot - distance_from_previous_rootknot
    return round(raw, 4)


def generate_blade_runtime_profile(blade: dict[str, Any], navigation_pace: float) -> dict[str, Any]:
    curve = blade["pace_response_curve"]
    weight_rating = blade["weight_rating"]
    pace_factor = max(0.15, navigation_pace)
    commitment = round(weight_rating * curve["tempo_bias"] + pace_factor * 0.08, 3)
    effective_arc = round(blade["movement_arc_degrees"] * curve["distance_bias"] + pace_factor * 1.7, 2)
    recovery = round(blade["swing_recovery_seconds"] + weight_rating * 0.03 - pace_factor * 0.01, 3)
    return {
        "blade_id": blade["id"],
        "commitment": commitment,
        "effective_arc": effective_arc,
        "recovery_seconds": max(0.12, recovery),
        "weight_rating": weight_rating,
        "arc_profile": blade["movement_arc_profile"],
    }


def generate_enemy_runtime_profile(enemy: dict[str, Any], navigation_pace: float, run_seed: int) -> dict[str, Any]:
    curve = enemy["threat_response_curve"]
    spawn_profile = enemy["spawn_profile"]
    behavior_profile = enemy["behavior_profile"]
    randomizer = random.Random(run_seed ^ stable_hash(enemy["id"]))
    pace_factor = max(0.1, navigation_pace)
    spawn_weight = round(spawn_profile["base_weight"] * curve["distance_gain"] + randomizer.uniform(0.0, 0.25), 3)
    aggression = round(behavior_profile["aggression"] * curve["tempo_gain"] + randomizer.uniform(-0.08, 0.1), 3)
    flank_bias = round(behavior_profile["flank_bias"] + randomizer.uniform(-0.05, 0.12), 3)
    return {
        "enemy_id": enemy["id"],
        "spawn_weight": max(0.05, spawn_weight + pace_factor * 0.02),
        "aggression": max(0.05, aggression + pace_factor * 0.03),
        "flank_bias": max(0.0, flank_bias),
        "retreat_threshold": behavior_profile["retreat_threshold"],
        "behavior_seed": randomizer.randint(0, 999_999),
    }


def build_run_variation_tables(manifest: dict[str, Any], run_seed: int, navigation_pace: float) -> dict[str, Any]:
    blades = manifest["blades"]
    enemies = manifest["enemy_varieties"]
    return {
        "run_seed": run_seed,
        "navigation_pace": navigation_pace,
        "blade_profiles": [generate_blade_runtime_profile(blade, navigation_pace) for blade in blades],
        "enemy_profiles": [generate_enemy_runtime_profile(enemy, navigation_pace, run_seed) for enemy in enemies],
    }
