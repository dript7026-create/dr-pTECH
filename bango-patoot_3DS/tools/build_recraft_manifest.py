from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RIGS_PATH = ROOT / "rigs" / "entity_rigs.json"
OUTPUT_PATH = ROOT / "recraft" / "bango_patoot_recraft_manifest.json"


def main() -> int:
    rig_data = json.loads(RIGS_PATH.read_text(encoding="utf-8"))
    items = []
    for skeleton in rig_data.get("skeletons", []):
        entity = skeleton["entity"].lower()
        items.append({
            "name": f"{entity}_turnaround_sheet",
            "prompt": f"Transparent background four-angle turnaround sheet for {skeleton['entity']} in Bango-Patoot, urban fantasy horror, readable silhouette, rig-friendly posture, clean key-pose spacing, pseudo-3D shading cues.",
            "w": 1536,
            "h": 1024,
            "out": f"generated/{entity}_turnaround_sheet.png",
            "negative_prompt": "solid background, blurry silhouette, cropped limbs, unreadable pose"
        })
        items.append({
            "name": f"{entity}_keypose_loop_sheet",
            "prompt": f"Transparent background key-pose sequence sheet for {skeleton['entity']} in Bango-Patoot, six major posture beats suitable for GIF loop planning and rig mapping, expressive motion arcs, urban occult adventure tone.",
            "w": 1536,
            "h": 1536,
            "out": f"generated/{entity}_keypose_loop_sheet.png",
            "negative_prompt": "solid background, merged frames, unreadable anatomy, missing extremities"
        })
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())