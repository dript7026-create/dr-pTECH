from __future__ import annotations

import argparse
from pathlib import Path

from experiential_genesis.hypermanager import build_demo_hypermanager
from experiential_genesis.kaijugaiden import export_kaijugaiden_runtime_contract


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
    parser.add_argument("--include-kaijugaiden", action="store_true", help="Register the KaijuGaiden runtime adapter")
    parser.add_argument("--contract-out", type=Path, help="Optional path to write a KaijuGaiden HOPE runtime contract JSON")
    parser.add_argument("--scene-id", default="harbor_boss_duel", help="Scene id for the KaijuGaiden runtime contract")
    parser.add_argument("--scene-type", default="boss-rush", help="Scene type for the KaijuGaiden runtime contract")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    include_kaijugaiden = args.include_kaijugaiden or args.contract_out is not None
    manager = build_demo_hypermanager(
        preset=args.preset,
        include_kaijugaiden=include_kaijugaiden,
        kaijugaiden_scene_id=args.scene_id,
        kaijugaiden_scene_type=args.scene_type,
    )
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
    if args.contract_out:
        adapter = manager.adapters["kaijugaiden"]
        exported_contract = export_kaijugaiden_runtime_contract(adapter, args.contract_out)
        print(f"contract={exported_contract}")


if __name__ == "__main__":
    main()