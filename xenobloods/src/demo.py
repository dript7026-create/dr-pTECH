from xenobloods_adaptive_director import CombatTelemetry, build_chapter_plan
from xenobloods_systems import Plane, create_starting_player


def main() -> None:
    player = create_starting_player("Ishtasha")
    print("=== XenoBloods Systems Demo ===")
    print(f"Start: plane={player.plane.value}, form={player.life_form.value}, blood={player.blood.current:.1f}")

    player.spill_blood(32.0)
    print(
        "After blood spill: "
        f"blood={player.blood.current:.1f}, field_pool={player.spilled_blood_pool:.1f}, gourd={player.gourd.stored_blood:.1f}"
    )

    player.die()
    print(f"After death: plane={player.plane.value}, form={player.life_form.value}, acuity={player.mental_acuity:.1f}")

    player.route_from_shrine(Plane.LAND)
    player.descend_into_land()
    while not player.hatch_from_gourd():
        player.struggle_in_gourd(26.0)
        print(
            "Rebirth struggle: "
            f"rupture={player.rupture_progress:.1f}, shell={player.gourd.shell_integrity:.2f}, charge={player.gourd.infant_charge:.1f}"
        )

    print(
        "After hatching: "
        f"plane={player.plane.value}, form={player.life_form.value}, blood={player.blood.current:.1f}, stamina={player.stamina:.1f}"
    )

    telemetry = CombatTelemetry(
        parry_success_rate=0.42,
        late_dodge_rate=0.38,
        overcommit_rate=0.31,
        heal_panic_rate=0.21,
        crowd_separation_rate=0.47,
        ranged_interrupt_rate=0.63,
        boss_retry_count=4,
        dominant_style_tags=["parry_hungry", "launcher_fisher"],
    )
    packets = build_chapter_plan(telemetry)
    print("\n=== Adaptive Encounter Packets ===")
    for packet in packets:
        print(
            f"- {packet.chapter}: schism={packet.schism_title}, outfit={packet.outfit}, "
            f"count={packet.enemy_count}, overlap={packet.overlap_level}, reinforcement={packet.reinforcement}"
        )
        print(f"  {packet.notes}")


if __name__ == "__main__":
    main()