s"""CLI wrapper that converts a ClipConceptBook (.ccp) into a standard Recraft manifest JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ccp_manifest import ccp_to_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ccp_path")
    parser.add_argument("out_json")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--default-w", type=int, default=1024)
    parser.add_argument("--default-h", type=int, default=1024)
    args = parser.parse_args()

    items = ccp_to_manifest(args.ccp_path, args.output_dir, args.default_w, args.default_h)
    output_path = Path(args.out_json)
    output_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())