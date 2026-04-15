from __future__ import annotations

import base64
import json
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None


DODO_SHADER_MANIFEST = {
    'backend': 'python-pillow-cpu-raster',
    'look': 'illusioncanvas-pseudo3d',
    'passes': [
        {'id': 'sky-dome-gradient', 'label': 'Sky Dome Gradient', 'role': 'Establishes the amber-jade atmospheric base before geometry is drawn.'},
        {'id': 'floor-warp-grid', 'label': 'Floor Warp Grid', 'role': 'Projects a curved horizon-floor plane to create the IllusionCanvas pseudo-3D stage feel.'},
        {'id': 'lambert-rim-band', 'label': 'Lambert Rim Band', 'role': 'Applies depth light, rim light, and stepped palette banding to mesh faces.'},
        {'id': 'fog-and-aerial-perspective', 'label': 'Fog And Aerial Perspective', 'role': 'Compresses distant contrast so silhouettes feel painted instead of sterile.'},
        {'id': 'scanline-canvas-grain', 'label': 'Scanline Canvas Grain', 'role': 'Adds frame texture, scanline drift, and vignette for the hybrid canvas feel.'},
    ],
    'uniforms': {
        'fog_density': 0.26,
        'rim_power': 2.4,
        'scanline_intensity': 0.18,
        'palette_steps': 5,
        'floor_curvature': 0.16,
    },
    'asset_loaders': ['builtin', 'obj', 'glb', 'billboard', 'scene-manifest'],
    'script_capabilities': ['spin', 'bob', 'pulse', 'orbit', 'drift', 'sway', 'channel_follow', 'threshold_gate', 'accent_burst'],
}


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: 'Vec3') -> 'Vec3':
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vec3') -> 'Vec3':
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def scale(self, amount: float) -> 'Vec3':
        return Vec3(self.x * amount, self.y * amount, self.z * amount)

    def dot(self, other: 'Vec3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vec3') -> 'Vec3':
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def length(self) -> float:
        return math.sqrt(max(1e-9, self.dot(self)))

    def normalized(self) -> 'Vec3':
        size = self.length()
        return self.scale(1.0 / size)

    @staticmethod
    def from_value(value: object, *, default: 'Vec3' | None = None) -> 'Vec3':
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return Vec3(float(value[0]), float(value[1]), float(value[2]))
        return default or Vec3(0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Face:
    indices: tuple[int, int, int]
    color: tuple[int, int, int]
    material: str = 'stone'


@dataclass(frozen=True)
class Mesh:
    name: str
    vertices: tuple[Vec3, ...]
    faces: tuple[Face, ...]


@dataclass
class MeshInstance:
    name: str
    mesh: Mesh
    position: Vec3
    rotation: Vec3
    scale: float
    material: str = 'stone'
    label: str = ''
    scripts: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class BillboardInstance:
    name: str
    position: Vec3
    size: tuple[int, int]
    image_path: str | None
    label: str
    tint: tuple[int, int, int]
    scripts: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def _append_box(
    vertices: list[Vec3],
    faces: list[Face],
    *,
    min_corner: tuple[float, float, float],
    max_corner: tuple[float, float, float],
    side_color: tuple[int, int, int] = (156, 124, 92),
    top_color: tuple[int, int, int] = (226, 209, 176),
    bottom_color: tuple[int, int, int] = (102, 82, 68),
    side_material: str = 'stone',
    top_material: str = 'bone',
    bottom_material: str = 'shadow',
) -> None:
    x0, y0, z0 = min_corner
    x1, y1, z1 = max_corner
    offset = len(vertices)
    vertices.extend(
        [
            Vec3(x0, y0, z0), Vec3(x1, y0, z0), Vec3(x1, y1, z0), Vec3(x0, y1, z0),
            Vec3(x0, y0, z1), Vec3(x1, y0, z1), Vec3(x1, y1, z1), Vec3(x0, y1, z1),
        ]
    )
    faces.extend(
        [
            Face((offset + 0, offset + 1, offset + 2), side_color, side_material), Face((offset + 0, offset + 2, offset + 3), side_color, side_material),
            Face((offset + 1, offset + 5, offset + 6), side_color, side_material), Face((offset + 1, offset + 6, offset + 2), side_color, side_material),
            Face((offset + 5, offset + 4, offset + 7), side_color, side_material), Face((offset + 5, offset + 7, offset + 6), side_color, side_material),
            Face((offset + 4, offset + 0, offset + 3), side_color, side_material), Face((offset + 4, offset + 3, offset + 7), side_color, side_material),
            Face((offset + 3, offset + 2, offset + 6), top_color, top_material), Face((offset + 3, offset + 6, offset + 7), top_color, top_material),
            Face((offset + 4, offset + 5, offset + 1), bottom_color, bottom_material), Face((offset + 4, offset + 1, offset + 0), bottom_color, bottom_material),
        ]
    )


def rotate_x(vec: Vec3, angle: float) -> Vec3:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vec3(vec.x, vec.y * cos_a - vec.z * sin_a, vec.y * sin_a + vec.z * cos_a)


def rotate_y(vec: Vec3, angle: float) -> Vec3:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vec3(vec.x * cos_a + vec.z * sin_a, vec.y, -vec.x * sin_a + vec.z * cos_a)


def rotate_z(vec: Vec3, angle: float) -> Vec3:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vec3(vec.x * cos_a - vec.y * sin_a, vec.x * sin_a + vec.y * cos_a, vec.z)


def transform_vertex(vertex: Vec3, position: Vec3, rotation: Vec3, scale: float) -> Vec3:
    scaled = vertex.scale(scale)
    rotated = rotate_z(rotate_x(rotate_y(scaled, rotation.y), rotation.x), rotation.z)
    return rotated + position


def cube_mesh(name: str = 'cube') -> Mesh:
    vertices = (
        Vec3(-1.0, -1.0, -1.0),
        Vec3(1.0, -1.0, -1.0),
        Vec3(1.0, 1.0, -1.0),
        Vec3(-1.0, 1.0, -1.0),
        Vec3(-1.0, -1.0, 1.0),
        Vec3(1.0, -1.0, 1.0),
        Vec3(1.0, 1.0, 1.0),
        Vec3(-1.0, 1.0, 1.0),
    )
    faces = (
        Face((0, 1, 2), (165, 129, 90), 'stone'),
        Face((0, 2, 3), (165, 129, 90), 'stone'),
        Face((1, 5, 6), (204, 141, 84), 'amber'),
        Face((1, 6, 2), (204, 141, 84), 'amber'),
        Face((5, 4, 7), (93, 128, 111), 'jade'),
        Face((5, 7, 6), (93, 128, 111), 'jade'),
        Face((4, 0, 3), (103, 136, 124), 'jade'),
        Face((4, 3, 7), (103, 136, 124), 'jade'),
        Face((3, 2, 6), (233, 215, 170), 'bone'),
        Face((3, 6, 7), (233, 215, 170), 'bone'),
        Face((4, 5, 1), (110, 87, 71), 'shadow'),
        Face((4, 1, 0), (110, 87, 71), 'shadow'),
    )
    return Mesh(name=name, vertices=vertices, faces=faces)


def pedestal_mesh(name: str = 'pedestal') -> Mesh:
    vertices = (
        Vec3(-1.4, -0.4, -1.4), Vec3(1.4, -0.4, -1.4), Vec3(1.4, 0.4, -1.4), Vec3(-1.4, 0.4, -1.4),
        Vec3(-1.4, -0.4, 1.4), Vec3(1.4, -0.4, 1.4), Vec3(1.4, 0.4, 1.4), Vec3(-1.4, 0.4, 1.4),
        Vec3(-0.9, 0.4, -0.9), Vec3(0.9, 0.4, -0.9), Vec3(0.9, 1.5, -0.9), Vec3(-0.9, 1.5, -0.9),
        Vec3(-0.9, 0.4, 0.9), Vec3(0.9, 0.4, 0.9), Vec3(0.9, 1.5, 0.9), Vec3(-0.9, 1.5, 0.9),
    )
    faces = (
        Face((0, 1, 2), (118, 93, 72), 'stone'), Face((0, 2, 3), (118, 93, 72), 'stone'),
        Face((1, 5, 6), (158, 111, 76), 'amber'), Face((1, 6, 2), (158, 111, 76), 'amber'),
        Face((5, 4, 7), (88, 116, 98), 'jade'), Face((5, 7, 6), (88, 116, 98), 'jade'),
        Face((4, 0, 3), (96, 124, 109), 'jade'), Face((4, 3, 7), (96, 124, 109), 'jade'),
        Face((3, 2, 6), (210, 197, 161), 'bone'), Face((3, 6, 7), (210, 197, 161), 'bone'),
        Face((8, 9, 10), (162, 132, 94), 'stone'), Face((8, 10, 11), (162, 132, 94), 'stone'),
        Face((9, 13, 14), (194, 150, 98), 'amber'), Face((9, 14, 10), (194, 150, 98), 'amber'),
        Face((13, 12, 15), (98, 128, 110), 'jade'), Face((13, 15, 14), (98, 128, 110), 'jade'),
        Face((12, 8, 11), (102, 134, 119), 'jade'), Face((12, 11, 15), (102, 134, 119), 'jade'),
        Face((11, 10, 14), (226, 206, 170), 'bone'), Face((11, 14, 15), (226, 206, 170), 'bone'),
    )
    return Mesh(name=name, vertices=vertices, faces=faces)


def monolith_mesh(name: str = 'monolith') -> Mesh:
    vertices = (
        Vec3(-0.6, -2.0, -0.6), Vec3(0.6, -2.0, -0.6), Vec3(0.6, 2.0, -0.6), Vec3(-0.6, 2.0, -0.6),
        Vec3(-0.6, -2.0, 0.6), Vec3(0.6, -2.0, 0.6), Vec3(0.6, 2.0, 0.6), Vec3(-0.6, 2.0, 0.6),
        Vec3(0.0, 2.8, 0.0),
    )
    faces = (
        Face((0, 1, 2), (129, 105, 82), 'stone'), Face((0, 2, 3), (129, 105, 82), 'stone'),
        Face((1, 5, 6), (187, 135, 86), 'amber'), Face((1, 6, 2), (187, 135, 86), 'amber'),
        Face((5, 4, 7), (92, 123, 110), 'jade'), Face((5, 7, 6), (92, 123, 110), 'jade'),
        Face((4, 0, 3), (104, 136, 126), 'jade'), Face((4, 3, 7), (104, 136, 126), 'jade'),
        Face((3, 2, 8), (229, 214, 180), 'bone'), Face((2, 6, 8), (229, 214, 180), 'bone'),
        Face((6, 7, 8), (229, 214, 180), 'bone'), Face((7, 3, 8), (229, 214, 180), 'bone'),
    )
    return Mesh(name=name, vertices=vertices, faces=faces)


def arch_mesh(name: str = 'arch') -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    _append_box(vertices, faces, min_corner=(-1.5, -1.9, -0.55), max_corner=(-0.7, 1.5, 0.55), side_color=(118, 99, 78), top_color=(214, 193, 164), side_material='stone')
    _append_box(vertices, faces, min_corner=(0.7, -1.9, -0.55), max_corner=(1.5, 1.5, 0.55), side_color=(118, 99, 78), top_color=(214, 193, 164), side_material='stone')
    _append_box(vertices, faces, min_corner=(-1.5, 1.15, -0.7), max_corner=(1.5, 1.95, 0.7), side_color=(186, 142, 91), top_color=(236, 214, 182), side_material='amber', top_material='bone')
    _append_box(vertices, faces, min_corner=(-0.45, -0.2, -0.35), max_corner=(0.45, 0.7, 0.35), side_color=(96, 131, 116), top_color=(208, 198, 168), side_material='jade', top_material='bone')
    return Mesh(name=name, vertices=tuple(vertices), faces=tuple(faces))


def shard_mesh(name: str = 'shard') -> Mesh:
    vertices = (
        Vec3(0.0, 1.9, 0.0),
        Vec3(-0.9, -1.0, -0.7),
        Vec3(0.95, -0.85, -0.55),
        Vec3(0.65, -1.15, 0.92),
        Vec3(-0.72, -0.92, 0.88),
        Vec3(0.0, -1.55, 0.0),
    )
    faces = (
        Face((0, 1, 2), (205, 152, 96), 'amber'),
        Face((0, 2, 3), (232, 212, 178), 'bone'),
        Face((0, 3, 4), (101, 136, 121), 'jade'),
        Face((0, 4, 1), (170, 132, 94), 'stone'),
        Face((5, 2, 1), (109, 86, 70), 'shadow'),
        Face((5, 3, 2), (118, 92, 75), 'shadow'),
        Face((5, 4, 3), (112, 90, 74), 'shadow'),
        Face((5, 1, 4), (116, 88, 72), 'shadow'),
    )
    return Mesh(name=name, vertices=vertices, faces=faces)


def spire_mesh(name: str = 'spire') -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    _append_box(vertices, faces, min_corner=(-0.95, -1.7, -0.95), max_corner=(0.95, -0.6, 0.95), side_color=(116, 95, 76), top_color=(206, 188, 158), side_material='stone')
    _append_box(vertices, faces, min_corner=(-0.55, -0.6, -0.55), max_corner=(0.55, 1.9, 0.55), side_color=(186, 142, 90), top_color=(238, 219, 188), side_material='amber', top_material='bone')
    _append_box(vertices, faces, min_corner=(-0.28, 1.9, -0.28), max_corner=(0.28, 3.0, 0.28), side_color=(96, 131, 116), top_color=(230, 215, 180), side_material='jade', top_material='bone')
    return Mesh(name=name, vertices=tuple(vertices), faces=tuple(faces))


def deco_frame_mesh(name: str = 'deco_frame') -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    _append_box(vertices, faces, min_corner=(-1.9, -2.4, -0.42), max_corner=(-1.15, 2.7, 0.42), side_color=(120, 96, 72), top_color=(214, 194, 162), side_material='stone', top_material='bone')
    _append_box(vertices, faces, min_corner=(1.15, -2.4, -0.42), max_corner=(1.9, 2.7, 0.42), side_color=(120, 96, 72), top_color=(214, 194, 162), side_material='stone', top_material='bone')
    _append_box(vertices, faces, min_corner=(-1.9, 2.05, -0.54), max_corner=(1.9, 2.78, 0.54), side_color=(192, 150, 96), top_color=(236, 218, 186), side_material='amber', top_material='bone')
    _append_box(vertices, faces, min_corner=(-1.56, 1.4, -0.32), max_corner=(1.56, 2.03, 0.32), side_color=(96, 129, 116), top_color=(220, 206, 172), side_material='jade', top_material='bone')
    _append_box(vertices, faces, min_corner=(-0.34, -1.15, -0.26), max_corner=(0.34, 1.08, 0.26), side_color=(104, 132, 118), top_color=(232, 214, 180), side_material='jade', top_material='bone')
    return Mesh(name=name, vertices=tuple(vertices), faces=tuple(faces))


def neural_relay_mesh(name: str = 'neural_relay') -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    _append_box(vertices, faces, min_corner=(-0.55, -0.55, -0.55), max_corner=(0.55, 0.55, 0.55), side_color=(92, 128, 116), top_color=(224, 214, 186), side_material='jade', top_material='bone')
    _append_box(vertices, faces, min_corner=(-2.2, -0.18, -0.18), max_corner=(-0.55, 0.18, 0.18), side_color=(92, 128, 116), top_color=(224, 214, 186), side_material='jade', top_material='bone')
    _append_box(vertices, faces, min_corner=(0.55, -0.18, -0.18), max_corner=(2.2, 0.18, 0.18), side_color=(92, 128, 116), top_color=(224, 214, 186), side_material='jade', top_material='bone')
    _append_box(vertices, faces, min_corner=(-0.18, -0.18, -2.2), max_corner=(0.18, 0.18, -0.55), side_color=(92, 128, 116), top_color=(224, 214, 186), side_material='jade', top_material='bone')
    _append_box(vertices, faces, min_corner=(-0.18, -0.18, 0.55), max_corner=(0.18, 0.18, 2.2), side_color=(92, 128, 116), top_color=(224, 214, 186), side_material='jade', top_material='bone')
    _append_box(vertices, faces, min_corner=(-0.18, 0.55, -0.18), max_corner=(0.18, 2.15, 0.18), side_color=(188, 144, 92), top_color=(238, 220, 190), side_material='amber', top_material='bone')
    _append_box(vertices, faces, min_corner=(-0.92, 2.15, -0.92), max_corner=(0.92, 2.7, 0.92), side_color=(120, 96, 72), top_color=(226, 208, 178), side_material='stone', top_material='bone')
    return Mesh(name=name, vertices=tuple(vertices), faces=tuple(faces))


def ooze_pod_mesh(name: str = 'ooze_pod') -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    _append_box(vertices, faces, min_corner=(-0.95, -1.25, -0.95), max_corner=(0.95, -0.2, 0.95), side_color=(76, 118, 82), top_color=(142, 188, 136), bottom_color=(48, 74, 50), side_material='jade', top_material='jade', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.72, -0.2, -0.72), max_corner=(0.72, 0.92, 0.72), side_color=(98, 146, 96), top_color=(182, 228, 164), bottom_color=(54, 84, 56), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.26, 0.92, -0.26), max_corner=(0.26, 1.62, 0.26), side_color=(120, 176, 112), top_color=(214, 244, 196), bottom_color=(64, 98, 64), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-1.32, -0.6, -0.24), max_corner=(-0.82, 0.34, 0.24), side_color=(86, 132, 88), top_color=(174, 220, 156), bottom_color=(56, 84, 58), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(0.82, -0.54, -0.22), max_corner=(1.28, 0.4, 0.22), side_color=(86, 132, 88), top_color=(174, 220, 156), bottom_color=(56, 84, 58), side_material='jade', top_material='bone', bottom_material='shadow')
    return Mesh(name=name, vertices=tuple(vertices), faces=tuple(faces))


