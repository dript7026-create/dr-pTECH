from __future__ import annotations

import argparse
import json
from pathlib import Path

from graphics_polish_ai import RASTER_EXTENSIONS, polish_asset_path


def gather_inputs(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        results = []
        for candidate in sorted(path.rglob("*")):
            if candidate.suffix.lower() in RASTER_EXTENSIONS or candidate.suffix.lower() == ".clip":
                results.append(candidate)
        return results
    raise FileNotFoundError(f"Input not found: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="readAIpolish raster and Clip Studio bridge processor")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()

    outputs = []
    for source in gather_inputs(args.input):
        target = None
        if args.out_dir:
            args.out_dir.mkdir(parents=True, exist_ok=True)
            target = args.out_dir / f"{source.stem}_readAIpolish{source.suffix}"
        outputs.append(polish_asset_path(source, target))
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
