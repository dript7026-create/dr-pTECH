from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List

from .adapters import ExperientialAdapter, Mutation, apply_demo_preset, demo_adapters
from .coherency import CoherencySignal, compute_field
from .consensus import ConsensusFrame, build_consensus_frame


@dataclass
class ExperientialGenesis:
    seed: int = 113
    adapters: Dict[str, ExperientialAdapter] = field(default_factory=dict)
    tick_index: int = 0
    history: List[ConsensusFrame] = field(default_factory=list)

    def register(self, adapter: ExperientialAdapter) -> None:
        self.adapters[adapter.name] = adapter

    def snapshots(self):
        return [adapter.snapshot() for adapter in self.adapters.values()]

    def tick(self) -> ConsensusFrame:
        snapshots = self.snapshots()
        signals: List[CoherencySignal] = []
        for snapshot in snapshots:
            signals.extend(snapshot.signals)

        field = compute_field(signals)
        for adapter in self.adapters.values():
            for mutation in adapter.propose_mutations(field):
                adapter.apply(mutation)

        self.tick_index += 1
        frame = build_consensus_frame(self.tick_index, field, self.snapshots())
        self.history.append(frame)
        return frame

    def export_history(self, file_path: str | Path) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for frame in self.history:
                handle.write(json.dumps(frame.to_dict(), sort_keys=True) + "\n")
        return path


def build_demo_hypermanager(preset: str = "default") -> ExperientialGenesis:
    manager = ExperientialGenesis()
    for adapter in apply_demo_preset(demo_adapters(), preset):
        manager.register(adapter)
    return manager