def patoot_mesh(name: str = 'patoot') -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    _append_box(vertices, faces, min_corner=(-0.75, -0.62, -0.48), max_corner=(0.46, 0.18, 0.5), side_color=(86, 126, 94), top_color=(182, 210, 164), bottom_color=(48, 70, 56), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(0.2, -0.12, -0.16), max_corner=(0.98, 0.84, 0.22), side_color=(96, 138, 106), top_color=(204, 228, 188), bottom_color=(58, 82, 64), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(0.76, 0.32, -0.24), max_corner=(1.36, 0.92, 0.28), side_color=(108, 148, 118), top_color=(220, 236, 202), bottom_color=(66, 90, 72), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(1.26, 0.46, -0.12), max_corner=(1.76, 0.72, 0.16), side_color=(182, 166, 128), top_color=(238, 230, 206), bottom_color=(88, 76, 54), side_material='amber', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-1.2, -0.12, -0.12), max_corner=(-0.72, 0.18, 0.16), side_color=(92, 130, 104), top_color=(200, 224, 184), bottom_color=(52, 78, 62), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-1.66, -0.02, -0.08), max_corner=(-1.12, 0.12, 0.14), side_color=(104, 146, 118), top_color=(208, 232, 192), bottom_color=(58, 82, 66), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(0.54, 0.88, -0.08), max_corner=(1.12, 1.28, 0.12), side_color=(126, 154, 128), top_color=(236, 224, 192), bottom_color=(66, 86, 70), side_material='stone', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.28, -1.14, -0.12), max_corner=(-0.02, -0.22, 0.12), side_color=(122, 112, 86), top_color=(238, 218, 184), bottom_color=(68, 56, 42), side_material='amber', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(0.1, -1.18, -0.12), max_corner=(0.36, -0.24, 0.12), side_color=(122, 112, 86), top_color=(238, 218, 184), bottom_color=(68, 56, 42), side_material='amber', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(0.34, -1.3, -0.2), max_corner=(0.66, -1.08, 0.18), side_color=(212, 176, 110), top_color=(246, 230, 188), bottom_color=(86, 70, 48), side_material='amber', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.84, -0.18, -0.72), max_corner=(-0.2, 0.06, 0.72), side_color=(76, 112, 90), top_color=(164, 196, 150), bottom_color=(44, 64, 50), side_material='jade', top_material='bone', bottom_material='shadow')
    return Mesh(name=name, vertices=tuple(vertices), faces=tuple(faces))


