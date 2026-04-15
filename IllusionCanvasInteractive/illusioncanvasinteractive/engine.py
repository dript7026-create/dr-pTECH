from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from .combat import burst_pet_effect, clamp, chorus_drain_per_tick, perfect_dodge_relief, primary_attack_damage, crest_passive_effect, combo_hit, update_pet_trust, bond_level_scale, COMBO_WINDOW
from .egosphere_bridge import EgoSphereBridge
from .godai import GodAIConductor
from tick_gnosis import TickGnosisState


@dataclass(slots=True)
class EnemyState:
    name: str
    x: float
    y: float
    hp: int
    max_hp: int
    aggression: float
    armor: float
    posture: float
    is_boss: bool = False
    weave_gate: dict = field(default_factory=dict)
    root_ticks: int = 0
    attack_cooldown: int = 0


@dataclass(slots=True)
class PlayerState:
    x: float
    y: float
    vy: float
    hp: int
    max_hp: int
    bond_tension: float
    attack_cooldown: int
    burst_cooldown: int
    dodge_cooldown: int
    damage_cooldown: int
    chorus_active: bool
    grounded: bool
    bond_weave_charge: float
    rescued_pets: set[str] = field(default_factory=set)
    completed_milestones: set[str] = field(default_factory=set)
    room_enemies: list[EnemyState] = field(default_factory=list)
    combo_step: int = 0
    combo_window_left: int = 0
    pet_trust: dict = field(default_factory=dict)
    facing: int = 1
    move_delta_x: float = 0.0
    animation_name: str = "idle"
    animation_started_tick: int = 0
    animation_lock_ticks: int = 0
    level: int = 1
    experience: int = 0
    weapon_points: int = 0
    equipped_weapon: str = ""
    equipped_sidearm: str = ""
    equipped_relic: str = ""
    inventory: list[str] = field(default_factory=list)
    tutorial_pet: str | None = None


