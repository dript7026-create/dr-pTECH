from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def primary_attack_damage(player_power: float, enemy_armor: float, directive_scale: float) -> int:
    base = (player_power * 5.5) - enemy_armor
    return max(1, int(round(base * (2.0 - min(1.4, directive_scale)))))


def burst_pet_effect(pet_definition: dict, directive_scale: float, bond_level: int = 0) -> dict:
    scale = bond_level_scale(bond_level)
    effect_type = pet_definition.get("effect", "spark")
    if effect_type == "chain":
        return {"damage": int(round(8 * directive_scale * scale)), "posture": 22, "root_ticks": 0}
    if effect_type == "root":
        return {"damage": int(round(4 * directive_scale * scale)), "posture": 15, "root_ticks": 4}
    if effect_type == "arc":
        return {"damage": int(round(6 * directive_scale * scale)), "posture": 18, "root_ticks": 1}
    return {"damage": int(round(5 * directive_scale * scale)), "posture": 12, "root_ticks": 0}


def chorus_drain_per_tick(pet_definition: dict) -> float:
    return float(pet_definition.get("chorus_drain", 0.24))


def perfect_dodge_relief() -> float:
    return 8.0


def bond_level_scale(bond_level: int) -> float:
    """Return a multiplier (1.0 – 1.4) that grows with bond level 0-4."""
    return 1.0 + min(bond_level, 4) * 0.1


def crest_passive_effect(pet_definitions: list[dict], bond_levels: dict | None = None) -> dict:
    """Compute aggregate passive bonuses from all slotted Crest pets."""
    if bond_levels is None:
        bond_levels = {}
    result = {
        "damage_reduction": 0.0,
        "tension_decay": 0.0,
        "weave_charge_bonus": 0.0,
    }
    for pet in pet_definitions:
        scale = bond_level_scale(bond_levels.get(pet.get("id"), {}).get("bond_level", 0) if isinstance(bond_levels.get(pet.get("id")), dict) else 0)
        effect = pet.get("effect", "")
        if effect == "stabilize":
            result["damage_reduction"] += 0.12 * scale
            result["tension_decay"] += 0.35 * scale
        elif effect == "harden":
            result["damage_reduction"] += 0.18 * scale
        elif effect == "resonance":
            result["tension_decay"] += 0.5 * scale
            result["weave_charge_bonus"] += 2.0 * scale
    return result


COMBO_CHAIN = [
    {"damage_mult": 1.0, "posture_damage": 14, "cooldown": 7, "weave_charge": 8},
    {"damage_mult": 1.15, "posture_damage": 18, "cooldown": 7, "weave_charge": 9},
    {"damage_mult": 1.4, "posture_damage": 26, "cooldown": 12, "weave_charge": 14},
]
COMBO_WINDOW = 18


def combo_hit(step: int, player_power: float, enemy_armor: float, directive_scale: float) -> dict:
    """Return damage, posture_damage, cooldown, weave_charge for combo step 0-2."""
    stage = COMBO_CHAIN[min(step, len(COMBO_CHAIN) - 1)]
    base = (player_power * 5.5 * stage["damage_mult"]) - enemy_armor
    return {
        "damage": max(1, int(round(base * (2.0 - min(1.4, directive_scale))))),
        "posture_damage": stage["posture_damage"],
        "cooldown": stage["cooldown"],
        "weave_charge": stage["weave_charge"],
    }


def update_pet_trust(pet_state: dict, event: str) -> dict:
    """Advance trust/growth for a pet based on a gameplay event. Returns updated state."""
    trust = float(pet_state.get("trust", 0.0))
    bond_level = int(pet_state.get("bond_level", 0))
    if event == "burst_used":
        trust += 1.2
    elif event == "chorus_sustained":
        trust += 0.4
    elif event == "crest_passive_tick":
        trust += 0.15
    elif event == "rescue":
        trust += 8.0
    elif event == "perfect_dodge":
        trust += 0.6
    elif event == "bond_weave":
        trust += 3.0
    elif event == "tension_spike":
        trust = max(0.0, trust - 2.0)
    elif event == "route_opened":
        trust += 4.0
    # Level thresholds
    thresholds = [0, 12, 30, 60, 100]
    new_level = bond_level
    for i, threshold in enumerate(thresholds):
        if trust >= threshold:
            new_level = i
    return {"trust": round(min(trust, 120.0), 2), "bond_level": min(new_level, len(thresholds) - 1)}