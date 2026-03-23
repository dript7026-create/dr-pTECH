from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from bango_pipeline_paths import resolve_asset_root


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
ASSET_ROOT = resolve_asset_root(ROOT)
GENERATED_DIR = ASSET_ROOT / "generated" / "clip_blend_id"
RAW_OUTPUT_DIR = ASSET_ROOT / "production_raw"
POLISHED_OUTPUT_DIR = ASSET_ROOT / "production_polished"
DOENGINE_ROOT = WORKSPACE_ROOT / "DoENGINE"
ILLUSIONCANVAS_ROOT = WORKSPACE_ROOT / "IllusionCanvasInteractive"

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_bango_production_asset_program import MANIFEST_PATH, PROTOCOL_PATH, build_manifest, save_json


def load_manifest() -> dict:
    manifest, protocol = build_manifest()
    save_json(MANIFEST_PATH, manifest)
    save_json(PROTOCOL_PATH, protocol)
    return manifest


def build_clipstudio_ingest(assets: list[dict]) -> dict:
    ingest_assets = []
    for asset in assets:
        if "clipstudio" not in asset["pipeline_targets"]:
            continue
        ingest_assets.append(
            {
                "asset_id": asset["name"],
                "source_path": asset["out"],
                "transparent_background": asset.get("transparent_background", True),
                "auto_polish": asset.get("auto_polish", True),
                "protocol": asset["protocol"],
            }
        )
    return {
        "project_name": "BangoPatootAssetProduction",
        "asset_count": len(ingest_assets),
        "assets": ingest_assets,
    }


def build_polish_queue(assets: list[dict]) -> dict:
    return {
        "input_root": str(RAW_OUTPUT_DIR),
        "output_root": str(POLISHED_OUTPUT_DIR),
        "assets": [
            {
                "asset_id": asset["name"],
                "raw_path": asset["out"],
                "polish_required": asset.get("auto_polish", True),
            }
            for asset in assets
            if asset.get("auto_polish", True)
        ],
    }


def build_blender_ingest(assets: list[dict]) -> dict:
    ingest_assets = []
    for asset in assets:
        if "blender" not in asset["pipeline_targets"]:
            continue
        ingest_assets.append(
            {
                "asset_id": asset["name"],
                "source_path": asset["out"],
                "category": asset["category"],
                "riggable": asset["category"] in {"character_sheet", "animation_pack", "animated_environment_object", "apiary_sheet"},
                "derived_outputs": asset["protocol"].get("derived_outputs", []),
            }
        )
    return {
        "project_name": "BangoPatootAssetProduction",
        "asset_count": len(ingest_assets),
        "assets": ingest_assets,
    }


def build_idtech2_registry(assets: list[dict]) -> dict:
    registry_assets = []
    for asset in assets:
        if "idtech2" not in asset["pipeline_targets"]:
            continue
        registry_assets.append(
            {
                "asset_id": asset["name"],
                "category": asset["category"],
                "asset_root": f"baseq2/bangopatoot/{asset['category']}/{Path(asset['out']).name}",
                "generation_mode": asset.get("generation_mode", "packed_master"),
            }
        )
    return {
        "module_name": "g_bangopatoot",
        "asset_count": len(registry_assets),
        "assets": registry_assets,
    }


def build_donow_manifest() -> dict:
    command = [
        sys.executable,
        str(DOENGINE_ROOT / 'tools' / 'build_donow_runtime_manifest.py'),
        '--source',
        str(MANIFEST_PATH),
        '--out',
        str(GENERATED_DIR / 'donow_runtime_manifest.json'),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        'command': ' '.join(command),
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'out': str(GENERATED_DIR / 'donow_runtime_manifest.json'),
    }


def build_illusioncanvas_manifest() -> dict:
    command = [
        sys.executable,
        str(ILLUSIONCANVAS_ROOT / 'tools' / 'build_illusioncanvas_bundle.py'),
        '--source',
        str(MANIFEST_PATH),
        '--ui-skin',
        str(GENERATED_DIR / 'illusioncanvas_ui_skin.json'),
        '--out-manifest',
        str(GENERATED_DIR / 'illusioncanvas_runtime_manifest.json'),
        '--out-iig',
        str(GENERATED_DIR / 'aridfeihth_illusioncanvas_bundle.iig'),
        '--out-studio-session',
        str(GENERATED_DIR / 'illusioncanvas_studio_session.json'),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        'command': ' '.join(command),
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'out_manifest': str(GENERATED_DIR / 'illusioncanvas_runtime_manifest.json'),
        'out_iig': str(GENERATED_DIR / 'aridfeihth_illusioncanvas_bundle.iig'),
        'out_studio_session': str(GENERATED_DIR / 'illusioncanvas_studio_session.json'),
    }


