from __future__ import annotations

import argparse
import json
import math
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART_DIR = ROOT / "art" / "chibi_overhaul"
PACKAGE_DIR = ROOT / "review_package" / "chibi_overhaul"
IMAGE_DIR = PACKAGE_DIR / "images"
PAGE_DIR = PACKAGE_DIR / "pages"
BOOK_PATH = PACKAGE_DIR / "ArmoredGearFlySlight_chibi_overhaul_review.ecbmps"
SUMMARY_PATH = PACKAGE_DIR / "chibi_overhaul_summary.json"
DEFAULT_COMPILER = ROOT.parent / "ecbmps_ccp_studio" / "build" / "ecbmps_compiler.exe"

PAGE_IMAGE_SIZE = (640, 480)
PAPER = (242, 236, 226)
PANEL = (226, 218, 206)
FRAME = (116, 106, 96)
INK = (36, 34, 33)
ACCENT = (176, 92, 86)
SEA = (118, 166, 196)
SAND = (222, 196, 148)
FIELD = (128, 182, 118)
STONE = (148, 152, 164)
SHADOW = (84, 86, 110)
HORN = (214, 198, 166)
SPINE = (170, 110, 122)
BODY = (96, 108, 140)
ARMOR = (188, 140, 96)
ARC = (224, 134, 92)
GLOW = (236, 210, 162)
RELIC = (166, 130, 102)
VOID = (50, 44, 60)

DIGITS = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
}


def load_json(name: str) -> dict:
    return json.loads((ART_DIR / name).read_text(encoding="utf-8"))


def make_canvas(width: int, height: int, color: tuple[int, int, int]) -> bytearray:
    return bytearray(bytes(color) * (width * height))


def set_pixel(canvas: bytearray, width: int, height: int, x: int, y: int, color: tuple[int, int, int]) -> None:
    if x < 0 or y < 0 or x >= width or y >= height:
        return
    offset = (y * width + x) * 3
    canvas[offset:offset + 3] = bytes(color)


def fill_rect(canvas: bytearray, width: int, height: int, left: int, top: int, rect_w: int, rect_h: int, color: tuple[int, int, int]) -> None:
    for y in range(top, top + rect_h):
        for x in range(left, left + rect_w):
            set_pixel(canvas, width, height, x, y, color)


def draw_rect(canvas: bytearray, width: int, height: int, left: int, top: int, rect_w: int, rect_h: int, color: tuple[int, int, int]) -> None:
    for x in range(left, left + rect_w):
        set_pixel(canvas, width, height, x, top, color)
        set_pixel(canvas, width, height, x, top + rect_h - 1, color)
    for y in range(top, top + rect_h):
        set_pixel(canvas, width, height, left, y, color)
        set_pixel(canvas, width, height, left + rect_w - 1, y, color)


