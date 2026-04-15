from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jumpclip_xenobloods_pipeline import build_and_stage_xenobloods_preview_set  # noqa: E402


def main() -> None:
    result = build_and_stage_xenobloods_preview_set()
    print(
        json.dumps(
            {
                "active_preview": result["active_preview"],
                "active_bundle_dir": str(result["active_bundle_dir"]),
                "link_manifest": str(result["active_manifest"]),
                "runtime_preview": str(result["runtime"]["sprite_preview"]) if result.get("runtime") else None,
                "asset_service_summary": str(result["asset_service"]["summary_path"]) if result.get("asset_service") else None,
                "preview_roster": str(result["summary_path"]),
                "bundles": result["staged_previews"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
