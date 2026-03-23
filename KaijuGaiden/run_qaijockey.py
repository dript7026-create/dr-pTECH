#!/usr/bin/env python3

import importlib.util
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    neowakeup_root = root.parent / "NeoWakeUP"
    runner_path = neowakeup_root / "neowakeup" / "runner.py"
    if str(neowakeup_root) not in sys.path:
        sys.path.insert(0, str(neowakeup_root))
    spec = importlib.util.spec_from_file_location("neowakeup_runner", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load NeoWakeUP runner from {runner_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


if __name__ == "__main__":
    main()
