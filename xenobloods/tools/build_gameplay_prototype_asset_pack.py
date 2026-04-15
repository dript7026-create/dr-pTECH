from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import generate_prototype_assets  # noqa: E402
from jumpclip_xenobloods_pipeline import build_and_stage_xenobloods_preview_set  # noqa: E402


def build_gameplay_prototype_asset_pack() -> dict:
    generate_prototype_assets.main()
    preview_result = build_and_stage_xenobloods_preview_set()

    generated_manifest_path = ROOT / "assets" / "generated" / "prototype_gameplay_asset_manifest.json"
    generated_manifest = json.loads(generated_manifest_path.read_text(encoding="utf-8"))

    result = {
        "generated_manifest": str(generated_manifest_path),
        "static_sections": {key: len(value) if isinstance(value, list) else value for key, value in generated_manifest.items()},
        "active_preview": preview_result["active_preview"],
        "active_manifest": str(preview_result["active_manifest"]),
        "runtime_preview": str(preview_result["runtime"]["sprite_preview"]) if preview_result.get("runtime") else None,
        "asset_service_summary": str(preview_result["asset_service"]["summary_path"]) if preview_result.get("asset_service") else None,
        "staged_previews": preview_result["staged_previews"],
    }

    summary_path = ROOT / "assets" / "generated" / "gameplay_prototype_asset_pack.json"
    summary_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["summary_path"] = str(summary_path)
    return result


def main() -> None:
    result = build_gameplay_prototype_asset_pack()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()