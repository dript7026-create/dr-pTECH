from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "models"


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]] = field(default_factory=list)
    uvs: list[tuple[float, float]] = field(default_factory=list)
    faces: list[tuple[str, tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]] = field(default_factory=list)

    def add_vertex(self, x: float, y: float, z: float) -> int:
        self.vertices.append((x, y, z))
        return len(self.vertices)

    def add_uv(self, u: float, v: float) -> int:
        self.uvs.append((u, v))
        return len(self.uvs)

    def add_triangle(
        self,
        material: str,
        a: tuple[int, int],
        b: tuple[int, int],
        c: tuple[int, int],
    ) -> None:
        self.faces.append((material, (a[0], a[1], 0), (b[0], b[1], 0), (c[0], c[1], 0)))

    def add_quad(
        self,
        material: str,
        a: tuple[int, int],
        b: tuple[int, int],
        c: tuple[int, int],
        d: tuple[int, int],
    ) -> None:
        self.add_triangle(material, a, b, c)
        self.add_triangle(material, a, c, d)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mesh = Mesh()

    build_basket_body(mesh)
    build_lid_roof(mesh)
    build_handle(mesh)
    build_stilts_and_platform(mesh)
    build_porch(mesh)
    build_door_and_windows(mesh)

    obj_path = OUT_DIR / "pikerel_picnic_basket_house.obj"
    mtl_path = OUT_DIR / "pikerel_picnic_basket_house.mtl"
    write_obj(mesh, obj_path, mtl_path.name)
    write_mtl(mtl_path)

    summary = OUT_DIR / "pikerel_picnic_basket_house_summary.txt"
    summary.write_text(
        "Pikerel Picnic Basket House\n"
        f"Vertices: {len(mesh.vertices)}\n"
        f"UVs: {len(mesh.uvs)}\n"
        f"Triangles: {len(mesh.faces)}\n",
        encoding="utf-8",
    )
    print(obj_path)
    print(summary)
    print(f"vertices={len(mesh.vertices)} triangles={len(mesh.faces)}")


def build_basket_body(mesh: Mesh) -> None:
    radial_segments = 72
    profile = resample_profile(
        [
            (0.0, 1.45),
            (0.35, 1.72),
            (0.95, 1.98),
            (1.7, 2.16),
            (2.55, 2.22),
            (3.25, 2.08),
            (3.85, 1.86),
            (4.25, 1.52),
        ],
        30,
    )

    rings: list[list[tuple[int, int]]] = []
    for yi, (y, radius) in enumerate(profile):
        ring: list[tuple[int, int]] = []
        for xi in range(radial_segments):
            angle = xi / radial_segments * math.tau
            weave_offset = 1.0 + 0.05 * math.sin(angle * 6.0 + yi * 0.45)
            x = math.cos(angle) * radius * weave_offset
            z = math.sin(angle) * radius * weave_offset
            vertex = mesh.add_vertex(x, y, z)
            uv = mesh.add_uv(xi / radial_segments, yi / max(1, len(profile) - 1))
            ring.append((vertex, uv))
        rings.append(ring)

    for yi in range(len(rings) - 1):
        current = rings[yi]
        nxt = rings[yi + 1]
        for xi in range(radial_segments):
            a = current[xi]
            b = current[(xi + 1) % radial_segments]
            c = nxt[(xi + 1) % radial_segments]
            d = nxt[xi]
            mesh.add_quad("basket_body", a, b, c, d)

    bottom_center = mesh.add_vertex(0.0, 0.0, 0.0)
    bottom_uv = mesh.add_uv(0.5, 0.5)
    first_ring = rings[0]
    for xi in range(radial_segments):
        a = first_ring[(xi + 1) % radial_segments]
        b = first_ring[xi]
        mesh.add_triangle("basket_body", (bottom_center, bottom_uv), a, b)


