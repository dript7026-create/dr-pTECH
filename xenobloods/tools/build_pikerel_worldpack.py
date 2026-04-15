from __future__ import annotations

from copy import deepcopy
import json
import math
import os
import shutil
from pathlib import Path
import sys

from generate_pikerel_basket_house import Mesh, add_box, write_mtl, write_obj


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
XENO_ROOT = WORKSPACE_ROOT / "xenobloods"
MODELS_DIR = XENO_ROOT / "assets" / "models"
DOENGINE_ROOT = WORKSPACE_ROOT / "DoENGINE"
DOENGINE_GENERATED = DOENGINE_ROOT / "generated" / "xenobloods_preview"
DOENGINE_PACKAGE_MODELS = DOENGINE_GENERATED / "models"
DOENGINE_PACKAGE_BILLBOARDS = DOENGINE_GENERATED / "billboards"
DOENGINE_GAME_ROOT = DOENGINE_ROOT / "games" / "xenobloods"
DOENGINE_GAME_CONTENT = DOENGINE_GAME_ROOT / "content"
DOENGINE_GAME_SCENES = DOENGINE_GAME_CONTENT / "scenes"
DOENGINE_GAME_MODELS = DOENGINE_GAME_CONTENT / "models"
DOENGINE_GAME_BILLBOARDS = DOENGINE_GAME_CONTENT / "billboards"
DOENGINE_GAME_SAVES = DOENGINE_GAME_ROOT / "saves"
DOENGINE_GAME_SCRIPTS = DOENGINE_GAME_ROOT / "scripts"
DOENGINE_GAME_PROFILE = DOENGINE_GAME_ROOT / "game_profile.json"
DOENGINE_GAME_PACKAGE = DOENGINE_GAME_ROOT / "xenobloods_doengine_game.json"
DOENGINE_DEFAULT_SAVE = DOENGINE_GAME_SAVES / "default_save.json"
OPTIONAL_BACKUP_ROOT = Path(os.environ["XENO_WORLDPACK_BACKUP_ROOT"]).expanduser() if os.environ.get("XENO_WORLDPACK_BACKUP_ROOT") else None
OPTIONAL_BACKUP_PACKAGE_MODELS = OPTIONAL_BACKUP_ROOT / "models" if OPTIONAL_BACKUP_ROOT else None
OPTIONAL_BACKUP_PACKAGE_BILLBOARDS = OPTIONAL_BACKUP_ROOT / "billboards" if OPTIONAL_BACKUP_ROOT else None

GENERATED_BILLBOARD_SOURCES = {
    "ishtasha_landborne.png": XENO_ROOT / "assets" / "generated" / "portrait_landborne.png",
    "ishtasha_gourd_infant.png": XENO_ROOT / "assets" / "generated" / "portrait_gourd_infant.png",
    "ishtasha_etheric_current.png": XENO_ROOT / "assets" / "generated" / "portrait_etheric.png",
}

JUMPCLIP_BILLBOARD_SOURCES = {
    "scarab_child_preview.gif": XENO_ROOT / "JumpClipAssets" / "scarab-child-basic-preview" / "preview.gif",
    "lattice_ward_preview.gif": XENO_ROOT / "JumpClipAssets" / "lattice-ward-preview" / "preview.gif",
    "lahgroid_boss_preview.gif": XENO_ROOT / "JumpClipAssets" / "lahgroid-boss-preview" / "preview.gif",
}

PACKAGED_SCRIPT_SOURCES = [
    XENO_ROOT / "src" / "doengine_xenobloods_bridge.py",
    XENO_ROOT / "src" / "prototype_gameplay_flow.py",
    XENO_ROOT / "src" / "xenobloods_systems.py",
    XENO_ROOT / "src" / "xenobloods_adaptive_director.py",
]


