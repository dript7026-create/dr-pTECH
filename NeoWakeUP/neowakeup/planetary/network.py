"""Recursive planetary social simulation for NeoWakeUP."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import random
from statistics import fmean

from .equations import (
    directive_solution,
    individual_activation,
    planetary_coherence,
    regional_coherence,
    relational_resonance,
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass
class EntityGenome:
    curiosity: float
    empathy: float
    agency: float
    cohesion: float
    plasticity: float
    memory_bias: float


@dataclass
class EntityMind:
    entity_id: str
    region_id: str
    genome: EntityGenome
    stress: float
    knowledge: float
    trust: float
    resources: float
    activation: float = 0.0


@dataclass
class RegionState:
    region_id: str
    entity_ids: list[str] = field(default_factory=list)
    coherence: float = 0.0
    knowledge: float = 0.0
    resource_balance: float = 0.0
    volatility: float = 0.0


@dataclass
class Directive:
    novelty: float = 0.7
    equity: float = 0.7
    resilience: float = 0.7
    speed: float = 0.6


class PlanetaryMindNetwork:
    def __init__(self, seed: int = 7):
        self._rng = random.Random(seed)
        self.tick_count = 0
        self.entities: dict[str, EntityMind] = {}
        self.regions: dict[str, RegionState] = {}
        self.exchange = 0.5
        self.volatility = 0.2

    def bootstrap(self, region_count: int = 6, entities_per_region: int = 12) -> None:
        self.entities.clear()
        self.regions.clear()
        for region_index in range(region_count):
            region_id = f"region-{region_index + 1}"
            region = RegionState(region_id=region_id)
            self.regions[region_id] = region
            for entity_index in range(entities_per_region):
                entity_id = f"{region_id}-mind-{entity_index + 1}"
                genome = EntityGenome(
                    curiosity=self._rng.uniform(0.35, 0.95),
                    empathy=self._rng.uniform(0.30, 0.90),
                    agency=self._rng.uniform(0.30, 0.95),
                    cohesion=self._rng.uniform(0.25, 0.90),
                    plasticity=self._rng.uniform(0.25, 0.90),
                    memory_bias=self._rng.uniform(0.10, 0.85),
                )
                self.entities[entity_id] = EntityMind(
                    entity_id=entity_id,
                    region_id=region_id,
                    genome=genome,
                    stress=self._rng.uniform(0.10, 0.65),
                    knowledge=self._rng.uniform(0.20, 0.80),
                    trust=self._rng.uniform(0.25, 0.75),
                    resources=self._rng.uniform(0.25, 0.90),
                )
                region.entity_ids.append(entity_id)
        self.recompute()

    def recompute(self) -> None:
        for entity in self.entities.values():
            entity.activation = individual_activation(
                entity.genome.agency,
                entity.genome.curiosity,
                entity.genome.plasticity,
                entity.stress,
            )
        regional_scores = []
        regional_knowledge = []
        for region in self.regions.values():
            minds = [self.entities[entity_id] for entity_id in region.entity_ids]
            if not minds:
                region.coherence = 0.0
                region.knowledge = 0.0
                region.resource_balance = 0.0
                region.volatility = 0.0
                continue
            resonance_values = []
            for index, entity in enumerate(minds):
                partner = minds[(index + 1) % len(minds)]
                conflict = abs(entity.activation - partner.activation)
                resonance_values.append(relational_resonance(entity.trust, entity.genome.empathy, conflict))
            region.knowledge = fmean(entity.knowledge for entity in minds)
            resource_avg = fmean(entity.resources for entity in minds)
            region.resource_balance = 1.0 - fmean(abs(entity.resources - resource_avg) for entity in minds)
            region.volatility = fmean(abs(entity.stress - entity.activation) for entity in minds)
            region.coherence = regional_coherence(fmean(resonance_values), region.knowledge, region.resource_balance)
            regional_scores.append(region.coherence)
            regional_knowledge.append(region.knowledge)
        self.exchange = fmean(regional_knowledge) if regional_knowledge else 0.0
        self.volatility = fmean(region.volatility for region in self.regions.values()) if self.regions else 0.0
        self._planetary_coherence = planetary_coherence(fmean(regional_scores) if regional_scores else 0.0, self.exchange, self.volatility)

    @property
    def planetary_coherence_value(self) -> float:
        return getattr(self, "_planetary_coherence", 0.0)

    def step(self, directive: Directive) -> dict:
        self.tick_count += 1
        for entity in self.entities.values():
            novelty_drive = directive.novelty * entity.genome.curiosity
            equity_damping = directive.equity * entity.genome.empathy
            resilience_support = directive.resilience * entity.genome.cohesion
            speed_pressure = directive.speed * entity.genome.agency
            entity.knowledge = _clamp(entity.knowledge + 0.06 * novelty_drive + 0.02 * resilience_support - 0.03 * entity.stress)
            entity.resources = _clamp(entity.resources + 0.03 * resilience_support - 0.02 * speed_pressure + 0.02 * equity_damping)
            entity.trust = _clamp(entity.trust + 0.04 * equity_damping - 0.03 * speed_pressure + 0.01 * entity.genome.memory_bias)
            entity.stress = _clamp(entity.stress + 0.03 * speed_pressure - 0.04 * resilience_support - 0.02 * equity_damping)
        self.recompute()
        return self.solve(directive)

    def solve(self, directive: Directive) -> dict:
        coherence = self.planetary_coherence_value
        novelty = fmean(entity.genome.curiosity for entity in self.entities.values()) if self.entities else 0.0
        solution_score = directive_solution(coherence, novelty, directive.equity, directive.resilience, directive.speed)
        return {
            "tick": self.tick_count,
            "planetary_coherence": round(coherence, 6),
            "exchange": round(self.exchange, 6),
            "volatility": round(self.volatility, 6),
            "solution_score": round(solution_score, 6),
            "directive": asdict(directive),
            "regions": {
                region_id: {
                    "coherence": round(region.coherence, 6),
                    "knowledge": round(region.knowledge, 6),
                    "resource_balance": round(region.resource_balance, 6),
                    "volatility": round(region.volatility, 6),
                }
                for region_id, region in self.regions.items()
            },
        }

    def export_state(self) -> dict:
        return {
            "tick_count": self.tick_count,
            "exchange": self.exchange,
            "volatility": self.volatility,
            "entities": {
                entity_id: {
                    "entity_id": entity.entity_id,
                    "region_id": entity.region_id,
                    "genome": asdict(entity.genome),
                    "stress": entity.stress,
                    "knowledge": entity.knowledge,
                    "trust": entity.trust,
                    "resources": entity.resources,
                    "activation": entity.activation,
                }
                for entity_id, entity in self.entities.items()
            },
            "regions": {region_id: asdict(region) for region_id, region in self.regions.items()},
        }

    def import_state(self, payload: dict) -> bool:
        try:
            entities = payload["entities"]
            regions = payload["regions"]
        except (KeyError, TypeError):
            return False
        imported_entities = {}
        for entity_id, raw in entities.items():
            genome = EntityGenome(**raw["genome"])
            imported_entities[entity_id] = EntityMind(
                entity_id=raw["entity_id"],
                region_id=raw["region_id"],
                genome=genome,
                stress=float(raw["stress"]),
                knowledge=float(raw["knowledge"]),
                trust=float(raw["trust"]),
                resources=float(raw["resources"]),
                activation=float(raw.get("activation", 0.0)),
            )
        imported_regions = {region_id: RegionState(**raw) for region_id, raw in regions.items()}
        self.entities = imported_entities
        self.regions = imported_regions
        self.tick_count = int(payload.get("tick_count", 0))
        self.exchange = float(payload.get("exchange", 0.5))
        self.volatility = float(payload.get("volatility", 0.2))
        self.recompute()
        return True


class PlanetaryMindStore:
    def __init__(self, path: str):
        self.path = Path(path)

    def load_into(self, network: PlanetaryMindNetwork) -> bool:
        if not self.path.exists():
            return False
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return network.import_state(payload)

    def save(self, network: PlanetaryMindNetwork) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(network.export_state(), indent=2, sort_keys=True), encoding="utf-8")