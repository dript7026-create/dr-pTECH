#!/usr/bin/env python3
"""Tkinter-based NeoWakeUP control hub."""

from __future__ import annotations

import json
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from ..planetary.erpsequencer import ErpSequencer
from ..planetary.models import MODEL_PRESETS
from ..planetary.network import Directive, PlanetaryMindNetwork, PlanetaryMindStore

ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = ROOT / "assets" / "recraft"
STATE_FILE = ROOT / "state" / "planetary_mind.json"
ERP_REPORT_FILE = ROOT / "state" / "erpsequencer_report.json"
GUI_600 = ASSET_ROOT / "gui_pass_600"
GUI_300 = ASSET_ROOT / "gui_pass_300"


class ControlHubApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NeoWakeUP Control Hub")
        self.root.geometry("1380x860")
        self.network = PlanetaryMindNetwork(seed=7)
        self.store = PlanetaryMindStore(str(STATE_FILE))
        if not self.store.load_into(self.network):
            self.network.bootstrap()
            self.store.save(self.network)

        self.model_var = tk.StringVar(value="civic")
        self.prompt_var = tk.StringVar(value="Stabilize the planetary exchange network while preserving room for novelty.")
        self.novelty_var = tk.DoubleVar(value=MODEL_PRESETS["civic"]["directive"]["novelty"])
        self.equity_var = tk.DoubleVar(value=MODEL_PRESETS["civic"]["directive"]["equity"])
        self.resilience_var = tk.DoubleVar(value=MODEL_PRESETS["civic"]["directive"]["resilience"])
        self.speed_var = tk.DoubleVar(value=MODEL_PRESETS["civic"]["directive"]["speed"])
        self.erp_intoxication_var = tk.DoubleVar(value=0.42)
        self.erp_recovery_var = tk.DoubleVar(value=0.46)
        self.erp_focus_var = tk.DoubleVar(value=0.37)
        self.log_var = tk.StringVar(value="Control hub initialized.")
        self.last_erp_report = self._load_erp_report()
        self._photo_cache: dict[str, ImageTk.PhotoImage] = {}
        self._frame_index = 0
        self._assets = self._discover_assets()
        self._control_photos: dict[str, ImageTk.PhotoImage] = {}
        self._dial_labels: list[ttk.Label] = []
        self._build()
        self._refresh_graph()
        self.root.after(240, self._animate)

    def _discover_assets(self) -> dict[str, Path]:
        corrective = ASSET_ROOT / "gui_pass_300_corrective"
        corrective_v2 = ASSET_ROOT / "gui_pass_300_corrective_v2"
        dial_path = (corrective_v2 / "controls" / "dial_knob_set.png") if (corrective_v2 / "controls" / "dial_knob_set.png").exists() else ((corrective / "controls" / "dial_knob_set.png") if (corrective / "controls" / "dial_knob_set.png").exists() else (GUI_300 / "controls" / "dial_knob_set.png"))
        return {
            "panel_bg": GUI_300 / "panels" / "control_panel_background.png",
            "brand": (corrective / "branding" / "brand_mark_set.png") if (corrective / "branding" / "brand_mark_set.png").exists() else (GUI_300 / "branding" / "brand_mark_set.png"),
            "node_overlay": (corrective / "network" / "node_map_overlay.png") if (corrective / "network" / "node_map_overlay.png").exists() else (GUI_300 / "network" / "node_map_overlay.png"),
            "dial_set": dial_path,
            "slider_set": (corrective / "controls" / "slider_track_set.png") if (corrective / "controls" / "slider_track_set.png").exists() else (GUI_300 / "controls" / "slider_track_set.png"),
            "button_set": (corrective / "controls" / "button_cluster_set.png") if (corrective / "controls" / "button_cluster_set.png").exists() else (GUI_300 / "controls" / "button_cluster_set.png"),
            "planet": GUI_600 / "planet" / "planetary_mind_planet_core.png",
            "icons": GUI_600 / "icons" / "humanoid_mind_icons_set_a.png",
            "streams": GUI_600 / "network" / "network_channel_streams.png",
            "signal_sheet": GUI_600 / "network" / "signal_transfer_spritesheet.png",
            "node_sheet": GUI_600 / "network" / "node_marker_spritesheet.png",
            "font_upper": GUI_600 / "font" / "font_glyph_reference_uppercase.png",
        }

    def _open_image(self, key: str) -> Image.Image | None:
        path = self._assets.get(key)
        if path is None or not path.exists():
            return None
        return Image.open(path).convert("RGBA")

    def _get_photo(self, cache_key: str, image: Image.Image) -> ImageTk.PhotoImage:
        photo = ImageTk.PhotoImage(image)
        self._photo_cache[cache_key] = photo
        return photo

    def _fit(self, image: Image.Image, max_w: int, max_h: int) -> Image.Image:
        scale = min(max_w / max(image.width, 1), max_h / max(image.height, 1))
        scale = max(scale, 0.01)
        return image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.LANCZOS)

    def _sheet_frame(self, key: str, frame_count: int, frame_index: int) -> Image.Image | None:
        image = self._open_image(key)
        if image is None:
            return None
        frame_w = max(1, image.width // frame_count)
        left = frame_w * (frame_index % frame_count)
        return image.crop((left, 0, min(image.width, left + frame_w), image.height))

    def _split_sheet(self, key: str, count: int) -> list[Image.Image]:
        image = self._open_image(key)
        if image is None:
            return []
        frame_w = max(1, image.width // count)
        frames = []
        for index in range(count):
            left = frame_w * index
            frames.append(image.crop((left, 0, min(image.width, left + frame_w), image.height)))
        return frames

    def _grid_slice(self, key: str, columns: int, rows: int) -> list[Image.Image]:
        image = self._open_image(key)
        if image is None:
            return []
        cell_w = max(1, image.width // columns)
        cell_h = max(1, image.height // rows)
        cells = []
        for row in range(rows):
            for col in range(columns):
                left = col * cell_w
                top = row * cell_h
                cells.append(image.crop((left, top, min(image.width, left + cell_w), min(image.height, top + cell_h))))
        return cells

    def _image_button(self, parent, text: str, images: list[Image.Image], image_index: int, command) -> tk.Button:
        image = images[image_index] if image_index < len(images) else None
        photo = None
        if image is not None:
            photo = self._get_photo(f"button_img_{text}_{image_index}", self._fit(image, 72, 72))
            self._control_photos[f"button_{text}"] = photo
        btn = tk.Button(
            parent,
            text=text,
            image=photo,
            compound=tk.TOP if photo is not None else tk.NONE,
            command=command,
            bg="#12202a",
            fg="#d9ece6",
            activebackground="#203949",
            activeforeground="#f5fffc",
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=8,
        )
        return btn

    def _update_dial_labels(self) -> None:
        dial_cells = self._grid_slice("dial_set", 3, 1) or self._grid_slice("dial_set", 3, 3)
        if not dial_cells or not self._dial_labels:
            return
        vars_and_keys = [self.novelty_var, self.equity_var, self.resilience_var, self.speed_var]
        for label, var, idx in zip(self._dial_labels, vars_and_keys, range(len(self._dial_labels))):
            selector = min(len(dial_cells) - 1, int(round(var.get() * (min(3, len(dial_cells)) - 1))))
            image = self._fit(dial_cells[selector], 42, 42)
            photo = self._get_photo(f"dial_label_{idx}_{selector}", image)
            label.configure(image=photo)
            label.image = photo

    def _render_slider_preview(self, parent, label_text: str) -> None:
        slider_cells = self._grid_slice("slider_set", 3, 1) or self._grid_slice("slider_set", 3, 3)
        image = slider_cells[0] if slider_cells else None
        if image is not None:
            image = self._fit(image, 88, 24)
            photo = self._get_photo(f"slider_preview_{label_text}", image)
            ttk.Label(parent, image=photo).pack(anchor="w", pady=(0, 2))

    def _load_erp_report(self) -> dict[str, object] | None:
        if not ERP_REPORT_FILE.exists():
            return None
        try:
            return json.loads(ERP_REPORT_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def _write_erp_report(self, report: dict[str, object]) -> None:
        ERP_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        ERP_REPORT_FILE.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    def _build(self) -> None:
        self.root.configure(bg="#101820")
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=0)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        left = ttk.Frame(outer, padding=12)
        left.grid(row=0, column=0, sticky="nsw")

        brand = self._open_image("brand")
        if brand is not None:
            brand = self._fit(brand, 300, 110)
            brand_photo = self._get_photo("brand_header", brand)
            ttk.Label(left, image=brand_photo).pack(anchor="w", pady=(0, 12))

        ttk.Label(left, text="Directive Model").pack(anchor="w")
        model_box = ttk.Combobox(left, textvariable=self.model_var, values=sorted(MODEL_PRESETS.keys()), state="readonly", width=20)
        model_box.pack(fill=tk.X, pady=(4, 10))
        model_box.bind("<<ComboboxSelected>>", lambda _event: self._apply_model())

        ttk.Label(left, text="Prompt Intake").pack(anchor="w")
        ttk.Entry(left, textvariable=self.prompt_var, width=48).pack(fill=tk.X, pady=(4, 10))

        slider_frame = ttk.Frame(left)
        slider_frame.pack(fill=tk.X)
        for label, var in [
            ("Novelty", self.novelty_var),
            ("Equity", self.equity_var),
            ("Resilience", self.resilience_var),
            ("Speed", self.speed_var),
        ]:
            row = ttk.Frame(slider_frame)
            row.pack(fill=tk.X, pady=(0, 6))
            ttk.Label(row, text=label, width=10).pack(side=tk.LEFT, anchor="n")
            dial_label = ttk.Label(row)
            dial_label.pack(side=tk.LEFT, padx=(0, 6))
            self._dial_labels.append(dial_label)
            slider_holder = ttk.Frame(row)
            slider_holder.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._render_slider_preview(slider_holder, label)
            scale = tk.Scale(slider_holder, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, variable=var, length=250, bg="#101820", fg="#d9ece6", troughcolor="#274955", highlightthickness=0, command=lambda _v: self._update_dial_labels())
            scale.pack(anchor="w")

        controls = ttk.Frame(left)
        controls.pack(fill=tk.X, pady=(6, 10))
        button_cells = self._grid_slice("button_set", 3, 1) or self._grid_slice("button_set", 3, 2) or self._grid_slice("button_set", 3, 3)
        self._image_button(controls, "Step", button_cells, 0, self._step_once).pack(side=tk.LEFT)
        self._image_button(controls, "Run x12", button_cells, 1 if len(button_cells) > 1 else 0, lambda: self._run_many(12)).pack(side=tk.LEFT, padx=6)
        self._image_button(controls, "Save", button_cells, 2 if len(button_cells) > 2 else 0, self._save_state).pack(side=tk.LEFT)

        ttk.Label(left, text="ERP Sequencer").pack(anchor="w", pady=(8, 4))
        erp_frame = ttk.Frame(left)
        erp_frame.pack(fill=tk.X)
        for label, var in [
            ("Intoxication", self.erp_intoxication_var),
            ("Recovery", self.erp_recovery_var),
            ("Focus", self.erp_focus_var),
        ]:
            row = ttk.Frame(erp_frame)
            row.pack(fill=tk.X, pady=(0, 6))
            ttk.Label(row, text=label, width=10).pack(side=tk.LEFT, anchor="n")
            slider_holder = ttk.Frame(row)
            slider_holder.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._render_slider_preview(slider_holder, f"erp_{label}")
            scale = tk.Scale(slider_holder, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, variable=var, length=250, bg="#101820", fg="#d9ece6", troughcolor="#274955", highlightthickness=0)
            scale.pack(anchor="w")

        erp_controls = ttk.Frame(left)
        erp_controls.pack(fill=tk.X, pady=(2, 8))
        ttk.Button(erp_controls, text="ERP x12", command=lambda: self._run_erp(12)).pack(side=tk.LEFT)
        ttk.Button(erp_controls, text="ERP x24", command=lambda: self._run_erp(24)).pack(side=tk.LEFT, padx=6)

        ttk.Label(left, text="Status").pack(anchor="w", pady=(12, 4))
        ttk.Label(left, textvariable=self.log_var, wraplength=320, justify=tk.LEFT).pack(anchor="w")

        preview_row = ttk.Frame(left)
        preview_row.pack(anchor="w", pady=(14, 0))
        for key, size in [("dial_set", (88, 88)), ("slider_set", (88, 60)), ("button_set", (88, 88))]:
            img = self._open_image(key)
            if img is None:
                continue
            preview = self._fit(img, size[0], size[1])
            photo = self._get_photo(f"preview_{key}", preview)
            ttk.Label(preview_row, image=photo).pack(side=tk.LEFT, padx=(0, 8))
        self._update_dial_labels()

        right = ttk.Frame(outer, padding=8)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=4)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(right, bg="#0e161d", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.info = tk.Text(right, height=10, bg="#16242d", fg="#d9ece6", insertbackground="#d9ece6", relief=tk.FLAT)
        self.info.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.info.insert("1.0", "NeoWakeUP live planetary network\n")
        self.info.configure(state=tk.DISABLED)

    def _apply_model(self) -> None:
        directive = MODEL_PRESETS[self.model_var.get()]["directive"]
        self.novelty_var.set(directive["novelty"])
        self.equity_var.set(directive["equity"])
        self.resilience_var.set(directive["resilience"])
        self.speed_var.set(directive["speed"])
        self.log_var.set(f"Applied model preset: {self.model_var.get()}")
        self._update_dial_labels()

    def _directive(self) -> Directive:
        return Directive(
            novelty=float(self.novelty_var.get()),
            equity=float(self.equity_var.get()),
            resilience=float(self.resilience_var.get()),
            speed=float(self.speed_var.get()),
        )

    def _save_state(self) -> None:
        self.store.save(self.network)
        self.log_var.set(f"Saved planetary state to {STATE_FILE}")

    def _step_once(self) -> None:
        report = self.network.step(self._directive())
        self.store.save(self.network)
        self.log_var.set(f"Tick {report['tick']} coherence={report['planetary_coherence']:.3f} solution={report['solution_score']:.3f}")
        self._refresh_graph(report)
        self._update_dial_labels()

    def _run_many(self, steps: int) -> None:
        report = None
        for _ in range(steps):
            report = self.network.step(self._directive())
        self.store.save(self.network)
        if report is not None:
            self.log_var.set(f"Ran {steps} steps. Tick {report['tick']} coherence={report['planetary_coherence']:.3f}")
            self._refresh_graph(report)
            self._update_dial_labels()

    def _run_erp(self, steps: int) -> None:
        report = ErpSequencer(seed=23).sequence(
            self.network,
            steps=steps,
            intoxication=float(self.erp_intoxication_var.get()),
            recovery=float(self.erp_recovery_var.get()),
            focus=float(self.erp_focus_var.get()),
            model_name=self.model_var.get(),
        )
        self.store.save(self.network)
        self._write_erp_report(report)
        self.last_erp_report = report
        lead_name = next(iter(sorted(report["legend_counts"].items(), key=lambda item: (-item[1], item[0]))), ("none", 0))[0]
        self.log_var.set(f"ERP x{steps} generated {report['event_count']} events. Lead alias={lead_name}")
        self._refresh_graph(self.network.solve(self._directive()))

    def _refresh_graph(self, report: dict | None = None) -> None:
        if report is None:
            report = self.network.solve(self._directive())
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 900)
        height = max(self.canvas.winfo_height(), 520)
        center_x = width * 0.5
        center_y = height * 0.48

        panel_bg = self._open_image("panel_bg")
        if panel_bg is not None:
            panel_bg = panel_bg.resize((width, height), Image.LANCZOS)
            bg_photo = self._get_photo(f"panel_bg_{width}x{height}", panel_bg)
            self.canvas.create_image(0, 0, image=bg_photo, anchor=tk.NW)
        else:
            self.canvas.create_rectangle(0, 0, width, height, fill="#0e161d", outline="")

        overlay = self._open_image("node_overlay")
        if overlay is not None:
            overlay = overlay.resize((width, height), Image.LANCZOS)
            overlay_photo = self._get_photo(f"overlay_{width}x{height}", overlay)
            self.canvas.create_image(0, 0, image=overlay_photo, anchor=tk.NW)

        streams = self._open_image("streams")
        if streams is not None:
            streams = self._fit(streams, int(width * 0.74), int(height * 0.64))
            streams_photo = self._get_photo(f"streams_{width}x{height}", streams)
            self.canvas.create_image(center_x, center_y, image=streams_photo)

        planet = self._open_image("planet")
        if planet is not None:
            planet = self._fit(planet, 250, 250)
            planet_photo = self._get_photo("planet_core", planet)
            self.canvas.create_image(center_x, center_y, image=planet_photo)
        else:
            planet_radius = 108
            self.canvas.create_oval(center_x - planet_radius, center_y - planet_radius, center_x + planet_radius, center_y + planet_radius, fill="#1c5968", outline="#8ad2d9", width=3)
            self.canvas.create_oval(center_x - 84, center_y - 84, center_x + 84, center_y + 84, outline="#d7fffb", width=2)
        self.canvas.create_text(center_x, center_y, text=f"Planetary\nCoherence\n{report['planetary_coherence']:.3f}", fill="#e5fff8", font=("Segoe UI", 16, "bold"), justify=tk.CENTER)

        region_items = list(report["regions"].items())[:6]
        orbit = 235
        icon_frames = self._split_sheet("icons", 5)
        node_marker = self._sheet_frame("node_sheet", 8, self._frame_index)
        if node_marker is not None:
            node_marker = self._fit(node_marker, 28, 28)
        signal_frame = self._sheet_frame("signal_sheet", 8, self._frame_index)
        if signal_frame is not None:
            signal_frame = self._fit(signal_frame, 92, 28)
        for index, (region_id, region_data) in enumerate(region_items):
            angle = (index / max(len(region_items), 1)) * (math.pi * 2.0)
            rx = center_x + orbit * math.cos(angle)
            ry = center_y + orbit * math.sin(angle)
            color = "#a5ff9f" if region_data["coherence"] > 0.62 else "#ffd37d"
            self.canvas.create_line(center_x, center_y, rx, ry, fill="#3f7f89", width=2)
            if signal_frame is not None:
                signal_photo = self._get_photo(f"signal_{index}_{self._frame_index}", signal_frame)
                mid_x = (center_x + rx) / 2.0
                mid_y = (center_y + ry) / 2.0
                self.canvas.create_image(mid_x, mid_y, image=signal_photo)
            icon_image = None
            if icon_frames:
                icon_image = self._fit(icon_frames[index % len(icon_frames)], 68, 68)
            if icon_image is not None:
                icon_photo = self._get_photo(f"icon_{index}", icon_image)
                self.canvas.create_image(rx, ry, image=icon_photo)
            else:
                self.canvas.create_oval(rx - 26, ry - 26, rx + 26, ry + 26, fill="#162b35", outline=color, width=3)
            if node_marker is not None and region_data["coherence"] > 0.55:
                marker_photo = self._get_photo(f"marker_{index}_{self._frame_index}", node_marker)
                self.canvas.create_image(rx + 26, ry - 28, image=marker_photo)
            self.canvas.create_text(rx, ry + 42, text=region_id.split("-")[-1], fill="#f2fff8", font=("Segoe UI", 10, "bold"))
            for sub_index in range(5):
                sx = rx + (sub_index - 2) * 22
                sy = ry + 54
                active = (sub_index / 5.0) < region_data["coherence"]
                self.canvas.create_oval(sx - 8, sy - 8, sx + 8, sy + 8, fill="#8cf7d2" if active else "#253841", outline="")

        text = {
            "prompt": self.prompt_var.get(),
            "directive": report["directive"],
            "planetary_coherence": report["planetary_coherence"],
            "exchange": report["exchange"],
            "volatility": report["volatility"],
            "solution_score": report["solution_score"],
            "asset_manifests": [
                str(ASSET_ROOT / "neowakeup_gui_pass_600_manifest.json"),
                str(ASSET_ROOT / "neowakeup_gui_pass_300_manifest.json"),
            ],
        }
        if self.last_erp_report is not None:
            text["erpsequencer"] = {
                "model": self.last_erp_report.get("model"),
                "steps": self.last_erp_report.get("steps"),
                "event_count": self.last_erp_report.get("event_count"),
                "band_counts": self.last_erp_report.get("band_counts"),
                "legend_counts": self.last_erp_report.get("legend_counts"),
            }
        self.info.configure(state=tk.NORMAL)
        self.info.delete("1.0", tk.END)
        self.info.insert("1.0", json.dumps(text, indent=2))
        self.info.configure(state=tk.DISABLED)

    def _animate(self) -> None:
        self._frame_index = (self._frame_index + 1) % 8
        self._refresh_graph()
        self.root.after(240, self._animate)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    ControlHubApp(root)
    root.mainloop()