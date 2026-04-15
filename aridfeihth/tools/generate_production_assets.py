"""Generate production-quality assets for aridfeihth vertical slice.

Environments: 640x360  – procedural dunes, sand grain detail, jagged spires, 3-point perspective
Characters:   256x512  – segmented body parts, 5-head proportions, anticipation/follow-through
Pets:         128x128  – chibi (large head, compact body), half human scale
FX:           256x64   – bond weave expansion strip
HUD:          320x80   – meters, pet slots, milestone frame
Audio:        WAV       – Hijaz-scale violin/brass/percussion fusion

Palette (ash-reliquary frontier):
    Ash cobalt sky   #2d3448    Oxidized brass #b59657
    Ember rust       #934632    Kiln brown     #8e7157
    Grave grey       #6b6968    Slate cobalt   #5e738c
    Deep shadow      #16171b    Brass glow     #d2b06a
    Bone dust        #c7b395    Dark rust      #5f2f22
"""
from __future__ import annotations

import math
import random
import json
import struct
import wave
from pathlib import Path

from PIL import Image, ImageDraw

WORKSPACE = Path(__file__).resolve().parents[2]
OUT_ROOT = WORKSPACE / "aridfeihth" / "production_raw"

random.seed(42)

# ── Palette ────────────────────────────────────────────────────────
SKY        = (0x2D, 0x34, 0x48)
SKY_TOP    = (0x16, 0x19, 0x24)
SKY_MID    = (0x48, 0x4D, 0x59)
SKY_LOW    = (0x68, 0x63, 0x60)
BRASS      = (0xB5, 0x96, 0x57)
RUST       = (0x93, 0x46, 0x32)
SAND       = (0xA4, 0x87, 0x6C)
SAND_LIGHT = (0xC7, 0xB3, 0x95)
SAND_DARK  = (0x6A, 0x56, 0x45)
SHADOW     = (0x16, 0x17, 0x1B)
TEAL       = (0x5E, 0x73, 0x8C)
HIGHLIGHT  = (0xD2, 0xB0, 0x6A)
DARK_RUST  = (0x5F, 0x2F, 0x22)
BONE       = (0xC7, 0xB3, 0x95)
MID_BLUE   = (0x4C, 0x5B, 0x6F)
WARM_RUST  = (0xB9, 0x62, 0x48)
IRON       = (0x6B, 0x69, 0x68)
DETAIL_DARK = (0x0E, 0x0F, 0x12)
SOOT       = (0x23, 0x20, 0x1F)
SKIN       = (0xC8, 0xA0, 0x78)
SKIN_SHADE = (0xA0, 0x7C, 0x58)
HAIR       = (0x2A, 0x1E, 0x14)
BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)
PIXEL_ART_COLOR_COUNT = 64
ANIMATION_FRAME_MS = 70
ANIMATION_HOLD_REPEATS = 2
ANIMATION_MOVE_REPEATS = 1


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _noise_seed() -> float:
    return random.random()


def _held_pose(base_pose: dict, repeats: int = 2, **overrides: int) -> list[dict]:
    pose = dict(base_pose)
    pose.update(overrides)
    return [dict(pose) for _ in range(repeats)]


# ═══════════════════════════════════════════════════════════════════
# ENVIRONMENTS  640×360
# ═══════════════════════════════════════════════════════════════════

ENV_W, ENV_H = 640, 360


def _sky_gradient(draw: ImageDraw.ImageDraw, w: int, h: int, horizon_y: int) -> None:
    """3-band dusk gradient with muted cobalt preserved as an accent."""
    for y in range(horizon_y):
        t = y / max(1, horizon_y)
        if t < 0.4:
            c = _lerp_color(SKY_TOP, SKY, t / 0.4)
        elif t < 0.75:
            c = _lerp_color(SKY, SKY_MID, (t - 0.4) / 0.35)
        else:
            c = _lerp_color(SKY_MID, SKY_LOW, (t - 0.75) / 0.25)
        draw.line([(0, y), (w - 1, y)], fill=c)


def _sand_grain_texture(img: Image.Image, y_start: int, y_end: int, density: float = 0.12) -> None:
    """Per-pixel specular sand grain noise — tiny bright/dark flecks."""
    pixels = img.load()
    w = img.width
    for y in range(max(0, y_start), min(img.height, y_end)):
        for x in range(w):
            if random.random() < density:
                r, g, b = pixels[x, y][:3] if img.mode == "RGBA" else pixels[x, y]
                shift = random.choice([-18, -12, -8, 8, 14, 22])
                nr = max(0, min(255, r + shift))
                ng = max(0, min(255, g + shift))
                nb = max(0, min(255, b + shift))
                if img.mode == "RGBA":
                    pixels[x, y] = (nr, ng, nb, 255)
                else:
                    pixels[x, y] = (nr, ng, nb)


def _dune_contour(draw: ImageDraw.ImageDraw, w: int, base_y: int, amplitude: float,
                  freq: float, phase: float, color_top: tuple, color_body: tuple, h: int) -> None:
    """Sine-based dune with lit crest and shaded body."""
    points_top = []
    for x in range(w + 1):
        dy = amplitude * math.sin(freq * x / w * math.pi * 2 + phase)
        dy += amplitude * 0.3 * math.sin(freq * 2.3 * x / w * math.pi * 2 + phase * 1.7)
        y = base_y + int(dy)
        points_top.append((x, y))

    # Fill body below dune crest
    for x, crest_y in points_top:
        for y in range(crest_y, h):
            t = min(1.0, (y - crest_y) / max(1, h - crest_y))
            c = _lerp_color(color_body, SHADOW, t * 0.4)
            draw.point((x, y), fill=c)
    # Lit crest highlight
    for x, crest_y in points_top:
        draw.point((x, crest_y), fill=color_top)
        if crest_y + 1 < h:
            draw.point((x, crest_y + 1), fill=_lerp_color(color_top, color_body, 0.5))