def repo_path(path: Path) -> str:
    return path.relative_to(WORKSPACE_ROOT).as_posix()


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DOENGINE_GENERATED.mkdir(parents=True, exist_ok=True)
    DOENGINE_PACKAGE_MODELS.mkdir(parents=True, exist_ok=True)
    DOENGINE_PACKAGE_BILLBOARDS.mkdir(parents=True, exist_ok=True)
    DOENGINE_GAME_SCENES.mkdir(parents=True, exist_ok=True)
    DOENGINE_GAME_MODELS.mkdir(parents=True, exist_ok=True)
    DOENGINE_GAME_BILLBOARDS.mkdir(parents=True, exist_ok=True)
    DOENGINE_GAME_SAVES.mkdir(parents=True, exist_ok=True)
    DOENGINE_GAME_SCRIPTS.mkdir(parents=True, exist_ok=True)

    variant_names = []
    for index, params in enumerate(VILLAGE_VARIANTS, start=1):
        name = f"pikerel_basket_house_{index:02d}"
        build_house_variant(name=name, **params)
        variant_names.append(name)

    prop_names = []
    for name, builder in [
        ("pikerel_walkway_segment", build_walkway_segment),
        ("pikerel_shrine_post", build_shrine_post),
        ("pikerel_dock_platform", build_dock_platform),
        ("pikerel_reed_cluster", build_reed_cluster),
        ("xenobloods_swamp_island", build_swamp_island),
        ("xenobloods_lagoon_water_plane", build_lagoon_water_plane),
        ("xenobloods_mangrove_root_cluster", build_mangrove_roots),
        ("xenobloods_sewer_tunnel_blockout", build_sewer_tunnel_blockout),
    ]:
        mesh = builder()
        write_mesh_bundle(name, mesh)
        prop_names.append(name)

    package_model_bundle(variant_names + prop_names, DOENGINE_PACKAGE_MODELS)
    package_model_bundle(variant_names + prop_names, DOENGINE_GAME_MODELS)
    package_billboard_bundle(DOENGINE_PACKAGE_BILLBOARDS)
    package_billboard_bundle(DOENGINE_GAME_BILLBOARDS)
    package_game_scripts()

    scene_payload = build_scene_manifest(variant_names, prop_names, model_path_prefix="models/", billboard_path_prefix="billboards/")
    scene_path = DOENGINE_GENERATED / "xenobloods_pikerel_swamp_showcase.json"
    scene_path.write_text(json.dumps(scene_payload, indent=2), encoding="utf-8")

    game_scene_payload = build_scene_manifest(variant_names, prop_names, model_path_prefix="../models/", billboard_path_prefix="../billboards/")
    game_scene_path = DOENGINE_GAME_SCENES / "xenobloods_pikerel_swamp_showcase.json"
    game_scene_path.write_text(json.dumps(game_scene_payload, indent=2), encoding="utf-8")

    install_path = DOENGINE_ROOT / "generated" / "dodogame_bangonow_showcase.json"
    install_path.write_text(json.dumps(scene_payload, indent=2), encoding="utf-8")

    write_standalone_game_package(game_scene_payload, game_scene_path)

    summary_path = DOENGINE_GENERATED / "xenobloods_worldpack_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "village_variants": variant_names,
                "support_meshes": prop_names,
                "scene_manifest": repo_path(scene_path),
                "installed_showcase_manifest": repo_path(install_path),
                "packaged_models_dir": repo_path(DOENGINE_PACKAGE_MODELS),
                "packaged_billboards_dir": repo_path(DOENGINE_PACKAGE_BILLBOARDS),
                "standalone_game_profile": repo_path(DOENGINE_GAME_PROFILE),
                "standalone_game_package": repo_path(DOENGINE_GAME_PACKAGE),
                "standalone_default_save": repo_path(DOENGINE_DEFAULT_SAVE),
                "standalone_scripts_dir": repo_path(DOENGINE_GAME_SCRIPTS),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    mirror_to_optional_backup(scene_path, summary_path)
    print(scene_path)
    print(summary_path)


VILLAGE_VARIANTS = [
    {"body_scale": 1.0, "roof_scale": 1.0, "stilts": 2.8, "porch_depth": 1.2, "window_offset": 1.2},
    {"body_scale": 1.08, "roof_scale": 1.1, "stilts": 3.2, "porch_depth": 1.45, "window_offset": 1.3},
    {"body_scale": 0.92, "roof_scale": 0.9, "stilts": 2.45, "porch_depth": 1.0, "window_offset": 1.08},
    {"body_scale": 1.16, "roof_scale": 1.22, "stilts": 3.45, "porch_depth": 1.68, "window_offset": 1.36},
    {"body_scale": 0.98, "roof_scale": 1.04, "stilts": 2.9, "porch_depth": 1.32, "window_offset": 1.15},
    {"body_scale": 1.24, "roof_scale": 1.3, "stilts": 3.9, "porch_depth": 1.88, "window_offset": 1.42},
]


def build_house_variant(name: str, body_scale: float, roof_scale: float, stilts: float, porch_depth: float, window_offset: float) -> None:
    mesh = Mesh()
    build_variant_body(mesh, body_scale)
    build_variant_roof(mesh, roof_scale, body_scale)
    build_variant_handle(mesh, roof_scale, body_scale)
    build_variant_stilts(mesh, stilts, body_scale)
    build_variant_porch(mesh, porch_depth, body_scale)
    build_variant_door_windows(mesh, body_scale, window_offset)
    write_mesh_bundle(name, mesh)


def build_variant_body(mesh: Mesh, body_scale: float) -> None:
    radial_segments = 56
    profile = resample_profile(
        [
            (0.0, 1.2 * body_scale),
            (0.48, 1.5 * body_scale),
            (1.24, 1.82 * body_scale),
            (2.1, 1.98 * body_scale),
            (3.02, 1.92 * body_scale),
            (3.78, 1.68 * body_scale),
            (4.18, 1.34 * body_scale),
        ],
        24,
    )
    rings = []
    for yi, (y, radius) in enumerate(profile):
        ring = []
        for xi in range(radial_segments):
            angle = xi / radial_segments * math.tau
            wobble = 1.0 + 0.05 * math.sin(angle * 5.0 + yi * 0.6)
            x = math.cos(angle) * radius * wobble
            z = math.sin(angle) * radius * wobble
            vertex = mesh.add_vertex(x, y, z)
            uv = mesh.add_uv(xi / radial_segments, yi / max(1, len(profile) - 1))
            ring.append((vertex, uv))
        rings.append(ring)
    stitch_rings(mesh, rings, "basket_body")
    cap_bottom(mesh, rings[0], "basket_body")


