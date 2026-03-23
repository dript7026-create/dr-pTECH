from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiential_genesis.adapters import ArchesAndAngelsAdapter, IllusionCanvasAdapter
from experiential_genesis.authorization import AuthorizationScope, MutationDomain, safe_profile
from experiential_genesis.hypermanager import build_demo_hypermanager


def test_hypermanager_tick_returns_consensus_frame() -> None:
    manager = build_demo_hypermanager()
    frame = manager.tick()
    assert frame.tick_index == 1
    assert frame.framebuffer["deterministic_luminance"] >= 0.0
    assert len(frame.particles) == 2
    assert len(manager.history) == 1


def test_illlusioncanvas_adapter_mutates_only_authorized_domains() -> None:
    adapter = IllusionCanvasAdapter(
        name="illusioncanvas",
        authorization=safe_profile(AuthorizationScope.ENGINE),
    )
    snapshot_before = adapter.snapshot()
    for mutation in adapter.propose_mutations(build_demo_hypermanager().tick().field):
        adapter.apply(mutation)
    snapshot_after = adapter.snapshot()
    assert snapshot_before.metrics != snapshot_after.metrics


def test_simulation_adapter_updates_campaign_focus() -> None:
    adapter = ArchesAndAngelsAdapter(
        name="archesandangels",
        authorization=safe_profile(AuthorizationScope.SIMULATION),
    )
    field = build_demo_hypermanager().tick().field
    for mutation in adapter.propose_mutations(field):
        adapter.apply(mutation)
    assert 0.0 <= adapter.campaign_stability <= 1.0
    assert 0.0 <= adapter.mission_focus <= 1.0


def test_observe_only_profile_blocks_mutation_domain() -> None:
    profile = safe_profile(AuthorizationScope.OBSERVE_ONLY)
    assert not profile.allows(MutationDomain.STATE)


def test_hypermanager_can_export_jsonl_history(tmp_path: Path) -> None:
    manager = build_demo_hypermanager(preset="storm")
    manager.tick()
    manager.tick()
    output = manager.export_history(tmp_path / "eg_history.jsonl")
    lines = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    loaded = json.loads(lines[0])
    assert loaded["tick_index"] == 1


def test_demo_preset_changes_initial_state() -> None:
    calm = build_demo_hypermanager(preset="calm")
    storm = build_demo_hypermanager(preset="storm")
    calm_arches = calm.adapters["archesandangels"]
    storm_arches = storm.adapters["archesandangels"]
    assert calm_arches.campaign_stability > storm_arches.campaign_stability