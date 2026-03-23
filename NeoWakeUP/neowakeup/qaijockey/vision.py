"""
qaijockey/vision.py — Framebuffer analysis for QAIJockey.

Converts the raw PyBoy framebuffer (PIL RGBA 160×144) into a GameState
by examining specific pixel regions that directly map to kaijugaiden.c's
HUD and sprite layout.
"""

import numpy as np
from dataclasses import dataclass
from collections import deque
from typing import Deque

HUD_Y = (0, 8)
PLAYER_HP_X = (0, 48)
NANO_X = (80, 96)
BOSS_HP_X = (112, 160)
ARENA_Y = (8, 128)
PLAYER_ZONE_X = (0, 80)
BOSS_ZONE_X = (80, 160)
PLAYER_HP_TILES = 6
BOSS_HP_TILES = 6
SHADE_THRESH = [200, 130, 60]


def pil_to_shades(pil_rgba) -> np.ndarray:
    arr = np.array(pil_rgba, dtype=np.uint8)
    lum = (
        arr[:, :, 0].astype(np.uint16) * 299
        + arr[:, :, 1].astype(np.uint16) * 587
        + arr[:, :, 2].astype(np.uint16) * 114
    ) // 1000
    lum = lum.astype(np.uint8)
    shades = np.full(lum.shape, 3, dtype=np.uint8)
    shades[lum > SHADE_THRESH[2]] = 2
    shades[lum > SHADE_THRESH[1]] = 1
    shades[lum > SHADE_THRESH[0]] = 0
    return shades


def _count_filled_segments(shades: np.ndarray, x0: int, x1: int,
                           y0: int, y1: int, n_tiles: int,
                           dark_mean_thresh: float = 0.25) -> int:
    region = shades[y0:y1, x0:x1]
    filled = 0
    tile_w = (x1 - x0) // n_tiles
    for i in range(n_tiles):
        tile = region[:, i * tile_w:(i + 1) * tile_w]
        if (tile > 0).mean() > dark_mean_thresh:
            filled += 1
    return filled


def _sprite_centroid_x(shades: np.ndarray,
                       x0: int, x1: int,
                       y0: int, y1: int,
                       shade_thresh: int = 2,
                       default_x: int = None) -> int:
    region = shades[y0:y1, x0:x1]
    mask = region >= shade_thresh
    if mask.sum() < 8:
        return default_x if default_x is not None else (x0 + x1) // 2
    _, xs = np.where(mask)
    return int(xs.mean()) + x0


def _detect_phase(shades: np.ndarray) -> str:
    total = shades.size
    white_frac = (shades == 0).sum() / total
    dark_frac = (shades >= 2).sum() / total
    hud = shades[HUD_Y[0]:HUD_Y[1], 0:160]
    hud_active = (hud > 0).mean()
    arena = shades[ARENA_Y[0]:ARENA_Y[1], 0:160]
    arena_var = float(arena.var())

    if dark_frac > 0.60:
        if arena_var > 0.8:
            return "cinematic"
        return "gameover"
    if white_frac > 0.80 and arena_var < 0.15:
        return "splash"
    if hud_active > 0.08 and arena_var > 0.30:
        return "combat"
    if white_frac > 0.50 and arena_var < 0.50:
        return "title"
    return "transition"


@dataclass
class GameState:
    phase: str = "unknown"
    player_hp: int = 6
    boss_hp_frac: float = 1.0
    boss_visible: bool = False
    player_x: int = 40
    boss_x: int = 120
    nanocells: int = 0


def analyze(shades: np.ndarray) -> GameState:
    gs = GameState()
    gs.phase = _detect_phase(shades)

    if gs.phase == "combat":
        gs.player_hp = _count_filled_segments(shades, *PLAYER_HP_X, *HUD_Y, PLAYER_HP_TILES)
        boss_filled = _count_filled_segments(shades, *BOSS_HP_X, *HUD_Y, BOSS_HP_TILES)
        gs.boss_hp_frac = boss_filled / BOSS_HP_TILES
        gs.boss_visible = boss_filled > 0
        gs.player_x = _sprite_centroid_x(shades, *PLAYER_ZONE_X, *ARENA_Y, default_x=40)
        gs.boss_x = _sprite_centroid_x(shades, *BOSS_ZONE_X, *ARENA_Y, default_x=120)
        nano_tile = shades[HUD_Y[0]:HUD_Y[1], NANO_X[0]:NANO_X[1]]
        gs.nanocells = 1 if (nano_tile > 0).mean() > 0.12 else 0

    return gs


class TemporalContext:
    HISTORY = 8

    def __init__(self):
        self._frames: Deque[np.ndarray] = deque(maxlen=self.HISTORY)
        self._boss_diffs: Deque[float] = deque(maxlen=self.HISTORY)
        self._player_diffs: Deque[float] = deque(maxlen=self.HISTORY)
        self._full_diffs: Deque[float] = deque(maxlen=self.HISTORY)

    def update(self, shades: np.ndarray) -> None:
        if self._frames:
            prev = self._frames[-1]
            diff = np.abs(shades.astype(np.int16) - prev.astype(np.int16))
            bd = diff[ARENA_Y[0]:ARENA_Y[1], BOSS_ZONE_X[0]:BOSS_ZONE_X[1]].mean()
            self._boss_diffs.append(float(bd))
            pd = diff[ARENA_Y[0]:ARENA_Y[1], PLAYER_ZONE_X[0]:PLAYER_ZONE_X[1]].mean()
            self._player_diffs.append(float(pd))
            self._full_diffs.append(float(diff.mean()))
        else:
            self._boss_diffs.append(0.0)
            self._player_diffs.append(0.0)
            self._full_diffs.append(0.0)
        self._frames.append(shades.copy())

    @property
    def boss_attacking(self) -> bool:
        if len(self._boss_diffs) < 3:
            return False
        return float(np.mean(list(self._boss_diffs)[-3:])) > 0.18

    @property
    def boss_diff_mean(self) -> float:
        if not self._boss_diffs:
            return 0.0
        return float(np.mean(self._boss_diffs))

    @property
    def player_hit_flash(self) -> bool:
        if len(self._full_diffs) < 2:
            return False
        recent = list(self._full_diffs)[-2:]
        return max(recent) > 0.45

    @property
    def scene_static(self) -> bool:
        if not self._full_diffs:
            return True
        return float(np.mean(self._full_diffs)) < 0.02