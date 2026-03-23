#!/usr/bin/env python3
"""CLI for the NeoWakeUP planetary simulation."""

from __future__ import annotations

import argparse
from pathlib import Path
import time

from .equations import EQUATION_SPECS
from .models import MODEL_PRESETS
from .network import Directive, PlanetaryMindNetwork, PlanetaryMindStore

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE = ROOT / "state" / "planetary_mind.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NeoWakeUP planetary mind simulation")
    parser.add_argument("--steps", type=int, default=12, help="How many simulation steps to run")
    parser.add_argument("--regions", type=int, default=6, help="Bootstrap region count when no saved state exists")
    parser.add_argument("--entities-per-region", type=int, default=12, help="Bootstrap entity count per region")
    parser.add_argument("--model", choices=sorted(MODEL_PRESETS.keys()), default="civic", help="Preset directive profile")
    parser.add_argument("--novelty", type=float, help="Override novelty weight")
    parser.add_argument("--equity", type=float, help="Override equity weight")
    parser.add_argument("--resilience", type=float, help="Override resilience weight")
    parser.add_argument("--speed", type=float, help="Override speed weight")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE), help="Persistent JSON state path")
    parser.add_argument("--sleep-ms", type=float, default=0.0, help="Optional delay between steps")
    parser.add_argument("--show-equations", action="store_true", help="Print the equation registry before running")
    return parser.parse_args()


def _build_directive(args: argparse.Namespace) -> Directive:
    preset = MODEL_PRESETS[args.model]["directive"]
    return Directive(
        novelty=float(preset["novelty"] if args.novelty is None else args.novelty),
        equity=float(preset["equity"] if args.equity is None else args.equity),
        resilience=float(preset["resilience"] if args.resilience is None else args.resilience),
        speed=float(preset["speed"] if args.speed is None else args.speed),
    )


def main() -> None:
    args = parse_args()
    directive = _build_directive(args)
    network = PlanetaryMindNetwork(seed=7)
    store = PlanetaryMindStore(args.state_file)

    loaded = store.load_into(network)
    if not loaded:
        network.bootstrap(region_count=args.regions, entities_per_region=args.entities_per_region)

    if args.show_equations:
        print("[NeoWakeUP] Equation registry")
        for spec in EQUATION_SPECS.values():
            print(f"  - {spec.key}: {spec.expression}")
            print(f"    {spec.description}")
        print()

    print(f"[NeoWakeUP] Planetary model : {args.model}")
    print(f"[NeoWakeUP] State file      : {args.state_file}")
    print(f"[NeoWakeUP] Loaded state    : {'yes' if loaded else 'no'}")
    print(f"[NeoWakeUP] Directive       : novelty={directive.novelty:.2f} equity={directive.equity:.2f} resilience={directive.resilience:.2f} speed={directive.speed:.2f}")

    try:
        for _ in range(args.steps):
            report = network.step(directive)
            print(
                f"tick={report['tick']:4d}  coherence={report['planetary_coherence']:.3f}  "
                f"exchange={report['exchange']:.3f}  volatility={report['volatility']:.3f}  "
                f"solution={report['solution_score']:.3f}"
            )
            if args.sleep_ms > 0:
                time.sleep(args.sleep_ms / 1000.0)
    except KeyboardInterrupt:
        print("\n[NeoWakeUP] Interrupted.")
    finally:
        store.save(network)
        final = network.solve(directive)
        print("\n[NeoWakeUP] Final summary")
        print(f"  coherence : {final['planetary_coherence']:.4f}")
        print(f"  exchange  : {final['exchange']:.4f}")
        print(f"  volatility: {final['volatility']:.4f}")
        print(f"  solution  : {final['solution_score']:.4f}")
