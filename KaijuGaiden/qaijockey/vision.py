"""
qaijockey/vision.py — Framebuffer analysis for QAIJockey.

Converts the raw PyBoy framebuffer (PIL RGBA 160×144) into a GameState
by examining specific pixel regions that directly map to kaijugaiden.c's
HUD and sprite layout.

Screen layout from kaijugaiden.c tile constants (each tile = 8×8 px):
  HUD row 0   (y=0..7):
    cols 0-5   → Player HP segments (TILE_HP_SEG or TILE_BLANK)
    cols 10-11 → NanoCell digit
    cols 14-19 → Boss HP segments
  Arena       (y=8..127): background + sprites
  Ground row  (y=128..143): TILE_GROUND / TILE_CLIFF
"""

import numpy as np
from dataclasses import dataclass, field
from collections import deque
from typing import Deque

# ── Pixel coordinates of HUD regions ─────────────────────────────────────────
HUD_Y            = (0,   8)    # top tile row
PLAYER_HP_X      = (0,   48)   # tile cols 0-5  × 8px
NANO_X           = (80,  96)   # tile cols 10-11 × 8px
BOSS_HP_X        = (112, 160)  # tile cols 14-19 × 8px

# Arena zones for sprite detection
ARENA_Y          = (8,   128)
PLAYER_ZONE_X    = (0,   80)   # Rei is left side
BOSS_ZONE_X      = (80,  160)  # Boss is right side

# Number of tiles per HP region
PLAYER_HP_TILES  = 6
BOSS_HP_TILES    = 6

# ── Shade quantisation thresholds (luminance, 0-255) ─────────────────────────
# PyBoy uses its own internal DMG palette; we quantise to 4 abstract shades
# 0=lightest (blank/white)  3=darkest (solid black)
SHADE_THRESH = [200, 130, 60]   # luminance cut-offs for shades 0/1/2/3


def pil_to_shades(pil_rgba) -> np.ndarray:
    """Convert PyBoy screen PIL RGBA image → uint8 [0..3] shade array (H×W)."""
    arr = np.array(pil_rgba, dtype=np.uint8)
    # Weighted luminance: 0.299R + 0.587G + 0.114B
    lum = (arr[:, :, 0].astype(np.uint16) * 299 +
           arr[:, :, 1].astype(np.uint16) * 587 +
           arr[:, :, 2].astype(np.uint16) * 114) // 1000
    lum = lum.astype(np.uint8)
    shades = np.full(lum.shape, 3, dtype=np.uint8)
    shades[lum > SHADE_THRESH[2]] = 2
    shades[lum > SHADE_THRESH[1]] = 1
    shades[lum > SHADE_THRESH[0]] = 0
    return shades


def _count_filled_segments(shades: np.ndarray, x0: int, x1: int,
                           y0: int, y1: int, n_tiles: int,
                           dark_mean_thresh: float = 0.25) -> int:
    """
    Count how many 8-px-wide tile columns in the HUD region contain
    predominantly non-zero (filled) shades.
    Returns integer count 0..n_tiles.
    """
    region = shades[y0:y1, x0:x1]
    filled = 0
    tile_w = (x1 - x0) // n_tiles
    for i in range(n_tiles):
        tile = region[:, i * tile_w: (i + 1) * tile_w]
        if (tile > 0).mean() > dark_mean_thresh:
            filled += 1
    return filled


def _sprite_centroid_x(shades: np.ndarray,
                       x0: int, x1: int,
                       y0: int, y1: int,
                       shade_thresh: int = 2,
                       default_x: int = None) -> int:
    """Find the horizontal centroid of dark pixels (sprite body) in a region."""
    region = shades[y0:y1, x0:x1]
    mask = region >= shade_thresh
    if mask.sum() < 8:
        return default_x if default_x is not None else (x0 + x1) // 2
    _, xs = np.where(mask)
    return int(xs.mean()) + x0


# ── Phase detection ───────────────────────────────────────────────────────────

