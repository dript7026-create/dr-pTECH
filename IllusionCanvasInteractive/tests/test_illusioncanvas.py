from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from illusioncanvasinteractive.engine import GameEngine
from illusioncanvasinteractive.egosphere_bridge import EgoSphereBridge
from illusioncanvasinteractive.iig import load_iig, validate_iig
from illusioncanvasinteractive.runtime_manifest import build_illusioncanvas_runtime_manifest


SAMPLE = ROOT / "sample_games" / "aridfeihth_vertical_slice.iig"


class IllusionCanvasTests(unittest.TestCase):
    def test_sample_iig_is_valid(self) -> None:
        document = json.loads(SAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(validate_iig(document), [])

    def test_runtime_manifest_uses_illusioncanvas_target(self) -> None:
        source_manifest = {
            "assets": [
                {
                    "name": "hero_sheet",
                    "category": "character_sheet",
                    "out": "production_raw/characters/hero.png",
                    "pipeline_targets": ["clipstudio", "illusioncanvas"],
                    "protocol": {"layout": "four_angle_quadrant", "derived_outputs": ["texture_depth_map"]},
                },
                {
                    "name": "ignored_sheet",
                    "category": "hud_pack",
                    "out": "production_raw/ui/ignored.png",
                    "pipeline_targets": ["clipstudio"],
                    "protocol": {"layout": "ui_atlas", "derived_outputs": []},
                },
            ]
        }
        runtime_manifest = build_illusioncanvas_runtime_manifest(source_manifest)
        self.assertEqual(runtime_manifest["asset_count"], 1)
        self.assertEqual(runtime_manifest["bucket_counts"], {"actors": 1})

    def test_engine_can_rescue_key_pet(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.step({"right": True})
        while engine.current_room_id != "glasswind_causeway":
            engine.step({"right": True})
        for _ in range(24):
            engine.step({"attack": True})
            engine.step({"burst": True})
        engine.state.x = 78
        engine.step({"rescue": True})
        self.assertIn("mirror_newt", engine.state.rescued_pets)

    def test_engine_boss_bond_weave_flow(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.state.rescued_pets.update({"mirror_newt", "latch_spider"})
        engine.current_room_id = "ember_nave"
        engine._sync_room_enemies()
        engine.state.bond_weave_charge = 100
        engine.state.chorus_active = True
        engine.state.room_enemies[0].root_ticks = 4
        engine.state.room_enemies[0].posture = 18
        engine.step({"bond_weave": True})
        self.assertTrue(engine.snapshot()["boss_defeated"])

    def test_engine_jump_and_landing_cycle(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.current_room_id = "choir_stair"
        engine._sync_room_enemies()
        engine._snap_player_to_support()
        baseline = engine.state.y
        engine.step({"jump": True})
        self.assertGreater(engine.state.y, baseline)
        for _ in range(32):
            engine.step({})
        self.assertTrue(engine.state.grounded)
        self.assertAlmostEqual(engine.state.y, baseline, delta=0.5)

    def test_engine_save_and_load_round_trip(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.current_room_id = "glasswind_causeway"
        engine._sync_room_enemies()
        engine.state.x = 78
        for _ in range(24):
            engine.step({"attack": True})
            engine.step({"burst": True})
        engine.step({"rescue": True})
        save_data = engine.export_save_data()

        restored = GameEngine(load_iig(SAMPLE))
        restored.load_save_data(save_data)
        self.assertIn("mirror_newt", restored.state.rescued_pets)
        self.assertEqual(restored.current_room_id, "glasswind_causeway")
        self.assertTrue(restored.room_states["glasswind_causeway"]["rescued"])

    def test_engine_can_reach_post_tutorial_branch(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.state.rescued_pets.update({"mirror_newt", "latch_spider", "salt_ram"})
        engine.state.completed_milestones.update({
            "refuge_reset",
            "mirror_newt_rescued",
            "latch_spider_rescued",
            "switchyard_stabilized",
            "ember_nave_weave",
            "sanctum_return",
        })
        engine.current_room_id = "tutorial_sanctum"
        engine._sync_room_enemies()
        engine.state.x = 101
        engine.step({})
        self.assertEqual(engine.current_room_id, "reliquary_bazaar")
        engine.state.x = 101
        engine.step({})
        self.assertEqual(engine.current_room_id, "atlas_choir")

    def test_egosphere_bridge_returns_reading(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        bridge = EgoSphereBridge({"mode": "native-preferred", "auto_build": False})
        reading = bridge.read_encounter(engine.state, engine.state.room_enemies)
        self.assertIn(reading.recommended_style, {"advance", "probe", "stabilize", "commit", "dodge_counter", "pressure_step"})


if __name__ == "__main__":
    unittest.main()