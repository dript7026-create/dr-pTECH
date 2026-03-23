import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog

from .data_loader import build_fixture_feature_row, load_csv, prepare_training_frame
from .challenge_mode import build_challenge_cue_profile
from .model import (
    evolutionary_search_and_train,
    export_model,
    load_model,
    predict_matches,
    train_model,
)
from .playback import PlaybackWindow
from .simulation import simulate_match
from .sports import get_sport_config, normalize_sport


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DirkOdds")
        self.resize(980, 720)

        layout = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel("DirkOdds")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        subtitle = QtWidgets.QLabel(
            "Team-vs-team match probabilities for football, baseball, and basketball with explicit uncertainty. DirkOdds is a decision-support tool, not a guarantee engine."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        sport_row = QtWidgets.QHBoxLayout()
        sport_row.addWidget(QtWidgets.QLabel("Sport"))
        self.sport_combo = QtWidgets.QComboBox()
        self.sport_combo.addItem("Football", "football")
        self.sport_combo.addItem("Baseball", "baseball")
        self.sport_combo.addItem("Basketball", "basketball")
        self.sport_combo.currentIndexChanged.connect(self._on_sport_changed)
        sport_row.addWidget(self.sport_combo)
        sport_row.addStretch(1)
        layout.addLayout(sport_row)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setStyleSheet(
            "padding: 8px 10px; background: #1f2933; color: #f5f7fa; border-radius: 6px;"
        )
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        button_row = QtWidgets.QHBoxLayout()

        self.load_btn = QtWidgets.QPushButton("Load Match CSV")
        self.load_btn.clicked.connect(self.load_csv)
        button_row.addWidget(self.load_btn)

        self.load_model_btn = QtWidgets.QPushButton("Load Saved Model")
        self.load_model_btn.clicked.connect(self.load_saved_model)
        button_row.addWidget(self.load_model_btn)

        self.info_label = QtWidgets.QLabel("No dataset loaded.")
        self.info_label.setWordWrap(True)

        self.train_btn = QtWidgets.QPushButton("Train DirkOdds")
        self.train_btn.clicked.connect(self.train_model)
        self.train_btn.setEnabled(False)
        button_row.addWidget(self.train_btn)

        self.evolve_btn = QtWidgets.QPushButton("Evolve Hyperparameters")
        self.evolve_btn.clicked.connect(self.evolve)
        self.evolve_btn.setEnabled(False)
        button_row.addWidget(self.evolve_btn)

        self.export_btn = QtWidgets.QPushButton("Export Model")
        self.export_btn.clicked.connect(self.export_model)
        self.export_btn.setEnabled(False)
        button_row.addWidget(self.export_btn)

        self.plot_btn = QtWidgets.QPushButton("Plot Sample Predictions")
        self.plot_btn.clicked.connect(self.plot_predictions)
        self.plot_btn.setEnabled(False)
        button_row.addWidget(self.plot_btn)

        self.predict_btn = QtWidgets.QPushButton("Predict Recent Matches")
        self.predict_btn.clicked.connect(self.predict_rows)
        self.predict_btn.setEnabled(False)
        button_row.addWidget(self.predict_btn)

        layout.addLayout(button_row)

        fixture_group = QtWidgets.QGroupBox("Upcoming Fixture")
        fixture_layout = QtWidgets.QFormLayout(fixture_group)
        self.home_team_combo = QtWidgets.QComboBox()
        self.away_team_combo = QtWidgets.QComboBox()
        self.match_date_edit = QtWidgets.QDateEdit()
        self.match_date_edit.setCalendarPopup(True)
        self.match_date_edit.setDate(QDate.currentDate().addDays(7))
        self.swap_teams_btn = QtWidgets.QPushButton("Swap Teams")
        self.swap_teams_btn.clicked.connect(self.swap_teams)
        self.predict_fixture_btn = QtWidgets.QPushButton("Predict Fixture")
        self.predict_fixture_btn.clicked.connect(self.predict_fixture)
        self.predict_fixture_btn.setEnabled(False)
        self.challenge_mode_checkbox = QtWidgets.QCheckBox("Hide Exact Accuracy")
        self.challenge_mode_checkbox.setChecked(True)
        self.playback_fixture_btn = QtWidgets.QPushButton("3D Fixture Playback")
        self.playback_fixture_btn.clicked.connect(self.open_fixture_playback)
        self.playback_fixture_btn.setEnabled(False)
        self.live_render_btn = QtWidgets.QPushButton("Live 3D Match View")
        self.live_render_btn.clicked.connect(self.open_live_render)
        self.live_render_btn.setEnabled(False)
        fixture_layout.addRow("Home team", self.home_team_combo)
        fixture_layout.addRow("Away team", self.away_team_combo)
        fixture_layout.addRow("Match date", self.match_date_edit)
        fixture_layout.addRow(self.swap_teams_btn)
        fixture_layout.addRow(self.challenge_mode_checkbox)
        fixture_layout.addRow(self.predict_fixture_btn)
        fixture_layout.addRow(self.playback_fixture_btn)
        fixture_layout.addRow(self.live_render_btn)
        layout.addWidget(fixture_group)

        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)

        layout.addWidget(self.info_label)
        layout.addWidget(self.text)

        self.figure = Figure(figsize=(6, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.raw_df = None
        self.df = None
        self.model = None
        self._evo_worker = None
        self._playback_window = None
        self._live_render_process = None
        self._update_status_banner()

    def _selected_sport(self) -> str:
        return normalize_sport(self.sport_combo.currentData())

    def _active_sport(self) -> str:
        if self.model is not None:
            return normalize_sport(getattr(self.model, "sport", self._selected_sport()))
        return self._selected_sport()

    def _update_playback_availability(self) -> None:
        enabled = self.model is not None and self.raw_df is not None
        self.playback_fixture_btn.setEnabled(enabled)
        self.live_render_btn.setEnabled(enabled)
        self._update_status_banner()

    def _update_status_banner(self) -> None:
        sport = get_sport_config(self._active_sport() if self.model is not None else self._selected_sport())
        model_name = getattr(self.model, "model_name", "No model loaded") if self.model is not None else "No model loaded"
        dataset_state = f"{len(self.raw_df)} games loaded" if self.raw_df is not None else "No dataset loaded"
        playback_state = "Playback ready" if self.playback_fixture_btn.isEnabled() else "Playback unavailable"
        self.status_label.setText(
            f"Sport: {sport.display_name} | Dataset: {dataset_state} | Model: {model_name} | {playback_state} | Live render {'ready' if self.live_render_btn.isEnabled() else 'unavailable'}"
        )
        self.playback_fixture_btn.setText(f"3D {sport.display_name} Playback")
        self.live_render_btn.setText(f"Live {sport.display_name} Match View")

    def _on_sport_changed(self) -> None:
        sport = get_sport_config(self._selected_sport()).display_name
        self.text.appendPlainText(f"Sport set to {sport}.")
        self._update_playback_availability()

    def _set_team_choices(self):
        if self.raw_df is None:
            return
        teams = sorted(set(self.raw_df["home_team"].astype(str)).union(set(self.raw_df["away_team"].astype(str))))
        self.home_team_combo.clear()
        self.away_team_combo.clear()
        self.home_team_combo.addItems(teams)
        self.away_team_combo.addItems(teams)
        if len(teams) > 1:
            self.away_team_combo.setCurrentIndex(1)

    def swap_teams(self) -> None:
        home_index = self.home_team_combo.currentIndex()
        away_index = self.away_team_combo.currentIndex()
        if home_index < 0 or away_index < 0:
            return
        self.home_team_combo.setCurrentIndex(away_index)
        self.away_team_combo.setCurrentIndex(home_index)

    def _append_metrics(self, prefix, metrics):
        parts = []
        for key, value in metrics.items():
            if isinstance(value, float):
                parts.append(f"{key}={value:.4f}")
            else:
                parts.append(f"{key}={value}")
        self.text.appendPlainText(f"{prefix}: " + ", ".join(parts))

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", filter="CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        try:
            sport = self._selected_sport()
            raw_df = load_csv(path, sport=sport)
            df = prepare_training_frame(raw_df, window=5, sport=sport)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {e}")
            return
        self.raw_df = raw_df
        self.df = df

        self._set_team_choices()
        team_count = len(set(raw_df["home_team"].astype(str)).union(set(raw_df["away_team"].astype(str))))
        sport_name = get_sport_config(self._selected_sport()).display_name
        self.info_label.setText(
            f"Loaded {len(raw_df)} {sport_name.lower()} games across {team_count} teams. Engineered {len(df.columns)} columns with pre-match form, points, rest, and experience features."
        )
        self.text.appendPlainText(f"Loaded dataset: {path}")
        self.train_btn.setEnabled(True)
        self.evolve_btn.setEnabled(True)
        self.predict_fixture_btn.setEnabled(self.model is not None)
        self._update_playback_availability()
        self._update_status_banner()

    def train_model(self):
        if self.df is None:
            return
        try:
            clf, metrics = train_model(self.df, sport=self._selected_sport())
        except Exception as e:
            QMessageBox.critical(self, "Train Error", str(e))
            return
        self.model = clf
        self._append_metrics(f"Model trained ({clf.model_name})", metrics)
        self.predict_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.plot_btn.setEnabled(True)
        self.predict_fixture_btn.setEnabled(True)
        self._update_playback_availability()
        self._update_status_banner()

    def predict_rows(self):
        if self.model is None or self.df is None:
            return
        sample = self.df.tail(5)
        sport = self._active_sport()
        allows_draws = get_sport_config(sport).allows_draws
        try:
            predictions = predict_matches(self.model, sample, sport=sport)
        except Exception as e:
            QMessageBox.critical(self, "Predict Error", str(e))
            return
        self.text.appendPlainText("Recent match probability snapshot:")
        for row in predictions.itertuples():
            if self.challenge_mode_checkbox.isChecked():
                cues = build_challenge_cue_profile(pd.Series(row._asdict()))
                self.text.appendPlainText(
                    f"{row.home_team} vs {row.away_team}: pick={row.prediction}, signal={cues['visible_label']}, pressure={cues['pressure_label']}, timing={cues['timing_window_label']}"
                )
            else:
                probability_text = (
                    f"away={row.prob_away_win:.2f}, draw={row.prob_draw:.2f}, home={row.prob_home_win:.2f}"
                    if allows_draws
                    else f"away={row.prob_away_win:.2f}, home={row.prob_home_win:.2f}"
                )
                self.text.appendPlainText(f"{row.home_team} vs {row.away_team}: {probability_text}, pick={row.prediction}, confidence={row.confidence:.2f}, uncertainty={row.uncertainty:.2f}")

    def predict_fixture(self):
        if self.model is None or self.raw_df is None:
            return
        home_team = self.home_team_combo.currentText().strip()
        away_team = self.away_team_combo.currentText().strip()
        if not home_team or not away_team:
            return
        if home_team == away_team:
            QMessageBox.warning(self, "Fixture Error", "Home and away teams must be different.")
            return
        match_date = self.match_date_edit.date().toString("yyyy-MM-dd")
        sport = self._active_sport()
        allows_draws = get_sport_config(sport).allows_draws
        try:
            fixture_df = build_fixture_feature_row(self.raw_df, home_team, away_team, match_date=match_date, sport=sport)
            prediction = predict_matches(self.model, fixture_df, sport=sport).iloc[0]
        except Exception as e:
            QMessageBox.critical(self, "Fixture Error", str(e))
            return
        if self.challenge_mode_checkbox.isChecked():
            cues = build_challenge_cue_profile(prediction)
            self.text.appendPlainText(
                f"Upcoming fixture {home_team} vs {away_team} on {match_date}: pick={prediction['prediction']}, signal={cues['visible_label']}, pressure={cues['pressure_label']}, timing={cues['timing_window_label']}, rhythm={cues['rhythm_label']}"
            )
        else:
            probability_text = (
                f"away={prediction['prob_away_win']:.2f}, draw={prediction['prob_draw']:.2f}, home={prediction['prob_home_win']:.2f}"
                if allows_draws
                else f"away={prediction['prob_away_win']:.2f}, home={prediction['prob_home_win']:.2f}"
            )
            self.text.appendPlainText(f"Upcoming fixture {home_team} vs {away_team} on {match_date}: {probability_text}, pick={prediction['prediction']}, confidence={prediction['confidence']:.2f}, entropy={prediction['entropy']:.2f}")

    def evolve(self):
        if self.df is None:
            return
        self.text.appendPlainText("Starting evolutionary hyperparameter search in the background...")

        self.progress = QProgressDialog("Evolving hyperparameters...", "Cancel", 0, 0, self)
        self.progress.setWindowModality(QtCore.Qt.WindowModal)
        self.progress.setMinimumDuration(100)
        self.progress.setValue(0)
        self.progress.show()

        # Worker thread to run evolution
        class EvoWorker(QtCore.QThread):
            finished = QtCore.Signal(object, object)

            def __init__(self, df, ngen, pop_size):
                super().__init__()
                self.df = df
                self.ngen = ngen
                self.pop_size = pop_size

            def run(self):
                try:
                    clf, info = evolutionary_search_and_train(self.df, ngen=self.ngen, pop_size=self.pop_size, sport=self.df.iloc[0].get("sport", "football"))
                except Exception as e:
                    self.finished.emit(None, {"error": str(e)})
                    return
                self.finished.emit(clf, info)

        self._evo_worker = EvoWorker(self.df, ngen=10, pop_size=18)
        self._evo_worker.finished.connect(self._on_evo_finished)
        self._evo_worker.start()

    def _on_evo_finished(self, clf, info):
        try:
            self.progress.close()
        except Exception:
            pass
        if clf is None:
            self.text.appendPlainText(f"Evolution failed: {info.get('error')}")
            QMessageBox.critical(self, "Evolve Error", info.get("error", "Unknown"))
            return
        self.model = clf
        self.text.appendPlainText(f"Evolution finished — best params: {info.get('best_params')}")
        self._append_metrics("Evolved model metrics", info.get("metrics", {}))
        self.predict_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.plot_btn.setEnabled(True)
        self.predict_fixture_btn.setEnabled(True)
        self._update_playback_availability()
        self._update_status_banner()

    def load_saved_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open model", filter="Joblib Files (*.joblib);;All Files (*)")
        if not path:
            return
        try:
            self.model = load_model(path)
        except Exception as e:
            QMessageBox.critical(self, "Load Model Error", str(e))
            return
        self.text.appendPlainText(f"Loaded saved model: {path}")
        self._append_metrics(f"Loaded model ({self.model.model_name})", self.model.metrics)
        model_sport = normalize_sport(getattr(self.model, "sport", self._selected_sport()))
        self.sport_combo.setCurrentIndex(self.sport_combo.findData(model_sport))
        self.predict_btn.setEnabled(self.df is not None)
        self.export_btn.setEnabled(True)
        self.plot_btn.setEnabled(self.df is not None)
        self.predict_fixture_btn.setEnabled(self.raw_df is not None)
        self._update_playback_availability()
        self._update_status_banner()

    def export_model(self):
        if self.model is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save model", filter="Joblib Files (*.joblib);;All Files (*)")
        if not path:
            return
        try:
            export_model(self.model, path)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
            return
        self.text.appendPlainText(f"Model exported to: {path}")

    def plot_predictions(self):
        if self.model is None or self.df is None:
            return
        sample = self.df.tail(8)
        sport = self._active_sport()
        try:
            predictions = predict_matches(self.model, sample, sport=sport)
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))
            return
        labels = [f"{getattr(r,'home_team','home')} vs {getattr(r,'away_team','away')}" for r in predictions.itertuples()]
        probs = predictions[["prob_away_win", "prob_draw", "prob_home_win"]].to_numpy()
        x = np.arange(len(labels))
        width = 0.25

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.bar(x - width, probs[:, 0], width, label='away win')
        ax.bar(x, probs[:, 1], width, label='draw')
        ax.bar(x + width, probs[:, 2], width, label='home win')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_ylim(0.0, 1.0)
        ax.set_ylabel('Probability')
        ax.set_title('DirkOdds prediction profile')
        ax.legend()
        self.figure.tight_layout()
        self.canvas.draw()

    def open_fixture_playback(self):
        if self.model is None or self.raw_df is None:
            return
        home_team = self.home_team_combo.currentText().strip()
        away_team = self.away_team_combo.currentText().strip()
        if not home_team or not away_team or home_team == away_team:
            QMessageBox.warning(self, "Playback Error", "Choose two different teams first.")
            return
        match_date = self.match_date_edit.date().toString("yyyy-MM-dd")
        try:
            sport = self._active_sport()
            fixture_df = build_fixture_feature_row(self.raw_df, home_team, away_team, match_date=match_date, sport=sport)
            prediction = predict_matches(self.model, fixture_df, sport=sport)
            simulation = simulate_match(prediction.iloc[0])
        except Exception as e:
            QMessageBox.critical(self, "Playback Error", str(e))
            return
        report = {"predictions": prediction.to_dict(orient="records"), "simulations": [simulation]}
        self._playback_window = PlaybackWindow(report=report)
        self._playback_window.show()

    def open_live_render(self):
        if self.model is None or self.raw_df is None:
            return
        home_team = self.home_team_combo.currentText().strip()
        away_team = self.away_team_combo.currentText().strip()
        if not home_team or not away_team or home_team == away_team:
            QMessageBox.warning(self, "Live Render Error", "Choose two different teams first.")
            return
        match_date = self.match_date_edit.date().toString("yyyy-MM-dd")
        try:
            sport = self._active_sport()
            fixture_df = build_fixture_feature_row(self.raw_df, home_team, away_team, match_date=match_date, sport=sport)
            prediction = predict_matches(self.model, fixture_df, sport=sport)
            simulation = simulate_match(prediction.iloc[0])
        except Exception as e:
            QMessageBox.critical(self, "Live Render Error", str(e))
            return
        report = {"predictions": prediction.to_dict(orient="records"), "simulations": [simulation]}
        temp_dir = Path(tempfile.gettempdir())
        safe_name = f"dirkodds_live_render_{sport}_{home_team}_{away_team}".replace(" ", "_").replace("/", "-")
        report_path = temp_dir / f"{safe_name}.json"
        report_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        env = os.environ.copy()
        project_root = str(Path(__file__).resolve().parent.parent)
        env["PYTHONPATH"] = project_root if not env.get("PYTHONPATH") else project_root + os.pathsep + env["PYTHONPATH"]
        self._live_render_process = subprocess.Popen(
            [sys.executable, "-m", "football_predictor.live_render", "--report", str(report_path)],
            cwd=project_root,
            env=env,
        )


def run_app():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
