from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import tkinter as tk

from PIL import Image, ImageOps, ImageTk

from .engine import GameEngine
from .iig import load_iig
from .orb_projection import depth_scale, lane_screen_y, parallax_screen_x, sideview_screen_y
from .ui_skin import load_ui_skin
from .xinput import available as xinput_available, read_gamepad


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


class IllusionCanvasApp:
    def __init__(self, document: dict, game_path: Path | None = None) -> None:
        self.document = document
        self.engine = GameEngine(document)
        self.game_path = game_path
        self.ui_skin = load_ui_skin(document, game_path.parent if game_path else None)
        self.ui_images: dict[tuple[str, str], tk.PhotoImage] = {}
        self._pil_images: dict[Path, Image.Image] = {}
        self._frame_images: list[ImageTk.PhotoImage] = []
        self._backdrop_cache: dict[tuple[Path, int, int], ImageTk.PhotoImage] = {}
        self._sprite_cache: dict[tuple[Path, int, int, int, int, int], ImageTk.PhotoImage] = {}
        self.runtime_manifest = self._load_runtime_manifest()
        self.runtime_assets = self._index_runtime_assets()
        self.player_animation_pack = self._load_player_animation_pack()
        self.prototype = document.get("prototype", {})
        self.mode = "title"
        self.title_options = ["Start Prototype", "Ship Adventure Test", "Controls", "Quit"]
        self.title_index = 0
        self.controller_supported = xinput_available()
        self.controller_state: dict = {}
        self.previous_controller_state: dict = {}
        self.ship_state = {"x": 220.0, "y": 300.0, "vx": 0.0, "vy": 0.0, "boost": 100.0, "broadside_cooldown": 0}
        self.pet_tutorial_state = {"pet_id": None, "x": 180.0, "y": 360.0, "vx": 0.0, "vy": 0.0, "dummy_hp": 42}
        self.save_path = game_path.with_suffix(".save.json") if game_path else Path("aridfeihth.save.json")
        self.root = tk.Tk()
        self.root.title(self.ui_skin.get("theme_name", "IllusionCanvasInteractive"))
        self.canvas = tk.Canvas(self.root, width=1120, height=720, bg=self.ui_skin["palette"].get("panel_alt", "#0e1726"), highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.pressed: set[str] = set()
        self.previous_pressed: set[str] = set()
        self.root.bind("<KeyPress>", self._on_press)
        self.root.bind("<KeyRelease>", self._on_release)
        self.root.after(33, self._tick)

    def _on_press(self, event) -> None:
        self.pressed.add(event.keysym.lower())

    def _on_release(self, event) -> None:
        self.pressed.discard(event.keysym.lower())

    def _tick(self) -> None:
        current = set(self.pressed)
        self.controller_state = read_gamepad() or {}
        if self.mode == "title":
            self._tick_title(current)
        elif self.mode == "controls":
            self._tick_controls(current)
        elif self.mode == "ship_test":
            self._tick_ship_test(current)
        elif self.mode == "pet_tutorial":
            self._tick_pet_tutorial(current)
        else:
            commands = self._build_commands(current)
            if self._just_pressed(current, "f5"):
                self._save_game()
                snapshot = self.engine.snapshot()
            elif self._just_pressed(current, "f9"):
                self._load_game()
                snapshot = self.engine.snapshot()
            else:
                snapshot = self.engine.step(commands)
            if snapshot.get("interaction", {}).get("type") == "hologem_visualizer":
                self.pet_tutorial_state = {"pet_id": snapshot["interaction"].get("pet_id") or snapshot["player"].get("tutorial_pet"), "x": 180.0, "y": 360.0, "vx": 0.0, "vy": 0.0, "dummy_hp": 42}
                self.mode = "pet_tutorial"
            self._render(snapshot)
        self.previous_pressed = current
        self.previous_controller_state = dict(self.controller_state)
        self.root.after(33, self._tick)

    def _just_pressed(self, current: set[str], key: str) -> bool:
        return key in current and key not in self.previous_pressed

    def _controller_pressed(self, key: str) -> bool:
        return bool(self.controller_state.get(key)) and not bool(self.previous_controller_state.get(key))

    def _axis_active(self, axis_name: str, threshold: float) -> bool:
        value = float(self.controller_state.get(axis_name, 0.0))
        return value >= threshold if threshold > 0 else value <= threshold

    def _build_commands(self, current: set[str]) -> dict:
        left_active = "left" in current or "a" in current or self._axis_active("left_x", -0.35) or self.controller_state.get("dpad_left")
        right_active = "right" in current or "d" in current or self._axis_active("left_x", 0.35) or self.controller_state.get("dpad_right")
        jump_pressed = self._just_pressed(current, "up") or self._just_pressed(current, "w") or self._controller_pressed("a")
        attack_pressed = self._just_pressed(current, "z") or self._controller_pressed("x")
        burst_pressed = self._just_pressed(current, "x") or self._controller_pressed("y")
        chorus_pressed = self._just_pressed(current, "c") or self._controller_pressed("rb")
        dodge_pressed = self._just_pressed(current, "space") or self._controller_pressed("b")
        interact_pressed = self._just_pressed(current, "e") or self._controller_pressed("back")
        rest_pressed = self._just_pressed(current, "r")
        weave_pressed = self._just_pressed(current, "v") or (float(self.controller_state.get("rt", 0.0)) > 0.65 and float(self.previous_controller_state.get("rt", 0.0)) <= 0.65)
        return {
            "left": left_active,
            "right": right_active,
            "jump": jump_pressed,
            "attack": attack_pressed,
            "burst": burst_pressed,
            "chorus_toggle": chorus_pressed,
            "dodge": dodge_pressed,
            "interact": interact_pressed,
            "rescue": interact_pressed,
            "rest": rest_pressed,
            "bond_weave": weave_pressed,
        }

    def _load_image(self, collection: str, key: str) -> tk.PhotoImage | None:
        entry = self.ui_skin.get(collection, {}).get(key)
        if not entry:
            return None
        if isinstance(entry, str):
            entry = {"path": entry}
        image_key = (collection, key)
        if image_key in self.ui_images:
            return self.ui_images[image_key]
        path = Path(entry.get("path", ""))
        if not path.exists():
            return None
        image = tk.PhotoImage(file=str(path))
        subsample = max(1, int(entry.get("subsample", 1)))
        if subsample > 1:
            image = image.subsample(subsample, subsample)
        self.ui_images[image_key] = image
        return image

    def _resolve_asset_path(self, asset_path: str | None) -> Path | None:
        if not asset_path:
            return None
        candidate = Path(asset_path)
        if candidate.exists():
            return candidate
        if self.game_path:
            resolved = (self.game_path.parent / candidate).resolve()
            if resolved.exists():
                return resolved
        resolved = (WORKSPACE_ROOT / candidate).resolve()
        if resolved.exists():
            return resolved
        return None

    def _load_runtime_manifest(self) -> dict:
        candidates: list[Path] = []
        automation = self.document.get("automation", {})
        runtime_path = automation.get("runtime_manifest")
        resolved_runtime = self._resolve_asset_path(runtime_path)
        if resolved_runtime is not None:
            candidates.append(resolved_runtime)
        project = self.document.get("metadata", {}).get("project")
        if project:
            candidates.append(WORKSPACE_ROOT / project / "generated" / f"{project}_runtime_manifest.json")
        candidates.append(WORKSPACE_ROOT / "aridfeihth" / "generated" / "aridfeihth_runtime_manifest.json")
        for candidate in candidates:
            if candidate.exists():
                return json.loads(candidate.read_text(encoding="utf-8"))
        return {"assets": []}

    def _index_runtime_assets(self) -> dict[str, dict]:
        indexed: dict[str, dict] = {}
        for asset in self.runtime_manifest.get("assets", []):
            resolved = self._resolve_asset_path(asset.get("source_path"))
            indexed[asset["asset_id"]] = {**asset, "resolved_path": resolved}
        return indexed

    def _load_player_animation_pack(self) -> dict:
        pack = self.runtime_assets.get("field_handler_animation_pack")
        if pack and pack.get("resolved_path") and pack["resolved_path"].exists():
            return json.loads(pack["resolved_path"].read_text(encoding="utf-8"))
        fallback = WORKSPACE_ROOT / "aridfeihth" / "production_raw" / "previews" / "field_handler_animations.json"
        if fallback.exists():
            return json.loads(fallback.read_text(encoding="utf-8"))
        return {"animations": {}}

    def _load_pil_image(self, path: Path | None) -> Image.Image | None:
        if path is None:
            return None
        if path not in self._pil_images:
            self._pil_images[path] = Image.open(path).convert("RGBA")
        return self._pil_images[path]

    def _tick_title(self, current: set[str]) -> None:
        up = self._just_pressed(current, "up") or self._controller_pressed("dpad_up") or self._axis_active("left_y", 0.45)
        down = self._just_pressed(current, "down") or self._controller_pressed("dpad_down") or self._axis_active("left_y", -0.45)
        accept = self._just_pressed(current, "return") or self._just_pressed(current, "z") or self._controller_pressed("a") or self._controller_pressed("start")
        if up:
            self.title_index = (self.title_index - 1) % len(self.title_options)
        if down:
            self.title_index = (self.title_index + 1) % len(self.title_options)
        if accept:
            selection = self.title_options[self.title_index]
            if selection == "Start Prototype":
                self.mode = "game"
            elif selection == "Ship Adventure Test":
                self.mode = "ship_test"
            elif selection == "Controls":
                self.mode = "controls"
            elif selection == "Quit":
                self.root.destroy()
                return
        self._render_title()

    def _tick_controls(self, current: set[str]) -> None:
        if self._just_pressed(current, "escape") or self._controller_pressed("b") or self._controller_pressed("back"):
            self.mode = "title"
        self._render_controls()

    def _tick_ship_test(self, current: set[str]) -> None:
        if self._just_pressed(current, "escape") or self._controller_pressed("back"):
            self.mode = "title"
        left = -1 if ("left" in current or self.controller_state.get("dpad_left") or self._axis_active("left_x", -0.35)) else 1 if ("right" in current or self.controller_state.get("dpad_right") or self._axis_active("left_x", 0.35)) else 0
        vertical = -1 if ("up" in current or self.controller_state.get("dpad_up") or self._axis_active("left_y", 0.35)) else 1 if ("down" in current or self.controller_state.get("dpad_down") or self._axis_active("left_y", -0.35)) else 0
        boost = float(self.controller_state.get("rt", 0.0)) > 0.35 or "shift_l" in current
        broadside = self._just_pressed(current, "z") or self._controller_pressed("x")
        brake = float(self.controller_state.get("lt", 0.0)) > 0.35 or self._just_pressed(current, "space")
        if boost and self.ship_state["boost"] > 0:
            self.ship_state["vx"] += left * 0.8
            self.ship_state["vy"] += vertical * 0.4
            self.ship_state["boost"] = max(0.0, self.ship_state["boost"] - 1.5)
        else:
            self.ship_state["vx"] += left * 0.35
            self.ship_state["vy"] += vertical * 0.18
            self.ship_state["boost"] = min(100.0, self.ship_state["boost"] + 0.4)
        if brake:
            self.ship_state["vx"] *= 0.82
            self.ship_state["vy"] *= 0.75
        if broadside and self.ship_state["broadside_cooldown"] <= 0:
            self.ship_state["broadside_cooldown"] = 18
        if self.ship_state["broadside_cooldown"] > 0:
            self.ship_state["broadside_cooldown"] -= 1
        self.ship_state["x"] = max(120.0, min(1000.0, self.ship_state["x"] + self.ship_state["vx"]))
        self.ship_state["y"] = max(180.0, min(560.0, self.ship_state["y"] + self.ship_state["vy"]))
        self.ship_state["vx"] *= 0.94
        self.ship_state["vy"] *= 0.9
        self._render_ship_test()

    def _tick_pet_tutorial(self, current: set[str]) -> None:
        if self._just_pressed(current, "escape") or self._controller_pressed("back"):
            self.mode = "game"
        left = -1 if ("left" in current or self.controller_state.get("dpad_left") or self._axis_active("left_x", -0.35)) else 1 if ("right" in current or self.controller_state.get("dpad_right") or self._axis_active("left_x", 0.35)) else 0
        jump = self._just_pressed(current, "up") or self._controller_pressed("a")
        attack = self._just_pressed(current, "z") or self._controller_pressed("x")
        pulse = self._just_pressed(current, "x") or self._controller_pressed("y")
        self.pet_tutorial_state["vx"] += left * 0.5
        if jump:
            self.pet_tutorial_state["vy"] = -4.8
        self.pet_tutorial_state["vy"] += 0.22
        self.pet_tutorial_state["x"] = max(90.0, min(1030.0, self.pet_tutorial_state["x"] + self.pet_tutorial_state["vx"]))
        self.pet_tutorial_state["y"] = min(500.0, self.pet_tutorial_state["y"] + self.pet_tutorial_state["vy"])
        if self.pet_tutorial_state["y"] >= 500.0:
            self.pet_tutorial_state["y"] = 500.0
            self.pet_tutorial_state["vy"] = 0.0
        self.pet_tutorial_state["vx"] *= 0.86
        if attack:
            self.pet_tutorial_state["dummy_hp"] = max(0, self.pet_tutorial_state["dummy_hp"] - 4)
        if pulse:
            self.pet_tutorial_state["dummy_hp"] = max(0, self.pet_tutorial_state["dummy_hp"] - 6)
        self._render_pet_tutorial()

    def _draw_backdrop(self, room: dict, width: int, height: int) -> bool:
        asset_id = room.get("backdrop_asset") or f"{room.get('id')}_backdrop"
        asset = self.runtime_assets.get(asset_id)
        if not asset or not asset.get("resolved_path"):
            return False
        cache_key = (asset["resolved_path"], width, height)
        image = self._backdrop_cache.get(cache_key)
        if image is None:
            backdrop = self._load_pil_image(asset["resolved_path"])
            if backdrop is None:
                return False
            resized = backdrop.resize((width, height), Image.Resampling.NEAREST)
            image = ImageTk.PhotoImage(resized)
            self._backdrop_cache[cache_key] = image
        self._frame_images.append(image)
        self.canvas.create_image(0, 0, image=image, anchor="nw")
        return True

    def _resolve_player_frame(self, snapshot: dict) -> tuple[int, int, int, bool]:
        animation = snapshot["player"].get("animation", {})
        animation_name = animation.get("name", "idle")
        spec = self.player_animation_pack.get("animations", {}).get(animation_name)
        if not spec:
            return (0, 0, 2, False)
        playback_frames = spec.get("playback_frames", [])
        if not playback_frames:
            return (0, 0, 2, False)
        frame_duration_ms = max(1, int(self.player_animation_pack.get("timing_rule", {}).get("frame_duration_ms", 70)))
        elapsed_ticks = max(0, int(snapshot.get("tick", 0)) - int(animation.get("started_tick", snapshot.get("tick", 0))))
        frame_index = int((elapsed_ticks * 33) // frame_duration_ms)
        if spec.get("loop", True):
            frame_index %= len(playback_frames)
        else:
            frame_index = min(frame_index, len(playback_frames) - 1)
        frame = playback_frames[frame_index]
        return (int(frame.get("row", 0)), int(frame.get("col", 0)), 3, snapshot["player"].get("facing", 1) < 0)

    def _draw_player_sprite(self, snapshot: dict, player_x: float, player_y: float, player_scale: float) -> bool:
        asset = self.runtime_assets.get("field_handler_sheet")
        if not asset or not asset.get("resolved_path"):
            return False
        row, col, zoom, mirrored = self._resolve_player_frame(snapshot)
        size = max(64, int(64 * zoom * player_scale))
        cache_key = (asset["resolved_path"], row, col, zoom, size, int(mirrored))
        image = self._sprite_cache.get(cache_key)
        if image is None:
            sheet = self._load_pil_image(asset["resolved_path"])
            if sheet is None:
                return False
            frame = sheet.crop((col * 64, row * 64, (col + 1) * 64, (row + 1) * 64))
            if mirrored:
                frame = ImageOps.mirror(frame)
            frame = frame.resize((size, size), Image.Resampling.NEAREST)
            image = ImageTk.PhotoImage(frame)
            self._sprite_cache[cache_key] = image
        self._frame_images.append(image)
        self.canvas.create_image(int(player_x), int(player_y - 54 * player_scale), image=image, anchor="s")
        return True

    def _draw_hud_pack(self) -> None:
        asset = self.runtime_assets.get("aridfeihth_hud_pack")
        if not asset or not asset.get("resolved_path"):
            return
        cache_key = (asset["resolved_path"], 640, 160)
        image = self._backdrop_cache.get(cache_key)
        if image is None:
            hud = self._load_pil_image(asset["resolved_path"])
            if hud is None:
                return
            scaled = hud.resize((640, 160), Image.Resampling.NEAREST)
            image = ImageTk.PhotoImage(scaled)
            self._backdrop_cache[cache_key] = image
        self._frame_images.append(image)
        self.canvas.create_image(24, 18, image=image, anchor="nw")

    def _render_title(self) -> None:
        width = int(self.canvas.winfo_width())
        height = int(self.canvas.winfo_height())
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, width, height, fill="#120d13", outline="")
        self.canvas.create_text(width // 2, 96, text=self.document["metadata"]["title"], fill="#f1dfc4", font=("Consolas", 26, "bold"))
        self.canvas.create_text(width // 2, 132, text="Tech-fantasy desert-pirate prototype", fill="#c99d63", font=("Consolas", 12))
        self.canvas.create_text(width // 2, 168, text="Kingdom stone on one mountain. Spiritual fief on the other.", fill="#8ca8b9", font=("Consolas", 11))
        for index, option in enumerate(self.title_options):
            y = 250 + index * 42
            fill = "#f6e1bb" if index == self.title_index else "#7f8f9d"
            self.canvas.create_text(width // 2, y, text=option, fill=fill, font=("Consolas", 18 if index == self.title_index else 14, "bold" if index == self.title_index else "normal"))
        ship_label = self.prototype.get("ship_adventure_mode", {}).get("description", "")
        self.canvas.create_text(width // 2, height - 120, text=ship_label, fill="#c7b07d", font=("Consolas", 10), width=760)
        controller_text = "Xbox Series controller ready" if self.controller_supported else "Keyboard active; XInput controller not detected"
        self.canvas.create_text(width // 2, height - 84, text=controller_text, fill="#9cb8c8", font=("Consolas", 10))
        self.canvas.create_text(width // 2, height - 52, text="Enter/A or Start to select   Esc/Back to return", fill="#d2d7de", font=("Consolas", 10))

    def _render_controls(self) -> None:
        width = int(self.canvas.winfo_width())
        height = int(self.canvas.winfo_height())
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, width, height, fill="#140f18", outline="")
        self.canvas.create_text(width // 2, 70, text="Prototype Controls", fill="#f2e1c9", font=("Consolas", 24, "bold"))
        lines = [
            "Keyboard: Arrows/WASD move, Up/W jump, Z attack, X burst, C chorus, Space dodge, E interact, V bond weave, F5/F9 save/load",
            "Xbox Series: Left Stick or D-pad move, A jump, X attack, Y burst, RB chorus, B dodge, Back interact, RT bond weave, Start confirm/menu",
            "Prototype systems: 13 player moves taste, 6 pet tutorial moves, 8 enemy archetypes, 16 boss moves, gear + XP + weapon points",
        ]
        for index, line in enumerate(lines):
            self.canvas.create_text(width // 2, 180 + index * 56, text=line, fill="#d8dee4", font=("Consolas", 11), width=920)
        self.canvas.create_text(width // 2, height - 60, text="Esc or Controller Back returns to title", fill="#b7c4d0", font=("Consolas", 10))

    def _render_ship_test(self) -> None:
        width = int(self.canvas.winfo_width())
        height = int(self.canvas.winfo_height())
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, width, height, fill="#1a1820", outline="")
        self.canvas.create_rectangle(0, height * 0.62, width, height, fill="#4f342c", outline="")
        for band in range(6):
            y = 100 + band * 46
            color = "#2a3645" if band % 2 == 0 else "#3d4a58"
            self.canvas.create_line(0, y, width, y, fill=color, width=3)
        ship_x = self.ship_state["x"]
        ship_y = self.ship_state["y"]
        self.canvas.create_polygon(ship_x - 46, ship_y + 18, ship_x + 30, ship_y + 18, ship_x + 48, ship_y, ship_x - 52, ship_y, fill="#7f5a3f", outline="#24160f", width=2)
        self.canvas.create_rectangle(ship_x - 10, ship_y - 60, ship_x + 8, ship_y, fill="#8fa3b5", outline="#1f252e")
        self.canvas.create_polygon(ship_x, ship_y - 58, ship_x + 36, ship_y - 20, ship_x, ship_y - 6, fill="#c7b07d", outline="#40362a")
        if self.ship_state["broadside_cooldown"] > 12:
            self.canvas.create_oval(ship_x + 52, ship_y - 6, ship_x + 88, ship_y + 22, fill="#d48a4a", outline="")
        self.canvas.create_text(32, 28, anchor="nw", text="Ship Adventure Test", fill="#f4dfc6", font=("Consolas", 22, "bold"))
        self.canvas.create_text(32, 64, anchor="nw", text="A fleeting aerial-skimming pirate ship drill projected from Aridfeihth's harbor cameo.", fill="#c7d4df", font=("Consolas", 11))
        self.canvas.create_text(32, 100, anchor="nw", text=f"Boost {self.ship_state['boost']:.0f}   Broadside CD {self.ship_state['broadside_cooldown']}", fill="#d9ae6a", font=("Consolas", 11))
        self.canvas.create_text(32, height - 54, anchor="nw", text="Left Stick steer  A skim lift  X broadside  RT burn boost  LT anchor brake  Back return", fill="#d9dde2", font=("Consolas", 10))

    def _render_pet_tutorial(self) -> None:
        width = int(self.canvas.winfo_width())
        height = int(self.canvas.winfo_height())
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, width, height, fill="#0f1218", outline="")
        for gx in range(0, width, 32):
            self.canvas.create_line(gx, 0, gx, height, fill="#1d2832")
        for gy in range(0, height, 32):
            self.canvas.create_line(0, gy, width, gy, fill="#1d2832")
        self.canvas.create_text(width // 2, 56, text="Munki Hologem Refraction Visualizer", fill="#f0e2c5", font=("Consolas", 22, "bold"))
        self.canvas.create_text(width // 2, 88, text="Optional pet tutorial: assume direct SimIAM control and test six inputs.", fill="#9db9ca", font=("Consolas", 11))
        x = self.pet_tutorial_state["x"]
        y = self.pet_tutorial_state["y"]
        self.canvas.create_oval(x - 18, y - 18, x + 18, y + 18, fill="#8bd0df", outline="#d6f7ff", width=2)
        self.canvas.create_oval(850, 446, 910, 506, fill="#8d4f4f", outline="#2d1212", width=2)
        self.canvas.create_text(880, 426, text=f"Dummy {self.pet_tutorial_state['dummy_hp']}", fill="#f1d2d2", font=("Consolas", 10))
        for index, move in enumerate(self.prototype.get("pet_tutorial_moves", [])):
            self.canvas.create_text(56, 150 + index * 28, anchor="nw", text=f"{move['input']}: {move['name']} - {move['effect']}", fill="#dde6ef", font=("Consolas", 10))
        self.canvas.create_text(40, height - 54, anchor="nw", text="A jump  X attack  Y focus pulse  Back return", fill="#d3d9df", font=("Consolas", 10))

    def _draw_interactables(self, snapshot: dict, width: int, height: int) -> None:
        for obj in snapshot["room"].get("layout", {}).get("objects", []):
            obj_x = parallax_screen_x(float(obj.get("x", 0)), snapshot["player"]["x"], width, 1.0)
            obj_y = sideview_screen_y(height, float(obj.get("y", 0)))
            obj_type = obj.get("type")
            color = "#d1ad6d"
            if obj_type == "hologem_visualizer":
                color = "#88d7ea"
            elif obj_type == "ship_console":
                color = "#c8835d"
            elif obj_type == "puzzle_switch":
                color = "#b95e44"
            elif obj_type in {"gear_cache", "weapon_cache", "xp_cache"}:
                color = "#c7c0a2"
            self.canvas.create_rectangle(obj_x - 8, obj_y - 26, obj_x + 8, obj_y, fill=color, outline="#161616")
            self.canvas.create_text(obj_x, obj_y - 34, text=obj.get("label", obj_type), fill="#efe3c6", font=("Consolas", 8))

    def _save_game(self) -> None:
        payload = self.engine.export_save_data()
        self.save_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.engine.last_event = f"Saved expedition state to {self.save_path.name}."

    def _load_game(self) -> None:
        if not self.save_path.exists():
            self.engine.last_event = "No save file exists for this expedition yet."
            return
        payload = json.loads(self.save_path.read_text(encoding="utf-8"))
        self.engine.load_save_data(payload)

    def _render(self, snapshot: dict) -> None:
        width = int(self.canvas.winfo_width())
        height = int(self.canvas.winfo_height())
        self.canvas.delete("all")
        self._frame_images = []
        room = snapshot["room"]

        palette_skin = self.ui_skin.get("palette", {})
        ink = palette_skin.get("ink", "#f2f4f7")
        accent = palette_skin.get("accent", "#f4cf86")
        accent_soft = palette_skin.get("accent_soft", "#a6c8f2")
        success = palette_skin.get("success", "#d8fff8")
        warning = palette_skin.get("warning", "#ffd38d")

        if not self._draw_backdrop(room, width, height):
            self.canvas.create_rectangle(0, 0, width, height * 0.55, fill=palette_skin.get("sky", "#13233d"), outline="")
            self.canvas.create_rectangle(0, height * 0.55, width, height, fill=palette_skin.get("ground", "#1f1d2b"), outline="")
            self.canvas.create_polygon(
                120,
                height * 0.56,
                width - 120,
                height * 0.56,
                width,
                height,
                0,
                height,
                fill=palette_skin.get("floor", "#2d3642"),
                outline="",
            )

        shell_image = self._load_image("runtime_assets", "shell_frame")
        if shell_image is not None:
            self.canvas.create_image(width // 2, height // 2, image=shell_image)

        ground_line = sideview_screen_y(height, 0.0)
        layout = room.get("layout", {})
        for zone in layout.get("encounter_zones", []):
            zone_left = parallax_screen_x(float(zone.get("x1", 0)), snapshot["player"]["x"], width, 1.0)
            zone_right = parallax_screen_x(float(zone.get("x2", 0)), snapshot["player"]["x"], width, 1.0)
            self.canvas.create_rectangle(
                zone_left,
                sideview_screen_y(height, 5.2),
                zone_right,
                ground_line + 8,
                fill=zone.get("color", "#573f52"),
                stipple="gray25",
                outline="",
            )
        for platform in layout.get("platforms", []):
            left = parallax_screen_x(float(platform.get("x1", 0)), snapshot["player"]["x"], width, 1.0)
            right = parallax_screen_x(float(platform.get("x2", 100)), snapshot["player"]["x"], width, 1.0)
            top = sideview_screen_y(height, float(platform.get("y", 0)))
            self.canvas.create_rectangle(left, top - 10, right, top + 4, fill=platform.get("color", palette_skin.get("floor", "#2d3642")), outline="")
        for hazard in layout.get("hazards", []):
            left = parallax_screen_x(float(hazard.get("x1", 0)), snapshot["player"]["x"], width, 1.0)
            right = parallax_screen_x(float(hazard.get("x2", 0)), snapshot["player"]["x"], width, 1.0)
            hazard_y = sideview_screen_y(height, float(hazard.get("y", 0)))
            for x in range(int(left), int(right), 18):
                self.canvas.create_polygon(x, hazard_y + 6, x + 9, hazard_y - 10, x + 18, hazard_y + 6, fill=hazard.get("color", "#d96a56"), outline="")

        self._draw_interactables(snapshot, width, height)

        self._draw_hud_pack()

        hud_frame = self._load_image("runtime_assets", "hud_frame")
        if hud_frame is not None:
            self.canvas.create_image(18, 14, image=hud_frame, anchor="nw")

        sidebar_frame = self._load_image("runtime_assets", "sidebar_frame")
        if sidebar_frame is not None:
            self.canvas.create_image(width - 18, 14, image=sidebar_frame, anchor="ne")

        palette = room.get("palette", ["#1f3552", "#284b6d", "#e2a45f"])
        for index, color in enumerate(palette[:-1]):
            y = lane_screen_y(height, index, lane_count=3)
            self.canvas.create_rectangle(0, y - 18, width, y + 18, fill=color, outline="")
        for layer_index, layer in enumerate(room.get("parallax", []), start=1):
            layer_x = parallax_screen_x(layer["x"], snapshot["player"]["x"], width, layer.get("parallax", 0.45))
            self.canvas.create_rectangle(
                layer_x - 70,
                lane_screen_y(height, min(layer_index, 3), lane_count=4) - 80,
                layer_x + 70,
                lane_screen_y(height, min(layer_index, 3), lane_count=4) + 20,
                fill=layer.get("color", "#40506a"),
                outline="",
            )
            self.canvas.create_text(layer_x, lane_screen_y(height, min(layer_index, 3), lane_count=4) - 96, text=layer["label"], fill="#dce5f0", font=("Consolas", 9))

        player_x = parallax_screen_x(snapshot["player"]["x"], snapshot["player"]["x"], width, 1.0)
        player_scale = depth_scale(0.3)
        player_y = sideview_screen_y(height, snapshot["player"]["y"])
        if not self._draw_player_sprite(snapshot, player_x, player_y, player_scale):
            self.canvas.create_rectangle(
                player_x - (16 * player_scale),
                player_y - (50 * player_scale),
                player_x + (16 * player_scale),
                player_y + 10,
                fill="#f0d78c",
                outline="#1e1208",
                width=2,
            )

        for enemy in snapshot["enemies"]:
            enemy_x = parallax_screen_x(enemy["x"], snapshot["player"]["x"], width, 1.0)
            enemy_scale = depth_scale(0.2)
            enemy_y = sideview_screen_y(height, enemy.get("y", 0.0))
            self.canvas.create_oval(
                enemy_x - (18 * enemy_scale),
                enemy_y - (40 * enemy_scale),
                enemy_x + (18 * enemy_scale),
                enemy_y + 14,
                fill="#d05f5f",
                outline="#250809",
                width=2,
            )
            self.canvas.create_text(enemy_x, enemy_y - 48, text=f"{enemy['name']} {enemy['hp']}/{enemy['max_hp']}", fill="#f9d8d8", font=("Consolas", 9))

        rescue = snapshot.get("rescue")
        if rescue:
            rescue_x = parallax_screen_x(rescue["x"], snapshot["player"]["x"], width, 1.0)
            rescue_y = sideview_screen_y(height, float(rescue.get("y", 0.0)))
            self.canvas.create_polygon(
                rescue_x,
                rescue_y - 54,
                rescue_x + 18,
                rescue_y - 16,
                rescue_x,
                rescue_y + 8,
                rescue_x - 18,
                rescue_y - 16,
                fill="#6fd8c1",
                outline="#14302a",
                width=2,
            )
            self.canvas.create_text(rescue_x, rescue_y - 70, text=f"Rescue: {rescue['pet']}", fill="#d8fff8", font=("Consolas", 10))

        self.canvas.create_text(28, 22, anchor="nw", text=self.document["metadata"]["title"], fill=ink, font=("Consolas", 18, "bold"))
        self.canvas.create_text(28, 54, anchor="nw", text=room["name"], fill="#d8e4f2", font=("Consolas", 12))
        self.canvas.create_text(
            28,
            88,
            anchor="nw",
            text=(
                f"HP {snapshot['player']['hp']}/{snapshot['player']['max_hp']}   "
                f"Bond {snapshot['player']['bond_tension']}   "
                f"Weave {snapshot['player']['bond_weave_charge']}   "
                f"Chorus {'on' if snapshot['player']['chorus_active'] else 'off'}   "
                f"Lvl {snapshot['player']['level']}   XP {snapshot['player']['experience']}   WP {snapshot['player']['weapon_points']}"
            ),
            fill=accent,
            font=("Consolas", 11),
        )
        self.canvas.create_text(
            28,
            116,
            anchor="nw",
            text=(
                f"godAI omen: {snapshot['directive']['omen']}   "
                f"style: {snapshot['directive']['recommended_style']}   "
                f"egosphere: {snapshot['directive'].get('egosphere_source', snapshot['directive'].get('source', 'unknown'))}"
            ),
            fill=accent_soft,
            font=("Consolas", 10),
        )
        self.canvas.create_text(28, 144, anchor="nw", text=snapshot.get("objective", ""), fill="#e4f0cb", font=("Consolas", 10), width=780)
        self.canvas.create_text(28, 170, anchor="nw", text=snapshot["event"], fill="#cfd8e3", font=("Consolas", 10), width=780)
        self.canvas.create_text(28, 188, anchor="nw", text=f"Weapon {snapshot['player']['equipped_weapon'] or 'none'}   Sidearm {snapshot['player']['equipped_sidearm'] or 'none'}   Relic {snapshot['player']['equipped_relic'] or 'none'}", fill="#c7b07d", font=("Consolas", 10), width=780)

        milestone_y = 198
        self.canvas.create_text(28, milestone_y, anchor="nw", text="Milestones", fill=warning, font=("Consolas", 10, "bold"))
        for milestone in snapshot.get("milestones", [])[:6]:
            status = "[x]" if milestone["completed"] else "[ ]"
            self.canvas.create_text(28, milestone_y + 18, anchor="nw", text=f"{status} {milestone['label']}", fill="#d9e3ee", font=("Consolas", 9), width=760)
            milestone_y += 18
        progress = snapshot.get("route_progress", {"completed": 0, "total": 0})
        self.canvas.create_text(28, milestone_y + 6, anchor="nw", text=f"Route progress {progress['completed']}/{progress['total']}", fill=success, font=("Consolas", 10))

        popup = dict(snapshot.get("room_popup") or {})
        popup_text = popup.get("text") or snapshot.get("tutorial_tip")
        popup_template = popup.get("template", "tutorial_tip_shell")
        popup_title = popup.get("title", "Tutorial Prompt")
        if popup_text:
            tip_shell = self._load_image("popup_templates", popup_template)
            if tip_shell is not None:
                self.canvas.create_image(width // 2, 214, image=tip_shell, anchor="n")
                self.canvas.create_text(width // 2, 228, text=popup_title, fill=ink, font=("Consolas", 11, "bold"))
                self.canvas.create_text(width // 2, 262, text=popup_text, fill="#dbe6cf", font=("Consolas", 10), width=420)
            else:
                self.canvas.create_text(width // 2, 214, text=popup_text, fill="#dbe6cf", font=("Consolas", 10), width=420)

        self.canvas.create_text(
            28,
            height - 56,
            anchor="nw",
            text="Arrows move  Up jump  Z attack  X burst  C chorus  Space dodge  E rescue  R rest  V weave  F5 save  F9 load",
            fill="#d8dee9",
            font=("Consolas", 10),
        )
        self.canvas.create_text(
            width - 300,
            24,
            anchor="nw",
            text="Rescued: " + ", ".join(snapshot["player"]["rescued_pets"]),
            fill="#e7f5ee",
            font=("Consolas", 10),
            width=260,
        )
        if snapshot.get("boss_defeated"):
            self.canvas.create_text(width - 300, 116, anchor="nw", text="Boss stabilized", fill=warning, font=("Consolas", 12, "bold"))

        self.canvas.create_text(width - 300, 176, anchor="nw", text=f"Save: {self.save_path.name}", fill=success, font=("Consolas", 9), width=260)
        self.canvas.create_text(width - 300, 204, anchor="nw", text=f"Inventory: {', '.join(snapshot['player']['inventory'][:5]) or 'none'}", fill="#d8e3ec", font=("Consolas", 9), width=260)
        self.canvas.create_text(width - 300, 246, anchor="nw", text=f"Controller: {'Xbox ready' if self.controller_supported else 'keyboard only'}", fill="#b8cad8", font=("Consolas", 9), width=260)
        move_preview = ", ".join(move["name"] for move in snapshot.get("available_moves", [])[:6])
        self.canvas.create_text(width - 300, 274, anchor="nw", text=f"Moves: {move_preview}", fill="#d6c7a2", font=("Consolas", 9), width=260)
        if snapshot.get("interaction"):
            self.canvas.create_text(width - 300, 330, anchor="nw", text=f"Interaction: {snapshot['interaction'].get('type')}", fill="#9fd0dd", font=("Consolas", 10), width=260)

        if self.ui_skin.get("font_atlases"):
            atlas_names = ", ".join(self.ui_skin["font_atlases"].keys())
            self.canvas.create_text(width - 300, 150, anchor="nw", text=f"Atlases: {atlas_names}", fill=success, font=("Consolas", 9), width=260)

    def run(self) -> int:
        self.root.mainloop()
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run IllusionCanvasInteractive")
    parser.add_argument("game", nargs="?", default=str(Path(__file__).resolve().parent.parent / "sample_games" / "aridfeihth_vertical_slice.iig"))
    args = parser.parse_args(argv)
    game_path = Path(args.game)
    document = load_iig(game_path)
    app = IllusionCanvasApp(document, game_path)
    return app.run()