from __future__ import annotations

import json
import math
import re
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps, ImageStat


ROOT = Path(__file__).resolve().parent.parent
TILE_DIR = ROOT / "assets" / "tiles" / "bango-patoot-tiles"
OUT_DIR = ROOT / "generated"
OUT_FILE = OUT_DIR / "bango_test_level.h"
OUT_JSON = OUT_DIR / "bango_test_level.json"

WORLD_W = 24
WORLD_H = 24
CELL_SIZE = 1.38
SAMPLE_SIZE = 8


def tokenise(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "tile"


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def pack_rgba(color: tuple[int, int, int]) -> int:
    return (color[0] << 24) | (color[1] << 16) | (color[2] << 8) | 0xFF


def sample_tile(path: Path) -> dict:
    image = Image.open(path).convert("RGB")
    albedo_small = image.resize((SAMPLE_SIZE, SAMPLE_SIZE), Image.Resampling.BOX)
    albedo_bytes = albedo_small.tobytes()
    albedo_samples = [
        pack_rgba((albedo_bytes[index], albedo_bytes[index + 1], albedo_bytes[index + 2]))
        for index in range(0, len(albedo_bytes), 3)
    ]

    gray = ImageOps.grayscale(image)
    edge = gray.filter(ImageFilter.FIND_EDGES)
    edge_small = edge.resize((SAMPLE_SIZE, SAMPLE_SIZE), Image.Resampling.BOX)
    gray_small = gray.resize((SAMPLE_SIZE, SAMPLE_SIZE), Image.Resampling.BOX)
    gray_bytes = gray_small.tobytes()
    edge_bytes = edge_small.tobytes()

    height_samples: list[int] = []
    for luminance, edge_value in zip(gray_bytes, edge_bytes):
        combined = int(round(luminance * 0.72 + edge_value * 0.28))
        height_samples.append(max(0, min(255, combined)))

    stat = ImageStat.Stat(image)
    edge_stat = ImageStat.Stat(edge)
    mean = tuple(int(round(v)) for v in stat.mean)

    bright_image = image.resize((32, 32), Image.Resampling.BOX)
    bright_bytes = bright_image.tobytes()
    bright_pixels = sorted(
        [
            (bright_bytes[index], bright_bytes[index + 1], bright_bytes[index + 2])
            for index in range(0, len(bright_bytes), 3)
        ],
        key=lambda rgb: rgb[0] + rgb[1] + rgb[2],
    )
    accent_slice = bright_pixels[-max(1, len(bright_pixels) // 6) :]
    accent = tuple(int(round(sum(pixel[channel] for pixel in accent_slice) / len(accent_slice))) for channel in range(3))

    brightness = sum(stat.mean) / 3.0
    relief = sum(edge_stat.mean) / 3.0 / 255.0

    return {
        "name": path.stem,
        "token": tokenise(path.stem),
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "base": mean,
        "accent": accent,
        "brightness": brightness,
        "relief": relief,
        "albedo_samples": albedo_samples,
        "height_samples": height_samples,
    }


def build_tile_groups(tiles: list[dict]) -> dict[str, list[int]]:
    brightness_order = sorted(range(len(tiles)), key=lambda index: tiles[index]["brightness"])
    relief_order = sorted(range(len(tiles)), key=lambda index: tiles[index]["relief"])
    darkest = brightness_order[: max(3, len(tiles) // 4)]
    brightest = brightness_order[-max(3, len(tiles) // 4) :]
    mids = brightness_order[max(2, len(tiles) // 6) : -max(2, len(tiles) // 6)]
    if not mids:
        mids = brightness_order[:]
    industrial = relief_order[-max(4, len(tiles) // 3) :]
    calm = relief_order[: max(4, len(tiles) // 3)]
    return {
        "darkest": darkest,
        "brightest": brightest,
        "mids": mids,
        "industrial": industrial,
        "calm": calm,
    }


def height_at(x: int, z: int) -> float:
    nx = x / float(WORLD_W - 1) - 0.5
    nz = z / float(WORLD_H - 1)
    central_causeway = math.exp(-((nx * 2.35) ** 2)) * (0.40 + nz * 0.55)
    left_sewer = -math.exp(-(((nx + 0.26) * 6.5) ** 2 + ((nz - 0.33) * 8.0) ** 2)) * 1.10
    right_sump = -math.exp(-(((nx - 0.31) * 5.7) ** 2 + ((nz - 0.48) * 7.0) ** 2)) * 0.88
    altar_dais = math.exp(-(((nx) * 4.8) ** 2 + ((nz - 0.90) * 10.0) ** 2)) * 1.05
    ridge = math.sin((nx + 0.12) * math.pi * 3.4) * 0.26 + math.cos((nz - 0.18) * math.pi * 2.2) * 0.18
    service_ramp = math.exp(-(((nx - 0.18) * 8.5) ** 2)) * math.exp(-(((nz - 0.62) * 4.2) ** 2)) * 0.36
    perimeter_drop = -(abs(nx) ** 1.5) * 0.95
    return ridge + central_causeway + altar_dais + service_ramp + left_sewer + right_sump + perimeter_drop


def choose_tile(x: int, z: int, height: float, slope: float, groups: dict[str, list[int]]) -> int:
    if z >= WORLD_H - 3:
        band = groups["brightest"]
    elif z >= WORLD_H - 6 and abs(x - WORLD_W // 2) <= 3:
        band = groups["calm"]
    elif height < -0.62:
        band = groups["darkest"]
    elif height < -0.18 or slope > 0.36:
        band = groups["industrial"]
    elif abs(x - WORLD_W // 2) <= 2:
        band = groups["brightest"]
    elif x < WORLD_W // 3:
        band = groups["mids"]
    elif x > (WORLD_W * 2) // 3:
        band = groups["calm"]
    else:
        band = groups["mids"]
    return band[(x * 5 + z * 3) % len(band)]


def world_pos(cell_x: int, cell_z: int) -> tuple[float, float]:
    origin_x = -((WORLD_W - 1) * CELL_SIZE) * 0.5
    origin_z = 4.0
    return origin_x + cell_x * CELL_SIZE, origin_z + cell_z * CELL_SIZE


def build_level(tiles: list[dict]) -> dict:
    groups = build_tile_groups(tiles)
    heights: list[float] = []
    tile_indices: list[int] = []
    for z in range(WORLD_H):
        for x in range(WORLD_W):
            center = height_at(x, z)
            dx = height_at(min(WORLD_W - 1, x + 1), z) - height_at(max(0, x - 1), z)
            dz = height_at(x, min(WORLD_H - 1, z + 1)) - height_at(x, max(0, z - 1))
            slope = math.sqrt(dx * dx + dz * dz)
            heights.append(round(center, 5))
            tile_indices.append(choose_tile(x, z, center, slope, groups))

    objects = []
    for cell_x, cell_z, name, kind, interactive, solid, half_extents in [
        (12, 21, "altar_slot", 2, True, True, (1.25, 1.90, 1.25)),
        (8, 11, "sluice_crate_a", 0, False, True, (0.75, 0.72, 0.75)),
        (15, 12, "sluice_crate_b", 0, False, True, (0.75, 0.72, 0.75)),
        (7, 16, "lantern_brazier", 1, True, True, (0.62, 1.25, 0.62)),
        (17, 17, "lantern_post", 1, True, True, (0.42, 1.85, 0.42)),
        (11, 18, "supply_cache", 3, True, True, (0.96, 0.78, 0.96)),
        (5, 9, "service_column", 0, False, True, (0.54, 1.45, 0.54)),
        (18, 9, "service_column_b", 0, False, True, (0.54, 1.45, 0.54)),
    ]:
        pos_x, pos_z = world_pos(cell_x, cell_z)
        objects.append({
            "name": name,
            "x": round(pos_x, 3),
            "z": round(pos_z, 3),
            "half_x": half_extents[0],
            "half_y": half_extents[1],
            "half_z": half_extents[2],
            "interactive": interactive,
            "solid": solid,
            "kind": kind,
        })

    enemies = []
    for cell_x, cell_z, name, kind, health, speed in [
        (10, 10, "gutter_ghoul_a", 0, 24.0, 0.045),
        (14, 11, "gutter_ghoul_b", 0, 24.0, 0.046),
        (9, 15, "wax_knight", 1, 34.0, 0.040),
        (16, 18, "altar_warden", 2, 42.0, 0.037),
        (6, 13, "sump_howler", 0, 28.0, 0.048),
    ]:
        pos_x, pos_z = world_pos(cell_x, cell_z)
        enemies.append({
            "name": name,
            "x": round(pos_x, 3),
            "z": round(pos_z, 3),
            "health": health,
            "speed": speed,
            "kind": kind,
        })

    spawn_x, spawn_z = world_pos(12, 3)
    goal_x, goal_z = world_pos(12, 21)
    return {
        "tiles": tiles,
        "world_width": WORLD_W,
        "world_height": WORLD_H,
        "cell_size": CELL_SIZE,
        "spawn": [round(spawn_x, 3), round(spawn_z, 3)],
        "goal": [round(goal_x, 3), round(goal_z, 3)],
        "heights": heights,
        "tile_indices": tile_indices,
        "objects": objects,
        "enemies": enemies,
    }


def emit_header(level: dict) -> str:
    lines = [
        "#pragma once",
        "",
        "#include <stdint.h>",
        "",
        f"#define BANGO_TEST_TILE_SAMPLE_SIZE {SAMPLE_SIZE}",
        f"#define BANGO_TEST_TILE_COUNT {len(level['tiles'])}",
        f"#define BANGO_TEST_LEVEL_W {WORLD_W}",
        f"#define BANGO_TEST_LEVEL_H {WORLD_H}",
        f"#define BANGO_TEST_LEVEL_OBJECT_COUNT {len(level['objects'])}",
        f"#define BANGO_TEST_LEVEL_ENEMY_COUNT {len(level['enemies'])}",
        "",
        "typedef struct RuntimeLandscapeTileDef {",
        "    const char *name;",
        "    uint8_t base_r;",
        "    uint8_t base_g;",
        "    uint8_t base_b;",
        "    uint8_t accent_r;",
        "    uint8_t accent_g;",
        "    uint8_t accent_b;",
        "    float relief_strength;",
        "    const uint32_t *albedo_samples;",
        "    const uint8_t *height_samples;",
        "} RuntimeLandscapeTileDef;",
        "",
        "typedef struct RuntimeLevelObjectSpawnDef {",
        "    const char *name;",
        "    float x;",
        "    float z;",
        "    float half_x;",
        "    float half_y;",
        "    float half_z;",
        "    int interactive;",
        "    int solid;",
        "    int kind;",
        "} RuntimeLevelObjectSpawnDef;",
        "",
        "typedef struct RuntimeLevelEnemySpawnDef {",
        "    const char *name;",
        "    float x;",
        "    float z;",
        "    float health;",
        "    float speed;",
        "    int kind;",
        "} RuntimeLevelEnemySpawnDef;",
        "",
    ]

    for tile in level["tiles"]:
        token = tile["token"]
        lines.append(f"static const uint32_t g_bango_test_tile_{token}_albedo[BANGO_TEST_TILE_SAMPLE_SIZE * BANGO_TEST_TILE_SAMPLE_SIZE] = {{")
        for row in range(SAMPLE_SIZE):
            row_values = tile["albedo_samples"][row * SAMPLE_SIZE : (row + 1) * SAMPLE_SIZE]
            lines.append("    " + ", ".join(f"0x{value:08X}u" for value in row_values) + ",")
        lines.append("};")
        lines.append("")
        lines.append(f"static const uint8_t g_bango_test_tile_{token}_height[BANGO_TEST_TILE_SAMPLE_SIZE * BANGO_TEST_TILE_SAMPLE_SIZE] = {{")
        for row in range(SAMPLE_SIZE):
            row_values = tile["height_samples"][row * SAMPLE_SIZE : (row + 1) * SAMPLE_SIZE]
            lines.append("    " + ", ".join(f"{value}u" for value in row_values) + ",")
        lines.append("};")
        lines.append("")

    lines.append("static const RuntimeLandscapeTileDef g_bango_test_tiles[BANGO_TEST_TILE_COUNT] = {")
    for tile in level["tiles"]:
        token = tile["token"]
        base = tile["base"]
        accent = tile["accent"]
        lines.append(
            f"    {{\"{tile['name']}\", {base[0]}, {base[1]}, {base[2]}, {accent[0]}, {accent[1]}, {accent[2]}, {tile['relief']:.5f}f, g_bango_test_tile_{token}_albedo, g_bango_test_tile_{token}_height}},"
        )
    lines.append("};")
    lines.append("")

    lines.append("static const float g_bango_test_level_heights[BANGO_TEST_LEVEL_W * BANGO_TEST_LEVEL_H] = {")
    for row in range(WORLD_H):
        row_values = level["heights"][row * WORLD_W : (row + 1) * WORLD_W]
        lines.append("    " + ", ".join(f"{value:.5f}f" for value in row_values) + ",")
    lines.append("};")
    lines.append("")

    lines.append("static const uint8_t g_bango_test_level_tile_indices[BANGO_TEST_LEVEL_W * BANGO_TEST_LEVEL_H] = {")
    for row in range(WORLD_H):
        row_values = level["tile_indices"][row * WORLD_W : (row + 1) * WORLD_W]
        lines.append("    " + ", ".join(str(value) for value in row_values) + ",")
    lines.append("};")
    lines.append("")

    lines.append("static const RuntimeLevelObjectSpawnDef g_bango_test_level_objects[BANGO_TEST_LEVEL_OBJECT_COUNT] = {")
    for obj in level["objects"]:
        lines.append(
            f"    {{\"{obj['name']}\", {obj['x']:.3f}f, {obj['z']:.3f}f, {obj['half_x']:.3f}f, {obj['half_y']:.3f}f, {obj['half_z']:.3f}f, {1 if obj['interactive'] else 0}, {1 if obj['solid'] else 0}, {obj['kind']}}},"
        )
    lines.append("};")
    lines.append("")

    lines.append("static const RuntimeLevelEnemySpawnDef g_bango_test_level_enemies[BANGO_TEST_LEVEL_ENEMY_COUNT] = {")
    for enemy in level["enemies"]:
        lines.append(
            f"    {{\"{enemy['name']}\", {enemy['x']:.3f}f, {enemy['z']:.3f}f, {enemy['health']:.3f}f, {enemy['speed']:.3f}f, {enemy['kind']}}},"
        )
    lines.extend([
        "};",
        "",
        f"static const float g_bango_test_level_cell_size = {CELL_SIZE:.3f}f;",
        f"static const float g_bango_test_level_origin_x = {-((WORLD_W - 1) * CELL_SIZE) * 0.5:.3f}f;",
        "static const float g_bango_test_level_origin_z = 4.000f;",
        f"static const float g_bango_test_spawn_x = {level['spawn'][0]:.3f}f;",
        f"static const float g_bango_test_spawn_z = {level['spawn'][1]:.3f}f;",
        f"static const float g_bango_test_goal_x = {level['goal'][0]:.3f}f;",
        f"static const float g_bango_test_goal_z = {level['goal'][1]:.3f}f;",
        "",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if not TILE_DIR.exists():
        raise SystemExit(f"Tile directory not found: {TILE_DIR}")
    tiles = [sample_tile(path) for path in sorted(TILE_DIR.glob("*.png"))]
    if not tiles:
        raise SystemExit(f"No tiles found in {TILE_DIR}")
    level = build_level(tiles)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(emit_header(level), encoding="utf-8")
    save_json(OUT_JSON, level)
    print(f"Wrote tiled Bango-Patoot test level: {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())