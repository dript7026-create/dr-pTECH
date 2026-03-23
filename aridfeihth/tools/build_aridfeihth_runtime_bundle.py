from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ILLUSION_ROOT = ROOT / "IllusionCanvasInteractive"
if str(ILLUSION_ROOT) not in sys.path:
    sys.path.insert(0, str(ILLUSION_ROOT))


def main(argv: list[str] | None = None) -> int:
    iig_module = importlib.import_module("illusioncanvasinteractive.iig")
    runtime_manifest_module = importlib.import_module("illusioncanvasinteractive.runtime_manifest")
    load_iig = iig_module.load_iig
    save_iig = iig_module.save_iig
    build_illusioncanvas_runtime_manifest = runtime_manifest_module.build_illusioncanvas_runtime_manifest
    enrich_iig_document = runtime_manifest_module.enrich_iig_document

    parser = argparse.ArgumentParser(description="Build dedicated aridfeihth IllusionCanvas runtime outputs")
    parser.add_argument("--source", default=str(ROOT / "aridfeihth" / "recraft" / "aridfeihth_illusioncanvas_manifest.json"))
    parser.add_argument("--template", default=str(ROOT / "IllusionCanvasInteractive" / "sample_games" / "aridfeihth_vertical_slice.iig"))
    parser.add_argument("--out-manifest", default=str(ROOT / "aridfeihth" / "generated" / "aridfeihth_runtime_manifest.json"))
    parser.add_argument("--out-iig", default=str(ROOT / "aridfeihth" / "generated" / "aridfeihth_vertical_slice_bundle.iig"))
    parser.add_argument("--ui-skin", default=str(ROOT / "IllusionCanvasInteractive" / "generated" / "ui" / "illusioncanvas_gothic_ui_skin.json"))
    parser.add_argument("--out-studio-session", default=str(ROOT / "aridfeihth" / "generated" / "aridfeihth_studio_session.json"))
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    template_path = Path(args.template)
    out_manifest_path = Path(args.out_manifest)
    out_iig_path = Path(args.out_iig)
    studio_session_path = Path(args.out_studio_session)

    source_manifest = json.loads(source_path.read_text(encoding="utf-8"))
    runtime_manifest = build_illusioncanvas_runtime_manifest(source_manifest)
    out_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    out_manifest_path.write_text(json.dumps(runtime_manifest, indent=2), encoding="utf-8")

    template_document = load_iig(template_path)
    enriched_document = enrich_iig_document(
        template_document,
        runtime_manifest,
        str(source_path),
        str(out_manifest_path),
        args.ui_skin,
    )
    save_iig(enriched_document, out_iig_path)

    studio_session_path.parent.mkdir(parents=True, exist_ok=True)
    studio_session_path.write_text(
        json.dumps(
            {
                "launcher": str(ROOT / "IllusionCanvasInteractive" / "run_illusioncanvas_studio.py"),
                "runtime_launcher": str(ROOT / "IllusionCanvasInteractive" / "run_illusioncanvas.py"),
                "game": str(out_iig_path),
                "runtime_manifest": str(out_manifest_path),
                "ui_skin": args.ui_skin,
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
                "studio_session": str(studio_session_path),
                "asset_count": runtime_manifest["asset_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
