"""Generate 64×64 placeholder pixel-art assets for aridfeihth vertical slice.

Desert wasteland-pirate metroidvania palette:
  - Dry cobalt sky:   #1a2744
  - Salt brass:       #c6a84b
  - Ember rust:       #8b3a1e
  - Bone sand:        #d4c098
  - Deep shadow:      #0f1520
  - Teal accent:      #3a7a7a
  - Hot highlight:    #e8c25c
"""
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

WORKSPACE = Path(__file__).resolve().parents[2]
OUT_ROOT = WORKSPACE / "aridfeihth" / "production_raw"

# Palette
SKY = (0x1A, 0x27, 0x44)
BRASS = (0xC6, 0xA8, 0x4B)
RUST = (0x8B, 0x3A, 0x1E)
SAND = (0xD4, 0xC0, 0x98)
SHADOW = (0x0F, 0x15, 0x20)
TEAL = (0x3A, 0x7A, 0x7A)
HIGHLIGHT = (0xE8, 0xC2, 0x5C)
DARK_RUST = (0x5C, 0x24, 0x12)
BONE = (0xE2, 0xD5, 0xB0)
MID_BLUE = (0x2A, 0x3A, 0x5C)

SIZE = 64
random.seed(42)


def _dither(draw: ImageDraw.ImageDraw, x: int, y: int, c1: tuple, c2: tuple) -> None:
    draw.point((x, y), fill=c1 if (x + y) % 2 == 0 else c2)


def _noise_fill(draw: ImageDraw.ImageDraw, y_start: int, y_end: int, base: tuple, alt: tuple, density: float = 0.3) -> None:
    for y in range(y_start, y_end):
        for x in range(SIZE):
            if random.random() < density:
                draw.point((x, y), fill=alt)
            else:
                draw.point((x, y), fill=base)


# ── Backdrops (environment rooms) ──────────────────────────────────

def gen_latchspire_refuge() -> Image.Image:
    """Safe room: tower refuge in sand dunes under cobalt sky."""
    img = Image.new("RGBA", (SIZE, SIZE), SKY)
    draw = ImageDraw.Draw(img)
    # Sky gradient
    for y in range(32):
        r = SKY[0] + (MID_BLUE[0] - SKY[0]) * y // 32
        g = SKY[1] + (MID_BLUE[1] - SKY[1]) * y // 32
        b = SKY[2] + (MID_BLUE[2] - SKY[2]) * y // 32
        draw.line([(0, y), (63, y)], fill=(r, g, b))
    # Sand dune ground
    _noise_fill(draw, 42, 64, SAND, BRASS, 0.25)
    # Tower structure
    draw.rectangle([24, 14, 39, 41], fill=RUST)
    draw.rectangle([26, 16, 37, 39], fill=DARK_RUST)
    # Tower windows
    draw.rectangle([29, 20, 31, 22], fill=HIGHLIGHT)
    draw.rectangle([33, 20, 35, 22], fill=HIGHLIGHT)
    draw.rectangle([29, 28, 31, 30], fill=TEAL)
    draw.rectangle([33, 28, 35, 30], fill=TEAL)
    # Spire top
    draw.polygon([(24, 14), (32, 6), (39, 14)], fill=BRASS)
    draw.point((32, 5), fill=HIGHLIGHT)
    # Flag
    draw.line([(32, 5), (32, 2)], fill=SHADOW)
    draw.rectangle([33, 2, 37, 4], fill=RUST)
    # Dune contour
    for x in range(64):
        h = 42 + int(3 * ((x / 64) ** 2 - 0.5))
        draw.point((x, h), fill=BRASS)
    return img


