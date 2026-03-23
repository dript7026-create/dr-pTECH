"""
SpectrumExprncs.

Bango-Patoot-specific EgoAssurance layer built on the same lightweight
relationship philosophy used by egosphere and NeoWakeUP.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SpectrumProfile:
    name: str
    resonance: float = 0.5
    assurance: float = 0.5
    pressure: float = 0.3
    memory_color: float = 0.5


class SpectrumExprncs:
    def __init__(self):
        self._profiles: dict[str, SpectrumProfile] = {}

    def ensure(self, name: str) -> SpectrumProfile:
        if name not in self._profiles:
            self._profiles[name] = SpectrumProfile(name=name)
        return self._profiles[name]

    def observe_encounter(self, name: str, outcome: float, intensity: float, novelty: float) -> SpectrumProfile:
        profile = self.ensure(name)
        profile.resonance = max(0.0, min(1.0, profile.resonance + 0.15 * outcome + 0.05 * novelty))
        profile.assurance = max(0.0, min(1.0, profile.assurance + 0.10 * outcome - 0.08 * intensity))
        profile.pressure = max(0.0, min(1.0, profile.pressure + 0.12 * intensity - 0.10 * outcome))
        profile.memory_color = max(0.0, min(1.0, profile.memory_color + 0.08 * novelty))
        return profile

    def export_state(self) -> dict:
        return {
            name: {
                "name": profile.name,
                "resonance": profile.resonance,
                "assurance": profile.assurance,
                "pressure": profile.pressure,
                "memory_color": profile.memory_color,
            }
            for name, profile in self._profiles.items()
        }