def draw_line(canvas: bytearray, width: int, height: int, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_pixel(canvas, width, height, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = err * 2
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def draw_polyline(canvas: bytearray, width: int, height: int, points: list[tuple[int, int]], color: tuple[int, int, int]) -> None:
    for index in range(len(points) - 1):
        draw_line(canvas, width, height, points[index][0], points[index][1], points[index + 1][0], points[index + 1][1], color)


def fill_circle(canvas: bytearray, width: int, height: int, center_x: int, center_y: int, radius: int, color: tuple[int, int, int]) -> None:
    radius_sq = radius * radius
    for y in range(center_y - radius, center_y + radius + 1):
        for x in range(center_x - radius, center_x + radius + 1):
            if (x - center_x) * (x - center_x) + (y - center_y) * (y - center_y) <= radius_sq:
                set_pixel(canvas, width, height, x, y, color)


def draw_circle(canvas: bytearray, width: int, height: int, center_x: int, center_y: int, radius: int, color: tuple[int, int, int]) -> None:
    for step in range(0, 360, 4):
        radians = math.radians(step)
        x = center_x + int(math.cos(radians) * radius)
        y = center_y + int(math.sin(radians) * radius)
        set_pixel(canvas, width, height, x, y, color)


def draw_grid(canvas: bytearray, width: int, height: int, left: int, top: int, cols: int, rows: int, cell: int, color: tuple[int, int, int]) -> None:
    draw_rect(canvas, width, height, left, top, cols * cell + 1, rows * cell + 1, color)
    for col in range(1, cols):
        x = left + col * cell
        fill_rect(canvas, width, height, x, top, 1, rows * cell + 1, color)
    for row in range(1, rows):
        y = top + row * cell
        fill_rect(canvas, width, height, left, y, cols * cell + 1, 1, color)


def draw_number(canvas: bytearray, width: int, height: int, x: int, y: int, value: int, color: tuple[int, int, int], scale: int = 2) -> None:
    cursor_x = x
    for char in str(value):
        pattern = DIGITS[char]
        for row, bits in enumerate(pattern):
            for col, bit in enumerate(bits):
                if bit != "1":
                    continue
                fill_rect(canvas, width, height, cursor_x + col * scale, y + row * scale, scale, scale, color)
        cursor_x += (len(pattern[0]) + 1) * scale


def fill_grid_rect(canvas: bytearray, width: int, height: int, left: int, top: int, cell: int, rect: list[int], color: tuple[int, int, int]) -> None:
    x, y, rect_w, rect_h = rect
    fill_rect(canvas, width, height, left + x * cell, top + y * cell, rect_w * cell, rect_h * cell, color)


def draw_anchor(canvas: bytearray, width: int, height: int, left: int, top: int, cell: int, xy: list[int], number: int) -> None:
    x, y = xy
    fill_rect(canvas, width, height, left + x * cell - 2, top + y * cell - 2, 5, 5, ACCENT)
    draw_number(canvas, width, height, left + x * cell + 4, top + y * cell - 4, number, INK, scale=2)


def draw_hatch(canvas: bytearray, width: int, height: int, left: int, top: int, rect_w: int, rect_h: int, spacing: int, color: tuple[int, int, int], direction: str = "forward") -> None:
    start = -rect_h
    stop = rect_w + rect_h
    for offset in range(start, stop, max(spacing, 2)):
        if direction == "backward":
            draw_line(canvas, width, height, left + offset, top + rect_h, left + offset + rect_h, top, color)
        else:
            draw_line(canvas, width, height, left + offset, top, left + offset + rect_h, top + rect_h, color)


def draw_chain(canvas: bytearray, width: int, height: int, left: int, top: int, links: int, spacing: int, color: tuple[int, int, int], horizontal: bool = True) -> None:
    previous: tuple[int, int] | None = None
    for index in range(links):
        center_x = left + index * spacing if horizontal else left
        center_y = top if horizontal else top + index * spacing
        draw_circle(canvas, width, height, center_x, center_y, 4, color)
        if previous is not None:
            draw_line(canvas, width, height, previous[0], previous[1], center_x, center_y, color)
        previous = (center_x, center_y)


def draw_spike_row(canvas: bytearray, width: int, height: int, left: int, top: int, length: int, spike_count: int, color: tuple[int, int, int], orientation: str = "up") -> None:
    spike_count = max(spike_count, 1)
    step = max(length // spike_count, 6)
    for index in range(spike_count):
        start_x = left + index * step
        end_x = min(start_x + step, left + length)
        mid_x = (start_x + end_x) // 2
        if orientation == "down":
            draw_line(canvas, width, height, start_x, top, mid_x, top + 10, color)
            draw_line(canvas, width, height, mid_x, top + 10, end_x, top, color)
        else:
            draw_line(canvas, width, height, start_x, top + 10, mid_x, top, color)
            draw_line(canvas, width, height, mid_x, top, end_x, top + 10, color)


def draw_pointed_arch(canvas: bytearray, width: int, height: int, left: int, top: int, rect_w: int, rect_h: int, color: tuple[int, int, int]) -> None:
    base_y = top + rect_h
    apex_x = left + rect_w // 2
    draw_line(canvas, width, height, left, base_y, apex_x, top, color)
    draw_line(canvas, width, height, left + rect_w, base_y, apex_x, top, color)
    draw_line(canvas, width, height, left, base_y, left, base_y + 10, color)
    draw_line(canvas, width, height, left + rect_w, base_y, left + rect_w, base_y + 10, color)


def draw_wave_band(canvas: bytearray, width: int, height: int, left: int, top: int, length: int, amplitude: int, segments: int, color: tuple[int, int, int]) -> None:
    points = []
    for step in range(segments + 1):
        x = left + (step * length) // max(segments, 1)
        y = top + int(math.sin((step / max(segments, 1)) * math.tau) * amplitude)
        points.append((x, y))
    draw_polyline(canvas, width, height, points, color)


def draw_arc_swipe(canvas: bytearray, width: int, height: int, left: int, top: int, rect_w: int, rect_h: int, direction: str, color: tuple[int, int, int]) -> None:
    if direction in {"east", "west"}:
        for step in range(0, rect_h, 4):
            if direction == "east":
                draw_line(canvas, width, height, left, top + rect_h - step - 1, left + rect_w, top + step, color)
            else:
                draw_line(canvas, width, height, left + rect_w, top + rect_h - step - 1, left, top + step, color)
    else:
        for step in range(0, rect_w, 4):
            if direction == "north":
                draw_line(canvas, width, height, left + step, top + rect_h, left + rect_w - step - 1, top, color)
            else:
                draw_line(canvas, width, height, left + step, top, left + rect_w - step - 1, top + rect_h, color)


def write_bmp(path: Path, width: int, height: int, canvas: bytearray) -> None:
    row_stride = width * 3
    padding = (4 - (row_stride % 4)) % 4
    image_size = (row_stride + padding) * height
    file_size = 14 + 40 + image_size
    header = bytearray()
    header.extend(b"BM")
    header.extend(struct.pack("<I", file_size))
    header.extend(b"\x00\x00\x00\x00")
    header.extend(struct.pack("<I", 54))
    header.extend(struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, image_size, 2835, 2835, 0, 0))

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(header)
        for row in range(height - 1, -1, -1):
            start = row * row_stride
            rgb_row = canvas[start:start + row_stride]
            bgr = bytearray()
            for offset in range(0, len(rgb_row), 3):
                red = rgb_row[offset]
                green = rgb_row[offset + 1]
                blue = rgb_row[offset + 2]
                bgr.extend((blue, green, red))
            bgr.extend(b"\x00" * padding)
            handle.write(bgr)


def render_translation_board(authoring: dict, output_path: Path) -> None:
    width, height = PAGE_IMAGE_SIZE
    canvas = make_canvas(width, height, PAPER)
    fill_rect(canvas, width, height, 18, 18, width - 36, height - 36, PANEL)
    draw_rect(canvas, width, height, 18, 18, width - 36, height - 36, FRAME)

    left_panel = (44, 56)
    right_panel = (348, 56)
    cell = 28
    draw_grid(canvas, width, height, left_panel[0], left_panel[1], 4, 4, cell, FRAME)
    fill_grid_rect(canvas, width, height, left_panel[0], left_panel[1], cell, [1, 1, 2, 2], BODY)
    for direction, rect in {
        "north": [1, 0, 2, 1],
        "south": [1, 3, 2, 1],
        "west": [0, 1, 1, 2],
        "east": [3, 1, 1, 2],
    }.items():
        fill_grid_rect(canvas, width, height, left_panel[0], left_panel[1], cell, rect, ARC)
        draw_arc_swipe(
            canvas,
            width,
            height,
            left_panel[0] + rect[0] * cell,
            left_panel[1] + rect[1] * cell,
            rect[2] * cell,
            rect[3] * cell,
            direction,
            GLOW,
        )
    draw_pointed_arch(canvas, width, height, left_panel[0] + 24, left_panel[1] + 10, 64, 74, FRAME)
    draw_chain(canvas, width, height, left_panel[0] + 12, left_panel[1] + 118, 6, 18, RELIC)
    draw_spike_row(canvas, width, height, left_panel[0] + 10, left_panel[1] + 6, 92, 6, HORN)
    draw_number(canvas, width, height, left_panel[0] + 18, left_panel[1] + 124, 1, INK, scale=4)

    draw_grid(canvas, width, height, right_panel[0], right_panel[1], 4, 4, cell, FRAME)
    quadrant_colors = [SEA, SAND, FIELD, STONE]
    fill_grid_rect(canvas, width, height, right_panel[0], right_panel[1], cell, [0, 0, 2, 2], quadrant_colors[0])
    fill_grid_rect(canvas, width, height, right_panel[0], right_panel[1], cell, [2, 0, 2, 2], quadrant_colors[1])
    fill_grid_rect(canvas, width, height, right_panel[0], right_panel[1], cell, [0, 2, 2, 2], quadrant_colors[2])
    fill_grid_rect(canvas, width, height, right_panel[0], right_panel[1], cell, [2, 2, 2, 2], quadrant_colors[3])
    draw_wave_band(canvas, width, height, right_panel[0] + 8, right_panel[1] + 22, 44, 4, 8, PAPER)
    draw_hatch(canvas, width, height, right_panel[0] + 62, right_panel[1] + 10, 44, 44, 8, FRAME)
    draw_spike_row(canvas, width, height, right_panel[0] + 8, right_panel[1] + 86, 44, 5, INK, "up")
    draw_pointed_arch(canvas, width, height, right_panel[0] + 66, right_panel[1] + 66, 36, 28, VOID)
    draw_number(canvas, width, height, right_panel[0] + 18, right_panel[1] + 124, 2, INK, scale=4)

    draw_rect(canvas, width, height, 84, 272, 472, 138, FRAME)
    section_lefts = [108, 262, 416]
    section_colors = [BODY, ARC, ARMOR]
    for index, section_left in enumerate(section_lefts, start=3):
        draw_rect(canvas, width, height, section_left, 292, 104, 96, FRAME)
        fill_rect(canvas, width, height, section_left + 14, 308, 76, 60, section_colors[index - 3])
        draw_hatch(canvas, width, height, section_left + 14, 308, 76, 60, 8, PANEL, "backward")
        draw_pointed_arch(canvas, width, height, section_left + 22, 316, 58, 34, SHADOW)
        draw_chain(canvas, width, height, section_left + 24, 360, 4, 16, RELIC)
        draw_number(canvas, width, height, section_left + 34, 392, index, INK, scale=3)

    write_bmp(output_path, width, height, canvas)


def render_environment_card(canvas: bytearray, width: int, height: int, left: int, top: int, entry: dict, index: int, palette_lookup: dict[str, tuple[tuple[int, int, int], ...]]) -> None:
    draw_rect(canvas, width, height, left, top, 170, 168, FRAME)
    fill_rect(canvas, width, height, left + 1, top + 1, 168, 166, PANEL)
    grid_left = left + 10
    grid_top = top + 10
    cell = 34
    draw_grid(canvas, width, height, grid_left, grid_top, 4, 4, cell, FRAME)

    palette = palette_lookup[entry["palette_role"]]
    fill_grid_rect(canvas, width, height, grid_left, grid_top, cell, [0, 0, 2, 2], palette[0])
    fill_grid_rect(canvas, width, height, grid_left, grid_top, cell, [2, 0, 2, 2], palette[1])
    fill_grid_rect(canvas, width, height, grid_left, grid_top, cell, [0, 2, 2, 2], palette[2])
    fill_grid_rect(canvas, width, height, grid_left, grid_top, cell, [2, 2, 2, 2], palette[3])

    entry_id = entry["id"]
    if entry_id == "shore_wreck":
        draw_wave_band(canvas, width, height, grid_left + 8, grid_top + 18, 48, 5, 8, PAPER)
        draw_wave_band(canvas, width, height, grid_left + 14, grid_top + 32, 38, 4, 6, PAPER)
        draw_polyline(canvas, width, height, [(grid_left + 62, grid_top + 14), (grid_left + 92, grid_top + 36), (grid_left + 118, grid_top + 54)], RELIC)
        draw_polyline(canvas, width, height, [(grid_left + 70, grid_top + 28), (grid_left + 102, grid_top + 48), (grid_left + 134, grid_top + 70)], RELIC)
        draw_chain(canvas, width, height, grid_left + 20, grid_top + 114, 4, 14, FRAME)
    elif entry_id == "dune_path":
        draw_polyline(canvas, width, height, [(grid_left + 8, grid_top + 44), (grid_left + 40, grid_top + 18), (grid_left + 74, grid_top + 28)], SHADOW)
        draw_polyline(canvas, width, height, [(grid_left + 66, grid_top + 76), (grid_left + 96, grid_top + 48), (grid_left + 132, grid_top + 58)], SHADOW)
        draw_hatch(canvas, width, height, grid_left + 76, grid_top + 12, 48, 38, 8, FRAME)
        draw_spike_row(canvas, width, height, grid_left + 18, grid_top + 116, 44, 6, INK, "up")
    elif entry_id == "field_vista":
        draw_wave_band(canvas, width, height, grid_left + 8, grid_top + 104, 122, 4, 14, SHADOW)
        draw_wave_band(canvas, width, height, grid_left + 8, grid_top + 122, 122, 3, 14, FRAME)
        for flower_x in range(grid_left + 18, grid_left + 118, 20):
            fill_circle(canvas, width, height, flower_x, grid_top + 88 + (flower_x % 9), 3, GLOW)
        draw_pointed_arch(canvas, width, height, grid_left + 102, grid_top + 42, 18, 18, VOID)
    elif entry_id == "settlement_foundation":
        for offset in range(0, 64, 18):
            draw_line(canvas, width, height, grid_left + 18 + offset, grid_top + 16, grid_left + 18 + offset, grid_top + 88, RELIC)
        draw_line(canvas, width, height, grid_left + 18, grid_top + 28, grid_left + 72, grid_top + 74, FRAME)
        draw_line(canvas, width, height, grid_left + 36, grid_top + 20, grid_left + 90, grid_top + 66, FRAME)
        draw_polyline(canvas, width, height, [(grid_left + 106, grid_top + 24), (grid_left + 132, grid_top + 36), (grid_left + 108, grid_top + 52)], ACCENT)
    elif entry_id == "shrine_monolith":
        fill_rect(canvas, width, height, grid_left + 52, grid_top + 12, 38, 82, STONE)
        draw_rect(canvas, width, height, grid_left + 52, grid_top + 12, 38, 82, VOID)
        draw_pointed_arch(canvas, width, height, grid_left + 46, grid_top + 4, 50, 20, GLOW)
        draw_circle(canvas, width, height, grid_left + 70, grid_top + 114, 24, GLOW)
        draw_polyline(canvas, width, height, [(grid_left + 60, grid_top + 36), (grid_left + 72, grid_top + 28), (grid_left + 82, grid_top + 42)], FRAME)
        draw_polyline(canvas, width, height, [(grid_left + 62, grid_top + 58), (grid_left + 72, grid_top + 48), (grid_left + 80, grid_top + 62)], FRAME)
    elif entry_id == "rim_battlefield":
        fill_circle(canvas, width, height, grid_left + 30, grid_top + 36, 18, VOID)
        draw_spike_row(canvas, width, height, grid_left + 56, grid_top + 20, 72, 6, SPINE)
        draw_polyline(canvas, width, height, [(grid_left + 64, grid_top + 86), (grid_left + 84, grid_top + 68), (grid_left + 104, grid_top + 92), (grid_left + 126, grid_top + 76)], GLOW)
        draw_polyline(canvas, width, height, [(grid_left + 18, grid_top + 114), (grid_left + 54, grid_top + 96), (grid_left + 76, grid_top + 118)], FRAME)

    draw_number(canvas, width, height, left + 70, top + 146, index, INK, scale=3)


def render_environment_board(environment: dict, output_path: Path) -> None:
    width, height = PAGE_IMAGE_SIZE
    canvas = make_canvas(width, height, PAPER)
    fill_rect(canvas, width, height, 18, 18, width - 36, height - 36, PANEL)
    draw_rect(canvas, width, height, 18, 18, width - 36, height - 36, FRAME)

    palette_lookup = {
        "shorelight": (SEA, SAND, PANEL, SHADOW),
        "sunbleached": (SAND, PANEL, FIELD, SHADOW),
        "lush": (FIELD, (146, 198, 128), SAND, SHADOW),
        "warm_earth": (SAND, ARMOR, (170, 120, 82), SHADOW),
        "moonstone": (STONE, (196, 210, 226), PANEL, SHADOW),
        "abyssal": (VOID, SPINE, SAND, STONE),
    }

    for index, entry in enumerate(environment["metatiles"][:6], start=1):
        row = (index - 1) // 3
        col = (index - 1) % 3
        left = 28 + col * 194
        top = 38 + row * 196
        render_environment_card(canvas, width, height, left, top, entry, index, palette_lookup)

    write_bmp(output_path, width, height, canvas)


def render_player_rig_board(player: dict, equipment: dict, output_path: Path) -> None:
    width, height = PAGE_IMAGE_SIZE
    canvas = make_canvas(width, height, PAPER)
    fill_rect(canvas, width, height, 18, 18, width - 36, height - 36, PANEL)
    draw_rect(canvas, width, height, 18, 18, width - 36, height - 36, FRAME)

    origin_x = 42
    origin_y = 40
    cell = 10
    draw_grid(canvas, width, height, origin_x, origin_y, 32, 32, cell, FRAME)
    fill_grid_rect(canvas, width, height, origin_x, origin_y, cell, player["canvas"]["body_core"], BODY)
    for direction, rect in player["canvas"]["attack_space"].items():
        fill_grid_rect(canvas, width, height, origin_x, origin_y, cell, rect, ARC)
        draw_arc_swipe(
            canvas,
            width,
            height,
            origin_x + rect[0] * cell,
            origin_y + rect[1] * cell,
            rect[2] * cell,
            rect[3] * cell,
            direction,
            GLOW,
        )
    draw_pointed_arch(canvas, width, height, origin_x + 74, origin_y + 32, 90, 96, FRAME)
    fill_circle(canvas, width, height, origin_x + 160, origin_y + 106, 18, GLOW)
    fill_rect(canvas, width, height, origin_x + 140, origin_y + 126, 40, 58, BODY)
    draw_line(canvas, width, height, origin_x + 140, origin_y + 138, origin_x + 118, origin_y + 176, FRAME)
    draw_line(canvas, width, height, origin_x + 180, origin_y + 138, origin_x + 202, origin_y + 176, FRAME)
    draw_line(canvas, width, height, origin_x + 148, origin_y + 184, origin_x + 136, origin_y + 238, FRAME)
    draw_line(canvas, width, height, origin_x + 172, origin_y + 184, origin_x + 186, origin_y + 238, FRAME)
    draw_hatch(canvas, width, height, origin_x + 134, origin_y + 126, 52, 62, 8, PANEL)
    draw_chain(canvas, width, height, origin_x + 140, origin_y + 192, 4, 12, RELIC)

    for number, anchor in enumerate(player["anchor_points"], start=1):
        draw_anchor(canvas, width, height, origin_x, origin_y, cell, anchor["xy"], number)

    mini_positions = [(392, 48), (392, 148), (392, 248), (392, 348)]
    for number, (left, top) in enumerate(mini_positions, start=1):
        draw_rect(canvas, width, height, left, top, 196, 82, FRAME)
        fill_circle(canvas, width, height, left + 48, top + 28, 10, GLOW)
        fill_rect(canvas, width, height, left + 36, top + 38, 24, 26, BODY)
        fill_rect(canvas, width, height, left + 62, top + 42, 14, 14, ARMOR)
        draw_chain(canvas, width, height, left + 28, top + 66, 3, 14, RELIC)
        if number == 1:
            draw_arc_swipe(canvas, width, height, left + 82, top + 12, 56, 18, "north", ARC)
        elif number == 2:
            draw_arc_swipe(canvas, width, height, left + 92, top + 20, 58, 28, "east", ARC)
        elif number == 3:
            draw_arc_swipe(canvas, width, height, left + 80, top + 48, 56, 18, "south", ARC)
        else:
            draw_arc_swipe(canvas, width, height, left + 16, top + 20, 58, 28, "west", ARC)
        draw_number(canvas, width, height, left + 146, top + 30, number, ACCENT, scale=3)

    write_bmp(output_path, width, height, canvas)


def draw_armor_panel(canvas: bytearray, width: int, height: int, left: int, top: int, armor_set: dict, index: int) -> None:
    draw_rect(canvas, width, height, left, top, 176, 160, FRAME)
    fill_rect(canvas, width, height, left + 1, top + 1, 174, 158, PANEL)
    draw_pointed_arch(canvas, width, height, left + 56, top + 10, 56, 34, FRAME)
    fill_circle(canvas, width, height, left + 88, top + 46, 12, GLOW)
    fill_rect(canvas, width, height, left + 72, top + 58, 32, 46, BODY)
    fill_rect(canvas, width, height, left + 68, top + 62, 10, 16, ARMOR)
    fill_rect(canvas, width, height, left + 98, top + 62, 10, 16, ARMOR)
    fill_rect(canvas, width, height, left + 72, top + 82, 32, 18, ARMOR)

    for piece_index, _piece in enumerate(armor_set["pieces"]):
        piece_left = left + 18 + (piece_index % 4) * 36
        piece_top = top + 110 + (piece_index // 4) * 18
        draw_rect(canvas, width, height, piece_left, piece_top, 24, 12, ARMOR)
        draw_number(canvas, width, height, piece_left + 8, piece_top + 2, piece_index + 1, INK, scale=1)
    draw_chain(canvas, width, height, left + 30, top + 146, 4, 18, RELIC)
    draw_number(canvas, width, height, left + 74, top + 132, index, ACCENT, scale=3)


def draw_daemon_panel(canvas: bytearray, width: int, height: int, left: int, top: int, actor: dict, index: int) -> None:
    draw_rect(canvas, width, height, left, top, 250, 180, FRAME)
    fill_rect(canvas, width, height, left + 1, top + 1, 248, 178, PANEL)
    draw_pointed_arch(canvas, width, height, left + 88, top + 8, 70, 34, SHADOW)

    torso_left = left + 96
    torso_top = top + 54
    fill_rect(canvas, width, height, torso_left, torso_top, 44, 64, BODY)
    fill_circle(canvas, width, height, torso_left + 22, torso_top - 8, 16, VOID)
    fill_circle(canvas, width, height, torso_left + 10, torso_top - 16, 8, HORN)
    fill_circle(canvas, width, height, torso_left + 34, torso_top - 16, 8, HORN)
    draw_line(canvas, width, height, torso_left + 10, torso_top - 16, torso_left + 2, torso_top - 36, HORN)
    draw_line(canvas, width, height, torso_left + 34, torso_top - 16, torso_left + 42, torso_top - 36, HORN)
    draw_rect(canvas, width, height, torso_left + 12, torso_top + 12, 20, 10, GLOW)
    draw_hatch(canvas, width, height, torso_left, torso_top, 44, 64, 8, SHADOW)
    draw_spike_row(canvas, width, height, torso_left + 44, torso_top + 4, 50, max(len(actor.get("surface_layers", [])), 3), SPINE)
    draw_chain(canvas, width, height, torso_left - 18, torso_top + 48, max(len(actor.get("vice_markers", [])), 3), 16, RELIC)
    draw_polyline(canvas, width, height, [(torso_left + 16, torso_top + 8), (torso_left + 22, torso_top - 4), (torso_left + 28, torso_top + 8)], ARC)
    draw_polyline(canvas, width, height, [(torso_left - 12, torso_top + 64), (torso_left - 34, torso_top + 102), (torso_left - 22, torso_top + 130)], FRAME)
    draw_polyline(canvas, width, height, [(torso_left + 54, torso_top + 64), (torso_left + 76, torso_top + 102), (torso_left + 64, torso_top + 130)], FRAME)
    draw_polyline(canvas, width, height, [(torso_left + 10, torso_top + 116), (torso_left - 4, torso_top + 150)], FRAME)
    draw_polyline(canvas, width, height, [(torso_left + 34, torso_top + 116), (torso_left + 48, torso_top + 150)], FRAME)
    draw_number(canvas, width, height, left + 112, top + 148, index, ACCENT, scale=4)


def render_overlay_board(equipment: dict, daemons: dict, output_path: Path) -> None:
    width, height = PAGE_IMAGE_SIZE
    canvas = make_canvas(width, height, PAPER)
    fill_rect(canvas, width, height, 18, 18, width - 36, height - 36, PANEL)
    draw_rect(canvas, width, height, 18, 18, width - 36, height - 36, FRAME)

    for index, armor_set in enumerate(equipment["armor_sets"], start=1):
        left = 18 + (index - 1) * 202
        top = 26
        draw_armor_panel(canvas, width, height, left, top, armor_set, index)

    for index, actor in enumerate(daemons["actors"], start=4):
        left = 42 + (index - 4) * 284
        top = 222
        draw_daemon_panel(canvas, width, height, left, top, actor, index)

    write_bmp(output_path, width, height, canvas)


def draw_player_frame(canvas: bytearray, width: int, height: int, left: int, top: int, frame: int, mode: str) -> None:
    draw_rect(canvas, width, height, left, top, 110, 64, FRAME)
    body_offset = frame * 4 if mode == "walk" else frame * 2
    fill_circle(canvas, width, height, left + 34 + (body_offset // 2), top + 18, 8, GLOW)
    fill_rect(canvas, width, height, left + 28 + (body_offset // 2), top + 26, 18, 24, BODY)
    draw_line(canvas, width, height, left + 28, top + 34, left + 18, top + 52 - (frame % 2) * 6, FRAME)
    draw_line(canvas, width, height, left + 46, top + 34, left + 58, top + 52 - ((frame + 1) % 2) * 6, FRAME)
    draw_line(canvas, width, height, left + 32, top + 50, left + 24 + (frame % 2) * 4, top + 62, FRAME)
    draw_line(canvas, width, height, left + 42, top + 50, left + 50 - (frame % 2) * 4, top + 62, FRAME)
    if mode == "wake":
        draw_polyline(canvas, width, height, [(left + 10, top + 54), (left + 26, top + 42), (left + 44, top + 36)], SEA)
    elif mode == "attack":
        draw_arc_swipe(canvas, width, height, left + 58, top + 10, 40, 36, "east", ARC)
    elif mode == "build":
        draw_line(canvas, width, height, left + 60, top + 14, left + 76, top + 46, RELIC)
        draw_rect(canvas, width, height, left + 74, top + 44, 10, 10, ARMOR)
    else:
        draw_chain(canvas, width, height, left + 14, top + 56, 3, 12, RELIC)


def draw_daemon_frame(canvas: bytearray, width: int, height: int, left: int, top: int, frame: int) -> None:
    draw_rect(canvas, width, height, left, top, 110, 64, FRAME)
    fill_circle(canvas, width, height, left + 36, top + 18, 10, VOID)
    fill_rect(canvas, width, height, left + 26, top + 26, 22, 22, BODY)
    draw_line(canvas, width, height, left + 30, top + 10, left + 22 - frame * 2, top + 2, HORN)
    draw_line(canvas, width, height, left + 42, top + 10, left + 50 + frame * 2, top + 2, HORN)
    draw_spike_row(canvas, width, height, left + 50, top + 16, 32, 4, SPINE)
    draw_arc_swipe(canvas, width, height, left + 58, top + 18, 36, 20, "east", ARC)
    draw_chain(canvas, width, height, left + 12, top + 56, 3, 12, RELIC)


def render_animation_board(player: dict, daemons: dict, output_path: Path) -> None:
    width, height = PAGE_IMAGE_SIZE
    canvas = make_canvas(width, height, PAPER)
    fill_rect(canvas, width, height, 18, 18, width - 36, height - 36, PANEL)
    draw_rect(canvas, width, height, 18, 18, width - 36, height - 36, FRAME)

    lanes = [
        ("wake_ashore", "wake"),
        ("walk_east", "walk"),
        ("rake_combo_east", "attack"),
        (daemons["actors"][0]["animation_sets"][1]["id"], "daemon"),
    ]
    for lane_index, (_name, mode) in enumerate(lanes, start=1):
        top = 34 + (lane_index - 1) * 104
        draw_rect(canvas, width, height, 32, top, 574, 82, FRAME)
        for frame in range(4):
            left = 48 + frame * 136
            if mode == "daemon":
                draw_daemon_frame(canvas, width, height, left, top + 10, frame)
            else:
                draw_player_frame(canvas, width, height, left, top + 10, frame, mode)
            draw_number(canvas, width, height, left + 86, top + 56, frame + 1, INK, scale=2)
        draw_number(canvas, width, height, 562, top + 26, lane_index, ACCENT, scale=3)

    write_bmp(output_path, width, height, canvas)


def write_pages(authoring: dict, environment: dict, player: dict, equipment: dict, daemons: dict) -> list[str]:
    page1_lines = [
        "Armored Gear: Fly Slight Chibi Overhaul Review",
        "",
        "This package defines a 32x32 authoring pipeline for a future anime-chibi overhaul while preserving the Game Boy DMG runtime target.",
        "",
        "New density pass:",
        f"- {authoring['complexity_target']['detail_multiplier']}",
        "- Medieval and gothic daemon folklore now drives the silhouette language",
        "- Pixel-economy rules require every added detail to be paid for with nearby negative-space cuts",
        "- Review boards are denser blueprints, not finished painted art",
    ]

    page2_lines = [
        "Hardware Translation And Pixel Economy",
        "",
        "The overhaul is authored at 32x32 but exported down to DMG-safe chunks:",
        "",
    ]
    for line in authoring["translation_rules"]:
        page2_lines.append(f"- {line}")
    page2_lines.append("")
    page2_lines.append("Pixel-economy principles:")
    for line in authoring["pixel_economy_principles"]:
        page2_lines.append(f"- {line}")

    page3_lines = [
        "Epic Environment Metatiles",
        "",
        f"Density profile: {environment['density_profile']['detail_multiplier']}",
        environment["density_profile"]["focus_rule"],
        "",
    ]
    for index, entry in enumerate(environment["metatiles"], start=1):
        page3_lines.append(f"{index}. {entry['id']} -> {entry['role']}")
        page3_lines.append(f"   gothic motifs: {', '.join(entry['gothic_motifs'][:2])}")
        page3_lines.append(f"   micro forms: {', '.join(entry['micro_forms'][:2])}")

    page4_lines = [
        "Player Rig, Costume Density, And Anchors",
        "",
        "The Feather Bearer uses a 32x32 canvas with a central 16x16 body core and named equipment anchors.",
        "",
        "Silhouette priorities:",
    ]
    for line in player["density_rules"]["silhouette_priority"]:
        page4_lines.append(f"- {line}")
    page4_lines.append("")
    page4_lines.append("Animation families:")
    for animation in player["animation_sets"]:
        page4_lines.append(f"- {animation['id']} ({animation['frames']} frames): {animation['purpose']}")

    page5_lines = [
        "Armor, Tools, And Daemon Folklore",
        "",
        "Folklore drivers:",
    ]
    for group, inspirations in authoring["folklore_inspirations"].items():
        page5_lines.append(f"- {group}: {', '.join(inspirations[:2])}")
    page5_lines.append("")
    page5_lines.append("Armor sets:")
    for armor_set in equipment["armor_sets"]:
        page5_lines.append(f"- {armor_set['id']}: {armor_set['role']}")
    page5_lines.append("")
    page5_lines.append("Daemon actors:")
    for actor in daemons["actors"]:
        page5_lines.append(f"- {actor['id']}: {actor['archetype']} / hybrids {', '.join(actor['hybrid_sources'])}")

    page6_lines = [
        "Animation Choreography",
        "",
        "Every move is authored with a body core plus a telegraph band for the active tool or weapon.",
        "",
        "Recommended lane order:",
        "- wake ashore",
        "- idle and walk in four directions",
        "- rake combo in four directions",
        "- till, plant, harvest, build, rest, and hurt",
        "- daemon perch, roam, windup, lunge, stagger, and boss break",
        "",
        "Daemon motion notes:",
        "- lesser kin perch like hungry gargoyles before they spring",
        "- the famine boss should feel like a cathedral guardian cracking into motion",
    ]

    page_texts = {
        "page001.txt": "\n".join(page1_lines) + "\n",
        "page002.txt": "\n".join(page2_lines) + "\n",
        "page003.txt": "\n".join(page3_lines) + "\n",
        "page004.txt": "\n".join(page4_lines) + "\n",
        "page005.txt": "\n".join(page5_lines) + "\n",
        "page006.txt": "\n".join(page6_lines) + "\n",
    }
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in page_texts.items():
        (PAGE_DIR / name).write_text(content, encoding="utf-8")
    return [name for name in sorted(page_texts.keys())]


def build_summary(authoring: dict, environment: dict, player: dict, equipment: dict, daemons: dict) -> dict:
    return {
        "project": authoring["project"],
        "runtime_target": authoring["runtime_target"],
        "authoring_target": authoring["authoring_target"],
        "complexity_target": authoring["complexity_target"],
        "folklore_inspirations": authoring["folklore_inspirations"],
        "style_direction": authoring["style_direction"],
        "environment_metatiles": [entry["id"] for entry in environment["metatiles"]],
        "player_animation_count": len(player["animation_sets"]),
        "armor_set_count": len(equipment["armor_sets"]),
        "weapon_set_count": len(equipment["weapon_sets"]),
        "daemon_actor_count": len(daemons["actors"]),
        "book": str(BOOK_PATH.relative_to(ROOT)),
    }


def render_review_assets() -> list[str]:
    authoring = load_json("authoring_manifest.json")
    environment = load_json("environment_manifest.json")
    player = load_json("player_actor_manifest.json")
    equipment = load_json("equipment_layers.json")
    daemons = load_json("daemon_actor_manifest.json")

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    translation_path = IMAGE_DIR / "page002_translation_board.bmp"
    environment_path = IMAGE_DIR / "page003_environment_board.bmp"
    player_path = IMAGE_DIR / "page004_player_rig_board.bmp"
    overlay_path = IMAGE_DIR / "page005_overlay_board.bmp"
    animation_path = IMAGE_DIR / "page006_animation_board.bmp"

    render_translation_board(authoring, translation_path)
    render_environment_board(environment, environment_path)
    render_player_rig_board(player, equipment, player_path)
    render_overlay_board(equipment, daemons, overlay_path)
    render_animation_board(player, daemons, animation_path)

    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(build_summary(authoring, environment, player, equipment, daemons), indent=2), encoding="utf-8")
    write_pages(authoring, environment, player, equipment, daemons)

    return [
        str(PAGE_DIR / "page001.txt"),
        f"{PAGE_DIR / 'page002.txt'}+{translation_path}",
        f"{PAGE_DIR / 'page003.txt'}+{environment_path}",
        f"{PAGE_DIR / 'page004.txt'}+{player_path}",
        f"{PAGE_DIR / 'page005.txt'}+{overlay_path}",
        f"{PAGE_DIR / 'page006.txt'}+{animation_path}",
    ]


def compile_book(page_args: list[str], compiler_path: Path) -> None:
    if not compiler_path.exists():
        raise FileNotFoundError(f"Missing ECBMPS compiler: {compiler_path}")
    command = [
        str(compiler_path),
        "-o",
        str(BOOK_PATH),
        "-t",
        "Armored Gear: Fly Slight Chibi Overhaul",
        "-a",
        "GitHub Copilot",
    ] + page_args
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Armored Gear: Fly Slight chibi-overhaul review package.")
    parser.add_argument("--skip-compile", action="store_true", help="Render the review package without compiling the ECBMPS book.")
    parser.add_argument("--compiler", type=Path, default=DEFAULT_COMPILER, help="Override the path to ecbmps_compiler.exe.")
    args = parser.parse_args()

    page_args = render_review_assets()
    if not args.skip_compile:
        compile_book(page_args, args.compiler)
    print(json.dumps({
        "package_dir": str(PACKAGE_DIR),
        "book": str(BOOK_PATH),
        "summary": str(SUMMARY_PATH),
        "compiled": not args.skip_compile,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())