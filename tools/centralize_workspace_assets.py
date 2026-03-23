from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ASSET_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tga", ".tif", ".tiff", ".webp", ".psd", ".ase", ".aseprite",
    ".kra", ".clip", ".obj", ".fbx", ".dae", ".gltf", ".glb", ".blend", ".wav", ".mp3", ".ogg", ".flac",
    ".m4a", ".aac", ".mid", ".midi", ".xm", ".mod", ".it", ".s3m", ".mp4", ".mov", ".avi", ".mkv", ".wmv",
    ".ttf", ".otf", ".woff", ".woff2", ".ico", ".icns", ".xcf", ".ecbmps",
}
SKIP_DIR_NAMES = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".copilot_bridge", ".ipynb_checkpoints",
}


@dataclass
class AssetRecord:
    source_path: Path
    relative_path: Path
    top_level: str
    category: str
    extension: str
    size: int
    sha256: str
    unique_name: str
    unique_path: Path
    project_path: Path


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_component(text: str) -> str:
    keep = []
    for char in text:
        if char.isalnum() or char in {"-", "_", "."}:
            keep.append(char)
        else:
            keep.append("_")
    return "".join(keep).strip("_") or "unnamed"


def classify_category(extension: str) -> str:
    if extension in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tga", ".tif", ".tiff", ".webp", ".ico", ".icns"}:
        return "images"
    if extension in {".psd", ".ase", ".aseprite", ".kra", ".clip", ".xcf", ".ecbmps"}:
        return "art_source"
    if extension in {".obj", ".fbx", ".dae", ".gltf", ".glb", ".blend"}:
        return "models"
    if extension in {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".mid", ".midi", ".xm", ".mod", ".it", ".s3m"}:
        return "audio"
    if extension in {".mp4", ".mov", ".avi", ".mkv", ".wmv"}:
        return "video"
    if extension in {".ttf", ".otf", ".woff", ".woff2"}:
        return "fonts"
    return "misc_media"


