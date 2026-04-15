from __future__ import annotations

import json
import math
import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config"
PROJECT = json.loads((CONFIG / "project.json").read_text(encoding="utf-8"))
LEVEL = json.loads((CONFIG / "level_01.json").read_text(encoding="utf-8"))
MODEL_INFO = {model["id"]: model for model in PROJECT["models"]}
MESH_CACHE: dict[str, "MeshAsset"] = {}

sys.path.insert(0, str(ROOT / "tools"))
try:
    from xbox_series_input import XboxSeriesController
except Exception:
    XboxSeriesController = None

try:
    import winsound
except Exception:
    winsound = None

WIDTH = 1280
HEIGHT = 720
ROOM_HALF_W = 32.0
ROOM_DEPTH = 36.0
PLAYER_RADIUS = 1.35
FOCAL_LENGTH = 760.0
HORIZON_Y = HEIGHT * 0.3


@dataclass
class Bullet:
    x: float
    z: float
    vx: float
    vz: float
    damage: int
    radius: float = 0.35
    pierce: int = 1
    prev_x: float = 0.0
    prev_z: float = 0.0
    visual: str = "player_round"


@dataclass
class Enemy:
    kind: str
    x: float
    z: float
    hp: int
    max_hp: int
    weapon: str
    variant: str
    marking: str
    speed: float
    boss: bool = False
    cooldown: float = 0.0
    attack_phase: int = 0
    jump_offset: float = 0.0
    ai_style: str = "hunter"
    taunt_timer: float = 0.0
    weave_phase: float = 0.0


@dataclass
class Pickup:
    kind: str
    x: float
    z: float
    taken: bool = False


@dataclass
class MeshAsset:
    vertices: list[tuple[float, float, float]]
    faces: list[tuple[int, ...]]


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _shade(color: str, factor: float) -> str:
    r, g, b = _hex_to_rgb(color)
    factor = max(0.2, min(1.25, factor))
    rr = max(0, min(255, int(r * factor)))
    gg = max(0, min(255, int(g * factor)))
    bb = max(0, min(255, int(b * factor)))
    return f"#{rr:02x}{gg:02x}{bb:02x}"


def _rotate_y(x: float, z: float, yaw: float) -> tuple[float, float]:
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    return x * cy - z * sy, x * sy + z * cy


def _load_mesh(model_id: str) -> MeshAsset:
    cached = MESH_CACHE.get(model_id)
    if cached is not None:
        return cached

    info = MODEL_INFO.get(model_id)
    if not info:
        mesh = MeshAsset([], [])
        MESH_CACHE[model_id] = mesh
        return mesh

    obj_path = ROOT / info["obj"]
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for line in obj_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("v "):
            _, x, y, z = line.split()
            vertices.append((float(x), float(y), float(z)))
        elif line.startswith("f "):
            indices = []
            for token in line.split()[1:]:
                indices.append(int(token.split("/")[0]) - 1)
            if len(indices) >= 3:
                faces.append(tuple(indices))

    mesh = MeshAsset(vertices, faces)
    MESH_CACHE[model_id] = mesh
    return mesh


class SoundSystem:
    def __init__(self) -> None:
        self.enabled = winsound is not None
        self.last_music = 0.0
        self.step = 0

    def _ping(self, freq: int, duration: int) -> None:
        if not self.enabled:
            return

        def _worker() -> None:
            try:
                winsound.Beep(max(80, min(1800, int(freq))), int(duration))
            except RuntimeError:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def sfx(self, name: str) -> None:
        tones = {
            "fire": (980, 28),
            "jump": (620, 45),
            "dodge": (420, 55),
            "pickup": (1180, 70),
            "melee": (760, 45),
            "parry": (900, 40),
            "hit": (210, 65),
            "taunt": (320, 55),
            "reload": (540, 35),
            "boss": (180, 90),
        }
        if name in tones:
            self._ping(*tones[name])

    def update_music(self, room_index: int, boss_room: bool) -> None:
        if not self.enabled:
            return
        interval = 0.42 if boss_room else 0.72
        now = time.time()
        if now - self.last_music < interval:
            return
        self.last_music = now
        motifs = ([220, 330, 262, 392], [196, 294, 247, 330], [147, 220, 196, 294])
        motif = motifs[min(room_index, len(motifs) - 1)]
        self._ping(motif[self.step % len(motif)], 80 if boss_room else 60)
        self.step += 1


