from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xenobloods_systems import LifeForm, Plane, PlayerState


class GameplayMode(str, Enum):
    LAND_NAVIGATION = "land_navigation"
    UP_DIALOGUE = "up_dialogue"
    LOW_PUZZLE = "low_puzzle"
    COLLISION_RACE = "collision_race"
    BATTLE_SCENE = "battle_scene"
    BOSS_REALTIME = "boss_realtime"


@dataclass(frozen=True)
class PrototypeActor:
    actor_id: str
    label: str
    preview_name: str | None
    plane: Plane
    threat: float
    expected_action: str
    expected_lane: str


@dataclass
class CollisionRaceState:
    enemy_id: str
    distance: float = 1.0
    player_progress: float = 0.0
    enemy_progress: float = 0.0
    preemptive_window: tuple[float, float] = (0.44, 0.62)
    preemptive_damage: float = 12.0
    resolved: bool = False


@dataclass
class BattleExchangeState:
    enemy_id: str
    enemy_health: float
    player_health: float
    beat_index: int = 0
    telegraphs: list[tuple[str, str]] = field(default_factory=list)
    last_resolution: str = ""


@dataclass
class DialogueState:
    npc_id: str
    suspicion: float = 0.0
    exchange_index: int = 0
    safe_card: str = "defer"
    last_resolution: str = ""


@dataclass
class LowPuzzleState:
    curgz_id: str
    progress: int = 0
    target_progress: int = 3
    last_resolution: str = ""


ACTORS: dict[str, PrototypeActor] = {
    "scarab_child_acolyte": PrototypeActor("scarab_child_acolyte", "Scarab Child Acolyte", "scarab-child-basic-preview", Plane.LAND, 0.42, "attack", "foreground"),
    "lattice_ward": PrototypeActor("lattice_ward", "Lattice Ward", None, Plane.LAND, 0.58, "parry", "midground"),
    "lahgroid_hierophant": PrototypeActor("lahgroid_hierophant", "Lahgroid Hierophant", "lahgroid-boss-preview", Plane.LAND, 0.94, "dodge", "background"),
    "opal_tetrarch": PrototypeActor("opal_tetrarch", "Opal Tetrarch", None, Plane.UP, 0.74, "defer", "background"),
    "auditor_sal": PrototypeActor("auditor_sal", "Auditor Sal", None, Plane.UP, 0.78, "answer", "midground"),
    "verdict_chorister": PrototypeActor("verdict_chorister", "Verdict Chorister", None, Plane.UP, 0.68, "appease", "foreground"),
    "curgz_alpha": PrototypeActor("curgz_alpha", "Curgz Alpha", None, Plane.LOW, 0.5, "redirect", "midground"),
    "curgz_beta": PrototypeActor("curgz_beta", "Curgz Beta", None, Plane.LOW, 0.56, "redirect", "background"),
    "curgz_gamma": PrototypeActor("curgz_gamma", "Curgz Gamma", None, Plane.LOW, 0.62, "redirect", "foreground"),
}


STANDARD_TELEGRAPHS = {
    "scarab_child_acolyte": [("attack", "foreground"), ("dodge", "midground"), ("parry", "foreground")],
    "lattice_ward": [("parry", "midground"), ("block", "foreground"), ("attack", "midground")],
}

LAHGROID_TELEGRAPHS = [
    ("dodge", "background"),
    ("parry", "midground"),
    ("attack", "foreground"),
    ("block", "background"),
]


