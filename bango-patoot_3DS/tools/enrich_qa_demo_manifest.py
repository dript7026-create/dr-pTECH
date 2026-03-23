from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "recraft" / "bango_patoot_qa_demo_manifest.json"
DEFAULT_RECON_SPEC = ROOT / "recraft" / "bango_patoot_qa_demo_3d_reconstruction_spec.json"
DEFAULT_RIGS = ROOT / "rigs" / "entity_rigs.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_size_pair(text: str) -> tuple[int, int] | None:
    match = re.search(r"(\d+)x(\d+)", text)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def infer_runtime_size(asset: dict, manifest: dict) -> tuple[int, int] | None:
    runtime_target = asset.get("runtime_target", "")
    parsed = parse_size_pair(runtime_target)
    if parsed:
        return parsed

    category = asset.get("category", "")
    contract = manifest.get("runtime_export_contract", {})
    mapping = {
        "player": contract.get("standard_character"),
        "companion": contract.get("standard_character"),
        "npc": contract.get("standard_npc"),
        "enemy": contract.get("standard_enemy"),
        "enemy_elite": contract.get("elite_or_boss"),
        "boss": contract.get("elite_or_boss"),
    }
    fallback = mapping.get(category)
    return parse_size_pair(fallback or "")


def infer_entity_name(asset_name: str) -> str | None:
    lowered = asset_name.lower()
    if lowered.startswith("bango_"):
        return "Bango"
    if lowered.startswith("patoot_"):
        return "Patoot"
    return None


def infer_baseline_anchor(asset: dict) -> str:
    name = asset["name"]
    category = asset["category"]
    if "hurt" in name or "fall" in name:
        return "feet or body center when airborne"
    if category == "ui":
        return "screen space"
    if category == "fx":
        return "effect origin"
    return "feet"


def infer_integration_role(asset: dict) -> list[str]:
    category = asset["category"]
    name = asset["name"]
    roles = {
        "player": ["runtime sprite source", "animation keypose source", "rig reference", "mesh blockout reference"],
        "companion": ["runtime sprite source", "animation keypose source", "rig reference", "mesh blockout reference"],
        "npc": ["runtime sprite source", "portrait source", "rig reference", "mesh blockout reference"],
        "enemy": ["runtime sprite source", "combat keypose source", "rig reference", "mesh blockout reference"],
        "enemy_elite": ["runtime sprite source", "combat keypose source", "rig reference", "mesh blockout reference"],
        "boss": ["runtime sprite source", "boss keypose source", "rig reference", "mesh blockout reference"],
        "world": ["modular kit source", "environment mesh blockout reference", "surface-material source"],
        "interactable": ["prop sprite source", "collision proxy reference", "mesh blockout reference"],
        "wildlife": ["runtime sprite source", "ambient actor reference", "mesh blockout reference"],
        "fx": ["runtime effect source", "billboard source", "emissive mask source"],
        "ui": ["screen-space source", "slice source", "QA reference source"],
    }[category][:]
    if "turnaround" in name and "billboard source" not in roles:
        roles.insert(1, "billboard source")
    return roles


def infer_review_focus(asset: dict) -> list[str]:
    category = asset["category"]
    name = asset["name"]
    if category in {"player", "companion"}:
        base = ["baseline lock", "silhouette readability", "joint clarity", "material separation"]
        if "turnaround" in name:
            base.insert(0, "turnaround consistency")
        if "melee" in name or "attack" in name:
            base.extend(["anticipation", "contact pose clarity"])
        if "glide" in name:
            base.append("wing or lift readability")
        return base
    if category in {"enemy", "enemy_elite", "boss"}:
        return ["hostile silhouette readability", "attack-source clarity", "hitbox planning", "weak-point readability"]
    if category == "npc":
        return ["portrait crop readability", "stance readability", "costume layering", "face clarity"]
    if category in {"world", "interactable"}:
        return ["modular seam safety", "collision readability", "material separation", "repeat-safe boundaries"]
    if category == "wildlife":
        return ["non-hostile versus hostile readability", "small-scale silhouette clarity", "downsample stability"]
    if category == "fx":
        return ["emissive readability", "effect origin clarity", "downsample readability"]
    return ["screen readability", "slice readability", "contrast safety"]


