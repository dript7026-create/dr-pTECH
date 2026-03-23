from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
MANIFEST_PATH = ROOT / 'generated' / 'dodogame_gui_recraft_manifest.json'
RUNNER_PATH = WORKSPACE_ROOT / 'egosphere' / 'tools' / 'run_recraft_manifest.py'


def main() -> int:
    parser = argparse.ArgumentParser(description='Execute the DODOGame live Recraft pass through the shared manifest runner.')
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print('{"status": "missing_manifest"}')
        return 1
    if not RUNNER_PATH.exists():
        print('{"status": "missing_runner"}')
        return 1

    command = [sys.executable, str(RUNNER_PATH), str(MANIFEST_PATH)]
    if args.limit > 0:
        command.extend(['--limit', str(args.limit)])
    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == '__main__':
    raise SystemExit(main())