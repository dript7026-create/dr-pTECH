import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "pipeline" / "sample_project" / "game_project.json"
OUT = ROOT / "pipeline" / "out" / "validation"


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)

    cmd = [sys.executable, str(ROOT / "tools" / "game_pipeline.py"), "build", "--project", str(PROJECT), "--out", str(OUT)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print(result.stdout.strip())

    required = [
        OUT / "clipstudio_bundle" / "clipstudio_export.json",
        OUT / "clipstudio_bundle" / "clipstudio_runtime_manifest.json",
        OUT / "blender_bundle" / "blender_conversion.json",
        OUT / "blender_bundle" / "blender_ingest.py",
        OUT / "idtech2_bundle" / "idtech2_manifest.json",
        OUT / "idtech2_bundle" / "g_driptech_pipeline_autogen.h",
        OUT / "idtech2_bundle" / "g_driptech_pipeline_autogen.c",
    ]

    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print(json.dumps({"status": "failed", "missing": missing}, indent=2))
        return 1

    manifest = json.loads((OUT / "idtech2_bundle" / "idtech2_manifest.json").read_text(encoding="utf-8"))
    summary = {
        "status": "ok",
        "project_name": manifest["project_name"],
        "system_count": len(manifest["systems"]),
        "entity_count": len(manifest["entities"]),
        "precache_count": len(manifest["precache"]),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())