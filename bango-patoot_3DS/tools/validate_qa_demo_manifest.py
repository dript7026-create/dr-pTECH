from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "recraft" / "bango_patoot_qa_demo_manifest.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_asset(asset: dict) -> list[str]:
    errors: list[str] = []
    required_fields = [
        "integration_role",
        "cell_layout",
        "baseline_anchor",
        "review_focus",
        "translation_metadata",
        "reconstruction_outputs",
        "slice_plan",
    ]
    for field in required_fields:
        if field not in asset:
            errors.append(f"missing field: {field}")

    slice_plan = asset.get("slice_plan", {})
    mode = slice_plan.get("mode")
    if mode == "uniform-grid":
        grid = slice_plan.get("grid", {})
        cols = int(grid.get("cols", 0))
        rows = int(grid.get("rows", 0))
        cell_width = int(grid.get("cell_width", 0))
        cell_height = int(grid.get("cell_height", 0))
        if cols * cell_width != int(asset["w"]):
            errors.append("grid width does not match asset width")
        if rows * cell_height != int(asset["h"]):
            errors.append("grid height does not match asset height")
        if not slice_plan.get("cells"):
            errors.append("uniform-grid plan missing cells")
    elif mode == "uniform-grid-auto":
        grid = slice_plan.get("grid", {})
        cols = int(grid.get("cols", 0))
        rows = int(grid.get("rows", 0))
        cell_width = int(grid.get("cell_width", 0))
        cell_height = int(grid.get("cell_height", 0))
        if cols * cell_width != int(asset["w"]):
            errors.append("auto-grid width does not match asset width")
        if rows * cell_height != int(asset["h"]):
            errors.append("auto-grid height does not match asset height")
        if not slice_plan.get("auto_exports"):
            errors.append("auto-grid plan missing export variants")
    elif mode == "manual-regions":
        if "canvas" not in slice_plan:
            errors.append("manual-regions plan missing canvas")
    else:
        errors.append("unsupported or missing slice_plan mode")

    translation = asset.get("translation_metadata", {})
    for field in ["analysis_profile", "neighbor_stencil", "depth_inference_method", "engine_mapping", "pivot_policy", "collision_policy", "surface_contract", "keypose_intake"]:
        if field not in translation:
            errors.append(f"translation metadata missing: {field}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate that every QA demo asset includes translation metadata and slice plans.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    assets = manifest.get("assets", [])
    failures = 0
    for asset in assets:
        errors = validate_asset(asset)
        if errors:
            failures += 1
            print(f"[FAIL] {asset['name']}")
            for error in errors:
                print(f"  - {error}")

    if failures:
        print(f"Validation failed for {failures} assets.")
        return 1

    print(f"Validated {len(assets)} assets with complete metadata and slice plans.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())