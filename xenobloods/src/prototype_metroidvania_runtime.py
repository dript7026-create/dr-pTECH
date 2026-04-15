from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math

from prototype_gameplay_flow import GameplayMode, GameplayPrototypeController
from xenobloods_systems import LifeForm, Plane


class PresentationMode(str, Enum):
    TITLE = "title"
    INCUBATION = "incubation"
    EXPLORATION = "exploration"
    BATTLE = "battle"
    UP_DIALOGUE = "up_dialogue"
    LOW_PUZZLE = "low_puzzle"


class BattlePhase(str, Enum):
    EYECONTACT = "eyecontact"
    INTRO = "intro"
    WINDOW = "window"
    RESOLVE = "resolve"


@dataclass(frozen=True)
class EncounterCadenceProfile:
    label: str
    curve_index: int
    intro_duration: float
    window_duration: float
    resolve_duration: float
    eyecontact_rate: float
    arena_span: float
    timing_window_half: float
    pressure_speed: float


CADENCE_PROFILES: dict[str, EncounterCadenceProfile] = {
    "scarab_child_acolyte": EncounterCadenceProfile(
        label="Opening lesson",
        curve_index=1,
        intro_duration=0.84,
        window_duration=1.32,
        resolve_duration=0.56,
        eyecontact_rate=3.0,
        arena_span=0.34,
        timing_window_half=32.0,
        pressure_speed=0.84,
    ),
    "lattice_ward": EncounterCadenceProfile(
        label="Escalation",
        curve_index=2,
        intro_duration=0.68,
        window_duration=1.02,
        resolve_duration=0.56,
        eyecontact_rate=3.8,
        arena_span=0.44,
        timing_window_half=24.0,
        pressure_speed=1.02,
    ),
    "lahgroid_hierophant": EncounterCadenceProfile(
        label="Boss climax",
        curve_index=3,
        intro_duration=0.52,
        window_duration=0.82,
        resolve_duration=0.64,
        eyecontact_rate=0.0,
        arena_span=0.54,
        timing_window_half=16.0,
        pressure_speed=1.28,
    ),
}


@dataclass(frozen=True)
class RuntimeInput:
    move_x: float = 0.0
    move_y: float = 0.0
    jump_pressed: bool = False
    dash_pressed: bool = False
    dodge_pressed: bool = False
    interact_pressed: bool = False
    light_attack_pressed: bool = False
    heavy_attack_pressed: bool = False
    block_pressed: bool = False
    block_held: bool = False
    crouch_held: bool = False
    crawl_held: bool = False
    confirm_pressed: bool = False
    pause_pressed: bool = False


@dataclass(frozen=True)
class Platform:
    start_x: float
    end_x: float
    top_y: float


@dataclass(frozen=True)
class SpikeStrip:
    start_x: float
    end_x: float
    tip_y: float
    height: float = 28.0


@dataclass(frozen=True)
class SludgePatch:
    start_x: float
    end_x: float
    top_y: float
    depth: float = 20.0
    viscosity: float = 0.32


@dataclass
class GourdSegment:
    x: float
    y: float
    capacity_gain: float = 24.0
    stored_blood_bonus: float = 18.0
    label: str = "amniotic gourd segment"
    consumed: bool = False


@dataclass(frozen=True)
class AmbientEnemy:
    actor_id: str
    x: float
    ground_y: float
    scale: int = 90
    sway: float = 0.0
    lane: str = "midground"


@dataclass
class EncounterZone:
    start_x: float
    end_x: float
    enemy_id: str
    consumed: bool = False


@dataclass(frozen=True)
class RoomDefinition:
    room_id: str
    width: float
    ground_y: float
    palette: tuple[str, str, str]
    landmark_heights: tuple[int, ...]
    platforms: tuple[Platform, ...]
    spikes: tuple[SpikeStrip, ...]
    sludge_patches: tuple[SludgePatch, ...]
    gourd_segments: tuple[GourdSegment, ...]
    ambient_enemies: tuple[AmbientEnemy, ...]
    encounters: tuple[EncounterZone, ...]
    next_room: str | None = None
    previous_room: str | None = None
    gate_rule: str | None = None