def infer_cell_layout(asset: dict) -> str:
    w = int(asset["w"])
    h = int(asset["h"])
    category = asset["category"]
    runtime_target = asset.get("runtime_target", "")
    if "4 angles" in runtime_target:
        return f"4x1, {w // 4}x{h} per cell"
    if "6 frames" in runtime_target:
        return f"6x1, {w // 6}x{h} per cell"
    if "portrait crop" in runtime_target:
        return f"3x1, {w // 3}x{h} per cell"
    if category in {"world", "interactable"} and w == 1536 and h == 1536:
        return "6x6, 256x256 per cell"
    if category == "wildlife" and w == 1024 and h == 1024:
        return "4x4, 256x256 per cell"
    if category == "fx" and w == 1536 and h == 768:
        return "6x3, 256x256 per cell"
    return "manual free-layout master"


def make_cells(prefix: str, cols: int, rows: int, export_size: tuple[int, int], labels: list[str] | None = None) -> list[dict]:
    cells: list[dict] = []
    index = 0
    for row in range(rows):
        for col in range(cols):
            label = labels[index] if labels and index < len(labels) else f"{prefix}_{index:02d}"
            cells.append({
                "name": label,
                "row": row,
                "col": col,
                "exports": [{"name": label, "mode": "fit", "size": list(export_size)}],
            })
            index += 1
    return cells


