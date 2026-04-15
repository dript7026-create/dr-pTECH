from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "double_blade_everglades_project.json"
OUTPUT_PATH = ROOT / "generated" / "progression_manifest.json"


def stable_hash(text: str) -> int:
    value = 17
    for char in text:
        value = (value * 31 + ord(char)) % 1_000_003
    return value


def load_source() -> dict:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def build_blades(source: dict) -> list[dict]:
    forms = source["blade_generation"]["forms"]
    materials = source["blade_generation"]["materials"]
    edges = source["blade_generation"]["edge_profiles"]
    blades: list[dict] = []
    for form in forms:
        handedness = "double" if form in {"amber_halberd", "double_stem", "bog_lance"} else "single"
        weight_class = "heavy" if form in {"graft_axe", "amber_halberd", "double_stem"} else "mid"
        for material in materials:
            for edge in edges:
                blade_id = f"{material}_{edge}_{form}"
                blade_hash = stable_hash(blade_id)
                weight_rating = round(1.2 + (blade_hash % 240) / 100 + (0.8 if handedness == "double" else 0.0), 2)
                movement_arc_degrees = 38 + (blade_hash % 109)
                movement_arc_profile = [
                    round(0.18 + ((blade_hash // 3) % 17) / 20, 2),
                    round(0.34 + ((blade_hash // 11) % 19) / 18, 2),
                    round(0.22 + ((blade_hash // 23) % 13) / 20, 2),
                ]
                blades.append(
                    {
                        "id": blade_id,
                        "name": f"{material.replace('_', ' ').title()} {edge.title()} {form.replace('_', ' ').title()}",
                        "handedness": handedness,
                        "weight_class": weight_class,
                        "material": material,
                        "edge_profile": edge,
                        "form": form,
                        "weight_rating": weight_rating,
                        "movement_arc_degrees": movement_arc_degrees,
                        "movement_arc_profile": movement_arc_profile,
                        "swing_recovery_seconds": round(0.24 + weight_rating * 0.08 + ((blade_hash // 7) % 12) / 100, 2),
                        "pace_response_curve": {
                            "tempo_bias": round(0.75 + ((blade_hash // 5) % 37) / 50, 2),
                            "distance_bias": round(0.55 + ((blade_hash // 13) % 31) / 40, 2),
                            "rootknot_bias": round(0.35 + ((blade_hash // 29) % 27) / 45, 2),
                        },
                    }
                )
    return blades


def build_items(source: dict) -> list[dict]:
    items: list[dict] = []
    slot = 0
    for pool_name, names in source["item_pools"].items():
        for name in names:
            items.append(
                {
                    "id": name,
                    "name": name.replace("_", " ").title(),
                    "pool": pool_name,
                    "dpad_slot_hint": slot % 4,
                }
            )
            slot += 1
    return items


def build_skills(source: dict) -> list[dict]:
    skills: list[dict] = []
    face_button_cycle = ["south", "east", "west", "north"]
    skill_index = 0
    for act_index, act in enumerate(source["progression"]["acts"], start=1):
        for unlock in act["new_skill_unlocks"]:
            skills.append(
                {
                    "id": unlock,
                    "name": unlock.replace("_", " ").title(),
                    "unlock_act": act["id"],
                    "skill_page": skill_index // 4,
                    "face_button": face_button_cycle[skill_index % 4],
                    "precision_scalar": round(0.8 + act_index * 0.07, 2),
                }
            )
            skill_index += 1
    return skills


def build_rootknots(source: dict) -> list[dict]:
    total = source["catalog_targets"]["rootknots"]
    half_diagonal = math.sqrt(source["project"]["world_area_sqft"] / 2.0)
    start = -half_diagonal
    end = half_diagonal
    step = (end - start) / (total - 1)
    rootknots: list[dict] = []
    acts = source["progression"]["acts"]
    for index in range(total):
        coord = start + step * index
        progress = index / (total - 1)
        act = next(
            current
            for current in acts
            if current["distance_band"][0] <= progress <= current["distance_band"][1]
        )
        rootknots.append(
            {
                "id": f"rootknot_{index + 1:02d}",
                "name": f"RootKnot {index + 1:02d}",
                "diamond_position": {"x": round(coord, 2), "y": round(abs(coord) * 0.48, 2)},
                "progress": round(progress, 3),
                "act": act["id"],
                "functions": ["rest", "fast_travel", "growth_hub"],
            }
        )
    return rootknots


def assign_rootknot_milestones(rootknots: list[dict], acts: list[dict], skills: list[dict]) -> list[dict]:
    rootknot_index = {rootknot["id"]: rootknot for rootknot in rootknots}
    skills_by_act: dict[str, list[dict]] = {}
    for skill in skills:
        skills_by_act.setdefault(skill["unlock_act"], []).append(skill)

    for act_position, act in enumerate(acts):
        act_rootknots = [rootknot for rootknot in rootknots if rootknot["act"] == act["id"]]
        act_skills = skills_by_act.get(act["id"], [])
        total_act_rootknots = len(act_rootknots)

        for local_index, rootknot in enumerate(act_rootknots):
            milestone_type = "recovery"
            if act_position == 0 and local_index == 0:
                milestone_type = "origin"
            elif act_position == len(acts) - 1 and local_index == total_act_rootknots - 1:
                milestone_type = "final_ascent"
            elif local_index == total_act_rootknots - 1:
                milestone_type = "boss_gate"
            elif local_index == 0:
                milestone_type = "act_entry"

            rootknot_index[rootknot["id"]]["milestone_type"] = milestone_type
            rootknot_index[rootknot["id"]]["unlocks"] = []

        if not act_skills or not act_rootknots:
            continue

        skill_slots = max(1, total_act_rootknots - 1)
        for skill_index, skill in enumerate(act_skills):
            target_slot = min(skill_slots - 1, int(skill_index * skill_slots / len(act_skills)))
            target_rootknot = act_rootknots[target_slot]
            rootknot_index[target_rootknot["id"]]["unlocks"].append(skill["id"])

    cumulative_skills = 0
    for rootknot in rootknots:
        cumulative_skills += len(rootknot.get("unlocks", []))
        rootknot["cumulative_skill_unlocks"] = cumulative_skills
        rootknot["growth_rating"] = round(0.15 + cumulative_skills * 0.05 + rootknot["progress"] * 0.35, 2)

    return rootknots


def build_enemy_varieties(source: dict) -> list[dict]:
    families = source["enemy_generation"]["families"]
    mutations = source["enemy_generation"]["mutations"]
    enemies: list[dict] = []
    acts = source["progression"]["acts"]
    for family_index, family in enumerate(families):
        family_act = acts[min(len(acts) - 1, family_index // 2)]["id"]
        for mutation_index, mutation in enumerate(mutations):
            enemy_id = f"{family}_{mutation}"
            enemy_hash = stable_hash(enemy_id)
            severity = round(0.18 + (mutation_index / (len(mutations) - 1)) * 0.74, 2)
            enemies.append(
                {
                    "id": enemy_id,
                    "name": f"{mutation.title()} {family.replace('_', ' ').title()}",
                    "family": family,
                    "mutation": mutation,
                    "recommended_act": family_act,
                    "severity": severity,
                    "spawn_profile": {
                        "base_weight": round(0.2 + (enemy_hash % 71) / 100, 2),
                        "pack_bias": round(0.3 + ((enemy_hash // 5) % 41) / 50, 2),
                        "ambush_bias": round(0.15 + ((enemy_hash // 19) % 33) / 60, 2),
                    },
                    "behavior_profile": {
                        "aggression": round(0.25 + ((enemy_hash // 11) % 59) / 80, 2),
                        "flank_bias": round(0.15 + ((enemy_hash // 17) % 43) / 70, 2),
                        "retreat_threshold": round(0.1 + ((enemy_hash // 31) % 37) / 100, 2),
                    },
                    "threat_response_curve": {
                        "tempo_gain": round(0.8 + ((enemy_hash // 7) % 29) / 30, 2),
                        "distance_gain": round(0.55 + ((enemy_hash // 23) % 31) / 40, 2),
                        "fatigue_gain": round(0.4 + ((enemy_hash // 37) % 27) / 45, 2),
                    },
                }
            )
    return enemies


def build_progression(source: dict) -> dict:
    blades = build_blades(source)
    items = build_items(source)
    skills = build_skills(source)
    rootknots = build_rootknots(source)
    rootknots = assign_rootknot_milestones(rootknots, source["progression"]["acts"], skills)
    enemies = build_enemy_varieties(source)
    acts = []
    for act in source["progression"]["acts"]:
        act_rootknot_entries = [rk for rk in rootknots if rk["act"] == act["id"]]
        act_rootknots = [rk["id"] for rk in act_rootknot_entries]
        act_skills = [skill["id"] for skill in skills if skill["unlock_act"] == act["id"]]
        act_enemies = [enemy["id"] for enemy in enemies if enemy["recommended_act"] == act["id"]]
        acts.append(
            {
                **act,
                "rootknots": act_rootknots,
                "skills": act_skills,
                "skill_unlock_rootknots": [
                    rootknot["id"] for rootknot in act_rootknot_entries if rootknot.get("unlocks")
                ],
                "recommended_power_floor": round(0.2 + len(act_skills) * 0.06 + act["pressure"] * 0.4, 2),
                "enemy_count": len(act_enemies),
                "enemy_sample": act_enemies[:8],
            }
        )

    return {
        "project": source["project"],
        "fiction": source["fiction"],
        "controller_contract": source["controller_contract"],
        "runtime_contract": {
            "pace_formula": "(character_traverse_rate / max(idle_time_between_progressive_actions, 0.35)) * distance_to_nearest_rootknot - distance_from_previous_rootknot",
            "save_policy": {
                "autosave_enabled": True,
                "rootknot_checkpoint_save": True,
                "manual_save_allowed": True,
            },
            "run_variation": {
                "enemy_spawn_randomized_per_run": True,
                "behavior_pattern_randomized_per_run": True,
            },
        },
        "catalog_summary": {
            "blade_variants": len(blades),
            "items": len(items),
            "skills": len(skills),
            "enemy_varieties": len(enemies),
            "rootknots": len(rootknots),
        },
        "progression": {
            "acts": acts,
            "rootknots": rootknots,
            "skill_unlock_order": [
                {
                    "skill_id": skill["id"],
                    "unlock_act": skill["unlock_act"],
                    "face_button": skill["face_button"],
                }
                for skill in skills
            ],
            "final_destination": {
                "boss": source["fiction"]["final_boss"],
                "furthest_rootknot": rootknots[-1]["id"],
            },
        },
        "items": items,
        "skills": skills,
        "blades": blades,
        "enemy_varieties": enemies,
    }


def main() -> None:
    source = load_source()
    manifest = build_progression(source)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "manifest": str(OUTPUT_PATH),
                "blade_variants": manifest["catalog_summary"]["blade_variants"],
                "items": manifest["catalog_summary"]["items"],
                "skills": manifest["catalog_summary"]["skills"],
                "enemy_varieties": manifest["catalog_summary"]["enemy_varieties"],
                "rootknots": manifest["catalog_summary"]["rootknots"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()