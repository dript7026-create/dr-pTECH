from __future__ import annotations

import json
from pathlib import Path

from ..planetary.network import PlanetaryMindNetwork, PlanetaryMindStore


ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = ROOT / "state"
PUBLIC_ROOT = ROOT / "public_samples"


def _make_sample_planetary_state() -> dict:
    network = PlanetaryMindNetwork(seed=11)
    network.bootstrap(region_count=4, entities_per_region=8)
    return network.export_state()


def _make_sample_genome_state() -> dict:
    return {
        "genetics": {
            "population": [
                {
                    "predictive_weight": 0.58,
                    "reactive_weight": 1.02,
                    "stress_weight": 0.88,
                    "courage": 0.94,
                    "patience": 1.08,
                    "instinct_noise": 0.18,
                }
            ],
            "scores": [0.0],
            "active_index": 0,
            "generations": 0,
        },
        "relationships": {"nodes": {}, "sensitivity": 1.0},
        "skill": 0.75,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.5,
    }


def main() -> None:
    PUBLIC_ROOT.mkdir(parents=True, exist_ok=True)
    (PUBLIC_ROOT / "sample_planetary_mind.json").write_text(json.dumps(_make_sample_planetary_state(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (PUBLIC_ROOT / "sample_qaijockey_genome.json").write_text(json.dumps(_make_sample_genome_state(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme = {
        "files": [
            "sample_planetary_mind.json",
            "sample_qaijockey_genome.json",
        ],
        "note": "Sanitized sample states for public repository distribution.",
    }
    (PUBLIC_ROOT / "README_samples.json").write_text(json.dumps(readme, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote public samples to {PUBLIC_ROOT}")