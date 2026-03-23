from __future__ import annotations

from collections import Counter
from copy import deepcopy


BUCKET_MAP = {
    "character_sheet": "actors",
    "animation_pack": "actors",
    "environment_set": "spaces",
    "animated_environment_object": "spaces",
    "apiary_sheet": "spaces",
    "hud_pack": "interface",
    "combat_fx": "effects",
    "environmental_fx": "effects",
    "item_pack": "equipment",
    "item_unique": "equipment",
    "weapon_pack": "equipment",
    "ammunition_pack": "equipment",
    "armor_set": "equipment",
    "pipeline_calibration": "diagnostics",
}


def classify_runtime_bucket(category: str) -> str:
    return BUCKET_MAP.get(category, "misc")


def build_illusioncanvas_runtime_manifest(source_manifest: dict) -> dict:
    runtime_assets = []
    bucket_counts: Counter[str] = Counter()
    for asset in source_manifest.get("assets", []):
        if "illusioncanvas" not in asset.get("pipeline_targets", []):
            continue
        bucket = classify_runtime_bucket(asset["category"])
        bucket_counts[bucket] += 1
        protocol = asset.get("protocol", {})
        runtime_assets.append(
            {
                "asset_id": asset["name"],
                "bucket": bucket,
                "category": asset["category"],
                "source_path": asset["out"],
                "generation_mode": asset.get("generation_mode", "packed_master"),
                "derived_outputs": protocol.get("derived_outputs", []),
                "hybrid_render_role": _render_role(asset["category"]),
                "projection_profile": {
                    "layout": protocol.get("layout", "packed_reference_sheet"),
                    "angle_positions": protocol.get("angle_positions", {}),
                },
            }
        )
    return {
        "runtime_name": "IllusionCanvasInteractive",
        "runtime_version": "2026-03-13.prototype",
        "asset_count": len(runtime_assets),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "assets": runtime_assets,
    }


def enrich_iig_document(
    document: dict,
    runtime_manifest: dict,
    source_manifest_path: str,
    runtime_manifest_path: str,
    ui_skin_path: str | None = None,
) -> dict:
    enriched = deepcopy(document)
    enriched["automation"] = {
        "profile": "clip_blend_id_do_illusioncanvas",
        "source_manifest": source_manifest_path,
        "runtime_manifest": runtime_manifest_path,
        "asset_count": runtime_manifest["asset_count"],
        "bucket_counts": runtime_manifest["bucket_counts"],
    }
    if ui_skin_path:
        enriched.setdefault("ui", {})["skin_manifest"] = ui_skin_path
        enriched["automation"]["ui_skin_manifest"] = ui_skin_path
    return enriched


def _render_role(category: str) -> str:
    if category in {"character_sheet", "animation_pack"}:
        return "sprite_actor"
    if category in {"environment_set", "animated_environment_object", "apiary_sheet"}:
        return "pseudo3d_plane"
    if category in {"hud_pack"}:
        return "overlay"
    if category in {"combat_fx", "environmental_fx"}:
        return "atmosphere"
    return "support"