def build_variant_roof(mesh: Mesh, roof_scale: float, body_scale: float) -> None:
    radial_segments = 56
    vertical_segments = 14
    base_y = 4.2 * body_scale
    base_radius = 1.35 * roof_scale
    rings = []
    for yi in range(vertical_segments + 1):
        t = yi / vertical_segments
        angle = t * math.pi * 0.6
        radius = math.cos(angle) * base_radius
        y = base_y + math.sin(angle) * (1.1 * roof_scale)
        ring = []
        for xi in range(radial_segments):
            theta = xi / radial_segments * math.tau
            x = math.cos(theta) * radius
            z = math.sin(theta) * radius
            vertex = mesh.add_vertex(x, y, z)
            uv = mesh.add_uv(xi / radial_segments, t)
            ring.append((vertex, uv))
        rings.append(ring)
    stitch_rings(mesh, rings, "roof_lid")
    top_center = mesh.add_vertex(0.0, base_y + 1.28 * roof_scale, 0.0)
    top_uv = mesh.add_uv(0.5, 1.0)
    last_ring = rings[-1]
    for xi in range(radial_segments):
        mesh.add_triangle("roof_lid", last_ring[xi], last_ring[(xi + 1) % radial_segments], (top_center, top_uv))


def build_variant_handle(mesh: Mesh, roof_scale: float, body_scale: float) -> None:
    arc_segments = 28
    tube_segments = 12
    major_radius = 2.5 * body_scale
    tube_radius = 0.1 * roof_scale
    center_y = 3.7 * body_scale
    rings = []
    for ai in range(arc_segments + 1):
        t = ai / arc_segments
        sweep = math.pi * (0.1 + t * 0.8)
        anchor_x = math.cos(sweep) * major_radius
        anchor_y = center_y + math.sin(sweep) * (1.75 * roof_scale)
        ring = []
        for ti in range(tube_segments):
            phi = ti / tube_segments * math.tau
            vertex = mesh.add_vertex(anchor_x, anchor_y + math.cos(phi) * tube_radius, math.sin(phi) * tube_radius)
            uv = mesh.add_uv(t, ti / tube_segments)
            ring.append((vertex, uv))
        rings.append(ring)
    stitch_rings(mesh, rings, "basket_trim")


def build_variant_stilts(mesh: Mesh, stilt_height: float, body_scale: float) -> None:
    post_positions = [(-1.22 * body_scale, -1.22 * body_scale), (1.22 * body_scale, -1.22 * body_scale), (-1.22 * body_scale, 1.22 * body_scale), (1.22 * body_scale, 1.22 * body_scale)]
    for x, z in post_positions:
        add_box(mesh, "basket_trim", (x, -stilt_height / 2.0, z), (0.15, stilt_height / 2.0, 0.15), uv_scale=0.3)
    add_box(mesh, "basket_trim", (0.0, -0.16, 0.0), (1.9 * body_scale, 0.16, 1.9 * body_scale), uv_scale=0.6)


def build_variant_porch(mesh: Mesh, porch_depth: float, body_scale: float) -> None:
    add_box(mesh, "basket_trim", (0.0, 0.08, 2.15 * body_scale + porch_depth * 0.5), (1.25 * body_scale, 0.1, porch_depth), uv_scale=0.35)
    for side in (-0.65, 0.65):
        add_box(mesh, "basket_trim", (side * body_scale, 0.72, 2.1 * body_scale + porch_depth * 0.35), (0.07, 0.7, 0.07), uv_scale=0.1)


def build_variant_door_windows(mesh: Mesh, body_scale: float, window_offset: float) -> None:
    add_box(mesh, "door_frame", (0.0, 1.42 * body_scale, 1.92 * body_scale), (0.5 * body_scale, 0.95 * body_scale, 0.07), uv_scale=0.2)
    for side in (-window_offset, window_offset):
        add_box(mesh, "window_frame", (side, 2.18 * body_scale, 1.64 * body_scale), (0.36 * body_scale, 0.28 * body_scale, 0.06), uv_scale=0.18)


def build_walkway_segment() -> Mesh:
    mesh = Mesh()
    add_box(mesh, "basket_trim", (0.0, 0.0, 0.0), (2.4, 0.1, 0.55), uv_scale=0.4)
    for x in (-1.9, -0.6, 0.6, 1.9):
        add_box(mesh, "basket_trim", (x, -0.6, -0.38), (0.08, 0.6, 0.08), uv_scale=0.1)
        add_box(mesh, "basket_trim", (x, -0.6, 0.38), (0.08, 0.6, 0.08), uv_scale=0.1)
    return mesh


def build_shrine_post() -> Mesh:
    mesh = Mesh()
    add_box(mesh, "basket_trim", (0.0, 1.2, 0.0), (0.18, 1.2, 0.18), uv_scale=0.1)
    add_box(mesh, "roof_lid", (0.0, 2.85, 0.0), (0.75, 0.16, 0.75), uv_scale=0.2)
    add_box(mesh, "window_frame", (0.0, 2.2, 0.0), (0.28, 0.28, 0.28), uv_scale=0.15)
    return mesh


def build_dock_platform() -> Mesh:
    mesh = Mesh()
    add_box(mesh, "basket_trim", (0.0, 0.0, 0.0), (3.2, 0.12, 1.8), uv_scale=0.45)
    for x in (-2.6, 2.6):
        for z in (-1.2, 1.2):
            add_box(mesh, "basket_trim", (x, -0.95, z), (0.12, 0.95, 0.12), uv_scale=0.12)
    return mesh


