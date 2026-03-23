from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
GENERATED = ROOT / "generated" / "windows_preview"
TILE_DIR = GENERATED / "env_tiles"
WORLD_W = 24
WORLD_H = 24
CELL_SIZE = 1.45

TILES = [
    ("brass_cobbles_clean", (149, 119, 62), (225, 196, 123), "brick"),
    ("brass_cobbles_wet", (99, 87, 70), (173, 149, 109), "brick"),
    ("wax_brick_wall", (142, 103, 51), (216, 170, 84), "brick"),
    ("crypt_stone_large", (92, 100, 111), (162, 173, 182), "slab"),
    ("crypt_stone_small", (74, 80, 90), (142, 149, 160), "brick"),
    ("sewer_moss_grate", (52, 86, 61), (130, 163, 115), "grate"),
    ("rusted_plate_floor", (109, 75, 58), (178, 125, 97), "plate"),
    ("wax_resin_planks", (95, 64, 33), (166, 122, 78), "plank"),
    ("ash_flagstone", (106, 99, 94), (186, 178, 168), "slab"),
    ("fungal_silt_ground", (78, 96, 58), (152, 176, 122), "grain"),
    ("bone_inlay_stone", (114, 108, 96), (211, 198, 174), "slab"),
    ("apiary_hex_pavers", (143, 121, 64), (213, 191, 106), "hex"),
    ("machine_conduit_floor", (72, 87, 104), (141, 165, 188), "plate"),
    ("catwalk_mesh_floor", (84, 99, 106), (158, 182, 189), "grate"),
    ("salt_streak_concrete", (122, 119, 116), (200, 197, 192), "grain"),
    ("mural_ceramic_fragments", (98, 112, 129), (190, 168, 132), "chip"),
    ("obsidian_shard_ground", (34, 39, 50), (89, 96, 111), "shard"),
    ("ivy_brass_lattice", (64, 105, 72), (176, 157, 92), "hex"),
    ("tar_blackened_brick", (48, 41, 38), (110, 82, 64), "brick"),
    ("wet_ropewood_deck", (97, 73, 54), (174, 135, 103), "plank"),
    ("beeswax_mosaic", (163, 136, 68), (236, 205, 118), "hex"),
    ("storm_drain_grit", (90, 97, 88), (164, 170, 154), "grain"),
    ("chalk_sigil_floor", (93, 90, 104), (208, 204, 214), "sigil"),
    ("copper_pipe_crossing", (111, 81, 53), (188, 145, 103), "pipe"),
    ("lantern_glass_fragments", (84, 95, 100), (204, 186, 124), "glass"),
]

POINT_LIGHTS = [
    {"name": "altar_slot", "x": 0.0, "y": 2.6, "z": 26.0, "r": 1.0, "g": 0.82, "b": 0.46, "intensity": 1.55, "radius": 10.5},
    {"name": "sewer_lantern_left", "x": -7.0, "y": 2.1, "z": 11.0, "r": 0.48, "g": 0.86, "b": 0.75, "intensity": 0.9, "radius": 7.0},
    {"name": "sewer_lantern_right", "x": 7.2, "y": 2.1, "z": 13.0, "r": 0.55, "g": 0.72, "b": 0.95, "intensity": 0.82, "radius": 7.4},
    {"name": "brazier", "x": -4.0, "y": 1.7, "z": 22.5, "r": 1.0, "g": 0.48, "b": 0.18, "intensity": 0.95, "radius": 6.2},
]


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def tile_index(x: int, z: int, height: float, slope: float) -> int:
    if z > WORLD_H - 5:
        return 20
    if slope > 0.72:
        return 16
    if height < -0.55:
        return 9
    if height < -0.18:
        return 5 if (x + z) % 2 == 0 else 21
    if height < 0.08:
        return 3 if z % 3 == 0 else 4
    if height < 0.42:
        return 11 if (x + z) % 4 == 0 else 0
    if height < 0.78:
        return 14 if x % 3 == 0 else 8
    return 17 if x % 2 == 0 else 22


