from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the native EgoSphere bridge DLL for IllusionCanvasInteractive")
    parser.add_argument("--workspace", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace)
    egosphere_root = workspace / "egosphere"
    out_path = Path(args.out) if args.out else egosphere_root / "egosphere.dll"
    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        raise SystemExit("No C compiler found on PATH")

    command = [
        compiler,
        "-std=c11",
        "-O2",
        "-shared",
        "-Wl,--export-all-symbols",
        "-o",
        str(out_path),
        str(egosphere_root / "egosphere.c"),
        "-lm",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        return result.returncode
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())