def build_reed_cluster() -> Mesh:
    mesh = Mesh()
    angles = [0.0, 0.6, -0.4, 1.1, -1.0, 0.2, -0.7, 0.95]
    for index, angle in enumerate(angles):
        x = math.cos(angle) * (0.22 + 0.04 * index)
        z = math.sin(angle) * (0.22 + 0.04 * index)
        add_box(mesh, "jade", (x, 0.9 + 0.07 * index, z), (0.03, 0.9 + 0.05 * index, 0.03), uv_scale=0.05)
    return mesh


def build_swamp_island() -> Mesh:
    mesh = Mesh()
    radial_segments = 40
    rings = []
    levels = [(0.0, 4.4), (0.25, 4.8), (0.55, 4.1), (0.95, 2.8), (1.25, 1.1)]
    for yi, (y, radius) in enumerate(levels):
        ring = []
        for xi in range(radial_segments):
            theta = xi / radial_segments * math.tau
            jitter = 1.0 + 0.12 * math.sin(theta * 3.0 + yi)
            x = math.cos(theta) * radius * jitter
            z = math.sin(theta) * radius * jitter
            vertex = mesh.add_vertex(x, y, z)
            uv = mesh.add_uv((x / 10.0) + 0.5, (z / 10.0) + 0.5)
            ring.append((vertex, uv))
        rings.append(ring)
    stitch_rings(mesh, rings, "stone")
    cap_bottom(mesh, rings[0], "shadow")
    return mesh


def build_lagoon_water_plane() -> Mesh:
    mesh = Mesh()
    size = 32.0
    a = (mesh.add_vertex(-size, 0.0, -size), mesh.add_uv(0.0, 0.0))
    b = (mesh.add_vertex(size, 0.0, -size), mesh.add_uv(1.0, 0.0))
    c = (mesh.add_vertex(size, 0.0, size), mesh.add_uv(1.0, 1.0))
    d = (mesh.add_vertex(-size, 0.0, size), mesh.add_uv(0.0, 1.0))
    mesh.add_quad("jade", a, b, c, d)
    return mesh


def build_mangrove_roots() -> Mesh:
    mesh = Mesh()
    for index in range(12):
        angle = index / 12 * math.tau
        x = math.cos(angle) * 1.8
        z = math.sin(angle) * 1.8
        height = 1.6 + 0.3 * math.sin(index)
        add_box(mesh, "basket_trim", (x * 0.5, height * 0.5, z * 0.5), (0.14, height * 0.5, 0.14), uv_scale=0.08)
        add_box(mesh, "basket_trim", (x, 0.15, z), (0.08, 0.18, 0.08), uv_scale=0.05)
    return mesh


def build_sewer_tunnel_blockout() -> Mesh:
    mesh = Mesh()
    segments = 18
    for index in range(segments):
        z = index * 2.6
        add_box(mesh, "stone", (-3.2, 1.3, z), (0.25, 1.3, 1.2), uv_scale=0.15)
        add_box(mesh, "stone", (3.2, 1.3, z), (0.25, 1.3, 1.2), uv_scale=0.15)
        add_box(mesh, "stone", (0.0, 2.6, z), (3.45, 0.22, 1.25), uv_scale=0.15)
    add_box(mesh, "shadow", (0.0, -0.18, segments * 1.3), (3.0, 0.18, segments * 1.4), uv_scale=0.2)
    return mesh


def stitch_rings(mesh: Mesh, rings, material: str) -> None:
    for yi in range(len(rings) - 1):
        current = rings[yi]
        nxt = rings[yi + 1]
        count = len(current)
        for xi in range(count):
            mesh.add_quad(material, current[xi], current[(xi + 1) % count], nxt[(xi + 1) % count], nxt[xi])


def cap_bottom(mesh: Mesh, ring, material: str) -> None:
    center = mesh.add_vertex(0.0, min(mesh.vertices[i[0] - 1][1] for i in ring), 0.0)
    center_uv = mesh.add_uv(0.5, 0.5)
    count = len(ring)
    for xi in range(count):
        mesh.add_triangle(material, (center, center_uv), ring[(xi + 1) % count], ring[xi])


def resample_profile(points, steps: int):
    segments = len(points) - 1
    result = []
    for index in range(steps + 1):
        t = index / steps * segments
        segment = min(int(t), segments - 1)
        local_t = t - segment
        y0, r0 = points[segment]
        y1, r1 = points[segment + 1]
        result.append((y0 + (y1 - y0) * local_t, r0 + (r1 - r0) * local_t))
    return result


def write_mesh_bundle(name: str, mesh: Mesh) -> None:
    obj_path = MODELS_DIR / f"{name}.obj"
    mtl_path = MODELS_DIR / f"{name}.mtl"
    write_obj(mesh, obj_path, mtl_path.name)
    write_mtl(mtl_path)


