from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def primary_attack_damage(player_power: float, enemy_armor: float, directive_scale: float) -> int:
    base = (player_power * 5.5) - enemy_armor
    return max(1, int(round(base * (2.0 - min(1.4, directive_scale)))))


def burst_pet_effect(pet_definition: dict, directive_scale: float) -> dict:
    effect_type = pet_definition.get("effect", "spark")
    if effect_type == "chain":
        return {"damage": int(round(8 * directive_scale)), "posture": 22, "root_ticks": 0}
    if effect_type == "root":
        return {"damage": int(round(4 * directive_scale)), "posture": 15, "root_ticks": 4}
    if effect_type == "arc":
        return {"damage": int(round(6 * directive_scale)), "posture": 18, "root_ticks": 1}
    return {"damage": int(round(5 * directive_scale)), "posture": 12, "root_ticks": 0}


def chorus_drain_per_tick(pet_definition: dict) -> float:
    return float(pet_definition.get("chorus_drain", 0.24))


def perfect_dodge_relief() -> float:
    return 8.0