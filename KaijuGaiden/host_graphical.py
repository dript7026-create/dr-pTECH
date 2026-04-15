#!/usr/bin/env python3
"""
host_graphical.py

Lightweight graphical host for Kaiju Gaiden prototype using only Tkinter
and the provided placeholder PPM assets. Draws a scaled GBA-like viewport,
places the player, a few minions and nanocell icons, and shows the genetics
HUD. This avoids external dependencies and uses the existing assets folder.
"""
import os
import time
import math
import random
import json
import traceback
try:
    from gb_runtime_assets import load_gb_base_assets, build_runtime_bundle
except Exception:
    load_gb_base_assets = None
    build_runtime_bundle = None
try:
    import pygame
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False
import tkinter as tk
import tkinter.font as tkfont
import ctypes
from ctypes import wintypes
import types
import threading
import subprocess
try:
    from PIL import Image, ImageTk, ImageFilter, ImageOps, ImageEnhance
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False
try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    cv2 = None
    CV2_AVAILABLE = False
try:
    import winsound
except Exception:
    winsound = None

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
RUNTIME_ERROR_LOG = os.path.join(os.path.dirname(__file__), 'runtime_error.log')
RENDER_AUDIT_LOG = os.path.join(os.path.dirname(__file__), 'render_audit.log')
PLACEHOLDER_DIR = os.path.join(ASSETS_DIR, 'placeholderassets')

# asset filenames (prefer PNGs in placeholderassets)
ASSET_FILES = {
    'title': 'KaijuGaiden_placeholderasset_titlescreen_0001.png',
    'player': 'KaijuGaiden_placeholderasset_Rei_0001.png',
    'minion1': 'KaijuGaiden_placeholderasset_minion_0001.png',
    'minion2': 'KaijuGaiden_placeholderasset_minion_0002.png',
    'minion3': 'KaijuGaiden_placeholderasset_minion_0003.png',
    'nanocell1': 'KaijuGaiden_placeholderasset_nanocell_0001.png',
    'nanocell2': 'KaijuGaiden_placeholderasset_nanocell_0002.png',
    'boss': 'KaijuGaiden_placeholderasset_boss_0001.png',
    'attackfx1': 'KaijuGaiden_placeholderasset_attackfx_0001.png',
    'attackfx2': 'KaijuGaiden_placeholderasset_attackfx_0002.png',
    'blodfx': 'KaijuGaiden_placeholderasset_blodfx_0001.png',
    'background': 'KaijuGaiden_placeholderasset_background_0001.png',
}

GBA_W, GBA_H = 240, 160
TARGET_W, TARGET_H = 1680, 1020
SCALE = 6
WIN_W, WIN_H = TARGET_W, TARGET_H
SCENE_W, SCENE_H = GBA_W * SCALE, GBA_H * SCALE
VIEWPORT_X = (WIN_W - SCENE_W) // 2
VIEWPORT_Y = (WIN_H - SCENE_H) // 2
GBA_ROM_PATH = os.path.join(os.path.dirname(__file__), 'kaijugaiden.gba')
GBA_ROM_SIZE_BYTES = os.path.getsize(GBA_ROM_PATH) if os.path.exists(GBA_ROM_PATH) else (128 * 1024 * 1024)
HOST_RENDER_CACHE_LIMIT = max(24, min(96, GBA_ROM_SIZE_BYTES // (2 * 1024 * 1024)))

ATTACK_TOTAL_MS = 240
ATTACK_ACTIVE_MS = 110
ATTACK_BUFFER_MS = 150
DODGE_BUFFER_MS = 130
DODGE_MS = 190
DODGE_FLASH_MS = 240
DODGE_STEP_PX = 22
HIT_STUN_MS = 320
COMBO_WINDOW_MS = 340
BEAT_PERIOD_MS = 520
PERFECT_WINDOW_MS = 72
BOSS_PHASE_STUN_MS = 850
BOSS_HIT_STUN_MS = 320
BOSS_INTRO_LOCK_MS = 780
BOSS_FIRST_STRIKE_MS = 1500
PLAYER_ATTACK_FRONT_PX = 32
PLAYER_ATTACK_REAR_PX = 10
MINION_ATTACK_RANGE_PX = 18

STEREO_PROFILE_PATHS = (
    os.path.join(os.path.dirname(__file__), '3ds', 'ndsx_adaptive_profile.json'),
    os.path.join(os.path.dirname(__file__), 'ndsx_profile.json'),
)

HOPE_CONTRACT_PATHS = (
    os.path.join(os.path.dirname(__file__), 'runtime', 'hope_runtime_contract.json'),
    os.path.join(os.path.dirname(__file__), 'hope_runtime_contract.json'),
)

DEPTH_PRESET_HINTS = {
    'studio-balanced': {
        'base_strength': 0.68,
        'center_pull': 0.22,
        'target_brightness': 0.48,
        'target_proximity': 0.42,
        'floor': 0.08,
        'ceiling': 0.82,
    },
    'bright-floor-demo': {
        'base_strength': 0.82,
        'center_pull': 0.28,
        'target_brightness': 0.66,
        'target_proximity': 0.36,
        'floor': 0.10,
        'ceiling': 0.94,
    },
    'low-strain-mono': {
        'base_strength': 0.10,
        'center_pull': 0.04,
        'target_brightness': 0.46,
        'target_proximity': 0.40,
        'floor': 0.00,
        'ceiling': 0.12,
    },
}

STAGE_LIBRARY = {
    'marsh_shore': {
        'id': 'marsh_shore',
        'display_name': 'Marsh Shore',
        'subtitle': 'Brine pylons, reef carcasses, and tide-soaked shacks',
        'width': 840,
        'horizon_y': 54,
        'ground_y': 118,
        'sky_top': '#29444d',
        'sky_mid': '#52757c',
        'sky_low': '#8ea49a',
        'fog_color': '#b9d7c9',
        'ground_color': '#45523d',
        'surface_color': '#60766c',
        'accent': '#7fe7ff',
        'ink': '#0d1b23',
        'detail_ink': '#13242c',
        'water_color': '#516c72',
        'water_glow': '#a8d7d6',
        'hud_glow': '#dff8ff',
        'frame_glow': '#f2d35a',
        'wall_color': '#55665b',
        'wear_color': '#2f3b34',
        'roof_color': '#31443d',
        'roof_shadow': '#1e2924',
        'parallax': {'far': 0.18, 'mid': 0.46, 'near': 0.82},
        'spawn_lanes': [70, 90, 112],
        'speed_mul': 0.92,
    },
    'city_outskirts': {
        'id': 'city_outskirts',
        'display_name': 'City Outskirts',
        'subtitle': 'Signal towers, warehouses, and skyline pressure',
        'width': 980,
        'horizon_y': 48,
        'ground_y': 122,
        'sky_top': '#20283a',
        'sky_mid': '#48526d',
        'sky_low': '#8a6e64',
        'fog_color': '#c8b8ad',
        'ground_color': '#32343c',
        'surface_color': '#555760',
        'accent': '#ffd36e',
        'ink': '#121722',
        'detail_ink': '#1b2030',
        'wall_color': '#686259',
        'wear_color': '#2b2a2f',
        'roof_color': '#5d443f',
        'roof_shadow': '#372724',
        'sidewalk_color': '#8e8782',
        'sidewalk_edge': '#615d5c',
        'asphalt_color': '#2b2c31',
        'lane_color': '#c0ad74',
        'grit_color': '#80756f',
        'parallax': {'far': 0.16, 'mid': 0.42, 'near': 0.86},
        'spawn_lanes': [80, 96, 112],
        'speed_mul': 1.0,
    },
    'inner_city': {
        'id': 'inner_city',
        'display_name': 'Inner City',
        'subtitle': 'Climb routes, block canyons, and stacked fire escapes',
        'width': 1120,
        'horizon_y': 42,
        'ground_y': 128,
        'sky_top': '#171d2c',
        'sky_mid': '#373c4f',
        'sky_low': '#66505d',
        'fog_color': '#b8a0ab',
        'ground_color': '#2d2f36',
        'surface_color': '#43454f',
        'accent': '#ff7b63',
        'ink': '#090c12',
        'detail_ink': '#141824',
        'wall_color': '#58505f',
        'wear_color': '#23242c',
        'roof_color': '#4b3944',
        'roof_shadow': '#2a1f28',
        'sidewalk_color': '#76727c',
        'sidewalk_edge': '#4c4b54',
        'asphalt_color': '#25262d',
        'lane_color': '#d3b26f',
        'grit_color': '#8e7b79',
        'parallax': {'far': 0.14, 'mid': 0.40, 'near': 0.88},
        'spawn_lanes': [52, 78, 104, 124],
        'speed_mul': 1.04,
    },
}

VISUAL_SEED_PROFILES = (
    {
        'id': 'cathedral_spire',
        'label': 'Cathedral Spire',
        'tagline': 'Ritual pressure climbing a vertical nave',
        'accent_shift': '#d7c27a',
        'shadow_shift': '#261b22',
        'wall_shift': '#746a60',
        'tracery_bias': 0.88,
        'arch_bias': 0.82,
        'wear_bias': 0.56,
        'layout_seed': 17,
        'motif': 'spire',
        'ui_panel_fill': '#081019',
        'ui_panel_line': '#d7c27a',
        'ui_panel_glow': '#7ac1d5',
        'ui_trim': '#8f7347',
        'ui_text': '#f7ecd0',
        'ui_muted': '#aab6c2',
        'burst_fill': '#5d120c',
        'burst_outline': '#f2d35a',
        'metric_primary': '#f3dfa1',
        'metric_secondary': '#7fd9e8',
        'metric_warning': '#ff8d72',
        'panel_notch': 24,
        'panel_ribs': 7,
        'meter_segments': 12,
    },
    {
        'id': 'gargoyle_cloister',
        'label': 'Gargoyle Cloister',
        'tagline': 'Stone-claw pressure and predatory sidewind',
        'accent_shift': '#9dc5d4',
        'shadow_shift': '#1c202d',
        'wall_shift': '#5f6269',
        'tracery_bias': 0.72,
        'arch_bias': 0.67,
        'wear_bias': 0.74,
        'layout_seed': 41,
        'motif': 'fang',
        'ui_panel_fill': '#0a1118',
        'ui_panel_line': '#9dc5d4',
        'ui_panel_glow': '#f0b67d',
        'ui_trim': '#5a7388',
        'ui_text': '#e6f3f7',
        'ui_muted': '#98a9b8',
        'burst_fill': '#1a222d',
        'burst_outline': '#9dc5d4',
        'metric_primary': '#b9dae1',
        'metric_secondary': '#f0b67d',
        'metric_warning': '#ff7f6b',
        'panel_notch': 16,
        'panel_ribs': 5,
        'meter_segments': 10,
    },
    {
        'id': 'rose_transept',
        'label': 'Rose Transept',
        'tagline': 'Circular liturgy, stained heat, blooming impact',
        'accent_shift': '#d38f78',
        'shadow_shift': '#28181a',
        'wall_shift': '#7a665e',
        'tracery_bias': 0.94,
        'arch_bias': 0.78,
        'wear_bias': 0.63,
        'layout_seed': 73,
        'motif': 'rose',
        'ui_panel_fill': '#131019',
        'ui_panel_line': '#d38f78',
        'ui_panel_glow': '#f2d35a',
        'ui_trim': '#8d5b58',
        'ui_text': '#fff0df',
        'ui_muted': '#c8afb0',
        'burst_fill': '#6b1f15',
        'burst_outline': '#d38f78',
        'metric_primary': '#f4c89d',
        'metric_secondary': '#f2d35a',
        'metric_warning': '#ff7b63',
        'panel_notch': 28,
        'panel_ribs': 9,
        'meter_segments': 14,
    },
)


def _hex_to_rgb(value):
    value = value.lstrip('#')
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _rgb_to_hex(rgb):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(channel))) for channel in rgb)


def blend_hex(base, target, amount):
    base_rgb = _hex_to_rgb(base)
    target_rgb = _hex_to_rgb(target)
    return _rgb_to_hex(tuple(base_rgb[index] + ((target_rgb[index] - base_rgb[index]) * amount) for index in range(3)))


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def load_json_from_paths(paths):
    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                return json.load(handle)
        except Exception:
            continue
    return {}


def load_stereo_profile():
    profile = load_json_from_paths(STEREO_PROFILE_PATHS)
    return profile if isinstance(profile, dict) else {}


def load_hope_contract():
    profile = load_json_from_paths(HOPE_CONTRACT_PATHS)
    return profile if isinstance(profile, dict) else {}


class HopeDepthBridge:
    def __init__(self):
        self.available = False
        self.status = 'native bridge unavailable'
        self.dll = None
        self._strength = None
        self._project_x = None
        self._project_y = None
        self._strength_uses_bridge = False
        search_paths = (
            os.path.join(os.path.dirname(__file__), 'build', 'asm', 'hope_depth_core.dll'),
            os.path.join(os.path.dirname(__file__), 'hope_depth_core.dll'),
        )
        for candidate in search_paths:
            if not os.path.exists(candidate):
                continue
            try:
                dll = ctypes.CDLL(candidate)
                strength_bridge = getattr(dll, 'hope_depth_strength_bridge', None)
                strength_raw = getattr(dll, 'hope_depth_strength_i32', None)
                project_x_bridge = getattr(dll, 'hope_depth_project_x_bridge', None)
                project_x_raw = getattr(dll, 'hope_depth_project_x_i32', None)
                project_y_bridge = getattr(dll, 'hope_depth_project_y_bridge', None)
                project_y_raw = getattr(dll, 'hope_depth_project_y_i32', None)
                strength = strength_bridge or strength_raw
                project_x = project_x_bridge or project_x_raw
                project_y = project_y_bridge or project_y_raw
                if strength is None or project_x is None:
                    continue
                if strength_bridge is not None:
                    strength.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
                    self._strength_uses_bridge = True
                else:
                    strength.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
                strength.restype = ctypes.c_int
                project_x.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
                project_x.restype = ctypes.c_int
                if project_y is not None:
                    project_y.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
                    project_y.restype = ctypes.c_int
                self.dll = dll
                self._strength = strength
                self._project_x = project_x
                self._project_y = project_y
                self.available = True
                self.status = f'native bridge loaded: {os.path.basename(candidate)}'
                break
            except Exception:
                continue

    def strength(self, brightness, proximity, eye_open, motion, preset_bias=0):
        if not self.available:
            return None
        try:
            if self._strength_uses_bridge:
                return int(self._strength(int(brightness), int(proximity), int(eye_open), int(motion)))
            return int(self._strength(int(brightness), int(proximity), int(eye_open), int(motion), int(preset_bias)))
        except Exception:
            self.available = False
            self.status = 'native bridge faulted'
            return None

    def project_x(self, x, scene_center, band_depth, strength, focus_px):
        if not self.available:
            return None
        try:
            return int(self._project_x(int(x), int(scene_center), int(band_depth), int(strength), int(focus_px)))
        except Exception:
            self.available = False
            self.status = 'native bridge faulted'
            return None

    def project_y(self, y, scene_center, band_depth, strength, focus_px):
        if not self.available or self._project_y is None:
            return None
        try:
            return int(self._project_y(int(y), int(scene_center), int(band_depth), int(strength), int(focus_px)))
        except Exception:
            self.available = False
            self.status = 'native bridge faulted'
            return None


