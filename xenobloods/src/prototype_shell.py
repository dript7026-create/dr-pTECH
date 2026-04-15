from __future__ import annotations

import argparse
import atexit
import math
import time
from pathlib import Path
import subprocess
import sys
import tkinter as tk
import json

try:
    import winsound
except ImportError:
    winsound = None

from PIL import Image, ImageTk

from jumpclip_xenobloods_pipeline import load_link_manifest, load_serviced_preview_assets, sync_runtime_assets_from_link
from prototype_asset_registry import PrototypeAssetRegistry
from prototype_gameplay_flow import GameplayMode, GameplayPrototypeController
from prototype_metroidvania_runtime import BattlePhase, MetroidvaniaRuntime, PresentationMode, ROOMS, RuntimeInput
from prototype_sprite_bank import ensure_sprite_bank
from prototype_xinput import (
    XINPUT_GAMEPAD_A,
    XINPUT_GAMEPAD_B,
    XINPUT_GAMEPAD_BACK,
    XINPUT_GAMEPAD_LEFT_SHOULDER,
    XINPUT_GAMEPAD_RIGHT_SHOULDER,
    XINPUT_GAMEPAD_START,
    XINPUT_GAMEPAD_X,
    XINPUT_GAMEPAD_Y,
    ControllerSnapshot,
    XInputController,
)
from xenobloods_systems import create_starting_player


ROOT = Path(__file__).resolve().parents[1]
AUDIO_REPORT = ROOT / "assets" / "audio" / "generated_manifest.json"
MUSIC_LOOP_HELPER = ROOT / "src" / "prototype_audio_loop.py"