def tutorial_stage_mesh(name: str = 'tutorial_stage') -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    _append_box(vertices, faces, min_corner=(-4.2, -1.75, -4.4), max_corner=(4.2, -1.24, 4.4), side_color=(88, 72, 58), top_color=(146, 116, 84), bottom_color=(54, 42, 34), side_material='stone', top_material='amber', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-2.8, -1.24, -2.6), max_corner=(2.8, -0.96, 2.8), side_color=(96, 82, 62), top_color=(166, 136, 96), bottom_color=(56, 46, 36), side_material='stone', top_material='amber', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-3.8, -0.96, 2.72), max_corner=(3.8, -0.7, 3.12), side_color=(78, 108, 94), top_color=(164, 198, 164), bottom_color=(42, 62, 48), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-3.7, -0.96, -3.18), max_corner=(3.7, -0.72, -2.72), side_color=(78, 108, 94), top_color=(164, 198, 164), bottom_color=(42, 62, 48), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-3.66, -0.96, -3.18), max_corner=(-3.22, 0.2, 3.12), side_color=(118, 94, 72), top_color=(214, 194, 164), bottom_color=(60, 48, 38), side_material='stone', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(3.22, -0.96, -3.18), max_corner=(3.66, 0.2, 3.12), side_color=(118, 94, 72), top_color=(214, 194, 164), bottom_color=(60, 48, 38), side_material='stone', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.82, -0.96, 2.9), max_corner=(0.82, 0.58, 3.34), side_color=(184, 146, 98), top_color=(238, 220, 188), bottom_color=(72, 58, 42), side_material='amber', top_material='bone', bottom_material='shadow')
    return Mesh(name=name, vertices=tuple(vertices), faces=tuple(faces))


def drone_mesh(name: str = 'drone') -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    _append_box(vertices, faces, min_corner=(-0.72, -0.18, -0.72), max_corner=(0.72, 0.18, 0.72), side_color=(90, 122, 112), top_color=(210, 222, 212), bottom_color=(52, 62, 58), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.22, -0.34, -0.94), max_corner=(0.22, 0.34, 0.94), side_color=(182, 142, 92), top_color=(236, 218, 184), bottom_color=(78, 62, 44), side_material='amber', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.94, -0.34, -0.22), max_corner=(0.94, 0.34, 0.22), side_color=(182, 142, 92), top_color=(236, 218, 184), bottom_color=(78, 62, 44), side_material='amber', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.18, 0.18, -0.18), max_corner=(0.18, 0.84, 0.18), side_color=(108, 150, 136), top_color=(236, 246, 220), bottom_color=(66, 78, 70), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.32, -0.12, 0.82), max_corner=(0.32, 0.12, 1.18), side_color=(216, 178, 112), top_color=(248, 232, 194), bottom_color=(90, 70, 50), side_material='amber', top_material='bone', bottom_material='shadow')
    return Mesh(name=name, vertices=tuple(vertices), faces=tuple(faces))