def _jagged_spires(draw: ImageDraw.ImageDraw, w: int, horizon_y: int, count: int = 7) -> None:
    """Sharp rocky outcroppings silhouetted on the horizon."""
    for i in range(count):
        cx = int(w * (i + 0.5) / count + random.randint(-30, 30))
        base_w = random.randint(8, 28)
        spire_h = random.randint(30, 80)
        top_y = horizon_y - spire_h
        # Jagged peak shape — asymmetric triangle with notches
        peak_offset = random.randint(-6, 6)
        pts = [(cx - base_w, horizon_y), (cx + peak_offset, top_y)]
        # Add 1-2 jagged notches along the right edge
        notch_y = top_y + spire_h // 3
        pts.append((cx + base_w // 3, notch_y))
        pts.append((cx + base_w // 4 - 2, notch_y + random.randint(4, 12)))
        pts.append((cx + base_w, horizon_y))

        outline_c = _lerp_color(DARK_RUST, SHADOW, 0.6)
        draw.polygon(pts, fill=outline_c)
        # Lit edge on left face
        for j in range(len(pts) - 1):
            draw.line([pts[j], pts[j + 1]], fill=_lerp_color(DARK_RUST, RUST, 0.3), width=1)


def _arch_formation(draw: ImageDraw.ImageDraw, cx: int, horizon_y: int) -> None:
    """Natural stone arch silhouette."""
    arch_w = random.randint(40, 70)
    arch_h = random.randint(30, 55)
    pillar_w = arch_w // 5
    top_y = horizon_y - arch_h
    c = _lerp_color(DARK_RUST, SHADOW, 0.5)
    # Left pillar
    draw.rectangle([cx - arch_w // 2, top_y + arch_h // 3, cx - arch_w // 2 + pillar_w, horizon_y], fill=c)
    # Right pillar
    draw.rectangle([cx + arch_w // 2 - pillar_w, top_y + arch_h // 3, cx + arch_w // 2, horizon_y], fill=c)
    # Arch curve
    draw.arc([cx - arch_w // 2, top_y, cx + arch_w // 2, top_y + arch_h],
             start=180, end=360, fill=c, width=pillar_w)


def _3point_ground_lines(draw: ImageDraw.ImageDraw, w: int, horizon_y: int, h: int) -> None:
    """Converging perspective lines on the ground plane."""
    vp_x = w // 2
    vp_y = horizon_y
    for offset in range(-w, w * 2, 60):
        x_bot = offset
        draw.line([(x_bot, h), (vp_x, vp_y)], fill=_lerp_color(SAND_DARK, SHADOW, 0.15), width=1)


def _shadow_band(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], thickness: int = 10) -> None:
    for x, y in points:
        for dy in range(thickness):
            draw.point((x, y + dy), fill=_lerp_color(DETAIL_DARK, SHADOW, min(1.0, dy / max(1, thickness))))


def _scatter_dark_detail(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, count: int, accent: tuple = DETAIL_DARK) -> None:
    for _ in range(count):
        px = random.randint(x1, x2)
        py = random.randint(y1, y2)
        if random.random() < 0.5:
            draw.point((px, py), fill=accent)
        else:
            draw.line([(px, py), (px + random.randint(1, 3), py + random.randint(-1, 1))], fill=accent, width=1)


def _draw_lane_glyph(draw: ImageDraw.ImageDraw, lane: str, x: int, y: int, color: tuple) -> None:
    if lane == "burst":
        draw.line([(x + 3, y + 2), (x + 10, y + 8)], fill=color, width=1)
        draw.line([(x + 10, y + 8), (x + 5, y + 8)], fill=color, width=1)
        draw.line([(x + 10, y + 8), (x + 8, y + 3)], fill=color, width=1)
    elif lane == "chorus":
        draw.arc([x + 1, y + 1, x + 11, y + 11], start=200, end=340, fill=color, width=1)
        draw.arc([x + 3, y + 3, x + 13, y + 13], start=200, end=340, fill=color, width=1)
    elif lane == "crest":
        draw.polygon([(x + 7, y + 1), (x + 12, y + 6), (x + 9, y + 12), (x + 5, y + 12), (x + 2, y + 6)], outline=color, fill=None)
    elif lane == "key":
        draw.ellipse([x + 2, y + 3, x + 8, y + 9], outline=color, width=1)
        draw.line([(x + 8, y + 6), (x + 13, y + 6)], fill=color, width=1)
        draw.line([(x + 11, y + 6), (x + 11, y + 9)], fill=color, width=1)
        draw.line([(x + 13, y + 6), (x + 13, y + 8)], fill=color, width=1)


def _finalize_pixel_art(img: Image.Image) -> Image.Image:
    """Constrain output to a crisp 64-color pixel-art treatment while preserving size and alpha."""
    if img.mode == "RGBA":
        alpha = img.getchannel("A")
        quantized = img.convert("RGB").quantize(colors=PIXEL_ART_COLOR_COUNT, dither=Image.Dither.NONE)
        final_img = quantized.convert("RGBA")
        final_img.putalpha(alpha)
        return final_img
    quantized = img.convert("RGB").quantize(colors=PIXEL_ART_COLOR_COUNT, dither=Image.Dither.NONE)
    return quantized.convert("RGB")


def gen_latchspire_refuge() -> Image.Image:
    img = Image.new("RGB", (ENV_W, ENV_H), SKY)
    draw = ImageDraw.Draw(img)
    horizon = 200

    _sky_gradient(draw, ENV_W, ENV_H, horizon)
    _jagged_spires(draw, ENV_W, horizon, count=5)
    _arch_formation(draw, 480, horizon)

    # Far dune layer
    _dune_contour(draw, ENV_W, horizon + 10, 18, 1.2, 0.3, SAND_LIGHT, SAND, ENV_H)
    # Mid dune
    _dune_contour(draw, ENV_W, horizon + 40, 25, 0.8, 1.1, BRASS, SAND_DARK, ENV_H)
    # Foreground dune
    _dune_contour(draw, ENV_W, horizon + 80, 30, 0.6, 2.2, HIGHLIGHT, SAND, ENV_H)

    _3point_ground_lines(draw, ENV_W, horizon, ENV_H)
    _scatter_dark_detail(draw, 0, horizon + 18, ENV_W - 1, ENV_H - 8, 180, SOOT)

    # Tower refuge structure (center)
    tower_x, tower_w = 280, 60
    tower_top = 100
    draw.rectangle([tower_x, tower_top, tower_x + tower_w, horizon + 60], fill=RUST)
    draw.rectangle([tower_x + 4, tower_top + 4, tower_x + tower_w - 4, horizon + 56], fill=DARK_RUST)
    draw.rectangle([tower_x + 4, tower_top + 4, tower_x + 12, horizon + 56], fill=_lerp_color(HIGHLIGHT, BRASS, 0.35))
    draw.rectangle([tower_x + tower_w - 12, tower_top + 4, tower_x + tower_w - 4, horizon + 56], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.15))
    for seam_y in range(tower_top + 10, horizon + 54, 16):
        draw.line([(tower_x + 6, seam_y), (tower_x + tower_w - 6, seam_y)], fill=DETAIL_DARK, width=1)
    draw.line([(tower_x + tower_w // 2, tower_top + 4), (tower_x + tower_w // 2, horizon + 54)], fill=SOOT, width=1)
    # Spire top
    draw.polygon([(tower_x - 6, tower_top), (tower_x + tower_w // 2, tower_top - 40),
                   (tower_x + tower_w + 6, tower_top)], fill=BRASS)
    draw.polygon([(tower_x + tower_w // 2, tower_top - 40), (tower_x + tower_w + 6, tower_top), (tower_x + tower_w // 2 + 6, tower_top)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.2))
    # Windows (3 rows)
    for wy in range(tower_top + 20, horizon + 40, 28):
        for wx_off in [14, 36]:
            draw.rectangle([tower_x + wx_off, wy, tower_x + wx_off + 10, wy + 14], fill=HIGHLIGHT)
            draw.rectangle([tower_x + wx_off + 2, wy + 2, tower_x + wx_off + 8, wy + 12], fill=TEAL)
            draw.line([(tower_x + wx_off + 1, wy + 13), (tower_x + wx_off + 9, wy + 13)], fill=DETAIL_DARK, width=1)
    # Flag
    draw.line([(tower_x + tower_w // 2, tower_top - 40), (tower_x + tower_w // 2, tower_top - 58)], fill=SHADOW, width=2)
    draw.polygon([(tower_x + tower_w // 2, tower_top - 58), (tower_x + tower_w // 2 + 20, tower_top - 52),
                   (tower_x + tower_w // 2, tower_top - 46)], fill=RUST)
    draw.arc([454, horizon - 46, 508, horizon + 8], start=180, end=360, fill=DETAIL_DARK, width=3)
    draw.polygon([(tower_x + tower_w, horizon + 46), (tower_x + tower_w + 92, horizon + 34), (tower_x + tower_w + 132, ENV_H - 4), (tower_x + tower_w + 20, ENV_H - 4)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.28))
    draw.polygon([(480, horizon + 2), (514, horizon + 6), (550, horizon + 44), (506, horizon + 44)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.22))

    _sand_grain_texture(img, horizon, ENV_H, density=0.08)
    return img


def gen_choir_stair() -> Image.Image:
    img = Image.new("RGB", (ENV_W, ENV_H), SKY)
    draw = ImageDraw.Draw(img)
    horizon = 180

    _sky_gradient(draw, ENV_W, ENV_H, horizon)
    _jagged_spires(draw, ENV_W, horizon, count=8)

    # Far dune
    _dune_contour(draw, ENV_W, horizon + 5, 15, 1.5, 0.7, SAND_LIGHT, SAND, ENV_H)
    _dune_contour(draw, ENV_W, horizon + 35, 20, 1.0, 1.8, BRASS, SAND_DARK, ENV_H)

    _3point_ground_lines(draw, ENV_W, horizon, ENV_H)
    _scatter_dark_detail(draw, 0, horizon + 30, ENV_W - 1, ENV_H - 1, 220, SOOT)

    # Ruin pillars (crumbling)
    pillar_positions = [60, 160, 280, 400, 530]
    for px in pillar_positions:
        ph = random.randint(80, 140)
        pw = random.randint(16, 24)
        top = horizon + 40 - ph
        draw.rectangle([px, top, px + pw, horizon + 60], fill=DARK_RUST)
        draw.rectangle([px - 4, top - 6, px + pw + 4, top], fill=RUST)
        draw.rectangle([px + 1, top, px + 4, horizon + 60], fill=_lerp_color(HIGHLIGHT, BRASS, 0.18))
        draw.rectangle([px + pw - 4, top, px + pw - 1, horizon + 60], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.1))
        draw.line([(px + pw - 2, top + 4), (px + pw - 2, horizon + 56)], fill=DETAIL_DARK, width=1)
        # Crack details
        for _ in range(3):
            cy = random.randint(top + 10, horizon + 50)
            draw.line([(px + 2, cy), (px + pw - 2, cy + random.randint(-4, 4))], fill=SHADOW, width=1)
        draw.polygon([(px + pw, horizon + 52), (px + pw + 34, horizon + 46), (px + pw + 62, ENV_H - 8), (px + pw + 14, ENV_H - 8)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.2))

    # Staircase climbing left to right
    stair_y = horizon + 60
    for i in range(12):
        sx = 30 + i * 50
        sy = stair_y - i * 12
        draw.rectangle([sx, sy, sx + 55, sy + 8], fill=SAND)
        draw.rectangle([sx, sy + 8, sx + 55, sy + 12], fill=RUST)
        # Step lip highlight
        draw.line([(sx, sy), (sx + 55, sy)], fill=HIGHLIGHT, width=1)
        draw.line([(sx + 2, sy + 9), (sx + 53, sy + 9)], fill=DETAIL_DARK, width=1)
        draw.rectangle([sx + 2, sy + 1, sx + 10, sy + 7], fill=_lerp_color(HIGHLIGHT, SAND, 0.45))
        if i % 2 == 0:
            draw.line([(sx + 8, sy + 1), (sx + 18, sy + 7)], fill=SOOT, width=1)
        draw.polygon([(sx + 55, sy + 10), (sx + 80, sy + 6), (sx + 106, sy + 24), (sx + 68, sy + 24)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.16))

    # Scattered bones/debris
    for _ in range(15):
        bx = random.randint(20, 600)
        by = random.randint(horizon + 50, 340)
        draw.line([(bx, by), (bx + random.randint(3, 8), by - random.randint(1, 4))], fill=BONE, width=1)
    for chain_x in [116, 342, 520]:
        for cy in range(horizon + 8, horizon + 55, 8):
            draw.line([(chain_x, cy), (chain_x + random.randint(-1, 1), cy + 5)], fill=DETAIL_DARK, width=1)
        draw.line([(chain_x, horizon + 56), (chain_x + 18, horizon + 88)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.15), width=1)

    _sand_grain_texture(img, horizon, ENV_H, density=0.10)
    return img


def gen_glasswind_causeway() -> Image.Image:
    img = Image.new("RGB", (ENV_W, ENV_H), MID_BLUE)
    draw = ImageDraw.Draw(img)
    horizon = 160
    bridge_y = 200

    # Stormy slate sky with retained cobalt undertone
    for y in range(horizon):
        t = y / max(1, horizon)
        c = _lerp_color(SHADOW, MID_BLUE, t)
        draw.line([(0, y), (ENV_W - 1, y)], fill=c)

    # Sand wind streaks
    for _ in range(30):
        sx = random.randint(0, ENV_W - 80)
        sy = random.randint(20, horizon - 10)
        length = random.randint(30, 100)
        draw.line([(sx, sy), (sx + length, sy + random.randint(-2, 2))], fill=SAND_LIGHT, width=1)

    _jagged_spires(draw, ENV_W, horizon, count=9)
    _scatter_dark_detail(draw, 0, horizon + 8, ENV_W - 1, bridge_y - 10, 70, DETAIL_DARK)

    # Bridge structure across chasm
    draw.rectangle([0, bridge_y, ENV_W, bridge_y + 20], fill=RUST)
    draw.rectangle([0, bridge_y, ENV_W, bridge_y + 3], fill=BRASS)
    draw.rectangle([0, bridge_y + 3, ENV_W, bridge_y + 8], fill=_lerp_color(HIGHLIGHT, BRASS, 0.3))
    draw.rectangle([0, bridge_y + 14, ENV_W, bridge_y + 20], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.14))
    draw.line([(0, bridge_y + 17), (ENV_W, bridge_y + 17)], fill=DETAIL_DARK, width=1)
    # Bridge rivets/detail
    for rx in range(20, ENV_W, 40):
        draw.ellipse([rx - 2, bridge_y + 8, rx + 2, bridge_y + 12], fill=DARK_RUST)
        if rx + 20 < ENV_W:
            draw.line([(rx + 2, bridge_y + 10), (rx + 18, bridge_y + 10)], fill=DETAIL_DARK, width=1)

    # Cobalt-brass shard hazards
    for gx in range(50, ENV_W - 40, 70):
        shard_h = random.randint(16, 30)
        draw.polygon([(gx, bridge_y - shard_h), (gx + 6, bridge_y), (gx - 6, bridge_y)], fill=TEAL)
        draw.polygon([(gx, bridge_y - shard_h), (gx + 3, bridge_y - shard_h + 6), (gx - 3, bridge_y - shard_h + 6)], fill=HIGHLIGHT)
        draw.line([(gx, bridge_y - shard_h + 2), (gx, bridge_y - 2)], fill=DETAIL_DARK, width=1)

    # Railing posts
    for rx in range(30, ENV_W, 50):
        draw.line([(rx, bridge_y - 30), (rx, bridge_y)], fill=DARK_RUST, width=2)
        draw.rectangle([rx - 3, bridge_y - 32, rx + 3, bridge_y - 28], fill=RUST)
        draw.line([(rx - 1, bridge_y - 31), (rx - 1, bridge_y - 1)], fill=_lerp_color(HIGHLIGHT, BRASS, 0.18), width=1)
        if rx + 50 < ENV_W:
            draw.line([(rx + 3, bridge_y - 25), (rx + 47, bridge_y - 25)], fill=DETAIL_DARK, width=1)
        draw.polygon([(rx + 2, bridge_y + 18), (rx + 26, bridge_y + 18), (rx + 40, bridge_y + 36), (rx + 12, bridge_y + 36)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.2))

    # Void below
    for y in range(bridge_y + 20, ENV_H):
        t = (y - bridge_y - 20) / max(1, ENV_H - bridge_y - 20)
        c = _lerp_color(DARK_RUST, SHADOW, t * 0.8)
        draw.line([(0, y), (ENV_W - 1, y)], fill=c)
    draw.polygon([(0, bridge_y + 20), (ENV_W, bridge_y + 20), (ENV_W, bridge_y + 34), (0, bridge_y + 26)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.35))
    _scatter_dark_detail(draw, 0, bridge_y + 24, ENV_W - 1, ENV_H - 1, 90, SHADOW)

    _sand_grain_texture(img, bridge_y, bridge_y + 20, density=0.06)
    return img


def gen_ember_nave() -> Image.Image:
    img = Image.new("RGB", (ENV_W, ENV_H), SHADOW)
    draw = ImageDraw.Draw(img)

    # Kiln-glow ceiling gradient
    for y in range(80):
        t = y / 80
        c = _lerp_color(RUST, SHADOW, t)
        draw.line([(0, y), (ENV_W - 1, y)], fill=c)

    # Grand pillars
    for px in [40, 160, 440, 560]:
        draw.rectangle([px, 40, px + 30, 290], fill=DARK_RUST)
        draw.rectangle([px + 3, 42, px + 27, 288], fill=_lerp_color(DARK_RUST, RUST, 0.3))
        draw.rectangle([px + 3, 42, px + 8, 288], fill=_lerp_color(RUST, HIGHLIGHT, 0.18))
        draw.rectangle([px + 21, 42, px + 27, 288], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.2))
        draw.rectangle([px + 16, 42, px + 21, 288], fill=_lerp_color(SOOT, DARK_RUST, 0.4))
        draw.line([(px + 24, 42), (px + 24, 288)], fill=DETAIL_DARK, width=1)
        for seam_y in range(60, 280, 22):
            draw.line([(px + 4, seam_y), (px + 26, seam_y)], fill=SOOT, width=1)
        draw.polygon([(px + 30, 290), (px + 44, 290), (px + 54, 320), (px + 38, 320)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.35))
        # Capital
        draw.rectangle([px - 6, 34, px + 36, 42], fill=RUST)
        draw.rectangle([px - 4, 36, px + 34, 38], fill=BRASS)

    # Arena floor of heated rust and ash
    draw.rectangle([0, 290, ENV_W, ENV_H], fill=RUST)
    _sand_grain_texture(img, 290, ENV_H, density=0.06)

    # Molten cracks in floor
    for _ in range(8):
        cx = random.randint(40, 600)
        draw.line([(cx, 290), (cx + random.randint(-20, 20), 290 + random.randint(20, 60))],
                  fill=HIGHLIGHT, width=2)
        draw.line([(cx + 1, 291), (cx + random.randint(-15, 15), 290 + random.randint(15, 50))],
                  fill=BRASS, width=1)

    # Boss pedestal (center)
    draw.rectangle([240, 270, 400, 290], fill=BRASS)
    draw.rectangle([250, 260, 390, 270], fill=HIGHLIGHT)
    draw.rectangle([260, 255, 380, 260], fill=WARM_RUST)
    draw.rectangle([240, 286, 400, 290], fill=_lerp_color(DARK_RUST, DETAIL_DARK, 0.4))
    draw.rectangle([240, 270, 248, 290], fill=_lerp_color(HIGHLIGHT, BRASS, 0.35))
    draw.rectangle([388, 270, 400, 290], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.15))
    draw.line([(246, 288), (394, 288)], fill=DETAIL_DARK, width=1)
    draw.line([(265, 258), (375, 258)], fill=SOOT, width=1)
    draw.polygon([(400, 290), (434, 290), (458, 320), (420, 320)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.25))

    # Ember particles
    for _ in range(40):
        ex = random.randint(30, 610)
        ey = random.randint(60, 260)
        size = random.randint(1, 3)
        c = random.choice([HIGHLIGHT, BRASS, WARM_RUST])
        draw.ellipse([ex, ey, ex + size, ey + size], fill=c)
    for chain_x in [115, 318, 508]:
        for cy in range(26, 120, 9):
            draw.line([(chain_x, cy), (chain_x + random.randint(-1, 1), cy + 5)], fill=DETAIL_DARK, width=1)
    _scatter_dark_detail(draw, 0, 286, ENV_W - 1, ENV_H - 1, 150, SOOT)

    return img


# ═══════════════════════════════════════════════════════════════════
# CHARACTERS  256×512  (segmented, 5-head proportions)
# ═══════════════════════════════════════════════════════════════════

CHAR_W, CHAR_H = 256, 512
# Frame cells: 4 columns × 8 rows of 64×64 cells
CELL = 64
HEAD_H = 12  # ~1/5 of 64px character height


def _draw_body_segment(draw: ImageDraw.ImageDraw, ox: int, oy: int,
                       torso_color: tuple, limb_color: tuple, skin: tuple,
                       pose: dict) -> None:
    """Draw a segmented character at cell origin (ox, oy) within a 64×64 cell.
    pose dict keys: head_tilt, torso_lean, l_arm_angle, r_arm_angle,
                    l_leg_angle, r_leg_angle, squash_y (stretch/squash offset)
    Character uses 5-head proportion (total ~60px tall in cell).
    """
    head_tilt = pose.get("head_tilt", 0)
    torso_lean = pose.get("torso_lean", 0)
    squash = pose.get("squash_y", 0)
    l_arm = pose.get("l_arm_angle", 0)
    r_arm = pose.get("r_arm_angle", 0)
    l_leg = pose.get("l_leg_angle", 0)
    r_leg = pose.get("r_leg_angle", 0)

    # Proportions: head=12, neck=2, torso=18, waist=4, upper_leg=10, lower_leg=10, foot=4 = 60px
    cx = ox + 32 + torso_lean  # center x
    top = oy + 2 + squash

    # Head (proportional: h=12, w ~=head_h*1.2 ≈ 15)
    head_w = 15
    head_cx = cx + head_tilt
    draw.ellipse([head_cx - head_w // 2, top, head_cx + head_w // 2, top + HEAD_H], fill=skin)
    draw.ellipse([head_cx - head_w // 2 + 1, top + 1, head_cx - 2, top + HEAD_H - 2], fill=_lerp_color(skin, HIGHLIGHT, 0.18))
    draw.ellipse([head_cx + 2, top + 1, head_cx + head_w // 2 - 1, top + HEAD_H - 1], fill=SKIN_SHADE)
    # Hair/bandana
    draw.rectangle([head_cx - head_w // 2 - 1, top, head_cx + head_w // 2 + 1, top + 4], fill=RUST)
    draw.line([(head_cx - head_w // 2, top + 1), (head_cx + head_w // 2 - 1, top + 1)], fill=HIGHLIGHT, width=1)
    draw.point((head_cx + head_w // 2 + 1, top + 2), fill=BRASS)
    draw.line([(head_cx - head_w // 2, top + 4), (head_cx + head_w // 2, top + 4)], fill=DETAIL_DARK, width=1)
    # Eyes
    draw.rectangle([head_cx + 2, top + 5, head_cx + 4, top + 7], fill=SHADOW)
    draw.point((head_cx + 3, top + 5), fill=WHITE)
    draw.point((head_cx - 3, top + 7), fill=DETAIL_DARK)

    # Neck
    neck_top = top + HEAD_H
    draw.rectangle([cx - 3, neck_top, cx + 3, neck_top + 2], fill=skin)

    # Torso (shoulders wider than waist: shoulder_w=22, waist_w=14)
    torso_top = neck_top + 2
    shoulder_w = 22
    waist_w = 14
    # Trapezoid torso
    for ty in range(18):
        t = ty / 17
        half_w = int(shoulder_w / 2 + (waist_w / 2 - shoulder_w / 2) * t)
        y = torso_top + ty
        draw.line([(cx - half_w, y), (cx + half_w, y)], fill=torso_color)
    draw.line([(cx - shoulder_w // 2 + 1, torso_top + 1), (cx - shoulder_w // 2 + 1, torso_top + 17)], fill=_lerp_color(HIGHLIGHT, torso_color, 0.35), width=1)
    draw.line([(cx + shoulder_w // 2 - 1, torso_top + 2), (cx + shoulder_w // 2 - 1, torso_top + 17)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.15), width=1)
    draw.line([(cx - 1, torso_top + 1), (cx - 1, torso_top + 17)], fill=DETAIL_DARK, width=1)
    draw.line([(cx - 8, torso_top + 3), (cx + 5, torso_top + 11)], fill=BRASS, width=1)
    draw.line([(cx - 7, torso_top + 5), (cx + 4, torso_top + 13)], fill=DETAIL_DARK, width=1)
    draw.line([(cx - 6, torso_top + 8), (cx + 2, torso_top + 8)], fill=_lerp_color(HIGHLIGHT, WHITE, 0.2), width=1)
    # Belt
    draw.rectangle([cx - waist_w // 2, torso_top + 16, cx + waist_w // 2, torso_top + 20], fill=BRASS)
    draw.line([(cx - waist_w // 2, torso_top + 19), (cx + waist_w // 2, torso_top + 19)], fill=DETAIL_DARK, width=1)

    waist_y = torso_top + 20

    # Arms (from shoulders, hang to past waist — arm length ~24px)
    shoulder_y = torso_top + 2
    arm_length = 24
    arm_w = 4
    for side, angle in [(-1, l_arm), (1, r_arm)]:
        shoulder_x = cx + side * (shoulder_w // 2 - 2)
        end_x = shoulder_x + int(arm_length * 0.3 * math.sin(math.radians(angle)))
        end_y = shoulder_y + int(arm_length * math.cos(math.radians(angle)))
        # Upper arm
        mid_x = (shoulder_x + end_x) // 2
        mid_y = (shoulder_y + end_y) // 2
        draw.line([(shoulder_x, shoulder_y), (mid_x, mid_y)], fill=torso_color, width=arm_w)
        draw.line([(shoulder_x + side, shoulder_y + 1), (mid_x + side, mid_y + 1)], fill=_lerp_color(HIGHLIGHT, torso_color, 0.4), width=1)
        # Forearm
        draw.line([(mid_x, mid_y), (end_x, end_y)], fill=skin, width=arm_w - 1)
        draw.line([(mid_x + side, mid_y + 1), (end_x + side, end_y + 1)], fill=SKIN_SHADE, width=1)
        draw.point((mid_x, mid_y), fill=DETAIL_DARK)
        # Hand
        draw.ellipse([end_x - 2, end_y - 1, end_x + 2, end_y + 3], fill=skin)
        draw.point((end_x, end_y + 1), fill=DETAIL_DARK)

    # Legs
    hip_y = waist_y
    leg_length = 20
    for side, angle in [(-1, l_leg), (1, r_leg)]:
        hip_x = cx + side * 5
        knee_x = hip_x + int(leg_length * 0.5 * math.sin(math.radians(angle)))
        knee_y = hip_y + int(leg_length * 0.5 * math.cos(math.radians(angle * 0.6)))
        foot_x = knee_x + int(leg_length * 0.5 * math.sin(math.radians(angle * 0.3)))
        foot_y = knee_y + int(leg_length * 0.5)
        # Thigh
        draw.line([(hip_x, hip_y), (knee_x, knee_y)], fill=limb_color, width=5)
        draw.line([(hip_x + side, hip_y + 1), (knee_x + side, knee_y + 1)], fill=_lerp_color(HIGHLIGHT, limb_color, 0.3), width=1)
        # Shin
        draw.line([(knee_x, knee_y), (foot_x, foot_y)], fill=limb_color, width=4)
        draw.line([(knee_x + side, knee_y + 1), (foot_x + side, foot_y + 1)], fill=_lerp_color(DETAIL_DARK, SHADOW, 0.1), width=1)
        draw.point((knee_x, knee_y), fill=DETAIL_DARK)
        # Boot
        draw.rectangle([foot_x - 4, foot_y, foot_x + 4, foot_y + 4], fill=DARK_RUST)
        draw.line([(foot_x - 4, foot_y), (foot_x + 2, foot_y)], fill=_lerp_color(HIGHLIGHT, BRASS, 0.2), width=1)
        draw.line([(foot_x - 4, foot_y + 3), (foot_x + 4, foot_y + 3)], fill=DETAIL_DARK, width=1)

    # Cape (flowing from shoulders)
    cape_sway = pose.get("cape_sway", 0)
    cape_pts = [
        (cx - shoulder_w // 2, shoulder_y),
        (cx - shoulder_w // 2 - 4 + cape_sway, waist_y + 10),
        (cx - shoulder_w // 2 + 4 + cape_sway, waist_y + 16),
        (cx - 2, shoulder_y + 6),
    ]
    draw.polygon(cape_pts, fill=BRASS)
    draw.polygon([cape_pts[0], cape_pts[3], ((cape_pts[3][0] + cape_pts[2][0]) // 2, (cape_pts[3][1] + cape_pts[2][1]) // 2), ((cape_pts[0][0] + cape_pts[1][0]) // 2, (cape_pts[0][1] + cape_pts[1][1]) // 2)], fill=_lerp_color(HIGHLIGHT, BRASS, 0.25))
    draw.polygon([((cape_pts[0][0] + cape_pts[1][0]) // 2, (cape_pts[0][1] + cape_pts[1][1]) // 2), cape_pts[1], cape_pts[2], ((cape_pts[3][0] + cape_pts[2][0]) // 2, (cape_pts[3][1] + cape_pts[2][1]) // 2)], fill=_lerp_color(DARK_RUST, DETAIL_DARK, 0.2))
    draw.line([cape_pts[0], cape_pts[1]], fill=HIGHLIGHT, width=1)
    draw.line([cape_pts[3], cape_pts[2]], fill=DETAIL_DARK, width=1)
    draw.line([cape_pts[0], cape_pts[3]], fill=SOOT, width=1)
    draw.line([cape_pts[1], cape_pts[2]], fill=DETAIL_DARK, width=1)


def gen_field_handler_sheet() -> Image.Image:
    """4-column × 8-row sprite sheet with clearer keyed poses for preview export."""
    img = Image.new("RGBA", (CHAR_W, CHAR_H), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    # Row 0: Idle (4 frames with breathing/cape flutter)
    idle_poses = [
        {"head_tilt": 0, "torso_lean": 0, "l_arm_angle": 8, "r_arm_angle": -8, "l_leg_angle": 0, "r_leg_angle": 0, "cape_sway": 0, "squash_y": 0},
        {"head_tilt": 0, "torso_lean": 0, "l_arm_angle": 10, "r_arm_angle": -6, "l_leg_angle": 0, "r_leg_angle": 0, "cape_sway": -2, "squash_y": -1},
        {"head_tilt": 1, "torso_lean": 0, "l_arm_angle": 8, "r_arm_angle": -8, "l_leg_angle": 0, "r_leg_angle": 0, "cape_sway": -3, "squash_y": 0},
        {"head_tilt": -1, "torso_lean": 0, "l_arm_angle": 6, "r_arm_angle": -10, "l_leg_angle": 0, "r_leg_angle": 0, "cape_sway": 1, "squash_y": 1},
    ]
    for i, pose in enumerate(idle_poses):
        _draw_body_segment(draw, i * CELL, 0, TEAL, SAND_DARK, SKIN, pose)

    # Row 1: Walk cycle (4 frames with anticipation/follow-through)
    walk_poses = [
        {"head_tilt": 0, "torso_lean": 2, "l_arm_angle": -25, "r_arm_angle": 25, "l_leg_angle": 20, "r_leg_angle": -20, "cape_sway": -4, "squash_y": 0},
        {"head_tilt": 1, "torso_lean": 1, "l_arm_angle": -10, "r_arm_angle": 10, "l_leg_angle": 5, "r_leg_angle": -5, "cape_sway": -2, "squash_y": -1},
        {"head_tilt": 0, "torso_lean": 2, "l_arm_angle": 25, "r_arm_angle": -25, "l_leg_angle": -20, "r_leg_angle": 20, "cape_sway": -5, "squash_y": 0},
        {"head_tilt": -1, "torso_lean": 1, "l_arm_angle": 10, "r_arm_angle": -10, "l_leg_angle": -5, "r_leg_angle": 5, "cape_sway": -3, "squash_y": 1},
    ]
    for i, pose in enumerate(walk_poses):
        _draw_body_segment(draw, i * CELL, CELL, TEAL, SAND_DARK, SKIN, pose)

    # Row 2: Run cycle (exaggerated with rubber-hose stretch)
    run_poses = [
        {"head_tilt": 2, "torso_lean": 4, "l_arm_angle": -45, "r_arm_angle": 45, "l_leg_angle": 35, "r_leg_angle": -30, "cape_sway": -8, "squash_y": 2},
        {"head_tilt": 1, "torso_lean": 3, "l_arm_angle": -20, "r_arm_angle": 20, "l_leg_angle": 10, "r_leg_angle": -10, "cape_sway": -5, "squash_y": -2},
        {"head_tilt": 2, "torso_lean": 4, "l_arm_angle": 45, "r_arm_angle": -45, "l_leg_angle": -30, "r_leg_angle": 35, "cape_sway": -9, "squash_y": 2},
        {"head_tilt": 1, "torso_lean": 3, "l_arm_angle": 20, "r_arm_angle": -20, "l_leg_angle": -10, "r_leg_angle": 10, "cape_sway": -6, "squash_y": -2},
    ]
    for i, pose in enumerate(run_poses):
        _draw_body_segment(draw, i * CELL, CELL * 2, TEAL, SAND_DARK, SKIN, pose)

    # Row 3-4: Attack combo (3 anticipation frames + 3 swing + 2 follow-through)
    attack_anticipation = [
        {"head_tilt": -3, "torso_lean": -5, "l_arm_angle": 12, "r_arm_angle": -75, "l_leg_angle": -12, "r_leg_angle": 10, "cape_sway": 10, "squash_y": 4},
        {"head_tilt": -5, "torso_lean": -7, "l_arm_angle": 18, "r_arm_angle": -95, "l_leg_angle": -16, "r_leg_angle": 14, "cape_sway": 14, "squash_y": 5},
        {"head_tilt": 5, "torso_lean": 7, "l_arm_angle": -18, "r_arm_angle": 72, "l_leg_angle": 14, "r_leg_angle": -8, "cape_sway": -12, "squash_y": -3},
        {"head_tilt": 6, "torso_lean": 9, "l_arm_angle": -24, "r_arm_angle": 96, "l_leg_angle": 18, "r_leg_angle": -10, "cape_sway": -16, "squash_y": -5},
    ]
    for i, pose in enumerate(attack_anticipation):
        _draw_body_segment(draw, i * CELL, CELL * 3, TEAL, SAND_DARK, SKIN, pose)

    attack_follow = [
        {"head_tilt": 5, "torso_lean": 6, "l_arm_angle": -10, "r_arm_angle": 104, "l_leg_angle": 16, "r_leg_angle": -4, "cape_sway": -12, "squash_y": -3},
        {"head_tilt": 3, "torso_lean": 4, "l_arm_angle": -4, "r_arm_angle": 58, "l_leg_angle": 10, "r_leg_angle": -2, "cape_sway": -8, "squash_y": -1},
        {"head_tilt": 1, "torso_lean": 2, "l_arm_angle": 2, "r_arm_angle": 22, "l_leg_angle": 4, "r_leg_angle": -1, "cape_sway": -3, "squash_y": 1},
        {"head_tilt": 0, "torso_lean": 0, "l_arm_angle": 8, "r_arm_angle": -8, "l_leg_angle": 0, "r_leg_angle": 0, "cape_sway": 0, "squash_y": 0},
    ]
    for i, pose in enumerate(attack_follow):
        _draw_body_segment(draw, i * CELL, CELL * 4, TEAL, SAND_DARK, SKIN, pose)

    # Row 5: Second strike (wider swing)
    strike2 = [
        {"head_tilt": -4, "torso_lean": -6, "l_arm_angle": 28, "r_arm_angle": -82, "l_leg_angle": -14, "r_leg_angle": 12, "cape_sway": 14, "squash_y": 4},
        {"head_tilt": 6, "torso_lean": 10, "l_arm_angle": -28, "r_arm_angle": 108, "l_leg_angle": 22, "r_leg_angle": -12, "cape_sway": -18, "squash_y": -5},
        {"head_tilt": 4, "torso_lean": 5, "l_arm_angle": -8, "r_arm_angle": 64, "l_leg_angle": 10, "r_leg_angle": -5, "cape_sway": -10, "squash_y": 0},
        {"head_tilt": 0, "torso_lean": 0, "l_arm_angle": 8, "r_arm_angle": -8, "l_leg_angle": 0, "r_leg_angle": 0, "cape_sway": 0, "squash_y": 0},
    ]
    for i, pose in enumerate(strike2):
        _draw_body_segment(draw, i * CELL, CELL * 5, TEAL, SAND_DARK, SKIN, pose)

    # Row 6: Third strike (full follow-through with squash)
    strike3 = [
        {"head_tilt": -5, "torso_lean": -8, "l_arm_angle": 36, "r_arm_angle": -94, "l_leg_angle": -18, "r_leg_angle": 16, "cape_sway": 18, "squash_y": 5},
        {"head_tilt": 7, "torso_lean": 11, "l_arm_angle": -32, "r_arm_angle": 112, "l_leg_angle": 26, "r_leg_angle": -14, "cape_sway": -20, "squash_y": -6},
        {"head_tilt": 5, "torso_lean": 7, "l_arm_angle": -14, "r_arm_angle": 72, "l_leg_angle": 14, "r_leg_angle": -7, "cape_sway": -12, "squash_y": 1},
        {"head_tilt": 1, "torso_lean": 2, "l_arm_angle": 5, "r_arm_angle": -5, "l_leg_angle": 2, "r_leg_angle": -2, "cape_sway": -2, "squash_y": 3},
    ]
    for i, pose in enumerate(strike3):
        _draw_body_segment(draw, i * CELL, CELL * 6, TEAL, SAND_DARK, SKIN, pose)

    # Row 7: Jump (anticipation, ascent, peak, descent)
    jump_poses = [
        {"head_tilt": -1, "torso_lean": -2, "l_arm_angle": 14, "r_arm_angle": -14, "l_leg_angle": 20, "r_leg_angle": 20, "cape_sway": 4, "squash_y": 5},
        {"head_tilt": 1, "torso_lean": -3, "l_arm_angle": -36, "r_arm_angle": 36, "l_leg_angle": -26, "r_leg_angle": -24, "cape_sway": 10, "squash_y": -5},
        {"head_tilt": 2, "torso_lean": 0, "l_arm_angle": -18, "r_arm_angle": 18, "l_leg_angle": -14, "r_leg_angle": 12, "cape_sway": 12, "squash_y": -4},
        {"head_tilt": 0, "torso_lean": 3, "l_arm_angle": 24, "r_arm_angle": -24, "l_leg_angle": 28, "r_leg_angle": 26, "cape_sway": -6, "squash_y": 4},
    ]
    for i, pose in enumerate(jump_poses):
        _draw_body_segment(draw, i * CELL, CELL * 7, TEAL, SAND_DARK, SKIN, pose)

    return img


FIELD_HANDLER_ANIMATIONS = {
    "idle": {
        "loop": True,
        "frames": [
            {"row": 0, "col": 0, "phase": "move"},
            {"row": 0, "col": 1, "phase": "move"},
            {"row": 0, "col": 2, "phase": "move"},
            {"row": 0, "col": 3, "phase": "move"},
        ],
    },
    "walk": {
        "loop": True,
        "frames": [
            {"row": 1, "col": 0, "phase": "move"},
            {"row": 1, "col": 1, "phase": "move"},
            {"row": 1, "col": 2, "phase": "move"},
            {"row": 1, "col": 3, "phase": "move"},
        ],
    },
    "run": {
        "loop": True,
        "frames": [
            {"row": 2, "col": 0, "phase": "move"},
            {"row": 2, "col": 1, "phase": "move"},
            {"row": 2, "col": 2, "phase": "move"},
            {"row": 2, "col": 3, "phase": "move"},
        ],
    },
    "combo_1": {
        "loop": True,
        "frames": [
            {"row": 3, "col": 0, "phase": "hold"},
            {"row": 3, "col": 1, "phase": "hold"},
            {"row": 3, "col": 2, "phase": "move"},
            {"row": 3, "col": 3, "phase": "move"},
            {"row": 4, "col": 0, "phase": "hold"},
            {"row": 4, "col": 1, "phase": "hold"},
            {"row": 4, "col": 2, "phase": "move"},
            {"row": 4, "col": 3, "phase": "move"},
        ],
    },
    "combo_2": {
        "loop": True,
        "frames": [
            {"row": 5, "col": 0, "phase": "hold"},
            {"row": 5, "col": 1, "phase": "move"},
            {"row": 5, "col": 2, "phase": "hold"},
            {"row": 5, "col": 3, "phase": "move"},
        ],
    },
    "combo_3": {
        "loop": True,
        "frames": [
            {"row": 6, "col": 0, "phase": "hold"},
            {"row": 6, "col": 1, "phase": "move"},
            {"row": 6, "col": 2, "phase": "hold"},
            {"row": 6, "col": 3, "phase": "move"},
        ],
    },
    "jump": {
        "loop": True,
        "frames": [
            {"row": 7, "col": 0, "phase": "hold"},
            {"row": 7, "col": 1, "phase": "move"},
            {"row": 7, "col": 2, "phase": "move"},
            {"row": 7, "col": 3, "phase": "hold"},
        ],
    },
}


def _field_handler_frame(sheet: Image.Image, row: int, col: int) -> Image.Image:
    box = (col * CELL, row * CELL, (col + 1) * CELL, (row + 1) * CELL)
    return sheet.crop(box)


def _preview_canvas(frame: Image.Image) -> Image.Image:
    matte = Image.new("RGBA", (CELL * 2, CELL * 2), SKY_TOP + (255,))
    draw = ImageDraw.Draw(matte)
    draw.rectangle([0, CELL + 28, CELL * 2, CELL * 2], fill=_lerp_color(SOOT, SHADOW, 0.3) + (255,))
    draw.line([(0, CELL + 24), (CELL * 2, CELL + 24)], fill=_lerp_color(BRASS, SHADOW, 0.75) + (255,), width=2)
    sprite = frame.resize((CELL * 2, CELL * 2), Image.NEAREST)
    matte.alpha_composite(sprite, (0, 0))
    return matte.convert("P", palette=Image.ADAPTIVE, colors=PIXEL_ART_COLOR_COUNT)


def _expanded_animation_frames(sheet: Image.Image, animation_name: str) -> tuple[list[Image.Image], list[dict]]:
    spec = FIELD_HANDLER_ANIMATIONS[animation_name]
    frames: list[Image.Image] = []
    playback: list[dict] = []
    for entry in spec["frames"]:
        repeats = ANIMATION_HOLD_REPEATS if entry["phase"] == "hold" else ANIMATION_MOVE_REPEATS
        source = _field_handler_frame(sheet, entry["row"], entry["col"])
        preview = _preview_canvas(source)
        for _ in range(repeats):
            frames.append(preview.copy())
            playback.append({
                "row": entry["row"],
                "col": entry["col"],
                "phase": entry["phase"],
                "duration_ms": ANIMATION_FRAME_MS,
            })
    return frames, playback


def export_field_handler_previews(sheet: Image.Image) -> None:
    preview_root = OUT_ROOT / "previews"
    preview_root.mkdir(parents=True, exist_ok=True)
    metadata = {
        "sheet": "aridfeihth/production_raw/actors/field_handler_sheet.png",
        "frame_size": [CELL, CELL],
        "preview_size": [CELL * 2, CELL * 2],
        "timing_rule": {
            "hold_repeats": ANIMATION_HOLD_REPEATS,
            "move_repeats": ANIMATION_MOVE_REPEATS,
            "frame_duration_ms": ANIMATION_FRAME_MS,
            "ratio": "2:1 hold-to-move playback frames",
        },
        "animations": {},
    }
    for name in FIELD_HANDLER_ANIMATIONS:
        frames, playback = _expanded_animation_frames(sheet, name)
        gif_path = preview_root / f"field_handler_{name}.gif"
        frames[0].save(
            str(gif_path),
            save_all=True,
            append_images=frames[1:],
            duration=[frame["duration_ms"] for frame in playback],
            loop=0,
            disposal=2,
        )
        metadata["animations"][name] = {
            "preview": f"aridfeihth/production_raw/previews/field_handler_{name}.gif",
            "loop": FIELD_HANDLER_ANIMATIONS[name]["loop"],
            "playback_frames": playback,
        }
    metadata_path = preview_root / "field_handler_animations.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════
# PETS  128×128  (chibi — large head, compact body, half human size)
# ═══════════════════════════════════════════════════════════════════

PET_W, PET_H = 128, 128
PET_CELL = 32  # 4×4 grid of 32px cells


def _draw_chibi_pet(draw: ImageDraw.ImageDraw, ox: int, oy: int,
                    body: tuple, accent: tuple, eye: tuple,
                    shape: str, pose_idx: int) -> None:
    """Draw a chibi pet in a 32×32 cell. Head = ~60% of body height. Distinct silhouette."""
    bob = (pose_idx % 2) * 2
    cx = ox + 16
    base_y = oy + 28 - bob

    if shape == "lizard":
        # Large expressive head (chibi proportions)
        head_r = 8
        draw.ellipse([cx - head_r, base_y - 20, cx + head_r, base_y - 4], fill=body)
        # Big eye (anime style)
        draw.ellipse([cx + 1, base_y - 16, cx + 6, base_y - 10], fill=WHITE)
        draw.ellipse([cx + 2, base_y - 15, cx + 5, base_y - 11], fill=eye)
        draw.point((cx + 3, base_y - 14), fill=WHITE)  # eye glint
        # Compact body
        draw.ellipse([cx - 5, base_y - 6, cx + 5, base_y + 2], fill=body)
        draw.line([(cx - 4, base_y - 9), (cx + 4, base_y - 9)], fill=DETAIL_DARK, width=1)
        draw.point((cx - 2, base_y - 13), fill=DETAIL_DARK)
        draw.point((cx, base_y - 11), fill=DETAIL_DARK)
        # Tail (distinct silhouette: curling)
        tail_sway = 3 if pose_idx % 2 == 0 else -2
        draw.line([(cx - 5, base_y - 2), (cx - 10 + tail_sway, base_y + 4)], fill=accent, width=2)
        draw.line([(cx - 10 + tail_sway, base_y + 4), (cx - 8 + tail_sway, base_y + 6)], fill=accent, width=2)
        # Tiny legs
        leg_spread = 2 + pose_idx % 2
        draw.line([(cx - 3, base_y + 1), (cx - 3 - leg_spread, base_y + 5)], fill=body, width=2)
        draw.line([(cx + 3, base_y + 1), (cx + 3 + leg_spread, base_y + 5)], fill=body, width=2)
        # Fin crest (silhouette detail)
        draw.polygon([(cx - 2, base_y - 20), (cx, base_y - 24), (cx + 3, base_y - 18)], fill=accent)

    elif shape == "spider":
        # Big round head/body merge (chibi spider)
        r = 9
        draw.ellipse([cx - r, base_y - 18, cx + r, base_y], fill=body)
        # Multiple eyes (distinct)
        for ex, ey in [(cx - 3, base_y - 12), (cx + 3, base_y - 12), (cx - 1, base_y - 9), (cx + 1, base_y - 9)]:
            draw.ellipse([ex - 1, ey - 1, ex + 1, ey + 1], fill=eye)
        draw.line([(cx - 4, base_y - 5), (cx + 4, base_y - 5)], fill=DETAIL_DARK, width=1)
        draw.line([(cx - 2, base_y - 15), (cx + 2, base_y - 3)], fill=SOOT, width=1)
        draw.line([(cx + 2, base_y - 15), (cx - 2, base_y - 3)], fill=SOOT, width=1)
        # Legs (splayed for silhouette)
        leg_wave = 1 if pose_idx % 2 == 0 else -1
        for i in range(4):
            angle_l = -30 - i * 18 + leg_wave * 5
            angle_r = 30 + i * 18 - leg_wave * 5
            l_len = 10 + i * 2
            lx = cx - r + int(l_len * 0.4 * math.sin(math.radians(angle_l)))
            ly = base_y - 4 + i * 3 + int(l_len * 0.3 * math.cos(math.radians(angle_l)))
            draw.line([(cx - r + 2, base_y - 10 + i * 3), (lx, ly)], fill=accent, width=2)
            rx = cx + r + int(l_len * 0.4 * math.sin(math.radians(angle_r)))
            ry = base_y - 4 + i * 3 + int(l_len * 0.3 * math.cos(math.radians(angle_r)))
            draw.line([(cx + r - 2, base_y - 10 + i * 3), (rx, ry)], fill=accent, width=2)
        # Mandible detail
        draw.line([(cx - 2, base_y), (cx - 4, base_y + 3)], fill=accent, width=1)
        draw.line([(cx + 2, base_y), (cx + 4, base_y + 3)], fill=accent, width=1)
        draw.point((cx, base_y - 2), fill=DETAIL_DARK)

    elif shape == "ram":
        # Big head with horns (distinct silhouette)
        head_r = 9
        draw.ellipse([cx - head_r, base_y - 22, cx + head_r, base_y - 4], fill=body)
        # Big eye
        draw.ellipse([cx + 2, base_y - 16, cx + 7, base_y - 10], fill=WHITE)
        draw.ellipse([cx + 3, base_y - 15, cx + 6, base_y - 11], fill=eye)
        draw.point((cx + 4, base_y - 14), fill=WHITE)
        # Curling horns (signature silhouette)
        for side in [-1, 1]:
            hx = cx + side * head_r
            draw.arc([hx - 5, base_y - 24, hx + 5, base_y - 14], start=180 if side < 0 else 0,
                     end=360 if side < 0 else 180, fill=accent, width=3)
            draw.arc([hx - 4, base_y - 22, hx + 4, base_y - 15], start=180 if side < 0 else 0,
                     end=360 if side < 0 else 180, fill=DETAIL_DARK, width=1)
        # Compact body
        draw.ellipse([cx - 6, base_y - 6, cx + 6, base_y + 2], fill=body)
        draw.line([(cx - 3, base_y - 10), (cx + 2, base_y - 7)], fill=DETAIL_DARK, width=1)
        draw.line([(cx - 5, base_y - 2), (cx + 5, base_y - 2)], fill=SOOT, width=1)
        # Sturdy legs
        draw.rectangle([cx - 5, base_y + 1, cx - 2, base_y + 6], fill=body)
        draw.rectangle([cx + 2, base_y + 1, cx + 5, base_y + 6], fill=body)
        # Hooves
        draw.rectangle([cx - 6, base_y + 5, cx - 1, base_y + 7], fill=DARK_RUST)
        draw.rectangle([cx + 1, base_y + 5, cx + 6, base_y + 7], fill=DARK_RUST)
        # Tail tuft
        draw.ellipse([cx - 8, base_y - 4, cx - 5, base_y], fill=accent)


def _gen_pet_sheet(body: tuple, accent: tuple, eye: tuple, shape: str) -> Image.Image:
    """4×4 grid: row 0 idle, row 1 walk, row 2 attack/ability, row 3 rescue pose."""
    img = Image.new("RGBA", (PET_W, PET_H), TRANSPARENT)
    draw = ImageDraw.Draw(img)
    for row in range(4):
        for col in range(4):
            _draw_chibi_pet(draw, col * PET_CELL, row * PET_CELL, body, accent, eye, shape, col + row * 4)
    return img


def gen_mirror_newt_sheet() -> Image.Image:
    return _gen_pet_sheet(TEAL, HIGHLIGHT, BRASS, "lizard")


def gen_latch_spider_sheet() -> Image.Image:
    return _gen_pet_sheet(DARK_RUST, RUST, HIGHLIGHT, "spider")


def gen_salt_ram_sheet() -> Image.Image:
    return _gen_pet_sheet(SAND, BRASS, SHADOW, "ram")


# ═══════════════════════════════════════════════════════════════════
# FX  256×64
# ═══════════════════════════════════════════════════════════════════

def gen_bond_weave_fx() -> Image.Image:
    """8-frame bond weave effect strip (32px per frame in 256×64)."""
    img = Image.new("RGBA", (256, 64), TRANSPARENT)
    draw = ImageDraw.Draw(img)
    for frame in range(8):
        ox = frame * 32
        cx, cy = ox + 16, 32
        t = frame / 7.0
        outer_r = int(4 + 12 * t)
        inner_r = max(1, outer_r - 4)
        # Outer ring
        draw.ellipse([cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r], outline=TEAL, width=2)
        if frame > 1:
            draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], outline=HIGHLIGHT, width=1)
            draw.ellipse([cx - max(1, inner_r - 2), cy - max(1, inner_r - 2), cx + max(1, inner_r - 2), cy + max(1, inner_r - 2)], outline=DETAIL_DARK, width=1)
        if frame > 3:
            # Expanding rays
            for angle in range(0, 360, 45):
                ex = cx + int(outer_r * 1.3 * math.cos(math.radians(angle + frame * 15)))
                ey = cy + int(outer_r * 1.3 * math.sin(math.radians(angle + frame * 15)))
                draw.line([(cx, cy), (ex, ey)], fill=BRASS, width=1)
        # Sparks
        for _ in range(frame + 2):
            sx = cx + random.randint(-outer_r - 2, outer_r + 2)
            sy = cy + random.randint(-outer_r - 2, outer_r + 2)
            draw.point((max(ox, min(ox + 31, sx)), max(0, min(63, sy))), fill=HIGHLIGHT)
        # Fade on last frames
        if frame >= 6:
            draw.ellipse([cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r], outline=SAND, width=1)
    return img


# ═══════════════════════════════════════════════════════════════════
# HUD  320×80
# ═══════════════════════════════════════════════════════════════════

def gen_hud_pack() -> Image.Image:
    """HUD elements: HP bar, bond tension, weave charge, pet slots, milestone frame."""
    img = Image.new("RGBA", (320, 80), TRANSPARENT)
    draw = ImageDraw.Draw(img)
    # HP bar (top row)
    draw.rectangle([4, 4, 154, 18], outline=SHADOW, fill=DARK_RUST, width=2)
    draw.rectangle([6, 6, 100, 16], fill=RUST)
    draw.rectangle([6, 6, 60, 10], fill=WARM_RUST)  # glossy highlight
    for tick_x in range(24, 148, 22):
        draw.line([(tick_x, 6), (tick_x, 16)], fill=DETAIL_DARK, width=1)
    # Bond tension meter
    draw.rectangle([164, 4, 314, 18], outline=SHADOW, fill=SHADOW, width=2)
    draw.rectangle([166, 6, 260, 16], fill=BRASS)
    draw.rectangle([166, 6, 260, 10], fill=HIGHLIGHT)  # glossy
    for tick_x in range(182, 308, 22):
        draw.line([(tick_x, 6), (tick_x, 16)], fill=DETAIL_DARK, width=1)
    # Weave charge ring keeps the cobalt accent alive inside the rust-heavy HUD
    draw.ellipse([8, 30, 58, 76], outline=TEAL, width=3)
    draw.arc([12, 34, 54, 72], start=-90, end=180, fill=HIGHLIGHT, width=2)
    # Center diamond
    draw.polygon([(33, 36), (45, 53), (33, 70), (21, 53)], outline=BRASS, fill=SHADOW)
    draw.line([(26, 40), (40, 66)], fill=DETAIL_DARK, width=1)
    draw.line([(40, 40), (26, 66)], fill=DETAIL_DARK, width=1)
    # Pet slots (4)
    slot_specs = [
        (RUST, "burst"),
        (TEAL, "chorus"),
        (SAND, "crest"),
        (HIGHLIGHT, "key"),
    ]
    for i, (sc, lane) in enumerate(slot_specs):
        sx = 70 + i * 50
        draw.rectangle([sx, 30, sx + 40, 62], outline=SHADOW, fill=sc, width=2)
        draw.rectangle([sx + 3, 33, sx + 37, 59], fill=_lerp_color(sc, SHADOW, 0.5))
        draw.line([(sx + 6, 36), (sx + 34, 36)], fill=DETAIL_DARK, width=1)
        draw.line([(sx + 6, 56), (sx + 34, 56)], fill=SOOT, width=1)
        _draw_lane_glyph(draw, lane, sx + 12, 40, _lerp_color(HIGHLIGHT, WHITE, 0.2) if lane != "chorus" else WHITE)
        # Lane label bar
        draw.rectangle([sx, 62, sx + 40, 70], fill=SHADOW)
        draw.line([(sx + 4, 66), (sx + 36, 66)], fill=_lerp_color(sc, SHADOW, 0.2), width=1)
    # Milestone frame (right)
    draw.rectangle([270, 26, 316, 76], outline=BRASS, fill=MID_BLUE, width=2)
    draw.rectangle([274, 30, 312, 72], outline=SHADOW, fill=_lerp_color(MID_BLUE, SHADOW, 0.3))
    for mark_y in range(34, 71, 8):
        draw.line([(278, mark_y), (284, mark_y)], fill=DETAIL_DARK, width=1)
        draw.line([(302, mark_y), (308, mark_y)], fill=DETAIL_DARK, width=1)
    draw.rectangle([288, 42, 298, 60], outline=BRASS, fill=DETAIL_DARK, width=1)
    return img


# ═══════════════════════════════════════════════════════════════════
# AUDIO  – Hijaz-scale violin/brass/percussion WAV synthesis
# ═══════════════════════════════════════════════════════════════════

SAMPLE_RATE = 22050
BIT_DEPTH = 32


def _sine(freq: float, t: float, amplitude: float = 0.3) -> float:
    return amplitude * math.sin(2 * math.pi * freq * t)


def _sawtooth(freq: float, t: float, amplitude: float = 0.15) -> float:
    """Brass-like sawtooth wave."""
    phase = (freq * t) % 1.0
    return amplitude * (2.0 * phase - 1.0)


def _violin_tone(freq: float, t: float, amplitude: float = 0.25) -> float:
    """Bowed string: fundamental + odd harmonics with vibrato."""
    vibrato = 5.5 * math.sin(2 * math.pi * 5.2 * t)
    f = freq + vibrato
    val = 0.0
    val += 1.0 * math.sin(2 * math.pi * f * t)
    val += 0.5 * math.sin(2 * math.pi * f * 2 * t)
    val += 0.25 * math.sin(2 * math.pi * f * 3 * t)
    val += 0.12 * math.sin(2 * math.pi * f * 5 * t)
    return amplitude * val / 1.87


def _percussion_hit(t: float, attack: float = 0.005, decay: float = 0.15) -> float:
    """Envelope for percussion."""
    if t < attack:
        return t / attack
    return max(0.0, 1.0 - (t - attack) / decay)


def _kick(t: float) -> float:
    freq = 120 * max(0.3, 1.0 - t * 6)
    return 0.4 * math.sin(2 * math.pi * freq * t) * _percussion_hit(t, 0.003, 0.2)


def _snare(t: float) -> float:
    noise = random.uniform(-1, 1)
    return 0.2 * noise * _percussion_hit(t, 0.002, 0.1)


def _drone_tone(freq: float, t: float, amplitude: float = 0.18) -> float:
    return amplitude * (
        0.7 * math.sin(2 * math.pi * freq * t)
        + 0.2 * math.sin(2 * math.pi * freq * 0.5 * t)
        + 0.1 * math.sin(2 * math.pi * freq * 1.5 * t)
    )


def _bell_stinger(freq: float, t: float, decay: float = 1.7, amplitude: float = 0.22) -> float:
    env = math.exp(-t / decay)
    return env * amplitude * (
        math.sin(2 * math.pi * freq * t)
        + 0.4 * math.sin(2 * math.pi * freq * 2.01 * t)
        + 0.2 * math.sin(2 * math.pi * freq * 3.97 * t)
    )


def _metal_scrape(freq: float, t: float, amplitude: float = 0.12) -> float:
    env = max(0.0, 1.0 - t / 0.28)
    return env * amplitude * (random.uniform(-1, 1) * 0.6 + math.sin(2 * math.pi * freq * t) * 0.4)


def _clamp_sample(value: float) -> int:
    return max(-(2**31) + 1, min((2**31) - 1, int(value * ((2**31) - 1))))


def gen_audio_theme() -> bytes:
    """Generate a short (~8s) frontier ritual loop.

    Hijaz scale (from D): D Eb F# G A Bb C# D
    Pattern: violin melody + brass pad + low drone + frame drum + ritual bell/scrape stingers
    """
    duration = 8.0
    n_samples = int(SAMPLE_RATE * duration)

    # Hijaz scale frequencies from D4
    D4 = 293.66
    hijaz_intervals = [0, 1, 4, 5, 7, 8, 11, 12]  # semitones: D Eb F# G A Bb C# D
    scale = [D4 * (2 ** (s / 12.0)) for s in hijaz_intervals]

    # Melody sequence (violin) — 16 notes, each 0.5s
    melody_notes = [0, 2, 3, 4, 3, 2, 5, 4, 6, 7, 6, 5, 3, 2, 1, 0]
    note_dur = 0.5
    # Brass pad — sustained chord tones
    brass_notes = [0, 2, 4]  # D, F#, A (major triad in Hijaz)

    # Darbuka pattern (Middle-Eastern frame drum): Dum-tek-ka-tek per beat (0.5s)
    # Dum at beat start, tek at 0.25s, ka at 0.375s
    beat_dur = 0.5

    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        val = 0.0

        # ── Violin melody ──
        note_idx = int(t / note_dur) % len(melody_notes)
        note_t = t - (int(t / note_dur) * note_dur)
        freq = scale[melody_notes[note_idx] % len(scale)]
        env = min(1.0, note_t / 0.05) * max(0.0, 1.0 - max(0.0, note_t - 0.4) / 0.1)
        val += _violin_tone(freq, t, 0.28) * env

        # ── Brass pad ──
        for bi in brass_notes:
            bf = scale[bi % len(scale)] / 2  # one octave lower
            val += _sawtooth(bf, t, 0.06)

        # ── Low ash drone ──
        val += _drone_tone(D4 / 4, t, 0.14)
        val += _drone_tone(scale[4] / 4, t, 0.05)

        # ── Darbuka pattern ──
        beat_t = t % beat_dur
        if beat_t < 0.15:
            val += _kick(beat_t) * 0.7
        elif 0.25 <= beat_t < 0.35:
            val += _snare(beat_t - 0.25) * 0.5
        elif 0.375 <= beat_t < 0.45:
            val += _snare(beat_t - 0.375) * 0.3

        # ── Deep kick on downbeat ──
        bar_t = t % (beat_dur * 4)
        if bar_t < 0.2:
            val += _kick(bar_t) * 0.5

        # ── Large percussion accent every 2 bars ──
        accent_t = t % (beat_dur * 8)
        if accent_t < 0.3:
            val += _kick(accent_t) * 0.6
            if accent_t < 0.08:
                val += 0.15 * math.sin(2 * math.pi * 200 * accent_t) * (1.0 - accent_t / 0.08)

        # ── Room-like stingers embedded in loop ──
        bell_cycle = t % 4.0
        if bell_cycle < 1.4:
            bell_freq = 440.0 if int(t / 4.0) % 2 == 0 else 329.63
            val += _bell_stinger(bell_freq, bell_cycle, amplitude=0.08)

        scrape_cycle = (t + 0.5) % 2.0
        if scrape_cycle < 0.18:
            val += _metal_scrape(180.0, scrape_cycle, amplitude=0.08)

        samples.append(_clamp_sample(val))

    return struct.pack(f"<{len(samples)}i", *samples)


def write_wav(path: Path, pcm_data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(4)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

IMAGE_GENERATORS = {
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

AUDIO_OUTPUTS = {
    "audio/aridfeihth_theme_loop.wav": gen_audio_theme,
}


def main() -> None:
    print("Generating production assets...\n")
    for rel_path, gen_fn in IMAGE_GENERATORS.items():
        out_path = OUT_ROOT / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img = _finalize_pixel_art(gen_fn())
        img.save(str(out_path))
        print(f"  [IMG] {out_path.relative_to(WORKSPACE)}  ({img.width}x{img.height})")
        if rel_path == "actors/field_handler_sheet.png":
            export_field_handler_previews(img)
            print("  [GIF] aridfeihth/production_raw/previews/field_handler_*.gif")
            print("  [JSON] aridfeihth/production_raw/previews/field_handler_animations.json")

    for rel_path, gen_fn in AUDIO_OUTPUTS.items():
        out_path = OUT_ROOT / rel_path
        pcm = gen_fn()
        write_wav(out_path, pcm)
        size_kb = out_path.stat().st_size / 1024
        print(f"  [WAV] {out_path.relative_to(WORKSPACE)}  ({size_kb:.0f} KB)")

    total = len(IMAGE_GENERATORS) + len(AUDIO_OUTPUTS)
    print(f"\n  {total} production assets generated under aridfeihth/production_raw/")


if __name__ == "__main__":
    main()