def gen_choir_stair() -> Image.Image:
    """Encounter room: crumbling staircase rising through desert ruins."""
    img = Image.new("RGBA", (SIZE, SIZE), SKY)
    draw = ImageDraw.Draw(img)
    # Sky
    for y in range(28):
        draw.line([(0, y), (63, y)], fill=SKY)
    # Background ruin pillars
    for px in [8, 22, 50]:
        draw.rectangle([px, 12, px + 4, 40], fill=DARK_RUST)
        draw.rectangle([px - 1, 10, px + 5, 12], fill=RUST)
    # Staircase
    for i in range(6):
        sx = 4 + i * 10
        sy = 44 - i * 4
        draw.rectangle([sx, sy, sx + 12, sy + 3], fill=SAND)
        draw.rectangle([sx, sy + 3, sx + 12, sy + 4], fill=RUST)
    # Ground
    _noise_fill(draw, 48, 64, RUST, DARK_RUST, 0.35)
    # Scattered bones/debris
    for _ in range(6):
        bx = random.randint(2, 60)
        by = random.randint(49, 62)
        draw.line([(bx, by), (bx + 2, by - 1)], fill=BONE)
    return img


def gen_glasswind_causeway() -> Image.Image:
    """Hazard room: sand-blasted bridge with glass shards."""
    img = Image.new("RGBA", (SIZE, SIZE), MID_BLUE)
    draw = ImageDraw.Draw(img)
    # Darker sky — storm
    for y in range(20):
        c = tuple(max(0, v - y) for v in MID_BLUE)
        draw.line([(0, y), (63, y)], fill=c)
    # Sand wind streaks
    for _ in range(10):
        sx = random.randint(0, 50)
        sy = random.randint(5, 30)
        draw.line([(sx, sy), (sx + random.randint(6, 14), sy)], fill=SAND)
    # Bridge
    draw.rectangle([0, 36, 63, 42], fill=RUST)
    draw.rectangle([0, 36, 63, 37], fill=BRASS)
    # Glass shard hazards on bridge
    for gx in [12, 28, 44, 56]:
        draw.polygon([(gx, 33), (gx + 2, 36), (gx - 2, 36)], fill=TEAL)
        draw.point((gx, 33), fill=HIGHLIGHT)
    # Void below bridge
    _noise_fill(draw, 43, 64, SHADOW, DARK_RUST, 0.2)
    # Railing posts
    for rx in range(4, 60, 12):
        draw.line([(rx, 30), (rx, 36)], fill=DARK_RUST)
    return img


def gen_ember_nave() -> Image.Image:
    """Boss arena: volcanic nave with molten floor edges."""
    img = Image.new("RGBA", (SIZE, SIZE), SHADOW)
    draw = ImageDraw.Draw(img)
    # Magma glow ceiling
    for y in range(12):
        r = SHADOW[0] + (RUST[0] - SHADOW[0]) * y // 12
        g = SHADOW[1] + (RUST[1] - SHADOW[1]) * y // 12
        b = SHADOW[2] + (RUST[2] - SHADOW[2]) * y // 12
        draw.line([(0, y), (63, y)], fill=(r, g, b))
    # Stone pillars
    for px in [6, 52]:
        draw.rectangle([px, 8, px + 6, 48], fill=DARK_RUST)
        draw.rectangle([px + 1, 6, px + 5, 8], fill=RUST)
    # Arena floor
    draw.rectangle([0, 48, 63, 63], fill=RUST)
    _noise_fill(draw, 48, 64, RUST, DARK_RUST, 0.3)
    # Molten edge cracks
    for ex in range(0, 64, 8):
        draw.line([(ex, 48), (ex + 3, 50)], fill=HIGHLIGHT)
        draw.line([(ex + 3, 50), (ex + 6, 48)], fill=BRASS)
    # Boss pedestal center
    draw.rectangle([24, 44, 39, 48], fill=BRASS)
    draw.rectangle([26, 42, 37, 44], fill=HIGHLIGHT)
    # Ember particles
    for _ in range(8):
        ex = random.randint(10, 54)
        ey = random.randint(14, 42)
        draw.point((ex, ey), fill=HIGHLIGHT)
    return img


# ── Character/pet sprite sheets ───────────────────────────────────