def build_lid_roof(mesh: Mesh) -> None:
    radial_segments = 72
    vertical_segments = 18
    base_y = 4.28
    base_radius = 1.58

    rings: list[list[tuple[int, int]]] = []
    for yi in range(vertical_segments + 1):
        t = yi / vertical_segments
        angle = t * math.pi * 0.58
        radius = math.cos(angle) * base_radius
        y = base_y + math.sin(angle) * 1.45 + t * 0.12
        ring: list[tuple[int, int]] = []
        for xi in range(radial_segments):
            theta = xi / radial_segments * math.tau
            x = math.cos(theta) * radius
            z = math.sin(theta) * radius
            vertex = mesh.add_vertex(x, y, z)
            uv = mesh.add_uv(xi / radial_segments, t)
            ring.append((vertex, uv))
        rings.append(ring)

    for yi in range(len(rings) - 1):
        current = rings[yi]
        nxt = rings[yi + 1]
        for xi in range(radial_segments):
            a = current[xi]
            b = current[(xi + 1) % radial_segments]
            c = nxt[(xi + 1) % radial_segments]
            d = nxt[xi]
            mesh.add_quad("roof_lid", a, b, c, d)

    top_center = mesh.add_vertex(0.0, base_y + 1.65, 0.0)
    top_uv = mesh.add_uv(0.5, 1.0)
    last_ring = rings[-1]
    for xi in range(radial_segments):
        a = last_ring[xi]
        b = last_ring[(xi + 1) % radial_segments]
        mesh.add_triangle("roof_lid", a, b, (top_center, top_uv))


def build_handle(mesh: Mesh) -> None:
    arc_segments = 36
    tube_segments = 18
    major_radius = 3.02
    tube_radius = 0.12
    center_y = 3.8

    rings: list[list[tuple[int, int]]] = []
    for ai in range(arc_segments + 1):
        t = ai / arc_segments
        sweep = math.pi * (0.08 + t * 0.84)
        anchor_x = math.cos(sweep) * major_radius
        anchor_y = center_y + math.sin(sweep) * 2.15
        anchor_z = 0.0
        ring: list[tuple[int, int]] = []
        for ti in range(tube_segments):
            phi = ti / tube_segments * math.tau
            x = anchor_x
            y = anchor_y + math.cos(phi) * tube_radius
            z = anchor_z + math.sin(phi) * tube_radius
            vertex = mesh.add_vertex(x, y, z)
            uv = mesh.add_uv(t, ti / tube_segments)
            ring.append((vertex, uv))
        rings.append(ring)

    for ai in range(len(rings) - 1):
        current = rings[ai]
        nxt = rings[ai + 1]
        for ti in range(tube_segments):
            a = current[ti]
            b = current[(ti + 1) % tube_segments]
            c = nxt[(ti + 1) % tube_segments]
            d = nxt[ti]
            mesh.add_quad("basket_trim", a, b, c, d)


def build_stilts_and_platform(mesh: Mesh) -> None:
    post_positions = [(-1.45, -1.45), (1.45, -1.45), (-1.45, 1.45), (1.45, 1.45)]
    for x, z in post_positions:
        add_box(mesh, "basket_trim", (x, -2.8, z), (0.18, 2.8, 0.18), uv_scale=0.4)
    add_box(mesh, "basket_trim", (0.0, -0.18, 0.0), (2.2, 0.18, 2.2), uv_scale=0.8)


def build_porch(mesh: Mesh) -> None:
    add_box(mesh, "basket_trim", (0.0, 0.1, 2.75), (1.6, 0.12, 1.2), uv_scale=0.5)
    add_box(mesh, "basket_trim", (-0.72, 0.86, 2.75), (0.08, 0.8, 0.08), uv_scale=0.2)
    add_box(mesh, "basket_trim", (0.72, 0.86, 2.75), (0.08, 0.8, 0.08), uv_scale=0.2)
    add_box(mesh, "basket_trim", (0.0, 1.58, 2.75), (0.86, 0.06, 0.06), uv_scale=0.2)
    for step_index in range(4):
        add_box(
            mesh,
            "basket_trim",
            (0.0, -0.2 - step_index * 0.2, 3.5 + step_index * 0.34),
            (0.75, 0.06, 0.22),
            uv_scale=0.2,
        )


