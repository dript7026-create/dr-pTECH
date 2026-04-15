"""Generate production-quality pixel-art assets for aridfeihth vertical slice.

Desert wasteland-pirate metroidvania aesthetic:
  - Vast dunes with reflective sand grain detail
  - Jagged rocky arches and spires on horizon
  - 3-point perspective depth cues
  - Characters: 5-head proportions, segmented limbs, anticipation/follow-through
  - Pets: half-human chibi with large heads
  - Audio: Hijaz-scale Arabic-Mexican fusion (violin, brass, percussion)

Palette (expanded):
  Sky deep:      #0e1a30   Sky mid:       #1a2744   Sky bright:    #2a4068
  Horizon haze:  #5c6e8a   Sand light:    #e8d4a8   Sand mid:      #d4c098
  Sand dark:     #b09868   Sand shadow:   #8a7450   Brass:         #c6a84b
  Highlight:     #e8c25c   Rust:          #8b3a1e   Dark rust:     #5c2412
  Bone:          #e2d5b0   Teal:          #3a7a7a   Deep teal:     #1e4a4a
  Shadow:        #0f1520   Rock mid:      #4a3828   Rock light:    #6a5844
  Specular:      #fff4d0   Magma:         #d44a18
"""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

WORKSPACE = Path(__file__).resolve().parents[2]
OUT_ROOT = WORKSPACE / "aridfeihth" / "production_raw"

random.seed(42)
np.random.seed(42)

# ── Expanded palette ──────────────────────────────────────────────

SKY_DEEP    = (0x0E, 0x1A, 0x30)
SKY_MID     = (0x1A, 0x27, 0x44)
SKY_BRIGHT  = (0x2A, 0x40, 0x68)
HORIZON     = (0x5C, 0x6E, 0x8A)
SAND_LIGHT  = (0xE8, 0xD4, 0xA8)
SAND_MID    = (0xD4, 0xC0, 0x98)
SAND_DARK   = (0xB0, 0x98, 0x68)
SAND_SHADOW = (0x8A, 0x74, 0x50)
BRASS       = (0xC6, 0xA8, 0x4B)
HIGHLIGHT   = (0xE8, 0xC2, 0x5C)
RUST        = (0x8B, 0x3A, 0x1E)
DARK_RUST   = (0x5C, 0x24, 0x12)
BONE        = (0xE2, 0xD5, 0xB0)
TEAL        = (0x3A, 0x7A, 0x7A)
DEEP_TEAL   = (0x1E, 0x4A, 0x4A)
SHADOW      = (0x0F, 0x15, 0x20)
ROCK_MID    = (0x4A, 0x38, 0x28)
ROCK_LIGHT  = (0x6A, 0x58, 0x44)
SPECULAR    = (0xFF, 0xF4, 0xD0)
MAGMA       = (0xD4, 0x4A, 0x18)
SKIN_MID    = (0xC8, 0x9E, 0x74)
SKIN_SHADOW = (0xA0, 0x78, 0x58)
SKIN_LIGHT  = (0xDE, 0xBE, 0x98)
CLOTH_TEAL  = (0x2E, 0x66, 0x66)
CLOTH_DARK  = (0x1A, 0x44, 0x44)
CAPE_RUST   = (0x7A, 0x30, 0x18)
CAPE_DARK   = (0x50, 0x1E, 0x0E)
BOOT_BROWN  = (0x4A, 0x2E, 0x1A)
BELT_BRASS  = (0xAA, 0x90, 0x3E)
WEAPON_BONE = (0xD8, 0xCC, 0xAA)


# ── Utility ───────────────────────────────────────────────────────

def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _perlin_1d(n: int, octaves: int = 4, seed: int = 0) -> np.ndarray:
    """Simple 1D fractional Brownian motion."""
    rng = np.random.RandomState(seed)
    result = np.zeros(n, dtype=np.float64)
    for octave in range(octaves):
        freq = 2 ** octave
        amp = 1.0 / (1.5 ** octave)
        phase = rng.uniform(0, 2 * np.pi)
        x = np.linspace(0, freq * np.pi * 2, n) + phase
        result += np.sin(x + rng.uniform(-1, 1, n) * 0.6) * amp
    return result


def _sand_noise(w: int, h: int, y_start: int, base: tuple, light: tuple,
                dark: tuple, specular: tuple, density: float = 0.15) -> np.ndarray:
    """Generate sand texture array with grain-level detail and specular highlights."""
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(y_start, h):
        row_t = (y - y_start) / max(1, h - y_start)
        for x in range(w):
            r = random.random()
            if r < 0.005:
                c = specular  # reflective grain
            elif r < density * 0.3:
                c = light
            elif r < density:
                c = dark
            else:
                c = _lerp_color(base, dark, row_t * 0.4 + random.uniform(-0.08, 0.08))
            arr[y, x] = (*c, 255)
    return arr


