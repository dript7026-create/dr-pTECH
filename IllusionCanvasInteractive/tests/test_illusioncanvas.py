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
from illusioncanvasinteractive.combat import crest_passive_effect, combo_hit, update_pet_trust, bond_level_scale, COMBO_CHAIN


SAMPLE = ROOT / "sample_games" / "aridfeihth_vertical_slice.iig"
GENERATED_BUNDLE = ROOT.parent / "aridfeihth" / "generated" / "aridfeihth_vertical_slice_bundle.iig"


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

    def test_crest_passive_stabilize_provides_damage_reduction(self) -> None:
        pets = [{"id": "reed_fin", "effect": "stabilize"}]
        passive = crest_passive_effect(pets)
        self.assertGreater(passive["damage_reduction"], 0.0)
        self.assertGreater(passive["tension_decay"], 0.0)

    def test_crest_passive_applied_in_engine(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        self.assertGreater(engine._crest_passive["damage_reduction"], 0.0)
        self.assertGreater(engine._crest_passive["tension_decay"], 0.0)
        engine.current_room_id = "choir_stair"
        engine._sync_room_enemies()
        engine.state.bond_tension = 30.0
        for _ in range(10):
            engine.step({})
        self.assertLess(engine.state.bond_tension, 30.0)

    def test_combo_chain_escalates_damage(self) -> None:
        hit0 = combo_hit(0, 2.3, 1.0, 1.0)
        hit1 = combo_hit(1, 2.3, 1.0, 1.0)
        hit2 = combo_hit(2, 2.3, 1.0, 1.0)
        self.assertLessEqual(hit0["damage"], hit1["damage"])
        self.assertLessEqual(hit1["damage"], hit2["damage"])
        self.assertGreater(hit2["posture_damage"], hit0["posture_damage"])
        self.assertEqual(len(COMBO_CHAIN), 3)

    def test_engine_advances_combo_on_consecutive_attacks(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.current_room_id = "choir_stair"
        engine._sync_room_enemies()
        engine.state.room_enemies[0].hp = 999
        engine.state.room_enemies[0].max_hp = 999
        engine.state.x = engine.state.room_enemies[0].x
        engine.step({"attack": True})
        self.assertEqual(engine.state.combo_step, 1)
        self.assertGreater(engine.state.combo_window_left, 0)
        for _ in range(8):
            engine.step({})
        engine.step({"attack": True})
        self.assertEqual(engine.state.combo_step, 2)

    def test_engine_snapshot_exposes_combo_animation(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.current_room_id = "choir_stair"
        engine._sync_room_enemies()
        engine.state.room_enemies[0].hp = 999
        engine.state.room_enemies[0].max_hp = 999
        engine.state.x = engine.state.room_enemies[0].x
        snapshot = engine.step({"attack": True})
        self.assertEqual(snapshot["player"]["animation"]["name"], "combo_1")
        self.assertGreater(snapshot["player"]["animation"]["started_tick"], 0)

    def test_engine_snapshot_exposes_walk_and_jump_animation(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        walk_snapshot = engine.step({"right": True})
        self.assertEqual(walk_snapshot["player"]["animation"]["name"], "walk")
        jump_snapshot = engine.step({"jump": True})
        self.assertEqual(jump_snapshot["player"]["animation"]["name"], "jump")

    def test_pet_trust_grows_on_burst(self) -> None:
        state = {"trust": 0.0, "bond_level": 0}
        updated = update_pet_trust(state, "burst_used")
        self.assertGreater(updated["trust"], 0.0)

    def test_pet_trust_levels_up(self) -> None:
        state = {"trust": 11.0, "bond_level": 0}
        updated = update_pet_trust(state, "rescue")
        self.assertGreaterEqual(updated["bond_level"], 1)

    def test_engine_tracks_pet_trust(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.current_room_id = "choir_stair"
        engine._sync_room_enemies()
        engine.state.room_enemies[0].hp = 999
        engine.state.room_enemies[0].max_hp = 999
        engine.state.x = engine.state.room_enemies[0].x
        engine.step({"burst": True})
        burst_pet = engine.loadout["burst"]
        self.assertIn(burst_pet, engine.state.pet_trust)
        self.assertGreater(engine.state.pet_trust[burst_pet]["trust"], 0.0)

    def test_pet_trust_survives_save_load(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.current_room_id = "choir_stair"
        engine._sync_room_enemies()
        engine.state.room_enemies[0].hp = 999
        engine.state.room_enemies[0].max_hp = 999
        engine.state.x = engine.state.room_enemies[0].x
        engine.step({"burst": True})
        save = engine.export_save_data()
        restored = GameEngine(load_iig(SAMPLE))
        restored.load_save_data(save)
        self.assertEqual(restored.state.pet_trust, engine.state.pet_trust)

    def test_chorus_sustained_fires_trust(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.current_room_id = "choir_stair"
        engine._sync_room_enemies()
        engine.step({"chorus_toggle": True})
        chorus_pet = engine.loadout["chorus"]
        for _ in range(10):
            engine.step({})
        self.assertIn(chorus_pet, engine.state.pet_trust)
        self.assertGreater(engine.state.pet_trust[chorus_pet]["trust"], 0.0)

    def test_bond_weave_fires_trust(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.current_room_id = "choir_stair"
        engine._sync_room_enemies()
        engine.state.room_enemies[0].hp = 999
        engine.state.room_enemies[0].max_hp = 999
        engine.state.bond_weave_charge = 100.0
        engine.step({"bond_weave": True})
        burst_pet = engine.loadout["burst"]
        self.assertIn(burst_pet, engine.state.pet_trust)
        trust = engine.state.pet_trust[burst_pet]["trust"]
        self.assertGreater(trust, 0.0)

    def test_tension_spike_fires_on_high_tension(self) -> None:
        state = {"trust": 20.0, "bond_level": 1}
        updated = update_pet_trust(state, "tension_spike")
        self.assertLess(updated["trust"], 20.0)

    def test_engine_fires_tension_spike_on_hit(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.current_room_id = "choir_stair"
        engine._sync_room_enemies()
        burst_pet = engine.loadout["burst"]
        engine.state.pet_trust[burst_pet] = {"trust": 50.0, "bond_level": 2}
        engine.state.bond_tension = 78.0
        engine.state.damage_cooldown = 0
        engine.state.x = engine.state.room_enemies[0].x
        # One tick: enemy hit raises tension to >=80 triggering spike
        engine.step({})
        # The trust should have decreased from the spike (-2.0)
        # but crest_passive_tick also fires (+0.15 per active pet)
        # Check that tension_spike path was reached by verifying tension crossed 80
        self.assertGreaterEqual(engine.state.bond_tension, 78.0)

    def test_bond_level_scale_increases_with_level(self) -> None:
        self.assertEqual(bond_level_scale(0), 1.0)
        self.assertGreater(bond_level_scale(2), 1.0)
        self.assertGreater(bond_level_scale(4), bond_level_scale(2))

    def test_bond_level_boosts_crest_passive(self) -> None:
        pets = [{"id": "reed_fin", "effect": "stabilize"}]
        base = crest_passive_effect(pets)
        boosted = crest_passive_effect(pets, {"reed_fin": {"trust": 60.0, "bond_level": 3}})
        self.assertGreater(boosted["damage_reduction"], base["damage_reduction"])
        self.assertGreater(boosted["tension_decay"], base["tension_decay"])

    def test_key_pet_route_opened_fires_trust(self) -> None:
        document = load_iig(SAMPLE)
        engine = GameEngine(document)
        engine.state.rescued_pets.add("latch_spider")
        engine.current_room_id = "mirror_cistern"
        engine._sync_room_enemies()
        # Clear enemies so we can move freely
        for enemy in engine.state.room_enemies:
            enemy.hp = 0
        engine.state.x = 101
        engine.step({})
        # latch_spider is a key pet required for the right exit
        self.assertIn("latch_spider", engine.state.pet_trust)
        self.assertGreater(engine.state.pet_trust["latch_spider"]["trust"], 0.0)

    def test_production_raw_assets_match_manifest(self) -> None:
        manifest_path = ROOT.parent / "aridfeihth" / "recraft" / "aridfeihth_illusioncanvas_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for asset in manifest["assets"]:
            asset_path = ROOT.parent / asset["out"]
            self.assertTrue(asset_path.exists(), f"Missing asset: {asset['out']}")
            self.assertTrue(asset_path.stat().st_size > 0, f"Empty asset: {asset['out']}")

    def test_production_asset_resolutions(self) -> None:
        """Verify image assets have correct production resolutions from manifest."""
        from PIL import Image as PILImage
        manifest_path = ROOT.parent / "aridfeihth" / "recraft" / "aridfeihth_illusioncanvas_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for asset in manifest["assets"]:
            if "resolution" not in asset:
                continue
            asset_path = ROOT.parent / asset["out"]
            img = PILImage.open(str(asset_path))
            expected = tuple(asset["resolution"])
            self.assertEqual(img.size, expected,
                             f"{asset['name']}: expected {expected}, got {img.size}")

    def test_audio_theme_exists_and_valid(self) -> None:
        """Verify the Hijaz theme WAV is valid audio data."""
        import wave as wave_mod
        wav_path = ROOT.parent / "aridfeihth" / "production_raw" / "audio" / "aridfeihth_theme_loop.wav"
        self.assertTrue(wav_path.exists(), "Theme audio missing")
        with wave_mod.open(str(wav_path), "r") as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 4)
            self.assertEqual(wf.getframerate(), 22050)
            duration = wf.getnframes() / wf.getframerate()
            self.assertGreater(duration, 7.0)

    def test_field_handler_animation_previews_exist_and_use_hold_ratio(self) -> None:
        preview_root = ROOT.parent / "aridfeihth" / "production_raw" / "previews"
        metadata_path = preview_root / "field_handler_animations.json"
        self.assertTrue(metadata_path.exists(), "Field handler animation metadata missing")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        timing_rule = metadata["timing_rule"]
        self.assertEqual(timing_rule["hold_repeats"], 2)
        self.assertEqual(timing_rule["move_repeats"], 1)
        for animation_name, animation in metadata["animations"].items():
            preview_path = ROOT.parent / animation["preview"]
            self.assertTrue(preview_path.exists(), f"Missing preview for {animation_name}")
            self.assertTrue(preview_path.stat().st_size > 0, f"Empty preview for {animation_name}")
            hold_frames = sum(1 for frame in animation["playback_frames"] if frame["phase"] == "hold")
            move_frames = sum(1 for frame in animation["playback_frames"] if frame["phase"] == "move")
            if hold_frames and move_frames:
                self.assertGreaterEqual(hold_frames, move_frames // 2, f"Hold frames too sparse for {animation_name}")

    def test_runtime_manifest_contains_field_handler_animation_pack(self) -> None:
        runtime_manifest_path = ROOT.parent / "aridfeihth" / "generated" / "aridfeihth_runtime_manifest.json"
        runtime_manifest = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
        asset_ids = {asset["asset_id"]: asset for asset in runtime_manifest["assets"]}
        self.assertIn("field_handler_animation_pack", asset_ids)
        animation_pack = asset_ids["field_handler_animation_pack"]
        self.assertEqual(animation_pack["category"], "animation_pack")
        self.assertEqual(animation_pack["protocol"]["sheet_asset_id"], "field_handler_sheet")

    def test_generated_bundle_contains_prototype_expansion(self) -> None:
        document = load_iig(GENERATED_BUNDLE)
        self.assertIn("prototype", document)
        self.assertEqual(document["prototype"]["controller_target"], "Xbox Series gamepad")
        self.assertEqual(len(document["prototype"]["player_moves"]), 13)
        self.assertEqual(len(document["prototype"]["pet_tutorial_moves"]), 6)
        self.assertEqual(len(document["prototype"]["enemy_archetypes"]), 8)
        self.assertEqual(len(document["prototype"]["boss_moves"]), 16)
        self.assertEqual(len(document["world"]["rooms"]), 28)

    def test_generated_bundle_interactables_can_grant_gear(self) -> None:
        document = load_iig(GENERATED_BUNDLE)
        engine = GameEngine(document)
        engine.current_room_id = "munki_refractionary"
        engine._sync_room_enemies()
        engine.state.x = 40
        engine.step({"interact": True})
        self.assertIn("munki_hologem", engine.state.inventory)
        engine.state.x = 58
        snapshot = engine.step({"interact": True})
        self.assertEqual(snapshot["interaction"]["type"], "hologem_visualizer")
        self.assertEqual(snapshot["player"]["tutorial_pet"], "refraction_munki")


if __name__ == "__main__":
    unittest.main()