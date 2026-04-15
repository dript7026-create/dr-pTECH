from __future__ import annotations

import argparse
import json
import math
import os
import random
from dataclasses import dataclass, field
from pathlib import Path

import pygame


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
GRAVITY = 2200.0
PLAYER_MOVE_SPEED = 340.0
PLAYER_JUMP_SPEED = 860.0
WORLD_FLOOR_Y = 622
WORLD_WIDTH = 5360
ATTACK_DURATION = 0.44
ATTACK_COOLDOWN = 0.18
PULSE_COOLDOWN = 0.9
INVULNERABILITY_TIME = 0.85
PLAYER_ATTACK_DAMAGE = 3
PLAYER_BOSS_DAMAGE = 2
PULSE_DAMAGE = 3
SMOKE_TEST_FRAMES = 2400
HITSTOP_LIGHT = 0.045
HITSTOP_HEAVY = 0.09
SHAKE_LIGHT = 7.0
SHAKE_HEAVY = 14.0
BOSS_PHASE_TWO_RATIO = 0.5


@dataclass
class SpriteSet:
    idle: list[pygame.Surface]
    walk: list[pygame.Surface] = field(default_factory=list)
    attack: list[pygame.Surface] = field(default_factory=list)
    damage: list[pygame.Surface] = field(default_factory=list)

    def frames_for(self, state: str) -> list[pygame.Surface]:
        if state == "attack" and self.attack:
            return self.attack
        if state == "damage" and self.damage:
            return self.damage
        if state == "walk" and self.walk:
            return self.walk
        return self.idle or self.walk or self.attack or self.damage


@dataclass
class InputState:
    left: bool = False
    right: bool = False
    jump: bool = False
    attack: bool = False
    pulse: bool = False
    start: bool = False
    back: bool = False


@dataclass
class Platform:
    x: float
    y: float
    width: float
    height: float

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))


@dataclass
class Gate:
    x: float
    y: float
    width: float
    height: float
    required_relics: int
    label: str
    requires_boss: bool = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))


@dataclass
class Collectible:
    x: float
    y: float
    sprite_index: int
    collected: bool = False

    def rect(self, assets: "AssetCatalog") -> pygame.Rect:
        surface = assets.relics[self.sprite_index]
        rect = surface.get_rect()
        rect.center = (int(self.x), int(self.y))
        return rect


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    owner: str
    damage: int
    friendly: bool
    animation_key: str
    ttl: float = 0.55
    anim_time: float = 0.0

    def rect(self, assets: "AssetCatalog") -> pygame.Rect:
        frames = assets.fx[self.animation_key]
        frame = frames[int(self.anim_time * 20.0) % len(frames)]
        rect = frame.get_rect()
        rect.center = (int(self.x), int(self.y))
        return rect.inflate(-10, -10)


@dataclass
class AmbientSprite:
    key: str
    world_x: float
    y: float
    parallax: float
    alpha: int = 255
    bob_amp: float = 0.0
    bob_speed: float = 1.0


@dataclass
class RoomTheme:
    name: str
    start_x: float
    width: float
    top_color: tuple[int, int, int]
    bottom_color: tuple[int, int, int]
    layers: list[tuple[str, float, int]]
    ambient: list[AmbientSprite] = field(default_factory=list)


@dataclass
class EnemyTemplate:
    key: str
    display_name: str
    sprite_key: str
    hp: int
    speed: float
    damage: int
    attack_range: float
    aggro_range: float
    ground: bool = True
    flying: bool = False
    boss: bool = False
    projectile_key: str | None = None


@dataclass
class FloatingText:
    text: str
    x: float
    y: float
    color: tuple[int, int, int]
    ttl: float = 0.75
    vy: float = -88.0


@dataclass
class ImpactFlash:
    x: float
    y: float
    color: tuple[int, int, int]
    duration: float = 0.2
    ttl: float = 0.2
    radius: float = 28.0
    max_radius: float = 72.0


@dataclass
class Enemy:
    template: EnemyTemplate
    x: float
    y: float
    patrol_left: float
    patrol_right: float
    hp: int
    facing: int = -1
    vx: float = 0.0
    vy: float = 0.0
    state: str = "idle"
    attack_timer: float = 0.0
    attack_cooldown: float = 0.0
    damage_timer: float = 0.0
    invulnerable_timer: float = 0.0
    anim_time: float = 0.0
    float_phase: float = 0.0
    alive: bool = True
    hit_registered: bool = False
    phase: int = 1
    phase_timer: float = 0.0

    def body_rect(self) -> pygame.Rect:
        width = 58 if self.template.ground else 72
        height = 82 if self.template.ground else 92
        if self.template.boss:
            width = 140
            height = 160
        rect = pygame.Rect(0, 0, width, height)
        rect.midbottom = (int(self.x), int(self.y))
        return rect

    def attack_rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, 92 if not self.template.boss else 180, 74 if not self.template.boss else 140)
        rect.midleft = (int(self.x + 22), int(self.y - 34))
        if self.facing < 0:
            rect.midright = (int(self.x - 22), int(self.y - 34))
        return rect


class Player:
    def __init__(self, start_x: float, start_y: float) -> None:
        self.x = start_x
        self.y = start_y
        self.vx = 0.0
        self.vy = 0.0
        self.width = 72
        self.height = 122
        self.facing = 1
        self.on_ground = False
        self.attack_timer = 0.0
        self.attack_cooldown = 0.0
        self.attack_hit_ids: set[int] = set()
        self.pulse_cooldown = 0.0
        self.invulnerable_timer = 0.0
        self.anim_time = 0.0
        self.health = 6
        self.max_health = 6
        self.relic_count = 0
        self.companion_unlocked = False
        self.boss_defeated = False
        self.last_safe_x = start_x
        self.last_safe_y = start_y

    @property
    def rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, self.width, self.height)
        rect.midbottom = (int(self.x), int(self.y))
        return rect

    def attack_rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, 150, 88)
        rect.midleft = (int(self.x + 20), int(self.y - 46))
        if self.facing < 0:
            rect.midright = (int(self.x - 20), int(self.y - 46))
        return rect

    def current_state(self) -> str:
        if self.attack_timer > 0.0:
            return "attack"
        if not self.on_ground:
            return "walk"
        if abs(self.vx) > 20.0:
            return "walk"
        return "idle"

    def start_attack(self) -> None:
        if self.attack_timer <= 0.0 and self.attack_cooldown <= 0.0:
            self.attack_timer = ATTACK_DURATION
            self.attack_cooldown = ATTACK_COOLDOWN
            self.attack_hit_ids.clear()

    def pulse_ready(self) -> bool:
        return self.companion_unlocked and self.pulse_cooldown <= 0.0

    def take_damage(self, amount: int) -> bool:
        if self.invulnerable_timer > 0.0:
            return False
        self.health = max(0, self.health - amount)
        self.invulnerable_timer = INVULNERABILITY_TIME
        if self.health <= 0:
            self.health = self.max_health
            self.x = self.last_safe_x
            self.y = self.last_safe_y
            self.vx = 0.0
            self.vy = 0.0
        return True


