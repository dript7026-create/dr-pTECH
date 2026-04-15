from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from doengine_xenobloods_bridge import create_bridge


def _stub_package() -> dict:
    bindings = {
        "player_life_landborne": {"object_id": "player_life_landborne", "kind": "player-life-state", "label": "Landborne", "life_form": "landborne"},
        "player_life_gourd_infant": {"object_id": "player_life_gourd_infant", "kind": "player-life-state", "label": "Gourd Infant", "life_form": "gourd_infant"},
        "player_life_etheric_current": {"object_id": "player_life_etheric_current", "kind": "player-life-state", "label": "Etheric Current", "life_form": "etheric_current"},
        "encounter_scarab_child": {"object_id": "encounter_scarab_child", "kind": "encounter-preview", "label": "Scarab Child", "actor_id": "scarab_child_acolyte"},
        "encounter_lattice_ward": {"object_id": "encounter_lattice_ward", "kind": "encounter-preview", "label": "Lattice Ward", "actor_id": "lattice_ward"},
        "boss_lahgroid": {"object_id": "boss_lahgroid", "kind": "boss-preview", "label": "Lahgroid", "actor_id": "lahgroid_hierophant"},
        "sewer_preview_gate": {"object_id": "sewer_preview", "kind": "future-biome-preview", "label": "Sewer Preview", "unlock_flag": "sewer_unlocked"},
    }
    for index, plane in enumerate(["up", "low", "land"], start=1):
        bindings[f"soul_shrine_{index:02d}"] = {
            "object_id": f"shrine_post_{index}",
            "kind": "shrine-marker",
            "label": f"Soul Shrine {index}",
            "plane_target": plane,
        }
    for index in range(1, 7):
        bindings[f"village_house_{index:02d}"] = {
            "object_id": f"house_{index:02d}",
            "kind": "village-house",
            "label": f"Village House {index}",
        }
    return {"gameplay_bindings": bindings}


def test_bridge_builds_demo_states_with_lifecycle_and_boss_progression() -> None:
    bridge = create_bridge(_stub_package())

    demo_states = bridge.build_demo_states()

    checkpoint_ids = [entry["save_name"] for entry in demo_states]
    assert checkpoint_ids == [
        "landborne_entry",
        "ether_recall",
        "gourd_incubation",
        "landborne_reborn",
        "boss_intro",
        "boss_clash",
        "boss_defeat",
    ]
    life_forms = {entry["gameplay_state"]["player"]["life_form"] for entry in demo_states}
    assert {"landborne", "gourd_infant", "etheric_current"}.issubset(life_forms)

    boss_intro = next(entry for entry in demo_states if entry["save_name"] == "boss_intro")
    boss_clash = next(entry for entry in demo_states if entry["save_name"] == "boss_clash")
    boss_defeat = next(entry for entry in demo_states if entry["save_name"] == "boss_defeat")

    assert boss_intro["gameplay_state"]["demo"]["boss_stage"] == "intro"
    assert boss_intro["gameplay_state"]["demo"]["current_actor_id"] == "lahgroid_hierophant"
    assert boss_clash["gameplay_state"]["demo"]["boss_health"] < boss_intro["gameplay_state"]["demo"]["boss_health"]
    assert boss_defeat["gameplay_state"]["demo"]["boss_stage"] == "defeated"
    assert boss_defeat["gameplay_state"]["world"]["boss_defeated"] is True


def test_bridge_scene_state_highlights_active_life_state_and_boss() -> None:
    bridge = create_bridge(_stub_package())
    demo_states = bridge.build_demo_states()
    bindings = _stub_package()["gameplay_bindings"]

    land_scene_state = bridge.build_scene_state(demo_states[0]["gameplay_state"], bindings)
    land_billboards = {entry["id"]: entry for entry in land_scene_state["billboards"]}
    assert land_billboards["player_life_landborne"]["width"] > land_billboards["player_life_gourd_infant"]["width"]

    boss_scene_state = bridge.build_scene_state(demo_states[4]["gameplay_state"], bindings)
    boss_billboards = {entry["id"]: entry for entry in boss_scene_state["billboards"]}
    assert boss_billboards["boss_lahgroid"]["width"] > boss_billboards["encounter_scarab_child"]["width"]
    assert any(script["type"] == "accent_burst" for script in boss_billboards["boss_lahgroid"]["scripts"])