def build_scene_manifest(variant_names: list[str], prop_names: list[str], model_path_prefix: str, billboard_path_prefix: str) -> dict:
    scene_entries: list[dict] = [
        {
            "id": "lagoon_water",
            "kind": "mesh",
            "loader": "obj",
            "mesh": packaged_model_path(model_path_prefix, "xenobloods_lagoon_water_plane.obj"),
            "position": [0.0, -1.2, 18.0],
            "rotation": [0.0, 0.0, 0.0],
            "scale": 1.0,
            "material": "jade",
            "label": "Pikerel Lagoon",
            "scripts": [{"type": "drift", "amplitude_x": 0.14, "amplitude_z": 0.06, "speed": 0.18}],
            "metadata": {"role": "water-plane", "binding_id": "pikerel_lagoon"},
        },
        {
            "id": "swamp_island_core",
            "kind": "mesh",
            "loader": "obj",
            "mesh": packaged_model_path(model_path_prefix, "xenobloods_swamp_island.obj"),
            "position": [0.0, -1.05, 17.8],
            "rotation": [0.0, 0.1, 0.0],
            "scale": 1.0,
            "material": "stone",
            "label": "Swamp Island Core",
            "scripts": [{"type": "bob", "amplitude": 0.06, "speed": 0.33}],
            "metadata": {"role": "terrain-core", "binding_id": "swamp_island_core"},
        },
        {
            "id": "sewer_preview",
            "kind": "mesh",
            "loader": "obj",
            "mesh": packaged_model_path(model_path_prefix, "xenobloods_sewer_tunnel_blockout.obj"),
            "position": [0.0, -0.7, 33.0],
            "rotation": [0.0, 0.0, 0.0],
            "scale": 0.85,
            "material": "shadow",
            "label": "Sewer Tunnel Blockout",
            "scripts": [],
            "metadata": {"role": "future-biome-preview", "binding_id": "sewer_preview_gate", "unlock_flag": "sewer_unlocked"},
        },
    ]

    house_positions = [
        (-8.8, 0.0, 12.6, 0.18),
        (-4.8, 0.0, 11.4, -0.08),
        (-1.2, 0.0, 10.7, 0.02),
        (2.6, 0.0, 11.2, -0.16),
        (6.3, 0.0, 12.3, 0.14),
        (9.6, 0.0, 13.4, -0.22),
    ]
    for index, (name, pos) in enumerate(zip(variant_names, house_positions), start=1):
        x, y, z, yaw = pos
        scene_entries.append(
            {
                "id": f"house_{index:02d}",
                "kind": "mesh",
                "loader": "obj",
                "mesh": packaged_model_path(model_path_prefix, f"{name}.obj"),
                "position": [x, y, z],
                "rotation": [0.0, yaw, 0.0],
                "scale": 1.0,
                "material": "stone",
                "label": f"Pikerel Basket House {index}",
                "scripts": [{"type": "bob", "amplitude": 0.04 + index * 0.003, "speed": 0.2 + index * 0.03}],
                "metadata": {"role": "village-house", "binding_id": f"village_house_{index:02d}", "district": "pikerel_village"},
            }
        )

    walkway_z = [10.0, 11.8, 13.6, 15.4]
    for row, z in enumerate(walkway_z, start=1):
        for col, x in enumerate([-6.4, -1.6, 3.2, 8.0], start=1):
            scene_entries.append(
                {
                    "id": f"walkway_{row}_{col}",
                    "kind": "mesh",
                    "loader": "obj",
                    "mesh": packaged_model_path(model_path_prefix, "pikerel_walkway_segment.obj"),
                    "position": [x, -0.58, z],
                    "rotation": [0.0, 0.0, 0.0],
                    "scale": 1.0,
                    "material": "basket_trim",
                    "label": "Walkway Segment",
                    "scripts": [],
                    "metadata": {"role": "walkway", "binding_id": f"walkway_{row}_{col}"},
                }
            )

    shrine_posts = [(-10.6, 0.0, 14.0), (10.9, 0.0, 15.0), (0.0, 0.0, 8.0)]
    for index, (x, y, z) in enumerate(shrine_posts, start=1):
        scene_entries.append(
            {
                "id": f"shrine_post_{index}",
                "kind": "mesh",
                "loader": "obj",
                "mesh": packaged_model_path(model_path_prefix, "pikerel_shrine_post.obj"),
                "position": [x, y, z],
                "rotation": [0.0, 0.0, 0.0],
                "scale": 1.0,
                "material": "bone",
                "label": "Soul Shrine Post",
                "scripts": [{"type": "pulse", "amplitude": 0.04, "speed": 0.7}],
                "metadata": {"role": "shrine-marker", "binding_id": f"soul_shrine_{index:02d}", "plane_target": ["up", "low", "land"][index - 1]},
            }
        )

    for index, x in enumerate([-13.0, -9.5, -6.0, 5.0, 9.2, 13.0], start=1):
        scene_entries.append(
            {
                "id": f"reed_cluster_{index}",
                "kind": "mesh",
                "loader": "obj",
                "mesh": packaged_model_path(model_path_prefix, "pikerel_reed_cluster.obj"),
                "position": [x, -0.95, 19.4 + (index % 2) * 1.8],
                "rotation": [0.0, 0.15 * index, 0.0],
                "scale": 1.0 + (index % 3) * 0.1,
                "material": "jade",
                "label": "Swamp Reeds",
                "scripts": [{"type": "sway", "amplitude": 0.08, "speed": 0.48 + index * 0.03}],
                "metadata": {"role": "foliage", "binding_id": f"reed_cluster_{index:02d}"},
            }
        )

    for index, x in enumerate([-7.8, 7.8], start=1):
        scene_entries.append(
            {
                "id": f"dock_platform_{index}",
                "kind": "mesh",
                "loader": "obj",
                "mesh": packaged_model_path(model_path_prefix, "pikerel_dock_platform.obj"),
                "position": [x, -0.9, 22.5 + index * 1.2],
                "rotation": [0.0, 0.06 * index, 0.0],
                "scale": 1.0,
                "material": "basket_trim",
                "label": "Lagoon Dock",
                "scripts": [],
                "metadata": {"role": "dock", "binding_id": f"lagoon_dock_{index:02d}", "route_hint": "lagoon_crossing"},
            }
        )

    for index, x in enumerate([-15.0, -11.4, 11.7, 15.2], start=1):
        scene_entries.append(
            {
                "id": f"mangrove_cluster_{index}",
                "kind": "mesh",
                "loader": "obj",
                "mesh": packaged_model_path(model_path_prefix, "xenobloods_mangrove_root_cluster.obj"),
                "position": [x, -1.0, 21.0 + index],
                "rotation": [0.0, 0.22 * index, 0.0],
                "scale": 1.0 + (index % 2) * 0.12,
                "material": "stone",
                "label": "Mangrove Root Cluster",
                "scripts": [{"type": "sway", "amplitude": 0.05, "speed": 0.4}],
                "metadata": {"role": "tree-root", "binding_id": f"mangrove_cluster_{index:02d}"},
            }
        )

    scene_entries.extend(build_demo_billboard_entries(billboard_path_prefix))

    return {
        "showcase_name": "XenoBloods Pikerel Village And Swamp Showcase",
        "scene_version": "2026-03-31.xenobloods-preview",
        "camera": {"orbit": 0.44, "elevation": 0.16, "focus_z": 18.5},
        "asset_loaders": ["builtin", "obj", "billboard"],
        "script_capabilities": ["spin", "bob", "pulse", "drift", "sway", "channel_follow", "threshold_gate", "accent_burst"],
        "concept_translation": {
            "project": "XenoBloods",
            "biomes": ["pikerel_village", "swamp_lagoon", "sewer_preview"],
            "notes": [
                "Village built from basket-house variants, docks, shrine posts, and walkway spans.",
                "Swamp blockout includes island terrain, lagoon plane, reed clusters, and mangrove roots.",
                "Sewer tunnel sits as a future biome preview deeper in scene space.",
                "Lifecycle and encounter billboards are packaged with the scene so standalone DoENGINE saves can surface Landborne, Gourd Infant, Etheric Current, and Lahgroid boss states.",
            ],
        },
        "pipeline": {
            "variant_house_count": len(variant_names),
            "support_mesh_count": len(prop_names),
            "doengine_target": repo_path(DOENGINE_ROOT),
            **({"optional_backup_target": str(OPTIONAL_BACKUP_ROOT)} if OPTIONAL_BACKUP_ROOT is not None else {}),
            "packaged_models_dir": repo_path(DOENGINE_PACKAGE_MODELS if model_path_prefix == "models/" else DOENGINE_GAME_MODELS),
            "packaged_billboards_dir": repo_path(DOENGINE_PACKAGE_BILLBOARDS if billboard_path_prefix == "billboards/" else DOENGINE_GAME_BILLBOARDS),
            "standalone_game_package": repo_path(DOENGINE_GAME_PACKAGE),
        },
        "scene_entries": scene_entries,
    }