def _detect_phase(shades: np.ndarray) -> str:
    """
    Heuristic phase detection from pixel distribution.

    kaijugaiden phases:
      splash     — drIpTECH logo: mostly blank (shade 0) with small logo centre
      cinematic  — large sprite tiles; high dark coverage, big FX
      title      — title logo + menu text; medium coverage, mostly centered
      combat     — HUD content + arena sprites; high variance in arena
      gameover   — mostly dark background, "GAME OVER" text tiles
      transition — intermediate / loading state (treat as splash/title)
    """
    total = shades.size
    white_frac = (shades == 0).sum() / total
    dark_frac  = (shades >= 2).sum() / total

    # HUD row: in combat phase this row has HP-segment tiles (non-zero shades)
    hud    = shades[HUD_Y[0]:HUD_Y[1], 0:160]
    hud_active = (hud > 0).mean()

    # Arena: combat has high spatial variance from sprites
    arena  = shades[ARENA_Y[0]:ARENA_Y[1], 0:160]
    arena_var = float(arena.var())

    # ---- Classify ----
    if dark_frac > 0.60:
        # Could be gameover or cinematic
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


# ── Public GameState ──────────────────────────────────────────────────────────

@dataclass
class GameState:
    phase:        str   = "unknown"
    player_hp:    int   = 6       # 0..6
    boss_hp_frac: float = 1.0     # 0.0..1.0 (fraction of current phase HP)
    boss_visible: bool  = False
    player_x:     int   = 40      # pixel x of Rei centroid
    boss_x:       int   = 120     # pixel x of boss centroid
    nanocells:    int   = 0       # 0..9 (1 if digit tile is non-blank)


def analyze(shades: np.ndarray) -> GameState:
    """
    Full frame analysis: quantised shade array (160×144) → GameState.
    Called every frame from QAIJockey.tick().
    """
    gs = GameState()
    gs.phase = _detect_phase(shades)

    if gs.phase == "combat":
        gs.player_hp = _count_filled_segments(
            shades, *PLAYER_HP_X, *HUD_Y, PLAYER_HP_TILES)

        boss_filled = _count_filled_segments(
            shades, *BOSS_HP_X, *HUD_Y, BOSS_HP_TILES)
        gs.boss_hp_frac = boss_filled / BOSS_HP_TILES
        gs.boss_visible = boss_filled > 0

        gs.player_x = _sprite_centroid_x(
            shades, *PLAYER_ZONE_X, *ARENA_Y, default_x=40)
        gs.boss_x = _sprite_centroid_x(
            shades, *BOSS_ZONE_X,   *ARENA_Y, default_x=120)

        # NanoCell: digit tile at cols 10-11 is non-blank when count > 0
        nano_tile = shades[HUD_Y[0]:HUD_Y[1], NANO_X[0]:NANO_X[1]]
        gs.nanocells = 1 if (nano_tile > 0).mean() > 0.12 else 0

    return gs


# ── Temporal context ──────────────────────────────────────────────────────────

class TemporalContext:
    """
    Maintains a rolling window of recent shade frames and computes
    per-region temporal differentials to detect boss attacks, player
    movement, and hit-flash events.

    This is the 'temporal probability analysis' core of QAIJockey:
    each frame-diff snapshot gives evidence about what the game 'just did',
    which updates the action probability weights in jockey.py.
    """

    HISTORY = 8   # frames of shade history kept

    def __init__(self):
        self._frames:        Deque[np.ndarray] = deque(maxlen=self.HISTORY)
        self._boss_diffs:    Deque[float]      = deque(maxlen=self.HISTORY)
        self._player_diffs:  Deque[float]      = deque(maxlen=self.HISTORY)
        self._full_diffs:    Deque[float]      = deque(maxlen=self.HISTORY)

    def update(self, shades: np.ndarray) -> None:
        """Push a new frame; compute diffs against previous."""
        if self._frames:
            prev = self._frames[-1]
            diff = np.abs(shades.astype(np.int16) - prev.astype(np.int16))

            # Boss zone diff (right half of arena)
            bd = diff[ARENA_Y[0]:ARENA_Y[1], BOSS_ZONE_X[0]:BOSS_ZONE_X[1]].mean()
            self._boss_diffs.append(float(bd))

            # Player zone diff (left half)
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
        """True when sustained motion detected in boss zone (>=3 recent frames)."""
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
        """Sudden full-screen brightness spike = hit flash."""
        if len(self._full_diffs) < 2:
            return False
        recent = list(self._full_diffs)[-2:]
        return max(recent) > 0.45

    @property
    def scene_static(self) -> bool:
        """True in non-interactive phases (very little screen change)."""
        if not self._full_diffs:
            return True
        return float(np.mean(self._full_diffs)) < 0.02