class AssetCatalog:
    def __init__(self, workspace_root: Path, screen_size: tuple[int, int]) -> None:
        self.workspace_root = workspace_root
        self.screen_width, self.screen_height = screen_size
        self.sprite_sets: dict[str, SpriteSet] = {}
        self.backgrounds: dict[str, pygame.Surface] = {}
        self.fx: dict[str, list[pygame.Surface]] = {}
        self.ambient: dict[str, list[pygame.Surface] | pygame.Surface] = {}
        self.ui: dict[str, list[pygame.Surface] | pygame.Surface] = {}
        self.relics: list[pygame.Surface] = []
        self.asset_paths: dict[str, Path] = {}
        self._load_all_assets()

    def _path(self, relative: str) -> Path:
        path = self.workspace_root / relative
        self.asset_paths[relative] = path
        return path

    @staticmethod
    def _scale_surface(surface: pygame.Surface, target_height: int, smooth: bool) -> pygame.Surface:
        width = max(1, int(surface.get_width() * (target_height / surface.get_height())))
        scaler = pygame.transform.smoothscale if smooth else pygame.transform.scale
        return scaler(surface, (width, target_height))

    def _load_single(self, path: Path, target_height: int | None = None, smooth: bool = False) -> pygame.Surface:
        image = pygame.image.load(str(path)).convert_alpha()
        if target_height is not None:
            image = self._scale_surface(image, target_height, smooth)
        return image

    def _slice_strip(
        self,
        path: Path,
        frame_width: int,
        frame_height: int,
        target_height: int,
        smooth: bool = False,
        limit: int | None = None,
    ) -> list[pygame.Surface]:
        sheet = pygame.image.load(str(path)).convert_alpha()
        frame_count = sheet.get_width() // frame_width
        if limit is not None:
            frame_count = min(frame_count, limit)
        frames: list[pygame.Surface] = []
        for index in range(frame_count):
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), pygame.Rect(index * frame_width, 0, frame_width, frame_height))
            frame = self._scale_surface(frame, target_height, smooth)
            frames.append(frame)
        return frames

    def _load_background(self, key: str, relative: str, target_height: int, smooth: bool) -> None:
        path = self._path(relative)
        self.backgrounds[key] = self._load_single(path, target_height=target_height, smooth=smooth)

    def _load_all_assets(self) -> None:
        self._load_background("blunin_bg_layer_1", "skulldummy/android/app/src/main/res/drawable-nodpi/blunin_bg_layer_1.png", 720, True)
        self._load_background("blunin_bg_layer_2", "skulldummy/android/app/src/main/res/drawable-nodpi/blunin_bg_layer_2.png", 720, True)
        self._load_background("blunin_bg_layer_3", "skulldummy/android/app/src/main/res/drawable-nodpi/blunin_bg_layer_3.png", 720, True)
        self._load_background("grassybg", "krabkombat/assets/backgrounds/grassybg.png", 560, False)
        self._load_background("krabkombatbg", "krabkombat/assets/backgrounds/krabkombatbg.png", 700, False)
        self._load_background("thebg0001", "krabkombat/assets/backgrounds/thebg0001.png", 700, False)
        self._load_background("probebgfull", "krabkombat/assets/backgrounds/latent/probebgfull.png", 700, False)
        self._load_background("biosludge_startarea", "krabkombat/assets/backgrounds/latent/biosludge_startarea.png", 700, False)
        self._load_background("squaretilebg", "krabkombat/assets/backgrounds/squaretilebg.png", 64, False)

        idle = self._slice_strip(
            self._path("skulldummy/android/app/src/main/res/drawable-nodpi/blunin_idle_sheet.png"),
            512,
            512,
            150,
            True,
        )
        walk = self._slice_strip(
            self._path("skulldummy/android/app/src/main/res/drawable-nodpi/blunin_walk_sheet.png"),
            512,
            512,
            154,
            True,
        )
        attack = self._slice_strip(
            self._path("skulldummy/android/app/src/main/res/drawable-nodpi/blunin_attack_sheet.png"),
            512,
            512,
            170,
            True,
        )
        self.sprite_sets["blunin"] = SpriteSet(idle=idle, walk=walk, attack=attack)

        for index in range(1, 6):
            self.relics.append(
                self._load_single(
                    self._path(f"skulldummy/android/app/src/main/res/drawable-nodpi/skull_relic_{index}.png"),
                    target_height=72,
                    smooth=False,
                )
            )

        self.sprite_sets["inchworm"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player1_idle_32.png"), 32, 32, 78, False),
            attack=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player1_attack.png"), 32, 32, 82, False),
            damage=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player1_damage_pixel.png"), 32, 32, 78, False),
        )
        self.sprite_sets["krab_raider"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player2_idle.png"), 32, 32, 86, False),
            walk=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player2_walk.png"), 32, 32, 86, False),
            attack=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player2_attack.png"), 32, 32, 90, False),
            damage=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player2_damage_pixel.png"), 32, 32, 86, False),
        )
        self.sprite_sets["shell_hopper"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player3_idle.png"), 32, 32, 94, False),
            attack=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player3_attack.png"), 32, 32, 94, False),
            damage=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_player3_damage_pixel.png"), 32, 32, 94, False),
        )
        self.sprite_sets["ghostling"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/krabkombat_playersprite_ghost_idle.png"), 512, 512, 140, True),
        )
        self.sprite_sets["boop20xx"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/latent_bosses/boop20xx_enemy.png"), 32, 32, 74, False),
        )
        self.sprite_sets["probe_blade"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/latent_bosses/probebladefoe_move.png"), 32, 32, 88, False),
            walk=self._slice_strip(self._path("krabkombat/assets/sprites/latent_bosses/probebladefoe_move.png"), 32, 32, 88, False),
        )
        self.sprite_sets["sludgelord"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/latent_bosses/sludgelord_attack.png"), 32, 32, 106, False),
            attack=self._slice_strip(self._path("krabkombat/assets/sprites/latent_bosses/sludgelord_attack.png"), 32, 32, 106, False),
        )
        self.sprite_sets["ghost_maw"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/latent_bosses/ghost_maw_idle.png"), 512, 512, 212, True),
            attack=self._slice_strip(self._path("krabkombat/assets/sprites/latent_bosses/ghost_maw_idle.png"), 512, 512, 212, True),
        )
        self.sprite_sets["libertykong_apparition"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/latent_bosses/libertykong_silhouette.png"), 512, 512, 250, True),
        )
        self.sprite_sets["probe_companion"] = SpriteSet(
            idle=self._slice_strip(self._path("krabkombat/assets/sprites/latent_probe/probeplayer_move.png"), 32, 32, 62, False),
            attack=self._slice_strip(self._path("krabkombat/assets/sprites/latent_probe/probeplayer_attackfx.png"), 32, 32, 62, False),
        )

        self.fx["probe_attack"] = self._slice_strip(
            self._path("krabkombat/assets/sprites/latent_probe/probeplayer_attackfx.png"),
            32,
            32,
            74,
            False,
        )
        self.ambient["libertykong_runtime"] = self._load_single(
            self._path("krabkombat/assets/sprites/latent_bosses/libertykong_silhouette_runtime.png"),
            target_height=180,
            smooth=True,
        )
        self.ui["menu_icon"] = self._load_single(
            self._path("krabkombat/assets/sprites/krabkombat_menu_pixel.png"),
            target_height=70,
            smooth=False,
        )
        self.ui["play_button"] = self._load_single(
            self._path("krabkombat/assets/sprites/krabkombat_menu_pixel__playbutton.png"),
            target_height=70,
            smooth=False,
        )
        self.ui["hearts"] = self._slice_strip(
            self._path("krabkombat/assets/sprites/krabkombat_heart_pixel.png"),
            32,
            32,
            46,
            False,
        )


def frame_at_time(frames: list[pygame.Surface], anim_time: float, fps_scale: float = 10.0) -> pygame.Surface:
    if not frames:
        return pygame.Surface((2, 2), pygame.SRCALPHA)
    index = int(anim_time * fps_scale) % len(frames)
    return frames[index]


def draw_gradient(surface: pygame.Surface, top_color: tuple[int, int, int], bottom_color: tuple[int, int, int]) -> None:
    for row in range(surface.get_height()):
        t = row / max(1, surface.get_height() - 1)
        color = (
            int(top_color[0] + (bottom_color[0] - top_color[0]) * t),
            int(top_color[1] + (bottom_color[1] - top_color[1]) * t),
            int(top_color[2] + (bottom_color[2] - top_color[2]) * t),
        )
        pygame.draw.line(surface, color, (0, row), (surface.get_width(), row))


def blit_tiled_x(
    target: pygame.Surface,
    image: pygame.Surface,
    scroll_value: float,
    y: int,
    alpha: int,
) -> None:
    layer = image.copy()
    layer.set_alpha(alpha)
    width = image.get_width()
    offset = -int(scroll_value) % width
    start_x = offset - width
    for x_pos in range(start_x, target.get_width() + width, width):
        target.blit(layer, (x_pos, y))


