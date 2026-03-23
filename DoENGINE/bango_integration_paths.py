from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT.parent
DEFAULT_PROJECT_ROOT = WORKSPACE_ROOT / "bango-patoot_3DS"
DEFAULT_EXTERNAL_ASSET_ROOT = Path(r"E:\Bango-Patoot assets\test assets\recraft")


def resolve_bango_asset_root() -> Path:
    candidate = os.environ.get("BANGO_ASSET_ROOT")
    if candidate:
        return Path(candidate).expanduser().resolve()
    if DEFAULT_EXTERNAL_ASSET_ROOT.exists():
        return DEFAULT_EXTERNAL_ASSET_ROOT
    return DEFAULT_PROJECT_ROOT


def resolve_bango_project_root() -> Path:
    return DEFAULT_PROJECT_ROOT


def resolve_generated_root(asset_root: Path | None = None) -> Path:
    return (asset_root or resolve_bango_asset_root()) / "generated"


def resolve_clip_blend_id_dir(asset_root: Path | None = None) -> Path:
    return resolve_generated_root(asset_root) / "clip_blend_id"


def resolve_idloadint_dir(asset_root: Path | None = None) -> Path:
    return resolve_generated_root(asset_root) / "idLoadINT_bundle"


def resolve_playnow_dir(asset_root: Path | None = None) -> Path:
    return resolve_generated_root(asset_root) / "playnow"


def resolve_playnow_runtime_path(asset_root: Path | None = None) -> Path:
    return resolve_playnow_dir(asset_root) / "playnow_runtime_manifest.json"


def resolve_playnow_finalstage_path(asset_root: Path | None = None) -> Path:
    return resolve_playnow_dir(asset_root) / "playnow_finalstage_manifest.json"