def pouch_fluid_mesh(name: str = 'pouch_fluid') -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    _append_box(vertices, faces, min_corner=(-0.38, -0.28, -0.32), max_corner=(0.34, 0.18, 0.28), side_color=(88, 136, 98), top_color=(188, 238, 180), bottom_color=(46, 72, 50), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.18, 0.12, -0.14), max_corner=(0.22, 0.48, 0.18), side_color=(116, 168, 120), top_color=(214, 248, 202), bottom_color=(58, 86, 60), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(-0.52, -0.18, -0.14), max_corner=(-0.18, 0.14, 0.14), side_color=(96, 148, 106), top_color=(196, 236, 186), bottom_color=(48, 74, 52), side_material='jade', top_material='bone', bottom_material='shadow')
    _append_box(vertices, faces, min_corner=(0.12, -0.22, -0.18), max_corner=(0.44, 0.12, 0.16), side_color=(96, 148, 106), top_color=(196, 236, 186), bottom_color=(48, 74, 52), side_material='jade', top_material='bone', bottom_material='shadow')
    return Mesh(name=name, vertices=tuple(vertices), faces=tuple(faces))


def load_obj_mesh(path: Path) -> Mesh:
    vertices: list[Vec3] = []
    faces: list[Face] = []
    if not path.exists():
        raise FileNotFoundError(f'OBJ file not found: {path}')
    for raw_line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('v '):
            _, x, y, z = line.split()[:4]
            vertices.append(Vec3(float(x), float(y), float(z)))
        elif line.startswith('f '):
            parts = line.split()[1:]
            indices: list[int] = []
            for part in parts:
                head = part.split('/')[0]
                if not head:
                    continue
                indices.append(int(head) - 1)
            if len(indices) < 3:
                continue
            for start in range(1, len(indices) - 1):
                faces.append(Face((indices[0], indices[start], indices[start + 1]), (168, 132, 92), 'stone'))
    if not vertices or not faces:
        raise ValueError(f'OBJ mesh did not contain usable geometry: {path}')
    return Mesh(name=path.stem, vertices=tuple(vertices), faces=tuple(faces))


GLTF_COMPONENT_FORMATS = {
    5120: ('b', 1),
    5121: ('B', 1),
    5122: ('h', 2),
    5123: ('H', 2),
    5125: ('I', 4),
    5126: ('f', 4),
}

GLTF_TYPE_COUNTS = {
    'SCALAR': 1,
    'VEC2': 2,
    'VEC3': 3,
    'VEC4': 4,
}


def _decode_data_uri(uri: str) -> bytes:
    _, encoded = uri.split(',', 1)
    return base64.b64decode(encoded)


def _normalize_mesh_vertices(vertices: list[Vec3], *, target_height: float = 4.0) -> tuple[Vec3, ...]:
    if not vertices:
        return tuple()
    min_x = min(vertex.x for vertex in vertices)
    max_x = max(vertex.x for vertex in vertices)
    min_y = min(vertex.y for vertex in vertices)
    max_y = max(vertex.y for vertex in vertices)
    min_z = min(vertex.z for vertex in vertices)
    max_z = max(vertex.z for vertex in vertices)
    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z
    max_extent = max(size_x, size_y, size_z, 1e-5)
    scale = target_height / max_extent
    center_x = (min_x + max_x) * 0.5
    center_z = (min_z + max_z) * 0.5
    return tuple(
        Vec3((vertex.x - center_x) * scale, (vertex.y - min_y) * scale, (vertex.z - center_z) * scale)
        for vertex in vertices
    )


def _load_gltf_buffers(gltf: dict, glb_bin_chunk: bytes | None, root: Path) -> list[bytes]:
    buffers: list[bytes] = []
    for index, buffer in enumerate(gltf.get('buffers', [])):
        uri = buffer.get('uri')
        if uri is None:
            if index == 0 and glb_bin_chunk is not None:
                buffers.append(glb_bin_chunk)
                continue
            raise ValueError(f'GLTF buffer {index} is missing binary data.')
        if str(uri).startswith('data:'):
            buffers.append(_decode_data_uri(str(uri)))
            continue
        buffer_path = Path(str(uri))
        if not buffer_path.is_absolute():
            buffer_path = (root / buffer_path).resolve()
        buffers.append(buffer_path.read_bytes())
    return buffers


def _read_gltf_accessor(gltf: dict, accessor_index: int, buffers: list[bytes]) -> list[float] | list[tuple[float, ...]]:
    accessor = gltf['accessors'][accessor_index]
    buffer_view = gltf['bufferViews'][accessor['bufferView']]
    buffer_bytes = buffers[buffer_view['buffer']]
    component_type = int(accessor['componentType'])
    component_format, component_size = GLTF_COMPONENT_FORMATS[component_type]
    type_name = str(accessor['type'])
    component_count = GLTF_TYPE_COUNTS[type_name]
    count = int(accessor['count'])
    stride = int(buffer_view.get('byteStride', component_size * component_count))
    start = int(buffer_view.get('byteOffset', 0)) + int(accessor.get('byteOffset', 0))
    values: list[float] | list[tuple[float, ...]] = []
    for item_index in range(count):
        offset = start + item_index * stride
        chunk = struct.unpack_from('<' + component_format * component_count, buffer_bytes, offset)
        if component_count == 1:
            values.append(chunk[0])
        else:
            values.append(tuple(float(value) for value in chunk))
    return values


def load_glb_mesh(path: Path) -> Mesh:
    if not path.exists():
        raise FileNotFoundError(f'GLB file not found: {path}')
    raw = path.read_bytes()
    if raw[:4] != b'glTF':
        raise ValueError(f'Unsupported GLB header: {path}')
    version = struct.unpack_from('<I', raw, 4)[0]
    if version != 2:
        raise ValueError(f'Unsupported GLB version {version}: {path}')
    total_length = struct.unpack_from('<I', raw, 8)[0]
    cursor = 12
    gltf_json: dict | None = None
    glb_bin_chunk: bytes | None = None
    while cursor < total_length:
        chunk_length, chunk_type = struct.unpack_from('<II', raw, cursor)
        cursor += 8
        chunk_data = raw[cursor:cursor + chunk_length]
        cursor += chunk_length
        if chunk_type == 0x4E4F534A:
            gltf_json = json.loads(chunk_data.decode('utf-8'))
        elif chunk_type == 0x004E4942:
            glb_bin_chunk = chunk_data
    if not isinstance(gltf_json, dict):
        raise ValueError(f'GLB did not contain a JSON chunk: {path}')
    buffers = _load_gltf_buffers(gltf_json, glb_bin_chunk, path.parent)
    vertices: list[Vec3] = []
    faces: list[Face] = []
    mesh_color_cycle = [
        ((173, 131, 93), 'stone'),
        ((203, 148, 92), 'amber'),
        ((96, 132, 116), 'jade'),
        ((228, 210, 176), 'bone'),
    ]
    vertex_offset = 0
    for mesh_index, mesh in enumerate(gltf_json.get('meshes', [])):
        primitives = mesh.get('primitives', [])
        for primitive_index, primitive in enumerate(primitives):
            if int(primitive.get('mode', 4)) != 4:
                continue
            attributes = primitive.get('attributes', {})
            position_accessor = attributes.get('POSITION')
            if position_accessor is None:
                continue
            positions = _read_gltf_accessor(gltf_json, int(position_accessor), buffers)
            primitive_vertices = [Vec3(float(item[0]), float(item[1]), float(item[2])) for item in positions if isinstance(item, tuple) and len(item) >= 3]
            if not primitive_vertices:
                continue
            primitive_vertices = list(_normalize_mesh_vertices(primitive_vertices))
            vertices.extend(primitive_vertices)
            if 'indices' in primitive:
                indices_raw = _read_gltf_accessor(gltf_json, int(primitive['indices']), buffers)
                indices = [int(value) + vertex_offset for value in indices_raw if not isinstance(value, tuple)]
            else:
                indices = list(range(vertex_offset, vertex_offset + len(primitive_vertices)))
            color, material = mesh_color_cycle[(mesh_index + primitive_index) % len(mesh_color_cycle)]
            for start in range(0, len(indices) - 2, 3):
                faces.append(Face((indices[start], indices[start + 1], indices[start + 2]), color, material))
            vertex_offset += len(primitive_vertices)
    if not vertices or not faces:
        raise ValueError(f'GLB mesh did not contain usable triangle geometry: {path}')
    return Mesh(name=path.stem, vertices=tuple(vertices), faces=tuple(faces))


