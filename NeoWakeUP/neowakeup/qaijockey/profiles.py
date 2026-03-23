from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Protocol

import numpy as np

from . import vision as kaiju_vision


@dataclass(frozen=True)
class ActionSpec:
    label: str
    button: str | None
    hold_frames: int
    role: str
    axis: str | None = None
    direction: int = 0


@dataclass
class GameState:
    phase: str = "unknown"
    player_progress: float = 1.0
    opponent_progress: float = 1.0
    player_x: float = 40.0
    opponent_x: float = 120.0
    resource: float = 0.0
    player_visible: bool = True
    opponent_visible: bool = False
    danger: float = 0.0
    opportunity: float = 0.0
    scene_motion: float = 0.0
    player_hit_flash: bool = False
    predicted_attack_hint: bool = False
    win: bool = False
    loss: bool = False
    meta: dict = field(default_factory=dict)

    @property
    def boss_x(self) -> float:
        return self.opponent_x

    @property
    def boss_visible(self) -> bool:
        return self.opponent_visible

    @property
    def boss_hp_frac(self) -> float:
        return self.opponent_progress

    @property
    def player_hp(self) -> int:
        return max(0, int(round(self.player_progress * 6.0)))

    @property
    def nanocells(self) -> int:
        return 1 if self.resource >= 0.5 else 0


class GameProfile(Protocol):
    name: str
    action_specs: list[ActionSpec]
    opponent_id: str
    opponent_archetype: str

    def analyze_frame(self, shades: np.ndarray) -> GameState: ...
    def forced_action(self, state: GameState, frame_n: int) -> str | None: ...
    def evaluate_outcome(self, previous_phase: str, state: GameState) -> str | None: ...
    def format_status(self, state: GameState) -> str: ...


class _BaseProfile:
    name = "base"
    opponent_id = "opponent"
    opponent_archetype = "unknown"
    action_specs: list[ActionSpec] = []

    def forced_action(self, state: GameState, frame_n: int) -> str | None:
        return None

    def evaluate_outcome(self, previous_phase: str, state: GameState) -> str | None:
        if state.win:
            return "win"
        if state.loss:
            return "loss"
        return None

    def format_status(self, state: GameState) -> str:
        return (
            f"phase={state.phase} self={state.player_progress:.2f} opp={state.opponent_progress:.2f} "
            f"danger={state.danger:.2f} oppo={state.opportunity:.2f}"
        )


class KaijuGaidenProfile(_BaseProfile):
    name = "kaijugaiden"
    opponent_id = "kaiju_boss"
    opponent_archetype = "boss-monster"
    action_specs = [
        ActionSpec("ATTACK", "a", 3, "primary"),
        ActionSpec("DODGE", "b", 6, "evade"),
        ActionSpec("LEFT", "left", 4, "move", axis="x", direction=-1),
        ActionSpec("RIGHT", "right", 4, "move", axis="x", direction=1),
        ActionSpec("NANO", "select", 2, "resource"),
        ActionSpec("WAIT", None, 0, "wait"),
    ]

    def __init__(self) -> None:
        self._temporal = kaiju_vision.TemporalContext()

    def analyze_frame(self, shades: np.ndarray) -> GameState:
        self._temporal.update(shades)
        legacy = kaiju_vision.analyze(shades)
        danger = float(
            np.clip(
                0.45 * self._temporal.boss_diff_mean
                + 0.35 * max(0.0, (32.0 - abs(legacy.player_x - legacy.boss_x)) / 32.0)
                + 0.20 * (1.0 if self._temporal.boss_attacking else 0.0),
                0.0,
                1.0,
            )
        )
        opportunity = float(np.clip((1.0 - legacy.boss_hp_frac) * 0.55 + (1.0 - danger) * 0.45, 0.0, 1.0))
        return GameState(
            phase=legacy.phase,
            player_progress=float(np.clip(legacy.player_hp / 6.0, 0.0, 1.0)),
            opponent_progress=float(np.clip(legacy.boss_hp_frac, 0.0, 1.0)),
            player_x=float(legacy.player_x),
            opponent_x=float(legacy.boss_x),
            resource=float(np.clip(legacy.nanocells, 0.0, 1.0)),
            player_visible=True,
            opponent_visible=legacy.boss_visible,
            danger=danger,
            opportunity=opportunity,
            scene_motion=float(np.clip(self._temporal.boss_diff_mean, 0.0, 1.0)),
            player_hit_flash=self._temporal.player_hit_flash,
            predicted_attack_hint=self._temporal.boss_attacking,
            meta={
                "player_hp": legacy.player_hp,
                "boss_hp_frac": legacy.boss_hp_frac,
                "nanocells": legacy.nanocells,
            },
        )

    def forced_action(self, state: GameState, frame_n: int) -> str | None:
        if state.phase == "splash" and frame_n % 45 == 0:
            return "ATTACK"
        if state.phase == "cinematic":
            return "DODGE"
        if state.phase == "title" and frame_n % 60 == 0:
            return "START"
        if state.phase == "gameover" and frame_n % 90 == 0:
            return "START"
        if state.phase == "transition" and frame_n % 30 == 0:
            return "ATTACK"
        return None

    def evaluate_outcome(self, previous_phase: str, state: GameState) -> str | None:
        if previous_phase == "combat" and state.phase in ("title", "transition", "splash"):
            if state.player_progress > 0.0 or state.opponent_progress <= 0.0:
                return "win"
        if previous_phase == "combat" and state.phase == "gameover":
            return "loss"
        return None

    def format_status(self, state: GameState) -> str:
        return (
            f"phase={state.phase} php={state.meta.get('player_hp', state.player_hp)} "
            f"bhp={state.opponent_progress:.2f} nano={state.meta.get('nanocells', state.nanocells)} "
            f"danger={state.danger:.2f}"
        )