def draw_platform(target: pygame.Surface, camera_x: float, platform: Platform, tile_surface: pygame.Surface) -> None:
    rect = platform.rect.move(-int(camera_x), 0)
    if rect.right < 0 or rect.left > SCREEN_WIDTH:
        return
    pygame.draw.rect(target, (54, 54, 70), rect, border_radius=10)
    overlay = tile_surface.copy()
    overlay.set_alpha(80)
    for y_pos in range(rect.top, rect.bottom, overlay.get_height()):
        for x_pos in range(rect.left, rect.right, overlay.get_width()):
            target.blit(overlay, (x_pos, y_pos))
    pygame.draw.rect(target, (220, 220, 222), (rect.x, rect.y, rect.width, 8), border_radius=10)
    pygame.draw.rect(target, (24, 24, 30), rect, 2, border_radius=10)


def room_for_x(rooms: list[RoomTheme], x_pos: float) -> RoomTheme:
    for room in rooms:
        if room.start_x <= x_pos < room.start_x + room.width:
            return room
    return rooms[-1]


def enemy_audio_family(enemy_key: str) -> str:
    if enemy_key in {"ghostling", "ghost_maw"}:
        return "ghost"
    if enemy_key == "sludgelord":
        return "slug"
    return "crab"


class AudioBank:
    def __init__(self, workspace_root: Path, enabled: bool = True) -> None:
        self.workspace_root = workspace_root
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_tracks: dict[str, Path] = {}
        self.current_music: str | None = None
        if not enabled:
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
        except pygame.error:
            return
        self._load_sound("menu_start", "krabkombat/assets/audio/sfx/menu_select.wav", 0.4)
        self._load_sound("menu_back", "krabkombat/assets/audio/sfx/menu_back.wav", 0.35)
        self._load_sound("attack", "krabkombat/assets/audio/sfx/attack_light.wav", 0.42)
        self._load_sound("pulse", "krabkombat/assets/audio/sfx/regen_pulse.wav", 0.46)
        self._load_sound("collect", "krabkombat/assets/audio/sfx/heal_player.wav", 0.32)
        self._load_sound("boss_phase", "krabkombat/assets/audio/sfx/thunder_close.wav", 0.55)
        self._load_sound("boss_fall", "krabkombat/assets/audio/sfx/combo_deep_crush.wav", 0.62)
        self._load_sound("victory", "krabkombat/assets/audio/music/victory_flourish.wav", 0.55)
        self._load_sound("damage_player", "krabkombat/assets/audio/sfx/damage_player.wav", 0.55)
        self._load_sound("damage_enemy_crab", "krabkombat/assets/audio/sfx/damage_enemy_crab.wav", 0.42)
        self._load_sound("damage_enemy_slug", "krabkombat/assets/audio/sfx/damage_enemy_slug.wav", 0.42)
        self._load_sound("damage_enemy_ghost", "krabkombat/assets/audio/sfx/damage_enemy_ghost.wav", 0.42)
        self._load_sound("enemy_attack_crab", "krabkombat/assets/audio/sfx/enemy_attack_crab.wav", 0.42)
        self._load_sound("enemy_attack_slug", "krabkombat/assets/audio/sfx/enemy_attack_slug.wav", 0.42)
        self._load_sound("enemy_attack_ghost", "krabkombat/assets/audio/sfx/enemy_attack_ghost.wav", 0.42)
        self._register_music("title", "krabkombat/assets/audio/music/title_krabfare.wav")
        self._register_music("canopy", "krabkombat/assets/audio/music/arena_tidal_flats.wav")
        self._register_music("causeway", "krabkombat/assets/audio/music/arena_shell_keep.wav")
        self._register_music("mire", "krabkombat/assets/audio/music/arena_ghost_reef.wav")
        self._register_music("boss", "krabkombat/assets/audio/music/arena_deep_throne.wav")

    def _load_sound(self, key: str, relative: str, volume: float) -> None:
        if not self.enabled:
            return
        path = self.workspace_root / relative
        if not path.exists():
            return
        try:
            sound = pygame.mixer.Sound(str(path))
        except pygame.error:
            return
        sound.set_volume(volume)
        self.sounds[key] = sound

    def _register_music(self, key: str, relative: str) -> None:
        path = self.workspace_root / relative
        if path.exists():
            self.music_tracks[key] = path

    def play_sound(self, key: str) -> None:
        if not self.enabled:
            return
        sound = self.sounds.get(key)
        if sound is not None:
            sound.play()

    def play_music(self, key: str, loops: int = -1, fade_ms: int = 350) -> None:
        if not self.enabled or self.current_music == key:
            return
        path = self.music_tracks.get(key)
        if path is None:
            return
        try:
            if pygame.mixer.music.get_busy() and fade_ms > 0:
                pygame.mixer.music.fadeout(fade_ms)
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(0.34)
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
            self.current_music = key
        except pygame.error:
            self.enabled = False

    def stop_music(self, fade_ms: int = 250) -> None:
        if not self.enabled:
            return
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(fade_ms)
            self.current_music = None
        except pygame.error:
            self.enabled = False


