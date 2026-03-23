from __future__ import annotations

import argparse
import json
import math
from collections import deque
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RIGS = ROOT / "rigs" / "entity_rigs.json"
ALPHA_EMPTY_THRESHOLD = 12
SOFT_DELTA_E = 8.0
HARD_DELTA_E = 14.0
SEGMENT_DELTA_E = 12.5
NEIGHBOR_STENCIL_32 = [
    (-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1),
    (-2, -2), (0, -2), (2, -2), (-2, 0), (2, 0), (-2, 2), (0, 2), (2, 2),
    (-2, -1), (-1, -2), (1, -2), (2, -1), (-2, 1), (-1, 2), (1, 2), (2, 1),
    (0, -3), (-1, -3), (1, -3), (-3, 0), (3, 0), (0, 3), (-1, 3), (1, 3),
]


def clamp(value: float, lo: float, hi: float) -> float:
    return lo if value < lo else hi if value > hi else value


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def srgb_to_linear(channel: int) -> float:
    value = channel / 255.0
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def rgb_to_lab(red: int, green: int, blue: int) -> tuple[float, float, float]:
    r = srgb_to_linear(red)
    g = srgb_to_linear(green)
    b = srgb_to_linear(blue)

    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    x /= 0.95047
    y /= 1.00000
    z /= 1.08883

    def f(value: float) -> float:
        if value > 0.008856:
            return value ** (1.0 / 3.0)
        return 7.787 * value + 16.0 / 116.0

    fx = f(x)
    fy = f(y)
    fz = f(z)
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def delta_e(lab_a: tuple[float, float, float], lab_b: tuple[float, float, float]) -> float:
    return math.sqrt(
        (lab_a[0] - lab_b[0]) ** 2 +
        (lab_a[1] - lab_b[1]) ** 2 +
        (lab_a[2] - lab_b[2]) ** 2
    )


def luminance(rgba: tuple[int, int, int, int]) -> float:
    red, green, blue, _ = rgba
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def alpha_state(alpha: int) -> str:
    if alpha < ALPHA_EMPTY_THRESHOLD:
        return "empty"
    if alpha < 255:
        return "partial"
    return "solid"


def classify_boundary(alpha: int, min_neighbor_alpha: int, max_neighbor_delta_e: float, edge_confidence: float) -> str:
    if alpha < ALPHA_EMPTY_THRESHOLD:
        return "empty_space"
    if min_neighbor_alpha < ALPHA_EMPTY_THRESHOLD:
        return "silhouette_boundary"
    if max_neighbor_delta_e >= HARD_DELTA_E:
        return "hard_material_transition"
    if max_neighbor_delta_e >= SOFT_DELTA_E:
        return "soft_material_transition"
    if edge_confidence > 0.33:
        return "highlight_boundary"
    return "interior_stable_fill"


def neighbors8(x: int, y: int, width: int, height: int):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx = x + dx
            ny = y + dy
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny


def compute_distance_to_empty(alpha_matrix: list[list[int]]) -> list[list[int]]:
    height = len(alpha_matrix)
    width = len(alpha_matrix[0]) if height else 0
    distances = [[10 ** 9 for _ in range(width)] for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()

    for y in range(height):
        for x in range(width):
            if alpha_matrix[y][x] < ALPHA_EMPTY_THRESHOLD:
                distances[y][x] = 0
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        current = distances[y][x]
        for nx, ny in neighbors8(x, y, width, height):
            if distances[ny][nx] > current + 1:
                distances[ny][nx] = current + 1
                queue.append((nx, ny))

    return distances


def segment_regions(rgba_rows: list[list[tuple[int, int, int, int]]], lab_rows: list[list[tuple[float, float, float]]]) -> tuple[list[list[int]], list[dict]]:
    height = len(rgba_rows)
    width = len(rgba_rows[0]) if height else 0
    region_map = [[-1 for _ in range(width)] for _ in range(height)]
    regions: list[dict] = []

    for y in range(height):
        for x in range(width):
            if region_map[y][x] >= 0 or rgba_rows[y][x][3] < ALPHA_EMPTY_THRESHOLD:
                continue

            region_id = len(regions)
            queue: deque[tuple[int, int]] = deque([(x, y)])
            region_map[y][x] = region_id
            pixels: list[tuple[int, int]] = []
            seed_lab = lab_rows[y][x]

            while queue:
                px, py = queue.popleft()
                pixels.append((px, py))
                for nx, ny in neighbors8(px, py, width, height):
                    if region_map[ny][nx] >= 0:
                        continue
                    if rgba_rows[ny][nx][3] < ALPHA_EMPTY_THRESHOLD:
                        continue
                    if delta_e(seed_lab, lab_rows[ny][nx]) <= SEGMENT_DELTA_E:
                        region_map[ny][nx] = region_id
                        queue.append((nx, ny))

            xs = [p[0] for p in pixels]
            ys = [p[1] for p in pixels]
            regions.append({
                "region_id": region_id,
                "pixel_count": len(pixels),
                "bounding_box": [min(xs), min(ys), max(xs) + 1, max(ys) + 1],
                "pixels": pixels,
            })

    return region_map, regions


def infer_material_family(red: int, green: int, blue: int) -> str:
    if red > 180 and green > 160 and blue < 120:
        return "brass_or_honey"
    if red < 90 and green < 90 and blue < 90:
        return "shadow_or_machine"
    if blue > red + 30 and blue > green + 20:
        return "cloth_or_arcana"
    if green > red + 15 and green > blue:
        return "flora_or_growth"
    return "organic_or_mixed_surface"


def infer_deformation_type(category: str) -> str:
    if category in {"player", "companion", "npc", "enemy", "enemy_elite", "boss", "wildlife"}:
        return "bone_owned_deforming_volume"
    if category in {"world", "interactable"}:
        return "rigid_volume"
    if category == "fx":
        return "emissive_only"
    return "screen_space_only"


def select_category_color(category: str) -> tuple[int, int, int]:
    palette = {
        "player": (255, 160, 80),
        "companion": (80, 220, 220),
        "npc": (210, 210, 120),
        "enemy": (220, 80, 100),
        "enemy_elite": (240, 120, 50),
        "boss": (220, 80, 220),
        "world": (100, 160, 210),
        "interactable": (180, 180, 180),
        "wildlife": (90, 200, 120),
        "fx": (255, 255, 255),
        "ui": (220, 220, 220),
    }
    return palette.get(category, (255, 255, 255))


def nearest_bone_name(entity: str | None, centroid: tuple[float, float], image_size: tuple[int, int], rig_lookup: dict[str, dict]) -> str | None:
    if not entity or entity not in rig_lookup:
        return None
    rig = rig_lookup[entity]
    width, height = image_size
    origin_x = width * 0.5
    origin_y = height * 0.7
    best_name = None
    best_dist = float("inf")
    for bone in rig.get("bones", []):
        bone_x = origin_x + float(bone.get("x", 0.0))
        bone_y = origin_y - float(bone.get("y", 0.0))
        dist = math.hypot(centroid[0] - bone_x, centroid[1] - bone_y)
        if dist < best_dist:
            best_dist = dist
            best_name = bone["name"]
    return best_name


def build_symbol_objects(regions: list[dict], rgba_rows, distance_map, category: str, entity: str | None, rig_lookup: dict[str, dict], image_size: tuple[int, int]) -> list[dict]:
    result: list[dict] = []
    category_color = select_category_color(category)
    for region in regions:
        region_id = region["region_id"]
        pixels = region["pixels"]
        colors = [rgba_rows[y][x] for x, y in pixels]
        avg_r = sum(p[0] for p in colors) / len(colors)
        avg_g = sum(p[1] for p in colors) / len(colors)
        avg_b = sum(p[2] for p in colors) / len(colors)
        centroid_x = sum(x for x, _ in pixels) / len(pixels)
        centroid_y = sum(y for _, y in pixels) / len(pixels)
        thickness_hint = sum(distance_map[y][x] for x, y in pixels) / len(pixels)
        nearest_bone = nearest_bone_name(entity, (centroid_x, centroid_y), image_size, rig_lookup)
        bbox = region["bounding_box"]
        result.append({
            "symbol_id": f"symbol_{region_id:04d}",
            "parent_symbol_id": None,
            "category": category,
            "bounding_box": bbox,
            "pixel_count": len(pixels),
            "boundary_contour": [bbox[0], bbox[1], bbox[2] - 1, bbox[3] - 1],
            "centroid": [round(centroid_x, 3), round(centroid_y, 3)],
            "primary_color_family": [round(avg_r, 3), round(avg_g, 3), round(avg_b, 3)],
            "material_family": infer_material_family(int(avg_r), int(avg_g), int(avg_b)),
            "thickness_hint": round(thickness_hint, 3),
            "pivot_candidates": [[round(centroid_x, 3), float(bbox[3] - 1)]],
            "socket_candidates": [[round(centroid_x, 3), round(centroid_y, 3)]],
            "collision_type": "silhouette_hull",
            "deformation_type": infer_deformation_type(category),
            "adjacent_symbol_ids": [],
            "occlusion_order_hint": round(centroid_y / max(1, image_size[1]), 4),
            "nearest_rig_bone": nearest_bone,
            "analysis_color": list(category_color),
        })
    return result


def write_region_preview(region_map: list[list[int]], category: str, path: Path) -> None:
    height = len(region_map)
    width = len(region_map[0]) if height else 0
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    base_color = select_category_color(category)
    for y in range(height):
        for x in range(width):
            region_id = region_map[y][x]
            if region_id < 0:
                pixels[x, y] = (0, 0, 0, 0)
            else:
                pixels[x, y] = (
                    (base_color[0] + region_id * 43) % 256,
                    (base_color[1] + region_id * 71) % 256,
                    (base_color[2] + region_id * 97) % 256,
                    255,
                )
    image.save(path)


def write_depth_map(rgba_rows, distance_map, region_map, path: Path) -> list[list[float]]:
    height = len(rgba_rows)
    width = len(rgba_rows[0]) if height else 0
    image = Image.new("L", (width, height), 0)
    pixels = image.load()
    values: list[list[float]] = []
    max_distance = max(max(row) for row in distance_map) if distance_map else 1
    for y in range(height):
        row_values: list[float] = []
        for x in range(width):
            rgba = rgba_rows[y][x]
            if rgba[3] < ALPHA_EMPTY_THRESHOLD or region_map[y][x] < 0:
                pixels[x, y] = 0
                row_values.append(0.0)
                continue
            shade = luminance(rgba) / 255.0
            dist_component = distance_map[y][x] / max(1, max_distance)
            value = clamp(shade * 0.55 + dist_component * 0.45, 0.0, 1.0)
            pixels[x, y] = int(round(value * 255.0))
            row_values.append(round(value, 4))
        values.append(row_values)
    image.save(path)
    return values


def scalar_field_to_image(values: list[list[float]], alpha_rows: list[list[int]], path: Path) -> None:
    height = len(values)
    width = len(values[0]) if height else 0
    image = Image.new("L", (width, height), 0)
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            if alpha_rows[y][x] < ALPHA_EMPTY_THRESHOLD:
                pixels[x, y] = 0
            else:
                pixels[x, y] = int(round(clamp(values[y][x], 0.0, 1.0) * 255.0))
    image.save(path)


def sample_field(values: list[list[float]], sample_x: float, sample_y: float) -> float:
    height = len(values)
    width = len(values[0]) if height else 0
    if width == 0 or height == 0:
        return 0.0
    x = clamp(sample_x, 0.0, float(width - 1))
    y = clamp(sample_y, 0.0, float(height - 1))
    x0 = int(math.floor(x))
    y0 = int(math.floor(y))
    x1 = min(width - 1, x0 + 1)
    y1 = min(height - 1, y0 + 1)
    tx = x - x0
    ty = y - y0
    v00 = values[y0][x0]
    v10 = values[y0][x1]
    v01 = values[y1][x0]
    v11 = values[y1][x1]
    vx0 = v00 * (1.0 - tx) + v10 * tx
    vx1 = v01 * (1.0 - tx) + v11 * tx
    return vx0 * (1.0 - ty) + vx1 * ty


def resample_field(values: list[list[float]], target_width: int, target_height: int) -> list[list[float]]:
    if not values or not values[0]:
        return [[0.0 for _ in range(target_width)] for _ in range(target_height)]
    source_height = len(values)
    source_width = len(values[0])
    result: list[list[float]] = []
    for y in range(target_height):
        sample_y = 0.0 if target_height <= 1 else (y / (target_height - 1)) * (source_height - 1)
        row: list[float] = []
        for x in range(target_width):
            sample_x = 0.0 if target_width <= 1 else (x / (target_width - 1)) * (source_width - 1)
            row.append(sample_field(values, sample_x, sample_y))
        result.append(row)
    return result


def build_material_response_fields(depth_values: list[list[float]], alpha_rows: list[list[int]], distance_map: list[list[int]]) -> dict[str, list[list[float]]]:
    height = len(depth_values)
    width = len(depth_values[0]) if height else 0
    max_distance = max(max(row) for row in distance_map) if distance_map else 1
    fiber_field: list[list[float]] = []
    elasticity_field: list[list[float]] = []
    bump_field: list[list[float]] = []
    curvature_field: list[list[float]] = []
    normal_vectors: list[list[tuple[float, float, float]]] = []

    omni_dirs = [
        (1, 0), (0.7071, 0.7071), (0, 1), (-0.7071, 0.7071),
        (-1, 0), (-0.7071, -0.7071), (0, -1), (0.7071, -0.7071),
    ]

    for y in range(height):
        fiber_row: list[float] = []
        elasticity_row: list[float] = []
        bump_row: list[float] = []
        curvature_row: list[float] = []
        normal_row: list[tuple[float, float, float]] = []
        for x in range(width):
            if alpha_rows[y][x] < ALPHA_EMPTY_THRESHOLD:
                fiber_row.append(0.0)
                elasticity_row.append(0.0)
                bump_row.append(0.0)
                curvature_row.append(0.0)
                normal_row.append((0.0, 0.0, 1.0))
                continue

            left = sample_field(depth_values, x - 1.0, y)
            right = sample_field(depth_values, x + 1.0, y)
            up = sample_field(depth_values, x, y - 1.0)
            down = sample_field(depth_values, x, y + 1.0)
            center = depth_values[y][x]

            grad_x = (right - left) * 0.5
            grad_y = (down - up) * 0.5
            grad_mag = math.sqrt(grad_x * grad_x + grad_y * grad_y)
            curvature = (left + right + up + down - 4.0 * center)

            omni_energy = 0.0
            for dx, dy in omni_dirs:
                outer = sample_field(depth_values, x + dx * 2.0, y + dy * 2.0)
                inner = sample_field(depth_values, x - dx * 2.0, y - dy * 2.0)
                omni_energy += abs(outer - inner)
            omni_energy /= float(len(omni_dirs))

            distance_norm = distance_map[y][x] / max(1.0, float(max_distance))
            fiber_strength = clamp(grad_mag * 2.35 + abs(curvature) * 1.65 + omni_energy * 1.40, 0.0, 1.0)
            elasticity = clamp(distance_norm * 0.48 + (1.0 - clamp(abs(curvature) * 2.4, 0.0, 1.0)) * 0.22 + (1.0 - clamp(grad_mag * 2.0, 0.0, 1.0)) * 0.15 + omni_energy * 0.15, 0.0, 1.0)
            bump = clamp(fiber_strength * 0.55 + abs(curvature) * 1.25 + grad_mag * 0.45, 0.0, 1.0)

            normal_x = -grad_x * 2.0
            normal_y = -grad_y * 2.0
            normal_z = 1.0
            normal_len = math.sqrt(normal_x * normal_x + normal_y * normal_y + normal_z * normal_z)
            normal_row.append((normal_x / normal_len, normal_y / normal_len, normal_z / normal_len))
            fiber_row.append(round(fiber_strength, 6))
            elasticity_row.append(round(elasticity, 6))
            bump_row.append(round(bump, 6))
            curvature_row.append(round(clamp(abs(curvature) * 4.0, 0.0, 1.0), 6))
        fiber_field.append(fiber_row)
        elasticity_field.append(elasticity_row)
        bump_field.append(bump_row)
        curvature_field.append(curvature_row)
        normal_vectors.append(normal_row)

    return {
        "fiber": fiber_field,
        "elasticity": elasticity_field,
        "bump": bump_field,
        "curvature": curvature_field,
        "normals": normal_vectors,
    }


def write_normal_map(normal_vectors: list[list[tuple[float, float, float]]], alpha_rows: list[list[int]], path: Path) -> None:
    height = len(normal_vectors)
    width = len(normal_vectors[0]) if height else 0
    image = Image.new("RGBA", (width, height), (128, 128, 255, 0))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            if alpha_rows[y][x] < ALPHA_EMPTY_THRESHOLD:
                pixels[x, y] = (128, 128, 255, 0)
                continue
            nx, ny, nz = normal_vectors[y][x]
            pixels[x, y] = (
                int(round((nx * 0.5 + 0.5) * 255.0)),
                int(round((ny * 0.5 + 0.5) * 255.0)),
                int(round((nz * 0.5 + 0.5) * 255.0)),
                255,
            )
    image.save(path)


def summarize_volume_layers(depth_values: list[list[float]], alpha_rows: list[list[int]], elasticity_values: list[list[float]], layer_count: int = 140) -> dict:
    bucket_counts = [0 for _ in range(layer_count)]
    bucket_elasticity = [0.0 for _ in range(layer_count)]
    solid_pixels = 0
    for y, row in enumerate(depth_values):
        for x, value in enumerate(row):
            if alpha_rows[y][x] < ALPHA_EMPTY_THRESHOLD:
                continue
            solid_pixels += 1
            bucket = int(round(clamp(value, 0.0, 1.0) * float(layer_count - 1)))
            bucket_counts[bucket] += 1
            bucket_elasticity[bucket] += elasticity_values[y][x]

    layers = []
    cumulative_coverage = 0
    for index in range(layer_count - 1, -1, -1):
        cumulative_coverage += bucket_counts[index]
        layers.append({
            "layer_index": index,
            "normalized_depth": round(index / max(1, layer_count - 1), 6),
            "coverage_pixels": cumulative_coverage,
            "coverage_ratio": round(cumulative_coverage / max(1, solid_pixels), 6),
            "shell_pixels": bucket_counts[index],
            "mean_elasticity": round(bucket_elasticity[index] / max(1, bucket_counts[index]), 6),
        })
    layers.reverse()
    return {"layer_count": layer_count, "solid_pixel_count": solid_pixels, "layers": layers}


def write_volume_layer_preview(depth_values: list[list[float]], alpha_rows: list[list[int]], path: Path, layer_count: int = 140) -> None:
    cols = 14
    rows = 10
    cell = 16
    depth_small = resample_field(depth_values, cell, cell)
    alpha_small = resample_field([[1.0 if alpha >= ALPHA_EMPTY_THRESHOLD else 0.0 for alpha in row] for row in alpha_rows], cell, cell)
    image = Image.new("L", (cols * cell, rows * cell), 0)
    pixels = image.load()
    for layer in range(layer_count):
        ox = (layer % cols) * cell
        oy = (layer // cols) * cell
        threshold = layer / max(1, layer_count - 1)
        for y in range(cell):
            for x in range(cell):
                occupied = alpha_small[y][x] > 0.05 and depth_small[y][x] >= threshold
                pixels[ox + x, oy + y] = 255 if occupied else 0
    image.save(path)


def find_solid_bounds(alpha_rows: list[list[int]]) -> tuple[int, int, int, int]:
    height = len(alpha_rows)
    width = len(alpha_rows[0]) if height else 0
    xs = []
    ys = []
    for y in range(height):
        for x in range(width):
            if alpha_rows[y][x] >= ALPHA_EMPTY_THRESHOLD:
                xs.append(x)
                ys.append(y)
    if not xs or not ys:
        return (0, 0, max(1, width), max(1, height))
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def estimate_dense_shell_resolution(width: int, height: int, polygon_target: int) -> tuple[int, int]:
    aspect = width / max(1.0, float(height))
    surface_budget = polygon_target / 2.0
    grid_width = max(18, int(round(math.sqrt(surface_budget * max(0.2, aspect))))) + 1
    grid_height = max(18, int(round(math.sqrt(surface_budget / max(0.2, aspect))))) + 1
    return grid_width, grid_height


def write_dense_shell_obj(depth_values: list[list[float]], alpha_rows: list[list[int]], fiber_values: list[list[float]], elasticity_values: list[list[float]], path: Path, polygon_target: int = 10000) -> dict:
    min_x, min_y, max_x, max_y = find_solid_bounds(alpha_rows)
    source_width = max(1, max_x - min_x)
    source_height = max(1, max_y - min_y)
    grid_width, grid_height = estimate_dense_shell_resolution(source_width, source_height, polygon_target)

    depth_crop = [row[min_x:max_x] for row in depth_values[min_y:max_y]]
    alpha_crop = [[1.0 if alpha >= ALPHA_EMPTY_THRESHOLD else 0.0 for alpha in row[min_x:max_x]] for row in alpha_rows[min_y:max_y]]
    fiber_crop = [row[min_x:max_x] for row in fiber_values[min_y:max_y]]
    elasticity_crop = [row[min_x:max_x] for row in elasticity_values[min_y:max_y]]

    depth_grid = resample_field(depth_crop, grid_width, grid_height)
    alpha_grid = resample_field(alpha_crop, grid_width, grid_height)
    fiber_grid = resample_field(fiber_crop, grid_width, grid_height)
    elasticity_grid = resample_field(elasticity_crop, grid_width, grid_height)

    aspect = source_width / max(1.0, float(source_height))
    front_index = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
    back_index = [[0 for _ in range(grid_width)] for _ in range(grid_height)]
    vertices: list[tuple[float, float, float]] = []
    uv_coords: list[tuple[float, float]] = []
    faces: list[list[int]] = []

    def add_vertex(px: float, py: float, pz: float, u: float, v: float) -> int:
        vertices.append((px, py, pz))
        uv_coords.append((u, v))
        return len(vertices)

    for y in range(grid_height):
        ty = 0.0 if grid_height <= 1 else y / (grid_height - 1)
        for x in range(grid_width):
            tx = 0.0 if grid_width <= 1 else x / (grid_width - 1)
            alpha = alpha_grid[y][x]
            depth = depth_grid[y][x]
            fiber = fiber_grid[y][x]
            elasticity = elasticity_grid[y][x]
            thickness = (0.035 + depth * 0.20 + fiber * 0.045) * alpha
            px = (tx - 0.5) * aspect * 2.0
            py = (0.5 - ty) * 2.0
            front_z = thickness * (0.55 + elasticity * 0.35)
            back_z = -thickness * (0.45 + (1.0 - elasticity) * 0.15)
            front_index[y][x] = add_vertex(px, py, front_z, tx, ty)
            back_index[y][x] = add_vertex(px, py, back_z, tx, ty)

    def occupied(cx: int, cy: int) -> bool:
        if not (0 <= cx < grid_width - 1 and 0 <= cy < grid_height - 1):
            return False
        mean_alpha = (alpha_grid[cy][cx] + alpha_grid[cy][cx + 1] + alpha_grid[cy + 1][cx] + alpha_grid[cy + 1][cx + 1]) * 0.25
        return mean_alpha > 0.05

    for y in range(grid_height - 1):
        for x in range(grid_width - 1):
            if not occupied(x, y):
                continue
            f00 = front_index[y][x]
            f10 = front_index[y][x + 1]
            f11 = front_index[y + 1][x + 1]
            f01 = front_index[y + 1][x]
            b00 = back_index[y][x]
            b10 = back_index[y][x + 1]
            b11 = back_index[y + 1][x + 1]
            b01 = back_index[y + 1][x]
            faces.append([f00, f10, f11, f01])
            faces.append([b01, b11, b10, b00])
            if not occupied(x - 1, y):
                faces.append([b00, f00, f01, b01])
            if not occupied(x + 1, y):
                faces.append([f10, b10, b11, f11])
            if not occupied(x, y - 1):
                faces.append([b00, b10, f10, f00])
            if not occupied(x, y + 1):
                faces.append([f01, f11, b11, b01])

    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"# Dense shell mesh generated from 2D asset field with target {polygon_target} polygons\n")
        for vx, vy, vz in vertices:
            handle.write(f"v {vx:.6f} {vy:.6f} {vz:.6f}\n")
        for u, v in uv_coords:
            handle.write(f"vt {u:.6f} {1.0 - v:.6f}\n")
        for face in faces:
            handle.write("f " + " ".join(f"{index}/{index}" for index in face) + "\n")

    return {
        "path": str(path),
        "polygon_target": polygon_target,
        "generated_polygon_count": len(faces),
        "grid_resolution": [grid_width, grid_height],
        "depth_layer_count": 140,
        "construction_method": "calculus_gradient_shell_with_omnidirectional_fibre_response",
    }


def build_pixel_matrix(rgba_rows, lab_rows, region_map, distance_map):
    height = len(rgba_rows)
    width = len(rgba_rows[0]) if height else 0
    matrix_rows = []
    for y in range(height):
        row = []
        for x in range(width):
            rgba = rgba_rows[y][x]
            center_lab = lab_rows[y][x]
            center_luma = luminance(rgba)
            max_delta = 0.0
            min_alpha = 255
            sum_dx = 0.0
            sum_dy = 0.0
            count = 0
            for dx, dy in NEIGHBOR_STENCIL_32:
                nx = x + dx
                ny = y + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                neighbor_rgba = rgba_rows[ny][nx]
                neighbor_lab = lab_rows[ny][nx]
                min_alpha = min(min_alpha, neighbor_rgba[3])
                max_delta = max(max_delta, delta_e(center_lab, neighbor_lab))
                sum_dx += dx * (luminance(neighbor_rgba) - center_luma)
                sum_dy += dy * (luminance(neighbor_rgba) - center_luma)
                count += 1
            grad_mag = math.sqrt(sum_dx * sum_dx + sum_dy * sum_dy) / max(1.0, count * 255.0)
            grad_dir = math.atan2(sum_dy, sum_dx) if grad_mag > 0.0 else 0.0
            edge_conf = clamp(max_delta / 35.0 + grad_mag * 0.35, 0.0, 1.0)
            row.append({
                "x": x,
                "y": y,
                "rgba": [rgba[0], rgba[1], rgba[2], rgba[3]],
                "linear_rgb": [round(srgb_to_linear(rgba[0]), 6), round(srgb_to_linear(rgba[1]), 6), round(srgb_to_linear(rgba[2]), 6)],
                "lab": [round(center_lab[0], 4), round(center_lab[1], 4), round(center_lab[2], 4)],
                "alpha_state": alpha_state(rgba[3]),
                "gradient_magnitude": round(grad_mag, 6),
                "gradient_direction": round(grad_dir, 6),
                "edge_confidence": round(edge_conf, 6),
                "region_id": region_map[y][x],
                "symbol_id": f"symbol_{region_map[y][x]:04d}" if region_map[y][x] >= 0 else None,
                "depth_hint": round(distance_map[y][x], 6),
                "surface_normal_hint": [round(math.cos(grad_dir), 5), round(math.sin(grad_dir), 5), round(1.0 - grad_mag, 5)],
                "boundary_state": classify_boundary(rgba[3], min_alpha, max_delta, edge_conf),
            })
        matrix_rows.append(row)
    return {
        "neighbor_stencil": [list(offset) for offset in NEIGHBOR_STENCIL_32],
        "rows": matrix_rows,
    }


def build_spatial_metrics(symbols: list[dict], image_size: tuple[int, int]) -> dict:
    width, height = image_size
    metrics = []
    for symbol in symbols:
        bbox = symbol["bounding_box"]
        box_width = bbox[2] - bbox[0]
        box_height = bbox[3] - bbox[1]
        thickness = symbol["thickness_hint"]
        metrics.append({
            "symbol_id": symbol["symbol_id"],
            "source_metrics": {
                "width_px": box_width,
                "height_px": box_height,
                "estimated_thickness_px": round(thickness, 4),
            },
            "normalized_metrics": {
                "width_norm": round(box_width / max(1, width), 6),
                "height_norm": round(box_height / max(1, height), 6),
                "thickness_norm": round(thickness / max(1, min(width, height)), 6),
            },
            "engine_space_hint": {
                "x_extent": round(box_width / 24.0, 5),
                "y_extent": round(box_height / 36.0, 5),
                "z_extent": round(max(1.0, thickness) / 24.0, 5),
            },
        })
    return {"image_size": [width, height], "symbols": metrics}


def build_mesh_contract(asset_name: str, category: str, symbols: list[dict], dense_shell_profile: dict | None = None) -> dict:
    return {
        "asset": asset_name,
        "category": category,
        "high_poly_profile": dense_shell_profile or {},
        "mesh_sections": [
            {
                "section_name": symbol["symbol_id"],
                "source_symbol": symbol["symbol_id"],
                "deformation_type": symbol["deformation_type"],
                "collision_type": symbol["collision_type"],
                "material_family": symbol["material_family"],
                "blockout_primitive": "capsule_or_box" if category in {"player", "companion", "npc", "enemy", "enemy_elite", "boss", "wildlife"} else "box_or_plane",
                "polygon_target": dense_shell_profile.get("polygon_target", 0) if dense_shell_profile else 0,
                "depth_layers": dense_shell_profile.get("depth_layer_count", 0) if dense_shell_profile else 0,
            }
            for symbol in symbols
        ],
    }


def build_surface_contract(asset_name: str, symbols: list[dict], material_maps: dict | None = None) -> dict:
    return {
        "asset": asset_name,
        "material_response_maps": material_maps or {},
        "materials": [
            {
                "symbol_id": symbol["symbol_id"],
                "material_family": symbol["material_family"],
                "base_color_hint": symbol["primary_color_family"],
                "height_texture_ready": True,
                "normal_hint_ready": True,
                "fiber_ready": True,
                "elasticity_ready": True,
                "omni_directional_spread": 1.0,
                "emissive_hint": symbol["material_family"] in {"cloth_or_arcana", "brass_or_honey"},
            }
            for symbol in symbols
        ],
    }


def build_rig_lookup(rigs: dict) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for skeleton in rigs.get("skeletons", []):
        lookup[skeleton["entity"]] = skeleton
        lookup[skeleton["entity"].lower()] = skeleton
    return lookup


def build_rig_mapping(entity: str, symbols: list[dict], rig_lookup: dict[str, dict]) -> dict:
    rig = rig_lookup.get(entity)
    if not rig:
        return {"entity": entity, "rig_name": None, "bindings": []}
    return {
        "entity": entity,
        "rig_name": rig["name"],
        "bindings": [
            {
                "symbol_id": symbol["symbol_id"],
                "nearest_bone": symbol.get("nearest_rig_bone"),
                "binding_mode": "nearest-bone seed",
            }
            for symbol in symbols
        ],
    }


def build_keypose_intake(entity: str, asset_name: str, category: str, symbols: list[dict]) -> dict:
    return {
        "entity": entity,
        "asset": asset_name,
        "category": category,
        "contact_points": [
            symbol["pivot_candidates"][0]
            for symbol in symbols[: min(8, len(symbols))]
        ],
        "key_deformation_zones": [
            {
                "symbol_id": symbol["symbol_id"],
                "deformation_type": symbol["deformation_type"],
            }
            for symbol in symbols
        ],
    }


def build_runtime_inbetween_constraints(entity: str, category: str) -> dict:
    return {
        "entity": entity,
        "category": category,
        "allows_runtime_inbetween": category in {"player", "companion", "npc", "enemy", "enemy_elite", "boss", "wildlife"},
        "rules": [
            "Do not change authored silhouette-defining beats.",
            "Allow only overlap, secondary motion, contact settling, and balance smoothing.",
            "Respect stable gameplay timing windows and collision contact points.",
        ],
    }


def analyze(image_path: Path, asset_name: str, category: str, entity: str | None, output_dir: Path, rig_lookup: dict[str, dict]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size
    rgba_rows = [[image.getpixel((x, y)) for x in range(width)] for y in range(height)]
    lab_rows = [[rgb_to_lab(pixel[0], pixel[1], pixel[2]) for pixel in row] for row in rgba_rows]
    alpha_rows = [[pixel[3] for pixel in row] for row in rgba_rows]
    distance_map = compute_distance_to_empty(alpha_rows)
    region_map, regions = segment_regions(rgba_rows, lab_rows)
    symbols = build_symbol_objects(regions, rgba_rows, distance_map, category, entity, rig_lookup, (width, height))
    pixel_matrix = build_pixel_matrix(rgba_rows, lab_rows, region_map, distance_map)
    spatial_metrics = build_spatial_metrics(symbols, (width, height))
    depth_values = write_depth_map(rgba_rows, distance_map, region_map, output_dir / "depth_map.png")
    material_fields = build_material_response_fields(depth_values, alpha_rows, distance_map)
    scalar_field_to_image(material_fields["fiber"], alpha_rows, output_dir / "fiber_map.png")
    scalar_field_to_image(material_fields["elasticity"], alpha_rows, output_dir / "elasticity_map.png")
    scalar_field_to_image(material_fields["bump"], alpha_rows, output_dir / "bump_map.png")
    scalar_field_to_image(material_fields["curvature"], alpha_rows, output_dir / "curvature_map.png")
    write_normal_map(material_fields["normals"], alpha_rows, output_dir / "normal_map.png")
    volume_layers = summarize_volume_layers(depth_values, alpha_rows, material_fields["elasticity"], 140)
    write_volume_layer_preview(depth_values, alpha_rows, output_dir / "volume_layers_140_preview.png", 140)
    dense_shell_profile = write_dense_shell_obj(depth_values, alpha_rows, material_fields["fiber"], material_fields["elasticity"], output_dir / "dense_shell_10000.obj", 10000)
    material_map_paths = {
        "depth_map": str(output_dir / "depth_map.png"),
        "normal_map": str(output_dir / "normal_map.png"),
        "bump_map": str(output_dir / "bump_map.png"),
        "fiber_map": str(output_dir / "fiber_map.png"),
        "elasticity_map": str(output_dir / "elasticity_map.png"),
        "curvature_map": str(output_dir / "curvature_map.png"),
        "volume_layers": str(output_dir / "volume_layers_140.json"),
        "volume_layers_preview": str(output_dir / "volume_layers_140_preview.png"),
    }
    mesh_contract = build_mesh_contract(asset_name, category, symbols, dense_shell_profile)
    surface_contract = build_surface_contract(asset_name, symbols, material_map_paths)

    save_json(output_dir / "pixel_matrix.json", pixel_matrix)
    save_json(output_dir / "region_map.json", {"regions": [{k: v for k, v in region.items() if k != "pixels"} for region in regions]})
    save_json(output_dir / "symbol_objects.json", symbols)
    write_region_preview(region_map, category, output_dir / "region_map_preview.png")
    save_json(output_dir / "spatial_metrics.json", spatial_metrics)
    save_json(output_dir / "volume_layers_140.json", volume_layers)
    save_json(output_dir / "high_poly_contract.json", dense_shell_profile)
    save_json(output_dir / "mesh_contract.json", mesh_contract)
    save_json(output_dir / "surface_contract.json", surface_contract)

    if entity:
        save_json(output_dir / "rig_mapping.json", build_rig_mapping(entity, symbols, rig_lookup))
        save_json(output_dir / "keypose_intake.json", build_keypose_intake(entity, asset_name, category, symbols))
        save_json(output_dir / "runtime_inbetween_constraints.json", build_runtime_inbetween_constraints(entity, category))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a source asset into per-pixel reconstruction outputs.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--entity")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--rigs", type=Path, default=DEFAULT_RIGS)
    args = parser.parse_args()

    rig_lookup = build_rig_lookup(load_json(args.rigs))
    analyze(args.image, args.asset_name, args.category, args.entity, args.out_dir, rig_lookup)
    print(f"Analyzed {args.image} into {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())