def gen_field_handler_sheet() -> Image.Image:
    """Player character: 4-frame idle strip (16×16 per frame in 64×64 sheet)."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for frame in range(4):
        ox = frame * 16
        oy = 0
        # Boots
        draw.rectangle([ox + 5, oy + 12, ox + 7, oy + 15], fill=RUST)
        draw.rectangle([ox + 9, oy + 12, ox + 11, oy + 15], fill=RUST)
        # Legs
        draw.rectangle([ox + 6, oy + 9, ox + 7, oy + 12], fill=SAND)
        draw.rectangle([ox + 9, oy + 9, ox + 10, oy + 12], fill=SAND)
        # Torso
        draw.rectangle([ox + 5, oy + 5, ox + 11, oy + 9], fill=TEAL)
        # Cape flutter (varies per frame)
        cape_sway = frame % 3 - 1
        draw.line([(ox + 5, oy + 5), (ox + 3 + cape_sway, oy + 10)], fill=BRASS)
        draw.line([(ox + 5, oy + 6), (ox + 3 + cape_sway, oy + 11)], fill=DARK_RUST)
        # Head
        draw.rectangle([ox + 6, oy + 2, ox + 10, oy + 5], fill=SAND)
        # Hat (pirate bandana)
        draw.rectangle([ox + 5, oy + 1, ox + 11, oy + 3], fill=RUST)
        draw.point((ox + 11, oy + 2), fill=BRASS)
        # Eye
        draw.point((ox + 9, oy + 3), fill=SHADOW)
        # Weapon arm
        if frame == 2:
            draw.line([(ox + 11, oy + 6), (ox + 14, oy + 4)], fill=BONE)
        else:
            draw.line([(ox + 11, oy + 6), (ox + 13, oy + 8)], fill=BONE)

    # Second row: walk frames
    for frame in range(4):
        ox = frame * 16
        oy = 16
        leg_off = 1 if frame % 2 == 0 else -1
        draw.rectangle([ox + 5, oy + 12, ox + 7, oy + 15], fill=RUST)
        draw.rectangle([ox + 9 + leg_off, oy + 12, ox + 11 + leg_off, oy + 15], fill=RUST)
        draw.rectangle([ox + 6, oy + 9, ox + 7, oy + 12], fill=SAND)
        draw.rectangle([ox + 9 + leg_off, oy + 9, ox + 10 + leg_off, oy + 12], fill=SAND)
        draw.rectangle([ox + 5, oy + 5, ox + 11, oy + 9], fill=TEAL)
        draw.rectangle([ox + 6, oy + 2, ox + 10, oy + 5], fill=SAND)
        draw.rectangle([ox + 5, oy + 1, ox + 11, oy + 3], fill=RUST)
        draw.point((ox + 9, oy + 3), fill=SHADOW)

    # Third row: attack frames (3-hit combo)
    for frame in range(3):
        ox = frame * 16
        oy = 32
        draw.rectangle([ox + 5, oy + 12, ox + 7, oy + 15], fill=RUST)
        draw.rectangle([ox + 9, oy + 12, ox + 11, oy + 15], fill=RUST)
        draw.rectangle([ox + 5, oy + 5, ox + 11, oy + 9], fill=TEAL)
        draw.rectangle([ox + 6, oy + 2, ox + 10, oy + 5], fill=SAND)
        draw.rectangle([ox + 5, oy + 1, ox + 11, oy + 3], fill=RUST)
        draw.point((ox + 9, oy + 3), fill=SHADOW)
        # Sword swing arc
        swing_ext = 3 + frame * 3
        draw.line([(ox + 11, oy + 5), (ox + 11 + swing_ext, oy + 3 - frame)], fill=BONE)
        draw.point((ox + 11 + swing_ext, oy + 3 - frame), fill=HIGHLIGHT)

    # Fourth row: jump + dodge
    for frame in range(2):
        ox = frame * 16
        oy = 48
        y_off = -3 if frame == 0 else 0
        draw.rectangle([ox + 5, oy + 12 + y_off, ox + 7, oy + 15 + y_off], fill=RUST)
        draw.rectangle([ox + 9, oy + 12 + y_off, ox + 11, oy + 15 + y_off], fill=RUST)
        draw.rectangle([ox + 5, oy + 5 + y_off, ox + 11, oy + 9 + y_off], fill=TEAL)
        draw.rectangle([ox + 6, oy + 2 + y_off, ox + 10, oy + 5 + y_off], fill=SAND)
        draw.rectangle([ox + 5, oy + 1 + y_off, ox + 11, oy + 3 + y_off], fill=RUST)
    return img


def _gen_simiam_sheet(body_color: tuple, accent: tuple, eye_color: tuple, shape: str) -> Image.Image:
    """Generic SimIAM pet sheet: 4 idle frames + rescue pose."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for frame in range(4):
        ox = frame * 16
        oy = 0
        bob = frame % 2
        if shape == "lizard":
            # Body
            draw.rectangle([ox + 4, oy + 8 - bob, ox + 12, oy + 12 - bob], fill=body_color)
            # Head
            draw.rectangle([ox + 10, oy + 6 - bob, ox + 14, oy + 9 - bob], fill=body_color)
            draw.point((ox + 13, oy + 7 - bob), fill=eye_color)
            # Tail
            draw.line([(ox + 4, oy + 10 - bob), (ox + 1, oy + 12 - bob)], fill=accent)
            # Legs
            draw.line([(ox + 6, oy + 12 - bob), (ox + 6, oy + 14)], fill=body_color)
            draw.line([(ox + 10, oy + 12 - bob), (ox + 10, oy + 14)], fill=body_color)
        elif shape == "spider":
            # Abdomen
            draw.ellipse([ox + 5, oy + 6 - bob, ox + 11, oy + 12 - bob], fill=body_color)
            draw.point((ox + 8, oy + 7 - bob), fill=eye_color)
            draw.point((ox + 9, oy + 7 - bob), fill=eye_color)
            # Legs (4 per side)
            for i in range(4):
                lx = ox + 5 - i
                ly = oy + 8 + i - bob
                draw.line([(ox + 5, ly), (lx, ly + 2)], fill=accent)
                draw.line([(ox + 11, ly), (ox + 11 + (3 - i) + 1, ly + 2)], fill=accent)
        elif shape == "ram":
            # Body
            draw.rectangle([ox + 3, oy + 7 - bob, ox + 12, oy + 12 - bob], fill=body_color)
            # Head
            draw.rectangle([ox + 10, oy + 5 - bob, ox + 14, oy + 9 - bob], fill=body_color)
            draw.point((ox + 13, oy + 6 - bob), fill=eye_color)
            # Horns
            draw.line([(ox + 11, oy + 5 - bob), (ox + 10, oy + 3 - bob)], fill=accent)
            draw.line([(ox + 13, oy + 5 - bob), (ox + 14, oy + 3 - bob)], fill=accent)
            # Legs
            draw.rectangle([ox + 4, oy + 12 - bob, ox + 5, oy + 14], fill=body_color)
            draw.rectangle([ox + 10, oy + 12 - bob, ox + 11, oy + 14], fill=body_color)
            # Tail tuft
            draw.point((ox + 2, oy + 8 - bob), fill=accent)

    # Rescue pose (row 2 — pet curled up / distressed)
    oy = 16
    if shape == "lizard":
        draw.ellipse([4, oy + 6, 12, oy + 14], fill=body_color)
        draw.point((10, oy + 8), fill=eye_color)
        draw.line([(6, oy + 12), (4, oy + 14)], fill=accent)
    elif shape == "spider":
        draw.ellipse([4, oy + 5, 14, oy + 14], fill=body_color)
        for i in range(4):
            draw.line([(6 - i, oy + 10 + i), (4 - i, oy + 14)], fill=accent)
    elif shape == "ram":
        draw.rectangle([3, oy + 8, 13, oy + 14], fill=body_color)
        draw.line([(8, oy + 6), (6, oy + 4)], fill=accent)
        draw.line([(10, oy + 6), (12, oy + 4)], fill=accent)
        draw.point((12, oy + 9), fill=eye_color)
    return img


