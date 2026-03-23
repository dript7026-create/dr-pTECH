import json
from pathlib import Path

from compile_knave_asset_generator_model import COMMON_APPENDIX, MODEL_PATH, PROJECT_ROOT


MANIFEST_PATH = PROJECT_ROOT / "recraft_manifest.json"
SUMMARY_PATH = PROJECT_ROOT / "knave_recraft_pass_summary.json"


def load_components() -> list[dict]:
    payload = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    return payload["designer_components"]


def make_manifest_asset(component: dict) -> dict:
    width, height = component["dimensions"]
    transparent = component["category"] != "environment"
    return {
        "name": component["asset_id"],
        "category": component["category"],
        "prompt": component["compiled_prompt"],
        "negative_prompt": "direct imitation, muddy shapes, unreadable silhouettes, cluttered staging, watermark, text blocks, noisy anatomy",
        "w": width,
        "h": height,
        "model": "recraftv4",
        "planned_credits": component["planned_credits"],
        "api_units": component["planned_credits"],
        "out": component["output"],
        "transparent_background": transparent,
        "auto_polish": True,
        "component_tags": component["component_tags"],
        "mutation_axes": component["mutation_axes"],
    }


def main() -> int:
    components = load_components()
    assets = [make_manifest_asset(component) for component in components]
    manifest = {
        "manifest_name": "knave_advanced_asset_pass_2000_credit",
        "manifest_version": "2026-03-15.knave.recraft.v1",
        "intent": "Advanced original knave asset pass for Asset Generator ingestion and pipeline compilation.",
        "output_root": ".",
        "budget": {
            "requested_budget": 2000,
            "allocated_credits": sum(asset["planned_credits"] for asset in assets),
        },
        "shared_prompt_appendix": COMMON_APPENDIX,
        "godai": {
            "mode": "asset_direction_conductor",
            "pressure_policy": "increase novelty only if silhouette readability remains stable",
            "mercy_policy": "reduce ornamental density when component clarity drops",
        },
        "assets": assets,
    }
    summary = {
        "asset_count": len(assets),
        "allocated_credits": manifest["budget"]["allocated_credits"],
        "character_assets": len([asset for asset in assets if asset["category"] == "character"]),
        "environment_assets": len([asset for asset in assets if asset["category"] == "environment"]),
        "ui_assets": len([asset for asset in assets if asset["category"] == "ui"]),
        "portrait_assets": len([asset for asset in assets if asset["category"] == "portrait"]),
        "fx_assets": len([asset for asset in assets if asset["category"] == "fx"]),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST_PATH), "summary": str(SUMMARY_PATH), "allocated_credits": summary["allocated_credits"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())