ROOMS: dict[str, RoomDefinition] = {
    "veinmarket": RoomDefinition(
        room_id="veinmarket",
        width=1860.0,
        ground_y=592.0,
        palette=("#071019", "#101b29", "#21151a"),
        landmark_heights=(224, 260, 206, 248, 214, 238),
        platforms=(
            Platform(368.0, 556.0, 544.0),
            Platform(646.0, 796.0, 498.0),
            Platform(878.0, 1012.0, 452.0),
            Platform(1088.0, 1210.0, 504.0),
            Platform(1312.0, 1444.0, 462.0),
            Platform(1518.0, 1644.0, 516.0),
        ),
        spikes=(
            SpikeStrip(684.0, 768.0, 592.0),
            SpikeStrip(1110.0, 1190.0, 592.0),
            SpikeStrip(1330.0, 1426.0, 552.0),
        ),
        sludge_patches=(
            SludgePatch(232.0, 328.0, 592.0, depth=18.0, viscosity=0.26),
            SludgePatch(954.0, 1052.0, 592.0, depth=24.0, viscosity=0.34),
            SludgePatch(1540.0, 1604.0, 516.0, depth=14.0, viscosity=0.28),
        ),
        gourd_segments=(
            GourdSegment(522.0, 544.0, label="split gourd rib"),
            GourdSegment(1572.0, 516.0, label="vein-warm cradle shard"),
        ),
        ambient_enemies=(
            AmbientEnemy("scarab_child_acolyte", 462.0, 544.0, scale=84, sway=0.4, lane="foreground"),
            AmbientEnemy("lattice_ward", 930.0, 452.0, scale=78, sway=1.0, lane="background"),
            AmbientEnemy("scarab_child_acolyte", 1496.0, 516.0, scale=74, sway=1.8, lane="midground"),
        ),
        encounters=(
            EncounterZone(1210.0, 1360.0, "scarab_child_acolyte"),
        ),
        next_room="ossuary_rise",
    ),
    "ossuary_rise": RoomDefinition(
        room_id="ossuary_rise",
        width=2140.0,
        ground_y=584.0,
        palette=("#091019", "#132030", "#2a1c24"),
        landmark_heights=(248, 196, 282, 218, 258, 210),
        platforms=(
            Platform(324.0, 474.0, 546.0),
            Platform(566.0, 712.0, 506.0),
            Platform(848.0, 972.0, 462.0),
            Platform(1032.0, 1144.0, 430.0),
            Platform(1268.0, 1388.0, 474.0),
            Platform(1486.0, 1596.0, 434.0),
            Platform(1718.0, 1822.0, 492.0),
            Platform(1914.0, 2022.0, 528.0),
        ),
        spikes=(
            SpikeStrip(592.0, 688.0, 584.0),
            SpikeStrip(872.0, 948.0, 544.0),
            SpikeStrip(1048.0, 1128.0, 516.0),
            SpikeStrip(1510.0, 1582.0, 494.0),
        ),
        sludge_patches=(
            SludgePatch(214.0, 286.0, 584.0, depth=18.0, viscosity=0.28),
            SludgePatch(1192.0, 1264.0, 584.0, depth=24.0, viscosity=0.36),
            SludgePatch(1738.0, 1806.0, 492.0, depth=16.0, viscosity=0.30),
        ),
        gourd_segments=(
            GourdSegment(884.0, 462.0, capacity_gain=28.0, stored_blood_bonus=20.0, label="ossuary shell segment"),
        ),
        ambient_enemies=(
            AmbientEnemy("lattice_ward", 638.0, 506.0, scale=88, sway=0.9, lane="midground"),
            AmbientEnemy("scarab_child_acolyte", 1088.0, 430.0, scale=72, sway=1.6, lane="background"),
            AmbientEnemy("lattice_ward", 1766.0, 492.0, scale=82, sway=2.1, lane="foreground"),
        ),
        encounters=(
            EncounterZone(1020.0, 1160.0, "lattice_ward"),
        ),
        previous_room="veinmarket",
        next_room="boss_gate",
        gate_rule="clear_room",
    ),
    "boss_gate": RoomDefinition(
        room_id="boss_gate",
        width=2020.0,
        ground_y=590.0,
        palette=("#081017", "#172231", "#23161d"),
        landmark_heights=(264, 252, 230, 294, 246, 272),
        platforms=(
            Platform(468.0, 622.0, 548.0),
            Platform(720.0, 842.0, 506.0),
            Platform(968.0, 1098.0, 470.0),
            Platform(1204.0, 1328.0, 432.0),
            Platform(1420.0, 1536.0, 486.0),
        ),
        spikes=(
            SpikeStrip(744.0, 818.0, 590.0),
            SpikeStrip(988.0, 1076.0, 548.0),
            SpikeStrip(1222.0, 1310.0, 510.0),
        ),
        sludge_patches=(
            SludgePatch(310.0, 380.0, 590.0, depth=18.0, viscosity=0.24),
            SludgePatch(1450.0, 1518.0, 486.0, depth=16.0, viscosity=0.30),
        ),
        gourd_segments=(
            GourdSegment(988.0, 470.0, capacity_gain=30.0, stored_blood_bonus=22.0, label="gateborn cup segment"),
        ),
        ambient_enemies=(
            AmbientEnemy("scarab_child_acolyte", 558.0, 548.0, scale=76, sway=0.7, lane="foreground"),
            AmbientEnemy("lahgroid_hierophant", 1276.0, 432.0, scale=96, sway=1.3, lane="background"),
        ),
        encounters=(
            EncounterZone(1460.0, 1600.0, "lahgroid_hierophant"),
        ),
        previous_room="ossuary_rise",
        next_room="sunken_sanctum",
        gate_rule="boss_clear",
    ),
    "sunken_sanctum": RoomDefinition(
        room_id="sunken_sanctum",
        width=1480.0,
        ground_y=596.0,
        palette=("#0a1118", "#182534", "#18233c"),
        landmark_heights=(196, 188, 204, 178, 220, 198),
        platforms=(
            Platform(356.0, 498.0, 548.0),
            Platform(610.0, 736.0, 504.0),
            Platform(862.0, 986.0, 460.0),
        ),
        spikes=(
            SpikeStrip(636.0, 710.0, 596.0),
        ),
        sludge_patches=(
            SludgePatch(190.0, 280.0, 596.0, depth=20.0, viscosity=0.22),
            SludgePatch(906.0, 974.0, 460.0, depth=14.0, viscosity=0.26),
        ),
        gourd_segments=(
            GourdSegment(930.0, 460.0, capacity_gain=32.0, stored_blood_bonus=24.0, label="sanctum amnion shard"),
        ),
        ambient_enemies=(
            AmbientEnemy("lahgroid_hierophant", 674.0, 504.0, scale=82, sway=1.4, lane="midground"),
        ),
        encounters=(),
        previous_room="boss_gate",
    ),
}


@dataclass
class ExplorationState:
    room_id: str = "veinmarket"
    player_x: float = 220.0
    player_y: float = 592.0
    ground_y: float = 592.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    facing: int = 1
    on_ground: bool = True
    crouching: bool = False
    crawling: bool = False
    dodging: bool = False
    dash_timer: float = 0.0
    dodge_timer: float = 0.0
    camera_x: float = 0.0
    room_transition: float = 0.0
    transition_direction: int = 1
    gate_feedback: float = 0.0
    gate_locked: bool = False
    platforms: list[Platform] = field(default_factory=list)
    spikes: list[SpikeStrip] = field(default_factory=list)
    sludge_patches: list[SludgePatch] = field(default_factory=list)
    gourd_segments: list[GourdSegment] = field(default_factory=list)
    encounters: list[EncounterZone] = field(default_factory=list)
    hazard_cooldown: float = 0.0
    damage_flash: float = 0.0
    sludge_cling: float = 0.0
    hazard_impact_timer: float = 0.0
    hazard_impact_x: float = 0.0
    hazard_impact_y: float = 0.0
    last_safe_x: float = 220.0
    last_safe_y: float = 592.0


