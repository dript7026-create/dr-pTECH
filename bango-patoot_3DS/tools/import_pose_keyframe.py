from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "pose_imports" / "imported_pose_registry.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pose_json")
    args = parser.parse_args()

    pose_path = Path(args.pose_json).resolve()
    pose = json.loads(pose_path.read_text(encoding="utf-8"))
    registry = []
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry.append({
        "entity": pose.get("entity"),
        "rig": pose.get("rig"),
        "move_name": pose.get("move_name"),
        "frame_index": pose.get("frame_index"),
        "duration_ms": pose.get("duration_ms"),
        "source_image": pose.get("source_image"),
        "tags": pose.get("tags", []),
        "inbetween": pose.get("inbetween", {}),
        "pose_json": str(pose_path),
    })
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"Imported pose keyframe metadata into {REGISTRY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())