def _jagged_spire(draw: ImageDraw.ImageDraw, base_x: int, base_y: int,
                  height: int, width: int, color: tuple, highlight: tuple,
                  facing: int = 1) -> None:
    """Draw a jagged rocky spire/arch silhouette."""
    pts = [(base_x - width // 2, base_y)]
    segments = random.randint(6, 12)
    for i in range(1, segments):
        t = i / segments
        # Taper as we go up, with random jaggedness
        w = width * (1.0 - t * 0.7) * 0.5
        jag = random.uniform(-width * 0.15, width * 0.15) * facing
        y = base_y - int(height * t)
        pts.append((base_x + int(jag) - int(w * 0.3), y))
    # Pointy top
    pts.append((base_x + random.randint(-3, 3), base_y - height))
    # Return path (other side)
    for i in range(segments - 1, 0, -1):
        t = i / segments
        w = width * (1.0 - t * 0.7) * 0.5
        jag = random.uniform(-width * 0.1, width * 0.1) * facing
        y = base_y - int(height * t)
        pts.append((base_x + int(jag) + int(w * 0.5), y))
    pts.append((base_x + width // 2, base_y))
    draw.polygon(pts, fill=color)
    # Light edge on the facing side
    for i in range(len(pts) // 2):
        if i + 1 < len(pts):
            draw.line([pts[i], pts[i + 1]], fill=highlight, width=1)


def _draw_dune_contour(draw: ImageDraw.ImageDraw, w: int, y_base: int,
                       amplitude: float, wavelength: float, color_near: tuple,
                       color_far: tuple, sand_specular: tuple, thickness: int = 1,
                       seed: int = 0) -> list[int]:
    """Draw a sine-composite dune contour line with fill below. Returns heights."""
    noise = _perlin_1d(w, octaves=3, seed=seed)
    heights = []
    for x in range(w):
        y = y_base + int(amplitude * math.sin(x / wavelength * math.pi * 2 + noise[x] * 1.2))
        y += int(noise[x] * amplitude * 0.3)
        heights.append(y)
    # Fill below the contour
    for x in range(w):
        yt = heights[x]
        t = x / w
        col = _lerp_color(color_near, color_far, t * 0.6 + 0.2)
        draw.line([(x, yt), (x, yt + thickness + 60)], fill=col)
        # Specular grain on crest
        if random.random() < 0.03:
            draw.point((x, yt), fill=sand_specular)
        # Shadow on lee side
        if x > 0 and heights[x] > heights[x - 1]:
            shadow = _lerp_color(col, SHADOW, 0.3)
            draw.line([(x, yt), (x, yt + 2)], fill=shadow)
    return heights


# ── Environment backdrops (640×360) ──────────────────────────────

def gen_latchspire_refuge(w: int = 640, h: int = 360) -> Image.Image:
    """Safe room: tower refuge amid sprawling dunes under vast cobalt sky."""
    img = Image.new("RGBA", (w, h), SKY_DEEP)
    draw = ImageDraw.Draw(img)

    # Sky gradient (deep -> bright -> horizon haze)
    horizon_y = int(h * 0.44)
    for y in range(horizon_y):
        t = y / horizon_y
        if t < 0.5:
            c = _lerp_color(SKY_DEEP, SKY_MID, t * 2)
        else:
            c = _lerp_color(SKY_MID, SKY_BRIGHT, (t - 0.5) * 2)
        draw.line([(0, y), (w - 1, y)], fill=c)

    # Horizon haze band
    for y in range(horizon_y - 8, horizon_y + 12):
        t = (y - (horizon_y - 8)) / 20
        c = _lerp_color(SKY_BRIGHT, HORIZON, t)
        draw.line([(0, y), (w - 1, y)], fill=(*c, 180))

    # Far spires on horizon (atmospheric blue tint)
    far_color = _lerp_color(ROCK_MID, HORIZON, 0.6)
    far_highlight = _lerp_color(ROCK_LIGHT, HORIZON, 0.5)
    for bx in [60, 140, 380, 480, 560]:
        _jagged_spire(draw, bx, horizon_y + 2, random.randint(30, 65), random.randint(12, 22),
                      far_color, far_highlight, facing=random.choice([-1, 1]))

    # Mid-ground dunes
    _draw_dune_contour(draw, w, horizon_y + 14, 12, 160, SAND_MID, SAND_DARK, SPECULAR, 40, seed=10)
    _draw_dune_contour(draw, w, horizon_y + 40, 18, 120, SAND_MID, SAND_SHADOW, SPECULAR, 50, seed=20)

    # Foreground large dune
    _draw_dune_contour(draw, w, int(h * 0.65), 25, 200, SAND_LIGHT, SAND_MID, SPECULAR, 80, seed=30)

    # Sand grain detail layer (foreground)
    for _ in range(3000):
        x = random.randint(0, w - 1)
        y = random.randint(int(h * 0.55), h - 1)
        r = random.random()
        if r < 0.02:
            draw.point((x, y), fill=SPECULAR)
        elif r < 0.15:
            draw.point((x, y), fill=SAND_LIGHT)
        elif r < 0.3:
            draw.point((x, y), fill=SAND_SHADOW)

    # Tower structure (3-point perspective: slightly converging verticals)
    tx = w // 2
    tower_base = int(h * 0.62)
    tower_top = int(h * 0.18)
    tw_base = 60
    tw_top = 48  # narrower at top (3-point convergence)
    # Main body
    pts = [(tx - tw_base // 2, tower_base), (tx + tw_base // 2, tower_base),
           (tx + tw_top // 2, tower_top), (tx - tw_top // 2, tower_top)]
    draw.polygon(pts, fill=RUST)
    # Dark side (right)
    pts_dark = [(tx + 4, tower_base), (tx + tw_base // 2, tower_base),
                (tx + tw_top // 2, tower_top), (tx + 2, tower_top)]
    draw.polygon(pts_dark, fill=DARK_RUST)
    # Stone lines
    for sy in range(tower_top + 8, tower_base, 16):
        w_at = tw_base - int((tw_base - tw_top) * (tower_base - sy) / (tower_base - tower_top))
        draw.line([(tx - w_at // 2, sy), (tx + w_at // 2, sy)], fill=SAND_SHADOW)
    # Windows (arched)
    for wy in range(tower_top + 30, tower_base - 30, 40):
        for wxo in [-12, 12]:
            draw.rectangle([tx + wxo - 5, wy - 8, tx + wxo + 5, wy + 6], fill=SHADOW)
            draw.arc([tx + wxo - 5, wy - 12, tx + wxo + 5, wy - 4], 180, 0, fill=RUST)
            draw.rectangle([tx + wxo - 3, wy - 4, tx + wxo + 3, wy + 4], fill=HIGHLIGHT)
    # Spire top
    draw.polygon([(tx - tw_top // 2, tower_top), (tx, tower_top - 40),
                  (tx + tw_top // 2, tower_top)], fill=BRASS)
    draw.line([(tx, tower_top - 40), (tx, tower_top - 55)], fill=DARK_RUST, width=2)
    # Flag
    flag_pts = [(tx + 2, tower_top - 55), (tx + 22, tower_top - 50), (tx + 2, tower_top - 44)]
    draw.polygon(flag_pts, fill=RUST)
    draw.polygon(flag_pts, outline=DARK_RUST)

    # 3-point perspective ground lines
    vanish_x, vanish_y = w // 2, int(h * 0.42)
    for angle in range(-40, 41, 10):
        end_x = vanish_x + int(math.tan(math.radians(angle)) * (h - vanish_y))
        draw.line([(vanish_x, vanish_y), (end_x, h)], fill=(*SAND_SHADOW, 30), width=1)

    return img


def gen_choir_stair(w: int = 640, h: int = 360) -> Image.Image:
    """Encounter room: crumbling staircase ascending through desert ruins."""
    img = Image.new("RGBA", (w, h), SKY_DEEP)
    draw = ImageDraw.Draw(img)

    horizon_y = int(h * 0.38)
    # Sky
    for y in range(horizon_y + 10):
        t = y / (horizon_y + 10)
        c = _lerp_color(SKY_DEEP, SKY_BRIGHT, t)
        draw.line([(0, y), (w - 1, y)], fill=c)

    # Distant spires
    for bx in [30, 100, 200, 420, 530, 590]:
        ht = random.randint(20, 50)
        c = _lerp_color(ROCK_MID, HORIZON, 0.55)
        _jagged_spire(draw, bx, horizon_y, ht, random.randint(8, 18), c,
                      _lerp_color(ROCK_LIGHT, HORIZON, 0.5))

    # Dune background
    _draw_dune_contour(draw, w, horizon_y + 4, 10, 180, SAND_DARK, SAND_SHADOW, SPECULAR, 30, seed=40)

    # Ruin pillars (with proper perspective — taller ones further apart)
    for i, px in enumerate([80, 180, 300, 420, 540]):
        pillar_h = 100 + i * 8
        pillar_w = 18 - i
        base_y = int(h * 0.72) - i * 10
        # Pillar body
        draw.rectangle([px, base_y - pillar_h, px + pillar_w, base_y], fill=ROCK_MID)
        draw.rectangle([px + pillar_w // 2, base_y - pillar_h, px + pillar_w, base_y],
                       fill=_lerp_color(ROCK_MID, SHADOW, 0.3))
        # Capital
        draw.rectangle([px - 4, base_y - pillar_h - 6, px + pillar_w + 4, base_y - pillar_h],
                       fill=ROCK_LIGHT)
        # Cracks
        for _ in range(3):
            cy = random.randint(base_y - pillar_h + 10, base_y - 10)
            cx = random.randint(px + 2, px + pillar_w - 2)
            draw.line([(cx, cy), (cx + random.randint(-4, 4), cy + random.randint(5, 15))],
                      fill=SHADOW, width=1)

    # Staircase (proper 3-point perspective convergence)
    stair_count = 12
    for i in range(stair_count):
        sx = 40 + i * 48
        sy = int(h * 0.78) - i * 14
        sw = 56 - i * 2
        sh = 10
        # Top face
        draw.rectangle([sx, sy, sx + sw, sy + sh], fill=SAND_MID)
        draw.rectangle([sx, sy, sx + sw, sy + 2], fill=SAND_LIGHT)
        # Front face
        draw.rectangle([sx, sy + sh, sx + sw, sy + sh + 6], fill=SAND_DARK)
        # Shadow under
        draw.rectangle([sx + 2, sy + sh + 6, sx + sw - 2, sy + sh + 8],
                       fill=(*SAND_SHADOW, 120))

    # Floor
    _draw_dune_contour(draw, w, int(h * 0.8), 6, 300, SAND_MID, SAND_DARK, SPECULAR, 80, seed=50)

    # Sand grain foreground detail
    for _ in range(2000):
        x = random.randint(0, w - 1)
        y = random.randint(int(h * 0.7), h - 1)
        r = random.random()
        if r < 0.02:
            draw.point((x, y), fill=SPECULAR)
        elif r < 0.12:
            draw.point((x, y), fill=SAND_LIGHT)

    # Scattered bone debris
    for _ in range(15):
        bx = random.randint(30, w - 30)
        by = random.randint(int(h * 0.78), h - 10)
        ln = random.randint(6, 14)
        ang = random.uniform(-0.4, 0.4)
        draw.line([(bx, by), (bx + int(ln * math.cos(ang)), by + int(ln * math.sin(ang)))],
                  fill=BONE, width=2)

    return img


def gen_glasswind_causeway(w: int = 640, h: int = 360) -> Image.Image:
    """Hazard room: sand-blasted bridge over abyss with glass shards and wind streaks."""
    img = Image.new("RGBA", (w, h), SKY_MID)
    draw = ImageDraw.Draw(img)

    # Storm sky
    for y in range(int(h * 0.35)):
        t = y / (h * 0.35)
        c = _lerp_color(SKY_DEEP, _lerp_color(SKY_MID, HORIZON, 0.3), t)
        draw.line([(0, y), (w - 1, y)], fill=c)

    # Wind streaks (horizontal sand lines)
    for _ in range(40):
        sx = random.randint(0, w - 80)
        sy = random.randint(10, int(h * 0.42))
        length = random.randint(30, 120)
        draw.line([(sx, sy), (sx + length, sy + random.randint(-2, 2))],
                  fill=(*SAND_MID, random.randint(40, 120)), width=1)

    # Distant rock arches
    for bx in [120, 340, 520]:
        # Arch: two spires with a connecting span
        _jagged_spire(draw, bx - 20, int(h * 0.38), random.randint(40, 70), 14,
                      _lerp_color(ROCK_MID, HORIZON, 0.5),
                      _lerp_color(ROCK_LIGHT, HORIZON, 0.4))
        _jagged_spire(draw, bx + 20, int(h * 0.38), random.randint(40, 70), 14,
                      _lerp_color(ROCK_MID, HORIZON, 0.5),
                      _lerp_color(ROCK_LIGHT, HORIZON, 0.4))
        # Arch span
        arch_y = int(h * 0.38) - random.randint(25, 45)
        draw.arc([bx - 22, arch_y, bx + 22, arch_y + 30],
                 180, 0, fill=_lerp_color(ROCK_MID, HORIZON, 0.5), width=4)

    # Bridge
    bridge_y = int(h * 0.48)
    bridge_h = 22
    # Bridge body with perspective (wider near camera)
    draw.polygon([(0, bridge_y), (w, bridge_y - 4),
                  (w, bridge_y + bridge_h - 4), (0, bridge_y + bridge_h)], fill=RUST)
    # Top surface
    draw.polygon([(0, bridge_y), (w, bridge_y - 4),
                  (w, bridge_y + 3), (0, bridge_y + 4)], fill=BRASS)
    # Stone block pattern
    for bx in range(0, w, 32):
        draw.line([(bx, bridge_y), (bx, bridge_y + bridge_h)], fill=DARK_RUST, width=1)
    # Railing posts
    for rx in range(20, w, 40):
        ry = bridge_y - int(rx / w * 4)
        draw.line([(rx, ry - 18), (rx, ry)], fill=DARK_RUST, width=3)
        draw.rectangle([rx - 2, ry - 20, rx + 2, ry - 18], fill=ROCK_LIGHT)
    # Railing rope
    draw.line([(20, bridge_y - 20), (w - 20, bridge_y - 24)],
              fill=SAND_DARK, width=2)

    # Glass shard hazards
    for gx in range(60, w - 40, 80):
        gy = bridge_y - random.randint(2, 6)
        shard_h = random.randint(10, 20)
        draw.polygon([(gx, gy - shard_h), (gx + 5, gy), (gx - 5, gy)], fill=TEAL)
        draw.polygon([(gx, gy - shard_h), (gx + 5, gy), (gx + 1, gy - shard_h + 2)],
                     fill=_lerp_color(TEAL, SPECULAR, 0.5))
        draw.point((gx, gy - shard_h), fill=SPECULAR)

    # Void below
    for y in range(bridge_y + bridge_h, h):
        t = (y - bridge_y - bridge_h) / (h - bridge_y - bridge_h)
        c = _lerp_color(DARK_RUST, SHADOW, t * 0.8)
        draw.line([(0, y), (w - 1, y)], fill=c)
    # Fog wisps in void
    for _ in range(20):
        fx = random.randint(0, w)
        fy = random.randint(bridge_y + bridge_h + 20, h - 20)
        fl = random.randint(40, 120)
        draw.line([(fx, fy), (fx + fl, fy + random.randint(-3, 3))],
                  fill=(*HORIZON, random.randint(20, 60)), width=2)

    return img


def gen_ember_nave(w: int = 640, h: int = 360) -> Image.Image:
    """Boss arena: volcanic nave with molten cracks and oppressive pillars."""
    img = Image.new("RGBA", (w, h), SHADOW)
    draw = ImageDraw.Draw(img)

    # Ceiling glow
    for y in range(int(h * 0.2)):
        t = y / (h * 0.2)
        c = _lerp_color(SHADOW, DARK_RUST, t * 0.6)
        draw.line([(0, y), (w - 1, y)], fill=c)

    # Massive pillars (3-point perspective convergence to top-center)
    vanish_x = w // 2
    pillar_positions = [60, 160, 480, 580]
    for px in pillar_positions:
        # Pillar tapers toward ceiling vanishing point
        base_w = 40
        top_w = 28
        top_y = 20
        base_y = int(h * 0.72)
        # Compute pillar edges with perspective
        left_base = px - base_w // 2
        right_base = px + base_w // 2
        # Top converges toward vanish_x slightly
        dx = (vanish_x - px) * 0.08
        left_top = px - top_w // 2 + int(dx)
        right_top = px + top_w // 2 + int(dx)
        draw.polygon([(left_base, base_y), (right_base, base_y),
                      (right_top, top_y), (left_top, top_y)], fill=DARK_RUST)
        # Lit face
        mid = (left_base + right_base) // 2
        draw.polygon([(left_base, base_y), (mid, base_y),
                      ((left_top + right_top) // 2, top_y), (left_top, top_y)], fill=ROCK_MID)
        # Capital
        draw.rectangle([left_top - 6, top_y - 8, right_top + 6, top_y], fill=RUST)
        draw.rectangle([left_top - 4, top_y - 12, right_top + 4, top_y - 8], fill=ROCK_LIGHT)

    # Arena floor
    floor_y = int(h * 0.72)
    draw.rectangle([0, floor_y, w, h], fill=ROCK_MID)
    # Floor texture
    for _ in range(1500):
        x = random.randint(0, w - 1)
        y = random.randint(floor_y, h - 1)
        draw.point((x, y), fill=random.choice([DARK_RUST, ROCK_LIGHT, SAND_SHADOW]))

    # Molten cracks
    for _ in range(12):
        cx = random.randint(20, w - 20)
        cy = random.randint(floor_y + 5, h - 10)
        for seg in range(random.randint(4, 10)):
            nx = cx + random.randint(-8, 8)
            ny = cy + random.randint(1, 6)
            draw.line([(cx, cy), (nx, ny)], fill=MAGMA, width=2)
            draw.line([(cx, cy), (nx, ny)], fill=HIGHLIGHT, width=1)
            cx, cy = nx, ny

    # Boss pedestal
    ped_x = w // 2
    ped_y = floor_y + 8
    draw.polygon([(ped_x - 50, ped_y + 30), (ped_x + 50, ped_y + 30),
                  (ped_x + 40, ped_y), (ped_x - 40, ped_y)], fill=BRASS)
    draw.polygon([(ped_x - 40, ped_y), (ped_x + 40, ped_y),
                  (ped_x + 36, ped_y - 6), (ped_x - 36, ped_y - 6)], fill=HIGHLIGHT)

    # Ember particles
    for _ in range(60):
        ex = random.randint(40, w - 40)
        ey = random.randint(30, floor_y - 10)
        size = random.choice([1, 1, 1, 2])
        draw.ellipse([ex, ey, ex + size, ey + size], fill=random.choice([HIGHLIGHT, MAGMA, BRASS]))

    # Oppressive dark vignette corners
    for corner_x in [0, w]:
        for corner_y in [0, h]:
            for r in range(80, 10, -5):
                draw.ellipse([corner_x - r, corner_y - r, corner_x + r, corner_y + r],
                             fill=(*SHADOW, 8))

    return img


# ── Segmented character sprite sheet (256×512) ────────────────────

# Character proportions: 5 heads tall = 200px at our scale
# Head: 40px tall × 25px wide
# Shoulders: 50px wide, Waist: 34px wide
# Arms: shoulder to just past waist (~85px long)
# Each frame: 128×200 cell (arranged in 256×512 = 2 cols × ~2.5 rows of frames)

CHAR_H = 200  # total height
HEAD_H = 40
HEAD_W = 25
TORSO_H = 50   # shoulder to waist
SHOULDER_W = 50
WAIST_W = 34
ARM_LEN = 85   # shoulder to fingertips
UPPER_ARM = 42
FOREARM = 43
LEG_H = 70     # waist to ankles
THIGH = 38
SHIN = 32
FOOT_H = 10
SHEET_W = 512
SHEET_H = 1024
FRAME_W = 128
FRAME_H = 220


def _draw_body_segment(draw: ImageDraw.ImageDraw, pts: list[tuple], fill: tuple,
                       outline: tuple | None = None, width: int = 1) -> None:
    """Draw a body part polygon with optional outline."""
    if len(pts) >= 3:
        draw.polygon(pts, fill=fill)
        if outline:
            draw.polygon(pts, outline=outline)
    elif len(pts) == 2:
        draw.line(pts, fill=fill, width=max(width, 3))


def _draw_character_pose(draw: ImageDraw.ImageDraw, ox: int, oy: int,
                         pose: dict, squash_y: float = 1.0, stretch_x: float = 1.0) -> None:
    """Draw a full character at offset (ox, oy) with segmented body parts.

    pose keys:
        head_tilt, torso_lean, l_shoulder_angle, r_shoulder_angle,
        l_elbow_angle, r_elbow_angle, l_hip_angle, r_hip_angle,
        l_knee_angle, r_knee_angle, weapon_extend, cape_sway
    """
    cx = ox + FRAME_W // 2  # center x

    # Apply squash/stretch
    head_h = int(HEAD_H * squash_y)
    torso_h = int(TORSO_H * squash_y)
    leg_h_total = int(LEG_H * squash_y)
    shoulder_w = int(SHOULDER_W * stretch_x)

    # Key Y positions
    head_top = oy + 10
    neck_y = head_top + head_h
    waist_y = neck_y + torso_h
    foot_y = waist_y + leg_h_total + FOOT_H

    torso_lean = pose.get("torso_lean", 0)
    head_tilt = pose.get("head_tilt", 0)

    # ── Cape (behind) ──
    cape_sway = pose.get("cape_sway", 0)
    cape_pts = [
        (cx - shoulder_w // 2 - 2 + torso_lean, neck_y + 4),
        (cx - shoulder_w // 2 - 8 + cape_sway + torso_lean, waist_y + 20),
        (cx - shoulder_w // 2 + 6 + cape_sway + torso_lean, waist_y + 30),
        (cx - 4 + torso_lean, waist_y + 10),
    ]
    draw.polygon(cape_pts, fill=CAPE_RUST)
    # Cape dark fold
    fold_pts = [
        (cape_pts[0][0] + 4, cape_pts[0][1] + 3),
        (cape_pts[1][0] + 6, cape_pts[1][1] - 2),
        (cape_pts[2][0] - 2, cape_pts[2][1]),
        (cape_pts[3][0] - 2, cape_pts[3][1]),
    ]
    draw.polygon(fold_pts, fill=CAPE_DARK)

    # ── Torso ──
    t_cx = cx + torso_lean
    torso_pts = [
        (t_cx - shoulder_w // 2, neck_y),
        (t_cx + shoulder_w // 2, neck_y),
        (t_cx + int(WAIST_W * stretch_x) // 2, waist_y),
        (t_cx - int(WAIST_W * stretch_x) // 2, waist_y),
    ]
    draw.polygon(torso_pts, fill=CLOTH_TEAL)
    # Cloth fold lines
    for fy in range(neck_y + 8, waist_y - 4, 10):
        fw = int((shoulder_w - (shoulder_w - WAIST_W * stretch_x) * (fy - neck_y) / torso_h) * 0.4)
        draw.line([(t_cx - fw, fy), (t_cx - fw + 6, fy + 4)], fill=CLOTH_DARK, width=1)
        draw.line([(t_cx + fw - 6, fy), (t_cx + fw, fy + 4)], fill=CLOTH_DARK, width=1)
    # Belt
    draw.rectangle([t_cx - int(WAIST_W * stretch_x) // 2, waist_y - 4,
                     t_cx + int(WAIST_W * stretch_x) // 2, waist_y + 2], fill=BELT_BRASS)
    draw.rectangle([t_cx - 4, waist_y - 5, t_cx + 4, waist_y + 3], fill=HIGHLIGHT)

    # ── Legs ──
    thigh_len = int(THIGH * squash_y)
    shin_len = int(SHIN * squash_y)
    for side, hip_key, knee_key, x_offset in [
        ("L", "l_hip_angle", "l_knee_angle", -10),
        ("R", "r_hip_angle", "r_knee_angle", 10)
    ]:
        hip_angle = math.radians(pose.get(hip_key, 0))
        knee_angle = math.radians(pose.get(knee_key, 0))

        hip_x = t_cx + x_offset
        hip_y = waist_y + 2
        knee_x = hip_x + int(math.sin(hip_angle) * thigh_len)
        knee_y = hip_y + int(math.cos(hip_angle) * thigh_len)
        ankle_x = knee_x + int(math.sin(hip_angle + knee_angle) * shin_len)
        ankle_y = knee_y + int(math.cos(hip_angle + knee_angle) * shin_len)

        # Thigh
        draw.line([(hip_x, hip_y), (knee_x, knee_y)], fill=SAND_DARK, width=8)
        draw.line([(hip_x, hip_y), (knee_x, knee_y)], fill=SAND_MID, width=5)
        # Shin
        draw.line([(knee_x, knee_y), (ankle_x, ankle_y)], fill=SAND_DARK, width=7)
        draw.line([(knee_x, knee_y), (ankle_x, ankle_y)], fill=SAND_MID, width=4)
        # Knee joint marker
        draw.ellipse([knee_x - 4, knee_y - 4, knee_x + 4, knee_y + 4], fill=SAND_SHADOW)
        # Boot
        draw.ellipse([ankle_x - 6, ankle_y - 2, ankle_x + 8, ankle_y + FOOT_H],
                     fill=BOOT_BROWN)
        draw.ellipse([ankle_x - 4, ankle_y, ankle_x + 6, ankle_y + FOOT_H - 2],
                     fill=_lerp_color(BOOT_BROWN, SHADOW, 0.3))

    # ── Arms ──
    for side, sh_key, elb_key, x_offset in [
        ("L", "l_shoulder_angle", "l_elbow_angle", -(shoulder_w // 2)),
        ("R", "r_shoulder_angle", "r_elbow_angle", (shoulder_w // 2))
    ]:
        sh_angle = math.radians(pose.get(sh_key, 15 if side == "L" else -15))
        elb_angle = math.radians(pose.get(elb_key, 10 if side == "L" else -10))

        shoulder_x = t_cx + x_offset
        shoulder_y = neck_y + 6
        elbow_x = shoulder_x + int(math.sin(sh_angle) * UPPER_ARM)
        elbow_y = shoulder_y + int(math.cos(sh_angle) * UPPER_ARM)
        wrist_x = elbow_x + int(math.sin(sh_angle + elb_angle) * FOREARM)
        wrist_y = elbow_y + int(math.cos(sh_angle + elb_angle) * FOREARM)

        # Upper arm
        draw.line([(shoulder_x, shoulder_y), (elbow_x, elbow_y)], fill=SKIN_SHADOW, width=7)
        draw.line([(shoulder_x, shoulder_y), (elbow_x, elbow_y)], fill=SKIN_MID, width=4)
        # Forearm (wrapped cloth)
        draw.line([(elbow_x, elbow_y), (wrist_x, wrist_y)], fill=CLOTH_DARK, width=6)
        draw.line([(elbow_x, elbow_y), (wrist_x, wrist_y)], fill=CLOTH_TEAL, width=3)
        # Elbow joint
        draw.ellipse([elbow_x - 4, elbow_y - 4, elbow_x + 4, elbow_y + 4], fill=SKIN_SHADOW)
        # Hand
        draw.ellipse([wrist_x - 4, wrist_y - 3, wrist_x + 5, wrist_y + 5], fill=SKIN_MID)

        # Weapon in right hand
        if side == "R" and pose.get("weapon_extend", 0) > 0:
            ext = pose["weapon_extend"]
            blade_angle = sh_angle + elb_angle
            bx = wrist_x + int(math.sin(blade_angle) * ext)
            by = wrist_y + int(math.cos(blade_angle) * ext)
            draw.line([(wrist_x, wrist_y), (bx, by)], fill=WEAPON_BONE, width=3)
            draw.line([(wrist_x, wrist_y), (bx, by)], fill=BONE, width=1)
            draw.point((bx, by), fill=SPECULAR)

    # ── Head ──
    head_cx = cx + torso_lean + head_tilt
    # Neck
    draw.rectangle([head_cx - 5, neck_y - 4, head_cx + 5, neck_y + 4], fill=SKIN_MID)
    # Head shape (slightly oval)
    draw.ellipse([head_cx - HEAD_W // 2, head_top, head_cx + HEAD_W // 2, head_top + head_h],
                 fill=SKIN_MID)
    draw.ellipse([head_cx - HEAD_W // 2 + 1, head_top + 1,
                  head_cx + HEAD_W // 2 - 4, head_top + head_h - 1], fill=SKIN_LIGHT)
    # Pirate bandana
    draw.rectangle([head_cx - HEAD_W // 2 - 2, head_top + 2,
                    head_cx + HEAD_W // 2 + 2, head_top + 12], fill=RUST)
    draw.rectangle([head_cx - HEAD_W // 2 - 2, head_top + 6,
                    head_cx + HEAD_W // 2 + 2, head_top + 8], fill=DARK_RUST)
    # Bandana tail
    draw.line([(head_cx + HEAD_W // 2 + 2, head_top + 6),
               (head_cx + HEAD_W // 2 + 14, head_top + 14 + pose.get("cape_sway", 0))],
              fill=RUST, width=2)
    # Eyes
    eye_y = head_top + head_h // 2 + 2
    draw.ellipse([head_cx + 2, eye_y - 2, head_cx + 8, eye_y + 3], fill=(255, 255, 255))
    draw.ellipse([head_cx + 4, eye_y - 1, head_cx + 7, eye_y + 2], fill=SHADOW)
    # Nose
    draw.line([(head_cx + 1, eye_y + 2), (head_cx + 3, eye_y + 6)], fill=SKIN_SHADOW, width=1)
    # Jaw line
    draw.arc([head_cx - HEAD_W // 2 + 3, head_top + head_h // 2,
              head_cx + HEAD_W // 2 - 3, head_top + head_h + 2], 0, 180,
             fill=SKIN_SHADOW, width=1)


# Animation pose definitions
IDLE_POSES = [
    {"torso_lean": 0, "head_tilt": 0, "l_shoulder_angle": 12, "r_shoulder_angle": -12,
     "l_elbow_angle": 8, "r_elbow_angle": -8, "l_hip_angle": 2, "r_hip_angle": -2,
     "l_knee_angle": 0, "r_knee_angle": 0, "weapon_extend": 30, "cape_sway": 0},
    {"torso_lean": 0, "head_tilt": 1, "l_shoulder_angle": 13, "r_shoulder_angle": -11,
     "l_elbow_angle": 9, "r_elbow_angle": -7, "l_hip_angle": 2, "r_hip_angle": -2,
     "l_knee_angle": 1, "r_knee_angle": -1, "weapon_extend": 30, "cape_sway": 2},
    {"torso_lean": 0, "head_tilt": 0, "l_shoulder_angle": 12, "r_shoulder_angle": -12,
     "l_elbow_angle": 8, "r_elbow_angle": -8, "l_hip_angle": 2, "r_hip_angle": -2,
     "l_knee_angle": 0, "r_knee_angle": 0, "weapon_extend": 30, "cape_sway": -1},
    {"torso_lean": 0, "head_tilt": -1, "l_shoulder_angle": 11, "r_shoulder_angle": -13,
     "l_elbow_angle": 7, "r_elbow_angle": -9, "l_hip_angle": 2, "r_hip_angle": -2,
     "l_knee_angle": -1, "r_knee_angle": 1, "weapon_extend": 30, "cape_sway": -3},
]

WALK_POSES = [
    # Contact (right foot forward) - anticipation
    {"torso_lean": 2, "head_tilt": 1, "l_shoulder_angle": -20, "r_shoulder_angle": 25,
     "l_elbow_angle": 15, "r_elbow_angle": -20, "l_hip_angle": -15, "r_hip_angle": 22,
     "l_knee_angle": 5, "r_knee_angle": -10, "weapon_extend": 28, "cape_sway": 6},
    # Down (absorb)
    {"torso_lean": 1, "head_tilt": 0, "l_shoulder_angle": -10, "r_shoulder_angle": 15,
     "l_elbow_angle": 10, "r_elbow_angle": -15, "l_hip_angle": -8, "r_hip_angle": 15,
     "l_knee_angle": 12, "r_knee_angle": -5, "weapon_extend": 28, "cape_sway": 3},
    # Passing (vertical)
    {"torso_lean": 0, "head_tilt": 0, "l_shoulder_angle": 5, "r_shoulder_angle": -5,
     "l_elbow_angle": 5, "r_elbow_angle": -5, "l_hip_angle": 2, "r_hip_angle": -2,
     "l_knee_angle": 0, "r_knee_angle": 18, "weapon_extend": 30, "cape_sway": 0},
    # Up (push off)
    {"torso_lean": -1, "head_tilt": 0, "l_shoulder_angle": 15, "r_shoulder_angle": -20,
     "l_elbow_angle": -10, "r_elbow_angle": 10, "l_hip_angle": 12, "r_hip_angle": -18,
     "l_knee_angle": -5, "r_knee_angle": 5, "weapon_extend": 30, "cape_sway": -4},
    # Contact (left foot forward)
    {"torso_lean": 2, "head_tilt": -1, "l_shoulder_angle": 25, "r_shoulder_angle": -20,
     "l_elbow_angle": -20, "r_elbow_angle": 15, "l_hip_angle": 22, "r_hip_angle": -15,
     "l_knee_angle": -10, "r_knee_angle": 5, "weapon_extend": 28, "cape_sway": -6},
    # Down 2
    {"torso_lean": 1, "head_tilt": 0, "l_shoulder_angle": 15, "r_shoulder_angle": -10,
     "l_elbow_angle": -15, "r_elbow_angle": 10, "l_hip_angle": 15, "r_hip_angle": -8,
     "l_knee_angle": -5, "r_knee_angle": 12, "weapon_extend": 28, "cape_sway": -3},
]

ATTACK_POSES = [
    # Hit 1: Anticipation
    [{"torso_lean": -6, "head_tilt": -2, "l_shoulder_angle": 10, "r_shoulder_angle": -50,
      "l_elbow_angle": 5, "r_elbow_angle": -30, "l_hip_angle": 5, "r_hip_angle": -8,
      "l_knee_angle": 8, "r_knee_angle": -5, "weapon_extend": 35, "cape_sway": -8},
     # Hit 1: Strike
     {"torso_lean": 5, "head_tilt": 3, "l_shoulder_angle": 15, "r_shoulder_angle": 55,
      "l_elbow_angle": 8, "r_elbow_angle": 25, "l_hip_angle": 8, "r_hip_angle": -5,
      "l_knee_angle": 2, "r_knee_angle": -2, "weapon_extend": 48, "cape_sway": 10},
     # Hit 1: Follow-through
     {"torso_lean": 8, "head_tilt": 2, "l_shoulder_angle": 20, "r_shoulder_angle": 70,
      "l_elbow_angle": 10, "r_elbow_angle": 15, "l_hip_angle": 10, "r_hip_angle": -3,
      "l_knee_angle": 0, "r_knee_angle": 0, "weapon_extend": 44, "cape_sway": 14}],
    # Hit 2: Anticipation (reverse sweep)
    [{"torso_lean": 6, "head_tilt": 2, "l_shoulder_angle": 20, "r_shoulder_angle": 65,
      "l_elbow_angle": 10, "r_elbow_angle": 20, "l_hip_angle": -5, "r_hip_angle": 8,
      "l_knee_angle": -5, "r_knee_angle": 10, "weapon_extend": 40, "cape_sway": 12},
     # Hit 2: Strike
     {"torso_lean": -4, "head_tilt": -2, "l_shoulder_angle": 12, "r_shoulder_angle": -45,
      "l_elbow_angle": 5, "r_elbow_angle": -35, "l_hip_angle": -8, "r_hip_angle": 5,
      "l_knee_angle": 2, "r_knee_angle": -2, "weapon_extend": 50, "cape_sway": -8},
     # Hit 2: Follow-through
     {"torso_lean": -8, "head_tilt": -3, "l_shoulder_angle": 8, "r_shoulder_angle": -60,
      "l_elbow_angle": 3, "r_elbow_angle": -25, "l_hip_angle": -10, "r_hip_angle": 3,
      "l_knee_angle": 0, "r_knee_angle": 3, "weapon_extend": 42, "cape_sway": -14}],
    # Hit 3: Anticipation (overhead)
    [{"torso_lean": -3, "head_tilt": -4, "l_shoulder_angle": -30, "r_shoulder_angle": -65,
      "l_elbow_angle": -20, "r_elbow_angle": -40, "l_hip_angle": 10, "r_hip_angle": -10,
      "l_knee_angle": 15, "r_knee_angle": -12, "weapon_extend": 38, "cape_sway": -6},
     # Hit 3: Strike (slam down)
     {"torso_lean": 8, "head_tilt": 5, "l_shoulder_angle": 25, "r_shoulder_angle": 80,
      "l_elbow_angle": 15, "r_elbow_angle": 30, "l_hip_angle": 15, "r_hip_angle": -5,
      "l_knee_angle": 5, "r_knee_angle": -5, "weapon_extend": 55, "cape_sway": 16},
     # Hit 3: Follow-through (grounded)
     {"torso_lean": 12, "head_tilt": 4, "l_shoulder_angle": 30, "r_shoulder_angle": 85,
      "l_elbow_angle": 20, "r_elbow_angle": 10, "l_hip_angle": 18, "r_hip_angle": -8,
      "l_knee_angle": 2, "r_knee_angle": -2, "weapon_extend": 50, "cape_sway": 18}],
]

JUMP_POSES = [
    # Crouch (anticipation, squash)
    {"torso_lean": 0, "head_tilt": 0, "l_shoulder_angle": 20, "r_shoulder_angle": -20,
     "l_elbow_angle": 15, "r_elbow_angle": -15, "l_hip_angle": 20, "r_hip_angle": -20,
     "l_knee_angle": 35, "r_knee_angle": -35, "weapon_extend": 25, "cape_sway": 0,
     "_squash": 0.85, "_stretch": 1.1},
    # Ascent (stretch)
    {"torso_lean": 0, "head_tilt": -2, "l_shoulder_angle": 30, "r_shoulder_angle": -30,
     "l_elbow_angle": 20, "r_elbow_angle": -20, "l_hip_angle": -15, "r_hip_angle": 15,
     "l_knee_angle": -10, "r_knee_angle": 10, "weapon_extend": 32, "cape_sway": -10,
     "_squash": 1.12, "_stretch": 0.92},
    # Apex
    {"torso_lean": 0, "head_tilt": 0, "l_shoulder_angle": 25, "r_shoulder_angle": -25,
     "l_elbow_angle": 10, "r_elbow_angle": -10, "l_hip_angle": -5, "r_hip_angle": 5,
     "l_knee_angle": 8, "r_knee_angle": -8, "weapon_extend": 30, "cape_sway": -12},
    # Land (squash)
    {"torso_lean": 2, "head_tilt": 2, "l_shoulder_angle": 15, "r_shoulder_angle": -15,
     "l_elbow_angle": 12, "r_elbow_angle": -12, "l_hip_angle": 18, "r_hip_angle": -18,
     "l_knee_angle": 30, "r_knee_angle": -30, "weapon_extend": 26, "cape_sway": 4,
     "_squash": 0.88, "_stretch": 1.08},
]

DODGE_POSES = [
    # Wind-up
    {"torso_lean": -8, "head_tilt": -3, "l_shoulder_angle": 5, "r_shoulder_angle": -5,
     "l_elbow_angle": 5, "r_elbow_angle": -5, "l_hip_angle": -10, "r_hip_angle": 10,
     "l_knee_angle": 20, "r_knee_angle": -15, "weapon_extend": 20, "cape_sway": -12},
    # Mid-dash (extreme stretch)
    {"torso_lean": 15, "head_tilt": 5, "l_shoulder_angle": -35, "r_shoulder_angle": 35,
     "l_elbow_angle": -20, "r_elbow_angle": 20, "l_hip_angle": 30, "r_hip_angle": -30,
     "l_knee_angle": -15, "r_knee_angle": 15, "weapon_extend": 25, "cape_sway": -20,
     "_squash": 1.15, "_stretch": 0.85},
    # Recovery
    {"torso_lean": 4, "head_tilt": 1, "l_shoulder_angle": 10, "r_shoulder_angle": -10,
     "l_elbow_angle": 8, "r_elbow_angle": -8, "l_hip_angle": 5, "r_hip_angle": -5,
     "l_knee_angle": 5, "r_knee_angle": -5, "weapon_extend": 28, "cape_sway": -8},
]


def gen_field_handler_sheet() -> Image.Image:
    """Player character sprite sheet with segmented limbs and animation poses.

    Layout (128×220 cells on a 512×1024 sheet):
      Row 0: 4 idle frames
      Row 1: 6 walk frames (+ 2 blank)
      Row 2-3: 3 attack combos × 3 frames (anticipation/strike/follow-through)
      Row 4: 4 jump frames (crouch/ascent/apex/land)
      Row remaining: 3 dodge frames
    """
    img = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Row 0: Idle (4 frames)
    for i, pose in enumerate(IDLE_POSES):
        _draw_character_pose(draw, i * FRAME_W, 0, pose)

    # Row 1: Walk (6 frames)
    for i, pose in enumerate(WALK_POSES):
        _draw_character_pose(draw, i * FRAME_W, FRAME_H, pose)

    # Rows 2-3: Attack combos (3 hits × 3 frames = 9 frames)
    frame_idx = 0
    for combo in ATTACK_POSES:
        for pose in combo:
            col = frame_idx % 4
            row = 2 + frame_idx // 4
            _draw_character_pose(draw, col * FRAME_W, row * FRAME_H, pose)
            frame_idx += 1

    # Row 4: Jump (4 frames with squash/stretch)
    row_y = 4 * FRAME_H
    for i, pose in enumerate(JUMP_POSES):
        sq = pose.get("_squash", 1.0)
        st = pose.get("_stretch", 1.0)
        _draw_character_pose(draw, i * FRAME_W, row_y, pose, squash_y=sq, stretch_x=st)

    # Remaining: Dodge (3 frames)
    row_y = 5 * FRAME_H  # overflow handled by sheet height padding
    if row_y + FRAME_H <= SHEET_H:
        for i, pose in enumerate(DODGE_POSES):
            sq = pose.get("_squash", 1.0)
            st = pose.get("_stretch", 1.0)
            _draw_character_pose(draw, i * FRAME_W, row_y, pose, squash_y=sq, stretch_x=st)

    return img


# ── Chibi pet sprite sheets (256×256) ────────────────────────────

PET_SHEET = 256
PET_FRAME = 64  # 4×4 grid of 64px frames

def _draw_chibi_pet(draw: ImageDraw.ImageDraw, ox: int, oy: int,
                    body_color: tuple, accent: tuple, eye_color: tuple,
                    shape: str, bob: int = 0, emotion: str = "neutral") -> None:
    """Draw a chibi pet: large head (~40% height), compact body, distinct silhouette."""
    h = 52  # total pet height in cell
    head_h = int(h * 0.42)
    body_h = h - head_h
    cx = ox + PET_FRAME // 2
    body_top = oy + head_h + 4 - bob

    # ── Body (compact) ──
    if shape == "lizard":
        # Rounded body
        draw.ellipse([cx - 12, body_top, cx + 14, body_top + body_h - 4], fill=body_color)
        draw.ellipse([cx - 10, body_top + 2, cx + 10, body_top + body_h - 6],
                     fill=_lerp_color(body_color, accent, 0.3))
        # Tail (curvy)
        for t in range(8):
            tx = cx - 14 - t * 2
            ty = body_top + body_h // 2 + int(4 * math.sin(t * 0.8))
            draw.ellipse([tx - 2, ty - 1, tx + 2, ty + 1], fill=accent)
        # Legs (stubby)
        for lx in [cx - 8, cx + 8]:
            draw.rectangle([lx - 3, body_top + body_h - 6, lx + 3, body_top + body_h + 2],
                           fill=body_color)

    elif shape == "spider":
        # Round abdomen
        draw.ellipse([cx - 14, body_top + 2, cx + 14, body_top + body_h], fill=body_color)
        # Abdomen pattern
        draw.ellipse([cx - 8, body_top + 6, cx + 8, body_top + body_h - 4],
                     fill=_lerp_color(body_color, accent, 0.2))
        # Legs (4 per side, curving)
        for i in range(4):
            angle = -40 + i * 25
            for side in [-1, 1]:
                sx = cx + side * 14
                sy = body_top + 6 + i * 4
                ex = sx + side * (12 + i * 2)
                ey = sy + 8 - abs(i - 1.5) * 3
                mx = (sx + ex) // 2
                my = min(sy, ey) - 4
                draw.line([(sx, sy), (mx, my)], fill=accent, width=2)
                draw.line([(mx, my), (ex, ey)], fill=accent, width=2)

    elif shape == "ram":
        # Blocky stocky body
        draw.rectangle([cx - 14, body_top + 2, cx + 14, body_top + body_h - 2], fill=body_color)
        draw.rectangle([cx - 12, body_top + 4, cx + 12, body_top + body_h - 4],
                       fill=_lerp_color(body_color, (255, 255, 255), 0.15))
        # Legs (thick)
        for lx in [cx - 10, cx - 4, cx + 4, cx + 10]:
            draw.rectangle([lx - 3, body_top + body_h - 4, lx + 3, body_top + body_h + 4],
                           fill=_lerp_color(body_color, SHADOW, 0.3))
        # Fluffy tail
        draw.ellipse([cx - 18, body_top + body_h // 2 - 4,
                      cx - 12, body_top + body_h // 2 + 4], fill=accent)

    # ── Head (large, chibi) ──
    head_top = oy + 4 - bob
    head_w = int(head_h * 1.3)
    # Head shape
    draw.ellipse([cx - head_w // 2, head_top, cx + head_w // 2, head_top + head_h],
                 fill=body_color)
    # Cheek highlights
    draw.ellipse([cx - head_w // 2 + 3, head_top + head_h // 2,
                  cx - head_w // 2 + 10, head_top + head_h - 4],
                 fill=_lerp_color(body_color, (255, 200, 200), 0.3))

    # Eyes (big anime style)
    eye_y = head_top + head_h // 2 - 2
    for ex_offset in [-6, 6]:
        # Eye white
        draw.ellipse([cx + ex_offset - 5, eye_y - 4, cx + ex_offset + 5, eye_y + 5],
                     fill=(255, 255, 255))
        # Iris
        draw.ellipse([cx + ex_offset - 3, eye_y - 2, cx + ex_offset + 3, eye_y + 4],
                     fill=eye_color)
        # Pupil
        draw.ellipse([cx + ex_offset - 1, eye_y, cx + ex_offset + 2, eye_y + 3],
                     fill=SHADOW)
        # Highlight
        draw.ellipse([cx + ex_offset + 1, eye_y - 1, cx + ex_offset + 3, eye_y + 1],
                     fill=SPECULAR)
        if emotion == "distressed":
            # Worried brow
            draw.line([(cx + ex_offset - 4, eye_y - 6), (cx + ex_offset + 2, eye_y - 4)],
                      fill=SHADOW, width=2)

    # Mouth
    if emotion == "distressed":
        draw.arc([cx - 4, eye_y + 6, cx + 4, eye_y + 12], 0, 180, fill=SHADOW, width=1)
    else:
        draw.arc([cx - 3, eye_y + 5, cx + 3, eye_y + 9], 0, 180, fill=SHADOW, width=1)

    # Species-specific head features
    if shape == "lizard":
        # Small fin/crest
        draw.polygon([(cx, head_top - 2), (cx + 4, head_top + 4), (cx - 4, head_top + 4)],
                     fill=accent)
    elif shape == "spider":
        # Little fang marks under eyes and extra tiny eyes
        draw.point((cx - 10, eye_y), fill=eye_color)
        draw.point((cx + 10, eye_y), fill=eye_color)
        draw.point((cx - 8, eye_y - 5), fill=eye_color)
        draw.point((cx + 8, eye_y - 5), fill=eye_color)
    elif shape == "ram":
        # Curly horns
        for side in [-1, 1]:
            hx = cx + side * (head_w // 2 + 2)
            draw.arc([hx - 6, head_top + 2, hx + 6, head_top + 16],
                     90 if side > 0 else 270, 270 if side > 0 else 90,
                     fill=accent, width=3)


def _gen_chibi_sheet(body_color: tuple, accent: tuple, eye_color: tuple,
                     shape: str) -> Image.Image:
    """Generate a chibi pet sheet: 4×4 grid of 64px cells.
    Row 0: 4 idle frames
    Row 1: 4 walk frames
    Row 2: rescue/distressed poses
    Row 3: special (burst/ability frames)
    """
    img = Image.new("RGBA", (PET_SHEET, PET_SHEET), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Row 0: Idle (bob animation)
    for i in range(4):
        bob = [0, -2, 0, 2][i]
        _draw_chibi_pet(draw, i * PET_FRAME, 0, body_color, accent, eye_color, shape, bob=bob)

    # Row 1: Walk (alternating lean)
    for i in range(4):
        bob = [1, -1, 1, -1][i]
        _draw_chibi_pet(draw, i * PET_FRAME, PET_FRAME, body_color, accent, eye_color, shape, bob=bob)

    # Row 2: Distressed/rescue
    _draw_chibi_pet(draw, 0, PET_FRAME * 2, body_color, accent, eye_color, shape,
                    bob=3, emotion="distressed")
    _draw_chibi_pet(draw, PET_FRAME, PET_FRAME * 2, body_color, accent, eye_color, shape,
                    bob=1, emotion="distressed")

    # Row 3: Ability frames
    for i in range(4):
        bob = [0, -3, -1, 1][i]
        _draw_chibi_pet(draw, i * PET_FRAME, PET_FRAME * 3, body_color, accent, eye_color, shape, bob=bob)

    return img


def gen_mirror_newt_sheet() -> Image.Image:
    return _gen_chibi_sheet(TEAL, HIGHLIGHT, BRASS, "lizard")


def gen_latch_spider_sheet() -> Image.Image:
    return _gen_chibi_sheet(DARK_RUST, RUST, HIGHLIGHT, "spider")


def gen_salt_ram_sheet() -> Image.Image:
    return _gen_chibi_sheet(SAND_MID, BRASS, SHADOW, "ram")


# ── Bond Weave FX (256×256, 8 frames) ────────────────────────────

def gen_bond_weave_fx() -> Image.Image:
    """Bond weave effect: expanding energy rings with particle bursts."""
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    frame_size = 64

    for row in range(4):
        for col in range(4):
            frame = row * 4 + col
            if frame >= 10:
                break
            ox = col * frame_size
            oy = row * frame_size
            cx = ox + frame_size // 2
            cy = oy + frame_size // 2

            if frame < 6:
                # Expanding rings
                radius = 6 + frame * 5
                for r in range(radius, max(0, radius - 8), -2):
                    alpha = max(30, 255 - frame * 30)
                    color = _lerp_color(TEAL, HIGHLIGHT, frame / 6)
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                                 outline=(*color, alpha), width=2)
                # Inner glow
                inner = max(2, radius - 10)
                draw.ellipse([cx - inner, cy - inner, cx + inner, cy + inner],
                             fill=(*HIGHLIGHT, 60))
                # Spark particles
                for _ in range(frame * 3 + 2):
                    angle = random.uniform(0, 2 * math.pi)
                    dist = random.uniform(inner, radius + 4)
                    px = int(cx + math.cos(angle) * dist)
                    py = int(cy + math.sin(angle) * dist)
                    if ox <= px < ox + frame_size and oy <= py < oy + frame_size:
                        draw.ellipse([px - 1, py - 1, px + 1, py + 1],
                                     fill=random.choice([BRASS, HIGHLIGHT, SPECULAR]))
            else:
                # Dissipation frames
                fade = frame - 6
                radius = 26 + fade * 3
                alpha = max(10, 120 - fade * 30)
                draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                             outline=(*BRASS, alpha), width=1)
                for _ in range(8 - fade * 2):
                    angle = random.uniform(0, 2 * math.pi)
                    dist = random.uniform(radius - 5, radius + 5)
                    px = int(cx + math.cos(angle) * dist)
                    py = int(cy + math.sin(angle) * dist)
                    if ox <= px < ox + frame_size and oy <= py < oy + frame_size:
                        draw.point((px, py), fill=(*HIGHLIGHT, alpha))

    return img


# ── HUD Pack (256×256) ────────────────────────────────────────────

def gen_hud_pack() -> Image.Image:
    """HUD elements at production resolution."""
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # HP bar (top section)
    draw.rounded_rectangle([8, 8, 200, 28], radius=4, fill=SHADOW)
    draw.rounded_rectangle([10, 10, 140, 26], radius=3, fill=RUST)
    draw.rounded_rectangle([10, 10, 100, 18], radius=2, fill=HIGHLIGHT)
    # HP label area
    draw.rectangle([204, 8, 248, 28], fill=(*SHADOW, 180))

    # Bond tension meter
    draw.rounded_rectangle([8, 36, 200, 52], radius=4, fill=SHADOW)
    draw.rounded_rectangle([10, 38, 150, 50], radius=3, fill=BRASS)
    # Tension zone markers
    for tx in [80, 120, 160]:
        draw.line([(tx, 36), (tx, 52)], fill=(*RUST, 180), width=1)

    # Weave charge ring
    ring_cx, ring_cy = 48, 100
    draw.ellipse([ring_cx - 30, ring_cy - 30, ring_cx + 30, ring_cy + 30],
                 outline=SHADOW, width=4)
    draw.arc([ring_cx - 28, ring_cy - 28, ring_cx + 28, ring_cy + 28],
             -90, 180, fill=TEAL, width=6)
    draw.arc([ring_cx - 26, ring_cy - 26, ring_cx + 26, ring_cy + 26],
             -90, 90, fill=HIGHLIGHT, width=3)

    # Pet slot indicators (4 slots)
    pet_colors = [RUST, TEAL, SAND_MID, HIGHLIGHT]
    pet_labels = ["B", "C", "Cr", "K"]
    for i in range(4):
        sx = 120 + i * 34
        sy = 80
        draw.rounded_rectangle([sx, sy, sx + 28, sy + 28], radius=3, fill=SHADOW)
        draw.rounded_rectangle([sx + 2, sy + 2, sx + 26, sy + 26], radius=2,
                               fill=pet_colors[i])
        draw.rounded_rectangle([sx + 4, sy + 4, sx + 24, sy + 24], radius=2,
                               fill=_lerp_color(pet_colors[i], SHADOW, 0.4))

    # Milestone tracker frame
    draw.rounded_rectangle([8, 140, 248, 200], radius=6, outline=BRASS, width=2)
    draw.rounded_rectangle([12, 144, 244, 196], radius=4, fill=(*SHADOW, 200))
    # Milestone dots
    for i in range(8):
        mx = 24 + i * 28
        my = 170
        if i < 5:
            draw.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill=BRASS)
        else:
            draw.ellipse([mx - 6, my - 6, mx + 6, my + 6], outline=SAND_DARK, width=1)

    # Minimap frame
    draw.rounded_rectangle([8, 210, 100, 248], radius=4, outline=SAND_DARK, width=2)
    draw.rounded_rectangle([10, 212, 98, 246], radius=3, fill=(*SKY_DEEP, 180))
    # Minimap room dots
    for _ in range(6):
        rx = random.randint(16, 90)
        ry = random.randint(218, 240)
        draw.ellipse([rx - 2, ry - 2, rx + 2, ry + 2], fill=TEAL)

    return img


# ── Audio: Hijaz-scale Arabic-Mexican fusion ──────────────────────

SAMPLE_RATE = 22050


def _sine_wave(freq: float, duration: float, amplitude: float = 0.5,
               attack: float = 0.05, release: float = 0.1) -> np.ndarray:
    """Generate a sine wave with attack/release envelope."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    wave = np.sin(2 * np.pi * freq * t) * amplitude
    # Envelope
    attack_n = int(SAMPLE_RATE * attack)
    release_n = int(SAMPLE_RATE * release)
    env = np.ones(n)
    if attack_n > 0:
        env[:attack_n] = np.linspace(0, 1, attack_n)
    if release_n > 0 and release_n < n:
        env[-release_n:] = np.linspace(1, 0, release_n)
    return wave * env


def _saw_wave(freq: float, duration: float, amplitude: float = 0.3,
              attack: float = 0.08, release: float = 0.15) -> np.ndarray:
    """Filtered sawtooth for violin-like timbre."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    # Additive synthesis: sum of harmonics with roll-off (violin-like)
    wave = np.zeros(n)
    for harmonic in range(1, 8):
        wave += np.sin(2 * np.pi * freq * harmonic * t) * (amplitude / (harmonic * 1.2))
    # Vibrato
    vibrato = 1.0 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
    wave *= vibrato
    # Envelope
    attack_n = int(SAMPLE_RATE * attack)
    release_n = int(SAMPLE_RATE * release)
    env = np.ones(n)
    if attack_n > 0:
        env[:attack_n] = np.linspace(0, 1, attack_n)
    if release_n > 0 and release_n < n:
        env[-release_n:] = np.linspace(1, 0, release_n)
    return wave * env


def _brass_tone(freq: float, duration: float, amplitude: float = 0.25) -> np.ndarray:
    """Brass-like tone via clipped square harmonics."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    wave = np.zeros(n)
    for h in [1, 2, 3, 5]:
        wave += np.sin(2 * np.pi * freq * h * t) * (amplitude / (h * 0.8))
    wave = np.clip(wave, -amplitude, amplitude)
    # Attack envelope (brass swell)
    attack_n = int(SAMPLE_RATE * 0.12)
    release_n = int(SAMPLE_RATE * 0.08)
    env = np.ones(n)
    if attack_n > 0:
        env[:attack_n] = np.linspace(0, 1, attack_n)
    if release_n > 0 and release_n < n:
        env[-release_n:] = np.linspace(1, 0, release_n)
    return wave * env


def _percussion_hit(duration: float = 0.15, amplitude: float = 0.6) -> np.ndarray:
    """Noise burst percussion (large drum)."""
    n = int(SAMPLE_RATE * duration)
    noise = np.random.uniform(-1, 1, n) * amplitude
    # Sharp attack, exponential decay
    env = np.exp(-np.linspace(0, 8, n))
    # Low-pass effect: running average
    kernel = 8
    padded = np.pad(noise * env, (kernel, 0), mode='edge')
    filtered = np.convolve(padded, np.ones(kernel) / kernel, mode='valid')[:n]
    return filtered


def _hijaz_scale(root: float = 220.0) -> list[float]:
    """Hijaz maqam/Phrygian dominant scale: 1 b2 3 4 5 b6 b7.
    This creates that Arabic-meets-Mexican/Mariachi feel."""
    intervals = [0, 1, 4, 5, 7, 8, 10]  # semitones
    return [root * (2 ** (i / 12)) for i in intervals]


def gen_theme_music() -> bytes:
    """Generate a ~16 second Arabic-Mexican fusion loop.

    Structure: 4-bar melody (violin) + brass counterpoint + percussion.
    """
    bpm = 90
    beat = 60.0 / bpm
    bar = beat * 4
    total_duration = bar * 4
    n_total = int(SAMPLE_RATE * total_duration)
    mix = np.zeros(n_total, dtype=np.float64)

    scale = _hijaz_scale(220.0)
    scale_hi = _hijaz_scale(440.0)

    # ── Violin melody (call and response pattern) ──
    melody_pattern = [
        # Bar 1: ascending phrase
        (0, beat * 0.8), (2, beat * 0.4), (3, beat * 0.6), (4, beat * 1.2),
        # Bar 2: ornamental descent
        (4, beat * 0.5), (3, beat * 0.3), (2, beat * 0.9), (1, beat * 0.6),
        (0, beat * 1.0),
        # Bar 3: leap and resolve
        (5, beat * 0.6), (6, beat * 0.4), (4, beat * 1.0), (3, beat * 0.5),
        (2, beat * 0.5), (0, beat * 1.0),
        # Bar 4: sustain home
        (0, beat * 1.5), (1, beat * 0.5), (0, beat * 2.0),
    ]
    t_cursor = 0.0
    for note_idx, dur in melody_pattern:
        freq = scale[note_idx % len(scale)]
        if note_idx >= len(scale):
            freq = scale_hi[note_idx - len(scale)]
        start = int(t_cursor * SAMPLE_RATE)
        tone = _saw_wave(freq, dur, amplitude=0.22)
        end = min(start + len(tone), n_total)
        mix[start:end] += tone[:end - start]
        t_cursor += dur

    # ── Brass counterpoint (sustained chords) ──
    brass_pattern = [
        (0, bar),           # root
        (3, bar * 0.5), (4, bar * 0.5),  # 4th -> 5th
        (2, bar),           # 3rd (major)
        (0, bar * 0.5), (5, bar * 0.5),  # root -> b6
    ]
    t_cursor = 0.0
    for note_idx, dur in brass_pattern:
        freq = scale[note_idx % len(scale)] * 0.5  # octave below
        start = int(t_cursor * SAMPLE_RATE)
        tone = _brass_tone(freq, dur, amplitude=0.12)
        end = min(start + len(tone), n_total)
        mix[start:end] += tone[:end - start]
        t_cursor += dur

    # ── Percussion (large drum on 1 and 3, snare-like on 2 and 4) ──
    for bar_num in range(4):
        for beat_num in range(4):
            t = bar_num * bar + beat_num * beat
            start = int(t * SAMPLE_RATE)
            if beat_num % 2 == 0:
                hit = _percussion_hit(0.2, 0.35)
            else:
                hit = _percussion_hit(0.1, 0.18)
            end = min(start + len(hit), n_total)
            mix[start:end] += hit[:end - start]
        # Extra subdivisions (triplet feel for Mexican rhythm)
        for sub in [0.33, 0.67, 2.33, 2.67]:
            t = bar_num * bar + sub * beat
            start = int(t * SAMPLE_RATE)
            hit = _percussion_hit(0.06, 0.10)
            end = min(start + len(hit), n_total)
            mix[start:end] += hit[:end - start]

    # Normalize
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.85

    # Convert to 16-bit PCM
    pcm = (mix * 32767).astype(np.int16)
    return pcm.tobytes()


def gen_ambient_desert() -> bytes:
    """Generate ~8 seconds of desert wind ambience."""
    duration = 8.0
    n = int(SAMPLE_RATE * duration)
    # Low rumble
    t = np.linspace(0, duration, n, endpoint=False)
    wind = np.zeros(n, dtype=np.float64)
    # Filtered noise (wind)
    noise = np.random.uniform(-1, 1, n) * 0.15
    # Slow amplitude modulation (gusting)
    gust = 0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * t) * np.sin(2 * np.pi * 0.08 * t + 1.3)
    wind += noise * gust
    # Low drone
    wind += np.sin(2 * np.pi * 55 * t) * 0.05 * gust
    wind += np.sin(2 * np.pi * 82.5 * t) * 0.03 * gust
    # Very subtle Hijaz note
    wind += np.sin(2 * np.pi * 220 * t) * 0.015 * gust * np.sin(2 * np.pi * 0.2 * t)
    # Normalize
    peak = np.max(np.abs(wind))
    if peak > 0:
        wind = wind / peak * 0.7
    pcm = (wind * 32767).astype(np.int16)
    return pcm.tobytes()


def _write_wav(path: Path, pcm_data: bytes) -> None:
    """Write mono 16-bit WAV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)


# ── Main ──────────────────────────────────────────────────────────

GENERATORS = {
    "spaces/latchspire_refuge_backdrop.png": gen_latchspire_refuge,
    "spaces/choir_stair_backdrop.png": gen_choir_stair,
    "spaces/glasswind_causeway_backdrop.png": gen_glasswind_causeway,
    "spaces/ember_nave_backdrop.png": gen_ember_nave,
    "actors/field_handler_sheet.png": gen_field_handler_sheet,
    "actors/mirror_newt_sheet.png": gen_mirror_newt_sheet,
    "actors/latch_spider_sheet.png": gen_latch_spider_sheet,
    "actors/salt_ram_sheet.png": gen_salt_ram_sheet,
    "effects/bond_weave_fx.png": gen_bond_weave_fx,
    "interface/aridfeihth_hud_pack.png": gen_hud_pack,
}


def main() -> None:
    print("Generating production sprites...")
    for rel_path, gen_fn in GENERATORS.items():
        out_path = OUT_ROOT / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img = gen_fn()
        img.save(str(out_path))
        print(f"  [{img.size[0]}×{img.size[1]}] {out_path.relative_to(WORKSPACE)}")

    print("\nGenerating audio...")
    theme_path = OUT_ROOT / "audio" / "aridfeihth_theme.wav"
    _write_wav(theme_path, gen_theme_music())
    print(f"  [16s loop] {theme_path.relative_to(WORKSPACE)}")

    ambient_path = OUT_ROOT / "audio" / "desert_wind_ambient.wav"
    _write_wav(ambient_path, gen_ambient_desert())
    print(f"  [8s loop]  {ambient_path.relative_to(WORKSPACE)}")

    total = len(GENERATORS) + 2
    print(f"\n  {total} assets generated under aridfeihth/production_raw/")


if __name__ == "__main__":
    main()