def stylize_comic_asset(image):
    if not PIL_AVAILABLE or image is None:
        return image
    rgba = image.convert('RGBA')
    alpha = rgba.getchannel('A')
    rgb = rgba.convert('RGB')
    rgb = ImageEnhance.Color(rgb).enhance(1.18)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.22)
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.35)
    rgb = ImageOps.posterize(rgb, 4)
    edge_map = rgb.filter(ImageFilter.FIND_EDGES).convert('L')
    edge_map = ImageOps.autocontrast(edge_map)
    edge_mask = edge_map.point(lambda value: 255 if value > 48 else 0)
    ink = Image.new('RGBA', rgba.size, (18, 14, 20, 255))
    stylized = Image.composite(ink, rgba, edge_mask)
    halftone = Image.new('RGBA', rgba.size, (0, 0, 0, 0))
    halftone_pixels = halftone.load()
    for y in range(0, rgba.height, 6):
        for x in range(0, rgba.width, 6):
            if ((x // 6) + (y // 6)) % 2 == 0:
                for dy in range(2):
                    for dx in range(2):
                        px = x + dx
                        py = y + dy
                        if px < rgba.width and py < rgba.height:
                            halftone_pixels[px, py] = (255, 255, 255, 18)
    stylized = Image.blend(stylized, Image.alpha_composite(stylized, halftone), 0.22)
    stylized.putalpha(alpha)
    return stylized


class CameraFedDepthProcessor:
    def __init__(self):
        self.available = CV2_AVAILABLE
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.metrics = {
            'status': 'camera package unavailable' if not CV2_AVAILABLE else 'camera idle',
            'brightness': 0.50,
            'face_ratio': 0.0,
            'proximity': 0.35,
            'space_open': 0.50,
            'eye_open': 0.50,
            'dilation': 0.50,
            'confidence': 0.0,
            'face_offset_x': 0.0,
            'face_offset_y': 0.0,
            'edge_density': 0.0,
            'available': CV2_AVAILABLE,
            'camera_live': False,
        }
        self.face_cascade = None
        self.eye_cascade = None
        if not CV2_AVAILABLE:
            self.available = False
            return
        try:
            self.face_cascade = cv2.CascadeClassifier(
                os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
            )
            self.eye_cascade = cv2.CascadeClassifier(
                os.path.join(cv2.data.haarcascades, 'haarcascade_eye_tree_eyeglasses.xml')
            )
            if self.face_cascade.empty() or self.eye_cascade.empty():
                self.available = False
                self.metrics['status'] = 'camera cascades unavailable'
        except Exception:
            self.available = False
            self.metrics['status'] = 'camera cascade init failed'

    def start(self):
        if not self.available or self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        thread = self.thread
        self.thread = None
        if thread and thread.is_alive():
            thread.join(timeout=1.0)

    def sample(self):
        with self.lock:
            return dict(self.metrics)

    def _set_metrics(self, **updates):
        with self.lock:
            self.metrics.update(updates)

    def _run(self):
        capture = None
        try:
            if hasattr(cv2, 'CAP_DSHOW'):
                capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if capture is None or not capture.isOpened():
                capture = cv2.VideoCapture(0)
            if capture is None or not capture.isOpened():
                self._set_metrics(status='camera unavailable', camera_live=False, confidence=0.0)
                return
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            self._set_metrics(status='camera live', camera_live=True)
            while self.running:
                ok, frame = capture.read()
                if not ok or frame is None:
                    self._set_metrics(status='camera read stalled', camera_live=False, confidence=0.0)
                    time.sleep(0.1)
                    continue
                self._set_metrics(**self._analyze_frame(frame), camera_live=True)
                time.sleep(0.06)
        finally:
            if capture is not None:
                capture.release()
            self._set_metrics(camera_live=False)

    def _analyze_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_h, frame_w = gray.shape[:2]
        brightness = float(gray.mean()) / 255.0
        edges = cv2.Canny(gray, 48, 128)
        edge_density = float(edges.mean()) / 255.0
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(56, 56))
        metrics = {
            'status': 'camera live / scanning',
            'brightness': brightness,
            'face_ratio': 0.0,
            'proximity': 0.20,
            'space_open': clamp(0.75 - edge_density * 0.35, 0.0, 1.0),
            'eye_open': 0.45,
            'dilation': clamp((0.62 - brightness) * 1.4, 0.0, 1.0),
            'confidence': 0.12,
            'face_offset_x': 0.0,
            'face_offset_y': 0.0,
            'edge_density': edge_density,
            'available': self.available,
        }
        if len(faces) == 0:
            metrics['status'] = 'camera live / no face'
            return metrics
        x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
        face_ratio = float(w * h) / float(max(frame_w * frame_h, 1))
        proximity = clamp((face_ratio - 0.035) / 0.18, 0.0, 1.0)
        face_center_x = (x + (w * 0.5)) / float(frame_w)
        face_center_y = (y + (h * 0.5)) / float(frame_h)
        face_offset_x = clamp((face_center_x - 0.5) * 2.0, -1.0, 1.0)
        face_offset_y = clamp((face_center_y - 0.5) * 2.0, -1.0, 1.0)
        space_open = clamp(1.0 - face_ratio * 2.5 - edge_density * 0.25, 0.0, 1.0)
        face_roi = gray[y:y + h, x:x + w]
        eyes = self.eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=4, minSize=(16, 12))
        eye_open = 0.45
        dilation = clamp((0.60 - brightness) * 1.3, 0.0, 1.0)
        if len(eyes) > 0:
            eye_open_values = []
            dilation_values = []
            sorted_eyes = sorted(eyes, key=lambda eye: eye[2] * eye[3], reverse=True)[:2]
            for ex, ey, ew, eh in sorted_eyes:
                eye_roi = face_roi[ey:ey + eh, ex:ex + ew]
                if eye_roi.size == 0:
                    continue
                eye_open_values.append(clamp((float(eh) / float(max(ew, 1))) * 3.0, 0.0, 1.0))
                pupil_roi = eye_roi[eh // 4:(eh * 3) // 4 or eh, ew // 6:(ew * 5) // 6 or ew]
                if pupil_roi.size == 0:
                    pupil_roi = eye_roi
                blurred = cv2.GaussianBlur(pupil_roi, (5, 5), 0)
                _, pupil_mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                dark_ratio = float(pupil_mask.mean()) / 255.0
                dilation_values.append(clamp((dark_ratio - 0.12) / 0.36, 0.0, 1.0))
            if eye_open_values:
                eye_open = sum(eye_open_values) / len(eye_open_values)
            if dilation_values:
                dilation = sum(dilation_values) / len(dilation_values)
        confidence = clamp(0.30 + face_ratio * 2.4 + len(eyes) * 0.12 + eye_open * 0.10, 0.0, 1.0)
        metrics.update({
            'status': 'camera live / face tracked',
            'face_ratio': face_ratio,
            'proximity': proximity,
            'space_open': space_open,
            'eye_open': eye_open,
            'dilation': dilation,
            'confidence': confidence,
            'face_offset_x': face_offset_x,
            'face_offset_y': face_offset_y,
        })
        return metrics


class Entity:
    def __init__(self, x=0, y=0, color='red'):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.hp = 100
        self.max_hp = 100
        self.color = color
        self.growth_tier = 0
        self.variant = 0
        self.state = 'idle'
        self.sprite = None
        self.attack_cooldown = 0
        self.ai_timer = 0
        self.size = (12, 12)


class Game:
    def __init__(self, root):
        self.root = root
        root.title('Kaiju Gaiden - Graphical Host')
        self.root.report_callback_exception = self._report_callback_exception
        self.canvas = tk.Canvas(root, width=WIN_W, height=WIN_H, bg='black')
        self.canvas.pack()
        try:
            self.canvas.focus_set()
            self.root.focus_force()
        except Exception:
            pass
        try:
            root.attributes('-fullscreen', False)
            root.geometry(f'{WIN_W}x{WIN_H}+40+20')
            root.resizable(False, False)
        except Exception:
            pass
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self.viewport_x = VIEWPORT_X
        self.viewport_y = VIEWPORT_Y
        self.scene_w = SCENE_W
        self.scene_h = SCENE_H
        self.playthrough_seed = int(time.time() * 1000) & 0xFFFFFFFF
        families = set(tkfont.families(root))
        self.font_display_family = self._pick_font_family(families, ['Terminal', 'Fixedsys', 'Small Fonts', 'Courier New'])
        self.font_body_family = self._pick_font_family(families, ['Terminal', 'Fixedsys', 'Small Fonts', 'Courier New'])
        self.font_caption_family = self._pick_font_family(families, ['Terminal', 'Fixedsys', 'Small Fonts', 'Courier New'])
        self.visual_profile = self._select_visual_profile()

        self.stereo_profile = load_stereo_profile()
        self.hope_contract = load_hope_contract()
        self.depth_presets = self._build_depth_presets()
        stereo_defaults = self.stereo_profile.get('adaptiveStereo3D', {})
        self.depth_preset_name = stereo_defaults.get('startupPreset', 'studio-balanced')
        if self.depth_preset_name not in self.depth_presets:
            self.depth_preset_name = 'studio-balanced'
        self.depth_enabled = True
        self.depth_sensor = CameraFedDepthProcessor()
        self.depth_sensor.start()
        self.depth_bridge = HopeDepthBridge()
        self.depth_metrics = self.depth_sensor.sample()
        self.depth_state = {
            'strength': 0.0,
            'band_pull': {'far': 0.0, 'near': 0.0, 'entity': 0.0, 'fx': 0.0},
            'focus_bias_x': 0.0,
            'focus_bias_y': 0.0,
            'comfort': 1.0,
            'status': 'depth standby',
            'native': self.depth_bridge.available,
        }

        self.assets = {}
        self.assets_pil = {}
        self.scaled = {}
        self.render_cache = {}
        self.asset_bbox = {}
        self.gb_base_assets = {}
        self.runtime_sprite_signature = None
        self.sprite_refresh_timer = 0
        self.audio_ambient_timer = 900
        self.audio_telegraph_latch = 0
        self.last_error = None
        self.render_audit_written = False
        self._load_placeholder_assets()
        if PIL_AVAILABLE and load_gb_base_assets is not None:
            self.gb_base_assets = load_gb_base_assets(os.path.join(ASSETS_DIR, 'gb'))
        self._sync_asset_refs()
        self._refresh_asset_bbox()

        # game state / entities
        self.state = 'splash'  # splash, cinematic, title, stage_intro, playing, cypher, grade, paused, vn
        self.player = Entity(60, 80, color='cyan')
        # facing for projectile placement
        self.player.facing = 'right'
        self.player.attack_cooldown = 0
        self.player.nanocell_count = 0
        self.player.combo_count = 0
        self.player.combo_timer = 0
        self.player.beat_timer = 0
        self.player.dodge_timer = 0
        self.player.hit_stun = 0
        self.player.attack_buffer = 0
        self.player.dodge_buffer = 0
        self.player.nanocell_boost_timer = 0
        self.player.beat_perfect = False
        self.player.dodge_read_total = 0
        self.player.attack_power = 14
        self.player.attack_pose_timer = 0
        self.player.dodge_flash_timer = 0
        self.player.flow_feint_timer = 0
        self.player.rupture_drive_timer = 0
        self.player.motion_energy = 0.0
        self.player.attack_resolved = False
        self.minions = []
        self.nanocells = []
        self.boss = None
        self.wave = 0
        self.score = 0
        # projectiles created by attacks (immobile 'projectile' placed at forward edge)
        self.projectiles = []
        # camera and world dimensions (use background width if present)
        self.camera_x = 0
        self.world_width = GBA_W
        self.parity_mode = True
        self.central_build = 'harbor_fidelity'
        self.stage_id = 'city_outskirts'
        self.stage_profile = dict(STAGE_LIBRARY[self.stage_id])
        self.stage_cycle = self._build_stage_cycle()
        self.preboss_waves = max(1, len(self.stage_cycle) - 1)
        self.stage_layers = {'far': [], 'mid': [], 'near': []}
        self.stage_obstacles = []
        self.stage_climb_routes = []
        self.stage_spawn_lanes = list(self.stage_profile.get('spawn_lanes', [72, 96, 116]))
        self.stage_intro_timer = 0
        self.stage_clear_timer = 0
        self.splash_timer = 1800
        self.cinematic_duration = 2600
        self.cinematic_timer = self.cinematic_duration
        self.cypher_timer = 0
        self.grade_timer = 0
        self.banner_text = ''
        self.banner_timer = 0
        self.boss_name = self._profile_boss_name()
        self.boss_phase_hp = [120, 100, 80]
        self.grade_summary = 'STYLE PRESSURE: 0  PRECISION: 0  ADAPTATION: 0'
        bg = self.assets.get('background')
        if bg:
            try:
                bw = bg.width()
                self.world_width = max(self.world_width, bw)
            except Exception:
                pass
        self._set_stage(self.stage_id)
        if self.gb_base_assets:
            self._refresh_runtime_sprite_assets(force=True)

        # keyboard state
        self.keys = set()
        root.bind_all('<KeyPress>', self.on_key)
        root.bind_all('<KeyRelease>', self.on_key_release)
        # move debug toggle off 'd' (conflicted) to F1
        root.bind('<F1>', self._toggle_debug)
        root.bind('<F3>', self._toggle_depth)
        root.bind('<F4>', self._cycle_depth_preset)
        root.bind('<F5>', self._toggle_depth_sensor)
        root.bind('<F6>', self._dump_render_audit)

        # XInput dynamic loader for Xbox controller support
        self.xinput = None
        self._load_xinput()

        # menu state for title
        self.menu_options = ['Start Game', 'Controls', 'Quit']
        self.menu_index = 0
        self.menu_focus_float = 0.0
        self.menu_nav_cooldown = 0

        # controls popup state
        self.controls_win = None
        self.controls_page = 0
        # in-canvas tutorial overlay (blocks gameplay until closed)
        self.tutorial_open = False
        self.controls_pages = [
            "Xbox Controller:\n\nLeft Stick / DPad: Move\nA: Primary Attack\nB: Dodge / Back\nX: NanoCell Surge\nY / RB / RT: Rupture Drive\nLB / LT: Feather Step\nStart: Pause\nBack/View: Close Tutorial",
            "Combat Tips:\n\nChain A into a 3-hit combo.\nUse B only on telegraphed pressure.\nFeather Step repositions and keeps you fluid.\nRupture Drive commits forward and extends pressure.",
            "Buttons:\n\nLeft / Right: Title panels and tutorial pages\nA / Start: Confirm\nB / Back / Escape: Cancel or close tutorial",
            "Adaptive Depth:\n\nF3 toggles HOPE adaptive depth.\nF4 cycles 3DS preset vocabulary.\nF5 toggles the camera-fed processor.\nThe single-screen inward depth illusion reacts to lighting, face proximity, eye state, and HOPE runtime bias."
        ]
        # previous keyboard state for edge detection
        self.prev_keys = set()
        # previous gamepad state for edge detection
        self.prev_gp = {}
        # debug overlay
        self.show_debug = False
        # show computed PIL alpha bboxes for visual verification
        self.show_bboxes = False
        root.bind('<F2>', lambda e: self._toggle_bboxes())
        self.debug_text_id = None
        # background scroll
        self.bg_x = 0.0
        # scaled background cache
        self.scaled_bg = None
        if self.img_title:
            try:
                self.scaled_bg = self.img_title.zoom(SCALE, SCALE)
            except Exception:
                self.scaled_bg = None

        # active attack effects: list of (x,y,sprite,timer)
        self.effects = []

        # HUD text
        self.hud_text = self.canvas.create_text(8, 8, anchor='nw', fill='white', font=self._font_body(10), text='')

        # schedule loop
        self.last = time.time()
        self.running = True
        self.loop()

    def _crop(self, img, x, y, w, h):
        """Crop a PhotoImage (returns new PhotoImage)."""
        out = tk.PhotoImage(width=w, height=h)
        # use tk.call to copy region
        out.tk.call(out, 'copy', img, '-from', x, y, x + w - 1, y + h - 1, '-to', 0, 0)
        return out

    def _present_xy(self, x, y):
        return int(self.viewport_x + x), int(self.viewport_y + y)

    def _present_rect(self, x0, y0, x1, y1):
        px0, py0 = self._present_xy(x0, y0)
        px1, py1 = self._present_xy(x1, y1)
        return px0, py0, px1, py1

    def _scene_safe_rect(self):
        inset_left = 84
        inset_top = 96
        inset_right = 84
        inset_bottom = 78
        return (
            inset_left,
            inset_top,
            self.scene_w - inset_right,
            self.scene_h - inset_bottom,
        )

    def _window_safe_rect(self):
        x0, y0, x1, y1 = self._scene_safe_rect()
        return self._present_rect(x0, y0, x1, y1)

    def _pick_font_family(self, families, preferred):
        for family in preferred:
            if family in families:
                return family
        return 'Arial'

    def _select_visual_profile(self):
        index = self.playthrough_seed % len(VISUAL_SEED_PROFILES)
        return dict(VISUAL_SEED_PROFILES[index])

    def _apply_visual_profile(self, base_profile):
        profile = dict(base_profile)
        seed_profile = self.visual_profile
        profile['accent'] = blend_hex(profile.get('accent', '#7fe7ff'), seed_profile['accent_shift'], 0.48)
        profile['ink'] = blend_hex(profile.get('ink', '#121722'), seed_profile['shadow_shift'], 0.60)
        profile['detail_ink'] = blend_hex(profile.get('detail_ink', profile.get('ink', '#121722')), seed_profile['shadow_shift'], 0.44)
        profile['wall_color'] = blend_hex(profile.get('wall_color', profile.get('surface_color', '#606060')), seed_profile['wall_shift'], 0.50)
        profile['wear_color'] = blend_hex(profile.get('wear_color', profile.get('ink', '#121722')), seed_profile['shadow_shift'], 0.35 + seed_profile['wear_bias'] * 0.25)
        profile['roof_color'] = blend_hex(profile.get('roof_color', profile.get('surface_color', '#606060')), seed_profile['shadow_shift'], 0.24)
        profile['roof_shadow'] = blend_hex(profile.get('roof_shadow', profile.get('ink', '#121722')), seed_profile['shadow_shift'], 0.65)
        profile['hud_glow'] = blend_hex(profile.get('hud_glow', '#dff8ff'), seed_profile['accent_shift'], 0.28)
        profile['frame_glow'] = blend_hex(profile.get('frame_glow', '#f2d35a'), seed_profile['accent_shift'], 0.22)
        profile['tracery_bias'] = seed_profile['tracery_bias']
        profile['arch_bias'] = seed_profile['arch_bias']
        profile['wear_bias'] = seed_profile['wear_bias']
        profile['layout_seed'] = seed_profile['layout_seed']
        profile['profile_label'] = seed_profile['label']
        profile['profile_tagline'] = seed_profile['tagline']
        profile['profile_motif'] = seed_profile['motif']
        profile['ui_panel_fill'] = seed_profile['ui_panel_fill']
        profile['ui_panel_line'] = blend_hex(seed_profile['ui_panel_line'], profile['accent'], 0.20)
        profile['ui_panel_glow'] = blend_hex(seed_profile['ui_panel_glow'], profile['frame_glow'], 0.35)
        profile['ui_trim'] = seed_profile['ui_trim']
        profile['ui_text'] = seed_profile['ui_text']
        profile['ui_muted'] = seed_profile['ui_muted']
        profile['burst_fill'] = seed_profile['burst_fill']
        profile['burst_outline'] = blend_hex(seed_profile['burst_outline'], profile['frame_glow'], 0.35)
        profile['metric_primary'] = seed_profile['metric_primary']
        profile['metric_secondary'] = seed_profile['metric_secondary']
        profile['metric_warning'] = seed_profile['metric_warning']
        profile['panel_notch'] = seed_profile['panel_notch']
        profile['panel_ribs'] = seed_profile['panel_ribs']
        profile['meter_segments'] = seed_profile['meter_segments']
        return profile

    def _build_stage_cycle(self):
        profile_id = self.visual_profile.get('id', 'cathedral_spire')
        if profile_id == 'gargoyle_cloister':
            return ['marsh_shore', 'city_outskirts', 'inner_city']
        if profile_id == 'rose_transept':
            return ['city_outskirts', 'marsh_shore', 'inner_city']
        return ['city_outskirts', 'inner_city', 'marsh_shore']

    def _profile_boss_name(self):
        names = {
            'cathedral_spire': 'NAVE LEVIATHAN',
            'gargoyle_cloister': 'CLOISTER DEVOURER',
            'rose_transept': 'TRANSEPT BLOOM',
        }
        return names.get(self.visual_profile.get('id', 'cathedral_spire'), 'HARBOR LEVIATHAN')

    def _font_display(self, size, weight='normal'):
        return (self.font_display_family, size, weight)

    def _font_body(self, size, weight='normal'):
        return (self.font_body_family, size, weight)

    def _font_caption(self, size, weight='normal'):
        return (self.font_caption_family, size, weight)

    def _write_runtime_error(self, summary, detail):
        try:
            with open(RUNTIME_ERROR_LOG, 'a', encoding='utf-8') as handle:
                handle.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {summary}\n')
                handle.write(detail.rstrip() + '\n\n')
        except Exception:
            pass

    def _report_callback_exception(self, exc, val, tb):
        detail = ''.join(traceback.format_exception(exc, val, tb))
        self.last_error = detail
        self._write_runtime_error('Tk callback exception', detail)
        self.running = False
        try:
            self.draw()
        except Exception:
            pass

    def _draw_runtime_error(self):
        detail = self.last_error or 'Unknown runtime failure.'
        summary = detail.strip().splitlines()[-1] if detail.strip() else 'Unknown runtime failure.'
        self.canvas.create_rectangle(0, 0, WIN_W, WIN_H, fill='#12080b', outline='')
        self.canvas.create_rectangle(self.viewport_x + 100, self.viewport_y + 120, self.viewport_x + self.scene_w - 100, self.viewport_y + self.scene_h - 120, fill='#1d0d12', outline='#ff8a6b', width=3)
        self.canvas.create_text(WIN_W // 2, self.viewport_y + 178, text='RUNTIME INTERRUPTION', fill='#f6d4c6', font=self._font_display(28, 'bold'))
        self.canvas.create_text(WIN_W // 2, self.viewport_y + 232, text=summary, fill='#ffb7a0', font=self._font_body(15, 'bold'), width=self.scene_w - 280)
        self.canvas.create_text(WIN_W // 2, self.viewport_y + 316, text='The failure was written to runtime_error.log in the KaijuGaiden folder.', fill='#d8dbe6', font=self._font_caption(14), width=self.scene_w - 280)
        self.canvas.create_text(WIN_W // 2, self.viewport_y + 430, text=detail[-1600:], fill='#fff4f0', font=self._font_caption(11), width=self.scene_w - 260)

    def _write_render_audit(self, lines):
        try:
            with open(RENDER_AUDIT_LOG, 'a', encoding='utf-8') as handle:
                handle.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] render audit\n')
                for line in lines:
                    handle.write(line.rstrip() + '\n')
                handle.write('\n')
        except Exception:
            pass

    def _audit_entity_render(self, label, world_x, world_y, width, height, band='entity'):
        scene_x = (world_x - int(self.camera_x)) * SCALE
        scene_y = world_y * SCALE
        projected_x, projected_y = self._depth_project_point(scene_x, scene_y, band)
        window_x, window_y = self._present_xy(projected_x, projected_y)
        safe_x0, safe_y0, safe_x1, safe_y1 = self._window_safe_rect()
        center_x = window_x + (width // 2)
        center_y = window_y + (height // 2)
        inside_safe = safe_x0 <= center_x <= safe_x1 and safe_y0 <= center_y <= safe_y1
        return (
            f'{label}: world=({world_x:.2f},{world_y:.2f}) '
            f'scene=({scene_x:.2f},{scene_y:.2f}) '
            f'projected=({projected_x},{projected_y}) '
            f'window=({window_x},{window_y}) size=({width},{height}) '
            f'center=({center_x},{center_y}) inside_safe={inside_safe}'
        )

    def _dump_render_audit(self, ev=None):
        lines = [
            f'state={self.state} parity_mode={self.parity_mode} scale={SCALE}',
            f'window_rect=(0,0,{WIN_W},{WIN_H})',
            f'viewport_rect=({self.viewport_x},{self.viewport_y},{self.viewport_x + self.scene_w},{self.viewport_y + self.scene_h})',
            f'scene_rect=(0,0,{self.scene_w},{self.scene_h})',
            f'safe_scene_rect={self._scene_safe_rect()}',
            f'safe_window_rect={self._window_safe_rect()}',
            f'camera_x={self.camera_x:.2f} player_facing={getattr(self.player, "facing", "right")}',
            self._audit_entity_render('player', self.player.x, self.player.y, 12 * SCALE, 12 * SCALE),
        ]
        if self.boss:
            lines.append(self._audit_entity_render('boss', self.boss.x, self.boss.y, 64 * SCALE, 64 * SCALE))
        for index, minion in enumerate(self.minions[:4]):
            lines.append(self._audit_entity_render(f'minion_{index}', minion.x, minion.y, 12 * SCALE, 12 * SCALE))
        self._write_render_audit(lines)
        self.render_audit_written = True

    def _duel_balance(self):
        player_ratio = max(0.0, min(1.0, self.player.hp / max(1, self.player.max_hp)))
        boss_ratio = self._boss_hp_ratio() if self.boss else 0.25
        combo_weight = min(0.22, self.player.combo_count * 0.05)
        boost_weight = 0.12 if self.player.nanocell_boost_timer > 0 else 0.0
        player_force = max(0.08, min(0.92, (player_ratio * 0.62) + combo_weight + boost_weight))
        if self.boss:
            boss_force = max(0.08, min(0.92, boss_ratio * 0.80 + (0.06 * self._boss_phase_index())))
        else:
            boss_force = 0.22
        total = max(0.01, player_force + boss_force)
        return player_force / total, boss_force / total

    def on_key(self, ev):
        key = ev.keysym.lower()
        first_press = key not in self.keys
        self.keys.add(key)
        if not first_press:
            return
        if key == 'space' and self.state == 'playing':
            self._on_select()
        elif key == 'x' and self.state == 'playing':
            self._use_nanocell()
        elif key == 'q':
            self._press_lb(True)
        elif key == 'e':
            self._press_rb(True)
        elif key == 'v':
            self.on_vn()
        elif key == 'p':
            self.on_pause()
        elif key == 'c':
            self.on_toggle_controls()

    def on_key_release(self, ev):
        k = ev.keysym.lower()
        if k in self.keys:
            self.keys.remove(k)
        if k == 'q':
            self._press_lb(False)
        elif k == 'e':
            self._press_rb(False)

    def update(self, dt):
        speed = 72 * self._movement_speed_multiplier() * (dt / 1000.0)  # tuned closer to the original duel pace
        if getattr(self, 'menu_nav_cooldown', 0) > 0:
            self.menu_nav_cooldown = max(0, self.menu_nav_cooldown - dt)
        self.menu_focus_float += (self.menu_index - getattr(self, 'menu_focus_float', float(self.menu_index))) * min(1.0, dt / 90.0)
        # poll controller and merge into keys/actions with edge detection
        gp = self._poll_gamepad()
        if self.state == 'splash':
            if 'return' in self.keys or 'space' in self.keys or (gp and (gp.get('a') or gp.get('b') or gp.get('start'))):
                self.state = 'cinematic'
                self.cinematic_timer = self.cinematic_duration
            self.prev_gp = gp
            self.prev_keys = set(self.keys)
            return
        if self.state == 'cinematic':
            if 'x' in self.keys or 'space' in self.keys or (gp and (gp.get('b') or gp.get('back') or gp.get('start'))):
                self.state = 'title'
            self.prev_gp = gp
            self.prev_keys = set(self.keys)
            return
        # handle menu navigation when on title
        if self.state == 'title':
            prev = self.prev_gp or {}
            if getattr(self, 'tutorial_open', False):
                if gp:
                    if (gp.get('a') and not prev.get('a')) or (gp.get('dpad_right') and not prev.get('dpad_right')) or (gp.get('rx', 0) > 12000 and not prev.get('rx', 0) > 12000):
                        self._controls_next()
                    if gp.get('dpad_left') and not prev.get('dpad_left'):
                        self._controls_prev()
                    if (gp.get('b') and not prev.get('b')) or (gp.get('back') and not prev.get('back')) or (gp.get('start') and not prev.get('start')):
                        self.on_toggle_controls()
                if 'right' in self.keys and 'right' not in self.prev_keys:
                    self._controls_next()
                if 'left' in self.keys and 'left' not in self.prev_keys:
                    self._controls_prev()
                if ('space' in self.keys and 'space' not in self.prev_keys) or ('return' in self.keys and 'return' not in self.prev_keys):
                    self.on_toggle_controls()
                self.prev_gp = gp
                self.prev_keys = set(self.keys)
                return
            any_start_key = any(key in self.keys for key in ('return', 'space', 'z', 'x'))
            nav_delta = 0
            if gp:
                lx = gp.get('lx', 0)
                if (gp.get('dpad_left') and not prev.get('dpad_left')) or (lx < -12000 and not prev.get('lx', 0) < -12000):
                    nav_delta = -1
                elif (gp.get('dpad_right') and not prev.get('dpad_right')) or (lx > 12000 and not prev.get('lx', 0) > 12000):
                    nav_delta = 1
                if (gp.get('a') and not prev.get('a')) or (gp.get('x') and not prev.get('x')) or (gp.get('start') and not prev.get('start')) or (gp.get('b') and not prev.get('b')):
                    self.on_start()
                if gp.get('back') and not prev.get('back'):
                    self.on_toggle_controls()
                rx = gp.get('rx',0)
                self.bg_x += (rx/32767.0) * (dt/16.0)
            if 'left' in self.keys and 'left' not in self.prev_keys:
                nav_delta = -1
            elif 'right' in self.keys and 'right' not in self.prev_keys:
                nav_delta = 1
            if nav_delta != 0 and getattr(self, 'menu_nav_cooldown', 0) <= 0:
                self._change_title_selection(nav_delta)
                self.menu_nav_cooldown = 140
            if any_start_key and not any(key in self.prev_keys for key in ('return', 'space', 'z', 'x')):
                self.on_start()
            self.prev_gp = gp
            self.prev_keys = set(self.keys)
            return
        if self.state == 'stage_intro':
            if self.stage_intro_timer <= 0:
                self.state = 'playing'
                if self.wave == 0 and len(self.minions) == 0 and self.boss is None:
                    self.start_wave()
            self.prev_gp = gp
            self.prev_keys = set(self.keys)
            return
        if self.state == 'cypher':
            self.prev_gp = gp
            self.prev_keys = set(self.keys)
            return
        if self.state == 'grade':
            if 'return' in self.keys or 'space' in self.keys or (gp and (gp.get('a') or gp.get('b') or gp.get('start'))):
                self.state = 'title'
                self._reset_combat_lane()
            self.prev_gp = gp
            self.prev_keys = set(self.keys)
            return
        # if tutorial overlay open, only allow navigation/close inputs and skip gameplay updates
        if getattr(self, 'tutorial_open', False):
            prev = self.prev_gp or {}
            if gp:
                # next page: A button, dpad_right, or right stick push
                if (gp.get('a') and not prev.get('a')) or (gp.get('dpad_right') and not prev.get('dpad_right')) or (gp.get('rx',0) > 12000 and not prev.get('rx',0) > 12000):
                    self._controls_next()
                # prev page: dpad_left
                if (gp.get('dpad_left') and not prev.get('dpad_left')):
                    self._controls_prev()
                # close: B or Back
                if (gp.get('b') and not prev.get('b')) or (gp.get('back') and not prev.get('back')):
                    self.on_toggle_controls()
            # keyboard navigation while tutorial open
            if 'right' in self.keys and 'right' not in self.prev_keys:
                self._controls_next()
            if 'left' in self.keys and 'left' not in self.prev_keys:
                self._controls_prev()
            if 'space' in self.keys and 'space' not in self.prev_keys or 'return' in self.keys and 'return' not in self.prev_keys:
                self.on_toggle_controls()
            self.prev_gp = gp
            self.prev_keys = set(self.keys)
            return
        if gp:
            lx = gp.get('lx', 0)
            ly = gp.get('ly', 0)
            dead = 8000
            if lx < -dead:
                self.keys.add('left')
            else:
                self.keys.discard('left')
            if lx > dead:
                self.keys.add('right')
            else:
                self.keys.discard('right')
            if ly < -dead:
                self.keys.add('up')
            else:
                self.keys.discard('up')
            if ly > dead:
                self.keys.add('down')
            else:
                self.keys.discard('down')
            # button edge detection: trigger on transition False->True
            prev = self.prev_gp or {}
            # if in-canvas tutorial open, allow Back/View or B to close it
            if getattr(self, 'tutorial_open', False):
                if gp.get('back') and not prev.get('back') or gp.get('b') and not prev.get('b'):
                    try:
                        self.on_toggle_controls()
                    except Exception:
                        pass
            # A = attack (or menu select handled above)
            if gp.get('a') and not prev.get('a'):
                if self.state == 'playing':
                    self.on_attack()
            # B = dodge
            if gp.get('b') and not prev.get('b'):
                if self.state == 'playing':
                    self._dodge()
            # X = primary attack for Rei (map to same as A)
            if gp.get('x') and not prev.get('x'):
                if self.state == 'playing':
                    self.on_attack()
            if gp.get('y') and not prev.get('y'):
                if self.state == 'playing':
                    self._special_r()
            # LB / RB map to specials
            if gp.get('lb') and not prev.get('lb'):
                self._press_lb(True)
            if not gp.get('lb') and prev.get('lb'):
                self._press_lb(False)
            if gp.get('rb') and not prev.get('rb'):
                self._press_rb(True)
            if not gp.get('rb') and prev.get('rb'):
                self._press_rb(False)
            if gp.get('lt', 0) > 180 and not prev.get('lt', 0) > 180:
                if self.state == 'playing':
                    self._special_l()
            if gp.get('rt', 0) > 180 and not prev.get('rt', 0) > 180:
                if self.state == 'playing':
                    self._special_r()
            # Start = pause/menu
            if gp.get('start') and not prev.get('start'):
                if self.state == 'title':
                    self.on_start()
                else:
                    self.on_pause()
        # remember gp state
        self.prev_gp = gp
        # controller movement -> keys mapping (leftstick + dpad)
        if gp:
            # left stick
            lx = gp.get('lx', 0)
            ly = gp.get('ly', 0)
            dead = 8000
            left_active = lx < -dead or gp.get('dpad_left')
            right_active = lx > dead or gp.get('dpad_right')
            up_active = ly < -dead or gp.get('dpad_up')
            down_active = ly > dead or gp.get('dpad_down')
            if left_active:
                self.keys.add('left')
            else:
                self.keys.discard('left')
            if right_active:
                self.keys.add('right')
            else:
                self.keys.discard('right')
            if up_active:
                self.keys.add('up')
            else:
                self.keys.discard('up')
            if down_active:
                self.keys.add('down')
            else:
                self.keys.discard('down')
            # right stick influences background parallax
            rx = gp.get('rx', 0)
            self.bg_x += (rx / 32767.0) * 2.0 * (dt/16.0)
        # keyboard edge detection (Z = attack)
        if 'z' in self.keys and 'z' not in self.prev_keys:
            self.on_attack()
        # save current keys for next tick
        self.prev_keys = set(self.keys)
        # keyboard uses arrow keys for movement; z/x map to action buttons
        old_x = self.player.x
        old_y = self.player.y
        if getattr(self.player, 'hit_stun', 0) <= 0:
            if 'left' in self.keys:
                self.player.x -= speed
                self.player.facing = 'left'
            if 'right' in self.keys:
                self.player.x += speed
                self.player.facing = 'right'
            if 'up' in self.keys:
                self.player.y -= speed
            if 'down' in self.keys:
                self.player.y += speed

        # clamp
        self.player.x = max(0, min((GBA_W - 8) if self.parity_mode else (self.world_width - 8), self.player.x))
        self.player.y = max(0, min(GBA_H - 8, self.player.y))
        self.player.x, self.player.y = self._resolve_stage_movement(old_x, old_y, self.player.x, self.player.y)
        self.player.x = max(0, min((GBA_W - 8) if self.parity_mode else (self.world_width - 8), self.player.x))
        self.player.y = max(0, min(GBA_H - 8, self.player.y))
        self.player.y = self._ground_contact_y(self.player.y)
        distance_moved = abs(self.player.x - old_x) + abs(self.player.y - old_y)
        speed_unit = max(1.0, speed * 1.6)
        self.player.motion_energy = max(0.0, min(1.0, distance_moved / speed_unit))

        if self.player.attack_buffer > 0 and self.player.attack_cooldown <= 0 and self.player.dodge_timer <= 0 and getattr(self.player, 'hit_stun', 0) <= 0:
            self.player.attack_cooldown = ATTACK_TOTAL_MS
            self.player.attack_pose_timer = ATTACK_TOTAL_MS
            self.player.attack_buffer = 0
            self.player.attack_resolved = False
        if self.player.dodge_buffer > 0 and getattr(self.player, 'hit_stun', 0) <= 0 and self.player.attack_cooldown <= 0:
            boss_threat = 0
            if self.boss and getattr(self.boss, 'windup_timer', 0) > 0:
                boss_threat = self._boss_attack_threat(getattr(self.boss, 'attack_kind', 'sweep'))
            self.player.dodge_timer = DODGE_MS
            self.player.dodge_flash_timer = DODGE_FLASH_MS
            self.player.state = 'dodge'
            move_dir = -DODGE_STEP_PX if getattr(self.player, 'facing', 'right') == 'right' else DODGE_STEP_PX
            self.player.x = max(0, min((GBA_W - 8) if self.parity_mode else (self.world_width - 8), self.player.x + move_dir))
            self.player.combo_timer = 0
            self.player.combo_count = 0
            self.player.dodge_buffer = 0
            if boss_threat >= 1:
                self.player.dodge_read_total = getattr(self.player, 'dodge_read_total', 0) + 1
            self._set_banner('A COUNTER NOW' if boss_threat >= 2 else 'DODGE CLEAN', 450)

        # background scroll
        self.bg_x = (self.bg_x + 12 * (dt/1000.0)) % GBA_W

        # update camera smoothly to follow player, allow small right-stick nudge
        if self.parity_mode:
            desired_cam = self._parity_camera_target()
            self.camera_x += (desired_cam - self.camera_x) * 0.16
            self.camera_x = max(-8, min(8, self.camera_x))
        else:
            lead = 26 if getattr(self.player, 'facing', 'right') == 'right' else -26
            if self.stage_id == 'inner_city':
                lead *= 1.35
            desired_cam = max(0, min(self.player.x + lead - (GBA_W // 2), max(0, self.world_width - GBA_W)))
            self.camera_x += (desired_cam - self.camera_x) * 0.12
            if gp:
                rx = gp.get('rx', 0)
                self.camera_x += (rx / 32767.0) * 6.0 * (dt/1000.0)
            self.camera_x = max(0, min(self.camera_x, max(0, self.world_width - GBA_W)))

        # simple minion AI: move left-right
        for m in list(self.minions):
            m.x += m.vx * (dt / 1000.0)
            if getattr(m, 'recover_timer', 0) > 0:
                m.recover_timer = max(0, m.recover_timer - dt)
            lane_y = getattr(m, 'lane_y', self.stage_spawn_lanes[m.variant % len(self.stage_spawn_lanes)])
            lane_y = self._ground_contact_y(lane_y)
            lane_sway = math.sin((time.time() * (1.8 + (m.variant * 0.17))) + getattr(m, 'lane_phase', 0.0)) * getattr(m, 'lane_amp', 0.0)
            target_y = lane_y + lane_sway
            if abs(m.y - target_y) > 1:
                lane_speed = 18 if self.parity_mode else 24
                m.y += math.copysign(min(lane_speed * (dt / 1000.0), abs(target_y - m.y)), target_y - m.y)
            m.y = self._ground_contact_y(m.y)
            # simple bounds and oscillation
            if m.x < 16 or m.x > self.world_width - 24:
                m.vx = -m.vx
            # minion attack AI: telegraph then attack
            m.ai_timer = max(0, getattr(m, 'ai_timer', 0) - dt)
            if not hasattr(m, 'tele'):
                m.tele = 0
            if m.tele > 0:
                m.tele = max(0, m.tele - dt)
                # telegraph effect (use attackfx2 as telegraph cue)
                if m.tele > 0 and int(m.tele) % 200 < 16:
                    tb = getattr(self, 's_img_attack2', None) or getattr(self, 'img_attack2', None)
                    if tb is not None:
                        self.effects.append((m.x, m.y - 6, tb, min(200, int(m.tele))))
                if m.tele == 0:
                    # perform attack
                    if self.player.dodge_timer <= 0 and getattr(self.player, 'hit_stun', 0) <= 0 and self._rects_overlap(m.x, m.y, 12, 12, self.player.x, self.player.y, 12, 12):
                        self.player.hp = max(0, self.player.hp - 12)
                        self.player.hit_stun = HIT_STUN_MS
                        m.recover_timer = 280
                        # blood + attackfx on player to cue damage
                        tb2 = getattr(self, 's_img_blodfx', None) or getattr(self, 's_img_attack2', None) or getattr(self, 'img_blodfx', None)
                        if tb2 is not None:
                            self.effects.append((self.player.x, self.player.y, tb2, 400))
            elif m.ai_timer <= 0 and getattr(m, 'recover_timer', 0) <= 0:
                # decide to telegraph an attack when player nearby
                dx = abs(self.player.x - m.x)
                dy = abs(self.player.y - m.y)
                if dx < 64 and dy < 30:
                    m.tele = 300
                    try:
                        self.play_sound('telegraph')
                    except Exception:
                        pass
                m.ai_timer = 1100 if self.stage_id == 'inner_city' else 1500
            # projectile collisions (player projectiles are immobile placed at forward edge)
            for p in list(self.projectiles):
                # projectiles use world coordinates
                if self._rects_overlap(p['x'], p['y'], p['w'], p['h'], m.x, m.y, getattr(m, 'size', (12,12))[0], getattr(m, 'size', (12,12))[1]):
                    # calculate precision-based damage
                    nowt = time.time()
                    delta = max(0.0, nowt - p.get('spawn_time', nowt))
                    ideal = 0.05
                    precision = max(0.0, 1.0 - min(abs(delta - ideal) / ideal, 1.0))
                    base = p.get('base_damage', 40)
                    damage = int(base * (0.7 + 0.6 * precision)) + random.randint(-5, 5)
                    m.hp -= max(1, damage)
                    # show projectile impact effect (use attackfx1) and blood overlay
                    img_fx = getattr(self, 's_img_attack', None) or getattr(self, 'img_attack', None)
                    if img_fx is not None:
                        self.effects.append((m.x, m.y, img_fx, 450))
                    bfx = getattr(self, 's_img_blodfx', None) or getattr(self, 'img_blodfx', None)
                    if bfx is not None:
                        self.effects.append((m.x, m.y - 4, bfx, 500))
                    try:
                        self.projectiles.remove(p)
                    except ValueError:
                        pass
                    if m.hp <= 0:
                        self.score += 40 + int(precision * 25)
                        self.spawn_nanocell(m.x, m.y)
                        try:
                            self.minions.remove(m)
                        except ValueError:
                            pass
                        try:
                            self.play_sound('minion_die')
                        except Exception:
                            pass
                        if m.hp <= 0:
                            self.spawn_nanocell(m.x, m.y)
                            try:
                                self.minions.remove(m)
                            except ValueError:
                                pass
                            # play death sound
                            try:
                                self.play_sound('minion_die')
                            except Exception:
                                pass

        # boss parity-leaning AI: intro lock, telegraph windup, resolve, recover
        if self.boss:
            distx = (self.player.x - self.boss.x)
            disty = (self.player.y - self.boss.y)
            if getattr(self.boss, 'intro_lock', 0) > 0:
                self.boss.intro_lock = max(0, self.boss.intro_lock - dt)
            elif getattr(self.boss, 'stun_timer', 0) > 0:
                self.boss.stun_timer = max(0, self.boss.stun_timer - dt)
                self.boss.telegraph = 0
            elif getattr(self.boss, 'recover_timer', 0) > 0:
                self.boss.recover_timer = max(0, self.boss.recover_timer - dt)
            elif getattr(self.boss, 'windup_timer', 0) > 0:
                self.boss.windup_timer = max(0, self.boss.windup_timer - dt)
                self.boss.telegraph = self.boss.windup_timer
                if self.boss.windup_timer == 0:
                    kind = getattr(self.boss, 'attack_kind', 'sweep')
                    distance = abs((self.boss.x + 24) - (self.player.x + 6))
                    if kind == 'tidal':
                        pull = 16 if self.boss.x > self.player.x else -16
                        self.player.x = max(0, min((GBA_W - 8) if self.parity_mode else (self.world_width - 8), self.player.x + pull))
                    if distance <= self._boss_attack_range(kind) and self.player.dodge_timer <= 0 and getattr(self.player, 'hit_stun', 0) <= 0:
                        self.player.hp = max(0, self.player.hp - self._boss_attack_damage(kind))
                        self.player.hit_stun = HIT_STUN_MS + (80 if kind == 'slam' else 0)
                        befx = getattr(self, 's_img_attack', None) or getattr(self, 'img_attack', None)
                        if befx is not None:
                            self.effects.append((self.player.x, self.player.y, befx, 600))
                        pb = getattr(self, 's_img_blodfx', None) or getattr(self, 'img_blodfx', None)
                        if pb is not None:
                            self.effects.append((self.player.x, self.player.y - 4, pb, 500))
                    self.boss.recover_timer = self._boss_attack_recover(kind)
                    self.boss.atk_timer = 460 if self._boss_phase_index() < 2 else 360
            else:
                boss_step = 14 if self._boss_phase_index() == 0 else 20
                if self.boss.x > self.player.x + 44:
                    self.boss.x -= boss_step * (dt / 1000.0)
                elif self.boss.x < self.player.x + 8:
                    self.boss.x += boss_step * (dt / 1000.0)
                self.boss.y += max(-8, min(8, disty * 0.12))
                self.boss.atk_timer = max(0, getattr(self.boss, 'atk_timer', 0) - dt)
                if self.boss.atk_timer <= 0:
                    self.boss.attack_kind = self._boss_attack_kind()
                    self.boss.windup_timer = self._boss_attack_windup(self.boss.attack_kind)
                    self.boss.telegraph = self.boss.windup_timer
                    boss_threat = self._boss_attack_threat(self.boss.attack_kind)
                    self._set_banner('CUT THE ANGLE' if boss_threat >= 2 else self._boss_attack_label(self.boss.attack_kind), 520)
                    try:
                        self.play_sound('telegraph')
                    except Exception:
                        pass
            if getattr(self.boss, 'first_strike_timer', 0) > 0:
                self.boss.first_strike_timer = max(0, self.boss.first_strike_timer - dt)
            if getattr(self.boss, 'telegraph', 0) > 0:
                tx = self.boss.x
                ty = self.boss.y - 8
                timg = getattr(self, 's_img_attack', None) or getattr(self, 'img_attack', None)
                if timg is None:
                    timg = getattr(self, 's_img_blodfx', None) or getattr(self, 'img_blodfx', None)
                if timg is not None:
                    self.effects.append((tx, ty, timg, int(self.boss.telegraph)))
            self.boss.phase = self._boss_phase_index() + 1
            self.boss.x = max(132, min(176, self.boss.x)) if self.parity_mode else max(24, min(self.world_width - 80, self.boss.x))
            self.boss.y = self._ground_contact_y(max(18, min(GBA_H - 72, self.boss.y)), sprite_h=64)
                

        # spawn waves when playing, then escalate into the boss arena
        if self.state == 'playing' and self.stage_clear_timer <= 0 and len(self.minions) == 0 and not getattr(self, 'tutorial_open', False):
            if self.wave >= self.preboss_waves and self.boss is None:
                self.spawn_boss()
            elif self.wave < self.preboss_waves:
                self.start_wave()

        # nanocell pickup and timers
        for nc in list(self.nanocells):
            nc.timer = max(0, getattr(nc, 'timer', 0) - dt)
            # pickup if overlapping player
            if self._rects_overlap(nc.x, nc.y, 8, 8, self.player.x, self.player.y, 12, 12):
                self.player.nanocell_count = getattr(self.player, 'nanocell_count', 0) + 1
                try:
                    self.play_sound('pickup')
                except Exception:
                    pass
                try:
                    self.nanocells.remove(nc)
                except ValueError:
                    pass
            elif nc.timer <= 0:
                try:
                    self.nanocells.remove(nc)
                except ValueError:
                    pass

    def draw(self):
        self.canvas.delete('all')
        if self.last_error:
            self._draw_runtime_error()
            return
        if self.state == 'playing' and not self.render_audit_written:
            self._dump_render_audit()
        self.canvas.create_rectangle(0, 0, WIN_W, WIN_H, fill='#0a0c14', outline='')
        if self.state == 'splash':
            self.canvas.create_rectangle(0, 0, WIN_W, WIN_H, fill='#081018', outline='')
            self._draw_splash_overlay()
            self.canvas.create_text(WIN_W // 2, WIN_H // 2 - 24, text='drIpTECH', fill='#f2d35a', font=self._font_display(34, 'bold'))
            self.canvas.create_text(WIN_W // 2, WIN_H // 2 + 18, text='Kaiju Gaiden', fill='white', font=self._font_display(22))
            self._draw_pixel_light_bloom(WIN_W // 2, WIN_H - 68, 24, 18, '#69d2e7', bands=4)
            return
        if self.state == 'cinematic':
            self.canvas.create_rectangle(0, 0, WIN_W, WIN_H, fill='#0a0f18', outline='')
            self._draw_stage_background()
            self._draw_cinematic_scene()
            self._draw_cinematic_overlay()
            self._draw_pixel_light_bloom(WIN_W // 2, WIN_H - 94, 20, 14, '#f2d35a', bands=4)
            return
        self._draw_atmosphere()
        self.canvas.create_rectangle(self.viewport_x - 14, self.viewport_y - 14, self.viewport_x + self.scene_w + 14, self.viewport_y + self.scene_h + 14, outline=self.stage_profile.get('frame_glow', '#f2d35a'), width=2)
        self.canvas.create_rectangle(self.viewport_x - 4, self.viewport_y - 4, self.viewport_x + self.scene_w + 4, self.viewport_y + self.scene_h + 4, outline='#1b2438', width=8)
        sky_color = self.stage_profile.get('sky_mid', '#203040') if self.state != 'title' else '#203040'
        self.canvas.create_rectangle(*self._present_rect(0, 0, self.scene_w, self.scene_h), fill=sky_color, outline='')
        if self.state == 'title' and self.img_title:
            try:
                bg = self.img_title
                px, py = self._present_xy(0, 0)
                self.canvas.create_image(px, py, image=bg, anchor='nw')
            except Exception:
                pass
        elif self.state != 'title':
            self._draw_stage_background()
        if self.state == 'title':
            self._draw_title_overlay()
            title_rei = self._get_scaled_asset_variant(self._current_player_asset_key(), 1.32) or self.s_img_player
            title_boss = self._get_scaled_asset_variant(self._current_boss_asset_key(), 1.12) or self.s_img_boss
            minion_a = self._get_scaled_asset_variant('minion1', 0.84) or self.s_img_minion1
            minion_b = self._get_scaled_asset_variant('minion2', 0.84) or self.s_img_minion1
            if title_rei:
                self.canvas.create_image(self.viewport_x + 196, self.viewport_y + 506, image=title_rei, anchor='nw')
            if title_boss:
                self.canvas.create_image(self.viewport_x + self.scene_w - 474, self.viewport_y + 324, image=title_boss, anchor='nw')
            if minion_a:
                self.canvas.create_image(self.viewport_x + 520, self.viewport_y + 690, image=minion_a, anchor='nw')
            if minion_b:
                self.canvas.create_image(self.viewport_x + self.scene_w - 646, self.viewport_y + 704, image=minion_b, anchor='nw')
            self._draw_duel_orb()
            if getattr(self, 'tutorial_open', False):
                pages = getattr(self, 'controls_pages', [])
                ptext = pages[self.controls_page] if 0 <= self.controls_page < len(pages) else ''
                ow = int(WIN_W * 0.88)
                oh = int(WIN_H * 0.42)
                ox = (WIN_W - ow) // 2
                oy = (WIN_H - oh) // 2
                self._draw_pixel_panel(ox, oy, ox + ow, oy + oh, '#05101a', '#f2d35a', glow=self.stage_profile.get('accent', '#7fe7ff'), notch=22, rib_count=7)
                self.canvas.create_text(ox + 26, oy + 24, anchor='nw', text='CONTROL PANEL', fill='#fff1dd', font=self._font_display(20, 'bold'))
                self.canvas.create_text(ox + 26, oy + 74, anchor='nw', text=ptext, fill='white', font=self._font_body(13), width=ow - 52)
                prompts = 'A / RIGHT: NEXT   LEFT: PREV   B / START / SPACE: CLOSE'
                self.canvas.create_text(ox + ow - 20, oy + oh - 24, anchor='ne', text=prompts, fill='#ffbe97', font=self._font_caption(11, 'bold'))
            return

        # draw nanocells
        for nc in self.nanocells:
            draw_x, draw_y = self._depth_project_point(nc.x * SCALE, nc.y * SCALE, 'fx')
            draw_x, draw_y = self._present_xy(draw_x, draw_y)
            self._draw_entity_shadow(draw_x, draw_y, 8 * SCALE, 8 * SCALE, '#241636')
            if self.img_nanocell:
                self.canvas.create_image(draw_x, draw_y, image=self.img_nanocell, anchor='nw')
            else:
                self._draw_pixel_light_bloom(draw_x + (4 * SCALE), draw_y + (4 * SCALE), 16, 16, 'magenta', bands=3)
            # overlay bbox for nanocell
            if getattr(self, 'show_bboxes', False):
                self._draw_asset_bbox_at(nc.x, nc.y, 'nanocell1')

        # draw minions
        for m in self.minions:
            minion_key = f'minion{(getattr(m, "variant", 0) % 3) + 1}'
            sprite = self._get_scaled_asset_variant(minion_key, 0.82) or self._current_minion_image(getattr(m, 'variant', 0), scaled=True) or getattr(m, 'sprite_scaled', None) or getattr(m, 'sprite', self.img_minion1)
            draw_x = (m.x - int(self.camera_x)) * SCALE
            draw_y = m.y * SCALE
            draw_x, draw_y = self._depth_project_point(draw_x, draw_y, 'entity')
            draw_x, draw_y = self._present_xy(draw_x, draw_y)
            sprite_w = sprite.width() if sprite and hasattr(sprite, 'width') else int(12 * SCALE * 0.82)
            sprite_h = sprite.height() if sprite and hasattr(sprite, 'height') else int(12 * SCALE * 0.82)
            draw_y -= max(0, sprite_h - (12 * SCALE))
            self._draw_entity_shadow(draw_x, draw_y, sprite_w, sprite_h, '#16233e')
            if getattr(m, 'tele', 0) > 0:
                self._draw_entity_halo(draw_x, draw_y, sprite_w, sprite_h, '#ffb347', 0.7)
            if sprite:
                # sprite may be a scaled PhotoImage already
                try:
                    self.canvas.create_image(draw_x, draw_y, image=sprite, anchor='nw')
                except Exception:
                    self.canvas.create_rectangle(draw_x, draw_y, draw_x+(12*SCALE), draw_y+(12*SCALE), fill=m.color)
            else:
                self.canvas.create_rectangle(draw_x, draw_y, draw_x+(12*SCALE), draw_y+(12*SCALE), fill=m.color)
            # overlay bbox for minion
            if getattr(self, 'show_bboxes', False):
                self._draw_asset_bbox_at(m.x, m.y, 'minion1')
            # minion healthbar
            hw = 20
            hx = draw_x + 6
            hy = self._present_xy(0, (m.y - 6) * SCALE)[1]
            maxhp = getattr(m, 'max_hp', getattr(m, 'hp', 1)) or 1
            hpw = max(0, int((getattr(m, 'hp', 0) / maxhp) * hw))
            self.canvas.create_rectangle(hx, hy, hx+hw, hy+4, outline='white')
            self.canvas.create_rectangle(hx, hy, hx+hpw, hy+4, fill='green', outline='')

        # draw player (with attack flash)
        px = (self.player.x - int(self.camera_x)) * SCALE
        py = self.player.y * SCALE
        px, py = self._depth_project_point(px, py, 'entity')
        px, py = self._present_xy(px, py)
        player_image = self._get_scaled_asset_variant(self._current_player_asset_key(), 1.18) or self._current_player_image(scaled=True) or self.img_player
        player_w = player_image.width() if player_image and hasattr(player_image, 'width') else int(12 * SCALE * 1.18)
        player_h = player_image.height() if player_image and hasattr(player_image, 'height') else int(12 * SCALE * 1.18)
        motion_phase = time.time() * 9.0
        motion_energy = max(getattr(self.player, 'motion_energy', 0.0), min(1.0, getattr(self.player, 'rupture_drive_timer', 0) / 320.0))
        motion_lead = int((1 if getattr(self.player, 'facing', 'right') == 'right' else -1) * (10 * motion_energy + 8 * min(1.0, getattr(self.player, 'rupture_drive_timer', 0) / 320.0)))
        motion_lift = int(math.sin(motion_phase) * (3 + motion_energy * 3))
        px += motion_lead
        py += motion_lift
        py -= max(0, player_h - (12 * SCALE))
        self._draw_entity_shadow(px, py, player_w, player_h, '#16233e')
        self._draw_entity_halo(px, py, player_w, player_h, '#7fe7ff', 1.2 if getattr(self.player, 'attacking', False) else 0.85)
        if motion_energy > 0.16 and player_image:
            trail_dir = -1 if getattr(self.player, 'facing', 'right') == 'right' else 1
            for index in range(1, 3):
                self.canvas.create_image(px + (trail_dir * index * 14), py + (index * 2), image=player_image, anchor='nw')
        if getattr(self.player, 'dodge_flash_timer', 0) > 0 and player_image:
            trail_dir = 1 if getattr(self.player, 'facing', 'right') == 'right' else -1
            for index in range(1, 3):
                self.canvas.create_image(px + (trail_dir * index * 18), py + (index * 3), image=player_image, anchor='nw')
        if getattr(self.player, 'flow_feint_timer', 0) > 0:
            self._draw_pixel_light_bloom(px + player_w // 2, py + player_h // 2, max(18, player_w // 3), max(16, player_h // 3), self.stage_profile.get('metric_secondary', '#7fd9e8'), bands=3)
        if player_image:
            self.canvas.create_image(px, py, image=player_image, anchor='nw')
        else:
            self.canvas.create_rectangle(px, py, px+(12*SCALE), py+(12*SCALE), fill=self.player.color)
        if getattr(self.player, 'attack_pose_timer', 0) > 0:
            attack_stamp_x = px + player_w + 14 if getattr(self.player, 'facing', 'right') == 'right' else px - 18
            self._draw_profile_stamp(attack_stamp_x, py + 28, 18, self.stage_profile.get('metric_primary', '#f3dfa1'), self.stage_profile.get('metric_secondary', '#7fd9e8'))
        # player bbox overlay
        if getattr(self, 'show_bboxes', False):
            self._draw_asset_bbox_at(self.player.x, self.player.y, 'player')
        # draw player attack projectiles if present
        for p in list(self.projectiles):
            try:
                imgp = p.get('img')
                draw_px = (p['x'] - int(self.camera_x)) * SCALE
                draw_py = p['y'] * SCALE
                draw_px, draw_py = self._depth_project_point(draw_px, draw_py, 'fx')
                draw_px, draw_py = self._present_xy(draw_px, draw_py)
                if imgp:
                    self.canvas.create_image(draw_px, draw_py, image=imgp, anchor='nw')
                else:
                    self._draw_pixel_light_bloom(draw_px + (p['w'] * SCALE) // 2, draw_py + (p['h'] * SCALE) // 2, max(10, p['w'] * SCALE // 2), max(10, p['h'] * SCALE // 2), 'orange', bands=3)
                # projectile bbox overlay (attackfx)
                if getattr(self, 'show_bboxes', False):
                    self._draw_asset_bbox_at(p['x'], p['y'], 'attackfx1')
            except Exception:
                pass

        self._draw_visual_hud()
        self._draw_duel_orb()

        # boss
        if self.boss:
            bx = self.boss.x * SCALE
            by = self.boss.y * SCALE
            # draw boss with camera offset
            bx = (self.boss.x - int(self.camera_x)) * SCALE
            bx, by = self._depth_project_point(bx, by, 'entity')
            bx, by = self._present_xy(bx, by)
            boss_image = self._get_scaled_asset_variant(self._current_boss_asset_key(), 1.08) or self._current_boss_image(scaled=True) or self.boss_sprite or self.img_boss
            boss_w = boss_image.width() if boss_image and hasattr(boss_image, 'width') else int(64 * SCALE * 1.08)
            boss_h = boss_image.height() if boss_image and hasattr(boss_image, 'height') else int(64 * SCALE * 1.08)
            by -= max(0, boss_h - (64 * SCALE))
            self._draw_entity_shadow(bx, by, boss_w, boss_h, '#20060a')
            self._draw_entity_halo(bx, by, boss_w, boss_h, '#ff5e5e', 1.4)
            if boss_image:
                self.canvas.create_image(bx, by, image=boss_image, anchor='nw')
            else:
                self.canvas.create_rectangle(bx, by, bx+64, by+64, fill='maroon')
            if getattr(self.boss, 'telegraph', 0) > 0:
                self.canvas.create_rectangle(bx + 8, by - 18, bx + boss_w - 8, by - 8, fill=self.stage_profile.get('metric_warning', '#ff8d72'), outline='')
            if getattr(self.boss, 'parts', None):
                cell_w = max(10, (64 * SCALE) // 4)
                cell_h = max(12, (64 * SCALE) // 2)
                for part_index, part_hp in enumerate(self.boss.parts):
                    col = part_index % 4
                    row = part_index // 4
                    px0 = bx + (col * cell_w)
                    py0 = by + (row * cell_h)
                    px1 = px0 + cell_w - 2
                    py1 = py0 + cell_h - 2
                    ratio = max(0.0, min(1.0, part_hp / 40.0))
                    outline = '#f2d35a' if ratio > 0.5 else '#ff8a6b' if ratio > 0.0 else '#301010'
                    self.canvas.create_rectangle(px0, py0, px1, py1, outline=outline)
            # boss bbox overlay
            if getattr(self, 'show_bboxes', False):
                self._draw_asset_bbox_at(self.boss.x, self.boss.y, 'boss')
        if self.show_debug:
            gp = self.prev_gp or {}
            s = f"A:{int(gp.get('a',0))} B:{int(gp.get('b',0))} LX:{gp.get('lx',0)} LY:{gp.get('ly',0)}"
            self.canvas.create_text(WIN_W-18, 64, anchor='ne', fill='white', font=self._font_body(14), text=s)

        # draw effects
        for i, ef in enumerate(list(self.effects)):
            ex, ey, sp, t = ef
            draw_ex, draw_ey = self._depth_project_point(ex * SCALE, ey * SCALE, 'fx')
            draw_ex, draw_ey = self._present_xy(draw_ex, draw_ey)
            if sp:
                try:
                    # sp may be a raw or scaled PhotoImage; prefer scaled variants
                    img_to_draw = sp
                    if isinstance(sp, str):
                        img_to_draw = self.scaled.get(sp) or self.assets.get(sp)
                    self.canvas.create_image(draw_ex, draw_ey, image=img_to_draw, anchor='nw')
                except Exception:
                    self._draw_pixel_light_bloom(draw_ex + (4 * SCALE), draw_ey + (4 * SCALE), 14, 14, 'orange', bands=3)
            else:
                self._draw_pixel_light_bloom(draw_ex + (4 * SCALE), draw_ey + (4 * SCALE), 14, 14, 'orange', bands=3)
            t -= 16
            if t <= 0:
                try:
                    self.effects.remove(ef)
                except ValueError:
                    pass
            else:
                # replace tuple with updated timer
                self.effects[self.effects.index(ef)] = (ex, ey, sp, t)

        self._draw_stage_foreground()

        self._draw_depth_frame()
        self._draw_viewport_scanlines()
        self._draw_central_shell()
        self._draw_playfield_tension()
        if getattr(self.player, 'attacking', False):
            self._draw_speedlines(px + 60, py + 40, 8, '#7fe7ff')
        elif self.boss:
            self._draw_speedlines(bx + 120, by + 120, 6, '#ff8a6b')

        if self.banner_text:
            self._draw_word_burst(WIN_W // 2, self.viewport_y + 72, self.banner_text, '#5f1710', '#f2d35a', '#fff3df', scale=0.78)
        if self.state == 'stage_intro' or self.stage_intro_timer > 0:
            self._draw_status_card(
                f'WAVE {max(1, self.wave + (1 if self.state == "stage_intro" and self.wave == 0 else 0))}: {self.stage_profile.get("display_name", "CITY OUTSKIRTS").upper()}',
                self.stage_profile.get('subtitle', '').upper(),
            )
        elif self.state == 'cypher':
            self._draw_status_card(
                'CYPHER SECURED',
                f'{self.boss_name} BROKEN  |  {self.stage_profile.get("profile_label", "CATALOG").upper()}',
            )
        elif self.state == 'grade':
            self._draw_status_card(
                'PRESSURE GRADE',
                self.grade_summary,
            )
        elif self.stage_clear_timer > 0:
            self._draw_status_card(
                'STAGE CLEAR',
                self.stage_profile.get('profile_tagline', '').upper(),
            )

        # draw tutorial overlay in-canvas if open (blocks gameplay)
        if getattr(self, 'tutorial_open', False):
            pages = getattr(self, 'controls_pages', [])
            ptext = pages[self.controls_page] if 0 <= self.controls_page < len(pages) else ''
            ow = int(WIN_W * 0.92)
            oh = int(WIN_H * 0.42)
            ox = (WIN_W - ow) // 2
            oy = (WIN_H - oh) // 2
            self._draw_pixel_panel(ox, oy, ox + ow, oy + oh, '#001018', '#f2d35a', glow=self.stage_profile.get('accent', '#7fe7ff'), notch=22, rib_count=8)
            self.canvas.create_text(ox + 20, oy + 18, anchor='nw', text='CONTROL PANEL', fill='#fff1dd', font=self._font_display(20, 'bold'))
            self.canvas.create_text(ox + 20, oy + 72, anchor='nw', text=ptext, fill='white', font=self._font_body(12), width=ow - 40)
            prompts = 'A/Right: Next    Left: Prev    B/Back/Space: Close'
            self.canvas.create_text(ox + ow - 20, oy + oh - 18, anchor='ne', text=prompts, fill='#ffc39e', font=self._font_caption(10, 'bold'))

    def loop(self):
        try:
            now = time.time()
            dt = (now - self.last) * 1000
            self.last = now
            # tick cooldowns
            if getattr(self.player, 'combo_timer', 0) > 0:
                self.player.combo_timer = max(0, self.player.combo_timer - dt)
                if self.player.combo_timer == 0:
                    self.player.combo_count = 0
            self.player.beat_timer = (getattr(self.player, 'beat_timer', 0) + dt) % BEAT_PERIOD_MS
            beat_timer = getattr(self.player, 'beat_timer', 0)
            self.player.beat_perfect = beat_timer <= PERFECT_WINDOW_MS or beat_timer >= (BEAT_PERIOD_MS - PERFECT_WINDOW_MS)
            if getattr(self.player, 'dodge_timer', 0) > 0:
                self.player.dodge_timer = max(0, self.player.dodge_timer - dt)
            if getattr(self.player, 'hit_stun', 0) > 0:
                self.player.hit_stun = max(0, self.player.hit_stun - dt)
            if getattr(self.player, 'attack_buffer', 0) > 0:
                self.player.attack_buffer = max(0, self.player.attack_buffer - dt)
            if getattr(self.player, 'dodge_buffer', 0) > 0:
                self.player.dodge_buffer = max(0, self.player.dodge_buffer - dt)
            if getattr(self.player, 'attack_cooldown', 0) > 0:
                previous_attack_timer = self.player.attack_cooldown
                self.player.attack_cooldown = max(0, self.player.attack_cooldown - dt)
                if not getattr(self.player, 'attack_resolved', False) and previous_attack_timer > ATTACK_ACTIVE_MS >= self.player.attack_cooldown:
                    self._resolve_player_attack()
                    self.player.attack_resolved = True
            if getattr(self.player, 'attack_pose_timer', 0) > 0:
                self.player.attack_pose_timer = max(0, self.player.attack_pose_timer - dt)
            if getattr(self.player, 'dodge_flash_timer', 0) > 0:
                self.player.dodge_flash_timer = max(0, self.player.dodge_flash_timer - dt)
            if getattr(self.player, 'flow_feint_timer', 0) > 0:
                self.player.flow_feint_timer = max(0, self.player.flow_feint_timer - dt)
            if getattr(self.player, 'rupture_drive_timer', 0) > 0:
                self.player.rupture_drive_timer = max(0, self.player.rupture_drive_timer - dt)
            if getattr(self.player, 'nanocell_boost_timer', 0) > 0:
                self.player.nanocell_boost_timer = max(0, self.player.nanocell_boost_timer - dt)
            if getattr(self, 'banner_timer', 0) > 0:
                self.banner_timer = max(0, self.banner_timer - dt)
                if self.banner_timer == 0:
                    self.banner_text = ''
            if getattr(self, 'stage_intro_timer', 0) > 0:
                self.stage_intro_timer = max(0, self.stage_intro_timer - dt)
            if getattr(self, 'stage_clear_timer', 0) > 0:
                self.stage_clear_timer = max(0, self.stage_clear_timer - dt)
                if self.stage_clear_timer == 0:
                    self.state = 'title'
                    self._reset_combat_lane()
            if getattr(self, 'splash_timer', 0) > 0 and self.state == 'splash':
                self.splash_timer = max(0, self.splash_timer - dt)
                if self.splash_timer == 0:
                    self.state = 'cinematic'
                    self.cinematic_timer = self.cinematic_duration
            if getattr(self, 'cinematic_timer', 0) > 0 and self.state == 'cinematic':
                self.cinematic_timer = max(0, self.cinematic_timer - dt)
                if self.cinematic_timer == 0:
                    self.state = 'title'
            if getattr(self, 'cypher_timer', 0) > 0 and self.state == 'cypher':
                self.cypher_timer = max(0, self.cypher_timer - dt)
                if self.cypher_timer == 0:
                    self.state = 'grade'
                    self.grade_timer = 2200
            if getattr(self, 'grade_timer', 0) > 0 and self.state == 'grade':
                self.grade_timer = max(0, self.grade_timer - dt)
                if self.grade_timer == 0:
                    self.state = 'title'
                    self._reset_combat_lane()
            self.player.attacking = getattr(self.player, 'attack_pose_timer', 0) > 0
            self.update(dt)
            self._update_adaptive_depth(dt)
            self.sprite_refresh_timer = max(0, self.sprite_refresh_timer - dt)
            if self.sprite_refresh_timer == 0:
                self._refresh_runtime_sprite_assets()
                self.sprite_refresh_timer = 140
            self._tick_audio(dt)
            self.draw()
        except Exception:
            detail = traceback.format_exc()
            self.last_error = detail
            self._write_runtime_error('Main loop exception', detail)
            self.running = False
            try:
                self.draw()
            except Exception:
                pass
        if self.running:
            self.loop_after_id = self.root.after(16, self.loop)

    def _set_runtime_asset(self, key, pil_image):
        if pil_image is None or not PIL_AVAILABLE:
            return
        self.assets_pil[key] = pil_image
        scaled_image = pil_image.resize((pil_image.width * SCALE, pil_image.height * SCALE), Image.Resampling.NEAREST)
        photo_image = ImageTk.PhotoImage(scaled_image)
        self.assets[key] = photo_image
        self.scaled[key] = photo_image

    def _load_placeholder_assets(self):
        for key, fname in ASSET_FILES.items():
            path = os.path.join(PLACEHOLDER_DIR, fname)
            if not os.path.exists(path):
                self.assets[key] = None
                self.scaled[key] = None
                continue
            try:
                if PIL_AVAILABLE:
                    base_image = Image.open(path).convert('RGBA')
                    styled_image = stylize_comic_asset(base_image)
                    self._set_runtime_asset(key, styled_image)
                else:
                    image = tk.PhotoImage(file=path)
                    self.assets[key] = image
                    self.scaled[key] = image
            except Exception:
                self.assets[key] = None
                self.scaled[key] = None

    def _sync_asset_refs(self):
        self.img_title = self.assets.get('title')
        self.img_player = self.assets.get('player') or self.assets.get('player_idle')
        self.img_minion1 = self.assets.get('minion1') or self.assets.get('minion2') or self.assets.get('minion3')
        self.img_nanocell = self.assets.get('nanocell1') or self.assets.get('nanocell2')
        self.img_boss = self.assets.get('boss') or self.assets.get('boss_p1')
        self.img_attack = self.assets.get('attackfx1')
        self.img_attack2 = self.assets.get('attackfx2')
        self.img_blodfx = self.assets.get('blodfx')
        self.s_img_attack = self.scaled.get('attackfx1') or self.scaled.get('attackfx2')
        self.s_img_attack2 = self.scaled.get('attackfx2') or self.s_img_attack
        self.s_img_blodfx = self.scaled.get('blodfx')
        self.s_img_minion1 = self.scaled.get('minion1') or self.scaled.get('minion2') or self.scaled.get('minion3')
        self.s_img_player = self.scaled.get('player') or self.scaled.get('player_idle')
        self.s_img_boss = self.scaled.get('boss') or self.scaled.get('boss_p1')

    def _refresh_asset_bbox(self):
        self.asset_bbox = {}
        if not PIL_AVAILABLE:
            for key in self.assets.keys():
                self.asset_bbox[key] = None
            return
        for key, image in self.assets_pil.items():
            if image is None:
                self.asset_bbox[key] = None
                continue
            alpha = image.getchannel('A')
            bbox = alpha.getbbox()
            self.asset_bbox[key] = bbox if bbox else (0, 0, image.width, image.height)

    def _sprite_context(self):
        boss_hp_ratio = 1.0
        boss_phase = 1
        active_keys = getattr(self, 'keys', set())
        if self.boss:
            boss_hp_ratio = max(0.0, min(1.0, self.boss.hp / max(1, self.boss.max_hp)))
            boss_phase = getattr(self.boss, 'phase', 1)
        input_x = int('right' in active_keys) - int('left' in active_keys)
        input_y = int('down' in active_keys) - int('up' in active_keys)
        input_pressure = sum(1 for key in ('left', 'right', 'up', 'down', 'z', 'x', 'lb', 'rb') if key in active_keys)
        aggression = min(1.0, (self.player.combo_count * 0.18) + (0.35 if getattr(self.player, 'attacking', False) else 0.0) + (0.20 if self.player.beat_perfect else 0.0))
        defense = min(1.0, (0.45 if self.player.dodge_timer > 0 else 0.0) + ((1.0 - boss_hp_ratio) * 0.2))
        return {
            'stage_id': self.stage_id,
            'visual_profile': self.visual_profile['id'],
            'playthrough_seed': int(self.playthrough_seed),
            'phase': boss_phase,
            'wave': int(self.wave),
            'score': int(self.score),
            'hp_ratio': max(0.0, min(1.0, self.player.hp / max(1, self.player.max_hp))),
            'boss_hp_ratio': boss_hp_ratio,
            'boost_active': self.player.nanocell_boost_timer > 0,
            'beat_perfect': bool(self.player.beat_perfect),
            'combo_count': int(self.player.combo_count),
            'facing': getattr(self.player, 'facing', 'right'),
            'input_x': input_x,
            'input_y': input_y,
            'input_pressure': input_pressure,
            'aggression': aggression,
            'defense': defense,
            'movement_energy': min(1.0, (abs(input_x) + abs(input_y)) * 0.5 + (0.22 if self.player.combo_timer > 0 else 0.0)),
            'variant_seed': int((self.playthrough_seed % 97) + self.player.combo_count + boss_phase + (2 if self.player.nanocell_boost_timer > 0 else 0) + input_pressure),
        }

    def _runtime_sprite_signature(self):
        metrics = self.depth_metrics or {}
        context = self._sprite_context()
        return (
            self.state,
            self.stage_id,
            int(metrics.get('brightness', 0.5) * 6),
            int(metrics.get('proximity', 0.35) * 6),
            int(metrics.get('eye_open', 0.5) * 6),
            int(metrics.get('dilation', 0.5) * 6),
            int(metrics.get('edge_density', 0.0) * 8),
            int(metrics.get('confidence', 0.0) * 6),
            int(context.get('phase', 1)),
            int(context.get('boost_active', False)),
            int(context.get('beat_perfect', False)),
            int(context.get('combo_count', 0)),
            int(context.get('hp_ratio', 1.0) * 5),
            int(context.get('boss_hp_ratio', 1.0) * 5),
            int(context.get('input_pressure', 0)),
            int((context.get('aggression', 0.0)) * 6),
            int((context.get('defense', 0.0)) * 6),
            int((context.get('movement_energy', 0.0)) * 6),
            int(context.get('wave', 0)),
            context.get('visual_profile', 'cathedral_spire'),
            int(context.get('playthrough_seed', 0) % 97),
        )

    def _refresh_runtime_sprite_assets(self, force=False):
        if not PIL_AVAILABLE or not self.gb_base_assets or build_runtime_bundle is None:
            return
        signature = self._runtime_sprite_signature()
        if not force and signature == self.runtime_sprite_signature:
            return
        runtime_bundle = build_runtime_bundle(self.gb_base_assets, self.depth_metrics or {}, self._sprite_context())
        if not runtime_bundle:
            return
        alias_map = {
            'player_idle': 'player',
            'boss_p1': 'boss',
            'cinematic_player': 'player_cinematic',
            'cinematic_boss': 'boss_cinematic',
        }
        for key, pil_image in runtime_bundle.items():
            self._set_runtime_asset(key, pil_image)
            alias_key = alias_map.get(key)
            if alias_key:
                self._set_runtime_asset(alias_key, pil_image)
        self.runtime_sprite_signature = signature
        self._sync_asset_refs()
        self._refresh_asset_bbox()

    def _current_player_asset_key(self):
        if getattr(self.player, 'attack_pose_timer', 0) > 0 or getattr(self.player, 'attacking', False):
            return 'player_attack'
        if getattr(self.player, 'dodge_timer', 0) > 0 or self.player.combo_count > 0:
            return 'player_run'
        return 'player_idle'

    def _current_player_image(self, scaled=True):
        key = self._current_player_asset_key()
        return self.scaled.get(key) if scaled else self.assets.get(key)

    def _current_boss_asset_key(self):
        phase = self._boss_phase_index() + 1 if self.boss else 1
        return f'boss_p{max(1, min(3, phase))}'

    def _current_boss_image(self, scaled=True):
        key = self._current_boss_asset_key()
        return self.scaled.get(key) if scaled else self.assets.get(key)

    def _current_minion_image(self, variant=0, scaled=True):
        key = f'minion{(variant % 3) + 1}'
        return self.scaled.get(key) if scaled else self.assets.get(key)

    def _current_cinematic_image(self, side, scaled=True):
        key = 'cinematic_player' if side == 'player' else 'cinematic_boss'
        return self.scaled.get(key) if scaled else self.assets.get(key)

    def _build_depth_presets(self):
        presets = {}
        stereo = self.stereo_profile.get('adaptiveStereo3D', {})
        for preset in stereo.get('calibrationPresets', []):
            name = preset.get('name')
            if not name:
                continue
            hint = DEPTH_PRESET_HINTS.get(name, DEPTH_PRESET_HINTS['studio-balanced'])
            presets[name] = {
                'name': name,
                'comfort': bool(preset.get('comfort', True)),
                'force_flat': bool(preset.get('forceFlat', False)),
                'smoothing': preset.get('smoothing', 'soft'),
                'intended_use': preset.get('intendedUse', ''),
                **hint,
            }
        for name, hint in DEPTH_PRESET_HINTS.items():
            presets.setdefault(name, {
                'name': name,
                'comfort': True,
                'force_flat': name == 'low-strain-mono',
                'smoothing': 'soft',
                'intended_use': '',
                **hint,
            })
        return presets

    def _set_stage(self, stage_id):
        profile = self._apply_visual_profile(STAGE_LIBRARY.get(stage_id, STAGE_LIBRARY['marsh_shore']))
        self.stage_id = profile['id']
        self.stage_profile = profile
        self.world_width = GBA_W if self.parity_mode else max(int(profile.get('width', GBA_W)), GBA_W)
        self.stage_spawn_lanes = list(profile.get('spawn_lanes', [72, 96, 116]))
        layout = self._build_stage_layout(profile)
        self.stage_layers = layout['layers']
        self.stage_obstacles = layout['obstacles']
        self.stage_climb_routes = layout['climb_routes']
        if self.parity_mode:
            self.stage_obstacles = []
            self.stage_climb_routes = []
        self.player.x = max(0, min(self.player.x, self.world_width - 8))
        self.camera_x = max(-10, min(self.camera_x, 10)) if self.parity_mode else max(0, min(self.camera_x, max(0, self.world_width - GBA_W)))

    def _set_banner(self, text, duration=850):
        self.banner_text = text
        self.banner_timer = duration

    def _reset_combat_lane(self):
        self.player.combo_count = 0
        self.player.combo_timer = 0
        self.player.beat_timer = 0
        self.player.attack_buffer = 0
        self.player.dodge_buffer = 0
        self.player.beat_perfect = False
        self.player.dodge_read_total = 0
        self.player.nanocell_count = 0
        self.player.attack_cooldown = 0
        self.player.dodge_timer = 0
        self.player.hit_stun = 0
        self.player.nanocell_boost_timer = 0
        self.player.attack_pose_timer = 0
        self.player.dodge_flash_timer = 0
        self.player.flow_feint_timer = 0
        self.player.rupture_drive_timer = 0
        self.player.motion_energy = 0.0
        self.player.attack_power = 14
        self.player.attack_resolved = False
        self.player.facing = 'right'
        self.player.x = 72
        self.player.y = 100
        self.wave = 0
        self.minions = []
        self.nanocells = []
        self.projectiles = []
        self.boss = None
        self.camera_x = self._parity_camera_target() if self.parity_mode else 0
        self.render_audit_written = False

    def _boss_phase_index(self):
        if not self.boss:
            return 0
        return max(0, min(2, int(getattr(self.boss, 'phase', 1)) - 1))

    def _boss_hp_ratio(self):
        if not self.boss or not getattr(self.boss, 'max_hp', 0):
            return 0.0
        return max(0.0, min(1.0, float(self.boss.hp) / float(self.boss.max_hp)))

    def _current_attack_damage(self):
        damage = self.player.attack_power
        if self.player.nanocell_boost_timer > 0:
            damage += 10
        if self.player.combo_count >= 2:
            damage += 6
        if self.player.beat_perfect:
            damage += 6
        return damage

    def _attack_buffer_duration_ms(self):
        duration = ATTACK_BUFFER_MS
        if getattr(self.player, 'combo_timer', 0) > 0 or getattr(self.boss, 'windup_timer', 0) > 0:
            duration += 20
        return duration

    def _attack_hits_target(self, target_center_x, forward_range=PLAYER_ATTACK_FRONT_PX, rear_range=PLAYER_ATTACK_REAR_PX):
        player_center_x = self.player.x + 6
        delta = target_center_x - player_center_x
        if getattr(self.player, 'facing', 'right') == 'left':
            delta = -delta
        if delta >= 0:
            return delta <= forward_range
        return (-delta) <= rear_range

    def _boss_attack_kind(self):
        phase = self._boss_phase_index()
        distance = abs((self.boss.x + 20) - (self.player.x + 6)) if self.boss else 0
        if phase == 0:
            return 'spit' if distance > 68 else 'sweep'
        if phase == 1:
            return 'slam' if distance < 92 else 'spit'
        if self.player.nanocell_boost_timer <= 0 and distance < 88:
            return 'tidal'
        return 'sweep' if distance < 84 else 'spit'

    def _boss_attack_windup(self, kind):
        return {
            'sweep': 320,
            'spit': 280,
            'slam': 420,
            'tidal': 360,
        }.get(kind, 300)

    def _boss_attack_recover(self, kind):
        return {
            'sweep': 340,
            'spit': 300,
            'slam': 460,
            'tidal': 420,
        }.get(kind, 320)

    def _boss_attack_damage(self, kind):
        return {
            'sweep': 14,
            'spit': 12,
            'slam': 22,
            'tidal': 10,
        }.get(kind, 12)

    def _boss_attack_label(self, kind):
        return {
            'sweep': 'REAPER SWEEP',
            'spit': 'ACID SPIT',
            'slam': 'GRAVE SLAM',
            'tidal': 'VOID TIDE',
        }.get(kind, 'DUEL')

    def _boss_attack_range(self, kind):
        return {
            'sweep': 72,
            'spit': 94,
            'slam': 84,
            'tidal': 96,
        }.get(kind, 72)

    def _boss_attack_threat(self, kind):
        if not self.boss:
            return 0
        distance = abs((self.boss.x + 24) - (self.player.x + 6))
        attack_range = self._boss_attack_range(kind)
        if distance > attack_range + 10:
            return 0
        if distance > attack_range:
            return 1
        return 2

    def _resolve_player_attack(self):
        damage = self._current_attack_damage()
        landed_hit = False
        if self.boss:
            if getattr(self.boss, 'first_strike_timer', 0) > 0:
                damage += 12
                self.boss.first_strike_timer = 0
                self.boss.intro_lock = 0
                self._set_banner('FIRST STRIKE', 520)
            hit_x = self.player.x + (18 if self.player.facing == 'right' else -8)
            hit_y = self.player.y + 4
            boss_center_x = self.boss.x + 32
            if self._attack_hits_target(boss_center_x, PLAYER_ATTACK_FRONT_PX + 4, PLAYER_ATTACK_REAR_PX):
                landed_hit = self._apply_boss_hit(damage, hit_x, hit_y)
            if landed_hit:
                bfx = getattr(self, 's_img_blodfx', None) or getattr(self, 'img_blodfx', None)
                if bfx is not None and self.boss is not None:
                    self.effects.append((self.boss.x, self.boss.y - 4, bfx, 400))
        for m in list(self.minions):
            target_center_x = m.x + 6
            if self._attack_hits_target(target_center_x, MINION_ATTACK_RANGE_PX, PLAYER_ATTACK_REAR_PX):
                m.hp -= damage
                landed_hit = True
                m.recover_timer = max(getattr(m, 'recover_timer', 0), 240)
                m.tele = 0
                if m.hp <= 0:
                    self.score += 40 + (20 if self.player.beat_perfect else 0)
                    self.spawn_nanocell(m.x, m.y)
                    try:
                        self.minions.remove(m)
                    except ValueError:
                        pass
                    try:
                        self.play_sound('minion_die')
                    except Exception:
                        pass
        if landed_hit:
            self.player.combo_count = min(3, self.player.combo_count + 1)
            self.player.combo_timer = COMBO_WINDOW_MS
            if self.player.combo_count >= 3:
                self._set_banner('ONE HIT TO FINISH', 520)
            elif self.player.beat_perfect:
                self._set_banner('PERFECT STRIKE', 420)
        else:
            self.player.combo_count = 0
            self.player.combo_timer = 0
        try:
            aimg = getattr(self, 's_img_attack', None) or getattr(self, 'img_attack', None)
            pw = getattr(self.player, 'size', (12,12))[0]
            if self.player.facing == 'right':
                px = self.player.x + pw
            else:
                px = self.player.x - 8
            py = self.player.y
            pwid = aimg.width() if aimg and hasattr(aimg, 'width') else 12
            phei = aimg.height() if aimg and hasattr(aimg, 'height') else 12
            proj = {'x': px, 'y': py, 'w': pwid, 'h': phei, 'img': aimg, 'timer': 180, 'spawn_time': time.time(), 'base_damage': damage, 'facing': getattr(self.player, 'facing', 'right')}
            self.projectiles.append(proj)
        except Exception:
            pass

    def _apply_boss_hit(self, damage, hit_x, hit_y):
        if not self.boss:
            return False
        if getattr(self.boss, 'stun_timer', 0) > 0:
            return False
        previous_phase = getattr(self.boss, 'phase', 1)
        bw = getattr(self.boss_sprite, 'width', lambda: 64)()
        bh = getattr(self.boss_sprite, 'height', lambda: 64)()
        if not self._rects_overlap(hit_x, hit_y, 16, 16, self.boss.x, self.boss.y, bw, bh):
            return False
        local_x = max(0, min(bw - 1, int(hit_x - self.boss.x)))
        local_y = max(0, min(bh - 1, int(hit_y - self.boss.y)))
        part_x = min(3, max(0, local_x // max(1, bw // 4)))
        part_y = min(1, max(0, local_y // max(1, bh // 2)))
        part_index = (part_y * 4) + part_x
        self.boss.parts[part_index] = max(0, self.boss.parts[part_index] - damage)
        phase_pool = max(0, getattr(self.boss, 'phase_hp_remaining', self.boss_phase_hp[previous_phase - 1]))
        if phase_pool <= damage:
            if previous_phase < 3:
                next_phase = previous_phase + 1
                self.boss.phase = next_phase
                self.boss.phase_hp_remaining = self.boss_phase_hp[next_phase - 1]
                self.boss.hp = self.boss.phase_hp_remaining + sum(self.boss_phase_hp[next_phase:])
                self.boss.windup_timer = 0
                self.boss.recover_timer = self._boss_attack_recover('slam')
                self.boss.stun_timer = BOSS_PHASE_STUN_MS
                self.boss.atk_timer = 560
                self.boss.telegraph = 0
                self._set_banner(['TIDE RISING', 'LEVIA PHASE 2', 'LEVIA PHASE 3'][next_phase - 1], 620)
                return True
            self.boss.phase_hp_remaining = 0
            self.boss.hp = 0
        else:
            self.boss.phase_hp_remaining = phase_pool - damage
            self.boss.hp = max(0, self.boss.hp - damage)
            self.boss.stun_timer = BOSS_HIT_STUN_MS
            self.boss.windup_timer = 0
            self.boss.recover_timer = 220
        if self.boss.hp <= 0:
            self.score += 300 + (self.player.combo_count * 40) + (60 if self.player.beat_perfect else 0)
            self.spawn_nanocell(self.boss.x + 18, self.boss.y + 22)
            self._set_banner(f'{self.stage_profile.get("profile_label", "CATALOG").upper()} CYPHER SECURED', 1800)
            self.state = 'cypher'
            self.cypher_timer = 1800
            self.grade_summary = (
                f'{self.stage_profile.get("profile_label", "CATALOG").upper()}  '
                f'SCORE {self.score}  '
                f'STYLE {self.player.combo_count * 3}  '
                f'PRECISION {2 if self.player.beat_perfect else 1}  '
                f'ADAPTATION {1 if self.player.nanocell_boost_timer > 0 else 0}'
            )
            self.boss = None
            try:
                self.play_sound('boss_die')
            except Exception:
                pass
        return True

    def _parity_camera_target(self):
        focus_x = self.player.x
        desired_x = GBA_W * 0.47
        if self.boss:
            focus_x = (self.player.x * 0.46) + (self.boss.x * 0.54)
            desired_x = GBA_W * 0.50
        elif self.minions:
            lane_focus = sum(m.x for m in self.minions) / max(1, len(self.minions))
            focus_x = (self.player.x * 0.55) + (lane_focus * 0.45)
            desired_x = GBA_W * 0.46

        target = focus_x - desired_x
        if self.boss and getattr(self.boss, 'telegraph', 0) > 0:
            target += 6.0 if self.boss.x > self.player.x else -6.0
        if getattr(self.player, 'dodge_timer', 0) > 0:
            target += -8.0 if getattr(self.player, 'facing', 'right') == 'right' else 8.0
        elif getattr(self.player, 'combo_timer', 0) > 0:
            target += 4.0 if getattr(self.player, 'facing', 'right') == 'right' else -4.0
        return max(-28.0, min(28.0, target))

    def _stage_spawn_point(self, index, elevated_bias=0.0):
        lanes = list(self.stage_spawn_lanes) or [96]
        lane_index = index % len(lanes)
        if self.stage_id == 'inner_city' and elevated_bias > 0.0:
            lane_index = index % max(1, len(lanes) // 2)
        lane_y = lanes[lane_index]
        spacing = 44
        if self.stage_id == 'marsh_shore':
            spacing = 40
        elif self.stage_id == 'city_outskirts':
            spacing = 52
        elif self.stage_id == 'inner_city':
            spacing = 58
        base_x = self.world_width - 180 - (index * spacing)
        return max(72, min(self.world_width - 28, base_x)), lane_y

    def _build_stage_layout(self, profile):
        stage_id = profile['id']
        width = int(profile['width'])
        ground_y = int(profile['ground_y'])
        horizon_y = int(profile['horizon_y'])
        rng = random.Random(f"{stage_id}:{width}:{ground_y}:{self.playthrough_seed}:{profile.get('layout_seed', 0)}")
        layers = {'far': [], 'mid': [], 'near': []}
        obstacles = []
        climb_routes = []

        if stage_id == 'marsh_shore':
            x = -40
            while x < width + 120:
                kind = rng.choice(['mangrove', 'reef_spire', 'storm_tower'])
                w = rng.randint(28, 76)
                h = rng.randint(18, 56)
                layers['far'].append({'type': kind, 'x': x, 'y': horizon_y - h, 'w': w, 'h': h})
                x += rng.randint(24, 46)
            x = 10
            while x < width + 40:
                layers['far'].append({'type': 'breaker_lights', 'x': x, 'y': horizon_y + rng.randint(2, 10), 'w': rng.randint(20, 48), 'h': rng.randint(6, 12)})
                x += rng.randint(58, 98)
            x = 30
            while x < width - 40:
                kind = rng.choice(['salt_shack', 'tide_pylon', 'trawler_hulk', 'wrecked_walkway'])
                w = rng.randint(32, 82)
                h = rng.randint(24, 52)
                layers['mid'].append({'type': kind, 'x': x, 'y': ground_y - h, 'w': w, 'h': h})
                if kind == 'salt_shack':
                    obstacles.append({'x': x + 8, 'y': ground_y - 18, 'w': max(16, w - 16), 'h': 18, 'climbable': False})
                x += w + rng.randint(28, 66)
            x = 0
            while x < width + 40:
                kind = rng.choice(['reed_bank', 'mooring_post', 'tide_pipe', 'foam_band', 'signal_buoy', 'kelp_cluster'])
                w = rng.randint(14, 34)
                h = rng.randint(10, 34)
                layers['near'].append({'type': kind, 'x': x, 'y': ground_y - h + rng.randint(-4, 6), 'w': w, 'h': h})
                x += rng.randint(18, 42)
        elif stage_id == 'city_outskirts':
            x = -60
            while x < width + 180:
                kind = rng.choice(['skyline_block', 'water_tank', 'signal_spire'])
                w = rng.randint(34, 92)
                h = rng.randint(28, 78)
                layers['far'].append({'type': kind, 'x': x, 'y': horizon_y - h, 'w': w, 'h': h})
                x += rng.randint(26, 52)
            x = 40
            while x < width - 60:
                kind = rng.choice(['warehouse', 'billboard_frame', 'transit_gantry'])
                w = rng.randint(36, 94)
                h = rng.randint(26, 62)
                layers['mid'].append({'type': kind, 'x': x, 'y': ground_y - h, 'w': w, 'h': h})
                if kind == 'warehouse':
                    obstacles.append({'x': x + 6, 'y': ground_y - 22, 'w': max(18, w - 12), 'h': 22, 'climbable': False})
                x += w + rng.randint(30, 60)
            x = 0
            while x < width + 30:
                kind = rng.choice(['guardrail', 'streetlight', 'conduit_box'])
                w = rng.randint(10, 28)
                h = rng.randint(16, 40)
                layers['near'].append({'type': kind, 'x': x, 'y': ground_y - h + rng.randint(-2, 8), 'w': w, 'h': h})
                x += rng.randint(20, 38)
        else:
            x = -80
            while x < width + 220:
                kind = rng.choice(['tower_block', 'skybridge_stub', 'antenna_stack'])
                w = rng.randint(42, 96)
                h = rng.randint(40, 92)
                layers['far'].append({'type': kind, 'x': x, 'y': horizon_y - h, 'w': w, 'h': h})
                x += rng.randint(30, 56)
            x = 72
            previous_roof = None
            while x < width - 90:
                w = rng.randint(58, 90)
                top = rng.randint(38, 72)
                layers['mid'].append({'type': 'city_block', 'x': x, 'y': top, 'w': w, 'h': ground_y - top})
                route_x = x + rng.randint(12, max(14, w - 18))
                climb_routes.append({'x': route_x - 2, 'y': top - 12, 'w': 18, 'h': (ground_y - top) + 28})
                layers['near'].append({'type': 'fire_escape', 'x': route_x - 4, 'y': top - 6, 'w': 20, 'h': (ground_y - top) + 18})
                layers['near'].append({'type': 'rooftop_walk', 'x': x + 6, 'y': top - 4, 'w': max(18, w - 12), 'h': 8})
                if rng.random() < 0.45:
                    layers['near'].append({'type': 'neon_panel', 'x': x + 8, 'y': top + 8, 'w': max(18, w - 16), 'h': 12})
                if previous_roof is not None:
                    bridge_gap = x - previous_roof['right']
                    if bridge_gap < 92 and rng.random() < 0.7:
                        bridge_y = max(top, previous_roof['top']) + 6
                        bridge_x = previous_roof['right'] - 4
                        bridge_w = bridge_gap + 8
                        layers['mid'].append({'type': 'skybridge', 'x': bridge_x, 'y': bridge_y, 'w': bridge_w, 'h': 10})
                        climb_routes.append({'x': bridge_x, 'y': bridge_y - 8, 'w': bridge_w, 'h': 24})
                obstacles.append({'x': x, 'y': top, 'w': w, 'h': ground_y - top, 'climbable': True})
                previous_roof = {'right': x + w, 'top': top}
                x += w + rng.randint(24, 48)
            x = 0
            while x < width + 40:
                kind = rng.choice(['street_barrier', 'signal_post', 'steam_vent'])
                w = rng.randint(10, 28)
                h = rng.randint(12, 34)
                layers['near'].append({'type': kind, 'x': x, 'y': ground_y - h + rng.randint(-2, 8), 'w': w, 'h': h})
                x += rng.randint(18, 34)

        return {'layers': layers, 'obstacles': obstacles, 'climb_routes': climb_routes}

    def _movement_speed_multiplier(self):
        base = float(self.stage_profile.get('speed_mul', 1.0))
        if self.stage_id == 'marsh_shore' and self.player.y >= self.stage_profile.get('ground_y', 118) - 22:
            return base * 0.90
        if self.stage_id == 'inner_city' and self._in_climb_route(self.player.x, self.player.y):
            return base * 1.08
        return base

    def _in_climb_route(self, x, y):
        cx = x + 6
        cy = y + 6
        for route in self.stage_climb_routes:
            if route['x'] - 3 <= cx <= route['x'] + route['w'] + 3 and route['y'] - 4 <= cy <= route['y'] + route['h'] + 4:
                return True
        return False

    def _resolve_stage_movement(self, old_x, old_y, new_x, new_y):
        player_w = 12
        player_h = 12
        climb_ok = self._in_climb_route(new_x, new_y)
        for obstacle in self.stage_obstacles:
            if not self._rects_overlap(new_x, new_y, player_w, player_h, obstacle['x'], obstacle['y'], obstacle['w'], obstacle['h']):
                continue
            if obstacle.get('climbable') and climb_ok:
                continue
            overlap_left = (new_x + player_w) - obstacle['x']
            overlap_right = (obstacle['x'] + obstacle['w']) - new_x
            overlap_top = (new_y + player_h) - obstacle['y']
            overlap_bottom = (obstacle['y'] + obstacle['h']) - new_y
            min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
            if min_overlap == overlap_left:
                new_x = obstacle['x'] - player_w
            elif min_overlap == overlap_right:
                new_x = obstacle['x'] + obstacle['w']
            elif min_overlap == overlap_top:
                new_y = obstacle['y'] - player_h
            else:
                new_y = obstacle['y'] + obstacle['h']
        return new_x, new_y

    def _world_to_scene_x(self, world_x, parallax):
        return int((world_x - (self.camera_x * parallax)) * SCALE)

    def _pixel_fill(self, x0, y0, x1, y1, base, shade, step=12, accent=None):
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=base, outline='')
        for py in range(y0, y1, step):
            for px in range(x0, x1, step):
                selector = ((px // step) * 3 + (py // step) * 5) % 7
                if selector in (0, 3):
                    self.canvas.create_rectangle(px, py, min(x1, px + step // 2), min(y1, py + step // 2), fill=shade, outline='')
                elif accent and selector == 5:
                    self.canvas.create_rectangle(px + (step // 3), py + (step // 3), min(x1, px + step // 2 + 1), min(y1, py + step // 2 + 1), fill=accent, outline='')

    def _pixel_wall_texture(self, x0, y0, x1, y1, wall_color, grain_color, wear_color):
        self._pixel_fill(x0, y0, x1, y1, wall_color, grain_color, step=12, accent=wear_color)
        for row in range(y0 + 10, y1, 18):
            self.canvas.create_line(x0 + 6, row, x1 - 6, row, fill=grain_color)
        for col in range(x0 + 8, x1, 22):
            self.canvas.create_line(col, y0 + 8, col, y1 - 8, fill=wear_color)
        self.canvas.create_rectangle(x0, y0, x1, y1, outline=wear_color)

    def _pixel_roof(self, x0, y0, x1, y1, roof_color, shingle_color, shadow_color):
        self.canvas.create_polygon(x0 - 6, y1, (x0 + x1) // 2, y0, x1 + 6, y1, fill=roof_color, outline=shadow_color)
        row = y0 + 8
        offset = 0
        while row < y1:
            for col in range(x0 + 6 + offset, x1 - 6, 14):
                self.canvas.create_rectangle(col, row, min(x1 - 4, col + 10), min(y1, row + 6), fill=shingle_color, outline='')
            offset = 6 if offset == 0 else 0
            row += 7
        self.canvas.create_line(x0 + 8, y1 - 4, x1 - 8, y1 - 4, fill=shadow_color, width=2)

    def _draw_gothic_facade(self, x0, y0, x1, y1, accent, wear_color, arch_bias, tracery_bias):
        width = max(12, x1 - x0)
        height = max(12, y1 - y0)
        window_count = max(2, min(5, int(width / 28) + int(arch_bias * 1.5)))
        for index in range(window_count):
            center_x = x0 + int(((index + 1) / (window_count + 1)) * width)
            arch_top = y0 + 10 + ((index % 2) * 4)
            arch_bottom = min(y1 - 10, arch_top + max(18, int(height * 0.22)))
            self.canvas.create_line(center_x - 6, arch_bottom, center_x, arch_top, fill=accent)
            self.canvas.create_line(center_x + 6, arch_bottom, center_x, arch_top, fill=accent)
            self.canvas.create_line(center_x - 6, arch_bottom, center_x + 6, arch_bottom, fill=accent)
            self.canvas.create_line(center_x, arch_top + 4, center_x, arch_bottom - 2, fill=wear_color)
        if tracery_bias > 0.7:
            rose_x = (x0 + x1) // 2
            rose_y = y0 + max(12, int(height * 0.18))
            self.canvas.create_oval(rose_x - 10, rose_y - 10, rose_x + 10, rose_y + 10, outline=accent)
            self.canvas.create_line(rose_x - 8, rose_y, rose_x + 8, rose_y, fill=accent)
            self.canvas.create_line(rose_x, rose_y - 8, rose_x, rose_y + 8, fill=accent)
        for buttress in range(x0 + 4, x1 - 6, 20):
            self.canvas.create_line(buttress, y0 + 8, buttress - 2, y1 - 4, fill=wear_color)
            self.canvas.create_line(buttress + 4, y0 + 8, buttress + 6, y1 - 4, fill=wear_color)

    def _pixel_asphalt(self, x0, y0, x1, y1, asphalt_color, grit_color, lane_color, sidewalk_color=None, curb_color=None):
        self._pixel_fill(x0, y0, x1, y1, asphalt_color, grit_color, step=12)
        if sidewalk_color is not None and curb_color is not None:
            curb_y = y0 + 14
            self.canvas.create_rectangle(x0, y0, x1, curb_y, fill=sidewalk_color, outline='')
            for slab in range(x0 + 18, x1, 42):
                self.canvas.create_line(slab, y0 + 2, slab, curb_y - 2, fill=curb_color)
            self.canvas.create_line(x0, curb_y, x1, curb_y, fill=curb_color, width=2)
        lane_y = y0 + ((y1 - y0) // 2)
        for dash_x in range(x0 + 24, x1 - 20, 68):
            self.canvas.create_rectangle(dash_x, lane_y, dash_x + 28, lane_y + 6, fill=lane_color, outline='')
        for crack_x in range(x0 + 16, x1 - 16, 54):
            self.canvas.create_line(crack_x, y0 + 24 + ((crack_x // 7) % 14), crack_x + 16, y0 + 30 + ((crack_x // 11) % 12), fill=grit_color)

    def _ground_contact_y(self, world_y, sprite_h=12):
        ground_y = self.stage_profile.get('ground_y', 120)
        upper = max(ground_y - 56, min(self.stage_spawn_lanes) - 4 if self.stage_spawn_lanes else ground_y - 56)
        lower = min(ground_y - sprite_h + 2, max(self.stage_spawn_lanes) + 4 if self.stage_spawn_lanes else ground_y - sprite_h + 2)
        return max(upper, min(lower, world_y))

    def _draw_stage_item(self, item, parallax, band):
        profile = self.stage_profile
        accent = profile.get('accent', '#7fe7ff')
        ink = profile.get('ink', '#101820')
        detail_ink = profile.get('detail_ink', ink)
        ground = profile.get('ground_color', '#404040')
        surface = profile.get('surface_color', '#606060')
        wall_color = profile.get('wall_color', surface)
        wear_color = profile.get('wear_color', detail_ink)
        roof_color = profile.get('roof_color', ink)
        roof_shadow = profile.get('roof_shadow', detail_ink)
        arch_bias = float(profile.get('arch_bias', 0.6))
        tracery_bias = float(profile.get('tracery_bias', 0.6))
        scene_x = self._world_to_scene_x(item['x'], parallax)
        scene_y = int(item['y'] * SCALE)
        scene_w = int(item['w'] * SCALE)
        scene_h = int(item['h'] * SCALE)
        if scene_x + scene_w < -160 or scene_x > self.scene_w + 160:
            return
        draw_x, draw_y = self._depth_project_point(scene_x, scene_y, band)
        draw_x, draw_y = self._present_xy(draw_x, draw_y)
        item_type = item['type']

        if item_type in ('mangrove', 'reef_spire', 'storm_tower', 'skyline_block', 'water_tank', 'signal_spire', 'tower_block', 'skybridge_stub', 'antenna_stack'):
            self.canvas.create_rectangle(draw_x, draw_y, draw_x + scene_w, draw_y + scene_h, fill=ink, outline='')
        if item_type == 'mangrove':
            self.canvas.create_line(draw_x + scene_w // 3, draw_y + scene_h, draw_x + scene_w // 3, draw_y + scene_h + 20, fill=ink, width=4)
            self.canvas.create_line(draw_x + (scene_w * 2) // 3, draw_y + scene_h, draw_x + (scene_w * 2) // 3, draw_y + scene_h + 18, fill=ink, width=4)
            self.canvas.create_oval(draw_x - 10, draw_y - 6, draw_x + scene_w + 12, draw_y + scene_h // 2, outline=profile.get('fog_color', accent), stipple='gray50')
        elif item_type == 'reef_spire':
            self.canvas.create_polygon(draw_x, draw_y + scene_h, draw_x + scene_w // 2, draw_y, draw_x + scene_w, draw_y + scene_h, fill=ink, outline='')
        elif item_type == 'storm_tower':
            self.canvas.create_rectangle(draw_x + scene_w // 3, draw_y, draw_x + (scene_w * 2) // 3, draw_y + scene_h, fill=ink, outline='')
            self.canvas.create_line(draw_x, draw_y + scene_h // 3, draw_x + scene_w, draw_y + scene_h // 3, fill=accent, width=2)
        elif item_type == 'breaker_lights':
            self.canvas.create_line(draw_x, draw_y, draw_x + scene_w, draw_y, fill=detail_ink, width=2)
            for light in range(4, max(6, scene_w), 12):
                self.canvas.create_oval(draw_x + light - 2, draw_y - 2, draw_x + light + 2, draw_y + 2, fill=accent, outline='')
        elif item_type == 'salt_shack':
            self._pixel_wall_texture(draw_x, draw_y + 20, draw_x + scene_w, draw_y + scene_h, wall_color, detail_ink, wear_color)
            self._pixel_roof(draw_x, draw_y, draw_x + scene_w, draw_y + 24, roof_color, profile.get('surface_color', '#60766c'), roof_shadow)
            self.canvas.create_line(draw_x + 12, draw_y + scene_h, draw_x + 12, draw_y + scene_h + 16, fill=ink, width=3)
            self.canvas.create_line(draw_x + scene_w - 12, draw_y + scene_h, draw_x + scene_w - 12, draw_y + scene_h + 16, fill=ink, width=3)
        elif item_type == 'tide_pylon':
            self.canvas.create_line(draw_x + scene_w // 3, draw_y, draw_x + scene_w // 3, draw_y + scene_h, fill=ink, width=5)
            self.canvas.create_line(draw_x + (scene_w * 2) // 3, draw_y + 8, draw_x + (scene_w * 2) // 3, draw_y + scene_h + 8, fill=ink, width=5)
            self.canvas.create_line(draw_x, draw_y + scene_h // 3, draw_x + scene_w, draw_y + scene_h // 3, fill=surface, width=4)
        elif item_type == 'trawler_hulk':
            self.canvas.create_polygon(draw_x, draw_y + scene_h, draw_x + scene_w // 4, draw_y + scene_h // 2, draw_x + scene_w, draw_y + scene_h // 2, draw_x + scene_w - 10, draw_y + scene_h, fill=ink, outline='')
            self.canvas.create_line(draw_x + scene_w // 2, draw_y + 6, draw_x + scene_w // 2, draw_y + scene_h // 2, fill=accent, width=2)
        elif item_type == 'wrecked_walkway':
            self.canvas.create_line(draw_x, draw_y + scene_h - 4, draw_x + scene_w, draw_y + scene_h - 4, fill=detail_ink, width=4)
            for post in range(6, max(8, scene_w), 16):
                self.canvas.create_line(draw_x + post, draw_y + 4, draw_x + post, draw_y + scene_h + 10, fill=ink, width=3)
            self.canvas.create_line(draw_x + 4, draw_y + scene_h // 2, draw_x + scene_w - 4, draw_y + scene_h // 2, fill=accent, width=2)
        elif item_type == 'reed_bank':
            for idx in range(0, max(6, scene_w), 8):
                self.canvas.create_line(draw_x + idx, draw_y + scene_h, draw_x + idx + 4, draw_y, fill=ink, width=2)
        elif item_type == 'mooring_post':
            self.canvas.create_line(draw_x + scene_w // 2, draw_y, draw_x + scene_w // 2, draw_y + scene_h, fill=ink, width=4)
            self.canvas.create_line(draw_x, draw_y + scene_h // 3, draw_x + scene_w, draw_y + scene_h // 3, fill=accent, width=2)
        elif item_type == 'tide_pipe':
            self.canvas.create_rectangle(draw_x, draw_y + scene_h // 2, draw_x + scene_w, draw_y + scene_h, fill=surface, outline='')
            self.canvas.create_oval(draw_x, draw_y, draw_x + scene_w, draw_y + scene_h // 2, outline=accent, width=2)
        elif item_type == 'foam_band':
            for ridge in range(0, max(8, scene_w), 10):
                self.canvas.create_line(draw_x + ridge, draw_y + scene_h // 2, draw_x + ridge + 8, draw_y + scene_h // 2 - 2, fill=profile.get('water_glow', accent), width=2)
        elif item_type == 'signal_buoy':
            self.canvas.create_line(draw_x + scene_w // 2, draw_y + 4, draw_x + scene_w // 2, draw_y + scene_h, fill=ink, width=3)
            self.canvas.create_oval(draw_x + 2, draw_y, draw_x + scene_w - 2, draw_y + max(10, scene_h // 2), fill=accent, outline='')
        elif item_type == 'kelp_cluster':
            for leaf in range(0, max(6, scene_w), 7):
                self.canvas.create_line(draw_x + leaf, draw_y + scene_h, draw_x + leaf + 2, draw_y + scene_h // 3, fill=detail_ink, width=2)
                self.canvas.create_line(draw_x + leaf + 2, draw_y + scene_h // 2, draw_x + leaf + 6, draw_y, fill=detail_ink, width=2)
        elif item_type == 'water_tank':
            self.canvas.create_oval(draw_x, draw_y, draw_x + scene_w, draw_y + scene_h // 2, fill=ink, outline='')
            self.canvas.create_line(draw_x + 10, draw_y + scene_h // 2, draw_x + 10, draw_y + scene_h, fill=ink, width=4)
            self.canvas.create_line(draw_x + scene_w - 10, draw_y + scene_h // 2, draw_x + scene_w - 10, draw_y + scene_h, fill=ink, width=4)
        elif item_type == 'signal_spire':
            self.canvas.create_line(draw_x + scene_w // 2, draw_y, draw_x + scene_w // 2, draw_y + scene_h, fill=ink, width=4)
            self.canvas.create_line(draw_x, draw_y + scene_h // 4, draw_x + scene_w, draw_y + scene_h // 4, fill=accent, width=2)
            self.canvas.create_line(draw_x + 8, draw_y + scene_h // 2, draw_x + scene_w - 8, draw_y + scene_h // 2, fill=accent, width=2)
        elif item_type == 'billboard_frame':
            self.canvas.create_rectangle(draw_x, draw_y, draw_x + scene_w, draw_y + scene_h // 2, outline=accent, width=3)
            self.canvas.create_line(draw_x + 10, draw_y + scene_h // 2, draw_x + 10, draw_y + scene_h, fill=ink, width=4)
            self.canvas.create_line(draw_x + scene_w - 10, draw_y + scene_h // 2, draw_x + scene_w - 10, draw_y + scene_h, fill=ink, width=4)
        elif item_type == 'transit_gantry':
            self.canvas.create_line(draw_x, draw_y + scene_h, draw_x + scene_w, draw_y + scene_h, fill=ink, width=6)
            self.canvas.create_line(draw_x + 8, draw_y, draw_x + 8, draw_y + scene_h, fill=ink, width=4)
            self.canvas.create_line(draw_x + scene_w - 8, draw_y + 6, draw_x + scene_w - 8, draw_y + scene_h, fill=ink, width=4)
        elif item_type == 'guardrail':
            self.canvas.create_line(draw_x, draw_y + scene_h // 2, draw_x + scene_w, draw_y + scene_h // 2, fill=surface, width=4)
            self.canvas.create_line(draw_x, draw_y + scene_h, draw_x + scene_w, draw_y + scene_h, fill=ink, width=3)
        elif item_type == 'streetlight':
            self.canvas.create_line(draw_x + scene_w // 2, draw_y, draw_x + scene_w // 2, draw_y + scene_h, fill=ink, width=4)
            self.canvas.create_oval(draw_x + scene_w // 2 - 8, draw_y - 4, draw_x + scene_w // 2 + 8, draw_y + 12, fill=accent, outline='')
        elif item_type == 'conduit_box':
            self._pixel_wall_texture(draw_x, draw_y, draw_x + scene_w, draw_y + scene_h, surface, detail_ink, wear_color)
        elif item_type == 'city_block':
            self._pixel_wall_texture(draw_x, draw_y, draw_x + scene_w, draw_y + scene_h, wall_color, detail_ink, wear_color)
            self._pixel_roof(draw_x, draw_y - 16, draw_x + scene_w, draw_y + 10, roof_color, accent, roof_shadow)
            self._draw_gothic_facade(draw_x + 4, draw_y + 6, draw_x + scene_w - 4, draw_y + scene_h - 6, accent, wear_color, arch_bias, tracery_bias)
            for row in range(12, max(14, scene_h - 10), 18):
                for col in range(10, max(12, scene_w - 12), 18):
                    self.canvas.create_rectangle(draw_x + col, draw_y + row, draw_x + col + 8, draw_y + row + 10, fill=accent, outline='')
            for chip in range(draw_x + 6, draw_x + scene_w - 8, 26):
                self.canvas.create_line(chip, draw_y + scene_h - 8, chip + 8, draw_y + scene_h - 14, fill=wear_color)
        elif item_type == 'warehouse':
            self._pixel_wall_texture(draw_x, draw_y + 14, draw_x + scene_w, draw_y + scene_h, wall_color, detail_ink, wear_color)
            self._pixel_roof(draw_x, draw_y - 6, draw_x + scene_w, draw_y + 18, roof_color, profile.get('surface_color', '#6e6256'), roof_shadow)
            self._draw_gothic_facade(draw_x + 6, draw_y + 18, draw_x + scene_w - 6, draw_y + scene_h - 8, accent, wear_color, arch_bias * 0.9, tracery_bias * 0.75)
            self.canvas.create_rectangle(draw_x + 10, draw_y + scene_h - 26, draw_x + scene_w - 12, draw_y + scene_h - 8, fill=wear_color, outline=detail_ink)
        elif item_type == 'skybridge':
            self._pixel_wall_texture(draw_x, draw_y, draw_x + scene_w, draw_y + scene_h, surface, detail_ink, wear_color)
            self.canvas.create_line(draw_x, draw_y + scene_h, draw_x + scene_w, draw_y + scene_h, fill=accent, width=2)
        elif item_type == 'rooftop_walk':
            self._pixel_fill(draw_x, draw_y, draw_x + scene_w, draw_y + scene_h, surface, detail_ink, step=10)
            for stripe in range(4, max(6, scene_w), 16):
                self.canvas.create_line(draw_x + stripe, draw_y, draw_x + stripe, draw_y + scene_h, fill=accent, width=1)
        elif item_type == 'fire_escape':
            self.canvas.create_line(draw_x + 4, draw_y, draw_x + 4, draw_y + scene_h, fill=ink, width=3)
            self.canvas.create_line(draw_x + scene_w - 4, draw_y, draw_x + scene_w - 4, draw_y + scene_h, fill=ink, width=3)
            for step in range(10, max(12, scene_h), 18):
                self.canvas.create_line(draw_x, draw_y + step, draw_x + scene_w, draw_y + step, fill=accent, width=2)
        elif item_type == 'neon_panel':
            self.canvas.create_rectangle(draw_x, draw_y, draw_x + scene_w, draw_y + scene_h, fill=accent, outline='')
            self.canvas.create_line(draw_x + 4, draw_y + scene_h // 2, draw_x + scene_w - 4, draw_y + scene_h // 2, fill=ink, width=2)
        elif item_type == 'street_barrier':
            self._pixel_fill(draw_x, draw_y + scene_h // 2, draw_x + scene_w, draw_y + scene_h, surface, detail_ink, step=8)
            self.canvas.create_rectangle(draw_x, draw_y + scene_h // 2, draw_x + scene_w, draw_y + scene_h, outline=ink)
        elif item_type == 'signal_post':
            self.canvas.create_line(draw_x + scene_w // 2, draw_y, draw_x + scene_w // 2, draw_y + scene_h, fill=ink, width=4)
            self.canvas.create_oval(draw_x + scene_w // 2 - 6, draw_y + 8, draw_x + scene_w // 2 + 6, draw_y + 20, fill=accent, outline='')
        elif item_type == 'steam_vent':
            self.canvas.create_rectangle(draw_x, draw_y + scene_h // 2, draw_x + scene_w, draw_y + scene_h, fill=surface, outline='')
            self.canvas.create_oval(draw_x - 8, draw_y - 12, draw_x + scene_w + 8, draw_y + scene_h // 2, outline=profile.get('fog_color', accent), stipple='gray50')

    def _draw_stage_background(self):
        profile = self.stage_profile
        horizon_y = int(profile.get('horizon_y', 48) * SCALE)
        self.canvas.create_rectangle(*self._present_rect(0, 0, self.scene_w, horizon_y), fill=profile.get('sky_top', '#203040'), outline='')
        self.canvas.create_rectangle(*self._present_rect(0, horizon_y, self.scene_w, horizon_y + 80), fill=profile.get('sky_mid', '#40526a'), outline='')
        self.canvas.create_rectangle(*self._present_rect(0, horizon_y + 80, self.scene_w, self.scene_h), fill=profile.get('sky_low', '#6b7688'), outline='')
        for band_y in range(0, horizon_y + 90, 24):
            px0, py0, px1, py1 = self._present_rect(0, band_y, self.scene_w, band_y)
            tone = profile.get('fog_color', '#b9d7c9') if (band_y // 24) % 2 == 0 else profile.get('sky_mid', '#40526a')
            self.canvas.create_line(px0, py0, px1, py1, fill=tone)
        ground_y = int(profile.get('ground_y', 120) * SCALE)
        surface_h = max(26, self.scene_h - ground_y)
        if self.stage_id == 'marsh_shore':
            self.canvas.create_rectangle(*self._present_rect(0, ground_y, self.scene_w, self.scene_h), fill=profile.get('ground_color', '#404040'), outline='')
            self.canvas.create_rectangle(*self._present_rect(0, ground_y + surface_h // 3, self.scene_w, self.scene_h), fill=profile.get('surface_color', '#606060'), outline='')
            water_y = ground_y + 10
            self.canvas.create_rectangle(*self._present_rect(0, water_y, self.scene_w, min(self.scene_h, water_y + 90)), fill=profile.get('water_color', '#516c72'), outline='')
            self.canvas.create_rectangle(*self._present_rect(0, ground_y - 14, self.scene_w, ground_y + 12), fill='#73887c', outline='')
            for foam in range(0, self.scene_w + 40, 70):
                wave_y = water_y + 12 + ((foam // 18) % 14)
                self.canvas.create_line(self.viewport_x + foam, self.viewport_y + wave_y, self.viewport_x + foam + 32, self.viewport_y + wave_y - 2, fill=profile.get('water_glow', '#a8d7d6'), width=2)
                self.canvas.create_line(self.viewport_x + foam + 18, self.viewport_y + wave_y + 18, self.viewport_x + foam + 62, self.viewport_y + wave_y + 16, fill=profile.get('fog_color', '#b9d7c9'))
            for ripple in range(0, self.scene_w, 90):
                self.canvas.create_line(self.viewport_x + ripple, self.viewport_y + water_y + (ripple // 12) % 18, self.viewport_x + ripple + 60, self.viewport_y + water_y + (ripple // 12) % 18, fill=profile.get('fog_color', '#b9d7c9'))
        else:
            sidewalk_top = max(ground_y - 18, 0)
            street_top = min(self.scene_h, ground_y + 20)
            px0, py0, px1, py1 = self._present_rect(0, sidewalk_top, self.scene_w, self.scene_h)
            self._pixel_asphalt(px0, py0, px1, py1, profile.get('asphalt_color', '#2b2c31'), profile.get('grit_color', '#80756f'), profile.get('lane_color', '#c0ad74'), profile.get('sidewalk_color', '#8e8782'), profile.get('sidewalk_edge', '#615d5c'))
            curb_y = self.viewport_y + street_top
            self.canvas.create_line(self.viewport_x, curb_y, self.viewport_x + self.scene_w, curb_y, fill=profile.get('sidewalk_edge', '#615d5c'), width=2)
            for oil_x in range(self.viewport_x + 40, self.viewport_x + self.scene_w - 60, 92):
                self.canvas.create_oval(oil_x, curb_y + 34, oil_x + 30, curb_y + 46, outline=profile.get('wear_color', '#2b2a2f'))

        for item in self.stage_layers.get('far', []):
            self._draw_stage_item(item, self.stage_profile['parallax']['far'], 'far')
        for item in self.stage_layers.get('mid', []):
            self._draw_stage_item(item, self.stage_profile['parallax']['mid'], 'near')

    def _draw_stage_foreground(self):
        for item in self.stage_layers.get('near', []):
            self._draw_stage_item(item, self.stage_profile['parallax']['near'], 'near')

    def _draw_viewport_scanlines(self):
        left = self.viewport_x
        right = self.viewport_x + self.scene_w
        for y in range(self.viewport_y + 6, self.viewport_y + self.scene_h, 12):
            self.canvas.create_line(left, y, right, y, fill='#0f1624')

    def _draw_central_shell(self):
        edge_color = self.stage_profile.get('accent', '#7fe7ff')
        shadow_color = '#071018'
        left = self.viewport_x - 94
        right = self.viewport_x + self.scene_w + 94
        top = self.viewport_y - 8
        bottom = self.viewport_y + self.scene_h + 8
        self.canvas.create_polygon(0, 0, left, top, left, bottom, 0, WIN_H, fill=shadow_color, outline='')
        self.canvas.create_polygon(WIN_W, 0, right, top, right, bottom, WIN_W, WIN_H, fill=shadow_color, outline='')
        self.canvas.create_line(left + 10, top + 40, left + 10, bottom - 40, fill=edge_color, stipple='gray50', width=2)
        self.canvas.create_line(right - 10, top + 40, right - 10, bottom - 40, fill=edge_color, stipple='gray50', width=2)
        if self.show_debug:
            safe_x0, safe_y0, safe_x1, safe_y1 = self._window_safe_rect()
            self.canvas.create_rectangle(safe_x0, safe_y0, safe_x1, safe_y1, outline='#f2d35a', dash=(8, 6), width=2)

    def _panel_points(self, x0, y0, x1, y1, notch=18):
        return [
            x0 + notch, y0,
            x1 - notch, y0,
            x1, y0 + notch,
            x1, y1 - notch,
            x1 - notch, y1,
            x0 + notch, y1,
            x0, y1 - notch,
            x0, y0 + notch,
        ]

    def _draw_pixel_panel(self, x0, y0, x1, y1, fill, outline, glow=None, notch=18, rib_count=4):
        points = self._panel_points(x0, y0, x1, y1, notch)
        self.canvas.create_polygon(points, fill=fill, outline=outline, width=3)
        inset = 8
        inner_points = self._panel_points(x0 + inset, y0 + inset, x1 - inset, y1 - inset, max(8, notch - 6))
        self.canvas.create_polygon(inner_points, fill='', outline='#0f1824', width=2)
        if glow:
            self.canvas.create_polygon(self._panel_points(x0 - 4, y0 - 4, x1 + 4, y1 + 4, notch + 4), fill='', outline=glow, stipple='gray50', width=2)
        width = max(1, x1 - x0)
        for rib in range(rib_count):
            rib_x = x0 + 18 + int((rib / max(1, rib_count)) * max(20, width - 42))
            self.canvas.create_line(rib_x, y0 + 16, rib_x, y1 - 16, fill='#1a2636')
        self.canvas.create_rectangle(x0 + 12, y0 + 10, x0 + 46, y0 + 18, fill=outline, outline='')
        self.canvas.create_rectangle(x1 - 46, y1 - 18, x1 - 12, y1 - 10, fill=outline, outline='')

    def _draw_panel_meter(self, x0, y0, x1, y1, ratio, fill, empty, segments=10, reverse=False):
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=empty, outline='')
        gap = 4
        segment_w = max(8, int(((x1 - x0) - ((segments - 1) * gap)) / max(1, segments)))
        active = int(round(max(0.0, min(1.0, ratio)) * segments))
        for index in range(segments):
            start = segments - 1 - index if reverse else index
            sx = x0 + (start * (segment_w + gap))
            color = fill if index < active else '#1c2734'
            self.canvas.create_rectangle(sx, y0 + 2, sx + segment_w, y1 - 2, fill=color, outline='')

    def _draw_word_burst(self, cx, cy, text, fill, outline, text_fill, scale=1.0):
        burst_w = int(188 * scale)
        burst_h = int(66 * scale)
        points = [
            cx - burst_w, cy - 10,
            cx - burst_w // 2, cy - burst_h,
            cx - 18, cy - burst_h // 2,
            cx + burst_w // 3, cy - burst_h,
            cx + burst_w, cy - 8,
            cx + burst_w // 2, cy + burst_h,
            cx + 8, cy + burst_h // 2,
            cx - burst_w // 2, cy + burst_h,
        ]
        self.canvas.create_polygon(points, fill=fill, outline=outline, width=3)
        self.canvas.create_text(cx + 6, cy + 6, text=text, fill='#16070a', font=self._font_display(int(18 * scale), 'bold'), justify='center')
        self.canvas.create_text(cx, cy, text=text, fill=text_fill, font=self._font_display(int(18 * scale), 'bold'), justify='center')

    def _get_scaled_asset_variant(self, key, scale_mul=1.0):
        if scale_mul <= 1.01:
            return self.scaled.get(key) or self.assets.get(key)
        if not PIL_AVAILABLE:
            return self.scaled.get(key) or self.assets.get(key)
        pil_image = self.assets_pil.get(key)
        if pil_image is None:
            return self.scaled.get(key) or self.assets.get(key)
        cache_key = ('variant', key, round(scale_mul, 2))
        if cache_key in self.render_cache:
            return self.render_cache[cache_key]
        resized = pil_image.resize((max(1, int(pil_image.width * SCALE * scale_mul)), max(1, int(pil_image.height * SCALE * scale_mul))), Image.Resampling.NEAREST)
        photo_image = ImageTk.PhotoImage(resized)
        self.render_cache[cache_key] = photo_image
        return photo_image

    def _current_metric_values(self):
        context = self._sprite_context()
        metrics = self.depth_metrics or {}
        hope_signal = min(1.0, (float(metrics.get('confidence', 0.0)) * 0.35) + (float(metrics.get('proximity', 0.35)) * 0.25) + (float(metrics.get('eye_open', 0.45)) * 0.15) + (float(metrics.get('dilation', 0.45)) * 0.15) + (float(metrics.get('edge_density', 0.0)) * 0.10))
        return {
            'AGG': float(context.get('aggression', 0.0)),
            'GUARD': float(context.get('defense', 0.0)),
            'DRIVE': float(context.get('movement_energy', 0.0)),
            'HOPE': hope_signal,
        }

    def _draw_profile_stamp(self, cx, cy, size, primary, secondary=None):
        motif = self.stage_profile.get('profile_motif', 'spire')
        secondary = secondary or self.stage_profile.get('ui_trim', primary)
        if motif == 'fang':
            tooth = max(4, size // 5)
            for index in range(-2, 3):
                tx = cx + (index * tooth)
                self.canvas.create_polygon(tx - tooth, cy - tooth, tx + tooth, cy - tooth, tx, cy + tooth, fill=primary, outline=secondary)
        elif motif == 'rose':
            step = max(4, size // 4)
            self.canvas.create_rectangle(cx - step * 2, cy - step * 2, cx + step * 2, cy + step * 2, outline=primary, width=2)
            self.canvas.create_rectangle(cx - step, cy - step, cx + step, cy + step, outline=secondary, width=2)
            self.canvas.create_line(cx - step * 2, cy, cx + step * 2, cy, fill=primary, width=2)
            self.canvas.create_line(cx, cy - step * 2, cx, cy + step * 2, fill=primary, width=2)
        else:
            step = max(4, size // 4)
            self.canvas.create_polygon(cx, cy - step * 3, cx + step * 2, cy + step * 2, cx - step * 2, cy + step * 2, fill=primary, outline=secondary, width=2)
            self.canvas.create_rectangle(cx - step // 2, cy - step, cx + step // 2, cy + step * 3, fill=secondary, outline='')

    def _draw_mist_block(self, center_x, center_y, span_x, span_y, color):
        bands = 5
        for index in range(bands):
            inset = index * max(6, span_x // 12)
            height = max(8, (span_y // bands) + 2)
            x0 = center_x - span_x + inset
            x1 = center_x + span_x - inset
            y0 = center_y - span_y + (index * height)
            y1 = y0 + height - 2
            self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, stipple='gray50')

    def _draw_pixel_light_bloom(self, center_x, center_y, span_x, span_y, color, bands=4):
        for index in range(bands):
            inset_x = index * max(4, span_x // 10)
            inset_y = index * max(3, span_y // 10)
            x0 = center_x - span_x + inset_x
            x1 = center_x + span_x - inset_x
            y0 = center_y - span_y + inset_y
            y1 = center_y + span_y - inset_y
            if x1 <= x0 or y1 <= y0:
                continue
            self.canvas.create_rectangle(x0, y0, x1, y1, outline=color if index == 0 else '', fill=color if index > 0 else '', stipple='gray50')

    def _draw_pixel_bracket(self, cx, cy, width, height, color, weight=4):
        left = cx - width // 2
        right = cx + width // 2
        top = cy - height // 2
        bottom = cy + height // 2
        self.canvas.create_rectangle(left, top, left + weight, bottom, fill=color, outline='')
        self.canvas.create_rectangle(right - weight, top, right, bottom, fill=color, outline='')
        self.canvas.create_rectangle(left, top, left + width // 3, top + weight, fill=color, outline='')
        self.canvas.create_rectangle(right - width // 3, top, right, top + weight, fill=color, outline='')
        self.canvas.create_rectangle(left, bottom - weight, left + width // 3, bottom, fill=color, outline='')
        self.canvas.create_rectangle(right - width // 3, bottom - weight, right, bottom, fill=color, outline='')

    def _draw_metric_rack(self, x0, y0, metrics_map, align='left'):
        primary = self.stage_profile.get('metric_primary', '#f3dfa1')
        secondary = self.stage_profile.get('metric_secondary', '#7fd9e8')
        warning = self.stage_profile.get('metric_warning', '#ff8d72')
        meter_segments = int(self.stage_profile.get('meter_segments', 12))
        spacing = 84
        labels = list(metrics_map.items())
        if align == 'right':
            labels = list(reversed(labels))
        for index, (label, value) in enumerate(labels):
            base_x = x0 + (index * spacing)
            edge = warning if value > 0.76 and label in ('AGG', 'HOPE') else primary
            self.canvas.create_text(base_x, y0, anchor='nw', text=label, fill=edge, font=self._font_caption(11, 'bold'))
            for segment in range(6):
                sx0 = base_x
                sy0 = y0 + 18 + (segment * 7)
                tone = secondary if segment < int(round(value * 6)) else '#1a2532'
                self.canvas.create_rectangle(sx0, sy0, sx0 + 26, sy0 + 5, fill=tone, outline='')
            self.canvas.create_text(base_x + 34, y0 + 18, anchor='nw', text=f'{int(value * 99):02d}', fill=self.stage_profile.get('ui_text', '#fff0df'), font=self._font_body(10, 'bold'))
            if index == 0:
                self._draw_profile_stamp(base_x + 50, y0 + 36, 20, edge, secondary)

    def _draw_visual_hud(self):
        player_ratio = max(0.0, min(1.0, self.player.hp / max(1, self.player.max_hp)))
        boss_ratio = self._boss_hp_ratio() if self.boss else 0.0
        nanocells = getattr(self.player, 'nanocell_count', 0)
        combo = getattr(self.player, 'combo_count', 0)
        accent = self.stage_profile.get('accent', '#7fe7ff')
        frame_glow = self.stage_profile.get('frame_glow', '#f2d35a')
        ui_fill = self.stage_profile.get('ui_panel_fill', '#08111a')
        ui_line = self.stage_profile.get('ui_panel_line', accent)
        ui_text = self.stage_profile.get('ui_text', '#fff0df')
        ui_muted = self.stage_profile.get('ui_muted', '#aab6c2')
        meter_segments = int(self.stage_profile.get('meter_segments', 12))
        metric_values = self._current_metric_values()
        left_x0 = self.viewport_x + 22
        left_y0 = self.viewport_y + self.scene_h - 126
        left_x1 = left_x0 + 384
        left_y1 = left_y0 + 94
        self._draw_pixel_panel(left_x0, left_y0, left_x1, left_y1, ui_fill, ui_line, glow=frame_glow, notch=self.stage_profile.get('panel_notch', 20), rib_count=self.stage_profile.get('panel_ribs', 5))
        self.canvas.create_text(left_x0 + 26, left_y0 + 20, anchor='nw', text=f'REI FRAME  |  {self.stage_profile.get("profile_label", "CATALOG")}'.upper(), fill=ui_text, font=self._font_caption(14, 'bold'))
        self.canvas.create_text(left_x0 + 26, left_y0 + 48, anchor='nw', text=f'HP {int(self.player.hp)}/{int(self.player.max_hp)}', fill=ui_text, font=self._font_body(14, 'bold'))
        self._draw_panel_meter(left_x0 + 112, left_y0 + 42, left_x0 + 252, left_y0 + 62, player_ratio, accent, '#111926', segments=meter_segments)
        for index in range(max(1, nanocells + 1)):
            cx0 = left_x0 + 26 + (index * 28)
            fill = '#d8fdff' if index < nanocells else '#122133'
            self.canvas.create_rectangle(cx0, left_y1 - 28, cx0 + 18, left_y1 - 10, fill=fill, outline=frame_glow)
        self._draw_metric_rack(left_x0 + 264, left_y0 + 18, {'AGG': metric_values['AGG'], 'DRIVE': metric_values['DRIVE']})
        if self.boss:
            right_x1 = self.viewport_x + self.scene_w - 22
            right_y0 = self.viewport_y + 26
            right_x0 = right_x1 - 430
            right_y1 = right_y0 + 88
            self._draw_pixel_panel(right_x0, right_y0, right_x1, right_y1, blend_hex(ui_fill, '#220d0f', 0.55), '#ff8a6b', glow=frame_glow, notch=max(16, self.stage_profile.get('panel_notch', 20) - 2), rib_count=max(4, self.stage_profile.get('panel_ribs', 5) - 1))
            self.canvas.create_text(right_x1 - 24, right_y0 + 18, anchor='ne', text=self.boss_name, fill='#f8e2d9', font=self._font_caption(14, 'bold'))
            self.canvas.create_text(right_x1 - 24, right_y0 + 42, anchor='ne', text=f'PHASE {self._boss_phase_index() + 1}', fill='#ffb39c', font=self._font_body(13, 'bold'))
            self._draw_panel_meter(right_x0 + 140, right_y0 + 40, right_x1 - 24, right_y0 + 60, boss_ratio, '#ff8a6b', '#2a1217', segments=meter_segments, reverse=True)
            self._draw_metric_rack(right_x0 + 22, right_y0 + 16, {'HOPE': metric_values['HOPE'], 'GUARD': metric_values['GUARD']})
        for index in range(combo):
            combo_x = self.viewport_x + (self.scene_w // 2) - 86 + (index * 62)
            combo_y = self.viewport_y + self.scene_h - 108
            self._draw_word_burst(combo_x, combo_y, str(index + 1), self.stage_profile.get('burst_fill', '#65120f'), self.stage_profile.get('burst_outline', '#f2d35a'), '#fff0db', scale=0.52)

    def _draw_duel_orb(self):
        split, _ = self._duel_balance()
        orb_r = 54
        orb_x = self.viewport_x + (self.scene_w // 2)
        orb_y = self.viewport_y + 70
        primary = self.stage_profile.get('metric_primary', '#f3dfa1')
        secondary = self.stage_profile.get('metric_secondary', '#7fd9e8')
        panel = [orb_x - orb_r, orb_y - orb_r // 2, orb_x - orb_r // 2, orb_y - orb_r, orb_x + orb_r // 2, orb_y - orb_r, orb_x + orb_r, orb_y - orb_r // 2, orb_x + orb_r, orb_y + orb_r // 2, orb_x + orb_r // 2, orb_y + orb_r, orb_x - orb_r // 2, orb_y + orb_r, orb_x - orb_r, orb_y + orb_r // 2]
        self.canvas.create_polygon(panel, fill=self.stage_profile.get('ui_panel_fill', '#081018'), outline=primary, width=3)
        split_x = int((orb_x - orb_r + 8) + ((orb_r * 2 - 16) * split))
        self.canvas.create_polygon([orb_x - orb_r + 8, orb_y - orb_r + 8, split_x, orb_y - orb_r + 8, split_x, orb_y + orb_r - 8, orb_x - orb_r + 8, orb_y + orb_r - 8], fill='#69d2e7', outline='')
        self.canvas.create_polygon([split_x, orb_y - orb_r + 8, orb_x + orb_r - 8, orb_y - orb_r + 8, orb_x + orb_r - 8, orb_y + orb_r - 8, split_x, orb_y + orb_r - 8], fill='#b14f46', outline='')
        wave_y = orb_y + int(math.sin(time.time() * 4.0) * 5)
        segment_w = 12
        for sx in range(orb_x - orb_r + 14, orb_x + orb_r - 14, segment_w + 4):
            self.canvas.create_rectangle(sx, wave_y - 3, min(sx + segment_w, orb_x + orb_r - 14), wave_y + 3, fill=primary, outline='')
        self.canvas.create_rectangle(orb_x - 8, orb_y - 8, orb_x + 8, orb_y + 8, fill=primary, outline='')
        self._draw_profile_stamp(orb_x, orb_y - 72, 22, primary, secondary)

    def _draw_playfield_tension(self):
        player_px = self.viewport_x + int((self.player.x - int(self.camera_x)) * SCALE) + 48
        player_py = self.viewport_y + int(self.player.y * SCALE) + 60
        boss_px = player_px + 160
        boss_py = player_py - 30
        metrics_map = self._current_metric_values()
        primary = self.stage_profile.get('metric_primary', '#f3dfa1')
        secondary = self.stage_profile.get('metric_secondary', '#7fd9e8')
        warning = self.stage_profile.get('metric_warning', '#ff8d72')
        if self.boss:
            boss_px = self.viewport_x + int((self.boss.x - int(self.camera_x)) * SCALE) + 90
            boss_py = self.viewport_y + int(self.boss.y * SCALE) + 72
        self._draw_pixel_bracket(player_px - 90, player_py - 64, 42, 42, secondary, weight=4)
        self._draw_pixel_bracket(player_px + 90, player_py + 64, 42, 42, secondary, weight=4)
        if self.boss:
            self._draw_pixel_bracket(boss_px - 134, boss_py - 96, 50, 50, warning, weight=4)
            self._draw_pixel_bracket(boss_px + 134, boss_py + 96, 50, 50, warning, weight=4)
            bridge_width = max(18, int((boss_px - player_px) * 0.5))
            self.canvas.create_rectangle(player_px + 18, player_py - 16, player_px + 18 + bridge_width, player_py - 10, fill=primary, outline='')
            if getattr(self.boss, 'telegraph', 0) > 0:
                self._draw_profile_stamp(boss_px, boss_py - 92, 22, warning, primary)
        if getattr(self.player, 'dodge_timer', 0) > 0:
            self._draw_profile_stamp(player_px - 64 if getattr(self.player, 'facing', 'right') == 'right' else player_px + 64, player_py - 34, 18, secondary, primary)

    def _draw_title_overlay(self):
        frame_glow = self.stage_profile.get('frame_glow', '#f2d35a')
        accent = self.stage_profile.get('accent', '#7fe7ff')
        x0 = self.viewport_x + 58
        x1 = self.viewport_x + self.scene_w - 58
        y0 = self.viewport_y + 76
        y1 = self.viewport_y + self.scene_h - 112
        self._draw_pixel_panel(x0, y0, x1, y1, self.stage_profile.get('ui_panel_fill', '#09111a'), frame_glow, glow=self.stage_profile.get('ui_panel_glow', accent), notch=self.stage_profile.get('panel_notch', 26), rib_count=self.stage_profile.get('panel_ribs', 8))
        self._draw_word_burst(WIN_W // 2, self.viewport_y + 188, 'KAIJU\nGAIDEN', self.stage_profile.get('burst_fill', '#5d120c'), self.stage_profile.get('burst_outline', frame_glow), '#fff3d9', scale=1.36)
        self.canvas.create_text(WIN_W // 2, self.viewport_y + 284, text=self.stage_profile.get('profile_tagline', 'MONSTER-MANGA DUEL BUILT INTO THE CITY SHELL').upper(), fill=accent, font=self._font_body(18, 'bold'))
        self.canvas.create_text(WIN_W // 2, self.viewport_y + 314, text=f"PROFILE EXTENSION: {self.stage_profile.get('profile_label', 'CATALOG').upper()}  |  PANELS GROW FROM THE STREET SHELL", fill=self.stage_profile.get('ui_muted', '#a8bbca'), font=self._font_caption(14))
        self._draw_profile_stamp(WIN_W // 2, self.viewport_y + 368, 32, frame_glow, self.stage_profile.get('metric_secondary', accent))
        panel_y = self.viewport_y + self.scene_h - 264
        panel_w = 248
        gap = 24
        panel_pitch = panel_w + gap
        pulse = 0.5 + (0.5 * math.sin(time.time() * 7.0))
        focus_index = getattr(self, 'menu_focus_float', float(self.menu_index))
        for index, label in enumerate(self.menu_options):
            selected = index == self.menu_index
            grow = 1.0 + (0.08 * pulse if selected else -0.02)
            width = int(panel_w * grow)
            height = int((92 if selected else 84) * grow)
            center_x = int((WIN_W // 2) + ((index - focus_index) * panel_pitch))
            px0 = center_x - (width // 2)
            py0 = panel_y - ((height - 84) // 2)
            px1 = px0 + width
            py1 = py0 + height
            fill = self.stage_profile.get('burst_fill', '#1a0d10') if selected else self.stage_profile.get('ui_panel_fill', '#081018')
            outline = frame_glow if selected else self.stage_profile.get('ui_trim', '#31465d')
            glow = accent if selected else None
            self._draw_pixel_panel(px0, py0, px1, py1, fill, outline, glow=glow, notch=max(14, self.stage_profile.get('panel_notch', 18) - 4), rib_count=max(3, self.stage_profile.get('panel_ribs', 5) - 3))
            if selected:
                self.canvas.create_rectangle(px0 + 14, py0 + 14, px0 + 54, py0 + 26, fill=accent, outline='')
                self._draw_pixel_light_bloom(center_x, py1 + 18, width // 2, 18, accent, bands=3)
            self.canvas.create_text((px0 + px1) // 2, py0 + 36, text=label.upper(), fill=self.stage_profile.get('ui_text', '#fff1dd') if selected else '#d7dde8', font=self._font_display(18 if selected else 16, 'bold'))
            self.canvas.create_text((px0 + px1) // 2, py1 - 22, text='PRESS START' if selected else 'SWITCH', fill=self.stage_profile.get('metric_secondary', '#ffb197') if selected else self.stage_profile.get('ui_muted', '#8fa3bb'), font=self._font_caption(11, 'bold'))
        self.canvas.create_text(WIN_W // 2, self.viewport_y + self.scene_h - 126, text='LEFT / RIGHT OR DPAD TO CUT BETWEEN PANELS  |  A / START TO ENTER', fill=self.stage_profile.get('ui_text', '#d1d8e3'), font=self._font_caption(13, 'bold'))

    def _draw_splash_overlay(self):
        frame_glow = self.stage_profile.get('frame_glow', '#f2d35a')
        self.canvas.create_rectangle(self.viewport_x + 140, self.viewport_y + 150, self.viewport_x + self.scene_w - 140, self.viewport_y + self.scene_h - 150, fill='#0b1320', outline=frame_glow, width=3)
        for y in range(self.viewport_y + 168, self.viewport_y + self.scene_h - 150, 18):
            self.canvas.create_line(self.viewport_x + 160, y, self.viewport_x + self.scene_w - 160, y, fill='#162338')

    def _cinematic_progress(self):
        duration = max(1, int(getattr(self, 'cinematic_duration', 2600)))
        remaining = max(0, int(getattr(self, 'cinematic_timer', duration)))
        return max(0.0, min(1.0, 1.0 - (remaining / duration)))

    def _cinematic_shot(self):
        shots = [
            {
                'name': 'WIDE RUSH',
                'player_scale': 1.52,
                'boss_scale': 1.12,
                'player_pos': (170, 452),
                'boss_pos': (994, 344),
                'camera_amp': 18,
                'line1': 'VAINCOIL, THE PEACOCK-SERPENT, PAINTS THE HARBOR SKY WITH KNIFE-FEATHERS.',
                'line2': 'MORVASA, THE GORGON REPTILE JAGUAR, CLIMBS THE BRICK FACE ON STONE-BENT CLAWS.',
            },
            {
                'name': 'CLOSE FEATHER',
                'player_scale': 1.92,
                'boss_scale': 0.92,
                'player_pos': (264, 388),
                'boss_pos': (1116, 412),
                'camera_amp': 26,
                'line1': 'VAINCOIL FANS HIS THROAT-CREST, THEN DRIVES A COLOR-STRIKE THROUGH THE RAIN.',
                'line2': 'THE CAMERA RUSHES IN SO FAST THE WHOLE STREET FEELS LIKE A LUNGE.',
            },
            {
                'name': 'JAGUAR SNAP',
                'player_scale': 1.18,
                'boss_scale': 1.46,
                'player_pos': (186, 476),
                'boss_pos': (874, 302),
                'camera_amp': 20,
                'line1': 'MORVASA SHOWS THE GORGON MASK: SCALE, FANG, JAGUAR SPINE, AND A STATUE-MAKING GLARE.',
                'line2': 'HE HITS THE ASPHALT IN A SIDEWAYS SLAM THAT KICKS THE FRAME OFF ITS AXIS.',
            },
            {
                'name': 'FINAL LOCK',
                'player_scale': 1.62,
                'boss_scale': 1.34,
                'player_pos': (212, 430),
                'boss_pos': (930, 332),
                'camera_amp': 14,
                'line1': 'FEATHER AGAINST STONE. SERPENT ARC AGAINST JAGUAR MAW. THE CITY CHOOSES A DUEL LANE.',
                'line2': 'REI STEPS INTO THE CUT BETWEEN THEM BEFORE THE NEXT IMPACT CAN DECIDE THE BLOCK.',
            },
        ]
        progress = self._cinematic_progress()
        index = min(len(shots) - 1, int(progress * len(shots)))
        return shots[index]

    def _draw_cinematic_scene(self):
        shot = self._cinematic_shot()
        pulse = 0.5 + (0.5 * math.sin(time.time() * 8.5))
        cinematic_player = self._get_scaled_asset_variant('player', shot['player_scale']) or self._current_cinematic_image('player', scaled=True) or self.s_img_player
        cinematic_boss = self._get_scaled_asset_variant(self._current_boss_asset_key(), shot['boss_scale']) or self._current_cinematic_image('boss', scaled=True) or self.s_img_boss
        jitter_x = int(math.sin(time.time() * 18.0) * shot['camera_amp'])
        jitter_y = int(math.cos(time.time() * 14.0) * max(6, shot['camera_amp'] // 2))
        left_x, left_y = self._present_xy(shot['player_pos'][0] + jitter_x, shot['player_pos'][1] + jitter_y)
        right_x, right_y = self._present_xy(shot['boss_pos'][0] - jitter_x, shot['boss_pos'][1] - jitter_y)
        self._draw_pixel_light_bloom(WIN_W // 2, self.viewport_y + 220, 180, 58, self.stage_profile.get('accent', '#7fe7ff'), bands=3)
        if cinematic_player:
            for index in range(1, 3):
                self.canvas.create_image(left_x - (index * 22), left_y + (index * 6), image=cinematic_player, anchor='nw')
            self.canvas.create_image(left_x, left_y, image=cinematic_player, anchor='nw')
        else:
            self.canvas.create_rectangle(left_x, left_y, left_x + 96, left_y + 96, fill='#6ad0ff')
        if cinematic_boss:
            for index in range(1, 3):
                self.canvas.create_image(right_x + (index * 18), right_y - (index * 4), image=cinematic_boss, anchor='nw')
            self.canvas.create_image(right_x, right_y, image=cinematic_boss, anchor='nw')
        else:
            self.canvas.create_rectangle(right_x, right_y, right_x + 220, right_y + 220, fill='#701b20')
        self._draw_pixel_bracket(left_x + 120, left_y + 96, 118, 118, self.stage_profile.get('metric_secondary', '#7fd9e8'), weight=5)
        self._draw_pixel_bracket(right_x + 146, right_y + 112, 146, 146, self.stage_profile.get('metric_warning', '#ff8d72'), weight=5)
        slash_y = self.viewport_y + 258 + int(pulse * 12)
        self.canvas.create_rectangle(self.viewport_x + 180, slash_y, self.viewport_x + self.scene_w - 180, slash_y + 10, fill=self.stage_profile.get('metric_primary', '#f3dfa1'), outline='')
        self.canvas.create_text(self.viewport_x + 110, self.viewport_y + 94, anchor='nw', text=shot['name'], fill='#fff1dd', font=self._font_display(18, 'bold'))

    def _draw_cinematic_overlay(self):
        shot = self._cinematic_shot()
        frame_glow = self.stage_profile.get('frame_glow', '#f2d35a')
        self.canvas.create_rectangle(self.viewport_x + 44, self.viewport_y + 44, self.viewport_x + self.scene_w - 44, self.viewport_y + self.scene_h - 44, outline=frame_glow, width=2)
        self.canvas.create_rectangle(self.viewport_x + 72, self.viewport_y + self.scene_h - 192, self.viewport_x + self.scene_w - 72, self.viewport_y + self.scene_h - 78, fill='#081018', outline=frame_glow, width=2)
        self.canvas.create_text(self.viewport_x + 96, self.viewport_y + self.scene_h - 170, anchor='nw', text=shot['line1'], fill='#f7e7d2', font=self._font_body(16, 'bold'), width=self.scene_w - 220)
        self.canvas.create_text(self.viewport_x + 96, self.viewport_y + self.scene_h - 126, anchor='nw', text=shot['line2'], fill='#b7c7d8', font=self._font_caption(14), width=self.scene_w - 220)
        self.canvas.create_text(self.viewport_x + self.scene_w - 92, self.viewport_y + self.scene_h - 92, anchor='ne', text='B / START TO CUT AHEAD', fill='#ffbe97', font=self._font_caption(12, 'bold'))

    def _draw_status_card(self, title, subtitle=''):
        frame_glow = self.stage_profile.get('frame_glow', '#f2d35a')
        x0 = self.viewport_x + 194
        y0 = self.viewport_y + 206
        x1 = self.viewport_x + self.scene_w - 194
        y1 = self.viewport_y + self.scene_h - 206
        self._draw_pixel_panel(x0, y0, x1, y1, self.stage_profile.get('ui_panel_fill', '#081018'), frame_glow, glow=self.stage_profile.get('ui_panel_glow', self.stage_profile.get('accent', '#7fe7ff')), notch=self.stage_profile.get('panel_notch', 24), rib_count=self.stage_profile.get('panel_ribs', 5))
        if not title and not subtitle:
            self._draw_word_burst(WIN_W // 2, WIN_H // 2, self.banner_text or 'READY', self.stage_profile.get('burst_fill', '#61120d'), self.stage_profile.get('burst_outline', frame_glow), '#fff2de', scale=0.88)
            return
        self.canvas.create_text(WIN_W // 2, WIN_H // 2 - 18, anchor='center', fill=self.stage_profile.get('ui_text', '#f2d35a'), font=self._font_display(28, 'bold'), text=title)
        if subtitle:
            self.canvas.create_text(WIN_W // 2, WIN_H // 2 + 24, anchor='center', fill=self.stage_profile.get('ui_muted', 'white'), font=self._font_body(16), text=subtitle)

    def _draw_entity_shadow(self, draw_x, draw_y, width, height, tone):
        span = max(14, width - 12)
        base_y = draw_y + height - 8
        self.canvas.create_rectangle(draw_x + 6, base_y, draw_x + 6 + span, base_y + 6, fill=tone, outline='')
        self.canvas.create_rectangle(draw_x + 14, base_y + 6, draw_x + width - 14, base_y + 10, fill=tone, outline='')

    def _active_depth_preset(self):
        return self.depth_presets.get(self.depth_preset_name, self.depth_presets['studio-balanced'])

    def _toggle_depth(self, ev=None):
        self.depth_enabled = not self.depth_enabled

    def _cycle_depth_preset(self, ev=None):
        names = list(self.depth_presets.keys())
        if not names:
            return
        try:
            index = names.index(self.depth_preset_name)
        except ValueError:
            index = -1
        self.depth_preset_name = names[(index + 1) % len(names)]

    def _toggle_depth_sensor(self, ev=None):
        if not self.depth_sensor.available:
            return
        if self.depth_sensor.running:
            self.depth_sensor.stop()
        else:
            self.depth_sensor.start()

    def _update_adaptive_depth(self, dt):
        preset = self._active_depth_preset()
        metrics = self.depth_sensor.sample()
        self.depth_metrics = metrics
        hope = self.hope_contract
        volumetric_support = float(hope.get('bridgeVolumetricSupport', 0.50))
        volumetric_bias = float(hope.get('bridgeVolumetricBias', 0.50))
        render_reactivity = float(hope.get('bridgeRenderReactivity', 0.35))
        hope_theta = float(hope.get('bridgeHopeTheta', 0.55))
        adaptive_share = float(hope.get('bridgeHopeAdaptiveShare', 0.45))
        predictive_share = float(hope.get('bridgeHopePredictiveShare', 0.45))
        clog_risk = float(hope.get('bridgeHopeClogRisk', 0.15))
        brightness = float(metrics.get('brightness', 0.50))
        proximity = float(metrics.get('proximity', 0.35))
        space_open = float(metrics.get('space_open', 0.50))
        eye_open = float(metrics.get('eye_open', 0.50))
        dilation = float(metrics.get('dilation', 0.50))
        confidence = float(metrics.get('confidence', 0.0))
        lighting_fit = clamp(1.0 - abs(brightness - preset['target_brightness']) / 0.55, 0.0, 1.0)
        proximity_fit = clamp(1.0 - abs(proximity - preset['target_proximity']) / 0.60, 0.0, 1.0)
        comfort_risk = max(0.0, proximity - 0.78) * 0.72
        comfort_risk += max(0.18 - brightness, 0.0) * 0.90
        comfort_risk += max(brightness - 0.90, 0.0) * 0.45
        comfort_risk += dilation * (1.0 - lighting_fit) * 0.35
        hope_drive = 0.42 + volumetric_support * 0.18 + volumetric_bias * 0.20 + hope_theta * 0.12
        hope_drive += adaptive_share * 0.08 + predictive_share * 0.05 + render_reactivity * 0.05
        camera_drive = 0.44 + lighting_fit * 0.18 + proximity_fit * 0.15 + eye_open * 0.13 + space_open * 0.10
        camera_drive *= 0.35 + confidence * 0.65
        target_strength = preset['base_strength'] * hope_drive * camera_drive
        target_strength -= comfort_risk + clog_risk * 0.10
        target_strength = clamp(target_strength, preset['floor'], preset['ceiling'])
        if preset['force_flat'] or not self.depth_enabled:
            target_strength = 0.0
        if self.depth_bridge.available:
            bridge_strength = self.depth_bridge.strength(
                int(target_strength * 1000),
                int(hope_drive * 1000),
                int(camera_drive * 1000),
                int((1.0 - comfort_risk) * 1000),
            )
            if bridge_strength is not None:
                target_strength = clamp(bridge_strength / 1000.0, preset['floor'], preset['ceiling'])
        smoothing = preset.get('smoothing', 'soft')
        if smoothing == 'off':
            alpha = 0.42
        elif smoothing == 'balanced':
            alpha = 0.26
        else:
            alpha = 0.16
        blend = 1.0 - pow(1.0 - alpha, max(dt, 16.0) / 16.0)
        self.depth_state['strength'] += (target_strength - self.depth_state['strength']) * blend
        strength = self.depth_state['strength']
        recession = strength * preset['center_pull']
        self.depth_state['band_pull'] = {
            'far': clamp(recession * (1.45 + volumetric_bias * 0.30), 0.0, 0.24),
            'near': clamp(recession * (0.92 + render_reactivity * 0.18), 0.0, 0.15),
            'entity': clamp(recession * (0.58 + adaptive_share * 0.24), 0.0, 0.10),
            'fx': clamp(recession * 0.38, 0.0, 0.06),
        }
        target_bias_x = float(metrics.get('face_offset_x', 0.0)) * (10.0 + strength * 14.0)
        target_bias_y = float(metrics.get('face_offset_y', 0.0)) * (6.0 + strength * 10.0)
        self.depth_state['focus_bias_x'] += (target_bias_x - self.depth_state['focus_bias_x']) * blend
        self.depth_state['focus_bias_y'] += (target_bias_y - self.depth_state['focus_bias_y']) * blend
        self.depth_state['comfort'] = clamp(1.0 - comfort_risk, 0.0, 1.0)
        if metrics.get('camera_live'):
            self.depth_state['status'] = (
                f"{preset['name']} depth {int(strength * 100)}%  "
                f"cam {metrics.get('status', 'live')}  "
                f"light {int(brightness * 100)}  prox {int(proximity * 100)}  "
                f"pupil {int(dilation * 100)}"
            )
        else:
            self.depth_state['status'] = f"{preset['name']} depth {int(strength * 100)}%  HOPE-only fallback"

    def _depth_project_point(self, screen_x, screen_y, band):
        pull = self.depth_state['band_pull'].get(band, 0.0)
        center_x = (self.scene_w * 0.5) + self.depth_state.get('focus_bias_x', 0.0)
        center_y = (self.scene_h * 0.46) + self.depth_state.get('focus_bias_y', 0.0)
        fallback_x = screen_x + (center_x - screen_x) * pull
        fallback_y = screen_y + (center_y - screen_y) * (pull * 0.60)
        projected_x = None
        projected_y = None
        if self.depth_bridge.available:
            projected_x = self.depth_bridge.project_x(
                int(screen_x),
                int(center_x),
                int(pull * 1000),
                int(self.depth_state.get('strength', 0.0) * 1000),
                int(self.depth_state.get('focus_bias_x', 0.0)),
            )
            projected_y = self.depth_bridge.project_y(
                int(screen_y),
                int(center_y),
                int(pull * 1000),
                int(self.depth_state.get('strength', 0.0) * 1000),
                int(self.depth_state.get('focus_bias_y', 0.0)),
            )
        max_scene_margin_x = self.scene_w * 0.18
        max_scene_margin_y = self.scene_h * 0.18
        if projected_x is None or projected_x < -max_scene_margin_x or projected_x > self.scene_w + max_scene_margin_x or abs(projected_x - fallback_x) > (self.scene_w * 0.22):
            projected_x = fallback_x
        if projected_y is None or projected_y < -max_scene_margin_y or projected_y > self.scene_h + max_scene_margin_y or abs(projected_y - fallback_y) > (self.scene_h * 0.18):
            projected_y = fallback_y
        return int(projected_x), int(projected_y)

    def _draw_depth_frame(self):
        strength = self.depth_state.get('strength', 0.0)
        if strength <= 0.02:
            return
        comfort = self.depth_state.get('comfort', 1.0)
        frame_color = '#5e8ec7' if comfort >= 0.55 else '#93684a'
        base_margin = int(14 + (1.0 - comfort) * 10)
        for index in range(3):
            margin = base_margin + index * int(10 + strength * 14)
            self.canvas.create_rectangle(
                self.viewport_x - margin,
                self.viewport_y - margin,
                self.viewport_x + self.scene_w + margin,
                self.viewport_y + self.scene_h + margin,
                outline=frame_color,
            )

    def _draw_atmosphere(self):
        brightness = float(self.depth_metrics.get('brightness', 0.5))
        dilation = float(self.depth_metrics.get('dilation', 0.5))
        proximity = float(self.depth_metrics.get('proximity', 0.35))
        player_share, boss_share = self._duel_balance()
        volumetric_bias = float(self.hope_contract.get('bridgeVolumetricBias', 0.55))
        render_reactivity = float(self.hope_contract.get('bridgeRenderReactivity', 0.35))
        top_color = '#16233e' if brightness < 0.5 else self.stage_profile.get('sky_color', '#244066')
        low_color = self.stage_profile.get('fog_color', '#28171e') if dilation > 0.45 else self.stage_profile.get('ground_color', '#16232a')
        for band in range(16):
            y0 = int((band / 16.0) * self.scene_h)
            y1 = int(((band + 1) / 16.0) * self.scene_h)
            mix = band / 15.0
            color = top_color if mix < 0.55 else low_color
            px0, py0, px1, py1 = self._present_rect(0, y0, self.scene_w, y1)
            self.canvas.create_rectangle(px0, py0, px1, py1, fill=color, outline='', stipple='gray50')
        mist_count = 4 + int(volumetric_bias * 6)
        for idx in range(mist_count):
            radius = int(self.scene_w * (0.18 + idx * 0.05 + proximity * 0.02))
            center_x = int(self.scene_w * (0.18 + idx * 0.16 + render_reactivity * 0.04))
            center_y = int(self.scene_h * (0.20 + (idx % 3) * 0.22))
            px0, py0 = self._present_xy(center_x - radius, center_y - radius)
            px1, py1 = self._present_xy(center_x + radius, center_y + radius)
            self._draw_mist_block((px0 + px1) // 2, (py0 + py1) // 2, max(12, (px1 - px0) // 2), max(10, (py1 - py0) // 3), self.stage_profile.get('accent', '#8ec5ff'))
        tension = 0.3 + proximity * 0.4 + dilation * 0.25 + self.depth_state.get('strength', 0.0) * 0.3
        storm_width = int(60 + tension * 90)
        self.canvas.create_rectangle(self.viewport_x, self.viewport_y, self.viewport_x + storm_width, self.viewport_y + self.scene_h, fill='#091018', outline='', stipple='gray50')
        self.canvas.create_rectangle(self.viewport_x + self.scene_w - storm_width, self.viewport_y, self.viewport_x + self.scene_w, self.viewport_y + self.scene_h, fill='#16090d', outline='', stipple='gray50')
        left_glow = int(120 + player_share * 140)
        right_glow = int(120 + boss_share * 140)
        self._draw_mist_block(self.viewport_x + (left_glow // 3), self.viewport_y + (self.scene_h // 2), max(24, left_glow // 2), max(18, self.scene_h // 3), '#69d2e7')
        self._draw_mist_block(self.viewport_x + self.scene_w - (right_glow // 3), self.viewport_y + (self.scene_h // 2), max(24, right_glow // 2), max(18, self.scene_h // 3), '#ff8a6b')

    def _draw_entity_halo(self, draw_x, draw_y, width, height, color, emphasis=1.0):
        halo_pad = int(10 + emphasis * 12)
        x0 = draw_x - halo_pad
        y0 = draw_y - halo_pad
        x1 = draw_x + width + halo_pad
        y1 = draw_y + height + halo_pad
        notch = max(8, halo_pad // 2)
        self.canvas.create_polygon(
            x0 + notch,
            y0,
            x1 - notch,
            y0,
            x1,
            y0 + notch,
            x1,
            y1 - notch,
            x1 - notch,
            y1,
            x0 + notch,
            y1,
            x0,
            y1 - notch,
            x0,
            y0 + notch,
            outline=color,
            fill='',
            width=2,
        )

    def _draw_speedlines(self, focus_x, focus_y, density, color):
        if density <= 0:
            return
        for idx in range(density):
            offset = idx * 46
            left_y = focus_y + offset // 6
            right_y = focus_y - offset // 5
            self.canvas.create_polygon(0, left_y - 3, focus_x - 168, focus_y + offset - 10, focus_x - 120, focus_y + offset + 10, 0, left_y + 3, fill=color, outline='')
            self.canvas.create_polygon(WIN_W, right_y - 3, focus_x + 168, focus_y - offset - 10, focus_x + 120, focus_y - offset + 10, WIN_W, right_y + 3, fill=color, outline='')

    # game actions
    def start_wave(self):
        self.wave += 1
        wave_stage_index = min(max(0, self.wave - 1), max(0, self.preboss_waves - 1))
        self._set_stage(self.stage_cycle[wave_stage_index])
        count = 4
        self.minions = []
        for i in range(count):
            spawn_x, spawn_y = self._stage_spawn_point(i)
            spawn_y = self._ground_contact_y(spawn_y)
            m = Entity(spawn_x, spawn_y, color='yellow')
            m.vx = (-1 if i%2==0 else 1) * 18
            m.hp = 30
            m.max_hp = m.hp
            m.variant = i
            m.lane_y = spawn_y
            m.lane_amp = 4 + (i % 3) * 2
            m.lane_phase = i * 0.8
            m.recover_timer = 0
            # assign varied sprites if available (use scaled variants)
            s_choices = [self.scaled.get('minion1'), self.scaled.get('minion2'), self.scaled.get('minion3')]
            raw_choices = [self.assets.get('minion1'), self.assets.get('minion2'), self.assets.get('minion3')]
            if any(s_choices):
                m.sprite = raw_choices[i % len(raw_choices)] if any(raw_choices) else None
                m.sprite_scaled = s_choices[i % len(s_choices)]
            else:
                m.sprite = raw_choices[i % len(raw_choices)] if any(raw_choices) else None
                m.sprite_scaled = None
            self.minions.append(m)
        self._set_banner(f'WAVE {self.wave}: {self.stage_profile.get("display_name", "CITY OUTSKIRTS").upper()}', 1200)

    def spawn_nanocell(self, x, y):
        nc = Entity(x, y, color='magenta')
        nc.timer = 10000
        self.nanocells.append(nc)

    def spawn_boss(self):
        self._set_stage(self.stage_cycle[-1])
        b = Entity(156, self._ground_contact_y(54, sprite_h=64), color='maroon')
        b.max_hp = sum(self.boss_phase_hp)
        b.hp = b.max_hp
        b.phase_hp_remaining = self.boss_phase_hp[0]
        b.parts = [38, 36, 38, 36, 38, 36, 38, 40]
        b.phase = 1
        b.anchor_x = 156
        b.anchor_y = 42
        b.attack_kind = 'sweep'
        b.state = 'idle'
        b.atk_timer = BOSS_INTRO_LOCK_MS
        b.intro_lock = BOSS_INTRO_LOCK_MS
        b.first_strike_timer = BOSS_FIRST_STRIKE_MS
        b.recover_timer = 0
        b.stun_timer = 0
        b.windup_timer = 0
        b.telegraph = 0
        self.boss = b
        self.minions = []
        self.boss_sprite = self.s_img_boss or self.img_boss
        self._set_banner(f'FINAL FRAME: {self.boss_name}', 1400)

    def _dodge(self):
        self.player.dodge_buffer = max(getattr(self.player, 'dodge_buffer', 0), DODGE_BUFFER_MS)

    def on_start(self, ev=None):
        if self.state == 'title':
            option = self.menu_options[self.menu_index] if self.menu_options else 'Start Game'
            if option == 'Controls':
                self.on_toggle_controls()
                return
            if option == 'Quit':
                self.running = False
                try:
                    self.root.destroy()
                except Exception:
                    pass
                return
            self.state = 'stage_intro'
            self._set_stage(self.stage_cycle[0])
            self._reset_combat_lane()
            self.stage_intro_timer = 1200
            self._set_banner(self.stage_profile.get('display_name', 'CITY OUTSKIRTS').upper(), 1200)
        # ensure minions spread within world bounds
        for m in self.minions:
            m.x = max(8, min(m.x, GBA_W - 24))

    def _change_title_selection(self, delta):
        if not self.menu_options:
            return
        self.menu_index = (self.menu_index + delta) % len(self.menu_options)
        self._set_banner(self.menu_options[self.menu_index].upper(), 280)
    def on_attack(self, ev=None):
        if self.state != 'playing':
            return
        self.player.attack_buffer = max(getattr(self.player, 'attack_buffer', 0), self._attack_buffer_duration_ms())
        try:
            self.play_sound('attack')
        except Exception:
            pass

    def on_vn(self, ev=None):
        if self.state == 'playing':
            self.state = 'vn'
        elif self.state == 'vn':
            self.state = 'playing'

    # Controls overlay (in-canvas tutorial)
    def on_toggle_controls(self, ev=None):
        # toggle the in-canvas tutorial overlay
        if getattr(self, 'tutorial_open', False):
            # close overlay and start waves if not started
            self.tutorial_open = False
            # start waves if none have started yet
            if self.wave == 0 and len(self.minions) == 0 and self.boss is None:
                self.start_wave()
            return
        # open overlay
        self.controls_page = 0
        self.tutorial_open = True

    def _controls_render(self):
        # Rendering is handled in draw() for in-canvas overlay. This keeps API compatibility.
        return

    def _controls_prev(self):
        if self.controls_page>0:
            self.controls_page -= 1

    def _controls_next(self):
        pages_count = len(getattr(self, 'controls_pages', [])) or 1
        if self.controls_page < pages_count-1:
            self.controls_page += 1

    # XInput helper functions
    def _load_xinput(self):
        names = ('xinput1_4.dll','xinput1_3.dll','xinput9_1_0.dll')
        for n in names:
            try:
                lib = ctypes.WinDLL(n)
            except Exception:
                lib = None
            if lib:
                try:
                    # set argtypes/restype for safety
                    # XInputGetState(DWORD, XINPUT_STATE*) -> DWORD
                    self.xinput = lib
                    return
                except Exception:
                    pass
        # if no XInput, try to use a compiled C wrapper if present
        wrapper = None
        try:
            # prefer KaijuGaiden/build/xinput_wrapper.dll
            wrapper = ctypes.CDLL(os.path.join(os.path.dirname(__file__), 'build', 'xinput_wrapper.dll'))
        except Exception:
            wrapper = None
        if wrapper:
            self.xinput = wrapper
            return
        # If we couldn't find XInput or wrapper, try launching the Xbox Accessories app
        # to let the user pair/configure controllers. This is a courtesy helper and
        # will silently fail if the app isn't installed.
        try:
            self._launch_xbox_accessories()
        except Exception:
            pass

    def _poll_gamepad(self):
        # Prefer XInput if available
        if self.xinput:
            try:
                class XINPUT_GAMEPAD(ctypes.Structure):
                    _fields_ = [('wButtons', wintypes.WORD), ('bLeftTrigger', wintypes.BYTE), ('bRightTrigger', wintypes.BYTE), ('sThumbLX', wintypes.SHORT), ('sThumbLY', wintypes.SHORT), ('sThumbRX', wintypes.SHORT), ('sThumbRY', wintypes.SHORT)]
                class XINPUT_STATE(ctypes.Structure):
                    _fields_ = [('dwPacketNumber', wintypes.DWORD), ('Gamepad', XINPUT_GAMEPAD)]
                state = XINPUT_STATE()
                # ensure function prototype if present
                try:
                    func = self.xinput.XInputGetState
                    func.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
                    func.restype = wintypes.DWORD
                    res = func(0, ctypes.byref(state))
                except Exception:
                    # possibly using a custom wrapper with xi_get_state
                    try:
                        # wrapper: int xi_get_state(int idx, unsigned short *buttons, short *lx, short *ly, unsigned char *lt, unsigned char *rt)
                        btn = wintypes.WORD()
                        lx = ctypes.c_short()
                        ly = ctypes.c_short()
                        lt = ctypes.c_ubyte()
                        rt = ctypes.c_ubyte()
                        r = self.xinput.xi_get_state(0, ctypes.byref(btn), ctypes.byref(lx), ctypes.byref(ly), ctypes.byref(lt), ctypes.byref(rt))
                        if r != 0:
                            return None
                        buttons = btn.value
                        g = types.SimpleNamespace(sThumbLX=lx.value, sThumbLY=ly.value, sThumbRX=0, sThumbRY=0, bLeftTrigger=lt.value, bRightTrigger=rt.value, wButtons=buttons)
                    except Exception:
                        return None
                else:
                        if res != 0:
                            return None
                        g = state.Gamepad
                buttons = g.wButtons
                return {
                    'a': bool(buttons & 0x1000),
                    'b': bool(buttons & 0x2000),
                    'x': bool(buttons & 0x4000),
                    'y': bool(buttons & 0x8000),
                    'lb': bool(buttons & 0x0100),
                    'rb': bool(buttons & 0x0200),
                    'start': bool(buttons & 0x0010),
                    'back': bool(buttons & 0x0020),
                    'dpad_up': bool(buttons & 0x0001),
                    'dpad_down': bool(buttons & 0x0002),
                    'dpad_left': bool(buttons & 0x0004),
                    'dpad_right': bool(buttons & 0x0008),
                    'lx': g.sThumbLX,
                    'ly': g.sThumbLY,
                    'rx': getattr(g, 'sThumbRX', 0),
                    'ry': getattr(g, 'sThumbRY', 0),
                    'lt': getattr(g, 'bLeftTrigger', 0),
                    'rt': getattr(g, 'bRightTrigger', 0),
                }
            except Exception:
                # on any failure parse, fall back
                return None
        # Fallback: pygame joystick if available
        if PYGAME_AVAILABLE:
            try:
                if not pygame.get_init():
                    pygame.init()
                if pygame.joystick.get_count() > 0:
                    j = pygame.joystick.Joystick(0)
                    j.init()
                    # common mapping for Xbox controllers
                    lx = int(j.get_axis(0) * 32767)
                    ly = int(j.get_axis(1) * 32767)
                    a = j.get_button(0)
                    b = j.get_button(1)
                    start = j.get_button(7) if j.get_numbuttons() > 7 else 0
                    return {'a': bool(a), 'b': bool(b), 'start': bool(start), 'lx': lx, 'ly': ly, 'lt': 0, 'rt': 0}
            except Exception:
                pass
        return None

    def _launch_xbox_accessories(self):
        """Attempt to open the Xbox Accessories app so the user can pair/configure controllers."""
        try:
            # Try explorer shell protocol for Appsfolder
            os.startfile('shell:Appsfolder\\Microsoft.XboxAccessories_8wekyb3d8bbwe!App')
            return True
        except Exception:
            pass
        # Fallback to powershell Start-Process
        try:
            subprocess.run(['powershell', '-NoProfile', '-Command', "Start-Process 'shell:Appsfolder\\Microsoft.XboxAccessories_8wekyb3d8bbwe!App'"], check=False)
            return True
        except Exception:
            return False
        

    def on_pause(self, ev=None):
        if self.state == 'playing':
            self.state = 'paused'
        elif self.state == 'paused':
            self.state = 'playing'

    def _toggle_debug(self, ev=None):
        """Toggle the simple on-screen debug overlay."""
        self.show_debug = not getattr(self, 'show_debug', False)

    def _on_close(self):
        self.running = False
        try:
            self.depth_sensor.stop()
        except Exception:
            pass
        try:
            self.root.after_cancel(getattr(self, 'loop_after_id', ''))
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _rects_overlap(self, ax, ay, aw, ah, bx, by, bw, bh):
        return not (ax + aw < bx or bx + bw < ax or ay + ah < by or by + bh < ay)

    def _draw_asset_bbox_at(self, world_x, world_y, asset_key):
        """Draw the precomputed PIL alpha bbox for the named asset at world coordinates."""
        bbox = self.asset_bbox.get(asset_key)
        if not bbox:
            return
        try:
            left, top, right, bottom = bbox
            w = (right - left) * SCALE
            h = (bottom - top) * SCALE
            # world_x/world_y represent the top-left anchor for the sprite
            draw_x = (world_x - int(self.camera_x) + left) * SCALE
            draw_y = (world_y + top) * SCALE
            draw_x, draw_y = self._present_xy(draw_x, draw_y)
            self.canvas.create_rectangle(draw_x, draw_y, draw_x + w, draw_y + h, outline='red')
        except Exception:
            return

    def _toggle_bboxes(self, ev=None):
        self.show_bboxes = not getattr(self, 'show_bboxes', False)

    # Keyboard/controller helper actions
    def _on_select(self):
        # Space = Select: consume a NanoCell during combat, mirroring the original handheld flow.
        if self.state == 'playing':
            self._use_nanocell()

    def _use_nanocell(self):
        if getattr(self.player, 'nanocell_count', 0) > 0:
            self.player.nanocell_count -= 1
            self.player.nanocell_boost_timer = 5000
            self.player.attack_power = 14
            self._set_banner('NANOCELL SURGE', 700)
            try:
                self.play_sound('attack')
            except Exception:
                pass

    def _press_lb(self, down):
        if down:
            self.keys.add('lb')
            # trigger special / phase move
            try:
                self._special_l()
            except Exception:
                pass
        else:
            self.keys.discard('lb')

    def _press_rb(self, down):
        if down:
            self.keys.add('rb')
            try:
                self._special_r()
            except Exception:
                pass
        else:
            self.keys.discard('rb')

    def _special_l(self):
        if self.state != 'playing' or getattr(self.player, 'hit_stun', 0) > 0:
            return
        retreat = -18 if getattr(self.player, 'facing', 'right') == 'right' else 18
        self.player.x = max(0, min((GBA_W - 8) if self.parity_mode else (self.world_width - 8), self.player.x + retreat))
        self.player.flow_feint_timer = 260
        self.player.dodge_flash_timer = max(getattr(self.player, 'dodge_flash_timer', 0), 180)
        self.player.combo_timer = max(getattr(self.player, 'combo_timer', 0), 180)
        fx_x = self.player.x + (4 if getattr(self.player, 'facing', 'right') == 'right' else -4)
        fx_y = self.player.y - 2
        self.effects.append((fx_x, fx_y, self.img_attack2 or self.img_attack, 320))
        self._set_banner('FEATHER STEP', 360)
        try:
            self.play_sound('attack')
        except Exception:
            pass

    def _special_r(self):
        if self.state != 'playing' or getattr(self.player, 'hit_stun', 0) > 0:
            return
        surge = 22 if getattr(self.player, 'facing', 'right') == 'right' else -22
        self.player.x = max(0, min((GBA_W - 8) if self.parity_mode else (self.world_width - 8), self.player.x + surge))
        self.player.rupture_drive_timer = 320
        self.player.attack_pose_timer = max(getattr(self.player, 'attack_pose_timer', 0), 190)
        self.player.attack_buffer = max(getattr(self.player, 'attack_buffer', 0), 90)
        fx_x = self.player.x + (16 if getattr(self.player, 'facing', 'right') == 'right' else -16)
        fx_y = self.player.y - 4
        self.effects.append((fx_x, fx_y, self.assets.get('blodfx') or self.img_attack2, 520))
        self._set_banner('RUPTURE DRIVE', 420)
        try:
            self.play_sound('attack')
        except Exception:
            pass

    def _tick_audio(self, dt):
        if winsound is None:
            return
        self.audio_ambient_timer = max(0, self.audio_ambient_timer - dt)
        if self.state == 'playing' and self.audio_ambient_timer == 0:
            split, boss_share = self._duel_balance()
            if self.boss or self.minions:
                self.play_sound('ambient', split, boss_share)
            self.audio_ambient_timer = 950 if self.boss else 1400

    def play_sound(self, name, *args):
        """Very small placeholder sound system. Uses winsound.Beep on Windows if present.
        Non-blocking (spawns a thread).
        """
        if winsound is None:
            return
        def _beep(freq, dur):
            try:
                winsound.Beep(freq, dur)
            except Exception:
                pass
        def _pattern(tones):
            for freq, dur in tones:
                _beep(freq, dur)
        if name == 'attack':
            threading.Thread(target=_pattern, args=([(860, 45), (1120, 35)],), daemon=True).start()
        elif name == 'minion_die':
            threading.Thread(target=_pattern, args=([(520, 60), (320, 120)],), daemon=True).start()
        elif name == 'boss_die':
            threading.Thread(target=_pattern, args=([(300, 120), (220, 180), (180, 240)],), daemon=True).start()
        elif name == 'pickup':
            threading.Thread(target=_pattern, args=([(980, 40), (1320, 60)],), daemon=True).start()
        elif name == 'telegraph':
            threading.Thread(target=_pattern, args=([(720, 35), (720, 35), (920, 60)],), daemon=True).start()
        elif name == 'ambient':
            split = float(args[0]) if args else 0.5
            boss_share = float(args[1]) if len(args) > 1 else (1.0 - split)
            player_freq = int(280 + split * 180)
            boss_freq = int(190 + boss_share * 120)
            threading.Thread(target=_pattern, args=([(boss_freq, 70), (player_freq, 55)],), daemon=True).start()
        else:
            threading.Thread(target=_beep, args=(600, 100), daemon=True).start()


def main():
    root = tk.Tk()
    game = Game(root)
    root.mainloop()


if __name__ == '__main__':
    main()
