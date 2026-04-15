from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EnemyOutfitPackage:
    name: str
    weapon: str
    pressure_bias: str
    telegraph_clarity: float


@dataclass(frozen=True)
class EnemySchism:
    id: str
    title: str
    mastery_targets: tuple[str, ...]
    outfit_packages: tuple[EnemyOutfitPackage, ...]


@dataclass
class CombatTelemetry:
    parry_success_rate: float = 0.0
    late_dodge_rate: float = 0.0
    overcommit_rate: float = 0.0
    heal_panic_rate: float = 0.0
    crowd_separation_rate: float = 0.0
    ranged_interrupt_rate: float = 0.0
    boss_retry_count: int = 0
    dominant_style_tags: list[str] = field(default_factory=list)


@dataclass
class EncounterPacket:
    chapter: str
    schism_id: str
    schism_title: str
    outfit: str
    enemy_count: int
    overlap_level: int
    reinforcement: bool
    notes: str


RENDLINE = EnemySchism(
    id="rendline",
    title="Rendline",
    mastery_targets=("close_pressure_timing", "short_window_punish", "crowd_collapse"),
    outfit_packages=(
        EnemyOutfitPackage("knife_rush", "hook knives", "aggressive", 0.8),
        EnemyOutfitPackage("wire_lunge", "tendon wire", "flank", 0.65),
        EnemyOutfitPackage("buckler_harrier", "split buckler", "counter", 0.72),
    ),
)

LATTICE = EnemySchism(
    id="lattice",
    title="Lattice",
    mastery_targets=("angle_breaking", "priority_collapse", "guard_split"),
    outfit_packages=(
        EnemyOutfitPackage("relay_wall", "tower shield", "formation", 0.82),
        EnemyOutfitPackage("oath_pike", "relay pike", "formation", 0.74),
        EnemyOutfitPackage("seal_hook", "seal hook", "pin", 0.7),
    ),
)

MIRECAST = EnemySchism(
    id="mirecast",
    title="Mirecast",
    mastery_targets=("hazard_reading", "anti_caster_pathing", "ranged_interrupt"),
    outfit_packages=(
        EnemyOutfitPackage("curse_sling", "curse sling", "zoning", 0.76),
        EnemyOutfitPackage("basin_bell", "basin bell", "delay", 0.68),
        EnemyOutfitPackage("rot_scroll", "rot scrolls", "debuff", 0.7),
    ),
)

IDOLWROUGHT = EnemySchism(
    id="idolwrought",
    title="Idolwrought",
    mastery_targets=("stamina_economy", "posture_break", "greed_control"),
    outfit_packages=(
        EnemyOutfitPackage("bell_maul", "bell maul", "heavy", 0.84),
        EnemyOutfitPackage("wax_fist", "wax fist", "trap", 0.72),
        EnemyOutfitPackage("judgment_ram", "judgment ram", "burst", 0.66),
    ),
)

MIRRORBLOOD = EnemySchism(
    id="mirrorblood",
    title="Mirrorblood",
    mastery_targets=("mixup_discipline", "tempo_masking", "route_variation"),
    outfit_packages=(
        EnemyOutfitPackage("habit_breaker", "mirrored blade", "counterstyle", 0.62),
        EnemyOutfitPackage("feint_rebuttal", "mirrored spear", "feint", 0.58),
        EnemyOutfitPackage("panic_punisher", "mirrored wand", "punish", 0.6),
    ),
)


def build_chapter_plan(telemetry: CombatTelemetry) -> list[EncounterPacket]:
    packets: list[EncounterPacket] = []
    weakness_score = 0
    if telemetry.late_dodge_rate > 0.33:
        weakness_score += 1
    if telemetry.overcommit_rate > 0.28:
        weakness_score += 1
    if telemetry.heal_panic_rate > 0.25:
        weakness_score += 1
    if telemetry.boss_retry_count >= 3:
        weakness_score += 1

    overlap_level = 1 if weakness_score >= 2 else 2
    reinforcement = weakness_score >= 2

    packets.append(_make_packet("Gourdwake Breach", RENDLINE, telemetry, overlap_level, reinforcement))
    packets.append(_make_packet("Veinmarket Mile", LATTICE, telemetry, overlap_level, reinforcement))
    packets.append(_make_packet("Flood Archive of Lillypads", MIRECAST, telemetry, overlap_level, reinforcement))
    packets.append(_make_packet("Token Tong Causeway", IDOLWROUGHT, telemetry, overlap_level, reinforcement))
    packets.append(_make_packet("Oshin Ishtasha Tribunal", MIRRORBLOOD, telemetry, overlap_level + 1, False))
    return packets


def _make_packet(
    chapter: str,
    schism: EnemySchism,
    telemetry: CombatTelemetry,
    overlap_level: int,
    reinforcement: bool,
) -> EncounterPacket:
    package = schism.outfit_packages[0]

    if schism.id == "rendline" and telemetry.late_dodge_rate <= 0.2:
        package = schism.outfit_packages[1]
    elif schism.id == "lattice" and telemetry.crowd_separation_rate >= 0.65:
        package = schism.outfit_packages[2]
    elif schism.id == "mirecast" and telemetry.ranged_interrupt_rate >= 0.55:
        package = schism.outfit_packages[1]
    elif schism.id == "idolwrought" and telemetry.overcommit_rate <= 0.18:
        package = schism.outfit_packages[2]
    elif schism.id == "mirrorblood":
        if "panic_healer" in telemetry.dominant_style_tags:
            package = schism.outfit_packages[2]
        elif "parry_hungry" in telemetry.dominant_style_tags:
            package = schism.outfit_packages[0]
        else:
            package = schism.outfit_packages[1]

    notes = (
        f"Teaches {', '.join(schism.mastery_targets[:2])}. "
        f"Outfit package '{package.name}' keeps pressure_bias={package.pressure_bias}."
    )
    if reinforcement:
        notes += " Insert one simpler isolation encounter before the main room."

    enemy_count = 3 if overlap_level == 1 else 5
    if schism.id in {"idolwrought", "mirrorblood"}:
        enemy_count = 1 if schism.id == "mirrorblood" else 2

    return EncounterPacket(
        chapter=chapter,
        schism_id=schism.id,
        schism_title=schism.title,
        outfit=package.weapon,
        enemy_count=enemy_count,
        overlap_level=overlap_level,
        reinforcement=reinforcement,
        notes=notes,
    )