def build_illusioncanvas_ui_skin() -> dict:
    command = [
        sys.executable,
        str(ILLUSIONCANVAS_ROOT / 'tools' / 'build_illusioncanvas_ui_skin.py'),
        '--manifest',
        str(ILLUSIONCANVAS_ROOT / 'recraft' / 'illusioncanvas_gui_1000_credit_manifest.json'),
        '--out',
        str(GENERATED_DIR / 'illusioncanvas_ui_skin.json'),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        'command': ' '.join(command),
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'out': str(GENERATED_DIR / 'illusioncanvas_ui_skin.json'),
    }


def build_idtech2_bootstrap() -> dict:
    command = [
        sys.executable,
        str(ROOT / 'tools' / 'build_bango_idtech2_bootstrap.py'),
        '--registry',
        str(GENERATED_DIR / 'idtech2_runtime_registry.json'),
        '--out-dir',
        str(ROOT / 'idtech2_mod' / 'generated'),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        'command': ' '.join(command),
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'out_dir': str(ROOT / 'idtech2_mod' / 'generated'),
    }


def maybe_run_recraft(run_generation: bool, limit: int) -> dict:
    if not run_generation:
        return {"status": "skipped", "reason": "generation_not_requested"}
    command = [sys.executable, str(WORKSPACE_ROOT / "egosphere" / "tools" / "run_recraft_manifest.py"), str(MANIFEST_PATH)]
    if limit > 0:
        command.extend(["--limit", str(limit)])
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "status": "invoked",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def maybe_run_polish(run_polish: bool, input_path: str | None) -> dict:
    if not run_polish:
        return {"status": "skipped", "reason": "polish_not_requested"}
    target = Path(input_path) if input_path else RAW_OUTPUT_DIR
    command = [sys.executable, str(WORKSPACE_ROOT / "readAIpolish" / "readAIpolish_cli.py"), str(target), "--out-dir", str(POLISHED_OUTPUT_DIR)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "status": "invoked",
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "target": str(target),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Bango clip-blend-id production asset pipeline queues")
    parser.add_argument("--run-recraft", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--run-polish", action="store_true")
    parser.add_argument("--polish-input", type=str)
    args = parser.parse_args()

    manifest = load_manifest()
    assets = manifest["assets"]
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    clipstudio_manifest = build_clipstudio_ingest(assets)
    polish_queue = build_polish_queue(assets)
    blender_manifest = build_blender_ingest(assets)
    idtech2_registry = build_idtech2_registry(assets)

    save_json(GENERATED_DIR / "clipstudio_ingest_manifest.json", clipstudio_manifest)
    save_json(GENERATED_DIR / "auto_polish_queue.json", polish_queue)
    save_json(GENERATED_DIR / "blender_ingest_manifest.json", blender_manifest)
    save_json(GENERATED_DIR / "idtech2_runtime_registry.json", idtech2_registry)

    donow_manifest = build_donow_manifest()
    illusioncanvas_ui_skin = build_illusioncanvas_ui_skin()
    illusioncanvas_manifest = build_illusioncanvas_manifest()
    idtech2_bootstrap = build_idtech2_bootstrap()

    report = {
        "asset_root": str(ASSET_ROOT),
        "manifest": str(MANIFEST_PATH),
        "protocol": str(PROTOCOL_PATH),
        "clipstudio_manifest": str(GENERATED_DIR / "clipstudio_ingest_manifest.json"),
        "polish_queue": str(GENERATED_DIR / "auto_polish_queue.json"),
        "blender_manifest": str(GENERATED_DIR / "blender_ingest_manifest.json"),
        "donow_manifest": str(GENERATED_DIR / "donow_runtime_manifest.json"),
        "illusioncanvas_ui_skin": str(GENERATED_DIR / "illusioncanvas_ui_skin.json"),
        "illusioncanvas_manifest": str(GENERATED_DIR / "illusioncanvas_runtime_manifest.json"),
        "illusioncanvas_iig": str(GENERATED_DIR / "aridfeihth_illusioncanvas_bundle.iig"),
        "illusioncanvas_studio_session": str(GENERATED_DIR / "illusioncanvas_studio_session.json"),
        "idtech2_registry": str(GENERATED_DIR / "idtech2_runtime_registry.json"),
        "idtech2_bootstrap": idtech2_bootstrap,
        "donow": donow_manifest,
        "illusioncanvas_ui_skin_build": illusioncanvas_ui_skin,
        "illusioncanvas": illusioncanvas_manifest,
        "recraft": maybe_run_recraft(args.run_recraft, args.limit),
        "polish": maybe_run_polish(args.run_polish, args.polish_input),
    }
    save_json(GENERATED_DIR / "pipeline_report.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
