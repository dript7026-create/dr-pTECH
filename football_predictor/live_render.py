from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight,
    CardMaker,
    DirectionalLight,
    LineSegs,
    NodePath,
    TransparencyAttrib,
    WindowProperties,
    loadPrcFileData,
)

from .live_scene import SURFACE_CONFIG, scene_from_report
from .sports import get_sport_config, normalize_sport


class LiveMatchRenderer(ShowBase):
    def __init__(
        self,
        report: Optional[Dict[str, object]] = None,
        fixture_index: int = 0,
        offscreen: bool = False,
        auto_close_after: float | None = None,
        software_render: bool = False,
    ):
        use_software = software_render or os.environ.get("DIRKODDS_PANDA_SOFTWARE_RENDER") == "1"
        if use_software:
            loadPrcFileData("", "load-display p3tinydisplay")
        else:
            loadPrcFileData("", "load-display pandagl")
            loadPrcFileData("", "aux-display p3tinydisplay")
        loadPrcFileData("", "audio-library-name null")
        loadPrcFileData("", f"window-type {'none' if offscreen else 'onscreen'}")
        loadPrcFileData("", "sync-video false")
        loadPrcFileData("", "show-frame-rate-meter false")
        loadPrcFileData("", "window-title DirkOdds Live Match Renderer")
        super().__init__()
        self.disableMouse()

        if report is None:
            raise ValueError("A prediction report is required for live rendering.")

        self.scene_bundle = scene_from_report(report, fixture_index=fixture_index)
        self.frames: List[Dict[str, object]] = self.scene_bundle["frames"]
        self.match_seconds = float(self.scene_bundle["match_seconds"])
        self.sport = normalize_sport(self.scene_bundle["sport"])
        self.surface = SURFACE_CONFIG[self.sport]
        self.current_time = 0.0
        self.current_index = 0
        self.playing = True
        self.playback_speed = 1.0
        self.camera_mode = 0
        self.auto_close_after = auto_close_after
        self._wall_clock = 0.0
        self._crowd_nodes: List[NodePath] = []
        self._crowd_offsets: List[float] = []
        self._crowd_base_z: List[float] = []
        self.focus_marker: NodePath | None = None
        self.ball_shadow: NodePath | None = None
        self._camera_target_pos: Tuple[float, float, float] | None = None

        if self.win is not None:
            props = WindowProperties()
            props.setSize(1600 if not offscreen else 800, 900 if not offscreen else 600)
            self.win.requestProperties(props)

        self._build_world()
        self._apply_frame(self.frames[0])
        self._bind_controls()
        self.taskMgr.add(self._update_task, "dirkodds-live-render")

    def _build_world(self) -> None:
        self.setBackgroundColor(0.03, 0.05, 0.08, 1.0)
        self.render.setShaderAuto()
        self._build_lights()
        self._build_arena()
        self._build_crowd()
        self.home_nodes = [self._build_player_node((0.10, 0.55, 0.92, 1.0)) for _ in self.frames[0]["home_players"]]
        self.away_nodes = [self._build_player_node((0.92, 0.32, 0.20, 1.0)) for _ in self.frames[0]["away_players"]]
        self.ball_node = self._make_cube((0.94, 0.94, 0.96, 1.0), scale=(0.38, 0.38, 0.38))
        self.ball_node.reparentTo(self.render)
        self.ball_shadow = self._make_focus_marker()
        self.ball_shadow.setColor(0.05, 0.06, 0.08, 0.22)
        self.ball_shadow.setScale(0.38, 0.38, 1.0)
        self.scoreboard = OnscreenText(text="", pos=(-1.28, 0.92), scale=0.055, mayChange=True, fg=(1, 1, 1, 1), align=0)
        self.detail_text = OnscreenText(text="", pos=(-1.28, 0.84), scale=0.038, mayChange=True, fg=(0.82, 0.88, 0.96, 1), align=0)
        self.cue_text = OnscreenText(text="", pos=(-1.28, 0.76), scale=0.035, mayChange=True, fg=(1.0, 0.9, 0.7, 1), align=0)
        self.prompt_text = OnscreenText(text="", pos=(-1.28, 0.68), scale=0.03, mayChange=True, fg=(0.88, 0.92, 0.98, 0.92), align=0)
        self.help_text = OnscreenText(
            text="space play/pause | left/right step | c camera | 1/2/3 speed | r restart",
            pos=(-1.28, -0.95),
            scale=0.032,
            mayChange=False,
            fg=(0.85, 0.85, 0.85, 0.85),
            align=0,
        )
        self.focus_marker = self._make_focus_marker()

    def _build_lights(self) -> None:
        ambient = AmbientLight("ambient")
        ambient.setColor((0.45, 0.45, 0.48, 1.0))
        ambient_node = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_node)

        key = DirectionalLight("key")
        key.setColor((0.95, 0.95, 0.90, 1.0))
        key_node = self.render.attachNewNode(key)
        key_node.setHpr(-28, -52, 0)
        self.render.setLight(key_node)

    def _build_arena(self) -> None:
        surface = self.surface
        field = self._make_card(
            width=surface["width"] + 10.0,
            length=surface["length"] + 10.0,
            color=self._surface_color(),
        )
        field.reparentTo(self.render)
        field.setPos(0, 0, 0)

        line_root = self.render.attachNewNode("field-lines")
        lines = LineSegs()
        lines.setThickness(2.0)
        lines.setColor(0.94, 0.94, 0.94, 1.0)
        self._draw_surface_lines(lines)
        line_root.attachNewNode(lines.create())

        stand_color = (0.12, 0.13, 0.18, 1.0)
        stand_specs = [
            ((surface["width"] / 2.0 + 18.0, 0.0, 7.0), (18.0, surface["length"] + 34.0, 7.0)),
            ((-surface["width"] / 2.0 - 18.0, 0.0, 7.0), (18.0, surface["length"] + 34.0, 7.0)),
            ((0.0, surface["length"] / 2.0 + 16.0, 7.0), (surface["width"] + 32.0, 16.0, 7.0)),
            ((0.0, -surface["length"] / 2.0 - 16.0, 7.0), (surface["width"] + 32.0, 16.0, 7.0)),
        ]
        for center, scale in stand_specs:
            stand = self._make_cube(stand_color, scale=scale)
            stand.reparentTo(self.render)
            stand.setPos(*center)

    def _build_crowd(self) -> None:
        surface = self.surface
        crowd_rows = 6 if self.sport == "football" else 5
        seats_per_side = 28 if self.sport == "football" else 22
        for side in (-1, 1):
            for row in range(crowd_rows):
                z_value = 3.0 + row * 1.25
                for seat in range(seats_per_side):
                    y_value = -surface["length"] / 2.0 - 10.0 + seat * ((surface["length"] + 20.0) / max(seats_per_side - 1, 1))
                    x_value = side * (surface["width"] / 2.0 + 8.0 + row * 1.2)
                    fan = self._make_cube((0.48, 0.55, 0.62, 0.92), scale=(0.45, 0.45, 0.8))
                    fan.reparentTo(self.render)
                    fan.setPos(x_value, y_value, z_value)
                    fan.setTransparency(TransparencyAttrib.MAlpha)
                    self._crowd_nodes.append(fan)
                    self._crowd_offsets.append((row * 0.37) + (seat * 0.08))
                    self._crowd_base_z.append(z_value)

    def _build_player_node(self, color: Tuple[float, float, float, float]) -> Dict[str, NodePath]:
        root = self.render.attachNewNode("player")
        torso = self._make_cube(color, scale=(0.55, 0.42, 1.15))
        torso.reparentTo(root)
        torso.setZ(1.15)
        head = self._make_cube((0.95, 0.82, 0.68, 1.0), scale=(0.34, 0.34, 0.34))
        head.reparentTo(root)
        head.setZ(2.2)
        left_arm = self._make_cube(color, scale=(0.14, 0.14, 0.72))
        left_arm.reparentTo(root)
        left_arm.setPos(-0.34, 0.0, 1.36)
        right_arm = self._make_cube(color, scale=(0.14, 0.14, 0.72))
        right_arm.reparentTo(root)
        right_arm.setPos(0.34, 0.0, 1.36)
        left_leg = self._make_cube(color, scale=(0.18, 0.18, 0.85))
        left_leg.reparentTo(root)
        left_leg.setPos(-0.12, 0.0, 0.42)
        right_leg = self._make_cube(color, scale=(0.18, 0.18, 0.85))
        right_leg.reparentTo(root)
        right_leg.setPos(0.12, 0.0, 0.42)
        root.setScale(1.0)
        badge = self._make_cube((1.0, 1.0, 1.0, 0.95), scale=(0.10, 0.02, 0.10))
        badge.reparentTo(root)
        badge.setPos(0.0, -0.23, 1.55)
        return {
            "root": root,
            "torso": torso,
            "head": head,
            "left_arm": left_arm,
            "right_arm": right_arm,
            "left_leg": left_leg,
            "right_leg": right_leg,
            "badge": badge,
        }

    def _make_focus_marker(self) -> NodePath:
        maker = CardMaker("focus-marker")
        maker.setFrame(-1.0, 1.0, -1.0, 1.0)
        marker = self.render.attachNewNode(maker.generate())
        marker.setP(-90)
        marker.setColor(1.0, 0.84, 0.25, 0.2)
        marker.setTransparency(TransparencyAttrib.MAlpha)
        marker.setZ(0.08)
        return marker

    def _make_cube(self, color: Tuple[float, float, float, float], scale: Tuple[float, float, float]) -> NodePath:
        model = self.loader.loadModel("models/misc/rgbCube")
        model.clearTexture()
        model.setColor(*color)
        model.setScale(*scale)
        return model

    def _make_card(self, width: float, length: float, color: Tuple[float, float, float, float]) -> NodePath:
        maker = CardMaker("surface")
        maker.setFrame(-width / 2.0, width / 2.0, -length / 2.0, length / 2.0)
        card = self.render.attachNewNode(maker.generate())
        card.setP(-90)
        card.setColor(*color)
        return card

    def _surface_color(self) -> Tuple[float, float, float, float]:
        if self.sport == "basketball":
            return (0.76, 0.57, 0.31, 1.0)
        if self.sport == "baseball":
            return (0.26, 0.53, 0.25, 1.0)
        return (0.14, 0.46, 0.16, 1.0)

    def _draw_surface_lines(self, lines: LineSegs) -> None:
        width = self.surface["width"]
        length = self.surface["length"]
        x0 = -width / 2.0
        x1 = width / 2.0
        y0 = -length / 2.0
        y1 = length / 2.0
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        for index, (x_value, y_value) in enumerate(corners):
            if index == 0:
                lines.moveTo(x_value, y_value, 0.06)
            else:
                lines.drawTo(x_value, y_value, 0.06)
        if self.sport == "football":
            lines.moveTo(0.0, y0, 0.06)
            lines.drawTo(0.0, y1, 0.06)
        elif self.sport == "basketball":
            lines.moveTo(0.0, y0, 0.06)
            lines.drawTo(0.0, y1, 0.06)
            radius = 6.0
            for step in range(65):
                angle = (step / 64.0) * 2.0 * math.pi
                px = math.cos(angle) * radius
                py = math.sin(angle) * radius
                if step == 0:
                    lines.moveTo(px, py, 0.06)
                else:
                    lines.drawTo(px, py, 0.06)
        else:
            diamond = [self._to_scene(14.0, 14.0, 0.06), self._to_scene(31.75, 31.75, 0.06), self._to_scene(49.5, 14.0, 0.06), self._to_scene(31.75, -3.75, 0.06), self._to_scene(14.0, 14.0, 0.06)]
            for index, point in enumerate(diamond):
                if index == 0:
                    lines.moveTo(*point)
                else:
                    lines.drawTo(*point)

    def _bind_controls(self) -> None:
        self.accept("space", self._toggle_pause)
        self.accept("arrow_left", self._step_relative, [-1])
        self.accept("arrow_right", self._step_relative, [1])
        self.accept("c", self._cycle_camera)
        self.accept("r", self._restart)
        self.accept("1", self._set_speed, [0.75])
        self.accept("2", self._set_speed, [1.0])
        self.accept("3", self._set_speed, [1.5])
        self.accept("escape", self.userExit)

    def _toggle_pause(self) -> None:
        self.playing = not self.playing

    def _step_relative(self, offset: int) -> None:
        self.playing = False
        self.current_index = int(max(0, min(len(self.frames) - 1, self.current_index + offset)))
        self.current_time = float(self.frames[self.current_index]["time"])
        self._apply_frame(self.frames[self.current_index])

    def _cycle_camera(self) -> None:
        self.camera_mode = (self.camera_mode + 1) % 3
        self._update_camera(self.frames[self.current_index])

    def _restart(self) -> None:
        self.current_index = 0
        self.current_time = 0.0
        self.playing = False
        self._apply_frame(self.frames[0])

    def _set_speed(self, speed: float) -> None:
        self.playback_speed = speed

    def _update_task(self, task):
        dt = globalClock.getDt()
        self._wall_clock += dt
        if self.auto_close_after is not None and self._wall_clock >= self.auto_close_after:
            self.userExit()
            return task.done
        if self.playing:
            self.current_time += dt * self.playback_speed
            if self.current_time >= self.match_seconds:
                self.current_time = self.match_seconds
                self.playing = False
            while self.current_index < len(self.frames) - 1 and self.frames[self.current_index + 1]["time"] <= self.current_time:
                self.current_index += 1
            self._apply_frame(self.frames[self.current_index])
        return task.cont

    def _apply_frame(self, frame: Dict[str, object]) -> None:
        for node, actor in zip(self.home_nodes, frame["home_players"]):
            self._position_actor(node, actor)
        for node, actor in zip(self.away_nodes, frame["away_players"]):
            self._position_actor(node, actor)
        ball_x, ball_y, ball_z = self._to_scene(*frame["ball"])
        self.ball_node.setPos(ball_x, ball_y, ball_z + 0.3)
        if self.ball_shadow is not None:
            shadow_scale = max(0.22, 0.42 - min(0.2, ball_z * 0.015))
            self.ball_shadow.setPos(ball_x, ball_y, 0.05)
            self.ball_shadow.setScale(shadow_scale, shadow_scale, 1.0)
        self._animate_crowd(frame)
        self._update_focus_marker(frame)
        self._update_camera(frame)
        display_name = get_sport_config(self.sport).display_name
        self.scoreboard.setText(
            f"{display_name} | {frame['home_team']} {frame['home_score']} - {frame['away_score']} {frame['away_team']} | {frame['minute']:.1f}'"
        )
        self.detail_text.setText(
            f"Possession: {frame['possession']} | Phase {frame.get('phase', 'transition')} | Ball {frame.get('ball_speed', 0.0):.2f} m/s | Crowd {frame['crowd_intensity']:.2f} | Speed x{self.playback_speed:.2f}"
        )
        self.cue_text.setText(
            f"Focus {str(frame.get('attention_focus', 'whole_field_read')).replace('_', ' ')} | Window {str(frame.get('pressure_window', 'standard_window')).replace('_', ' ')} | Reflex {float(frame.get('reflex_intensity', 0.5)):.2f}"
        )
        self.prompt_text.setText(str(frame.get("spectator_prompt", "Read both teams and react to the pressure swing.")))

    def _position_actor(self, node: Dict[str, NodePath], actor: Dict[str, object]) -> None:
        x_value, y_value, z_value = self._to_scene(float(actor["x"]), float(actor["y"]), float(actor["z"]))
        root = node["root"]
        root.setPos(x_value, y_value, z_value)
        root.setH(-float(actor.get("heading", 0.0)))
        self._animate_actor(node, actor)

    def _animate_actor(self, node: Dict[str, NodePath], actor: Dict[str, object]) -> None:
        speed = float(actor.get("speed", 0.0))
        gait_phase = float(actor.get("gait_phase", 0.0))
        action = str(actor.get("action", "set"))
        mistake_state = str(actor.get("mistake_state", "stable"))
        lean = float(actor.get("lean", 0.0))
        balance_phase = float(actor.get("gait_phase", 0.0))
        base_z = node["root"].getZ()
        stride = min(38.0, 8.0 + speed * 4.2)
        arm_swing = stride * 0.85
        control_actions = {
            "control",
            "receive",
            "carry",
            "shield",
            "short_pass",
            "switch_pass",
            "through_ball",
            "cross",
            "set_pitch",
            "receive_pitch",
            "work_count",
            "field_transfer",
            "relay_throw",
            "lead_off",
            "dribble_probe",
            "swing_pass",
            "post_entry",
            "jab_step",
            "screen_reject",
        }
        defensive_actions = {
            "press",
            "jockey",
            "mark",
            "block_lane",
            "intercept",
            "clear",
            "guard_goal",
            "frame_pitch",
            "tag_runner",
            "force_out",
            "cut_off_lane",
            "stay_home",
            "chase_ball",
            "contain_drive",
            "close_out",
            "switch",
            "box_out",
            "guard_rim",
            "guard",
        }
        scoring_actions = {"shoot", "header", "release", "swing_contact", "drive_gap", "sacrifice_fly", "steal_break", "pull_up", "catch_and_shoot", "layup", "dunk"}
        recovery_actions = {"recover", "regather", "retreat", "reset_shape", "scramble", "relay_recover", "dead_ball_reset", "reset"}
        if action in control_actions:
            stride *= 0.55
            arm_swing *= 0.45
        elif action in defensive_actions:
            stride *= 0.92
        elif action in scoring_actions:
            stride = 42.0
            arm_swing = 12.0
        elif action in recovery_actions:
            stride *= 0.48
            arm_swing *= 0.38
        elif action == "guard":
            stride = 4.0
            arm_swing = 6.0
        leg_a = math.sin(gait_phase) * stride
        leg_b = math.sin(gait_phase + math.pi) * stride
        arm_a = math.sin(gait_phase + math.pi) * arm_swing
        arm_b = math.sin(gait_phase) * arm_swing
        node["left_leg"].setP(leg_a)
        node["right_leg"].setP(leg_b)
        node["left_arm"].setP(arm_a)
        node["right_arm"].setP(arm_b)
        node["torso"].setP(-12.0 * lean)
        node["head"].setP(4.0 * lean)
        root_bob = 0.04 * min(1.0, speed / 6.0) * max(0.0, math.sin(balance_phase * 2.0))
        if action in {"shoot", "header", "release", "swing_contact", "pull_up", "layup", "dunk"}:
            root_bob += 0.08
        node["root"].setZ(base_z + root_bob)
        if action in scoring_actions:
            node["right_leg"].setP(-52.0)
            node["left_arm"].setP(24.0)
            node["right_arm"].setP(-18.0)
            node["torso"].setP(-18.0)
            node["head"].setP(10.0)
        elif action in defensive_actions:
            node["left_arm"].setP(-10.0)
            node["right_arm"].setP(-10.0)
            node["torso"].setP(6.0)
            node["head"].setP(-4.0)
        elif action in {"control", "receive", "carry", "dribble_probe", "post_entry"}:
            node["torso"].setP(-8.0)
            node["head"].setP(6.0)
        if mistake_state != "stable":
            wobble = 8.0 * math.sin(gait_phase * 0.8)
            node["torso"].setR(wobble)
            node["head"].setR(-wobble * 0.6)
        else:
            node["torso"].setR(0.0)
            node["head"].setR(0.0)

    def _animate_crowd(self, frame: Dict[str, object]) -> None:
        intensity = float(frame["crowd_intensity"])
        for node, offset, base_z in zip(self._crowd_nodes, self._crowd_offsets, self._crowd_base_z):
            pulse = 0.75 + 0.25 * math.sin(frame["time"] * 4.0 + offset)
            bright = min(1.0, 0.25 + intensity * pulse)
            node.setColor(0.22 + bright * 0.55, 0.18 + bright * 0.42, 0.24 + bright * 0.46, 0.95)
            node.setZ(base_z + 0.015 * math.sin(frame["time"] * 3.0 + offset))

    def _update_focus_marker(self, frame: Dict[str, object]) -> None:
        if self.focus_marker is None:
            return
        spot = frame.get("focus_spot") or frame.get("camera_target")
        if spot is None:
            return
        x_value, y_value, z_value = self._to_scene(float(spot[0]), float(spot[1]), float(spot[2]))
        reflex = float(frame.get("reflex_intensity", 0.5))
        radius = max(2.0, float(frame.get("focus_radius", 6.0)))
        pulse = 0.9 + 0.25 * math.sin(frame["time"] * (4.0 + reflex * 4.0))
        self.focus_marker.setPos(x_value, y_value, max(0.08, z_value * 0.02 + 0.08))
        self.focus_marker.setScale(radius * 0.14 * pulse, radius * 0.14 * pulse, 1.0)
        self.focus_marker.setColor(1.0, 0.84 - reflex * 0.2, 0.25 + reflex * 0.15, 0.12 + reflex * 0.18)

    def _update_camera(self, frame: Dict[str, object]) -> None:
        if self.camera is None:
            return
        focus_target = frame.get("focus_spot") or frame["camera_target"]
        target_x, target_y, target_z = self._to_scene(*focus_target)
        reflex = float(frame.get("reflex_intensity", 0.5))
        depth_scale = 1.0 - reflex * 0.16
        height_scale = 1.0 - reflex * 0.1
        if self.camera_mode == 0:
            cam_pos = (target_x, target_y - self.surface["length"] * 0.78 * depth_scale, self.surface["zmax"] * 0.88 * height_scale)
        elif self.camera_mode == 1:
            cam_pos = (self.surface["width"] * 0.76, target_y - self.surface["length"] * 0.12 * depth_scale, self.surface["zmax"] * 0.62 * height_scale)
        else:
            cam_pos = (target_x + self.surface["width"] * 0.24, target_y - self.surface["length"] * 0.26 * depth_scale, self.surface["zmax"] * 0.48 * height_scale)
        if self._camera_target_pos is None:
            self._camera_target_pos = cam_pos
        else:
            self._camera_target_pos = tuple(
                self._camera_target_pos[index] + (cam_pos[index] - self._camera_target_pos[index]) * 0.16
                for index in range(3)
            )
        self.camera.setPos(*self._camera_target_pos)
        self.camera.lookAt(target_x, target_y, target_z)

    def _to_scene(self, x_value: float, y_value: float, z_value: float) -> Tuple[float, float, float]:
        return (y_value - self.surface["width"] / 2.0, x_value - self.surface["length"] / 2.0, z_value)


def run_live_render(
    report_path: str,
    fixture_index: int = 0,
    offscreen: bool = False,
    auto_close_after: float | None = None,
    software_render: bool = False,
) -> None:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    app = LiveMatchRenderer(
        report=report,
        fixture_index=fixture_index,
        offscreen=offscreen,
        auto_close_after=auto_close_after,
        software_render=software_render,
    )
    app.run()


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Open the DirkOdds live 3D match renderer for a prediction report.")
    parser.add_argument("--report", required=True, help="Path to a DirkOdds report JSON file")
    parser.add_argument("--fixture-index", type=int, default=0, help="Simulation index inside the report")
    parser.add_argument("--offscreen", action="store_true", help="Create the renderer in offscreen mode")
    parser.add_argument("--auto-close-after", type=float, help="Auto-close the renderer after N wall-clock seconds")
    parser.add_argument("--software-render", action="store_true", help="Force Panda3D software rendering when hardware OpenGL is unavailable")
    args = parser.parse_args(argv)
    run_live_render(
        args.report,
        fixture_index=args.fixture_index,
        offscreen=args.offscreen,
        auto_close_after=args.auto_close_after,
        software_render=args.software_render,
    )


if __name__ == "__main__":
    main(sys.argv[1:])