def height_at(x: int, z: int) -> float:
    nx = (x - WORLD_W * 0.5) / WORLD_W
    nz = z / WORLD_H
    ridge = math.sin(nx * math.pi * 2.4) * 0.35
    basin = -math.cos(nz * math.pi) * 0.55
    ramp = (nz - 0.45) * 0.85
    causeway = math.exp(-((nx * 3.1) ** 2)) * 0.52
    return ridge + basin + ramp + causeway


def build_height_grid() -> tuple[list[float], list[int]]:
    heights = []
    tiles = []
    for z in range(WORLD_H):
        for x in range(WORLD_W):
            center = height_at(x, z)
            dx = height_at(min(WORLD_W - 1, x + 1), z) - height_at(max(0, x - 1), z)
            dz = height_at(x, min(WORLD_H - 1, z + 1)) - height_at(x, max(0, z - 1))
            slope = math.sqrt(dx * dx + dz * dz)
            heights.append(round(center, 5))
            tiles.append(tile_index(x, z, center, slope))
    return heights, tiles


def draw_tile_pattern(name: str, base: tuple[int, int, int], accent: tuple[int, int, int], pattern: str) -> Image.Image:
    image = Image.new("RGBA", (128, 128), (*base, 255))
    draw = ImageDraw.Draw(image)
    if pattern == "brick":
        for y in range(0, 128, 16):
            offset = 8 if (y // 16) % 2 else 0
            draw.line((0, y, 127, y), fill=accent, width=2)
            for x in range(offset, 128, 32):
                draw.line((x, y, x, min(127, y + 16)), fill=accent, width=2)
    elif pattern == "slab":
        for y in range(0, 128, 32):
            draw.line((0, y, 127, y), fill=accent, width=3)
        for x in range(0, 128, 48):
            draw.line((x, 0, x, 127), fill=accent, width=3)
    elif pattern == "grate":
        for step in range(-128, 128, 16):
            draw.line((step, 0, step + 128, 128), fill=accent, width=2)
            draw.line((step + 128, 0, step, 128), fill=accent, width=2)
    elif pattern == "plate":
        for y in range(0, 128, 32):
            draw.rectangle((0, y, 127, min(127, y + 28)), outline=accent, width=2)
            for x in range(10, 118, 28):
                draw.ellipse((x, y + 8, x + 6, y + 14), fill=accent)
    elif pattern == "plank":
        for x in range(0, 128, 18):
            draw.line((x, 0, x, 127), fill=accent, width=2)
        for y in range(6, 128, 26):
            draw.line((0, y, 127, y + 8), fill=(*accent, 180), width=1)
    elif pattern == "grain":
        for i in range(0, 128, 6):
            draw.arc((i - 32, 12, i + 32, 44), 10, 160, fill=accent, width=1)
            draw.arc((i - 12, 62, i + 28, 88), 15, 165, fill=accent, width=1)
    elif pattern == "hex":
        for y in range(0, 128, 22):
            for x in range(0, 128, 24):
                ox = 12 if (y // 22) % 2 else 0
                cx = x + ox
                points = [(cx + 6, y), (cx + 18, y), (cx + 24, y + 11), (cx + 18, y + 22), (cx + 6, y + 22), (cx, y + 11)]
                draw.polygon(points, outline=accent)
    elif pattern == "chip":
        for x in range(0, 128, 22):
            for y in range(0, 128, 22):
                draw.polygon([(x + 4, y + 2), (x + 18, y + 6), (x + 14, y + 19), (x + 2, y + 14)], outline=accent)
    elif pattern == "shard":
        for x in range(0, 128, 18):
            draw.polygon([(x + 4, 8), (x + 15, 18), (x + 7, 30)], fill=(*accent, 140))
            draw.polygon([(x + 8, 56), (x + 18, 72), (x + 3, 84)], fill=(*accent, 120))
    elif pattern == "sigil":
        draw.ellipse((22, 22, 106, 106), outline=accent, width=3)
        draw.line((64, 16, 64, 112), fill=accent, width=2)
        draw.line((16, 64, 112, 64), fill=accent, width=2)
        draw.line((28, 28, 100, 100), fill=accent, width=2)
        draw.line((100, 28, 28, 100), fill=accent, width=2)
    elif pattern == "pipe":
        draw.rectangle((0, 54, 127, 74), fill=accent)
        draw.rectangle((54, 0, 74, 127), fill=accent)
        draw.ellipse((44, 44, 84, 84), outline=(255, 255, 255), width=2)
    elif pattern == "glass":
        for x in range(8, 128, 20):
            draw.polygon([(x, 18), (x + 12, 24), (x + 6, 42)], fill=(*accent, 140))
            draw.polygon([(x + 4, 68), (x + 16, 76), (x + 8, 94)], fill=(*accent, 160))
    return image


def emit_world_header(heights: list[float], tiles: list[int], object_spawns: list[dict], enemy_spawns: list[dict]) -> None:
    lines = [
        "#pragma once",
        "",
        f"#define PREVIEW_WORLD_W {WORLD_W}",
        f"#define PREVIEW_WORLD_H {WORLD_H}",
        f"#define PREVIEW_TILE_COUNT {len(TILES)}",
        f"#define PREVIEW_POINT_LIGHT_COUNT {len(POINT_LIGHTS)}",
        f"#define PREVIEW_OBJECT_COUNT {len(object_spawns)}",
        f"#define PREVIEW_ENEMY_COUNT {len(enemy_spawns)}",
        "",
        "static const PreviewTileDef kPreviewTiles[PREVIEW_TILE_COUNT] = {",
    ]
    for name, base, accent, pattern in TILES:
        lines.append(
            f'    {{"{name}", {base[0]}, {base[1]}, {base[2]}, {accent[0]}, {accent[1]}, {accent[2]}, "{pattern}"}},'
        )
    lines.extend([
        "};",
        "",
        "static const float kPreviewWorldHeights[PREVIEW_WORLD_W * PREVIEW_WORLD_H] = {",
    ])
    for row in range(WORLD_H):
        chunk = ", ".join(f"{heights[row * WORLD_W + col]:.5f}f" for col in range(WORLD_W))
        lines.append(f"    {chunk},")
    lines.extend([
        "};",
        "",
        "static const unsigned char kPreviewWorldTiles[PREVIEW_WORLD_W * PREVIEW_WORLD_H] = {",
    ])
    for row in range(WORLD_H):
        chunk = ", ".join(str(tiles[row * WORLD_W + col]) for col in range(WORLD_W))
        lines.append(f"    {chunk},")
    lines.extend([
        "};",
        "",
        "static const PreviewPointLightDef kPreviewPointLights[PREVIEW_POINT_LIGHT_COUNT] = {",
    ])
    for light in POINT_LIGHTS:
        lines.append(
            f'    {{"{light["name"]}", {light["x"]:.3f}f, {light["y"]:.3f}f, {light["z"]:.3f}f, {light["r"]:.3f}f, {light["g"]:.3f}f, {light["b"]:.3f}f, {light["intensity"]:.3f}f, {light["radius"]:.3f}f}},'
        )
    lines.extend([
        "};",
        "",
        "static const PreviewObjectSpawnDef kPreviewObjectSpawns[PREVIEW_OBJECT_COUNT] = {",
    ])
    for obj in object_spawns:
        lines.append(
            f'    {{"{obj["name"]}", {obj["x"]:.3f}f, {obj["z"]:.3f}f, {obj["half_x"]:.3f}f, {obj["half_y"]:.3f}f, {obj["half_z"]:.3f}f, {1 if obj["interactive"] else 0}, {1 if obj["solid"] else 0}, {obj["kind"]}}},'
        )
    lines.extend([
        "};",
        "",
        "static const PreviewEnemySpawnDef kPreviewEnemySpawns[PREVIEW_ENEMY_COUNT] = {",
    ])
    for enemy in enemy_spawns:
        lines.append(
            f'    {{"{enemy["name"]}", {enemy["x"]:.3f}f, {enemy["z"]:.3f}f, {enemy["health"]:.3f}f, {enemy["speed"]:.3f}f, {enemy["kind"]}}},'
        )
    lines.extend([
        "};",
        "",
        "static const float kPreviewCellSize = 1.45f;",
        "static const float kPreviewPlayerSpawn[3] = {0.0f, 0.0f, 5.0f};",
        "static const float kPreviewGoalSlot[3] = {0.0f, 0.0f, 26.0f};",
        "static const float kPreviewObjectiveDrop[3] = {0.0f, 0.0f, 20.0f};",
    ])
    (GENERATED / "generated_preview_world.h").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    GENERATED.mkdir(parents=True, exist_ok=True)
    TILE_DIR.mkdir(parents=True, exist_ok=True)

    heights, tiles = build_height_grid()

    for name, base, accent, pattern in TILES:
        draw_tile_pattern(name, base, accent, pattern).save(TILE_DIR / f"{name}.png")

    object_spawns = [
        {"name": "slot_altar", "x": 0.0, "z": 26.0, "half_x": 1.1, "half_y": 1.8, "half_z": 1.1, "interactive": True, "solid": True, "kind": 2},
        {"name": "wax_crate_a", "x": -3.6, "z": 9.8, "half_x": 0.8, "half_y": 0.7, "half_z": 0.8, "interactive": False, "solid": True, "kind": 0},
        {"name": "wax_crate_b", "x": 3.2, "z": 12.0, "half_x": 0.7, "half_y": 0.8, "half_z": 0.7, "interactive": False, "solid": True, "kind": 0},
        {"name": "brazier", "x": -4.0, "z": 22.5, "half_x": 0.6, "half_y": 1.2, "half_z": 0.6, "interactive": True, "solid": True, "kind": 1},
        {"name": "lantern_post", "x": 6.4, "z": 15.6, "half_x": 0.4, "half_y": 1.8, "half_z": 0.4, "interactive": True, "solid": True, "kind": 1},
        {"name": "supply_cache", "x": 0.8, "z": 19.2, "half_x": 0.9, "half_y": 0.7, "half_z": 0.9, "interactive": True, "solid": True, "kind": 3},
    ]
    enemy_spawns = [
        {"name": "gutter_ghoul_a", "x": -2.2, "z": 13.2, "health": 24.0, "speed": 0.045, "kind": 0},
        {"name": "gutter_ghoul_b", "x": 2.4, "z": 15.0, "health": 24.0, "speed": 0.048, "kind": 0},
        {"name": "wax_knight", "x": -4.8, "z": 18.4, "health": 34.0, "speed": 0.042, "kind": 1},
        {"name": "slot_guardian", "x": 4.6, "z": 21.5, "health": 42.0, "speed": 0.038, "kind": 2},
    ]
    emit_world_header(heights, tiles, object_spawns, enemy_spawns)

    save_json(
        GENERATED / "demo_world.json",
        {
            "world_size": [WORLD_W, WORLD_H],
            "cell_size": CELL_SIZE,
            "tiles": [{"name": name, "base": base, "accent": accent, "pattern": pattern} for name, base, accent, pattern in TILES],
            "point_lights": POINT_LIGHTS,
            "object_spawns": object_spawns,
            "enemy_spawns": enemy_spawns,
            "goal_slot": {"x": 0.0, "z": 26.0},
            "objective_drop": {"x": 0.0, "z": 20.0},
            "heights": heights,
            "terrain_tiles": tiles,
        },
    )
    print("Built demo world assets and preview terrain data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())