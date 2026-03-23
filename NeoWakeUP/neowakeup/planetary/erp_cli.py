#!/usr/bin/env python3
"""CLI for the NeoWakeUP ERP sequencer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .erpsequencer import ErpSequencer
from .network import PlanetaryMindNetwork, PlanetaryMindStore

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE = ROOT / "state" / "planetary_mind.json"
DEFAULT_OUTPUT = ROOT / "state" / "erpsequencer_report.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NeoWakeUP ERP sequencer")
    parser.add_argument("--steps", type=int, default=16, help="How many simulated ticks to sequence")
    parser.add_argument("--regions", type=int, default=6, help="Bootstrap region count when no saved state exists")
    parser.add_argument("--entities-per-region", type=int, default=12, help="Bootstrap entity count per region")
    parser.add_argument("--model", default="mythic", help="Planetary directive preset to use while sequencing")
    parser.add_argument("--intoxication", type=float, default=0.42, help="Stylized intoxication factor in the range 0..1")
    parser.add_argument("--recovery", type=float, default=0.46, help="Recovery bias in the range 0..1")
    parser.add_argument("--focus", type=float, default=0.37, help="Focus bias in the range 0..1")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE), help="Persistent JSON state path")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Where to write the sequencer report")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    network = PlanetaryMindNetwork(seed=7)
    store = PlanetaryMindStore(args.state_file)
    loaded = store.load_into(network)
    if not loaded:
        network.bootstrap(region_count=args.regions, entities_per_region=args.entities_per_region)

    report = ErpSequencer(seed=23).sequence(
        network,
        steps=args.steps,
        intoxication=args.intoxication,
        recovery=args.recovery,
        focus=args.focus,
        model_name=args.model,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    store.save(network)

    print(f"[NeoWakeUP] ERP sequencer report : {output_path}")
    print(f"[NeoWakeUP] Loaded state         : {'yes' if loaded else 'no'}")
    print(f"[NeoWakeUP] Events               : {report['event_count']}")
    print(f"[NeoWakeUP] Coherence            : {report['planetary_coherence']:.4f}")
    print(f"[NeoWakeUP] Volatility           : {report['volatility']:.4f}")
    print("[NeoWakeUP] Band counts          : " + ", ".join(f"{key}={value}" for key, value in sorted(report["band_counts"].items())))


if __name__ == "__main__":
    main()