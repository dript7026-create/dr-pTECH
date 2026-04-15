from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
DOENGINE_APPS = WORKSPACE_ROOT / "DoENGINE" / "apps"
for candidate in (ROOT, WORKSPACE_ROOT, DOENGINE_APPS):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

try:
    from dodo_engine3d import DODO_SHADER_MANIFEST, DodoPseudo3DEngine
except Exception:
    DODO_SHADER_MANIFEST = None
    DodoPseudo3DEngine = None


CONFIG_DIR = ROOT / "config"
DEFAULT_CONTRACT_PATH = CONFIG_DIR / "homelair_runtime_contract.json"
DEFAULT_PROFILES_PATH = CONFIG_DIR / "runtime_profiles.json"
DEFAULT_SCENE_PATH = ROOT / "assets" / "scenes" / "homeviuplay_depth_lair.scene.json"
GENERATED_DIR = ROOT / "generated"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_profiles() -> list[dict]:
    payload = load_json(DEFAULT_PROFILES_PATH)
    if not isinstance(payload, list):
        raise ValueError("runtime_profiles.json must contain a list")
    return payload


def load_contract() -> dict:
    payload = load_json(DEFAULT_CONTRACT_PATH)
    if not isinstance(payload, dict):
        raise ValueError("homelair_runtime_contract.json must contain an object")
    return payload


def load_scene_manifest(path: Path) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"scene manifest must contain an object: {path}")
    return payload


def select_profile(profile_id: str | None) -> dict:
    profiles = load_profiles()
    if profile_id is None:
        return profiles[0]
    for profile in profiles:
        if profile.get("profile_id") == profile_id:
            return profile
    known = ", ".join(str(profile.get("profile_id")) for profile in profiles)
    raise ValueError(f"unknown profile_id '{profile_id}'. known profiles: {known}")


def resolve_profile_scene(profile: dict) -> Path:
    raw_scene = profile.get("scene_manifest")
    if not raw_scene:
        return DEFAULT_SCENE_PATH
    scene_path = Path(str(raw_scene))
    if not scene_path.is_absolute():
        scene_path = (ROOT / scene_path).resolve()
    return scene_path


def build_runtime_bundle(profile_id: str | None = None, scene_manifest_path: Path | None = None) -> dict:
    profile = select_profile(profile_id)
    scene_path = scene_manifest_path or resolve_profile_scene(profile)
    scene_manifest = load_scene_manifest(scene_path)
    contract = load_contract()
    return {
        "schema": "homelair_manifest_bundle/v1",
        "shell": contract["shell"],
        "runtime_contract": contract,
        "profile": profile,
        "scene_manifest_path": str(scene_path),
        "scene_manifest": scene_manifest,
        "render_backend": DODO_SHADER_MANIFEST if DODO_SHADER_MANIFEST is not None else {"status": "unavailable"},
    }


def render_preview(output_path: Path, profile_id: str | None = None, scene_manifest_path: Path | None = None) -> dict:
    if DodoPseudo3DEngine is None:
        raise RuntimeError("DodoPseudo3DEngine is unavailable; cannot render preview.")
    bundle = build_runtime_bundle(profile_id=profile_id, scene_manifest_path=scene_manifest_path)
    profile = bundle["profile"]
    render_profile = profile.get("render_profile", {})
    scene_path = Path(bundle["scene_manifest_path"])
    engine = DodoPseudo3DEngine(width=640, height=360, scene_manifest_path=scene_path)
    payload = engine.write_preview(
        output_path,
        orbit=bundle["scene_manifest"].get("camera", {}).get("orbit", 0.62),
        elevation=bundle["scene_manifest"].get("camera", {}).get("elevation", 0.2),
        shader_mix=render_profile.get("shader_mix", 0.85),
        time_s=1.35,
        scene_manifest_path=scene_path,
    )
    return {
        "bundle": bundle,
        "preview": payload,
    }


class HOMElairShellApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("HOMElair Shell")
        self.root.geometry("980x720")
        self.profile_var = tk.StringVar()
        self.scene_var = tk.StringVar(value=str(DEFAULT_SCENE_PATH))
        self.status_var = tk.StringVar(value="Ready")
        self.profiles = load_profiles()
        self.profile_var.set(str(self.profiles[0]["profile_id"]))
        self.scene_var.set(str(resolve_profile_scene(self.profiles[0])))

        controls = ttk.Frame(self.root, padding=12)
        controls.pack(fill="x")
        ttk.Label(controls, text="Profile").pack(side="left")
        ttk.Combobox(
            controls,
            textvariable=self.profile_var,
            values=[str(profile["profile_id"]) for profile in self.profiles],
            state="readonly",
            width=32,
        ).pack(side="left", padx=(8, 18))
        self.profile_var.trace_add("write", self._on_profile_change)
        ttk.Label(controls, text="Scene").pack(side="left")
        ttk.Entry(controls, textvariable=self.scene_var, width=56).pack(side="left", padx=(8, 12), fill="x", expand=True)
        ttk.Button(controls, text="Refresh Bundle", command=self.refresh_bundle).pack(side="left")
        ttk.Button(controls, text="Render Preview", command=self.write_preview).pack(side="left", padx=(8, 0))

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.bundle_text = tk.Text(notebook, wrap="none")
        self.render_text = tk.Text(notebook, wrap="none")
        notebook.add(self.bundle_text, text="Runtime Bundle")
        notebook.add(self.render_text, text="Render Preview")

        ttk.Label(self.root, textvariable=self.status_var, padding=(12, 0, 12, 12)).pack(fill="x")
        self.refresh_bundle()

    def _bundle(self) -> dict:
        scene_path = Path(self.scene_var.get()).resolve()
        return build_runtime_bundle(profile_id=self.profile_var.get(), scene_manifest_path=scene_path)

    def _write_text(self, widget: tk.Text, payload: object) -> None:
        widget.delete("1.0", tk.END)
        widget.insert("1.0", json.dumps(payload, indent=2))

    def refresh_bundle(self) -> None:
        bundle = self._bundle()
        self._write_text(self.bundle_text, bundle)
        self.status_var.set(f"Loaded {bundle['profile']['label']}")

    def _on_profile_change(self, *_args: object) -> None:
        try:
            profile = select_profile(self.profile_var.get())
        except ValueError:
            return
        self.scene_var.set(str(resolve_profile_scene(profile)))

    def write_preview(self) -> None:
        output_path = GENERATED_DIR / f"{self.profile_var.get()}_preview.png"
        payload = render_preview(output_path, profile_id=self.profile_var.get(), scene_manifest_path=Path(self.scene_var.get()).resolve())
        self._write_text(self.render_text, payload)
        self.status_var.set(f"Preview written to {output_path}")

    def run(self) -> None:
        self.root.mainloop()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HOMElair shell scaffold")
    parser.add_argument("--profile", help="Profile id from config/runtime_profiles.json")
    parser.add_argument("--scene-manifest", type=Path)
    parser.add_argument("--dump-bundle", action="store_true", help="Print the merged runtime bundle and exit")
    parser.add_argument("--dump-profiles", action="store_true", help="Print the available runtime profiles and exit")
    parser.add_argument("--render-preview", type=Path, help="Write a preview image and companion JSON report")
    parser.add_argument("--ui", action="store_true", help="Launch the Tk shell UI")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    scene_manifest = args.scene_manifest.resolve() if args.scene_manifest is not None else None
    if args.dump_profiles:
        print(json.dumps(load_profiles(), indent=2))
        return 0
    if args.dump_bundle:
        print(json.dumps(build_runtime_bundle(profile_id=args.profile, scene_manifest_path=scene_manifest), indent=2))
        return 0
    if args.render_preview:
        payload = render_preview(args.render_preview.resolve(), profile_id=args.profile, scene_manifest_path=scene_manifest)
        print(json.dumps(payload, indent=2))
        return 0
    app = HOMElairShellApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())