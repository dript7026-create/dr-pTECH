from __future__ import annotations

import json
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .integration import stage_bundle_for_game
from .models import RenderRequest
from .pipeline import export_game_bundle, load_pipeline_config, resolve_render_scale
from .render import apply_motion_overrides, infer_animation_spec, load_profile_input, render_frames

ART_PRESETS = ["", "retro-arcade", "snes-rpg", "hd2d-rpg", "cel-brawler", "space-shooter", "soulslike-action"]
STYLE_FAMILIES = ["", "8bit", "16bit", "hd2d", "bitmap-traced", "cel-shaded-2.5d"]
ANIMATIONS = ["run cycle", "attack combo", "jump arc", "idle"]


class JumpClipShell(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("JumpClip Shell")
        self.geometry("1040x780")
        self.minsize(960, 720)

        self.game_root_var = tk.StringVar()
        self.centerpiece_var = tk.StringVar()
        self.profile_var = tk.StringVar()
        self.pipeline_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.assets_subdir_var = tk.StringVar(value="JumpClipAssets")
        self.character_var = tk.StringVar(value="lantern courier")
        self.animation_var = tk.StringVar(value="run cycle")
        self.prompt_var = tk.StringVar(value="readable courier silhouette")
        self.art_preset_var = tk.StringVar(value="retro-arcade")
        self.style_family_var = tk.StringVar()

        self.optional_vars: dict[str, tk.StringVar] = {
            "grid_size": tk.StringVar(value="12"),
            "canvas_size": tk.StringVar(),
            "upscale": tk.StringVar(),
            "silhouette_emphasis": tk.StringVar(),
            "texture_detail": tk.StringVar(),
            "palette_limit": tk.StringVar(),
            "cel_shading": tk.StringVar(),
            "outline_weight": tk.StringVar(),
            "accessory_density": tk.StringVar(),
            "tracing_bias": tk.StringVar(),
            "motion_silhouette_bias": tk.StringVar(),
            "motion_squash_stretch": tk.StringVar(),
            "motion_impact": tk.StringVar(),
            "motion_lift": tk.StringVar(),
        }

        self.status_var = tk.StringVar(value="Ready.")
        self.log = tk.Text(self, height=14, wrap="word", state="disabled")
        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        title = ttk.Label(root, text="JumpClip Game Shell", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w")
        subtitle = ttk.Label(root, text="Select a game root, its centerpiece source file, and generate pipeline-ready assets into the project.")
        subtitle.pack(anchor="w", pady=(0, 12))

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        integration_tab = ttk.Frame(notebook, padding=12)
        visual_tab = ttk.Frame(notebook, padding=12)
        motion_tab = ttk.Frame(notebook, padding=12)
        notebook.add(integration_tab, text="Integration")
        notebook.add(visual_tab, text="Visual")
        notebook.add(motion_tab, text="Motion")

        self._build_integration_tab(integration_tab)
        self._build_visual_tab(visual_tab)
        self._build_motion_tab(motion_tab)

        action_row = ttk.Frame(root)
        action_row.pack(fill="x", pady=(12, 8))
        ttk.Button(action_row, text="Generate + Link To Game", command=self.generate_and_link).pack(side="left")
        ttk.Button(action_row, text="Clear Log", command=self.clear_log).pack(side="left", padx=(8, 0))
        ttk.Label(action_row, textvariable=self.status_var).pack(side="right")

        self.log.pack(in_=root, fill="both", expand=False)

    def _build_integration_tab(self, frame: ttk.Frame) -> None:
        self._path_row(frame, 0, "Game Root", self.game_root_var, lambda: self._choose_directory(self.game_root_var))
        self._path_row(frame, 1, "Centerpiece Source", self.centerpiece_var, lambda: self._choose_file(self.centerpiece_var))
        self._path_row(frame, 2, "Profile Or Manifest", self.profile_var, lambda: self._choose_file(self.profile_var))
        self._path_row(frame, 3, "Pipeline Config", self.pipeline_var, lambda: self._choose_file(self.pipeline_var))
        self._path_row(frame, 4, "Output Bundle Dir", self.output_var, lambda: self._choose_directory(self.output_var))
        self._entry_row(frame, 5, "Asset Subdir", self.assets_subdir_var)
        self._entry_row(frame, 6, "Character", self.character_var)

        ttk.Label(frame, text="Animation").grid(row=7, column=0, sticky="w", pady=6)
        ttk.Combobox(frame, textvariable=self.animation_var, values=ANIMATIONS, state="readonly").grid(row=7, column=1, sticky="ew", padx=(8, 8))

        ttk.Label(frame, text="Prompt").grid(row=8, column=0, sticky="nw", pady=6)
        prompt_entry = tk.Text(frame, height=5, wrap="word")
        prompt_entry.insert("1.0", self.prompt_var.get())
        prompt_entry.grid(row=8, column=1, columnspan=2, sticky="nsew", padx=(8, 0))
        frame.rowconfigure(8, weight=1)
        frame.columnconfigure(1, weight=1)

        def sync_prompt(*_: object) -> None:
            self.prompt_var.set(prompt_entry.get("1.0", "end").strip())

        prompt_entry.bind("<KeyRelease>", sync_prompt)

    def _build_visual_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(1, weight=1)
        self._combo_row(frame, 0, "Art Preset", self.art_preset_var, ART_PRESETS)
        self._combo_row(frame, 1, "Style Family", self.style_family_var, STYLE_FAMILIES)
        self._entry_row(frame, 2, "Grid Size", self.optional_vars["grid_size"])
        self._entry_row(frame, 3, "Canvas Size", self.optional_vars["canvas_size"])
        self._entry_row(frame, 4, "Upscale", self.optional_vars["upscale"])
        self._entry_row(frame, 5, "Silhouette Emphasis", self.optional_vars["silhouette_emphasis"])
        self._entry_row(frame, 6, "Texture Detail", self.optional_vars["texture_detail"])
        self._entry_row(frame, 7, "Palette Limit", self.optional_vars["palette_limit"])
        self._entry_row(frame, 8, "Cel Shading", self.optional_vars["cel_shading"])
        self._entry_row(frame, 9, "Outline Weight", self.optional_vars["outline_weight"])
        self._entry_row(frame, 10, "Accessory Density", self.optional_vars["accessory_density"])
        self._entry_row(frame, 11, "Tracing Bias", self.optional_vars["tracing_bias"])

    def _build_motion_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(1, weight=1)
        self._entry_row(frame, 0, "Motion Silhouette Bias", self.optional_vars["motion_silhouette_bias"])
        self._entry_row(frame, 1, "Motion Squash Stretch", self.optional_vars["motion_squash_stretch"])
        self._entry_row(frame, 2, "Motion Impact", self.optional_vars["motion_impact"])
        self._entry_row(frame, 3, "Motion Lift", self.optional_vars["motion_lift"])

        help_text = (
            "Use motion controls when a move needs different staging from the base preset. "
            "Higher impact and squash values push attacks harder; higher lift helps jump arcs and hover-like motion."
        )
        ttk.Label(frame, text=help_text, wraplength=720).grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def _path_row(self, frame: ttk.Frame, row: int, label: str, var: tk.StringVar, browse_command) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=var).grid(row=row, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(frame, text="Browse", command=browse_command).grid(row=row, column=2, sticky="ew")
        frame.columnconfigure(1, weight=1)

    def _entry_row(self, frame: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=var).grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8, 0))

    def _combo_row(self, frame: ttk.Frame, row: int, label: str, var: tk.StringVar, values: list[str]) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Combobox(frame, textvariable=var, values=values).grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8, 0))

    def _choose_directory(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def _choose_file(self, var: tk.StringVar) -> None:
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def _optional_float(self, name: str) -> float | None:
        value = self.optional_vars[name].get().strip()
        return float(value) if value else None

    def _optional_int(self, name: str) -> int | None:
        value = self.optional_vars[name].get().strip()
        return int(value) if value else None

    def _append_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", f"{message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def generate_and_link(self) -> None:
        try:
            game_root = Path(self.game_root_var.get()).expanduser().resolve()
            centerpiece = Path(self.centerpiece_var.get()).expanduser().resolve()
            profile_source = Path(self.profile_var.get()).expanduser().resolve()
            pipeline_path = Path(self.pipeline_var.get()).expanduser().resolve() if self.pipeline_var.get().strip() else None
            output_dir = Path(self.output_var.get()).expanduser().resolve() if self.output_var.get().strip() else game_root / ".jumpclip-build" / self.character_var.get().replace(" ", "_")
            assets_subdir = self.assets_subdir_var.get().strip() or "JumpClipAssets"
            prompt = self.prompt_var.get().strip()
            if not all([game_root, centerpiece, profile_source, prompt]):
                raise ValueError("Game root, centerpiece source, profile/manifest, and prompt are required")

            profile = load_profile_input(
                profile_source,
                grid_size=self._optional_int("grid_size") or 12,
                download_dir=None,
            )
            config = load_pipeline_config(pipeline_path)
            animation = apply_motion_overrides(
                infer_animation_spec(self.animation_var.get()),
                {
                    "silhouette_bias": self._optional_float("motion_silhouette_bias"),
                    "squash_stretch": self._optional_float("motion_squash_stretch"),
                    "impact": self._optional_float("motion_impact"),
                    "lift_scale": self._optional_float("motion_lift"),
                },
            )
            canvas_size, upscale = resolve_render_scale(
                config,
                requested_canvas_size=self._optional_int("canvas_size"),
                requested_upscale=self._optional_int("upscale"),
            )
            request = RenderRequest(
                character=self.character_var.get().strip(),
                prompt=prompt,
                animation=animation,
                canvas_size=canvas_size,
                upscale=upscale,
                output_path=output_dir,
                art_preset=self.art_preset_var.get().strip() or None,
                style_family=self.style_family_var.get().strip() or None,
                silhouette_emphasis=self._optional_float("silhouette_emphasis"),
                texture_detail=self._optional_float("texture_detail"),
                palette_limit=self._optional_int("palette_limit"),
                cel_shading=self._optional_float("cel_shading"),
                outline_weight=self._optional_float("outline_weight"),
                accessory_density=self._optional_float("accessory_density"),
                tracing_bias=self._optional_float("tracing_bias"),
                motion_silhouette_bias=self._optional_float("motion_silhouette_bias"),
                motion_squash_stretch=self._optional_float("motion_squash_stretch"),
                motion_impact=self._optional_float("motion_impact"),
                motion_lift=self._optional_float("motion_lift"),
            )
            frames = render_frames(request, profile)
            bundle = export_game_bundle(request, profile, config, frames, output_dir)
            staging = stage_bundle_for_game(game_root, centerpiece, output_dir, assets_subdir=assets_subdir)

            self.status_var.set("Bundle generated and linked.")
            self._append_log(json.dumps(
                {
                    "bundle_dir": str(bundle["bundle_dir"]),
                    "manifest_path": str(staging["manifest_path"]),
                    "centerpiece_source": staging["manifest"]["centerpiece_source"],
                    "asset_bundle_dir": staging["manifest"]["asset_bundle_dir"],
                },
                indent=2,
            ))
            messagebox.showinfo("JumpClip Shell", f"Assets linked into game project.\nManifest: {staging['manifest_path']}")
        except Exception as exc:
            self.status_var.set("Generation failed.")
            self._append_log(str(exc))
            self._append_log(traceback.format_exc())
            messagebox.showerror("JumpClip Shell", str(exc))


def main() -> None:
    app = JumpClipShell()
    app.mainloop()


if __name__ == "__main__":
    main()
