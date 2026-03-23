from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6 import QtCore, QtWidgets

from .avatar_profile import HEAD_SIZE_M, AvatarProfile, build_avatar_profile
from .challenge_mode import build_challenge_cue_profile
from .player_stats import fixture_player_qualities, load_player_stats_csv
from .simulation import SimulationConfig, simulate_match, with_probability_override
from .sports import get_sport_config, normalize_sport


DEFAULT_MATCH_SECONDS = 24.0

SURFACE_CONFIG = {
    "football": {"title": "Pitch", "length": 105.0, "width": 68.0, "zmax": 12.0},
    "baseball": {"title": "Diamond", "length": 127.0, "width": 127.0, "zmax": 18.0},
    "basketball": {"title": "Court", "length": 94.0, "width": 50.0, "zmax": 14.0},
}


def build_playback_frames(simulation_result: Dict[str, object], match_seconds: float = DEFAULT_MATCH_SECONDS) -> List[Dict[str, object]]:
    sport = normalize_sport(simulation_result.get("sport", "football"))
    trajectories = simulation_result.get("event_trajectories", []) or []
    frames: List[Dict[str, object]] = []
    home_score = 0
    away_score = 0
    for event in sorted(trajectories, key=lambda item: float(item.get("minute", 0.0))):
        event_start = float(event.get("minute", 0.0)) / 90.0 * match_seconds
        team = str(event.get("team", "home"))
        points = event.get("trajectory", []) or []
        if not points:
            continue
        for point in points:
            x = float(point["x"])
            y = float(point["y"])
            z = float(point["z"])
            attacker, keeper = _playback_actor_positions(sport, team, (x, y, z))
            frames.append(
                {
                    "sport": sport,
                    "time": event_start + float(point["t"]),
                    "minute": float(event.get("minute", 0.0)),
                    "ball": (x, y, z),
                    "attacker": attacker,
                    "keeper": keeper,
                    "team": team,
                    "home_score": home_score,
                    "away_score": away_score,
                    "phase_state": str(event.get("phase_state", "transition")),
                    "primary_action": str(event.get("primary_action", event.get("event_type", "release"))),
                    "pressure_window": str(event.get("pressure_window", "standard_window")),
                    "attention_focus": str(event.get("attention_focus", "whole_field_read")),
                    "spectator_prompt": str(event.get("spectator_prompt", "Track both teams.")),
                    "focus_radius": float(event.get("focus_radius", 6.0)),
                    "focus_spot": (
                        float((event.get("hotspot") or {}).get("x", x)),
                        float((event.get("hotspot") or {}).get("y", y)),
                        float((event.get("hotspot") or {}).get("z", z)),
                    ),
                    "reflex_intensity": float(event.get("reflex_intensity", 0.5)),
                }
            )
        if team == "home":
            home_score += 1
        else:
            away_score += 1
        if frames:
            frames[-1]["home_score"] = home_score
            frames[-1]["away_score"] = away_score
    if not frames:
        frames.append(
            {
                "sport": sport,
                "time": 0.0,
                "minute": 0.0,
                "ball": _default_ball_position(sport),
                "attacker": _default_actor_positions(sport)[0],
                "keeper": _default_actor_positions(sport)[1],
                "team": "home",
                "home_score": 0,
                "away_score": 0,
                "phase_state": "preview",
                "primary_action": "scan",
                "pressure_window": "wide_window",
                "attention_focus": "whole_field_read",
                "spectator_prompt": "Track both teams and wait for a live interaction.",
                "focus_radius": 6.0,
                "focus_spot": _default_ball_position(sport),
                "reflex_intensity": 0.25,
            }
        )
    return frames


def _default_ball_position(sport: str) -> tuple[float, float, float]:
    surface = SURFACE_CONFIG[normalize_sport(sport)]
    if sport == "baseball":
        return (14.0, 14.0, 1.0)
    return (surface["length"] / 2.0, surface["width"] / 2.0, 0.18)


def _default_actor_positions(sport: str) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    surface = SURFACE_CONFIG[normalize_sport(sport)]
    if sport == "basketball":
        return ((surface["length"] / 2.0 - 6.0, surface["width"] / 2.0, 0.0), (surface["length"] - 7.0, surface["width"] / 2.0, 0.0))
    if sport == "baseball":
        return ((14.0, 14.0, 0.0), (63.5, 63.5, 0.0))
    return ((50.0, 34.0, 0.0), (103.0, 34.0, 0.0))


