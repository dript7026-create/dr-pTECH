"""Helpers for reading ClipConceptBook (.ccp) containers and translating them to Recraft manifests."""

from __future__ import annotations

import json
import struct
from pathlib import Path

CCP_HEADER_STRUCT = struct.Struct("<4sIIQQ")
CCP_MAGIC = b"CCP1"


def read_ccp(ccp_path: str | Path) -> dict:
    path = Path(ccp_path)
    with path.open("rb") as handle:
        header = handle.read(CCP_HEADER_STRUCT.size)
        if len(header) != CCP_HEADER_STRUCT.size:
            raise ValueError(f"{path} is too small to be a .ccp file")
        magic, version, page_count, manifest_size, source_zip_size = CCP_HEADER_STRUCT.unpack(header)
        if magic != CCP_MAGIC:
            raise ValueError(f"{path} does not start with the CCP1 magic header")
        manifest_bytes = handle.read(manifest_size)
        if len(manifest_bytes) != manifest_size:
            raise ValueError(f"{path} is truncated; missing manifest payload")
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        manifest["_ccp"] = {
            "path": str(path),
            "version": version,
            "page_count": page_count,
            "source_zip_size": source_zip_size,
        }
        return manifest


def _page_prompt(page: dict, prompt_map: dict, title: str, book_mode: str) -> str:
    page_number = page.get("page")
    clip_name = page.get("clip", f"pg{page_number}.clip")
    page_key = f"pg{page_number}"
    page_meta = prompt_map.get(page_key, {}) if isinstance(prompt_map, dict) else {}
    description = page_meta.get("description") or page_meta.get("prompt") or f"ClipConceptBook page {page_number} from {title}"
    visual_tags = page_meta.get("visual_tags") or []
    if isinstance(visual_tags, list) and visual_tags:
        description = f"{description}. Visual tags: {', '.join(str(tag) for tag in visual_tags)}"
    return f"{description}. Source page: {clip_name}. Book mode: {book_mode}. Preserve transparent background and production-ready sprite-sheet readability where applicable."


def ccp_to_manifest(ccp_path: str | Path, output_dir: str | Path | None = None, default_w: int = 1024, default_h: int = 1024) -> list[dict]:
    manifest = read_ccp(ccp_path)
    output_root = Path(output_dir) if output_dir else Path(ccp_path).with_suffix("")
    prompt_map = manifest.get("prompt_map", {})
    title = manifest.get("title", "ClipConceptBook")
    book_mode = manifest.get("book_mode", "interactive")
    items: list[dict] = []

    for page in manifest.get("pages", []):
        page_number = int(page.get("page", 0))
        page_key = f"pg{page_number}"
        page_meta = prompt_map.get(page_key, {}) if isinstance(prompt_map, dict) else {}
        width = int(page_meta.get("w", default_w))
        height = int(page_meta.get("h", default_h))
        out_name = page_meta.get("out") or f"{page_key}.png"
        item = {
            "name": page_meta.get("name") or page_key,
            "prompt": _page_prompt(page, prompt_map, title, book_mode),
            "w": width,
            "h": height,
            "out": str((output_root / out_name).resolve()),
            "transparent_background": True,
            "source_ccp": str(ccp_path),
            "source_page": page.get("clip"),
        }
        if "negative_prompt" in page_meta:
            item["negative_prompt"] = page_meta["negative_prompt"]
        if "style" in page_meta:
            item["style"] = page_meta["style"]
        if "style_id" in page_meta:
            item["style_id"] = page_meta["style_id"]
        if "model" in page_meta:
            item["model"] = page_meta["model"]
        if "controls" in page_meta:
            item["controls"] = page_meta["controls"]
        items.append(item)

    return items