def build_demo_billboard_entries(billboard_path_prefix: str) -> list[dict]:
    return [
        {
            "id": "player_life_landborne",
            "kind": "billboard",
            "image_path": packaged_billboard_path(billboard_path_prefix, "ishtasha_landborne.png"),
            "position": [-9.8, 1.1, 8.6],
            "width": 360,
            "height": 360,
            "label": "Ishtasha: Landborne",
            "scripts": [{"type": "channel_follow", "channel": "life_state_landborne", "y_amplitude": 0.16, "scale_amplitude": 0.2, "speed": 0.72}],
            "metadata": {"role": "player-life-state", "binding_id": "player_life_landborne", "life_form": "landborne"},
        },
        {
            "id": "player_life_gourd_infant",
            "kind": "billboard",
            "image_path": packaged_billboard_path(billboard_path_prefix, "ishtasha_gourd_infant.png"),
            "position": [0.0, 1.0, 7.8],
            "width": 340,
            "height": 340,
            "label": "Ishtasha: Gourd Infant",
            "scripts": [{"type": "channel_follow", "channel": "life_state_gourd_infant", "y_amplitude": 0.16, "scale_amplitude": 0.2, "speed": 0.72}],
            "metadata": {"role": "player-life-state", "binding_id": "player_life_gourd_infant", "life_form": "gourd_infant"},
        },
        {
            "id": "player_life_etheric_current",
            "kind": "billboard",
            "image_path": packaged_billboard_path(billboard_path_prefix, "ishtasha_etheric_current.png"),
            "position": [9.8, 1.2, 8.6],
            "width": 340,
            "height": 340,
            "label": "Ishtasha: Etheric Current",
            "scripts": [{"type": "channel_follow", "channel": "life_state_etheric_current", "y_amplitude": 0.18, "scale_amplitude": 0.2, "speed": 0.78}],
            "metadata": {"role": "player-life-state", "binding_id": "player_life_etheric_current", "life_form": "etheric_current"},
        },
        {
            "id": "encounter_scarab_child",
            "kind": "billboard",
            "image_path": packaged_billboard_path(billboard_path_prefix, "scarab_child_preview.gif"),
            "position": [-6.4, 1.1, 23.4],
            "width": 260,
            "height": 240,
            "label": "Scarab Child Acolyte",
            "scripts": [{"type": "channel_follow", "channel": "encounter_focus_scarab", "y_amplitude": 0.14, "scale_amplitude": 0.18, "speed": 0.66}],
            "metadata": {"role": "encounter-preview", "binding_id": "encounter_scarab_child", "actor_id": "scarab_child_acolyte"},
        },
        {
            "id": "encounter_lattice_ward",
            "kind": "billboard",
            "image_path": packaged_billboard_path(billboard_path_prefix, "lattice_ward_preview.gif"),
            "position": [6.6, 1.2, 23.9],
            "width": 260,
            "height": 240,
            "label": "Lattice Ward",
            "scripts": [{"type": "channel_follow", "channel": "encounter_focus_lattice", "y_amplitude": 0.14, "scale_amplitude": 0.18, "speed": 0.66}],
            "metadata": {"role": "encounter-preview", "binding_id": "encounter_lattice_ward", "actor_id": "lattice_ward"},
        },
        {
            "id": "boss_lahgroid",
            "kind": "billboard",
            "image_path": packaged_billboard_path(billboard_path_prefix, "lahgroid_boss_preview.gif"),
            "position": [0.0, 1.9, 29.4],
            "width": 380,
            "height": 360,
            "label": "Lahgroid Hierophant",
            "scripts": [
                {"type": "channel_follow", "channel": "boss_focus", "y_amplitude": 0.18, "scale_amplitude": 0.22, "speed": 0.6},
                {"type": "threshold_gate", "threshold": "boss_intro", "y_amplitude": 0.2, "scale_amplitude": 0.12, "speed": 0.72},
                {"type": "accent_burst", "channel": "boss_pressure", "scale_amplitude": 0.18, "y_amplitude": 0.2, "curve": 6.0, "speed": 1.08},
            ],
            "metadata": {"role": "boss-preview", "binding_id": "boss_lahgroid", "actor_id": "lahgroid_hierophant", "threshold": "boss_intro"},
        },
    ]


