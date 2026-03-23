from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


DEFAULT_UI_SKIN = {
    "theme_name": "IllusionCanvas Default",
    "palette": {
        "sky": "#13233d",
        "ground": "#1f1d2b",
        "floor": "#2d3642",
        "panel": "#162033",
        "panel_alt": "#0b111a",
        "ink": "#f2f4f7",
        "accent": "#f4cf86",
        "accent_soft": "#a6c8f2",
        "success": "#d8fff8",
        "warning": "#ffd38d",
    },
    "runtime_assets": {},
    "studio_assets": {},
    "popup_templates": {},
    "font_atlases": {},
}


def load_ui_skin(document: dict, base_path: str | Path | None = None) -> dict:
    skin = deepcopy(DEFAULT_UI_SKIN)
    ui_block = document.get("ui", {})
    manifest_path = ui_block.get("skin_manifest")
    resolved_manifest: Path | None = None
    if manifest_path:
        resolved_manifest = _resolve_path(manifest_path, base_path)
        if resolved_manifest.exists():
            loaded = json.loads(resolved_manifest.read_text(encoding="utf-8"))
            _merge_dicts(skin, loaded)
            _resolve_asset_tree(skin, resolved_manifest.parent)
    _merge_dicts(skin, {key: value for key, value in ui_block.items() if key != "skin_manifest"})
    if base_path is not None:
        _resolve_asset_tree(skin, Path(base_path))
    if resolved_manifest is not None:
        skin["skin_manifest"] = str(resolved_manifest)
    return skin


def _resolve_path(value: str, base_path: str | Path | None) -> Path:
    path = Path(value)
    if path.is_absolute() or base_path is None:
        return path
    return (Path(base_path) / path).resolve()


def _merge_dicts(target: dict, incoming: dict) -> None:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_dicts(target[key], value)
        else:
            target[key] = value


def _resolve_asset_tree(node, base_dir: Path) -> None:
    if isinstance(node, dict):
        if "path" in node and isinstance(node["path"], str):
            path = Path(node["path"])
            if not path.is_absolute():
                node["path"] = str((base_dir / path).resolve())
        for value in node.values():
            _resolve_asset_tree(value, base_dir)
    elif isinstance(node, list):
        for value in node:
            _resolve_asset_tree(value, base_dir)