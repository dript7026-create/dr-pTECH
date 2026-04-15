from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
MODELS = ASSETS / "models"
MATERIALS = ASSETS / "materials"
TEXTURES = ASSETS / "textures"
CONFIG = ROOT / "config"


def clamp(v: int) -> int:
	return max(0, min(255, v))


def write_ppm(path: Path, w: int, h: int, pixel_fn) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="ascii") as f:
		f.write(f"P3\n{w} {h}\n255\n")
		for y in range(h):
			row = []
			for x in range(w):
				r, g, b = pixel_fn(x, y)
				row.append(f"{clamp(r)} {clamp(g)} {clamp(b)}")
			f.write(" ".join(row) + "\n")


@dataclass
class Mesh:
	vertices: list[tuple[float, float, float]] = field(default_factory=list)
	faces: list[tuple[int, ...]] = field(default_factory=list)

	def add_box(self, cx: float, cy: float, cz: float, sx: float, sy: float, sz: float) -> None:
		x0, x1 = cx - sx / 2.0, cx + sx / 2.0
		y0, y1 = cy - sy / 2.0, cy + sy / 2.0
		z0, z1 = cz - sz / 2.0, cz + sz / 2.0
		base = len(self.vertices) + 1
		self.vertices.extend(
			[
				(x0, y0, z0),
				(x1, y0, z0),
				(x1, y1, z0),
				(x0, y1, z0),
				(x0, y0, z1),
				(x1, y0, z1),
				(x1, y1, z1),
				(x0, y1, z1),
			]
		)
		self.faces.extend(
			[
				(base + 0, base + 1, base + 2, base + 3),
				(base + 4, base + 5, base + 6, base + 7),
				(base + 0, base + 1, base + 5, base + 4),
				(base + 1, base + 2, base + 6, base + 5),
				(base + 2, base + 3, base + 7, base + 6),
				(base + 3, base + 0, base + 4, base + 7),
			]
		)

	def add_octa_column(self, cx: float, cy: float, cz: float, radius: float, height: float) -> None:
		segments = 36
		angles = [i * (2.0 * math.pi / segments) for i in range(segments)]
		top = [(cx + math.cos(a) * radius, cy + height / 2.0, cz + math.sin(a) * radius) for a in angles]
		bot = [(cx + math.cos(a) * radius, cy - height / 2.0, cz + math.sin(a) * radius) for a in angles]
		top_center = (cx, cy + height / 2.0, cz)
		bot_center = (cx, cy - height / 2.0, cz)
		base = len(self.vertices) + 1
		self.vertices.extend(top + bot + [top_center, bot_center])
		for i in range(segments):
			n = (i + 1) % segments
			self.faces.append((base + i, base + n, base + segments + n, base + segments + i))
			top_center_idx = base + segments * 2
			bot_center_idx = base + segments * 2 + 1
			self.faces.append((top_center_idx, base + i, base + n))
			self.faces.append((bot_center_idx, base + segments + n, base + segments + i))

	def write_obj(self, path: Path, name: str, mtl_name: str) -> None:
		path.parent.mkdir(parents=True, exist_ok=True)
		with path.open("w", encoding="ascii") as f:
			f.write(f"mtllib ../materials/{mtl_name}\n")
			f.write(f"o {name}\n")
			for vx, vy, vz in self.vertices:
				f.write(f"v {vx:.4f} {vy:.4f} {vz:.4f}\n")
			f.write("usemtl body\n")
			for face in self.faces:
				f.write("f " + " ".join(str(idx) for idx in face) + "\n")

	@property
	def poly_count(self) -> int:
		return len(self.faces)


def write_mtl(path: Path, texture_name: str) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="ascii") as f:
		f.write("newmtl body\n")
		f.write("Ka 0.2 0.2 0.2\n")
		f.write("Kd 0.9 0.9 0.9\n")
		f.write("Ks 0.1 0.1 0.1\n")
		f.write("Ns 10.0\n")
		f.write(f"map_Kd ../textures/{texture_name}\n")