@dataclass
class BattlePresentationState:
    enemy_id: str = "scarab_child_acolyte"
    phase: BattlePhase = BattlePhase.EYECONTACT
    timer: float = 0.0
    camera_zoom: float = 1.0
    camera_shake: float = 0.0
    lane_bias: str = "midground"
    prompt_action: str = "attack"
    prompt_lane: str = "foreground"
    last_resolution_strength: float = 0.0
    eyecontact_progress: float = 0.0
    player_depth_bias: float = 0.0
    enemy_depth_bias: float = 0.0
    player_pose: str = "ready"
    enemy_pose: str = "ready"
    telegraph_strength: float = 0.0
    player_commit: float = 0.0
    enemy_commit: float = 0.0
    camera_pan: float = 0.0
    resolution_action: str = "attack"
    resolution_lane: str = "midground"
    eyecontact_hold: float = 0.0
    line_of_sight_strength: float = 0.0
    anticipation_flash: float = 0.0
    sound_cue_pending: bool = False
    resolution_quality: str = "neutral"
    resolution_timing_bucket: str = "center"
    player_battle_x: float = 0.28
    enemy_battle_x: float = 0.72
    proximity: float = 0.36
    selected_action: str = "block"
    selected_action_display: str = "block"
    exchange_precision: float = 0.0
    window_duration: float = 1.18
    intro_duration: float = 0.72
    resolve_duration: float = 0.52
    window_progress: float = 0.0
    time_dilation: float = 1.0
    tutorial_active: bool = False
    tutorial_page: int = 0
    tutorial_pages: tuple[str, ...] = ()
    cadence_label: str = "Opening lesson"
    curve_index: int = 1
    eyecontact_rate: float = 3.0
    arena_span: float = 0.34
    timing_window_half: float = 32.0
    pressure_speed: float = 0.84


@dataclass
class IncubationState:
    zone: str = "veinmarket"
    stage_index: int = 0
    pulse: float = 0.0
    birth_flash: float = 0.0
    tutorial_text: str = ""
    action_order: tuple[str, ...] = ("interact", "block", "jump", "dash")
    lane_order: tuple[str, ...] = ("midground", "foreground", "background", "foreground")
    timing_required: tuple[bool, ...] = (False, True, False, True)
    lane_bias: str = "midground"
    pulse_strength: float = 0.0
    pulse_progress: float = 0.0
    pulse_window_half: float = 0.13
    audio_event: str = ""
    audio_event_nonce: int = 0


