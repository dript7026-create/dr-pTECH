from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from illusioncanvasinteractive.iig import load_iig, save_iig
from illusioncanvasinteractive.runtime_manifest import build_illusioncanvas_runtime_manifest, enrich_iig_document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build IllusionCanvas runtime outputs from a source manifest")
    parser.add_argument("--source", required=True)
    parser.add_argument("--out-manifest", required=True)
    parser.add_argument("--template", default=str(ROOT / "sample_games" / "aridfeihth_vertical_slice.iig"))
    parser.add_argument("--out-iig", required=True)
    parser.add_argument("--ui-skin")
    parser.add_argument("--out-studio-session")
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    out_manifest_path = Path(args.out_manifest)
    out_iig_path = Path(args.out_iig)

    source_manifest = json.loads(source_path.read_text(encoding="utf-8"))
    runtime_manifest = build_illusioncanvas_runtime_manifest(source_manifest)
    out_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    out_manifest_path.write_text(json.dumps(runtime_manifest, indent=2), encoding="utf-8")

    template_document = load_iig(args.template)
    enriched_document = enrich_iig_document(
        template_document,
        runtime_manifest,
        str(source_path),
        str(out_manifest_path),
        args.ui_skin,
    )
    save_iig(enriched_document, out_iig_path)

    if args.out_studio_session:
        studio_session_path = Path(args.out_studio_session)
        studio_session_path.parent.mkdir(parents=True, exist_ok=True)
        studio_session_path.write_text(
            json.dumps(
                {
                    "launcher": str(ROOT / "run_illusioncanvas_studio.py"),
                    "game": str(out_iig_path),
                    "ui_skin": args.ui_skin,
                    "runtime_launcher": str(ROOT / "run_illusioncanvas.py"),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "runtime_manifest": str(out_manifest_path),
                "iig": str(out_iig_path),
                "asset_count": runtime_manifest["asset_count"],
                "ui_skin": args.ui_skin,
                "studio_session": args.out_studio_session,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())