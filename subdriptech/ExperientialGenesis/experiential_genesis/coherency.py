from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CoherencySignal:
    name: str
    frequency: float
    amplitude: float
    phase: float
    trust: float


@dataclass(frozen=True)
class CoherencyField:
    stability: float
    tension: float
    resonance: float
    coherence_index: float


def clamp_unit(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def compute_field(signals: Iterable[CoherencySignal]) -> CoherencyField:
    collected = list(signals)
    if not collected:
        return CoherencyField(stability=0.0, tension=0.0, resonance=0.0, coherence_index=0.0)

    weighted_frequency = sum(signal.frequency * signal.trust for signal in collected)
    weighted_amplitude = sum(signal.amplitude * signal.trust for signal in collected)
    weighted_phase = sum(signal.phase * signal.trust for signal in collected)
    trust_total = sum(signal.trust for signal in collected) or 1.0
    mean_frequency = weighted_frequency / trust_total
    mean_amplitude = weighted_amplitude / trust_total
    mean_phase = weighted_phase / trust_total

    variance = sum(abs(signal.frequency - mean_frequency) * signal.trust for signal in collected) / trust_total
    stability = clamp_unit(1.0 - (variance / 10.0))
    tension = clamp_unit(mean_amplitude * (1.0 - stability))
    resonance = clamp_unit((mean_frequency / 12.0) * 0.6 + (1.0 - abs(mean_phase - 0.5)) * 0.4)
    coherence_index = clamp_unit((stability * 0.45) + (resonance * 0.4) + ((1.0 - tension) * 0.15))
    return CoherencyField(
        stability=stability,
        tension=tension,
        resonance=resonance,
        coherence_index=coherence_index,
    )