class DodoPseudo3DEngine:
    def __init__(self, width: int = 480, height: int = 270, scene_manifest_path: Path | None = None) -> None:
        self.width = width
        self.height = height
        self.mesh_library = {
            'cube': cube_mesh(),
            'pedestal': pedestal_mesh(),
            'monolith': monolith_mesh(),
            'arch': arch_mesh(),
            'shard': shard_mesh(),
            'spire': spire_mesh(),
            'deco_frame': deco_frame_mesh(),
            'neural_relay': neural_relay_mesh(),
            'ooze_pod': ooze_pod_mesh(),
            'patoot': patoot_mesh(),
            'tutorial_stage': tutorial_stage_mesh(),
            'drone': drone_mesh(),
            'pouch_fluid': pouch_fluid_mesh(),
        }
        self.mesh_cache: dict[str, Mesh] = {}
        self.image_cache: dict[str, object] = {}
        self.light_direction = Vec3(-0.45, 0.82, -0.35).normalized()
        self.scene_manifest_path: Path | None = None
        self.scene_metadata: dict = {}
        self.runtime_overrides: dict[str, object] = {}
        self.mesh_instances: list[MeshInstance] = []
        self.billboards: list[BillboardInstance] = []
        self.label_font = ImageFont.load_default() if ImageFont is not None else None
        if scene_manifest_path is not None and Path(scene_manifest_path).exists():
            self.load_scene_manifest(Path(scene_manifest_path))
        else:
            self._load_default_scene()

    def _load_default_scene(self) -> None:
        self.scene_metadata = {'name': 'default_dodo_scene', 'source': 'builtin', 'camera': {'orbit': 0.58, 'elevation': 0.22}}
        self.mesh_instances = [
            MeshInstance('gate_left', self.mesh_library['cube'], Vec3(-2.7, -0.1, 8.0), Vec3(0.18, 0.35, 0.0), 1.4, label='Gate Left', scripts=[{'type': 'spin', 'speed': 0.18}, {'type': 'bob', 'amplitude': 0.08, 'speed': 0.8}]),
            MeshInstance('gate_right', self.mesh_library['cube'], Vec3(2.5, -0.35, 9.6), Vec3(0.22, -0.5, 0.0), 1.8, label='Gate Right', scripts=[{'type': 'spin', 'speed': -0.14}, {'type': 'bob', 'amplitude': 0.07, 'speed': 0.9}]),
            MeshInstance('spine', self.mesh_library['monolith'], Vec3(0.0, 0.8, 12.4), Vec3(0.0, 0.8, 0.1), 1.0, label='Spine', scripts=[{'type': 'spin', 'speed': 0.08}]),
            MeshInstance('altar', self.mesh_library['pedestal'], Vec3(0.0, -1.15, 6.0), Vec3(0.0, 0.2, 0.0), 0.95, label='Altar', scripts=[{'type': 'pulse', 'amplitude': 0.05, 'speed': 1.8}]),
        ]
        self.billboards = []

    def load_scene_manifest(self, path: Path) -> None:
        payload = json.loads(path.read_text(encoding='utf-8'))
        self.scene_manifest_path = path
        self.scene_metadata = payload
        self.mesh_instances = []
        self.billboards = []
        for entry in payload.get('scene_entries', []):
            kind = entry.get('kind', 'mesh')
            if kind == 'billboard':
                self.billboards.append(self._parse_billboard(entry, path.parent))
            else:
                self.mesh_instances.append(self._parse_mesh_instance(entry, path.parent))

    def describe_runtime(self) -> dict:
        return {
            'renderer_backend': DODO_SHADER_MANIFEST['backend'],
            'look': DODO_SHADER_MANIFEST['look'],
            'resolution': {'width': self.width, 'height': self.height},
            'mesh_instances': len(self.mesh_instances),
            'billboards': len(self.billboards),
            'scene_manifest': str(self.scene_manifest_path) if self.scene_manifest_path else None,
            'asset_loaders': DODO_SHADER_MANIFEST['asset_loaders'],
            'script_capabilities': DODO_SHADER_MANIFEST['script_capabilities'],
            'scene_state_support': ['export_scene_state', 'apply_scene_state'],
            'shader_manifest': DODO_SHADER_MANIFEST,
            'scene_name': self.scene_metadata.get('showcase_name') or self.scene_metadata.get('name'),
        }

    def set_runtime_overrides(self, overrides: dict[str, object] | None) -> None:
        self.runtime_overrides = dict(overrides or {})

    def export_scene_state(self) -> dict:
        return {
            'scene_manifest': str(self.scene_manifest_path) if self.scene_manifest_path else None,
            'scene_name': self.scene_metadata.get('showcase_name') or self.scene_metadata.get('name'),
            'runtime_overrides': dict(self.runtime_overrides),
            'mesh_instances': [self._serialize_mesh_instance(instance) for instance in self.mesh_instances],
            'billboards': [self._serialize_billboard(instance) for instance in self.billboards],
        }

    def apply_scene_state(self, state: dict | None) -> None:
        if not isinstance(state, dict):
            return
        if isinstance(state.get('runtime_overrides'), dict):
            self.set_runtime_overrides(state.get('runtime_overrides'))
        mesh_instances = state.get('mesh_instances', [])
        if isinstance(mesh_instances, list):
            for entry in mesh_instances:
                if not isinstance(entry, dict):
                    continue
                target = self._find_mesh_instance(str(entry.get('id', '')))
                if target is None:
                    continue
                target.position = Vec3.from_value(entry.get('position'), default=target.position)
                target.rotation = Vec3.from_value(entry.get('rotation'), default=target.rotation)
                target.scale = float(entry.get('scale', target.scale))
                target.material = str(entry.get('material', target.material))
                target.label = str(entry.get('label', target.label))
                if isinstance(entry.get('scripts'), list):
                    target.scripts = list(entry.get('scripts', target.scripts))
                if isinstance(entry.get('metadata'), dict):
                    target.metadata = dict(entry.get('metadata', target.metadata))
        billboards = state.get('billboards', [])
        if isinstance(billboards, list):
            for entry in billboards:
                if not isinstance(entry, dict):
                    continue
                target = self._find_billboard(str(entry.get('id', '')))
                if target is None:
                    continue
                target.position = Vec3.from_value(entry.get('position'), default=target.position)
                width = int(entry.get('width', target.size[0]))
                height = int(entry.get('height', target.size[1]))
                target.size = (width, height)
                image_path = entry.get('image_path', target.image_path)
                target.image_path = str(image_path) if image_path else None
                target.label = str(entry.get('label', target.label))
                tint = entry.get('tint')
                if isinstance(tint, (list, tuple)) and len(tint) == 3:
                    target.tint = (int(tint[0]), int(tint[1]), int(tint[2]))
                if isinstance(entry.get('scripts'), list):
                    target.scripts = list(entry.get('scripts', target.scripts))
                if isinstance(entry.get('metadata'), dict):
                    target.metadata = dict(entry.get('metadata', target.metadata))

    def write_preview(self, output_path: Path, orbit: float = 0.5, elevation: float = 0.2, shader_mix: float = 0.85, time_s: float = 1.25, scene_manifest_path: Path | None = None) -> dict:
        if scene_manifest_path is not None and scene_manifest_path.exists():
            self.load_scene_manifest(scene_manifest_path)
        image, stats = self.render_preview(orbit=orbit, elevation=elevation, shader_mix=shader_mix, time_s=time_s)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        payload = {'output': str(output_path), 'stats': stats, 'runtime': self.describe_runtime(), 'scene': self.scene_metadata}
        output_path.with_suffix('.json').write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
        return payload

    def render_preview(self, orbit: float, elevation: float, shader_mix: float, time_s: float):
        if Image is None or ImageDraw is None:
            raise RuntimeError('Pillow is required for the DODO pseudo-3D renderer.')
        image = Image.new('RGBA', (self.width, self.height), (18, 25, 22, 255))
        draw = ImageDraw.Draw(image, 'RGBA')
        self._draw_sky(draw, time_s, shader_mix)
        horizon = int(self.height * (0.38 - elevation * 0.05))
        self._draw_floor(draw, orbit, shader_mix, horizon)
        runtime_state = self._build_runtime_state(time_s)
        stats = self._draw_scene(image, draw, orbit, elevation, shader_mix, time_s, runtime_state)
        self._apply_canvas_post(image, shader_mix, time_s)
        stats['passes'] = [entry['id'] for entry in DODO_SHADER_MANIFEST['passes']]
        stats['runtime_state'] = runtime_state
        return image, stats

    def _parse_mesh_instance(self, entry: dict, manifest_root: Path) -> MeshInstance:
        loader = str(entry.get('loader', 'builtin'))
        mesh_name = str(entry.get('mesh', 'cube'))
        mesh = self._resolve_mesh(loader, mesh_name, manifest_root)
        return MeshInstance(
            name=str(entry.get('id', mesh_name)),
            mesh=mesh,
            position=Vec3.from_value(entry.get('position'), default=Vec3(0.0, 0.0, 6.0)),
            rotation=Vec3.from_value(entry.get('rotation'), default=Vec3(0.0, 0.0, 0.0)),
            scale=float(entry.get('scale', 1.0)),
            material=str(entry.get('material', 'stone')),
            label=str(entry.get('label', entry.get('id', mesh_name))),
            scripts=list(entry.get('scripts', [])),
            metadata=dict(entry.get('metadata', {})),
        )

    def _parse_billboard(self, entry: dict, manifest_root: Path) -> BillboardInstance:
        image_path = entry.get('image_path')
        if image_path:
            resolved = Path(image_path)
            if not resolved.is_absolute():
                resolved = (manifest_root / resolved).resolve()
            image_path = str(resolved)
        tint = entry.get('tint', [204, 164, 110])
        return BillboardInstance(
            name=str(entry.get('id', 'billboard')),
            position=Vec3.from_value(entry.get('position'), default=Vec3(0.0, 0.0, 8.0)),
            size=(int(entry.get('width', 420)), int(entry.get('height', 280))),
            image_path=image_path,
            label=str(entry.get('label', entry.get('id', 'billboard'))),
            tint=(int(tint[0]), int(tint[1]), int(tint[2])),
            scripts=list(entry.get('scripts', [])),
            metadata=dict(entry.get('metadata', {})),
        )

    def _serialize_mesh_instance(self, instance: MeshInstance) -> dict:
        return {
            'id': instance.name,
            'position': [instance.position.x, instance.position.y, instance.position.z],
            'rotation': [instance.rotation.x, instance.rotation.y, instance.rotation.z],
            'scale': instance.scale,
            'material': instance.material,
            'label': instance.label,
            'scripts': list(instance.scripts),
            'metadata': dict(instance.metadata),
        }

    def _serialize_billboard(self, instance: BillboardInstance) -> dict:
        return {
            'id': instance.name,
            'position': [instance.position.x, instance.position.y, instance.position.z],
            'width': instance.size[0],
            'height': instance.size[1],
            'image_path': instance.image_path,
            'label': instance.label,
            'tint': [instance.tint[0], instance.tint[1], instance.tint[2]],
            'scripts': list(instance.scripts),
            'metadata': dict(instance.metadata),
        }

    def _find_mesh_instance(self, instance_id: str) -> MeshInstance | None:
        for instance in self.mesh_instances:
            if instance.name == instance_id:
                return instance
        return None

    def _find_billboard(self, instance_id: str) -> BillboardInstance | None:
        for instance in self.billboards:
            if instance.name == instance_id:
                return instance
        return None

    def _resolve_mesh(self, loader: str, mesh_name: str, manifest_root: Path) -> Mesh:
        if loader == 'builtin':
            return self.mesh_library.get(mesh_name, self.mesh_library['cube'])
        if loader == 'obj':
            mesh_path = Path(mesh_name)
            if not mesh_path.is_absolute():
                mesh_path = (manifest_root / mesh_path).resolve()
            cache_key = str(mesh_path)
            if cache_key not in self.mesh_cache:
                self.mesh_cache[cache_key] = load_obj_mesh(mesh_path)
            return self.mesh_cache[cache_key]
        if loader == 'glb':
            mesh_path = Path(mesh_name)
            if not mesh_path.is_absolute():
                mesh_path = (manifest_root / mesh_path).resolve()
            cache_key = str(mesh_path)
            if cache_key not in self.mesh_cache:
                self.mesh_cache[cache_key] = load_glb_mesh(mesh_path)
            return self.mesh_cache[cache_key]
        return self.mesh_library['cube']

    def _camera_position(self, orbit: float, elevation: float) -> Vec3:
        focus_z = float(self.scene_metadata.get('camera', {}).get('focus_z', 9.5))
        return Vec3(math.sin(orbit) * 3.2, 1.3 + elevation * 2.0, focus_z - 13.2 + math.cos(orbit) * 1.2)

    def _camera_rotation(self, orbit: float, elevation: float) -> tuple[float, float]:
        return orbit * 0.55, -0.18 - elevation * 0.28

    def _draw_sky(self, draw, time_s: float, shader_mix: float) -> None:
        for row in range(self.height):
            t = row / max(1, self.height - 1)
            amber = 64 + int(118 * (1.0 - t))
            jade = 88 + int(80 * math.sin(time_s * 0.35 + t * 2.1) * 0.5 + 40)
            blue = 62 + int(92 * (1.0 - min(1.0, t * 1.2)))
            blend = 0.35 + shader_mix * 0.4
            color = (int(amber * blend), int(jade * (0.65 + shader_mix * 0.35)), int(blue * (0.7 + shader_mix * 0.3)), 255)
            draw.line((0, row, self.width, row), fill=color)

    def _draw_floor(self, draw, orbit: float, shader_mix: float, horizon: int) -> None:
        horizon = max(32, min(self.height - 24, horizon))
        for row in range(horizon, self.height):
            depth_t = (row - horizon) / max(1, self.height - horizon)
            curve = depth_t * depth_t
            brightness = 32 + int(70 * depth_t)
            sway = math.sin(orbit + depth_t * 9.0) * 18.0 * shader_mix
            left = -16 + sway - curve * 32
            right = self.width + 16 + sway + curve * 32
            stripe = int((depth_t * 15.0 + orbit * 2.0) % 2)
            floor_color = (35 + stripe * 8, 42 + brightness // 3, 34 + brightness // 5, 255)
            draw.line((left, row, right, row), fill=floor_color)
            if row % 12 == 0:
                guide = (62, 82, 70, 180)
                draw.line((self.width * 0.5 + sway, row, self.width * 0.5 + sway + curve * 120, self.height), fill=guide, width=1)
                draw.line((self.width * 0.5 + sway, row, self.width * 0.5 + sway - curve * 120, self.height), fill=guide, width=1)

    def _draw_scene(self, image, draw, orbit: float, elevation: float, shader_mix: float, time_s: float, runtime_state: dict) -> dict:
        camera_pos = self._camera_position(orbit, elevation)
        camera_yaw, camera_pitch = self._camera_rotation(orbit, elevation)
        focal = self.width * 0.9
        draw_ops: list[tuple[float, str, object]] = []
        faces_drawn = 0
        mesh_count = 0
        billboard_count = 0

        for obj in self.mesh_instances:
            position, rotation, scale = self._animate_transform(obj.position, obj.rotation, obj.scale, obj.scripts, time_s, obj.metadata, runtime_state)
            world_vertices = [transform_vertex(vertex, position, rotation, scale) for vertex in obj.mesh.vertices]
            camera_vertices = [self._world_to_camera(vertex, camera_pos, camera_yaw, camera_pitch) for vertex in world_vertices]
            screen_vertices = [self._project(vertex, focal) for vertex in camera_vertices]
            mesh_count += 1
            for face in obj.mesh.faces:
                v0 = camera_vertices[face.indices[0]]
                v1 = camera_vertices[face.indices[1]]
                v2 = camera_vertices[face.indices[2]]
                if min(v0.z, v1.z, v2.z) <= 0.2:
                    continue
                edge1 = v1 - v0
                edge2 = v2 - v0
                normal = edge1.cross(edge2).normalized()
                if normal.z >= -0.02:
                    continue
                depth = (v0.z + v1.z + v2.z) / 3.0
                points = [screen_vertices[index] for index in face.indices]
                if any(point is None for point in points):
                    continue
                face_color = self._shade_face(face.color, normal, depth, shader_mix, face.material or obj.material)
                draw_ops.append((depth, 'mesh_face', {'points': points, 'color': face_color, 'material': face.material or obj.material}))
                faces_drawn += 1

        for billboard in self.billboards:
            position, _rotation, scale = self._animate_transform(billboard.position, Vec3(0.0, 0.0, 0.0), 1.0, billboard.scripts, time_s, billboard.metadata, runtime_state)
            camera_vertex = self._world_to_camera(position, camera_pos, camera_yaw, camera_pitch)
            screen_point = self._project(camera_vertex, focal)
            if screen_point is None or camera_vertex.z <= 0.25:
                continue
            draw_ops.append((camera_vertex.z, 'billboard', {'billboard': billboard, 'screen_point': screen_point, 'depth': camera_vertex.z, 'scale': scale}))
            billboard_count += 1

        draw_ops.sort(key=lambda item: item[0], reverse=True)
        for _depth, kind, payload in draw_ops:
            if kind == 'mesh_face':
                outline = (18, 22, 19, 220)
                if payload['material'] == 'bone':
                    outline = (80, 62, 45, 200)
                draw.polygon(payload['points'], fill=payload['color'], outline=outline)
            else:
                self._draw_billboard(image, payload['billboard'], payload['screen_point'], payload['depth'], payload['scale'])

        return {
            'faces_drawn': faces_drawn,
            'mesh_instances': mesh_count,
            'billboards': billboard_count,
            'scene_name': self.scene_metadata.get('showcase_name') or self.scene_metadata.get('name'),
            'scripted_entries': sum(1 for item in self.mesh_instances if item.scripts) + sum(1 for item in self.billboards if item.scripts),
            'orbit': round(orbit, 3),
            'elevation': round(elevation, 3),
            'shader_mix': round(shader_mix, 3),
        }

    def _build_runtime_state(self, time_s: float) -> dict:
        concept_translation = self.scene_metadata.get('concept_translation', {}) if isinstance(self.scene_metadata, dict) else {}
        sequencer = concept_translation.get('erp_sequencer', {}) if isinstance(concept_translation, dict) else {}
        thresholds = [str(item) for item in sequencer.get('thresholds', [])] if isinstance(sequencer, dict) else []
        pressure_wave = 0.5 + 0.5 * math.sin(time_s * 0.52)
        relay_resonance = 0.5 + 0.5 * math.sin(time_s * 1.28 + 0.45)
        ooze_surge = 0.5 + 0.5 * math.sin(time_s * 1.74 - 0.25)
        fracture_pulse = max(0.0, math.sin(time_s * 2.16 - 0.58))
        stall_decay = 0.5 + 0.5 * math.sin(time_s * 0.34 + 1.15)
        threshold_index = min(len(thresholds) - 1, int(pressure_wave * len(thresholds))) if thresholds else -1
        active_threshold = thresholds[threshold_index] if 0 <= threshold_index < len(thresholds) else None
        runtime_state = {
            'time_s': round(time_s, 3),
            'pressure_wave': round(pressure_wave, 4),
            'relay_resonance': round(relay_resonance, 4),
            'ooze_surge': round(ooze_surge, 4),
            'fracture_pulse': round(fracture_pulse, 4),
            'stall_decay': round(stall_decay, 4),
            'thresholds': thresholds,
            'active_threshold_index': threshold_index,
            'active_threshold': active_threshold,
            'patoot_attack_cue': sequencer.get('patoot_attack') if isinstance(sequencer, dict) else None,
            'neural_map': sequencer.get('neural_map') if isinstance(sequencer, dict) else None,
        }
        if self.runtime_overrides:
            runtime_state.update(self.runtime_overrides)
        return runtime_state

    def _draw_billboard(self, image, billboard: BillboardInstance, screen_point: tuple[float, float], depth: float, scale: float) -> None:
        width = max(72, int((billboard.size[0] / max(1.0, depth)) * 1.6 * scale))
        height = max(56, int((billboard.size[1] / max(1.0, depth)) * 1.6 * scale))
        left = int(screen_point[0] - width / 2)
        top = int(screen_point[1] - height * 0.88)
        source = self._resolve_billboard_image(billboard.image_path, width, height, billboard.tint, billboard.label)
        image.alpha_composite(source, (left, top))
        if ImageDraw is None:
            return
        draw = ImageDraw.Draw(image, 'RGBA')
        label_top = top + height + 4
        label_height = 18
        draw.rounded_rectangle((left + 10, label_top, left + width - 10, label_top + label_height), radius=6, fill=(12, 17, 15, 170), outline=(205, 170, 118, 160), width=1)
        draw.text((left + 16, label_top + 3), billboard.label[:36], fill=(243, 231, 212, 255), font=self.label_font)

    def _resolve_billboard_image(self, image_path: str | None, width: int, height: int, tint: tuple[int, int, int], label: str):
        if Image is None or ImageDraw is None:
            raise RuntimeError('Pillow is required for billboard rendering.')
        cache_key = f'{image_path}|{width}|{height}'
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        if image_path and Path(image_path).exists():
            source = Image.open(image_path).convert('RGBA')
            source.thumbnail((width, height), Image.Resampling.LANCZOS)
            card = Image.new('RGBA', (width, height), (18, 23, 20, 210))
            offset = ((width - source.width) // 2, (height - source.height) // 2)
            card.alpha_composite(source, offset)
        else:
            card = Image.new('RGBA', (width, height), (20, 26, 23, 220))
            draw = ImageDraw.Draw(card, 'RGBA')
            for row in range(height):
                shade = int(36 + 44 * (row / max(1, height - 1)))
                draw.line((0, row, width, row), fill=(min(255, tint[0] // 2 + shade), min(255, tint[1] // 2 + shade // 2), min(255, tint[2] // 2 + shade // 3), 255))
            draw.rounded_rectangle((6, 6, width - 6, height - 6), radius=12, outline=(245, 205, 154, 180), width=2)
            draw.text((14, 14), label[:28], fill=(250, 240, 220, 255), font=self.label_font)
        overlay = ImageDraw.Draw(card, 'RGBA')
        overlay.rounded_rectangle((0, 0, width - 1, height - 1), radius=10, outline=(243, 202, 148, 155), width=2)
        self.image_cache[cache_key] = card
        return card

    def _animate_transform(self, position: Vec3, rotation: Vec3, scale: float, scripts: list[dict], time_s: float, metadata: dict, runtime_state: dict) -> tuple[Vec3, Vec3, float]:
        animated_position = position
        animated_rotation = rotation
        animated_scale = scale
        for script in scripts:
            script_type = str(script.get('type', '')).lower()
            speed = float(script.get('speed', 1.0))
            phase = float(script.get('phase', 0.0))
            sample = time_s * speed + phase
            if script_type == 'spin':
                axis = script.get('axis', 'y')
                if axis == 'x':
                    animated_rotation = Vec3(animated_rotation.x + sample, animated_rotation.y, animated_rotation.z)
                elif axis == 'z':
                    animated_rotation = Vec3(animated_rotation.x, animated_rotation.y, animated_rotation.z + sample)
                else:
                    animated_rotation = Vec3(animated_rotation.x, animated_rotation.y + sample, animated_rotation.z)
            elif script_type == 'bob':
                amplitude = float(script.get('amplitude', 0.12))
                animated_position = Vec3(animated_position.x, animated_position.y + math.sin(sample) * amplitude, animated_position.z)
            elif script_type == 'pulse':
                amplitude = float(script.get('amplitude', 0.08))
                animated_scale = animated_scale * (1.0 + math.sin(sample) * amplitude)
            elif script_type == 'orbit':
                radius = float(script.get('radius', 0.65))
                anchor = Vec3.from_value(script.get('anchor'), default=position)
                animated_position = Vec3(anchor.x + math.cos(sample) * radius, animated_position.y, anchor.z + math.sin(sample) * radius)
            elif script_type == 'drift':
                amplitude_x = float(script.get('amplitude_x', 0.0))
                amplitude_y = float(script.get('amplitude_y', 0.0))
                amplitude_z = float(script.get('amplitude_z', 0.0))
                animated_position = Vec3(
                    animated_position.x + math.cos(sample) * amplitude_x,
                    animated_position.y + math.sin(sample * 1.12) * amplitude_y,
                    animated_position.z + math.sin(sample * 0.84) * amplitude_z,
                )
            elif script_type == 'sway':
                amplitude_x = float(script.get('rotation_x', 0.0))
                amplitude_y = float(script.get('rotation_y', 0.0))
                amplitude_z = float(script.get('rotation_z', 0.0))
                animated_rotation = Vec3(
                    animated_rotation.x + math.sin(sample) * amplitude_x,
                    animated_rotation.y + math.sin(sample * 0.85) * amplitude_y,
                    animated_rotation.z + math.cos(sample) * amplitude_z,
                )
            elif script_type == 'channel_follow':
                channel_name = str(script.get('channel', metadata.get('role', 'pressure_wave')))
                channel_value = float(runtime_state.get(channel_name, 0.0))
                centered = channel_value * 2.0 - 1.0
                wave = math.sin(sample)
                animated_position = Vec3(
                    animated_position.x + centered * wave * float(script.get('x_amplitude', 0.0)),
                    animated_position.y + centered * wave * float(script.get('y_amplitude', 0.0)),
                    animated_position.z + centered * wave * float(script.get('z_amplitude', 0.0)),
                )
                animated_rotation = Vec3(
                    animated_rotation.x + centered * wave * float(script.get('rotation_x', 0.0)),
                    animated_rotation.y + centered * wave * float(script.get('rotation_y', 0.0)),
                    animated_rotation.z + centered * wave * float(script.get('rotation_z', 0.0)),
                )
                animated_scale = animated_scale * (1.0 + channel_value * float(script.get('scale_amplitude', 0.0)))
            elif script_type == 'threshold_gate':
                threshold_name = str(script.get('threshold', metadata.get('threshold', '')))
                thresholds = runtime_state.get('thresholds', []) if isinstance(runtime_state.get('thresholds'), list) else []
                try:
                    threshold_index = thresholds.index(threshold_name)
                except ValueError:
                    threshold_index = int(script.get('threshold_index', 0))
                active_index = int(runtime_state.get('active_threshold_index', -1))
                gate_strength = max(0.0, min(1.0, active_index - threshold_index + 1.0)) if active_index >= 0 else 0.0
                gate_strength *= 0.7 + float(runtime_state.get('fracture_pulse', 0.0)) * 0.3
                wave = math.sin(sample)
                animated_position = Vec3(
                    animated_position.x,
                    animated_position.y + gate_strength * wave * float(script.get('y_amplitude', 0.0)),
                    animated_position.z,
                )
                animated_rotation = Vec3(
                    animated_rotation.x,
                    animated_rotation.y + gate_strength * wave * float(script.get('rotation_y', 0.0)),
                    animated_rotation.z + gate_strength * wave * float(script.get('rotation_z', 0.0)),
                )
                animated_scale = animated_scale * (1.0 + gate_strength * float(script.get('scale_amplitude', 0.0)))
            elif script_type == 'accent_burst':
                burst_window = max(0.0, math.sin(sample))
                burst_strength = burst_window ** float(script.get('curve', 9.0))
                channel_name = str(script.get('channel', ''))
                if channel_name:
                    burst_strength *= max(0.0, min(1.0, float(runtime_state.get(channel_name, 0.0))))
                animated_position = Vec3(
                    animated_position.x + burst_strength * float(script.get('x_amplitude', 0.0)),
                    animated_position.y + burst_strength * float(script.get('y_amplitude', 0.0)),
                    animated_position.z + burst_strength * float(script.get('z_amplitude', 0.0)),
                )
                animated_rotation = Vec3(
                    animated_rotation.x + burst_strength * float(script.get('rotation_x', 0.0)),
                    animated_rotation.y + burst_strength * float(script.get('rotation_y', 0.0)),
                    animated_rotation.z + burst_strength * float(script.get('rotation_z', 0.0)),
                )
                animated_scale = animated_scale * (1.0 + burst_strength * float(script.get('scale_amplitude', 0.0)))
        return animated_position, animated_rotation, animated_scale

    def _world_to_camera(self, vertex: Vec3, camera_pos: Vec3, camera_yaw: float, camera_pitch: float) -> Vec3:
        translated = vertex - camera_pos
        yawed = rotate_y(translated, -camera_yaw)
        pitched = rotate_x(yawed, -camera_pitch)
        return pitched

    def _project(self, vertex: Vec3, focal: float):
        if vertex.z <= 0.2:
            return None
        x = self.width * 0.5 + (vertex.x / vertex.z) * focal
        y = self.height * 0.48 - (vertex.y / vertex.z) * focal
        return (x, y)

    def _shade_face(self, base_color: tuple[int, int, int], normal: Vec3, depth: float, shader_mix: float, material: str) -> tuple[int, int, int, int]:
        lambert = max(0.0, normal.dot(self.light_direction))
        rim = max(0.0, (-normal.z) ** DODO_SHADER_MANIFEST['uniforms']['rim_power'])
        light = 0.24 + lambert * 0.68 + rim * 0.22 * shader_mix
        if material == 'shadow':
            light *= 0.72
        if material == 'amber':
            light += 0.08
        if material == 'jade':
            light += 0.04
        fog = min(0.78, max(0.0, (depth - 5.5) * DODO_SHADER_MANIFEST['uniforms']['fog_density'] * 0.06))
        steps = max(3, int(DODO_SHADER_MANIFEST['uniforms']['palette_steps']))
        light = round(light * steps) / steps
        shaded = [min(255, max(0, int(channel * light))) for channel in base_color]
        fog_color = (104, 122, 110)
        mixed = [int(shaded[index] * (1.0 - fog) + fog_color[index] * fog) for index in range(3)]
        alpha = 255 if depth < 17.0 else 230
        return mixed[0], mixed[1], mixed[2], alpha

    def _apply_canvas_post(self, image, shader_mix: float, time_s: float) -> None:
        pixels = image.load()
        scanline_intensity = DODO_SHADER_MANIFEST['uniforms']['scanline_intensity'] * shader_mix
        for y in range(self.height):
            scanline = 1.0 - scanline_intensity * (0.5 + 0.5 * math.sin(y * 0.62 + time_s * 3.2))
            for x in range(self.width):
                r, g, b, a = pixels[x, y]
                vignette_x = abs((x / max(1, self.width - 1)) - 0.5) * 2.0
                vignette_y = abs((y / max(1, self.height - 1)) - 0.52) * 1.9
                vignette = max(0.72, 1.0 - (vignette_x * vignette_x + vignette_y * vignette_y) * 0.23)
                grain = ((x * 17 + y * 31 + int(time_s * 19)) % 19) - 9
                pixels[x, y] = (
                    max(0, min(255, int(r * scanline * vignette + grain * 0.35))),
                    max(0, min(255, int(g * scanline * vignette + grain * 0.25))),
                    max(0, min(255, int(b * scanline * vignette + grain * 0.15))),
                    a,
                )