class XenobloodsShell:
    def __init__(self) -> None:
        self.player = create_starting_player("Ishtasha")
        self.flow = GameplayPrototypeController(self.player)
        self.assets = PrototypeAssetRegistry()
        self.runtime_assets = sync_runtime_assets_from_link() or {}
        self.serviced_previews = load_serviced_preview_assets()
        self.link_manifest = load_link_manifest()
        self.sprite_bank = ensure_sprite_bank()
        self.controller = XInputController()
        self.previous_controller_state = ControllerSnapshot()
        self.key_held: set[str] = set()
        self.key_events: set[str] = set()
        self.image_cache: dict[tuple[str, int, int], ImageTk.PhotoImage] = {}
        self.preview_sequence_cache: dict[tuple[str, int, int], list[ImageTk.PhotoImage]] = {}
        self.last_tick = time.perf_counter()
        self.audio_library = self._load_audio_library()
        self.music_process: subprocess.Popen[str] | None = None
        self.current_music_id: str | None = None

        self.runtime = MetroidvaniaRuntime(self.flow)

        self.root = tk.Tk()
        self.root.title("XenoBloods")
        self.root.geometry("1280x760")
        self.root.configure(bg="#05070c")
        self.canvas = tk.Canvas(self.root, width=1280, height=760, bg="#05070c", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.logo_image = self._load_bitmap(self.assets.path_for("logo.main"), 420, 120)
        self.player_sprite = self._load_preview_sprite("ishtasha-botanical-spider-preview", 170, 170) or self._load_runtime_sprite("sprite_preview", 170, 170)
        self.player_sprite_far = self._load_preview_sprite("ishtasha-botanical-spider-preview", 120, 120) or self._load_runtime_sprite("sprite_preview", 120, 120)
        self.last_sound_cue_state = False
        self.last_prompt_signature: tuple[str, str] | None = None
        self.last_battle_phase: BattlePhase | None = None
        self.last_incubation_audio_nonce = 0
        atexit.register(self._stop_music)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._bind_inputs()
        self._tick()

    def _bind_inputs(self) -> None:
        for key in ("Left", "Right", "Up", "Down", "a", "d", "w", "s", "Shift_L", "Control_L"):
            self.root.bind(f"<KeyPress-{key}>", lambda event, name=key: self._on_key_press(name))
            self.root.bind(f"<KeyRelease-{key}>", lambda event, name=key: self._on_key_release(name))

        action_keys = {
            "space": "jump",
            "x": "interact",
            "z": "dodge",
            "c": "dash",
            "v": "block",
            "Return": "confirm",
            "Escape": "pause",
        }
        for key, action in action_keys.items():
            self.root.bind(f"<KeyPress-{key}>", lambda event, name=action: self._on_action_press(name))

    def _on_key_press(self, key: str) -> None:
        self.key_held.add(key)

    def _on_key_release(self, key: str) -> None:
        self.key_held.discard(key)

    def _on_action_press(self, action: str) -> None:
        self.key_events.add(action)

    def _consume_action(self, action: str) -> bool:
        if action in self.key_events:
            self.key_events.discard(action)
            return True
        return False

    def _controller_edge(self, state: ControllerSnapshot, flag: int) -> bool:
        return state.pressed(flag) and not self.previous_controller_state.pressed(flag)

    def _trigger_edge(self, current_value: int, previous_value: int, threshold: int = 100) -> bool:
        return current_value > threshold and previous_value <= threshold

    def _compose_input(self, controller_state: ControllerSnapshot) -> RuntimeInput:
        move_x = 0.0
        if "Left" in self.key_held or "a" in self.key_held:
            move_x -= 1.0
        if "Right" in self.key_held or "d" in self.key_held:
            move_x += 1.0
        move_y = 0.0
        if "Up" in self.key_held or "w" in self.key_held:
            move_y -= 1.0
        if "Down" in self.key_held or "s" in self.key_held:
            move_y += 1.0

        if controller_state.connected:
            if abs(controller_state.left_x) > 7000:
                move_x = controller_state.left_x / 32767.0
            if abs(controller_state.left_y) > 7000:
                move_y = -(controller_state.left_y / 32767.0)

        return RuntimeInput(
            move_x=max(-1.0, min(1.0, move_x)),
            move_y=max(-1.0, min(1.0, move_y)),
            jump_pressed=self._consume_action("jump") or self._controller_edge(controller_state, XINPUT_GAMEPAD_A),
            dash_pressed=self._consume_action("dash") or self._controller_edge(controller_state, XINPUT_GAMEPAD_Y),
            dodge_pressed=self._consume_action("dodge") or self._trigger_edge(controller_state.left_trigger, self.previous_controller_state.left_trigger) or self._controller_edge(controller_state, XINPUT_GAMEPAD_B),
            interact_pressed=self._consume_action("interact") or self._controller_edge(controller_state, XINPUT_GAMEPAD_X) or self._controller_edge(controller_state, XINPUT_GAMEPAD_RIGHT_SHOULDER),
            light_attack_pressed=self._consume_action("interact") or self._controller_edge(controller_state, XINPUT_GAMEPAD_RIGHT_SHOULDER),
            heavy_attack_pressed=self._consume_action("dash") or self._trigger_edge(controller_state.right_trigger, self.previous_controller_state.right_trigger),
            block_pressed=self._consume_action("block") or self._controller_edge(controller_state, XINPUT_GAMEPAD_LEFT_SHOULDER),
            block_held=("v" in self.key_held) or controller_state.pressed(XINPUT_GAMEPAD_LEFT_SHOULDER),
            crouch_held=("Shift_L" in self.key_held) or controller_state.left_trigger > 100,
            crawl_held=("Control_L" in self.key_held) or controller_state.pressed(XINPUT_GAMEPAD_LEFT_SHOULDER),
            confirm_pressed=self._consume_action("confirm") or self._controller_edge(controller_state, XINPUT_GAMEPAD_START),
            pause_pressed=self._consume_action("pause") or self._controller_edge(controller_state, XINPUT_GAMEPAD_BACK),
        )

    def _load_bitmap(self, path: Path, width: int, height: int) -> ImageTk.PhotoImage:
        cache_key = (str(path), width, height)
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        image = Image.open(path).convert("RGBA").resize((width, height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.image_cache[cache_key] = photo
        return photo

    def _load_runtime_sprite(self, key: str, width: int, height: int) -> ImageTk.PhotoImage | None:
        path = self.runtime_assets.get(key)
        if path is None:
            return None
        runtime_path = Path(path)
        if not runtime_path.exists():
            return None
        return self._load_bitmap(runtime_path, width, height)

    def _load_preview_sprite(self, preview_name: str, width: int, height: int) -> ImageTk.PhotoImage | None:
        preview = self.serviced_previews.get(preview_name)
        if not preview or not preview.get("ready"):
            return None
        sprite_path = preview.get("sprite_preview")
        if not isinstance(sprite_path, Path) or not sprite_path.exists():
            return None
        return self._load_bitmap(sprite_path, width, height)

    def _load_preview_animation(self, preview_name: str, width: int, height: int) -> list[ImageTk.PhotoImage]:
        cache_key = (preview_name, width, height)
        if cache_key in self.preview_sequence_cache:
            return self.preview_sequence_cache[cache_key]

        preview = self.serviced_previews.get(preview_name)
        if not preview or not preview.get("ready"):
            return []
        atlas_path = preview.get("atlas")
        metadata_path = preview.get("metadata")
        if not isinstance(atlas_path, Path) or not atlas_path.exists() or not isinstance(metadata_path, Path) or not metadata_path.exists():
            return []

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        atlas = Image.open(atlas_path).convert("RGBA")
        frames: list[ImageTk.PhotoImage] = []
        for frame in metadata.get("frames", []):
            x = int(frame.get("x", 0))
            y = int(frame.get("y", 0))
            frame_width = int(frame.get("width", atlas.width))
            frame_height = int(frame.get("height", atlas.height))
            sprite = atlas.crop((x, y, x + frame_width, y + frame_height)).resize((width, height), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(sprite))
        self.preview_sequence_cache[cache_key] = frames
        return frames

    def _load_sprite_bank_animation(self, sprite_id: str, animation: str, width: int, height: int) -> list[ImageTk.PhotoImage]:
        cache_key = (f"sprite-bank:{sprite_id}:{animation}", width, height)
        if cache_key in self.preview_sequence_cache:
            return self.preview_sequence_cache[cache_key]
        sprite_info = self.sprite_bank.get("sprites", {}).get(sprite_id, {})
        animation_frames = sprite_info.get("animations", {}).get(animation, [])
        frames: list[ImageTk.PhotoImage] = []
        for relative_path in animation_frames:
            absolute_path = ROOT / relative_path
            if absolute_path.exists():
                frames.append(self._load_bitmap(absolute_path, width, height))
        self.preview_sequence_cache[cache_key] = frames
        return frames

    def _sprite_bank_frame(
        self,
        sprite_id: str,
        animation: str,
        width: int,
        height: int,
        cadence: float = 1.0,
        phase_bias: float = 0.0,
        hold_last: bool = False,
    ) -> ImageTk.PhotoImage | None:
        frames = self._load_sprite_bank_animation(sprite_id, animation, width, height)
        if not frames:
            return None
        if hold_last:
            return frames[-1]
        frame_index = int((time.perf_counter() * max(0.12, cadence) * 10.0) + phase_bias) % len(frames)
        return frames[frame_index]

    def _enemy_sprite_id(self, actor_id: str) -> str:
        return {
            "scarab_child_acolyte": "scarab_child",
            "lattice_ward": "lattice_ward",
            "lahgroid_hierophant": "lahgroid",
        }.get(actor_id, "scarab_child")

    def _battle_player_animation(self, battle: object) -> str:
        if battle.phase == BattlePhase.EYECONTACT:
            return "stalk" if battle.eyecontact_progress < 0.85 else "idle"
        if battle.phase == BattlePhase.INTRO:
            return "dash"
        if battle.phase == BattlePhase.WINDOW:
            return {
                "light_attack": "light_attack",
                "heavy_attack": "heavy_attack",
                "dodge": "dash",
                "block": "block",
            }.get(battle.selected_action, "block")
        if battle.phase == BattlePhase.RESOLVE:
            if battle.resolution_quality == "fail":
                return "hit"
            return {
                "parry": "parry",
                "light_attack": "surge",
                "heavy_attack": "surge",
                "dodge": "dash",
                "block": "block",
                "attack": "surge",
            }.get(battle.resolution_action, "idle")
        return "idle"

    def _battle_enemy_animation(self, actor_id: str, battle: object) -> str:
        if battle.phase == BattlePhase.EYECONTACT:
            if actor_id == "lattice_ward":
                return "flare"
            if actor_id in {"scarab_child_acolyte", "lahgroid_hierophant"}:
                return "feint"
            return "idle"
        if battle.phase == BattlePhase.INTRO:
            return "transition"
        if battle.phase == BattlePhase.RESOLVE:
            if self.flow.mode == GameplayMode.LAND_NAVIGATION and battle.last_resolution_strength >= 1.0:
                return "death"
            if battle.resolution_quality in {"success", "partial"}:
                return "recoil"
            if actor_id == "lattice_ward" and battle.prompt_action == "parry":
                return "flare"
            if actor_id in {"scarab_child_acolyte", "lahgroid_hierophant"} and battle.prompt_action == "parry":
                return "feint"
            return {
                "attack": "attack",
                "parry": "block",
                "block": "block",
                "dodge": "dodge",
            }.get(battle.prompt_action, "idle")
        if battle.phase == BattlePhase.WINDOW:
            if actor_id == "lattice_ward" and battle.prompt_action == "parry":
                return "flare"
            if actor_id in {"scarab_child_acolyte", "lahgroid_hierophant"} and battle.prompt_action == "parry":
                return "feint"
            return {
                "attack": "attack",
                "parry": "block",
                "block": "block",
                "dodge": "dodge",
            }.get(battle.prompt_action, "idle")
        return "idle"

    def _draw_banked_sprite(
        self,
        sprite_id: str,
        animation: str,
        center_x: float,
        ground_y: float,
        width: int,
        height: int,
        cadence: float,
        hold_last: bool = False,
    ) -> bool:
        sprite = self._sprite_bank_frame(sprite_id, animation, width, height, cadence=cadence, hold_last=hold_last)
        if sprite is None:
            return False
        self.canvas.create_image(center_x, ground_y, anchor="s", image=sprite)
        return True

    def _animated_preview_frame(self, preview_name: str, width: int, height: int, cadence: float = 1.0, phase_bias: float = 0.0) -> ImageTk.PhotoImage | None:
        frames = self._load_preview_animation(preview_name, width, height)
        if not frames:
            return self._load_preview_sprite(preview_name, width, height)
        frame_index = int((time.perf_counter() * max(0.1, cadence) * 10.0) + phase_bias) % len(frames)
        return frames[frame_index]

    def _battle_preview_frame(self, preview_name: str, width: int, height: int, battle: object) -> ImageTk.PhotoImage | None:
        frames = self._load_preview_animation(preview_name, width, height)
        if not frames:
            return self._load_preview_sprite(preview_name, width, height)
        if battle.phase == BattlePhase.EYECONTACT:
            if battle.eyecontact_hold > 0.0:
                frame_index = min(len(frames) - 1, max(0, len(frames) - 2))
            else:
                frame_index = min(len(frames) - 1, int(battle.eyecontact_progress * (len(frames) - 1)))
            return frames[frame_index]
        if battle.phase == BattlePhase.INTRO:
            frame_index = min(len(frames) - 1, int(min(1.0, battle.timer / 0.56) * (len(frames) - 1)))
            return frames[frame_index]
        cadence = 1.6 if battle.phase == BattlePhase.RESOLVE else 1.2
        frame_index = int(time.perf_counter() * cadence * 10.0) % len(frames)
        return frames[frame_index]

    def _load_audio_library(self) -> dict[str, Path]:
        if not AUDIO_REPORT.exists():
            return {}
        payload = json.loads(AUDIO_REPORT.read_text(encoding="utf-8"))
        library: dict[str, Path] = {}
        for section in ("music", "sfx"):
            for item in payload.get(section, []):
                clip_id = item.get("id")
                clip_path = item.get("path")
                if clip_id and clip_path:
                    raw_path = Path(str(clip_path))
                    resolved = raw_path
                    if not raw_path.is_absolute():
                        workspace_relative = (ROOT.parent / raw_path).resolve()
                        repo_relative = (ROOT / raw_path).resolve()
                        if workspace_relative.exists():
                            resolved = workspace_relative
                        elif repo_relative.exists():
                            resolved = repo_relative
                    library[str(clip_id)] = resolved
        return library

    def _play_audio_clip(self, clip_id: str) -> bool:
        clip_path = self.audio_library.get(clip_id)
        if clip_path is None or not clip_path.exists() or winsound is None:
            return False
        winsound.PlaySound(str(clip_path), winsound.SND_ASYNC | winsound.SND_FILENAME | winsound.SND_NODEFAULT)
        return True

    def _desired_music_track(self) -> str | None:
        if self.runtime.mode == PresentationMode.TITLE:
            return "title_dread_bed"
        if self.runtime.mode == PresentationMode.INCUBATION:
            return "birth_brass_horror"
        if self.runtime.mode == PresentationMode.UP_DIALOGUE:
            return "title_dread_bed"
        if self.runtime.mode == PresentationMode.LOW_PUZZLE:
            return "battle_undertow"
        if self.runtime.mode == PresentationMode.EXPLORATION:
            return "title_dread_bed"
        if self.runtime.battle.phase == BattlePhase.EYECONTACT:
            return "eyecontact_dread_bed"
        if self.flow.current_actor().actor_id == "lahgroid_hierophant":
            return "boss_hierophant_dread"
        return "battle_undertow"

    def _stop_music(self) -> None:
        if self.music_process is not None:
            self.music_process.terminate()
            self.music_process = None
        self.current_music_id = None

    def _ensure_music_track(self, track_id: str | None) -> None:
        if track_id == self.current_music_id:
            return
        self._stop_music()
        if track_id is None:
            return
        track_path = self.audio_library.get(track_id)
        if track_path is None or not track_path.exists() or not MUSIC_LOOP_HELPER.exists():
            return
        self.music_process = subprocess.Popen([sys.executable, str(MUSIC_LOOP_HELPER), str(track_path)])
        self.current_music_id = track_id

    def _on_close(self) -> None:
        self._stop_music()
        self.root.destroy()

    def _actor_sprite(self, actor_id: str, scale: int) -> ImageTk.PhotoImage:
        banked = self._sprite_bank_frame(self._enemy_sprite_id(actor_id), "idle", scale, scale, cadence=0.35)
        if banked is not None:
            return banked
        preview_name = {
            "scarab_child_acolyte": "scarab-child-basic-preview",
            "lattice_ward": "lattice-ward-preview",
            "lahgroid_hierophant": "lahgroid-boss-preview",
        }.get(actor_id)
        if preview_name is not None:
            sprite = self._load_preview_sprite(preview_name, scale, scale)
            if sprite is not None:
                return sprite
        asset_id = {
            "scarab_child_acolyte": "actor.scarab_child_acolyte",
            "lattice_ward": "actor.lattice_ward",
            "lahgroid_hierophant": "actor.lahgroid_hierophant",
        }.get(actor_id, "actor.scarab_child_acolyte")
        return self._load_bitmap(self.assets.path_for(asset_id), scale, scale)

    def _play_eyecontact_cue(self) -> None:
        if self._play_audio_clip("eyecontact_lock"):
            return
        if winsound is not None:
            winsound.Beep(784, 35)
            winsound.Beep(988, 55)
            return
        self.root.bell()

    def _play_incubation_audio_event(self, event: str) -> None:
        if self._play_audio_clip(event):
            return
        if winsound is None:
            self.root.bell()
            return
        if event == "birth_stage":
            winsound.Beep(196, 50)
            winsound.Beep(247, 70)
            return
        if event == "birth_complete":
            winsound.Beep(220, 70)
            winsound.Beep(277, 80)
            winsound.Beep(330, 90)
            return
        winsound.Beep(164, 45)
        winsound.Beep(131, 60)

    def _sync_incubation_audio(self) -> None:
        if self.runtime.mode != PresentationMode.INCUBATION:
            self.last_incubation_audio_nonce = self.runtime.incubation.audio_event_nonce
            return
        if self.runtime.incubation.audio_event_nonce == self.last_incubation_audio_nonce:
            return
        self.last_incubation_audio_nonce = self.runtime.incubation.audio_event_nonce
        self._play_incubation_audio_event(self.runtime.incubation.audio_event)

    def _sync_audio_events(self, prev_phase: BattlePhase | None, prev_prompt_signature: tuple[str, str] | None, prev_hold: float, prev_mode: PresentationMode) -> None:
        battle = self.runtime.battle
        if self.runtime.mode != PresentationMode.BATTLE:
            self.last_prompt_signature = None
            return
        prompt_signature = (battle.prompt_action, battle.prompt_lane)
        if prev_phase == BattlePhase.EYECONTACT and battle.phase == BattlePhase.EYECONTACT and prev_hold <= 0.0 < battle.eyecontact_hold:
            self._play_audio_clip("eyecontact_meet")
        if battle.phase == BattlePhase.WINDOW and (prev_phase != BattlePhase.WINDOW or prev_prompt_signature != prompt_signature):
            self._play_audio_clip(f"prompt_{battle.prompt_action}_{battle.prompt_lane}")
        if battle.phase == BattlePhase.RESOLVE and prev_phase != BattlePhase.RESOLVE:
            self._play_audio_clip(
                f"resolve_{battle.resolution_action}_{battle.resolution_lane}_{battle.resolution_quality}_{battle.resolution_timing_bucket}"
            )
        self.last_prompt_signature = prompt_signature

    def _tick(self) -> None:
        now = time.perf_counter()
        dt = min(0.033, now - self.last_tick)
        self.last_tick = now

        controller_state = self.controller.poll()
        controls = self._compose_input(controller_state)
        prev_mode = self.runtime.mode
        prev_phase = self.runtime.battle.phase if self.runtime.mode == PresentationMode.BATTLE else None
        prev_hold = self.runtime.battle.eyecontact_hold if self.runtime.mode == PresentationMode.BATTLE else 0.0
        prev_prompt_signature = (self.runtime.battle.prompt_action, self.runtime.battle.prompt_lane) if self.runtime.mode == PresentationMode.BATTLE else None
        prev_gate_locked = self.runtime.exploration.gate_locked
        self.runtime.update(dt, controls)
        self._ensure_music_track(self._desired_music_track())
        cue_pending = self.runtime.battle.sound_cue_pending
        if cue_pending and not self.last_sound_cue_state:
            self._play_eyecontact_cue()
            self.runtime.battle.sound_cue_pending = False
        self.last_sound_cue_state = cue_pending
        if not prev_gate_locked and self.runtime.exploration.gate_locked:
            self._play_audio_clip("gate_locked")
        self._sync_incubation_audio()
        self._sync_audio_events(prev_phase, prev_prompt_signature, prev_hold, prev_mode)
        self.previous_controller_state = controller_state
        self._render()
        self.root.after(16, self._tick)

    def _render(self) -> None:
        self.canvas.delete("all")
        if self.runtime.mode == PresentationMode.TITLE:
            self._draw_title_screen()
        elif self.runtime.mode == PresentationMode.INCUBATION:
            self._draw_incubation_scene()
        elif self.runtime.mode == PresentationMode.UP_DIALOGUE:
            self._draw_up_dialogue_scene()
        elif self.runtime.mode == PresentationMode.LOW_PUZZLE:
            self._draw_low_puzzle_scene()
        elif self.runtime.mode == PresentationMode.EXPLORATION:
            self._draw_exploration_scene()
        else:
            self._draw_battle_scene()

    def _curve_stage_index(self) -> int:
        if self.runtime.mode == PresentationMode.INCUBATION:
            return 0
        if self.runtime.mode == PresentationMode.UP_DIALOGUE:
            return 4
        if self.runtime.mode == PresentationMode.LOW_PUZZLE:
            return 5
        if self.runtime.mode == PresentationMode.BATTLE and self.flow.mode == GameplayMode.BOSS_REALTIME:
            return 3
        if self.runtime.mode == PresentationMode.BATTLE and self.flow.current_actor().actor_id == "lattice_ward":
            return 2
        room_id = self.runtime.exploration.room_id
        if room_id == "ossuary_rise":
            return 2
        if room_id == "boss_gate":
            return 3
        if room_id == "sunken_sanctum":
            return 5
        return 1

    def _draw_training_curve_tracker(self) -> None:
        steps = (
            ("BIRTH", "RUPTURE"),
            ("VEIN", "LESSON"),
            ("OSS", "PRESS"),
            ("BOSS", "CLIMAX"),
            ("UP", "DENOUE"),
            ("LOW", "EPILOGUE"),
        )
        active_index = self._curve_stage_index()
        self.canvas.create_rectangle(760, 18, 1248, 82, fill="#090d15", outline="#1f2a39")
        self.canvas.create_text(778, 34, text="TRAINING CURVE", anchor="w", fill="#8f99ad", font=("Segoe UI", 9, "bold"))
        for index, (label, sublabel) in enumerate(steps):
            left = 778 + index * 76
            active = index == active_index
            completed = index < active_index
            fill = "#f0dba4" if active else ("#5b7fa6" if completed else "#141b28")
            text_fill = "#081018" if active else ("#d8e0ef" if completed else "#7d8799")
            self.canvas.create_rectangle(left, 44, left + 64, 70, fill=fill, outline="#243141")
            self.canvas.create_text(left + 32, 53, text=label, fill=text_fill, font=("Segoe UI", 8, "bold"))
            self.canvas.create_text(left + 32, 64, text=sublabel, fill=text_fill, font=("Segoe UI", 7, "bold"))

    def _draw_title_screen(self) -> None:
        flash = 0.5 + 0.5 * math.sin(self.runtime.title_flash * 2.4)
        self.canvas.create_rectangle(0, 0, 1280, 760, fill="#04060b", outline="")
        for index in range(14):
            top = 90 + index * 38
            color = "#0c1220" if index % 2 == 0 else "#0a0f1a"
            self.canvas.create_rectangle(0, top, 1280, top + 22, fill=color, outline="")
        self.canvas.create_image(640, 220, image=self.logo_image)
        self.canvas.create_rectangle(514, 412, 766, 420, fill="#c6524c", outline="")
        self.canvas.create_text(640, 474, text="GRAMATOS BELOW, LAND AHEAD", fill="#cfd7e4", font=("Segoe UI", 14, "bold"))
        self.canvas.create_text(640, 620, text="PRESS A OR START", fill=f"#{int(150 + flash * 90):02x}{int(155 + flash * 80):02x}{int(180 + flash * 60):02x}", font=("Segoe UI", 18, "bold"))
        self.canvas.create_text(640, 668, text="Left Stick: Move    A: Jump    B: Dodge    X: Interact    Y: Dash", fill="#8f99ad", font=("Segoe UI", 11))

    def _draw_incubation_scene(self) -> None:
        stage = self.runtime.incubation
        player = self.flow.player
        pulse = 0.5 + 0.5 * math.sin(stage.pulse * 3.2)
        flash = stage.birth_flash
        tick = time.perf_counter()
        self.canvas.create_rectangle(0, 0, 1280, 760, fill="#06070d", outline="")
        for index in range(8):
            inset = 40 + index * 28
            self.canvas.create_oval(inset, 70 + index * 12, 1280 - inset, 700 - index * 18, outline="#151d28", width=2)
        shell_w = 180 + pulse * 24
        shell_h = 236 + pulse * 32
        for veil in range(6):
            veil_shift = math.sin(tick * 0.9 + veil) * 18
            self.canvas.create_arc(640 - shell_w - 42 - veil_shift, 392 - shell_h - 28 + veil * 10, 640 + shell_w + 42 + veil_shift, 392 + shell_h + 36, start=210 + veil * 6, extent=110, style="arc", outline="#293746", width=2)
        self.canvas.create_oval(640 - shell_w, 392 - shell_h, 640 + shell_w, 392 + shell_h, fill="#5f4836", outline="#d0b788", width=4)
        self.canvas.create_oval(640 - shell_w * 0.72, 392 - shell_h * 0.82, 640 + shell_w * 0.72, 392 + shell_h * 0.82, fill="#7a5e45", outline="#f0dba4", width=2)
        self.canvas.create_arc(640 - 74, 392 - 108, 640 + 74, 392 + 108, start=62, extent=256, style="arc", outline="#a4c676", width=4)
        self.canvas.create_line(640, 250, 640, 542, fill="#f0dba4", width=3)
        for crack in range(stage.stage_index + 1):
            spread = 28 + crack * 22
            self.canvas.create_line(640, 300 + crack * 22, 640 - spread, 364 + crack * 28, fill="#261710", width=3)
            self.canvas.create_line(640, 318 + crack * 20, 640 + spread, 386 + crack * 24, fill="#261710", width=3)
            self.canvas.create_line(640 - spread * 0.3, 332 + crack * 18, 640 - spread - 18, 402 + crack * 18, fill="#311d18", width=2)
            self.canvas.create_line(640 + spread * 0.25, 340 + crack * 16, 640 + spread + 14, 410 + crack * 16, fill="#311d18", width=2)
        fetus_x = 640 + math.sin(stage.pulse * 2.4) * 18
        fetus_y = 398 + math.cos(stage.pulse * 2.1) * 12
        self.canvas.create_oval(fetus_x - 34, fetus_y - 54, fetus_x + 26, fetus_y + 46, fill="#402a24", outline="#8c6150", width=2)
        self.canvas.create_line(fetus_x - 8, fetus_y - 8, fetus_x - 34, fetus_y + 20, fill="#d0b788", width=3)
        self.canvas.create_line(fetus_x + 4, fetus_y + 4, fetus_x + 28, fetus_y + 30, fill="#d0b788", width=3)
        self.canvas.create_line(fetus_x - 10, fetus_y + 28, fetus_x - 26, fetus_y + 64, fill="#d0b788", width=3)
        self.canvas.create_line(fetus_x + 2, fetus_y + 24, fetus_x + 22, fetus_y + 58, fill="#d0b788", width=3)
        debris_count = stage.stage_index * 5 + (6 if flash > 0.18 else 0)
        for shard in range(debris_count):
            angle = (shard / max(1, debris_count)) * math.pi * 1.55 - math.pi * 0.78
            drift = 42 + shard * 6 + flash * 46
            shard_x = 640 + math.cos(angle) * (shell_w * 0.58 + drift)
            shard_y = 392 + math.sin(angle) * (shell_h * 0.34 + drift * 0.62)
            width = 8 + (shard % 3) * 4
            self.canvas.create_polygon(
                shard_x,
                shard_y,
                shard_x + width,
                shard_y - 4,
                shard_x + width * 0.35,
                shard_y + 12,
                fill="#d0b788",
                outline="#6f5141",
            )
        for droplet in range(stage.stage_index * 4 + 4):
            angle = (droplet * 0.47) - 1.4
            radius = 28 + droplet * 9 + flash * 24
            drop_x = 640 + math.cos(angle + tick * 0.1) * radius
            drop_y = 430 + math.sin(angle) * radius * 0.65
            size = 2 + (droplet % 2)
            self.canvas.create_oval(drop_x - size, drop_y - size, drop_x + size, drop_y + size, fill="#8c6150", outline="")
        if flash > 0.0:
            radius = 120 + (1.0 - flash) * 80
            self.canvas.create_oval(640 - radius, 392 - radius * 0.72, 640 + radius, 392 + radius * 0.72, outline="#f0dba4", width=3)
        self.canvas.create_text(640, 96, text="AMNIOTIC GOURD DESCENT", fill="#f0dba4", font=("Segoe UI", 18, "bold"))
        self.canvas.create_text(640, 138, text="A brass-horror birth drill: learn lane, timing, and commit before Ishtasha is allowed into Land.", fill="#d8e0ef", font=("Segoe UI", 12, "bold"))
        self.canvas.create_text(640, 572, text=stage.tutorial_text, width=860, fill="#d8e0ef", font=("Segoe UI", 14, "bold"))
        progress = min(1.0, player.rupture_progress / 100.0)
        self.canvas.create_rectangle(402, 620, 878, 634, fill="#151d28", outline="")
        self.canvas.create_rectangle(402, 620, 402 + progress * 476, 634, fill="#a4c676", outline="")
        pulse_left = 468
        pulse_right = 812
        pulse_x = pulse_left + (stage.pulse_progress * (pulse_right - pulse_left))
        current_lane_x = {"background": 506, "midground": 640, "foreground": 774}[stage.lane_bias]
        target_lane = stage.lane_order[min(stage.stage_index, len(stage.lane_order) - 1)]
        target_lane_x = {"background": 506, "midground": 640, "foreground": 774}[target_lane]
        self.canvas.create_rectangle(pulse_left, 652, pulse_right, 664, fill="#151d28", outline="")
        window_half = stage.pulse_window_half * (pulse_right - pulse_left)
        self.canvas.create_rectangle(640 - window_half, 648, 640 + window_half, 668, outline="#f0dba4", width=2)
        self.canvas.create_line(pulse_x, 646, pulse_x, 670, fill="#d65758", width=3)
        self.canvas.create_text(640, 682, text=f"Rupture {player.rupture_progress:.0f}%   Gourd charge {player.gourd.infant_charge:.0f}%   Shell {player.gourd.shell_integrity:.2f}   Pulse {stage.pulse_strength:.2f}", fill="#8f99ad", font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(640, 704, text="Lane training and combat-style center window", fill="#8f99ad", font=("Segoe UI", 10, "bold"))
        self.canvas.create_line(506, 720, 774, 720, fill="#334153", width=2)
        for label, lane_x in (("BACK", 506), ("MID", 640), ("FORE", 774)):
            self.canvas.create_oval(lane_x - 18, 708, lane_x + 18, 732, fill="#1a2232", outline="#334153")
            self.canvas.create_text(lane_x, 720, text=label, fill="#d8e0ef", font=("Segoe UI", 8, "bold"))
        self.canvas.create_arc(target_lane_x - 28, 700, target_lane_x + 28, 740, start=0, extent=180, style="arc", outline="#f0dba4", width=3)
        self.canvas.create_oval(current_lane_x - 8, 712, current_lane_x + 8, 728, fill="#66c06a", outline="")
        self.canvas.create_text(948, 656, text="Hit center on stages 2 and 4", anchor="w", fill="#f0dba4", font=("Segoe UI", 9, "bold"))
        actions = [
            ("X", "Seed / mid"),
            ("LB", "Brace / fore / pulse"),
            ("A", "Kick / back"),
            ("Y", "Burst / fore / pulse"),
        ]
        for index, (button, label) in enumerate(actions):
            left = 194 + index * 220
            active = stage.stage_index == index
            fill = "#f0dba4" if active else "#1a2232"
            text_fill = "#081018" if active else "#d8e0ef"
            self.canvas.create_rectangle(left, 696, left + 168, 732, fill=fill, outline="#334153")
            self.canvas.create_text(left + 26, 714, text=button, fill=text_fill, font=("Segoe UI", 12, "bold"))
            self.canvas.create_text(left + 56, 714, text=label, anchor="w", fill=text_fill, font=("Segoe UI", 10, "bold"))
        self._draw_training_curve_tracker()

    def _draw_up_dialogue_scene(self) -> None:
        dialogue = self.flow.dialogue_state
        actor_id = self.flow.current_actor().actor_id
        scene = self._load_bitmap(self.assets.path_for("scene.up.dialogue"), 1280, 760)
        panel = self._load_bitmap(self.assets.path_for("panel.dialogue"), 460, 260)
        strip = self._load_bitmap(self.assets.path_for("support.up.dialogue"), 920, 160)
        actor_card = self._load_bitmap(self.assets.path_for(f"actor.{actor_id}"), 320, 360)
        self.canvas.create_image(640, 380, image=scene)
        self.canvas.create_rectangle(0, 0, 1280, 760, fill="#05070c", outline="", stipple="gray75")
        self.canvas.create_image(640, 108, image=strip)
        self.canvas.create_image(998, 404, image=actor_card)
        self.canvas.create_image(312, 442, image=panel)
        self.canvas.create_text(108, 88, text="UP DENOUEMENT", anchor="w", fill="#f0dba4", font=("Segoe UI", 18, "bold"))
        self.canvas.create_text(108, 124, text="The climax has passed. Trade literal cards until the chamber lets the pressure out.", anchor="w", fill="#d8e0ef", font=("Segoe UI", 11, "bold"))
        if dialogue is not None:
            self.canvas.create_text(118, 344, text=self.flow.status_text, anchor="w", width=360, fill="#d8e0ef", font=("Segoe UI", 13, "bold"))
            self.canvas.create_text(118, 520, text=f"Release {dialogue.successful_cards}/{dialogue.target_exchanges}", anchor="w", fill="#8f99ad", font=("Segoe UI", 11, "bold"))
            self.canvas.create_rectangle(118, 538, 382, 548, fill="#1a2232", outline="")
            progress = 0.0 if dialogue.target_exchanges <= 0 else min(1.0, dialogue.successful_cards / dialogue.target_exchanges)
            self.canvas.create_rectangle(118, 538, 118 + progress * 264, 548, fill="#66c06a", outline="")
            self.canvas.create_text(118, 576, text=f"Suspicion {dialogue.suspicion:.2f}", anchor="w", fill="#8f99ad", font=("Segoe UI", 10, "bold"))
            self.canvas.create_rectangle(118, 592, 382, 602, fill="#1a2232", outline="")
            self.canvas.create_rectangle(118, 592, 118 + min(1.0, dialogue.suspicion) * 264, 602, fill="#d65758", outline="")
            options = (("LB", "DEFER", "defer"), ("X / RB", "ANSWER", "answer"), ("Y / RT", "APPEASE", "appease"))
            for index, (button, label, card_id) in enumerate(options):
                left = 520 + index * 196
                active = dialogue.safe_card == card_id
                fill = "#f0dba4" if active else "#141b28"
                text_fill = "#081018" if active else "#d8e0ef"
                self.canvas.create_rectangle(left, 558, left + 168, 622, fill=fill, outline="#243141")
                self.canvas.create_text(left + 84, 580, text=button, fill=text_fill, font=("Segoe UI", 10, "bold"))
                self.canvas.create_text(left + 84, 604, text=label, fill=text_fill, font=("Segoe UI", 12, "bold"))
        self._draw_status_ribbon()
        self._draw_training_curve_tracker()

    def _draw_low_puzzle_scene(self) -> None:
        low = self.flow.low_puzzle_state
        actor_id = self.flow.current_actor().actor_id
        scene = self._load_bitmap(self.assets.path_for("scene.low.puzzle"), 1280, 760)
        panel = self._load_bitmap(self.assets.path_for("panel.low"), 520, 300)
        support = self._load_bitmap(self.assets.path_for("support.low.puzzle"), 420, 280)
        actor_card = self._load_bitmap(self.assets.path_for(f"actor.{actor_id}"), 300, 320)
        self.canvas.create_image(640, 380, image=scene)
        self.canvas.create_rectangle(0, 0, 1280, 760, fill="#04060b", outline="", stipple="gray75")
        self.canvas.create_image(274, 410, image=panel)
        self.canvas.create_image(1020, 390, image=support)
        self.canvas.create_image(964, 456, image=actor_card)
        self.canvas.create_text(108, 92, text="LOW EPILOGUE", anchor="w", fill="#9db9df", font=("Segoe UI", 18, "bold"))
        self.canvas.create_text(108, 128, text="Cool the aftermath below the boss. Route the current in the order that spends the remaining force.", anchor="w", fill="#d8e0ef", font=("Segoe UI", 11, "bold"))
        if low is not None:
            sequence = low.step_sequence or ("refract", "resist", "collapse")
            target = sequence[min(low.progress, len(sequence) - 1)] if low.progress < low.target_progress else sequence[-1]
            self.canvas.create_text(116, 324, text=self.flow.status_text, anchor="w", width=340, fill="#d8e0ef", font=("Segoe UI", 13, "bold"))
            self.canvas.create_text(116, 514, text=f"Target {low.progress + 1}/{low.target_progress}: {target.upper()}", anchor="w", fill="#8f99ad", font=("Segoe UI", 11, "bold"))
            self.canvas.create_rectangle(116, 534, 392, 546, fill="#1a2232", outline="")
            progress = 0.0 if low.target_progress <= 0 else min(1.0, low.progress / low.target_progress)
            self.canvas.create_rectangle(116, 534, 116 + progress * 276, 546, fill="#9db9df", outline="")
            for index, step in enumerate(sequence):
                left = 516 + index * 188
                active = low.progress == index
                completed = low.progress > index
                fill = "#9db9df" if active else ("#5f8fe0" if completed else "#141b28")
                text_fill = "#081018" if active else "#d8e0ef"
                self.canvas.create_rectangle(left, 278, left + 160, 336, fill=fill, outline="#243141")
                self.canvas.create_text(left + 80, 307, text=step.upper(), fill=text_fill, font=("Segoe UI", 11, "bold"))
            controls = (("X / RB", "REFRACT"), ("LB", "RESIST"), ("Y / RT", "COLLAPSE"))
            for index, (button, label) in enumerate(controls):
                left = 520 + index * 196
                self.canvas.create_rectangle(left, 560, left + 168, 622, fill="#141b28", outline="#243141")
                self.canvas.create_text(left + 84, 582, text=button, fill="#d8e0ef", font=("Segoe UI", 10, "bold"))
                self.canvas.create_text(left + 84, 606, text=label, fill="#9db9df", font=("Segoe UI", 12, "bold"))
        self._draw_status_ribbon()
        self._draw_training_curve_tracker()

    def _draw_exploration_scene(self) -> None:
        state = self.runtime.exploration
        room = self.runtime.current_room()
        self._draw_landscape(state.camera_x, 0.0, 0, room.room_id)
        self._draw_atmosphere_fx(state.camera_x, room.room_id)
        self._draw_environment_enemies(state.camera_x)
        self._draw_platforms(state.camera_x)
        self._draw_hazard_fields(state.camera_x)
        self._draw_gourd_segments(state.camera_x)
        self._draw_encounter_sigils(state.camera_x)
        self._draw_room_gates(state.camera_x)
        self._draw_player(state.player_x - state.camera_x, state.player_y, moving=abs(state.velocity_x) > 8.0, crouching=state.crouching, crawling=state.crawling)
        self._draw_hazard_impact_fx(state.camera_x)
        self._draw_minimal_presence()
        self._draw_status_ribbon()
        self._draw_room_signature(room.room_id, state.room_transition)
        self._draw_room_transition(state.room_transition, state.transition_direction)
        self._draw_training_curve_tracker()
        if state.damage_flash > 0.0:
            strength = int(80 * state.damage_flash)
            self.canvas.create_rectangle(0, 0, 1280, 760, fill=f"#2a0a0a", outline="", stipple="gray50")
            self.canvas.create_rectangle(12, 12, 1268, 748, outline=f"#{140 + strength:02x}4a4a", width=4)

    def _draw_battle_scene(self) -> None:
        state = self.runtime.exploration
        battle = self.runtime.battle
        shake = battle.camera_shake
        shake_offset = 6 if int(shake) % 2 == 0 else -6
        offset = shake_offset + battle.camera_pan
        self._draw_landscape(max(0.0, state.camera_x - 60.0), battle.camera_zoom, offset, self.runtime.current_room().room_id)
        self.canvas.create_rectangle(0, 0, 1280, 72, fill="#05070c", outline="")
        self.canvas.create_rectangle(0, 688, 1280, 760, fill="#05070c", outline="")

        lane_y = {"foreground": 560, "midground": 474, "background": 392}
        enemy_lane = battle.prompt_lane
        player_lane = battle.lane_bias
        player_scale = 186 if player_lane != "background" else 144
        enemy_scale = {"foreground": 236, "midground": 182, "background": 138}[enemy_lane]
        player_x = 180 + (battle.player_battle_x * 860) + offset
        enemy_x = 180 + (battle.enemy_battle_x * 860) - offset
        if battle.phase == BattlePhase.EYECONTACT:
            gaze_t = battle.eyecontact_progress
            player_x = 202 + gaze_t * 194
            enemy_x = 1078 - gaze_t * 210
            self._draw_eyecontact_anticipation(player_x, lane_y[player_lane], enemy_x, lane_y[enemy_lane])
        elif battle.phase == BattlePhase.INTRO:
            intro_t = min(1.0, battle.timer / 0.56)
            intro_player = 148 + intro_t * 220
            intro_enemy = 1088 - intro_t * 236
            player_x = intro_player * (1.0 - intro_t) + player_x * intro_t
            enemy_x = intro_enemy * (1.0 - intro_t) + enemy_x * intro_t
        elif battle.phase == BattlePhase.RESOLVE:
            push = 28 if battle.last_resolution_strength >= 1.0 else -16
            player_x += push
            enemy_x -= push
        self._draw_battle_floor(player_x, enemy_x)
        self._draw_battle_focus_fx(player_x, lane_y[player_lane], enemy_x, lane_y[enemy_lane])
        self._draw_combat_telegraph(player_x, lane_y[player_lane], enemy_x, lane_y[enemy_lane])
        player_drawn = self._draw_banked_sprite(
            "ishtasha",
            self._battle_player_animation(battle),
            player_x,
            lane_y[player_lane],
            player_scale,
            player_scale,
            cadence=1.3 if battle.phase != BattlePhase.RESOLVE else 1.7,
            hold_last=battle.phase == BattlePhase.EYECONTACT and battle.eyecontact_hold > 0.0,
        )
        enemy_drawn = self._draw_banked_sprite(
            self._enemy_sprite_id(self.flow.current_actor().actor_id),
            self._battle_enemy_animation(self.flow.current_actor().actor_id, battle),
            enemy_x,
            lane_y[enemy_lane],
            enemy_scale,
            enemy_scale,
            cadence=1.1 if battle.phase != BattlePhase.RESOLVE else 1.5,
        )
        if not player_drawn:
            player_preview = self._battle_preview_frame("ishtasha-botanical-spider-preview", player_scale, player_scale, battle)
            player_sprite = player_preview if player_preview is not None else (self.player_sprite if player_lane != "background" else self.player_sprite_far)
            self.canvas.create_image(player_x, lane_y[player_lane], anchor="s", image=player_sprite)
        if not enemy_drawn:
            enemy_preview_name = {
                "scarab_child_acolyte": "scarab-child-basic-preview",
                "lattice_ward": "lattice-ward-preview",
                "lahgroid_hierophant": "lahgroid-boss-preview",
            }.get(self.flow.current_actor().actor_id)
            enemy_sprite = self._battle_preview_frame(enemy_preview_name, enemy_scale, enemy_scale, battle) if enemy_preview_name else None
            if enemy_sprite is None:
                enemy_sprite = self._actor_sprite(self.flow.current_actor().actor_id, enemy_scale)
            self.canvas.create_image(enemy_x, lane_y[enemy_lane], anchor="s", image=enemy_sprite)
        self._draw_battle_status(battle)
        self._draw_status_ribbon()
        self._draw_training_curve_tracker()

        if battle.tutorial_active:
            self._draw_battle_tutorial_overlay()

        if battle.phase == BattlePhase.WINDOW:
            self._draw_time_window_prompt()

        if battle.phase == BattlePhase.RESOLVE:
            self.canvas.create_rectangle(0, 0, 1280, 760, fill="", outline="#d8e0ef", width=4)
            self.canvas.create_line(320, 620, 960, 620, fill="#d65758" if battle.last_resolution_strength < 1.0 else "#66c06a", width=5)

    def _draw_eyecontact_anticipation(self, player_x: float, player_y: float, enemy_x: float, enemy_y: float) -> None:
        battle = self.runtime.battle
        line_strength = battle.line_of_sight_strength
        hold_strength = min(1.0, battle.eyecontact_hold / 0.16) if battle.eyecontact_hold > 0.0 else 0.0
        flash = max(0.0, battle.anticipation_flash)
        line_color = "#f0dba4" if hold_strength > 0.0 else "#d8e0ef"
        width = 2 + int(line_strength * 4)
        corridor = 160 + line_strength * 88
        self.canvas.create_rectangle(0, 0, 640 - corridor, 760, fill="#04060b", outline="", stipple="gray50")
        self.canvas.create_rectangle(640 + corridor, 0, 1280, 760, fill="#04060b", outline="", stipple="gray50")
        self.canvas.create_line(player_x + 38, player_y - 74, enemy_x - 38, enemy_y - 82, fill=line_color, width=width)
        self.canvas.create_arc(player_x - 66, player_y - 132, player_x + 54, player_y - 22, start=312, extent=122, style="arc", outline="#8cb6d2", width=2)
        self.canvas.create_arc(enemy_x - 54, enemy_y - 142, enemy_x + 68, enemy_y - 26, start=102, extent=128, style="arc", outline="#d7a07b", width=2)
        ring_radius = 10 + int(line_strength * 20)
        self.canvas.create_oval(640 - ring_radius, 280 - ring_radius, 640 + ring_radius, 280 + ring_radius, outline="#f0dba4", width=3)
        self.canvas.create_oval(640 - ring_radius * 1.8, 280 - ring_radius * 1.2, 640 + ring_radius * 1.8, 280 + ring_radius * 1.2, outline="#62748c", width=1, stipple="gray50")
        self.canvas.create_line(422, 186, 858, 186, fill="#243141", width=2)
        self.canvas.create_text(410, 186, text="GAZE PRESSURE", anchor="e", fill="#8f99ad", font=("Segoe UI", 9, "bold"))
        gather_left = 640 - min(188.0, line_strength * 212.0)
        gather_right = 640 + min(188.0, line_strength * 212.0)
        self.canvas.create_oval(gather_left - 5, 181, gather_left + 5, 191, fill="#8cb6d2", outline="")
        self.canvas.create_oval(gather_right - 5, 181, gather_right + 5, 191, fill="#d7a07b", outline="")
        self.canvas.create_line(602, 176, 602, 196, fill="#f0dba4", width=2)
        self.canvas.create_line(678, 176, 678, 196, fill="#f0dba4", width=2)
        for index in range(3):
            inset = 16 + index * 18
            self.canvas.create_line(640 - inset, 280 - ring_radius - 12, 640 + inset, 280 - ring_radius - 12, fill="#2c394a", width=1)
        if hold_strength > 0.0:
            pause_width = 120 + hold_strength * 180
            self.canvas.create_line(640 - pause_width * 0.5, 320, 640 + pause_width * 0.5, 320, fill="#d65758", width=3)
            self.canvas.create_text(640, 344, text="MEET", fill="#f0dba4", font=("Segoe UI", 12, "bold"))
        if flash > 0.0:
            alpha_color = "#d8e0ef" if flash > 0.5 else "#f0dba4"
            self.canvas.create_arc(560, 200, 720, 360, start=18, extent=144, style="arc", outline=alpha_color, width=4)
        self.canvas.create_text(640, 228, text="EYE LOCK", fill="#d8e0ef", font=("Segoe UI", 11, "bold"))
        self.canvas.create_text(640, 370, text="Hold the stare. Read the lane before the impact window opens.", fill="#8f99ad", font=("Segoe UI", 10, "bold"))

    def _draw_landscape(self, camera_x: float, zoom: float, offset_x: float = 0.0, room_id: str = "veinmarket") -> None:
        room = ROOMS[room_id]
        sky, mountain, earth = room.palette
        self.canvas.create_rectangle(0, 0, 1280, 760, fill=sky, outline="")
        self.canvas.create_rectangle(0, 420, 1280, 760, fill="#0b1118", outline="")
        for index in range(7):
            top = 40 + index * 34
            tint = 8 + index * 2
            self.canvas.create_rectangle(0, top, 1280, top + 18, fill=f"#{tint:02x}{18 + tint:02x}{28 + tint:02x}", outline="")
        heights = room.landmark_heights
        for index in range(9):
            base_x = (index * 320) - (camera_x * 0.18 % 320) - 120 + offset_x
            peak = 430 - heights[index % len(heights)]
            self.canvas.create_polygon(
                base_x, 430,
                base_x + 140, peak,
                base_x + 260, 430,
                fill=mountain,
                outline="",
            )
            self.canvas.create_polygon(
                base_x + 96, 430,
                base_x + 148, peak + 36,
                base_x + 198, 430,
                fill="#1f2d3d",
                outline="",
            )
        for index in range(14):
            base_x = (index * 240) - (camera_x * 0.42 % 240) - 40 + offset_x
            self.canvas.create_rectangle(base_x + 48, 282, base_x + 72, 584, fill="#151e2a", outline="")
            self.canvas.create_arc(base_x, 248, base_x + 120, 402, start=0, extent=180, style="arc", outline="#1d2a38", width=4)
            glow = 0.5 + 0.5 * math.sin(time.perf_counter() * 0.8 + index)
            glow_color = "#d7b780" if room_id in {"boss_gate", "sunken_sanctum"} else "#92a9c9"
            self.canvas.create_oval(base_x + 54, 318, base_x + 66, 330, fill=glow_color, outline="")
            if glow > 0.45:
                self.canvas.create_oval(base_x + 44, 308, base_x + 76, 340, outline=glow_color, width=2)
        self.canvas.create_rectangle(0, 592, 1280, 760, fill="#0d0e13", outline="")
        for index in range(64):
            start = (index * 120) - (camera_x % 120) + offset_x
            self.canvas.create_line(start, 592, start + 72, 560, fill=earth, width=3)
            self.canvas.create_line(start + 18, 592, start + 82, 568, fill="#27191d", width=2)
        for index in range(18):
            x = (index * 96) - (camera_x * 0.76 % 96) + offset_x
            self.canvas.create_line(x, 612, x + 44, 594, fill="#171a20", width=2)
        if zoom > 1.0:
            vignette = int((zoom - 1.0) * 120)
            self.canvas.create_rectangle(0, 0, 1280, 760, fill="", outline=f"#{20+vignette:02x}{16+vignette:02x}{20+vignette:02x}", width=10)

    def _draw_atmosphere_fx(self, camera_x: float, room_id: str) -> None:
        tick = time.perf_counter()
        fog_color = {
            "veinmarket": "#99a6b6",
            "ossuary_rise": "#8ca0af",
            "boss_gate": "#b89b86",
            "sunken_sanctum": "#88a5bc",
        }[room_id]
        for index in range(4):
            x = ((index * 420) - (camera_x * (0.16 + index * 0.03)) + tick * (8 + index * 2)) % 1560 - 140
            y = 168 + index * 82 + math.sin(tick * 0.45 + index) * 12
            width = 280 + index * 44
            self.canvas.create_oval(x, y, x + width, y + 60, fill=fog_color, outline="", stipple="gray50")
        swarm_centers = {
            "veinmarket": (428, 516),
            "ossuary_rise": (936, 468),
            "boss_gate": (1188, 438),
            "sunken_sanctum": (742, 500),
        }
        swarm_x, swarm_y = swarm_centers[room_id]
        for index in range(12):
            jitter = index * 0.7
            x = swarm_x - camera_x * 0.82 + math.sin(tick * 2.1 + jitter) * (18 + index)
            y = swarm_y + math.cos(tick * 1.8 + jitter) * (10 + index * 0.4)
            size = 2 + (index % 2)
            self.canvas.create_oval(x, y, x + size, y + size, fill="#d7d28a", outline="")
        for index in range(5):
            light_x = (220 + index * 228) - (camera_x * 0.4 % 228)
            light_y = 186 + (index % 2) * 42
            self.canvas.create_line(light_x, 0, light_x, light_y - 18, fill="#2f3642", width=2)
            self.canvas.create_oval(light_x - 6, light_y - 6, light_x + 6, light_y + 6, fill="#f0d6a0", outline="")
            self.canvas.create_oval(light_x - 34, light_y - 8, light_x + 34, light_y + 36, outline="#f0d6a0", width=2, stipple="gray50")

    def _draw_hazard_fields(self, camera_x: float) -> None:
        tick = time.perf_counter()
        for patch in self.runtime.exploration.sludge_patches:
            left = patch.start_x - camera_x
            right = patch.end_x - camera_x
            if right < -80 or left > 1360:
                continue
            wave = math.sin(tick * 2.2 + patch.start_x * 0.01)
            width = right - left
            self.canvas.create_rectangle(left, patch.top_y, right, patch.top_y + patch.depth, fill="#243823", outline="")
            self.canvas.create_rectangle(left, patch.top_y + patch.depth * 0.3, right, patch.top_y + patch.depth, fill="#1b2a1b", outline="")
            self.canvas.create_line(left, patch.top_y + 3 + wave * 2, right, patch.top_y + 3 - wave * 2, fill="#76a05d", width=2)
            self.canvas.create_line(left, patch.top_y + 7 - wave * 1.6, right, patch.top_y + 6 + wave * 1.2, fill="#a4c676", width=1)
            for index in range(0, int(max(1.0, right - left)), 22):
                x = left + index
                height = 6 + math.sin(tick * 1.7 + index * 0.16) * 4
                self.canvas.create_line(x, patch.top_y + patch.depth - 2, x + 6, patch.top_y + patch.depth - height, fill="#5e8348", width=2)
            for orb in range(4):
                bubble_x = left + ((tick * 36 + orb * (width * 0.23 + 11)) % max(28.0, width))
                bubble_y = patch.top_y + patch.depth - 5 - ((tick * (9 + orb)) % max(8.0, patch.depth - 4))
                radius = 2 + (orb % 2)
                self.canvas.create_oval(bubble_x - radius, bubble_y - radius, bubble_x + radius, bubble_y + radius, outline="#b8d492", width=1)
                if orb % 2 == 0:
                    ripple = 5 + math.sin(tick * 3.1 + orb) * 2
                    self.canvas.create_arc(bubble_x - ripple, patch.top_y + 2, bubble_x + ripple, patch.top_y + 10, start=0, extent=180, style="arc", outline="#8db167", width=1)
        for spikes in self.runtime.exploration.spikes:
            left = spikes.start_x - camera_x
            right = spikes.end_x - camera_x
            if right < -80 or left > 1360:
                continue
            self.canvas.create_line(left, spikes.tip_y + 12, right, spikes.tip_y + 12, fill="#372227", width=4)
            x = left
            while x < right:
                self.canvas.create_polygon(x, spikes.tip_y + 12, x + 8, spikes.tip_y, x + 16, spikes.tip_y + 12, fill="#d4c7b0", outline="#6e4b56")
                glint = 0.5 + 0.5 * math.sin(tick * 5.0 + x * 0.08)
                if glint > 0.62:
                    self.canvas.create_line(x + 5, spikes.tip_y - 5, x + 10, spikes.tip_y + 2, fill="#f8e7b8", width=1)
                    self.canvas.create_line(x + 11, spikes.tip_y - 3, x + 6, spikes.tip_y + 4, fill="#f8e7b8", width=1)
                x += 16
            for mote in range(3):
                mote_x = left + ((tick * 52 + mote * 31) % max(20.0, right - left))
                mote_y = spikes.tip_y - 8 - (mote * 6) - math.sin(tick * 4.6 + mote) * 3
                self.canvas.create_oval(mote_x, mote_y, mote_x + 2, mote_y + 2, fill="#d65758", outline="")

    def _draw_hazard_impact_fx(self, camera_x: float) -> None:
        state = self.runtime.exploration
        if state.hazard_impact_timer <= 0.0:
            return
        progress = min(1.0, state.hazard_impact_timer)
        center_x = state.hazard_impact_x - camera_x
        center_y = state.hazard_impact_y
        radius = 18 + (1.0 - progress) * 34
        self.canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, outline="#f0dba4", width=2)
        self.canvas.create_oval(center_x - radius * 0.65, center_y - radius * 0.5, center_x + radius * 0.65, center_y + radius * 0.5, outline="#d65758", width=2)
        for shard in range(7):
            angle = (-0.9 + shard * 0.3) + math.sin(shard + progress) * 0.08
            reach = 12 + shard * 5 + (1.0 - progress) * 24
            end_x = center_x + math.cos(angle) * reach
            end_y = center_y - math.sin(angle) * (reach * 0.85)
            self.canvas.create_line(center_x, center_y, end_x, end_y, fill="#f4d7ab", width=2)
        self.canvas.create_arc(center_x - 48, center_y - 28, center_x + 48, center_y + 20, start=8, extent=164, style="arc", outline="#c78663", width=2)

    def _draw_environment_enemies(self, camera_x: float) -> None:
        tick = time.perf_counter()
        for enemy in self.runtime.current_room().ambient_enemies:
            base_x = enemy.x - camera_x
            if base_x < -120 or base_x > 1400:
                continue
            bob = math.sin(tick * 1.4 + enemy.sway) * 6
            screen_y = enemy.ground_y + bob
            shadow_w = max(14, enemy.scale * 0.2)
            self.canvas.create_oval(base_x - shadow_w, screen_y - 10, base_x + shadow_w, screen_y + 2, fill="#0c1118", outline="")
            animation = {
                "scarab_child_acolyte": "feint",
                "lattice_ward": "flare",
                "lahgroid_hierophant": "feint",
            }.get(enemy.actor_id, "idle")
            drawn = self._draw_banked_sprite(self._enemy_sprite_id(enemy.actor_id), animation, base_x, screen_y, enemy.scale, enemy.scale, cadence=0.75 + enemy.sway * 0.1)
            if not drawn:
                sprite = self._actor_sprite(enemy.actor_id, enemy.scale)
                self.canvas.create_image(base_x, screen_y, anchor="s", image=sprite)
            eye_color = "#d65758" if enemy.actor_id != "lattice_ward" else "#d8e0ef"
            halo = 12 if enemy.lane == "foreground" else 8
            self.canvas.create_arc(base_x - halo, screen_y - enemy.scale * 0.75, base_x + halo, screen_y - enemy.scale * 0.48, start=0, extent=180, style="arc", outline=eye_color, width=2)

    def _draw_gourd_segments(self, camera_x: float) -> None:
        state = self.runtime.exploration
        tick = time.perf_counter()
        for segment in state.gourd_segments:
            if segment.consumed:
                continue
            screen_x = segment.x - camera_x
            if screen_x < -90 or screen_x > 1370:
                continue
            bob = math.sin(tick * 1.8 + segment.x * 0.01) * 4
            y = segment.y + bob
            self.canvas.create_oval(screen_x - 18, y - 28, screen_x + 18, y + 10, fill="#84694c", outline="#d0b788", width=2)
            self.canvas.create_arc(screen_x - 28, y - 36, screen_x + 28, y + 20, start=24, extent=132, style="arc", outline="#f0dba4", width=2)
            self.canvas.create_line(screen_x, y - 36, screen_x, y - 14, fill="#7ba35d", width=3)
            self.canvas.create_oval(screen_x - 6, y - 42, screen_x + 6, y - 30, fill="#7ba35d", outline="")
            if abs(state.player_x - segment.x) <= 52.0:
                self.canvas.create_text(screen_x, y - 52, text="X: ABSORB SEGMENT", fill="#f0dba4", font=("Segoe UI", 9, "bold"))

    def _draw_status_ribbon(self) -> None:
        player = self.flow.player
        health = max(0.0, min(100.0, player.health))
        gourd_fill = 0.0 if player.gourd.capacity <= 0.0 else min(1.0, player.gourd.stored_blood / player.gourd.capacity)
        self.canvas.create_rectangle(24, 680, 692, 742, fill="#090d15", outline="#1f2a39")
        self.canvas.create_text(40, 698, text=f"Health {health:.0f}", anchor="w", fill="#d8e0ef", font=("Segoe UI", 10, "bold"))
        self.canvas.create_rectangle(40, 710, 220, 720, fill="#1a2232", outline="")
        self.canvas.create_rectangle(40, 710, 40 + health * 1.8, 720, fill="#d65758" if health < 40.0 else "#66c06a", outline="")
        self.canvas.create_text(248, 698, text=f"Gourd {player.gourd.stored_blood:.0f}/{player.gourd.capacity:.0f}", anchor="w", fill="#d8e0ef", font=("Segoe UI", 10, "bold"))
        self.canvas.create_rectangle(248, 710, 448, 720, fill="#1a2232", outline="")
        self.canvas.create_rectangle(248, 710, 248 + gourd_fill * 200, 720, fill="#f0dba4", outline="")
        self.canvas.create_text(40, 732, text=self.flow.status_text[:92], anchor="w", fill="#8f99ad", font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(664, 698, text="X/RB interact or use gourd", anchor="e", fill="#8f99ad", font=("Segoe UI", 9, "bold"))

    def _draw_battle_tutorial_overlay(self) -> None:
        battle = self.runtime.battle
        page_count = len(battle.tutorial_pages)
        page_index = battle.tutorial_page
        message = battle.tutorial_pages[page_index] if page_count else ""
        self.canvas.create_rectangle(166, 130, 1114, 632, fill="#05070c", outline="#d8e0ef", width=2, stipple="gray25")
        self.canvas.create_text(206, 170, text=f"COMBAT TUTORIAL {page_index + 1}/{page_count}", anchor="w", fill="#f0dba4", font=("Segoe UI", 16, "bold"))
        self.canvas.create_text(206, 222, text=message, anchor="w", width=860, fill="#d8e0ef", font=("Segoe UI", 14, "bold"))
        self.canvas.create_rectangle(206, 288, 476, 432, fill="#0b0f18", outline="#334153")
        self.canvas.create_text(228, 314, text="Core Read", anchor="w", fill="#8f99ad", font=("Segoe UI", 11, "bold"))
        self.canvas.create_text(228, 350, text="Enemy move, your lane, and your timing all stack into the result.", anchor="w", width=220, fill="#d8e0ef", font=("Segoe UI", 11, "bold"))
        self.canvas.create_rectangle(522, 288, 802, 432, fill="#0b0f18", outline="#334153")
        self.canvas.create_text(544, 314, text="Buttons", anchor="w", fill="#8f99ad", font=("Segoe UI", 11, "bold"))
        self.canvas.create_text(544, 350, text="LB block/parry\nRB light\nRT heavy\nLT dodge", anchor="w", fill="#d8e0ef", font=("Segoe UI", 11, "bold"))
        self.canvas.create_rectangle(850, 288, 1074, 432, fill="#0b0f18", outline="#334153")
        self.canvas.create_text(872, 314, text="Lane Read", anchor="w", fill="#8f99ad", font=("Segoe UI", 11, "bold"))
        self.canvas.create_text(872, 350, text="Up: background\nNeutral: midground\nDown: foreground", anchor="w", fill="#d8e0ef", font=("Segoe UI", 11, "bold"))
        self.canvas.create_text(640, 578, text="Press Enter or X to continue", fill="#f0dba4", font=("Segoe UI", 12, "bold"))

    def _draw_battle_focus_fx(self, player_x: float, player_y: float, enemy_x: float, enemy_y: float) -> None:
        battle = self.runtime.battle
        focus_y = (player_y + enemy_y) * 0.5 - 90
        depth_color = "#d8e0ef" if battle.phase == BattlePhase.WINDOW else "#a8b4c9"
        self.canvas.create_polygon(0, 0, 1280, 0, 1280, 120, 0, 92, fill="#04060b", outline="")
        self.canvas.create_polygon(0, 760, 1280, 760, 1280, 650, 0, 628, fill="#04060b", outline="")
        acuity_width = 164 + battle.proximity * 96 + battle.arena_span * 84
        self.canvas.create_rectangle(0, 0, 640 - acuity_width, 760, fill="#04060b", outline="", stipple="gray50")
        self.canvas.create_rectangle(640 + acuity_width, 0, 1280, 760, fill="#04060b", outline="", stipple="gray50")
        for index in range(5):
            inset = 48 + index * 30
            self.canvas.create_line(player_x - inset, focus_y + index * 10, enemy_x + inset, focus_y + index * 6, fill=depth_color, width=1)
            self.canvas.create_line(player_x - inset, 620 - index * 8, enemy_x + inset, 608 - index * 4, fill="#2d3442", width=1)
        for band in range(4):
            lift = band * 18
            self.canvas.create_line(640 - acuity_width, focus_y - 42 - lift, 640 + acuity_width, focus_y - 52 - lift, fill="#202937", width=1)
            self.canvas.create_line(640 - acuity_width, focus_y + 34 + lift, 640 + acuity_width, focus_y + 26 + lift, fill="#171e29", width=1)
        vignette = 14 + battle.time_dilation * 8
        self.canvas.create_rectangle(8, 8, 1272, 752, outline="#151b24", width=int(vignette))
        self.canvas.create_polygon(640 - acuity_width, focus_y - 86, 640 + acuity_width, focus_y - 70, 640 + acuity_width - 38, focus_y + 120, 640 - acuity_width + 38, focus_y + 134, outline="#334153", fill="", width=2)
        if battle.phase == BattlePhase.WINDOW:
            self.canvas.create_oval(540, 220, 740, 420, outline="#9db9df", width=2)
            self.canvas.create_oval(504, 184, 776, 456, outline="#4f617a", width=1, stipple="gray50")
            self.canvas.create_text(640, 192, text="COMBAT ACUITY", fill="#9db9df", font=("Segoe UI", 10, "bold"))

    def _draw_room_gates(self, camera_x: float) -> None:
        room = self.runtime.current_room()
        state = self.runtime.exploration
        if room.previous_room is not None:
            self.canvas.create_rectangle(-camera_x - 24, room.ground_y - 112, -camera_x + 22, room.ground_y, fill="#2b3342", outline="")
        if room.next_room is not None:
            gate_x = room.width - camera_x
            color = "#66c06a" if self.runtime.room_gate_open(room.room_id) else "#6a3a40"
            self.canvas.create_rectangle(gate_x - 18, room.ground_y - 138, gate_x + 22, room.ground_y, fill=color, outline="")
            self.canvas.create_line(gate_x + 2, room.ground_y - 138, gate_x + 2, room.ground_y, fill="#081018", width=2)
            if state.gate_feedback > 0.0 and state.gate_locked:
                pulse = 20 + (1.0 - state.gate_feedback) * 72
                pulse_color = "#f0dba4" if state.gate_feedback > 0.55 else "#d65758"
                self.canvas.create_arc(gate_x - pulse, room.ground_y - 186, gate_x + pulse, room.ground_y - 18, start=90, extent=180, style="arc", outline=pulse_color, width=4)

    def _draw_room_signature(self, room_id: str, transition: float) -> None:
        labels = {
            "veinmarket": "VEINMARKET",
            "ossuary_rise": "OSSUARY RISE",
            "boss_gate": "BOSS GATE",
            "sunken_sanctum": "SUNKEN SANCTUM",
        }
        alpha_bias = 0.35 + transition * 0.65
        fill = f"#{int(120 * alpha_bias):02x}{int(132 * alpha_bias):02x}{int(150 * alpha_bias):02x}"
        self.canvas.create_text(106, 42, text=labels[room_id], anchor="w", fill=fill, font=("Segoe UI", 12, "bold"))

    def _draw_room_transition(self, transition: float, direction: int) -> None:
        if transition <= 0.0:
            return
        width = int(240 * transition)
        if direction >= 0:
            self.canvas.create_rectangle(0, 0, width, 760, fill="#d8e0ef", outline="", stipple="gray50")
        else:
            self.canvas.create_rectangle(1280 - width, 0, 1280, 760, fill="#d8e0ef", outline="", stipple="gray50")

    def _draw_combat_telegraph(self, player_x: float, player_y: float, enemy_x: float, enemy_y: float) -> None:
        battle = self.runtime.battle
        if battle.phase not in {BattlePhase.INTRO, BattlePhase.WINDOW, BattlePhase.EYECONTACT}:
            return
        lane_offsets = {"foreground": 34, "midground": 0, "background": -34}
        telegraph_y = enemy_y - 112 + lane_offsets.get(battle.prompt_lane, 0)
        width = 54 + battle.telegraph_strength * 96
        self.canvas.create_line(enemy_x - width, telegraph_y, enemy_x + width, telegraph_y, fill="#f0dba4", width=4)
        self.canvas.create_line(player_x - 46, player_y - 132, player_x + 46, player_y - 132, fill="#d8e0ef", width=2)
        pressure_band_y = 178 + lane_offsets.get(battle.prompt_lane, 0) * 0.45
        self.canvas.create_line(404, pressure_band_y, 876, pressure_band_y, fill="#243141", width=2)
        self.canvas.create_text(392, pressure_band_y, text="PRESSURE", anchor="e", fill="#8f99ad", font=("Segoe UI", 9, "bold"))
        pressure_travel = 164 + battle.telegraph_strength * 180
        left_stop = 640 - 42
        right_stop = 640 + 42
        self.canvas.create_line(left_stop, pressure_band_y - 10, left_stop, pressure_band_y + 10, fill="#f0dba4", width=2)
        self.canvas.create_line(right_stop, pressure_band_y - 10, right_stop, pressure_band_y + 10, fill="#f0dba4", width=2)
        self.canvas.create_arc(640 - 70, pressure_band_y - 26, 640 + 70, pressure_band_y + 26, start=0, extent=180, style="arc", outline="#62748c", width=1)
        if battle.phase == BattlePhase.WINDOW:
            for pulse in range(3):
                phase = (battle.window_progress * battle.pressure_speed + pulse * 0.24) % 1.0
                left_x = 640 - min(pressure_travel, phase * pressure_travel)
                right_x = 640 + min(pressure_travel, phase * pressure_travel)
                if left_x < left_stop:
                    self.canvas.create_oval(left_x - 5, pressure_band_y - 5, left_x + 5, pressure_band_y + 5, fill="#d65758", outline="")
                if right_x > right_stop:
                    self.canvas.create_oval(right_x - 5, pressure_band_y - 5, right_x + 5, pressure_band_y + 5, fill="#d65758", outline="")
            lane_panel_x = 930
            lane_panel_y = 234
            self.canvas.create_rectangle(lane_panel_x, lane_panel_y, lane_panel_x + 158, lane_panel_y + 148, fill="#0b0f18", outline="#334153")
            self.canvas.create_text(lane_panel_x + 12, lane_panel_y + 16, text="LANE READ", anchor="w", fill="#8f99ad", font=("Segoe UI", 9, "bold"))
            lane_rows = (("BACKGROUND", "background"), ("MIDGROUND", "midground"), ("FOREGROUND", "foreground"))
            for index, (label, lane_key) in enumerate(lane_rows):
                top = lane_panel_y + 34 + index * 36
                active = battle.prompt_lane == lane_key
                fill = "#d65758" if active else "#1a2232"
                text_fill = "#081018" if active else "#d8e0ef"
                self.canvas.create_rectangle(lane_panel_x + 14, top, lane_panel_x + 144, top + 24, fill=fill, outline="#243141")
                self.canvas.create_text(lane_panel_x + 79, top + 12, text=label, fill=text_fill, font=("Segoe UI", 8, "bold"))
        if battle.phase == BattlePhase.EYECONTACT:
            self.canvas.create_line(player_x + 28, player_y - 94, enemy_x - 28, enemy_y - 110, fill="#cfd7e4", width=2)

    def _draw_battle_floor(self, player_x: float, enemy_x: float) -> None:
        self.canvas.create_polygon(126, 620, 1154, 620, 1094, 664, 182, 664, fill="#16131b", outline="")
        self.canvas.create_line(164, 610, 1116, 610, fill="#31242a", width=4)
        for marker in range(6):
            x = 220 + marker * 160
            self.canvas.create_line(x, 598, x, 624, fill="#43313a", width=2)
            self.canvas.create_line(x + 14, 622, x + 48, 634, fill="#20171d", width=1)
        self.canvas.create_oval(player_x - 24, 612, player_x + 24, 624, outline="#66c06a", width=2)
        self.canvas.create_oval(enemy_x - 24, 612, enemy_x + 24, 624, outline="#d65758", width=2)
        self.canvas.create_oval(player_x - 44, 604, player_x + 44, 636, outline="#6a7c95", width=1, stipple="gray50")
        self.canvas.create_oval(enemy_x - 44, 604, enemy_x + 44, 636, outline="#6a7c95", width=1, stipple="gray50")

    def _draw_battle_status(self, battle: object) -> None:
        left = 108
        self.canvas.create_rectangle(left, 84, left + 252, 150, fill="#0b0f18", outline="#1f2a39")
        self.canvas.create_text(left + 14, 100, text="PROXIMITY", anchor="w", fill="#8f99ad", font=("Segoe UI", 10, "bold"))
        self.canvas.create_rectangle(left + 14, 116, left + 222, 124, fill="#1a2232", outline="")
        self.canvas.create_rectangle(left + 14, 116, left + 14 + battle.proximity * 208, 124, fill="#66c06a" if battle.proximity > 0.48 else "#d65758", outline="")
        acuity = max(0.0, 1.0 - abs(battle.window_progress - 0.5) * 2.0) if battle.phase == BattlePhase.WINDOW else battle.line_of_sight_strength
        self.canvas.create_text(left + 14, 140, text=f"{battle.cadence_label}  Move: {battle.prompt_action.upper()}  Lane: {battle.prompt_lane.upper()}  Focus x{battle.time_dilation:.2f}  Acuity {acuity:.2f}", anchor="w", fill="#d8e0ef", font=("Segoe UI", 9, "bold"))

    def _draw_platforms(self, camera_x: float) -> None:
        for platform in self.runtime.exploration.platforms:
            left = platform.start_x - camera_x
            right = platform.end_x - camera_x
            if right < -80 or left > 1360:
                continue
            self.canvas.create_rectangle(left, platform.top_y, right, platform.top_y + 18, fill="#46343c", outline="")
            self.canvas.create_line(left, platform.top_y, right, platform.top_y, fill="#88656f", width=3)
            for beam in range(int(left), int(right), 28):
                self.canvas.create_line(beam, platform.top_y + 2, beam + 12, platform.top_y + 18, fill="#34242c", width=2)
            for rivet in range(int(left) + 10, int(right), 34):
                self.canvas.create_oval(rivet - 1, platform.top_y + 6, rivet + 1, platform.top_y + 8, fill="#d0b788", outline="")

    def _draw_encounter_sigils(self, camera_x: float) -> None:
        color_map = {
            "scarab_child_acolyte": "#d65758",
            "lattice_ward": "#d8e0ef",
            "lahgroid_hierophant": "#f0dba4",
        }
        for zone in self.runtime.exploration.encounters:
            if zone.consumed:
                continue
            center_x = ((zone.start_x + zone.end_x) * 0.5) - camera_x
            if center_x < -64 or center_x > 1344:
                continue
            color = color_map[zone.enemy_id]
            self.canvas.create_line(center_x, 512, center_x, 592, fill=color, width=2)
            self.canvas.create_oval(center_x - 18, 478, center_x + 18, 514, outline=color, width=2)

    def _draw_player(self, screen_x: float, ground_y: float, moving: bool, crouching: bool, crawling: bool) -> None:
        state = self.runtime.exploration
        animation = "idle"
        if not state.on_ground:
            animation = "jump" if state.velocity_y < 0.0 else "land"
        elif state.dodging or state.dash_timer > 0.0:
            animation = "dash"
        elif crawling:
            animation = "crawl"
        elif crouching:
            animation = "block"
        elif moving:
            animation = "run"
        sprite = self._sprite_bank_frame("ishtasha", animation, 182, 182, cadence=1.5 if moving else 0.35)
        if sprite is None:
            sprite = self._animated_preview_frame("ishtasha-botanical-spider-preview", 170, 170, cadence=1.2 if moving else 0.2)
        if sprite is None:
            sprite = self.player_sprite or self.player_sprite_far
        anchor_y = ground_y
        if sprite is not None:
            if crouching:
                anchor_y += 18
            if crawling:
                anchor_y += 26
            bob = -4 if moving and not crouching and not crawling and int(time.perf_counter() * 8) % 2 == 0 else 0
            self.canvas.create_image(screen_x, anchor_y + bob, anchor="s", image=sprite)
            if state.sludge_cling > 0.0:
                self._draw_sludge_cling(screen_x, anchor_y + bob, state.sludge_cling)
            return
        self.canvas.create_rectangle(screen_x - 22, ground_y - 88, screen_x + 22, ground_y, fill="#d65758", outline="")

    def _draw_sludge_cling(self, screen_x: float, ground_y: float, intensity: float) -> None:
        width = 10 + intensity * 18
        self.canvas.create_oval(screen_x - width, ground_y - 16, screen_x + width, ground_y - 2, fill="#5f874b", outline="")
        for offset in (-10, -2, 6, 14):
            self.canvas.create_line(screen_x + offset, ground_y - 12, screen_x + offset - 2, ground_y + 2, fill="#7ca65a", width=2)
        pulse = math.sin(time.perf_counter() * 5.4) * 3
        self.canvas.create_arc(screen_x - width - 4, ground_y - 14 + pulse, screen_x + width + 4, ground_y + 4 + pulse, start=0, extent=180, style="arc", outline="#a1c76b", width=1)

    def _draw_minimal_presence(self) -> None:
        self.canvas.create_oval(1208, 26, 1222, 40, fill="#66c06a" if self.controller.poll().connected else "#394359", outline="")
        for index in range(3):
            left = 1120 + index * 26
            fill = "#c6524c" if index == 1 else "#1a1f2c"
            self.canvas.create_rectangle(left, 28, left + 18, 36, fill=fill, outline="")

    def _draw_time_window_prompt(self) -> None:
        battle = self.runtime.battle
        self.canvas.create_rectangle(392, 220, 888, 514, fill="#0b0f18", outline="#d8e0ef", width=2, stipple="gray25")
        self.canvas.create_polygon(426, 248, 854, 248, 818, 296, 462, 296, outline="#334153", fill="", width=2)
        self.canvas.create_polygon(452, 306, 828, 306, 788, 456, 492, 456, outline="#243141", fill="", width=2)
        bar_left = 444
        bar_right = 836
        bar_width = bar_right - bar_left
        progress_x = bar_left + (battle.window_progress * bar_width)
        center_gain = 0.0
        if battle.time_dilation > 1.0:
            center_gain = min(1.0, (battle.time_dilation - 1.0) / max(0.01, 0.24 + battle.curve_index * 0.05))
        center_half = battle.timing_window_half + center_gain * 6
        timing_top = 270
        timing_bottom = 286
        pressure_top = 244
        pressure_bottom = 256
        self.canvas.create_text(430, 236, text="TIMING PRESSURE", anchor="w", fill="#8f99ad", font=("Segoe UI", 9, "bold"))
        self.canvas.create_rectangle(bar_left, pressure_top, bar_right, pressure_bottom, fill="#111824", outline="")
        self.canvas.create_rectangle(bar_left, timing_top, bar_right, timing_bottom, fill="#1a2232", outline="")
        self.canvas.create_rectangle(bar_left, timing_top, progress_x, timing_bottom, fill="#d8e0ef", outline="")
        self.canvas.create_rectangle(640 - center_half, timing_top - 4, 640 + center_half, timing_bottom + 4, outline="#9db9df", width=2)
        self.canvas.create_line(progress_x, timing_top - 8, progress_x, timing_bottom + 8, fill="#66c06a", width=3)
        self.canvas.create_line(640, 250, 640, 470, fill="#2c394a", width=1)
        approach_extent = min(bar_width * 0.5 - center_half - 12, 64 + battle.telegraph_strength * 132)
        self.canvas.create_line(640 - center_half - approach_extent, 250, 640 - center_half - 8, 250, fill="#d65758", width=3)
        self.canvas.create_line(640 + center_half + 8, 250, 640 + center_half + approach_extent, 250, fill="#d65758", width=3)
        for bead in range(3):
            bead_phase = (battle.window_progress * battle.pressure_speed + bead * 0.2) % 1.0
            inward = approach_extent * (1.0 - bead_phase)
            left_x = 640 - center_half - 10 - inward
            right_x = 640 + center_half + 10 + inward
            self.canvas.create_oval(left_x - 4, 246, left_x + 4, 254, fill="#d65758", outline="")
            self.canvas.create_oval(right_x - 4, 246, right_x + 4, 254, fill="#d65758", outline="")
        prompt_map = {
            "attack": ("ATTACK", "#d65758"),
            "parry": ("PARRY", "#f0dba4"),
            "dodge": ("DODGE", "#66c06a"),
            "block": ("BLOCK", "#5f8fe0"),
        }
        lane_map = {"foreground": 0, "midground": 1, "background": 2}
        label, color = prompt_map.get(battle.prompt_action, ("ATTACK", "#66c06a"))
        self.canvas.create_text(430, 320, text="LANE PRESSURE", anchor="w", fill="#8f99ad", font=("Segoe UI", 9, "bold"))
        for index in range(3):
            left = 504 + index * 112
            perspective = index * 8
            fill = color if lane_map.get(battle.prompt_lane, 1) == index else "#1c2332"
            self.canvas.create_polygon(left + perspective, 330, left + 84 - perspective, 330, left + 96, 430, left - 12, 430, fill=fill, outline="#0a1018")
            if lane_map.get(battle.prompt_lane, 1) != index:
                self.canvas.create_line(left + 18, 338, left + 66, 422, fill="#111824", width=2)
        self.canvas.create_oval(608, 276, 672, 340, fill=color, outline="")
        self.canvas.create_text(640, 308, text=label, fill="#081018", font=("Segoe UI", 14, "bold"))
        self.canvas.create_arc(588, 258, 692, 362, start=28, extent=124, style="arc", outline="#9db9df", width=3)
        self.canvas.create_text(640, 454, text=f"{battle.cadence_label}: timing holds the center, pressure halts outside it, lane sits apart.", fill="#8f99ad", font=("Segoe UI", 10, "bold"))
        controls = [
            ("LB", "Block / Parry", "#5f8fe0"),
            ("RB", "Light", "#66c06a"),
            ("RT", "Heavy", "#f0dba4"),
            ("LT", "Dodge", "#d65758"),
        ]
        for index, (button, action, swatch) in enumerate(controls):
            top = 350 + index * 28
            self.canvas.create_rectangle(442, top, 490, top + 20, fill=swatch, outline="")
            self.canvas.create_text(466, top + 10, text=button, fill="#081018", font=("Segoe UI", 10, "bold"))
            self.canvas.create_text(508, top + 10, text=action, anchor="w", fill="#d8e0ef", font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(640, 470, text=f"Precision {battle.exchange_precision:.2f}   Proximity {battle.proximity:.2f}   Dilation x{battle.time_dilation:.2f}", fill="#8f99ad", font=("Segoe UI", 10, "bold"))

    def run(self) -> None:
        self.root.mainloop()


def smoke_test() -> None:
    player = create_starting_player("Smoke")
    flow = GameplayPrototypeController(player)
    runtime = MetroidvaniaRuntime(flow)
    runtime.tutorial_completed = True
    runtime.start_game()
    runtime.update(0.016, RuntimeInput(interact_pressed=True))
    runtime.update(0.5, RuntimeInput())
    runtime.update(0.016, RuntimeInput(move_y=1.0, block_pressed=True))
    runtime.update(0.016, RuntimeInput(move_y=-1.0, jump_pressed=True))
    runtime.update(0.5, RuntimeInput())
    runtime.update(0.016, RuntimeInput(move_y=1.0, dash_pressed=True))
    runtime.update(0.016, RuntimeInput(move_x=1.0))
    runtime.exploration.player_x = 1360.0
    runtime.update(0.016, RuntimeInput())
    runtime.update(0.34, RuntimeInput(move_y=1.0))
    runtime.update(0.16, RuntimeInput(move_y=1.0))
    runtime.update(0.84, RuntimeInput(move_y=1.0))
    runtime.update(0.2, RuntimeInput(move_y=1.0, light_attack_pressed=True))
    print("XenoBloods shell smoke OK")
    linked = load_link_manifest() is not None
    print(f"mode={runtime.mode.value} flow={flow.mode.value} linked_2d_assets={linked}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    if args.smoke:
        smoke_test()
        return

    app = XenobloodsShell()
    app.run()


if __name__ == "__main__":
    main()