class MetroidvaniaRuntime:
    def __init__(self, flow: GameplayPrototypeController) -> None:
        self.flow = flow
        self.mode = PresentationMode.TITLE
        self.exploration = ExplorationState()
        self.battle = BattlePresentationState()
        self.incubation = IncubationState()
        self.title_flash = 0.0
        self.pause_overlay = False
        self.tutorial_completed = False
        self.boss_defeated = False

    def start_game(self) -> None:
        self.mode = PresentationMode.INCUBATION
        self.pause_overlay = False
        self.boss_defeated = False
        self._begin_land_birth("veinmarket")

    def current_room(self) -> RoomDefinition:
        return ROOMS[self.exploration.room_id]

    def room_cleared(self, room_id: str) -> bool:
        room = ROOMS[room_id]
        return all(encounter.consumed for encounter in self.exploration.encounters) if room_id == self.exploration.room_id else all(encounter.enemy_id != room_id for encounter in self.exploration.encounters)

    def room_gate_open(self, room_id: str) -> bool:
        room = ROOMS[room_id]
        if room.gate_rule is None:
            return True
        if room.gate_rule == "clear_room":
            return all(encounter.consumed for encounter in self.exploration.encounters)
        if room.gate_rule == "boss_clear":
            return self._boss_defeated()
        return True

    def _make_room_state(self, room_id: str, entry_x: float | None = None) -> ExplorationState:
        room = ROOMS[room_id]
        return ExplorationState(
            room_id=room_id,
            player_x=entry_x if entry_x is not None else 220.0,
            player_y=room.ground_y,
            ground_y=room.ground_y,
            platforms=list(room.platforms),
            spikes=list(room.spikes),
            sludge_patches=list(room.sludge_patches),
            gourd_segments=[GourdSegment(segment.x, segment.y, segment.capacity_gain, segment.stored_blood_bonus, segment.label, segment.consumed) for segment in room.gourd_segments],
            encounters=[EncounterZone(enc.start_x, enc.end_x, enc.enemy_id, enc.consumed) for enc in room.encounters],
            last_safe_x=entry_x if entry_x is not None else 220.0,
            last_safe_y=room.ground_y,
        )

    def update(self, dt: float, controls: RuntimeInput) -> None:
        self.title_flash += dt
        if self.mode == PresentationMode.TITLE:
            if controls.confirm_pressed or controls.jump_pressed or controls.pause_pressed:
                self.start_game()
            return

        if controls.pause_pressed:
            self.pause_overlay = not self.pause_overlay
        if self.pause_overlay:
            return

        if self.mode == PresentationMode.INCUBATION:
            self._update_incubation(dt, controls)
            return
        if self.mode == PresentationMode.EXPLORATION:
            self._update_exploration(dt, controls)
            return
        if self.mode == PresentationMode.UP_DIALOGUE:
            self._update_up_dialogue(controls)
            return
        if self.mode == PresentationMode.LOW_PUZZLE:
            self._update_low_puzzle(controls)
            return
        self._update_battle(dt, controls)

    def _begin_land_birth(self, zone: str) -> None:
        player = self.flow.player
        if player.life_form != LifeForm.GOURD_INFANT:
            player.route_from_shrine(Plane.LAND)
            player.descend_into_land()
        self.flow.current_zone = zone
        self.incubation = IncubationState(zone=zone)
        self.incubation.tutorial_text = self._incubation_stage_text(0)
        self.mode = PresentationMode.INCUBATION
        self.flow.status_text = self.incubation.tutorial_text

    def _incubation_stage_text(self, stage_index: int) -> str:
        prompts = (
            "Birth 1/4. Gather the ether into the amniotic gourd. Stay centered in midground and press X to seed the vessel.",
            "Birth 2/4. Shift down into the foreground lane, then press LB inside the same bright center read the later combat QTE uses.",
            "Birth 3/4. Pull up into the background lane and press A to kick through the membrane.",
            "Birth 4/4. Drop back to the foreground and press Y inside the tighter center window to burst into Land as Ishtasha.",
        )
        return prompts[min(stage_index, len(prompts) - 1)]

    def _emit_incubation_audio_event(self, event: str) -> None:
        self.incubation.audio_event = event
        self.incubation.audio_event_nonce += 1

    def _birth_input_action(self, controls: RuntimeInput) -> str | None:
        if controls.interact_pressed:
            return "interact"
        if controls.block_pressed or controls.block_held:
            return "block"
        if controls.jump_pressed:
            return "jump"
        if controls.dash_pressed:
            return "dash"
        return None

    def _update_incubation(self, dt: float, controls: RuntimeInput) -> None:
        stage = self.incubation
        player = self.flow.player
        stage.pulse += dt
        pulse_timing = stage.pulse % 1.0
        stage.pulse_progress = self._ease_in_out_cubic(pulse_timing)
        window_profile = (0.24, 0.17, 0.2, 0.14)
        stage.pulse_window_half = window_profile[min(stage.stage_index, len(window_profile) - 1)]
        if stage.pulse_window_half > 0.0:
            stage.pulse_strength = max(0.0, 1.0 - (abs(stage.pulse_progress - 0.5) / stage.pulse_window_half))
        else:
            stage.pulse_strength = 0.0
        stage.birth_flash = max(0.0, stage.birth_flash - dt * 2.2)
        stage.lane_bias = self._lane_from_input(controls.move_y)
        action = self._birth_input_action(controls)
        if action is None:
            return
        expected = stage.action_order[min(stage.stage_index, len(stage.action_order) - 1)]
        expected_lane = stage.lane_order[min(stage.stage_index, len(stage.lane_order) - 1)]
        timing_required = stage.timing_required[min(stage.stage_index, len(stage.timing_required) - 1)]
        timing_ok = (not timing_required) or abs(stage.pulse_progress - 0.5) <= stage.pulse_window_half
        lane_ok = stage.lane_bias == expected_lane
        if action != expected or not lane_ok or not timing_ok:
            stage.birth_flash = max(stage.birth_flash, 0.35)
            self.flow.status_text = f"The vessel resists. {self._incubation_stage_text(stage.stage_index)}"
            self._emit_incubation_audio_event("birth_fail")
            return

        effort = {
            "interact": 22.0,
            "block": 24.0,
            "jump": 28.0,
            "dash": 30.0,
        }[action]
        player.struggle_in_gourd(effort)
        player.gourd.collect(6.0 + stage.stage_index * 3.0)
        stage.birth_flash = 1.0
        stage.pulse = 0.0
        stage.stage_index += 1
        self._emit_incubation_audio_event("birth_stage")
        if stage.stage_index >= len(stage.action_order) and player.hatch_from_gourd():
            self.flow.enter_land_navigation(stage.zone)
            self.mode = PresentationMode.EXPLORATION
            self.exploration = self._make_room_state(stage.zone)
            self._emit_incubation_audio_event("birth_complete")
            self.flow.status_text = "Ishtasha is born into Land. The amniotic gourd remains in inventory as a refillable healing vessel."
            return
        stage.tutorial_text = self._incubation_stage_text(stage.stage_index)
        self.flow.status_text = stage.tutorial_text

    def _update_exploration(self, dt: float, controls: RuntimeInput) -> None:
        state = self.exploration
        room = self.current_room()
        state.crouching = controls.crouch_held
        state.crawling = controls.crawl_held
        state.room_transition = max(0.0, state.room_transition - dt * 1.8)
        state.gate_feedback = max(0.0, state.gate_feedback - dt * 2.4)
        state.damage_flash = max(0.0, state.damage_flash - dt * 2.0)
        state.sludge_cling = max(0.0, state.sludge_cling - dt * 1.35)
        state.hazard_cooldown = max(0.0, state.hazard_cooldown - dt)
        state.hazard_impact_timer = max(0.0, state.hazard_impact_timer - dt * 2.4)
        if state.gate_feedback == 0.0:
            state.gate_locked = False

        move_speed = 220.0
        if state.crawling:
            move_speed = 96.0
        elif state.crouching:
            move_speed = 0.0

        move_speed *= 1.0 - self._sludge_viscosity_at(state.player_x, state.player_y, state.on_ground) * 0.58

        if state.dash_timer > 0.0:
            state.dash_timer = max(0.0, state.dash_timer - dt)
            state.velocity_x = 420.0 * state.facing
        elif state.dodge_timer > 0.0:
            state.dodge_timer = max(0.0, state.dodge_timer - dt)
            state.velocity_x = 340.0 * state.facing
        else:
            state.velocity_x = controls.move_x * move_speed
            if abs(controls.move_x) > 0.12:
                state.facing = 1 if controls.move_x > 0 else -1

        if controls.dash_pressed and state.on_ground:
            state.dash_timer = 0.18
        if controls.dodge_pressed and state.on_ground:
            state.dodge_timer = 0.34
            state.dodging = True
        else:
            state.dodging = state.dodge_timer > 0.0

        if controls.jump_pressed and state.on_ground and not state.crouching and not state.crawling:
            state.velocity_y = -428.0
            state.on_ground = False

        gravity = 980.0
        previous_y = state.player_y
        state.velocity_y += gravity * dt
        state.player_x += state.velocity_x * dt
        state.player_y += state.velocity_y * dt

        landed = False
        target_ground = room.ground_y
        for platform in state.platforms:
            if (
                platform.start_x <= state.player_x <= platform.end_x
                and state.velocity_y >= 0
                and previous_y <= platform.top_y + 2.0
                and state.player_y >= platform.top_y
            ):
                target_ground = min(target_ground, platform.top_y)
        if state.player_y >= target_ground:
            state.player_y = target_ground
            state.velocity_y = 0.0
            state.on_ground = True
            landed = True
        if not landed and state.player_y < target_ground - 0.5:
            state.on_ground = False

        if state.on_ground and not self._spike_contact(state.player_x, state.player_y):
            state.last_safe_x = state.player_x
            state.last_safe_y = state.player_y

        if self._apply_environment_contacts():
            return

        if state.player_x < 0.0:
            if room.previous_room is not None:
                self._transition_room(room.previous_room, entry_side="right")
                return
            state.player_x = 0.0
        if state.player_x > room.width:
            if room.next_room is not None and self.room_gate_open(room.room_id):
                self._transition_room(room.next_room, entry_side="left")
                return
            if room.next_room is not None:
                state.gate_feedback = 1.0
                state.gate_locked = True
            state.player_x = room.width

        state.camera_x = max(0.0, min(max(0.0, room.width - 1280.0), state.player_x - 420.0))

        if controls.interact_pressed:
            self._handle_exploration_interact()

        for encounter in state.encounters:
            if encounter.consumed:
                continue
            if encounter.start_x <= state.player_x <= encounter.end_x:
                encounter.consumed = True
                self._start_battle(encounter.enemy_id)
                return

    def _dialogue_card_from_input(self, controls: RuntimeInput) -> str | None:
        if controls.block_pressed or controls.block_held:
            return "defer"
        if controls.interact_pressed or controls.light_attack_pressed:
            return "answer"
        if controls.heavy_attack_pressed or controls.dash_pressed:
            return "appease"
        return None

    def _low_route_from_input(self, controls: RuntimeInput) -> str | None:
        if controls.interact_pressed or controls.light_attack_pressed:
            return "refract"
        if controls.block_pressed or controls.block_held:
            return "resist"
        if controls.heavy_attack_pressed or controls.dash_pressed:
            return "collapse"
        return None

    def _start_up_denouement(self) -> None:
        self.flow.route_to_up_dialogue("auditor_sal")
        if self.flow.dialogue_state is not None:
            self.flow.dialogue_state.target_exchanges = 2
            self.flow.dialogue_state.successful_cards = 0
            self.flow.dialogue_state.safe_card = "answer"
        self.mode = PresentationMode.UP_DIALOGUE
        self.flow.status_text = "Lahgroid falls. Up denouement begins; let the pressure drain by answering cleanly twice."

    def _start_low_epilogue(self) -> None:
        self.flow.route_to_low_puzzle(
            "curgz_gamma",
            target_progress=3,
            return_zone="sunken_sanctum",
            step_sequence=("collapse", "resist", "refract"),
        )
        self.mode = PresentationMode.LOW_PUZZLE
        self.flow.status_text = "Low epilogue active. Collapse, then resist, then refract to settle the aftermath below the boss gate."

    def _update_up_dialogue(self, controls: RuntimeInput) -> None:
        dialogue = self.flow.dialogue_state
        if dialogue is None:
            self.mode = PresentationMode.EXPLORATION
            return
        card = self._dialogue_card_from_input(controls)
        if card is None:
            return

        dialogue.exchange_index += 1
        if card == dialogue.safe_card:
            dialogue.successful_cards += 1
            dialogue.suspicion = max(0.0, dialogue.suspicion - 0.12)
            if dialogue.successful_cards >= dialogue.target_exchanges:
                self._start_low_epilogue()
                return
            dialogue.last_resolution = (
                f"The answer releases the chamber. Up denouement {dialogue.successful_cards}/{dialogue.target_exchanges}; hold the same calm card once more."
            )
            self.flow.status_text = dialogue.last_resolution
            return

        dialogue.suspicion += 0.28
        if dialogue.suspicion >= 0.84:
            self._start_low_epilogue()
            self.flow.status_text = "The answer curdles into judgment. The denouement collapses into the Low epilogue."
            return
        dialogue.last_resolution = "The chamber tightens. Feed it the card that lowers pressure instead of sharpening it."
        self.flow.status_text = dialogue.last_resolution

    def _update_low_puzzle(self, controls: RuntimeInput) -> None:
        route = self._low_route_from_input(controls)
        if route is None:
            return
        self.flow.redirect_curgz_current(route)
        if self.flow.mode == GameplayMode.LAND_NAVIGATION and self.flow.current_zone == "sunken_sanctum":
            self.mode = PresentationMode.EXPLORATION
            self.exploration = self._make_room_state("sunken_sanctum")
            self.flow.status_text = "The Low epilogue settles. Ishtasha returns to the sanctum with the pressure spent."

    def _sludge_viscosity_at(self, player_x: float, player_y: float, on_ground: bool) -> float:
        if not on_ground:
            return 0.0
        viscosity = 0.0
        for patch in self.exploration.sludge_patches:
            if patch.start_x <= player_x <= patch.end_x and abs(player_y - patch.top_y) <= patch.depth + 4.0:
                viscosity = max(viscosity, patch.viscosity)
        return viscosity

    def _spike_contact(self, player_x: float, player_y: float) -> bool:
        for spikes in self.exploration.spikes:
            if spikes.start_x <= player_x <= spikes.end_x and spikes.tip_y - 10.0 <= player_y <= spikes.tip_y + spikes.height:
                return True
        return False

    def _apply_environment_contacts(self) -> bool:
        state = self.exploration
        sludge_viscosity = self._sludge_viscosity_at(state.player_x, state.player_y, state.on_ground)
        if sludge_viscosity > 0.0:
            state.sludge_cling = max(state.sludge_cling, 0.5 + sludge_viscosity)

        if state.hazard_cooldown > 0.0 or not self._spike_contact(state.player_x, state.player_y):
            return False

        state.hazard_cooldown = 0.88
        state.damage_flash = 1.0
        state.hazard_impact_timer = 1.0
        state.hazard_impact_x = state.player_x
        state.hazard_impact_y = state.player_y - 10.0
        self.flow.player.health = max(0.0, self.flow.player.health - 10.0)
        self.flow.player.sync_derived_stats()
        retreat_x = state.last_safe_x - (30.0 * state.facing)
        if abs(retreat_x - state.player_x) < 8.0:
            retreat_x = state.player_x - (42.0 * state.facing)
        state.player_x = max(36.0, min(retreat_x, self.current_room().width - 36.0))
        state.player_y = max(200.0, state.last_safe_y - 22.0)
        state.velocity_x = -228.0 * state.facing
        state.velocity_y = -276.0
        state.on_ground = False
        self.flow.status_text = "Spike contact. Bone shards burst upward and fling Ishtasha off the line."
        if self.flow.player.health <= 0.0:
            self.flow.player.die()
            self.start_game()
            self.flow.status_text = "Ishtasha ruptures on the hazard field and reforms at the opening route."
            return True
        return False

    def _handle_exploration_interact(self) -> None:
        if self._collect_nearby_gourd_segment():
            return
        self._use_gourd_heal()

    def _collect_nearby_gourd_segment(self) -> bool:
        state = self.exploration
        player = self.flow.player
        for segment in state.gourd_segments:
            if segment.consumed:
                continue
            if abs(state.player_x - segment.x) > 44.0 or abs(state.player_y - segment.y) > 70.0:
                continue
            segment.consumed = True
            player.gourd.capacity += segment.capacity_gain
            captured = player.gourd.collect(segment.stored_blood_bonus)
            player.sync_derived_stats()
            self.flow.status_text = (
                f"Recovered {segment.label}. Gourd capacity widens to {player.gourd.capacity:.0f} and captures {captured:.0f} blood for later healing."
            )
            return True
        return False

    def _use_gourd_heal(self) -> bool:
        player = self.flow.player
        if player.life_form != LifeForm.LANDBORNE:
            self.flow.status_text = "The gourd only decants into a fully born landborne vessel."
            return False
        if player.health >= 100.0:
            self.flow.status_text = "Ishtasha is already whole enough; keep the gourd sealed for a worse turn."
            return False
        if player.gourd.stored_blood <= 0.0:
            self.flow.status_text = "The gourd is dry. Recover more amniotic blood before trying to heal."
            return False
        decanted = player.gourd.decant(22.0)
        healed = min(100.0 - player.health, 10.0 + decanted * 0.72)
        player.health += healed
        player.blood.restore(decanted * 0.28)
        player.sync_derived_stats()
        self.flow.status_text = f"Ishtasha drinks from the gourd and restores {healed:.0f} health from the amniotic reserve."
        return True

    def _transition_room(self, room_id: str, entry_side: str) -> None:
        entry_x = 128.0 if entry_side == "left" else max(240.0, ROOMS[room_id].width - 128.0)
        self.flow.enter_land_navigation(room_id)
        self.exploration = self._make_room_state(room_id, entry_x=entry_x)
        self.exploration.room_transition = 1.0
        self.exploration.transition_direction = 1 if entry_side == "left" else -1

    def _start_battle(self, enemy_id: str) -> None:
        self.mode = PresentationMode.BATTLE
        profile = self._battle_cadence_profile(enemy_id)
        if enemy_id == "lahgroid_hierophant":
            self.flow.begin_boss_sequence()
            phase = BattlePhase.INTRO
        else:
            self.flow.begin_eye_lock_encounter(enemy_id)
            phase = BattlePhase.EYECONTACT
        player_anchor = max(0.18, 0.30 - (profile.curve_index - 1) * 0.02)
        enemy_anchor = min(0.84, player_anchor + profile.arena_span)
        proximity = max(0.0, 1.0 - abs(enemy_anchor - player_anchor) / 0.72)
        self.battle = BattlePresentationState(
            enemy_id=enemy_id,
            phase=phase,
            intro_duration=profile.intro_duration,
            window_duration=profile.window_duration,
            resolve_duration=profile.resolve_duration,
            cadence_label=profile.label,
            curve_index=profile.curve_index,
            eyecontact_rate=profile.eyecontact_rate,
            arena_span=profile.arena_span,
            timing_window_half=profile.timing_window_half,
            pressure_speed=profile.pressure_speed,
            player_battle_x=player_anchor,
            enemy_battle_x=enemy_anchor,
            proximity=proximity,
        )
        self.battle.sound_cue_pending = True
        if phase == BattlePhase.EYECONTACT and not self.tutorial_completed:
            self.battle.tutorial_active = True
            self.battle.tutorial_page = 0
            self.battle.tutorial_pages = self._combat_tutorial_pages()
            self.flow.status_text = self.battle.tutorial_pages[0]
        if phase == BattlePhase.INTRO:
            self._sync_battle_prompt()
            self._set_intro_poses(0.0)

    def _combat_tutorial_pages(self) -> tuple[str, ...]:
        return (
            "Tutorial 1/4. Eye contact is the collision race. Let the stare close, then read the incoming lane before the window fully opens.",
            "Tutorial 2/4. The left stick changes depth lanes: up for background, neutral for midground, down for foreground.",
            "Tutorial 3/4. The QTE bar is the timing read. Aim for the bright center while keeping your lane close to the enemy telegraph.",
            "Tutorial 4/4. LB blocks and can parry on perfect timing. RB is a quick light hit, RT is a slower heavy strike, LT dodges out of line.",
        )

    def _battle_cadence_profile(self, enemy_id: str) -> EncounterCadenceProfile:
        return CADENCE_PROFILES.get(enemy_id, CADENCE_PROFILES["scarab_child_acolyte"])

    def _sync_battle_prompt(self) -> None:
        if self.flow.battle_state is None:
            return
        action, lane = self.flow.battle_state.telegraphs[self.flow.battle_state.beat_index % len(self.flow.battle_state.telegraphs)]
        self.battle.prompt_action = action
        self.battle.prompt_lane = lane

    def _player_pose_for_lane(self, lane: str, committed: bool = False) -> str:
        if committed:
            return {
                "foreground": "surge_low",
                "midground": "surge_mid",
                "background": "surge_high",
            }[lane]
        return {
            "foreground": "guard_low",
            "midground": "ready",
            "background": "lift_high",
        }[lane]

    def _enemy_pose_for_telegraph(self, action: str, lane: str) -> str:
        pose_map = {
            "attack": {
                "foreground": "strike_low",
                "midground": "strike_mid",
                "background": "strike_high",
            },
            "parry": {
                "foreground": "feint_low",
                "midground": "feint_mid",
                "background": "feint_high",
            },
            "block": {
                "foreground": "brace_low",
                "midground": "brace_mid",
                "background": "brace_high",
            },
            "dodge": {
                "foreground": "coil_low",
                "midground": "coil_mid",
                "background": "coil_high",
            },
        }
        return pose_map.get(action, pose_map["attack"])[lane]

    def _set_intro_poses(self, strength: float) -> None:
        battle = self.battle
        battle.telegraph_strength = strength
        battle.enemy_pose = self._enemy_pose_for_telegraph(battle.prompt_action, battle.prompt_lane)
        battle.player_pose = self._player_pose_for_lane(battle.lane_bias)
        battle.enemy_commit = strength
        battle.player_commit = max(0.18, abs(battle.player_depth_bias) * 0.45)

    def _set_resolution_poses(self, action: str, lane: str, success: bool) -> None:
        battle = self.battle
        battle.player_pose = self._player_pose_for_lane(lane, committed=True)
        battle.enemy_pose = "break_open" if success else self._enemy_pose_for_telegraph(battle.prompt_action, battle.prompt_lane)
        battle.player_commit = 1.0 if success else 0.62
        battle.enemy_commit = 0.24 if success else 0.88

    def _update_battle_positions(self, dt: float, controls: RuntimeInput) -> None:
        battle = self.battle
        battle.player_battle_x = max(0.14, min(0.86, battle.player_battle_x + controls.move_x * dt * 0.72))
        target_enemy_x = 0.72
        preferred_gap = battle.arena_span
        if battle.prompt_action == "attack":
            target_enemy_x = max(0.48, battle.player_battle_x + preferred_gap * 0.68)
        elif battle.prompt_action == "dodge":
            target_enemy_x = min(0.86, battle.player_battle_x + preferred_gap + 0.08)
        elif battle.prompt_action == "parry":
            target_enemy_x = max(0.52, min(0.8, battle.player_battle_x + preferred_gap * 0.82))
        battle.enemy_battle_x += (target_enemy_x - battle.enemy_battle_x) * min(1.0, dt * 3.4)
        battle.proximity = max(0.0, 1.0 - abs(battle.enemy_battle_x - battle.player_battle_x) / 0.72)

    def _resolve_exchange(self, action: str, timing: float, lane: str) -> tuple[str, str, str]:
        if self.flow.battle_state is None:
            return (action, "fail", "No exchange state was active.")

        enemy_move = self.battle.prompt_action
        proximity = self.battle.proximity
        precision = max(0.0, 1.0 - abs(0.5 - timing) * 2.0)
        lane_score = 1.0 if lane == self.battle.prompt_lane else 0.7
        action_profiles = {
            "attack": {"light_attack": 0.42, "heavy_attack": 0.54, "block": 0.98, "dodge": 0.78},
            "block": {"light_attack": 0.38, "heavy_attack": 0.94, "block": 0.54, "dodge": 0.62},
            "dodge": {"light_attack": 0.88, "heavy_attack": 0.7, "block": 0.34, "dodge": 0.58},
            "parry": {"light_attack": 0.26, "heavy_attack": 0.66, "block": 0.48, "dodge": 0.9},
        }
        base_score = action_profiles.get(enemy_move, action_profiles["attack"]).get(action, 0.32)
        proximity_factor = proximity if action in {"light_attack", "heavy_attack"} else max(0.4, proximity)
        score = base_score * 0.52 + precision * 0.24 + lane_score * 0.12 + proximity_factor * 0.12

        final_action = action
        if action == "block" and enemy_move == "attack" and precision >= 0.9 and proximity >= 0.34:
            final_action = "parry"
            score = max(score, 0.96)

        quality = "fail"
        if score >= 0.82:
            quality = "success"
        elif score >= 0.56:
            quality = "partial"

        action_base_damage = {
            "light_attack": 9.0,
            "heavy_attack": 14.0,
            "block": 4.0,
            "dodge": 3.0,
            "parry": 18.0,
        }
        enemy_damage = 0.0
        player_damage = 0.0
        if quality == "success":
            enemy_damage = action_base_damage[final_action] * (0.72 + precision * 0.58) * (0.6 + proximity_factor * 0.5)
            if final_action in {"block", "parry"}:
                player_damage = 0.0
            elif enemy_move == "block":
                player_damage = 1.0
        elif quality == "partial":
            enemy_damage = action_base_damage[final_action] * (0.34 + precision * 0.24) * max(0.35, proximity_factor)
            player_damage = 3.0 + (1.0 - precision) * 4.0
        else:
            player_damage = 9.0 + (1.0 - precision) * 6.0 + (0.4 - min(0.4, proximity_factor)) * 10.0
            if action in {"light_attack", "heavy_attack"} and enemy_move == "attack" and proximity > 0.54:
                enemy_damage = 2.0

        state = self.flow.battle_state
        state.enemy_health = max(0.0, state.enemy_health - enemy_damage)
        state.player_health = max(0.0, state.player_health - player_damage)
        state.beat_index += 1

        if quality == "success":
            if final_action == "parry":
                status = "Perfect block. Ishtasha turns the contact into a parry and seizes the beat."
            elif final_action == "heavy_attack":
                status = "Heavy read lands cleanly inside the window and crushes through the exchange."
            elif final_action == "dodge":
                status = "The dodge slips outside the line and opens a punished return."
            else:
                status = "The exchange is read cleanly and Ishtasha wins the beat decisively."
        elif quality == "partial":
            status = "The timing is close enough to keep the exchange contested, but both sides connect."
        else:
            status = "The read breaks down in range and timing, and the enemy punishes the approach."

        state.last_resolution = status
        self.flow.status_text = status
        self.battle.exchange_precision = precision

        if state.enemy_health <= 0.0:
            refill = self.flow.player.gourd.collect(14.0 if self.flow.mode != GameplayMode.BOSS_REALTIME else 24.0)
            if self.flow.mode == GameplayMode.BOSS_REALTIME:
                self.boss_defeated = True
                self._start_up_denouement()
                self.flow.status_text = f"Lahgroid falls. The gourd drinks {refill:.0f} blood from the collapse, and the arc rises into Up for denouement."
                self.mode = PresentationMode.UP_DIALOGUE
            else:
                self.flow.enter_land_navigation(self.flow.current_zone)
                self.flow.status_text = f"Encounter cleared. Land navigation resumes, and the gourd absorbs {refill:.0f} blood from the opened enemy."
        elif state.player_health <= 0.0:
            self.flow.player.die()
            self.flow.status_text = "Ishtasha was overwhelmed in the exchange and shed back into ether."

        return (final_action, quality, self.flow.status_text)

    def _update_battle(self, dt: float, controls: RuntimeInput) -> None:
        battle = self.battle
        if battle.tutorial_active:
            if controls.confirm_pressed or controls.interact_pressed:
                next_page = battle.tutorial_page + 1
                if next_page < len(battle.tutorial_pages):
                    battle.tutorial_page = next_page
                    self.flow.status_text = battle.tutorial_pages[next_page]
                else:
                    battle.tutorial_active = False
                    self.tutorial_completed = True
                    self.flow.status_text = "Combat tutorial complete. Keep lane, action, and timing aligned as the QTE opens."
            return
        battle.timer += dt
        battle.camera_shake = max(0.0, battle.camera_shake - dt * 18.0)
        battle.anticipation_flash = max(0.0, battle.anticipation_flash - dt * 3.2)
        battle.lane_bias = self._lane_from_input(controls.move_y)
        battle.player_depth_bias = max(-1.0, min(1.0, controls.move_y))
        battle.enemy_depth_bias = 1.0 if battle.prompt_lane == "foreground" else (-1.0 if battle.prompt_lane == "background" else 0.0)
        self._update_battle_positions(dt, controls)

        if battle.phase == BattlePhase.EYECONTACT:
            if battle.eyecontact_progress < 1.0:
                battle.eyecontact_progress = min(1.0, battle.eyecontact_progress + dt * battle.eyecontact_rate)
                if battle.eyecontact_progress >= 1.0:
                    battle.anticipation_flash = 1.0
            else:
                battle.eyecontact_hold = min(0.16, battle.eyecontact_hold + dt)
            anticipation = min(1.0, battle.eyecontact_hold / 0.16)
            battle.line_of_sight_strength = min(1.0, battle.eyecontact_progress + anticipation * 0.25)
            battle.camera_zoom = 1.0 + battle.eyecontact_progress * 0.18 + anticipation * 0.08
            battle.camera_pan = (0.5 - battle.eyecontact_progress) * 24.0
            battle.player_pose = "stalk"
            battle.enemy_pose = "fixate"
            battle.telegraph_strength = battle.line_of_sight_strength
            battle.player_commit = battle.line_of_sight_strength
            battle.enemy_commit = battle.line_of_sight_strength * 0.92
            if battle.eyecontact_progress >= 1.0 and battle.eyecontact_hold >= 0.16:
                self.flow.resolve_collision(0.53)
                battle.phase = BattlePhase.INTRO
                battle.timer = 0.0
                battle.eyecontact_progress = 1.0
                battle.eyecontact_hold = 0.0
                self._sync_battle_prompt()
                self._set_intro_poses(0.2)
            return

        if battle.phase == BattlePhase.INTRO:
            intro_progress = min(1.0, battle.timer / max(0.01, battle.intro_duration))
            intro_eased = self._ease_in_out_cubic(intro_progress)
            battle.window_progress = 0.0
            battle.time_dilation = 1.0
            battle.telegraph_strength = 0.25 + intro_eased * 0.55
            battle.camera_zoom = 1.05 + intro_eased * 0.15
            battle.camera_pan = battle.enemy_depth_bias * 22.0
            battle.selected_action = "block"
            battle.selected_action_display = "block"
            self._set_intro_poses(intro_eased)
            if battle.timer >= battle.intro_duration:
                battle.phase = BattlePhase.WINDOW
                battle.timer = 0.0
            return

        if battle.phase == BattlePhase.WINDOW:
            raw_timing = min(1.0, battle.timer / max(0.01, battle.window_duration))
            timing = self._ease_in_out_cubic(raw_timing)
            focus = max(0.0, 1.0 - abs(timing - 0.5) * 2.0)
            battle.window_progress = timing
            dilation_gain = 0.24 + battle.curve_index * 0.05
            battle.time_dilation = 1.0 + focus * dilation_gain
            battle.camera_zoom = 1.15 + focus * 0.07
            battle.camera_pan = battle.enemy_depth_bias * 26.0 + (battle.enemy_battle_x - battle.player_battle_x) * 84.0
            battle.telegraph_strength = 0.22 + math.sin(timing * math.pi) * (0.62 + battle.curve_index * 0.08)
            battle.selected_action = "block"
            battle.selected_action_display = "block"
            if controls.light_attack_pressed:
                battle.selected_action = "light_attack"
                battle.selected_action_display = "light_attack"
            elif controls.heavy_attack_pressed:
                battle.selected_action = "heavy_attack"
                battle.selected_action_display = "heavy_attack"
            elif controls.dodge_pressed:
                battle.selected_action = "dodge"
                battle.selected_action_display = "dodge"
            elif controls.block_pressed or controls.block_held:
                battle.selected_action = "block"
                battle.selected_action_display = "block"
            self._set_intro_poses(timing)
            if battle.timer >= battle.window_duration:
                self.perform_action("block", timing=timing)
                return
            if controls.light_attack_pressed:
                self.perform_action("light_attack", timing=timing)
                return
            if controls.heavy_attack_pressed:
                self.perform_action("heavy_attack", timing=timing)
                return
            if controls.dodge_pressed:
                self.perform_action("dodge", timing=timing)
                return
            if controls.block_pressed or (controls.block_held and timing >= 0.52):
                self.perform_action("block", timing=timing)
                return
            return

        battle.camera_zoom = max(1.0, 1.14 - battle.timer * 0.22)
        battle.camera_pan *= 0.8
        battle.window_progress = 1.0
        battle.time_dilation = max(0.88, 1.08 - battle.timer * 0.35)
        battle.telegraph_strength = max(0.0, 1.0 - battle.timer * 2.2)
        if battle.timer >= battle.resolve_duration:
            if self.flow.player.life_form == LifeForm.ETHERIC_CURRENT:
                self._begin_land_birth(self.flow.current_zone)
                return
            if self.flow.mode == GameplayMode.LAND_NAVIGATION or self.flow.battle_state is None:
                self.mode = PresentationMode.EXPLORATION
                self.battle = BattlePresentationState()
                return
            battle.phase = BattlePhase.INTRO
            battle.timer = 0.0
            self._sync_battle_prompt()
            self._set_intro_poses(0.0)

    def perform_action(self, action: str, timing: float) -> None:
        lane = self.battle.lane_bias
        resolved_action, quality, _status = self._resolve_exchange(action, timing, lane)
        self.battle.phase = BattlePhase.RESOLVE
        self.battle.timer = 0.0
        success = quality == "success"
        self.battle.camera_shake = 12.0 if success else 6.0
        self.battle.last_resolution_strength = 1.0 if success else (0.7 if quality == "partial" else 0.4)
        self.battle.resolution_action = resolved_action
        self.battle.resolution_lane = lane
        self.battle.selected_action = action
        self.battle.selected_action_display = resolved_action
        self.battle.resolution_quality = quality
        if timing < 0.26:
            self.battle.resolution_timing_bucket = "early"
        elif timing > 0.68:
            self.battle.resolution_timing_bucket = "late"
        else:
            self.battle.resolution_timing_bucket = "center"
        self.battle.camera_pan = (1.0 if success else -1.0) * 52.0
        self._set_resolution_poses(resolved_action, lane, success)

    def _ease_in_out_cubic(self, value: float) -> float:
        value = max(0.0, min(1.0, value))
        if value < 0.5:
            return 4.0 * value * value * value
        return 1.0 - pow(-2.0 * value + 2.0, 3) / 2.0

    def _lane_from_input(self, move_y: float) -> str:
        if move_y < -0.35:
            return "background"
        if move_y > 0.35:
            return "foreground"
        return "midground"

    def _boss_defeated(self) -> bool:
        return self.boss_defeated
