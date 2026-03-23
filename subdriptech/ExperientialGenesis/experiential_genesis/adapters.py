from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Protocol

from .authorization import AuthorizationProfile, MutationDomain, safe_profile, AuthorizationScope
from .coherency import CoherencyField, CoherencySignal


@dataclass(frozen=True)
class Mutation:
    domain: MutationDomain
    key: str
    value: float


@dataclass(frozen=True)
class AdapterSnapshot:
    name: str
    summary: str
    signals: List[CoherencySignal]
    metrics: Dict[str, float]


class ExperientialAdapter(Protocol):
    name: str
    authorization: AuthorizationProfile

    def snapshot(self) -> AdapterSnapshot:
        ...

    def propose_mutations(self, field: CoherencyField) -> Iterable[Mutation]:
        ...

    def apply(self, mutation: Mutation) -> None:
        ...


@dataclass
class BaseAdapter:
    name: str
    authorization: AuthorizationProfile

    def apply(self, mutation: Mutation) -> None:
        if not self.authorization.allows(mutation.domain):
            raise PermissionError(f"Adapter {self.name} is not authorized for {mutation.domain.value}")
        self._apply_mutation(mutation)

    def _apply_mutation(self, mutation: Mutation) -> None:
        raise NotImplementedError


@dataclass
class IllusionCanvasAdapter(BaseAdapter):
    bond_flux: float = 0.56
    particle_density: float = 0.44
    popups_per_minute: float = 0.30

    def snapshot(self) -> AdapterSnapshot:
        return AdapterSnapshot(
            name=self.name,
            summary="IllusionCanvas runtime shell",
            signals=[
                CoherencySignal("bond_flux", 8.4, self.bond_flux, 0.42, 0.92),
                CoherencySignal("particle_density", 6.8, self.particle_density, 0.38, 0.86),
            ],
            metrics={
                "bond_flux": self.bond_flux,
                "particle_density": self.particle_density,
                "popups_per_minute": self.popups_per_minute,
            },
        )

    def propose_mutations(self, field: CoherencyField) -> Iterable[Mutation]:
        yield Mutation(MutationDomain.PARTICLES, "particle_density", max(0.1, min(1.0, field.resonance)))
        yield Mutation(MutationDomain.RENDER, "popups_per_minute", max(0.05, min(0.9, field.tension + 0.15)))

    def _apply_mutation(self, mutation: Mutation) -> None:
        if mutation.key == "particle_density":
            self.particle_density = mutation.value
        elif mutation.key == "popups_per_minute":
            self.popups_per_minute = mutation.value


@dataclass
class ArchesAndAngelsAdapter(BaseAdapter):
    campaign_stability: float = 0.50
    agenda_heat: float = 0.66
    mission_pressure: float = 0.62
    mission_focus: float = 0.40

    def snapshot(self) -> AdapterSnapshot:
        return AdapterSnapshot(
            name=self.name,
            summary="ArchesAndAngels strategy shell",
            signals=[
                CoherencySignal("campaign_stability", 5.4, 1.0 - self.campaign_stability, 0.47, 0.91),
                CoherencySignal("agenda_heat", 9.1, self.agenda_heat, 0.62, 0.88),
                CoherencySignal("mission_pressure", 7.7, self.mission_pressure, 0.53, 0.79),
            ],
            metrics={
                "campaign_stability": self.campaign_stability,
                "agenda_heat": self.agenda_heat,
                "mission_pressure": self.mission_pressure,
                "mission_focus": self.mission_focus,
            },
        )

    def propose_mutations(self, field: CoherencyField) -> Iterable[Mutation]:
        yield Mutation(MutationDomain.STATE, "campaign_stability", max(0.1, min(0.95, field.coherence_index)))
        yield Mutation(MutationDomain.MISSIONS, "mission_focus", max(0.05, min(1.0, field.tension + 0.2)))

    def _apply_mutation(self, mutation: Mutation) -> None:
        if mutation.key == "campaign_stability":
            self.campaign_stability = mutation.value
        elif mutation.key == "mission_focus":
            self.mission_focus = mutation.value


def demo_adapters() -> List[ExperientialAdapter]:
    return [
        IllusionCanvasAdapter(name="illusioncanvas", authorization=safe_profile(AuthorizationScope.ENGINE)),
        ArchesAndAngelsAdapter(name="archesandangels", authorization=safe_profile(AuthorizationScope.SIMULATION)),
    ]


def apply_demo_preset(adapters: List[ExperientialAdapter], preset: str) -> List[ExperientialAdapter]:
    if preset == "storm":
        for adapter in adapters:
            if isinstance(adapter, IllusionCanvasAdapter):
                adapter.bond_flux = 0.82
                adapter.particle_density = 0.74
                adapter.popups_per_minute = 0.58
            elif isinstance(adapter, ArchesAndAngelsAdapter):
                adapter.campaign_stability = 0.31
                adapter.agenda_heat = 0.87
                adapter.mission_pressure = 0.86
                adapter.mission_focus = 0.73
    elif preset == "calm":
        for adapter in adapters:
            if isinstance(adapter, IllusionCanvasAdapter):
                adapter.bond_flux = 0.34
                adapter.particle_density = 0.22
                adapter.popups_per_minute = 0.12
            elif isinstance(adapter, ArchesAndAngelsAdapter):
                adapter.campaign_stability = 0.76
                adapter.agenda_heat = 0.29
                adapter.mission_pressure = 0.36
                adapter.mission_focus = 0.24
    return adapters