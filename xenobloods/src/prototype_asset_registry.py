from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "generated"
MANIFEST_PATH = ASSET_DIR / "prototype_gameplay_asset_manifest.json"


DEFAULT_ASSET_INDEX: dict[str, str] = {
    "logo.main": "logo_xenobloods.png",
    "scene.land.navigation": "nav_land_zone_map.png",
    "scene.up.dialogue": "nav_up_tetrarch_hall.png",
    "scene.low.puzzle": "nav_low_curgz_channel.png",
    "scene.land.battle": "battle_stage_land.png",
    "scene.up.battle": "battle_stage_up.png",
    "scene.low.battle": "battle_stage_low.png",
    "battle.timing_ring": "combat_timing_ring.png",
    "battle.storyboard": "battle_exchange_storyboard.png",
    "battle.boss_flow": "boss_realtime_flow.png",
    "portrait.landborne": "portrait_landborne.png",
    "portrait.gourd_infant": "portrait_gourd_infant.png",
    "portrait.etheric_current": "portrait_etheric.png",
    "state.landborne": "life_state_landborne.png",
    "state.gourd_infant": "life_state_gourd_infant.png",
    "state.etheric_current": "life_state_etheric.png",
    "actor.scarab_child_acolyte": "enemy_scarab_child.png",
    "actor.lattice_ward": "enemy_lattice_ward.png",
    "actor.lahgroid_hierophant": "boss_lahgroid_card.png",
    "actor.opal_tetrarch": "npc_tetrarch_opal.png",
    "actor.auditor_sal": "npc_tetrarch_auditor.png",
    "actor.verdict_chorister": "npc_tetrarch_verdict.png",
    "actor.curgz_alpha": "curgz_alpha.png",
    "actor.curgz_beta": "curgz_beta.png",
    "actor.curgz_gamma": "curgz_gamma.png",
    "support.up.dialogue": "up_dialogue_danger_strip.png",
    "support.low.puzzle": "low_curgz_puzzle_sheet.png",
    "panel.navigation": "hud_navigation.png",
    "panel.dialogue": "hud_dialogue.png",
    "panel.battle": "hud_battle.png",
    "panel.low": "hud_low_puzzle.png",
    "controller.layout": "xbox_series_controller_layout.png",
    "controller.prompts": "xbox_button_prompts.png",
}


class PrototypeAssetRegistry:
    def __init__(self, asset_dir: Path = ASSET_DIR, manifest_path: Path = MANIFEST_PATH) -> None:
        self.asset_dir = asset_dir
        self.manifest_path = manifest_path
        self.asset_index = dict(DEFAULT_ASSET_INDEX)
        self.asset_index.update(self._load_manifest_index())

    def _load_manifest_index(self) -> dict[str, str]:
        if not self.manifest_path.exists():
            return {}
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest_index = payload.get("asset_index", {})
        return {asset_id: record["file"] for asset_id, record in manifest_index.items()}

    def path_for(self, asset_id: str) -> Path:
        filename = self.asset_index[asset_id]
        return self.asset_dir / filename

    def file_for(self, asset_id: str) -> str:
        return self.asset_index[asset_id]
