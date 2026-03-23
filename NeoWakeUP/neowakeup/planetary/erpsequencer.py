"""Symbolic ERP sequencer for stress- and intoxication-driven activation drift."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random
from statistics import fmean

from .models import MODEL_PRESETS
from .network import Directive, PlanetaryMindNetwork


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


ERP_LEGEND_FAMILIES: dict[str, tuple[str, ...]] = {
    "murmur": ("erpsquible", "erpskwiible", "erpskqible"),
    "ripple": ("erp skwible", "erpskquible", "erpskwiqble"),
    "fracture": ("erpsquerble", "eprscerber", "erpsckwerble"),
    "blackglass": ("swkeeble", "erpsquible", "erpsquerble"),
}


@dataclass(frozen=True)
class ErpEvent:
    tick: int
    entity_id: str
    region_id: str
    phase: str
    band: str
    legend_name: str
    score: float
    stress: float
    intoxication: float
    activation_gap: float

    def to_dict(self) -> dict[str, object]:
        return {
            "tick": self.tick,
            "entity_id": self.entity_id,
            "region_id": self.region_id,
            "phase": self.phase,
            "band": self.band,
            "legend_name": self.legend_name,
            "score": round(self.score, 6),
            "stress": round(self.stress, 6),
            "intoxication": round(self.intoxication, 6),
            "activation_gap": round(self.activation_gap, 6),
        }


class ErpSequencer:
    """Generate symbolic perturbation events from a planetary network state.

    This is an interpretive simulator for game/systems work. It is not a
    medical model and should be treated as a stylized signal generator.
    """

    _PHASES = ("pre_echo", "crossfade", "afterimage", "dropout")
    _BANDS = (
        (0.24, "murmur"),
        (0.42, "ripple"),
        (0.62, "fracture"),
        (1.01, "blackglass"),
    )

    def __init__(self, seed: int = 23):
        self._rng = random.Random(seed)

    def sequence(
        self,
        network: PlanetaryMindNetwork,
        steps: int = 12,
        intoxication: float = 0.35,
        recovery: float = 0.45,
        focus: float = 0.40,
        model_name: str = "civic",
    ) -> dict[str, object]:
        if not network.entities:
            network.bootstrap()

        preset = MODEL_PRESETS.get(model_name, MODEL_PRESETS["civic"])
        directive = Directive(**preset["directive"])
        events: list[ErpEvent] = []
        tick_summaries: list[dict[str, object]] = []

        intoxication = _clamp(intoxication)
        recovery = _clamp(recovery)
        focus = _clamp(focus)

        for _ in range(steps):
            network.step(directive)
            tick = network.tick_count
            tick_events = self._sequence_tick(network, tick, intoxication, recovery, focus)
            events.extend(tick_events)
            if tick_events:
                peak = max(event.score for event in tick_events)
                density = len(tick_events) / max(len(network.entities), 1)
            else:
                peak = 0.0
                density = 0.0
            tick_summaries.append(
                {
                    "tick": tick,
                    "event_count": len(tick_events),
                    "peak_score": round(peak, 6),
                    "density": round(density, 6),
                    "planetary_coherence": round(network.planetary_coherence_value, 6),
                    "volatility": round(network.volatility, 6),
                }
            )

        band_counts: dict[str, int] = {}
        legend_counts: dict[str, int] = {}
        for event in events:
            band_counts[event.band] = band_counts.get(event.band, 0) + 1
            legend_counts[event.legend_name] = legend_counts.get(event.legend_name, 0) + 1

        return {
            "mode": "erpsequencer",
            "model": model_name,
            "steps": steps,
            "intoxication": round(intoxication, 6),
            "recovery": round(recovery, 6),
            "focus": round(focus, 6),
            "planetary_coherence": round(network.planetary_coherence_value, 6),
            "volatility": round(network.volatility, 6),
            "event_count": len(events),
            "band_counts": band_counts,
            "legend_catalog": {band: list(names) for band, names in ERP_LEGEND_FAMILIES.items()},
            "legend_counts": legend_counts,
            "tick_summaries": tick_summaries,
            "events": [event.to_dict() for event in events],
        }

    def _sequence_tick(
        self,
        network: PlanetaryMindNetwork,
        tick: int,
        intoxication: float,
        recovery: float,
        focus: float,
    ) -> list[ErpEvent]:
        events: list[ErpEvent] = []
        baseline_stress = fmean(entity.stress for entity in network.entities.values()) if network.entities else 0.0
        for entity in network.entities.values():
            region = network.regions[entity.region_id]
            activation_gap = abs(entity.activation - region.coherence)
            load = (
                0.50 * entity.stress
                + 0.36 * intoxication
                + 0.24 * activation_gap
                + 0.12 * (1.0 - entity.trust)
                + 0.10 * network.volatility
            )
            damping = 0.18 * recovery * entity.genome.cohesion + 0.12 * focus * entity.genome.memory_bias
            drift = self._oscillation(entity.entity_id, tick)
            score = _clamp(load - damping + drift + 0.12 * max(entity.stress - baseline_stress, 0.0), 0.0, 1.01)
            band = self._band_for(score)
            if band is None:
                continue
            legend_name = self._legend_name(entity.entity_id, tick, band)
            events.append(
                ErpEvent(
                    tick=tick,
                    entity_id=entity.entity_id,
                    region_id=entity.region_id,
                    phase=self._phase_for(entity.entity_id, tick),
                    band=band,
                    legend_name=legend_name,
                    score=score,
                    stress=entity.stress,
                    intoxication=intoxication,
                    activation_gap=activation_gap,
                )
            )
        events.sort(key=lambda event: event.score, reverse=True)
        return events[:24]

    def _phase_for(self, entity_id: str, tick: int) -> str:
        digest = hashlib.sha256(f"{entity_id}:{tick}".encode("utf-8")).digest()
        index = digest[0] % len(self._PHASES)
        return self._PHASES[index]

    def _oscillation(self, entity_id: str, tick: int) -> float:
        digest = hashlib.sha256(f"osc:{entity_id}:{tick}".encode("utf-8")).digest()
        lane = digest[1] / 255.0
        return (lane - 0.5) * 0.22 + self._rng.uniform(-0.025, 0.025)

    def _legend_name(self, entity_id: str, tick: int, band: str) -> str:
        family = ERP_LEGEND_FAMILIES.get(band, ERP_LEGEND_FAMILIES["murmur"])
        digest = hashlib.sha256(f"legend:{band}:{entity_id}:{tick}".encode("utf-8")).digest()
        return family[digest[2] % len(family)]

    def _band_for(self, score: float) -> str | None:
        selected: str | None = None
        for threshold, band in self._BANDS:
            if score >= threshold:
                selected = band
                continue
            break
        return selected