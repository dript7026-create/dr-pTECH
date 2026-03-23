from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from .iig import load_iig, save_iig
from .ui_skin import load_ui_skin


class IllusionCanvasStudio:
    def __init__(self, initial_path: str | Path) -> None:
        self.path = Path(initial_path)
        self.document = load_iig(self.path)
        self.ui_skin = load_ui_skin(self.document, self.path.parent)
        self.ui_images: dict[str, tk.PhotoImage] = {}
        self.root = tk.Tk()
        self.root.title(self.ui_skin.get("theme_name", "IllusionCanvasInteractive Studio"))
        self.root.geometry("1280x820")
        self.root.configure(bg=self.ui_skin["palette"].get("panel_alt", "#0b111a"))

        toolbar = tk.Frame(self.root, bg=self.ui_skin["palette"].get("panel", "#162033"))
        toolbar.pack(fill=tk.X)
        button_kwargs = {
            "bg": self.ui_skin["palette"].get("accent", "#f4cf86"),
            "fg": "#151515",
            "activebackground": self.ui_skin["palette"].get("warning", "#ffd38d"),
        }
        tk.Button(toolbar, text="Open", command=self.open_file, **button_kwargs).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="Save", command=self.save_file, **button_kwargs).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="Save As", command=self.save_file_as, **button_kwargs).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="Run", command=self.run_preview, **button_kwargs).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="Add Room", command=self.add_room, **button_kwargs).pack(side=tk.LEFT, padx=4, pady=4)

        body = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RIDGE)
        body.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(body, bg=self.ui_skin["palette"].get("panel", "#101827"))
        center = tk.Frame(body, bg=self.ui_skin["palette"].get("panel_alt", "#0c1422"))
        right = tk.Frame(body, bg=self.ui_skin["palette"].get("panel_alt", "#0b111a"))
        body.add(left, width=260)
        body.add(center, width=520)
        body.add(right, width=420)

        self.room_list = tk.Listbox(left)
        self.room_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.room_list.bind("<<ListboxSelect>>", self.on_room_select)

        metadata_box = tk.LabelFrame(center, text="Metadata")
        metadata_box.pack(fill=tk.X, padx=8, pady=8)
        self.title_var = tk.StringVar()
        self.goal_var = tk.StringVar()
        tk.Label(metadata_box, text="Title").grid(row=0, column=0, sticky="w")
        tk.Entry(metadata_box, textvariable=self.title_var, width=60).grid(row=0, column=1, sticky="ew")
        tk.Label(metadata_box, text="Experience Goal").grid(row=1, column=0, sticky="w")
        tk.Entry(metadata_box, textvariable=self.goal_var, width=60).grid(row=1, column=1, sticky="ew")
        metadata_box.grid_columnconfigure(1, weight=1)

        room_box = tk.LabelFrame(center, text="Selected Room")
        room_box.pack(fill=tk.X, padx=8, pady=8)
        self.room_id_var = tk.StringVar()
        self.room_name_var = tk.StringVar()
        self.room_danger_var = tk.StringVar()
        self.room_objective_var = tk.StringVar()
        tk.Label(room_box, text="ID").grid(row=0, column=0, sticky="w")
        tk.Entry(room_box, textvariable=self.room_id_var, width=42).grid(row=0, column=1, sticky="ew")
        tk.Label(room_box, text="Name").grid(row=1, column=0, sticky="w")
        tk.Entry(room_box, textvariable=self.room_name_var, width=42).grid(row=1, column=1, sticky="ew")
        tk.Label(room_box, text="Danger").grid(row=2, column=0, sticky="w")
        tk.Entry(room_box, textvariable=self.room_danger_var, width=8).grid(row=2, column=1, sticky="w")
        tk.Label(room_box, text="Objective").grid(row=3, column=0, sticky="nw")
        self.room_objective_text = tk.Text(room_box, height=5, width=60)
        self.room_objective_text.grid(row=3, column=1, sticky="ew")
        room_box.grid_columnconfigure(1, weight=1)

        pet_box = tk.LabelFrame(center, text="Loadout")
        pet_box.pack(fill=tk.X, padx=8, pady=8)
        self.burst_var = tk.StringVar()
        self.chorus_var = tk.StringVar()
        tk.Label(pet_box, text="Burst").grid(row=0, column=0, sticky="w")
        tk.Entry(pet_box, textvariable=self.burst_var, width=32).grid(row=0, column=1, sticky="ew")
        tk.Label(pet_box, text="Chorus").grid(row=1, column=0, sticky="w")
        tk.Entry(pet_box, textvariable=self.chorus_var, width=32).grid(row=1, column=1, sticky="ew")
        pet_box.grid_columnconfigure(1, weight=1)

        theme_preview = self._load_image("studio_assets", "header_frame")
        if theme_preview is not None:
            tk.Label(right, image=theme_preview, bg=self.ui_skin["palette"].get("panel_alt", "#0b111a")).pack(fill=tk.X, padx=8, pady=8)
        else:
            tk.Label(
                right,
                text=f"Theme: {self.ui_skin.get('theme_name', 'IllusionCanvas Studio')}",
                bg=self.ui_skin["palette"].get("panel_alt", "#0b111a"),
                fg=self.ui_skin["palette"].get("ink", "#dce6f4"),
                anchor="w",
            ).pack(fill=tk.X, padx=8, pady=(8, 0))
        tk.Label(right, text="JSON Preview", bg=self.ui_skin["palette"].get("panel_alt", "#0b111a"), fg="#dce6f4", anchor="w").pack(fill=tk.X, padx=8, pady=(0, 0))
        self.asset_summary = tk.Label(right, text="", bg=self.ui_skin["palette"].get("panel_alt", "#0b111a"), fg="#d8fff8", anchor="w", justify=tk.LEFT)
        self.asset_summary.pack(fill=tk.X, padx=8, pady=(4, 0))
        self.preview = tk.Text(right, wrap="none")
        self.preview.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.current_room_index = 0
        self.refresh_from_document()

    def _load_image(self, collection: str, key: str) -> tk.PhotoImage | None:
        entry = self.ui_skin.get(collection, {}).get(key)
        if not entry:
            return None
        if isinstance(entry, str):
            entry = {"path": entry}
        cache_key = f"{collection}:{key}"
        if cache_key in self.ui_images:
            return self.ui_images[cache_key]
        path = Path(entry.get("path", ""))
        if not path.exists():
            return None
        image = tk.PhotoImage(file=str(path))
        subsample = max(1, int(entry.get("subsample", 1)))
        if subsample > 1:
            image = image.subsample(subsample, subsample)
        self.ui_images[cache_key] = image
        return image

    def refresh_from_document(self) -> None:
        self.title_var.set(self.document["metadata"].get("title", ""))
        self.goal_var.set(self.document["metadata"].get("experience_goal", ""))
        self.burst_var.set(self.document["player"]["loadout"].get("burst", ""))
        self.chorus_var.set(self.document["player"]["loadout"].get("chorus", ""))
        self.room_list.delete(0, tk.END)
        for room in self.document["world"]["rooms"]:
            self.room_list.insert(tk.END, f"{room['id']}  |  {room['name']}")
        if self.document["world"]["rooms"]:
            self.current_room_index = min(self.current_room_index, len(self.document["world"]["rooms"]) - 1)
            self.room_list.selection_clear(0, tk.END)
            self.room_list.selection_set(self.current_room_index)
            self._load_room(self.current_room_index)
        popup_names = ", ".join(sorted(self.ui_skin.get("popup_templates", {}).keys())) or "none"
        font_names = ", ".join(sorted(self.ui_skin.get("font_atlases", {}).keys())) or "none"
        self.asset_summary.config(text=f"Popup shells: {popup_names}\nFont atlases: {font_names}")
        self._refresh_preview()

    def _load_room(self, index: int) -> None:
        room = self.document["world"]["rooms"][index]
        self.room_id_var.set(room.get("id", ""))
        self.room_name_var.set(room.get("name", ""))
        self.room_danger_var.set(str(room.get("danger", 0)))
        self.room_objective_text.delete("1.0", tk.END)
        self.room_objective_text.insert("1.0", room.get("objective", ""))

    def _apply_form_to_document(self) -> None:
        self.document["metadata"]["title"] = self.title_var.get().strip()
        self.document["metadata"]["experience_goal"] = self.goal_var.get().strip()
        self.document["player"]["loadout"]["burst"] = self.burst_var.get().strip()
        self.document["player"]["loadout"]["chorus"] = self.chorus_var.get().strip()
        rooms = self.document["world"]["rooms"]
        if rooms:
            room = rooms[self.current_room_index]
            room["id"] = self.room_id_var.get().strip()
            room["name"] = self.room_name_var.get().strip()
            try:
                room["danger"] = int(self.room_danger_var.get().strip() or "0")
            except ValueError:
                room["danger"] = 0
            room["objective"] = self.room_objective_text.get("1.0", tk.END).strip()

    def _refresh_preview(self) -> None:
        import json

        self.preview.delete("1.0", tk.END)
        self.preview.insert("1.0", json.dumps(self.document, indent=2))

    def on_room_select(self, _event=None) -> None:
        selection = self.room_list.curselection()
        if not selection:
            return
        self._apply_form_to_document()
        self.current_room_index = int(selection[0])
        self._load_room(self.current_room_index)
        self._refresh_preview()

    def add_room(self) -> None:
        self._apply_form_to_document()
        new_room = {
            "id": f"new_room_{len(self.document['world']['rooms']) + 1:02d}",
            "name": "New Room",
            "safe_room": False,
            "danger": 1,
            "objective": "Author the new route objective.",
            "palette": ["#22314a", "#3d5c78", "#d89d66"],
            "parallax": [],
            "exits": {},
            "enemies": [],
        }
        self.document["world"]["rooms"].append(new_room)
        self.current_room_index = len(self.document["world"]["rooms"]) - 1
        self.refresh_from_document()

    def open_file(self) -> None:
        chosen = filedialog.askopenfilename(filetypes=[("Illusion Interactive Game", "*.iig"), ("JSON", "*.json")])
        if not chosen:
            return
        self.path = Path(chosen)
        self.document = load_iig(self.path)
        self.ui_skin = load_ui_skin(self.document, self.path.parent)
        self.ui_images.clear()
        self.current_room_index = 0
        self.refresh_from_document()

    def save_file(self) -> None:
        self._apply_form_to_document()
        save_iig(self.document, self.path)
        self._refresh_preview()
        messagebox.showinfo("IllusionCanvas Studio", f"Saved {self.path}")

    def save_file_as(self) -> None:
        self._apply_form_to_document()
        chosen = filedialog.asksaveasfilename(defaultextension=".iig", filetypes=[("Illusion Interactive Game", "*.iig")])
        if not chosen:
            return
        self.path = Path(chosen)
        save_iig(self.document, self.path)
        self._refresh_preview()
        messagebox.showinfo("IllusionCanvas Studio", f"Saved {self.path}")

    def run_preview(self) -> None:
        self._apply_form_to_document()
        temp_path = self.path
        save_iig(self.document, temp_path)
        runtime = Path(__file__).resolve().parents[1] / "run_illusioncanvas.py"
        subprocess.Popen([sys.executable, str(runtime), str(temp_path)], start_new_session=True)

    def run(self) -> int:
        self.root.mainloop()
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run IllusionCanvasInteractive Studio")
    parser.add_argument("game", nargs="?", default=str(Path(__file__).resolve().parents[1] / "sample_games" / "aridfeihth_vertical_slice.iig"))
    args = parser.parse_args(argv)
    studio = IllusionCanvasStudio(args.game)
    return studio.run()