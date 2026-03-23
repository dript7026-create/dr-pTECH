from __future__ import annotations

import os
from pathlib import Path


DEFAULT_EXTERNAL_ASSET_ROOT = Path(r"E:\Bango-Patoot assets\test assets\recraft")


def resolve_asset_root(project_root: Path) -> Path:
    configured = os.environ.get("BANGO_ASSET_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    if Path("E:\\").exists():
        return DEFAULT_EXTERNAL_ASSET_ROOT
    return project_root.resolve()


def manifest_output_root(asset_root: Path) -> str:
    return str(asset_root)