class GameplayPrototypeController:
    def __init__(self, player: PlayerState) -> None:
        self.player = player
        self.mode = GameplayMode.LAND_NAVIGATION
        self.current_zone = "veinmarket"
        self.current_actor_id = "scarab_child_acolyte"
        self.collision_state: CollisionRaceState | None = None
        self.battle_state: BattleExchangeState | None = None
        self.dialogue_state: DialogueState | None = None
        self.low_puzzle_state: LowPuzzleState | None = None
        self.status_text = "Land navigation active. Seek eye contact to begin an encounter."

    def enter_land_navigation(self, zone: str = "veinmarket") -> None:
        self.current_zone = zone
        self.mode = GameplayMode.LAND_NAVIGATION
        self.player.plane = Plane.LAND
        self.current_actor_id = "scarab_child_acolyte"
        self.collision_state = None
        self.battle_state = None
        self.dialogue_state = None
        self.low_puzzle_state = None
        if self.player.life_form == LifeForm.LANDBORNE:
            self.status_text = "Land navigation active. Eye-lock with a sparse encounter to start the collision race."
        elif self.player.life_form == LifeForm.GOURD_INFANT:
            self.status_text = "The infant vessel is not yet born into Land. Complete the amniotic gourd birth sequence first."
        else:
            self.status_text = "The etheric current has found Land, but it still needs the amniotic gourd to be born into a vessel."

    def route_to_up_dialogue(self, npc_id: str = "opal_tetrarch") -> None:
        self.mode = GameplayMode.UP_DIALOGUE
        self.player.route_from_shrine(Plane.UP)
        self.current_actor_id = npc_id
        safe_card = "defer" if npc_id == "opal_tetrarch" else "answer"
        if npc_id == "verdict_chorister":
            safe_card = "appease"
        self.dialogue_state = DialogueState(npc_id=npc_id, safe_card=safe_card)
        self.low_puzzle_state = None
        self.collision_state = None
        self.battle_state = None
        self.status_text = f"Up dialogue active with {ACTORS[npc_id].label}. Literal cards only exist here."

    def route_to_low_puzzle(self, curgz_id: str = "curgz_alpha") -> None:
        self.mode = GameplayMode.LOW_PUZZLE
        self.player.route_from_shrine(Plane.LOW)
        self.current_actor_id = curgz_id
        self.low_puzzle_state = LowPuzzleState(curgz_id=curgz_id)
        self.dialogue_state = None
        self.collision_state = None
        self.battle_state = None
        self.status_text = f"Low puzzle active with {ACTORS[curgz_id].label}. Route directed energy to collapse its gravity safely."

    def begin_eye_lock_encounter(self, enemy_id: str | None = None) -> None:
        if self.player.life_form != LifeForm.LANDBORNE:
            self.status_text = "Only the landborne vessel can force an eye-lock collision race."
            return
        enemy_id = enemy_id or self.current_actor_id
        self.current_actor_id = enemy_id
        self.mode = GameplayMode.COLLISION_RACE
        self.collision_state = CollisionRaceState(enemy_id=enemy_id)
        self.status_text = f"Eye contact established with {ACTORS[enemy_id].label}. Race to collision and time the preemptive strike."

    def advance_collision_race(self, player_push: float = 0.22, enemy_push: float = 0.18) -> None:
        if self.collision_state is None:
            return
        self.collision_state.player_progress = min(1.0, self.collision_state.player_progress + player_push)
        self.collision_state.enemy_progress = min(1.0, self.collision_state.enemy_progress + enemy_push)
        self.collision_state.distance = max(0.0, 1.0 - ((self.collision_state.player_progress + self.collision_state.enemy_progress) * 0.5))
        self.status_text = f"Collision race closing. Distance {self.collision_state.distance:.2f}. Commit attack inside the read window before impact."
        if self.collision_state.distance <= 0.0:
            self.resolve_collision(None)

    def resolve_collision(self, timing: float | None) -> None:
        if self.collision_state is None or self.collision_state.resolved:
            return
        preemptive = False
        enemy = ACTORS[self.collision_state.enemy_id]
        enemy_health = 44.0 if enemy.actor_id == "scarab_child_acolyte" else 62.0
        if timing is not None and self.collision_state.preemptive_window[0] <= timing <= self.collision_state.preemptive_window[1]:
            preemptive = True
            enemy_health -= self.collision_state.preemptive_damage
        self.collision_state.resolved = True
        self.mode = GameplayMode.BATTLE_SCENE
        telegraphs = list(STANDARD_TELEGRAPHS.get(enemy.actor_id, STANDARD_TELEGRAPHS["scarab_child_acolyte"]))
        self.battle_state = BattleExchangeState(enemy_id=enemy.actor_id, enemy_health=enemy_health, player_health=self._player_combat_health(), telegraphs=telegraphs)
        if preemptive:
            self.battle_state.last_resolution = "Preemptive damage dealt at collision. The battle begins with momentum in Ishtasha's favor."
        else:
            self.battle_state.last_resolution = "Collision reached without preemptive damage. The battle begins even."
        self.status_text = self.battle_state.last_resolution

    def resolve_battle_beat(self, action: str, timing: float, lane: str) -> None:
        if self.battle_state is None or self.mode != GameplayMode.BATTLE_SCENE:
            return
        expected_action, expected_lane = self.battle_state.telegraphs[self.battle_state.beat_index % len(self.battle_state.telegraphs)]
        score = 0.0
        if action == expected_action:
            score += 0.5
        if lane == expected_lane:
            score += 0.3
        score += max(0.0, 0.2 - abs(0.5 - timing))
        if score >= 0.85:
            self.battle_state.enemy_health = max(0.0, self.battle_state.enemy_health - 18.0)
            self.battle_state.last_resolution = f"Read confirmed: {action} at {lane}. Ishtasha wins the exchange decisively."
        elif score >= 0.55:
            self.battle_state.enemy_health = max(0.0, self.battle_state.enemy_health - 8.0)
            self.battle_state.player_health = max(0.0, self.battle_state.player_health - 3.0)
            self.battle_state.last_resolution = "Partial read. Both fighters connect, but Ishtasha retains tempo."
        else:
            self.battle_state.player_health = max(0.0, self.battle_state.player_health - 14.0)
            self.battle_state.last_resolution = "Read failed. The opponent presses into the next lane and punishes the turn."
        self.battle_state.beat_index += 1
        self.status_text = self.battle_state.last_resolution
        if self.battle_state.enemy_health <= 0.0:
            self.enter_land_navigation(self.current_zone)
            self.status_text = "Encounter cleared. Land navigation resumes with the next sparse enemy placement ahead."
        elif self.battle_state.player_health <= 0.0:
            self.player.die()
            self.status_text = "Ishtasha was overwhelmed in the exchange and shed back into ether."

    def begin_boss_sequence(self) -> None:
        self.mode = GameplayMode.BOSS_REALTIME
        self.current_actor_id = "lahgroid_hierophant"
        self.battle_state = BattleExchangeState(
            enemy_id="lahgroid_hierophant",
            enemy_health=120.0,
            player_health=self._player_combat_health() + 20.0,
            telegraphs=list(LAHGROID_TELEGRAPHS),
        )
        self.status_text = "Boss flow active. Lahgroid uses real-time lane shifts, ranged pressure, and chained punish windows."

    def resolve_boss_exchange(self, action: str, timing: float, lane: str, ranged: bool = False) -> None:
        if self.battle_state is None or self.mode != GameplayMode.BOSS_REALTIME:
            return
        expected_action, expected_lane = self.battle_state.telegraphs[self.battle_state.beat_index % len(self.battle_state.telegraphs)]
        score = 0.0
        if action == expected_action:
            score += 0.4
        if lane == expected_lane:
            score += 0.25
        if ranged and lane == "background":
            score += 0.15
        score += max(0.0, 0.25 - abs(0.5 - timing))
        if score >= 0.8:
            self.battle_state.enemy_health = max(0.0, self.battle_state.enemy_health - 16.0)
            self.battle_state.last_resolution = "Boss rhythm held. Ishtasha uses the full frame and wins the exchange."
        elif score >= 0.5:
            self.battle_state.enemy_health = max(0.0, self.battle_state.enemy_health - 7.0)
            self.battle_state.player_health = max(0.0, self.battle_state.player_health - 5.0)
            self.battle_state.last_resolution = "The flow remains contested across lanes and distance."
        else:
            self.battle_state.player_health = max(0.0, self.battle_state.player_health - 18.0)
            self.battle_state.last_resolution = "Lahgroid breaks the rhythm and forces a costly correction."
        self.battle_state.beat_index += 1
        self.status_text = self.battle_state.last_resolution
        if self.battle_state.enemy_health <= 0.0:
            self.enter_land_navigation("boss_gate")
            self.status_text = "Lahgroid falls. The Land zone opens past the boss gate."
        elif self.battle_state.player_health <= 0.0:
            self.player.die()
            self.status_text = "Lahgroid breaks the vessel and casts Ishtasha back into ether."

    def play_dialogue_card(self, card_id: str) -> None:
        if self.dialogue_state is None or self.mode != GameplayMode.UP_DIALOGUE:
            return
        self.dialogue_state.exchange_index += 1
        if card_id == self.dialogue_state.safe_card:
            self.dialogue_state.suspicion = max(0.0, self.dialogue_state.suspicion - 0.1)
            self.dialogue_state.last_resolution = "The tetrarch accepts the card. The exchange remains tense but survivable."
            self.status_text = self.dialogue_state.last_resolution
            return
        self.dialogue_state.suspicion += 0.55
        if self.dialogue_state.suspicion >= 0.5:
            self.route_to_low_puzzle("curgz_alpha")
            self.status_text = "The wrong card provokes instant smiting. Ishtasha is cast down into Low."
        else:
            self.dialogue_state.last_resolution = "The response lands poorly. One more mistake could trigger immediate smiting."
            self.status_text = self.dialogue_state.last_resolution

    def redirect_curgz_current(self, route: str) -> None:
        if self.low_puzzle_state is None or self.mode != GameplayMode.LOW_PUZZLE:
            return
        target = ["refract", "resist", "collapse"][self.low_puzzle_state.progress % 3]
        if route == target:
            self.low_puzzle_state.progress += 1
            self.low_puzzle_state.last_resolution = f"Current routed through {route}. Gravity collapse step {self.low_puzzle_state.progress}/{self.low_puzzle_state.target_progress}."
            self.status_text = self.low_puzzle_state.last_resolution
        else:
            self.low_puzzle_state.last_resolution = f"The {route} route destabilizes the field. The curgz begins to widen again."
            self.status_text = self.low_puzzle_state.last_resolution
        if self.low_puzzle_state.progress >= self.low_puzzle_state.target_progress:
            self.enter_land_navigation("veinmarket")
            self.status_text = "The curgz triad collapses safely. Ishtasha finds a route back toward Land."

    def current_actor(self) -> PrototypeActor:
        return ACTORS[self.current_actor_id]

    def preview_name_for_current_actor(self) -> str | None:
        return self.current_actor().preview_name

    def _player_combat_health(self) -> float:
        if self.player.life_form == LifeForm.GOURD_INFANT:
            return 36.0
        if self.player.life_form == LifeForm.ETHERIC_CURRENT:
            return 42.0
        return 72.0