from __future__ import annotations

import argparse
import json
from pathlib import Path
import tkinter as tk

from .engine import GameEngine
from .iig import load_iig
from .orb_projection import depth_scale, lane_screen_y, parallax_screen_x, sideview_screen_y
from .ui_skin import load_ui_skin


class IllusionCanvasApp:
    def __init__(self, document: dict, game_path: Path | None = None) -> None:
        self.document = document
        self.engine = GameEngine(document)
        self.game_path = game_path
        self.ui_skin = load_ui_skin(document, game_path.parent if game_path else None)
        self.ui_images: dict[tuple[str, str], tk.PhotoImage] = {}
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
        commands = {
            "left": "left" in current,
            "right": "right" in current,
            "jump": self._just_pressed(current, "up") or self._just_pressed(current, "w"),
            "attack": self._just_pressed(current, "z"),
            "burst": self._just_pressed(current, "x"),
            "chorus_toggle": self._just_pressed(current, "c"),
            "dodge": self._just_pressed(current, "space"),
            "rescue": self._just_pressed(current, "e"),
            "rest": self._just_pressed(current, "r"),
            "bond_weave": self._just_pressed(current, "v"),
        }
        if self._just_pressed(current, "f5"):
            self._save_game()
            snapshot = self.engine.snapshot()
        elif self._just_pressed(current, "f9"):
            self._load_game()
            snapshot = self.engine.snapshot()
        else:
            snapshot = self.engine.step(commands)
        self.previous_pressed = current
        self._render(snapshot)
        self.root.after(33, self._tick)

    def _just_pressed(self, current: set[str], key: str) -> bool:
        return key in current and key not in self.previous_pressed

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
        room = snapshot["room"]

        palette_skin = self.ui_skin.get("palette", {})
        ink = palette_skin.get("ink", "#f2f4f7")
        accent = palette_skin.get("accent", "#f4cf86")
        accent_soft = palette_skin.get("accent_soft", "#a6c8f2")
        success = palette_skin.get("success", "#d8fff8")
        warning = palette_skin.get("warning", "#ffd38d")

        shell_image = self._load_image("runtime_assets", "shell_frame")
        if shell_image is not None:
            self.canvas.create_image(width // 2, height // 2, image=shell_image)

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
                f"Y {snapshot['player']['y']}"
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