def package_model_bundle(names: list[str], target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        for suffix in (".obj", ".mtl"):
            source = MODELS_DIR / f"{name}{suffix}"
            if source.exists():
                shutil.copy2(source, target_dir / source.name)


def ensure_generated_billboards() -> None:
    if all(path.exists() for path in GENERATED_BILLBOARD_SOURCES.values()):
        return
    source_dir = XENO_ROOT / "src"
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))
    from generate_prototype_assets import main as generate_prototype_assets

    generate_prototype_assets()


def package_billboard_bundle(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    ensure_generated_billboards()
    for target_name, source in {**GENERATED_BILLBOARD_SOURCES, **JUMPCLIP_BILLBOARD_SOURCES}.items():
        if source.exists():
            shutil.copy2(source, target_dir / target_name)


def package_game_scripts() -> None:
    DOENGINE_GAME_SCRIPTS.mkdir(parents=True, exist_ok=True)
    for source in PACKAGED_SCRIPT_SOURCES:
        if source.exists():
            shutil.copy2(source, DOENGINE_GAME_SCRIPTS / source.name)


def build_gameplay_bindings(scene_payload: dict) -> dict:
    bindings = {}
    for entry in scene_payload.get("scene_entries", []):
        metadata = entry.get("metadata", {}) if isinstance(entry.get("metadata"), dict) else {}
        binding_id = metadata.get("binding_id")
        if not binding_id:
            continue
        binding_payload = {
            "object_id": entry.get("id"),
            "kind": metadata.get("role", entry.get("kind", "mesh")),
            "label": entry.get("label"),
        }
        for key, value in metadata.items():
            if key != "binding_id":
                binding_payload[key] = value
        bindings[str(binding_id)] = binding_payload
    return bindings


def build_default_save_payload(package_payload: dict) -> dict:
    bindings = package_payload.get("gameplay_bindings", {}) if isinstance(package_payload, dict) else {}
    gameplay_state: dict
    runtime_overrides: dict = {}
    scene_state = {
        "scene_manifest": "content/scenes/xenobloods_pikerel_swamp_showcase.json",
        "runtime_overrides": {},
        "mesh_instances": [],
        "billboards": [],
    }
    try:
        source_dir = XENO_ROOT / "src"
        if str(source_dir) not in sys.path:
            sys.path.insert(0, str(source_dir))
        from doengine_xenobloods_bridge import create_bridge

        bridge = create_bridge(package_payload)
        gameplay_state = deepcopy(bridge.create_initial_state()) if hasattr(bridge, "create_initial_state") else {}
        if hasattr(bridge, "build_runtime_overrides"):
            runtime_overrides = dict(bridge.build_runtime_overrides(gameplay_state, bindings))
        if hasattr(bridge, "build_scene_state"):
            bridge_scene_state = bridge.build_scene_state(gameplay_state, bindings)
            if isinstance(bridge_scene_state, dict):
                scene_state.update(bridge_scene_state)
        scene_state["runtime_overrides"] = runtime_overrides
    except Exception:
        object_state = {}
        for binding_id, binding in bindings.items():
            role = binding.get("kind")
            state = {"object_id": binding.get("object_id"), "kind": role, "visited": False, "activated": False}
            if role == "village-house":
                state["blood_cache"] = 12.0
            if role == "shrine-marker":
                state["plane_target"] = binding.get("plane_target", "land")
            object_state[binding_id] = state
        gameplay_state = {
            "player": {
                "name": "Shellfarer",
                "plane": "land",
                "life_form": "landborne",
                "alignment": "mortal",
                "blood_current": 120.0,
                "blood_maximum": 120.0,
                "health": 100.0,
                "stamina": 100.0,
                "mental_acuity": 100.0,
                "rupture_progress": 0.0,
                "gourd_capacity": 180.0,
                "gourd_stored_blood": 0.0,
                "gourd_shell_integrity": 1.0,
                "gourd_infant_charge": 0.0,
                "spilled_blood_pool": 0.0,
            },
            "world": {
                "current_biome": "pikerel_village",
                "sewer_unlocked": False,
                "activated_shrines": [],
                "visited_houses": [],
            },
            "objects": object_state,
        }
    return {
        "save_version": "doengine.game-state.v1",
        "game_id": "xenobloods",
        "game_profile_manifest": DOENGINE_GAME_PROFILE.name,
        "game_package_manifest": DOENGINE_GAME_PACKAGE.name,
        "scene_state": scene_state,
        "gameplay_state": gameplay_state,
        "runtime_overrides": runtime_overrides,
    }


def write_standalone_game_package(scene_payload: dict, scene_path: Path) -> None:
    bindings = build_gameplay_bindings(scene_payload)
    profile_payload = {
        "game_id": "xenobloods",
        "title": "XenoBloods: Pikerel Village",
        "pipeline_target": "dodogame",
        "render_mode": "full3d-pseudo3d-hybrid",
        "game_package_manifest": DOENGINE_GAME_PACKAGE.name,
        "scene_manifest": "content/scenes/xenobloods_pikerel_swamp_showcase.json",
        "primary_source": "scripts/doengine_xenobloods_bridge.py",
        "source_language": "python",
        "gameplay_bridge": "scripts/doengine_xenobloods_bridge.py",
        "default_save_path": "saves/default_save.json",
        "gameplay_premise": "A swamp-village entry slice that binds XenoBloods systemic state to authored DoENGINE objects and scene packages.",
        "ingest_role": "Standalone DoENGINE package for Xenobloods with load/save support and object gameplay bindings.",
        "controller_profile_id": "bango-xinput-full",
        "supports": [
            "Standalone DoENGINE package",
            "Scene-manifest driven 3D world slice",
            "Saveable object and gameplay state",
            "Python gameplay bridge",
            "Bridge-authored checkpoint exports and preview rendering",
            "Shared registry support across all DoENGINE game projects",
        ],
    }
    package_payload = {
        "package_id": "xenobloods-doengine-game",
        "game_id": "xenobloods",
        "scene_manifest": str(scene_path.relative_to(DOENGINE_GAME_ROOT)).replace("\\", "/"),
        "packaged_models_dir": "content/models",
        "packaged_billboards_dir": "content/billboards",
        "packaged_scripts_dir": "scripts",
        "default_save_path": "saves/default_save.json",
        "gameplay_bridge": {
            "path": "scripts/doengine_xenobloods_bridge.py",
            "factory": "create_bridge",
        },
        "demo_checkpoints": [
            "landborne_entry",
            "ether_recall",
            "gourd_incubation",
            "landborne_reborn",
            "boss_intro",
            "boss_clash",
            "boss_defeat",
        ],
        "gameplay_bindings": bindings,
        "package_notes": [
            "Standalone Xenobloods DoENGINE package built from generated OBJ/MTL assets.",
            "Scene object ids remain stable so gameplay state can bind directly to authored mesh and billboard entries.",
            "Lifecycle portraits, encounter billboards, and Lahgroid boss media are packaged with the game project.",
            "Default save path is packaged with the game project for load/save validation inside DoENGINE.",
        ],
    }
    DOENGINE_GAME_PROFILE.write_text(json.dumps(profile_payload, indent=2), encoding="utf-8")
    DOENGINE_GAME_PACKAGE.write_text(json.dumps(package_payload, indent=2), encoding="utf-8")
    DOENGINE_DEFAULT_SAVE.write_text(json.dumps(build_default_save_payload(package_payload), indent=2), encoding="utf-8")


def packaged_model_path(prefix: str, filename: str) -> str:
    return f"{prefix}{filename}"


def packaged_billboard_path(prefix: str, filename: str) -> str:
    return f"{prefix}{filename}"


def mirror_to_optional_backup(scene_path: Path, summary_path: Path) -> None:
    if OPTIONAL_BACKUP_ROOT is None or OPTIONAL_BACKUP_PACKAGE_MODELS is None or OPTIONAL_BACKUP_PACKAGE_BILLBOARDS is None:
        return
    try:
        OPTIONAL_BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        OPTIONAL_BACKUP_PACKAGE_MODELS.mkdir(parents=True, exist_ok=True)
        OPTIONAL_BACKUP_PACKAGE_BILLBOARDS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(scene_path, OPTIONAL_BACKUP_ROOT / scene_path.name)
        shutil.copy2(summary_path, OPTIONAL_BACKUP_ROOT / summary_path.name)
        for model_path in DOENGINE_PACKAGE_MODELS.glob("*"):
            if model_path.is_file():
                shutil.copy2(model_path, OPTIONAL_BACKUP_PACKAGE_MODELS / model_path.name)
        for billboard_path in DOENGINE_PACKAGE_BILLBOARDS.glob("*"):
            if billboard_path.is_file():
                shutil.copy2(billboard_path, OPTIONAL_BACKUP_PACKAGE_BILLBOARDS / billboard_path.name)
    except Exception:
        pass


if __name__ == "__main__":
    main()