def texture_patterns() -> None:
	write_ppm(
		TEXTURES / "metal_robot.ppm",
		320,
		320,
		lambda x, y: (
			148 + ((x * 5 + y * 2) % 34),
			156 + ((x * 3 + y * 4) % 28),
			168 + ((x + y * 5) % 24),
		),
	)
	write_ppm(
		TEXTURES / "metal_robot_marked.ppm",
		320,
		320,
		lambda x, y: (
			126 + ((x * 3 + y * 2) % 36),
			132 + ((x * 2 + y * 5) % 24),
			148 + ((x + y * 4) % 28),
		),
	)
	write_ppm(
		TEXTURES / "scales_lizard_emerald.ppm",
		320,
		320,
		lambda x, y: (
			34 + ((x // 7 + y // 5) % 5) * 14,
			88 + ((x // 6 + y // 7) % 4) * 18,
			38 + ((x // 5 + y // 8) % 3) * 12,
		),
	)
	write_ppm(
		TEXTURES / "scales_lizard_amber.ppm",
		320,
		320,
		lambda x, y: (
			96 + ((x // 7 + y // 5) % 3) * 15,
			70 + ((x // 8 + y // 6) % 4) * 12,
			42 + ((x // 6 + y // 9) % 2) * 10,
		),
	)
	write_ppm(
		TEXTURES / "fur_ape_boss.ppm",
		320,
		320,
		lambda x, y: (
			74 + ((x * 6 + y * 5) % 38),
			56 + ((x * 5 + y * 2) % 24),
			42 + ((x * 3 + y * 8) % 18),
		),
	)
	write_ppm(
		TEXTURES / "office_wallpaper.ppm",
		320,
		320,
		lambda x, y: (
			192 - ((x // 14 + y // 14) % 2) * 14,
			184 - ((x // 12 + y // 11) % 2) * 12,
			172 - ((x // 18 + y // 18) % 2) * 10,
		),
	)
	write_ppm(
		TEXTURES / "office_furniture.ppm",
		320,
		320,
		lambda x, y: (
			110 + ((x // 9 + y // 10) % 4) * 10,
			84 + ((x // 8 + y // 8) % 3) * 8,
			58 + ((x // 6 + y // 6) % 2) * 8,
		),
	)
	write_ppm(
		TEXTURES / "ammo_pickup_glow.ppm",
		320,
		320,
		lambda x, y: (
			134 + ((x * 2 + y * 3) % 84),
			96 + ((x * 4 + y) % 92),
			48 + ((x * 5 + y * 3) % 70),
		),
	)


def robot_player_mesh() -> Mesh:
	m = Mesh()
	for side in (-0.28, 0.28):
		m.add_octa_column(side, 0.56, 0.0, 0.08, 0.92)
		m.add_octa_column(side * 0.98, 1.36, 0.1, 0.07, 0.82)
		m.add_box(side, 0.08, 0.02, 0.28, 0.16, 0.56)
		m.add_box(side, 0.0, 0.06, 0.34, 0.05, 0.64)
		m.add_box(side, 0.34, 0.0, 0.1, 0.22, 0.1)
		m.add_box(side, 0.64, 0.0, 0.09, 0.22, 0.09)
		m.add_box(side, 0.96, 0.02, 0.1, 0.28, 0.12)
		m.add_box(side, 1.22, 0.0, 0.1, 0.24, 0.1)
		m.add_box(side + 0.07, 0.52, 0.07, 0.04, 0.42, 0.04)
		m.add_box(side - 0.07, 0.82, -0.06, 0.04, 0.34, 0.04)
	m.add_box(0.0, 1.45, 0.0, 0.52, 0.24, 0.28)
	m.add_box(0.0, 2.0, 0.0, 1.0, 1.12, 0.58)
	m.add_box(0.0, 2.0, 0.24, 0.42, 0.58, 0.12)
	m.add_box(0.0, 1.82, -0.18, 0.62, 0.44, 0.16)
	m.add_box(-0.54, 2.42, -0.18, 0.16, 0.24, 0.16)
	m.add_box(0.54, 2.42, -0.18, 0.16, 0.24, 0.16)
	for side in (-1, 1):
		sx = 0.62 * side
		m.add_octa_column(sx + 0.24 * side, 1.66, 0.12, 0.06, 1.08)
		m.add_box(sx, 2.38, 0.0, 0.14, 0.2, 0.14)
		m.add_box(sx + 0.24 * side, 2.02, 0.08, 0.1, 0.34, 0.1)
		m.add_box(sx + 0.4 * side, 1.62, 0.14, 0.09, 0.32, 0.09)
		m.add_box(sx + 0.5 * side, 1.25, 0.18, 0.08, 0.28, 0.08)
		m.add_box(sx + 0.58 * side, 0.92, 0.24, 0.08, 0.18, 0.08)
		m.add_box(0.42 * side, 2.66, -0.06, 0.04, 0.44, 0.04)
		m.add_box(0.52 * side, 2.54, -0.12, 0.04, 0.36, 0.04)
	m.add_box(0.0, 3.02, 0.02, 0.44, 0.46, 0.38)
	m.add_box(0.0, 3.22, 0.12, 0.26, 0.12, 0.14)
	m.add_box(-0.1, 3.06, 0.2, 0.06, 0.06, 0.05)
	m.add_box(0.1, 3.06, 0.2, 0.06, 0.06, 0.05)
	m.add_box(-0.08, 3.44, 0.0, 0.03, 0.2, 0.03)
	m.add_box(0.08, 3.48, -0.02, 0.03, 0.24, 0.03)
	return m


def lizard_mesh(seed_shift: float, horn_side: float, pack_offset: float) -> Mesh:
	m = Mesh()
	is_brute = horn_side < 0
	m.add_octa_column(0.0, 1.94, 0.46, 0.12 if is_brute else 0.08, 0.8)
	m.add_octa_column(-0.18 if is_brute else -0.12, 0.78, 0.02, 0.09 if is_brute else 0.06, 0.92)
	m.add_octa_column(0.18 if is_brute else 0.12, 0.78, 0.02, 0.09 if is_brute else 0.06, 0.92)
	if is_brute:
		m.add_box(0.0, 1.22, 0.0, 1.08, 1.28, 0.68)
		m.add_box(0.0, 2.06, 0.34, 0.52, 0.4, 0.66)
		for side in (-0.34, 0.34):
			m.add_box(side, 0.12, 0.06, 0.34, 0.18, 0.62)
			m.add_box(side, 0.44, 0.0, 0.18, 0.28, 0.18)
			m.add_box(side, 0.82, -0.08, 0.18, 0.34, 0.16)
			m.add_box(side + 0.14 * side, 1.14, 0.08, 0.18, 0.28, 0.14)
			m.add_box(side + 0.22 * side, 1.5, 0.0, 0.16, 0.3, 0.14)
			m.add_box(side * 1.05, 1.8, 0.08, 0.18, 0.7, 0.2)
		m.add_box(0.0, 0.94, -0.68 - seed_shift, 0.24, 0.22, 1.18)
		m.add_box(0.0, 1.76, 0.58, 0.28, 0.2, 0.78)
		m.add_box(-0.18, 2.24, 0.44, 0.1, 0.16, 0.34)
		m.add_box(0.18, 2.24, 0.44, 0.1, 0.16, 0.34)
		m.add_box(-0.12, 2.0, 0.64, 0.08, 0.08, 0.18)
		m.add_box(0.12, 2.0, 0.64, 0.08, 0.08, 0.18)
		m.add_box(-0.56, 1.46, 0.2, 0.08, 0.28, 0.08)
		m.add_box(0.56, 1.36, -0.1, 0.08, 0.28, 0.08)
	else:
		m.add_box(0.0, 1.08, 0.0, 0.7, 0.88, 0.4)
		m.add_box(0.0, 1.96, 0.22, 0.34, 0.34, 0.76)
		for side in (-0.24, 0.24):
			m.add_box(side, 0.08, 0.08, 0.22, 0.12, 0.54)
			m.add_box(side, 0.44, -0.08, 0.1, 0.26, 0.1)
			m.add_box(side + 0.12 * side, 0.82, 0.12, 0.1, 0.28, 0.1)
			m.add_box(side + 0.28 * side, 1.12, -0.04, 0.1, 0.24, 0.08)
			m.add_box(side + 0.36 * side, 1.42, 0.1, 0.08, 0.22, 0.08)
			m.add_box(side * 0.95, 1.34, 0.14, 0.12, 0.78, 0.12)
			m.add_box(side * 1.18, 0.94, 0.26, 0.1, 0.3, 0.1)
		m.add_box(0.0, 0.88, -0.92 - seed_shift, 0.14, 0.16, 1.44)
		m.add_box(0.0, 2.18, 0.7, 0.24, 0.18, 0.96)
		m.add_box(horn_side, 2.24, 0.38, 0.08, 0.2, 0.3)
		m.add_box(-horn_side, 2.18, 0.32, 0.08, 0.18, 0.22)
		m.add_box(0.0, 2.04, 0.82, 0.08, 0.08, 0.18)
		m.add_box(pack_offset, 1.46, -0.12, 0.14, 0.36, 0.2)
	return m


def ape_robot_boss_mesh() -> Mesh:
	m = Mesh()
	m.add_octa_column(-1.1, 1.28, 0.06, 0.18, 1.6)
	m.add_octa_column(1.1, 1.18, 0.06, 0.16, 1.45)
	m.add_octa_column(-0.48, 0.56, 0.0, 0.18, 1.0)
	m.add_octa_column(0.48, 0.56, 0.0, 0.18, 1.0)
	m.add_box(0.0, 1.6, 0.0, 1.56, 1.7, 1.04)
	m.add_box(0.0, 2.74, 0.24, 0.96, 0.76, 0.86)
	m.add_box(0.0, 2.0, -0.36, 0.78, 0.82, 0.4)
	for side, arm_scale in ((-1.08, 0.62), (1.08, 0.5)):
		m.add_box(side, 1.9, 0.0, 0.38 if side > 0 else 0.52, 1.18, 0.4)
		m.add_box(side * 1.16, 1.1, 0.1, 0.34 if side > 0 else 0.46, 0.92, 0.36)
		m.add_box(side * 1.22, 0.46, 0.24, 0.28 + arm_scale * 0.1, 0.42, 0.3)
	for side in (-0.48, 0.48):
		m.add_box(side, 0.54, 0.0, 0.4, 0.92, 0.42)
		m.add_box(side, 0.06, 0.14, 0.46, 0.12, 0.72)
	m.add_box(0.0, 1.1, -0.98, 0.36, 0.24, 1.56)
	m.add_box(-0.64, 2.26, -0.2, 0.28, 0.52, 0.28)
	m.add_box(0.62, 2.18, -0.18, 0.24, 0.42, 0.24)
	m.add_box(0.0, 2.28, 0.84, 0.62, 0.26, 0.34)
	m.add_box(-0.2, 2.94, 0.56, 0.22, 0.18, 0.22)
	m.add_box(0.24, 2.9, 0.58, 0.18, 0.16, 0.18)
	return m


def rifle_mesh() -> Mesh:
	m = Mesh()
	m.add_box(0.0, 0.0, 0.0, 0.9, 0.12, 0.12)
	m.add_box(-0.22, -0.18, 0.0, 0.16, 0.3, 0.1)
	m.add_box(0.35, 0.1, 0.0, 0.2, 0.1, 0.1)
	m.add_box(0.52, 0.0, 0.0, 0.24, 0.08, 0.08)
	m.add_box(0.08, -0.04, 0.12, 0.26, 0.08, 0.08)
	return m


def weapon_mesh(style: str) -> Mesh:
	m = Mesh()
	m.add_box(0.0, 0.0, 0.0, 0.85, 0.12, 0.12)
	m.add_box(-0.2, -0.16, 0.0, 0.14, 0.28, 0.1)
	if style == "shock_pike":
		m.add_box(0.48, 0.0, 0.0, 0.34, 0.06, 0.06)
		m.add_box(0.68, 0.06, 0.0, 0.14, 0.14, 0.14)
	elif style == "scrap_shotgun":
		m.add_box(0.34, 0.08, 0.0, 0.28, 0.16, 0.14)
		m.add_box(0.55, 0.0, 0.0, 0.18, 0.1, 0.1)
	elif style == "arc_pistol":
		m.add_box(0.18, 0.08, 0.0, 0.16, 0.12, 0.14)
		m.add_box(0.4, 0.0, 0.0, 0.16, 0.08, 0.08)
	elif style == "raptor_claws":
		m.add_box(0.18, 0.0, 0.1, 0.2, 0.08, 0.06)
		m.add_box(0.18, 0.0, -0.1, 0.2, 0.08, 0.06)
		m.add_box(0.42, 0.04, 0.1, 0.26, 0.03, 0.03)
		m.add_box(0.42, 0.04, 0.0, 0.26, 0.03, 0.03)
		m.add_box(0.42, 0.04, -0.1, 0.26, 0.03, 0.03)
	elif style == "bolas_launcher":
		m.add_box(0.22, 0.1, 0.0, 0.26, 0.1, 0.18)
		m.add_box(0.55, 0.0, 0.12, 0.08, 0.08, 0.08)
		m.add_box(0.55, 0.0, -0.12, 0.08, 0.08, 0.08)
	elif style == "furnace_cannon":
		m.add_box(0.24, 0.12, 0.0, 0.42, 0.22, 0.22)
		m.add_box(0.58, 0.0, 0.0, 0.22, 0.14, 0.14)
	elif style == "arc_maul":
		m.add_box(0.42, 0.18, 0.0, 0.18, 0.36, 0.18)
		m.add_box(0.6, 0.22, 0.0, 0.22, 0.22, 0.22)
	elif style == "missile_fist":
		m.add_box(0.32, 0.08, 0.0, 0.32, 0.22, 0.22)
		m.add_box(0.52, 0.0, 0.0, 0.18, 0.18, 0.18)
	return m


def pickup_mesh(kind: str) -> Mesh:
	m = Mesh()
	m.add_box(0.0, 0.0, 0.0, 0.34, 0.34, 0.34)
	m.add_box(0.0, 0.3, 0.0, 0.18, 0.14, 0.18)
	if kind == "overcharge":
		m.add_box(0.18, 0.0, 0.0, 0.08, 0.26, 0.08)
	elif kind == "spread":
		m.add_box(0.18, 0.0, 0.12, 0.08, 0.18, 0.08)
		m.add_box(0.18, 0.0, -0.12, 0.08, 0.18, 0.08)
	else:
		m.add_box(0.2, 0.0, 0.0, 0.12, 0.12, 0.12)
		m.add_box(-0.2, 0.0, 0.0, 0.12, 0.12, 0.12)
	return m


def room_mesh(variant: int) -> Mesh:
	m = Mesh()
	m.add_box(0.0, -0.25, 0.0, 48.0, 0.5, 48.0)
	m.add_box(0.0, 6.0, -24.0, 48.0, 12.0, 0.5)
	m.add_box(0.0, 6.0, 24.0, 48.0, 12.0, 0.5)
	m.add_box(-24.0, 6.0, 0.0, 0.5, 12.0, 48.0)
	m.add_box(24.0, 6.0, 0.0, 0.5, 12.0, 48.0)
	m.add_box(0.0, 12.25, 0.0, 48.0, 0.5, 48.0)
	if variant == 1:
		m.add_box(-12.0, 1.0, 8.0, 5.0, 2.0, 2.0)
		m.add_box(8.0, 0.75, -10.0, 6.0, 1.5, 3.0)
	elif variant == 2:
		m.add_box(-8.0, 0.9, -6.0, 8.0, 1.8, 2.2)
		m.add_box(10.0, 0.8, 9.0, 4.0, 1.6, 5.0)
	else:
		m.add_box(0.0, 1.2, -6.0, 10.0, 2.4, 3.5)
		m.add_box(-10.0, 0.8, 10.0, 4.0, 1.6, 4.0)
	return m


def write_assets() -> dict:
	texture_patterns()

	mesh_specs = {
		"robot_player": (robot_player_mesh(), "metal_robot_marked.ppm"),
		"lizard_enemy_a": (lizard_mesh(0.0, -0.1, 0.0), "scales_lizard_emerald.ppm"),
		"lizard_enemy_a_raider": (lizard_mesh(0.06, -0.12, 0.08), "scales_lizard_amber.ppm"),
		"lizard_enemy_a_scarred": (lizard_mesh(0.1, -0.14, -0.02), "scales_lizard_emerald.ppm"),
		"lizard_enemy_b": (lizard_mesh(0.12, 0.1, 0.0), "scales_lizard_amber.ppm"),
		"lizard_enemy_b_guard": (lizard_mesh(0.16, 0.12, 0.06), "scales_lizard_amber.ppm"),
		"lizard_enemy_b_marksman": (lizard_mesh(0.08, 0.14, -0.05), "scales_lizard_emerald.ppm"),
		"ape_robot_boss": (ape_robot_boss_mesh(), "fur_ape_boss.ppm"),
		"rifle": (rifle_mesh(), "metal_robot.ppm"),
		"enemy_shock_pike": (weapon_mesh("shock_pike"), "metal_robot.ppm"),
		"enemy_scrap_shotgun": (weapon_mesh("scrap_shotgun"), "metal_robot.ppm"),
		"enemy_arc_pistol": (weapon_mesh("arc_pistol"), "metal_robot.ppm"),
		"enemy_raptor_claws": (weapon_mesh("raptor_claws"), "metal_robot.ppm"),
		"enemy_bolas_launcher": (weapon_mesh("bolas_launcher"), "metal_robot.ppm"),
		"boss_furnace_cannon": (weapon_mesh("furnace_cannon"), "metal_robot_marked.ppm"),
		"boss_arc_maul": (weapon_mesh("arc_maul"), "metal_robot_marked.ppm"),
		"boss_missile_fist": (weapon_mesh("missile_fist"), "metal_robot_marked.ppm"),
		"pickup_overcharge": (pickup_mesh("overcharge"), "ammo_pickup_glow.ppm"),
		"pickup_spread": (pickup_mesh("spread"), "ammo_pickup_glow.ppm"),
		"pickup_piercing": (pickup_mesh("piercing"), "ammo_pickup_glow.ppm"),
		"room_hangar": (room_mesh(1), "office_wallpaper.ppm"),
		"room_office_wing": (room_mesh(2), "office_wallpaper.ppm"),
		"room_boss_atrium": (room_mesh(3), "office_wallpaper.ppm"),
		"furniture_set": (room_mesh(1), "office_furniture.ppm"),
	}

	models_manifest = []
	for name, (mesh, texture) in mesh_specs.items():
		mtl_name = f"{name}.mtl"
		obj_name = f"{name}.obj"
		write_mtl(MATERIALS / mtl_name, texture)
		mesh.write_obj(MODELS / obj_name, name, mtl_name)
		models_manifest.append(
			{
				"id": name,
				"obj": f"assets/models/{obj_name}",
				"mtl": f"assets/materials/{mtl_name}",
				"texture": f"assets/textures/{texture}",
				"polygons": mesh.poly_count,
				"polygon_budget": 1000,
			}
		)

	return {"models": models_manifest}


def build_spawn_set() -> list[dict]:
	spawns: list[dict] = []
	brute_weapons = ["shock_pike", "scrap_shotgun", "arc_pistol", "bolas_launcher"]
	variant_cycle = [
		"lizard_enemy_a",
		"lizard_enemy_a_raider",
		"lizard_enemy_a_scarred",
		"lizard_enemy_b",
		"lizard_enemy_b_guard",
		"lizard_enemy_b_marksman",
	]
	markings = ["jaw_scar", "shoulder_stripe", "neck_brand", "tail_wrap", "split_fin"]
	room_layout = {
		"room_01": [(-16.0, -8.0), (-8.0, -10.0), (0.0, -4.0), (10.0, -2.0), (16.0, 6.0), (-10.0, 10.0), (8.0, 14.0)],
		"room_02": [(-18.0, -10.0), (-6.0, -8.0), (6.0, -4.0), (16.0, 0.0), (-12.0, 6.0), (-2.0, 10.0), (10.0, 14.0), (18.0, 18.0)],
	}
	idx = 0
	for room_id, positions in room_layout.items():
		for x, z in positions:
			variant_model = variant_cycle[idx % len(variant_cycle)]
			base_type = "lizard_enemy_a" if "enemy_a" in variant_model else "lizard_enemy_b"
			weapon_type = brute_weapons[idx % len(brute_weapons)] if base_type == "lizard_enemy_a" else "raptor_claws"
			spawns.append(
				{
					"spawn_id": f"e_{idx:02d}",
					"room": room_id,
					"enemy_type": base_type,
					"variant_model": variant_model,
					"weapon_type": weapon_type,
					"ai_profile": "brute_bait_flank" if base_type == "lizard_enemy_a" else "raptor_skirt_deek",
					"taunt_style": "predatory_dance",
					"outfit_variant": f"loadout_{(idx % 5) + 1}",
					"marking": markings[idx % len(markings)],
					"position": {"x": x, "y": 0.0, "z": z},
					"hitpoints": 8,
				}
			)
			idx += 1
	return spawns


def write_configs(models_manifest: dict) -> None:
	CONFIG.mkdir(parents=True, exist_ok=True)
	controller_profile = {
		"enabled": True,
		"device": "Xbox Series Controller",
		"api": "xinput",
		"move": "left_stick",
		"aim": "right_stick",
		"shoot": "right_trigger",
		"parry": "left_shoulder",
		"melee": "right_shoulder",
		"dodge": "b",
		"jump": "a",
		"reload": "x",
		"swap_mode": "y",
		"sprint": "left_trigger",
		"pause": "menu",
		"deadzone": {"left_stick": 0.18, "right_stick": 0.16},
	}
	enemy_weapons = [
		{"id": "shock_pike", "model": "enemy_shock_pike", "class": "melee_lunge", "boss_exclusive": False},
		{"id": "scrap_shotgun", "model": "enemy_scrap_shotgun", "class": "close_burst", "boss_exclusive": False},
		{"id": "arc_pistol", "model": "enemy_arc_pistol", "class": "midrange_sidearm", "boss_exclusive": False},
		{"id": "bolas_launcher", "model": "enemy_bolas_launcher", "class": "snare_ranged", "boss_exclusive": False},
		{"id": "raptor_claws", "model": "enemy_raptor_claws", "class": "close_rake", "boss_exclusive": False},
	]
	boss_weapons = [
		{"id": "furnace_cannon", "model": "boss_furnace_cannon", "class": "area_blast", "boss_exclusive": True},
		{"id": "arc_maul", "model": "boss_arc_maul", "class": "shock_slam", "boss_exclusive": True},
		{"id": "missile_fist", "model": "boss_missile_fist", "class": "tracking_strike", "boss_exclusive": True},
	]
	ammo_upgrades = [
		{"id": "overcharge_rounds", "model": "pickup_overcharge", "collectible": True, "temporary_seconds": 18, "effect": "+2 damage per shot"},
		{"id": "spread_burst", "model": "pickup_spread", "collectible": True, "temporary_seconds": 14, "effect": "triple spread volley"},
		{"id": "piercing_slugs", "model": "pickup_piercing", "collectible": True, "temporary_seconds": 20, "effect": "pierces multiple enemies"},
	]
	temporary_ammo_upgrades = [
		{
			"id": item["id"],
			"model": item["model"],
			"collectible": item["collectible"],
			"duration_seconds": item["temporary_seconds"],
			"effect": item["effect"],
		}
		for item in ammo_upgrades
	]
	game = {
		"project": "SHOOT",
		"render_style": {
			"presentation": "enhanced_photoreal_anthropomorphic_3d",
			"projectile_trails": True,
			"camera": "over_the_shoulder",
			"movement": "omnidirectional",
			"material_response": "chrome_specular_scaled_skin_and_fur_microdetail",
			"texture_resolution": 320,
		},
		"audio": {
			"music_enabled": True,
			"sfx_enabled": True,
			"music_profile": "industrial_predator_pulse",
			"sfx_profile": "metal_clang_hiss_dash_shot",
		},
		"character_design": {
			"player_robot": {
				"silhouette": "slender_android",
				"features": [
					"chrome plating",
					"wire bundles from shoulders",
					"skeletal limb tubing",
					"defined abdomen and chest armor",
					"articulated neck and faceplate",
					"electro-fluid chest core",
					"hovering keen-eyed head",
				],
			},
			"boss": {
				"silhouette": "gorilla_steampunk_cyborg",
				"behavior": ["arena_leaps", "furniture_throws", "weapon_cycle"],
			},
		},
		"enemy_archetypes": [
			{"id": "lizard_brute", "traits": ["bulky", "armored", "slow", "weapon_user", "bait", "flank", "taunt_dance"]},
			{"id": "lizard_raptor", "traits": ["swift", "reverse_jointed", "claw_attacker", "snouted", "skirt_feint", "deek", "taunt_dance"]},
		],
		"source_reference": {
			"xenobloods_manifest": "xenobloods/docs/XENOBLOODS_GRAPHICS_MANIFEST.md",
			"xenobloods_templates": "xenobloods/examples/xenobloods_preview_roster.json",
			"style_transfer": [
				"silhouette_emphasis",
				"texture_detail",
				"enemy_family_boss_weighting",
				"asymmetrical_character_detail",
			],
		},
		"mode": "third_person_over_the_shoulder",
		"dialogue": False,
		"onscreen_text": False,
		"controller_support": {
			"enabled": True,
			"preferred_device": "xbox_series",
			"xbox_series": controller_profile,
		},
		"weapon": {
			"id": "rifle",
			"ammo": "infinite",
			"damage_per_shot": 1,
		},
		"ammo_upgrades": ammo_upgrades,
		"temporary_ammo_upgrades": temporary_ammo_upgrades,
		"enemy_weapon_types": enemy_weapons,
		"boss_weapon_types": boss_weapons,
		"player": {
			"model": "robot_player",
			"hitpoints": 3,
		},
		"enemy_defaults": {
			"lizard_enemy_a": {"hitpoints": 8},
			"lizard_enemy_b": {"hitpoints": 8},
			"ape_robot_boss": {"hitpoints": 32},
		},
		"enemy_variants": [
			{"id": "lizard_enemy_a_raider", "base": "lizard_enemy_a", "details": ["jaw_scar", "single_spike_pauldron", "amber_wraps"]},
			{"id": "lizard_enemy_a_scarred", "base": "lizard_enemy_a", "details": ["rib_plate", "tail_ring", "crest_notch"]},
			{"id": "lizard_enemy_b_guard", "base": "lizard_enemy_b", "details": ["visor_mark", "left_knee_pad", "bandolier"]},
			{"id": "lizard_enemy_b_marksman", "base": "lizard_enemy_b", "details": ["eye_stripe", "backpack_cell", "split_fin"]},
		],
		"models": models_manifest["models"],
	}

	regular_spawns = build_spawn_set()
	level = {
		"level_id": "level_01",
		"gating": [
			{"from": "room_01", "to": "room_02", "requirement": {"type": "enemy_clear_threshold", "count": 7, "gate": "security_shutter"}},
			{"from": "room_02", "to": "room_03", "requirement": {"type": "pickup_and_enemy_clear", "count": 8, "required_pickup": "piercing_slugs", "gate": "atrium_bulkhead"}},
		],
		"rooms": [
			{
				"id": "room_01",
				"model": "room_hangar",
				"size": {"width": 64, "length": 64, "height": 14},
				"role": "combat",
				"flow_note": "security hangar with staggered cover and first gate shutter",
				"pickups": [
					{"pickup_id": "pickup_01", "type": "overcharge_rounds", "position": {"x": -10.0, "y": 0.0, "z": 12.0}},
				],
				"enemies": [s for s in regular_spawns if s["room"] == "room_01"],
			},
			{
				"id": "room_02",
				"model": "room_office_wing",
				"size": {"width": 68, "length": 60, "height": 14},
				"role": "combat",
				"flow_note": "wide office wing with flanking lanes and boss access bulkhead",
				"pickups": [
					{"pickup_id": "pickup_02", "type": "spread_burst", "position": {"x": 8.0, "y": 0.0, "z": -6.0}},
					{"pickup_id": "pickup_03", "type": "piercing_slugs", "position": {"x": -4.0, "y": 0.0, "z": 16.0}},
				],
				"enemies": [s for s in regular_spawns if s["room"] == "room_02"],
			},
			{
				"id": "room_03",
				"model": "room_boss_atrium",
				"size": {"width": 72, "length": 72, "height": 16},
				"role": "boss",
				"flow_note": "large atrium for furniture throws, leaps, and weapon cycling",
				"pickups": [],
				"enemies": [
					{
						"spawn_id": "boss_00",
						"room": "room_03",
						"enemy_type": "ape_robot_boss",
						"variant_model": "ape_robot_boss",
						"weapon_cycle": ["furnace_cannon", "arc_maul", "missile_fist"],
						"movement_profile": "arena_leap_furniture_throw",
						"position": {"x": 0.0, "y": 0.0, "z": 0.0},
						"hitpoints": 32,
					}
				],
			},
		],
		"transitions": [
			{"from": "room_01", "to": "room_02"},
			{"from": "room_02", "to": "room_03"},
		],
	}

	with (CONFIG / "project.json").open("w", encoding="utf-8") as f:
		json.dump(game, f, indent=2)
	with (CONFIG / "level_01.json").open("w", encoding="utf-8") as f:
		json.dump(level, f, indent=2)
	with (CONFIG / "xbox_series_input.json").open("w", encoding="utf-8") as f:
		json.dump(controller_profile, f, indent=2)


def main() -> None:
	for p in (MODELS, MATERIALS, TEXTURES, CONFIG):
		p.mkdir(parents=True, exist_ok=True)

	models_manifest = write_assets()
	write_configs(models_manifest)
	print("SHOOT assets generated.")


if __name__ == "__main__":
	main()