def gen_mirror_newt_sheet() -> Image.Image:
    return _gen_simiam_sheet(TEAL, HIGHLIGHT, BRASS, "lizard")


def gen_latch_spider_sheet() -> Image.Image:
    return _gen_simiam_sheet(DARK_RUST, RUST, HIGHLIGHT, "spider")


def gen_salt_ram_sheet() -> Image.Image:
    return _gen_simiam_sheet(SAND, BRASS, SHADOW, "ram")


# ── Effects / HUD ─────────────────────────────────────────────────

def gen_bond_weave_fx() -> Image.Image:
    """6-frame effect strip: energy rings expanding outward."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 4 frames across top row (16px each)
    for frame in range(4):
        ox = frame * 16
        oy = 0
        cx, cy = ox + 8, oy + 8
        radius = 2 + frame * 2
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=TEAL)
        if frame > 0:
            inner = radius - 2
            draw.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], outline=HIGHLIGHT)
        # Spark particles
        for _ in range(frame + 1):
            sx = cx + random.randint(-radius, radius)
            sy = cy + random.randint(-radius, radius)
            draw.point((max(ox, min(ox + 15, sx)), max(oy, min(oy + 15, sy))), fill=BRASS)
    # 2 frames on second row (dissipation)
    for frame in range(2):
        ox = frame * 16
        oy = 16
        cx, cy = ox + 8, oy + 8
        radius = 6 + frame
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=BRASS)
        for _ in range(3):
            sx = cx + random.randint(-radius - 1, radius + 1)
            sy = cy + random.randint(-radius - 1, radius + 1)
            draw.point((max(ox, min(ox + 15, sx)), max(oy, min(oy + 15, sy))), fill=HIGHLIGHT)
    return img


def gen_hud_pack() -> Image.Image:
    """HUD elements: HP bar, bond tension meter, weave charge ring, minimap frame."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # HP bar background (top-left quadrant)
    draw.rectangle([1, 1, 30, 5], outline=SHADOW, fill=DARK_RUST)
    draw.rectangle([2, 2, 20, 4], fill=RUST)
    # Bond tension meter (top-right quadrant)
    draw.rectangle([33, 1, 62, 5], outline=SHADOW, fill=SHADOW)
    draw.rectangle([34, 2, 50, 4], fill=BRASS)
    # Weave charge ring (bottom-left quadrant)
    draw.ellipse([4, 36, 28, 60], outline=TEAL)
    draw.arc([6, 38, 26, 58], start=0, end=270, fill=HIGHLIGHT)
    # Milestone frame (bottom-right)
    draw.rectangle([34, 36, 62, 60], outline=BRASS)
    draw.rectangle([36, 38, 60, 58], outline=SHADOW)
    draw.rectangle([38, 40, 58, 56], fill=MID_BLUE)
    # Pet slot indicators (middle row)
    for i, color in enumerate([RUST, TEAL, SAND, HIGHLIGHT]):
        sx = 2 + i * 16
        draw.rectangle([sx, 18, sx + 10, 28], outline=SHADOW, fill=color)
        draw.rectangle([sx + 1, 19, sx + 9, 27], fill=SHADOW)
        draw.rectangle([sx + 2, 20, sx + 8, 26], fill=color)
    return img


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
    for rel_path, gen_fn in GENERATORS.items():
        out_path = OUT_ROOT / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img = gen_fn()
        img.save(str(out_path))
        print(f"  wrote {out_path.relative_to(WORKSPACE)}")
    print(f"\n  {len(GENERATORS)} assets generated under aridfeihth/production_raw/")


if __name__ == "__main__":
    main()