def collect_assets(source_root: Path) -> list[AssetRecord]:
    records: list[AssetRecord] = []
    for root, dirs, files in os.walk(source_root):
        dirs[:] = [directory for directory in dirs if directory not in SKIP_DIR_NAMES]
        root_path = Path(root)
        for file_name in files:
            source_path = root_path / file_name
            extension = source_path.suffix.lower()
            if extension not in ASSET_EXTENSIONS:
                continue
            relative_path = source_path.relative_to(source_root)
            top_level = relative_path.parts[0] if len(relative_path.parts) > 1 else "_root"
            category = classify_category(extension)
            sha256 = hash_file(source_path)
            size = source_path.stat().st_size
            unique_name = f"{sha256[:16]}__{sanitize_component(source_path.stem)}{extension}"
            records.append(
                AssetRecord(
                    source_path=source_path,
                    relative_path=relative_path,
                    top_level=top_level,
                    category=category,
                    extension=extension,
                    size=size,
                    sha256=sha256,
                    unique_name=unique_name,
                    unique_path=Path(),
                    project_path=Path(),
                )
            )
    return records


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def materialize_primary_backup(records: list[AssetRecord], primary_root: Path) -> dict:
    unique_pool = primary_root / "unique_pool"
    by_project = primary_root / "by_project"
    manifests = primary_root / "manifests"
    for directory in (unique_pool, by_project, manifests):
        directory.mkdir(parents=True, exist_ok=True)

    hash_to_unique: dict[str, Path] = {}
    duplicates: dict[str, list[str]] = defaultdict(list)
    for record in records:
        unique_dir = unique_pool / record.category
        unique_dir.mkdir(parents=True, exist_ok=True)
        project_dir = by_project / sanitize_component(record.top_level) / record.category / record.relative_path.parent
        project_dir.mkdir(parents=True, exist_ok=True)

        unique_target = hash_to_unique.get(record.sha256)
        if unique_target is None:
            unique_target = unique_dir / record.unique_name
            shutil.copy2(record.source_path, unique_target)
            hash_to_unique[record.sha256] = unique_target
        duplicates[record.sha256].append(str(record.relative_path).replace("\\", "/"))

        project_target = project_dir / record.source_path.name
        if project_target.exists():
            project_target.unlink()
        try:
            os.link(unique_target, project_target)
        except OSError:
            shutil.copy2(unique_target, project_target)

        record.unique_path = unique_target
        record.project_path = project_target

    inventory = {
        "source_root": str(primary_root),
        "asset_count": len(records),
        "unique_asset_count": len(hash_to_unique),
        "total_bytes": sum(record.size for record in records),
        "records": [
            {
                "source": str(record.source_path),
                "relative": str(record.relative_path).replace("\\", "/"),
                "top_level": record.top_level,
                "category": record.category,
                "extension": record.extension,
                "size": record.size,
                "sha256": record.sha256,
                "unique_path": str(record.unique_path),
                "project_path": str(record.project_path),
            }
            for record in records
        ],
    }
    duplicate_report = {
        "duplicate_groups": [
            {
                "sha256": sha256,
                "count": len(paths),
                "paths": paths,
            }
            for sha256, paths in duplicates.items()
            if len(paths) > 1
        ]
    }
    (manifests / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    (manifests / "duplicates.json").write_text(json.dumps(duplicate_report, indent=2) + "\n", encoding="utf-8")
    return inventory


def mirror_primary_to_secondary(primary_root: Path, secondary_root: Path) -> None:
    if secondary_root.exists():
        shutil.rmtree(secondary_root)
    shutil.copytree(primary_root, secondary_root)


def verify_backup(primary_root: Path, secondary_root: Path, expected_count: int) -> dict:
    primary_inventory = json.loads((primary_root / "manifests" / "inventory.json").read_text(encoding="utf-8"))
    secondary_inventory = json.loads((secondary_root / "manifests" / "inventory.json").read_text(encoding="utf-8"))
    if primary_inventory["asset_count"] != expected_count:
        raise RuntimeError("Primary backup inventory count mismatch.")
    if secondary_inventory["asset_count"] != expected_count:
        raise RuntimeError("Secondary backup inventory count mismatch.")
    if primary_inventory["records"] != secondary_inventory["records"]:
        raise RuntimeError("Primary and secondary backup inventories differ.")
    return primary_inventory


def delete_local_assets(records: list[AssetRecord]) -> int:
    deleted = 0
    for record in records:
        if record.source_path.exists():
            record.source_path.unlink()
            deleted += 1
    return deleted


def write_summary(dest_root: Path, summary: dict) -> None:
    summary_path = dest_root / "asset_backups" / "centralized_assets_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Centralize, mirror-backup, and optionally delete workspace asset files.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--dest-root", type=Path, required=True)
    parser.add_argument("--delete-local", action="store_true")
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    dest_root = args.dest_root.resolve()
    primary_root = dest_root / "asset_backups" / "centralized_assets_primary"
    secondary_root = dest_root / "asset_backups" / "centralized_assets_secondary"

    records = collect_assets(source_root)
    ensure_clean_dir(primary_root)
    inventory = materialize_primary_backup(records, primary_root)
    mirror_primary_to_secondary(primary_root, secondary_root)
    verified_inventory = verify_backup(primary_root, secondary_root, len(records))

    deleted = 0
    if args.delete_local:
        deleted = delete_local_assets(records)

    summary = {
        "source_root": str(source_root),
        "dest_root": str(dest_root),
        "primary_root": str(primary_root),
        "secondary_root": str(secondary_root),
        "asset_count": verified_inventory["asset_count"],
        "unique_asset_count": verified_inventory["unique_asset_count"],
        "total_bytes": verified_inventory["total_bytes"],
        "deleted_local_assets": deleted,
    }
    write_summary(dest_root, summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())