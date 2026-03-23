from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List

from .adapters import AdapterSnapshot
from .coherency import CoherencyField


@dataclass(frozen=True)
class ParticleNode:
    source: str
    intensity: float
    polarity: float


@dataclass(frozen=True)
class ConsensusFrame:
    tick_index: int
    field: CoherencyField
    particles: List[ParticleNode]
    framebuffer: Dict[str, float]
    notes: List[str]

    def describe(self) -> str:
        notes = " | ".join(self.notes)
        return (
            f"tick={self.tick_index} coherence={self.field.coherence_index:.3f} "
            f"stability={self.field.stability:.3f} tension={self.field.tension:.3f} "
            f"particles={len(self.particles)} framebuffer={self.framebuffer} notes={notes}"
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "tick_index": self.tick_index,
            "field": asdict(self.field),
            "particles": [asdict(particle) for particle in self.particles],
            "framebuffer": self.framebuffer,
            "notes": self.notes,
        }


def build_consensus_frame(tick_index: int, field: CoherencyField, snapshots: Iterable[AdapterSnapshot]) -> ConsensusFrame:
    snapshot_list = list(snapshots)
    particles = [
        ParticleNode(
            source=snapshot.name,
            intensity=max(0.0, min(1.0, sum(snapshot.metrics.values()) / max(1, len(snapshot.metrics)))),
            polarity=field.resonance - field.tension,
        )
        for snapshot in snapshot_list
    ]
    framebuffer = {
        "deterministic_luminance": round((field.coherence_index * 0.65) + (field.resonance * 0.35), 4),
        "particle_visibility": round(max(0.1, min(1.0, field.resonance)), 4),
        "simulation_grain": round(max(0.0, min(1.0, field.tension * 0.8)), 4),
    }
    notes = [f"{snapshot.name}:{snapshot.summary}" for snapshot in snapshot_list]
    return ConsensusFrame(
        tick_index=tick_index,
        field=field,
        particles=particles,
        framebuffer=framebuffer,
        notes=notes,
    )