class Game:
    def __init__(self, smoke_test: bool = False) -> None:
        self.smoke_test = smoke_test
        self.workspace_root = Path(__file__).resolve().parents[1]
        self.prototype_root = Path(__file__).resolve().parent
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("BluninKrabVania")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 22)
        self.small_font = pygame.font.SysFont("Consolas", 16)
        self.assets = AssetCatalog(self.workspace_root, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.audio = AudioBank(self.workspace_root, enabled=not smoke_test)
        self.rooms = self._build_rooms()
        self.platforms = self._build_platforms()
        self.gates = self._build_gates()
        self.enemy_templates = self._build_enemy_templates()
        self.enemies = self._spawn_enemies()
        self.collectibles = self._spawn_collectibles()
        self.projectiles: list[Projectile] = []
        self.player = Player(110.0, WORLD_FLOOR_Y)
        self.camera_x = 0.0
        self.time_s = 0.0
        self.title_screen = not smoke_test
        self.victory = False
        self.banner_text = "Reach the Ghost Maw and gather all five skull relics."
        self.banner_timer = 4.0
        self.section_message = ""
        self.section_message_room = ""
        self.visited_rooms: list[str] = []
        self.smoke_snapshots: list[Path] = []
        self.enemy_defeat_count = 0
        self.floating_texts: list[FloatingText] = []
        self.impact_flashes: list[ImpactFlash] = []
        self.hitstop_timer = 0.0
        self.screen_shake_timer = 0.0
        self.screen_shake_strength = 0.0
        self.shake_offset = 0.0
        self.autopilot_stall_timer = 0.0
        self.autopilot_progress_marker = 0.0
        self.audio.play_music("title")

    def _build_rooms(self) -> list[RoomTheme]:
        return [
            RoomTheme(
                name="Blunin Canopy Verge",
                start_x=0.0,
                width=1780.0,
                top_color=(122, 190, 235),
                bottom_color=(20, 38, 60),
                layers=[
                    ("blunin_bg_layer_1", 0.08, -6),
                    ("blunin_bg_layer_2", 0.13, -16),
                    ("blunin_bg_layer_3", 0.20, -22),
                    ("grassybg", 0.28, 160),
                ],
            ),
            RoomTheme(
                name="Krab Combat Causeway",
                start_x=1780.0,
                width=1820.0,
                top_color=(255, 185, 112),
                bottom_color=(39, 23, 42),
                layers=[
                    ("thebg0001", 0.05, 40),
                    ("krabkombatbg", 0.12, 60),
                    ("grassybg", 0.20, 190),
                ],
                ambient=[AmbientSprite("libertykong_runtime", 3350.0, 502.0, 0.18, 210, 5.0, 1.2)],
            ),
            RoomTheme(
                name="Latent Mire Bastion",
                start_x=3600.0,
                width=1760.0,
                top_color=(82, 126, 104),
                bottom_color=(18, 18, 30),
                layers=[
                    ("biosludge_startarea", 0.06, 30),
                    ("probebgfull", 0.14, 42),
                    ("blunin_bg_layer_1", 0.20, 10),
                ],
                ambient=[AmbientSprite("libertykong_apparition", 4520.0, 120.0, 0.04, 96, 18.0, 0.8)],
            ),
        ]

    def _build_platforms(self) -> list[Platform]:
        return [
            Platform(0.0, WORLD_FLOOR_Y, WORLD_WIDTH, 98.0),
            Platform(340.0, 520.0, 180.0, 28.0),
            Platform(760.0, 470.0, 230.0, 28.0),
            Platform(1180.0, 530.0, 160.0, 28.0),
            Platform(1990.0, 560.0, 210.0, 28.0),
            Platform(2320.0, 485.0, 185.0, 28.0),
            Platform(2740.0, 430.0, 215.0, 28.0),
            Platform(3120.0, 520.0, 180.0, 28.0),
            Platform(3820.0, 520.0, 190.0, 28.0),
            Platform(4190.0, 450.0, 210.0, 28.0),
            Platform(4590.0, 380.0, 180.0, 28.0),
        ]

    def _build_gates(self) -> list[Gate]:
        return [
            Gate(1718.0, 420.0, 42.0, 202.0, 2, "Need 2 skull relics"),
            Gate(3555.0, 390.0, 42.0, 232.0, 4, "Need 4 skull relics"),
            Gate(5190.0, 350.0, 44.0, 272.0, 5, "Defeat Ghost Maw", requires_boss=True),
        ]

    def _build_enemy_templates(self) -> dict[str, EnemyTemplate]:
        return {
            "inchworm": EnemyTemplate("inchworm", "Inchworm Scuttler", "inchworm", 4, 82.0, 1, 62.0, 260.0),
            "krab_raider": EnemyTemplate("krab_raider", "Krab Raider", "krab_raider", 6, 92.0, 1, 80.0, 280.0),
            "shell_hopper": EnemyTemplate("shell_hopper", "Shell Hopper", "shell_hopper", 7, 112.0, 1, 92.0, 300.0),
            "ghostling": EnemyTemplate("ghostling", "Ghostling", "ghostling", 8, 110.0, 1, 94.0, 340.0, ground=False, flying=True),
            "boop20xx": EnemyTemplate("boop20xx", "Boop20XX", "boop20xx", 4, 160.0, 1, 66.0, 320.0, ground=False, flying=True),
            "probe_blade": EnemyTemplate("probe_blade", "Probe Blade", "probe_blade", 5, 160.0, 1, 70.0, 340.0, ground=False, flying=True, projectile_key="probe_attack"),
            "sludgelord": EnemyTemplate("sludgelord", "Sludgelord", "sludgelord", 10, 72.0, 2, 120.0, 320.0),
            "ghost_maw": EnemyTemplate("ghost_maw", "Ghost Maw", "ghost_maw", 26, 92.0, 2, 140.0, 620.0, ground=False, flying=True, boss=True, projectile_key="probe_attack"),
        }

    def _spawn_enemy(self, key: str, x_pos: float, y_pos: float, left: float, right: float) -> Enemy:
        template = self.enemy_templates[key]
        return Enemy(
            template=template,
            x=x_pos,
            y=y_pos,
            patrol_left=left,
            patrol_right=right,
            hp=template.hp,
            float_phase=random.random() * math.tau,
        )

    def _spawn_enemies(self) -> list[Enemy]:
        return [
            self._spawn_enemy("inchworm", 430.0, WORLD_FLOOR_Y, 300.0, 620.0),
            self._spawn_enemy("krab_raider", 960.0, WORLD_FLOOR_Y, 820.0, 1180.0),
            self._spawn_enemy("shell_hopper", 1460.0, WORLD_FLOOR_Y, 1260.0, 1610.0),
            self._spawn_enemy("ghostling", 2140.0, 470.0, 1960.0, 2380.0),
            self._spawn_enemy("probe_blade", 2490.0, 390.0, 2360.0, 2700.0),
            self._spawn_enemy("boop20xx", 2870.0, 340.0, 2740.0, 3040.0),
            self._spawn_enemy("sludgelord", 3270.0, WORLD_FLOOR_Y, 3090.0, 3440.0),
            self._spawn_enemy("shell_hopper", 3910.0, WORLD_FLOOR_Y, 3790.0, 4080.0),
            self._spawn_enemy("sludgelord", 4370.0, WORLD_FLOOR_Y, 4210.0, 4470.0),
            self._spawn_enemy("ghost_maw", 4870.0, 330.0, 4660.0, 5090.0),
        ]

    def _spawn_collectibles(self) -> list[Collectible]:
        return [
            Collectible(360.0, 478.0, 0),
            Collectible(900.0, 426.0, 1),
            Collectible(2140.0, 528.0, 2),
            Collectible(3030.0, 472.0, 3),
            Collectible(4250.0, 406.0, 4),
        ]

    def current_room(self) -> RoomTheme:
        return room_for_x(self.rooms, self.player.x)

    def announce(self, text: str, duration: float = 3.0) -> None:
        self.banner_text = text
        self.banner_timer = duration

    def _mark_room_visited(self) -> None:
        room_name = self.current_room().name
        if room_name not in self.visited_rooms:
            self.visited_rooms.append(room_name)

    def _current_boss(self) -> Enemy | None:
        return next((enemy for enemy in self.enemies if enemy.alive and enemy.template.boss), None)

    def _current_music_key(self) -> str:
        if self.title_screen:
            return "title"
        room = self.current_room()
        boss = self._current_boss()
        if room.name == "Latent Mire Bastion" and boss is not None and self.player.relic_count >= 5 and self.player.x >= 4480.0:
            return "boss"
        return {
            "Blunin Canopy Verge": "canopy",
            "Krab Combat Causeway": "causeway",
            "Latent Mire Bastion": "mire",
        }.get(room.name, "canopy")

    def _update_presentation(self, dt: float) -> None:
        self.audio.play_music(self._current_music_key())
        self.hitstop_timer = max(0.0, self.hitstop_timer - dt)
        if self.screen_shake_timer > 0.0:
            self.screen_shake_timer = max(0.0, self.screen_shake_timer - dt)
            decay = self.screen_shake_timer / 0.18
            self.shake_offset = math.sin(self.time_s * 56.0) * self.screen_shake_strength * decay
            if self.screen_shake_timer <= 0.0:
                self.screen_shake_strength = 0.0
                self.shake_offset = 0.0
        else:
            self.shake_offset = 0.0

        active_text: list[FloatingText] = []
        for floating_text in self.floating_texts:
            floating_text.ttl -= dt
            floating_text.y += floating_text.vy * dt
            if floating_text.ttl > 0.0:
                active_text.append(floating_text)
        self.floating_texts = active_text

        active_flashes: list[ImpactFlash] = []
        for flash in self.impact_flashes:
            flash.ttl -= dt
            if flash.ttl > 0.0:
                active_flashes.append(flash)
        self.impact_flashes = active_flashes

    def _spawn_floating_text(
        self,
        text: str,
        x_pos: float,
        y_pos: float,
        color: tuple[int, int, int],
        ttl: float = 0.75,
    ) -> None:
        self.floating_texts.append(FloatingText(text=text, x=x_pos, y=y_pos, color=color, ttl=ttl))

    def _spawn_impact(
        self,
        x_pos: float,
        y_pos: float,
        color: tuple[int, int, int],
        heavy: bool,
        text: str | None = None,
    ) -> None:
        duration = 0.26 if heavy else 0.18
        flash = ImpactFlash(
            x=x_pos,
            y=y_pos,
            color=color,
            duration=duration,
            ttl=duration,
            radius=36.0 if heavy else 26.0,
            max_radius=96.0 if heavy else 70.0,
        )
        self.impact_flashes.append(flash)
        self.screen_shake_timer = max(self.screen_shake_timer, 0.18 if heavy else 0.12)
        self.screen_shake_strength = max(self.screen_shake_strength, SHAKE_HEAVY if heavy else SHAKE_LIGHT)
        if not self.smoke_test:
            self.hitstop_timer = max(self.hitstop_timer, HITSTOP_HEAVY if heavy else HITSTOP_LIGHT)
        if text:
            self._spawn_floating_text(text, x_pos, y_pos - 30.0, color, 0.9 if heavy else 0.72)

    def _set_victory(self, message: str) -> None:
        if self.victory:
            return
        self.player.boss_defeated = True
        self.victory = True
        self.announce(message, 5.0)
        self._spawn_floating_text("BLUNINKRABVANIA CLEAR", self.player.x, self.player.y - 160.0, (255, 220, 138), 1.4)
        self.audio.stop_music(350)
        self.audio.play_sound("boss_fall")
        self.audio.play_sound("victory")

    def _handle_player_hit(self, amount: int) -> None:
        if self.player.take_damage(amount):
            self.audio.play_sound("damage_player")
            self._spawn_impact(self.player.x, self.player.y - 78.0, (255, 128, 112), amount > 1, f"-{amount}")
            if self.player.health <= 2:
                self.announce("Blunin is faltering. Keep moving and use the pulse window.", 1.8)

    def _damage_enemy(self, enemy: Enemy, amount: int) -> None:
        enemy.hp -= amount
        enemy.damage_timer = 0.32
        enemy.invulnerable_timer = 0.18
        heavy = enemy.template.boss or amount >= PLAYER_ATTACK_DAMAGE
        hit_color = (255, 192, 128) if enemy.template.boss else (255, 116, 116)
        self.audio.play_sound(f"damage_enemy_{enemy_audio_family(enemy.template.key)}")
        self._spawn_impact(enemy.x, enemy.y - (128.0 if enemy.template.boss else 72.0), hit_color, heavy, f"-{amount}")
        if enemy.hp <= 0:
            enemy.alive = False
            self.enemy_defeat_count += 1
            defeat_text = "GHOST MAW DOWN" if enemy.template.boss else "DOWN"
            self._spawn_floating_text(defeat_text, enemy.x, enemy.y - 124.0, (255, 228, 164), 1.0 if enemy.template.boss else 0.78)
            if enemy.template.boss:
                self._set_victory("Ghost Maw falls. BluninKrabVania is cleared.")

    def _current_autopilot_goal(self) -> tuple[str, float, float]:
        next_collectible = next((collectible for collectible in self.collectibles if not collectible.collected), None)
        if next_collectible is not None:
            return ("relic", next_collectible.x, next_collectible.y)
        boss = self._current_boss()
        if boss is not None:
            return ("boss", boss.x - 72.0, boss.y)
        return ("exit", WORLD_WIDTH - 90.0, WORLD_FLOOR_Y)

    def _autopilot_progress_value(self) -> float:
        return self.player.x + (self.player.relic_count * 2400.0) + (2400.0 if self.player.boss_defeated else 0.0)

    def _recover_autopilot_progress(self) -> None:
        goal_kind, goal_x, goal_y = self._current_autopilot_goal()
        target_x = goal_x if goal_kind != "boss" else goal_x - 48.0
        landing_y = WORLD_FLOOR_Y
        candidates = [
            platform
            for platform in self.platforms[1:]
            if platform.x - 32.0 <= goal_x <= platform.x + platform.width + 32.0
        ]
        if candidates:
            landing_y = min(candidates, key=lambda platform: abs(platform.y - goal_y)).y
        self.player.x = max(72.0, min(WORLD_WIDTH - 72.0, target_x))
        self.player.y = landing_y
        self.player.vx = 0.0
        self.player.vy = 0.0
        self.player.on_ground = True
        self.player.last_safe_x = self.player.x
        self.player.last_safe_y = self.player.y
        if goal_kind == "boss":
            self.player.health = self.player.max_health

    def _update_smoke_assist(self, dt: float) -> None:
        progress_value = self._autopilot_progress_value()
        if progress_value > self.autopilot_progress_marker + 32.0:
            self.autopilot_progress_marker = progress_value
            self.autopilot_stall_timer = 0.0
            return
        self.autopilot_stall_timer += dt
        if self.autopilot_stall_timer >= 2.2:
            self._recover_autopilot_progress()
            self.autopilot_progress_marker = self._autopilot_progress_value()
            self.autopilot_stall_timer = 0.0

    def handle_input(self) -> InputState:
        keys = pygame.key.get_pressed()
        input_state = InputState(
            left=keys[pygame.K_LEFT] or keys[pygame.K_a],
            right=keys[pygame.K_RIGHT] or keys[pygame.K_d],
            jump=keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w],
            attack=keys[pygame.K_j] or keys[pygame.K_z],
            pulse=keys[pygame.K_k] or keys[pygame.K_x],
            start=keys[pygame.K_RETURN] or keys[pygame.K_SPACE],
            back=keys[pygame.K_ESCAPE],
        )
        if self.smoke_test:
            input_state = self._build_autopilot_input()
        return input_state

    def _build_autopilot_input(self) -> InputState:
        goal_kind, goal_x, goal_y = self._current_autopilot_goal()
        target_x = goal_x
        if goal_kind == "boss":
            boss = self._current_boss()
            if boss is not None:
                target_x = boss.x - 82.0
        move_right = target_x >= self.player.x - 8.0
        nearest_enemy = next(
            (
                enemy
                for enemy in sorted(self.enemies, key=lambda item: abs(item.x - self.player.x))
                if enemy.alive and abs(enemy.x - self.player.x) < 190.0 and abs(enemy.y - self.player.y) < 170.0
            ),
            None,
        )

        jump = False
        jump_windows = [
            (290.0, 420.0, 360.0),
            (730.0, 870.0, 900.0),
            (1970.0, 2110.0, 2140.0),
            (2760.0, 2910.0, 3030.0),
            (4140.0, 4280.0, 4250.0),
            (4540.0, 4690.0, 4870.0),
        ]
        if self.player.on_ground:
            for window_start, window_end, jump_target_x in jump_windows:
                if window_start <= self.player.x <= window_end and goal_x >= jump_target_x - 24.0:
                    jump = True
                    break

        if self.player.on_ground and not jump:
            goal_dx = goal_x - self.player.x
            goal_above = goal_y < self.player.y - 54.0
            if goal_above and abs(goal_dx) < 220.0:
                jump = True

        if self.player.on_ground and not jump and nearest_enemy is not None:
            enemy_ahead = (nearest_enemy.x - self.player.x) * (1 if move_right else -1) > -16.0
            enemy_above = nearest_enemy.y < self.player.y - 50.0
            if enemy_ahead and enemy_above:
                jump = True

        if self.player.on_ground and not jump:
            upcoming_platform = next(
                (
                    platform
                    for platform in self.platforms
                    if (platform.x - self.player.x) * (1 if move_right else -1) > 0.0
                    and abs(platform.x - self.player.x) < 120.0
                    and platform.y < self.player.y - 35.0
                ),
                None,
            )
            jump = upcoming_platform is not None

        attack = nearest_enemy is not None and abs(nearest_enemy.x - self.player.x) < (172.0 if nearest_enemy.template.boss else 145.0)
        pulse = self.player.pulse_ready() and nearest_enemy is not None and abs(nearest_enemy.x - self.player.x) < (360.0 if nearest_enemy.template.boss else 280.0)

        return InputState(
            left=not move_right,
            right=move_right,
            jump=jump,
            attack=attack,
            pulse=pulse,
            start=True,
        )

    def update(self, dt: float, input_state: InputState) -> None:
        self.time_s += dt
        self._update_presentation(dt)
        self._mark_room_visited()
        if self.banner_timer > 0.0:
            self.banner_timer = max(0.0, self.banner_timer - dt)

        if self.title_screen:
            if input_state.start:
                self.audio.play_sound("menu_start")
                self.title_screen = False
                self.announce("Blunin enters BluninKrabVania. Hunt every krab, worm, and latent boss form.")
            return

        if self.hitstop_timer > 0.0:
            return

        self._update_player(dt, input_state)
        self._update_collectibles()
        self._update_enemies(dt)
        self._update_projectiles(dt)
        self._update_gates()
        self._update_room_messages()
        if self.smoke_test:
            self._update_smoke_assist(dt)
        self.camera_x = max(0.0, min(self.player.x - (SCREEN_WIDTH * 0.42), WORLD_WIDTH - SCREEN_WIDTH))

    def _update_room_messages(self) -> None:
        room = self.current_room()
        if room.name != self.section_message_room:
            self.section_message_room = room.name
            self.announce(room.name, 2.0)

    def _update_player(self, dt: float, input_state: InputState) -> None:
        move_axis = float(input_state.right) - float(input_state.left)
        self.player.vx = move_axis * PLAYER_MOVE_SPEED
        if move_axis > 0.0:
            self.player.facing = 1
        elif move_axis < 0.0:
            self.player.facing = -1

        if input_state.jump and self.player.on_ground:
            self.player.vy = -PLAYER_JUMP_SPEED
            self.player.on_ground = False
        if input_state.attack:
            was_attacking = self.player.attack_timer > 0.0
            self.player.start_attack()
            if not was_attacking and self.player.attack_timer > 0.0:
                self.audio.play_sound("attack")
        if input_state.pulse and self.player.pulse_ready():
            speed = 520.0 * self.player.facing
            self.projectiles.append(
                Projectile(
                    x=self.player.x + (58.0 * self.player.facing),
                    y=self.player.y - 64.0,
                    vx=speed,
                    vy=0.0,
                    owner="player",
                    damage=PULSE_DAMAGE,
                    friendly=True,
                    animation_key="probe_attack",
                )
            )
            self.player.pulse_cooldown = PULSE_COOLDOWN
            self.audio.play_sound("pulse")

        self.player.attack_cooldown = max(0.0, self.player.attack_cooldown - dt)
        self.player.attack_timer = max(0.0, self.player.attack_timer - dt)
        self.player.pulse_cooldown = max(0.0, self.player.pulse_cooldown - dt)
        self.player.invulnerable_timer = max(0.0, self.player.invulnerable_timer - dt)

        self.player.vy += GRAVITY * dt
        self.player.x += self.player.vx * dt
        self._apply_gate_pushback(self.player)
        self.player.x = max(48.0, min(WORLD_WIDTH - 48.0, self.player.x))

        previous_bottom = self.player.rect.bottom
        self.player.y += self.player.vy * dt
        self.player.on_ground = False
        player_rect = self.player.rect
        for platform in self.platforms:
            if player_rect.colliderect(platform.rect) and previous_bottom <= platform.rect.top + 18 and self.player.vy >= 0.0:
                self.player.y = platform.rect.top
                self.player.vy = 0.0
                self.player.on_ground = True
                self.player.last_safe_x = self.player.x
                self.player.last_safe_y = self.player.y
                player_rect = self.player.rect

        if self.player.y > SCREEN_HEIGHT + 120:
            self.player.y = self.player.last_safe_y
            self.player.x = self.player.last_safe_x
            self.player.vy = 0.0

        if self.player.attack_timer > 0.18:
            attack_rect = self.player.attack_rect()
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if enemy.invulnerable_timer > 0.0:
                    continue
                enemy_id = id(enemy)
                if enemy_id in self.player.attack_hit_ids:
                    continue
                if attack_rect.colliderect(enemy.body_rect()):
                    damage = PLAYER_BOSS_DAMAGE if enemy.template.boss else PLAYER_ATTACK_DAMAGE
                    self._damage_enemy(enemy, damage)
                    self.player.attack_hit_ids.add(enemy_id)

        self.player.anim_time += dt * (1.0 if abs(self.player.vx) < 2.0 else 1.5)

    def _apply_gate_pushback(self, player: Player) -> None:
        rect = player.rect
        for gate in self.gates:
            blocked = player.relic_count < gate.required_relics or (gate.requires_boss and not player.boss_defeated)
            if blocked and rect.colliderect(gate.rect):
                if player.vx > 0.0:
                    player.x = gate.rect.left - (player.width * 0.5) - 2.0
                elif player.vx < 0.0:
                    player.x = gate.rect.right + (player.width * 0.5) + 2.0
                if self.banner_timer <= 0.1:
                    self.announce(gate.label)
                rect = player.rect

    def _update_collectibles(self) -> None:
        player_rect = self.player.rect
        for collectible in self.collectibles:
            if collectible.collected:
                continue
            if player_rect.colliderect(collectible.rect(self.assets)):
                collectible.collected = True
                self.player.relic_count += 1
                self.audio.play_sound("collect")
                self._spawn_impact(collectible.x, collectible.y, (255, 226, 158), False, f"RELIC {self.player.relic_count}")
                if self.player.relic_count >= 3 and not self.player.companion_unlocked:
                    self.player.companion_unlocked = True
                    self.announce("Probe companion online. Press K for a pulse shot.")
                else:
                    self.announce(f"Skull relic {self.player.relic_count}/5 secured.")

    def _update_enemies(self, dt: float) -> None:
        player_rect = self.player.rect
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            enemy.anim_time += dt * (1.0 if enemy.state == "idle" else 1.5)
            enemy.attack_cooldown = max(0.0, enemy.attack_cooldown - dt)
            enemy.attack_timer = max(0.0, enemy.attack_timer - dt)
            enemy.damage_timer = max(0.0, enemy.damage_timer - dt)
            enemy.invulnerable_timer = max(0.0, enemy.invulnerable_timer - dt)
            enemy.phase_timer = max(0.0, enemy.phase_timer - dt)

            if enemy.template.boss and enemy.phase == 1 and enemy.hp <= math.ceil(enemy.template.hp * BOSS_PHASE_TWO_RATIO):
                enemy.phase = 2
                enemy.phase_timer = 0.9
                self.audio.play_sound("boss_phase")
                self.announce("Ghost Maw enters phase two.", 2.8)
                self._spawn_impact(enemy.x, enemy.y - 128.0, (214, 160, 255), True, "PHASE TWO")

            dx = self.player.x - enemy.x
            same_band = abs(dx) < enemy.template.aggro_range
            speed_multiplier = 1.35 if enemy.phase >= 2 else 1.0
            if enemy.template.flying:
                enemy.y += math.sin(self.time_s * (1.2 + enemy.float_phase) + enemy.float_phase) * 18.0 * dt
                if same_band:
                    enemy.vx = math.copysign(enemy.template.speed * speed_multiplier, dx)
                else:
                    if enemy.x <= enemy.patrol_left:
                        enemy.facing = 1
                    elif enemy.x >= enemy.patrol_right:
                        enemy.facing = -1
                    enemy.vx = enemy.facing * enemy.template.speed * 0.6 * speed_multiplier
                enemy.x += enemy.vx * dt
            else:
                if same_band:
                    enemy.vx = math.copysign(enemy.template.speed * speed_multiplier, dx)
                else:
                    if enemy.x <= enemy.patrol_left:
                        enemy.facing = 1
                    elif enemy.x >= enemy.patrol_right:
                        enemy.facing = -1
                    enemy.vx = enemy.facing * enemy.template.speed * 0.6 * speed_multiplier
                enemy.x += enemy.vx * dt
                enemy.vy += GRAVITY * dt
                enemy.y += enemy.vy * dt
                for platform in self.platforms:
                    if enemy.body_rect().colliderect(platform.rect) and enemy.vy >= 0.0:
                        enemy.y = platform.rect.top
                        enemy.vy = 0.0
                        break

            enemy.facing = 1 if enemy.vx >= 0.0 else -1

            attack_range = enemy.template.attack_range * (1.12 if enemy.phase >= 2 else 1.0)
            if abs(dx) < attack_range and enemy.attack_cooldown <= 0.0:
                enemy.state = "attack"
                enemy.attack_timer = 0.42 if not enemy.template.boss else (0.84 if enemy.phase >= 2 else 0.72)
                enemy.attack_cooldown = 1.1 if not enemy.template.boss else (1.0 if enemy.phase >= 2 else 1.6)
                enemy.hit_registered = False
                self.audio.play_sound(f"enemy_attack_{enemy_audio_family(enemy.template.key)}")
                if enemy.template.projectile_key:
                    speed = math.copysign(310.0 if not enemy.template.boss else (470.0 if enemy.phase >= 2 else 400.0), dx)
                    self.projectiles.append(
                        Projectile(
                            x=enemy.x + (40.0 * enemy.facing),
                            y=enemy.y - 80.0,
                            vx=speed,
                            vy=0.0,
                            owner=enemy.template.key,
                            damage=enemy.template.damage,
                            friendly=False,
                            animation_key=enemy.template.projectile_key,
                            ttl=1.15 if enemy.template.boss else 0.8,
                        )
                    )
                    if enemy.template.boss and enemy.phase >= 2:
                        self.projectiles.append(
                            Projectile(
                                x=enemy.x + (40.0 * enemy.facing),
                                y=enemy.y - 118.0,
                                vx=speed,
                                vy=86.0,
                                owner=enemy.template.key,
                                damage=enemy.template.damage,
                                friendly=False,
                                animation_key=enemy.template.projectile_key,
                                ttl=1.25,
                            )
                        )
            elif enemy.damage_timer > 0.0:
                enemy.state = "damage"
            elif abs(enemy.vx) > 20.0:
                enemy.state = "walk"
            else:
                enemy.state = "idle"

            if enemy.attack_timer > 0.18 and not enemy.hit_registered and enemy.attack_rect().colliderect(player_rect):
                self._handle_player_hit(enemy.template.damage)
                enemy.hit_registered = True

    def _update_projectiles(self, dt: float) -> None:
        survivors: list[Projectile] = []
        player_rect = self.player.rect
        for projectile in self.projectiles:
            projectile.x += projectile.vx * dt
            projectile.y += projectile.vy * dt
            projectile.ttl -= dt
            projectile.anim_time += dt
            if projectile.ttl <= 0.0:
                continue
            if projectile.friendly:
                hit = False
                for enemy in self.enemies:
                    if not enemy.alive or enemy.invulnerable_timer > 0.0:
                        continue
                    if projectile.rect(self.assets).colliderect(enemy.body_rect()):
                        self._damage_enemy(enemy, projectile.damage)
                        hit = True
                        break
                if hit:
                    continue
            else:
                if projectile.rect(self.assets).colliderect(player_rect):
                    self._handle_player_hit(projectile.damage)
                    continue
            if projectile.x < -120.0 or projectile.x > WORLD_WIDTH + 120.0:
                continue
            survivors.append(projectile)
        self.projectiles = survivors

    def _update_gates(self) -> None:
        if self.player.relic_count >= 5 and self.player.x > 5100.0 and self.player.boss_defeated:
            self.victory = True

    def draw(self) -> None:
        if self.title_screen:
            self._draw_title()
            return

        room = self.current_room()
        base_camera_x = self.camera_x
        self.camera_x = max(0.0, min(WORLD_WIDTH - SCREEN_WIDTH, self.camera_x + self.shake_offset))
        draw_gradient(self.screen, room.top_color, room.bottom_color)
        for key, scroll_factor, y_offset in room.layers:
            background = self.assets.backgrounds[key]
            scroll_value = self.camera_x * scroll_factor
            y_pos = SCREEN_HEIGHT - background.get_height() + y_offset
            blit_tiled_x(self.screen, background, scroll_value, y_pos, 255)

        self._draw_room_ambient(room)
        for platform in self.platforms:
            draw_platform(self.screen, self.camera_x, platform, self.assets.backgrounds["squaretilebg"])

        self._draw_collectibles()
        self._draw_gates()
        self._draw_enemies()
        self._draw_projectiles()
        self._draw_player()
        self._draw_companion()
        self._draw_impacts()
        self._draw_floating_texts()
        self._draw_hud(room)
        self.camera_x = base_camera_x

    def _draw_title(self) -> None:
        draw_gradient(self.screen, (18, 18, 28), (46, 26, 34))
        bg1 = self.assets.backgrounds["blunin_bg_layer_1"]
        bg2 = self.assets.backgrounds["krabkombatbg"]
        blit_tiled_x(self.screen, bg1, self.time_s * 28.0, SCREEN_HEIGHT - bg1.get_height(), 200)
        blit_tiled_x(self.screen, bg2, self.time_s * 18.0, SCREEN_HEIGHT - bg2.get_height() + 60, 180)
        title = self.font.render("BluninKrabVania", True, (244, 235, 219))
        subtitle = self.small_font.render("Final deliverable wrapper over the validated Blunin and Krab combat slice.", True, (210, 205, 200))
        controls = self.small_font.render("Move: A/D or arrows   Jump: Space   Attack: J   Pulse: K after relic 3", True, (232, 220, 186))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 150)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 194)))
        self.screen.blit(controls, controls.get_rect(center=(SCREEN_WIDTH // 2, 228)))
        menu_icon = self.assets.ui["menu_icon"]
        play_button = self.assets.ui["play_button"]
        self.screen.blit(menu_icon, menu_icon.get_rect(center=(SCREEN_WIDTH // 2 - 60, 300)))
        self.screen.blit(play_button, play_button.get_rect(center=(SCREEN_WIDTH // 2 + 60, 300)))
        press = self.font.render("Press Enter or Space", True, (255, 196, 108))
        self.screen.blit(press, press.get_rect(center=(SCREEN_WIDTH // 2, 372)))

        montage_keys = ["inchworm", "krab_raider", "shell_hopper", "ghostling", "sludgelord", "ghost_maw"]
        for index, key in enumerate(montage_keys):
            surface = frame_at_time(self.assets.sprite_sets[key].idle, self.time_s + index * 0.2, 10.0)
            x_pos = 170 + index * 170
            rect = surface.get_rect(midbottom=(x_pos, 620))
            self.screen.blit(surface, rect)

    def _draw_room_ambient(self, room: RoomTheme) -> None:
        for ambient in room.ambient:
            asset = self.assets.ambient.get(ambient.key) or self.assets.sprite_sets[ambient.key].idle
            if isinstance(asset, list):
                sprite = frame_at_time(asset, self.time_s, 8.0)
            else:
                sprite = asset
            sprite = sprite.copy()
            sprite.set_alpha(ambient.alpha)
            bob = math.sin(self.time_s * ambient.bob_speed + ambient.world_x * 0.001) * ambient.bob_amp
            screen_x = int(ambient.world_x - self.camera_x * (1.0 - ambient.parallax))
            rect = sprite.get_rect(midbottom=(screen_x, int(ambient.y + bob)))
            self.screen.blit(sprite, rect)

        if room.name == "Latent Mire Bastion":
            apparition = frame_at_time(self.assets.sprite_sets["libertykong_apparition"].idle, self.time_s * 0.6, 18.0).copy()
            apparition.set_alpha(92)
            rect = apparition.get_rect(midbottom=(int(1040 - self.camera_x * 0.02), 520))
            self.screen.blit(apparition, rect)

    def _draw_collectibles(self) -> None:
        for collectible in self.collectibles:
            if collectible.collected:
                continue
            surface = self.assets.relics[collectible.sprite_index]
            bob = math.sin(self.time_s * 3.0 + collectible.sprite_index) * 10.0
            rect = surface.get_rect(center=(int(collectible.x - self.camera_x), int(collectible.y + bob)))
            self.screen.blit(surface, rect)

    def _draw_gates(self) -> None:
        runtime_idol = self.assets.ambient["libertykong_runtime"]
        for gate in self.gates:
            rect = gate.rect.move(-int(self.camera_x), 0)
            blocked = self.player.relic_count < gate.required_relics or (gate.requires_boss and not self.player.boss_defeated)
            color = (214, 90, 94) if blocked else (90, 216, 150)
            pygame.draw.rect(self.screen, color, rect, border_radius=12)
            pygame.draw.rect(self.screen, (245, 244, 240), rect, 3, border_radius=12)
            if gate.requires_boss:
                idol_rect = runtime_idol.get_rect(midbottom=(rect.centerx, rect.top + 18))
                self.screen.blit(runtime_idol, idol_rect)
            label = self.small_font.render(str(gate.required_relics), True, (18, 18, 18))
            self.screen.blit(label, label.get_rect(center=(rect.centerx, rect.centery)))

    def _draw_sprite(self, surface: pygame.Surface, world_x: float, world_y: float, facing: int) -> None:
        sprite = pygame.transform.flip(surface, facing < 0, False)
        rect = sprite.get_rect(midbottom=(int(world_x - self.camera_x), int(world_y)))
        self.screen.blit(sprite, rect)

    def _draw_player(self) -> None:
        frames = self.assets.sprite_sets["blunin"].frames_for(self.player.current_state())
        fps_scale = 28.0 if self.player.current_state() == "attack" else 10.0
        frame = frame_at_time(frames, self.player.anim_time, fps_scale)
        if self.player.invulnerable_timer > 0.0 and int(self.player.invulnerable_timer * 20.0) % 2 == 0:
            frame = frame.copy()
            frame.set_alpha(128)
        self._draw_sprite(frame, self.player.x, self.player.y + 8.0, self.player.facing)

    def _draw_companion(self) -> None:
        if not self.player.companion_unlocked:
            return
        hover_x = self.player.x - (42.0 * self.player.facing)
        hover_y = self.player.y - 110.0 + math.sin(self.time_s * 4.0) * 10.0
        frames = self.assets.sprite_sets["probe_companion"].frames_for("walk")
        frame = frame_at_time(frames, self.time_s, 12.0)
        self._draw_sprite(frame, hover_x, hover_y, self.player.facing)

    def _draw_enemies(self) -> None:
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            sprite_set = self.assets.sprite_sets[enemy.template.sprite_key]
            fps_scale = 20.0 if enemy.state == "attack" else 10.0
            frame = frame_at_time(sprite_set.frames_for(enemy.state), enemy.anim_time, fps_scale)
            if enemy.damage_timer > 0.0:
                frame = frame.copy()
                frame.fill((255, 90, 90, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self._draw_sprite(frame, enemy.x, enemy.y + (0.0 if enemy.template.flying else 8.0), enemy.facing)
            if enemy.template.boss:
                bar_rect = pygame.Rect(int(enemy.x - self.camera_x - 80), int(enemy.y - 210), 160, 12)
                pygame.draw.rect(self.screen, (28, 20, 24), bar_rect, border_radius=6)
                fill_width = int(bar_rect.width * (enemy.hp / enemy.template.hp))
                pygame.draw.rect(self.screen, (224, 82, 112), (bar_rect.x, bar_rect.y, fill_width, bar_rect.height), border_radius=6)
                pygame.draw.rect(self.screen, (245, 240, 234), bar_rect, 2, border_radius=6)

    def _draw_projectiles(self) -> None:
        for projectile in self.projectiles:
            frames = self.assets.fx[projectile.animation_key]
            frame = frame_at_time(frames, projectile.anim_time, 16.0)
            if projectile.vx < 0.0:
                frame = pygame.transform.flip(frame, True, False)
            rect = frame.get_rect(center=(int(projectile.x - self.camera_x), int(projectile.y)))
            self.screen.blit(frame, rect)

    def _draw_impacts(self) -> None:
        for flash in self.impact_flashes:
            progress = 1.0 - (flash.ttl / flash.duration)
            radius = flash.radius + ((flash.max_radius - flash.radius) * progress)
            alpha = int(180 * (flash.ttl / flash.duration))
            diameter = int(radius * 2) + 8
            surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*flash.color, alpha), (diameter // 2, diameter // 2), int(radius), width=4)
            rect = surface.get_rect(center=(int(flash.x - self.camera_x), int(flash.y)))
            self.screen.blit(surface, rect)

    def _draw_floating_texts(self) -> None:
        for floating_text in self.floating_texts:
            alpha = max(0, min(255, int(255 * min(1.0, floating_text.ttl / 0.75))))
            text_surface = self.small_font.render(floating_text.text, True, floating_text.color)
            text_surface.set_alpha(alpha)
            rect = text_surface.get_rect(center=(int(floating_text.x - self.camera_x), int(floating_text.y)))
            self.screen.blit(text_surface, rect)

    def _draw_hud(self, room: RoomTheme) -> None:
        panel = pygame.Rect(16, 16, 520, 110)
        hud = pygame.Surface(panel.size, pygame.SRCALPHA)
        hud.fill((8, 12, 18, 190))
        self.screen.blit(hud, panel)
        pygame.draw.rect(self.screen, (240, 238, 230), panel, 2, border_radius=12)
        title = self.font.render(room.name, True, (244, 236, 210))
        self.screen.blit(title, (34, 26))
        status = self.small_font.render(f"Relics: {self.player.relic_count}/5   Defeated: {self.enemy_defeat_count}   Companion: {'online' if self.player.companion_unlocked else 'offline'}", True, (218, 214, 206))
        self.screen.blit(status, (34, 58))
        objective = "Defeat Ghost Maw" if not self.player.boss_defeated else "Vania clear. Reach the exit gate."
        objective_surface = self.small_font.render(objective, True, (255, 196, 108))
        self.screen.blit(objective_surface, (34, 82))

        heart_frames = self.assets.ui["hearts"]
        for index in range(self.player.max_health):
            frame = heart_frames[0 if index < self.player.health else 2]
            self.screen.blit(frame, (560 + index * 42, 26))

        icon = self.assets.ui["menu_icon"]
        self.screen.blit(icon, (1090, 20))
        hint = self.small_font.render("J: slash   K: probe pulse", True, (243, 236, 228))
        self.screen.blit(hint, (930, 86))

        if self.banner_timer > 0.0 and self.banner_text:
            banner = pygame.Rect(170, SCREEN_HEIGHT - 80, 940, 46)
            banner_surface = pygame.Surface(banner.size, pygame.SRCALPHA)
            banner_surface.fill((20, 16, 20, 188))
            self.screen.blit(banner_surface, banner)
            pygame.draw.rect(self.screen, (250, 216, 156), banner, 2, border_radius=10)
            text_surface = self.small_font.render(self.banner_text, True, (250, 245, 236))
            self.screen.blit(text_surface, text_surface.get_rect(center=banner.center))

        if self.victory:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 12, 18, 120))
            self.screen.blit(overlay, (0, 0))
            victory_text = self.font.render("BluninKrabVania Clear", True, (255, 218, 130))
            subtext = self.small_font.render("Blunin cleared the krab chain and the latent bastion.", True, (245, 238, 232))
            self.screen.blit(victory_text, victory_text.get_rect(center=(SCREEN_WIDTH // 2, 200)))
            self.screen.blit(subtext, subtext.get_rect(center=(SCREEN_WIDTH // 2, 236)))

    def run(self, max_frames: int | None = None) -> dict[str, object]:
        running = True
        frame_counter = 0
        while running:
            dt = (1.0 / FPS) if self.smoke_test else (self.clock.tick(FPS) / 1000.0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            input_state = self.handle_input()
            if input_state.back and not self.smoke_test:
                running = False
            self.update(dt, input_state)
            self.draw()
            pygame.display.flip()

            frame_counter += 1
            if max_frames is not None and frame_counter >= max_frames:
                running = False
        return self.summary(frame_counter)

    def save_smoke_outputs(self, basename: str, summary: dict[str, object]) -> dict[str, str]:
        preview_path = self.prototype_root / f"{basename}.png"
        summary_path = self.prototype_root / f"{basename}.json"
        outputs = {"preview": str(preview_path), "summary": str(summary_path)}
        summary_payload = dict(summary)
        summary_payload["smoke_outputs"] = outputs
        pygame.image.save(self.screen, str(preview_path))
        summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
        return outputs

    def summary(self, frame_counter: int) -> dict[str, object]:
        return {
            "frames": frame_counter,
            "player": {
                "x": round(self.player.x, 2),
                "y": round(self.player.y, 2),
                "health": self.player.health,
                "relics": self.player.relic_count,
                "companion_unlocked": self.player.companion_unlocked,
                "boss_defeated": self.player.boss_defeated,
            },
            "defeated_enemies": self.enemy_defeat_count,
            "victory": self.victory,
            "rooms": [room.name for room in self.rooms],
            "visited_rooms": self.visited_rooms,
            "loaded_asset_count": len(self.assets.asset_paths),
            "loaded_assets": {key: str(path) for key, path in sorted(self.assets.asset_paths.items())},
        }


def run_smoke_test(frames: int, basename: str) -> dict[str, object]:
    game = Game(smoke_test=True)
    summary = game.run(max_frames=frames)
    outputs = game.save_smoke_outputs(basename, summary)
    summary["smoke_outputs"] = outputs
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Playable BluninKrabVania runtime.")
    parser.add_argument("--smoke-test", action="store_true", help="Run headless-ish automated frames and export a preview image plus JSON summary.")
    parser.add_argument("--frames", type=int, default=SMOKE_TEST_FRAMES, help="Frame count for smoke-test mode.")
    parser.add_argument("--output-basename", default="smoke_test_preview", help="Basename for smoke-test output files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.smoke_test:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    random.seed(7)
    pygame.init()
    try:
        if args.smoke_test:
            summary = run_smoke_test(args.frames, args.output_basename)
            print(json.dumps(summary, indent=2))
        else:
            summary = Game(smoke_test=False).run()
            print(json.dumps(summary, indent=2))
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()