from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Plane(str, Enum):
    UP = "up"
    LAND = "land"
    LOW = "low"
    ETHER = "ether"


class LifeForm(str, Enum):
    GOURD_INFANT = "gourd_infant"
    LANDBORNE = "landborne"
    ETHERIC_CURRENT = "etheric_current"


class Alignment(str, Enum):
    GRAMATOS = "gramatos"
    MORTAL = "mortal"
    SORROW = "sorrow"


@dataclass
class AmnioticGourd:
    capacity: float = 180.0
    stored_blood: float = 0.0
    shell_integrity: float = 1.0
    infant_charge: float = 0.0

    def collect(self, amount: float) -> float:
        free_space = max(0.0, self.capacity - self.stored_blood)
        captured = min(amount, free_space)
        self.stored_blood += captured
        return captured

    def decant(self, amount: float) -> float:
        poured = min(amount, self.stored_blood)
        self.stored_blood -= poured
        return poured

    def incubate(self, force: float) -> None:
        self.infant_charge = min(100.0, self.infant_charge + force)
        if force > 0:
            self.shell_integrity = max(0.0, self.shell_integrity - force / 180.0)

    @property
    def ready_to_hatch(self) -> bool:
        return self.infant_charge >= 100.0 or self.shell_integrity <= 0.12


@dataclass
class BloodReservoir:
    current: float = 120.0
    maximum: float = 120.0

    def spend(self, amount: float) -> float:
        spent = min(amount, self.current)
        self.current -= spent
        return spent

    def restore(self, amount: float) -> float:
        restored = min(amount, self.maximum - self.current)
        self.current += restored
        return restored


@dataclass
class PlayerState:
    name: str
    plane: Plane = Plane.LAND
    life_form: LifeForm = LifeForm.LANDBORNE
    alignment: Alignment = Alignment.MORTAL
    blood: BloodReservoir = field(default_factory=BloodReservoir)
    health: float = 100.0
    stamina: float = 100.0
    mental_acuity: float = 100.0
    rupture_progress: float = 0.0
    gourd: AmnioticGourd = field(default_factory=AmnioticGourd)
    spilled_blood_pool: float = 0.0

    def sync_derived_stats(self) -> None:
        blood_ratio = self.blood.current / self.blood.maximum if self.blood.maximum else 0.0
        self.stamina = max(20.0, 40.0 + blood_ratio * 60.0)
        self.mental_acuity = max(10.0, 15.0 + blood_ratio * 85.0)
        if self.life_form == LifeForm.GOURD_INFANT:
            self.health = min(self.health, 35.0)
            self.stamina = min(self.stamina, 30.0)
        elif self.life_form == LifeForm.ETHERIC_CURRENT:
            self.health = 0.0

    def spill_blood(self, amount: float, into_gourd: bool = True) -> float:
        spilled = self.blood.spend(amount)
        self.spilled_blood_pool += spilled
        if into_gourd:
            captured = self.gourd.collect(spilled * 0.65)
            self.spilled_blood_pool = max(0.0, self.spilled_blood_pool - captured)
        self.sync_derived_stats()
        return spilled

    def collect_field_blood(self, amount: float) -> float:
        collectible = min(amount, self.spilled_blood_pool)
        restored = self.blood.restore(collectible * 0.7)
        excess = collectible - restored
        if excess > 0:
            self.gourd.collect(excess)
        self.spilled_blood_pool = max(0.0, self.spilled_blood_pool - collectible)
        self.sync_derived_stats()
        return restored

    def blood_burn(self, cost: float) -> float:
        spent = self.blood.spend(cost)
        self.stamina = min(100.0, self.stamina + spent * 0.75)
        self.sync_derived_stats()
        return spent

    def die(self) -> None:
        self.spill_blood(self.blood.current * 0.55, into_gourd=True)
        self.plane = Plane.ETHER
        self.life_form = LifeForm.ETHERIC_CURRENT
        self.alignment = Alignment.MORTAL
        self.rupture_progress = 0.0
        self.sync_derived_stats()

    def route_from_shrine(self, target_plane: Plane) -> None:
        if target_plane not in {Plane.UP, Plane.LAND, Plane.LOW, Plane.ETHER}:
            raise ValueError("invalid shrine target")
        self.plane = Plane.ETHER if target_plane != Plane.ETHER else target_plane
        self.life_form = LifeForm.ETHERIC_CURRENT
        if target_plane == Plane.UP:
            self.alignment = Alignment.GRAMATOS
        elif target_plane == Plane.LOW:
            self.alignment = Alignment.SORROW
        else:
            self.alignment = Alignment.MORTAL
        self.sync_derived_stats()

    def descend_into_land(self) -> None:
        self.plane = Plane.LAND
        self.life_form = LifeForm.GOURD_INFANT
        self.rupture_progress = 0.0
        self.health = 30.0
        self.gourd.infant_charge = 0.0
        self.gourd.shell_integrity = max(0.25, self.gourd.shell_integrity)
        self.sync_derived_stats()

    def struggle_in_gourd(self, effort: float) -> float:
        if self.life_form != LifeForm.GOURD_INFANT:
            return 0.0
        self.gourd.incubate(effort)
        self.rupture_progress = min(100.0, self.rupture_progress + effort)
        return self.rupture_progress

    def hatch_from_gourd(self) -> bool:
        if self.life_form != LifeForm.GOURD_INFANT or not self.gourd.ready_to_hatch:
            return False
        self.life_form = LifeForm.LANDBORNE
        self.health = 70.0
        self.blood.restore(self.gourd.decant(40.0))
        self.rupture_progress = 100.0
        self.sync_derived_stats()
        return True


def create_starting_player(name: str) -> PlayerState:
    player = PlayerState(name=name)
    player.sync_derived_stats()
    return player