def infer_slice_plan(asset: dict, export_size: tuple[int, int] | None) -> dict:
    w = int(asset["w"])
    h = int(asset["h"])
    runtime_target = asset.get("runtime_target", "")
    category = asset["category"]
    name = asset["name"]

    if export_size and "4 angles" in runtime_target:
        return {
            "mode": "uniform-grid",
            "grid": {"cols": 4, "rows": 1, "cell_width": w // 4, "cell_height": h},
            "cells": make_cells(name, 4, 1, export_size, ["front", "left", "right", "rear"]),
        }

    if export_size and "6 frames" in runtime_target:
        return {
            "mode": "uniform-grid",
            "grid": {"cols": 6, "rows": 1, "cell_width": w // 6, "cell_height": h},
            "cells": make_cells(name, 6, 1, export_size),
        }

    if "portrait crop" in runtime_target:
        standee_size = export_size or (24, 36)
        cells = []
        for index in range(3):
            label = f"pose_{index:02d}"
            cells.append({
                "name": label,
                "row": 0,
                "col": index,
                "exports": [
                    {"name": f"{label}_standee", "mode": "fit", "size": [standee_size[0], standee_size[1]]},
                    {"name": f"{label}_portrait", "mode": "alpha_square_portrait", "size": [96, 96]},
                ],
            })
        return {
            "mode": "uniform-grid",
            "grid": {"cols": 3, "rows": 1, "cell_width": w // 3, "cell_height": h},
            "cells": cells,
        }

    if category in {"world", "interactable"} and w == 1536 and h == 1536:
        return {
            "mode": "uniform-grid-auto",
            "grid": {"cols": 6, "rows": 6, "cell_width": 256, "cell_height": 256},
            "auto_exports": [
                {"name": "raw", "mode": "raw"},
                {"name": "tile_24x24", "mode": "fit", "size": [24, 24]},
                {"name": "prop_24x36", "mode": "fit", "size": [24, 36]},
                {"name": "large_48x48", "mode": "fit", "size": [48, 48]},
            ],
        }

    if category == "interactable" and w == 1024 and h == 1024:
        return {
            "mode": "uniform-grid-auto",
            "grid": {"cols": 4, "rows": 4, "cell_width": 256, "cell_height": 256},
            "auto_exports": [
                {"name": "raw", "mode": "raw"},
                {"name": "small_16x16", "mode": "fit", "size": [16, 16]},
                {"name": "medium_24x24", "mode": "fit", "size": [24, 24]},
                {"name": "actor_24x36", "mode": "fit", "size": [24, 36]},
            ],
        }

    if category == "wildlife" and w == 1024 and h == 1024:
        return {
            "mode": "uniform-grid-auto",
            "grid": {"cols": 4, "rows": 4, "cell_width": 256, "cell_height": 256},
            "auto_exports": [
                {"name": "raw", "mode": "raw"},
                {"name": "small_16x16", "mode": "fit", "size": [16, 16]},
                {"name": "medium_24x24", "mode": "fit", "size": [24, 24]},
                {"name": "actor_24x36", "mode": "fit", "size": [24, 36]},
            ],
        }

    if category == "fx" and w == 1536 and h == 768:
        return {
            "mode": "uniform-grid-auto",
            "grid": {"cols": 6, "rows": 3, "cell_width": 256, "cell_height": 256},
            "auto_exports": [
                {"name": "raw", "mode": "raw"},
                {"name": "fx_24x24", "mode": "fit", "size": [24, 24]},
                {"name": "fx_48x48", "mode": "fit", "size": [48, 48]},
            ],
        }

    return {
        "mode": "manual-regions",
        "canvas": {"width": w, "height": h},
        "template_outputs": [
            "top_screen_slice",
            "bottom_screen_slice",
            "icon_exports",
            "portrait_exports",
        ],
    }


def infer_translation_metadata(asset: dict, recon_spec: dict, rig_lookup: dict[str, str]) -> dict:
    category = asset["category"]
    translation_rules = recon_spec["category_translation_rules"][category]
    entity_name = infer_entity_name(asset["name"])
    bind_to_rig = bool(translation_rules.get("bind_to_rig"))
    metadata = {
        "analysis_profile": translation_rules["mesh_target"],
        "symbol_object_policy": "meaningful contiguous image regions become self-contained symbol objects",
        "neighbor_stencil": "32-neighbor comparison",
        "depth_inference_method": "region stack, local shading, occlusion order, and cross-view consistency",
        "engine_mapping": translation_rules,
        "pivot_policy": {
            "primary_anchor": infer_baseline_anchor(asset),
            "stable_pivot_required": True,
        },
        "collision_policy": {
            "required": category not in {"ui", "fx"},
            "proxy_source": "silhouette-derived region hull",
        },
        "surface_contract": {
            "height_texture_ready": category not in {"ui"},
            "material_mask_ready": True,
            "normal_hint_ready": category not in {"ui"},
        },
        "keypose_intake": {
            "required": bind_to_rig,
            "runtime_inbetween_candidate": bind_to_rig,
        },
    }
    if entity_name and entity_name in rig_lookup:
        metadata["rig_reference"] = rig_lookup[entity_name]
    return metadata


def build_reconstruction_outputs(asset: dict, recon_spec: dict) -> list[str]:
    outputs = list(recon_spec["required_outputs_per_asset"])
    bind_to_rig = recon_spec["category_translation_rules"][asset["category"]].get("bind_to_rig", False)
    if bind_to_rig:
        outputs.extend(recon_spec["animated_asset_extra_outputs"])
    return outputs


def build_rig_lookup(rigs: dict) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for skeleton in rigs.get("skeletons", []):
        lookup[skeleton["entity"]] = skeleton["name"]
    return lookup


def enrich_manifest(manifest: dict, recon_spec: dict, rig_lookup: dict[str, str]) -> dict:
    manifest["manifest_version"] = "2026-03-12.integration_metadata_complete"
    manifest["tooling"] = {
        "manifest_enricher": "tools/enrich_qa_demo_manifest.py",
        "manifest_validator": "tools/validate_qa_demo_manifest.py",
        "asset_slicer": "tools/slice_qa_demo_assets.py",
    }
    for asset in manifest.get("assets", []):
        runtime_size = infer_runtime_size(asset, manifest)
        asset["integration_role"] = infer_integration_role(asset)
        asset["cell_layout"] = infer_cell_layout(asset)
        asset["baseline_anchor"] = infer_baseline_anchor(asset)
        asset["review_focus"] = infer_review_focus(asset)
        asset["translation_metadata"] = infer_translation_metadata(asset, recon_spec, rig_lookup)
        asset["reconstruction_outputs"] = build_reconstruction_outputs(asset, recon_spec)
        asset["slice_plan"] = infer_slice_plan(asset, runtime_size)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich the QA demo manifest with per-asset 3D translation metadata and slice plans.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--recon-spec", type=Path, default=DEFAULT_RECON_SPEC)
    parser.add_argument("--rigs", type=Path, default=DEFAULT_RIGS)
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    recon_spec = load_json(args.recon_spec)
    rig_lookup = build_rig_lookup(load_json(args.rigs))
    save_json(args.manifest, enrich_manifest(manifest, recon_spec, rig_lookup))
    print(f"Enriched manifest metadata in {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())