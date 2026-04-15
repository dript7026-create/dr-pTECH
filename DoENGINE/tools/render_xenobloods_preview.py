from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "apps") not in sys.path:
    sys.path.insert(0, str(ROOT / "apps"))

from dodo_engine3d import DodoPseudo3DEngine  # type: ignore


SCENE_PATH = ROOT / "generated" / "xenobloods_preview" / "xenobloods_pikerel_swamp_showcase.json"
PREVIEW_PATH = ROOT / "generated" / "xenobloods_preview" / "xenobloods_pikerel_swamp_preview.png"


def main() -> None:
    engine = DodoPseudo3DEngine(width=920, height=540, scene_manifest_path=SCENE_PATH)
    payload = engine.write_preview(PREVIEW_PATH, orbit=0.48, elevation=0.18, shader_mix=0.9, time_s=1.4)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()