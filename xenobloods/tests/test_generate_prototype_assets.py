from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import generate_prototype_assets  # noqa: E402
from prototype_asset_registry import PrototypeAssetRegistry  # noqa: E402


def _load_tool_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_prototype_assets_emits_gameplay_pack(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(generate_prototype_assets, "ASSET_DIR", tmp_path)

    generate_prototype_assets.main()

    expected = [
        tmp_path / "nav_land_zone_map.png",
        tmp_path / "battle_stage_land.png",
        tmp_path / "combat_timing_ring.png",
        tmp_path / "npc_tetrarch_opal.png",
        tmp_path / "enemy_scarab_child.png",
        tmp_path / "curgz_alpha.png",
        tmp_path / "xbox_series_controller_layout.png",
        tmp_path / "prototype_gameplay_asset_manifest.json",
    ]
    for path in expected:
        assert path.exists()

    manifest = json.loads((tmp_path / "prototype_gameplay_asset_manifest.json").read_text(encoding="utf-8"))
    assert manifest["prototype_pack"]["prototype_scope"]["boss"] == "lahgroid_hierophant"
    assert "xbox_series_controller" in manifest["prototype_pack"]
    assert manifest["asset_index"]["actor.lahgroid_hierophant"]["file"] == "boss_lahgroid_card.png"
    assert len(manifest["actors"]) >= 10


def test_asset_registry_resolves_manifest_backed_ids(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(generate_prototype_assets, "ASSET_DIR", tmp_path)
    generate_prototype_assets.main()

    registry = PrototypeAssetRegistry(asset_dir=tmp_path, manifest_path=tmp_path / "prototype_gameplay_asset_manifest.json")

    assert registry.file_for("scene.land.navigation") == "nav_land_zone_map.png"
    assert registry.path_for("controller.prompts") == tmp_path / "xbox_button_prompts.png"


def test_build_gameplay_prototype_asset_pack_writes_summary(tmp_path: Path, monkeypatch) -> None:
    builder = _load_tool_module("build_gameplay_prototype_asset_pack", TOOLS / "build_gameplay_prototype_asset_pack.py")

    generated_dir = tmp_path / "assets" / "generated"
    generated_dir.mkdir(parents=True)
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder.generate_prototype_assets, "ASSET_DIR", generated_dir)

    def fake_preview_build() -> dict:
        return {
            "active_preview": "lahgroid-boss-preview",
            "active_manifest": tmp_path / "jumpclip_pipeline_link.json",
            "runtime": {"sprite_preview": tmp_path / "runtime_preview.png"},
            "asset_service": {"summary_path": tmp_path / "service_summary.json"},
            "staged_previews": [{"name": "lahgroid-boss-preview", "character": "Lahgroid"}],
        }

    monkeypatch.setattr(builder, "build_and_stage_xenobloods_preview_set", fake_preview_build)

    result = builder.build_gameplay_prototype_asset_pack()

    summary_path = Path(result["summary_path"])
    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["active_preview"] == "lahgroid-boss-preview"
    assert payload["static_sections"]["backgrounds"] == 4
    assert payload["static_sections"]["battle_stages"] == 8
    assert payload["static_sections"]["controller"] == 2