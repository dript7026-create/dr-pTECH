import os
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
PROJECT_ROOT = ROOT / "pipeline" / "projects" / "pertinence_tribunal"
MANIFEST = PROJECT_ROOT / "game_project.json"
OUT = ROOT / "pipeline" / "out" / "pertinence_tribunal_validation"


def run(cmd: list[str]) -> str:
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def verify_png_alpha(path: Path) -> dict:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    extrema = alpha.getextrema()
    has_transparency = extrema[0] < 255
    return {"path": str(path), "size": image.size, "has_transparency": has_transparency}


def main() -> int:
    build_output = run([sys.executable, str(TOOLS / "build_pertinence_test_pack.py")])
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    png_reports = []
    for group in ("tilesets", "sprites", "portraits"):
        for asset in manifest["assets"][group]:
            asset_path = PROJECT_ROOT / asset["path"]
            if not asset_path.exists():
                raise FileNotFoundError(asset_path)
            png_reports.append(verify_png_alpha(asset_path))

    pipeline_output = run([
        sys.executable,
        str(TOOLS / "game_pipeline.py"),
        "build",
        "--project",
        str(MANIFEST),
        "--out",
        str(OUT),
    ])

    blender_bundle = OUT / "blender_bundle" / "blender_conversion.json"
    blender_ingest = OUT / "blender_bundle" / "blender_ingest.py"
    blender_report = run([sys.executable, str(blender_ingest), str(blender_bundle)])

    id_manifest = json.loads((OUT / "idtech2_bundle" / "idtech2_manifest.json").read_text(encoding="utf-8"))
    report = {
        "build_output": json.loads(build_output),
        "pipeline_output": json.loads(pipeline_output),
        "png_assets_checked": len(png_reports),
        "png_transparency_failures": [item["path"] for item in png_reports if not item["has_transparency"]],
        "blender_report": json.loads(blender_report),
        "idtech_summary": {
            "asset_count": len(id_manifest["assets"]),
            "precache_count": len(id_manifest["precache"]),
            "system_count": len(id_manifest["systems"]),
            "entity_count": len(id_manifest["entities"]),
        },
        "recraft_manifest": {
            "path": str(PROJECT_ROOT / "recraft_manifest.json"),
            "api_key_present": bool(os.environ.get("RECRAFT_API_KEY")),
        },
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())