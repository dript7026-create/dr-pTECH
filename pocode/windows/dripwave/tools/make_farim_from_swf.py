from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main() -> None:
    parser = argparse.ArgumentParser(description="Package a SWF into a FARIM 0.1 zip container for dripwave.")
    parser.add_argument("swf", help="Path to the source .swf file")
    parser.add_argument("output", nargs="?", help="Output .farim path; defaults next to the source SWF")
    parser.add_argument("--entry-name", default="content/main.swf", help="Entry path inside the FARIM zip")
    args = parser.parse_args()

    swf_path = Path(args.swf).resolve()
    if not swf_path.exists() or swf_path.suffix.lower() != ".swf":
        raise SystemExit("Input must be an existing .swf file.")

    output_path = Path(args.output).resolve() if args.output else swf_path.with_suffix(".farim")
    manifest = {
        "format": "farim-0.1",
        "entry_swf": args.entry_name,
        "title": swf_path.stem,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("farim_manifest.json", json.dumps(manifest, indent=2) + "\n")
        archive.write(swf_path, args.entry_name)

    print(output_path)


if __name__ == "__main__":
    main()