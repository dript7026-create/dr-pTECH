from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "bundle"


def _relativize(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def build_game_link_manifest(game_root: Path, centerpiece_file: Path, staged_bundle_dir: Path) -> dict:
    metadata_path = staged_bundle_dir / "metadata.json"
    profile_path = staged_bundle_dir / "profile.json"
    atlas_path = staged_bundle_dir / "atlas.png"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    return {
        "game_root": str(game_root.resolve()),
        "centerpiece_source": _relativize(centerpiece_file, game_root),
        "asset_bundle_dir": _relativize(staged_bundle_dir, game_root),
        "atlas": _relativize(atlas_path, game_root),
        "metadata": _relativize(metadata_path, game_root),
        "profile": _relativize(profile_path, game_root),
        "animation": metadata.get("animation", {}),
        "designer": metadata.get("designer", {}),
        "pipeline": metadata.get("pipeline", {}),
        "engine_outputs": {
            path.name: _relativize(path, game_root)
            for path in staged_bundle_dir.glob("*.json")
            if path.name not in {"metadata.json", "profile.json"}
        },
    }


def stage_bundle_for_game(
    game_root: Path,
    centerpiece_file: Path,
    bundle_dir: Path,
    assets_subdir: str = "JumpClipAssets",
    manifest_name: str = "jumpclip_pipeline_link.json",
) -> dict:
    if not game_root.exists():
        raise FileNotFoundError(f"Game root does not exist: {game_root}")
    if not centerpiece_file.exists():
        raise FileNotFoundError(f"Centerpiece source file does not exist: {centerpiece_file}")
    if not bundle_dir.exists():
        raise FileNotFoundError(f"Bundle directory does not exist: {bundle_dir}")

    staged_bundle_dir = game_root / assets_subdir / _slugify(bundle_dir.name)
    staged_bundle_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(bundle_dir, staged_bundle_dir, dirs_exist_ok=True)

    manifest = build_game_link_manifest(game_root, centerpiece_file, staged_bundle_dir)
    manifest_path = game_root / manifest_name
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "staged_bundle_dir": staged_bundle_dir,
        "manifest_path": manifest_path,
        "manifest": manifest,
    }