class GameEngine:
    def __init__(self, document: dict) -> None:
        self.document = document
        self.prototype = document.get("prototype", {})
        self.player_moves = {move["id"]: move for move in self.prototype.get("player_moves", [])}
        self.enemy_archetypes = {enemy["id"]: enemy for enemy in self.prototype.get("enemy_archetypes", [])}
        self.boss_moves = list(self.prototype.get("boss_moves", []))
        self.gear_catalog = {item["id"]: item for item in self.prototype.get("gear_catalog", [])}
        self.progression_gates = {gate["id"]: gate for gate in self.prototype.get("progression_gates", [])}
        self.pet_definitions = {pet["id"]: pet for pet in document["pets"]["definitions"]}
        self.rooms = {room["id"]: room for room in document["world"]["rooms"]}
        self.room_order = [room["id"] for room in document["world"]["rooms"]]
        player = document["player"]
        self.room_states = {room_id: self._build_room_state(self.rooms[room_id]) for room_id in self.rooms}
        self.current_room_id = document["world"]["start_room"]
        self.state = PlayerState(
            x=float(player.get("start_x", 18)),
            y=float(player.get("start_y", 0)),
            vy=0.0,
            hp=int(player["stats"]["hp"]),
            max_hp=int(player["stats"]["hp"]),
            bond_tension=float(player["stats"].get("bond_tension", 10)),
            attack_cooldown=0,
            burst_cooldown=0,
            dodge_cooldown=0,
            damage_cooldown=0,
            chorus_active=False,
            grounded=True,
            bond_weave_charge=0.0,
            rescued_pets=set(player.get("rescued_pets", [])),
            completed_milestones=set(player.get("completed_milestones", [])),
            room_enemies=[],
            level=int(player.get("progression", {}).get("level", 1)),
            experience=int(player.get("progression", {}).get("experience", 0)),
            weapon_points=int(player.get("progression", {}).get("weapon_points", 0)),
            equipped_weapon=str(player.get("progression", {}).get("equipped_weapon", "")),
            equipped_sidearm=str(player.get("progression", {}).get("equipped_sidearm", "")),
            equipped_relic=str(player.get("progression", {}).get("equipped_relic", "")),
            inventory=list(player.get("progression", {}).get("inventory", [])),
        )
        self.loadout = player["loadout"]
        self._crest_pets = [self.pet_definitions[pid] for pid in self.loadout.get("crest", []) if pid in self.pet_definitions]
        self._crest_passive = crest_passive_effect(self._crest_pets, self.state.pet_trust)
        self.egosphere = EgoSphereBridge(document.get("integrations", {}).get("egosphere"))
        self.godai = GodAIConductor(document.get("integrations", {}).get("godai"))
        self.milestone_defs = list(document.get("gameplay", {}).get("milestones", []))
        self.last_event = "Enter the refuge and prepare the expedition."
        self.interaction_signal: dict | None = None
        self.tick_count = 0
        self.tick_gnosis = TickGnosisState("illusioncanvas-engine")
        self.last_tick_gnosis = self.tick_gnosis.capture(
            tick=0,
            frame_delta_ms=16.667,
            entity_count=1,
            energy_total=float(self.state.hp + self.state.bond_tension),
            camera_motion=0.0,
            input_pressure=0.0,
            recursion_depth=1.0,
        )
        self.tick_flags = self._empty_tick_flags()
        self._sync_room_enemies()
        self._snap_player_to_support()

    def _build_room_state(self, room: dict) -> dict:
        enemies = []
        for enemy in room.get("enemies", []):
            enemies.append(
                EnemyState(
                    name=enemy["name"],
                    x=float(enemy["x"]),
                    y=float(enemy.get("y", 0.0)),
                    hp=int(enemy["hp"]),
                    max_hp=int(enemy["hp"]),
                    aggression=float(enemy.get("aggression", 0.6)),
                    armor=float(enemy.get("armor", 1.0)),
                    posture=float(enemy.get("posture", 40)),
                    is_boss=bool(enemy.get("boss", False)),
                    weave_gate=dict(enemy.get("bond_weave_requirements", {})),
                )
            )
        return {
            "enemies": enemies,
            "rescued": False,
            "boss_defeated": False,
            "zones_triggered": set(),
            "interacted_objects": set(),
            "opened_gates": set(),
            "puzzle_progress": {},
        }

    def _empty_tick_flags(self) -> dict:
        return {
            "entered_room": None,
            "rescued_pet": None,
            "rested_room": None,
            "boss_defeated_room": None,
            "room_cleared": None,
        }

    def _room_layout(self, room: dict | None = None) -> dict:
        if room is None:
            room = self._current_room()
        layout = dict(room.get("layout", {}))
        if not layout.get("platforms"):
            layout["platforms"] = [{"id": "floor", "x1": 0, "x2": 100, "y": 0, "kind": "floor"}]
        layout.setdefault("hazards", [])
        layout.setdefault("encounter_zones", [])
        layout.setdefault("objects", [])
        return layout

    def _interactable_objects(self) -> list[dict]:
        return list(self._room_layout().get("objects", []))

    def _current_weapon_profile(self) -> dict:
        return self.gear_catalog.get(self.state.equipped_weapon, {})

    def _current_relic_profile(self) -> dict:
        return self.gear_catalog.get(self.state.equipped_relic, {})

    def _weapon_power_bonus(self) -> float:
        return float(self._current_weapon_profile().get("power", 0.0))

    def _precision_bonus(self) -> int:
        return int(self._current_weapon_profile().get("precision_bonus", 0))

    def _gain_experience(self, amount: int) -> None:
        if amount <= 0:
            return
        relic_bonus = float(self._current_relic_profile().get("xp_bonus", 0.0))
        adjusted = int(round(amount * (1.0 + relic_bonus)))
        self.state.experience += adjusted
        next_level = self.state.level * 60
        while self.state.experience >= next_level:
            self.state.level += 1
            self.state.max_hp += 6
            self.state.hp = min(self.state.max_hp, self.state.hp + 6)
            self.state.weapon_points += 4
            next_level = self.state.level * 60

    def _progress_gate(self, puzzle_id: str, sequence_index: int, gate_id: str | None) -> bool:
        room_state = self.room_states[self.current_room_id]
        progress = room_state["puzzle_progress"].get(puzzle_id, 0)
        if sequence_index == progress:
            progress += 1
            room_state["puzzle_progress"][puzzle_id] = progress
            gate = self.progression_gates.get(puzzle_id, {})
            sequence = gate.get("sequence", [])
            if gate_id and progress >= len(sequence):
                room_state["opened_gates"].add(gate_id)
                return True
        else:
            room_state["puzzle_progress"][puzzle_id] = 0
        return False

    def _near_object(self) -> dict | None:
        room_state = self.room_states[self.current_room_id]
        for obj in self._interactable_objects():
            if obj.get("id") in room_state["interacted_objects"] and obj.get("type") not in {"puzzle_switch", "ship_console", "hologem_visualizer", "tea_relief"}:
                continue
            if abs(float(obj.get("x", 0.0)) - self.state.x) <= 7.0 and abs(float(obj.get("y", 0.0)) - self.state.y) <= 3.5:
                return obj
        return None

    def _platforms(self, room: dict | None = None) -> list[dict]:
        return list(self._room_layout(room).get("platforms", []))

    def _support_height(self, x: float, reference_y: float) -> float | None:
        support: float | None = None
        for platform in self._platforms():
            x1 = float(platform.get("x1", 0))
            x2 = float(platform.get("x2", 100))
            platform_y = float(platform.get("y", 0))
            if x < x1 or x > x2:
                continue
            if platform_y > reference_y + 0.6:
                continue
            if support is None or platform_y > support:
                support = platform_y
        return support

    def _entity_floor_height(self, x: float) -> float:
        return self._support_height(x, 100.0) or 0.0

    def _snap_player_to_support(self) -> None:
        support = self._support_height(self.state.x, max(self.state.y, 8.0))
        self.state.y = 0.0 if support is None else support
        self.state.vy = 0.0
        self.state.grounded = True

    def _sync_room_enemies(self) -> None:
        self.state.room_enemies = self.room_states[self.current_room_id]["enemies"]

    def _current_room(self) -> dict:
        return self.rooms[self.current_room_id]

    def _burst_pet(self) -> dict:
        return self.pet_definitions[self.loadout["burst"]]

    def _chorus_pet(self) -> dict:
        return self.pet_definitions[self.loadout["chorus"]]

    def _room_clear(self) -> bool:
        return all(enemy.hp <= 0 for enemy in self.state.room_enemies)

    def _active_boss(self) -> EnemyState | None:
        for enemy in self.state.room_enemies:
            if enemy.is_boss and enemy.hp > 0:
                return enemy
        return None

    def _find_target(self) -> EnemyState | None:
        living = [enemy for enemy in self.state.room_enemies if enemy.hp > 0]
        if not living:
            return None
        return min(living, key=lambda enemy: abs(enemy.x - self.state.x))

    def _trust_event(self, event: str, pet_id: str | None = None) -> None:
        """Update trust for a specific pet or all active pets."""
        ids = [pet_id] if pet_id else [self.loadout.get("burst"), self.loadout.get("chorus")] + list(self.loadout.get("crest", []))
        for pid in ids:
            if pid and pid in self.pet_definitions:
                current = self.state.pet_trust.get(pid, {"trust": 0.0, "bond_level": 0})
                self.state.pet_trust[pid] = update_pet_trust(current, event)
        self._crest_passive = crest_passive_effect(self._crest_pets, self.state.pet_trust)

    def _move_between_rooms(self, direction: str) -> None:
        room = self._current_room()
        exit_spec = room.get("exits", {}).get(direction)
        if not exit_spec:
            self.state.x = clamp(self.state.x, 0, 100)
            return
        if isinstance(exit_spec, str):
            destination = exit_spec
            requirement = None
            requires_room_clear = False
            required_gate = None
        else:
            destination = exit_spec.get("room")
            requirement = exit_spec.get("requires")
            requires_room_clear = bool(exit_spec.get("requires_room_clear", False))
            required_gate = exit_spec.get("requires_gate")
        if required_gate and required_gate not in self.room_states[self.current_room_id]["opened_gates"]:
            self.last_event = "A mechanical gate still blocks the route. Complete the local contraption chain first."
            self.state.x = clamp(self.state.x, 0, 100)
            return
        if requirement and requirement not in self.state.rescued_pets:
            self.last_event = f"A route shift blocks the way. {requirement.replace('_', ' ')} is required."
            self.state.x = clamp(self.state.x, 0, 100)
            return
        if requires_room_clear and not self._room_clear():
            self.last_event = "The route is locked until the local threat is stabilized."
            self.state.x = clamp(self.state.x, 0, 100)
            return
        if requirement and requirement in self.state.rescued_pets:
            pet_def = self.pet_definitions.get(requirement, {})
            if pet_def.get("lane") == "key":
                self._trust_event("route_opened", pet_id=requirement)
        self.current_room_id = destination
        self.state.x = 8 if direction == "right" else 92
        self._sync_room_enemies()
        self._snap_player_to_support()
        self.tick_flags["entered_room"] = destination
        self.last_event = f"Entered {self._current_room()['name']}."

    def _apply_room_physics(self, commands: dict[str, bool]) -> None:
        player_stats = self.document.get("player", {}).get("stats", {})
        move_speed = float(player_stats.get("move_speed", 2.4))
        jump_velocity = float(player_stats.get("jump_velocity", 5.4))
        gravity = float(player_stats.get("gravity", 0.34))
        movement_scale = 0.88 if self.state.chorus_active else 1.0
        if commands.get("left"):
            self.state.x -= move_speed * movement_scale
        if commands.get("right"):
            self.state.x += move_speed * movement_scale
        if commands.get("jump") and self.state.grounded:
            self.state.vy = jump_velocity
            self.state.grounded = False
            self.last_event = "Vault jump engaged."

        self.state.vy -= gravity
        next_y = self.state.y + self.state.vy
        support = self._support_height(self.state.x, max(self.state.y, next_y))
        if support is not None and self.state.vy <= 0 and next_y <= support:
            self.state.y = support
            self.state.vy = 0.0
            self.state.grounded = True
        else:
            self.state.y = next_y
            self.state.grounded = False

        if self.state.y < -6.0:
            self.state.hp = max(0, self.state.hp - 6)
            self.state.bond_tension = clamp(self.state.bond_tension + 9.0, 0, 100)
            self.state.x = 8.0
            self._snap_player_to_support()
            self.last_event = "You slip off the route and scramble back onto stable footing."

    def _apply_hazards(self) -> None:
        if self.state.damage_cooldown > 0:
            return
        for hazard in self._room_layout().get("hazards", []):
            x1 = float(hazard.get("x1", 0))
            x2 = float(hazard.get("x2", 0))
            hazard_y = float(hazard.get("y", 0))
            if x1 <= self.state.x <= x2 and abs(self.state.y - hazard_y) <= 1.0:
                damage = int(hazard.get("damage", 4))
                if self.state.chorus_active:
                    damage = max(1, damage - 1)
                self.state.hp = max(0, self.state.hp - damage)
                self.state.bond_tension = clamp(self.state.bond_tension + float(hazard.get("tension", 4.0)), 0, 100)
                self.state.damage_cooldown = 20
                self.last_event = hazard.get("event", f"{hazard.get('id', 'hazard')} clips the expedition for {damage}.")
                return

    def _apply_encounter_zones(self, directive: dict) -> dict:
        adjusted = dict(directive)
        zones = self._room_layout().get("encounter_zones", [])
        triggered = self.room_states[self.current_room_id]["zones_triggered"]
        active_zone = None
        for zone in zones:
            x1 = float(zone.get("x1", 0))
            x2 = float(zone.get("x2", 0))
            if x1 <= self.state.x <= x2:
                active_zone = zone
                adjusted["pressure_scale"] = round(adjusted["pressure_scale"] + float(zone.get("pressure_bonus", 0.0)), 3)
                adjusted["zone"] = zone.get("id")
                if zone.get("id") and zone.get("id") not in triggered and zone.get("event"):
                    triggered.add(zone["id"])
                    self.last_event = zone["event"]
                if zone.get("tension_bonus"):
                    self.state.bond_tension = clamp(self.state.bond_tension + float(zone.get("tension_bonus", 0.0)), 0, 100)
                break
        if active_zone is None:
            adjusted["zone"] = None
        return adjusted

    def _select_player_move(self, commands: dict[str, bool]) -> dict:
        combo_step = self.state.combo_step if self.state.combo_window_left > 0 else 0
        if not self.state.grounded:
            if self.state.vy < -1.0:
                return self.player_moves.get("dive_keel", {"name": "Dive Keel", "base_power": 1.2, "precision_window": 2, "weapon_points": 1})
            if self.state.vy > 1.0:
                return self.player_moves.get("rising_notch", {"name": "Rising Notch", "base_power": 1.1, "precision_window": 3, "weapon_points": 1})
            return self.player_moves.get("aerial_crescent", {"name": "Aerial Crescent", "base_power": 1.1, "precision_window": 3, "weapon_points": 1})
        if abs(self.state.move_delta_x) >= 4.0:
            return self.player_moves.get("dash_slash", {"name": "Dash Slash", "base_power": 1.15, "precision_window": 3, "weapon_points": 1})
        if combo_step == 0:
            return self.player_moves.get("salt_cut", {"name": "Salt Cut", "base_power": 1.0, "precision_window": 4, "weapon_points": 1})
        if combo_step == 1:
            return self.player_moves.get("rust_hook", {"name": "Rust Hook", "base_power": 1.18, "precision_window": 4, "weapon_points": 1})
        return self.player_moves.get("brass_splitter", {"name": "Brass Splitter", "base_power": 1.42, "precision_window": 5, "weapon_points": 2})

    def _precision_multiplier(self, target: EnemyState, move_profile: dict) -> tuple[float, bool]:
        timing_window = int(move_profile.get("precision_window", 0)) + self._precision_bonus()
        sweet_spot = 4.5 <= abs(target.x - self.state.x) <= 9.5
        timed = 0 < target.attack_cooldown <= max(1, timing_window)
        staggered = target.root_ticks > 0 or target.posture <= 12
        perfect = sweet_spot or timed or staggered
        return (1.22 if perfect else 1.0, perfect)

    def _resolve_enemy_move(self, enemy: EnemyState, directive: dict) -> dict:
        archetype = self.enemy_archetypes.get(enemy.name, {})
        move_table = list(self.boss_moves) if enemy.is_boss else list(archetype.get("moves", []))
        if not move_table:
            return {"name": "pressure strike", "damage": 4, "cooldown": 18, "range": 6, "windup": 3}
        distance = abs(enemy.x - self.state.x)
        move_index = min(len(move_table) - 1, int((distance + directive["pressure_scale"] * 2 + self.tick_count) % len(move_table)))
        candidate = move_table[move_index]
        if distance <= float(candidate.get("range", 6)):
            return candidate
        return min(move_table, key=lambda move: abs(float(move.get("range", 6)) - distance))

    def _attempt_interact(self) -> None:
        obj = self._near_object()
        if obj is None:
            self._attempt_rescue()
            return
        room_state = self.room_states[self.current_room_id]
        obj_type = obj.get("type")
        self.interaction_signal = {"type": obj_type, "object_id": obj.get("id"), "pet_id": obj.get("pet_id"), "item_id": obj.get("item_id")}
        if obj_type in {"gear_cache", "weapon_cache"}:
            item_id = obj.get("item_id")
            if item_id and item_id not in self.state.inventory:
                self.state.inventory.append(item_id)
                item = self.gear_catalog.get(item_id, {})
                if item.get("slot") == "weapon":
                    self.state.equipped_weapon = item_id
                elif item.get("slot") == "sidearm":
                    self.state.equipped_sidearm = item_id
                elif item.get("slot") == "relic":
                    self.state.equipped_relic = item_id
                room_state["interacted_objects"].add(obj["id"])
                self.last_event = obj.get("event", f"Recovered {item_id.replace('_', ' ')}.")
                return
        if obj_type == "xp_cache":
            self._gain_experience(int(obj.get("xp_award", 12)))
            self.state.weapon_points += int(obj.get("weapon_points", 0))
            room_state["interacted_objects"].add(obj["id"])
            self.last_event = obj.get("event", "Study and salvage translate into growth.")
            return
        if obj_type == "tea_relief":
            self.state.bond_tension = clamp(self.state.bond_tension - float(obj.get("tension_relief", 6.0)), 0, 100)
            self.last_event = obj.get("event", "Tea settles the roster.")
            return
        if obj_type == "puzzle_switch":
            opened = self._progress_gate(str(obj.get("puzzle_id")), int(obj.get("sequence_index", 0)), obj.get("unlock_gate"))
            if opened:
                self.last_event = obj.get("event", "The final relay opens a heavy gate.")
            else:
                self.last_event = obj.get("event", "A mechanical relay advances somewhere nearby.")
            return
        if obj_type == "ship_console":
            self.last_event = obj.get("event", "A ship route hums at the edge of the desert.")
            return
        if obj_type == "hologem_visualizer":
            self.state.tutorial_pet = obj.get("pet_id")
            self.last_event = obj.get("event", "A hologem lesson spins up around the Munki.")
            return
        if obj_type == "merchant":
            self.last_event = obj.get("event", "The quartermaster explains how salvage and gear bend a route.")
            return
        self.last_event = obj.get("event", f"Interacted with {obj.get('label', 'the object')}.")

    def _apply_primary_attack(self, directive: dict) -> None:
        if self.state.attack_cooldown > 0:
            return None
        target = self._find_target()
        if target is None or abs(target.x - self.state.x) > 12:
            self.last_event = "The strike cuts empty air."
            self.state.attack_cooldown = 8
            self.state.combo_step = 0
            self.state.combo_window_left = 0
            return None
        move_profile = self._select_player_move({})
        step = self.state.combo_step if self.state.combo_window_left > 0 else 0
        hit = combo_hit(step, self.document["player"]["stats"].get("power", 2.0) + self._weapon_power_bonus(), target.armor, directive["pressure_scale"])
        precision_mult, perfect = self._precision_multiplier(target, move_profile)
        hit_damage = max(1, int(round(hit["damage"] * float(move_profile.get("base_power", 1.0)) * precision_mult)))
        target.hp = max(0, target.hp - hit_damage)
        target.posture = max(0, target.posture - hit["posture_damage"])
        self.state.attack_cooldown = hit["cooldown"]
        charge = hit["weave_charge"] + self._crest_passive["weave_charge_bonus"]
        self.state.bond_weave_charge = clamp(self.state.bond_weave_charge + charge, 0, 100)
        label = ["First", "Second", "Third"][min(step, 2)]
        self.state.weapon_points += int(move_profile.get("weapon_points", 0))
        timing_text = " with perfect timing" if perfect else ""
        self.last_event = f"{label} strike {move_profile.get('name', 'attack')} hits {target.name.replace('_', ' ')} for {hit_damage}{timing_text}."
        self.state.combo_step = min(step + 1, 2) if step < 2 else 0
        self.state.combo_window_left = COMBO_WINDOW if step < 2 else 0
        if target.hp == 0:
            self.last_event = f"{target.name.replace('_', ' ')} collapses."
            self.state.bond_weave_charge = clamp(self.state.bond_weave_charge + 12, 0, 100)
            self._gain_experience(int(self.enemy_archetypes.get(target.name, {}).get("xp", 18 if not target.is_boss else 110)))
            if target.is_boss:
                self.room_states[self.current_room_id]["boss_defeated"] = True
                self.tick_flags["boss_defeated_room"] = self.current_room_id
        return f"combo_{step + 1}"

    def _set_player_animation(self, animation_name: str, lock_ticks: int = 0) -> None:
        if self.state.animation_name != animation_name:
            self.state.animation_started_tick = self.tick_count
        self.state.animation_name = animation_name
        self.state.animation_lock_ticks = lock_ticks

    def _update_player_animation(self, requested_animation: str | None = None) -> None:
        combo_locks = {
            "combo_1": 26,
            "combo_2": 13,
            "combo_3": 13,
        }
        if requested_animation:
            self._set_player_animation(requested_animation, combo_locks.get(requested_animation, 0))
            return
        if not self.state.grounded:
            self._set_player_animation("jump")
            return
        if self.state.animation_lock_ticks > 0 and self.state.animation_name.startswith("combo_"):
            self.state.animation_lock_ticks -= 1
            return
        locomotion = "run" if abs(self.state.move_delta_x) >= 4.0 else "walk" if abs(self.state.move_delta_x) > 0.05 else "idle"
        self._set_player_animation(locomotion)

    def _apply_burst(self, directive: dict) -> None:
        if self.state.burst_cooldown > 0:
            return
        pet = self._burst_pet()
        if self.state.bond_tension >= 92:
            self.last_event = "Bond tension is too high for a Burst command."
            return
        target = self._find_target()
        if target is None:
            self.last_event = f"{pet['name']} circles without a target."
            self.state.burst_cooldown = 12
            self.state.bond_tension = clamp(self.state.bond_tension + 4, 0, 100)
            return
        effect = burst_pet_effect(pet, directive["pressure_scale"], bond_level=self.state.pet_trust.get(self.loadout["burst"], {}).get("bond_level", 0))
        target.hp = max(0, target.hp - effect["damage"])
        target.posture = max(0, target.posture - effect["posture"])
        target.root_ticks = max(target.root_ticks, effect["root_ticks"])
        self.state.burst_cooldown = int(pet.get("cooldown", 22))
        self.state.bond_tension = clamp(self.state.bond_tension + float(pet.get("tension_cost", 8)), 0, 100)
        self.state.bond_weave_charge = clamp(self.state.bond_weave_charge + 14, 0, 100)
        self._trust_event("burst_used", pet_id=self.loadout["burst"])
        self.last_event = f"{pet['name']} triggers a Burst command against {target.name.replace('_', ' ')}."

    def _toggle_chorus(self) -> None:
        self.state.chorus_active = not self.state.chorus_active
        pet = self._chorus_pet()
        state = "active" if self.state.chorus_active else "resting"
        self.last_event = f"{pet['name']} is now {state}."

    def _dodge(self, directive: dict) -> None:
        if self.state.dodge_cooldown > 0:
            return
        focus = self._find_target()
        success = focus is not None and abs(focus.x - self.state.x) <= 10 and directive["recommended_style"] in {"dodge_counter", "stabilize"}
        self.state.x += 9 if success else 5
        self.state.dodge_cooldown = 14
        if success:
            self.state.bond_tension = clamp(self.state.bond_tension - perfect_dodge_relief(), 0, 100)
            self.state.bond_weave_charge = clamp(self.state.bond_weave_charge + 10, 0, 100)
            self._trust_event("perfect_dodge")
            self.last_event = "Perfect dodge. The bond settles."
        else:
            self.last_event = "Short dodge executed."

    def _attempt_rescue(self) -> None:
        room = self._current_room()
        rescue = room.get("rescue")
        if not rescue:
            return
        if self.room_states[self.current_room_id]["rescued"]:
            return
        if not self._room_clear():
            self.last_event = "The room is still hostile. Calm it before attempting a rescue."
            return
        if abs(self.state.x - float(rescue.get("x", 50))) > 8:
            self.last_event = "Move closer to the distressed SimIAM to stabilize the bond."
            return
        pet_id = rescue["pet"]
        self.state.rescued_pets.add(pet_id)
        self.room_states[self.current_room_id]["rescued"] = True
        self.tick_flags["rescued_pet"] = pet_id
        self._trust_event("rescue", pet_id=pet_id)
        self.last_event = f"Rescued {self.pet_definitions[pet_id]['name']}."

    def _rest(self) -> None:
        room = self._current_room()
        if not room.get("safe_room"):
            return
        self.state.hp = self.state.max_hp
        self.state.bond_tension = max(0.0, self.state.bond_tension - 28.0)
        self.tick_flags["rested_room"] = self.current_room_id
        self.last_event = "You rest, repair gear, and settle the SimIAM roster."

    def _bond_weave(self) -> None:
        if self.state.bond_weave_charge < 100:
            self.last_event = "Bond weave is not ready."
            return
        target = self._find_target()
        if target is None:
            self.last_event = "The weave unspools harmlessly."
            self.state.bond_weave_charge = 0
            return
        if target.is_boss:
            requirements = dict(self._current_room().get("bond_weave", {}))
            requirements.update(target.weave_gate)
            missing = []
            posture_limit = float(requirements.get("posture_at_most", 24))
            if target.posture > posture_limit:
                missing.append("break the boss posture")
            required_chorus = requirements.get("requires_chorus")
            if required_chorus and not (self.state.chorus_active and self.loadout["chorus"] == required_chorus):
                missing.append(f"sustain {required_chorus.replace('_', ' ')}")
            if requirements.get("requires_rooted") and target.root_ticks <= 0:
                missing.append("pin the boss with a rooted window")
            for pet_id in requirements.get("requires_rescued_pets", []):
                if pet_id not in self.state.rescued_pets:
                    missing.append(pet_id.replace("_", " "))
            if missing:
                self.state.bond_weave_charge = clamp(self.state.bond_weave_charge - 18, 0, 100)
                self.state.bond_tension = clamp(self.state.bond_tension + 10, 0, 100)
                self.last_event = "Bond weave fails. Needed: " + ", ".join(missing) + "."
                return
            target.hp = 0
            target.posture = 0
            target.root_ticks = 0
            self.room_states[self.current_room_id]["boss_defeated"] = True
            self.tick_flags["boss_defeated_room"] = self.current_room_id
            self.state.bond_weave_charge = 0
            self.state.bond_tension = clamp(self.state.bond_tension + 4, 0, 100)
            self._trust_event("bond_weave")
            self.last_event = f"Bond weave completes. {target.name.replace('_', ' ')} is unraveled."
            return
        target.hp = max(0, target.hp - 22)
        target.posture = 0
        target.root_ticks = max(target.root_ticks, 6)
        self.state.bond_weave_charge = 0
        self.state.bond_tension = clamp(self.state.bond_tension + 6, 0, 100)
        self._trust_event("bond_weave")
        self.last_event = f"Bond weave pins {target.name.replace('_', ' ')} in place."

    def _update_enemy_ai(self, directive: dict) -> None:
        chorus_defense = 0.85 if self.state.chorus_active else 1.0
        for enemy in self.state.room_enemies:
            if enemy.hp <= 0:
                continue
            enemy.y = self._entity_floor_height(enemy.x)
            if enemy.root_ticks > 0:
                enemy.root_ticks -= 1
            else:
                step = 0.8 + (enemy.aggression * directive["pressure_scale"])
                if enemy.x < self.state.x:
                    enemy.x += step
                else:
                    enemy.x -= step
            if enemy.attack_cooldown > 0:
                enemy.attack_cooldown -= 1
                continue
            if abs(enemy.x - self.state.x) <= 6:
                enemy_move = self._resolve_enemy_move(enemy, directive)
                damage = max(1, int(round(float(enemy_move.get("damage", 4)) * directive["pressure_scale"] * chorus_defense)))
                if self._crest_passive["damage_reduction"] > 0:
                    damage = max(1, int(round(damage * (1.0 - self._crest_passive["damage_reduction"]))))
                if directive["mercy_window"]:
                    damage = max(1, damage - 1)
                if self.state.damage_cooldown > 0:
                    continue
                self.state.hp = max(0, self.state.hp - damage)
                tension_gain = 3.0 if not directive["mercy_window"] else 1.5
                self.state.bond_tension = clamp(self.state.bond_tension + tension_gain, 0, 100)
                if self.state.bond_tension >= 80:
                    self._trust_event("tension_spike")
                enemy.attack_cooldown = int(enemy_move.get("cooldown", 18))
                self.state.damage_cooldown = 16
                self.last_event = f"{enemy.name.replace('_', ' ')} uses {enemy_move.get('name', 'pressure strike')} for {damage}."

    def _cooldowns(self) -> None:
        if self.state.attack_cooldown > 0:
            self.state.attack_cooldown -= 1
        if self.state.burst_cooldown > 0:
            self.state.burst_cooldown -= 1
        if self.state.dodge_cooldown > 0:
            self.state.dodge_cooldown -= 1
        if self.state.damage_cooldown > 0:
            self.state.damage_cooldown -= 1
        if self.state.combo_window_left > 0:
            self.state.combo_window_left -= 1
            if self.state.combo_window_left == 0:
                self.state.combo_step = 0
        if self.state.chorus_active:
            self.state.bond_tension = clamp(self.state.bond_tension + chorus_drain_per_tick(self._chorus_pet()), 0, 100)
            self._trust_event("chorus_sustained", pet_id=self.loadout["chorus"])
        if self._crest_passive["tension_decay"] > 0 and self.state.bond_tension > 0:
            self.state.bond_tension = clamp(self.state.bond_tension - self._crest_passive["tension_decay"], 0, 100)
            self._trust_event("crest_passive_tick")

    def _criteria_complete(self, milestone: dict) -> bool:
        criteria = milestone.get("criteria", {})
        previous = set(criteria.get("requires_previous", []))
        if not previous.issubset(self.state.completed_milestones):
            return False
        if criteria.get("rested_in_room"):
            return self.tick_flags["rested_room"] == criteria["rested_in_room"]
        if criteria.get("rescued_pet"):
            return self.tick_flags["rescued_pet"] == criteria["rescued_pet"]
        if criteria.get("room_clear_in_room"):
            return self.tick_flags["room_cleared"] == criteria["room_clear_in_room"]
        if criteria.get("boss_defeated_in_room"):
            return self.tick_flags["boss_defeated_room"] == criteria["boss_defeated_in_room"]
        if criteria.get("entered_room"):
            return self.tick_flags["entered_room"] == criteria["entered_room"]
        if criteria.get("requires_rescued_pets"):
            return set(criteria["requires_rescued_pets"]).issubset(self.state.rescued_pets)
        return False

    def _update_milestones(self) -> None:
        for milestone in self.milestone_defs:
            milestone_id = milestone.get("id")
            if not milestone_id or milestone_id in self.state.completed_milestones:
                continue
            if self._criteria_complete(milestone):
                self.state.completed_milestones.add(milestone_id)
                self.last_event = f"Milestone complete: {milestone.get('label', milestone_id)}."

    def export_save_data(self) -> dict:
        room_states = {}
        for room_id, room_state in self.room_states.items():
            room_states[room_id] = {
                "rescued": room_state["rescued"],
                "boss_defeated": room_state["boss_defeated"],
                "zones_triggered": sorted(room_state["zones_triggered"]),
                "interacted_objects": sorted(room_state["interacted_objects"]),
                "opened_gates": sorted(room_state["opened_gates"]),
                "puzzle_progress": dict(room_state["puzzle_progress"]),
                "enemies": [
                    {
                        "name": enemy.name,
                        "x": enemy.x,
                        "y": enemy.y,
                        "hp": enemy.hp,
                        "max_hp": enemy.max_hp,
                        "aggression": enemy.aggression,
                        "armor": enemy.armor,
                        "posture": enemy.posture,
                        "is_boss": enemy.is_boss,
                        "root_ticks": enemy.root_ticks,
                        "attack_cooldown": enemy.attack_cooldown,
                        "weave_gate": dict(enemy.weave_gate),
                    }
                    for enemy in room_state["enemies"]
                ],
            }
        return {
            "format": "illusioncanvas.save.v1",
            "current_room_id": self.current_room_id,
            "player": {
                "x": self.state.x,
                "y": self.state.y,
                "vy": self.state.vy,
                "hp": self.state.hp,
                "max_hp": self.state.max_hp,
                "bond_tension": self.state.bond_tension,
                "attack_cooldown": self.state.attack_cooldown,
                "burst_cooldown": self.state.burst_cooldown,
                "dodge_cooldown": self.state.dodge_cooldown,
                "damage_cooldown": self.state.damage_cooldown,
                "chorus_active": self.state.chorus_active,
                "grounded": self.state.grounded,
                "bond_weave_charge": self.state.bond_weave_charge,
                "rescued_pets": sorted(self.state.rescued_pets),
                "completed_milestones": sorted(self.state.completed_milestones),
                "combo_step": self.state.combo_step,
                "combo_window_left": self.state.combo_window_left,
                "pet_trust": dict(self.state.pet_trust),
                "facing": self.state.facing,
                "animation_name": self.state.animation_name,
                "animation_started_tick": self.state.animation_started_tick,
                "animation_lock_ticks": self.state.animation_lock_ticks,
                "level": self.state.level,
                "experience": self.state.experience,
                "weapon_points": self.state.weapon_points,
                "equipped_weapon": self.state.equipped_weapon,
                "equipped_sidearm": self.state.equipped_sidearm,
                "equipped_relic": self.state.equipped_relic,
                "inventory": list(self.state.inventory),
                "tutorial_pet": self.state.tutorial_pet,
            },
            "room_states": room_states,
        }

    def load_save_data(self, save_data: dict) -> None:
        player = save_data.get("player", {})
        self.current_room_id = save_data.get("current_room_id", self.current_room_id)
        self.state.x = float(player.get("x", self.state.x))
        self.state.y = float(player.get("y", self.state.y))
        self.state.vy = float(player.get("vy", 0.0))
        self.state.hp = int(player.get("hp", self.state.hp))
        self.state.max_hp = int(player.get("max_hp", self.state.max_hp))
        self.state.bond_tension = float(player.get("bond_tension", self.state.bond_tension))
        self.state.attack_cooldown = int(player.get("attack_cooldown", 0))
        self.state.burst_cooldown = int(player.get("burst_cooldown", 0))
        self.state.dodge_cooldown = int(player.get("dodge_cooldown", 0))
        self.state.damage_cooldown = int(player.get("damage_cooldown", 0))
        self.state.chorus_active = bool(player.get("chorus_active", False))
        self.state.grounded = bool(player.get("grounded", True))
        self.state.bond_weave_charge = float(player.get("bond_weave_charge", 0.0))
        self.state.rescued_pets = set(player.get("rescued_pets", []))
        self.state.completed_milestones = set(player.get("completed_milestones", []))
        self.state.combo_step = int(player.get("combo_step", 0))
        self.state.combo_window_left = int(player.get("combo_window_left", 0))
        self.state.pet_trust = dict(player.get("pet_trust", {}))
        self.state.facing = -1 if int(player.get("facing", 1)) < 0 else 1
        self.state.animation_name = str(player.get("animation_name", "idle"))
        self.state.animation_started_tick = int(player.get("animation_started_tick", 0))
        self.state.animation_lock_ticks = int(player.get("animation_lock_ticks", 0))
        self.state.level = int(player.get("level", self.state.level))
        self.state.experience = int(player.get("experience", self.state.experience))
        self.state.weapon_points = int(player.get("weapon_points", self.state.weapon_points))
        self.state.equipped_weapon = str(player.get("equipped_weapon", self.state.equipped_weapon))
        self.state.equipped_sidearm = str(player.get("equipped_sidearm", self.state.equipped_sidearm))
        self.state.equipped_relic = str(player.get("equipped_relic", self.state.equipped_relic))
        self.state.inventory = list(player.get("inventory", self.state.inventory))
        self.state.tutorial_pet = player.get("tutorial_pet")

        for room_id, room_state in save_data.get("room_states", {}).items():
            if room_id not in self.room_states:
                continue
            rebuilt_enemies = []
            for enemy_data in room_state.get("enemies", []):
                rebuilt_enemies.append(
                    EnemyState(
                        name=enemy_data["name"],
                        x=float(enemy_data.get("x", 0.0)),
                        y=float(enemy_data.get("y", 0.0)),
                        hp=int(enemy_data.get("hp", 0)),
                        max_hp=int(enemy_data.get("max_hp", enemy_data.get("hp", 0))),
                        aggression=float(enemy_data.get("aggression", 0.6)),
                        armor=float(enemy_data.get("armor", 1.0)),
                        posture=float(enemy_data.get("posture", 40.0)),
                        is_boss=bool(enemy_data.get("is_boss", False)),
                        weave_gate=dict(enemy_data.get("weave_gate", {})),
                        root_ticks=int(enemy_data.get("root_ticks", 0)),
                        attack_cooldown=int(enemy_data.get("attack_cooldown", 0)),
                    )
                )
            self.room_states[room_id] = {
                "enemies": rebuilt_enemies,
                "rescued": bool(room_state.get("rescued", False)),
                "boss_defeated": bool(room_state.get("boss_defeated", False)),
                "zones_triggered": set(room_state.get("zones_triggered", [])),
                "interacted_objects": set(room_state.get("interacted_objects", [])),
                "opened_gates": set(room_state.get("opened_gates", [])),
                "puzzle_progress": dict(room_state.get("puzzle_progress", {})),
            }
        self._sync_room_enemies()
        self.last_event = "Loaded persistent expedition state."

    def step(self, commands: dict[str, bool]) -> dict:
        self.tick_count += 1
        self.tick_flags = self._empty_tick_flags()
        self.interaction_signal = None
        room = self._current_room()
        starting_x = self.state.x
        starting_room_id = self.current_room_id
        reading = self.egosphere.read_encounter(self.state, self.state.room_enemies)
        directive = self.godai.evaluate(self.state, room, reading)
        room_clear_before = self._room_clear()

        self._apply_room_physics(commands)

        requested_animation = None
        if commands.get("attack"):
            requested_animation = self._apply_primary_attack(directive)
        if commands.get("burst"):
            self._apply_burst(directive)
        if commands.get("chorus_toggle"):
            self._toggle_chorus()
        if commands.get("dodge"):
            self._dodge(directive)
        if commands.get("interact") or commands.get("rescue"):
            self._attempt_interact()
        if commands.get("rest"):
            self._rest()
        if commands.get("bond_weave"):
            self._bond_weave()

        if self.state.x < 0:
            self._move_between_rooms("left")
        elif self.state.x > 100:
            self._move_between_rooms("right")
        else:
            self.state.x = clamp(self.state.x, 0, 100)

        if self.current_room_id != starting_room_id:
            self.state.move_delta_x = 0.0
        else:
            self.state.move_delta_x = round(self.state.x - starting_x, 2)
        if self.state.move_delta_x > 0.05:
            self.state.facing = 1
        elif self.state.move_delta_x < -0.05:
            self.state.facing = -1

        directive = self._apply_encounter_zones(directive)
        self._update_enemy_ai(directive)
        self._apply_hazards()
        self._cooldowns()
        self._update_player_animation(requested_animation)

        if not room_clear_before and self._room_clear():
            self.tick_flags["room_cleared"] = self.current_room_id
        self._update_milestones()

        living_enemies = [enemy for enemy in self.state.room_enemies if enemy.hp > 0]
        self.last_tick_gnosis = self.tick_gnosis.capture(
            tick=self.tick_count,
            frame_delta_ms=16.667,
            entity_count=1 + len(living_enemies),
            energy_total=float(self.state.hp + self.state.bond_tension + sum(enemy.hp for enemy in living_enemies)),
            camera_motion=abs(self.state.vy) + (1.0 if commands.get('left') or commands.get('right') else 0.0),
            input_pressure=float(sum(1 for value in commands.values() if value)),
            recursion_depth=1.0 + len(self.room_states[self.current_room_id]['zones_triggered']) * 0.35,
        )

        if self.state.hp == 0:
            self.last_event = "The expedition falls. Return to the refuge and tune the roster."
        return self.snapshot(directive)

    def snapshot(self, directive: dict | None = None) -> dict:
        room = self._current_room()
        rescue = room.get("rescue")
        rescued = self.room_states[self.current_room_id]["rescued"]
        boss_defeated = self.room_states[self.current_room_id]["boss_defeated"]
        if directive is None:
            directive = self.godai.evaluate(self.state, room, self.egosphere.read_encounter(self.state, self.state.room_enemies))
        return {
            "room": room,
            "player": {
                "x": self.state.x,
                "y": round(self.state.y, 2),
                "vy": round(self.state.vy, 2),
                "grounded": self.state.grounded,
                "hp": self.state.hp,
                "max_hp": self.state.max_hp,
                "bond_tension": round(self.state.bond_tension, 1),
                "attack_cooldown": self.state.attack_cooldown,
                "burst_cooldown": self.state.burst_cooldown,
                "chorus_active": self.state.chorus_active,
                "bond_weave_charge": round(self.state.bond_weave_charge, 1),
                "rescued_pets": sorted(self.state.rescued_pets),
                "facing": self.state.facing,
                "move_delta_x": self.state.move_delta_x,
                "animation": {
                    "name": self.state.animation_name,
                    "started_tick": self.state.animation_started_tick,
                    "lock_ticks": self.state.animation_lock_ticks,
                },
                "level": self.state.level,
                "experience": self.state.experience,
                "weapon_points": self.state.weapon_points,
                "equipped_weapon": self.state.equipped_weapon,
                "equipped_sidearm": self.state.equipped_sidearm,
                "equipped_relic": self.state.equipped_relic,
                "inventory": list(self.state.inventory),
                "tutorial_pet": self.state.tutorial_pet,
            },
            "enemies": [
                {
                    "name": enemy.name,
                    "x": enemy.x,
                    "y": round(enemy.y, 2),
                    "hp": enemy.hp,
                    "max_hp": enemy.max_hp,
                    "posture": enemy.posture,
                    "root_ticks": enemy.root_ticks,
                }
                for enemy in self.state.room_enemies
                if enemy.hp > 0
            ],
            "directive": directive,
            "objective": room.get("objective", ""),
            "tutorial_tip": room.get("tutorial_tip", ""),
            "room_popup": room.get("popup", {}),
            "boss_defeated": boss_defeated,
            "rescue": None if not rescue or rescued else rescue,
            "loadout": self.loadout,
            "pet_trust": dict(self.state.pet_trust),
            "crest_passive": self._crest_passive,
            "interaction": self.interaction_signal,
            "available_moves": list(self.prototype.get("player_moves", [])),
            "pet_tutorial_moves": list(self.prototype.get("pet_tutorial_moves", [])),
            "gear_catalog": list(self.prototype.get("gear_catalog", [])),
            "ship_adventure_mode": dict(self.prototype.get("ship_adventure_mode", {})),
            "milestones": [
                {
                    "id": milestone.get("id"),
                    "label": milestone.get("label", milestone.get("id", "milestone")),
                    "completed": milestone.get("id") in self.state.completed_milestones,
                }
                for milestone in self.milestone_defs
            ],
            "route_progress": {
                "completed": len(self.state.completed_milestones),
                "total": len(self.milestone_defs),
            },
            "tick_gnosis": self.last_tick_gnosis,
            "event": self.last_event,
            "tick": self.tick_count,
        }