class GenericTemporalContext:
    def __init__(self) -> None:
        self._frames: list[np.ndarray] = []
        self.full_diff_mean = 0.0
        self.hit_flash = False

    def update(self, shades: np.ndarray) -> None:
        if self._frames:
            prev = self._frames[-1]
            diff = np.abs(shades.astype(np.int16) - prev.astype(np.int16))
            self.full_diff_mean = float(np.clip(diff.mean() / 3.0, 0.0, 1.0))
            self.hit_flash = self.full_diff_mean > 0.25
        else:
            self.full_diff_mean = 0.0
            self.hit_flash = False
        self._frames.append(shades.copy())
        if len(self._frames) > 6:
            self._frames.pop(0)


class GenericGameProfile(_BaseProfile):
    name = "generic"
    opponent_id = "generic_target"
    opponent_archetype = "unknown-game-entity"
    action_specs = [
        ActionSpec("PRESS_A", "a", 3, "primary"),
        ActionSpec("PRESS_B", "b", 3, "secondary"),
        ActionSpec("LEFT", "left", 3, "move", axis="x", direction=-1),
        ActionSpec("RIGHT", "right", 3, "move", axis="x", direction=1),
        ActionSpec("UP", "up", 3, "move", axis="y", direction=-1),
        ActionSpec("DOWN", "down", 3, "move", axis="y", direction=1),
        ActionSpec("START", "start", 2, "menu_confirm"),
        ActionSpec("SELECT", "select", 2, "resource"),
        ActionSpec("WAIT", None, 0, "wait"),
    ]

    def __init__(self) -> None:
        self._temporal = GenericTemporalContext()

    def _centroid(self, shades: np.ndarray, x0: int, x1: int) -> float:
        region = shades[:, x0:x1]
        mask = region >= 2
        if mask.sum() < 8:
            return float((x0 + x1) / 2)
        _ys, xs = np.where(mask)
        return float(xs.mean() + x0)

    def analyze_frame(self, shades: np.ndarray) -> GameState:
        self._temporal.update(shades)
        height, width = shades.shape
        white_frac = float((shades == 0).mean())
        dark_frac = float((shades >= 2).mean())
        if white_frac > 0.80 and self._temporal.full_diff_mean < 0.03:
            phase = "splash"
        elif self._temporal.full_diff_mean < 0.015:
            phase = "menu"
        else:
            phase = "active"

        player_x = self._centroid(shades, 0, width // 2)
        opponent_x = self._centroid(shades, width // 2, width)
        proximity = float(np.clip((48.0 - abs(player_x - opponent_x)) / 48.0, 0.0, 1.0))
        danger = float(np.clip(0.65 * self._temporal.full_diff_mean + 0.35 * proximity, 0.0, 1.0))
        opportunity = float(np.clip(1.0 - danger * 0.7, 0.0, 1.0))
        opponent_visible = dark_frac > 0.08
        player_visible = dark_frac > 0.02
        return GameState(
            phase=phase,
            player_progress=1.0,
            opponent_progress=1.0,
            player_x=player_x,
            opponent_x=opponent_x,
            resource=0.0,
            player_visible=player_visible,
            opponent_visible=opponent_visible,
            danger=danger,
            opportunity=opportunity,
            scene_motion=self._temporal.full_diff_mean,
            player_hit_flash=self._temporal.hit_flash,
            predicted_attack_hint=danger > 0.6,
            meta={
                "white_frac": round(white_frac, 4),
                "dark_frac": round(dark_frac, 4),
            },
        )

    def forced_action(self, state: GameState, frame_n: int) -> str | None:
        if state.phase in ("splash", "menu"):
            if frame_n % 90 == 0:
                return "START"
            if frame_n % 45 == 0:
                return "PRESS_A"
        return None

    def format_status(self, state: GameState) -> str:
        return (
            f"phase={state.phase} motion={state.scene_motion:.2f} danger={state.danger:.2f} "
            f"opp_visible={int(state.opponent_visible)} pos=({state.player_x:.0f},{state.opponent_x:.0f})"
        )


BUILTIN_PROFILES = {
    "kaijugaiden": KaijuGaidenProfile,
    "generic": GenericGameProfile,
}


def load_profile(spec: str | None) -> GameProfile:
    key = (spec or "kaijugaiden").strip()
    builtin = BUILTIN_PROFILES.get(key.lower())
    if builtin is not None:
        return builtin()

    module = import_module(key)
    profile = getattr(module, "PROFILE", None)
    if profile is not None:
        return profile

    builder = getattr(module, "build_profile", None)
    if callable(builder):
        return builder()

    profile_cls = getattr(module, "Profile", None)
    if profile_cls is not None:
        return profile_cls()

    raise RuntimeError(
        f"Could not load game profile '{spec}'. Use a built-in profile or expose PROFILE, build_profile(), or Profile in the module."
    )