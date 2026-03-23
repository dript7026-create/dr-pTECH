from __future__ import annotations

import argparse
from pathlib import Path

from experiential_genesis.hypermanager import build_demo_hypermanager


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Experiential Genesis demo hypermanager")
    parser.add_argument("--ticks", type=int, default=3, help="Number of EG ticks to execute")
    parser.add_argument(
        "--preset",
        choices=("default", "storm", "calm"),
        default="default",
        help="Initial scenario preset for demo adapters",
    )
    parser.add_argument("--history-out", type=Path, help="Optional JSONL file to write tick history to")
    parser.add_argument("--show-snapshots", action="store_true", help="Print adapter snapshots after each tick")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manager = build_demo_hypermanager(preset=args.preset)
    for _ in range(args.ticks):
        frame = manager.tick()
        print(frame.describe())
        if args.show_snapshots:
            for snapshot in manager.snapshots():
                print(f"  snapshot={snapshot.name} metrics={snapshot.metrics}")
        print("-" * 72)
    if args.history_out:
        exported = manager.export_history(args.history_out)
        print(f"history={exported}")


if __name__ == "__main__":
    main()