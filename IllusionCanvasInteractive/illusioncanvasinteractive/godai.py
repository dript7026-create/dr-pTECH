from __future__ import annotations


class GodAIConductor:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}
        self.difficulty_floor = float(self.config.get("difficulty_floor", 0.85))
        self.difficulty_ceiling = float(self.config.get("difficulty_ceiling", 1.35))

    def evaluate(self, player_state, room: dict, encounter_reading) -> dict:
        danger = float(room.get("danger", 0))
        living_enemies = len([enemy for enemy in player_state.room_enemies if enemy.hp > 0])
        raw_pressure = self.difficulty_floor + (danger * 0.09) + (living_enemies * 0.04) + (encounter_reading.pressure * 0.16)
        pressure_scale = min(self.difficulty_ceiling, max(self.difficulty_floor, raw_pressure))

        omen = "steady hush"
        mercy_window = False
        if player_state.hp <= 35 or player_state.bond_tension >= 78:
            omen = "mercy drift"
            pressure_scale = max(self.difficulty_floor, pressure_scale - 0.12)
            mercy_window = True
        elif living_enemies >= 3 and danger >= 2:
            omen = "predator surge"
        elif room.get("safe_room"):
            omen = "refuge calm"

        return {
            "omen": omen,
            "pressure_scale": round(pressure_scale, 3),
            "mercy_window": mercy_window,
            "recommended_style": encounter_reading.recommended_style,
        }