class ShootGame:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SHOOT - low poly 3D prototype")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.configure(bg="#05070d")
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#05070d", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.player_hp = int(PROJECT["player"]["hitpoints"])
        self.player_x = 0.0
        self.player_z = -18.0
        self.aim_x = 0.0
        self.aim_z = 1.0
        self.last_fire = 0.0
        self.fire_delay = 0.16
        self.room_index = 0
        self.room_clear = False
        self.victory = False
        self.game_over = False
        self.status_text = ""
        self.status_until = 0.0
        self.active_upgrade: str | None = None
        self.upgrade_until = 0.0
        self.unlocked_upgrades: list[str] = []
        self.camera_yaw = 0.0
        self.camera_pitch = 0.08
        self.player_y = 0.0
        self.jump_velocity = 0.0
        self.dodge_timer = 0.0
        self.parry_timer = 0.0
        self.dodge_vector = (0.0, 0.0)
        self.prev_cycle_pressed = False
        self.prev_reload_pressed = False
        self.prev_jump_pressed = False
        self.prev_dodge_pressed = False
        self.prev_melee_pressed = False
        self.prev_parry_pressed = False
        self.audio = SoundSystem()
        self.current_flow_note = ""
        self.current_gate = None
        self.room_kills = 0

        self.bullets: list[Bullet] = []
        self.enemy_projectiles: list[Bullet] = []
        self.enemies: list[Enemy] = []
        self.pickups: list[Pickup] = []
        self.keys: set[str] = set()
        self.mouse_x = WIDTH / 2
        self.mouse_y = HEIGHT / 2

        self.controller = XboxSeriesController() if XboxSeriesController else None
        self._bind_inputs()
        self._load_room(0)

    def _bind_inputs(self) -> None:
        self.root.bind("<KeyPress>", lambda e: self.keys.add(e.keysym.lower()))
        self.root.bind("<KeyRelease>", lambda e: self.keys.discard(e.keysym.lower()))
        self.root.bind("<Motion>", self._on_mouse_move)
        self.root.bind("<Button-1>", lambda e: self.fire())

    def _on_mouse_move(self, event) -> None:
        self.mouse_x = event.x
        self.mouse_y = event.y
        self.aim_x = (event.x - WIDTH / 2) / max(1.0, WIDTH / 2)
        self.aim_z = 1.0

    def _load_room(self, index: int) -> None:
        self.room_index = index
        room = LEVEL["rooms"][index]
        self.enemies.clear()
        self.bullets.clear()
        self.enemy_projectiles.clear()
        self.pickups.clear()
        self.room_clear = False
        self.player_x = 0.0
        self.player_z = -18.0
        self.status_text = f"ROOM {index + 1}"
        self.status_until = time.time() + 1.8

        self.current_flow_note = room.get("flow_note", "")
        self.current_gate = next((gate for gate in LEVEL.get("gating", []) if gate["from"] == room["id"]), None)
        self.room_kills = 0
        for idx, entry in enumerate(room.get("enemies", [])):
            boss = entry["enemy_type"] == "ape_robot_boss"
            hp = int(entry["hitpoints"])
            self.enemies.append(
                Enemy(
                    kind=entry["enemy_type"],
                    x=float(entry["position"]["x"]),
                    z=float(entry["position"]["z"]),
                    hp=hp,
                    max_hp=hp,
                    weapon=entry.get("weapon_type", entry.get("weapon_cycle", ["furnace_cannon" if boss else "shock_pike"])[0]),
                    variant=entry.get("variant_model", entry["enemy_type"]),
                    marking=entry.get("marking", "scar" if not boss else "boss"),
                    speed=(0.042 if entry["enemy_type"] == "lizard_enemy_a" else 0.082) if not boss else 0.03,
                    boss=boss,
                    ai_style=entry.get("ai_profile", "boss_leaper" if boss else ("brute_bait_flank" if entry["enemy_type"] == "lizard_enemy_a" else "raptor_skirt_deek")),
                    weave_phase=idx * 0.8,
                )
            )
        for entry in room.get("pickups", []):
            p = entry["position"]
            self.pickups.append(Pickup(entry["type"], float(p["x"]), float(p["z"])))

    def fire(self) -> None:
        now = time.time()
        if self.game_over or self.victory or now - self.last_fire < self.fire_delay:
            return
        self.last_fire = now

        if self.controller:
            snap = self.controller.poll()
            if snap.connected and (abs(snap.right_x) > 0.05 or abs(snap.right_y) > 0.05):
                ax = -snap.right_x
                az = max(0.2, -snap.right_y)
            else:
                ax = (self.mouse_x - WIDTH / 2) / max(1.0, WIDTH / 2)
                az = 1.0
        else:
            ax = (self.mouse_x - WIDTH / 2) / max(1.0, WIDTH / 2)
            az = 1.0

        length = math.hypot(ax, az) or 1.0
        ax /= length
        az /= length
        self.aim_x = ax
        self.aim_z = az
        damage = 1
        pierce = 1
        spreads = [0.0]
        if self.active_upgrade == "overcharge_rounds":
            damage = 3
        elif self.active_upgrade == "spread_burst":
            spreads = [-0.18, 0.0, 0.18]
        elif self.active_upgrade == "piercing_slugs":
            pierce = 99
        self.audio.sfx("fire")
        for offset in spreads:
            dx = ax + offset
            dz = az
            dlen = math.hypot(dx, dz) or 1.0
            self.bullets.append(Bullet(self.player_x, self.player_z + 1.8 + self.player_y, dx / dlen * 0.8, dz / dlen * 0.8, damage, pierce=pierce, prev_x=self.player_x, prev_z=self.player_z + 1.8 + self.player_y, visual="player_round"))

    def _move_player(self, local_x: float, local_z: float, sprinting: bool = False) -> None:
        magnitude = math.hypot(local_x, local_z)
        if magnitude < 0.01:
            return
        local_x /= magnitude
        local_z /= magnitude
        world_x, world_z = _rotate_y(local_x, local_z, self.camera_yaw)
        speed = 0.34 + (0.24 if sprinting else 0.0)
        if self.dodge_timer > 0.0:
            speed += 0.42
        next_x = self.player_x + world_x * speed
        next_z = self.player_z + world_z * speed
        self.player_x = max(-ROOM_HALF_W + PLAYER_RADIUS, min(ROOM_HALF_W - PLAYER_RADIUS, next_x))
        self.player_z = max(-ROOM_DEPTH + PLAYER_RADIUS, min(ROOM_DEPTH - PLAYER_RADIUS, next_z))

    def _jump(self) -> None:
        if self.player_y <= 0.001:
            self.jump_velocity = 0.52
            self.status_text = "JUMP"
            self.status_until = time.time() + 0.35
            self.audio.sfx("jump")

    def _dodge(self, local_x: float, local_z: float) -> None:
        if self.dodge_timer > 0.0:
            return
        magnitude = math.hypot(local_x, local_z)
        if magnitude < 0.1:
            local_z = 1.0
            magnitude = 1.0
        self.dodge_vector = (local_x / magnitude, local_z / magnitude)
        self.dodge_timer = 0.18
        self.status_text = "DODGE"
        self.status_until = time.time() + 0.4
        self.audio.sfx("dodge")

    def _cycle_special_ammo(self) -> None:
        if not self.unlocked_upgrades:
            self.status_text = "NO SPECIAL AMMO"
            self.status_until = time.time() + 0.6
            return
        if self.active_upgrade not in self.unlocked_upgrades:
            self.active_upgrade = self.unlocked_upgrades[0]
        else:
            idx = self.unlocked_upgrades.index(self.active_upgrade)
            self.active_upgrade = self.unlocked_upgrades[(idx + 1) % len(self.unlocked_upgrades)]
        self.upgrade_until = max(self.upgrade_until, time.time() + 12.0)
        self.status_text = f"SPECIAL {self.active_upgrade.replace('_', ' ').upper()}"
        self.status_until = time.time() + 0.9

    def _reload_weapon(self) -> None:
        self.status_text = "RELOAD CHECK"
        self.status_until = time.time() + 0.5
        self.audio.sfx("reload")

    def _melee_attack(self) -> None:
        self.status_text = "MELEE"
        self.status_until = time.time() + 0.35
        self.audio.sfx("melee")
        facing_x, facing_z = _rotate_y(0.0, 1.0, self.camera_yaw)
        for enemy in list(self.enemies):
            dx = enemy.x - self.player_x
            dz = enemy.z - self.player_z
            distance = math.hypot(dx, dz)
            if distance > 2.6:
                continue
            if dx * facing_x + dz * facing_z < -0.2:
                continue
            enemy.hp -= 4
            enemy.x += facing_x * 0.9
            enemy.z += facing_z * 0.9
            if enemy.hp <= 0:
                self.enemies.remove(enemy)
            break

    def _start_parry(self) -> None:
        self.parry_timer = 0.28
        self.status_text = "PARRY"
        self.status_until = time.time() + 0.35
        self.audio.sfx("parry")

    def _controller_input(self) -> None:
        if not self.controller:
            return
        snap = self.controller.poll()
        if not snap.connected:
            return

        local_x = snap.left_x
        local_z = -snap.left_y
        sprinting = snap.left_trigger > 0.2
        self._move_player(local_x, local_z, sprinting=sprinting)

        if snap.right_trigger > 0.2:
            self.fire()
        if snap.a and not self.prev_jump_pressed:
            self._jump()
        if snap.b and not self.prev_dodge_pressed:
            self._dodge(local_x, local_z)
        if snap.x and not self.prev_reload_pressed:
            self._reload_weapon()
        if snap.y and not self.prev_cycle_pressed:
            self._cycle_special_ammo()
        if snap.right_shoulder and not self.prev_melee_pressed:
            self._melee_attack()
        if snap.left_shoulder and not self.prev_parry_pressed:
            self._start_parry()
        if abs(snap.right_x) > 0.05 or abs(snap.right_y) > 0.05:
            self.aim_x = -snap.right_x
            self.aim_z = max(0.2, -snap.right_y)

        self.prev_jump_pressed = snap.a
        self.prev_dodge_pressed = snap.b
        self.prev_reload_pressed = snap.x
        self.prev_cycle_pressed = snap.y
        self.prev_melee_pressed = snap.right_shoulder
        self.prev_parry_pressed = snap.left_shoulder

    def _keyboard_input(self) -> None:
        local_x = 0.0
        local_z = 0.0
        if "a" in self.keys or "left" in self.keys:
            local_x -= 1.0
        if "d" in self.keys or "right" in self.keys:
            local_x += 1.0
        if "w" in self.keys or "up" in self.keys:
            local_z += 1.0
        if "s" in self.keys or "down" in self.keys:
            local_z -= 1.0
        sprinting = "shift_l" in self.keys or "shift_r" in self.keys
        self._move_player(local_x, local_z, sprinting=sprinting)
        if "space" in self.keys:
            self.fire()
        if "e" in self.keys:
            self._melee_attack()
        if "q" in self.keys and self.parry_timer <= 0.0:
            self._start_parry()

    def _clamp_player(self) -> None:
        self.player_x = max(-ROOM_HALF_W + PLAYER_RADIUS, min(ROOM_HALF_W - PLAYER_RADIUS, self.player_x))
        self.player_z = max(-ROOM_DEPTH + PLAYER_RADIUS, min(ROOM_DEPTH - PLAYER_RADIUS, self.player_z))
        self.player_y = max(0.0, self.player_y)

    def _update_vertical_motion(self) -> None:
        if self.dodge_timer > 0.0:
            self.dodge_timer = max(0.0, self.dodge_timer - 1 / 60)
            dx, dz = self.dodge_vector
            self._move_player(dx, dz, sprinting=True)
        if self.parry_timer > 0.0:
            self.parry_timer = max(0.0, self.parry_timer - 1 / 60)
        if self.player_y > 0.0 or self.jump_velocity > 0.0:
            self.player_y += self.jump_velocity
            self.jump_velocity -= 0.045
            if self.player_y <= 0.0:
                self.player_y = 0.0
                self.jump_velocity = 0.0

    def _update_pickups(self) -> None:
        for pickup in self.pickups:
            if pickup.taken:
                continue
            if math.hypot(self.player_x - pickup.x, self.player_z - pickup.z) < 2.0:
                pickup.taken = True
                if pickup.kind not in self.unlocked_upgrades:
                    self.unlocked_upgrades.append(pickup.kind)
                self.active_upgrade = pickup.kind
                self.upgrade_until = time.time() + 18.0
                self.status_text = pickup.kind.replace("_", " ").upper()
                self.status_until = time.time() + 1.6
                self.audio.sfx("pickup")

    def _update_bullets(self) -> None:
        alive: list[Bullet] = []
        for bullet in self.bullets:
            bullet.prev_x = bullet.x
            bullet.prev_z = bullet.z
            bullet.x += bullet.vx
            bullet.z += bullet.vz
            if bullet.z > ROOM_DEPTH + 3 or abs(bullet.x) > ROOM_HALF_W + 4:
                continue
            hit = False
            for enemy in list(self.enemies):
                if not enemy.boss and math.hypot(bullet.x - enemy.x, bullet.z - enemy.z) < 2.6 and enemy.taunt_timer <= 0.0:
                    side_x, side_z = -bullet.vz, bullet.vx
                    enemy.x += side_x * 0.8
                    enemy.z += side_z * 0.8
                    enemy.taunt_timer = 0.35
                if math.hypot(bullet.x - enemy.x, bullet.z - enemy.z) < (1.9 if enemy.boss else 1.2):
                    enemy.hp -= bullet.damage
                    hit = True
                    bullet.pierce -= 1
                    if enemy.hp <= 0:
                        if not enemy.boss:
                            self.room_kills += 1
                        self.enemies.remove(enemy)
                    if bullet.pierce <= 0:
                        break
            if not hit or bullet.pierce > 0:
                alive.append(bullet)
        self.bullets = alive

    def _enemy_attack(self, enemy: Enemy) -> None:
        dx = self.player_x - enemy.x
        dz = self.player_z - enemy.z
        distance = math.hypot(dx, dz) or 1.0
        if self.parry_timer > 0.0 and distance < 2.4:
            self.status_text = "BLOCK"
            self.status_until = time.time() + 0.35
            return
        if enemy.weapon in {"shock_pike", "raptor_claws", "arc_maul"}:
            if distance < (2.3 if enemy.boss else 1.8):
                self.player_hp -= 1
                self.status_text = "HIT"
                self.status_until = time.time() + 0.7
                self.audio.sfx("hit")
        elif enemy.weapon == "missile_fist":
            vx = dx / distance * 0.38
            vz = dz / distance * 0.38
            self.enemy_projectiles.append(Bullet(enemy.x, enemy.z, vx, vz, 1, radius=0.75, prev_x=enemy.x, prev_z=enemy.z, visual="boss_missile"))
        elif enemy.weapon == "furnace_cannon":
            vx = dx / distance * 0.3
            vz = dz / distance * 0.3
            self.enemy_projectiles.append(Bullet(enemy.x, enemy.z, vx, vz, 1, radius=0.62, prev_x=enemy.x, prev_z=enemy.z, visual="boss_shot"))
        else:
            vx = dx / distance * 0.26
            vz = dz / distance * 0.26
            self.enemy_projectiles.append(Bullet(enemy.x, enemy.z, vx, vz, 1, radius=0.5, prev_x=enemy.x, prev_z=enemy.z, visual="enemy_round"))

    def _boss_behavior(self, enemy: Enemy) -> None:
        anchors = [(-14.0, -8.0), (14.0, -6.0), (-12.0, 14.0), (13.0, 16.0), (0.0, 8.0)]
        dx = self.player_x - enemy.x
        dz = self.player_z - enemy.z
        distance = math.hypot(dx, dz) or 1.0
        enemy.jump_offset = max(0.0, enemy.jump_offset - 0.08)
        enemy.cooldown -= 1 / 60
        if enemy.cooldown <= 0:
            weapon_cycle = ["furnace_cannon", "arc_maul", "missile_fist"]
            enemy.weapon = weapon_cycle[enemy.attack_phase % len(weapon_cycle)]
            if enemy.attack_phase % 3 == 0:
                enemy.x, enemy.z = anchors[enemy.attack_phase % len(anchors)]
                enemy.jump_offset = 1.8
                self.status_text = "BOSS LEAP"
                self.status_until = time.time() + 0.45
                self.audio.sfx("boss")
            elif enemy.attack_phase % 3 == 1:
                vx = dx / distance * 0.24
                vz = dz / distance * 0.24
                self.enemy_projectiles.append(Bullet(enemy.x, enemy.z, vx, vz, 2, radius=0.95, prev_x=enemy.x, prev_z=enemy.z, visual="furniture_throw"))
                self.status_text = "FURNITURE THROW"
                self.status_until = time.time() + 0.5
                self.audio.sfx("boss")
            else:
                self._enemy_attack(enemy)
            enemy.attack_phase += 1
            enemy.cooldown = 0.72
        else:
            enemy.x += dx / distance * enemy.speed * 0.45
            enemy.z += dz / distance * enemy.speed * 0.45

    def _update_enemies(self) -> None:
        now = time.time()
        for idx, enemy in enumerate(self.enemies):
            if enemy.boss:
                self._boss_behavior(enemy)
                continue
            dx = self.player_x - enemy.x
            dz = self.player_z - enemy.z
            distance = math.hypot(dx, dz) or 1.0
            side_x, side_z = -dz / distance, dx / distance
            enemy.taunt_timer = max(0.0, enemy.taunt_timer - 1 / 60)
            dance = math.sin(now * (4.4 if enemy.kind == "lizard_enemy_b" else 3.0) + enemy.weave_phase)
            approach = 0.0
            lateral = dance * (0.78 if enemy.kind == "lizard_enemy_b" else 0.42)
            if enemy.kind == "lizard_enemy_a":
                if distance > 9.0:
                    approach = 0.55
                elif distance > 4.0:
                    approach = 0.18
                else:
                    approach = -0.24
            else:
                approach = 0.7 if distance > 3.2 else -0.08
                lateral *= 1.4
            enemy.x += (dx / distance * approach + side_x * lateral) * enemy.speed
            enemy.z += (dz / distance * approach + side_z * lateral) * enemy.speed
            enemy.jump_offset = 0.08 + abs(dance) * (0.12 if enemy.kind == "lizard_enemy_b" else 0.06)
            if distance < 10.0 and enemy.taunt_timer <= 0.0 and ((idx + int(now * 2)) % 11 == 0):
                enemy.taunt_timer = 1.0
                self.status_text = "TAUNT"
                self.status_until = time.time() + 0.35
                self.audio.sfx("taunt")
            enemy.cooldown -= 1 / 60
            if enemy.cooldown <= 0:
                self._enemy_attack(enemy)
                enemy.cooldown = 0.9 if enemy.weapon == "raptor_claws" else 1.3

    def _update_enemy_projectiles(self) -> None:
        alive: list[Bullet] = []
        for bullet in self.enemy_projectiles:
            bullet.prev_x = bullet.x
            bullet.prev_z = bullet.z
            bullet.x += bullet.vx
            bullet.z += bullet.vz
            if math.hypot(bullet.x - self.player_x, bullet.z - self.player_z) < 1.2:
                if self.parry_timer <= 0.0:
                    self.player_hp -= bullet.damage
                    self.status_text = "HIT"
                    self.audio.sfx("hit")
                else:
                    self.status_text = "PARRY"
                    self.audio.sfx("parry")
                self.status_until = time.time() + 0.7
                continue
            if -24 <= bullet.z <= ROOM_DEPTH + 2 and abs(bullet.x) <= ROOM_HALF_W + 2:
                alive.append(bullet)
        self.enemy_projectiles = alive

    def _camera(self) -> tuple[float, float, float, float]:
        target_yaw = math.atan2(self.aim_x, max(0.15, self.aim_z))
        yaw_delta = (target_yaw - self.camera_yaw + math.pi) % (2 * math.pi) - math.pi
        self.camera_yaw += yaw_delta * 0.14
        shoulder_x, shoulder_z = _rotate_y(2.2, 0.0, self.camera_yaw)
        back_x, back_z = _rotate_y(0.0, -7.5, self.camera_yaw)
        cam_x = self.player_x + shoulder_x + back_x
        cam_y = 4.7 + self.player_y * 0.35
        cam_z = self.player_z + shoulder_z + back_z
        return cam_x, cam_y, cam_z, self.camera_yaw

    def _project_point(self, x: float, y: float, z: float, cam: tuple[float, float, float, float]) -> tuple[float, float, float] | None:
        cam_x, cam_y, cam_z, yaw = cam
        px = x - cam_x
        py = y - cam_y
        pz = z - cam_z
        rx, rz = _rotate_y(px, pz, -yaw)
        if rz <= 0.25:
            return None
        sx = WIDTH / 2 + (rx / rz) * FOCAL_LENGTH
        sy = HORIZON_Y + HEIGHT * 0.3 - (py / rz) * FOCAL_LENGTH
        return sx, sy, rz

    def _draw_mesh(self, model_id: str, pos: tuple[float, float, float], yaw: float, scale: float, base_color: str, cam: tuple[float, float, float, float]) -> None:
        mesh = _load_mesh(model_id)
        if not mesh.vertices:
            return

        world_vertices: list[tuple[float, float, float]] = []
        projected: list[tuple[float, float, float] | None] = []
        px, py, pz = pos
        for vx, vy, vz in mesh.vertices:
            rx, rz = _rotate_y(vx * scale, vz * scale, yaw)
            wx = px + rx
            wy = py + vy * scale
            wz = pz + rz
            world_vertices.append((wx, wy, wz))
            projected.append(self._project_point(wx, wy, wz, cam))

        faces_to_draw: list[tuple[float, list[float], str]] = []
        for face in mesh.faces:
            pts: list[float] = []
            face_world: list[tuple[float, float, float]] = []
            face_depth: list[float] = []
            visible = True
            for idx in face:
                proj = projected[idx]
                if proj is None:
                    visible = False
                    break
                pts.extend((proj[0], proj[1]))
                face_world.append(world_vertices[idx])
                face_depth.append(proj[2])
            if not visible or len(face_world) < 3:
                continue

            ax, ay, az = face_world[0]
            bx, by, bz = face_world[1]
            cx, cy, cz = face_world[2]
            ux, uy, uz = bx - ax, by - ay, bz - az
            vx, vy, vz = cx - ax, cy - ay, cz - az
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            nl = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            nx, ny, nz = nx / nl, ny / nl, nz / nl
            depth_avg = sum(face_depth) / len(face_depth)
            diffuse = max(0.0, nx * 0.25 + ny * 0.82 + nz * -0.22)
            specular = max(0.0, ny) ** 6
            atmosphere = max(0.78, 1.08 - depth_avg / 140.0)
            color = _shade(base_color, (0.42 + diffuse * 0.58 + specular * 0.22) * atmosphere)
            faces_to_draw.append((depth_avg, pts, color))

        for _, pts, color in sorted(faces_to_draw, key=lambda item: item[0], reverse=True):
            self.canvas.create_polygon(pts, fill=color, outline=_shade(color, 0.78), width=1)

    def _model_color(self, model_id: str) -> str:
        palette = {
            "robot_player": "#b8c6d8",
            "rifle": "#73808f",
            "lizard_enemy_a": "#638b52",
            "lizard_enemy_a_raider": "#8e7a4e",
            "lizard_enemy_a_scarred": "#547247",
            "lizard_enemy_b": "#8b6a49",
            "lizard_enemy_b_guard": "#7c5941",
            "lizard_enemy_b_marksman": "#677f68",
            "ape_robot_boss": "#6d574e",
            "enemy_shock_pike": "#97b7d9",
            "enemy_scrap_shotgun": "#86838a",
            "enemy_arc_pistol": "#7a99b8",
            "enemy_cleaver": "#a09b9b",
            "enemy_bolas_launcher": "#7c6442",
            "boss_furnace_cannon": "#a55747",
            "boss_arc_maul": "#6888b6",
            "boss_missile_fist": "#876b5d",
            "pickup_overcharge": "#4dd9ff",
            "pickup_spread": "#ffd44c",
            "pickup_piercing": "#ff66ad",
            "room_hangar": "#756457",
            "room_office_wing": "#6e706c",
            "room_boss_atrium": "#65423f",
            "furniture_set": "#7d6552",
        }
        return palette.get(model_id, "#9aa3ad")

    def _draw_world(self) -> None:
        c = self.canvas
        c.delete("all")
        sky_top = "#111621" if self.room_index < 2 else "#2a1013"
        sky_bottom = "#2e3544" if self.room_index < 2 else "#4b2124"
        for i in range(10):
            y0 = int(i * HEIGHT / 10)
            mix = i / 9 if i else 0.0
            color = _shade(sky_bottom if mix > 0.5 else sky_top, 0.7 + mix * 0.4)
            c.create_rectangle(0, y0, WIDTH, y0 + HEIGHT / 10 + 2, fill=color, outline="")
        c.create_rectangle(0, HORIZON_Y + 145, WIDTH, HEIGHT, fill="#1d1716", outline="")

        cam = self._camera()
        room_id = LEVEL["rooms"][self.room_index]["model"]
        self._draw_mesh(room_id, (0.0, 0.0, 0.0), 0.0, 1.0, self._model_color(room_id), cam)
        room_furniture = {
            0: [((-14.0, 0.0, 8.0), 0.25), ((-2.0, 0.0, -4.0), -0.1), ((10.0, 0.0, -10.0), -0.35), ((14.0, 0.0, 12.0), 0.1)],
            1: [((-18.0, 0.0, 6.0), 0.18), ((-6.0, 0.0, -10.0), 0.08), ((6.0, 0.0, 2.0), -0.2), ((16.0, 0.0, 16.0), 0.32), ((0.0, 0.0, 18.0), 0.0)],
            2: [((-16.0, 0.0, -8.0), 0.25), ((16.0, 0.0, -4.0), -0.25), ((-8.0, 0.0, 12.0), 0.15), ((8.0, 0.0, 14.0), -0.12), ((0.0, 0.0, 20.0), 0.0)],
        }
        for pos, rot in room_furniture.get(self.room_index, []):
            self._draw_mesh("furniture_set", pos, rot, 0.18, self._model_color("furniture_set"), cam)
        if self.enemies and self.room_index < 2:
            for block_x in (-4.0, 0.0, 4.0):
                self._draw_mesh("furniture_set", (block_x, 0.0, ROOM_DEPTH - 2.0), 0.0, 0.12, "#5c4d47", cam)

        for pickup in self.pickups:
            if pickup.taken:
                continue
            bob = 0.7 + math.sin(time.time() * 3.0 + pickup.x) * 0.15
            model_id = {
                "overcharge_rounds": "pickup_overcharge",
                "spread_burst": "pickup_spread",
                "piercing_slugs": "pickup_piercing",
            }.get(pickup.kind, "pickup_overcharge")
            self._draw_mesh(model_id, (pickup.x, bob, pickup.z), time.time(), 0.75, self._model_color(model_id), cam)

        for bullet in self.enemy_projectiles:
            p0 = self._project_point(bullet.prev_x, 1.0, bullet.prev_z, cam)
            p1 = self._project_point(bullet.x, 1.0, bullet.z, cam)
            if p0 and p1:
                c.create_line(p0[0], p0[1], p1[0], p1[1], fill="#ff9c72", width=3)
            model_id = "furniture_set" if bullet.visual == "furniture_throw" else "pickup_overcharge"
            scale = 0.16 if bullet.visual != "furniture_throw" else 0.12
            self._draw_mesh(model_id, (bullet.x, 1.0, bullet.z), time.time(), scale, "#ff8454", cam)
        for bullet in self.bullets:
            p0 = self._project_point(bullet.prev_x, 1.0, bullet.prev_z, cam)
            p1 = self._project_point(bullet.x, 1.0, bullet.z, cam)
            if p0 and p1:
                c.create_line(p0[0], p0[1], p1[0], p1[1], fill="#d8f8ff", width=2)
            self._draw_mesh("pickup_spread", (bullet.x, 1.0, bullet.z), 0.0, 0.1, "#d8f8ff", cam)

        for enemy in sorted(self.enemies, key=lambda e: e.z, reverse=True):
            shadow = self._project_point(enemy.x, 0.03, enemy.z, cam)
            if shadow:
                rx = 20 if not enemy.boss else 34
                ry = 9 if not enemy.boss else 16
                self.canvas.create_oval(shadow[0] - rx, shadow[1] - ry, shadow[0] + rx, shadow[1] + ry, fill="#000000", outline="", stipple="gray50")
            facing = math.atan2(self.player_x - enemy.x, self.player_z - enemy.z)
            model_id = enemy.variant or enemy.kind
            self._draw_mesh(model_id, (enemy.x, enemy.jump_offset, enemy.z), facing, 1.0 if not enemy.boss else 1.3, self._model_color(model_id), cam)
            if enemy.taunt_timer > 0.0:
                mark = self._project_point(enemy.x, 2.6 + enemy.jump_offset, enemy.z, cam)
                if mark:
                    c.create_text(mark[0], mark[1], text="!", fill="#ffcc66", font=("Segoe UI", 16, "bold"))
            weapon_model = {
                "shock_pike": "enemy_shock_pike",
                "scrap_shotgun": "enemy_scrap_shotgun",
                "arc_pistol": "enemy_arc_pistol",
                "raptor_claws": "enemy_raptor_claws",
                "bolas_launcher": "enemy_bolas_launcher",
                "furnace_cannon": "boss_furnace_cannon",
                "arc_maul": "boss_arc_maul",
                "missile_fist": "boss_missile_fist",
            }.get(enemy.weapon, "enemy_shock_pike")
            wx = enemy.x + math.cos(facing) * 0.5
            wz = enemy.z + math.sin(facing) * 0.5
            self._draw_mesh(weapon_model, (wx, 1.0 if not enemy.boss else 1.7, wz), facing, 0.8 if not enemy.boss else 1.0, self._model_color(weapon_model), cam)

        player_shadow = self._project_point(self.player_x, 0.03, self.player_z, cam)
        if player_shadow:
            self.canvas.create_oval(player_shadow[0] - 24, player_shadow[1] - 10, player_shadow[0] + 24, player_shadow[1] + 10, fill="#000000", outline="", stipple="gray50")
        player_yaw = math.atan2(self.aim_x, max(0.1, self.aim_z))
        self._draw_mesh("robot_player", (self.player_x, self.player_y, self.player_z), player_yaw, 1.0, self._model_color("robot_player"), cam)
        self._draw_mesh("rifle", (self.player_x + 0.35, 1.2 + self.player_y, self.player_z + 0.4), player_yaw, 1.0, self._model_color("rifle"), cam)

        c.create_oval(WIDTH / 2 - 6, HEIGHT / 2 - 6, WIDTH / 2 + 6, HEIGHT / 2 + 6, outline="#f1f4f5", width=2)
        c.create_line(WIDTH / 2 - 14, HEIGHT / 2, WIDTH / 2 - 8, HEIGHT / 2, fill="#f1f4f5", width=2)
        c.create_line(WIDTH / 2 + 8, HEIGHT / 2, WIDTH / 2 + 14, HEIGHT / 2, fill="#f1f4f5", width=2)

    def _draw_hud(self) -> None:
        c = self.canvas
        c.create_rectangle(12, 12, 160, 50, fill="#111723", outline="#39465a")
        for i in range(self.player_hp):
            x = 22 + i * 28
            c.create_rectangle(x, 21, x + 20, 39, fill="#ff5867", outline="white")
        c.create_rectangle(WIDTH - 195, 12, WIDTH - 14, 58, fill="#111723", outline="#39465a")
        c.create_text(WIDTH - 104, 27, text="AMMO ∞", fill="white", font=("Segoe UI", 14, "bold"))
        room_names = ["SECURITY HANGAR", "OFFICE WING", "BOSS ATRIUM"]
        room_label = f"ROOM {self.room_index + 1}/3 - {room_names[self.room_index]}"
        c.create_text(WIDTH / 2, 22, text=room_label, fill="#e8ecef", font=("Segoe UI", 15, "bold"))
        if self.active_upgrade:
            remain = max(0.0, self.upgrade_until - time.time())
            c.create_text(WIDTH - 104, 47, text=f"BOOST {remain:0.1f}s", fill="#7df2d2", font=("Segoe UI", 11, "bold"))
        if self.unlocked_upgrades:
            c.create_text(250, 31, text=f"SPECIAL {self.active_upgrade or self.unlocked_upgrades[0]}", fill="#b9ccff", font=("Segoe UI", 11, "bold"))
        c.create_text(340, 50, text="A JUMP  B DODGE  X RELOAD  Y CYCLE  LB PARRY  RB MELEE  LT SPRINT  RT FIRE", fill="#c7d2e1", font=("Segoe UI", 10, "bold"))
        objective = self.current_flow_note or "Clear the room to unlock the next gate"
        if self.current_gate:
            gate = self.current_gate["requirement"]
            if gate["type"] == "pickup_and_enemy_clear":
                objective = f"OPEN {gate['gate'].replace('_', ' ').upper()}: clear zone and secure {gate['required_pickup'].replace('_', ' ').upper()}"
            else:
                objective = f"OPEN {gate['gate'].replace('_', ' ').upper()}: neutralize hostiles"
        c.create_text(WIDTH / 2, 76, text=objective, fill="#b7c4d8", font=("Segoe UI", 10, "bold"))
        if time.time() < self.status_until:
            c.create_text(WIDTH / 2, 58, text=self.status_text, fill="#ffd54e", font=("Segoe UI", 18, "bold"))
        if self.victory:
            c.create_text(WIDTH / 2, HEIGHT / 2, text="STAGE CLEAR", fill="#93ffba", font=("Segoe UI", 34, "bold"))
        elif self.game_over:
            c.create_text(WIDTH / 2, HEIGHT / 2, text="GAME OVER", fill="#ff6f78", font=("Segoe UI", 34, "bold"))

    def update(self) -> None:
        if self.game_over or self.victory:
            self.draw()
            self.root.after(16, self.update)
            return
        self._keyboard_input()
        self._controller_input()
        self._update_vertical_motion()
        self._clamp_player()
        self._update_pickups()
        if self.active_upgrade and time.time() > self.upgrade_until:
            self.active_upgrade = None
        self.audio.update_music(self.room_index, self.room_index == 2 or any(enemy.boss for enemy in self.enemies))
        self._update_bullets()
        self._update_enemies()
        self._update_enemy_projectiles()

        if self.player_hp <= 0:
            self.game_over = True
        elif not self.enemies and not self.room_clear:
            self.room_clear = True
            if self.room_index < len(LEVEL["rooms"]) - 1:
                self._load_room(self.room_index + 1)
            else:
                self.victory = True

        self.draw()
        self.root.after(16, self.update)

    def draw(self) -> None:
        self._draw_world()
        self._draw_hud()

    def run(self) -> None:
        self.update()
        self.root.mainloop()


def smoke_test() -> None:
    game = ShootGame()
    summary = {
        "rooms": len(LEVEL["rooms"]),
        "controller_support": PROJECT.get("controller_support", {}).get("enabled", False),
        "enemy_total": sum(len(room.get("enemies", [])) for room in LEVEL["rooms"]),
        "pickup_total": sum(len(room.get("pickups", [])) for room in LEVEL["rooms"]),
        "player_hp": PROJECT["player"]["hitpoints"],
        "renderer_mode": "obj_low_poly_3d",
        "camera_mode": "over_the_shoulder",
        "movement_mode": "omnidirectional",
        "projectile_trails": True,
        "melee_enabled": True,
        "parry_enabled": True,
        "boss_behavior": "arena_leap_furniture_throw",
        "audio_enabled": PROJECT.get("audio", {}).get("music_enabled", False),
        "gating_mode": "multi_stage_security_shutters",
    }
    print(json.dumps(summary))
    game.root.destroy()


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        smoke_test()
    else:
        ShootGame().run()
