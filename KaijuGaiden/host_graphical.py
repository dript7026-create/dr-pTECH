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
try:
    import pygame
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False
import tkinter as tk
import ctypes
from ctypes import wintypes
import types
import threading
import subprocess
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False
try:
    import winsound
except Exception:
    winsound = None

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
# Prefer the workspace placeholderassets directory when available so the
# host always uses the intended placeholder assets regardless of cwd.
_ABS_PLACEHOLDER = r"C:\Users\rrcar\Documents\drIpTECH\KaijuGaiden\assets\placeholderassets"
if os.path.exists(_ABS_PLACEHOLDER):
    PLACEHOLDER_DIR = _ABS_PLACEHOLDER
else:
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
SCALE = 2
WIN_W, WIN_H = GBA_W * SCALE, GBA_H * SCALE


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
        self.canvas = tk.Canvas(root, width=WIN_W, height=WIN_H, bg='black')
        self.canvas.pack()

        # load placeholder assets (PNG preferred)
        self.assets = {}
        for key, fname in ASSET_FILES.items():
            path = os.path.join(PLACEHOLDER_DIR, fname)
            if os.path.exists(path):
                try:
                    self.assets[key] = tk.PhotoImage(file=path)
                except Exception:
                    self.assets[key] = None
            else:
                self.assets[key] = None

        # assign images
        self.img_title = self.assets.get('title')
        self.img_player = self.assets.get('player')
        self.img_minion1 = self.assets.get('minion1') or self.assets.get('minion2') or self.assets.get('minion3')
        self.img_nanocell = self.assets.get('nanocell1') or self.assets.get('nanocell2')
        self.img_boss = self.assets.get('boss')
        self.img_attack = self.assets.get('attackfx1')
        self.img_attack2 = self.assets.get('attackfx2')
        self.img_blodfx = self.assets.get('blodfx')

        # precompute scaled assets to avoid GC and ensure effects render
        self.scaled = {}
        for k, img in self.assets.items():
            if img:
                try:
                    self.scaled[k] = img.zoom(SCALE, SCALE)
                except Exception:
                    self.scaled[k] = img
            else:
                self.scaled[k] = None
        # handy references to scaled variants
        self.s_img_attack = self.scaled.get('attackfx1') or self.scaled.get('attackfx2')
        self.s_img_attack2 = self.scaled.get('attackfx2') or self.s_img_attack
        self.s_img_blodfx = self.scaled.get('blodfx')
        self.s_img_minion1 = self.scaled.get('minion1') or self.scaled.get('minion2') or self.scaled.get('minion3')
        self.s_img_player = self.scaled.get('player')
        self.s_img_boss = self.scaled.get('boss')

        # compute non-transparent bounding boxes for assets when PIL is available
        self.asset_bbox = {}
        if PIL_AVAILABLE:
            for k, fname in ASSET_FILES.items():
                path = os.path.join(PLACEHOLDER_DIR, fname)
                if os.path.exists(path):
                    try:
                        im = Image.open(path).convert('RGBA')
                        alpha = im.split()[-1]
                        bbox = alpha.getbbox()
                        if bbox:
                            self.asset_bbox[k] = bbox  # (left, upper, right, lower)
                        else:
                            self.asset_bbox[k] = (0, 0, im.width, im.height)
                    except Exception:
                        self.asset_bbox[k] = None
                else:
                    self.asset_bbox[k] = None
        else:
            for k in ASSET_FILES.keys():
                self.asset_bbox[k] = None

        # game state / entities
        self.state = 'title'  # title, playing, vn, paused
        self.player = Entity(60, 80, color='cyan')
        # facing for projectile placement
        self.player.facing = 'right'
        self.player.attack_cooldown = 0
        self.player.nanocell_count = 0
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
        bg = self.assets.get('background')
        if bg:
            try:
                bw = bg.width()
                self.world_width = max(self.world_width, bw)
            except Exception:
                pass

        # keyboard state
        self.keys = set()
        root.bind('<KeyPress>', self.on_key)
        root.bind('<KeyRelease>', self.on_key_release)
        root.bind('<Return>', self.on_start)
        # remap: Space -> Select, Z/X -> A/B, Q/E -> LB/RB
        root.bind('<space>', lambda e: self._on_select())
        root.bind('z', lambda e: self.on_attack())
        root.bind('x', lambda e: self._use_nanocell())
        root.bind('q', lambda e: self._press_lb(True))
        root.bind('e', lambda e: self._press_rb(True))
        root.bind('Q', lambda e: self._press_lb(True))
        root.bind('E', lambda e: self._press_rb(True))
        root.bind('<KeyRelease-q>', lambda e: self._press_lb(False))
        root.bind('<KeyRelease-e>', lambda e: self._press_rb(False))
        root.bind('v', self.on_vn)
        root.bind('p', self.on_pause)
        root.bind('c', self.on_toggle_controls)
        root.bind('C', self.on_toggle_controls)
        # move debug toggle off 'd' (conflicted) to F1
        root.bind('<F1>', self._toggle_debug)

        # XInput dynamic loader for Xbox controller support
        self.xinput = None
        self._load_xinput()

        # menu state for title
        self.menu_options = ['Start Game', 'Controls', 'Quit']
        self.menu_index = 0

        # controls popup state
        self.controls_win = None
        self.controls_page = 0
        # in-canvas tutorial overlay (blocks gameplay until closed)
        self.tutorial_open = False
        self.controls_pages = [
            "Xbox Controller:\n\nLeft Stick / DPad: Move\nA / X: Primary Attack\nB: Use Nanocell\nLB/RB: Specials\nStart: Pause\nBack/View: Close Tutorial",
            "Combat Tips:\n\nUse A/X to perform Rei's primary attack.\nAvoid enemy telegraphs (red flash) and dodge with B.\nCollect NanoCells to heal.",
            "Buttons:\n\nRight/Left or Right Stick: Scroll pages\nA: Next page\nB / Back: Close tutorial"
        ]
        # previous keyboard state for edge detection
        self.prev_keys = set()
        # previous gamepad state for edge detection
        self.prev_gp = {}
        # debug overlay
        self.show_debug = False
        # show computed PIL alpha bboxes for visual verification
        self.show_bboxes = bool(PIL_AVAILABLE)
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
        self.hud_text = self.canvas.create_text(8, 8, anchor='nw', fill='white', font=('Consolas', 10), text='')

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

    def on_key(self, ev):
        self.keys.add(ev.keysym.lower())

    def on_key_release(self, ev):
        k = ev.keysym.lower()
        if k in self.keys:
            self.keys.remove(k)

    def update(self, dt):
        speed = 80 * (dt / 1000.0)  # pixels per second scaled
        # poll controller and merge into keys/actions with edge detection
        gp = self._poll_gamepad()
        # handle menu navigation when on title
        if self.state == 'title':
            if gp:
                prev = self.prev_gp or {}
                # use dpad or leftstick x for menu movement
                lx = gp.get('lx', 0)
                if (gp.get('dpad_left') and not (prev.get('dpad_left'))) or lx < -12000 and (not prev or prev.get('lx',0) >= -12000):
                    self.menu_index = max(0, self.menu_index - 1)
                if (gp.get('dpad_right') and not (prev.get('dpad_right'))) or lx > 12000 and (not prev or prev.get('lx',0) <= 12000):
                    self.menu_index = min(len(self.menu_options)-1, self.menu_index + 1)
                # start on A or Start
                if gp.get('a') and not prev.get('a') or gp.get('start') and not prev.get('start'):
                    if self.menu_options[self.menu_index] == 'Start Game':
                        self.on_start()
                    elif self.menu_options[self.menu_index] == 'Controls':
                        self.on_toggle_controls()
                    elif self.menu_options[self.menu_index] == 'Quit':
                        self.root.quit()
                # right stick affects menu scroll visual
                rx = gp.get('rx',0)
                self.bg_x += (rx/32767.0) * (dt/16.0)
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
            # LB / RB map to specials
            if gp.get('lb') and not prev.get('lb'):
                self._press_lb(True)
            if not gp.get('lb') and prev.get('lb'):
                self._press_lb(False)
            if gp.get('rb') and not prev.get('rb'):
                self._press_rb(True)
            if not gp.get('rb') and prev.get('rb'):
                self._press_rb(False)
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
        self.player.x = max(0, min(GBA_W - 8, self.player.x))
        self.player.y = max(0, min(GBA_H - 8, self.player.y))

        # background scroll
        self.bg_x = (self.bg_x + 12 * (dt/1000.0)) % GBA_W

        # update camera smoothly to follow player, allow small right-stick nudge
        desired_cam = max(0, min(self.player.x - (GBA_W // 2), max(0, self.world_width - GBA_W)))
        # apply small smoothing
        self.camera_x += (desired_cam - self.camera_x) * 0.12
        # apply right-stick nudge if controller present
        if gp:
            rx = gp.get('rx', 0)
            self.camera_x += (rx / 32767.0) * 6.0 * (dt/1000.0)
        # clamp camera
        self.camera_x = max(0, min(self.camera_x, max(0, self.world_width - GBA_W)))

        # simple minion AI: move left-right
        for m in list(self.minions):
            m.x += m.vx * (dt / 1000.0)
            # simple bounds and oscillation
            if m.x < 16 or m.x > GBA_W - 24:
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
                    if self._rects_overlap(m.x, m.y, 12, 12, self.player.x, self.player.y, 12, 12):
                        self.player.hp = max(0, self.player.hp - 12)
                        # blood + attackfx on player to cue damage
                        tb2 = getattr(self, 's_img_blodfx', None) or getattr(self, 's_img_attack2', None) or getattr(self, 'img_blodfx', None)
                        if tb2 is not None:
                            self.effects.append((self.player.x, self.player.y, tb2, 400))
            elif m.ai_timer <= 0:
                # decide to telegraph an attack when player nearby
                dx = abs(self.player.x - m.x)
                dy = abs(self.player.y - m.y)
                if dx < 48 and dy < 24:
                    m.tele = 300
                m.ai_timer = 1500
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

        # boss simple AI (inquisitive -> aggressive -> defensive)
        if self.boss:
            self.boss.ai_timer = max(0, getattr(self.boss, 'ai_timer', 0) - dt)
            # telegraph timer for boss attacks
            if not hasattr(self.boss, 'telegraph'):
                self.boss.telegraph = 0
            self.boss.telegraph = max(0, getattr(self.boss, 'telegraph', 0) - dt)
            # if player within notice range, approach (inquisitive)
            distx = (self.player.x - self.boss.x)
            disty = (self.player.y - self.boss.y)
            dist = math.hypot(distx, disty)
            if dist < 140 and self.boss.state == 'idle':
                self.boss.state = 'investigate'
            if self.boss.state == 'investigate':
                # move towards player slowly
                self.boss.x += (distx/ (dist+1)) * 20 * (dt/1000.0)
                if dist < 80:
                    self.boss.state = 'aggro'
                    # telegraph before the first lunge
                    self.boss.ai_timer = 800
                    self.boss.telegraph = 300
            elif self.boss.state == 'aggro':
                # aggressive behavior: lunge and attack periodically
                if self.boss.ai_timer <= 0:
                    # lunge: teleport closer for simplicity
                    # before lunging, telegraph briefly
                    if self.boss.telegraph <= 0:
                        self.boss.telegraph = 200
                        # schedule the actual lunge on next tick
                        self.boss.ai_timer = 200
                    else:
                        self.boss.x -= 30
                    self.boss.ai_timer = 800
                    # damage player if overlapping
                    bw = getattr(self.boss_sprite, 'width', lambda:64)()
                    bh = getattr(self.boss_sprite, 'height', lambda:64)()
                    if self._rects_overlap(self.boss.x, self.boss.y, bw, bh, self.player.x, self.player.y, 12, 12):
                        # show boss attack effect (use attackfx1)
                        befx = getattr(self, 's_img_attack', None) or getattr(self, 'img_attack', None)
                        if befx is not None:
                            self.effects.append((self.player.x, self.player.y, befx, 600))
                        # blood overlay on player
                        pb = getattr(self, 's_img_blodfx', None) or getattr(self, 'img_blodfx', None)
                        if pb is not None:
                            self.effects.append((self.player.x, self.player.y - 4, pb, 500))
                        self.player.hp = max(0, self.player.hp - 20)
                    # create visual telegraph if set
                if getattr(self.boss, 'telegraph', 0) > 0:
                    # show a telegraph marker using boss attackfx (attackfx1)
                    tx = self.boss.x
                    ty = self.boss.y - 8
                    timg = getattr(self, 's_img_attack', None) or getattr(self, 'img_attack', None)
                    if timg is None:
                        timg = getattr(self, 's_img_blodfx', None) or getattr(self, 'img_blodfx', None)
                    if timg is not None:
                        self.effects.append((tx, ty, timg, int(self.boss.telegraph)))
                # if boss low health, become defensive
                if self.boss.hp < self.boss.max_hp * 0.35:
                    self.boss.state = 'defensive'
            elif self.boss.state == 'defensive':
                # back away a bit
                self.boss.x += 10 * (dt/1000.0)
                if dist > 160:
                    self.boss.state = 'idle'
                

        # spawn waves when playing (but handle boss spawn after wave 2 clears)
        if self.state == 'playing' and len(self.minions) == 0 and not getattr(self, 'tutorial_open', False):
            # after clearing wave 2, spawn boss instead of starting wave 3
            if self.wave == 2 and self.boss is None:
                self.spawn_boss()
            else:
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
        # background tile using sheet if present and layered parallax
        if self.assets.get('background'):
            try:
                bg = self.assets.get('background')
                bw = bg.width()
                bh = bg.height()
                # split into far (upper) and near (lower) halves if possible
                mid = max(1, bh // 2)
                try:
                    far = self._crop(bg, 0, 0, bw, mid).zoom(SCALE, SCALE)
                    near = self._crop(bg, 0, mid, bw, bh - mid).zoom(SCALE, SCALE)
                except Exception:
                    far = bg.zoom(SCALE, SCALE)
                    near = None
                # far layer scroll ratio
                far_x = int(-self.camera_x * 0.3) % (bw * SCALE)
                self.canvas.create_image(far_x - (bw * SCALE), 0, image=far, anchor='nw')
                self.canvas.create_image(far_x, 0, image=far, anchor='nw')
            except Exception:
                self.canvas.create_rectangle(0, 0, WIN_W, WIN_H, fill='#203040')
        elif self.scaled_bg:
            try:
                ox = int(-self.bg_x * SCALE) % (WIN_W)
                self.canvas.create_image(ox - WIN_W, 0, image=self.scaled_bg, anchor='nw')
                self.canvas.create_image(ox, 0, image=self.scaled_bg, anchor='nw')
            except Exception:
                self.canvas.create_rectangle(0, 0, WIN_W, WIN_H, fill='#203040')
        elif self.img_title:
            try:
                bg = self.img_title.zoom(SCALE, SCALE)
                self.canvas.create_image(0, 0, image=bg, anchor='nw')
            except Exception:
                self.canvas.create_rectangle(0, 0, WIN_W, WIN_H, fill='#203040')
        else:
            self.canvas.create_rectangle(0, 0, WIN_W, WIN_H, fill='#203040')
        if self.state == 'title':
            self.canvas.create_text(WIN_W//2, WIN_H-24, text='Press Enter to Start', fill='white', font=('Consolas', 14))
            return

        # draw nanocells
        for nc in self.nanocells:
            if self.img_nanocell:
                self.canvas.create_image(nc.x * SCALE, nc.y * SCALE, image=self.img_nanocell, anchor='nw')
            else:
                self.canvas.create_oval(nc.x * SCALE, nc.y * SCALE, (nc.x+8)*SCALE, (nc.y+8)*SCALE, fill='magenta')
            # overlay bbox for nanocell
            if getattr(self, 'show_bboxes', False):
                self._draw_asset_bbox_at(nc.x, nc.y, 'nanocell1')

        # draw minions
        for m in self.minions:
            sprite = getattr(m, 'sprite_scaled', None) or getattr(m, 'sprite', self.img_minion1)
            draw_x = (m.x - int(self.camera_x)) * SCALE
            draw_y = m.y * SCALE
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
            hy = (m.y - 6) * SCALE
            maxhp = getattr(m, 'max_hp', getattr(m, 'hp', 1)) or 1
            hpw = max(0, int((getattr(m, 'hp', 0) / maxhp) * hw))
            self.canvas.create_rectangle(hx, hy, hx+hw, hy+4, outline='white')
            self.canvas.create_rectangle(hx, hy, hx+hpw, hy+4, fill='green', outline='')

        # draw player (with attack flash)
        px = (self.player.x - int(self.camera_x)) * SCALE
        py = self.player.y * SCALE
        if self.img_player:
            self.canvas.create_image(px, py, image=self.img_player, anchor='nw')
        else:
            self.canvas.create_rectangle(px, py, px+(12*SCALE), py+(12*SCALE), fill=self.player.color)
        # player bbox overlay
        if getattr(self, 'show_bboxes', False):
            self._draw_asset_bbox_at(self.player.x, self.player.y, 'player')
        # draw player attack projectiles if present
        for p in list(self.projectiles):
            try:
                imgp = p.get('img')
                draw_px = (p['x'] - int(self.camera_x)) * SCALE
                draw_py = p['y'] * SCALE
                if imgp:
                    self.canvas.create_image(draw_px, draw_py, image=imgp, anchor='nw')
                else:
                    self.canvas.create_rectangle(draw_px, draw_py, draw_px+(p['w']*SCALE), draw_py+(p['h']*SCALE), fill='orange')
                # projectile bbox overlay (attackfx)
                if getattr(self, 'show_bboxes', False):
                    self._draw_asset_bbox_at(p['x'], p['y'], 'attackfx1')
            except Exception:
                pass

        # HUD
        hud = f"HP: {self.player.hp}/{self.player.max_hp}  Tier:{self.player.growth_tier}  Variant:{self.player.variant}  Nano:{self.player.nanocell_count}  Wave:{self.wave}"
        self.canvas.create_text(6, 6, anchor='nw', fill='white', font=('Consolas', 12), text=hud)

        # boss
        if self.boss:
            bx = self.boss.x * SCALE
            by = self.boss.y * SCALE
            # draw boss with camera offset
            bx = (self.boss.x - int(self.camera_x)) * SCALE
            if self.img_boss:
                self.canvas.create_image(bx, by, image=self.boss_sprite or self.img_boss, anchor='nw')
            else:
                self.canvas.create_rectangle(bx, by, bx+64, by+64, fill='maroon')
            # boss bbox overlay
            if getattr(self, 'show_bboxes', False):
                self._draw_asset_bbox_at(self.boss.x, self.boss.y, 'boss')
            # boss HP bar
            self.canvas.create_rectangle(WIN_W-220, 10, WIN_W-20, 26, outline='white')
            hpw = max(0, int((self.boss.hp / self.boss.max_hp) * 200))
            self.canvas.create_rectangle(WIN_W-220, 10, WIN_W-220+hpw, 26, fill='red', outline='')

        # controller debug overlay
        if self.show_debug:
            gp = self.prev_gp or {}
            s = f"A:{int(gp.get('a',0))} B:{int(gp.get('b',0))} LX:{gp.get('lx',0)} LY:{gp.get('ly',0)}"
            self.canvas.create_text(WIN_W-10, 30, anchor='ne', fill='white', font=('Consolas', 10), text=s)

        # draw effects
        for i, ef in enumerate(list(self.effects)):
            ex, ey, sp, t = ef
            if sp:
                try:
                    # sp may be a raw or scaled PhotoImage; prefer scaled variants
                    img_to_draw = sp
                    if isinstance(sp, str):
                        img_to_draw = self.scaled.get(sp) or self.assets.get(sp)
                    self.canvas.create_image(ex * SCALE, ey * SCALE, image=img_to_draw, anchor='nw')
                except Exception:
                    self.canvas.create_oval(ex * SCALE, ey * SCALE, (ex+8)*SCALE, (ey+8)*SCALE, fill='orange')
            else:
                self.canvas.create_oval(ex * SCALE, ey * SCALE, (ex+8)*SCALE, (ey+8)*SCALE, fill='orange')
            t -= 16
            if t <= 0:
                try:
                    self.effects.remove(ef)
                except ValueError:
                    pass
            else:
                # replace tuple with updated timer
                self.effects[self.effects.index(ef)] = (ex, ey, sp, t)

        # draw foreground layer (lower portion of background) on top of entities
        if self.assets.get('background'):
            try:
                bg = self.assets.get('background')
                bw = bg.width()
                bh = bg.height()
                mid = max(1, bh // 2)
                try:
                    near = self._crop(bg, 0, mid, bw, bh - mid).zoom(SCALE, SCALE)
                    near_x = int(-self.camera_x * 0.9) % (bw * SCALE)
                    self.canvas.create_image(near_x - (bw * SCALE), WIN_H - (bh - mid) * SCALE, image=near, anchor='nw')
                    self.canvas.create_image(near_x, WIN_H - (bh - mid) * SCALE, image=near, anchor='nw')
                except Exception:
                    pass
            except Exception:
                pass

        # draw tutorial overlay in-canvas if open (blocks gameplay)
        if getattr(self, 'tutorial_open', False):
            pages = getattr(self, 'controls_pages', [])
            ptext = pages[self.controls_page] if 0 <= self.controls_page < len(pages) else ''
            ow = int(WIN_W * 0.92)
            oh = int(WIN_H * 0.42)
            ox = (WIN_W - ow) // 2
            oy = (WIN_H - oh) // 2
            # background box
            self.canvas.create_rectangle(ox, oy, ox+ow, oy+oh, fill='#001018', outline='white')
            # text
            self.canvas.create_text(ox+12, oy+12, anchor='nw', text=ptext, fill='white', font=('Consolas', 12), width=ow-24)
            # footer prompts
            prompts = 'A/Right: Next    Left: Prev    B/Back/Space: Close'
            self.canvas.create_text(ox+ow-12, oy+oh-12, anchor='ne', text=prompts, fill='white', font=('Consolas', 10))

    def loop(self):
        now = time.time()
        dt = (now - self.last) * 1000
        self.last = now
        # tick cooldowns
        if getattr(self.player, 'attack_cooldown', 0) > 0:
            self.player.attack_cooldown = max(0, self.player.attack_cooldown - dt)
        self.player.attacking = False
        self.update(dt)
        self.draw()
        if self.running:
            self.root.after(16, self.loop)

    # game actions
    def start_wave(self):
        self.wave += 1
        count = 3 + self.wave
        self.minions = []
        for i in range(count):
            m = Entity(120 + i*18, 40 + (i%3)*12, color='yellow')
            m.vx = (-1 if i%2==0 else 1) * (20 + self.wave*2)
            m.hp = 50 + self.wave*10
            m.max_hp = m.hp
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
        # boss spawns are handled after wave clear

    def spawn_nanocell(self, x, y):
        nc = Entity(x, y, color='magenta')
        nc.timer = 10000
        self.nanocells.append(nc)

    def spawn_boss(self):
        b = Entity(GBA_W - 64, 40, color='maroon')
        b.hp = 500
        b.max_hp = 500
        b.x = GBA_W - 80
        b.y = 20
        b.state = 'idle'
        b.ai_timer = 0
        self.boss = b
        # prefer scaled boss sprite
        self.boss_sprite = self.s_img_boss or self.img_boss

    def _dodge(self):
        # brief invulnerability and small move
        if getattr(self.player, 'dodge_timer', 0) <= 0:
            self.player.dodge_timer = 400
            self.player.state = 'dodge'
            # small evasive hop (away from facing direction)
            try:
                move_dir = -10 if getattr(self.player, 'facing', 'right') == 'right' else 10
                self.player.x = max(0, min(self.world_width - 8, self.player.x + move_dir))
            except Exception:
                pass
            try:
                self.play_sound('attack')
            except Exception:
                pass

    def on_start(self, ev=None):
        if self.state == 'title':
            self.state = 'playing'
            self.wave = 0
            # delay starting waves until tutorial is closed
            # waves will start when tutorial overlay is closed
            # swap background to dedicated gameplay background if present
        # ensure minions spread within world bounds
        for m in self.minions:
            m.x = max(8, min(m.x, max(8, self.world_width - 24)))
    def on_attack(self, ev=None):
        if self.state != 'playing':
            return
        if getattr(self.player, 'attack_cooldown', 0) <= 0:
            self.player.attacking = True
            self.player.attack_cooldown = 300
            try:
                self.play_sound('attack')
            except Exception:
                pass
            # apply attack to boss if in range
            if self.boss:
                bw = getattr(self.boss_sprite, 'width', lambda:64)()
                bh = getattr(self.boss_sprite, 'height', lambda:64)()
                if self._rects_overlap(self.player.x, self.player.y, 12, 12, self.boss.x, self.boss.y, bw, bh):
                    self.boss.hp -= 40
                    # blood overlay on boss when hit
                    bfx = getattr(self, 's_img_blodfx', None) or getattr(self, 'img_blodfx', None)
                    if bfx is not None:
                        self.effects.append((self.boss.x, self.boss.y - 4, bfx, 400))
                    if self.boss.hp <= 0:
                        self.spawn_nanocell(self.boss.x, self.boss.y)
                        self.boss = None
                        try:
                            self.play_sound('boss_die')
                        except Exception:
                            pass
            # Create an immobile projectile at the forward-facing edge using attackfx1
            try:
                aimg = getattr(self, 's_img_attack', None) or getattr(self, 'img_attack', None)
                pw = getattr(self.player, 'size', (12,12))[0]
                ph = getattr(self.player, 'size', (12,12))[1]
                if self.player.facing == 'right':
                    px = self.player.x + pw
                else:
                    px = self.player.x - 8
                py = self.player.y
                pwid = aimg.width() if aimg and hasattr(aimg, 'width') else 12
                phei = aimg.height() if aimg and hasattr(aimg, 'height') else 12
                proj = {'x': px, 'y': py, 'w': pwid, 'h': phei, 'img': aimg, 'timer': 400, 'spawn_time': time.time(), 'base_damage': 48}
                self.projectiles.append(proj)
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
            self.canvas.create_rectangle(draw_x, draw_y, draw_x + w, draw_y + h, outline='red')
        except Exception:
            return

    def _toggle_bboxes(self, ev=None):
        self.show_bboxes = not getattr(self, 'show_bboxes', False)

    # Keyboard/controller helper actions
    def _on_select(self):
        # Space = Select: act as VN toggle in gameplay, or no-op on title
        if self.state == 'playing':
            self.on_vn()

    def _use_nanocell(self):
        # Keyboard X or controller B
        if getattr(self.player, 'nanocell_count', 0) > 0:
            self.player.nanocell_count -= 1
            self.player.hp = min(self.player.max_hp, self.player.hp + 30)
            try:
                self.play_sound('minion_die')
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
        # placeholder phase move L: small area damage near player
        fx_x = self.player.x + 8
        fx_y = self.player.y
        self.effects.append((fx_x, fx_y, self.img_attack2 or self.img_attack, 400))
        try:
            self.play_sound('attack')
        except Exception:
            pass

    def _special_r(self):
        # placeholder phase move R: wider effect
        fx_x = max(0, self.player.x - 8)
        fx_y = self.player.y
        self.effects.append((fx_x, fx_y, self.assets.get('blodfx') or self.img_attack2, 500))
        try:
            self.play_sound('attack')
        except Exception:
            pass

    def play_sound(self, name):
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
        if name == 'attack':
            threading.Thread(target=_beep, args=(800, 80), daemon=True).start()
        elif name == 'minion_die':
            threading.Thread(target=_beep, args=(400, 140), daemon=True).start()
        elif name == 'boss_die':
            threading.Thread(target=_beep, args=(220, 300), daemon=True).start()
        else:
            threading.Thread(target=_beep, args=(600, 100), daemon=True).start()


def main():
    root = tk.Tk()
    game = Game(root)
    root.mainloop()


if __name__ == '__main__':
    main()