def build_door_and_windows(mesh: Mesh) -> None:
    add_box(mesh, "door_frame", (0.0, 1.55, 2.18), (0.62, 1.15, 0.08), uv_scale=0.3)
    for side in (-1.2, 1.2):
        add_box(mesh, "window_frame", (side, 2.45, 1.82), (0.48, 0.36, 0.08), uv_scale=0.25)
        add_box(mesh, "window_frame", (side, 2.45, 1.95), (0.08, 0.36, 0.14), uv_scale=0.15)


def add_box(mesh: Mesh, material: str, center: tuple[float, float, float], half: tuple[float, float, float], uv_scale: float) -> None:
    cx, cy, cz = center
    hx, hy, hz = half
    corners = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    faces = [
        (0, 1, 2, 3),
        (5, 4, 7, 6),
        (4, 0, 3, 7),
        (1, 5, 6, 2),
        (3, 2, 6, 7),
        (4, 5, 1, 0),
    ]
    for a_i, b_i, c_i, d_i in faces:
        vertices = []
        for point in (corners[a_i], corners[b_i], corners[c_i], corners[d_i]):
            vx, vy, vz = point
            v_id = mesh.add_vertex(vx, vy, vz)
            u_id = mesh.add_uv((vx + vz) * uv_scale, vy * uv_scale)
            vertices.append((v_id, u_id))
        mesh.add_quad(material, vertices[0], vertices[1], vertices[2], vertices[3])


def resample_profile(points: list[tuple[float, float]], steps: int) -> list[tuple[float, float]]:
    segments = len(points) - 1
    result: list[tuple[float, float]] = []
    for index in range(steps + 1):
        t = index / steps * segments
        segment = min(int(t), segments - 1)
        local_t = t - segment
        y0, r0 = points[segment]
        y1, r1 = points[segment + 1]
        y = y0 + (y1 - y0) * local_t
        radius = r0 + (r1 - r0) * local_t
        result.append((y, radius))
    return result


def write_obj(mesh: Mesh, path: Path, mtl_name: str) -> None:
    material_groups: dict[str, list[tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]]] = {}
    for material, a, b, c in mesh.faces:
        material_groups.setdefault(material, []).append((a, b, c))

    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"mtllib {mtl_name}\n")
        handle.write("o pikerel_picnic_basket_house\n")
        for x, y, z in mesh.vertices:
            handle.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        for u, v in mesh.uvs:
            handle.write(f"vt {u:.6f} {v:.6f}\n")
        for material, tris in material_groups.items():
            handle.write(f"usemtl {material}\n")
            for a, b, c in tris:
                handle.write(
                    "f "
                    f"{a[0]}/{a[1]} {b[0]}/{b[1]} {c[0]}/{c[1]}\n"
                )


def write_mtl(path: Path) -> None:
    path.write_text(
        "newmtl basket_body\n"
        "Kd 0.55 0.37 0.18\n"
        "Ka 0.20 0.12 0.05\n"
        "Ks 0.08 0.06 0.02\n"
        "Ns 32.0\n\n"
        "newmtl roof_lid\n"
        "Kd 0.68 0.49 0.22\n"
        "Ka 0.25 0.18 0.08\n"
        "Ks 0.10 0.08 0.03\n"
        "Ns 28.0\n\n"
        "newmtl basket_trim\n"
        "Kd 0.23 0.15 0.08\n"
        "Ka 0.09 0.05 0.03\n"
        "Ks 0.04 0.04 0.04\n"
        "Ns 14.0\n\n"
        "newmtl door_frame\n"
        "Kd 0.16 0.08 0.05\n"
        "Ka 0.05 0.03 0.02\n"
        "Ks 0.03 0.03 0.03\n"
        "Ns 10.0\n\n"
        "newmtl window_frame\n"
        "Kd 0.78 0.72 0.54\n"
        "Ka 0.16 0.14 0.08\n"
        "Ks 0.18 0.18 0.16\n"
        "Ns 40.0\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()