def _playback_actor_positions(sport: str, team: str, ball: tuple[float, float, float]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    x, y, _ = ball
    surface = SURFACE_CONFIG[normalize_sport(sport)]
    if sport == "basketball":
        defender_x = min(surface["length"] - 4.5, x + 5.0) if team == "home" else max(4.5, x - 5.0)
        attacker_x = max(0.0, min(surface["length"], x - (2.0 if team == "home" else -2.0)))
        defender_y = surface["width"] / 2.0 + float(np.clip((y - surface["width"] / 2.0) * 0.3, -6.0, 6.0))
        return (attacker_x, y, 0.0), (defender_x, defender_y, 0.0)
    if sport == "baseball":
        runner_x = max(0.0, min(surface["length"], x * 0.42 + 10.0))
        runner_y = max(0.0, min(surface["width"], y * 0.42 + 10.0))
        fielder_x = max(0.0, min(surface["length"], x - 10.0))
        fielder_y = max(0.0, min(surface["width"], y - 8.0))
        return (runner_x, runner_y, 0.0), (fielder_x, fielder_y, 0.0)
    keeper_x = surface["length"] - 2.0 if team == "home" else 2.0
    keeper_y = surface["width"] / 2.0 + float(np.clip((y - surface["width"] / 2.0) * 0.22, -6.0, 6.0))
    attacker_x = float(np.clip(x - (2.8 if team == "home" else -2.8), 0.0, surface["length"]))
    return (attacker_x, y, 0.0), (keeper_x, keeper_y, 0.0)


def _draw_surface(ax, sport: str) -> None:
    sport = normalize_sport(sport)
    surface = SURFACE_CONFIG[sport]
    ax.clear()
    ax.set_xlim(0.0, surface["length"])
    ax.set_ylim(0.0, surface["width"])
    ax.set_zlim(0.0, surface["zmax"])
    ax.set_xlabel("Length")
    ax.set_ylabel("Width")
    ax.set_zlabel("Height")
    ax.view_init(elev=22, azim=-62)
    if sport == "basketball":
        corners = [(0, 0), (surface["length"], 0), (surface["length"], surface["width"]), (0, surface["width"]), (0, 0)]
        xs, ys = zip(*corners)
        ax.plot(xs, ys, zs=[0] * len(xs), color="#d08b3e", linewidth=1.5)
        ax.plot([surface["length"] / 2.0, surface["length"] / 2.0], [0, surface["width"]], zs=[0, 0], color="#d08b3e", linewidth=1.0)
        circle = np.linspace(0, 2 * np.pi, 100)
        ax.plot(surface["length"] / 2.0 + 6.0 * np.cos(circle), surface["width"] / 2.0 + 6.0 * np.sin(circle), zs=np.zeros_like(circle), color="#d08b3e", linewidth=1.0)
        for hoop_x in [5.25, surface["length"] - 5.25]:
            ax.plot([hoop_x, hoop_x], [surface["width"] / 2.0 - 3.0, surface["width"] / 2.0 + 3.0], zs=[surface["zmax"] * 0.22, surface["zmax"] * 0.22], color="#ff6f3c", linewidth=2.0)
    elif sport == "baseball":
        diamond = np.array([[14.0, 14.0], [31.75, 31.75], [49.5, 14.0], [31.75, -3.75], [14.0, 14.0]])
        ax.plot(diamond[:, 0], diamond[:, 1], zs=np.zeros(len(diamond)), color="#a37b52", linewidth=1.6)
        outfield = np.linspace(np.pi / 4.0, 3.0 * np.pi / 4.0, 80)
        ax.plot(14.0 + 105.0 * np.cos(outfield), 14.0 + 105.0 * np.sin(outfield), zs=np.zeros_like(outfield), color="#3a7d44", linewidth=1.2)
        ax.scatter([14.0, 31.75, 49.5, 31.75], [14.0, 31.75, 14.0, -3.75], [0.0, 0.0, 0.0, 0.0], color="#f4e7c5", s=18)
    else:
        corners = [(0, 0), (surface["length"], 0), (surface["length"], surface["width"]), (0, surface["width"]), (0, 0)]
        xs, ys = zip(*corners)
        ax.plot(xs, ys, zs=[0] * len(xs), color="#2b7a0b", linewidth=1.5)
        ax.plot([surface["length"] / 2.0, surface["length"] / 2.0], [0, surface["width"]], zs=[0, 0], color="#2b7a0b", linewidth=1.0)
        circle = np.linspace(0, 2 * np.pi, 100)
        ax.plot(surface["length"] / 2.0 + 9.15 * np.cos(circle), surface["width"] / 2.0 + 9.15 * np.sin(circle), zs=np.zeros_like(circle), color="#2b7a0b", linewidth=1.0)


def _avatar_profiles_for_fixture(row: pd.Series, players_df: Optional[pd.DataFrame]) -> Dict[str, AvatarProfile]:
    match_date = str(pd.to_datetime(row["date"]).date())
    return {
        "home_attacker": build_avatar_profile(
            str(row["home_team"]),
            role="attacker",
            player_quality=float(row.get("home_player_quality", 0.0)),
            players_df=players_df,
            match_date=match_date,
        ),
        "away_attacker": build_avatar_profile(
            str(row["away_team"]),
            role="attacker",
            player_quality=float(row.get("away_player_quality", 0.0)),
            players_df=players_df,
            match_date=match_date,
        ),
        "home_keeper": build_avatar_profile(
            str(row["home_team"]),
            role="keeper",
            player_quality=float(row.get("home_player_quality", 0.0)),
            players_df=players_df,
            match_date=match_date,
        ),
        "away_keeper": build_avatar_profile(
            str(row["away_team"]),
            role="keeper",
            player_quality=float(row.get("away_player_quality", 0.0)),
            players_df=players_df,
            match_date=match_date,
        ),
    }


def _draw_avatar(ax, position: tuple[float, float, float], profile: AvatarProfile, color: str) -> None:
    x, y, z = position
    foot_z = float(z)
    head_radius = profile.head_size_m / 2.0
    height = profile.height_m
    shoulder_z = foot_z + height - profile.head_size_m - 0.08
    pelvis_z = max(foot_z + profile.leg_length_m, foot_z + 0.42 * height)
    head_center_z = foot_z + height - head_radius
    shoulder_half_width = profile.shoulder_width_m / 2.0
    arm_reach = shoulder_half_width * 1.15

    ax.plot([x, x], [y, y], [pelvis_z, shoulder_z], color=color, linewidth=2.6)
    ax.plot([x - shoulder_half_width, x + shoulder_half_width], [y, y], [shoulder_z, shoulder_z], color=color, linewidth=2.4)
    ax.plot([x - shoulder_half_width, x - arm_reach], [y, y], [shoulder_z, foot_z + 0.54 * height], color=color, linewidth=2.0, alpha=0.9)
    ax.plot([x + shoulder_half_width, x + arm_reach], [y, y], [shoulder_z, foot_z + 0.54 * height], color=color, linewidth=2.0, alpha=0.9)
    hip_spread = max(profile.torso_depth_m * 0.35, 0.08)
    ax.plot([x, x - hip_spread], [y, y], [pelvis_z, foot_z], color=color, linewidth=2.2)
    ax.plot([x, x + hip_spread], [y, y], [pelvis_z, foot_z], color=color, linewidth=2.2)
    ax.scatter([x], [y], [head_center_z], color=color, s=(profile.head_size_m * 180.0) ** 2 * 0.12)
    ax.plot(
        [x - shoulder_half_width, x + shoulder_half_width, x + shoulder_half_width, x - shoulder_half_width, x - shoulder_half_width],
        [y - profile.torso_depth_m / 2.0, y - profile.torso_depth_m / 2.0, y + profile.torso_depth_m / 2.0, y + profile.torso_depth_m / 2.0, y - profile.torso_depth_m / 2.0],
        [pelvis_z, pelvis_z, shoulder_z, shoulder_z, pelvis_z],
        color=color,
        alpha=0.55,
        linewidth=1.4,
    )


class PlaybackWindow(QtWidgets.QWidget):
    def __init__(self, report: Optional[Dict[str, object]] = None):
        super().__init__()
        self.setWindowTitle("DirkOdds 3D Playback")
        self.resize(1200, 860)

        self.report = report or {"predictions": [], "simulations": []}
        self.predictions_df = pd.DataFrame(self.report.get("predictions", []))
        self.player_stats_df: Optional[pd.DataFrame] = None
        self.frames: List[Dict[str, object]] = []
        self.avatar_profiles: Dict[str, AvatarProfile] = {}
        self.simulations: List[Dict[str, object]] = list(self.report.get("simulations", []))
        self.current_result: Optional[Dict[str, object]] = None
        self.current_time = 0.0
        self.match_seconds = DEFAULT_MATCH_SECONDS
        self.session_state = dict(self.report.get("session_state", {}))
        self._pending_restore_time: Optional[float] = None

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._tick)

        root = QtWidgets.QVBoxLayout(self)

        top_row = QtWidgets.QHBoxLayout()
        self.load_report_btn = QtWidgets.QPushButton("Load Report")
        self.load_report_btn.clicked.connect(self.load_report)
        top_row.addWidget(self.load_report_btn)

        self.save_session_btn = QtWidgets.QPushButton("Save Session")
        self.save_session_btn.clicked.connect(self.save_session_report)
        top_row.addWidget(self.save_session_btn)

        self.load_stats_btn = QtWidgets.QPushButton("Load Player Stats CSV")
        self.load_stats_btn.clicked.connect(self.load_player_stats)
        top_row.addWidget(self.load_stats_btn)

        self.fixture_combo = QtWidgets.QComboBox()
        self.fixture_combo.currentIndexChanged.connect(self._fixture_changed)
        top_row.addWidget(self.fixture_combo, 1)
        root.addLayout(top_row)

        controls = QtWidgets.QGridLayout()
        self.home_prob = QtWidgets.QDoubleSpinBox()
        self.home_prob.setRange(0.0, 1.0)
        self.home_prob.setSingleStep(0.01)
        self.draw_prob = QtWidgets.QDoubleSpinBox()
        self.draw_prob.setRange(0.0, 1.0)
        self.draw_prob.setSingleStep(0.01)
        self.away_prob = QtWidgets.QDoubleSpinBox()
        self.away_prob.setRange(0.0, 1.0)
        self.away_prob.setSingleStep(0.01)
        self.user_weight = QtWidgets.QDoubleSpinBox()
        self.user_weight.setRange(0.0, 1.0)
        self.user_weight.setSingleStep(0.05)
        self.user_weight.setValue(0.5)
        self.home_quality = QtWidgets.QDoubleSpinBox()
        self.home_quality.setRange(-2.0, 2.0)
        self.home_quality.setSingleStep(0.1)
        self.away_quality = QtWidgets.QDoubleSpinBox()
        self.away_quality.setRange(-2.0, 2.0)
        self.away_quality.setSingleStep(0.1)
        self.match_speed = QtWidgets.QDoubleSpinBox()
        self.match_speed.setRange(8.0, 60.0)
        self.match_speed.setValue(DEFAULT_MATCH_SECONDS)
        self.match_speed.setSingleStep(2.0)

        for widget in [self.home_prob, self.draw_prob, self.away_prob, self.user_weight, self.home_quality, self.away_quality, self.match_speed]:
            widget.valueChanged.connect(self._resimulate_selected_fixture)

        labels = [
            ("Home prob", self.home_prob),
            ("Draw prob", self.draw_prob),
            ("Away prob", self.away_prob),
            ("User weight", self.user_weight),
            ("Home quality", self.home_quality),
            ("Away quality", self.away_quality),
            ("Match seconds", self.match_speed),
        ]
        for index, (label, widget) in enumerate(labels):
            controls.addWidget(QtWidgets.QLabel(label), 0, index)
            controls.addWidget(widget, 1, index)

        self.restart_btn = QtWidgets.QPushButton("Restart")
        self.restart_btn.clicked.connect(self._restart_playback)
        controls.addWidget(self.restart_btn, 0, len(labels), 2, 1)

        self.step_back_btn = QtWidgets.QPushButton("Step -")
        self.step_back_btn.clicked.connect(lambda: self._step_frame(-1))
        controls.addWidget(self.step_back_btn, 0, len(labels) + 1, 2, 1)

        self.play_btn = QtWidgets.QPushButton("Play")
        self.play_btn.clicked.connect(self.toggle_playback)
        controls.addWidget(self.play_btn, 0, len(labels) + 2, 2, 1)

        self.step_forward_btn = QtWidgets.QPushButton("Step +")
        self.step_forward_btn.clicked.connect(lambda: self._step_frame(1))
        controls.addWidget(self.step_forward_btn, 0, len(labels) + 3, 2, 1)

        self.challenge_mode_checkbox = QtWidgets.QCheckBox("Challenge Cue Mode")
        self.challenge_mode_checkbox.setChecked(True)
        self.challenge_mode_checkbox.stateChanged.connect(self._refresh_visible_state)
        controls.addWidget(self.challenge_mode_checkbox, 0, len(labels) + 4, 2, 1)
        root.addLayout(controls)

        self.fixture_status = QtWidgets.QLabel("No fixture selected.")
        self.fixture_status.setWordWrap(True)
        root.addWidget(self.fixture_status)

        self.summary = QtWidgets.QLabel("Load a prediction report to begin playback.")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        self.cue_banner = QtWidgets.QLabel("Attention cues will appear here during playback.")
        self.cue_banner.setWordWrap(True)
        self.cue_banner.setStyleSheet("padding: 8px 10px; background: #18232f; color: #e7eef6; border-radius: 6px;")
        root.addWidget(self.cue_banner)

        self.state_summary = QtWidgets.QPlainTextEdit()
        self.state_summary.setReadOnly(True)
        self.state_summary.setMaximumHeight(170)

        self.operator_summary = QtWidgets.QPlainTextEdit()
        self.operator_summary.setReadOnly(True)
        self.operator_summary.setMaximumHeight(190)

        self.detail_tabs = QtWidgets.QTabWidget()
        self.detail_tabs.addTab(self.state_summary, "State")
        self.detail_tabs.addTab(self.operator_summary, "Operator")
        root.addWidget(self.detail_tabs)

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.axis = self.figure.add_subplot(111, projection="3d")
        root.addWidget(self.canvas, 1)

        timeline_row = QtWidgets.QHBoxLayout()
        timeline_row.addWidget(QtWidgets.QLabel("Timeline"))

        self.time_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.time_slider.setRange(0, 1000)
        self.time_slider.valueChanged.connect(self._seek)
        timeline_row.addWidget(self.time_slider, 1)

        self.playhead_label = QtWidgets.QLabel("00:00 / 00:24")
        timeline_row.addWidget(self.playhead_label)

        self.score_label = QtWidgets.QLabel("Score 0-0")
        timeline_row.addWidget(self.score_label)

        root.addLayout(timeline_row)

        self._refresh_fixture_list()
        self._restore_session_state()
        if not self.predictions_df.empty:
            self._fixture_changed(self.fixture_combo.currentIndex() if self.fixture_combo.currentIndex() >= 0 else 0)
        else:
            self._render_pitch_only()

    def _active_sport(self) -> str:
        if self.current_result is not None:
            return normalize_sport(self.current_result.get("sport", "football"))
        index = self.fixture_combo.currentIndex()
        if not self.predictions_df.empty and 0 <= index < len(self.predictions_df):
            return normalize_sport(self.predictions_df.iloc[index].get("sport", "football"))
        return "football"

    def _restore_session_state(self) -> None:
        if not self.session_state:
            return
        self.challenge_mode_checkbox.blockSignals(True)
        self.challenge_mode_checkbox.setChecked(bool(self.session_state.get("challenge_mode_enabled", True)))
        self.challenge_mode_checkbox.blockSignals(False)
        self.user_weight.setValue(float(self.session_state.get("user_weight", self.user_weight.value())))
        self.home_quality.setValue(float(self.session_state.get("home_quality", self.home_quality.value())))
        self.away_quality.setValue(float(self.session_state.get("away_quality", self.away_quality.value())))
        self.match_speed.setValue(float(self.session_state.get("match_seconds", self.match_speed.value())))
        current_time = self.session_state.get("current_time")
        if current_time is not None:
            self._pending_restore_time = float(current_time)
        fixture_index = int(self.session_state.get("fixture_index", 0))
        if fixture_index >= 0 and fixture_index < self.fixture_combo.count():
            self.fixture_combo.setCurrentIndex(fixture_index)

    def _collect_session_state(self) -> Dict[str, object]:
        return {
            "challenge_mode_enabled": self.challenge_mode_checkbox.isChecked(),
            "fixture_index": self.fixture_combo.currentIndex(),
            "user_weight": self.user_weight.value(),
            "home_quality": self.home_quality.value(),
            "away_quality": self.away_quality.value(),
            "home_probability": self.home_prob.value(),
            "draw_probability": self.draw_prob.value(),
            "away_probability": self.away_prob.value(),
            "match_seconds": self.match_speed.value(),
            "current_time": self.current_time,
        }

    def save_session_report(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save playback session", filter="JSON Files (*.json);;All Files (*)")
        if not path:
            return
        payload = dict(self.report)
        payload["predictions"] = self.predictions_df.to_dict(orient="records") if not self.predictions_df.empty else []
        payload["simulations"] = self.simulations
        payload["session_state"] = self._collect_session_state()
        Path(path).write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    def _refresh_fixture_list(self) -> None:
        self.fixture_combo.blockSignals(True)
        self.fixture_combo.clear()
        if self.predictions_df.empty:
            self.fixture_combo.addItem("No fixtures loaded")
        else:
            for row in self.predictions_df.itertuples(index=False):
                self.fixture_combo.addItem(f"{row.home_team} vs {row.away_team} ({str(row.date)[:10]})")
        self.fixture_combo.blockSignals(False)

    def _render_pitch_only(self) -> None:
        sport = self._active_sport()
        _draw_surface(self.axis, sport)
        ball = _default_ball_position(sport)
        actors = _default_actor_positions(sport)
        self.axis.scatter([ball[0]], [ball[1]], [ball[2]], color="#ffffff", s=35)
        placeholder = build_avatar_profile("Home", role="attacker")
        _draw_avatar(self.axis, actors[0], placeholder, "#1f77b4")
        _draw_avatar(self.axis, actors[1], build_avatar_profile("Away", role="keeper"), "#d62728")
        self.axis.set_title(f"{get_sport_config(sport).display_name} {SURFACE_CONFIG[sport]['title']} Preview")
        self.figure.tight_layout()
        self.canvas.draw_idle()
        self.playhead_label.setText(f"00:00 / {self._format_clock(self.match_seconds)}")
        self.score_label.setText("Score 0-0")
        self.fixture_status.setText(f"{get_sport_config(sport).display_name} | Surface {SURFACE_CONFIG[sport]['title']} | Preview")

    def load_report(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open playback report", filter="JSON Files (*.json);;All Files (*)")
        if not path:
            return
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        self.report = payload
        self.predictions_df = pd.DataFrame(payload.get("predictions", []))
        self.simulations = list(payload.get("simulations", []))
        self.session_state = dict(payload.get("session_state", {}))
        self._refresh_fixture_list()
        self._restore_session_state()
        if not self.predictions_df.empty:
            self._fixture_changed(self.fixture_combo.currentIndex() if self.fixture_combo.currentIndex() >= 0 else 0)

    def load_player_stats(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open player stats CSV", filter="CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        self.player_stats_df = load_player_stats_csv(path)
        self._fixture_changed(self.fixture_combo.currentIndex())

    def _fixture_changed(self, index: int) -> None:
        if self.predictions_df.empty or index < 0 or index >= len(self.predictions_df):
            self.summary.setText("No fixture available.")
            self.frames = []
            self._render_pitch_only()
            return
        row = self.predictions_df.iloc[index]
        sport = normalize_sport(row.get("sport", "football"))
        self.fixture_status.setText(
            f"{get_sport_config(sport).display_name} | {row['home_team']} vs {row['away_team']} | {str(row.get('date', ''))[:10]} | Surface {SURFACE_CONFIG[sport]['title']}"
        )
        allows_draws = get_sport_config(sport).allows_draws
        self.home_prob.blockSignals(True)
        self.draw_prob.blockSignals(True)
        self.away_prob.blockSignals(True)
        self.home_prob.setValue(float(row.get("prob_home_win", 1.0 / 3.0)))
        self.draw_prob.setValue(float(row.get("prob_draw", 1.0 / 3.0 if allows_draws else 0.0)))
        self.away_prob.setValue(float(row.get("prob_away_win", 1.0 / 3.0)))
        self.draw_prob.setEnabled(allows_draws)

        qualities = fixture_player_qualities(row["home_team"], row["away_team"], str(pd.to_datetime(row["date"]).date()), self.player_stats_df)
        self.home_quality.setValue(float(row.get("home_player_quality", qualities["home_player_quality"])))
        self.away_quality.setValue(float(row.get("away_player_quality", qualities["away_player_quality"])))
        self.home_prob.blockSignals(False)
        self.draw_prob.blockSignals(False)
        self.away_prob.blockSignals(False)
        self._resimulate_selected_fixture()

    def _resimulate_selected_fixture(self) -> None:
        if self.predictions_df.empty:
            return
        index = self.fixture_combo.currentIndex()
        if index < 0 or index >= len(self.predictions_df):
            return
        row = self.predictions_df.iloc[index].copy()
        overridden = with_probability_override(
            row,
            home_probability=self.home_prob.value(),
            draw_probability=self.draw_prob.value(),
            away_probability=self.away_prob.value(),
            user_weight=self.user_weight.value(),
            home_player_quality=self.home_quality.value(),
            away_player_quality=self.away_quality.value(),
        )
        self.avatar_profiles = _avatar_profiles_for_fixture(overridden, self.player_stats_df)
        result = simulate_match(overridden, config=SimulationConfig(simulation_count=1000), random_state=42 + index)
        if index < len(self.simulations):
            self.simulations[index] = result
        else:
            self.simulations.append(result)
        self.current_result = result
        self.match_seconds = self.match_speed.value()
        self.frames = build_playback_frames(result, match_seconds=self.match_seconds)
        self._update_visible_summary(overridden, result)
        target_time = self.current_time
        if self._pending_restore_time is not None:
            target_time = self._pending_restore_time
            self._pending_restore_time = None
        self._set_current_time(target_time)

    def _refresh_visible_state(self) -> None:
        if self.current_result is None or self.predictions_df.empty:
            return
        index = self.fixture_combo.currentIndex()
        if index < 0 or index >= len(self.predictions_df):
            return
        row = self.predictions_df.iloc[index].copy()
        overridden = with_probability_override(
            row,
            home_probability=self.home_prob.value(),
            draw_probability=self.draw_prob.value(),
            away_probability=self.away_prob.value(),
            user_weight=self.user_weight.value(),
            home_player_quality=self.home_quality.value(),
            away_player_quality=self.away_quality.value(),
        )
        self._update_visible_summary(overridden, self.current_result)

    def _update_visible_summary(self, overridden: pd.Series, simulation_result: Dict[str, object]) -> None:
        challenge_mode = self.challenge_mode_checkbox.isChecked()
        cues = simulation_result.get("challenge_cues") or build_challenge_cue_profile(overridden, simulation_result)
        if challenge_mode:
            self.summary.setText(
                f"{simulation_result['home_team']} vs {simulation_result['away_team']} | pick={overridden['prediction']} | "
                f"signal={cues['visible_label']} | pressure={cues['pressure_label']} | timing={cues['timing_window_label']} | rhythm={cues['rhythm_label']}"
            )
        else:
            self.summary.setText(
                f"{simulation_result['home_team']} vs {simulation_result['away_team']} | pick={overridden['prediction']} | model/user blend={self.user_weight.value():.2f} | "
                f"xG {simulation_result['expected_goals_home']:.2f}-{simulation_result['expected_goals_away']:.2f} | most likely score {simulation_result['most_likely_score']['home']}-{simulation_result['most_likely_score']['away']}"
            )
        self.cue_banner.setText(
            f"Focus {cues.get('attention_focus_label', 'Whole-Field Read')} | Reflex {cues.get('reflex_window_label', 'Measured Reflex')} | "
            f"Target {cues.get('focus_target', 'central_balance').replace('_', ' ')} | {cues.get('spectator_prompt', 'Track the whole flow and react to pressure swings.')}"
        )
        self._update_state_summary(simulation_result, challenge_mode=challenge_mode)
        self._update_operator_summary(simulation_result)

    def _update_state_summary(self, simulation_result: Dict[str, object], challenge_mode: bool = True) -> None:
        incidents = simulation_result.get("match_incidents", []) or []
        entity_states = simulation_result.get("entity_states", {}) or {}
        home = entity_states.get("home", {})
        away = entity_states.get("away", {})
        cues = simulation_result.get("challenge_cues", {}) or {}
        lines = []
        if challenge_mode and cues:
            lines.append(
                f"Cue profile | signal={cues.get('visible_label', 'Unknown')} pressure={cues.get('pressure_label', 'Unknown')} timing={cues.get('timing_window_label', 'Unknown')} rhythm={cues.get('rhythm_label', 'Unknown')} focus={cues.get('attention_focus_label', 'Whole-Field Read')} reflex={cues.get('reflex_window_label', 'Measured Reflex')}"
            )
        if home:
            lines.append(
                f"Home state | preparedness={home.get('team_preparedness', 0.0):.2f} readiness={home.get('pregame_readiness', 0.0):.2f} fatigue={home.get('fatigue_pressure', 0.0):.2f} sodium={home.get('sodium_state', 0.0):.2f} coach={home.get('coach_motivation', 0.0):.2f}"
            )
            if home.get("delta_signature"):
                lines.append(
                    f"Home delta | magnitude={home['delta_signature'].get('delta_magnitude', 0.0):.2f} quality->preparedness={home['delta_signature'].get('quality_signal_to_preparedness_signal', 0.0):.2f}"
                )
        if away:
            lines.append(
                f"Away state | preparedness={away.get('team_preparedness', 0.0):.2f} readiness={away.get('pregame_readiness', 0.0):.2f} fatigue={away.get('fatigue_pressure', 0.0):.2f} sodium={away.get('sodium_state', 0.0):.2f} coach={away.get('coach_motivation', 0.0):.2f}"
            )
            if away.get("delta_signature"):
                lines.append(
                    f"Away delta | magnitude={away['delta_signature'].get('delta_magnitude', 0.0):.2f} quality->preparedness={away['delta_signature'].get('quality_signal_to_preparedness_signal', 0.0):.2f}"
                )
        if incidents:
            lines.append("Incidents:")
            for incident in incidents[:4]:
                lines.append(
                    f"{incident['minute']:.1f}' {incident['team']} {incident['role']} {incident['incident_type']} sev={incident['severity']:.2f}"
                )
        else:
            lines.append("Incidents: none synthesized in this run.")
        regulated_session = simulation_result.get("regulated_session", {}) or {}
        channels = regulated_session.get("simulation_channels", []) or []
        prompts = regulated_session.get("human_presence_prompts", []) or []
        consent_gate = regulated_session.get("consent_gate", {}) or {}
        if consent_gate:
            lines.append(
                f"Consent gate | lineup={consent_gate.get('lineup_approval_ratio', 0.0):.2f}/{consent_gate.get('required_ratio', 1.0):.2f} live_allowed={consent_gate.get('live_activation_allowed', False)}"
            )
        if channels:
            visible = [channel for channel in channels if channel.get("visible_to_user", False)]
            if visible:
                if challenge_mode:
                    lines.append(
                        "Channels: " + ", ".join(
                            f"{channel['label']} ({channel['state']})" for channel in visible[:2]
                        )
                    )
                else:
                    lines.append(
                        "Channels: " + ", ".join(
                            f"{channel['label']}={channel['confidence_band']:.2f} ({channel['state']})" for channel in visible[:2]
                        )
                    )
        if prompts:
            prompt = prompts[0]
            lines.append(
                f"Human check | next={prompt['prompt_type']} at {prompt['minute']:.1f}' window={prompt['response_window_ms']}ms"
            )
        hooks = simulation_result.get("artisapien_hooks", {}) or {}
        if hooks:
            lines.append(f"ArtiSapien hooks enabled={hooks.get('enabled', False)} status=placeholder_only")
        self.state_summary.setPlainText("\n".join(lines))

    def _update_operator_summary(self, simulation_result: Dict[str, object]) -> None:
        regulated_session = simulation_result.get("regulated_session", {}) or {}
        consent = regulated_session.get("player_consent_registry", {}) or {}
        entity_states = simulation_result.get("entity_states", {}) or {}
        lines = ["Operator View"]
        for side in ["home", "away"]:
            consent_side = consent.get(side, {}) or {}
            team_state = entity_states.get(side, {}) or {}
            if consent_side:
                lines.append(
                    f"{side.title()} consent | approved={consent_side.get('approved_count', 0)}/{consent_side.get('required_count', 0)} ratio={consent_side.get('approval_ratio', 0.0):.2f}"
                )
            influence_network = team_state.get("influence_network", []) or []
            if influence_network:
                top_edges = sorted(influence_network, key=lambda item: float(item.get("weight", 0.0)), reverse=True)[:3]
                lines.append(
                    f"{side.title()} top influences: " + ", ".join(
                        f"{edge['source']}->{edge['target']}:{edge['weight']:.2f}" for edge in top_edges
                    )
                )
        operator_status = regulated_session.get("operator_session_status", {}) or {}
        if operator_status:
            lines.append(
                f"Session status | consent_ready={operator_status.get('consent_ready', False)} visible_channel={operator_status.get('top_visible_channel', 'none')}"
            )
        self.operator_summary.setPlainText("\n".join(lines))

    def _render_frame(self, frame: Dict[str, object]) -> None:
        sport = normalize_sport(frame.get("sport", self._active_sport()))
        _draw_surface(self.axis, sport)
        ball = frame["ball"]
        attacker = frame["attacker"]
        keeper = frame["keeper"]
        self.axis.scatter([ball[0]], [ball[1]], [ball[2]], color="#ffffff", s=40)
        focus_spot = frame.get("focus_spot", ball)
        focus_radius = float(frame.get("focus_radius", 6.0))
        pulse = 20.0 + 10.0 * float(frame.get("reflex_intensity", 0.5))
        self.axis.scatter([focus_spot[0]], [focus_spot[1]], [focus_spot[2]], color="#ffd166", s=focus_radius * pulse, alpha=0.28)
        attacker_color = "#1f77b4" if frame["team"] == "home" else "#ff7f0e"
        attacker_key = "home_attacker" if frame["team"] == "home" else "away_attacker"
        keeper_key = "away_keeper" if frame["team"] == "home" else "home_keeper"
        attacker_profile = self.avatar_profiles.get(attacker_key, build_avatar_profile("Attacker", role="attacker"))
        keeper_profile = self.avatar_profiles.get(keeper_key, build_avatar_profile("Keeper", role="keeper"))
        _draw_avatar(self.axis, attacker, attacker_profile, attacker_color)
        _draw_avatar(self.axis, keeper, keeper_profile, "#d62728")

        trail_points = [item["ball"] for item in self.frames if item["time"] <= frame["time"]][-15:]
        if trail_points:
            xs, ys, zs = zip(*trail_points)
            self.axis.plot(xs, ys, zs, color="#ffffff", alpha=0.35)
        self.axis.set_title(
            f"{get_sport_config(sport).display_name} | Minute {frame['minute']:.1f} | Score {frame['home_score']}-{frame['away_score']} | "
            f"{frame.get('phase_state', 'transition').replace('_', ' ')} | {frame.get('primary_action', 'scan').replace('_', ' ')}"
        )
        self.figure.tight_layout()
        self.canvas.draw_idle()
        self.playhead_label.setText(f"{self._format_clock(self.current_time)} / {self._format_clock(self.match_seconds)}")
        self.score_label.setText(f"Score {frame['home_score']}-{frame['away_score']}")
        self.cue_banner.setText(
            f"Focus {frame.get('attention_focus', 'whole_field_read').replace('_', ' ')} | Window {frame.get('pressure_window', 'standard_window').replace('_', ' ')} | "
            f"Reflex {float(frame.get('reflex_intensity', 0.5)):.2f} | {frame.get('spectator_prompt', 'Track both teams.')}"
        )

    def _format_clock(self, seconds: float) -> str:
        total_seconds = max(0, int(round(seconds)))
        minutes, remainder = divmod(total_seconds, 60)
        return f"{minutes:02d}:{remainder:02d}"

    def _set_current_time(self, current_time: float) -> None:
        if not self.frames:
            return
        self.current_time = float(np.clip(current_time, 0.0, self.match_seconds))
        frame = self._frame_for_time(self.current_time)
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(int((self.current_time / max(self.match_seconds, 1e-6)) * 1000))
        self.time_slider.blockSignals(False)
        self._render_frame(frame)

    def _restart_playback(self) -> None:
        self.timer.stop()
        self.play_btn.setText("Play")
        self._set_current_time(0.0)

    def _step_frame(self, offset: int) -> None:
        if not self.frames:
            return
        self.timer.stop()
        self.play_btn.setText("Play")
        current_index = 0
        for index, frame in enumerate(self.frames):
            if frame["time"] <= self.current_time:
                current_index = index
            else:
                break
        target_index = int(np.clip(current_index + offset, 0, len(self.frames) - 1))
        self._set_current_time(float(self.frames[target_index]["time"]))

    def toggle_playback(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
            self.play_btn.setText("Play")
        else:
            self.timer.start()
            self.play_btn.setText("Pause")

    def _seek(self, value: int) -> None:
        if not self.frames:
            return
        if self.timer.isActive():
            self.timer.stop()
            self.play_btn.setText("Play")
        self._set_current_time((value / 1000.0) * self.match_seconds)

    def _frame_for_time(self, current_time: float) -> Dict[str, object]:
        for frame in reversed(self.frames):
            if frame["time"] <= current_time:
                return frame
        return self.frames[0]

    def _tick(self) -> None:
        if not self.frames:
            return
        next_time = self.current_time + self.timer.interval() / 1000.0
        if next_time > self.match_seconds:
            self.timer.stop()
            self.play_btn.setText("Play")
            next_time = self.match_seconds
        self._set_current_time(next_time)


def run_app(report_path: Optional[str] = None) -> None:
    report = None
    if report_path:
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    app = QtWidgets.QApplication(sys.argv)
    window = PlaybackWindow(report=report)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Open the DirkOdds 3D playback window for a prediction report.")
    parser.add_argument("--report", help="Path to a DirkOdds prediction report JSON")
    parsed = parser.parse_args()
    run_app(parsed.report)